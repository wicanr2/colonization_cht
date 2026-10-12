// 研究用：重播正常 GUI 輸入，唯讀追查 PHYS0.SS 第148幀。
// 不由正式組裝器引用，不安裝 HD，不修改原版狀態。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"

	golem "github.com/wicanr2/dosgolem"
)

const seaCanvas = 0x2cae0
const seaStageCanvas = 0x3c500
const seaEncodedSHA = "192698d118f87f0f0c4f1605962c000a63db80c935510cef2b4087bf2bd8399f"
const seaPixelsSHA = "4f040c4dd1172b8c81c2f0a21b42cf21c5c14bdac7db5fe6ebc9a45d4e4f693a"

func seaNeed(err error) {
	if err != nil {
		panic(err)
	}
}
func seaRead(path string) []byte { b, err := os.ReadFile(path); seaNeed(err); return b }
func seaHash(b []byte) string    { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func seaJSON(path string, value any) {
	b, err := json.MarshalIndent(value, "", "  ")
	seaNeed(err)
	seaNeed(os.WriteFile(path, append(b, '\n'), 0644))
}

type seaInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int `json:"button"`
}

type seaCall struct {
	Entry      uint64            `json:"entry_step"`
	Return     uint64            `json:"return_step"`
	Registers  [8]uint16         `json:"registers"`
	Segments   [4]uint16         `json:"segments"`
	Args       []uint16          `json:"ss_sp_plus4_words"`
	Descriptor []uint16          `json:"ds_bx_words"`
	RecordFar  string            `json:"record_far"`
	Record     []uint16          `json:"record_words"`
	SourceFar  string            `json:"source_far"`
	SourceSHA  string            `json:"source_first_263_sha256"`
	ReturnSite string            `json:"return_cs_ip"`
	Rect       [4]int            `json:"rect"`
	Selected   bool              `json:"selected"`
	Writes     int               `json:"unique_writes"`
	WriteCount uint64            `json:"write_count"`
	WriteSHA   string            `json:"sorted_local_offset_value_sha256"`
	WriterSite map[string]uint64 `json:"writer_sites"`
	BeforeSHA  string            `json:"before_roi_sha256"`
	AfterSHA   string            `json:"after_roi_sha256"`
	Mismatch   string            `json:"geometry_or_write_mismatch,omitempty"`
}

type seaObserver struct {
	m           *golem.Machine
	out         string
	pixels      []byte
	active      *seaCall
	retCS       uint16
	retIP       uint16
	sp          uint16
	before      []byte
	writes      map[uint32][3]uint64
	calls       []*seaCall
	owners      [64000]int
	losses      map[string]uint64
	same        uint64
	matched     int
	copySites   map[string]uint64
	copySamples []map[string]any
	mainOwners  [64000]int
	mainOrigins [64000]int
	transferred uint64
	mainLosses  map[string]uint64
}

func (b *seaObserver) read(seg, off uint16, size int) []byte {
	at := uint32(seg)*16 + uint32(off)
	if uint64(at)+uint64(size) > uint64(len(b.m.Mem)) {
		panic("研究讀取越界")
	}
	return b.m.Mem[at : at+uint32(size)]
}
func seaWords(data []byte) []uint16 {
	words := make([]uint16, len(data)/2)
	for i := range words {
		words[i] = binary.LittleEndian.Uint16(data[i*2 : i*2+2])
	}
	return words
}
func (b *seaObserver) roi(rect [4]int) []byte {
	var data []byte
	for y := rect[1]; y < rect[3]; y++ {
		data = append(data, b.m.Mem[seaStageCanvas+y*320+rect[0]:seaStageCanvas+y*320+rect[2]]...)
	}
	return data
}

func (b *seaObserver) finish() {
	c := b.active
	c.Return = b.m.Steps
	c.Writes = len(b.writes)
	c.AfterSHA = seaHash(b.roi(c.Rect))
	var sorted []int
	for addr, values := range b.writes {
		c.WriteCount += values[2]
		i := int(addr) - seaStageCanvas
		x, y := i%320-c.Rect[0], i/320-c.Rect[1]
		if x < 0 || x >= 16 || y < 0 || y >= 16 || values[2] != 1 || uint8(values[1]) != b.pixels[y*16+x] {
			c.Mismatch = "寫入超出矩形、重複或色號不同"
			continue
		}
		sorted = append(sorted, y*16+x)
	}
	if c.Writes != 256 || c.AfterSHA != seaPixelsSHA {
		c.Mismatch = "未完整寫入256點或返回圖像不同"
	}
	sort.Ints(sorted)
	var encoded []byte
	for _, i := range sorted {
		encoded = binary.LittleEndian.AppendUint16(encoded, uint16(i))
		encoded = append(encoded, b.pixels[i])
	}
	c.WriteSHA = seaHash(encoded)
	if c.Mismatch == "" {
		for y := c.Rect[1]; y < c.Rect[3]; y++ {
			for x := c.Rect[0]; x < c.Rect[2]; x++ {
				b.owners[y*320+x] = len(b.calls)
			}
		}
	}
	if b.matched == 1 {
		seaNeed(os.WriteFile(filepath.Join(b.out, "first-before-canvas.idx"), b.before, 0644))
		seaNeed(os.WriteFile(filepath.Join(b.out, "first-after-canvas.idx"), b.m.Mem[seaStageCanvas:seaStageCanvas+64000], 0644))
	}
	b.active = nil
}

func (b *seaObserver) beforeStep() {
	if b == nil || b.m.Steps < 50000000 {
		return
	}
	m := b.m
	if b.active != nil {
		if m.CPU.Seg[golem.CS] == b.retCS && m.CPU.IP == b.retIP && m.CPU.R[golem.SP] == b.sp+10 {
			b.finish()
		} else if m.Steps-b.active.Entry > 100000 {
			panic("已匹配來源的繪製未在界限內返回")
		}
	}
	if m.CPU.Seg[golem.CS] != 0xd46 || m.CPU.IP != 0x000a {
		return
	}
	if b.active != nil || len(b.calls) >= 20000 {
		panic("研究呼叫重入或超出界限")
	}
	if !bytes.Equal(b.read(0xd46, 0x000a, 12), []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 0x02}) {
		panic("已驗 IDA 入口碼不同")
	}
	sp, ss := m.CPU.R[golem.SP], m.CPU.Seg[golem.SS]
	stack := seaWords(b.read(ss, sp, 10))
	// 原始位移運算沿規格061的IDA讀取指令；此處先記原始讀值。
	off := uint16((m.CPU.R[golem.AX]&0x7fff)*12 + stack[3] + 0x36)
	r := seaWords(b.read(stack[4], off, 12))
	c := &seaCall{Entry: m.Steps, Registers: m.CPU.R, Segments: m.CPU.Seg,
		Args: stack[2:], Descriptor: seaWords(b.read(m.CPU.Seg[golem.DS], m.CPU.R[golem.BX], 8)),
		RecordFar: fmt.Sprintf("%04X:%04X", stack[4], off), Record: r,
		SourceFar:  fmt.Sprintf("%04X:%04X", r[1], r[0]),
		SourceSHA:  seaHash(b.read(r[1], r[0], 263)),
		ReturnSite: fmt.Sprintf("%04X:%04X", stack[1], stack[0])}
	b.calls = append(b.calls, c)
	if c.SourceSHA != seaEncodedSHA {
		return
	}
	b.matched++
	x, y := int(int16(m.CPU.R[golem.DX])), int(int16(stack[2]))
	c.Rect = [4]int{x, y, x + 16, y + 16}
	if r[4] != 16 || r[5] != 16 || c.Descriptor[0] != 200 || c.Descriptor[1] != 320 ||
		uint32(c.Descriptor[3])*16+uint32(c.Descriptor[2]) != seaStageCanvas ||
		x < 0 || x+16 > 320 || y < 0 || y+16 > 200 || m.CPU.R[golem.AX]&0x8000 != 0 {
		c.Mismatch = "來源相同但幾何、畫布或高位未驗"
		return
	}
	c.Selected = true
	c.WriterSite = map[string]uint64{}
	c.BeforeSHA = seaHash(b.roi(c.Rect))
	b.before = append(b.before[:0], m.Mem[seaStageCanvas:seaStageCanvas+64000]...)
	b.active, b.retCS, b.retIP, b.sp = c, stack[1], stack[0], sp
	b.writes = map[uint32][3]uint64{}
}

func (b *seaObserver) write(addr uint32, old, value uint8) {
	if b.m.Steps < 50000000 {
		return
	}
	cs, ip := b.m.CPU.OpAddr()
	site := fmt.Sprintf("%04X:%04X", cs, ip)
	i := int(addr) - seaStageCanvas
	if b.owners[i] != 0 {
		b.losses[site]++
		if old == value {
			b.same++
		}
		b.owners[i] = 0
	}
	if b.active == nil {
		return
	}
	r, exists := b.writes[addr]
	if !exists {
		r[0] = uint64(old)
	}
	r[1], r[2] = uint64(value), r[2]+1
	b.writes[addr] = r
	b.active.WriterSite[site]++
}

// 限本次已觀測的 REP MOVSW。每個word的兩次byte回呼以目的位移補足來源。
// 只傳遞本探針已完整驗證的來源身分，不按畫面相似度還原被後畫撤銷的點。
func (b *seaObserver) canvasWrite(addr uint32, old, value uint8) {
	m := b.m
	if m.Steps < 50000000 {
		return
	}
	i := int(addr) - seaCanvas
	cs, ip := m.CPU.OpAddr()
	site := fmt.Sprintf("%04X:%04X", cs, ip)
	if b.mainOwners[i] != 0 {
		b.mainLosses[site]++
	}
	b.mainOwners[i] = 0
	if cs == 0xcba && ip == 0xca && bytes.Equal(b.read(cs, ip, 16), []byte{0xf3, 0xa5, 0x03, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0x00, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0x00, 0x08}) {
		dest := int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI])
		delta := int(addr) - dest
		src := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.SI]) + delta
		if delta >= 0 && delta < 2 && src >= seaStageCanvas && src < seaStageCanvas+64000 && m.Mem[src] == value {
			sourceIndex := src - seaStageCanvas
			id := b.owners[sourceIndex]
			if id != 0 {
				c := b.calls[id-1]
				x, y := sourceIndex%320-c.Rect[0], sourceIndex/320-c.Rect[1]
				if x < 0 || x >= 16 || y < 0 || y >= 16 || b.pixels[y*16+x] != value {
					panic("已驗來源擁有權與複製色號不一致")
				}
				b.mainOwners[i] = id
				b.mainOrigins[i] = sourceIndex
				b.transferred++
			}
		}
	}
	if i%320 >= 16 || i/320 < 8 || i/320 >= 24 {
		return
	}
	b.copySites[site]++
	if b.copySites[site] > 12 {
		return
	}
	ss, sp := m.CPU.Seg[golem.SS], m.CPU.R[golem.SP]
	b.copySamples = append(b.copySamples, map[string]any{
		"step": m.Steps, "cs_ip": site, "linear_address": addr, "old": old, "value": value,
		"registers": m.CPU.R, "segments": m.CPU.Seg,
		"code_hex":  fmt.Sprintf("%x", b.read(cs, ip, 16)),
		"stack_hex": fmt.Sprintf("%x", b.read(ss, sp, 48))})
}

func seaState(m *golem.Machine) map[string]any {
	return map[string]any{"steps": m.Steps, "memory_sha256": seaHash(m.Mem),
		"indexed_sha256": seaHash(m.Indexed()), "palette_sha256": seaHash(m.DAC[:]),
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags}
}

func main() {
	root := flag.String("root", "/game", "唯讀合法原版")
	seed := flag.String("seed", "", "正常玩家產生的 COLONY09.SAV")
	inputs := flag.String("inputs", "", "既有正常 GUI 輸入收據")
	pixels := flag.String("pixels", "", "本機第148幀完整256點")
	out := flag.String("out", "", "新的本機研究輸出目錄")
	control := flag.Bool("control", false, "不安裝觀測器")
	flag.Parse()
	for name, want := range map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"PHYS0.SS":    "deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
	} {
		if _, err := os.Stat(filepath.Join(*root, name)); os.IsNotExist(err) {
			fmt.Fprintln(os.Stderr, "SKIP：缺少合法原版 "+name)
			os.Exit(77)
		}
		if seaHash(seaRead(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	seedBytes, inputBytes, pixelBytes := seaRead(*seed), seaRead(*inputs), seaRead(*pixels)
	if seaHash(seedBytes) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" ||
		seaHash(inputBytes) != "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979" ||
		len(pixelBytes) != 256 || seaHash(pixelBytes) != seaPixelsSHA {
		panic("初始存檔、正常輸入或素材不同")
	}
	var replay struct {
		Inputs []seaInput `json:"inputs"`
		End    uint64     `json:"end"`
	}
	seaNeed(json.Unmarshal(inputBytes, &replay))
	const end = uint64(75900000)
	if replay.End < end {
		panic("正常輸入未到檢查點")
	}
	seaNeed(os.Mkdir(*out, 0755))
	scratch := filepath.Join(*out, "saves")
	seaNeed(os.Mkdir(scratch, 0755))
	seaNeed(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seedBytes, 0644))
	m := golem.New()
	seaNeed(m.LoadEXE(seaRead(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		panic("無數位音效能力")
	}
	m.EnableOPLSynth(true)
	var observer *seaObserver
	if !*control {
		observer = &seaObserver{m: m, out: *out, pixels: pixelBytes, losses: map[string]uint64{}, copySites: map[string]uint64{}, mainLosses: map[string]uint64{}}
		m.WatchWrite(seaStageCanvas, seaStageCanvas+63999, func(_ *golem.Machine, addr uint32, old, value uint8) {
			observer.write(addr, old, value)
		})
		m.WatchWrite(seaCanvas, seaCanvas+63999, func(_ *golem.Machine, addr uint32, old, value uint8) { observer.canvasWrite(addr, old, value) })
	}
	var checkpoints []map[string]any
	capture := func() {
		if m.Steps != 63525000 && m.Steps != end {
			return
		}
		state := seaState(m)
		name := fmt.Sprintf("cp-%d", m.Steps)
		seaNeed(os.WriteFile(filepath.Join(*out, name+".idx"), m.Indexed(), 0644))
		seaNeed(os.WriteFile(filepath.Join(*out, name+".canvas"), m.Mem[seaCanvas:seaCanvas+64000], 0644))
		seaNeed(os.WriteFile(filepath.Join(*out, name+".stage"), m.Mem[seaStageCanvas:seaStageCanvas+64000], 0644))
		if observer != nil {
			counts := map[int]int{}
			for _, id := range observer.owners {
				if id != 0 {
					counts[id]++
				}
			}
			seaJSON(filepath.Join(*out, name+".owners.json"), counts)
			seaJSON(filepath.Join(*out, name+".main-owners.json"), observer.mainOwners)
			seaJSON(filepath.Join(*out, name+".main-origins.json"), observer.mainOrigins)
		}
		checkpoints = append(checkpoints, state)
	}
	step := func() { observer.beforeStep(); capture(); seaNeed(m.Step()) }
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
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		default:
			panic("未支援輸入：" + e.Kind)
		}
	}
	for m.Steps < end {
		step()
	}
	observer.beforeStep()
	capture()
	result := map[string]any{"kind": "readonly-sea-148-normal-input-research", "control": *control,
		"input_sha256": seaHash(inputBytes), "seed_sha256": seaHash(seedBytes), "checkpoints": checkpoints,
		"address_space": "dosgolem real-mode CS:IP; 20-bit linear RAM; no IDA EA conversion",
		"limitations":   "One normal-input trace; no HD, no production contract, no animation or clipping claim."}
	if observer != nil {
		if observer.active != nil {
			panic("終點仍在素材繪製中")
		}
		result["calls"] = observer.calls
		result["source_matches"] = observer.matched
		result["ownership_loss_sites"] = observer.losses
		result["same_value_ownership_losses"] = observer.same
		result["main_canvas_sample_rect"] = [4]int{0, 8, 16, 24}
		result["main_canvas_write_sites"] = observer.copySites
		result["main_canvas_write_samples"] = observer.copySamples
		result["verified_transferred_pixels"] = observer.transferred
		result["main_ownership_loss_sites"] = observer.mainLosses
	}
	seaJSON(filepath.Join(*out, "draws.json"), result)
	fmt.Printf("steps=%d memory=%s control=%v\n", m.Steps, seaHash(m.Mem), *control)
}
