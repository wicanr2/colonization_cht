package main

import (
	"bytes"
	"encoding/json"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

func TestNotoOrdersFieldIsolation(t *testing.T) {
	lines, canvas := compactStyleFixture()
	old := &dialogCatalog{}
	items := []string{"old"}
	var absent *notoOrdersDisplay
	got, cat, why := absent.field(items, old, lines, canvas, image.Rect(80, 12, 159, 77))
	if why != "" || cat != old || !reflect.DeepEqual(got, items) {
		t.Fatal("未啟用時改變既有欄位")
	}
	p := &notoOrdersDisplay{reason: "invalid-translation"}
	if _, _, why := p.field(items, old, lines, canvas, image.Rect(80, 12, 159, 77)); why != "noto-orders-invalid-translation" {
		t.Fatal("錯誤語言包未整欄回原文", why)
	}
	canvas[9*320+100] = 128
	got, cat, why = p.field(items, old, lines, canvas, image.Rect(80, 12, 159, 77))
	if why != "" || cat != old || !reflect.DeepEqual(got, items) {
		t.Fatal("不屬六列守門的其他欄位受到影響")
	}
	_, canvas = compactStyleFixture()
	p.reason = ""
	if _, _, why := p.field(items, old, lines, canvas, image.Rect(80, 12, 160, 77)); why != "noto-orders-geometry" {
		t.Fatal("未量測安全區接受")
	}
}

// 真實原版缺失時明確skip；正式驗收容器必須提供兩個輸入路徑。
func TestNotoOrdersActualCatalogAndMasks(t *testing.T) {
	dir, game := os.Getenv("TEST_NOTO_ORDERS_DIR"), os.Getenv("TEST_GAME_ROOT")
	if dir == "" || game == "" {
		t.Skip("需要私用Noto圖集與原版MENU.TXT，不以自製資料替代")
	}
	read := func(path string) []byte {
		t.Helper()
		b, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	base := read("/repo/text/draft.zh-Hant.tsv")
	menu := read(filepath.Join(game, "MENU.TXT"))
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			draft := read(filepath.Join(dir, "draft."+locale+".tsv"))
			atlas := read(filepath.Join(dir, "atlas."+locale+".json"))
			p := loadNotoOrders(locale, base, draft, atlas, menu)
			if p.reason != "" || len(p.items) != 6 {
				t.Fatal("實際語言包拒絕", p.reason)
			}
			lines, canvas := compactStyleFixture()
			originalLines, originalCanvas := append([]runLine(nil), lines...), append([]byte(nil), canvas...)
			old := &dialogCatalog{}
			safe := image.Rect(80, 12, 159, 77)
			items, cat, why := p.field(nil, old, lines, canvas, safe)
			if why != "" || cat == old || old.fonts != nil {
				t.Fatal("欄位字模污染共用字模", why)
			}
			_, normal, accent, dim, size := cat.lineLayerMasks(items, lines, safe, 8, false, []int{layerNormal, layerDim, layerDim, layerDim, layerDim, layerNormal})
			if size != 18 || !reflect.DeepEqual(lines, originalLines) || !bytes.Equal(canvas, originalCanvas) {
				t.Fatal("選錯字級或改變原版資料", size)
			}
			for name, mask := range map[string]*image.Alpha{"normal": normal, "accent": accent, "dim": dim} {
				im, err := png.Decode(bytes.NewReader(read(filepath.Join(dir, "mask."+locale+"."+name+".png"))))
				if err != nil || mask == nil || im.Bounds() != mask.Rect {
					t.Fatal("參考遮罩大小不同", name, err)
				}
				for y := 0; y < mask.Rect.Dy(); y++ {
					for x := 0; x < mask.Rect.Dx(); x++ {
						r, _, _, _ := im.At(x, y).RGBA()
						if mask.AlphaAt(x, y).A != uint8(r>>8) {
							t.Fatal("Go與獨立Python遮罩不同", name, x, y)
						}
					}
				}
			}
			for _, kind := range []string{"wrong-locale", "wrong-base", "wrong-menu", "missing-row", "duplicate-key", "stale-source", "wrong-hotkey", "control-code", "ambiguous-fortify", "wrong-face", "wrong-size", "missing-ascii", "missing-cjk", "invalid-alpha"} {
				t.Run(kind, func(t *testing.T) {
					loc, b, d, a, m := locale, base, draft, atlas, menu
					rows, _ := notoOrdersRows(d, false)
					var object map[string]any
					if err := json.Unmarshal(a, &object); err != nil {
						t.Fatal(err)
					}
					switch kind {
					case "wrong-locale":
						loc = "en"
					case "wrong-base":
						b = append(append([]byte(nil), base...), '\n')
					case "wrong-menu":
						m = append([]byte(nil), menu...)
						m[0] ^= 1
					case "missing-row":
						delete(rows, notoOrdersKeys[0])
					case "duplicate-key":
						d = append(append([]byte(nil), d...), []byte(strings.Join(rows[notoOrdersKeys[0]], "\t")+"\n")...)
					case "stale-source":
						rows[notoOrdersKeys[0]][4] = strings.Repeat("0", 64)
					case "wrong-hotkey":
						rows[notoOrdersKeys[0]][6] = strings.ReplaceAll(rows[notoOrdersKeys[0]][6], "~A", "~B")
					case "control-code":
						rows[notoOrdersKeys[0]][6] += "%STRING0"
					case "ambiguous-fortify":
						rows[notoOrdersAlias][6] += "W"
					case "wrong-face":
						object["bindings"].(map[string]any)["locale_profile"] = "wrong"
					case "wrong-size":
						object["font_px"] = 19
					case "missing-ascii", "missing-cjk", "invalid-alpha":
						glyphs := object["sizes"].(map[string]any)["18"].(map[string]any)["glyphs"].(map[string]any)
						key := "V"
						if kind == "missing-cjk" {
							for _, ch := range p.items[0] {
								if ch > 127 {
									key = string(ch)
									break
								}
							}
						}
						if kind == "invalid-alpha" {
							glyphs[key].(map[string]any)["alpha"] = "AA=="
						} else {
							delete(glyphs, key)
						}
					}
					if kind == "missing-row" || kind == "stale-source" || kind == "wrong-hotkey" || kind == "control-code" || kind == "ambiguous-fortify" {
						var out strings.Builder
						out.WriteString(strings.SplitN(string(draft), "\n", 2)[0] + "\n")
						for _, key := range append(append([]string(nil), notoOrdersKeys...), notoOrdersAlias) {
							if row := rows[key]; row != nil {
								out.WriteString(strings.Join(row, "\t") + "\n")
							}
						}
						d = []byte(out.String())
						// 反例重綁TSV，確保來源／標記守門本身能拒絕。
						object["bindings"].(map[string]any)["draft"] = notoOrdersHash(d)
					}
					if kind != "duplicate-key" {
						a, _ = json.Marshal(object)
					}
					bad := loadNotoOrders(loc, b, d, a, m)
					if bad.reason == "" {
						t.Fatal("錯誤輸入接受", kind)
					}
					if _, _, why := bad.field(nil, old, lines, canvas, safe); why == "" {
						t.Fatal("錯誤輸入未回原文")
					}
				})
			}
			long := append([]string(nil), items...)
			long[0] = strings.Repeat("W", 1000)
			_, _, _, _, size = cat.lineLayerMasks(long, lines, safe, 8, false, []int{layerNormal, layerDim, layerDim, layerDim, layerDim, layerNormal})
			if size != 0 {
				t.Fatal("超長列未回原文")
			}
		})
	}
}
