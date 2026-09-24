// 目標098只讀探針：正常玩家姓名 Enter 後，追首次國家介紹的來源與畫布。
// 所有原版像素、RAM 線索與完整印字序列只寫入已忽略的 workplace。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"

	golem "github.com/wicanr2/dosgolem"
)

type introInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X, Y   int
	Button int
}
type introReplay struct {
	Inputs []introInput `json:"inputs"`
	End    uint64       `json:"end"`
}
type introSource struct {
	Name   string `json:"name"`
	Offset int64  `json:"offset"`
	Bytes  string `json:"bytes"`
}
type introWriter struct {
	Count     int               `json:"count"`
	BBox      [4]int            `json:"bbox"`
	FirstStep uint64            `json:"first_step"`
	LastStep  uint64            `json:"last_step"`
	Rows      map[int]*introRow `json:"rows"`
}
type introRow struct {
	Count int `json:"count"`
	MinX  int `json:"min_x"`
	MaxX  int `json:"max_x"`
}

func mustIntro(err error) {
	if err != nil {
		panic(err)
	}
}
func readIntro(path string) []byte {
	b, err := os.ReadFile(path)
	mustIntro(err)
	return b
}
func hashIntro(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀目錄")
	inputs := flag.String("inputs", "", "已驗十六筆正常玩家輸入")
	out := flag.String("out", "", "已忽略 workplace 輸出前綴")
	control := flag.Bool("control", false, "不安裝記憶體讀寫觀測器")
	nextEnter := flag.Bool("next-enter", false, "65M步再按 Enter 觀察下一頁")
	nation := flag.String("nation", "france", "目標101：england/france/spain/netherlands，實際點選四張旗卡")
	afterB := flag.String("after-b", "none", "目標101：B頁後 none/wait/enter/esc")
	afterFollow := flag.String("after-follow", "none", "目標105：85M後續頁後 none/wait/enter/esc")
	followUntil := flag.Uint64("follow-until", 100000000, "後續觀測終點；一般上限150M，字幕後稽核上限1500M")
	followEnterAt := flag.String("follow-enter-at", "", "目標105：額外 Enter 的百萬步數，以逗號分隔，例如100,115")
	preprint := flag.Bool("preprint", false, "在 A/B 與啟用後續頁時的首筆 0D21:012C 寫入前擷取原始畫布")
	postCaptionAudit := flag.Bool("post-caption-audit", false, "目標107：選用鍵盤待取數診斷與有界字幕後觀測")
	captionFrameAudit := flag.Bool("caption-frame-audit", false, "目標129：首張字幕的當次印字、畫布與逐幀失效觀測；預設關閉")
	captionScreenAudit := flag.Bool("caption-screen-audit", false, "目標130：在已驗字幕畫格逐幀比較實際 VGA 索引與原版底層畫布；預設關閉")
	gameInputsPath := flag.String("game-inputs", "", "目標110：字幕後正常玩家滑鼠／鍵盤事件 JSON；預設不改舊重播")
	optionsAudit := flag.Bool("options-audit", false, "目標112：固定 GAME.TXT 遊戲選項九欄的 DOS 讀入來源")
	optionsPreprint := flag.Bool("options-preprint", false, "目標113：九欄各自首筆原版印字前底圖與印字緩衝寫入")
	optionsWriterAudit := flag.Bool("options-writer-audit", false, "目標114：原版印字緩衝寫入者附近的讀取與暫存器")
	retireAudit := flag.Bool("retire-audit", false, "目標126：只追退休確認框三段固定來源；預設關閉")
	retireFlowAudit := flag.Bool("retire-flow-audit", false, "目標127：只追退休框 DOS 讀入至印字緩衝的近端讀寫；預設關閉")
	retireResidentAudit := flag.Bool("retire-resident-audit", false, "目標127：與近端監看互斥，追退休框高位址常駐字串寫入；預設關閉")
	optionsResidentAudit := flag.Bool("options-resident-audit", false, "目標114：互斥觀測九欄高位址 RAM 來源的寫入者")
	optionsPhaseSamples := flag.String("options-phase-samples", "", "目標119：選項點擊附近額外取樣的遞增絕對指令步數，逗號分隔；預設關閉")
	optionsTitleScreenAudit := flag.String("options-title-screen-audit", "", "目標131：固定1,300M原版畫布檔路徑；逐幀核對選項標題的底層與真 VGA")
	allowEarlyExit := flag.Bool("allow-early-exit", false, "目標123：只在後續正常玩家路徑觀測 DOS 提前結束，保留真實終止步數；預設關閉")
	scratch := flag.String("scratch", "", "目標125：原版唯讀 Root 外的跨次 DOS 暫存層；預設關閉")
	flag.Parse()
	if *inputs == "" || *out == "" {
		panic("缺必要參數")
	}
	if *afterB != "none" && *afterB != "wait" && *afterB != "enter" && *afterB != "esc" {
		panic("未知 B 頁後輸入")
	}
	if *afterB != "none" && !*nextEnter {
		panic("必須先實際進入 B 頁")
	}
	if *afterFollow != "none" && *afterFollow != "wait" && *afterFollow != "enter" && *afterFollow != "esc" {
		panic("未知後續頁輸入")
	}
	if *afterFollow != "none" && *afterB != "enter" && *afterB != "esc" {
		panic("必須先實際離開 B 頁")
	}
	if *afterFollow == "none" && (*followUntil != 100000000 || *followEnterAt != "") {
		panic("延伸觀測必須先啟用後續頁輸入")
	}
	if *postCaptionAudit && (*afterFollow != "enter" && *afterFollow != "esc" ||
		!*nextEnter || *preprint) {
		panic("字幕後稽核需正常 B 頁後路徑，且不與印前擷取混用")
	}
	if *captionFrameAudit && (!*postCaptionAudit || *nation != "england" ||
		*afterB != "enter" || *afterFollow != "enter" || *followUntil < 210000000 ||
		*gameInputsPath != "" || *followEnterAt != "") {
		panic("字幕逐幀觀測只接受固定英格蘭 Enter 路徑至至少210M，無額外輸入")
	}
	if *captionScreenAudit && !*captionFrameAudit {
		panic("字幕顯示畫面逐幀觀測須啟用字幕生命週期觀測")
	}
	maxFollow := uint64(150000000)
	if *postCaptionAudit {
		maxFollow = 1500000000
		if *scratch != "" && *allowEarlyExit {
			maxFollow = 1700000000
		}
	}
	if *afterFollow != "none" && (*followUntil < 100000000 || *followUntil > maxFollow || *followUntil%5000000 != 0) {
		panic("後續觀測終點超出限定範圍")
	}
	if *postCaptionAudit && *followUntil > 500000000 && *followUntil%25000000 != 0 {
		panic("500M 後只在25M檢查點停止")
	}
	if *gameInputsPath != "" && (!*postCaptionAudit || *followUntil <= 1225000000) {
		panic("字幕後玩家事件須沿已驗海上畫面並保留鍵盤稽核")
	}
	if *allowEarlyExit && (*gameInputsPath == "" || *followUntil < 1300000000 || *optionsAudit) {
		panic("提前終止收據只接受既有海上玩家事件且不可混用選項來源稽核")
	}
	if *scratch != "" {
		if !*postCaptionAudit || *gameInputsPath == "" {
			panic("可寫暫存層僅供字幕後正常玩家輸入實驗")
		}
		st, err := os.Stat(*scratch)
		mustIntro(err)
		owner, ok := st.Sys().(*syscall.Stat_t)
		if !st.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
			panic("可寫暫存層不存在或擁有者不符")
		}
		rootAbs, err := filepath.EvalSymlinks(*root)
		mustIntro(err)
		scratchAbs, err := filepath.EvalSymlinks(*scratch)
		mustIntro(err)
		if rootAbs == scratchAbs {
			panic("可寫暫存層不得等於原版 Root")
		}
	}
	if *optionsAudit && (*gameInputsPath == "" || *followUntil < 1300000000) {
		panic("遊戲選項來源稽核需要正常玩家開窗輸入與1300M終點")
	}
	if *retireAudit && (*gameInputsPath == "" || !*postCaptionAudit || *followUntil < 1275000000) {
		panic("退休來源稽核需要已驗玩家輸入及確認框終點")
	}
	if *retireFlowAudit && !*retireAudit {
		panic("退休資料流稽核須同時啟用退休來源稽核")
	}
	if *retireResidentAudit && (!*retireAudit || *retireFlowAudit || *optionsResidentAudit) {
		panic("退休高位址稽核需單獨啟用，且須同時啟用退休來源稽核")
	}
	if *optionsPreprint && !*optionsAudit {
		panic("遊戲選項印前底圖需同時啟用來源稽核")
	}
	if *optionsTitleScreenAudit != "" && (!*optionsPreprint || *captionFrameAudit || *followUntil < 1375000000) {
		panic("選項標題逐幀審計需九欄印前證據、至少1375M終點，且不可與字幕逐幀審計混用")
	}
	if *optionsWriterAudit && !*optionsPreprint {
		panic("印字緩衝來源稽核需同時啟用逐欄印前底圖")
	}
	if *optionsResidentAudit && (!*optionsAudit || *optionsPreprint || *optionsWriterAudit) {
		panic("高位址 RAM 來源稽核需單獨啟用，不能與畫布寫入監看並用")
	}
	phaseSteps := []uint64{}
	if *optionsPhaseSamples != "" {
		if !*optionsAudit || *followUntil < 1350000000 {
			panic("選項相位取樣需要正常玩家選項稽核與至少1350M終點")
		}
		for _, token := range strings.Split(*optionsPhaseSamples, ",") {
			step, err := strconv.ParseUint(token, 10, 64)
			mustIntro(err)
			if step <= 1300000000 || step >= 1325000000 || step%25000000 == 0 ||
				(len(phaseSteps) > 0 && step <= phaseSteps[len(phaseSteps)-1]) || len(phaseSteps) >= 24 {
				panic("選項額外取樣須在1300M–1325M內遞增，最多24個且不可覆蓋標準檢查點")
			}
			phaseSteps = append(phaseSteps, step)
		}
	}
	extraEnters := map[uint64]bool{}
	if *followEnterAt != "" {
		previous := uint64(0)
		for _, token := range strings.Split(*followEnterAt, ",") {
			million, err := strconv.ParseUint(token, 10, 64)
			mustIntro(err)
			if million > maxFollow/1000000 {
				panic("額外 Enter 步數超出限定範圍")
			}
			step := million * 1000000
			if step < 100000000 || step >= *followUntil || step%5000000 != 0 ||
				(*postCaptionAudit && step > 500000000 && step%25000000 != 0) || step <= previous {
				panic("額外 Enter 步數不是遞增的有效檢查點")
			}
			extraEnters[step] = true
			previous = step
		}
	}
	lateInputs := []introInput{}
	lateInputHash := ""
	lateInputUsesSpace := false
	if *gameInputsPath != "" {
		inputBytes := readIntro(*gameInputsPath)
		lateInputHash = hashIntro(inputBytes)
		mustIntro(json.Unmarshal(inputBytes, &lateInputs))
		maxInputs := 12
		if *scratch != "" {
			maxInputs = 30
		}
		if len(lateInputs) == 0 || len(lateInputs) > maxInputs {
			panic("字幕後玩家事件數量不符")
		}
		previous := uint64(1225000000)
		for _, e := range lateInputs {
			if e.Step <= previous || e.Step >= *followUntil || e.Step%1000000 != 0 ||
				e.Step%25000000 == 0 {
				panic("字幕後玩家事件必須位於遞增的百萬步檢查點之間")
			}
			if e.Kind != "move" && e.Kind != "press" && e.Kind != "release" &&
				e.Kind != "enter" && e.Kind != "esc" && e.Kind != "left" && e.Kind != "right" && e.Kind != "space" {
				panic("未知字幕後玩家事件")
			}
			if e.Kind == "space" {
				lateInputUsesSpace = true
			}
			if e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200 || e.Button != 0 {
				panic("字幕後滑鼠座標或按鍵不符")
			}
			previous = e.Step
		}
		for _, step := range phaseSteps {
			for _, e := range lateInputs {
				if step == e.Step {
					panic("選項額外取樣不得與玩家事件同一步")
				}
			}
		}
	}
	parent, err := os.Stat(filepath.Dir(*out))
	mustIntro(err)
	owner, ok := parent.Sys().(*syscall.Stat_t)
	if !parent.IsDir() || !ok || int(owner.Uid) != os.Getuid() {
		panic("輸出目錄擁有者不符")
	}
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NATIONS.PIK": "bd31e62d7b7652e6903aaea76b1641f11d5333ff6a6da13fd26411c9f080bf54",
	}
	if *gameInputsPath != "" {
		wants["MENU.TXT"] = "5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702"
	}
	for name, want := range wants {
		if hashIntro(readIntro(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	game := readIntro(filepath.Join(*root, "GAME.TXT"))
	captionExpected := game[0x153ce:0x1540b]
	type nationRoute struct {
		first, second, end int64
		marker, title      string
		x, y               int
	}
	routes := map[string]nationRoute{
		"england":     {0xAE7C, 0xB204, 0xB2DB, "NATION0", "ENGLAND", 155, 50},
		"france":      {0xB2DB, 0xB641, 0xB73E, "NATION1", "FRANCE", 255, 50},
		"spain":       {0xB73E, 0xBB46, 0xBC28, "NATION2", "SPAIN", 155, 150},
		"netherlands": {0xBC28, 0xC032, 0xC191, "NATION3", "NETHERLANDS", 255, 150},
	}
	route, ok := routes[*nation]
	if !ok {
		panic("未知國家選項")
	}
	first := game[route.first:route.second]
	second := game[route.second:route.end]
	firstMarker, secondMarker := "@"+route.marker+"A", "@"+route.marker+"B"
	title := "^^" + route.title
	firstTitle := bytes.Index(first, []byte(title))
	secondTitle := bytes.Index(second, []byte(title))
	firstBody := bytes.Index(first, []byte("__"))
	if firstTitle < 0 || secondTitle < 0 || firstBody < 0 {
		panic("國家節控制標記不符")
	}
	firstBody += 2
	sources := []introSource{{"GAME.TXT", route.first, firstMarker},
		{"GAME.TXT", route.first + int64(firstTitle), title},
		{"GAME.TXT", route.first + int64(firstBody), string(first[firstBody : firstBody+10])},
		{"GAME.TXT", route.second, secondMarker},
		{"GAME.TXT", route.second + int64(secondTitle), title}}
	if *afterFollow != "none" {
		// 字幕跨 512-byte DOS 讀取邊界；分兩段保留兩次讀檔目的位址。
		caption := "In the Year of Our Lord One Thousand Four Hundred Ninety-Two,"
		boundary := 0x15400 - 0x153ce
		sources = append(sources,
			introSource{"GAME.TXT", 0x1316a, "@TUTORIAL1"},
			introSource{"GAME.TXT", 0x13190, "Our {%STRING0}"},
			introSource{"GAME.TXT", 0x153b0, "@BUILD1"},
			introSource{"GAME.TXT", 0x153ce, caption[:boundary]},
			introSource{"GAME.TXT", 0x15400, caption[boundary:]})
		if *postCaptionAudit {
			// 目標107只記固定原版標記的 DOS 預讀；是否印字仍由讀字事件判定。
			for _, marker := range []struct {
				offset int64
				text   string
			}{{0x1540f, "@BUILD2"}, {0x15466, "@BUILD3"},
				{0x154af, "@BUILD4"}, {0x15506, "@BUILD5"},
				{0x15541, "@BUILD6"}, {0x1557b, "@BUILD7"},
				{0x155d9, "@BUILD8"}, {0x15623, "@BUILD9"},
				{0x15678, "@BUILD10"}} {
				sources = append(sources, introSource{"GAME.TXT", marker.offset, marker.text})
			}
		}
	}
	if *optionsAudit {
		// 只追原版視窗中實際可見的九段；位移與原始 bytes 雙重守門。
		sources = append(sources,
			introSource{"GAME.TXT", 0x4cd, "Set Game Options"},
			introSource{"GAME.TXT", 0x4e9, "Show ~Indian Moves"},
			introSource{"GAME.TXT", 0x4fd, "Show ~Foreign Moves"},
			introSource{"GAME.TXT", 0x512, "Fast Piece ~Slide"},
			introSource{"GAME.TXT", 0x525, "~End of Turn"},
			introSource{"GAME.TXT", 0x533, "~Autosave"},
			introSource{"GAME.TXT", 0x53e, "~Combat Analysis"},
			introSource{"GAME.TXT", 0x550, "Water Color C~ycling"},
			introSource{"GAME.TXT", 0x566, "~Tutorial Hints"})
	}
	if *retireAudit {
		sources = append(sources,
			introSource{"GAME.TXT", 0x122, "Do you really want to quit?"},
			introSource{"GAME.TXT", 0x141, "Yes"},
			introSource{"GAME.TXT", 0x146, "No"})
	}
	for _, source := range sources {
		end := source.Offset + int64(len(source.Bytes))
		if end > int64(len(game)) || !bytes.Equal(game[source.Offset:end], []byte(source.Bytes)) {
			panic("候選位元組不符：" + source.Bytes)
		}
	}
	inputData := readIntro(*inputs)
	if hashIntro(inputData) != "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e" {
		panic("正常玩家輸入版本不符")
	}
	var replay introReplay
	mustIntro(json.Unmarshal(inputData, &replay))
	if len(replay.Inputs) != 16 || replay.End != 100000000 {
		panic("正常玩家輸入結構不符")
	}
	m := golem.New()
	mustIntro(m.LoadEXE(readIntro(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	if *scratch != "" {
		d.Scratch = *scratch
	}
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	const canvas uint32 = 0x2cae0
	printReads := []map[string]any{}
	retireBefore := map[string][]byte{}
	retireFirstSteps := map[string]uint64{}
	retireFlowReads := []map[string]any{}
	retireFlowWrites := []map[string]any{}
	retireResidentWrites := []map[string]any{}
	optionSourceReads := []map[string]any{}
	optionPrintWrites := []map[string]any{}
	optionWriterReads := []map[string]any{}
	optionIntermediateWrites := []map[string]any{}
	optionResidentWrites := []map[string]any{}
	optionBefore := map[int][]byte{}
	optionFirstSteps := map[int]uint64{}
	optionWriteCounts := map[int]int{}
	captionReadStage := 0
	captionReadStart := uint64(0)
	captionReadEnd := uint64(0)
	captionFirstReadCanvasSHA := ""
	captionReadOperands := []map[string]any{}
	captionReadMismatch := 0
	captionWriteCount := 0
	captionWriteFirst := uint64(0)
	captionWriteLast := uint64(0)
	captionFirstWriteCanvasSHA := ""
	captionWriteBBox := [4]int{320, 200, 0, 0}
	captionFrames := 0
	captionSignatureFrames := 0
	captionEligibleFrames := 0
	captionIndexedMismatchFrames := 0
	captionSafeMismatchFrames := 0
	captionFirstSafeMismatchStep := uint64(0)
	captionLastSafeMismatchStep := uint64(0)
	captionPhase := "unseen"
	captionTransitions := []map[string]any{}
	captionSignatureFirst := uint64(0)
	captionSignatureLast := uint64(0)
	optionSafe := [9][4]int{{65, 44, 253, 59}, {80, 59, 252, 71},
		{80, 71, 252, 83}, {80, 83, 252, 95}, {80, 95, 252, 107},
		{80, 107, 252, 119}, {80, 119, 252, 131}, {80, 131, 252, 143},
		{80, 143, 252, 155}}
	var titleReference []byte
	if *optionsTitleScreenAudit != "" {
		titleReference = readIntro(*optionsTitleScreenAudit)
		if len(titleReference) != 64000 || hashIntro(titleReference) != "c1a32b289c17f6db4a65983fa4dd9ed04fa7024cfbc82a709c7ee87732c0a23b" {
			panic("選項標題原版1,300M底層畫布不符")
		}
	}
	titleFrames, titleCanvasMatch, titleVGAMatch := 0, 0, 0
	titleFirstCanvas, titleFirstVGA, titleLastVGA := uint64(0), uint64(0), uint64(0)
	titlePhase := "unseen"
	titleTransitions := []map[string]any{}
	writers := map[string]*introWriter{}
	preprintCanvas := map[string][]byte{}
	preprintSteps := map[string]uint64{}
	observeEnd := uint64(75000000)
	if *afterB != "none" {
		observeEnd = 85000000
	}
	if *afterFollow != "none" {
		observeEnd = *followUntil
	}
	if !*control {
		m.WatchReads(0x20000, 0x80000, func(a uint32, value uint8) {
			if *captionFrameAudit && m.Steps >= 88600000 && m.Steps < 88900000 &&
				captionReadEnd == 0 {
				cs, ip := m.CPU.OpAddr()
				if cs == 0x0d21 && ip == 0x00c6 && (a == 0x2a560 || a == 0x2a561) {
					wantedAddr := uint32(0x2a560)
					wantedValue := captionExpected[captionReadStage/2]
					if captionReadStage%2 == 1 {
						wantedAddr, wantedValue = 0x2a561, 0
					}
					if a == wantedAddr && value == wantedValue {
						if captionReadStage == 0 {
							captionReadStart = m.Steps
							if *captionScreenAudit {
								captionFirstReadCanvasSHA = hashIntro(m.Mem[canvas : canvas+64000])
							}
						}
						if *captionScreenAudit && len(captionReadOperands) < len(captionExpected)*2 {
							c := m.CPU
							captionReadOperands = append(captionReadOperands, map[string]any{
								"step": m.Steps, "linear": a, "value": value,
								"ss": c.Seg[golem.SS], "bx": c.R[golem.BX],
								"ds": c.Seg[golem.DS], "si": c.R[golem.SI],
								"di":           c.R[golem.DI],
								"ss_bx_linear": uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.BX]),
							})
						}
						captionReadStage++
						if captionReadStage == len(captionExpected)*2 {
							captionReadEnd = m.Steps
						}
					} else {
						captionReadMismatch++
						captionReadStage = 0
						if a == 0x2a560 && value == captionExpected[0] {
							captionReadStart, captionReadStage = m.Steps, 1
						}
					}
				}
			}
			if *retireFlowAudit && m.Steps >= 1253240000 && m.Steps < 1253355000 &&
				((a >= 0x2ac00 && a < 0x2b180) || (a >= 0x74000 && a < 0x74600)) &&
				len(retireFlowReads) < 50000 {
				cs, ip := m.CPU.OpAddr()
				if cs == 0x0e2d || (cs == 0x8bdf && ip >= 0x0500 && ip < 0x0600) ||
					(cs == 0x0d21 && ip == 0x00c6) {
					retireFlowReads = append(retireFlowReads, map[string]any{
						"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
						"linear": a, "value": value})
				}
			}
			if *retireAudit && m.Steps >= 1253300000 && m.Steps < 1254000000 {
				cs, ip := m.CPU.OpAddr()
				if cs == 0x0d21 && ip == 0x00c6 {
					name := ""
					switch {
					case a == 175232 && value == 'D':
						name = "question"
					case a == 175590 && value == 'Y':
						name = "yes"
					case a == 175590 && value == 'N':
						name = "no"
					}
					if name != "" && retireBefore[name] == nil {
						retireBefore[name] = bytes.Clone(m.Mem[canvas : canvas+64000])
						retireFirstSteps[name] = m.Steps
					}
				}
			}
			if *optionsWriterAudit && m.Steps >= 1253400000 && m.Steps < 1253600000 &&
				len(optionWriterReads) < 30000 {
				cs, ip := m.CPU.OpAddr()
				if cs == 0x0e2d || (cs == 0x8bdf && ip >= 0x0500 && ip <= 0x0600) {
					optionWriterReads = append(optionWriterReads, map[string]any{
						"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
						"linear": a, "value": value})
				}
			}
			if *optionsAudit && m.Steps >= 1253314011 && m.Steps < 1253600000 &&
				a >= 0x2b0cf && a < 0x2b177 && len(optionSourceReads) < 10000 {
				cs, ip := m.CPU.OpAddr()
				optionSourceReads = append(optionSourceReads, map[string]any{
					"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
					"linear": a, "value": value})
			}
			if m.Steps < 55000000 || m.Steps >= observeEnd || len(printReads) >= 30000 {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if (cs == 0x0d21 && ip == 0x00c6) || (cs == 0x0d3a && ip == 0x0015) {
				printReads = append(printReads, map[string]any{"step": m.Steps,
					"cs_ip": fmt.Sprintf("%04X:%04X", cs, ip), "linear": a, "value": value})
			}
		})
		// Machine.WatchWrites 只有一組 active range；分次註冊會覆蓋前一組。
		// 同一個監看範圍先分流兩處字元緩衝，再沿用原有畫布事件。
		writeLo := canvas
		if *optionsPreprint {
			writeLo = 0x2ac78
		}
		if *retireFlowAudit {
			writeLo = 0x2ac00
		}
		m.WatchWrites(writeLo, canvas+64000, func(a uint32, old, value uint8) {
			if a < canvas {
				if *retireFlowAudit && m.Steps >= 1253240000 && m.Steps < 1253355000 &&
					a < 0x2b180 && len(retireFlowWrites) < 50000 {
					cs, ip := m.CPU.OpAddr()
					if cs == 0x0e2d || (cs == 0x8bdf && ip >= 0x0500 && ip < 0x0600) {
						retireFlowWrites = append(retireFlowWrites, map[string]any{
							"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
							"linear": a, "old": old, "value": value})
					}
				}
				if *optionsWriterAudit && m.Steps >= 1253400000 && m.Steps < 1253600000 &&
					((a >= 0x2acea && a < 0x2acec) || (a >= 0x2ad70 && a < 0x2ad81) ||
						(a >= 0x2ae50 && a < 0x2ae52)) && len(optionIntermediateWrites) < 3000 {
					cs, ip := m.CPU.OpAddr()
					optionIntermediateWrites = append(optionIntermediateWrites, map[string]any{
						"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
						"linear": a, "old": old, "value": value})
				}
				if *optionsPreprint && m.Steps >= 1250000000 && m.Steps < 1253600000 &&
					((a >= 0x2ac78 && a < 0x2ac7a) || (a >= 0x2adde && a < 0x2ade0)) &&
					len(optionPrintWrites) < 5000 {
					cs, ip := m.CPU.OpAddr()
					entry := map[string]any{
						"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
						"linear": a, "old": old, "value": value}
					if *optionsWriterAudit {
						entry["registers"] = m.CPU.R
						entry["segments"] = m.CPU.Seg
					}
					optionPrintWrites = append(optionPrintWrites, entry)
				}
				return
			}
			if m.Steps < 55000000 || m.Steps >= observeEnd || old == value {
				return
			}
			cs, ip := m.CPU.OpAddr()
			if *captionFrameAudit && m.Steps >= 88600000 && m.Steps < 88900000 &&
				cs == 0x0d21 && ip == 0x012c {
				if captionWriteCount == 0 {
					captionWriteFirst = m.Steps
					if *captionScreenAudit {
						captionFirstWriteCanvasSHA = hashIntro(m.Mem[canvas : canvas+64000])
					}
				}
				captionWriteCount++
				captionWriteLast = m.Steps
				x, y := int(a-canvas)%320, int(a-canvas)/320
				if x < captionWriteBBox[0] {
					captionWriteBBox[0] = x
				}
				if y < captionWriteBBox[1] {
					captionWriteBBox[1] = y
				}
				if x+1 > captionWriteBBox[2] {
					captionWriteBBox[2] = x + 1
				}
				if y+1 > captionWriteBBox[3] {
					captionWriteBBox[3] = y + 1
				}
			}
			phase := "first"
			if m.Steps >= 85000000 {
				phase = "after-follow"
			} else if m.Steps >= 75000000 {
				phase = "after-b"
			} else if m.Steps >= 65000000 {
				phase = "second"
			}
			if *preprint && (phase == "first" || phase == "second" ||
				(phase == "after-follow" && *afterFollow != "none")) &&
				cs == 0x0d21 && ip == 0x012c && preprintCanvas[phase] == nil {
				// WatchWrites 先於 Mem 寫入回呼；此時仍是真正的首字印前多色底圖。
				preprintCanvas[phase] = bytes.Clone(m.Mem[canvas : canvas+64000])
				preprintSteps[phase] = m.Steps
			}
			key := fmt.Sprintf("%s/%04X:%04X", phase, cs, ip)
			writer := writers[key]
			x, y := int(a-canvas)%320, int(a-canvas)/320
			if *optionsPreprint && m.Steps >= 1253300000 && m.Steps < 1253600000 &&
				cs == 0x0d21 && ip == 0x012c {
				for index, safe := range optionSafe {
					if safe[0] <= x && x < safe[2] && safe[1] <= y && y < safe[3] {
						if optionBefore[index] == nil {
							optionBefore[index] = bytes.Clone(m.Mem[canvas : canvas+64000])
							optionFirstSteps[index] = m.Steps
						}
						optionWriteCounts[index]++
					}
				}
			}
			if writer == nil {
				writer = &introWriter{BBox: [4]int{x, y, x + 1, y + 1},
					FirstStep: m.Steps, Rows: map[int]*introRow{}}
				writers[key] = writer
			}
			writer.Count++
			writer.LastStep = m.Steps
			row := writer.Rows[y]
			if row == nil {
				row = &introRow{MinX: x, MaxX: x}
				writer.Rows[y] = row
			}
			row.Count++
			if x < row.MinX {
				row.MinX = x
			}
			if x > row.MaxX {
				row.MaxX = x
			}
			if x < writer.BBox[0] {
				writer.BBox[0] = x
			}
			if y < writer.BBox[1] {
				writer.BBox[1] = y
			}
			if x+1 > writer.BBox[2] {
				writer.BBox[2] = x + 1
			}
			if y+1 > writer.BBox[3] {
				writer.BBox[3] = y + 1
			}
		})
		if *optionsResidentAudit {
			// 此旗標與逐欄畫布觀測互斥；Machine 只有一組 WatchWrites。
			m.WatchWrites(0x74380, 0x74560, func(a uint32, old, value uint8) {
				if m.Steps < 1250000000 || m.Steps >= 1253600000 || len(optionResidentWrites) >= 5000 {
					return
				}
				cs, ip := m.CPU.OpAddr()
				optionResidentWrites = append(optionResidentWrites, map[string]any{
					"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
					"linear": a, "old": old, "value": value})
			})
		}
		if *retireResidentAudit {
			// Machine 只有一組 active write range；此模式不取得逐欄印前底圖。
			m.WatchWrites(0x74300, 0x74600, func(a uint32, old, value uint8) {
				if m.Steps < 1253240000 || m.Steps >= 1253355000 || len(retireResidentWrites) >= 20000 {
					return
				}
				cs, ip := m.CPU.OpAddr()
				retireResidentWrites = append(retireResidentWrites, map[string]any{
					"step": m.Steps, "cs_ip": fmt.Sprintf("%04X:%04X", cs, ip),
					"linear": a, "old": old, "value": value})
			})
		}
	}
	if *captionFrameAudit {
		const captionCanvasSHA = "b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772"
		const captionPaletteSHA = "92593125369b8224c1f00b30ad0367d6f1766da49afb614dcf753ad8d70b665b"
		m.SetOnFrame(func() {
			if m.Steps < 85000000 || m.Steps > *followUntil {
				return
			}
			captionFrames++
			canvasSHA := hashIntro(m.Mem[canvas : canvas+64000])
			paletteSHA := hashIntro(m.DAC[:])
			signature := m.VideoMode() == 0x13 && canvasSHA == captionCanvasSHA && paletteSHA == captionPaletteSHA
			safeMismatch := false
			if *captionScreenAudit && signature {
				indexed := m.Indexed()
				if !bytes.Equal(indexed, m.Mem[canvas:canvas+64000]) {
					captionIndexedMismatchFrames++
				}
				for y := 27; y < 42; y++ {
					if !bytes.Equal(indexed[y*320+12:y*320+307],
						m.Mem[canvas+uint32(y*320+12):canvas+uint32(y*320+307)]) {
						safeMismatch = true
						break
					}
				}
				if safeMismatch {
					captionSafeMismatchFrames++
					if captionFirstSafeMismatchStep == 0 {
						captionFirstSafeMismatchStep = m.Steps
					}
					captionLastSafeMismatchStep = m.Steps
				}
			}
			if signature {
				captionSignatureFrames++
				if captionSignatureFirst == 0 {
					captionSignatureFirst = m.Steps
				}
				captionSignatureLast = m.Steps
			}
			if *control {
				return
			}
			eligible := captionReadEnd != 0 && captionWriteCount == 1040 &&
				captionWriteBBox == [4]int{16, 30, 303, 39} && signature && !safeMismatch
			if captionPhase == "unseen" && eligible {
				captionPhase = "ready"
				captionTransitions = append(captionTransitions, map[string]any{
					"event": "ready", "step": m.Steps, "frames": m.Frames,
					"canvas_sha256": canvasSHA, "palette_sha256": paletteSHA})
			} else if captionPhase == "ready" && !eligible {
				captionPhase = "expired"
				captionTransitions = append(captionTransitions, map[string]any{
					"event": "expired", "step": m.Steps, "frames": m.Frames,
					"canvas_sha256": canvasSHA, "palette_sha256": paletteSHA,
					"mode": m.VideoMode()})
			}
			if captionPhase == "ready" {
				captionEligibleFrames++
			}
		})
	}
	if *optionsTitleScreenAudit != "" {
		m.SetOnFrame(func() {
			if m.Steps < 1253000000 || m.Steps > *followUntil {
				return
			}
			titleFrames++
			canvasMatch := true
			for y := 44; y < 59; y++ {
				start, end := y*320+65, y*320+253
				if !bytes.Equal(m.Mem[canvas+uint32(start):canvas+uint32(end)], titleReference[start:end]) {
					canvasMatch = false
					break
				}
			}
			vgaMatch := false
			if canvasMatch && m.VideoMode() == 0x13 {
				titleCanvasMatch++
				if titleFirstCanvas == 0 {
					titleFirstCanvas = m.Steps
				}
				indexed := m.Indexed()
				vgaMatch = true
				for y := 44; y < 59; y++ {
					start, end := y*320+65, y*320+253
					if !bytes.Equal(indexed[start:end], titleReference[start:end]) {
						vgaMatch = false
						break
					}
				}
			}
			if vgaMatch {
				titleVGAMatch++
				if titleFirstVGA == 0 {
					titleFirstVGA = m.Steps
				}
				titleLastVGA = m.Steps
			}
			phase := "absent"
			if canvasMatch {
				phase = "canvas-only"
			}
			if vgaMatch {
				phase = "visible"
			}
			if phase != titlePhase {
				if len(titleTransitions) >= 64 {
					panic("選項標題畫格相位超出審計上限")
				}
				titleTransitions = append(titleTransitions, map[string]any{
					"step": m.Steps, "frame": m.Frames, "phase": phase,
					"canvas_sha256":  hashIntro(m.Mem[canvas : canvas+64000]),
					"palette_sha256": hashIntro(m.DAC[:]), "mode": m.VideoMode(),
				})
				titlePhase = phase
			}
		})
	}
	transferIndex := 0
	transfers := []map[string]any{}
	collectTransfers := func() {
		for transferIndex < len(d.Reads) {
			r := d.Reads[transferIndex]
			transferIndex++
			if !strings.EqualFold(r.Name, "GAME.TXT") {
				continue
			}
			var pos int64 = -1
			for j := len(d.FileOps) - 1; j >= 0; j-- {
				op := d.FileOps[j]
				if op.Step == r.Step && op.Fn == 0x3f && op.Handle == r.Handle && strings.EqualFold(op.Name, r.Name) {
					pos = op.Pos
					break
				}
			}
			if pos < 0 || (r.Step < 55000000 && !*retireAudit) {
				continue
			}
			for _, source := range sources {
				end := source.Offset + int64(len(source.Bytes))
				if !(pos <= source.Offset && end <= pos+int64(r.Got)) {
					continue
				}
				linear := uint32(r.Seg)*16 + uint32(r.Off) + uint32(source.Offset-pos)
				actual := m.Mem[linear : linear+uint32(len(source.Bytes))]
				transfers = append(transfers, map[string]any{"step": r.Step,
					"name": r.Name, "file_offset": source.Offset, "read_pos": pos,
					"got": r.Got, "destination_seg": r.Seg, "destination_off": r.Off,
					"candidate_linear": linear, "prefix_sha256": hashIntro(actual),
					"match": bytes.Equal(actual, []byte(source.Bytes))})
			}
		}
	}
	keyEvents := []map[string]any{}
	lastKeyPending := -1
	terminated := false
	lateIndex := 0
	advance := func(end uint64) {
		for m.Steps < end && !d.Exited && !m.CPU.Halted {
			mustIntro(m.Step())
			if transferIndex < len(d.Reads) {
				collectTransfers()
			}
			if *postCaptionAudit && m.Steps >= 85000000 && m.Steps%1024 == 0 {
				pending := d.KeysPending()
				if pending != lastKeyPending {
					keyEvents = append(keyEvents, map[string]any{"event": "observed", "step": m.Steps,
						"pending": pending, "segments": m.CPU.Seg, "ip": m.CPU.IP})
					lastKeyPending = pending
				}
			}
		}
		if m.Steps != end {
			if *allowEarlyExit && m.Steps >= 1275000000 && (d.Exited || m.CPU.Halted) {
				terminated = true
				return
			}
			panic("原版提前停止")
		}
	}
	apply := func(e introInput) {
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		case "esc":
			d.PushKey(golem.Key{Scan: 0x01, ASCII: 27})
		case "left":
			d.PushKey(golem.Key{Scan: 0x4b, ASCII: 0})
		case "right":
			d.PushKey(golem.Key{Scan: 0x4d, ASCII: 0})
		case "space":
			d.PushKey(golem.Key{Scan: 0x39, ASCII: 0x20})
		default:
			panic("未知玩家輸入")
		}
	}
	for _, e := range replay.Inputs {
		if e.Step > 43000000 {
			break
		}
		advance(e.Step)
		apply(e)
	}
	advance(43000000)
	if hashIntro(m.Indexed()) != "48b52cb99391ab05aafd6809a838cc5714c193d3fca5dc0c1202bb2835a1c835" {
		panic("左卡基準不符")
	}
	d.MoveMouse(route.x, route.y)
	advance(44000000)
	d.PressMouse(0)
	advance(45000000)
	d.ReleaseMouse(0)
	advance(46000000)
	nationIndexedSHA := hashIntro(m.Indexed())
	d.MoveMouse(65, 184)
	advance(47000000)
	d.PressMouse(0)
	advance(48000000)
	d.ReleaseMouse(0)
	advance(49000000)
	nameIndexedSHA := hashIntro(m.Indexed())
	if *nation == "france" && nameIndexedSHA != "128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e" {
		panic("姓名頁基準不符")
	}
	samples := map[string]map[string]any{}
	sample := func(label string) {
		collectTransfers()
		indexed := m.Indexed()
		picture := bytes.Clone(m.Mem[canvas : canvas+64000])
		palette := bytes.Clone(m.DAC[:])
		for suffix, b := range map[string][]byte{"idx": indexed, "canvas": picture, "pal": palette} {
			mustIntro(os.WriteFile(*out+"."+label+"."+suffix, b, 0644))
		}
		hits := map[string][]int{}
		for _, source := range sources {
			cursor := 0
			for cursor < len(m.Mem) {
				at := bytes.Index(m.Mem[cursor:], []byte(source.Bytes))
				if at < 0 {
					break
				}
				cursor += at
				if len(hits[source.Bytes]) < 20 {
					hits[source.Bytes] = append(hits[source.Bytes], cursor)
				}
				cursor++
			}
		}
		entry := map[string]any{"step": m.Steps, "cycles": m.CPU.Cycles,
			"ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg,
			"ip": m.CPU.IP, "flags": m.CPU.Flags, "memory_sha256": hashIntro(m.Mem),
			"indexed_sha256": hashIntro(indexed), "canvas_sha256": hashIntro(picture),
			"palette_sha256": hashIntro(palette), "opened_count": len(d.Opened),
			"resident_hits": hits}
		if *postCaptionAudit {
			entry["key_pending"] = d.KeysPending()
		}
		samples[label] = entry
	}
	advance(55000000)
	sample("55m")
	d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
	for _, s := range []struct {
		label string
		step  uint64
	}{{"56m", 56000000}, {"57m", 57000000}, {"60m", 60000000}, {"65m", 65000000}} {
		advance(s.step)
		sample(s.label)
	}
	if *nextEnter {
		d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		advance(70000000)
		sample("70m")
		advance(75000000)
		sample("75m")
		if *afterB != "none" {
			if *afterB == "enter" {
				d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
			} else if *afterB == "esc" {
				d.PushKey(golem.Key{Scan: 0x01, ASCII: 27})
			}
			advance(80000000)
			sample("80m")
			advance(85000000)
			sample("85m")
			if *afterFollow != "none" {
				if *afterFollow == "enter" {
					d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
					if *postCaptionAudit {
						keyEvents = append(keyEvents, map[string]any{"event": "enqueue-enter", "step": m.Steps, "pending": d.KeysPending()})
						lastKeyPending = d.KeysPending()
					}
				} else if *afterFollow == "esc" {
					d.PushKey(golem.Key{Scan: 0x01, ASCII: 27})
					if *postCaptionAudit {
						keyEvents = append(keyEvents, map[string]any{"event": "enqueue-esc", "step": m.Steps, "pending": d.KeysPending()})
						lastKeyPending = d.KeysPending()
					}
				}
				lateIndex = 0
				phaseIndex := 0
			lateLoop:
				for step := uint64(90000000); step <= *followUntil; {
					for {
						hasInput := lateIndex < len(lateInputs) && lateInputs[lateIndex].Step < step
						hasPhase := phaseIndex < len(phaseSteps) && phaseSteps[phaseIndex] < step
						if !hasInput && !hasPhase {
							break
						}
						if hasPhase && (!hasInput || phaseSteps[phaseIndex] < lateInputs[lateIndex].Step) {
							advance(phaseSteps[phaseIndex])
							if terminated {
								break lateLoop
							}
							sample(fmt.Sprintf("phase-%02d", phaseIndex))
							phaseIndex++
							continue
						}
						advance(lateInputs[lateIndex].Step)
						if terminated {
							break lateLoop
						}
						sample(fmt.Sprintf("before-game-input-%02d", lateIndex))
						apply(lateInputs[lateIndex])
						lateIndex++
					}
					advance(step)
					if terminated {
						break lateLoop
					}
					sample(fmt.Sprintf("%dm", step/1000000))
					if extraEnters[step] {
						d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
						if *postCaptionAudit {
							keyEvents = append(keyEvents, map[string]any{"event": "enqueue-enter", "step": m.Steps, "pending": d.KeysPending()})
							lastKeyPending = d.KeysPending()
						}
					}
					if *postCaptionAudit && step >= 500000000 {
						step += 25000000
					} else {
						step += 5000000
					}
				}
				if terminated {
					sample("terminal")
				} else if lateIndex != len(lateInputs) || phaseIndex != len(phaseSteps) {
					panic("字幕後玩家事件或選項相位取樣未全部送出")
				}
			}
		}
	}
	collectTransfers()
	version := "goal101-intro-v1"
	if *nation == "france" && *afterB == "none" {
		version = "goal098-intro-v3"
	} else if *afterB != "none" {
		version = "goal104-intro-exit-v1"
	}
	if *afterFollow != "none" {
		version = "goal105-tutorial-route-v4"
		if *preprint {
			version = "goal106-build-preprint-v1"
		}
		if *postCaptionAudit {
			version = "goal107-post-caption-audit-v1"
			if *gameInputsPath != "" {
				version = "goal110-game-input-audit-v1"
				if lateInputUsesSpace {
					version = "goal111-game-input-audit-v2"
				}
				if *optionsAudit {
					version = "goal112-game-options-source-v2"
					if len(phaseSteps) > 0 {
						version = "goal119-options-phase-v1"
					}
					if *optionsResidentAudit {
						version = "goal114-options-resident-v1"
					}
					if *optionsPreprint {
						version = "goal113-game-options-preprint-v1"
						if *optionsWriterAudit {
							version = "goal114-options-writer-v4"
						}
					}
				}
			}
		}
	}
	if *allowEarlyExit {
		version = "goal123-retire-terminal-v1"
	}
	if *retireAudit {
		version = "goal126-retire-preprint-v1"
		if *retireFlowAudit {
			version = "goal127-retire-flow-v1"
		}
		if *retireResidentAudit {
			version = "goal127-retire-resident-v1"
		}
	}
	if *captionFrameAudit {
		version = "goal129-caption-frame-audit-v1"
		if *captionScreenAudit {
			version = "goal130-caption-screen-audit-v2"
		}
	}
	if *optionsTitleScreenAudit != "" {
		version = "goal131-options-title-screen-v1"
	}
	report := map[string]any{"version": version, "control": *control,
		"next_enter": *nextEnter,
		"nation":     *nation, "after_b": *afterB,
		"route": map[string]any{"selected_x": route.x, "selected_y": route.y,
			"nation_indexed_sha256": nationIndexedSHA, "name_indexed_sha256": nameIndexedSHA},
		"input_sha256": hashIntro(inputData), "input_hashes": wants,
		"sources": sources, "transfers": transfers, "samples": samples,
		"print_reads": printReads, "writers": writers, "opened": d.Opened,
		"address_space": "original file offset; DOS real-mode CS:IP; 20-bit linear RAM; 320x200 indexed canvas"}
	if *afterFollow != "none" {
		report["after_follow"] = *afterFollow
		if *postCaptionAudit {
			report["key_events"] = keyEvents
		}
		if *followUntil != 100000000 || *followEnterAt != "" {
			report["follow_until"] = *followUntil
			report["follow_enter_at"] = *followEnterAt
		}
	}
	if *captionFrameAudit {
		report["caption_frame_audit"] = map[string]any{
			"event_source":    "GAME.TXT:0x153CE, 0D21:00C6, linear 0x2A560/1",
			"source_sha256":   hashIntro(captionExpected),
			"read_start_step": captionReadStart, "read_end_step": captionReadEnd,
			"read_match_bytes": captionReadStage / 2, "read_mismatches": captionReadMismatch,
			"writer_ip": "0D21:012C", "write_first_step": captionWriteFirst,
			"write_last_step": captionWriteLast, "write_count": captionWriteCount,
			"write_bbox": captionWriteBBox, "frames": captionFrames,
			"signature_frames":     captionSignatureFrames,
			"signature_first_step": captionSignatureFirst,
			"signature_last_step":  captionSignatureLast,
			"eligible_frames":      captionEligibleFrames, "phase_at_end": captionPhase,
			"transitions": captionTransitions,
		}
		if *captionScreenAudit {
			report["caption_screen_audit"] = map[string]any{
				"indexed_mismatch_frames":   captionIndexedMismatchFrames,
				"safe_mismatch_frames":      captionSafeMismatchFrames,
				"first_safe_mismatch_step":  captionFirstSafeMismatchStep,
				"last_safe_mismatch_step":   captionLastSafeMismatchStep,
				"first_read_canvas_sha256":  captionFirstReadCanvasSHA,
				"first_write_canvas_sha256": captionFirstWriteCanvasSHA,
				"read_operands":             captionReadOperands,
				"safe_logical":              [4]int{12, 27, 307, 42},
			}
		}
	}
	if *gameInputsPath != "" {
		report["game_inputs"] = lateInputs
		report["game_inputs_sha256"] = lateInputHash
	}
	if *allowEarlyExit {
		report["game_terminal"] = map[string]any{"observed": terminated,
			"step": m.Steps, "dos_exited": d.Exited, "cpu_halted": m.CPU.Halted,
			"events_delivered": lateIndex, "events_total": len(lateInputs)}
	}
	if *scratch != "" {
		report["scratch"] = true
		report["write_intents"] = d.Wrote
	}
	if *retireAudit && !*control && !*retireResidentAudit {
		preprints := map[string]any{}
		for _, name := range []string{"question", "yes", "no"} {
			before := retireBefore[name]
			if len(before) != 64000 {
				panic("退休確認框印前底圖缺失：" + name)
			}
			mustIntro(os.WriteFile(*out+".before-"+name+".canvas", before, 0644))
			preprints[name] = map[string]any{"step": retireFirstSteps[name], "canvas_sha256": hashIntro(before)}
		}
		report["retire_preprint"] = preprints
	}
	if *retireFlowAudit {
		if len(retireFlowReads) == 50000 || len(retireFlowWrites) == 50000 {
			panic("退休資料流監看事件超出上限")
		}
		report["retire_flow_reads"] = retireFlowReads
		report["retire_flow_writes"] = retireFlowWrites
		report["retire_flow_window"] = [2]uint64{1253240000, 1253355000}
	}
	if *retireResidentAudit {
		if len(retireResidentWrites) == 20000 {
			panic("退休高位址監看事件超出上限")
		}
		report["retire_resident_writes"] = retireResidentWrites
		report["retire_resident_window"] = [2]uint64{1253240000, 1253355000}
	}
	if *optionsAudit {
		report["option_source_reads"] = optionSourceReads
		if *optionsTitleScreenAudit != "" {
			report["option_title_screen_audit"] = map[string]any{
				"reference_sha256": hashIntro(titleReference),
				"safe":             optionSafe[0], "frames": titleFrames,
				"canvas_match_frames": titleCanvasMatch, "vga_match_frames": titleVGAMatch,
				"first_canvas_step": titleFirstCanvas, "first_vga_step": titleFirstVGA,
				"last_vga_step": titleLastVGA, "phase_at_end": titlePhase,
				"transitions": titleTransitions,
			}
		}
		if len(phaseSteps) > 0 {
			report["option_phase_steps"] = phaseSteps
		}
		if *optionsResidentAudit {
			report["option_resident_writes"] = optionResidentWrites
		}
	}
	if *optionsPreprint {
		report["option_print_writes"] = optionPrintWrites
		if *optionsWriterAudit {
			report["option_writer_reads"] = optionWriterReads
			report["option_intermediate_writes"] = optionIntermediateWrites
		}
		preprints := map[string]any{}
		if !*control && len(optionBefore) != len(optionSafe) {
			panic("遊戲選項九欄印前底圖不完整")
		}
		for index, before := range optionBefore {
			name := fmt.Sprintf("option-before-%02d", index)
			if len(before) != 64000 {
				panic("遊戲選項印前底圖尺寸不符")
			}
			mustIntro(os.WriteFile(*out+"."+name+".canvas", before, 0644))
			preprints[name] = map[string]any{"step": optionFirstSteps[index],
				"canvas_sha256": hashIntro(before), "writes": optionWriteCounts[index],
				"safe": optionSafe[index], "writer_ip": "0D21:012C"}
		}
		report["option_preprint"] = preprints
	}
	if *preprint {
		phases := []string{"first", "second"}
		if *afterFollow != "none" && *afterFollow != "wait" {
			phases = append(phases, "after-follow")
		}
		if *control || !*nextEnter || len(preprintCanvas) != len(phases) {
			panic("印前底圖需要當次實際印字及觀測收據")
		}
		preprintReceipt := map[string]any{}
		for _, phase := range phases {
			b := preprintCanvas[phase]
			if len(b) != 64000 {
				panic("印前畫布大小不符：" + phase)
			}
			mustIntro(os.WriteFile(*out+"."+phase+".pre.canvas", b, 0644))
			preprintReceipt[phase] = map[string]any{"step": preprintSteps[phase],
				"canvas_sha256": hashIntro(b), "writer_ip": "0D21:012C"}
		}
		report["preprint"] = preprintReceipt
	}
	b, err := json.MarshalIndent(report, "", "  ")
	mustIntro(err)
	mustIntro(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("control=%v transfers=%d print_reads=%d writers=%d end=%d opened=%d\n",
		*control, len(transfers), len(printReads), len(writers), m.Steps, len(d.Opened))
}
