// 規格068 READY：正式八來源與65點原版收據。
package main

import (
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestHDSmallTerrainRuntimeNative65(t *testing.T) {
	game, reference, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_SMALL_TERRAIN_REFERENCE"), os.Getenv("TEST_SMALL_TERRAIN_OUTPUT")
	if game == "" || reference == "" || out == "" {
		t.Skip("需要合法原版與本機GUI收據")
	}
	for _, name := range []string{"OPENING.EXE", "VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "ICONS.SS", "CURSOR.SS"} {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版輸入", name)
		} else if err != nil {
			t.Fatal(err)
		}
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(path string) []byte { t.Helper(); b, err := os.ReadFile(path); need(err); return b }
	var replay struct {
		Inputs []windowInput
		End    uint64
	}
	raw := read(filepath.Join(reference, "inputs.json"))
	if hash(raw) != "6783faef06b074fa738bc33276ac186f89479954b75e6d5a142868fbdacb113f" {
		t.Fatal("原始GUI前綴不同")
	}
	need(json.Unmarshal(raw, &replay))
	var points []struct {
		Step, Count              uint64
		Memory, Indexed, Palette string
		Registers                [8]uint16
		Segments                 [4]uint16
		IP, Flags                uint16
	}
	var original []struct {
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
	need(json.Unmarshal(read(filepath.Join(reference, "points.json")), &original))
	for _, p := range original {
		points = append(points, struct {
			Step, Count              uint64
			Memory, Indexed, Palette string
			Registers                [8]uint16
			Segments                 [4]uint16
			IP, Flags                uint16
		}{p.Step, p.Count, p.Memory, p.Indexed, p.Palette, p.Registers, p.Segments, p.IP, p.Flags})
	}
	if len(points) != 65 || len(replay.Inputs) != 143 || replay.End != 251625001 {
		t.Fatal("GUI範圍不同")
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatal("需新輸出目錄")
	}
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "save")
	need(os.Mkdir(scratch, 0755))
	seed := read(os.Getenv("TEST_SMALL_TERRAIN_SEED"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("原版種子不同")
	}
	need(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("缺數位音訊能力")
	}
	m.EnableOPLSynth(true)
	h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))
	need(err)
	p := h.smallTerrain
	if p == nil {
		t.Fatal("原型未載入")
	}
	p.trace = true
	entries, finishes, ownership := map[int]bool{}, map[int]bool{}, map[int]bool{}
	var negatives []string
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		if p.active && !entries[p.current.ordinal] {
			negatives = append(negatives, hdSmallTerrainEntryNegatives(t, p)...)
			entries[p.current.ordinal] = true
		}
		if p.current != nil && p.acceptedBy[p.current.ordinal] > 0 && !finishes[p.current.ordinal] {
			negatives = append(negatives, hdSmallTerrainFinishNegatives(t, p)...)
			finishes[p.current.ordinal] = true
		}
	})
	count, at := uint64(0), 0
	started := time.Now()
	var records []map[string]any
	capture := func() {
		if at == len(points) {
			return
		}
		point := points[at]
		if m.Steps > point.Step || (m.Steps == point.Step && count > point.Count) {
			t.Fatal("略過原版檢查點", at, m.Steps, count)
		}
		if m.Steps != point.Step || count != point.Count {
			return
		}
		c := m.CPU
		if hash(m.Mem) != point.Memory || hash(m.Indexed()) != point.Indexed || hash(m.DAC[:]) != point.Palette || c.R != point.Registers || c.Seg != point.Segments || c.IP != point.IP || c.Flags != point.Flags {
			t.Fatal("原型改變原版狀態", at)
		}
		var oracle map[int]struct {
			Ordinal int  `json:"ordinal"`
			Local   int  `json:"local"`
			Native  byte `json:"native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_SMALL_TERRAIN_MODEL"), fmt.Sprintf("point-%03d.terrain-model.json", at))), &oracle))
		cells := map[int]map[string]any{}
		for pos, cell := range p.visible {
			want, known := oracle[pos]
			_, selected := p.frames[want.Ordinal]
			owned := known && selected
			if cell.owned != owned || (owned && (int(cell.ordinal) != want.Ordinal || int(cell.k) != want.Local || cell.native != want.Native || m.Mem[hdBuildingCanvas+uint32(pos)] != cell.native)) {
				t.Fatal("逐來源模型不同", at, pos, cell, want)
			}
			if owned {
				cells[pos] = map[string]any{"ordinal": want.Ordinal, "local": want.Local, "native": want.Native}
				if !ownership[want.Ordinal] {
					n := hdSmallTerrainClone(p)
					n.memoryWrite(hdBuildingCanvas+uint32(pos), cell.native, cell.native)
					if n.visible[pos].owned {
						t.Fatal("未知同值寫入未撤銷", want.Ordinal)
					}
					ownership[want.Ordinal] = true
					negatives = append(negatives, fmt.Sprintf("%03d-unknown-same-write", want.Ordinal))
				}
			}
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		before, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		im, record := h.base(f)
		h.restoreCursor(im, f)
		cursor := h.cursor.paint(h, im, f)
		h.smallTerrain = nil
		baseline, _ := h.base(f)
		h.smallTerrain = p
		h.restoreCursor(baseline, f)
		h.cursor.paint(h, baseline, f)
		if hash(m.Mem) != before || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("合成改變原版", at)
		}
		record["cursor"] = cursor
		record["small_terrain_cells"] = cells
		record["point"], record["step"], record["dos_mouse"], record["original_state_equal"] = at, m.Steps, map[string]int{"x": int(d.Mouse.X), "y": int(d.Mouse.Y)}, true
		prefix := filepath.Join(out, fmt.Sprintf("point-%03d", at))
		file, err := os.Create(prefix + ".png")
		need(err)
		need(png.Encode(file, im))
		need(file.Close())
		file, err = os.Create(prefix + ".baseline.png")
		need(err)
		need(png.Encode(file, baseline))
		need(file.Close())
		for suffix, data := range map[string][]byte{".memory": m.Mem, ".idx": f.indexed, ".canvas": f.canvas, ".palette": f.palette, ".cursor": m.Mem[0x1cd74:0x1ce74]} {
			need(os.WriteFile(prefix+suffix, data, 0644))
		}
		records = append(records, record)
		at++
	}
	step := func() { capture(); need(m.Step()) }
	for _, e := range replay.Inputs {
		for m.Steps < e.Step {
			step()
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < replay.End {
		step()
	}
	capture()
	if at != 65 || p.accepted != 57 || p.rejected != 0 || p.bufferSaves != 697 || p.bufferRestores != 474 || len(p.pairs) != 56 {
		t.Fatal("批次原版範圍不同", at, p.accepted, p.rejected, p.bufferSaves, p.bufferRestores, len(p.pairs))
	}
	if len(entries) != 8 || len(finishes) != 8 || len(ownership) != 8 || len(negatives) != 72 {
		t.Fatal("來源反例未齊", len(entries), len(finishes), len(ownership), len(negatives))
	}
	var control struct {
		End struct {
			Memory    string `json:"memory_sha256"`
			Indexed   string `json:"indexed_sha256"`
			Palette   string `json:"palette_sha256"`
			Registers [8]uint16
			Segments  [4]uint16
			IP, Flags uint16
			Steps     uint64
		}
	}
	need(json.Unmarshal(read(filepath.Join(reference, "oracle-r1/control/draws.json")), &control))
	e := control.End
	if m.Steps != e.Steps || hash(m.Mem) != e.Memory || hash(m.Indexed()) != e.Indexed || hash(m.DAC[:]) != e.Palette || m.CPU.R != e.Registers || m.CPU.Seg != e.Segments || m.CPU.IP != e.IP || m.CPU.Flags != e.Flags {
		t.Fatal("原版終點不同")
	}
	d.Close()
	for _, name := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		if hash(read(filepath.Join(scratch, name))) != hash(read(filepath.Join(reference, "oracle-r1/control/saves", name))) {
			t.Fatal("存檔不同", name)
		}
	}
	result := map[string]any{"result": "PASS_SMALL_TERRAIN_FORMAL_NATIVE_65", "production_connected": true, "points": records, "calls": p.calls, "cursor_pairs": p.pairs, "accepted_calls": p.accepted, "accepted_by_ordinal": p.acceptedBy, "ram_saves": p.bufferSaves, "ram_restores": p.bufferRestores, "owned_cursor_restores": len(p.pairs), "dos_inputs": count, "end": m.Steps, "negatives": negatives, "original_state_and_saves_equal": true, "seconds": time.Since(started).Seconds()}
	raw, err = json.MarshalIndent(result, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func hdSmallTerrainClone(p *hdSmallTerrainRuntime) *hdSmallTerrainRuntime {
	m := golem.New()
	copy(m.Mem, p.h.m.Mem)
	m.Steps = p.h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = p.h.m.CPU.R, p.h.m.CPU.Seg, p.h.m.CPU.IP, p.h.m.CPU.Flags
	h := *p.h
	h.m = m
	n := *p
	n.h = &h
	h.smallTerrain = &n
	n.trace = false
	n.calls = nil
	n.pairs = nil
	n.entry = nil
	n.pending = map[int]hdSmallTerrainPair{}
	for k, v := range p.pending {
		n.pending[k] = v
	}
	n.backing = map[uint32]hdSmallTerrainCell{}
	for k, v := range p.backing {
		n.backing[k] = v
	}
	n.acceptedBy = map[int]uint64{}
	for k, v := range p.acceptedBy {
		n.acceptedBy[k] = v
	}
	n.cursorRestoresBy = map[int]uint64{}
	for k, v := range p.cursorRestoresBy {
		n.cursorRestoresBy[k] = v
	}
	return &n
}
func hdSmallTerrainEntryNegatives(t *testing.T, p *hdSmallTerrainRuntime) []string {
	t.Helper()
	positive := hdSmallTerrainClone(p)
	positive.active = false
	positive.beforeInstruction()
	if !positive.active {
		t.Fatal("正向入口未接受")
	}
	c := p.h.m.CPU
	stack, _ := hdBuildingWords(p.h.m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	off := uint16(uint32(c.R[golem.AX])*12 + uint32(stack[3]) + 0x36)
	rec, _ := hdBuildingWords(p.h.m.Mem, stack[4], off, 6)
	source := int(rec[1])*16 + int(rec[0])
	record := int(stack[4])*16 + int(off)
	tests := []struct {
		name   string
		change func(*hdSmallTerrainRuntime)
	}{
		{"wrong-ordinal", func(n *hdSmallTerrainRuntime) { n.h.m.CPU.R[golem.AX] = 65535 }},
		{"wrong-source", func(n *hdSmallTerrainRuntime) { n.h.m.Mem[source] ^= 1 }},
		{"wrong-entry", func(n *hdSmallTerrainRuntime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
		{"wrong-geometry", func(n *hdSmallTerrainRuntime) { n.h.m.Mem[record+8]++ }},
	}
	var result []string
	for _, test := range tests {
		n := hdSmallTerrainClone(p)
		n.active = false
		test.change(n)
		n.beforeInstruction()
		if n.active {
			t.Fatal("入口錯件未拒絕", p.current.ordinal, test.name)
		}
		result = append(result, fmt.Sprintf("%03d-%s", p.current.ordinal, test.name))
	}
	return result
}
func hdSmallTerrainFinishNegatives(t *testing.T, p *hdSmallTerrainRuntime) []string {
	t.Helper()
	positive := hdSmallTerrainClone(p)
	positive.finish()
	if positive.accepted != p.accepted+1 {
		t.Fatal("正向返回未接受", p.current.ordinal)
	}
	opaque, transparent := -1, -1
	for k, n := range p.counts {
		if n == 1 && opaque < 0 {
			opaque = k
		}
		if n == 0 && transparent < 0 {
			transparent = k
		}
	}
	if opaque < 0 {
		t.Fatal("缺正向透明與不透明格")
	}
	address := func(k int) uint32 { return hdSmallTerrainStage + uint32((p.y+k/8)*320+p.x+k%8) }
	tests := []struct {
		name   string
		change func(*hdSmallTerrainRuntime)
	}{
		{"missing-write", func(n *hdSmallTerrainRuntime) { n.counts[opaque] = 0 }},
		{"duplicate-write", func(n *hdSmallTerrainRuntime) { n.counts[opaque]++ }},
		{"transparent-changed", func(n *hdSmallTerrainRuntime) { n.h.m.Mem[address(transparent)] ^= 1 }},
		{"stale-return", func(n *hdSmallTerrainRuntime) { n.h.m.Mem[address(opaque)] ^= 1 }},
	}
	if transparent < 0 {
		tests[2].name = "outside-write"
		tests[2].change = func(n *hdSmallTerrainRuntime) { n.outside = true }
	}
	var result []string
	for _, test := range tests {
		n := hdSmallTerrainClone(p)
		test.change(n)
		n.finish()
		if n.accepted != p.accepted || n.rejected != p.rejected+1 {
			t.Fatal("返回錯件未拒絕", p.current.ordinal, test.name)
		}
		result = append(result, fmt.Sprintf("%03d-%s", p.current.ordinal, test.name))
	}
	return result
}

func TestHDSmallTerrainAssetNegatives(t *testing.T) {
	game, assets, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_SMALL_TERRAIN_ASSET_OUTPUT")
	if game == "" || assets == "" || out == "" {
		t.Skip("需要合法原版及候選素材")
	}
	if _, err := os.Stat(filepath.Join(game, "PHYS0.SS")); os.IsNotExist(err) {
		t.Skip("缺少合法原版PHYS0.SS")
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(path string) []byte { b, err := os.ReadFile(path); need(err); return b }
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatal("需新輸出")
	}
	need(os.Mkdir(out, 0755))
	work := t.TempDir()
	copyGame, copyAssets := filepath.Join(work, "game"), filepath.Join(work, "assets")
	need(os.Mkdir(copyGame, 0755))
	need(os.Mkdir(copyAssets, 0755))
	originalSource := read(filepath.Join(game, "PHYS0.SS"))
	need(os.WriteFile(filepath.Join(copyGame, "PHYS0.SS"), originalSource, 0644))
	for _, d := range hdSmallTerrainDefinitions {
		need(os.WriteFile(filepath.Join(copyAssets, d.asset), read(filepath.Join(assets, d.asset)), 0644))
	}
	h := &hdRuntime{m: golem.New()}
	var cases []string
	for _, d := range hdSmallTerrainDefinitions {
		path := filepath.Join(copyAssets, d.asset)
		raw := read(path)
		for _, kind := range []string{"missing", "wrong", "linked"} {
			need(os.Remove(path))
			if kind == "wrong" {
				need(os.WriteFile(path, []byte("wrong"), 0644))
			}
			if kind == "linked" {
				need(os.Symlink(filepath.Join(assets, d.asset), path))
			}
			if _, err := loadHDSmallTerrainRuntime(h, copyGame, copyAssets); err == nil {
				t.Fatal("錯候選未拒絕", d.ordinal, kind)
			}
			cases = append(cases, fmt.Sprintf("%03d-%s", d.ordinal, kind))
			if kind != "missing" {
				need(os.Remove(path))
			}
			need(os.WriteFile(path, raw, 0644))
		}
	}
	source := filepath.Join(copyGame, "PHYS0.SS")
	for _, kind := range []string{"missing", "wrong", "linked"} {
		need(os.Remove(source))
		if kind == "wrong" {
			need(os.WriteFile(source, []byte("wrong"), 0644))
		}
		if kind == "linked" {
			need(os.Symlink(filepath.Join(game, "PHYS0.SS"), source))
		}
		if _, err := loadHDSmallTerrainRuntime(h, copyGame, copyAssets); err == nil {
			t.Fatal("錯原版來源未拒絕", kind)
		}
		cases = append(cases, "source-"+kind)
		if kind != "missing" {
			need(os.Remove(source))
		}
		need(os.WriteFile(source, originalSource, 0644))
	}
	if _, err := loadHDSmallTerrainRuntime(nil, copyGame, copyAssets); err == nil {
		t.Fatal("缺HD來源仍接受")
	}
	cases = append(cases, "missing-runtime")
	positive, err := loadHDSmallTerrainRuntime(h, copyGame, copyAssets)
	need(err)
	if len(cases) != 28 || len(positive.frames) != 28 || hash(read(filepath.Join(game, "PHYS0.SS"))) != hash(originalSource) {
		t.Fatal("反例後正向或原版不同")
	}
	result := map[string]any{"result": "PASS_SMALL_TERRAIN_28_LOADER_NEGATIVES_AND_POSITIVE_RECHECK", "cases": cases, "positive_after_negatives": true, "original_source_unchanged": true, "production_connected": true}
	raw, err := json.MarshalIndent(result, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}
