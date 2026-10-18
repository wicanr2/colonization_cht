// 規格069 R82／R83／R85：獨立原版來源模型；輸出只准本機/out，不替正式GUI授予HD信用。
package main

import (
	"bufio"
	"bytes"
	"crypto/sha256"
	"encoding/binary"
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
	"sort"
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
	sourceModel := flag.Bool("source-model", false, "逐寫重建完整開場PIK來源，保留私有模型")
	normalExit := flag.Bool("normal-exit", false, "沿六筆已驗正常輸入離開開場")
	inputFile := flag.String("inputs", "", "當次正常GUI輸入JSON；只接受已支援的輸入")
	saveSeed := flag.String("save-seed", "", "當次GUI使用的合法COLONY09.SAV；只複製至私有輸出")

	sprites := flag.Bool("opening-sprites", false, "R83 DRAFT：另建開場SS與已發布來源，不安裝HD")
	catalog := flag.String("catalog", "", "R83固定原版全資產清冊")
	sampleEvery := flag.Uint64("sample-every", 200000, "R84研究快照間隔；200000的倍數，最多10000000")
	allSprites := flag.Bool("all-opening-sprites", false, "觀測全部指紋吻合的OPEN及MPS片頭SS；不授予HD信用")
	writeSamples := flag.Bool("write-samples", true, "記錄寫入入口樣本；長流程可停用，來源模型仍持續")
	publicationFile := flag.String("publication-windows", "", "半開區間JSON [[start,end],...]；省略時持續觀測發布，空陣列停用")
	stepFile := flag.String("sample-steps", "", "額外快照步數JSON，須為遞增的200000倍數")
	flag.Parse()
	var publicationEdges []uint64
	if *publicationFile != "" {
		var windows [][2]uint64
		need(json.Unmarshal(read(*publicationFile), &windows))
		if len(windows) > 128 {
			panic("too many publication windows")
		}
		for _, w := range windows {
			if w[0] >= w[1] || w[1] > 800000000 || w[0]%200000 != 0 || w[1]%200000 != 0 || len(publicationEdges) > 0 && w[0] <= publicationEdges[len(publicationEdges)-1] {
				panic("invalid publication windows")
			}
			publicationEdges = append(publicationEdges, w[0], w[1])
		}
	}
	extraSteps := map[uint64]bool{}
	if *stepFile != "" {
		var steps []uint64
		need(json.Unmarshal(read(*stepFile), &steps))
		if len(steps) > 128 {
			panic("too many snapshot steps")
		}
		for i, step := range steps {
			if step >= 800000000 || step%200000 != 0 || i > 0 && step <= steps[i-1] {
				panic("invalid snapshot steps")
			}
			extraSteps[step] = true
		}
	}
	if _, e := os.Stat("/.dockerenv"); e != nil || os.Geteuid() == 0 {
		panic("Docker with non-root user required")
	}
	out, e := filepath.Abs(*output)
	need(e)
	if !strings.HasPrefix(out, "/out/") || *decoded == "" || flag.NArg() != 0 {
		panic("explicit private output/decoded paths required")
	}
	if *sampleEvery == 0 || *sampleEvery%200000 != 0 || *sampleEvery > 10000000 {
		panic("sample-every must be a positive multiple of 200000, at most 10000000")
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
	if *sprites {
		if !*sourceModel || *catalog == "" {
			panic("opening-sprites requires source-model and catalog")
		}
		for n, want := range map[string]string{"OPENSHIP.SS": "eee07bfee9a7abf512d6bd9688409427149df3226edd024342871f41e143af10", "OPENSUN.SS": "639e0ff1eaf4fb4a9b649557c63658b0ba611caeb3ebf46da75affd342ed30bd"} {
			if hash(read(filepath.Join(*game, n))) != want {
				panic("opening sprite fingerprint: " + n)
			}
		}
		if hash(read(*catalog)) != "e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d" {
			panic("decoded catalog fingerprint")
		}
	}
	need(os.Mkdir(out, 0755))
	if *saveSeed != "" {
		seed := read(*saveSeed)
		if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
			panic("normal GUI seed fingerprint")
		}
		need(os.WriteFile(filepath.Join(out, "COLONY09.SAV"), seed, 0644))
	}
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
	model := &openingSourceModel{m: m, mapRaw: raws["OPENING.PIK"], borderRaw: raws["OPENBORD.PIK"]}
	if !*control && *sourceModel {
		m.WatchWrite(115760, 115760+63999, func(_ *golem.Machine, a uint32, o, v byte) { model.write(a, o, v) })
		m.WatchWrite(230960, 230960+126719, func(_ *golem.Machine, a uint32, o, v byte) { model.write(a, o, v) })
	}
	var actor *openingActorProbe
	if *sprites {
		actor = newOpeningActorProbe(m, *decoded, *catalog, *game, *allSprites)
		actor.pic = model
		if !*control {
			actor.observePublication = *publicationFile == ""
			actor.publicationEdges = publicationEdges
			watcherInstalled := false
			m.SetBeforeInstruction(func() {
				actor.publicationWindow()
				if actor.observePublication && !watcherInstalled {
					m.WatchWrite(0xa0000, 0xafa00-1, func(_ *golem.Machine, a uint32, o, v byte) { actor.publish(a, o, v) })
					watcherInstalled = true
				}
				actor.before()
			})
			m.WatchWrite(115760, 115760+63999, func(_ *golem.Machine, a uint32, o, v byte) { actor.write(a, o, v) })
			// 區間外不保留發布來源信用；首次區間開始才掛入VGA監看。
		}
	}
	file, e := os.Create(filepath.Join(out, "vga-writes.jsonl"))
	need(e)
	log := bufio.NewWriterSize(file, 1<<20)
	events := 0
	sites := map[uint32]uint64{}
	samples := map[[3]uint32]int{}
	vgaWrites := uint64(0)
	if *writeSamples && !*control {
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

	inputs := []openingProbeInput{{Step: 800000, Kind: "enter"}}
	end := uint64(16000000)
	if *normalExit {
		end = 22400000
		inputs = []openingProbeInput{{Step: 0, Kind: "move", X: 160, Y: 96}, {Step: 200000, Kind: "move", X: 160, Y: 106}, {Step: 800000, Kind: "enter"}, {Step: 10200000, Kind: "move", X: 160, Y: 100}, {Step: 10600000, Kind: "press"}, {Step: 11200000, Kind: "release"}}
	}
	if *inputFile != "" {
		if *normalExit {
			panic("normal-exit and inputs are mutually exclusive")
		}
		var replay struct {
			Inputs []openingProbeInput
			End    uint64
		}
		need(json.Unmarshal(read(*inputFile), &replay))
		inputs, end = replay.Inputs, replay.End
	}
	if end == 0 || end > 800000000 || end%200000 != 0 {
		panic("bounded step-aligned replay end required")
	}
	for i, v := range inputs {
		if v.Step >= end || i > 0 && v.Step < inputs[i-1].Step {
			panic("unordered/out-of-range input")
		}
		switch v.Kind {
		case "move":
			if v.X < 0 || v.X >= 320 || v.Y < 0 || v.Y >= 200 {
				panic("mouse bounds")
			}
		case "press", "release":
			if v.Button < 0 || v.Button > 2 {
				panic("button bounds")
			}
		case "enter", "escape":
		default:
			panic("unsupported input")
		}
	}
	for step := range extraSteps {
		if step >= end {
			panic("snapshot outside replay")
		}
	}
	inputAt := 0
	for m.Steps < end {
		if actor != nil && !*control {
			actor.publicationWindow()
		}
		for inputAt < len(inputs) && inputs[inputAt].Step == m.Steps {
			v := inputs[inputAt]
			switch v.Kind {
			case "move":
				d.MoveMouse(v.X, v.Y)
			case "press":
				d.PressMouse(v.Button)
			case "release":
				d.ReleaseMouse(v.Button)
			case "enter":
				if !d.PushKeyNamed("Return") {
					panic("Return unsupported")
				}
			case "escape":
				if !d.PushKeyNamed("Escape") {
					panic("Escape unsupported")
				}
			}
			inputAt++
		}

		if m.Steps%*sampleEvery == 0 || extraSteps[m.Steps] {
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
			if !*control && *sourceModel {
				model.capture(out)
			}
			if actor != nil && !*control {
				actor.capture(out)
			}
			points = append(points, s)
			fmt.Println("POINT", m.Steps, m.VideoMode(), refs)
		}
		if e := m.Step(); e != nil {
			fail = e.Error()
			break
		}
	}
	if actor != nil {
		put(filepath.Join(out, "actors.json"), map[string]any{"state": "DRAFT", "all_opening_sprites": *allSprites, "publication_edges": publicationEdges, "entries": actor.entries, "calls": actor.calls, "points": actor.points, "verified_calls": actor.matched, "published_transfers": actor.publishedTransfers, "unknown_vga_revocations": actor.publishedUnknown, "same_value_vga_revocations": actor.publishedSame, "revoked": actor.revoked, "same_value_revoked": actor.same, "production_connected": false})
	}
	put(filepath.Join(out, "model.json"), model.receipt())
	need(log.Flush())
	need(file.Close())
	put(filepath.Join(out, "check.json"), map[string]any{"result": "DRAFT_OPENING_COLD_NATIVE_OBSERVATION", "production_connected": false, "control": *control, "go_version": runtime.Version(), "binary_sha256": hash(read(os.Args[0])), "vga_observation_enabled": *vgaSamples, "original_exe_sha256": hash(exe), "original_pik_sha256": map[string]string{"OPENING.PIK": hash(read(filepath.Join(*game, "OPENING.PIK"))), "OPENBORD.PIK": hash(read(filepath.Join(*game, "OPENBORD.PIK")))}, "end": m.Steps, "events": events, "vga_writes_seen": vgaWrites, "log_scope": "At most 64 write samples per CS:IP, physical source region and destination; main/source memory observed, VGA optional. Physical region labels do not establish source identity before a complete native bitmap match. Remaining observed writes counted, not logged. Discovery only, no full ownership/parity credit.", "write_sites": sites, "opened": d.Opened, "reads": d.Reads, "points": points, "error": fail, "input_count": len(inputs), "inputs": inputs, "sample_every": *sampleEvery, "source_model_enabled": *sourceModel, "opening_sprites_enabled": *sprites, "all_opening_sprites_enabled": *allSprites, "write_samples_enabled": *writeSamples, "publication_windows_file": *publicationFile, "publication_edges": publicationEdges, "extra_snapshot_steps": extraSteps, "address_space": "dosgolem real-mode CS:IP and 20-bit linear RAM", "limitations": []string{"Read-only sampled discovery; no complete write trace, source ownership or production credit", "Normal Enter at 800000 along established goal146 opening path; no direct entry or state injection"}})
}

type openingModelCell struct {
	kind  byte
	local uint32
	value byte
}
type openingSourceModel struct {
	m                                                                                       *golem.Machine
	mapRaw, borderRaw                                                                       []byte
	cells                                                                                   [64000]openingModelCell
	mapNext, borderNext                                                                     int
	mapValid                                                                                bool
	mapBirths, borderBirths, mapInvalidations, transfers, revocations, sameValueRevocations uint64
	maxMapLocal                                                                             uint32
	retired                                                                                 uint64
	births                                                                                  []map[string]any
	captures                                                                                []map[string]any
}

func (p *openingSourceModel) decoderKnown(cs, ip uint16) bool {
	code := ""
	if cs == 0xac2 && ip == 0x4f4 {
		code = "a4ebed33c94a7509adb210d1ed8be8d1"
	}
	if cs == 0xac2 && ip == 0x550 {
		code = "aae2faeb8fac0ac074323c0174058ac8"
	}
	if code == "" {
		return false
	}
	raw, _ := hex.DecodeString(code)
	at := int(cs)*16 + int(ip)
	return bytes.Equal(p.m.Mem[at:at+16], raw)
}
func (p *openingSourceModel) write(a uint32, old, value byte) {
	cs, ip := p.m.CPU.OpAddr()
	if a >= 230960 && a < 230960+126720 {
		if p.mapValid {
			p.mapValid = false
			p.mapInvalidations++
		}
		k := int(a) - 230960
		known := p.decoderKnown(cs, ip)
		if !known || k != p.mapNext || value != p.mapRaw[k] {
			p.mapNext = 0
		}
		if known && k == p.mapNext && value == p.mapRaw[k] {
			p.mapNext++
		}
		if p.mapNext == len(p.mapRaw) {
			if !bytes.Equal(p.m.Mem[230960:230960+126720], p.mapRaw) {
				panic("map final decode")
			}
			p.mapValid = true
			p.mapBirths++
			p.mapNext = 0
			p.births = append(p.births, map[string]any{"kind": "map", "step": p.m.Steps, "bytes": 126720, "native_sha256": hash(p.mapRaw)})
		}
		return
	}
	if a < 115760 || a >= 115760+64000 {
		return
	}
	k := int(a) - 115760
	prior := p.cells[k]
	p.cells[k] = openingModelCell{}
	known := p.decoderKnown(cs, ip)
	if !known || k != p.borderNext || value != p.borderRaw[k] {
		p.borderNext = 0
	}
	if known && k == p.borderNext && value == p.borderRaw[k] {
		p.borderNext++
	}
	if p.borderNext == len(p.borderRaw) {
		if !bytes.Equal(p.m.Mem[115760:115760+64000], p.borderRaw) {
			panic("border final decode")
		}
		for i, v := range p.borderRaw {
			p.cells[i] = openingModelCell{kind: 1, local: uint32(i), value: v}
		}
		p.borderBirths++
		p.borderNext = 0
		p.births = append(p.births, map[string]any{"kind": "border", "step": p.m.Steps, "bytes": 64000, "native_sha256": hash(p.borderRaw)})
		return
	}
	c := p.m.CPU
	pc := int(cs)*16 + int(ip)
	if cs == 0x3bd && ip == 0xc8 && p.mapValid && c.Flags&0x400 == 0 &&
		bytes.Equal(p.m.Mem[pc:pc+16], []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}) {
		delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
		src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
		if delta >= 0 && delta < 2 && int(c.R[golem.SI])+delta < 65536 && int(c.R[golem.DI])+delta < 65536 &&
			src >= 230960 && src < 230960+126720 && p.m.Mem[src] == value && p.mapRaw[src-230960] == value {
			local := uint32(src - 230960)
			p.cells[k] = openingModelCell{kind: 2, local: local, value: value}
			p.transfers++
			if local > p.maxMapLocal {
				p.maxMapLocal = local
			}
		}
	}
	if prior.kind != 0 && p.cells[k].kind == 0 {
		p.revocations++
		if old == value {
			p.sameValueRevocations++
		}
	}
}
func (p *openingSourceModel) capture(out string) {

	signature, _ := hex.DecodeString("f3a503f3790c81ee00808cd981c100088ed903fd4875e75d5f5e071fc9cb0000")
	live := bytes.Equal(p.m.Mem[0x5570+0x9f:0x5570+0x9f+32], signature)
	if !live {
		have := p.mapValid
		for _, c := range p.cells {
			have = have || c.kind != 0
		}
		if have {
			p.retired++
			clear(p.cells[:])
			p.mapValid = false
			p.mapNext = 0
			p.borderNext = 0
		}
	}
	counts := map[byte]int{}
	idx := p.m.Indexed()
	main := p.m.Mem[115760 : 115760+64000]
	for i, c := range p.cells {
		if c.kind == 0 {
			continue
		}
		raw := p.borderRaw
		if c.kind == 2 {
			raw = p.mapRaw
		}
		if int(c.local) >= len(raw) || c.value != raw[c.local] || main[i] != c.value {
			panic(fmt.Sprint("owner mismatch ", p.m.Steps, " ", i))
		}
		counts[c.kind]++
	}

	reason := ""
	if p.m.VideoMode() != 0x13 {
		reason = "mode"
	} else if !bytes.Equal(p.m.Mem[0x5570+0x9f:0x5570+0x9f+32], signature) {
		reason = "code"
	}
	if reason == "" && (!bytes.Equal(main, idx) || !bytes.Equal(p.m.Mem[0xa0000:0xa0000+64000], idx)) {
		reason = "surface"
	}
	if reason == "" && (hash(p.m.DAC[:]) != "b53fcec3d9bbe9af2e1d07566cd74d079dedce14f792788c7471f9e2ef0c6a54" || hash(p.m.Mem[0xafc00:0xaff00]) != "b53fcec3d9bbe9af2e1d07566cd74d079dedce14f792788c7471f9e2ef0c6a54") {
		reason = "palette"
	}
	row := map[string]any{"step": p.m.Steps, "owners": counts, "map_valid": p.mapValid, "guard_reason": reason, "paintable": reason == ""}
	{
		b := make([]byte, 64000*6)
		for i, c := range p.cells {
			at := i * 6
			b[at] = c.kind
			binary.LittleEndian.PutUint32(b[at+1:at+5], c.local)
			b[at+5] = c.value
		}
		file := fmt.Sprintf("model-%08d.owners", p.m.Steps)
		need(os.WriteFile(filepath.Join(out, file), b, 0644))
		row["owners_file"] = file
		row["owners_sha256"] = hash(b)
	}
	p.captures = append(p.captures, row)
}
func (p *openingSourceModel) receipt() map[string]any {
	return map[string]any{"state": "DRAFT", "production_connected": false, "retirements": p.retired, "map_births": p.mapBirths, "border_births": p.borderBirths, "map_invalidations": p.mapInvalidations, "map_transfers": p.transfers, "unknown_revocations": p.revocations, "same_value_revocations": p.sameValueRevocations, "max_map_local": p.maxMapLocal, "births": p.births, "points": p.captures, "owner_format": "private fixture only: kind u8, source local u32 little endian, native value u8; zero kind unknown"}
}

type openingProbeInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}

type openingActorFrame struct {
	ID            int    `json:"research_id"`
	File          string `json:"file"`
	FileSHA       string `json:"file_sha256"`
	Ordinal       int    `json:"ordinal"`
	Size          [2]int `json:"size"`
	EncodedLength int    `json:"encoded_length"`
	EncodedSHA    string `json:"encoded_sha256"`
	IndexedSHA    string `json:"indexed_sha256"`
	Opaque        int    `json:"opaque_pixels"`
	Transparent   byte   `json:"transparency_index"`
	Pixels        []byte `json:"-"`
}
type openingActorCell struct {
	ID, Local uint16
	Value     byte
	Under     openingModelCell
}
type openingActorProbe struct {
	observePublication                                  bool
	allSprites                                          bool
	publicationEdges                                    []uint64
	publicationEdge                                     int
	firstUnder                                          map[int]bool
	publishedActor                                      [64000]openingActorCell
	publishedPIC                                        [64000]openingModelCell
	publishedTransfers, publishedUnknown, publishedSame uint64

	pic   *openingSourceModel
	under []openingModelCell

	m                      *golem.Machine
	frames                 []openingActorFrame
	byID                   map[int]*openingActorFrame
	active                 map[string]any
	selected               *openingActorFrame
	x, y                   int
	retCS, retIP, sp       uint16
	start                  uint64
	writes                 map[int]byte
	counts                 map[int]int
	outside                bool
	cells                  [64000]openingActorCell
	entries, calls, points []map[string]any
	matched, revoked, same uint64
	writerCodes            map[uint16][]byte
}

func actorWords(m *golem.Machine, seg, off uint16, n int) []uint16 {
	at := int(seg)*16 + int(off)
	if int(off)+n*2 > 65536 || at+n*2 > len(m.Mem) {
		return nil
	}
	out := make([]uint16, n)
	for i := range out {
		out[i] = binary.LittleEndian.Uint16(m.Mem[at+i*2:])
	}
	return out
}
func newOpeningActorProbe(m *golem.Machine, decoded, catalog, game string, allSprites bool) *openingActorProbe {
	var cat struct {
		Frames []openingActorFrame
		Files  []struct {
			File string
			SHA  string `json:"sha256"`
		}
	}
	need(json.Unmarshal(read(catalog), &cat))
	files := map[string]string{}
	for _, f := range cat.Files {
		files[f.File] = f.SHA
	}
	checked := map[string]bool{}
	p := &openingActorProbe{m: m, allSprites: allSprites, byID: map[int]*openingActorFrame{}, writerCodes: map[uint16][]byte{}}
	for _, f := range cat.Frames {
		if (!strings.HasPrefix(f.File, "OPEN") && (!allSprites || f.File != "MPSLOGO.SS" && f.File != "MPSNAME.SS")) || !strings.HasSuffix(f.File, ".SS") || f.EncodedLength <= 0 || f.IndexedSHA == "" || f.Opaque == 0 {
			continue
		}
		if !checked[f.File] {
			if files[f.File] == "" || hash(read(filepath.Join(game, f.File))) != files[f.File] {
				panic("actor original fingerprint: " + f.File)
			}
			checked[f.File] = true
		}
		f.Pixels = read(filepath.Join(decoded, fmt.Sprintf("%04d.idx", f.ID)))
		if hash(f.Pixels) != f.IndexedSHA {
			panic("actor decoded fingerprint")
		}
		p.frames = append(p.frames, f)
	}
	for i := range p.frames {
		p.byID[p.frames[i].ID] = &p.frames[i]
	}
	for ip, hexcode := range map[uint16]string{0x177: "268807035ef042fecc7402ebe7ebd03b", 0x1aa: "268807035ef042fecc7403ebe790ebcc", 0x1c8: "268807035ef042ebb5905a5b035efe79"} {
		b, e := hex.DecodeString(hexcode)
		need(e)
		p.writerCodes[ip] = b
	}
	return p
}
func (p *openingActorProbe) before() {
	c := p.m.CPU
	cs, ip := c.Seg[golem.CS], c.IP
	if p.active != nil {
		if cs == p.retCS && ip == p.retIP && c.R[golem.SP] == p.sp+10 {
			p.finish()
		} else if p.m.Steps-p.start > 100000 && !p.allSprites || p.m.Steps-p.start > 1000000 || (cs == 0x4a2 && ip == 0) {
			p.active["rejected"] = "unfinished"
			p.calls = append(p.calls, p.active)
			p.active = nil
			p.selected = nil
		}
	}
	if cs != 0x4a2 || ip != 0 {
		return
	}
	if !bytes.Equal(p.m.Mem[0x4a20:0x4a20+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	stack := actorWords(p.m, c.Seg[golem.SS], c.R[golem.SP], 5)
	desc := actorWords(p.m, c.Seg[golem.DS], c.R[golem.BX], 4)
	if len(stack) != 5 || len(desc) != 4 {
		panic("actor descriptor bounds")
	}
	recordOffset := uint32(c.R[golem.AX]&0x7fff)*12 + uint32(stack[3]) + 0x36
	if recordOffset+12 > 65536 {
		return
	}
	off := uint16(recordOffset)
	record := actorWords(p.m, stack[4], off, 6)
	row := map[string]any{"entry_step": p.m.Steps, "registers": c.R, "segments": c.Seg, "stack": stack, "descriptor": desc, "record_far": fmt.Sprintf("%04X:%04X", stack[4], off), "record": record, "code12": fmt.Sprintf("%x", p.m.Mem[0x4a20:0x4a20+12])}
	matches := []int{}
	if len(record) == 6 {
		src := int(record[1])*16 + int(record[0])
		row["source_far"] = fmt.Sprintf("%04X:%04X", record[1], record[0])
		for _, f := range p.frames {
			if f.Ordinal != int(c.R[golem.AX]&0x7fff)-1 || src+f.EncodedLength > len(p.m.Mem) {
				continue
			}
			if hash(p.m.Mem[src:src+f.EncodedLength]) == f.EncodedSHA {
				matches = append(matches, f.ID)
			}
		}
	}
	row["matched_ids"] = matches
	if len(p.entries) >= 12000 {
		panic("actor entry bound")
	}
	p.entries = append(p.entries, row)
	if len(matches) != 1 {
		return
	}
	f := p.byID[matches[0]]
	if !p.allSprites && f.File != "OPENSHIP.SS" && f.File != "OPENSUN.SS" {
		return
	}
	// 原版診斷範圍擴充不改動正式HD定義。
	x, y := int(int16(c.R[golem.DX])), int(int16(stack[2]))
	row["source_id"] = f.ID
	row["source_file"] = f.File
	row["ordinal"] = f.Ordinal
	row["rect"] = [4]int{x, y, x + f.Size[0], y + f.Size[1]}
	row["encoded_sha256"] = f.EncodedSHA
	if desc[0] != 200 || desc[1] != 320 || uint32(desc[3])*16+uint32(desc[2]) != 115760 || int(record[4]) != f.Size[0] || int(record[5]) != f.Size[1] || x < 0 || y < 0 || x >= 320 || y+f.Size[1] > 200 || (y+f.Size[1]-1)*320+x+f.Size[0] > 64000 {
		row["rejected"] = "source geometry"
		p.calls = append(p.calls, row)
		return
	}

	p.under = make([]openingModelCell, f.Size[0]*f.Size[1])
	underCount := 0
	for k, v := range f.Pixels {
		if v == f.Transparent {
			continue
		}
		pos := (y+k/f.Size[0])*320 + x + k%f.Size[0]
		uc := p.pic.cells[pos]

		inherited := false
		if uc.kind == 0 {
			previous := p.cells[pos]
			if previous.ID != 0 && previous.Value == p.m.Mem[115760+pos] {
				uc = previous.Under
				inherited = true
			}
		}
		if uc.kind != 0 && (inherited || uc.value == p.m.Mem[115760+pos]) {

			raw := p.pic.borderRaw
			if uc.kind == 2 {
				raw = p.pic.mapRaw
			}
			if int(uc.local) < len(raw) && raw[uc.local] == uc.value {
				p.under[k] = uc
				underCount++
			}
		}
	}
	row["verified_underlay_cells"] = underCount
	p.active, p.selected, p.x, p.y = row, f, x, y
	p.retIP, p.retCS, p.sp = stack[0], stack[1], c.R[golem.SP]
	p.start = p.m.Steps
	p.writes = map[int]byte{}
	p.counts = map[int]int{}
	p.outside = false
}
func (p *openingActorProbe) write(a uint32, old, v byte) {
	if a < 115760 || a >= 115760+64000 {
		return
	}
	at := int(a) - 115760
	if p.cells[at].ID != 0 {
		p.revoked++
		if old == v {
			p.same++
		}
	}
	p.cells[at] = openingActorCell{}
	if p.active == nil {
		return
	}
	f := p.selected
	delta := at - (p.y*320 + p.x)
	x, y := delta%320, delta/320
	if delta < 0 {
		p.outside = true
		return
	}
	cs, ip := p.m.CPU.OpAddr()
	code := p.writerCodes[ip]
	pc := int(cs)*16 + int(ip)
	if cs != 0x4a2 || len(code) != 16 || !bytes.Equal(p.m.Mem[pc:pc+16], code) || x < 0 || y < 0 || x >= f.Size[0] || y >= f.Size[1] {
		p.outside = true
		return
	}
	local := y*f.Size[0] + x
	p.writes[local] = v
	p.counts[local]++
}
func (p *openingActorProbe) finish() {
	row, f := p.active, p.selected
	p.active, p.selected = nil, nil
	row["return_step"] = p.m.Steps
	row["unique_writes"] = len(p.writes)
	row["outside"] = p.outside
	mismatch := p.outside
	blob := []byte{}
	visible := 0
	for local, v := range f.Pixels {
		if v == f.Transparent {
			if p.counts[local] != 0 {
				mismatch = true
			}
			continue
		}
		x, y := p.x+local%f.Size[0], p.y+local/f.Size[0]
		if x < 0 || x >= 320 || y < 0 || y >= 200 {
			if p.counts[local] != 0 {
				mismatch = true
			}
			continue
		}
		visible++
		if p.counts[local] != 1 || p.writes[local] != v {
			mismatch = true
		}
		blob = binary.LittleEndian.AppendUint16(blob, uint16(local))
		blob = append(blob, p.writes[local])
	}
	row["sorted_local_value_sha256"] = hash(blob)
	row["expected_visible_opaque"] = visible
	row["source_opaque_total"] = f.Opaque
	row["verified"] = !mismatch && len(p.writes) == visible
	if row["verified"] == true {
		if p.firstUnder == nil {
			p.firstUnder = map[int]bool{}
		}
		if !p.firstUnder[f.ID] {
			p.firstUnder[f.ID] = true
			cells := [][4]uint32{}
			for local, u := range p.under {
				if u.kind != 0 {
					cells = append(cells, [4]uint32{uint32(local), uint32(u.kind), u.local, uint32(u.value)})
				}
			}
			sort.Slice(cells, func(i, j int) bool { return cells[i][0] < cells[j][0] })
			row["first_verified_underlay"] = cells
		}

		for k, v := range p.writes {
			pos := (p.y+k/f.Size[0])*320 + p.x + k%f.Size[0]
			p.cells[pos] = openingActorCell{uint16(f.ID), uint16(k), v, p.under[k]}
		}
		p.matched++
	}
	p.calls = append(p.calls, row)
}
func (p *openingActorProbe) capture(out string) {
	signature, _ := hex.DecodeString("f3a503f3790c81ee00808cd981c100088ed903fd4875e75d5f5e071fc9cb0000")
	live := bytes.Equal(p.m.Mem[0x5570+0x9f:0x5570+0x9f+32], signature)
	if !live {
		clear(p.cells[:])
		clear(p.publishedActor[:])
		clear(p.publishedPIC[:])
	}
	idx := p.m.Indexed()
	counts := map[int]int{}
	mainUnderCounts := map[int]int{}
	blob := make([]byte, 64000*12)
	for i, c := range p.cells {
		if c.ID != 0 {
			f := p.byID[int(c.ID)]
			if f == nil || int(c.Local) >= len(f.Pixels) || f.Pixels[c.Local] != c.Value || p.m.Mem[115760+i] != c.Value {
				panic("actor owner mismatch")
			}
			counts[int(c.ID)]++
			if c.Under.kind != 0 {
				mainUnderCounts[int(c.ID)]++
			}
		}
		at := i * 12
		binary.LittleEndian.PutUint16(blob[at:at+2], c.ID)
		binary.LittleEndian.PutUint16(blob[at+2:at+4], c.Local)
		blob[at+4] = c.Value
		blob[at+6] = c.Under.kind
		binary.LittleEndian.PutUint32(blob[at+7:at+11], c.Under.local)
		blob[at+11] = c.Under.value
	}
	file := fmt.Sprintf("actor-%08d.owners", p.m.Steps)
	need(os.WriteFile(filepath.Join(out, file), blob, 0644))

	pubActor := make([]byte, 64000*12)
	pubPIC := make([]byte, 64000*6)
	actorCounts, picCounts, underCounts := map[int]int{}, map[byte]int{}, map[int]int{}
	for pos, c := range p.publishedActor {
		if c.ID != 0 {
			if c.Value != idx[pos] {
				panic("published actor value")
			}
			actorCounts[int(c.ID)]++
			if c.Under.kind != 0 {
				underCounts[int(c.ID)]++
			}
		}
		at := pos * 12
		binary.LittleEndian.PutUint16(pubActor[at:at+2], c.ID)
		binary.LittleEndian.PutUint16(pubActor[at+2:at+4], c.Local)
		pubActor[at+4] = c.Value
		pubActor[at+6] = c.Under.kind
		binary.LittleEndian.PutUint32(pubActor[at+7:at+11], c.Under.local)
		pubActor[at+11] = c.Under.value
	}
	for pos, c := range p.publishedPIC {
		if c.kind != 0 {
			if c.value != idx[pos] {
				panic("published PIK value")
			}
			picCounts[c.kind]++
		}
		at := pos * 6
		pubPIC[at] = c.kind
		binary.LittleEndian.PutUint32(pubPIC[at+1:at+5], c.local)
		pubPIC[at+5] = c.value
	}
	actorFile := fmt.Sprintf("published-actor-%08d.owners", p.m.Steps)
	picFile := fmt.Sprintf("published-pik-%08d.owners", p.m.Steps)
	need(os.WriteFile(filepath.Join(out, actorFile), pubActor, 0644))
	need(os.WriteFile(filepath.Join(out, picFile), pubPIC, 0644))
	p.points = append(p.points, map[string]any{"step": p.m.Steps, "published_actor_counts": actorCounts, "published_pic_counts": picCounts, "published_underlay_counts": underCounts, "published_actor_file": actorFile, "published_pic_file": picFile, "owners": counts, "underlay_counts": mainUnderCounts, "owners_file": file, "live_code": live, "full_main_vga_equal": bytes.Equal(p.m.Mem[115760:115760+64000], p.m.Indexed()) && bytes.Equal(p.m.Mem[0xa0000:0xafa00], p.m.Indexed())})
}

func (p *openingActorProbe) publish(a uint32, old, value byte) {
	if !p.observePublication {
		return
	}
	pos := int(a) - 0xa0000
	if pos < 0 || pos >= 64000 {
		return
	}
	had := p.publishedActor[pos].ID != 0 || p.publishedPIC[pos].kind != 0
	p.publishedActor[pos] = openingActorCell{}
	p.publishedPIC[pos] = openingModelCell{}
	m := p.m
	c := m.CPU
	cs, ip := c.OpAddr()
	pc := int(cs)*16 + int(ip)
	code := []byte{0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8}
	known := false
	if cs == 0x557 && ip == 0x9f && c.Flags&0x400 == 0 && bytes.Equal(m.Mem[pc:pc+16], code) {
		delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
		src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
		known = delta >= 0 && delta < 2 && int(c.R[golem.DI])+delta < 65536 && int(c.R[golem.SI])+delta < 65536 && src == 115760+pos && m.Mem[src] == value
	}
	if known {
		pic := p.pic.cells[pos]
		actor := p.cells[pos]
		if pic.kind != 0 && pic.value == value {
			p.publishedPIC[pos] = pic
			p.publishedTransfers++
		}
		if actor.ID != 0 && actor.Value == value {
			p.publishedActor[pos] = actor
			p.publishedTransfers++
		}
	} else if had {
		p.publishedUnknown++
		if old == value {
			p.publishedSame++
		}
	}
}

// 每次開關區間清空發布來源；區間外不宣稱來源。
func (p *openingActorProbe) publicationWindow() {
	if p.publicationEdge >= len(p.publicationEdges) || p.m.Steps != p.publicationEdges[p.publicationEdge] {
		return
	}
	p.observePublication = p.publicationEdge%2 == 0
	clear(p.publishedActor[:])
	clear(p.publishedPIC[:])
	p.publicationEdge++
}
