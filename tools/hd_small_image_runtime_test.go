package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func hdSmallClone(p *hdSmallRuntime) *hdSmallRuntime {
	m := golem.New()
	copy(m.Mem, p.h.m.Mem)
	m.Steps = p.h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = p.h.m.CPU.R, p.h.m.CPU.Seg, p.h.m.CPU.IP, p.h.m.CPU.Flags
	h := *p.h
	h.m = m
	n := *p
	n.h = &h
	h.small = &n
	n.trace = false
	n.frames = append([]hdSmallFrame(nil), p.frames...)
	n.backing = map[uint32]hdSmallCell{}
	for k, v := range p.backing {
		n.backing[k] = v
	}
	n.pending = map[int]hdSmallPending{}
	for k, v := range p.pending {
		n.pending[k] = v
	}
	return &n
}
func hdSmallEntryNegatives(t *testing.T, p *hdSmallRuntime) []string {
	t.Helper()
	positive := hdSmallClone(p)
	positive.active = false
	positive.beforeInstruction()
	if !positive.active {
		t.Fatal("小圖像真實入口未接受")
	}
	c := p.h.m.CPU
	f := p.frames[p.selected]
	stack := int(c.Seg[golem.SS])*16 + int(c.R[golem.SP])
	words := [5]uint16{}
	for i := range words {
		words[i] = binary.LittleEndian.Uint16(p.h.m.Mem[stack+i*2:])
	}
	at := int(words[4])*16 + int(uint16(c.R[golem.AX]*12+words[3]+0x36))
	source := int(binary.LittleEndian.Uint16(p.h.m.Mem[at+2:]))*16 + int(binary.LittleEndian.Uint16(p.h.m.Mem[at:]))
	cases := []struct {
		name   string
		change func(*hdSmallRuntime)
	}{
		{"wrong-frame", func(n *hdSmallRuntime) { n.h.m.CPU.R[golem.AX] |= 0x1000 }},
		{"high-frame-bit", func(n *hdSmallRuntime) { n.h.m.CPU.R[golem.AX] |= 0x8000 }},
		{"negative-x", func(n *hdSmallRuntime) { n.h.m.CPU.R[golem.DX] = 65535 }},
		{"clipped-right", func(n *hdSmallRuntime) { n.h.m.CPU.R[golem.DX] = uint16(321 - f.w) }},
		{"negative-y", func(n *hdSmallRuntime) { binary.LittleEndian.PutUint16(n.h.m.Mem[stack+4:], 65535) }},
		{"clipped-bottom", func(n *hdSmallRuntime) { binary.LittleEndian.PutUint16(n.h.m.Mem[stack+4:], uint16(201-f.h)) }},
		{"wrong-destination", func(n *hdSmallRuntime) { n.h.m.Mem[int(c.Seg[golem.DS])*16+int(c.R[golem.BX])+6]++ }},
		{"wrong-width", func(n *hdSmallRuntime) { n.h.m.Mem[at+8]++ }},
		{"wrong-source-bytes", func(n *hdSmallRuntime) { n.h.m.Mem[source] ^= 1 }},
		{"wrong-entry-code", func(n *hdSmallRuntime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
	}
	var names []string
	for _, tc := range cases {
		n := hdSmallClone(p)
		n.active = false
		tc.change(n)
		n.beforeInstruction()
		if n.active || n.accepted != p.accepted {
			t.Fatal("小圖像入口反例未拒絕", f.ordinal, tc.name)
		}
		names = append(names, tc.name)
	}
	return names
}
func hdSmallWriterNegative(t *testing.T, p *hdSmallRuntime) string {
	t.Helper()
	c := p.h.m.CPU
	f := p.frames[p.selected]
	addr := int(c.Seg[golem.ES])*16 + int(c.R[golem.BX])
	x, y := addr-int(hdBuildingCanvas), 0
	y = x/320 - p.y
	x = x%320 - p.x
	if x < 0 || x >= f.w || y < 0 || y >= f.h {
		t.Fatal("原版小圖像MOV目的不同", f.ordinal)
	}
	local := y*f.w + x
	for _, bad := range []bool{false, true} {
		n := hdSmallClone(p)
		if bad {
			n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)+15] ^= 1
		}
		n.h.m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, o, v byte) { n.write(a, o, v) })
		if err := n.h.m.CPU.Step(); err != nil {
			t.Fatal(err)
		}
		if bad {
			if !n.outside || n.counts[local] != p.counts[local] {
				t.Fatal("小圖像錯寫入碼仍接受", f.ordinal)
			}
		} else if n.outside || n.counts[local] != p.counts[local]+1 {
			t.Fatal("真實小圖像MOV未接受", f.ordinal)
		}
	}
	return "wrong-writer-code"
}
func hdSmallFinishNegatives(t *testing.T, p *hdSmallRuntime) []string {
	t.Helper()
	var names []string
	local := -1
	for k, n := range p.counts {
		if n == 1 {
			local = k
			break
		}
	}
	if local < 0 {
		t.Fatal("缺少小圖像實際寫入")
	}
	for _, duplicate := range []bool{false, true} {
		n := hdSmallClone(p)
		name := "missing-source-write"
		n.counts[local] = 0
		if duplicate {
			name = "duplicate-source-write"
			n.counts[local] = 2
		}
		n.finish()
		if n.accepted != p.accepted || n.rejected != p.rejected+1 {
			t.Fatal("不完整小圖像未拒絕", name)
		}
		names = append(names, name)
	}
	return names
}
func hdSmallOwnershipNegatives(t *testing.T, p *hdSmallRuntime, f draftNativeFrame, slot int) []string {
	t.Helper()
	pixel := -1
	a := p.frames[slot]
	if a.art == nil {
		for i, c := range p.visible {
			if c.owned && int(c.slot) == slot && f.canvas[i] == c.native {
				pixel = i
				break
			}
		}
		if pixel < 0 {
			t.Fatal("缺少已驗小圖像身分", a.ordinal)
		}
		addr := hdBuildingCanvas + uint32(pixel)
		for _, same := range []bool{false, true} {
			n := hdSmallClone(p)
			n.h.m.Mem[0x1cd74] ^= 1
			old := n.h.m.Mem[addr]
			v := old
			if !same {
				v ^= 1
			}
			n.h.m.Mem[addr] = v
			n.write(addr, old, v)
			if n.visible[pixel].owned {
				t.Fatal("未有素材的來源仍須撤銷", a.ordinal, same)
			}
		}
		n := hdSmallClone(p)
		before := n.receipt(f)["valid"].(int)
		n.h.m.Mem[addr] ^= 1
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		if n.receipt(g)["valid"].(int) != before-1 {
			t.Fatal("過期來源仍有效", a.ordinal)
		}
		n = hdSmallClone(p)
		n.pending[pixel] = hdSmallPending{cell: n.visible[pixel]}
		n.h.m.Mem[0x1cd74] ^= 1
		n.write(addr, n.h.m.Mem[addr], n.h.m.Mem[addr])
		if len(n.pending) != 0 {
			t.Fatal("未知寫入未清配對", a.ordinal)
		}
		return []string{"unknown-changed-write", "unknown-same-write", "stale-native-ownership", "interleaved-cursor-pair"}
	}
	for i, c := range p.visible {
		if !c.owned || int(c.slot) != slot || f.canvas[i] != c.native {
			continue
		}
		ink := false
		for y := 0; y < 4; y++ {
			for x := 0; x < 4; x++ {
				_, _, _, v := a.art.At(int(c.local)%a.w*4+x, int(c.local)/a.w*4+y).RGBA()
				ink = ink || v != 0
			}
		}
		if ink {
			pixel = i
			break
		}
	}
	if pixel < 0 {
		t.Fatal("缺少小圖像可見墨跡", a.ordinal)
	}
	paint := func(n *hdSmallRuntime) int {
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		return n.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), g)["painted"].(int)
	}
	baseline := paint(hdSmallClone(p))
	addr := hdBuildingCanvas + uint32(pixel)
	var names []string
	for _, same := range []bool{false, true} {
		n := hdSmallClone(p)
		n.h.m.Mem[0x1cd74] ^= 1
		v := n.h.m.Mem[addr]
		old := v
		name := "unknown-same-write"
		if !same {
			v ^= 1
			name = "unknown-changed-write"
		}
		n.h.m.Mem[addr] = v
		n.write(addr, old, v)
		if n.visible[pixel].owned || paint(n) != baseline-1 {
			t.Fatal("小圖像未知寫入未撤銷", a.ordinal, name)
		}
		names = append(names, name)
	}
	n := hdSmallClone(p)
	n.h.m.Mem[addr] ^= 1
	if paint(n) != baseline-1 {
		t.Fatal("小圖像過期像素仍繪製")
	}
	names = append(names, "stale-native-pixel")
	n = hdSmallClone(p)
	n.pending[pixel] = hdSmallPending{cell: n.visible[pixel]}
	n.h.m.Mem[0x1cd74] ^= 1
	n.write(addr, n.h.m.Mem[addr], n.h.m.Mem[addr])
	if len(n.pending) != 0 {
		t.Fatal("小圖像未知寫入未清除配對")
	}
	names = append(names, "interleaved-cursor-pair")
	for _, tc := range []struct {
		name string
		at   int
	}{{"unknown-cursor-source", 0x1cd74}, {"incomplete-cursor-buffer", 0xafb00}} {
		n = hdSmallClone(p)
		n.h.m.Mem[tc.at] ^= 1
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		_, r := n.h.base(g)
		if r["reason"] != "unverified-cursor-or-native-surface" || r["small"] != nil {
			t.Fatal("小圖像未知游標未回退", tc.name)
		}
		names = append(names, tc.name)
	}
	raw, err := os.ReadFile(filepath.Join(os.Getenv("TEST_HD_SMALL_ASSETS"), a.file))
	if err != nil {
		t.Fatal(err)
	}
	raw[len(raw)-1] ^= 1
	bad := filepath.Join(t.TempDir(), a.file)
	if err = os.WriteFile(bad, raw, 0644); err != nil {
		t.Fatal(err)
	}
	before := hash(p.h.m.Mem)
	if _, err = hdSmallRead(bad, a.artSHA, 8<<20); err == nil || hash(p.h.m.Mem) != before {
		t.Fatal("小圖像錯素材未拒絕或改寫DOS")
	}
	return append(names, "wrong-art-sha256")
}
func TestHDSmallRuntimeNativeLifecycle(t *testing.T) {
	game, assets, receipts := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_HD_RECEIPTS")
	for _, name := range []string{"OPENING.EXE", "VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "ICONS.SS"} {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版", name)
		}
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	load := func(path string) []byte { t.Helper(); b, e := os.ReadFile(path); need(e); return b }
	inputBytes := load(filepath.Join(receipts, "lifecycle-r29-r1/gui/gui.inputs.json"))
	pointBytes := load(filepath.Join(receipts, "lifecycle-public-r29-r1/observed/gui-points.json"))
	if hash(inputBytes) != "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca" || hash(pointBytes) != "821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901" {
		t.Fatal("正常輸入或49點收據不同")
	}
	var replay windowReceipt
	need(json.Unmarshal(inputBytes, &replay))
	var points []struct {
		Step      uint64    `json:"step"`
		Count     uint64    `json:"dos_input_count"`
		Memory    string    `json:"memory_sha256"`
		Indexed   string    `json:"indexed_sha256"`
		Palette   string    `json:"palette_sha256"`
		Registers [8]uint16 `json:"registers"`
		Segments  [4]uint16 `json:"segments"`
		IP        uint16    `json:"ip"`
		Flags     uint16    `json:"flags"`
	}
	need(json.Unmarshal(pointBytes, &points))
	if len(points) != 49 || len(replay.Inputs) != 53 || replay.End != 134600000 {
		t.Fatal("正常路徑規模不同")
	}
	seed := load(filepath.Join(receipts, "lifecycle-r29-r1/gui/save/COLONY09.SAV"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("原始存檔不同")
	}
	scratch := t.TempDir()
	need(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	need(m.LoadEXE(load(filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("缺少數位音效")
	}
	m.EnableOPLSynth(true)
	before := hash(m.Mem)
	h, err := loadHDRuntime(m, game, assets)
	need(err)

	if h.small == nil || len(h.small.frames) != 31 || hash(m.Mem) != before {
		t.Fatal("小圖像載入失敗或改寫DOS")
	}
	p := h.small
	p.trace = true
	negatives := map[int][]string{}
	entryChecked, writerChecked, finishChecked, ownerChecked := map[int]bool{}, map[int]bool{}, map[int]bool{}, map[int]bool{}
	ramChecked := map[bool]bool{}
	ramNegatives := map[string][]string{}
	prior := uint64(0)
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		c := m.CPU
		if c.Seg[golem.CS] == 0xcba && c.IP == 0xca && c.R[golem.CX] > 0 && !c.Flag(golem.DF) {
			for offset := 0; offset < int(c.R[golem.CX])*2; offset++ {
				if int(c.R[golem.SI])+offset >= 65536 || int(c.R[golem.DI])+offset >= 65536 {
					break
				}
				src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + offset
				dst := int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]) + offset
				save := src >= int(hdBuildingCanvas) && src < int(hdBuildingCanvas)+64000 && p.visible[src-int(hdBuildingCanvas)].owned && (dst < int(hdBuildingCanvas) || dst >= int(hdBuildingCanvas)+64000) && (dst < int(hdSeaStage) || dst >= int(hdSeaStage)+64000) && dst+1 < 0xa0000
				restore := dst >= int(hdBuildingCanvas) && dst < int(hdBuildingCanvas)+64000 && p.backing[uint32(src)].owned
				if save && !ramChecked[true] {
					ramNegatives["save"] = hdSmallRAMNegatives(t, p, true, offset)
					ramChecked[true] = true
				}
				if restore && !ramChecked[false] {
					ramNegatives["restore"] = hdSmallRAMNegatives(t, p, false, offset)
					ramChecked[false] = true
				}
			}
		}
		if p.accepted != prior {
			n := p.frames[p.selected].ordinal
			if !finishChecked[n] {
				negatives[n] = append(negatives[n], hdSmallFinishNegatives(t, p)...)
				finishChecked[n] = true
			}
			prior = p.accepted
		}
		if p.active {
			n := p.frames[p.selected].ordinal
			if !entryChecked[n] {
				negatives[n] = append(negatives[n], hdSmallEntryNegatives(t, p)...)
				entryChecked[n] = true
			}
			if !writerChecked[n] && m.CPU.Seg[golem.CS] == 0xd46 && hdSmallWriterCodes[m.CPU.IP] != nil {
				negatives[n] = append(negatives[n], hdSmallWriterNegative(t, p))
				writerChecked[n] = true
			}
		}
	})
	at, count := 0, uint64(0)
	var records []map[string]any
	var guardPoints []int
	capture := func() {
		if at == len(points) {
			return
		}
		point := points[at]
		if m.Steps > point.Step || (m.Steps == point.Step && count > point.Count) {
			t.Fatal("略過原版檢查點", at)
		}
		if m.Steps != point.Step || count != point.Count {
			return
		}
		c := m.CPU
		if hash(m.Mem) != point.Memory || hash(m.Indexed()) != point.Indexed || hash(m.DAC[:]) != point.Palette || c.R != point.Registers || c.Seg != point.Segments || c.IP != point.IP || c.Flags != point.Flags {
			t.Fatal("小圖像改變原版完整狀態", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), step: m.Steps, mode: m.VideoMode()}
		ram, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		var oracle map[string]struct {
			Ordinal int
			Local   int
			Native  byte
		}
		need(json.Unmarshal(load(filepath.Join(os.Getenv("TEST_HD_SMALL_MODEL"), fmt.Sprintf("point-%03d.terrain-model.json", at))), &oracle))
		for pos, cell := range p.visible {
			if !cell.owned {
				continue
			}
			expected, ok := oracle[fmt.Sprint(pos)]
			if !ok || expected.Ordinal != p.frames[cell.slot].ordinal || expected.Local != int(cell.local) || expected.Native != cell.native || f.canvas[pos] != cell.native {
				t.Fatal("小圖像沒有獨立逐點證據", at, pos, cell)
			}
		}
		ownedCount := 0
		for _, cell := range p.visible {
			if cell.owned {
				ownedCount++
			}
		}
		if ownedCount != len(oracle) {
			t.Fatal("小圖像來源少於獨立模型", at, ownedCount, len(oracle))
		}
		output, record := h.base(f)
		h.restoreCursor(output, f)
		receipt := p.receipt(f)
		if record["reason"] == "known-building" {
			artOwned := 0
			for _, cell := range p.visible {
				if cell.owned && p.frames[cell.slot].art != nil {
					artOwned++
				}
			}
			if artOwned > 0 {
				actual, ok := record["small"].(map[string]any)
				if !ok || actual["painted"].(int) <= 0 {
					t.Fatal("小圖像正常狀態未合成", at)
				}
			}
			for slot, a := range p.frames {
				r := receipt["sources"].(map[string]any)[fmt.Sprint(a.ordinal)].(map[string]any)
				if r["owned"].(int) > 0 && !ownerChecked[a.ordinal] {
					negatives[a.ordinal] = append(negatives[a.ordinal], hdSmallOwnershipNegatives(t, p, f, slot)...)
					ownerChecked[a.ordinal] = true
				}
			}
		} else {
			if record["small"] != nil {
				t.Fatal("守門回退仍繪小圖像")
			}
			guardPoints = append(guardPoints, at)
		}
		allowed := [64000]bool{}
		for i, v := range h.owned {
			if v {
				allowed[hdBuildingCanvasIndex(i)] = true
			}
		}
		for i, v := range h.sea.visible {
			if v.owned && v.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, v := range h.person.visible {
			if v.owned && v.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, v := range h.shelter.visible {
			if v.owned && v.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, v := range h.nine.visible {
			if v.owned && v.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, v := range p.visible {
			if v.owned && v.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, v := range h.terrain079.visible {
			if v.owned && v.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, cell := range h.terrainBatch.visible {
			if cell.owned && cell.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, cell := range h.smallTerrain.visible {
			if cell.owned && cell.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		native := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if !allowed[(y/4)*320+x/4] && output.RGBAAt(x, y) != native.RGBAAt(x, y) {
					t.Fatal("小圖像越出已驗像素", at, x, y)
				}
			}
		}
		if at == 4 || at == 9 || at == 20 || at == 37 || at == 44 {
			root := os.Getenv("TEST_HD_SMALL_OUTPUT") + "-samples"
			if err := os.MkdirAll(root, 0755); err != nil {
				t.Fatal(err)
			}
			smallOnly := draftRGB(f.indexed, f.palette)
			smallReceipt := map[string]any{}
			if record["reason"] == "known-building" {
				smallReceipt = p.paint(smallOnly, f)
				h.restoreCursor(smallOnly, f)
			}
			for name, im := range map[string]*image.RGBA{"original": native, "small-only": smallOnly, "all-hd": output} {
				file, err := os.Create(filepath.Join(root, fmt.Sprintf("point-%03d-%s.png", at, name)))
				need(err)
				need(png.Encode(file, im))
				need(file.Close())
			}
			dumpJSON(filepath.Join(root, fmt.Sprintf("point-%03d.json", at)), map[string]any{"point": at, "small": smallReceipt, "cells": oracle, "cursor": f.cursor, "cursor_source_sha256": hash(m.Mem[0x1cd74:0x1ce74])})
		}
		if hash(m.Mem) != ram || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("小圖像合成改寫原版", at)
		}
		records = append(records, map[string]any{"point": at, "step": m.Steps, "small": receipt, "hd": record, "original_state_equal": true})
		at++
	}
	for _, e := range replay.Inputs {
		for m.Steps < e.Step {
			capture()
			need(m.Step())
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < replay.End {
		capture()
		need(m.Step())
	}
	capture()
	if at != 49 || count != 53 || p.accepted != 420 || p.rejected != 0 {
		t.Fatal("小圖像原版路徑不同", at, count, p.accepted, p.rejected)
	}
	for _, f := range p.frames {
		if !entryChecked[f.ordinal] || !writerChecked[f.ordinal] || !finishChecked[f.ordinal] || !ownerChecked[f.ordinal] || len(negatives[f.ordinal]) != map[bool]int{true: 20, false: 17}[f.art != nil] {
			t.Fatal("小圖像反例缺漏", f.ordinal, negatives[f.ordinal])
		}
	}
	if !ramChecked[true] || !ramChecked[false] {
		t.Fatal("缺少RAM反例真實來源")
	}
	if p.bufferSaves != 547 || p.bufferRestores != 422 || len(p.pairs) != 260 {
		t.Fatal("小圖像還原統計不同", p.bufferSaves, p.bufferRestores, len(p.pairs))
	}
	for _, name := range []string{"COLONY00.SAV", "COLONY09.SAV"} {
		if !bytes.Equal(load(filepath.Join(scratch, name)), load(filepath.Join(receipts, "lifecycle-r29-r1/gui/save", name))) {
			t.Fatal("小圖像改變原版存檔", name)
		}
	}
	target := os.Getenv("TEST_HD_SMALL_OUTPUT")
	if target == "" {
		t.Fatal("缺少小圖像收據輸出")
	}
	need(os.Mkdir(target, 0755))
	data, err := json.MarshalIndent(map[string]any{"result": "PASS_SMALL_RUNTIME_NATIVE_49", "production_connected": true, "points": records, "accepted": p.accepted, "rejected": p.rejected, "dos_inputs": count, "end": m.Steps, "negative_cases": negatives, "guard_points": guardPoints, "calls": p.calls, "cursor_pairs": p.pairs, "buffer_saves": p.bufferSaves, "buffer_restores": p.bufferRestores, "peak_buffered": p.peakBuffered, "ram_negative_cases": ramNegatives}, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(target, "check.json"), append(data, '\n'), 0644))
}

func hdSmallRAMNegatives(t *testing.T, p *hdSmallRuntime, save bool, offset int) []string {
	t.Helper()
	c := p.h.m.CPU
	src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + offset
	dst := int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]) + offset
	expected := p.backing[uint32(src)]
	if save {
		expected = p.visible[src-int(hdBuildingCanvas)]
	}
	step := func(n *hdSmallRuntime) {
		target := int(n.h.m.CPU.Seg[golem.ES])*16 + int(n.h.m.CPU.R[golem.DI]) + offset
		seen := false
		n.h.m.WatchWrite(0, 0x9ffff, func(_ *golem.Machine, a uint32, o, v byte) {
			if int(a) == target {
				seen = true
			}
			n.memoryWrite(a, o, v)
		})
		if err := n.h.m.CPU.Step(); err != nil {
			t.Fatal(err)
		}
		if !seen {
			t.Fatal("RAM反例未寫入真實搬移範圍", save, offset, target)
		}
	}
	owned := func(n *hdSmallRuntime, addr int) hdSmallCell {
		if addr >= int(hdBuildingCanvas) && addr < int(hdBuildingCanvas)+64000 {
			return n.visible[addr-int(hdBuildingCanvas)]
		}
		return n.backing[uint32(addr)]
	}
	positive := hdSmallClone(p)
	step(positive)
	if got := owned(positive, dst); !got.owned || got != expected {
		t.Fatal("真實RAM複製未接受", save, src, dst, got, expected)
	}
	cases := []struct {
		name   string
		change func(*hdSmallRuntime)
	}{
		{"unknown-code", func(n *hdSmallRuntime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)+15] ^= 1 }},
		{"unaccepted-site", func(n *hdSmallRuntime) {
			copy(n.h.m.Mem[0xc9f0+0xca:0xc9f0+0xca+16], n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP):int(c.Seg[golem.CS])*16+int(c.IP)+16])
			n.h.m.CPU.Seg[golem.CS] = 0xc9f
		}},
		{"unowned-source", func(n *hdSmallRuntime) { n.h.m.CPU.Seg[golem.DS] = 0 }},
		{"stale-source-byte", func(n *hdSmallRuntime) { n.h.m.Mem[src] ^= 1 }},
		{"wrapped-source", func(n *hdSmallRuntime) { n.h.m.CPU.R[golem.SI] = 65535 }},
		{"unaccepted-destination", func(n *hdSmallRuntime) {
			n.h.m.CPU.R[golem.DI] = 0
			if save {
				n.h.m.CPU.Seg[golem.ES] = uint16(hdSeaStage / 16)
			} else {
				n.h.m.CPU.Seg[golem.ES] = 0
			}
		}},
	}
	var names []string
	for _, tc := range cases {
		n := hdSmallClone(p)
		tc.change(n)
		target := int(n.h.m.CPU.Seg[golem.ES])*16 + int(n.h.m.CPU.R[golem.DI]) + offset
		step(n)
		if got := owned(n, target); got.owned {
			t.Fatal("RAM反例仍授予來源", save, tc.name, target, got)
		}
		names = append(names, tc.name)
	}
	for _, same := range []bool{false, true} {
		n := hdSmallClone(positive)
		n.h.m.WatchWrite(0, 0x9ffff, func(_ *golem.Machine, a uint32, o, v byte) { n.memoryWrite(a, o, v) })
		value := n.h.m.Mem[dst]
		name := "unknown-same-write"
		if !same {
			value ^= 1
			name = "unknown-changed-write"
		}
		n.h.m.Write8(uint32(dst), value)
		if got := owned(n, dst); got.owned {
			t.Fatal("RAM或主畫布未知寫入未撤銷", save, name, got)
		}
		names = append(names, name)
	}
	return names
}

func TestHDSmallResourceContract(t *testing.T) {
	game, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_SMALL_ASSETS")
	if game == "" || assets == "" {
		t.Skip("需合法原版與小圖像候選")
	}
	icons, err := os.ReadFile(filepath.Join(game, "ICONS.SS"))
	if os.IsNotExist(err) {
		t.Skip("缺合法ICONS.SS")
	}
	if err != nil {
		t.Fatal(err)
	}
	m := golem.New()
	before := bytes.Clone(m.Mem)
	h := &hdRuntime{m: m}
	p, err := loadHDSmallRuntime(h, game, assets)
	if err != nil {
		t.Fatal(err)
	}
	if len(p.frames) != 31 || !bytes.Equal(before, m.Mem) {
		t.Fatal("素材載入來源或原版記憶體不同")
	}
	available := map[int]bool{}
	for _, f := range p.frames {
		if f.art != nil {
			available[f.ordinal] = true
		}
	}
	if len(available) != 30 || !available[5] || !available[22] || !available[23] || !available[24] || !available[25] || !available[26] || !available[27] || !available[28] || !available[29] || !available[30] || !available[31] || !available[32] || !available[33] || !available[34] || !available[35] || !available[36] || !available[37] || !available[38] || !available[42] || !available[53] || !available[56] || !available[59] || !available[62] || !available[67] || !available[68] || !available[69] || !available[94] || !available[122] || !available[123] || !available[124] {
		t.Fatal("尚無候選來源被計為HD", available)
	}
	if _, err := loadHDSmallRuntime(nil, game, assets); err == nil {
		t.Fatal("缺少HD仍接受")
	}
	if _, err := loadHDSmallRuntime(h, game, ""); err == nil {
		t.Fatal("缺少素材路徑仍接受")
	}
	names := []string{"missing-icons", "wrong-icons", "linked-icons"}
	for _, f := range p.frames {
		if f.file != "" {
			for _, kind := range []string{"missing", "wrong", "linked", "truncated"} {
				names = append(names, kind+"-"+f.file)
			}
		}
	}
	for _, name := range names {
		a, g := filepath.Join(t.TempDir(), "assets"), filepath.Join(t.TempDir(), "game")
		for _, dir := range []string{a, g} {
			if err := os.Mkdir(dir, 0755); err != nil {
				t.Fatal(err)
			}
		}
		if err := os.WriteFile(filepath.Join(g, "ICONS.SS"), icons, 0644); err != nil {
			t.Fatal(err)
		}
		for _, f := range p.frames {
			if f.file != "" {
				raw, err := os.ReadFile(filepath.Join(assets, f.file))
				if err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(a, f.file), raw, 0644); err != nil {
					t.Fatal(err)
				}
			}
		}
		if name == "missing-icons" {
			err = os.Remove(filepath.Join(g, "ICONS.SS"))
		} else if name == "wrong-icons" {
			err = os.WriteFile(filepath.Join(g, "ICONS.SS"), []byte("wrong"), 0644)
		} else if name == "linked-icons" {
			err = os.Remove(filepath.Join(g, "ICONS.SS"))
			if err == nil {
				err = os.Symlink(filepath.Join(game, "ICONS.SS"), filepath.Join(g, "ICONS.SS"))
			}
		} else {
			for _, f := range p.frames {
				if f.file == "" {
					continue
				}
				path := filepath.Join(a, f.file)
				switch name {
				case "missing-" + f.file:
					err = os.Remove(path)
				case "wrong-" + f.file:
					err = os.WriteFile(path, []byte("wrong"), 0644)
				case "truncated-" + f.file:
					raw, e := os.ReadFile(path)
					err = e
					if err == nil {
						err = os.WriteFile(path, raw[:32], 0644)
					}
				case "linked-" + f.file:
					err = os.Remove(path)
					if err == nil {
						err = os.Symlink(filepath.Join(assets, f.file), path)
					}
				}
			}
		}
		if err != nil {
			t.Fatal(err)
		}
		m := golem.New()
		before := bytes.Clone(m.Mem)
		if p, err := loadHDSmallRuntime(&hdRuntime{m: m}, g, a); err == nil || p != nil {
			t.Fatal("錯件未拒絕", name)
		}
		if !bytes.Equal(before, m.Mem) {
			t.Fatal("錯件載入改寫原版", name)
		}
	}
	fmt.Println("PASS_SMALL_IMAGE_RESOURCE_REJECTIONS", len(names)+2)
}
