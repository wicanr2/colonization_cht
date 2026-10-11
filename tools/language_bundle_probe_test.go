package main

import (
	"encoding/json"
	"io/fs"
	"os"
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
	needs, err := draftIndexedRequirements()
	if err != nil {
		t.Fatal(err)
	}
	return os.DirFS(root), needs
}

func TestDraftResourceIndexOwnsExpectations(t *testing.T) {
	a, err := draftIndexedRequirements()
	if err != nil || len(a.Tables) != 13 || len(a.Masks) != 64 {
		t.Fatal("compiled index incomplete", err)
	}
	first := a.Tables[0]
	var file string
	var original draftMaskRequirement
	for key, value := range a.Masks {
		file, original = key, value
		break
	}
	a.Tables[0] = "candidate-controlled.tsv"
	a.Masks[file] = draftMaskRequirement{}
	b, err := draftIndexedRequirements()
	if err != nil || b.Tables[0] != first || b.Masks[file] != original {
		t.Fatal("requirements alias another preparation", err)
	}
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
