package main

import (
	"crypto/sha256"
	"fmt"
	"image"
	"os"
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

func TestDialogColonyValueScope(t *testing.T) {
	template := makeDialogTemplate("GAME.TXT:@ABANDON:0x00001994", "Colony %STRING0.", "領地%STRING0。", false)
	c := &dialogCatalog{templates: []dialogTemplate{template}, terms: map[string]string{"Camp": "營地群"}}
	if _, _, why := c.match("Colony Home."); why != "variable-without-term" {
		t.Fatal("沒有名稱回呼仍翻譯", why)
	}
	c.colonyValue = func(name string) string {
		if name == "Home" {
			return "甲（Home）"
		}
		return name
	}
	for name, want := range map[string]string{"Home": "領地甲（Home）。", "Camp": "領地Camp。", "Town-17": "領地Town-17。"} {
		if _, zh, why := c.match("Colony " + name + "."); why != "" || zh != want {
			t.Fatalf("%s：%q %q", name, zh, why)
		}
	}
	for name, want := range map[string]string{"A{Town}": "unrenderable-variable", "A%Town": "unresolved-variable"} {
		if _, zh, why := c.match("Colony " + name + "."); zh != "" || why != want {
			t.Fatalf("不能按原樣顯示時未回退：%q %q", zh, why)
		}
	}
	for _, fixture := range []struct{ id, variable string }{
		{"GAME.TXT:@ABANDON2:0x00001A5B", "%STRING0"},
		{"GAME.TXT:@OTHER", "%STRING0"},
		{"GAME.TXT:@ABANDON:0x00001994", "%STRING1"},
	} {
		other := makeDialogTemplate(fixture.id, "Colony "+fixture.variable+".", "領地"+fixture.variable+"。", false)
		if _, _, why := c.matchIn([]dialogTemplate{other}, "Colony Unknown."); why != "variable-without-term" {
			t.Fatalf("未知欄位借用了名稱回呼：%s %s %s", fixture.id, fixture.variable, why)
		}
	}
}

func TestDialogLoadFilenameScope(t *testing.T) {
	load := makeDialogTemplate("GAME.TXT:0x00000854", "Loaded %STRING0 successfully.", "已成功載入 %STRING0。", false)
	c := &dialogCatalog{templates: []dialogTemplate{load}, terms: map[string]string{"COLONY02.SAV": "不應查譯"}}
	for _, name := range []string{"COLONY00.SAV", "COLONY02.SAV", "COLONY99.SAV"} {
		if _, zh, why := c.match("Loaded " + name + " successfully."); why != "" || zh != "已成功載入 "+name+"。" {
			t.Fatalf("檔名未保留原值：%s %q %q", name, zh, why)
		}
	}
	for _, name := range []string{"COLONY2.SAV", "COLONY002.SAV", "colony02.sav", "OTHER02.SAV", "COLONY0X.SAV", "../COLONY02.SAV", "COLONY{02}.SAV", "COLONY%02.SAV"} {
		if _, zh, why := c.match("Loaded " + name + " successfully."); zh != "" || why != "unverified-save-filename" {
			t.Fatalf("未驗格式未回退：%s %q %q", name, zh, why)
		}
	}
	delete(c.terms, "COLONY02.SAV")
	for _, fixture := range []struct{ id, variable string }{
		{"GAME.TXT:0x00000854", "%STRING1"},
		{"GAME.TXT:0x0000078E", "%STRING0"},
		{"GAME.TXT:@OTHER", "%STRING0"},
	} {
		other := makeDialogTemplate(fixture.id, "Loaded "+fixture.variable+" successfully.", "已載入"+fixture.variable+"。", false)
		if _, _, why := c.matchIn([]dialogTemplate{other}, "Loaded COLONY02.SAV successfully."); why != "variable-without-term" {
			t.Fatalf("其他欄位借用檔名例外：%s %s %s", fixture.id, fixture.variable, why)
		}
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
	if id, zh, why := c.match("FOO Foo is a thing."); why != "" || id != "PEDIA.TXT:@CARGO1" || zh != `^{甲}\n乙` {
		t.Fatalf("%q %q %q", id, zh, why)
	}
	if (&dialogCatalog{seen: map[string]bool{}}).addPedia([]byte(head+row+"\n"), append(pedia, 'x')) == nil {
		t.Fatal("版本不符應失敗")
	}
}

func TestNonprintingF9ReadPair(t *testing.T) {
	for _, tc := range []struct {
		name   string
		high   byte
		drawn  bool
		next   uint32
		gap    uint64
		accept bool
	}{
		{"無墨F9缺0", 0xF9, false, 0x1000, 10, true},
		{"其他高位元組", 0xFA, false, 0x1000, 10, false},
		{"已繪製F9", 0xF9, true, 0x1000, 10, false},
		{"錯誤基址", 0xF9, false, 0x1002, 10, false},
		{"段落超時", 0xF9, false, 0x1000, dialogGap, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			d := &dialogRuntime{}
			d.onRead(0x1000, 'A', 1)
			d.run.chars[0].box = image.Rect(10, 10, 15, 15)
			d.onRead(0x1001, 0, 2)
			d.onRead(0x1000, tc.high, 3)
			before := d.run
			if tc.drawn {
				before.chars[len(before.chars)-1].box = image.Rect(15, 10, 16, 15)
			}
			finished := d.onRead(tc.next, ' ', 3+tc.gap)
			if !tc.accept {
				if finished != before || d.run == before {
					t.Fatal("未證實配對必須結束舊段")
				}
				return
			}
			if finished != nil || d.run != before {
				t.Fatal("F9不可拆掉完整段落")
			}
			d.onRead(0x1001, 0, 4+tc.gap)
			d.onRead(0x1000, 'B', 5+tc.gap)
			d.run.chars[len(d.run.chars)-1].box = image.Rect(20, 10, 25, 15)
			d.onRead(0x1001, 0, 6+tc.gap)
			if d.run.readPos%2 != 0 || dialogShownText(d.run.chars) != "A B" {
				t.Fatal("完整顯示串應不含非印字F9")
			}
			lines := runLines(d.run.chars)
			if len(lines) != 1 || lines[0].text != "A B" {
				t.Fatal("行重組同樣應略去F9")
			}
		})
	}
	// 段尾未讀到下一字，仍是未完成，不能放寬finish的完整性守門。
	d := &dialogRuntime{}
	d.onRead(0x1000, 0xF9, 1)
	if st, shown, why := d.finish(d.run, make([]byte, 64000), 2); st != nil || shown != "" || why != "" {
		t.Fatal("段尾F9仍須拒絕未完成配對")
	}
	// 原版有讀結尾0時照原配對，不額外跳過下一字。
	d = &dialogRuntime{}
	d.onRead(0x1000, 0xF9, 1)
	d.onRead(0x1001, 0, 2)
	d.onRead(0x1000, 'A', 3)
	if d.run.readPos != 3 {
		t.Fatal("正常配對不可多算")
	}
}

func TestPediaPercentAndBlankTabParagraph(t *testing.T) {
	// 百科原版顯示單一百分比；譯稿保留原始 %% 與跳脫 Tab。
	pedia := []byte("@JOB8\r\n^{FISHER}\r\n50%%\r\n^\t\r\n{BODY}\r\n")
	sum := func(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
	raw := pedia[7:]
	head := "message_id\tsource_file\tsource_file_sha256\tsection_offset\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_en\tzh_hant\tstatus\tnotes\n"
	inputZh := `^{甲}\n50%%\n^\t\n{乙}`
	row := strings.Join([]string{"PEDIA.TXT:@JOB8", "PEDIA.TXT", sum(pedia), "0", "7", fmt.Sprint(len(raw)), sum(raw), "x", inputZh, "draft", ""}, "\t")
	c := &dialogCatalog{terms: map[string]string{}, seen: map[string]bool{}}
	if err := c.addPedia([]byte(head+row+"\n"), pedia); err != nil {
		t.Fatal(err)
	}
	_, zh, why := c.match("FISHER 50% BODY")
	if why != "" || zh != "^{甲}\\n50%\\n^\t\\n{乙}" {
		t.Fatalf("顯示解碼不符：%q %q", zh, why)
	}
	if _, _, why := c.match("FISHER 50%% BODY"); why == "" {
		t.Fatal("不可把雙百分比當原版顯示")
	}
	// 同樣的百分比放在未取得百科字面證據的模板，仍須拒絕。
	plain := &dialogCatalog{templates: []dialogTemplate{makeDialogTemplate("plain", "FISHER 50% BODY", "50%", false)}}
	if _, _, why := plain.match("FISHER 50% BODY"); why != "unresolved-variable" {
		t.Fatal("通用百分比守門不可移除")
	}
	dialogTestFonts(c, "甲乙50%")
	_, n, ac, size := c.centeredMasks(zh, 400, 400, 40, false)
	if n == nil || size == 0 {
		t.Fatal("跳脫Tab不應造成缺字形回退")
	}
	rowY := func(k int) int { return 4 + k*40 - 2 + 5 }
	if n.AlphaAt(6, rowY(2)).A != 0 || ac.AlphaAt(6, rowY(3)).A == 0 {
		t.Fatal("Tab段落應保留空行及後續強調段")
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

// 目標178：段內連續字串（選單的停用項目）接在垂直清單的下一列時屬於同一段；
// 段首就是連續字串、或首字不在清單下一列（殖民地畫面的數字）仍整段丟棄。
func TestOnReadContiguousInRun(t *testing.T) {
	// feed 讀入 seq，每個非 0 字元讀後立刻「畫出」在 (x0+4*i, y)，i 為該串內第幾字。
	feed := func(d *dialogRuntime, base uint32, step *uint64, x0, y int, seq ...byte) {
		for i, v := range seq {
			*step += 800
			d.onRead(base+uint32(i), v, *step)
			if v != 0 && v != '~' && d.run != nil {
				d.onWrite(y*320+x0+4*i, 0, 68, true, false)
			}
		}
	}
	base := uint32(0x2AE44)
	d := &dialogRuntime{}
	step := uint64(1000)
	// 逐字項目 "Ab"：每字從基址讀「字元、0」，畫在 (81,20)、(85,20)。
	for i, c := range []byte("Ab") {
		feed(d, base, &step, 81+4*i, 20, c, 0)
	}
	// 連續字串 "Cd~e"（左緣同為 81、在下一列），以 0 結尾。
	feed(d, base, &step, 81, 28, 'C', 'd', '~', 'e', 0)
	// 之後仍是逐字項目 "F"。
	feed(d, base, &step, 81, 36, 'F', 0)
	r := d.run
	if r == nil || r.contig || r.readPos%2 != 0 {
		t.Fatalf("連續字串結束後應回到逐字讀取：%+v", r)
	}
	var got []byte
	for _, ch := range r.chars {
		got = append(got, ch.c)
	}
	if string(got) != "AbCd~eF" {
		t.Fatalf("段內字元 %q", got)
	}
	for i, ch := range r.chars {
		if want := i >= 2 && i <= 5; ch.contig != want {
			t.Fatalf("第 %d 字（%q）連續字串旗標 %v", i, ch.c, ch.contig)
		}
	}
	// 段首就是連續字串（頂端選單列、狀態欄）：整段丟棄。
	d2 := &dialogRuntime{}
	step = 5000
	feed(d2, base, &step, 13, 1, 'G', 'A', 'M', 'E', 0)
	if d2.run != nil && len(d2.run.chars) > 1 {
		t.Fatalf("段首連續字串應丟棄：%+v", d2.run)
	}
	// 連續字串的首字不在清單下一列（例如殖民地畫面散在各處的數字）：丟棄，不併入。
	d4 := &dialogRuntime{}
	step = 20000
	for i, c := range []byte("Ab") {
		feed(d4, base, &step, 81+4*i, 20, c, 0)
	}
	feed(d4, base, &step, 150, 60, 'X', 'y', 'z', 0) // 左緣差 69
	if d4.run != nil && len(d4.run.chars) > 3 {
		t.Fatalf("錯位的連續字串不應併入：%+v", d4.run)
	}
	// 連續字串未讀到 0 就被打斷（位址跳開）：不完整，收尾時不出事件。
	d3 := &dialogRuntime{}
	step = 9000
	feed(d3, base, &step, 81, 20, 'A', 0)
	feed(d3, base, &step, 81, 28, 'C', 'd')
	if fin, why, _ := d3.finish(d3.run, make([]byte, 64000), step); fin != nil || why != "" {
		t.Fatal("未結束的連續字串不應出事件")
	}
}

// 目標178：沒有墨跡的 ~ 是熱鍵記號，不算文字；有墨跡的 ~ 照算。
func TestMenuLeadingHotkeyContinuation(t *testing.T) {
	for _, tc := range []struct {
		name             string
		x, y             int
		ink, ended, want bool
	}{
		{"下一列", 81, 36, true, true, true},
		{"錯位", 90, 36, true, true, false},
		{"同列", 81, 28, true, true, false},
		{"沒有字形", 81, 36, false, true, false},
		{"斷讀", 81, 36, true, false, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			d := &dialogRuntime{}
			step := uint64(1000)
			base := uint32(175684)
			draw := func(x, y int) {
				for yy := y; yy < y+5; yy++ {
					for xx := x; xx < x+3; xx++ {
						d.onWrite(yy*320+xx, 0, 8, true, false)
					}
				}
			}
			for row, word := range []string{"Ab", "Cd"} {
				for i, c := range []byte(word) {
					step += 800
					d.onRead(base, c, step)
					draw(81+i*4, 20+row*8)
					step += 800
					d.onRead(base+1, 0, step)
				}
			}
			for i, c := range []byte("~Load") {
				step += 800
				d.onRead(base+uint32(i), c, step)
				if i > 0 && tc.ink {
					draw(tc.x+(i-1)*4, tc.y)
				}
			}
			if tc.ended {
				step += 800
				d.onRead(base+5, 0, step)
			}
			if d.run == nil {
				t.Fatal("應暫留待字形確認")
			}
			var raw []byte
			for _, ch := range d.run.chars {
				raw = append(raw, ch.c)
			}
			if string(raw) != "AbCd~Load" {
				t.Fatalf("原始字元丟失：%q", raw)
			}
			valid := d.run.readPos%2 == 0 && menuPrefixesValid(d.run.chars)
			if valid != tc.want {
				t.Fatalf("字形確認=%v，預期%v", valid, tc.want)
			}
			if !tc.want {
				if st, _, _ := d.finish(d.run, make([]byte, 64000), step); st != nil {
					t.Fatal("負例不得出覆蓋")
				}
			}
		})
	}
	for _, next := range []byte{'0', ' ', '~'} {
		chars := []dialogChar{{c: 'A', box: image.Rect(81, 20, 84, 25)}, {c: 'B', box: image.Rect(81, 28, 84, 33)}, {c: '~'}}
		if menuPrefixNext(chars, next) {
			t.Fatalf("未證實前綴~%c不得暫留", next)
		}
	}
}

func TestPrefixCandidatePartiallyErased(t *testing.T) {
	r := &dialogRun{readPos: 2, firstOld: map[int]byte{100: 0, 101: 0}, lastText: map[int]bool{100: true, 101: false}}
	r.chars = []dialogChar{
		{c: 'A', box: image.Rect(81, 20, 84, 25)}, {c: 'b', box: image.Rect(85, 20, 88, 25)},
		{c: 'C', box: image.Rect(81, 28, 84, 33)}, {c: 'd', box: image.Rect(85, 28, 88, 33)},
		{c: '~', contig: true, prefixContinuation: true},
		{c: 'L', box: image.Rect(81, 36, 84, 41), contig: true}, {c: 'o', box: image.Rect(85, 36, 88, 41), contig: true},
	}
	d := &dialogRuntime{}
	if st, _, why := d.finish(r, make([]byte, 64000), 1); st != nil || why != "text-erased-before-finish" {
		t.Fatalf("部分抹除仍須拒絕：%v %q", st, why)
	}
}

func TestHotkeyMarkIgnored(t *testing.T) {
	ink := image.Rect(0, 0, 3, 5)
	chars := []dialogChar{{c: 'B', box: ink}, {c: '~'}, {c: 'R', box: image.Rect(4, 0, 7, 5)}}
	if got := dialogShownText(chars); got != "BR" {
		t.Fatalf("熱鍵記號應略過：%q", got)
	}
	if got := runLines(chars); len(got) != 1 || got[0].text != "BR" {
		t.Fatalf("行文字 %+v", got)
	}
	chars[1].box = image.Rect(2, 0, 3, 5)
	if got := dialogShownText(chars); got != "B~R" {
		t.Fatalf("有墨跡的 ~ 應保留：%q", got)
	}
}

// 目標178：強調色取多色行的次要色號；主色號不是一般色也不是強調色的行歸第三層。
func TestLineRoles(t *testing.T) {
	enabled := runLine{text: "Fortify", colors: map[byte]int{68: 60, 149: 12}}
	other := runLine{text: "Sentry", colors: map[byte]int{68: 50, 149: 10}}
	gray := runLine{text: "Build Road", colors: map[byte]int{8: 70}}
	accent, dimC, layers, why := lineRoles([]runLine{enabled, gray, other, gray}, 68, 8, 0)
	if why != "" || accent != 149 || dimC != 8 || fmt.Sprint(layers) != "[0 1 0 1]" {
		t.Fatalf("角色 %d %d %v %q", accent, dimC, layers, why)
	}
	// 沒有多色行：沿用全段統計的強調色，整行單色的強調行仍走強調層（買不起的灰色選項）。
	accent, dimC, layers, why = lineRoles([]runLine{{colors: map[byte]int{68: 9}}, {colors: map[byte]int{8: 9}}}, 68, 8, 0)
	if why != "" || accent != 8 || dimC != 0 || fmt.Sprint(layers) != "[0 0]" {
		t.Fatalf("無多色行 %d %d %v %q", accent, dimC, layers, why)
	}
	// 未取證的混色停用項目：整段回原文，不推測熱鍵配色。
	mixed := runLine{text: "x", colors: map[byte]int{8: 40, 149: 6}}
	if _, _, _, why := lineRoles([]runLine{enabled, mixed}, 68, 149, 0); why != "line-colors" {
		t.Fatalf("混色第三層應回原文：%q", why)
	}
	// 兩種以上的第三色號：回原文。
	if _, _, _, why := lineRoles([]runLine{enabled, gray, {colors: map[byte]int{15: 9}}}, 68, 149, 0); why != "line-colors" {
		t.Fatalf("兩種第三色應回原文：%q", why)
	}
}

// 目標178：第三層的行只畫在第三層遮罩，且 layerDim 不畫強調字母。
func TestLineLayerMasks(t *testing.T) {
	c := &dialogCatalog{}
	dialogTestFonts(c, "耕森林清除")
	lines := []runLine{{text: "a", box: image.Rect(15, 122, 25, 128), capH: 7}, {text: "b", box: image.Rect(15, 134, 22, 140), capH: 7}}
	safe := image.Rect(14, 121, 80, 142)
	_, n, ac, dm, size := c.lineLayerMasks([]string{"{耕}森", "{清}除"}, lines, safe, 12, false, []int{layerNormal, layerDim})
	if size == 0 || dm == nil {
		t.Fatal("應有第三層")
	}
	first, second := image.Pt(4+1, 4+1), image.Pt(4+1, 13*4+4+1)
	if n.AlphaAt(first.X, first.Y).A == 0 || dm.AlphaAt(first.X, first.Y).A != 0 || ac.AlphaAt(first.X, first.Y).A == 0 {
		t.Fatal("一般層的行應畫在一般層並帶強調字母")
	}
	if n.AlphaAt(second.X, second.Y).A != 0 || dm.AlphaAt(second.X, second.Y).A == 0 || ac.AlphaAt(second.X, second.Y).A != 0 {
		t.Fatal("第三層的行不應進一般層或強調層")
	}
	if _, _, _, dm2, _ := c.lineLayerMasks([]string{"耕"}, lines[:1], safe, 12, false, nil); dm2 != nil {
		t.Fatal("沒有第三層的行時遮罩應為 nil")
	}
}

// 目標178：併入的連續字串不讓整段像訊息框（殖民地畫面的數字與按鈕不應被自動應答當成對話框）。
func TestContigDoesNotMakeDialogLike(t *testing.T) {
	r := &dialogRun{}
	for i := 0; i < 12; i++ {
		r.chars = append(r.chars, dialogChar{c: 'a', box: image.Rect(10+i*4, 50, 13+i*4, 55), contig: true})
	}
	if r.dialogLike() {
		t.Fatal("只有連續字串的墨跡不應像訊息框")
	}
	for i := 0; i < 10; i++ {
		r.chars = append(r.chars, dialogChar{c: 'b', box: image.Rect(10+i*4, 60, 13+i*4, 65)})
	}
	if !r.dialogLike() {
		t.Fatal("逐字墨跡十字以上仍像訊息框")
	}
}

// 目標178：併入連續字串的段必須是左緣對齊的垂直清單，否則靜默略過。
func TestFinishContigNeedsAlignedList(t *testing.T) {
	d := &dialogRuntime{}
	mk := func(s string, x, y int, contig bool) []dialogChar {
		var out []dialogChar
		for i, c := range []byte(s) {
			out = append(out, dialogChar{c: c, box: image.Rect(x+i*4, y, x+i*4+3, y+5), colors: map[byte]int{68: 6}, contig: contig})
		}
		return out
	}
	r := &dialogRun{readPos: 2}
	r.chars = append(mk("AAAA", 81, 20, false), mk("CCCC", 90, 28, true)...) // 第二行左緣差 9
	if st, shown, why := d.finish(r, make([]byte, 64000), 1); st != nil || shown != "" || why != "" {
		t.Fatalf("錯位的混合段應靜默略過：%v %q %q", st, shown, why)
	}
	// 左緣對齊時不被這條擋下（後續因沒有模板目錄而在別處回覆；這裡只確認不是靜默略過）。
	d.cat = &dialogCatalog{}
	r.chars = append(mk("AAAA", 81, 20, false), mk("CCCC", 81, 28, true)...)
	// 第二行起點 81 < 第一行最後一字 93，兩行左緣皆 81。
	if _, shown, _ := d.finish(r, make([]byte, 64000), 1); shown == "" {
		t.Fatal("左緣對齊的清單應進入比對")
	}
}

// 目標178：逐行清單成功時，狀態帶各行原文（普查逐行歸屬用）。
func TestFinishListItems(t *testing.T) {
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
	dialogTestFonts(c, "儲存遊戲(V)檢視單位")
	mk := func(s string, x, y int) []dialogChar {
		var out []dialogChar
		for i, ch := range []byte(s) {
			d := dialogChar{c: ch}
			if ch != ' ' {
				d.box, d.colors = image.Rect(x+i*4, y, x+i*4+3, y+5), map[byte]int{68: 6}
			}
			out = append(out, d)
		}
		return out
	}
	d := &dialogRuntime{cat: c}
	r := &dialogRun{readPos: 2, chars: append(mk("Save Game", 81, 20), mk("View Pieces", 81, 28)...)}
	st, shown, why := d.finish(r, make([]byte, 64000), 1)
	if st == nil {
		t.Fatalf("逐行清單應成功：%q %q", shown, why)
	}
	if fmt.Sprint(st.items) != "[Save Game View Pieces]" {
		t.Fatalf("各行原文：%v", st.items)
	}
}

// 收尾延遲期間原版重畫會抹除候選；部分覆蓋與游標仍沿既有規則。
func TestFinishErasedBeforeFinish(t *testing.T) {
	for _, tc := range []struct {
		name       string
		erase      int
		cursor     bool
		wantErased bool
	}{
		{"完整重畫", 3, false, true},
		{"部分重畫", 2, false, false},
		{"游標覆蓋", 3, true, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			d := &dialogRuntime{cat: &dialogCatalog{}, run: &dialogRun{
				readPos: 2, firstOld: map[int]byte{}, lastText: map[int]bool{},
				chars: []dialogChar{{c: 'X'}},
			}}
			for x := 20; x < 23; x++ {
				d.onWrite(40*320+x, 0, 68, true, false)
			}
			for x := 20; x < 20+tc.erase; x++ {
				d.onWrite(40*320+x, 68, 0, false, tc.cursor)
			}
			st, shown, why := d.finish(d.run, make([]byte, 64000), 100000)
			if shown != "X" || (why == "text-erased-before-finish") != tc.wantErased {
				t.Fatalf("收尾結果：%q %q", shown, why)
			}
			if tc.wantErased && st != nil {
				t.Fatal("已完全抹除的候選不應產生覆蓋")
			}
		})
	}
}

func TestSaveGoodVariableIsolation(t *testing.T) {
	c := &dialogCatalog{terms: map[string]string{"COLONY03.SAV": "假檔名譯詞"}, templates: []dialogTemplate{
		makeDialogTemplate("GAME.TXT:0x000007B9", "Save %STRING1 to %STRING0.", "存%STRING1至%STRING0。", false),
		makeDialogTemplate("GAME.TXT:other", "Other %STRING1 to %STRING0.", "其他%STRING1至%STRING0。", false),
	}}
	calls := 0
	c.saveDescription = func(v string) (string, bool) { calls++; return "名字", v == "Player" }
	_, got, why := c.match("Save Player to COLONY03.SAV.")
	if why != "" || got != "存名字至COLONY03.SAV。" || calls != 1 {
		t.Fatalf("%q %q %d", got, why, calls)
	}
	if _, _, why := c.match("Save Player to OTHER.SAV."); why != "unverified-save-filename" {
		t.Fatal(why)
	}
	if _, _, why := c.match("Save Unknown to COLONY03.SAV."); why != "unverified-save-description" {
		t.Fatal(why)
	}
	before := calls
	if _, _, why := c.match("Other Player to COLONY03.SAV."); why != "variable-without-term" || calls != before {
		t.Fatalf("其他模板取得回呼：%q", why)
	}
	c.saveDescription = nil
	if _, _, why := c.match("Save Player to COLONY03.SAV."); why != "unverified-save-description" {
		t.Fatal(why)
	}
}

func TestSaveGoodDraftPromotion(t *testing.T) {
	raw := []byte("Report %STRING1 to %STRING0.")
	sum := fmt.Sprintf("%x", sha256.Sum256(raw))
	head := "candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_bytes_sha256\tsource_byte_length\tzh_hant\tstatus\tnotes\n"
	row := func(id string) []byte {
		return []byte(head + strings.Join([]string{id, "GAME.TXT", sum, "0", sum, fmt.Sprint(len(raw)), "存%STRING1至%STRING0。", "draft", ""}, "\t") + "\n")
	}
	for _, id := range []string{"GAME.TXT:0x000007B9", "GAME.TXT:other"} {
		c := &dialogCatalog{terms: map[string]string{}}
		if err := c.addDraft(row(id), map[string][]byte{"GAME.TXT": raw}, nil); err != nil {
			t.Fatal(err)
		}
		want := 0
		if id == "GAME.TXT:0x000007B9" {
			want = 1
		}
		if len(c.templates) != want || len(c.lines) != 1 {
			t.Fatalf("%s templates %d lines %d", id, len(c.templates), len(c.lines))
		}
	}
	c := &dialogCatalog{}
	if err := c.addDraft(row("GAME.TXT:0x000007B9"), map[string][]byte{"GAME.TXT": []byte("Wrong")}, nil); err == nil {
		t.Fatal("來源不同仍載入")
	}
	if len(c.templates) != 0 {
		t.Fatal("來源錯誤仍加入完整模板")
	}
}

func TestSlotContextAndTitleRetention(t *testing.T) {
	title := &dialogShown{id: "GAME.TXT:0x00000826", phase: "active", safe: image.Rect(10, 10, 12, 12), afterSafe: []byte{0, 0, 0, 0}}
	list := &dialogShown{id: "STRING:save-slot+list", phase: "active", safe: image.Rect(10, 14, 20, 30)}
	d := &dialogRuntime{cur: title}
	for _, n := range []int{0, 1, 2, 7, 9, 11} {
		if d.slotListContext(n) {
			t.Fatal("未知列數", n)
		}
	}
	if !d.slotListContext(8) || !d.slotListContext(10) {
		t.Fatal("正常列數未接受")
	}
	d.cur, d.prev = list, title
	canvas := make([]byte, 64000)
	if !d.slotListContext(10) || !d.retainSlotTitle(list, canvas) {
		t.Fatal("反白重印未保留完整標題")
	}
	canvas[10*320+10] = 1
	if d.retainSlotTitle(list, canvas) {
		t.Fatal("標題底图變更仍保留")
	}
	canvas[10*320+10] = 0
	for _, phase := range []string{"waiting-screen", "expired", "unknown"} {
		title.phase = phase
		if d.retainSlotTitle(list, canvas) {
			t.Fatal("非活動標題仍保留", phase)
		}
	}
	title.phase = "active"
	title.id = "OTHER"
	if d.slotListContext(10) || d.retainSlotTitle(list, canvas) {
		t.Fatal("其他標題借用回呼")
	}
	title.id = "GAME.TXT:0x00000826"
	list.id = "STRING:line+list"
	if d.slotListContext(10) || d.retainSlotTitle(list, canvas) {
		t.Fatal("其他清單借用生命週期")
	}
}

func TestSlotClosingAndWholeListFallback(t *testing.T) {
	mk := func(rows int) *dialogRun {
		r := &dialogRun{firstOld: map[int]byte{}, lastText: map[int]bool{}}
		for row := 0; row < rows; row++ {
			for i, c := range []byte("(EMPTY)") {
				x, y := 10+i*4, 20+row*8
				r.chars = append(r.chars, dialogChar{c: c, box: image.Rect(x, y, x+3, y+5), colors: map[byte]int{68: 15}})
				at := y*320 + x
				r.firstOld[at] = 0
				r.lastText[at] = true
			}
		}
		return r
	}
	title := &dialogShown{id: "GAME.TXT:0x0000078E", phase: "active"}
	d := &dialogRuntime{cat: &dialogCatalog{}, cur: title, slotFallback: func(s string) (string, bool) { return "空白", s == "(EMPTY)" }, lineFallback: func(string) (string, bool) { t.Fatal("槽位落入一般回呼"); return "", false }}
	r := mk(8)
	canvas := make([]byte, 64000)
	if st, _, why := d.finish(r, canvas, 100); st != nil || why != "layout-overflow" {
		t.Fatal("缺字模未整段回退", why)
	}
	r.lastText[20*320+10] = false
	if st, _, why := d.finish(r, canvas, 100); st != nil || why != "text-erased-before-finish" {
		t.Fatal("只剩部分文字仍啟用", why)
	}
	r = mk(8)
	r.chars[0].c = 'X'
	if st, _, why := d.finish(r, canvas, 100); st != nil || why != "slot-no-translation" {
		t.Fatal("未知列沒有整段回退", why)
	}
	d.slotFallback = nil
	r = mk(8)
	if st, _, why := d.finish(r, canvas, 100); st != nil || why != "slot-no-translation" {
		t.Fatal("缺譯文仍翻譯", why)
	}
}

func TestEuropeShadeRoles(t *testing.T) {
	lines := []runLine{{colors: map[byte]int{68: 30, 47: 15, 128: 8}}, {colors: map[byte]int{8: 40, 47: 20, 128: 9}}}
	a, dim, l, why := lineRoles(lines, 68, 149, 47)
	if why != "" || a != 149 || dim != 8 || len(l) != 2 || l[1] != layerDim {
		t.Fatal(a, dim, l, why)
	}
	for _, bad := range []map[byte]int{{8: 40, 47: 20, 128: 9, 149: 1}, {8: 40, 47: 20, 128: 9, 9: 1}} {
		q := append([]runLine(nil), lines...)
		q[1].colors = bad
		if _, _, _, why = lineRoles(q, 68, 149, 47); why != "line-colors" {
			t.Fatal("真正混色未拒絕", why)
		}
	}
	q := append([]runLine(nil), lines...)
	q = append(q, runLine{colors: map[byte]int{9: 40, 47: 20, 128: 9}})
	if _, _, _, why = lineRoles(q, 68, 149, 47); why != "line-colors" {
		t.Fatal("兩種停用色未拒絕")
	}
	if _, k := lineDominant(runLine{colors: map[byte]int{8: 40, 128: 10}}, 0); k != 2 {
		t.Fatal("無木紋陰影時誤排除128")
	}
}

// 規格035：整個名稱須綁定UNIT來源，不能由通用術語或數字規則補譯。
func TestUnitCaptionWholeNameScope(t *testing.T) {
	tpl := makeDialogTemplate("GAME.TXT:@COLONYUNIT:0x00009A33", "Options for {%STRING0%STRING1}:", "{%STRING0%STRING1}的選項：", false)
	c := &dialogCatalog{templates: []dialogTemplate{tpl}, terms: map[string]string{"England": "英國", "Soldiers": "一般譯名"}, unitCaptionNames: map[string]string{"Soldiers": "士兵"}}
	if _, zh, why := c.match("Options for Soldiers:"); zh != "{士兵}的選項：" || why != "" {
		t.Fatal(zh, why)
	}
	for _, name := range []string{"England", "999", "Unknown", "S oldiers"} {
		if _, zh, why := c.match("Options for " + name + ":"); zh != "" || why != "unverified-unit-caption-name" {
			t.Fatal(name, zh, why)
		}
	}
	c.unitCaptionNames = nil
	if _, zh, why := c.match("Options for Soldiers:"); zh != "" || why != "unverified-unit-caption-name" {
		t.Fatal("缺來源綁定", zh, why)
	}
	c.unitCaptionNames = map[string]string{"Soldiers": "舊名"}
	if c.bindUnitCaptionNames(nil, nil) || c.unitCaptionNames != nil {
		t.Fatal("錯版來源未清除舊綁定")
	}
	other := makeDialogTemplate("OTHER", "Options for {%STRING0%STRING1}:", "{%STRING0%STRING1}的選項：", false)
	if len(other.names) != 2 {
		t.Fatal("完整名稱特例外溢其他模板")
	}
}

// 抵港教學的玩家名稱須與一般術語及強調碼隔離。
func TestDockTutorialColonyNameIsolation(t *testing.T) {
	template := makeDialogTemplate("GAME.TXT:@TUTORIAL12", "Ship arrived %STRING0.", "船已抵達%STRING0。", false)
	c := &dialogCatalog{templates: []dialogTemplate{template}, terms: map[string]string{"Camp": "一般術語"}}
	if _, _, why := c.match("Ship arrived Camp."); why != "unverified-colony-name" {
		t.Fatal(why)
	}
	c.colonyValue = func(name string) string {
		if name == "Home" {
			return "家園（Home）"
		}
		return name
	}
	for name, want := range map[string]string{"Home": "船已抵達家園（Home）。", "Camp": "船已抵達Camp。", "999": "船已抵達999。"} {
		if _, zh, why := c.match("Ship arrived " + name + "."); why != "" || zh != want {
			t.Fatal(name, zh, why)
		}
	}
	if _, _, why := c.match("Ship arrived {Camp}."); why != "unrenderable-variable" {
		t.Fatal(why)
	}
}

func TestCargoShipProfilesAndSourceIsolation(t *testing.T) {
	game, e := os.ReadFile("/game/GAME.TXT")
	if os.IsNotExist(e) {
		t.Skip("缺合法原版")
	}
	if e != nil {
		t.Fatal(e)
	}
	corpus, e := os.ReadFile("/repo/text/corpus.zh-Hant.tsv")
	if e != nil {
		t.Fatal(e)
	}
	terms, e := os.ReadFile("/repo/text/terms.zh-Hant.tsv")
	if e != nil {
		t.Fatal(e)
	}
	c, e := loadDialogCatalog(corpus, terms, game, "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a", nil)
	if e != nil {
		t.Fatal(e)
	}
	lines := func(a ...string) []runLine {
		out := make([]runLine, len(a))
		for i, s := range a {
			out[i].text = s
		}
		return out
	}
	for _, test := range []struct {
		ls  []runLine
		ids []string
		zh  []string
	}{
		{lines("Sentry.", "Anchor in harbor (\"Fortify\").", "Unload all cargo.", "No changes."), []string{"3", "4", "5", "6"}, []string{"警戒。", "在港口下錨（「駐守」）。", "卸下所有貨物。", "不做更動。"}},
		{lines("Clear orders.", "Sentry.", "No changes."), []string{"2", "3", "6"}, []string{"清除命令。", "警戒。", "不做更動。"}},
	} {
		group := c.observedShipOptions(test.ls)
		if len(group) != len(test.ls) {
			t.Fatal("完整組合未匹配", test.ls)
		}
		for i, l := range test.ls {
			hit, zh, why := c.matchIn(group[i:i+1], l.text)
			if why != "" || hit.id != "GAME.TXT:@SHIPOPTIONS:0x00009AC0#"+test.ids[i] || zh != test.zh[i] {
				t.Fatal(i, hit, zh, why)
			}
		}
	}
	for _, ls := range [][]runLine{
		lines("Move to front.", "Clear orders.", "Sentry.", "Anchor in harbor (\"Fortify\").", "Unload all cargo.", "No changes."),
		lines("Clear orders.", "Anchor in harbor (\"Fortify\").", "No changes."),
		lines("Clear orders.", "Sentry.", "Unload all cargo.", "No changes."),
		lines("Sentry.", "Unload all cargo.", "No changes."),
		lines("Sentry.", "Clear orders.", "No changes."),
		lines("Sentry.", "Anchor in harbor (\"Fortify\").", "Unload all cargo."),
	} {
		if c.observedShipOptions(ls) != nil {
			t.Fatal("未觀測完整組合被接受", ls)
		}
	}
	hit, _, why := c.matchIn(c.lines, "No changes.")
	if why != "" || hit.id != "GAME.TXT:@UNITOPTIONS:0x00009A64#5" {
		t.Fatal("士兵尾列來源改變", hit, why)
	}
}

func TestIndexedLineFallbackSourceRole(t *testing.T) {
	d := &dialogRuntime{lineFallbackAt: func(text string, index int) (string, bool) {
		if text == "Same" && index == 0 {
			return "港口", true
		}
		return "", false
	}, lineFallback: func(text string) (string, bool) { return text, true }}
	if zh, ok := d.fallbackLine("Same", 0); !ok || zh != "港口" {
		t.Fatal(zh, ok)
	}
	for _, index := range []int{1, 2, -1} {
		if zh, ok := d.fallbackLine("Same", index); !ok || zh != "Same" {
			t.Fatal(index, zh, ok)
		}
	}
	d.lineFallbackAt = nil
	if zh, ok := d.fallbackLine("Same", 0); !ok || zh != "Same" {
		t.Fatal("legacy fallback", zh, ok)
	}
	d.lineFallback = nil
	if _, ok := d.fallbackLine("Same", 0); ok {
		t.Fatal("missing providers")
	}
}

func TestDialogOptionSourceGroups(t *testing.T) {
	c := dialogFixture(t)
	group := c.messageOptions["GAME.TXT:@A"]
	if len(group) != 2 || group[0].id != "GAME.TXT:@A#1" || group[1].id != "GAME.TXT:@A#2" {
		t.Fatalf("完整來源組：%+v", group)
	}
	for i, want := range []string{"是", "否"} {
		shown := []string{"Yes", "No"}[i]
		c.lines = append(c.lines, makeDialogTemplate("unrelated", shown, "別的選項", false))
		if _, _, why := c.matchIn(c.lines, shown); why != "template-not-unique" {
			t.Fatal("未限定來源不應解開歧義", why)
		}
		tp, zh, why := c.matchIn(group[i:i+1], shown)
		if why != "" || zh != want || tp.id != group[i].id {
			t.Fatal("來源組不應借別的譯文", zh, why)
		}
	}
	if len(c.messageOptions["GAME.TXT:@B"]) != 0 || len(c.messageOptions["GAME.TXT:@C"]) != 0 {
		t.Fatal("無選項或未載入正文不應建立選項組")
	}
	if _, _, why := c.matchIn(group[0:1], "Unknown"); why != "no-template" {
		t.Fatal("未知選項被翻譯", why)
	}
}
