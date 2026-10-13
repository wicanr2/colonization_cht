// 規格064 DRAFT：十種城內建築的唯讀正常路徑探針。
// 不由正式組裝器引用，不安裝HD，不修改原版資料或遊戲狀態。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"os"
	"path/filepath"
	"sort"
)

const buildingMain = uint32(0x2cae0)
const buildingStage = uint32(0x3c500)

type buildingSource struct {
	Ordinal, Width, Height, Opaque, Length int
	Encoded, Pixels                        string
	Raw                                    []byte
}

var buildingSources = []buildingSource{
	{16, 73, 18, 504, 713, "37e3c67aad3611c0d6098cd3804fa17a6a33d8b0bf66e6df3e038089388a4568", "5c1b7e4199eb8f106ea596d2aa3f67a73ee2b6a7a6c5f3536f447195a65dc975", nil},
	{21, 23, 27, 446, 531, "d50481bdb7cfbb742035730387bb72601750c1cce584a47b9099034b410e38c8", "6c69fa0082ef58180a1489ef234d76c6b6f6af48a0a02e6013e06b095eb8d6bb", nil},
	{24, 23, 27, 263, 383, "91a6a162404b43e2c17d13bd1ffe5818286e27763ffab2a776f24bc1fbf70c03", "c22c2d5aa17d28373e7588832295924ccafeb15c93576bee89312baf00c28898", nil},
	{27, 23, 27, 465, 570, "51dd0b1f21b29b0e7ee6f7e07d93e5418ed3368a11eaedffc81aa69b954e7d31", "8541b157d3e5e3e8ec4c8b84c274764eee1c27587b1f2ac7de3cce17c48d2b56", nil},
	{35, 44, 22, 507, 752, "8d75b678630f769528a01f79c897dcc33f982353c93674997fc02fc9df32c198", "10510afec834aca13437d2ed8575e4d99b7d10bbe47b8f62a164a241321cc671", nil},
	{39, 23, 27, 459, 541, "29dafe80be32105e570abf822fea90b1ce73bcc206523aa758346b24066c8936", "988755043f1431b5a51248ddaa34fad39f8977de9e4e4d813125dd6d5d485e06", nil},
	{42, 53, 37, 848, 1176, "349af0f0328751db570320e0964f65a50fc6c7b393b991cd61e886a429536582", "2950cb32342d763fc7e3d7d5826b6cc8d8e01a244146610bbfa0280cf96e396f", nil},
	{43, 44, 22, 369, 546, "31756e82c00bdbbd5dee53414b08061e47bf102e87cc3d70beef9be0dd5116aa", "c319dd0fcaae464e995f8a38db41a991404ee09d8e5440c1029249f40422cfae", nil},
	{44, 23, 27, 262, 462, "f9bb3cc9064ce58f05443b8671a870d69fde96667e9a3dde1c24763b1c368332", "b66a25f13e36cad8ee721a2d482db887b58abecd7ca14b9a283a95cac706b4f3", nil},
	{45, 75, 48, 1069, 1591, "129934aa9808419a2164569da49363b9a8c8486a0460fd9da876cb641b797de1", "8b4ead6d9cabcad609b53a8bb995ce8a5a94d16319d788c7cac5e5deb9989c45", nil},
}

func buildingNeed(err error) {
	if err != nil {
		panic(err)
	}
}
func buildingRead(p string) []byte { b, e := os.ReadFile(p); buildingNeed(e); return b }
func buildingHash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func buildingJSON(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	buildingNeed(e)
	buildingNeed(os.WriteFile(p, append(b, '\n'), 0644))
}
func buildingWords(b []byte) []uint16 {
	r := make([]uint16, len(b)/2)
	for i := range r {
		r[i] = binary.LittleEndian.Uint16(b[i*2:])
	}
	return r
}

type buildingInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int    `json:"button"`
	Text   string `json:"text"`
}
type buildingPoint struct {
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

type buildingCall struct {
	Ordinal         int               `json:"ordinal"`
	ReturnRegisters [8]uint16         `json:"return_registers"`
	ReturnSegments  [4]uint16         `json:"return_segments"`
	ReturnIP        uint16            `json:"return_ip"`
	EntryCode       string            `json:"entry_code12"`
	Entry           uint64            `json:"entry_step"`
	Return          uint64            `json:"return_step"`
	Registers       [8]uint16         `json:"registers"`
	Segments        [4]uint16         `json:"segments"`
	Stack           []uint16          `json:"ss_sp_words"`
	Descriptor      []uint16          `json:"ds_bx_words"`
	RecordFar       string            `json:"record_far"`
	Record          []uint16          `json:"record_words"`
	SourceFar       string            `json:"source_far"`
	SourceSHA       string            `json:"source_encoded_sha256"`
	ReturnSite      string            `json:"return_cs_ip"`
	Canvas          uint32            `json:"canvas_linear"`
	Rect            [4]int            `json:"rect"`
	Selected        bool              `json:"selected"`
	Writes          int               `json:"unique_writes"`
	WriteCount      uint64            `json:"write_count"`
	WriteSHA        string            `json:"sorted_local_offset_value_sha256"`
	WriterSites     map[string]uint64 `json:"writer_sites"`
	WriterCode      map[string]string `json:"writer_code16"`
	Before          []byte            `json:"private_before_roi"`
	After           []byte            `json:"private_after_roi"`
	TransparentSame bool              `json:"transparent_background_unchanged"`
	OutsideSame     bool              `json:"outside_rectangle_unchanged"`
	Mismatch        string            `json:"geometry_or_write_mismatch,omitempty"`
}
type buildingCell struct {
	Call   int  `json:"call"`
	Local  int  `json:"local"`
	Native byte `json:"native"`
}
type buildingObserver struct {
	tracked           [2][64000]bool
	events            []map[string]any
	m                 *golem.Machine
	source            *buildingSource
	calls             []*buildingCall
	active            *buildingCall
	sp, retCS, retIP  uint16
	before            []byte
	writes            map[uint32][3]uint64
	owners            [2][64000]buildingCell
	losses            map[string]uint64
	same, transferred uint64
	copySites         map[string]uint64
	copySamples       []map[string]any
}

func (b *buildingObserver) read(seg, off uint16, n int) []byte {
	at := uint32(seg)*16 + uint32(off)
	if uint64(at)+uint64(n) > uint64(len(b.m.Mem)) {
		panic("唯讀研究讀取越界")
	}
	return b.m.Mem[at : at+uint32(n)]
}
func (b *buildingObserver) roi(base uint32, r [4]int) []byte {
	var data []byte
	for y := r[1]; y < r[3]; y++ {
		data = append(data, b.m.Mem[base+uint32(y*320+r[0]):base+uint32(y*320+r[2])]...)
	}
	return data
}
func buildingSurface(addr uint32) (int, int, bool) {
	for n, base := range []uint32{buildingMain, buildingStage} {
		if addr >= base && addr < base+64000 {
			return n, int(addr - base), true
		}
	}
	return 0, 0, false
}
func (b *buildingObserver) finish() {
	c := b.active
	c.Return = b.m.Steps
	c.ReturnRegisters, c.ReturnSegments, c.ReturnIP = b.m.CPU.R, b.m.CPU.Seg, b.m.CPU.IP
	c.After = b.roi(c.Canvas, c.Rect)
	c.Writes = len(b.writes)
	c.TransparentSame = true
	c.OutsideSame = true
	var offsets []int
	for addr, v := range b.writes {
		c.WriteCount += v[2]
		i := int(addr - c.Canvas)
		x, y := i%320-c.Rect[0], i/320-c.Rect[1]
		if x < 0 || x >= b.source.Width || y < 0 || y >= b.source.Height || v[2] != 1 {
			c.Mismatch = "寫入超出矩形或重複"
			continue
		}
		k := y*b.source.Width + x
		if b.source.Raw[k] == 253 || byte(v[1]) != b.source.Raw[k] {
			c.Mismatch = "透明處被寫或來源色號不同"
			continue
		}
		offsets = append(offsets, k)
	}
	if c.Writes != b.source.Opaque || c.WriteCount != uint64(b.source.Opaque) {
		c.Mismatch = "不是完整不透明點"
	}
	for k, v := range b.source.Raw {
		if v == 253 {
			if c.Before[k] != c.After[k] {
				c.TransparentSame = false
			}
		} else if c.After[k] != v {
			c.Mismatch = "返回圖像與完整來源不符"
		}
	}
	for i, v := range b.before {
		x, y := i%320, i/320
		if (x < c.Rect[0] || x >= c.Rect[2] || y < c.Rect[1] || y >= c.Rect[3]) && b.m.Mem[c.Canvas+uint32(i)] != v {
			c.OutsideSame = false
		}
	}
	if !c.TransparentSame || !c.OutsideSame {
		c.Mismatch = "底圖或矩形外被改"
	}
	sort.Ints(offsets)
	var data []byte
	for _, k := range offsets {
		data = binary.LittleEndian.AppendUint16(data, uint16(k))
		data = append(data, b.source.Raw[k])
	}
	c.WriteSHA = buildingHash(data)
	if c.Mismatch == "" {
		s, _, ok := buildingSurface(c.Canvas)
		if !ok {
			panic("未知畫布")
		}
		for k, v := range b.source.Raw {
			if v != 253 {
				i := (c.Rect[1]+k/b.source.Width)*320 + c.Rect[0] + k%b.source.Width
				b.owners[s][i] = buildingCell{len(b.calls), k, v}
			}
		}
	}
	if c.Mismatch == "" {
		b.events = append(b.events, map[string]any{"kind": "draw", "step": b.m.Steps, "call": len(b.calls)})
	}
	b.active = nil
}
func (b *buildingObserver) beforeStep() {
	if b == nil || b.m.Steps < 50000000 {
		return
	}
	m := b.m
	if b.active != nil {
		if m.CPU.Seg[golem.CS] == b.retCS && m.CPU.IP == b.retIP && m.CPU.R[golem.SP] == b.sp+10 {
			b.finish()
		} else if m.Steps-b.active.Entry > 100000 {
			panic("建築繪製未在界限內返回")
		}
	}
	if m.CPU.Seg[golem.CS] != 0xd46 || m.CPU.IP != 0xa {
		return
	}
	if b.active != nil || len(b.calls) >= 20000 {
		panic("重入或呼叫數超限")
	}
	if !bytes.Equal(b.read(0xd46, 0xa, 12), []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		panic("入口原始碼不同")
	}
	ss, sp := m.CPU.Seg[golem.SS], m.CPU.R[golem.SP]
	stack := buildingWords(b.read(ss, sp, 10))
	off := uint16((m.CPU.R[golem.AX]&0x7fff)*12 + stack[3] + 0x36)
	record := buildingWords(b.read(stack[4], off, 12))
	// 只把已驗其他素材的欄位讀取當搜尋線索；建築另驗完整來源及實際寫入。
	var source *buildingSource
	for i := range buildingSources {
		candidate := &buildingSources[i]
		if buildingHash(b.read(record[1], record[0], candidate.Length)) == candidate.Encoded {
			source = candidate
			break
		}
	}
	if source == nil {
		return
	}
	b.source = source
	descriptor := buildingWords(b.read(m.CPU.Seg[golem.DS], m.CPU.R[golem.BX], 8))
	x, y := int(int16(m.CPU.R[golem.DX])), int(int16(stack[2]))
	c := &buildingCall{Ordinal: source.Ordinal, Entry: m.Steps, Registers: m.CPU.R, Segments: m.CPU.Seg, Stack: stack, Descriptor: descriptor,
		RecordFar: fmt.Sprintf("%04X:%04X", stack[4], off), Record: record, SourceFar: fmt.Sprintf("%04X:%04X", record[1], record[0]), SourceSHA: source.Encoded,
		ReturnSite: fmt.Sprintf("%04X:%04X", stack[1], stack[0]), Canvas: uint32(descriptor[3])*16 + uint32(descriptor[2]), Rect: [4]int{x, y, x + source.Width, y + source.Height},
		WriterSites: map[string]uint64{}, WriterCode: map[string]string{}}
	b.calls = append(b.calls, c)
	if int(record[4]) != source.Width || int(record[5]) != source.Height || descriptor[0] != 200 || descriptor[1] != 320 || (c.Canvas != buildingMain && c.Canvas != buildingStage) || x < 0 || x+source.Width > 320 || y < 0 || y+source.Height > 200 || m.CPU.R[golem.AX]&0x8000 != 0 {
		c.Mismatch = "來源相同但幾何、畫布或高位未驗"
		return
	}
	c.Selected = true
	c.EntryCode = fmt.Sprintf("%x", b.read(0xd46, 0xa, 12))
	surface, _, _ := buildingSurface(c.Canvas)
	for yy := c.Rect[1]; yy < c.Rect[3]; yy++ {
		for xx := c.Rect[0]; xx < c.Rect[2]; xx++ {
			b.tracked[surface][yy*320+xx] = true
		}
	}
	c.Before = b.roi(c.Canvas, c.Rect)
	b.before = append(b.before[:0], m.Mem[c.Canvas:c.Canvas+64000]...)
	b.active, b.sp, b.retCS, b.retIP = c, sp, stack[1], stack[0]
	b.writes = map[uint32][3]uint64{}
}
func (b *buildingObserver) write(addr uint32, old, value byte) {
	if b.m.Steps < 50000000 {
		return
	}
	s, i, ok := buildingSurface(addr)
	if !ok {
		panic("觀測畫布不同")
	}
	cs, ip := b.m.CPU.OpAddr()
	site := fmt.Sprintf("%04X:%04X", cs, ip)
	if b.owners[s][i].Call != 0 {
		b.losses[site]++
		if old == value {
			b.same++
		}
	}
	b.owners[s][i] = buildingCell{}
	if b.active != nil && addr >= b.active.Canvas && addr < b.active.Canvas+64000 {
		r, exists := b.writes[addr]
		if !exists {
			r[0] = uint64(old)
		}
		r[1], r[2] = uint64(value), r[2]+1
		b.writes[addr] = r
		b.active.WriterSites[site]++
		b.active.WriterCode[site] = fmt.Sprintf("%x", b.read(cs, ip, 16))
	}
	// 新來源尚未驗游標或背景複製。任何後畫含同值均撤銷，不保留轉送身分。
	if b.tracked[s][i] {
		if len(b.events) >= 1000000 {
			panic("建築矩形寫入證據超限")
		}
		b.events = append(b.events, map[string]any{"kind": "write", "step": b.m.Steps, "surface": s, "offset": i, "old": old, "value": value, "site": site, "code16": fmt.Sprintf("%x", b.read(cs, ip, 16)), "after_cell": b.owners[s][i]})
	}
}
func buildingState(m *golem.Machine) map[string]any {
	return map[string]any{"steps": m.Steps, "memory_sha256": buildingHash(m.Mem), "indexed_sha256": buildingHash(m.Indexed()), "palette_sha256": buildingHash(m.DAC[:]), "registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags, "cycles": m.CPU.Cycles}
}
func main() {
	root := flag.String("root", "/game", "唯讀合法原版")
	seed := flag.String("seed", "", "正常產生的COLONY09.SAV")
	inputs := flag.String("inputs", "", "既有正常GUI輸入")
	sources := flag.String("sources", "", "本機固定十種建築索引來源目錄")
	out := flag.String("out", "", "尚不存在的本機研究輸出")
	control := flag.Bool("control", false, "不安裝觀測器的同輸入對照")
	pointsFile := flag.String("lifecycle-points", "", "可選：已固定49點正常GUI原版收據")
	flag.Parse()
	for n, h := range map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
	} {
		p := filepath.Join(*root, n)
		if _, e := os.Stat(p); os.IsNotExist(e) {
			fmt.Fprintln(os.Stderr, "SKIP：缺少合法原版 "+n)
			os.Exit(77)
		}
		if buildingHash(buildingRead(p)) != h {
			panic("原版版本不同：" + n)
		}
	}
	seedBytes, inputBytes := buildingRead(*seed), buildingRead(*inputs)
	for i := range buildingSources {
		source := &buildingSources[i]
		source.Raw = buildingRead(filepath.Join(*sources, fmt.Sprintf("building-%03d.pixels", source.Ordinal)))
		if len(source.Raw) != source.Width*source.Height || buildingHash(source.Raw) != source.Pixels {
			panic("建築完整索引來源不同")
		}
	}
	wantInput := "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979"
	var points []buildingPoint
	if *pointsFile != "" {
		wantInput = "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"
		raw := buildingRead(*pointsFile)
		if buildingHash(raw) != "821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901" {
			panic("49點原版收據不同")
		}
		buildingNeed(json.Unmarshal(raw, &points))
		if len(points) != 49 {
			panic("檢查點數不同")
		}
	}
	if buildingHash(seedBytes) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" || buildingHash(inputBytes) != wantInput {
		panic("正常輸入、存檔或素材不同")
	}
	var replay struct {
		Inputs []buildingInput `json:"inputs"`
		End    uint64          `json:"end"`
	}
	buildingNeed(json.Unmarshal(inputBytes, &replay))
	end := uint64(75900000)
	if *pointsFile != "" {
		end = 134600000
	}
	if replay.End < end {
		panic("正常輸入未達終點")
	}
	buildingNeed(os.Mkdir(*out, 0755))
	scratch := filepath.Join(*out, "saves")
	buildingNeed(os.Mkdir(scratch, 0755))
	buildingNeed(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seedBytes, 0644))
	m := golem.New()
	buildingNeed(m.LoadEXE(buildingRead(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		panic("缺數位音效能力")
	}
	m.EnableOPLSynth(true)
	var observer *buildingObserver
	if !*control {
		observer = &buildingObserver{m: m, losses: map[string]uint64{}, copySites: map[string]uint64{}}
		for _, base := range []uint32{buildingMain, buildingStage} {
			m.WatchWrite(base, base+63999, func(_ *golem.Machine, a uint32, o, v byte) { observer.write(a, o, v) })
		}
	}
	var checkpoints []map[string]any
	count, pointAt := uint64(0), 0
	seenShort := map[uint64]bool{}
	capture := func() {
		name := ""
		if len(points) > 0 {
			if pointAt == len(points) {
				return
			}
			p := points[pointAt]
			if m.Steps > p.Step || (m.Steps == p.Step && count > p.Count) {
				panic("略過GUI檢查點")
			}
			if m.Steps != p.Step || count != p.Count {
				return
			}
			if buildingHash(m.Mem) != p.Memory || buildingHash(m.Indexed()) != p.Indexed || buildingHash(m.DAC[:]) != p.Palette || m.CPU.R != p.Registers || m.CPU.Seg != p.Segments || m.CPU.IP != p.IP || m.CPU.Flags != p.Flags {
				panic("建築觀測與既有完整原版狀態不同")
			}
			name = fmt.Sprintf("point-%03d", pointAt)
			pointAt++
		} else {
			if (m.Steps != 63525000 && m.Steps != end) || seenShort[m.Steps] {
				return
			}
			seenShort[m.Steps] = true
			name = fmt.Sprintf("cp-%d", m.Steps)
		}
		state := buildingState(m)
		state["dos_input_count"] = count
		state["snapshot_prefix"] = name
		if observer != nil {
			state["event_count"] = len(observer.events)
		}
		checkpoints = append(checkpoints, state)
		for suffix, data := range map[string][]byte{".idx": m.Indexed(), ".canvas": m.Mem[buildingMain : buildingMain+64000], ".stage": m.Mem[buildingStage : buildingStage+64000], ".palette": m.DAC[:]} {
			buildingNeed(os.WriteFile(filepath.Join(*out, name+suffix), data, 0644))
		}
		if observer != nil {
			owners := map[string]map[int]buildingCell{"main": {}, "stage": {}}
			for surface, key := range []string{"main", "stage"} {
				for i, c := range observer.owners[surface] {
					if c.Call != 0 {
						owners[key][i] = c
					}
				}
			}
			buildingJSON(filepath.Join(*out, name+".owners.json"), owners)
		}
	}
	step := func() { observer.beforeStep(); capture(); buildingNeed(m.Step()) }
	previous := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step < previous {
			panic("輸入步數倒退")
		}
		previous = e.Step
		if e.Step > end {
			break
		}
		for m.Steps < e.Step {
			step()
		}
		capture()
		switch e.Kind {
		case "move":
			if e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200 {
				panic("座標越界")
			}
			d.MoveMouse(e.X, e.Y)
		case "press", "release":
			if e.Button < 0 || e.Button > 2 {
				panic("按鈕越界")
			}
			if e.Kind == "press" {
				d.PressMouse(e.Button)
			} else {
				d.ReleaseMouse(e.Button)
			}
		case "enter", "escape", "backspace":
			name := map[string]string{"enter": "Return", "escape": "Escape", "backspace": "Backspace"}[e.Kind]
			if !d.PushKeyNamed(name) {
				panic("缺少已驗鍵盤映射：" + name)
			}
		case "text":
			if !d.PushText(e.Text) {
				panic("原版拒絕文字輸入")
			}
		default:
			panic("未支援輸入：" + e.Kind)
		}
		count++
		capture()
	}
	for m.Steps < end {
		step()
	}
	observer.beforeStep()
	capture()
	if len(points) > 0 && pointAt != len(points) {
		panic("未完成49點正常路徑")
	}
	buildingNeed(os.WriteFile(filepath.Join(*out, "final.memory"), m.Mem, 0644))
	result := map[string]any{"kind": "readonly-colony-building-batch-normal-input-research", "control": *control, "input_sha256": buildingHash(inputBytes), "seed_sha256": buildingHash(seedBytes), "checkpoints": checkpoints, "end": buildingState(m), "dos_inputs": count, "address_space": "dosgolem real-mode CS:IP and 20-bit linear RAM; not IDA EA", "limitations": "Ten exact decoded sources; no production HD, animation, cursor or RAM restoration claim."}
	if observer != nil {
		if observer.active != nil {
			panic("終點仍在繪製")
		}
		buildingJSON(filepath.Join(*out, "writes.json"), observer.events)
		result["calls"] = observer.calls
		result["source_matches"] = len(observer.calls)
		result["ownership_loss_sites"] = observer.losses
		result["same_value_ownership_losses"] = observer.same
		result["verified_transferred_pixels"] = observer.transferred
		result["copy_sites"] = observer.copySites
		result["copy_samples"] = observer.copySamples
	}
	buildingJSON(filepath.Join(*out, "draws.json"), result)
	fmt.Printf("steps=%d memory=%s control=%v\n", m.Steps, buildingHash(m.Mem), *control)
}
