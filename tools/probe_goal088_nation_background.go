// 目標088可丟棄探針：第一張旗卡兩行實際印字前後畫布；原版檔案唯讀。
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type event088 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replay088 struct {
	Inputs []event088 `json:"inputs"`
	End    uint64     `json:"end"`
}

func must088(err error) {
	if err != nil {
		panic(err)
	}
}
func read088(path string) []byte {
	b, err := os.ReadFile(path)
	must088(err)
	return b
}
func sha088(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀目錄")
	inputs := flag.String("inputs", "", "已驗16筆真視窗輸入")
	out := flag.String("out", "", "只留 workplace 的輸出前綴")
	control := flag.Bool("control", false, "不註冊畫布寫入監看器")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("需明示 -inputs 與 -out")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must088(err)
	owner, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
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
		if sha088(read088(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := read088(*inputs)
	if sha088(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("真視窗輸入指紋不符")
	}
	var replay replay088
	must088(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("真視窗輸入結構不符")
	}
	m := golem.New()
	must088(m.LoadEXE(read088(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	const end uint64 = 43000000
	snapSteps := map[uint64]string{
		42860474: "before-upper",
		42867603: "after-upper",
		42871144: "before-lower",
		42880764: "after-lower",
		43000000: "settled",
	}
	snapshots := map[string]map[string]any{}
	counts := map[string]int{"upper": 0, "lower": 0}
	if !*control {
		m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, value uint8) {
			if old == value || m.Steps < 42860474 || m.Steps > 42880763 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if cs != 0x0d21 || ip != 0x012c {
				return
			}
			i := a - canvas
			x, y := i%320, i/320
			if x >= 125 && x < 190 && y >= 12 && y < 25 {
				counts["upper"]++
			} else if x >= 125 && x < 190 && y >= 83 && y < 96 {
				counts["lower"]++
			}
		})
	}
	snapshot := func(name string) {
		frame := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
		indexed := m.Indexed()
		must088(os.WriteFile(*out+"."+name+".canvas", frame, 0644))
		must088(os.WriteFile(*out+"."+name+".idx", indexed, 0644))
		snapshots[name] = map[string]any{"step": m.Steps,
			"canvas_sha256": sha088(frame), "indexed_sha256": sha088(indexed)}
	}
	step := func() {
		if name, ok := snapSteps[m.Steps]; ok && name != "settled" {
			snapshot(name)
		}
		must088(m.Step())
	}
	advance := func(target uint64) {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			step()
		}
		if m.Steps != target {
			panic("原版未抵達固定步數")
		}
	}
	apply := func(e event088) {
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
			panic("非法真視窗事件")
		}
	}
	var previous uint64
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > replay.End || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("非法真視窗輸入收據")
		}
		if e.Step > end {
			break
		}
		advance(e.Step)
		apply(e)
		previous = e.Step
	}
	for m.Steps < end {
		step()
	}
	snapshot("settled")
	if len(snapshots) != 5 {
		panic("固定快照不完整")
	}
	if !*control && (counts["upper"] != 144 || counts["lower"] != 172) {
		panic("原版旗卡印字點數不符")
	}
	must088(os.WriteFile(*out+".final.pal", m.DAC[:], 0644))
	result := map[string]any{"version": "goal088-nation-background-v1", "control": *control,
		"input_sha256": sha088(inputData), "input_hashes": wants, "opened": d.Opened,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas",
		"snapshots":     snapshots, "write_counts": counts,
		"state": map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags,
			"memory_sha256": sha088(m.Mem), "indexed_sha256": sha088(m.Indexed()),
			"palette_sha256": sha088(m.DAC[:])}}
	b, err := json.MarshalIndent(result, "", "  ")
	must088(err)
	must088(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("第一張旗卡上下印字點數 %d／%d；RAM %s\n",
		counts["upper"], counts["lower"], sha088(m.Mem))
}
