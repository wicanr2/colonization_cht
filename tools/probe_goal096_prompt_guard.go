// 目標096：以真視窗輸入重播原版，窄觀測完整提示來源至多色畫布的同一次事件。
// 原版唯讀；報告只含雜湊、位置與有限事件，原始畫布不寫入版控。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type input096 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
	Text   string `json:"text,omitempty"`
}
type receipt096 struct {
	Inputs []input096 `json:"inputs"`
	End    uint64     `json:"end"`
}
type event096 struct {
	Step  uint64 `json:"step"`
	CSIP  string `json:"cs_ip"`
	X     int    `json:"x,omitempty"`
	Y     int    `json:"y,omitempty"`
	Old   uint8  `json:"old,omitempty"`
	New   uint8  `json:"new,omitempty"`
	Value uint8  `json:"value,omitempty"`
}

func must096(err error) {
	if err != nil {
		panic(err)
	}
}
func read096(path string) []byte { b, err := os.ReadFile(path); must096(err); return b }
func sha096(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法原版唯讀目錄")
	inputsPath := flag.String("inputs", "", "目標095真視窗輸入收據")
	out := flag.String("out", "", "已忽略 workplace 輸出前綴")
	control := flag.Bool("control", false, "不安裝原版讀寫／逐指令觀測器")
	flag.Parse()
	if *inputsPath == "" || *out == "" {
		panic("缺少輸入或輸出路徑")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must096(err)
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
		if sha096(read096(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	const visible = "Please Enter Your Name."
	game := read096(filepath.Join(*root, "GAME.TXT"))
	if !bytes.Equal(game[0xa7a:0xa7c], []byte("^^")) ||
		!bytes.Equal(game[0xa7c:0xa7c+len(visible)], []byte(visible)) {
		panic("原始提示控制碼或文字不符")
	}
	inputData := read096(*inputsPath)
	if sha096(inputData) != "d5a0902056911fa13a93f7f5466c27c795d3c12600214ff8be71e2be95ea3fec" {
		panic("真視窗輸入指紋不符")
	}
	var replay receipt096
	must096(json.Unmarshal(inputData, &replay))
	if replay.End != 90000000 || len(replay.Inputs) != 26 {
		panic("真視窗輸入結構不符")
	}
	prev := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step < prev || e.Step > 70000000 {
			panic("真視窗輸入次序或終點不符")
		}
		prev = e.Step
	}
	m := golem.New()
	must096(m.LoadEXE(read096(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	const source uint32 = 0x2b072
	const glyph uint32 = 0x2a864
	safe := func(x, y int) bool { return 100 <= x && x < 219 && 85 <= y && y < 98 }
	safeHash := func() string {
		buf := make([]byte, 0, (219-100)*(98-85))
		for y := 85; y < 98; y++ {
			buf = append(buf, m.Mem[canvas+uint32(y*320+100):canvas+uint32(y*320+219)]...)
		}
		return sha096(buf)
	}
	sourceReads := []map[string]any{}
	glyphReads := []event096{}
	glyphContexts := []map[string]any{}
	writes := []event096{}
	sourceBeforeStep, sourceReadStep, displayStep, firstGlyphStep, afterStep := uint64(0), uint64(0), uint64(0), uint64(0), uint64(0)
	sourceBeforeSteps := []uint64{}
	sourceBeforeEvents := []map[string]any{}
	displayTailByte := uint8(0)
	sourceMatch := false
	var beforeCanvas, afterCanvas []byte
	pendingAfter := false
	if !*control {
		// dosgolem 同一時間只有一個讀取監看器；合併兩個位址，避免後註冊覆蓋前者。
		m.WatchReads(glyph, source+1, func(a uint32, value uint8) {
			if a == source {
				cs, ip := m.CPU.OpAddr()
				if cs != 0x0e2d || ip != 0x09f4 || m.Steps < 40000000 || m.Steps >= 55000000 {
					return
				}
				candidate := m.Mem[source : source+uint32(len(visible)+1)]
				match := bytes.Equal(candidate[:len(visible)], []byte(visible)) && candidate[len(visible)] == '\n'
				sourceReads = append(sourceReads, map[string]any{"step": m.Steps,
					"cs_ip": "0E2D:09F4", "linear": source, "first_value": value,
					"registers": m.CPU.R, "segments": m.CPU.Seg,
					"opcode_hex":       hex.EncodeToString(m.Mem[0x0e2d*16+0x09f4 : 0x0e2d*16+0x09f4+3]),
					"candidate_sha256": sha096(candidate), "matches_full_visible_and_newline": match,
					"candidate_prefix_hex": hex.EncodeToString(candidate),
					"display_prefix_hex":   hex.EncodeToString(m.Mem[0x6f200 : 0x6f200+uint32(len(visible)+1)]),
					"opened_count":         len(d.Opened)})
				if value == 'P' && match {
					sourceReadStep = m.Steps
				}
				return
			}
			if a != glyph {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if !sourceMatch || cs != 0x0d21 || ip != 0x00c6 ||
				m.Steps-displayStep > 120000 || len(glyphReads) >= 80 {
				return
			}
			if firstGlyphStep == 0 {
				firstGlyphStep = m.Steps
				beforeCanvas = bytes.Clone(m.Mem[canvas : canvas+64000])
			}
			glyphReads = append(glyphReads, event096{Step: m.Steps, CSIP: "0D21:00C6", Value: value})
			glyphContexts = append(glyphContexts, map[string]any{"step": m.Steps,
				"registers": m.CPU.R, "segments": m.CPU.Seg,
				"opcode_hex": hex.EncodeToString(m.Mem[0x0d21*16+0x00c6 : 0x0d21*16+0x00c6+3])})
		})
		m.WatchWrites(canvas, canvas+64000, func(a uint32, old, value uint8) {
			if firstGlyphStep == 0 || m.Steps-firstGlyphStep > 120000 || old == value || len(writes) >= 3000 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			i := int(a - canvas)
			writes = append(writes, event096{Step: m.Steps,
				CSIP: fmt.Sprintf("%04X:%04X", cs, ip), X: i % 320, Y: i / 320,
				Old: old, New: value})
			if len(writes) == 415 && cs == 0x0d21 && ip == 0x012c && safe(i%320, i/320) {
				pendingAfter = true
			}
		})
		m.SetBeforeInstruction(func() {
			if m.CPU.Seg[golem.CS] == 0x0e2d && m.CPU.IP == 0x09f4 &&
				uint32(m.CPU.Seg[golem.DS])*16+uint32(m.CPU.R[golem.SI]) == source &&
				bytes.Equal(m.Mem[source:source+uint32(len(visible)+1)], append([]byte(visible), '\n')) {
				if sourceBeforeStep == 0 {
					sourceBeforeStep = m.Steps
				}
				if len(sourceBeforeSteps) < 10 {
					sourceBeforeSteps = append(sourceBeforeSteps, m.Steps)
					sourceBeforeEvents = append(sourceBeforeEvents, map[string]any{
						"step": m.Steps, "opened_count": len(d.Opened),
						"last_opened":        d.Opened[len(d.Opened)-1],
						"canvas_sha256":      sha096(m.Mem[canvas : canvas+64000]),
						"prompt_safe_sha256": safeHash(), "palette_sha256": sha096(m.DAC[:]),
						"video_mode": m.VideoMode()})
				}
			}
			if !sourceMatch && sourceReadStep != 0 &&
				m.Steps-sourceReadStep < 20000 &&
				bytes.Equal(m.Mem[0x6f200:0x6f200+uint32(len(visible))], []byte(visible)) {
				displayStep, sourceMatch = m.Steps, true
				displayTailByte = m.Mem[0x6f200+uint32(len(visible))]
			}
			if pendingAfter && afterStep == 0 {
				afterStep = m.Steps
				afterCanvas = bytes.Clone(m.Mem[canvas : canvas+64000])
				pendingAfter = false
			}
		})
	}
	samples := map[string]map[string]any{}
	sample := func(name string) {
		indexed := m.Indexed()
		picture := m.Mem[canvas : canvas+64000]
		palette := m.DAC[:]
		samples[name] = map[string]any{"step": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags, "memory_sha256": sha096(m.Mem),
			"indexed_sha256": sha096(indexed), "canvas_sha256": sha096(picture),
			"palette_sha256": sha096(palette), "prompt_safe_sha256": safeHash(),
			"opened_count": len(d.Opened), "exited": d.Exited, "halted": m.CPU.Halted,
			"source_matches_prompt":  bytes.Equal(m.Mem[source:source+uint32(len(visible)+1)], append([]byte(visible), '\n')),
			"display_matches_prompt": bytes.Equal(m.Mem[0x6f200:0x6f200+uint32(len(visible))], []byte(visible)),
			"display_tail_byte":      m.Mem[0x6f200+uint32(len(visible))]}
	}
	advance := func(end uint64) {
		for m.Steps < end && !d.Exited && !m.CPU.Halted {
			must096(m.Step())
		}
		if m.Steps != end {
			panic("原版提前停止")
		}
	}
	apply := func(e input096) {
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			if !d.PushKeyNamed("Return") {
				panic("Return 鍵表缺失")
			}
		case "backspace":
			if !d.PushKeyNamed("Backspace") {
				panic("Backspace 鍵表缺失")
			}
		case "text":
			if len(e.Text) != 1 || !d.PushText(e.Text) {
				panic("未驗文字鍵")
			}
		default:
			panic("未知真視窗事件")
		}
	}
	checkpoints := map[uint64]string{55000000: "55m", 58000000: "58m",
		61000000: "61m", 66000000: "66m", 70000000: "70m"}
	times := make([]uint64, 0, len(replay.Inputs)+len(checkpoints))
	for _, e := range replay.Inputs {
		times = append(times, e.Step)
	}
	for step := range checkpoints {
		times = append(times, step)
	}
	sort.Slice(times, func(i, j int) bool { return times[i] < times[j] })
	seen := map[uint64]bool{}
	inputIndex := 0
	for _, step := range times {
		if seen[step] {
			continue
		}
		seen[step] = true
		advance(step)
		if name, ok := checkpoints[step]; ok {
			sample(name)
		}
		for inputIndex < len(replay.Inputs) && replay.Inputs[inputIndex].Step == step {
			apply(replay.Inputs[inputIndex])
			inputIndex++
		}
	}
	advance(70000000)
	if !*control && beforeCanvas != nil && afterCanvas != nil {
		changed, outside := 0, 0
		newColors := map[uint8]int{}
		minX, minY, maxX, maxY := 320, 200, -1, -1
		for i, old := range beforeCanvas {
			if old == afterCanvas[i] {
				continue
			}
			changed++
			x, y := i%320, i/320
			if !safe(x, y) {
				outside++
			}
			if x < minX {
				minX = x
			}
			if y < minY {
				minY = y
			}
			if x > maxX {
				maxX = x
			}
			if y > maxY {
				maxY = y
			}
			newColors[afterCanvas[i]]++
		}
		samples["prompt_diff"] = map[string]any{
			"changed_pixels": changed, "outside_safe": outside,
			"bbox_inclusive": []int{minX, minY, maxX, maxY},
			"new_colors":     newColors, "before_canvas_sha256": sha096(beforeCanvas),
			"after_canvas_sha256": sha096(afterCanvas)}
	}
	report := map[string]any{"version": "goal096-prompt-guard-v1", "control": *control,
		"input_sha256": sha096(inputData), "input_hashes": wants, "source_reads": sourceReads,
		"source_before_step": sourceBeforeStep, "source_before_steps": sourceBeforeSteps,
		"source_before_events": sourceBeforeEvents,
		"source_read_step":     sourceReadStep,
		"display_step":         displayStep, "display_tail_byte": displayTailByte,
		"first_glyph_step": firstGlyphStep, "after_step": afterStep,
		"glyph_reads": glyphReads, "glyph_contexts": glyphContexts,
		"canvas_writes": writes, "samples": samples,
		"opened":        d.Opened,
		"address_space": "original file offset; DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas"}
	b, err := json.MarshalIndent(report, "", "  ")
	must096(err)
	must096(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("control=%v source=%d first_glyph=%d after=%d reads=%d writes=%d end=%d\n",
		*control, sourceReadStep, firstGlyphStep, afterStep, len(glyphReads), len(writes), m.Steps)
}
