package main

import (
	"bytes"
	"encoding/json"
	"image/png"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestNotoMenuActualFields(t *testing.T) {
	dir, gameRoot := os.Getenv("TEST_NOTO_MENU_DIR"), os.Getenv("TEST_GAME_ROOT")
	if dir == "" || gameRoot == "" {
		t.Skip("需要私用四語主選單字模及原版GAME.TXT")
	}
	read := func(path string) []byte {
		t.Helper()
		b, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	base, game := read("/repo/text/draft.zh-Hant.tsv"), read(filepath.Join(gameRoot, "GAME.TXT"))
	before := append([]byte(nil), game...)
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			draft := read(filepath.Join(dir, "draft."+locale+".tsv"))
			masks := map[string][]byte{}
			for _, key := range notoMenuKeys {
				masks[key] = read(filepath.Join(dir, locale, strings.ReplaceAll(key, ":", "-")+".json"))
			}
			p := loadNotoMenu(locale, base, draft, game, masks)
			if p.reason != "" || len(p.inks) != 5 {
				t.Fatal("實際主選單字模拒絕", p.reason)
			}
			makeLines := func() []*menuLine {
				var ls []*menuLine
				for i, key := range notoMenuKeys {
					o, n := notoMenuOffsets[i], notoMenuLengths[i]
					ls = append(ls, &menuLine{id: key, offset: o, length: n, y: 107 + 8*i, matches: 1, catalogValid: true,
						source: append([]byte(nil), game[o:o+n]...), translation: "old"})
				}
				return ls
			}
			lines := makeLines()
			p.apply(lines, false)
			for i, l := range lines {
				im, err := png.Decode(bytes.NewReader(read(filepath.Join(dir, locale, strings.ReplaceAll(l.id, ":", "-")+".png"))))
				if err != nil || l.ink == nil || l.ink.Rect != im.Bounds() || l.translation != p.texts[i] || l.fontReason != "" {
					t.Fatal("載入與參考遮罩不同", err)
				}
				for y := 0; y < im.Bounds().Dy(); y++ {
					for x := 0; x < im.Bounds().Dx(); x++ {
						r, _, _, _ := im.At(x, y).RGBA()
						if l.ink.AlphaAt(x, y).A != uint8(r>>8) {
							t.Fatal("Pillow與Go遮罩不同", x, y)
						}
					}
				}
				if !bytes.Equal(l.source, game[l.offset:l.offset+l.length]) || !bytes.Equal(game, before) {
					t.Fatal("顯示載入改變原版來源")
				}
			}
			for _, kind := range []string{"locale", "base", "game", "missing-row", "duplicate-row", "source", "control", "translation", "face", "font", "size", "width", "height", "alpha", "empty", "missing-mask", "geometry-guard", "source-guard", "missing-flag", "incomplete-scope"} {
				t.Run(kind, func(t *testing.T) {
					loc, b, d, g := locale, base, draft, game
					ms := map[string][]byte{}
					for key, value := range masks {
						ms[key] = value
					}
					key := notoMenuKeys[0]
					var obj map[string]any
					if err := json.Unmarshal(ms[key], &obj); err != nil {
						t.Fatal(err)
					}
					switch kind {
					case "locale":
						loc = "en"
					case "base":
						b = append(append([]byte(nil), base...), '\n')
					case "game":
						g = append([]byte(nil), game...)
						g[0] ^= 1
					case "missing-row":
						d = []byte(strings.Join(strings.Split(string(draft), "\n")[:5], "\n") + "\n")
					case "duplicate-row":
						d = append(append([]byte(nil), draft...), []byte(strings.Split(string(draft), "\n")[1]+"\n")...)
					case "source", "control", "translation":
						rows := strings.Split(string(draft), "\n")
						cols := strings.Split(rows[1], "\t")
						if kind == "source" {
							cols[4] = strings.Repeat("0", 64)
						} else if kind == "control" {
							cols[6] += "%STRING0"
						} else {
							cols[6] += "W"
						}
						rows[1] = strings.Join(cols, "\t")
						d = []byte(strings.Join(rows, "\n"))
						obj["bindings"].(map[string]any)["draft"] = notoOrdersHash(d)
						obj["catalog_sha256"] = notoOrdersHash(d)
					case "face":
						obj["bindings"].(map[string]any)["locale_profile"] = "wrong-region"
					case "font":
						obj["font_sha256"] = "old-font"
					case "size":
						obj["font_size"] = 18
					case "width":
						obj["width"] = 581
					case "height":
						obj["height"] = 25
					case "alpha":
						obj["alpha"] = "AA=="
					case "empty":
						zero := make([]byte, int(obj["width"].(float64)*obj["height"].(float64)))
						obj["alpha"] = zero
						obj["values_sha256"] = notoOrdersHash(zero)
					case "missing-mask":
						delete(ms, key)
					}
					if kind != "missing-mask" {
						ms[key], _ = json.Marshal(obj)
					}
					bad := loadNotoMenu(loc, b, d, g, ms)
					ls := makeLines()
					switch kind {
					case "geometry-guard":
						ls[0].y++
					case "source-guard":
						ls[0].catalogValid = false
					case "incomplete-scope":
						ls = ls[:1]
					}
					bad.apply(ls, kind == "missing-flag")
					for _, l := range ls {
						if l.ink != nil || !strings.HasPrefix(l.fontReason, "noto-menu-") || l.translation != "old" {
							t.Fatal("錯誤包未整組回原文", kind, l.fontReason)
						}
					}
				})
			}
			ls := makeLines()
			original := *ls[0]
			var absent *notoMenuDisplay
			absent.apply(ls, false)
			if !reflect.DeepEqual(*ls[0], original) {
				t.Fatal("未啟用時改變原版路徑")
			}
		})
	}
}
