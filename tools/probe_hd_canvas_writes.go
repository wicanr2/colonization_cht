// 研究用：重播既有真實玩家輸入，觀測建築矩形的原版畫布寫入。
// 不安裝正式HD覆蓋，不修改原版RAM或輸入。
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"

	golem "github.com/wicanr2/dosgolem"
)

type hdProbeInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int `json:"button"`
}

type hdProbeWrite struct {
	Step      uint64    `json:"step"`
	Site      string    `json:"cs_ip"`
	Address   uint32    `json:"linear_address"`
	Value     uint8     `json:"value"`
	Registers [8]uint16 `json:"registers"`
	Segments  [4]uint16 `json:"segments"`
	Code      string    `json:"code_hex"`
	Stack     string    `json:"stack_hex"`
	Source    string    `json:"source_segment_prefix_hex"`
}

func hdNeed(err error) {
	if err != nil {
		panic(err)
	}
}
func hdRead(path string) []byte { b, err := os.ReadFile(path); hdNeed(err); return b }
func hdHash(b []byte) string    { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "唯讀合法原版")
	seed := flag.String("seed", "", "正常玩家產生的初始COLONY09.SAV")
	inputs := flag.String("inputs", "", "既有正常GUI輸入收據")
	out := flag.String("out", "", "本機研究輸出目錄，必須不存在")
	control := flag.Bool("control", false, "不裝觀測器的同輸入對照")
	flag.Parse()
	for name, want := range map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
	} {
		if hdHash(hdRead(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	seedBytes := hdRead(*seed)
	if hdHash(seedBytes) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		panic("初始存檔失配")
	}
	inputBytes := hdRead(*inputs)
	if hdHash(inputBytes) != "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979" {
		panic("正常GUI輸入收據失配")
	}
	var replay struct {
		Inputs []hdProbeInput `json:"inputs"`
		End    uint64         `json:"end"`
	}
	hdNeed(json.Unmarshal(inputBytes, &replay))
	const end = uint64(75900000)
	if replay.End < end {
		panic("輸入收據未到檢查點")
	}
	hdNeed(os.Mkdir(*out, 0755))
	scratch := filepath.Join(*out, "saves")
	hdNeed(os.Mkdir(scratch, 0755))
	hdNeed(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seedBytes, 0644))
	m := golem.New()
	hdNeed(m.LoadEXE(hdRead(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		panic("無數位音效能力")
	}
	m.EnableOPLSynth(true)
	counts := map[string]uint64{}
	var samples []hdProbeWrite
	if !*control {
		m.WatchWrite(0x2cae0, 0x2cae0+63999, func(_ *golem.Machine, addr uint32, _, value uint8) {
			if m.Steps < 50000000 {
				return
			}
			i := int(addr) - 0x2cae0
			if i%320 < 56 || i%320 >= 79 || i/320 < 13 || i/320 >= 40 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			site := fmt.Sprintf("%04X:%04X", cs, ip)
			counts[site]++
			if counts[site] > 12 {
				return
			}
			pc := uint32(cs)*16 + uint32(ip)
			stack := uint32(m.CPU.Seg[golem.SS])*16 + uint32(m.CPU.R[golem.SP])
			source := uint32(m.CPU.Seg[golem.DS]) * 16
			if pc+16 > uint32(len(m.Mem)) || stack+48 > uint32(len(m.Mem)) || source+1024 > uint32(len(m.Mem)) {
				panic("觀測範圍越界")
			}
			samples = append(samples, hdProbeWrite{m.Steps, site, addr, value, m.CPU.R, m.CPU.Seg,
				fmt.Sprintf("%x", m.Mem[pc:pc+16]), fmt.Sprintf("%x", m.Mem[stack:stack+48]),
				fmt.Sprintf("%x", m.Mem[source:source+1024])})
		})
	}
	previous := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step < previous {
			panic("輸入步數倒退")
		}
		previous = e.Step
		if e.Step > end {
			break
		}
		for m.Steps < e.Step {
			hdNeed(m.Step())
		}
		switch e.Kind {
		case "move":
			if e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200 {
				panic("輸入座標越界")
			}
			d.MoveMouse(e.X, e.Y)
		case "press", "release":
			if e.Button < 0 || e.Button > 2 {
				panic("滑鼠按鈕越界")
			}
			if e.Kind == "press" {
				d.PressMouse(e.Button)
			} else {
				d.ReleaseMouse(e.Button)
			}
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		default:
			panic("本研究收據未支援輸入：" + e.Kind)
		}
	}
	for m.Steps < end {
		hdNeed(m.Step())
	}
	result := map[string]any{"kind": "research-canvas-write-sites-not-ready-draw-contract", "control": *control,
		"steps": m.Steps, "input_sha256": hdHash(inputBytes), "seed_sha256": hdHash(seedBytes),
		"memory_sha256": hdHash(m.Mem), "indexed_sha256": hdHash(m.Indexed()), "palette_sha256": hdHash(m.DAC[:]),
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
		"observed_canvas_rect": []int{56, 13, 79, 40}, "write_counts": counts, "write_samples": samples,
		"address_space": "dosgolem real-mode CS:IP and 20-bit linear RAM; original canvas base 0x2cae0",
		"limitations":   "Write sites and stack bytes only. Function boundaries, arguments, source asset and draw order need further evidence."}
	b, err := json.MarshalIndent(result, "", "  ")
	hdNeed(err)
	hdNeed(os.WriteFile(filepath.Join(*out, "writes.json"), append(b, '\n'), 0644))
	fmt.Printf("steps=%d memory=%s sites=%d samples=%d\n", m.Steps, hdHash(m.Mem), len(counts), len(samples))
}
