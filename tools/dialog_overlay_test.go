package main

import (
	"crypto/sha256"
	"fmt"
	"image"
	"strings"
	"testing"
)

// 以自製的假 GAME.TXT 與語料測試（不含原版文字）。
func dialogFixture(t *testing.T) *dialogCatalog {
	t.Helper()
	game := []byte("@A\r\nThe {%STRING0} greet\r\nthe {%STRING1}.\r\n\r\nYes\r\nNo\r\n@B\r\nWe have %NUMBER0 %STRING0.\r\n@C\r\nThe %STRING0 greet the %STRING1.\r\n")
	gameSHA := fmt.Sprintf("%x", sha256.Sum256(game))
	row := func(id string, off int, text, zh string) string {
		raw := game[off : off+len(text)]
		if string(raw) != text {
			t.Fatalf("fixture 位移錯：%q", raw)
		}
		return strings.Join([]string{id, "GAME.TXT", gameSHA, fmt.Sprintf("0x%08X", off), fmt.Sprint(len(text)),
			fmt.Sprintf("%x", sha256.Sum256(raw)), "en", zh, "draft", ""}, "\t")
	}
	a := "The {%STRING0} greet\r\nthe {%STRING1}.\r\n\r\nYes\r\nNo"
	b := "We have %NUMBER0 %STRING0."
	corpus := strings.Join([]string{
		"message_id\tsource_file\tsource_file_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_en\tzh_hant\tstatus\tnotes",
		row("GAME.TXT:@A", strings.Index(string(game), a), a, `{%STRING0}問候\n{%STRING1}。\n\n是\n否`),
		row("GAME.TXT:@B", strings.Index(string(game), b), b, `我們有%NUMBER0%STRING0。`),
		"NAMES.TXT:@X\tNAMES.TXT\tx\t0x0\t1\tx\tSemi, Camp,  Camps\t半, 營地,  營地群\tdraft\t",
	}, "\n") + "\n"
	terms := "en\tzh\tcategory\nSioux\t蘇族\ttribe\nEnglish\t英國\tnation\nDup\t甲\tx\nDup\t乙\tx\n"
	c, err := loadDialogCatalog([]byte(corpus), []byte(terms), game, gameSHA, map[string]bool{"GAME.TXT:@C": true})
	if err != nil {
		t.Fatal(err)
	}
	return c
}

func TestDialogMatch(t *testing.T) {
	c := dialogFixture(t)
	id, zh, why := c.match("The Sioux greet the English.")
	if why != "" || id != "GAME.TXT:@A" || zh != "{蘇族}問候{英國}。" {
		t.Fatalf("%q %q %q", id, zh, why)
	}
	if _, zh, why := c.match("We have 9 Camps."); why != "" || zh != "我們有9營地群。" {
		t.Fatalf("NAMES 對照：%q %q", zh, why)
	}
	for text, want := range map[string]string{
		"The Aztec greet the English.": "variable-without-term",
		"The Dup greet the English.":   "variable-without-term",
		"Something else.":              "no-template",
		"We have x Camps.":             "no-template",
	} {
		if _, _, why := c.match(text); why != want {
			t.Errorf("%q：%q，應為 %q", text, why, want)
		}
	}
}

func TestDialogShown(t *testing.T) {
	var chars []dialogChar
	x, y := 10, 20
	for _, r := range "The Sioux greet" {
		chars = append(chars, dialogChar{c: byte(r), box: image.Rect(x, y, x+3, y+7)})
		if r == ' ' {
			chars[len(chars)-1].box = image.Rectangle{}
		}
		x += 4
	}
	x, y = 10, 30
	for _, r := range "the English." {
		chars = append(chars, dialogChar{c: byte(r), box: image.Rect(x, y, x+3, y+7)})
		x += 4
	}
	if got := dialogShownText(chars); got != "The Sioux greet the English." {
		t.Fatalf("%q", got)
	}
}

func TestDialogMasks(t *testing.T) {
	c := dialogFixture(t)
	c.fonts = map[int]*dialogFont{}
	for size := dialogAtlasMin; size <= dialogFontPx; size++ {
		f := &dialogFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, cjkTop: 2, cjkBottom: size - 2}
		for _, r := range "問候蘇族英國。甲" {
			a := image.NewAlpha(image.Rect(0, 0, size, size+5))
			for i := range a.Pix {
				a.Pix[i] = 255
			}
			f.glyphs[r], f.widths[r] = a, size
		}
		c.fonts[size] = f
	}
	sh, n, ac, size := c.dialogMasks("{蘇族}問候{英國}。", 400, 100, 7)
	if size != 30 || sh == nil || n == nil || ac == nil {
		t.Fatalf("30px 應放得下：%d", size)
	}
	if ac.AlphaAt(4+5, 10).A == 0 || ac.AlphaAt(4+2*30+5, 10).A != 0 {
		t.Fatal("強調層只含 {} 內字")
	}
	if _, _, _, size := c.dialogMasks("問候問候問候問候問候問候", 200, 40, 7); size != 0 {
		t.Fatalf("放不下應回 0，得 %d", size)
	}
	if _, _, _, size := c.dialogMasks("問候問候問候", 200, 100, 7); size != 30 {
		t.Fatalf("兩行 30px：%d", size)
	}
	if _, _, _, size := c.dialogMasks("缺字", 400, 100, 7); size != 0 {
		t.Fatal("圖集缺字應回原文")
	}
}

func dialogTestFonts(c *dialogCatalog, chars string) {
	c.fonts = map[int]*dialogFont{}
	for size := dialogAtlasMin; size <= dialogFontPx; size++ {
		f := &dialogFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, cjkTop: 2, cjkBottom: size - 2}
		for _, r := range chars {
			a := image.NewAlpha(image.Rect(0, 0, size, size+5))
			for i := range a.Pix {
				a.Pix[i] = 255
			}
			f.glyphs[r], f.widths[r] = a, size
		}
		c.fonts[size] = f
	}
}

func TestRunLinesAndStyle(t *testing.T) {
	mk := func(s string, x, y int, color byte) []dialogChar {
		var out []dialogChar
		for _, r := range s {
			ch := dialogChar{c: byte(r)}
			if r != ' ' {
				ch.box, ch.colors = image.Rect(x, y, x+3, y+6), map[byte]int{color: 9, 242: 2}
			}
			out = append(out, ch)
			x += 4
		}
		return out
	}
	chars := append(mk("Save Game", 17, 61, 68), mk("Load Game", 17, 69, 68)...)
	chars = append(chars, dialogChar{c: 0})
	lines := runLines(chars)
	if len(lines) != 2 || lines[0].text != "Save Game" || lines[1].text != "Load Game" || observedPitch(lines, 10) != 8 {
		t.Fatalf("%+v", lines)
	}
	// 目標172：行內大段無墨空隙（港口價格欄）記為右欄；一般字間空白不算。
	gap := append(mk("Master Carpenters    ", 17, 61, 68), mk("(Cost: 1000)", 150, 61, 68)...)
	gl := runLines(gap)
	if len(gl) != 1 || gl[0].gapLeft != "Master Carpenters" || gl[0].text != "Master Carpenters (Cost: 1000)" || gl[0].right.Min.X != 150 {
		t.Fatalf("空隙分欄 %+v", gl)
	}
	// 目標174：輸入列記下第一個冒號為止的標籤文字與墨跡。
	in := runLines(mk("Name: Jamestown_", 40, 90, 68))
	if len(in) != 1 || in[0].labelText != "Name:" || in[0].label != image.Rect(40, 90, 59, 96) || in[0].text != "Name: Jamestown_" {
		t.Fatalf("輸入列標籤 %+v", in)
	}
	// 長名稱使空隙變窄時，以原文連續空白判定。
	tight := append(mk("TOBACCONIST'S SHOP    ", 17, 61, 68)[:20], mk("(64 Hammers)", 97, 61, 68)...)
	if tl := runLines(tight); len(tl) != 1 || tl[0].gapLeft != "TOBACCONIST'S SHOP" || tl[0].right.Min.X != 97 {
		t.Fatalf("連續空白分欄 %+v", tl)
	}
	if lines[0].gapLeft != "" || !lines[0].right.Empty() {
		t.Fatalf("一般字間不應分欄 %+v", lines[0])
	}
	r := &dialogRun{chars: append(mk("COLO", 0, 0, 252), mk("Version 3.0", 20, 0, 254)...)}
	if n, a, s := runStyle(r); n != 254 || a != 252 || s != 0 {
		t.Fatalf("字色 %d %d %d", n, a, s)
	}
	r.shadowWritten = true
	if n, a, s := runStyle(r); n != 68 || a != 149 || s != 47 {
		t.Fatal("有陰影應為木紋框配色")
	}
}

func TestCenteredAndLineMasks(t *testing.T) {
	c := &dialogCatalog{}
	dialogTestFonts(c, "主後覲見國王為了榮耀是否")
	sh, n, _, size := c.centeredMasks(`^^主後\n^\n^^國王\n為了榮耀為了榮耀`, 200, 200, 32, false)
	if size == 0 || n == nil {
		t.Fatal("置中段落應放得下")
	}
	if sh.AlphaAt(10, 10).A != 0 {
		t.Fatal("無陰影時陰影層應為空")
	}
	// 「主後」兩字置中：左緣 (200-2*size)/2
	left := (200 - 2*size) / 2
	if n.AlphaAt(left+1, 4+2).A == 0 || n.AlphaAt(left-2, 4+2).A != 0 {
		t.Fatalf("置中位置不符，字級 %d", size)
	}
	lines := []runLine{{text: "Yes", box: image.Rect(15, 122, 25, 128), capH: 7}, {text: "No", box: image.Rect(15, 134, 22, 140), capH: 7}}
	safe := image.Rect(14, 121, 60, 142)
	_, n2, _, size2 := c.lineMasks([]string{"是", "否"}, lines, safe, 12, true)
	if size2 != 30 || n2.AlphaAt(4+1, 4+1).A == 0 || n2.AlphaAt(4+1, 13*4+4+1).A == 0 {
		t.Fatalf("逐行位置不符：%d", size2)
	}
	if _, _, _, s := c.lineMasks([]string{"是是是是是是是是是是", "否"}, lines, safe, 12, true); s != 0 {
		t.Fatal("超出整段右緣應回原文")
	}
}

// 目標174：輸入列只在標籤墨跡內排版，中文右緣對齊標籤右緣。
func TestInputLabelMasks(t *testing.T) {
	c := &dialogCatalog{}
	dialogTestFonts(c, "名稱：")
	label := image.Rect(40, 90, 70, 96)
	safe := image.Rect(label.Min.X-1, label.Min.Y-1, label.Max.X+1, label.Max.Y+2)
	_, n, _, size := c.lineMasks([]string{"\t名稱："}, []runLine{{box: label, right: label, capH: 6}}, safe, 9, false)
	if size == 0 {
		t.Fatal("標籤應放得下")
	}
	right := (label.Max.X - safe.Min.X) * 4
	if n.AlphaAt(right-2, 8).A == 0 || n.AlphaAt(right-3*size-2, 8).A != 0 {
		t.Fatalf("標籤應靠右對齊，字級 %d", size)
	}
	if _, _, _, s := c.lineMasks([]string{"\t名稱名稱名稱名稱："}, []runLine{{box: label, right: label, capH: 6}}, safe, 9, false); s != 0 {
		t.Fatal("標籤譯文超出標籤範圍應回原文")
	}
}

func TestAddDraft(t *testing.T) {
	menu := []byte("@GAME\r\n  Save Game\r\n  ~View Pieces\r\n")
	sum := fmt.Sprintf("%x", sha256.Sum256(menu))
	row := func(id string, off, n int, zh string) string {
		raw := menu[off : off+n]
		return strings.Join([]string{id, "MENU.TXT", sum, fmt.Sprintf("0x%08X", off), fmt.Sprintf("%x", sha256.Sum256(raw)), fmt.Sprint(n), zh, "draft", ""}, "\t")
	}
	draft := "candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_bytes_sha256\tsource_byte_length\tzh_hant\tstatus\tnotes\n" +
		row("MENU.TXT:a", 7, 11, "  儲存遊戲") + "\n" + row("MENU.TXT:b", 20, 14, "  ~V檢視單位") + "\n"
	c := &dialogCatalog{terms: map[string]string{}}
	if err := c.addDraft([]byte(draft), map[string][]byte{"MENU.TXT": menu}, nil); err != nil {
		t.Fatal(err)
	}
	if len(c.lines) != 2 {
		t.Fatalf("目標177：MENU.TXT 含 ~ 的列也採用：%d", len(c.lines))
	}
	if _, zh, why := c.matchIn(c.lines, "Save Game"); why != "" || zh != "儲存遊戲" {
		t.Fatalf("%q %q", zh, why)
	}
	if _, zh, why := c.matchIn(c.lines, "View Pieces"); why != "" || zh != "({V})檢視單位" {
		t.Fatalf("熱鍵列：%q %q", zh, why)
	}
	bad := strings.Replace(draft, sum, strings.Repeat("0", 64), 1)
	if (&dialogCatalog{}).addDraft([]byte(bad), map[string][]byte{"MENU.TXT": menu}, nil) == nil {
		t.Fatal("版本不符應失敗")
	}
}

func TestAddDraftNames(t *testing.T) {
	names := []byte("Amsterdam\r\nLondon\r\n")
	sum := fmt.Sprintf("%x", sha256.Sum256(names))
	raw := names[11:17]
	row := strings.Join([]string{"NAMES.TXT:a", "NAMES.TXT", sum, "0x0000000B", fmt.Sprintf("%x", sha256.Sum256(raw)), "6", "倫敦", "draft", ""}, "\t")
	draft := "candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_bytes_sha256\tsource_byte_length\tzh_hant\tstatus\tnotes\n" + row + "\n"
	c := &dialogCatalog{terms: map[string]string{}}
	c.addTerm("Amsterdam", "阿姆斯特丹")
	if err := c.addDraft([]byte(draft), map[string][]byte{"NAMES.TXT": names}, nil); err != nil {
		t.Fatal(err)
	}
	if c.terms["London"] != "倫敦" || len(c.lines) != 0 {
		t.Fatalf("NAMES 列應成為變數對照而非逐行模板：%v %d", c.terms, len(c.lines))
	}
}

func TestTermPriority(t *testing.T) {
	c := &dialogCatalog{terms: map[string]string{}}
	c.addNamePairs("Caravel, Galleon", "卡拉維爾帆船, 大帆船")
	c.addTerm("Caravel", "輕帆船")
	c.addNamePairs("Galleon", "蓋倫船")
	if c.terms["Caravel"] != "輕帆船" || c.terms["Galleon"] != "大帆船" {
		t.Fatalf("定稿譯名應優先、對照保留先出現者：%v", c.terms)
	}
	c.addTerm("Caravel", "別的譯名")
	if c.terms["Caravel"] != "" {
		t.Fatal("定稿譯名彼此衝突應視為查無")
	}
}

func TestScanDialogBoxPortrait(t *testing.T) {
	canvas := make([]byte, 64000)
	for i := range canvas {
		canvas[i] = 5
	}
	for x := 10; x < 200; x++ {
		canvas[40*320+x] = 0 // 上框
	}
	for y := 40; y < 120; y++ {
		canvas[y*320+10], canvas[y*320+199] = 0, 0 // 左右框
	}
	for y := 0; y < 60; y++ {
		for x := 120; x < 190; x++ {
			canvas[y*320+x] = 9 // 肖像壓住上框的一段
		}
	}
	l, top, r := scanDialogBox(canvas, 20, 100, 15, 195, 50)
	if l != 10 || top != 40 || r != 199 {
		t.Fatalf("外框 %d %d %d", l, top, r)
	}
}

func TestDialogSizes(t *testing.T) {
	for _, tc := range [][3]int{{7, 30, 20}, {5, 22, 15}, {0, 30, 20}, {9, 30, 20}} {
		if s, f := dialogSizes(tc[0]); s != tc[1] || f != tc[2] {
			t.Errorf("字高 %d：%d／%d", tc[0], s, f)
		}
	}
	c := dialogFixture(t)
	dialogTestFonts(c, "問候")
	if _, _, _, size := c.dialogMasks("問候", 400, 100, 5); size != 22 {
		t.Fatalf("字高 5 起始 22px：%d", size)
	}
}

func TestCenteredParagraphs(t *testing.T) {
	c := dialogFixture(t)
	dialogTestFonts(c, "甲乙丙")
	_, n, ac, size := c.centeredMasks(`^{甲}\n乙乙\n^\n{丙}`, 400, 400, 40, false)
	if n == nil || size != 30 {
		t.Fatalf("應放得下：%d", size)
	}
	// 標題行獨立一行（第 0 行），內文在第 1 行，第 2 行空白，第 3 行強調。
	row := func(k int) int { return 4 + k*40 - 2 + 5 }
	if ac.AlphaAt(6, row(0)).A == 0 || n.AlphaAt(6, row(1)).A == 0 || n.AlphaAt(6, row(2)).A != 0 || ac.AlphaAt(6, row(3)).A == 0 {
		t.Fatal("單一 ^ 開頭的行應自成一段")
	}
}

func TestAddPedia(t *testing.T) {
	pedia := []byte("@CARGO1\r\n^{FOO}\r\nFoo is a \xf9thing.\r\n")
	sum := func(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
	raw := pedia[9:]
	head := "message_id\tsource_file\tsource_file_sha256\tsection_offset\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_en\tzh_hant\tstatus\tnotes\n"
	row := strings.Join([]string{"PEDIA.TXT:@CARGO1", "PEDIA.TXT", sum(pedia), "0x0", "0x9", fmt.Sprint(len(raw)), sum(raw), "x", `^{甲}\n乙`, "draft", ""}, "\t")
	c := &dialogCatalog{terms: map[string]string{}, seen: map[string]bool{}}
	if err := c.addPedia([]byte(head+row+"\n"), pedia); err != nil {
		t.Fatal(err)
	}
	if id, zh, why := c.match("FOO Foo is a \u00f9thing."); why != "" || id != "PEDIA.TXT:@CARGO1" || zh != `^{甲}\n乙` {
		t.Fatalf("%q %q %q", id, zh, why)
	}
	if (&dialogCatalog{seen: map[string]bool{}}).addPedia([]byte(head+row+"\n"), append(pedia, 'x')) == nil {
		t.Fatal("版本不符應失敗")
	}
}

// 目標177：下拉選單譯稿的熱鍵與對齊標記。
func TestMenuZh(t *testing.T) {
	for in, want := range map[string]string{
		"  ~M移動單位":        "  ({M})移動單位",
		"  放大#   ~Z":      "  ({Z})放大",
		"  ~F~1 地形資訊":     "  ({F1})地形資訊",
		"  顯示~H隱藏地形":      "  ({H})顯示隱藏地形",
		"  加入殖民領地 (~B)":   "  加入殖民領地 ({B})",
		"  縮放層級 #60 x 48": "  縮放層級  60 x 48",
		"  儲存遊戲":          "  儲存遊戲",
	} {
		if got := menuZh(in); got != want {
			t.Errorf("%q → %q，應為 %q", in, got, want)
		}
	}
}

// 目標177：同一段印字裡整份重畫的行只留一次。
func TestRunLinesRedrawDedupe(t *testing.T) {
	mk := func(s string, x, y int) []dialogChar {
		var out []dialogChar
		for _, r := range s {
			ch := dialogChar{c: byte(r)}
			if r != ' ' {
				ch.box, ch.colors = image.Rect(x, y, x+3, y+6), map[byte]int{68: 9}
			}
			out = append(out, ch)
			x += 4
		}
		return out
	}
	var chars []dialogChar
	for i := 0; i < 3; i++ {
		chars = append(chars, mk("Move Pieces", 49, 13)...)
		chars = append(chars, mk("View Pieces", 49, 21)...)
	}
	if lines := runLines(chars); len(lines) != 2 || lines[0].text != "Move Pieces" || lines[1].text != "View Pieces" {
		t.Fatalf("重畫應去重：%+v", lines)
	}
}

// 目標177：雙引號包住的變數是玩家輸入，原樣代入；未包引號的變數仍須查術語表。
func TestQuotedVariable(t *testing.T) {
	c := &dialogCatalog{terms: map[string]string{}}
	c.templates = []dialogTemplate{makeDialogTemplate("q", `"%STRING0" not found.`, `找不到「%STRING0」。`, false),
		makeDialogTemplate("p", `%STRING0 not found.`, `找不到%STRING0。`, false)}
	if _, zh, why := c.matchIn(c.templates[:1], `"Jam" not found.`); why != "" || zh != `找不到「Jam」。` {
		t.Fatalf("引號變數：%q %q", zh, why)
	}
	if _, zh, why := c.matchIn(c.templates[:1], `"" not found.`); why != "" || zh != `找不到「」。` {
		t.Fatalf("空的引號變數：%q %q", zh, why)
	}
	if _, _, why := c.matchIn(c.templates[1:], `Jam not found.`); why != "variable-without-term" {
		t.Fatalf("未包引號應查術語表：%q", why)
	}
}
