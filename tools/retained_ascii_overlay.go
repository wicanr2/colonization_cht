// 規格052 READY：主畫布單色英數的字格觀測與可撤銷字型覆蓋。
package main

import (
	"flag"
	"image"
	"strings"
)

var retainedASCIIEnabled = flag.Bool("retained-ascii-a", false, "規格052：保留原值、以現有中文字型顯示已驗單色英數")
var retainedGlyphBounds = map[*dialogFont]map[rune]image.Rectangle{}

func retainedPrintable(text []byte) bool {
	alnum := false
	for _, c := range text {
		if c < 0x20 || c > 0x7e {
			return false
		}
		alnum = alnum || c >= '0' && c <= '9' || c >= 'A' && c <= 'Z' || c >= 'a' && c <= 'z'
	}
	return alnum
}

func retainedTextBounds(f *dialogFont, text string) (image.Rectangle, bool) {
	var bounds image.Rectangle
	x := 0
	if retainedGlyphBounds[f] == nil {
		retainedGlyphBounds[f] = map[rune]image.Rectangle{}
	}
	for _, c := range text {
		glyph, has := f.glyphs[c]
		advance, widthOK := f.widths[c]
		if !has || glyph == nil || !widthOK || advance <= 0 {
			return image.Rectangle{}, false
		}
		b, cached := retainedGlyphBounds[f][c]
		if !cached {
			for y := glyph.Rect.Min.Y; y < glyph.Rect.Max.Y; y++ {
				for xx := glyph.Rect.Min.X; xx < glyph.Rect.Max.X; xx++ {
					if glyph.AlphaAt(xx, y).A != 0 {
						b = b.Union(image.Rect(xx, y, xx+1, y+1))
					}
				}
			}
			retainedGlyphBounds[f][c] = b
		}
		if !b.Empty() {
			bounds = bounds.Union(b.Add(image.Pt(x, 0)))
		}
		x += advance
	}
	return bounds, !bounds.Empty()
}

type retainedASCIIPlan struct {
	size   int
	bounds image.Rectangle
	font   *dialogFont
}

func planRetainedASCII(fonts map[int]*dialogFont, text string, original image.Rectangle) *retainedASCIIPlan {
	var best *retainedASCIIPlan
	for size := stringFloorPx; size <= stringFontPx; size++ {
		f := fonts[size]
		if f == nil {
			continue
		}
		bounds, ok := retainedTextBounds(f, text)
		if !ok || bounds.Dx() > original.Dx()*4 || bounds.Dy() > original.Dy()*4 {
			continue
		}
		if best == nil || bounds.Dy() > best.bounds.Dy() || bounds.Dy() == best.bounds.Dy() && size > best.size {
			best = &retainedASCIIPlan{size, bounds, f}
		}
	}
	return best
}

// 只用當次0D21:00C6的ES:DI游標及下一次讀字游標建立字格，不由字元猜寬度。
func observeRetainedASCIICursor(current, completed *stringRun, di, es uint16) {
	r := current
	if completed != nil {
		r = completed
	}
	if r != nil {
		r.retainedCursor = append(r.retainedCursor, image.Pt(int(di)%320, int(di)/320))
		r.retainedSegments = append(r.retainedSegments, es)
	}
}

func retainedASCIILayout(r *stringRun, ink image.Rectangle) (image.Rectangle, bool) {
	if len(r.retainedCursor) != len(r.text)+1 || len(r.retainedSegments) != len(r.retainedCursor) {
		return image.Rectangle{}, false
	}
	for i, box := range r.boxes {
		start, end := r.retainedCursor[i], r.retainedCursor[i+1]
		if r.retainedSegments[i] != 0x2cae || r.retainedSegments[i+1] != 0x2cae ||
			start.Y != end.Y || end.X <= start.X || end.X-start.X > 32 ||
			(!box.Empty() && !box.In(image.Rect(start.X, start.Y, end.X, start.Y+16))) {
			return image.Rectangle{}, false
		}
	}
	layout := image.Rect(ink.Min.X, ink.Min.Y, r.retainedCursor[len(r.text)].X, ink.Max.Y)
	return layout, !layout.Empty() && ink.In(layout) && layout.In(image.Rect(0, 0, 320, 200))
}

func retainedASCIIVisible(it *stringItem, indexed []byte, cursor image.Rectangle) bool {
	return it.phase == "active" && len(indexed) == 64000 && stringSame(indexed, it, cursor)
}

func finishRetainedASCII(s *stringRuntime, r *stringRun, canvas []byte, step uint64, baselineWhy string) (*stringItem, string) {
	if baselineWhy != "" && baselineWhy != "no-template" {
		return nil, baselineWhy
	}
	if len(canvas) != 64000 || len(r.text) != len(r.boxes) || !retainedPrintable(r.text) {
		return nil, "retained-invalid-source"
	}
	if s.cat == nil || s.cat.isOwned(string(r.text)) {
		return nil, "owned-by-field"
	}
	if r.buf2 || r.mixed || r.outline || r.keyColor != 0 || len(r.colors) != 1 {
		return nil, "retained-unreviewed-style"
	}
	var ink image.Rectangle
	for _, box := range r.boxes {
		ink = ink.Union(box)
	}
	if ink.Empty() || !ink.In(image.Rect(0, 0, 320, 200)) {
		return nil, "retained-invalid-ink"
	}
	layout, valid := retainedASCIILayout(r, ink)
	if !valid {
		return nil, "retained-unverified-cell"
	}
	safe := layout.Inset(-1).Intersect(image.Rect(0, 0, 320, 200))
	if r.others.Overlaps(safe) {
		return nil, "other-writer"
	}
	text := strings.Trim(string(r.text), " ")
	plan := planRetainedASCII(s.cat.fonts, text, layout)
	if plan == nil {
		return nil, "retained-font-does-not-fit"
	}
	normal := image.NewAlpha(image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4))
	x := (ink.Min.X-safe.Min.X)*4 - plan.bounds.Min.X
	y := (ink.Min.Y-safe.Min.Y)*4 - plan.bounds.Min.Y
	for _, c := range text {
		dialogBlit(normal, plan.font.glyphs[c], x, y)
		x += plan.font.widths[c]
	}
	before := append([]byte(nil), canvas...)
	for index, value := range r.firstOld {
		if index < 0 || index >= len(before) {
			return nil, "retained-invalid-writer"
		}
		before[index] = value
	}
	var color byte
	for value := range r.colors {
		color = value
	}
	const id = "STRING:retained-ascii"
	if previous := s.reprintBackground(r, id, ink, safe, color, canvas); previous != nil {
		for yy := safe.Min.Y; yy < safe.Max.Y; yy++ {
			copy(before[yy*320+safe.Min.X:yy*320+safe.Max.X], previous[(yy-safe.Min.Y)*safe.Dx():(yy-safe.Min.Y+1)*safe.Dx()])
		}
	}
	return &stringItem{id: id, text: string(r.text), zh: text, ink: ink, safe: safe, color: color,
		size: plan.size, norm: normal, shadow: image.NewAlpha(normal.Rect), accent: image.NewAlpha(normal.Rect),
		before: stringRect(before, safe), after: stringRect(canvas, safe), phase: "waiting-screen", complete: step}, ""
}
