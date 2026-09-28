package main

// 目標165（規格035）：通用對話框整句中文覆蓋的純邏輯（模板比對、變數譯名、依框寬重排與三層字模）。
// 目標166（規格036）：同一段落偵測另支援置中段落（^）與逐行清單（下拉選單、選項列、單行字串）。
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
	zh    string   // 正文譯稿（空行前），保留 {} 強調標記與 %變數；置中段落另保留 \n 與 ^
	// 目標166：原文含 ^ 置中碼的段落（例如國王接見），依譯稿的 ^^ 行置中、其餘依寬度重排。
	centered bool
}

type dialogFont struct {
	glyphs            map[rune]*image.Alpha
	widths            map[rune]int
	cjkTop, cjkBottom int
}

type dialogCatalog struct {
	templates []dialogTemplate
	lines     []dialogTemplate  // 目標166：逐行清單比對用的單行模板
	seen      map[string]bool   // 已載入的訊息鍵（跨語料檢查重複）
	terms     map[string]string // 英文→譯名；定稿譯名彼此衝突者為空字串（視為查無）
	canon     map[string]bool   // 目標167：來自定稿譯名表（優先於 NAMES.TXT 對照）的詞
	fonts     map[int]*dialogFont
}

type dialogChar struct {
	c      byte
	box    image.Rectangle // 無墨跡（空白）時為空矩形
	colors map[byte]int    // 目標166：本字改色點的色號分布
}

type dialogGlyph struct {
	r      rune
	accent bool
}

const (
	dialogFontPx    = 30 // A 版：與 help A 版同字級（原版墨跡 7 邏輯像素）
	dialogFloorPx   = 20 // 使用者 2026-09-26 決定：縮字下限為欄位字級 2/3（字高 7 時）
	dialogAtlasMin  = 12 // 目標170：圖集字級下限（字高 5 的框起始 22px、下限 15px）
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
	cat := &dialogCatalog{terms: map[string]string{}, seen: map[string]bool{}}
	if err := cat.addCorpus(corpus, game, gameSHA, exclude); err != nil {
		return nil, err
	}
	for _, r := range splitTSV(terms) {
		cat.addTerm(r["en"], r["zh"])
	}
	return cat, nil
}

// addCorpus 加入一份語料 TSV 的 GAME.TXT 模板（語料清冊或 help 雙語清冊，欄名相同）；
// NAMES.TXT 列另作變數譯名對照。每列以原檔位移、長度與片段雜湊核對。
func (cat *dialogCatalog) addCorpus(corpus, game []byte, gameSHA string, exclude map[string]bool) error {
	rows := splitTSV(corpus)
	if rows == nil {
		return fmt.Errorf("語料清冊欄位不符")
	}
	seen := cat.seen
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
			return fmt.Errorf("位移不符：%s", r["message_id"])
		}
		raw := game[off : int(off)+n]
		if fmt.Sprintf("%x", sha256.Sum256(raw)) != r["source_bytes_sha256"] {
			return fmt.Errorf("片段雜湊不符：%s", r["message_id"])
		}
		if seen[r["message_id"]] {
			return fmt.Errorf("重複鍵：%s", r["message_id"])
		}
		seen[r["message_id"]] = true
		parts := strings.SplitN(string(raw), "\r\n\r\n", 2)
		zhParts := strings.SplitN(r["zh_hant"], `\n\n`, 2)
		body := parts[0]
		if strings.Contains(body, "@") {
			continue // 指令列另案
		}
		centered := strings.Contains(body, "^")
		zh := zhParts[0]
		if !centered {
			zh = strings.ReplaceAll(zh, `\n`, "")
		}
		cat.templates = append(cat.templates, makeDialogTemplate(r["message_id"], body, zh, centered))
		if !centered && !strings.Contains(body, "\r\n") {
			cat.lines = append(cat.lines, makeDialogTemplate(r["message_id"], body, zh, false))
		}
		// 選項行：空行後逐行對應譯稿空行後的各行；行數不同即不採用。
		if len(parts) == 2 && len(zhParts) == 2 {
			var eo, zo []string
			for _, l := range strings.Split(parts[1], "\r\n") {
				if strings.TrimSpace(l) != "" && !strings.ContainsAny(l, "@^") {
					eo = append(eo, l)
				}
			}
			for _, l := range strings.Split(zhParts[1], `\n`) {
				if strings.TrimSpace(l) != "" {
					zo = append(zo, l)
				}
			}
			if len(eo) == len(zo) {
				for i := range eo {
					cat.lines = append(cat.lines, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
				}
			}
		}
	}
	return nil
}

// makeDialogTemplate 把原文正規化成整句比對用的正規式：去 {}、^，換行當空白並壓縮空白。
func makeDialogTemplate(id, body, zh string, centered bool) dialogTemplate {
	body = dialogNormalize(strings.NewReplacer("{", "", "}", "", "^", "", "\r\n", " ").Replace(body))
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
	return dialogTemplate{id: id, re: regexp.MustCompile(pattern), names: names, zh: zh, centered: centered}
}

// addDraft 由譯稿 TSV（draft.zh-Hant.tsv）加入逐行模板：GAME.TXT 單行列與 MENU.TXT 選單項目；
// NAMES.TXT 列另作變數譯名對照。
// 每列以原檔位移與片段雜湊核對；exclude 內是已由專屬欄位處理的鍵。
// 含熱鍵標記 ~ 或 # 的列顯示方式未取證，本輪不採用。
func (c *dialogCatalog) addDraft(draft []byte, files map[string][]byte, exclude map[string]bool) error {
	rows := splitTSV(draft)
	if rows == nil {
		return fmt.Errorf("譯稿 TSV 欄位不符")
	}
	for _, r := range rows {
		data, ok := files[r["source_file"]]
		if !ok || exclude[r["candidate_id"]] {
			continue
		}
		off, err1 := strconv.ParseInt(r["byte_offset"], 0, 64)
		n, err2 := strconv.Atoi(r["source_byte_length"])
		if r["source_sha256"] != fmt.Sprintf("%x", sha256.Sum256(data)) || err1 != nil || err2 != nil || off < 0 || int(off)+n > len(data) {
			return fmt.Errorf("%s 版本或位移不符：%s", r["source_file"], r["candidate_id"])
		}
		raw := string(data[off : int(off)+n])
		if fmt.Sprintf("%x", sha256.Sum256([]byte(raw))) != r["source_bytes_sha256"] {
			return fmt.Errorf("%s 片段雜湊不符：%s", r["source_file"], r["candidate_id"])
		}
		zh := strings.TrimSpace(r["zh_hant"])
		if r["source_file"] == "NAMES.TXT" {
			// 目標167：譯稿的 NAMES.TXT 單詞（例如歐洲母港名）作變數譯名對照，優先序低於定稿譯名。
			c.addNamePairs(raw, zh)
			continue
		}
		if zh == "" || strings.Contains(raw, "\r\n") || strings.ContainsAny(raw, "~#@^") || strings.ContainsAny(zh, "~#^") {
			continue
		}
		c.lines = append(c.lines, makeDialogTemplate(r["candidate_id"], raw, zh, false))
	}
	return nil
}

// addValues 讀執行檔提供的變數值譯名（例如版本日期）；每列以原檔位移核對原文。
func (c *dialogCatalog) addValues(tsv []byte, files map[string][]byte) error {
	rows := splitTSV(tsv)
	if rows == nil {
		return fmt.Errorf("變數值 TSV 欄位不符")
	}
	for _, r := range rows {
		data, ok := files[r["source_file"]]
		off, err := strconv.ParseInt(r["byte_offset"], 0, 64)
		if !ok || err != nil || fmt.Sprintf("%x", sha256.Sum256(data)) != r["source_sha256"] ||
			off < 0 || int(off)+len(r["en"]) > len(data) || string(data[off:int(off)+len(r["en"])]) != r["en"] {
			return fmt.Errorf("變數值來源不符：%s", r["en"])
		}
		c.addTerm(r["en"], r["zh"])
	}
	return nil
}

// addTerm 加入定稿譯名：優先於 NAMES.TXT 對照；定稿譯名彼此衝突即視為查無。
func (c *dialogCatalog) addTerm(en, zh string) {
	en, zh = strings.TrimSpace(en), strings.TrimSpace(zh)
	if en == "" || zh == "" {
		return
	}
	if c.canon == nil {
		c.canon = map[string]bool{}
	}
	if old, ok := c.terms[en]; ok && c.canon[en] && old != zh {
		c.terms[en] = ""
		return
	}
	c.terms[en], c.canon[en] = zh, true
}

// addWeakTerm 加入 NAMES.TXT 對照：只補定稿譯名沒有的詞；對照彼此衝突時保留先出現者。
func (c *dialogCatalog) addWeakTerm(en, zh string) {
	en, zh = strings.TrimSpace(en), strings.TrimSpace(zh)
	if en == "" || zh == "" {
		return
	}
	if _, ok := c.terms[en]; !ok {
		c.terms[en] = zh
	}
}

// addNamePairs 只在原文與譯文逗號數相同時逐欄配對含英文字母的欄位。
func (c *dialogCatalog) addNamePairs(en, zh string) {
	e, z := strings.Split(en, ","), strings.Split(zh, ",")
	if len(e) != len(z) {
		return
	}
	for i := range e {
		if strings.IndexFunc(e[i], unicode.IsLetter) >= 0 {
			c.addWeakTerm(e[i], z[i])
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
		if ch.c != 0 {
			b.WriteByte(ch.c)
		}
	}
	return dialogNormalize(b.String())
}

var dialogPlainValue = regexp.MustCompile(`^[0-9][0-9.,%$]*$`)

// match 回傳唯一命中的模板與代入變數後的中文；reason 非空即回原文。
func (c *dialogCatalog) match(shown string) (id, zh, reason string) {
	t, zh, reason := c.matchIn(c.templates, shown)
	if t != nil {
		id = t.id
	}
	return id, zh, reason
}

// matchIn 在指定模板集合中整句比對；數字與純數值變數原樣保留，其餘查譯名。
func (c *dialogCatalog) matchIn(list []dialogTemplate, shown string) (*dialogTemplate, string, string) {
	var hit *dialogTemplate
	var groups []string
	for i := range list {
		t := &list[i]
		if m := t.re.FindStringSubmatch(shown); m != nil {
			if hit != nil && hit.zh != t.zh {
				return nil, "", "template-not-unique"
			}
			hit, groups = t, m[1:]
		}
	}
	if hit == nil {
		return nil, "", "no-template"
	}
	zh := hit.zh
	for i, name := range hit.names {
		v := groups[i]
		if !strings.HasPrefix(name, "%NUMBER") && !dialogPlainValue.MatchString(v) {
			tr := c.terms[v]
			if tr == "" {
				return hit, "", "variable-without-term"
			}
			v = tr
		}
		zh = strings.Replace(zh, name, v, -1)
	}
	if strings.Contains(zh, "%") {
		return hit, "", "unresolved-variable"
	}
	return hit, zh, ""
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
// dialogSizes 依原版大寫字高量起始字級 ⌊capH×4.4⌋（上限 30）與下限（起始的 2/3）；字高未知時用 30／20。
func dialogSizes(capH int) (start, floor int) {
	if capH <= 0 {
		return dialogFontPx, dialogFloorPx
	}
	start, floor = stringStartPx(capH)
	if start > dialogFontPx {
		return dialogFontPx, dialogFloorPx
	}
	return start, max(floor, dialogAtlasMin)
}

func (c *dialogCatalog) dialogMasks(zh string, w, h, capH int) (shadow, normal, accent *image.Alpha, size int) {
	glyphs, ok := dialogMarked(zh)
	if !ok || len(glyphs) == 0 {
		return nil, nil, nil, 0
	}
	start, floor := dialogSizes(capH)
	for size = start; size >= floor; size-- {
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
func (c *dialogCatalog) loadDialogAtlas(b []byte, fontSHA string, bind map[string]string) string {
	fonts, reason := loadAtlasFonts(b, fontSHA, bind, dialogFontPx, dialogAtlasMin)
	if reason == "" {
		c.fonts = fonts
	}
	return reason
}

// loadAtlasFonts 讀字元圖集並核對字型、字級範圍與綁定雜湊（目標169：通用字串層共用）。
func loadAtlasFonts(b []byte, fontSHA string, bind map[string]string, px, floor int) (map[int]*dialogFont, string) {
	var atlas struct {
		Font  string            `json:"font_sha256"`
		Px    int               `json:"font_px"`
		Floor int               `json:"floor_px"`
		Bind  map[string]string `json:"bindings"`
		Sizes map[string]struct {
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
		return nil, "font-mask-unavailable"
	}
	if atlas.Font != fontSHA || atlas.Px != px || atlas.Floor != floor || len(atlas.Bind) != len(bind) {
		return nil, "font-binding-mismatch"
	}
	for k, v := range bind {
		if atlas.Bind[k] != v {
			return nil, "font-binding-mismatch"
		}
	}
	fonts := map[int]*dialogFont{}
	for size := floor; size <= px; size++ {
		src, ok := atlas.Sizes[strconv.Itoa(size)]
		if !ok || src.Height <= 0 || src.CJKBottom <= src.CJKTop {
			return nil, "font-mask-out-of-bounds"
		}
		f := &dialogFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, cjkTop: src.CJKTop, cjkBottom: src.CJKBottom}
		for k, g := range src.Glyphs {
			r := []rune(k)
			pix, err := base64.StdEncoding.DecodeString(g.Alpha)
			if len(r) != 1 || g.W <= 0 || err != nil || len(pix) != g.W*src.Height {
				return nil, "font-mask-out-of-bounds"
			}
			a := image.NewAlpha(image.Rect(0, 0, g.W, src.Height))
			copy(a.Pix, pix)
			f.glyphs[r[0]], f.widths[r[0]] = a, g.W
		}
		fonts[size] = f
	}
	return fonts, ""
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
	normalC, accentC       byte // 目標166：原版觀測字色
	shadowC                byte // 0 表示原版沒有陰影
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
			ch := &r.chars[n-1]
			ch.box = ch.box.Union(image.Rect(x, y, x+1, y+1))
			if ch.colors == nil {
				ch.colors = map[byte]int{}
			}
			ch.colors[value]++
		}
		return
	}
	if !cursor {
		r.lastText[i] = false
		r.others = r.others.Union(image.Rect(x, y, x+1, y+1))
	}
}

// dialogLike 判斷一段逐字印字像不像等待玩家應答的訊息框：有陰影色，或在地圖區（頂列與右側狀態欄以外）十字以上。
// 只供真 GUI 自動應答與探勘使用，不影響覆蓋。
func (r *dialogRun) dialogLike() bool {
	var ink image.Rectangle
	n := 0
	for _, ch := range r.chars {
		if !ch.box.Empty() {
			ink = ink.Union(ch.box)
			n++
		}
	}
	// 目標170：不再限制 x<240（港口說明框、訓練對話框延伸到右側）；狀態欄是連續字串，不經本判斷。
	return r.shadowWritten || (n >= 10 && ink.Min.Y > 8)
}

// scanDialogBox 掃描色號 0 的外框：左右框沿 (hx,hy) 所在列、上框取 [x0,x1) 各欄由 ty 往上的最常見列。
// 顧問肖像常壓在框的左上或上緣，所以呼叫端以最後一行（肖像下方）掃左右、以首行整段寬度掃上框。
func scanDialogBox(canvas []byte, hx, hy, x0, x1, ty int) (l, t, r int) {
	l, r = hx, hx
	for l > 0 && canvas[hy*320+l] != 0 {
		l--
	}
	for r < 319 && canvas[hy*320+r] != 0 {
		r++
	}
	count := map[int]int{}
	for x := max(x0, 0); x < min(x1, 320); x++ {
		y := ty
		for y > 0 && canvas[y*320+x] != 0 {
			y--
		}
		count[y]++
	}
	best := -1
	for y, n := range count {
		if best < 0 || n > count[best] || (n == count[best] && y > best) {
			best = y
		}
	}
	return l, max(best, 0), r
}

type runLine struct {
	text string
	box  image.Rectangle
	capH int // 原版大寫字母與數字的最大墨跡高（邏輯像素），作為中文字級上限
}

// runLines 依 x 回捲切行；空白沒有墨跡，歸入目前行。
func runLines(chars []dialogChar) []runLine {
	var out []runLine
	var cur runLine
	lastX := -1
	for _, ch := range chars {
		if !ch.box.Empty() {
			if lastX >= 0 && ch.box.Min.X < lastX {
				out = append(out, cur)
				cur = runLine{}
			}
			lastX = ch.box.Min.X
			cur.box = cur.box.Union(ch.box)
			if (ch.c >= 'A' && ch.c <= 'Z') || (ch.c >= '0' && ch.c <= '9') {
				cur.capH = max(cur.capH, ch.box.Dy())
			}
		}
		if ch.c != 0 {
			cur.text += string(rune(ch.c))
		}
	}
	if !cur.box.Empty() {
		out = append(out, cur)
	}
	for i := range out {
		out[i].text = dialogNormalize(out[i].text)
		if out[i].capH == 0 {
			out[i].capH = out[i].box.Dy()
		}
	}
	return out
}

// runStyle 由原版觀測色號決定中文字色：有陰影色 47／128 為木紋框配色；
// 否則以各字主色中最多者為一般色、其次為強調色，不畫陰影。
func runStyle(r *dialogRun) (normal, accent, shadow byte) {
	if r.shadowWritten {
		return 68, 149, 47
	}
	count := map[byte]int{}
	for _, ch := range r.chars {
		best, n := byte(0), -1
		for c, k := range ch.colors {
			if k > n || (k == n && c < best) {
				best, n = c, k
			}
		}
		if n > 0 {
			count[best]++
		}
	}
	first, second, n1, n2 := byte(0), byte(0), -1, -1
	for c, k := range count {
		switch {
		case k > n1 || (k == n1 && c < first):
			second, n2 = first, n1
			first, n1 = c, k
		case k > n2 || (k == n2 && c < second):
			second, n2 = c, k
		}
	}
	if n2 <= 0 {
		second = first
	}
	return first, second, 0
}

// observedPitch 取相鄰行上緣距離的最小值（邏輯像素）；單行時回傳 fallback。
func observedPitch(lines []runLine, fallback int) int {
	p := 0
	for i := 1; i < len(lines); i++ {
		if d := lines[i].box.Min.Y - lines[i-1].box.Min.Y; d > 0 && (p == 0 || d < p) {
			p = d
		}
	}
	if p == 0 {
		return fallback
	}
	return p
}

// finish 對一段已結束的逐字事件做比對與版面；回傳要顯示的狀態，或原因（無墨跡時兩者皆空）。
func (d *dialogRuntime) finish(r *dialogRun, canvas []byte, step uint64) (*dialogShown, string, string) {
	if r == nil || r.readPos%2 == 1 {
		return nil, "", ""
	}
	lines := runLines(r.chars)
	if len(lines) == 0 {
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
	before := bytes.Clone(canvas)
	for i, text := range r.lastText {
		if text {
			before[i] = r.firstOld[i]
		}
	}
	normalC, accentC, shadowC := runStyle(r)
	st := &dialogShown{before: before, normalC: normalC, accentC: accentC, shadowC: shadowC,
		phase: "waiting-screen", complete: step}
	t, zh, why := d.cat.matchIn(d.cat.templates, shown)
	switch {
	case why == "" && t.centered:
		// 置中段落（例如國王接見）：沒有色號 0 外框，安全區取原版墨跡外擴 2 邏輯像素。
		st.safe = ink.Inset(-2).Intersect(image.Rect(0, 0, 320, 200))
		st.shadow, st.normal, st.accent, st.size = d.cat.centeredMasks(zh, st.safe.Dx()*4, st.safe.Dy()*4,
			observedPitch(lines, 10)*4, shadowC != 0)
	case why == "":
		// 目標170：有色號 0 外框即可，不再要求陰影色（港口說明框、訓練對話框無陰影）。
		last := lines[len(lines)-1].box
		l, top, rt := scanDialogBox(before, last.Min.X, (last.Min.Y+last.Max.Y)/2, lines[0].box.Min.X, lines[0].box.Max.X, lines[0].box.Min.Y)
		st.safe = image.Rect(l+3, top+3, rt-3, ink.Max.Y+2)
		if l == 0 || top == 0 || rt == 319 || !ink.In(st.safe) {
			return nil, shown, "ink-outside-box"
		}
		// 目標167：印字期間其他寫入者（例如顧問肖像壓在框上）不撤銷；逐點以最後寫入者重建印前底圖，
		// 只還原最後由改色常式寫下的像素，肖像像素保留原版印後值。
		capH := 0
		for _, l := range lines {
			capH = max(capH, l.capH)
		}
		st.shadow, st.normal, st.accent, st.size = d.cat.dialogMasks(zh, st.safe.Dx()*4, st.safe.Dy()*4, capH)
		if st.shadow != nil && shadowC == 0 {
			st.shadow = image.NewAlpha(st.shadow.Rect) // 原版無陰影
		}
	case why == "no-template":
		// 逐行清單：每一行都必須各自唯一命中；任何一行不中即整段回原文。
		items := make([]string, len(lines))
		for i, l := range lines {
			lt, lzh, lwhy := d.cat.matchIn(d.cat.lines, l.text)
			if lwhy != "" {
				return nil, shown, "line-" + lwhy
			}
			items[i] = lzh
			t = lt
		}
		var union image.Rectangle
		for _, l := range lines {
			union = union.Union(l.box)
		}
		st.safe = image.Rect(union.Min.X-1, union.Min.Y-1, union.Max.X+2, union.Max.Y+2).Intersect(image.Rect(0, 0, 320, 200))
		st.shadow, st.normal, st.accent, st.size = d.cat.lineMasks(items, lines, st.safe, observedPitch(lines, union.Dy()+3), shadowC != 0)
		if len(lines) == 1 {
			st.id = t.id
		} else {
			st.id = t.id + "+list"
		}
		st.zh = strings.Join(items, "／")
		if st.size == 0 {
			return nil, shown, "layout-overflow"
		}
		return st, shown, ""
	default:
		return nil, shown, why
	}
	if st.size == 0 {
		return nil, shown, "layout-overflow"
	}
	st.id, st.zh = t.id, zh
	return st, shown, ""
}

// lineMasks 逐行在原位畫中文：行左緣對齊原版字首、字頭對齊原版行上緣；
// 中文墨跡高不超過原版大寫字墨跡高的 4 倍（逐段取最大者），也不超過行距；
// 寬度不得超過整段最右緣。任一行放不下即整段回原文。
func (c *dialogCatalog) lineMasks(items []string, lines []runLine, safe image.Rectangle, pitch int, shadow bool) (sh, n, ac *image.Alpha, size int) {
	rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
	capH := 0
	for _, l := range lines {
		capH = max(capH, l.capH)
	}
	start, floor := dialogSizes(capH)
	for size = start; size >= floor; size-- {
		f := c.fonts[size]
		if f == nil || f.cjkBottom-f.cjkTop > pitch*4-4 || f.cjkBottom-f.cjkTop > capH*4 {
			continue
		}
		sh, n, ac = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		ok := true
		for i, l := range lines {
			glyphs, good := dialogMarked(items[i])
			x, y := (l.box.Min.X-safe.Min.X)*4, (l.box.Min.Y-safe.Min.Y)*4-f.cjkTop
			w := 0
			for _, g := range glyphs {
				gw, has := f.widths[g.r]
				if !has {
					good = false
					break
				}
				w += gw
			}
			if !good || x+w+4 > rect.Dx() || y+f.cjkBottom > rect.Dy() {
				ok = false
				break
			}
			for _, g := range glyphs {
				a := f.glyphs[g.r]
				dialogBlit(n, a, x, y)
				if shadow {
					dialogBlit(sh, a, x+4, y+4)
				}
				if g.accent {
					dialogBlit(ac, a, x, y)
				}
				x += f.widths[g.r]
			}
		}
		if ok {
			return sh, n, ac, size
		}
	}
	return nil, nil, nil, 0
}

// centeredMasks 排版含 ^ 置中碼的譯稿：^^ 開頭的行置中、單獨的 ^ 為空行、其餘相鄰行合併後依寬度重排。
// 行距取原版觀測行距（輸出像素）；字級以行距為上限並逐級縮到下限。
func (c *dialogCatalog) centeredMasks(zh string, w, h, pitch int, shadow bool) (sh, n, ac *image.Alpha, size int) {
	type item struct {
		text     string
		centered bool
		blank    bool
	}
	var items []item
	body := ""
	flush := func() {
		if body != "" {
			items = append(items, item{text: body})
			body = ""
		}
	}
	for _, l := range strings.Split(zh, `\n`) {
		switch {
		case strings.HasPrefix(l, "^^"):
			flush()
			items = append(items, item{text: strings.TrimPrefix(l, "^^"), centered: true})
		case strings.TrimSpace(l) == "^":
			flush()
			items = append(items, item{blank: true})
		default:
			body += strings.TrimPrefix(l, "^")
		}
	}
	flush()
	rect := image.Rect(0, 0, w, h)
	for size = dialogFontPx; size >= dialogFloorPx; size-- {
		f := c.fonts[size]
		if f == nil || f.cjkBottom-f.cjkTop > pitch-4 {
			continue
		}
		type placed struct {
			glyphs   []dialogGlyph
			centered bool
		}
		var rows []*placed
		ok := true
		for _, it := range items {
			if it.blank {
				rows = append(rows, nil)
				continue
			}
			glyphs, good := dialogMarked(it.text)
			if !good {
				return nil, nil, nil, 0
			}
			wrapped, good := dialogWrap(glyphs, f, w-8)
			if !good {
				ok = false
				break
			}
			for _, g := range wrapped {
				rows = append(rows, &placed{g, it.centered})
			}
		}
		if !ok || 4+len(rows)*pitch > h {
			continue
		}
		sh, n, ac = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		for k, row := range rows {
			if row == nil {
				continue
			}
			lw := 0
			for _, g := range row.glyphs {
				lw += f.widths[g.r]
			}
			x, y := 4, 4+k*pitch-f.cjkTop
			if row.centered {
				x = (w - lw) / 2
			}
			for _, g := range row.glyphs {
				a := f.glyphs[g.r]
				dialogBlit(n, a, x, y)
				if shadow {
					dialogBlit(sh, a, x+4, y+4)
				}
				if g.accent {
					dialogBlit(ac, a, x, y)
				}
				x += f.widths[g.r]
			}
		}
		return sh, n, ac, size
	}
	return nil, nil, nil, 0
}
