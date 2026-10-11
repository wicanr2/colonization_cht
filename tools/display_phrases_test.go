package main

import (
	"image"
	"os"
	"sort"
	"strings"
	"testing"
)

func displayPhraseData(t *testing.T, locale string) []byte {
	t.Helper()
	data, err := os.ReadFile("/repo/text/string-templates.zh-Hant.tsv")
	if err != nil {
		t.Fatal(err)
	}
	result := "template_id\tpattern_en\tzh_hant\n"
	for _, row := range tsvRows(data) {
		if strings.HasPrefix(row["template_id"], "display-") {
			result += row["template_id"] + "\t" + row["pattern_en"] + "\t" + dialogLocaleTemplateText(t, locale, "templates", row["template_id"]) + "\n"
		}
	}
	return []byte(result)
}

func displayPhraseFixture(t *testing.T, locale string) displayPhrases {
	t.Helper()
	p, err := loadDisplayPhrases(displayPhraseData(t, locale))
	if err != nil || len(p) != 14 {
		t.Fatal("實際語言組句缺件", locale, err)
	}
	return p
}

func TestDisplayPhraseCatalogValidation(t *testing.T) {
	data := string(displayPhraseData(t, "zh-Hant"))
	lines := strings.Split(strings.TrimSuffix(data, "\n"), "\n")
	for _, kind := range []string{"missing", "duplicate", "unknown", "missing-slot", "extra-slot", "repeated-slot", "unknown-slot", "markup", "control", "bad-source"} {
		t.Run(kind, func(t *testing.T) {
			bad := append([]string(nil), lines...)
			switch kind {
			case "missing":
				bad = bad[:len(bad)-1]
			case "duplicate":
				bad = append(bad, bad[1])
			case "unknown":
				bad[1] = strings.Replace(bad[1], "display-sea-gold", "display-unknown", 1)
			default:
				row := strings.Split(bad[1], "\t")
				switch kind {
				case "missing-slot":
					row[2] = strings.ReplaceAll(row[2], "{n1}", "")
				case "extra-slot":
					row[2] += "{w9}"
				case "repeated-slot":
					row[2] += "{n1}"
				case "unknown-slot":
					row[2] += "{other}"
				case "markup":
					row[2] += "^"
				case "control":
					row[2] += "\x01"
				case "bad-source":
					row[1] = strings.ReplaceAll(row[1], "{n1}", "")
				}
				bad[1] = strings.Join(row, "\t")
			}
			if _, err := loadDisplayPhrases([]byte(strings.Join(bad, "\n") + "\n")); err == nil {
				t.Fatal("損壞組句被接受")
			}
		})
	}
	if p, err := loadDisplayPhrases([]byte("template_id\tpattern_en\tzh_hant\n")); err != nil || len(p) != 0 {
		t.Fatal("舊資料缺組句時應回原文", p, err)
	}
}

func TestDisplayPhraseValuesFailClosed(t *testing.T) {
	p := displayPhraseFixture(t, "zh-Hant")
	for _, value := range []string{"", "12.5", "-1", "１２", "1\n", "{n1}", "%NUMBER0"} {
		if _, ok := p.format("display-sea-date", map[string]string{"w1": "season", "n1": value}); ok {
			t.Fatal("數字被解讀或改寫", value)
		}
	}
	for _, value := range []string{"", "{w1}", "%STRING0", "word^", "word\x01", "word\n"} {
		if _, ok := p.format("display-voyage-go-to", map[string]string{"w1": value}); ok {
			t.Fatal("代入值再次解讀", value)
		}
	}
	for _, p := range []displayPhrases{nil, {}} {
		if _, ok := p.format("display-sea-date", map[string]string{"w1": "season", "n1": "1492"}); ok {
			t.Fatal("缺件有程式內回退")
		}
	}
	if _, ok := p.format("display-voyage-go-to", map[string]string{"w1": "port", "w2": "extra"}); ok {
		t.Fatal("額外代入值被忽略")
	}
}

func TestDisplayPhraseRuntimeFourLocales(t *testing.T) {
	names, err := os.ReadFile("/game/NAMES.TXT")
	if os.IsNotExist(err) {
		t.Skip("缺合法原版名稱角色")
	}
	if err != nil {
		t.Fatal(err)
	}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			p := displayPhraseFixture(t, locale)
			c := &stringCatalog{phrases: p, frags: map[string]string{"Discoverer": "difficulty", "English": "nation", "Spring": "season", "Caravel": "ship", "London": "port", "Sailing For": "action", "Sioux": "tribe", "Locat:": "location"}, portRoles: portKinds(names), viewTribes: verifiedViewTribes(names)}
			s := &stringRuntime{cat: c}
			sea := &seaState{phrases: p, dict: map[string]map[string]string{
				"label":  {"Gold:": "gold", "Tax:": "tax", "Locat:": "location", "Moves:": "moves", "Inbound From": "inbound"},
				"nation": {"English": "nation"}, "unit": {"Caravel": "ship"}, "port": {"London": "port"}, "nation_abbrev": {"Eng.": "abbrev"},
				"season": {"Spring": "season"}, "terrain": {"Ocean": "terrain"}, "goods": {"Food": "goods"},
			}}
			cases := []struct {
				id, raw string
				values  map[string]string
			}{
				{"display-sea-gold", "Gold:100$  Tax: 2%", map[string]string{"w1": "gold", "n1": "100", "w2": "tax", "n2": "2"}},
				{"display-sea-location", "Locat: (12, 34)", map[string]string{"w1": "location", "n1": "12", "n2": "34"}},
				{"display-sea-moves", "Moves: 1/3", map[string]string{"w1": "moves", "w2": "1/3"}},
				{"display-sea-inbound", "English Caravel Inbound From London", map[string]string{"w1": "nation", "w2": "ship", "w3": "inbound", "w4": "port"}},
				{"display-sea-date", "Spring 1492", map[string]string{"w1": "season", "n1": "1492"}},
				{"display-sea-unit", "Eng. Caravel", map[string]string{"w1": "abbrev", "w2": "ship"}},
				{"display-sea-terrain", "(Ocean)", map[string]string{"w1": "terrain"}},
				{"display-sea-goods", "50 Food", map[string]string{"n1": "50", "w1": "goods"}},
				{"display-view-location", "Locat: (12, 34) 9", map[string]string{"w1": "location", "n1": "12", "n2": "34", "n3": "9"}},
				{"display-view-tribe-land", "Sioux Land", map[string]string{"w1": "tribe"}},
				{"display-save-description", "Discoverer Alice of the English (Spring 1496)", map[string]string{"w1": "difficulty", "person": "Alice", "w2": "nation", "w3": "season", "n1": "1496"}},
				{"display-port-ship-header", "English Caravel in London", map[string]string{"w1": "nation", "w2": "ship", "w3": "port"}},
				{"display-voyage-go-to", "Go To London", map[string]string{"w1": "port"}},
				{"display-voyage-ship-header", "English Caravel Sailing For London", map[string]string{"w1": "nation", "w2": "ship", "w3": "action", "w4": "port"}},
			}
			for _, tc := range cases {
				t.Run(tc.id, func(t *testing.T) {
					var pairs []string
					keys := make([]string, 0, len(tc.values))
					for key := range tc.values {
						keys = append(keys, key)
					}
					sort.Strings(keys)
					for _, key := range keys {
						pairs = append(pairs, "{"+key+"}", tc.values[key])
					}
					want := strings.NewReplacer(pairs...).Replace(dialogLocaleTemplateText(t, locale, "templates", tc.id))
					var got string
					var ok bool
					r := &stringRun{text: []byte(tc.raw)}
					switch tc.id {
					case "display-save-description":
						got, ok = c.translateSaveDescription(tc.raw)
					case "display-port-ship-header":
						got, ok = c.portShipHeader(tc.raw)
					case "display-voyage-go-to":
						got, _, ok = s.voyageFieldTranslate(r, image.Rect(242, 93, 285, 98), 5, 149)
					case "display-voyage-ship-header":
						got, _, ok = s.voyageFieldTranslate(r, image.Rect(93, 1, 226, 7), 5, 149)
					case "display-view-location":
						got, _, ok = s.viewFieldTranslate(r, image.Rect(242, 68, 310, 74), 5, 68)
					case "display-view-tribe-land":
						got, _, ok = s.viewFieldTranslate(r, image.Rect(242, 75, 310, 81), 5, 68)
					default:
						got, ok = sea.seaTranslate(tc.raw)
					}
					if !ok || got != want {
						t.Fatal(tc.raw, got, want, ok)
					}
				})
			}
			for _, raw := range []string{"English Unknown in London", "English Caravel in My Port"} {
				if _, ok := c.portShipHeader(raw); ok {
					t.Fatal("未驗名稱覆蓋", raw)
				}
			}
			for _, raw := range []string{"Sioux Land", "Locat: (12, 34) 9"} {
				if _, _, ok := s.viewFieldTranslate(&stringRun{text: []byte(raw)}, image.Rect(242, 1, 310, 7), 5, 68); ok {
					t.Fatal("錯誤位置覆蓋", raw)
				}
			}
			if _, ok := sea.seaTranslate("Moves: %NUMBER0"); ok {
				t.Fatal("未展開代碼覆蓋")
			}
		})
	}
}

func TestDisplayPhrasesExcludedFromGenericTemplates(t *testing.T) {
	data := displayPhraseData(t, "zh-Hant")
	cat, err := loadStringCatalog(nil, data, []byte("candidate_id\n"), []byte("message_id\n"), []byte("candidate_id\n"), []byte("message_id\n"), nil)
	if err != nil || len(cat.templates) != 0 || len(cat.phrases) != 14 {
		t.Fatal(cat, err)
	}
	// 即使錯誤地注入一般模板，專屬前綴仍不可解除歧義。
	tpl, err := makeStringTemplate("display-voyage-go-to", "Go To {w1}", "destination{w1}")
	if err != nil {
		t.Fatal(err)
	}
	cat.templates, cat.frags = []stringTemplate{tpl}, map[string]string{"London": "port"}
	if _, _, reason := cat.translate("Go To London"); reason == "" {
		t.Fatal("專屬組句外洩一般入口")
	}
}

func TestDisplayTermFromCanonicalTable(t *testing.T) {
	data, err := os.ReadFile("/repo/text/terms.zh-Hant.tsv")
	if err != nil {
		t.Fatal(err)
	}
	if got, ok := displayTerm(data, "Caravel", "ship"); !ok || got != "輕帆船" {
		t.Fatal(got, ok)
	}
	for _, data := range []string{"en\tzh\tcategory\n", "en\tzh\tcategory\nCaravel\tship\tunit\n", "en\tzh\tcategory\nCaravel\tship\tship\nCaravel\tship\tship\n", "en\tzh\tcategory\nCaravel\t%STRING0\tship\n"} {
		if _, ok := displayTerm([]byte(data), "Caravel", "ship"); ok {
			t.Fatal("未定稿術語被接受", data)
		}
	}
}
