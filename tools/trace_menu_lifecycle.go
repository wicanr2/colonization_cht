// 可丟棄研究探針：正常冷啟動與滑鼠輸入，僅觀測既知入口，不改原版控制流。
package main

import (
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/wicanr2/dosgolem/internal/cpu"
	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
	"os"
)

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func hash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func main() {
	root := flag.String("root", "/game", "唯讀原版目錄")
	out := flag.String("out", "/out/goal056-lifecycle", "輸出前綴")
	end := flag.Uint64("end", 45000001, "有界停止步數")
	flag.Parse()
	m := machine.New()
	exe, err := os.ReadFile(*root + "/OPENING.EXE")
	must(err)
	must(m.LoadEXE(exe))
	m.Write8(uint32(machine.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(machine.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := dos.New(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	var events []map[string]any
	var frames []map[string]any
	var inputs []map[string]any
	var active map[string]any
	var before []byte
	var retIP, retSP uint16
	canvas := func() []byte { return m.Mem[0x2cae0 : 0x2cae0+64000] }
	frame := func(label string) {
		path := *out + "." + label
		idx := append([]byte(nil), m.Mem[0xa0000:0xafa00]...)
		must(os.WriteFile(path+".idx", idx, 0644))
		must(os.WriteFile(path+".pal", m.DAC[:], 0644))
		must(os.WriteFile(path+".canvas", canvas(), 0644))
		frames = append(frames, map[string]any{"label": label, "step": m.Steps, "prefix": path, "frame_sha256": hash(idx), "palette_sha256": hash(m.DAC[:]), "canvas_sha256": hash(canvas())})
	}
	phase, polls := 0, 0
	for m.Steps < *end && !d.Exited && !m.CPU.Halted {
		if m.Steps >= 31050000 && m.Steps <= 31350000 && m.Steps%50000 == 0 {
			frame(fmt.Sprintf("click-%d", m.Steps))
		}
		switch m.Steps {
		case 3000000:
			d.PushKey(dos.Key{Scan: 0x1c, ASCII: 13})
			inputs = append(inputs, map[string]any{"step": m.Steps, "kind": "Enter"})
		case 12000001, 31000001:
			x, y := 160, 100
			if m.Steps == 31000001 {
				x, y = 128, 110
			}
			d.MoveMouse(x, y)
			polls = len(d.Mouse.Polls)
			phase = 1
			inputs = append(inputs, map[string]any{"step": m.Steps, "kind": "click-premove", "x": x, "y": y})
		case 25000000, 29000000:
			d.MoveMouse(16, 16)
			inputs = append(inputs, map[string]any{"step": m.Steps, "kind": "move", "x": 16, "y": 16})
		case 27000000:
			d.MoveMouse(128, 110)
			inputs = append(inputs, map[string]any{"step": m.Steps, "kind": "move", "x": 128, "y": 110})
		case 24000000:
			frame("menu-initial")
		case 26000000:
			frame("menu-clear")
		case 28000000:
			frame("menu-hover")
		case 30000000:
			frame("menu-away")
		case 40000000:
			frame("difficulty")
		case 43000000:
			d.MoveMouse(16, 16)
			inputs = append(inputs, map[string]any{"step": m.Steps, "kind": "move", "x": 16, "y": 16})
		case 45000000:
			frame("difficulty-clear")
		}
		if phase == 1 && len(d.Mouse.Polls)-polls >= 2 {
			d.PressMouse(0)
			polls = len(d.Mouse.Polls)
			phase = 2
			inputs = append(inputs, map[string]any{"step": m.Steps, "kind": "press"})
		}
		if phase == 2 && len(d.Mouse.Polls)-polls >= 1 {
			d.ReleaseMouse(0)
			phase = 3
			inputs = append(inputs, map[string]any{"step": m.Steps, "kind": "release"})
		}
		cs, ip, sp := m.CPU.Seg[cpu.CS], m.CPU.IP, m.CPU.R[cpu.SP]
		if active != nil && cs == 0x937c && ip == retIP {
			after := append([]byte(nil), canvas()...)
			path := fmt.Sprintf("%s.event%03d", *out, len(events))
			must(os.WriteFile(path+".before", before, 0644))
			must(os.WriteFile(path+".after", after, 0644))
			active["return_step"] = m.Steps
			active["return_ip"] = fmt.Sprintf("%04X:%04X", cs, ip)
			active["capture"] = path
			active["entry_sp"] = retSP
			active["return_sp"] = sp
			active["before_sha256"] = hash(before)
			active["after_sha256"] = hash(after)
			var changes []int
			colors := map[uint8]int{}
			minx, miny, maxx, maxy := 320, 200, -1, -1
			for i, v := range before {
				if v != after[i] {
					changes = append(changes, i)
					colors[after[i]]++
					x, y := i%320, i/320
					if x < minx {
						minx = x
					}
					if y < miny {
						miny = y
					}
					if x > maxx {
						maxx = x
					}
					if y > maxy {
						maxy = y
					}
				}
			}
			active["changed_indices"] = changes
			active["changed_colors"] = colors
			active["bbox_inclusive"] = []int{minx, miny, maxx, maxy}
			events = append(events, active)
			active = nil
		}
		if active == nil && len(events) < 256 && cs == 0x937c && ip == 0x0538 {
			addr := uint32(m.CPU.Seg[cpu.SS])*16 + uint32(sp)
			word := func(a uint32) uint16 { return uint16(m.Mem[a]) | uint16(m.Mem[a+1])<<8 }
			off, seg := word(addr+2), word(addr+4)
			paramOff, paramSeg := word(addr+6), word(addr+8)
			paramLinear := uint32(paramSeg)*16 + uint32(paramOff)
			p := uint32(seg)*16 + uint32(off)
			source := []byte{}
			terminated := false
			for i := uint32(0); i < 512 && p+i < uint32(len(m.Mem)); i++ {
				if m.Mem[p+i] == 0 {
					terminated = true
					break
				}
				source = append(source, m.Mem[p+i])
			}
			retIP, retSP = word(addr), sp
			before = append([]byte(nil), canvas()...)
			active = map[string]any{"entry_step": m.Steps, "entry_ip": "937C:0538", "near_return_candidate": fmt.Sprintf("937C:%04X", retIP), "source": fmt.Sprintf("%04X:%04X", seg, off), "source_hex": fmt.Sprintf("%x", source), "source_sha256": hash(source), "nul_terminated": terminated, "registers": m.CPU.R, "segments": m.CPU.Seg, "stack": fmt.Sprintf("%x", m.Mem[addr:addr+32])}
			// 僅保存原始定位與位元組；不替尚未驗證的欄位命名。
			active["stack_plus_6_8_pointer"] = fmt.Sprintf("%04X:%04X", paramSeg, paramOff)
			active["stack_plus_6_8_linear"] = paramLinear
			active["stack_plus_6_8_raw14_hex"] = fmt.Sprintf("%x", m.Mem[paramLinear:paramLinear+14])
			active["canvas_descriptor_linear"] = 0x1f448
			active["canvas_descriptor_raw14_hex"] = fmt.Sprintf("%x", m.Mem[0x1f448:0x1f448+14])
		}
		must(m.Step())
	}
	result := map[string]any{"events": events, "pending_event": active, "frames": frames, "inputs": inputs, "end": m.Steps, "exited": d.Exited, "opened": d.Opened, "canvas_linear": 0x2cae0, "canvas_bytes": 64000}
	data, err := json.MarshalIndent(result, "", "  ")
	must(err)
	must(os.WriteFile(*out+".json", append(data, '\n'), 0644))
	fmt.Printf("完成 %d 印字事件、%d 畫面，終點 #%d\n", len(events), len(frames), m.Steps)
}
