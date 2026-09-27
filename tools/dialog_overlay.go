package main

// 目標165（規格035）：通用對話框整句中文覆蓋的純邏輯（模板比對、變數譯名、依框寬重排與三層字模）。
// 監看、權杖與啟用閘門在 live_menu.go；本檔不讀寫原版記憶體。

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"image"
	"regexp"
	"strconv"
	"strings"
	"unicode"

	"github.com/wicanr2/dosgolem/overlay"
)

type dialogTemplate struct {
	id    string
	re    *regexp.Regexp
	names []string // 依出現順序的變數名：%STRINGn、%NUMBERn、%COUNTRY
	zh    string   // 正文譯稿（空行前），保留 {} 強調標記與 %變數
}

type dialogFont struct {
	glyphs            map[rune]*image.Alpha
	widths            map[rune]int
	cjkTop, cjkBottom int
}

type dialogCatalog struct {
	templates []dialogTemplate
	terms     map[string]string // 英文→譯名；兩處譯名衝突者為空字串（視為查無）
	fonts     map[int]*dialogFont
}

type dialogChar struct {
	c   byte
	box image.Rectangle // 無墨跡（空白）時為空矩形
}

type dialogGlyph struct {
	r      rune
	accent bool
}

const (
	dialogFontPx    = 30 // A 版：與 help A 版同字級（原版墨跡 7 邏輯像素）
	dialogFloorPx   = 20 // 使用者 2026-09-26 決定：縮字下限為欄位字級 2/3
	dialogPitchAtPx = 40 // 30px 時行距 40 輸出像素（原版 10 邏輯像素）
)

var (
	dialogVar       = regexp.MustCompile(`%STRING\d|%NUMBER\d|%COUNTRY`)
	dialogSpaces    = regexp.MustCompile(`\s+`)
	dialogLineStart = "，。；：、！？％%）】》」』,.;:!?)]}"
	dialogLineEnd   = "（【《「『([{"
)

func dialogNormalize(s string) string {
	return strings.TrimSpace(dialogSpaces.ReplaceAllString(s, " "))
}

// splitTSV 以 tab 切欄、不處理引號（語料欄內有英文雙引號）。
func splitTSV(data []byte) []map[string]string {
	lines := strings.Split(strings.TrimRight(string(data), "\n"), "\n")
	header := strings.Split(lines[0], "\t")
	var rows []map[string]string
	for _, line := range lines[1:] {
		f := strings.Split(line, "\t")
		if len(f) != len(header) {
			return nil
		}
		row := map[string]string{}
		for i, h := range header {
			row[h] = f[i]
		}
		rows = append(rows, row)
	}
	return rows
}

// loadDialogCatalog 由語料清冊建立 GAME.TXT 正文模板；每列都以原版檔案位移、長度與片段雜湊核對。
// exclude 內的訊息鍵由專屬欄位處理，不進本引擎。
func loadDialogCatalog(corpus, terms []byte, game []byte, gameSHA string, exclude map[string]bool) (*dialogCatalog, error) {
	if fmt.Sprintf("%x", sha256.Sum256(game)) != gameSHA {
		return nil, fmt.Errorf("GAME.TXT 版本不符")
	}
	rows := splitTSV(corpus)
	if rows == nil {
		return nil, fmt.Errorf("語料清冊欄位不符")
	}
	cat := &dialogCatalog{terms: map[string]string{}}
	seen := map[string]bool{}
	for _, r := range rows {
		if r["source_file"] != "GAME.TXT" {
			if r["source_file"] == "NAMES.TXT" {
				cat.addNamePairs(r["source_en"], r["zh_hant"])
			}
			continue
		}
		if r["source_file_sha256"] != gameSHA || exclude[r["message_id"]] || r["zh_hant"] == "" {
			continue
		}
		off, err1 := strconv.ParseInt(r["text_offset"], 0, 64)
		n, err2 := strconv.Atoi(r["text_byte_length"])
		if err1 != nil || err2 != nil || off < 0 || int(off)+n > len(game) {
			return nil, fmt.Errorf("位移不符：%s", r["message_id"])
		}
		raw := game[off : int(off)+n]
		if fmt.Sprintf("%x", sha256.Sum256(raw)) != r["source_bytes_sha256"] {
			return nil, fmt.Errorf("片段雜湊不符：%s", r["message_id"])
		}
		if seen[r["message_id"]] {
			return nil, fmt.Errorf("重複鍵：%s", r["message_id"])
		}
		seen[r["message_id"]] = true
		body := string(bytes.SplitN(raw, []byte("\r\n\r\n"), 2)[0])
		if strings.ContainsAny(body, "^@") {
			continue // 置中碼與指令列另案
		}
		body = dialogNormalize(strings.NewReplacer("{", "", "}", "").Replace(body))
		pattern, names := "^", []string{}
		last := 0
		for _, m := range dialogVar.FindAllStringIndex(body, -1) {
			pattern += regexp.QuoteMeta(body[last:m[0]])
			name := body[m[0]:m[1]]
			if strings.HasPrefix(name, "%NUMBER") {
				pattern += `(\d+)`
			} else {
				pattern += `(.+?)`
			}
			names = append(names, name)
			last = m[1]
		}
		pattern += regexp.QuoteMeta(body[last:]) + "$"
		zh := strings.SplitN(r["zh_hant"], `\n\n`, 2)[0]
		zh = strings.ReplaceAll(zh, `\n`, "")
		cat.templates = append(cat.templates, dialogTemplate{id: r["message_id"], re: regexp.MustCompile(pattern), names: names, zh: zh})
	}
	for _, r := range splitTSV(terms) {
		cat.addTerm(r["en"], r["zh"])
	}
	return cat, nil
}

func (c *dialogCatalog) addTerm(en, zh string) {
	en, zh = strings.TrimSpace(en), strings.TrimSpace(zh)
	if en == "" || zh == "" {
		return
	}
	if old, ok := c.terms[en]; ok && old != zh {
		c.terms[en] = ""
		return
	}
	c.terms[en] = zh
}

// addNamePairs 只在原文與譯文逗號數相同時逐欄配對含英文字母的欄位。
func (c *dialogCatalog) addNamePairs(en, zh string) {
	e, z := strings.Split(en, ","), strings.Split(zh, ",")
	if len(e) != len(z) {
		return
	}
	for i := range e {
		if strings.IndexFunc(e[i], unicode.IsLetter) >= 0 {
			c.addTerm(e[i], z[i])
		}
	}
}

// dialogShownText 依逐字事件重組原版顯示字串：x 回捲即換行，行間補一個空白，再壓縮空白。
func dialogShownText(chars []dialogChar) string {
	var b strings.Builder
	lastX := -1
	for _, ch := range chars {
		if !ch.box.Empty() {
			if lastX >= 0 && ch.box.Min.X < lastX {
				b.WriteByte(' ')
			}
			lastX = ch.box.Min.X
		}
		b.WriteByte(ch.c)
	}
	return dialogNormalize(b.String())
}

// match 回傳唯一命中的模板與代入變數後的中文；reason 非空即回原文。
func (c *dialogCatalog) match(shown string) (id, zh, reason string) {
	var hit *dialogTemplate
	var groups []string
	for i := range c.templates {
		t := &c.templates[i]
		if m := t.re.FindStringSubmatch(shown); m != nil {
			if hit != nil {
				return "", "", "template-not-unique"
			}
			hit, groups = t, m[1:]
		}
	}
	if hit == nil {
		return "", "", "no-template"
	}
	zh = hit.zh
	for i, name := range hit.names {
		v := groups[i]
		if !strings.HasPrefix(name, "%NUMBER") {
			tr := c.terms[v]
			if tr == "" {
				return hit.id, "", "variable-without-term"
			}
			v = tr
		}
		zh = strings.Replace(zh, name, v, 1)
	}
	if strings.Contains(zh, "%") {
		return hit.id, "", "unresolved-variable"
	}
	return hit.id, zh, ""
}

func dialogMarked(zh string) ([]dialogGlyph, bool) {
	var out []dialogGlyph
	accent := false
	for _, r := range zh {
		switch r {
		case '{':
			if accent {
				return nil, false
			}
			accent = true
		case '}':
			if !accent {
				return nil, false
			}
			accent = false
		default:
			out = append(out, dialogGlyph{r, accent})
		}
	}
	return out, !accent
}

// dialogWrap 依寬度與行首／行尾禁則折行；連續 ASCII 英數字不拆開。
func dialogWrap(glyphs []dialogGlyph, f *dialogFont, limit int) ([][]dialogGlyph, bool) {
	var lines [][]dialogGlyph
	var cur []dialogGlyph
	w := 0
	for _, g := range glyphs {
		gw, ok := f.widths[g.r]
		if !ok {
			return nil, false
		}
		if len(cur) == 0 || w+gw <= limit {
			cur, w = append(cur, g), w+gw
			continue
		}
		carried := []dialogGlyph{g}
		if strings.ContainsRune(dialogLineStart, g.r) && len(cur) > 1 {
			carried = append([]dialogGlyph{cur[len(cur)-1]}, carried...)
			cur = cur[:len(cur)-1]
		}
		for len(cur) > 1 && isASCIIAlnum(cur[len(cur)-1].r) && isASCIIAlnum(carried[0].r) {
			carried = append([]dialogGlyph{cur[len(cur)-1]}, carried...)
			cur = cur[:len(cur)-1]
		}
		for len(cur) > 1 && strings.ContainsRune(dialogLineEnd, cur[len(cur)-1].r) {
			carried = append([]dialogGlyph{cur[len(cur)-1]}, carried...)
			cur = cur[:len(cur)-1]
		}
		lines = append(lines, cur)
		cur, w = carried, 0
		for _, c := range cur {
			w += f.widths[c.r]
		}
	}
	if len(cur) > 0 {
		lines = append(lines, cur)
	}
	for _, line := range lines {
		lw := 0
		for _, g := range line {
			lw += f.widths[g.r]
		}
		if lw > limit || strings.ContainsRune(dialogLineStart, line[0].r) || strings.ContainsRune(dialogLineEnd, line[len(line)-1].r) {
			return nil, false
		}
	}
	return lines, true
}

func isASCIIAlnum(r rune) bool {
	return r < 0x80 && (unicode.IsLetter(r) || unicode.IsDigit(r))
}

// dialogMasks 在 w×h 輸出像素的安全區內排版，回傳陰影、一般、強調三層與所用字級；放不下回傳 0。
// 字頭（中文墨跡上緣）對齊安全區上緣 +4、左緣 +4；陰影向右下 4 輸出像素。
func (c *dialogCatalog) dialogMasks(zh string, w, h int) (shadow, normal, accent *image.Alpha, size int) {
	glyphs, ok := dialogMarked(zh)
	if !ok || len(glyphs) == 0 {
		return nil, nil, nil, 0
	}
	for size = dialogFontPx; size >= dialogFloorPx; size-- {
		f := c.fonts[size]
		if f == nil {
			return nil, nil, nil, 0
		}
		lines, ok := dialogWrap(glyphs, f, w-8)
		if !ok {
			continue
		}
		pitch := (dialogPitchAtPx*size + dialogFontPx/2) / dialogFontPx
		if 4+(len(lines)-1)*pitch+(f.cjkBottom-f.cjkTop)+4 > h {
			continue
		}
		rect := image.Rect(0, 0, w, h)
		shadow, normal, accent = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		for k, line := range lines {
			x, y := 4, 4+k*pitch-f.cjkTop
			for _, g := range line {
				a := f.glyphs[g.r]
				dialogBlit(normal, a, x, y)
				dialogBlit(shadow, a, x+4, y+4)
				if g.accent {
					dialogBlit(accent, a, x, y)
				}
				x += f.widths[g.r]
			}
		}
		return shadow, normal, accent, size
	}
	return nil, nil, nil, 0
}

func dialogBlit(dst, src *image.Alpha, x, y int) {
	for gy := 0; gy < src.Rect.Dy(); gy++ {
		for gx := 0; gx < src.Rect.Dx(); gx++ {
			v := src.Pix[gy*src.Stride+gx]
			if v == 0 || !image.Pt(x+gx, y+gy).In(dst.Rect) {
				continue
			}
			if i := dst.PixOffset(x+gx, y+gy); v > dst.Pix[i] {
				dst.Pix[i] = v
			}
		}
	}
}

// loadDialogAtlas 讀 tools/bake_dialog_atlas.py 的圖集並核對字型、語料與術語表雜湊。
func (c *dialogCatalog) loadDialogAtlas(b []byte, fontSHA, corpusSHA, termsSHA string) string {
	var atlas struct {
		Font   string `json:"font_sha256"`
		Px     int    `json:"font_px"`
		Floor  int    `json:"floor_px"`
		Corpus string `json:"corpus_sha256"`
		Terms  string `json:"terms_sha256"`
		Sizes  map[string]struct {
			Height    int `json:"height"`
			CJKTop    int `json:"cjk_ink_top"`
			CJKBottom int `json:"cjk_ink_bottom"`
			Glyphs    map[string]struct {
				W     int    `json:"w"`
				Alpha string `json:"alpha"`
			} `json:"glyphs"`
		} `json:"sizes"`
	}
	if json.Unmarshal(b, &atlas) != nil {
		return "font-mask-unavailable"
	}
	if atlas.Font != fontSHA || atlas.Px != dialogFontPx || atlas.Floor != dialogFloorPx ||
		atlas.Corpus != corpusSHA || atlas.Terms != termsSHA {
		return "font-binding-mismatch"
	}
	c.fonts = map[int]*dialogFont{}
	for size := dialogFloorPx; size <= dialogFontPx; size++ {
		src, ok := atlas.Sizes[strconv.Itoa(size)]
		if !ok || src.Height <= 0 || src.CJKBottom <= src.CJKTop {
			return "font-mask-out-of-bounds"
		}
		f := &dialogFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, cjkTop: src.CJKTop, cjkBottom: src.CJKBottom}
		for k, g := range src.Glyphs {
			r := []rune(k)
			pix, err := base64.StdEncoding.DecodeString(g.Alpha)
			if len(r) != 1 || g.W <= 0 || err != nil || len(pix) != g.W*src.Height {
				return "font-mask-out-of-bounds"
			}
			a := image.NewAlpha(image.Rect(0, 0, g.W, src.Height))
			copy(a.Pix, pix)
			f.glyphs[r[0]], f.widths[r[0]] = a, g.W
		}
		c.fonts[size] = f
	}
	return ""
}

// ---- 執行期狀態（規格035 覆蓋設計 1、2、5、7）----

type dialogRun struct {
	base          uint32
	readPos       int
	start, last   uint64
	chars         []dialogChar
	firstOld      map[int]byte
	lastText      map[int]bool
	shadowWritten bool
	others        image.Rectangle // 段內其他寫入者（游標除外）的範圍
}

type dialogShown struct {
	id, zh, reason         string
	safe                   image.Rectangle
	before                 []byte
	shadow, normal, accent *image.Alpha
	size                   int
	phase                  string // waiting-screen、active、expired
	complete               uint64
	patch                  *overlay.Patch
	afterSafe              []byte
	appliedFrames          int
}

type dialogRuntime struct {
	cat        *dialogCatalog
	fontReason string
	run        *dialogRun
	cur        *dialogShown
	accepted   int
	misses     map[string]int // 有陰影色但未能中文化的顯示字串與原因
}

const dialogGap = 20000 // 兩萬步內無讀取即視為一段結束（字距約 800～1,400 步、換行約 2,500 步）

// onRead 處理一次 0D21:00C6 讀取；若上一段已結束，先回傳該段供呼叫端收尾。
func (d *dialogRuntime) onRead(a uint32, v byte, step uint64) (finished *dialogRun) {
	if r := d.run; r != nil && step-r.last < dialogGap {
		if r.readPos%2 == 1 && a == r.base+1 {
			if v != 0 {
				d.run = nil // 連續字串（狀態欄、選單列），不是逐字對話
				return nil
			}
			r.readPos++
			r.last = step
			return nil
		}
		if r.readPos%2 == 0 && a == r.base {
			r.chars = append(r.chars, dialogChar{c: v})
			r.readPos++
			r.last = step
			return nil
		}
	}
	finished = d.run
	d.run = &dialogRun{base: a, readPos: 1, start: step, last: step, chars: []dialogChar{{c: v}},
		firstOld: map[int]byte{}, lastText: map[int]bool{}}
	return finished
}

// onWrite 記錄段內畫布寫入；text 表示寫入者為 0D21:012C，cursor 表示游標常式在游標附近。
func (d *dialogRuntime) onWrite(i int, old, value byte, text, cursor bool) {
	r := d.run
	if r == nil {
		return
	}
	x, y := i%320, i/320
	if text {
		if _, seen := r.firstOld[i]; !seen {
			r.firstOld[i] = old
		}
		r.lastText[i] = true
		if value == 47 || value == 128 {
			r.shadowWritten = true
		}
		if n := len(r.chars); n > 0 {
			r.chars[n-1].box = r.chars[n-1].box.Union(image.Rect(x, y, x+1, y+1))
		}
		return
	}
	if !cursor {
		r.lastText[i] = false
		r.others = r.others.Union(image.Rect(x, y, x+1, y+1))
	}
}

// scanDialogBox 由框內一點向左、右、上掃描到色號 0 的外框。
func scanDialogBox(canvas []byte, x, y int) (l, t, r int) {
	l, r, t = x, x, y
	for l > 0 && canvas[y*320+l] != 0 {
		l--
	}
	for r < 319 && canvas[y*320+r] != 0 {
		r++
	}
	for t > 0 && canvas[t*320+x] != 0 {
		t--
	}
	return l, t, r
}

// finish 對一段已結束的逐字事件做比對與版面；回傳要顯示的狀態，或原因（不是對話框時兩者皆空）。
func (d *dialogRuntime) finish(r *dialogRun, canvas []byte, step uint64) (*dialogShown, string, string) {
	if r == nil || !r.shadowWritten || r.readPos%2 == 1 {
		return nil, "", ""
	}
	var ink image.Rectangle
	first := -1
	for i, ch := range r.chars {
		if !ch.box.Empty() {
			ink = ink.Union(ch.box)
			if first < 0 {
				first = i
			}
		}
	}
	shown := dialogShownText(r.chars)
	if first < 0 {
		return nil, shown, "no-ink"
	}
	id, zh, why := d.cat.match(shown)
	if why != "" {
		return nil, shown, why
	}
	before := bytes.Clone(canvas)
	for i, text := range r.lastText {
		if text {
			before[i] = r.firstOld[i]
		}
	}
	c0 := r.chars[first].box
	l, t, rt := scanDialogBox(before, c0.Min.X, (c0.Min.Y+c0.Max.Y)/2)
	safe := image.Rect(l+3, t+3, rt-3, ink.Max.Y+2)
	if l == 0 || t == 0 || rt == 319 || !ink.In(safe) {
		return nil, shown, "ink-outside-box"
	}
	if !r.others.Empty() && r.others.Overlaps(safe) {
		return nil, shown, "unexpected-writer-in-safe"
	}
	sh, n, ac, size := d.cat.dialogMasks(zh, safe.Dx()*4, safe.Dy()*4)
	if size == 0 {
		return nil, shown, "layout-overflow"
	}
	return &dialogShown{id: id, zh: zh, safe: safe, before: before, shadow: sh, normal: n, accent: ac,
		size: size, phase: "waiting-screen", complete: step}, shown, ""
}
