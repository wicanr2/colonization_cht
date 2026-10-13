package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func hdShelterClone(p *hdShelterRuntime) *hdShelterRuntime {
	m := golem.New()
	copy(m.Mem, p.h.m.Mem)
	m.Steps = p.h.m.Steps
	m.CPU.R, m.CPU.Seg, m.CPU.IP, m.CPU.Flags = p.h.m.CPU.R, p.h.m.CPU.Seg, p.h.m.CPU.IP, p.h.m.CPU.Flags
	h := *p.h
	h.m = m
	n := *p
	n.h = &h
	h.shelter = &n
	n.trace = false
	n.pending = map[int]hdShelterPending{}
	for k, v := range p.pending {
		n.pending[k] = v
	}
	return &n
}

// 只修改真實原版入口的隔離副本；正向狀態由正常重播取得。
func hdShelterEntryNegatives(t *testing.T, p *hdShelterRuntime) []string {
	t.Helper()
	positive := hdShelterClone(p)
	positive.active = false
	positive.beforeInstruction()
	if !positive.active {
		t.Fatal("原版木棚入口未被接受")
	}
	c := p.h.m.CPU
	stack := int(c.Seg[golem.SS])*16 + int(c.R[golem.SP])
	record, ok := hdBuildingWords(p.h.m.Mem, 0x4f22, 0xa826, 6)
	if !ok {
		t.Fatal("原版木棚記錄缺失")
	}
	source := int(record[1])*16 + int(record[0])
	tests := []struct {
		name   string
		change func(*hdShelterRuntime)
	}{
		{"wrong-frame", func(n *hdShelterRuntime) { n.h.m.CPU.R[golem.AX]++ }},
		{"high-frame-bit", func(n *hdShelterRuntime) { n.h.m.CPU.R[golem.AX] |= 0x8000 }},
		{"negative-x", func(n *hdShelterRuntime) { n.h.m.CPU.R[golem.DX] = 65535 }},
		{"clipped-right", func(n *hdShelterRuntime) { n.h.m.CPU.R[golem.DX] = 315 }},
		{"negative-y", func(n *hdShelterRuntime) { n.h.m.Mem[stack+4] = 255; n.h.m.Mem[stack+5] = 255 }},
		{"clipped-bottom", func(n *hdShelterRuntime) { n.h.m.Mem[stack+4] = 185; n.h.m.Mem[stack+5] = 0 }},
		{"wrong-destination", func(n *hdShelterRuntime) { n.h.m.Mem[int(c.Seg[golem.DS])*16+int(c.R[golem.BX])+6]++ }},
		{"wrong-width", func(n *hdShelterRuntime) { n.h.m.Mem[0x4f220+0xa826+8]++ }},
		{"wrong-source-bytes", func(n *hdShelterRuntime) { n.h.m.Mem[source] ^= 1 }},
		{"wrong-entry-code", func(n *hdShelterRuntime) { n.h.m.Mem[int(c.Seg[golem.CS])*16+int(c.IP)] ^= 1 }},
	}
	var names []string
	for _, tc := range tests {
		n := hdShelterClone(p)
		n.active = false
		tc.change(n)
		n.beforeInstruction()
		if n.active || n.accepted != p.accepted {
			t.Fatal("木棚未拒絕入口反例", tc.name)
		}
		names = append(names, tc.name)
	}
	return names
}
func hdShelterOwnershipNegatives(t *testing.T, p *hdShelterRuntime, f draftNativeFrame) []string {
	t.Helper()
	pixel := -1
	for i, c := range p.visible {
		if c.owned && f.canvas[i] == c.native && hdShelterHasInk(p, c) {
			pixel = i
			break
		}
	}
	if pixel < 0 {
		t.Fatal("缺少真實木棚來源")
	}
	paint := func(n *hdShelterRuntime) int {
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		return n.paint(image.NewRGBA(image.Rect(0, 0, 1280, 800)), g)["painted"].(int)
	}
	baseline := paint(hdShelterClone(p))
	addr := hdBuildingCanvas + uint32(pixel)
	var names []string
	for _, same := range []bool{true, false} {
		n := hdShelterClone(p)
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
			t.Fatal("木棚覆寫未回退", name)
		}
		names = append(names, name)
	}
	n := hdShelterClone(p)
	n.h.m.Mem[addr] ^= 1
	if paint(n) != baseline-1 {
		t.Fatal("過期木棚仍繪製")
	}
	names = append(names, "stale-native-pixel")
	n = hdShelterClone(p)
	n.pending[pixel] = hdShelterPending{cell: n.visible[pixel]}
	n.write(addr, n.h.m.Mem[addr], n.h.m.Mem[addr])
	if len(n.pending) != 0 {
		t.Fatal("未知寫入未清除游標配對")
	}
	names = append(names, "interleaved-cursor-pair")
	for _, tc := range []struct {
		name string
		at   int
	}{{"unknown-cursor-source", 0x1cd74}, {"incomplete-cursor-buffer", 0xafb00}} {
		n = hdShelterClone(p)
		n.h.m.Mem[tc.at] ^= 1
		g := f
		g.canvas = n.h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
		_, record := n.h.base(g)
		if record["reason"] != "unverified-cursor-or-native-surface" || record["shelter"] != nil {
			t.Fatal("未知游標仍繪木棚", tc.name)
		}
		names = append(names, tc.name)
	}
	raw, err := os.ReadFile(filepath.Join(os.Getenv("TEST_HD_ASSETS"), "building-024.png"))
	if err != nil {
		t.Fatal(err)
	}
	raw[len(raw)-1] ^= 1
	bad := filepath.Join(t.TempDir(), "building-024.png")
	if err := os.WriteFile(bad, raw, 0644); err != nil {
		t.Fatal(err)
	}
	before := hash(p.h.m.Mem)
	loaded, err := loadHDShelterRuntime(p.h, os.Getenv("TEST_GAME_ROOT"), filepath.Dir(bad))
	if err == nil || loaded != nil || hash(p.h.m.Mem) != before {
		t.Fatal("錯誤木棚素材未停用或改寫原版")
	}
	names = append(names, "wrong-art-sha256")
	for _, duplicate := range []bool{false, true} {
		n := hdShelterClone(p)
		local := -1
		for k, count := range n.counts {
			if count == 1 {
				local = k
				break
			}
		}
		if local < 0 {
			t.Fatal("缺少真實木棚完整寫入")
		}
		name := "missing-source-write"
		n.counts[local] = 0
		if duplicate {
			name = "duplicate-source-write"
			n.counts[local] = 2
		}
		n.finish()
		if n.accepted != p.accepted || n.rejected != p.rejected+1 {
			t.Fatal("不完整木棚繪製仍建立來源", name)
		}
		names = append(names, name)
	}
	return names
}

// 在真實0D46:01D2入口的副本執行同一MOV，只改其後尚未執行的指紋位元組。
func hdShelterWriterNegative(t *testing.T, p *hdShelterRuntime) string {
	t.Helper()
	for _, bad := range []bool{false, true} {
		n := hdShelterClone(p)
		if bad {
			n.h.m.Mem[0xd460+0x1d2+15] ^= 1
		}
		n.h.m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, old, value byte) { n.write(a, old, value) })
		// 新Machine沒有原版計時器狀態；此處只驗已取到的MOV，直接走CPU單步。
		if err := n.h.m.CPU.Step(); err != nil {
			t.Fatal(err)
		}
		writes := 0
		for _, count := range n.counts {
			writes += int(count)
		}
		if !bad && (n.outside || writes != 1) {
			t.Fatal("真實木棚MOV未接受", n.outside, writes, n.h.m.CPU.R, n.h.m.CPU.Seg, n.h.m.CPU.IP)
		}
		if bad && (!n.outside || writes != 0) {
			t.Fatal("錯誤原始寫入碼未拒絕")
		}
	}
	return "wrong-writer-code"
}

func TestHDShelterRuntimeNativeLifecycle(t *testing.T) {
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
	if h.shelter == nil || h.shelter.art.Bounds() != image.Rect(0, 0, 92, 108) || hash(m.Mem) != before {
		t.Fatal("木棚原圖載入失敗或改寫原版")
	}
	var negatives []string
	entryChecked, ownershipChecked, writerChecked := false, false, false
	m.SetBeforeInstruction(func() {
		h.beforeInstruction()
		if !entryChecked && h.shelter.active {
			negatives = append(negatives, hdShelterEntryNegatives(t, h.shelter)...)
			entryChecked = true
		}
		if !writerChecked && h.shelter.active && m.CPU.Seg[golem.CS] == 0xd46 && m.CPU.IP == 0x1d2 {
			negatives = append(negatives, hdShelterWriterNegative(t, h.shelter))
			writerChecked = true
		}
	})
	at, count := 0, uint64(0)
	var records []map[string]any
	expected := load(filepath.Join(os.Getenv("TEST_HD_SHELTER_EVIDENCE"), "source-check-r2.json"))
	var sourceProof struct {
		Checkpoints []struct {
			ByOrdinal map[string]int `json:"by_ordinal"`
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
			t.Fatal("木棚HD改變原版完整狀態", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), step: m.Steps, mode: m.VideoMode()}
		ram, regs, segs, ip, flags, cycles := hash(m.Mem), c.R, c.Seg, c.IP, c.Flags, c.Cycles
		output, record := h.base(f)
		h.restoreCursor(output, f)
		shelter := h.shelter.receipt(f)
		if shelter["owned"] != sourceProof.Checkpoints[at].ByOrdinal["24"] || shelter["valid"] != sourceProof.Checkpoints[at].ByOrdinal["24"] {
			t.Fatal("木棚逐點來源與獨立觀測不同", at, shelter)
		}
		var oracle map[string]map[string]struct {
			Call   int
			Local  int
			Native byte
		}
		need(json.Unmarshal(load(filepath.Join(os.Getenv("TEST_HD_SHELTER_EVIDENCE"), "lifecycle-r1/observed", fmt.Sprintf("point-%03d.owners.json", at))), &oracle))
		for pos, cell := range h.shelter.visible {
			if !cell.owned {
				continue
			}
			expected, ok := oracle["main"][fmt.Sprint(pos)]
			if !ok || expected.Local != int(cell.local) || expected.Native != cell.native {
				t.Fatal("木棚局部位移或原版色號不同", at, pos, cell)
			}
		}
		if shelter["owned"].(int) > 0 {
			if !ownershipChecked {
				negatives = append(negatives, hdShelterOwnershipNegatives(t, h.shelter, f)...)
				ownershipChecked = true
			}
			actual, ok := record["shelter"].(map[string]any)
			if !ok || actual["painted"].(int) <= 0 {
				t.Fatal("正常木棚來源沒有HD合成", at, record)
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
		records = append(records, map[string]any{"point": at, "step": m.Steps, "shelter": shelter, "hd": record, "original_state_equal": true})
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
	if at != 49 || count != 53 || h.shelter.accepted != 10 || h.shelter.rejected != 0 || !entryChecked || !ownershipChecked || !writerChecked || len(negatives) != 20 {
		t.Fatal("木棚正常來源或終點不同", at, count, h.shelter.accepted, h.shelter.rejected)
	}
	for _, name := range []string{"COLONY00.SAV", "COLONY09.SAV"} {
		if !bytes.Equal(load(filepath.Join(scratch, name)), load(filepath.Join(receipts, "lifecycle-r29-r1/gui/save", name))) {
			t.Fatal("木棚HD改變原版存檔", name)
		}
	}
	output := os.Getenv("TEST_HD_SHELTER_OUTPUT")
	if output == "" {
		t.Fatal("缺少木棚HD收據輸出")
	}
	need(os.Mkdir(output, 0755))
	data, err := json.MarshalIndent(map[string]any{"result": "PASS_HD_SHELTER_RUNTIME_49_NATIVE_POINTS", "production_connected": true, "points": records, "dos_inputs": count, "end": m.Steps, "accepted": h.shelter.accepted, "rejected": h.shelter.rejected, "asset_sha256": hdShelterArtSHA, "negative_cases": negatives}, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(output, "check.json"), append(data, '\n'), 0644))
}

func hdShelterHasInk(p *hdShelterRuntime, c hdShelterCell) bool {
	for dy := 0; dy < 4; dy++ {
		for dx := 0; dx < 4; dx++ {
			_, _, _, a := p.art.At(int(c.local)%23*4+dx, int(c.local)/23*4+dy).RGBA()
			if a != 0 {
				return true
			}
		}
	}
	return false
}
