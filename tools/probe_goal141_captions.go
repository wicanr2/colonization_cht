// 目標141可丟棄探針：沿英格蘭正常玩家路徑，記錄 @BUILD1～10 開場字幕的原版讀字、改色、印前／印後底圖與逐幀真 VGA 同步。
// 原版只讀；原始畫布、事件與完整狀態只存 workplace。
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

type input141 struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
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
	Reads        int
	Writes       int
	Colors       map[uint8]int
	MinX, MinY   int
	MaxX, MaxY   int
	BeforeSHA    string
	AfterSHA     string
	OtherWriters map[string]int
	OtherBoxes   map[string][4]int // 目標142：其他寫入者在本筆印字期間的範圍 (minX,minY,maxX,maxY)
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
	// 5c14…：目標132錄製路徑（85.2M 多一次 Enter，第四頁後跳過其餘字幕）；1762…：同路徑去掉該鍵，十張字幕全顯示。
	if h := sha141(inputBytes); h != "5c143497e6425f38495216f62fe582aa2b035a1afdb7351852dc50126ed487bc" &&
		h != "17627777dcdf69f56d7d98bca3ea4a0f1843057b8483bc8ee5462386c6167662" &&
		h != "de60e124d18e4c3c08582abd67a7cb7ba4cfb27be94014189dfa77597ecb6d08" { // 目標142：同路徑改選第一張難度卡（Discoverer），600M 按 Enter 關 help，終點 700M
		panic("輸入收據版本不符")
	}
	var replay replay141
	must141(json.Unmarshal(inputBytes, &replay))
	m := golem.New()
	must141(m.LoadEXE(file141(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	// @BUILD1 約在 78～89M 印字；最後一張字幕之後 1225.4M 才有玩家左移。
	const start uint64 = 76000000
	stop := uint64(1225000000)
	if replay.End > start && replay.End < stop {
		stop = replay.End
	}
	prints := []*print141{}
	var cur *print141
	frames := []map[string]any{}
	lastFrameKey := ""
	otherWrites := map[string]int{}
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
			if cur == nil || a != cur.Next || m.Steps-cur.Last > 200000 {
				b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
				cur = &print141{Start: m.Steps, Base: a, Colors: map[uint8]int{},
					MinX: 320, MinY: 200, MaxX: -1, MaxY: -1, BeforeSHA: sha141(b), OtherWriters: map[string]int{}, OtherBoxes: map[string][4]int{}}
				prints = append(prints, cur)
				if len(prints) > 4000 {
					panic("印字事件超出上限")
				}
				must141(os.WriteFile(fmt.Sprintf("%s.print-%d.before.canvas", *out, m.Steps), b, 0644))
			}
			if cur.Reads%2 == 0 {
				cur.Text = append(cur.Text, value)
			}
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
			cur.Writes++
			cur.Colors[value]++
			cur.MinX, cur.MinY = min(cur.MinX, x), min(cur.MinY, y)
			cur.MaxX, cur.MaxY = max(cur.MaxX, x), max(cur.MaxY, y)
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
				panic("畫格變化超出上限")
			}
			frames = append(frames, map[string]any{"s": m.Steps, "frame": m.Frames, "mode": m.VideoMode(),
				"canvas": sha141(base), "vga": sha141(indexed), "same": same, "pal": sha141(m.DAC[:])})
		})
	}
	advance := func(target uint64) {
		for m.Steps < target && !d.Exited && !m.CPU.Halted {
			must141(m.Step())
			// 印字結束 20 萬步後記錄印後底圖一次。
			if cur != nil && cur.AfterSHA == "" && m.Steps-cur.Last == 200000 {
				b := append([]byte(nil), m.Mem[canvas:canvas+64000]...)
				cur.AfterSHA = sha141(b)
				must141(os.WriteFile(fmt.Sprintf("%s.print-%d.after.canvas", *out, cur.Start), b, 0644))
			}
		}
		if m.Steps != target {
			panic("原版提前結束")
		}
	}
	for _, e := range replay.Inputs {
		if e.Step >= stop {
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
			panic("非法輸入事件")
		}
	}
	advance(stop)
	must141(os.WriteFile(*out+".final.idx", m.Indexed(), 0644))
	must141(os.WriteFile(*out+".final.pal", m.DAC[:], 0644))
	state := map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks, "frames": m.Frames,
		"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags,
		"memory_sha256": sha141(m.Mem), "indexed_sha256": sha141(m.Indexed()),
		"palette_sha256": sha141(m.DAC[:]), "canvas_sha256": sha141(m.Mem[canvas : canvas+64000])}
	result := map[string]any{"version": "goal141-captions-v1", "control": *control,
		"address_space": "DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas; file offsets",
		"input_sha256":  sha141(inputBytes), "input_hashes": wants, "window": []uint64{start, stop},
		"prints": prints, "frames": frames, "other_writes": otherWrites, "opened": d.Opened, "state": state}
	b, err := json.Marshal(result)
	must141(err)
	must141(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("字幕探針：印字 %d、畫格變化 %d、狀態 %s\n", len(prints), len(frames), state["memory_sha256"])
}
