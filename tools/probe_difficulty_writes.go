// 一次性唯讀探針：重播真視窗輸入，觀測難度標題區的畫布寫入與原文讀取。
// 本檔是研究工具，不是顯示層；任何定位結果均須先經規格審查。
package main

import (
	"crypto/sha256"
	"encoding/hex"
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
type receipt struct {
	Inputs []input `json:"inputs"`
	End    uint64  `json:"end"`
}
type site struct {
	Address   string `json:"address"`
	Count     int    `json:"count"`
	FirstStep uint64 `json:"first_step"`
	LastStep  uint64 `json:"last_step"`
	MinX      int    `json:"min_x"`
	MinY      int    `json:"min_y"`
	MaxX      int    `json:"max_x"`
	MaxY      int    `json:"max_y"`
}
type hit struct {
	Step    uint64 `json:"step"`
	Address string `json:"address"`
	Linear  uint32 `json:"linear"`
	X       int    `json:"x,omitempty"`
	Y       int    `json:"y,omitempty"`
	Old     uint8  `json:"old,omitempty"`
	New     uint8  `json:"new,omitempty"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte { b, e := os.ReadFile(path); must(e); return b }
func sha(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func main() {
	root := flag.String("root", "/game", "原版唯讀目錄")
	inputs := flag.String("inputs", "/out/goal059-ebiten.inputs.json", "既有正常玩家輸入收據")
	out := flag.String("out", "/out/goal061-difficulty-writes.json", "研究收據")
	end := flag.Uint64("end", 40000000, "執行上限")
	flag.Parse()
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	}
	for name, want := range wants {
		if sha(read(*root+"/"+name)) != want {
			panic("原版版本不符：" + name)
		}
	}
	var replay receipt
	must(json.Unmarshal(read(*inputs), &replay))
	m := golem.New()
	must(m.LoadEXE(read(*root + "/OPENING.EXE")))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas = 0x2cae0
	writeSites := map[string]*site{}
	readSites := map[string]int{}
	firstWrites := []hit{}
	firstReads := []hit{}
	textWrites := []hit{}
	readContext := []map[string]any{}
	checkpoints := map[string]map[string]any{}
	snapSteps := map[uint64]string{29757000: "choose-before", 29763000: "choose-after", 29765000: "level-before", 29777000: "level-after", 29779550: "finish-before", 29791000: "finish-after", 30000000: "settled"}
	address := func() string { cs, ip := m.CPU.OpAddr(); return fmt.Sprintf("%04X:%04X", cs, ip) }
	m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, new uint8) {
		if m.Steps < 28000000 {
			return
		}
		i := int(a - canvas)
		x, y := i%320, i/320
		// 難度頁標題、完成提示；由真視窗截圖的 4 倍座標換算，
		// 僅作研究觀測區，不是最後的文字安全矩形。
		if !((x >= 18 && x < 105 && y >= 12 && y < 41) || (x >= 10 && x < 112 && y >= 76 && y < 89)) {
			return
		}
		key := address()
		s := writeSites[key]
		if s == nil {
			s = &site{Address: key, FirstStep: m.Steps, MinX: x, MinY: y, MaxX: x, MaxY: y}
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
		if len(firstWrites) < 120 {
			firstWrites = append(firstWrites, hit{Step: m.Steps, Address: key, Linear: a, X: x, Y: y, Old: old, New: new})
		}
		if key == "0D21:012C" && len(textWrites) < 2000 {
			textWrites = append(textWrites, hit{Step: m.Steps, Address: key, Linear: a, X: x, Y: y, Old: old, New: new})
		}
	})
	// 目標014結束快照的線性字串候選；讀取命中不單獨證明印字。
	m.WatchReads(0x4df59, 0x4df8f, func(a uint32, _ uint8) {
		if m.Steps < 28000000 {
			return
		}
		key := address()
		readSites[key]++
		if len(firstReads) < 1000 {
			firstReads = append(firstReads, hit{Step: m.Steps, Address: key, Linear: a})
		}
		if (a == 0x4df59 || a == 0x4df72 || a == 0x4df79) && len(readContext) < 40 {
			sp, ss := m.CPU.R[golem.SP], m.CPU.Seg[golem.SS]
			base := uint32(ss)*16 + uint32(sp)
			readContext = append(readContext, map[string]any{"step": m.Steps, "address": key, "linear": a, "registers": m.CPU.R, "segments": m.CPU.Seg, "stack_hex": hex.EncodeToString(m.Mem[base : base+32])})
		}
	})
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
			panic("未知輸入：" + e.Kind)
		}
	}
	step := func() {
		must(m.Step())
		if name, ok := snapSteps[m.Steps]; ok {
			stem := strings.TrimSuffix(*out, filepath.Ext(*out)) + "." + name
			canvasBytes := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
			indexed := m.Indexed()
			must(os.WriteFile(stem+".canvas", canvasBytes, 0644))
			must(os.WriteFile(stem+".idx", indexed, 0644))
			checkpoints[name] = map[string]any{"step": m.Steps, "canvas_sha256": sha(canvasBytes), "indexed_sha256": sha(indexed), "canvas_file": stem + ".canvas", "indexed_file": stem + ".idx"}
		}
	}
	var previous uint64
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > *end || e.Button < 0 || e.Button > 2 || (e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("無效輸入收據")
		}
		for m.Steps < e.Step {
			step()
		}
		apply(e)
		previous = e.Step
	}
	for m.Steps < *end && !d.Exited && !m.CPU.Halted {
		step()
	}
	opened := false
	for _, v := range d.Opened {
		if strings.EqualFold(v, "DIFFICUL.PIK") {
			opened = true
		}
	}
	result := map[string]any{"end": m.Steps, "exited": d.Exited, "difficulty_art_opened": opened,
		"input_sha256": sha(read(*inputs)), "input_hashes": wants,
		"memory_sha256": sha(m.Mem), "indexed_sha256": sha(m.Indexed()), "palette_sha256": sha(m.DAC[:]),
		"canvas_sha256": sha(m.Mem[canvas : canvas+64000]), "write_sites": writeSites, "read_sites": readSites,
		"first_writes": firstWrites, "first_reads": firstReads, "text_writes": textWrites,
		"read_context":  readContext,
		"checkpoints":   checkpoints,
		"address_space": "DOS real-mode CS:IP for sites; DOS 20-bit linear for observed memory; 320x200 logical canvas for x/y",
		"limitations":   "觀測區不是安全矩形；讀字串與畫布寫入仍需連結同一輸出事件；不代表已可正式覆蓋"}
	b, e := json.MarshalIndent(result, "", "  ")
	must(e)
	must(os.WriteFile(*out, append(b, '\n'), 0644))
	fmt.Printf("結束 %d 步；畫布寫入位置 %d；原文讀取位置 %d；難度圖檔 %t\n", m.Steps, len(writeSites), len(readSites), opened)
}
