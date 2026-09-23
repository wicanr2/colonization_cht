// 目標090可丟棄探針：觀測相鄰旗卡重繪時原版讀字與畫布寫入。
// 原版只讀；原始畫布、事件與完整狀態只存 workplace。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type input090 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replay090 struct {
	Inputs []input090 `json:"inputs"`
	End    uint64     `json:"end"`
}
type read090 struct {
	Step   uint64 `json:"step"`
	Site   string `json:"site"`
	Linear uint32 `json:"linear"`
	Value  uint8  `json:"value"`
}
type write090 struct {
	Step   uint64 `json:"step"`
	Site   string `json:"site"`
	Region string `json:"region"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Old    uint8  `json:"old"`
	Value  uint8  `json:"value"`
}
type ram090 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	Site   string `json:"site"`
	Linear uint32 `json:"linear"`
	Old    uint8  `json:"old,omitempty"`
	Value  uint8  `json:"value"`
}

func must090(err error) {
	if err != nil {
		panic(err)
	}
}
func file090(path string) []byte { b, err := os.ReadFile(path); must090(err); return b }
func sha090(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func locations090(mem []byte, needle string) []int {
	addresses := []int{}
	for start := 0; start < len(mem); {
		rel := bytes.Index(mem[start:], []byte(needle))
		if rel < 0 {
			break
		}
		at := start + rel
		addresses = append(addresses, at)
		if len(addresses) > 256 {
			panic("候選 RAM 副本過多")
		}
		start = at + 1
	}
	return addresses
}

func main() {
	root := flag.String("root", "/game", "唯讀原版目錄")
	inputs := flag.String("inputs", "", "固定16筆玩家輸入")
	out := flag.String("out", "", "workplace 內輸出前綴")
	control := flag.Bool("control", false, "無讀寫監看的同輸入控制")
	flow := flag.Bool("flow", false, "監看 TXT 載入至 RAM 與新卡印字來源；單一寫入槽不能同時監看畫布")
	precise := flag.Bool("precise", false, "目標091：另存右側兩欄精確印字前後畫布")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("必須指定 inputs 與 out")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must090(err)
	stat, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(stat.Uid) != os.Getuid() {
		panic("輸出目錄不存在或擁有者不符")
	}
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NATIONS.PIK": "bd31e62d7b7652e6903aaea76b1641f11d5333ff6a6da13fd26411c9f080bf54",
	}
	for name, want := range wants {
		if sha090(file090(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputBytes := file090(*inputs)
	if sha090(inputBytes) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("輸入收據版本不符")
	}
	var replay replay090
	must090(json.Unmarshal(inputBytes, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("輸入收據結構不符")
	}
	m := golem.New()
	must090(m.LoadEXE(file090(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	const start uint64 = 44000000
	const stop uint64 = 44300000
	reads := []read090{}
	writes := []write090{}
	ramEvents := []ram090{}
	readCount, writeCount := 0, 0
	readTruncated, writeTruncated := false, false
	ramTruncated := false
	relevantRAM := func(a uint32) bool {
		return (0x2b0d0 <= a && a < 0x2b110) || (0x249d0 <= a && a < 0x249f0) ||
			(0x26c50 <= a && a < 0x26c80) || (0x4cbb0 <= a && a < 0x4cbe0) ||
			(0x4dfc0 <= a && a < 0x4dff0) || (0x2a700 <= a && a < 0x2a7c0) ||
			(0x21ae0 <= a && a < 0x21b20)
	}
	collectRAM := func(kind string, a uint32, old, value uint8) {
		step := m.Steps
		loading := (15500000 <= step && step < 15560000) || (17020000 <= step && step < 17080000) ||
			(18070000 <= step && step < 18140000)
		display := 44110000 <= step && step < 44150000
		if !*flow || !(loading || display) || !relevantRAM(a) {
			return
		}
		if len(ramEvents) >= 50000 {
			ramTruncated = true
			return
		}
		cs, ip := m.CPU.OpAddr()
		ramEvents = append(ramEvents, ram090{m.Steps, kind, fmt.Sprintf("%04X:%04X", cs, ip), a, old, value})
	}
	if !*control {
		m.WatchReads(0x20000, 0x4ffff, func(a uint32, value uint8) {
			collectRAM("read", a, 0, value)
			if m.Steps < start || m.Steps >= stop {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if !(cs == 0x0d21 && ip == 0x00c6) && !(cs == 0x0d3a && ip == 0x0015) {
				return
			}
			readCount++
			if len(reads) >= 12000 {
				readTruncated = true
				return
			}
			reads = append(reads, read090{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, value})
		})
		if *flow {
			// WatchWrites 只通知值有變化的寫入；解析緩衝需補同值寫入。
			m.WatchWrite(0x249d0, 0x249ef, func(_ *golem.Machine, a uint32, old, value uint8) {
				collectRAM("write", a, old, value)
			})
			m.WatchWrites(0x20000, 0x4ffff, func(a uint32, old, value uint8) {
				if 0x249d0 <= a && a < 0x249f0 {
					return
				}
				collectRAM("write", a, old, value)
			})
		} else {
			m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, value uint8) {
				if m.Steps < start || m.Steps >= stop || old == value {
					return
				}
				i := int(a - canvas)
				x, y := i%320, i/320
				region := ""
				if 125 <= x && x < 190 && 12 <= y && y < 25 {
					region = "upper"
				}
				if 125 <= x && x < 190 && 83 <= y && y < 96 {
					region = "lower"
				}
				cs, ip := m.CPU.OpAddr()
				if region == "" {
					if cs != 0x0d21 || ip != 0x012c {
						return
					}
					region = "other-text"
				}
				writeCount++
				if len(writes) >= 16000 {
					writeTruncated = true
					return
				}
				writes = append(writes, write090{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), region, x, y, old, value})
			})
		}
	}
	advance := func(target uint64) {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			must090(m.Step())
		}
		if m.Steps != target {
			panic("原版提前結束")
		}
	}
	apply := func(e input090) {
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
			panic("非法輸入事件")
		}
	}
	previous := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > replay.End || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("非法輸入收據")
		}
		if e.Step > 43000000 {
			break
		}
		advance(e.Step)
		apply(e)
		previous = e.Step
	}
	advance(43000000)
	residentBefore := map[string][]int{}
	for _, candidate := range []string{"France", "Cooperation", "FRANCE:"} {
		residentBefore[candidate] = locations090(m.Mem, candidate)
	}
	if sha090(m.Indexed()) != "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" ||
		sha090(m.Mem[canvas:canvas+64000]) != "2e005b93f811c7e0eb557eb68d1f5c1721caf027e5f32220c3c62195e7c9100b" {
		panic("旗卡基準不符")
	}
	d.MoveMouse(255, 50)
	advance(44000000)
	d.PressMouse(0)
	steps := []uint64{44000000, 44050000, 44100000, 44150000, 44200000, 44220000, 44240000, 44300000, 45000000}
	preciseNames := map[uint64]string{}
	if *precise {
		steps = []uint64{44000000, 44050000, 44100000, 44123301, 44129564,
			44133138, 44142300, 44150000, 44200000, 44220000, 44240000, 44300000, 45000000}
		preciseNames = map[uint64]string{44123301: "before-upper", 44129564: "after-upper",
			44133138: "before-lower", 44142300: "after-lower"}
	}
	samples := map[string]any{}
	preciseSnapshots := map[string]any{}
	for _, target := range steps {
		advance(target)
		label := fmt.Sprintf("%d", target)
		b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
		must090(os.WriteFile(*out+"."+label+".canvas", b, 0644))
		samples[label] = map[string]any{"canvas_sha256": sha090(b), "indexed_sha256": sha090(m.Indexed()),
			"memory_sha256": sha090(m.Mem), "cycles": m.CPU.Cycles, "ticks": m.Ticks}
		if name, ok := preciseNames[target]; ok {
			must090(os.WriteFile(*out+"."+name+".canvas", b, 0644))
			indexed := m.Indexed()
			must090(os.WriteFile(*out+"."+name+".idx", indexed, 0644))
			preciseSnapshots[name] = map[string]any{"step": target, "canvas_sha256": sha090(b),
				"indexed_sha256": sha090(indexed)}
		}
	}
	if *precise {
		must090(os.WriteFile(*out+".final.idx", m.Indexed(), 0644))
		must090(os.WriteFile(*out+".final.pal", m.DAC[:], 0644))
	}
	state := map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks,
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
		"memory_sha256": sha090(m.Mem), "indexed_sha256": sha090(m.Indexed()),
		"palette_sha256": sha090(m.DAC[:]), "canvas_sha256": sha090(m.Mem[canvas : canvas+64000])}
	result := map[string]any{"version": "goal090-neighbor-text-v2", "control": *control, "flow": *flow,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas; file offsets",
		"input_sha256":  sha090(inputBytes), "input_hashes": wants, "reads": reads, "read_count": readCount,
		"read_truncated": readTruncated, "writes": writes, "write_count": writeCount,
		"write_truncated": writeTruncated, "ram_events": ramEvents, "ram_truncated": ramTruncated,
		"samples": samples, "precise_snapshots": preciseSnapshots, "opened": d.Opened, "state": state,
		"resident_before": residentBefore,
		"resident_after": map[string][]int{"France": locations090(m.Mem, "France"),
			"Cooperation": locations090(m.Mem, "Cooperation"), "FRANCE:": locations090(m.Mem, "FRANCE:")}}
	b, err := json.MarshalIndent(result, "", "  ")
	must090(err)
	must090(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("相鄰旗卡：讀字 %d、區域寫入 %d、截斷 %t/%t、狀態 %s\n", readCount, writeCount, readTruncated, writeTruncated, state["memory_sha256"])
}
