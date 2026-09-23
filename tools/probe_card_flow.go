// 目標075的一次性研究探針：在正常玩家路徑追卡片字串讀取後的窄時間窗。
// 輸出只供本機研究；不改原版，也不授權正式中文覆蓋。
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
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
type receipt struct {
	Inputs []input `json:"inputs"`
	End    uint64  `json:"end"`
}
type event struct {
	Step     uint64    `json:"step"`
	Site     string    `json:"site"`
	Linear   uint32    `json:"linear,omitempty"`
	Old      uint8     `json:"old,omitempty"`
	Value    uint8     `json:"value"`
	Regs     [8]uint16 `json:"regs"`
	Segments [4]uint16 `json:"segments"`
	Code     []byte    `json:"code"`
	Stack    []byte    `json:"stack,omitempty"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte { data, err := os.ReadFile(path); must(err); return data }
func sha(data []byte) string  { return fmt.Sprintf("%x", sha256.Sum256(data)) }

func main() {
	root := flag.String("root", "/game", "唯讀原版根目錄")
	inputs := flag.String("inputs", "/out/goal059-ebiten.inputs.json", "正常玩家輸入收據")
	out := flag.String("out", "/out/goal075-card-flow.json", "本機研究收據")
	flag.Parse()
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	}
	for name, want := range wants {
		if sha(read(*root+"/"+name)) != want {
			panic("原版檔案版本不符：" + name)
		}
	}
	var replay receipt
	must(json.Unmarshal(read(*inputs), &replay))
	const end uint64 = 32000000
	const canvas uint32 = 0x2cae0
	m := golem.New()
	must(m.LoadEXE(read(*root + "/OPENING.EXE")))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	windows := [][2]uint64{{29797540, 29811000}, {29813140, 29819650}}
	inWindow := func(step uint64) bool {
		for _, window := range windows {
			if step >= window[0] && step <= window[1] {
				return true
			}
		}
		return false
	}
	capture := func(linear uint32, old, value uint8, stack bool) event {
		cs, ip := m.CPU.OpAddr()
		pc := uint32(cs)*16 + uint32(ip)
		sp := uint32(m.CPU.Seg[golem.SS])*16 + uint32(m.CPU.R[golem.SP])
		e := event{Step: m.Steps, Site: fmt.Sprintf("%04X:%04X", cs, ip), Linear: linear,
			Old: old, Value: value, Regs: m.CPU.R, Segments: m.CPU.Seg}
		if pc+8 <= uint32(len(m.Mem)) {
			e.Code = append([]byte(nil), m.Mem[pc:pc+8]...)
		}
		if stack && sp+32 <= uint32(len(m.Mem)) {
			e.Stack = append([]byte(nil), m.Mem[sp:sp+32]...)
		}
		return e
	}
	reads := []event{}
	writes := []event{}
	steps := []event{}
	snapshots := map[string][]byte{}
	snapshotSteps := map[uint64]string{29797540: "before-first", 29811000: "after-first", 29813140: "before-second", 29819650: "after-second"}
	writeCount := 0
	const maxWrites = 100000
	watchRead := func() {
		m.WatchReads(0x2a6b0, 0x4df97, func(a uint32, value uint8) {
			if !inWindow(m.Steps) || !((a >= 0x2a6b0 && a <= 0x2a6bb) || (a >= 0x2a74c && a <= 0x2a756) || (a >= 0x4cc6a && a <= 0x4cc74) || (a >= 0x4df90 && a <= 0x4df97)) {
				return
			}
			reads = append(reads, capture(a, 0, value, true))
		})
	}
	watchWrite := func() {
		m.WatchWrites(0, 0xfffff, func(a uint32, old, value uint8) {
			if !inWindow(m.Steps) {
				return
			}
			writeCount++
			if len(writes) < maxWrites {
				writes = append(writes, capture(a, old, value, false))
			}
		})
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
			panic("未知輸入種類：" + e.Kind)
		}
	}
	step := func() {
		if name, ok := snapshotSteps[m.Steps]; ok {
			snapshots[name] = append([]byte(nil), m.Mem[canvas:canvas+64000]...)
		}
		if m.Steps == windows[0][0] || m.Steps == windows[1][0] {
			watchRead()
			watchWrite()
		}
		if m.Steps == windows[0][1]+1 || m.Steps == windows[1][1]+1 {
			m.WatchReads(1, 0, nil)
			m.WatchWrites(1, 0, nil)
		}
		if inWindow(m.Steps) {
			steps = append(steps, capture(0, 0, 0, false))
		}
		must(m.Step())
	}
	var previous uint64
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > end || e.Button < 0 || e.Button > 2 || (e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("無效正常玩家輸入收據")
		}
		for m.Steps < e.Step {
			step()
		}
		apply(e)
		previous = e.Step
	}
	for m.Steps < end && !d.Exited && !m.CPU.Halted {
		step()
	}
	opened := false
	for _, name := range d.Opened {
		opened = opened || strings.EqualFold(name, "DIFFICUL.PIK")
	}
	result := map[string]any{
		"version": "goal075-card-flow-v5", "end": m.Steps, "exited": d.Exited,
		"input_hashes": wants, "input_sha256": sha(read(*inputs)), "difficulty_art_opened": opened,
		"dos_address_space": "real-mode CS:IP and 20-bit linear RAM", "canvas_address_space": "320x200 logical indexed pixels",
		"windows": windows, "reads": reads, "writes": writes, "write_count": writeCount, "snapshots": snapshots,
		"writes_truncated": writeCount > maxWrites, "steps": steps,
		"memory_sha256": sha(m.Mem), "canvas_sha256": sha(m.Mem[canvas : canvas+64000]),
		"indexed_sha256": sha(m.Indexed()), "palette_sha256": sha(m.DAC[:]),
		"limitations": "窄時間窗正常路徑 trace；字串到像素的語意須再由讀寫端與反向條件審查，不是正式覆蓋鍵",
	}
	data, err := json.MarshalIndent(result, "", "  ")
	must(err)
	must(os.WriteFile(*out, append(data, '\n'), 0644))
	fmt.Printf("結束 %d 步；來源讀取 %d；記憶體寫入 %d；指令樣本 %d\n", m.Steps, len(reads), writeCount, len(steps))
}
