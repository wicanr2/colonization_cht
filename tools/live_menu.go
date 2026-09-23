// 固定版本主選單即時顯示切片。規格009/010/011/012；只使用公開API，不寫回原版。
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
	"strings"

	golem "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/overlay"
)

const fontHash = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"

var versions = map[string]string{
	"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
	"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
	"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
	"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
}

// 視窗前端由另外連結的檔案註冊；單獨建置此驗證器時不引入圖形依賴。
var frontendFrameSink func(*image.RGBA, map[string]any)
var frontendRunner func(*golem.Machine, *golem.DOS, func(string), string)

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
	FontSize        int    `json:"font_size"`
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

type menuLine struct {
	id                          string
	offset, length              int
	runtimeOffset               uint16
	y, maxX, maxY, pixels       int
	source                      []byte
	translation, fontReason     string
	matches                     int
	catalogValid                bool
	ink                         *image.Alpha
	patch                       *overlay.Patch
	afterSafe, patchDescription []byte
	patchDescriptionPtr         uint32
	pendingEvent                *pending
}

// 規格014／015：難度頁獨立的真實原版印字事件；不是全畫面 OCR 鍵。
type difficultyLine struct {
	id                      string
	file                    string
	offset, length          int
	fontSize                int
	card                    bool
	display                 []byte
	displayLinear           uint32
	formattedSeen           bool
	linear                  uint32
	readCS, readIP          uint16
	safe                    image.Rectangle
	cursorGuard             image.Rectangle
	inkSize                 image.Point
	bbox                    image.Rectangle
	pixels                  int
	only254                 bool
	position                image.Point
	source                  []byte
	translation, fontReason string
	matches                 int
	valid                   bool
	ink                     *image.Alpha
	before                  []byte
	startStep               uint64
	openedCount             int
	patch                   *overlay.Patch
	accepted                int
}

func (l *menuLine) safe() image.Rectangle { return image.Rect(86, l.y, 232, l.y+7) }
func (l *menuLine) safeBytes(buf []byte) []byte {
	b := make([]byte, 0, 146*7)
	for y := l.y; y < l.y+7; y++ {
		b = append(b, buf[y*320+86:y*320+232]...)
	}
	return b
}

func main() {
	root := flag.String("root", "/game", "唯讀原版")
	catalog := flag.String("catalog", "/repo/text/draft.zh-Hant.tsv", "譯文唯一來源")
	fontPath := flag.String("font-mask", "/out/goal056-font-mask.json", "已驗字模")
	allMenu := flag.Bool("all-menu", false, "啟用規格012的五列主選單")
	fontDir := flag.String("font-dir", "/out", "五列本機字模目錄")
	out := flag.String("out", "/out/goal056-live", "輸出前綴")
	control := flag.Bool("control", false, "無指令觀測、無合成對照")
	missing := flag.Bool("missing", false, "缺字模回退對照")
	window := flag.Bool("window", false, "使用已連結的 Ebitengine 視窗前端")
	flag.Parse()
	if *window && frontendRunner == nil {
		fmt.Fprintln(os.Stderr, "未連結 Ebitengine 視窗前端")
		os.Exit(2)
	}
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
	labelsSource := read(filepath.Join(*root, "LABELS.TXT"))
	namesSource := read(filepath.Join(*root, "NAMES.TXT"))
	difficulty := []*difficultyLine{}
	if *allMenu {
		difficulty = []*difficultyLine{
			{id: "LABELS.TXT:0x00000888", offset: 0x888, length: 6, linear: 0x4df72, readCS: 0x0d3a, readIP: 0x0015, safe: image.Rect(39, 14, 76, 26), bbox: image.Rect(42, 16, 73, 24), pixels: 126, position: image.Pt(168, 64)},
			{id: "LABELS.TXT:0x00000890", offset: 0x890, length: 16, linear: 0x4df79, readCS: 0x0d3a, readIP: 0x0015, safe: image.Rect(20, 27, 96, 40), bbox: image.Rect(23, 29, 92, 38), pixels: 284, position: image.Pt(92, 116)},
			{id: "LABELS.TXT:0x0000086E", offset: 0x86e, length: 24, linear: 0x4df59, readCS: 0x0e2d, readIP: 0x11cf, safe: image.Rect(10, 79, 105, 88), bbox: image.Rect(13, 81, 102, 86), pixels: 167, only254: true, position: image.Pt(52, 324)},
		}
		for _, l := range difficulty {
			l.file = "LABELS.TXT"
			l.fontSize = 24
			l.source = bytes.Clone(labelsSource[l.offset : l.offset+l.length])
		}
		// 規格017／019各自授權卡片、來源、顯示緩衝與安全區；不得跨卡片共用鍵。
		card := []*difficultyLine{
			{id: "NAMES.TXT:0x00000C0C", file: "NAMES.TXT", offset: 0xc0c, length: 10,
				linear: 0x4cc6a, readCS: 0x0e2d, readIP: 0x11cf,
				safe: image.Rect(138, 44, 186, 51), bbox: image.Rect(141, 45, 183, 50),
				pixels: 164, position: image.Pt(614, 180), fontSize: 21,
				card: true, display: []byte("DISCOVERER:"), displayLinear: 0x2a6b0,
				cursorGuard: image.Rect(112, 24, 212, 80), inkSize: image.Pt(69, 19)},
			{id: "LABELS.TXT:0x000008A9", file: "LABELS.TXT", offset: 0x8a9, length: 7,
				linear: 0x4df90, readCS: 0x0e2d, readIP: 0x11cf,
				safe: image.Rect(146, 52, 180, 60), bbox: image.Rect(150, 53, 175, 59),
				pixels: 83, position: image.Pt(612, 212), fontSize: 25,
				card: true, display: []byte("Easiest"), displayLinear: 0x2a6b0,
				cursorGuard: image.Rect(112, 24, 212, 80), inkSize: image.Pt(81, 23)},
			{id: "NAMES.TXT:0x00000C18", file: "NAMES.TXT", offset: 0xc18, length: 8,
				linear: 0x4cc75, readCS: 0x0e2d, readIP: 0x11cf,
				safe: image.Rect(247, 44, 287, 51), bbox: image.Rect(250, 45, 284, 50),
				pixels: 134, position: image.Pt(1034, 180), fontSize: 21,
				card: true, display: []byte("EXPLORER:"), displayLinear: 0x2a718,
				cursorGuard: image.Rect(225, 24, 304, 80), inkSize: image.Pt(69, 19)},
			{id: "LABELS.TXT:0x000008B2", file: "LABELS.TXT", offset: 0x8b2, length: 4,
				linear: 0x4df98, readCS: 0x0e2d, readIP: 0x11cf,
				safe: image.Rect(256, 52, 279, 60), bbox: image.Rect(260, 53, 276, 59),
				pixels: 55, position: image.Pt(1043, 212), fontSize: 25,
				card: true, display: []byte("Easy"), displayLinear: 0x2a718,
				cursorGuard: image.Rect(225, 24, 304, 80), inkSize: image.Pt(54, 23)},
		}
		for _, l := range card {
			source := namesSource
			if l.file == "LABELS.TXT" {
				source = labelsSource
			}
			l.source = bytes.Clone(source[l.offset : l.offset+l.length])
		}
		difficulty = append(difficulty, card...)
	}
	lines := []*menuLine{
		{offset: 0x1b0, length: 25, runtimeOffset: 0xdf, y: 107, maxX: 176, maxY: 112, pixels: 180},
		{offset: 0x1cb, length: 23, runtimeOffset: 0x111, y: 115, maxX: 168, maxY: 120, pixels: 163},
		{offset: 0x1e4, length: 19, runtimeOffset: 0x141, y: 123, maxX: 160, maxY: 127, pixels: 152},
		{offset: 0x1f9, length: 9, runtimeOffset: 0x16d, y: 131, maxX: 120, maxY: 135, pixels: 77},
		{offset: 0x204, length: 17, runtimeOffset: 0x18f, y: 139, maxX: 144, maxY: 144, pixels: 112},
	}
	if !*allMenu {
		lines = lines[:1]
	}
	for _, l := range lines {
		l.id = fmt.Sprintf("GAME.TXT:0x%08X", l.offset)
		l.source = bytes.Clone(rawSource[l.offset : l.offset+l.length])
	}
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
	for {
		row, e := r.Read()
		if e == io.EOF {
			break
		}
		must(e)
		for _, l := range lines {
			if get(row, "candidate_id") != l.id {
				continue
			}
			l.matches++
			offset, e := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
			l.catalogValid = e == nil && int(offset) == l.offset && get(row, "source_file") == "GAME.TXT" && get(row, "source_sha256") == versions["GAME.TXT"] && get(row, "source_bytes_sha256") == hash(l.source) && get(row, "source_byte_length") == strconv.Itoa(l.length)
			l.translation = get(row, "zh_hant")
		}
		for _, l := range difficulty {
			if get(row, "candidate_id") != l.id {
				continue
			}
			l.matches++
			offset, e := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
			l.valid = e == nil && int(offset) == l.offset && get(row, "source_file") == l.file && get(row, "source_sha256") == versions[l.file] && get(row, "source_bytes_sha256") == hash(l.source) && get(row, "source_byte_length") == strconv.Itoa(l.length) && (!l.card || get(row, "status") == "draft")
			l.translation = get(row, "zh_hant")
		}
	}
	for _, l := range lines {
		if l.matches != 1 || !l.catalogValid || l.translation == "" {
			l.fontReason = "missing-or-invalid-translation"
		} else {
			var mask fontMask
			path := *fontPath
			if *allMenu {
				path = filepath.Join(*fontDir, strings.ReplaceAll(l.id, ":", "-")+".json")
			}
			maskBytes, readErr := os.ReadFile(path)
			decodeErr := json.Unmarshal(maskBytes, &mask)
			if readErr != nil || decodeErr != nil {
				l.fontReason = "font-mask-unavailable"
			} else if mask.CandidateID != l.id || mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(l.translation)) {
				l.fontReason = "font-binding-mismatch"
			} else if mask.Width <= 0 || mask.Height <= 0 || mask.Width > l.safe().Dx()*4 || mask.Height > l.safe().Dy()*4 || len(mask.Alpha) != mask.Width*mask.Height {
				l.fontReason = "font-mask-out-of-bounds"
			} else {
				l.ink = image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
				copy(l.ink.Pix, mask.Alpha)
			}
		}
		if *missing {
			l.ink = nil
			l.fontReason = "missing-ink"
		}
	}
	for _, l := range difficulty {
		if l.matches != 1 || !l.valid || l.translation == "" {
			l.fontReason = "missing-or-invalid-translation"
			continue
		}
		path := filepath.Join(*fontDir, strings.ReplaceAll(l.id, ":", "-")+".json")
		var mask fontMask
		b, e := os.ReadFile(path)
		if e != nil || json.Unmarshal(b, &mask) != nil {
			l.fontReason = "font-mask-unavailable"
			continue
		}
		if mask.CandidateID != l.id || mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(l.translation)) || (l.card && mask.FontSize != l.fontSize) {
			l.fontReason = "font-binding-mismatch"
			continue
		}
		inset := 0
		if l.card {
			inset = 4
		}
		if mask.Width <= 0 || mask.Height <= 0 || mask.Width > l.safe.Dx()*4 || mask.Height > l.safe.Dy()*4 || len(mask.Alpha) != mask.Width*mask.Height || (l.card && (mask.Width != l.inkSize.X || mask.Height != l.inkSize.Y)) || l.position.X < l.safe.Min.X*4+inset || l.position.Y < l.safe.Min.Y*4+inset || l.position.X+mask.Width > l.safe.Max.X*4-inset || l.position.Y+mask.Height > l.safe.Max.Y*4-inset {
			l.fontReason = "font-mask-out-of-bounds"
			continue
		}
		l.ink = image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
		copy(l.ink.Pix, mask.Alpha)
		if *missing {
			l.ink = nil
			l.fontReason = "missing-ink"
		}
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
	sourceOK := func(l *menuLine) bool {
		p := 0x6f160 + int(l.runtimeOffset)
		return bytes.Equal(m.Mem[p:p+l.length], l.source) && m.Mem[p+l.length] == 0
	}
	descriptor, _ := hex.DecodeString("c80040010000ae2c1700180019001a00")
	paramBytes, _ := hex.DecodeString("0000fe000800fc00fd0000000000")
	descriptorOK := func() bool { return bytes.Equal(m.Mem[0x1f448:0x1f448+len(descriptor)], descriptor) }
	events := []map[string]any{}
	frames := []map[string]any{}
	checkpoints := []map[string]any{}
	drops := []map[string]any{}
	lastOpened := 0
	if !*control && len(difficulty) > 0 {
		m.WatchReads(0x4cc6a, 0x4df9d, func(a uint32, _ uint8) {
			cs, ip := m.CPU.OpAddr()
			if m.VideoMode() != 0x13 {
				return
			}
			for _, l := range difficulty {
				if a != l.linear || cs != l.readCS || ip != l.readIP || l.patch != nil || l.before != nil {
					continue
				}
				p := int(l.linear)
				if !bytes.Equal(m.Mem[p:p+l.length], l.source) || m.Mem[p+l.length] != 0 {
					continue
				}
				seenArt := false
				for _, name := range d.Opened {
					if strings.EqualFold(name, "DIFFICUL.PIK") {
						seenArt = true
					}
				}
				if !seenArt {
					continue
				}
				l.before = bytes.Clone(canvas())
				l.formattedSeen = false
				l.startStep = m.Steps
				l.openedCount = len(d.Opened)
			}
		})
	}
	enabled := true
	drop := func(l *menuLine, reason string) {
		if l.patch != nil || l.pendingEvent != nil {
			drops = append(drops, map[string]any{"candidate_id": l.id, "step": m.Steps, "reason": reason, "patch": l.patch != nil, "pending": l.pendingEvent != nil})
		}
		l.patch = nil
		l.pendingEvent = nil
		l.afterSafe = nil
	}
	checkContext := func() {
		if len(d.Opened) != lastOpened {
			for _, l := range lines {
				drop(l, "file-open")
			}
			lastOpened = len(d.Opened)
		}
		for _, l := range lines {
			if l.patch != nil && (!sourceOK(l) || !descriptorOK() || m.VideoMode() != 0x13 || !bytes.Equal(m.Mem[l.patchDescriptionPtr:l.patchDescriptionPtr+14], l.patchDescription) || !bytes.Equal(l.safeBytes(canvas()), l.afterSafe)) {
				drop(l, "source-descriptor-canvas-or-mode-changed")
			}
		}
		for _, l := range difficulty {
			p := int(l.linear)
			if (l.patch != nil || l.before != nil) && (len(d.Opened) != l.openedCount || m.VideoMode() != 0x13 || !bytes.Equal(m.Mem[p:p+l.length], l.source) || m.Mem[p+l.length] != 0) {
				l.patch = nil
				l.before = nil
				l.formattedSeen = false
			}
		}
	}
	if !*control {
		m.SetBeforeInstruction(func() {
			if len(d.Opened) != lastOpened {
				for _, l := range lines {
					drop(l, "file-open")
				}
				lastOpened = len(d.Opened)
			}
			c := m.CPU
			cs, ip := c.Seg[golem.CS], c.IP
			if cs == 0x0d21 && ip == 0x00c6 {
				for _, l := range difficulty {
					if !l.card || l.before == nil || m.Steps-l.startStep > 500000 {
						continue
					}
					p := int(l.displayLinear)
					if bytes.Equal(m.Mem[p:p+len(l.display)], l.display) && m.Mem[p+len(l.display)] == 0 {
						l.formattedSeen = true
					}
				}
			}
			for _, l := range lines {
				if l.pendingEvent != nil {
					p := l.pendingEvent
					if m.Steps-p.step > 100000 || !sourceOK(l) || !descriptorOK() || !bytes.Equal(m.Mem[p.descriptionPtr:p.descriptionPtr+14], paramBytes) {
						drop(l, "pending-expired-or-context-changed")
					} else if cs == 0x937c && ip == 0x1d50 {
						if c.Seg[golem.SS] != p.ss || c.R[golem.SP] != p.sp+10 {
							drop(l, "return-stack-mismatch")
						} else {
							after := bytes.Clone(canvas())
							count := 0
							valid := true
							minX, minY, maxX, maxY := 320, 200, -1, -1
							for i, b := range p.before {
								if b != after[i] {
									count++
									x, y := i%320, i/320
									if x < minX {
										minX = x
									}
									if y < minY {
										minY = y
									}
									if x > maxX {
										maxX = x
									}
									if y > maxY {
										maxY = y
									}
									if after[i] != 254 || x < 86 || x > l.maxX || y < l.y || y > l.maxY {
										valid = false
									}
								}
							}
							valid = valid && minX == 86 && minY == l.y && maxX == l.maxX && maxY == l.maxY
							p.record["return_step"] = m.Steps
							p.record["legacy_return_step"] = m.Steps - 1
							p.record["return_sp"] = c.R[golem.SP]
							p.record["changed_pixels"] = count
							p.record["before_sha256"] = hash(p.before)
							p.record["after_sha256"] = hash(after)
							p.record["accepted"] = valid && count == l.pixels
							events = append(events, p.record)
							if valid && count == l.pixels {
								var e error
								l.patch, e = overlay.NewPatch(p.before, after, 320, 200, l.safe())
								must(e)
								l.afterSafe = l.safeBytes(after)
								l.patchDescription = bytes.Clone(p.description)
								l.patchDescriptionPtr = p.descriptionPtr
							} else {
								l.patch = nil
							}
							l.pendingEvent = nil
						}
					}
				}
			}
			if cs != 0x937c || ip != 0x0538 {
				return
			}
			for _, l := range lines {
				if l.pendingEvent != nil {
					drop(l, "unexpected-reentry")
				}
			}
			if !validVersion || !descriptorOK() || !bytes.Equal(m.Mem[0x93cf8:0x93cfc], []byte{0xc8, 8, 0, 0}) || c.R[golem.AX] != 86 {
				return
			}
			sp := c.R[golem.SP]
			ss := c.Seg[golem.SS]
			a := uint32(ss)*16 + uint32(sp)
			word := func(p uint32) uint16 { return uint16(m.Mem[p]) | uint16(m.Mem[p+1])<<8 }
			if word(a) != 0x1d50 || word(a+4) != 0x6f16 {
				return
			}
			param := uint32(word(a+8))*16 + uint32(word(a+6))
			if param != 0x6f1d4 || param+14 > uint32(len(m.Mem)) || !bytes.Equal(m.Mem[param:param+14], paramBytes) {
				return
			}
			for _, l := range lines {
				if word(a+2) != l.runtimeOffset || int(c.R[golem.DX]) != l.y || !sourceOK(l) {
					continue
				}
				l.patch = nil
				l.afterSafe = nil
				desc := bytes.Clone(m.Mem[param : param+14])
				l.pendingEvent = &pending{step: m.Steps, ss: ss, sp: sp, before: bytes.Clone(canvas()), description: desc, descriptionPtr: param, record: map[string]any{"candidate_id": l.id, "entry_step": m.Steps, "legacy_entry_step": m.Steps - 1, "entry_ip": "937C:0538", "return_ip": "937C:1D50", "ss": ss, "entry_sp": sp, "source": fmt.Sprintf("6F16:%04X", l.runtimeOffset), "source_sha256": hash(l.source), "descriptor_linear": param, "descriptor_hex": hex.EncodeToString(desc), "canvas_descriptor_hex": hex.EncodeToString(descriptor), "registers": c.R, "segments": c.Seg}}
			}
		})
	}
	cardCursorBlocked := func(l *difficultyLine) bool {
		return l.card && (image.Pt(int(d.Mouse.X), int(d.Mouse.Y)).In(l.cursorGuard) || d.Mouse.Buttons != 0)
	}
	render := func(label string) {
		if !*control {
			checkContext()
			for _, l := range difficulty {
				if l.before == nil || l.patch != nil {
					continue
				}
				if m.Steps-l.startStep > 500000 {
					l.before = nil
					continue
				}
				after := canvas()
				count := 0
				minX, minY, maxX, maxY := 320, 200, -1, -1
				valid := true
				for y := l.safe.Min.Y; y < l.safe.Max.Y; y++ {
					for x := l.safe.Min.X; x < l.safe.Max.X; x++ {
						i := y*320 + x
						if l.before[i] == after[i] {
							continue
						}
						count++
						if x < minX {
							minX = x
						}
						if y < minY {
							minY = y
						}
						if x > maxX {
							maxX = x
						}
						if y > maxY {
							maxY = y
						}
						if (l.only254 && after[i] != 254) || (!l.card && !l.only254 && after[i] != 0 && after[i] != 253 && after[i] != 254) {
							valid = false
						}
					}
				}
				if count != l.pixels {
					continue
				}
				if !valid || (l.card && !l.formattedSeen) || minX != l.bbox.Min.X || minY != l.bbox.Min.Y || maxX != l.bbox.Max.X-1 || maxY != l.bbox.Max.Y-1 {
					l.before = nil
					continue
				}
				var e error
				l.patch, e = overlay.NewPatch(l.before, after, 320, 200, l.safe)
				must(e)
				l.accepted++
				events = append(events, map[string]any{"candidate_id": l.id, "entry_ip": fmt.Sprintf("%04X:%04X", l.readCS, l.readIP), "writer_ip": "0D21:012C", "entry_step": l.startStep, "accepted": true, "changed_pixels": count, "bbox_inclusive": []int{minX, minY, maxX, maxY}, "source_linear": l.linear})
				l.before = nil
			}
		}
		indexed := m.Mem[0xa0000:0xafa00]
		var output *image.RGBA
		applied := false
		reason := "control-no-compose"
		lineRecords := []map[string]any{}
		anyPending := false
		for _, l := range lines {
			anyPending = anyPending || l.pendingEvent != nil
		}
		if *control {
			// 對照組不用overlay.Compose，也不裝指令hook；只在截圖時直接解碼原圖。
			if label != "" || frontendFrameSink != nil {
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
			for _, l := range lines {
				lineRecords = append(lineRecords, map[string]any{"candidate_id": l.id, "applied": false, "reason": reason})
			}
		} else {
			layers := make([]overlay.Layer, len(lines)+len(difficulty))
			for i, l := range lines {
				layers[i] = overlay.Layer{Patch: l.patch, Ink: l.ink, Position: image.Pt(344, l.y*4), ColorIndex: 254, Enabled: enabled && validVersion}
			}
			for i, l := range difficulty {
				layers[len(lines)+i] = overlay.Layer{Patch: l.patch, Ink: l.ink, Position: l.position, ColorIndex: 254, Enabled: enabled && validVersion && !cardCursorBlocked(l)}
			}
			var e error
			var results []overlay.LayerResult
			output, results, e = overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, layers)
			must(e)
			for i, result := range results[:len(lines)] {
				l := lines[i]
				lineReason := result.Reason
				if !validVersion {
					lineReason = "wrong-version"
				}
				if l.fontReason != "" && enabled && l.patch != nil {
					lineReason = l.fontReason
				}
				if i == 0 {
					reason = lineReason
				}
				applied = applied || result.Applied
				lineRecords = append(lineRecords, map[string]any{"candidate_id": l.id, "applied": result.Applied, "reason": lineReason})
			}
			for i, l := range difficulty {
				result := results[len(lines)+i]
				lineReason := result.Reason
				if l.fontReason != "" {
					lineReason = l.fontReason
				}
				if cardCursorBlocked(l) && l.patch != nil {
					lineReason = "cursor-conservative-guard"
				}
				applied = applied || result.Applied
				lineRecords = append(lineRecords, map[string]any{"candidate_id": l.id, "applied": result.Applied, "reason": lineReason, "accepted_events": l.accepted})
			}
			if *allMenu && applied {
				reason = "applied"
			}
		}
		rec := map[string]any{"step": m.Steps, "applied": applied, "reason": reason, "pending": anyPending, "dropped": len(drops), "events": len(events), "lines": lineRecords}
		if label == "" {
			if frontendFrameSink != nil {
				frontendFrameSink(output, rec)
			}
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
	if *window {
		frontendRunner(m, d, render, *out)
		render("final")
	} else {
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
	}
	must(os.WriteFile(*out+".memory", m.Mem, 0644))
	c := m.CPU
	state := map[string]any{"memory_sha256": hash(m.Mem), "registers": c.R, "segments": c.Seg, "ip": c.IP, "flags": c.Flags, "steps": m.Steps, "ticks": m.Ticks, "frames": m.Frames, "cycles": c.Cycles, "frame_sha256": hash(m.Mem[0xa0000:0xafa00]), "palette_sha256": hash(m.DAC[:])}
	dumpJSON(*out+".json", map[string]any{"state": state, "checkpoints": checkpoints, "frames": frames, "events": events, "drops": drops, "input_hashes": inputs, "catalog_sha256": hash(catalogBytes), "translation_sha256": hash([]byte(lines[0].translation)), "font_sha256": fontHash, "control": *control, "missing": *missing, "all_menu": *allMenu, "step_convention": "before-instruction-number = legacy-pre-Step + 1", "opened": d.Opened})
	fmt.Printf("完成 %d 事件、%d 幀、%d 截圖，原版狀態 %s\n", len(events), len(frames), len(checkpoints), hash(m.Mem))
}
