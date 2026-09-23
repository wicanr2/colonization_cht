// 目標092：右上相鄰旗卡的原版游標、換卡與可見完成提示輸入。
// 僅正常玩家滑鼠事件；原版唯讀，原始畫布與 RAM 指紋只留 workplace。
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

type event092 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replay092 struct {
	Inputs []event092 `json:"inputs"`
	End    uint64     `json:"end"`
}
type action092 struct {
	At, End uint64
	Name    string
	Kind    string
	X, Y    int
}

var safes092 = map[string][4]int{
	"upper": {225, 12, 290, 24},
	"lower": {225, 83, 290, 96},
}

func must092(err error) {
	if err != nil {
		panic(err)
	}
}
func read092(path string) []byte {
	b, err := os.ReadFile(path)
	must092(err)
	return b
}
func sha092(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func diff092(left, right []byte, rect [4]int) int {
	if len(left) != 64000 || len(right) != 64000 {
		panic("索引畫面大小不符")
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
	out := flag.String("out", "", "workplace 內輸出前綴")
	scenario := flag.String("scenario", "hover", "hover、press、back 或 finish")
	control := flag.Bool("control", false, "同輸入、無逐幀觀測的控制組")
	flag.Parse()
	if *inputs == "" || *out == "" ||
		(*scenario != "hover" && *scenario != "press" && *scenario != "back" && *scenario != "finish") {
		panic("必須指定 inputs、out 與合法 scenario")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must092(err)
	owner, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
		panic("輸出目錄不存在或擁有者不符")
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
		if sha092(read092(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := read092(*inputs)
	if sha092(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("真視窗輸入指紋不符")
	}
	var replay replay092
	must092(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("真視窗輸入結構不符")
	}
	m := golem.New()
	must092(m.LoadEXE(read092(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	var baseline []byte
	frames := make([]map[string]any, 0)
	intersections := func(indexed []byte) map[string]int {
		out := map[string]int{}
		for name, safe := range safes092 {
			out[name] = diff092(baseline, indexed, safe)
		}
		return out
	}
	if !*control {
		m.SetOnFrame(func() {
			if baseline == nil || len(frames) >= 160 {
				return
			}
			indexed := m.Indexed()
			frames = append(frames, map[string]any{
				"step": m.Steps, "mouse": [3]uint16{d.Mouse.X, d.Mouse.Y, d.Mouse.Buttons},
				"indexed_sha256": sha092(indexed),
				"canvas_sha256":  sha092(m.Mem[canvas : canvas+64000]),
				"intersections":  intersections(indexed), "opened_count": len(d.Opened),
			})
		})
	}
	advance := func(target uint64) bool {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			must092(m.Step())
		}
		return m.Steps == target
	}
	apply := func(e event092) {
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
		if e.Step > 43000000 {
			break
		}
		if !advance(e.Step) {
			panic("原版提前退出")
		}
		apply(e)
		previous = e.Step
	}
	if !advance(43000000) || sha092(m.Indexed()) !=
		"48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" {
		panic("第一張旗卡基準不符")
	}
	d.MoveMouse(255, 50)
	if !advance(44000000) {
		panic("未抵達右卡左鍵前")
	}
	d.PressMouse(0)
	if !advance(45000000) {
		panic("未抵達右卡左鍵後")
	}
	d.ReleaseMouse(0)
	if !advance(46000000) {
		panic("未抵達右卡放開後")
	}
	baseline = append([]byte(nil), m.Indexed()...)
	if sha092(baseline) != "c867bee2f4c5b7a0af07415d68bccb8d028c905fba53d830b01bfb300672af74" ||
		sha092(m.Mem[canvas:canvas+64000]) != "9e2be3fc35e842afbb03b128a7fedce353f3874d60f0c2101de79b75a366a87b" ||
		sha092(m.Mem) != "935404090ebaa9326051ce5c9fc29a289f5c09f4ce55b21608116523262d5349" {
		panic("右側旗卡基準與目標089／091不同")
	}
	samples := map[string]map[string]any{}
	snapshot := func(name string) {
		indexed := m.Indexed()
		picture := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
		must092(os.WriteFile(*out+"."+name+".idx", indexed, 0644))
		must092(os.WriteFile(*out+"."+name+".canvas", picture, 0644))
		must092(os.WriteFile(*out+"."+name+".pal", m.DAC[:], 0644))
		samples[name] = map[string]any{
			"step": m.Steps, "mouse": [3]uint16{d.Mouse.X, d.Mouse.Y, d.Mouse.Buttons},
			"video_mode": m.VideoMode(), "exited": d.Exited, "halted": m.CPU.Halted,
			"memory_sha256": sha092(m.Mem), "canvas_sha256": sha092(picture),
			"indexed_sha256": sha092(indexed), "palette_sha256": sha092(m.DAC[:]),
			"cycles": m.CPU.Cycles, "ticks": m.Ticks, "registers": m.CPU.R,
			"segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
			"intersections": intersections(indexed), "opened_count": len(d.Opened),
		}
	}
	snapshot("base")
	actions := []action092{{46000000, 47000000, "upper", "move", 255, 18},
		{47000000, 48000000, "lower", "move", 255, 90},
		{48000000, 49000000, "away", "move", 16, 16}}
	if *scenario != "hover" {
		actions = []action092{{46000000, 47000000, "target", "move", 255, 50},
			{47000000, 48000000, "pressed", "press", 0, 0},
			{48000000, 49000000, "released", "release", 0, 0}}
	}
	if *scenario == "back" {
		actions[0] = action092{46000000, 47000000, "target", "move", 156, 50}
	}
	if *scenario == "finish" {
		// 原版畫面左下可見「Click here when finished」；座標在提示字範圍內。
		actions = []action092{{46000000, 47000000, "target", "move", 65, 184},
			{47000000, 48000000, "pressed", "press", 0, 0},
			{48000000, 49000000, "released", "release", 0, 0},
			{49000000, 55000000, "settled", "wait", 0, 0}}
	}
	for _, a := range actions {
		if m.Steps != a.At {
			panic("測試步數不連續")
		}
		switch a.Kind {
		case "move":
			d.MoveMouse(a.X, a.Y)
		case "press":
			d.PressMouse(0)
		case "release":
			d.ReleaseMouse(0)
		case "wait":
		default:
			panic("非法探針動作")
		}
		reached := advance(a.End)
		snapshot(a.Name)
		if !reached {
			break
		}
	}
	state := map[string]any{
		"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks,
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP,
		"flags": m.CPU.Flags, "memory_sha256": sha092(m.Mem),
		"indexed_sha256": sha092(m.Indexed()), "palette_sha256": sha092(m.DAC[:]),
		"canvas_sha256": sha092(m.Mem[canvas : canvas+64000]),
		"exited":        d.Exited, "halted": m.CPU.Halted,
	}
	report := map[string]any{
		"version": "goal092-neighbor-runtime-v1", "scenario": *scenario,
		"control": *control, "input_sha256": sha092(inputData),
		"input_hashes": wants, "baseline_indexed_sha256": sha092(baseline),
		"samples": samples, "frames": frames, "state": state, "opened": d.Opened,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas",
	}
	data, err := json.MarshalIndent(report, "", "  ")
	must092(err)
	must092(os.WriteFile(*out+".json", append(data, '\n'), 0644))
	fmt.Printf("scenario=%s control=%v samples=%d frames=%d end=%d opened=%d\n",
		*scenario, *control, len(samples), len(frames), m.Steps, len(d.Opened))
}
