package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"image"
	"os"
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

func TestSavannahRequiresVisiblePediaHeader(t *testing.T) {
	c := stringFixture(t)
	c.colony["Savannah"] = "薩凡納（Savannah）"
	c.colony["Fooville"] = "福村"
	c.dlg.terms["Savannah"] = "熱帶草原"
	s := &stringRuntime{cat: c}
	canvas := make([]byte, 64000)
	header := &stringItem{text: "ENCYCLOPEDIA OF COLONIZATION", safe: image.Rect(4, 1, 8, 3)}
	for y := 1; y < 3; y++ {
		for x := 4; x < 8; x++ {
			canvas[y*320+x] = 68
		}
	}
	header.after = stringRect(canvas, header.safe)
	check := func(want string) {
		t.Helper()
		zh, _, why := s.translateObserved("Savannah", canvas)
		if zh != want || why != "" {
			t.Fatalf("%q %q，預期%q", zh, why, want)
		}
	}
	check("薩凡納（Savannah）") // 其他場景仍是殖民地名称。
	s.items = []*stringItem{header}
	check("熱帶草原")
	if zh, _, _ := s.translateObserved("Fooville", canvas); zh != "福村" {
		t.Fatal("不可改變其他殖民地名稱")
	}
	canvas[320+4] = 0
	check("薩凡納（Savannah）") // 標題被重畫，不可沿用舊場景。
	canvas[320+4] = 68
	header.safe = image.Rectangle{}
	check("薩凡納（Savannah）")
	header.safe = image.Rect(4, 1, 8, 3)
	s.items = nil
	check("薩凡納（Savannah）") // 已移除的標題不可被沿用。
	s.items = []*stringItem{header}
	delete(c.dlg.terms, "Savannah")
	check("薩凡納（Savannah）") // 缺地形譯名仍使用既有回退。
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

func TestPediaPrerequisiteDelayedScreenCopy(t *testing.T) {
	// 重現原版最長2,351,390步的延遲；只測觀測守門，不代替DOS正常路徑。
	const position = 20*320 + 40
	none := image.Rect(-10, -10, -9, -9)
	fixture := func(id string) (*stringRuntime, []byte, []byte) {
		canvas, vga := make([]byte, 64000), make([]byte, 64000)
		canvas[position] = 68
		it := &stringItem{id: id, safe: image.Rect(40, 20, 41, 21), after: []byte{68},
			phase: "waiting-screen", complete: 100}
		return &stringRuntime{items: []*stringItem{it}}, canvas, vga
	}
	s, canvas, vga := fixture("STRING:template:pedia-prerequisite")
	if ch := s.step(canvas, vga, none, 100+2351390, true); len(ch) != 0 || len(s.items) != 1 {
		t.Fatal("本欄須等到已觀測的原版同步延遲")
	}
	copy(vga, canvas)
	if ch := s.step(canvas, vga, none, 100+2351391, true); len(ch) != 1 || ch[0][1] != "active" {
		t.Fatal("真VGA同步後應啟用")
	}
	// 原版先印標題，再組装整頁；完成的文字不能因螢幕尚未同步而丟失。
	for _, id := range []string{"STRING:dictionary:Door", "STRING:template:pedia-prerequisite"} {
		late, c, v := fixture(id)
		if ch := late.step(c, v, none, 100+100000000, true); len(ch) != 0 || len(late.items) != 1 || late.accepted != 0 {
			t.Fatal("未同步只能保留，不能顯示或丟棄")
		}
		copy(v, c)
		if ch := late.step(c, v, none, 100+100000001, true); len(ch) != 1 || ch[0][1] != "active" || late.accepted != 1 {
			t.Fatal("實際VGA同步後須顯示完整文字")
		}
	}
	changed, c, v := fixture("STRING:template:pedia-prerequisite")
	c[position] = 69
	if ch := changed.step(c, v, none, 101, true); len(ch) != 1 || ch[0][2] != "canvas-changed-before-screen" {
		t.Fatal("畫布改變不可藉等待裕度繼續保留")
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

func TestStringAmbiguousSame(t *testing.T) {
	c := stringFixture(t)
	for _, row := range [][3]string{{"a", "{w1} ({n1} Boats)", "{w1}（{n1} 船）"}, {"b", "{w1} ({n1} {w2})", "{w1}（{n1} {w2}）"}} {
		tpl, err := makeStringTemplate(row[0], row[1], row[2])
		if err != nil {
			t.Fatal(err)
		}
		c.templates = append(c.templates, tpl)
	}
	c.addFrag("Boats", "船")
	if zh, _, why := c.translate("Door: (2 Boats)"); why != "" || zh != "門：（2 船）" {
		t.Fatalf("相同譯文的多列命中應接受：%q %q", zh, why)
	}
	c.addFrag("Carts", "車")
	c.templates = append(c.templates, func() stringTemplate {
		x, _ := makeStringTemplate("c", "{w1} ({n1} Carts)", "{w1}有{n1}車")
		return x
	}())
	if _, _, why := c.translate("Door: (2 Carts)"); why != "ambiguous-template" {
		t.Fatal("譯文不同的多列命中仍應視為不明確：" + why)
	}
}

// 目標178：地圖殖民地名稱標籤畫在離屏緩衝區（位移與畫布一致），雙色字：外框 0、填色 15。
func labelRunFixture(s *stringRuntime, text string, x0, y0 int, b2 []byte) *stringRun {
	var done *stringRun
	for i, ch := range append([]byte(text), 0) {
		fixtureStep += 10
		if r := s.onRead(uint32(0x2000+i), ch, fixtureStep); r != nil {
			done = r
			break
		}
		for dy := 0; dy < 7; dy++ {
			// 每字寬 4：填色 15 在中間兩欄，外框 0 在兩側。
			for dx, v := range []byte{0, 15, 15, 0} {
				p := (y0+dy)*320 + x0 + i*4 + dx
				s.onWriteBuf(p, b2[p], v, true)
				b2[p] = v
			}
		}
	}
	return done
}

// labelTestFonts 假字型：漢字與全形括號寬一個字級，拉丁字母寬半個字級（與真字型的比例相近）。
func labelTestFonts(c *stringCatalog, chars string) {
	stringTestFonts(c, chars)
	for size, f := range c.fonts {
		for r := range f.widths {
			if r < 0x100 {
				f.widths[r] = size / 2
			}
		}
	}
}

func TestStringLabel(t *testing.T) {
	c := stringFixture(t)
	c.colony["Fooville"] = "福村（Fooville）"
	labelTestFonts(c, "福村（Fooville）")
	s := &stringRuntime{cat: c, misses: map[string]int{}}
	b2 := make([]byte, 64000)
	for i := range b2 {
		b2[i] = 60
	}
	canvas := append([]byte(nil), b2...)
	r := labelRunFixture(s, "Fooville", 100, 130, b2)
	if r == nil || !r.buf2 || r.mixed || len(r.colors) != 2 {
		t.Fatalf("緩衝區串：%+v", r)
	}
	it, why := s.finishLabel(r, b2, canvas, 1000)
	if it == nil {
		t.Fatal(why)
	}
	if it.phase != "waiting-copy" || it.zh != "福村（Fooville）" || it.color != 15 || it.shadowColor != 0 || it.shadow == nil || it.norm == nil {
		t.Fatalf("項目不符：%+v", it)
	}
	if !it.safe.In(stringMapView) || !it.safe.Overlaps(it.ink) {
		t.Fatalf("安全區 %v", it.safe)
	}
	// 中文以原版填色墨跡的水平中心置中：中心在 x=100+16 處。
	mid := (it.safe.Min.X*4 + it.norm.Rect.Dx()/2) / 4
	if d := mid - 116; d < -3 || d > 3 {
		t.Fatalf("置中偏差：安全區 %v 中心 %d", it.safe, mid)
	}
	for i, v := range it.before {
		if v != 60 {
			t.Fatalf("印前底圖應還原標籤像素：%d=%d", i, v)
		}
	}
	// waiting-copy：畫布還沒有標籤時等待；搬上畫布後進入 waiting-screen，真 VGA 相同即啟用。
	s.add(it)
	vga := append([]byte(nil), canvas...)
	none := image.Rect(-10, -10, -9, -9)
	if ch := s.step(canvas, vga, none, 1100, true); len(ch) != 0 || it.phase != "waiting-copy" {
		t.Fatalf("畫布尚無標籤應等待：%v %s", ch, it.phase)
	}
	copy(canvas, b2)
	if ch := s.step(canvas, vga, none, 1200, true); len(ch) != 0 || it.phase != "waiting-screen" {
		t.Fatalf("搬上畫布後等真 VGA：%v %s", ch, it.phase)
	}
	copy(vga, canvas)
	if ch := s.step(canvas, vga, none, 1300, true); len(ch) != 1 || ch[0][1] != "active" {
		t.Fatalf("真 VGA 相同即啟用：%v", ch)
	}
	// 規格038 READY：3M未完整搬上畫布時只暫停，仍禁止啟用。
	s2 := &stringRuntime{cat: c, misses: map[string]int{}}
	it2, _ := s2.finishLabel(r, b2, canvas, 5000)
	s2.add(it2)
	blank := make([]byte, 64000)
	if ch := s2.step(blank, blank, none, 5000+3000001, true); len(ch) != 1 || ch[0][1] != "suspended-copy" || ch[0][2] != "canvas-copy-occluded" || len(s2.items) != 1 || s2.accepted != 0 {
		t.Fatalf("逾時應暫停並禁止啟用：%v", ch)
	}
}

func TestStringLabelRejects(t *testing.T) {
	c := stringFixture(t)
	c.colony["Fooville"] = "福村（Fooville）"
	labelTestFonts(c, "福村（Fooville）")
	mk := func(text string, x0 int) (*stringRuntime, *stringRun, []byte) {
		s := &stringRuntime{cat: c, misses: map[string]int{}}
		b2 := make([]byte, 64000)
		return s, labelRunFixture(s, text, x0, 130, b2), b2
	}
	// 玩家自訂名（不等於預設名）：保持原樣。
	s, r, b2 := mk("Barville", 100)
	if _, why := s.finishLabel(r, b2, b2, 0); why != "no-template" {
		t.Fatalf("非預設名：%q", why)
	}
	// 兩色以外：回原文。
	s, r, b2 = mk("Fooville", 100)
	r.colors[7] = 1
	if _, why := s.finishLabel(r, b2, b2, 0); why != "label-colors" {
		t.Fatalf("三色：%q", why)
	}
	delete(r.colors, 7)
	delete(r.colors, 0)
	r.colors[9] = 3 // 沒有外框色 0
	if _, why := s.finishLabel(r, b2, b2, 0); why != "label-colors" {
		t.Fatalf("缺外框色：%q", why)
	}
	// 同時有畫布與緩衝區墨跡：回原文。
	s, r, b2 = mk("Fooville", 100)
	r.mixed = true
	if _, why := s.finishLabel(r, b2, b2, 0); why != "mixed-buffers" {
		t.Fatalf("混合緩衝區：%q", why)
	}
	// 貼近地圖視窗右緣：中文比原版寬，超出視窗時回原文（安全區必須在地圖視窗內）。
	s, r, b2 = mk("Fooville", 205)
	if it, why := s.finishLabel(r, b2, b2, 0); it != nil || why != "does-not-fit" {
		t.Fatalf("超出地圖視窗：%v %q", it, why)
	}
	// 圖集缺字。
	labelTestFonts(c, "福村")
	s, r, b2 = mk("Fooville", 100)
	if _, why := s.finishLabel(r, b2, b2, 0); why != "does-not-fit" {
		t.Fatalf("缺字：%q", why)
	}
}

// 目標178：同一串的畫布與緩衝區墨跡混在一起時標記 mixed；畫布串不受緩衝區非墨跡寫入影響。
func TestStringWriteBuffers(t *testing.T) {
	s := &stringRuntime{}
	s.onRead(0x3000, 'A', 1)
	s.onWriteBuf(5, 0, 15, false) // 非 0D21:012C 的緩衝區寫入：忽略
	if len(s.cur.firstOld) != 0 {
		t.Fatal("緩衝區的非墨跡寫入不應記錄")
	}
	s.onWrite(10, 0, 68, true, false)
	s.onWriteBuf(20, 0, 15, true)
	if !s.cur.mixed || s.cur.buf2 {
		t.Fatalf("畫布串出現緩衝區墨跡應標 mixed：%+v", s.cur)
	}
}

func TestColonyDelayedCopyRetention(t *testing.T) {
	none := image.Rect(-10, -10, -9, -9)
	const pos = 20*320 + 40
	fixture := func(id string) (*stringRuntime, []byte, []byte) {
		c, v := make([]byte, 64000), make([]byte, 64000)
		c[pos], v[pos] = 68, 68
		it := &stringItem{id: id, safe: image.Rect(40, 20, 42, 21), ink: image.Rect(40, 20, 42, 21),
			after: []byte{68, 68}, before: []byte{0, 0}, phase: "waiting-copy", complete: 100}
		return &stringRuntime{items: []*stringItem{it}}, c, v
	}
	s, c, v := fixture("STRING:colony")
	if ch := s.step(c, v, none, 3000101, true); len(ch) != 1 || ch[0][1] != "suspended-copy" || len(s.items) != 1 || s.accepted != 0 {
		t.Fatal("部分複製逾時須保留而不啟用")
	}
	if ch := s.step(c, v, none, 5000000, true); len(ch) != 0 || s.items[0].phase != "suspended-copy" {
		t.Fatal("仍被遮擋不得繪製")
	}
	c[pos+1] = 68
	if ch := s.step(c, v, none, 5000001, true); len(ch) != 0 || s.items[0].phase != "waiting-screen" {
		t.Fatal("畫布完整後仍須等VGA")
	}
	v[pos+1] = 68
	if ch := s.step(c, v, none, 5000002, true); len(ch) != 1 || ch[0][1] != "active" || s.accepted != 1 {
		t.Fatal("兩側完整才啟用")
	}

	ordinary, c, v := fixture("STRING:other")
	if ch := ordinary.step(c, v, none, 3000101, true); len(ch) != 1 || ch[0][2] != "canvas-copy-timeout" || len(ordinary.items) != 0 {
		t.Fatal("其他候選仍須逾時撤銷")
	}
	mode, c, v := fixture("STRING:colony")
	mode.step(c, v, none, 3000101, true)
	if ch := mode.step(c, v, none, 3000102, false); len(ch) != 1 || ch[0][2] != "mode-changed" || len(mode.items) != 0 {
		t.Fatal("模式改變須撤銷暫停來源")
	}
	newer, c, v := fixture("STRING:colony")
	old := newer.items[0]
	newer.step(c, v, none, 3000101, true)
	fresh := &stringItem{id: "STRING:new", ink: old.ink, safe: old.safe, phase: "waiting-screen"}
	if dropped := newer.add(fresh); len(dropped) != 1 || dropped[0] != old || len(newer.items) != 1 || newer.items[0] != fresh {
		t.Fatal("新印字須取代暫停來源")
	}
	late, c, v := fixture("STRING:colony")
	late.step(c, v, none, 3000101, true)
	c[pos+1] = 68
	late.step(c, v, none, 5000001, true)
	if ch := late.step(c, v, none, 7000002, true); len(ch) != 0 || late.items[0].phase != "waiting-screen" || late.accepted != 0 {
		t.Fatal("轉螢幕階段後保留完整字串，不提前繪製")
	}
	c[pos] = 0
	if ch := late.step(c, v, none, 7000003, true); len(ch) != 1 || ch[0][2] != "canvas-changed-before-screen" || len(late.items) != 0 {
		t.Fatal("等待中原版文字被清掉，必須撤銷")
	}
	c[pos], v[pos], v[pos+1] = 68, 68, 68
	if ch := late.step(c, v, none, 7000004, true); len(ch) != 0 || late.accepted != 0 {
		t.Fatal("被清掉的印字紀錄不能隨相同像素復活")
	}
}

// 規格035 SAVEGOOD：測試顯示字串形狀，不推定原版姓名或年份上限。
func TestSaveDescriptionGrammar(t *testing.T) {
	c := &stringCatalog{frags: map[string]string{"Discoverer": "難度A", "English": "國家A", "Spring": "季節A"}}
	for _, name := range []string{"Alice", "Anne-Marie O'Neil", "A (B)"} {
		got, ok := c.translateSaveDescription("Discoverer " + name + " of the English (Spring 1496)")
		want := "國家A難度A " + name + "（1496年季節A）"
		if !ok || got != want {
			t.Fatalf("%q => %q %v", name, got, ok)
		}
	}
	for _, bad := range []string{"Soldier Alice of the English (Spring 1496)", "Discoverer Alice of the Unknown (Spring 1496)", "Discoverer Alice of the English (Summer 1496)", "Discoverer %STRING0 of the English (Spring 1496)", "Discoverer {Alice} of the English (Spring 1496)", "Discoverer A\nB of the English (Spring 1496)", "Discoverer 中文 of the English (Spring 1496)"} {
		if _, ok := c.translateSaveDescription(bad); ok {
			t.Fatalf("不應接受 %q", bad)
		}
	}
	delete(c.frags, "Spring")
	if _, ok := c.translateSaveDescription("Discoverer Alice of the English (Spring 1496)"); ok {
		t.Fatal("缺譯名必須回原文")
	}
}

func slotSourceRow() map[string]string {
	return map[string]string{"candidate_id": slotEmptyID, "source_file": "VICEROY.EXE", "source_sha256": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3", "byte_offset": "0x0001FA8E", "source_byte_length": "7", "source_bytes_sha256": "9251e2d6e3d0ccd4ce35aa27a82a36251ad36af2cb17b229c34a3daa2f0cdaa7", "zh_hant": "（空白）"}
}

func TestSlotEmptySourceValidation(t *testing.T) {
	c := &stringCatalog{frags: map[string]string{}}
	for _, field := range []string{"source_file", "source_sha256", "byte_offset", "source_byte_length", "source_bytes_sha256"} {
		row := slotSourceRow()
		row[field] = "bad"
		if err := c.loadSlotEmpty([]map[string]string{row}, nil); err == nil || c.slotEmpty != "" {
			t.Fatalf("來源損壞未拒絕：%s", field)
		}
	}
	row := slotSourceRow()
	if err := c.loadSlotEmpty([]map[string]string{row, row}, nil); err == nil {
		t.Fatal("重複來源未拒絕")
	}
	for _, rows := range [][]map[string]string{nil, {row}} {
		if err := c.loadSlotEmpty(rows, nil); err != nil || c.slotEmpty != "" {
			t.Fatal("缺檔或缺列須維持原文", err)
		}
	}
	game, err := os.ReadFile("/game/VICEROY.EXE")
	if os.IsNotExist(err) {
		t.Skip("缺合法原版，來源正例略過")
	}
	if err != nil {
		t.Fatal(err)
	}
	files := map[string][]byte{"VICEROY.EXE": game}
	if err = c.loadSlotEmpty([]map[string]string{row}, files); err != nil || c.slotEmpty != "（空白）" {
		t.Fatal("真來源未載入", err)
	}
	if _, _, why := c.translate("(EMPTY)"); why == "" {
		t.Fatal("空槽進入通用字典")
	}
	for _, zh := range []string{"", "{空白}", "空白\n", "%STRING0"} {
		row := slotSourceRow()
		row["zh_hant"] = zh
		if err = c.loadSlotEmpty([]map[string]string{row}, files); err != nil {
			t.Fatal(err)
		}
		// 空白去除後仍可安全顯示，其他標記不可進入槽位。
		if zh != "空白\n" && c.slotEmpty != "" {
			t.Fatalf("不安全譯文 %q", zh)
		}
	}
	bad := append([]byte(nil), game...)
	bad[129678] ^= 1
	if err = c.loadSlotEmpty([]map[string]string{slotSourceRow()}, map[string][]byte{"VICEROY.EXE": bad}); err == nil {
		t.Fatal("全檔損壞未拒絕")
	}
}

func TestSlotDescriptionScope(t *testing.T) {
	c := &stringCatalog{slotEmpty: "（空白）", frags: map[string]string{"Discoverer": "難度A", "English": "國家A", "Spring": "季節A"}}
	for _, name := range []string{"Alice", "Anne-Marie O'Neil", "A (B)"} {
		input := "Discoverer " + name + " of the English, Spring 1496"
		got, ok := c.translateSaveSlot(input)
		if !ok || got != "國家A難度A "+name+"（1496年季節A）" {
			t.Fatal(input, got, ok)
		}
		if _, _, why := c.translate(input); why == "" {
			t.Fatal("逗號描述進入一般字串")
		}
		if _, ok := c.translateSaveDescription(input); ok {
			t.Fatal("逗號描述擴張 SAVEGOOD")
		}
	}
	for _, input := range []string{"Discoverer Alice of the English (Spring 1496)", "Soldier Alice of the English, Spring 1496", "Discoverer 中文 of the English, Spring 1496", "Discoverer {Alice} of the English, Spring 1496", "Discoverer %STRING0 of the English, Spring 1496", "Discoverer A\nB of the English, Spring 1496", "Discoverer Alice of the Unknown, Spring 1496", "Discoverer Alice of the English, Summer 1496"} {
		if _, ok := c.translateSaveSlot(input); ok {
			t.Fatal("未驗格式", input)
		}
	}
	delete(c.frags, "Spring")
	if _, ok := c.translateSaveSlot("Discoverer Alice of the English, Spring 1496"); ok {
		t.Fatal("缺季節仍翻譯")
	}
	c.slotEmpty = ""
	if _, ok := c.translateSaveSlot("(EMPTY)"); ok {
		t.Fatal("缺空槽列仍翻譯")
	}
}

func TestEuropeReportTemplateGuards(t *testing.T) {
	c := stringFixture(t)
	c.addFrag("Known Father", "定稿姓名")
	for _, q := range []struct{ id, pattern, zh string }{{"next-congress", "Next Continental Congress Session: ({w1})", "下次大陸議會會期：（{w1}）"}, {"rebel-score", "Rebel Sentiment:  +{n1}", "反叛情緒：+{n1}"}} {
		tpl, e := makeStringTemplate(q.id, q.pattern, q.zh)
		if e != nil {
			t.Fatal(e)
		}
		c.templates = append(c.templates, tpl)
	}
	for _, q := range []struct{ in, want string }{{"Next Continental Congress Session: (Known Father)", "下次大陸議會會期：（定稿姓名）"}, {"Rebel Sentiment:  +1", "反叛情緒：+1"}, {"Rebel Sentiment:  +0", "反叛情緒：+0"}} {
		z, _, why := c.translate(q.in)
		if why != "" || z != q.want {
			t.Fatal(q.in, z, why)
		}
	}
	for _, s := range []string{"Next Continental Congress Session: (Unknown)", "Rebel Sentiment: +1", "Rebel Sentiment:  -1", "Rebel Sentiment:  +"} {
		if _, _, why := c.translate(s); why == "" {
			t.Fatal("未知來源或語法未拒絕", s)
		}
	}
}

func TestCargoOriginAndSameNamedCity(t *testing.T) {
	signature := []byte{0xf2, 0xae, 0xf7, 0xd1, 0x2b, 0xf9, 0x8c, 0xc0, 0x8e, 0xd8, 0x8e, 0x46, 0x08, 0x87, 0xfe, 0x8b, 0x46, 0x06}
	const ss uint16 = 7274
	const bp uint16 = 59400
	makeMem := func() []byte {
		m := make([]byte, 1<<20)
		for p, v := range map[uint32]string{320325: "Loading", 320171: "moved to", 315996: "Furs", 316238: "Caravel", 140264: "Caravel", 116461: " ", 175798: "27"} {
			copy(m[p:], v)
		}
		return m
	}
	appendPart := func(a *cargoAssembly, m []byte, src uint32, code []byte) {
		pos := uint32(ss)*16 + uint32(bp)
		word := func(off uint32, v uint16) { m[pos+off] = byte(v); m[pos+off+1] = byte(v >> 8) }
		word(6, 11604)
		word(8, ss)
		if src >= uint32(ss)*16 && src < uint32(ss)*16+65536 {
			word(10, uint16(src-uint32(ss)*16))
			word(12, ss)
		} else {
			word(10, uint16(src%16))
			word(12, uint16(src/16))
		}
		a.observe(m, ss, bp, code)
		before, _ := cargoCString(m, 127988)
		value, _ := cargoCString(m, src)
		copy(m[127988:], before+value+"\x00")
	}
	cat := &stringCatalog{dlg: &dialogCatalog{unitCaptionNames: map[string]string{"Caravel": "輕帆船"}, terms: map[string]string{"Furs": "毛皮"}}, colony: map[string]string{"Jamestown": "詹姆斯敦（Jamestown）"}}
	for _, v := range [][3]string{{"cargo-moved-unit", "{n1} {w1} moved to {w2}", "{n1} {w1}已移動至{w2}"}, {"cargo-moved-city", "{n1} {w1} moved to {colony}", "{n1} {w1}已移動至{colony}"}, {"cargo-loading-commodity", "Loading {w1}", "裝載中{w1}"}} {
		tpl, err := makeStringTemplate(v[0], v[1], v[2])
		if err != nil {
			t.Fatal(err)
		}
		cat.templates = append(cat.templates, tpl)
	}
	s := &stringRuntime{cat: cat}
	for _, tc := range []struct {
		name       string
		source     uint32
		role, want string
	}{
		{"fixed-unit", 316238, "unit", "27 毛皮已移動至輕帆船"},
		{"same-named-player-city", 140264, "city", "27 毛皮已移動至Caravel"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			m := makeMem()
			a := cargoAssembly{}
			for _, src := range []uint32{175798, 116461, 315996, 116461, 320171, 116461, tc.source, 116461} {
				appendPart(&a, m, src, signature)
			}
			p := a.proof(m)
			if p.role != tc.role {
				t.Fatalf("role=%q", p.role)
			}
			r := &stringRun{text: []byte(p.text), cargo: p}
			zh, _, why, handled := s.cargoTranslate(r, image.Rect(116, 1, 202, 7), 5, 149)
			if zh != tc.want || why != "" || !handled {
				t.Fatalf("%q %q %v", zh, why, handled)
			}
			if _, _, reason := cat.translate(strings.TrimSpace(p.text)); reason == "" {
				t.Fatal("unobserved general translation accepted cargo")
			}
			r.cargo = cargoProof{}
			if _, _, reason, _ := s.cargoTranslate(r, image.Rect(116, 1, 202, 7), 5, 149); reason == "" {
				t.Fatal("missing provenance accepted")
			}
			r.cargo = p
			r.text = []byte("28 Furs moved to Caravel ")
			if _, _, reason, _ := s.cargoTranslate(r, image.Rect(116, 1, 202, 7), 5, 149); reason == "" {
				t.Fatal("different print accepted")
			}
			m[127988] = 'X'
			if a.proof(m).role != "" {
				t.Fatal("changed original buffer accepted")
			}
		})
	}
	for _, tc := range []struct {
		name    string
		seq     []uint32
		badCode bool
	}{
		{"unknown-source", []uint32{175798, 116461, 315996, 116461, 320171, 116461, 140300, 116461}, false},
		{"missing-space", []uint32{175798, 315996, 320171, 316238}, false},
		{"swapped-roles", []uint32{175798, 116461, 316238, 116461, 320171, 116461, 315996, 116461}, false},
		{"incomplete", []uint32{320325, 116461, 315996}, false},
		{"bad-instruction", []uint32{320325, 116461, 315996, 116461}, true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			m := makeMem()
			copy(m[140300:], "Caravel")
			a := cargoAssembly{}
			code := append([]byte(nil), signature...)
			if tc.badCode {
				code[0] = 0x90
			}
			for _, src := range tc.seq {
				appendPart(&a, m, src, code)
			}
			if a.proof(m).role != "" {
				t.Fatal("invalid sequence accepted")
			}
		})
	}
}

func TestCargoHeldSourceAndRectangle(t *testing.T) {
	indexed := make([]byte, 64000)
	for i := range indexed {
		indexed[i] = 57
	}
	safe := image.Rect(137, 0, 182, 8)
	item := stringItem{id: "STRING:template:cargo-loading-commodity", text: "Loading Furs ", phase: "active", size: 22, safe: safe, after: stringRect(indexed, safe)}
	if !cargoHeldAllowed(&item, indexed, image.Rect(138, 170, 154, 186), nil) {
		t.Fatal("complete isolated loading cue rejected")
	}
	tests := []struct {
		name    string
		change  func(*stringItem, []byte)
		cursor  image.Rectangle
		dialogs []image.Rectangle
	}{
		{"partial-original", func(_ *stringItem, b []byte) { b[137]++ }, image.Rectangle{}, nil},
		{"cursor-over-cue", func(_ *stringItem, _ []byte) {}, safe, nil},
		{"dialog-over-cue", func(_ *stringItem, _ []byte) {}, image.Rectangle{}, []image.Rectangle{safe}},
		{"unverified-id", func(p *stringItem, _ []byte) { p.id = "STRING:dictionary" }, image.Rectangle{}, nil},
		{"other-commodity", func(p *stringItem, _ []byte) { p.text = "Loading Ore " }, image.Rectangle{}, nil},
		{"suspended", func(p *stringItem, _ []byte) { p.phase = "suspended" }, image.Rectangle{}, nil},
		{"different-field", func(p *stringItem, _ []byte) { p.safe = p.safe.Add(image.Pt(0, 1)) }, image.Rectangle{}, nil},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			p := item
			b := append([]byte(nil), indexed...)
			tc.change(&p, b)
			if cargoHeldAllowed(&p, b, tc.cursor, tc.dialogs) {
				t.Fatal("unsafe held cue accepted")
			}
		})
	}
	if cargoHeldAllowed(&item, indexed[:10], image.Rectangle{}, nil) {
		t.Fatal("incomplete VGA accepted")
	}
}

func TestCargoMissingDialogDoesNotClaimOtherStrings(t *testing.T) {
	s := &stringRuntime{cat: &stringCatalog{}}
	if _, _, _, handled := s.cargoTranslate(&stringRun{text: []byte("Other ordinary text")}, image.Rectangle{}, 5, 149); handled {
		t.Fatal("ordinary text claimed by cargo")
	}
	if _, _, why, handled := s.cargoTranslate(&stringRun{text: []byte("Loading Furs ")}, image.Rect(138, 1, 181, 7), 5, 149); !handled || why == "" {
		t.Fatal("cargo accepted without name binding")
	}
}

func TestCargoPhraseDoesNotClaimOrdinarySentence(t *testing.T) {
	s := &stringRuntime{cat: &stringCatalog{}}
	for _, text := range []string{"Goods were moved to Jamestown", "The icon moved to the right", "Other ordinary text"} {
		if _, _, _, handled := s.cargoTranslate(&stringRun{text: []byte(text)}, image.Rectangle{}, 5, 149); handled {
			t.Fatalf("ordinary phrase claimed: %q", text)
		}
	}
}

func tradeContextFixture() (*stringRuntime, []byte) {
	canvas := make([]byte, 64000)
	cat := &stringCatalog{routeLand: "陸上", frags: map[string]string{"London": "倫敦", "England": "英格蘭"}}
	title := &stringItem{id: "STRING:template:route-editor-title", text: "EDIT TRADE ROUTE 1", safe: image.Rect(127, 4, 193, 11), color: 15, size: 22, phase: "active", after: make([]byte, 462)}
	return &stringRuntime{cat: cat, items: []*stringItem{title}}, canvas
}
func TestTradeLandContext(t *testing.T) {
	s, canvas := tradeContextFixture()
	if zh, ok := s.routeLandTranslate("Land", image.Rect(55, 33, 70, 38), 5, 15, canvas); !ok || zh != "陸上" {
		t.Fatalf("%q %v", zh, ok)
	}
	s.items[0].phase = "waiting-screen"
	if !s.routeEditorContext(canvas) {
		t.Fatal("complete native title may precede first frontend composition")
	}
	canvas[199*320] = 1
	if !s.routeEditorContext(canvas) {
		t.Fatal("unrelated native drawing invalidated title")
	}
}
func TestTradeLandWrongField(t *testing.T) {
	for _, v := range []struct {
		text  string
		rect  image.Rectangle
		cap   int
		color byte
	}{
		{"Land", image.Rect(55, 32, 70, 37), 5, 15}, {"Land", image.Rect(55, 33, 70, 38), 6, 15}, {"Land", image.Rect(55, 33, 70, 38), 5, 149}, {"Sea", image.Rect(55, 33, 70, 38), 5, 15},
	} {
		s, c := tradeContextFixture()
		if _, ok := s.routeLandTranslate(v.text, v.rect, v.cap, v.color, c); ok {
			t.Fatal(v)
		}
	}
	s, c := tradeContextFixture()
	s.cat.routeLand = ""
	if _, ok := s.routeLandTranslate("Land", image.Rect(55, 33, 70, 38), 5, 15, c); ok {
		t.Fatal("missing verified ROUTE fragment")
	}
}
func TestTradeContextStaleOriginal(t *testing.T) {
	cases := []func(*stringRuntime, []byte){
		func(s *stringRuntime, c []byte) { s.items[0].id = "STRING:dictionary" },
		func(s *stringRuntime, c []byte) { s.items[0].text = "EDIT TRADE ROUTE 2" },
		func(s *stringRuntime, c []byte) { s.items[0].phase = "expired" },
		func(s *stringRuntime, c []byte) { s.items[0].phase = "suspended" },
		func(s *stringRuntime, c []byte) { s.items[0].safe = image.Rect(126, 4, 193, 11) },
		func(s *stringRuntime, c []byte) { s.items[0].color = 149 },
		func(s *stringRuntime, c []byte) { s.items[0].size = 14 },
		func(s *stringRuntime, c []byte) { s.items[0].size = 23 },
		func(s *stringRuntime, c []byte) { s.items[0].after = nil },
		func(s *stringRuntime, c []byte) { c[4*320+127] = 1 },
		func(s *stringRuntime, c []byte) { s.cat = nil },
		func(s *stringRuntime, c []byte) { s.items = []*stringItem{nil} },
	}
	for i, mutate := range cases {
		s, c := tradeContextFixture()
		mutate(s, c)
		if s.routeEditorContext(c) {
			t.Fatalf("stale case %d accepted", i)
		}
	}
	s, _ := tradeContextFixture()
	if s.routeEditorContext(nil) {
		t.Fatal("invalid VGA")
	}
	var none *stringRuntime
	if none.routeEditorContext(make([]byte, 64000)) {
		t.Fatal("nil runtime")
	}
}
func TestTradePortContextAndTerms(t *testing.T) {
	s, c := tradeContextFixture()
	title := &dialogShown{id: "GAME.TXT:0x00001CBB", safe: image.Rect(66, 76, 176, 88), size: 30, phase: "waiting-screen", complete: 1000, items: []string{"Select a port to sail to:"}}
	if zh, ok := s.routePortTranslate("London (England)", 0, c, title, 1001); !ok || zh != "倫敦（英格蘭）" {
		t.Fatalf("%q %v", zh, ok)
	}
	for _, text := range []string{"London", "London (France)", "Paris (France)", "London (England) Run"} {
		if _, ok := s.routePortTranslate(text, 0, c, title, 1001); ok {
			t.Fatal(text)
		}
	}
	for i, mutate := range []func(*dialogShown){
		func(v *dialogShown) { v.id = "GAME.TXT:other" }, func(v *dialogShown) { v.safe.Min.X++ }, func(v *dialogShown) { v.phase = "expired" }, func(v *dialogShown) { v.size = 29 }, func(v *dialogShown) { v.complete = 2000 }, func(v *dialogShown) { v.items = nil },
	} {
		v := *title
		mutate(&v)
		if _, ok := s.routePortTranslate("London (England)", 0, c, &v, 1001); ok {
			t.Fatalf("port case %d", i)
		}
	}
	if _, ok := s.routePortTranslate("London (England)", 0, c, title, 2001000); ok {
		t.Fatal("old port title")
	}
	for _, index := range []int{-1, 1, 2, 100} {
		if _, ok := s.routePortTranslate("London (England)", index, c, title, 1001); ok {
			t.Fatalf("player city row %d borrowed port role", index)
		}
	}
	s.cat.frags["England"] = ""
	if _, ok := s.routePortTranslate("London (England)", 0, c, title, 1001); ok {
		t.Fatal("missing country source")
	}
}
func TestTradeCitySourceTemplates(t *testing.T) {
	for _, sample := range []struct{ id, verb, zh string }{
		{"GAME.TXT:@CARGOLOAD:0x0000862B", "load", "裝"},
		{"GAME.TXT:@CARGOUNLOAD:0x0000866E", "unload", "卸"},
	} {
		tpl := makeDialogTemplate(sample.id, "Select a cargo to "+sample.verb+" at {%STRING0}.", "請選擇{%STRING0}"+sample.zh+"貨。", false)
		c := &dialogCatalog{templates: []dialogTemplate{tpl}, terms: map[string]string{"Caravel": "輕帆船"}, colonyValue: func(v string) string {
			if v == "Jamestown" {
				return "詹姆斯敦（Jamestown）"
			}
			return v
		}}
		for _, v := range []struct{ name, want string }{{"Caravel", "Caravel"}, {"Jamestown", "詹姆斯敦（Jamestown）"}, {"My Port", "My Port"}} {
			_, zh, why := c.matchIn(c.templates, "Select a cargo to "+sample.verb+" at "+v.name+".")
			if why != "" || zh != "請選擇{"+v.want+"}"+sample.zh+"貨。" {
				t.Fatalf("%s %q %q", sample.id, zh, why)
			}
		}
		c.colonyValue = nil
		if _, _, why := c.matchIn(c.templates, "Select a cargo to "+sample.verb+" at Caravel."); why == "" {
			t.Fatal("missing colony provider used unit translation")
		}
	}
}

func TestTradeTitleSourceScope(t *testing.T) {
	tpl, e := makeStringTemplate("route-editor-title", "EDIT TRADE ROUTE {n1}", "編輯貿易路線 {n1}")
	if e != nil {
		t.Fatal(e)
	}
	c := &stringCatalog{templates: []stringTemplate{tpl}, frags: map[string]string{"EDIT TRADE ROUTE": "編輯貿易路線"}}
	s := &stringRuntime{cat: c}
	if zh, key, ok := s.routeTitleTranslate("EDIT TRADE ROUTE 1", image.Rect(128, 5, 192, 10), 5, 15); !ok || zh != "編輯貿易路線 1" || key != "template:route-editor-title" {
		t.Fatalf("%q %q %v", zh, key, ok)
	}
	for _, text := range []string{"EDIT TRADE ROUTE 1", "EDIT TRADE ROUTE 2", "EDIT TRADE ROUTE Caravel"} {
		if _, _, why := c.translate(text); why == "" {
			t.Fatal("general lookup captured player route name", text)
		}
	}
}
func TestTradeTitleWrongField(t *testing.T) {
	tpl, e := makeStringTemplate("route-editor-title", "EDIT TRADE ROUTE {n1}", "編輯貿易路線 {n1}")
	if e != nil {
		t.Fatal(e)
	}
	s := &stringRuntime{cat: &stringCatalog{templates: []stringTemplate{tpl}, frags: map[string]string{"EDIT TRADE ROUTE": "編輯貿易路線"}}}
	for _, v := range []struct {
		text  string
		rect  image.Rectangle
		cap   int
		color byte
	}{
		{"EDIT TRADE ROUTE 1", image.Rect(55, 25, 119, 30), 5, 15},
		{"EDIT TRADE ROUTE 1", image.Rect(128, 5, 192, 10), 7, 15},
		{"EDIT TRADE ROUTE 1", image.Rect(128, 5, 192, 10), 5, 149},
		{"EDIT TRADE ROUTE 2", image.Rect(128, 5, 192, 10), 5, 15},
	} {
		if _, _, ok := s.routeTitleTranslate(v.text, v.rect, v.cap, v.color); ok {
			t.Fatal(v)
		}
	}
	s.cat.frags["EDIT TRADE ROUTE"] = ""
	if _, _, ok := s.routeTitleTranslate("EDIT TRADE ROUTE 1", image.Rect(128, 5, 192, 10), 5, 15); ok {
		t.Fatal("missing verified literal")
	}
}

func TestTradeGridDefaultNameRole(t *testing.T) {
	s, c := tradeContextFixture()
	s.cat.colony = map[string]string{"Jamestown": "詹姆斯敦（Jamestown）", "FakeTown": "假城（FakeTown）"}
	for _, v := range []struct {
		text       string
		face, safe image.Rectangle
		want       string
	}{
		{"1.  Jamestown", image.Rect(11, 69, 60, 75), image.Rect(10, 68, 114, 76), "1.  詹姆斯敦（Jamestown）"},
		{"2.  Jamestown", image.Rect(10, 89, 60, 95), image.Rect(9, 88, 114, 96), "2.  詹姆斯敦（Jamestown）"},
		{"1.  FakeTown", image.Rect(11, 69, 55, 74), image.Rect(10, 68, 114, 75), "1.  假城（FakeTown）"},
	} {
		zh, area, ok := s.routeGridTranslate(v.text, v.face, 5, 15, c)
		if !ok || zh != v.want || area != v.safe {
			t.Fatal(v.text, zh, area, ok)
		}
	}
	// 母港／單位片段存在也不能當城市來源。
	s.cat.frags["Caravel"] = "輕帆船"
	for _, name := range []string{"London", "Caravel", "My Port", "", " Jamestown", "Jamestown "} {
		if _, _, ok := s.routeGridTranslate("1.  "+name, image.Rect(11, 69, 60, 75), 5, 15, c); ok {
			t.Fatal("borrowed name role", name)
		}
	}
}
func TestTradeGridWrongSourceAndContext(t *testing.T) {
	for _, v := range []struct {
		text  string
		face  image.Rectangle
		cap   int
		color byte
	}{
		{"1. Jamestown", image.Rect(11, 69, 60, 75), 5, 15}, {"3.  Jamestown", image.Rect(11, 69, 60, 75), 5, 15},
		{"1.  Jamestown", image.Rect(55, 25, 104, 31), 5, 15}, {"1.  Jamestown", image.Rect(10, 69, 60, 75), 5, 15},
		{"1.  Jamestown", image.Rect(11, 69, 115, 75), 5, 15}, {"1.  Jamestown", image.Rect(11, 69, 60, 76), 5, 15},
		{"1.  Jamestown", image.Rect(11, 69, 60, 75), 6, 15}, {"1.  Jamestown", image.Rect(11, 69, 60, 75), 5, 68},
	} {
		s, c := tradeContextFixture()
		s.cat.colony = map[string]string{"Jamestown": "詹姆斯敦（Jamestown）"}
		if _, _, ok := s.routeGridTranslate(v.text, v.face, v.cap, v.color, c); ok {
			t.Fatal(v)
		}
	}
	s, c := tradeContextFixture()
	s.cat.colony = map[string]string{"Jamestown": "詹姆斯敦（Jamestown）"}
	c[5*320+128] = 1
	if _, _, ok := s.routeGridTranslate("1.  Jamestown", image.Rect(11, 69, 60, 75), 5, 15, c); ok {
		t.Fatal("stale title")
	}
	var nilRuntime *stringRuntime
	if _, _, ok := nilRuntime.routeGridTranslate("1.  Jamestown", image.Rect(11, 69, 60, 75), 5, 15, c); ok {
		t.Fatal("nil runtime")
	}
}
func TestTradeGridExpandedAreaWriter(t *testing.T) {
	s, c := tradeContextFixture()
	s.cat.colony = map[string]string{"Jamestown": "詹姆斯敦（Jamestown）"}
	f := &dialogFont{widths: map[rune]int{}, glyphs: map[rune]*image.Alpha{}, cjkTop: 2, cjkBottom: 21}
	for _, ch := range "1.  詹姆斯敦（Jamestown）" {
		f.widths[ch] = 16
		a := image.NewAlpha(image.Rect(0, 0, 10, 22))
		for i := range a.Pix {
			a.Pix[i] = 255
		}
		f.glyphs[ch] = a
	}
	s.cat.fonts = map[int]*dialogFont{22: f}
	boxes := make([]image.Rectangle, 13)
	boxes[0] = image.Rect(11, 69, 14, 74)
	boxes[12] = image.Rect(57, 70, 60, 75)
	r := &stringRun{text: []byte("1.  Jamestown"), boxes: boxes, colors: map[byte]int{15: 1}, others: image.Rect(70, 70, 71, 71)}
	if it, why := s.finish(r, c, 1000, image.Rectangle{}); it != nil || why != "other-writer" {
		t.Fatal("extended area writer accepted", it, why)
	}
	r.others = image.Rect(100, 70, 101, 71)
	if it, why := s.finish(r, c, 1000, image.Rectangle{}); it == nil || why != "" || it.safe.Max.X >= 100 {
		t.Fatal("unrelated cell drawing rejected", it, why)
	}
}

func TestTradeGridUntranslatedRedrawRetiresOldCity(t *testing.T) {
	first := &stringItem{id: "STRING:route-grid-colony", text: "1.  Jamestown", ink: image.Rect(11, 69, 60, 75)}
	second := &stringItem{id: "STRING:route-grid-colony", text: "2.  Jamestown", ink: image.Rect(10, 89, 60, 95), phase: "suspended"}
	other := &stringItem{id: "STRING:other", text: "Other", ink: image.Rect(10, 89, 60, 95)}
	s := &stringRuntime{items: []*stringItem{first, second, other}}
	dropped := s.retireRouteGrid("2.  London", image.Rect(10, 89, 44, 94))
	if len(dropped) != 1 || dropped[0] != second || len(s.items) != 2 || s.items[0] != first || s.items[1] != other {
		t.Fatal("untranslated redraw retained city", dropped, s.items)
	}
}
func TestTradeGridRetirementPreservesUnchangedAndUnrelatedText(t *testing.T) {
	for _, v := range []struct {
		text string
		ink  image.Rectangle
	}{
		{"2.  Jamestown", image.Rect(10, 89, 60, 95)},
		{"2.  London", image.Rect(55, 25, 100, 31)},
		{"L", image.Rect(10, 89, 14, 94)},
	} {
		it := &stringItem{id: "STRING:route-grid-colony", text: "2.  Jamestown", ink: image.Rect(10, 89, 60, 95)}
		s := &stringRuntime{items: []*stringItem{it}}
		if dropped := s.retireRouteGrid(v.text, v.ink); len(dropped) != 0 || len(s.items) != 1 || s.items[0] != it {
			t.Fatal(v, dropped, s.items)
		}
	}
}

func TestTradeGridCompleteFieldRetiresUnknownShortNames(t *testing.T) {
	for _, name := range []string{"London", "L", "12345", "My Port"} {
		it := &stringItem{id: "STRING:route-grid-colony", text: "2.  Jamestown", ink: image.Rect(10, 89, 60, 95)}
		s := &stringRuntime{items: []*stringItem{it}}
		dropped := s.retireRouteGrid("2.  "+name, image.Rect(10, 89, 30, 95))
		if len(dropped) != 1 || dropped[0] != it || len(s.items) != 0 {
			t.Fatal("unknown full field retained old city", name, dropped)
		}
	}
	for _, v := range []struct {
		text string
		ink  image.Rectangle
	}{
		{"London", image.Rect(10, 89, 44, 94)}, {"2.  London", image.Rect(10, 88, 44, 94)},
		{"1.  London", image.Rect(10, 89, 44, 94)}, {"2.  ", image.Rect(10, 89, 20, 94)},
	} {
		it := &stringItem{id: "STRING:route-grid-colony", text: "2.  Jamestown", ink: image.Rect(10, 89, 60, 95)}
		s := &stringRuntime{items: []*stringItem{it}}
		if d := s.retireRouteGrid(v.text, v.ink); len(d) != 0 || len(s.items) != 1 {
			t.Fatal("unrelated print removed grid", v)
		}
	}
}

// 港口名稱只供專屬欄位，玩家同字姓名不得被通用模板收走。
func TestStringPortTypedSlots(t *testing.T) {
	c := stringFixture(t)
	c.portRoles = map[string]map[string]bool{"nation": {"English": true}, "unit": {"Colonists": true}, "job": {"Carpenter": true}, "cargo": {"Food": true}}
	for _, pair := range [][2]string{{"English", "英國"}, {"Colonists", "殖民地居民"}, {"Carpenter", "木匠"}, {"Food", "食物"}} {
		c.addFrag(pair[0], pair[1])
	}
	for _, row := range [][3]string{{"port-field-unit", "{w1} {w2}", "{w1}{w2}"}, {"port-field-profession", "{w1} {w2} ( {w3} )", "{w1}{w2}（{w3}）"}, {"port-field-market", "{w1} (Bidding {n1}, Asking {n2})", "{w1}（出價{n1}，開價{n2}）"}} {
		tpl, e := makeStringTemplate(row[0], row[1], row[2])
		if e != nil {
			t.Fatal(e)
		}
		c.templates = append(c.templates, tpl)
	}
	for _, row := range [][3]string{{"port-field-unit", "English Colonists ", "英國殖民地居民"}, {"port-field-profession", "English Colonists ( Carpenter ) ", "英國殖民地居民（木匠）"}, {"port-field-market", "Food (Bidding 2, Asking 10)", "食物（出價2，開價10）"}} {
		if value, ok := c.portText(row[0], row[1]); !ok || value != row[2] {
			t.Fatalf("typed field %q: %q %v", row[1], value, ok)
		}
		if _, _, why := c.translate(row[1]); why != "no-template" {
			t.Fatalf("context-free translation accepted %q: %s", row[1], why)
		}
	}
	for _, row := range [][2]string{{"port-field-unit", "Food Colonists"}, {"port-field-profession", "English Colonists ( Food )"}, {"port-field-market", "Carpenter (Bidding 2, Asking 10)"}, {"port-field-unit", "My Name Colonists"}, {"port-field-profession", "English Colonists ( My Name )"}, {"port-field-market", "My Name (Bidding 2, Asking 10)"}} {
		if _, ok := c.portText(row[0], row[1]); ok {
			t.Fatal("wrong source role or player name", row[1])
		}
	}
	if portKinds([]byte("@NATIONALITY\r\nEnglish\r\n")) != nil {
		t.Fatal("unverified NAMES version accepted")
	}
	if portScene(make([]byte, 64000)) || portScene(nil) {
		t.Fatal("unverified port canvas accepted")
	}
}

func woodcutFixture(t *testing.T, corpus, draft, present bool, change string) (*stringCatalog, error) {
	t.Helper()
	raw := []byte("GOLDEN GARDEN")
	file := append(append([]byte("@E\r\n"), raw...), '\r', '\n')
	sum := func(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }
	header := func(s string) []byte { return []byte(s + "\n") }
	cor := "message_id\tsource_file\tsource_file_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tzh_hant\n"
	dra := "candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_byte_length\tsource_bytes_sha256\tzh_hant\n"
	values := []string{"WOODCUT.TXT:0x4", "WOODCUT.TXT", sum(file), "0x4", fmt.Sprint(len(raw)), sum(raw), "田園探索"}
	switch change {
	case "file":
		values[2] = strings.Repeat("0", 64)
	case "fragment":
		values[5] = strings.Repeat("0", 64)
	case "offset":
		values[3] = "0xFFFF"
	}
	if corpus {
		cor += strings.Join(values, "\t") + "\n"
	}
	if draft {
		dra += strings.Join(values, "\t") + "\n"
	}
	files := map[string][]byte{}
	if present {
		files["WOODCUT.TXT"] = file
	}
	return loadStringCatalog(&dialogCatalog{terms: map[string]string{}},
		header("template_id\tpattern_en\tzh_hant"), header("candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_byte_length\tsource_bytes_sha256\tzh_hant"),
		[]byte(cor), []byte(dra), header("message_id\tsource_member_sha256\ttext_offset\ttext_byte_length\tsource_bytes_sha256\tsource_name\tzh_hant"), files)
}

func TestWoodcutCatalogSources(t *testing.T) {
	for _, sides := range [][2]bool{{true, false}, {false, true}, {true, true}} {
		c, e := woodcutFixture(t, sides[0], sides[1], true, "")
		if e != nil || c.woodcut["GOLDEN GARDEN"] != (woodcutTitle{"WOODCUT.TXT:0x4", "田園探索"}) {
			t.Fatalf("來源身份未綁定：%v", e)
		}
		c.addWoodcut("GOLDEN GARDEN", "OTHER", "田園探索")
		c.addWoodcut("GOLDEN GARDEN", "WOODCUT.TXT:0x4", "田園探索")
		if c.woodcut["GOLDEN GARDEN"].id != "" {
			t.Fatal("衝突來源不得恢復")
		}
	}
	c, e := woodcutFixture(t, true, true, false, "")
	if e != nil || len(c.woodcut) != 0 {
		t.Fatal("缺原檔不得綁定")
	}
	for _, change := range []string{"file", "fragment", "offset"} {
		if _, e := woodcutFixture(t, true, true, true, change); e == nil {
			t.Fatalf("未拒絕%s", change)
		}
	}
	c, e = woodcutFixture(t, true, false, true, "")
	if e != nil {
		t.Fatal(e)
	}
	c.addWoodcut("GOLDEN GARDEN", "WOODCUT.TXT:0x4", "其他譯文")
	if c.woodcut["GOLDEN GARDEN"].zh != "" {
		t.Fatal("衝突譯文不得使用")
	}
}

func woodcutTestRun(t *testing.T) (*stringRuntime, *stringRun, []byte) {
	t.Helper()
	c, e := woodcutFixture(t, true, false, true, "")
	if e != nil {
		t.Fatal(e)
	}
	c.fonts = map[int]*dialogFont{}
	for size := 20; size <= 30; size++ {
		f := &dialogFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, cjkTop: 2, cjkBottom: size}
		for _, ch := range "田園探索字" {
			g := image.NewAlpha(image.Rect(0, 0, size, size+2))
			for y := 2; y < size; y++ {
				for x := 2; x < size-2; x++ {
					g.Pix[y*g.Stride+x] = 255
				}
			}
			f.glyphs[ch], f.widths[ch] = g, size
		}
		c.fonts[size] = f
	}
	s := &stringRuntime{cat: c, misses: map[string]int{}}
	r := &stringRun{text: []byte("GOLDEN GARDEN"), boxes: make([]image.Rectangle, 13), colors: map[byte]int{}, firstOld: map[int]byte{}, lastVal: map[int]byte{}}
	canvas := bytes.Repeat([]byte{69}, 64000)
	for j, ch := range r.text {
		if ch == ' ' {
			continue
		}
		x := 90 + 137*j/(len(r.text)-1)
		r.boxes[j] = image.Rect(x, 165, x+3, 172)
		for y := 165; y < 172; y++ {
			i := y*320 + x
			value := byte(92 + (y-165)%3)
			r.firstOld[i] = canvas[i]
			r.lastVal[i] = value
			canvas[i] = value
			r.colors[value]++
		}
	}
	return s, r, canvas
}

func TestWoodcutFieldMasksAndOriginalIsolation(t *testing.T) {
	s, r, canvas := woodcutTestRun(t)
	original := append([]byte(nil), canvas...)
	it, why := s.finish(r, canvas, 200, image.Rectangle{})
	if it == nil {
		t.Fatal(why)
	}
	if it.id != "STRING:woodcut:WOODCUT.TXT:0x4" || it.size != 30 || it.phase != "waiting-screen" || it.safe != image.Rect(89, 164, 231, 173) ||
		it.color != 94 || it.accentColor != 92 || it.shadowColor != 93 || it.shadowOff != 4 {
		t.Fatalf("欄位不符：%+v", it)
	}
	if !bytes.Equal(original, canvas) {
		t.Fatal("不得改寫原版畫布")
	}
	if !bytes.Equal(it.before, bytes.Repeat([]byte{69}, it.safe.Dx()*it.safe.Dy())) || !bytes.Equal(it.after, stringRect(canvas, it.safe)) {
		t.Fatal("背景來源不符")
	}
	counts := [3]int{}
	for i := range it.norm.Pix {
		hits := 0
		for j, m := range []*image.Alpha{it.shadow, it.norm, it.accent} {
			if m.Pix[i] != 0 {
				counts[j]++
				hits++
			}
		}
		if hits > 1 {
			t.Fatal("三色遮罩必須互斥")
		}
	}
	for _, n := range counts {
		if n == 0 {
			t.Fatal("缺少色層")
		}
	}
}

func TestWoodcutGuardRefusals(t *testing.T) {
	for _, tc := range []struct {
		name, want string
		change     func(*stringRuntime, *stringRun, []byte)
	}{
		{"unbound", "multi-color", func(s *stringRuntime, r *stringRun, b []byte) {
			delete(s.cat.woodcut, string(r.text))
			s.cat.frags[string(r.text)] = "田園探索"
		}},
		{"unknown-suffix", "multi-color", func(s *stringRuntime, r *stringRun, b []byte) { r.text[len(r.text)-1] = 'X' }},
		{"colour", "woodcut-colors", func(s *stringRuntime, r *stringRun, b []byte) { delete(r.colors, 92); r.colors[91] = 10 }},
		{"outline", "woodcut-geometry", func(s *stringRuntime, r *stringRun, b []byte) { r.outline = true }},
		{"buffer", "woodcut-geometry", func(s *stringRuntime, r *stringRun, b []byte) { r.buf2 = true }},
		{"mixed", "woodcut-geometry", func(s *stringRuntime, r *stringRun, b []byte) { r.mixed = true }},
		{"position", "woodcut-geometry", func(s *stringRuntime, r *stringRun, b []byte) {
			for i := range r.boxes {
				r.boxes[i] = r.boxes[i].Add(image.Pt(0, -1))
			}
		}},
		{"writer", "other-writer", func(s *stringRuntime, r *stringRun, b []byte) { r.others = image.Rect(89, 164, 90, 165) }},
		{"pixels-changed", "woodcut-source-changed", func(s *stringRuntime, r *stringRun, b []byte) { b[165*320+90] = 1 }},
		{"old-missing", "woodcut-source-changed", func(s *stringRuntime, r *stringRun, b []byte) { delete(r.firstOld, 165*320+90) }},
		{"missing-font", "does-not-fit", func(s *stringRuntime, r *stringRun, b []byte) { s.cat.fonts = nil }},
		{"missing-glyph", "does-not-fit", func(s *stringRuntime, r *stringRun, b []byte) {
			for _, f := range s.cat.fonts {
				delete(f.glyphs, '探')
			}
		}},
		{"overflow", "does-not-fit", func(s *stringRuntime, r *stringRun, b []byte) {
			s.cat.woodcut[string(r.text)] = woodcutTitle{"WOODCUT.TXT:0x4", strings.Repeat("字", 1000)}
		}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			s, r, b := woodcutTestRun(t)
			tc.change(s, r, b)
			original := append([]byte(nil), b...)
			it, why := s.finish(r, b, 200, image.Rectangle{})
			if it != nil || why != tc.want {
				t.Fatalf("%v %q，預期%s", it, why, tc.want)
			}
			if !bytes.Equal(original, b) {
				t.Fatal("拒絕不得改原版")
			}
		})
	}
}

func TestWoodcutOutsideWritesAndCapacity(t *testing.T) {
	s, r, b := woodcutTestRun(t)
	r.others = image.Rect(1, 20, 2, 21)
	b[20*320+1] = 1
	if it, why := s.finish(r, b, 200, image.Rectangle{}); it == nil {
		t.Fatal(why)
	}
	s.cat.woodcut[string(r.text)] = woodcutTitle{"WOODCUT.TXT:0x4", strings.Repeat("字", 21)}
	it, why := s.finish(r, b, 200, image.Rectangle{})
	if it == nil || it.size >= 30 || it.size < 20 {
		t.Fatalf("應依欄寬縮字：%v %s", it, why)
	}
	for _, f := range s.cat.fonts {
		f.glyphs['字'].Pix[0] = 255
	}
	if it, why = s.finish(r, b, 200, image.Rectangle{}); it != nil || why != "does-not-fit" {
		t.Fatal("失真的字模量測不得裁切顯示")
	}
}

func TestWoodcutVisibleSourceAndPageGuard(t *testing.T) {
	s, r, indexed := woodcutTestRun(t)
	it, why := s.finish(r, indexed, 200, image.Rectangle{})
	if it == nil {
		t.Fatal(why)
	}
	s.items = []*stringItem{it}
	key := "WOODCUT.TXT:0x00000017"
	s.cat.woodcut[it.text] = woodcutTitle{key, it.zh}
	it.id = "STRING:woodcut:" + key
	it.phase = "active"
	original := append([]byte(nil), indexed...)
	if !s.woodcutVisible(indexed, image.Rectangle{}) {
		t.Fatal("完整來源頁未識別")
	}
	if !bytes.Equal(indexed, original) || it.phase != "active" || len(s.items) != 1 {
		t.Fatal("不得改原版或覆蓋狀態")
	}
	for _, phase := range []string{"waiting-screen", "suspended", "expired"} {
		it.phase = phase
		if s.woodcutVisible(indexed, image.Rectangle{}) {
			t.Fatal("舊頁不得識別：", phase)
		}
	}
	it.phase = "active"
	indexed[165*320+90] = 1
	if s.woodcutVisible(indexed, image.Rectangle{}) {
		t.Fatal("原版已改頁不得識別")
	}
	if !s.woodcutVisible(indexed, image.Rect(90, 165, 91, 166)) {
		t.Fatal("既有游標例外失效")
	}
	copy(indexed, original)
	it.id = "STRING:dictionary"
	if s.woodcutVisible(indexed, image.Rectangle{}) {
		t.Fatal("一般文字不得識別")
	}
	it.id = "STRING:woodcut:" + key
	s.cat.woodcut[it.text] = woodcutTitle{"WOODCUT.TXT:0xOTHER", it.zh}
	if s.woodcutVisible(indexed, image.Rectangle{}) {
		t.Fatal("未驗來源不得識別")
	}
	s.cat.woodcut[it.text] = woodcutTitle{key, it.zh}
	it.after = it.after[:1]
	if s.woodcutVisible(indexed, image.Rectangle{}) {
		t.Fatal("部分來源不得識別")
	}
	if s.woodcutVisible(nil, image.Rectangle{}) {
		t.Fatal("缺畫布不得識別")
	}
}
