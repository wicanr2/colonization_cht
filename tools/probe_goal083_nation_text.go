// 目標083可丟棄只讀探針：難度完成後國家選擇頁的候選原文讀取與畫布寫入。
// 原版 bytes 與快照只輸出至本機 workplace；本工具不修改 DOS 原版或正式顯示層。
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

type replayInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replayFile struct {
	Inputs []replayInput `json:"inputs"`
	End    uint64        `json:"end"`
}
type readEvent struct {
	Step     uint64    `json:"step"`
	Site     string    `json:"site"`
	Linear   uint32    `json:"linear"`
	Value    uint8     `json:"value"`
	Regs     [8]uint16 `json:"regs"`
	Segments [4]uint16 `json:"segments"`
}
type writeEvent struct {
	Step   uint64 `json:"step"`
	Site   string `json:"site"`
	Linear uint32 `json:"linear"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Old    uint8  `json:"old"`
	Value  uint8  `json:"value"`
}
type writeSite struct {
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
func hash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "唯讀合法 DOS 原版")
	inputs := flag.String("inputs", "", "固定正常玩家輸入")
	out := flag.String("out", "", "本機輸出前綴")
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
	}
	for name, want := range wants {
		if hash(read(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	labels := read(filepath.Join(*root, "LABELS.TXT"))
	if string(labels[0x8d3:0x8d9]) != "Select" || string(labels[0x8db:0x8e9]) != "European Power" {
		panic("LABELS.TXT 候選原文字節不符")
	}
	inputData := read(*inputs)
	var replay replayFile
	must(json.Unmarshal(inputData, &replay))
	if replay.End < 60000000 || len(replay.Inputs) < 16 {
		panic("難度完成輸入不足")
	}
	last := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step < last || e.Step > replay.End || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("無效輸入收據")
		}
		last = e.Step
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
	const sourceSelect uint32 = 0x4dfb5
	const sourcePower uint32 = 0x4dfbc
	snapSteps := map[uint64]string{
		40000000: "before-move", 41000000: "before-press",
		42000000: "before-release", 43000000: "before-away",
		42628840: "before-select-source", 42633550: "after-select-ink",
		42636530: "before-power-source", 42648000: "after-power-ink",
		44000000: "after-click", 46000000: "settled-46m",
		50000000: "settled-50m", 60000000: "settled-60m",
		62000000: "cursor-hover", 66000000: "cursor-away",
		70000000: "post-f1-70m", 75000000: "post-f1-75m",
	}
	snapshots := map[string]map[string]string{}
	reads := []readEvent{}
	writes := []writeEvent{}
	readCount := map[string]int{"source": 0, "display": 0}
	writeCounts := map[string]int{}
	writeSites := map[string]*writeSite{}
	readTruncated, writeTruncated := false, false
	nationOpenedAt := uint64(0)
	start := uint64(40000000)
	stop := uint64(50000000)
	m.WatchReads(0x2a000, 0x4dfce, func(a uint32, value uint8) {
		if m.Steps < start || m.Steps > stop {
			return
		}
		cs, ip := m.CPU.OpAddr()
		group := ""
		if a >= sourceSelect && a <= sourceSelect+6 || a >= sourcePower && a <= sourcePower+14 {
			group = "source"
		} else if cs == 0x0d21 && ip == 0x00c6 {
			group = "display"
		}
		if group == "" {
			return
		}
		readCount[group]++
		if len(reads) >= 16000 {
			readTruncated = true
			return
		}
		reads = append(reads, readEvent{Step: m.Steps, Site: fmt.Sprintf("%04X:%04X", cs, ip),
			Linear: a, Value: value, Regs: m.CPU.R, Segments: m.CPU.Seg})
	})
	m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, value uint8) {
		if m.Steps < start || m.Steps > stop || old == value {
			return
		}
		i := int(a - canvas)
		x, y := i%320, i/320
		if !(x >= 12 && x < 108 && y >= 30 && y < 65) {
			return
		}
		cs, ip := m.CPU.OpAddr()
		key := fmt.Sprintf("%04X:%04X", cs, ip)
		writeCounts[key]++
		s := writeSites[key]
		if s == nil {
			s = &writeSite{FirstStep: m.Steps, MinX: x, MinY: y, MaxX: x, MaxY: y}
			writeSites[key] = s
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
		if len(writes) >= 20000 {
			writeTruncated = true
			return
		}
		writes = append(writes, writeEvent{Step: m.Steps, Site: key, Linear: a,
			X: x, Y: y, Old: old, Value: value})
	})
	step := func() {
		if name, ok := snapSteps[m.Steps]; ok {
			b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
			idx := m.Indexed()
			must(os.WriteFile(*out+"."+name+".canvas", b, 0644))
			must(os.WriteFile(*out+"."+name+".idx", idx, 0644))
			snapshots[name] = map[string]string{"canvas_sha256": hash(b), "indexed_sha256": hash(idx)}
		}
		must(m.Step())
		if nationOpenedAt == 0 && len(d.Opened) > 0 && strings.EqualFold(d.Opened[len(d.Opened)-1], "NATIONS.PIK") {
			nationOpenedAt = m.Steps
		}
	}
	apply := func(e replayInput) {
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		case "f1":
			d.PushKey(golem.Key{Scan: 0x3b, ASCII: 0})
		default:
			panic("未知輸入種類")
		}
	}
	for _, e := range replay.Inputs {
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			step()
		}
		if d.Exited || m.CPU.Halted {
			panic("輸入前原版提前結束")
		}
		apply(e)
	}
	for m.Steps < replay.End && !d.Exited && !m.CPU.Halted {
		step()
	}
	if m.Steps != replay.End {
		panic("原版未到達指定終點")
	}
	result := map[string]any{
		"version":      "goal083-nation-text-probe-v1",
		"input_sha256": hash(inputData), "input_hashes": wants,
		"tool_address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas",
		"labels_source": map[string]any{
			"select_file_offset": "0x8D3", "select_hex": fmt.Sprintf("%x", labels[0x8d3:0x8d9]),
			"power_file_offset": "0x8DB", "power_hex": fmt.Sprintf("%x", labels[0x8db:0x8e9]),
		},
		"candidate_ram": map[string]any{
			"select_linear": fmt.Sprintf("0x%X", sourceSelect),
			"select_hex":    fmt.Sprintf("%x", m.Mem[sourceSelect:sourceSelect+7]),
			"power_linear":  fmt.Sprintf("0x%X", sourcePower),
			"power_hex":     fmt.Sprintf("%x", m.Mem[sourcePower:sourcePower+15]),
		},
		"nation_art_open_step": nationOpenedAt, "opened": d.Opened,
		"read_counts": readCount, "read_truncated": readTruncated, "reads": reads,
		"write_counts": writeCounts, "write_sites": writeSites,
		"write_truncated": writeTruncated, "writes": writes,
		"snapshots": snapshots,
		"state": map[string]any{
			"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks,
			"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP,
			"flags": m.CPU.Flags, "memory_sha256": hash(m.Mem),
			"indexed_sha256": hash(m.Indexed()), "palette_sha256": hash(m.DAC[:]),
			"canvas_sha256": hash(m.Mem[canvas : canvas+64000]),
		},
		"limitations": "候選來源與標題區讀寫收據；未單獨閉合每行畫布差分、當次底圖或正式覆蓋鍵",
	}
	b, err := json.MarshalIndent(result, "", "  ")
	must(err)
	must(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	must(os.WriteFile(*out+".final.idx", m.Indexed(), 0644))
	must(os.WriteFile(*out+".final.pal", m.DAC[:], 0644))
	fmt.Printf("國家圖開檔步 %d；來源讀取 %d、顯示讀取 %d、標題區寫入 %d\n",
		nationOpenedAt, readCount["source"], readCount["display"], len(writes))
}
