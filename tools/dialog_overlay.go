package main

// 目標165（規格035）：通用對話框整句中文覆蓋的純邏輯（模板比對、變數譯名、依框寬重排與三層字模）。
// 目標166（規格036）：同一段落偵測另支援置中段落（^）與逐行清單（下拉選單、選項列、單行字串）。
// 監看、權杖與啟用閘門在 live_menu.go；本檔不讀寫原版記憶體。

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"image"
	"regexp"
	"strconv"
	"strings"
	"unicode"

	"github.com/wicanr2/dosgolem/overlay"
)

type dialogTemplate struct {
	id    string
	re    *regexp.Regexp
	names []string // 依出現順序的變數名：%STRINGn、%NUMBERn、%COUNTRY
	// quoted 標示原文以雙引號緊貼包住的變數（目標177）：玩家輸入，原樣代入、不查術語表。
	quoted []bool
	zh     string // 正文譯稿（空行前），保留 {} 強調標記與 %變數；置中段落另保留 \n 與 ^
	// 目標166：原文含 ^ 置中碼的段落（例如國王接見），依譯稿的 ^^ 行置中、其餘依寬度重排。
	centered        bool
	literalPercents int // 規格036：只由百科原始 %% 確認的字面百分比數量；其他模板為0。
}

type dialogFont struct {
	glyphs            map[rune]*image.Alpha
	widths            map[rune]int
	cjkTop, cjkBottom int
}

type dialogCatalog struct {
	routeDeleteChoice string
	voyageRoles       map[string]map[string]bool  // 規格035 READY：驗證NAMES來源角色。
	messageOptions    map[string][]dialogTemplate // 規格036：原檔正文鍵對應的完整選項。
	templates         []dialogTemplate
	unitCaptionNames  map[string]string // 規格035 READY：只來自驗證的UNIT資料列。
	dockOptionSets    [][]dialogTemplate
	dockOptions       []dialogTemplate
	portShipOptions   []dialogTemplate   // 規格035 READY：歐洲空貨艙船隻的三列完整選項。
	shipOptions       []dialogTemplate   // 規格036 READY：空貨艙完整三列。
	shipOptionSets    [][]dialogTemplate // 規格036 READY：正常載貨與下錨的完整列組合。
	lines             []dialogTemplate   // 目標166：逐行清單比對用的單行模板
	seen              map[string]bool    // 已載入的訊息鍵（跨語料檢查重複）
	terms             map[string]string  // 英文→譯名；定稿譯名彼此衝突者為空字串（視為查無）
	canon             map[string]bool    // 目標167：來自定稿譯名表（優先於 NAMES.TXT 對照）的詞
	fonts             map[int]*dialogFont
	// 規格035：只供已取證 ABANDON 正文的殖民地名稱欄；來源綁定有效時由前端接入。
	colonyValue     func(string) string
	saveDescription func(string) (string, bool)
}

type dialogChar struct {
	c                  byte
	box                image.Rectangle // 無墨跡（空白）時為空矩形
	colors             map[byte]int    // 目標166：本字改色點的色號分布
	contig             bool            // 目標178：來自段內連續字串（選單的停用項目）
	prefixContinuation bool            // 規格036：暫留無墨跡熱鍵前綴，收尾須確認後續字形。
}

type dialogGlyph struct {
	r      rune
	accent bool
}

const (
	dialogFontPx    = 30 // A 版：與 help A 版同字級（原版墨跡 7 邏輯像素）
	dialogFloorPx   = 20 // 使用者 2026-09-26 決定：縮字下限為欄位字級 2/3（字高 7 時）
	dialogAtlasMin  = 12 // 目標170：圖集字級下限（字高 5 的框起始 22px、下限 15px）
	dialogPitchAtPx = 40 // 30px 時行距 40 輸出像素（原版 10 邏輯像素）
)

var (
	dialogVar       = regexp.MustCompile(`%STRING\d|%NUMBER\d|%COUNTRY`)
	dialogSpaces    = regexp.MustCompile(`\s+`)
	dialogLineStart = "，。；：、！？％%）】》」』,.;:!?)]}"
	dialogLineEnd   = "（【《「『([{"
)

func dialogNormalize(s string) string {
	return strings.TrimSpace(dialogSpaces.ReplaceAllString(s, " "))
}

// splitTSV 以 tab 切欄、不處理引號（語料欄內有英文雙引號）。
func splitTSV(data []byte) []map[string]string {
	lines := strings.Split(strings.TrimRight(string(data), "\n"), "\n")
	header := strings.Split(lines[0], "\t")
	var rows []map[string]string
	for _, line := range lines[1:] {
		f := strings.Split(line, "\t")
		if len(f) != len(header) {
			return nil
		}
		row := map[string]string{}
		for i, h := range header {
			row[h] = f[i]
		}
		rows = append(rows, row)
	}
	return rows
}

// loadDialogCatalog 由語料清冊建立 GAME.TXT 正文模板；每列都以原版檔案位移、長度與片段雜湊核對。
// exclude 內的訊息鍵由專屬欄位處理，不進本引擎。
func loadDialogCatalog(corpus, terms []byte, game []byte, gameSHA string, exclude map[string]bool) (*dialogCatalog, error) {
	if fmt.Sprintf("%x", sha256.Sum256(game)) != gameSHA {
		return nil, fmt.Errorf("GAME.TXT 版本不符")
	}
	cat := &dialogCatalog{terms: map[string]string{}, seen: map[string]bool{}}
	if err := cat.addCorpus(corpus, game, gameSHA, exclude); err != nil {
		return nil, err
	}
	for _, r := range splitTSV(terms) {
		cat.addTerm(r["en"], r["zh"])
	}
	return cat, nil
}

// addCorpus 加入一份語料 TSV 的 GAME.TXT 模板（語料清冊或 help 雙語清冊，欄名相同）；
// NAMES.TXT 列另作變數譯名對照。每列以原檔位移、長度與片段雜湊核對。
func (cat *dialogCatalog) addCorpus(corpus, game []byte, gameSHA string, exclude map[string]bool) error {
	rows := splitTSV(corpus)
	if rows == nil {
		return fmt.Errorf("語料清冊欄位不符")
	}
	seen := cat.seen
	for _, r := range rows {
		if r["source_file"] != "GAME.TXT" {
			if r["source_file"] == "NAMES.TXT" {
				cat.addNamePairs(r["source_en"], r["zh_hant"])
			}
			continue
		}
		if r["source_file_sha256"] != gameSHA || exclude[r["message_id"]] || r["zh_hant"] == "" {
			continue
		}
		off, err1 := strconv.ParseInt(r["text_offset"], 0, 64)
		n, err2 := strconv.Atoi(r["text_byte_length"])
		if err1 != nil || err2 != nil || off < 0 || int(off)+n > len(game) {
			return fmt.Errorf("位移不符：%s", r["message_id"])
		}
		raw := game[off : int(off)+n]
		if fmt.Sprintf("%x", sha256.Sum256(raw)) != r["source_bytes_sha256"] {
			return fmt.Errorf("片段雜湊不符：%s", r["message_id"])
		}
		if seen[r["message_id"]] {
			return fmt.Errorf("重複鍵：%s", r["message_id"])
		}
		seen[r["message_id"]] = true
		parts := strings.SplitN(string(raw), "\r\n\r\n", 2)
		zhParts := strings.SplitN(r["zh_hant"], `\n\n`, 2)
		body := parts[0]
		if strings.Contains(body, "@") {
			continue // 指令列另案
		}
		centered := strings.Contains(body, "^")
		zh := zhParts[0]
		if !centered {
			zh = strings.ReplaceAll(zh, `\n`, "")
		}
		cat.templates = append(cat.templates, makeDialogTemplate(r["message_id"], body, zh, centered))
		// 規格035／036 READY：原始整列仍先以完整來源雜湊驗證，加入已驗第3至5列及駐守後第2列；未驗第1列不加入。
		if r["message_id"] == "GAME.TXT:@UNITOPTIONS:0x00009A64" {
			eo := strings.Split(strings.TrimSpace(body), "\r\n")
			zo := strings.Split(r["zh_hant"], `\n`)
			if len(eo) == 5 && len(zo) == 5 && eo[1] == "Clear orders." && eo[2] == "Sentry / Board ship." && eo[3] == "Fortify." && eo[4] == "No changes." {
				for i := 1; i < 5; i++ {
					cat.lines = append(cat.lines, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
				}
			}
		}

		// 規格035 READY：只載入原版已觀測的完整六列碼頭組合。
		if r["message_id"] == "GAME.TXT:@ARMOPTIONS:0x000098AC" {
			eo := strings.Split(strings.TrimSpace(body), "\r\n")
			zo := strings.Split(r["zh_hant"], `\n`)
			if len(eo) == 12 && len(zo) == 12 {
				for _, i := range []int{0, 3, 5, 7, 9, 11} {
					cat.dockOptions = append(cat.dockOptions, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
				}
				for _, indices := range [][]int{{1, 3, 5, 7, 9, 11}, {0, 4, 7, 11}, {1, 4, 7, 11}, {1, 6, 11}, {1, 3, 8, 11}, {0, 10, 11}, {1, 10, 11}, {0, 2, 3, 5, 7, 9, 11}, {1, 2, 3, 5, 7, 9, 11}} {
					var group []dialogTemplate
					for _, i := range indices {
						group = append(group, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
					}
					cat.dockOptionSets = append(cat.dockOptionSets, group)
				}

			}
		}
		if r["message_id"] == "GAME.TXT:@EUROPESHIPOPTIONS:0x00009B3D" {
			eo := strings.Split(strings.TrimSpace(body), "\r\n")
			zo := strings.Split(r["zh_hant"], `\n`)
			if len(eo) == 4 && len(zo) == 4 {
				for i := range eo {
					cat.portShipOptions = append(cat.portShipOptions, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
				}
				if cat.messageOptions == nil {
					cat.messageOptions = map[string][]dialogTemplate{}
				}
				cat.messageOptions["GAME.TXT:@EUROPESHIPCLICK:0x00009874"] = cat.portShipOptions
			}
		}
		if r["message_id"] == "GAME.TXT:@SHIPOPTIONS:0x00009AC0" {
			eo := strings.Split(strings.TrimSpace(body), "\r\n")
			zo := strings.Split(r["zh_hant"], `\n`)
			if len(eo) == 6 && len(zo) == 6 && eo[1] == "Clear orders." && eo[2] == "Sentry." && eo[3] == "Anchor in harbor (\"Fortify\")." && eo[5] == "No changes." && eo[4] == "Unload all cargo." {
				for _, indices := range [][]int{{2, 3, 4, 5}, {1, 2, 5}} {
					group := make([]dialogTemplate, 0, len(indices))
					for _, i := range indices {
						group = append(group, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
					}
					cat.shipOptionSets = append(cat.shipOptionSets, group)
				}
				for _, i := range []int{2, 3, 5} {
					cat.shipOptions = append(cat.shipOptions, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
				}
			}
		}
		if !centered && !strings.Contains(body, "\r\n") {
			cat.lines = append(cat.lines, makeDialogTemplate(r["message_id"], body, zh, false))
		}
		// 選項行：空行後逐行對應譯稿空行後的各行；行數不同即不採用。
		if len(parts) == 2 && len(zhParts) == 2 {
			var eo, zo []string
			for _, l := range strings.Split(parts[1], "\r\n") {
				if strings.TrimSpace(l) != "" && !strings.ContainsAny(l, "@^") {
					eo = append(eo, l)
				}
			}
			for _, l := range strings.Split(zhParts[1], `\n`) {
				if strings.TrimSpace(l) != "" {
					zo = append(zo, l)
				}
			}
			if len(eo) == len(zo) {
				if len(eo) > 0 && cat.messageOptions == nil {
					cat.messageOptions = map[string][]dialogTemplate{}
				}
				for i := range eo {
					cat.messageOptions[r["message_id"]] = append(cat.messageOptions[r["message_id"]], makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
					cat.lines = append(cat.lines, makeDialogTemplate(fmt.Sprintf("%s#%d", r["message_id"], i+1), eo[i], zo[i], false))
				}
			}
		}
	}
	return nil
}

// makeDialogTemplate 把原文正規化成整句比對用的正規式：去 {}、^，換行當空白並壓縮空白。
// addPedia 加入百科雙語稿的條目正文（目標171）：每列以 PEDIA.TXT 位移、長度與片段雜湊核對，
// 正文含 ^ 段落碼，以置中段落型版面（規格036）排版。
func (c *dialogCatalog) addPedia(tsv, pedia []byte) error {
	rows := splitTSV(tsv)
	if rows == nil {
		return fmt.Errorf("百科雙語稿欄位不符")
	}
	sum := fmt.Sprintf("%x", sha256.Sum256(pedia))
	for _, r := range rows {
		if r["source_file"] != "PEDIA.TXT" || r["zh_hant"] == "" {
			continue
		}
		off, err1 := strconv.ParseInt(r["text_offset"], 0, 64)
		n, err2 := strconv.Atoi(r["text_byte_length"])
		if r["source_file_sha256"] != sum || err1 != nil || err2 != nil || off < 0 || int(off)+n > len(pedia) {
			return fmt.Errorf("PEDIA.TXT 版本或位移不符：%s", r["message_id"])
		}
		raw := pedia[off : int(off)+n]
		if fmt.Sprintf("%x", sha256.Sum256(raw)) != r["source_bytes_sha256"] {
			return fmt.Errorf("PEDIA.TXT 片段雜湊不符：%s", r["message_id"])
		}
		if c.seen[r["message_id"]] {
			return fmt.Errorf("重複鍵：%s", r["message_id"])
		}
		c.seen[r["message_id"]] = true
		// 原文逐位元組轉成碼位；規格036證實0xF9在此印字入口不繪製，匹配正文時略去。
		body := make([]rune, len(raw))
		for i, b := range raw {
			body[i] = rune(b)
		}
		// 規格036目標180：百科原版將 %% 顯示為 %；TSV 原始控制碼仍保留。
		shownBody := strings.NewReplacer("%%", "%", "\u00F9", "").Replace(string(body))
		shownZh := strings.NewReplacer("%%", "%", `\t`, "\t").Replace(r["zh_hant"])
		t := makeDialogTemplate(r["message_id"], shownBody, shownZh, true)
		escaped := strings.Count(r["zh_hant"], "%%")
		if strings.Count(r["zh_hant"], "%") == 2*escaped {
			t.literalPercents = escaped
		}
		c.templates = append(c.templates, t)
	}
	return nil
}

func makeDialogTemplate(id, body, zh string, centered bool) dialogTemplate {
	body = dialogNormalize(strings.NewReplacer("{", "", "}", "", "^", "", "\r\n", " ").Replace(body))
	// 規格035／036 READY：只處理已取證的同一強調群組，不猜原版兩個變數的分界。
	if id == "GAME.TXT:@COLONYUNIT:0x00009A33" && body == "Options for %STRING0%STRING1:" && zh == "{%STRING0%STRING1}的選項：" {
		return dialogTemplate{id: id, re: regexp.MustCompile(`^Options for (.+?):$`), names: []string{"%STRING0%STRING1"}, quoted: []bool{false}, zh: zh, centered: centered}
	}
	pattern, names, quoted := "^", []string{}, []bool{}
	last := 0
	for _, m := range dialogVar.FindAllStringIndex(body, -1) {
		pattern += regexp.QuoteMeta(body[last:m[0]])
		name := body[m[0]:m[1]]
		q := m[0] > 0 && m[1] < len(body) && body[m[0]-1] == '"' && body[m[1]] == '"'
		switch {
		case strings.HasPrefix(name, "%NUMBER"):
			pattern += `(\d+)`
		case q:
			pattern += `(.*?)` // 目標177：玩家輸入可為空（直接按 Enter）
		default:
			pattern += `(.+?)`
		}
		names = append(names, name)
		quoted = append(quoted, q)
		last = m[1]
	}
	pattern += regexp.QuoteMeta(body[last:]) + "$"
	return dialogTemplate{id: id, re: regexp.MustCompile(pattern), names: names, quoted: quoted, zh: zh, centered: centered}
}

// addDraft 由譯稿 TSV（draft.zh-Hant.tsv）加入逐行模板：GAME.TXT 單行列與 MENU.TXT 選單項目；
// NAMES.TXT 列另作變數譯名對照。
// 每列以原檔位移與片段雜湊核對；exclude 內是已由專屬欄位處理的鍵。
// 含熱鍵標記 ~ 或 # 的列顯示方式未取證，本輪不採用。
func (c *dialogCatalog) addDraft(draft []byte, files map[string][]byte, exclude map[string]bool) error {
	rows := splitTSV(draft)
	if rows == nil {
		return fmt.Errorf("譯稿 TSV 欄位不符")
	}
	for _, r := range rows {
		// 此列由來源驗證的槽位專用回呼載入。
		if r["candidate_id"] == slotEmptyID {
			continue
		}
		data, ok := files[r["source_file"]]
		if !ok || exclude[r["candidate_id"]] {
			continue
		}
		off, err1 := strconv.ParseInt(r["byte_offset"], 0, 64)
		n, err2 := strconv.Atoi(r["source_byte_length"])
		if r["source_sha256"] != fmt.Sprintf("%x", sha256.Sum256(data)) || err1 != nil || err2 != nil || off < 0 || int(off)+n > len(data) {
			return fmt.Errorf("%s 版本或位移不符：%s", r["source_file"], r["candidate_id"])
		}
		raw := string(data[off : int(off)+n])
		if fmt.Sprintf("%x", sha256.Sum256([]byte(raw))) != r["source_bytes_sha256"] {
			return fmt.Errorf("%s 片段雜湊不符：%s", r["source_file"], r["candidate_id"])
		}
		zh := strings.TrimSpace(r["zh_hant"])
		if r["source_file"] == "NAMES.TXT" {
			// 目標167：譯稿的 NAMES.TXT 單詞（例如歐洲母港名）作變數譯名對照，優先序低於定稿譯名。
			c.addNamePairs(raw, zh)
			continue
		}
		if r["source_file"] == "MENU.TXT" && zh != "" && !strings.Contains(raw, "\r\n") && !strings.ContainsAny(raw, "@^") {
			// 目標177：下拉選單的 ~ 是熱鍵標記（不印出，後一字以強調色顯示）、# 是無墨的對齊空白（照印）。
			c.lines = append(c.lines, makeDialogTemplate(r["candidate_id"], strings.ReplaceAll(raw, "~", ""), menuZh(zh), false))
			continue
		}

		if r["candidate_id"] == "GAME.TXT:0x000002C8" && r["source_file"] == "GAME.TXT" && raw == "^^Select Map File to Load" && zh == "^^選擇要載入的地圖檔" {
			c.templates = append(c.templates, makeDialogTemplate(r["candidate_id"], raw, zh, true))
			continue
		}
		if zh == "" || strings.Contains(raw, "\r\n") || strings.ContainsAny(raw, "~#@^") || strings.ContainsAny(zh, "~#^") {
			continue
		}
		c.lines = append(c.lines, makeDialogTemplate(r["candidate_id"], raw, zh, false))
		// 規格035 SAVEGOOD：已驗完整正文，原版會自動折行。
		if r["candidate_id"] == "GAME.TXT:0x000007B9" && r["source_file"] == "GAME.TXT" {
			c.templates = append(c.templates, makeDialogTemplate(r["candidate_id"], raw, zh, false))
		}
	}
	return nil
}

// menuZh 把下拉選單譯稿的標記換成顯示用文字（目標177）：括號外的 ~X 熱鍵集中到行首成 (X)，
// 與頂端選單列、港口按鈕的熱鍵樣式一致；括號內的 ~X 留在原位；熱鍵字母以強調色（{}）標示；# 換成空白。
func menuZh(zh string) string {
	var keys, out []rune
	depth := 0
	rs := []rune(zh)
	for i := 0; i < len(rs); i++ {
		switch r := rs[i]; {
		case r == '~' && i+1 < len(rs):
			i++
			if depth > 0 {
				out = append(out, '{', rs[i], '}')
			} else {
				keys = append(keys, rs[i])
			}
		case r == '#':
			out = append(out, ' ')
		default:
			if r == '(' {
				depth++
			} else if r == ')' && depth > 0 {
				depth--
			}
			out = append(out, r)
		}
	}
	s := strings.TrimRight(string(out), " ")
	if len(keys) == 0 {
		return s
	}
	// 熱鍵放在譯稿原本的縮排之後；熱鍵後面的分隔空白一併去掉。
	indent := len(zh) - len(strings.TrimLeft(zh, " "))
	return zh[:indent] + "({" + string(keys) + "})" + strings.TrimLeft(s, " ")
}

// addValues 讀執行檔提供的變數值譯名（例如版本日期）；每列以原檔位移核對原文。
func (c *dialogCatalog) addValues(tsv []byte, files map[string][]byte) error {
	rows := splitTSV(tsv)
	if rows == nil {
		return fmt.Errorf("變數值 TSV 欄位不符")
	}
	for _, r := range rows {
		data, ok := files[r["source_file"]]
		off, err := strconv.ParseInt(r["byte_offset"], 0, 64)
		if !ok || err != nil || fmt.Sprintf("%x", sha256.Sum256(data)) != r["source_sha256"] ||
			off < 0 || int(off)+len(r["en"]) > len(data) || string(data[off:int(off)+len(r["en"])]) != r["en"] {
			return fmt.Errorf("變數值來源不符：%s", r["en"])
		}
		c.addTerm(r["en"], r["zh"])
	}
	return nil
}

// addTerm 加入定稿譯名：優先於 NAMES.TXT 對照；定稿譯名彼此衝突即視為查無。
func (c *dialogCatalog) addTerm(en, zh string) {
	en, zh = strings.TrimSpace(en), strings.TrimSpace(zh)
	if en == "" || zh == "" {
		return
	}
	if c.canon == nil {
		c.canon = map[string]bool{}
	}
	if old, ok := c.terms[en]; ok && c.canon[en] && old != zh {
		c.terms[en] = ""
		return
	}
	c.terms[en], c.canon[en] = zh, true
}

// addWeakTerm 加入 NAMES.TXT 對照：只補定稿譯名沒有的詞；對照彼此衝突時保留先出現者。
func (c *dialogCatalog) addWeakTerm(en, zh string) {
	en, zh = strings.TrimSpace(en), strings.TrimSpace(zh)
	if en == "" || zh == "" {
		return
	}
	if _, ok := c.terms[en]; !ok {
		c.terms[en] = zh
	}
}

// addNamePairs 只在原文與譯文逗號數相同時逐欄配對含英文字母的欄位。
func (c *dialogCatalog) addNamePairs(en, zh string) {
	e, z := strings.Split(en, ","), strings.Split(zh, ",")
	if len(e) != len(z) {
		return
	}
	for i := range e {
		if strings.IndexFunc(e[i], unicode.IsLetter) >= 0 {
			c.addWeakTerm(e[i], z[i])
		}
	}
}

// dialogShownText 依逐字事件重組原版顯示字串：x 回捲即換行，行間補一個空白，再壓縮空白。
// dialogHotkeyMark 判斷選單熱鍵記號 `~`：連續字串路徑會把它讀進來但不印出（沒有墨跡），逐字路徑則不含它。
func dialogHotkeyMark(ch dialogChar) bool { return ch.c == '~' && ch.box.Empty() }

// dialogNonprintingBullet 保留原始事件，但不把已取證的無墨跡F9放入顯示字串（規格036目標180）。
func dialogNonprintingBullet(ch dialogChar) bool { return ch.c == 0xF9 && ch.box.Empty() }

func dialogShownText(chars []dialogChar) string {
	var b strings.Builder
	lastX := -1
	for _, ch := range chars {
		if !ch.box.Empty() {
			if lastX >= 0 && ch.box.Min.X < lastX {
				b.WriteByte(' ')
			}
			lastX = ch.box.Min.X
		}
		if ch.c != 0 && !dialogHotkeyMark(ch) && !dialogNonprintingBullet(ch) {
			b.WriteByte(ch.c)
		}
	}
	return dialogNormalize(b.String())
}

var dialogPlainValue = regexp.MustCompile(`^[0-9][0-9.,%$]*$`)

// match 回傳唯一命中的模板與代入變數後的中文；reason 非空即回原文。
func (c *dialogCatalog) match(shown string) (id, zh, reason string) {
	t, zh, reason := c.matchIn(c.templates, shown)
	if t != nil {
		id = t.id
	}
	return id, zh, reason
}

// matchIn 在指定模板集合中整句比對；數字與純數值變數原樣保留，其餘查譯名。
var dialogSaveFilename = regexp.MustCompile(`^COLONY[0-9]{2}[.]SAV$`)

func (c *dialogCatalog) matchIn(list []dialogTemplate, shown string) (*dialogTemplate, string, string) {
	var hit *dialogTemplate
	var groups []string
	for i := range list {
		t := &list[i]
		if m := t.re.FindStringSubmatch(shown); m != nil {
			if hit != nil && hit.zh != t.zh {
				return nil, "", "template-not-unique"
			}
			hit, groups = t, m[1:]
		}
	}
	if hit == nil {
		return nil, "", "no-template"
	}
	zh := hit.zh
	for i, name := range hit.names {
		v := groups[i]
		if hit.id == "GAME.TXT:0x00000854" && name == "%STRING0" {
			// 規格035：已取證的讀檔成功欄位只保留已量測格式的檔名，不經術語翻譯。
			if !dialogSaveFilename.MatchString(v) {
				return hit, "", "unverified-save-filename"
			}
		} else if (hit.id == "GAME.TXT:0x000007F0" || hit.id == "GAME.TXT:0x00000971" || hit.id == "GAME.TXT:0x0000088B" || hit.id == "GAME.TXT:0x000008C7" || hit.id == "GAME.TXT:@LOADSIZE:0x00000904") && name == "%STRING0" {
			// 規格035 READY：已取證的存讀檔錯誤來源保留格式已核對的檔名。
			if !dialogSaveFilename.MatchString(v) {
				return hit, "", "unverified-save-filename"
			}
		} else if hit.id == "GAME.TXT:0x000007B9" && name == "%STRING0" {
			if !dialogSaveFilename.MatchString(v) {
				return hit, "", "unverified-save-filename"
			}
		} else if hit.id == "GAME.TXT:0x000007B9" && name == "%STRING1" {
			if c.saveDescription == nil {
				return hit, "", "unverified-save-description"
			}
			var ok bool
			v, ok = c.saveDescription(v)
			if !ok {
				return hit, "", "unverified-save-description"
			}
		} else if ((hit.id == "GAME.TXT:0x00001447" || hit.id == "GAME.TXT:@FULL:0x00001482" || hit.id == "GAME.TXT:@TOONEAR:0x00006A24" || hit.id == "GAME.TXT:@ABANDON2:0x00001A5B" || hit.id == "GAME.TXT:@ALREADYHAVE:0x0000AD9D" || hit.id == "GAME.TXT:@NOMOREWAREHOUSE:0x0001527E" || hit.id == "GAME.TXT:@NOMOREWAGONS:0x00015315") && name == "%STRING0") || (hit.id == "GAME.TXT:@INDIANFOREST2:0x00004F7B" && name == "%STRING1") {
			if c.colonyValue == nil {
				return hit, "", "unverified-colony-name"
			}
			if strings.ContainsAny(v, "{}") {
				return hit, "", "unrenderable-variable"
			}
			v = c.colonyValue(v)
		} else if hit.id == "GAME.TXT:@TUTORIAL6" && name == "%STRING1" {
			// 規格035 READY：貨物提示中的名稱只沿既有城市顯示回呼。
			if c.colonyValue == nil {
				return hit, "", "unverified-colony-name"
			}
			if strings.ContainsAny(v, "{}") {
				return hit, "", "unrenderable-variable"
			}
			v = c.colonyValue(v)
		} else if (hit.id == "GAME.TXT:@TUTORIAL12" || hit.id == "GAME.TXT:@TUTORIAL7" || hit.id == "GAME.TXT:@TUTORIAL15") && name == "%STRING0" {
			// 規格035 READY：名稱只經殖民地顯示回呼，拒絕玩家強調碼。
			if c.colonyValue == nil {
				return hit, "", "unverified-colony-name"
			}
			if strings.ContainsAny(v, "{}") {
				return hit, "", "unrenderable-variable"
			}
			v = c.colonyValue(v)
		} else if (hit.id == "GAME.TXT:@CARGOLOAD:0x0000862B" || hit.id == "GAME.TXT:@CARGOUNLOAD:0x0000866E") && name == "%STRING0" {
			if c.colonyValue == nil {
				return hit, "", "cargo-colony-provider-unavailable"
			}
			if strings.ContainsAny(v, "{}") {
				return hit, "", "unrenderable-variable"
			}
			v = c.colonyValue(v)
		} else if hit.id == "GAME.TXT:@ABANDON:0x00001994" && name == "%STRING0" && c.colonyValue != nil {
			// 名稱是玩家資料，不能交給一般術語或強調碼解讀。
			if strings.ContainsAny(v, "{}") {
				return hit, "", "unrenderable-variable"
			}
			v = c.colonyValue(v)
		} else if hit.id == "GAME.TXT:@COLONYUNIT:0x00009A33" && name == "%STRING0%STRING1" {
			tr := c.unitCaptionNames[v]
			if tr == "" {
				return hit, "", "unverified-unit-caption-name"
			}
			v = tr
		} else if !strings.HasPrefix(name, "%NUMBER") && !dialogPlainValue.MatchString(v) && !hit.quoted[i] {
			tr := c.terms[v]
			if tr == "" {
				return hit, "", "variable-without-term"
			}
			v = tr
		}
		zh = strings.Replace(zh, name, v, -1)
	}
	if strings.Count(zh, "%") != hit.literalPercents {
		return hit, "", "unresolved-variable"
	}
	return hit, zh, ""
}

func dialogMarked(zh string) ([]dialogGlyph, bool) {
	var out []dialogGlyph
	accent := false
	for _, r := range zh {
		switch r {
		case '{':
			if accent {
				return nil, false
			}
			accent = true
		case '}':
			if !accent {
				return nil, false
			}
			accent = false
		default:
			out = append(out, dialogGlyph{r, accent})
		}
	}
	return out, !accent
}

// dialogWrap 依寬度與行首／行尾禁則折行；連續 ASCII 英數字不拆開。
func dialogWrap(glyphs []dialogGlyph, f *dialogFont, limit int) ([][]dialogGlyph, bool) {
	var lines [][]dialogGlyph
	var cur []dialogGlyph
	w := 0
	for _, g := range glyphs {
		gw, ok := f.widths[g.r]
		if !ok {
			return nil, false
		}
		if len(cur) == 0 || w+gw <= limit {
			cur, w = append(cur, g), w+gw
			continue
		}
		carried := []dialogGlyph{g}
		if strings.ContainsRune(dialogLineStart, g.r) && len(cur) > 1 {
			carried = append([]dialogGlyph{cur[len(cur)-1]}, carried...)
			cur = cur[:len(cur)-1]
		}
		for len(cur) > 1 && isASCIIAlnum(cur[len(cur)-1].r) && isASCIIAlnum(carried[0].r) {
			carried = append([]dialogGlyph{cur[len(cur)-1]}, carried...)
			cur = cur[:len(cur)-1]
		}
		for len(cur) > 1 && strings.ContainsRune(dialogLineEnd, cur[len(cur)-1].r) {
			carried = append([]dialogGlyph{cur[len(cur)-1]}, carried...)
			cur = cur[:len(cur)-1]
		}
		lines = append(lines, cur)
		cur, w = carried, 0
		for _, c := range cur {
			w += f.widths[c.r]
		}
	}
	if len(cur) > 0 {
		lines = append(lines, cur)
	}
	for _, line := range lines {
		lw := 0
		for _, g := range line {
			lw += f.widths[g.r]
		}
		if lw > limit || strings.ContainsRune(dialogLineStart, line[0].r) || strings.ContainsRune(dialogLineEnd, line[len(line)-1].r) {
			return nil, false
		}
	}
	return lines, true
}

func isASCIIAlnum(r rune) bool {
	return r < 0x80 && (unicode.IsLetter(r) || unicode.IsDigit(r))
}

// dialogMasks 在 w×h 輸出像素的安全區內排版，回傳陰影、一般、強調三層與所用字級；放不下回傳 0。
// 字頭（中文墨跡上緣）對齊安全區上緣 +4、左緣 +4；陰影向右下 4 輸出像素。
// dialogSizes 依原版大寫字高量起始字級 ⌊capH×4.4⌋（上限 30）與下限（起始的 2/3）；字高未知時用 30／20。
func dialogSizes(capH int) (start, floor int) {
	if capH <= 0 {
		return dialogFontPx, dialogFloorPx
	}
	start, floor = stringStartPx(capH)
	if start > dialogFontPx {
		return dialogFontPx, dialogFloorPx
	}
	return start, max(floor, dialogAtlasMin)
}

func (c *dialogCatalog) dialogMasks(zh string, w, h, capH int) (shadow, normal, accent *image.Alpha, size int) {
	glyphs, ok := dialogMarked(zh)
	if !ok || len(glyphs) == 0 {
		return nil, nil, nil, 0
	}
	start, floor := dialogSizes(capH)
	for size = start; size >= floor; size-- {
		f := c.fonts[size]
		if f == nil {
			return nil, nil, nil, 0
		}
		lines, ok := dialogWrap(glyphs, f, w-8)
		if !ok {
			continue
		}
		pitch := (dialogPitchAtPx*size + dialogFontPx/2) / dialogFontPx
		if 4+(len(lines)-1)*pitch+(f.cjkBottom-f.cjkTop)+4 > h {
			continue
		}
		rect := image.Rect(0, 0, w, h)
		shadow, normal, accent = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		for k, line := range lines {
			x, y := 4, 4+k*pitch-f.cjkTop
			for _, g := range line {
				a := f.glyphs[g.r]
				dialogBlit(normal, a, x, y)
				dialogBlit(shadow, a, x+4, y+4)
				if g.accent {
					dialogBlit(accent, a, x, y)
				}
				x += f.widths[g.r]
			}
		}
		return shadow, normal, accent, size
	}
	return nil, nil, nil, 0
}

func dialogBlit(dst, src *image.Alpha, x, y int) {
	for gy := 0; gy < src.Rect.Dy(); gy++ {
		for gx := 0; gx < src.Rect.Dx(); gx++ {
			v := src.Pix[gy*src.Stride+gx]
			if v == 0 || !image.Pt(x+gx, y+gy).In(dst.Rect) {
				continue
			}
			if i := dst.PixOffset(x+gx, y+gy); v > dst.Pix[i] {
				dst.Pix[i] = v
			}
		}
	}
}

// loadDialogAtlas 讀 tools/bake_dialog_atlas.py 的圖集並核對字型、語料與術語表雜湊。
func (c *dialogCatalog) loadDialogAtlas(b []byte, fontSHA string, bind map[string]string) string {
	fonts, reason := loadAtlasFonts(b, fontSHA, bind, dialogFontPx, dialogAtlasMin)
	if reason == "" {
		c.fonts = fonts
	}
	return reason
}

// loadAtlasFonts 讀字元圖集並核對字型、字級範圍與綁定雜湊（目標169：通用字串層共用）。
func loadAtlasFonts(b []byte, fontSHA string, bind map[string]string, px, floor int) (map[int]*dialogFont, string) {
	var atlas struct {
		Font  string            `json:"font_sha256"`
		Px    int               `json:"font_px"`
		Floor int               `json:"floor_px"`
		Bind  map[string]string `json:"bindings"`
		Sizes map[string]struct {
			Height    int `json:"height"`
			CJKTop    int `json:"cjk_ink_top"`
			CJKBottom int `json:"cjk_ink_bottom"`
			Glyphs    map[string]struct {
				W     int    `json:"w"`
				Alpha string `json:"alpha"`
			} `json:"glyphs"`
		} `json:"sizes"`
	}
	if json.Unmarshal(b, &atlas) != nil {
		return nil, "font-mask-unavailable"
	}
	if atlas.Font != fontSHA || atlas.Px != px || atlas.Floor != floor || len(atlas.Bind) != len(bind) {
		return nil, "font-binding-mismatch"
	}
	for k, v := range bind {
		if atlas.Bind[k] != v {
			return nil, "font-binding-mismatch"
		}
	}
	fonts := map[int]*dialogFont{}
	for size := floor; size <= px; size++ {
		src, ok := atlas.Sizes[strconv.Itoa(size)]
		if !ok || src.Height <= 0 || src.CJKBottom <= src.CJKTop {
			return nil, "font-mask-out-of-bounds"
		}
		f := &dialogFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, cjkTop: src.CJKTop, cjkBottom: src.CJKBottom}
		for k, g := range src.Glyphs {
			r := []rune(k)
			pix, err := base64.StdEncoding.DecodeString(g.Alpha)
			if len(r) != 1 || g.W <= 0 || err != nil || len(pix) != g.W*src.Height {
				return nil, "font-mask-out-of-bounds"
			}
			a := image.NewAlpha(image.Rect(0, 0, g.W, src.Height))
			copy(a.Pix, pix)
			f.glyphs[r[0]], f.widths[r[0]] = a, g.W
		}
		fonts[size] = f
	}
	return fonts, ""
}

// ---- 執行期狀態（規格035 覆蓋設計 1、2、5、7）----

type dialogRun struct {
	base          uint32
	readPos       int
	start, last   uint64
	chars         []dialogChar
	firstOld      map[int]byte
	lastText      map[int]bool
	shadowWritten bool
	others        image.Rectangle // 段內其他寫入者（游標除外）的範圍
	contig        bool            // 目標178：段內連續字串（停用項目）讀取中
	contigNext    uint32          // 連續字串下一個預期位址
}

type dialogShown struct {
	buildSource            []byte // 規格035 READY：來源畫布的建造標題快照，不替代VGA啟用快照。
	optionBody             []byte // 正文印完的原版安全區；只供同框選項識別，不寫回原版。
	id, zh, reason         string
	normalC, accentC       byte     // 目標166：原版觀測字色
	shadowC                byte     // 0 表示原版沒有陰影
	dimC                   byte     // 目標178：行色層的色號（停用項目）
	items                  []string // 目標178：逐行清單各行的原文（供普查逐行歸屬）
	safe                   image.Rectangle
	before                 []byte
	shadow, normal, accent *image.Alpha
	dim                    *image.Alpha // 目標178：主色號不是一般色也不是強調色的行；沒有這種行時為 nil
	size                   int
	phase                  string // waiting-screen、active、expired
	complete               uint64
	patch                  *overlay.Patch
	afterSafe              []byte
	appliedFrames          int
}

type dialogRuntime struct {
	readCanvas func() []byte // 規格035 READY：原版來源畫布只讀。
	cat        *dialogCatalog
	fontReason string
	run        *dialogRun
	cur        *dialogShown
	prev       *dialogShown // 目標172：與目前一段不重疊、先後印出的前一段（例如選單標題）
	accepted   int
	misses     map[string]int // 有陰影色但未能中文化的顯示字串與原因
	// 目標172：逐行清單的行查不到逐行模板時，改問規格038 字串層的字典與模板（對話框選項列、選單）。
	lineFallback   func(string) (string, bool)
	lineFallbackAt func(string, int) (string, bool) // 規格038 READY：只傳完整清單的來源列索引。
	slotFallback   func(string) (string, bool)
}

// fallbackLine 不向標籤或分欄回呼提供清單列身分。
func (d *dialogRuntime) fallbackLine(text string, lineIndex int) (string, bool) {
	if d.lineFallbackAt != nil {
		if zh, ok := d.lineFallbackAt(text, lineIndex); ok {
			return zh, true
		}
	}
	if d.lineFallback != nil {
		return d.lineFallback(text)
	}
	return "", false
}

const dialogGap = 20000 // 兩萬步內無讀取即視為一段結束（字距約 800～1,400 步、換行約 2,500 步）

// menuListNext 判斷段內連續字串的首字（已畫出）是否接在垂直清單的下一列：
// 左緣與上一行對齊（差 ≤1 邏輯像素）且在其下方（目標178，規格036 附記規則 1）。
func menuListNext(chars []dialogChar) bool {
	first := chars[len(chars)-1]
	if first.box.Empty() {
		return false
	}
	lines := runLines(chars[:len(chars)-1])
	if len(lines) == 0 {
		return false
	}
	last := lines[len(lines)-1]
	return abs(first.box.Min.X-last.box.Min.X) <= 1 && first.box.Min.Y > last.box.Min.Y
}

// menuPrefixNext 只暫留既有清單後的無墨跡熱鍵前綴；還不能據此啟用覆蓋。
func menuPrefixNext(chars []dialogChar, next byte) bool {
	if len(chars) < 3 || next < 'A' || (next > 'Z' && next < 'a') || next > 'z' {
		return false
	}
	first := chars[len(chars)-1]
	if first.c != '~' || !first.box.Empty() {
		return false
	}
	lines := runLines(chars[:len(chars)-1])
	if len(lines) < 2 {
		return compactOrdersPrefix(chars, next)
	}
	for i := 1; i < len(lines); i++ {
		if abs(lines[i].box.Min.X-lines[0].box.Min.X) > 1 {
			return false
		}
	}
	return true
}

// menuPrefixesValid 用真正字形確認暫留項目仍接在清單下一列。
func menuPrefixesValid(chars []dialogChar) bool {
	for i, ch := range chars {
		if !ch.prefixContinuation {
			continue
		}
		lines := runLines(chars[:i])
		if len(lines) < 2 && (i+1 >= len(chars) || !compactOrdersPrefix(chars[:i+1], chars[i+1].c)) {
			return false
		}
		var first image.Rectangle
		for _, next := range chars[i+1:] {
			if !next.contig {
				break
			}
			if !next.box.Empty() {
				first = next.box
				break
			}
		}
		last := lines[len(lines)-1].box
		if first.Empty() || abs(first.Min.X-last.Min.X) > 1 || first.Min.Y <= last.Min.Y {
			return false
		}
	}
	return true
}

// onRead 處理一次 0D21:00C6 讀取；若上一段已結束，先回傳該段供呼叫端收尾。
func (d *dialogRuntime) onRead(a uint32, v byte, step uint64) (finished *dialogRun) {
	if r := d.run; r != nil && (step-r.last < dialogGap || d.buildReadTransaction(r, step)) {
		// 原版F9直接返回，沒有讀base+1的0；只在下一字同基址重讀時補齊觀測配對。
		if !r.contig && r.readPos%2 == 1 && a == r.base && len(r.chars) > 0 && dialogNonprintingBullet(r.chars[len(r.chars)-1]) {
			r.readPos++
		}
		if r.contig && a == r.contigNext {
			r.last = step
			if v == 0 {
				r.contig = false
				if r.readPos%2 == 1 {
					r.readPos++
				}
			} else {
				r.chars = append(r.chars, dialogChar{c: v, contig: true})
				r.contigNext++
			}
			return nil
		}
		if !r.contig && r.readPos%2 == 1 && a == r.base+1 {
			if v != 0 {
				if len(r.chars) < 2 || (!menuListNext(r.chars) && !menuPrefixNext(r.chars, v)) {
					d.run = nil // 連續字串（狀態欄、選單列、殖民地畫面的數字），不是逐字對話
					return nil
				}
				// 目標178：段內已有完整項目時，基址後接非 0 位元組表示這一項是連續字串（選單的停用項目），
				// 屬於同一段；讀到 0 才結束，其後仍從基址重讀「字元、0」。
				r.chars[len(r.chars)-1].prefixContinuation = r.chars[len(r.chars)-1].box.Empty()
				r.contig, r.contigNext = true, a+1
				r.chars[len(r.chars)-1].contig = true
				r.chars = append(r.chars, dialogChar{c: v, contig: true})
				r.last = step
				return nil
			}
			r.readPos++
			r.last = step
			return nil
		}
		if !r.contig && r.readPos%2 == 0 && a == r.base {
			r.chars = append(r.chars, dialogChar{c: v})
			r.readPos++
			r.last = step
			return nil
		}
	}
	finished = d.run
	d.run = &dialogRun{base: a, readPos: 1, start: step, last: step, chars: []dialogChar{{c: v}},
		firstOld: map[int]byte{}, lastText: map[int]bool{}}
	return finished
}

// onWrite 記錄段內畫布寫入；text 表示寫入者為 0D21:012C，cursor 表示游標常式在游標附近。
func (d *dialogRuntime) onWrite(i int, old, value byte, text, cursor bool) {
	r := d.run
	if r == nil {
		return
	}
	x, y := i%320, i/320
	if text {
		if _, seen := r.firstOld[i]; !seen {
			r.firstOld[i] = old
		}
		r.lastText[i] = true
		if value == 47 || value == 128 {
			r.shadowWritten = true
		}
		if n := len(r.chars); n > 0 {
			ch := &r.chars[n-1]
			ch.box = ch.box.Union(image.Rect(x, y, x+1, y+1))
			if ch.colors == nil {
				ch.colors = map[byte]int{}
			}
			ch.colors[value]++
		}
		return
	}
	if !cursor {
		r.lastText[i] = false
		r.others = r.others.Union(image.Rect(x, y, x+1, y+1))
	}
}

// dialogLike 判斷一段逐字印字像不像等待玩家應答的訊息框：有陰影色，或在地圖區（頂列與右側狀態欄以外）十字以上。
// 只供真 GUI 自動應答與探勘使用，不影響覆蓋。
func (r *dialogRun) dialogLike() bool {
	var ink image.Rectangle
	n := 0
	for _, ch := range r.chars {
		if !ch.box.Empty() {
			ink = ink.Union(ch.box)
			if !ch.contig { // 目標178：併入的連續字串（例如殖民地畫面的數字與按鈕）不讓整段像訊息框
				n++
			}
		}
	}
	// 目標170：不再限制 x<240（港口說明框、訓練對話框延伸到右側）；狀態欄是連續字串，不經本判斷。
	return r.shadowWritten || (n >= 10 && ink.Min.Y > 8)
}

// scanDialogBox 掃描色號 0 的外框：左右框沿 (hx,hy) 所在列、上框取 [x0,x1) 各欄由 ty 往上的最常見列。
// 顧問肖像常壓在框的左上或上緣，所以呼叫端以最後一行（肖像下方）掃左右、以首行整段寬度掃上框。
func scanDialogBox(canvas []byte, hx, hy, x0, x1, ty int) (l, t, r int) {
	l, r = hx, hx
	for l > 0 && canvas[hy*320+l] != 0 {
		l--
	}
	for r < 319 && canvas[hy*320+r] != 0 {
		r++
	}
	count := map[int]int{}
	for x := max(x0, 0); x < min(x1, 320); x++ {
		y := ty
		for y > 0 && canvas[y*320+x] != 0 {
			y--
		}
		count[y]++
	}
	best := -1
	for y, n := range count {
		if best < 0 || n > count[best] || (n == count[best] && y > best) {
			best = y
		}
	}
	return l, max(best, 0), r
}

type runLine struct {
	text    string
	box     image.Rectangle
	capH    int             // 原版大寫字母與數字的最大墨跡高（邏輯像素），作為中文字級上限
	colors  map[byte]int    // 目標172：本行改色點的色號分布（選項列買不起的行為灰色）
	right   image.Rectangle // 目標172：「=」右對齊標記之後的墨跡（職業選單右欄）
	inRight bool
	// gapLeft 是行內出現大段無墨空隙或連續兩個以上空白（歐洲港口價格欄、建造清單成本欄）之前的正規化文字；
	// 此時 right 為空隙之後的墨跡。沒有空隙或已有「=」時為空。
	gapLeft string
	gapRaw  int
	// 目標174：本行第一個冒號（含）之前的文字與墨跡，輸入列（例如 `Name: Jamestown_`）只翻這段標籤。
	labelText string
	label     image.Rectangle
}

// lineGapPx 是判定行內右欄的最小無墨空隙（邏輯像素）；原版字間空白約 3～6 點。
const lineGapPx = 16

// runLines 依 x 回捲切行；空白沒有墨跡，歸入目前行。
func runLines(chars []dialogChar) []runLine {
	var out []runLine
	var cur runLine
	lastX := -1
	for _, ch := range chars {
		if !ch.box.Empty() {
			if lastX >= 0 && ch.box.Min.X < lastX {
				out = append(out, cur)
				cur = runLine{}
			}
			if !cur.inRight && !cur.box.Empty() && (ch.box.Min.X-cur.box.Max.X >= lineGapPx || strings.HasSuffix(cur.text, "  ")) {
				cur.inRight, cur.gapRaw = true, len(cur.text)+1
			}
			lastX = ch.box.Min.X
			cur.box = cur.box.Union(ch.box)
			if cur.inRight {
				cur.right = cur.right.Union(ch.box)
			}
			if cur.colors == nil {
				cur.colors = map[byte]int{}
			}
			for c, n := range ch.colors {
				cur.colors[c] += n
			}
			if (ch.c >= 'A' && ch.c <= 'Z') || (ch.c >= '0' && ch.c <= '9') {
				cur.capH = max(cur.capH, ch.box.Dy())
			}
		}
		if ch.c != 0 && !dialogHotkeyMark(ch) && !dialogNonprintingBullet(ch) {
			cur.text += string(rune(ch.c))
		}
		if ch.c == '=' {
			cur.inRight = true
		}
		if ch.c == ':' && cur.labelText == "" && !cur.box.Empty() {
			cur.labelText, cur.label = dialogNormalize(cur.text), cur.box
		}
	}
	if !cur.box.Empty() {
		out = append(out, cur)
	}
	// 目標177：同一段印字裡整份重畫（下拉選單反白移動時重印），位置與文字都相同的行只留第一次。
	uniq := out[:0]
	for _, l := range out {
		dup := false
		for _, u := range uniq {
			dup = dup || (u.box == l.box && u.text == l.text)
		}
		if !dup {
			uniq = append(uniq, l)
		}
	}
	out = uniq
	for i := range out {
		if g := out[i].gapRaw; g > 0 {
			out[i].gapLeft = dialogNormalize(out[i].text[:g-1])
		}
		out[i].text = dialogNormalize(out[i].text)
		if out[i].capH == 0 {
			out[i].capH = out[i].box.Dy()
		}
	}
	return out
}

// runStyle 由原版觀測色號決定中文字色：有陰影色 47／128 為木紋框配色；
// 否則以各字主色中最多者為一般色、其次為強調色，不畫陰影。
func runStyle(r *dialogRun) (normal, accent, shadow byte) {
	if r.shadowWritten {
		return 68, 149, 47
	}
	count := map[byte]int{}
	for _, ch := range r.chars {
		best, n := byte(0), -1
		for c, k := range ch.colors {
			if k > n || (k == n && c < best) {
				best, n = c, k
			}
		}
		if n > 0 {
			count[best]++
		}
	}
	first, second, n1, n2 := byte(0), byte(0), -1, -1
	for c, k := range count {
		switch {
		case k > n1 || (k == n1 && c < first):
			second, n2 = first, n1
			first, n1 = c, k
		case k > n2 || (k == n2 && c < second):
			second, n2 = c, k
		}
	}
	if n2 <= 0 {
		second = first
	}
	return first, second, 0
}

// observedPitch 取相鄰行上緣距離的最小值（邏輯像素）；單行時回傳 fallback。
func observedPitch(lines []runLine, fallback int) int {
	p := 0
	for i := 1; i < len(lines); i++ {
		if d := lines[i].box.Min.Y - lines[i-1].box.Min.Y; d > 0 && (p == 0 || d < p) {
			p = d
		}
	}
	if p == 0 {
		return fallback
	}
	return p
}

// 行色層（目標178，規格036 附記）。
const (
	layerNormal = iota // 一般色層（含整行強調層的行）
	layerDim           // 第三層，整行單色，不用熱鍵強調
)

// lineDominant 回傳一行的主色號與前景色數；木紋陰影47同時排除已驗下方陰影128。
// 其他陰影配色只排除指定色，同數取色號較小者。
func lineDominant(l runLine, shadowC byte) (dom byte, kinds int) {
	best := -1
	for c, n := range l.colors {
		if c == shadowC || (shadowC == 47 && c == 128) {
			continue
		}
		kinds++
		if n > best || (n == best && c < dom) {
			dom, best = c, n
		}
	}
	return dom, kinds
}

// lineRoles 決定逐行清單的強調色與各行所屬色層：
// 含兩種以上色號的行，其次要色號（合計最多者）是強調色，優先於全段字元主色統計；
// 主色號既不是一般色也不是強調色的行歸第三層，全段只允許一種第三色號。
func lineRoles(lines []runLine, normalC, accentC, shadowC byte) (accent, dimC byte, layers []int, why string) {
	accent = accentC
	minor := map[byte]int{}
	for _, l := range lines {
		dom, kinds := lineDominant(l, shadowC)
		if kinds < 2 {
			continue
		}
		for c, n := range l.colors {
			if c != shadowC && !(shadowC == 47 && c == 128) && c != dom {
				minor[c] += n
			}
		}
	}
	best := -1
	for c, n := range minor {
		if n > best || (n == best && c < accent) {
			accent, best = c, n
		}
	}
	layers = make([]int, len(lines))
	for i, l := range lines {
		dom, kinds := lineDominant(l, shadowC)
		if dom == normalC || (dom == accent && accent != 0 && accent != normalC) {
			continue
		}
		// 規格036 接手補審：第三層混色沒有原版證據，回原文。
		if kinds >= 2 {
			return accent, 0, nil, "line-colors"
		}
		if dimC != 0 && dimC != dom {
			return accent, 0, nil, "line-colors"
		}
		dimC = dom
		layers[i] = layerDim
	}
	return accent, dimC, layers, ""
}

// finish 對一段已結束的逐字事件做比對與版面；回傳要顯示的狀態，或原因（無墨跡時兩者皆空）。
func (d *dialogRuntime) finish(r *dialogRun, canvas []byte, step uint64) (*dialogShown, string, string) {
	if r == nil || r.readPos%2 == 1 {
		return nil, "", ""
	}
	if !menuPrefixesValid(r.chars) {
		return nil, dialogShownText(r.chars), "contiguous-prefix-layout"
	}
	lines := runLines(r.chars)
	if len(lines) == 0 {
		return nil, "", ""
	}
	// 目標178（規格036 附記規則 1）：段內併入連續字串時，各行必須左緣對齊（垂直清單）；
	// 否則是混合多個元件的畫面（例如殖民地畫面），靜默略過，由字串層各自處理。
	for _, ch := range r.chars {
		if ch.contig {
			for _, l := range lines[1:] {
				if abs(l.box.Min.X-lines[0].box.Min.X) > 1 {
					return nil, "", ""
				}
			}
			break
		}
	}
	var ink image.Rectangle
	first := -1
	for i, ch := range r.chars {
		if !ch.box.Empty() {
			ink = ink.Union(ch.box)
			if first < 0 {
				first = i
			}
		}
	}
	shown := dialogShownText(r.chars)
	slotList := d.slotListContext(len(lines))
	// 規格035：候選收尾前已被完全抹除，不把舊文字覆蓋到新畫面。
	if len(r.firstOld) > 0 {
		alive := false
		for _, text := range r.lastText {
			alive = alive || text
		}
		// 規格036：新前綴候選須完整存活，不能把關框後殘存的一點當成整份清單仍顯示。
		prefix, intact := false, true
		for _, ch := range r.chars {
			prefix = prefix || ch.prefixContinuation
		}
		if prefix || slotList {
			for i := range r.firstOld {
				intact = intact && r.lastText[i]
			}
		}
		if !alive || ((prefix || slotList) && !intact) {
			return nil, shown, "text-erased-before-finish"
		}
	}
	before := bytes.Clone(canvas)
	for i, text := range r.lastText {
		if text {
			before[i] = r.firstOld[i]
		}
	}
	normalC, accentC, shadowC := runStyle(r)
	if compactOrdersStyle(lines, canvas) {
		normalC, accentC, shadowC = 68, 149, 0
	}
	st := &dialogShown{before: before, normalC: normalC, accentC: accentC, shadowC: shadowC,
		phase: "waiting-screen", complete: step}
	t, zh, why := d.cat.matchIn(d.cat.templates, shown)
	if why == "no-template" && d.professionTitleContext(lines, normalC, accentC, shadowC) && d.lineFallback != nil {
		if value, ok := d.lineFallback(shown); ok {
			t, zh, why = &dialogTemplate{id: "STRING:profession-title"}, value, ""
		}
	}

	if why == "" && t.id == "GAME.TXT:0x000002C8" && !mapTitleContext(lines, normalC, accentC, shadowC) {
		return nil, shown, "map-title-geometry"
	}
	// 規格035 READY：完整四列仍有段落模板，來源與欄位符合時優先保留逐列語意。
	if len(lines) == 4 && d.portShipChoices(lines, canvas, step) != nil {
		t, zh, why = nil, "", "no-template"
	}
	switch {
	case why == "" && t.centered:
		// 置中段落（例如國王接見）：沒有色號 0 外框，安全區取原版墨跡外擴 2 邏輯像素。
		st.safe = ink.Inset(-2).Intersect(image.Rect(0, 0, 320, 200))
		st.shadow, st.normal, st.accent, st.size = d.cat.centeredMasks(zh, st.safe.Dx()*4, st.safe.Dy()*4,
			observedPitch(lines, 10)*4, shadowC != 0)
	case why == "":
		// 目標170：有色號 0 外框即可，不再要求陰影色（港口說明框、訓練對話框無陰影）。
		last := lines[len(lines)-1].box
		l, top, rt := scanDialogBox(before, last.Min.X, (last.Min.Y+last.Max.Y)/2, lines[0].box.Min.X, lines[0].box.Max.X, lines[0].box.Min.Y)
		st.safe = image.Rect(l+3, top+3, rt-3, ink.Max.Y+2)
		if l == 0 || top == 0 || rt == 319 || !ink.In(st.safe) {
			// 目標172：整句命中但沒有色號 0 外框（例如殖民地 BUY 說明框），改用無框段落版面：
			// 安全區為原版墨跡外擴 2 邏輯像素，依原版行距排版。
			st.safe = ink.Inset(-2).Intersect(image.Rect(0, 0, 320, 200))
			st.shadow, st.normal, st.accent, st.size = d.cat.centeredMasks(zh, st.safe.Dx()*4, st.safe.Dy()*4,
				observedPitch(lines, 10)*4, shadowC != 0)
			if st.size == 0 {
				return nil, shown, "layout-overflow"
			}
			st.id, st.zh = t.id, zh
			return st, shown, ""
		}
		// 規格035 READY：標題須從原版文字起點繪製，保留左側圖示與原版基線。
		if t.id == "GAME.TXT:@COLONYUNIT:0x00009A33" {
			st.safe.Min.X = max(st.safe.Min.X, ink.Min.X-1)
			st.safe.Min.Y = max(st.safe.Min.Y, ink.Min.Y-1)
		}
		// 目標167：印字期間其他寫入者（例如顧問肖像壓在框上）不撤銷；逐點以最後寫入者重建印前底圖，
		// 只還原最後由改色常式寫下的像素，肖像像素保留原版印後值。
		capH := 0
		for _, l := range lines {
			capH = max(capH, l.capH)
		}
		st.shadow, st.normal, st.accent, st.size = d.cat.dialogMasks(zh, st.safe.Dx()*4, st.safe.Dy()*4, capH)
		if st.shadow != nil && shadowC == 0 {
			st.shadow = image.NewAlpha(st.shadow.Rect) // 原版無陰影
		}
	case why == "no-template" && len(lines) == 1 && lines[0].labelText != "" && strings.HasSuffix(lines[0].text, "_"):
		// 目標174：輸入列＝標籤＋玩家輸入內容＋游標 `_`。只把標籤換成中文（逐行字典，其次字串層），
		// 右緣對齊原版標籤墨跡右緣；安全區只含標籤，輸入內容與游標保留原版像素。
		l := lines[0]
		_, lzh, lwhy := d.cat.matchIn(d.cat.lines, l.labelText)
		if lwhy != "" && d.lineFallback != nil {
			if z, ok := d.lineFallback(l.labelText); ok {
				lzh, lwhy = z, ""
			}
		}
		if lwhy != "" {
			return nil, shown, "input-label-" + lwhy
		}
		lab := runLine{box: l.label, right: l.label, capH: l.capH}
		st.safe = image.Rect(l.label.Min.X-1, l.label.Min.Y-1, l.label.Max.X+1, l.label.Max.Y+2).Intersect(image.Rect(0, 0, 320, 200))
		st.shadow, st.normal, st.accent, st.size = d.cat.lineMasks([]string{"\t" + lzh}, []runLine{lab}, st.safe,
			l.box.Dy()+3, shadowC != 0)
		if st.size == 0 {
			return nil, shown, "layout-overflow"
		}
		// 同一標籤在多個段落出現（新陸地、殖民地、改名），不以命中的譯稿列當鍵，免得歸錯段落。
		st.id, st.zh = "STRING:input-label", lzh
		return st, shown, ""
	case why == "no-template":
		// 逐行清單：每一行都必須各自唯一命中；任何一行不中即整段回原文。
		// 目標178：先決定強調色與各行色層（停用項目的第三色）。
		accentC, dimC, layers, rwhy := lineRoles(lines, normalC, accentC, shadowC)
		dockList := d.cat.observedDockOptions(lines)
		if group := d.portShipChoices(lines, canvas, step); group != nil {
			dockList = group
		}
		if dockList != nil && normalC == 68 && st.accentC == 149 && shadowC == 47 {
			// 規格035 READY：六個已驗字格／來源組合的68／149／47已直接量測。
			accentC, dimC, layers, rwhy = 149, 0, make([]int, len(lines)), ""
		} else {
			dockList = nil
		}

		if group, observedLayers, ok := d.cat.portDisabledDockOptions(lines, canvas, normalC, st.accentC, shadowC); ok {
			dockList, accentC, dimC, rwhy = group, 149, 8, ""
			layers = observedLayers
		}
		if rwhy != "" {
			return nil, shown, rwhy
		}
		st.accentC, st.dimC = accentC, dimC
		shipList := d.cat.observedShipOptions(lines)
		if shipList == nil {
			shipList = dockList
		}
		optionList, optionWhy, optionHandled := d.parentChoices(lines, canvas, step)
		if shipList == nil && optionHandled && optionWhy != "" {
			return nil, shown, optionWhy
		}
		voyageItems := d.voyagePortChoices(lines, canvas, step)
		if voyageItems == nil {
			voyageItems = d.onePortChoices(lines, canvas, step)
		}
		familyArea := image.Rectangle{}
		if voyageItems == nil {
			voyageItems, familyArea = d.tradeStartChoices(lines, canvas, step)
		}
		if voyageItems == nil {
			voyageItems, familyArea = d.familyPortChoices(lines, canvas, step)
		}
		captionItems, captionArea := d.unitCaptionChoices(lines, canvas)
		items := make([]string, len(lines))
		id := ""
		for i, l := range lines {
			var lt *dialogTemplate
			lzh, lwhy := "", "no-template"
			if slotList {
				if d.slotFallback == nil {
					return nil, shown, "slot-no-translation"
				}
				var ok bool
				lzh, ok = d.slotFallback(l.text)
				if !ok {
					return nil, shown, "slot-no-translation"
				}
				lwhy, id = "", "STRING:save-slot"
			} else if left, right, ok := strings.Cut(l.text, " = "); ok && !l.right.Empty() && d.lineFallback != nil {
				// 目標172：「=」是右對齊標記：左欄、右欄分別翻譯，以 \t 分隔交給 lineMasks 分欄排版。
				lz, ok1 := d.lineFallback(left)
				rz, ok2 := d.lineFallback(right)
				if !ok1 || !ok2 {
					return nil, shown, "line-no-template"
				}
				lzh, lwhy = lz+"\t"+rz, ""
			} else if l.gapLeft != "" && strings.HasPrefix(l.text, l.gapLeft) && d.lineFallback != nil {
				// 行內大段空隙（港口價格欄）：兩欄都命中才分欄；否則整行照舊翻譯。
				lz, ok1 := d.lineFallback(l.gapLeft)
				rz, ok2 := d.lineFallback(strings.TrimSpace(l.text[len(l.gapLeft):]))
				if ok1 && ok2 {
					lzh, lwhy = lz+"\t"+rz, ""
				}
			}
			if lwhy == "" {
				if id == "" {
					id = "STRING:line"
				}
			} else {
				if shipList != nil {
					lt, lzh, lwhy = d.cat.matchIn(shipList[i:i+1], l.text)
				} else if optionHandled {
					lt, lzh, lwhy = d.cat.matchIn(optionList[i:i+1], l.text)
				} else {
					lt, lzh, lwhy = d.cat.matchIn(d.cat.lines, l.text)
				}
				if lwhy != "" && (d.lineFallback != nil || d.lineFallbackAt != nil) {
					if zh, ok := d.fallbackLine(l.text, i); ok {
						lzh, lwhy, lt = zh, "", nil
						if id == "" {
							id = "STRING:line"
						}
					}
				}
			}
			if voyageItems != nil {
				lzh, lwhy, lt, id = voyageItems[i], "", nil, "STRING:voyage-ports"
			}
			if captionItems != nil {
				lzh, lwhy, lt, id = captionItems[i], "", nil, "STRING:unit-selection-caption"
			}
			if lwhy != "" {
				return nil, shown, "line-" + lwhy
			}
			items[i] = lzh
			// 目標172：本行主要色號是整段的第二色（例如買不起的灰色選項）時，整行用強調層（該色）畫。
			if layers[i] == layerNormal && accentC != 0 && accentC != normalC {
				if dom, _ := lineDominant(l, shadowC); dom == accentC && !strings.ContainsAny(lzh, "{}") {
					items[i] = "{" + strings.ReplaceAll(lzh, "\t", "}\t{") + "}"
				}
			}
			if lt != nil {
				t, id = lt, lt.id
			}
		}
		var union image.Rectangle
		for _, l := range lines {
			union = union.Union(l.box)
		}
		st.safe = image.Rect(union.Min.X-1, union.Min.Y-1, union.Max.X+2, union.Max.Y+2).Intersect(image.Rect(0, 0, 320, 200))
		if !familyArea.Empty() {
			st.safe = familyArea
		}
		if !captionArea.Empty() {
			st.safe = captionArea
		}
		// LOADGAME 標題下一列已是槽位反白邊緣，保留墨跡外一列即可。
		if len(lines) == 1 && id == "GAME.TXT:0x00000826" {
			st.safe.Max.Y = union.Max.Y + 1
		}
		st.shadow, st.normal, st.accent, st.dim, st.size = d.cat.lineLayerMasks(items, lines, st.safe,
			observedPitch(lines, union.Dy()+3), shadowC != 0, layers)
		if len(lines) == 1 {
			st.id = id
		} else {
			st.id = id + "+list"
		}
		// 規格035 READY：完整MENU不得由關框後的零星存活墨跡重新啟用。
		if strings.HasPrefix(st.id, "MENU.TXT:") {
			for index := range r.firstOld {
				if !r.lastText[index] {
					return nil, shown, "text-erased-before-finish"
				}
			}
		}
		st.zh = strings.Join(items, "／")
		st.items = make([]string, len(lines))
		for i, l := range lines {
			st.items[i] = l.text
		}
		if st.size == 0 {
			return nil, shown, "layout-overflow"
		}
		if st.id == "STRING:line" && len(st.items) == 1 && st.items[0] == "Select An Item To Build" {
			st.buildSource = rectBytes(canvas, st.safe)
		}
		return st, shown, ""
	default:
		return nil, shown, why
	}
	if st.size == 0 {
		return nil, shown, "layout-overflow"
	}
	st.id, st.zh = t.id, zh
	if len(d.cat.messageOptions[st.id]) > 0 && len(canvas) == 320*200 {
		st.optionBody = rectBytes(canvas, st.safe)
	}
	return st, shown, ""
}

// lineMasks 逐行在原位畫中文：行左緣對齊原版字首、字頭對齊原版行上緣；
// 中文墨跡高不超過原版大寫字墨跡高的 4 倍（逐段取最大者），也不超過行距；
// 寬度不得超過整段最右緣。任一行放不下即整段回原文。
func (c *dialogCatalog) lineMasks(items []string, lines []runLine, safe image.Rectangle, pitch int, shadow bool) (sh, n, ac *image.Alpha, size int) {
	sh, n, ac, _, size = c.lineLayerMasks(items, lines, safe, pitch, shadow, nil)
	return sh, n, ac, size
}

// lineLayerMasks 同 lineMasks；layers 依行指定色層（目標178）：第三層的行畫在 dm，
// layerDim 的行不畫強調字母。沒有第三層的行時 dm 為 nil。
func (c *dialogCatalog) lineLayerMasks(items []string, lines []runLine, safe image.Rectangle, pitch int, shadow bool, layers []int) (sh, n, ac, dm *image.Alpha, size int) {
	rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
	capH := 0
	for _, l := range lines {
		capH = max(capH, l.capH)
	}
	start, floor := dialogSizes(capH)
	for size = start; size >= floor; size-- {
		f := c.fonts[size]
		if f == nil || f.cjkBottom-f.cjkTop > pitch*4-4 || f.cjkBottom-f.cjkTop > capH*4 {
			continue
		}
		sh, n, ac, dm = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		usedDim := false
		ok := true
		for i, l := range lines {
			layer := layerNormal
			if i < len(layers) {
				layer = layers[i]
			}
			usedDim = usedDim || layer != layerNormal
			base := n
			if layer != layerNormal {
				base = dm
			}
			y := (l.box.Min.Y-safe.Min.Y)*4 - f.cjkTop
			// 目標172：含 \t 的項目分兩欄：左欄靠原版行左緣，右欄右緣對齊原版右欄墨跡右緣。
			cols := strings.SplitN(items[i], "\t", 2)
			leftEnd := 0
			for k, col := range cols {
				glyphs, good := dialogMarked(col)
				w := 0
				for _, g := range glyphs {
					gw, has := f.widths[g.r]
					if !has {
						good = false
						break
					}
					w += gw
				}
				x := (l.box.Min.X - safe.Min.X) * 4
				if k == 1 {
					x = (l.right.Max.X-safe.Min.X)*4 - w
				}
				if !good || x+w+4 > rect.Dx() || y+f.cjkBottom > rect.Dy() || x < leftEnd {
					ok = false
					break
				}
				for _, g := range glyphs {
					a := f.glyphs[g.r]
					dialogBlit(base, a, x, y)
					if shadow {
						dialogBlit(sh, a, x+4, y+4)
					}
					if g.accent && layer != layerDim {
						dialogBlit(ac, a, x, y)
					}
					x += f.widths[g.r]
				}
				leftEnd = x + 8
			}
			if !ok {
				break
			}
		}
		if ok {
			if !usedDim {
				dm = nil
			}
			return sh, n, ac, dm, size
		}
	}
	return nil, nil, nil, nil, 0
}

// centeredMasks 排版含 ^ 置中碼的譯稿：^^ 開頭的行置中、單獨的 ^ 為空行、其餘相鄰行合併後依寬度重排。
// 行距取原版觀測行距（輸出像素）；字級以行距為上限並逐級縮到下限。
func (c *dialogCatalog) centeredMasks(zh string, w, h, pitch int, shadow bool) (sh, n, ac *image.Alpha, size int) {
	type item struct {
		text     string
		centered bool
		blank    bool
	}
	var items []item
	body := ""
	flush := func() {
		if body != "" {
			items = append(items, item{text: body})
			body = ""
		}
	}
	for _, l := range strings.Split(zh, `\n`) {
		switch {
		case strings.HasPrefix(l, "^^"):
			flush()
			items = append(items, item{text: strings.TrimPrefix(l, "^^"), centered: true})
		case strings.TrimSpace(l) == "^":
			flush()
			items = append(items, item{blank: true})
		case strings.HasPrefix(l, "^"):
			// 目標171：單一 ^ 開頭的行自成一段（百科標題行 ^{CIGARS}、GAME.TXT ^Treasury:），其後的行另起段落。
			flush()
			items = append(items, item{text: strings.TrimPrefix(l, "^")})
		default:
			body += l
		}
	}
	flush()
	rect := image.Rect(0, 0, w, h)
	for size = dialogFontPx; size >= dialogFloorPx; size-- {
		f := c.fonts[size]
		if f == nil || f.cjkBottom-f.cjkTop > pitch-4 {
			continue
		}
		type placed struct {
			glyphs   []dialogGlyph
			centered bool
		}
		var rows []*placed
		ok := true
		for _, it := range items {
			if it.blank {
				rows = append(rows, nil)
				continue
			}
			glyphs, good := dialogMarked(it.text)
			if !good {
				return nil, nil, nil, 0
			}
			wrapped, good := dialogWrap(glyphs, f, w-8)
			if !good {
				ok = false
				break
			}
			for _, g := range wrapped {
				rows = append(rows, &placed{g, it.centered})
			}
		}
		if !ok || 4+len(rows)*pitch > h {
			continue
		}
		sh, n, ac = image.NewAlpha(rect), image.NewAlpha(rect), image.NewAlpha(rect)
		for k, row := range rows {
			if row == nil {
				continue
			}
			lw := 0
			for _, g := range row.glyphs {
				lw += f.widths[g.r]
			}
			x, y := 4, 4+k*pitch-f.cjkTop
			if row.centered {
				x = (w - lw) / 2
			}
			for _, g := range row.glyphs {
				a := f.glyphs[g.r]
				dialogBlit(n, a, x, y)
				if shadow {
					dialogBlit(sh, a, x+4, y+4)
				}
				if g.accent {
					dialogBlit(ac, a, x, y)
				}
				x += f.widths[g.r]
			}
		}
		return sh, n, ac, size
	}
	return nil, nil, nil, 0
}

func saveSlotTitle(st *dialogShown) bool {
	return st != nil && (st.phase == "waiting-screen" || st.phase == "active") && (st.id == "GAME.TXT:0x00000826" || st.id == "GAME.TXT:0x0000078E")
}

func (d *dialogRuntime) slotListContext(rows int) bool {
	if rows != 8 && rows != 10 {
		return false
	}
	return saveSlotTitle(d.cur) || (d.cur != nil && d.cur.id == "STRING:save-slot+list" && (d.cur.phase == "waiting-screen" || d.cur.phase == "active") && saveSlotTitle(d.prev))
}

// 自己的槽位清單重印時，標題仍須逐像素完全相同；不延長其他對話框。
func (d *dialogRuntime) retainSlotTitle(st *dialogShown, canvas []byte) bool {
	return st != nil && st.id == "STRING:save-slot+list" && d.cur != nil && d.cur.id == st.id && saveSlotTitle(d.prev) && d.prev.phase == "active" && !d.prev.safe.Overlaps(st.safe) && bytes.Equal(stringRect(canvas, d.prev.safe), d.prev.afterSafe)
}

// 規格035 READY：只保留讀檔錯誤框外仍可見、來源已核對的槽位標題。
func (d *dialogRuntime) titleForLoadError(next *dialogShown, canvas []byte) *dialogShown {
	if next == nil || (next.id != "GAME.TXT:0x00000971" && next.id != "GAME.TXT:0x0000088B" && next.id != "GAME.TXT:0x000008C7" && next.id != "GAME.TXT:@LOADSIZE:0x00000904") || len(canvas) != 64000 {
		return nil
	}
	for _, title := range []*dialogShown{d.cur, d.prev} {
		if saveSlotTitle(title) && title.phase == "active" && next.complete >= title.complete && !title.safe.Overlaps(next.safe) && len(title.afterSafe) == title.safe.Dx()*title.safe.Dy() && bytes.Equal(stringRect(canvas, title.safe), title.afterSafe) {
			return title
		}
	}
	return nil
}

// 規格035 READY：只取原版UNIT資料列的名稱欄，不解讀數值或遊戲規則。
func (c *dialogCatalog) bindUnitCaptionNames(corpus, source []byte) bool {
	c.unitCaptionNames = nil
	const expected = "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061"
	if fmt.Sprintf("%x", sha256.Sum256(source)) != expected {
		return false
	}
	marker := []byte("@UNIT\r\n")
	if bytes.Count(source, marker) != 1 {
		return false
	}
	start := bytes.Index(source, marker) + len(marker)
	stop := len(source)
	if n := bytes.Index(source[start:], []byte("\r\n@")); n >= 0 {
		stop = start + n + 2
	}
	spans := map[int]int{}
	for pos := start; pos < stop; {
		end := stop
		if n := bytes.IndexByte(source[pos:stop], '\n'); n >= 0 {
			end = pos + n
		}
		lineEnd := end
		if lineEnd > pos && source[lineEnd-1] == '\r' {
			lineEnd--
		}
		if bytes.Contains(source[pos:lineEnd], []byte(",")) {
			spans[pos] = lineEnd - pos
		}
		pos = end + 1
	}
	rows := splitTSV(corpus)
	if rows == nil {
		return false
	}
	values := map[string]string{}
	for _, row := range rows {
		if row["source_file"] != "NAMES.TXT" || !strings.HasPrefix(row["message_id"], "NAMES.TXT:@UNIT:") {
			continue
		}
		off, e1 := strconv.ParseInt(row["text_offset"], 0, 64)
		n, e2 := strconv.Atoi(row["text_byte_length"])
		if e1 != nil || e2 != nil || off < 0 || n <= 0 || int(off)+n > len(source) || spans[int(off)] != n || row["source_file_sha256"] != expected {
			return false
		}
		raw := source[int(off) : int(off)+n]
		if fmt.Sprintf("%x", sha256.Sum256(raw)) != row["source_bytes_sha256"] {
			return false
		}
		en, zh := strings.Split(string(raw), ","), strings.Split(row["zh_hant"], ",")
		if len(en) != len(zh) || len(en) < 2 {
			return false
		}
		key, value := dialogNormalize(en[0]), strings.TrimSpace(zh[0])
		if key == "" || value == "" || strings.ContainsAny(value, "{}%\r\n\t") {
			return false
		}
		if old, ok := values[key]; ok && old != value {
			values[key] = ""
		} else if !ok {
			values[key] = value
		}
	}
	if len(values) == 0 {
		return false
	}
	for pos, n := range spans {
		key := dialogNormalize(strings.SplitN(string(source[pos:pos+n]), ",", 2)[0])
		if _, exists := values[key]; exists {
			continue
		}
		value := c.terms[key]
		if c.canon[key] && value != "" && !strings.ContainsAny(value, "{}%\r\n\t") {
			values[key] = value
		}
	}
	c.unitCaptionNames = values
	return true
}

// 規格036 READY：只接受正常觀測的三種完整列組合，保持船隻及士兵來源獨立。
func (c *dialogCatalog) observedShipOptions(lines []runLine) []dialogTemplate {
	groups := append([][]dialogTemplate{c.shipOptions}, c.shipOptionSets...)
	for _, group := range groups {
		if len(group) == 0 || len(group) != len(lines) {
			continue
		}
		matched := true
		for i, l := range lines {
			if _, _, why := c.matchIn(group[i:i+1], l.text); why != "" {
				matched = false
				break
			}
		}
		if matched {
			return group
		}
	}
	return nil
}

func (c *dialogCatalog) matchesObservedShip(lines []runLine) bool {
	return c.observedShipOptions(lines) != nil
}

// 規格035 READY：字格、色層、整份六列和來源模板皆須符合。

func (c *dialogCatalog) observedDockOptions(lines []runLine) []dialogTemplate {
	return c.observedDockOptionColors(lines, 0)
}

func (c *dialogCatalog) observedDockOptionColors(lines []runLine, dim byte) []dialogTemplate {
	for _, group := range append([][]dialogTemplate{c.dockOptions}, c.dockOptionSets...) {
		if len(group) != len(lines) || len(group) == 0 {
			continue
		}
		y0 := 0
		switch len(lines) {
		case 7:
			y0 = 67
		case 6:
			y0 = 73
		case 4:
			y0 = 85
		case 3:
			y0 = 91
		default:
			continue
		}
		matched := true
		for i, l := range lines {
			if l.box.Min != image.Pt(82, y0+i*12) || l.capH != 8 || l.box.Max.X > 234 || l.box.Max.Y > y0+i*12+9 {
				matched = false
				break
			}
			for color := range l.colors {
				if color != 68 && color != 149 && color != 47 && color != 128 && !(dim != 0 && color == dim) {
					matched = false
				}
			}
			if _, _, why := c.matchIn(group[i:i+1], l.text); why != "" {
				matched = false
				break
			}
		}
		if matched {
			return group
		}
	}
	return nil
}

// 規格035 READY：只按六列碼頭裝備欄的原版色辨識灰層，不改可選性或價格。
func (c *dialogCatalog) portDisabledDockOptions(lines []runLine, canvas []byte, normal, accent, shadow byte) ([]dialogTemplate, []int, bool) {
	if len(lines) != 6 || normal != 68 || accent != 149 || shadow != 47 || !portScene(canvas) {
		return nil, nil, false
	}
	layers := make([]int, len(lines))
	for i, line := range lines {
		dom, kinds := lineDominant(line, shadow)
		if dom == 8 {
			if i < 1 || i > 3 || kinds != 1 {
				return nil, nil, false
			}
			layers[i] = layerDim
		} else if (dom != 68 && dom != 149) || line.colors[8] != 0 {
			return nil, nil, false
		}
	}
	group := c.observedDockOptionColors(lines, 8)
	return group, layers, group != nil
}

// 規格036 READY：完整選項僅借同一原版框內且未改印的已辨識正文。
func (d *dialogRuntime) parentChoices(lines []runLine, canvas []byte, step uint64) ([]dialogTemplate, string, bool) {
	if len(lines) == 0 || len(canvas) != 320*200 {
		return nil, "", false
	}
	first, last := lines[0].box, lines[len(lines)-1].box
	l, top, rt := scanDialogBox(canvas, last.Min.X, (last.Min.Y+last.Max.Y)/2, first.Min.X, first.Max.X, first.Min.Y)
	if l == 0 || top == 0 || rt == 319 {
		return nil, "", false
	}
	var selected []dialogTemplate
	for _, body := range []*dialogShown{d.cur, d.prev} {
		if body == nil || (body.phase != "active" && body.phase != "waiting-screen") || step < body.complete || step-body.complete >= 2000000 {
			continue
		}
		group := d.cat.messageOptions[body.id]
		if len(group) == 0 || len(body.optionBody) != body.safe.Dx()*body.safe.Dy() || !bytes.Equal(body.optionBody, rectBytes(canvas, body.safe)) {
			continue
		}
		if body.safe.Min.X != l+3 || body.safe.Max.X != rt-3 || body.safe.Min.Y != top+3 || first.Min.Y < body.safe.Max.Y {
			continue
		}
		fits := true
		for _, line := range lines {
			fits = fits && line.box.Min.X >= body.safe.Min.X && line.box.Max.X <= body.safe.Max.X
		}
		if !fits {
			continue
		}
		if selected != nil {
			return nil, "option-body-not-unique", true
		}
		selected = group
	}
	if selected == nil {
		return nil, "", false
	}
	if len(selected) != len(lines) {
		return nil, "option-count-mismatch", true
	}
	for i, line := range lines {
		if _, _, why := d.cat.matchIn(selected[i:i+1], line.text); why != "" {
			return nil, "option-" + why, true
		}
	}
	return selected, "", true
}

// 規格035 READY：固定港口畫面、完整三列與正文印後像素共同確認選項身分。
func (d *dialogRuntime) portShipChoices(lines []runLine, canvas []byte, step uint64) []dialogTemplate {
	if (len(lines) != 3 && len(lines) != 4) || len(d.cat.portShipOptions) != 4 || !portScene(canvas) {
		return nil
	}
	group, y0, right := d.cat.portShipOptions, 85, []int{145, 205, 159, 136}
	if len(lines) == 3 {
		group, y0, right = []dialogTemplate{group[0], group[1], group[3]}, 91, []int{145, 205, 136}
	}
	for i, line := range lines {
		if line.capH != 8 || line.box != image.Rect(82, y0+12*i, right[i], y0+12*i+9) {
			return nil
		}
		if _, _, why := d.cat.matchIn(group[i:i+1], line.text); why != "" {
			return nil
		}
	}
	for _, body := range []*dialogShown{d.cur, d.prev} {
		if body != nil && body.id == "GAME.TXT:@EUROPESHIPCLICK:0x00009874" &&
			(body.phase == "active" || body.phase == "waiting-screen") && body.safe == image.Rect(63, y0-17, 265, y0-3) &&
			step >= body.complete && step-body.complete < 2000000 &&
			len(body.optionBody) == body.safe.Dx()*body.safe.Dy() && bytes.Equal(body.optionBody, rectBytes(canvas, body.safe)) {
			return group
		}
	}
	return nil
}

// 規格048 READY：相同選項重繪時保留像素完整且身份已核對的正文。
func (d *dialogRuntime) retainChoiceBody(next *dialogShown, canvas []byte) bool {
	body, old := d.prev, d.cur
	if body == nil || old == nil || next == nil || body.phase != "active" ||
		next.id != old.id || next.safe != old.safe || body.safe.Overlaps(next.safe) ||
		next.complete < old.complete || len(canvas) != 320*200 ||
		len(body.afterSafe) != body.safe.Dx()*body.safe.Dy() ||
		!bytes.Equal(body.afterSafe, rectBytes(canvas, body.safe)) {
		return false
	}
	group := d.cat.messageOptions[body.id]
	if body.id == "GAME.TXT:@EUROPESHIPCLICK:0x00009874" && len(group) == 4 && len(next.items) == 3 {
		group = []dialogTemplate{group[0], group[1], group[3]}
	}
	if len(group) == 0 || len(next.items) != len(group) || len(old.items) != len(group) {
		return false
	}
	for i, item := range next.items {
		if item != old.items[i] {
			return false
		}
		if _, _, why := d.cat.matchIn(group[i:i+1], item); why != "" {
			return false
		}
	}
	return true
}

// 規格035／038 READY：正常G兩列清單與原版標題像素守門。
func (d *dialogRuntime) voyagePortChoices(lines []runLine, canvas []byte, step uint64) []string {
	if len(lines) != 2 || len(canvas) != 64000 || d.lineFallback == nil {
		return nil
	}
	if lines[0].text != "London (England)" || lines[0].capH != 8 || lines[0].box != image.Rect(77, 97, 155, 106) ||
		lines[1].text != "Jamestown" || lines[1].capH != 8 || lines[1].box != image.Rect(77, 109, 127, 118) {
		return nil
	}
	for i, l := range lines {
		dom, _ := lineDominant(l, 47)
		if (i == 0 && dom != 68) || (i == 1 && dom != 68 && dom != 8) {
			return nil
		}
		for c := range l.colors {
			if c != dom && c != 47 && c != 128 {
				return nil
			}
		}
	}
	safe := image.Rect(66, 82, 176, 94)
	for _, title := range []*dialogShown{d.cur, d.prev} {
		if title == nil || title.id != "GAME.TXT:0x00001CBB" || title.safe != safe || title.size != 30 ||
			(title.phase != "active" && title.phase != "waiting-screen") || step < title.complete || step-title.complete >= 2000000 ||
			len(title.items) != 1 || title.items[0] != "Select a port to sail to:" {
			continue
		}
		if fmt.Sprintf("%x", sha256.Sum256(rectBytes(canvas, safe))) != "243bbad99dab8e3b061f63862dd8765c1b1b24a364c674fabf47b1aab849c2af" {
			continue
		}
		port, pok := d.lineFallback("London")
		country, cok := d.lineFallback("England")
		colony, jok := d.lineFallback("Jamestown")
		if !pok || !cok || !jok {
			return nil
		}
		return []string{port + "（" + country + "）", colony}
	}
	return nil
}

// 規格035 READY：完整兩行職業標題依同欄字格分流，整則模板由字串層驗證。
func (d *dialogRuntime) professionTitleContext(lines []runLine, n, a, sh byte) bool {
	if len(lines) != 2 || n != 68 || a != 68 || sh != 0 {
		return false
	}
	for i, line := range lines {
		if line.capH != 5 || line.box.Min != image.Pt(67, 19+i*6) || line.box.Max.Y != 25+i*6 || line.box.Max.X <= 67 || line.box.Max.X > 254 || len(line.colors) != 1 || line.colors[68] == 0 {
			return false
		}
	}
	shown := dialogNormalize(lines[0].text + " " + lines[1].text)
	const prefix = "Select a Profession for "
	if !strings.HasPrefix(shown, prefix) || !strings.HasSuffix(shown, "):") || strings.Count(shown, "(") != 1 || strings.Count(shown, ")") != 1 {
		return false
	}
	body := strings.TrimPrefix(shown, prefix)
	split := strings.IndexByte(body, '(')
	return split > 0 && strings.TrimSpace(body[:split]) != "" && strings.TrimSpace(body[split+1:len(body)-2]) != ""
}

func mapTitleContext(lines []runLine, n, a, sh byte) bool {
	if len(lines) != 1 || n != 68 || a != 149 || sh != 47 {
		return false
	}
	line := lines[0]
	if line.text != "Select Map File to Load" || line.box != image.Rect(108, 89, 212, 98) || line.capH != 8 || len(line.colors) != 3 || line.colors[68] <= 0 || line.colors[47] <= 0 || line.colors[128] <= 0 {
		return false
	}
	return true
}

func (d *dialogRuntime) retainBuildTitle(next *dialogShown, canvas []byte) bool {
	title, old := d.prev, d.cur
	if title == nil || old == nil || next == nil || title.id != "STRING:line" || title.phase != "active" || (title.safe != image.Rect(74, 45, 154, 54) && title.safe != image.Rect(74, 33, 154, 42)) || title.size != 21 || len(title.items) != 1 || title.items[0] != "Select An Item To Build" || len(canvas) != 64000 || len(title.afterSafe) != 720 || !bytes.Equal(title.afterSafe, rectBytes(canvas, title.safe)) {
		return false
	}
	if old.id != "STRING:line+list" || next.id != old.id || next.safe != old.safe || next.safe.Min.X != 78 || next.safe.Max.X != 241 || next.safe.Min.Y != title.safe.Max.Y+1 || next.safe.Dy() != len(next.items)*8 || next.size != 21 || title.safe.Overlaps(next.safe) || next.complete < old.complete || len(old.items) < 2 || len(old.items) != len(next.items) || next.safe.Max.Y > 171 {
		return false
	}
	for i, item := range next.items {
		if item != old.items[i] {
			return false
		}
	}
	return next.items[0] == "(No Production)" && next.items[len(next.items)-1] == "WAGON TRAIN (40 Hammers)"
}

func (d *dialogRuntime) onePortChoices(lines []runLine, canvas []byte, step uint64) []string {
	if len(lines) != 1 || len(canvas) != 64000 || d.lineFallback == nil || d.cat == nil {
		return nil
	}
	l := lines[0]
	if l.capH != 8 || l.box.Min != image.Pt(77, 103) || l.box.Max.Y != 112 || l.box.Max.X > 254 {
		return nil
	}
	dom, _ := lineDominant(l, 47)
	if dom != 68 {
		return nil
	}
	for color := range l.colors {
		if color != 68 && color != 47 && color != 128 {
			return nil
		}
	}
	safe := image.Rect(66, 88, 176, 100)
	found := false
	for _, title := range []*dialogShown{d.cur, d.prev} {
		if title == nil || title.id != "GAME.TXT:0x00001CBB" || title.safe != safe || title.size != 30 || (title.phase != "active" && title.phase != "waiting-screen") || step < title.complete || step-title.complete >= 2000000 || len(title.items) != 1 || title.items[0] != "Select a port to sail to:" {
			continue
		}
		if fmt.Sprintf("%x", sha256.Sum256(rectBytes(canvas, safe))) == "243bbad99dab8e3b061f63862dd8765c1b1b24a364c674fabf47b1aab849c2af" {
			found = true
		}
	}
	if !found {
		return nil
	}
	port, rest, ok := strings.Cut(l.text, " (")
	if !ok || !strings.HasSuffix(rest, ")") {
		return nil
	}
	country := strings.TrimSuffix(rest, ")")
	if !d.cat.voyageRoles["port"][port] || !d.cat.voyageRoles["country"][country] {
		return nil
	}
	p, pok := d.lineFallback(port)
	c, cok := d.lineFallback(country)
	if !pok || !cok {
		return nil
	}
	return []string{p + "（" + c + "）"}
}

// 規格035 READY：正常TRADESTART的一個Jamestown選項，依完整原版內框排版。
func (d *dialogRuntime) tradeStartChoices(lines []runLine, canvas []byte, step uint64) ([]string, image.Rectangle) {
	no := image.Rectangle{}
	if d.cat == nil || d.cat.colonyValue == nil || len(lines) != 1 || len(canvas) != 64000 {
		return nil, no
	}
	line := lines[0]
	if line.text != "Jamestown" || line.box != image.Rect(77, 103, 127, 112) || line.capH != 8 {
		return nil, no
	}
	if dom, _ := lineDominant(line, 47); dom != 68 {
		return nil, no
	}
	for color := range line.colors {
		if color != 68 && color != 47 && color != 128 {
			return nil, no
		}
	}
	left, top, right := scanDialogBox(canvas, 77, 107, 77, 127, 103)
	if left != 62 || top != 83 || right != 257 {
		return nil, no
	}
	for _, title := range []*dialogShown{d.cur, d.prev} {
		if title == nil || title.id != "GAME.TXT:@TRADESTART:0x00008390" || title.safe != image.Rect(65, 86, 254, 100) || title.size != 30 || (title.phase != "active" && title.phase != "waiting-screen") || step < title.complete || step-title.complete >= 2000000 || len(title.items) != 0 {
			continue
		}
		digest := fmt.Sprintf("%x", sha256.Sum256(rectBytes(canvas, title.safe)))
		if digest != "d92e03cf4309db02c1a6a5ed417be009b17af97534757f8b2206daaf316fcdb6" && digest != "f3903c8fd43c9bda810654eda5e24304db5ecf164850eb754b99cc24b2df7f16" {
			continue
		}
		value := d.cat.colonyValue(line.text)
		if value == "" || strings.ContainsAny(value, "{}\r\n\t") {
			return nil, no
		}
		return []string{value}, image.Rect(76, 102, right-3, 114)
	}
	return nil, no
}

// 規格035 READY：讀當次列位置與原版內框，不推算或改動目的地數。
func (d *dialogRuntime) familyPortChoices(lines []runLine, canvas []byte, step uint64) ([]string, image.Rectangle) {
	no := image.Rectangle{}
	if len(lines) < 2 || len(canvas) != 64000 || d.cat == nil || d.cat.colonyValue == nil || d.lineFallback == nil {
		return nil, no
	}
	first, last := lines[0].box, lines[len(lines)-1].box
	left, top, right := scanDialogBox(canvas, last.Min.X, (last.Min.Y+last.Max.Y)/2, first.Min.X, first.Max.X, first.Min.Y)
	if left != 62 || right != 257 {
		return nil, no
	}
	found := false
	for _, title := range []*dialogShown{d.cur, d.prev} {
		if title == nil || title.id != "GAME.TXT:0x00001CBB" || title.safe.Min.X != 66 || title.safe.Max.X != 176 || title.safe.Dy() != 12 || title.size != 30 || (title.phase != "active" && title.phase != "waiting-screen") || step < title.complete || step-title.complete >= 2000000 || len(title.items) != 1 || title.items[0] != "Select a port to sail to:" || top != title.safe.Min.Y-5 || first.Min.Y != title.safe.Max.Y+3 {
			continue
		}
		if fmt.Sprintf("%x", sha256.Sum256(rectBytes(canvas, title.safe))) == "243bbad99dab8e3b061f63862dd8765c1b1b24a364c674fabf47b1aab849c2af" {
			found = true
		}
	}
	if !found {
		return nil, no
	}
	var union image.Rectangle
	for i, line := range lines {
		if line.box.Min.X != 77 || line.box.Min.Y != first.Min.Y+i*12 || line.box.Dy() != 9 || line.box.Max.X <= 77 || line.box.Max.X > right-3 || (i == 0 && line.capH != 8) || (i > 0 && line.capH != 8 && line.capH != 9) {
			return nil, no
		}
		dom, _ := lineDominant(line, 47)
		if dom != 68 && dom != 8 {
			return nil, no
		}
		for color := range line.colors {
			if color != dom && color != 47 && color != 128 {
				return nil, no
			}
		}
		union = union.Union(line.box)
	}
	area := image.Rect(union.Min.X-1, union.Min.Y-1, right-3, union.Max.Y+2)
	if !area.In(image.Rect(0, 0, 320, 200)) {
		return nil, no
	}
	port, rest, ok := strings.Cut(lines[0].text, " (")
	if !ok || !strings.HasSuffix(rest, ")") {
		return nil, no
	}
	country := strings.TrimSuffix(rest, ")")
	if !d.cat.voyageRoles["port"][port] || !d.cat.voyageRoles["country"][country] {
		return nil, no
	}
	p, pok := d.lineFallback(port)
	c, cok := d.lineFallback(country)
	if !pok || !cok {
		return nil, no
	}
	items := []string{p + "（" + c + "）"}
	for offset, line := range lines[1:] {
		name := line.text
		if name == "" || name != strings.TrimSpace(name) || strings.ContainsAny(name, "{}\r\n\t") {
			return nil, no
		}
		value := d.cat.colonyValue(name)
		if name == "(Delete Destination)" {
			if len(lines) != 3 || offset != 1 || d.cat.routeDeleteChoice == "" {
				return nil, no
			}
			value = d.cat.routeDeleteChoice
		}
		if value == "" || strings.ContainsAny(value, "{}\r\n\t") {
			return nil, no
		}
		items = append(items, value)
	}
	return items, area
}

// 規格035 READY：既有標題身份與原版快照完整，來源仍為同一建造清單時，不以字間停頓拆散事務。
func (d *dialogRuntime) buildReadTransaction(r *dialogRun, step uint64) bool {
	if r == nil || d.readCanvas == nil || step < r.last || step < r.start || step-r.start >= 2000000 {
		return false
	}
	canvas := d.readCanvas()
	if len(canvas) != 64000 {
		return false
	}
	var title *dialogShown
	for _, it := range []*dialogShown{d.cur, d.prev} {
		if it == nil || it.id != "STRING:line" || len(it.items) != 1 || it.items[0] != "Select An Item To Build" || it.size != 21 || (it.phase != "active" && it.phase != "waiting-screen") || step < it.complete {
			continue
		}
		if it.safe != image.Rect(74, 33, 154, 42) && it.safe != image.Rect(74, 45, 154, 54) {
			continue
		}
		if len(it.buildSource) != it.safe.Dx()*it.safe.Dy() || !bytes.Equal(it.buildSource, rectBytes(canvas, it.safe)) {
			continue
		}
		if title != nil {
			return false
		}
		title = it
	}
	if title == nil {
		return false
	}
	lines := runLines(r.chars)
	if len(lines) == 0 || !strings.HasPrefix("(No Production)", lines[0].text) {
		return false
	}
	for i, line := range lines {
		if i > 0 && lines[0].text != "(No Production)" {
			return false
		}
		if line.box.Min.X < 79 || line.box.Min.X > 80 || line.box.Max.X > 241 || line.box.Min.Y != title.safe.Max.Y+2+8*i || line.box.Max.Y > line.box.Min.Y+6 || line.capH != 5 {
			return false
		}
		for color := range line.colors {
			if color != 68 && color != 149 && color != 8 {
				return false
			}
		}
	}
	return true
}

// 規格035 READY：原版國籍／UNIT名稱與LABELS字面值組成的肖像標籤。
func (d *dialogRuntime) unitCaptionChoices(lines []runLine, canvas []byte) ([]string, image.Rectangle) {
	no := image.Rectangle{}
	if d == nil || d.cat == nil || d.lineFallback == nil || len(lines) == 0 || len(canvas) != 64000 || len(d.cat.unitCaptionNames) == 0 {
		return nil, no
	}
	values := make([]string, len(lines))
	frames := make([]image.Rectangle, len(lines))
	var ink image.Rectangle
	for i, line := range lines {
		if line.capH != 8 || line.box.Dy() != 9 || !line.box.In(image.Rect(22, 6, 318, 187)) {
			return nil, no
		}
		for color := range line.colors {
			if color != 68 && color != 47 && color != 128 {
				return nil, no
			}
		}
		if dom, kinds := lineDominant(line, 47); dom != 68 || kinds != 1 {
			return nil, no
		}
		frame := image.Rect(line.box.Min.X-21, line.box.Min.Y-5, line.box.Min.X-3, line.box.Min.Y+13)
		for x := frame.Min.X; x < frame.Max.X; x++ {
			if canvas[frame.Min.Y*320+x] != 15 || canvas[(frame.Max.Y-1)*320+x] != 15 {
				return nil, no
			}
		}
		for y := frame.Min.Y; y < frame.Max.Y; y++ {
			if canvas[y*320+frame.Min.X] != 15 || canvas[y*320+frame.Max.X-1] != 15 {
				return nil, no
			}
		}
		head, tail, ok := strings.Cut(line.text, " (")
		if !ok || !strings.HasSuffix(tail, ")") {
			return nil, no
		}
		qualifier := strings.TrimSuffix(tail, ")")
		if qualifier != "None" && qualifier != "Expert" {
			return nil, no
		}
		nation, unit, ok := strings.Cut(head, " ")
		if !ok || !d.cat.voyageRoles["nation"][nation] {
			return nil, no
		}
		noun := d.cat.unitCaptionNames[unit]
		if noun == "" {
			return nil, no
		}
		country, ok1 := d.lineFallback(nation)
		status, ok2 := d.lineFallback(qualifier)
		if !ok1 || !ok2 || strings.ContainsAny(country+noun+status, "{}%\r\n\t") {
			return nil, no
		}
		values[i] = country + noun + "（" + status + "）"
		frames[i] = frame
		ink = ink.Union(line.box)
	}
	area := image.Rect(ink.Min.X-1, ink.Min.Y-1, ink.Max.X+2, ink.Max.Y+2)
	for _, frame := range frames {
		if frame.Overlaps(area) {
			return nil, no
		}
	}
	return values, area
}

func compactOrdersPrefix(chars []dialogChar, next byte) bool {
	if next != 'W' || len(chars) < 2 {
		return false
	}
	prefix := chars[len(chars)-1]
	if prefix.c != '~' || !prefix.box.Empty() {
		return false
	}
	lines := runLines(chars[:len(chars)-1])
	if len(lines) != 1 {
		return false
	}
	line := lines[0]
	if line.text != "Activate unit" || line.box != image.Rect(81, 13, 123, 19) || line.capH != 5 {
		return false
	}
	if len(line.colors) != 2 || line.colors[68] == 0 || line.colors[149] == 0 {
		return false
	}
	return true
}

func compactOrdersStyle(lines []runLine, canvas []byte) bool {
	if len(lines) != 6 || len(canvas) != 64000 {
		return false
	}
	texts := []string{"Activate unit", "Wait for next unit", "Fortify", "Sentry", "No Orders (space bar)", "Disband Unit (shift-D)"}
	boxes := []image.Rectangle{image.Rect(81, 13, 123, 19), image.Rect(81, 21, 141, 27), image.Rect(81, 29, 105, 35), image.Rect(81, 37, 103, 43), image.Rect(81, 53, 157, 59), image.Rect(81, 69, 155, 75)}
	for i, line := range lines {
		if line.text != texts[i] || line.box != boxes[i] || line.capH != 5 {
			return false
		}
		if i == 0 || i == 5 {
			if len(line.colors) != 2 || line.colors[68] == 0 || line.colors[149] == 0 {
				return false
			}
		} else if len(line.colors) != 1 || line.colors[8] == 0 {
			return false
		}
	}
	for x := 76; x < 164; x++ {
		if canvas[9*320+x] != 0 || canvas[77*320+x] != 0 {
			return false
		}
	}
	for y := 9; y < 78; y++ {
		if canvas[y*320+76] != 0 || canvas[y*320+163] != 0 {
			return false
		}
	}
	return true
}
