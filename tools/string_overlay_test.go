package main

import (
	"crypto/sha256"
	"fmt"
	"image"
	"strings"
	"testing"
)

// 以自製假檔案與假字型測試，不含原版文字。
func stringFixture(t *testing.T) *stringCatalog {
	t.Helper()
	labels := []byte("@X\r\nDoor:\r\nNo Boats Here\r\n")
	colonyTxt := []byte("@A\r\nFooville, 1600\r\n")
	sum := func(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
	head := "message_id\tsource_file\tsource_file_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_en\tzh_hant\tstatus\tnotes\n"
	corpus := head
	for _, f := range []struct {
		off, n int
		zh     string
	}{{4, 5, "門："}, {11, 13, "這裡沒有船"}} {
		raw := labels[f.off : f.off+f.n]
		corpus += strings.Join([]string{"L:" + string(raw), "LABELS.TXT", sum(labels), fmt.Sprintf("0x%X", f.off), fmt.Sprint(f.n), sum(raw), string(raw), f.zh, "draft", ""}, "\t") + "\n"
	}
	sea := "candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_byte_length\tsource_bytes_sha256\tsource_text\tzh_hant\trole\tstatus\tnotes\n"
	draft := "candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_bytes_sha256\tsource_byte_length\tzh_hant\tstatus\tnotes\n"
	rec := colonyTxt[4:18]
	colony := "message_id\tsource_member_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_name\tzh_hant\n" +
		strings.Join([]string{"C:0", sum(colonyTxt), "0x4", "14", sum(rec), "Fooville", "福村（Fooville，1600）"}, "\t") + "\n"
	templates := "template_id\tpattern_en\tzh_hant\tevidence\tstatus\tnotes\n" +
		"title\t{colony}.  {w1} {n1}\t{colony}　{n1}年{w1}\t假\tdraft\t\n" +
		"paren\t({w1})\t（{w1}）\t假\tdraft\t\n"
	dlg := &dialogCatalog{terms: map[string]string{"Winter": "冬季", "Swamp": "沼澤"}}
	c, err := loadStringCatalog(dlg, []byte(templates), []byte(sea), []byte(corpus), []byte(draft), []byte(colony),
		map[string][]byte{"LABELS.TXT": labels, "COLONY.TXT": colonyTxt})
	if err != nil {
		t.Fatal(err)
	}
	return c
}

func TestStringTranslate(t *testing.T) {
	c := stringFixture(t)
	for _, tc := range []struct{ in, want, why string }{
		{"Fooville.  Winter 1601", "福村（Fooville）　1601年冬季", ""},
		{"Barton.  Winter 1601", "Barton　1601年冬季", ""}, // 玩家自訂名保持原樣
		{"(Swamp)", "（沼澤）", ""},
		{"No Boats Here ", "這裡沒有船", ""},
		{"Fooville", "福村（Fooville）", ""},
		{"(Desert)", "", "no-template"},
		{"Fooville.  Summer 1601", "", "no-template"},
	} {
		zh, _, why := c.translate(tc.in)
		if zh != tc.want || why != tc.why {
			t.Errorf("%q → %q %q", tc.in, zh, why)
		}
	}
	c.owned["Door:"] = true
	if !c.isOwned("( Door: )") || !c.isOwned("Door: ") || c.isOwned("(Door") {
		t.Fatal("專屬欄位判定不符")
	}
	c.addFrag("Door:", "別的譯名")
	if _, _, why := c.translate("Door:"); why != "no-template" {
		t.Fatal("片段衝突應視為查無")
	}
}

func TestStringCatalogRejectsWrongVersion(t *testing.T) {
	labels := []byte("@X\r\nDoor:\r\n")
	corpus := "message_id\tsource_file\tsource_file_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_en\tzh_hant\tstatus\tnotes\n" +
		strings.Join([]string{"L", "LABELS.TXT", strings.Repeat("0", 64), "0x4", "5", strings.Repeat("0", 64), "Door:", "門：", "draft", ""}, "\t") + "\n"
	head := func(cols string) []byte { return []byte(cols + "\n") }
	_, err := loadStringCatalog(&dialogCatalog{terms: map[string]string{}}, head("template_id\tpattern_en\tzh_hant\tevidence\tstatus\tnotes"),
		head("candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_byte_length\tsource_bytes_sha256\tsource_text\tzh_hant\trole\tstatus\tnotes"),
		[]byte(corpus), head("candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_bytes_sha256\tsource_byte_length\tzh_hant\tstatus\tnotes"),
		head("message_id\tsource_member_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_name\tzh_hant"),
		map[string][]byte{"LABELS.TXT": labels})
	if err == nil {
		t.Fatal("版本不符應失敗")
	}
}

func stringTestFonts(c *stringCatalog, chars string) {
	c.fonts = map[int]*dialogFont{}
	for size := stringFloorPx; size <= stringFontPx; size++ {
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

func TestStringStartPx(t *testing.T) {
	for _, tc := range [][3]int{{5, 22, 15}, {7, 30, 20}} {
		if s, f := stringStartPx(tc[0]); s != tc[1] || f != tc[2] {
			t.Errorf("字高 %d：%d／%d", tc[0], s, f)
		}
	}
}

var fixtureStep uint64 = 100

// 模擬一串「Door:」：五個字元各寫一點墨跡，讀到 0 完成；步數逐次遞增。
func stringRunFixture(s *stringRuntime, x0, y0 int, color byte, canvas []byte) *stringRun {
	var done *stringRun
	for i, ch := range []byte("Door:\x00") {
		fixtureStep += 10
		if r := s.onRead(uint32(0x1000+i), ch, fixtureStep); r != nil {
			done = r
			break
		}
		for dy := 0; dy < 5; dy++ {
			p := (y0+dy)*320 + x0 + i*4
			s.onWrite(p, canvas[p], color, true, false)
			canvas[p] = color
		}
	}
	return done
}

func TestStringRuntime(t *testing.T) {
	c := stringFixture(t)
	stringTestFonts(c, "門：")
	s := &stringRuntime{cat: c, misses: map[string]int{}}
	canvas := make([]byte, 64000)
	for i := range canvas {
		canvas[i] = 7
	}
	r := stringRunFixture(s, 40, 20, 68, canvas)
	if r == nil || string(r.text) != "Door:" || len(r.boxes) != 5 {
		t.Fatalf("應完成一串：%+v", r)
	}
	it, why := s.finish(r, canvas, 200, image.Rectangle{})
	if it == nil {
		t.Fatal(why)
	}
	if it.zh != "門：" || it.color != 68 || !it.safe.Eq(image.Rect(39, 19, 58, 26)) || it.size != 22 || it.shadowOff != 0 {
		t.Fatalf("項目不符：%q %d %v %d", it.zh, it.color, it.safe, it.size)
	}
	for i, v := range it.before {
		if v != 7 {
			t.Fatalf("印前底圖應還原文字像素：%d=%d", i, v)
		}
	}
	s.add(it)
	vga := append([]byte(nil), canvas...)
	none := image.Rect(-10, -10, -9, -9)
	if ch := s.step(canvas, vga, none, 300, true); len(ch) != 1 || ch[0][1] != "active" {
		t.Fatalf("真 VGA 相同即啟用：%v", ch)
	}
	canvas[20*320+40] = 1 // 例如對話框蓋上
	if ch := s.step(canvas, vga, none, 400, true); len(ch) != 1 || ch[0][1] != "suspended" {
		t.Fatalf("畫布改變應暫停：%v", ch)
	}
	canvas[20*320+40] = 68 // 原版整塊還原
	if ch := s.step(canvas, vga, none, 500, true); len(ch) != 1 || ch[0][1] != "active" {
		t.Fatalf("畫布還原應恢復：%v", ch)
	}
	canvas[20*320+40] = 1
	if ch := s.step(canvas, vga, image.Rect(38, 18, 45, 25), 600, true); len(ch) != 0 {
		t.Fatal("游標範圍內的改變不算")
	}
	if ch := s.step(canvas, vga, none, 700, false); len(ch) != 1 || ch[0][1] != "expired" || len(s.items) != 0 {
		t.Fatal("影像模式改變應撤銷")
	}
}

func TestStringFinishRejects(t *testing.T) {
	c := stringFixture(t)
	stringTestFonts(c, "門：")
	s := &stringRuntime{cat: c, misses: map[string]int{}}
	canvas := make([]byte, 64000)
	r := stringRunFixture(s, 40, 20, 68, canvas)
	r.colors[15] = 1
	if _, why := s.finish(r, canvas, 0, image.Rectangle{}); why != "multi-color" {
		t.Fatal(why)
	}
	delete(r.colors, 15)
	r.others = image.Rect(45, 21, 46, 22)
	if _, why := s.finish(r, canvas, 0, image.Rectangle{}); why != "other-writer" {
		t.Fatal(why)
	}
	r.others = image.Rectangle{}
	c.owned["Door:"] = true
	if _, why := s.finish(r, canvas, 0, image.Rectangle{}); why != "owned-by-field" {
		t.Fatal(why)
	}
	delete(c.owned, "Door:")
	// 狀態欄樣式：安全區延伸到欄右緣並畫陰影。
	it, why := s.finish(r, canvas, 0, image.Rect(0, 0, 320, 200))
	if it == nil || it.shadowOff != 2 || it.safe.Max.X != 58 {
		t.Fatalf("狀態欄樣式不符：%v %s", it, why)
	}
	stringTestFonts(c, "門")
	if _, why := s.finish(r, canvas, 0, image.Rectangle{}); why != "does-not-fit" {
		t.Fatal("圖集缺字應回原文：" + why)
	}
	// 單字元（逐字模式的「字元、0」）不處理。
	s2 := &stringRuntime{cat: c, misses: map[string]int{}}
	s2.onRead(0x2000, 'A', 1)
	if r := s2.onRead(0x2001, 0, 2); r == nil {
		t.Fatal("應完成單字元串")
	} else if it, why := s2.finish(r, canvas, 0, image.Rectangle{}); it != nil || why != "" {
		t.Fatal("單字元串應略過")
	}
}

func TestStringAddSupersede(t *testing.T) {
	s := &stringRuntime{}
	a := &stringItem{ink: image.Rect(242, 100, 300, 105), safe: image.Rect(241, 99, 320, 106)}
	b := &stringItem{ink: image.Rect(243, 107, 263, 112), safe: image.Rect(242, 106, 320, 113)}
	if d := s.add(a); len(d) != 0 {
		t.Fatal(d)
	}
	if d := s.add(b); len(d) != 0 {
		t.Fatal("相鄰兩行安全區相接不算同位置重印")
	}
	c := &stringItem{ink: image.Rect(242, 100, 280, 105), safe: image.Rect(241, 99, 281, 106)}
	if d := s.add(c); len(d) != 1 || d[0] != a || len(s.items) != 2 {
		t.Fatal("墨跡重疊應撤銷舊項目")
	}
}

func TestStringJoinHotkey(t *testing.T) {
	c := stringFixture(t)
	stringTestFonts(c, "門：(D)")
	s := &stringRuntime{cat: c, misses: map[string]int{}}
	canvas := make([]byte, 64000)
	mk := func(text string, x0 int, color byte, base uint32, step uint64) *stringRun {
		var done *stringRun
		for i, ch := range []byte(text + "\x00") {
			if r := s.onRead(base+uint32(i), ch, step+uint64(i)); r != nil {
				done = r
				break
			}
			for dy := 0; dy < 5; dy++ {
				p := (20+dy)*320 + x0 + i*8
				s.onWrite(p, canvas[p], color, true, false)
			}
		}
		return done
	}
	k := mk("D", 40, 14, 0x3000, 100)
	if s.join(k) != nil || s.key == nil {
		t.Fatal("單字母應暫存")
	}
	rest := mk("oor:", 44, 15, 0x3100, 110)
	m := s.join(rest)
	if m == nil || string(m.text) != "Door:" || m.keyColor != 14 || len(m.colors) != 1 {
		t.Fatalf("應合併：%+v", m)
	}
	it, why := s.finish(m, canvas, 200, image.Rectangle{})
	if it == nil || it.zh != "(D)門：" || it.accentColor != 14 || it.color != 15 || it.accent == nil {
		t.Fatalf("熱鍵按鈕：%v %s", it, why)
	}
	// 間隔太遠或同色則不合併。
	s.join(mk("D", 40, 14, 0x3000, 300))
	if m := s.join(mk("oor:", 60, 15, 0x3100, 310)); m.keyColor != 0 {
		t.Fatal("不相鄰不應合併")
	}
}

func TestStringPersonSlot(t *testing.T) {
	names := []byte("@LEADERNAME\r\nAnn Bee,   1, 0, 0\r\n\r\n@OTHER\r\nNot Person, 1\r\n")
	head := func(cols string) []byte { return []byte(cols + "\n") }
	c, err := loadStringCatalog(&dialogCatalog{terms: map[string]string{}},
		[]byte("template_id\tpattern_en\tzh_hant\tevidence\tstatus\tnotes\np\t{person}'s\t{person}的\t假\tdraft\t\n"),
		head("candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_byte_length\tsource_bytes_sha256\tsource_text\tzh_hant\trole\tstatus\tnotes"),
		head("message_id\tsource_file\tsource_file_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_en\tzh_hant\tstatus\tnotes"),
		head("candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_bytes_sha256\tsource_byte_length\tzh_hant\tstatus\tnotes"),
		head("message_id\tsource_member_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_name\tzh_hant"),
		map[string][]byte{"NAMES.TXT": names})
	if err != nil {
		t.Fatal(err)
	}
	if zh, _, why := c.translate("Ann Bee's "); zh != "Ann Bee的" || why != "" {
		t.Fatalf("%q %q", zh, why)
	}
	if _, _, why := c.translate("Not Person's"); why != "no-template" {
		t.Fatal("只收元首段的名字")
	}
}

func TestStringOutline(t *testing.T) {
	c := stringFixture(t)
	stringTestFonts(c, "門：")
	s := &stringRuntime{cat: c, misses: map[string]int{}}
	canvas := make([]byte, 64000)
	for i := range canvas {
		canvas[i] = 7
	}
	var r *stringRun
	for n, off := range [][2]int{{0, 1}, {1, 0}, {1, 1}} {
		color := byte(0)
		if n == 2 {
			color = 67
		}
		copyRun := stringRunFixture(s, 40+off[0], 20+off[1], color, canvas)
		r = s.outline(copyRun)
	}
	if !r.outline || r.outlineC != 0 || len(r.colors) != 1 {
		t.Fatalf("三次位移重印應併成描邊字：%+v", r)
	}
	it, why := s.finish(r, canvas, 300, image.Rectangle{})
	if it == nil || it.color != 67 || it.shadowColor != 0 || !it.ink.Eq(image.Rect(40, 20, 58, 26)) {
		t.Fatalf("描邊字項目不符：%v %s", it, why)
	}
	for i, v := range it.before {
		if v != 7 {
			t.Fatalf("三次重印的文字像素都應還原：%d=%d", i, v)
		}
	}
	// 位移超過 1 像素不併。
	s.last = nil
	s.outline(stringRunFixture(s, 40, 20, 0, canvas))
	if m := s.outline(stringRunFixture(s, 43, 20, 67, canvas)); m.outline {
		t.Fatal("位移過大不應合併")
	}
}
