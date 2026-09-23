// 目標089可丟棄探針：第一張國家旗卡的原版游標／按鍵狀態。
// 不修改原版記憶體或畫布；原始像素與報告只寫入 workplace。
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

type event089 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}

type replay089 struct {
	Inputs []event089 `json:"inputs"`
	End    uint64     `json:"end"`
}

var safes089 = map[string][4]int{
	"upper": {125, 12, 190, 24},
	"lower": {125, 83, 190, 96},
}

func must089(err error) {
	if err != nil {
		panic(err)
	}
}

func read089(path string) []byte {
	data, err := os.ReadFile(path)
	must089(err)
	return data
}

func hash089(data []byte) string { return fmt.Sprintf("%x", sha256.Sum256(data)) }

func diff089(left, right []byte, rect [4]int) int {
	if len(left) != 64000 || len(right) != 64000 {
		panic("原版索引畫面大小不符")
	}
	count := 0
	for y := rect[1]; y < rect[3]; y++ {
		for x := rect[0]; x < rect[2]; x++ {
			i := y*320 + x
			if left[i] != right[i] {
				count++
			}
		}
	}
	return count
}

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀目錄")
	inputs := flag.String("inputs", "", "已驗十六筆真視窗輸入")
	out := flag.String("out", "", "workplace 內的輸出前綴")
	scenario := flag.String("scenario", "hover", "hover、left、right 或 next")
	control := flag.Bool("control", false, "同輸入、無逐幀觀測的控制組")
	flag.Parse()
	if *inputs == "" || *out == "" ||
		(*scenario != "hover" && *scenario != "left" && *scenario != "right" && *scenario != "next") {
		panic("必須指定 inputs、out 與合法 scenario")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must089(err)
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
		if hash089(read089(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := read089(*inputs)
	if hash089(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("真視窗輸入指紋不符")
	}
	var replay replay089
	must089(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("真視窗輸入結構不符")
	}
	m := golem.New()
	must089(m.LoadEXE(read089(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	var baseline []byte
	frames := make([]map[string]any, 0)
	if !*control {
		m.SetOnFrame(func() {
			if baseline == nil || len(frames) >= 160 {
				return
			}
			indexed := m.Indexed()
			intersections := map[string]int{}
			for name, safe := range safes089 {
				intersections[name] = diff089(baseline, indexed, safe)
			}
			frames = append(frames, map[string]any{
				"step": m.Steps, "mouse": [3]uint16{d.Mouse.X, d.Mouse.Y, d.Mouse.Buttons},
				"indexed_sha256": hash089(indexed), "canvas_sha256": hash089(m.Mem[canvas : canvas+64000]),
				"intersections": intersections,
			})
		})
	}
	advance := func(target uint64) bool {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			must089(m.Step())
		}
		return m.Steps == target
	}
	apply := func(e event089) {
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
	previous := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > replay.End || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("非法真視窗輸入收據")
		}
		if e.Step > 43000000 {
			break
		}
		if !advance(e.Step) {
			panic("抵達旗卡前原版提前退出")
		}
		apply(e)
		previous = e.Step
	}
	if !advance(43000000) {
		panic("未抵達第一張旗卡")
	}
	baseline = append([]byte(nil), m.Indexed()...)
	if hash089(baseline) != "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" ||
		hash089(m.Mem[canvas:canvas+64000]) != "2e005b93f811c7e0eb557eb68d1f5c1721caf027e5f32220c3c62195e7c9100b" {
		panic("第一張旗卡基準與目標088不同")
	}
	samples := map[string]map[string]any{}
	snapshot := func(name string) {
		indexed := m.Indexed()
		picture := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
		must089(os.WriteFile(*out+"."+name+".idx", indexed, 0644))
		must089(os.WriteFile(*out+"."+name+".canvas", picture, 0644))
		intersections := map[string]int{}
		for field, safe := range safes089 {
			intersections[field] = diff089(baseline, indexed, safe)
		}
		samples[name] = map[string]any{
			"step": m.Steps, "mouse": [3]uint16{d.Mouse.X, d.Mouse.Y, d.Mouse.Buttons},
			"video_mode": m.VideoMode(), "exited": d.Exited, "halted": m.CPU.Halted,
			"memory_sha256": hash089(m.Mem), "canvas_sha256": hash089(picture),
			"indexed_sha256": hash089(indexed), "palette_sha256": hash089(m.DAC[:]),
			"cycles": m.CPU.Cycles, "ticks": m.Ticks, "registers": m.CPU.R,
			"segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
			"intersections": intersections, "opened_count": len(d.Opened),
		}
	}
	snapshot("settled")
	type action struct {
		at, end uint64
		name    string
		kind    string
		x, y    int
	}
	actions := []action{{43000000, 44000000, "upper", "move", 156, 18},
		{44000000, 45000000, "lower", "move", 156, 90},
		{45000000, 46000000, "away", "move", 16, 16}}
	if *scenario != "hover" {
		actions = []action{{43000000, 44000000, "lower", "move", 156, 90},
			{44000000, 45000000, "pressed", "press", 0, 0},
			{45000000, 46000000, "released", "release", 0, 0}}
	}
	if *scenario == "next" {
		// 相鄰右上旗卡的可見中央；不是推測其文字鍵或玩家意義。
		actions[0] = action{43000000, 44000000, "neighbor", "move", 255, 50}
	}
	button := 0 // dosgolem：0=左鍵、1=右鍵；對照原16筆玩家輸入固定使用0。
	if *scenario == "right" {
		button = 1
	}
	for _, a := range actions {
		if m.Steps != a.at {
			panic("測試步數不連續")
		}
		switch a.kind {
		case "move":
			d.MoveMouse(a.x, a.y)
		case "press":
			d.PressMouse(button)
		case "release":
			d.ReleaseMouse(button)
		}
		reached := advance(a.end)
		snapshot(a.name)
		if !reached {
			break
		}
	}
	state := map[string]any{
		"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks,
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP,
		"flags": m.CPU.Flags, "memory_sha256": hash089(m.Mem),
		"indexed_sha256": hash089(m.Indexed()), "palette_sha256": hash089(m.DAC[:]),
		"canvas_sha256": hash089(m.Mem[canvas : canvas+64000]),
		"exited":        d.Exited, "halted": m.CPU.Halted,
	}
	report := map[string]any{
		"version": "goal089-nation-runtime-v2", "scenario": *scenario,
		"control": *control, "input_sha256": hash089(inputData),
		"input_hashes": wants, "baseline_indexed_sha256": hash089(baseline),
		"samples": samples, "frames": frames, "state": state, "opened": d.Opened,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas",
	}
	data, err := json.MarshalIndent(report, "", "  ")
	must089(err)
	must089(os.WriteFile(*out+".json", append(data, '\n'), 0644))
	fmt.Printf("scenario=%s control=%v samples=%d frames=%d end=%d\n",
		*scenario, *control, len(samples), len(frames), m.Steps)
}
