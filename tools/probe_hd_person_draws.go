// 規格063 DRAFT：ICONS.SS 第100幀的唯讀正常路徑探針。
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

const personMain = uint32(0x2cae0)
const personStage = uint32(0x3c500)
const personEncodedSHA = "36d3a8e51b4bce57a879d96703d5fad70797f9e940e13aa3abc4d6f830e4d832"
const personPixelsSHA = "d2b48efd38ba4d2a0f3a90f85cf6f4e0b218ce1fcf5d264f3c86b0636f956502"

func personNeed(err error) {
	if err != nil {
		panic(err)
	}
}
func personRead(p string) []byte { b, e := os.ReadFile(p); personNeed(e); return b }
func personHash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func personJSON(p string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	personNeed(e)
	personNeed(os.WriteFile(p, append(b, '\n'), 0644))
}
func personWords(b []byte) []uint16 {
	r := make([]uint16, len(b)/2)
	for i := range r {
		r[i] = binary.LittleEndian.Uint16(b[i*2:])
	}
	return r
}

type personInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int    `json:"button"`
	Text   string `json:"text"`
}
type personPoint struct {
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

type personCall struct {
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
	SourceSHA       string            `json:"source_first_101_sha256"`
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
type personCell struct {
	Call   int  `json:"call"`
	Local  int  `json:"local"`
	Native byte `json:"native"`
}
type personObserver struct {
	tracked           [2][64000]bool
	events            []map[string]any
	m                 *golem.Machine
	pixels            []byte
	calls             []*personCall
	active            *personCall
	sp, retCS, retIP  uint16
	before            []byte
	writes            map[uint32][3]uint64
	owners            [2][64000]personCell
	losses            map[string]uint64
	same, transferred uint64
	copySites         map[string]uint64
	copySamples       []map[string]any
}

func (b *personObserver) read(seg, off uint16, n int) []byte {
	at := uint32(seg)*16 + uint32(off)
	if uint64(at)+uint64(n) > uint64(len(b.m.Mem)) {
		panic("唯讀研究讀取越界")
	}
	return b.m.Mem[at : at+uint32(n)]
}
func (b *personObserver) roi(base uint32, r [4]int) []byte {
	var data []byte
	for y := r[1]; y < r[3]; y++ {
		data = append(data, b.m.Mem[base+uint32(y*320+r[0]):base+uint32(y*320+r[2])]...)
	}
	return data
}
func personSurface(addr uint32) (int, int, bool) {
	for n, base := range []uint32{personMain, personStage} {
		if addr >= base && addr < base+64000 {
			return n, int(addr - base), true
		}
	}
	return 0, 0, false
}
func (b *personObserver) finish() {
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
		if x < 0 || x >= 6 || y < 0 || y >= 16 || v[2] != 1 {
			c.Mismatch = "寫入超出矩形或重複"
			continue
		}
		k := y*6 + x
		if b.pixels[k] == 253 || byte(v[1]) != b.pixels[k] {
			c.Mismatch = "透明處被寫或來源色號不同"
			continue
		}
		offsets = append(offsets, k)
	}
	if c.Writes != 60 || c.WriteCount != 60 {
		c.Mismatch = "不是完整60個不透明點"
	}
	for k, v := range b.pixels {
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
		data = append(data, b.pixels[k])
	}
	c.WriteSHA = personHash(data)
	if c.Mismatch == "" {
		s, _, ok := personSurface(c.Canvas)
		if !ok {
			panic("未知畫布")
		}
		for k, v := range b.pixels {
			if v != 253 {
				i := (c.Rect[1]+k/6)*320 + c.Rect[0] + k%6
				b.owners[s][i] = personCell{len(b.calls), k, v}
			}
		}
	}
	if c.Mismatch == "" {
		b.events = append(b.events, map[string]any{"kind": "draw", "step": b.m.Steps, "call": len(b.calls)})
	}
	b.active = nil
}
func (b *personObserver) beforeStep() {
	if b == nil || b.m.Steps < 50000000 {
		return
	}
	m := b.m
	if b.active != nil {
		if m.CPU.Seg[golem.CS] == b.retCS && m.CPU.IP == b.retIP && m.CPU.R[golem.SP] == b.sp+10 {
			b.finish()
		} else if m.Steps-b.active.Entry > 100000 {
			panic("人物繪製未在界限內返回")
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
	stack := personWords(b.read(ss, sp, 10))
	off := uint16((m.CPU.R[golem.AX]&0x7fff)*12 + stack[3] + 0x36)
	record := personWords(b.read(stack[4], off, 12))
	// 只把已驗其他素材的欄位讀取當搜尋線索；人物另驗完整來源及實際寫入。
	if personHash(b.read(record[1], record[0], 101)) != personEncodedSHA {
		return
	}
	descriptor := personWords(b.read(m.CPU.Seg[golem.DS], m.CPU.R[golem.BX], 8))
	x, y := int(int16(m.CPU.R[golem.DX])), int(int16(stack[2]))
	c := &personCall{Entry: m.Steps, Registers: m.CPU.R, Segments: m.CPU.Seg, Stack: stack, Descriptor: descriptor,
		RecordFar: fmt.Sprintf("%04X:%04X", stack[4], off), Record: record, SourceFar: fmt.Sprintf("%04X:%04X", record[1], record[0]), SourceSHA: personEncodedSHA,
		ReturnSite: fmt.Sprintf("%04X:%04X", stack[1], stack[0]), Canvas: uint32(descriptor[3])*16 + uint32(descriptor[2]), Rect: [4]int{x, y, x + 6, y + 16},
		WriterSites: map[string]uint64{}, WriterCode: map[string]string{}}
	b.calls = append(b.calls, c)
	if record[4] != 6 || record[5] != 16 || descriptor[0] != 200 || descriptor[1] != 320 || (c.Canvas != personMain && c.Canvas != personStage) || x < 0 || x+6 > 320 || y < 0 || y+16 > 200 || m.CPU.R[golem.AX]&0x8000 != 0 {
		c.Mismatch = "來源相同但幾何、畫布或高位未驗"
		return
	}
	c.Selected = true
	c.EntryCode = fmt.Sprintf("%x", b.read(0xd46, 0xa, 12))
	surface, _, _ := personSurface(c.Canvas)
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
func (b *personObserver) write(addr uint32, old, value byte) {
	if b.m.Steps < 50000000 {
		return
	}
	s, i, ok := personSurface(addr)
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
	b.owners[s][i] = personCell{}
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
	// 已驗REP MOVSW仍逐byte核對實際來源，任何其他寫入含同值都撤銷。
	if cs == 0xcba && ip == 0xca && bytes.Equal(b.read(cs, ip, 16), []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0xc, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}) {
		dest := int(b.m.CPU.Seg[golem.ES])*16 + int(b.m.CPU.R[golem.DI])
		delta := int(addr) - dest
		source := int(b.m.CPU.Seg[golem.DS])*16 + int(b.m.CPU.R[golem.SI]) + delta
		if delta >= 0 && delta < 2 && source >= 0 && source < len(b.m.Mem) && b.m.Mem[source] == value {
			ss, si, known := personSurface(uint32(source))
			if known && b.owners[ss][si].Call != 0 {
				cell := b.owners[ss][si]
				if cell.Native != value || b.pixels[cell.Local] != value {
					panic("來源身分與原版色號不同")
				}
				b.owners[s][i] = cell
				b.transferred++
				b.copySites[site]++
				if len(b.copySamples) < 12 {
					b.copySamples = append(b.copySamples, map[string]any{"step": b.m.Steps, "cs_ip": site, "code16": fmt.Sprintf("%x", b.read(cs, ip, 16)), "registers": b.m.CPU.R, "segments": b.m.CPU.Seg, "source": source, "destination": addr, "value": value, "local": cell.Local})
				}
			}
		}
	}
	if b.tracked[s][i] {
		if len(b.events) >= 100000 {
			panic("人物矩形寫入證據超限")
		}
		b.events = append(b.events, map[string]any{"kind": "write", "step": b.m.Steps, "surface": s, "offset": i, "old": old, "value": value, "site": site, "code16": fmt.Sprintf("%x", b.read(cs, ip, 16)), "after_cell": b.owners[s][i]})
	}
}
func personState(m *golem.Machine) map[string]any {
	return map[string]any{"steps": m.Steps, "memory_sha256": personHash(m.Mem), "indexed_sha256": personHash(m.Indexed()), "palette_sha256": personHash(m.DAC[:]), "registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags, "cycles": m.CPU.Cycles}
}
func main() {
	root := flag.String("root", "/game", "唯讀合法原版")
	seed := flag.String("seed", "", "正常產生的COLONY09.SAV")
	inputs := flag.String("inputs", "", "既有正常GUI輸入")
	pixels := flag.String("pixels", "", "本機第100幀96個索引點")
	out := flag.String("out", "", "尚不存在的本機研究輸出")
	control := flag.Bool("control", false, "不安裝觀測器的同輸入對照")
	pointsFile := flag.String("lifecycle-points", "", "可選：已固定49點正常GUI原版收據")
	flag.Parse()
	for n, h := range map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"ICONS.SS":    "a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
	} {
		p := filepath.Join(*root, n)
		if _, e := os.Stat(p); os.IsNotExist(e) {
			fmt.Fprintln(os.Stderr, "SKIP：缺少合法原版 "+n)
			os.Exit(77)
		}
		if personHash(personRead(p)) != h {
			panic("原版版本不同：" + n)
		}
	}
	seedBytes, inputBytes, pixelBytes := personRead(*seed), personRead(*inputs), personRead(*pixels)
	wantInput := "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979"
	var points []personPoint
	if *pointsFile != "" {
		wantInput = "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"
		raw := personRead(*pointsFile)
		if personHash(raw) != "821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901" {
			panic("49點原版收據不同")
		}
		personNeed(json.Unmarshal(raw, &points))
		if len(points) != 49 {
			panic("檢查點數不同")
		}
	}
	if personHash(seedBytes) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" || personHash(inputBytes) != wantInput || len(pixelBytes) != 96 || personHash(pixelBytes) != personPixelsSHA {
		panic("正常輸入、存檔或素材不同")
	}
	var replay struct {
		Inputs []personInput `json:"inputs"`
		End    uint64        `json:"end"`
	}
	personNeed(json.Unmarshal(inputBytes, &replay))
	end := uint64(75900000)
	if *pointsFile != "" {
		end = 134600000
	}
	if replay.End < end {
		panic("正常輸入未達終點")
	}
	personNeed(os.Mkdir(*out, 0755))
	scratch := filepath.Join(*out, "saves")
	personNeed(os.Mkdir(scratch, 0755))
	personNeed(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seedBytes, 0644))
	m := golem.New()
	personNeed(m.LoadEXE(personRead(filepath.Join(*root, "OPENING.EXE"))))
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
	var observer *personObserver
	if !*control {
		observer = &personObserver{m: m, pixels: pixelBytes, losses: map[string]uint64{}, copySites: map[string]uint64{}}
		for _, base := range []uint32{personMain, personStage} {
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
			if personHash(m.Mem) != p.Memory || personHash(m.Indexed()) != p.Indexed || personHash(m.DAC[:]) != p.Palette || m.CPU.R != p.Registers || m.CPU.Seg != p.Segments || m.CPU.IP != p.IP || m.CPU.Flags != p.Flags {
				panic("人物觀測與既有完整原版狀態不同")
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
		state := personState(m)
		state["dos_input_count"] = count
		state["snapshot_prefix"] = name
		if observer != nil {
			state["event_count"] = len(observer.events)
		}
		checkpoints = append(checkpoints, state)
		for suffix, data := range map[string][]byte{".idx": m.Indexed(), ".canvas": m.Mem[personMain : personMain+64000], ".stage": m.Mem[personStage : personStage+64000], ".palette": m.DAC[:]} {
			personNeed(os.WriteFile(filepath.Join(*out, name+suffix), data, 0644))
		}
		if observer != nil {
			owners := map[string]map[int]personCell{"main": {}, "stage": {}}
			for surface, key := range []string{"main", "stage"} {
				for i, c := range observer.owners[surface] {
					if c.Call != 0 {
						owners[key][i] = c
					}
				}
			}
			personJSON(filepath.Join(*out, name+".owners.json"), owners)
		}
	}
	step := func() { observer.beforeStep(); capture(); personNeed(m.Step()) }
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
	personNeed(os.WriteFile(filepath.Join(*out, "final.memory"), m.Mem, 0644))
	result := map[string]any{"kind": "readonly-person-100-normal-input-research", "control": *control, "input_sha256": personHash(inputBytes), "seed_sha256": personHash(seedBytes), "checkpoints": checkpoints, "end": personState(m), "dos_inputs": count, "address_space": "dosgolem real-mode CS:IP and 20-bit linear RAM; not IDA EA", "limitations": "Single source; no production HD, animation, profession or unobserved restoration claim."}
	if observer != nil {
		if observer.active != nil {
			panic("終點仍在繪製")
		}
		personJSON(filepath.Join(*out, "writes.json"), observer.events)
		result["calls"] = observer.calls
		result["source_matches"] = len(observer.calls)
		result["ownership_loss_sites"] = observer.losses
		result["same_value_ownership_losses"] = observer.same
		result["verified_transferred_pixels"] = observer.transferred
		result["copy_sites"] = observer.copySites
		result["copy_samples"] = observer.copySamples
	}
	personJSON(filepath.Join(*out, "draws.json"), result)
	fmt.Printf("steps=%d memory=%s control=%v\n", m.Steps, personHash(m.Mem), *control)
}
