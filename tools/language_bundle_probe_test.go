package main

import (
	"encoding/json"
	"io/fs"
	"os"
	"path/filepath"
	"testing"
	"testing/fstest"
)

type draftOverlayFS struct {
	base    fs.FS
	overlay fstest.MapFS
	missing string
}

func (f draftOverlayFS) Open(name string) (fs.File, error) {
	if name == f.missing {
		return nil, fs.ErrNotExist
	}
	if _, ok := f.overlay[name]; ok {
		return f.overlay.Open(name)
	}
	return f.base.Open(name)
}

func draftFixture(t *testing.T) (fs.FS, draftBundleRequirements) {
	t.Helper()
	root := os.Getenv("DRAFT_BUNDLE_ROOT")
	if root == "" {
		t.Fatal("DRAFT_BUNDLE_ROOT must name actual generated resources; no substitute fixture")
	}
	base := os.DirFS(root)
	var registry struct {
		Source string `json:"source_binding_sha256"`
		Tables []struct {
			File string `json:"file"`
		} `json:"tables"`
	}
	data, err := os.ReadFile("/repo/tools/language-catalogs.json")
	if err != nil || json.Unmarshal(data, &registry) != nil {
		t.Fatal("registry unavailable", err)
	}
	needs := draftBundleRequirements{Source: registry.Source,
		Font:    "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a",
		License: "6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2",
		Fields:  "2be579643f7655f635a6bec4adcbae9a1fb11a4734d3b8daf80177934e15b61d",
		Masks:   map[string]draftMaskRequirement{}}
	for _, table := range registry.Tables {
		needs.Tables = append(needs.Tables, table.File)
	}
	data, err = os.ReadFile(filepath.Join(filepath.Dir(root), "fields.json"))
	if err != nil || draftDigest(data) != "2be579643f7655f635a6bec4adcbae9a1fb11a4734d3b8daf80177934e15b61d" {
		t.Fatal("fixed-field evidence unavailable", err)
	}
	var evidence struct {
		Fields []struct {
			ID     string `json:"id"`
			File   string `json:"file"`
			Group  string `json:"group"`
			Shadow int    `json:"shadow_offset"`
			Safe   struct {
				Min, Max struct{ X, Y int }
			} `json:"safe"`
		} `json:"fields"`
	}
	if err := json.Unmarshal(data, &evidence); err != nil {
		t.Fatal(err)
	}
	for _, field := range evidence.Fields {
		catalog := "draft.zh-Hant.tsv"
		switch field.Group {
		case "card", "cards-rest":
			catalog = "nation-card-fragments.zh-Hant.tsv"
		case "intro":
			catalog = "nation-introduction.zh-Hant.tsv"
		case "help":
			catalog = "help-bilingual.tsv"
		case "static":
			catalog = "static-overlay.zh-Hant.tsv"
		}
		needs.Masks[field.File] = draftMaskRequirement{ID: field.ID, Shadow: field.Shadow,
			Safe:    [4]int{field.Safe.Min.X * 4, field.Safe.Min.Y * 4, field.Safe.Max.X * 4, field.Safe.Max.Y * 4},
			Layered: field.Group == "intro" || field.Group == "help", Catalog: catalog}
	}
	return base, needs
}

func TestDraftPrepareActualLanguageResources(t *testing.T) {
	base, needs := draftFixture(t)
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		t.Run(locale, func(t *testing.T) {
			p, err := draftPrepareBundle(base, locale, needs)
			if err != nil || p == nil {
				t.Fatal("actual bundle preparation failed", err)
			}
			want := 80
			if locale == "en" {
				want = 0
			}
			if p.manifest.Locale != locale || len(p.files) != want {
				t.Fatal("prepared resource count or language differs")
			}
			t.Logf("prepared %s: %d files, original=%v", locale, len(p.files), p.manifest.Original)
		})
	}
}

func draftJSONMap(t *testing.T, data []byte) map[string]any {
	t.Helper()
	var result map[string]any
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatal(err)
	}
	return result
}

func draftEncode(t *testing.T, value any) []byte {
	t.Helper()
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	return data
}

func TestDraftPrepareRejectsCorruption(t *testing.T) {
	base, needs := draftFixture(t)
	manifest, err := fs.ReadFile(base, "ja/manifest.json")
	if err != nil {
		t.Fatal(err)
	}
	for _, test := range []struct {
		name, file string
		edit       func(map[string]any)
	}{
		{"wrong-locale", "", func(m map[string]any) { m["locale"] = "ko" }},
		{"wrong-face", "", func(m map[string]any) { m["face"] = 3 }},
		{"wrong-family", "", func(m map[string]any) { m["family"] = "Noto Sans CJK TC" }},
		{"wrong-font", "", func(m map[string]any) { m["font_sha256"] = needs.License }},
		{"wrong-license", "", func(m map[string]any) { m["license_sha256"] = needs.Font }},
		{"wrong-source", "", func(m map[string]any) { m["source_binding_sha256"] = needs.Font }},
		{"original-mode", "", func(m map[string]any) { m["original_rendering"] = true }},
		{"unknown-manifest-field", "", func(m map[string]any) { m["unreviewed"] = true }},
		{"missing-resource", "", func(m map[string]any) { delete(m["files_sha256"].(map[string]any), "masks/sea-atlas.json") }},
		{"bad-file-hash", "", func(m map[string]any) { m["files_sha256"].(map[string]any)["masks/sea-atlas.json"] = needs.Font }},
		{"unexpected-path", "", func(m map[string]any) {
			files := m["files_sha256"].(map[string]any)
			files["../outside"] = files["masks/sea-atlas.json"]
			delete(files, "masks/sea-atlas.json")
		}},
		{"mask-wrong-locale", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) { m["locale"] = "ko" }},
		{"mask-wrong-key", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) { m["candidate_id"] = "wrong" }},
		{"mask-invalid-alpha", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) { m["alpha"] = "AA==" }},
		{"mask-wrong-catalog", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) { m["catalog_sha256"] = needs.Font }},
		{"mask-wrong-text-binding", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) {
			m["bindings"].(map[string]any)["text"].(map[string]any)["draft.zh-Hant.tsv"] = needs.Font
		}},
		{"mask-overflow", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) { m["width"] = 1281 }},
		{"mask-altered-safe", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) {
			m["measurement"].(map[string]any)["safe_scaled"] = []int{0, 0, 1280, 800}
		}},
		{"mask-failed-measurement", "masks/menu/GAME.TXT-0x000001B0.json", func(m map[string]any) {
			m["measurement"].(map[string]any)["chosen"].(map[string]any)["fits"] = false
		}},
		{"atlas-wrong-face", "masks/sea-atlas.json", func(m map[string]any) { m["face"] = 3 }},
		{"atlas-wrong-catalog", "masks/sea-atlas.json", func(m map[string]any) { m["catalog_sha256"] = needs.Font }},
		{"atlas-missing-size", "masks/sea-atlas.json", func(m map[string]any) { delete(m["sizes"].(map[string]any), "22") }},
		{"atlas-missing-ascii", "masks/sea-atlas.json", func(m map[string]any) {
			delete(m["sizes"].(map[string]any)["22"].(map[string]any)["glyphs"].(map[string]any), "1")
		}},
	} {
		t.Run(test.name, func(t *testing.T) {
			m := draftJSONMap(t, manifest)
			overlay := fstest.MapFS{}
			if test.file == "" {
				test.edit(m)
			} else {
				data, err := fs.ReadFile(base, "ja/"+test.file)
				if err != nil {
					t.Fatal(err)
				}
				resource := draftJSONMap(t, data)
				test.edit(resource)
				changed := draftEncode(t, resource)
				overlay["ja/"+test.file] = &fstest.MapFile{Data: changed}
				// 重算外層hash，確保反例驗到內容閘門，而非僅撞到檔案hash。
				m["files_sha256"].(map[string]any)[test.file] = draftDigest(changed)
			}
			overlay["ja/manifest.json"] = &fstest.MapFile{Data: draftEncode(t, m)}
			p, err := draftPrepareBundle(draftOverlayFS{base: base, overlay: overlay}, "ja", needs)
			if err == nil || p != nil {
				t.Fatal("corrupt preparation must return no candidate", test.name)
			}
		})
	}
	t.Run("missing-file", func(t *testing.T) {
		p, err := draftPrepareBundle(draftOverlayFS{base: base, missing: "ja/text/draft.zh-Hant.tsv"}, "ja", needs)
		if err == nil || p != nil {
			t.Fatal("missing file accepted")
		}
	})
	t.Run("unknown-locale", func(t *testing.T) {
		p, err := draftPrepareBundle(base, "../ja", needs)
		if err == nil || p != nil {
			t.Fatal("unknown locale accepted")
		}
	})
}
