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
	gohash "hash"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"io"
	"os"
	"path/filepath"
	"regexp"
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
	ValuesHash      string `json:"values_sha256"`
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
	thirdCard               bool // 規格016第三張卡 A 版：色號14前景、色號0陰影向右4像素
	cardColor               byte // 旗卡前景色號＝NAMES.TXT @COUNTRY 行尾值（英格蘭12、法國9、西班牙14、荷蘭13）
	restCard                bool // 規格022其餘三張旗卡，字模另放獨立目錄
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
	// 規格029／026目標141：逐張字幕的已驗原版事件參數；@BUILD1 沿用規格029原值。
	keys                 []string
	keyMatches           []int
	keyValid             []bool
	keyTranslations      []string
	base                 uint32
	beforeSHA, afterSHA  string
	writeCount           int
	inkBBox, safe        image.Rectangle
	fgPos, inkSize       image.Point
	need54               bool
	maskPath, valuesHash string
	displayOK            bool
	displaySHA           string
	keyOffsets           []int
	keySources           [][]byte
	captionName          string
}

// 規格030僅授權遊戲選項標題；八列快捷鍵及文字仍維持原版。
type optionsTitle struct {
	buildCaption
	afterSafe []byte
}

// 規格031：遊戲選項八列。整組讀字事件為權杖，逐列在第一次被原版改色時擷取當次印前底圖。
type optionRow struct {
	id, translation, fontReason string
	offset                      int
	hotkey                      byte
	source, display             []byte
	matches                     int
	valid                       bool
	ink                         *image.Alpha
	before, afterSafe           []byte
	writes                      int
	waitSince                   uint64
	patch                       *overlay.Patch
	phase                       string
	accepted, appliedFrames     int
}

type optionRows struct {
	rows                    [8]*optionRow
	expect                  []byte // 268 次讀取的期望值；核取前綴位置以 0xff 表示「[ 或 ]」
	phase                   string
	base                    uint32
	readPos, outside        int
	startStep, completeStep uint64
	openedCount             int
	accepted                int
}

var (
	optionRowOffsets = [8]int{0x4e9, 0x4fd, 0x512, 0x525, 0x533, 0x53e, 0x550, 0x566}
	optionRowWrites  = [8]int{338, 349, 283, 186, 172, 316, 343, 246}
	optionRowSizes   = [8]int{25, 28, 28, 25, 28, 28, 27, 28}
	optionRowInk     = [8]image.Point{{229, 25}, {233, 27}, {233, 27}, {155, 25}, {176, 27}, {173, 27}, {223, 29}, {175, 27}}
	// 奇數列（索引0、2、4、6）與偶數列各兩種已驗印前底圖：一般、反白。
	optionRowBackgrounds = [2][2]string{
		{"3c24c328cb52d0ddfe5da07f462e685f9d41c89fabad06722a38095ff0078947", "903ff7549ac31fbb35f8a978ed3072aa4d6c7ab035dcea9ede983aea48490159"},
		{"a37541c55677774da71ee04095a82752663fd9e0a24bbaf671d79134a8627bff", "96f7592f13131bb6eaf8128df7a612867459f9abe14ebedf18d3810405180807"},
	}
)

// 規格025：首次國家介紹頁。整頁印字事件為權杖；中文為目標102貼近原版版式的三層字模。
type introPage struct {
	id                     string
	sectionOffset, length  int
	chars, writes          int
	printSHA               string
	bbox                   image.Rectangle
	valid                  bool
	matches                int
	translation            string
	fontReason             string
	shadow, normal, accent *image.Alpha
	accepted, appliedFrame int
}

type introState struct {
	pages               []*introPage
	textArea            image.Rectangle // 啟用頁面 0D21:012C 改色 bbox 的聯集
	maxChars, maxWrites int
	phase               string
	page                *introPage
	before, afterSafe   []byte
	patch               *overlay.Patch
	chars, readPos      int
	sum                 gohash.Hash
	writes              int
	bbox                image.Rectangle
	startStep, lastRead uint64
	openedCount         int
	completeStep        uint64
}

var (
	introPanel      = image.Rect(8, 8, 312, 192) // 原版木紋頁內；四倍即 (32,32)–(1248,768)
	introPreprint   = "f31602f9a239a4f83fd6e27e644384009d628517185aeb80bb248479e67d0e71"
	introReadLinear = uint32(0x2a862)
)

func introPanelBytes(buf []byte) []byte {
	b := make([]byte, 0, introPanel.Dx()*introPanel.Dy())
	for y := introPanel.Min.Y; y < introPanel.Max.Y; y++ {
		b = append(b, buf[y*320+introPanel.Min.X:y*320+introPanel.Max.X]...)
	}
	return b
}

// 游標只疊在真 VGA 上（底層畫布沒有游標）；以滑鼠左上角起 16×16 保守涵蓋。
func cursorBox(x, y int) image.Rectangle { return image.Rect(x, y, x+16, y+16) }

// 目標142：首則教學提示 @TUTORIAL1（Discoverer 難度英格蘭開局）。整段印字為權杖；讀字期間原版同時畫顧問肖像，
// 故逐點記錄最後寫入者，只還原最後由 0D21:012C 寫下的文字像素。
type helpState struct {
	id, translation, fontReason string
	valid                       bool
	matches                     int
	shadow, normal, accent      *image.Alpha
	phase                       string
	chars, readPos, writes      int
	sum                         gohash.Hash
	bbox                        image.Rectangle
	firstOld                    map[int]byte // 文字像素第一次被 0D21:012C 改寫前的值
	lastText                    map[int]bool // 該像素最後一次寫入者是否為 0D21:012C
	patch                       *overlay.Patch
	afterSafe                   []byte
	startStep, lastRead         uint64
	completeStep                uint64
	accepted, appliedFrames     int
}

var (
	helpText      = image.Rect(68, 104, 256, 169) // 文字安全區；原版墨跡 (69,106)–(250,165)
	helpPortrait  = image.Rect(60, 29, 135, 120)  // 讀字期間 0D46:* 畫顧問肖像的範圍
	helpReadBase  = uint32(0x2ac72)
	helpBeforeSHA = "a18ee5bc02b824945f57b1c454a0756ae09434a3b20683b22afd7168cf3c8b52"
	helpAfterSHA  = "111a048748df4ed963443821839c41703939017197ddf7b3d6ce583f4086c5b3"
	helpPrintSHA  = "4181fdd58a74d0031037027762468fbf8cbe28565ff097f4726a0fa73a37936b"
)

// 目標143（規格032）：海上主畫面頂列（選單／回合訊息）與右側狀態欄。原版每行是一次 0D21:00C6 連續讀字，
// 可見值會變；執行期依當次英文字串與模板、唯一詞典 TSV 組出中文，再以本機字元圖集拼字。
type seaEvent struct {
	last              uint64
	next              uint32
	raw               []byte
	firstOld, lastVal map[int]byte
	writes            int
	bbox              image.Rectangle
	colors            map[byte]int
}

type seaPart struct {
	text  string
	color byte
	x     int // 四倍輸出座標
	size  int // 本段字級；超界時由 22px 逐級縮到 15px（欄位字級 2/3）
}

type seaFont struct {
	glyphs map[rune]*image.Alpha
	widths map[rune]int
	height int
	cjkTop int
}

type seaRow struct {
	bbox              image.Rectangle
	text              string
	parts             []seaPart
	firstOld, lastVal map[int]byte
}

type seaLayer struct {
	name      string
	safe      image.Rectangle
	rows      []*seaRow
	patch     *overlay.Patch
	shadow    *image.Alpha
	fg        map[byte]*image.Alpha
	afterSafe []byte
	dirty     bool
	reason    string
}

type seaState struct {
	dict           map[string]map[string]string // 角色 → 英文 → 中文
	menu           []string                     // 選單六詞：快捷鍵字母＋中文
	glyphs         map[rune]*image.Alpha
	widths         map[rune]int
	height, cjkTop int
	fonts          map[int]*seaFont
	cur            *seaEvent
	menuRun        []*seaEvent
	panel, bar     *seaLayer
	misses         map[string]int
}

var (
	seaPanelRect = image.Rect(240, 48, 320, 200)
	seaBarRect   = image.Rect(0, 0, 320, 8)
	seaMenuText  = "GAMEVIEWORDERSREPORTSTRADECOLONIZOPEDIA"
	seaMenuWords = []int{4, 4, 6, 7, 5, 13}
	seaPatterns  = struct{ season, gold, moves, locat, unit, terrain, goods, title *regexp.Regexp }{
		regexp.MustCompile(`^(\S+) (\d+)$`),
		regexp.MustCompile(`^(Gold:)(\d+)\$  (Tax:) (\d+)%$`),
		regexp.MustCompile(`^(Moves:) (\S+)$`),
		regexp.MustCompile(`^(Locat:) \((\d+), (\d+)\)$`),
		regexp.MustCompile(`^(\S+\.) (.+)$`),
		regexp.MustCompile(`^\((.+)\)$`),
		regexp.MustCompile(`^(\d+) (.+)$`),
		regexp.MustCompile(`^(\S+) (.+) (Inbound From) (.+)$`),
	}
)

// seaTranslate 把一行原版英文依模板換成中文；任一詞缺譯即回傳 false，保留原文。
func (st *seaState) seaTranslate(text string) (string, bool) {
	t := strings.TrimRight(text, " \x00")
	d := func(role, en string) (string, bool) { zh, ok := st.dict[role][en]; return zh, ok }
	if m := seaPatterns.gold.FindStringSubmatch(t); m != nil {
		a, ok1 := d("label", m[1])
		b, ok2 := d("label", m[3])
		return a + m[2] + "$　" + b + m[4] + "%", ok1 && ok2
	}
	if m := seaPatterns.locat.FindStringSubmatch(t); m != nil {
		a, ok := d("label", m[1])
		return a + "(" + m[2] + ", " + m[3] + ")", ok
	}
	if m := seaPatterns.moves.FindStringSubmatch(t); m != nil {
		a, ok := d("label", m[1])
		return a + m[2], ok
	}
	if m := seaPatterns.title.FindStringSubmatch(t); m != nil {
		n, ok1 := d("nation", m[1])
		u, ok2 := d("unit", m[2])
		l, ok3 := d("label", m[3])
		pt, ok4 := d("port", m[4])
		return n + u + l + pt, ok1 && ok2 && ok3 && ok4
	}
	if m := seaPatterns.season.FindStringSubmatch(t); m != nil {
		if se, ok := d("season", m[1]); ok {
			return m[2] + "年" + se, true
		}
	}
	if m := seaPatterns.unit.FindStringSubmatch(t); m != nil {
		n, ok1 := d("nation_abbrev", m[1])
		u, ok2 := d("unit", m[2])
		return n + u, ok1 && ok2
	}
	if m := seaPatterns.terrain.FindStringSubmatch(t); m != nil {
		if tr, ok := d("terrain", m[1]); ok {
			return "（" + tr + "）", true
		}
		return "", false
	}
	if m := seaPatterns.goods.FindStringSubmatch(t); m != nil {
		if g, ok := d("goods", m[2]); ok {
			return m[1] + " " + g, true
		}
		return "", false
	}
	for _, role := range []string{"order", "cargo"} {
		if zh, ok := d(role, t); ok {
			return zh, true
		}
	}
	return "", false
}

func (st *seaState) seaWidth(text string) (int, bool) { return st.seaWidthAt(text, 22) }

func (st *seaState) seaWidthAt(text string, size int) (int, bool) {
	f := st.fonts[size]
	if f == nil {
		return 0, false
	}
	w := 0
	for _, r := range text {
		gw, ok := f.widths[r]
		if !ok {
			return 0, false
		}
		w += gw
	}
	return w, true
}

// seaFit 回傳能在 limit 輸出像素內放下的最大字級（22px 起逐級到 15px）；放不下回傳 0。
func (st *seaState) seaFit(text string, limit int) int {
	for size := 22; size >= 15; size-- {
		if w, ok := st.seaWidthAt(text, size); ok && w <= limit {
			return size
		}
	}
	return 0
}

// seaDraw 把字串貼到遮罩（以最大值合併），回傳是否有墨跡越出遮罩。
func (st *seaState) seaDraw(mask *image.Alpha, text string, x, y, size int) bool {
	clipped := false
	f := st.fonts[size]
	for _, r := range text {
		g := f.glyphs[r]
		for gy := 0; gy < g.Rect.Dy(); gy++ {
			for gx := 0; gx < g.Rect.Dx(); gx++ {
				v := g.Pix[gy*g.Stride+gx]
				if v == 0 {
					continue
				}
				px, py := x+gx, y+gy
				if !image.Pt(px, py).In(mask.Rect) {
					clipped = true
					continue
				}
				if i := mask.PixOffset(px, py); v > mask.Pix[i] {
					mask.Pix[i] = v
				}
			}
		}
		x += f.widths[r]
	}
	return clipped
}

// 目標151（規格034）：靜態內嵌文字（開場製作名單職稱橫幅）。沒有印字事件可當權杖，
// 以當幀真 VGA 索引畫面在指紋矩形內逐 byte 相符為唯一觸發條件，相符才清除文字帶原文並畫中文。
type staticItem struct {
	id, zh, reason string
	fp, band       image.Rectangle
	sha            string
	ink            byte
	mask           *image.Alpha
	pos            image.Point
	on             bool
	accepted       int
}

func parseRect(text string) (image.Rectangle, bool) {
	f := strings.Split(text, ",")
	if len(f) != 4 {
		return image.Rectangle{}, false
	}
	v := make([]int, 4)
	for i := range f {
		n, err := strconv.Atoi(f[i])
		if err != nil {
			return image.Rectangle{}, false
		}
		v[i] = n
	}
	r := image.Rect(v[0], v[1], v[2], v[3])
	return r, !r.Empty() && r.In(image.Rect(0, 0, 320, 200))
}

func seaMisses(sea *seaState) map[string]int {
	if sea == nil {
		return nil
	}
	return sea.misses
}

func helpTextBytes(buf []byte) []byte {
	b := make([]byte, 0, helpText.Dx()*helpText.Dy())
	for y := helpText.Min.Y; y < helpText.Max.Y; y++ {
		b = append(b, buf[y*320+helpText.Min.X:y*320+helpText.Max.X]...)
	}
	return b
}

// 規格028：退休確認框。問句與 Yes／No 各為一次整段印字事件；逐欄在第一次被改色時擷取當次底圖。
type retireField struct {
	id, translation, fontReason string
	offset, length              int
	rect, bbox                  image.Rectangle
	writes                      int
	background                  string
	position                    image.Point
	size                        image.Point
	ink                         *image.Alpha
	matches                     int
	valid                       bool
	before, afterSafe           []byte
	got                         int
	gotBBox                     image.Rectangle
	patch                       *overlay.Patch
	phase                       string
	accepted, appliedFrames     int
}

type retireEvent struct {
	bases               []uint32
	first               byte
	chars               int
	printSHA            string
	fields              []*retireField
	phase               string
	base                uint32
	sum                 gohash.Hash
	readPos, charCount  int
	startStep, lastRead uint64
	openedCount         int
	completeStep        uint64
	helper              image.Rectangle // 0CAE:00A8 可在尚未印字欄位畫底圖的範圍
}

func rectBytes(buf []byte, r image.Rectangle) []byte {
	b := make([]byte, 0, r.Dx()*r.Dy())
	for y := r.Min.Y; y < r.Max.Y; y++ {
		b = append(b, buf[y*320+r.Min.X:y*320+r.Max.X]...)
	}
	return b
}

func optionRowSafe(i int) image.Rectangle { return image.Rect(80, 59+12*i, 252, 71+12*i) }
func optionRowSafeBytes(buf []byte, i int) []byte {
	r := optionRowSafe(i)
	b := make([]byte, 0, r.Dx()*r.Dy())
	for y := r.Min.Y; y < r.Max.Y; y++ {
		b = append(b, buf[y*320+r.Min.X:y*320+r.Max.X]...)
	}
	return b
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
	buildCaptionsA := flag.Bool("build-captions-a", false, "啟用規格026目標141英格蘭 @BUILD2～10 開場字幕 A／38px")
	buildCaptionFonts := flag.String("build-caption-font-dir", "/out/goal141-caption-fonts", "@BUILD2～10 本機字模目錄")
	checkpointSteps := flag.String("checkpoint-steps", "", "僅驗收：以逗號分隔的遞增原版步數，於其後第一幀另存畫面、索引與完整 RAM 雜湊")
	buildValues := flag.String("build-values", "/repo/text/build-caption-values.zh-Hant.tsv", "開場字幕變數值唯一 TSV")
	optionsTitleA := flag.Bool("game-options-title-a", false, "啟用規格030遊戲選項標題 A／34px")
	optionsTitleFont := flag.String("game-options-title-font", "/out/goal132-options-title-font.json", "本機依固定字型與真 TSV 烘製的遊戲選項標題字模")
	staticA := flag.Bool("static-credits-a", false, "啟用規格034開場製作名單職稱橫幅靜態覆蓋")
	staticCatalog := flag.String("static-catalog", "/repo/text/static-overlay.zh-Hant.tsv", "靜態覆蓋唯一 TSV")
	staticMasks := flag.String("static-mask-dir", "/out/goal151-static-masks", "本機依固定字型與 TSV 烘製的靜態覆蓋字模目錄")
	seaA := flag.Bool("sea-status-a", false, "啟用規格032海上選單列與狀態欄（22px＋黑影）")
	seaCatalog := flag.String("sea-catalog", "/repo/text/sea-status.zh-Hant.tsv", "海上詞典唯一 TSV")
	seaAtlas := flag.String("sea-atlas", "/out/goal143-sea-atlas.json", "本機依固定字型與詞典烘製的海上字元圖集")
	helpA := flag.Bool("tutorial-help-a", false, "啟用目標142首則教學提示 @TUTORIAL1 A 版（正文30px）")
	helpCatalog := flag.String("help-catalog", "/repo/text/help-bilingual.tsv", "help 雙語唯一 TSV")
	helpMasks := flag.String("help-mask-dir", "/out/goal142-help-masks", "本機依固定字型與真 TSV 烘製的 help 三層字模目錄")
	introA := flag.Bool("england-intro-a", false, "啟用規格025英格蘭首次介紹兩頁（標題34px／正文38px）")
	introAll := flag.Bool("nation-intro-a", false, "啟用規格025四國首次介紹八頁（標題34px／正文38px）")
	introCatalog := flag.String("intro-catalog", "/repo/text/nation-introduction.zh-Hant.tsv", "國家介紹長文唯一 TSV")
	introMasks := flag.String("intro-mask-dir", "/out/goal135-intro-masks", "本機依固定字型與真 TSV 烘製的介紹頁三層字模目錄")
	restCardsA := flag.Bool("nation-cards-rest-a", false, "啟用規格022其餘三張旗卡 A 版（21／25px）")
	restCardFonts := flag.String("nation-cards-rest-font-dir", "/out/goal140-nation-card-fonts", "其餘三張旗卡本機字模目錄")
	thirdCardA := flag.Bool("third-card-a", false, "啟用規格016第三張難度卡 A 版（21／25px）")
	thirdCardFonts := flag.String("third-card-font-dir", "/out/goal139-third-card-fonts", "第三張難度卡本機字模目錄")
	retireA := flag.Bool("retire-a", false, "啟用規格028退休確認框三欄 A 版（34px、共同置中）")
	retireFonts := flag.String("retire-font-dir", "/out/goal138-retire-fonts", "本機依固定字型與真 TSV 烘製的退休框字模目錄")
	optionRowsA := flag.Bool("game-options-rows-a", false, "啟用規格031遊戲選項八列 A 字級")
	optionRowsFonts := flag.String("game-options-rows-font-dir", "/out/goal134-row-fonts", "本機依固定字型與真 TSV 烘製的八列字模目錄")
	scratch := flag.String("scratch", "", "目標137：原版唯讀 Root 外的可寫暫存層（存讀檔用）；預設關閉")
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
	var captions []*buildCaption
	if *build1A {
		caption := &buildCaption{
			id: "GAME.TXT:0x000153CC", phase: "idle",
			source:  bytes.Clone(rawSource[0x153cc:0x1540b]),
			display: bytes.Clone(rawSource[0x153ce:0x1540b]),
			base:    0x2a560, writeCount: 1040, need54: true, displayOK: true,
			beforeSHA: "d8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab",
			afterSHA:  "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772",
			inkBBox:   image.Rect(16, 30, 303, 39), safe: image.Rect(12, 27, 307, 42),
			fgPos: image.Pt(423, 120), inkSize: image.Pt(430, 35), maskPath: *build1Font,
		}
		caption.keys, caption.keyOffsets, caption.keySources = []string{caption.id}, []int{0x153cc}, [][]byte{caption.source}
		if !bytes.Equal(caption.source[:2], []byte("^^")) ||
			hash(caption.display) != "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6" {
			panic("固定原版首張字幕來源不符")
		}
		captions = append(captions, caption)
	}
	if *buildCaptionsA {
		// 規格026目標141：英格蘭正常玩家路徑（85M 後不按鍵）十張字幕的 @BUILD2～10；
		// 顯示字串由 GAME.TXT 原行去 ^^ 並以英格蘭變數原文展開，雙冷啟動實測 SHA 釘住。
		type captionSpec struct {
			name          string
			keys          []string
			offsets       [][2]int // GAME.TXT 原行位移與長度（含 ^^）
			displaySHA    string
			base          uint32
			before, after string
			writes        int
			bbox, safe    image.Rectangle
			need54        bool
		}
		for _, sp := range []captionSpec{
			{"@BUILD2", []string{"GAME.TXT:0x0001542B", "GAME.TXT:0x00015457"}, [][2]int{{0x1542b, 42}, {0x15457, 11}}, "0cfc5ab07ea787de0d84826366302ef1810044e8e34094a67b557daeda9fc937", 0x2a534,
				"ea862cdccd15062dbbee15c3e48b187f6f3eeec5b2d0b34916709ab849e456fc", "69859c61c490112c333982957339c23f09df22f2e2918ca881c44d8911dc54c3", 964, image.Rect(69, 30, 251, 49), image.Rect(12, 27, 307, 52), true},
			{"@BUILD3", []string{"GAME.TXT:0x00015482"}, [][2]int{{0x15482, 41}}, "bbbbdd6e1a3539314ea015d7764af6ed6451f5a4534c169bba1f882ce560d767", 0x2a534,
				"09d3f445bc0b5f44306c04cc59e7c9daae7285ae22e42328386c65a21ad7e346", "7570358e60c4302624ae02dd5aa9683481fc94ce03e45a00b2f0cd566ff87d94", 501, image.Rect(74, 30, 245, 38), image.Rect(12, 27, 307, 42), false},
			{"@BUILD4", []string{"GAME.TXT:0x000154CB"}, [][2]int{{0x154cb, 55}}, "c6e372958c2d98a8b53e59d58dac57d7de1eeaab01e145b71c40b9fcf6e373d5", 0x2a534,
				"f2f8f3fe8284bfd2c5e891fe1da1418840eea7d1ff62323cbd304dd282e4fb3e", "b83918fce65d04268703fcfa49c8d5ee4474d9b21e5295dffcc716b01597ed14", 891, image.Rect(45, 30, 274, 39), image.Rect(12, 27, 307, 42), true},
			{"@BUILD5", []string{"GAME.TXT:0x00015522"}, [][2]int{{0x15522, 27}}, "ee8b6569c2bba4b57ce2133fd1f0ac9fe52f62db4f5621ce73fa40898f1a78d5", 0x2a560,
				"8ad92f5763d792fdd5e556a82d759a697b70142b9be6c4486b2fb167da2cd752", "d681e6bf78f2ca7c9cbd91769eaac3bc2cea7951744ecd6bbf7051275c486c43", 429, image.Rect(101, 30, 219, 39), image.Rect(12, 27, 307, 42), true},
			{"@BUILD6", []string{"GAME.TXT:0x0001555D"}, [][2]int{{0x1555d, 26}}, "b8cb47fdb1c13aa34a0fce30e333a1232d7991ded6a9daedd8b210cf24cc27c2", 0x2a560,
				"8ed6acf0459ab453eb9ee5f730e8db96af81d13edd3fc5267cb290ef7379052f", "9479b3399a2324a2615ed3a362ced7fe156eefaea90facefcfd309028c6a62a5", 421, image.Rect(104, 30, 215, 39), image.Rect(12, 27, 307, 42), true},
			{"@BUILD7", []string{"GAME.TXT:0x00015597"}, [][2]int{{0x15597, 62}}, "53f1e7991791074f9e5a1f54f9a40abc9b4b1957ff168e01d502f2f52b21eda6", 0x2a560,
				"f5d1b29aaa2dfa94a00ecc4c7d0526e1b45217b53a562b97a0e1eedee300954b", "977f89f504dc72c577e3bdba7fabc62fc4317cc8c1593e690abf50dfaf9ba35a", 1003, image.Rect(24, 30, 296, 39), image.Rect(12, 27, 307, 42), true},
			{"@BUILD8", []string{"GAME.TXT:0x000155F5"}, [][2]int{{0x155f5, 42}}, "0d3ec9226fae1b8b33356f299e2726dc109db51904c5409d1c71b7a3360abf13", 0x2a560,
				"1d649ded519c803fdb672e49f9910e14cfe76c2c92ddc734fceeaa40ef7f59f2", "607e5ed7cee5b0e1d7b3f635e52af4b32ccc6d438f559db8b76848293482ef62", 714, image.Rect(67, 30, 253, 39), image.Rect(12, 27, 307, 42), true},
			{"@BUILD9", []string{"GAME.TXT:0x0001563F"}, [][2]int{{0x1563f, 53}}, "65e7fb3ace0f3a3b37f53d6410ee6de05bacab86a2ead7e37e81608fd4bbca5a", 0x2a560,
				"e884c2c1d5cd994f2b03dc99a3eac9b661db69bd7681adffdd6b10232e1b1acf", "3ed89dc0c35960d1d94181716448bd39bf94cae6b6fe371c53123c7ff52097b3", 766, image.Rect(49, 30, 271, 39), image.Rect(12, 27, 307, 42), true},
			{"@BUILD10", []string{"GAME.TXT:0x00015695"}, [][2]int{{0x15695, 14}}, "cff475dbcfaf09ea9edf40efa8a40350da7eba8e0f0f0983175eef16e479480e", 0x2a560,
				"f079f5624f414b7dfa731887f3739718196932d6083ccfa94ce0b45b199fb898", "755b912dd898a7c73cc75938e648ac8d7e0e7a9ab6774f06c4d088915d65deec", 237, image.Rect(131, 30, 188, 38), image.Rect(12, 27, 307, 42), true},
		} {
			c := &buildCaption{id: sp.keys[0], keys: sp.keys, captionName: sp.name, phase: "idle", base: sp.base,
				beforeSHA: sp.before, afterSHA: sp.after, writeCount: sp.writes, inkBBox: sp.bbox, safe: sp.safe,
				need54: sp.need54, maskPath: filepath.Join(*buildCaptionFonts, strings.ReplaceAll(sp.keys[0], ":", "-")+".json")}
			for _, o := range sp.offsets {
				line := rawSource[o[0] : o[0]+o[1]]
				if !bytes.HasPrefix(line, []byte("^^")) {
					panic("固定原版字幕來源不符：" + sp.keys[0])
				}
				c.source = append(c.source, line...)
				c.keyOffsets = append(c.keyOffsets, o[0])
				c.keySources = append(c.keySources, line)
				c.display = append(c.display, line[2:]...)
			}
			c.displaySHA = sp.displaySHA // 變數展開後比對，見字幕變數載入
			captions = append(captions, c)
		}
	}
	for _, c := range captions {
		n := len(c.keys)
		c.keyMatches, c.keyValid, c.keyTranslations = make([]int, n), make([]bool, n), make([]string, n)
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
	var rows *optionRows
	if *optionRowsA {
		rows = &optionRows{phase: "idle"}
		for i, offset := range optionRowOffsets {
			end := bytes.Index(rawSource[offset:], []byte("\r\n"))
			if end <= 0 {
				panic("固定原版遊戲選項列來源不符")
			}
			src := bytes.Clone(rawSource[offset : offset+end])
			tilde := bytes.IndexByte(src, '~')
			if tilde < 0 || tilde+1 >= len(src) || bytes.Count(src, []byte("~")) != 1 {
				panic("固定原版遊戲選項列快捷鍵不符")
			}
			rows.rows[i] = &optionRow{id: fmt.Sprintf("GAME.TXT:0x%08X", offset), offset: offset,
				source: src, display: bytes.ReplaceAll(src, []byte("~"), nil), hotkey: src[tilde+1], phase: "idle"}
			rows.expect = append(rows.expect, 0xff, 0, ' ', 0)
			for _, ch := range rows.rows[i].display {
				rows.expect = append(rows.expect, ch, 0)
			}
		}
		if len(rows.expect) != 268 {
			panic("固定原版遊戲選項八列讀字長度不符")
		}
	}
	var retire []*retireEvent
	if *retireA {
		q := &retireField{id: "GAME.TXT:0x00000122", offset: 0x122, length: 27, rect: image.Rect(118, 75, 184, 99),
			bbox: image.Rect(122, 78, 181, 97), writes: 441, position: image.Pt(512, 312), size: image.Pt(185, 72),
			background: "0ab9b89e1548b9876fd8851a4d1ee93a5f96d541422655d9adbeaa09a2000903"}
		yes := &retireField{id: "GAME.TXT:0x00000141", offset: 0x141, length: 3, rect: image.Rect(122, 99, 144, 112),
			bbox: image.Rect(126, 102, 141, 110), writes: 64, position: image.Pt(514, 408), size: image.Pt(37, 32),
			background: "d23d0f4236dfedece662f3c4a5a8bca247986e8119f7992a7a60367d9bc37cfa"}
		no := &retireField{id: "GAME.TXT:0x00000146", offset: 0x146, length: 2, rect: image.Rect(122, 112, 142, 125),
			bbox: image.Rect(126, 114, 136, 122), writes: 54, position: image.Pt(506, 456), size: image.Pt(37, 32),
			background: "498f71ea0dc7b57418100f5aec4b6cc70d71833e26da9dcc350f31a7e7054fda"}
		retire = []*retireEvent{
			{bases: []uint32{0x2ac80}, first: 'D', chars: 26, fields: []*retireField{q}, phase: "idle",
				printSHA: "8882639f39e799c1e3a9565ee8c952560558f247a71270d2ce8e252d789f1cca"},
			{bases: []uint32{0x2ade6, 0x2ae4e}, first: 'Y', chars: 5, fields: []*retireField{yes, no}, phase: "idle",
				printSHA: "88da672874b376794ba3e094ca6c15e58778b1f97313f3cb8b8d39c47e52f2e2", helper: image.Rect(121, 113, 199, 124)},
		}
		for _, ev := range retire {
			for _, f := range ev.fields {
				f.phase = "idle"
			}
		}
	}
	var intro *introState
	if *introA || *introAll {
		// 固定路徑已證實的整頁印字：可見字數、序列 SHA、0D21:012C 改色點數與 bbox（目標101／102）。
		all := []*introPage{
			{id: "GAME.TXT:@NATION0A", sectionOffset: 0xae7c, length: 904, chars: 833, writes: 14193,
				printSHA: "25f3dd22b2d753adc9f66c76c4e8c4dabe0474600d996b6128881552f1122d23", bbox: image.Rect(10, 20, 305, 179)},
			{id: "GAME.TXT:@NATION0B", sectionOffset: 0xb204, length: 215, chars: 170, writes: 2932,
				printSHA: "33cadaf8f05359be9c7f3ade81ab3d41ed3583e0c9b3361f9fda9d335e9d84a9", bbox: image.Rect(10, 75, 292, 124)},
			{id: "GAME.TXT:@NATION1A", sectionOffset: 0xb2db, length: 870, chars: 794, writes: 13412,
				printSHA: "7285983b0263b270b7e952a78aecc40e0fa682e45302ae088371b493da0a258b", bbox: image.Rect(10, 25, 304, 174)},
			{id: "GAME.TXT:@NATION1B", sectionOffset: 0xb641, length: 253, chars: 207, writes: 3438,
				printSHA: "9018be96a5ab5eb08fcb830beaa493a6090b6aec2eecdd682594065d6a6971d9", bbox: image.Rect(10, 70, 308, 129)},
			{id: "GAME.TXT:@NATION2A", sectionOffset: 0xb73e, length: 1032, chars: 953, writes: 16103,
				printSHA: "37df0dda5ca2f142501142b572ff8b7e3e51ec20d2baa7131aaaa236449b4fbe", bbox: image.Rect(10, 10, 305, 189)},
			{id: "GAME.TXT:@NATION2B", sectionOffset: 0xbb46, length: 226, chars: 180, writes: 3168,
				printSHA: "3dfc072784c1f2728e8a1f514623c54b8320b3185407b4a1ed74c29809ce850e", bbox: image.Rect(10, 75, 292, 124)},
			{id: "GAME.TXT:@NATION3A", sectionOffset: 0xbc28, length: 1034, chars: 957, writes: 16401,
				printSHA: "a13e855de4b202af656d76d6319fd0ecd5a87a81115e27df66b4dae67f938bbd", bbox: image.Rect(10, 10, 305, 189)},
			{id: "GAME.TXT:@NATION3B", sectionOffset: 0xc032, length: 351, chars: 299, writes: 5262,
				printSHA: "6fa75f110995ae368395a39d8b6ee4c8c44ab25ed72ce63342a913cb3e8b8d01", bbox: image.Rect(10, 65, 307, 134)},
		}
		intro = &introState{phase: "idle", pages: all[:2]}
		if *introAll {
			intro.pages = all
		}
		for i, pg := range intro.pages {
			if i == 0 {
				intro.textArea = pg.bbox
			}
			intro.textArea = intro.textArea.Union(pg.bbox)
			intro.maxChars, intro.maxWrites = max(intro.maxChars, pg.chars), max(intro.maxWrites, pg.writes)
		}
		introBytes := read(*introCatalog)
		lines := strings.Split(strings.TrimRight(string(introBytes), "\n"), "\n")
		header := strings.Split(lines[0], "\t")
		col := map[string]int{}
		for i, name := range header {
			col[name] = i
		}
		for _, line := range lines[1:] {
			f := strings.Split(line, "\t")
			if len(f) != len(header) {
				continue
			}
			for _, pg := range intro.pages {
				if f[col["message_id"]] != pg.id {
					continue
				}
				pg.matches++
				offset, e1 := strconv.ParseUint(f[col["section_offset"]], 0, 32)
				length, e2 := strconv.Atoi(f[col["section_byte_length"]])
				pg.valid = e1 == nil && e2 == nil && int(offset) == pg.sectionOffset && length == pg.length &&
					f[col["source_file"]] == "GAME.TXT" && f[col["source_file_sha256"]] == versions["GAME.TXT"] &&
					f[col["section_sha256"]] == hash(rawSource[pg.sectionOffset:pg.sectionOffset+pg.length])
				pg.translation = f[col["zh_hant_draft"]]
			}
		}
		for _, pg := range intro.pages {
			if pg.matches != 1 || !pg.valid || !strings.Contains(pg.translation, "\\n") {
				pg.fontReason = "missing-or-invalid-translation"
				continue
			}
			var mask struct {
				ID          string `json:"message_id"`
				Catalog     string `json:"catalog_sha256"`
				Translation string `json:"translation_sha256"`
				Font        string `json:"font_sha256"`
				Title       int    `json:"title_font_px"`
				Body        int    `json:"body_font_px"`
				Width       int    `json:"width"`
				Height      int    `json:"height"`
				Shadow      []byte `json:"shadow"`
				Normal      []byte `json:"normal"`
				Accent      []byte `json:"highlight"`
			}
			b, e := os.ReadFile(filepath.Join(*introMasks, strings.ReplaceAll(pg.id, ":", "-")+".json"))
			size := (introPanel.Dx() * 4) * (introPanel.Dy() * 4)
			if e != nil || json.Unmarshal(b, &mask) != nil {
				pg.fontReason = "font-mask-unavailable"
			} else if mask.ID != pg.id || mask.Catalog != hash(introBytes) || mask.Translation != hash([]byte(pg.translation)) ||
				mask.Font != fontHash || mask.Title != 34 || mask.Body != 38 {
				pg.fontReason = "font-binding-mismatch"
			} else if mask.Width != introPanel.Dx()*4 || mask.Height != introPanel.Dy()*4 ||
				len(mask.Shadow) != size || len(mask.Normal) != size || len(mask.Accent) != size {
				pg.fontReason = "font-mask-out-of-bounds"
			} else {
				r := image.Rect(0, 0, mask.Width, mask.Height)
				pg.shadow, pg.normal, pg.accent = image.NewAlpha(r), image.NewAlpha(r), image.NewAlpha(r)
				copy(pg.shadow.Pix, mask.Shadow)
				copy(pg.normal.Pix, mask.Normal)
				copy(pg.accent.Pix, mask.Accent)
			}
			if *missing {
				pg.shadow, pg.normal, pg.accent = nil, nil, nil
				pg.fontReason = "missing-ink"
			}
		}
	}
	var help *helpState
	if *helpA {
		help = &helpState{id: "GAME.TXT:@TUTORIAL1", phase: "idle"}
		helpBytes := read(*helpCatalog)
		// 同介紹頁 TSV：譯文換行寫成字面 \n、欄內可能含雙引號，故逐行以 tab 切欄，不用 csv 引號規則。
		helpLines := strings.Split(strings.TrimRight(string(helpBytes), "\n"), "\n")
		header := strings.Split(helpLines[0], "\t")
		col := map[string]int{}
		for i, h := range header {
			col[h] = i
		}
		helpFormatOK := true
		for _, line := range helpLines[1:] {
			row := strings.Split(line, "\t")
			if len(row) != len(header) {
				helpFormatOK = false
				continue
			}
			hget := func(k string) string {
				if i, ok := col[k]; ok {
					return row[i]
				}
				return ""
			}
			if hget("message_id") != help.id {
				continue
			}
			help.matches++
			offset, e1 := strconv.ParseUint(hget("text_offset"), 0, 32)
			length, e2 := strconv.Atoi(hget("text_byte_length"))
			help.valid = e1 == nil && e2 == nil && offset == 0x13190 && length == 222 &&
				hget("source_file") == "GAME.TXT" && hget("source_file_sha256") == versions["GAME.TXT"] &&
				hget("source_bytes_sha256") == hash(rawSource[offset:int(offset)+length]) && hget("status") == "draft"
			// 本路徑 %STRING0 的當次顯示值為 Caravel（由整段印字 SHA 釘住），譯名沿 PEDIA.TXT:@UNIT13。
			help.translation = strings.ReplaceAll(hget("zh_hant"), "%STRING0", "卡拉維爾帆船")
		}
		if !helpFormatOK || help.matches != 1 || !help.valid || strings.Contains(help.translation, "%") {
			help.fontReason = "missing-or-invalid-translation"
		} else {
			var mask struct {
				ID          string `json:"message_id"`
				Catalog     string `json:"catalog_sha256"`
				Translation string `json:"translation_sha256"`
				Font        string `json:"font_sha256"`
				Body        int    `json:"body_font_px"`
				Width       int    `json:"width"`
				Height      int    `json:"height"`
				Shadow      []byte `json:"shadow"`
				Normal      []byte `json:"normal"`
				Accent      []byte `json:"highlight"`
			}
			b, err := os.ReadFile(filepath.Join(*helpMasks, "GAME.TXT-@TUTORIAL1.json"))
			size := helpText.Dx() * 4 * helpText.Dy() * 4
			if err != nil || json.Unmarshal(b, &mask) != nil {
				help.fontReason = "font-mask-unavailable"
			} else if mask.ID != help.id || mask.Catalog != hash(helpBytes) || mask.Translation != hash([]byte(help.translation)) ||
				mask.Font != fontHash || mask.Body != 30 {
				help.fontReason = "font-binding-mismatch"
			} else if mask.Width != helpText.Dx()*4 || mask.Height != helpText.Dy()*4 ||
				len(mask.Shadow) != size || len(mask.Normal) != size || len(mask.Accent) != size {
				help.fontReason = "font-mask-out-of-bounds"
			} else {
				rect := image.Rect(0, 0, mask.Width, mask.Height)
				help.shadow, help.normal, help.accent = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
				copy(help.shadow.Pix, mask.Shadow)
				copy(help.normal.Pix, mask.Normal)
				copy(help.accent.Pix, mask.Accent)
			}
		}
		if *missing {
			help.shadow, help.normal, help.accent = nil, nil, nil
			help.fontReason = "missing-ink"
		}
	}
	labelsSource := read(filepath.Join(*root, "LABELS.TXT"))
	namesSource := read(filepath.Join(*root, "NAMES.TXT"))
	var statics []*staticItem
	if *staticA {
		staticBytes := read(*staticCatalog)
		lines := strings.Split(strings.TrimRight(string(staticBytes), "\n"), "\n")
		header := strings.Split(lines[0], "\t")
		col := map[string]int{}
		for i, h := range header {
			col[h] = i
		}
		for _, line := range lines[1:] {
			row := strings.Split(line, "\t")
			if len(row) != len(header) {
				continue
			}
			get := func(k string) string { return row[col[k]] }
			it := &staticItem{id: get("candidate_id"), zh: get("zh_hant"), sha: get("fingerprint_sha256")}
			fp, ok1 := parseRect(get("fingerprint_rect"))
			band, ok2 := parseRect(get("text_band"))
			it.fp, it.band = fp, band
			img, err := os.ReadFile(filepath.Join(*root, get("image_file")))
			switch {
			case !ok1 || !ok2 || !band.In(fp) || err != nil || hash(img) != get("image_sha256") || it.zh == "" || get("status") != "draft":
				it.reason = "missing-or-invalid-translation"
			}
			if it.reason == "" {
				var mask struct {
					ID          string `json:"candidate_id"`
					Catalog     string `json:"catalog_sha256"`
					Translation string `json:"translation_sha256"`
					Font        string `json:"font_sha256"`
					Px          int    `json:"font_px"`
					Width       int    `json:"width"`
					Height      int    `json:"height"`
					X           int    `json:"x"`
					Y           int    `json:"y"`
					Ink         int    `json:"ink_index"`
					Alpha       []byte `json:"alpha"`
				}
				b, err := os.ReadFile(filepath.Join(*staticMasks, strings.ReplaceAll(it.id, ":", "-")+".json"))
				var r image.Rectangle
				if err != nil || json.Unmarshal(b, &mask) != nil {
					it.reason = "font-mask-unavailable"
				} else if r = image.Rect(mask.X, mask.Y, mask.X+mask.Width, mask.Y+mask.Height); mask.ID != it.id ||
					mask.Catalog != hash(staticBytes) || mask.Translation != hash([]byte(it.zh)) || mask.Font != fontHash ||
					mask.Px < 15 || mask.Px > 22 || mask.Ink < 0 || mask.Ink > 255 {
					it.reason = "font-binding-mismatch"
				} else if mask.Width <= 0 || mask.Height <= 0 || len(mask.Alpha) != mask.Width*mask.Height ||
					!r.In(image.Rectangle{Min: band.Min.Mul(4), Max: band.Max.Mul(4)}) {
					it.reason = "font-mask-out-of-bounds"
				} else {
					it.mask = image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
					copy(it.mask.Pix, mask.Alpha)
					it.pos, it.ink = r.Min, byte(mask.Ink)
				}
			}
			if *missing {
				it.mask, it.reason = nil, "missing-ink"
			}
			statics = append(statics, it)
		}
		// 重複鍵整組停用（fail-closed），不讓先出現的那一列生效。
		count := map[string]int{}
		for _, it := range statics {
			count[it.id]++
		}
		for _, it := range statics {
			if count[it.id] > 1 {
				it.mask, it.reason = nil, "duplicate-key"
			}
		}
	}
	var sea *seaState
	seaReason := ""
	if *seaA {
		sea = &seaState{dict: map[string]map[string]string{}, misses: map[string]int{},
			panel: &seaLayer{name: "sea:panel", safe: seaPanelRect}, bar: &seaLayer{name: "sea:bar", safe: seaBarRect}}
		seaBytes := read(*seaCatalog)
		menuSource := read(filepath.Join(*root, "MENU.TXT"))
		sources := map[string][]byte{"NAMES.TXT": namesSource, "LABELS.TXT": labelsSource, "MENU.TXT": menuSource}
		seaLines := strings.Split(strings.TrimRight(string(seaBytes), "\n"), "\n")
		header := strings.Split(seaLines[0], "\t")
		col := map[string]int{}
		for i, h := range header {
			col[h] = i
		}
		seen := map[string]bool{}
		menuZh := map[string]string{}
		for _, line := range seaLines[1:] {
			row := strings.Split(line, "\t")
			if len(row) != len(header) {
				seaReason = "catalog-format"
				continue
			}
			get := func(k string) string { return row[col[k]] }
			src, ok := sources[get("source_file")]
			offset, e1 := strconv.ParseUint(get("byte_offset"), 0, 32)
			length, e2 := strconv.Atoi(get("source_byte_length"))
			text := get("source_text")
			if !ok || e1 != nil || e2 != nil || seen[get("candidate_id")] || int(offset)+length > len(src) ||
				get("source_sha256") != hash(src) || string(src[offset:int(offset)+length]) != text ||
				len(text) != length || get("zh_hant") == "" || get("status") != "draft" {
				seaReason = "catalog-source-mismatch"
				continue
			}
			seen[get("candidate_id")] = true
			role := get("role")
			if sea.dict[role] == nil {
				sea.dict[role] = map[string]string{}
			}
			if _, dup := sea.dict[role][text]; dup {
				seaReason = "catalog-duplicate"
			}
			sea.dict[role][text] = get("zh_hant")
			if role == "menu" {
				menuZh[text] = get("zh_hant")
			}
		}
		for _, key := range []string{"~GAME", "~VIEW", "~ORDERS", "~REPORTS", "~TRADE", "~COLONIZOPEDIA"} {
			zh, ok := menuZh[key]
			if !ok {
				seaReason = "catalog-missing-menu"
				break
			}
			sea.menu = append(sea.menu, "("+key[1:2]+")"+"\x00"+zh)
		}
		var atlas struct {
			Font    string `json:"font_sha256"`
			Px      int    `json:"font_px"`
			Catalog string `json:"catalog_sha256"`
			Floor   int    `json:"floor_px"`
			Sizes   map[string]struct {
				Height int `json:"height"`
				CJKTop int `json:"cjk_ink_top"`
				Glyphs map[string]struct {
					W     int    `json:"w"`
					Alpha []byte `json:"alpha"`
				} `json:"glyphs"`
			} `json:"sizes"`
		}
		b, err := os.ReadFile(*seaAtlas)
		if err != nil || json.Unmarshal(b, &atlas) != nil {
			seaReason = "font-mask-unavailable"
		} else if atlas.Font != fontHash || atlas.Px != 22 || atlas.Floor != 15 || atlas.Catalog != hash(seaBytes) || len(atlas.Sizes) != 8 {
			seaReason = "font-binding-mismatch"
		} else {
			sea.fonts = map[int]*seaFont{}
			for size := 15; size <= 22; size++ {
				src, ok := atlas.Sizes[strconv.Itoa(size)]
				if !ok || src.Height <= 0 {
					seaReason = "font-mask-out-of-bounds"
					break
				}
				f := &seaFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, height: src.Height, cjkTop: src.CJKTop}
				for k, g := range src.Glyphs {
					r := []rune(k)
					if len(r) != 1 || g.W <= 0 || len(g.Alpha) != g.W*src.Height {
						seaReason = "font-mask-out-of-bounds"
						break
					}
					a := image.NewAlpha(image.Rect(0, 0, g.W, src.Height))
					copy(a.Pix, g.Alpha)
					f.glyphs[r[0]], f.widths[r[0]] = a, g.W
				}
				sea.fonts[size] = f
			}
			if seaReason == "" {
				sea.glyphs, sea.widths = sea.fonts[22].glyphs, sea.fonts[22].widths
				sea.height, sea.cjkTop = sea.fonts[22].height, sea.fonts[22].cjkTop
			}
		}
		if *missing {
			seaReason = "missing-ink"
		}
		if seaReason != "" {
			sea.glyphs = nil
		}
	}
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
		if *thirdCardA {
			// 規格016目標120／121：第三張卡只在玩家點選後印出兩行；安全區為目標121修訂值。
			card = append(card,
				&difficultyLine{id: "NAMES.TXT:0x00000C22", file: "NAMES.TXT", offset: 0xc22, length: 12,
					linear: 0x4cc7e, readCS: 0x0e2d, readIP: 0x11cf,
					safe: image.Rect(29, 139, 84, 148), bbox: image.Rect(32, 141, 82, 146),
					pixels: 205, position: image.Pt(192, 564), fontSize: 21,
					card: true, thirdCard: true, display: []byte("CONQUISTADOR:"), displayLinear: 0x2a718,
					cursorGuard: image.Rect(3, 119, 110, 177), inkSize: image.Pt(69, 19)},
				&difficultyLine{id: "LABELS.TXT:0x000008B8", file: "LABELS.TXT", offset: 0x8b8, length: 8,
					linear: 0x4df9d, readCS: 0x0e2d, readIP: 0x11cf,
					safe: image.Rect(38, 148, 76, 157), bbox: image.Rect(41, 149, 74, 155),
					pixels: 116, position: image.Pt(201, 596), fontSize: 25,
					card: true, thirdCard: true, display: []byte("Moderate"), displayLinear: 0x2a718,
					cursorGuard: image.Rect(3, 119, 110, 177), inkSize: image.Pt(54, 23)})
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
					inkSize: image.Pt(92, 19), cardColor: 12},
				{id: "LABELS.TXT:0x000008F2", file: "LABELS.TXT", offset: 0x8f2, length: 11,
					linear: 0x4dfd1, readCS: 0x0e2d, readIP: 0x11cf,
					safe: image.Rect(125, 83, 190, 96), bbox: image.Rect(135, 87, 178, 93),
					pixels: 156, position: image.Pt(597, 348), fontSize: 25,
					nationCard: true, display: []byte("Immigration"), displayLinear: 0x2a6ae,
					inkSize: image.Pt(54, 23), cardColor: 12},
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
		if *restCardsA {
			// 規格022目標140：滑過、按下或放開其餘旗卡時原版重印兩欄；顯示字串都在0x2A716。
			type restField struct {
				id, file       string
				offset, length int
				linear         uint32
				safe, bbox     image.Rectangle
				pixels         int
				position       image.Point
				size           int
				display        string
				ink            image.Point
				color          byte
			}
			for _, f := range []restField{
				{"NAMES.TXT:0x00000906", "NAMES.TXT", 0x906, 6, 0x4cbc6, image.Rect(225, 12, 290, 24), image.Rect(242, 15, 268, 20), 100, image.Pt(986, 60), 21, "FRANCE:", image.Pt(69, 19), 9},
				{"LABELS.TXT:0x000008FF", "LABELS.TXT", 0x8ff, 11, 0x4dfdd, image.Rect(225, 83, 290, 96), image.Rect(235, 87, 276, 93), 136, image.Pt(993, 348), 25, "Cooperation", image.Pt(54, 23), 9},
				{"NAMES.TXT:0x00000921", "NAMES.TXT", 0x921, 5, 0x4cbcd, image.Rect(125, 103, 190, 115), image.Rect(145, 106, 167, 111), 82, image.Pt(578, 424), 21, "SPAIN:", image.Pt(92, 19), 14},
				{"LABELS.TXT:0x0000090C", "LABELS.TXT", 0x90c, 8, 0x4dfe9, image.Rect(125, 174, 190, 187), image.Rect(141, 178, 172, 184), 106, image.Pt(597, 712), 25, "Conquest", image.Pt(54, 23), 14},
				{"NAMES.TXT:0x0000093D", "NAMES.TXT", 0x93d, 11, 0x4cbd3, image.Rect(225, 103, 290, 115), image.Rect(232, 106, 278, 111), 184, image.Pt(986, 424), 21, "NETHERLANDS:", image.Pt(69, 19), 13},
				{"LABELS.TXT:0x00000916", "LABELS.TXT", 0x916, 5, 0x4dff2, image.Rect(225, 174, 290, 187), image.Rect(246, 178, 266, 183), 66, image.Pt(993, 712), 25, "Trade", image.Pt(54, 23), 13},
			} {
				l := &difficultyLine{id: f.id, file: f.file, offset: f.offset, length: f.length,
					linear: f.linear, readCS: 0x0e2d, readIP: 0x11cf, safe: f.safe, bbox: f.bbox,
					pixels: f.pixels, position: f.position, fontSize: f.size, nationCard: true, restCard: true,
					display: []byte(f.display), displayLinear: 0x2a716, inkSize: f.ink, cardColor: f.color}
				if f.file == "NAMES.TXT" {
					l.source = bytes.Clone(namesSource[f.offset : f.offset+f.length])
				} else {
					l.source = bytes.Clone(labelsSource[f.offset : f.offset+f.length])
				}
				difficulty = append(difficulty, l)
			}
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
		for _, c := range captions {
			for i, key := range c.keys {
				if get(row, "candidate_id") != key {
					continue
				}
				c.keyMatches[i]++
				offset, parseErr := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
				c.keyValid[i] = parseErr == nil && int(offset) == c.keyOffsets[i] &&
					get(row, "source_file") == "GAME.TXT" &&
					get(row, "source_sha256") == versions["GAME.TXT"] &&
					get(row, "source_bytes_sha256") == hash(c.keySources[i]) &&
					get(row, "source_byte_length") == strconv.Itoa(len(c.keySources[i])) &&
					get(row, "status") == "draft"
				c.keyTranslations[i] = get(row, "zh_hant")
			}
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
		for _, ev := range retire {
			for _, f := range ev.fields {
				if get(row, "candidate_id") != f.id {
					continue
				}
				f.matches++
				offset, parseErr := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
				f.valid = parseErr == nil && int(offset) == f.offset && get(row, "source_file") == "GAME.TXT" &&
					get(row, "source_sha256") == versions["GAME.TXT"] &&
					get(row, "source_bytes_sha256") == hash(rawSource[f.offset:f.offset+f.length]) &&
					get(row, "source_byte_length") == strconv.Itoa(f.length) && get(row, "status") == "draft"
				f.translation = get(row, "zh_hant")
			}
		}
		if rows != nil {
			for _, r := range rows.rows {
				if get(row, "candidate_id") != r.id {
					continue
				}
				r.matches++
				offset, parseErr := strconv.ParseUint(get(row, "byte_offset"), 0, 32)
				r.valid = parseErr == nil && int(offset) == r.offset &&
					get(row, "source_file") == "GAME.TXT" &&
					get(row, "source_sha256") == versions["GAME.TXT"] &&
					get(row, "source_bytes_sha256") == hash(r.source) &&
					get(row, "source_byte_length") == strconv.Itoa(len(r.source)) &&
					get(row, "status") == "draft"
				r.translation = get(row, "zh_hant")
			}
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
	if *nationCardA || *restCardsA {
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
		if l.thirdCard {
			maskDir = *thirdCardFonts
		}
		if l.restCard {
			maskDir = *restCardFonts
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
		if l.prompt || l.nationCard || l.thirdCard {
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
	// 規格026目標141：字幕變數只取英格蘭列；來源片段、檔案指紋與原文逐列核對。
	type captionValue struct{ en, zh string }
	captionValues := map[string]map[string]captionValue{}
	valuesHash := ""
	if *buildCaptionsA {
		valuesBytes, readErr := os.ReadFile(*buildValues)
		valuesOK := readErr == nil
		if valuesOK {
			valuesHash = hash(valuesBytes)
			vr := csv.NewReader(bytes.NewReader(valuesBytes))
			vr.Comma = '\t'
			header, e := vr.Read()
			col := map[string]int{}
			for i, h := range header {
				col[h] = i
			}
			for e == nil {
				var row []string
				if row, e = vr.Read(); e != nil {
					break
				}
				vget := func(k string) string {
					if i, ok := col[k]; ok && i < len(row) {
						return row[i]
					}
					return ""
				}
				if vget("nation") != "england" {
					continue
				}
				file := vget("source_file")
				offset, perr := strconv.ParseUint(vget("byte_offset"), 0, 32)
				length, lerr := strconv.Atoi(vget("source_byte_length"))
				var src []byte
				if file == "NAMES.TXT" {
					src = namesSource
				} else if file == "GAME.TXT" {
					src = rawSource
				}
				ok := perr == nil && lerr == nil && src != nil && versions[file] == vget("source_file_sha256") &&
					int(offset)+length <= len(src) && string(src[offset:int(offset)+length]) == vget("source_text") &&
					vget("observed_text") == vget("source_text") && vget("zh_hant") != "" && vget("status") == "draft"
				vm := captionValues[vget("caption")]
				if vm == nil {
					vm = map[string]captionValue{}
					captionValues[vget("caption")] = vm
				}
				if _, dup := vm[vget("placeholder")]; dup || !ok {
					vm[vget("placeholder")] = captionValue{} // 重複或來源不符：該變數視為缺值
				} else {
					vm[vget("placeholder")] = captionValue{vget("source_text"), vget("zh_hant")}
				}
			}
			valuesOK = e == io.EOF
		}
		if !valuesOK {
			captionValues = nil
		}
	}
	placeholder := regexp.MustCompile(`%STRING[0-9]`)
	expand := func(text string, vals map[string]captionValue, english bool) (string, bool) {
		ok := true
		out := placeholder.ReplaceAllStringFunc(text, func(name string) string {
			v, found := vals[name]
			if !found || v.en == "" {
				ok = false
				return name
			}
			if english {
				return v.en
			}
			return v.zh
		})
		return out, ok
	}
	for _, c := range captions {
		lines := []string{}
		valid := true
		for i := range c.keys {
			t := c.keyTranslations[i]
			if c.keyMatches[i] != 1 || !c.keyValid[i] || !strings.HasPrefix(t, "^^") || strings.Contains(t[2:], "^") || len(t) <= 2 {
				valid = false
				break
			}
			lines = append(lines, t[2:])
		}
		if c.id != "GAME.TXT:0x000153CC" && valid {
			// 以英格蘭變數原文展開原版行，須與雙冷啟動實測的當次顯示字串相同。
			vals := captionValues[c.captionName]
			display, ok := expand(string(c.display), vals, true)
			c.displayOK = ok && hash([]byte(display)) == c.displaySHA
			if c.displayOK {
				c.display = []byte(display)
			}
			for i := range lines {
				if lines[i], ok = expand(lines[i], vals, false); !ok {
					valid = false
				}
			}
		}
		if !valid {
			c.fontReason = "missing-or-invalid-translation"
		} else if !c.displayOK {
			c.fontReason = "display-values-mismatch"
		} else {
			c.translation = strings.Join(lines, "\n")
			var mask fontMask
			maskBytes, readErr := os.ReadFile(c.maskPath)
			if readErr != nil || json.Unmarshal(maskBytes, &mask) != nil {
				c.fontReason = "font-mask-unavailable"
			} else if mask.CandidateID != c.id || mask.CatalogHash != hash(catalogBytes) ||
				mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(c.translation)) ||
				mask.FontSize != 38 || (c.id != "GAME.TXT:0x000153CC" && mask.ValuesHash != valuesHash) {
				c.fontReason = "font-binding-mismatch"
			} else {
				if c.id != "GAME.TXT:0x000153CC" {
					// 共同中線 x=638（同 @BUILD1），頂端 y=120；前景與向右下4像素的陰影都須在安全區內。
					c.inkSize = image.Pt(mask.Width, mask.Height)
					c.fgPos = image.Pt(638-mask.Width/2, 120)
				}
				r := image.Rectangle{Min: c.fgPos, Max: c.fgPos.Add(c.inkSize).Add(image.Pt(4, 4))}
				if mask.Width != c.inkSize.X || mask.Height != c.inkSize.Y || len(mask.Alpha) != mask.Width*mask.Height ||
					mask.Width <= 0 || mask.Height <= 0 ||
					!r.In(image.Rectangle{Min: c.safe.Min.Mul(4), Max: c.safe.Max.Mul(4)}) {
					c.fontReason = "font-mask-out-of-bounds"
				} else {
					c.ink = image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
					copy(c.ink.Pix, mask.Alpha)
				}
			}
		}
		if *missing {
			c.ink = nil
			c.fontReason = "missing-ink"
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
	for _, ev := range retire {
		for _, f := range ev.fields {
			if f.matches != 1 || !f.valid || f.translation == "" || strings.ContainsAny(f.translation, "~^\n\r") {
				f.fontReason = "missing-or-invalid-translation"
				continue
			}
			var mask fontMask
			b, e := os.ReadFile(filepath.Join(*retireFonts, strings.ReplaceAll(f.id, ":", "-")+".json"))
			if e != nil || json.Unmarshal(b, &mask) != nil {
				f.fontReason = "font-mask-unavailable"
			} else if mask.CandidateID != f.id || mask.CatalogHash != hash(catalogBytes) || mask.FontHash != fontHash ||
				mask.TranslationHash != hash([]byte(f.translation)) || mask.FontSize != 34 {
				f.fontReason = "font-binding-mismatch"
			} else if mask.Width != f.size.X || mask.Height != f.size.Y || len(mask.Alpha) != mask.Width*mask.Height {
				f.fontReason = "font-mask-out-of-bounds"
			} else {
				f.ink = image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
				copy(f.ink.Pix, mask.Alpha)
			}
			if *missing {
				f.ink, f.fontReason = nil, "missing-ink"
			}
		}
	}
	if rows != nil {
		for i, r := range rows.rows {
			// 使用者定案：「(~X) 中文」，X 必須是原版該列快捷鍵；畫面只去掉 ~。
			prefix := "(~" + string(r.hotkey) + ") "
			if r.matches != 1 || !r.valid || !strings.HasPrefix(r.translation, prefix) ||
				len(r.translation) <= len(prefix) || strings.Count(r.translation, "~") != 1 ||
				strings.ContainsAny(r.translation, "^\n\r") {
				r.fontReason = "missing-or-invalid-translation"
				continue
			}
			r.translation = strings.Replace(r.translation, "~", "", 1)
			var mask fontMask
			maskBytes, readErr := os.ReadFile(filepath.Join(*optionRowsFonts, strings.ReplaceAll(r.id, ":", "-")+".json"))
			if readErr != nil || json.Unmarshal(maskBytes, &mask) != nil {
				r.fontReason = "font-mask-unavailable"
			} else if mask.CandidateID != r.id || mask.CatalogHash != hash(catalogBytes) ||
				mask.FontHash != fontHash || mask.TranslationHash != hash([]byte(r.translation)) ||
				mask.FontSize != optionRowSizes[i] {
				r.fontReason = "font-binding-mismatch"
			} else if mask.Width != optionRowInk[i].X || mask.Height != optionRowInk[i].Y ||
				len(mask.Alpha) != mask.Width*mask.Height {
				r.fontReason = "font-mask-out-of-bounds"
			} else {
				r.ink = image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
				copy(r.ink.Pix, mask.Alpha)
			}
			if *missing {
				r.ink = nil
				r.fontReason = "missing-ink"
			}
		}
	}
	m := golem.New()
	must(m.LoadEXE(read(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	if *scratch != "" {
		// 寫入只落在暫存層；原版 Root 仍唯讀，暫存層不得等於 Root。
		st, err := os.Stat(*scratch)
		must(err)
		rootAbs, err := filepath.EvalSymlinks(*root)
		must(err)
		scratchAbs, err := filepath.EvalSymlinks(*scratch)
		must(err)
		if !st.IsDir() || rootAbs == scratchAbs {
			panic("可寫暫存層不存在或等於原版 Root")
		}
		d.Scratch = *scratch
	}
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
	captionExpire := func(caption *buildCaption, reason string) {
		if caption.phase == "idle" || caption.phase == "expired" {
			return
		}
		events = append(events, map[string]any{"candidate_id": caption.id, "stage": "expired", "step": m.Steps, "reason": reason})
		caption.phase, caption.patch, caption.before = "expired", nil, nil
	}
	captionAnyInk := false
	for _, c := range captions {
		captionAnyInk = captionAnyInk || c.ink != nil
	}
	titleExpire := func(reason string) {
		if title == nil || title.phase == "idle" || title.phase == "expired" {
			return
		}
		events = append(events, map[string]any{"candidate_id": title.id, "stage": "expired", "step": m.Steps, "reason": reason})
		title.phase, title.patch, title.before, title.afterSafe = "expired", nil, nil, nil
	}
	rowsAnyInk := false
	if rows != nil {
		for _, r := range rows.rows {
			rowsAnyInk = rowsAnyInk || r.ink != nil
		}
	}
	rowExpire := func(r *optionRow, reason string) {
		if r.phase == "idle" || r.phase == "expired" {
			return
		}
		events = append(events, map[string]any{"candidate_id": r.id, "stage": "expired", "step": m.Steps, "reason": reason})
		r.phase, r.patch, r.before, r.afterSafe = "expired", nil, nil, nil
	}
	rowsExpire := func(reason string) {
		if rows == nil {
			return
		}
		if rows.phase == "reading" || rows.phase == "waiting-screen" {
			events = append(events, map[string]any{"candidate_id": "GAME.TXT:options-rows", "stage": "expired", "step": m.Steps, "reason": reason})
			rows.phase = "expired"
		}
		for _, r := range rows.rows {
			rowExpire(r, reason)
		}
	}
	helpAnyInk := help != nil && help.normal != nil
	seaOn := sea != nil && sea.glyphs != nil
	// seaFinish 把完成的印字事件歸入頂列或狀態欄；無法翻譯者記錄缺譯並保留原文。
	seaFinish := func() {
		ev := sea.cur
		sea.cur = nil
		if ev == nil || ev.writes == 0 {
			return
		}
		interleaved := len(ev.raw) == 2 && ev.raw[1] == 0
		text := strings.TrimRight(string(ev.raw), "\x00")
		if interleaved {
			text = string(ev.raw[:1])
		}
		row := &seaRow{bbox: ev.bbox, text: text, firstOld: ev.firstOld, lastVal: ev.lastVal}
		switch {
		case ev.bbox.In(seaBarRect) && interleaved:
			// 選單列逐字印出；從第一個字 G（x=13）起累積，整列 39 字完全相同才成立。
			if text == "G" && ev.bbox.Min.X == 13 {
				sea.menuRun = nil
			}
			sea.menuRun = append(sea.menuRun, ev)
			got := ""
			for _, g := range sea.menuRun {
				got += string(g.raw[:1])
			}
			if !strings.HasPrefix(seaMenuText, got) {
				sea.menuRun = nil
				return
			}
			if got != seaMenuText {
				return
			}
			menuRow := &seaRow{text: got, firstOld: map[int]byte{}, lastVal: map[int]byte{}}
			k := 0
			for w, n := range seaMenuWords {
				first := sea.menuRun[k].bbox
				parts := strings.SplitN(sea.menu[w], "\x00", 2)
				x := first.Min.X * 4
				menuRow.parts = append(menuRow.parts, seaPart{parts[0], 149, x, 22})
				key, _ := sea.seaWidth(parts[0])
				menuRow.parts = append(menuRow.parts, seaPart{parts[1], 68, x + key, 22})
				k += n
			}
			for _, g := range sea.menuRun {
				menuRow.bbox = menuRow.bbox.Union(g.bbox)
				for i, v := range g.firstOld {
					menuRow.firstOld[i] = v
				}
				for i, v := range g.lastVal {
					menuRow.lastVal[i] = v
				}
			}
			sea.menuRun = nil
			sea.bar.rows, sea.bar.dirty = []*seaRow{menuRow}, true
		case ev.bbox.In(seaBarRect):
			sea.menuRun = nil
			zh, ok := sea.seaTranslate(text)
			size := sea.seaFit(zh, 1280-2)
			if !ok || size == 0 {
				sea.misses[text]++
				sea.bar.rows, sea.bar.dirty = nil, true
				return
			}
			w, _ := sea.seaWidthAt(zh, size)
			row.parts = []seaPart{{zh, 149, 640 - w/2, size}}
			sea.bar.rows, sea.bar.dirty = []*seaRow{row}, true
		case ev.bbox.In(seaPanelRect) && !interleaved:
			kept := sea.panel.rows[:0]
			for _, r := range sea.panel.rows {
				if !r.bbox.Overlaps(ev.bbox) {
					kept = append(kept, r)
				}
			}
			sea.panel.rows, sea.panel.dirty = kept, true
			color := byte(0)
			for c := range ev.colors {
				color = c
			}
			zh, ok := sea.seaTranslate(text)
			// 右界留 2 輸出像素給陰影；放不下時逐級縮字，到 15px 仍不行則保留原文。
			size := sea.seaFit(zh, seaPanelRect.Max.X*4-ev.bbox.Min.X*4-2)
			if !ok || size == 0 || len(ev.colors) != 1 || (color != 68 && color != 149) {
				sea.misses[text]++
				return
			}
			row.parts = []seaPart{{zh, color, ev.bbox.Min.X * 4, size}}
			sea.panel.rows = append(sea.panel.rows, row)
		}
	}
	helpExpire := func(reason string) {
		if help == nil || help.phase == "idle" || help.phase == "expired" {
			return
		}
		events = append(events, map[string]any{"candidate_id": help.id, "stage": "expired", "step": m.Steps, "reason": reason})
		help.phase, help.patch, help.afterSafe, help.firstOld, help.lastText = "expired", nil, nil, nil, nil
	}
	introAnyInk := false
	if intro != nil {
		for _, pg := range intro.pages {
			introAnyInk = introAnyInk || pg.normal != nil
		}
	}
	introExpire := func(reason string) {
		if intro == nil || intro.phase == "idle" || intro.phase == "expired" {
			return
		}
		id := "GAME.TXT:@NATION"
		if intro.page != nil {
			id = intro.page.id
		}
		events = append(events, map[string]any{"candidate_id": id, "stage": "expired", "step": m.Steps, "reason": reason})
		intro.phase, intro.page, intro.patch, intro.before, intro.afterSafe = "expired", nil, nil, nil, nil
	}
	retireAnyInk := false
	for _, ev := range retire {
		for _, f := range ev.fields {
			retireAnyInk = retireAnyInk || f.ink != nil
		}
	}
	var retireCurrent *retireEvent // 最近開始讀字的退休框事件；改色只歸屬於它
	retireExpire := func(ev *retireEvent, reason string) {
		if ev.phase == "reading" || ev.phase == "waiting" {
			ev.phase = "expired"
		}
		for _, f := range ev.fields {
			if f.phase != "idle" && f.phase != "expired" {
				events = append(events, map[string]any{"candidate_id": f.id, "stage": "expired", "step": m.Steps, "reason": reason})
			}
			f.phase, f.patch, f.before, f.afterSafe = "expired", nil, nil, nil
		}
	}
	if !*control && (captionAnyInk || (title != nil && title.ink != nil) || rowsAnyInk || introAnyInk || retireAnyInk || helpAnyInk || seaOn) {
		m.WatchWrites(0x2cae0, 0x2cae0+64000, func(a uint32, old, value uint8) {
			if old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			x, y := int(a-0x2cae0)%320, int(a-0x2cae0)/320
			for _, ev := range retire {
				if ev.phase != "reading" || ev != retireCurrent {
					continue
				}
				var target *retireField
				for _, f := range ev.fields {
					if image.Pt(x, y).In(f.rect) {
						target = f
					}
				}
				if cs == 0x0d21 && ip == 0x012c {
					if target == nil || (value != 47 && value != 68 && value != 128) {
						retireExpire(ev, "write-outside-reviewed-pixels")
						continue
					}
					if target.got == 0 {
						target.before = bytes.Clone(canvas())
						target.before[a-0x2cae0] = old
						if hash(rectBytes(target.before, target.rect)) != target.background {
							retireExpire(ev, "field-background-not-reviewed")
							continue
						}
						target.gotBBox = image.Rect(x, y, x+1, y+1)
					}
					target.got++
					target.gotBBox = target.gotBBox.Union(image.Rect(x, y, x+1, y+1))
					if target.got > target.writes {
						retireExpire(ev, "write-count-exceeded")
					}
				} else if cs == 0x0b68 && ip == 0x051c && target == nil &&
					image.Pt(x, y).In(cursorBox(int(d.Mouse.X), int(d.Mouse.Y)).Inset(-2)) {
					// 原版游標常式在當下游標範圍暫寫底層並還原；不碰三欄即不影響本事件。
				} else if !(cs == 0x0cae && ip == 0x00a8 && image.Pt(x, y).In(ev.helper) && (target == nil || target.got == 0)) {
					// 原版在 Yes 印完、No 印字前以 0CAE:00A8 畫 No 按鈕底圖；其他情形一律撤銷。
					retireExpire(ev, fmt.Sprintf("unexpected-canvas-writer %04X:%04X (%d,%d)", cs, ip, x, y))
				}
			}
			if seaOn && sea.cur != nil && cs == 0x0d21 && ip == 0x012c && m.Steps-sea.cur.last < 200000 {
				ev, i := sea.cur, y*320+x
				if _, seen := ev.firstOld[i]; !seen {
					ev.firstOld[i] = old
				}
				ev.lastVal[i] = value
				ev.writes++
				ev.colors[value]++
				if ev.writes == 1 {
					ev.bbox = image.Rect(x, y, x+1, y+1)
				} else {
					ev.bbox = ev.bbox.Union(image.Rect(x, y, x+1, y+1))
				}
			}
			if help != nil && help.phase == "reading" {
				i := y*320 + x
				if cs == 0x0d21 && ip == 0x012c {
					if !image.Pt(x, y).In(helpText) {
						helpExpire("write-outside-reviewed-pixels")
					} else {
						if help.writes == 0 {
							help.bbox = image.Rect(x, y, x+1, y+1)
						} else {
							help.bbox = help.bbox.Union(image.Rect(x, y, x+1, y+1))
						}
						if _, seen := help.firstOld[i]; !seen {
							help.firstOld[i] = old
						}
						help.lastText[i] = true
						help.writes++
						if help.writes > 3258 {
							helpExpire("write-count-exceeded")
						}
					}
				} else if cs == 0x0d46 && (ip == 0x0181 || ip == 0x01b4 || ip == 0x01d2) && image.Pt(x, y).In(helpPortrait) {
					help.lastText[i] = false // 顧問肖像蓋過的像素保留原版印後值
				} else if !(cs == 0x0b68 && ip == 0x051c && image.Pt(x, y).In(cursorBox(int(d.Mouse.X), int(d.Mouse.Y)).Inset(-2))) {
					helpExpire(fmt.Sprintf("unexpected-canvas-writer %04X:%04X (%d,%d)", cs, ip, x, y))
				}
			}
			if intro != nil && intro.phase == "reading" {
				mx, my := int(d.Mouse.X), int(d.Mouse.Y)
				if cs == 0x0d21 && ip == 0x012c {
					if !image.Pt(x, y).In(intro.textArea) {
						introExpire("write-outside-reviewed-pixels")
					} else {
						if intro.writes == 0 {
							intro.bbox = image.Rect(x, y, x+1, y+1)
						} else {
							intro.bbox = intro.bbox.Union(image.Rect(x, y, x+1, y+1))
						}
						intro.writes++
						if intro.writes > intro.maxWrites {
							introExpire("write-count-exceeded")
						}
					}
				} else if !(cs == 0x0b68 && ip == 0x051c && image.Pt(x, y).In(cursorBox(mx, my).Inset(-2))) {
					// 原版游標常式會暫時寫入底層並還原；其他寫入者一律撤銷。
					introExpire("unexpected-canvas-writer")
				}
			}
			if rows != nil && rows.phase == "reading" {
				row := -1
				for i := range rows.rows {
					if image.Pt(x, y).In(optionRowSafe(i)) {
						row = i
					}
				}
				if cs != 0x0d21 || ip != 0x012c {
					// 點擊重印時原版以 0CAE:00A8 在事件中途畫被點列的反白底圖；只接受尚未印字的列、
					// 左側圖示欄與反白條右端，已印字列被改即撤銷。
					if cs != 0x0cae || ip != 0x00a8 || y < 59 || y >= 155 || x < 60 || x >= 260 ||
						(row >= 0 && rows.rows[row].writes != 0) {
						rowsExpire("unexpected-canvas-writer")
					}
				} else if value != 47 && value != 68 && value != 128 && value != 149 {
					rowsExpire("write-outside-reviewed-colors")
				} else if row < 0 {
					// 核取圖示在八列安全矩形左側；其他位置一律拒絕。
					if x < 70 || x >= 80 || y < 59 || y >= 155 {
						rowsExpire("write-outside-reviewed-pixels")
					} else if rows.outside++; rows.outside > 344 {
						rowsExpire("write-count-exceeded")
					}
				} else {
					r := rows.rows[row]
					if r.writes == 0 {
						r.before = bytes.Clone(canvas())
						r.before[a-0x2cae0] = old
						bg := hash(optionRowSafeBytes(r.before, row))
						if bg != optionRowBackgrounds[row%2][0] && bg != optionRowBackgrounds[row%2][1] {
							rowsExpire("row-background-not-reviewed")
							return
						}
					}
					r.writes++
					if r.writes > optionRowWrites[row] {
						rowsExpire("write-count-exceeded")
					}
				}
			}
			for _, caption := range captions {
				if caption.phase != "reading" {
					continue
				}
				if cs != 0x0d21 || ip != 0x012c {
					captionExpire(caption, "unexpected-canvas-writer")
				} else if !image.Pt(x, y).In(caption.safe) || (value != 14 && value != 47 && value != 54) {
					captionExpire(caption, "write-outside-reviewed-pixels")
				} else {
					if caption.writes == 0 {
						caption.bbox = image.Rect(x, y, x+1, y+1)
					} else {
						caption.bbox = caption.bbox.Union(image.Rect(x, y, x+1, y+1))
					}
					caption.writes++
					caption.colors[value]++
					if caption.writes > caption.writeCount {
						captionExpire(caption, "write-count-exceeded")
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
			for _, caption := range captions {
				if caption.ink == nil || cs != 0x0d21 || ip != 0x00c6 {
					continue
				}
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				if (caption.phase == "idle" || caption.phase == "expired") && a == caption.base &&
					m.VideoMode() == 0x13 && m.Mem[a] == caption.display[0] &&
					hash(canvas()) == caption.beforeSHA {
					caption.before = bytes.Clone(canvas())
					caption.phase, caption.startStep, caption.openedCount = "reading", m.Steps, len(d.Opened)
					caption.patch, caption.readPos, caption.writes = nil, 0, 0
					caption.bbox = image.Rectangle{}
					caption.colors = make(map[byte]int)
					events = append(events, map[string]any{"candidate_id": caption.id, "stage": "source", "step": m.Steps, "entry_ip": "0D21:00C6", "source_linear": a})
				}
				if caption.phase == "reading" {
					p := caption.readPos
					wantAddr := caption.base + uint32(p%2)
					want := byte(0)
					if p%2 == 0 && p/2 < len(caption.display) {
						want = caption.display[p/2]
					}
					if p >= 2*len(caption.display) || a != wantAddr || m.Mem[a] != want {
						captionExpire(caption, "source-read-mismatch")
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
			if retireAnyInk && cs == 0x0d21 && ip == 0x00c6 {
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				for _, ev := range retire {
					for _, base := range ev.bases {
						if ev.phase != "reading" && a == base && m.Mem[a] == ev.first && m.VideoMode() == 0x13 {
							retireExpire(ev, "superseded-by-new-print")
							ev.phase, ev.base, ev.sum, ev.readPos, ev.charCount = "reading", base, sha256.New(), 0, 0
							ev.startStep, ev.openedCount = m.Steps, len(d.Opened)
							retireCurrent = ev
							for _, f := range ev.fields {
								f.phase, f.got, f.before, f.patch, f.afterSafe = "reading", 0, nil, nil, nil
							}
							events = append(events, map[string]any{"candidate_id": ev.fields[0].id, "stage": "source", "step": m.Steps, "entry_ip": "0D21:00C6", "source_linear": a})
						}
					}
					if ev.phase != "reading" || (a != ev.base && a != ev.base+1) {
						continue
					}
					if a != ev.base+uint32(ev.readPos%2) || (ev.readPos%2 == 1 && m.Mem[a] != 0) {
						retireExpire(ev, "source-read-mismatch")
						continue
					}
					if ev.readPos%2 == 0 {
						ev.sum.Write([]byte{m.Mem[a]})
						ev.charCount++
						if ev.charCount > ev.chars {
							retireExpire(ev, "source-read-count-exceeded")
							continue
						}
					}
					ev.readPos++
					ev.lastRead = m.Steps
				}
			}
			if seaOn && cs == 0x0d21 && ip == 0x00c6 {
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				if sea.cur == nil || a != sea.cur.next || m.Steps-sea.cur.last > 200000 {
					seaFinish()
					sea.cur = &seaEvent{firstOld: map[int]byte{}, lastVal: map[int]byte{}, colors: map[byte]int{}}
				}
				sea.cur.raw = append(sea.cur.raw, m.Mem[a])
				sea.cur.next, sea.cur.last = a+1, m.Steps
			}
			if helpAnyInk && cs == 0x0d21 && ip == 0x00c6 {
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				if a == helpReadBase || a == helpReadBase+1 {
					if help.phase != "reading" && a == helpReadBase && m.VideoMode() == 0x13 && m.Mem[a] == 'O' &&
						hash(canvas()) == helpBeforeSHA {
						helpExpire("superseded-by-new-print")
						help.phase, help.chars, help.readPos, help.writes = "reading", 0, 0, 0
						help.sum, help.firstOld, help.lastText = sha256.New(), map[int]byte{}, map[int]bool{}
						help.startStep = m.Steps
						events = append(events, map[string]any{"candidate_id": help.id, "stage": "source", "step": m.Steps, "entry_ip": "0D21:00C6", "source_linear": a})
					}
					if help.phase == "reading" {
						if a != helpReadBase+uint32(help.readPos%2) || (help.readPos%2 == 1 && m.Mem[a] != 0) {
							helpExpire("source-read-mismatch")
						} else {
							if help.readPos%2 == 0 {
								help.sum.Write([]byte{m.Mem[a]})
								help.chars++
								if help.chars > 205 {
									helpExpire("source-read-count-exceeded")
								}
							}
							help.readPos++
							help.lastRead = m.Steps
						}
					}
				}
			}
			if intro != nil && introAnyInk && cs == 0x0d21 && ip == 0x00c6 {
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				if a == introReadLinear || a == introReadLinear+1 {
					if intro.phase != "reading" && a == introReadLinear && m.VideoMode() == 0x13 &&
						hash(canvas()) == introPreprint {
						introExpire("superseded-by-new-print")
						intro.phase, intro.page, intro.chars, intro.readPos, intro.writes = "reading", nil, 0, 0, 0
						intro.sum, intro.before = sha256.New(), bytes.Clone(canvas())
						intro.startStep, intro.openedCount = m.Steps, len(d.Opened)
						events = append(events, map[string]any{"candidate_id": "GAME.TXT:@NATION", "stage": "source", "step": m.Steps, "entry_ip": "0D21:00C6", "source_linear": a})
					}
					if intro.phase == "reading" {
						if a != introReadLinear+uint32(intro.readPos%2) || (intro.readPos%2 == 1 && m.Mem[a] != 0) {
							introExpire("source-read-mismatch")
						} else {
							if intro.readPos%2 == 0 {
								intro.sum.Write([]byte{m.Mem[a]})
								intro.chars++
								if intro.chars > intro.maxChars {
									introExpire("source-read-count-exceeded")
								}
							}
							intro.readPos++
							intro.lastRead = m.Steps
						}
					}
				}
			}
			if rows != nil && rowsAnyInk && cs == 0x0d21 && ip == 0x00c6 {
				a := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX])
				base := a &^ 1
				if rows.phase != "reading" && (base == 0x2adde || base == 0x2ae46) && a == base &&
					m.VideoMode() == 0x13 && (m.Mem[a] == '[' || m.Mem[a] == ']') {
					// 新的整組事件：舊權杖一律作廢，改以本次原版輸出為準。
					rowsExpire("superseded-by-new-print")
					rows.phase, rows.base, rows.readPos, rows.outside = "reading", base, 0, 0
					rows.startStep, rows.openedCount = m.Steps, len(d.Opened)
					for _, r := range rows.rows {
						r.phase, r.writes, r.before, r.patch, r.afterSafe = "reading", 0, nil, nil, nil
					}
					events = append(events, map[string]any{"candidate_id": "GAME.TXT:options-rows", "stage": "source", "step": m.Steps, "entry_ip": "0D21:00C6", "source_linear": a})
				}
				if rows.phase == "reading" {
					p := rows.readPos
					want := byte(0)
					if p < len(rows.expect) {
						want = rows.expect[p]
					}
					got := m.Mem[a]
					ok := p < len(rows.expect) && a == rows.base+uint32(p%2) &&
						(got == want || (want == 0xff && (got == '[' || got == ']')))
					if !ok {
						rowsExpire("source-read-mismatch")
					} else if rows.readPos++; rows.readPos == len(rows.expect) {
						rows.completeStep = m.Steps
						rows.phase = "waiting-screen"
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
	captionCursorBlocked := func(caption *buildCaption) bool {
		x, y := int(d.Mouse.X), int(d.Mouse.Y)
		// 只守住中譯實際墨跡與陰影（四倍座標換回邏輯像素外擴）；英語原文周圍的寬安全區仍可正常移鼠。
		ink := image.Rect(caption.fgPos.X/4, caption.fgPos.Y/4,
			(caption.fgPos.X+caption.inkSize.X+4+3)/4, (caption.fgPos.Y+caption.inkSize.Y+4+3)/4)
		return d.Mouse.Buttons != 0 || image.Rect(x, y, x+16, y+16).Overlaps(ink)
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
		for _, ev := range retire {
			if !retireAnyInk || *control {
				break
			}
			if (ev.phase == "reading" || ev.phase == "waiting") && (m.VideoMode() != 0x13 || len(d.Opened) != ev.openedCount) {
				retireExpire(ev, "mode-or-file-changed")
			}
			if ev.phase == "reading" {
				complete := ev.charCount == ev.chars && ev.readPos == 2*ev.chars &&
					fmt.Sprintf("%x", ev.sum.Sum(nil)) == ev.printSHA && m.Steps-ev.lastRead > 20000
				for _, f := range ev.fields {
					complete = complete && f.got == f.writes && f.gotBBox.Eq(f.bbox) && f.before != nil
				}
				if complete {
					ev.phase, ev.completeStep = "waiting", m.Steps
					for _, f := range ev.fields {
						f.phase = "waiting-screen"
					}
				} else if m.Steps-ev.startStep > 2000000 {
					retireExpire(ev, "incomplete-reviewed-output")
				}
			}
			for _, f := range ev.fields {
				switch f.phase {
				case "waiting-screen":
					if m.Steps-ev.completeStep > 2000000 {
						retireExpire(ev, "screen-sync-timeout")
					} else if bytes.Equal(rectBytes(canvas(), f.rect), rectBytes(m.Mem[0xa0000:0xafa00], f.rect)) {
						var err error
						f.patch, err = overlay.NewPatch(f.before, canvas(), 320, 200, f.rect)
						if err != nil {
							retireExpire(ev, "invalid-observed-patch")
						} else {
							f.afterSafe, f.phase = rectBytes(canvas(), f.rect), "active"
							f.accepted++
							events = append(events, map[string]any{"candidate_id": f.id, "stage": "active", "step": m.Steps, "changed_pixels": f.got})
						}
					}
				case "active":
					if !bytes.Equal(rectBytes(canvas(), f.rect), f.afterSafe) {
						events = append(events, map[string]any{"candidate_id": f.id, "stage": "expired", "step": m.Steps, "reason": "canvas-field-changed"})
						f.phase, f.patch, f.before, f.afterSafe = "expired", nil, nil, nil
					}
				}
			}
		}
		if seaOn && !*control {
			if sea.cur != nil && m.Steps-sea.cur.last > 20000 {
				seaFinish()
			}
			for _, layer := range []*seaLayer{sea.bar, sea.panel} {
				safeBytes := func(buf []byte) []byte {
					b := make([]byte, 0, layer.safe.Dx()*layer.safe.Dy())
					for y := layer.safe.Min.Y; y < layer.safe.Max.Y; y++ {
						b = append(b, buf[y*320+layer.safe.Min.X:y*320+layer.safe.Max.X]...)
					}
					return b
				}
				if !layer.dirty && (layer.afterSafe == nil || bytes.Equal(safeBytes(canvas()), layer.afterSafe)) {
					continue
				}
				// 重建：逐行核對文字像素仍為當次改色值，且改寫前不是文字色；其餘行保留原文。
				layer.dirty, layer.patch = false, nil
				cur := canvas()
				before := bytes.Clone(cur)
				w, h := layer.safe.Dx()*4, layer.safe.Dy()*4
				layer.shadow = image.NewAlpha(image.Rect(0, 0, w, h))
				layer.fg = map[byte]*image.Alpha{68: image.NewAlpha(image.Rect(0, 0, w, h)), 149: image.NewAlpha(image.Rect(0, 0, w, h))}
				kept := layer.rows[:0]
				for _, r := range layer.rows {
					ok := len(r.parts) > 0
					for i, v := range r.lastVal {
						if cur[i] != v || r.firstOld[i] == 68 || r.firstOld[i] == 149 {
							ok = false
							break
						}
					}
					if !ok {
						continue
					}
					clipped := false
					for _, pt := range r.parts {
						y := r.bbox.Min.Y*4 - sea.fonts[pt.size].cjkTop - layer.safe.Min.Y*4
						x := pt.x - layer.safe.Min.X*4
						clipped = sea.seaDraw(layer.shadow, pt.text, x+2, y+2, pt.size) || clipped
						clipped = sea.seaDraw(layer.fg[pt.color], pt.text, x, y, pt.size) || clipped
					}
					if clipped {
						sea.misses["clipped:"+r.text]++
						continue
					}
					for i, v := range r.firstOld {
						before[i] = v
					}
					kept = append(kept, r)
				}
				layer.rows = kept
				layer.afterSafe = safeBytes(cur)
				layer.reason = "no-translated-rows"
				if len(kept) > 0 {
					if p, err := overlay.NewPatch(before, cur, 320, 200, layer.safe); err == nil {
						layer.patch, layer.reason = p, ""
						events = append(events, map[string]any{"candidate_id": layer.name, "stage": "active", "step": m.Steps, "rows": len(kept)})
					}
				}
			}
		}
		if helpAnyInk && !*control {
			if help.phase != "idle" && help.phase != "expired" && m.VideoMode() != 0x13 {
				helpExpire("mode-changed")
			}
			if help.phase == "reading" && m.Steps-help.lastRead > 20000 {
				if help.chars == 205 && help.readPos == 410 && fmt.Sprintf("%x", help.sum.Sum(nil)) == helpPrintSHA &&
					help.writes == 3258 && help.bbox.Eq(image.Rect(69, 106, 250, 165)) && hash(canvas()) == helpAfterSHA {
					help.phase, help.completeStep = "waiting-screen", m.Steps
				} else if m.Steps-help.lastRead > 2000000 {
					helpExpire("incomplete-reviewed-output")
				}
			}
			if help.phase == "waiting-screen" {
				clean := bytes.Clone(m.Mem[0xa0000:0xafa00])
				box := cursorBox(int(d.Mouse.X), int(d.Mouse.Y)).Intersect(helpText)
				for y := box.Min.Y; y < box.Max.Y; y++ {
					for x := box.Min.X; x < box.Max.X; x++ {
						clean[y*320+x] = canvas()[y*320+x]
					}
				}
				if m.Steps-help.completeStep > 2000000 {
					helpExpire("screen-sync-timeout")
				} else if bytes.Equal(helpTextBytes(clean), helpTextBytes(canvas())) {
					// 印字前底圖＝印後畫面中最後由改色常式寫下的文字像素換回第一次改寫前的值。
					before := bytes.Clone(canvas())
					for i, text := range help.lastText {
						if text {
							before[i] = help.firstOld[i]
						}
					}
					var err error
					help.patch, err = overlay.NewPatch(before, canvas(), 320, 200, helpText)
					if err != nil {
						helpExpire("invalid-observed-patch")
					} else {
						help.afterSafe = helpTextBytes(canvas())
						help.phase = "active"
						help.accepted++
						events = append(events, map[string]any{"candidate_id": help.id, "stage": "active", "step": m.Steps,
							"visible_chars": help.chars, "changed_pixels": help.writes})
					}
				}
			} else if help.phase == "active" && !bytes.Equal(helpTextBytes(canvas()), help.afterSafe) {
				helpExpire("canvas-page-changed")
			}
		}
		if intro != nil && introAnyInk && !*control {
			mx, my := int(d.Mouse.X), int(d.Mouse.Y)
			if intro.phase != "idle" && intro.phase != "expired" && (m.VideoMode() != 0x13 || len(d.Opened) != intro.openedCount) {
				introExpire("mode-or-file-changed")
			}
			if intro.phase == "reading" {
				sum := fmt.Sprintf("%x", intro.sum.Sum(nil))
				for _, pg := range intro.pages {
					if intro.chars == pg.chars && intro.readPos == 2*pg.chars && sum == pg.printSHA &&
						intro.writes == pg.writes && intro.bbox.Eq(pg.bbox) && m.Steps-intro.lastRead > 20000 {
						intro.page, intro.phase, intro.completeStep = pg, "waiting-screen", m.Steps
					}
				}
				if intro.phase == "reading" && m.Steps-intro.lastRead > 2000000 {
					introExpire("incomplete-reviewed-output")
				}
			}
			if intro.phase == "waiting-screen" {
				vga := m.Mem[0xa0000:0xafa00]
				clean := bytes.Clone(vga)
				box := cursorBox(mx, my).Intersect(introPanel)
				for y := box.Min.Y; y < box.Max.Y; y++ {
					for x := box.Min.X; x < box.Max.X; x++ {
						clean[y*320+x] = canvas()[y*320+x]
					}
				}
				if m.Steps-intro.completeStep > 2000000 {
					introExpire("screen-sync-timeout")
				} else if bytes.Equal(introPanelBytes(clean), introPanelBytes(canvas())) {
					var err error
					intro.patch, err = overlay.NewPatch(intro.before, canvas(), 320, 200, introPanel)
					if err != nil {
						introExpire("invalid-observed-patch")
					} else {
						intro.afterSafe = introPanelBytes(canvas())
						intro.phase = "active"
						intro.page.accepted++
						events = append(events, map[string]any{"candidate_id": intro.page.id, "stage": "active", "step": m.Steps,
							"visible_chars": intro.chars, "changed_pixels": intro.writes})
					}
				}
			} else if intro.phase == "active" && !bytes.Equal(introPanelBytes(canvas()), intro.afterSafe) {
				introExpire("canvas-page-changed")
			}
		}
		if rows != nil && rowsAnyInk && !*control {
			if rows.phase == "reading" && m.Steps-rows.startStep > 2000000 {
				rowsExpire("source-read-timeout")
			}
			if m.VideoMode() != 0x13 || (rows.phase != "idle" && rows.phase != "expired" && len(d.Opened) != rows.openedCount) {
				rowsExpire("mode-or-file-changed")
			}
			if rows.phase == "waiting-screen" {
				complete := rows.outside == 344
				for i, r := range rows.rows {
					complete = complete && r.writes == optionRowWrites[i] && r.before != nil
				}
				if !complete {
					if m.Steps-rows.completeStep > 2000000 {
						rowsExpire("incomplete-reviewed-output")
					}
				} else {
					rows.phase = "complete"
					rows.accepted++
					for _, r := range rows.rows {
						r.phase, r.waitSince = "waiting-screen", m.Steps
					}
				}
			}
			if rows.phase == "complete" {
				for i, r := range rows.rows {
					switch r.phase {
					case "waiting-screen":
						after := optionRowSafeBytes(canvas(), i)
						// 游標疊在真 VGA 上會讓該列暫時不同；壓在該列時不計入同步逾時，啟用仍須逐點相同。
						x, y := int(d.Mouse.X), int(d.Mouse.Y)
						if image.Rect(x, y, x+16, y+16).Overlaps(optionRowSafe(i)) {
							r.waitSince = m.Steps
						}
						if m.Steps-r.waitSince > 2000000 {
							rowExpire(r, "screen-sync-timeout")
						} else if bytes.Equal(after, optionRowSafeBytes(m.Mem[0xa0000:0xafa00], i)) {
							var err error
							r.patch, err = overlay.NewPatch(r.before, canvas(), 320, 200, optionRowSafe(i))
							if err != nil {
								rowExpire(r, "invalid-observed-patch")
							} else {
								r.afterSafe = after
								r.phase = "active"
								r.accepted++
								events = append(events, map[string]any{"candidate_id": r.id, "stage": "active", "step": m.Steps,
									"background_sha256": hash(optionRowSafeBytes(r.before, i)), "changed_pixels": r.writes})
							}
						}
					case "active":
						if !bytes.Equal(optionRowSafeBytes(canvas(), i), r.afterSafe) {
							rowExpire(r, "canvas-row-changed")
						}
					}
				}
			}
		}
		for _, caption := range captions {
			if caption.ink == nil || *control {
				continue
			}
			if caption.phase == "reading" && m.Steps-caption.startStep > 2000000 {
				captionExpire(caption, "source-read-timeout")
			}
			if caption.phase == "waiting-screen" || caption.phase == "active" {
				reads := 2 * len(caption.display)
				// 字幕顯示期間原版會在背景預載下一段資源（@BUILD1 讀 PHYS0／ICONS／BUILDING.SS，@BUILD4 讀 NAMES.TXT），
				// 畫面不變；故不以開檔數撤銷，改由完整底層畫布、色盤、模式與每幀真 VGA 守門（目標141）。
				if m.VideoMode() != 0x13 || hash(canvas()) != caption.afterSHA ||
					hash(m.DAC[:]) != "92593125369b8224c1f00b30ad0367d6f1766da49afb614dcf753ad8d70b665b" {
					captionExpire(caption, "canvas-palette-or-mode-changed")
				} else if caption.phase == "waiting-screen" && m.Steps-caption.completeStep > 2000000 {
					captionExpire(caption, "screen-sync-timeout")
				} else if caption.phase == "waiting-screen" && caption.readPos == reads && caption.writes == caption.writeCount &&
					caption.bbox.Eq(caption.inkBBox) &&
					caption.colors[14] > 0 && caption.colors[47] > 0 && (caption.colors[54] > 0) == caption.need54 &&
					hash(m.Mem[0xa0000:0xafa00]) == caption.afterSHA {
					var err error
					caption.patch, err = overlay.NewPatch(caption.before, canvas(), 320, 200, caption.safe)
					if err != nil {
						captionExpire(caption, "invalid-observed-patch")
					} else {
						caption.phase = "active"
						caption.accepted++
						b := caption.inkBBox
						events = append(events, map[string]any{"candidate_id": caption.id, "stage": "active", "step": m.Steps, "read_count": caption.readPos, "changed_pixels": caption.writes, "bbox": []int{b.Min.X, b.Min.Y, b.Max.X, b.Max.Y}})
					}
				} else if caption.phase == "waiting-screen" && caption.readPos != reads {
					captionExpire(caption, "incomplete-source-read")
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
							(l.nationCard && after[i] != 0 && after[i] != l.cardColor) ||
							(l.thirdCard && after[i] != 0 && after[i] != 14) ||
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
				} else if l.nationCard || l.thirdCard {
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
				if result.Applied && (l.prompt || l.nationCard || l.thirdCard) {
					index := 68
					if l.nationCard {
						index = int(l.cardColor)
					} else if l.thirdCard {
						index = 14
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
			for _, it := range statics {
				reason, ok := it.reason, false
				if it.mask != nil && !*control {
					region := make([]byte, 0, it.fp.Dx()*it.fp.Dy())
					for y := it.fp.Min.Y; y < it.fp.Max.Y; y++ {
						region = append(region, indexed[y*320+it.fp.Min.X:y*320+it.fp.Max.X]...)
					}
					if hash(region) != it.sha {
						reason = "fingerprint-mismatch"
					} else {
						// 文字帶內亮度低於 122 的色號視為原文（含抗鋸齒），以同列最近的非文字像素補回紋理。
						lum := func(v byte) int { return int(m.DAC[int(v)*3]) + int(m.DAC[int(v)*3+1]) + int(m.DAC[int(v)*3+2]) }
						clean := bytes.Clone(indexed)
						for y := it.band.Min.Y; y < it.band.Max.Y; y++ {
							for x := it.band.Min.X; x < it.band.Max.X; x++ {
								if lum(indexed[y*320+x]) >= 122 {
									continue
								}
							search:
								for dx := 1; dx < it.band.Dx(); dx++ {
									for _, nx := range []int{x - dx, x + dx} {
										if nx >= it.band.Min.X && nx < it.band.Max.X && lum(indexed[y*320+nx]) >= 122 {
											clean[y*320+x] = indexed[y*320+nx]
											break search
										}
									}
								}
							}
						}
						patch, err := overlay.NewPatch(clean, indexed, 320, 200, it.band)
						if err != nil {
							reason = "invalid-observed-patch"
						} else {
							frame, composed, why, err := overlay.Compose(indexed, m.DAC[:], 320, 200, 4, patch, it.mask, it.pos, it.ink, enabled)
							must(err)
							reason = why
							if composed {
								out := image.Rectangle{Min: it.band.Min.Mul(4), Max: it.band.Max.Mul(4)}
								draw.Draw(output, out, frame, out.Min, draw.Src)
								ok, reason = true, "applied"
							}
						}
					}
				}
				if ok && !it.on {
					it.accepted++
					events = append(events, map[string]any{"candidate_id": it.id, "stage": "active", "step": m.Steps})
				}
				it.on = ok
				lineRecords = append(lineRecords, map[string]any{"candidate_id": it.id, "applied": ok, "reason": reason, "accepted_events": it.accepted})
			}
			if sea != nil {
				for _, layer := range []*seaLayer{sea.bar, sea.panel} {
					reason, ok := seaReason, false
					if reason == "" {
						reason = layer.reason
					}
					if seaOn && !*control && layer.patch != nil {
						// 游標範圍換回印後底層再比對；中文畫完後把真 VGA 的游標像素疊回最上層。
						mx, my := int(d.Mouse.X), int(d.Mouse.Y)
						clean := bytes.Clone(indexed)
						box := cursorBox(mx, my).Intersect(layer.safe)
						for y := box.Min.Y; y < box.Max.Y; y++ {
							for x := box.Min.X; x < box.Max.X; x++ {
								clean[y*320+x] = canvas()[y*320+x]
							}
						}
						frame, composed, why, err := overlay.Compose(clean, m.DAC[:], 320, 200, 4,
							layer.patch, layer.shadow, layer.safe.Min.Mul(4), 0, enabled)
						must(err)
						reason = why
						if composed {
							out := image.Rectangle{Min: layer.safe.Min.Mul(4), Max: layer.safe.Max.Mul(4)}
							draw.Draw(output, out, frame, out.Min, draw.Src)
							for _, index := range []byte{68, 149} {
								p := int(index) * 3
								fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
								draw.DrawMask(output, out, image.NewUniform(fg), image.Point{}, layer.fg[index], image.Point{}, draw.Over)
							}
							for y := box.Min.Y; y < box.Max.Y; y++ {
								for x := box.Min.X; x < box.Max.X; x++ {
									if v := indexed[y*320+x]; v != clean[y*320+x] {
										p := int(v) * 3
										c := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
										draw.Draw(output, image.Rect(x*4, y*4, x*4+4, y*4+4), image.NewUniform(c), image.Point{}, draw.Src)
									}
								}
							}
							ok, reason = true, "applied"
						}
					}
					lineRecords = append(lineRecords, map[string]any{"candidate_id": layer.name, "applied": ok, "reason": reason, "rows": len(layer.rows)})
				}
			}
			for _, caption := range captions {
				captionReason := caption.phase
				captionApplied := false
				if caption.ink == nil {
					captionReason = caption.fontReason
				} else if caption.phase == "active" && caption.patch != nil &&
					hash(indexed) == caption.afterSHA && !applied {
					if captionCursorBlocked(caption) {
						captionReason = "cursor-or-button-over-caption"
					} else {
						frame, ok, why, err := overlay.Compose(indexed, m.DAC[:], 320, 200, 4,
							caption.patch, caption.ink, caption.fgPos.Add(image.Pt(4, 4)), 47, enabled)
						must(err)
						captionReason = why
						if ok {
							safe := image.Rectangle{Min: caption.safe.Min.Mul(4), Max: caption.safe.Max.Mul(4)}
							draw.Draw(output, safe, frame, safe.Min, draw.Src)
							p := 14 * 3
							fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
							r := image.Rectangle{Min: caption.fgPos, Max: caption.fgPos.Add(caption.inkSize)}
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
			retireOther, retireShown := applied, false
			for _, ev := range retire {
				for _, f := range ev.fields {
					reason, ok := f.phase, false
					if f.ink == nil {
						reason = f.fontReason
					} else if f.phase == "active" && f.patch != nil && retireOther {
						// 退休框三欄彼此不重疊可同幀並存；其他覆蓋啟用時保留原文。
						reason = "other-overlay-active"
					} else if f.phase == "active" && f.patch != nil {
						x, y := int(d.Mouse.X), int(d.Mouse.Y)
						inkArea := image.Rect(f.position.X/4, f.position.Y/4, (f.position.X+f.size.X+4+3)/4, (f.position.Y+f.size.Y+4+3)/4)
						if d.Mouse.Buttons != 0 || image.Rect(x, y, x+16, y+16).Overlaps(inkArea) {
							reason = "cursor-or-button-over-field"
						} else if !bytes.Equal(rectBytes(indexed, f.rect), f.afterSafe) {
							reason = "vga-safe-mismatch"
						} else {
							frame, composed, why, err := overlay.Compose(indexed, m.DAC[:], 320, 200, 4,
								f.patch, f.ink, f.position.Add(image.Pt(4, 4)), 47, enabled)
							must(err)
							reason = why
							if composed {
								safe := image.Rect(f.rect.Min.X*4, f.rect.Min.Y*4, f.rect.Max.X*4, f.rect.Max.Y*4)
								draw.Draw(output, safe, frame, safe.Min, draw.Src)
								p := 68 * 3
								fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
								draw.DrawMask(output, image.Rectangle{Min: f.position, Max: f.position.Add(f.ink.Bounds().Size())},
									image.NewUniform(fg), image.Point{}, f.ink, f.ink.Bounds().Min, draw.Over)
								ok, retireShown = true, true
								f.appliedFrames++
							}
						}
					}
					lineRecords = append(lineRecords, map[string]any{"candidate_id": f.id, "applied": ok, "reason": reason, "accepted_events": f.accepted})
				}
			}
			if retireShown {
				applied, reason = true, "applied"
			}
			if intro != nil {
				for _, pg := range intro.pages {
					reason, ok := "idle", false
					if pg.normal == nil {
						reason = pg.fontReason
					} else if intro.page != pg {
						reason = intro.phase
						if intro.phase == "active" || intro.phase == "waiting-screen" {
							reason = "other-page"
						}
					} else if intro.phase != "active" || intro.patch == nil {
						reason = intro.phase
					} else if applied {
						reason = "other-overlay-active"
					} else if d.Mouse.Buttons != 0 {
						reason = "mouse-button-held"
					} else {
						// 把游標範圍換回印後底層再合成中文，最後把真 VGA 的游標像素畫回最上層。
						mx, my := int(d.Mouse.X), int(d.Mouse.Y)
						clean := bytes.Clone(indexed)
						box := cursorBox(mx, my).Intersect(introPanel)
						for y := box.Min.Y; y < box.Max.Y; y++ {
							for x := box.Min.X; x < box.Max.X; x++ {
								i := (y-introPanel.Min.Y)*introPanel.Dx() + x - introPanel.Min.X
								clean[y*320+x] = intro.afterSafe[i]
							}
						}
						if !bytes.Equal(introPanelBytes(clean), intro.afterSafe) {
							reason = "vga-safe-mismatch"
						} else {
							frame, composed, why, err := overlay.Compose(clean, m.DAC[:], 320, 200, 4,
								intro.patch, pg.shadow, image.Pt(32, 32), 47, enabled)
							must(err)
							reason = why
							if composed {
								panel := image.Rect(32, 32, 1248, 768)
								draw.Draw(output, panel, frame, panel.Min, draw.Src)
								for _, layer := range []struct {
									mask  *image.Alpha
									index int
								}{{pg.normal, 68}, {pg.accent, 149}} {
									p := layer.index * 3
									fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
									draw.DrawMask(output, panel, image.NewUniform(fg), image.Point{}, layer.mask, image.Point{}, draw.Over)
								}
								for y := box.Min.Y; y < box.Max.Y; y++ {
									for x := box.Min.X; x < box.Max.X; x++ {
										if v := indexed[y*320+x]; v != clean[y*320+x] {
											p := int(v) * 3
											c := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
											draw.Draw(output, image.Rect(x*4, y*4, x*4+4, y*4+4), image.NewUniform(c), image.Point{}, draw.Src)
										}
									}
								}
								ok, applied = true, true
								reason = "applied"
								pg.appliedFrame++
							}
						}
					}
					lineRecords = append(lineRecords, map[string]any{"candidate_id": pg.id, "applied": ok, "reason": reason, "accepted_events": pg.accepted})
				}
			}
			if help != nil {
				hreason, ok := help.phase, false
				if help.normal == nil {
					hreason = help.fontReason
				} else if help.phase != "active" || help.patch == nil {
					hreason = help.phase
				} else if applied {
					hreason = "other-overlay-active"
				} else if d.Mouse.Buttons != 0 {
					hreason = "mouse-button-held"
				} else {
					// 同介紹頁：游標範圍換回印後底層再合成中文，最後把真 VGA 的游標像素畫回最上層。
					mx, my := int(d.Mouse.X), int(d.Mouse.Y)
					clean := bytes.Clone(indexed)
					box := cursorBox(mx, my).Intersect(helpText)
					for y := box.Min.Y; y < box.Max.Y; y++ {
						for x := box.Min.X; x < box.Max.X; x++ {
							clean[y*320+x] = help.afterSafe[(y-helpText.Min.Y)*helpText.Dx()+x-helpText.Min.X]
						}
					}
					if !bytes.Equal(helpTextBytes(clean), help.afterSafe) {
						hreason = "vga-safe-mismatch"
					} else {
						origin := helpText.Min.Mul(4)
						frame, composed, why, err := overlay.Compose(clean, m.DAC[:], 320, 200, 4,
							help.patch, help.shadow, origin, 47, enabled)
						must(err)
						hreason = why
						if composed {
							panel := image.Rectangle{Min: origin, Max: helpText.Max.Mul(4)}
							draw.Draw(output, panel, frame, panel.Min, draw.Src)
							for _, layer := range []struct {
								mask  *image.Alpha
								index int
							}{{help.normal, 68}, {help.accent, 149}} {
								p := layer.index * 3
								fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
								draw.DrawMask(output, panel, image.NewUniform(fg), image.Point{}, layer.mask, image.Point{}, draw.Over)
							}
							for y := box.Min.Y; y < box.Max.Y; y++ {
								for x := box.Min.X; x < box.Max.X; x++ {
									if v := indexed[y*320+x]; v != clean[y*320+x] {
										p := int(v) * 3
										c := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
										draw.Draw(output, image.Rect(x*4, y*4, x*4+4, y*4+4), image.NewUniform(c), image.Point{}, draw.Src)
									}
								}
							}
							ok, applied = true, true
							hreason, reason = "applied", "applied"
							help.appliedFrames++
						}
					}
				}
				lineRecords = append(lineRecords, map[string]any{"candidate_id": help.id, "applied": ok, "reason": hreason, "accepted_events": help.accepted})
			}
			optionsTitleShown := false
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
							optionsTitleShown = true
							title.appliedFrames++
							reason = "applied"
						}
					}
				} else if title.phase == "active" && applied {
					titleReason = "other-overlay-active"
				}
				lineRecords = append(lineRecords, map[string]any{"candidate_id": title.id, "applied": titleApplied, "reason": titleReason, "accepted_events": title.accepted})
			}
			if rows != nil {
				// 標題與八列安全矩形互不重疊，可同幀並存；其他覆蓋啟用時八列保留原文。
				otherActive := applied && !optionsTitleShown
				rowApplied := false
				for i, r := range rows.rows {
					reason, ok := r.phase, false
					if r.ink == nil {
						reason = r.fontReason
					} else if r.phase == "active" && r.patch != nil && otherActive {
						reason = "other-overlay-active"
					} else if r.phase == "active" && r.patch != nil {
						x, y := int(d.Mouse.X), int(d.Mouse.Y)
						// 守住中譯前景與陰影在原版座標的覆蓋範圍（四倍座標向外取整）。
						inkArea := image.Rect(82, 61+12*i, (328+optionRowInk[i].X+4+3)/4, (244+48*i+optionRowInk[i].Y+4+3)/4)
						if d.Mouse.Buttons != 0 || image.Rect(x, y, x+16, y+16).Overlaps(inkArea) {
							reason = "cursor-or-button-over-row"
						} else if !bytes.Equal(optionRowSafeBytes(indexed, i), r.afterSafe) {
							reason = "vga-safe-mismatch"
						} else {
							frame, composed, why, err := overlay.Compose(indexed, m.DAC[:], 320, 200, 4,
								r.patch, r.ink, image.Pt(332, 248+48*i), 47, enabled)
							must(err)
							reason = why
							if composed {
								safe := image.Rect(320, 236+48*i, 1008, 284+48*i)
								draw.Draw(output, safe, frame, safe.Min, draw.Src)
								p := 68 * 3
								fg := color.RGBA{m.DAC[p]<<2 | m.DAC[p]>>4, m.DAC[p+1]<<2 | m.DAC[p+1]>>4, m.DAC[p+2]<<2 | m.DAC[p+2]>>4, 255}
								at := image.Pt(328, 244+48*i)
								draw.DrawMask(output, image.Rectangle{Min: at, Max: at.Add(r.ink.Bounds().Size())},
									image.NewUniform(fg), image.Point{}, r.ink, r.ink.Bounds().Min, draw.Over)
								ok, rowApplied = true, true
								r.appliedFrames++
							}
						}
					}
					lineRecords = append(lineRecords, map[string]any{"candidate_id": r.id, "applied": ok, "reason": reason, "accepted_events": r.accepted})
				}
				if rowApplied {
					applied = true
					reason = "applied"
				}
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
		if strings.HasPrefix(label, "cp-") {
			rec["memory_sha256"] = hash(m.Mem)
		}
		rec["raw_sha256"] = hash(indexed)
		rec["palette_sha256"] = hash(m.DAC[:])
		rec["png"] = prefix + ".png"
		checkpoints = append(checkpoints, rec)
	}
	var pendingCheckpoints []uint64
	for _, f := range strings.Split(*checkpointSteps, ",") {
		if f == "" {
			continue
		}
		v, e := strconv.ParseUint(f, 10, 64)
		if e != nil || (len(pendingCheckpoints) > 0 && v <= pendingCheckpoints[len(pendingCheckpoints)-1]) {
			panic("檢查點步數須為遞增整數")
		}
		pendingCheckpoints = append(pendingCheckpoints, v)
	}
	m.SetOnFrame(func() {
		render("")
		if len(pendingCheckpoints) > 0 && m.Steps >= pendingCheckpoints[0] {
			render(fmt.Sprintf("cp-%d", pendingCheckpoints[0]))
			pendingCheckpoints = pendingCheckpoints[1:]
		}
	})
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
	report := map[string]any{"state": state, "checkpoints": checkpoints, "frames": frames, "events": events, "drops": drops, "input_hashes": inputs, "catalog_sha256": hash(catalogBytes), "translation_sha256": hash([]byte(lines[0].translation)), "font_sha256": fontHash, "control": *control, "missing": *missing, "all_menu": *allMenu, "step_convention": "before-instruction-number = legacy-pre-Step + 1", "opened": d.Opened}
	if sea != nil {
		report["sea_misses"] = seaMisses(sea)
	}
	dumpJSON(*out+".json", report)
	fmt.Printf("完成 %d 事件、%d 幀、%d 截圖，原版狀態 %s\n", len(events), len(frames), len(checkpoints), hash(m.Mem))
}
