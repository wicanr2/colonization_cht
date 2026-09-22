// 研究探針：只讀觀測記憶體與指令，不改寫遊戲文字或控制流。
// 在容器內的 dosgolem 暫存源碼副本建置，不放進共用執行器。
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/wicanr2/dosgolem/internal/cpu"
	"github.com/wicanr2/dosgolem/internal/dos"
	"github.com/wicanr2/dosgolem/internal/machine"
	"github.com/wicanr2/dosgolem/internal/state"
)

func main() {
	input := flag.String("state", "", "輸入磁碟快照")
	root := flag.String("root", "/game", "唯讀原版目錄")
	out := flag.String("out", "/out/goal054-text-reads.json", "觀測紀錄")
	lo := flag.Uint("lo", 0x6f23f, "線性讀取位址")
	hi := flag.Uint("hi", 0x6f240, "線性讀取終點")
	end := flag.Uint64("end", 30000001, "停止步數")
	from := flag.Uint64("from", 0, "開始觀測步數")
	click := flag.Uint64("click", 12000001, "開場左鍵步數；0 不送")
	prefix := flag.String("prefix", "Start a Game", "只記錄此來源前綴")
	capture := flag.Bool("capture-text", false, "擷取已觀測 937C:0538 字串繪製前後")
	moveAway := flag.Uint64("move-away", 0, "正常移動游標至 (16,16) 的步數；0 不移動")
	flag.Parse()
	m := machine.New()
	if *input == "" {
		exe, err := os.ReadFile(*root + "/OPENING.EXE")
		must(err)
		must(m.LoadEXE(exe))
		m.Write8(uint32(machine.PSPSeg)*16+0x80, 2)
		m.WriteBytes(uint32(machine.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	}
	d := dos.New(m, *root)
	d.Install()
	defer d.Close()
	if *input != "" {
		must(state.Load(*input, m, d))
	}
	d.Root = *root
	m.SetSoundBlasterPro(true)
	var records []any
	var events []any
	active := false
	var retIP uint16
	var before []byte
	var event map[string]any
	var startCS, startIP uint16
	var startStep uint64
	var regs [8]uint16
	var segs [4]uint16
	m.WatchReads(uint32(*lo), uint32(*hi), func(a uint32, v uint8) {
		if startStep < *from || len(records) >= 10000 || !bytes.HasPrefix(m.Mem[*lo:], []byte(*prefix)) {
			return
		}
		sp := uint32(segs[cpu.SS])*16 + uint32(regs[cpu.SP])
		records = append(records, map[string]any{"step": startStep, "ip": fmt.Sprintf("%04X:%04X", startCS, startIP), "decoded_ip": fmt.Sprintf("%04X:%04X", m.CPU.Seg[cpu.CS], m.CPU.IP), "address": a, "value": v, "registers": regs, "segments": segs, "stack": fmt.Sprintf("%x", m.Mem[sp:sp+32])})
	})
	phase, polls := 0, 0
	for m.Steps < *end && !d.Exited && !m.CPU.Halted {
		if *input == "" && m.Steps == 3000000 {
			d.PushKey(dos.Key{Scan: 0x1c, ASCII: 13})
		}
		if *moveAway > 0 && m.Steps == *moveAway {
			d.MoveMouse(16, 16)
		}
		if *click > 0 && m.Steps == *click {
			d.MoveMouse(160, 100)
			polls = len(d.Mouse.Polls)
			phase = 1
		}
		if phase == 1 && len(d.Mouse.Polls)-polls >= 2 {
			d.PressMouse(0)
			polls = len(d.Mouse.Polls)
			phase = 2
		}
		if phase == 2 && len(d.Mouse.Polls)-polls >= 1 {
			d.ReleaseMouse(0)
			phase = 3
		}
		startCS, startIP, startStep = m.CPU.Seg[cpu.CS], m.CPU.IP, m.Steps
		regs, segs = m.CPU.R, m.CPU.Seg
		if active && startCS == 0x937c && startIP == retIP {
			path := fmt.Sprintf("%s.event%d", *out, len(events))
			must(os.WriteFile(path+".before", before, 0644))
			must(os.WriteFile(path+".after", m.Mem, 0644))
			event["return_step"] = startStep
			event["return_ip"] = fmt.Sprintf("%04X:%04X", startCS, startIP)
			event["capture"] = path
			events = append(events, event)
			active = false
		}
		if *capture && !active && len(events) < 5 && startCS == 0x937c && startIP == 0x0538 {
			sp := uint32(segs[cpu.SS])*16 + uint32(regs[cpu.SP])
			word := func(a uint32) uint16 { return uint16(m.Mem[a]) | uint16(m.Mem[a+1])<<8 }
			off, seg := word(sp+2), word(sp+4)
			a := uint32(seg)*16 + uint32(off)
			if bytes.HasPrefix(m.Mem[a:], []byte("Start a Game in NEW WORLD")) {
				active = true
				retIP = word(sp)
				before = append([]byte(nil), m.Mem...)
				event = map[string]any{"entry_step": startStep, "entry_ip": "937C:0538", "source": fmt.Sprintf("%04X:%04X", seg, off), "source_hex": fmt.Sprintf("%x", m.Mem[a:a+25]), "registers": regs, "segments": segs, "stack": fmt.Sprintf("%x", m.Mem[sp:sp+32])}
			}
		}
		must(m.Step())
	}
	m.WatchReads(0, 0, nil)
	result := map[string]any{"state": *input, "lo": *lo, "hi": *hi, "end": m.Steps, "exited": d.Exited, "records": records, "events": events, "end_ip": fmt.Sprintf("%04X:%04X", m.CPU.Seg[cpu.CS], m.CPU.IP), "opened": d.Opened}
	data, err := json.MarshalIndent(result, "", "  ")
	must(err)
	must(os.WriteFile(*out, append(data, '\n'), 0644))
	must(os.WriteFile(*out+".memory", m.Mem, 0644))
	must(os.WriteFile(*out+".idx", m.Mem[0xa0000:0xafa00], 0644))
	must(os.WriteFile(*out+".pal", m.DAC[:], 0644))
	fmt.Printf("記錄 %d 筆，終點 #%d\n", len(records), m.Steps)
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
