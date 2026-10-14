// 規格064 R44 READY：城內十來源正式HD顯示。
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

type hdNineFrame struct {
	ordinal, w, h, encodedLen, opaque    int
	encodedSHA, writesSHA, artSHA, file  string
	artW, artH                           int
	sample, content                      [4]int
	writers                              uint8
	art                                  *image.RGBA
	accepted, rejected, paints, restores uint64
}

var hdNineFrames = []hdNineFrame{
	{ordinal: 16, w: 73, h: 18, encodedLen: 713, opaque: 504, encodedSHA: "37e3c67aad3611c0d6098cd3804fa17a6a33d8b0bf66e6df3e038089388a4568", writesSHA: "6c6c6b9ad00ffec4ae37390daa63f5d4e95ddfc473ee8fdf1443d131073df141", artSHA: "4378783b1ea54f32af12047fb06f260b496d68459f1eaacb5d42d5231c11ecd1", file: "building-016.png", artW: 2170, artH: 725, sample: [4]int{8, 119, 2162, 609}, content: [4]int{0, 0, 73, 18}, writers: 6},
	{ordinal: 21, w: 23, h: 27, encodedLen: 531, opaque: 446, encodedSHA: "d50481bdb7cfbb742035730387bb72601750c1cce584a47b9099034b410e38c8", writesSHA: "39680bcc21bfac1a7c8aa353948022ae6cdf1755882824a05b1177373a6de4b5", artSHA: "f81583f35c5102290424fd6575b67f08e47ab2488af61ed67eea0244fafe46f7", file: "building-021.png", artW: 1158, artH: 1358, sample: [4]int{20, 29, 1143, 1263}, content: [4]int{0, 2, 23, 27}, writers: 6},
	{ordinal: 27, w: 23, h: 27, encodedLen: 570, opaque: 465, encodedSHA: "51dd0b1f21b29b0e7ee6f7e07d93e5418ed3368a11eaedffc81aa69b954e7d31", writesSHA: "379715daae1fc96a7496bc9732a66ab73df9137c5fc5fed1aea668654b8c76b7", artSHA: "59d78ffbe53983600336fa7b0919032fcb95f79f744f31c03242e6c2f7f4f4b1", file: "building-027.png", artW: 1158, artH: 1359, sample: [4]int{40, 16, 1120, 1336}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 35, w: 44, h: 22, encodedLen: 752, opaque: 507, encodedSHA: "8d75b678630f769528a01f79c897dcc33f982353c93674997fc02fc9df32c198", writesSHA: "146e920bfced13314162b208f61d37c19b166c83321703ad2c86b577b11e773b", artSHA: "05832b749f1cca7e97af3a8cdd3417c12284df2d6db43e4e6656de65c7a44e58", file: "building-035.png", artW: 1774, artH: 887, sample: [4]int{83, 111, 1733, 804}, content: [4]int{0, 0, 44, 21}, writers: 7},
	{ordinal: 39, w: 23, h: 27, encodedLen: 541, opaque: 459, encodedSHA: "29dafe80be32105e570abf822fea90b1ce73bcc206523aa758346b24066c8936", writesSHA: "c2534296a3f6ff776771ee5c1069ff95b8141511f2790629359a34f3978212bb", artSHA: "2c2f7f9c3c325c64b919b02ca37fd8876ad74850fa7f7e737ef96d15f6a1b8c0", file: "building-039.png", artW: 1158, artH: 1359, sample: [4]int{37, 17, 1138, 1300}, content: [4]int{0, 0, 23, 25}, writers: 6},
	{ordinal: 42, w: 53, h: 37, encodedLen: 1176, opaque: 848, encodedSHA: "349af0f0328751db570320e0964f65a50fc6c7b393b991cd61e886a429536582", writesSHA: "d11c6733d9f05e82872a4eb5a8e7e792bd3b5a0ccbfd0dc50ff97f4c6e36bfd9", artSHA: "34f7ee08d3429ed6a6659b5c5eb6aa1ecfdf1656a814a494658368c475fdd8d4", file: "building-042.png", artW: 1502, artH: 1047, sample: [4]int{24, 10, 1502, 1034}, content: [4]int{1, 0, 53, 36}, writers: 7},
	{ordinal: 43, w: 44, h: 22, encodedLen: 546, opaque: 369, encodedSHA: "31756e82c00bdbbd5dee53414b08061e47bf102e87cc3d70beef9be0dd5116aa", writesSHA: "4e40c62f6fae8204e485ddd6207239cd3c9031ea0ff234660d4fd35c56dd362c", artSHA: "0d9ad7021e2ddf5a2062e6705ba0be869e4ac3781046262eec0b4984a371b928", file: "building-043.png", artW: 1774, artH: 887, sample: [4]int{12, 44, 1766, 852}, content: [4]int{0, 1, 44, 22}, writers: 7},
	{ordinal: 44, w: 23, h: 27, encodedLen: 462, opaque: 262, encodedSHA: "f9bb3cc9064ce58f05443b8671a870d69fde96667e9a3dde1c24763b1c368332", writesSHA: "687fc5f1be762b2d8dea63c8f58ec52efa3234a6e5acc122bf225b4898116a8c", artSHA: "004fdb0045fc47653fd40beef438d0f2922933639a68c95a1d7b504ed908afed", file: "building-044.png", artW: 1158, artH: 1359, sample: [4]int{17, 21, 1138, 1323}, content: [4]int{0, 0, 23, 27}, writers: 6},
	{ordinal: 45, w: 75, h: 48, encodedLen: 1591, opaque: 1069, encodedSHA: "129934aa9808419a2164569da49363b9a8c8486a0460fd9da876cb641b797de1", writesSHA: "4cd7ef3f6f68a770158bddf9b98b1797c5c204acfbe83596bfc6bfaa33517627", artSHA: "07049354109ff9bee01f103a2b408d227a607b8bba138cefc9de5af840f99915", file: "building-045.png", artW: 1568, artH: 1003, sample: [4]int{18, 0, 1568, 979}, content: [4]int{1, 0, 75, 48}, writers: 6},
	{ordinal: 9, w: 53, h: 37, encodedLen: 1254, opaque: 1095, encodedSHA: "8900416036b739238f3d36ef0bd6de7c64cc92e2273658c866e233a328380d8c", writesSHA: "80e2c7b872906ce4fc27a12926b6a9be2a77c90f75c509f0524346254781f0d6", artSHA: "bc7057fa60db21a120f3d2fd81d59f7ae77cfa56ac351aa6df9d455f7bac29b6", file: "building-009.png", artW: 1500, artH: 1049, sample: [4]int{9, 57, 1490, 1004}, content: [4]int{0, 0, 53, 36}, writers: 6},
}
var hdNineWriterCodes = map[uint16][]byte{
	0x181: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xe7, 0xeb, 0xd0, 0x3b},
	0x1b4: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x03, 0xeb, 0xe7, 0x90, 0xeb, 0xcc},
	0x1d2: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xeb, 0xb5, 0x90, 0x5a, 0x5b, 0x03, 0x5e, 0xfe, 0x79},
}

type hdNineCell struct {
	owned  bool
	local  uint16
	native byte
	slot   uint8
}
type hdNinePending struct {
	cell       hdNineCell
	old, value byte
	cursor     int
}
type hdNineRuntime struct {
	h                                   *hdRuntime
	frames                              []hdNineFrame
	visible                             [64000]hdNineCell
	pending                             map[int]hdNinePending
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

func hdNineRead(path, want string, limit int64) ([]byte, error) {
	raw, err := hdReadFile(path, limit)
	if err != nil {
		return nil, err
	}
	if hash(raw) != want {
		return nil, fmt.Errorf("城內來源指紋不同：%s", path)
	}
	return raw, nil
}
func loadHDNineRuntime(h *hdRuntime, game, directory string) (*hdNineRuntime, error) {
	if h == nil || directory == "" {
		return nil, fmt.Errorf("城內來源需要既有HD及素材目錄")
	}
	if _, err := hdNineRead(filepath.Join(game, "BUILDING.SS"), hdBuildingFileSHA, 8<<20); err != nil {
		return nil, err
	}
	p := &hdNineRuntime{h: h, frames: append([]hdNineFrame(nil), hdNineFrames...), pending: map[int]hdNinePending{}}
	for i := range p.frames {
		f := &p.frames[i]
		raw, err := hdNineRead(filepath.Join(directory, f.file), f.artSHA, 8<<20)
		if err != nil {
			return nil, err
		}
		c, err := png.DecodeConfig(bytes.NewReader(raw))
		if err != nil || c.Width != f.artW || c.Height != f.artH {
			return nil, fmt.Errorf("城內來源原圖尺寸不同：%d", f.ordinal)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		a, b := f.sample, f.content
		if a[0] < 0 || a[1] < 0 || a[2] <= a[0] || a[3] <= a[1] || a[2] > f.artW || a[3] > f.artH || b[0] < 0 || b[1] < 0 || b[2] <= b[0] || b[3] <= b[1] || b[2] > f.w || b[3] > f.h {
			return nil, fmt.Errorf("城內來源取樣邊界不同：%d", f.ordinal)
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
func (p *hdNineRuntime) beforeInstruction() {
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
func (p *hdNineRuntime) finish() {
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
			p.visible[i] = hdNineCell{true, uint16(k), p.writes[k], uint8(p.selected)}
		}
	}
	p.accepted++
	f.accepted++
	if p.trace {
		if len(p.calls) >= 20000 {
			panic("城內來源繪製紀錄超限")
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
func (p *hdNineRuntime) write(addr uint32, old, value byte) {
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
		if cs == 0xd46 && bit&f.writers != 0 && bytes.Equal(m.Mem[pc:pc+16], hdNineWriterCodes[ip]) && x >= 0 && x < f.w && y >= 0 && y < f.h {
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
					p.pending[i] = hdNinePending{p.visible[i], old, value, k}
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
								panic("城內來源游標紀錄超限")
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
func (p *hdNineRuntime) receipt(f draftNativeFrame) map[string]any {
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
	return map[string]any{"formal": true, "asset": "building-nine", "accepted": p.accepted, "rejected": p.rejected, "owned": owned, "valid": valid, "mask": mask, "sources": sources, "pending": len(p.pending), "revision": p.revision}
}
func (p *hdNineRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
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
