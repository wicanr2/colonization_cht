package main

// 規格057／060 READY：依原文觀測重建，透過既有顯示設定交易交換整包。
import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"maps"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

var languageBundles = flag.String("language-bundles", "", "已驗五語顯示資源的根目錄")

var draftNativeBundles = flag.String("draft-native-bundles", "", "規格060隔離原型的完整候選根目錄")
var draftNativeLive = flag.Bool("draft-native-live", false, "規格060隔離原型：接入真視窗五語重建與設定交易")

// 正式資源啟用即時顯示；控制組仍只顯示原版。舊探針須明示觀測及設定列。
func languageRuntimeSelection(formal, probe string, probeLive, capture, settings, control bool) (string, bool, error) {
	if formal != "" && (probe != "" || probeLive) {
		return "", false, fmt.Errorf("language-bundles cannot be combined with draft-native bundle flags")
	}
	if probeLive && (probe == "" || !settings || control) {
		return "", false, fmt.Errorf("native live probe requires bundles and display settings without control")
	}
	if probe != "" && !capture {
		return "", false, fmt.Errorf("native bundle probe requires capture")
	}
	if formal != "" {
		return formal, !control, nil
	}
	return probe, probeLive, nil
}

type draftLanguageTarget struct {
	originalFonts    *displayUIFonts
	declarationPlans map[string]*notoDeclarationPlan
	portraits        *hdSceneRuntime
	pack             *draftPreparedBundle
	dlg              *dialogCatalog
	str              *stringCatalog
	sea              *seaState
	fixed            map[string]*draftFixedMask
	nativeLabels     map[string][2]string
}

type draftNativeFrame struct {
	journal                          *nativeJournal
	canvas, buffer, indexed, palette []byte
	cursor                           image.Rectangle
	step                             uint64
	mode                             byte
}

type draftLanguageDisplay struct {
	options   displayOptions
	target    *draftLanguageTarget
	frame     *image.RGBA
	receipt   map[string]any
	nativeKey string
	buildTime time.Duration
}

// 準備與生效資料分開；由既有設定保存成功後才呼叫提交。
type draftLanguageBackend struct {
	hd                *hdRuntime
	sourceScenes      *hdSceneRuntime
	hdReason          string
	targets           map[string]*draftLanguageTarget
	sample            func() draftNativeFrame
	active            *draftLanguageDisplay
	renders, rebuilds uint64
	maxBuildTime      time.Duration
}

func (b *draftLanguageBackend) sourceKey() string {
	if b.hd != nil {
		return b.hd.key()
	}
	if b.sourceScenes != nil {
		return fmt.Sprintf("/text-scene/%d", b.sourceScenes.revision)
	}
	return ""
}

func (f draftNativeFrame) key() string {
	if f.journal == nil {
		return ""
	}
	expired := 0
	for _, o := range f.journal.items {
		if o.fixed != nil && o.fixed.expired {
			expired++
		}
	}
	return fmt.Sprintf("%s/%d/%d/%d/%d/%v/%t", hash(bytes.Join([][]byte{f.canvas, f.buffer, f.indexed, f.palette}, nil)),
		f.journal.accepted, f.journal.lost, expired, f.mode, f.cursor, f.journal.buttons)
}

func (b *draftLanguageBackend) prepare(options displayOptions) (func(), error) {
	if err := options.validate(); err != nil {
		return nil, err
	}
	target := b.targets[options.Language]
	if (options.Graphics != "original" && (options.Graphics != "hd" || b.hd == nil)) || target == nil || target.pack == nil ||
		target.pack.manifest.Locale != options.Language || b.sample == nil {
		return nil, fmt.Errorf("ui.error.unavailable")
	}
	f := b.sample()
	if f.journal == nil {
		return nil, fmt.Errorf("ui.error.unavailable")
	}
	started := time.Now()
	frame, receipt, err := b.rebuildWithHD(target, options, f)
	if err != nil {
		return nil, err
	}
	next := &draftLanguageDisplay{options: options, target: target, frame: frame, receipt: receipt, nativeKey: f.key() + b.sourceKey(), buildTime: time.Since(started)}
	return func() { b.active = next }, nil
}

func (b *draftLanguageBackend) renderCurrent() (*image.RGBA, map[string]any, error) {
	if b.active == nil || b.sample == nil {
		return nil, nil, fmt.Errorf("native live backend not initialized")
	}
	f := b.sample()
	if f.journal == nil || len(f.canvas) != 64000 || len(f.buffer) != 64000 || len(f.indexed) != 64000 || len(f.palette) != 768 {
		return nil, nil, fmt.Errorf("invalid native live frame")
	}
	key := f.key() + b.sourceKey()
	reused := key == b.active.nativeKey
	if !reused {
		started := time.Now()
		frame, receipt, err := b.rebuildWithHD(b.active.target, b.active.options, f)
		if err != nil {
			return nil, nil, err
		}
		b.active = &draftLanguageDisplay{options: b.active.options, target: b.active.target, frame: frame, receipt: receipt,
			nativeKey: key, buildTime: time.Since(started)}
		b.rebuilds++
	}
	b.renders++
	b.maxBuildTime = max(b.maxBuildTime, b.active.buildTime)
	record := maps.Clone(b.active.receipt)
	record["hd_available"], record["hd_asset_reason"] = b.hd != nil, b.hdReason
	record["text_scene_sources_available"] = b.sourceScenes != nil || b.hd != nil && b.hd.scenes != nil
	record["step"], record["live_reused"] = f.step, reused
	record["live_renders"], record["live_rebuilds"] = b.renders, b.rebuilds
	record["build_nanoseconds"], record["max_build_nanoseconds"] = int64(b.active.buildTime), int64(b.maxBuildTime)
	return b.active.frame, record, nil
}

func draftTargetRequirements(_ string) (draftBundleRequirements, error) {
	return draftIndexedRequirements()
}

// 在原版執行前準備五包。之後重建只使用這些記憶體物件。
func draftPrepareTargets(root string, files map[string][]byte, owned, helpOwned map[string]bool) (map[string]*draftLanguageTarget, error) {
	needs, err := draftTargetRequirements(root)
	if err != nil {
		return nil, err
	}
	targets := map[string]*draftLanguageTarget{}
	var originalFonts *displayUIFonts
	if *displayUIFont != "" {
		data, err := os.ReadFile(*displayUIFont)
		if err != nil {
			return nil, err
		}
		originalFonts, err = readUIFonts(data, nil)
		if err != nil {
			return nil, err
		}
	}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		pack, err := draftPrepareBundle(os.DirFS(root), locale, needs)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", locale, err)
		}
		t := &draftLanguageTarget{pack: pack, originalFonts: originalFonts, declarationPlans: map[string]*notoDeclarationPlan{}}
		if locale == "en" {
			targets[locale] = t
			continue
		}
		get := func(name string) []byte { return pack.files["text/"+name] }
		cb, nb, db := get("corpus.zh-Hant.tsv"), get("terms.zh-Hant.tsv"), get("draft.zh-Hant.tsv")
		cat, err := loadDialogCatalog(cb, nb, files["GAME.TXT"], versions["GAME.TXT"], map[string]bool{})
		if err != nil {
			return nil, err
		}
		cat.bindUnitCaptionNames(cb, files["NAMES.TXT"])
		hb, vb, pb := get("help-bilingual.tsv"), get("variable-values.zh-Hant.tsv"), get("pedia-bilingual.tsv")
		for _, e := range []error{cat.addCorpus(hb, files["GAME.TXT"], versions["GAME.TXT"], helpOwned),
			cat.addDraft(db, files, owned), cat.addValues(vb, files), cat.addPedia(pb, files["PEDIA.TXT"])} {
			if e != nil {
				return nil, e
			}
		}
		bind := map[string]string{"corpus": hash(cb), "terms": hash(nb), "draft": hash(db), "values": hash(vb), "help": hash(hb), "pedia": hash(pb)}
		if why := cat.loadDialogAtlas(pack.files["masks/dialog-atlas.json"], pack.manifest.Font, bind); why != "" {
			return nil, fmt.Errorf("%s dialog: %s", locale, why)
		}
		tb, sb, colb := get("string-templates.zh-Hant.tsv"), get("sea-status.zh-Hant.tsv"), get("colony-bilingual.tsv")
		sc, err := loadStringCatalog(cat, tb, sb, cb, db, colb, files)
		if err != nil {
			return nil, err
		}
		if err = sc.addOwned(db, files, owned); err != nil {
			return nil, err
		}
		if err = sc.addOwned(get("nation-card-fragments.zh-Hant.tsv"), files, nil); err != nil {
			return nil, err
		}
		bind = map[string]string{"templates": hash(tb), "sea": hash(sb), "corpus": hash(cb), "draft": hash(db), "terms": hash(nb), "colony": hash(colb)}
		var why string
		sc.fonts, why = loadAtlasFonts(pack.files["masks/string-atlas.json"], pack.manifest.Font, bind, stringFontPx, stringFloorPx)
		if why != "" {
			return nil, fmt.Errorf("%s string: %s", locale, why)
		}
		cat.saveDescription, cat.colonyValue = sc.translateSaveDescription, func(name string) string {
			if value, ok := sc.colony[name]; ok {
				return value
			}
			return name
		}
		t.sea, err = draftPrepareSea(pack, files)
		if err != nil {
			return nil, fmt.Errorf("%s sea: %w", locale, err)
		}
		t.fixed, err = draftPrepareFixed(pack, needs)
		if err != nil {
			return nil, fmt.Errorf("%s fixed: %w", locale, err)
		}
		sc.labelPlan = func(text string, fill, ink image.Rectangle, capH int) (*image.Alpha, *image.Alpha, image.Rectangle, int) {
			return draftNotoMapLabelMasks(sc.fonts, text, fill, ink, capH)
		}
		sc.woodcutPlan = func(id, text string, ink, safe image.Rectangle, capH int) (*image.Alpha, *image.Alpha, *image.Alpha, int) {
			return draftNotoWoodcutMasks(sc.fonts, id, text, ink, safe, capH)
		}
		t.dlg, t.str = cat, sc
		draftBindNativeLabels(t, files)
		targets[locale] = t
	}
	return targets, nil
}

type draftFixedMask struct {
	id, text                      string
	safe                          image.Rectangle
	position                      image.Point
	size                          int
	alpha, normal, shadow, accent *image.Alpha
}

type draftFixedJSON struct {
	ID          string   `json:"candidate_id"`
	MessageID   string   `json:"message_id"`
	Translation string   `json:"translation_sha256"`
	Keys        []string `json:"keys"`
	Caption     string   `json:"caption"`
	Size        int      `json:"font_size"`
	X           int      `json:"x"`
	Y           int      `json:"y"`
	Width       int      `json:"width"`
	Height      int      `json:"height"`
	Alpha       []byte   `json:"alpha"`
	Normal      []byte   `json:"normal"`
	Shadow      []byte   `json:"shadow"`
	Accent      []byte   `json:"highlight"`
}

// 與固定字模產生器相同的既有TSV處理：移除控制碼、字幕槽位及教學定稿術語。
func draftFixedText(pack *draftPreparedBundle, requirement draftMaskRequirement, group string, mask draftFixedJSON) (string, error) {
	rows := tsvRows(pack.files["text/"+requirement.Catalog])
	if rows == nil {
		return "", fmt.Errorf("fixed catalog format")
	}
	index := map[string]map[string]string{}
	for _, r := range rows {
		id := r["candidate_id"]
		if id == "" {
			id = r["message_id"]
		}
		if id == "" || index[id] != nil {
			return "", fmt.Errorf("fixed catalog duplicate or empty key")
		}
		index[id] = r
	}
	keys := mask.Keys
	if len(keys) == 0 {
		keys = []string{requirement.ID}
	}
	var parts []string
	for _, key := range keys {
		r := index[key]
		if r == nil {
			return "", fmt.Errorf("fixed text missing: %s", key)
		}
		text := r["zh_hant"]
		if group == "intro" {
			text = r["zh_hant_draft"]
		}
		if text == "" {
			return "", fmt.Errorf("fixed text empty: %s", key)
		}
		parts = append(parts, strings.ReplaceAll(strings.TrimPrefix(text, "^^"), "~", ""))
	}
	if group == "captions" {
		for _, r := range tsvRows(pack.files["text/build-caption-values.zh-Hant.tsv"]) {
			if r["nation"] == "england" && r["caption"] == mask.Caption {
				if r["placeholder"] == "" || r["zh_hant"] == "" {
					return "", fmt.Errorf("fixed caption value empty")
				}
				for i := range parts {
					parts[i] = strings.ReplaceAll(parts[i], r["placeholder"], r["zh_hant"])
				}
			}
		}
	}
	text := strings.Join(parts, "\n")
	if (group == "card" || group == "cards-rest") && strings.HasPrefix(requirement.ID, "NAMES.TXT:") {
		text += "："
	}
	if group == "help" {
		var terms []string
		for _, r := range tsvRows(pack.files["text/terms.zh-Hant.tsv"]) {
			if r["en"] == "Caravel" && r["category"] == "ship" {
				terms = append(terms, r["zh"])
			}
		}
		if len(terms) != 1 || terms[0] == "" {
			return "", fmt.Errorf("fixed tutorial term missing")
		}
		text = strings.ReplaceAll(text, "%STRING0", terms[0])
	}
	if strings.Contains(text, "%STRING") || strings.Contains(text, "^^") || strings.Contains(text, "~") || hash([]byte(text)) != mask.Translation {
		return "", fmt.Errorf("fixed displayed text binding mismatch: %s", requirement.ID)
	}
	return text, nil
}

func draftPrepareFixed(pack *draftPreparedBundle, needs draftBundleRequirements) (map[string]*draftFixedMask, error) {
	result := map[string]*draftFixedMask{}
	for name, requirement := range needs.Masks {
		var raw draftFixedJSON
		if err := json.Unmarshal(pack.files["masks/"+name], &raw); err != nil {
			return nil, err
		}
		if raw.ID == "" {
			raw.ID = raw.MessageID
		}
		if raw.ID != requirement.ID || result[raw.ID] != nil || raw.Size <= 0 {
			return nil, fmt.Errorf("fixed mask identity or size")
		}
		group := strings.TrimSuffix(strings.SplitN(name, "/", 2)[0], ".json")
		text, err := draftFixedText(pack, requirement, group, raw)
		if err != nil {
			return nil, err
		}
		f := &draftFixedMask{id: raw.ID, text: text, safe: image.Rect(requirement.Safe[0]/4, requirement.Safe[1]/4, requirement.Safe[2]/4, requirement.Safe[3]/4), position: image.Pt(raw.X, raw.Y), size: raw.Size}
		load := func(data []byte) *image.Alpha {
			if len(data) == 0 {
				return nil
			}
			m := image.NewAlpha(image.Rect(0, 0, raw.Width, raw.Height))
			copy(m.Pix, data)
			return m
		}
		f.alpha, f.normal, f.shadow, f.accent = load(raw.Alpha), load(raw.Normal), load(raw.Shadow), load(raw.Accent)
		body := f.alpha
		if requirement.Layered {
			body = f.normal
		}
		if body == nil || bytes.Count(body.Pix, []byte{0}) == len(body.Pix) {
			return nil, fmt.Errorf("fixed body ink empty: %s", f.id)
		}
		result[f.id] = f
	}
	if len(result) != 64 {
		return nil, fmt.Errorf("fixed masks incomplete")
	}
	return result, nil
}

func draftPaintFixed(out *image.RGBA, mask *draftFixedMask, o *nativeObservation, j *nativeJournal, canvas, indexed, palette []byte, cursor image.Rectangle, hdBackgroundOverride ...draftHDBackground) (map[string]any, string) {
	f := o.fixed
	if f == nil || mask == nil || f.id != mask.id || f.safe != mask.safe || f.layered != (mask.normal != nil) {
		return nil, "fixed-field-binding"
	}
	if !o.visible(canvas, nil, indexed) {
		return nil, "fixed-native-expired-or-changed"
	}
	if f.paletteSHA != "" && hash(palette) != f.paletteSHA {
		return nil, "fixed-native-palette-changed"
	}
	if f.buttonGuard && j.buttons {
		return nil, "fixed-button-held"
	}
	guard := f.guard
	if f.mouseRule == "target-ink" {
		ink := mask.alpha.Bounds().Add(mask.position)
		ink = ink.Union(ink.Add(f.shadow))
		guard = image.Rect(ink.Min.X/4, ink.Min.Y/4, (ink.Max.X+3)/4, (ink.Max.Y+3)/4)
	}
	if (f.mouseRule == "point" && cursor.Min.In(guard)) || ((f.mouseRule == "overlap" || f.mouseRule == "target-ink") && cursor.Overlaps(guard)) {
		return nil, "fixed-cursor-over-field"
	}
	if !f.vga && !draftSameExceptCursor(indexed, canvas, f.safe, cursor) {
		return nil, "fixed-vga-safe-changed"
	}
	var layers []*image.Alpha
	var colors []byte
	var positions []image.Point
	if f.layered {
		layers = []*image.Alpha{mask.shadow, mask.normal, mask.accent}
		colors = []byte{f.shade, f.foreground, f.accent}
		positions = []image.Point{mask.position, mask.position, mask.position}
	} else {
		if f.shadow != (image.Point{}) {
			layers = append(layers, mask.alpha)
			colors = append(colors, f.shade)
			positions = append(positions, mask.position.Add(f.shadow))
		}
		layers = append(layers, mask.alpha)
		colors = append(colors, f.foreground)
		positions = append(positions, mask.position)
	}
	scaled := image.Rectangle{Min: f.safe.Min.Mul(4), Max: f.safe.Max.Mul(4)}
	for i, layer := range layers {
		if layer == nil || !layer.Bounds().Add(positions[i]).In(scaled) {
			return nil, "fixed-ink-out-of-bounds"
		}
	}
	k := 0
	for y := f.safe.Min.Y; y < f.safe.Max.Y; y++ {
		for x := f.safe.Min.X; x < f.safe.Max.X; x++ {
			if f.before[k] != f.after[k] {
				draftPaintPixel(out, y*320+x, f.before[k], palette, hdBackgroundOverride...)
			}
			k++
		}
	}
	for i, layer := range layers {
		at := positions[i]
		draw.DrawMask(out, layer.Bounds().Add(at), image.NewUniform(draftColor(colors[i], palette)), image.Point{}, layer, layer.Bounds().Min, draw.Over)
	}
	return map[string]any{"kind": "fixed", "id": f.id, "text": mask.text, "safe": f.safe, "font_px": mask.size, "position": mask.position, "layered": f.layered}, ""
}

// 沿規格032核對逐詞來源；整包載入器另核對地區、字型、圖集尺寸及綁定。
func draftPrepareSea(pack *draftPreparedBundle, files map[string][]byte) (*seaState, error) {
	st := &seaState{dict: map[string]map[string]string{}, fonts: map[int]*seaFont{}, misses: map[string]int{}}
	var err error
	st.phrases, err = loadDisplayPhrases(pack.files["text/string-templates.zh-Hant.tsv"])
	if err != nil {
		return nil, err
	}
	rows := tsvRows(pack.files["text/sea-status.zh-Hant.tsv"])
	if rows == nil {
		return nil, fmt.Errorf("sea catalog format")
	}
	seen := map[string]bool{}
	for _, r := range rows {
		source, ok := files[r["source_file"]]
		offset, e1 := strconv.ParseUint(r["byte_offset"], 0, 32)
		length, e2 := strconv.Atoi(r["source_byte_length"])
		text, id := r["source_text"], r["candidate_id"]
		if !ok || e1 != nil || e2 != nil || length <= 0 || offset+uint64(length) > uint64(len(source)) ||
			r["source_sha256"] != hash(source) || len(text) != length || string(source[offset:offset+uint64(length)]) != text ||
			id == "" || seen[id] || r["zh_hant"] == "" || r["status"] != "draft" {
			return nil, fmt.Errorf("sea source mismatch: %s", id)
		}
		seen[id] = true
		role := r["role"]
		if st.dict[role] == nil {
			st.dict[role] = map[string]string{}
		}
		if _, dup := st.dict[role][text]; dup {
			return nil, fmt.Errorf("sea duplicate: %s", id)
		}
		st.dict[role][text] = r["zh_hant"]
	}
	for _, key := range []string{"~GAME", "~VIEW", "~ORDERS", "~REPORTS", "~TRADE", "~COLONIZOPEDIA"} {
		zh := st.dict["menu"][key]
		if zh == "" {
			return nil, fmt.Errorf("sea missing menu: %s", key)
		}
		st.menu = append(st.menu, "("+key[1:2]+")\x00"+zh)
	}
	var atlas struct {
		Sizes map[string]struct {
			Height int `json:"height"`
			Top    int `json:"cjk_ink_top"`
			Glyphs map[string]struct {
				W     int    `json:"w"`
				Alpha []byte `json:"alpha"`
			} `json:"glyphs"`
		} `json:"sizes"`
	}
	if err = json.Unmarshal(pack.files["masks/sea-atlas.json"], &atlas); err != nil {
		return nil, err
	}
	for size := 15; size <= 22; size++ {
		src, ok := atlas.Sizes[strconv.Itoa(size)]
		if !ok || src.Height <= 0 || src.Height > 128 || src.Top < 0 || src.Top >= src.Height || len(src.Glyphs) == 0 {
			return nil, fmt.Errorf("sea invalid size: %d", size)
		}
		f := &seaFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, height: src.Height, cjkTop: src.Top}
		for key, glyph := range src.Glyphs {
			r := []rune(key)
			if len(r) != 1 || glyph.W <= 0 || glyph.W > 128 || len(glyph.Alpha) != glyph.W*src.Height {
				return nil, fmt.Errorf("sea invalid glyph")
			}
			mask := image.NewAlpha(image.Rect(0, 0, glyph.W, src.Height))
			copy(mask.Pix, glyph.Alpha)
			f.glyphs[r[0]], f.widths[r[0]] = mask, glyph.W
		}
		st.fonts[size] = f
	}
	return st, nil
}

type draftSeaRow struct {
	observation       *nativeObservation
	row               *seaRow
	layer             image.Rectangle
	foreground        []byte
	foregroundChanges int
	foregroundSource  int
	textOffsetY       int
	inputDialog       string
}

// 六欄分別以原版下一欄起點量寬；快捷鍵與譯文用同地區字型。
func draftSeaMenu(st *seaState, runs []*seaEvent) (*seaRow, string) {
	if len(runs) != len(seaMenuText) || len(st.menu) != len(seaMenuWords) {
		return nil, "incomplete-menu"
	}
	row := &seaRow{firstOld: map[int]byte{}, lastVal: map[int]byte{}}
	for _, r := range runs {
		if r == nil || len(r.raw) != 2 || r.raw[1] != 0 || !r.bbox.In(seaBarRect) {
			return nil, "incomplete-menu"
		}
		row.text += string(r.raw[:1])
		row.bbox = row.bbox.Union(r.bbox)
		for i, v := range r.firstOld {
			row.firstOld[i] = v
		}
		for i, v := range r.lastVal {
			row.lastVal[i] = v
		}
	}
	if row.text != seaMenuText || runs[0].bbox.Min.X != 13 {
		return nil, "menu-source-mismatch"
	}
	k := 0
	for word, count := range seaMenuWords {
		parts := strings.SplitN(st.menu[word], "\x00", 2)
		if len(parts) != 2 {
			return nil, "menu-format"
		}
		x, end := runs[k].bbox.Min.X*4, seaBarRect.Max.X*4
		k += count
		if k < len(runs) {
			end = runs[k].bbox.Min.X * 4
		}
		size := st.seaFit(parts[0]+parts[1], end-x-2)
		if size == 0 {
			return nil, "menu-does-not-fit"
		}
		keyWidth, _ := st.seaWidthAt(parts[0], size)
		row.parts = append(row.parts, seaPart{parts[0], 149, x, size}, seaPart{parts[1], 68, x + keyWidth, size})
	}
	return row, ""
}

func draftSeaObserve(st *seaState, o *nativeObservation) (*draftSeaRow, string) {
	if len(o.seaRuns) == 0 {
		return nil, "not-sea"
	}
	if o.kind == "sea-bar" && len(o.seaRuns) > 1 {
		row, why := draftSeaMenu(st, o.seaRuns)
		if why != "" {
			return nil, why
		}
		return &draftSeaRow{observation: o, row: row, layer: seaBarRect}, ""
	}
	if len(o.seaRuns) != 1 {
		return nil, "incomplete-sea-row"
	}
	ev := o.seaRuns[0]
	text := strings.TrimRight(string(ev.raw), "\x00")
	row := &seaRow{bbox: ev.bbox, text: text, firstOld: ev.firstOld, lastVal: ev.lastVal}
	zh, ok := st.seaTranslate(text)
	if !ok {
		return nil, "no-sea-translation"
	}
	layer, x, ink := seaPanelRect, ev.bbox.Min.X*4, byte(149)
	if ev.bbox.In(seaBarRect) {
		layer, x = seaBarRect, 0
	} else if !ev.bbox.In(seaPanelRect) || len(ev.colors) != 1 {
		return nil, "sea-source-style"
	} else {
		for c := range ev.colors {
			ink = c
		}
		if ink != 68 && ink != 149 {
			return nil, "sea-source-style"
		}
	}
	size := st.seaFit(zh, layer.Max.X*4-x-2)
	if size == 0 {
		return nil, "sea-does-not-fit"
	}
	if layer == seaBarRect {
		width, _ := st.seaWidthAt(zh, size)
		x = 640 - width/2
	}
	row.parts = []seaPart{{zh, ink, x, size}}
	return &draftSeaRow{observation: o, row: row, layer: layer}, ""
}

func draftAlphaInk(mask *image.Alpha) image.Rectangle {
	var ink image.Rectangle
	for y := 0; y < mask.Rect.Dy(); y++ {
		for x := 0; x < mask.Rect.Dx(); x++ {
			if mask.AlphaAt(x, y).A != 0 {
				ink = ink.Union(image.Rect(x, y, x+1, y+1))
			}
		}
	}
	return ink
}

func draftPaintSea(out *image.RGBA, st *seaState, candidate *draftSeaRow, canvas, indexed, palette []byte, cursor image.Rectangle, hdBackgroundOverride ...draftHDBackground) (map[string]any, string) {
	o, row, layer := candidate.observation, candidate.row, candidate.layer
	if !o.visible(canvas, nil) {
		return nil, "sea-source-changed"
	}
	for i := range row.lastVal {
		if row.firstOld[i] == 68 || row.firstOld[i] == 149 {
			return nil, "sea-source-background"
		}
	}
	shadow := image.NewAlpha(image.Rect(0, 0, layer.Dx()*4, layer.Dy()*4))
	fg := map[byte]*image.Alpha{68: image.NewAlpha(shadow.Rect), 149: image.NewAlpha(shadow.Rect)}
	var text strings.Builder
	var sizes []int
	for _, part := range row.parts {
		x, y := part.x-layer.Min.X*4, row.bbox.Min.Y*4-st.fonts[part.size].cjkTop-layer.Min.Y*4+candidate.textOffsetY
		if st.seaDraw(shadow, part.text, x+2, y+2, part.size) || st.seaDraw(fg[part.color], part.text, x, y, part.size) {
			return nil, "sea-clipped"
		}
		text.WriteString(part.text)
		sizes = append(sizes, part.size)
	}
	ink := draftAlphaInk(shadow).Union(draftAlphaInk(fg[68])).Union(draftAlphaInk(fg[149])).Add(layer.Min.Mul(4))
	safe := row.bbox.Union(image.Rect(ink.Min.X/4, ink.Min.Y/4, (ink.Max.X+3)/4, (ink.Max.Y+3)/4))
	if !safe.In(layer) || !draftSameExceptCursor(canvas, o.canvas, safe, image.Rectangle{}) || !draftSameExceptCursor(indexed, canvas, safe, cursor) {
		return nil, "sea-safe-changed"
	}
	var foreground *image.RGBA
	if len(candidate.foreground) != 0 {
		if len(candidate.foreground) != 8000 || !((o.kind == "sea-bar" && layer == seaBarRect) || (o.kind == "sea-panel" && layer == seaPanelRect && draftDialogPortraitSource(candidate.foregroundSource))) {
			return nil, "sea-foreground-shape"
		}
		foreground = image.NewRGBA(image.Rect(0, 0, layer.Dx()*4, layer.Dy()*4))
		draw.Draw(foreground, foreground.Bounds(), out, layer.Min.Mul(4), draw.Src)
	}
	for i, v := range row.firstOld {
		if after, ok := row.lastVal[i]; ok && canvas[i] == after && v != after {
			draftPaintPixel(out, i, v, palette, hdBackgroundOverride...)
		}
	}
	draftPaintLayers(out, layer, []*image.Alpha{shadow, fg[68], fg[149]}, []byte{0, 68, 149}, palette)
	protected := 0
	if foreground != nil {
		for y := layer.Min.Y; y < layer.Max.Y; y++ {
			for x := layer.Min.X; x < layer.Max.X; x++ {
				pos := y*320 + x
				if candidate.foreground[pos>>3]&(1<<uint(pos&7)) != 0 {
					draw.Draw(out, image.Rect(x*4, y*4, x*4+4, y*4+4), foreground, image.Pt((x-layer.Min.X)*4, (y-layer.Min.Y)*4), draw.Src)
					protected++
				}
			}
		}
	}
	record := map[string]any{"kind": o.kind, "id": "SEA:" + o.kind, "source": row.text, "text": text.String(), "safe": safe, "font_px": sizes[0], "part_font_px": sizes, "native_ink": row.bbox}
	if protected > 0 {
		sourceID := candidate.foregroundSource
		if sourceID == 0 {
			sourceID = 1061
		}
		record["foreground_source"], record["foreground_pixels"], record["source_background_changes"] = sourceID, protected, candidate.foregroundChanges
		record["baseline_shift_px"] = candidate.textOffsetY
	}
	if candidate.inputDialog != "" {
		record["dialog_occlusion_id"] = candidate.inputDialog
	}
	return record, ""
}

// 重建候選必須保留整個安全區，不能只以少數來源像素相同判定可用。
func draftSameExceptCursor(current, reference []byte, safe, cursor image.Rectangle) bool {
	if len(current) != 64000 || len(reference) != 64000 || safe.Empty() || !safe.In(image.Rect(0, 0, 320, 200)) {
		return false
	}
	for y := safe.Min.Y; y < safe.Max.Y; y++ {
		for x := safe.Min.X; x < safe.Max.X; x++ {
			if !image.Pt(x, y).In(cursor) && current[y*320+x] != reference[y*320+x] {
				return false
			}
		}
	}
	return true
}

func draftRGB(indexed, palette []byte) *image.RGBA {
	out := image.NewRGBA(image.Rect(0, 0, 1280, 800))
	for i, v := range indexed {
		draftPaintPixel(out, i, v, palette)
	}
	return out
}

func draftColor(v byte, palette []byte) color.RGBA {
	p := int(v) * 3
	return color.RGBA{palette[p]<<2 | palette[p]>>4, palette[p+1]<<2 | palette[p+1]>>4, palette[p+2]<<2 | palette[p+2]>>4, 255}
}

func draftPaintPixel(out *image.RGBA, i int, v byte, palette []byte, hdBackgroundOverride ...draftHDBackground) {
	if len(hdBackgroundOverride) > 0 && hdBackgroundOverride[0] != nil && hdBackgroundOverride[0](out,
		i, v, palette,
	) {
		return
	}

	x, y := (i%320)*4, (i/320)*4
	draw.Draw(out, image.Rect(x, y, x+4, y+4), image.NewUniform(draftColor(v, palette)), image.Point{}, draw.Src)
}

func draftPaintLayers(out *image.RGBA, safe image.Rectangle, masks []*image.Alpha, colors []byte, palette []byte) {
	origin := safe.Min.Mul(4)
	for i, mask := range masks {
		if mask != nil {
			draw.DrawMask(out, image.Rectangle{Min: origin, Max: safe.Max.Mul(4)}, image.NewUniform(draftColor(colors[i], palette)), image.Point{}, mask, image.Point{}, draw.Over)
		}
	}
}

func draftExpireRebuilt(d *dialogRuntime, canvas []byte) {
	for _, st := range []*dialogShown{d.prev, d.cur} {
		if st != nil && st.phase != "expired" && !bytes.Equal(rectBytes(canvas, st.safe), st.afterSafe) {
			st.phase = "expired"
		}
	}
}

func draftKeepDialog(d *dialogRuntime, st *dialogShown, canvas []byte) {
	expire := func(old *dialogShown) {
		if old != nil {
			old.phase = "expired"
		}
	}
	if title := d.titleForLoadError(st, canvas); title != nil {
		if d.cur != title {
			expire(d.cur)
		}
		if d.prev != title {
			expire(d.prev)
		}
		d.prev = title
	} else if d.retainSlotTitle(st, canvas) || d.retainChoiceBody(st, canvas) || d.retainBuildTitle(st, canvas) {
		expire(d.cur)
	} else if old := d.cur; old != nil && old.phase != "expired" && !old.safe.Overlaps(st.safe) && st.complete-old.complete < 2000000 {
		expire(d.prev)
		d.prev = old
	} else {
		expire(d.cur)
		expire(d.prev)
		d.prev = nil
	}
	d.cur = st
	st.afterSafe, st.phase = rectBytes(canvas, st.safe), "active"
}

// 規格060 DRAFT：反白重印會先改寫舊清單，仍須用原版未改寫的標題確認新清單身份。
// 只借用辨識上下文，不復活舊清單，也不改變其生命週期。
func draftDialogContext(d *dialogRuntime, r *dialogRun, canvas []byte) *dialogRuntime {
	if d.cur == nil || d.cur.id != "STRING:save-slot+list" || d.cur.phase != "expired" ||
		!saveSlotTitle(d.prev) || d.prev.phase != "active" || r == nil || r.readPos%2 != 0 || len(canvas) != 64000 {
		return d
	}
	lines := runLines(r.chars)
	if len(lines) != 8 && len(lines) != 10 {
		return d
	}
	var ink image.Rectangle
	for _, line := range lines {
		ink = ink.Union(line.box)
	}
	if ink.Overlaps(d.prev.safe) || !bytes.Equal(rectBytes(canvas, d.prev.safe), d.prev.afterSafe) {
		return d
	}
	context := *d
	context.cur, context.prev = d.prev, nil
	return &context
}

func draftAlphaBounds(masks []*image.Alpha) image.Rectangle {
	var ink image.Rectangle
	for _, mask := range masks {
		if mask == nil {
			continue
		}
		for y := mask.Rect.Min.Y; y < mask.Rect.Max.Y; y++ {
			for x := mask.Rect.Min.X; x < mask.Rect.Max.X; x++ {
				if mask.AlphaAt(x, y).A != 0 {
					ink = ink.Union(image.Rect(x, y, x+1, y+1))
				}
			}
		}
	}
	return ink
}

// 覆蓋區內仍逐像素核對。原版被底緣遮掉的墨點只可留在覆蓋區外；每個字格須仍可見。
func draftSlotPaintBounds(o *nativeObservation, masks []*image.Alpha, safe image.Rectangle, canvas, indexed []byte, cursor image.Rectangle) (image.Rectangle, int, bool) {
	if o == nil || o.dialogRun == nil || len(o.after) == 0 || len(canvas) != 64000 || len(indexed) != 64000 {
		return image.Rectangle{}, 0, false
	}
	ink := draftAlphaBounds(masks)
	if ink.Empty() {
		return image.Rectangle{}, 0, false
	}
	paint := image.Rect(safe.Min.X+ink.Min.X/4, safe.Min.Y+ink.Min.Y/4,
		safe.Min.X+(ink.Max.X+3)/4, safe.Min.Y+(ink.Max.Y+3)/4)
	visible := map[int]bool{}
	var missing []image.Point
	for pos, value := range o.after {
		if pos < 0 || pos >= 64000 || canvas[pos] != value || !image.Pt(pos%320, pos/320).In(safe) {
			return image.Rectangle{}, 0, false
		}
		p := image.Pt(pos%320, pos/320)
		if indexed[pos] == value || p.In(cursor) {
			visible[pos] = true
			paint = paint.Union(image.Rectangle{Min: p, Max: p.Add(image.Pt(1, 1))})
		} else {
			missing = append(missing, p)
		}
	}
	for _, ch := range o.dialogRun.chars {
		if ch.box.Empty() {
			continue
		}
		seen := false
		for pos := range visible {
			if image.Pt(pos%320, pos/320).In(ch.box) {
				seen = true
				break
			}
		}
		if !seen {
			return image.Rectangle{}, 0, false
		}
	}
	for _, p := range missing {
		if p.Y < paint.Max.Y {
			return image.Rectangle{}, 0, false
		}
	}
	if !paint.In(safe) || !draftSameExceptCursor(indexed, canvas, paint, cursor) {
		return image.Rectangle{}, 0, false
	}
	return paint, len(missing), true
}

func draftFitSlotDialog(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, canvas, indexed []byte, cursor image.Rectangle) (*dialogShown, int) {
	if st.id != "STRING:save-slot+list" || o == nil || o.dialogRun == nil {
		return nil, 0
	}
	lines := runLines(o.dialogRun.chars)
	if len(lines) != 8 && len(lines) != 10 {
		return nil, 0
	}
	items := make([]string, len(lines))
	capH := 0
	for i, line := range lines {
		var ok bool
		items[i], ok = t.str.translateSaveSlot(line.text)
		if !ok {
			return nil, 0
		}
		capH = max(capH, line.capH)
	}
	_, _, layers, why := lineRoles(lines, st.normalC, st.accentC, st.shadowC)
	if why != "" {
		return nil, 0
	}
	_, floor := dialogSizes(capH)
	for limit := st.size; limit >= floor; limit-- {
		cat := *t.dlg
		cat.fonts = map[int]*dialogFont{}
		for size, font := range t.dlg.fonts {
			if size <= limit {
				cat.fonts[size] = font
			}
		}
		sh, n, ac, dm, size := cat.lineLayerMasks(items, lines, st.safe,
			observedPitch(lines, st.safe.Dy()+3), st.shadowC != 0, layers)
		if size == 0 {
			break
		}
		limit = size
		masks := []*image.Alpha{sh, n, ac, dm}
		paint, clipped, ok := draftSlotPaintBounds(o, masks, st.safe, canvas, indexed, cursor)
		if !ok {
			continue
		}
		crop := func(mask *image.Alpha) *image.Alpha {
			if mask == nil {
				return nil
			}
			out := image.NewAlpha(image.Rect(0, 0, paint.Dx()*4, paint.Dy()*4))
			draw.Draw(out, out.Rect, mask, paint.Min.Sub(st.safe.Min).Mul(4), draw.Src)
			return out
		}
		next := *st
		next.safe, next.size = paint, size
		next.shadow, next.normal, next.accent, next.dim = crop(sh), crop(n), crop(ac), crop(dm)
		return &next, clipped
	}
	return nil, 0
}

// 這個切片重建保留的原文；完整暫停交易另驗，不能據此升READY。
// 規格060：只處理已驗改名對話的原值，不解析玩家文字中的譯文標記。
func draftInputASCII(o *nativeObservation, prompt *dialogShown, fonts map[int]*dialogFont) (*dialogShown, string) {
	if o == nil || o.dialogRun == nil || prompt == nil || prompt.id != "GAME.TXT:0x00000F5C" ||
		prompt.phase == "expired" || len(o.canvas) != 64000 || !bytes.Equal(rectBytes(o.canvas, prompt.safe), prompt.afterSafe) {
		return nil, "input-context"
	}
	r := o.dialogRun
	raw := make([]byte, len(r.chars))
	for i, ch := range r.chars {
		raw[i] = ch.c
	}
	if len(raw) < 8 || !bytes.HasPrefix(raw, []byte("Name: ")) || raw[len(raw)-1] != '_' || len(o.dialogCells) != len(raw) {
		return nil, "input-source"
	}
	for i, ch := range r.chars {
		c := o.dialogCells[i]
		start, end := image.Pt(int(c.StartDI)%320, int(c.StartDI)/320), image.Pt(int(c.EndDI)%320, int(c.EndDI)/320)
		if !c.StartKnown || !c.EndKnown || c.StartES != 0x2cae || c.EndES != 0x2cae ||
			start.Y != 103 || end.Y != 103 || end.X <= start.X || end.X-start.X > 32 ||
			(!ch.box.Empty() && !ch.box.In(image.Rect(start.X, start.Y, end.X, start.Y+16))) ||
			(i >= 7 && c.StartDI != o.dialogCells[i-1].EndDI) {
			return nil, "input-cell"
		}
	}
	if o.dialogCells[0].StartDI != 103*320+62 || o.dialogCells[6].StartDI != 103*320+95 {
		return nil, "input-origin"
	}
	text := string(raw[6 : len(raw)-1])
	for _, c := range []byte(text) {
		if c < 0x20 || c > 0x7e {
			return nil, "input-byte"
		}
	}
	caret := int(o.dialogCells[len(raw)-1].StartDI) % 320
	if caret <= 96 || caret > 218 {
		return nil, "input-width"
	}
	var ink image.Rectangle
	capHeight := 0
	for _, ch := range r.chars[6 : len(raw)-1] {
		ink = ink.Union(ch.box)
		capHeight = max(capHeight, ch.box.Dy())
		for c := range ch.colors {
			if c != 68 && c != 47 && c != 128 {
				return nil, "input-style"
			}
		}
		if ch.c != ' ' {
			visible := false
			for y := ch.box.Min.Y; y < ch.box.Max.Y; y++ {
				for x := ch.box.Min.X; x < ch.box.Max.X; x++ {
					i := y*320 + x
					value, ok := o.after[i]
					visible = visible || ok && value == 68 && o.canvas[i] == 68
					if !r.lastText[i] {
						if _, written := r.firstOld[i]; written {
							return nil, "input-erased"
						}
					}
				}
			}
			if !visible {
				return nil, "input-erased"
			}
		}
	}
	if ink.Empty() || capHeight > 9 || ink.Min.Y < 103 || ink.Max.Y > 112 {
		return nil, "input-ink"
	}
	// 原版字型的大寫高度8、基線111來自此欄證據；姓名大小寫不改變基線。
	var plan *retainedASCIIPlan
	baseline := 0
	for size := stringFloorPx; size <= stringFontPx; size++ {
		f := fonts[size]
		if f == nil {
			continue
		}
		bounds, ok := retainedTextBounds(f, text)
		capital, capOK := retainedTextBounds(f, "H")
		if !ok || !capOK || capital.Dy() > 8*4 || bounds.Dx() > (caret-96)*4 {
			continue
		}
		y := 9*4 - capital.Max.Y
		if bounds.Min.Y+y < 4 || bounds.Max.Y+y+4 > 11*4 {
			continue
		}
		if plan == nil || size > plan.size {
			plan = &retainedASCIIPlan{size, bounds, f}
			baseline = y
		}
	}
	if plan == nil {
		return nil, "input-font"
	}
	safe := image.Rect(94, 102, caret, 113)
	normal := image.NewAlpha(image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4))
	x, y := 4-plan.bounds.Min.X, baseline
	for _, c := range text {
		dialogBlit(normal, plan.font.glyphs[c], x, y)
		x += plan.font.widths[c]
	}
	shadow := image.NewAlpha(normal.Rect)
	dialogBlit(shadow, normal, 4, 4)
	if !draftAlphaBounds([]*image.Alpha{normal, shadow}).In(normal.Rect) {
		return nil, "input-mask"
	}
	before := bytes.Clone(o.canvas)
	for i, alive := range r.lastText {
		if alive && image.Pt(i%320, i/320).In(safe) {
			before[i] = r.firstOld[i]
		}
	}
	return &dialogShown{id: "STRING:input-ascii", zh: text, safe: safe, size: plan.size,
		normal: normal, shadow: shadow, normalC: 68, shadowC: 47, before: before, afterSafe: rectBytes(o.canvas, safe), phase: "waiting-screen"}, ""
}

func draftRebuildTarget(t *draftLanguageTarget, j *nativeJournal, canvas, buffer, indexed, palette []byte, cursor image.Rectangle, step uint64, mode byte) (*image.RGBA, map[string]any, error) {
	return draftRebuildTargetOn(t, j, canvas, buffer, indexed, palette, cursor, step, mode, nil)
}
func draftRebuildTargetOn(t *draftLanguageTarget, j *nativeJournal, canvas, buffer, indexed, palette []byte, cursor image.Rectangle, step uint64, mode byte, base *image.RGBA, hdBackgroundOverride ...draftHDBackground) (*image.RGBA, map[string]any, error) {
	if len(canvas) != 64000 || len(buffer) != 64000 || len(indexed) != 64000 || len(palette) != 768 {
		return nil, nil, fmt.Errorf("invalid native frame")
	}
	out := base
	if out == nil {
		out = draftRGB(indexed, palette)
	}
	result := map[string]any{"locale": t.pack.manifest.Locale, "original_rendering": t.pack.manifest.Original, "step": step}
	if t.pack.manifest.Original {
		result["items"] = []map[string]any{}
		return out, result, nil
	}
	d := &dialogRuntime{cat: t.dlg, misses: map[string]int{}}
	dialogSources := map[*dialogShown]*nativeObservation{}
	var diagnosticDialogs []*dialogShown
	retainedSources := map[*stringItem]*nativeObservation{}
	mapSources := map[*stringItem]*nativeObservation{}
	var inputASCII *dialogShown
	var landfallBody *dialogShown
	var attackBody *dialogShown
	attackPaired := false
	landfallPaired := false
	s := &stringRuntime{cat: t.str, misses: map[string]int{}}
	var context []byte
	var contextStep uint64
	d.readCanvas = func() []byte { return context }
	d.slotFallback = s.cat.translateSaveSlot
	d.lineFallback = func(text string) (string, bool) {
		if len(stringLetter.FindAllString(text, 2)) < 2 {
			return "", false
		}
		z, _, why := s.cat.translate(text)
		return z, why == ""
	}
	d.lineFallbackAt = func(text string, line int) (string, bool) {
		return s.routePortTranslate(text, line, context, d.cur, contextStep)
	}
	var records []map[string]any
	var seaRows []*draftSeaRow
	seaMisses := map[string]int{}
	for _, o := range j.items {
		context, contextStep = o.canvas, o.step
		draftExpireRebuilt(d, context)
		if len(o.seaRuns) > 0 {
			// 沿規格032的原版行替換規則，不以目標語言排版決定原文存活。
			kept := seaRows[:0]
			for _, old := range seaRows {
				if !old.row.bbox.Overlaps(o.ink) {
					kept = append(kept, old)
				}
			}
			seaRows = kept
			row, why := draftSeaObserve(t.sea, o)
			if row != nil {
				seaRows = append(seaRows, row)
			} else {
				var source strings.Builder
				for _, run := range o.seaRuns {
					source.Write(bytes.TrimRight(run.raw, "\x00"))
				}
				seaMisses[why+"\t"+source.String()]++
			}
		}
		if r := o.dialogRun; r != nil {
			for _, prompt := range []*dialogShown{d.prev, d.cur} {
				if prompt != nil && prompt.id == "GAME.TXT:0x00000F5C" {
					if candidate, why := draftInputASCII(o, prompt, t.str.fonts); candidate != nil {
						inputASCII = candidate
					} else if strings.HasPrefix(dialogShownText(r.chars), "Name: ") {
						inputASCII = nil
						d.misses[why+"\t"+dialogShownText(r.chars)]++
					}
				}
			}
			scoped := draftDialogContext(d, r, context)
			scoped = draftLandfallDialogContext(t, scoped, landfallBody, dialogSources[landfallBody], o, palette, cursor, landfallPaired)
			scoped = draftAttackDialogContext(t, scoped, attackBody, dialogSources[attackBody], o, canvas, indexed, palette, cursor, attackPaired)
			st, shown, why := scoped.finish(cloneNativeDialog(r), context, o.step)
			if st != nil {
				if *draftNativeCapture {
					diagnosticDialogs = append(diagnosticDialogs, st)
				}
				if st.id == "GAME.TXT:@LANDFALL:0x00000FAD" {
					landfallBody, landfallPaired = st, false
				} else if landfallBody != nil && draftLandfallChoice(t, st) &&
					st.complete >= landfallBody.complete && st.complete-landfallBody.complete < 2000000 {
					landfallPaired = true
				}
				if st.id == "GAME.TXT:@WHACKINDIANS:0x000038BD" {
					attackBody, attackPaired = st, false
				} else if attackBody != nil && draftAttackChoice(t, st) &&
					st.complete >= attackBody.complete && st.complete-attackBody.complete < 2000000 {
					attackPaired = true
				}
				draftKeepDialog(d, st, context)
				dialogSources[st] = o
			} else if why != "" {
				d.misses[why+"\t"+shown]++
			}
		}
		if r := o.stringRun; r != nil {
			var it *stringItem
			var why string
			if r.buf2 {
				it, why = s.finishLabel(cloneNativeString(r), o.buffer, context, o.step)
			} else {
				it, why = s.finish(cloneNativeString(r), context, o.step, seaPanelRect)
				if it == nil {
					it, why = finishRetainedASCII(s, cloneNativeString(r), context, o.step, why)
				}
			}
			if it != nil {
				s.add(it)
				if r.buf2 {
					mapSources[it] = o
				}
				if it.id == "STRING:retained-ascii" {
					retainedSources[it] = o
				}
			} else if why != "" {
				s.misses[why+"\t"+string(r.text)]++
			}
		}
	}
	if mode != 0x13 {
		result["items"] = records
		result["reason"] = "mode-changed"
		return out, result, nil
	}
	var dialogSafes []image.Rectangle
	var fixedSafes []image.Rectangle
	fixedMisses := map[string]int{}
	for _, o := range j.items {
		if o.fixed == nil || o.fixed.expired {
			continue
		}
		record, why := draftPaintFixed(out, t.fixed[o.fixed.id], o, j, canvas, indexed, palette, cursor, hdBackgroundOverride...)
		if record != nil {
			records = append(records, record)
			fixedSafes = append(fixedSafes, o.fixed.safe)
		} else {
			fixedMisses[why+"\t"+o.fixed.id]++
		}
	}
	var seaClaims []image.Rectangle
	inputProtection := draftVerifiedInputDialog(t, j, canvas, indexed, palette, cursor)
	for _, row := range seaRows {
		row = draftPreserveSoldierMenu(t, row, canvas, indexed, palette, cursor)
		row = draftPreserveDialogSea(t, row, canvas, indexed, palette, cursor, inputProtection)
		record, why := draftPaintSea(out, t.sea, row, canvas, indexed, palette, cursor, hdBackgroundOverride...)
		if record != nil {
			records = append(records, record)
			seaClaims = append(seaClaims, row.row.bbox)
		} else {
			seaMisses[why+"\t"+row.row.text]++
		}
	}
	if inputASCII != nil {
		livePrompt := false
		for _, prompt := range []*dialogShown{d.prev, d.cur} {
			livePrompt = livePrompt || prompt != nil && prompt.id == "GAME.TXT:0x00000F5C" && prompt.phase != "expired" && bytes.Equal(rectBytes(canvas, prompt.safe), prompt.afterSafe)
		}
		if !livePrompt {
			inputASCII = nil
		}
	}
	dialogStates := []*dialogShown{d.prev, d.cur, inputASCII}
	if landfallPaired && landfallBody != nil && landfallBody != d.prev && landfallBody != d.cur {
		dialogStates = append(dialogStates, landfallBody)
	}
	if attackPaired && attackBody != nil && attackBody != d.prev && attackBody != d.cur {
		dialogStates = append(dialogStates, attackBody)
	}
	for _, st := range dialogStates {
		var namingLayout map[string]any
		if st != nil && st.id == "GAME.TXT:@LANDHO:0x00000ECE" {
			st, namingLayout = draftFitLandHoDialog(t, st, dialogSources[st], canvas, indexed, palette, cursor)
			if st == nil {
				d.misses["land-ho-source-or-layout"]++
				continue
			}
		}
		immigrationChanged := -1
		if st != nil && st.id == "GAME.TXT:@TUTORIAL5" {
			original := st
			st, immigrationChanged = draftFitImmigrationTutorial(t, st, dialogSources[st], canvas, indexed, palette, cursor)
			if st == nil {
				d.misses["immigration-source-or-layout\t"+original.id]++
				continue
			}
		}
		soldierChanged := -1
		if st != nil && st.id == "GAME.TXT:@TUTORIAL14" {
			st, soldierChanged = draftFitSoldierDialog(t, st, dialogSources[st], canvas, indexed, palette, cursor)
		}
		landfallChanged := -1
		if st != nil && st.id == "GAME.TXT:@LANDFALL:0x00000FAD" {
			if !landfallPaired {
				continue
			}
			original := st
			st, landfallChanged = draftFitLandfallDialog(t, st, dialogSources[st], d.cur, canvas, indexed, palette, cursor)
			if st == nil {
				d.misses["landfall-source-or-layout\t"+original.id]++
				continue
			}
		}
		attackChanged := -1
		if st != nil && st.id == "GAME.TXT:@WHACKINDIANS:0x000038BD" {
			if !attackPaired {
				continue
			}
			original := st
			st, attackChanged = draftFitAttackDialog(t, st, dialogSources[st], d.cur, canvas, indexed, palette, cursor)
			if st == nil {
				d.misses["attack-source-or-layout\t"+original.id]++
				continue
			}
		}
		if st == nil || st.phase == "expired" || !bytes.Equal(rectBytes(canvas, st.safe), st.afterSafe) {
			continue
		}
		sourceSafe, clipped := st.safe, 0
		if !draftSameExceptCursor(indexed, canvas, st.safe, cursor) {
			fitted, count := draftFitSlotDialog(t, st, dialogSources[st], canvas, indexed, cursor)
			if fitted == nil {
				if st.id == "STRING:save-slot+list" {
					d.misses["slot-vga-safe-changed\t"+st.id]++
				}
				continue
			}
			st, clipped = fitted, count
		}
		for y := st.safe.Min.Y; y < st.safe.Max.Y; y++ {
			for x := st.safe.Min.X; x < st.safe.Max.X; x++ {
				i := y*320 + x
				if !image.Pt(x, y).In(cursor) && st.before[i] != canvas[i] {
					draftPaintPixel(out, i, st.before[i], palette, hdBackgroundOverride...)
				} else if image.Pt(x, y).In(cursor) && st.before[i] != canvas[i] && len(hdBackgroundOverride) > 0 && hdBackgroundOverride[0] != nil {
					hdBackgroundOverride[0](out, i, st.before[i], palette)
				}
			}
		}
		draftPaintLayers(out, st.safe, []*image.Alpha{st.shadow, st.normal, st.accent, st.dim}, []byte{st.shadowC, st.normalC, st.accentC, st.dimC}, palette)
		dialogSafes = append(dialogSafes, st.safe)
		record := map[string]any{"kind": "dialog", "id": st.id, "text": st.zh, "safe": st.safe, "font_px": st.size}
		for key, value := range namingLayout {
			record[key] = value
		}
		if immigrationChanged >= 0 {
			layout := st.safe
			layout.Min.Y = 125
			record["layout_safe"], record["foreground_source"], record["foreground_pixels"], record["native_occluded_pixels"] = layout, 1060, 3306, immigrationChanged
		}
		if soldierChanged >= 0 {
			layout := st.safe
			layout.Max.X = 208
			record["layout_safe"], record["foreground_source"], record["foreground_pixels"], record["native_occluded_pixels"] = layout, 1061, 4429, soldierChanged
		}
		if landfallChanged >= 0 {
			layout := st.safe
			layout.Min.Y = 124
			record["layout_safe"], record["foreground_source"], record["foreground_pixels"], record["native_occluded_pixels"] = layout, 1063, 5910, landfallChanged
		}
		if attackChanged >= 0 {
			layout := st.safe
			layout.Max.X = 193
			layout.Min.Y = 117
			record["layout_safe"], record["foreground_source"], record["foreground_pixels"], record["native_occluded_pixels"] = layout, 1061, 4429, attackChanged
		}
		if st.safe != sourceSafe {
			record["source_safe"], record["native_clipped_pixels"] = sourceSafe, clipped
		}
		records = append(records, record)
	}
	for _, it := range s.items {
		sourceSafe := it.safe
		mapSource := mapSources[it]
		mapChanges, mapClipped := 0, 0
		if mapSource != nil {
			fitted, changes, clipped := draftFitMapLabel(it, mapSource, j, canvas, indexed, cursor)
			if fitted == nil {
				s.misses["map-source-or-occlusion-changed\t"+it.text]++
				continue
			}
			it, mapChanges, mapClipped = fitted, changes, clipped
		}
		if it.id == "STRING:retained-ascii" && (!stringSame(canvas, it, image.Rectangle{}) || !draftSameExceptCursor(indexed, canvas, it.safe, cursor)) {
			if fitted := draftFitRetainedASCII(it, retainedSources[it], canvas, indexed, cursor); fitted != nil {
				it = fitted
			}
		}
		// 完整安全區不相同時回原文；本切片尚未處理部分遮擋與畫面世代。
		if !stringSame(canvas, it, image.Rectangle{}) {
			s.misses["source-safe-changed\t"+it.text]++
			continue
		}
		if !draftSameExceptCursor(indexed, canvas, it.safe, cursor) {
			s.misses["vga-safe-changed\t"+it.text]++
			continue
		}
		blocked := false
		for _, safe := range dialogSafes {
			blocked = blocked || safe.Inset(2).Overlaps(it.safe)
		}
		for _, ink := range seaClaims {
			blocked = blocked || ink.Overlaps(it.ink)
		}
		for _, safe := range fixedSafes {
			blocked = blocked || safe.Inset(2).Overlaps(it.safe)
		}
		if blocked {
			s.misses["claimed-safe-area\t"+it.text]++
			continue
		}
		// 重建項目沒有歷史phase；以當次原版VGA核對來源，不沿用waiting-screen。
		if it.id == "STRING:retained-ascii" && !stringSame(indexed, it, cursor) {
			s.misses["retained-vga-changed\t"+it.text]++
			continue
		}
		k := 0
		for y := it.safe.Min.Y; y < it.safe.Max.Y; y++ {
			for x := it.safe.Min.X; x < it.safe.Max.X; x++ {
				if !image.Pt(x, y).In(cursor) && it.before[k] != it.after[k] {
					draftPaintPixel(out, y*320+x, it.before[k], palette, hdBackgroundOverride...)
				} else if image.Pt(x, y).In(cursor) && it.before[k] != it.after[k] && len(hdBackgroundOverride) > 0 && hdBackgroundOverride[0] != nil {
					hdBackgroundOverride[0](out, y*320+x, it.before[k], palette)
				}
				k++
			}
		}
		if base != nil && strings.HasPrefix(it.id, "STRING:woodcut:") {
			draftPaintWoodcutGold(out, it.safe, []*image.Alpha{it.shadow, it.norm, it.accent})
		} else {
			draftPaintLayers(out, it.safe, []*image.Alpha{it.shadow, it.norm, it.accent}, []byte{it.shadowColor, it.color, it.accentColor}, palette)
		}
		record := map[string]any{"kind": "string", "id": it.id, "source": it.text, "text": it.zh, "safe": it.safe, "font_px": it.size}
		if base != nil && strings.HasPrefix(it.id, "STRING:woodcut:") {
			record["title_style"] = "gold"
		}
		if mapSource != nil {
			record["native_surface"], record["native_ink"] = "map", it.ink
			record["native_background_changes"], record["native_shadow_clipped_pixels"] = mapChanges, mapClipped
		}
		if it.safe != sourceSafe {
			record["source_safe"], record["unused_padding_changed"] = sourceSafe, true
		}
		records = append(records, record)
	}
	portLabel, portLabelMiss := draftPaintColonyNoShips(out, t, canvas, indexed, palette, cursor, records, hdBackgroundOverride...)
	if portLabel != nil {
		records = append(records, portLabel)
	}
	fontOnly, fontMisses := draftPaintOriginalNoto(out, t, j, canvas, indexed, palette, cursor, records, hdBackgroundOverride...)
	if portLabelMiss != "" {
		fontMisses[portLabelMiss]++
	}
	records = append(records, fontOnly...)
	declaration := draftPaintDeclarationNoto(out, t, canvas, indexed, palette, cursor, records)
	records = append(records, declaration...)
	result["font_only_misses"] = fontMisses
	// 只回貼原版游標改動的像素，保留游標框內未被遮擋的文字。
	for y := max(0, cursor.Min.Y); y < min(200, cursor.Max.Y); y++ {
		for x := max(0, cursor.Min.X); x < min(320, cursor.Max.X); x++ {
			i := y*320 + x
			if indexed[i] != canvas[i] {
				draftPaintPixel(out, i, indexed[i], palette, hdBackgroundOverride...)
			}
		}
	}
	result["items"], result["dialog_misses"], result["string_misses"] = records, d.misses, s.misses
	result["sea_misses"] = seaMisses
	result["fixed_misses"] = fixedMisses
	if *draftNativeCapture {
		var states []map[string]any
		for _, st := range diagnosticDialogs {
			states = append(states, map[string]any{"id": st.id, "safe": st.safe, "phase": st.phase,
				"step": st.complete, "source_ink": dialogSources[st].ink,
				"source_unchanged": bytes.Equal(rectBytes(canvas, st.safe), st.afterSafe)})
		}
		result["dialog_states"] = states
	}
	result["limitations"] = []string{"隔離重建目前只驗證抽樣正常路徑；完整來源生命週期仍待驗。", "未驗欄位、部分遮擋與畫面世代仍依原文回退。"}
	return out, result, nil
}

// draftFitRetainedASCII只排除未繪字的外緣；來源與整個排版區仍須完整相同。
func draftFitRetainedASCII(it *stringItem, o *nativeObservation, canvas, indexed []byte, cursor image.Rectangle) *stringItem {
	if it == nil || it.id != "STRING:retained-ascii" || o == nil || o.stringRun == nil ||
		o.kind != "string" || o.ink != it.ink || o.step != it.complete || string(o.stringRun.text) != it.text || len(canvas) != 64000 || len(indexed) != 64000 {
		return nil
	}
	r := o.stringRun
	layout, valid := retainedASCIILayout(r, it.ink)
	if !valid || it.safe != layout.Inset(-1).Intersect(image.Rect(0, 0, 320, 200)) ||
		len(it.before) != it.safe.Dx()*it.safe.Dy() || len(it.after) != len(it.before) || len(o.after) == 0 {
		return nil
	}
	for pos, value := range o.after {
		if pos < 0 || pos >= 64000 || !image.Pt(pos%320, pos/320).In(layout) || canvas[pos] != value {
			return nil
		}
	}
	for y := layout.Min.Y; y < layout.Max.Y; y++ {
		for x := layout.Min.X; x < layout.Max.X; x++ {
			old := (y-it.safe.Min.Y)*it.safe.Dx() + x - it.safe.Min.X
			if canvas[y*320+x] != it.after[old] {
				return nil
			}
		}
	}
	if !draftSameExceptCursor(indexed, canvas, layout, cursor) {
		return nil
	}
	offset := layout.Min.Sub(it.safe.Min).Mul(4)
	paint := image.Rect(offset.X, offset.Y, offset.X+layout.Dx()*4, offset.Y+layout.Dy()*4)
	hasInk := false
	for _, mask := range []*image.Alpha{it.norm, it.shadow, it.accent} {
		if mask == nil || mask.Rect != image.Rect(0, 0, it.safe.Dx()*4, it.safe.Dy()*4) {
			return nil
		}
		for y := mask.Rect.Min.Y; y < mask.Rect.Max.Y; y++ {
			for x := mask.Rect.Min.X; x < mask.Rect.Max.X; x++ {
				if mask.AlphaAt(x, y).A != 0 {
					hasInk = true
					if !image.Pt(x, y).In(paint) {
						return nil
					}
				}
			}
		}
	}
	if !hasInk {
		return nil
	}
	crop := func(mask *image.Alpha) *image.Alpha {
		next := image.NewAlpha(image.Rect(0, 0, paint.Dx(), paint.Dy()))
		draw.Draw(next, next.Rect, mask, paint.Min, draw.Src)
		return next
	}
	cropBytes := func(data []byte) []byte {
		next := make([]byte, layout.Dx()*layout.Dy())
		for y := 0; y < layout.Dy(); y++ {
			start := (layout.Min.Y-it.safe.Min.Y+y)*it.safe.Dx() + layout.Min.X - it.safe.Min.X
			copy(next[y*layout.Dx():(y+1)*layout.Dx()], data[start:start+layout.Dx()])
		}
		return next
	}
	next := *it
	next.safe = layout
	next.before, next.after = cropBytes(it.before), cropBytes(it.after)
	next.norm, next.shadow, next.accent = crop(it.norm), crop(it.shadow), crop(it.accent)
	return &next
}

// draftMapMaskAt用原版邏輯像素量測四倍alpha；原版後畫內容有優先權。
func draftMapMaskAt(mask *image.Alpha, safe image.Rectangle, p image.Point) bool {
	if mask == nil {
		return false
	}
	x0, y0 := (p.X-safe.Min.X)*4, (p.Y-safe.Min.Y)*4
	for y := y0; y < y0+4; y++ {
		for x := x0; x < x0+4; x++ {
			if mask.AlphaAt(x, y).A != 0 {
				return true
			}
		}
	}
	return false
}

func draftFitMapLabel(it *stringItem, o *nativeObservation, j *nativeJournal, canvas, indexed []byte, cursor image.Rectangle) (*stringItem, int, int) {
	if it == nil || o == nil || j == nil || o.stringRun == nil || it.id != "STRING:colony" ||
		o.kind != "string-map" || o.step != it.complete || o.ink != it.ink || string(o.stringRun.text) != it.text ||
		len(canvas) != 64000 || len(indexed) != 64000 || len(o.buffer) != 64000 || len(o.after) == 0 ||
		it.ink.Empty() || !it.ink.In(it.safe) || !it.safe.In(stringMapView) ||
		len(it.before) != it.safe.Dx()*it.safe.Dy() || len(it.after) != len(it.before) ||
		it.color == 0 || it.shadowColor != 0 || it.shadowOff != -stringLabelOutline || it.accent != nil {
		return nil, 0, 0
	}
	r := o.stringRun
	if !r.buf2 || r.mixed || r.outline || r.keyColor != 0 || len(r.colors) != 2 || r.colors[0] == 0 || r.colors[it.color] == 0 ||
		!bytes.Equal(it.after, stringRect(o.buffer, it.safe)) || !draftSameExceptCursor(indexed, canvas, it.safe, cursor) {
		return nil, 0, 0
	}
	for pos, value := range o.after {
		if pos < 0 || pos >= 64000 || !image.Pt(pos%320, pos/320).In(it.ink) || canvas[pos] != value {
			return nil, 0, 0
		}
	}
	rect := image.Rect(0, 0, it.safe.Dx()*4, it.safe.Dy()*4)
	if it.norm == nil || it.shadow == nil || it.norm.Rect != rect || it.shadow.Rect != rect {
		return nil, 0, 0
	}
	hasNormal := false
	for _, value := range it.norm.Pix {
		hasNormal = hasNormal || value != 0
	}
	if !hasNormal {
		return nil, 0, 0
	}
	changed := []image.Point{}
	for y := it.safe.Min.Y; y < it.safe.Max.Y; y++ {
		for x := it.safe.Min.X; x < it.safe.Max.X; x++ {
			pos := y*320 + x
			k := (y-it.safe.Min.Y)*it.safe.Dx() + x - it.safe.Min.X
			p := image.Pt(x, y)
			expectedBefore := o.buffer[pos]
			if value, ok := r.firstOld[pos]; ok {
				expectedBefore = value
			}
			if it.before[k] != expectedBefore {
				return nil, 0, 0
			}
			if !p.In(it.ink) && it.before[k] != it.after[k] {
				return nil, 0, 0
			}
			if canvas[pos] != it.after[k] {
				if p.In(it.ink) || draftMapMaskAt(it.norm, it.safe, p) {
					return nil, 0, 0
				}
				changed = append(changed, p)
			}
		}
	}
	// 同一預設名的歷史重印由完整原版墨跡守門；其他仍存活的離屏字形不能被蓋住。
	for _, other := range j.items {
		if other == nil || other.stringRun == nil || other.kind != "string-map" ||
			(other.ink == it.ink && string(other.stringRun.text) == it.text) {
			continue
		}
		for pos, value := range other.after {
			if pos < 0 || pos >= 64000 {
				return nil, 0, 0
			}
			p := image.Pt(pos%320, pos/320)
			if canvas[pos] == value && (draftMapMaskAt(it.norm, it.safe, p) || draftMapMaskAt(it.shadow, it.safe, p)) {
				return nil, 0, 0
			}
		}
	}
	if len(changed) == 0 {
		return it, 0, 0
	}
	next := *it
	next.before, next.after = bytes.Clone(it.before), bytes.Clone(it.after)
	clone := func(mask *image.Alpha) *image.Alpha {
		copy := image.NewAlpha(mask.Rect)
		draw.Draw(copy, copy.Rect, mask, mask.Rect.Min, draw.Src)
		return copy
	}
	next.norm, next.shadow = clone(it.norm), clone(it.shadow)
	clipped := 0
	for _, p := range changed {
		k := (p.Y-it.safe.Min.Y)*it.safe.Dx() + p.X - it.safe.Min.X
		next.before[k], next.after[k] = canvas[p.Y*320+p.X], canvas[p.Y*320+p.X]
		x0, y0 := (p.X-it.safe.Min.X)*4, (p.Y-it.safe.Min.Y)*4
		for y := y0; y < y0+4; y++ {
			for x := x0; x < x0+4; x++ {
				if next.shadow.AlphaAt(x, y).A != 0 {
					clipped++
					next.shadow.Pix[next.shadow.PixOffset(x, y)] = 0
				}
			}
		}
	}
	return &next, len(changed), clipped
}

// 僅供已驗Noto預設城名：依完整文案實際墨跡對齊原版填色上緣，選出可用最大字級。
func draftNotoMapLabelMasks(fonts map[int]*dialogFont, text string, fill, ink image.Rectangle, capH int) (sh, n *image.Alpha, safe image.Rectangle, size int) {
	if text == "" || capH <= 0 || ink.Empty() || fill.Empty() || !fill.In(ink) || !ink.In(stringMapView) {
		return nil, nil, image.Rectangle{}, 0
	}
	start, _ := stringStartPx(capH)
	limit := (ink.Dx() + stringLabelWiden) * 4
	cx4 := (fill.Min.X + fill.Max.X) * 2
	for size = min(start, stringFontPx); size >= stringFloorPx; size-- {
		f := fonts[size]
		if f == nil {
			continue
		}
		bounds, ok := retainedTextBounds(f, text)
		if !ok || bounds.Dy() > capH*4+4 {
			continue
		}
		width := 0
		for _, ch := range text {
			width += f.widths[ch]
		}
		if max(width, bounds.Max.X)-min(0, bounds.Min.X) > limit {
			continue
		}
		x0 := cx4 - width/2
		top := fill.Min.Y*4 - bounds.Min.Y
		paint := bounds.Add(image.Pt(x0, top)).Inset(-stringLabelOutline)
		logical := image.Rect(paint.Min.X/4-1, paint.Min.Y/4-1, (paint.Max.X+3)/4+1, (paint.Max.Y+3)/4+1)
		safe = ink.Inset(-1).Union(logical)
		if !safe.In(stringMapView) {
			continue
		}
		rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
		sh, n = image.NewAlpha(rect), image.NewAlpha(rect)
		x, y := x0-safe.Min.X*4, top-safe.Min.Y*4
		for _, ch := range text {
			glyph := f.glyphs[ch]
			dialogBlit(n, glyph, x, y)
			for _, d := range [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}, {-1, -1}, {1, 1}, {-1, 1}, {1, -1}} {
				dialogBlit(sh, glyph, x+d[0]*stringLabelOutline, y+d[1]*stringLabelOutline)
			}
			x += f.widths[ch]
		}
		return sh, n, safe, size
	}
	return nil, nil, image.Rectangle{}, 0
}

func draftExportRebuilds(targets map[string]*draftLanguageTarget, j *nativeJournal, canvas, buffer, indexed, palette []byte, cursor image.Rectangle, step uint64, mode byte, out string) error {
	before := hash(bytes.Join([][]byte{canvas, buffer, indexed, palette}, nil))
	backend := &draftLanguageBackend{targets: targets, sample: func() draftNativeFrame {
		return draftNativeFrame{j, canvas, buffer, indexed, palette, cursor, step, mode}
	}}
	preferences := out + ".display-preferences.json"
	initial := displayOptions{"en", "original", 0}
	if err := applyDisplayPreferences(preferences, initial, backend.prepare); err != nil {
		return err
	}
	var transactions []map[string]any
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		options := displayOptions{locale, "original", 0}
		old := backend.active
		oldPixels := hash(old.frame.Pix)
		saved, err := os.ReadFile(preferences)
		if err != nil {
			return err
		}
		cancelled, err := backend.prepare(options)
		if err != nil || cancelled == nil || backend.active != old || hash(old.frame.Pix) != oldPixels {
			return fmt.Errorf("language preparation changed active view: %s: %v", locale, err)
		}
		// 不呼叫cancelled就是既有面板的取消；保存失敗沿原有交易函式。
		if err := applyDisplayPreferences(filepath.Join(preferences, "blocked.json"), options, backend.prepare); err == nil || err.Error() != "ui.error.save" {
			return fmt.Errorf("language save failure accepted: %s: %v", locale, err)
		}
		afterFailure, err := os.ReadFile(preferences)
		if err != nil || !bytes.Equal(saved, afterFailure) || backend.active != old || hash(old.frame.Pix) != oldPixels {
			return fmt.Errorf("cancel or save failure changed active language: %s", locale)
		}
		if err := applyDisplayPreferences(preferences, options, backend.prepare); err != nil {
			return err
		}
		active := backend.active
		persisted, err := readDisplayPreferences(preferences, "", "")
		if err != nil || persisted != options || active.options != options || active.target != targets[locale] {
			return fmt.Errorf("language bundle transaction mismatch: %s", locale)
		}
		im, record := active.frame, active.receipt
		record["kind"] = "DRAFT-paused-native-text-rebuild"
		record["rgba_sha256"] = hash(im.Pix)
		savePNG(out+".rebuild-"+locale+".png", im)
		dumpJSON(out+".rebuild-"+locale+".json", record)
		transactions = append(transactions, map[string]any{"locale": locale, "cancel_kept_active": true,
			"save_failure_kept_active_and_preferences": true, "whole_target_committed": true,
			"rgba_sha256": hash(im.Pix), "saved": persisted})
	}
	after := hash(bytes.Join([][]byte{canvas, buffer, indexed, palette}, nil))
	if before != after {
		return fmt.Errorf("rebuild mutated native frame")
	}
	dumpJSON(out+".language-transactions.json", map[string]any{"kind": "DRAFT-language-bundle-transactions",
		"step": step, "native_before_sha256": before, "native_after_sha256": after, "transactions": transactions})
	return nil
}

type draftHDBackground func(*image.RGBA, int, byte, []byte) bool

// 規格069 R97 READY：三個已驗標題各自量測Noto實際alpha，舊Cubic路徑保持。
func draftNotoWoodcutMasks(fonts map[int]*dialogFont, id, text string, ink, safe image.Rectangle, capH int) (sh, n, ac *image.Alpha, size int) {
	fields := map[string]image.Rectangle{
		"WOODCUT.TXT:0x00000017": image.Rect(60, 165, 259, 172),
		"WOODCUT.TXT:0x00000033": image.Rect(96, 165, 223, 172),
		"WOODCUT.TXT:0x00000046": image.Rect(90, 165, 230, 172),
		"WOODCUT.TXT:0x0000009E": image.Rect(74, 165, 246, 172),
	}
	expected, known := fields[id]
	if !known || text == "" || ink != expected || safe != ink.Inset(-1) || capH != 7 {
		return nil, nil, nil, 0
	}
	measured := map[int]*dialogFont{}
	for px, font := range fonts {
		if font == nil {
			continue
		}
		top, bottom := 0, 0
		hasInk := false
		valid := true
		for _, char := range text {
			glyph := font.glyphs[char]
			if glyph == nil || font.widths[char] <= 0 {
				valid = false
				break
			}
			for y := glyph.Rect.Min.Y; y < glyph.Rect.Max.Y; y++ {
				for x := glyph.Rect.Min.X; x < glyph.Rect.Max.X; x++ {
					if glyph.AlphaAt(x, y).A != 0 {
						if !hasInk || y < top {
							top = y
						}
						bottom = max(bottom, y+1)
						hasInk = true
					}
				}
			}
		}
		if !valid || !hasInk || bottom <= top {
			continue
		}
		copyFont := *font
		copyFont.cjkTop, copyFont.cjkBottom = top, bottom
		measured[px] = &copyFont
	}
	catalog := &stringCatalog{fonts: measured}
	return catalog.woodcutMasks(text, ink, safe, capH)
}

// 規格069 R118：使用者指定的HD事件標題金色，只改放大畫布的RGB。
func draftPaintWoodcutGold(out *image.RGBA, safe image.Rectangle, masks []*image.Alpha) {
	colors := []color.RGBA{{53, 28, 8, 255}, {243, 205, 99, 255}, {255, 240, 175, 255}}
	origin := safe.Min.Mul(4)
	for i, mask := range masks {
		if mask != nil {
			draw.DrawMask(out, image.Rectangle{Min: origin, Max: safe.Max.Mul(4)}, image.NewUniform(colors[i]), image.Point{}, mask, image.Point{}, draw.Over)
		}
	}
}

// 英文沿已驗原版來源遮罩上色，保留原版字形與每個4倍像素的位置。
func draftPaintNativeWoodcutGold(out *image.RGBA, cat *stringCatalog, j *nativeJournal, canvas, indexed []byte, cursor image.Rectangle, covered map[string]bool) []map[string]any {
	records := []map[string]any{}
	if cat == nil || j == nil || len(canvas) != 64000 || len(indexed) != 64000 {
		return records
	}
	for _, o := range j.items {
		if o == nil || o.stringRun == nil {
			continue
		}
		run := o.stringRun
		if covered["STRING:woodcut:"+cat.woodcut[string(run.text)].id] {
			continue
		}
		copyCat := *cat
		copyCat.woodcutPlan = func(_, _ string, ink, safe image.Rectangle, _ int) (*image.Alpha, *image.Alpha, *image.Alpha, int) {
			masks := []*image.Alpha{image.NewAlpha(image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)), image.NewAlpha(image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)), image.NewAlpha(image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4))}
			for pos, value := range run.lastVal {
				if indexed[pos] != canvas[pos] {
					continue
				}
				layer := -1
				switch value {
				case 93:
					layer = 0
				case 94:
					layer = 1
				case 92:
					layer = 2
				}
				if layer < 0 {
					continue
				}
				x, y := (pos%320-safe.Min.X)*4, (pos/320-safe.Min.Y)*4
				draw.Draw(masks[layer], image.Rect(x, y, x+4, y+4), image.Opaque, image.Point{}, draw.Src)
			}
			return masks[0], masks[1], masks[2], 0
		}
		item, why := (&stringRuntime{cat: &copyCat}).finishWoodcut(run, o.ink, 7, o.canvas, o.step)
		if why != "" || item == nil || !stringSame(canvas, item, image.Rectangle{}) || !draftSameExceptCursor(indexed, canvas, item.safe, cursor) {
			continue
		}
		draftPaintWoodcutGold(out, item.safe, []*image.Alpha{item.shadow, item.norm, item.accent})
		records = append(records, map[string]any{"kind": "native-event-title", "id": item.id, "source": item.text, "safe": item.safe, "title_style": "gold", "font": "original"})
	}
	return records
}

// 規格060 R120：只接受完整SS來源仍持有的士兵前景，不容許不明後畫。
func (p *hdSceneRuntime) soldierDialogForeground(canvas, indexed, palette []byte, cursor image.Rectangle) []byte {
	if p == nil || p.blocked || len(canvas) != 64000 || len(indexed) != 64000 || len(palette) != 768 {
		return nil
	}
	var frame *hdSceneFrame
	slot := 0
	for i, f := range p.frames {
		if f.id == 1061 {
			frame, slot = f, i+1
			break
		}
	}
	if frame == nil || frame.sprite == nil || frame.decoded == 0 || len(frame.native) != 64000 || frame.sprite.width != 72 || frame.sprite.height != 139 || !frame.paletteSupported(palette) {
		return nil
	}
	mask := make([]byte, 8000)
	count := 0
	for y := 0; y < 139; y++ {
		for x := 0; x < 72; x++ {
			local := y*320 + x
			value := frame.native[local]
			if value == 253 {
				continue
			}
			pos := (y+6)*320 + x + 210
			cell := p.visible[pos]
			if cell.slot == 0 {
				if under, ok := p.spriteCursorCell(pos, draftNativeFrame{canvas: canvas, indexed: indexed, palette: palette, cursor: cursor, mode: 19}); ok {
					cell = under
				}
			}
			if int(cell.slot) != slot || int(cell.local) != local || cell.glyph || cell.value != value || canvas[pos] != value || (!image.Pt(pos%320, pos/320).In(cursor) && indexed[pos] != value) {
				return nil
			}
			mask[pos>>3] |= 1 << uint(pos&7)
			count++
		}
	}
	if count != 4429 {
		return nil
	}
	return mask
}

// 原正文與安全區保持來源驗證；譯文只使用人物左側已量測的欄位。
func draftFitSoldierDialog(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, canvas, indexed, palette []byte, cursor image.Rectangle) (*dialogShown, int) {
	if t == nil || t.dlg == nil || st == nil || st.id != "GAME.TXT:@TUTORIAL14" || o == nil || o.kind != "dialog" || o.dialogRun == nil || o.step != st.complete ||
		o.ink != image.Rect(44, 89, 255, 188) || st.safe != image.Rect(42, 86, 261, 190) ||
		len(st.before) != 64000 || len(st.afterSafe) != st.safe.Dx()*st.safe.Dy() || len(canvas) != 64000 || len(indexed) != 64000 {
		return nil, 0
	}
	mask := t.portraits.soldierDialogForeground(canvas, indexed, palette, cursor)
	if mask == nil || !draftSameExceptCursor(indexed, canvas, st.safe, cursor) {
		return nil, 0
	}
	changed := 0
	for y := st.safe.Min.Y; y < st.safe.Max.Y; y++ {
		for x := st.safe.Min.X; x < st.safe.Max.X; x++ {
			pos := y*320 + x
			k := (y-st.safe.Min.Y)*st.safe.Dx() + x - st.safe.Min.X
			if canvas[pos] != st.afterSafe[k] {
				if mask[pos>>3]&(1<<uint(pos&7)) == 0 {
					return nil, 0
				}
				if _, text := o.after[pos]; text {
					changed++
				}
			}
		}
	}
	capH := 0
	for _, line := range runLines(o.dialogRun.chars) {
		capH = max(capH, line.capH)
	}
	if capH != 9 {
		return nil, 0
	}
	layout := st.safe
	layout.Max.X = 208
	shadow, normal, accent, size := t.dlg.dialogMasks(st.zh, layout.Dx()*4, layout.Dy()*4, capH)
	if shadow == nil || normal == nil || accent == nil || size == 0 {
		return nil, 0
	}
	copy := *st
	copy.before = bytes.Clone(st.before)
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			copy.before[pos] = canvas[pos]
		}
	}
	pad := func(mask *image.Alpha) *image.Alpha {
		full := image.NewAlpha(image.Rect(0, 0, st.safe.Dx()*4, st.safe.Dy()*4))
		draw.Draw(full, mask.Rect, mask, image.Point{}, draw.Src)
		return full
	}
	copy.shadow, copy.normal, copy.accent, copy.dim = pad(shadow), pad(normal), pad(accent), nil
	copy.size, copy.phase, copy.afterSafe = size, "active", rectBytes(canvas, st.safe)
	return &copy, changed
}

func draftPreserveSoldierMenu(t *draftLanguageTarget, c *draftSeaRow, canvas, indexed, palette []byte, cursor image.Rectangle) *draftSeaRow {
	if t == nil || c == nil || c.observation == nil || c.row == nil || c.observation.kind != "sea-bar" || c.row.text != seaMenuText || c.layer != seaBarRect || len(c.observation.canvas) != 64000 || !c.observation.visible(canvas, nil) {
		return c
	}
	mask := t.portraits.soldierDialogForeground(canvas, indexed, palette, cursor)
	if len(mask) != 8000 {
		return c
	}
	changes, points := 0, 0
	for y := c.layer.Min.Y; y < c.layer.Max.Y; y++ {
		for x := c.layer.Min.X; x < c.layer.Max.X; x++ {
			pos := y*320 + x
			protected := mask[pos>>3]&(1<<uint(pos&7)) != 0
			if canvas[pos] != c.observation.canvas[pos] {
				if !protected {
					return c
				}
				changes++
			}
			if protected {
				points++
			}
		}
	}
	if points == 0 {
		return c
	}
	source := *c.observation
	source.canvas = bytes.Clone(source.canvas)
	for y := c.layer.Min.Y; y < c.layer.Max.Y; y++ {
		for x := c.layer.Min.X; x < c.layer.Max.X; x++ {
			pos := y*320 + x
			if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
				source.canvas[pos] = canvas[pos]
			}
		}
	}
	copy := *c
	copy.observation = &source
	copy.foreground = mask
	copy.foregroundChanges = changes
	return &copy
}

// R143候選：已登錄MSS與IND人物共用完整前景證明，來源位置仍逐點核對。
func (p *hdSceneRuntime) seaDialogForeground(canvas, indexed, palette []byte, cursor image.Rectangle) ([]byte, int) {
	if p == nil || p.blocked || len(canvas) != 64000 || len(indexed) != 64000 || len(palette) != 768 {
		return nil, 0
	}
	var selected []byte
	sourceID := 0
	for i, frame := range p.frames {
		if !draftDialogPortraitSource(frame.id) || frame.sprite == nil || frame.decoded == 0 || len(frame.native) != 64000 || !frame.paletteSupported(palette) {
			continue
		}
		slot, sprite := i+1, frame.sprite
		origins := map[image.Point]bool{}
		for pos, cell := range p.visible {
			if int(cell.slot) == slot {
				local := int(cell.local)
				if local >= 64000 || local%320 >= sprite.width || local/320 >= sprite.height {
					return nil, 0
				}
				origins[image.Pt(pos%320-local%320, pos/320-local/320)] = true
			}
		}
		if len(origins) != 1 {
			continue
		}
		var origin image.Point
		for at := range origins {
			origin = at
		}
		if !(image.Rectangle{Min: origin, Max: origin.Add(image.Pt(sprite.width, sprite.height))}).In(image.Rect(0, 0, 320, 200)) {
			continue
		}
		mask := make([]byte, 8000)
		count, valid := 0, true
		for y := 0; y < sprite.height && valid; y++ {
			for x := 0; x < sprite.width; x++ {
				local := y*320 + x
				value := frame.native[local]
				if value == 253 {
					continue
				}
				pos := (origin.Y+y)*320 + origin.X + x
				cell := p.visible[pos]
				if cell.slot == 0 {
					if under, ok := p.spriteCursorCell(pos, draftNativeFrame{canvas: canvas, indexed: indexed, palette: palette, cursor: cursor, mode: 19}); ok {
						cell = under
					}
				}
				if int(cell.slot) != slot || int(cell.local) != local || cell.glyph || cell.value != value || canvas[pos] != value || (!image.Pt(pos%320, pos/320).In(cursor) && indexed[pos] != value) {
					valid = false
					break
				}
				mask[pos>>3] |= 1 << uint(pos&7)
				count++
			}
		}
		if !valid || count != sprite.opaque {
			continue
		}
		if selected != nil {
			return nil, 0
		}
		selected, sourceID = mask, frame.id
	}
	return selected, sourceID
}

func draftPreserveDialogSea(t *draftLanguageTarget, c *draftSeaRow, canvas, indexed, palette []byte, cursor image.Rectangle, protection ...draftInputDialogProtection) *draftSeaRow {
	if t == nil || c == nil || c.observation == nil || c.row == nil || len(c.foreground) != 0 || len(c.observation.canvas) != 64000 || len(c.observation.after) == 0 {
		return c
	}
	o := c.observation
	if (o.kind != "sea-bar" || c.row.text != seaMenuText || c.layer != seaBarRect) &&
		(o.kind != "sea-panel" || len(o.seaRuns) != 1 || c.layer != seaPanelRect) {
		return c
	}
	mask, sourceID := t.portraits.seaDialogForeground(canvas, indexed, palette, cursor)
	if len(mask) != 8000 {
		return c
	}
	inputDialog := ""
	if len(protection) == 1 && protection[0].portrait == sourceID && len(protection[0].mask) == 8000 {
		for i, value := range protection[0].mask {
			mask[i] |= value
		}
		inputDialog = protection[0].id
	}
	for pos, value := range o.after {
		if pos < 0 || pos >= 64000 || !image.Pt(pos%320, pos/320).In(c.layer) || o.canvas[pos] != value ||
			(canvas[pos] != value && mask[pos>>3]&(1<<uint(pos&7)) == 0) {
			return c
		}
	}
	source := *o
	source.canvas = bytes.Clone(o.canvas)
	source.after = make(map[int]byte, len(o.after))
	for pos, value := range o.after {
		source.after[pos] = value
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			source.after[pos] = canvas[pos]
		}
	}
	changes, points := 0, 0
	for y := c.layer.Min.Y; y < c.layer.Max.Y; y++ {
		for x := c.layer.Min.X; x < c.layer.Max.X; x++ {
			pos := y*320 + x
			if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
				if source.canvas[pos] != canvas[pos] {
					changes++
				}
				source.canvas[pos] = canvas[pos]
				points++
			}
		}
	}
	if points == 0 || !source.visible(canvas, nil) {
		return c
	}
	copy := *c
	copy.observation, copy.foreground, copy.foregroundSource, copy.foregroundChanges = &source, mask, sourceID, changes
	copy.inputDialog = inputDialog
	if o.kind == "sea-panel" {
		copy.row, copy.textOffsetY = draftSeaNativeHeight(t.sea, c.row)
		if copy.row == nil {
			return c
		}
	}

	return &copy
}

func draftSeaNativeHeight(st *seaState, row *seaRow) (*seaRow, int) {
	if st == nil || row == nil || len(row.parts) != 1 || row.bbox.Empty() {
		return nil, 0
	}
	part := row.parts[0]
	for size := part.size; size >= 15; size-- {
		mask := image.NewAlpha(image.Rect(0, 0, seaPanelRect.Dx()*4, 256))
		x, y := part.x-seaPanelRect.Min.X*4, 128-st.fonts[size].cjkTop
		if st.seaDraw(mask, part.text, x+2, y+2, size) || st.seaDraw(mask, part.text, x, y, size) {
			continue
		}
		ink := draftAlphaInk(mask)
		if ink.Empty() || ink.Dy() > row.bbox.Dy()*4 {
			continue
		}
		copy := *row
		copy.parts = append([]seaPart(nil), row.parts...)
		copy.parts[0].size = size
		return &copy, 128 - ink.Min.Y
	}
	return nil, 0
}

// 規格060 R150：發現陸地正文的晚到人物只可改寫已核對的前景像素。
func draftFitLandHoDialog(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, canvas, indexed, palette []byte, cursor image.Rectangle) (*dialogShown, map[string]any) {
	if t == nil || t.dlg == nil || st == nil || st.id != "GAME.TXT:@LANDHO:0x00000ECE" ||
		o == nil || o.dialogRun == nil || o.kind != "dialog" || o.step != st.complete ||
		o.ink != image.Rect(64, 117, 253, 136) || st.safe != image.Rect(62, 114, 262, 138) ||
		len(st.before) != 64000 || len(st.afterSafe) != st.safe.Dx()*st.safe.Dy() ||
		len(canvas) != 64000 || len(indexed) != 64000 || !draftSameExceptCursor(indexed, canvas, st.safe, cursor) {
		return nil, nil
	}
	mask, source := t.portraits.seaDialogForeground(canvas, indexed, palette, cursor)
	if len(mask) != 8000 || !draftDialogPortraitSource(source) {
		return nil, nil
	}
	var covered image.Rectangle
	changes := 0
	for y := st.safe.Min.Y; y < st.safe.Max.Y; y++ {
		for x := st.safe.Min.X; x < st.safe.Max.X; x++ {
			pos := y*320 + x
			owned := mask[pos>>3]&(1<<uint(pos&7)) != 0
			if owned {
				covered = covered.Union(image.Rect(x, y, x+1, y+1))
			}
			k := (y-st.safe.Min.Y)*st.safe.Dx() + x - st.safe.Min.X
			if canvas[pos] != st.afterSafe[k] {
				if !owned {
					return nil, nil
				}
				changes++
			}
		}
	}
	capH := 0
	for _, line := range runLines(o.dialogRun.chars) {
		capH = max(capH, line.capH)
	}
	if capH != 8 || covered.Empty() {
		return nil, nil
	}
	candidates := []image.Rectangle{
		image.Rect(st.safe.Min.X, covered.Max.Y, st.safe.Max.X, st.safe.Max.Y),
		image.Rect(covered.Max.X, st.safe.Min.Y, st.safe.Max.X, st.safe.Max.Y),
		image.Rect(st.safe.Min.X, st.safe.Min.Y, covered.Min.X, st.safe.Max.Y),
		image.Rect(st.safe.Min.X, st.safe.Min.Y, st.safe.Max.X, covered.Min.Y),
	}
	var layout image.Rectangle
	var shadow, normal, accent *image.Alpha
	size := 0
	for _, candidate := range candidates {
		if candidate.Empty() || !candidate.In(st.safe) {
			continue
		}
		sh, n, a, px := t.dlg.dialogMasks(st.zh, candidate.Dx()*4, candidate.Dy()*4, capH)
		if sh == nil || n == nil || a == nil || px == 0 {
			continue
		}
		if px > size || px == size && candidate.Dx()*candidate.Dy() > layout.Dx()*layout.Dy() {
			layout, shadow, normal, accent, size = candidate, sh, n, a, px
		}
	}
	if size == 0 {
		return nil, nil
	}
	copy := *st
	copy.before = bytes.Clone(st.before)
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			copy.before[pos] = canvas[pos]
		}
	}
	pad := func(mask *image.Alpha) *image.Alpha {
		full := image.NewAlpha(image.Rect(0, 0, st.safe.Dx()*4, st.safe.Dy()*4))
		offset := layout.Min.Sub(st.safe.Min).Mul(4)
		draw.Draw(full, mask.Rect.Add(offset), mask, image.Point{}, draw.Src)
		return full
	}
	copy.shadow, copy.normal, copy.accent, copy.dim = pad(shadow), pad(normal), pad(accent), nil
	copy.size, copy.phase, copy.afterSafe = size, "active", rectBytes(canvas, st.safe)
	return &copy, map[string]any{"layout_safe": layout, "foreground_source": source, "native_occluded_pixels": changes}
}

// 規格060 R127：限定原生正文與完整選項；譯文不參與來源身份。
func draftLandfallChoice(t *draftLanguageTarget, choice *dialogShown) bool {
	if t == nil || t.dlg == nil || choice == nil || choice.id != "GAME.TXT:@LANDFALL:0x00000FAD#2+list" ||
		choice.safe != image.Rect(70, 145, 145, 168) {
		return false
	}
	group := t.dlg.messageOptions["GAME.TXT:@LANDFALL:0x00000FAD"]
	if len(group) != 2 || len(choice.items) != len(group) {
		return false
	}
	for i, item := range choice.items {
		if _, _, why := t.dlg.matchIn(group[i:i+1], item); why != "" {
			return false
		}
	}
	return true
}

func draftLandfallForeground(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, canvas, indexed, palette []byte, cursor image.Rectangle) ([]byte, int) {
	if t == nil || t.dlg == nil || st == nil || st.id != "GAME.TXT:@LANDFALL:0x00000FAD" ||
		o == nil || o.kind != "dialog" || o.dialogRun == nil || o.step != st.complete ||
		o.ink != image.Rect(67, 122, 250, 141) || st.safe != image.Rect(65, 119, 254, 143) ||
		len(st.before) != 64000 || len(st.afterSafe) != st.safe.Dx()*st.safe.Dy() ||
		len(canvas) != 64000 || len(indexed) != 64000 {
		return nil, 0
	}
	mask, id := t.portraits.seaDialogForeground(canvas, indexed, palette, cursor)
	if id != 1063 || len(mask) != 8000 || !draftSameExceptCursor(indexed, canvas, st.safe, cursor) {
		return nil, 0
	}
	var foreground image.Rectangle
	count := 0
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			foreground = foreground.Union(image.Rect(pos%320, pos/320, pos%320+1, pos/320+1))
			count++
		}
	}
	if count != 5910 || foreground != image.Rect(86, 29, 234, 124) {
		return nil, 0
	}
	changed := 0
	for y := st.safe.Min.Y; y < st.safe.Max.Y; y++ {
		for x := st.safe.Min.X; x < st.safe.Max.X; x++ {
			pos := y*320 + x
			k := (y-st.safe.Min.Y)*st.safe.Dx() + x - st.safe.Min.X
			if canvas[pos] != st.afterSafe[k] {
				if mask[pos>>3]&(1<<uint(pos&7)) == 0 {
					return nil, 0
				}
				if _, text := o.after[pos]; text {
					changed++
				}
			}
		}
	}
	return mask, changed
}

// 只限定這次原生選項事件的查譯來源，不改正式catalog、來源時刻或原生資料。
func draftLandfallDialogContext(t *draftLanguageTarget, d *dialogRuntime, body *dialogShown, source, next *nativeObservation, palette []byte, cursor image.Rectangle, paired bool) *dialogRuntime {
	if t == nil || t.dlg == nil || d == nil || d.cat == nil || body == nil || next == nil || next.dialogRun == nil ||
		next.step < body.complete || (!paired && next.step-body.complete >= 2000000) ||
		(paired && !draftLandfallChoice(t, d.cur)) || next.ink != image.Rect(71, 146, 143, 166) {
		return d
	}
	group := t.dlg.messageOptions["GAME.TXT:@LANDFALL:0x00000FAD"]
	lines := runLines(next.dialogRun.chars)
	if len(group) != 2 || len(lines) != len(group) {
		return d
	}
	for i, line := range lines {
		if _, _, why := t.dlg.matchIn(group[i:i+1], line.text); why != "" {
			return d
		}
	}
	// 這裡只借原生canvas確認身份；最後繪製另核對當下VGA。
	if mask, _ := draftLandfallForeground(t, body, source, next.canvas, next.canvas, palette, cursor); mask == nil {
		return d
	}
	scoped := *d
	catalog := *d.cat
	catalog.lines = group
	scoped.cat = &catalog
	return &scoped
}

func draftFitLandfallDialog(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, choice *dialogShown, canvas, indexed, palette []byte, cursor image.Rectangle) (*dialogShown, int) {
	if !draftLandfallChoice(t, choice) || choice == st || choice.phase != "active" ||
		st == nil || choice.complete < st.complete || len(canvas) != 64000 ||
		!bytes.Equal(choice.afterSafe, rectBytes(canvas, choice.safe)) ||
		!draftSameExceptCursor(indexed, canvas, choice.safe, cursor) {
		return nil, 0
	}
	mask, changed := draftLandfallForeground(t, st, o, canvas, indexed, palette, cursor)
	if mask == nil {
		return nil, 0
	}
	capH := 0
	for _, line := range runLines(o.dialogRun.chars) {
		capH = max(capH, line.capH)
	}
	if capH != 9 {
		return nil, 0
	}
	layout := st.safe
	layout.Min.Y = 124
	shadow, normal, accent, size := t.dlg.dialogMasks(st.zh, layout.Dx()*4, layout.Dy()*4, capH)
	if shadow == nil || normal == nil || accent == nil || size == 0 {
		return nil, 0
	}
	copy := *st
	copy.before = bytes.Clone(st.before)
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			copy.before[pos] = canvas[pos]
		}
	}
	pad := func(mask *image.Alpha) *image.Alpha {
		full := image.NewAlpha(image.Rect(0, 0, st.safe.Dx()*4, st.safe.Dy()*4))
		offset := image.Pt(0, (layout.Min.Y-st.safe.Min.Y)*4)
		draw.Draw(full, mask.Rect.Add(offset), mask, image.Point{}, draw.Src)
		return full
	}
	copy.shadow, copy.normal, copy.accent, copy.dim = pad(shadow), pad(normal), pad(accent), nil
	copy.size, copy.phase, copy.afterSafe = size, "active", rectBytes(canvas, st.safe)
	return &copy, changed
}

// 規格060 R131：限定原生正文與完整選項；譯文不參與來源身份。
func draftAttackChoice(t *draftLanguageTarget, choice *dialogShown) bool {
	if t == nil || t.dlg == nil || choice == nil || choice.id != "GAME.TXT:@WHACKINDIANS:0x000038BD#2+list" ||
		choice.safe != image.Rect(62, 140, 80, 163) {
		return false
	}
	group := t.dlg.messageOptions["GAME.TXT:@WHACKINDIANS:0x000038BD"]
	if len(group) != 2 || len(choice.items) != len(group) {
		return false
	}
	for i, item := range choice.items {
		if _, _, why := t.dlg.matchIn(group[i:i+1], item); why != "" {
			return false
		}
	}
	return true
}

func draftAttackForeground(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, canvas, indexed, palette []byte, cursor image.Rectangle) ([]byte, int) {
	if t == nil || t.dlg == nil || st == nil || st.id != "GAME.TXT:@WHACKINDIANS:0x000038BD" ||
		o == nil || o.kind != "dialog" || o.dialogRun == nil || o.step != st.complete ||
		o.ink != image.Rect(59, 117, 217, 136) || st.safe != image.Rect(57, 114, 246, 138) ||
		len(st.before) != 64000 || len(st.afterSafe) != st.safe.Dx()*st.safe.Dy() ||
		len(canvas) != 64000 || len(indexed) != 64000 {
		return nil, 0
	}
	mask, id := t.portraits.seaDialogForeground(canvas, indexed, palette, cursor)
	if id != 1061 || len(mask) != 8000 || !draftSameExceptCursor(indexed, canvas, st.safe, cursor) {
		return nil, 0
	}
	var foreground image.Rectangle
	count := 0
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			foreground = foreground.Union(image.Rect(pos%320, pos/320, pos%320+1, pos/320+1))
			count++
		}
	}
	if count != 4429 || foreground != image.Rect(195, 34, 266, 173) {
		return nil, 0
	}
	changed := 0
	for y := st.safe.Min.Y; y < st.safe.Max.Y; y++ {
		for x := st.safe.Min.X; x < st.safe.Max.X; x++ {
			pos := y*320 + x
			k := (y-st.safe.Min.Y)*st.safe.Dx() + x - st.safe.Min.X
			if canvas[pos] != st.afterSafe[k] {
				if mask[pos>>3]&(1<<uint(pos&7)) == 0 {
					return nil, 0
				}
				if _, text := o.after[pos]; text {
					changed++
				}
			}
		}
	}
	return mask, changed
}

// 只限定這次原生選項事件的查譯來源，不改正式catalog、來源時刻或原生資料。
func draftAttackDialogContext(t *draftLanguageTarget, d *dialogRuntime, body *dialogShown, source, next *nativeObservation, canvas, indexed, palette []byte, cursor image.Rectangle, paired bool) *dialogRuntime {
	if t == nil || t.dlg == nil || d == nil || d.cat == nil || body == nil || next == nil || next.dialogRun == nil ||
		next.step < body.complete || (!paired && next.step-body.complete >= 2000000) ||
		(paired && !draftAttackChoice(t, d.cur)) || next.ink != image.Rect(63, 141, 78, 161) {
		return d
	}
	group := t.dlg.messageOptions["GAME.TXT:@WHACKINDIANS:0x000038BD"]
	lines := runLines(next.dialogRun.chars)
	if len(group) != 2 || len(lines) != len(group) {
		return d
	}
	for i, line := range lines {
		if _, _, why := t.dlg.matchIn(group[i:i+1], line.text); why != "" {
			return d
		}
	}
	// 這裡只借原生canvas確認身份；最後繪製另核對當下VGA。
	if mask, _ := draftAttackForeground(t, body, source, canvas, indexed, palette, cursor); mask == nil {
		return d
	}
	scoped := *d
	catalog := *d.cat
	catalog.lines = group
	scoped.cat = &catalog
	return &scoped
}

func draftFitAttackDialog(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, choice *dialogShown, canvas, indexed, palette []byte, cursor image.Rectangle) (*dialogShown, int) {
	if !draftAttackChoice(t, choice) || choice == st || choice.phase != "active" ||
		st == nil || choice.complete < st.complete || len(canvas) != 64000 ||
		!bytes.Equal(choice.afterSafe, rectBytes(canvas, choice.safe)) ||
		!draftSameExceptCursor(indexed, canvas, choice.safe, cursor) {
		return nil, 0
	}
	mask, changed := draftAttackForeground(t, st, o, canvas, indexed, palette, cursor)
	if mask == nil {
		return nil, 0
	}
	capH := 0
	for _, line := range runLines(o.dialogRun.chars) {
		capH = max(capH, line.capH)
	}
	if capH != 8 {
		return nil, 0
	}
	layout := st.safe
	layout.Max.X = 193
	layout.Min.Y = 117
	shadow, normal, accent, size := t.dlg.dialogMasks(st.zh, layout.Dx()*4, layout.Dy()*4, capH)
	if shadow == nil || normal == nil || accent == nil || size == 0 {
		return nil, 0
	}
	copy := *st
	copy.before = bytes.Clone(st.before)
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			copy.before[pos] = canvas[pos]
		}
	}
	pad := func(mask *image.Alpha) *image.Alpha {
		full := image.NewAlpha(image.Rect(0, 0, st.safe.Dx()*4, st.safe.Dy()*4))
		offset := image.Pt(0, (layout.Min.Y-st.safe.Min.Y)*4)
		draw.Draw(full, mask.Rect.Add(offset), mask, image.Point{}, draw.Src)
		return full
	}
	copy.shadow, copy.normal, copy.accent, copy.dim = pad(shadow), pad(normal), pad(accent), nil
	copy.size, copy.phase, copy.afterSafe = size, "active", rectBytes(canvas, st.safe)
	return &copy, changed
}

// 規格060 R138候選：只容許已驗MSS0前景改動畫面，不放寬其他後畫。
func draftFitImmigrationTutorial(t *draftLanguageTarget, st *dialogShown, o *nativeObservation, canvas, indexed, palette []byte, cursor image.Rectangle) (*dialogShown, int) {
	if t == nil || t.dlg == nil || st == nil || st.id != "GAME.TXT:@TUTORIAL5" || o == nil || o.kind != "dialog" || o.dialogRun == nil || o.step != st.complete ||
		o.ink != image.Rect(54, 111, 264, 160) || st.safe != image.Rect(52, 108, 271, 162) ||
		len(st.before) != 64000 || len(st.afterSafe) != st.safe.Dx()*st.safe.Dy() || len(canvas) != 64000 || len(indexed) != 64000 {
		return nil, 0
	}
	mask, id := t.portraits.seaDialogForeground(canvas, indexed, palette, cursor)
	if id != 1060 || len(mask) != 8000 || !draftSameExceptCursor(indexed, canvas, st.safe, cursor) {
		return nil, 0
	}
	count := 0
	var foreground image.Rectangle
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			count++
			foreground = foreground.Union(image.Rect(pos%320, pos/320, pos%320+1, pos/320+1))
		}
	}
	if count != 3306 || foreground != image.Rect(45, 34, 120, 125) {
		return nil, 0
	}
	changed := 0
	for y := st.safe.Min.Y; y < st.safe.Max.Y; y++ {
		for x := st.safe.Min.X; x < st.safe.Max.X; x++ {
			pos := y*320 + x
			k := (y-st.safe.Min.Y)*st.safe.Dx() + x - st.safe.Min.X
			if canvas[pos] != st.afterSafe[k] {
				if mask[pos>>3]&(1<<uint(pos&7)) == 0 {
					return nil, 0
				}
				if _, text := o.after[pos]; text {
					changed++
				}
			}
		}
	}
	capH := 0
	for _, line := range runLines(o.dialogRun.chars) {
		capH = max(capH, line.capH)
	}
	if capH != 9 {
		return nil, 0
	}
	layout := st.safe
	layout.Min.Y = 125
	shadow, normal, accent, size := t.dlg.dialogMasks(st.zh, layout.Dx()*4, layout.Dy()*4, capH)
	if shadow == nil || normal == nil || accent == nil || size == 0 {
		return nil, 0
	}
	copy := *st
	copy.before = bytes.Clone(st.before)
	for pos := range canvas {
		if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
			copy.before[pos] = canvas[pos]
		}
	}
	pad := func(mask *image.Alpha) *image.Alpha {
		full := image.NewAlpha(image.Rect(0, 0, st.safe.Dx()*4, st.safe.Dy()*4))
		offset := image.Pt(0, (layout.Min.Y-st.safe.Min.Y)*4)
		draw.Draw(full, mask.Rect.Add(offset), mask, image.Point{}, draw.Src)
		return full
	}
	copy.shadow, copy.normal, copy.accent, copy.dim = pad(shadow), pad(normal), pad(accent), nil
	copy.size, copy.phase, copy.afterSafe = size, "active", rectBytes(canvas, st.safe)
	return &copy, changed
}

// R143候選：兩個守門共用已登錄MSS／IND來源集合。
func draftDialogPortraitSource(id int) bool {
	return (id >= 1060 && id <= 1065) || (id >= 958 && id <= 990)
}
