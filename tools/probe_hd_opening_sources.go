// 規格069 R82 DRAFT：開場來源樣本；輸出只准本機/out，不授予完整所有權或HD信用。
package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

func hash(b []byte) string { v := sha256.Sum256(b); return hex.EncodeToString(v[:]) }
func need(e error) {
	if e != nil {
		panic(e)
	}
}
func read(f string) []byte { b, e := os.ReadFile(f); need(e); return b }
func put(f string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	need(e)
	need(os.WriteFile(f, append(b, '\n'), 0644))
}
func main() {
	game := flag.String("game", "/game", "唯讀原版目錄")
	decoded := flag.String("decoded", "", "既有本機解碼pixels目錄")
	output := flag.String("out", "", "新的/out內研究輸出目錄")
	control := flag.Bool("control", false, "停用所有記憶體監看，其他輸入與快照相同")
	vgaSamples := flag.Bool("vga-samples", false, "另記VGA入口樣本；正式來源模型仍需自行重建")
	flag.Parse()
	if _, e := os.Stat("/.dockerenv"); e != nil || os.Geteuid() == 0 {
		panic("Docker with non-root user required")
	}
	out, e := filepath.Abs(*output)
	need(e)
	if !strings.HasPrefix(out, "/out/") || *decoded == "" || flag.NArg() != 0 {
		panic("explicit private output/decoded paths required")
	}
	for _, name := range []string{"OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK"} {
		if _, e := os.Stat(filepath.Join(*game, name)); os.IsNotExist(e) {
			fmt.Println("SKIP: missing legal original", name)
			os.Exit(77)
		}
	}
	for _, name := range []string{"1092.idx", "1179.idx"} {
		if _, e := os.Stat(filepath.Join(*decoded, name)); os.IsNotExist(e) {
			fmt.Println("SKIP: missing legal decoded original", name)
			os.Exit(77)
		}
	}
	for name, want := range map[string]string{"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39", "OPENING.PIK": "80ea1dd4a00a4029052112882305e573bd7e20066eb095ceabe273a217689185", "OPENBORD.PIK": "53f73ae336b5eaca30fa190ec9059426712de6c9c0c181d085814d45c96dab03"} {
		if hash(read(filepath.Join(*game, name))) != want {
			panic("original fingerprint: " + name)
		}
	}
	need(os.Mkdir(out, 0755))
	m := golem.New()
	exe := read(filepath.Join(*game, "OPENING.EXE"))
	need(m.LoadEXE(exe))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *game)
	d.Scratch = out
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		panic("digital")
	}
	m.EnableOPLSynth(true)
	raws := map[string][]byte{"OPENBORD.PIK": read(filepath.Join(*decoded, "1092.idx")), "OPENING.PIK": read(filepath.Join(*decoded, "1179.idx"))}
	if hash(raws["OPENING.PIK"]) != "9aa042dfb838820ea8d7d1c9953478f44dd7d8f85db4d5cc4aa0bb9bb0006b95" || hash(raws["OPENBORD.PIK"]) != "ee23b1d787958481210fb6c328ccc067805bdbd8d83300c5d8157dd40cf90816" {
		panic("decoded original fingerprint")
	}
	file, e := os.Create(filepath.Join(out, "vga-writes.jsonl"))
	need(e)
	log := bufio.NewWriterSize(file, 1<<20)
	events := 0
	sites := map[uint32]uint64{}
	samples := map[[3]uint32]int{}
	vgaWrites := uint64(0)
	if !*control {
		write := func(_ *golem.Machine, a uint32, o, v byte) {
			mainWrite := a >= 115760 && a < 115760+64000
			vgaWrite := a >= 0xa0000 && a < 0xa0000+64000
			sourceWrite := a >= 230960 && a < 230960+126720
			if !mainWrite && !vgaWrite && !sourceWrite {
				return
			}
			if vgaWrite {
				vgaWrites++
			}
			cs, ip := m.CPU.OpAddr()
			key := uint32(cs)<<16 | uint32(ip)
			sites[key]++
			delta := int(a) - (int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI]))
			src := int(m.CPU.Seg[golem.DS])*16 + int(m.CPU.R[golem.SI]) + delta
			kind := uint32(0)
			if src >= 115760 && src < 115760+64000 {
				kind = 1
			}
			if src >= 230960 && src < 230960+126720 {
				kind = 2
			}
			dest := uint32(0)
			if mainWrite {
				dest = 1
			}
			if sourceWrite {
				dest = 2
			}
			sampleKey := [3]uint32{key, kind, dest}
			if samples[sampleKey] >= 64 {
				return
			}
			samples[sampleKey]++

			c := m.CPU
			pc := int(cs)*16 + int(ip)
			fmt.Fprintf(log, "[%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%q]\n", m.Steps, a, o, v, cs, ip, c.Seg[golem.DS], c.R[golem.SI], c.Seg[golem.ES], c.R[golem.DI], c.R[golem.AX], c.R[golem.CX], c.Flags, fmt.Sprintf("%x", m.Mem[pc:pc+16]))
			events++
		}
		m.WatchWrite(115760, 115760+63999, write)
		m.WatchWrite(230960, 230960+126719, write)
		if *vgaSamples {
			m.WatchWrite(0xa0000, 0xa0000+63999, write)
		}
	}
	points := []map[string]any{}
	fail := ""
	for m.Steps < 16000000 {
		if m.Steps == 800000 {
			d.PushKey(golem.Key{ASCII: 13, Scan: 0x1c})
		}
		if m.Steps%200000 == 0 {
			refs := map[string]int{}
			for name, raw := range raws {
				refs[name] = bytes.Index(m.Mem, raw)
			}
			c := m.CPU
			s := map[string]any{"step": m.Steps, "mode": m.VideoMode(), "memory_sha256": hash(m.Mem), "indexed_sha256": hash(m.Indexed()), "palette_sha256": hash(m.DAC[:]), "registers": c.R, "segments": c.Seg, "ip": c.IP, "flags": c.Flags, "cycles": c.Cycles, "full_raw_ram_offsets": refs}
			stem := filepath.Join(out, fmt.Sprintf("point-%08d", m.Steps))
			need(os.WriteFile(stem+".memory", m.Mem, 0644))
			need(os.WriteFile(stem+".idx", m.Indexed(), 0644))
			need(os.WriteFile(stem+".palette", m.DAC[:], 0644))
			if m.VideoMode() == 0x13 {
				im := image.NewRGBA(image.Rect(0, 0, 320, 200))
				for k, v := range m.Indexed() {
					i := int(v) * 3
					r, g, b := m.DAC[i], m.DAC[i+1], m.DAC[i+2]
					im.SetRGBA(k%320, k/320, color.RGBA{r<<2 | r>>4, g<<2 | g>>4, b<<2 | b>>4, 255})
				}
				f, e := os.Create(stem + ".png")
				need(e)
				need(png.Encode(f, im))
				need(f.Close())
			}
			points = append(points, s)
			fmt.Println("POINT", m.Steps, m.VideoMode(), refs)
		}
		if e := m.Step(); e != nil {
			fail = e.Error()
			break
		}
	}
	need(log.Flush())
	need(file.Close())
	put(filepath.Join(out, "check.json"), map[string]any{"result": "DRAFT_OPENING_COLD_NATIVE_OBSERVATION", "production_connected": false, "control": *control, "go_version": runtime.Version(), "binary_sha256": hash(read(os.Args[0])), "vga_observation_enabled": *vgaSamples, "original_exe_sha256": hash(exe), "original_pik_sha256": map[string]string{"OPENING.PIK": hash(read(filepath.Join(*game, "OPENING.PIK"))), "OPENBORD.PIK": hash(read(filepath.Join(*game, "OPENBORD.PIK")))}, "end": m.Steps, "events": events, "vga_writes_seen": vgaWrites, "log_scope": "At most 64 write samples per CS:IP, physical source region and destination; main/source memory observed, VGA optional. Physical region labels do not establish source identity before a complete native bitmap match. Remaining observed writes counted, not logged. Discovery only, no full ownership/parity credit.", "write_sites": sites, "opened": d.Opened, "reads": d.Reads, "points": points, "error": fail, "input_count": 1, "inputs": []map[string]any{{"step": 800000, "kind": "enter"}}, "address_space": "dosgolem real-mode CS:IP and 20-bit linear RAM", "limitations": []string{"Read-only sampled discovery; no complete write trace, source ownership or production credit", "Normal Enter at 800000 along established goal146 opening path; no direct entry or state injection"}})
}
