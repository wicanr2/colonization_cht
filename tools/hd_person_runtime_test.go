package main

import (
	"bytes"
	"encoding/json"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func hdPersonClone(p *hdPersonRuntime) *hdPersonRuntime {
	m := golem.New()
	copy(m.Mem, p.h.m.Mem)
	m.Steps = p.h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = p.h.m.CPU.R, p.h.m.CPU.Seg, p.h.m.CPU.IP, p.h.m.CPU.Flags
	h := *p.h
	h.m = m
	n := *p
	n.h = &h
	h.person = &n
	n.trace = false
	n.pending = map[int]hdPersonPending{}
	for k, v := range p.pending {
		n.pending[k] = v
	}
	return &n
}

// 只修改真實原版入口的隔離副本；正向狀態由正常重播取得。
func hdPersonEntryNegatives(t *testing.T, p *hdPersonRuntime) []string {
	t.Helper()
	positive := hdPersonClone(p)
	positive.active = false
	positive.beforeInstruction()
	if !positive.active {
		t.Fatal("原版人物入口未被接受")
	}
	c := p.h.m.CPU
	stack := int(c.Seg[golem.SS])*16 + int(c.R[golem.SP])
	record, ok := hdBuildingWords(p.h.m.Mem, 0x4f22, 0x6825, 6)
	if !ok {
		t.Fatal("原版人物記錄缺失")
	}
	source := int(record[1])*16 + int(record[0])
	tests := []struct {
		name   string
		change func(*hdPersonRuntime)
	}{
		{"wrong-frame", func(n *hdPersonRuntime) { n.h.m.CPU.R[golem.AX]++ }},
		{"high-frame-bit", func(n *hdPersonRuntime) { n.h.m.CPU.R[golem.AX] |= 0x8000 }},
		{"negative-x", func(n *hdPersonRuntime) { n.h.m.CPU.R[golem.DX] = 65535 }},
		{"clipped-right", func(n *hdPersonRuntime) { n.h.m.CPU.R[golem.DX] = 315 }},
		{"negative-y", func(n *hdPersonRuntime) { n.h.m.Mem[stack+4] = 255; n.h.m.Mem[stack+5] = 255 }},
		{"clipped-bottom", func(n *hdPersonRuntime) { n.h.m.Mem[stack+4] = 185; n.h.m.Mem[stack+5] = 0 }},
		{"wrong-destination", func(n *hdPersonRuntime) { n.h.m.Mem[int(c.Seg[golem.DS])*16+int(c.R[golem.BX])+6]++ }},
		{"wrong-width", func(n *hdPersonRuntime) { n.h.m.Mem[0x4f220+0x6825+8]++ }},
		{"wrong-source-bytes", func(n *hdPersonRuntime) { n.h.m.Mem[source] ^= 1 }},
		{"wrong-entry-code", func(n *hdPersonRuntime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
	}
	var names []string
	for _, tc := range tests {
		n := hdPersonClone(p)
		n.active = false
		tc.change(n)
		n.beforeInstruction()
		if n.active || n.accepted != p.accepted {
			t.Fatal("人物未拒絕入口反例", tc.name)
		}
		names = append(names, tc.name)
	}
	return names
}
func hdPersonOwnershipNegatives(t *testing.T, p *hdPersonRuntime, f draftNativeFrame) []string {
	t.Helper()
	pixel := -1
	for i, c := range p.visible {
		if c.owned && f.canvas[i] == c.native {
			pixel = i
			break
		}
	}
	if pixel < 0 {
		t.Fatal("缺少真實人物來源")
	}
	paint := func(n *hdPersonRuntime) int {
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		return n.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), g)["painted"].(int)
	}
	baseline := paint(hdPersonClone(p))
	addr := hdBuildingCanvas + uint32(pixel)
	var names []string
	for _, same := range []bool{true, false} {
		n := hdPersonClone(p)
		old := n.h.m.Mem[addr]
		v := old
		name := "unknown-same-write"
		if !same {
			v ^= 1
			name = "unknown-changed-write"
		}
		n.h.m.Mem[addr] = v
		n.write(addr, old, v)
		if n.visible[pixel].owned || paint(n) != baseline-1 {
			t.Fatal("人物覆寫未回退", name)
		}
		names = append(names, name)
	}
	n := hdPersonClone(p)
	n.h.m.Mem[addr] ^= 1
	if paint(n) != baseline-1 {
		t.Fatal("過期人物仍繪製")
	}
	names = append(names, "stale-native-pixel")
	n = hdPersonClone(p)
	n.pending[pixel] = hdPersonPending{cell: n.visible[pixel]}
	n.write(addr, n.h.m.Mem[addr], n.h.m.Mem[addr])
	if len(n.pending) != 0 {
		t.Fatal("未知寫入未清除游標配對")
	}
	names = append(names, "interleaved-cursor-pair")
	for _, tc := range []struct {
		name string
		at   int
	}{{"unknown-cursor-source", 0x1cd74}, {"incomplete-cursor-buffer", 0xafb00}} {
		n = hdPersonClone(p)
		n.h.m.Mem[tc.at] ^= 1
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		_, record := n.h.base(g)
		if record["reason"] != "unverified-cursor-or-native-surface" || record["person"] != nil {
			t.Fatal("未知游標仍繪人物", tc.name)
		}
		names = append(names, tc.name)
	}
	raw, err := os.ReadFile(filepath.Join(os.Getenv("TEST_HD_ASSETS"), "person-100.png"))
	if err != nil {
		t.Fatal(err)
	}
	raw[len(raw)-1] ^= 1
	bad := filepath.Join(t.TempDir(), "person-100.png")
	if err := os.WriteFile(bad, raw, 0644); err != nil {
		t.Fatal(err)
	}
	before := hash(p.h.m.Mem)
	loaded, err := loadHDPersonRuntime(p.h, os.Getenv("TEST_GAME_ROOT"), filepath.Dir(bad))
	if err == nil || loaded != nil || hash(p.h.m.Mem) != before {
		t.Fatal("錯誤人物素材未停用或改寫原版")
	}
	return append(names, "wrong-art-sha256")
}

func TestHDPersonRuntimeNativeLifecycle(t *testing.T) {
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
		t.Fatal("正常路徑或原版收據不同")
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
		t.Fatal("初始存檔不同")
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
		t.Fatal("缺少數位音效能力")
	}
	m.EnableOPLSynth(true)
	before := hash(m.Mem)
	h, err := loadHDRuntime(m, game, assets)
	need(err)
	if h.person == nil || h.person.art.Bounds() != image.Rect(0, 0, 24, 64) || hash(m.Mem) != before {
		t.Fatal("人物原圖載入失敗或改寫原版")
	}
	var negatives []string
	entryChecked, ownershipChecked := false, false
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		if !entryChecked && h.person.active {
			negatives = append(negatives, hdPersonEntryNegatives(t, h.person)...)
			entryChecked = true
		}
	})
	at, count := 0, uint64(0)
	var records []map[string]any
	expected := load(filepath.Join(os.Getenv("TEST_HD_PERSON_EVIDENCE"), "person-check-r3.json"))
	var sourceProof struct {
		Checkpoints []struct {
			Owned int `json:"main_owned"`
		} `json:"checkpoints"`
	}
	need(json.Unmarshal(expected, &sourceProof))
	if len(sourceProof.Checkpoints) != 49 {
		t.Fatal("獨立來源證明規模不同")
	}
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
			t.Fatal("人物原型改變原版完整狀態", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), step: m.Steps, mode: m.VideoMode()}
		ram, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		output, record := h.base(f)
		h.restoreCursor(output, f)
		person := h.person.receipt(f)
		if person["owned"] != sourceProof.Checkpoints[at].Owned || person["valid"] != sourceProof.Checkpoints[at].Owned {
			t.Fatal("人物逐點來源與獨立觀測不同", at, person)
		}
		if person["owned"].(int) > 0 {
			if !ownershipChecked {
				negatives = append(negatives, hdPersonOwnershipNegatives(t, h.person, f)...)
				ownershipChecked = true
			}
			actual, ok := record["person"].(map[string]any)
			if !ok || actual["painted"].(int) <= 0 {
				t.Fatal("正常人物來源沒有HD合成", at, record)
			}
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
		for i, v := range h.small.visible {
			if v.owned && v.native == f.canvas[i] && h.small.frames[v.slot].art != nil {
				allowed[i] = true
			}
		}
		native := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if !allowed[(y/4)*320+x/4] && output.RGBAAt(x, y) != native.RGBAAt(x, y) {
					t.Fatal("HD越出已驗來源", at, x, y)
				}
			}
		}
		if hash(m.Mem) != ram || c.R != regs || c.Seg != segs || c.IP != ip || c.Flags != flags || c.Cycles != cycles {
			t.Fatal("合成改寫原版", at)
		}
		records = append(records, map[string]any{"point": at, "step": m.Steps, "person": person, "hd": record, "original_state_equal": true})
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
	if at != 49 || count != 53 || h.person.accepted != 13 || h.person.rejected != 0 || !entryChecked || !ownershipChecked || len(negatives) != 17 {
		t.Fatal("人物正常來源或終點不同", at, count, h.person.accepted, h.person.rejected)
	}
	for _, name := range []string{"COLONY00.SAV", "COLONY09.SAV"} {
		if !bytes.Equal(load(filepath.Join(scratch, name)), load(filepath.Join(receipts, "lifecycle-r29-r1/gui/save", name))) {
			t.Fatal("人物HD改變原版存檔", name)
		}
	}
	output := os.Getenv("TEST_HD_PERSON_OUTPUT")
	if output == "" {
		t.Fatal("缺少人物原型收據輸出")
	}
	need(os.Mkdir(output, 0755))
	data, err := json.MarshalIndent(map[string]any{"result": "PASS_HD_PERSON_RUNTIME_49_NATIVE_POINTS", "production_connected": true, "points": records, "dos_inputs": count, "end": m.Steps, "accepted": h.person.accepted, "rejected": h.person.rejected, "asset_sha256": hdPersonArtSHA, "negative_cases": negatives}, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(output, "check.json"), append(data, '\n'), 0644))
}
