package main

// 規格060 R145 READY：只改已觀測原文的顯示字型，不推斷譯文或原版狀態。
import (
	"bytes"
	"golang.org/x/image/font"
	"golang.org/x/image/math/fixed"
	"image"
	"image/color"
	"image/draw"
	"sort"
	"strings"
)

type notoOriginalField struct {
	source *nativeObservation
	text   string
	colors []byte
	ink    image.Rectangle
	shadow byte
}

func notoOriginalColor(colors map[byte]int, shadow byte) (byte, bool) {
	best, count := byte(0), 0
	for c, n := range colors {
		if shadow != 0 && (c == shadow || c == 128) {
			continue
		}
		if n > count || n == count && c < best {
			best, count = c, n
		}
	}
	return best, count > 0
}

func notoOriginalFields(o *nativeObservation) []notoOriginalField {
	var fields []notoOriginalField
	field := notoOriginalField{source: o}
	var lastBox image.Rectangle
	flush := func() {
		if !field.ink.Empty() && strings.TrimSpace(field.text) != "" {
			fields = append(fields, field)
		}
		field = notoOriginalField{source: o, shadow: field.shadow}
		lastBox = image.Rectangle{}
	}
	appendChar := func(c byte, box image.Rectangle, color byte) {
		if c < 32 || c > 126 {
			flush()
			return
		}
		if box.Empty() && c != ' ' {
			flush() // 無墨跡的對齊／控制標記不能變成新文字。
			return
		}
		if !box.Empty() && !field.ink.Empty() && (box.Min.Y >= field.ink.Max.Y || box.Max.Y <= field.ink.Min.Y ||
			(!lastBox.Empty() && box.Min.X < lastBox.Min.X) || box.Min.X-field.ink.Max.X >= lineGapPx) {
			flush()
		}
		field.text += string(c)
		field.colors = append(field.colors, color)
		field.ink = field.ink.Union(box)
		if !box.Empty() {
			lastBox = box
		}
	}
	if r := o.stringRun; r != nil {
		if r.mixed || len(r.text) != len(r.boxes) || r.others.Overlaps(o.ink) {
			return nil
		}
		if r.outline {
			return nil // 描邊仍由既有字串排版處理，不能猜原字面與描邊的邊界。
		}
		color, uniform := notoOriginalColor(r.colors, 0)
		if !uniform {
			return nil
		}
		for i, c := range r.text {
			ink := color
			if len(r.colors) > 1 {
				if i >= len(r.charColor) {
					return nil
				}
				var ok bool
				counts := map[byte]int{}
				for shade, rect := range r.charColor[i] {
					rect = rect.Intersect(image.Rect(0, 0, 320, 200))
					for y := rect.Min.Y; y < rect.Max.Y; y++ {
						for x := rect.Min.X; x < rect.Max.X; x++ {
							if value, written := o.after[y*320+x]; written && value == shade {
								counts[shade]++
							}
						}
					}
				}
				ink, ok = notoOriginalColor(counts, 0)
				if !ok && c != ' ' {
					return nil
				}
			}
			appendChar(c, r.boxes[i], ink)
		}
	} else if r := o.dialogRun; r != nil {
		if r.readPos%2 != 0 || r.others.Overlaps(o.ink) {
			return nil
		}
		if r.shadowWritten {
			field.shadow = 47
		}
		for _, ch := range r.chars {
			if ch.c == 0 || dialogHotkeyMark(ch) || dialogNonprintingBullet(ch) {
				continue
			}
			ink, ok := notoOriginalColor(ch.colors, field.shadow)
			if !ok && !ch.box.Empty() {
				return nil
			}
			appendChar(ch.c, ch.box, ink)
		}
	} else if len(o.seaRuns) == 1 {
		r := o.seaRuns[0]
		if len(r.colors) != 1 {
			return nil
		}
		ink, ok := notoOriginalColor(r.colors, 0)
		if !ok {
			return nil
		}
		text := strings.TrimRight(string(r.raw), "\x00")
		for _, c := range []byte(text) {
			if c < 32 || c > 126 {
				return nil
			}
			field.colors = append(field.colors, ink)
		}
		field.text, field.ink = text, r.bbox
	}
	flush()
	return fields
}

func notoOriginalBefore(o *nativeObservation) map[int]byte {
	if o.stringRun != nil {
		return o.stringRun.firstOld
	}
	if o.dialogRun != nil {
		return o.dialogRun.firstOld
	}
	if len(o.seaRuns) == 1 {
		return o.seaRuns[0].firstOld
	}
	return nil
}

func notoOriginalProtected(mask []byte, pos int) bool {
	return len(mask) == 8000 && pos >= 0 && pos < 64000 && mask[pos>>3]&(1<<uint(pos&7)) != 0
}

func notoOriginalSource(field notoOriginalField, canvas, indexed, mask []byte, cursor image.Rectangle, diagnostic ...*string) bool {
	fail := func(reason string) bool {
		for _, target := range diagnostic {
			if target != nil {
				*target = reason
			}
		}
		return false
	}
	o, safe := field.source, field.ink
	source := o.canvas
	if o.kind == "string-map" {
		source = o.buffer
	}
	if safe.Empty() || !safe.In(image.Rect(0, 0, 320, 200)) || len(source) != 64000 || len(o.after) == 0 {
		return fail("layout")
	}
	before, own := notoOriginalBefore(o), 0
	inkColors := map[byte]bool{}
	for i, color := range field.colors {
		if field.text[i] != ' ' {
			inkColors[color] = true
		}
	}
	for pos, value := range o.after {
		if pos < 0 || pos >= 64000 || source[pos] != value {
			return fail("source-snapshot")
		}
		if _, ok := before[pos]; !ok {
			return fail("before-missing")
		}
		if canvas[pos] != value && !notoOriginalProtected(mask, pos) {
			if !image.Pt(pos%320, pos/320).In(safe) {
				return fail("canvas-outside-field")
			}
			return fail("canvas-inside-field")
		}
		if image.Pt(pos%320, pos/320).In(safe) {
			if inkColors[before[pos]] {
				return fail("before-has-ink") // 原字色底圖可能含舊字；不猜背景。
			}
			own++
		}
	}
	if own == 0 {
		return fail("no-owned-pixels")
	}
	var backgroundChanges, indexedChanges image.Rectangle
	for y := safe.Min.Y; y < safe.Max.Y; y++ {
		for x := safe.Min.X; x < safe.Max.X; x++ {
			pos := y*320 + x
			if canvas[pos] != source[pos] && !notoOriginalProtected(mask, pos) {
				backgroundChanges = backgroundChanges.Union(image.Rect(x, y, x+1, y+1))
			}
			if indexed[pos] != canvas[pos] && !image.Pt(x, y).In(cursor) {
				indexedChanges = indexedChanges.Union(image.Rect(x, y, x+1, y+1))
			}
		}
	}
	if !backgroundChanges.Empty() {
		return fail("background:" + backgroundChanges.String())
	}
	if !indexedChanges.Empty() {
		return fail("indexed-canvas:" + indexedChanges.String())
	}
	return true
}

func draftPaintOriginalNoto(out *image.RGBA, t *draftLanguageTarget, j *nativeJournal, canvas, indexed, palette []byte, cursor image.Rectangle, claimed []map[string]any, hdBackgroundOverride ...draftHDBackground) ([]map[string]any, map[string]int) {
	var records []map[string]any
	misses := map[string]int{}
	var safes []image.Rectangle
	for _, record := range claimed {
		if safe, ok := record["safe"].(image.Rectangle); ok {
			safes = append(safes, safe)
		}
	}
	var candidates []notoOriginalField
	for _, o := range j.items {
		fields := notoOriginalFields(o)
		candidates = append(candidates, fields...)
		if len(fields) == 0 && o.fixed == nil {
			misses["unsupported-source-layout\t"+o.kind]++
		}
	}
	// 完整文字先占用欄位，不能由相同來源的單字元殘片擋住整行。
	sort.SliceStable(candidates, func(a, b int) bool {
		x, y := candidates[a].ink, candidates[b].ink
		return x.Dx()*x.Dy() > y.Dx()*y.Dy()
	})
	portrait, portraitID := t.portraits.seaDialogForeground(canvas, indexed, palette, cursor)
	input := draftVerifiedInputDialog(t, j, canvas, indexed, palette, cursor)
	for _, field := range candidates {
		blocked := false
		for _, safe := range safes {
			blocked = blocked || safe.Overlaps(field.ink)
		}
		if blocked {
			continue
		}
		fieldMask := portrait
		if input.id != "" && field.ink.In(seaPanelRect) {
			fieldMask = make([]byte, 8000)
			for i := range fieldMask {
				fieldMask[i] = portrait[i] | input.mask[i]
			}
		}
		var sourceReason string
		if !notoOriginalSource(field, canvas, indexed, fieldMask, cursor, &sourceReason) {
			misses["source-changed\t"+field.text]++
			if *draftNativeCapture && field.ink.In(seaPanelRect) {
				misses["source-detail|"+field.source.kind+"|"+sourceReason+"|"+input.id+"\t"+field.text]++
			}
			continue
		}
		if record := draftPaintTranslatedNativeField(out, t, field, canvas, palette, fieldMask, portraitID, hdBackgroundOverride...); record != nil {
			if input.id != "" && field.ink.In(seaPanelRect) {
				record["dialog_occlusion_id"] = input.id
			}
			records = append(records, record)
			safes = append(safes, field.ink)
			continue
		}
		fit := field.ink
		if field.shadow != 0 {
			fit.Max = fit.Max.Sub(image.Pt(1, 1))
		}
		plan := planRetainedASCII(t.str.fonts, field.text, fit)
		if plan == nil {
			misses["font-does-not-fit\t"+field.text]++
			continue
		}
		before := notoOriginalBefore(field.source)
		safe := field.ink
		original := image.NewRGBA(image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4))
		draw.Draw(original, original.Bounds(), out, safe.Min.Mul(4), draw.Src)
		for pos, value := range field.source.after {
			if image.Pt(pos%320, pos/320).In(safe) && !notoOriginalProtected(fieldMask, pos) && before[pos] != value {
				draftPaintPixel(out, pos, before[pos], palette, hdBackgroundOverride...)
			}
		}
		layers := map[byte]*image.Alpha{}
		x, y := -plan.bounds.Min.X, -plan.bounds.Min.Y
		var shadow *image.Alpha
		if field.shadow != 0 {
			shadow = image.NewAlpha(original.Bounds())
		}
		for i, c := range field.text {
			color := field.colors[i]
			if layers[color] == nil {
				layers[color] = image.NewAlpha(original.Bounds())
			}
			dialogBlit(layers[color], plan.font.glyphs[c], x, y)
			if shadow != nil {
				dialogBlit(shadow, plan.font.glyphs[c], x+4, y+4)
			}
			x += plan.font.widths[c]
		}
		if shadow != nil {
			draftPaintLayers(out, safe, []*image.Alpha{shadow}, []byte{field.shadow}, palette)
		}
		var order []int
		for color := range layers {
			order = append(order, int(color))
		}
		sort.Ints(order)
		for _, value := range order {
			color := byte(value)
			draftPaintLayers(out, safe, []*image.Alpha{layers[color]}, []byte{color}, palette)
		}
		for yy := safe.Min.Y; yy < safe.Max.Y; yy++ {
			for xx := safe.Min.X; xx < safe.Max.X; xx++ {
				if notoOriginalProtected(fieldMask, yy*320+xx) {
					draw.Draw(out, image.Rect(xx*4, yy*4, xx*4+4, yy*4+4), original, image.Pt((xx-safe.Min.X)*4, (yy-safe.Min.Y)*4), draw.Src)
				}
			}
		}
		record := map[string]any{"kind": "original-noto", "id": "FONT:original", "source": field.text, "text": field.text,
			"safe": safe, "native_ink": safe, "font_px": plan.size, "font_only": true, "translated": false,
			"source_kind": field.source.kind, "cap_height_native": notoNativeCapHeight(field), "baseline_shift_px": -plan.bounds.Min.Y}
		if len(portrait) != 0 {
			record["foreground_source"] = portraitID
		}
		records = append(records, record)
		safes = append(safes, safe)
	}
	return records, misses
}

// DEC-LOW/UPP 的來源檔名已明示英文字母；不把 SQIG 裝飾筆畫猜成文字。
func notoDeclarationRune(name string) rune {
	if len(name) != len("DEC-LOWA.SS") || !strings.HasSuffix(name, ".SS") || name[7] < 'A' || name[7] > 'Z' {
		return 0
	}
	if strings.HasPrefix(name, "DEC-LOW") {
		return rune(name[7] + 'a' - 'A')
	}
	if strings.HasPrefix(name, "DEC-UPP") {
		return rune(name[7])
	}
	return 0
}

type notoDeclarationGlyph struct {
	writeVersion  uint64
	slot          int
	safe          image.Rectangle
	before, after []byte
	backing       []hdSceneCell
	step          uint64
}

type notoDeclarationPlan struct {
	mask *image.Alpha
	ink  image.Rectangle
	size int
}

type notoDeclarationJournal struct {
	glyphs  map[int]*notoDeclarationGlyph
	writes  []uint64
	version uint64
}

func bindNotoDeclaration(p *hdSceneRuntime) {
	if p != nil && p.spriteFontSource == nil {
		journal := &notoDeclarationJournal{glyphs: map[int]*notoDeclarationGlyph{}, writes: make([]uint64, 64000)}
		p.spriteFontState = journal
		p.spriteFontSource = func(name string) bool { return notoDeclarationRune(name) != 0 }
		p.spriteFontObserver = p.captureNotoDeclaration
		p.spriteFontWriteObserver = func(a uint32) {
			if a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
				journal.version++
				journal.writes[int(a-hdBuildingCanvas)] = journal.version
			}
		}
		p.spriteFontRectStamp = func(safe image.Rectangle) uint64 {
			var last uint64
			for y := safe.Min.Y; y < safe.Max.Y; y++ {
				for x := safe.Min.X; x < safe.Max.X; x++ {
					last = max(last, journal.writes[y*320+x])
				}
			}
			return last
		}
	}
}
func notoDeclarationState(p *hdSceneRuntime, create bool) map[int]*notoDeclarationGlyph {
	journal, _ := p.spriteFontState.(*notoDeclarationJournal)
	if journal == nil && create {
		bindNotoDeclaration(p)
		journal, _ = p.spriteFontState.(*notoDeclarationJournal)
	}
	if journal == nil {
		return nil
	}
	return journal.glyphs
}

func (p *hdSceneRuntime) captureNotoDeclaration(call *hdSceneSpriteCall, frame *hdSceneFrame, after []byte) {
	if call.canvas != hdBuildingCanvas || notoDeclarationRune(frame.file) == 0 || len(call.notoBeforeCells) == 0 || len(frame.indices) != 1 {
		return
	}
	safe := image.Rect(call.x, call.y, call.x+frame.sprite.width, call.y+frame.sprite.height)
	before := rectBytes(call.before, safe)
	backing := call.notoBeforeCells
	key := call.y*320 + call.x
	glyphs := notoDeclarationState(p, true)
	if old := glyphs[key]; old != nil && old.safe == safe && p.frames[old.slot].file == frame.file && bytes.Equal(old.after, before) {
		if call.fontPriorWriteMax > old.writeVersion {
			return
		}
		before, backing = old.before, old.backing
	}
	if len(glyphs) >= 512 && glyphs[key] == nil {
		oldest, step := 0, ^uint64(0)
		for at, old := range glyphs {
			if old.step < step {
				oldest, step = at, old.step
			}
		}
		delete(glyphs, oldest)
	}
	glyphs[key] = &notoDeclarationGlyph{writeVersion: p.spriteFontState.(*notoDeclarationJournal).version, slot: call.slot, safe: safe, before: before, after: rectBytes(after, safe), backing: backing, step: p.h.m.Steps}
}

func (t *draftLanguageTarget) declarationPlan(frame, complete *hdSceneFrame) *notoDeclarationPlan {
	if t.originalFonts == nil {
		return nil
	}
	if t.declarationPlans == nil {
		t.declarationPlans = map[string]*notoDeclarationPlan{}
	}
	if plan, found := t.declarationPlans[frame.file]; found {
		return plan
	}
	text := string(notoDeclarationRune(frame.file))
	ink := notoDeclarationInk[complete.file]
	if ink.Empty() {
		return nil
	}
	var plan *notoDeclarationPlan
	// 上限來自此字形自己的原版墨跡高度，字級不是全域常數。
	for size := min(192, ink.Dy()*8); size >= 12; size-- {
		face := t.originalFonts.face(t.pack.manifest.Locale, size)
		bounds, _ := font.BoundString(face, text)
		b := image.Rect(bounds.Min.X.Floor(), bounds.Min.Y.Floor(), bounds.Max.X.Ceil(), bounds.Max.Y.Ceil())
		if b.Empty() || b.Dx() > ink.Dx()*4 || b.Dy() > ink.Dy()*4 {
			continue
		}
		mask := image.NewAlpha(image.Rect(0, 0, complete.sprite.width*4, complete.sprite.height*4))
		d := font.Drawer{Dst: mask, Src: image.NewUniform(color.Alpha{255}), Face: face, Dot: fixed.P(ink.Min.X*4-b.Min.X, ink.Min.Y*4-b.Min.Y)}
		d.DrawString(text)
		plan = &notoDeclarationPlan{mask: mask, ink: ink, size: size}
		break
	}
	t.declarationPlans[frame.file] = plan
	return plan
}

func draftPaintDeclarationNoto(out *image.RGBA, t *draftLanguageTarget, canvas, indexed, palette []byte, cursor image.Rectangle, claimed []map[string]any) []map[string]any {
	p := t.portraits
	if p == nil || p.blocked || t.originalFonts == nil {
		return nil
	}
	var records []map[string]any
	var keys []int
	glyphs := notoDeclarationState(p, false)
	for key := range glyphs {
		keys = append(keys, key)
	}
	sort.Ints(keys)
	for _, key := range keys {
		glyph := glyphs[key]
		frame := p.frames[glyph.slot]
		if p.spriteFontRectStamp == nil || p.spriteFontRectStamp(glyph.safe) > glyph.writeVersion {
			continue
		}
		if !frame.paletteSupported(palette) || !bytes.Equal(rectBytes(canvas, glyph.safe), glyph.after) || !draftSameExceptCursor(indexed, canvas, glyph.safe, cursor) {
			continue
		}
		blocked := false
		for _, record := range claimed {
			if safe, ok := record["safe"].(image.Rectangle); ok && safe.Overlaps(glyph.safe) {
				blocked = true
			}
		}
		if blocked {
			continue
		}
		valid := true
		for y := 0; y < frame.sprite.height; y++ {
			for x := 0; x < frame.sprite.width; x++ {
				local := y*320 + x
				if frame.native[local] == 253 {
					continue
				}
				pos := (glyph.safe.Min.Y+y)*320 + glyph.safe.Min.X + x
				cell := p.visible[pos]
				if cell.slot != uint16(glyph.slot+1) || int(cell.local) != local || cell.glyph || cell.value != frame.native[local] {
					valid = false
				}
			}
		}
		if !valid {
			continue
		}
		complete := frame
		for _, candidate := range p.frames {
			if candidate.file == frame.file && candidate.sprite != nil && candidate.sprite.ordinal > complete.sprite.ordinal {
				complete = candidate
			}
		}
		if complete.sprite.width != glyph.safe.Dx() || complete.sprite.height != glyph.safe.Dy() {
			continue
		}
		plan := t.declarationPlan(frame, complete)
		if plan == nil || complete.sprite.opaque == 0 {
			continue
		}
		for i, value := range glyph.before {
			x, y := glyph.safe.Min.X+i%glyph.safe.Dx(), glyph.safe.Min.Y+i/glyph.safe.Dx()
			cell := glyph.backing[i]
			if bg, ok := p.frame(cell); ok && !cell.glyph && cell.value == value && bg.paletteSupported(palette) && bg.native[int(cell.local)] == value {
				bg.drawCell(out, x*4, y*4, int(cell.local)%320*4, int(cell.local)/320*4, palette)
			} else {
				draftPaintPixel(out, y*320+x, value, palette)
			}
		}
		mask := image.NewAlpha(plan.mask.Rect)
		progress := min(complete.sprite.opaque, frame.sprite.opaque)
		for i, alpha := range plan.mask.Pix {
			mask.Pix[i] = byte(int(alpha) * progress / complete.sprite.opaque)
		}
		draftPaintLayers(out, glyph.safe, []*image.Alpha{mask}, []byte{frame.indices[0]}, palette)
		records = append(records, map[string]any{"kind": "declaration-noto", "id": "FONT:" + frame.file, "source": string(notoDeclarationRune(frame.file)), "safe": glyph.safe, "native_ink": plan.ink.Add(glyph.safe.Min), "font_px": plan.size, "font_only": true, "translated": false, "source_frame": frame.id, "source_ordinal": frame.sprite.ordinal, "native_progress_pixels": progress, "native_complete_pixels": complete.sprite.opaque})
	}
	return records
}

// 原版完整字形墨跡；來源指紋見規格060 R145及r145-declaration-measurements-r1.json。
var notoDeclarationInk = map[string]image.Rectangle{
	"DEC-LOWA.SS": image.Rect(0, 7, 8, 13),
	"DEC-LOWB.SS": image.Rect(0, 5, 6, 14),
	"DEC-LOWC.SS": image.Rect(0, 8, 6, 13),
	"DEC-LOWD.SS": image.Rect(0, 6, 9, 13),
	"DEC-LOWE.SS": image.Rect(0, 8, 6, 13),
	"DEC-LOWF.SS": image.Rect(0, 4, 5, 19),
	"DEC-LOWG.SS": image.Rect(0, 8, 7, 20),
	"DEC-LOWH.SS": image.Rect(0, 4, 7, 16),
	"DEC-LOWI.SS": image.Rect(0, 5, 6, 13),
	"DEC-LOWJ.SS": image.Rect(0, 6, 6, 20),
	"DEC-LOWK.SS": image.Rect(0, 2, 8, 17),
	"DEC-LOWL.SS": image.Rect(0, 3, 8, 13),
	"DEC-LOWM.SS": image.Rect(0, 8, 11, 13),
	"DEC-LOWN.SS": image.Rect(0, 8, 9, 13),
	"DEC-LOWO.SS": image.Rect(0, 8, 6, 13),
	"DEC-LOWP.SS": image.Rect(0, 8, 8, 17),
	"DEC-LOWQ.SS": image.Rect(0, 8, 8, 18),
	"DEC-LOWR.SS": image.Rect(0, 8, 7, 13),
	"DEC-LOWS.SS": image.Rect(0, 6, 8, 13),
	"DEC-LOWT.SS": image.Rect(0, 5, 7, 12),
	"DEC-LOWU.SS": image.Rect(0, 8, 9, 13),
	"DEC-LOWV.SS": image.Rect(0, 9, 7, 13),
	"DEC-LOWW.SS": image.Rect(0, 9, 8, 13),
	"DEC-LOWX.SS": image.Rect(0, 8, 8, 15),
	"DEC-LOWY.SS": image.Rect(0, 8, 9, 20),
	"DEC-LOWZ.SS": image.Rect(0, 9, 8, 21),
	"DEC-UPPA.SS": image.Rect(0, 4, 13, 14),
	"DEC-UPPB.SS": image.Rect(0, 3, 11, 14),
	"DEC-UPPC.SS": image.Rect(0, 3, 19, 14),
	"DEC-UPPD.SS": image.Rect(0, 4, 15, 16),
	"DEC-UPPE.SS": image.Rect(0, 3, 12, 14),
	"DEC-UPPF.SS": image.Rect(0, 2, 14, 15),
	"DEC-UPPG.SS": image.Rect(0, 2, 18, 20),
	"DEC-UPPH.SS": image.Rect(0, 2, 13, 14),
	"DEC-UPPI.SS": image.Rect(0, 2, 11, 13),
	"DEC-UPPJ.SS": image.Rect(0, 3, 8, 22),
	"DEC-UPPK.SS": image.Rect(0, 2, 15, 16),
	"DEC-UPPL.SS": image.Rect(0, 3, 13, 17),
	"DEC-UPPM.SS": image.Rect(0, 4, 16, 16),
	"DEC-UPPN.SS": image.Rect(0, 4, 18, 17),
	"DEC-UPPO.SS": image.Rect(0, 4, 11, 16),
	"DEC-UPPP.SS": image.Rect(0, 3, 14, 17),
	"DEC-UPPQ.SS": image.Rect(0, 4, 13, 15),
	"DEC-UPPR.SS": image.Rect(0, 4, 13, 16),
	"DEC-UPPS.SS": image.Rect(0, 3, 9, 16),
	"DEC-UPPT.SS": image.Rect(0, 3, 16, 13),
	"DEC-UPPU.SS": image.Rect(0, 4, 19, 14),
	"DEC-UPPV.SS": image.Rect(0, 5, 13, 15),
	"DEC-UPPW.SS": image.Rect(0, 1, 14, 17),
	"DEC-UPPX.SS": image.Rect(0, 3, 14, 18),
	"DEC-UPPY.SS": image.Rect(0, 3, 14, 19),
	"DEC-UPPZ.SS": image.Rect(0, 4, 13, 19),
}

// 規格060 R150：來源仍由已驗原版片段綁定，顯示文字只取現用語言字典。
func draftBindNativeLabels(t *draftLanguageTarget, files map[string][]byte) {
	t.nativeLabels = map[string][2]string{}
	for _, def := range []struct {
		id, file       string
		offset, length int
		sha            string
	}{
		{"LABELS.TXT:@MISC:0x00000159", "LABELS.TXT", 0x159, 16, "9257b2c3a4655ae2c496325d84d4e67b7b7071d461658e118ffdbcf2a301c947"},
		{"NAMES.TXT:0x00002855", "NAMES.TXT", 0x2855, 9, "e30049639cf74d69c8ed68679305053b30a83ac02f5860a226f5259b1f1066b1"},
		{"LABELS.TXT:0x00000411", "LABELS.TXT", 0x411, 7, "abcf0f136c1ed0ddcaf5ef1a97717e36b81f63b7f639d50c2c154f087060e191"},
		{"LABELS.TXT:0x000008A9", "LABELS.TXT", 0x8a9, 7, "040ff883e530a54bbfae42af1c34fb5bbf66d3d38c781d1e1adf1779ab3a0dbe"},
		{"LABELS.TXT:0x0000086E", "LABELS.TXT", 0x86e, 24, "b8aebf24f5bcc5139bea5a79fac8687020c10b10fc805f29916748e008cfd35e"},
		{"GAME.TXT:0x00015522", "GAME.TXT", 0x15522, 27, "c46adc07e89dc853f75888b5799426773196b67a07978b4b256ea97ebdbac65b"},
		{"NAMES.TXT:0x0000286A", "NAMES.TXT", 0x286a, 6, "5ece526b2e72c2e5004c95dcada14bb8fc8ecbc099e22d17c5afcdb853be46a2"},
	} {
		raw := files[def.file]
		if def.offset < 0 || def.offset+def.length > len(raw) {
			continue
		}
		raw = raw[def.offset : def.offset+def.length]
		if hash(raw) != def.sha {
			continue
		}
		source := string(raw)
		text := t.str.lookup(source)
		if def.id == "GAME.TXT:0x00015522" {
			for _, row := range splitTSV(t.pack.files["text/draft.zh-Hant.tsv"]) {
				if row["candidate_id"] == def.id {
					source = strings.TrimPrefix(source, "^^")
					text = strings.TrimPrefix(row["zh_hant"], "^^")
					break
				}
			}
		}
		if text != "" && text != source {
			t.nativeLabels[def.id] = [2]string{source, text}
		}
	}
}

func notoNativeCapHeight(field notoOriginalField) int {
	if field.source == nil {
		return 0
	}
	capH := 0
	if r := field.source.dialogRun; r != nil {
		for _, ch := range r.chars {
			if (ch.c >= 'A' && ch.c <= 'Z' || ch.c >= '0' && ch.c <= '9') && ch.box.In(field.ink) {
				capH = max(capH, ch.box.Dy())
			}
		}
	} else if r := field.source.stringRun; r != nil {
		for i, c := range r.text {
			if (c >= 'A' && c <= 'Z' || c >= '0' && c <= '9') && i < len(r.boxes) && r.boxes[i].In(field.ink) {
				capH = max(capH, r.boxes[i].Dy())
			}
		}
	} else if len(field.source.seaRuns) == 1 {
		capH = field.ink.Dy()
	}
	return capH
}

// 基線對齊原墨跡底緣；候選字級由此欄的大寫高度、寬度及陰影共同限制。
func notoTranslatedMasks(fonts map[int]*dialogFont, text string, safe, ink image.Rectangle, capH int, shadow bool, extraFonts ...map[int]*dialogFont) (*image.Alpha, *image.Alpha, int) {
	if text == "" || safe.Empty() || !ink.In(safe) || capH <= 0 || capH > 13 {
		return nil, nil, 0
	}
	rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
	for size := capH * 4; size >= (capH*8+2)/3; size-- {
		faces := []*dialogFont{fonts[size]}
		for _, extra := range extraFonts {
			faces = append(faces, extra[size])
		}
		for _, face := range faces {
			if face == nil {
				continue
			}
			bounds, ok := retainedTextBounds(face, text)
			if !ok {
				continue
			}
			bottom := (ink.Max.Y - safe.Min.Y) * 4
			if shadow {
				bottom -= 4
			}
			origin := image.Pt((ink.Min.X-safe.Min.X)*4-bounds.Min.X, bottom-bounds.Max.Y)
			placed := bounds.Add(origin)
			if !placed.In(rect) || shadow && !placed.Add(image.Pt(4, 4)).In(rect) {
				continue
			}
			normal := image.NewAlpha(rect)
			x := origin.X
			for _, c := range text {
				dialogBlit(normal, face.glyphs[c], x, origin.Y)
				x += face.widths[c]
			}
			shade := image.NewAlpha(rect)
			if shadow {
				dialogBlit(shade, normal, 4, 4)
			}
			return normal, shade, size
		}
	}
	return nil, nil, 0
}

// 圖集沒有這一行的字時，仍用已驗同地區Noto字型與此欄原字高量測。
func (t *draftLanguageTarget) notoTranslatedFontMasks(text string, ink image.Rectangle, capH int, shadow bool) (*image.Alpha, *image.Alpha, int) {
	if t.originalFonts == nil || text == "" || ink.Empty() || capH <= 0 || capH > 13 {
		return nil, nil, 0
	}
	rect := image.Rect(0, 0, ink.Dx()*4, ink.Dy()*4)
	for size := capH*4; size >= (capH*8+2)/3; size-- {
		face := t.originalFonts.face(t.pack.manifest.Locale, size)
		bounds, _ := font.BoundString(face, text)
		b := image.Rect(bounds.Min.X.Floor(), bounds.Min.Y.Floor(), bounds.Max.X.Ceil(), bounds.Max.Y.Ceil())
		if b.Empty() {
			continue
		}
		bottom := rect.Max.Y
		if shadow {
			bottom -= 4
		}
		origin := image.Pt(-b.Min.X, bottom-b.Max.Y)
		placed := b.Add(origin)
		if !placed.In(rect) || shadow && !placed.Add(image.Pt(4, 4)).In(rect) {
			continue
		}
		normal, shade := image.NewAlpha(rect), image.NewAlpha(rect)
		drawer := font.Drawer{Dst: normal, Src: image.NewUniform(color.Alpha{255}), Face: face, Dot: fixed.P(origin.X, origin.Y)}
		drawer.DrawString(text)
		if shadow {
			dialogBlit(shade, normal, 4, 4)
		}
		return normal, shade, size
	}
	return nil, nil, 0
}

// 僅補接已量測且綁定原始片段的具名欄位。
func draftPaintTranslatedNativeField(out *image.RGBA, t *draftLanguageTarget, field notoOriginalField, canvas, palette, portrait []byte, portraitID int, hdBackgroundOverride ...draftHDBackground) map[string]any {
	if t == nil || t.str == nil || field.source == nil {
		return nil
	}
	capH := notoNativeCapHeight(field)
	text, id := "", ""
	if field.ink.In(seaBarRect) && field.ink.Min.Y == 1 {
		if value, key, why := t.str.translate(field.text); why == "" && key == "template:colony-title" {
			text, id = value, "STRING:colony-title"
		}
	} else if field.ink == image.Rect(62, 118, 207, 127) {
		if value, key, why := t.str.translate(field.text); why == "" && key == "GAME.TXT:0x00000F21" {
			text, id = value, key
		}
	} else if field.ink.In(seaPanelRect) {
		for _, key := range []string{"NAMES.TXT:0x00002855", "LABELS.TXT:0x00000411", "NAMES.TXT:0x0000286A"} {
			value := t.nativeLabels[key]
			if value[0] != "" && strings.TrimSpace(field.text) == value[0] {
				text, id = value[1], key
				break
			}
		}
	}
	if text == "" {
		for _, def := range []struct {
			key string
			ink image.Rectangle
			wrapped bool
		}{
			{"LABELS.TXT:0x000008A9", image.Rect(150, 53, 174, 59), false},
			{"LABELS.TXT:0x0000086E", image.Rect(12, 182, 101, 187), true},
			{"GAME.TXT:0x00015522", image.Rect(101, 30, 219, 39), false},
		} {
			value := t.nativeLabels[def.key]
			if value[0] == "" || field.ink != def.ink {
				continue
			}
			if field.text == value[0] {
				text, id = value[1], def.key
			} else if def.wrapped && len(field.text) >= 2 && field.text[1:len(field.text)-1] == value[0] && field.text[0] == '(' && field.text[len(field.text)-1] == ')' {
				text, id = field.text[:1]+value[1]+field.text[len(field.text)-1:], def.key
			}
		}
	}
	if text == "" || text == field.text {
		return nil
	}
	var dialogueFonts map[int]*dialogFont
	if t.dlg != nil {
		dialogueFonts = t.dlg.fonts
	}
	normal, shade, size := notoTranslatedMasks(t.str.fonts, text, field.ink, field.ink, capH, field.shadow != 0, dialogueFonts)
	if normal == nil {
		normal, shade, size = t.notoTranslatedFontMasks(text, field.ink, capH, field.shadow != 0)
	}
	if normal == nil {
		return nil
	}
	if id == "GAME.TXT:0x00015522" {
		bounds := draftAlphaInk(normal).Union(draftAlphaInk(shade))
		dx := (normal.Bounds().Dx()-bounds.Dx())/2-bounds.Min.X
		for _, layer := range []*image.Alpha{normal, shade} {
			copy := image.NewAlpha(layer.Bounds())
			draw.Draw(copy, copy.Bounds(), layer, image.Pt(-dx, 0), draw.Src)
			copy.Pix, layer.Pix = layer.Pix, copy.Pix
		}
	}
	var foreground byte
	found := false
	for i, c := range field.text {
		if c == ' ' {
			continue
		}
		if i >= len(field.colors) {
			return nil
		}
		if found && field.colors[i] != foreground {
			return nil
		}
		foreground, found = field.colors[i], true
	}
	if !found {
		return nil
	}
	before := notoOriginalBefore(field.source)
	safe := field.ink
	original := image.NewRGBA(image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4))
	draw.Draw(original, original.Bounds(), out, safe.Min.Mul(4), draw.Src)
	for pos, value := range field.source.after {
		if image.Pt(pos%320, pos/320).In(safe) && !notoOriginalProtected(portrait, pos) && before[pos] != value {
			draftPaintPixel(out, pos, before[pos], palette, hdBackgroundOverride...)
		}
	}
	draftPaintLayers(out, safe, []*image.Alpha{shade, normal}, []byte{field.shadow, foreground}, palette)
	for y := safe.Min.Y; y < safe.Max.Y; y++ {
		for x := safe.Min.X; x < safe.Max.X; x++ {
			if notoOriginalProtected(portrait, y*320+x) {
				draw.Draw(out, image.Rect(x*4, y*4, x*4+4, y*4+4), original, image.Pt((x-safe.Min.X)*4, (y-safe.Min.Y)*4), draw.Src)
			}
		}
	}
	baseline := field.ink.Max.Y
	if field.shadow != 0 {
		baseline--
	}
	record := map[string]any{"kind": "native-field-translation", "id": id, "source": field.text, "text": text, "safe": safe, "native_ink": field.ink, "font_px": size, "text_ink_px": draftAlphaInk(normal), "cap_height_native": capH, "baseline_native": baseline, "source_kind": field.source.kind, "translated": true}
	if len(portrait) != 0 {
		record["foreground_source"] = portraitID
	}
	return record
}

func nativeRGBFingerprint(indexed, palette []byte, rect image.Rectangle) string {
	if len(indexed) != 64000 || len(palette) != 768 || rect.Empty() || !rect.In(image.Rect(0, 0, 320, 200)) {
		return ""
	}
	rgb := make([]byte, 0, rect.Dx()*rect.Dy()*3)
	for y := rect.Min.Y; y < rect.Max.Y; y++ {
		for x := rect.Min.X; x < rect.Max.X; x++ {
			c := draftColor(indexed[y*320+x], palette)
			rgb = append(rgb, c.R, c.G, c.B)
		}
	}
	return hash(rgb)
}

// 指紋來自R148正常建城截圖；字樣與城鎮退出箭頭必須同時命中。
func draftPaintColonyNoShips(out *image.RGBA, t *draftLanguageTarget, canvas, indexed, palette []byte, cursor image.Rectangle, claimed []map[string]any, hdBackgroundOverride ...draftHDBackground) (map[string]any, string) {
	if t == nil || t.str == nil {
		return nil, ""
	}
	safe, ink, context := image.Rect(135, 131, 191, 139), image.Rect(136, 132, 190, 138), image.Rect(309, 188, 318, 198)
	for _, record := range claimed {
		if rect, ok := record["safe"].(image.Rectangle); ok && rect.Overlaps(safe) {
			return nil, ""
		}
	}
	if nativeRGBFingerprint(canvas, palette, safe) != "d2e7f0d1d4fe4e09b293396371963987a5f125e97d2da0edbd8443f5f43ca3f7" ||
		nativeRGBFingerprint(canvas, palette, context) != "0ad2894e26380fd5ad86d5940a518c94e8ee3c440f4454d2a01bde4289d8d3be" ||
		!draftSameExceptCursor(indexed, canvas, safe, cursor) || !draftSameExceptCursor(indexed, canvas, context, cursor) {
		return nil, ""
	}
	label := t.nativeLabels["LABELS.TXT:@MISC:0x00000159"]
	if label[0] == "" || label[1] == "" {
		return nil, "colony-no-ships-translation-unavailable"
	}
	bg := canvas[safe.Min.Y*320+safe.Min.X]
	foreground := canvas[ink.Min.Y*320+ink.Min.X]
	if foreground == bg {
		return nil, "colony-no-ships-palette"
	}
	count := 0
	var originalInk image.Rectangle
	for y := safe.Min.Y; y < safe.Max.Y; y++ {
		for x := safe.Min.X; x < safe.Max.X; x++ {
			value := canvas[y*320+x]
			if value == bg {
				continue
			}
			if value != foreground {
				return nil, "colony-no-ships-palette"
			}
			count++
			originalInk = originalInk.Union(image.Rect(x, y, x+1, y+1))
		}
	}
	if count != 96 || originalInk != ink {
		return nil, "colony-no-ships-ink"
	}
	var dialogueFonts map[int]*dialogFont
	if t.dlg != nil {
		dialogueFonts = t.dlg.fonts
	}
	normal, _, size := notoTranslatedMasks(t.str.fonts, label[1], safe, ink, 6, false, dialogueFonts)
	if normal == nil {
		return nil, "colony-no-ships-does-not-fit"
	}
	for y := safe.Min.Y; y < safe.Max.Y; y++ {
		for x := safe.Min.X; x < safe.Max.X; x++ {
			if canvas[y*320+x] != bg {
				draftPaintPixel(out, y*320+x, bg, palette, hdBackgroundOverride...)
			}
		}
	}
	draftPaintLayers(out, safe, []*image.Alpha{normal}, []byte{foreground}, palette)
	return map[string]any{"kind": "static-recognition", "id": "LABELS.TXT:@MISC:0x00000159", "source": label[0], "text": label[1], "safe": safe, "native_ink": ink, "font_px": size, "cap_height_native": 6, "source_ink_pixels": count, "foreground_index": foreground, "background_index": bg, "text_ink_px": draftAlphaInk(normal), "baseline_native": ink.Max.Y, "source_rgb_sha256": "d2e7f0d1d4fe4e09b293396371963987a5f125e97d2da0edbd8443f5f43ca3f7", "context_rgb_sha256": "0ad2894e26380fd5ad86d5940a518c94e8ee3c440f4454d2a01bde4289d8d3be", "translated": true}, ""
}

type draftInputDialogProtection struct {
	id       string
	portrait int
	mask     []byte
}
type draftInputDialogDefinition struct {
	id               string
	portrait         int
	box, fingerprint image.Rectangle
	sha              string
}

var draftInputDialogDefinitions = []draftInputDialogDefinition{
	{"GAME.TXT:@LANDHO:0x00000ECE", 1060, image.Rect(59, 112, 266, 160), image.Rect(264, 114, 266, 158), "f71a593dd0554f257a15bf148b75e12877756ce00bd8da8371fd86f61bf64171"},
	{"GAME.TXT:0x00000F21", 1065, image.Rect(58, 113, 264, 151), image.Rect(261, 115, 264, 149), "8bdf95857f65c0b42b8fe28d9c403716df940a1ec692c056de0e595fd889e2c4"},
}

func draftInputDialogMask(def draftInputDialogDefinition) []byte {
	mask := make([]byte, 8000)
	for y := def.box.Min.Y; y < def.box.Max.Y; y++ {
		for x := def.box.Min.X; x < def.box.Max.X; x++ {
			pos := y*320 + x
			mask[pos>>3] |= 1 << uint(pos&7)
		}
	}
	return mask
}
func draftInputDialogBorder(def draftInputDialogDefinition, portrait int, canvas, indexed, palette []byte, cursor image.Rectangle) bool {
	return portrait == def.portrait && nativeRGBFingerprint(canvas, palette, def.fingerprint) == def.sha &&
		draftSameExceptCursor(indexed, canvas, def.fingerprint, cursor)
}

// 保留來源不代表准許繪製；繪製端另要求完整原文正文仍可辨認。
func (p *hdSceneRuntime) textForegroundWithInputBox(f nativeSurfaces, cursor image.Rectangle) []byte {
	mask, portrait := p.seaDialogForeground(f.canvas, f.indexed, f.palette, cursor)
	if len(mask) != 8000 {
		return mask
	}
	for _, def := range draftInputDialogDefinitions {
		if !draftInputDialogBorder(def, portrait, f.canvas, f.indexed, f.palette, cursor) {
			continue
		}
		box := draftInputDialogMask(def)
		for i, value := range box {
			mask[i] |= value
		}
		break
	}
	return mask
}
func draftVerifiedInputDialog(t *draftLanguageTarget, j *nativeJournal, canvas, indexed, palette []byte, cursor image.Rectangle) draftInputDialogProtection {
	if t == nil || t.dlg == nil || j == nil {
		return draftInputDialogProtection{}
	}
	portraitMask, portrait := t.portraits.seaDialogForeground(canvas, indexed, palette, cursor)
	if len(portraitMask) != 8000 {
		return draftInputDialogProtection{}
	}
	for _, def := range draftInputDialogDefinitions {
		if !draftInputDialogBorder(def, portrait, canvas, indexed, palette, cursor) {
			continue
		}
		for _, o := range j.items {
			if o.dialogRun == nil || o.dialogRun.readPos%2 != 0 {
				continue
			}
			shown := dialogShownText(o.dialogRun.chars)
			key, _, why := t.dlg.match(shown)
			if why != "" && t.str != nil {
				_, key, why = t.str.translate(shown)
			}
			fields := notoOriginalFields(o)
			// 命名正文可與輸入標籤併在同一原生觀測；以完整單行認身。
			if (why != "" || key != def.id) && def.id == "GAME.TXT:0x00000F21" && t.str != nil {
				for _, field := range fields {
					_, fieldKey, fieldWhy := t.str.translate(field.text)
					if field.ink == image.Rect(62, 118, 207, 127) && fieldWhy == "" && fieldKey == def.id &&
						notoOriginalSource(field, canvas, indexed, portraitMask, cursor) {
						return draftInputDialogProtection{def.id, portrait, draftInputDialogMask(def)}
					}
				}
			}
			if why != "" || key != def.id {
				continue
			}
			alive := len(fields) > 0
			for _, field := range fields {
				alive = alive && notoOriginalSource(field, canvas, indexed, portraitMask, cursor)
			}
			if alive {
				return draftInputDialogProtection{def.id, portrait, draftInputDialogMask(def)}
			}
		}
	}
	return draftInputDialogProtection{}
}
