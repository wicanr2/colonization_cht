package main

import (
	"bytes"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"path/filepath"

	golem "github.com/wicanr2/dosgolem"
)

// 規格069 R82 READY：開場PIK的獨立來源層，局部索引可超過65535。
const hdOpeningMain = uint32(0x1c430)
const hdOpeningMap = uint32(0x38630)
const hdOpeningPaletteSHA = "b53fcec3d9bbe9af2e1d07566cd74d079dedce14f792788c7471f9e2ef0c6a54"

var hdOpeningSignature = []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8, 0x8e, 0xd9, 3, 0xfd, 0x48, 0x75, 0xe7, 0x5d, 0x5f, 0x5e, 7, 0x1f, 0xc9, 0xcb, 0, 0}

type hdOpeningDefinition struct {
	kind                  byte
	asset, sha            string
	size                  image.Point
	nativeRects, artRects []image.Rectangle
	opaque                bool
}
type hdOpeningCell struct {
	kind  byte
	local uint32
	value byte
}
type hdOpeningRuntime struct {
	sprites                                                                                    *hdOpeningSpriteRuntime
	h                                                                                          *hdRuntime
	art                                                                                        [2]*image.RGBA
	native                                                                                     [2][]byte
	cells                                                                                      [64000]hdOpeningCell
	mapNext, borderNext                                                                        int
	mapValid                                                                                   bool
	revision, mapBirths, borderBirths, transfers, revoked, sameValueRevoked, retired, rejected uint64
}

func loadHDOpeningRuntime(h *hdRuntime, game, directory string) (*hdOpeningRuntime, error) {
	for name, want := range map[string]string{
		"OPENING.EXE":  "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"OPENING.PIK":  "80ea1dd4a00a4029052112882305e573bd7e20066eb095ceabe273a217689185",
		"OPENBORD.PIK": "53f73ae336b5eaca30fa190ec9059426712de6c9c0c181d085814d45c96dab03",
	} {
		raw, err := hdReadFile(filepath.Join(game, name), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != want {
			return nil, fmt.Errorf("opening original fingerprint: %s", name)
		}
	}
	p := &hdOpeningRuntime{h: h}
	p.art[0] = image.NewRGBA(image.Rect(0, 0, 1280, 800))
	p.art[1] = image.NewRGBA(image.Rect(0, 0, 3840, 528))
	for _, def := range hdOpeningDefinitions {
		raw, err := hdReadFile(filepath.Join(directory, def.asset), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != def.sha {
			return nil, fmt.Errorf("opening asset fingerprint: %s", def.asset)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		if im.Bounds() != image.Rect(0, 0, def.size.X, def.size.Y) || def.kind < 1 || def.kind > 2 || len(def.nativeRects) == 0 || len(def.nativeRects) != len(def.artRects) {
			return nil, fmt.Errorf("opening geometry")
		}
		dst := p.art[def.kind-1]
		for k, r := range def.nativeRects {
			a := def.artRects[k]
			target := image.Rect(r.Min.X*4, r.Min.Y*4, r.Max.X*4, r.Max.Y*4)
			if a.Empty() || !a.In(im.Bounds()) || target.Empty() || !target.In(dst.Bounds()) {
				return nil, fmt.Errorf("opening rectangle")
			}
			for y := target.Min.Y; y < target.Max.Y; y++ {
				for x := target.Min.X; x < target.Max.X; x++ {
					sx := a.Min.X + (2*(x-target.Min.X)+1)*a.Dx()/(2*target.Dx())
					sy := a.Min.Y + (2*(y-target.Min.Y)+1)*a.Dy()/(2*target.Dy())
					c := color.NRGBAModel.Convert(im.At(sx, sy)).(color.NRGBA)
					if def.opaque {
						if c.A != 255 {
							return nil, fmt.Errorf("opening opaque base alpha")
						}
						dst.SetRGBA(x, y, color.RGBA{c.R, c.G, c.B, 255})
					} else {
						b := dst.RGBAAt(x, y)
						if b.A != 255 {
							return nil, fmt.Errorf("opening missing opaque underlay")
						}
						// 透明物件只在顯示快取合成；原PNG及alpha保持。
						over := func(s, d byte) byte { return byte((uint32(s)*uint32(c.A) + uint32(d)*uint32(255-c.A) + 127) / 255) }
						dst.SetRGBA(x, y, color.RGBA{over(c.R, b.R), over(c.G, b.G), over(c.B, b.B), 255})
					}
				}
			}
		}
	}
	for _, im := range p.art {
		for at := 3; at < len(im.Pix); at += 4 {
			if im.Pix[at] != 255 {
				return nil, fmt.Errorf("opening incomplete base")
			}
		}
	}
	var err error
	p.sprites, err = loadHDOpeningSprites(p, game, directory)
	if err != nil {
		return nil, err
	}
	h.m.WatchWrite(hdOpeningMain, hdOpeningMain+63999, func(_ *golem.Machine, a uint32, o, v byte) { p.sprites.write(a, o, v) })
	h.m.WatchWrite(0xa0000, 0xafa00-1, func(_ *golem.Machine, a uint32, o, v byte) { p.sprites.publish(a, o, v) })
	h.m.WatchWrite(hdOpeningMain, hdOpeningMain+63999, func(_ *golem.Machine, a uint32, o, v byte) { p.write(a, o, v) })
	h.m.WatchWrite(hdOpeningMap, hdOpeningMap+126719, func(_ *golem.Machine, a uint32, o, v byte) { p.write(a, o, v) })
	return p, nil
}

func (p *hdOpeningRuntime) decoderKnown(cs, ip uint16) bool {
	var code []byte
	if cs == 0xac2 && ip == 0x4f4 {
		code = []byte{0xa4, 0xeb, 0xed, 0x33, 0xc9, 0x4a, 0x75, 9, 0xad, 0xb2, 0x10, 0xd1, 0xed, 0x8b, 0xe8, 0xd1}
	}
	if cs == 0xac2 && ip == 0x550 {
		code = []byte{0xaa, 0xe2, 0xfa, 0xeb, 0x8f, 0xac, 0x0a, 0xc0, 0x74, 0x32, 0x3c, 1, 0x74, 5, 0x8a, 0xc8}
	}
	at := int(cs)*16 + int(ip)
	return len(code) == 16 && at+16 <= len(p.h.m.Mem) && bytes.Equal(p.h.m.Mem[at:at+16], code)
}
func (p *hdOpeningRuntime) write(a uint32, old, value byte) {
	m := p.h.m
	cs, ip := m.CPU.OpAddr()
	if a >= hdOpeningMap && a < hdOpeningMap+126720 {
		if p.mapValid {
			p.mapValid = false
			p.revision++
		}
		k := int(a - hdOpeningMap)
		known := p.decoderKnown(cs, ip)
		if !known || k != p.mapNext {
			p.mapNext = 0
		}
		if known && k == p.mapNext {
			p.mapNext++
		}
		if p.mapNext == 126720 {
			p.mapNext = 0
			raw := m.Mem[hdOpeningMap : hdOpeningMap+126720]
			if hash(raw) != "9aa042dfb838820ea8d7d1c9953478f44dd7d8f85db4d5cc4aa0bb9bb0006b95" {
				p.rejected++
				return
			}
			p.native[1] = bytes.Clone(raw)
			p.mapValid = true
			p.mapBirths++
			p.revision++
		}
		return
	}
	if a < hdOpeningMain || a >= hdOpeningMain+64000 {
		return
	}
	k := int(a - hdOpeningMain)
	prior := p.cells[k]
	p.cells[k] = hdOpeningCell{}
	known := p.decoderKnown(cs, ip)
	if !known || k != p.borderNext {
		p.borderNext = 0
	}
	if known && k == p.borderNext {
		p.borderNext++
	}
	if p.borderNext == 64000 {
		p.borderNext = 0
		raw := m.Mem[hdOpeningMain : hdOpeningMain+64000]
		if hash(raw) != "ee23b1d787958481210fb6c328ccc067805bdbd8d83300c5d8157dd40cf90816" {
			p.rejected++
		} else {
			p.native[0] = bytes.Clone(raw)
			for i, v := range raw {
				p.cells[i] = hdOpeningCell{1, uint32(i), v}
			}
			p.borderBirths++
			p.revision++
			return
		}
	}
	c := m.CPU
	pc := int(cs)*16 + int(ip)
	if cs == 0x3bd && ip == 0xc8 && p.mapValid && c.Flags&0x400 == 0 && bytes.Equal(m.Mem[pc:pc+16], hdOpeningSignature[:16]) {
		delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
		src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
		if delta >= 0 && delta < 2 && int(c.R[golem.SI])+delta < 65536 && int(c.R[golem.DI])+delta < 65536 && src >= int(hdOpeningMap) && src < int(hdOpeningMap)+126720 && len(p.native[1]) == 126720 && m.Mem[src] == value && p.native[1][src-int(hdOpeningMap)] == value {
			p.cells[k] = hdOpeningCell{2, uint32(src - int(hdOpeningMap)), value}
			p.transfers++
		}
	}
	if prior != p.cells[k] {
		p.revision++
	}
	if prior.kind != 0 && p.cells[k].kind == 0 {
		p.revoked++
		if old == value {
			p.sameValueRevoked++
		}
	}
}
func (p *hdOpeningRuntime) live() bool {
	return len(p.h.m.Mem) >= 0x5570+0x9f+32 && bytes.Equal(p.h.m.Mem[0x5570+0x9f:0x5570+0x9f+32], hdOpeningSignature)
}
func (p *hdOpeningRuntime) retire() {
	if p.sprites != nil {
		p.sprites.retire()
	}
	have := p.mapValid
	for _, c := range p.cells {
		have = have || c.kind != 0
	}
	if have {
		clear(p.cells[:])
		p.mapValid = false
		p.mapNext = 0
		p.borderNext = 0
		p.retired++
		p.revision++
	}
}
func (p *hdOpeningRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	return p.paintWithin(out, f, image.Rect(0, 0, 320, 200))
}
func (p *hdOpeningRuntime) paintWithin(out *image.RGBA, f draftNativeFrame, bounds image.Rectangle) map[string]any {
	masks := [][]byte{make([]byte, 8000), make([]byte, 8000)}
	r := map[string]any{"formal": true, "painted": 0, "border_painted": 0, "map_painted": 0, "masks": masks, "map_births": p.mapBirths, "border_births": p.borderBirths, "same_value_revocations": p.sameValueRevoked, "retirements": p.retired, "revision": p.revision}
	reason := ""
	live := p.live()
	if !live {
		p.retire()
		r["retirements"], r["revision"] = p.retired, p.revision
	}
	if f.mode != 0x13 || len(f.indexed) != 64000 || len(f.palette) != 768 {
		reason = "mode"
	} else if !live {
		reason = "code"
	} else if !bytes.Equal(p.h.m.Mem[hdOpeningMain:hdOpeningMain+64000], f.indexed) || !bytes.Equal(p.h.m.Mem[0xa0000:0xafa00], f.indexed) {
		reason = "surface"
	} else if hash(f.palette) != hdOpeningPaletteSHA || hash(p.h.m.Mem[0xafc00:0xaff00]) != hdOpeningPaletteSHA {
		reason = "palette"
	}
	if reason != "" {
		r["reason"] = reason
		return r
	}
	for i, c := range p.cells {
		if c.kind == 0 {
			continue
		}
		if c.kind > 2 || int(c.local) >= len(p.native[c.kind-1]) || p.native[c.kind-1][c.local] != c.value || f.indexed[i] != c.value {
			r["reason"] = "source"
			return r
		}
	}
	counts := [2]int{}
	for pos, c := range p.cells {
		if c.kind == 0 || !image.Pt(pos%320, pos/320).In(bounds) {
			continue
		}
		width := 320
		if c.kind == 2 {
			width = 960
		}
		sx, sy := int(c.local)%width*4, int(c.local)/width*4
		x, y := pos%320*4, pos/320*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), p.art[c.kind-1], image.Pt(sx, sy), draw.Src)
		masks[c.kind-1][pos>>3] |= 1 << uint(pos&7)
		counts[c.kind-1]++
	}
	r["painted"], r["border_painted"], r["map_painted"] = counts[0]+counts[1], counts[0], counts[1]
	r["reason"] = "verified-opening"
	return r
}
