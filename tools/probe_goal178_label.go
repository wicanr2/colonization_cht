// 目標178可丟棄探針（Issue #55）：追查地圖上白字殖民地名稱標籤的印字常式。
// 沿真 GUI 輸入收據重播；在起點掃描記憶體中的名稱字串位置，視窗內記錄
// （1）誰讀了名稱字串（步數、CS:IP、位址）、（2）誰寫了標籤矩形內的畫布像素（CS:IP 彙整）。
// 原版只讀；輸出只存 workplace。
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
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

type writer struct {
	CSIP        string
	Values      map[uint8]int
	Count       int
	First, Last uint64
	MinX, MinY  int
	MaxX, MaxY  int
}

func main() {
	root := flag.String("root", "/game", "唯讀原版目錄")
	inputs := flag.String("inputs", "", "真 GUI 輸入收據")
	out := flag.String("out", "", "輸出 JSON")
	from := flag.Uint64("from", 0, "觀測起點（步數）")
	to := flag.Uint64("to", 0, "觀測終點（步數）")
	name := flag.String("name", "Jamestown", "要追的名稱字串")
	rx0 := flag.Int("rx0", 140, "標籤矩形左")
	ry0 := flag.Int("ry0", 130, "標籤矩形上")
	rx1 := flag.Int("rx1", 200, "標籤矩形右（含）")
	ry1 := flag.Int("ry1", 148, "標籤矩形下（含）")
	stride := flag.Int("stride", 320, "監看區每列位元組數（地圖視窗緩衝區為 240）")
	yoff := flag.Int("yoff", 0, "監看區第 0 列對應的螢幕列")
	events := flag.Bool("events", false, "改為記錄每一串 0D21:00C6 連續讀字，以及其間 0D21:012C 對離屏地圖緩衝區（0x3BB00）與畫布（0x2CAE0）的寫入")
	allValue := flag.Int("all-value", -1, "≥0：改為監看整個 1MB 位址空間中寫入此值的所有寫入者（依 CS:IP 彙整位址範圍）")
	snaps := flag.String("snaps", "", "逗號分隔的步數：各存一份離屏地圖緩衝區（0x34AE0）、畫布（0x2CAE0）與 VGA（0xA0000）")
	base := flag.Uint("base", 0x2cae0, "監看的 320x200 畫面起點（0x2cae0 為離屏畫布，0xa0000 為 VGA 記憶體）")
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
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)

	canvas := uint32(*base)
	type read struct {
		Step uint64
		CSIP string
		Addr uint32
		Val  uint8
	}
	var reads []read
	writers := map[string]*writer{}
	var spans [][2]uint32 // 名稱字串在記憶體中的位置
	started := false
	var finish func() any
	start := func() {
		started = true
		needle := []byte(*name)
		for i := 0; i+len(needle) < len(m.Mem); {
			j := bytes.Index(m.Mem[i:], needle)
			if j < 0 {
				break
			}
			spans = append(spans, [2]uint32{uint32(i + j), uint32(i + j + len(needle))})
			i += j + 1
		}
		fmt.Printf("起點 %d：名稱字串 %d 處\n", m.Steps, len(spans))
		for _, sp := range spans {
			sp := sp
			m.WatchReads(sp[0], sp[1]-1, func(a uint32, v uint8) {
				if m.Steps < *from || m.Steps >= *to || len(reads) >= 4000 {
					return
				}
				cs, ip := m.CPU.OpAddr()
				reads = append(reads, read{m.Steps, fmt.Sprintf("%04X:%04X", cs, ip), a, v})
			})
		}
		if *events {
			type ev struct {
				Step, Last uint64
				Text       string
				Base       uint32
				Buf        string
				Writes     map[uint8]int
				OldColors  map[uint8]int
				Remaining  int
				Pixels     int
				firstOld   map[int]uint8
				lastVal    map[int]uint8
				Writers    map[string]int
				MinX, MinY int
				MaxX, MaxY int
			}
			var list []*ev
			var cur *ev
			var next uint32
			m.WatchReads(0x20000, 0x4ffff, func(a uint32, v uint8) {
				if m.Steps < *from || m.Steps >= *to {
					return
				}
				cs, ip := m.CPU.OpAddr()
				if cs != 0x0d21 || ip != 0x00c6 || uint32(m.CPU.Seg[golem.SS])*16+uint32(m.CPU.R[golem.BX]) != a {
					return
				}
				if cur == nil || a != next || m.Steps-cur.Last > 200000 {
					cur = &ev{Step: m.Steps, Base: a, Writes: map[uint8]int{}, OldColors: map[uint8]int{}, firstOld: map[int]uint8{}, lastVal: map[int]uint8{}, Writers: map[string]int{}, MinX: 1 << 20, MinY: 1 << 20, MaxX: -1, MaxY: -1}
					list = append(list, cur)
				}
				if v != 0 {
					cur.Text += string(rune(v))
					next, cur.Last = a+1, m.Steps
				} else {
					cur.Last = m.Steps
					cur = nil
				}
			})
			// dosgolem 只有單一寫入監看：一個範圍涵蓋畫布（0x2CAE0）與離屏地圖緩衝區（0x3BB00）。
			m.WatchWrites(0x2cae0, 0x3bb00+64000-1, func(a uint32, old, value uint8) {
				if m.Steps < *from || m.Steps >= *to || cur == nil || old == value {
					return
				}
				name, base := "canvas", uint32(0x2cae0)
				if a >= 0x3bb00 {
					name, base = "buf", 0x3bb00
				} else if a >= 0x2cae0+64000 {
					return
				}
				cs, ip := m.CPU.OpAddr()
				cur.Writers[fmt.Sprintf("%s %04X:%04X", name, cs, ip)]++
				if cs != 0x0d21 || ip != 0x012c {
					return
				}
				i := int(a - base)
				if _, seen := cur.firstOld[int(a)]; !seen {
					cur.firstOld[int(a)] = old
					cur.OldColors[old]++
				}
				cur.lastVal[int(a)] = value
				x, y := i%320, i/320
				cur.Buf = name
				cur.Writes[value]++
				cur.MinX, cur.MinY, cur.MaxX, cur.MaxY = min(cur.MinX, x), min(cur.MinY, y), max(cur.MaxX, x), max(cur.MaxY, y)
			})
			finish = func() any {
				for _, e := range list {
					e.Pixels = len(e.lastVal)
					for a, v := range e.lastVal {
						if m.Mem[a] == v {
							e.Remaining++
						}
					}
				}
				return list
			}
			return
		}
		if *allValue >= 0 {
			type span struct {
				CSIP        string
				Count       int
				First, Last uint64
				MinA, MaxA  uint32
			}
			all := map[string]*span{}
			m.WatchWrites(0, 0xfffff, func(a uint32, old, value uint8) {
				if m.Steps < *from || m.Steps >= *to || old == value || int(value) != *allValue {
					return
				}
				cs, ip := m.CPU.OpAddr()
				key := fmt.Sprintf("%04X:%04X", cs, ip)
				sp := all[key]
				if sp == nil {
					sp = &span{CSIP: key, First: m.Steps, MinA: a, MaxA: a}
					all[key] = sp
				}
				sp.Count++
				sp.Last = m.Steps
				sp.MinA, sp.MaxA = min(sp.MinA, a), max(sp.MaxA, a)
			})
			finish = func() any {
				l := make([]*span, 0, len(all))
				for _, v := range all {
					l = append(l, v)
				}
				sort.Slice(l, func(i, j int) bool { return l[i].First < l[j].First })
				return l
			}
			return
		}
		m.WatchWrites(canvas, canvas+64000-1, func(a uint32, old, value uint8) {
			if m.Steps < *from || m.Steps >= *to || old == value {
				return
			}
			i := int(a - canvas)
			x, y := i%*stride, i/(*stride)+*yoff
			if x < *rx0 || x > *rx1 || y < *ry0 || y > *ry1 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			key := fmt.Sprintf("%04X:%04X", cs, ip)
			w := writers[key]
			if w == nil {
				w = &writer{CSIP: key, Values: map[uint8]int{}, First: m.Steps, MinX: x, MinY: y, MaxX: x, MaxY: y}
				writers[key] = w
			}
			w.Count++
			w.Values[value]++
			w.Last = m.Steps
			w.MinX, w.MinY, w.MaxX, w.MaxY = min(w.MinX, x), min(w.MinY, y), max(w.MaxX, x), max(w.MaxY, y)
		})
	}
	var snapAt []uint64
	for _, f := range strings.Split(*snaps, ",") {
		if f != "" {
			n, err := strconv.ParseUint(f, 10, 64)
			must(err)
			snapAt = append(snapAt, n)
		}
	}
	sort.Slice(snapAt, func(i, j int) bool { return snapAt[i] < snapAt[j] })
	dump := func() {
		for _, region := range []struct {
			name string
			base uint32
		}{{"buf", 0x34ae0}, {"canvas", 0x2cae0}, {"vga", 0xa0000}} {
			must(os.WriteFile(fmt.Sprintf("%s.snap-%d.%s", *out, m.Steps, region.name), m.Mem[region.base:region.base+64000], 0644))
		}
	}
	advance := func(target uint64) {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			if !started && m.Steps >= *from {
				start()
			}
			for len(snapAt) > 0 && m.Steps >= snapAt[0] {
				dump()
				snapAt = snapAt[1:]
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
	for _, e := range rp.Inputs {
		if e.Step >= *to {
			break
		}
		advance(e.Step)
		apply(e)
	}
	advance(*to)
	wl := make([]*writer, 0, len(writers))
	for _, w := range writers {
		wl = append(wl, w)
	}
	sort.Slice(wl, func(i, j int) bool { return wl[i].First < wl[j].First })
	// 名稱讀取依 CS:IP 彙整。
	type agg struct {
		CSIP        string
		Count       int
		First, Last uint64
		Addrs       []uint32
	}
	byIP := map[string]*agg{}
	for _, r := range reads {
		a := byIP[r.CSIP]
		if a == nil {
			a = &agg{CSIP: r.CSIP, First: r.Step}
			byIP[r.CSIP] = a
		}
		a.Count++
		a.Last = r.Step
		if len(a.Addrs) < 12 {
			a.Addrs = append(a.Addrs, r.Addr)
		}
	}
	al := make([]*agg, 0, len(byIP))
	for _, a := range byIP {
		al = append(al, a)
	}
	sort.Slice(al, func(i, j int) bool { return al[i].First < al[j].First })
	if finish != nil {
		res := map[string]any{"window": []uint64{*from, *to}, "value": *allValue, "writers": finish()}
		b, err := json.MarshalIndent(res, "", " ")
		must(err)
		must(os.WriteFile(*out, append(b, '\n'), 0644))
		fmt.Println("完成：全位址空間寫入者彙整")
		return
	}
	res := map[string]any{"name": *name, "spans": spans, "window": []uint64{*from, *to}, "rect": []int{*rx0, *ry0, *rx1, *ry1},
		"name_readers": al, "rect_writers": wl, "first_reads": reads[:min(len(reads), 60)]}
	b, err := json.MarshalIndent(res, "", " ")
	must(err)
	must(os.WriteFile(*out, append(b, '\n'), 0644))
	fmt.Printf("完成：名稱讀取 %d 筆（%d 個 CS:IP），矩形寫入者 %d 個\n", len(reads), len(al), len(wl))
}
