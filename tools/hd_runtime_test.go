package main

import (
	"bytes"
	"image"
	"os"
	"path/filepath"
	"testing"

	golem "github.com/wicanr2/dosgolem"
)

func TestHDResourceAndStartupFallback(t *testing.T) {
	game, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS")
	if game == "" || assets == "" {
		t.Skip("需合法原版與已驗生成HD素材")
	}
	readFile := func(path string) []byte {
		t.Helper()
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return raw
	}
	for _, name := range []string{"VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "ICONS.SS"} {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版", name)
		}
	}
	m := golem.New()
	before := bytes.Clone(m.Mem)
	h, err := loadHDRuntime(m, game, assets)
	if err != nil || h == nil || h.sea == nil || h.person == nil || h.person.art.Bounds() != image.Rect(0, 0, 24, 64) || h.sea.art.Bounds() != image.Rect(0, 0, 64, 64) || h.art.Bounds() != image.Rect(0, 0, 92, 108) || !bytes.Equal(before, m.Mem) {
		t.Fatal("正式素材載入失敗或改寫原版", err)
	}
	for name, mutate := range map[string]func(string, string){
		"missing-manifest": func(a, g string) { os.Remove(filepath.Join(a, "manifest.json")) },
		"bad-manifest":     func(a, g string) { os.WriteFile(filepath.Join(a, "manifest.json"), []byte("{}"), 0644) },
		"missing-image":    func(a, g string) { os.Remove(filepath.Join(a, "building-032.png")) },
		"bad-image":        func(a, g string) { os.WriteFile(filepath.Join(a, "building-032.png"), []byte("bad"), 0644) },
		"linked-image": func(a, g string) {
			p := filepath.Join(a, "building-032.png")
			os.Remove(p)
			os.Symlink(filepath.Join(assets, "building-032.png"), p)
		},
		"wrong-building":   func(a, g string) { os.WriteFile(filepath.Join(g, "BUILDING.SS"), []byte("wrong"), 0644) },
		"wrong-executable": func(a, g string) { os.WriteFile(filepath.Join(g, "VICEROY.EXE"), []byte("wrong"), 0644) },
		"missing-sea":      func(a, g string) { os.Remove(filepath.Join(a, "sea-148.png")) },
		"bad-sea":          func(a, g string) { os.WriteFile(filepath.Join(a, "sea-148.png"), []byte("wrong"), 0644) },
		"linked-sea": func(a, g string) {
			p := filepath.Join(a, "sea-148.png")
			os.Remove(p)
			os.Symlink(filepath.Join(assets, "sea-148.png"), p)
		},
		"missing-phys0":  func(a, g string) { os.Remove(filepath.Join(g, "PHYS0.SS")) },
		"missing-person": func(a, g string) { os.Remove(filepath.Join(a, "person-100.png")) },
		"bad-person":     func(a, g string) { os.WriteFile(filepath.Join(a, "person-100.png"), []byte("wrong"), 0644) },
		"linked-person": func(a, g string) {
			p := filepath.Join(a, "person-100.png")
			os.Remove(p)
			os.Symlink(filepath.Join(assets, "person-100.png"), p)
		},
		"missing-icons": func(a, g string) { os.Remove(filepath.Join(g, "ICONS.SS")) },
		"wrong-icons":   func(a, g string) { os.WriteFile(filepath.Join(g, "ICONS.SS"), []byte("wrong"), 0644) },
		"linked-icons": func(a, g string) {
			p := filepath.Join(g, "ICONS.SS")
			os.Remove(p)
			os.Symlink(filepath.Join(game, "ICONS.SS"), p)
		},
		"wrong-phys0": func(a, g string) { os.WriteFile(filepath.Join(g, "PHYS0.SS"), []byte("wrong"), 0644) },
		"linked-phys0": func(a, g string) {
			p := filepath.Join(g, "PHYS0.SS")
			os.Remove(p)
			os.Symlink(filepath.Join(game, "PHYS0.SS"), p)
		},
	} {
		t.Run(name, func(t *testing.T) {
			a, g := filepath.Join(t.TempDir(), "graphics"), filepath.Join(t.TempDir(), "game")
			for _, p := range []string{a, g} {
				if err := os.Mkdir(p, 0755); err != nil {
					t.Fatal(err)
				}
			}
			for _, n := range []string{"manifest.json", "building-032.png", "sea-148.png", "person-100.png"} {
				if err := os.WriteFile(filepath.Join(a, n), readFile(filepath.Join(assets, n)), 0644); err != nil {
					t.Fatal(err)
				}
			}
			for _, n := range []string{"VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "ICONS.SS"} {
				if err := os.WriteFile(filepath.Join(g, n), readFile(filepath.Join(game, n)), 0644); err != nil {
					t.Fatal(err)
				}
			}
			mutate(a, g)
			bad, err := loadHDRuntime(m, g, a)
			if bad != nil || err == nil || !bytes.Equal(before, m.Mem) {
				t.Fatal("缺件或錯件未拒絕，或改寫原版", err)
			}
		})
	}
	for _, locale := range displayUILanguages {
		for _, available := range []bool{false, true} {
			options := displayOptions{locale, "hd"}
			var loaded *hdRuntime
			if available {
				loaded = h
			}
			effective := hdStartupOptions(loaded, options)
			want := displayOptions{locale, "original"}
			if available {
				want = options
			}
			if effective != want || options.Graphics != "hd" {
				t.Fatal("啟動回退改變語言或輸入偏好", locale)
			}
		}
	}
}

func TestHDMissingResourcePreservesPreferenceAndTransaction(t *testing.T) {
	target := &draftLanguageTarget{pack: &draftPreparedBundle{manifest: draftBundleManifest{Locale: "en", Original: true}}}
	f := draftNativeFrame{journal: &nativeJournal{enabled: true}, canvas: make([]byte, 64000), buffer: make([]byte, 64000), indexed: make([]byte, 64000), palette: make([]byte, 768), mode: 0x13}
	b := &draftLanguageBackend{targets: map[string]*draftLanguageTarget{"en": target}, sample: func() draftNativeFrame { return f }}
	path := filepath.Join(t.TempDir(), "display.json")
	saved := displayOptions{"en", "hd"}
	if err := writeDisplayPreferences(path, saved); err != nil {
		t.Fatal(err)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	options, err := readDisplayPreferences(path, "", "")
	if err != nil {
		t.Fatal(err)
	}
	effective := hdStartupOptions(nil, options)
	commit, err := b.prepare(effective)
	if err != nil {
		t.Fatal(err)
	}
	commit()
	old := b.active
	if old.options != (displayOptions{"en", "original"}) {
		t.Fatal("缺件後未以原版啟動")
	}
	if err := applyDisplayPreferences(path, saved, b.prepare); err == nil {
		t.Fatal("缺件仍允許HD交易")
	}
	after, err := os.ReadFile(path)
	if err != nil || !bytes.Equal(raw, after) || b.active != old {
		t.Fatal("啟動回退或Apply失敗改變偏好／生效資料", err)
	}
}
