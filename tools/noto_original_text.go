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

func notoOriginalSource(field notoOriginalField, canvas, indexed, mask []byte, cursor image.Rectangle) bool {
	o, safe := field.source, field.ink
	source := o.canvas
	if o.kind == "string-map" {
		source = o.buffer
	}
	if safe.Empty() || !safe.In(image.Rect(0, 0, 320, 200)) || len(source) != 64000 || len(o.after) == 0 {
		return false
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
			return false
		}
		if _, ok := before[pos]; !ok {
			return false
		}
		if canvas[pos] != value && !notoOriginalProtected(mask, pos) {
			return false
		}
		if image.Pt(pos%320, pos/320).In(safe) {
			if inkColors[before[pos]] {
				return false // 原字色底圖可能含舊字；不猜背景。
			}
			own++
		}
	}
	if own == 0 {
		return false
	}
	for y := safe.Min.Y; y < safe.Max.Y; y++ {
		for x := safe.Min.X; x < safe.Max.X; x++ {
			pos := y*320 + x
			if canvas[pos] != source[pos] && !notoOriginalProtected(mask, pos) ||
				indexed[pos] != canvas[pos] && !image.Pt(x, y).In(cursor) {
				return false
			}
		}
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
	for _, field := range candidates {
		blocked := false
		for _, safe := range safes {
			blocked = blocked || safe.Overlaps(field.ink)
		}
		if blocked {
			continue
		}
		if !notoOriginalSource(field, canvas, indexed, portrait, cursor) {
			misses["source-changed\t"+field.text]++
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
			if image.Pt(pos%320, pos/320).In(safe) && !notoOriginalProtected(portrait, pos) && before[pos] != value {
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
				if notoOriginalProtected(portrait, yy*320+xx) {
					draw.Draw(out, image.Rect(xx*4, yy*4, xx*4+4, yy*4+4), original, image.Pt((xx-safe.Min.X)*4, (yy-safe.Min.Y)*4), draw.Src)
				}
			}
		}
		record := map[string]any{"kind": "original-noto", "id": "FONT:original", "source": field.text, "text": field.text,
			"safe": safe, "native_ink": safe, "font_px": plan.size, "font_only": true, "translated": false,
			"source_kind": field.source.kind, "baseline_shift_px": -plan.bounds.Min.Y}
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
