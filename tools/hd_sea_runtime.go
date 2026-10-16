// 規格062 READY：已驗海洋來源與背景還原；只合成顯示，不寫入DOS。
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"path/filepath"

	golem "github.com/wicanr2/dosgolem"
)

const hdSeaStage = uint32(0x3c500)
const hdSeaEncoded = "192698d118f87f0f0c4f1605962c000a63db80c935510cef2b4087bf2bd8399f"
const hdSeaWrites = "f81941f19ff0b50933f8520099d8e8c74b2a1d31563521c53df5e7eeb0736da3"

type hdSeaCell struct {
	owned  bool
	k      byte
	native byte
}
type hdSeaPair struct {
	cell       hdSeaCell
	old, value byte
	cursor     int
}
type hdSeaRuntime struct {
	h                                                                              *hdRuntime
	art                                                                            *image.RGBA
	stage, visible                                                                 [64000]hdSeaCell
	pending                                                                        map[int]hdSeaPair
	backing                                                                        map[uint32]hdSeaCell
	bufferSaves, bufferRestores, peakBuffered                                      uint64
	active, outside                                                                bool
	retCS, retIP, sp                                                               uint16
	x, y                                                                           int
	start, revision, accepted, rejected, transferred, cursorPaints, cursorRestores uint64
	writes                                                                         [256]byte
	counts                                                                         [256]uint16
}

func loadHDSeaRuntime(h *hdRuntime, game, directory string) (*hdSeaRuntime, error) {
	if h == nil {
		return nil, fmt.Errorf("sea HD requires verified building HD runtime")
	}
	raw, err := hdReadFile(filepath.Join(game, "PHYS0.SS"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != "deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16" {
		return nil, fmt.Errorf("sea source file mismatch")
	}
	raw, err = hdReadFile(filepath.Join(directory, "sea-148.png"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != "2c5d3edc8d38e44dc02d7ccb88e79e4f749edd8a0b1d3dfd54ec04b467ba61ff" {
		return nil, fmt.Errorf("sea HD asset mismatch")
	}
	im, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	if im.Bounds() != image.Rect(0, 0, 1254, 1254) {
		return nil, fmt.Errorf("sea HD asset shape mismatch")
	}
	p := &hdSeaRuntime{h: h, art: image.NewRGBA(image.Rect(0, 0, 64, 64)), pending: map[int]hdSeaPair{}, backing: map[uint32]hdSeaCell{}}
	for y := 0; y < 64; y++ {
		for x := 0; x < 64; x++ {
			c := color.RGBAModel.Convert(im.At((2*x+1)*1254/128, (2*y+1)*1254/128)).(color.RGBA)
			if c.A != 255 {
				return nil, fmt.Errorf("sea HD asset must be opaque")
			}
			p.art.SetRGBA(x, y, c)
		}
	}
	h.m.WatchWrite(0, uint32(len(h.m.Mem)-1), func(_ *golem.Machine, a uint32, old, value byte) {
		p.memoryWrite(a, old, value)
		if h.terrain079 != nil {
			h.terrain079.memoryWrite(a, old, value)
		}
		if h.terrainBatch != nil {
			h.terrainBatch.memoryWrite(a, old, value)
		}
		if h.smallTerrain != nil {
			h.smallTerrain.memoryWrite(a, old, value)
		}
		h.worldTexture.memoryWrite(a, old, value)
		h.parch.memoryWrite(a, old, value)
		if h.texture != nil {
			h.texture.memoryWrite(a, old, value)
		}
	})
	return p, nil
}

// RAM地址不是來源鍵。只有實際已驗複製可保存身分，每次其他寫入都撤銷。
func (p *hdSeaRuntime) memoryWrite(addr uint32, old, value byte) {
	if addr >= hdSeaStage && addr < hdSeaStage+64000 {
		p.stageWrite(addr, old, value)
		return
	}
	if addr >= hdBuildingCanvas && addr < hdBuildingCanvas+64000 {
		p.canvasWrite(addr, old, value)
		return
	}
	if p.accepted == 0 || addr >= 0xa0000 {
		return
	}
	cell, src, ok := p.copySource(addr, value)
	delete(p.backing, addr)
	if !ok || src < int(hdBuildingCanvas) || src >= int(hdBuildingCanvas)+64000 {
		return
	}
	p.backing[addr] = cell
	p.bufferSaves++
	if uint64(len(p.backing)) > p.peakBuffered {
		p.peakBuffered = uint64(len(p.backing))
	}
}

func (p *hdSeaRuntime) copySource(addr uint32, value byte) (hdSeaCell, int, bool) {
	m := p.h.m
	c := m.CPU
	cs, ip := c.OpAddr()
	if cs != 0xcba || ip != 0xca {
		return hdSeaCell{}, 0, false
	}
	pc := int(cs)*16 + int(ip)
	if !bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}) {
		return hdSeaCell{}, 0, false
	}
	delta := int(addr) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
	if delta < 0 || delta >= 2 || int(c.R[golem.SI])+delta >= 65536 || int(c.R[golem.DI])+delta >= 65536 || src < 0 || src >= 0xa0000 || src >= len(m.Mem) || m.Mem[src] != value {
		return hdSeaCell{}, 0, false
	}
	var cell hdSeaCell
	switch {
	case src >= int(hdSeaStage) && src < int(hdSeaStage)+64000:
		cell = p.stage[src-int(hdSeaStage)]
	case src >= int(hdBuildingCanvas) && src < int(hdBuildingCanvas)+64000:
		cell = p.visible[src-int(hdBuildingCanvas)]
	default:
		cell = p.backing[uint32(src)]
	}
	return cell, src, cell.owned && cell.native == value
}
func (p *hdSeaRuntime) beforeInstruction() {
	if p == nil {
		return
	}
	m := p.h.m
	c := m.CPU
	cs, ip := c.Seg[golem.CS], c.IP
	if p.active && cs == p.retCS && ip == p.retIP && c.R[golem.SP] == p.sp+10 {
		p.finish()
	}
	if p.active && (m.Steps-p.start > 100000 || (cs == 0xd46 && ip == 0xa)) {
		p.active = false
		p.rejected++
	}
	if cs != 0xd46 || ip != 0xa || c.R[golem.AX] != 149 {
		return
	}
	pc := int(cs)*16 + int(ip)
	if !bytes.Equal(m.Mem[pc:pc+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	stack, ok := hdBuildingWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	if !ok {
		return
	}
	dest, ok := hdBuildingWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok || dest[0] != 200 || dest[1] != 320 || uint32(dest[3])*16+uint32(dest[2]) != hdSeaStage {
		return
	}
	x, y := int(int16(c.R[golem.DX])), int(int16(stack[2]))
	if x < 0 || x+16 > 320 || y < 0 || y+16 > 200 {
		return
	}
	off := uint16(149*12 + uint32(stack[3]) + 0x36)
	record, ok := hdBuildingWords(m.Mem, stack[4], off, 6)
	if !ok || record[4] != 16 || record[5] != 16 {
		return
	}
	at := int(record[1])*16 + int(record[0])
	if int(record[0])+263 > 65536 || at+263 > len(m.Mem) || hash(m.Mem[at:at+263]) != hdSeaEncoded {
		p.rejected++
		return
	}
	p.active = true
	p.outside = false
	p.start = m.Steps
	p.x, p.y = x, y
	p.retCS, p.retIP, p.sp = stack[1], stack[0], c.R[golem.SP]
	clear(p.writes[:])
	clear(p.counts[:])
}
func (p *hdSeaRuntime) stageWrite(addr uint32, old, value byte) {
	i := int(addr - hdSeaStage)
	p.stage[i].owned = false
	if !p.active {
		return
	}
	x, y := i%320-p.x, i/320-p.y
	if x < 0 || x >= 16 || y < 0 || y >= 16 {
		p.outside = true
		return
	}
	k := y*16 + x
	if p.counts[k] == 65535 {
		p.outside = true
		return
	}
	p.counts[k]++
	p.writes[k] = value
}
func (p *hdSeaRuntime) finish() {
	p.active = false
	var encoded []byte
	for k, v := range p.writes {
		if p.counts[k] != 1 || p.h.m.Mem[hdSeaStage+uint32((p.y+k/16)*320+p.x+k%16)] != v {
			p.rejected++
			return
		}
		encoded = binary.LittleEndian.AppendUint16(encoded, uint16(k))
		encoded = append(encoded, v)
	}
	if p.outside || hash(encoded) != hdSeaWrites {
		p.rejected++
		return
	}
	for k, v := range p.writes {
		p.stage[(p.y+k/16)*320+p.x+k%16] = hdSeaCell{true, byte(k), v}
	}
	p.accepted++
}
func (p *hdSeaRuntime) canvasWrite(addr uint32, old, value byte) {
	m := p.h.m
	i := int(addr - hdBuildingCanvas)
	p.revision++
	cs, ip := m.CPU.OpAddr()
	if cs == 0xb68 && ip == 0x51c && m.CPU.Seg[golem.DS] == 0xa000 && m.CPU.Seg[golem.ES] == 0x2cae {
		pc := int(cs)*16 + int(ip)
		if bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}) {
			dest := int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI])
			src := int(m.CPU.R[golem.SI]) + int(addr) - dest
			if _, ok := p.h.cursorSource(); ok && src >= 0xfa00 && src < 0xfc00 && m.Mem[0xa0000+src] == value {
				k := src & 255
				if src >= 0xfb00 {
					p.pending[i] = hdSeaPair{p.visible[i], old, value, k}
					p.visible[i].owned = false
					p.cursorPaints++
					return
				}
				prior, ok := p.pending[i]
				delete(p.pending, i)
				if ok && prior.cursor == k && old == prior.value && value == prior.old {
					p.visible[i] = prior.cell
					p.cursorRestores++
					return
				}
			}
		}
	}
	p.visible[i].owned = false
	clear(p.pending)
	cell, src, ok := p.copySource(addr, value)
	if !ok || (src >= int(hdBuildingCanvas) && src < int(hdBuildingCanvas)+64000) {
		return
	}
	p.visible[i] = cell
	p.transferred++
	if src < int(hdSeaStage) || src >= int(hdSeaStage)+64000 {
		p.bufferRestores++
	}
}
func (p *hdSeaRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	owned, painted := 0, 0
	mask := make([]byte, 8000)
	for i, c := range p.visible {
		if !c.owned {
			continue
		}
		owned++
		if f.canvas[i] != c.native {
			continue
		}
		x, y := i%320*4, i/320*4
		sx, sy := int(c.k)%16*4, int(c.k)/16*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), p.art, image.Pt(sx, sy), draw.Src)
		painted++
		mask[i>>3] |= 1 << uint(i&7)
	}
	return map[string]any{"formal": true, "asset": "sea-148", "accepted": p.accepted, "rejected": p.rejected, "owned": owned, "painted": painted, "transferred": p.transferred, "cursor_paint_points": p.cursorPaints, "cursor_restore_points": p.cursorRestores, "buffer_saves": p.bufferSaves, "buffer_restores": p.bufferRestores, "buffered": len(p.backing), "peak_buffered": p.peakBuffered, "mask": mask, "pending": len(p.pending), "revision": p.revision}
}
