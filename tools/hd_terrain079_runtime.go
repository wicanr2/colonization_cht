// 規格062 R58 READY：世界079來源；沿既有海洋觀測回呼，只合成顯示。
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

const hdTerrain079Stage = uint32(0x3c500)
const hdTerrain079Encoded = "a8a861754068c86a9c150442f7b07f1fbd297d82b8e5dcb2e3ee108bde4dc84c"
const hdTerrain079Writes = "43e7c310e74049db1a05f0bb8349d79e74ebde3e0a7e95c085624e2808a8d54c"

type hdTerrain079Cell struct {
	owned  bool
	k      byte
	native byte
}
type hdTerrain079Pair struct {
	cell       hdTerrain079Cell
	old, value byte
	cursor     int
}
type hdTerrain079Runtime struct {
	trace                                                                          bool
	calls, pairs                                                                   []map[string]any
	entry                                                                          map[string]any
	h                                                                              *hdRuntime
	art                                                                            *image.RGBA
	stage, visible                                                                 [64000]hdTerrain079Cell
	pending                                                                        map[int]hdTerrain079Pair
	backing                                                                        map[uint32]hdTerrain079Cell
	bufferSaves, bufferRestores, peakBuffered                                      uint64
	active, outside                                                                bool
	retCS, retIP, sp                                                               uint16
	x, y                                                                           int
	start, revision, accepted, rejected, transferred, cursorPaints, cursorRestores uint64
	writes                                                                         [256]byte
	counts                                                                         [256]uint16
}

func loadHDTerrain079Runtime(h *hdRuntime, game, directory string) (*hdTerrain079Runtime, error) {
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
	raw, err = hdReadFile(filepath.Join(directory, "terrain-079.png"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != "081ffb5506aa7aca0e80571053b85f0bdc920cb5e7884cf028521a1dd7ffaa58" {
		return nil, fmt.Errorf("sea HD asset mismatch")
	}
	im, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	if im.Bounds() != image.Rect(0, 0, 1254, 1254) {
		return nil, fmt.Errorf("sea HD asset shape mismatch")
	}
	p := &hdTerrain079Runtime{h: h, art: image.NewRGBA(image.Rect(0, 0, 64, 64)), pending: map[int]hdTerrain079Pair{}, backing: map[uint32]hdTerrain079Cell{}}
	for y := 0; y < 64; y++ {
		for x := 0; x < 64; x++ {
			c := color.RGBAModel.Convert(im.At((2*x+1)*1254/128, (2*y+1)*1254/128)).(color.RGBA)
			if c.A != 255 {
				return nil, fmt.Errorf("sea HD asset must be opaque")
			}
			p.art.SetRGBA(x, y, c)
		}
	}
	return p, nil
}

func (p *hdTerrain079Runtime) memoryWrite(addr uint32, old, value byte) {
	if addr >= hdTerrain079Stage && addr < hdTerrain079Stage+64000 {
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

func (p *hdTerrain079Runtime) copySource(addr uint32, value byte) (hdTerrain079Cell, int, bool) {
	m := p.h.m
	c := m.CPU
	cs, ip := c.OpAddr()
	if cs != 0xcba || ip != 0xca {
		return hdTerrain079Cell{}, 0, false
	}
	pc := int(cs)*16 + int(ip)
	if !bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}) {
		return hdTerrain079Cell{}, 0, false
	}
	delta := int(addr) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
	if delta < 0 || delta >= 2 || int(c.R[golem.SI])+delta >= 65536 || int(c.R[golem.DI])+delta >= 65536 || src < 0 || src >= 0xa0000 || src >= len(m.Mem) || m.Mem[src] != value {
		return hdTerrain079Cell{}, 0, false
	}
	var cell hdTerrain079Cell
	switch {
	case src >= int(hdTerrain079Stage) && src < int(hdTerrain079Stage)+64000:
		cell = p.stage[src-int(hdTerrain079Stage)]
	case src >= int(hdBuildingCanvas) && src < int(hdBuildingCanvas)+64000:
		cell = p.visible[src-int(hdBuildingCanvas)]
	default:
		cell = p.backing[uint32(src)]
	}
	return cell, src, cell.owned && cell.native == value
}
func (p *hdTerrain079Runtime) beforeInstruction() {
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
	if cs != 0xd46 || ip != 0xa || c.R[golem.AX] != 80 {
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
	if !ok || dest[0] != 200 || dest[1] != 320 || uint32(dest[3])*16+uint32(dest[2]) != hdTerrain079Stage {
		return
	}
	x, y := int(int16(c.R[golem.DX])), int(int16(stack[2]))
	if x < 0 || x+16 > 320 || y < 0 || y+16 > 200 {
		return
	}
	off := uint16(80*12 + uint32(stack[3]) + 0x36)
	record, ok := hdBuildingWords(m.Mem, stack[4], off, 6)
	if !ok || record[4] != 16 || record[5] != 16 {
		return
	}
	at := int(record[1])*16 + int(record[0])
	if int(record[0])+285 > 65536 || at+285 > len(m.Mem) || hash(m.Mem[at:at+285]) != hdTerrain079Encoded {
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
	if p.trace {
		p.entry = map[string]any{"ordinal": 79, "entry_step": m.Steps, "registers": c.R, "segments": c.Seg, "stack": stack, "record_far": fmt.Sprintf("%04X:%04X", stack[4], off), "record": record, "source_far": fmt.Sprintf("%04X:%04X", record[1], record[0]), "source_sha256": hash(m.Mem[at : at+285]), "rect": [4]int{x, y, x + 16, y + 16}}
	}
}
func (p *hdTerrain079Runtime) stageWrite(addr uint32, old, value byte) {
	i := int(addr - hdTerrain079Stage)
	p.stage[i].owned = false
	if !p.active {
		return
	}
	x, y := i%320-p.x, i/320-p.y
	if x < 0 || x >= 16 || y < 0 || y >= 16 {
		p.outside = true
		return
	}
	cs, ip := p.h.m.CPU.OpAddr()
	pc := int(cs)*16 + int(ip)
	code, known := hdNineWriterCodes[ip]
	if cs != 0xd46 || !known || !bytes.Equal(p.h.m.Mem[pc:pc+16], code) {
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
func (p *hdTerrain079Runtime) finish() {
	p.active = false
	var encoded []byte
	for k, v := range p.writes {
		if p.counts[k] != 1 || p.h.m.Mem[hdTerrain079Stage+uint32((p.y+k/16)*320+p.x+k%16)] != v {
			p.rejected++
			return
		}
		encoded = binary.LittleEndian.AppendUint16(encoded, uint16(k))
		encoded = append(encoded, v)
	}
	if p.outside || hash(encoded) != hdTerrain079Writes {
		p.rejected++
		return
	}
	for k, v := range p.writes {
		p.stage[(p.y+k/16)*320+p.x+k%16] = hdTerrain079Cell{true, byte(k), v}
	}
	p.accepted++
	if p.trace {
		if len(p.calls) >= 20000 {
			panic("地形來源呼叫超限")
		}
		p.entry["return_step"] = p.h.m.Steps
		p.entry["return_registers"] = p.h.m.CPU.R
		p.entry["return_segments"] = p.h.m.CPU.Seg
		p.entry["return_ip"] = p.h.m.CPU.IP
		p.entry["writes_sha256"] = hash(encoded)
		p.calls = append(p.calls, p.entry)
		p.entry = nil
	}
}
func (p *hdTerrain079Runtime) canvasWrite(addr uint32, old, value byte) {
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
					p.pending[i] = hdTerrain079Pair{p.visible[i], old, value, k}
					p.visible[i].owned = false
					p.cursorPaints++
					return
				}
				prior, ok := p.pending[i]
				delete(p.pending, i)
				if ok && prior.cursor == k && old == prior.value && value == prior.old {
					p.visible[i] = prior.cell
					p.cursorRestores++
					if p.trace && prior.cell.owned {
						if len(p.pairs) >= 200000 {
							panic("地形游標配對超限")
						}
						p.pairs = append(p.pairs, map[string]any{"ordinal": 79, "step": m.Steps, "linear": addr, "local": int(prior.cell.k), "native": prior.cell.native, "source_cursor_index": k, "paint_old": prior.old, "paint_value": prior.value, "restore_old": old, "restore_value": value, "registers": m.CPU.R, "segments": m.CPU.Seg, "code16": fmt.Sprintf("%x", m.Mem[pc:pc+16])})
					}
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
	if src < int(hdTerrain079Stage) || src >= int(hdTerrain079Stage)+64000 {
		p.bufferRestores++
	}
}
func (p *hdTerrain079Runtime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
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
	return map[string]any{"formal": true, "asset": "terrain-079", "accepted": p.accepted, "rejected": p.rejected, "owned": owned, "painted": painted, "transferred": p.transferred, "cursor_paint_points": p.cursorPaints, "cursor_restore_points": p.cursorRestores, "buffer_saves": p.bufferSaves, "buffer_restores": p.bufferRestores, "buffered": len(p.backing), "peak_buffered": p.peakBuffered, "mask": mask, "pending": len(p.pending), "revision": p.revision}
}

func (p *hdTerrain079Runtime) receipt(f draftNativeFrame) map[string]any {
	return p.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), f)
}
