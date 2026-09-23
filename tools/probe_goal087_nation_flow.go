// 目標087可丟棄探針：觀測旗卡候選 DOS 緩衝、常駐字串及印字緩衝的讀寫端。
// 不修改原版或正式中文覆蓋；原始記憶體與收據只留 workplace。
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type flowInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type flowReplay struct {
	Inputs []flowInput `json:"inputs"`
	End    uint64      `json:"end"`
}
type flowEvent struct {
	Step     uint64    `json:"step"`
	Kind     string    `json:"kind"`
	Site     string    `json:"site"`
	Linear   uint32    `json:"linear"`
	Value    uint8     `json:"value"`
	Old      uint8     `json:"old,omitempty"`
	Regs     [8]uint16 `json:"regs"`
	Segments [4]uint16 `json:"segments"`
	Code     []byte    `json:"code"`
}

func fail(err error) {
	if err != nil {
		panic(err)
	}
}
func bytesFrom(path string) []byte {
	b, err := os.ReadFile(path)
	fail(err)
	return b
}
func sha256hex(data []byte) string { return fmt.Sprintf("%x", sha256.Sum256(data)) }

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀根目錄")
	inputs := flag.String("inputs", "", "已驗16筆真視窗輸入")
	out := flag.String("out", "", "只留 workplace 的收據路徑")
	control := flag.Bool("control", false, "不註冊 RAM 讀寫監看器的同輸入對照")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("需明示 -inputs 與 -out")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	fail(err)
	owner, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
		panic("輸出目錄不存在或擁有者不符")
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
		if sha256hex(bytesFrom(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputBytes := bytesFrom(*inputs)
	if sha256hex(inputBytes) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("真視窗輸入指紋不符")
	}
	var replay flowReplay
	fail(json.Unmarshal(inputBytes, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("真視窗輸入結構不符")
	}
	m := golem.New()
	fail(m.LoadEXE(bytesFrom(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	events := []flowEvent{}
	truncated := false
	relevant := func(a uint32) bool {
		step := m.Steps
		nameLoad := 15500000 <= step && step < 15550000
		nameReload := 17020000 <= step && step < 17080000
		labelLoad := 18070000 <= step && step < 18140000
		display := 42850000 <= step && step < 42890000
		if 0x2b0d0 <= a && a < 0x2b110 && (nameLoad || nameReload || labelLoad) {
			return true // 共用 DOS 讀入／就地整理緩衝
		}
		if ((0x26c50 <= a && a < 0x26c80) && (nameLoad || nameReload)) ||
			((0x249d0 <= a && a < 0x249f0) && (nameLoad || nameReload || labelLoad)) {
			return true // NAMES／LABELS 常駐字串前的原版中間緩衝
		}
		if (0x4cbb0 <= a && a < 0x4cbd0 && (nameLoad || nameReload || display)) ||
			(0x4dfc0 <= a && a < 0x4dfe0 && (labelLoad || display)) {
			return true // 20M RAM 快照中留存的兩個候選
		}
		if display && ((0x2a730 <= a && a < 0x2a770) ||
			(0x2a6a0 <= a && a < 0x2a6c0) || (0x249d0 <= a && a < 0x249f0) ||
			(0x21ac0 <= a && a < 0x21ae0)) {
			return true // 第一張旗卡的來源、格式化與替代同文位置
		}
		return false
	}
	collect := func(kind string, a uint32, old, value uint8) {
		if !relevant(a) {
			return
		}
		if len(events) >= 50000 {
			truncated = true
			return
		}
		cs, ip := m.CPU.OpAddr()
		pc := uint32(cs)*16 + uint32(ip)
		var code []byte
		if pc+8 <= uint32(len(m.Mem)) {
			code = append([]byte(nil), m.Mem[pc:pc+8]...)
		}
		events = append(events, flowEvent{Step: m.Steps, Kind: kind,
			Site: fmt.Sprintf("%04X:%04X", cs, ip), Linear: a,
			Old: old, Value: value, Regs: m.CPU.R, Segments: m.CPU.Seg, Code: code})
	}
	if !*control {
		m.WatchReads(0x20000, 0x4ffff, func(a uint32, value uint8) {
			collect("read", a, 0, value)
		})
		m.WatchWrites(0x20000, 0x4ffff, func(a uint32, old, value uint8) {
			collect("write", a, old, value)
		})
	}
	apply := func(e flowInput) {
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
	const end uint64 = 43000000
	for _, e := range replay.Inputs {
		if e.Step < previous || e.Step > replay.End || e.Button < 0 || e.Button > 2 ||
			(e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200)) {
			panic("非法真視窗輸入收據")
		}
		if e.Step > end {
			break
		}
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			fail(m.Step())
		}
		apply(e)
		previous = e.Step
	}
	for m.Steps < end && !d.Exited && !m.CPU.Halted {
		fail(m.Step())
	}
	if m.Steps != end {
		panic("原版未抵達旗卡終點")
	}
	result := map[string]any{"version": "goal087-nation-flow-v5-compact-source", "control": *control,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM",
		"input_sha256":  sha256hex(inputBytes), "input_hashes": wants,
		"events": events, "events_truncated": truncated, "opened": d.Opened,
		"state": map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags,
			"memory_sha256": sha256hex(m.Mem), "indexed_sha256": sha256hex(m.Indexed()),
			"palette_sha256": sha256hex(m.DAC[:])},
		"limitations": "僅候選位址的 CPU 讀寫；檔案載入位移另由同輸入緩衝清冊提供"}
	b, err := json.MarshalIndent(result, "", "  ")
	fail(err)
	fail(os.WriteFile(*out, append(b, '\n'), 0644))
	fmt.Printf("旗卡候選讀寫事件 %d；截斷 %t；原版 RAM %s\n",
		len(events), truncated, sha256hex(m.Mem))
}
