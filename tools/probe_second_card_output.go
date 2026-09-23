// 目標081可丟棄探針：只讀觀測第二張難度卡片的來源、緩衝與畫布。
// 不修改原版或正式中文化前端；輸出含原版位元組，只能留在本機 workplace。
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

type replayInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type replayFile struct {
	Inputs []replayInput `json:"inputs"`
	End    uint64        `json:"end"`
}
type memoryEvent struct {
	Step     uint64    `json:"step"`
	Site     string    `json:"site"`
	Linear   uint32    `json:"linear"`
	Old      uint8     `json:"old,omitempty"`
	Value    uint8     `json:"value"`
	Regs     [8]uint16 `json:"regs"`
	Segments [4]uint16 `json:"segments"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte {
	data, err := os.ReadFile(path)
	must(err)
	return data
}
func digest(data []byte) string { return fmt.Sprintf("%x", sha256.Sum256(data)) }

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀根目錄")
	inputs := flag.String("inputs", "", "目標081已核對的點擊輸入")
	out := flag.String("out", "", "本機輸出前綴")
	flag.Parse()
	if *inputs == "" || *out == "" {
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
		if digest(read(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := read(*inputs)
	var replay replayFile
	must(json.Unmarshal(inputData, &replay))
	if replay.End != 40000000 || len(replay.Inputs) != 13 ||
		replay.Inputs[9] != (replayInput{Step: 32000000, Kind: "move", X: 265, Y: 55}) ||
		replay.Inputs[10] != (replayInput{Step: 33000000, Kind: "press"}) ||
		replay.Inputs[11] != (replayInput{Step: 33800000, Kind: "release"}) ||
		replay.Inputs[12] != (replayInput{Step: 35000000, Kind: "move", X: 16, Y: 16}) {
		panic("第二張卡片固定輸入不符")
	}
	var previous uint64
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > replay.End || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("無效輸入收據")
		}
		previous = e.Step
	}
	m := golem.New()
	must(m.LoadEXE(read(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvasStart uint32 = 0x2cae0
	const canvasSize = 64000
	reads := []memoryEvent{}
	writes := []memoryEvent{}
	writeCounts := map[string]int{"source": 0, "copy": 0, "card-canvas": 0}
	readCounts := map[string]int{"source": 0, "display": 0}
	const eventLimit = 12000
	eventAt := func(a uint32, old, value uint8) memoryEvent {
		cs, ip := m.CPU.OpAddr()
		return memoryEvent{Step: m.Steps, Site: fmt.Sprintf("%04X:%04X", cs, ip),
			Linear: a, Old: old, Value: value, Regs: m.CPU.R, Segments: m.CPU.Seg}
	}
	watching := false
	watch := func() {
		m.WatchReads(0x2a000, 0x4dfa0, func(a uint32, value uint8) {
			if m.Steps < 32000000 || m.Steps >= 36000000 {
				return
			}
			group := ""
			cs, ip := m.CPU.OpAddr()
			if (a >= 0x4cc75 && a < 0x4cc7e) || (a >= 0x4df98 && a < 0x4df9e) {
				group = "source"
			} else if cs == 0x0d21 && ip == 0x00c6 {
				group = "display"
			}
			if group == "" {
				return
			}
			readCounts[group]++
			if len(reads) < eventLimit {
				reads = append(reads, eventAt(a, 0, value))
			}
		})
		m.WatchWrites(0, 0xfffff, func(a uint32, old, value uint8) {
			if m.Steps < 32000000 || m.Steps >= 36000000 || old == value {
				return
			}
			group := ""
			cs, ip := m.CPU.OpAddr()
			if (a >= 0x4cc75 && a < 0x4cc7e) || (a >= 0x4df98 && a < 0x4df9e) {
				group = "source"
			} else if cs == 0x0e2d && (ip == 0x11eb || ip == 0x11a5) {
				group = "copy"
			} else if a >= canvasStart && a < canvasStart+canvasSize {
				i := a - canvasStart
				x, y := i%320, i/320
				if x >= 128 && x < 304 && y >= 40 && y < 64 {
					group = "card-canvas"
				}
			}
			if group == "" {
				return
			}
			writeCounts[group]++
			if len(writes) < eventLimit {
				writes = append(writes, eventAt(a, old, value))
			}
		})
	}
	snapAt := map[uint64]string{
		31990000: "before-move", 32990000: "before-press", 33010000: "after-press",
		33089000: "before-title-source", 33090000: "before-title-ink",
		33099000: "after-title-ink", 33101500: "before-subtitle-ink",
		33106000: "after-subtitle-ink",
		33790000: "before-release", 33810000: "after-release", 34000000: "click-settled",
		34990000: "before-away", 35010000: "after-away", 36000000: "away-settled",
	}
	snapshots := map[string]map[string]string{}
	step := func() {
		if !watching && m.Steps == 32000000 {
			watch()
			watching = true
		}
		if name, ok := snapAt[m.Steps]; ok {
			canvas := append([]byte(nil), m.Mem[canvasStart:canvasStart+canvasSize]...)
			indexed := m.Indexed()
			must(os.WriteFile(*out+"."+name+".canvas", canvas, 0644))
			must(os.WriteFile(*out+"."+name+".idx", indexed, 0644))
			snapshots[name] = map[string]string{"canvas_sha256": digest(canvas), "indexed_sha256": digest(indexed)}
		}
		must(m.Step())
	}
	apply := func(e replayInput) {
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
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			step()
		}
		if d.Exited || m.CPU.Halted {
			panic("輸入前原版提前結束")
		}
		apply(e)
	}
	for m.Steps < replay.End && !d.Exited && !m.CPU.Halted {
		step()
	}
	if m.Steps != replay.End || len(reads) == eventLimit || len(writes) == eventLimit {
		panic("執行未到終點或事件收據截斷")
	}
	opened := false
	for _, name := range d.Opened {
		opened = opened || strings.EqualFold(name, "DIFFICUL.PIK")
	}
	result := map[string]any{
		"version": "goal081-second-card-v3", "end": m.Steps, "difficulty_art_opened": opened,
		"input_sha256": digest(inputData), "input_hashes": wants,
		"dos_address_space":    "real-mode CS:IP and 20-bit linear RAM",
		"canvas_address_space": "320x200 indexed logical pixels",
		"source_ram": map[string]string{
			"Explorer": fmt.Sprintf("%x", m.Mem[0x4cc75:0x4cc7d]),
			"Easy":     fmt.Sprintf("%x", m.Mem[0x4df98:0x4df9d]),
		},
		"read_counts": readCounts, "write_counts": writeCounts,
		"reads": reads, "writes": writes, "snapshots": snapshots,
		"state": map[string]any{
			"memory_sha256": digest(m.Mem), "registers": m.CPU.R,
			"segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
			"steps": m.Steps, "ticks": m.Ticks, "frames": m.Frames,
			"cycles": m.CPU.Cycles, "indexed_sha256": digest(m.Indexed()),
			"canvas_sha256":  digest(m.Mem[canvasStart : canvasStart+canvasSize]),
			"palette_sha256": digest(m.DAC[:]),
		},
		"limitations": "固定受控滑鼠重播的只讀探針；來源讀取與畫布寫入須以事件順序及快照差分審查，不是正式覆蓋鍵",
	}
	data, err := json.MarshalIndent(result, "", "  ")
	must(err)
	must(os.WriteFile(*out+".json", append(data, '\n'), 0644))
	fmt.Printf("第二張卡片：來源讀取 %d、顯示讀取 %d、複製寫入 %d、卡片區寫入 %d；終點 %d 步\n",
		readCounts["source"], readCounts["display"], writeCounts["copy"], writeCounts["card-canvas"], m.Steps)
}
