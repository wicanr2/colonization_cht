// 目標094：正常玩家路徑的姓名提示印前／印後原版畫布。
// 原版只讀；原始索引、色盤與畫布只輸出到已忽略的 workplace。
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

type event094 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}

type replay094 struct {
	Inputs []event094 `json:"inputs"`
	End    uint64     `json:"end"`
}

type write094 struct {
	Step uint64 `json:"step"`
	CSIP string `json:"cs_ip"`
	X    int    `json:"x"`
	Y    int    `json:"y"`
	Old  uint8  `json:"old"`
	New  uint8  `json:"new"`
}

type read094 struct {
	Step   uint64 `json:"step"`
	CSIP   string `json:"cs_ip"`
	Linear uint32 `json:"linear"`
	Value  uint8  `json:"value"`
}

func must094(err error) {
	if err != nil {
		panic(err)
	}
}

func file094(path string) []byte {
	b, err := os.ReadFile(path)
	must094(err)
	return b
}

func sha094(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法原版唯讀目錄")
	inputs := flag.String("inputs", "", "固定正常玩家輸入")
	out := flag.String("out", "", "workplace 內輸出前綴")
	control := flag.Bool("control", false, "不安裝畫布或印字觀測器")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("缺少輸入或輸出路徑")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must094(err)
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
		if sha094(file094(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	game := file094(filepath.Join(*root, "GAME.TXT"))
	const prompt = "Please Enter Your Name."
	if !bytes.Equal(game[0xa7a:0xa7c], []byte("^^")) ||
		!bytes.Equal(game[0xa7c:0xa7c+len(prompt)], []byte(prompt)) {
		panic("提示原始位元組不符")
	}
	inputData := file094(*inputs)
	if sha094(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("玩家輸入指紋不符")
	}
	var replay replay094
	must094(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("玩家輸入結構不符")
	}
	m := golem.New()
	must094(m.LoadEXE(file094(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	writes := []write094{}
	reads := []read094{}
	if !*control {
		m.WatchWrites(canvas, canvas+64000, func(a uint32, old, value uint8) {
			if m.Steps < 48696982 || m.Steps >= 48721827 || old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			i := int(a - canvas)
			writes = append(writes, write094{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), i % 320, i / 320, old, value})
		})
		m.WatchReads(0x2a864, 0x2a865, func(a uint32, value uint8) {
			if m.Steps < 48696982 || m.Steps >= 48721827 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if cs == 0x0d21 && ip == 0x00c6 {
				reads = append(reads, read094{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, value})
			}
		})
	}
	advance := func(end uint64) {
		for m.Steps < end && !d.Exited && !m.CPU.Halted {
			must094(m.Step())
		}
		if m.Steps != end {
			panic("原版提前停止")
		}
	}
	apply := func(e event094) {
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
	if sha094(m.Indexed()) != "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" {
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
	sample := func(name string) {
		indexed := m.Indexed()
		picture := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
		palette := append([]byte(nil), m.DAC[:]...)
		must094(os.WriteFile(*out+"."+name+".idx", indexed, 0644))
		must094(os.WriteFile(*out+"."+name+".canvas", picture, 0644))
		must094(os.WriteFile(*out+"."+name+".pal", palette, 0644))
		samples[name] = map[string]any{"step": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags, "memory_sha256": sha094(m.Mem),
			"indexed_sha256": sha094(indexed), "canvas_sha256": sha094(picture),
			"palette_sha256": sha094(palette), "opened_count": len(d.Opened)}
	}
	advance(48696982)
	sample("before")
	advance(48721827)
	sample("after")
	advance(49000000)
	sample("49m")
	if sha094(m.Indexed()) != "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e" {
		panic("姓名畫面基準不符")
	}
	advance(55000000)
	sample("55m")
	report := map[string]any{"version": "goal094-prompt-v1", "control": *control,
		"input_sha256": sha094(inputData), "input_hashes": wants,
		"samples": samples, "reads": reads, "writes": writes, "opened": d.Opened,
		"address_space": "original file offset; DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas"}
	data, err := json.MarshalIndent(report, "", "  ")
	must094(err)
	must094(os.WriteFile(*out+".json", append(data, '\n'), 0644))
	fmt.Printf("control=%v reads=%d writes=%d end=%d\n", *control, len(reads), len(writes), m.Steps)
}
