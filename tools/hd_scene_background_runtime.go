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
	"strings"
)

// 規格069 R76／R77 READY：來源、解碼畫布與原圖固定，所有狀態只供顯示。
type hdSceneDefinition struct {
	nativeGeometryMaterial                                    bool
	nativeGlyphMaterial                                       bool
	closingBackground                                         bool
	artSize                                                   image.Point
	alphaSprites                                              bool
	sprite                                                    *hdSceneSpriteDefinition
	allowPictureCursorProof                                   bool
	id, offset, height                                        int
	canvas, alternateCanvas                                   uint32
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
	slot  uint16
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
	spriteFontSource                                            func(string) bool
	spriteFontObserver                                          func(*hdSceneSpriteCall, *hdSceneFrame, []byte)
	spriteFontState                                             any
	spriteFontWriteObserver                                     func(uint32)
	spriteFontRectStamp                                         func(image.Rectangle) uint64
	spriteCall                                                  *hdSceneSpriteCall
	spriteAccepted, spriteRejected                              uint64
	publishedPending                                            map[int]hdSceneCursorPair
	h                                                           *hdRuntime
	frames                                                      []*hdSceneFrame
	visible, stage, published                                   [64000]hdSceneCell
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
	return loadSceneRuntime(h, game, directory, true)
}

// 規格060 R150：文字前景只觀測原版來源，不需要生成圖像或HD畫布。
func loadTextSceneRuntime(m *golem.Machine, game string) (*hdSceneRuntime, error) {
	original, err := hdReadFile(filepath.Join(game, "VICEROY.EXE"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(original) != versions["VICEROY.EXE"] {
		return nil, fmt.Errorf("text scene executable fingerprint")
	}
	return loadSceneRuntime(&hdRuntime{m: m}, game, "", false)
}

func loadSceneRuntime(h *hdRuntime, game, directory string, withArt bool) (*hdSceneRuntime, error) {
	closing, err := hdReadFile(filepath.Join(game, "CLOSING.EXE"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(closing) != hdClosingSceneEXESHA {
		return nil, fmt.Errorf("closing scene executable fingerprint")
	}
	p := &hdSceneRuntime{h: h, publishedPending: map[int]hdSceneCursorPair{}, backing: map[uint32]hdSceneCell{}, pending: map[int]hdSceneCursorPair{}, start: -1}
	artCache := map[string]struct {
		im  image.Image
		sha string
	}{}
	for _, def := range hdSceneDefinitions {
		original, err := hdReadFile(filepath.Join(game, def.file), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(original) != def.originalSHA {
			return nil, fmt.Errorf("scene original fingerprint: %s", def.file)
		}
		cached, exists := artCache[def.asset]
		if withArt && !exists {
			raw, err := hdReadFile(filepath.Join(directory, def.asset), 8<<20)
			if err != nil {
				return nil, err
			}
			digest := hash(raw)
			if digest != def.assetSHA {
				return nil, fmt.Errorf("scene asset fingerprint: %s", def.asset)
			}
			im, err := png.Decode(bytes.NewReader(raw))
			if err != nil {
				return nil, err
			}
			cached = struct {
				im  image.Image
				sha string
			}{im, digest}
			artCache[def.asset] = cached
		}
		if withArt && cached.sha != def.assetSHA {
			return nil, fmt.Errorf("scene cached asset fingerprint: %s", def.asset)
		}
		im := cached.im
		if def.alternateCanvas != 0 && (def.alternateCanvas != hdBuildingCanvas || def.canvas != 0) {
			return nil, fmt.Errorf("scene alternate canvas")
		}
		wantBounds := image.Rectangle{}
		for _, rect := range def.artRects {
			wantBounds.Max.X = max(wantBounds.Max.X, rect.Max.X)
			wantBounds.Max.Y = max(wantBounds.Max.Y, rect.Max.Y)
		}
		if def.artSize != (image.Point{}) {
			wantBounds = image.Rect(0, 0, def.artSize.X, def.artSize.Y)
		}
		if def.alphaSprites && def.sprite == nil {
			return nil, fmt.Errorf("scene alpha requires sprite")
		}
		if (withArt && im.Bounds() != wantBounds) || def.offset < 0 || def.height <= 0 || def.offset+320*def.height != 64000 || len(def.nativeRects) == 0 || len(def.nativeRects) != len(def.artRects) {
			return nil, fmt.Errorf("scene geometry")
		}
		artBounds := image.Rect(0, 0, 1280, def.height*4)
		if s := def.sprite; s != nil {
			artBounds = image.Rect(0, 0, s.width*4, s.height*4)
		}
		f := &hdSceneFrame{hdSceneDefinition: def}
		if withArt {
			f.art = image.NewRGBA(artBounds)
		}
		covered := make([]bool, 320*def.height)
		for i, r := range def.nativeRects {
			a := def.artRects[i]
			if r.Empty() || !r.In(image.Rect(0, 0, 320, def.height)) || a.Empty() || !a.In(wantBounds) {
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
			if !withArt {
				continue
			}
			target := image.Rect(r.Min.X*4, r.Min.Y*4, r.Max.X*4, r.Max.Y*4)
			for y := target.Min.Y; y < target.Max.Y; y++ {
				for x := target.Min.X; x < target.Max.X; x++ {
					sx := a.Min.X + (2*(x-target.Min.X)+1)*a.Dx()/(2*target.Dx())
					sy := a.Min.Y + (2*(y-target.Min.Y)+1)*a.Dy()/(2*target.Dy())
					c := color.RGBAModel.Convert(im.At(sx, sy)).(color.RGBA)
					if c.A != 255 && !def.alphaSprites {
						return nil, fmt.Errorf("scene art alpha")
					}
					f.art.SetRGBA(x, y, c)
				}
			}
		}
		expectedBounds := image.Rect(0, 0, 320, def.height)
		if s := def.sprite; s != nil {
			expectedBounds = image.Rect(0, 0, s.width, s.height)
			if s.content != (image.Rectangle{}) {
				if !def.alphaSprites || s.content.Empty() || !s.content.In(expectedBounds) {
					return nil, fmt.Errorf("scene sprite content")
				}
				expectedBounds = s.content
			}
		}
		for k, yes := range covered {
			expected := image.Pt(k%320, k/320).In(expectedBounds)
			if yes != expected {
				return nil, fmt.Errorf("incomplete scene geometry")
			}
		}
		p.frames = append(p.frames, f)
	}
	if len(p.frames) != 895 {
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
		if f.sprite != nil {
			continue
		}
		wantBase := f.canvas
		if wantBase == 0 {
			wantBase = 0x3c500
		}
		if (wantBase != base && (f.alternateCanvas == 0 || f.alternateCanvas != base)) || f.offset != start || f.nativeSHA != digest {
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
			cell := hdSceneCell{slot: uint16(slot + 1), local: uint16(local), value: v}
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
	pc := int(cs)*16 + int(ip)
	code, yes := hdSceneCopyCodes[ip]
	if hdClosingSceneCopyPC(pc) {
		code, yes = hdSceneVGACopyCode, c.Flags&0x400 == 0
	} else {
		yes = yes && (cs == 0xc9f || cs == 0xcba)
	}
	if !yes {
		return hdSceneCell{}, false
	}
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
	return got, got.slot != 0 && int(got.slot) <= len(p.frames) && (p.frames[int(got.slot)-1].sprite == nil || p.frames[int(got.slot)-1].closingSource()) && got.value == value
}
func (p *hdSceneRuntime) memoryWrite(a uint32, old, value byte) {
	if p != nil {
		p.recordSpriteWrite(a, value)
	}
	if p == nil || p.blocked {
		return
	}
	if a >= 0xa0000 {
		p.publish(a, old, value)
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
			if bufferBase == hdBuildingCanvas && p.spriteFontWriteObserver != nil {
				p.spriteFontWriteObserver(a)
			}
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
		if p.spriteFontWriteObserver != nil {
			p.spriteFontWriteObserver(a)
		}
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
	receipt := map[string]any{"formal": true, "sources": records, "blocked": p.blocked, "rejected": p.rejected, "unmatched_pictures": p.unmatched, "cursor_paint_points": p.cursorPaints, "cursor_restore_points": p.cursorRestores, "sprite_accepted": p.spriteAccepted, "sprite_rejected": p.spriteRejected}
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
		if c.slot == 0 {
			if under, yes := p.spriteCursorCell(at, f); yes {
				c = under
			}
		}
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
		frame.drawCell(out, x, y, sx, sy, f.palette)
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
	if c.slot == 0 {
		if under, known := p.spriteCursorCell(pos, f); known {
			c = under
		}
	}
	frame, yes := p.frame(c)
	if !yes || f.canvas[pos] != c.value || frame.native[int(c.local)] != value || !frame.paletteSupported(palette) {
		return false
	}
	x, y := pos%320*4, pos/320*4
	sx, sy := int(c.local)%320*4, int(c.local)/320*4
	frame.drawCell(out, x, y, sx, sy, palette)
	return true
}

var hdSceneVGAByteCode = []byte{0xa4, 0xe2, 0xec, 0xeb, 0xd8, 0xd1, 0xee, 0x73, 0x04, 0x81, 0xf6, 0x00, 0xb4, 0x81, 0xfe, 0x00}

var hdSceneVGACopyCode = []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}

// 規格069 R79 READY：主畫布送出後的寫入不能改變已顯示來源。
// 每一筆未知VGA寫入，包括同值寫入，都先撤銷該點的來源。

func (p *hdSceneRuntime) publish(a uint32, oldValue, value byte) {
	if a < 0xa0000 || a >= 0xa0000+64000 {
		return
	}
	at := int(a - 0xa0000)
	oldCell := p.published[at]
	p.published[at] = hdSceneCell{}
	pair, paired := p.publishedPending[at]
	delete(p.publishedPending, at)
	m, c := p.h.m, p.h.m.CPU
	cs, ip := c.OpAddr()
	pc := int(cs)*16 + int(ip)
	delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	sourceOffset := int(c.R[golem.SI]) + delta
	cursorCode := []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}
	if cs == 0xb68 && ip == 0x51c && c.Seg[golem.DS] == 0xa000 && c.Seg[golem.ES] == 0xa000 &&
		delta == 0 && sourceOffset >= 0xfa00 && sourceOffset < 0xfc00 && pc+16 <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+16], cursorCode) {
		if source, known := p.h.cursorSource(); known && m.Mem[0xa0000+sourceOffset] == value {
			k := sourceOffset & 255
			back, composed := m.Mem[0xafa00+k], m.Mem[0xafb00+k]
			if sourceOffset >= 0xfb00 && back == oldValue && composed == value && (source[k] == 255 && value == back || source[k] != 255 && value == source[k]) {
				if source[k] == 255 && oldValue == value && oldCell.slot != 0 && oldCell.value == value {
					p.published[at] = oldCell
				} else if source[k] != 255 && oldCell.slot != 0 && oldCell.value == oldValue {
					p.publishedPending[at] = hdSceneCursorPair{old: oldValue, value: value, k: k, cell: oldCell}
				}
			} else if sourceOffset < 0xfb00 && back == value {
				if source[k] == 255 && composed == oldValue && oldValue == value && oldCell.slot != 0 && oldCell.value == value {
					p.published[at] = oldCell
				} else if paired && pair.old == value && pair.value == oldValue && pair.k == k && composed == oldValue && source[k] == oldValue {
					p.published[at] = pair.cell
				}
			}
		}
	}
	if len(p.publishedPending) > 256 {
		p.blocked = true
		clear(p.published[:])
		clear(p.publishedPending)
	}
	knownWord := cs == 0xe21 && ip == 0x91 && delta >= 0 && delta < 2 && pc >= 0 && pc+16 <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+16], hdSceneVGACopyCode)
	knownByte := cs == 0xe2d && ip == 0xaa && delta == 0 && pc >= 0 && pc+16 <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+16], hdSceneVGAByteCode)
	if (knownWord || knownByte) && c.Seg[golem.ES] == 0xa000 {
		src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
		if delta >= 0 && delta < 2 && int(c.R[golem.SI])+delta < 65536 && int(c.R[golem.DI])+delta < 64000 && src == int(hdBuildingCanvas)+at && src < len(m.Mem) && m.Mem[src] == value {
			cell := p.visible[at]
			if frame, known := p.frame(cell); known && (frame.sprite == nil || frame.sprite.closingContext) && cell.value == value {
				p.published[at] = cell
			}
		}
	}
	if hdClosingSceneCopyPC(pc) && c.Flags&0x400 == 0 && c.Seg[golem.ES] == 0xa000 && delta >= 0 && delta < 2 && int(c.R[golem.SI])+delta < 65536 && int(c.R[golem.DI])+delta < 64000 && pc+16 <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+16], hdSceneVGACopyCode) {
		src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
		if src >= 0 && src < 0xa0000 && m.Mem[src] == value {
			cell := p.cell(uint32(src))
			if frame, known := p.frame(cell); known && frame.closingSource() && cell.value == value {
				p.published[at] = cell
			}
		}
	}
	if oldCell != p.published[at] {
		p.revision++
	}
}

// 只在既有完整主畫布守門拒絕時使用。其他HD層與文字來源契約保持。
// 原版可見索引、原始VGA、來源值及色盤逐點核對；游標矩形保留原圖。
func (p *hdSceneRuntime) paintPublished(out *image.RGBA, f draftNativeFrame) map[string]any {
	records := map[string]any{}
	r := map[string]any{"formal": true, "surface": "published-vga", "sources": records, "painted": 0}
	if p == nil || p.blocked || f.mode != 0x13 || len(f.canvas) != 64000 || len(f.indexed) != 64000 ||
		len(f.palette) != 768 ||
		len(p.h.m.Mem) < 0xa0000+64000 ||
		!bytes.Equal(p.h.m.Mem[0xa0000:0xa0000+64000], f.indexed) {
		r["reason"] = "unverified-vga-surface"
		return r
	}
	pictureOnlyCursor := p.pictureOnlyCursor(f)
	r["picture_only_cursor"] = pictureOnlyCursor
	_, reason := p.h.cursorProof(f)
	cursorVerified := pictureOnlyCursor || reason == "" || strings.HasPrefix(reason, "outside-cursor:")
	independent := false
	for _, cell := range p.published {
		if frame, known := p.frame(cell); known && frame.closingSource() {
			independent = true
			break
		}
	}
	if !independent && (f.cursor.Dx() != 16 || f.cursor.Dy() != 16) {
		r["reason"] = "unverified-vga-surface"
		return r
	}
	if !cursorVerified && !independent {
		r["reason"] = "unverified-cursor"
		return r
	}

	palettes := make([]bool, len(p.frames))
	masks := make([][]byte, len(p.frames))
	counts := make([]int, len(p.frames))
	for i, frame := range p.frames {
		palettes[i], masks[i] = frame.paletteSupported(f.palette), make([]byte, 8000)
	}
	cursorSource, _ := p.h.cursorSource()
	for at, c := range p.published {
		frame, known := p.frame(c)
		closing := known && frame.closingSource()
		if !closing && !cursorVerified {
			continue
		}
		if !known || c.glyph || !palettes[int(c.slot)-1] || c.value != f.indexed[at] ||
			frame.native[int(c.local)] != c.value || (!closing && !pictureOnlyCursor && image.Pt(at%320, at/320).In(f.cursor) && cursorSource[(at/320-f.cursor.Min.Y)*16+at%320-f.cursor.Min.X] != 255) {
			continue
		}
		x, y := at%320*4, at/320*4
		sx, sy := int(c.local)%320*4, int(c.local)/320*4
		frame.drawCell(out, x, y, sx, sy, f.palette)
		i := int(c.slot) - 1
		masks[i][at>>3] |= 1 << uint(at&7)
		counts[i]++
	}
	total := 0
	for i, frame := range p.frames {
		records[fmt.Sprint(frame.id)] = map[string]any{"painted": counts[i], "palette_supported": palettes[i], "mask": masks[i]}
		total += counts[i]
	}
	r["painted"], r["reason"] = total, "published-scene-background-only"
	return r
}

func (p *hdSceneRuntime) paintPublishedBackground(out *image.RGBA, f draftNativeFrame, pos int, value byte, palette []byte) bool {
	if p == nil || p.blocked || pos < 0 || pos >= 64000 || f.mode != 0x13 || len(f.indexed) != 64000 || len(f.canvas) != 64000 || len(p.h.m.Mem) < 0xa0000+64000 {
		return false
	}
	c := p.published[pos]
	frame, yes := p.frame(c)
	if !yes || c.value != f.indexed[pos] || p.h.m.Mem[0xa0000+pos] != c.value || frame.native[int(c.local)] != value || !frame.paletteSupported(palette) {
		return false
	}
	x, y := pos%320*4, pos/320*4
	sx, sy := int(c.local)%320*4, int(c.local)/320*4
	frame.drawCell(out, x, y, sx, sy, palette)
	return true
}

// 規格069 R89 READY： every current VGA cell under the nominal cursor must retain
// independently validated picture publication. An opaque cursor write revokes it.
func (p *hdSceneRuntime) pictureOnlyCursor(f draftNativeFrame) bool {
	if p == nil || p.blocked || len(f.indexed) != 64000 || f.cursor.Dx() != 16 || f.cursor.Dy() != 16 {
		return false
	}
	r := f.cursor.Intersect(image.Rect(0, 0, 320, 200))
	if r.Empty() {
		return false
	}
	for y := r.Min.Y; y < r.Max.Y; y++ {
		for x := r.Min.X; x < r.Max.X; x++ {
			at := y*320 + x
			c := p.published[at]
			frame, known := p.frame(c)
			if !known || !frame.allowPictureCursorProof || c.value != f.indexed[at] || (!c.glyph && frame.native[int(c.local)] != c.value) {
				return false
			}
		}
	}
	return true
}

func (f *hdSceneFrame) drawCell(out *image.RGBA, x, y, sx, sy int, palette []byte) {
	if f.nativeGlyphMaterial || f.nativeGeometryMaterial {
		k := sy/4*320 + sx/4
		if len(palette) != 768 || k < 0 || k >= len(f.native) || f.native[k] == 253 {
			return
		}
		at := int(f.native[k]) * 3
		for dy := 0; dy < 4; dy++ {
			for dx := 0; dx < 4; dx++ {
				a := f.art.RGBAAt(sx+dx, sy+dy)
				luma := (77*uint32(a.R) + 150*uint32(a.G) + 29*uint32(a.B) + 128) >> 8
				if f.nativeGeometryMaterial && palette[at] == 0 && palette[at+1] == 0 && palette[at+2] == 0 {
					v := byte(8 + luma/21)
					out.SetRGBA(x+dx, y+dy, color.RGBA{v, v, v, 255})
					continue
				}
				gain := uint32(128) + luma/2
				shade := func(v byte) byte {
					v = (v << 2) | (v >> 4)
					return byte((uint32(v)*gain + 127) / 255)
				}
				out.SetRGBA(x+dx, y+dy, color.RGBA{shade(palette[at]), shade(palette[at+1]), shade(palette[at+2]), 255})
			}
		}
		return
	}

	op := draw.Src
	if f.alphaSprites {
		op = draw.Over
	}
	draw.Draw(out, image.Rect(x, y, x+4, y+4), f.art, image.Pt(sx, sy), op)
}

func (f *hdSceneFrame) closingSource() bool {
	return f.closingBackground || f.sprite != nil && f.sprite.closingContext
}
func (p *hdSceneRuntime) captureClosingBackground(canvas uint32) {
	if canvas < 0x10000 || canvas+64000 > 0xa0000 {
		return
	}
	raw := p.h.m.Mem[canvas : canvas+64000]
	digest := hash(raw)
	for slot, f := range p.frames {
		if !f.closingBackground || f.sprite != nil || f.offset != 0 || f.height != 200 || f.nativeSHA != digest {
			continue
		}
		f.native = append([]byte(nil), raw...)
		f.indices = nil
		used := [256]bool{}
		for _, v := range raw {
			used[v] = true
		}
		for i, yes := range used {
			if yes {
				f.indices = append(f.indices, byte(i))
			}
		}
		f.decoded++
		for local, v := range raw {
			p.set(canvas+uint32(local), hdSceneCell{slot: uint16(slot + 1), local: uint16(local), value: v})
		}
		return
	}
}
