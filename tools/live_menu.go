// 固定版本選單即時顯示切片。規格009–020的限定範圍；只使用公開API，不寫回原版。
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
	"image/draw"
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
	CatalogHash     string `json:"catalog_sha256"`
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
	nation                  bool
	nationCard              bool
	prompt                  bool
	display                 []byte
	displayLinear           uint32
	runtimeSource           []byte
	formattedSeen           bool
	glyphCount              int
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

// 規格029只授權英格蘭第一張開場字幕；來源事件與頁面權杖不可重用到其餘字幕。
type buildCaption struct {
	id, translation, fontReason string
	source, display             []byte
	matches                     int
	valid                       bool
	ink                         *image.Alpha
	before                      []byte
	patch                       *overlay.Patch
	phase                       string
	readPos                     int
	startStep, completeStep     uint64
	writes                      int
	bbox                        image.Rectangle
	colors                      map[byte]int
	openedCount                 int
	accepted, appliedFrames     int
}

// 規格030僅授權遊戲選項標題；八列快捷鍵及文字仍維持原版。
type optionsTitle struct {
	buildCaption
	afterSafe []byte
}

func (l *menuLine) safe() image.Rectangle { return image.Rect(86, l.y, 232, l.y+7) }
func optionsTitleSafeBytes(buf []byte) []byte {
	b := make([]byte, 0, 188*15)
	for y := 44; y < 59; y++ {
		b = append(b, buf[y*320+65:y*320+253]...)
	}
	return b
}
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
	nationCardA := flag.Bool("nation-card-a", false, "啟用規格021第一張旗卡 A 版兩欄")
	nationCardCatalog := flag.String("nation-card-catalog", "/repo/text/nation-card-fragments.zh-Hant.tsv", "旗卡顯示片段唯一 TSV")
	nationCardFonts := flag.String("nation-card-font-dir", "/out/goal099-card-fonts", "旗卡兩欄本機已驗 A 版字模")
	build1A := flag.Bool("build1-a", false, "啟用規格029英格蘭首張開場字幕 A／38px")
	build1Font := flag.String("build1-font", "/out/goal130-build1-font.json", "本機依固定字型與真 TSV 烘製的首張字幕字模")
	optionsTitleA := flag.Bool("game-options-title-a", false, "啟用規格030遊戲選項標題 A／34px")
	optionsTitleFont := flag.String("game-options-title-font", "/out/goal132-options-title-font.json", "本機依固定字型與真 TSV 烘製的遊戲選項標題字模")
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
	var caption *buildCaption
	if *build1A {
		caption = &buildCaption{
			id: "GAME.TXT:0x000153CC", phase: "idle",
			source:  bytes.Clone(rawSource[0x153cc:0x1540b]),
			display: bytes.Clone(rawSource[0x153ce:0x1540b]),
		}
		if !bytes.Equal(caption.source[:2], []byte("^^")) ||
			hash(caption.display) != "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6" {
			panic("固定原版首張字幕來源不符")
		}
	}
	var title *optionsTitle
	if *optionsTitleA {
		title = &optionsTitle{buildCaption: buildCaption{
			id: "GAME.TXT:0x000004CD", phase: "idle",
			source:  bytes.Clone(rawSource[0x4cd:0x4dd]),
			display: bytes.Clone(rawSource[0x4cd:0x4dd]),
		}}
		if hash(title.source) != "547a9bc5a42a065a7c0994ef27d0fd8c30ea52ce2c0fd2224693ce937f032c04" {
			panic("固定原版遊戲選項標題來源不符")
		}
	}
	labelsSource := read(filepath.Join(*root, "LABELS.TXT"))
	namesSource := read(filepath.Join(*root, "NAMES.TXT"))
	difficulty := []*difficultyLine{}
	var prompt *difficultyLine
	if *allMenu {
		difficulty = []*difficultyLine{
			{id: "LABELS.TXT:0x00000888", offset: 0x888, length: 6, linear: 0x4df72, readCS: 0x0d3a, readIP: 0x0015, safe: image.Rect(39, 14, 76, 26), bbox: image.Rect(42, 16, 73, 24), pixels: 126, position: image.Pt(193, 64), fontSize: 34, inkSize: image.Pt(74, 32)},
			{id: "LABELS.TXT:0x00000890", offset: 0x890, length: 16, linear: 0x4df79, readCS: 0x0d3a, readIP: 0x0015, safe: image.Rect(20, 27, 96, 40), bbox: image.Rect(23, 29, 92, 38), pixels: 284, position: image.Pt(189, 116), fontSize: 38, inkSize: image.Pt(82, 35)},
			{id: "LABELS.TXT:0x0000086E", offset: 0x86e, length: 24, linear: 0x4df59, readCS: 0x0e2d, readIP: 0x11cf, safe: image.Rect(10, 79, 105, 88), bbox: image.Rect(13, 81, 102, 86), pixels: 167, only254: true, position: image.Pt(52, 324)},
		}
		for _, l := range difficulty {
			l.file = "LABELS.TXT"
			if l.fontSize == 0 {
				l.fontSize = 24
			}
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
		// 規格020：國家頁左側兩行，各自依原版36px墨跡選38px中文字模。
		nation := []*difficultyLine{
			{id: "LABELS.TXT:0x000008D3", file: "LABELS.TXT", offset: 0x8d3, length: 6,
				linear: 0x4dfb5, readCS: 0x0d3a, readIP: 0x0015,
				safe: image.Rect(39, 35, 73, 46), bbox: image.Rect(42, 36, 70, 45),
				pixels: 120, position: image.Pt(183, 144), fontSize: 38,
				nation: true, display: []byte("Select"), displayLinear: 0x2a710,
				inkSize: image.Pt(82, 35)},
			{id: "LABELS.TXT:0x000008DB", file: "LABELS.TXT", offset: 0x8db, length: 14,
				linear: 0x4dfbc, readCS: 0x0d3a, readIP: 0x0015,
				safe: image.Rect(17, 48, 95, 59), bbox: image.Rect(20, 49, 92, 58),
				pixels: 270, position: image.Pt(142, 196), fontSize: 38,
				nation: true, display: []byte("European Power"), displayLinear: 0x2a710,
				inkSize: image.Pt(164, 35)},
		}
		for _, l := range nation {
			l.source = bytes.Clone(labelsSource[l.offset : l.offset+l.length])
		}
		difficulty = append(difficulty, nation...)
		if *nationCardA {
			// 規格021：只限第一張旗卡的紅字，不沿用左側標題或其他旗卡的字級。
			flagCard := []*difficultyLine{
				{id: "NAMES.TXT:0x000008EA", file: "NAMES.TXT", offset: 0x8ea, length: 7,
					linear: 0x4cbbe, readCS: 0x0e2d, readIP: 0x11cf,
					safe: image.Rect(125, 12, 190, 24), bbox: image.Rect(141, 15, 171, 20),
					pixels: 123, position: image.Pt(578, 60), fontSize: 21,
					nationCard: true, display: []byte("ENGLAND:"), displayLinear: 0x2a6ae,
					inkSize: image.Pt(92, 19)},
				{id: "LABELS.TXT:0x000008F2", file: "LABELS.TXT", offset: 0x8f2, length: 11,
					linear: 0x4dfd1, readCS: 0x0e2d, readIP: 0x11cf,
					safe: image.Rect(125, 83, 190, 96), bbox: image.Rect(135, 87, 178, 93),
					pixels: 156, position: image.Pt(597, 348), fontSize: 25,
					nationCard: true, display: []byte("Immigration"), displayLinear: 0x2a6ae,
					inkSize: image.Pt(54, 23)},
			}
			for _, l := range flagCard {
				if l.file == "NAMES.TXT" {
					l.source = bytes.Clone(namesSource[l.offset : l.offset+l.length])
				} else {
					l.source = bytes.Clone(labelsSource[l.offset : l.offset+l.length])
				}
			}
			difficulty = append(difficulty, flagCard...)
		}
		// 規格023限定 READY：譯稿鍵含^^，執行期來源另為可見字串加換行。
		prompt = &difficultyLine{
			id: "GAME.TXT:0x00000A7A", file: "GAME.TXT", offset: 0xa7a, length: 25,
			linear: 0x2b072, readCS: 0x0e2d, readIP: 0x09f4,
			safe: image.Rect(100, 85, 219, 98), bbox: image.Rect(104, 88, 215, 97),
			pixels: 415, position: image.Pt(474, 352), fontSize: 38,
			prompt: true, display: []byte("Please Enter Your Name."), displayLinear: 0x6f200,
			inkSize: image.Pt(328, 35), source: bytes.Clone(rawSource[0xa7a : 0xa7a+25]),
			runtimeSource: []byte("Please Enter Your Name.\n"),
		}
		if !bytes.Equal(prompt.source, []byte("^^Please Enter Your Name.")) {
			panic("原版姓名提示完整來源鍵不符")
		}
		difficulty = append(difficulty, prompt)
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
		if caption != nil && get(row, "candidate_id") == caption.id {
			caption.matches++
			offset, parseErr := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
			caption.valid = parseErr == nil && offset == 0x153cc &&
				get(row, "source_file") == "GAME.TXT" &&
				get(row, "source_sha256") == versions["GAME.TXT"] &&
				get(row, "source_bytes_sha256") == hash(caption.source) &&
				get(row, "source_byte_length") == strconv.Itoa(len(caption.source)) &&
				get(row, "status") == "draft"
			caption.translation = get(row, "zh_hant")
		}
		if title != nil && get(row, "candidate_id") == title.id {
			title.matches++
			offset, parseErr := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
			title.valid = parseErr == nil && offset == 0x4cd &&
				get(row, "source_file") == "GAME.TXT" &&
				get(row, "source_sha256") == versions["GAME.TXT"] &&
				get(row, "source_bytes_sha256") == hash(title.source) &&
				get(row, "source_byte_length") == "16" &&
				get(row, "status") == "draft"
			title.translation = get(row, "zh_hant")
		}
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
			l.valid = e == nil && int(offset) == l.offset && get(row, "source_file") == l.file && get(row, "source_sha256") == versions[l.file] && get(row, "source_bytes_sha256") == hash(l.source) && get(row, "source_byte_length") == strconv.Itoa(l.length) && (!(l.card || l.nation || l.prompt) || get(row, "status") == "draft")
			l.translation = get(row, "zh_hant")
		}
	}
	if *nationCardA {
		// 旗卡複合來源不同於整行主譯稿，僅採專用片段 TSV 的兩筆真鍵。
		cardBytes, readErr := os.ReadFile(*nationCardCatalog)
		if readErr == nil {
			cardReader := csv.NewReader(bytes.NewReader(cardBytes))
			cardReader.Comma = '\t'
			cardHeader, headerErr := cardReader.Read()
			if headerErr == nil {
				cardCatalogValid := true
				cardColumns := map[string]int{}
				for i, h := range cardHeader {
					cardColumns[h] = i
				}
				cardGet := func(row []string, key string) string {
					if i, ok := cardColumns[key]; ok && i < len(row) {
						return row[i]
					}
					return ""
				}
				for {
					row, e := cardReader.Read()
					if e == io.EOF {
						break
					}
					if e != nil {
						cardCatalogValid = false
						break
					}
					for _, l := range difficulty {
						if !l.nationCard || cardGet(row, "candidate_id") != l.id {
							continue
						}
						l.matches++
						offset, parseErr := strconv.ParseUint(cardGet(row, "byte_offset"), 0, 32)
						l.valid = parseErr == nil && int(offset) == l.offset &&
							cardGet(row, "source_file") == l.file &&
							cardGet(row, "source_sha256") == versions[l.file] &&
							cardGet(row, "source_bytes_sha256") == hash(l.source) &&
							cardGet(row, "source_byte_length") == strconv.Itoa(l.length) &&
							cardGet(row, "source_text") == string(l.source) &&
							cardGet(row, "status") == "draft"
						l.translation = cardGet(row, "zh_hant")
						if l.file == "NAMES.TXT" {
							l.translation += "："
						}
					}
				}
				if !cardCatalogValid {
					for _, l := range difficulty {
						if l.nationCard {
							l.valid = false
						}
					}
				}
			}
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
		if l.prompt {
			if !strings.HasPrefix(l.translation, "^^") || strings.Contains(l.translation[2:], "^") {
				l.valid = false
			} else {
				l.translation = l.translation[2:]
			}
		}
		if l.matches != 1 || !l.valid || l.translation == "" {
			l.fontReason = "missing-or-invalid-translation"
			continue
		}
		maskDir := *fontDir
		if l.nationCard {
			maskDir = *nationCardFonts
		}
		path := filepath.Join(maskDir, strings.ReplaceAll(l.id, ":", "-")+".json")
		var mask fontMask
		b, e := os.ReadFile(path)
		if e != nil || json.Unmarshal(b, &mask) != nil {
			l.fontReason = "font-mask-unavailable"
			continue
		}
		if mask.CandidateID != l.id || mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(l.translation)) || mask.FontSize != l.fontSize {
			l.fontReason = "font-binding-mismatch"
			continue
		}
		inset := 0
		if l.inkSize.X > 0 {
			inset = 4
		}
		shadow := 0
		if l.prompt || l.nationCard {
			shadow = 4
		}
		if mask.Width <= 0 || mask.Height <= 0 || mask.Width > l.safe.Dx()*4 || mask.Height > l.safe.Dy()*4 || len(mask.Alpha) != mask.Width*mask.Height || (l.inkSize.X > 0 && (mask.Width != l.inkSize.X || mask.Height != l.inkSize.Y)) || l.position.X < l.safe.Min.X*4+inset || l.position.Y < l.safe.Min.Y*4+inset || l.position.X+mask.Width+shadow > l.safe.Max.X*4-inset || l.position.Y+mask.Height > l.safe.Max.Y*4-inset {
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
	if caption != nil {
		if caption.matches != 1 || !caption.valid || !strings.HasPrefix(caption.translation, "^^") ||
			strings.Contains(caption.translation[2:], "^") || len(caption.translation) <= 2 {
			caption.fontReason = "missing-or-invalid-translation"
		} else {
			caption.translation = caption.translation[2:]
			var mask fontMask
			maskBytes, readErr := os.ReadFile(*build1Font)
			if readErr != nil || json.Unmarshal(maskBytes, &mask) != nil {
				caption.fontReason = "font-mask-unavailable"
			} else if mask.CandidateID != caption.id || mask.CatalogHash != hash(catalogBytes) ||
				mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(caption.translation)) ||
				mask.FontSize != 38 {
				caption.fontReason = "font-binding-mismatch"
			} else if mask.Width != 430 || mask.Height != 35 || len(mask.Alpha) != 430*35 {
				caption.fontReason = "font-mask-out-of-bounds"
			} else {
				caption.ink = image.NewAlpha(image.Rect(0, 0, 430, 35))
				copy(caption.ink.Pix, mask.Alpha)
			}
		}
		if *missing {
			caption.ink = nil
			caption.fontReason = "missing-ink"
		}
	}
	if title != nil {
		if title.matches != 1 || !title.valid || title.translation == "" || strings.ContainsAny(title.translation, "~^\n\r") {
			title.fontReason = "missing-or-invalid-translation"
		} else {
			var mask fontMask
			maskBytes, readErr := os.ReadFile(*optionsTitleFont)
			if readErr != nil || json.Unmarshal(maskBytes, &mask) != nil {
				title.fontReason = "font-mask-unavailable"
			} else if mask.CandidateID != title.id || mask.CatalogHash != hash(catalogBytes) ||
				mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(title.translation)) ||
				mask.FontSize != 34 {
				title.fontReason = "font-binding-mismatch"
			} else if mask.Width != 222 || mask.Height != 32 || len(mask.Alpha) != 222*32 {
				title.fontReason = "font-mask-out-of-bounds"
			} else {
				title.ink = image.NewAlpha(image.Rect(0, 0, 222, 32))
				copy(title.ink.Pix, mask.Alpha)
			}
		}
		if *missing {
			title.ink = nil
			title.fontReason = "missing-ink"
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
	titleDiagnostics := 0
	frames := []map[string]any{}
	checkpoints := []map[string]any{}
	drops := []map[string]any{}
	lastOpened := 0
	captionExpire := func(reason string) {
		if caption == nil || caption.phase == "idle" || caption.phase == "expired" {
			return
		}
		events = append(events, map[string]any{"candidate_id": caption.id, "stage": "expired", "step": m.Steps, "reason": reason})
		caption.phase, caption.patch, caption.before = "expired", nil, nil
	}
	titleExpire := func(reason string) {
		if title == nil || title.phase == "idle" || title.phase == "expired" {
			return
		}
		events = append(events, map[string]any{"candidate_id": title.id, "stage": "expired", "step": m.Steps, "reason": reason})
		title.phase, title.patch, title.before, title.afterSafe = "expired", nil, nil, nil
	}
	if !*control && ((caption != nil && caption.ink != nil) || (title != nil && title.ink != nil)) {
		m.WatchWrites(0x2cae0, 0x2cae0+64000, func(a uint32, old, value uint8) {
			if old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			x, y := int(a-0x2cae0)%320, int(a-0x2cae0)/320
			if caption != nil && caption.phase == "reading" {
				if cs != 0x0d21 || ip != 0x012c {
					captionExpire("unexpected-canvas-writer")
				} else if x < 12 || x >= 307 || y < 27 || y >= 42 || (value != 14 && value != 47 && value != 54) {
					captionExpire("write-outside-reviewed-pixels")
				} else {
					if caption.writes == 0 {
						caption.bbox = image.Rect(x, y, x+1, y+1)
					} else {
						caption.bbox = caption.bbox.Union(image.Rect(x, y, x+1, y+1))
					}
					caption.writes++
					caption.colors[value]++
					if caption.writes > 1040 {
						captionExpire("write-count-exceeded")
					}
				}
			}
			if title != nil && title.phase == "reading" {
				if cs != 0x0d21 || ip != 0x012c {
					titleExpire("unexpected-canvas-writer")
				} else if x < 65 || x >= 253 || y < 44 || y >= 59 || (value != 68 && value != 47 && value != 128) {
					titleExpire("write-outside-reviewed-pixels")
				} else {
					if title.writes == 0 {
						title.bbox = image.Rect(x, y, x+1, y+1)
					} else {
						title.bbox = title.bbox.Union(image.Rect(x, y, x+1, y+1))
					}
					title.writes++
					title.colors[value]++
					if title.writes > 319 {
						titleExpire("write-count-exceeded")
					}
				}
			}
		})
	}
	if !*control && len(difficulty) > 0 {
		m.WatchReads(0x4c000, 0x4e000, func(a uint32, _ uint8) {
			cs, ip := m.CPU.OpAddr()
			if m.VideoMode() != 0x13 {
				return
			}
			for _, l := range difficulty {
				if l.prompt {
					continue
				}
				if a != l.linear || cs != l.readCS || ip != l.readIP || l.patch != nil || l.before != nil {
					continue
				}
				p := int(l.linear)
				if !bytes.Equal(m.Mem[p:p+l.length], l.source) ||
					(!l.nationCard && m.Mem[p+l.length] != 0) {
					continue
				}
				seenArt := false
				if l.nation || l.nationCard {
					seenArt = len(d.Opened) > 0 && strings.EqualFold(d.Opened[len(d.Opened)-1], "NATIONS.PIK")
				} else {
					for _, name := range d.Opened {
						if strings.EqualFold(name, "DIFFICUL.PIK") {
							seenArt = true
						}
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
			if l.prompt {
				if (l.patch != nil || l.before != nil) &&
					(len(d.Opened) != l.openedCount || m.VideoMode() != 0x13 ||
						!bytes.Equal(m.Mem[p:p+len(l.runtimeSource)], l.runtimeSource) ||
						hash(m.DAC[:]) != "898669705f7ec9ad40dd0bfa57eadd2a922a033478ee0a5d1a8ad602ddc2ce65") {
					l.patch = nil
					l.before = nil
					l.formattedSeen = false
					l.glyphCount = 0
				}
				continue
			}
			if (l.patch != nil || l.before != nil) &&
				(len(d.Opened) != l.openedCount || m.VideoMode() != 0x13 ||
					!bytes.Equal(m.Mem[p:p+l.length], l.source) ||
					(!l.nationCard && m.Mem[p+l.length] != 0) ||
					((l.nation || l.nationCard) && (len(d.Opened) == 0 ||
						!strings.EqualFold(d.Opened[len(d.Opened)-1], "NATIONS.PIK"))) ||
					(l.nationCard && hash(m.DAC[:]) != "adf1664eae7057124766a35b65afa8dcc85432e52237cad2764c6dd4250750d7")) {
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
			if caption != nil && caption.ink != nil && cs == 0x0d21 && ip == 0x00c6 {
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				if (caption.phase == "idle" || caption.phase == "expired") && a == 0x2a560 &&
					m.VideoMode() == 0x13 &&
					hash(canvas()) == "d8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab" &&
					m.Mem[a] == caption.display[0] {
					caption.before = bytes.Clone(canvas())
					caption.phase, caption.startStep, caption.openedCount = "reading", m.Steps, len(d.Opened)
					caption.patch, caption.readPos, caption.writes = nil, 0, 0
					caption.bbox = image.Rectangle{}
					caption.colors = make(map[byte]int)
					events = append(events, map[string]any{"candidate_id": caption.id, "stage": "source", "step": m.Steps, "entry_ip": "0D21:00C6", "source_linear": a})
				}
				if caption.phase == "reading" {
					p := caption.readPos
					wantAddr := uint32(0x2a560 + p%2)
					want := byte(0)
					if p%2 == 0 && p/2 < len(caption.display) {
						want = caption.display[p/2]
					}
					if p >= 2*len(caption.display) || a != wantAddr || m.Mem[a] != want {
						captionExpire("source-read-mismatch")
					} else {
						caption.readPos++
						if caption.readPos == 2*len(caption.display) {
							caption.completeStep = m.Steps
							caption.phase = "waiting-screen"
						}
					}
				}
			}
			if title != nil && title.ink != nil && cs == 0x0d21 && ip == 0x00c6 {
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				if titleDiagnostics < 3 && a == 0x2ac78 && m.Mem[a] == title.display[0] {
					titleDiagnostics++
					events = append(events, map[string]any{"candidate_id": title.id, "stage": "source-candidate", "step": m.Steps,
						"canvas_sha256": hash(canvas()), "safe_sha256": hash(optionsTitleSafeBytes(canvas())),
						"video_mode": m.VideoMode(), "source_linear": a, "opened_count": len(d.Opened)})
				}
				if (title.phase == "idle" || title.phase == "expired") && a == 0x2ac78 &&
					m.VideoMode() == 0x13 &&
					hash(optionsTitleSafeBytes(canvas())) == "358729d7a05203a18f1ea4882d5db540e90ed7edf83af3e11dc20f676e978e04" &&
					m.Mem[a] == title.display[0] {
					title.before = bytes.Clone(canvas())
					title.phase, title.startStep, title.openedCount = "reading", m.Steps, len(d.Opened)
					title.patch, title.readPos, title.writes = nil, 0, 0
					title.bbox = image.Rectangle{}
					title.colors = make(map[byte]int)
					events = append(events, map[string]any{"candidate_id": title.id, "stage": "source", "step": m.Steps, "entry_ip": "0D21:00C6", "source_linear": a})
				}
				if title.phase == "reading" {
					p := title.readPos
					wantAddr := uint32(0x2ac78 + p%2)
					want := byte(0)
					if p%2 == 0 && p/2 < len(title.display) {
						want = title.display[p/2]
					}
					if p >= 2*len(title.display) || a != wantAddr || m.Mem[a] != want {
						titleExpire("source-read-mismatch")
					} else {
						title.readPos++
						if title.readPos == 2*len(title.display) {
							title.completeStep = m.Steps
							title.phase = "waiting-screen"
						}
					}
				}
			}
			if prompt != nil && cs == 0x0e2d && ip == 0x09f4 &&
				uint32(c.Seg[golem.DS])*16+uint32(c.R[golem.SI]) == prompt.linear &&
				prompt.patch == nil && prompt.before == nil && m.VideoMode() == 0x13 &&
				len(d.Opened) == 53 && strings.EqualFold(d.Opened[len(d.Opened)-1], "GAME.TXT") &&
				bytes.Equal(m.Mem[prompt.linear:prompt.linear+uint32(len(prompt.runtimeSource))], prompt.runtimeSource) &&
				hash(canvas()) == "f31602f9a239a4f83fd6e27e644384009d628517185aeb80bb248479e67d0e71" &&
				hash(m.DAC[:]) == "898669705f7ec9ad40dd0bfa57eadd2a922a033478ee0a5d1a8ad602ddc2ce65" {
				prompt.before = bytes.Clone(canvas())
				prompt.startStep = m.Steps
				prompt.openedCount = len(d.Opened)
				prompt.formattedSeen = false
				prompt.glyphCount = 0
				events = append(events, map[string]any{"candidate_id": prompt.id,
					"stage": "source", "step": m.Steps, "opened_count": len(d.Opened)})
			}
			if cs == 0x0d21 && ip == 0x00c6 {
				for _, l := range difficulty {
					if !(l.card || l.nation || l.nationCard || l.prompt) || l.before == nil || m.Steps-l.startStep > 500000 {
						continue
					}
					p := int(l.displayLinear)
					if bytes.Equal(m.Mem[p:p+len(l.display)], l.display) && m.Mem[p+len(l.display)] == 0 {
						l.formattedSeen = true
						if l.prompt &&
							uint32(c.Seg[golem.SS])*16+uint32(c.R[golem.BX]) == 0x2a864 &&
							l.glyphCount < len(l.display) {
							if m.Mem[0x2a864] != l.display[l.glyphCount] {
								events = append(events, map[string]any{"candidate_id": l.id,
									"stage": "glyph-mismatch", "step": m.Steps, "index": l.glyphCount,
									"expected": l.display[l.glyphCount], "actual": m.Mem[0x2a864]})
								l.before = nil
								l.formattedSeen = false
							} else {
								l.glyphCount++
							}
						}
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
	nationButtonBlocked := func(l *difficultyLine) bool {
		return l.nation && d.Mouse.Buttons != 0
	}
	nationCardCursorBlocked := func(l *difficultyLine) bool {
		if !l.nationCard {
			return false
		}
		x, y := int(d.Mouse.X), int(d.Mouse.Y)
		return image.Rect(x, y, x+16, y+16).Overlaps(l.safe)
	}
	captionCursorBlocked := func() bool {
		if caption == nil {
			return false
		}
		x, y := int(d.Mouse.X), int(d.Mouse.Y)
		// 只守住中譯實際墨跡與陰影；英語原文周圍的寬安全區仍可正常移鼠。
		return d.Mouse.Buttons != 0 ||
			image.Rect(x, y, x+16, y+16).Overlaps(image.Rect(105, 30, 215, 40))
	}
	render := func(label string) {
		if title != nil && title.ink != nil && !*control {
			if title.phase == "reading" && m.Steps-title.startStep > 2000000 {
				titleExpire("source-read-timeout")
			}
			if title.phase == "waiting-screen" || title.phase == "active" {
				if m.VideoMode() != 0x13 || len(d.Opened) != title.openedCount {
					titleExpire("mode-or-file-changed")
				} else if title.phase == "waiting-screen" {
					if m.Steps-title.completeStep > 2000000 {
						titleExpire("screen-sync-timeout")
					} else if title.readPos != 32 || title.writes != 319 ||
						!title.bbox.Eq(image.Rect(67, 47, 147, 56)) ||
						title.colors[68] != 146 || title.colors[47] != 103 || title.colors[128] != 70 {
						titleExpire("incomplete-reviewed-output")
					} else if hash(optionsTitleSafeBytes(canvas())) == "4cc2db436024b492e5eb7440dad60bb768e6c16e9cb2dcb16eddee0b2da83ca3" &&
						bytes.Equal(optionsTitleSafeBytes(canvas()), optionsTitleSafeBytes(m.Mem[0xa0000:0xafa00])) {
						var err error
						title.patch, err = overlay.NewPatch(title.before, canvas(), 320, 200, image.Rect(65, 44, 253, 59))
						if err != nil {
							titleExpire("invalid-observed-patch")
						} else {
							title.afterSafe = optionsTitleSafeBytes(canvas())
							title.phase = "active"
							title.accepted++
							events = append(events, map[string]any{"candidate_id": title.id, "stage": "active", "step": m.Steps, "read_count": title.readPos, "changed_pixels": title.writes})
						}
					}
				} else if !bytes.Equal(optionsTitleSafeBytes(canvas()), title.afterSafe) {
					titleExpire("canvas-title-changed")
				}
			}
		}
		if caption != nil && caption.ink != nil && !*control {
			if caption.phase == "reading" && m.Steps-caption.startStep > 2000000 {
				captionExpire("source-read-timeout")
			}
			if caption.phase == "waiting-screen" || caption.phase == "active" {
				if m.VideoMode() != 0x13 || hash(canvas()) != "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772" ||
					hash(m.DAC[:]) != "92593125369b8224c1f00b30ad0367d6f1766da49afb614dcf753ad8d70b665b" ||
					len(d.Opened) != caption.openedCount {
					captionExpire("canvas-palette-mode-or-file-changed")
				} else if caption.phase == "waiting-screen" && m.Steps-caption.completeStep > 2000000 {
					captionExpire("screen-sync-timeout")
				} else if caption.phase == "waiting-screen" && caption.readPos == 122 && caption.writes == 1040 &&
					caption.bbox.Eq(image.Rect(16, 30, 303, 39)) &&
					caption.colors[14] > 0 && caption.colors[47] > 0 && caption.colors[54] > 0 &&
					hash(m.Mem[0xa0000:0xafa00]) == "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772" {
					var err error
					caption.patch, err = overlay.NewPatch(caption.before, canvas(), 320, 200, image.Rect(12, 27, 307, 42))
					if err != nil {
						captionExpire("invalid-observed-patch")
					} else {
						caption.phase = "active"
						caption.accepted++
						events = append(events, map[string]any{"candidate_id": caption.id, "stage": "active", "step": m.Steps, "read_count": caption.readPos, "changed_pixels": caption.writes, "bbox": []int{16, 30, 303, 39}})
					}
				} else if caption.phase == "waiting-screen" && caption.readPos != 122 {
					captionExpire("incomplete-source-read")
				}
			}
		}
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
				newColors := map[byte]int{}
				for y := l.safe.Min.Y; y < l.safe.Max.Y; y++ {
					for x := l.safe.Min.X; x < l.safe.Max.X; x++ {
						i := y*320 + x
						if l.before[i] == after[i] {
							continue
						}
						count++
						if l.prompt {
							newColors[after[i]]++
						}
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
						if (l.only254 && after[i] != 254) ||
							(l.prompt && after[i] != 68 && after[i] != 47 && after[i] != 128) ||
							(l.nationCard && after[i] != 0 && after[i] != 12) ||
							(!l.card && !l.prompt && !l.nationCard && !l.only254 && after[i] != 0 && after[i] != 253 && after[i] != 254) {
							valid = false
						}
					}
				}
				if count != l.pixels {
					continue
				}
				if l.prompt {
					events = append(events, map[string]any{"candidate_id": l.id,
						"stage": "canvas-candidate", "step": m.Steps,
						"glyph_count": l.glyphCount, "formatted_seen": l.formattedSeen,
						"colors": newColors, "valid_colors": valid})
				}
				if !valid || ((l.card || l.nation || l.nationCard || l.prompt) && !l.formattedSeen) ||
					(l.prompt && (l.glyphCount != len(l.display) || len(newColors) != 3 ||
						newColors[68] != 199 || newColors[47] != 135 || newColors[128] != 81)) ||
					minX != l.bbox.Min.X || minY != l.bbox.Min.Y || maxX != l.bbox.Max.X-1 || maxY != l.bbox.Max.Y-1 {
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
				position, colorIndex := l.position, byte(254)
				if l.prompt {
					position = position.Add(image.Pt(4, 0))
					colorIndex = 47
				} else if l.nationCard {
					position = position.Add(image.Pt(4, 0))
					colorIndex = 0
				}
				layers[len(lines)+i] = overlay.Layer{Patch: l.patch, Ink: l.ink, Position: position, ColorIndex: colorIndex, Enabled: enabled && validVersion && !cardCursorBlocked(l) && !nationButtonBlocked(l) && !nationCardCursorBlocked(l)}
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
				if result.Applied && (l.prompt || l.nationCard) {
					index := 68
					if l.nationCard {
						index = 12
					}
					p := index * 3
					foreground := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
					r := image.Rectangle{Min: l.position, Max: l.position.Add(l.ink.Bounds().Size())}
					draw.DrawMask(output, r, image.NewUniform(foreground), image.Point{}, l.ink, l.ink.Bounds().Min, draw.Over)
				}
				lineReason := result.Reason
				if l.fontReason != "" {
					lineReason = l.fontReason
				}
				if cardCursorBlocked(l) && l.patch != nil {
					lineReason = "cursor-conservative-guard"
				}
				if nationButtonBlocked(l) && l.patch != nil {
					lineReason = "mouse-button-held"
				}
				if nationCardCursorBlocked(l) && l.patch != nil {
					lineReason = "cursor-over-card-field"
				}
				applied = applied || result.Applied
				lineRecords = append(lineRecords, map[string]any{"candidate_id": l.id, "applied": result.Applied, "reason": lineReason, "accepted_events": l.accepted})
			}
			if *allMenu && applied {
				reason = "applied"
			}
			if caption != nil {
				captionReason := caption.phase
				captionApplied := false
				if caption.ink == nil {
					captionReason = caption.fontReason
				} else if caption.phase == "active" && caption.patch != nil &&
					hash(indexed) == "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772" && !applied {
					if captionCursorBlocked() {
						captionReason = "cursor-or-button-over-caption"
					} else {
						frame, ok, why, err := overlay.Compose(indexed, m.DAC[:], 320, 200, 4,
							caption.patch, caption.ink, image.Pt(427, 124), 47, enabled)
						must(err)
						captionReason = why
						if ok {
							safe := image.Rect(48, 108, 1228, 168)
							draw.Draw(output, safe, frame, safe.Min, draw.Src)
							p := 14 * 3
							fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
							r := image.Rect(423, 120, 853, 155)
							draw.DrawMask(output, r, image.NewUniform(fg), image.Point{}, caption.ink, caption.ink.Bounds().Min, draw.Over)
							captionApplied, applied = true, true
							caption.appliedFrames++
							reason = "applied"
						}
					}
				} else if caption.phase == "active" && applied {
					captionReason = "other-overlay-active"
				} else if caption.phase == "active" {
					captionReason = "vga-frame-mismatch"
				}
				lineRecords = append(lineRecords, map[string]any{"candidate_id": caption.id, "applied": captionApplied, "reason": captionReason, "accepted_events": caption.accepted})
			}
			if title != nil {
				titleReason := title.phase
				titleApplied := false
				if title.ink == nil {
					titleReason = title.fontReason
				} else if title.phase == "active" && title.patch != nil && !applied {
					x, y := int(d.Mouse.X), int(d.Mouse.Y)
					if d.Mouse.Buttons != 0 || image.Rect(x, y, x+16, y+16).Overlaps(image.Rect(67, 47, 124, 56)) {
						titleReason = "cursor-or-button-over-title"
					} else if !bytes.Equal(optionsTitleSafeBytes(indexed), title.afterSafe) {
						titleReason = "vga-safe-mismatch"
					} else {
						frame, ok, why, err := overlay.Compose(indexed, m.DAC[:], 320, 200, 4,
							title.patch, title.ink, image.Pt(272, 192), 47, enabled)
						must(err)
						titleReason = why
						if ok {
							safe := image.Rect(260, 176, 1012, 236)
							draw.Draw(output, safe, frame, safe.Min, draw.Src)
							p := 68 * 3
							fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
							r := image.Rect(268, 188, 490, 220)
							draw.DrawMask(output, r, image.NewUniform(fg), image.Point{}, title.ink, title.ink.Bounds().Min, draw.Over)
							titleApplied, applied = true, true
							title.appliedFrames++
							reason = "applied"
						}
					}
				} else if title.phase == "active" && applied {
					titleReason = "other-overlay-active"
				}
				lineRecords = append(lineRecords, map[string]any{"candidate_id": title.id, "applied": titleApplied, "reason": titleReason, "accepted_events": title.accepted})
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
