// 規格064 R44 DRAFT：中央來源隔離顯示。正式組裝不得引用。
// 只觀測原版寫入及合成四倍畫布，不寫入DOS。
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/draw"
	"image/png"
	"path/filepath"
)

type hdCenterFrame struct {
	ordinal, w, h, encodedLen, opaque    int
	encodedSHA, writesSHA, artSHA, file  string
	artW, artH                           int
	sample, content                      [4]int
	writers                              uint8
	art                                  *image.RGBA
	accepted, rejected, paints, restores uint64
}

var hdCenterFrames = []hdCenterFrame{
	{ordinal: 9, w: 53, h: 37, encodedLen: 1254, opaque: 1095, encodedSHA: "8900416036b739238f3d36ef0bd6de7c64cc92e2273658c866e233a328380d8c", writesSHA: "80e2c7b872906ce4fc27a12926b6a9be2a77c90f75c509f0524346254781f0d6", artSHA: "bc7057fa60db21a120f3d2fd81d59f7ae77cfa56ac351aa6df9d455f7bac29b6", file: "building-009-candidate-v1.png", artW: 1500, artH: 1049, sample: [4]int{9, 57, 1490, 1004}, content: [4]int{0, 0, 53, 36}, writers: 6},
}
var hdCenterWriterCodes = map[uint16][]byte{
	0x181: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xe7, 0xeb, 0xd0, 0x3b},
	0x1b4: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x03, 0xeb, 0xe7, 0x90, 0xeb, 0xcc},
	0x1d2: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xeb, 0xb5, 0x90, 0x5a, 0x5b, 0x03, 0x5e, 0xfe, 0x79},
}

type hdCenterCell struct {
	owned  bool
	local  uint16
	native byte
	slot   uint8
}
type hdCenterPending struct {
	cell       hdCenterCell
	old, value byte
	cursor     int
}
type hdCenterPrototype struct {
	h                                   *hdRuntime
	frames                              []hdCenterFrame
	visible                             [64000]hdCenterCell
	pending                             map[int]hdCenterPending
	active, outside                     bool
	selected                            int
	x, y                                int
	sp, retCS, retIP                    uint16
	start, revision, accepted, rejected uint64
	writes                              [3600]byte
	counts                              [3600]uint16
	trace                               bool
	calls, pairs                        []map[string]any
	entry                               map[string]any
}

func hdCenterRead(path, want string, limit int64) ([]byte, error) {
	raw, err := hdReadFile(path, limit)
	if err != nil {
		return nil, err
	}
	if hash(raw) != want {
		return nil, fmt.Errorf("中央來源指紋不同：%s", path)
	}
	return raw, nil
}
func loadHDCenterPrototype(h *hdRuntime, game, directory string) (*hdCenterPrototype, error) {
	if h == nil || directory == "" {
		return nil, fmt.Errorf("中央來源原型需要既有HD及素材目錄")
	}
	if _, err := hdCenterRead(filepath.Join(game, "BUILDING.SS"), hdBuildingFileSHA, 8<<20); err != nil {
		return nil, err
	}
	p := &hdCenterPrototype{h: h, frames: append([]hdCenterFrame(nil), hdCenterFrames...), pending: map[int]hdCenterPending{}}
	for i := range p.frames {
		f := &p.frames[i]
		raw, err := hdCenterRead(filepath.Join(directory, f.file), f.artSHA, 8<<20)
		if err != nil {
			return nil, err
		}
		c, err := png.DecodeConfig(bytes.NewReader(raw))
		if err != nil || c.Width != f.artW || c.Height != f.artH {
			return nil, fmt.Errorf("中央來源原圖尺寸不同：%d", f.ordinal)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		a, b := f.sample, f.content
		if a[0] < 0 || a[1] < 0 || a[2] <= a[0] || a[3] <= a[1] || a[2] > f.artW || a[3] > f.artH || b[0] < 0 || b[1] < 0 || b[2] <= b[0] || b[3] <= b[1] || b[2] > f.w || b[3] > f.h {
			return nil, fmt.Errorf("中央來源取樣邊界不同：%d", f.ordinal)
		}
		f.art = image.NewRGBA(image.Rect(0, 0, f.w*4, f.h*4))
		for y := b[1] * 4; y < b[3]*4; y++ {
			for x := b[0] * 4; x < b[2]*4; x++ {
				sx := a[0] + (2*(x-b[0]*4)+1)*(a[2]-a[0])/((b[2]-b[0])*8)
				sy := a[1] + (2*(y-b[1]*4)+1)*(a[3]-a[1])/((b[3]-b[1])*8)
				f.art.Set(x, y, im.At(sx, sy))
			}
		}
	}
	h.m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, o, v byte) { p.write(a, o, v) })
	return p, nil
}
func (p *hdCenterPrototype) beforeInstruction() {
	if p == nil {
		return
	}
	m := p.h.m
	c := m.CPU
	if p.active {
		if c.Seg[golem.CS] == p.retCS && c.IP == p.retIP && c.R[golem.SP] == p.sp+10 {
			p.finish()
		} else if m.Steps-p.start > 100000 {
			p.active = false
			p.rejected++
			p.frames[p.selected].rejected++
		}
	}
	if c.Seg[golem.CS] != 0xd46 || c.IP != 0xa || p.active {
		return
	}
	pc := int(c.Seg[golem.CS])*16 + int(c.IP)
	if !bytes.Equal(m.Mem[pc:pc+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	slot := -1
	for i, f := range p.frames {
		if c.R[golem.AX] == uint16(f.ordinal+1) {
			slot = i
			break
		}
	}
	if slot < 0 {
		return
	}
	f := &p.frames[slot]
	stack := int(c.Seg[golem.SS])*16 + int(c.R[golem.SP])
	if stack+10 > len(m.Mem) {
		return
	}
	words := [5]uint16{}
	for i := range words {
		words[i] = binary.LittleEndian.Uint16(m.Mem[stack+i*2:])
	}
	off := uint16((c.R[golem.AX]&0x7fff)*12 + words[3] + 0x36)
	at := int(words[4])*16 + int(off)
	if at+12 > len(m.Mem) {
		return
	}
	record := [6]uint16{}
	for i := range record {
		record[i] = binary.LittleEndian.Uint16(m.Mem[at+i*2:])
	}
	source := int(record[1])*16 + int(record[0])
	if source+f.encodedLen > len(m.Mem) || hash(m.Mem[source:source+f.encodedLen]) != f.encodedSHA {
		return
	}
	descriptor := int(c.Seg[golem.DS])*16 + int(c.R[golem.BX])
	if descriptor+8 > len(m.Mem) {
		return
	}
	d := [4]uint16{}
	for i := range d {
		d[i] = binary.LittleEndian.Uint16(m.Mem[descriptor+i*2:])
	}
	x, y := int(int16(c.R[golem.DX])), int(int16(words[2]))
	if d != [4]uint16{200, 320, 0, 0x2cae} || int(record[4]) != f.w || int(record[5]) != f.h || x < 0 || x+f.w > 320 || y < 0 || y+f.h > 200 {
		p.rejected++
		f.rejected++
		return
	}
	p.selected, p.active, p.outside, p.x, p.y = slot, true, false, x, y
	p.start, p.sp, p.retCS, p.retIP = m.Steps, c.R[golem.SP], words[1], words[0]
	p.writes, p.counts = [3600]byte{}, [3600]uint16{}
	if p.trace {
		p.entry = map[string]any{"ordinal": f.ordinal, "entry_step": m.Steps, "registers": c.R, "segments": c.Seg, "stack": words, "record_far": fmt.Sprintf("%04X:%04X", words[4], off), "record": record, "source_far": fmt.Sprintf("%04X:%04X", record[1], record[0]), "source_sha256": hash(m.Mem[source : source+f.encodedLen]), "rect": [4]int{x, y, x + f.w, y + f.h}}
	}
}
func (p *hdCenterPrototype) finish() {
	p.active = false
	f := &p.frames[p.selected]
	var encoded []byte
	for k, n := range p.counts[:f.w*f.h] {
		if n == 0 {
			continue
		}
		if n != 1 {
			p.outside = true
		}
		encoded = binary.LittleEndian.AppendUint16(encoded, uint16(k))
		encoded = append(encoded, p.writes[k])
	}
	if p.outside || len(encoded) != f.opaque*3 || hash(encoded) != f.writesSHA {
		p.rejected++
		f.rejected++
		return
	}
	for k, n := range p.counts[:f.w*f.h] {
		if n == 1 {
			i := (p.y+k/f.w)*320 + p.x + k%f.w
			p.visible[i] = hdCenterCell{true, uint16(k), p.writes[k], uint8(p.selected)}
		}
	}
	p.accepted++
	f.accepted++
	if p.trace {
		if len(p.calls) >= 20000 {
			panic("中央來源繪製紀錄超限")
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
func (p *hdCenterPrototype) write(addr uint32, old, value byte) {
	m := p.h.m
	i := int(addr - hdBuildingCanvas)
	p.revision++
	cs, ip := m.CPU.OpAddr()
	if p.active {
		f := &p.frames[p.selected]
		x, y := i%320-p.x, i/320-p.y
		bit := uint8(0)
		switch ip {
		case 0x181:
			bit = 1
		case 0x1b4:
			bit = 2
		case 0x1d2:
			bit = 4
		}
		pc := int(cs)*16 + int(ip)
		if cs == 0xd46 && bit&f.writers != 0 && bytes.Equal(m.Mem[pc:pc+16], hdCenterWriterCodes[ip]) && x >= 0 && x < f.w && y >= 0 && y < f.h {
			k := y*f.w + x
			p.counts[k]++
			p.writes[k] = value
		} else {
			p.outside = true
		}
	}
	if cs == 0xb68 && ip == 0x51c && m.CPU.Seg[golem.DS] == 0xa000 && m.CPU.Seg[golem.ES] == 0x2cae {
		pc := int(cs)*16 + int(ip)
		if bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}) {
			dest := int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI])
			source := int(m.CPU.R[golem.SI]) + int(addr) - dest
			if _, ok := p.h.cursorSource(); ok && source >= 0xfa00 && source < 0xfc00 && m.Mem[0xa0000+source] == value {
				k := source & 255
				if source >= 0xfb00 {
					p.pending[i] = hdCenterPending{p.visible[i], old, value, k}
					if p.visible[i].owned {
						p.frames[p.visible[i].slot].paints++
					}
					p.visible[i].owned = false
					return
				}
				prior, ok := p.pending[i]
				delete(p.pending, i)
				if ok && prior.cursor == k && old == prior.value && value == prior.old {
					p.visible[i] = prior.cell
					if prior.cell.owned {
						f := &p.frames[prior.cell.slot]
						f.restores++
						if p.trace {
							if len(p.pairs) >= 200000 {
								panic("中央來源游標紀錄超限")
							}
							p.pairs = append(p.pairs, map[string]any{"ordinal": f.ordinal, "step": m.Steps, "linear": addr, "source_cursor_index": k, "native": prior.cell.native, "local": prior.cell.local, "paint_old": prior.old, "paint_value": prior.value, "restore_old": old, "restore_value": value, "registers": m.CPU.R, "segments": m.CPU.Seg, "code16": fmt.Sprintf("%x", m.Mem[pc:pc+16])})
						}
					}
					return
				}
			}
		}
	}
	p.visible[i].owned = false
	clear(p.pending)
}
func (p *hdCenterPrototype) receipt(f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	owned, valid := 0, 0
	mask := make([]byte, 8000)
	counts := make([][2]int, len(p.frames))
	masks := make([][]byte, len(p.frames))
	for i := range masks {
		masks[i] = make([]byte, 8000)
	}
	for i, c := range p.visible {
		if !c.owned || int(c.slot) >= len(p.frames) {
			continue
		}
		owned++
		counts[c.slot][0]++
		if f.canvas[i] == c.native {
			valid++
			counts[c.slot][1]++
			mask[i>>3] |= 1 << uint(i&7)
			masks[c.slot][i>>3] |= 1 << uint(i&7)
		}
	}
	sources := map[string]any{}
	for i, a := range p.frames {
		sources[fmt.Sprint(a.ordinal)] = map[string]any{"ordinal": a.ordinal, "owned": counts[i][0], "valid": counts[i][1], "mask": masks[i], "accepted": a.accepted, "rejected": a.rejected, "cursor_paint_points": a.paints, "cursor_restore_points": a.restores, "painted": 0, "alpha_pixels": 0}
	}
	return map[string]any{"prototype": true, "asset": "building-009-prototype", "accepted": p.accepted, "rejected": p.rejected, "owned": owned, "valid": valid, "mask": mask, "sources": sources, "pending": len(p.pending), "revision": p.revision}
}
func (p *hdCenterPrototype) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	receipt := p.receipt(f)
	sources := receipt["sources"].(map[string]any)
	painted, alpha := 0, 0
	for i, c := range p.visible {
		if !c.owned || int(c.slot) >= len(p.frames) || f.canvas[i] != c.native {
			continue
		}
		a := p.frames[c.slot]
		sx, sy := int(c.local)%a.w*4, int(c.local)/a.w*4
		ink := 0
		for y := 0; y < 4; y++ {
			for x := 0; x < 4; x++ {
				_, _, _, v := a.art.At(sx+x, sy+y).RGBA()
				if v != 0 {
					ink++
				}
			}
		}
		if ink == 0 {
			continue
		}
		x, y := i%320*4, i/320*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), a.art, image.Pt(sx, sy), draw.Over)
		painted++
		alpha += ink
		r := sources[fmt.Sprint(a.ordinal)].(map[string]any)
		r["painted"] = r["painted"].(int) + 1
		r["alpha_pixels"] = r["alpha_pixels"].(int) + ink
	}
	receipt["painted"], receipt["alpha_pixels"] = painted, alpha
	return receipt
}
