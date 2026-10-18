package main

import (
	"bytes"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"path/filepath"
)

// 規格069 R76／R77 READY：來源、解碼畫布與原圖固定，所有狀態只供顯示。
type hdSceneDefinition struct {
	id, offset, height                                        int
	canvas                                                    uint32
	file, originalSHA, nativeSHA, asset, assetSHA, paletteSHA string
	nativeRects, artRects                                     []image.Rectangle
}
type hdSceneFrame struct {
	hdSceneDefinition
	art     *image.RGBA
	native  []byte
	indices []byte
	decoded uint64
}
type hdSceneCell struct {
	slot  uint8
	local uint16
	value byte
	glyph bool
}
type hdSceneCursorPair struct {
	old, value byte
	k          int
	cell       hdSceneCell
}
type hdSceneRuntime struct {
	h                                                           *hdRuntime
	frames                                                      []*hdSceneFrame
	visible, stage                                              [64000]hdSceneCell
	backing                                                     map[uint32]hdSceneCell
	pending                                                     map[int]hdSceneCursorPair
	decodeBase                                                  uint32
	decoding                                                    bool
	start, next                                                 int
	blocked                                                     bool
	revision, rejected, unmatched, cursorPaints, cursorRestores uint64
}

var hdSceneCopyCodes = map[uint16][]byte{
	0x9c: {0xf3, 0xa5, 0xa4, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0},
	0x9e: {0xa4, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8, 0x8e},
	0xca: {0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8},
}

func loadHDSceneRuntime(h *hdRuntime, game, directory string) (*hdSceneRuntime, error) {
	p := &hdSceneRuntime{h: h, backing: map[uint32]hdSceneCell{}, pending: map[int]hdSceneCursorPair{}, start: -1}
	for _, def := range hdSceneDefinitions {
		original, err := hdReadFile(filepath.Join(game, def.file), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(original) != def.originalSHA {
			return nil, fmt.Errorf("scene original fingerprint: %s", def.file)
		}
		raw, err := hdReadFile(filepath.Join(directory, def.asset), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != def.assetSHA {
			return nil, fmt.Errorf("scene asset fingerprint: %s", def.asset)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		wantBounds := image.Rectangle{}
		for _, rect := range def.artRects {
			wantBounds.Max.X = max(wantBounds.Max.X, rect.Max.X)
			wantBounds.Max.Y = max(wantBounds.Max.Y, rect.Max.Y)
		}
		if im.Bounds() != wantBounds || def.offset < 0 || def.height <= 0 || def.offset+320*def.height != 64000 || len(def.nativeRects) == 0 || len(def.nativeRects) != len(def.artRects) {
			return nil, fmt.Errorf("scene geometry")
		}
		f := &hdSceneFrame{hdSceneDefinition: def, art: image.NewRGBA(image.Rect(0, 0, 1280, def.height*4))}
		covered := make([]bool, 320*def.height)
		for i, r := range def.nativeRects {
			a := def.artRects[i]
			if r.Empty() || !r.In(image.Rect(0, 0, 320, def.height)) || a.Empty() || !a.In(im.Bounds()) {
				return nil, fmt.Errorf("scene rectangle")
			}
			for y := r.Min.Y; y < r.Max.Y; y++ {
				for x := r.Min.X; x < r.Max.X; x++ {
					k := y*320 + x
					if covered[k] {
						return nil, fmt.Errorf("overlapping scene rectangles")
					}
					covered[k] = true
				}
			}
			target := image.Rect(r.Min.X*4, r.Min.Y*4, r.Max.X*4, r.Max.Y*4)
			for y := target.Min.Y; y < target.Max.Y; y++ {
				for x := target.Min.X; x < target.Max.X; x++ {
					sx := a.Min.X + (2*(x-target.Min.X)+1)*a.Dx()/(2*target.Dx())
					sy := a.Min.Y + (2*(y-target.Min.Y)+1)*a.Dy()/(2*target.Dy())
					c := color.RGBAModel.Convert(im.At(sx, sy)).(color.RGBA)
					if c.A != 255 {
						return nil, fmt.Errorf("scene art alpha")
					}
					f.art.SetRGBA(x, y, c)
				}
			}
		}
		for _, yes := range covered {
			if !yes {
				return nil, fmt.Errorf("incomplete scene geometry")
			}
		}
		p.frames = append(p.frames, f)
	}
	if len(p.frames) != 10 {
		return nil, fmt.Errorf("scene source group")
	}
	h.m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, o, v byte) { p.memoryWrite(a, o, v) })
	return p, nil
}
func (p *hdSceneRuntime) cell(a uint32) hdSceneCell {
	switch {
	case a >= hdBuildingCanvas && a < hdBuildingCanvas+64000:
		return p.visible[a-hdBuildingCanvas]
	case a >= 0x3c500 && a < 0x3c500+64000:
		return p.stage[a-0x3c500]
	default:
		return p.backing[a]
	}
}
func (p *hdSceneRuntime) set(a uint32, c hdSceneCell) {
	old := p.cell(a)
	if old == c {
		return
	}
	switch {
	case a >= hdBuildingCanvas && a < hdBuildingCanvas+64000:
		p.visible[a-hdBuildingCanvas] = c
	case a >= 0x3c500 && a < 0x3c500+64000:
		p.stage[a-0x3c500] = c
	default:
		if c.slot == 0 {
			delete(p.backing, a)
		} else {
			if old.slot == 0 && len(p.backing) >= 300000 {
				p.blocked = true
				p.decoding = false
				clear(p.visible[:])
				clear(p.stage[:])
				clear(p.backing)
				clear(p.pending)
				p.revision++
				return
			}
			p.backing[a] = c
		}
	}
	p.revision++
}
func (p *hdSceneRuntime) decoded(start int) { p.decodedAt(0x3c500, start) }
func (p *hdSceneRuntime) decodedAt(base uint32, start int) {
	if (base != 0x3c500 && base != hdBuildingCanvas) || start < 0 || start >= 64000 {
		p.rejected++
		return
	}
	raw := p.h.m.Mem[int(base)+start : int(base)+64000]
	digest := hash(raw)
	for slot, f := range p.frames {
		wantBase := f.canvas
		if wantBase == 0 {
			wantBase = 0x3c500
		}
		if wantBase != base || f.offset != start || f.nativeSHA != digest {
			continue
		}
		f.native = append([]byte(nil), raw...)
		f.indices = nil
		used := [256]bool{}
		for _, v := range raw {
			used[v] = true
		}
		for v, yes := range used {
			if yes {
				f.indices = append(f.indices, byte(v))
			}
		}
		f.decoded++
		for local, v := range raw {
			cell := hdSceneCell{slot: uint8(slot + 1), local: uint16(local), value: v}
			if base == 0x3c500 {
				p.stage[start+local] = cell
			} else {
				p.visible[start+local] = cell
			}
		}
		p.revision++
		return
	}
	p.unmatched++
}
func (p *hdSceneRuntime) copyCell(a uint32, value byte) (hdSceneCell, bool) {
	m := p.h.m
	c := m.CPU
	cs, ip := c.OpAddr()
	code, yes := hdSceneCopyCodes[ip]
	if !yes || (cs != 0xc9f && cs != 0xcba) {
		return hdSceneCell{}, false
	}
	pc := int(cs)*16 + int(ip)
	if pc < 0 || pc+16 > len(m.Mem) || !bytes.Equal(m.Mem[pc:pc+16], code) {
		return hdSceneCell{}, false
	}
	delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	width := 2
	if ip == 0x9e {
		width = 1
	}
	src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
	if delta < 0 || delta >= width || int(c.R[golem.SI])+delta >= 65536 || int(c.R[golem.DI])+delta >= 65536 || src < 0 || src >= 0xa0000 || src >= len(m.Mem) || m.Mem[src] != value {
		return hdSceneCell{}, false
	}
	got := p.cell(uint32(src))
	return got, got.slot != 0 && int(got.slot) <= len(p.frames) && got.value == value
}
func (p *hdSceneRuntime) memoryWrite(a uint32, old, value byte) {
	if p == nil || p.blocked || a >= 0xa0000 {
		return
	}
	m := p.h.m
	c := m.CPU
	cs, ip := c.OpAddr()
	pc := int(cs)*16 + int(ip)
	knownCode := func(code []byte) bool {
		return pc >= 0 && pc+len(code) <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+len(code)], code)
	}
	bufferBase := uint32(0)
	if a >= 0x3c500 && a < 0x3c500+64000 {
		bufferBase = 0x3c500
	} else if a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
		bufferBase = hdBuildingCanvas
	}
	if bufferBase != 0 {
		k := int(a - bufferBase)
		code, known := hdPictureWriterCodes[ip]
		known = known && cs == 0x11b5 && knownCode(code)
		if known {
			if bufferBase == hdBuildingCanvas {
				clear(p.pending)
			}
			p.set(a, hdSceneCell{})
			if k == 0 || (bufferBase == 0x3c500 && k == 40960 && !p.decoding) {
				p.decodeBase = bufferBase
				p.start = k
				p.next = k
				p.decoding = true
			}
			if p.decoding {
				if bufferBase != p.decodeBase || k != p.next {
					p.decoding = false
					p.rejected++
				} else {
					p.next++
					if p.next == 64000 {
						p.decoding = false
						p.decodedAt(p.decodeBase, p.start)
					}
				}
			}
			return
		}
		if p.decoding && p.decodeBase == bufferBase {
			p.decoding = false
			p.rejected++
		}
	}
	prior := p.cell(a)
	main := a >= hdBuildingCanvas && a < hdBuildingCanvas+64000
	if main && cs == 0xb68 && ip == 0x51c && c.Seg[golem.DS] == 0xa000 && c.Seg[golem.ES] == 0x2cae && knownCode([]byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}) {
		delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
		src := int(c.R[golem.SI]) + delta
		if _, yes := p.h.cursorSource(); yes && delta == 0 && src >= 0xfa00 && src < 0xfc00 && m.Mem[0xa0000+src] == value {
			k := int(a - hdBuildingCanvas)
			if src >= 0xfb00 {
				p.pending[k] = hdSceneCursorPair{old, value, src & 255, prior}
				p.set(a, hdSceneCell{})
				p.cursorPaints++
				return
			}
			pair, yes := p.pending[k]
			delete(p.pending, k)
			if yes && pair.k == src&255 && old == pair.value && value == pair.old {
				p.set(a, pair.cell)
				p.cursorRestores++
				return
			}
		}
	}
	if main {
		clear(p.pending)
	}
	next, _ := p.copyCell(a, value)
	if cs == 0xd21 && ip == 0x12c && knownCode([]byte{0x26, 0x88, 0x25, 0x47, 0xfe, 0xca, 0x74, 0x0a, 0xfe, 0xcd, 0x75, 0xdf, 0xac, 0xb5, 4, 0xeb}) && prior.slot != 0 && prior.value == old {
		next = prior
		next.value = value
		next.glyph = true
	}
	p.set(a, next)
}
func (f *hdSceneFrame) paletteSupported(palette []byte) bool {
	if len(palette) != 768 || len(f.native) != 320*f.height || len(f.indices) == 0 {
		return false
	}
	raw := make([]byte, 0, len(f.indices)*4)
	for _, i := range f.indices {
		raw = append(raw, i)
		raw = append(raw, palette[int(i)*3:int(i)*3+3]...)
	}
	return hash(raw) == f.paletteSHA
}
func (p *hdSceneRuntime) frame(c hdSceneCell) (*hdSceneFrame, bool) {
	if c.slot == 0 || int(c.slot) > len(p.frames) {
		return nil, false
	}
	f := p.frames[int(c.slot)-1]
	return f, len(f.native) == 320*f.height && int(c.local) < len(f.native)
}
func (p *hdSceneRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	records := map[string]any{}
	receipt := map[string]any{"formal": true, "sources": records, "blocked": p.blocked, "rejected": p.rejected, "unmatched_pictures": p.unmatched, "cursor_paint_points": p.cursorPaints, "cursor_restore_points": p.cursorRestores}
	if p.blocked {
		receipt["reason"] = "backing-limit"
		return receipt
	}
	if f.mode != 0x13 || len(f.canvas) != 64000 || len(f.indexed) != 64000 || len(f.palette) != 768 {
		receipt["reason"] = "native-shape"
		return receipt
	}
	okPalette := make([]bool, len(p.frames))
	masks := make([][]byte, len(p.frames))
	counts := make([][4]int, len(p.frames))
	for i, frame := range p.frames {
		okPalette[i] = frame.paletteSupported(f.palette)
		masks[i] = make([]byte, 8000)
	}
	for at, c := range p.visible {
		frame, known := p.frame(c)
		if !known {
			continue
		}
		n := int(c.slot) - 1
		if c.glyph {
			counts[n][1]++
			continue
		}
		counts[n][0]++
		if f.canvas[at] != c.value || frame.native[int(c.local)] != c.value {
			continue
		}
		counts[n][2]++
		if !okPalette[n] {
			continue
		}
		x, y := at%320*4, at/320*4
		sx, sy := int(c.local)%320*4, int(c.local)/320*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), frame.art, image.Pt(sx, sy), draw.Src)
		masks[n][at>>3] |= 1 << uint(at&7)
		counts[n][3]++
	}
	for i, frame := range p.frames {
		v := counts[i]
		records[fmt.Sprint(frame.id)] = map[string]any{"decoded": frame.decoded, "palette_supported": okPalette[i], "owned_background": v[0], "glyph_underlays": v[1], "valid_background": v[2], "painted": v[3], "mask": masks[i]}
	}
	return receipt
}
func (p *hdSceneRuntime) paintBackground(out *image.RGBA, f draftNativeFrame, pos int, value byte, palette []byte) bool {
	if p == nil || p.blocked || pos < 0 || pos >= 64000 || len(f.canvas) != 64000 || f.mode != 0x13 {
		return false
	}
	c := p.visible[pos]
	frame, yes := p.frame(c)
	if !yes || f.canvas[pos] != c.value || frame.native[int(c.local)] != value || !frame.paletteSupported(palette) {
		return false
	}
	x, y := pos%320*4, pos/320*4
	sx, sy := int(c.local)%320*4, int(c.local)/320*4
	draw.Draw(out, image.Rect(x, y, x+4, y+4), frame.art, image.Pt(sx, sy), draw.Src)
	return true
}
