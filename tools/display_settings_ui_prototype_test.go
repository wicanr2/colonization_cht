package main

import (
	"bytes"
	"os"
	"strings"
	"testing"
)

func prototypeInputsForTest(t *testing.T) ([]byte, []byte) {
	t.Helper()
	path := os.Getenv("COLONIZATION_UI_TSV")
	fontPath := os.Getenv("COLONIZATION_UI_FONT")
	if path == "" || fontPath == "" {
		t.Skip("需明確指定本專案前端TSV與合法固定字型")
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	fontData, err := os.ReadFile(fontPath)
	if err != nil {
		t.Fatal(err)
	}
	return data, fontData
}

func TestPrototypeUICatalogAndRealFontGeometry(t *testing.T) {
	data, fontData := prototypeInputsForTest(t)
	c, err := readPrototypeCatalog(data)
	if err != nil {
		t.Fatal(err)
	}
	f, err := readPrototypeFonts(fontData, c)
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		for _, face := range f.faces {
			face.Close()
		}
	}()
	u := &displayUIPrototype{catalog: c, fonts: f}
	for _, language := range prototypeLanguages {
		for _, phase := range []displayPhase{displayPlaying, displayOpening, displayEditing, displayResuming} {
			u.settings = displaySettings{phase: phase, current: displayOptions{language, "original"}, draft: displayOptions{language, "hd"}}
			for _, problem := range []string{"", "ui.error.unavailable"} {
				u.settings.problem = problem
				image, err := u.canvas()
				if err != nil || image.Rect.Dx() != 1280 || image.Rect.Dy() != 848 {
					t.Fatalf("%s/%d/%s: %v", language, phase, problem, err)
				}
			}
		}
	}
	u.settings = displaySettings{phase: displayEditing, current: displayOptions{"zh-Hant", "original"}}
	c["ui.description"]["zh-Hant"] = strings.Repeat("漢", 5000)
	if _, err := u.canvas(); err == nil {
		t.Fatal("超長文案被裁切或超界繪製")
	}
}

func TestPrototypeUICatalogRejectsMissingDuplicateAndWrongFont(t *testing.T) {
	data, fontData := prototypeInputsForTest(t)
	lines := strings.Split(strings.TrimSpace(string(data)), "\n")
	bad := [][]byte{append(append([]byte(nil), data...), 0xff),
		[]byte(strings.Join(append(lines, lines[1]), "\n")),
		[]byte(strings.Join(lines[:len(lines)-1], "\n")),
		[]byte(strings.Replace(string(data), "\tDisplay settings\n", "\t\n", 1))}
	for _, input := range bad {
		if _, err := readPrototypeCatalog(input); err == nil {
			t.Fatal("損毀或缺譯文介面資料未拒絕")
		}
	}
	c, err := readPrototypeCatalog(data)
	if err != nil {
		t.Fatal(err)
	}
	changed := bytes.Clone(fontData)
	changed[len(changed)-1] ^= 1
	if _, err := readPrototypeFonts(changed, c); err == nil {
		t.Fatal("錯字型仍載入")
	}
}

func TestPrototypeToolbarCoordinates(t *testing.T) {
	u := &displayUIPrototype{}
	for _, c := range []struct {
		x, y, wantX, wantY int
		inside             bool
	}{{0, 48, 0, 0, true}, {1279, 847, 319, 199, true}, {512, 488, 128, 110, true},
		{0, 47, 0, 0, false}, {0, 0, 0, 0, false}, {1280, 48, 0, 0, false}, {0, 848, 0, 0, false}} {
		x, y, inside := u.logicalMouse(c.x, c.y)
		if x != c.wantX || y != c.wantY || inside != c.inside {
			t.Fatalf("座標映射錯誤：%+v 得到 %d,%d,%v", c, x, y, inside)
		}
	}
}
