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

func hdSceneFixtures(t *testing.T) (string, string, string) {
	t.Helper()
	game, root, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_SCENE_ROOT"), os.Getenv("TEST_HD_ASSETS")
	if game == "" || root == "" || assets == "" {
		t.Skip("需要合法原版及背景原版收據")
	}
	for _, name := range []string{"OPENING.EXE", "VICEROY.EXE", "COLONY.PIK", "EUROPE.PIK"} {
		if _, e := os.Stat(filepath.Join(game, name)); os.IsNotExist(e) {
			t.Skip("缺合法原版", name)
		}
	}
	return game, root, assets
}
func TestHDSceneNative19(t *testing.T) {
	game, root, assets := hdSceneFixtures(t)
	ref, model := filepath.Join(root, "scene-source-probe-r5"), filepath.Join(root, "scene-source-model-current-r1")
	if alternate := os.Getenv("TEST_HD_SCENE_MODEL"); alternate != "" {
		model = alternate
	}
	var oracle struct {
		Checkpoints []hdNewGameOracleState
		End         hdNewGameOracleState
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(ref, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 19 || oracle.End.Steps != 121000000 {
		t.Fatal("原版來源範圍不同")
	}
	var replay struct{ Inputs []windowInput }
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "current-route-inputs-r2.json")), &replay))
	out := os.Getenv("TEST_HD_SCENE_OUTPUT")
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
			expected := make([]byte, 64000)
			if frame.id == 308 || frame.id == 824 || (frame.id == 1551 && os.Getenv("TEST_HD_SCENE_MODEL") != "") {
				expected = hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d-source-%d-mask.bin", at, frame.id)))
			}
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
	if at != 19 || count != 45 || total == 0 {
		t.Fatal("原版範圍不同", at, count, total)
	}
	if !bytes.Equal(m.Mem, hdNewGameRead(t, filepath.Join(ref, "control/final.memory"))) {
		t.Fatal("完整終點RAM不同")
	}
	for _, frame := range p.frames {
		want := uint64(0)
		if frame.id == 308 || frame.id == 824 || (frame.id == 1551 && os.Getenv("TEST_HD_SCENE_MODEL") != "") {
			want = 1
		}
		if frame.decoded != want {
			t.Fatal("背景解碼次數", frame.id, frame.decoded)
		}
	}
	d.Close()
	if !bytes.Equal(seed, hdNewGameRead(t, filepath.Join(save, "COLONY09.SAV"))) {
		t.Fatal("原版存檔被修改")
	}
	proof := map[string]any{"result": "PASS_SCENE_NATIVE19_SOURCE_PIXELS_AND_STATE", "checkpoints": at, "dos_inputs": count, "rgba_source_pixels": total, "full_rgba_pixels": 19 * 1280 * 800, "points": records, "original_state_and_saves_equal": true, "production_connected": true}
	raw, err := json.MarshalIndent(proof, "", "  ")
	hdNewGameNeed(t, err)
	hdNewGameNeed(t, os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}
func TestHDScenePaletteAndUnderlayGuards(t *testing.T) {
	game, root, assets := hdSceneFixtures(t)
	h := &hdRuntime{m: golem.New()}
	p, err := loadHDSceneRuntime(h, game, assets)
	hdNewGameNeed(t, err)
	for index, point := range []int{4, 9} {
		frame := p.frames[index]
		raw := hdNewGameRead(t, filepath.Join("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels", fmt.Sprintf("%04d.idx", frame.id)))
		if hash(raw) != frame.nativeSHA {
			t.Fatal("獨立來源不同")
		}
		copy(h.m.Mem[0x3c500+frame.offset:0x3c500+64000], raw)
		p.decoded(frame.offset)
		palette := hdNewGameRead(t, filepath.Join(root, "scene-source-probe-r5/control", fmt.Sprintf("point-%03d.palette", point)))
		if !frame.paletteSupported(palette) {
			t.Fatal("正常來源色盤被拒絕", frame.id)
		}
		used := [256]bool{}
		for _, i := range raw {
			used[i] = true
		}
		t.Run(fmt.Sprintf("palette-%d", frame.id), func(t *testing.T) {
			for i := 0; i < 256; i++ {
				for ch := 0; ch < 3; ch++ {
					bad := append([]byte(nil), palette...)
					bad[i*3+ch] ^= 1
					if got := frame.paletteSupported(bad); got == used[i] {
						t.Fatal("實際來源色號守門不同", frame.id, i, ch, got, used[i])
					}
				}
			}
		})
		var model map[string][]any
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "scene-source-model-current-r1", fmt.Sprintf("point-%03d.owners.json", point))), &model))
		canvas := hdNewGameRead(t, filepath.Join(root, "scene-source-probe-r5/control", fmt.Sprintf("point-%03d.canvas", point)))
		found := false
		for key, expected := range model {
			if int(expected[0].(float64)) != frame.id || expected[3].(string) != "glyph" {
				continue
			}
			pos, err := strconv.Atoi(key)
			hdNewGameNeed(t, err)
			c := hdSceneCell{slot: uint8(index + 1), local: uint16(expected[1].(float64)), value: byte(expected[2].(float64)), glyph: true}
			p.visible[pos] = c
			f := draftNativeFrame{canvas: canvas, palette: palette, mode: 0x13}
			out := image.NewRGBA(image.Rect(0, 0, 1280, 800))
			native := frame.native[c.local]
			if !p.paintBackground(out, f, pos, native, palette) {
				t.Fatal("已驗字底未重繪")
			}
			tests := []struct {
				name    string
				pos     int
				value   byte
				f       draftNativeFrame
				palette []byte
			}{
				{"wrong-background", pos, native ^ 1, f, palette}, {"negative-position", -1, native, f, palette}, {"overflow-position", 64000, native, f, palette},
			}
			badCanvas := f
			badCanvas.canvas = append([]byte(nil), canvas...)
			badCanvas.canvas[pos] ^= 1
			tests = append(tests, struct {
				name    string
				pos     int
				value   byte
				f       draftNativeFrame
				palette []byte
			}{"invalid-current-pixel", pos, native, badCanvas, palette})
			badMode := f
			badMode.mode = 3
			tests = append(tests, struct {
				name    string
				pos     int
				value   byte
				f       draftNativeFrame
				palette []byte
			}{"wrong-mode", pos, native, badMode, palette})
			for _, tc := range tests {
				t.Run(fmt.Sprintf("underlay-%d-%s", frame.id, tc.name), func(t *testing.T) {
					if p.paintBackground(out, tc.f, tc.pos, tc.value, tc.palette) {
						t.Fatal("錯誤字底仍重繪")
					}
				})
			}
			found = true
			break
		}
		if !found {
			t.Fatal("缺原版正常字底正例", frame.id)
		}
	}
}
func TestHDSceneResourceFaults(t *testing.T) {
	game, _, assets := hdSceneFixtures(t)
	root := t.TempDir()
	g, a := filepath.Join(root, "game"), filepath.Join(root, "graphics")
	hdNewGameNeed(t, os.Mkdir(g, 0755))
	hdNewGameNeed(t, os.Mkdir(a, 0755))
	var files []string
	for _, frame := range hdSceneDefinitions {
		for _, pair := range [][2]string{{filepath.Join(game, frame.file), filepath.Join(g, frame.file)}, {filepath.Join(assets, frame.asset), filepath.Join(a, frame.asset)}} {
			hdNewGameNeed(t, os.WriteFile(pair[1], hdNewGameRead(t, pair[0]), 0644))
			files = append(files, pair[1])
		}
	}
	if _, err := loadHDSceneRuntime(&hdRuntime{m: golem.New()}, g, a); err != nil {
		t.Fatal("完整拒絕測試副本不可載入", err)
	}
	for _, file := range files {
		for _, kind := range []string{"missing", "wrong-bytes", "linked", "oversize"} {
			t.Run(filepath.Base(file)+"-"+kind, func(t *testing.T) {
				original := hdNewGameRead(t, file)
				defer func() { os.Remove(file); hdNewGameNeed(t, os.WriteFile(file, original, 0644)) }()
				hdNewGameNeed(t, os.Remove(file))
				switch kind {
				case "missing":
				case "wrong-bytes":
					bad := append([]byte(nil), original...)
					bad[len(bad)/2] ^= 1
					hdNewGameNeed(t, os.WriteFile(file, bad, 0644))
				case "linked":
					target := file + ".reference"
					hdNewGameNeed(t, os.WriteFile(target, original, 0644))
					defer os.Remove(target)
					hdNewGameNeed(t, os.Symlink(target, file))
				case "oversize":
					f, e := os.Create(file)
					hdNewGameNeed(t, e)
					hdNewGameNeed(t, f.Truncate((8<<20)+1))
					hdNewGameNeed(t, f.Close())
				}
				if _, err := loadHDSceneRuntime(&hdRuntime{m: golem.New()}, g, a); err == nil {
					t.Fatal("錯誤來源仍載入", file, kind)
				}
			})
		}
	}
}
