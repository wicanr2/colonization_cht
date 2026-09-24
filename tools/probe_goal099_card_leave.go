// 目標099只讀探針：第一張國家旗卡直接按完成區後的正常離頁負例。
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

type leaveInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int
}
type leaveReplay struct {
	Inputs []leaveInput `json:"inputs"`
	End    uint64       `json:"end"`
}

func leaveMust(err error) {
	if err != nil {
		panic(err)
	}
}
func leaveRead(path string) []byte {
	b, err := os.ReadFile(path)
	leaveMust(err)
	return b
}
func leaveHash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "唯讀合法 DOS 原版")
	inputs := flag.String("inputs", "", "已驗十六筆正常玩家輸入")
	out := flag.String("out", "", "已忽略 workplace 的輸出前綴")
	control := flag.Bool("control", false, "不安裝畫布監看器")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("缺必要參數")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	leaveMust(err)
	owner, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
		panic("輸出目錄擁有者不符")
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
		if leaveHash(leaveRead(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := leaveRead(*inputs)
	if leaveHash(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("正常玩家輸入版本不符")
	}
	var replay leaveReplay
	leaveMust(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("正常玩家輸入結構不符")
	}
	m := golem.New()
	leaveMust(m.LoadEXE(leaveRead(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	writes := map[string]int{}
	if !*control {
		m.WatchWrites(canvas, canvas+64000, func(_ uint32, old, value uint8) {
			if m.Steps < 43000000 || old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			writes[fmt.Sprintf("%04X:%04X", cs, ip)]++
		})
	}
	advance := func(end uint64) {
		for m.Steps < end && !d.Exited && !m.CPU.Halted {
			leaveMust(m.Step())
		}
		if m.Steps != end {
			panic("原版提前停止")
		}
	}
	for _, e := range replay.Inputs {
		if e.Step > 43000000 {
			break
		}
		advance(e.Step)
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
			panic("未知正常玩家輸入")
		}
	}
	advance(43000000)
	if leaveHash(m.Indexed()) != "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" ||
		len(d.Opened) != 51 || !strings.EqualFold(d.Opened[50], "NATIONS.PIK") {
		panic("第一張旗卡基準不符")
	}
	samples := map[string]map[string]any{}
	sample := func(name string) {
		indexed := bytes.Clone(m.Indexed())
		under := bytes.Clone(m.Mem[canvas : canvas+64000])
		palette := bytes.Clone(m.DAC[:])
		for suffix, data := range map[string][]byte{"idx": indexed, "canvas": under, "pal": palette} {
			leaveMust(os.WriteFile(*out+"."+name+"."+suffix, data, 0644))
		}
		samples[name] = map[string]any{"step": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags,
			"memory_sha256": leaveHash(m.Mem), "indexed_sha256": leaveHash(indexed),
			"canvas_sha256": leaveHash(under), "palette_sha256": leaveHash(palette),
			"opened_count": len(d.Opened), "last_opened": d.Opened[len(d.Opened)-1],
			"mouse": d.Mouse}
	}
	sample("43m")
	d.MoveMouse(65, 184)
	advance(44000000)
	sample("44m")
	d.PressMouse(0)
	advance(45000000)
	sample("45m")
	d.ReleaseMouse(0)
	advance(46000000)
	sample("46m")
	advance(49000000)
	sample("49m")
	report := map[string]any{"version": "goal099-first-card-leave-v1",
		"control": *control, "input_sha256": leaveHash(inputData),
		"source_hashes": wants, "samples": samples, "opened": d.Opened,
		"writers_after_43m": writes,
		"scope":             "第一張國家旗卡直接點完成區；沒有改原版 RAM 或資料"}
	b, err := json.MarshalIndent(report, "", "  ")
	leaveMust(err)
	leaveMust(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("control=%t end=%d opened=%d writers=%d\n", *control, m.Steps, len(d.Opened), len(writes))
}
