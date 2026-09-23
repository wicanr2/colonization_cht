// 目標097：沿正常玩家輸入擷取可編輯預設姓名的印前底圖、墨跡及輸入分支。
// 原版唯讀；原始畫布、索引、色盤及 RAM 僅留在已忽略的 workplace。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type input097 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int
}
type replay097 struct {
	Inputs []input097 `json:"inputs"`
	End    uint64     `json:"end"`
}
type point097 struct {
	Step uint64 `json:"step"`
	CSIP string `json:"cs_ip"`
	X    int    `json:"x"`
	Y    int    `json:"y"`
	Old  uint8  `json:"old"`
	New  uint8  `json:"new"`
}

func must097(err error) {
	if err != nil {
		panic(err)
	}
}
func read097(path string) []byte { b, err := os.ReadFile(path); must097(err); return b }
func sha097(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法原版唯讀目錄")
	inputs := flag.String("inputs", "", "已驗十六筆正常玩家輸入")
	out := flag.String("out", "", "已忽略 workplace 輸出前綴")
	scenario := flag.String("scenario", "idle", "idle、letter、backspace 或 enter")
	control := flag.Bool("control", false, "不裝原版讀寫觀測器")
	flag.Parse()
	if *inputs == "" || *out == "" ||
		(*scenario != "idle" && *scenario != "letter" && *scenario != "backspace" && *scenario != "enter") {
		panic("探針參數不完整")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must097(err)
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
		if sha097(read097(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	nameFile := read097(filepath.Join(*root, "NAMES.TXT"))
	if !bytes.Equal(nameFile[0xb4b:0xb4b+15], []byte("Jacques Cartier")) {
		panic("原始預設姓名不符")
	}
	inputData := read097(*inputs)
	if sha097(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("正常玩家輸入指紋不符")
	}
	var replay replay097
	must097(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("正常玩家輸入結構不符")
	}
	m := golem.New()
	must097(m.LoadEXE(read097(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	const glyph uint32 = 0x2a972
	reads := []map[string]any{}
	writes := []point097{}
	if !*control {
		m.WatchReads(glyph, glyph+1, func(a uint32, value uint8) {
			if m.Steps < 48723846 || m.Steps >= 48764342 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if cs == 0x0d21 && ip == 0x00c6 {
				reads = append(reads, map[string]any{"step": m.Steps, "cs_ip": "0D21:00C6",
					"linear": a, "value": value})
			}
		})
		m.WatchWrites(canvas, canvas+64000, func(a uint32, old, value uint8) {
			if m.Steps < 48723846 || m.Steps >= 48764342 || old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			i := int(a - canvas)
			writes = append(writes, point097{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip),
				i % 320, i / 320, old, value})
		})
	}
	advance := func(end uint64) {
		for m.Steps < end && !d.Exited && !m.CPU.Halted {
			must097(m.Step())
		}
		if m.Steps != end {
			panic("原版提前停止")
		}
	}
	apply := func(e input097) {
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
			panic("未知玩家事件")
		}
	}
	for _, e := range replay.Inputs {
		if e.Step > 43000000 {
			break
		}
		advance(e.Step)
		apply(e)
	}
	advance(43000000)
	if sha097(m.Indexed()) != "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" {
		panic("第一張旗卡基準不符")
	}
	d.MoveMouse(255, 50)
	advance(44000000)
	d.PressMouse(0)
	advance(45000000)
	d.ReleaseMouse(0)
	advance(46000000)
	d.MoveMouse(65, 184)
	advance(47000000)
	d.PressMouse(0)
	advance(48000000)
	d.ReleaseMouse(0)
	samples := map[string]map[string]any{}
	sample := func(label string) {
		idx := m.Indexed()
		picture := bytes.Clone(m.Mem[canvas : canvas+64000])
		palette := bytes.Clone(m.DAC[:])
		for suffix, data := range map[string][]byte{"idx": idx, "canvas": picture, "pal": palette} {
			must097(os.WriteFile(*out+"."+label+"."+suffix, data, 0644))
		}
		samples[label] = map[string]any{"step": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags, "memory_sha256": sha097(m.Mem),
			"indexed_sha256": sha097(idx), "canvas_sha256": sha097(picture),
			"palette_sha256": sha097(palette), "opened_count": len(d.Opened)}
	}
	advance(48723846)
	sample("before")
	advance(48746663)
	sample("before_ink")
	advance(48764342)
	sample("after")
	advance(49000000)
	sample("49m")
	if sha097(m.Indexed()) != "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e" {
		panic("姓名畫面基準不符")
	}
	advance(55000000)
	sample("55m")
	if *scenario == "letter" || *scenario == "backspace" {
		d.PushKey(golem.Key{Scan: 0x2d, ASCII: 'x'})
	} else if *scenario == "enter" {
		d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
	}
	advance(57000000)
	sample("57m")
	if *scenario == "backspace" {
		d.PushKey(golem.Key{Scan: 0x0e, ASCII: 8})
	}
	advance(65000000)
	sample("65m")
	report := map[string]any{"version": "goal097-name-field-v1", "scenario": *scenario,
		"control": *control, "input_sha256": sha097(inputData), "input_hashes": wants,
		"source":  map[string]any{"name": "NAMES.TXT", "offset": "0xB4B", "bytes": "Jacques Cartier"},
		"samples": samples, "reads": reads, "writes": writes, "opened": d.Opened,
		"address_space": "original file offset; DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas"}
	data, err := json.MarshalIndent(report, "", "  ")
	must097(err)
	must097(os.WriteFile(*out+".json", append(data, '\n'), 0644))
	fmt.Printf("scenario=%s control=%v reads=%d writes=%d end=%d\n",
		*scenario, *control, len(reads), len(writes), m.Steps)
}
