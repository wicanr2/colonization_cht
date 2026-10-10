package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"path/filepath"
	"testing"
)

func retainedRealFonts(t *testing.T) map[int]*dialogFont {
	t.Helper()
	path, textRoot := os.Getenv("COLONIZATION_ASCII_ATLAS"), os.Getenv("COLONIZATION_ASCII_TEXT_ROOT")
	if path == "" || textRoot == "" {
		t.Skip("需明確指定已授權的固定字型圖集與現行TSV")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	bindings := map[string]string{}
	for key, name := range map[string]string{"templates": "string-templates.zh-Hant.tsv", "sea": "sea-status.zh-Hant.tsv",
		"corpus": "corpus.zh-Hant.tsv", "draft": "draft.zh-Hant.tsv", "terms": "terms.zh-Hant.tsv", "colony": "colony-bilingual.tsv"} {
		text, err := os.ReadFile(filepath.Join(textRoot, name))
		if err != nil {
			t.Fatal(err)
		}
		bindings[key] = fmt.Sprintf("%x", sha256.Sum256(text))
	}
	fonts, why := loadAtlasFonts(data, "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c", bindings, 30, 12)
	if fonts == nil {
		t.Fatal(why)
	}
	return fonts
}

func retainedFixture(text string, ink image.Rectangle) *stringRun {
	r := &stringRun{text: []byte(text), firstOld: map[int]byte{}, colors: map[byte]int{15: 1}}
	for i := range text {
		x := ink.Min.X + ink.Dx()*i/len(text)
		x2 := ink.Min.X + ink.Dx()*(i+1)/len(text)
		r.boxes = append(r.boxes, image.Rect(x, ink.Min.Y, x2, ink.Max.Y))
		r.retainedCursor = append(r.retainedCursor, image.Pt(x, ink.Min.Y))
		r.retainedSegments = append(r.retainedSegments, 0x2cae)
	}
	r.retainedCursor = append(r.retainedCursor, image.Pt(ink.Max.X, ink.Min.Y))
	r.retainedSegments = append(r.retainedSegments, 0x2cae)
	return r
}

// 原版正常讀檔畫面的逐字年份幾何，來源與完整收據由規格052索引。
func TestRetainedASCIIObservedThinDigitUsesNativeCell(t *testing.T) {
	fonts := retainedRealFonts(t)
	s := &stringRuntime{cat: &stringCatalog{fonts: fonts, owned: map[string]bool{}}}
	height := 0
	for _, sample := range []struct {
		text       string
		ink        image.Rectangle
		start, end image.Point
	}{
		{"1", image.Rect(238, 129, 239, 134), image.Pt(237, 129), image.Pt(241, 129)},
		{"5", image.Rect(241, 129, 244, 134), image.Pt(241, 129), image.Pt(245, 129)},
		{"0", image.Rect(245, 129, 248, 134), image.Pt(245, 129), image.Pt(249, 129)},
		{"6", image.Rect(249, 129, 252, 134), image.Pt(249, 129), image.Pt(253, 129)},
	} {
		r := retainedFixture(sample.text, sample.ink)
		r.retainedCursor = []image.Point{sample.start, sample.end}
		it, why := finishRetainedASCII(s, r, make([]byte, 64000), 1, "")
		if it == nil {
			t.Fatalf("真實逐字幾何未接受：%s %s", sample.text, why)
		}
		layout, ok := retainedASCIILayout(r, sample.ink)
		plan := planRetainedASCII(fonts, sample.text, layout)
		if !ok || plan == nil || plan.bounds.Dy() != sample.ink.Dy()*4 ||
			(height != 0 && height != plan.bounds.Dy()) {
			t.Fatalf("年份數字大小不一致：%s %v", sample.text, plan)
		}
		height = plan.bounds.Dy()
	}
}

func TestRetainedASCIICellAndVisibilityGuards(t *testing.T) {
	s := &stringRuntime{cat: &stringCatalog{fonts: retainedRealFonts(t), owned: map[string]bool{}}}
	for _, mutate := range []func(*stringRun){
		func(r *stringRun) { r.retainedCursor = nil },
		func(r *stringRun) { r.retainedSegments[0] = 0x3bb0 },
		func(r *stringRun) { r.retainedCursor[1].Y++ },
		func(r *stringRun) { r.retainedCursor[1].X = r.retainedCursor[0].X },
		func(r *stringRun) { r.boxes[0].Min.X-- },
	} {
		r := retainedFixture("90", image.Rect(83, 194, 90, 199))
		mutate(r)
		if it, why := finishRetainedASCII(s, r, make([]byte, 64000), 1, ""); it != nil || why != "retained-unverified-cell" {
			t.Fatalf("未證實字格未拒絕：%v %s", it, why)
		}
	}
	r := retainedFixture("90", image.Rect(83, 194, 90, 199))
	canvas := make([]byte, 64000)
	it, why := finishRetainedASCII(s, r, canvas, 1, "")
	if it == nil {
		t.Fatal(why)
	}
	it.phase = "active"
	if !retainedASCIIVisible(it, canvas, image.Rectangle{}) {
		t.Fatal("當次完整數值被拒絕")
	}
	it.phase = "suspended"
	if retainedASCIIVisible(it, canvas, image.Rectangle{}) {
		t.Fatal("舊頁暫停數值仍被繪製")
	}
	it.phase = "active"
	canvas[it.safe.Min.Y*320+it.safe.Min.X] = 1
	if retainedASCIIVisible(it, canvas, image.Rectangle{}) {
		t.Fatal("新頁僅部分相同仍接受舊數值")
	}
}

func TestRetainedASCIIRealFontAndNoStateMutation(t *testing.T) {
	s := &stringRuntime{cat: &stringCatalog{fonts: retainedRealFonts(t), owned: map[string]bool{}}}
	for _, text := range []string{"90", "102 (0)", "100% (1)", "1000$", "Wicanr2"} {
		r := retainedFixture(text, image.Rect(30, 133, 90, 140))
		canvas := bytes.Repeat([]byte{61}, 64000)
		before := append([]byte(nil), canvas...)
		r.firstOld[134*320+32] = 50
		originalRun, err := json.Marshal(r.text)
		if err != nil {
			t.Fatal(err)
		}
		it, why := finishRetainedASCII(s, r, canvas, 400, "")
		if it == nil || why != "" || it.text != text || it.zh != text {
			t.Fatalf("%s: %v %s", text, it, why)
		}
		if !bytes.Equal(canvas, before) || !bytes.Equal(originalRun, mustRetainedJSON(t, r.text)) {
			t.Fatal("修改來源值或原版畫布")
		}
		var actual image.Rectangle
		for y := it.norm.Rect.Min.Y; y < it.norm.Rect.Max.Y; y++ {
			for x := it.norm.Rect.Min.X; x < it.norm.Rect.Max.X; x++ {
				if it.norm.AlphaAt(x, y).A != 0 {
					actual = actual.Union(image.Rect(x+it.safe.Min.X*4, y+it.safe.Min.Y*4, x+it.safe.Min.X*4+1, y+it.safe.Min.Y*4+1))
				}
			}
		}
		original := image.Rect(inkScale(it.ink.Min.X), inkScale(it.ink.Min.Y), inkScale(it.ink.Max.X), inkScale(it.ink.Max.Y))
		if actual.Empty() || !actual.In(original) || actual.Min != original.Min {
			t.Fatalf("真實英數墨跡越界或未對齊：%s %v %v", text, actual, original)
		}
	}
}

func inkScale(value int) int { return value * 4 }

func mustRetainedJSON(t *testing.T, value any) []byte {
	t.Helper()
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	return data
}

func TestRetainedASCIIRejectsUnsafeSourcesAndMissingGlyphs(t *testing.T) {
	fonts := retainedRealFonts(t)
	s := &stringRuntime{cat: &stringCatalog{fonts: fonts, owned: map[string]bool{"Owned": true}}}
	for _, text := range []string{"\x1b123", "123\n", "中文", "---", "Owned"} {
		if it, _ := finishRetainedASCII(s, retainedFixture(text, image.Rect(4, 4, 30, 11)), make([]byte, 64000), 1, ""); it != nil {
			t.Fatalf("不安全或專屬來源仍接手：%q", text)
		}
	}
	for _, mutate := range []func(*stringRun){func(r *stringRun) { r.outline = true }, func(r *stringRun) { r.buf2 = true },
		func(r *stringRun) { r.mixed = true }, func(r *stringRun) { r.colors[0] = 1 },
		func(r *stringRun) { r.others = image.Rect(5, 5, 6, 6) }} {
		r := retainedFixture("123", image.Rect(4, 4, 30, 11))
		mutate(r)
		if it, _ := finishRetainedASCII(s, r, make([]byte, 64000), 1, ""); it != nil {
			t.Fatal("未驗樣式或其他writer被接受")
		}
	}
	for _, why := range []string{"ambiguous-template", "other-writer", "owned-by-field"} {
		if it, _ := finishRetainedASCII(s, retainedFixture("123", image.Rect(4, 4, 30, 11)), make([]byte, 64000), 1, why); it != nil {
			t.Fatal("覆蓋原有拒絕原因")
		}
	}
	if planRetainedASCII(fonts, "123456789", image.Rect(4, 4, 6, 11)) != nil ||
		planRetainedASCII(fonts, "{123}", image.Rect(4, 4, 40, 11)) != nil {
		t.Fatal("超界或缺字未拒絕")
	}
}
