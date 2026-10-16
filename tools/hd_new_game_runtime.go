// 規格069 R69 READY：新遊戲背景，只合成顯示，不修改DOS。
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

type hdNewGameDefinition struct {
	id                                                        int
	file, originalSHA, nativeSHA, asset, assetSHA, paletteSHA string
	scenes                                                    map[string]string
	nativeRects, artRects                                     []image.Rectangle
}
type hdNewGameFrame struct {
	hdNewGameDefinition
	native  []byte
	art     *image.RGBA
	decoded uint64
}
type hdNewGameGlyphPair struct {
	old, value byte
	k          int
	glyph      bool
}
type hdNewGameRuntime struct {
	h                  *hdRuntime
	frames             []*hdNewGameFrame
	frame              *hdNewGameFrame
	glyph              [64000]bool
	pending            map[int]hdNewGameGlyphPair
	counts             [64000]byte
	decoding           bool
	seen               int
	revision, rejected uint64
}

var hdPictureWriterCodes = map[uint16][]byte{
	0x4ee: {0xa4, 0xeb, 0xed, 0x33, 0xc9, 0x4a, 0x75, 9, 0xad, 0xb2, 0x10, 0xd1, 0xed, 0x8b, 0xe8, 0xd1},
	0x54a: {0xaa, 0xe2, 0xfa, 0xeb, 0x8f, 0xac, 0x0a, 0xc0, 0x74, 0x32, 0x3c, 1, 0x74, 5, 0x8a, 0xc8},
}

func loadHDNewGameRuntime(h *hdRuntime, game, dir string) (*hdNewGameRuntime, error) {
	p := &hdNewGameRuntime{h: h, pending: map[int]hdNewGameGlyphPair{}}
	for _, def := range hdNewGameDefinitions {
		raw, err := hdReadFile(filepath.Join(game, def.file), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != def.originalSHA {
			return nil, fmt.Errorf("new-game original fingerprint")
		}
		raw, err = hdReadFile(filepath.Join(dir, def.asset), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != def.assetSHA {
			return nil, fmt.Errorf("new-game art fingerprint")
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		if im.Bounds() != image.Rect(0, 0, 1586, 992) || len(def.nativeRects) != len(def.artRects) {
			return nil, fmt.Errorf("new-game art geometry")
		}
		f := &hdNewGameFrame{hdNewGameDefinition: def, art: image.NewRGBA(image.Rect(0, 0, 1280, 800))}
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				sx, sy := (2*x+1)*1586/2560, (2*y+1)*992/1600
				card := false
				for i, r := range def.nativeRects {
					target := image.Rect(r.Min.X*4, r.Min.Y*4, r.Max.X*4, r.Max.Y*4)
					if image.Pt(x, y).In(target) {
						a := def.artRects[i]
						sx = a.Min.X + (2*(x-target.Min.X)+1)*a.Dx()/(2*target.Dx())
						sy = a.Min.Y + (2*(y-target.Min.Y)+1)*a.Dy()/(2*target.Dy())
						card = true
						break
					}
				}
				if !card {
					for _, r := range def.artRects {
						if image.Pt(sx, sy).In(r) {
							sx = 32
							break
						}
					}
				}
				c := color.RGBAModel.Convert(im.At(sx, sy)).(color.RGBA)
				if c.A != 255 {
					return nil, fmt.Errorf("new-game art alpha")
				}
				f.art.SetRGBA(x, y, c)
			}
		}
		p.frames = append(p.frames, f)
	}
	if len(p.frames) != 2 {
		return nil, fmt.Errorf("new-game source group")
	}
	return p, nil
}

func (p *hdNewGameRuntime) memoryWrite(a uint32, old, value byte) {
	if p == nil {
		return
	}
	m := p.h.m
	cs, ip := m.CPU.OpAddr()
	pc := int(cs)*16 + int(ip)
	if a >= 0x3c500 && a < 0x3c500+64000 {
		k := int(a - 0x3c500)
		code, known := hdPictureWriterCodes[ip]
		known = known && cs == 0x11b5 && bytes.Equal(m.Mem[pc:pc+16], code)
		if k == 0 && known {
			clear(p.counts[:])
			p.seen = 0
			p.decoding = true
		}
		if p.decoding {
			if !known || p.counts[k] != 0 {
				p.decoding = false
				p.rejected++
			} else {
				p.counts[k] = 1
				p.seen++
				if k == 63999 {
					p.decoding = false
					if p.seen == 64000 {
						raw := m.Mem[0x3c500 : 0x3c500+64000]
						digest := hash(raw)
						for _, f := range p.frames {
							if digest == f.nativeSHA {
								f.native = append([]byte(nil), raw...)
								f.decoded++
								p.revision++
								break
							}
						}
					} else {
						p.rejected++
					}
				}
			}
		}
	}
	if a < hdBuildingCanvas || a >= hdBuildingCanvas+64000 {
		return
	}
	k := int(a - hdBuildingCanvas)
	if cs == 0xb68 && ip == 0x51c && m.CPU.Seg[golem.DS] == 0xa000 && m.CPU.Seg[golem.ES] == 0x2cae &&
		bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}) {
		delta := int(a) - (int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI]))
		src := int(m.CPU.R[golem.SI]) + delta
		if delta == 0 && src >= 0xfa00 && src < 0xfc00 && m.Mem[0xa0000+src] == value {
			if _, ok := p.h.cursorSource(); ok {
				if src >= 0xfb00 {
					p.pending[k] = hdNewGameGlyphPair{old, value, src & 255, p.glyph[k]}
					p.glyph[k] = false
					p.revision++
					return
				}
				prior, ok := p.pending[k]
				delete(p.pending, k)
				if ok && prior.k == src&255 && old == prior.value && value == prior.old {
					p.glyph[k] = prior.glyph
					p.revision++
					return
				}
			}
		}
	}
	clear(p.pending)
	v := cs == 0xd21 && ip == 0x12c && bytes.Equal(m.Mem[pc:pc+16], []byte{0x26, 0x88, 0x25, 0x47, 0xfe, 0xca, 0x74, 0x0a, 0xfe, 0xcd, 0x75, 0xdf, 0xac, 0xb5, 4, 0xeb})
	if p.glyph[k] != v {
		p.glyph[k] = v
		p.revision++
	}
}

func (p *hdNewGameRuntime) glyphMask() []byte {
	mask := make([]byte, 8000)
	for k, v := range p.glyph {
		if v {
			mask[k>>3] |= 1 << uint(k&7)
		}
	}
	return mask
}
func (p *hdNewGameRuntime) selectFrame(f draftNativeFrame) *hdNewGameFrame {
	if p == nil || f.mode != 0x13 || len(f.canvas) != 64000 || len(f.palette) != 768 {
		return nil
	}
	canvas, palette, glyph := hash(f.canvas), hash(f.palette), hash(p.glyphMask())
	for _, frame := range p.frames {
		if frame.decoded > 0 && len(frame.native) == 64000 && frame.paletteSHA == palette && frame.scenes[canvas] == glyph {
			return frame
		}
	}
	return nil
}
func (p *hdNewGameRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	p.frame = p.selectFrame(f)
	mask := make([]byte, 8000)
	painted := 0
	id := 0
	if frame := p.frame; frame != nil {
		id = frame.id
		for k, v := range frame.native {
			if p.glyph[k] || f.canvas[k] != v {
				continue
			}
			x, y := k%320*4, k/320*4
			draw.Draw(out, image.Rect(x, y, x+4, y+4), frame.art, image.Pt(x, y), draw.Src)
			mask[k>>3] |= 1 << uint(k&7)
			painted++
		}
	}
	return map[string]any{"prototype": false, "formal": true, "matched": id != 0, "source_id": id, "painted": painted, "mask": mask, "glyph_mask": p.glyphMask(), "revision": p.revision, "rejected_decodes": p.rejected}
}
func (p *hdNewGameRuntime) paintBackground(out *image.RGBA, f draftNativeFrame, pos int, v byte, palette []byte) bool {
	if p == nil || p.frame == nil || pos < 0 || pos >= 64000 || len(f.canvas) != 64000 ||
		hash(palette) != p.frame.paletteSHA || p.frame.native[pos] != v {
		return false
	}
	x, y := pos%320*4, pos/320*4
	draw.Draw(out, image.Rect(x, y, x+4, y+4), p.frame.art, image.Pt(x, y), draw.Src)
	return true
}
