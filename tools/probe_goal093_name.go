// 目標093：從正常玩家路徑追姓名畫面原始來源與鍵盤反應。
// 原版唯讀；原始畫布及 RAM 線索僅輸出到已忽略的 workplace。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type event093 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int
}
type replay093 struct {
	Inputs []event093 `json:"inputs"`
	End    uint64     `json:"end"`
}
type source093 struct {
	Name   string `json:"name"`
	Offset int64  `json:"offset"`
	Bytes  string `json:"bytes"`
}
type read093 struct {
	Step   uint64 `json:"step"`
	CSIP   string `json:"cs_ip"`
	Linear uint32 `json:"linear"`
	Value  uint8  `json:"value"`
}
type write093 struct {
	Step     uint64 `json:"step"`
	CSIP     string `json:"cs_ip"`
	X, Y     int
	Old, New uint8
}
type ramwrite093 struct {
	Step     uint64 `json:"step"`
	CSIP     string `json:"cs_ip"`
	Linear   uint32 `json:"linear"`
	Old, New uint8
}

func must093(err error) {
	if err != nil {
		panic(err)
	}
}
func file093(path string) []byte { b, err := os.ReadFile(path); must093(err); return b }
func sha093(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法原版唯讀目錄")
	inputs := flag.String("inputs", "", "已驗十六筆正常玩家輸入")
	out := flag.String("out", "", "workplace 內輸出前綴")
	scenario := flag.String("scenario", "idle", "idle、letter、backspace、enter 或 letter-enter")
	control := flag.Bool("control", false, "無讀寫／逐幀觀測對照組")
	flag.Parse()
	if *inputs == "" || *out == "" ||
		(*scenario != "idle" && *scenario != "letter" && *scenario != "backspace" &&
			*scenario != "enter" && *scenario != "letter-enter") {
		panic("探針參數不完整")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must093(err)
	owner, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
		panic("輸出目錄擁有者不符")
	}
	wants := map[string]string{
		"OPENING.EXE":  "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE":  "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":     "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"NAMES.TXT":    "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"LABELS.TXT":   "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NATIONS.PIK":  "bd31e62d7b7652e6903aaea76b1641f11d5333ff6a6da13fd26411c9f080bf54",
		"WOODPANL.PIK": "0858856ad5b5dd0b6ab8e7a8f815fa602a9cf0237d8d323cd2b5ca141b32bc69",
	}
	for name, want := range wants {
		if sha093(file093(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	sources := []source093{{"GAME.TXT", 0xA7C, "Please Enter Your Name."},
		{"NAMES.TXT", 0xB4B, "Jacques Cartier"}}
	for _, s := range sources {
		b := file093(filepath.Join(*root, s.Name))
		if !bytes.Equal(b[s.Offset:s.Offset+int64(len(s.Bytes))], []byte(s.Bytes)) {
			panic("候選原始位元組不符：" + s.Name)
		}
	}
	inputData := file093(*inputs)
	if sha093(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("正常玩家輸入指紋不符")
	}
	var replay replay093
	must093(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("輸入結構不符")
	}
	m := golem.New()
	must093(m.LoadEXE(file093(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	reads := []read093{}
	loadReads := []read093{}
	loadWrites := []ramwrite093{}
	sourceReads := []read093{}
	ramWrites := []ramwrite093{}
	writes := []write093{}
	frames := []map[string]any{}
	readTotal, writeTotal := 0, 0
	if !*control {
		inNameLoad := func(a uint32) bool {
			return (0x21ae2 <= a && a < 0x21af1) || (0x2b14d <= a && a < 0x2b15c)
		}
		inSource := func(a uint32) bool {
			return (0x21ad0 <= a && a < 0x21b10) ||
				(0x2a860 <= a && a < 0x2a870) ||
				(0x2a970 <= a && a < 0x2a980) ||
				(0x2aa00 <= a && a < 0x2aa20) ||
				(0x2b060 <= a && a < 0x2b0a0) ||
				(0x6f1f0 <= a && a < 0x6f280)
		}
		m.WatchReads(0x20000, 0x7ffff, func(a uint32, value uint8) {
			if 15000000 <= m.Steps && m.Steps < 18500000 && inNameLoad(a) && len(loadReads) < 30000 {
				cs, ip := m.CPU.OpAddr()
				loadReads = append(loadReads, read093{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, value})
			}
			if m.Steps < 48000000 || m.Steps >= 50000000 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if 48655000 <= m.Steps && m.Steps < 48770000 && inSource(a) && len(sourceReads) < 30000 {
				sourceReads = append(sourceReads, read093{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, value})
			}
			if !(cs == 0x0d3a && ip == 0x0015) && !(cs == 0x0d21 && ip == 0x00c6) {
				return
			}
			readTotal++
			if len(reads) < 30000 {
				reads = append(reads, read093{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, value})
			}
		})
		m.WatchWrites(0x20000, 0x7ffff, func(a uint32, old, value uint8) {
			if 15000000 <= m.Steps && m.Steps < 18500000 && inNameLoad(a) && len(loadWrites) < 30000 {
				cs, ip := m.CPU.OpAddr()
				loadWrites = append(loadWrites, ramwrite093{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, old, value})
			}
			if 48655000 <= m.Steps && m.Steps < 48770000 && inSource(a) && len(ramWrites) < 30000 {
				cs, ip := m.CPU.OpAddr()
				ramWrites = append(ramWrites, ramwrite093{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, old, value})
			}
			if a < canvas || a >= canvas+64000 {
				return
			}
			if m.Steps < 48000000 || m.Steps >= 50000000 || old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if cs != 0x0d21 || ip != 0x012c {
				return
			}
			writeTotal++
			if len(writes) < 20000 {
				i := int(a - canvas)
				writes = append(writes, write093{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), i % 320, i / 320, old, value})
			}
		})
		m.SetOnFrame(func() {
			if m.Steps < 47000000 || len(frames) >= 200 {
				return
			}
			frames = append(frames, map[string]any{"step": m.Steps, "indexed_sha256": sha093(m.Indexed()),
				"canvas_sha256": sha093(m.Mem[canvas : canvas+64000]), "opened_count": len(d.Opened)})
		})
	}
	transferIndex := 0
	transfers := []map[string]any{}
	collectTransfers := func() {
		for transferIndex < len(d.Reads) {
			r := d.Reads[transferIndex]
			transferIndex++
			for _, s := range sources {
				if !strings.EqualFold(r.Name, s.Name) {
					continue
				}
				pos := int64(-1)
				for j := len(d.FileOps) - 1; j >= 0; j-- {
					op := d.FileOps[j]
					if op.Step == r.Step && op.Fn == 0x3f && op.Handle == r.Handle && strings.EqualFold(op.Name, r.Name) {
						pos = op.Pos
						break
					}
				}
				if pos < 0 || !(pos <= s.Offset && s.Offset+int64(len(s.Bytes)) <= pos+int64(r.Got)) {
					continue
				}
				linear := uint32(r.Seg)*16 + uint32(r.Off) + uint32(s.Offset-pos)
				transfers = append(transfers, map[string]any{"step": r.Step, "name": s.Name, "file_offset": s.Offset,
					"read_pos": pos, "got": r.Got, "destination_seg": r.Seg, "destination_off": r.Off,
					"candidate_linear": linear, "match": bytes.Equal(m.Mem[linear:linear+uint32(len(s.Bytes))], []byte(s.Bytes))})
			}
		}
	}
	advance := func(end uint64) {
		for m.Steps < end && !d.Exited && !m.CPU.Halted {
			must093(m.Step())
			if transferIndex < len(d.Reads) {
				collectTransfers()
			}
		}
		if m.Steps != end {
			panic("原版提前停止")
		}
	}
	apply := func(e event093) {
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		default:
			panic("未知玩家事件")
		}
	}
	for _, e := range replay.Inputs {
		if e.Step > 43000000 {
			break
		}
		advance(e.Step)
		apply(e)
	}
	advance(43000000)
	if sha093(m.Indexed()) != "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" {
		panic("第一張旗卡基準不符")
	}
	d.MoveMouse(255, 50)
	advance(44000000)
	d.PressMouse(0)
	advance(45000000)
	d.ReleaseMouse(0)
	advance(46000000)
	if sha093(m.Indexed()) != "c867bee2f4c5b7a0af07415d68bccb8d028c905fba53d830b01bfb300672af74" {
		panic("右卡基準不符")
	}
	d.MoveMouse(65, 184)
	advance(47000000)
	d.PressMouse(0)
	advance(48000000)
	d.ReleaseMouse(0)
	samples := map[string]map[string]any{}
	sample := func(name string) {
		collectTransfers()
		indexed := m.Indexed()
		picture := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
		must093(os.WriteFile(*out+"."+name+".idx", indexed, 0644))
		must093(os.WriteFile(*out+"."+name+".canvas", picture, 0644))
		must093(os.WriteFile(*out+"."+name+".pal", m.DAC[:], 0644))
		hits := map[string][]int{}
		for _, s := range sources {
			for cursor := 0; cursor < len(m.Mem); {
				i := bytes.Index(m.Mem[cursor:], []byte(s.Bytes))
				if i < 0 {
					break
				}
				cursor += i
				if len(hits[s.Name]) < 40 {
					hits[s.Name] = append(hits[s.Name], cursor)
				}
				cursor++
			}
		}
		samples[name] = map[string]any{"step": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks,
			"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
			"memory_sha256": sha093(m.Mem), "indexed_sha256": sha093(indexed),
			"canvas_sha256": sha093(picture), "palette_sha256": sha093(m.DAC[:]),
			"opened_count": len(d.Opened), "resident_hits": hits,
			"video_mode": m.VideoMode(), "exited": d.Exited, "halted": m.CPU.Halted}
	}
	advance(49000000)
	sample("49m")
	if sha093(m.Indexed()) != "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e" ||
		sha093(m.Mem[canvas:canvas+64000]) != "4182cf7454d507e9dda76e4d81bde65ded7508314c5c518892508f8cddfb1b37" {
		panic("姓名畫面基準不符")
	}
	advance(55000000)
	sample("55m")
	if *scenario == "letter" || *scenario == "backspace" || *scenario == "letter-enter" {
		d.PushKey(golem.Key{Scan: 0x2d, ASCII: 'x'})
	} else if *scenario == "enter" {
		d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
	}
	advance(57000000)
	sample("57m")
	if *scenario == "backspace" {
		d.PushKey(golem.Key{Scan: 0x0e, ASCII: 8})
	}
	if *scenario == "letter-enter" {
		d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
	}
	advance(65000000)
	sample("65m")
	collectTransfers()
	report := map[string]any{"version": "goal093-name-v1", "scenario": *scenario, "control": *control,
		"input_sha256": sha093(inputData), "input_hashes": wants, "sources": sources,
		"transfers": transfers, "samples": samples, "reads": reads,
		"load_reads": loadReads, "load_writes": loadWrites, "source_reads": sourceReads,
		"ram_writes": ramWrites, "writes": writes,
		"read_total": readTotal, "write_total": writeTotal, "frames": frames, "opened": d.Opened,
		"address_space": "original file offset; DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas"}
	data, err := json.MarshalIndent(report, "", "  ")
	must093(err)
	must093(os.WriteFile(*out+".json", append(data, '\n'), 0644))
	fmt.Printf("scenario=%s control=%v transfers=%d reads=%d writes=%d frames=%d end=%d opened=%d\n",
		*scenario, *control, len(transfers), readTotal, writeTotal, len(frames), m.Steps, len(d.Opened))
}
