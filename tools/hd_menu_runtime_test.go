package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestHDMenuRegressionNative89(t *testing.T) {
	game, reference, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_TEXTURE_REFERENCE"), os.Getenv("TEST_TEXTURE_OUTPUT")
	if game == "" || reference == "" || out == "" {
		t.Skip("需要合法原版及正常GUI前綴")
	}
	for _, n := range []string{"OPENING.EXE", "VICEROY.EXE", "OPENTILE.SS"} {
		if _, err := os.Stat(filepath.Join(game, n)); os.IsNotExist(err) {
			t.Skip("缺合法原版", n)
		}
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(p string) []byte { t.Helper(); b, err := os.ReadFile(p); need(err); return b }
	var replay struct {
		Inputs []windowInput
		End    uint64
	}
	raw := read(os.Getenv("TEST_TEXTURE_INPUTS"))
	if hash(raw) != "8b2b05308d091046379eca38e760f5fbf57fa863625ad53f78b8d3b30dab6b58" {
		t.Fatal("原始輸入不同")
	}
	need(json.Unmarshal(raw, &replay))
	type state struct {
		Steps     uint64
		Count     uint64 `json:"dos_input_count"`
		Memory    string `json:"memory_sha256"`
		Indexed   string `json:"indexed_sha256"`
		Palette   string `json:"palette_sha256"`
		Registers [8]uint16
		Segments  [4]uint16
		IP, Flags uint16
		Cycles    uint64
	}
	var oracle struct {
		Checkpoints []state
		End         state
	}
	need(json.Unmarshal(read(filepath.Join(reference, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 89 || oracle.End.Steps != 280665001 {
		t.Fatal("四點範圍不同")
	}
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "save")
	need(os.Mkdir(scratch, 0755))
	seed := read(os.Getenv("TEST_TEXTURE_SEED"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("原始存檔不同")
	}
	need(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("缺數位音訊")
	}
	m.EnableOPLSynth(true)
	h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))
	need(err)
	// 本項只隔離主選單圖層；世界木紋由TestHDWorldWoodNative89另驗。
	h.worldTexture = nil
	p := h.texture
	if p == nil {
		t.Fatal("底紋原型未載入")
	}
	m.SetBeforeInstruction(h.beforeInstruction)
	checkState := func(s state) {
		t.Helper()
		c := m.CPU
		if hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("原版完整狀態不同", m.Steps)
		}
	}
	at, count := 0, uint64(0)
	var records []map[string]any
	totalPixels := 0
	seenLarge := false
	var model struct {
		Transfers map[string]uint64 `json:"texture_transfer_writes"`
		Cursor    map[string]uint64 `json:"texture_cursor_pairs"`
	}
	need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_TEXTURE_MODEL"), "check.json")), &model))
	capture := func() {
		if at == 89 {
			return
		}
		s := oracle.Checkpoints[at]
		if m.Steps > s.Steps || (m.Steps == s.Steps && count > s.Count) {
			t.Fatal("略過原版點", at)
		}
		if m.Steps != s.Steps || count != s.Count {
			return
		}
		checkState(s)
		var want map[int]struct {
			ID     int  `json:"source_id"`
			Local  int  `json:"local"`
			Native byte `json:"native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_TEXTURE_MODEL"), fmt.Sprintf("point-%03d.texture-owners.json", at))), &want))
		for k, w := range want {
			if w.ID != 1265 {
				delete(want, k)
			}
		}
		owned := map[int]hdTextureCell{}
		for a, c := range p.owners {
			if a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
				owned[int(a-hdBuildingCanvas)] = c
			}
		}
		if len(owned) != len(want) {
			t.Fatal("來源格數不同", len(owned), len(want))
		}
		largeLocal := false
		for k, w := range want {
			c, ok := owned[k]
			if !ok || w.ID != 1265 || int(c.local) != w.Local || c.native != w.Native {
				t.Fatal("獨立來源模型不同", at, k, c, w)
			}
			largeLocal = largeLocal || w.Local > 255
		}
		seenLarge = seenLarge || largeLocal
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		h.texture = nil
		baseline, _ := h.base(f)
		h.texture = p
		im, receipt := h.base(f)
		h.restoreCursor(im, f)
		h.cursor.paint(h, im, f)
		h.restoreCursor(baseline, f)
		h.cursor.paint(h, baseline, f)
		pixels := 0
		supported := hash(f.palette) == hdTexturePaletteSHA
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				k := (y/4)*320 + x/4
				c, ok := owned[k]
				if !ok || !supported {
					if im.RGBAAt(x, y) != baseline.RGBAAt(x, y) {
						t.Fatal("來源外像素被改", at, x, y)
					}
					continue
				}
				sx, sy := int(c.local)%32*4+x%4, int(c.local)/32*4+y%4
				if im.RGBAAt(x, y) != p.art.RGBAAt(sx, sy) {
					t.Fatal("底紋RGBA不同", at, x, y)
				}
				pixels++
			}
		}
		if supported && pixels != len(owned)*16 {
			t.Fatal("像素數不同", pixels)
		}
		totalPixels += pixels
		checkState(s)
		// 未證實色盤維持原版，原本合成畫布不能被改。
		unsupported := f
		unsupported.palette = append([]byte(nil), f.palette...)
		unsupported.palette[0] ^= 1
		n := image.NewRGBA(im.Bounds())
		copy(n.Pix, baseline.Pix)
		record := p.paint(n, unsupported)
		if record["painted"].(int) != 0 || !bytes.Equal(n.Pix, baseline.Pix) {
			t.Fatal("未證實色盤沒有回退")
		}
		// 任何未知同值寫入撤銷已驗來源。
		clone := *p
		clone.owners = map[uint32]hdTextureCell{}
		for a, c := range p.owners {
			clone.owners[a] = c
		}
		hh := *h
		hh.m = golem.New()
		copy(hh.m.Mem, m.Mem)
		clone.h = &hh
		clone.active = false
		clone.pending = map[uint32]hdTexturePair{}
		clone.underlays = map[uint32]hdTextureUnderlay{}
		for k, c := range owned {
			a := hdBuildingCanvas + uint32(k)
			clone.memoryWrite(a, c.native, c.native)
			if _, ok := clone.owners[a]; ok {
				t.Fatal("同值未知寫入未撤銷")
			}
			break
		}
		name := filepath.Join(out, fmt.Sprintf("point-%03d", at))
		file, err := os.Create(name + ".png")
		need(err)
		need(png.Encode(file, im))
		need(file.Close())
		file, err = os.Create(name + ".baseline.png")
		need(err)
		need(png.Encode(file, baseline))
		need(file.Close())
		receipt["step"], receipt["point"], receipt["verified_rgba_pixels"] = m.Steps, at, pixels
		records = append(records, receipt)
		at++
	}
	step := func() { capture(); need(m.Step()) }
	for _, e := range replay.Inputs {
		if e.Step > 280665001 {
			break
		}
		for m.Steps < e.Step {
			step()
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < 280665001 {
		step()
	}
	capture()
	checkState(oracle.End)
	if at != 89 || count != 165 || p.accepted != 1 || p.rejected != 0 || p.transferred != model.Transfers["1265"] || p.cursorRestores != model.Cursor["1265"] {
		t.Fatal("原版來源範圍不同", at, count, p.accepted, p.rejected, p.transferred)
	}
	if !bytes.Equal(m.Mem, read(filepath.Join(reference, "control/final.memory"))) {
		t.Fatal("原版終點RAM不同")
	}
	d.Close()
	for _, n := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		if !bytes.Equal(read(filepath.Join(scratch, n)), read(filepath.Join(reference, "control/saves", n))) {
			t.Fatal("原版存檔不同", n)
		}
	}
	proof := map[string]any{"result": "PASS_TEXTURE_ISOLATED_NATIVE_89_GUI_POINTS", "production_connected": true, "checkpoints": 89, "dos_inputs": 165, "accepted": p.accepted, "transferred": p.transferred, "rgba_pixels": totalPixels, "large_index_positive_in_this_cohort": seenLarge, "cursor_source_restores": p.cursorRestores, "original_state_and_saves_equal": true, "points": records}
	raw, err = json.MarshalIndent(proof, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDMenuNative12(t *testing.T) {
	game, reference, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_MENU_REFERENCE"), os.Getenv("TEST_MENU_OUTPUT")
	if game == "" || reference == "" || out == "" {
		t.Skip("需要合法原版及正常GUI前綴")
	}
	for _, n := range []string{"OPENING.EXE", "VICEROY.EXE", "OPENTILE.SS"} {
		if _, err := os.Stat(filepath.Join(game, n)); os.IsNotExist(err) {
			t.Skip("缺合法原版", n)
		}
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(p string) []byte { t.Helper(); b, err := os.ReadFile(p); need(err); return b }
	var replay struct {
		Inputs []windowInput
		End    uint64
	}
	raw := read(os.Getenv("TEST_MENU_INPUTS"))
	if hash(raw) != "339f8741b8523f2f75f99a2670680f6b68666b69ad224eb97dd6c3b432be1826" {
		t.Fatal("原始輸入不同")
	}
	need(json.Unmarshal(raw, &replay))
	type state struct {
		Steps     uint64
		Count     uint64 `json:"dos_input_count"`
		Memory    string `json:"memory_sha256"`
		Indexed   string `json:"indexed_sha256"`
		Palette   string `json:"palette_sha256"`
		Registers [8]uint16
		Segments  [4]uint16
		IP, Flags uint16
		Cycles    uint64
	}
	var oracle struct {
		Checkpoints []state
		End         state
	}
	need(json.Unmarshal(read(filepath.Join(reference, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 12 || oracle.End.Steps != 27885000 {
		t.Fatal("四點範圍不同")
	}
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "save")
	need(os.Mkdir(scratch, 0755))
	seed := read(os.Getenv("TEST_TEXTURE_SEED"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("原始存檔不同")
	}
	need(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("缺數位音訊")
	}
	m.EnableOPLSynth(true)
	h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))
	need(err)
	p := h.texture
	if p == nil {
		t.Fatal("底紋原型未載入")
	}
	m.SetBeforeInstruction(h.beforeInstruction)
	checkState := func(s state) {
		t.Helper()
		c := m.CPU
		if hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("原版完整狀態不同", m.Steps)
		}
	}
	at, count := 0, uint64(0)
	var records []map[string]any
	totalPixels := 0
	seenLarge := false
	var model struct {
		Transfers map[string]uint64 `json:"texture_transfer_writes"`
		Cursor    map[string]uint64 `json:"texture_cursor_pairs"`
	}
	need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_MENU_MODEL"), "check.json")), &model))
	capture := func() {
		if at == 12 {
			return
		}
		s := oracle.Checkpoints[at]
		if m.Steps > s.Steps || (m.Steps == s.Steps && count > s.Count) {
			t.Fatal("略過原版點", at)
		}
		if m.Steps != s.Steps || count != s.Count {
			return
		}
		checkState(s)
		var want map[int]struct {
			ID     int  `json:"source_id"`
			Local  int  `json:"local"`
			Native byte `json:"native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_MENU_MODEL"), fmt.Sprintf("point-%03d.texture-owners.json", at))), &want))
		for k, w := range want {
			if w.ID != 1265 {
				delete(want, k)
			}
		}
		owned := map[int]hdTextureCell{}
		for a, c := range p.owners {
			if a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
				owned[int(a-hdBuildingCanvas)] = c
			}
		}
		if len(owned) != len(want) {
			t.Fatal("來源格數不同", len(owned), len(want))
		}
		largeLocal := false
		for k, w := range want {
			c, ok := owned[k]
			if !ok || w.ID != 1265 || int(c.local) != w.Local || c.native != w.Native {
				t.Fatal("獨立來源模型不同", at, k, c, w)
			}
			largeLocal = largeLocal || w.Local > 255
		}
		seenLarge = seenLarge || largeLocal
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		h.texture = nil
		baseline, _ := h.base(f)
		h.texture = p
		im, receipt := h.base(f)
		h.restoreCursor(im, f)
		h.cursor.paint(h, im, f)
		h.restoreCursor(baseline, f)
		h.cursor.paint(h, baseline, f)
		var wantUnder map[int]struct {
			ID     int  `json:"source_id"`
			Local  int  `json:"local"`
			Native byte `json:"native"`
			Glyph  byte `json:"glyph_native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_MENU_MODEL"), fmt.Sprintf("point-%03d.texture-underlays.json", at))), &wantUnder))
		if len(wantUnder) != len(p.underlays) {
			t.Fatal("底色來源數量不同", at)
		}
		for k, w := range wantUnder {
			u, ok := p.underlays[hdBuildingCanvas+uint32(k)]
			if !ok || w.ID != 1265 || int(u.cell.local) != w.Local || u.cell.native != w.Native || u.glyph != w.Glyph {
				t.Fatal("底色來源不同", at, k)
			}
		}
		if hash(p.picture) != "5325a3501b83df510cee60c134952130fdb9dfd4bdc00d9eb853fb7ae6021eff" {
			t.Fatal("背景來源不同")
		}
		if receipt["picture"].(map[string]any)["painted"] != 54206 {
			t.Fatal("完整背景沒有命中", at)
		}
		for _, kind := range []string{"palette", "indexed", "border"} {
			changed := f
			changed.palette = append([]byte(nil), f.palette...)
			changed.canvas = append([]byte(nil), f.canvas...)
			changed.indexed = append([]byte(nil), f.indexed...)
			switch kind {
			case "palette":
				changed.palette[0] ^= 1
			case "indexed":
				changed.indexed[0] ^= 1
			case "border":
				changed.canvas[91*320+77] ^= 1
			}
			n := image.NewRGBA(im.Bounds())
			copy(n.Pix, baseline.Pix)
			r := p.paintPicture(n, changed)
			if r["painted"] != 0 || !bytes.Equal(n.Pix, baseline.Pix) {
				t.Fatal("背景錯誤條件未回退", kind, at)
			}
		}
		for k, u := range p.underlays {
			n := image.NewRGBA(im.Bounds())
			pos := int(k - hdBuildingCanvas)
			if !p.paintBackground(n, f, pos, u.cell.native, f.palette) {
				t.Fatal("文字底色未命中", at, pos)
			}
			sx, sy := int(u.cell.local)%32*4, int(u.cell.local)/32*4
			for y := 0; y < 4; y++ {
				for x := 0; x < 4; x++ {
					if n.RGBAAt(pos%320*4+x, pos/320*4+y) != p.art.RGBAAt(sx+x, sy+y) {
						t.Fatal("底色取樣不同")
					}
				}
			}
			before := append([]byte(nil), n.Pix...)
			if p.paintBackground(n, f, pos, u.cell.native^1, f.palette) || !bytes.Equal(before, n.Pix) {
				t.Fatal("不符原版底色仍覆蓋")
			}
			clone := *p
			clone.owners = map[uint32]hdTextureCell{}
			clone.pending = map[uint32]hdTexturePair{}
			clone.underlays = map[uint32]hdTextureUnderlay{k: u}
			hh := *h
			hh.m = golem.New()
			copy(hh.m.Mem, m.Mem)
			clone.h = &hh
			clone.active = false
			clone.memoryWrite(k, u.glyph, u.glyph)
			if len(clone.underlays) != 0 {
				t.Fatal("未知同值寫入未撤銷文字底色")
			}
			break
		}
		pixels := 0
		checkState(s)
		name := filepath.Join(out, fmt.Sprintf("point-%03d", at))
		file, err := os.Create(name + ".png")
		need(err)
		need(png.Encode(file, im))
		need(file.Close())
		file, err = os.Create(name + ".baseline.png")
		need(err)
		need(png.Encode(file, baseline))
		need(file.Close())
		receipt["step"], receipt["point"], receipt["verified_rgba_pixels"] = m.Steps, at, pixels
		records = append(records, receipt)
		at++
	}
	step := func() { capture(); need(m.Step()) }
	for _, e := range replay.Inputs {
		if e.Step > 27885000 {
			break
		}
		for m.Steps < e.Step {
			step()
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < 27885000 {
		step()
	}
	capture()
	checkState(oracle.End)
	if at != 12 || count != 10 || p.accepted != 1 || p.rejected != 0 || p.transferred != model.Transfers["1265"] || p.cursorRestores != model.Cursor["1265"] {
		t.Fatal("原版來源範圍不同", at, count, p.accepted, p.rejected, p.transferred)
	}
	if !bytes.Equal(m.Mem, read(filepath.Join(reference, "control/final.memory"))) {
		t.Fatal("原版終點RAM不同")
	}
	d.Close()
	for _, n := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		_, left := os.Stat(filepath.Join(scratch, n))
		_, right := os.Stat(filepath.Join(reference, "control/saves", n))
		if os.IsNotExist(left) && os.IsNotExist(right) {
			continue
		}
		if !bytes.Equal(read(filepath.Join(scratch, n)), read(filepath.Join(reference, "control/saves", n))) {
			t.Fatal("原版存檔不同", n)
		}
	}
	proof := map[string]any{"result": "PASS_MENU_NATIVE_12_SOURCE_UNDERLAY_AND_REJECTION_POINTS", "production_connected": true, "checkpoints": 12, "dos_inputs": 10, "accepted": p.accepted, "transferred": p.transferred, "rgba_pixels": totalPixels, "large_index_positive_in_this_cohort": seenLarge, "cursor_source_restores": p.cursorRestores, "original_state_and_saves_equal": true, "points": records}
	raw, err = json.MarshalIndent(proof, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDMenuAssetsAndOriginalGuards(t *testing.T) {
	game, art := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS")
	if game == "" || art == "" {
		t.Skip("需要合法原版與候選")
	}
	originals := []string{"VICEROY.EXE", "OPENTILE.SS", "OPENMENU.PIK"}
	assets := []string{"opentile-000.png", "openmenu-000.png"}
	for _, n := range originals {
		if _, err := os.Stat(filepath.Join(game, n)); os.IsNotExist(err) {
			t.Skip("缺合法原版", n)
		}
	}
	for _, kind := range []string{"original", "art"} {
		names, source := originals, game
		if kind == "art" {
			names, source = assets, art
		}
		for _, name := range names {
			for _, bad := range []string{"missing", "wrong", "symlink"} {
				t.Run(kind+"/"+name+"/"+bad, func(t *testing.T) {
					dir := t.TempDir()
					for _, n := range names {
						if n == name && bad == "missing" {
							continue
						}
						path := filepath.Join(dir, n)
						if n == name && bad == "symlink" {
							if err := os.Symlink(filepath.Join(source, n), path); err != nil {
								t.Fatal(err)
							}
							continue
						}
						raw, err := os.ReadFile(filepath.Join(source, n))
						if err != nil {
							t.Fatal(err)
						}
						if n == name {
							raw = append([]byte(nil), raw...)
							raw[0] ^= 1
						}
						if err = os.WriteFile(path, raw, 0644); err != nil {
							t.Fatal(err)
						}
					}
					g, a := game, art
					if kind == "original" {
						g = dir
					} else {
						a = dir
					}
					if _, err := loadHDTextureRuntime(&hdRuntime{m: golem.New()}, g, a); err == nil {
						t.Fatal("錯誤來源被接受")
					}
				})
			}
		}
	}
}

func TestHDWorldWoodNative89(t *testing.T) {
	game, reference, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_WORLD_WOOD_REFERENCE"), os.Getenv("TEST_WORLD_WOOD_OUTPUT")
	if game == "" || reference == "" || out == "" {
		t.Skip("需要合法原版及正常GUI前綴")
	}
	for _, n := range []string{"OPENING.EXE", "VICEROY.EXE", "OPENTILE.SS", "WOODTILE.SS"} {
		if _, err := os.Stat(filepath.Join(game, n)); os.IsNotExist(err) {
			t.Skip("缺合法原版", n)
		}
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(p string) []byte { t.Helper(); b, err := os.ReadFile(p); need(err); return b }
	var replay struct {
		Inputs []windowInput
		End    uint64
	}
	raw := read(os.Getenv("TEST_TEXTURE_INPUTS"))
	if hash(raw) != "8b2b05308d091046379eca38e760f5fbf57fa863625ad53f78b8d3b30dab6b58" {
		t.Fatal("原始輸入不同")
	}
	need(json.Unmarshal(raw, &replay))
	type state struct {
		Steps     uint64
		Count     uint64 `json:"dos_input_count"`
		Memory    string `json:"memory_sha256"`
		Indexed   string `json:"indexed_sha256"`
		Palette   string `json:"palette_sha256"`
		Registers [8]uint16
		Segments  [4]uint16
		IP, Flags uint16
		Cycles    uint64
	}
	var oracle struct {
		Checkpoints []state
		End         state
	}
	need(json.Unmarshal(read(filepath.Join(reference, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 89 || oracle.End.Steps != 280665001 {
		t.Fatal("89點範圍不同")
	}
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "save")
	need(os.Mkdir(scratch, 0755))
	seed := read(os.Getenv("TEST_TEXTURE_SEED"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("原始存檔不同")
	}
	need(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("缺數位音訊")
	}
	m.EnableOPLSynth(true)
	h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))
	need(err)
	p := h.worldTexture
	if p == nil {
		t.Fatal("底紋原型未載入")
	}
	var checkedTransfers, lastTransfers uint64
	extraPages := map[uint32]uint64{}
	m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, old, value byte) {
		delta := p.transferred - lastTransfers
		lastTransfers = p.transferred
		if delta > 1 {
			t.Fatal("單次來源複製計數異常", delta)
		}
		if delta == 0 {
			return
		}
		observed := (a >= 0x2cae0 && a < 0x2cae0+64000) || (a >= 0x3c500 && a < 0x3c500+64000)
		for _, base := range []uint32{404160, 404960, 181952} {
			observed = observed || (a >= base && a < base+768)
		}
		if observed {
			checkedTransfers += delta
		} else {
			extraPages[a>>8] += delta
		}
	})
	m.SetBeforeInstruction(h.beforeInstruction)
	checkState := func(s state) {
		t.Helper()
		c := m.CPU
		if hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("原版完整狀態不同", m.Steps)
		}
	}
	at, count := 0, uint64(0)
	var records []map[string]any
	totalPixels := 0
	seenLarge := false
	var model struct {
		Transfers map[string]uint64 `json:"texture_transfer_writes"`
		Cursor    map[string]uint64 `json:"texture_cursor_pairs"`
	}
	need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_WORLD_WOOD_MODEL"), "check.json")), &model))
	capture := func() {
		if at == 89 {
			return
		}
		s := oracle.Checkpoints[at]
		if m.Steps > s.Steps || (m.Steps == s.Steps && count > s.Count) {
			t.Fatal("略過原版點", at)
		}
		if m.Steps != s.Steps || count != s.Count {
			return
		}
		checkState(s)
		var want map[int]struct {
			ID     int  `json:"source_id"`
			Local  int  `json:"local"`
			Native byte `json:"native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_WORLD_WOOD_MODEL"), fmt.Sprintf("point-%03d.texture-owners.json", at))), &want))
		for k, w := range want {
			if w.ID != 1552 {
				delete(want, k)
			}
		}
		owned := map[int]hdTextureCell{}
		for a, c := range p.owners {
			if a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
				owned[int(a-hdBuildingCanvas)] = c
			}
		}
		if len(owned) != len(want) {
			t.Fatal("來源格數不同", len(owned), len(want))
		}
		largeLocal := false
		for k, w := range want {
			c, ok := owned[k]
			if !ok || w.ID != 1552 || int(c.local) != w.Local || c.native != w.Native {
				t.Fatal("獨立來源模型不同", at, k, c, w)
			}
			largeLocal = largeLocal || w.Local > 255
		}
		seenLarge = seenLarge || largeLocal
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		h.worldTexture = nil
		baseline, _ := h.base(f)
		h.worldTexture = p
		im, receipt := h.base(f)
		h.restoreCursor(im, f)
		h.cursor.paint(h, im, f)
		h.restoreCursor(baseline, f)
		h.cursor.paint(h, baseline, f)
		pixels := 0
		supported := p.paletteSupported(f.palette) && receipt["reason"] != "unverified-cursor-or-native-surface"
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if image.Pt(x/4, y/4).In(f.cursor) {
					continue
				}
				k := (y/4)*320 + x/4
				c, ok := owned[k]
				if !ok || !supported {
					if im.RGBAAt(x, y) != baseline.RGBAAt(x, y) {
						t.Fatal("來源外像素被改", at, x, y)
					}
					continue
				}
				sx, sy := int(c.local)%32*4+x%4, int(c.local)/32*4+y%4
				if im.RGBAAt(x, y) != p.art.RGBAAt(sx, sy) {
					t.Fatal("底紋RGBA不同", at, x, y)
				}
				pixels++
			}
		}
		expectedPixels := 0
		for k := range owned {
			if !image.Pt(k%320, k/320).In(f.cursor) {
				expectedPixels += 16
			}
		}
		if supported && pixels != expectedPixels {
			t.Fatal("像素數不同", pixels)
		}
		totalPixels += pixels
		checkState(s)
		// 未證實色盤維持原版，原本合成畫布不能被改。
		unsupported := f
		unsupported.palette = append([]byte(nil), f.palette...)
		unsupported.palette[128*3] ^= 1
		n := image.NewRGBA(im.Bounds())
		copy(n.Pix, baseline.Pix)
		record := p.paint(n, unsupported)
		if record["painted"].(int) != 0 || !bytes.Equal(n.Pix, baseline.Pix) {
			t.Fatal("未證實色盤沒有回退")
		}
		// 任何未知同值寫入撤銷已驗來源。
		clone := *p
		clone.owners = map[uint32]hdTextureCell{}
		for a, c := range p.owners {
			clone.owners[a] = c
		}
		hh := *h
		hh.m = golem.New()
		copy(hh.m.Mem, m.Mem)
		clone.h = &hh
		clone.active = false
		clone.pending = map[uint32]hdTexturePair{}
		clone.underlays = map[uint32]hdTextureUnderlay{}
		for k, c := range owned {
			a := hdBuildingCanvas + uint32(k)
			clone.memoryWrite(a, c.native, c.native)
			if _, ok := clone.owners[a]; ok {
				t.Fatal("同值未知寫入未撤銷")
			}
			break
		}
		var wantUnder map[int]struct {
			ID     int  `json:"source_id"`
			Local  int  `json:"local"`
			Native byte `json:"native"`
			Glyph  byte `json:"glyph_native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_WORLD_WOOD_MODEL"), fmt.Sprintf("point-%03d.texture-underlays.json", at))), &wantUnder))
		for k, w := range wantUnder {
			if w.ID != 1552 {
				delete(wantUnder, k)
			}
		}
		if len(wantUnder) != len(p.underlays) {
			t.Fatal("獨立木紋文字底色數量不同", at, len(wantUnder), len(p.underlays))
		}
		for k, w := range wantUnder {
			u, ok := p.underlays[hdBuildingCanvas+uint32(k)]
			if !ok || int(u.cell.local) != w.Local || u.cell.native != w.Native || u.glyph != w.Glyph {
				t.Fatal("獨立木紋底色不同", at, k)
			}
		}
		if at%14 == 0 || at == 88 {
			name := filepath.Join(out, fmt.Sprintf("point-%03d", at))
			file, err := os.Create(name + ".png")
			need(err)
			need(png.Encode(file, im))
			need(file.Close())
			file, err = os.Create(name + ".baseline.png")
			need(err)
			need(png.Encode(file, baseline))
			need(file.Close())
		}
		receipt["step"], receipt["point"], receipt["verified_rgba_pixels"] = m.Steps, at, pixels
		records = append(records, receipt)
		at++
	}
	step := func() { capture(); need(m.Step()) }
	for _, e := range replay.Inputs {
		if e.Step > 280665001 {
			break
		}
		for m.Steps < e.Step {
			step()
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < 280665001 {
		step()
	}
	capture()
	checkState(oracle.End)
	diagnostic, diagnosticErr := json.MarshalIndent(map[string]any{"points": at, "inputs": count, "accepted": p.accepted, "rejected": p.rejected, "transferred": p.transferred, "checked_transfers": checkedTransfers, "expected_transfers": model.Transfers["1552"], "cursor_restores": p.cursorRestores, "expected_cursor_restores": model.Cursor["1552"], "extra_pages": extraPages}, "", "  ")
	need(diagnosticErr)
	need(os.WriteFile(filepath.Join(out, "diagnostic-final.json"), diagnostic, 0644))
	if at != 89 || count != 165 || p.accepted != 1 || p.rejected != 0 || p.transferred != model.Transfers["1552"] || p.cursorRestores != model.Cursor["1552"] {
		t.Fatal("原版來源範圍不同", at, count, p.accepted, p.rejected, p.transferred)
	}
	if !bytes.Equal(m.Mem, read(filepath.Join(reference, "control/final.memory"))) {
		t.Fatal("原版終點RAM不同")
	}
	d.Close()
	for _, n := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		if !bytes.Equal(read(filepath.Join(scratch, n)), read(filepath.Join(reference, "control/saves", n))) {
			t.Fatal("原版存檔不同", n)
		}
	}
	proof := map[string]any{"result": "PASS_WORLD_WOOD_NATIVE_89_SOURCE_RGBA_AND_UNDERLAY_POINTS", "production_connected": true, "checkpoints": 89, "dos_inputs": 165, "accepted": p.accepted, "transferred": p.transferred, "transferred_in_original_trace_regions": checkedTransfers, "transfers_outside_original_trace_regions_by_page": extraPages, "rgba_pixels": totalPixels, "large_index_positive_in_this_cohort": seenLarge, "cursor_source_restores": p.cursorRestores, "original_state_and_saves_equal": true, "points": records}
	raw, err = json.MarshalIndent(proof, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDWorldWoodAssetsAndPalette(t *testing.T) {
	game, assets, reference := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_WORLD_WOOD_REFERENCE")
	if game == "" || assets == "" || reference == "" {
		t.Skip("需要合法原版、生成圖及89點原版收據")
	}
	read := func(path string) []byte {
		t.Helper()
		b, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	wood := read(filepath.Join(game, "WOODTILE.SS"))
	art := read(filepath.Join(assets, "woodtile-000.png"))
	for _, kind := range []string{"missing", "bad", "linked"} {
		for _, source := range []bool{false, true} {
			name := "art/" + kind
			if source {
				name = "original/" + kind
			}
			t.Run(name, func(t *testing.T) {
				dir := t.TempDir()
				for n, b := range map[string][]byte{"WOODTILE.SS": wood, "woodtile-000.png": art} {
					if err := os.WriteFile(filepath.Join(dir, n), b, 0644); err != nil {
						t.Fatal(err)
					}
				}
				file, original := "woodtile-000.png", filepath.Join(assets, "woodtile-000.png")
				if source {
					file, original = "WOODTILE.SS", filepath.Join(game, "WOODTILE.SS")
				}
				path := filepath.Join(dir, file)
				if err := os.Remove(path); err != nil {
					t.Fatal(err)
				}
				if kind == "bad" {
					if err := os.WriteFile(path, []byte("wrong"), 0644); err != nil {
						t.Fatal(err)
					}
				}
				if kind == "linked" {
					if err := os.Symlink(original, path); err != nil {
						t.Fatal(err)
					}
				}
				if _, err := loadHDTextureVariant(&hdRuntime{m: golem.New()}, dir, dir, true); err == nil {
					t.Fatal("未拒絕錯誤來源", name)
				}
			})
		}
	}
	p, err := loadHDTextureVariant(&hdRuntime{m: golem.New()}, game, assets, true)
	if err != nil {
		t.Fatal(err)
	}
	palette := read(filepath.Join(reference, "control/point-000.palette"))
	if !p.paletteSupported(palette) {
		t.Fatal("已驗色盤未通過")
	}
	for i := 0; i < 256; i++ {
		changed := append([]byte(nil), palette...)
		changed[i*3] ^= 1
		if p.paletteSupported(changed) != (i < 128 || i > 138) {
			t.Fatal("色盤區段守門不同", i)
		}
	}
	if p.paletteSupported(nil) || p.paletteSupported(palette[:767]) {
		t.Fatal("短色盤未拒絕")
	}
	if p.pictureArt != nil || p.picture != nil {
		t.Fatal("WOOD不應載入主選單來源快取")
	}
}

func TestHDParchNative62(t *testing.T) {
	game, reference, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_PARCH_REFERENCE"), os.Getenv("TEST_PARCH_OUTPUT")
	if game == "" || reference == "" || out == "" {
		t.Skip("需要合法原版及正常GUI前綴")
	}
	for _, n := range []string{"OPENING.EXE", "VICEROY.EXE", "OPENTILE.SS", "WOODTILE.SS"} {
		if _, err := os.Stat(filepath.Join(game, n)); os.IsNotExist(err) {
			t.Skip("缺合法原版", n)
		}
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(p string) []byte { t.Helper(); b, err := os.ReadFile(p); need(err); return b }
	var replay struct {
		Inputs []windowInput
		End    uint64
	}
	raw := read(os.Getenv("TEST_TEXTURE_INPUTS"))
	if hash(raw) != "385b8679a43fbf27cdbdcd7c3b3b41030c684c70f0149816f4347f7030173cd6" {
		t.Fatal("原始輸入不同")
	}
	need(json.Unmarshal(raw, &replay))
	type state struct {
		Steps     uint64
		Count     uint64 `json:"dos_input_count"`
		Memory    string `json:"memory_sha256"`
		Indexed   string `json:"indexed_sha256"`
		Palette   string `json:"palette_sha256"`
		Registers [8]uint16
		Segments  [4]uint16
		IP, Flags uint16
		Cycles    uint64
	}
	var oracle struct {
		Checkpoints []state
		End         state
	}
	need(json.Unmarshal(read(filepath.Join(reference, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 62 || oracle.End.Steps != 136400000 {
		t.Fatal("89點範圍不同")
	}
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "save")
	need(os.Mkdir(scratch, 0755))
	seed := read(os.Getenv("TEST_TEXTURE_SEED"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("原始存檔不同")
	}
	need(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("缺數位音訊")
	}
	m.EnableOPLSynth(true)
	h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))
	need(err)
	p := h.parch
	if p == nil {
		t.Fatal("底紋原型未載入")
	}
	var checkedTransfers, lastTransfers uint64
	extraPages := map[uint32]uint64{}
	m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, old, value byte) {
		delta := p.transferred - lastTransfers
		lastTransfers = p.transferred
		if delta > 1 {
			t.Fatal("單次來源複製計數異常", delta)
		}
		if delta == 0 {
			return
		}
		observed := (a >= 0x2cae0 && a < 0x2cae0+64000) || (a >= 0x3c500 && a < 0x3c500+64000)
		for _, base := range []uint32{404160, 404960, 181952} {
			observed = observed || (a >= base && a < base+768)
		}
		if observed {
			checkedTransfers += delta
		} else {
			extraPages[a>>8] += delta
		}
	})
	m.SetBeforeInstruction(h.beforeInstruction)
	checkState := func(s state) {
		t.Helper()
		c := m.CPU
		if hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("原版完整狀態不同", m.Steps)
		}
	}
	at, count := 0, uint64(0)
	var records []map[string]any
	totalPixels := 0
	seenLarge := false
	var model struct {
		Transfers map[string]uint64 `json:"texture_transfer_writes"`
		Cursor    map[string]uint64 `json:"texture_cursor_pairs"`
	}
	need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_PARCH_MODEL"), "check.json")), &model))
	capture := func() {
		if at == 62 {
			return
		}
		s := oracle.Checkpoints[at]
		if m.Steps > s.Steps || (m.Steps == s.Steps && count > s.Count) {
			t.Fatal("略過原版點", at)
		}
		if m.Steps != s.Steps || count != s.Count {
			return
		}
		checkState(s)
		var want map[int]struct {
			ID     int  `json:"source_id"`
			Local  int  `json:"local"`
			Native byte `json:"native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_PARCH_MODEL"), fmt.Sprintf("point-%03d.texture-owners.json", at))), &want))
		for k, w := range want {
			if w.ID != 1287 {
				delete(want, k)
			}
		}
		owned := map[int]hdTextureCell{}
		for a, c := range p.owners {
			if a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
				owned[int(a-hdBuildingCanvas)] = c
			}
		}
		if len(owned) != len(want) {
			t.Fatal("來源格數不同", len(owned), len(want))
		}
		largeLocal := false
		for k, w := range want {
			c, ok := owned[k]
			if !ok || w.ID != 1287 || int(c.local) != w.Local || c.native != w.Native {
				t.Fatal("獨立來源模型不同", at, k, c, w)
			}
			largeLocal = largeLocal || w.Local > 255
		}
		seenLarge = seenLarge || largeLocal
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		h.parch = nil
		baseline, _ := h.base(f)
		h.parch = p
		im, receipt := h.base(f)
		h.restoreCursor(im, f)
		h.cursor.paint(h, im, f)
		h.restoreCursor(baseline, f)
		h.cursor.paint(h, baseline, f)
		pixels := 0
		supported := p.paletteSupported(f.palette) && receipt["reason"] != "unverified-cursor-or-native-surface"
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if image.Pt(x/4, y/4).In(f.cursor) {
					continue
				}
				k := (y/4)*320 + x/4
				c, ok := owned[k]
				if !ok || !supported {
					if im.RGBAAt(x, y) != baseline.RGBAAt(x, y) {
						t.Fatal("來源外像素被改", at, x, y)
					}
					continue
				}
				sx, sy := int(c.local)%32*4+x%4, int(c.local)/32*4+y%4
				if im.RGBAAt(x, y) != p.art.RGBAAt(sx, sy) {
					t.Fatal("底紋RGBA不同", at, x, y)
				}
				pixels++
			}
		}
		expectedPixels := 0
		for k := range owned {
			if !image.Pt(k%320, k/320).In(f.cursor) {
				expectedPixels += 16
			}
		}
		if supported && pixels != expectedPixels {
			t.Fatal("像素數不同", pixels)
		}
		totalPixels += pixels
		checkState(s)
		// 未證實色盤維持原版，原本合成畫布不能被改。
		unsupported := f
		unsupported.palette = append([]byte(nil), f.palette...)
		unsupported.palette[98*3] ^= 1
		n := image.NewRGBA(im.Bounds())
		copy(n.Pix, baseline.Pix)
		record := p.paint(n, unsupported)
		if record["painted"].(int) != 0 || !bytes.Equal(n.Pix, baseline.Pix) {
			t.Fatal("未證實色盤沒有回退")
		}
		// 任何未知同值寫入撤銷已驗來源。
		clone := *p
		clone.owners = map[uint32]hdTextureCell{}
		for a, c := range p.owners {
			clone.owners[a] = c
		}
		hh := *h
		hh.m = golem.New()
		copy(hh.m.Mem, m.Mem)
		clone.h = &hh
		clone.active = false
		clone.pending = map[uint32]hdTexturePair{}
		clone.underlays = map[uint32]hdTextureUnderlay{}
		for k, c := range owned {
			a := hdBuildingCanvas + uint32(k)
			clone.memoryWrite(a, c.native, c.native)
			if _, ok := clone.owners[a]; ok {
				t.Fatal("同值未知寫入未撤銷")
			}
			break
		}
		var wantUnder map[int]struct {
			ID     int  `json:"source_id"`
			Local  int  `json:"local"`
			Native byte `json:"native"`
			Glyph  byte `json:"glyph_native"`
		}
		need(json.Unmarshal(read(filepath.Join(os.Getenv("TEST_PARCH_MODEL"), fmt.Sprintf("point-%03d.texture-underlays.json", at))), &wantUnder))
		for k, w := range wantUnder {
			if w.ID != 1287 {
				delete(wantUnder, k)
			}
		}
		if len(wantUnder) != len(p.underlays) {
			t.Fatal("獨立木紋文字底色數量不同", at, len(wantUnder), len(p.underlays))
		}
		for k, w := range wantUnder {
			u, ok := p.underlays[hdBuildingCanvas+uint32(k)]
			if !ok || int(u.cell.local) != w.Local || u.cell.native != w.Native || u.glyph != w.Glyph {
				t.Fatal("獨立木紋底色不同", at, k)
			}
		}
		if at%14 == 0 || at == 61 || len(owned) > 0 {
			name := filepath.Join(out, fmt.Sprintf("point-%03d", at))
			file, err := os.Create(name + ".png")
			need(err)
			need(png.Encode(file, im))
			need(file.Close())
			file, err = os.Create(name + ".baseline.png")
			need(err)
			need(png.Encode(file, baseline))
			need(file.Close())
		}
		receipt["step"], receipt["point"], receipt["verified_rgba_pixels"] = m.Steps, at, pixels
		records = append(records, receipt)
		at++
	}
	step := func() { capture(); need(m.Step()) }
	for _, e := range replay.Inputs {
		if e.Step > 136400000 {
			break
		}
		for m.Steps < e.Step {
			step()
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < 136400000 {
		step()
	}
	capture()
	checkState(oracle.End)
	diagnostic, diagnosticErr := json.MarshalIndent(map[string]any{"points": at, "inputs": count, "accepted": p.accepted, "rejected": p.rejected, "transferred": p.transferred, "checked_transfers": checkedTransfers, "expected_transfers": model.Transfers["1287"], "cursor_restores": p.cursorRestores, "expected_cursor_restores": model.Cursor["1287"], "extra_pages": extraPages}, "", "  ")
	need(diagnosticErr)
	need(os.WriteFile(filepath.Join(out, "diagnostic-final.json"), diagnostic, 0644))
	if at != 62 || count != 56 || p.accepted != 1 || p.rejected != 0 || p.transferred != model.Transfers["1287"] || p.cursorRestores != model.Cursor["1287"] {
		t.Fatal("原版來源範圍不同", at, count, p.accepted, p.rejected, p.transferred)
	}
	if !bytes.Equal(m.Mem, read(filepath.Join(reference, "control/final.memory"))) {
		t.Fatal("原版終點RAM不同")
	}
	d.Close()
	for _, n := range []string{"COLONY09.SAV", "COLONY00.SAV"} {
		if !bytes.Equal(read(filepath.Join(scratch, n)), read(filepath.Join(reference, "control/saves", n))) {
			t.Fatal("原版存檔不同", n)
		}
	}
	proof := map[string]any{"result": "PASS_PARCH_NATIVE_62_SOURCE_RGBA_AND_UNDERLAY_POINTS", "production_connected": true, "checkpoints": 62, "dos_inputs": 56, "accepted": p.accepted, "transferred": p.transferred, "transferred_in_original_trace_regions": checkedTransfers, "transfers_outside_original_trace_regions_by_page": extraPages, "rgba_pixels": totalPixels, "large_index_positive_in_this_cohort": seenLarge, "cursor_source_restores": p.cursorRestores, "original_state_and_saves_equal": true, "points": records}
	raw, err = json.MarshalIndent(proof, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDParchAssetsAndPalette(t *testing.T) {
	game, assets, reference := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_PARCH_REFERENCE")
	if game == "" || assets == "" || reference == "" {
		t.Skip("需要合法原版、生成圖及89點原版收據")
	}
	read := func(path string) []byte {
		t.Helper()
		b, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return b
	}
	wood := read(filepath.Join(game, "PARCH.SS"))
	art := read(filepath.Join(assets, "parch-000.png"))
	for _, kind := range []string{"missing", "bad", "linked"} {
		for _, source := range []bool{false, true} {
			name := "art/" + kind
			if source {
				name = "original/" + kind
			}
			t.Run(name, func(t *testing.T) {
				dir := t.TempDir()
				for n, b := range map[string][]byte{"PARCH.SS": wood, "parch-000.png": art} {
					if err := os.WriteFile(filepath.Join(dir, n), b, 0644); err != nil {
						t.Fatal(err)
					}
				}
				file, original := "parch-000.png", filepath.Join(assets, "parch-000.png")
				if source {
					file, original = "PARCH.SS", filepath.Join(game, "PARCH.SS")
				}
				path := filepath.Join(dir, file)
				if err := os.Remove(path); err != nil {
					t.Fatal(err)
				}
				if kind == "bad" {
					if err := os.WriteFile(path, []byte("wrong"), 0644); err != nil {
						t.Fatal(err)
					}
				}
				if kind == "linked" {
					if err := os.Symlink(original, path); err != nil {
						t.Fatal(err)
					}
				}
				if _, err := loadHDTextureKind(&hdRuntime{m: golem.New()}, dir, dir, "parch"); err == nil {
					t.Fatal("未拒絕錯誤來源", name)
				}
			})
		}
	}
	p, err := loadHDTextureKind(&hdRuntime{m: golem.New()}, game, assets, "parch")
	if err != nil {
		t.Fatal(err)
	}
	palette := read(filepath.Join(reference, "control/point-023.palette"))
	if !p.paletteSupported(palette) {
		t.Fatal("已驗色盤未通過")
	}
	for i := 0; i < 256; i++ {
		changed := append([]byte(nil), palette...)
		changed[i*3] ^= 1
		if p.paletteSupported(changed) != (i != 98 && i != 99 && i != 100 && i != 106 && i != 107) {
			t.Fatal("色盤區段守門不同", i)
		}
	}
	if p.paletteSupported(nil) || p.paletteSupported(palette[:767]) {
		t.Fatal("短色盤未拒絕")
	}
	if p.pictureArt != nil || p.picture != nil {
		t.Fatal("WOOD不應載入主選單來源快取")
	}
}

func TestHDPublishedTextureNative32(t *testing.T) {
	game, _, assets := hdReportFixtures(t)
	root, model, out := os.Getenv("TEST_HD_TEXTURE_PUBLISHED_REFERENCE"), os.Getenv("TEST_HD_TEXTURE_PUBLISHED_MODEL"), os.Getenv("TEST_HD_TEXTURE_PUBLISHED_OUTPUT")
	if root == "" || model == "" || out == "" {
		t.Skip("需要已發布底紋的32點原版來源")
	}
	var oracle struct {
		Checkpoints []hdNewGameOracleState
		End         hdNewGameOracleState
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 32 || oracle.End.Steps != 80600000 {
		t.Fatal("原版來源範圍不同")
	}
	var replay struct{ Inputs []windowInput }
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, os.Getenv("TEST_HD_TEXTURE_PUBLISHED_INPUTS")), &replay))
	hdNewGameNeed(t, os.Mkdir(out, 0755))
	save := filepath.Join(out, "save")
	hdNewGameNeed(t, os.Mkdir(save, 0755))
	seed := hdNewGameRead(t, filepath.Join(root, "control/saves/COLONY09.SAV"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("原版種子不同")
	}
	hdNewGameNeed(t, os.WriteFile(filepath.Join(save, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	hdNewGameNeed(t, m.LoadEXE(hdNewGameRead(t, filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = save
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("缺數位音訊")
	}
	m.EnableOPLSynth(true)
	h := &hdRuntime{m: m}
	ps := map[int]*hdTextureRuntime{}
	for rid, kind := range map[int]string{1265: "menu", 1287: "parch", 1552: "wood"} {
		p, e := loadHDTextureKind(h, game, assets, kind)
		hdNewGameNeed(t, e)
		ps[rid] = p
	}
	h.texture, h.parch, h.worldTexture = ps[1265], ps[1287], ps[1552]
	m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, o, v byte) {
		for _, p := range ps {
			p.memoryWrite(a, o, v)
		}
	})
	m.SetBeforeInstruction(h.beforeInstruction)
	checkState := func(s hdNewGameOracleState) {
		t.Helper()
		c := m.CPU
		if m.Steps != s.Steps || hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("底紋觀測改變原版完整狀態", m.Steps)
		}
	}
	at, count, total := 0, uint64(0), 0
	records := []map[string]any{}
	capture := func() {
		if at == len(oracle.Checkpoints) {
			return
		}
		s := oracle.Checkpoints[at]
		if m.Steps > s.Steps || m.Steps == s.Steps && count > s.Count {
			t.Fatal("略過原版點", at)
		}
		if m.Steps != s.Steps || count != s.Count {
			return
		}
		checkState(s)
		var main, published map[int][]any
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d.owners.json", at))), &main))
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d.published.json", at))), &published))
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		im := draftRGB(f.indexed, f.palette)
		before := draftRGB(f.indexed, f.palette)
		counts := map[int]int{}
		masks := map[int][]byte{}
		for rid, p := range ps {
			for pos := 0; pos < 64000; pos++ {
				for _, pair := range []struct {
					got  hdSceneCell
					want []any
				}{{p.mainCell(pos), main[pos]}, {p.published[pos], published[pos]}} {
					want := pair.want
					has := len(want) > 0 && int(want[0].(float64)) == rid
					if !has {
						if pair.got.slot != 0 {
							t.Fatal("未知點仍持有底紋", at, rid, pos)
						}
						continue
					}
					if !p.validPublishedCell(pair.got) || int(pair.got.local) != int(want[1].(float64)) || int(pair.got.value) != int(want[2].(float64)) || pair.got.glyph != (want[3].(string) == "glyph") {
						t.Fatal("底紋來源與獨立模型不同", at, rid, pos, pair.got, want)
					}
				}
			}
			expected := hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d-published-%d-mask.bin", at, rid)))
			if len(expected) != 64000 {
				t.Fatal("遮罩長度")
			}
			masks[rid] = expected
			packed := make([]byte, 8000)
			n := 0
			for pos, v := range expected {
				if v != 0 {
					packed[pos>>3] |= 1 << uint(pos&7)
					n++
				}
			}
			got := p.paintPublished(im, f)
			if got["reason"] != "published-texture-background-only" || got["painted"].(int) != n || !bytes.Equal(got["mask"].([]byte), packed) {
				t.Fatal("底紋來源遮罩不同", at, rid, got["reason"], got["painted"], n)
			}
			counts[rid] = n
		}
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				pos := y/4*320 + x/4
				want := before.RGBAAt(x, y)
				found := 0
				for rid, p := range ps {
					if masks[rid][pos] != 0 {
						found++
						c := p.published[pos]
						want = p.art.RGBAAt(int(c.local)%32*4+x%4, int(c.local)/32*4+y%4)
						total++
					}
				}
				if found > 1 || im.RGBAAt(x, y) != want {
					t.Fatal("發布底紋RGBA或原版前景不同", at, x, y)
				}
			}
		}
		checkState(s)
		file, e := os.Create(filepath.Join(out, fmt.Sprintf("point-%03d.png", at)))
		hdNewGameNeed(t, e)
		hdNewGameNeed(t, png.Encode(file, im))
		hdNewGameNeed(t, file.Close())
		records = append(records, map[string]any{"point": at, "step": m.Steps, "painted": counts, "native_memory_sha256": hash(m.Mem)})
		at++
	}
	step := func() { capture(); hdNewGameNeed(t, m.Step()) }
	for _, e := range replay.Inputs {
		if e.Step > oracle.End.Steps {
			break
		}
		for m.Steps < e.Step {
			step()
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < oracle.End.Steps {
		step()
	}
	capture()
	checkState(oracle.End)
	if at != 32 || count != 31 || total == 0 {
		t.Fatal("原版範圍不同", at, count, total)
	}
	if !bytes.Equal(m.Mem, hdNewGameRead(t, filepath.Join(root, "control/final.memory"))) {
		t.Fatal("完整終點RAM不同")
	}
	for rid, p := range ps {
		if p.accepted != 1 || p.rejected != 0 || len(p.publishedPending) != 0 || p.publicationBlocked {
			t.Fatal("解碼或游標生命週期不同", rid, p.accepted, p.rejected)
		}
	}
	d.Close()
	if !bytes.Equal(seed, hdNewGameRead(t, filepath.Join(save, "COLONY09.SAV"))) {
		t.Fatal("原版存檔改變")
	}
	proof := map[string]any{"result": "PASS_PUBLISHED_TEXTURE_NATIVE32_SOURCE_RGBA_AND_STATE", "checkpoints": at, "dos_inputs": count, "source_rgba_pixels": total, "full_rgba_pixels": 32 * 1280 * 800, "points": records, "original_state_and_saves_equal": true, "production_connected": true}
	raw, e := json.MarshalIndent(proof, "", "  ")
	hdNewGameNeed(t, e)
	hdNewGameNeed(t, os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDTexturePublishedWriteGuards(t *testing.T) {
	game, _, assets := hdReportFixtures(t)
	for _, name := range []string{"known", "normalized-source", "wrong-code", "wrong-source", "source-value", "same-value-revoke", "post-publication-main-write"} {
		t.Run(name, func(t *testing.T) {
			m := golem.New()
			h := &hdRuntime{m: m}
			p, err := loadHDTextureKind(h, game, assets, "wood")
			hdNewGameNeed(t, err)
			h.worldTexture = p
			raw := hdNewGameRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/1552.idx")
			copy(p.native[:], raw)
			p.accepted = 1
			m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, o, v byte) { p.memoryWrite(a, o, v) })
			pos := 40000
			p.owners[hdBuildingCanvas+uint32(pos)] = hdTextureCell{local: 0, native: raw[0]}
			m.Mem[hdBuildingCanvas+uint32(pos)] = raw[0]
			m.CPU.Seg[golem.CS] = 0xe21
			m.CPU.IP = 0x91
			m.CPU.Seg[golem.DS] = 0x2cae
			m.CPU.R[golem.SI] = uint16(pos)
			if name == "normalized-source" {
				m.CPU.Seg[golem.DS] = 0x34ae
				m.CPU.R[golem.SI] = uint16(pos - 32768)
			}
			if name == "wrong-source" {
				m.CPU.Seg[golem.DS]++
			}
			m.CPU.Seg[golem.ES] = 0xa000
			m.CPU.R[golem.DI] = uint16(pos)
			m.CPU.R[golem.CX] = 1
			m.CPU.Flags &^= 0x400
			copy(m.Mem[0xe210+0x91:], hdSceneVGACopyCode)
			if name == "wrong-code" {
				m.Mem[0xe210+0x91+15] ^= 1
			}
			if name == "source-value" {
				m.Mem[hdBuildingCanvas+uint32(pos)] ^= 1
			}
			hdNewGameNeed(t, m.Step())
			rejected := name == "wrong-code" || name == "wrong-source" || name == "source-value"
			if (p.published[pos].slot == 0) != rejected {
				t.Fatal("VGA來源守門不同", name, p.published[pos])
			}
			if name == "same-value-revoke" || name == "post-publication-main-write" {
				before := p.published[pos]
				m.CPU.Seg[golem.CS] = 0x1000
				m.CPU.IP = 0
				m.Mem[0x10000] = 0xaa
				m.CPU.Seg[golem.ES] = 0xa000
				if name == "post-publication-main-write" {
					m.CPU.Seg[golem.ES] = 0x2cae
				}
				m.CPU.R[golem.DI] = uint16(pos)
				m.CPU.R[golem.AX] = uint16(raw[0])
				hdNewGameNeed(t, m.Step())
				if name == "same-value-revoke" && p.published[pos].slot != 0 {
					t.Fatal("未知VGA同值寫入未撤銷")
				}
				if name == "post-publication-main-write" && (p.published[pos] != before || p.mainCell(pos).slot != 0) {
					t.Fatal("主畫布後寫污染已發布來源")
				}
			}
		})
	}
}

func TestHDTexturePublishedCursorVGAOperations(t *testing.T) {
	game, _, assets := hdReportFixtures(t)
	root := os.Getenv("TEST_HD_CURSOR_ROOT")
	if root == "" {
		t.Skip("需要游標32點原版資料")
	}
	m := golem.New()
	h := &hdRuntime{m: m}
	p, err := loadHDTextureKind(h, game, assets, "wood")
	hdNewGameNeed(t, err)
	raw := hdNewGameRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/1552.idx")
	copy(p.native[:], raw)
	p.accepted = 1
	m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, o, v byte) { p.memoryWrite(a, o, v) })
	memory := hdNewGameRead(t, filepath.Join(root, "published-cursor-source-probe-r1/control/point-004.memory"))
	pos := 40000
	slot := uint8(1)
	names := []string{"transparent", "opaque-save", "opaque-restore", "post-main-write", "unknown-vga-same", "wrong-code", "wrong-source", "wrong-ds", "wrong-source-offset", "wrong-composition", "wrong-background", "wrong-restore-k", "wrong-restore-old", "wrong-restore-background", "wrong-restore-composition", "pending-bound"}
	for _, name := range names {
		t.Run(name, func(t *testing.T) {
			copy(m.Mem, memory)
			clear(p.published[:])
			clear(p.owners)
			clear(p.underlays)
			clear(p.publishedPending)
			p.publicationBlocked = false
			cell := hdSceneCell{slot: slot, local: 0, value: raw[0]}
			p.published[pos] = cell
			p.owners[hdBuildingCanvas+uint32(pos)] = hdTextureCell{local: 0, native: raw[0]}
			m.Mem[hdBuildingCanvas+uint32(pos)] = raw[0]
			m.Mem[0xa0000+pos] = raw[0]
			source, known := h.cursorSource()
			if !known {
				t.Fatal("原版游標來源不同")
			}
			k := -1
			for i, v := range source {
				if name == "transparent" && v == 255 || name != "transparent" && v != 255 && v != raw[0] {
					k = i
					break
				}
			}
			if k < 0 {
				t.Fatal("缺游標來源格")
			}
			paint := source[k]
			if paint == 255 {
				paint = raw[0]
			}
			m.Mem[0xafa00+k] = raw[0]
			m.Mem[0xafb00+k] = paint
			code := []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}
			copy(m.Mem[0xb680+0x51c:], code)
			m.CPU.Seg[golem.CS] = 0xb68
			m.CPU.IP = 0x51c
			m.CPU.Seg[golem.DS] = 0xa000
			m.CPU.Seg[golem.ES] = 0xa000
			m.CPU.R[golem.SI] = uint16(0xfb00 + k)
			m.CPU.R[golem.DI] = uint16(pos)
			m.CPU.R[golem.CX] = 1
			m.CPU.Flags &^= 0x400
			switch name {
			case "wrong-code":
				m.Mem[0xb680+0x51c+15] ^= 1
			case "wrong-source":
				m.Mem[0x1ce73] ^= 1
			case "wrong-ds":
				m.CPU.Seg[golem.DS]++
			case "wrong-source-offset":
				m.CPU.R[golem.SI] = 0xfc00
			case "wrong-composition":
				m.Mem[0xafb00+k] ^= 1
			case "wrong-background":
				m.Mem[0xafa00+k] ^= 1
			case "pending-bound":
				for i := 0; i < 257; i++ {
					p.publishedPending[i] = hdSceneCursorPair{}
				}
			}
			hdNewGameNeed(t, m.Step())
			rejected := name == "wrong-code" || name == "wrong-source" || name == "wrong-ds" || name == "wrong-source-offset" || name == "wrong-composition" || name == "wrong-background" || name == "pending-bound"
			if name == "transparent" {
				if p.published[pos] != cell || len(p.publishedPending) != 0 {
					t.Fatal("透明游標未保留發布來源")
				}
				return
			}
			if p.published[pos].slot != 0 {
				t.Fatal("不透明或未知寫入仍持有來源", name)
			}
			if rejected {
				if len(p.publishedPending) != 0 {
					t.Fatal("未知寫入仍保存配對", name)
				}
				if name == "pending-bound" && !p.publicationBlocked {
					t.Fatal("超限未關閉")
				}
				return
			}
			if _, yes := p.publishedPending[pos]; !yes {
				t.Fatal("不透明游標未保存來源")
			}
			if name == "opaque-save" {
				return
			}
			if name == "post-main-write" || name == "unknown-vga-same" {
				m.CPU.Seg[golem.CS] = 0x1000
				m.CPU.IP = 0
				m.Mem[0x10000] = 0xaa
				m.CPU.Seg[golem.ES] = 0x2cae
				m.CPU.R[golem.AX] = uint16(raw[0] ^ 1)
				if name == "unknown-vga-same" {
					m.CPU.Seg[golem.ES] = 0xa000
					m.CPU.R[golem.AX] = uint16(paint)
				}
				m.CPU.R[golem.DI] = uint16(pos)
				hdNewGameNeed(t, m.Step())
			}
			restoreK := k
			switch name {
			case "wrong-restore-k":
				for i, v := range source {
					if i != k && v == source[k] {
						restoreK = i
						break
					}
				}
				if restoreK == k {
					t.Fatal("缺相同值不同k")
				}
				m.Mem[0xafa00+restoreK] = raw[0]
				m.Mem[0xafb00+restoreK] = paint
			case "wrong-restore-old":
				m.Write8(uint32(0xa0000+pos), paint^1)
			case "wrong-restore-background":
				m.Mem[0xafa00+k] ^= 1
			case "wrong-restore-composition":
				m.Mem[0xafb00+k] ^= 1
			}
			m.CPU.Seg[golem.CS] = 0xb68
			m.CPU.IP = 0x51c
			m.CPU.Seg[golem.DS] = 0xa000
			m.CPU.Seg[golem.ES] = 0xa000
			m.CPU.R[golem.SI] = uint16(0xfa00 + restoreK)
			m.CPU.R[golem.DI] = uint16(pos)
			m.CPU.R[golem.CX] = 1
			hdNewGameNeed(t, m.Step())
			restored := name == "opaque-restore" || name == "post-main-write"
			if (p.published[pos] == cell) != restored || len(p.publishedPending) != 0 {
				t.Fatal("反向配對還原不同", name, p.published[pos])
			}
		})
	}
}

func TestHDTexturePublishedTextBackgroundGuards(t *testing.T) {
	game, root, assets := hdReportFixtures(t)
	h := &hdRuntime{m: golem.New()}
	p, err := loadHDTextureKind(h, game, assets, "wood")
	hdNewGameNeed(t, err)
	raw := hdNewGameRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/1552.idx")
	copy(p.native[:], raw)
	p.accepted = 1
	copy(h.m.Mem, hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control/point-001.memory")))
	palette := hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control/point-001.palette"))
	pos := 21506
	cell := hdSceneCell{slot: 1, local: 0, value: h.m.Mem[0xa0000+pos], glyph: true}
	p.published[pos] = cell
	f := draftNativeFrame{canvas: h.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: bytes.Clone(h.m.Mem[0xa0000 : 0xa0000+64000]), palette: palette, mode: 0x13}
	out := image.NewRGBA(image.Rect(0, 0, 1280, 800))
	if !p.paintPublishedBackground(out, f, pos, raw[0], palette) {
		t.Fatal("已發布字底正例未回畫")
	}
	for _, name := range []string{"wrong-value", "wrong-indexed", "wrong-vga", "wrong-palette", "missing-source", "wrong-mode", "negative", "overflow", "short-canvas", "blocked"} {
		t.Run(name, func(t *testing.T) {
			p.published[pos] = cell
			p.publicationBlocked = false
			bad := f
			bad.indexed = bytes.Clone(f.indexed)
			bad.palette = bytes.Clone(palette)
			at := pos
			value := raw[0]
			h.m.Mem[0xa0000+pos] = cell.value
			switch name {
			case "wrong-value":
				value ^= 1
			case "wrong-indexed":
				bad.indexed[pos] ^= 1
			case "wrong-vga":
				h.m.Mem[0xa0000+pos] ^= 1
			case "wrong-palette":
				bad.palette[int(raw[0])*3] ^= 1
			case "missing-source":
				p.published[pos] = hdSceneCell{}
			case "wrong-mode":
				bad.mode = 0x12
			case "negative":
				at = -1
			case "overflow":
				at = 64000
			case "short-canvas":
				bad.canvas = bad.canvas[:63999]
			case "blocked":
				p.publicationBlocked = true
			}
			result := image.NewRGBA(image.Rect(0, 0, 1280, 800))
			before := bytes.Clone(result.Pix)
			if p.paintPublishedBackground(result, bad, at, value, bad.palette) || !bytes.Equal(before, result.Pix) {
				t.Fatal("未知字底仍回畫", name)
			}
		})
	}
}
