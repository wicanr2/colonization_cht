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
	for _, name := range []string{"VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "ICONS.SS", "CURSOR.SS", "OPENTILE.SS", "OPENMENU.PIK", "WOODTILE.SS"} {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版", name)
		}
	}
	m := golem.New()
	before := bytes.Clone(m.Mem)
	h, err := loadHDRuntime(m, game, assets)
	if err != nil || h == nil || h.terrainBatch == nil || len(h.terrainBatch.frames) != 12 || h.smallTerrain == nil || len(h.smallTerrain.frames) != 8 || h.worldTexture == nil || h.texture == nil || h.small == nil || len(h.small.frames) != 31 || h.nine == nil || len(h.nine.frames) != 10 || h.shelter == nil || h.shelter.art.Bounds() != image.Rect(0, 0, 92, 108) || h.sea == nil || h.person == nil || h.person.art.Bounds() != image.Rect(0, 0, 24, 64) || h.sea.art.Bounds() != image.Rect(0, 0, 64, 64) || h.art.Bounds() != image.Rect(0, 0, 92, 108) || !bytes.Equal(before, m.Mem) {
		t.Fatal("正式素材載入失敗或改寫原版", err)
	}
	mutations := map[string]func(string, string){
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
		"missing-shelter": func(a, g string) { os.Remove(filepath.Join(a, "building-024.png")) },
		"bad-shelter":     func(a, g string) { os.WriteFile(filepath.Join(a, "building-024.png"), []byte("wrong"), 0644) },
		"linked-shelter": func(a, g string) {
			p := filepath.Join(a, "building-024.png")
			os.Remove(p)
			os.Symlink(filepath.Join(assets, "building-024.png"), p)
		},
		"missing-cursor-image": func(a, g string) { os.Remove(filepath.Join(a, "cursor-000.png")) },
		"bad-cursor-image":     func(a, g string) { os.WriteFile(filepath.Join(a, "cursor-000.png"), []byte("wrong"), 0644) },
		"linked-cursor-image": func(a, g string) {
			p := filepath.Join(a, "cursor-000.png")
			os.Remove(p)
			os.Symlink(filepath.Join(assets, "cursor-000.png"), p)
		},
		"missing-cursor-source": func(a, g string) { os.Remove(filepath.Join(g, "CURSOR.SS")) },
		"bad-cursor-source":     func(a, g string) { os.WriteFile(filepath.Join(g, "CURSOR.SS"), []byte("wrong"), 0644) },
		"linked-cursor-source": func(a, g string) {
			p := filepath.Join(g, "CURSOR.SS")
			os.Remove(p)
			os.Symlink(filepath.Join(game, "CURSOR.SS"), p)
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
	}
	for _, frame := range hdNineFrames {
		filename := frame.file
		mutations["missing-"+filename] = func(a, g string) { os.Remove(filepath.Join(a, filename)) }
		mutations["bad-"+filename] = func(a, g string) { os.WriteFile(filepath.Join(a, filename), []byte("wrong"), 0644) }
		mutations["linked-"+filename] = func(a, g string) {
			p := filepath.Join(a, filename)
			os.Remove(p)
			os.Symlink(filepath.Join(assets, filename), p)
		}
	}
	for _, frame := range hdSmallFrames {
		if frame.file == "" {
			continue
		}
		filename := frame.file
		mutations["missing-"+filename] = func(a, g string) { os.Remove(filepath.Join(a, filename)) }
		mutations["bad-"+filename] = func(a, g string) { os.WriteFile(filepath.Join(a, filename), []byte("wrong"), 0644) }
		mutations["linked-"+filename] = func(a, g string) {
			p := filepath.Join(a, filename)
			os.Remove(p)
			os.Symlink(filepath.Join(assets, filename), p)
		}
	}
	for _, frame := range hdTerrainBatchDefinitions {
		filename := frame.asset
		mutations["missing-"+filename] = func(a, g string) { os.Remove(filepath.Join(a, filename)) }
		mutations["bad-"+filename] = func(a, g string) { os.WriteFile(filepath.Join(a, filename), []byte("wrong"), 0644) }
		mutations["linked-"+filename] = func(a, g string) {
			p := filepath.Join(a, filename)
			os.Remove(p)
			os.Symlink(filepath.Join(assets, filename), p)
		}
	}
	for _, frame := range hdSmallTerrainDefinitions {
		filename := frame.asset
		mutations["missing-"+filename] = func(a, g string) { os.Remove(filepath.Join(a, filename)) }
		mutations["bad-"+filename] = func(a, g string) { os.WriteFile(filepath.Join(a, filename), []byte("wrong"), 0644) }
		mutations["linked-"+filename] = func(a, g string) {
			p := filepath.Join(a, filename)
			os.Remove(p)
			os.Symlink(filepath.Join(assets, filename), p)
		}
	}
	for _, filename := range []string{"opentile-000.png", "openmenu-000.png", "woodtile-000.png"} {
		mutations["missing-"+filename] = func(a, g string) { os.Remove(filepath.Join(a, filename)) }
		mutations["bad-"+filename] = func(a, g string) { os.WriteFile(filepath.Join(a, filename), []byte("wrong"), 0644) }
		mutations["linked-"+filename] = func(a, g string) {
			p := filepath.Join(a, filename)
			os.Remove(p)
			os.Symlink(filepath.Join(assets, filename), p)
		}
	}
	for name, mutate := range mutations {
		t.Run(name, func(t *testing.T) {
			a, g := filepath.Join(t.TempDir(), "graphics"), filepath.Join(t.TempDir(), "game")
			for _, p := range []string{a, g} {
				if err := os.Mkdir(p, 0755); err != nil {
					t.Fatal(err)
				}
			}
			for _, n := range []string{"manifest.json", "building-032.png", "sea-148.png", "person-100.png", "building-024.png", "building-016.png", "building-021.png", "building-027.png", "building-035.png", "building-039.png", "building-042.png", "building-043.png", "building-044.png", "building-045.png", "building-009.png", "icons-022.png", "icons-024.png", "icons-025.png", "icons-026.png", "icons-027.png", "icons-028.png", "icons-029.png", "icons-030.png", "icons-031.png", "icons-032.png", "icons-033.png", "icons-034.png", "icons-035.png", "icons-036.png", "icons-037.png", "icons-038.png", "icons-005.png", "icons-023.png", "icons-042.png", "icons-053.png", "icons-056.png", "icons-059.png", "icons-062.png", "icons-067.png", "icons-068.png", "icons-069.png", "icons-094.png", "icons-122.png", "icons-123.png", "icons-124.png", "terrain-079.png", "cursor-000.png", "terrain-006.png", "terrain-009.png", "terrain-017.png", "terrain-066.png", "terrain-071.png", "terrain-074.png", "terrain-077.png", "terrain-078.png", "terrain-080.png", "terrain-096.png", "terrain-147.png", "terrain-150.png", "terrain-112.png", "terrain-113.png", "terrain-116.png", "terrain-119.png", "terrain-126.png", "terrain-127.png", "terrain-136.png", "terrain-139.png", "opentile-000.png", "openmenu-000.png", "woodtile-000.png"} {
				if err := os.WriteFile(filepath.Join(a, n), readFile(filepath.Join(assets, n)), 0644); err != nil {
					t.Fatal(err)
				}
			}
			for _, n := range []string{"VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "ICONS.SS", "CURSOR.SS", "OPENTILE.SS", "OPENMENU.PIK", "WOODTILE.SS"} {
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
