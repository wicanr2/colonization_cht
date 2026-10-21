package main

import (
	"image"
	"image/color"
)

var hdMiniMapBounds = image.Rect(251, 8, 309, 49)
var hdMiniMapInterior = image.Rect(252, 9, 308, 48)

func hdMiniMapOriginalText(o *nativeObservation) ([]byte, bool) {
	if o == nil || len(o.seaRuns) == 0 {
		return nil, false
	}
	var text []byte
	for _, r := range o.seaRuns {
		if r == nil || len(r.raw) < 2 || len(r.raw) > 256 || r.raw[len(r.raw)-1] != 0 {
			return nil, false
		}
		for _, v := range r.raw[:len(r.raw)-1] {
			if v < 32 || v > 126 {
				return nil, false
			}
			text = append(text, v)
		}
	}
	return text, true
}

func hdMiniMapPalette(palette []byte) bool {
	if len(palette) != 768 {
		return false
	}
	colors := []int{0, 6, 12, 15, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67}
	var used []byte
	for _, v := range colors {
		used = append(used, palette[v*3:v*3+3]...)
	}
	return hash(used) == "bb1631956095f032b1a3b042235ac819d0984e91698ca55f973ec8f51a7bc4bb"
}

func hdMiniMapWorldContext(f draftNativeFrame) bool {
	if f.journal == nil {
		return false
	}
	menu, date := false, false
	for _, o := range f.journal.items {
		if o == nil || !o.visible(f.canvas, f.buffer, f.indexed) {
			continue
		}
		if o.ink.Overlaps(hdMiniMapBounds) {
			return false
		}
		text, ok := hdMiniMapOriginalText(o)
		if !ok {
			continue
		}
		if o.kind == "sea-bar" && o.ink == image.Rect(13, 1, 306, 6) && hash(text) == "3f02988e15cd4e0312d3f17063a6c897240e6a156913987a405061cc98137bbc" {
			menu = true
		}
		if o.kind == "sea-panel" && o.ink.Min == image.Pt(242, 51) && o.ink.Max.Y == 57 && o.ink.Max.X <= 314 && o.ink.Max.X > 242 && len(text) >= 6 {
			digits := true
			for _, v := range text[len(text)-4:] {
				digits = digits && v >= '0' && v <= '9'
			}
			date = date || digits
		}
	}
	return menu && date
}

func (h *hdRuntime) miniMapMaterial() *image.NRGBA {
	if h == nil || h.opening == nil || h.opening.sprites == nil {
		return nil
	}
	slot, ok := hdOpeningSpriteSlot(1031)
	if !ok {
		return nil
	}
	d := hdOpeningSpriteDefinitions[slot]
	art := h.opening.sprites.art[slot]
	if d.id != 1031 || !d.silverGlyphMaterial || d.asset != "mpsname-silver-material.png" ||
		d.artSHA != "d7bf0ac7048ab765381a582d5fe380267c7186b130ae6237944c7242df0f82ad" ||
		art == nil || art.Rect != image.Rect(0, 0, 96, 100) {
		return nil
	}
	return art
}

// 規格069 R140 READY：只重建已驗世界小地圖輸出，不讀取未探索地圖或改寫原版。
func (h *hdRuntime) paintNativeMiniMap(out *image.RGBA, f draftNativeFrame) map[string]any {
	result := map[string]any{"formal": true, "source": "VICEROY.EXE:world-minimap", "painted": 0, "native_bounds": hdMiniMapBounds}
	reject := func(reason string) map[string]any { result["reason"] = reason; return result }
	if h == nil || h.m == nil || out == nil || out.Rect != image.Rect(0, 0, 1280, 800) || f.mode != 0x13 ||
		len(f.canvas) != 64000 || len(f.buffer) != 64000 || len(f.indexed) != 64000 || len(f.palette) != 768 {
		return reject("native-shape")
	}
	if !hdMiniMapPalette(f.palette) {
		return reject("native-palette")
	}
	art := h.miniMapMaterial()
	if art == nil {
		return reject("material")
	}
	if !hdMiniMapWorldContext(f) {
		return reject("world-context-or-text")
	}
	if !draftSameExceptCursor(f.indexed, f.canvas, hdMiniMapBounds, f.cursor) {
		return reject("visible-surface")
	}
	if f.cursor.Overlaps(hdMiniMapBounds) {
		if _, why := h.cursorPixelsProof(f); why != "" {
			return reject("unverified-cursor")
		}
	}
	whiteBounds := image.Rectangle{}
	white := 0
	preserve := make([]bool, hdMiniMapBounds.Dx()*hdMiniMapBounds.Dy())
	owned := 0
	for y := hdMiniMapBounds.Min.Y; y < hdMiniMapBounds.Max.Y; y++ {
		for x := hdMiniMapBounds.Min.X; x < hdMiniMapBounds.Max.X; x++ {
			pos := y*320 + x
			value := f.canvas[pos]
			frame := x == hdMiniMapBounds.Min.X || x == hdMiniMapBounds.Max.X-1 || y == hdMiniMapBounds.Min.Y || y == hdMiniMapBounds.Max.Y-1
			if frame {
				if value != 6 {
					return reject("frame-incomplete")
				}
			} else if value != 0 && value != 12 && value != 15 && (value < 56 || value > 67) {
				return reject("unclassified-map-pixel")
			}
			if value == 15 {
				whiteBounds = whiteBounds.Union(image.Rect(x, y, x+1, y+1))
				white++
			}
			if h.scenes != nil {
				c := h.scenes.visible[pos]
				if c.slot != 0 {
					source, valid := h.scenes.frame(c)
					if !valid || int(c.local) >= len(source.native) || c.value != value || source.native[int(c.local)] != value || c.glyph {
						return reject("bitmap-owner")
					}
					preserve[(y-hdMiniMapBounds.Min.Y)*hdMiniMapBounds.Dx()+x-hdMiniMapBounds.Min.X] = true
					owned++
				}
			}
		}
	}
	painted, changed := 0, 0
	for y := hdMiniMapBounds.Min.Y; y < hdMiniMapBounds.Max.Y; y++ {
		for x := hdMiniMapBounds.Min.X; x < hdMiniMapBounds.Max.X; x++ {
			k := (y-hdMiniMapBounds.Min.Y)*hdMiniMapBounds.Dx() + x - hdMiniMapBounds.Min.X
			if preserve[k] {
				continue
			}
			value := f.canvas[y*320+x]
			at := int(value) * 3
			native := color.RGBA{(f.palette[at] << 2) | (f.palette[at] >> 4), (f.palette[at+1] << 2) | (f.palette[at+1] >> 4), (f.palette[at+2] << 2) | (f.palette[at+2] >> 4), 255}
			for dy := 0; dy < 4; dy++ {
				for dx := 0; dx < 4; dx++ {
					sample := art.NRGBAAt(((x-hdMiniMapBounds.Min.X)*4+dx)%art.Rect.Dx(), ((y-hdMiniMapBounds.Min.Y)*4+dy)%art.Rect.Dy())
					luma := (uint32(sample.R)*77 + uint32(sample.G)*150 + uint32(sample.B)*29) >> 8
					pixel := native
					if value == 0 {
						v := byte(8 + luma/21)
						pixel = color.RGBA{v, v, v, 255}
					} else if value != 15 {
						gain := uint32(128) + luma/2
						pixel.R = byte(uint32(native.R) * gain / 256)
						pixel.G = byte(uint32(native.G) * gain / 256)
						pixel.B = byte(uint32(native.B) * gain / 256)
					}
					out.SetRGBA(x*4+dx, y*4+dy, pixel)
					if pixel != native {
						changed++
					}
				}
			}
			painted++
		}
	}
	result["painted"], result["changed_RGBA_points"], result["bitmap_cells_preserved"] = painted, changed, owned
	result["white_bounds"], result["white_pixels"], result["material_asset"] = whiteBounds, white, "mpsname-silver-material.png"
	result["reason"] = "verified-native-world-minimap"
	return result
}
