// 目標120：第三張難度卡片原版輸出只讀觀測；原版畫素收據只留 workplace。
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
type event struct {
	Step   uint64 `json:"step"`
	Group  string `json:"group"`
	Site   string `json:"site"`
	Linear uint32 `json:"linear"`
	Value  byte   `json:"value"`
	Old    byte   `json:"old,omitempty"`
	X      int    `json:"x,omitempty"`
	Y      int    `json:"y,omitempty"`
}
type fileCandidate struct {
	Name   string `json:"name"`
	Offset int64  `json:"offset"`
	Length int    `json:"length"`
	Target uint32 `json:"target"`
	Text   string `json:"text"`
}
type fileLoad struct {
	Step         uint64 `json:"step"`
	Name         string `json:"name"`
	FileOffset   int64  `json:"file_offset"`
	Got          int    `json:"got"`
	Linear       uint32 `json:"linear"`
	Candidate    string `json:"candidate"`
	CandidateRAM uint32 `json:"candidate_ram"`
	Matched      bool   `json:"matched"`
	TargetAfter  string `json:"target_after_hex"`
}

func need(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte { b, e := os.ReadFile(path); need(e); return b }
func sha(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法原版唯讀目錄")
	inputPath := flag.String("inputs", "", "固定玩家輸入")
	out := flag.String("out", "", "本機收據前綴")
	observe := flag.Bool("observe", true, "安裝只讀事件監看；false 為同輸入控制")
	flag.Parse()
	if *inputPath == "" || *out == "" {
		panic("必須指定 -inputs 與 -out")
	}
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	}
	for name, want := range wants {
		if sha(read(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	candidates := []fileCandidate{
		{Name: "NAMES.TXT", Offset: 0xc22, Length: 12, Target: 0x4cc7e, Text: "Conquistador"},
		{Name: "LABELS.TXT", Offset: 0x8b8, Length: 8, Target: 0x4df9d, Text: "Moderate"},
	}
	for _, c := range candidates {
		original := read(filepath.Join(*root, c.Name))
		if c.Offset < 0 || int(c.Offset)+c.Length > len(original) ||
			string(original[c.Offset:int(c.Offset)+c.Length]) != c.Text {
			panic("候選原始位元組不符：" + c.Name)
		}
	}
	inputBytes := read(*inputPath)
	var r replay
	need(json.Unmarshal(inputBytes, &r))
	if r.End != 40000000 || len(r.Inputs) < 9 || len(r.Inputs) > 13 {
		panic("輸入數目或終點不符")
	}
	prefix := []input{
		{0, "move", 160, 100, 0}, {3800000, "enter", 0, 0, 0},
		{12600000, "press", 0, 0, 0}, {13600000, "release", 0, 0, 0},
		{22600000, "move", 16, 16, 0}, {26600000, "move", 128, 110, 0},
		{28200000, "press", 0, 0, 0}, {29000000, "release", 0, 0, 0},
		{29800000, "move", 16, 16, 0},
	}
	for i, want := range prefix {
		if r.Inputs[i] != want {
			panic("九筆真視窗前綴不符")
		}
	}
	var last uint64
	for _, e := range r.Inputs {
		if e.Step < last || e.Step > r.End || e.Button < 0 || e.Button > 2 {
			panic("輸入步數或按鍵無效")
		}
		if e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200) {
			panic("滑鼠座標無效")
		}
		if e.Kind != "move" && e.Kind != "press" && e.Kind != "release" && e.Kind != "enter" {
			panic("輸入類型無效")
		}
		last = e.Step
	}
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	const size uint32 = 64000
	reads := []event{}
	writes := []event{}
	fileLoads := []fileLoad{}
	readIndex := 0
	readCounts := map[string]int{}
	writeCounts := map[string]int{}
	const limit = 16000
	site := func() string { cs, ip := m.CPU.OpAddr(); return fmt.Sprintf("%04X:%04X", cs, ip) }
	watch := func() {
		m.WatchReads(0x2a000, 0x4e000, func(a uint32, value byte) {
			if m.Steps < 32000000 || m.Steps >= 36000000 {
				return
			}
			group := ""
			at := site()
			if at == "0D21:00C6" {
				group = "display"
			} else if (a >= 0x4cc75 && a < 0x4ccaa) || (a >= 0x4df98 && a < 0x4dfb8) {
				group = "source-candidate"
			}
			if group == "" {
				return
			}
			readCounts[group]++
			if len(reads) < limit {
				reads = append(reads, event{Step: m.Steps, Group: group, Site: at, Linear: a, Value: value})
			}
		})
		m.WatchWrites(0, 0xfffff, func(a uint32, old, value byte) {
			if m.Steps < 32000000 || m.Steps >= 36000000 || old == value {
				return
			}
			group := ""
			x, y := 0, 0
			at := site()
			if a >= canvas && a < canvas+size {
				i := a - canvas
				x, y = int(i%320), int(i/320)
				if x >= 15 && x < 105 && y >= 95 && y < 195 {
					group = "third-card-canvas"
				}
			} else if (a >= 0x4cc75 && a < 0x4ccaa) || (a >= 0x4df98 && a < 0x4dfb8) {
				group = "source-candidate"
			} else if at == "0E2D:11EB" || at == "0E2D:11A5" {
				group = "format-copy"
			}
			if group == "" {
				return
			}
			writeCounts[group]++
			if len(writes) < limit {
				writes = append(writes, event{Step: m.Steps, Group: group, Site: at, Linear: a, Old: old, Value: value, X: x, Y: y})
			}
		})
	}
	snapAt := map[uint64]string{
		31990000: "before-move", 32990000: "before-press", 33010000: "after-press",
		33089000: "before-ink", 33090750: "before-title-ink",
		33099000: "during-first-ink", 33104900: "after-title-before-subtitle",
		33104000: "before-subtitle-ink",
		33106000: "during-second-ink", 33115000: "after-second-ink",
		34000000: "click-settled", 34990000: "before-away", 36000000: "away-settled",
	}
	snaps := map[string]map[string]string{}
	watching := false
	step := func() {
		if !watching && *observe && m.Steps == 32000000 {
			watch()
			watching = true
		}
		if name, ok := snapAt[m.Steps]; ok {
			c := append([]byte(nil), m.Mem[canvas:canvas+size]...)
			idx := m.Indexed()
			need(os.WriteFile(*out+"."+name+".canvas", c, 0644))
			need(os.WriteFile(*out+"."+name+".idx", idx, 0644))
			snaps[name] = map[string]string{"canvas_sha256": sha(c), "indexed_sha256": sha(idx)}
		}
		need(m.Step())
		for readIndex < len(d.Reads) {
			rd := d.Reads[readIndex]
			readIndex++
			for _, c := range candidates {
				if !strings.EqualFold(rd.Name, c.Name) {
					continue
				}
				for j := len(d.FileOps) - 1; j >= 0; j-- {
					op := d.FileOps[j]
					if op.Step != rd.Step || op.Fn != 0x3f || op.Handle != rd.Handle ||
						!strings.EqualFold(op.Name, rd.Name) {
						continue
					}
					if c.Offset >= op.Pos && c.Offset+int64(c.Length) <= op.Pos+int64(rd.Got) {
						linear := uint32(rd.Seg)*16 + uint32(rd.Off)
						candidateRAM := linear + uint32(c.Offset-op.Pos)
						fileLoads = append(fileLoads, fileLoad{Step: rd.Step, Name: c.Name, FileOffset: op.Pos,
							Got: rd.Got, Linear: linear, Candidate: c.Text, CandidateRAM: candidateRAM,
							Matched:     string(m.Mem[candidateRAM:candidateRAM+uint32(c.Length)]) == c.Text,
							TargetAfter: fmt.Sprintf("%x", m.Mem[c.Target:c.Target+uint32(c.Length)]),
						})
					}
					break
				}
			}
		}
	}
	for _, e := range r.Inputs {
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			step()
		}
		if d.Exited || m.CPU.Halted {
			panic("原版在輸入前結束")
		}
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		}
	}
	for m.Steps < r.End && !d.Exited && !m.CPU.Halted {
		step()
	}
	if m.Steps != r.End || len(reads) == limit || len(writes) == limit {
		panic("重播未完成或事件截斷")
	}
	opened := false
	for _, name := range d.Opened {
		if strings.EqualFold(name, "DIFFICUL.PIK") {
			opened = true
		}
	}
	result := map[string]any{
		"version": "goal120-third-card-v3", "observed": *observe, "input_sha256": sha(inputBytes),
		"input_hashes": wants, "end": r.End, "difficulty_art_opened": opened,
		"dos_address_space":    "real-mode CS:IP and 20-bit linear RAM",
		"canvas_address_space": "320x200 indexed logical pixels",
		"source_candidates": map[string]string{
			"title_ram_0x4cc7e":    fmt.Sprintf("%x", m.Mem[0x4cc7e:0x4cc8b]),
			"subtitle_ram_0x4df9d": fmt.Sprintf("%x", m.Mem[0x4df9d:0x4dfa6]),
		},
		"file_loads": fileLoads, "read_counts": readCounts, "write_counts": writeCounts,
		"reads": reads, "writes": writes, "snapshots": snaps,
		"state": map[string]any{
			"memory_sha256": sha(m.Mem), "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags, "steps": m.Steps, "ticks": m.Ticks,
			"frames": m.Frames, "cycles": m.CPU.Cycles, "indexed_sha256": sha(m.Indexed()),
			"canvas_sha256": sha(m.Mem[canvas : canvas+size]), "palette_sha256": sha(m.DAC[:]),
		},
		"opened":      d.Opened,
		"limitations": "固定正常玩家前綴的受控滑鼠重播；候選地址不等於已證實輸出來源或正式覆蓋鍵",
	}
	b, err := json.MarshalIndent(result, "", "  ")
	need(err)
	need(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("第三張卡：候選來源讀取 %d、顯示讀取 %d、卡片區寫入 %d；終點 %d 步\n",
		readCounts["source-candidate"], readCounts["display"], writeCounts["third-card-canvas"], m.Steps)
}
