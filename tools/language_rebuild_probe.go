package main

// 規格060 DRAFT：只連結到隔離觀測器，在停止DOS後重建；不交換正式前端。
import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"os"
	"path/filepath"
	"strconv"
	"strings"
)

var draftNativeBundles = flag.String("draft-native-bundles", "", "規格060隔離原型的完整候選根目錄")

type draftLanguageTarget struct {
	pack *draftPreparedBundle
	dlg  *dialogCatalog
	str  *stringCatalog
	sea  *seaState
}

func draftTargetRequirements(root string) (draftBundleRequirements, error) {
	needs := draftBundleRequirements{
		Font:    "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a",
		License: "6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2",
		Fields:  "2be579643f7655f635a6bec4adcbae9a1fb11a4734d3b8daf80177934e15b61d",
		Masks:   map[string]draftMaskRequirement{},
	}
	// 固定基準來自受版控的清冊，不從候選manifest取得預期值。
	registry, err := os.ReadFile("/repo/tools/language-catalogs.json")
	var index struct {
		Source string `json:"source_binding_sha256"`
		Tables []struct {
			File string `json:"file"`
		} `json:"tables"`
	}
	if err != nil {
		return needs, err
	}
	if err = json.Unmarshal(registry, &index); err != nil {
		return needs, err
	}
	needs.Source = index.Source
	for _, table := range index.Tables {
		needs.Tables = append(needs.Tables, table.File)
	}
	data, err := os.ReadFile(filepath.Join(filepath.Dir(root), "fields.json"))
	if err != nil {
		return needs, err
	}
	if hash(data) != needs.Fields {
		return needs, fmt.Errorf("fixed field evidence mismatch")
	}
	var evidence struct {
		Fields []struct {
			ID     string          `json:"id"`
			File   string          `json:"file"`
			Group  string          `json:"group"`
			Shadow int             `json:"shadow_offset"`
			Safe   image.Rectangle `json:"safe"`
		} `json:"fields"`
	}
	if err = json.Unmarshal(data, &evidence); err != nil {
		return needs, err
	}
	for _, f := range evidence.Fields {
		catalog := "draft.zh-Hant.tsv"
		switch f.Group {
		case "card", "cards-rest":
			catalog = "nation-card-fragments.zh-Hant.tsv"
		case "intro":
			catalog = "nation-introduction.zh-Hant.tsv"
		case "help":
			catalog = "help-bilingual.tsv"
		case "static":
			catalog = "static-overlay.zh-Hant.tsv"
		}
		needs.Masks[f.File] = draftMaskRequirement{ID: f.ID, Shadow: f.Shadow,
			Safe:    [4]int{f.Safe.Min.X * 4, f.Safe.Min.Y * 4, f.Safe.Max.X * 4, f.Safe.Max.Y * 4},
			Layered: f.Group == "intro" || f.Group == "help", Catalog: catalog}
	}
	return needs, nil
}

// 在原版執行前準備五包。之後重建只使用這些記憶體物件。
func draftPrepareTargets(root string, files map[string][]byte, owned, helpOwned map[string]bool) (map[string]*draftLanguageTarget, error) {
	needs, err := draftTargetRequirements(root)
	if err != nil {
		return nil, err
	}
	targets := map[string]*draftLanguageTarget{}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		pack, err := draftPrepareBundle(os.DirFS(root), locale, needs)
		if err != nil {
			return nil, fmt.Errorf("%s: %w", locale, err)
		}
		t := &draftLanguageTarget{pack: pack}
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
		t.dlg, t.str = cat, sc
		targets[locale] = t
	}
	return targets, nil
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
	observation *nativeObservation
	row         *seaRow
	layer       image.Rectangle
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
		return &draftSeaRow{o, row, seaBarRect}, ""
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
	return &draftSeaRow{o, row, layer}, ""
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

func draftPaintSea(out *image.RGBA, st *seaState, candidate *draftSeaRow, canvas, indexed, palette []byte, cursor image.Rectangle) (map[string]any, string) {
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
		x, y := part.x-layer.Min.X*4, row.bbox.Min.Y*4-st.fonts[part.size].cjkTop-layer.Min.Y*4
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
	for i, v := range row.firstOld {
		if after, ok := row.lastVal[i]; ok && canvas[i] == after && v != after {
			draftPaintPixel(out, i, v, palette)
		}
	}
	draftPaintLayers(out, layer, []*image.Alpha{shadow, fg[68], fg[149]}, []byte{0, 68, 149}, palette)
	return map[string]any{"kind": o.kind, "id": "SEA:" + o.kind, "source": row.text, "text": text.String(), "safe": safe, "font_px": sizes[0], "part_font_px": sizes, "native_ink": row.bbox}, ""
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

func draftPaintPixel(out *image.RGBA, i int, v byte, palette []byte) {
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

// 這個切片驗對話、字串及海上；固定欄及完整暫停交易另驗，不能據此升READY。
func draftRebuildTarget(t *draftLanguageTarget, j *nativeJournal, canvas, buffer, indexed, palette []byte, cursor image.Rectangle, step uint64, mode byte) (*image.RGBA, map[string]any, error) {
	if len(canvas) != 64000 || len(buffer) != 64000 || len(indexed) != 64000 || len(palette) != 768 {
		return nil, nil, fmt.Errorf("invalid native frame")
	}
	out := draftRGB(indexed, palette)
	result := map[string]any{"locale": t.pack.manifest.Locale, "original_rendering": t.pack.manifest.Original, "step": step}
	if t.pack.manifest.Original {
		result["items"] = []map[string]any{}
		return out, result, nil
	}
	d := &dialogRuntime{cat: t.dlg, misses: map[string]int{}}
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
			st, shown, why := d.finish(cloneNativeDialog(r), context, o.step)
			if st != nil {
				draftKeepDialog(d, st, context)
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
	var seaClaims []image.Rectangle
	for _, row := range seaRows {
		record, why := draftPaintSea(out, t.sea, row, canvas, indexed, palette, cursor)
		if record != nil {
			records = append(records, record)
			seaClaims = append(seaClaims, row.row.bbox)
		} else {
			seaMisses[why+"\t"+row.row.text]++
		}
	}
	for _, st := range []*dialogShown{d.prev, d.cur} {
		if st == nil || st.phase == "expired" || !bytes.Equal(rectBytes(canvas, st.safe), st.afterSafe) {
			continue
		}
		if !draftSameExceptCursor(indexed, canvas, st.safe, cursor) {
			continue
		}
		for y := st.safe.Min.Y; y < st.safe.Max.Y; y++ {
			for x := st.safe.Min.X; x < st.safe.Max.X; x++ {
				i := y*320 + x
				if !image.Pt(x, y).In(cursor) && st.before[i] != canvas[i] {
					draftPaintPixel(out, i, st.before[i], palette)
				}
			}
		}
		draftPaintLayers(out, st.safe, []*image.Alpha{st.shadow, st.normal, st.accent, st.dim}, []byte{st.shadowC, st.normalC, st.accentC, st.dimC}, palette)
		dialogSafes = append(dialogSafes, st.safe)
		records = append(records, map[string]any{"kind": "dialog", "id": st.id, "text": st.zh, "safe": st.safe, "font_px": st.size})
	}
	for _, it := range s.items {
		// 完整安全區不相同時回原文；本切片尚未處理部分遮擋與畫面世代。
		if !stringSame(canvas, it, image.Rectangle{}) || !draftSameExceptCursor(indexed, canvas, it.safe, cursor) {
			continue
		}
		blocked := false
		for _, safe := range dialogSafes {
			blocked = blocked || safe.Inset(2).Overlaps(it.safe)
		}
		for _, ink := range seaClaims {
			blocked = blocked || ink.Overlaps(it.ink)
		}
		if blocked {
			continue
		}
		if it.id == "STRING:retained-ascii" && !retainedASCIIVisible(it, indexed, cursor) {
			continue
		}
		k := 0
		for y := it.safe.Min.Y; y < it.safe.Max.Y; y++ {
			for x := it.safe.Min.X; x < it.safe.Max.X; x++ {
				if !image.Pt(x, y).In(cursor) && it.before[k] != it.after[k] {
					draftPaintPixel(out, y*320+x, it.before[k], palette)
				}
				k++
			}
		}
		draftPaintLayers(out, it.safe, []*image.Alpha{it.shadow, it.norm, it.accent}, []byte{it.shadowColor, it.color, it.accentColor}, palette)
		records = append(records, map[string]any{"kind": "string", "id": it.id, "source": it.text, "text": it.zh, "safe": it.safe, "font_px": it.size})
	}
	// 只回貼原版游標改動的像素，保留游標框內未被遮擋的文字。
	for y := max(0, cursor.Min.Y); y < min(200, cursor.Max.Y); y++ {
		for x := max(0, cursor.Min.X); x < min(320, cursor.Max.X); x++ {
			i := y*320 + x
			if indexed[i] != canvas[i] {
				draftPaintPixel(out, i, indexed[i], palette)
			}
		}
	}
	result["items"], result["dialog_misses"], result["string_misses"] = records, d.misses, s.misses
	result["sea_misses"] = seaMisses
	result["limitations"] = []string{"只驗對話、字串與海上重建候選，固定欄未接入。", "歷史VGA同步、部分遮擋、畫面世代與正式提交交易仍待驗。"}
	return out, result, nil
}

func draftExportRebuilds(targets map[string]*draftLanguageTarget, j *nativeJournal, canvas, buffer, indexed, palette []byte, cursor image.Rectangle, step uint64, mode byte, out string) error {
	before := hash(bytes.Join([][]byte{canvas, buffer, indexed, palette}, nil))
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		im, record, err := draftRebuildTarget(targets[locale], j, canvas, buffer, indexed, palette, cursor, step, mode)
		if err != nil {
			return err
		}
		record["kind"] = "DRAFT-paused-native-text-rebuild"
		record["rgba_sha256"] = hash(im.Pix)
		savePNG(out+".rebuild-"+locale+".png", im)
		dumpJSON(out+".rebuild-"+locale+".json", record)
	}
	if before != hash(bytes.Join([][]byte{canvas, buffer, indexed, palette}, nil)) {
		return fmt.Errorf("rebuild mutated native frame")
	}
	return nil
}
