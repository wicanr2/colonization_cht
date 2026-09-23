// 目標083只讀探針：LABELS.TXT 國家選擇標題兩個片段的 DOS 載入邊。
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

type inputEvent struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type inputReceipt struct {
	Inputs []inputEvent `json:"inputs"`
	End    uint64       `json:"end"`
}
type transfer struct {
	Step            uint64 `json:"step"`
	FileOffset      int64  `json:"file_offset"`
	Got             int    `json:"got"`
	Destination     uint32 `json:"destination_linear"`
	SelectBuffer    uint32 `json:"select_buffer_linear"`
	SelectHex       string `json:"select_hex"`
	PowerBuffer     uint32 `json:"power_buffer_linear"`
	PowerHex        string `json:"power_hex"`
	TransferMatched bool   `json:"transfer_matched"`
}
type memoryEvent struct {
	Step   uint64 `json:"step"`
	Site   string `json:"site"`
	Linear uint32 `json:"linear"`
	Old    uint8  `json:"old,omitempty"`
	Value  uint8  `json:"value"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func file(path string) []byte {
	b, err := os.ReadFile(path)
	must(err)
	return b
}
func sha(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "唯讀 DOS 原版")
	inputs := flag.String("inputs", "", "真視窗輸入收據")
	out := flag.String("out", "", "本機 JSON 收據")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("需指定 -inputs 與 -out")
	}
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	}
	for name, want := range wants {
		if sha(file(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	labels := file(filepath.Join(*root, "LABELS.TXT"))
	selectBytes, powerBytes := labels[0x8d3:0x8d9], labels[0x8db:0x8e9]
	if string(selectBytes) != "Select" || string(powerBytes) != "European Power" {
		panic("候選原文字節不符")
	}
	inputData := file(*inputs)
	var replay inputReceipt
	must(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) < 4 || replay.Inputs[3].Step > 20000000 {
		panic("正常入口輸入不足")
	}
	m := golem.New()
	must(m.LoadEXE(file(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const end uint64 = 20000000
	const selectTarget uint32 = 0x4dfb5
	const powerTarget uint32 = 0x4dfbc
	var selectBuffer, powerBuffer uint32
	transfers := []transfer{}
	reads := []memoryEvent{}
	writes := []memoryEvent{}
	readIndex := 0
	m.WatchReads(0x2b000, 0x2bfff, func(a uint32, value uint8) {
		if m.Steps < 18000000 || m.Steps > 20000000 ||
			!((selectBuffer <= a && a < selectBuffer+uint32(len(selectBytes))) ||
				(powerBuffer <= a && a < powerBuffer+uint32(len(powerBytes)))) {
			return
		}
		if len(reads) >= 10000 {
			panic("來源緩衝讀取超出上限")
		}
		cs, ip := m.CPU.OpAddr()
		reads = append(reads, memoryEvent{Step: m.Steps, Site: fmt.Sprintf("%04X:%04X", cs, ip),
			Linear: a, Value: value})
	})
	m.WatchWrites(selectTarget, powerTarget+uint32(len(powerBytes)), func(a uint32, old, value uint8) {
		if m.Steps < 18000000 || m.Steps > 20000000 {
			return
		}
		if len(writes) >= 10000 {
			panic("目標寫入超出上限")
		}
		cs, ip := m.CPU.OpAddr()
		writes = append(writes, memoryEvent{Step: m.Steps, Site: fmt.Sprintf("%04X:%04X", cs, ip),
			Linear: a, Old: old, Value: value})
	})
	step := func() {
		must(m.Step())
		for readIndex < len(d.Reads) {
			r := d.Reads[readIndex]
			readIndex++
			if !strings.EqualFold(r.Name, "LABELS.TXT") {
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
				panic("無法定位 DOS AH=3Fh 讀入前偏移")
			}
			if !(pos <= 0x8d3 && pos+int64(r.Got) >= 0x8e9) {
				continue
			}
			base := uint32(r.Seg)*16 + uint32(r.Off)
			selectBuffer = base + uint32(int64(0x8d3)-pos)
			powerBuffer = base + uint32(int64(0x8db)-pos)
			gotSelect := m.Mem[selectBuffer : selectBuffer+uint32(len(selectBytes))]
			gotPower := m.Mem[powerBuffer : powerBuffer+uint32(len(powerBytes))]
			transfers = append(transfers, transfer{Step: r.Step, FileOffset: pos, Got: r.Got,
				Destination: base, SelectBuffer: selectBuffer, SelectHex: fmt.Sprintf("%x", gotSelect),
				PowerBuffer: powerBuffer, PowerHex: fmt.Sprintf("%x", gotPower),
				TransferMatched: string(gotSelect) == string(selectBytes) && string(gotPower) == string(powerBytes)})
		}
	}
	apply := func(e inputEvent) {
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
			panic("未知輸入")
		}
	}
	for _, e := range replay.Inputs {
		if e.Step > end {
			break
		}
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			step()
		}
		apply(e)
	}
	for m.Steps < end && !d.Exited && !m.CPU.Halted {
		step()
	}
	if m.Steps != end || len(transfers) != 1 || !transfers[0].TransferMatched {
		panic("候選載入邊不完整")
	}
	result := map[string]any{
		"version": "goal083-label-load-v1", "input_sha256": sha(inputData),
		"input_hashes": wants, "address_space": "DOS AH=3Fh file offset; 20-bit linear RAM; real-mode CS:IP",
		"select_file_offset": "0x8D3", "select_bytes_sha256": sha(selectBytes),
		"power_file_offset": "0x8DB", "power_bytes_sha256": sha(powerBytes),
		"transfers": transfers, "source_reads": reads, "target_writes": writes,
		"target_select_hex": fmt.Sprintf("%x", m.Mem[selectTarget:selectTarget+7]),
		"target_power_hex":  fmt.Sprintf("%x", m.Mem[powerTarget:powerTarget+15]),
		"end":               m.Steps, "memory_sha256": sha(m.Mem),
		"limitations": "檔案載入與目標記憶體；後續原版格式化及畫布寫入由獨立探針核對",
	}
	b, err := json.MarshalIndent(result, "", "  ")
	must(err)
	must(os.WriteFile(*out, append(b, '\n'), 0644))
	fmt.Printf("LABELS.TXT %d次匹配讀取；來源緩衝讀取 %d；目標寫入 %d\n",
		len(transfers), len(reads), len(writes))
}
