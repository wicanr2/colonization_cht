// 規格069 R90 READY：單一國王與獵犬的完整來源與顯示層，不寫入DOS。
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

const hdRoyalEncodedSHA = "096034463bc78340a4e7b16a8809e1deae9e6cf42aa58e8375875e86f6185769"
const hdRoyalNativeSHA = "946f5f2d30ae8d5402e763a9d0393bfcfd4448e2d9edf2321e9b7f904ef18a60"
const hdRoyalWritesSHA = "5705f430fc8c5474a6f259d96c38e49d52a4a8d03adef567888f432036bda128"
const hdRoyalArtSHA = "c703753a240057c7379a4c192e3d97349d45ef5d12a8e27beddd1bf1468e504b"

type hdRoyalCell struct {
	serial uint32
	local  uint16
	value  byte
}
type hdRoyalPair struct {
	old, value byte
	k          int
	cell       hdRoyalCell
}
type hdRoyalRuntime struct {
	h                                                                  *hdRuntime
	art                                                                *image.NRGBA
	stage, main, published                                             [64000]hdRoyalCell
	pending, publishedPending                                          map[int]hdRoyalPair
	before                                                             []byte
	prior                                                              [64000]hdSceneCell
	source                                                             [35343]byte
	counts                                                             [35343]uint16
	active, ready, bad, blocked                                        bool
	sp, retCS, retIP, sourceDS                                         uint16
	sourceOffset                                                       int
	start                                                              uint64
	serial                                                             uint32
	writes, accepted, rejected, revision, cursorPaints, cursorRestores uint64
}

func loadHDRoyalRuntime(h *hdRuntime, game, directory string) (*hdRoyalRuntime, error) {
	for name, want := range map[string]string{"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3", "KING1.SS": "bfdcb69af1376dc4334d7822121a55c112e19cc473b6a11cc9c6ff599b9c9e7f"} {
		raw, e := hdReadFile(filepath.Join(game, name), 8<<20)
		if e != nil {
			return nil, e
		}
		if hash(raw) != want {
			return nil, fmt.Errorf("royal original %s", name)
		}
	}
	raw, e := hdReadFile(filepath.Join(directory, "king1-000.png"), 8<<20)
	if e != nil {
		return nil, e
	}
	if hash(raw) != hdRoyalArtSHA {
		return nil, fmt.Errorf("royal art")
	}
	art, e := png.Decode(bytes.NewReader(raw))
	if e != nil {
		return nil, e
	}
	if art.Bounds() != image.Rect(0, 0, 1254, 1254) {
		return nil, fmt.Errorf("royal geometry")
	}
	p := &hdRoyalRuntime{h: h, art: image.NewNRGBA(image.Rect(0, 0, 756, 748)), pending: map[int]hdRoyalPair{}, publishedPending: map[int]hdRoyalPair{}}
	for y := 0; y < 748; y++ {
		for x := 0; x < 756; x++ {
			p.art.SetNRGBA(x, y, color.NRGBAModel.Convert(art.At((2*x+1)*1254/(2*756), (2*y+1)*1254/(2*748))).(color.NRGBA))
		}
	}
	for _, base := range []uint32{0x3c500, hdBuildingCanvas, 0xa0000} {
		h.m.WatchWrite(base, base+63999, func(_ *golem.Machine, a uint32, o, v byte) { p.write(a, o, v) })
	}
	return p, nil
}
func (p *hdRoyalRuntime) beforeInstruction() {
	if p == nil || p.blocked {
		return
	}
	m, c := p.h.m, p.h.m.CPU
	if p.active {
		if c.Seg[golem.CS] == p.retCS && c.IP == p.retIP && c.R[golem.SP] == p.sp+12 {
			p.finish()
		} else if m.Steps-p.start > 2000000 {
			p.active = false
			p.rejected++
		}
	}
	if p.active || c.Seg[golem.CS] != 0xd66 || c.IP != 4 || c.R[golem.AX] != 1 {
		return
	}
	pc := int(c.Seg[golem.CS])*16 + int(c.IP)
	if !bytes.Equal(m.Mem[pc:pc+12], []byte{0xc8, 0x6e, 1, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	st, ok := hdBuildingWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], 6)
	if !ok {
		return
	}
	if int(st[4])+0x36+12+12 > 65536 {
		return
	}
	rec, ok := hdBuildingWords(m.Mem, st[5], st[4]+0x36+12, 6)
	if !ok {
		return
	}
	if rec[4] != 189 || rec[5] != 187 || rec[2] != 94 || rec[3] != 198 {
		return
	}
	src := int(rec[1])*16 + int(rec[0])
	if int(rec[0])+12207 > 65536 || src+12207 > len(m.Mem) || hash(m.Mem[src:src+12207]) != hdRoyalEncodedSHA {
		return
	}
	desc, ok := hdBuildingWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok {
		return
	}
	if st[2] != 100 || st[3] != 198 || c.R[golem.DX] != 94 || desc[0] != 200 || desc[1] != 320 || desc[2] != 0 || desc[3] != 0x3c50 || p.h.scenes == nil {
		p.rejected++
		return
	}
	p.serial++
	if p.serial == 0 {
		p.blocked = true
		return
	}
	p.ready = false
	p.active, p.bad = true, false
	p.start, p.sp, p.retCS, p.retIP = m.Steps, c.R[golem.SP], st[1], st[0]
	p.sourceDS, p.sourceOffset = rec[1], int(rec[0])
	p.writes = 0
	p.counts = [35343]uint16{}
	for i := range p.source {
		p.source[i] = 253
	}
	p.before = bytes.Clone(m.Mem[0x3c500 : 0x3c500+64000])
	p.prior = p.h.scenes.stage
}
func (p *hdRoyalRuntime) finish() {
	p.active = false
	p.ready = false
	triples := make([]byte, 0, 11930*3)
	current := p.h.m.Mem[0x3c500 : 0x3c500+64000]
	expected := bytes.Clone(p.before)
	for local, n := range p.counts {
		if n == 0 {
			continue
		}
		if n != 1 {
			p.bad = true
		}
		triples = binary.LittleEndian.AppendUint16(triples, uint16(local))
		triples = append(triples, p.source[local])
		expected[(local/189+12)*320+local%189] = p.source[local]
	}
	if p.bad || len(triples) != 11930*3 || hash(triples) != hdRoyalWritesSHA || hash(p.source[:]) != hdRoyalNativeSHA || !bytes.Equal(expected, current) {
		p.rejected++
		return
	}
	p.ready = true
	for local, n := range p.counts {
		if n == 1 {
			pos := (local/189+12)*320 + local%189
			p.stage[pos] = hdRoyalCell{p.serial, uint16(local), p.source[local]}
		}
	}
	p.accepted++
	p.revision++
}
func (p *hdRoyalRuntime) write(a uint32, old, v byte) {
	if p == nil || p.blocked {
		return
	}
	m, c := p.h.m, p.h.m.CPU
	cs, ip := c.OpAddr()
	pc := int(cs)*16 + int(ip)
	known := func(code []byte) bool {
		return pc >= 0 && pc+len(code) <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+len(code)], code)
	}
	if a >= 0x3c500 && a < 0x3c500+64000 {
		pos := int(a - 0x3c500)
		p.stage[pos] = hdRoyalCell{}
		p.revision++
		if !p.active {
			return
		}
		codes := map[uint16][]byte{0x29e: {0x26, 0x88, 7, 3, 0x5e, 0xf0, 0x42, 0x47, 0xeb, 0x96, 0x5a, 0x5b, 0x5f, 3, 0x5e, 0xfe}, 0x272: {0x26, 0x88, 7, 3, 0x5e, 0xf0, 0x42, 0x47, 0xfe, 0xcc, 0x74, 2, 0xeb, 0xd8, 0xeb, 0xbc}}
		x, y := pos%320, pos/320-12
		if cs != 0xd66 || len(codes[ip]) != 16 || !known(codes[ip]) || a != uint32(c.Seg[golem.ES])*16+uint32(c.R[golem.BX]) || c.Seg[golem.DS] != p.sourceDS || int(c.R[golem.SI]) < p.sourceOffset || int(c.R[golem.SI]) > p.sourceOffset+12207 || x < 0 || x >= 189 || y < 0 || y >= 187 || v == 253 {
			p.bad = true
			return
		}
		local := y*189 + x
		if p.writes == 0 && local != 102 {
			p.bad = true
		}
		p.counts[local]++
		p.source[local] = v
		p.writes++
		return
	}
	dest := uint32(hdBuildingCanvas)
	cells := &p.main
	pending := p.pending
	if a >= 0xa0000 && a < 0xa0000+64000 {
		dest = 0xa0000
		cells = &p.published
		pending = p.publishedPending
	} else if a < dest || a >= dest+64000 {
		return
	}
	pos := int(a - dest)
	prior := cells[pos]
	cells[pos] = hdRoyalCell{}
	pair, paired := pending[pos]
	delete(pending, pos)
	p.revision++
	delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	off := int(c.R[golem.SI]) + delta
	src := int(c.Seg[golem.DS])*16 + off
	if cs == 0xb68 && ip == 0x51c && c.Seg[golem.DS] == 0xa000 && uint32(c.Seg[golem.ES])*16 == dest && delta == 0 && off >= 0xfa00 && off < 0xfc00 && known([]byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}) {
		if source, yes := p.h.cursorSource(); yes && m.Mem[0xa0000+off] == v {
			k := off & 255
			back, composed := m.Mem[0xafa00+k], m.Mem[0xafb00+k]
			if off >= 0xfb00 && back == old && composed == v && (source[k] == 255 && v == back || source[k] != 255 && v == source[k]) {
				if source[k] == 255 && old == v && prior.serial != 0 && prior.value == v {
					cells[pos] = prior
				} else if source[k] != 255 && prior.serial != 0 && prior.value == old {
					pending[pos] = hdRoyalPair{old, v, k, prior}
					p.cursorPaints++
				}
			} else if off < 0xfb00 && back == v {
				if source[k] == 255 && composed == old && old == v && prior.serial != 0 && prior.value == v {
					cells[pos] = prior
				} else if paired && pair.old == v && pair.value == old && pair.k == k && composed == old && source[k] == old {
					cells[pos] = pair.cell
					p.cursorRestores++
				}
			}
			if len(pending) > 256 {
				p.blocked = true
				clear(cells[:])
				clear(pending)
			}
			return
		}
	}
	if dest == hdBuildingCanvas {
		clear(p.pending)
	}
	word := []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}
	if delta < 0 || delta > 1 || off >= 65536 || int(c.R[golem.DI])+delta >= 65536 || src < 0 || src >= len(m.Mem) || m.Mem[src] != v || !known(word) {
		return
	}
	var got hdRoyalCell
	if dest == hdBuildingCanvas && cs == 0xc9f && ip == 0xca && src == 0x3c500+pos {
		got = p.stage[pos]
	}
	if dest == 0xa0000 && cs == 0xe21 && ip == 0x91 && c.Seg[golem.ES] == 0xa000 && int(c.R[golem.DI])+delta < 64000 && src == int(hdBuildingCanvas)+pos {
		got = p.main[pos]
	}
	if got.serial != 0 && got.value == v {
		cells[pos] = got
	}
}
func (p *hdRoyalRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	result := map[string]any{"prototype": false, "formal": true, "accepted": p.accepted, "rejected": p.rejected, "painted": 0, "source_cells": 0}
	if p.active || !p.ready || p.blocked || p.serial == 0 || len(f.canvas) != 64000 || len(f.indexed) != 64000 || len(f.palette) != 768 || f.mode != 0x13 || !bytes.Equal(p.h.m.Mem[0xa0000:0xa0000+64000], f.indexed) {
		result["reason"] = "shape-or-no-source"
		return result
	}
	used := [256]bool{}
	for _, v := range p.source {
		if v != 253 {
			used[v] = true
		}
	}
	projection := []byte{}
	for k, yes := range used {
		if yes {
			projection = append(projection, byte(k))
			projection = append(projection, f.palette[k*3:k*3+3]...)
		}
	}
	if hash(projection) != "40d165ed8880e61530a6a2ab50280ce40eb58ffbe9d3469bc550e885eb488f59" {
		result["reason"] = "unsupported-palette"
		return result
	}
	source, reason := p.h.cursorPixelsProof(f)
	cursor := reason == ""
	isCursor := func(pos int) bool {
		return cursor && image.Pt(pos%320, pos/320).In(f.cursor) && source[(pos/320-f.cursor.Min.Y)*16+pos%320-f.cursor.Min.X] != 255
	}
	for local, v := range p.source {
		if v == 253 {
			continue
		}
		pos := (local/189+12)*320 + local%189
		c := p.published[pos]
		if isCursor(pos) {
			pair, yes := p.publishedPending[pos]
			if !yes || pair.cell.serial != p.serial || pair.k != (pos/320-f.cursor.Min.Y)*16+pos%320-f.cursor.Min.X || pair.old != v || pair.value != f.indexed[pos] {
				result["reason"] = "unverified-cursor-pair"
				return result
			}
			c = pair.cell
		} else if f.indexed[pos] != v {
			result["reason"] = "changed-foreground"
			return result
		}
		if c.serial != p.serial || int(c.local) != local || c.value != v {
			result["reason"] = "incomplete-current-pose"
			return result
		}
	}
	old := 0
	nativeFallback := 0
	painted := 0
	mask := make([]byte, 8000)
	for local, v := range p.source {
		pos := (local/189+12)*320 + local%189
		if isCursor(pos) {
			continue
		}
		before := p.prior[pos]
		frame, known := p.h.scenes.frame(before)
		known = known && frame.id == 1002 && !before.glyph && before.value == p.before[pos] && int(before.local) == pos && frame.native[before.local] == p.before[pos] && frame.paletteSupported(f.palette)
		if v == 253 {
			current := p.h.scenes.published[pos]
			if !known || current != before || f.indexed[pos] != p.before[pos] {
				continue
			}
		} else {
			if known {
				draw.Draw(out, image.Rect(pos%320*4, pos/320*4, pos%320*4+4, pos/320*4+4), frame.art, image.Pt(int(before.local)%320*4, int(before.local)/320*4), draw.Src)
				old++
			} else {
				draftPaintPixel(out, pos, p.before[pos], f.palette)
				nativeFallback++
			}
		}
		for dy := 0; dy < 4; dy++ {
			for dx := 0; dx < 4; dx++ {
				c := p.art.NRGBAAt(local%189*4+dx, local/189*4+dy)
				if c.A == 0 {
					continue
				}
				x, y := pos%320*4+dx, pos/320*4+dy
				prior := out.RGBAAt(x, y)
				a := uint32(c.A)
				blend := func(s, d byte) byte { return byte((uint32(s)*a + uint32(d)*(255-a) + 127) / 255) }
				out.SetRGBA(x, y, color.RGBA{blend(c.R, prior.R), blend(c.G, prior.G), blend(c.B, prior.B), 255})
				painted++
			}
		}
		mask[pos>>3] |= 1 << uint(pos&7)
	}
	result["painted"] = painted
	result["source_cells"] = 11930
	result["typed_background_restored"] = old
	result["native_underlay_restored"] = nativeFallback
	result["mask"] = mask
	result["reason"] = "complete-current-pose"
	result["cursor_reason"] = reason
	result["cursor_paints"] = p.cursorPaints
	result["cursor_restores"] = p.cursorRestores
	return result
}
