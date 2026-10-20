package main

import (
	"bytes"
	"encoding/binary"
	golem "github.com/wicanr2/dosgolem"
	"image"
)

// 規格069 R97 READY修正。完整原版回傳後才建立Main來源；不改寫DOS。
type hdSceneSpriteDefinition struct {
	content                                    image.Rectangle
	capturedReturn                             bool
	ordinal, width, height, encodedLen, opaque int
	nominal                                    [2]uint16
	encodedSHA, indexedSHA, writesSHA          string
}
type hdSceneSpriteCall struct {
	sourceOffset       int
	slot, x, y, source int
	sourceSegment      uint16
	sp, retCS, retIP   uint16
	start              uint64
	bad                bool
	before             []byte
	values, counts     []byte
}

var hdSceneSpriteWriterCodes = map[uint16][]byte{
	0x181: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x02, 0xeb, 0xe7, 0xeb, 0xd0, 0x3b},
	0x1b4: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xfe, 0xcc, 0x74, 0x03, 0xeb, 0xe7, 0x90, 0xeb, 0xcc},
	0x1d2: {0x26, 0x88, 0x07, 0x03, 0x5e, 0xf0, 0x42, 0xeb, 0xb5, 0x90, 0x5a, 0x5b, 0x03, 0x5e, 0xfe, 0x79},
}

func (p *hdSceneRuntime) beforeSpriteInstruction() {
	if p == nil || p.blocked {
		return
	}
	m, c := p.h.m, p.h.m.CPU
	if call := p.spriteCall; call != nil {
		if c.Seg[golem.CS] == call.retCS && c.IP == call.retIP && c.R[golem.SP] == call.sp+10 {
			p.finishSprite()
		} else if m.Steps-call.start > 750000 || (c.Seg[golem.CS] == 0xd46 && c.IP == 0xa && c.R[golem.SP] != call.sp) {
			p.spriteCall = nil
			p.spriteRejected++
		}
	}
	if p.spriteCall != nil || c.Seg[golem.CS] != 0xd46 || c.IP != 0xa {
		return
	}
	pc := int(c.Seg[golem.CS])*16 + int(c.IP)
	prolog := []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}
	if pc+len(prolog) > len(m.Mem) || !bytes.Equal(m.Mem[pc:pc+len(prolog)], prolog) {
		return
	}
	stack, ok := hdBuildingWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	if !ok {
		return
	}
	offset := int(stack[3]) + 0x36 + int(c.R[golem.AX]&0x7fff)*12
	if offset+12 > 65536 {
		return
	}
	record, ok := hdBuildingWords(m.Mem, stack[4], uint16(offset), 6)
	if !ok {
		return
	}
	slot := -1
	for i, f := range p.frames {
		s := f.sprite
		if s == nil || c.R[golem.AX] != uint16(s.ordinal+1) || int(record[4]) != s.width || int(record[5]) != s.height || record[2] != s.nominal[0] || record[3] != s.nominal[1] {
			continue
		}
		source := int(record[1])*16 + int(record[0])
		if int(record[0])+s.encodedLen > 65536 || source+s.encodedLen > len(m.Mem) || hash(m.Mem[source:source+s.encodedLen]) != s.encodedSHA {
			continue
		}
		if slot >= 0 {
			p.spriteRejected++
			return
		}
		slot = i
	}
	if slot < 0 {
		return
	}
	f := p.frames[slot]
	s := f.sprite
	desc, ok := hdBuildingWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	x, y := int(int16(c.R[golem.DX])), int(int16(stack[2]))
	if !ok || desc[0] != 200 || desc[1] != 320 || desc[2] != 0 || desc[3] != 0x2cae || x < 0 || y < 0 || x+s.width > 320 || y+s.height > 200 || (!s.capturedReturn && (stack[0] != 0x1554 || stack[1] != 0x121d)) || int(c.R[golem.SP])+10 > 65535 {
		p.spriteRejected++
		return
	}
	p.spriteCall = &hdSceneSpriteCall{slot: slot, x: x, y: y, source: int(record[1])*16 + int(record[0]), sourceSegment: record[1], sourceOffset: int(record[0]), sp: c.R[golem.SP], retCS: stack[1], retIP: stack[0], start: m.Steps, before: append([]byte(nil), m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000]...), values: make([]byte, s.width*s.height), counts: make([]byte, s.width*s.height)}
}

func (p *hdSceneRuntime) recordSpriteWrite(a uint32, value byte) {
	call := p.spriteCall
	if call == nil {
		return
	}
	if a < hdBuildingCanvas || a >= hdBuildingCanvas+64000 {
		cs, ip := p.h.m.CPU.OpAddr()
		if _, known := hdSceneSpriteWriterCodes[ip]; known && cs == 0xd46 && uint32(p.h.m.CPU.Seg[golem.ES])*16+uint32(p.h.m.CPU.R[golem.BX]) == a {
			call.bad = true
		}
		return
	}
	m, c := p.h.m, p.h.m.CPU
	s := p.frames[call.slot].sprite
	pos := int(a - hdBuildingCanvas)
	x, y := pos%320-call.x, pos/320-call.y
	cs, ip := c.OpAddr()
	code, known := hdSceneSpriteWriterCodes[ip]
	pc := int(cs)*16 + int(ip)
	if x < 0 || x >= s.width || y < 0 || y >= s.height || !known || cs != 0xd46 || pc+len(code) > len(m.Mem) || !bytes.Equal(m.Mem[pc:pc+len(code)], code) || (c.Seg[golem.ES] != 0x2cae && c.Seg[golem.ES] != 0x33ae) || c.Seg[golem.DS] != call.sourceSegment || int(c.R[golem.SI]) < call.sourceOffset || int(c.R[golem.SI]) > call.sourceOffset+s.encodedLen || uint32(c.Seg[golem.ES])*16+uint32(c.R[golem.BX]) != a {
		call.bad = true
		return
	}
	k := y*s.width + x
	if call.counts[k] < 2 {
		call.counts[k]++
	}
	call.values[k] = value
}

func (p *hdSceneRuntime) finishSprite() {
	call := p.spriteCall
	p.spriteCall = nil
	f := p.frames[call.slot]
	s := f.sprite
	m := p.h.m
	raw := bytes.Repeat([]byte{253}, s.width*s.height)
	padded := bytes.Repeat([]byte{253}, 64000)
	expected := append([]byte(nil), call.before...)
	canonical := make([]byte, 0, s.opaque*3)
	for k, n := range call.counts {
		if n == 0 {
			continue
		}
		if n != 1 || call.values[k] == 253 {
			call.bad = true
		}
		raw[k] = call.values[k]
		padded[k/s.width*320+k%s.width] = call.values[k]
		expected[(call.y+k/s.width)*320+call.x+k%s.width] = call.values[k]
		canonical = binary.LittleEndian.AppendUint16(canonical, uint16(k))
		canonical = append(canonical, call.values[k])
	}
	if call.bad || len(canonical) != s.opaque*3 || hash(canonical) != s.writesSHA || hash(raw) != s.indexedSHA || hash(padded) != f.nativeSHA || hash(m.Mem[call.source:call.source+s.encodedLen]) != s.encodedSHA || !bytes.Equal(expected, m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000]) {
		p.spriteRejected++
		return
	}
	f.native = padded
	f.indices = nil
	used := [256]bool{}
	for _, v := range raw {
		if v != 253 {
			used[v] = true
		}
	}
	for v, yes := range used {
		if yes {
			f.indices = append(f.indices, byte(v))
		}
	}
	for k, n := range call.counts {
		if n == 1 {
			at := (call.y+k/s.width)*320 + call.x + k%s.width
			p.set(hdBuildingCanvas+uint32(at), hdSceneCell{slot: uint8(call.slot + 1), local: uint16(k/s.width*320 + k%s.width), value: call.values[k]})
		}
	}
	f.decoded++
	p.spriteAccepted++
	p.revision++
}

// Main游標配對不改變來源持有權，只恢復原游標透明格下方已驗的SS底圖。
// 原游標不透明格繼續沿既有游標合成契約處理。
func (p *hdSceneRuntime) spriteCursorCell(pos int, f draftNativeFrame) (hdSceneCell, bool) {
	if p == nil || p.blocked || pos < 0 || pos >= 64000 || len(f.canvas) != 64000 || f.cursor.Dx() != 16 || f.cursor.Dy() != 16 {
		return hdSceneCell{}, false
	}
	pair, known := p.pending[pos]
	frame, valid := p.frame(pair.cell)
	if !known || !valid || frame.sprite == nil || pair.cell.value != pair.old || pair.old != pair.value || f.canvas[pos] != pair.value {
		return hdSceneCell{}, false
	}
	x, y := pos%320-f.cursor.Min.X, pos/320-f.cursor.Min.Y
	if x < 0 || x >= 16 || y < 0 || y >= 16 || pair.k != y*16+x {
		return hdSceneCell{}, false
	}
	source, valid := p.h.cursorSource()
	if !valid || source[pair.k] != 255 || p.h.m.Mem[hdBuildingCanvas+uint32(pos)] != pair.value || p.h.m.Mem[0xafa00+pair.k] != pair.old || p.h.m.Mem[0xafb00+pair.k] != pair.value {
		return hdSceneCell{}, false
	}
	return pair.cell, true
}
