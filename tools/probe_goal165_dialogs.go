// 目標165可丟棄探針（Issue #41）：沿任意真 GUI 輸入收據記錄每一筆 0D21:00C6 讀字、0D21:012C 改色、印前／印後底圖與其他寫入者，
// 供普查正常路徑上的對話框。由目標141字幕探針改寫；輸入不設白名單，收據雜湊記入輸出。
// 原版只讀；原始畫布、事件與完整狀態只存 workplace。
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type input141 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
	Text   string `json:"text"`
}
type replay141 struct {
	Inputs []input141 `json:"inputs"`
	End    uint64     `json:"end"`
}

// 一次 0D21:00C6 連續讀字（SS:BX 線性位址遞增）視為一筆印字字串。
type print141 struct {
	Start, Last  uint64
	Base, Next   uint32
	Text         []byte
	Raw          []byte // 目標143：本筆全部讀取位元組（狀態欄字串為連續讀取，不是字元與 0 交錯）
	Reads        int
	Writes       int
	Colors       map[uint8]int
	MinX, MinY   int
	MaxX, MaxY   int
	BeforeSHA    string
	AfterSHA     string
	OtherWriters map[string]int
	OtherBoxes   map[string][4]int // 目標142：其他寫入者在本筆印字期間的範圍 (minX,minY,maxX,maxY)
	before       []byte            // 目標165：印前畫布，只為對話框段落落檔
	Chars        []char165         // 目標165：逐字事件（同基址重讀的字元與 0 交錯）各字的步數與墨跡範圍
}

// 目標169：連續讀取模式的一串文字（以 0 結尾），逐字記墨跡範圍；相同文字、位置與色號只記一次並計次。
type string169 struct {
	First, Last uint64
	Count       int
	Base        uint32
	Text        string
	Box         [4]int
	Chars       [][4]int
	Colors      map[uint8]int
	next        uint32
	lastRead    uint64
}

type char165 struct {
	C                      byte
	Step                   uint64
	MinX, MinY, MaxX, MaxY int
}

func must141(err error) {
	if err != nil {
		panic(err)
	}
}
func file141(path string) []byte { b, err := os.ReadFile(path); must141(err); return b }
func sha141(b []byte) string     { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "唯讀原版目錄")
	inputs := flag.String("inputs", "", "英格蘭正常玩家路徑輸入（目標132前綴或目標141無跳過版）")
	out := flag.String("out", "", "workplace 內輸出前綴")
	control := flag.Bool("control", false, "無讀寫監看的同輸入控制")
	from := flag.Uint64("from", 76000000, "觀測起點（目標146：靜態文字普查自 10M 起）")
	snapEvery := flag.Uint64("snap-every", 0, "目標165：每隔多少步另存一次索引畫面與色盤（0 為不存）")
	// 目標167：自動應答。輸入檔用完後，對話框印完即依文字選按鍵，閒置時依序送出玩家意圖鍵；產生的輸入另存。
	autoKeys := flag.String("auto-keys", "", "閒置時依序送出的鍵（逗號分隔：kp4、enter、down、text:b 等）")
	autoAnswers := flag.String("auto-answers", "", "對話框應答：文字片段=鍵+鍵;…（未列者按 enter）")
	autoIdle := flag.Uint64("auto-idle", 15000000, "閒置多少步送下一個意圖鍵")
	autoDelay := flag.Uint64("auto-delay", 4000000, "對話框印完後多少步應答")
	autoEnd := flag.Uint64("auto-end", 0, "自動應答的終點步數（0 為不啟用）")
	autoFrom := flag.Uint64("auto-from", 0, "意圖鍵最早在此步數後送出")
	wavOut := flag.Bool("wav", false, "目標168：開啟 OPL3 合成並把整段聲音寫成 <out>.wav")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("必須指定 inputs 與 out")
	}
	parent, err := os.Stat(filepath.Dir(*out))
	must141(err)
	stat, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(stat.Uid) != os.Getuid() {
		panic("輸出目錄不存在或擁有者不符")
	}
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	}
	for name, want := range wants {
		if sha141(file141(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputBytes := file141(*inputs)
	var replay replay141
	must141(json.Unmarshal(inputBytes, &replay))
	if *autoEnd > 0 {
		replay.End = *autoEnd
	}
	m := golem.New()
	must141(m.LoadEXE(file141(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if *wavOut {
		m.EnableOPLSynth(true)
	}
	const canvas uint32 = 0x2cae0
	// @BUILD1 約在 78～89M 印字；最後一張字幕之後 1225.4M 才有玩家左移。
	start := *from
	stop := uint64(1 << 62)
	dialogPending, dialogText, dialogAt := false, "", uint64(0)
	// 目標167：像對話框的段落（有陰影色，或畫面中央十字以上的段落）印完即等待應答。
	markDialog := func(p *print141) {
		if p.Colors[47] > 0 || p.Colors[128] > 0 || (len(p.Chars) >= 10 && p.MinY > 8 && p.MaxX < 240) {
			dialogPending, dialogAt = true, m.Steps
			dialogText += string(p.Text) + " "
		}
	}
	if replay.End > start && replay.End < stop {
		stop = replay.End
	}
	strs := map[string]*string169{}
	var strCur *string169
	strDone := func() {
		c := strCur
		strCur = nil
		if c == nil || c.Box[2] < 0 {
			return
		}
		key := fmt.Sprint(c.Text, c.Box, c.Colors)
		if old, ok := strs[key]; ok {
			old.Count++
			old.Last = c.First
			return
		}
		if len(strs) < 20000 {
			c.Count, c.Last = 1, c.First
			strs[key] = c
		}
	}
	prints := []*print141{}
	var cur *print141
	frames := []map[string]any{}
	lastFrameKey := ""
	otherWrites := map[string]int{}
	otherBoxes := map[string][4]int{} // 目標146：印字事件以外的寫入者範圍
	if !*control {
		m.WatchReads(0x20000, 0x4ffff, func(a uint32, value uint8) {
			if m.Steps < start || m.Steps >= stop {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if cs != 0x0d21 || ip != 0x00c6 {
				return
			}
			c := m.CPU
			op := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
			if op != a {
				return
			}
			// 目標143：狀態欄字串逐 byte 連續讀取；同基址遞增仍屬同一筆。
			// 目標165：對話框與 help 逐字呼叫，每字都從同一基址重讀「字元、0」；兩萬步內的重讀併為同一段。
			sameRun := cur != nil && a == cur.Base && cur.Reads%2 == 0 && m.Steps-cur.Last < 20000
			if !sameRun && (cur == nil || a != cur.Next || m.Steps-cur.Last > 200000) {
				b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
				// 目標165：上一段尚未等到印後就被接手（例如正文後緊接選項），此刻畫布即其印後。
				if cur != nil && cur.before != nil && (cur.Colors[47] > 0 || cur.Colors[128] > 0) {
					cur.AfterSHA = sha141(b)
					markDialog(cur)
					must141(os.WriteFile(fmt.Sprintf("%s.print-%d.before.canvas", *out, cur.Start), cur.before, 0644))
					must141(os.WriteFile(fmt.Sprintf("%s.print-%d.after.canvas", *out, cur.Start), b, 0644))
					must141(os.WriteFile(fmt.Sprintf("%s.print-%d.pal", *out, cur.Start), m.DAC[:], 0644))
					cur.before = nil
				}
				cur = &print141{Start: m.Steps, Base: a, Colors: map[uint8]int{},
					MinX: 320, MinY: 200, MaxX: -1, MaxY: -1, BeforeSHA: sha141(b), before: b, OtherWriters: map[string]int{}, OtherBoxes: map[string][4]int{}}
				prints = append(prints, cur)
				if len(prints) > 40000 {
					panic("印字事件超出上限")
				}
			}
			// 目標169：連續讀取字串（位址遞增、0 結尾）另行逐串記錄；逐字模式的「字元、0」會成為單字元字串。
			if strCur == nil || a != strCur.next || m.Steps-strCur.lastRead > 200000 {
				strDone()
				strCur = &string169{First: m.Steps, Base: a, Box: [4]int{320, 200, -1, -1}, Colors: map[uint8]int{}}
			}
			if value == 0 {
				strDone()
			} else {
				strCur.Text += string(rune(value))
				strCur.Chars = append(strCur.Chars, [4]int{320, 200, -1, -1})
				strCur.next, strCur.lastRead = a+1, m.Steps
			}
			if cur.Reads%2 == 0 {
				cur.Text = append(cur.Text, value)
				cur.Chars = append(cur.Chars, char165{C: value, Step: m.Steps, MinX: 320, MinY: 200, MaxX: -1, MaxY: -1})
			}
			cur.Raw = append(cur.Raw, value)
			cur.Reads++
			cur.Next = a + 1
			cur.Last = m.Steps
		})
		m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, value uint8) {
			if m.Steps < start || m.Steps >= stop || old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			site := fmt.Sprintf("%04X:%04X", cs, ip)
			if cur == nil || m.Steps-cur.Last > 200000 {
				otherWrites[site]++
				i := int(a - canvas)
				x, y := i%320, i/320
				b, seen := otherBoxes[site]
				if !seen {
					b = [4]int{x, y, x, y}
				}
				otherBoxes[site] = [4]int{min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)}
				return
			}
			i := int(a - canvas)
			x, y := i%320, i/320
			if site != "0D21:012C" {
				cur.OtherWriters[site]++
				b, seen := cur.OtherBoxes[site]
				if !seen {
					b = [4]int{x, y, x, y}
				}
				cur.OtherBoxes[site] = [4]int{min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)}
				return
			}
			if sc := strCur; sc != nil && len(sc.Chars) > 0 {
				sc.Colors[value]++
				sc.Box = [4]int{min(sc.Box[0], x), min(sc.Box[1], y), max(sc.Box[2], x), max(sc.Box[3], y)}
				b := &sc.Chars[len(sc.Chars)-1]
				*b = [4]int{min(b[0], x), min(b[1], y), max(b[2], x), max(b[3], y)}
			}
			cur.Writes++
			cur.Colors[value]++
			cur.MinX, cur.MinY = min(cur.MinX, x), min(cur.MinY, y)
			cur.MaxX, cur.MaxY = max(cur.MaxX, x), max(cur.MaxY, y)
			if n := len(cur.Chars); n > 0 {
				c := &cur.Chars[n-1]
				c.MinX, c.MinY, c.MaxX, c.MaxY = min(c.MinX, x), min(c.MinY, y), max(c.MaxX, x), max(c.MaxY, y)
			}
			cur.AfterSHA = ""
		})
		m.SetOnFrame(func() {
			if m.Steps < start || m.Steps >= stop {
				return
			}
			base := m.Mem[canvas : canvas+64000]
			indexed := m.Indexed()
			same := string(base) == string(indexed)
			key := fmt.Sprint(m.VideoMode(), sha141(base), sha141(indexed), sha141(m.DAC[:]))
			if key == lastFrameKey {
				return
			}
			lastFrameKey = key
			if len(frames) >= 30000 {
				return // 目標165：長路徑只保留前三萬筆畫格變化
			}
			frames = append(frames, map[string]any{"s": m.Steps, "frame": m.Frames, "mode": m.VideoMode(),
				"canvas": sha141(base), "vga": sha141(indexed), "same": same, "pal": sha141(m.DAC[:])})
		})
	}
	var pitChanges [][2]uint64
	lastDiv := uint32(0)
	advance := func(target uint64) {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			must141(m.Step())
			// 目標168：每十萬步記一次 PIT 分頻變化（判斷音樂計時器頻率）。
			if m.Steps%100000 == 0 {
				if div := m.PITDivisor(); div != lastDiv {
					pitChanges = append(pitChanges, [2]uint64{m.Steps, uint64(div)})
					lastDiv = div
				}
			}
			if *snapEvery > 0 && m.Steps >= start && m.Steps%*snapEvery == 0 {
				must141(os.WriteFile(fmt.Sprintf("%s.snap-%d.idx", *out, m.Steps), m.Indexed(), 0644))
				must141(os.WriteFile(fmt.Sprintf("%s.snap-%d.pal", *out, m.Steps), m.DAC[:], 0644))
			}
			// 印字結束 20 萬步後記錄印後底圖一次。
			if cur != nil && cur.AfterSHA == "" && m.Steps-cur.Last == 200000 {
				b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
				cur.AfterSHA = sha141(b)
				markDialog(cur)
				// 目標165：只替帶陰影色 47／128 的段落或 24 字以上的字串（對話框候選）保存印前／印後畫布與色盤，避免狀態欄短字串灌爆輸出。
				if cur.Colors[47] > 0 || cur.Colors[128] > 0 || len(cur.Text) >= 24 {
					must141(os.WriteFile(fmt.Sprintf("%s.print-%d.before.canvas", *out, cur.Start), cur.before, 0644))
					must141(os.WriteFile(fmt.Sprintf("%s.print-%d.after.canvas", *out, cur.Start), b, 0644))
					must141(os.WriteFile(fmt.Sprintf("%s.print-%d.pal", *out, cur.Start), m.DAC[:], 0644))
				}
				cur.before = nil
			}
		}
		if m.Steps != target {
			panic("原版提前結束")
		}
	}
	apply := func(e input141) {
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
			panic("非法輸入事件")
		}
	}
	lastInput := uint64(0)
	for _, e := range replay.Inputs {
		if e.Step >= stop {
			break
		}
		advance(e.Step)
		apply(e)
		lastInput = e.Step
	}
	if *autoEnd > 0 {
		toInput := func(name string) input141 {
			switch {
			case strings.HasPrefix(name, "text:"):
				return input141{Kind: "text", Text: strings.TrimPrefix(name, "text:")}
			case name == "enter" || name == "down" || name == "up" || name == "left" || name == "right" || name == "escape" || name == "backspace":
				return input141{Kind: name}
			default:
				return input141{Kind: "key", Text: name}
			}
		}
		generated := []input141{}
		send := func(name string) {
			e := toInput(name)
			e.Step = m.Steps
			apply(e)
			generated = append(generated, e)
			lastInput = m.Steps
		}
		var intents []string
		if *autoKeys != "" {
			intents = strings.Split(*autoKeys, ",")
		}
		answers := [][2]string{}
		for _, a := range strings.Split(*autoAnswers, ";") {
			if k, v, ok := strings.Cut(a, "="); ok {
				answers = append(answers, [2]string{k, v})
			}
		}
		dialogPending, dialogText = false, ""
		for m.Steps+100000 <= *autoEnd && !d.Exited && !m.CPU.Halted {
			advance(m.Steps + 100000)
			if dialogPending && m.Steps-dialogAt >= *autoDelay {
				keys := []string{"enter"}
				for _, a := range answers {
					if strings.Contains(dialogText, a[0]) {
						keys = strings.Split(a[1], "+")
					}
				}
				fmt.Printf("應答 %d：%q → %v\n", m.Steps, dialogText, keys)
				for i, k := range keys {
					if i > 0 {
						advance(m.Steps + 1000000)
					}
					send(k)
				}
				dialogPending, dialogText = false, ""
			} else if !dialogPending && m.Steps >= *autoFrom && m.Steps-lastInput >= *autoIdle && len(intents) > 0 {
				fmt.Printf("意圖 %d：%s\n", m.Steps, intents[0])
				send(intents[0])
				intents = intents[1:]
			}
		}
		all := append(append([]input141{}, replay.Inputs...), generated...)
		b, err := json.MarshalIndent(map[string]any{"inputs": all, "end": m.Steps}, "", "  ")
		must141(err)
		must141(os.WriteFile(*out+".auto.inputs.json", append(b, '\n'), 0644))
		stop = m.Steps
	}
	advance(stop)
	if *wavOut {
		pcm := m.DrainAudio()
		rate := m.AudioRate()
		data := make([]byte, 44+len(pcm)*2)
		copy(data, "RIFF")
		le := func(off int, v uint32, n int) {
			for i := 0; i < n; i++ {
				data[off+i] = byte(v >> (8 * i))
			}
		}
		le(4, uint32(36+len(pcm)*2), 4)
		copy(data[8:], "WAVEfmt ")
		le(16, 16, 4)
		le(20, 1, 2)
		le(22, 2, 2)
		le(24, rate, 4)
		le(28, rate*4, 4)
		le(32, 4, 2)
		le(34, 16, 2)
		copy(data[36:], "data")
		le(40, uint32(len(pcm)*2), 4)
		for i, v := range pcm {
			le(44+i*2, uint32(uint16(v)), 2)
		}
		must141(os.WriteFile(*out+".wav", data, 0644))
	}
	must141(os.WriteFile(*out+".final.idx", m.Indexed(), 0644))
	must141(os.WriteFile(*out+".final.pal", m.DAC[:], 0644))
	state := map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks, "frames": m.Frames,
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
		"memory_sha256": sha141(m.Mem), "indexed_sha256": sha141(m.Indexed()),
		"palette_sha256": sha141(m.DAC[:]), "canvas_sha256": sha141(m.Mem[canvas : canvas+64000])}
	bank1, firstOPL, lastOPL := 0, uint64(0), uint64(0)
	for i, w := range m.OPL {
		if w.Bank == 1 {
			bank1++
		}
		if i == 0 {
			firstOPL = w.Step
		}
		lastOPL = w.Step
	}
	// 目標168：完整 OPL 寫入序列（步數、組、暫存器、值），供離線合成與對拍。
	oplSeq := make([][4]uint64, 0, len(m.OPL))
	for _, w := range m.OPL {
		oplSeq = append(oplSeq, [4]uint64{w.Step, uint64(w.Bank), uint64(w.Reg), uint64(w.Val)})
	}
	ob, err := json.Marshal(oplSeq)
	must141(err)
	must141(os.WriteFile(*out+".opl.json", ob, 0644))
	// 目標168：Sound Blaster DSP 與 DMA 埠的寫入統計（判斷是否播放數位音效）。
	sbPorts := map[string]int{}
	dspCmds := [][2]uint64{}
	for _, w := range m.PortLog {
		if (w.Port >= 0x220 && w.Port <= 0x22f) || w.Port <= 0x0f || (w.Port >= 0x80 && w.Port <= 0x8f) {
			sbPorts[fmt.Sprintf("%03X", w.Port)]++
			if w.Port == 0x22c && len(dspCmds) < 200 {
				dspCmds = append(dspCmds, [2]uint64{w.Step, uint64(w.Val)})
			}
		}
	}
	audio := map[string]any{"sb_ports": sbPorts, "dsp_writes": dspCmds, "pit_changes": pitChanges, "irq0_every": m.IRQ0Every, "opl_writes": len(m.OPL),
		"opl_bank1_writes": bank1, "first_opl_step": firstOPL, "last_opl_step": lastOPL, "ticks": m.Ticks}
	strDone()
	strList := make([]*string169, 0, len(strs))
	for _, v := range strs {
		strList = append(strList, v)
	}
	sort.Slice(strList, func(i, j int) bool { return strList[i].First < strList[j].First })
	result := map[string]any{"version": "goal165-dialogs-v1", "control": *control,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas; file offsets",
		"input_sha256":  sha141(inputBytes), "input_hashes": wants, "window": []uint64{start, stop},
		"strings": strList, "prints": prints, "frames": frames, "other_writes": otherWrites, "other_boxes": otherBoxes, "opened": d.Opened, "state": state, "audio": audio}
	b, err := json.Marshal(result)
	must141(err)
	must141(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("對話框探針：印字 %d、畫格變化 %d、狀態 %s\n", len(prints), len(frames), state["memory_sha256"])
}

// 與 tools/window_prototype.go 相同的標準 PC BIOS 鍵字（目標163）。
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
