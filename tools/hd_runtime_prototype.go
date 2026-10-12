// 規格061 DRAFT的可丟棄HD原型；不由正式組裝器引用，不寫入DOS。
package main

import (
	"bytes"
	"encoding/binary"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"os"

	golem "github.com/wicanr2/dosgolem"
)

var hdPrototypeAsset = flag.String("hd-prototype-asset", "", "僅隔離研究：已驗單一建築候選PNG")

const hdProtoSourceSHA = "7c34170632e995ebfb281e451f340d14faec5fa25970ca0479493d99758afb2a"
const hdProtoOpaqueSHA = "1c5978b8b131150ba8abecca42a240282344553352195d683ad827e51b4fbef1"
const hdProtoCursorSHA = "47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03"
const hdProtoCanvas = uint32(0x2cae0)

type hdProtoPixel struct {
	old, value  byte
	owned       bool
	cursorIndex int
}
type hdPrototype struct {
	m                                                *golem.Machine
	art                                              *image.RGBA
	owned                                            [621]bool
	opaque                                           [621]bool
	background, after                                [621]byte
	pending                                          map[int]hdProtoPixel
	active                                           bool
	retCS, retIP, sp                                 uint16
	start, revision                                  uint64
	before                                           [621]byte
	writes                                           map[int]byte
	counts                                           map[int]int
	outside                                          bool
	accepted, rejected, cursorPaints, cursorRestores uint64
}

func hdProtoIndex(addr uint32) (int, bool) {
	if addr < hdProtoCanvas || addr >= hdProtoCanvas+64000 {
		return 0, false
	}
	i := int(addr - hdProtoCanvas)
	x, y := i%320, i/320
	if x < 56 || x >= 79 || y < 13 || y >= 40 {
		return 0, false
	}
	return (y-13)*23 + x - 56, true
}
func hdProtoCanvasIndex(i int) int { return (13+i/23)*320 + 56 + i%23 }
func hdProtoRegion(mem []byte) (out [621]byte) {
	for i := range out {
		out[i] = mem[int(hdProtoCanvas)+hdProtoCanvasIndex(i)]
	}
	return
}
func hdProtoWords(mem []byte, seg, off uint16, n int) ([]uint16, bool) {
	at := int(seg)*16 + int(off)
	if int(off)+n*2 > 65536 || at+n*2 > len(mem) {
		return nil, false
	}
	words := make([]uint16, n)
	for i := range words {
		words[i] = binary.LittleEndian.Uint16(mem[at+i*2 : at+i*2+2])
	}
	return words, true
}
func newHDPrototype(m *golem.Machine, path string) (*hdPrototype, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	if len(raw) > 8<<20 || hash(raw) != "c33885bd2570cc5ec0eb204aece69f1363b66fab5c1f16da82786f3b7e5139d8" {
		return nil, fmt.Errorf("HD prototype asset fingerprint mismatch")
	}
	im, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	if im.Bounds().Dx() != 1158 || im.Bounds().Dy() != 1359 {
		return nil, fmt.Errorf("HD prototype asset dimensions mismatch")
	}
	art := image.NewRGBA(image.Rect(0, 0, 92, 108))
	for y := 0; y < 108; y++ {
		for x := 0; x < 92; x++ {
			// Pillow既有離線原型的像素中心最近鄰取樣，不重寫原始候選。
			sx, sy := (2*x+1)*1158/(2*92), (2*y+1)*1359/(2*108)
			art.SetRGBA(x, y, color.RGBAModel.Convert(im.At(sx, sy)).(color.RGBA))
		}
	}
	h := &hdPrototype{m: m, art: art, pending: map[int]hdProtoPixel{}}
	m.WatchWrite(hdProtoCanvas, hdProtoCanvas+63999, func(_ *golem.Machine, a uint32, old, value byte) { h.write(a, old, value) })
	return h, nil
}

func (h *hdPrototype) key() string {
	if h == nil {
		return ""
	}
	return fmt.Sprintf("/hd/%d", h.revision)
}
func (h *hdPrototype) beforeInstruction() {
	if h == nil {
		return
	}
	m := h.m
	c := m.CPU
	cs, ip := c.Seg[golem.CS], c.IP
	if h.active && (m.Steps-h.start > 100000 || (cs == 0xd46 && ip == 0xa)) {
		h.active = false
		h.rejected++
	}
	if h.active && cs == h.retCS && ip == h.retIP && c.R[golem.SP] == h.sp+10 {
		h.finish()
	}
	if cs != 0xd46 || ip != 0xa || c.R[golem.AX] != 33 || c.R[golem.DX] != 56 {
		return
	}
	pc := int(cs)*16 + int(ip)
	prefix := []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 0x02}
	if !bytes.Equal(m.Mem[pc:pc+len(prefix)], prefix) {
		h.rejected++
		return
	}
	stack, ok := hdProtoWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	if !ok || stack[2] != 13 {
		return
	}
	dest, ok := hdProtoWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok || dest[0] != 200 || dest[1] != 320 || uint32(dest[3])*16+uint32(dest[2]) != hdProtoCanvas {
		return
	}
	off := uint16(33*12 + uint32(stack[3]) + 0x36)
	record, ok := hdProtoWords(m.Mem, stack[4], off, 6)
	if !ok || record[4] != 23 || record[5] != 27 {
		return
	}
	at := int(record[1])*16 + int(record[0])
	if int(record[0])+534 > 65536 || at+534 > len(m.Mem) || hash(m.Mem[at:at+534]) != hdProtoSourceSHA {
		h.rejected++
		return
	}
	h.active = true
	h.start = m.Steps
	h.retCS, h.retIP, h.sp = stack[1], stack[0], c.R[golem.SP]
	h.before = hdProtoRegion(m.Mem)
	h.writes = map[int]byte{}
	h.counts = map[int]int{}
	h.outside = false
}
func (h *hdPrototype) finish() {
	h.active = false
	var encoded []byte
	for i := 0; i < 621; i++ {
		if v, ok := h.writes[i]; ok {
			if h.counts[i] != 1 {
				h.rejected++
				return
			}
			encoded = append(encoded, byte(i), byte(i>>8), v)
		}
	}
	current := hdProtoRegion(h.m.Mem)
	if h.outside || len(h.writes) != 440 || hash(encoded) != hdProtoOpaqueSHA {
		h.rejected++
		return
	}
	for i, v := range current {
		expected := h.before[i]
		if n, ok := h.writes[i]; ok {
			expected = n
		}
		if v != expected {
			h.rejected++
			return
		}
	}
	h.background, h.after = h.before, current
	for i := range h.owned {
		_, h.opaque[i] = h.writes[i]
		h.owned[i] = true
	}
	h.pending = map[int]hdProtoPixel{}
	h.accepted++
	h.revision++
}
func (h *hdPrototype) cursorSource() ([]byte, bool) {
	if len(h.m.Mem) < 0xafe00 {
		return nil, false
	}
	source := h.m.Mem[0x1cd74:0x1ce74]
	return source, hash(source) == hdProtoCursorSHA
}
func (h *hdPrototype) write(addr uint32, old, value byte) {
	i, inside := hdProtoIndex(addr)
	if h.active {
		if !inside {
			h.outside = true
		} else {
			h.counts[i]++
			h.writes[i] = value
		}
	}
	if !inside {
		return
	}
	h.revision++
	cs, ip := h.m.CPU.OpAddr()
	if cs == 0xb68 && ip == 0x51c && h.m.CPU.Seg[golem.DS] == 0xa000 && h.m.CPU.Seg[golem.ES] == 0x2cae {
		pc := int(cs)*16 + int(ip)
		code := []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 0x03, 0xf3, 0x03, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}
		if bytes.Equal(h.m.Mem[pc:pc+16], code) {
			c := h.m.CPU
			at := uint32(c.Seg[golem.ES])*16 + uint32(c.R[golem.DI])
			sourceOffset := int(c.R[golem.SI]) + int(int64(addr)-int64(at))
			if _, ok := h.cursorSource(); ok && sourceOffset >= 0xfa00 && sourceOffset < 0xfc00 &&
				h.m.Mem[0xa0000+sourceOffset] == value {
				k := sourceOffset & 255
				if sourceOffset >= 0xfb00 {
					h.pending[i] = hdProtoPixel{old, value, h.owned[i], k}
					h.owned[i] = false
					h.cursorPaints++
					return
				}
				prior, ok := h.pending[i]
				delete(h.pending, i)
				if ok && prior.cursorIndex == k && old == prior.value && value == prior.old {
					h.owned[i] = prior.owned
					h.cursorRestores++
					return
				}
			}
		}
	}
	h.owned[i] = false
	// 任何其他矩形寫入使未完成游標配對失效，不能還原過期擁有權。
	clear(h.pending)
}
func (h *hdPrototype) cursorValid(f draftNativeFrame) ([]byte, bool) {
	source, reason := h.cursorProof(f)
	return source, reason == ""
}
func (h *hdPrototype) cursorProof(f draftNativeFrame) ([]byte, string) {
	source, ok := h.cursorSource()
	if !ok {
		return nil, "source"
	}
	if f.mode != 0x13 || f.cursor.Dx() != 16 || f.cursor.Dy() != 16 {
		return nil, "mode-or-size"
	}
	tail := h.m.Mem[0xafa00:0xafc00]
	for k, v := range source {
		expected := v
		if v == 255 {
			expected = tail[k]
		}
		if tail[256+k] != expected {
			return nil, fmt.Sprintf("cursor-composition:%d", k)
		}
		x, y := f.cursor.Min.X+k%16, f.cursor.Min.Y+k/16
		if x < 0 || y < 0 || x >= 320 || y >= 200 {
			continue
		}
		i := y*320 + x
		if f.canvas[i] != tail[k] {
			return nil, fmt.Sprintf("cursor-background:%d", k)
		}
		if f.indexed[i] != tail[256+k] {
			return nil, fmt.Sprintf("cursor-indexed:%d", k)
		}
	}
	for i, v := range f.indexed {
		if !image.Pt(i%320, i/320).In(f.cursor) && v != f.canvas[i] {
			return nil, fmt.Sprintf("outside-cursor:%d", i)
		}
	}
	return source, ""
}
func (h *hdPrototype) base(f draftNativeFrame) (*image.RGBA, map[string]any) {
	out := draftRGB(f.indexed, f.palette)
	receipt := map[string]any{"prototype": true, "accepted": h.accepted, "rejected": h.rejected,
		"cursor_paint_points": h.cursorPaints, "cursor_restore_points": h.cursorRestores, "owned": 0, "painted": 0}
	_, reason := h.cursorProof(f)
	if reason != "" {
		receipt["reason"] = "unverified-cursor-or-native-surface"
		receipt["cursor_reject"] = reason
		return out, receipt
	}
	owned, painted := 0, 0
	for i, v := range h.owned {
		if !v {
			continue
		}
		owned++
		pos := hdProtoCanvasIndex(i)
		if f.canvas[pos] != h.after[i] {
			continue
		}
		if h.opaque[i] {
			draftPaintPixel(out, pos, h.background[i], f.palette)
		}
		x, y := i%23*4, i/23*4
		rect := image.Rect(224+x, 52+y, 228+x, 56+y)
		draw.Draw(out, rect, h.art, image.Pt(x, y), draw.Over)
		painted++
	}
	receipt["owned"], receipt["painted"], receipt["reason"] = owned, painted, "known-building"
	return out, receipt
}
func (h *hdPrototype) restoreCursor(out *image.RGBA, f draftNativeFrame) {
	source, ok := h.cursorValid(f)
	if !ok {
		return
	}
	for k, v := range source {
		if v == 255 {
			continue
		}
		x, y := f.cursor.Min.X+k%16, f.cursor.Min.Y+k/16
		if x >= 0 && y >= 0 && x < 320 && y < 200 {
			draftPaintPixel(out, y*320+x, f.indexed[y*320+x], f.palette)
		}
	}
}
func (b *draftLanguageBackend) rebuildWithHD(t *draftLanguageTarget, o displayOptions, f draftNativeFrame) (*image.RGBA, map[string]any, error) {
	if o.Graphics != "hd" {
		return draftRebuildTarget(t, f.journal, f.canvas, f.buffer, f.indexed, f.palette, f.cursor, f.step, f.mode)
	}
	if b.hd == nil {
		return nil, nil, fmt.Errorf("ui.error.unavailable")
	}
	base, hd := b.hd.base(f)
	out, record, err := draftRebuildTargetOn(t, f.journal, f.canvas, f.buffer, f.indexed, f.palette, f.cursor, f.step, f.mode, base)
	if err != nil {
		return nil, nil, err
	}
	b.hd.restoreCursor(out, f)
	record["hd"] = hd
	return out, record, nil
}
