// 目標077：以 DOS 讀檔收據與 CPU 寫入觀測，追第一張難度卡片的原文載入邊。
// 僅研究固定原版與正常玩家路徑；不修改機器／DOS 狀態或正式中文顯示。
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

type loadInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type loadReplay struct {
	Inputs []loadInput `json:"inputs"`
	End    uint64      `json:"end"`
}
type candidate struct {
	Name       string `json:"name"`
	FileOffset int64  `json:"file_offset"`
	SourceSHA  string `json:"source_sha256"`
	BytesSHA   string `json:"bytes_sha256"`
	Length     int    `json:"length"`
	Target     uint32 `json:"runtime_target"`
	Text       []byte `json:"-"`
}
type loadRead struct {
	Step            uint64 `json:"step"`
	Name            string `json:"name"`
	Handle          uint16 `json:"handle"`
	FileOffset      int64  `json:"file_offset"`
	Got             int    `json:"got"`
	Seg             uint16 `json:"seg"`
	Off             uint16 `json:"off"`
	Linear          uint32 `json:"linear"`
	CandidateOffset int64  `json:"candidate_offset,omitempty"`
	CandidateLinear uint32 `json:"candidate_linear,omitempty"`
	CandidateSHA    string `json:"candidate_ram_sha256,omitempty"`
	CandidateMatch  bool   `json:"candidate_ram_match,omitempty"`
	TargetAfter     string `json:"target_after_hex,omitempty"`
}
type loadWrite struct {
	Step      uint64    `json:"step"`
	Site      string    `json:"site"`
	Linear    uint32    `json:"linear"`
	Old       uint8     `json:"old"`
	Value     uint8     `json:"value"`
	Regs      [8]uint16 `json:"regs"`
	Segments  [4]uint16 `json:"segments"`
	Code      []byte    `json:"code"`
	Opened    int       `json:"opened_count"`
	ReadCount int       `json:"read_count"`
}
type loadSourceRead struct {
	Step   uint64 `json:"step"`
	Site   string `json:"site"`
	Linear uint32 `json:"linear"`
	Value  uint8  `json:"value"`
}

func need(err error) {
	if err != nil {
		panic(err)
	}
}
func data(path string) []byte {
	b, err := os.ReadFile(path)
	need(err)
	return b
}
func digest(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "唯讀原版根目錄")
	inputs := flag.String("inputs", "/out/goal059-ebiten.inputs.json", "正常玩家輸入收據")
	out := flag.String("out", "/out/goal077-card-load.json", "本機研究收據")
	second := flag.Bool("second", false, "目標081：只追第二張卡片的 Explorer／Easy 載入邊")
	flag.Parse()
	versions := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	}
	for name, want := range versions {
		if digest(data(*root+"/"+name)) != want {
			panic("原版檔案版本不符：" + name)
		}
	}
	candidates := []candidate{
		{Name: "GAME.TXT", FileOffset: 0xA26, SourceSHA: versions["GAME.TXT"], Target: 0x4CC6A, Text: []byte("Discoverer")},
		{Name: "NAMES.TXT", FileOffset: 0xC0C, SourceSHA: versions["NAMES.TXT"], Target: 0x4CC6A, Text: []byte("Discoverer")},
		{Name: "LABELS.TXT", FileOffset: 0x8A9, SourceSHA: versions["LABELS.TXT"], Target: 0x4DF90, Text: []byte("Easiest")},
	}
	if *second {
		candidates = []candidate{
			{Name: "NAMES.TXT", FileOffset: 0xC18, SourceSHA: versions["NAMES.TXT"], Target: 0x4CC75, Text: []byte("Explorer")},
			{Name: "LABELS.TXT", FileOffset: 0x8B2, SourceSHA: versions["LABELS.TXT"], Target: 0x4DF98, Text: []byte("Easy")},
		}
	}
	for i := range candidates {
		c := &candidates[i]
		original := data(*root + "/" + c.Name)
		if c.FileOffset < 0 || int(c.FileOffset)+len(c.Text) > len(original) ||
			string(original[c.FileOffset:int(c.FileOffset)+len(c.Text)]) != string(c.Text) {
			panic("原始 TXT 候選位元組不符：" + c.Name)
		}
		c.Length = len(c.Text)
		c.BytesSHA = digest(c.Text)
	}
	var replay loadReplay
	need(json.Unmarshal(data(*inputs), &replay))
	const end uint64 = 32000000
	const canvas uint32 = 0x2CAE0
	m := golem.New()
	need(m.LoadEXE(data(*root + "/OPENING.EXE")))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	fileReads := []loadRead{}
	writes := []loadWrite{}
	sourceReads := []loadSourceRead{}
	watchTruncated := false
	readTruncated := false
	titleWindow := func(step uint64) bool { return 16208974 <= step && step <= 16215530 }
	subtitleWindow := func(step uint64) bool { return 18648994 <= step && step <= 18682730 }
	m.WatchReads(176130, 176641, func(a uint32, value uint8) {
		if !((titleWindow(m.Steps) && 176130 <= a && a <= 176170) ||
			(subtitleWindow(m.Steps) && 176265 <= a && a <= 176320)) {
			return
		}
		if len(sourceReads) >= 20000 {
			readTruncated = true
			return
		}
		cs, ip := m.CPU.OpAddr()
		sourceReads = append(sourceReads, loadSourceRead{Step: m.Steps,
			Site: fmt.Sprintf("%04X:%04X", cs, ip), Linear: a, Value: value})
	})
	watchEnd := uint32(0x4DF97)
	if *second {
		watchEnd = 0x4DF9C
	}
	m.WatchWrites(149980, watchEnd, func(a uint32, old, value uint8) {
		intermediate := 149980 <= a && a <= 149990 &&
			(titleWindow(m.Steps) || subtitleWindow(m.Steps))
		buffer := titleWindow(m.Steps) && 176130 <= a && a <= 176170 ||
			subtitleWindow(m.Steps) && 176265 <= a && a <= 176320
		target := 0x4CC6A <= a && a <= 0x4CC74 || 0x4DF90 <= a && a <= 0x4DF97
		if *second {
			target = 0x4CC75 <= a && a <= 0x4CC7D || 0x4DF98 <= a && a <= 0x4DF9C
		}
		if !(intermediate || buffer || target) {
			return
		}
		if len(writes) >= 20000 {
			watchTruncated = true
			return
		}
		cs, ip := m.CPU.OpAddr()
		pc := uint32(cs)*16 + uint32(ip)
		var code []byte
		if pc+8 <= uint32(len(m.Mem)) {
			code = append([]byte(nil), m.Mem[pc:pc+8]...)
		}
		writes = append(writes, loadWrite{Step: m.Steps, Site: fmt.Sprintf("%04X:%04X", cs, ip),
			Linear: a, Old: old, Value: value, Regs: m.CPU.R, Segments: m.CPU.Seg,
			Code: code, Opened: len(d.Opened), ReadCount: len(d.Reads)})
	})
	apply := func(e loadInput) {
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1C, ASCII: 13})
		default:
			panic("未知玩家輸入")
		}
	}
	readIndex := 0
	step := func() {
		need(m.Step())
		for readIndex < len(d.Reads) {
			r := d.Reads[readIndex]
			readIndex++
			name := strings.ToUpper(r.Name)
			if name != "GAME.TXT" && name != "NAMES.TXT" && name != "LABELS.TXT" {
				continue
			}
			var pos int64 = -1
			for j := len(d.FileOps) - 1; j >= 0; j-- {
				op := d.FileOps[j]
				if op.Step == r.Step && op.Fn == 0x3F && op.Handle == r.Handle && strings.EqualFold(op.Name, r.Name) {
					pos = op.Pos
					break
				}
			}
			if pos < 0 {
				panic("找不到同一步的 DOS FileOp 偏移")
			}
			linear := uint32(r.Seg)*16 + uint32(r.Off)
			row := loadRead{Step: r.Step, Name: name, Handle: r.Handle,
				FileOffset: pos, Got: r.Got, Seg: r.Seg, Off: r.Off, Linear: linear}
			for _, c := range candidates {
				if name != c.Name || c.FileOffset < pos || c.FileOffset+int64(c.Length) > pos+int64(r.Got) {
					continue
				}
				addr := linear + uint32(c.FileOffset-pos)
				if addr+uint32(c.Length) > uint32(len(m.Mem)) {
					panic("DOS 讀入位址越界")
				}
				actual := m.Mem[addr : addr+uint32(c.Length)]
				row.CandidateOffset = c.FileOffset
				row.CandidateLinear = addr
				row.CandidateSHA = digest(actual)
				row.CandidateMatch = string(actual) == string(c.Text)
				row.TargetAfter = fmt.Sprintf("%x", m.Mem[c.Target:c.Target+uint32(c.Length)])
			}
			fileReads = append(fileReads, row)
		}
	}
	var previous uint64
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > end || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
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
	version := "goal077-card-load-v4"
	titleStart, titleEnd := uint32(0x4CC6A), uint32(0x4CC74)
	subtitleStart, subtitleEnd := uint32(0x4DF90), uint32(0x4DF97)
	if *second {
		version = "goal081-second-card-load-v1"
		titleStart, titleEnd = 0x4CC75, 0x4CC7D
		subtitleStart, subtitleEnd = 0x4DF98, 0x4DF9D
	}
	result := map[string]any{
		"version": version, "end": m.Steps, "exited": d.Exited,
		"input_hashes": versions, "input_sha256": digest(data(*inputs)),
		"dos_address_space":  "real-mode CS:IP and 20-bit linear RAM",
		"file_address_space": "DOS AH=3Fh file offset, DS:DX destination",
		"candidates":         candidates, "file_reads": fileReads,
		"target_writes": writes, "writes_truncated": watchTruncated,
		"source_reads": sourceReads, "reads_truncated": readTruncated,
		"opened":              d.Opened,
		"target_title_hex":    fmt.Sprintf("%x", m.Mem[titleStart:titleEnd]),
		"target_subtitle_hex": fmt.Sprintf("%x", m.Mem[subtitleStart:subtitleEnd]),
		"memory_sha256":       digest(m.Mem),
		"canvas_sha256":       digest(m.Mem[canvas : canvas+64000]),
		"indexed_sha256":      digest(m.Indexed()), "palette_sha256": digest(m.DAC[:]),
		"limitations": "DOS ReadOp/ FileOp read edges and CPU target writes; indirect copy needs separate evidence",
	}
	encoded, err := json.MarshalIndent(result, "", "  ")
	need(err)
	need(os.WriteFile(*out, append(encoded, '\n'), 0644))
	fmt.Printf("%d steps; target writes %d; relevant file reads %d\n", m.Steps, len(writes), len(fileReads))
}
