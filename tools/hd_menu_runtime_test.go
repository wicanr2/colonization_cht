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
