// 規格069 R83 READY：開場SS完整呼叫與已發布來源；不改原版RAM、規則或計時。
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"path/filepath"
)

type hdOpeningSpriteDefinition struct {
	ordinal                              int
	encodedSHA, writesSHA, asset, artSHA string
	artRects, nativeRects                []image.Rectangle
}
type hdOpeningSpriteCell struct {
	id, local uint16
	value     byte
	under     hdOpeningCell
}
type hdOpeningSpriteRuntime struct {
	p                                                                 *hdOpeningRuntime
	art                                                               [8]*image.NRGBA
	native                                                            [8][1175]byte
	nativeValid                                                       [8]bool
	cells, published                                                  [64000]hdOpeningSpriteCell
	pictures                                                          [64000]hdOpeningCell
	active, outside                                                   bool
	selected, x, y                                                    int
	retCS, retIP, sp                                                  uint16
	start                                                             uint64
	counts                                                            [1175]uint16
	writes                                                            [1175]byte
	under                                                             [1175]hdOpeningCell
	accepted, rejected, revoked, same, transfers, unknownVGA, sameVGA uint64
}

var hdOpeningSpriteWriterCodes = map[uint16][]byte{
	0x177: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xe7, 0xeb, 0xd0, 0x3b},
	0x1aa: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x03, 0xeb, 0xe7, 0x90, 0xeb, 0xcc},
	0x1c8: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xeb, 0xb5, 0x90, 0x5a, 0x5b, 0x03, 0x5e, 0xfe, 0x79},
}

func loadHDOpeningSprites(p *hdOpeningRuntime, game, directory string) (*hdOpeningSpriteRuntime, error) {
	raw, e := hdReadFile(filepath.Join(game, "OPENSHIP.SS"), 8<<20)
	if e != nil {
		return nil, e
	}
	if hash(raw) != "eee07bfee9a7abf512d6bd9688409427149df3226edd024342871f41e143af10" {
		return nil, fmt.Errorf("opening ship original fingerprint")
	}
	s := &hdOpeningSpriteRuntime{p: p}
	for i, d := range hdOpeningSpriteDefinitions {
		raw, e = hdReadFile(filepath.Join(directory, d.asset), 8<<20)
		if e != nil {
			return nil, e
		}
		if hash(raw) != d.artSHA {
			return nil, fmt.Errorf("opening ship asset fingerprint: %s", d.asset)
		}
		im, e := png.Decode(bytes.NewReader(raw))
		if e != nil {
			return nil, e
		}
		if im.Bounds() != image.Rect(0, 0, 1442, 1091) || d.ordinal != i || len(d.artRects) != len(d.nativeRects) || len(d.artRects) == 0 {
			return nil, fmt.Errorf("opening ship geometry")
		}
		dst := image.NewNRGBA(image.Rect(0, 0, 188, 100))
		if i != 0 {
			copy(dst.Pix, s.art[0].Pix)
		}
		for k, r := range d.nativeRects {
			a := d.artRects[k]
			target := image.Rect(r.Min.X*4, r.Min.Y*4, r.Max.X*4, r.Max.Y*4)
			if a.Empty() || !a.In(im.Bounds()) || target.Empty() || !target.In(dst.Bounds()) {
				return nil, fmt.Errorf("opening ship rectangle")
			}
			for y := target.Min.Y; y < target.Max.Y; y++ {
				for x := target.Min.X; x < target.Max.X; x++ {
					sx := a.Min.X + (2*(x-target.Min.X)+1)*a.Dx()/(2*target.Dx())
					sy := a.Min.Y + (2*(y-target.Min.Y)+1)*a.Dy()/(2*target.Dy())
					dst.SetNRGBA(x, y, color.NRGBAModel.Convert(im.At(sx, sy)).(color.NRGBA))
				}
			}
		}
		s.art[i] = dst
	}
	return s, nil
}
func hdOpeningSpriteWords(m *golem.Machine, seg, off uint16, n int) ([]uint16, bool) {
	at := int(seg)*16 + int(off)
	if int(off)+n*2 > 65536 || at+n*2 > len(m.Mem) {
		return nil, false
	}
	v := make([]uint16, n)
	for i := range v {
		v[i] = binary.LittleEndian.Uint16(m.Mem[at+i*2:])
	}
	return v, true
}
func (s *hdOpeningSpriteRuntime) beforeInstruction() {
	if s == nil {
		return
	}
	m := s.p.h.m
	c := m.CPU
	cs, ip := c.Seg[golem.CS], c.IP
	if s.active {
		if cs == s.retCS && ip == s.retIP && c.R[golem.SP] == s.sp+10 {
			s.finish()
		} else if m.Steps-s.start > 100000 || (cs == 0x4a2 && ip == 0) {
			s.active = false
			s.rejected++
		}
	}
	if cs != 0x4a2 || ip != 0 || s.active {
		return
	}
	if !bytes.Equal(m.Mem[0x4a20:0x4a20+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	ordinal := int(c.R[golem.AX]&0x7fff) - 1
	if ordinal < 0 || ordinal >= 8 {
		return
	}
	stack, ok := hdOpeningSpriteWords(m, c.Seg[golem.SS], c.R[golem.SP], 5)
	if !ok {
		return
	}
	desc, ok := hdOpeningSpriteWords(m, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok {
		return
	}
	off := uint32(c.R[golem.AX]&0x7fff)*12 + uint32(stack[3]) + 0x36
	if off+12 > 65536 {
		return
	}
	record, ok := hdOpeningSpriteWords(m, stack[4], uint16(off), 6)
	if !ok {
		return
	}
	src := int(record[1])*16 + int(record[0])
	if int(record[0])+639 > 65536 || src+639 > len(m.Mem) || hash(m.Mem[src:src+639]) != hdOpeningSpriteDefinitions[ordinal].encodedSHA {
		return
	}
	x, y := int(int16(c.R[golem.DX])), int(int16(stack[2]))
	if desc[0] != 200 || desc[1] != 320 || desc[2] != 0 || desc[3] != 0x1c43 || record[4] != 47 || record[5] != 25 || x < 0 || y < 0 || x+47 > 320 || y+25 > 200 {
		s.rejected++
		return
	}
	s.active, s.outside, s.selected, s.x, s.y = true, false, ordinal, x, y
	s.retIP, s.retCS, s.sp, s.start = stack[0], stack[1], c.R[golem.SP], m.Steps
	clear(s.counts[:])
	clear(s.writes[:])
	clear(s.under[:])
	for k := 0; k < 1175; k++ {
		pos := (y+k/47)*320 + x + k%47
		under := s.p.cells[pos]
		inherited := false
		if under.kind == 0 {
			prev := s.cells[pos]
			if prev.id != 0 && prev.value == m.Mem[hdOpeningMain+uint32(pos)] {
				under = prev.under
				inherited = true
			}
		}
		if s.validUnder(under) && (inherited || under.value == m.Mem[hdOpeningMain+uint32(pos)]) {
			s.under[k] = under
		}
	}
}
func (s *hdOpeningSpriteRuntime) validUnder(c hdOpeningCell) bool {
	return c.kind >= 1 && c.kind <= 2 && int(c.local) < len(s.p.native[c.kind-1]) && s.p.native[c.kind-1][c.local] == c.value
}
func (s *hdOpeningSpriteRuntime) write(a uint32, old, v byte) {
	pos := int(a - hdOpeningMain)
	if pos < 0 || pos >= 64000 {
		return
	}
	if s.cells[pos].id != 0 {
		s.revoked++
		if old == v {
			s.same++
		}
	}
	s.cells[pos] = hdOpeningSpriteCell{}
	if !s.active {
		return
	}
	x, y := pos%320-s.x, pos/320-s.y
	cs, ip := s.p.h.m.CPU.OpAddr()
	code := hdOpeningSpriteWriterCodes[ip]
	pc := int(cs)*16 + int(ip)
	if cs != 0x4a2 || len(code) != 16 || !bytes.Equal(s.p.h.m.Mem[pc:pc+16], code) || x < 0 || y < 0 || x >= 47 || y >= 25 {
		s.outside = true
		return
	}
	k := y*47 + x
	s.counts[k]++
	s.writes[k] = v
}
func (s *hdOpeningSpriteRuntime) finish() {
	s.active = false
	blob := make([]byte, 0, 512*3)
	for k, n := range s.counts {
		if n == 0 {
			continue
		}
		if n != 1 {
			s.outside = true
		}
		blob = binary.LittleEndian.AppendUint16(blob, uint16(k))
		blob = append(blob, s.writes[k])
	}
	if s.outside || len(blob) != 512*3 || hash(blob) != hdOpeningSpriteDefinitions[s.selected].writesSHA {
		s.rejected++
		return
	}
	for k := range s.native[s.selected] {
		s.native[s.selected][k] = 253
	}
	for k, n := range s.counts {
		if n != 1 {
			continue
		}
		s.native[s.selected][k] = s.writes[k]
		pos := (s.y+k/47)*320 + s.x + k%47
		s.cells[pos] = hdOpeningSpriteCell{uint16(1250 + s.selected), uint16(k), s.writes[k], s.under[k]}
	}
	s.nativeValid[s.selected] = true
	s.accepted++
	s.p.revision++
}
func (s *hdOpeningSpriteRuntime) publish(a uint32, old, value byte) {
	pos := int(a) - 0xa0000
	if pos < 0 || pos >= 64000 {
		return
	}
	oldActor, oldPIC := s.published[pos], s.pictures[pos]
	s.published[pos] = hdOpeningSpriteCell{}
	s.pictures[pos] = hdOpeningCell{}
	m := s.p.h.m
	c := m.CPU
	cs, ip := c.OpAddr()
	pc := int(cs)*16 + int(ip)
	known := false
	if cs == 0x557 && ip == 0x9f && c.Flags&0x400 == 0 && bytes.Equal(m.Mem[pc:pc+16], hdOpeningSignature[:16]) {
		delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
		src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
		known = delta >= 0 && delta < 2 && int(c.R[golem.DI])+delta < 65536 && int(c.R[golem.SI])+delta < 65536 && src == int(hdOpeningMain)+pos && m.Mem[src] == value
	}
	if known {
		pic, actor := s.p.cells[pos], s.cells[pos]
		if pic.kind != 0 && pic.value == value {
			s.pictures[pos] = pic
			s.transfers++
		}
		if actor.id != 0 && actor.value == value {
			s.published[pos] = actor
			s.transfers++
		}
	} else if oldActor.id != 0 || oldPIC.kind != 0 {
		s.unknownVGA++
		if old == value {
			s.sameVGA++
		}
	}
	if oldActor != s.published[pos] || oldPIC != s.pictures[pos] {
		s.p.revision++
	}
}
func (s *hdOpeningSpriteRuntime) retire() {
	clear(s.cells[:])
	clear(s.published[:])
	clear(s.pictures[:])
	clear(s.nativeValid[:])
	s.active = false
}
func (s *hdOpeningSpriteRuntime) paintWithin(out *image.RGBA, f draftNativeFrame, bounds image.Rectangle) map[string]any {
	r := map[string]any{"formal": true, "painted": 0, "sprite_painted": 0, "border_painted": 0, "map_painted": 0, "accepted": s.accepted, "rejected": s.rejected, "same_value_revocations": s.same, "published_transfers": s.transfers, "unknown_vga_revocations": s.unknownVGA, "same_value_vga_revocations": s.sameVGA}
	m := s.p.h.m
	reason := ""
	if !s.p.live() {
		s.retire()
		s.p.retire()
		reason = "code"
	} else if f.mode != 0x13 || len(f.indexed) != 64000 || len(f.palette) != 768 {
		reason = "mode"
	} else if !bytes.Equal(m.Mem[0xa0000:0xafa00], f.indexed) {
		reason = "surface"
	} else if hash(f.palette) != hdOpeningPaletteSHA || hash(m.Mem[0xafc00:0xaff00]) != hdOpeningPaletteSHA {
		reason = "palette"
	}
	if reason != "" {
		r["reason"] = reason
		return r
	}
	for pos, c := range s.pictures {
		if c.kind != 0 && (!s.validUnder(c) || f.indexed[pos] != c.value) {
			r["reason"] = "picture-source"
			return r
		}
	}
	for pos, c := range s.published {
		if c.id == 0 {
			continue
		}
		slot := int(c.id) - 1250
		if slot < 0 || slot >= 8 || int(c.local) >= 1175 || !s.nativeValid[slot] || s.native[slot][c.local] != c.value || c.value == 253 || f.indexed[pos] != c.value {
			r["reason"] = "sprite-source"
			return r
		}
		if c.under.kind != 0 && !s.validUnder(c.under) {
			r["reason"] = "underlay-source"
			return r
		}
	}
	mask := make([]byte, 8000)
	spriteMask := make([]byte, 8000)
	counts := [2]int{}
	sprites := 0
	frames := [8]int{}
	for pos := 0; pos < 64000; pos++ {
		if !image.Pt(pos%320, pos/320).In(bounds) {
			continue
		}
		x, y := pos%320*4, pos/320*4
		pic := s.pictures[pos]
		actor := s.published[pos]
		if actor.id != 0 && s.validUnder(actor.under) {
			pic = actor.under
		}
		if pic.kind == 0 {
			continue
		}
		w := 320
		if pic.kind == 2 {
			w = 960
		}
		sx, sy := int(pic.local)%w*4, int(pic.local)/w*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), s.p.art[pic.kind-1], image.Pt(sx, sy), draw.Src)
		if actor.id == 0 {
			counts[pic.kind-1]++
			mask[pos>>3] |= 1 << uint(pos&7)
			continue
		}
		if !s.validUnder(actor.under) {
			continue
		}
		slot := int(actor.id) - 1250
		sx, sy = int(actor.local)%47*4, int(actor.local)/47*4
		for dy := 0; dy < 4; dy++ {
			for dx := 0; dx < 4; dx++ {
				a := s.art[slot].NRGBAAt(sx+dx, sy+dy)
				b := out.RGBAAt(x+dx, y+dy)
				over := func(v, d byte) byte { return byte((uint32(v)*uint32(a.A) + uint32(d)*uint32(255-a.A) + 127) / 255) }
				out.SetRGBA(x+dx, y+dy, color.RGBA{over(a.R, b.R), over(a.G, b.G), over(a.B, b.B), 255})
			}
		}
		sprites++
		frames[slot]++
		spriteMask[pos>>3] |= 1 << uint(pos&7)
	}
	r["painted"] = counts[0] + counts[1] + sprites
	r["border_painted"] = counts[0]
	r["map_painted"] = counts[1]
	r["sprite_painted"] = sprites
	r["frames"] = frames
	r["picture_mask"] = mask
	r["sprite_mask"] = spriteMask
	r["reason"] = "verified-published-opening"
	return r
}
