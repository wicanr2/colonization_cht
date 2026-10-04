// 目標178可丟棄探針（Issue #55）：沿目標177 真 GUI 輸入收據重播到指定步數視窗，
// 在視窗內逐指令記錄 CS:IP、暫存器與該指令讀寫的記憶體位址，供追查 ORDERS 停用項目的奇數位字元來源。
// 原版只讀；輸出只存 workplace。
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

type input struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
	Text   string `json:"text"`
}

type replay struct {
	Inputs []input `json:"inputs"`
	End    uint64  `json:"end"`
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}

// 與 tools/probe_goal165_dialogs.go 相同的標準 PC BIOS 鍵字。
var letterScanCodes = [26]uint8{0x1E, 0x30, 0x2E, 0x20, 0x12, 0x21, 0x22, 0x23, 0x17, 0x24, 0x25, 0x26, 0x32,
	0x31, 0x18, 0x19, 0x10, 0x13, 0x1F, 0x14, 0x16, 0x2F, 0x11, 0x2D, 0x15, 0x2C}

var biosKeyWords = func() map[string]uint16 {
	w := map[string]uint16{"home": 0x4700, "end": 0x4F00, "pgup": 0x4900, "pgdn": 0x5100,
		"insert": 0x5200, "delete": 0x5300, "tab": 0x0F09,
		"kp7": 0x4700, "kp8": 0x4800, "kp9": 0x4900, "kp4": 0x4B00, "kp5": 0x4C00, "kp6": 0x4D00,
		"kp1": 0x4F00, "kp2": 0x5000, "kp3": 0x5100, "kp0": 0x5200, "kpdot": 0x5300}
	for i := 0; i < 10; i++ {
		n := fmt.Sprint(i + 1)
		w["f"+n] = uint16(0x3B+i) << 8
		w["shift-f"+n] = uint16(0x54+i) << 8
		w["ctrl-f"+n] = uint16(0x5E+i) << 8
		w["alt-f"+n] = uint16(0x68+i) << 8
	}
	for i, scan := range letterScanCodes {
		c := string(rune('a' + i))
		w["alt-"+c] = uint16(scan) << 8
		w["ctrl-"+c] = uint16(scan)<<8 | uint16(i+1)
	}
	return w
}()

func main() {
	root := flag.String("root", "/game", "唯讀原版目錄")
	inputs := flag.String("inputs", "", "真 GUI 輸入收據")
	out := flag.String("out", "", "輸出檔")
	from := flag.Uint64("from", 0, "追蹤起點（步數）")
	to := flag.Uint64("to", 0, "追蹤終點（步數）")
	scratch := flag.String("scratch", "", "正常讀檔用的可寫暫存層；原版Root唯讀")
	verifyStep := flag.Uint64("verify-step", 0, "追蹤後繼續到既有檢查點，記錄完整RAM雜湊")
	flag.Parse()
	if *inputs == "" || *out == "" || *to <= *from {
		panic("必須指定 inputs、out、from<to")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must(err)
	stat, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(stat.Uid) != os.Getuid() {
		panic("輸出目錄不存在或擁有者不符")
	}
	raw, err := os.ReadFile(*inputs)
	must(err)
	var rp replay
	must(json.Unmarshal(raw, &rp))
	exe, err := os.ReadFile(filepath.Join(*root, "OPENING.EXE"))
	must(err)
	m := golem.New()
	must(m.LoadEXE(exe))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	if *scratch != "" {
		st, err := os.Stat(*scratch)
		must(err)
		info, ok := st.Sys().(*syscall.Stat_t)
		if !st.IsDir() || !ok || int(info.Uid) != os.Getuid() {
			panic("暫存目錄擁有者不符")
		}
		r, err := filepath.EvalSymlinks(*root)
		must(err)
		s, err := filepath.EvalSymlinks(*scratch)
		must(err)
		if r == s {
			panic("暫存層不可等於原版Root")
		}
		d.Scratch = *scratch
	}
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)

	f, err := os.Create(*out)
	must(err)
	defer f.Close()
	// 視窗內每次記憶體讀取記下（位址、值）；由當前指令的行收集。
	type rd struct {
		a uint32
		v uint8
	}
	var reads []rd
	tracing, watching := false, false
	advance := func(target uint64) {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			if m.Steps >= *from && m.Steps < *to {
				if !watching {
					watching = true // 只在視窗內掛讀取監看，避免拖慢前段重播
					m.WatchReads(0, 0xfffff, func(a uint32, v uint8) {
						if tracing && len(reads) < 64 {
							reads = append(reads, rd{a, v})
						}
					})
				}
				tracing = true
				reads = reads[:0]
				c := m.CPU
				cs, ip := c.Seg[golem.CS], c.IP
				lin := uint32(cs)*16 + uint32(ip)
				op := m.Mem[lin : lin+6]
				step := m.Steps
				must(m.Step())
				fmt.Fprintf(f, "%d %04X:%04X % X | AX=%04X BX=%04X CX=%04X DX=%04X SI=%04X DI=%04X BP=%04X SP=%04X DS=%04X ES=%04X SS=%04X |",
					step, cs, ip, op, c.R[golem.AX], c.R[golem.BX], c.R[golem.CX], c.R[golem.DX], c.R[golem.SI], c.R[golem.DI],
					c.R[golem.BP], c.R[golem.SP], c.Seg[golem.DS], c.Seg[golem.ES], c.Seg[golem.SS])
				for _, r := range reads {
					fmt.Fprintf(f, " %05X=%02X", r.a, r.v)
				}
				fmt.Fprintln(f)
				tracing = false
				continue
			}
			must(m.Step())
		}
		if m.Steps != target {
			panic("原版提前結束")
		}
	}
	apply := func(e input) {
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			if !d.PushKeyNamed("Return") {
				panic("dosgolem 缺少 Return")
			}
		case "backspace", "escape", "left", "right", "up", "down":
			name := map[string]string{"backspace": "Backspace", "escape": "Escape", "left": "Left", "right": "Right", "up": "Up", "down": "Down"}[e.Kind]
			if !d.PushKeyNamed(name) {
				panic("dosgolem 缺少 " + name)
			}
		case "text":
			if !d.PushText(e.Text) {
				panic("dosgolem 拒絕字元")
			}
		case "key":
			k, ok := biosKeyWords[e.Text]
			if !ok {
				panic("未知鍵名 " + e.Text)
			}
			d.PushKey(golem.Key{Scan: uint8(k >> 8), ASCII: uint8(k)})
		default:
			panic("非法輸入事件 " + e.Kind)
		}
	}
	end := *to
	if *verifyStep > end {
		end = *verifyStep
	}
	for _, e := range rp.Inputs {
		if e.Step >= end {
			break
		}
		advance(e.Step)
		apply(e)
	}
	advance(end)
	if *verifyStep != 0 {
		b, err := json.Marshal(map[string]any{"step": m.Steps, "memory_sha256": fmt.Sprintf("%x", sha256.Sum256(m.Mem))})
		must(err)
		must(os.WriteFile(*out+".state.json", b, 0644))
	}
	fmt.Printf("追蹤完成 steps=%d\n", m.Steps)
}
