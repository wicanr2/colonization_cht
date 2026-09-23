// 目標087可丟棄探針：原版 TXT 候選 DOS 載入與旗卡印字前後 RAM 分布。
// 只讀原版，收據含原始記憶體片段，僅可留在忽略版控的 workplace。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type input087 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replay087 struct {
	Inputs []input087 `json:"inputs"`
	End    uint64     `json:"end"`
}
type transfer087 struct {
	Step            uint64 `json:"step"`
	Name            string `json:"name"`
	Handle          uint16 `json:"handle"`
	FileOffset      int64  `json:"file_offset"`
	Got             int    `json:"got"`
	DestinationSeg  uint16 `json:"destination_seg"`
	DestinationOff  uint16 `json:"destination_off"`
	CandidateOffset int64  `json:"candidate_offset"`
	CandidateLinear uint32 `json:"candidate_linear"`
	CandidateSHA    string `json:"candidate_sha256"`
	CandidateMatch  bool   `json:"candidate_match"`
}
type hit087 struct {
	Linear uint32 `json:"linear"`
	Text   string `json:"text"`
}
type snapshot087 struct {
	Step          uint64   `json:"step"`
	MemorySHA     string   `json:"memory_sha256"`
	SourceWindow  string   `json:"source_window_hex"`
	PrintWindow   string   `json:"print_window_hex"`
	Hits          []hit087 `json:"hits"`
	HitsTruncated bool     `json:"hits_truncated"`
}

func must087(err error) {
	if err != nil {
		panic(err)
	}
}
func read087(path string) []byte {
	b, err := os.ReadFile(path)
	must087(err)
	return b
}
func digest087(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀目錄")
	inputs := flag.String("inputs", "", "已驗16筆真視窗輸入")
	out := flag.String("out", "", "僅 workplace 的本機 JSON 收據")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("需明示 -inputs 與 -out")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must087(err)
	owner, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
		panic("輸出目錄不符")
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
		if digest087(read087(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	texts := []struct {
		Name   string
		Offset int64
		Bytes  []byte
	}{
		{"NAMES.TXT", 0x8ea, []byte("England")},
		{"LABELS.TXT", 0x8f2, []byte("Immigration")},
	}
	for _, item := range texts {
		raw := read087(filepath.Join(*root, item.Name))
		if string(raw[item.Offset:item.Offset+int64(len(item.Bytes))]) != string(item.Bytes) {
			panic("候選原始位元組不符：" + item.Name)
		}
	}
	inputData := read087(*inputs)
	if digest087(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("真視窗輸入指紋不符")
	}
	var trace replay087
	must087(json.Unmarshal(inputData, &trace))
	if len(trace.Inputs) != 16 || trace.End != 100000000 {
		panic("真視窗輸入結構不符")
	}
	m := golem.New()
	must087(m.LoadEXE(read087(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const end uint64 = 43000000
	steps := map[uint64]bool{18700000: true, 20000000: true,
		42500000: true, 42600000: true, 42700000: true,
		42800000: true, 42900000: true, 43000000: true}
	snapshots := []snapshot087{}
	transfers := []transfer087{}
	readIndex := 0
	snapshot := func() {
		hits := []hit087{}
		truncated := false
		for _, needle := range [][]byte{[]byte("England"), []byte("Immigration"),
			[]byte("ENGLAND:"), []byte("IMMIGRATION")} {
			for cursor := 0; cursor < len(m.Mem); {
				at := bytes.Index(m.Mem[cursor:], needle)
				if at < 0 {
					break
				}
				cursor += at
				if len(hits) < 100 {
					hits = append(hits, hit087{Linear: uint32(cursor), Text: string(needle)})
				} else {
					truncated = true
				}
				cursor++
			}
		}
		snapshots = append(snapshots, snapshot087{Step: m.Steps,
			MemorySHA:    digest087(m.Mem),
			SourceWindow: fmt.Sprintf("%x", m.Mem[0x2a730:0x2a7c0]),
			PrintWindow:  fmt.Sprintf("%x", m.Mem[0x2a6a0:0x2a6d0]),
			Hits:         hits, HitsTruncated: truncated})
	}
	step := func() {
		if steps[m.Steps] {
			snapshot()
		}
		must087(m.Step())
		for readIndex < len(d.Reads) {
			r := d.Reads[readIndex]
			readIndex++
			for _, item := range texts {
				if !strings.EqualFold(r.Name, item.Name) {
					continue
				}
				pos := int64(-1)
				for j := len(d.FileOps) - 1; j >= 0; j-- {
					op := d.FileOps[j]
					if op.Step == r.Step && op.Fn == 0x3f && op.Handle == r.Handle && strings.EqualFold(op.Name, r.Name) {
						pos = op.Pos
						break
					}
				}
				if pos < 0 {
					panic("DOS 讀入前偏移未知")
				}
				if !(pos <= item.Offset && item.Offset+int64(len(item.Bytes)) <= pos+int64(r.Got)) {
					continue
				}
				base := uint32(r.Seg)*16 + uint32(r.Off)
				linear := base + uint32(item.Offset-pos)
				actual := m.Mem[linear : linear+uint32(len(item.Bytes))]
				transfers = append(transfers, transfer087{Step: r.Step, Name: item.Name,
					Handle: r.Handle, FileOffset: pos, Got: r.Got,
					DestinationSeg: r.Seg, DestinationOff: r.Off,
					CandidateOffset: item.Offset, CandidateLinear: linear,
					CandidateSHA: digest087(actual), CandidateMatch: bytes.Equal(actual, item.Bytes)})
			}
		}
	}
	apply := func(e input087) {
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
	for _, e := range trace.Inputs {
		if e.Step < previous || e.Step > trace.End || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("非法真視窗輸入收據")
		}
		if e.Step > end {
			break
		}
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			step()
		}
		apply(e)
		previous = e.Step
	}
	for m.Steps < end && !d.Exited && !m.CPU.Halted {
		step()
	}
	if m.Steps != end {
		panic("原版未抵達旗卡終點")
	}
	snapshot()
	if len(transfers) < 2 {
		panic("缺候選 TXT 讀入事件")
	}
	result := map[string]any{"version": "goal087-buffer-inventory-v1",
		"address_space": "DOS AH=3Fh file offsets and DS:DX; 20-bit linear RAM",
		"input_sha256":  digest087(inputData), "input_hashes": wants,
		"transfers": transfers, "snapshots": snapshots, "opened": d.Opened,
		"state": map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags,
			"memory_sha256": digest087(m.Mem), "indexed_sha256": digest087(m.Indexed()),
			"palette_sha256": digest087(m.DAC[:])},
		"limitations": "只證明檔案載入與各時點 RAM 候選位置；尚未證實中間轉存的指令資料流"}
	encoded, err := json.MarshalIndent(result, "", "  ")
	must087(err)
	must087(os.WriteFile(*out, append(encoded, '\n'), 0644))
	fmt.Printf("候選 DOS 載入 %d 筆，RAM 快照 %d 筆\n", len(transfers), len(snapshots))
}
