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
	"sort"
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

	if h.small == nil || len(h.small.frames) != 124 || hash(m.Mem) != before {
		t.Fatal("小圖像載入失敗或改寫DOS")
	}
	p := h.small
	hdSmallHistorical80Fixture(t, p)
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
		// R57小圖像邊界只核對本層；R66以後的背景沿各自獨立驗收。
		sourceOnly := draftRGB(f.indexed, f.palette)
		_, cursorReason := h.cursorProof(f)
		if cursorReason == "" {
			p.paint(sourceOnly, f)
			h.restoreCursor(sourceOnly, f)
		}
		receipt := p.receipt(f)
		if cursorReason == "" {
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
		for i, cell := range p.visible {
			if cell.owned && cell.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		native := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if !allowed[(y/4)*320+x/4] && sourceOnly.RGBAAt(x, y) != native.RGBAAt(x, y) {
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
			if cursorReason == "" {
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
		// R49固定路徑只涵蓋規格065原31幀；其他來源由各自正常路徑驗證。
		switch f.ordinal {
		case 5, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 42, 53, 56, 59, 62, 67, 68, 69, 94, 100, 122, 123, 124:
		default:
			continue
		}
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
	data, err := json.MarshalIndent(map[string]any{"result": "PASS_SMALL_RUNTIME_NATIVE_49", "pixel_comparison_scope": "small-only; newer backgrounds retain their independent conformance", "production_connected": true, "points": records, "accepted": p.accepted, "rejected": p.rejected, "dos_inputs": count, "end": m.Steps, "negative_cases": negatives, "guard_points": guardPoints, "calls": p.calls, "cursor_pairs": p.pairs, "buffer_saves": p.bufferSaves, "buffer_restores": p.bufferRestores, "peak_buffered": p.peakBuffered, "ram_negative_cases": ramNegatives}, "", "  ")
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
	if len(p.frames) != 124 || !bytes.Equal(before, m.Mem) {
		t.Fatal("素材載入來源或原版記憶體不同")
	}
	available := map[int]bool{}
	for _, f := range p.frames {
		if f.art != nil {
			available[f.ordinal] = true
		}
	}
	wantedAvailable := []int{113, 54, 3, 11, 118, 5, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 42, 53, 56, 59, 62, 67, 68, 69, 94, 122, 123, 124, 6, 7, 14, 15, 127, 8, 9, 16, 58, 60, 66, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 95, 96, 97, 98, 106, 107, 65, 73, 74, 75, 76, 77, 101, 102, 103, 104, 105, 109, 110, 111, 112, 125, 126, 128, 129, 0, 1, 2, 10, 12, 13, 17, 18, 19, 20, 21, 39, 40, 41, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 55, 57, 61, 63, 64, 99, 108, 114, 115, 116, 117, 119, 120, 121, 130}
	if len(available) != 123 {
		t.Fatal("小圖像素材集合不同", available)
	}
	for _, ordinal := range wantedAvailable {
		if !available[ordinal] {
			t.Fatal("已READY素材未載入", ordinal)
		}
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
	sort.Strings(names)
	if path := os.Getenv("TEST_HD_SMALL_RESOURCE_CASE_CATALOG"); path != "" {
		raw, e := json.Marshal(names)
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(path, raw, 0644); e != nil {
			t.Fatal(e)
		}
		if os.Getenv("TEST_HD_SMALL_RESOURCE_CASE_CATALOG_ONLY") == "1" {
			return
		}
	}
	if path := os.Getenv("TEST_HD_SMALL_RESOURCE_CASE_SELECTION"); path != "" {
		raw, e := os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
		var selected []string
		if e = json.Unmarshal(raw, &selected); e != nil {
			t.Fatal(e)
		}
		if len(selected) == 0 {
			t.Fatal("小圖像資源批次不可為空")
		}
		known := map[string]bool{}
		for _, name := range names {
			known[name] = true
		}
		seen := map[string]bool{}
		for _, name := range selected {
			if !known[name] || seen[name] {
				t.Fatal("小圖像資源案例不存在或重複", name)
			}
			seen[name] = true
		}
		names = selected
	}

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
	if _, e := loadHDSmallRuntime(&hdRuntime{m: golem.New()}, g, a); e != nil {
		t.Fatal("完整小圖像測試副本無法載入", e)
	}
	restoreFixture := hdRestoreResourceFixture(t, a, g)
	for _, name := range names {
		t.Run(name, func(t *testing.T) {
			defer restoreFixture(t)
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
		})
	}
	fmt.Println("PASS_SMALL_IMAGE_RESOURCE_REJECTIONS", len(names)+2)
}

// 規格070 R72：五艘船的獨立正常來源、游標及真實反例。
type hdSmallNativeFixture struct {
	isolatedArt                                                                                bool
	inputPath, pointPath, inputSHA, pointSHA, modelDir, outputEnv, imageKey, result, pointsKey string
	points, inputs, positivePoints                                                             int
	inputEnd, end                                                                              uint64
	sources                                                                                    map[int]int
}

func TestHDShipRuntimeNativeLifecycle(t *testing.T) {
	hdSmallNativeLifecycle(t, hdSmallNativeFixture{
		inputPath: "baseline-ships-r5/gui.inputs.json", pointPath: "icons-ships-entry-r1/points.json",
		inputSHA: "639574cafe140655c699c9cc9709208f668af08751bdab4895b875c8673353e1",
		pointSHA: "fd2fc2ee7ba3c7eb63c9250d742a26909b67a19ea83a0157212b8e40a8efd1e8",
		modelDir: "ships-ram-r1/model-r1", outputEnv: "TEST_HD_SHIP_OUTPUT", imageKey: "ships",
		result: "PASS_FIVE_SHIP_RUNTIME_NATIVE_24", pointsKey: "ship_points",
		points: 24, inputs: 109, positivePoints: 15, inputEnd: 227600000, end: 227400000,
		sources: map[int]int{6: 121, 7: 143, 14: 127, 15: 125, 127: 137},
	})
}
func TestHDVehicleRuntimeNativeLifecycle(t *testing.T) {
	hdSmallNativeLifecycle(t, hdSmallNativeFixture{
		inputPath: "baseline-vehicles-r1/gui.inputs.json", pointPath: "r73-icons-entry-r1/points.json",
		inputSHA: "26f0bcb8bab7fce4fe0ea47c712fd9a236911a7b9cb00f361b4a65c177c934a7", pointSHA: "7221fa287182174aaf80f91879b343a4ec5f04cadade513825ef0ed50c7fa807",
		modelDir: "vehicles-ram-r1/model-r1", outputEnv: "TEST_HD_VEHICLE_OUTPUT", imageKey: "vehicles",
		result: "PASS_THREE_VEHICLE_RUNTIME_NATIVE_18", pointsKey: "vehicle_points",
		points: 18, inputs: 86, positivePoints: 9, inputEnd: 175600000, end: 175200000,
		sources: map[int]int{8: 138, 9: 67, 16: 82}, isolatedArt: true,
	})
}

func TestHDColonistRuntimeNativeLifecycle(t *testing.T) {
	hdSmallNativeLifecycle(t, hdSmallNativeFixture{
		inputPath: "baseline-colonists-r1/gui.inputs.json", pointPath: "r74-icons-entry-r1/points.json",
		inputSHA: "9feb15c45241094ac65f095283c27d5ac8a839d379142feaf9b4f3cc94aad97f",
		pointSHA: "465fb7834d18eca3c105df7d007795bcec6099e6733cff1ac9b798e532385945",
		modelDir: "colonists-ram-r1/model-r1", outputEnv: "TEST_HD_COLONIST_OUTPUT", imageKey: "colonists",
		result: "PASS_COLONIST_22_RUNTIME_NATIVE_54", pointsKey: "colonist_points",
		points: 54, inputs: 81, positivePoints: 45, inputEnd: 156400000, end: 156200000,
		sources: map[int]int{58: 60, 60: 60, 66: 51, 81: 69, 82: 59, 83: 60, 84: 60, 85: 75, 86: 74, 87: 68, 88: 63, 89: 62, 90: 54, 91: 53, 92: 54, 93: 75, 95: 63, 96: 75, 97: 60, 98: 50, 106: 52, 107: 56}, isolatedArt: true,
	})
}

func TestHDUnit19RuntimeNativeLifecycle(t *testing.T) {
	hdSmallNativeLifecycle(t, hdSmallNativeFixture{
		inputPath: "baseline-unit19-r1/gui.inputs.json", pointPath: "r75-icons-entry-r1/points.json",
		inputSHA: "2a2007acb65dfe021ac4d2aa8323561607d505446289a49376aa57476518f24c", pointSHA: "ff19d096b2082c673c2d16cc02543f3d7f6ce0baefdb5025f643e66a575b0eae",
		modelDir: "units19-ram-r1/model-r1", outputEnv: "TEST_HD_UNIT19_OUTPUT", imageKey: "units19",
		result: "PASS_UNIT19_RUNTIME_NATIVE_61", pointsKey: "unit_points",
		points: 61, inputs: 137, positivePoints: 52, inputEnd: 310000000, end: 309600000,
		sources: map[int]int{65: 33, 73: 58, 74: 68, 75: 102, 76: 111, 77: 61, 101: 58, 102: 67, 103: 102, 104: 112, 105: 60, 109: 65, 110: 65, 111: 100, 112: 116, 125: 66, 126: 113, 128: 68, 129: 114}, isolatedArt: true,
	})
}

func hdSmallNativeLifecycle(t *testing.T, fixture hdSmallNativeFixture) {
	root := os.Getenv("TEST_HD_UNIT_NATIVE")
	if root == "" {
		root = os.Getenv("TEST_HD_SHIP_NATIVE")
	}
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
	inputBytes := load(filepath.Join(root, fixture.inputPath))
	pointBytes := load(filepath.Join(root, fixture.pointPath))
	if hash(inputBytes) != fixture.inputSHA || hash(pointBytes) != fixture.pointSHA {
		t.Fatal("固定正常路徑收據不同")
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
	if len(points) != fixture.points || len(replay.Inputs) != fixture.inputs || replay.End != fixture.inputEnd {
		t.Fatal("正常路徑規模不同")
	}
	replay.End = fixture.end // 本批原版oracle終點為最後正常截點。
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

	if h.small == nil || len(h.small.frames) != 124 || hash(m.Mem) != before {
		t.Fatal("小圖像載入失敗或改寫DOS")
	}
	p := h.small
	hdSmallHistorical80Fixture(t, p)
	p.trace = true

	targets := fixture.sources
	negatives := map[int][]string{}
	entryChecked, writerChecked, finishChecked, ownerChecked := map[int]bool{}, map[int]bool{}, map[int]bool{}, map[int]bool{}
	prior := uint64(0)
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		if p.accepted != prior {
			n := p.frames[p.selected].ordinal
			if _, ok := targets[n]; ok && !finishChecked[n] {
				negatives[n] = append(negatives[n], hdSmallFinishNegatives(t, p)...)
				finishChecked[n] = true
			}
			prior = p.accepted
		}
		if p.active {
			n := p.frames[p.selected].ordinal
			if _, ok := targets[n]; !ok {
				return
			}
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
	target := os.Getenv(fixture.outputEnv)
	if target == "" {
		t.Fatal("缺少單位小圖像原版收據輸出")
	}
	need(os.Mkdir(target, 0755))
	at, count := 0, uint64(0)
	var records []map[string]any
	shipPoints, guarded := 0, []int{}
	capture := func() {
		if at == len(points) {
			return
		}
		point := points[at]
		if m.Steps > point.Step || (m.Steps == point.Step && count > point.Count) {
			t.Fatal("略過單位小圖像原版截點", at)
		}
		if m.Steps != point.Step || count != point.Count {
			return
		}
		c := m.CPU
		if hash(m.Mem) != point.Memory || hash(m.Indexed()) != point.Indexed || hash(m.DAC[:]) != point.Palette || c.R != point.Registers || c.Seg != point.Segments || c.IP != point.IP || c.Flags != point.Flags {
			t.Fatal("單位小圖像覆蓋改變原版狀態", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), step: m.Steps, mode: m.VideoMode()}
		type expectedCell struct {
			Ordinal, Local int
			Native         byte
		}
		var oracle map[string]expectedCell
		need(json.Unmarshal(load(filepath.Join(root, fixture.modelDir, fmt.Sprintf("point-%03d.terrain-model.json", at))), &oracle))
		owned := 0
		for pos, cell := range p.visible {
			if !cell.owned {
				continue
			}
			ordinal := p.frames[cell.slot].ordinal
			if _, ok := targets[ordinal]; !ok {
				continue
			}
			expected, ok := oracle[fmt.Sprint(pos)]
			if !ok || expected.Ordinal != ordinal || expected.Local != int(cell.local) || expected.Native != cell.native || f.canvas[pos] != cell.native {
				t.Fatal("單位小圖像來源與獨立模型不同", at, pos, cell)
			}
			owned++
		}
		if owned != len(oracle) {
			t.Fatal("單位小圖像來源缺漏", at, owned, len(oracle))
		}
		before, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		_, reason := h.cursorProof(f)
		if reason != "" {
			if len(oracle) != 0 || (at != 1 && at != 2) {
				t.Fatal("單位小圖像出現未知游標表面", at, reason)
			}
			guarded = append(guarded, at)
		}
		if len(oracle) > 0 {
			shipPoints++
			if reason != "" {
				t.Fatal("單位小圖像游標契約未通過", at)
			}
			only := draftRGB(f.indexed, f.palette)
			painter := p
			if fixture.isolatedArt {
				// 只隔離本批來源的像素測試；正式GUI另驗完整HD合成。
				copyRuntime := *p
				copyRuntime.frames = append([]hdSmallFrame(nil), p.frames...)
				for i := range copyRuntime.frames {
					if _, ok := targets[copyRuntime.frames[i].ordinal]; !ok {
						copyRuntime.frames[i].art = nil
					}
				}
				painter = &copyRuntime
			}
			receipt := painter.paint(only, f)
			h.restoreCursor(only, f)
			for slot, a := range p.frames {
				expectedPaint, ok := targets[a.ordinal]
				if !ok {
					continue
				}
				r := receipt["sources"].(map[string]any)[fmt.Sprint(a.ordinal)].(map[string]any)
				if r["owned"].(int) > 0 {
					if r["painted"].(int) != expectedPaint {
						t.Fatal("單位小圖像原alpha繪製格不同", at, a.ordinal, r)
					}
					if !ownerChecked[a.ordinal] {
						negatives[a.ordinal] = append(negatives[a.ordinal], hdSmallOwnershipNegatives(t, p, f, slot)...)
						ownerChecked[a.ordinal] = true
					}
				}
			}
			mask := map[int]bool{}
			for key := range oracle {
				var pos int
				if _, e := fmt.Sscan(key, &pos); e != nil {
					t.Fatal(e)
				}
				mask[pos] = true
			}
			native := draftRGB(f.indexed, f.palette)
			for y := 0; y < 800; y++ {
				for x := 0; x < 1280; x++ {
					if !mask[(y/4)*320+x/4] && only.RGBAAt(x, y) != native.RGBAAt(x, y) {
						t.Fatal("單位小圖像越出有效來源", at, x, y)
					}
				}
			}
			for name, im := range map[string]*image.RGBA{"original": native, fixture.imageKey: only} {
				file, e := os.Create(filepath.Join(target, fmt.Sprintf("point-%03d-%s.png", at, name)))
				need(e)
				need(png.Encode(file, im))
				need(file.Close())
			}
			file, e := os.Create(filepath.Join(target, fmt.Sprintf("point-%03d-art.png", at)))
			need(e)
			for _, a := range p.frames {
				if _, ok := targets[a.ordinal]; ok && a.accepted > 0 && receipt["sources"].(map[string]any)[fmt.Sprint(a.ordinal)].(map[string]any)["owned"].(int) > 0 {
					need(png.Encode(file, a.art))
					break
				}
			}
			need(file.Close())
			dumpJSON(filepath.Join(target, fmt.Sprintf("point-%03d.json", at)), map[string]any{"point": at, "cells": oracle, "small": receipt, "cursor": f.cursor, "cursor_source_sha256": hash(m.Mem[0x1cd74:0x1ce74])})
		}
		if hash(m.Mem) != before || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("單位小圖像合成改寫原版", at)
		}
		records = append(records, map[string]any{"point": at, "step": m.Steps, "ship_owned": owned, "cursor_reason": reason, "original_state_equal": true})
		at++
	}
	for _, e := range replay.Inputs {
		if e.Step > replay.End {
			break
		}
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
	if at != fixture.points || count != uint64(fixture.inputs) || shipPoints != fixture.positivePoints || p.rejected != 0 || len(guarded) != 2 {
		t.Fatal("單位小圖像原版路徑未完成", at, count, shipPoints, p.rejected, guarded)
	}
	for _, f := range p.frames {
		if _, ok := targets[f.ordinal]; !ok {
			continue
		}
		if f.accepted != 1 || !entryChecked[f.ordinal] || !writerChecked[f.ordinal] || !finishChecked[f.ordinal] || !ownerChecked[f.ordinal] || len(negatives[f.ordinal]) != 20 {
			t.Fatal("單位小圖像真實反例或來源缺漏", f.ordinal, f.accepted, negatives[f.ordinal])
		}
	}
	if !bytes.Equal(load(filepath.Join(scratch, "COLONY09.SAV")), seed) {
		t.Fatal("單位小圖像覆蓋改變存檔")
	}
	dumpJSON(filepath.Join(target, "check.json"), map[string]any{"result": fixture.result, "production_connected": true, "points": records, fixture.pointsKey: shipPoints, "dos_inputs": count, "end": m.Steps, "negative_cases": negatives, "guarded_non_source_points": guarded})
}

// 規格065 R96：正常原版入口快照、錯件及來源複製守門。
type hdScaledSmallDecoderFixture struct {
	Entry struct {
		ResearchID                int `json:"research_id"`
		SourceOrdinal             int `json:"source_ordinal"`
		Registers                 [8]uint16
		Segments                  [4]uint16
		Stack, Record, Descriptor []uint16
		Canvas                    uint32
		SourceFar                 string `json:"source_far"`
	}
	Flags         uint16
	Cycles, Steps uint64
	MemorySHA     string `json:"memory_sha256"`
	MemoryFile    string `json:"memory_file"`
}

func hdScaledSmallFixture(t *testing.T, name, mode string) (*golem.Machine, *hdSmallRuntime, hdScaledSmallDecoderFixture) {
	t.Helper()
	root := hdScaledSmallFixtureRoot(t)
	raw, e := os.ReadFile(filepath.Join(root, name))
	if e != nil {
		t.Fatal(e)
	}
	want, known := hdScaledSmallFixtureSHAs[name]
	if !known || hash(raw) != want[0] {
		t.Fatal("original fixture metadata fingerprint")
	}
	var f hdScaledSmallDecoderFixture
	if e = json.Unmarshal(raw, &f); e != nil {
		t.Fatal(e)
	}
	mem, e := os.ReadFile(filepath.Join(root, f.MemoryFile))
	if e != nil || (hash(mem) != f.MemorySHA || hash(mem) != want[1]) {
		t.Fatal("original fixture", e)
	}
	m := golem.New()
	if len(mem) != len(m.Mem) {
		t.Fatal("original memory length")
	}
	copy(m.Mem, mem)
	m.CPU.R = f.Entry.Registers
	m.CPU.Seg = f.Entry.Segments
	m.CPU.IP = 4
	m.CPU.Flags = f.Flags
	// 局部解碼測試不還原硬體時鐘；正常44點另外核對完整原版週期。
	m.CPU.Cycles = 0
	h := &hdRuntime{m: m}
	p := &hdSmallRuntime{h: h, frames: append([]hdSmallFrame(nil), hdSmallFrames...), pending: map[int]hdSmallPending{}, backing: map[uint32]hdSmallCell{}}
	first := true
	m.WatchWrite(0, 0x9ffff, func(_ *golem.Machine, a uint32, o, v byte) {
		target := p.active && a >= p.destination && a < p.destination+64000
		if target && first {
			first = false
			if mode == "missing" {
				return
			}
			if mode == "wrong-writer" {
				cs, ip := m.CPU.OpAddr()
				at := int(cs)*16 + int(ip) + 15
				old := m.Mem[at]
				m.Mem[at] ^= 1
				p.memoryWrite(a, o, v)
				m.Mem[at] = old
				return
			}
			if mode == "duplicate" {
				p.memoryWrite(a, o, v)
			}
		}
		p.memoryWrite(a, o, v)
	})
	return m, p, f
}
func hdScaledSmallRunDecoder(t *testing.T, m *golem.Machine, p *hdSmallRuntime) {
	t.Helper()
	for i := 0; i < 100000; i++ {
		p.beforeInstruction()
		if !p.active {
			if p.accepted+p.rejected != 1 {
				t.Fatal("decoder never armed", p.accepted, p.rejected)
			}
			return
		}
		if e := m.Step(); e != nil {
			t.Fatal("actual original decoder", e)
		}
	}
	t.Fatal("decoder bound")
}
func hdScaledSmallWord(m *golem.Machine, seg, off uint16, word int, v uint16) {
	binary.LittleEndian.PutUint16(m.Mem[int(seg)*16+int(off)+word*2:], v)
}
func hdScaledSmallFixtureNames(t *testing.T) []string {
	t.Helper()
	paths, e := filepath.Glob(filepath.Join(hdScaledSmallFixtureRoot(t), "r96-decoder-*.json"))
	if e != nil || len(paths) != 5 {
		t.Fatal("five normal Main/Stage fixtures required", paths, e)
	}
	names := []string{}
	for _, p := range paths {
		names = append(names, filepath.Base(p))
	}
	return names
}
func TestHDScaledSourceGuards(t *testing.T) {
	for _, name := range hdScaledSmallFixtureNames(t) {
		t.Run(name, func(t *testing.T) {
			t.Run("actual-original-decoder", func(t *testing.T) {
				m, p, f := hdScaledSmallFixture(t, name, "")
				hdScaledSmallRunDecoder(t, m, p)
				if p.accepted != 1 || p.rejected != 0 {
					t.Fatal("positive")
				}
				owned := 0
				cells := &p.visible
				if f.Entry.Canvas == hdSeaStage {
					cells = &p.stage
				}
				for _, c := range cells {
					if c.owned {
						owned++
					}
				}
				if owned != p.frames[p.selected].opaque {
					t.Fatal("all original opaque cells", owned)
				}
			})
			entryCases := []string{"entry-code", "high-AX", "wrong-frame", "encoded-byte", "source-bank-wrap", "record-width", "record-height", "nominal-word2", "nominal-word3", "scale99", "wrong-surface", "surface-alias", "left-bound", "right-bound", "top-bound", "bottom-bound"}
			for _, kind := range entryCases {
				t.Run(kind, func(t *testing.T) {
					m, p, f := hdScaledSmallFixture(t, name, "")
					c := m.CPU
					stSeg, stOff := c.Seg[golem.SS], c.R[golem.SP]
					recSeg, recOff := f.Entry.Stack[5], f.Entry.Stack[4]+0x36+c.R[golem.AX]*12
					descSeg, descOff := c.Seg[golem.DS], c.R[golem.BX]
					switch kind {
					case "entry-code":
						m.Mem[int(c.Seg[golem.CS])*16+4] ^= 1
					case "high-AX":
						c.R[golem.AX] |= 0x8000
					case "wrong-frame":
						c.R[golem.AX]++
					case "encoded-byte":
						m.Mem[int(f.Entry.Record[1])*16+int(f.Entry.Record[0])] ^= 1
					case "source-bank-wrap":
						hdScaledSmallWord(m, recSeg, recOff, 0, 0xfffe)
					case "record-width":
						hdScaledSmallWord(m, recSeg, recOff, 4, f.Entry.Record[4]+1)
					case "record-height":
						hdScaledSmallWord(m, recSeg, recOff, 5, f.Entry.Record[5]+1)
					case "nominal-word2":
						hdScaledSmallWord(m, recSeg, recOff, 2, f.Entry.Record[2]+1)
					case "nominal-word3":
						hdScaledSmallWord(m, recSeg, recOff, 3, f.Entry.Record[3]+1)
					case "scale99":
						hdScaledSmallWord(m, stSeg, stOff, 2, 99)
					case "wrong-surface":
						hdScaledSmallWord(m, descSeg, descOff, 3, 0x4000)
					case "surface-alias":
						hdScaledSmallWord(m, descSeg, descOff, 2, 16)
						hdScaledSmallWord(m, descSeg, descOff, 3, f.Entry.Descriptor[3]-1)
					case "left-bound":
						c.R[golem.DX] = 0
					case "right-bound":
						c.R[golem.DX] = 319
					case "top-bound":
						hdScaledSmallWord(m, stSeg, stOff, 3, 0)
					case "bottom-bound":
						hdScaledSmallWord(m, stSeg, stOff, 3, 200)
					}
					p.beforeInstruction()
					if p.active || p.accepted != 0 {
						t.Fatal("near match armed", kind)
					}
				})
			}
			for _, kind := range []string{"missing", "duplicate", "wrong-writer"} {
				t.Run(kind, func(t *testing.T) {
					m, p, _ := hdScaledSmallFixture(t, name, kind)
					hdScaledSmallRunDecoder(t, m, p)
					if p.accepted != 0 || p.rejected != 1 {
						t.Fatal("incomplete source accepted", kind)
					}
				})
			}
			t.Run("wrong-return-SP", func(t *testing.T) {
				m, p, f := hdScaledSmallFixture(t, name, "")
				p.beforeInstruction()
				if !p.active {
					t.Fatal("entry")
				}
				m.CPU.Seg[golem.CS] = f.Entry.Stack[1]
				m.CPU.IP = f.Entry.Stack[0]
				m.CPU.R[golem.SP] = f.Entry.Registers[golem.SP] + 10
				p.beforeInstruction()
				if !p.active || p.accepted != 0 {
					t.Fatal("SP10 accepted as SP12")
				}
			})
			t.Run("bounded-return", func(t *testing.T) {
				m, p, _ := hdScaledSmallFixture(t, name, "")
				p.beforeInstruction()
				if e := m.Step(); e != nil {
					t.Fatal(e)
				}
				m.Steps = p.start + 100001
				p.beforeInstruction()
				if p.active || p.accepted != 0 || p.rejected != 1 {
					t.Fatal("unbounded return")
				}
			})
			t.Run("unknown-same-value-revokes", func(t *testing.T) {
				m, p, f := hdScaledSmallFixture(t, name, "")
				hdScaledSmallRunDecoder(t, m, p)
				cells := &p.visible
				if f.Entry.Canvas == hdSeaStage {
					cells = &p.stage
				}
				for i, c := range cells {
					if c.owned {
						m.Write8(f.Entry.Canvas+uint32(i), c.native)
						if cells[i].owned {
							t.Fatal("same value restored source")
						}
						return
					}
				}
				t.Fatal("positive cell missing")
			})
		})
	}
}
func TestHDScaledPaletteScope(t *testing.T) {
	hdScaledSmallFixtureRoot(t)
	path := os.Getenv("TEST_HD_SCALED_PALETTE")
	if path == "" {
		t.Skip("缺少固定原版DAC收據")
	}
	pal, e := os.ReadFile(path)
	if e != nil || hash(pal) != "94c4b1630d99483212fc8bd85dec3751ffd0d9423eedb395dc0004e9f823976b" {
		t.Fatal("原版DAC指紋", e)
	}
	used := map[byte]bool{}
	for _, name := range []string{"r96-decoder-830-3c500.json", "r96-decoder-838-3c500.json", "r96-decoder-945-3c500.json"} {
		m, p, _ := hdScaledSmallFixture(t, name, "")
		hdScaledSmallRunDecoder(t, m, p)
		if p.accepted != 1 {
			t.Fatal("實際解碼色號來源")
		}
		for k, n := range p.counts {
			if n == 1 {
				used[p.writes[k]] = true
			}
		}
	}
	if len(used) != 30 {
		t.Fatal("原版已用色號數", len(used))
	}
	t.Run("actual-palette", func(t *testing.T) {
		if !hdSmallScaledPaletteSupported(pal) {
			t.Fatal("palette")
		}
	})
	for i := 0; i < 256; i++ {
		v := byte(i)
		if !used[v] {
			continue
		}
		t.Run(fmt.Sprintf("index-%03d", v), func(t *testing.T) {
			wrong := bytes.Clone(pal)
			wrong[int(v)*3] ^= 1
			if hdSmallScaledPaletteSupported(wrong) {
				t.Fatal("wrong source color accepted", v)
			}
		})
	}
	t.Run("unrelated-color-keeps-scope", func(t *testing.T) {
		for i := 0; i < 256; i++ {
			if !used[byte(i)] {
				wrong := bytes.Clone(pal)
				wrong[i*3] ^= 1
				if !hdSmallScaledPaletteSupported(wrong) {
					t.Fatal("unrelated color")
				}
				return
			}
		}
		t.Fatal("no unused color")
	})
	t.Run("wrong-length", func(t *testing.T) {
		if hdSmallScaledPaletteSupported(pal[:767]) {
			t.Fatal("short palette")
		}
	})
}
func hdScaledSmallAdjacent(t *testing.T, cells *[64000]hdSmallCell) int {
	t.Helper()
	for i := 0; i < 63999; i++ {
		a, b := cells[i], cells[i+1]
		if a.owned && b.owned && a.slot == b.slot {
			return i
		}
	}
	t.Fatal("adjacent actual source cells")
	return 0
}
func hdScaledSmallCopyWord(t *testing.T, m *golem.Machine, src, dest uint32, reverse bool) {
	t.Helper()
	pc := 0xcba0 + 0xca
	want := []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0xc, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}
	if !bytes.Equal(m.Mem[pc:pc+16], want) {
		t.Fatal("actual copy opcode")
	}
	m.CPU.Seg[golem.CS] = 0xcba
	m.CPU.IP = 0xca
	m.CPU.Seg[golem.DS] = uint16(src >> 4)
	m.CPU.R[golem.SI] = uint16(src & 15)
	m.CPU.Seg[golem.ES] = uint16(dest >> 4)
	m.CPU.R[golem.DI] = uint16(dest & 15)
	m.CPU.R[golem.CX] = 1
	m.CPU.Flags &^= 0x400
	if reverse {
		m.CPU.Flags |= 0x400
	}
	if e := m.Step(); e != nil {
		t.Fatal(e)
	}
}
func TestHDScaledTypedCopies(t *testing.T) {
	stageFixture := "r96-decoder-830-3c500.json"
	mainFixture := "r96-decoder-830-2cae0.json"
	t.Run("actual-Stage-to-Main", func(t *testing.T) {
		m, p, _ := hdScaledSmallFixture(t, stageFixture, "")
		hdScaledSmallRunDecoder(t, m, p)
		i := hdScaledSmallAdjacent(t, &p.stage)
		hdScaledSmallCopyWord(t, m, hdSeaStage+uint32(i), hdBuildingCanvas, false)
		if !p.visible[0].owned || !p.visible[1].owned {
			t.Fatal("valid Stage copy lost")
		}
	})
	t.Run("reverse-copy-rejected", func(t *testing.T) {
		m, p, _ := hdScaledSmallFixture(t, stageFixture, "")
		hdScaledSmallRunDecoder(t, m, p)
		i := hdScaledSmallAdjacent(t, &p.stage)
		hdScaledSmallCopyWord(t, m, hdSeaStage+uint32(i), hdBuildingCanvas, true)
		if p.visible[0].owned || p.visible[1].owned {
			t.Fatal("reverse Stage granted")
		}
	})
	t.Run("Main-save-restore", func(t *testing.T) {
		m, p, _ := hdScaledSmallFixture(t, mainFixture, "")
		hdScaledSmallRunDecoder(t, m, p)
		i := hdScaledSmallAdjacent(t, &p.visible)
		hdScaledSmallCopyWord(t, m, hdBuildingCanvas+uint32(i), 0x80000, false)
		m.Write8(hdBuildingCanvas+uint32(i), m.Mem[hdBuildingCanvas+uint32(i)])
		m.Write8(hdBuildingCanvas+uint32(i+1), m.Mem[hdBuildingCanvas+uint32(i+1)])
		hdScaledSmallCopyWord(t, m, 0x80000, hdBuildingCanvas+uint32(i), false)
		if !p.visible[i].owned || !p.visible[i+1].owned {
			t.Fatal("valid Main backing restore lost")
		}
	})
	t.Run("Main-to-Main-revokes", func(t *testing.T) {
		m, p, _ := hdScaledSmallFixture(t, mainFixture, "")
		hdScaledSmallRunDecoder(t, m, p)
		i := hdScaledSmallAdjacent(t, &p.visible)
		hdScaledSmallCopyWord(t, m, hdBuildingCanvas+uint32(i), hdBuildingCanvas, false)
		if p.visible[0].owned || p.visible[1].owned {
			t.Fatal("Main-to-Main granted")
		}
	})
}

func hdScaledSmallFixtureRoot(t *testing.T) string {
	t.Helper()
	game := os.Getenv("TEST_GAME_ROOT")
	raw, e := os.ReadFile(filepath.Join(game, "ICONS.SS"))
	if os.IsNotExist(e) {
		t.Skip("缺少合法原版ICONS.SS")
	}
	if e != nil || hash(raw) != "a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716" {
		t.Fatal("原版ICONS指紋", e)
	}
	root := os.Getenv("TEST_HD_SCALED_FIXTURES")
	if root == "" {
		t.Skip("缺少正常原版D66入口快照")
	}
	return root
}

var hdScaledSmallFixtureSHAs = map[string][2]string{"r96-decoder-830-2cae0.json": {"94190de6b1c0efd6e18285cb281fef53b8748e907b2d545355e6ce37ee73c8a3", "9ef06ac7d676add91809fd1fe35bc2a3ad986ed430fab806071b798183156847"},
	"r96-decoder-830-3c500.json": {"a8d1825025bad4c2cb6fbe5e8d12137a7e3b25456fef30c96c3da8fac60a7701", "f294ff16aeb27bb33b513bcc73c77ae9a2e0ac8c2fdc98e21cf55252e459151d"},
	"r96-decoder-838-3c500.json": {"7f65681d30806472a4b716d73cba778a736122892dde9aacf63444ddd4278a2f", "9a5b55e474ed2e6f0594cf50f0bb6fa3829aad88dbfb9825a8ba935fc605b390"},
	"r96-decoder-945-2cae0.json": {"bfbb00ebdecf5b4c47700f4559c95e1f5bc901c05aa09388b919aeb3aa915ed7", "78a66877595600dfb4fb9bbf4280515113aa6e7355ff809bfb8201a75dea4b3b"},
	"r96-decoder-945-3c500.json": {"66ccc5bd539f09387cc595cb06cf5276cacd21903b0bbd55abcdef7627614af8", "e862c536a2f5529de29feb416349331f86a1cc1d23cebf4141c4b99163f8c14f"}}

func TestHDScaledSmallResources(t *testing.T) {
	game := os.Getenv("TEST_GAME_ROOT")
	assets := os.Getenv("TEST_HD_ASSETS")
	if assets == "" {
		t.Skip("缺少HD原圖")
	}
	source := filepath.Join(game, "ICONS.SS")
	if _, e := os.Stat(source); os.IsNotExist(e) {
		t.Skip("missing legal original ICONS.SS")
	}
	need := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	read := func(p string) []byte { t.Helper(); b, e := os.ReadFile(p); need(e); return b }
	original := read(source)
	tmp := t.TempDir()
	g, a := filepath.Join(tmp, "game"), filepath.Join(tmp, "assets")
	need(os.Mkdir(g, 0755))
	need(os.Mkdir(a, 0755))
	need(os.WriteFile(filepath.Join(g, "ICONS.SS"), original, 0644))
	names := []string{}
	for _, f := range hdSmallFrames {
		if f.file != "" {
			names = append(names, f.file)
			need(os.WriteFile(filepath.Join(a, f.file), read(filepath.Join(assets, f.file)), 0644))
		}
	}
	if len(hdSmallFrames) != 124 || len(names) != 123 {
		t.Fatal("124 sources and 123 artwork references")
	}
	h := &hdRuntime{m: golem.New()}
	before := bytes.Clone(h.m.Mem)
	positive := func(t *testing.T) {
		t.Helper()
		p, e := loadHDSmallRuntime(h, g, a)
		need(e)
		if len(p.frames) != 124 {
			t.Fatal("positive full loader")
		}
	}
	t.Run("all83-positive-before", positive)
	cases := []string{}
	for _, name := range []string{"icons-003.png", "icons-011.png", "icons-118.png"} {
		for _, kind := range []string{"missing", "wrong", "linked"} {
			key := name + "-" + kind
			cases = append(cases, key)
			t.Run(key, func(t *testing.T) {
				target := filepath.Join(a, name)
				raw := read(target)
				need(os.Remove(target))
				if kind == "wrong" {
					need(os.WriteFile(target, []byte("wrong"), 0644))
				}
				if kind == "linked" {
					need(os.Symlink(filepath.Join(assets, name), target))
				}
				if _, e := loadHDSmallRuntime(h, g, a); e == nil {
					t.Fatal("wrong asset accepted")
				}
				if kind != "missing" {
					need(os.Remove(target))
				}
				need(os.WriteFile(target, raw, 0644))
			})
		}
	}
	for _, kind := range []string{"missing", "wrong", "linked"} {
		key := "original-" + kind
		cases = append(cases, key)
		t.Run(key, func(t *testing.T) {
			target := filepath.Join(g, "ICONS.SS")
			need(os.Remove(target))
			if kind == "wrong" {
				need(os.WriteFile(target, []byte("wrong"), 0644))
			}
			if kind == "linked" {
				need(os.Symlink(source, target))
			}
			if _, e := loadHDSmallRuntime(h, g, a); e == nil {
				t.Fatal("wrong original accepted")
			}
			if kind != "missing" {
				need(os.Remove(target))
			}
			need(os.WriteFile(target, original, 0644))
		})
	}
	cases = append(cases, "nil-runtime", "missing-directory")
	t.Run("nil-runtime", func(t *testing.T) {
		if _, e := loadHDSmallRuntime(nil, g, a); e == nil {
			t.Fatal("nil accepted")
		}
	})
	t.Run("missing-directory", func(t *testing.T) {
		if _, e := loadHDSmallRuntime(h, g, filepath.Join(tmp, "absent")); e == nil {
			t.Fatal("absent assets accepted")
		}
	})
	t.Run("all83-positive-after", positive)
	if !bytes.Equal(before, h.m.Mem) || !bytes.Equal(original, read(source)) {
		t.Fatal("original or RAM modified")
	}
	for _, name := range names {
		if !bytes.Equal(read(filepath.Join(a, name)), read(filepath.Join(assets, name))) {
			t.Fatal("raw asset changed", name)
		}
	}
	record := map[string]any{"result": "PASS_R96_SMALL84_FULL83_ASSETS_AND_FAULT14", "frames": 84, "art_files": 83, "positive_before_and_after": true, "cases": cases, "original_and_RAM_unchanged": true, "all_raw_art_unchanged": true}
	raw, e := json.MarshalIndent(record, "", "  ")
	need(e)
	if out := os.Getenv("TEST_HD_SCALED_RESOURCE_OUTPUT"); out != "" {
		need(os.WriteFile(out, append(raw, '\n'), 0644))
	}
}

// R57／R72至R75的歷史模型限當時80來源。施工槌54及R96縮放來源各有獨立驗收。
// 只縮小這兩組歷史測試的追蹤，不改正式組裝或正常玩家路徑。
func hdSmallHistorical80Fixture(t *testing.T, p *hdSmallRuntime) {
	t.Helper()
	frames := []hdSmallFrame{}
	for _, f := range p.frames {
		if !f.scaled100 && f.ordinal != 54 && f.ordinal != 113 {
			frames = append(frames, f)
		}
	}
	if len(frames) != 80 {
		t.Fatal("歷史80來源群組不同", len(frames))
	}
	p.frames = frames
}

// 規格065 R99 READY：實際顧問頁fixture、原圖與色盤守門。
func r99Load(t *testing.T, path string) []byte {
	t.Helper()
	b, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func r99Frame(t *testing.T) hdSmallFrame {
	for _, f := range hdSmallFrames {
		if f.ordinal == 113 {
			return f
		}
	}
	t.Fatal("missing113")
	return hdSmallFrame{}
}
func r99Small(t *testing.T, m *golem.Machine, dir string) *hdSmallRuntime {
	t.Helper()
	old := hdSmallFrames
	hdSmallFrames = []hdSmallFrame{r99Frame(t)}
	defer func() { hdSmallFrames = old }()
	h := &hdRuntime{m: m}
	p, e := loadHDSmallRuntime(h, os.Getenv("TEST_GAME_ROOT"), dir)
	if e != nil {
		t.Fatal(e)
	}
	h.small = p
	return p
}
func TestR99HeadCPUFixture(t *testing.T) {
	if os.Getenv("TEST_R99_ROOT") == "" {
		t.Skip("缺少本機原版顧問頁收據")
	}
	root := os.Getenv("TEST_R99_ROOT")
	fix := filepath.Join(root, "r99-indian-observed-r3")
	var meta struct {
		Entry struct {
			Registers [8]uint16 `json:"registers"`
			Segments  [4]uint16 `json:"segments"`
			Step      uint64    `json:"entry_step"`
		} `json:"entry"`
		Flags  uint16 `json:"flags"`
		Cycles uint64 `json:"cycles"`
		Memory string `json:"memory_sha256"`
	}
	if e := json.Unmarshal(r99Load(t, filepath.Join(fix, "r98-decoder-940-2cae0.json")), &meta); e != nil {
		t.Fatal(e)
	}
	m := golem.New()
	raw := r99Load(t, filepath.Join(fix, "r98-decoder-940-2cae0.memory"))
	if hash(raw) != meta.Memory {
		t.Fatal("fixture hash")
	}
	copy(m.Mem, raw)
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags, m.CPU.Cycles = meta.Entry.Registers, meta.Entry.Segments, 0xa, meta.Flags, meta.Cycles
	m.Steps = meta.Entry.Step
	before := hash(m.Mem)
	p := r99Small(t, m, filepath.Join(root, "r99-head-prototype-assets-r1"))
	if hash(m.Mem) != before {
		t.Fatal("loader changed RAM")
	}
	p.beforeInstruction()
	if !p.active {
		t.Fatal("entry refused")
	}
	entryCases := hdSmallEntryNegatives(t, p)
	writerDone := false
	steps := 0
	for ; steps < 100000 && p.accepted == 0; steps++ {
		if steps > 0 {
			p.beforeInstruction()
		}
		if p.accepted > 0 {
			break
		}
		if !writerDone && m.CPU.Seg[golem.CS] == 0xd46 && hdSmallWriterCodes[m.CPU.IP] != nil {
			hdSmallWriterNegative(t, p)
			writerDone = true
		}
		if e := m.CPU.Step(); e != nil {
			t.Fatal(e)
		}
		m.Steps++
	}
	if p.accepted != 1 || p.rejected != 0 || !writerDone {
		t.Fatal("CPU draw not accepted", p.accepted, p.rejected)
	}
	finishCases := hdSmallFinishNegatives(t, p)
	owned := 0
	for _, c := range p.visible {
		if c.owned {
			owned++
		}
	}
	if owned != 226 {
		t.Fatal("source count", owned)
	}
	mem := r99Load(t, filepath.Join(root, "r99-indian-advisor-observed-r1/final.memory"))
	idx := r99Load(t, filepath.Join(root, "r99-indian-advisor-observed-r1/final.idx"))
	pal := r99Load(t, filepath.Join(root, "r99-indian-advisor-observed-r1/final.palette"))
	frame := draftNativeFrame{canvas: mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: idx, palette: pal, mode: 0x13}
	art := draftRGB(idx, pal)
	receipt := p.paint(art, frame)
	out := filepath.Join(root, "r99-head-formal-component-r1.png")
	f, e := os.Create(out)
	if e != nil {
		t.Fatal(e)
	}
	e = png.Encode(f, art)
	f.Close()
	if e != nil {
		t.Fatal(e)
	}
	for i, c := range p.visible {
		if c.owned {
			p.memoryWrite(hdBuildingCanvas+uint32(i), c.native, c.native)
		}
	}
	for _, c := range p.visible {
		if c.owned {
			t.Fatal("same-value did not revoke")
		}
	}
	report := map[string]any{"entry_cases": entryCases, "finish_cases": finishCases, "writer_wrong_code": writerDone, "CPU_steps": steps, "accepted": p.accepted, "owned_before": owned, "owned_after_same_value": 0, "receipt": receipt, "partial_fixture_only": true, "no_normal_GUI_credit": true}
	b, _ := json.MarshalIndent(report, "", "  ")
	if e := os.WriteFile(filepath.Join(root, "r99-head-formal-fixture-r1.json"), b, 0644); e != nil {
		t.Fatal(e)
	}
}
func TestR99HeadPalette(t *testing.T) {
	if os.Getenv("TEST_R99_ROOT") == "" {
		t.Skip("缺少本機原版顧問頁收據")
	}
	root := os.Getenv("TEST_R99_ROOT")
	pal := r99Load(t, filepath.Join(root, "r99-indian-advisor-observed-r1/final.palette"))
	f := r99Frame(t)
	if !f.paletteSupported(pal) {
		t.Fatal("actual rejected")
	}
	for _, i := range f.paletteIndices {
		t.Run("used-"+string([]byte{'0' + i/100, '0' + i/10%10, '0' + i%10}), func(t *testing.T) {
			bad := append([]byte(nil), pal...)
			bad[int(i)*3] ^= 1
			if f.paletteSupported(bad) {
				t.Fatal("wrong color accepted")
			}
		})
	}
	if f.paletteSupported(nil) || f.paletteSupported(pal[:767]) {
		t.Fatal("short palette")
	}
	unused := 0
	for bytes.Contains(f.paletteIndices, []byte{byte(unused)}) {
		unused++
	}
	changed := append([]byte(nil), pal...)
	changed[unused*3] ^= 1
	if !f.paletteSupported(changed) {
		t.Fatal("unused palette field changed scope")
	}
}
func TestR99HeadResources(t *testing.T) {
	if os.Getenv("TEST_R99_ROOT") == "" {
		t.Skip("缺少本機原版顧問頁收據")
	}
	root := os.Getenv("TEST_R99_ROOT")
	f := r99Frame(t)
	raw := r99Load(t, filepath.Join(root, "r99-head-prototype-assets-r1/icons-113.png"))
	original := hdSmallFrames
	hdSmallFrames = []hdSmallFrame{f}
	defer func() { hdSmallFrames = original }()
	run := func(t *testing.T, dir string, ok bool) {
		m := golem.New()
		before := hash(m.Mem)
		_, e := loadHDSmallRuntime(&hdRuntime{m: m}, os.Getenv("TEST_GAME_ROOT"), dir)
		if (e == nil) != ok || hash(m.Mem) != before {
			t.Fatal("resource guard", e)
		}
	}
	t.Run("valid", func(t *testing.T) { run(t, filepath.Join(root, "r99-head-prototype-assets-r1"), true) })
	t.Run("missing", func(t *testing.T) { run(t, t.TempDir(), false) })
	t.Run("changed", func(t *testing.T) {
		dir := t.TempDir()
		b := append([]byte(nil), raw...)
		b[len(b)/2] ^= 1
		os.WriteFile(filepath.Join(dir, f.file), b, 0644)
		run(t, dir, false)
	})
	t.Run("truncated", func(t *testing.T) {
		dir := t.TempDir()
		os.WriteFile(filepath.Join(dir, f.file), raw[:64], 0644)
		run(t, dir, false)
	})
	t.Run("symlink", func(t *testing.T) {
		dir := t.TempDir()
		os.Symlink(filepath.Join(root, "r99-head-prototype-assets-r1/icons-113.png"), filepath.Join(dir, f.file))
		run(t, dir, false)
	})
}
