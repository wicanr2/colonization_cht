package main

// 規格038：連續字串通用覆蓋。0D21:00C6 以遞增位址讀出、以 0 結尾的一串文字，
// 逐串比對模板與字典，在原版墨跡外擴 1 邏輯像素的安全區內改排中文；任一條件不成立即回原文。

import (
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

type stringCatalog struct {
	dlg       *dialogCatalog    // 定稿術語、NAMES 對照與逐行模板（規格035／036）
	frags     map[string]string // 片段字典：英文→中文；衝突者為空字串（視為查無）
	templates []stringTemplate
	colony    map[string]string // COLONY.TXT 預設名→「中文（原名）」
	owned     map[string]bool   // 專屬欄位已處理的原文，本層不處理
	fonts     map[int]*dialogFont
}

const (
	stringGap      = 200000 // 同一串相鄰兩次讀取的最大間隔（步）
	stringMaxItems = 512
	stringFontPx   = 30 // 圖集字級範圍：原版大寫字高 7 的起始字級
	stringFloorPx  = 12
)

var (
	stringSlot   = regexp.MustCompile(`\{(n\d|w\d|colony)\}`)
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
	c := &stringCatalog{dlg: dlg, frags: map[string]string{}, colony: map[string]string{}, owned: map[string]bool{}}
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
		}
	}
	rows = tsvRows(draft)
	if rows == nil {
		return nil, fmt.Errorf("譯稿 TSV 欄位不符")
	}
	for _, r := range rows {
		f := r["source_file"]
		if f != "LABELS.TXT" && f != "WOODCUT.TXT" && f != "NAMES.TXT" {
			continue
		}
		raw, ok, err := verifiedRaw(files, f, r["source_sha256"], r["byte_offset"], r["source_byte_length"], r["source_bytes_sha256"], r["candidate_id"])
		if err != nil {
			return nil, err
		}
		if ok && !strings.Contains(raw, ",") && single(raw, r["zh_hant"]) {
			c.addFrag(raw, r["zh_hant"])
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
func (c *stringCatalog) lookup(en string) string {
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
	t := strings.TrimRight(text, " ")
	var hits []string
	var hitID string
	for _, tpl := range c.templates {
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
		return "", "", "ambiguous-template"
	}
	if zh, ok := c.colony[t]; ok {
		return zh, "colony", ""
	}
	if zh := c.lookup(t); zh != "" {
		return zh, "dictionary", ""
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
func (c *stringCatalog) stringMasks(zh string, ink, safe image.Rectangle, capH, limitRight, shadow int) (sh, n *image.Alpha, size int) {
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
		for _, r := range zh {
			gw, has := f.widths[r]
			if !has {
				good = false
				break
			}
			w += gw
		}
		if !good {
			return nil, nil, 0
		}
		if x+w+shadow > limitRight || y+f.cjkBottom+shadow > rect.Dy() || y+f.cjkTop < 0 {
			continue
		}
		// 安全區只延伸到中文實際需要的寬度（不少於原版墨跡外擴 1 像素），避免把之後畫的圖示包進比對範圍。
		need := max(rect.Dx()-(safe.Max.X-ink.Max.X-1)*4, x+w+shadow)
		if safe.Max.X > ink.Max.X+1 {
			rect.Max.X = min(rect.Dx(), (need+3)/4*4)
		}
		sh, n = image.NewAlpha(rect), image.NewAlpha(rect)
		for _, r := range zh {
			a := f.glyphs[r]
			dialogBlit(n, a, x, y)
			if shadow > 0 {
				dialogBlit(sh, a, x+shadow, y+shadow)
			}
			x += f.widths[r]
		}
		return sh, n, size
	}
	return nil, nil, 0
}

// ---- 執行期（設計第 1、2、7 點）----

type stringRun struct {
	base, next  uint32
	start, last uint64
	text        []byte
	boxes       []image.Rectangle
	colors      map[byte]int
	firstOld    map[int]byte
	lastVal     map[int]byte
	others      image.Rectangle
}

type stringItem struct {
	id, text, zh string
	ink, safe    image.Rectangle
	color        byte
	size         int
	shadowOff    int
	shadow, norm *image.Alpha
	before       []byte // 印前畫布的安全區（本串文字像素已還原）
	after        []byte // 完成時畫布的安全區
	phase        string // waiting-screen、active、suspended
	complete     uint64
	appliedFrame int
}

type stringRuntime struct {
	cat      *stringCatalog
	cur      *stringRun
	items    []*stringItem
	misses   map[string]int
	reason   string
	accepted int
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
	r.next, r.last = a+1, step
	return nil
}

// onWrite 記錄畫布寫入：text 表示 0D21:012C，cursor 表示游標常式在游標附近。
func (s *stringRuntime) onWrite(i int, old, value byte, text, cursor bool) {
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
	if _, seen := r.firstOld[i]; !seen {
		r.firstOld[i] = old
	}
	r.lastVal[i] = value
	r.colors[value]++
	r.boxes[len(r.boxes)-1] = r.boxes[len(r.boxes)-1].Union(p)
}

func stringRect(buf []byte, r image.Rectangle) []byte {
	b := make([]byte, 0, r.Dx()*r.Dy())
	for y := r.Min.Y; y < r.Max.Y; y++ {
		b = append(b, buf[y*320+r.Min.X:y*320+r.Max.X]...)
	}
	return b
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
		return nil, "multi-color"
	}
	var color byte
	for c := range r.colors {
		color = c
	}
	if capH == 0 {
		capH = ink.Dy()
	}
	safe := ink.Inset(-1).Intersect(image.Rect(0, 0, 320, 200))
	if r.others.Overlaps(safe) {
		return nil, "other-writer"
	}
	zh, id, why := s.cat.translate(text)
	if why != "" {
		return nil, why
	}
	limit, shadow := safe.Dx()*4, 0
	if !panel.Empty() && ink.In(panel) {
		// 設計第 6 點（狀態欄樣式）：安全區延伸到欄右緣，右界留 2 輸出像素給陰影。
		safe = image.Rect(safe.Min.X, safe.Min.Y, panel.Max.X, safe.Max.Y)
		limit, shadow = safe.Dx()*4, 2
	}
	sh, n, size := s.cat.stringMasks(zh, ink, safe, capH, limit, shadow)
	if n == nil {
		return nil, "does-not-fit"
	}
	safe.Max.X = safe.Min.X + n.Rect.Dx()/4
	before := make([]byte, len(canvas))
	copy(before, canvas)
	for i, v := range r.firstOld {
		before[i] = v
	}
	return &stringItem{id: "STRING:" + id, text: text, zh: zh, ink: ink, safe: safe, color: color, size: size, shadowOff: shadow,
		shadow: sh, norm: n, before: stringRect(before, safe), after: stringRect(canvas, safe), phase: "waiting-screen", complete: step}, ""
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
		case it.phase == "waiting-screen" && !same:
			changes = append(changes, [3]any{it, "expired", "canvas-changed-before-screen"})
			continue
		case it.phase == "waiting-screen" && now-it.complete > 2000000:
			changes = append(changes, [3]any{it, "expired", "screen-sync-timeout"})
			continue
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
