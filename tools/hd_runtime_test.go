package main

import (
	"bytes"
	"encoding/json"
	"image"
	"os"
	"path/filepath"
	"sort"
	"testing"

	golem "github.com/wicanr2/dosgolem"
)

func hdResourceOriginalFiles() []string {
	files := []string{"OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK", "VICEROY.EXE", "BUILDING.SS", "PHYS0.SS", "TERRAIN.SS", "ICONS.SS", "CURSOR.SS", "OPENTILE.SS", "OPENMENU.PIK", "WOODTILE.SS", "PARCH.SS", "DIFFICUL.PIK", "NATIONS.PIK", "CUSTOMIZ.PIK", "KING1.SS"}
	seen := map[string]bool{}
	for _, name := range files {
		seen[name] = true
	}
	// 完整測試副本也需要片頭逐幀來源；依目前固定定義去重。
	for _, frame := range hdOpeningSpriteDefinitions {
		if !seen[frame.sourceFile] {
			files = append(files, frame.sourceFile)
			seen[frame.sourceFile] = true
		}
	}
	for _, frame := range hdSceneDefinitions {
		if !seen[frame.file] {
			files = append(files, frame.file)
			seen[frame.file] = true
		}
	}
	return files
}

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
	for _, name := range hdResourceOriginalFiles() {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版", name)
		}
	}
	m := golem.New()
	before := bytes.Clone(m.Mem)
	h, err := loadHDRuntime(m, game, assets)
	if err != nil || h == nil || h.scenes == nil || len(h.scenes.frames) != 158 || h.terrainBatch == nil || len(h.terrainBatch.frames) != 114 || h.smallTerrain == nil || len(h.smallTerrain.frames) != 28 || h.terrainTextures == nil || len(h.terrainTextures.frames) != 12 || h.parch == nil || h.worldTexture == nil || h.texture == nil || h.small == nil || len(h.small.frames) != 124 || h.nine == nil || len(h.nine.frames) != len(hdNineFrames) || h.shelter == nil || h.shelter.art.Bounds() != image.Rect(0, 0, 92, 108) || h.sea == nil || h.person == nil || h.person.art.Bounds() != image.Rect(0, 0, 24, 64) || h.sea.art.Bounds() != image.Rect(0, 0, 64, 64) || h.art.Bounds() != image.Rect(0, 0, 92, 108) || !bytes.Equal(before, m.Mem) {
		t.Fatal("正式素材載入失敗或改寫原版", err)
	}
	mutations := map[string]func(string, string){
		"missing-event-picture": func(a, g string) { os.Remove(filepath.Join(a, "wdcut01-000.png")) },
		"bad-event-frame":       func(a, g string) { os.WriteFile(filepath.Join(a, "woodfram-000.png"), []byte("bad"), 0644) },
		"linked-event-nameplate": func(a, g string) {
			os.Remove(filepath.Join(a, "nameplat-001.png"))
			os.Symlink(filepath.Join(assets, "nameplat-001.png"), filepath.Join(a, "nameplat-001.png"))
		},
		"missing-scaled-town":   func(a, g string) { os.Remove(filepath.Join(a, "icons-003.png")) },
		"bad-scaled-settlement": func(a, g string) { os.WriteFile(filepath.Join(a, "icons-011.png"), []byte("bad"), 0644) },
		"linked-scaled-flag": func(a, g string) {
			os.Remove(filepath.Join(a, "icons-118.png"))
			os.Symlink(filepath.Join(os.Getenv("TEST_HD_ASSETS"), "icons-118.png"), filepath.Join(a, "icons-118.png"))
		},
		"missing-terrain-remaining": func(a, g string) { os.Remove(filepath.Join(a, "terrain-037.png")) },
		"bad-terrain-remaining":     func(a, g string) { os.WriteFile(filepath.Join(a, "terrain-095.png"), []byte("wrong"), 0644) },
		"linked-terrain-remaining": func(a, g string) {
			p := filepath.Join(a, "terrain-098.png")
			os.Remove(p)
			os.Symlink(filepath.Join(g, "PHYS0.SS"), p)
		},
		"missing-foreground":        func(a, g string) { os.Remove(filepath.Join(a, "terrain-022.png")) },
		"bad-foreground":            func(a, g string) { os.WriteFile(filepath.Join(a, "terrain-064.png"), []byte("wrong"), 0644) },
		"wrong-foreground-original": func(a, g string) { os.WriteFile(filepath.Join(g, "PHYS0.SS"), []byte("wrong"), 0644) },

		"missing-terrain-texture": func(a, g string) { os.Remove(filepath.Join(a, "terrain-texture-011.png")) },
		"bad-terrain-texture":     func(a, g string) { os.WriteFile(filepath.Join(a, "terrain-texture-011.png"), []byte("wrong"), 0644) },
		"wrong-terrain-original":  func(a, g string) { os.WriteFile(filepath.Join(g, "TERRAIN.SS"), []byte("wrong"), 0644) },
		"missing-hammer":          func(a, g string) { os.Remove(filepath.Join(a, "icons-054.png")) },
		"missing-manifest":        func(a, g string) { os.Remove(filepath.Join(a, "manifest.json")) },
		"bad-manifest":            func(a, g string) { os.WriteFile(filepath.Join(a, "manifest.json"), []byte("{}"), 0644) },
		"oversized-manifest": func(a, g string) {
			os.WriteFile(filepath.Join(a, "manifest.json"), bytes.Repeat([]byte("x"), (16<<20)+1), 0644)
		},
		"missing-image": func(a, g string) { os.Remove(filepath.Join(a, "building-032.png")) },
		"bad-image":     func(a, g string) { os.WriteFile(filepath.Join(a, "building-032.png"), []byte("bad"), 0644) },
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
	for _, filename := range []string{"opentile-000.png", "openmenu-000.png", "woodtile-000.png", "parch-000.png", "difficul-000.png", "nations-000.png", "customiz-000.png"} {
		mutations["missing-"+filename] = func(a, g string) { os.Remove(filepath.Join(a, filename)) }
		mutations["bad-"+filename] = func(a, g string) { os.WriteFile(filepath.Join(a, filename), []byte("wrong"), 0644) }
		mutations["linked-"+filename] = func(a, g string) {
			p := filepath.Join(a, filename)
			os.Remove(p)
			os.Symlink(filepath.Join(assets, filename), p)
		}
	}

	mutations["missing-terrain079"] = func(a, g string) { os.Remove(filepath.Join(a, "terrain-079.png")) }
	mutations["bad-terrain079"] = func(a, g string) { os.WriteFile(filepath.Join(a, "terrain-079.png"), []byte("wrong"), 0644) }
	mutations["linked-terrain079"] = func(a, g string) {
		p := filepath.Join(a, "terrain-079.png")
		os.Remove(p)
		os.Symlink(filepath.Join(assets, "terrain-079.png"), p)
	}
	for _, frame := range hdOpeningDefinitions {
		filename := frame.asset
		mutations["missing-"+filename] = func(a, g string) { os.Remove(filepath.Join(a, filename)) }
		mutations["bad-"+filename] = func(a, g string) { os.WriteFile(filepath.Join(a, filename), []byte("wrong"), 0644) }
		mutations["linked-"+filename] = func(a, g string) {
			p := filepath.Join(a, filename)
			os.Remove(p)
			os.Symlink(filepath.Join(assets, filename), p)
		}
	}

	requiredCases := make([]string, 0, len(mutations))
	for name := range mutations {
		requiredCases = append(requiredCases, name)
	}
	sort.Strings(requiredCases)
	if path := os.Getenv("TEST_HD_RESOURCE_CASE_CATALOG"); path != "" {
		raw, err := json.Marshal(requiredCases)
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(path, raw, 0644); err != nil {
			t.Fatal(err)
		}
		if os.Getenv("TEST_HD_RESOURCE_CASE_CATALOG_ONLY") == "1" {
			return
		}
	}
	selectedCases := requiredCases
	if path := os.Getenv("TEST_HD_RESOURCE_CASE_SELECTION"); path != "" {
		raw, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		if err = json.Unmarshal(raw, &selectedCases); err != nil {
			t.Fatal(err)
		}
		if len(selectedCases) == 0 {
			t.Fatal("資源案例批次不可為空")
		}
		seen := map[string]bool{}
		for _, name := range selectedCases {
			if _, ok := mutations[name]; !ok || seen[name] {
				t.Fatal("資源案例不存在或重複", name)
			}
			seen[name] = true
		}
	}
	a, g := filepath.Join(t.TempDir(), "graphics"), filepath.Join(t.TempDir(), "game")
	for _, p := range []string{a, g} {
		if err := os.Mkdir(p, 0755); err != nil {
			t.Fatal(err)
		}
	}
	entries, e := os.ReadDir(assets)
	if e != nil {
		t.Fatal(e)
	}
	for _, entry := range entries {
		if !entry.Type().IsRegular() {
			t.Fatal("素材來源型態不同", entry.Name())
		}
		n := entry.Name()
		if e := os.WriteFile(filepath.Join(a, n), readFile(filepath.Join(assets, n)), 0644); e != nil {
			t.Fatal(e)
		}
	}
	for _, n := range hdResourceOriginalFiles() {
		if err := os.WriteFile(filepath.Join(g, n), readFile(filepath.Join(game, n)), 0644); err != nil {
			t.Fatal(err)
		}
	}
	fixtureMachine := golem.New()
	fixtureMemory := hash(fixtureMachine.Mem)
	fixtureHD, e := loadHDRuntime(fixtureMachine, g, a)
	if e != nil || fixtureHD == nil || hash(fixtureMachine.Mem) != fixtureMemory {
		t.Fatal("完整HD測試副本無法載入", e)
	}
	restoreFixture := hdRestoreResourceFixture(t, a, g)
	for _, name := range selectedCases {
		mutate := mutations[name]
		t.Run(name, func(t *testing.T) {
			defer restoreFixture(t)
			caseMachine := golem.New()
			caseMemory := hash(caseMachine.Mem)
			mutate(a, g)
			bad, err := loadHDRuntime(caseMachine, g, a)
			if bad != nil || err == nil || hash(caseMachine.Mem) != caseMemory {
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

func hdRestoreResourceFixture(t *testing.T, directories ...string) func(*testing.T) {
	t.Helper()
	original := map[string][]byte{}
	for _, directory := range directories {
		entries, err := os.ReadDir(directory)
		if err != nil {
			t.Fatal(err)
		}
		for _, entry := range entries {
			if !entry.Type().IsRegular() {
				t.Fatal("基準副本含非普通檔案", entry.Name())
			}
			path := filepath.Join(directory, entry.Name())
			raw, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			original[path] = raw
		}
	}
	return func(t *testing.T) {
		t.Helper()
		for _, directory := range directories {
			entries, err := os.ReadDir(directory)
			if err != nil {
				t.Fatal(err)
			}
			for _, entry := range entries {
				if _, ok := original[filepath.Join(directory, entry.Name())]; !ok {
					t.Fatal("測試副本出現未知檔案", entry.Name())
				}
			}
		}
		for path, raw := range original {
			info, err := os.Lstat(path)
			if err != nil && !os.IsNotExist(err) {
				t.Fatal(err)
			}
			if err == nil && info.Mode().IsRegular() {
				current, e := os.ReadFile(path)
				if e != nil {
					t.Fatal(e)
				}
				if bytes.Equal(current, raw) {
					continue
				}
			}
			if err == nil {
				if e := os.Remove(path); e != nil {
					t.Fatal(e)
				}
			}
			if e := os.WriteFile(path, raw, 0644); e != nil {
				t.Fatal(e)
			}
			info, e := os.Lstat(path)
			if e != nil || !info.Mode().IsRegular() {
				t.Fatal("復原後檔案型態不同", path, e)
			}
			current, e := os.ReadFile(path)
			if e != nil || !bytes.Equal(current, raw) {
				t.Fatal("復原後內容不同", path, e)
			}
		}
	}
}
