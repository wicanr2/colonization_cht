// 目標140可丟棄探針：以目標136真 GUI 錄下的選國輸入，觀測其餘三張旗卡的原版讀字、改色與畫布。
// 原版只讀；原始畫布、事件與完整狀態只存 workplace。
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

type input140 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replay140 struct {
	Inputs []input140 `json:"inputs"`
	End    uint64     `json:"end"`
}

func must140(err error) {
	if err != nil {
		panic(err)
	}
}
func file140(path string) []byte { b, err := os.ReadFile(path); must140(err); return b }
func sha140(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "唯讀原版目錄")
	inputs := flag.String("inputs", "", "目標136真 GUI 錄下的選國輸入")
	nation := flag.String("nation", "", "france/spain/netherlands")
	out := flag.String("out", "", "workplace 內輸出前綴")
	control := flag.Bool("control", false, "無讀寫監看的同輸入控制")
	flag.Parse()
	wantInputs := map[string]string{
		"france":      "f0b2b0f420a78a1e7a806719babdc9afd6c7ced1b1320f9a5ae3279f878bf237",
		"spain":       "77636ce47ee1effc31a7913d6ab92bd7577195296315755f6e2a97ce59c9bd3a",
		"netherlands": "79040af9bb6e25720cb38407f89bb2ce45d52ad0056ff8b70478fe00778d1ec0",
	}
	if *inputs == "" || *out == "" || wantInputs[*nation] == "" {
		panic("必須指定 inputs、nation 與 out")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must140(err)
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
		if sha140(file140(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputBytes := file140(*inputs)
	if sha140(inputBytes) != wantInputs[*nation] {
		panic("輸入收據版本不符")
	}
	var replay replay140
	must140(json.Unmarshal(inputBytes, &replay))
	m := golem.New()
	must140(m.LoadEXE(file140(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	// 44.6M 按下目標旗卡、45.2M 放開；46.0M 起才移向完成提示，窗口不含離頁。
	const start, stop uint64 = 44100000, 46000000
	events := []map[string]any{}
	record := func(e map[string]any) {
		if len(events) >= 200000 {
			panic("事件超出記錄上限")
		}
		events = append(events, e)
	}
	snapshots := map[string]any{}
	lastSource := uint64(0)
	if !*control {
		m.WatchReads(0x20000, 0x4ffff, func(a uint32, value uint8) {
			if m.Steps < start || m.Steps >= stop {
				return
			}
			cs, ip := m.CPU.OpAddr()
			switch {
			case cs == 0x0e2d && ip == 0x11cf && 0x4c000 <= a && a < 0x4e000:
				// 來源字串開始讀取時存印前畫布，與正式前端擷取底圖的時點相同。
				if m.Steps-lastSource > 1000 {
					label := fmt.Sprintf("source-%d", m.Steps)
					b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
					must140(os.WriteFile(*out+"."+label+".canvas", b, 0644))
					snapshots[label] = sha140(b)
				}
				lastSource = m.Steps
				record(map[string]any{"k": "src", "s": m.Steps, "a": a, "v": value})
			case cs == 0x0d21 && ip == 0x00c6:
				c := m.CPU
				record(map[string]any{"k": "fmt", "s": m.Steps, "a": a, "v": value,
					"op": uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])})
			}
		})
		m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, value uint8) {
			if m.Steps < start || m.Steps >= stop || old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			i := int(a - canvas)
			record(map[string]any{"k": "w", "s": m.Steps, "x": i % 320, "y": i / 320, "o": old, "v": value,
				"site": fmt.Sprintf("%04X:%04X", cs, ip)})
		})
	}
	advance := func(target uint64) {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			must140(m.Step())
		}
		if m.Steps != target {
			panic("原版提前結束")
		}
	}
	previous := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("非法輸入收據")
		}
		if e.Step >= stop {
			break
		}
		advance(e.Step)
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
		previous = e.Step
	}
	advance(stop)
	final := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
	must140(os.WriteFile(*out+".final.canvas", final, 0644))
	must140(os.WriteFile(*out+".final.idx", m.Indexed(), 0644))
	must140(os.WriteFile(*out+".final.pal", m.DAC[:], 0644))
	state := map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks,
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
		"memory_sha256": sha140(m.Mem), "indexed_sha256": sha140(m.Indexed()),
		"palette_sha256": sha140(m.DAC[:]), "canvas_sha256": sha140(final)}
	result := map[string]any{"version": "goal140-nation-cards-v1", "nation": *nation, "control": *control,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas; file offsets",
		"input_sha256":  sha140(inputBytes), "input_hashes": wants, "window": []uint64{start, stop},
		"events": events, "snapshots": snapshots, "opened": d.Opened, "state": state}
	b, err := json.Marshal(result)
	must140(err)
	must140(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("%s：事件 %d、狀態 %s\n", *nation, len(events), state["memory_sha256"])
}
