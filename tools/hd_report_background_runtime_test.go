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
	"strconv"
	"testing"
)

func hdReportFixtures(t *testing.T) (string, string, string) {
	t.Helper()
	game, root, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_REPORT_ROOT"), os.Getenv("TEST_HD_ASSETS")
	if game == "" || root == "" || assets == "" {
		t.Skip("需要合法原版及報告來源收據")
	}
	for _, name := range []string{"VICEROY.EXE", "OPENING.EXE", "REPORT1.PIK", "REPORT2.PIK", "REPORT3.PIK", "REPORT4.PIK", "REPORT5.PIK", "REPORT6.PIK", "REPORT7.PIK", "REPORT8.PIK"} {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺合法原版", name)
		}
	}
	return game, root, assets
}
func TestHDReportNative27(t *testing.T) {
	game, root, assets := hdReportFixtures(t)
	ref, model := filepath.Join(root, "report-source-probe-r2"), filepath.Join(root, "report-source-model-r3")
	if alternate := os.Getenv("TEST_HD_REPORT_MODEL"); alternate != "" {
		model = alternate
	}
	var oracle struct {
		Checkpoints []hdNewGameOracleState
		End         hdNewGameOracleState
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(ref, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 27 || oracle.End.Steps != 192600000 {
		t.Fatal("原版來源範圍不同")
	}
	var replay struct{ Inputs []windowInput }
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "report-baseline-inputs-r1.json")), &replay))
	out := os.Getenv("TEST_HD_REPORT_OUTPUT")
	if out == "" {
		t.Skip("需要新的背景驗證輸出")
	}
	hdNewGameNeed(t, os.Mkdir(out, 0755))
	save := filepath.Join(out, "save")
	hdNewGameNeed(t, os.Mkdir(save, 0755))
	seed := hdNewGameRead(t, filepath.Join(ref, "control/saves/COLONY09.SAV"))
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
	p, err := loadHDSceneRuntime(h, game, assets)
	hdNewGameNeed(t, err)
	h.scenes = p
	checkState := func(s hdNewGameOracleState) {
		t.Helper()
		c := m.CPU
		if m.Steps != s.Steps || hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("背景觀測改變原版完整狀態", m.Steps)
		}
	}
	at, count := 0, uint64(0)
	records := []map[string]any{}
	total := 0
	capture := func() {
		if at == len(oracle.Checkpoints) {
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
		var wanted map[string][]any
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d.owners.json", at))), &wanted))
		for pos, c := range p.visible {
			expected, yes := wanted[strconv.Itoa(pos)]
			if !yes {
				if c.slot != 0 {
					t.Fatal("無來源仍持有背景", at, pos)
				}
				continue
			}
			frame, known := p.frame(c)
			if !known || frame.id != int(expected[0].(float64)) || int(c.local) != int(expected[1].(float64)) || int(c.value) != int(expected[2].(float64)) || c.glyph != (expected[3].(string) == "glyph") {
				t.Fatal("獨立來源擁有權不同", at, pos, c, expected)
			}
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		im, receipt := h.base(f)
		h.restoreCursor(im, f)
		masks := map[int][]byte{}
		painted := map[int]int{}
		for _, frame := range p.frames {
			if frame.id == 1002 || (frame.id >= 1005 && frame.id <= 1014) {
				continue
			}
			expected := hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d-source-%d-mask.bin", at, frame.id)))
			if len(expected) != 64000 {
				t.Fatal("來源遮罩長度")
			}
			packed := make([]byte, 8000)
			for k, v := range expected {
				if v != 0 {
					packed[k>>3] |= 1 << uint(k&7)
					painted[frame.id]++
				}
			}
			masks[frame.id] = expected
			if group, yes := receipt["scene_picture"].(map[string]any); yes {
				src := group["sources"].(map[string]any)[fmt.Sprint(frame.id)].(map[string]any)
				if src["painted"].(int) != painted[frame.id] || !bytes.Equal(src["mask"].([]byte), packed) {
					t.Fatal("獨立來源遮罩不同", at, frame.id, src["painted"], painted[frame.id])
				}
			} else if painted[frame.id] != 0 {
				t.Fatal("正常來源被守門拒絕", at, receipt["reason"])
			}
		}

		if publishedModel := os.Getenv("TEST_HD_PUBLISHED_MODEL"); publishedModel != "" {
			var expectedPublished map[string][]any
			hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(publishedModel, fmt.Sprintf("point-%03d.published.json", at))), &expectedPublished))
			for pos, c := range p.published {
				expected, yes := expectedPublished[strconv.Itoa(pos)]
				if !yes {
					if c.slot != 0 {
						t.Fatal("未知VGA點仍持有來源", at, pos)
					}
					continue
				}
				frame, known := p.frame(c)
				if !known || frame.id != int(expected[0].(float64)) || int(c.local) != int(expected[1].(float64)) || int(c.value) != int(expected[2].(float64)) || c.glyph != (expected[3].(string) == "glyph") {
					t.Fatal("已送出來源與獨立逐寫模型不同", at, pos)
				}
			}
			publishedImage := draftRGB(f.indexed, f.palette)
			publishedReceipt := p.paintPublished(publishedImage, f)
			sources, ok := publishedReceipt["sources"].(map[string]any)
			if !ok || publishedReceipt["reason"] != "published-scene-background-only" {
				t.Fatal("已送出來源未驗", at, publishedReceipt)
			}
			expectedCells := map[int]*hdSceneFrame{}
			for _, frame := range p.frames {
				if frame.id == 1002 || (frame.id >= 1005 && frame.id <= 1014) {
					continue
				}
				expectedMask := hdNewGameRead(t, filepath.Join(publishedModel, fmt.Sprintf("point-%03d-published-%d-mask.bin", at, frame.id)))
				packed := make([]byte, 8000)
				count := 0
				for pos, v := range expectedMask {
					if v != 0 {
						packed[pos>>3] |= 1 << uint(pos&7)
						count++
						expectedCells[pos] = frame
					}
				}
				got := sources[fmt.Sprint(frame.id)].(map[string]any)
				if got["painted"].(int) != count || !bytes.Equal(got["mask"].([]byte), packed) {
					t.Fatal("已送出來源遮罩不同", at, frame.id)
				}
			}
			before := draftRGB(f.indexed, f.palette)
			for y := 0; y < 800; y++ {
				for x := 0; x < 1280; x++ {
					pos := y/4*320 + x/4
					want := before.RGBAAt(x, y)
					if frame := expectedCells[pos]; frame != nil {
						c := p.published[pos]
						want = frame.art.RGBAAt(int(c.local)%320*4+x%4, int(c.local)/320*4+y%4)
					}
					if publishedImage.RGBAAt(x, y) != want {
						t.Fatal("已送出背景RGBA或原版前景不同", at, x, y)
					}
				}
			}
			checkState(s)
			file, e := os.Create(filepath.Join(out, fmt.Sprintf("point-%03d-published.png", at)))
			hdNewGameNeed(t, e)
			hdNewGameNeed(t, png.Encode(file, publishedImage))
			hdNewGameNeed(t, file.Close())
		}

		baseline := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				k := y/4*320 + x/4
				wantedPixel := baseline.RGBAAt(x, y)
				cursorIndex := (y/4-f.cursor.Min.Y)*16 + x/4 - f.cursor.Min.X
				opaqueCursor := image.Pt(x/4, y/4).In(f.cursor) && cursorIndex >= 0 && cursorIndex < 256 && m.Mem[0x1cd74+cursorIndex] != 255
				if !opaqueCursor {
					for _, frame := range p.frames {
						if frame.id == 1002 || (frame.id >= 1005 && frame.id <= 1014) {
							continue
						}
						if masks[frame.id][k] != 0 {
							c := p.visible[k]
							wantedPixel = frame.art.RGBAAt(int(c.local)%320*4+x%4, int(c.local)/320*4+y%4)
							total++
						}
					}
				}
				if im.RGBAAt(x, y) != wantedPixel {
					t.Fatal("背景RGBA或前景保留不同", at, x, y)
				}
			}
		}
		checkState(s)
		file, err := os.Create(filepath.Join(out, fmt.Sprintf("point-%03d.png", at)))
		hdNewGameNeed(t, err)
		hdNewGameNeed(t, png.Encode(file, im))
		hdNewGameNeed(t, file.Close())
		records = append(records, map[string]any{"point": at, "step": m.Steps, "painted": painted, "native_memory_sha256": hash(m.Mem), "native_indexed_sha256": hash(m.Indexed())})
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
	if at != 27 || count != 42 || total == 0 {
		t.Fatal("原版範圍不同", at, count, total)
	}
	if !bytes.Equal(m.Mem, hdNewGameRead(t, filepath.Join(ref, "control/final.memory"))) {
		t.Fatal("完整終點RAM不同")
	}
	for _, frame := range p.frames {
		if frame.id == 1002 || (frame.id >= 1005 && frame.id <= 1014) {
			continue
		}
		want := map[int]uint64{120: 1, 1551: 2, 308: 1, 824: 0, 1442: 1, 1443: 1, 1444: 1, 1445: 1, 1446: 2, 1447: 2, 1448: 1, 1449: 1}[frame.id]
		if frame.decoded != want {
			t.Fatal("背景解碼次數", frame.id, frame.decoded)
		}
	}
	d.Close()
	if !bytes.Equal(seed, hdNewGameRead(t, filepath.Join(save, "COLONY09.SAV"))) {
		t.Fatal("原版存檔被修改")
	}
	proof := map[string]any{"result": "PASS_REPORT_NATIVE27_SOURCE_PIXELS_AND_STATE", "checkpoints": at, "dos_inputs": count, "rgba_source_pixels": total, "full_rgba_pixels": 27 * 1280 * 800, "points": records, "original_state_and_saves_equal": true, "production_connected": true}
	raw, err := json.MarshalIndent(proof, "", "  ")
	hdNewGameNeed(t, err)
	hdNewGameNeed(t, os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDReportPaletteDecodeAndUnderlayGuards(t *testing.T) {
	game, root, assets := hdReportFixtures(t)
	h := &hdRuntime{m: golem.New()}
	p, err := loadHDSceneRuntime(h, game, assets)
	hdNewGameNeed(t, err)
	var summary struct {
		Points []struct {
			Sources map[string]struct{ Painted int }
		}
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "report-source-model-r3/check.json")), &summary))
	for index, frame := range p.frames {
		if frame.id < 1442 || frame.id > 1449 {
			continue
		}
		point := -1
		for i, c := range summary.Points {
			if c.Sources[fmt.Sprint(frame.id)].Painted > 0 {
				point = i
				break
			}
		}
		if point < 0 {
			t.Fatal("缺正常報告正例", frame.id)
		}
		raw := hdNewGameRead(t, filepath.Join("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels", fmt.Sprintf("%04d.idx", frame.id)))
		if len(raw) != 64000 || hash(raw) != frame.nativeSHA {
			t.Fatal("報告原版來源不同")
		}
		copy(h.m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000], raw)
		p.decodedAt(hdBuildingCanvas, 0)
		if frame.decoded != 1 {
			t.Fatal("直接主畫布來源未授權")
		}
		t.Run(fmt.Sprintf("decode-%d-wrong-buffer", frame.id), func(t *testing.T) {
			before := p.visible
			copy(h.m.Mem[0x3c500:0x3c500+64000], raw)
			p.decodedAt(0x3c500, 0)
			if frame.decoded != 1 || p.visible != before {
				t.Fatal("錯基址仍授權報告來源")
			}
		})
		t.Run(fmt.Sprintf("decode-%d-wrong-bytes", frame.id), func(t *testing.T) {
			before := p.visible
			h.m.Mem[hdBuildingCanvas+32000] ^= 1
			p.decodedAt(hdBuildingCanvas, 0)
			if frame.decoded != 1 || p.visible != before {
				t.Fatal("錯IDX仍授權報告來源")
			}
			h.m.Mem[hdBuildingCanvas+32000] ^= 1
		})
		palette := hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control", fmt.Sprintf("point-%03d.palette", point)))
		if !frame.paletteSupported(palette) {
			t.Fatal("正常報告色盤被拒絕")
		}
		used := [256]bool{}
		for _, v := range raw {
			used[v] = true
		}
		t.Run(fmt.Sprintf("palette-%d", frame.id), func(t *testing.T) {
			for i := 0; i < 256; i++ {
				for ch := 0; ch < 3; ch++ {
					bad := append([]byte(nil), palette...)
					bad[i*3+ch] ^= 1
					if got := frame.paletteSupported(bad); got == used[i] {
						t.Fatal("使用色號精確守門不同", i, ch)
					}
				}
			}
		})
		var owners map[string][]any
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "report-source-model-r3", fmt.Sprintf("point-%03d.owners.json", point))), &owners))
		canvas := hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control", fmt.Sprintf("point-%03d.canvas", point)))
		found := false
		for key, expected := range owners {
			if int(expected[0].(float64)) != frame.id || expected[3].(string) != "glyph" {
				continue
			}
			pos, e := strconv.Atoi(key)
			hdNewGameNeed(t, e)
			cell := hdSceneCell{slot: uint8(index + 1), local: uint16(expected[1].(float64)), value: byte(expected[2].(float64)), glyph: true}
			p.visible[pos] = cell
			f := draftNativeFrame{canvas: canvas, palette: palette, mode: 0x13}
			out := image.NewRGBA(image.Rect(0, 0, 1280, 800))
			native := frame.native[cell.local]
			if !p.paintBackground(out, f, pos, native, palette) {
				t.Fatal("正常報告字底未重繪", frame.id)
			}
			cases := []struct {
				name  string
				pos   int
				value byte
				frame draftNativeFrame
			}{
				{"wrong-background", pos, native ^ 1, f}, {"negative-position", -1, native, f}, {"overflow-position", 64000, native, f},
			}
			bad := f
			bad.canvas = append([]byte(nil), canvas...)
			bad.canvas[pos] ^= 1
			cases = append(cases, struct {
				name  string
				pos   int
				value byte
				frame draftNativeFrame
			}{"wrong-current-pixel", pos, native, bad})
			bad = f
			bad.mode = 3
			cases = append(cases, struct {
				name  string
				pos   int
				value byte
				frame draftNativeFrame
			}{"wrong-mode", pos, native, bad})
			for _, tc := range cases {
				t.Run(fmt.Sprintf("underlay-%d-%s", frame.id, tc.name), func(t *testing.T) {
					if p.paintBackground(out, tc.frame, tc.pos, tc.value, palette) {
						t.Fatal("錯誤字底仍重繪")
					}
				})
			}
			found = true
			break
		}
		if !found {
			t.Fatal("缺已驗報告字底", frame.id)
		}
	}
}

func TestHDPublishedNative32(t *testing.T) {
	game, _, assets := hdReportFixtures(t)
	root := os.Getenv("TEST_HD_CURSOR_ROOT")
	model := os.Getenv("TEST_HD_CURSOR_MODEL")
	if root == "" || model == "" {
		t.Skip("需要已發布游標32點原版來源")
	}
	ref := filepath.Join(root, "published-cursor-source-probe-r1")
	var oracle struct {
		Checkpoints []hdNewGameOracleState
		End         hdNewGameOracleState
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(ref, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 32 || oracle.End.Steps != 72800000 {
		t.Fatal("原版來源範圍不同")
	}
	var replay struct{ Inputs []windowInput }
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join("/r79", "formal-published-inputs-r1.json")), &replay))
	out := os.Getenv("TEST_HD_PUBLISHED_OUTPUT")
	if out == "" {
		t.Skip("需要新的背景驗證輸出")
	}
	hdNewGameNeed(t, os.Mkdir(out, 0755))
	save := filepath.Join(out, "save")
	hdNewGameNeed(t, os.Mkdir(save, 0755))
	seed := hdNewGameRead(t, filepath.Join(ref, "control/saves/COLONY09.SAV"))
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
	p, err := loadHDSceneRuntime(h, game, assets)
	hdNewGameNeed(t, err)
	h.scenes = p
	checkState := func(s hdNewGameOracleState) {
		t.Helper()
		c := m.CPU
		if m.Steps != s.Steps || hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("背景觀測改變原版完整狀態", m.Steps)
		}
	}
	at, count := 0, uint64(0)
	records := []map[string]any{}
	total := 0
	capture := func() {
		if at == len(oracle.Checkpoints) {
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
		var wanted map[string][]any
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d.owners.json", at))), &wanted))
		for pos, c := range p.visible {
			expected, yes := wanted[strconv.Itoa(pos)]
			if !yes {
				if c.slot != 0 {
					t.Fatal("無來源仍持有背景", at, pos)
				}
				continue
			}
			frame, known := p.frame(c)
			if !known || frame.id != int(expected[0].(float64)) || int(c.local) != int(expected[1].(float64)) || int(c.value) != int(expected[2].(float64)) || c.glyph != (expected[3].(string) == "glyph") {
				t.Fatal("獨立來源擁有權不同", at, pos, c, expected)
			}
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		im, receipt := h.base(f)
		h.restoreCursor(im, f)
		masks := map[int][]byte{}
		painted := map[int]int{}
		for _, frame := range p.frames {
			expected := hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d-source-%d-mask.bin", at, frame.id)))
			if len(expected) != 64000 {
				t.Fatal("來源遮罩長度")
			}
			packed := make([]byte, 8000)
			for k, v := range expected {
				if v != 0 {
					packed[k>>3] |= 1 << uint(k&7)
					painted[frame.id]++
				}
			}
			masks[frame.id] = expected
			if group, yes := receipt["scene_picture"].(map[string]any); yes {
				src := group["sources"].(map[string]any)[fmt.Sprint(frame.id)].(map[string]any)
				if src["painted"].(int) != painted[frame.id] || !bytes.Equal(src["mask"].([]byte), packed) {
					t.Fatal("獨立來源遮罩不同", at, frame.id, src["painted"], painted[frame.id])
				}
			} else if painted[frame.id] != 0 {
				t.Fatal("正常來源被守門拒絕", at, receipt["reason"])
			}
		}

		if publishedModel := os.Getenv("TEST_HD_CURSOR_MODEL"); publishedModel != "" {
			var expectedPublished map[string][]any
			hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(publishedModel, fmt.Sprintf("point-%03d.published.json", at))), &expectedPublished))
			for pos, c := range p.published {
				expected, yes := expectedPublished[strconv.Itoa(pos)]
				if !yes {
					if c.slot != 0 {
						t.Fatal("未知VGA點仍持有來源", at, pos)
					}
					continue
				}
				frame, known := p.frame(c)
				if !known || frame.id != int(expected[0].(float64)) || int(c.local) != int(expected[1].(float64)) || int(c.value) != int(expected[2].(float64)) || c.glyph != (expected[3].(string) == "glyph") {
					t.Fatal("已送出來源與獨立逐寫模型不同", at, pos)
				}
			}
			publishedImage := draftRGB(f.indexed, f.palette)
			publishedReceipt := p.paintPublished(publishedImage, f)
			sources, ok := publishedReceipt["sources"].(map[string]any)
			if !ok || publishedReceipt["reason"] != "published-scene-background-only" {
				t.Fatal("已送出來源未驗", at, publishedReceipt)
			}
			expectedCells := map[int]*hdSceneFrame{}
			for _, frame := range p.frames {
				expectedMask := hdNewGameRead(t, filepath.Join(publishedModel, fmt.Sprintf("point-%03d-published-%d-mask.bin", at, frame.id)))
				packed := make([]byte, 8000)
				count := 0
				for pos, v := range expectedMask {
					if v != 0 {
						packed[pos>>3] |= 1 << uint(pos&7)
						count++
						expectedCells[pos] = frame
					}
				}
				got := sources[fmt.Sprint(frame.id)].(map[string]any)
				if got["painted"].(int) != count || !bytes.Equal(got["mask"].([]byte), packed) {
					t.Fatal("已送出來源遮罩不同", at, frame.id)
				}
			}
			before := draftRGB(f.indexed, f.palette)
			for y := 0; y < 800; y++ {
				for x := 0; x < 1280; x++ {
					pos := y/4*320 + x/4
					want := before.RGBAAt(x, y)
					if frame := expectedCells[pos]; frame != nil {
						c := p.published[pos]
						want = frame.art.RGBAAt(int(c.local)%320*4+x%4, int(c.local)/320*4+y%4)
					}
					if publishedImage.RGBAAt(x, y) != want {
						t.Fatal("已送出背景RGBA或原版前景不同", at, x, y)
					}
				}
			}
			checkState(s)
			file, e := os.Create(filepath.Join(out, fmt.Sprintf("point-%03d-published.png", at)))
			hdNewGameNeed(t, e)
			hdNewGameNeed(t, png.Encode(file, publishedImage))
			hdNewGameNeed(t, file.Close())
		}

		baseline := draftRGB(f.indexed, f.palette)
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				k := y/4*320 + x/4
				wantedPixel := baseline.RGBAAt(x, y)
				cursorIndex := (y/4-f.cursor.Min.Y)*16 + x/4 - f.cursor.Min.X
				opaqueCursor := image.Pt(x/4, y/4).In(f.cursor) && cursorIndex >= 0 && cursorIndex < 256 && m.Mem[0x1cd74+cursorIndex] != 255
				if !opaqueCursor {
					for _, frame := range p.frames {
						if masks[frame.id][k] != 0 {
							c := p.visible[k]
							wantedPixel = frame.art.RGBAAt(int(c.local)%320*4+x%4, int(c.local)/320*4+y%4)
							total++
						}
					}
				}
				if im.RGBAAt(x, y) != wantedPixel {
					t.Fatal("背景RGBA或前景保留不同", at, x, y)
				}
			}
		}
		checkState(s)
		file, err := os.Create(filepath.Join(out, fmt.Sprintf("point-%03d.png", at)))
		hdNewGameNeed(t, err)
		hdNewGameNeed(t, png.Encode(file, im))
		hdNewGameNeed(t, file.Close())
		records = append(records, map[string]any{"point": at, "step": m.Steps, "painted": painted, "native_memory_sha256": hash(m.Mem), "native_indexed_sha256": hash(m.Indexed())})
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
	if !bytes.Equal(m.Mem, hdNewGameRead(t, filepath.Join(ref, "control/final.memory"))) {
		t.Fatal("完整終點RAM不同")
	}
	for _, frame := range p.frames {
		want := map[int]uint64{120: 0, 1551: 1, 308: 1, 824: 0, 1442: 0, 1443: 0, 1444: 0, 1445: 0, 1446: 0, 1447: 0, 1448: 0, 1449: 0}[frame.id]
		if frame.decoded != want {
			t.Fatal("背景解碼次數", frame.id, frame.decoded)
		}
	}
	d.Close()
	if !bytes.Equal(seed, hdNewGameRead(t, filepath.Join(save, "COLONY09.SAV"))) {
		t.Fatal("原版存檔被修改")
	}
	proof := map[string]any{"result": "PASS_PUBLISHED_CURSOR_NATIVE32_SOURCE_RGBA_AND_STATE", "checkpoints": at, "dos_inputs": count, "rgba_source_pixels": total, "full_rgba_pixels": 32 * 1280 * 800, "points": records, "original_state_and_saves_equal": true, "production_connected": true}
	raw, err := json.MarshalIndent(proof, "", "  ")
	hdNewGameNeed(t, err)
	hdNewGameNeed(t, os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

// 規格069 R89 READY：實際原版來源的byte發布與無游標守門。

func hdStoryFixtures(t *testing.T) (string, string, string) {
	t.Helper()
	game, root, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_STORY_ROOT"), os.Getenv("TEST_HD_ASSETS")
	if game == "" || root == "" || assets == "" {
		t.Skip("需要合法原版、國王／出航來源收據與HD素材")
	}
	for _, def := range hdSceneDefinitions {
		if _, e := os.Stat(filepath.Join(game, def.file)); os.IsNotExist(e) {
			t.Skip("缺合法原版", def.file)
		}
	}
	return game, root, assets
}
func hdStorySnapshot(t *testing.T, at int) (*hdRuntime, *hdSceneRuntime, draftNativeFrame) {
	t.Helper()
	game, root, assets := hdStoryFixtures(t)
	m := golem.New()
	h := &hdRuntime{m: m}
	p, e := loadHDSceneRuntime(h, game, assets)
	hdNewGameNeed(t, e)
	h.scenes = p
	for _, frame := range p.frames {
		if frame.id != 1002 && (frame.id < 1005 || frame.id > 1014) {
			continue
		}
		raw := hdNewGameRead(t, fmt.Sprintf("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/%04d.idx", frame.id))
		base := frame.canvas
		if base == 0 {
			base = 0x3c500
		}
		copy(m.Mem[base:base+64000], raw)
		p.decodedAt(base, 0)
	}
	stem := fmt.Sprintf("point-%03d", at)
	dir := filepath.Join(root, "nation-story-source-probe-r3/observed")
	copy(m.Mem, hdNewGameRead(t, filepath.Join(dir, stem+".memory")))
	clear(p.visible[:])
	clear(p.published[:])
	for _, pair := range []struct {
		target *[64000]hdSceneCell
		suffix string
	}{{&p.visible, ".owners.json"}, {&p.published, ".published.json"}} {
		var cells map[string][]any
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "nation-story-published-source-model-r4", stem+pair.suffix)), &cells))
		for key, c := range cells {
			pos, e := strconv.Atoi(key)
			hdNewGameNeed(t, e)
			slot := 0
			for i, frame := range p.frames {
				if frame.id == int(c[0].(float64)) {
					slot = i + 1
				}
			}
			if slot == 0 {
				t.Fatal("source", c)
			}
			pair.target[pos] = hdSceneCell{slot: uint8(slot), local: uint16(c[1].(float64)), value: byte(c[2].(float64)), glyph: c[3].(string) == "glyph"}
		}
	}
	var points []struct {
		Mouse struct{ X, Y int } `json:"dos_mouse"`
		Step  uint64             `json:"step"`
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "normal-nation-story-points-r1.json")), &points))
	v := points[at]
	f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: hdNewGameRead(t, filepath.Join(dir, stem+".idx")), palette: hdNewGameRead(t, filepath.Join(dir, stem+".palette")), cursor: image.Rect(v.Mouse.X, v.Mouse.Y, v.Mouse.X+16, v.Mouse.Y+16), mode: 0x13, step: v.Step}
	return h, p, f
}
func TestHDStoryPictureCursorGuards(t *testing.T) {
	_, root, _ := hdStoryFixtures(t)
	for _, name := range []string{"known", "missing-cell", "unknown-slot", "invalid-local", "wrong-value", "changed-indexed", "legacy-source", "same-value-write", "wrong-cursor", "short-indexed", "blocked", "glyph-underlay"} {
		t.Run(name, func(t *testing.T) {
			h, p, f := hdStorySnapshot(t, 8)
			pos := f.cursor.Min.Y*320 + f.cursor.Min.X
			if !p.pictureOnlyCursor(f) {
				t.Fatal("positive proof missing")
			}
			_, reason := h.cursorProof(f)
			if reason == "" {
				t.Fatal("needs hidden cursor fixture")
			}
			switch name {
			case "missing-cell":
				p.published[pos] = hdSceneCell{}
			case "unknown-slot":
				p.published[pos].slot = 255
			case "invalid-local":
				p.published[pos].local = 65535
			case "wrong-value":
				p.published[pos].value ^= 1
			case "changed-indexed":
				f.indexed = bytes.Clone(f.indexed)
				f.indexed[pos] ^= 1
			case "legacy-source":
				for _, frame := range p.frames {
					frame.allowPictureCursorProof = false
				}
			case "same-value-write":
				h.m.CPU.Seg[golem.CS] = 0x1000
				h.m.CPU.IP = 0
				h.m.Mem[0x10000] = 0xaa
				h.m.CPU.Seg[golem.ES] = 0xa000
				h.m.CPU.R[golem.DI] = uint16(pos)
				h.m.CPU.R[golem.AX] = uint16(f.indexed[pos])
				hdNewGameNeed(t, h.m.Step())
			case "wrong-cursor":
				f.cursor.Max.X--
			case "short-indexed":
				f.indexed = f.indexed[:63999]
			case "blocked":
				p.blocked = true
			case "glyph-underlay":
				p.published[pos].glyph = true
			}
			accepted := name == "known" || name == "glyph-underlay"
			if p.pictureOnlyCursor(f) != accepted {
				t.Fatal("picture cursor guard", name)
			}
			im := draftRGB(hdNewGameRead(t, filepath.Join(root, "nation-story-source-probe-r3/observed/point-008.idx")), f.palette)
			before := bytes.Clone(im.Pix)
			got := p.paintPublished(im, f)
			if !accepted && (got["painted"] != 0 || !bytes.Equal(before, im.Pix)) {
				t.Fatal("unknown cursor painted", name, got)
			}
			if accepted && got["painted"] == 0 {
				t.Fatal("positive not painted", name)
			}
		})
	}
}
func TestHDStoryBytePublication(t *testing.T) {
	game, _, assets := hdStoryFixtures(t)
	for _, name := range []string{"known", "wrong-code", "wrong-CS", "wrong-IP", "wrong-ES", "wrong-DS", "changed-source", "missing-owner", "wrong-owner-value", "same-value-revoke", "post-main-write", "word-second-byte"} {
		t.Run(name, func(t *testing.T) {
			m := golem.New()
			h := &hdRuntime{m: m}
			p, e := loadHDSceneRuntime(h, game, assets)
			hdNewGameNeed(t, e)
			raw := hdNewGameRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/1005.idx")
			copy(m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000], raw)
			p.decodedAt(hdBuildingCanvas, 0)
			pos := 40000
			m.CPU.Seg[golem.CS] = 0xe2d
			m.CPU.IP = 0xaa
			m.CPU.Seg[golem.DS] = 0x2cae
			m.CPU.Seg[golem.ES] = 0xa000
			m.CPU.R[golem.SI] = uint16(pos)
			m.CPU.R[golem.DI] = uint16(pos)
			m.CPU.Flags &^= 0x400
			copy(m.Mem[0xe2d0+0xaa:], hdSceneVGAByteCode)
			switch name {
			case "wrong-code":
				m.Mem[0xe2d0+0xaa+15] ^= 1
			case "wrong-CS":
				m.CPU.Seg[golem.CS]++
				copy(m.Mem[0xe2e0+0xaa:], hdSceneVGAByteCode)
			case "wrong-IP":
				m.CPU.IP++
				copy(m.Mem[0xe2d0+0xab:], hdSceneVGAByteCode)
			case "wrong-ES":
				m.CPU.Seg[golem.ES]++
			case "wrong-DS":
				m.CPU.Seg[golem.DS]++
			case "changed-source":
				m.Mem[hdBuildingCanvas+uint32(pos)] ^= 1
			case "missing-owner":
				p.visible[pos] = hdSceneCell{}
			case "wrong-owner-value":
				p.visible[pos].value ^= 1
			case "word-second-byte":
				m.Mem[0xe2d0+0xaa] = 0xa5
			}
			hdNewGameNeed(t, m.Step())
			accepted := name == "known" || name == "same-value-revoke" || name == "post-main-write"
			if (p.published[pos].slot != 0) != accepted {
				t.Fatal("byte publication", name, p.published[pos])
			}
			if name == "same-value-revoke" || name == "post-main-write" {
				previous := p.published[pos]
				m.CPU.Seg[golem.CS] = 0x1000
				m.CPU.IP = 0
				m.Mem[0x10000] = 0xaa
				m.CPU.Seg[golem.ES] = 0xa000
				if name == "post-main-write" {
					m.CPU.Seg[golem.ES] = 0x2cae
				}
				m.CPU.R[golem.DI] = uint16(pos)
				m.CPU.R[golem.AX] = uint16(raw[pos])
				hdNewGameNeed(t, m.Step())
				if name == "same-value-revoke" && p.published[pos].slot != 0 {
					t.Fatal("same value kept")
				}
				if name == "post-main-write" && (p.published[pos] != previous || p.visible[pos].slot != 0) {
					t.Fatal("main polluted")
				}
			}
		})
	}
}
