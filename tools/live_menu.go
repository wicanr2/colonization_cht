// 固定版本第一列即時顯示切片。規格009/010/011；只使用公開API，不寫回原版。
// SetBeforeInstruction 的 Steps 為本次指令編號，比舊 pre-Step 探針多1。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"io"
	"os"
	"path/filepath"
	"strconv"

	golem "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/overlay"
)

const candidate = "GAME.TXT:0x000001B0"
const fontHash = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
const sourceHash = "6d3dbc785cd2b8fe343ae1345d6371b637867083e45f7f50f76eb3ee67fec427"

var safe = image.Rect(86, 107, 232, 114)
var versions = map[string]string{
	"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
	"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
	"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
}

func must(err error) {
	if err != nil {
		panic(err)
	}
}
func hash(b []byte) string    { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func read(path string) []byte { b, e := os.ReadFile(path); must(e); return b }
func dumpJSON(path string, v any) {
	b, e := json.MarshalIndent(v, "", "  ")
	must(e)
	must(os.WriteFile(path, append(b, '\n'), 0644))
}
func savePNG(path string, im image.Image) {
	f, e := os.Create(path)
	must(e)
	must(png.Encode(f, im))
	must(f.Close())
}

type fontMask struct {
	CandidateID     string `json:"candidate_id"`
	TranslationHash string `json:"translation_sha256"`
	FontHash        string `json:"font_sha256"`
	Width           int    `json:"width"`
	Height          int    `json:"height"`
	Alpha           []byte `json:"alpha"`
}
type pending struct {
	step                uint64
	ss, sp              uint16
	before, description []byte
	descriptionPtr      uint32
	record              map[string]any
}

func main() {
	root := flag.String("root", "/game", "唯讀原版")
	catalog := flag.String("catalog", "/repo/text/draft.zh-Hant.tsv", "譯文唯一來源")
	fontPath := flag.String("font-mask", "/out/goal056-font-mask.json", "已驗字模")
	out := flag.String("out", "/out/goal056-live", "輸出前綴")
	control := flag.Bool("control", false, "無指令觀測、無合成對照")
	missing := flag.Bool("missing", false, "缺字模回退對照")
	flag.Parse()
	validVersion := true
	inputs := map[string]string{}
	for name, want := range versions {
		inputs[name] = hash(read(filepath.Join(*root, name)))
		validVersion = validVersion && inputs[name] == want
	}
	if !validVersion {
		fmt.Fprintln(os.Stderr, "原版版本不符：此有限驗收器拒絕啟動，不套用中文")
		os.Exit(2)
	}
	rawSource := read(filepath.Join(*root, "GAME.TXT"))
	var source []byte
	if len(rawSource) >= 0x1b0+25 {
		source = bytes.Clone(rawSource[0x1b0 : 0x1b0+25])
	}
	validVersion = validVersion && hash(source) == sourceHash
	catalogBytes := read(*catalog)
	r := csv.NewReader(bytes.NewReader(catalogBytes))
	r.Comma = '\t'
	header, err := r.Read()
	must(err)
	columns := map[string]int{}
	for i, h := range header {
		columns[h] = i
	}
	get := func(row []string, key string) string {
		if i, ok := columns[key]; ok && i < len(row) {
			return row[i]
		}
		return ""
	}
	translation := ""
	matches := 0
	catalogValid := false
	for {
		row, e := r.Read()
		if e == io.EOF {
			break
		}
		must(e)
		if get(row, "candidate_id") != candidate {
			continue
		}
		matches++
		offset, e := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
		catalogValid = e == nil && offset == 0x1b0 && get(row, "source_file") == "GAME.TXT" && get(row, "source_sha256") == versions["GAME.TXT"] && get(row, "source_bytes_sha256") == sourceHash && get(row, "source_byte_length") == "25"
		translation = get(row, "zh_hant")
	}
	fontReason := ""
	var ink *image.Alpha
	if matches != 1 || !catalogValid || translation == "" {
		fontReason = "missing-or-invalid-translation"
	} else {
		var mask fontMask
		maskBytes, readErr := os.ReadFile(*fontPath)
		decodeErr := json.Unmarshal(maskBytes, &mask)
		if readErr != nil || decodeErr != nil {
			fontReason = "font-mask-unavailable"
		} else if mask.CandidateID != candidate || mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(translation)) {
			fontReason = "font-binding-mismatch"
		} else if mask.Width <= 0 || mask.Height <= 0 || mask.Width > safe.Dx()*4 || mask.Height > safe.Dy()*4 || len(mask.Alpha) != mask.Width*mask.Height {
			fontReason = "font-mask-out-of-bounds"
		} else {
			ink = image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
			copy(ink.Pix, mask.Alpha)
		}
	}
	if *missing {
		ink = nil
		fontReason = "missing-ink"
	}
	m := golem.New()
	must(m.LoadEXE(read(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	canvas := func() []byte { return m.Mem[0x2cae0 : 0x2cae0+64000] }
	sourceOK := func() bool { return bytes.Equal(m.Mem[0x6f23f:0x6f23f+25], source) && m.Mem[0x6f23f+25] == 0 }
	descriptor, _ := hex.DecodeString("c80040010000ae2c1700180019001a00")
	descriptorOK := func() bool { return bytes.Equal(m.Mem[0x1f448:0x1f448+len(descriptor)], descriptor) }
	var patch *overlay.Patch
	var afterSafe, patchDescription []byte
	var patchDescriptionPtr uint32
	var pendingEvent *pending
	events := []map[string]any{}
	frames := []map[string]any{}
	checkpoints := []map[string]any{}
	drops := []map[string]any{}
	lastOpened := 0
	enabled := true
	safeBytes := func(buf []byte) []byte {
		b := make([]byte, 0, safe.Dx()*safe.Dy())
		for y := safe.Min.Y; y < safe.Max.Y; y++ {
			b = append(b, buf[y*320+safe.Min.X:y*320+safe.Max.X]...)
		}
		return b
	}
	drop := func(reason string) {
		if patch != nil || pendingEvent != nil {
			drops = append(drops, map[string]any{"step": m.Steps, "reason": reason, "patch": patch != nil, "pending": pendingEvent != nil})
		}
		patch = nil
		pendingEvent = nil
		afterSafe = nil
	}
	checkContext := func() {
		if len(d.Opened) != lastOpened {
			drop("file-open")
			lastOpened = len(d.Opened)
		}
		if patch != nil && (!sourceOK() || !descriptorOK() || m.VideoMode() != 0x13 || !bytes.Equal(m.Mem[patchDescriptionPtr:patchDescriptionPtr+14], patchDescription) || !bytes.Equal(safeBytes(canvas()), afterSafe)) {
			drop("source-descriptor-canvas-or-mode-changed")
		}
	}
	if !*control {
		m.SetBeforeInstruction(func() {
			if len(d.Opened) != lastOpened {
				drop("file-open")
				lastOpened = len(d.Opened)
			}
			c := m.CPU
			cs, ip := c.Seg[golem.CS], c.IP
			if pendingEvent != nil {
				p := pendingEvent
				if m.Steps-p.step > 100000 || !sourceOK() || !descriptorOK() {
					drop("pending-expired-or-context-changed")
				} else if cs == 0x937c && ip == 0x1d50 {
					if c.Seg[golem.SS] != p.ss || c.R[golem.SP] != p.sp+10 {
						drop("return-stack-mismatch")
					} else {
						after := bytes.Clone(canvas())
						count := 0
						valid := true
						for i, b := range p.before {
							if b != after[i] {
								count++
								x, y := i%320, i/320
								if after[i] != 254 || x < 86 || x > 176 || y < 107 || y > 112 {
									valid = false
								}
							}
						}
						p.record["return_step"] = m.Steps
						p.record["legacy_return_step"] = m.Steps - 1
						p.record["return_sp"] = c.R[golem.SP]
						p.record["changed_pixels"] = count
						p.record["before_sha256"] = hash(p.before)
						p.record["after_sha256"] = hash(after)
						p.record["accepted"] = valid && count == 180
						events = append(events, p.record)
						if valid && count == 180 {
							var e error
							patch, e = overlay.NewPatch(p.before, after, 320, 200, safe)
							must(e)
							afterSafe = safeBytes(after)
							patchDescription = bytes.Clone(p.description)
							patchDescriptionPtr = p.descriptionPtr
						} else {
							patch = nil
						}
						pendingEvent = nil
					}
				}
			}
			if cs != 0x937c || ip != 0x0538 {
				return
			}
			if pendingEvent != nil {
				drop("unexpected-reentry")
			}
			if !validVersion || !sourceOK() || !descriptorOK() || !bytes.Equal(m.Mem[0x93cf8:0x93cfc], []byte{0xc8, 8, 0, 0}) || c.R[golem.AX] != 86 || c.R[golem.DX] != 107 {
				return
			}
			sp := c.R[golem.SP]
			ss := c.Seg[golem.SS]
			a := uint32(ss)*16 + uint32(sp)
			word := func(p uint32) uint16 { return uint16(m.Mem[p]) | uint16(m.Mem[p+1])<<8 }
			if word(a) != 0x1d50 || word(a+2) != 0xdf || word(a+4) != 0x6f16 {
				return
			}
			param := uint32(word(a+8))*16 + uint32(word(a+6))
			if param+14 > uint32(len(m.Mem)) {
				return
			}
			patch = nil
			afterSafe = nil
			desc := bytes.Clone(m.Mem[param : param+14])
			pendingEvent = &pending{step: m.Steps, ss: ss, sp: sp, before: bytes.Clone(canvas()), description: desc, descriptionPtr: param, record: map[string]any{"entry_step": m.Steps, "legacy_entry_step": m.Steps - 1, "entry_ip": "937C:0538", "return_ip": "937C:1D50", "ss": ss, "entry_sp": sp, "source": "6F16:00DF", "source_sha256": hash(source), "descriptor_linear": param, "descriptor_hex": hex.EncodeToString(desc), "canvas_descriptor_hex": hex.EncodeToString(descriptor), "registers": c.R, "segments": c.Seg}}
		})
	}
	render := func(label string) {
		if !*control {
			checkContext()
		}
		indexed := m.Mem[0xa0000:0xafa00]
		var output *image.RGBA
		applied := false
		reason := "control-no-compose"
		if *control {
			// 對照組不用overlay.Compose，也不裝指令hook；只在截圖時直接解碼原圖。
			if label != "" {
				output = image.NewRGBA(image.Rect(0, 0, 1280, 800))
				for i, v := range indexed {
					p := int(v) * 3
					c := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
					for dy := 0; dy < 4; dy++ {
						for dx := 0; dx < 4; dx++ {
							output.SetRGBA(i%320*4+dx, i/320*4+dy, c)
						}
					}
				}
			}
		} else {
			var e error
			output, applied, reason, e = overlay.Compose(indexed, m.DAC[:], 320, 200, 4, patch, ink, image.Pt(344, 428), 254, enabled && validVersion)
			must(e)
			if !validVersion {
				reason = "wrong-version"
			}
			if fontReason != "" && enabled && patch != nil {
				reason = fontReason
			}
		}
		rec := map[string]any{"step": m.Steps, "applied": applied, "reason": reason, "pending": pendingEvent != nil, "dropped": len(drops), "events": len(events)}
		if label == "" {
			frames = append(frames, rec)
			return
		}
		prefix := *out + "." + label
		savePNG(prefix+".png", output)
		must(os.WriteFile(prefix+".idx", indexed, 0644))
		must(os.WriteFile(prefix+".pal", m.DAC[:], 0644))
		rec["label"] = label
		rec["raw_sha256"] = hash(indexed)
		rec["palette_sha256"] = hash(m.DAC[:])
		rec["png"] = prefix + ".png"
		checkpoints = append(checkpoints, rec)
	}
	m.SetOnFrame(func() { render("") })
	phase, polls := 0, 0
	for m.Steps < 45000001 && !d.Exited && !m.CPU.Halted {
		switch m.Steps {
		case 3000000:
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		case 12000001, 31000001:
			x, y := 160, 100
			if m.Steps == 31000001 {
				x, y = 128, 110
			}
			d.MoveMouse(x, y)
			polls = len(d.Mouse.Polls)
			phase = 1
		case 25000000, 29000000, 43000000:
			d.MoveMouse(16, 16)
		case 27000000:
			d.MoveMouse(128, 110)
		case 24000000:
			render("menu-initial")
		case 26000000:
			render("menu-clear")
		case 28000000:
			render("menu-hover")
		case 29500000:
			enabled = false
			render("switch-off")
		case 29750000:
			enabled = true
			render("switch-on")
		case 30000000:
			render("menu-away")
		case 40000000:
			render("difficulty")
		case 45000000:
			render("difficulty-clear")
		}
		if m.Steps >= 31050000 && m.Steps <= 31350000 && m.Steps%50000 == 0 {
			render(fmt.Sprintf("click-%d", m.Steps))
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
		must(m.Step())
	}
	must(os.WriteFile(*out+".memory", m.Mem, 0644))
	c := m.CPU
	state := map[string]any{"memory_sha256": hash(m.Mem), "registers": c.R, "segments": c.Seg, "ip": c.IP, "flags": c.Flags, "steps": m.Steps, "ticks": m.Ticks, "frames": m.Frames, "cycles": c.Cycles, "frame_sha256": hash(m.Mem[0xa0000:0xafa00]), "palette_sha256": hash(m.DAC[:])}
	dumpJSON(*out+".json", map[string]any{"state": state, "checkpoints": checkpoints, "frames": frames, "events": events, "drops": drops, "input_hashes": inputs, "catalog_sha256": hash(catalogBytes), "translation_sha256": hash([]byte(translation)), "font_sha256": fontHash, "control": *control, "missing": *missing, "step_convention": "before-instruction-number = legacy-pre-Step + 1", "opened": d.Opened})
	fmt.Printf("完成 %d 事件、%d 幀、%d 截圖，原版狀態 %s\n", len(events), len(frames), len(checkpoints), hash(m.Mem))
}
