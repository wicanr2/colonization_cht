package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func hdNineClone(p *hdNineRuntime) *hdNineRuntime {
	m := golem.New()
	copy(m.Mem, p.h.m.Mem)
	m.Steps = p.h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = p.h.m.CPU.R, p.h.m.CPU.Seg, p.h.m.CPU.IP, p.h.m.CPU.Flags
	h := *p.h
	h.m = m
	n := *p
	n.h = &h
	h.nine = &n
	n.trace = false
	n.frames = append([]hdNineFrame(nil), p.frames...)
	n.pending = map[int]hdNinePending{}
	for k, v := range p.pending {
		n.pending[k] = v
	}
	return &n
}
func hdNineEntryNegatives(t *testing.T, p *hdNineRuntime) []string {
	t.Helper()
	positive := hdNineClone(p)
	positive.active = false
	positive.beforeInstruction()
	if !positive.active {
		t.Fatal("九來源真實入口未接受")
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
		change func(*hdNineRuntime)
	}{
		{"wrong-frame", func(n *hdNineRuntime) { n.h.m.CPU.R[golem.AX] |= 0x1000 }},
		{"high-frame-bit", func(n *hdNineRuntime) { n.h.m.CPU.R[golem.AX] |= 0x8000 }},
		{"negative-x", func(n *hdNineRuntime) { n.h.m.CPU.R[golem.DX] = 65535 }},
		{"clipped-right", func(n *hdNineRuntime) { n.h.m.CPU.R[golem.DX] = uint16(321 - f.w) }},
		{"negative-y", func(n *hdNineRuntime) { binary.LittleEndian.PutUint16(n.h.m.Mem[stack+4:], 65535) }},
		{"clipped-bottom", func(n *hdNineRuntime) { binary.LittleEndian.PutUint16(n.h.m.Mem[stack+4:], uint16(201-f.h)) }},
		{"wrong-destination", func(n *hdNineRuntime) { n.h.m.Mem[int(c.Seg[golem.DS])*16+int(c.R[golem.BX])+6]++ }},
		{"wrong-width", func(n *hdNineRuntime) { n.h.m.Mem[at+8]++ }},
		{"wrong-source-bytes", func(n *hdNineRuntime) { n.h.m.Mem[source] ^= 1 }},
		{"wrong-entry-code", func(n *hdNineRuntime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
	}
	var names []string
	for _, tc := range cases {
		n := hdNineClone(p)
		n.active = false
		tc.change(n)
		n.beforeInstruction()
		if n.active || n.accepted != p.accepted {
			t.Fatal("九來源入口反例未拒絕", f.ordinal, tc.name)
		}
		names = append(names, tc.name)
	}
	return names
}
func hdNineWriterNegative(t *testing.T, p *hdNineRuntime) string {
	t.Helper()
	c := p.h.m.CPU
	f := p.frames[p.selected]
	addr := int(c.Seg[golem.ES])*16 + int(c.R[golem.BX])
	x, y := addr-int(hdBuildingCanvas), 0
	y = x/320 - p.y
	x = x%320 - p.x
	if x < 0 || x >= f.w || y < 0 || y >= f.h {
		t.Fatal("原版九來源MOV目的不同", f.ordinal)
	}
	local := y*f.w + x
	for _, bad := range []bool{false, true} {
		n := hdNineClone(p)
		if bad {
			n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)+15] ^= 1
		}
		n.h.m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, o, v byte) { n.write(a, o, v) })
		if err := n.h.m.CPU.Step(); err != nil {
			t.Fatal(err)
		}
		if bad {
			if !n.outside || n.counts[local] != p.counts[local] {
				t.Fatal("九來源錯寫入碼仍接受", f.ordinal)
			}
		} else if n.outside || n.counts[local] != p.counts[local]+1 {
			t.Fatal("真實九來源MOV未接受", f.ordinal)
		}
	}
	return "wrong-writer-code"
}
func hdNineFinishNegatives(t *testing.T, p *hdNineRuntime) []string {
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
		t.Fatal("缺少九來源實際寫入")
	}
	for _, duplicate := range []bool{false, true} {
		n := hdNineClone(p)
		name := "missing-source-write"
		n.counts[local] = 0
		if duplicate {
			name = "duplicate-source-write"
			n.counts[local] = 2
		}
		n.finish()
		if n.accepted != p.accepted || n.rejected != p.rejected+1 {
			t.Fatal("不完整九來源未拒絕", name)
		}
		names = append(names, name)
	}
	return names
}
func hdNineOwnershipNegatives(t *testing.T, p *hdNineRuntime, f draftNativeFrame, slot int) []string {
	t.Helper()
	pixel := -1
	a := p.frames[slot]
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
		t.Fatal("缺少九來源可見墨跡", a.ordinal)
	}
	paint := func(n *hdNineRuntime) int {
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		return n.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), g)["painted"].(int)
	}
	baseline := paint(hdNineClone(p))
	addr := hdBuildingCanvas + uint32(pixel)
	var names []string
	for _, same := range []bool{false, true} {
		n := hdNineClone(p)
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
			t.Fatal("九來源未知寫入未撤銷", a.ordinal, name)
		}
		names = append(names, name)
	}
	n := hdNineClone(p)
	n.h.m.Mem[addr] ^= 1
	if paint(n) != baseline-1 {
		t.Fatal("九來源過期像素仍繪製")
	}
	names = append(names, "stale-native-pixel")
	n = hdNineClone(p)
	n.pending[pixel] = hdNinePending{cell: n.visible[pixel]}
	n.h.m.Mem[0x1cd74] ^= 1
	n.write(addr, n.h.m.Mem[addr], n.h.m.Mem[addr])
	if len(n.pending) != 0 {
		t.Fatal("九來源未知寫入未清除配對")
	}
	names = append(names, "interleaved-cursor-pair")
	for _, tc := range []struct {
		name string
		at   int
	}{{"unknown-cursor-source", 0x1cd74}, {"incomplete-cursor-buffer", 0xafb00}} {
		n = hdNineClone(p)
		n.h.m.Mem[tc.at] ^= 1
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		_, r := n.h.base(g)
		if r["reason"] != "unverified-cursor-or-native-surface" || r["nine"] != nil {
			t.Fatal("九來源未知游標未回退", tc.name)
		}
		names = append(names, tc.name)
	}
	raw, err := os.ReadFile(filepath.Join(os.Getenv("TEST_HD_NINE_ASSETS"), a.file))
	if err != nil {
		t.Fatal(err)
	}
	raw[len(raw)-1] ^= 1
	bad := filepath.Join(t.TempDir(), a.file)
	if err = os.WriteFile(bad, raw, 0644); err != nil {
		t.Fatal(err)
	}
	before := hash(p.h.m.Mem)
	if _, err = hdNineRead(bad, a.artSHA, 8<<20); err == nil || hash(p.h.m.Mem) != before {
		t.Fatal("九來源錯素材未拒絕或改寫DOS")
	}
	return append(names, "wrong-art-sha256")
}
func TestHDNineRuntimeNativeLifecycle(t *testing.T) {
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
	if h.nine == nil || len(h.nine.frames) != 10 || hash(m.Mem) != before {
		t.Fatal("九來源載入失敗或改寫DOS")
	}
	p := h.nine
	p.trace = true
	negatives := map[int][]string{}
	entryChecked, writerChecked, finishChecked, ownerChecked := map[int]bool{}, map[int]bool{}, map[int]bool{}, map[int]bool{}
	prior := uint64(0)
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		if p.accepted != prior {
			n := p.frames[p.selected].ordinal
			if !finishChecked[n] {
				negatives[n] = append(negatives[n], hdNineFinishNegatives(t, p)...)
				finishChecked[n] = true
			}
			prior = p.accepted
		}
		if p.active {
			n := p.frames[p.selected].ordinal
			if !entryChecked[n] {
				negatives[n] = append(negatives[n], hdNineEntryNegatives(t, p)...)
				entryChecked[n] = true
			}
			if !writerChecked[n] && m.CPU.Seg[golem.CS] == 0xd46 && hdNineWriterCodes[m.CPU.IP] != nil {
				negatives[n] = append(negatives[n], hdNineWriterNegative(t, p))
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
			t.Fatal("九來源改變原版完整狀態", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), step: m.Steps, mode: m.VideoMode()}
		ram, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		var oracle map[string]struct {
			Ordinal int
			Local   int
			Native  byte
		}
		need(json.Unmarshal(load(filepath.Join(os.Getenv("TEST_HD_NINE_MODEL"), fmt.Sprintf("point-%03d.nine-model.json", at))), &oracle))
		for pos, cell := range p.visible {
			if !cell.owned {
				continue
			}
			expected, ok := oracle[fmt.Sprint(pos)]
			if !ok || expected.Ordinal != p.frames[cell.slot].ordinal || expected.Local != int(cell.local) || expected.Native != cell.native || f.canvas[pos] != cell.native {
				t.Fatal("九來源沒有獨立逐點證據", at, pos, cell)
			}
		}
		output, record := h.base(f)
		h.restoreCursor(output, f)
		receipt := p.receipt(f)
		if record["reason"] == "known-building" {
			if receipt["owned"].(int) > 0 {
				actual, ok := record["nine"].(map[string]any)
				if !ok || actual["painted"].(int) <= 0 {
					t.Fatal("九來源正常狀態未合成", at)
				}
			}
			for slot, a := range p.frames {
				r := receipt["sources"].(map[string]any)[fmt.Sprint(a.ordinal)].(map[string]any)
				if r["owned"].(int) > 0 && !ownerChecked[a.ordinal] {
					negatives[a.ordinal] = append(negatives[a.ordinal], hdNineOwnershipNegatives(t, p, f, slot)...)
					ownerChecked[a.ordinal] = true
				}
			}
		} else {
			if record["nine"] != nil {
				t.Fatal("守門回退仍繪九來源")
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
		for i, v := range p.visible {
			if v.owned && v.native == f.canvas[i] {
				allowed[i] = true
			}
		}
		for i, v := range h.small.visible {
			if v.owned && v.native == f.canvas[i] && h.small.frames[v.slot].art != nil {
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
		native := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if !allowed[(y/4)*320+x/4] && output.RGBAAt(x, y) != native.RGBAAt(x, y) {
					t.Fatal("九來源越出已驗像素", at, x, y)
				}
			}
		}
		if hash(m.Mem) != ram || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("九來源合成改寫原版", at)
		}
		records = append(records, map[string]any{"point": at, "step": m.Steps, "nine": receipt, "hd": record, "original_state_equal": true})
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
	if at != 49 || count != 53 || p.accepted != 130 || p.rejected != 0 {
		t.Fatal("九來源原版路徑不同", at, count, p.accepted, p.rejected)
	}
	for _, f := range p.frames {
		if !entryChecked[f.ordinal] || !writerChecked[f.ordinal] || !finishChecked[f.ordinal] || !ownerChecked[f.ordinal] || len(negatives[f.ordinal]) != 20 {
			t.Fatal("九來源反例缺漏", f.ordinal, negatives[f.ordinal])
		}
	}
	for _, name := range []string{"COLONY00.SAV", "COLONY09.SAV"} {
		if !bytes.Equal(load(filepath.Join(scratch, name)), load(filepath.Join(receipts, "lifecycle-r29-r1/gui/save", name))) {
			t.Fatal("九來源改變原版存檔", name)
		}
	}
	target := os.Getenv("TEST_HD_NINE_OUTPUT")
	if target == "" {
		t.Fatal("缺少九來源收據輸出")
	}
	need(os.Mkdir(target, 0755))
	data, err := json.MarshalIndent(map[string]any{"result": "PASS_NINE_RUNTIME_NATIVE_49", "production_connected": true, "points": records, "accepted": p.accepted, "rejected": p.rejected, "dos_inputs": count, "end": m.Steps, "negative_cases": negatives, "guard_points": guardPoints, "calls": p.calls, "cursor_pairs": p.pairs}, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(target, "check.json"), append(data, '\n'), 0644))
}
