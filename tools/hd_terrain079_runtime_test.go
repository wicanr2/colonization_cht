package main

import (
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
	"time"

	golem "github.com/wicanr2/dosgolem"
)

// 使用真實GUI收據、合法原版與原版產生的存檔；不自行製造像素或遊戲狀態。
func TestHDTerrain079RuntimeNativeLifecycle(t *testing.T) {
	game, receiptRoot, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_RECEIPTS"), os.Getenv("TEST_HD_TERRAIN079_OUTPUT")
	if game == "" || receiptRoot == "" || out == "" {
		t.Skip("需要合法原版與本機HD研究收據")
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(p string) []byte { t.Helper(); b, err := os.ReadFile(p); need(err); return b }
	for _, name := range []string{"OPENING.EXE", "VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "ICONS.SS"} {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版輸入：", name)
		} else {
			need(err)
		}
	}
	for name, want := range map[string]string{
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4",
	} {
		if hash(read(filepath.Join(game, name))) != want {
			t.Fatal("原版指紋不同", name)
		}
	}
	gui := filepath.Join(receiptRoot, "lifecycle-r29-r1/gui")
	input := read(filepath.Join(gui, "gui.inputs.json"))
	if hash(input) != "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca" {
		t.Fatal("實際GUI輸入指紋不同")
	}
	var replay struct {
		Inputs []windowInput
		End    uint64
	}
	need(json.Unmarshal(input, &replay))
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
	need(json.Unmarshal(read(filepath.Join(receiptRoot, "lifecycle-public-r29-r1/observed/gui-points.json")), &points))
	if len(points) != 49 || len(replay.Inputs) != 53 || replay.End != 134600000 {
		t.Fatal("正常路徑收據範圍不同")
	}
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatal("需新的本機輸出目錄")
	}
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "save")
	need(os.Mkdir(scratch, 0755))
	seed := read(filepath.Join(gui, "save/COLONY09.SAV"))
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
		t.Fatal("缺少原版數位音效能力")
	}
	m.EnableOPLSynth(true)
	h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))
	need(err)
	h.terrain079.trace = true
	if h.terrain079 == nil {
		t.Fatal("正式海洋未載入")
	}
	var negatives []string
	entryChecked, finishChecked, ownershipChecked := false, false, false
	bufferChecked := false
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		if !bufferChecked && h.terrain079.bufferSaves > 0 && m.CPU.IP == 0xca {
			if cases, ok := hdTerrain079BufferNegatives(t, h.terrain079); ok {
				negatives = append(negatives, cases...)
				bufferChecked = true
			}
		}
		if !entryChecked && h.terrain079.active {
			negatives = append(negatives, hdTerrain079EntryNegatives(t, h.terrain079)...)
			entryChecked = true
		}
		if !finishChecked && h.terrain079.accepted > 0 {
			negatives = append(negatives, hdTerrain079FinishNegatives(t, h.terrain079)...)
			finishChecked = true
		}
	})
	started := time.Now()
	count, at := uint64(0), 0
	var records []map[string]any
	expected := map[uint64]int{75400000: 621, 119000000: 621, 121400000: 460, 125600000: 460,
		102200000: 0, 106200000: 0, 110600000: 0, 129800000: 0, 134000000: 0}
	capture := func() {
		if at == len(points) {
			return
		}
		p := points[at]
		if m.Steps > p.Step || (m.Steps == p.Step && count > p.Count) {
			t.Fatal("略過GUI檢查點", at, m.Steps, count)
		}
		if m.Steps != p.Step || count != p.Count {
			return
		}
		c := m.CPU
		if hash(m.Mem) != p.Memory || hash(m.Indexed()) != p.Indexed || hash(m.DAC[:]) != p.Palette ||
			c.R != p.Registers || c.Seg != p.Segments || c.IP != p.IP || c.Flags != p.Flags {
			t.Fatal("正式HD改變原版狀態", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:],
			cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		var oracle map[int]struct {
			Ordinal int  `json:"ordinal"`
			Local   int  `json:"local"`
			Native  byte `json:"native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_HD_TERRAIN079_MODEL"), fmt.Sprintf("point-%03d.terrain-model.json", at))), &oracle))
		cells := map[int]map[string]any{}
		for pos, cell := range h.terrain079.visible {
			want, ok := oracle[pos]
			owned := ok && want.Ordinal == 79
			if cell.owned != owned || (owned && (int(cell.k) != want.Local || cell.native != want.Native || f.canvas[pos] != cell.native)) {
				t.Fatal("地形來源與獨立原版模型不同", at, pos, cell, want)
			}
			if owned {
				cells[pos] = map[string]any{"ordinal": 79, "local": int(cell.k), "native": cell.native}
			}
		}
		ram, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		base, record := h.base(f)
		h.restoreCursor(base, f)
		if p.Step == 64600000 || p.Step == 75400000 || p.Step == 110600000 {
			var nativeNS, hdNS []int64
			for trial := 0; trial < 5; trial++ {
				start := time.Now()
				draftRGB(f.indexed, f.palette)
				nativeNS = append(nativeNS, time.Since(start).Nanoseconds())
				start = time.Now()
				im, _ := h.base(f)
				h.restoreCursor(im, f)
				hdNS = append(hdNS, time.Since(start).Nanoseconds())
			}
			record["composition_nanoseconds"] = map[string]any{"native": nativeNS, "hd": hdNS, "samples": 5}
		}
		if hash(m.Mem) != ram || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("合成改變原版", at)
		}
		if want, ok := expected[p.Step]; ok && record["painted"].(int) != want {
			t.Fatalf("HD point %d step %d: %+v want painted %d", at, p.Step, record, want)
		}
		if !ownershipChecked {
			if sea, ok := record["terrain079"].(map[string]any); ok && sea["painted"].(int) > 0 {
				negatives = append(negatives, hdTerrain079OwnershipNegatives(t, h.terrain079, f)...)
				ownershipChecked = true
			}
		}
		native := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if image.Pt(x, y).In(image.Rect(224, 52, 316, 160)) || h.sea.visible[(y/4)*320+x/4].owned {
					continue
				}
				if cell := h.terrain079.visible[(y/4)*320+x/4]; cell.owned && cell.native == f.canvas[(y/4)*320+x/4] {
					continue
				}
				if h.person != nil {
					cell := h.person.visible[(y/4)*320+x/4]
					if cell.owned && cell.native == f.canvas[(y/4)*320+x/4] {
						continue
					}
				}
				if h.shelter != nil {
					cell := h.shelter.visible[(y/4)*320+x/4]
					if cell.owned && cell.native == f.canvas[(y/4)*320+x/4] {
						continue
					}
				}
				if h.nine != nil {
					cell := h.nine.visible[(y/4)*320+x/4]
					if cell.owned && cell.native == f.canvas[(y/4)*320+x/4] {
						continue
					}
				}
				if h.small != nil {
					i := (y/4)*320 + x/4
					cell := h.small.visible[i]
					if cell.owned && cell.native == f.canvas[i] && h.small.frames[cell.slot].art != nil {
						continue
					}
				}
				if cell := h.terrainBatch.visible[(y/4)*320+x/4]; cell.owned && cell.native == f.canvas[(y/4)*320+x/4] {
					continue
				}
				if cell := h.smallTerrain.visible[(y/4)*320+x/4]; cell.owned && cell.native == f.canvas[(y/4)*320+x/4] {
					continue
				}
				if base.RGBAAt(x, y) != native.RGBAAt(x, y) {
					t.Fatal("HD越出已驗建築與海洋範圍", at, x, y)
				}
			}
		}
		if source, ok := h.cursorValid(f); ok {
			for k, v := range source {
				if v == 255 {
					continue
				}
				x, y := f.cursor.Min.X+k%16, f.cursor.Min.Y+k/16
				if x < 0 || y < 0 || x >= 320 || y >= 200 {
					continue
				}
				for j := 0; j < 4; j++ {
					for i := 0; i < 4; i++ {
						if base.RGBAAt(x*4+i, y*4+j) != native.RGBAAt(x*4+i, y*4+j) {
							t.Fatal("不透明游標被HD蓋住", at, k)
						}
					}
				}
			}
		}
		record["terrain079_cells"] = cells
		record["terrain079_source"] = h.terrain079.receipt(f)
		prefix := filepath.Join(out, fmt.Sprintf("point-%03d", at))
		file, err := os.Create(prefix + ".png")
		need(err)
		need(png.Encode(file, base))
		need(file.Close())
		for suffix, data := range map[string][]byte{".memory": m.Mem, ".idx": f.indexed, ".canvas": f.canvas, ".palette": f.palette, ".cursor": m.Mem[0x1cd74:0x1ce74]} {
			need(os.WriteFile(prefix+suffix, data, 0644))
		}
		record["step"], record["point"], record["original_state_equal"] = p.Step, at, true
		records = append(records, record)
		at++
	}
	step := func() {
		capture()
		need(m.Step())
	}
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
	if at != 49 || h.accepted != 10 || h.cursorRestores != 1050 || h.terrain079.accepted != 27 {
		t.Fatalf("正式HD未走完已驗路徑：points=%d accepted=%d rejected=%d paints=%d restores=%d", at, h.accepted, h.rejected, h.cursorPaints, h.cursorRestores)
	}
	if !entryChecked || !finishChecked || !ownershipChecked || !bufferChecked || len(negatives) != 31 {
		t.Fatalf("海洋反例未完整驗證：%v", negatives)
	}
	d.Close()
	for _, name := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		if hash(read(filepath.Join(scratch, name))) != hash(read(filepath.Join(gui, "save", name))) {
			t.Fatal("正式HD改變存檔", name)
		}
	}
	data, err := json.MarshalIndent(map[string]any{"result": "PASS_TERRAIN079_FORMAL_NATIVE_49", "production_connected": true, "points": records,
		"accepted_calls": h.accepted, "cursor_restore_points": h.cursorRestores, "dos_inputs": count, "end": m.Steps,
		"negative_cases": negatives, "terrain079_accepted_calls": h.terrain079.accepted, "terrain079_cursor_paints": h.terrain079.cursorPaints, "terrain079_cursor_restores": h.terrain079.cursorRestores, "replay_seconds": time.Since(started).Seconds()}, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(data, '\n'), 0644))
}

// 反例只修改真實執行期狀態的隔離副本，不供正式遊玩或正向對拍使用。
func hdTerrain079Clone(p *hdTerrain079Runtime) *hdTerrain079Runtime {
	m := golem.New()
	copy(m.Mem, p.h.m.Mem)
	m.Steps = p.h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = p.h.m.CPU.R, p.h.m.CPU.Seg, p.h.m.CPU.IP, p.h.m.CPU.Flags
	h := *p.h
	h.m = m
	n := *p
	n.h = &h
	n.trace = false
	n.calls = nil
	n.pairs = nil
	n.entry = nil
	h.terrain079 = &n
	n.pending = map[int]hdTerrain079Pair{}
	for k, v := range p.pending {
		n.pending[k] = v
	}
	n.backing = map[uint32]hdTerrain079Cell{}
	for k, v := range p.backing {
		n.backing[k] = v
	}
	return &n
}

// 只在正常重播實際還原指令之前取樣；正向副本執行該原始REP，不製造遊戲狀態。
func hdTerrain079BufferNegatives(t *testing.T, p *hdTerrain079Runtime) ([]string, bool) {
	t.Helper()
	c := p.h.m.CPU
	if c.Seg[golem.CS] != 0xcba || c.IP != 0xca {
		return nil, false
	}
	src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI])
	dst := int(c.Seg[golem.ES])*16 + int(c.R[golem.DI])
	width := int(c.R[golem.CX]) * 2
	if dst < int(hdBuildingCanvas) || dst+width > int(hdBuildingCanvas)+64000 {
		return nil, false
	}
	at := -1
	for i := 0; i < width; i++ {
		if v := p.backing[uint32(src+i)]; v.owned && v.native == p.h.m.Mem[src+i] {
			at = i
			break
		}
	}
	if at < 0 {
		return nil, false
	}
	source := uint32(src + at)
	dest := uint32(dst + at)
	pixel := int(dest - hdBuildingCanvas)
	cell := p.backing[source]
	execute := func(n *hdTerrain079Runtime) {
		n.h.m.WatchWrite(0, uint32(len(n.h.m.Mem)-1), func(_ *golem.Machine, a uint32, old, value byte) { n.memoryWrite(a, old, value) })
		if err := n.h.m.CPU.Step(); err != nil {
			t.Fatal("隔離原版複製指令失敗", err)
		}
	}
	positive := hdTerrain079Clone(p)
	execute(positive)
	if positive.visible[pixel] != cell || positive.h.m.Mem[dest] != cell.native {
		t.Fatal("實際背景來源未還原")
	}
	pc := int(c.Seg[golem.CS])*16 + int(c.IP)
	mutations := []struct {
		name   string
		change func(*hdTerrain079Runtime)
	}{
		{"buffer-unknown-same-write", func(n *hdTerrain079Runtime) { n.memoryWrite(source, n.h.m.Mem[source], n.h.m.Mem[source]) }},
		{"buffer-unknown-changed-write", func(n *hdTerrain079Runtime) {
			old := n.h.m.Mem[source]
			n.h.m.Mem[source] ^= 1
			n.memoryWrite(source, old, n.h.m.Mem[source])
		}},
		{"buffer-stale-native-source", func(n *hdTerrain079Runtime) { n.h.m.Mem[source] ^= 1 }},
		{"buffer-missing-ownership", func(n *hdTerrain079Runtime) { delete(n.backing, source) }},
		{"buffer-wrong-copy-code", func(n *hdTerrain079Runtime) { n.h.m.Mem[pc+2] ^= 1 }},
		{"buffer-wrong-copy-site", func(n *hdTerrain079Runtime) {
			n.h.m.CPU.IP = 0x300
			a := int(c.Seg[golem.CS])*16 + 0x300
			copy(n.h.m.Mem[a:a+16], p.h.m.Mem[pc:pc+16])
		}},
		{"buffer-wrong-source-pointer", func(n *hdTerrain079Runtime) { n.h.m.CPU.Seg[golem.DS] = 0 }},
	}
	var names []string
	for _, test := range mutations {
		n := hdTerrain079Clone(p)
		test.change(n)
		execute(n)
		if n.visible[pixel].owned {
			t.Fatal("背景還原未拒絕反例", test.name)
		}
		names = append(names, test.name)
	}
	// 取已完成還原的獨立副本，以未知來源覆寫同值，亦須撤銷。
	n := hdTerrain079Clone(positive)
	n.memoryWrite(dest, n.h.m.Mem[dest], n.h.m.Mem[dest])
	if n.visible[pixel].owned {
		t.Fatal("還原後未知同值覆寫未撤銷")
	}
	return append(names, "buffer-restored-unknown-overwrite"), true
}
func hdTerrain079EntryNegatives(t *testing.T, p *hdTerrain079Runtime) []string {
	t.Helper()
	positive := hdTerrain079Clone(p)
	positive.active = false
	positive.beforeInstruction()
	if !positive.active {
		t.Fatal("實際海洋入口未被接受")
	}
	c := p.h.m.CPU
	stack, _ := hdBuildingWords(p.h.m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	at := int(stack[4])*16 + int(uint16(80*12+uint32(stack[3])+0x36))
	rec, _ := hdBuildingWords(p.h.m.Mem, stack[4], uint16(80*12+uint32(stack[3])+0x36), 6)
	source := int(rec[1])*16 + int(rec[0])
	mutations := []struct {
		name   string
		change func(*hdTerrain079Runtime)
	}{
		{"wrong-frame", func(n *hdTerrain079Runtime) { n.h.m.CPU.R[golem.AX]++ }},
		{"negative-x", func(n *hdTerrain079Runtime) { n.h.m.CPU.R[golem.DX] = 65535 }},
		{"clipped-right", func(n *hdTerrain079Runtime) { n.h.m.CPU.R[golem.DX] = 305 }},
		{"negative-y", func(n *hdTerrain079Runtime) {
			a := int(c.Seg[golem.SS])*16 + int(c.R[golem.SP]) + 4
			n.h.m.Mem[a] = 255
			n.h.m.Mem[a+1] = 255
		}},
		{"wrong-destination", func(n *hdTerrain079Runtime) { n.h.m.Mem[int(c.Seg[golem.DS])*16+int(c.R[golem.BX])+6]++ }},
		{"wrong-width", func(n *hdTerrain079Runtime) { n.h.m.Mem[at+8]++ }},
		{"wrong-source-pointer", func(n *hdTerrain079Runtime) { n.h.m.Mem[at]++ }},
		{"wrong-source-bytes", func(n *hdTerrain079Runtime) { n.h.m.Mem[source] ^= 1 }},
		{"wrong-entry-code", func(n *hdTerrain079Runtime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
	}
	var names []string
	for _, test := range mutations {
		n := hdTerrain079Clone(p)
		n.active = false
		test.change(n)
		n.beforeInstruction()
		if n.active || n.accepted != p.accepted {
			t.Fatal("未拒絕海洋入口反例", test.name)
		}
		names = append(names, test.name)
	}
	n := hdTerrain079Clone(positive)
	n.h.m.Steps += 100001
	n.h.m.CPU.IP++
	n.beforeInstruction()
	if n.active || n.rejected != positive.rejected+1 {
		t.Fatal("未拒絕海洋逾時")
	}
	return append(names, "missing-return-timeout")
}
func hdTerrain079FinishNegatives(t *testing.T, p *hdTerrain079Runtime) []string {
	t.Helper()
	positive := hdTerrain079Clone(p)
	positive.stage = [64000]hdTerrain079Cell{}
	positive.finish()
	if positive.accepted != p.accepted+1 {
		t.Fatal("實際完整海洋返回未被接受")
	}
	mutations := []struct {
		name   string
		change func(*hdTerrain079Runtime)
	}{
		{"missing-draw-write", func(n *hdTerrain079Runtime) { n.counts[0] = 0 }},
		{"duplicate-draw-write", func(n *hdTerrain079Runtime) { n.counts[0]++ }},
		{"outside-draw-write", func(n *hdTerrain079Runtime) { n.outside = true }},
		{"wrong-draw-pixels", func(n *hdTerrain079Runtime) { n.writes[0] ^= 1 }},
		{"stale-return-pixel", func(n *hdTerrain079Runtime) { n.h.m.Mem[hdTerrain079Stage+uint32(n.y*320+n.x)] ^= 1 }},
	}
	var names []string
	for _, test := range mutations {
		n := hdTerrain079Clone(p)
		n.stage = [64000]hdTerrain079Cell{}
		test.change(n)
		n.finish()
		if n.accepted != p.accepted || n.rejected != p.rejected+1 {
			t.Fatal("未拒絕海洋返回反例", test.name)
		}
		for _, c := range n.stage {
			if c.owned {
				t.Fatal("拒絕後仍有海洋來源", test.name)
			}
		}
		names = append(names, test.name)
	}
	return names
}
func hdTerrain079OwnershipNegatives(t *testing.T, p *hdTerrain079Runtime, f draftNativeFrame) []string {
	t.Helper()
	pixel := -1
	for i, c := range p.visible {
		if c.owned && f.canvas[i] == c.native {
			pixel = i
			break
		}
	}
	if pixel < 0 {
		t.Fatal("沒有實際可見海洋")
	}
	frame := func(n *hdTerrain079Runtime) draftNativeFrame {
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		return g
	}
	paint := func(n *hdTerrain079Runtime) int {
		return n.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), frame(n))["painted"].(int)
	}
	baseline := paint(hdTerrain079Clone(p))
	var names []string
	for _, same := range []bool{true, false} {
		for _, stage := range []bool{true, false} {
			n := hdTerrain079Clone(p)
			old := n.h.m.Mem[hdBuildingCanvas+uint32(pixel)]
			value := old
			kind := "changed"
			if same {
				kind = "same"
			} else {
				value ^= 1
			}
			name := "unknown-canvas-" + kind + "-write"
			if stage {
				at := -1
				for i, c := range n.stage {
					if c.owned {
						at = i
						break
					}
				}
				if at < 0 {
					t.Fatal("沒有實際暫存來源")
				}
				addr := hdTerrain079Stage + uint32(at)
				old = n.h.m.Mem[addr]
				value = old
				if !same {
					value ^= 1
				}
				n.h.m.Mem[addr] = value
				n.stageWrite(addr, old, value)
				if n.stage[at].owned {
					t.Fatal("暫存覆寫未撤銷來源")
				}
				name = "unknown-stage-" + kind + "-write"
			} else {
				addr := hdBuildingCanvas + uint32(pixel)
				n.h.m.Mem[addr] = value
				n.canvasWrite(addr, old, value)
				if n.visible[pixel].owned || paint(n) != baseline-1 {
					t.Fatal("主畫布覆寫未撤銷來源", name)
				}
			}
			names = append(names, name)
		}
	}
	n := hdTerrain079Clone(p)
	n.h.m.Mem[hdBuildingCanvas+uint32(pixel)] ^= 1
	if paint(n) != baseline-1 {
		t.Fatal("過期海洋仍繪製")
	}
	names = append(names, "stale-native-pixel")
	n = hdTerrain079Clone(p)
	n.pending[pixel] = hdTerrain079Pair{cell: n.visible[pixel]}
	addr := hdBuildingCanvas + uint32(pixel)
	n.canvasWrite(addr, n.h.m.Mem[addr], n.h.m.Mem[addr])
	if len(n.pending) != 0 {
		t.Fatal("未知覆寫未撤銷未完成游標配對")
	}
	names = append(names, "interleaved-cursor-pair")
	for _, test := range []struct {
		name string
		at   int
	}{{"unknown-cursor-source", 0x1cd74}, {"incomplete-cursor-buffer", 0xafb00}} {
		n = hdTerrain079Clone(p)
		n.h.m.Mem[test.at] ^= 1
		_, record := n.h.base(frame(n))
		if record["reason"] != "unverified-cursor-or-native-surface" || record["terrain079"] != nil {
			t.Fatal("未知游標仍繪海洋", test.name, record)
		}
		names = append(names, test.name)
	}
	return names
}
