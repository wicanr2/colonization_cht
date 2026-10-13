// 規格064 READY：已驗第024幀木棚、逐點來源與正常游標還原。
// 只觀測原版來源並在四倍畫布合成，沒有DOS寫入。
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

const hdShelterArtSHA = "cb83a56cde5f06bb13bc69237fe5476efb6b40eb8ea6cfb2fe0942f3fd3da462"
const hdShelterEncodedSHA = "91a6a162404b43e2c17d13bd1ffe5818286e27763ffab2a776f24bc1fbf70c03"
const hdShelterWritesSHA = "ea54c35681b9d6d952473715f01cc7ee957871f4fc1eb1abfc7bc1f9fdb4cd12"

type hdShelterCell struct {
	owned  bool
	local  uint16
	native byte
}
type hdShelterPending struct {
	cell       hdShelterCell
	old, value byte
	cursor     int
}
type hdShelterRuntime struct {
	h                                                                 *hdRuntime
	art                                                               *image.RGBA
	visible                                                           [64000]hdShelterCell
	pending                                                           map[int]hdShelterPending
	active, outside                                                   bool
	x, y                                                              int
	sp, retCS, retIP                                                  uint16
	start, revision, accepted, rejected, cursorPaints, cursorRestores uint64
	writes                                                            [621]byte
	counts                                                            [621]uint16
	trace                                                             bool
	calls, pairs                                                      []map[string]any
	entry                                                             map[string]any
}

func hdShelterReadBounded(path, want string, limit int64) ([]byte, error) {
	raw, err := hdReadFile(path, limit)
	if err != nil {
		return nil, err
	}
	if hash(raw) != want {
		return nil, fmt.Errorf("木棚HD來源或素材指紋不同：%s", path)
	}
	return raw, nil
}
func loadHDShelterRuntime(h *hdRuntime, game, directory string) (*hdShelterRuntime, error) {
	if directory == "" {
		return nil, fmt.Errorf("木棚HD素材目錄未指定")
	}
	if h == nil {
		return nil, fmt.Errorf("木棚HD需要既有HD顯示層")
	}
	if _, err := hdShelterReadBounded(filepath.Join(game, "BUILDING.SS"), "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4", 8<<20); err != nil {
		return nil, err
	}
	raw, err := hdShelterReadBounded(filepath.Join(directory, "building-024.png"), hdShelterArtSHA, 8<<20)
	if err != nil {
		return nil, err
	}
	config, err := png.DecodeConfig(bytes.NewReader(raw))
	if err != nil || config.Width != 1158 || config.Height != 1359 {
		return nil, fmt.Errorf("木棚原圖尺寸不同")
	}
	source, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	art := image.NewRGBA(image.Rect(0, 0, 92, 108))
	for y := 0; y < 108; y++ {
		for x := 0; x < 92; x++ {
			sx, sy := (2*x+1)*source.Bounds().Dx()/184, (2*y+1)*source.Bounds().Dy()/216
			art.Set(x, y, source.At(sx, sy))
		}
	}
	p := &hdShelterRuntime{h: h, art: art, pending: map[int]hdShelterPending{}}
	h.m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, o, v byte) { p.write(a, o, v) })
	return p, nil
}
func (p *hdShelterRuntime) beforeInstruction() {
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
		}
	}
	if c.Seg[golem.CS] != 0xd46 || c.IP != 0xa || p.active {
		return
	}
	entry := int(c.Seg[golem.CS])*16 + int(c.IP)
	if !bytes.Equal(m.Mem[entry:entry+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	if c.R[golem.AX] != 25 {
		return
	}
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
	if source+383 > len(m.Mem) || hash(m.Mem[source:source+383]) != hdShelterEncodedSHA {
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
	if d != [4]uint16{200, 320, 0, 0x2cae} || record[4] != 23 || record[5] != 27 || x < 0 || x+23 > 320 || y < 0 || y+27 > 200 {
		p.rejected++
		return
	}
	p.active, p.outside, p.x, p.y = true, false, x, y
	p.start, p.sp, p.retCS, p.retIP = m.Steps, c.R[golem.SP], words[1], words[0]
	p.writes, p.counts = [621]byte{}, [621]uint16{}
	if p.trace {
		p.entry = map[string]any{"entry_step": m.Steps, "registers": c.R, "segments": c.Seg, "stack": words, "record_far": fmt.Sprintf("%04X:%04X", words[4], off), "record": record,
			"source_far": fmt.Sprintf("%04X:%04X", record[1], record[0]), "source_sha256": hash(m.Mem[source : source+383]), "rect": [4]int{x, y, x + 23, y + 27}}
	}
}
func (p *hdShelterRuntime) finish() {
	p.active = false
	var encoded []byte
	for k, n := range p.counts {
		if n == 0 {
			continue
		}
		if n != 1 {
			p.outside = true
		}
		encoded = binary.LittleEndian.AppendUint16(encoded, uint16(k))
		encoded = append(encoded, p.writes[k])
	}
	if p.outside || len(encoded) != 789 || hash(encoded) != hdShelterWritesSHA {
		p.rejected++
		return
	}
	for k, n := range p.counts {
		if n == 1 {
			i := (p.y+k/23)*320 + p.x + k%23
			p.visible[i] = hdShelterCell{true, uint16(k), p.writes[k]}
		}
	}
	p.accepted++
	if p.trace {
		if len(p.calls) >= 20000 {
			panic("木棚來源紀錄超限")
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
func (p *hdShelterRuntime) write(addr uint32, old, value byte) {
	m := p.h.m
	i := int(addr - hdBuildingCanvas)
	p.revision++
	cs, ip := m.CPU.OpAddr()
	if p.active {
		x, y := i%320-p.x, i/320-p.y
		if cs == 0xd46 && ip == 0x1d2 && bytes.Equal(m.Mem[int(cs)*16+int(ip):int(cs)*16+int(ip)+16], []byte{0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xeb, 0xb5, 0x90, 0x5a, 0x5b, 0x03, 0x5e, 0xfe, 0x79}) && x >= 0 && x < 23 && y >= 0 && y < 27 {
			k := y*23 + x
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
					// 外圍背景也要保留配對；還原順序會先經過木棚外的像素。
					p.pending[i] = hdShelterPending{p.visible[i], old, value, k}
					if p.visible[i].owned {
						p.cursorPaints++
					}
					p.visible[i].owned = false
					return
				}
				prior, ok := p.pending[i]
				delete(p.pending, i)
				if ok && prior.cursor == k && old == prior.value && value == prior.old {
					p.visible[i] = prior.cell
					if prior.cell.owned {
						p.cursorRestores++
					}
					if p.trace && prior.cell.owned {
						if len(p.pairs) >= 200000 {
							panic("木棚游標紀錄超限")
						}
						p.pairs = append(p.pairs, map[string]any{"step": m.Steps, "linear": addr, "source_cursor_index": k, "native": prior.cell.native, "local": prior.cell.local,
							"paint_old": prior.old, "paint_value": prior.value, "restore_old": old, "restore_value": value, "registers": m.CPU.R, "segments": m.CPU.Seg,
							"code16": fmt.Sprintf("%x", m.Mem[pc:pc+16])})
					}
					return
				}
			}
		}
	}
	p.visible[i].owned = false
	clear(p.pending)
}
func (p *hdShelterRuntime) receipt(f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	owned, valid := 0, 0
	mask := make([]byte, 8000)
	for i, c := range p.visible {
		if !c.owned {
			continue
		}
		owned++
		if f.canvas[i] == c.native {
			valid++
			mask[i>>3] |= 1 << uint(i&7)
		}
	}
	return map[string]any{"formal": true, "asset": "building-024", "accepted": p.accepted, "rejected": p.rejected, "owned": owned, "valid": valid,
		"cursor_paint_points": p.cursorPaints, "cursor_restore_points": p.cursorRestores, "pending": len(p.pending), "revision": p.revision, "mask": mask}
}
func (p *hdShelterRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	if p == nil {
		return nil
	}
	receipt := p.receipt(f)
	painted, alphaPixels := 0, 0
	for i, c := range p.visible {
		if !c.owned || f.canvas[i] != c.native {
			continue
		}
		sx, sy := int(c.local)%23*4, int(c.local)/23*4
		ink := 0
		for yy := 0; yy < 4; yy++ {
			for xx := 0; xx < 4; xx++ {
				_, _, _, a := p.art.At(sx+xx, sy+yy).RGBA()
				if a != 0 {
					ink++
				}
			}
		}
		if ink == 0 {
			continue
		}
		x, y := i%320*4, i/320*4
		draw.Draw(out, image.Rect(x, y, x+4, y+4), p.art, image.Pt(sx, sy), draw.Over)
		painted++
		alphaPixels += ink
	}
	receipt["painted"] = painted
	receipt["alpha_pixels"] = alphaPixels
	return receipt
}
