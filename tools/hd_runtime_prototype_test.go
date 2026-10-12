package main

import (
	"encoding/json"
	"image"
	"os"
	"path/filepath"
	"testing"
	"time"

	golem "github.com/wicanr2/dosgolem"
)

// 使用真實GUI收據、合法原版與原版產生的存檔；不自行製造像素或遊戲狀態。
func TestHDPrototypeNativeLifecycle(t *testing.T) {
	game, receiptRoot, asset, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_RECEIPTS"), os.Getenv("TEST_HD_ASSET"), os.Getenv("TEST_HD_OUTPUT")
	if game == "" || receiptRoot == "" || asset == "" || out == "" {
		t.Skip("需要合法原版與本機HD研究收據")
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(p string) []byte { t.Helper(); b, err := os.ReadFile(p); need(err); return b }
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
	h, err := newHDPrototype(m, asset)
	need(err)
	m.SetBeforeInstruction(h.beforeInstruction)
	started := time.Now()
	var negativeCases []string
	entryChecked, ownershipChecked := false, false
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
			t.Fatal("原型改變原版狀態", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdProtoCanvas : hdProtoCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:],
			cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		ram, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		base, record := h.base(f)
		h.restoreCursor(base, f)
		if p.Step == 75400000 && !ownershipChecked {
			negativeCases = append(negativeCases, hdProtoCheckOwnershipRejections(t, h, f)...)
			ownershipChecked = true
		}
		if hash(m.Mem) != ram || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("合成改變原版", at)
		}
		if want, ok := expected[p.Step]; ok && record["painted"].(int) != want {
			t.Fatalf("HD point %d step %d: %+v want painted %d", at, p.Step, record, want)
		}
		native := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if image.Pt(x, y).In(image.Rect(224, 52, 316, 160)) {
					continue
				}
				if base.RGBAAt(x, y) != native.RGBAAt(x, y) {
					t.Fatal("HD越出已驗建築範圍", at, x, y)
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
		record["step"], record["point"], record["original_state_equal"] = p.Step, at, true
		records = append(records, record)
		at++
	}
	step := func() {
		capture()
		if !entryChecked && m.CPU.Seg[golem.CS] == 0xd46 && m.CPU.IP == 0xa &&
			m.CPU.R[golem.AX] == 33 && m.CPU.R[golem.DX] == 56 {
			negativeCases = append(negativeCases, hdProtoCheckEntryRejections(t, h)...)
			entryChecked = true
		}
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
	if at != 49 || h.accepted != 10 || h.cursorRestores != 1050 || !entryChecked || !ownershipChecked {
		t.Fatalf("原型未走完已驗路徑：points=%d accepted=%d rejected=%d paints=%d restores=%d", at, h.accepted, h.rejected, h.cursorPaints, h.cursorRestores)
	}
	d.Close()
	for _, name := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		if hash(read(filepath.Join(scratch, name))) != hash(read(filepath.Join(gui, "save", name))) {
			t.Fatal("原型改變存檔", name)
		}
	}
	data, err := json.MarshalIndent(map[string]any{"result": "PASS_HD_RUNTIME_NATIVE_REPLAY", "points": records,
		"accepted_calls": h.accepted, "cursor_restore_points": h.cursorRestores, "dos_inputs": count, "end": m.Steps,
		"negative_cases": negativeCases, "replay_seconds": time.Since(started).Seconds()}, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(data, '\n'), 0644))
}

// 反例只改實際執行狀態的私有複本，不修改正常路徑的Machine。
func hdProtoClone(h *hdPrototype) *hdPrototype {
	m := golem.New()
	copy(m.Mem, h.m.Mem)
	m.Steps = h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = h.m.CPU.R, h.m.CPU.Seg, h.m.CPU.IP, h.m.CPU.Flags
	cloned := *h
	cloned.m = m
	cloned.pending = map[int]hdProtoPixel{}
	for k, v := range h.pending {
		cloned.pending[k] = v
	}
	cloned.writes = map[int]byte{}
	for k, v := range h.writes {
		cloned.writes[k] = v
	}
	cloned.counts = map[int]int{}
	for k, v := range h.counts {
		cloned.counts[k] = v
	}
	return &cloned
}
func hdProtoCheckEntryRejections(t *testing.T, h *hdPrototype) []string {
	t.Helper()
	baseline := hdProtoClone(h)
	baseline.active = false
	baseline.beforeInstruction()
	if !baseline.active {
		t.Fatal("實際入口不符合原型")
	}
	c := h.m.CPU
	stack, _ := hdProtoWords(h.m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	recordAt := int(stack[4])*16 + int(uint16(33*12+uint32(stack[3])+0x36))
	record, _ := hdProtoWords(h.m.Mem, stack[4], uint16(33*12+uint32(stack[3])+0x36), 6)
	sourceAt := int(record[1])*16 + int(record[0])
	mutations := []struct {
		name   string
		change func(*hdPrototype)
	}{
		{"wrong-x", func(n *hdPrototype) { n.m.CPU.R[golem.DX]-- }},
		{"wrong-frame", func(n *hdPrototype) { n.m.CPU.R[golem.AX]++ }},
		{"wrong-y", func(n *hdPrototype) { n.m.Mem[int(c.Seg[golem.SS])*16+int(c.R[golem.SP])+4]++ }},
		{"wrong-canvas", func(n *hdPrototype) { n.m.Mem[int(c.Seg[golem.DS])*16+int(c.R[golem.BX])+6]++ }},
		{"wrong-width", func(n *hdPrototype) { n.m.Mem[recordAt+8]++ }},
		{"wrong-source-pointer", func(n *hdPrototype) { n.m.Mem[recordAt]++ }},
		{"wrong-source-bytes", func(n *hdPrototype) { n.m.Mem[sourceAt] ^= 1 }},
		{"wrong-entry-code", func(n *hdPrototype) { n.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
	}
	var names []string
	for _, test := range mutations {
		n := hdProtoClone(h)
		n.active = false
		test.change(n)
		n.beforeInstruction()
		if n.active || n.accepted != h.accepted {
			t.Fatal("未拒絕入口反例", test.name)
		}
		names = append(names, test.name)
	}
	n := hdProtoClone(baseline)
	n.m.Steps += 100001
	n.m.CPU.IP++
	n.beforeInstruction()
	if n.active || n.rejected != baseline.rejected+1 {
		t.Fatal("未拒絕逾時繪製")
	}
	return append(names, "missing-return-timeout")
}
func hdProtoCheckOwnershipRejections(t *testing.T, h *hdPrototype, f draftNativeFrame) []string {
	t.Helper()
	frame := func(n *hdPrototype) draftNativeFrame {
		g := f
		g.canvas = n.m.Mem[hdProtoCanvas : hdProtoCanvas+64000]
		g.indexed = append([]byte(nil), f.indexed...)
		g.indexed[hdProtoCanvasIndex(0)] = g.canvas[hdProtoCanvasIndex(0)]
		return g
	}
	pixel := 0
	addr := hdProtoCanvas + uint32(hdProtoCanvasIndex(pixel))
	var names []string
	for _, same := range []bool{true, false} {
		n := hdProtoClone(h)
		old := n.m.Mem[addr]
		value := old
		name := "unknown-same-value-write"
		if !same {
			value ^= 1
			name = "unknown-changed-write"
		}
		n.m.Mem[addr] = value
		n.write(addr, old, value)
		_, r := n.base(frame(n))
		if n.owned[pixel] || r["painted"] != 620 {
			t.Fatal("未撤除未知寫入", name, r)
		}
		names = append(names, name)
	}
	n := hdProtoClone(h)
	n.m.Mem[addr] ^= 1
	_, r := n.base(frame(n))
	if r["painted"] != 620 {
		t.Fatal("使用過期底圖", r)
	}
	names = append(names, "stale-native-pixel")
	n = hdProtoClone(h)
	n.pending[1] = hdProtoPixel{owned: true}
	n.write(addr, n.m.Mem[addr], n.m.Mem[addr])
	if len(n.pending) != 0 {
		t.Fatal("未知寫入未清除未完成游標配對")
	}
	names = append(names, "interleaved-incomplete-cursor-pair")
	for _, test := range []struct {
		name string
		at   int
	}{
		{"unknown-cursor-source", 0x1cd74},
		{"incomplete-cursor-buffer", 0xafb00},
	} {
		n = hdProtoClone(h)
		n.m.Mem[test.at] ^= 1
		_, r = n.base(frame(n))
		if r["painted"] != 0 || r["reason"] != "unverified-cursor-or-native-surface" {
			t.Fatal("未知游標沒有回退", test.name, r)
		}
		names = append(names, test.name)
	}
	for _, test := range []struct {
		name   string
		change func(*hdPrototype)
	}{
		{"duplicate-draw-write", func(n *hdPrototype) {
			for k := range n.counts {
				n.counts[k]++
				break
			}
		}},
		{"outside-draw-write", func(n *hdPrototype) { n.outside = true }},
		{"wrong-draw-pixels", func(n *hdPrototype) {
			for k := range n.writes {
				n.writes[k] ^= 1
				break
			}
		}},
	} {
		n = hdProtoClone(h)
		n.owned = [621]bool{}
		test.change(n)
		n.finish()
		if n.accepted != h.accepted || n.rejected != h.rejected+1 {
			t.Fatal("未拒絕繪製反例", test.name)
		}
		for _, v := range n.owned {
			if v {
				t.Fatal("拒絕後仍建立覆蓋", test.name)
			}
		}
		names = append(names, test.name)
	}
	return names
}
