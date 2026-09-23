// 目標085可丟棄探針：只讀觀測國家旗卡上下紅字候選區的 RAM 讀取與畫布寫入。
// 不是正式中文覆蓋；原版畫面、記憶體索引與收據只留本機 workplace。
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	golem "github.com/wicanr2/dosgolem"
)

type input struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replay struct {
	Inputs []input `json:"inputs"`
	End    uint64  `json:"end"`
}
type readEvent struct {
	Step   uint64 `json:"step"`
	Site   string `json:"site"`
	Linear uint32 `json:"linear"`
	Value  uint8  `json:"value"`
}
type writeEvent struct {
	Step   uint64 `json:"step"`
	Site   string `json:"site"`
	Region string `json:"region"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Old    uint8  `json:"old"`
	Value  uint8  `json:"value"`
}
type writeSummary struct {
	Count     int    `json:"count"`
	FirstStep uint64 `json:"first_step"`
	LastStep  uint64 `json:"last_step"`
	MinX      int    `json:"min_x"`
	MinY      int    `json:"min_y"`
	MaxX      int    `json:"max_x"`
	MaxY      int    `json:"max_y"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte {
	b, err := os.ReadFile(path)
	must(err)
	return b
}
func digest(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀目錄")
	inputs := flag.String("inputs", "", "已驗16筆真視窗輸入")
	out := flag.String("out", "", "本機輸出前綴")
	control := flag.Bool("control", false, "不註冊讀寫觀測器的同輸入對照")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("需明示 -inputs 與 -out")
	}
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"NATIONS.PIK": "bd31e62d7b7652e6903aaea76b1641f11d5333ff6a6da13fd26411c9f080bf54",
	}
	for name, want := range wants {
		if digest(read(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := read(*inputs)
	if digest(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("真視窗輸入指紋不符")
	}
	var trace replay
	must(json.Unmarshal(inputData, &trace))
	if len(trace.Inputs) != 16 || trace.End != 100000000 {
		panic("真視窗輸入結構不符")
	}
	var previous uint64
	for _, e := range trace.Inputs {
		if e.Step < previous || e.Step > 50000000 || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("非法真視窗事件")
		}
		previous = e.Step
	}
	m := golem.New()
	must(m.LoadEXE(read(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	const start uint64 = 42000000
	const stop uint64 = 44000000
	reads := []readEvent{}
	writes := []writeEvent{}
	sites := map[string]*writeSummary{}
	readCount, writeCount := 0, 0
	readTruncated, writeTruncated := false, false
	if !*control {
		// Machine 只有一組讀取監看槽；在同一回呼內分流來源與顯示讀取。
		m.WatchReads(0x28000, 0x4ffff, func(a uint32, value uint8) {
			if m.Steps < start || m.Steps > stop {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if cs != 0x0d21 || ip != 0x00c6 {
				if cs != 0x0d3a || ip != 0x0015 {
					return
				}
			}
			readCount++
			if len(reads) >= 16000 {
				readTruncated = true
				return
			}
			reads = append(reads, readEvent{Step: m.Steps,
				Site: fmt.Sprintf("%04X:%04X", cs, ip), Linear: a, Value: value})
		})
		m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, value uint8) {
			if m.Steps < start || m.Steps > stop || old == value {
				return
			}
			i := int(a - canvas)
			x, y := i%320, i/320
			region := ""
			if x >= 125 && x < 190 && y >= 12 && y < 25 {
				region = "upper"
			} else if x >= 125 && x < 190 && y >= 83 && y < 96 {
				region = "lower"
			}
			if region == "" {
				return
			}
			cs, ip := m.CPU.OpAddr()
			site := fmt.Sprintf("%04X:%04X", cs, ip)
			key := region + "/" + site
			writeCount++
			s := sites[key]
			if s == nil {
				s = &writeSummary{FirstStep: m.Steps, MinX: x, MinY: y, MaxX: x, MaxY: y}
				sites[key] = s
			}
			s.Count++
			s.LastStep = m.Steps
			if x < s.MinX {
				s.MinX = x
			}
			if y < s.MinY {
				s.MinY = y
			}
			if x > s.MaxX {
				s.MaxX = x
			}
			if y > s.MaxY {
				s.MaxY = y
			}
			if len(writes) >= 30000 {
				writeTruncated = true
				return
			}
			writes = append(writes, writeEvent{Step: m.Steps, Site: site, Region: region,
				X: x, Y: y, Old: old, Value: value})
		})
	}
	snapSteps := map[uint64]string{
		42200000: "after-release", 42400000: "before-card-text",
		42600000: "during-card-text", 42800000: "after-card-text",
		43000000: "settled-43m", 50000000: "settled-50m",
	}
	snaps := map[string]map[string]string{}
	openedAt := uint64(0)
	step := func() {
		if name, ok := snapSteps[m.Steps]; ok {
			b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
			idx := m.Indexed()
			must(os.WriteFile(*out+"."+name+".canvas", b, 0644))
			must(os.WriteFile(*out+"."+name+".idx", idx, 0644))
			snaps[name] = map[string]string{"canvas_sha256": digest(b), "indexed_sha256": digest(idx)}
		}
		must(m.Step())
		if openedAt == 0 && len(d.Opened) > 0 && strings.EqualFold(d.Opened[len(d.Opened)-1], "NATIONS.PIK") {
			openedAt = m.Steps
		}
	}
	apply := func(e input) {
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
			panic("未支援的玩家輸入")
		}
	}
	for _, e := range trace.Inputs {
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			step()
		}
		if d.Exited || m.CPU.Halted {
			panic("原版提前結束")
		}
		apply(e)
	}
	for m.Steps < 50000000 && !d.Exited && !m.CPU.Halted {
		step()
	}
	if m.Steps != 50000000 || openedAt == 0 {
		panic("未到達國家旗卡終點")
	}
	names := read(filepath.Join(*root, "NAMES.TXT"))
	labels := read(filepath.Join(*root, "LABELS.TXT"))
	result := map[string]any{
		"version": "goal085-nation-card-probe-v1", "control": *control,
		"input_sha256": digest(inputData), "input_hashes": wants,
		"tool_address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas; file offsets",
		"file_candidates": map[string]any{
			"NAMES.TXT:0x8EA":  string(names[0x8ea:0x8f1]),
			"LABELS.TXT:0x8F2": string(labels[0x8f2:0x8fd]),
		},
		"nation_art_open_step": openedAt, "opened": d.Opened,
		"read_count": readCount, "read_truncated": readTruncated, "reads": reads,
		"write_count": writeCount, "write_truncated": writeTruncated,
		"write_sites": sites, "writes": writes, "snapshots": snaps,
		"state": map[string]any{
			"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks,
			"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP,
			"flags": m.CPU.Flags, "memory_sha256": digest(m.Mem),
			"indexed_sha256": digest(m.Indexed()), "palette_sha256": digest(m.DAC[:]),
			"canvas_sha256": digest(m.Mem[canvas : canvas+64000]),
		},
		"limitations": "候選檔案字串與上下紅字區讀寫；尚未閉合檔案載入至 RAM 的來源邊",
	}
	b, err := json.MarshalIndent(result, "", "  ")
	must(err)
	must(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	must(os.WriteFile(*out+".final.idx", m.Indexed(), 0644))
	must(os.WriteFile(*out+".final.pal", m.DAC[:], 0644))
	fmt.Printf("國家圖步 %d；讀取 %d、兩區寫入 %d；收據 %s\n",
		openedAt, readCount, writeCount, *out+".json")
}
