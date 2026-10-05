package main

// 規格038：連續字串通用覆蓋。0D21:00C6 以遞增位址讀出、以 0 結尾的一串文字，
// 逐串比對模板與字典，在原版墨跡外擴 1 邏輯像素的安全區內改排中文；任一條件不成立即回原文。

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"image"
	"math"
	"regexp"
	"strconv"
	"strings"
	"unicode"
)

type stringTemplate struct {
	id    string
	re    *regexp.Regexp
	slots []string // 依出現順序：n1、w1、colony…
	zh    string
}

type woodcutTitle struct {
	id, zh string
}

type stringCatalog struct {
	dlg       *dialogCatalog    // 定稿術語、NAMES 對照與逐行模板（規格035／036）
	frags     map[string]string // 片段字典：英文→中文；衝突者為空字串（視為查無）
	templates []stringTemplate
	colony    map[string]string // COLONY.TXT 預設名→「中文（原名）」
	people    map[string]bool   // 目標170：NAMES.TXT @LEADERNAME 的元首名（玩家可改名，顯示原名）
	owned     map[string]bool   // 專屬欄位已處理的原文，本層不處理
	fonts     map[int]*dialogFont
	woodcut   map[string]woodcutTitle // 規格038：經原檔指紋驗證的事件標題。
	portRoles map[string]map[string]bool

	routeLand string // 規格038 READY：只供已驗第一路線Land欄。
	slotEmpty string // 規格038：只供存讀檔槽位，不加入通用字典。
}

const (
	stringGap      = 200000 // 同一串相鄰兩次讀取的最大間隔（步）
	stringMaxItems = 512
	stringFontPx   = 30 // 圖集字級範圍：原版大寫字高 7 的起始字級
	stringFloorPx  = 12
)

var (
	stringSlot   = regexp.MustCompile(`\{(n\d|w\d|colony|person)\}`)
	stringLetter = regexp.MustCompile(`[A-Za-z]`)
)

// tsvRows 同 splitTSV，但只有表頭時回空列表而不是錯誤。
func tsvRows(data []byte) []map[string]string {
	if rows := splitTSV(data); rows != nil {
		return rows
	}
	if t := strings.TrimRight(string(data), "\n"); t != "" && !strings.Contains(t, "\n") {
		return []map[string]string{}
	}
	return nil
}

// addFrag 加入片段字典；同一原文有兩個不同中文即視為查無。
func (c *stringCatalog) addFrag(en, zh string) {
	en, zh = strings.TrimRight(en, " "), strings.TrimSpace(zh)
	if en == "" || zh == "" {
		return
	}
	if old, ok := c.frags[en]; ok && old != zh {
		c.frags[en] = ""
		return
	}
	c.frags[en] = zh
}

// verifiedRaw 依原檔、位移、長度與片段雜湊取出原文；任一不符回錯誤。
func verifiedRaw(files map[string][]byte, file, fileSHA, offset, length, rawSHA, id string) (string, bool, error) {
	data, ok := files[file]
	if !ok {
		return "", false, nil
	}
	off, err1 := strconv.ParseInt(offset, 0, 64)
	n, err2 := strconv.Atoi(length)
	if fileSHA != fmt.Sprintf("%x", sha256.Sum256(data)) || err1 != nil || err2 != nil || off < 0 || int(off)+n > len(data) {
		return "", false, fmt.Errorf("%s 版本或位移不符：%s", file, id)
	}
	raw := data[off : int(off)+n]
	if fmt.Sprintf("%x", sha256.Sum256(raw)) != rawSHA {
		return "", false, fmt.Errorf("%s 片段雜湊不符：%s", file, id)
	}
	return string(raw), true, nil
}

// loadStringCatalog 建立片段字典（海上詞典、語料清冊與譯稿的 LABELS／NAMES／WOODCUT 單行列）、模板與殖民地名稱。
func loadStringCatalog(dlg *dialogCatalog, templates, sea, corpus, draft, colony []byte, files map[string][]byte) (*stringCatalog, error) {
	c := &stringCatalog{dlg: dlg, frags: map[string]string{}, colony: map[string]string{}, owned: map[string]bool{}, people: map[string]bool{}, woodcut: map[string]woodcutTitle{}}
	if names, ok := files["NAMES.TXT"]; ok {
		section := ""
		for _, line := range strings.Split(string(names), "\r\n") {
			switch {
			case strings.HasPrefix(line, "@"):
				section = line
			case section == "@LEADERNAME" && line != "" && !strings.HasPrefix(line, ";"):
				c.people[strings.TrimSpace(strings.SplitN(line, ",", 2)[0])] = true
			}
		}
	}
	c.portRoles = portKinds(files["NAMES.TXT"])
	single := func(raw, zh string) bool {
		return zh != "" && !strings.Contains(raw, "\r\n") && !strings.ContainsAny(raw, "~#@^") && !strings.ContainsAny(zh, "~#^{}")
	}
	rows := tsvRows(sea)
	if rows == nil {
		return nil, fmt.Errorf("海上詞典欄位不符")
	}
	for _, r := range rows {
		raw, ok, err := verifiedRaw(files, r["source_file"], r["source_sha256"], r["byte_offset"], r["source_byte_length"], r["source_bytes_sha256"], r["candidate_id"])
		if err != nil {
			return nil, err
		}
		if ok && r["role"] != "menu" && single(raw, r["zh_hant"]) {
			c.addFrag(raw, r["zh_hant"])
		}
	}
	rows = tsvRows(corpus)
	if rows == nil {
		return nil, fmt.Errorf("語料清冊欄位不符")
	}
	for _, r := range rows {
		f := r["source_file"]
		if f != "LABELS.TXT" && f != "WOODCUT.TXT" {
			continue
		}
		raw, ok, err := verifiedRaw(files, f, r["source_file_sha256"], r["text_offset"], r["text_byte_length"], r["source_bytes_sha256"], r["message_id"])
		if err != nil {
			return nil, err
		}
		if ok && single(raw, r["zh_hant"]) {
			c.addFrag(raw, r["zh_hant"])
			if f == "WOODCUT.TXT" {
				c.addWoodcut(raw, r["message_id"], r["zh_hant"])
			}
			if r["message_id"] == "LABELS.TXT:@ROUTE:0x00000B2A" && r["text_offset"] == "0x00000B2A" && r["text_byte_length"] == "4" && raw == "Land" {
				c.routeLand = r["zh_hant"]
			}
		}
	}
	rows = tsvRows(draft)
	if rows == nil {
		return nil, fmt.Errorf("譯稿 TSV 欄位不符")
	}
	if err := c.loadSlotEmpty(rows, files); err != nil {
		return nil, err
	}
	for _, r := range rows {
		f := r["source_file"]
		if f != "LABELS.TXT" && f != "WOODCUT.TXT" && f != "NAMES.TXT" && f != "PEDIA.TXT" && f != "MENU.TXT" {
			continue
		}
		raw, ok, err := verifiedRaw(files, f, r["source_sha256"], r["byte_offset"], r["source_byte_length"], r["source_bytes_sha256"], r["candidate_id"])
		if err != nil {
			return nil, err
		}
		// 目標170：MENU.TXT 選單項目與 PEDIA.TXT 類別名（百科副標）也收；MENU 項目去掉前導縮排。
		if ok && !strings.Contains(raw, ",") && single(raw, r["zh_hant"]) {
			c.addFrag(strings.TrimLeft(raw, " "), r["zh_hant"])
			if f == "WOODCUT.TXT" {
				c.addWoodcut(raw, r["candidate_id"], r["zh_hant"])
			}
		}
	}
	rows = tsvRows(colony)
	if rows == nil {
		return nil, fmt.Errorf("殖民地名稱清冊欄位不符")
	}
	for _, r := range rows {
		raw, ok, err := verifiedRaw(files, "COLONY.TXT", r["source_member_sha256"], r["text_offset"], r["text_byte_length"], r["source_bytes_sha256"], r["message_id"])
		if err != nil {
			return nil, err
		}
		name, zh := r["source_name"], r["zh_hant"]
		cut := strings.Index(zh, "（")
		if !ok || name == "" || cut <= 0 || !strings.Contains(raw, name) {
			if ok {
				return nil, fmt.Errorf("殖民地名稱不符：%s", r["message_id"])
			}
			continue
		}
		// 使用者 2026-09-28 決定：預設名顯示「中文（原名）」，不含年份。
		c.colony[name] = zh[:cut] + "（" + name + "）"
	}
	rows = tsvRows(templates)
	if rows == nil {
		return nil, fmt.Errorf("字串模板表欄位不符")
	}
	seen := map[string]bool{}
	for _, r := range rows {
		t, err := makeStringTemplate(r["template_id"], r["pattern_en"], r["zh_hant"])
		if err != nil || seen[t.id] {
			return nil, fmt.Errorf("字串模板不符：%s", r["template_id"])
		}
		seen[t.id] = true
		c.templates = append(c.templates, t)
	}
	return c, nil
}

// addOwned 記下已由專屬欄位處理的譯稿鍵之原文（設計第 8 點）；這些字串本層不處理。ids 為 nil 時整表都收（例如旗卡片段表）。
func (c *stringCatalog) addOwned(draft []byte, files map[string][]byte, ids map[string]bool) error {
	for _, r := range splitTSV(draft) {
		if ids != nil && !ids[r["candidate_id"]] {
			continue
		}
		raw, ok, err := verifiedRaw(files, r["source_file"], r["source_sha256"], r["byte_offset"], r["source_byte_length"], r["source_bytes_sha256"], r["candidate_id"])
		if err != nil {
			return err
		}
		if ok {
			c.owned[strings.Trim(raw, " ")] = true
		}
	}
	return nil
}

// isOwned 判斷字串是否由專屬欄位處理：去頭尾空白後相同，或去掉一層外括號後相同（原版在片段外加括號印出）。
func (c *stringCatalog) isOwned(text string) bool {
	t := strings.Trim(text, " ")
	if c.owned[t] {
		return true
	}
	return strings.HasPrefix(t, "(") && strings.HasSuffix(t, ")") && c.owned[strings.Trim(t[1:len(t)-1], " ")]
}

// makeStringTemplate 把原文樣式轉成正規式：{nK} 為十進位數字（可含逗號），{wK}、{colony} 為非貪婪任意字；其餘逐字相同。
func makeStringTemplate(id, pattern, zh string) (stringTemplate, error) {
	t := stringTemplate{id: id, zh: zh}
	var b strings.Builder
	b.WriteString("^")
	last := 0
	for _, m := range stringSlot.FindAllStringSubmatchIndex(pattern, -1) {
		b.WriteString(regexp.QuoteMeta(pattern[last:m[0]]))
		name := pattern[m[2]:m[3]]
		if name[0] == 'n' {
			b.WriteString(`([0-9][0-9,]*)`)
		} else {
			b.WriteString(`(.+?)`)
		}
		t.slots = append(t.slots, name)
		last = m[1]
	}
	b.WriteString(regexp.QuoteMeta(pattern[last:]) + "$")
	if id == "" || zh == "" || len(t.slots) == 0 {
		return t, fmt.Errorf("空模板")
	}
	for _, m := range stringSlot.FindAllStringSubmatch(zh, -1) {
		found := false
		for _, s := range t.slots {
			found = found || s == m[1]
		}
		if !found {
			return t, fmt.Errorf("譯文槽位不在原文")
		}
	}
	re, err := regexp.Compile(b.String())
	t.re = re
	return t, err
}

// lookup 查一個片段：片段字典、定稿術語與 NAMES 對照；查無或衝突回空字串。
// 目標172：全大寫的片段（建造清單 ARMORY、PRINTING PRESS）查不到時，改查每字首字大寫的寫法。
func (c *stringCatalog) lookup(en string) string {
	if zh := c.lookupExact(en); zh != "" {
		return zh
	}
	if strings.ToUpper(en) == en && strings.ToLower(en) != en {
		words := strings.Split(strings.ToLower(en), " ")
		for i, w := range words {
			if w != "" {
				words[i] = strings.ToUpper(w[:1]) + w[1:]
			}
		}
		return c.lookupExact(strings.Join(words, " "))
	}
	return ""
}

func (c *stringCatalog) lookupExact(en string) string {
	if zh := c.frags[en]; zh != "" {
		return zh
	}
	if c.dlg != nil {
		return c.dlg.terms[en]
	}
	return ""
}

// translate 依設計第 4 點把一串原文換成中文；回傳原因（空字串表示成功）。
func (c *stringCatalog) translate(text string) (zh, id, reason string) {
	t := strings.Trim(text, " ") // 前導縮排與尾端空白都不佔墨跡
	// 目標170：整串精確相同者優先（殖民地名稱、片段字典），再試模板，最後逐行模板。
	if zh, ok := c.colony[t]; ok {
		return zh, "colony", ""
	}
	if zh := c.lookup(t); zh != "" {
		return zh, "dictionary", ""
	}
	var hits []string
	var hitID string
	for _, tpl := range c.templates {
		if strings.HasPrefix(tpl.id, "cargo-") || strings.HasPrefix(tpl.id, "port-field-") || tpl.id == "route-editor-title" {
			continue
		} // 規格038 READY：貨物與港口模板只由專屬欄位回呼代入。
		m := tpl.re.FindStringSubmatch(t)
		if m == nil {
			continue
		}
		vals := map[string]string{}
		ok := true
		for i, s := range tpl.slots {
			v := m[i+1]
			switch {
			case s[0] == 'n':
			case s == "colony":
				if zh, has := c.colony[v]; has {
					v = zh
				}
			case s == "person":
				ok = ok && c.people[v]
			default:
				v = c.lookup(v)
				ok = ok && v != ""
			}
			vals[s] = v
		}
		if ok {
			hits = append(hits, stringSlot.ReplaceAllStringFunc(tpl.zh, func(s string) string { return vals[s[1:len(s)-1]] }))
			hitID = tpl.id
		}
	}
	switch {
	case len(hits) == 1:
		return hits[0], "template:" + hitID, ""
	case len(hits) > 1:
		// 目標172：多列命中但譯文完全相同（例如泛用與專用模板給出同一句），視為命中。
		for _, h := range hits[1:] {
			if h != hits[0] {
				return "", "", "ambiguous-template"
			}
		}
		return hits[0], "template:" + hitID, ""
	}
	if c.dlg != nil {
		if tpl, zh, why := c.dlg.matchIn(c.dlg.lines, t); why == "" {
			return strings.NewReplacer("{", "", "}", "").Replace(zh), tpl.id, ""
		}
	}
	return "", "", "no-template"
}

// stringStartPx 依原版大寫字高量起始字級：⌊capH×4.4⌋（字高 5→22px、7→30px），下限為其 2/3。
func stringStartPx(capH int) (start, floor int) {
	start = capH * 44 / 10
	floor = int(math.Ceil(float64(start) * 2 / 3))
	return start, floor
}

// stringMasks 單行排版：靠原版墨跡左緣，中文墨跡頂端對齊原版墨跡頂端；寬度放不下即逐級縮字。
// limitRight 是右界（輸出像素，相對安全區左緣）；shadow 為陰影位移（0 表示不畫陰影）。
func (c *stringCatalog) stringMasks(prefix, zh string, ink, safe image.Rectangle, capH, limitRight, shadow int) (sh, n, ac *image.Alpha, size int) {
	full := prefix + zh
	nPrefix := len([]rune(prefix))
	start, floor := stringStartPx(capH)
	rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
	for size = start; size >= floor; size-- {
		f := c.fonts[size]
		if f == nil || f.cjkBottom-f.cjkTop > capH*4+4 {
			continue
		}
		x, y := (ink.Min.X-safe.Min.X)*4, (ink.Min.Y-safe.Min.Y)*4-f.cjkTop
		w := 0
		good := true
		for _, r := range full {
			gw, has := f.widths[r]
			if !has {
				good = false
				break
			}
			w += gw
		}
		if !good {
			return nil, nil, nil, 0
		}
		pad := shadow
		if shadow < 0 {
			pad = -shadow
		}
		if x+w+pad > limitRight || y+f.cjkBottom+pad > rect.Dy() || y+f.cjkTop-max(-shadow, 0) < 0 || x-max(-shadow, 0) < 0 {
			continue
		}
		// 安全區只延伸到中文實際需要的寬度（不少於原版墨跡外擴 1 像素），避免把之後畫的圖示包進比對範圍。
		need := max(rect.Dx()-(safe.Max.X-ink.Max.X-1)*4, x+w+pad)
		if safe.Max.X > ink.Max.X+1 {
			rect.Max.X = min(rect.Dx(), (need+3)/4*4)
		}
		sh, n, ac = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		for i, r := range []rune(full) {
			a := f.glyphs[r]
			if i < nPrefix {
				dialogBlit(ac, a, x, y)
			} else {
				dialogBlit(n, a, x, y)
			}
			if shadow > 0 {
				dialogBlit(sh, a, x+shadow, y+shadow)
			} else if shadow < 0 {
				for _, d := range [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}, {-1, -1}, {1, 1}, {-1, 1}, {1, -1}} {
					dialogBlit(sh, a, x+d[0]*-shadow, y+d[1]*-shadow)
				}
			}
			x += f.widths[r]
		}
		return sh, n, ac, size
	}
	return nil, nil, nil, 0
}

// ---- 執行期（設計第 1、2、7 點）----

type stringRun struct {
	cargo cargoProof

	base, next  uint32
	start, last uint64
	text        []byte
	boxes       []image.Rectangle
	colors      map[byte]int
	firstOld    map[int]byte
	lastVal     map[int]byte
	others      image.Rectangle
	keyColor    byte                       // 目標170：熱鍵首字母另成一串時合併進來的首字母色號（0 表示沒有）
	keyNext     byte                       // 首字母後其餘字母的色號
	outline     bool                       // 目標170：同一串以 1 像素位移重印數次的描邊字
	outlineC    byte                       // 描邊色（先印的幾次）
	outlineInk  image.Rectangle            // 各次重印墨跡的聯集
	buf2        bool                       // 目標178：墨跡寫進離屏地圖緩衝區（0x3BB00）而非畫布
	mixed       bool                       // 目標178：同一串同時有畫布與緩衝區的墨跡寫入
	charColor   []map[byte]image.Rectangle // 目標178：緩衝區串每個字元各色號的墨跡
}

type stringItem struct {
	id, text, zh string
	ink, safe    image.Rectangle
	color        byte
	accentColor  byte // 目標170：熱鍵按鈕「(R)」的色號
	shadowColor  byte // 陰影或描邊色號
	size         int
	shadowOff    int
	shadow, norm *image.Alpha
	accent       *image.Alpha
	before       []byte // 印前畫布的安全區（本串文字像素已還原）
	after        []byte // 完成時畫布的安全區
	phase        string // waiting-copy（目標178）、waiting-screen、active、suspended
	complete     uint64
	appliedFrame int
}

type stringRuntime struct {
	cargo cargoAssembly

	cat      *stringCatalog
	cur      *stringRun
	key      *stringRun // 目標170：暫存的單字母字串，等待與緊接的同列字串合併
	last     *stringRun // 目標170：上一串（描邊字比對用）
	items    []*stringItem
	misses   map[string]int
	reason   string
	accepted int
}

// translateObserved 只在原版百科標題像素仍完整時消除 Savannah 的名稱歧義（規格038目標180）。
func (s *stringRuntime) translateObserved(text string, canvas []byte) (zh, id, reason string) {
	if strings.Trim(text, " ") == "Savannah" {
		for _, item := range s.items {
			if item.text == "ENCYCLOPEDIA OF COLONIZATION" && !item.safe.Empty() &&
				bytes.Equal(stringRect(canvas, item.safe), item.after) {
				if zh := s.cat.lookup("Savannah"); zh != "" {
					return zh, "dictionary:pedia-terrain", ""
				}
			}
		}
	}
	return s.cat.translate(text)
}

// onRead 處理一次 0D21:00C6 讀取；回傳完成的一串（讀到 0）。
func (s *stringRuntime) onRead(a uint32, v byte, step uint64) *stringRun {
	if s.cur == nil || a != s.cur.next || step-s.cur.last >= stringGap {
		s.cur = &stringRun{base: a, start: step, colors: map[byte]int{}, firstOld: map[int]byte{}, lastVal: map[int]byte{}}
	}
	r := s.cur
	if v == 0 {
		s.cur = nil
		return r
	}
	r.text = append(r.text, v)
	r.boxes = append(r.boxes, image.Rectangle{})
	r.charColor = append(r.charColor, nil)
	r.next, r.last = a+1, step
	return nil
}

// onWrite 記錄畫布寫入：text 表示 0D21:012C，cursor 表示游標常式在游標附近。
func (s *stringRuntime) onWrite(i int, old, value byte, text, cursor bool) {
	s.write(i, old, value, text, cursor, false)
}

// onWriteBuf 記錄離屏地圖緩衝區（0x3BB00 起，位移與畫布一致）的寫入（目標178，規格038 附記）：只計 0D21:012C 的墨跡。
func (s *stringRuntime) onWriteBuf(i int, old, value byte, text bool) {
	if text {
		s.write(i, old, value, true, false, true)
	}
}

func (s *stringRuntime) write(i int, old, value byte, text, cursor, buf2 bool) {
	r := s.cur
	if r == nil || len(r.text) == 0 {
		return
	}
	p := image.Rect(i%320, i/320, i%320+1, i/320+1)
	if !text {
		if !cursor {
			r.others = r.others.Union(p)
		}
		return
	}
	if len(r.firstOld) > 0 && r.buf2 != buf2 {
		r.mixed = true
		return
	}
	r.buf2 = buf2
	if _, seen := r.firstOld[i]; !seen {
		r.firstOld[i] = old
	}
	r.lastVal[i] = value
	r.colors[value]++
	n := len(r.boxes) - 1
	r.boxes[n] = r.boxes[n].Union(p)
	if buf2 {
		if r.charColor[n] == nil {
			r.charColor[n] = map[byte]image.Rectangle{}
		}
		r.charColor[n][value] = r.charColor[n][value].Union(p)
	}
}

func stringRect(buf []byte, r image.Rectangle) []byte {
	b := make([]byte, 0, r.Dx()*r.Dy())
	for y := r.Min.Y; y < r.Max.Y; y++ {
		b = append(b, buf[y*320+r.Min.X:y*320+r.Max.X]...)
	}
	return b
}

// join 處理熱鍵按鈕：單一字母的一串先暫存；緊接的下一串若在同一基線、左緣緊貼（間隔 0～3 像素）、
// 色號不同且兩串各自單色，就合併成一串並記下首字母色號。回傳要交給 finish 的一串（暫存時回傳 nil）。
func (s *stringRuntime) join(r *stringRun) *stringRun {
	var ink image.Rectangle
	for _, b := range r.boxes {
		ink = ink.Union(b)
	}
	k := s.key
	s.key = nil
	if len(r.text) == 1 && stringLetter.Match(r.text) && !ink.Empty() && len(r.colors) == 1 {
		s.key = r
		return nil
	}
	if k == nil || len(r.colors) != 1 || ink.Empty() || r.start-k.last >= stringGap {
		return r
	}
	var kink image.Rectangle
	for _, b := range k.boxes {
		kink = kink.Union(b)
	}
	gap := ink.Min.X - kink.Max.X
	var kc, rc byte
	for c := range k.colors {
		kc = c
	}
	for c := range r.colors {
		rc = c
	}
	if gap < 0 || gap > 3 || abs(ink.Max.Y-kink.Max.Y) > 1 || kc == rc {
		return r
	}
	m := &stringRun{base: k.base, next: r.next, start: k.start, last: r.last, text: append(append([]byte{}, k.text...), r.text...),
		boxes: append(append([]image.Rectangle{}, k.boxes...), r.boxes...), colors: map[byte]int{rc: r.colors[rc]},
		firstOld: map[int]byte{}, lastVal: map[int]byte{}, others: k.others.Union(r.others), keyColor: kc, keyNext: rc}
	for _, src := range []*stringRun{k, r} {
		for i, v := range src.firstOld {
			if _, seen := m.firstOld[i]; !seen {
				m.firstOld[i] = v
			}
		}
		for i, v := range src.lastVal {
			m.lastVal[i] = v
		}
	}
	return m
}

// outline 處理描邊字：與上一串文字相同、墨跡左上角位移不超過 1 像素、且在 100,000 步內，即併成一串：
// 墨跡取聯集、印前值保留最早者，先印者的色號當描邊色，最後一次的色號當字色。
func (s *stringRuntime) outline(r *stringRun) *stringRun {
	l := s.last
	s.last = r
	if l == nil || string(l.text) != string(r.text) || len(r.colors) != 1 || r.start < l.last || r.start-l.last >= 100000 {
		return r
	}
	var li, ri image.Rectangle
	for _, b := range l.boxes {
		li = li.Union(b)
	}
	for _, b := range r.boxes {
		ri = ri.Union(b)
	}
	if li.Empty() || ri.Empty() || abs(li.Min.X-ri.Min.X) > 1 || abs(li.Min.Y-ri.Min.Y) > 1 {
		return r
	}
	oc := l.outlineC
	if !l.outline {
		if len(l.colors) != 1 {
			return r
		}
		for c := range l.colors {
			oc = c
		}
	}
	m := *r
	m.outline, m.outlineC = true, oc
	m.outlineInk = li.Union(l.outlineInk).Union(ri)
	m.firstOld, m.lastVal = map[int]byte{}, map[int]byte{}
	for i, v := range l.firstOld {
		m.firstOld[i] = v
	}
	for i, v := range r.firstOld {
		if _, seen := m.firstOld[i]; !seen {
			m.firstOld[i] = v
		}
	}
	for _, src := range []*stringRun{l, r} {
		for i, v := range src.lastVal {
			m.lastVal[i] = v
		}
	}
	m.others = l.others.Union(r.others)
	s.last = &m
	return &m
}

func abs(v int) int {
	if v < 0 {
		return -v
	}
	return v
}

// finish 依設計第 3～6 點處理一串完成的文字；回傳新項目，或原因（空字串且無項目表示不需處理）。
// panel 非空時，落在其中的字串沿用規格032 狀態欄樣式：右界延伸到欄邊、黑色陰影向右下 2 輸出像素。
func (s *stringRuntime) finish(r *stringRun, canvas []byte, step uint64, panel image.Rectangle) (*stringItem, string) {
	text := string(r.text)
	if len(stringLetter.FindAllString(text, 2)) < 2 {
		return nil, ""
	}
	var ink image.Rectangle
	capH := 0
	for i, b := range r.boxes {
		ink = ink.Union(b)
		if c := rune(text[i]); unicode.IsUpper(c) || unicode.IsDigit(c) {
			capH = max(capH, b.Dy())
		}
	}
	if ink.Empty() {
		return nil, ""
	}
	if s.cat.isOwned(text) {
		return nil, "owned-by-field"
	}
	if len(r.colors) != 1 {
		return s.finishWoodcut(r, ink, capH, canvas, step)
	}
	var color byte
	for c := range r.colors {
		color = c
	}
	if capH == 0 {
		capH = ink.Dy()
	}
	face := ink
	ink = ink.Union(r.outlineInk)
	safe := ink.Inset(-1).Intersect(image.Rect(0, 0, 320, 200))
	if r.others.Overlaps(safe) {
		return nil, "other-writer"
	}
	zh, id, why := s.translateObserved(text, canvas)
	if value, key, ok := s.routeTitleTranslate(text, face, capH, color); ok {
		zh, id, why = value, key, ""
	}
	if value, ok := s.routeLandTranslate(text, face, capH, color, canvas); ok {
		zh, id, why = value, "dictionary:route-land", ""
	}
	gridField := false
	if value, area, ok := s.routeGridTranslate(text, face, capH, color, canvas); ok {
		gridField = true
		zh, id, why, safe = value, "route-grid-colony", "", area
	}
	if cargoZH, cargoID, cargoWhy, handled := s.cargoTranslate(r, ink, capH, color); handled {
		zh, id, why = cargoZH, cargoID, cargoWhy
	}
	if value, key, ok := s.portFieldTranslate(r, face, capH, color, canvas); ok {
		zh, id, why = value, key, ""
	}
	if why != "" {
		return nil, why
	}
	prefix := ""
	if r.keyColor != 0 {
		// 熱鍵按鈕依規格032 選單列樣式：「(R)」用首字母原色，中文用其餘字母原色。
		prefix = "(" + string(r.text[0]) + ")"
	}
	limit, shadow := safe.Dx()*4, 0
	if !panel.Empty() && ink.In(panel) {
		// 設計第 6 點（狀態欄樣式）：安全區延伸到欄右緣，右界留 2 輸出像素給陰影。
		safe = image.Rect(safe.Min.X, safe.Min.Y, panel.Max.X, safe.Max.Y)
		limit, shadow = safe.Dx()*4, 2
	}
	shadowC := byte(0)
	if r.outline {
		shadow, shadowC = -4, r.outlineC // 負值：描邊（字形向四周各擴 4 輸出像素）
	}
	sh, n, ac, size := s.cat.stringMasks(prefix, zh, face, safe, capH, limit, shadow)
	if n == nil {
		return nil, "does-not-fit"
	}
	safe.Max.X = safe.Min.X + n.Rect.Dx()/4
	if gridField && r.others.Overlaps(safe) {
		return nil, "other-writer"
	}
	before := make([]byte, len(canvas))
	copy(before, canvas)
	for i, v := range r.firstOld {
		before[i] = v
	}
	return &stringItem{id: "STRING:" + id, text: text, zh: prefix + zh, ink: ink, safe: safe, color: color, accentColor: r.keyColor, shadowColor: shadowC,
		size: size, shadowOff: shadow, shadow: sh, norm: n, accent: ac, before: stringRect(before, safe), after: stringRect(canvas, safe), phase: "waiting-screen", complete: step}, ""
}

// 地圖視窗（目標178）：標籤必須完整落在此範圍內。
var stringMapView = image.Rect(0, 8, 240, 190)

const (
	stringLabelWiden   = 16 // 中文標籤寬度上限：原版墨跡寬加此邏輯像素
	stringLabelOutline = 3  // 標籤外框向四周各擴的輸出像素
)

// labelMasks 地圖殖民地名稱標籤置中排版（規格038 目標178 附記規則 3）：以原版填色墨跡的水平中心置中，
// 字頭對齊填色墨跡上緣，外框色層 sh、填色層 n。回傳安全區（邏輯像素）；放不下或超出地圖視窗回 nil。
func (c *stringCatalog) labelMasks(zh string, fill, ink image.Rectangle, capH int) (sh, n *image.Alpha, safe image.Rectangle, size int) {
	start, floor := stringStartPx(capH)
	limit := (ink.Dx() + stringLabelWiden) * 4
	cx4 := (fill.Min.X + fill.Max.X) * 2
	for size = start; size >= floor; size-- {
		f := c.fonts[size]
		if f == nil || f.cjkBottom-f.cjkTop > capH*4+4 {
			continue
		}
		w := 0
		for _, r := range zh {
			gw, has := f.widths[r]
			if !has {
				return nil, nil, image.Rectangle{}, 0
			}
			w += gw
		}
		if w > limit {
			continue
		}
		x0 := cx4 - w/2
		top := fill.Min.Y*4 - f.cjkTop
		zhBox := image.Rect(x0-stringLabelOutline, top+f.cjkTop-stringLabelOutline, x0+w+stringLabelOutline, top+f.cjkBottom+stringLabelOutline)
		zhLogical := image.Rect(zhBox.Min.X/4-1, zhBox.Min.Y/4-1, (zhBox.Max.X+3)/4+1, (zhBox.Max.Y+3)/4+1)
		safe = ink.Inset(-1).Union(zhLogical)
		if !safe.In(stringMapView) {
			continue
		}
		rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
		sh, n = image.NewAlpha(rect), image.NewAlpha(rect)
		x := x0 - safe.Min.X*4
		y := top - safe.Min.Y*4
		for _, r := range zh {
			a := f.glyphs[r]
			dialogBlit(n, a, x, y)
			for _, d := range [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}, {-1, -1}, {1, 1}, {-1, 1}, {1, -1}} {
				dialogBlit(sh, a, x+d[0]*stringLabelOutline, y+d[1]*stringLabelOutline)
			}
			x += f.widths[r]
		}
		return sh, n, safe, size
	}
	return nil, nil, image.Rectangle{}, 0
}

// finishLabel 處理一串寫進離屏地圖緩衝區的文字（殖民地名稱標籤，規格038 目標178 附記）。
// b2 是離屏緩衝區在畫布座標下的 320×200 視圖（標籤已畫上）；canvas 為目前畫布。
func (s *stringRuntime) finishLabel(r *stringRun, b2, canvas []byte, step uint64) (*stringItem, string) {
	text := string(r.text)
	if len(stringLetter.FindAllString(text, 2)) < 2 {
		return nil, ""
	}
	if r.mixed {
		return nil, "mixed-buffers"
	}
	var ink image.Rectangle
	for _, b := range r.boxes {
		ink = ink.Union(b)
	}
	if ink.Empty() {
		return nil, ""
	}
	if len(r.colors) != 2 {
		return nil, "label-colors"
	}
	var fillC byte
	outline := false
	for c := range r.colors {
		if c == 0 {
			outline = true
		} else {
			fillC = c
		}
	}
	if !outline || fillC == 0 {
		return nil, "label-colors"
	}
	var fill image.Rectangle
	capH := 0
	for i, cb := range r.charColor {
		b := cb[fillC]
		fill = fill.Union(b)
		if c := rune(text[i]); unicode.IsUpper(c) || unicode.IsDigit(c) {
			capH = max(capH, b.Dy())
		}
	}
	if fill.Empty() {
		return nil, "label-colors"
	}
	if capH == 0 {
		capH = fill.Dy()
	}
	zh, id, why := s.cat.translate(text)
	if why != "" {
		return nil, why
	}
	if id != "colony" {
		return nil, "label-not-default-name"
	}
	sh, n, safe, size := s.cat.labelMasks(zh, fill, ink, capH)
	if n == nil {
		return nil, "does-not-fit"
	}
	before := make([]byte, len(b2))
	copy(before, b2)
	for i, v := range r.firstOld {
		before[i] = v
	}
	return &stringItem{id: "STRING:" + id, text: text, zh: zh, ink: ink, safe: safe, color: fillC, shadowColor: 0,
		size: size, shadowOff: -stringLabelOutline, shadow: sh, norm: n, before: stringRect(before, safe), after: stringRect(b2, safe),
		phase: "waiting-copy", complete: step}, ""
}

// add 加入新項目：原版墨跡與新項目重疊的舊項目（同位置重印）撤銷；超過上限先撤銷最舊者。回傳被撤銷的項目。
func (s *stringRuntime) add(it *stringItem) (dropped []*stringItem) {
	kept := s.items[:0]
	for _, old := range s.items {
		if old.ink.Overlaps(it.ink) {
			dropped = append(dropped, old)
		} else {
			kept = append(kept, old)
		}
	}
	s.items = append(kept, it)
	if len(s.items) > stringMaxItems {
		dropped = append(dropped, s.items[0])
		s.items = s.items[1:]
	}
	return dropped
}

// stringSame 比對 buf 在安全區內是否等於完成時的畫布；skip 範圍（游標）不比。
func stringSame(buf []byte, it *stringItem, skip image.Rectangle) bool {
	i := 0
	for y := it.safe.Min.Y; y < it.safe.Max.Y; y++ {
		for x := it.safe.Min.X; x < it.safe.Max.X; x++ {
			if buf[y*320+x] != it.after[i] && !image.Pt(x, y).In(skip) {
				return false
			}
			i++
		}
	}
	return true
}

// stringIntactMin 是暫停中項目仍繪製的門檻：原版英文墨跡至少這個比例未被改動（目標177）。
const stringIntactMin = 0.3

// stringIntact 回原版英文墨跡（印前與完成時不同的點）在 buf 中仍與完成時相同的比例。
func stringIntact(buf []byte, it *stringItem) float64 {
	i, ink, same := 0, 0, 0
	for y := it.safe.Min.Y; y < it.safe.Max.Y; y++ {
		for x := it.safe.Min.X; x < it.safe.Max.X; x++ {
			if it.before[i] != it.after[i] {
				ink++
				if buf[y*320+x] == it.after[i] {
					same++
				}
			}
			i++
		}
	}
	if ink == 0 {
		return 0
	}
	return float64(same) / float64(ink)
}

// step 每個畫格推進各項目的狀態（設計第 7 點）；回傳狀態改變的事件（項目、階段、原因）。
func (s *stringRuntime) step(canvas, vga []byte, cursor image.Rectangle, now uint64, mode13 bool) (changes [][3]any) {
	if s.cur != nil && now-s.cur.last >= stringGap {
		s.cur = nil
	}
	kept := s.items[:0]
	for _, it := range s.items {
		same := stringSame(canvas, it, cursor)
		switch {
		case !mode13:
			changes = append(changes, [3]any{it, "expired", "mode-changed"})
			continue
		case (it.phase == "waiting-copy" || it.phase == "suspended-copy") && same:
			// 目標178：標籤已從離屏緩衝區搬上畫布，起算螢幕同步。
			it.phase, it.complete = "waiting-screen", now
			if stringSame(vga, it, cursor) {
				it.phase = "active"
				s.accepted++
				changes = append(changes, [3]any{it, "active", ""})
			}
		case it.id == "STRING:colony" && it.phase == "waiting-copy" && now-it.complete > 3000000:
			it.phase = "suspended-copy"
			changes = append(changes, [3]any{it, "suspended-copy", "canvas-copy-occluded"})
		case it.phase == "waiting-copy" && now-it.complete > 3000000:
			changes = append(changes, [3]any{it, "expired", "canvas-copy-timeout"})
			continue
		case it.phase == "waiting-copy":
		case it.phase == "waiting-screen" && !same:
			changes = append(changes, [3]any{it, "expired", "canvas-changed-before-screen"})
			continue
		// 規格038：完整印字在畫布未改變時保留，真VGA同步才啟用。
		// 原版整頁組裝可能超過舊等待上限；容量仍由add限制為512項。
		case it.phase == "waiting-screen" && stringSame(vga, it, cursor):
			it.phase = "active"
			s.accepted++
			changes = append(changes, [3]any{it, "active", ""})
		case it.phase == "active" && !same:
			it.phase = "suspended"
			changes = append(changes, [3]any{it, "suspended", "canvas-changed"})
		case it.phase == "suspended" && same:
			it.phase = "active"
			changes = append(changes, [3]any{it, "active", "canvas-restored"})
		}
		kept = append(kept, it)
	}
	s.items = kept
	return changes
}

// overlapsAny 判斷 r 是否與任一矩形重疊。
func overlapsAny(r image.Rectangle, list []image.Rectangle) bool {
	for _, x := range list {
		if r.Overlaps(x) {
			return true
		}
	}
	return false
}

// 規格035 SAVEGOOD：原版複合存檔描述；只讀顯示，不改存檔資料。
var saveDescriptionPattern = regexp.MustCompile(`^(Discoverer|Explorer|Conquistador|Governor|Viceroy) (.+) of the (English|French|Spanish|Dutch) \((Spring|Autumn) ([0-9]+)\)$`)

func (c *stringCatalog) translateSaveDescription(text string) (string, bool) {
	m := saveDescriptionPattern.FindStringSubmatch(text)
	if m == nil {
		return "", false
	}
	for _, ch := range m[2] {
		if ch < 32 || ch > 126 || strings.ContainsRune("{}%", ch) {
			return "", false
		}
	}
	difficulty, nation, season := c.lookup(m[1]), c.lookup(m[3]), c.lookup(m[4])
	if difficulty == "" || nation == "" || season == "" {
		return "", false
	}
	return nation + difficulty + " " + m[2] + "（" + m[5] + "年" + season + "）", true
}

// 規格038 READY：原版已驗唯一片段，與全檔指紋一併限制在槽位專用入口。
const slotEmptyID = "VICEROY.EXE:0x0001FA8E"

func (c *stringCatalog) loadSlotEmpty(rows []map[string]string, files map[string][]byte) error {
	c.slotEmpty = ""
	seen := false
	for _, row := range rows {
		if row["candidate_id"] != slotEmptyID {
			continue
		}
		if seen {
			return fmt.Errorf("重複槽位空欄鍵：%s", slotEmptyID)
		}
		seen = true
		off, err := strconv.ParseInt(row["byte_offset"], 0, 64)
		if row["source_file"] != "VICEROY.EXE" || row["source_sha256"] != "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3" || err != nil || off != 129678 || row["source_byte_length"] != "7" || row["source_bytes_sha256"] != "9251e2d6e3d0ccd4ce35aa27a82a36251ad36af2cb17b229c34a3daa2f0cdaa7" {
			return fmt.Errorf("槽位空欄來源不符：%s", slotEmptyID)
		}
		raw, ok, err := verifiedRaw(files, row["source_file"], row["source_sha256"], row["byte_offset"], row["source_byte_length"], row["source_bytes_sha256"], slotEmptyID)
		if err != nil {
			return err
		}
		zh := strings.TrimSpace(row["zh_hant"])
		if ok && raw == "(EMPTY)" && zh != "" && !strings.ContainsAny(zh, "~#^{}%\r\n\t") {
			c.slotEmpty = zh
		}
	}
	return nil
}

var saveSlotDescription = regexp.MustCompile(`^(Discoverer|Explorer|Conquistador|Governor|Viceroy) (.+) of the (English|French|Spanish|Dutch), (Spring|Autumn) ([0-9]+)$`)

// 槽位清單由 dialogRuntime 限定上下文及列數，不供一般字串查詢。
func (c *stringCatalog) translateSaveSlot(text string) (string, bool) {
	if c.slotEmpty == "" {
		return "", false
	}
	if text == "(EMPTY)" {
		return c.slotEmpty, true
	}
	m := saveSlotDescription.FindStringSubmatch(text)
	if len(m) != 6 {
		return "", false
	}
	return c.translateSaveDescription(m[1] + " " + m[2] + " of the " + m[3] + " (" + m[4] + " " + m[5] + ")")
}

type cargoPart struct{ kind, text string }
type cargoProof struct {
	text, role string
	base       uint32
}
type cargoAssembly struct {
	parts       []cargoPart
	text        string
	headerStart uint32
	header      cargoProof
}

func cargoCString(mem []byte, a uint32) (string, bool) {
	if uint64(a)+128 > uint64(len(mem)) {
		return "", false
	}
	raw := mem[a : a+128]
	n := bytes.IndexByte(raw, 0)
	if n < 0 {
		return "", false
	}
	for _, v := range raw[:n] {
		if v < 32 || v > 126 {
			return "", false
		}
	}
	return string(raw[:n]), true
}

func cargoDigits(v string) bool {
	if len(v) == 0 || len(v) > 5 {
		return false
	}
	for _, c := range v {
		if c < '0' || c > '9' {
			return false
		}
	}
	return true
}

// 呼叫點0E2D:11CF；raw words與複製後記憶體的契約來自v142／v144。
func (a *cargoAssembly) observe(mem []byte, ss, bp uint16, code []byte) {
	signature := []byte{0xf2, 0xae, 0xf7, 0xd1, 0x2b, 0xf9, 0x8c, 0xc0, 0x8e, 0xd8, 0x8e, 0x46, 0x08, 0x87, 0xfe, 0x8b, 0x46, 0x06}
	if !bytes.HasPrefix(code, signature) {
		*a = cargoAssembly{}
		return
	}
	p := uint32(ss)*16 + uint32(bp)
	if uint64(p)+14 > uint64(len(mem)) {
		*a = cargoAssembly{}
		return
	}
	word := func(i uint32) uint16 { return uint16(mem[p+i]) | uint16(mem[p+i+1])<<8 }
	dst := uint32(word(8))*16 + uint32(word(6))
	src := uint32(word(12))*16 + uint32(word(10))
	before, ok := cargoCString(mem, dst)
	value, good := cargoCString(mem, src)
	if !ok || !good {
		if dst == 127988 || dst == a.headerStart {
			*a = cargoAssembly{}
		}
		return
	}
	if src == 317818 && value == "Loading" && before == "" {
		a.headerStart = dst
		a.header = cargoProof{}
		return
	}
	if dst == a.headerStart && src == 316238 && value == "Caravel" && (before == "Loading: " || before == "Loading:  ") {
		a.header = cargoProof{text: before + value, role: "header", base: dst}
		return
	}
	if dst != 127988 {
		return
	}
	if before == "" {
		a.parts = nil
		a.text = ""
	}
	if before != a.text {
		a.parts = nil
		a.text = ""
		return
	}
	kind := ""
	switch {
	case src == 320325 && value == "Loading":
		kind = "loading"
	case src == 320171 && value == "moved to":
		kind = "moved"
	case src == 315996 && value == "Furs":
		kind = "commodity"
	case src == 316238 && value == "Caravel":
		kind = "unit"
	case src == 140264 && value != "" && !strings.ContainsAny(value, "~#^{}\\"):
		kind = "city"
	case src == 116461 && value == " ":
		kind = "space"
	case word(12) == ss && word(10) >= 0xe000 && cargoDigits(value):
		kind = "number"
	}
	if kind == "" || len(a.parts) >= 8 {
		a.parts = nil
		a.text = ""
		return
	}
	a.parts = append(a.parts, cargoPart{kind, value})
	a.text += value
}

func (a *cargoAssembly) proof(mem []byte) cargoProof {
	raw, ok := cargoCString(mem, 127988)
	if ok && raw == a.text {
		kinds := make([]string, len(a.parts))
		for i, p := range a.parts {
			kinds[i] = p.kind
		}
		pattern := strings.Join(kinds, ",")
		if pattern == "loading,space,commodity,space" {
			return cargoProof{raw, "loading", 127988}
		}
		if pattern == "number,space,commodity,space,moved,space,unit,space" {
			return cargoProof{raw, "unit", 127988}
		}
		if pattern == "number,space,commodity,space,moved,space,city,space" {
			return cargoProof{raw, "city", 127988}
		}
	}
	return cargoProof{}
}

func (a *cargoAssembly) headerProof(mem []byte) cargoProof {
	raw, ok := cargoCString(mem, a.header.base)
	if ok && a.header.role == "header" && raw == a.header.text {
		return a.header
	}
	return cargoProof{}
}

func (s *stringRuntime) cargoTranslate(r *stringRun, ink image.Rectangle, capH int, color byte) (string, string, string, bool) {
	text := strings.Trim(string(r.text), " ")
	p := r.cargo
	if !cargoStatement(text) {
		return "", "", "", false
	}
	id := ""
	vals := map[string]string{}
	if s.cat == nil || s.cat.dlg == nil {
		return "", "", "cargo-name-unverified", true
	}
	if p.role == "header" && p.text == string(r.text) && capH == 5 && ((text == "Loading: Caravel" && ink == image.Rect(135, 132, 192, 138) && color == 57) || (text == "Loading:  Caravel" && ink == image.Rect(154, 120, 213, 126) && color == 69)) {
		id = "cargo-loading-header"
		text = dialogNormalize(text) // 規格038 READY：只正規化已驗header角色的模板輸入。
		vals["w1"] = s.cat.dlg.unitCaptionNames["Caravel"]
	} else if p.role != "" && strings.Trim(p.text, " ") == text && ink.Min.Y == 1 && ink.Max.Y == 7 && capH == 5 && color == 149 {
		switch p.role {
		case "loading":
			if text != "Loading Furs" {
				return "", "", "cargo-source-mismatch", true
			}
			id = "cargo-loading-commodity"
			vals["w1"] = s.cat.lookup("Furs")
		case "unit", "city":
			words := strings.SplitN(text, " Furs moved to ", 2)
			if len(words) != 2 || !cargoDigits(words[0]) {
				return "", "", "cargo-source-mismatch", true
			}
			vals["n1"], vals["w1"] = words[0], s.cat.lookup("Furs")
			if p.role == "unit" {
				if words[1] != "Caravel" {
					return "", "", "cargo-source-mismatch", true
				}
				id = "cargo-moved-unit"
				vals["w2"] = s.cat.dlg.unitCaptionNames["Caravel"]
			} else {
				id = "cargo-moved-city"
				vals["colony"] = words[1]
				if zh, ok := s.cat.colony[words[1]]; ok {
					vals["colony"] = zh
				}
			}
		}
	}
	if id == "" {
		if cargoStatement(text) {
			return "", "", "cargo-source-unverified", true
		}
		return "", "", "", false
	}
	for _, v := range vals {
		if v == "" {
			return "", "", "cargo-name-unverified", true
		}
	}
	for _, t := range s.cat.templates {
		if t.id != id {
			continue
		}
		if t.re.FindStringSubmatch(text) == nil {
			return "", "", "cargo-template-mismatch", true
		}
		zh := stringSlot.ReplaceAllStringFunc(t.zh, func(token string) string { return vals[token[1:len(token)-1]] })
		return zh, "template:" + id, "", true
	}
	return "", "", "cargo-template-missing", true
}

func cargoStatement(text string) bool {
	if strings.HasPrefix(text, "Loading:") || strings.HasPrefix(text, "Loading ") {
		return true
	}
	number, rest, ok := strings.Cut(text, " ")
	return ok && cargoDigits(number) && strings.Contains(rest, " moved to ")
}

// 規格038 READY：只放行完整、未遮擋的來源角色裝貨提示；其餘按住守門保持原契約。
func cargoHeldAllowed(it *stringItem, indexed []byte, cursor image.Rectangle, dialogs []image.Rectangle) bool {
	if it == nil || len(indexed) != 64000 || it.id != "STRING:template:cargo-loading-commodity" || it.text != "Loading Furs " || it.phase != "active" || it.size < 15 || it.size > 22 || it.safe != image.Rect(137, 0, 182, 8) {
		return false
	}
	if cursor.Overlaps(it.safe) {
		return false
	}
	for _, rect := range dialogs {
		if rect.Overlaps(it.safe) {
			return false
		}
	}
	return bytes.Equal(stringRect(indexed, it.safe), it.after)
}

// 規格038 READY：只採已觀測第一路線、原生位置與原VGA當次內容。
func (s *stringRuntime) routeEditorContext(canvas []byte) bool {
	if s == nil || s.cat == nil || len(canvas) != 64000 {
		return false
	}
	for _, it := range s.items {
		if it == nil || it.id != "STRING:template:route-editor-title" || it.text != "EDIT TRADE ROUTE 1" || it.safe != image.Rect(127, 4, 193, 11) || it.color != 15 || it.size < 15 || it.size > 22 || (it.phase != "active" && it.phase != "waiting-screen") || len(it.after) != (193-127)*(11-4) {
			continue
		}
		if bytes.Equal(stringRect(canvas, it.safe), it.after) {
			return true
		}
	}
	return false
}
func (s *stringRuntime) routeLandTranslate(text string, face image.Rectangle, capH int, color byte, canvas []byte) (string, bool) {
	if text != "Land" || face != image.Rect(55, 33, 70, 38) || capH != 5 || color != 15 || !s.routeEditorContext(canvas) || s.cat.routeLand == "" {
		return "", false
	}
	return s.cat.routeLand, true
}
func (s *stringRuntime) routePortTranslate(text string, lineIndex int, canvas []byte, title *dialogShown, step uint64) (string, bool) {
	if lineIndex != 0 || text != "London (England)" || !s.routeEditorContext(canvas) || title == nil || title.id != "GAME.TXT:0x00001CBB" || title.safe != image.Rect(66, 76, 176, 88) || title.size != 30 || (title.phase != "active" && title.phase != "waiting-screen") || step < title.complete || step-title.complete >= 2000000 || len(title.items) != 1 || title.items[0] != "Select a port to sail to:" {
		return "", false
	}
	port, country := s.cat.lookup("London"), s.cat.lookup("England")
	if port == "" || country == "" {
		return "", false
	}
	return port + "（" + country + "）", true
}

// 規格038 READY：標題模板不進通用匹配，玩家命名與其他欄位保持原有路徑。
func (s *stringRuntime) routeTitleTranslate(text string, face image.Rectangle, capH int, color byte) (string, string, bool) {
	if s == nil || s.cat == nil || text != "EDIT TRADE ROUTE 1" || face != image.Rect(128, 5, 192, 10) || capH != 5 || color != 15 || s.cat.lookup("EDIT TRADE ROUTE") == "" {
		return "", "", false
	}
	for _, tpl := range s.cat.templates {
		if tpl.id == "route-editor-title" && tpl.re.MatchString(text) {
			return strings.ReplaceAll(tpl.zh, "{n1}", "1"), "template:" + tpl.id, true
		}
	}
	return "", "", false
}

// 規格038 READY：已觀測第一路線的前兩個目的地城市欄。
func (s *stringRuntime) routeGridTranslate(text string, face image.Rectangle, capH int, color byte, canvas []byte) (string, image.Rectangle, bool) {
	if capH != 5 || color != 15 || !s.routeEditorContext(canvas) {
		return "", image.Rectangle{}, false
	}
	index, name, ok := strings.Cut(text, ".  ")
	if !ok {
		return "", image.Rectangle{}, false
	}
	start := image.Point{}
	bottom := 0
	switch index {
	case "1":
		start, bottom = image.Pt(11, 69), 75
	case "2":
		start, bottom = image.Pt(10, 89), 95
	default:
		return "", image.Rectangle{}, false
	}
	if face.Min != start || face.Max.X <= start.X || face.Max.X > 114 || face.Max.Y < bottom-1 || face.Max.Y > bottom {
		return "", image.Rectangle{}, false
	}
	zh, known := s.cat.colony[name]
	if !known || zh == "" {
		return "", image.Rectangle{}, false
	}
	safe := face.Inset(-1)
	safe.Max.X = 114
	return index + ".  " + zh, safe, true
}

// 規格038 READY：完整原版改印先移除舊網格項，包含未翻譯的新值。
func (s *stringRuntime) retireRouteGrid(text string, ink image.Rectangle) []*stringItem {
	index, name, ok := strings.Cut(text, ".  ")
	if !ok || name == "" {
		return nil
	}
	start := image.Point{}
	switch index {
	case "1":
		start = image.Pt(11, 69)
	case "2":
		start = image.Pt(10, 89)
	default:
		return nil
	}
	if ink.Min != start {
		return nil
	}
	var dropped []*stringItem
	kept := s.items[:0]
	for _, it := range s.items {
		if it.id == "STRING:route-grid-colony" && it.ink.Overlaps(ink) && it.text != text {
			dropped = append(dropped, it)
			continue
		}
		kept = append(kept, it)
	}
	s.items = kept
	return dropped
}

// 規格038 READY：只移除這次已觀測購船改印所取代的舊港口項。
func (s *stringRuntime) retirePortHeader(r *stringRun, ink image.Rectangle) []*stringItem {
	if r == nil || string(r.text) != "Loading:  Caravel" || ink != image.Rect(154, 120, 213, 126) || r.outline || r.buf2 || r.mixed || len(r.colors) != 1 || r.colors[69] == 0 || !r.others.Empty() {
		return nil
	}
	var dropped []*stringItem
	kept := s.items[:0]
	for _, it := range s.items {
		if it.id == "STRING:dictionary" && it.text == "No Ships In Port" && it.ink == image.Rect(156, 120, 210, 126) && it.safe == image.Rect(155, 119, 211, 127) {
			dropped = append(dropped, it)
			continue
		}
		kept = append(kept, it)
	}
	s.items = kept
	return dropped
}

// 規格038 READY港口欄位：詞槽只接受指定版本名稱檔的分類，不引用玩家名稱。
func portKinds(names []byte) map[string]map[string]bool {
	if fmt.Sprintf("%x", sha256.Sum256(names)) != "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061" {
		return nil
	}
	result := map[string]map[string]bool{}
	section := ""
	for _, line := range strings.Split(string(names), "\r\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "@") {
			section = line
			continue
		}
		if line == "" || strings.HasPrefix(line, ";") {
			continue
		}
		role := ""
		switch section {
		case "@NATIONALITY":
			role = "nation"
		case "@JOB":
			role = "job"
		case "@CARGO":
			role = "cargo"
		case "@UNIT":
			role = "unit"
		}
		if role == "" {
			continue
		}
		word := strings.TrimSpace(strings.SplitN(line, ",", 2)[0])
		if role == "unit" && word != "Colonists" {
			continue
		}
		if result[role] == nil {
			result[role] = map[string]bool{}
		}
		result[role][word] = true
	}
	return result
}

func portScene(canvas []byte) bool {
	if len(canvas) != 320*200 {
		return false
	}
	for _, v := range []struct {
		rect image.Rectangle
		sha  string
	}{
		{image.Rect(284, 91, 316, 97), "1e01823ef22283bc594e37b025b50426b346419c2f3f623727e720a915fae802"},
		{image.Rect(284, 102, 316, 108), "cd62f1e8b65075b9976218fbfa5e8ac41a79440467600a234e25ecf6d2445a9c"},
		{image.Rect(284, 113, 316, 119), "c0be6db681165ce3a2d9bbb73137238baef313fc9e88cb9551982ccd5d9a8dc5"},
	} {
		if fmt.Sprintf("%x", sha256.Sum256(stringRect(canvas, v.rect))) != v.sha {
			return false
		}
	}
	return true
}

func (c *stringCatalog) portText(id, text string) (string, bool) {
	for _, tpl := range c.templates {
		if tpl.id != id {
			continue
		}
		m := tpl.re.FindStringSubmatch(strings.Trim(text, " "))
		if m == nil {
			return "", false
		}
		vals := map[string]string{}
		for i, slot := range tpl.slots {
			value := m[i+1]
			role := ""
			switch slot {
			case "w1":
				if id == "port-field-market" {
					role = "cargo"
				} else {
					role = "nation"
				}
			case "w2":
				role = "unit"
			case "w3":
				role = "job"
			default:
				if slot[0] != 'n' {
					return "", false
				}
			}
			if role != "" {
				if !c.portRoles[role][value] {
					return "", false
				}
				value = c.lookup(value)
				if value == "" {
					return "", false
				}
			}
			vals[slot] = value
		}
		return stringSlot.ReplaceAllStringFunc(tpl.zh, func(slot string) string { return vals[slot[1:len(slot)-1]] }), true
	}
	return "", false
}

func (s *stringRuntime) portFieldTranslate(r *stringRun, face image.Rectangle, capH int, color byte, canvas []byte) (string, string, bool) {
	if r.outline || r.buf2 || r.mixed || capH != 5 || !portScene(canvas) {
		return "", "", false
	}
	var ids []string
	switch {
	case color == 149 && face.Min.Y == 1 && face.Max.Y == 7 && face.Min.X >= 1 && face.Max.X < 320:
		ids = []string{"port-field-profession", "port-field-unit"}
	case color == 15 && face.Min.X == 1 && face.Min.Y == 194 && face.Max.Y == 200:
		ids = []string{"port-field-market"}
	}
	for _, id := range ids {
		if zh, ok := s.cat.portText(id, string(r.text)); ok {
			return zh, "template:" + id, true
		}
	}
	return "", "", false
}

// addWoodcut 保留完整來源身份；同文異鍵或異譯永久拒絕，不借用通用片段字典。
func (c *stringCatalog) addWoodcut(raw, id, zh string) {
	if raw == "" || id == "" || zh == "" {
		return
	}
	if c.woodcut == nil {
		c.woodcut = map[string]woodcutTitle{}
	}
	title := woodcutTitle{id: id, zh: zh}
	if old, ok := c.woodcut[raw]; ok && old != title {
		c.woodcut[raw] = woodcutTitle{}
		return
	}
	c.woodcut[raw] = title
}

// woodcutMasks 逐欄求字級；填色置中、墨跡上緣對齊，三個色層互斥。
func (c *stringCatalog) woodcutMasks(zh string, ink, safe image.Rectangle, capH int) (sh, n, ac *image.Alpha, size int) {
	start, floor := stringStartPx(capH)
	rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
	const relief = 4
	for size = start; size >= floor; size-- {
		f := c.fonts[size]
		if f == nil {
			continue
		}
		w := 0
		for _, ch := range zh {
			gw, ok := f.widths[ch]
			if !ok || gw <= 0 || f.glyphs[ch] == nil {
				return nil, nil, nil, 0
			}
			w += gw
		}
		if w == 0 {
			return nil, nil, nil, 0
		}
		x, y := (rect.Dx()-w)/2, (ink.Min.Y-safe.Min.Y)*4-f.cjkTop
		if x < relief || x+w+relief > rect.Dx() || y+f.cjkTop < relief || y+f.cjkBottom+relief > rect.Dy() {
			continue
		}
		// 核對實際alpha，字模中繼資料不許掩蓋裁切。
		fits, dx := true, x
		for _, ch := range zh {
			g := f.glyphs[ch]
			for gy := g.Rect.Min.Y; gy < g.Rect.Max.Y; gy++ {
				for gx := g.Rect.Min.X; gx < g.Rect.Max.X; gx++ {
					if g.AlphaAt(gx, gy).A != 0 && (dx+gx < relief || dx+gx+relief >= rect.Max.X || y+gy < relief || y+gy+relief >= rect.Max.Y) {
						fits = false
					}
				}
			}
			dx += f.widths[ch]
		}
		if !fits {
			continue
		}
		sh, n, ac = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		for _, ch := range zh {
			g := f.glyphs[ch]
			dialogBlit(n, g, x, y)
			dialogBlit(ac, g, x-relief, y-relief)
			dialogBlit(sh, g, x+relief, y+relief)
			x += f.widths[ch]
		}
		for i := range n.Pix {
			if n.Pix[i] != 0 {
				sh.Pix[i], ac.Pix[i] = 0, 0
			} else if ac.Pix[i] != 0 {
				sh.Pix[i] = 0
			}
		}
		return sh, n, ac, size
	}
	return nil, nil, nil, 0
}

// finishWoodcut 僅授權已驗WOODCUT來源與原版標題帶；其他多色串沿原文回退。
func (s *stringRuntime) finishWoodcut(r *stringRun, ink image.Rectangle, capH int, canvas []byte, step uint64) (*stringItem, string) {
	title, ok := s.cat.woodcut[string(r.text)]
	if !ok || title.id == "" || title.zh == "" {
		return nil, "multi-color"
	}
	if r.outline || r.buf2 || r.mixed || capH != 7 || ink.Min.Y != 165 || ink.Max.Y != 172 ||
		(ink.Min.X+ink.Max.X != 319 && ink.Min.X+ink.Max.X != 320) || !ink.In(image.Rect(1, 1, 319, 199)) {
		return nil, "woodcut-geometry"
	}
	if len(r.colors) != 3 || r.colors[92] <= 0 || r.colors[93] <= 0 || r.colors[94] <= 0 {
		return nil, "woodcut-colors"
	}
	safe := ink.Inset(-1)
	if r.others.Overlaps(safe) {
		return nil, "other-writer"
	}
	if len(canvas) != 64000 || len(r.lastVal) < 3 || len(r.lastVal) != len(r.firstOld) {
		return nil, "woodcut-source-changed"
	}
	for i, value := range r.lastVal {
		_, old := r.firstOld[i]
		if i < 0 || i >= len(canvas) || !image.Pt(i%320, i/320).In(ink) || !old || value < 92 || value > 94 || canvas[i] != value {
			return nil, "woodcut-source-changed"
		}
	}
	sh, n, ac, size := s.cat.woodcutMasks(title.zh, ink, safe, capH)
	if n == nil {
		return nil, "does-not-fit"
	}
	before := append([]byte(nil), canvas...)
	for i, value := range r.firstOld {
		before[i] = value
	}
	return &stringItem{id: "STRING:woodcut:" + title.id, text: string(r.text), zh: title.zh, ink: ink, safe: safe,
		color: 94, shadowColor: 93, accentColor: 92, size: size, shadowOff: 4, shadow: sh, norm: n, accent: ac,
		before: stringRect(before, safe), after: stringRect(canvas, safe), phase: "waiting-screen", complete: step}, ""
}

// woodcutVisible 僅識別三種正常路徑已驗、當前原版標題仍完整的事件頁。
func (s *stringRuntime) woodcutVisible(indexed []byte, cursor image.Rectangle) bool {
	if s == nil || s.cat == nil || len(indexed) != 64000 {
		return false
	}
	for _, it := range s.items {
		title := s.cat.woodcut[it.text]
		switch title.id {
		case "WOODCUT.TXT:0x00000017", "WOODCUT.TXT:0x00000046", "WOODCUT.TXT:0x0000009E":
		default:
			continue
		}
		if it.id == "STRING:woodcut:"+title.id && it.phase == "active" && !it.safe.Empty() &&
			it.safe.In(image.Rect(0, 0, 320, 200)) && len(it.after) == it.safe.Dx()*it.safe.Dy() && stringSame(indexed, it, cursor) {
			return true
		}
	}
	return false
}
