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
	for size := dialogFloorPx; size <= dialogFontPx; size++ {
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
	sh, n, ac, size := c.dialogMasks("{蘇族}問候{英國}。", 400, 100)
	if size != 30 || sh == nil || n == nil || ac == nil {
		t.Fatalf("30px 應放得下：%d", size)
	}
	if ac.AlphaAt(4+5, 10).A == 0 || ac.AlphaAt(4+2*30+5, 10).A != 0 {
		t.Fatal("強調層只含 {} 內字")
	}
	if _, _, _, size := c.dialogMasks("問候問候問候問候問候問候", 200, 40); size != 0 {
		t.Fatalf("放不下應回 0，得 %d", size)
	}
	if _, _, _, size := c.dialogMasks("問候問候問候", 200, 100); size != 30 {
		t.Fatalf("兩行 30px：%d", size)
	}
	if _, _, _, size := c.dialogMasks("缺字", 400, 100); size != 0 {
		t.Fatal("圖集缺字應回原文")
	}
}
