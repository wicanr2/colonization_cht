// 規格067 READY：十二世界來源；共用原版觀測，只合成顯示。
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

const hdTerrainBatchStage = uint32(0x3c500)

type hdTerrainBatchDefinition struct {
	ordinal, length, opaque, width, height int
	encoded, writes, asset, assetSHA       string
}
type hdTerrainBatchFrame struct {
	hdTerrainBatchDefinition
	art *image.RGBA
}
type hdTerrainBatchCell struct {
	owned   bool
	ordinal uint16
	k       byte
	native  byte
}
type hdTerrainBatchPair struct {
	cell       hdTerrainBatchCell
	old, value byte
	cursor     int
}
type hdTerrainBatchRuntime struct {
	trace                                                                          bool
	calls, pairs                                                                   []map[string]any
	entry                                                                          map[string]any
	h                                                                              *hdRuntime
	frames                                                                         map[int]*hdTerrainBatchFrame
	current                                                                        *hdTerrainBatchFrame
	before                                                                         [256]byte
	acceptedBy                                                                     map[int]uint64
	cursorRestoresBy                                                               map[int]uint64
	stage, visible                                                                 [64000]hdTerrainBatchCell
	pending                                                                        map[int]hdTerrainBatchPair
	backing                                                                        map[uint32]hdTerrainBatchCell
	bufferSaves, bufferRestores, peakBuffered                                      uint64
	active, outside                                                                bool
	retCS, retIP, sp                                                               uint16
	x, y                                                                           int
	start, revision, accepted, rejected, transferred, cursorPaints, cursorRestores uint64
	writes                                                                         [256]byte
	counts                                                                         [256]uint16
}

func loadHDTerrainBatchRuntime(h *hdRuntime, game, directory string) (*hdTerrainBatchRuntime, error) {
	if h == nil {
		return nil, fmt.Errorf("missing verified HD runtime")
	}
	raw, err := hdReadFile(filepath.Join(game, "PHYS0.SS"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != "deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16" {
		return nil, fmt.Errorf("terrain source mismatch")
	}
	p := &hdTerrainBatchRuntime{h: h, frames: map[int]*hdTerrainBatchFrame{}, acceptedBy: map[int]uint64{}, cursorRestoresBy: map[int]uint64{}, pending: map[int]hdTerrainBatchPair{}, backing: map[uint32]hdTerrainBatchCell{}}
	for _, d := range hdTerrainBatchDefinitions {
		raw, err = hdReadFile(filepath.Join(directory, d.asset), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != d.assetSHA {
			return nil, fmt.Errorf("terrain asset mismatch: %d", d.ordinal)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		if im.Bounds() != image.Rect(0, 0, d.width, d.height) || d.width != d.height {
			return nil, fmt.Errorf("terrain asset shape mismatch")
		}
		f := &hdTerrainBatchFrame{hdTerrainBatchDefinition: d, art: image.NewRGBA(image.Rect(0, 0, 64, 64))}
		for y := 0; y < 64; y++ {
			for x := 0; x < 64; x++ {
				f.art.SetRGBA(x, y, color.RGBAModel.Convert(im.At((2*x+1)*d.width/128, (2*y+1)*d.height/128)).(color.RGBA))
			}
		}
		p.frames[d.ordinal] = f
	}
	if len(p.frames) != 12 {
		return nil, fmt.Errorf("incomplete terrain group")
	}
	return p, nil
}

func (p *hdTerrainBatchRuntime) memoryWrite(addr uint32, old, value byte) {
	if addr >= hdTerrainBatchStage && addr < hdTerrainBatchStage+64000 {
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

func (p *hdTerrainBatchRuntime) copySource(addr uint32, value byte) (hdTerrainBatchCell, int, bool) {
	m := p.h.m
	c := m.CPU
	cs, ip := c.OpAddr()
	if cs != 0xcba || ip != 0xca {
		return hdTerrainBatchCell{}, 0, false
	}
	pc := int(cs)*16 + int(ip)
	if !bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}) {
		return hdTerrainBatchCell{}, 0, false
	}
	delta := int(addr) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
	if delta < 0 || delta >= 2 || int(c.R[golem.SI])+delta >= 65536 || int(c.R[golem.DI])+delta >= 65536 || src < 0 || src >= 0xa0000 || src >= len(m.Mem) || m.Mem[src] != value {
		return hdTerrainBatchCell{}, 0, false
	}
	var cell hdTerrainBatchCell
	switch {
	case src >= int(hdTerrainBatchStage) && src < int(hdTerrainBatchStage)+64000:
		cell = p.stage[src-int(hdTerrainBatchStage)]
	case src >= int(hdBuildingCanvas) && src < int(hdBuildingCanvas)+64000:
		cell = p.visible[src-int(hdBuildingCanvas)]
	default:
		cell = p.backing[uint32(src)]
	}
	return cell, src, cell.owned && cell.native == value
}
func (p *hdTerrainBatchRuntime) beforeInstruction() {
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
	if cs != 0xd46 || ip != 0xa {
		return
	}
	frame, selected := p.frames[int(c.R[golem.AX])-1]
	if !selected {
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
	if !ok || dest[0] != 200 || dest[1] != 320 || uint32(dest[3])*16+uint32(dest[2]) != hdTerrainBatchStage {
		return
	}
	x, y := int(int16(c.R[golem.DX])), int(int16(stack[2]))
	if x < 0 || x+16 > 320 || y < 0 || y+16 > 200 {
		return
	}
	off := uint16(uint32(c.R[golem.AX])*12 + uint32(stack[3]) + 0x36)
	record, ok := hdBuildingWords(m.Mem, stack[4], off, 6)
	if !ok || record[4] != 16 || record[5] != 16 {
		return
	}
	at := int(record[1])*16 + int(record[0])
	if int(record[0])+frame.length > 65536 || at+frame.length > len(m.Mem) || hash(m.Mem[at:at+frame.length]) != frame.encoded {
		p.rejected++
		return
	}
	p.current = frame
	for k := 0; k < 256; k++ {
		p.before[k] = m.Mem[hdTerrainBatchStage+uint32((y+k/16)*320+x+k%16)]
	}
	p.active = true
	p.outside = false
	p.start = m.Steps
	p.x, p.y = x, y
	p.retCS, p.retIP, p.sp = stack[1], stack[0], c.R[golem.SP]
	clear(p.writes[:])
	clear(p.counts[:])
	if p.trace {
		p.entry = map[string]any{"ordinal": frame.ordinal, "entry_step": m.Steps, "registers": c.R, "segments": c.Seg, "stack": stack, "record_far": fmt.Sprintf("%04X:%04X", stack[4], off), "record": record, "source_far": fmt.Sprintf("%04X:%04X", record[1], record[0]), "source_sha256": hash(m.Mem[at : at+frame.length]), "rect": [4]int{x, y, x + 16, y + 16}}
	}
}
func (p *hdTerrainBatchRuntime) stageWrite(addr uint32, old, value byte) {
	i := int(addr - hdTerrainBatchStage)
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
func (p *hdTerrainBatchRuntime) finish() {
	p.active = false
	var encoded []byte
	count := 0
	for k, v := range p.writes {
		actual := p.h.m.Mem[hdTerrainBatchStage+uint32((p.y+k/16)*320+p.x+k%16)]
		if p.counts[k] == 0 {
			if actual != p.before[k] {
				p.rejected++
				return
			}
			continue
		}
		if p.counts[k] != 1 || actual != v {
			p.rejected++
			return
		}
		count++
		encoded = binary.LittleEndian.AppendUint16(encoded, uint16(k))
		encoded = append(encoded, v)
	}
	if p.outside || p.current == nil || count != p.current.opaque || hash(encoded) != p.current.writes {
		p.rejected++
		return
	}
	for k, v := range p.writes {
		if p.counts[k] == 1 {
			p.stage[(p.y+k/16)*320+p.x+k%16] = hdTerrainBatchCell{true, uint16(p.current.ordinal), byte(k), v}
		}
	}
	p.accepted++
	p.acceptedBy[p.current.ordinal]++
	if p.trace {
		if len(p.calls) >= 20000 {
			panic("terrain calls limit")
		}
		p.entry["return_step"] = p.h.m.Steps
		p.entry["writes_sha256"] = hash(encoded)
		p.calls = append(p.calls, p.entry)
		p.entry = nil
	}
}
func (p *hdTerrainBatchRuntime) canvasWrite(addr uint32, old, value byte) {
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
					p.pending[i] = hdTerrainBatchPair{p.visible[i], old, value, k}
					p.visible[i].owned = false
					p.cursorPaints++
					return
				}
				prior, ok := p.pending[i]
				delete(p.pending, i)
				if ok && prior.cursor == k && old == prior.value && value == prior.old {
					p.visible[i] = prior.cell
					p.cursorRestores++
					if prior.cell.owned {
						p.cursorRestoresBy[int(prior.cell.ordinal)]++
					}
					if p.trace && prior.cell.owned {
						if len(p.pairs) >= 200000 {
							panic("地形游標配對超限")
						}
						p.pairs = append(p.pairs, map[string]any{"ordinal": int(prior.cell.ordinal), "step": m.Steps, "linear": addr, "local": int(prior.cell.k), "native": prior.cell.native, "source_cursor_index": k, "paint_old": prior.old, "paint_value": prior.value, "restore_old": old, "restore_value": value, "registers": m.CPU.R, "segments": m.CPU.Seg, "code16": fmt.Sprintf("%x", m.Mem[pc:pc+16])})
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
	if src < int(hdTerrainBatchStage) || src >= int(hdTerrainBatchStage)+64000 {
		p.bufferRestores++
	}
}
func (p *hdTerrainBatchRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	owned, valid, painted := 0, 0, 0
	mask := make([]byte, 8000)
	by := map[int]int{}
	validBy := map[int]int{}
	for i, c := range p.visible {
		if !c.owned {
			continue
		}
		owned++
		if f.canvas[i] != c.native {
			continue
		}
		valid++
		validBy[int(c.ordinal)]++
		frame := p.frames[int(c.ordinal)]
		sx, sy := int(c.k)%16*4, int(c.k)/16*4
		active := false
		for y := 0; y < 4; y++ {
			for x := 0; x < 4; x++ {
				if frame.art.RGBAAt(sx+x, sy+y).A > 0 {
					active = true
				}
			}
		}
		if !active {
			continue
		}
		x, y := i%320*4, i/320*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), frame.art, image.Pt(sx, sy), draw.Over)
		painted++
		by[int(c.ordinal)]++
		mask[i>>3] |= 1 << uint(i&7)
	}
	return map[string]any{"formal": true, "prototype": false, "accepted": p.accepted, "accepted_by_ordinal": p.acceptedBy, "rejected": p.rejected, "owned": owned, "valid": valid, "painted": painted, "by_ordinal": by, "valid_by_ordinal": validBy, "transferred": p.transferred, "cursor_restore_points": p.cursorRestores, "owned_cursor_restores_by_ordinal": p.cursorRestoresBy, "buffer_saves": p.bufferSaves, "buffer_restores": p.bufferRestores, "mask": mask, "revision": p.revision}
}

func (p *hdTerrainBatchRuntime) receipt(f draftNativeFrame) map[string]any {
	return p.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), f)
}
