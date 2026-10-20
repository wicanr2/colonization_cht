// 規格067 READY：正式十二來源與獨立原版收據的同狀態驗證。
package main

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestHDWorldTerrainNative29(t *testing.T) {
	game, reference, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_TERRAIN_BATCH_REFERENCE"), os.Getenv("TEST_TERRAIN_BATCH_OUTPUT")
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
	raw := read(filepath.Join(reference, "gui-oracle-inputs.json"))
	if hash(raw) != "63b8cc52610760adf4a63e4d8351a262d6c4007db45e3939f24ce94de1f20cfb" {
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
	need(json.Unmarshal(read(filepath.Join(reference, "gui-oracle-points.json")), &original))
	for _, p := range original {
		points = append(points, struct {
			Step, Count              uint64
			Memory, Indexed, Palette string
			Registers                [8]uint16
			Segments                 [4]uint16
			IP, Flags                uint16
		}{p.Step, p.Count, p.Memory, p.Indexed, p.Palette, p.Registers, p.Segments, p.IP, p.Flags})
	}
	if len(points) != 29 || len(replay.Inputs) != 109 || replay.End != 218130001 {
		t.Fatal("GUI範圍不同")
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatal("需新輸出目錄")
	}
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "save")
	need(os.Mkdir(scratch, 0755))
	seed := read(os.Getenv("TEST_TERRAIN_BATCH_SEED"))
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
	p := h.terrainBatch
	if p == nil {
		t.Fatal("原型未載入")
	}
	p.trace = true
	entries, finishes, ownership := map[int]bool{}, map[int]bool{}, map[int]bool{}
	var negatives []string
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		if p.active && !entries[p.current.ordinal] {
			negatives = append(negatives, hdTerrainBatchEntryNegatives(t, p)...)
			entries[p.current.ordinal] = true
		}
		if p.current != nil && p.acceptedBy[p.current.ordinal] > 0 && !finishes[p.current.ordinal] {
			negatives = append(negatives, hdTerrainBatchFinishNegatives(t, p)...)
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
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_TERRAIN_BATCH_MODEL"), fmt.Sprintf("point-%03d.terrain-model.json", at))), &oracle))
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
					n := hdTerrainBatchClone(p)
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
		h.terrainBatch = nil
		baseline, _ := h.base(f)
		h.terrainBatch = p
		h.restoreCursor(baseline, f)
		h.cursor.paint(h, baseline, f)
		if hash(m.Mem) != before || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("合成改變原版", at)
		}
		record["cursor"] = cursor
		record["terrain_batch_cells"] = cells
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
	if at != 29 || p.accepted != 80 || p.rejected != 0 || p.bufferSaves != 3325 || p.bufferRestores != 2471 || len(p.pairs) != 220 {
		t.Fatal("批次原版範圍不同", at, p.accepted, p.rejected, p.bufferSaves, p.bufferRestores, len(p.pairs))
	}
	if len(entries) != 12 || len(finishes) != 12 || len(ownership) != 12 || len(negatives) != 108 {
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
	need(json.Unmarshal(read(filepath.Join(reference, "gui-oracle-r1/control/draws.json")), &control))
	e := control.End
	if m.Steps != e.Steps || hash(m.Mem) != e.Memory || hash(m.Indexed()) != e.Indexed || hash(m.DAC[:]) != e.Palette || m.CPU.R != e.Registers || m.CPU.Seg != e.Segments || m.CPU.IP != e.IP || m.CPU.Flags != e.Flags {
		t.Fatal("原版終點不同")
	}
	d.Close()
	for _, name := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		if hash(read(filepath.Join(scratch, name))) != hash(read(filepath.Join(reference, "gui-oracle-r1/control/saves", name))) {
			t.Fatal("存檔不同", name)
		}
	}
	result := map[string]any{"result": "PASS_WORLD_TERRAIN_FORMAL_NATIVE_29", "production_connected": true, "points": records, "calls": p.calls, "cursor_pairs": p.pairs, "accepted_calls": p.accepted, "accepted_by_ordinal": p.acceptedBy, "ram_saves": p.bufferSaves, "ram_restores": p.bufferRestores, "owned_cursor_restores": len(p.pairs), "dos_inputs": count, "end": m.Steps, "negatives": negatives, "original_state_and_saves_equal": true, "seconds": time.Since(started).Seconds()}
	raw, err = json.MarshalIndent(result, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func hdTerrainBatchClone(p *hdTerrainBatchRuntime) *hdTerrainBatchRuntime {
	m := golem.New()
	copy(m.Mem, p.h.m.Mem)
	m.Steps = p.h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = p.h.m.CPU.R, p.h.m.CPU.Seg, p.h.m.CPU.IP, p.h.m.CPU.Flags
	h := *p.h
	h.m = m
	n := *p
	n.h = &h
	h.terrainBatch = &n
	n.trace = false
	n.calls = nil
	n.pairs = nil
	n.entry = nil
	n.pending = map[int]hdTerrainBatchPair{}
	for k, v := range p.pending {
		n.pending[k] = v
	}
	n.backing = map[uint32]hdTerrainBatchCell{}
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
func hdTerrainBatchEntryNegatives(t *testing.T, p *hdTerrainBatchRuntime) []string {
	t.Helper()
	positive := hdTerrainBatchClone(p)
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
		change func(*hdTerrainBatchRuntime)
	}{
		{"wrong-ordinal", func(n *hdTerrainBatchRuntime) { n.h.m.CPU.R[golem.AX] = 65535 }},
		{"wrong-source", func(n *hdTerrainBatchRuntime) { n.h.m.Mem[source] ^= 1 }},
		{"wrong-entry", func(n *hdTerrainBatchRuntime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
		{"wrong-geometry", func(n *hdTerrainBatchRuntime) { n.h.m.Mem[record+8]++ }},
	}
	var result []string
	for _, test := range tests {
		n := hdTerrainBatchClone(p)
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
func hdTerrainBatchFinishNegatives(t *testing.T, p *hdTerrainBatchRuntime) []string {
	t.Helper()
	positive := hdTerrainBatchClone(p)
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
	if opaque < 0 || transparent < 0 {
		t.Fatal("缺正向透明與不透明格")
	}
	address := func(k int) uint32 { return hdTerrainBatchStage + uint32((p.y+k/16)*320+p.x+k%16) }
	tests := []struct {
		name   string
		change func(*hdTerrainBatchRuntime)
	}{
		{"missing-write", func(n *hdTerrainBatchRuntime) { n.counts[opaque] = 0 }},
		{"duplicate-write", func(n *hdTerrainBatchRuntime) { n.counts[opaque]++ }},
		{"transparent-changed", func(n *hdTerrainBatchRuntime) { n.h.m.Mem[address(transparent)] ^= 1 }},
		{"stale-return", func(n *hdTerrainBatchRuntime) { n.h.m.Mem[address(opaque)] ^= 1 }},
	}
	var result []string
	for _, test := range tests {
		n := hdTerrainBatchClone(p)
		test.change(n)
		n.finish()
		if n.accepted != p.accepted || n.rejected != p.rejected+1 {
			t.Fatal("返回錯件未拒絕", p.current.ordinal, test.name)
		}
		result = append(result, fmt.Sprintf("%03d-%s", p.current.ordinal, test.name))
	}
	return result
}

func TestHDWorldTerrainAssetNegatives(t *testing.T) {
	game, assets, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_TERRAIN_BATCH_ASSET_OUTPUT")
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
	definitions := append([]hdTerrainBatchDefinition(nil), hdTerrainBatchDefinitions...)
	for _, d := range hdTerrainForegroundDefinitions {
		definitions = append(definitions, d.hdTerrainBatchDefinition)
	}
	for _, d := range definitions {
		need(os.WriteFile(filepath.Join(copyAssets, d.asset), read(filepath.Join(assets, d.asset)), 0644))
	}
	h := &hdRuntime{m: golem.New()}
	var cases []string
	for _, d := range definitions {
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
			if _, err := loadHDTerrainBatchRuntime(h, copyGame, copyAssets); err == nil {
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
		if _, err := loadHDTerrainBatchRuntime(h, copyGame, copyAssets); err == nil {
			t.Fatal("錯原版來源未拒絕", kind)
		}
		cases = append(cases, "source-"+kind)
		if kind != "missing" {
			need(os.Remove(source))
		}
		need(os.WriteFile(source, originalSource, 0644))
	}
	if _, err := loadHDTerrainBatchRuntime(nil, copyGame, copyAssets); err == nil {
		t.Fatal("缺HD來源仍接受")
	}
	cases = append(cases, "missing-runtime")
	positive, err := loadHDTerrainBatchRuntime(h, copyGame, copyAssets)
	need(err)
	if len(cases) != 166 || len(positive.frames) != 114 || hash(read(filepath.Join(game, "PHYS0.SS"))) != hash(originalSource) {
		t.Fatal("反例後正向或原版不同")
	}
	result := map[string]any{"result": "PASS_TERRAIN_BATCH_166_LOADER_NEGATIVES_AND_POSITIVE_RECHECK", "cases": cases, "positive_after_negatives": true, "original_source_unchanged": true, "production_connected": true}
	raw, err := json.MarshalIndent(result, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDTerrainForegroundSourceGuards(t *testing.T) {
	type call struct {
		Registers                 [8]uint16
		Segments                  [4]uint16
		Stack, Descriptor, Record []uint16
		Entry                     uint64 `json:"entry_step"`
		WritesSHA                 string `json:"sorted_local_offset_value_sha256"`
	}
	var fixtures []struct {
		Ordinal, Length, Opaque int
		Path                    string
		MemorySHA               string `json:"checkpoint_memory_sha256"`
		EncodedSHA              string `json:"encoded_sha256"`
		Call                    call
	}
	fixturePath := os.Getenv("TEST_TERRAIN_FOREGROUND_FIXTURES")
	if fixturePath == "" {
		t.Skip("需要本機原版來源fixture")
	}
	raw, e := os.ReadFile(fixturePath)
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(raw, &fixtures); e != nil {
		t.Fatal(e)
	}
	for _, f := range fixtures {
		t.Run(fmt.Sprint(f.Ordinal), func(t *testing.T) {
			original, e := os.ReadFile(f.Path)
			if e != nil {
				t.Fatal(e)
			}
			if hash(original) != f.MemorySHA {
				t.Fatal("fixture")
			}
			makeFixture := func() (*golem.Machine, *hdTerrainBatchRuntime) {
				m := golem.New()
				copy(m.Mem, original)
				m.CPU.R = f.Call.Registers
				m.CPU.Seg = f.Call.Segments
				m.CPU.IP = 0xa
				m.CPU.Flags = 2
				m.Steps = f.Call.Entry
				stack := uint32(m.CPU.Seg[golem.SS])*16 + uint32(m.CPU.R[golem.SP])
				desc := uint32(m.CPU.Seg[golem.DS])*16 + uint32(m.CPU.R[golem.BX])
				off := uint16(uint32(m.CPU.R[golem.AX])*12 + uint32(f.Call.Stack[3]) + 0x36)
				record := uint32(f.Call.Stack[4])*16 + uint32(off)
				for i, v := range f.Call.Stack {
					binary.LittleEndian.PutUint16(m.Mem[int(stack)+i*2:], v)
				}
				for i, v := range f.Call.Descriptor {
					binary.LittleEndian.PutUint16(m.Mem[int(desc)+i*2:], v)
				}
				for i, v := range f.Call.Record {
					binary.LittleEndian.PutUint16(m.Mem[int(record)+i*2:], v)
				}
				frame := &hdTerrainBatchFrame{hdTerrainBatchDefinition: hdTerrainBatchDefinition{ordinal: f.Ordinal, length: f.Length, opaque: f.Opaque, encoded: f.EncodedSHA, writes: f.Call.WritesSHA}}
				p := &hdTerrainBatchRuntime{h: &hdRuntime{m: m}, frames: map[int]*hdTerrainBatchFrame{f.Ordinal: frame}, acceptedBy: map[int]uint64{}, cursorRestoresBy: map[int]uint64{}, pending: map[int]hdTerrainBatchPair{}, backing: map[uint32]hdTerrainBatchCell{}}
				m.WatchWrite(0, 0x9ffff, func(_ *golem.Machine, a uint32, o, v byte) { p.memoryWrite(a, o, v) })
				return m, p
			}
			cases := []struct {
				name   string
				mutate func(*golem.Machine)
			}{
				{"entry-code", func(m *golem.Machine) { m.Mem[0xd46*16+0xa] ^= 1 }},
				{"wrong-AX", func(m *golem.Machine) { m.CPU.R[golem.AX] += 2000 }},
				{"descriptor-height", func(m *golem.Machine) { at := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.BX]); m.Mem[at] ^= 1 }},
				{"descriptor-stride", func(m *golem.Machine) { at := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.BX]); m.Mem[at+2] ^= 1 }},
				{"stage-rejected", func(m *golem.Machine) {
					at := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.BX])
					binary.LittleEndian.PutUint16(m.Mem[at+4:], 0)
					binary.LittleEndian.PutUint16(m.Mem[at+6:], 0x3c50)
				}},
				{"negative-X", func(m *golem.Machine) { m.CPU.R[golem.DX] = 0xffff }},
				{"right-edge", func(m *golem.Machine) { m.CPU.R[golem.DX] = 305 }},
				{"negative-Y", func(m *golem.Machine) {
					at := int(m.CPU.Seg[golem.SS])*16 + int(m.CPU.R[golem.SP])
					binary.LittleEndian.PutUint16(m.Mem[at+4:], 0xffff)
				}},
				{"bottom-edge", func(m *golem.Machine) {
					at := int(m.CPU.Seg[golem.SS])*16 + int(m.CPU.R[golem.SP])
					binary.LittleEndian.PutUint16(m.Mem[at+4:], 185)
				}},
				{"record-size", func(m *golem.Machine) {
					off := uint16(uint32(m.CPU.R[golem.AX])*12 + uint32(f.Call.Stack[3]) + 0x36)
					at := int(f.Call.Stack[4])*16 + int(off)
					m.Mem[at+8] ^= 1
				}},
				{"encoded-source", func(m *golem.Machine) { at := int(f.Call.Record[1])*16 + int(f.Call.Record[0]); m.Mem[at] ^= 1 }},
			}
			for _, v := range cases {
				t.Run(v.name, func(t *testing.T) {
					m, p := makeFixture()
					v.mutate(m)
					p.beforeInstruction()
					if p.active || p.accepted != 0 {
						t.Fatal("invalid entry accepted")
					}
				})
			}
			m, p := makeFixture()
			p.beforeInstruction()
			if !p.active || p.destination != hdBuildingCanvas {
				t.Fatal("positive Main entry rejected")
			}
			for i := 0; i < 100000 && p.accepted == 0; i++ {
				if e := m.CPU.Step(); e != nil {
					t.Fatal(e)
				}
				m.Steps++
				p.beforeInstruction()
			}
			if p.accepted != 1 || p.rejected != 0 {
				t.Fatal("positive complete return", p.accepted, p.rejected)
			}
			first := -1
			for k, n := range p.counts {
				if n == 1 {
					first = k
					break
				}
			}
			if first < 0 {
				t.Fatal("empty")
			}
			clone := func() *hdTerrainBatchRuntime {
				v := *p
				machine := golem.New()
				copy(machine.Mem, m.Mem)
				v.h = &hdRuntime{m: machine}
				frame := *p.current
				v.current = &frame
				v.acceptedBy = map[int]uint64{}
				v.pending = map[int]hdTerrainBatchPair{}
				v.backing = map[uint32]hdTerrainBatchCell{}
				return &v
			}
			finishes := []struct {
				name   string
				mutate func(*hdTerrainBatchRuntime)
			}{
				{"outside-write", func(v *hdTerrainBatchRuntime) { v.outside = true }},
				{"missing-write", func(v *hdTerrainBatchRuntime) { v.counts[first] = 0 }},
				{"duplicate-write", func(v *hdTerrainBatchRuntime) { v.counts[first] = 2 }},
				{"RAM-mismatch", func(v *hdTerrainBatchRuntime) { v.h.m.Mem[v.destination+uint32((v.y+first/16)*320+v.x+first%16)] ^= 1 }},
				{"opaque-count", func(v *hdTerrainBatchRuntime) { v.current.opaque++ }},
				{"write-digest", func(v *hdTerrainBatchRuntime) { v.current.writes = "wrong" }},
			}
			for _, v := range finishes {
				t.Run(v.name, func(t *testing.T) {
					n := clone()
					before := n.accepted
					v.mutate(n)
					n.finish()
					if n.accepted != before || n.rejected != 1 {
						t.Fatal("invalid completion accepted")
					}
				})
			}
			t.Run("unknown-same-value-revokes", func(t *testing.T) {
				pos := (p.y+first/16)*320 + p.x + first%16
				n := clone()
				if !n.visible[pos].owned {
					t.Fatal("positive cell missing")
				}
				value := n.visible[pos].native
				n.memoryWrite(hdBuildingCanvas+uint32(pos), value, value)
				if n.visible[pos].owned {
					t.Fatal("same-value source survived")
				}
			})
			t.Run("timeout-rejects", func(t *testing.T) {
				m, n := makeFixture()
				n.beforeInstruction()
				m.Steps += 100001
				m.CPU.IP = 0xb
				n.beforeInstruction()
				if n.active || n.rejected != 1 {
					t.Fatal("timeout not rejected")
				}
			})
		})
	}
}

func TestHDTerrainBatchCopyDirection(t *testing.T) {
	for _, backwards := range []bool{false, true} {
		name := "forward-copy"
		if backwards {
			name = "backward-copy-rejected"
		}
		t.Run(name, func(t *testing.T) {
			m := golem.New()
			m.CPU.Seg[golem.CS] = 0xcba
			m.CPU.IP = 0xca
			m.CPU.Seg[golem.DS] = 0x3c50
			m.CPU.Seg[golem.ES] = 0x2cae
			m.CPU.R[golem.SI] = 0
			m.CPU.R[golem.DI] = 0
			m.CPU.R[golem.CX] = 1
			m.CPU.Flags = 2
			if backwards {
				m.CPU.Flags |= 0x400
			}
			copy(m.Mem[0xcba*16+0xca:], []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8})
			m.Mem[hdTerrainBatchStage] = 41
			m.Mem[hdTerrainBatchStage+1] = 42
			p := &hdTerrainBatchRuntime{h: &hdRuntime{m: m}, pending: map[int]hdTerrainBatchPair{}, backing: map[uint32]hdTerrainBatchCell{}}
			p.stage[0] = hdTerrainBatchCell{fromMain: false, owned: true, ordinal: 71, k: 0, native: 41}
			p.stage[1] = hdTerrainBatchCell{fromMain: false, owned: true, ordinal: 71, k: 1, native: 42}
			m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, old, value byte) { p.memoryWrite(a, old, value) })
			if err := m.CPU.Step(); err != nil {
				t.Fatal(err)
			}
			for k := 0; k < 2; k++ {
				if m.Mem[hdBuildingCanvas+uint32(k)] != byte(41+k) {
					t.Fatal("原版複製未執行")
				}
				if p.visible[k].owned == backwards {
					t.Fatal("方向守門未生效", backwards, k)
				}
			}
		})
	}
}

func TestHDLegacyMainSourceGuards(t *testing.T) {
	type call struct {
		Registers                 [8]uint16
		Segments                  [4]uint16
		Stack, Descriptor, Record []uint16
		Entry                     uint64 `json:"entry_step"`
		WritesSHA                 string `json:"sorted_local_offset_value_sha256"`
	}
	var fixtures []struct {
		Ordinal, Length, Opaque int
		Path                    string
		MemorySHA               string `json:"checkpoint_memory_sha256"`
		EncodedSHA              string `json:"encoded_sha256"`
		Call                    call
	}
	path := os.Getenv("TEST_TERRAIN_LEGACY_FIXTURES")
	if path == "" {
		t.Skip("需要本機原版來源fixture")
	}
	raw, e := os.ReadFile(path)
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(raw, &fixtures); e != nil {
		t.Fatal(e)
	}
	for _, f := range fixtures {
		t.Run(fmt.Sprint(f.Ordinal), func(t *testing.T) {
			original, e := os.ReadFile(f.Path)
			if e != nil {
				t.Fatal(e)
			}
			if hash(original) != f.MemorySHA {
				t.Fatal("fixture")
			}
			makeFixture := func() (*golem.Machine, *hdTerrainBatchRuntime) {
				m := golem.New()
				copy(m.Mem, original)
				m.CPU.R = f.Call.Registers
				m.CPU.Seg = f.Call.Segments
				m.CPU.IP = 0xa
				m.CPU.Flags = 2
				m.Steps = f.Call.Entry
				stack := uint32(m.CPU.Seg[golem.SS])*16 + uint32(m.CPU.R[golem.SP])
				desc := uint32(m.CPU.Seg[golem.DS])*16 + uint32(m.CPU.R[golem.BX])
				off := uint16(uint32(m.CPU.R[golem.AX])*12 + uint32(f.Call.Stack[3]) + 0x36)
				record := uint32(f.Call.Stack[4])*16 + uint32(off)
				for i, v := range f.Call.Stack {
					binary.LittleEndian.PutUint16(m.Mem[int(stack)+i*2:], v)
				}
				for i, v := range f.Call.Descriptor {
					binary.LittleEndian.PutUint16(m.Mem[int(desc)+i*2:], v)
				}
				for i, v := range f.Call.Record {
					binary.LittleEndian.PutUint16(m.Mem[int(record)+i*2:], v)
				}
				frame := &hdTerrainBatchFrame{hdTerrainBatchDefinition: hdTerrainBatchDefinition{ordinal: f.Ordinal, length: f.Length, opaque: f.Opaque, encoded: f.EncodedSHA, writes: f.Call.WritesSHA}}
				p := &hdTerrainBatchRuntime{h: &hdRuntime{m: m}, frames: map[int]*hdTerrainBatchFrame{f.Ordinal: frame}, acceptedBy: map[int]uint64{}, cursorRestoresBy: map[int]uint64{}, pending: map[int]hdTerrainBatchPair{}, backing: map[uint32]hdTerrainBatchCell{}}
				m.WatchWrite(0, 0x9ffff, func(_ *golem.Machine, a uint32, o, v byte) { p.memoryWrite(a, o, v) })
				return m, p
			}
			cases := []struct {
				name   string
				mutate func(*golem.Machine)
			}{
				{"entry-code", func(m *golem.Machine) { m.Mem[0xd46*16+0xa] ^= 1 }},
				{"wrong-AX", func(m *golem.Machine) { m.CPU.R[golem.AX] += 2000 }},
				{"descriptor-height", func(m *golem.Machine) { at := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.BX]); m.Mem[at] ^= 1 }},
				{"descriptor-stride", func(m *golem.Machine) { at := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.BX]); m.Mem[at+2] ^= 1 }},
				{"wrong-buffer", func(m *golem.Machine) {
					at := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.BX])
					binary.LittleEndian.PutUint16(m.Mem[at+4:], 0)
					binary.LittleEndian.PutUint16(m.Mem[at+6:], 0x2cbf)
				}},
				{"negative-X", func(m *golem.Machine) { m.CPU.R[golem.DX] = 0xffff }},
				{"right-edge", func(m *golem.Machine) { m.CPU.R[golem.DX] = 305 }},
				{"negative-Y", func(m *golem.Machine) {
					at := int(m.CPU.Seg[golem.SS])*16 + int(m.CPU.R[golem.SP])
					binary.LittleEndian.PutUint16(m.Mem[at+4:], 0xffff)
				}},
				{"bottom-edge", func(m *golem.Machine) {
					at := int(m.CPU.Seg[golem.SS])*16 + int(m.CPU.R[golem.SP])
					binary.LittleEndian.PutUint16(m.Mem[at+4:], 185)
				}},
				{"record-size", func(m *golem.Machine) {
					off := uint16(uint32(m.CPU.R[golem.AX])*12 + uint32(f.Call.Stack[3]) + 0x36)
					at := int(f.Call.Stack[4])*16 + int(off)
					m.Mem[at+8] ^= 1
				}},
				{"encoded-source", func(m *golem.Machine) { at := int(f.Call.Record[1])*16 + int(f.Call.Record[0]); m.Mem[at] ^= 1 }},
			}
			for _, v := range cases {
				t.Run(v.name, func(t *testing.T) {
					m, p := makeFixture()
					v.mutate(m)
					p.beforeInstruction()
					if p.active || p.accepted != 0 {
						t.Fatal("invalid entry accepted")
					}
				})
			}
			m, p := makeFixture()
			p.beforeInstruction()
			if !p.active || p.destination != hdBuildingCanvas {
				t.Fatal("positive Main entry rejected")
			}
			for i := 0; i < 100000 && p.accepted == 0; i++ {
				if e := m.CPU.Step(); e != nil {
					t.Fatal(e)
				}
				m.Steps++
				p.beforeInstruction()
			}
			if p.accepted != 1 || p.rejected != 0 {
				t.Fatal("positive complete return", p.accepted, p.rejected)
			}

			t.Run("Stage-scope", func(t *testing.T) {
				machine, stage := makeFixture()
				at := int(machine.CPU.Seg[golem.DS])*16 + int(machine.CPU.R[golem.BX])
				binary.LittleEndian.PutUint16(machine.Mem[at+4:], 0)
				binary.LittleEndian.PutUint16(machine.Mem[at+6:], 0x3c50)
				stage.beforeInstruction()
				if f.Ordinal == 79 {
					if stage.active || stage.accepted != 0 {
						t.Fatal("79 Stage不屬於此Main核心")
					}
					return
				}
				if !stage.active || stage.destination != hdTerrainBatchStage {
					t.Fatal("既有Stage入口失效")
				}
				for k := 0; k < 100000 && stage.accepted == 0; k++ {
					if err := machine.CPU.Step(); err != nil {
						t.Fatal(err)
					}
					machine.Steps++
					stage.beforeInstruction()
				}
				if stage.accepted != 1 || stage.rejected != 0 {
					t.Fatal("既有Stage實際返回失效")
				}
				count := 0
				for _, cell := range stage.stage {
					if cell.owned {
						count++
						if cell.fromMain {
							t.Fatal("Stage起點被誤標Main")
						}
					}
				}
				if count != f.Opaque {
					t.Fatal("Stage遮罩不同", count, f.Opaque)
				}
			})
			first := -1
			for k, n := range p.counts {
				if n == 1 {
					first = k
					break
				}
			}
			if first < 0 {
				t.Fatal("empty")
			}
			clone := func() *hdTerrainBatchRuntime {
				v := *p
				machine := golem.New()
				copy(machine.Mem, m.Mem)
				v.h = &hdRuntime{m: machine}
				frame := *p.current
				v.current = &frame
				v.acceptedBy = map[int]uint64{}
				v.pending = map[int]hdTerrainBatchPair{}
				v.backing = map[uint32]hdTerrainBatchCell{}
				return &v
			}
			finishes := []struct {
				name   string
				mutate func(*hdTerrainBatchRuntime)
			}{
				{"outside-write", func(v *hdTerrainBatchRuntime) { v.outside = true }},
				{"missing-write", func(v *hdTerrainBatchRuntime) { v.counts[first] = 0 }},
				{"duplicate-write", func(v *hdTerrainBatchRuntime) { v.counts[first] = 2 }},
				{"RAM-mismatch", func(v *hdTerrainBatchRuntime) { v.h.m.Mem[v.destination+uint32((v.y+first/16)*320+v.x+first%16)] ^= 1 }},
				{"opaque-count", func(v *hdTerrainBatchRuntime) { v.current.opaque++ }},
				{"write-digest", func(v *hdTerrainBatchRuntime) { v.current.writes = "wrong" }},
			}
			for _, v := range finishes {
				t.Run(v.name, func(t *testing.T) {
					n := clone()
					before := n.accepted
					v.mutate(n)
					n.finish()
					if n.accepted != before || n.rejected != 1 {
						t.Fatal("invalid completion accepted")
					}
				})
			}
			t.Run("unknown-same-value-revokes", func(t *testing.T) {
				pos := (p.y+first/16)*320 + p.x + first%16
				n := clone()
				if !n.visible[pos].owned {
					t.Fatal("positive cell missing")
				}
				value := n.visible[pos].native
				n.memoryWrite(hdBuildingCanvas+uint32(pos), value, value)
				if n.visible[pos].owned {
					t.Fatal("same-value source survived")
				}
			})
			t.Run("timeout-rejects", func(t *testing.T) {
				m, n := makeFixture()
				n.beforeInstruction()
				m.Steps += 100001
				m.CPU.IP = 0xb
				n.beforeInstruction()
				if n.active || n.rejected != 1 {
					t.Fatal("timeout not rejected")
				}
			})
		})
	}
}

func TestHDLegacyMainOriginCopies(t *testing.T) {
	makeRuntime := func() (*golem.Machine, *hdTerrainBatchRuntime, func(uint16, uint16, uint16, uint16)) {
		m := golem.New()
		p := &hdTerrainBatchRuntime{h: &hdRuntime{m: m}, pending: map[int]hdTerrainBatchPair{}, backing: map[uint32]hdTerrainBatchCell{}, accepted: 1}
		copy(m.Mem[0xcba*16+0xca:], []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8})
		m.WatchWrite(0, 0x9ffff, func(_ *golem.Machine, a uint32, old, value byte) { p.memoryWrite(a, old, value) })
		move := func(ds, si, es, di uint16) {
			m.CPU.Seg[golem.CS] = 0xcba
			m.CPU.IP = 0xca
			m.CPU.Seg[golem.DS] = ds
			m.CPU.Seg[golem.ES] = es
			m.CPU.R[golem.SI] = si
			m.CPU.R[golem.DI] = di
			m.CPU.R[golem.CX] = 1
			m.CPU.Flags = 2
			if err := m.CPU.Step(); err != nil {
				t.Fatal(err)
			}
		}
		return m, p, move
	}
	t.Run("Main-buffer-roundtrip", func(t *testing.T) {
		m, p, move := makeRuntime()
		for k := 0; k < 2; k++ {
			m.Mem[hdBuildingCanvas+uint32(k)] = byte(41 + k)
			p.visible[k] = hdTerrainBatchCell{owned: true, fromMain: true, ordinal: 71, k: byte(k), native: byte(41 + k)}
		}
		move(0x2cae, 0, 0x5000, 0)
		for k := 0; k < 2; k++ {
			c := p.backing[0x50000+uint32(k)]
			if !c.owned || !c.fromMain {
				t.Fatal("Main起點未存入背景", k)
			}
		}
		move(0x5000, 0, 0x2cae, 16)
		for k := 0; k < 2; k++ {
			c := p.visible[16+k]
			if !c.owned || !c.fromMain || c.k != byte(k) {
				t.Fatal("Main起點未隨還原保留", k, c)
			}
		}
	})
	t.Run("Main-to-Main-revokes", func(t *testing.T) {
		m, p, move := makeRuntime()
		for k := 0; k < 2; k++ {
			m.Mem[hdBuildingCanvas+uint32(k)] = byte(41 + k)
			p.visible[k] = hdTerrainBatchCell{owned: true, fromMain: true, ordinal: 71, k: byte(k), native: byte(41 + k)}
			p.visible[16+k] = p.visible[k]
		}
		move(0x2cae, 0, 0x2cae, 16)
		for k := 0; k < 2; k++ {
			if p.visible[16+k].owned {
				t.Fatal("Main到Main錯授來源", k)
			}
		}
	})
	t.Run("Stage-origin-copy", func(t *testing.T) {
		m, p, move := makeRuntime()
		for k := 0; k < 2; k++ {
			m.Mem[hdTerrainBatchStage+uint32(k)] = byte(41 + k)
			p.stage[k] = hdTerrainBatchCell{owned: true, fromMain: false, ordinal: 71, k: byte(k), native: byte(41 + k)}
		}
		move(0x3c50, 0, 0x2cae, 16)
		for k := 0; k < 2; k++ {
			c := p.visible[16+k]
			if !c.owned || c.fromMain {
				t.Fatal("Stage起點被誤標Main", k, c)
			}
		}
	})
}
func TestHDLegacyMainPalettePreservesStage(t *testing.T) {
	path := os.Getenv("TEST_TERRAIN_LEGACY_PALETTE")
	if path == "" {
		t.Skip("需要本機原版色盤")
	}
	reference, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if !hdTerrainLegacyMainPaletteSupported(reference) {
		t.Fatal("原版色盤不符")
	}
	indices := []int{-1, 39, 41, 54, 56, 64, 65, 66, 67, 68, 69, 70, 71, 84, 86, 100, 101, 102}
	for _, index := range indices {
		for _, main := range []bool{false, true} {
			name := "normal"
			if index >= 0 {
				name = fmt.Sprintf("changed-%03d", index)
			}
			name += fmt.Sprint("/Main=", main)
			t.Run(name, func(t *testing.T) {
				pal := append([]byte(nil), reference...)
				if index >= 0 {
					pal[index*3] ^= 1
				}
				m := golem.New()
				p := &hdTerrainBatchRuntime{h: &hdRuntime{m: m}, frames: map[int]*hdTerrainBatchFrame{71: {art: image.NewRGBA(image.Rect(0, 0, 64, 64))}}}
				for y := 0; y < 64; y++ {
					for x := 0; x < 64; x++ {
						p.frames[71].art.SetRGBA(x, y, color.RGBA{50, 100, 20, 255})
					}
				}
				p.visible[0] = hdTerrainBatchCell{owned: true, fromMain: main, ordinal: 71, k: 0, native: 41}
				canvas := make([]byte, 64000)
				canvas[0] = 41
				receipt := p.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), draftNativeFrame{canvas: canvas, palette: pal})
				want := 1
				if main && index >= 0 {
					want = 0
				}
				if receipt["painted"].(int) != want {
					t.Fatal("Main與既有Stage色盤邊界不同", main, index, receipt)
				}
			})
		}
	}
}
