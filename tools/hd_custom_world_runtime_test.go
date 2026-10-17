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

func TestHDCustomWorldNative89(t *testing.T) {
	game, root, _ := hdCustomWorldFixtures(t)
	ref := filepath.Join(root, "native-source-r2")
	var oracle struct {
		Checkpoints []hdNewGameOracleState
		End         hdNewGameOracleState
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(ref, "control/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 89 || oracle.End.Steps < 100000000 {
		t.Fatal("正常路徑範圍不同")
	}
	var replay struct{ Inputs []windowInput }
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(ref, "inputs.json")), &replay))
	out := os.Getenv("TEST_CUSTOM_WORLD_OUTPUT")
	if out == "" {
		t.Skip("需要新的原生驗證輸出目錄")
	}
	hdNewGameNeed(t, os.Mkdir(out, 0755))
	save := filepath.Join(out, "save")
	hdNewGameNeed(t, os.Mkdir(save, 0755))
	seed := hdNewGameRead(t, filepath.Join(ref, "control/saves/COLONY09.SAV"))
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("初始存檔不同")
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
	h, err := loadHDRuntime(m, game, os.Getenv("TEST_HD_ASSETS"))
	hdNewGameNeed(t, err)
	p := h.newGame
	if p == nil {
		t.Fatal("未載入新遊戲候選")
	}
	m.SetBeforeInstruction(h.beforeInstruction)
	checkState := func(s hdNewGameOracleState) {
		t.Helper()
		c := m.CPU
		if m.Steps != s.Steps || hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed ||
			hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("完整原版狀態不同", m.Steps)
		}
	}
	at, count, total := 0, uint64(0), 0
	records := []map[string]any{}
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
		var model hdNewGameModelPoint
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "native-custom-model-r4", fmt.Sprintf("point-%03d.json", at))), &model))
		if !bytes.Equal(p.glyphMask(), model.Glyph) || !bytes.Equal(p.borderMask(), model.Border) {
			t.Fatal("獨立字形生命週期不同", at)
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:],
			cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), mode: m.VideoMode(), step: m.Steps}
		h.newGame = nil
		baseline, _ := h.base(f)
		h.newGame = p
		im, receipt := h.base(f)
		h.restoreCursor(im, f)
		h.cursor.paint(h, im, f)
		h.restoreCursor(baseline, f)
		h.cursor.paint(h, baseline, f)
		group, ok := receipt["new_game_picture"].(map[string]any)
		if !ok {
			t.Fatal("原版守門拒絕本批正常畫面", at, receipt["reason"])
		}
		if group["source_id"].(int) != model.ID || !bytes.Equal(group["mask"].([]byte), model.Mask) || group["painted"].(int) != model.Cells {
			t.Fatal("獨立背景模型不同", at, group["source_id"], model.ID, group["painted"], model.Cells)
		}
		pixels := 0
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				if image.Pt(x/4, y/4).In(f.cursor) {
					continue
				}
				k := y/4*320 + x/4
				wanted := baseline.RGBAAt(x, y)
				if model.Mask[k>>3]&(1<<uint(k&7)) != 0 {
					wanted = p.frame.art.RGBAAt(x, y)
					pixels++
				}
				if im.RGBAAt(x, y) != wanted {
					t.Fatal("RGBA或區外保持不同", at, x, y)
				}
			}
		}
		total += pixels
		checkState(s)
		file, err := os.Create(filepath.Join(out, fmt.Sprintf("point-%03d.png", at)))
		hdNewGameNeed(t, err)
		hdNewGameNeed(t, png.Encode(file, im))
		hdNewGameNeed(t, file.Close())
		records = append(records, map[string]any{"point": at, "step": m.Steps, "source_id": model.ID, "painted": model.Cells, "rgba_pixels": pixels, "native_canvas_sha256": hash(f.canvas), "glyph_mask_sha256": hash(p.glyphMask())})
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
	if at != 89 || count != 350 || total == 0 || p.rejected != 0 {
		t.Fatal("來源範圍不同", at, count, total, p.rejected)
	}
	if !bytes.Equal(m.Mem, hdNewGameRead(t, filepath.Join(ref, "control/final.memory"))) {
		t.Fatal("終點RAM不同")
	}
	for _, frame := range p.frames {
		if (frame.id == 311 && frame.decoded != 1) || (frame.id != 311 && frame.decoded != 0) {
			t.Fatal("來源解碼次數不同", frame.id, frame.decoded)
		}
	}
	d.Close()
	if !bytes.Equal(seed, hdNewGameRead(t, filepath.Join(save, "COLONY09.SAV"))) {
		t.Fatal("改動初始存檔")
	}
	proof := map[string]any{"result": "PASS_CUSTOM_WORLD_NATIVE89_FOREGROUND_RGBA_AND_ORIGINAL_STATE", "production_connected": true, "checkpoints": at, "dos_inputs": count, "rgba_pixels": total, "original_state_and_saves_equal": true, "points": records}
	raw, err := json.MarshalIndent(proof, "", "  ")
	hdNewGameNeed(t, err)
	hdNewGameNeed(t, os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}

func TestHDCustomWorldGuards(t *testing.T) {
	game, root, assets := hdCustomWorldFixtures(t)
	h := &hdRuntime{m: golem.New()}
	p, err := loadHDNewGameRuntime(h, game, assets)
	hdNewGameNeed(t, err)
	for _, i := range []int{1, 4, 44, 84, 87} {
		var model hdNewGameModelPoint
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "native-custom-model-r4", fmt.Sprintf("point-%03d.json", i))), &model))
		f := draftNativeFrame{canvas: hdNewGameRead(t, filepath.Join(root, "native-source-r2/control", fmt.Sprintf("point-%03d.canvas", i))),
			palette: hdNewGameRead(t, filepath.Join(root, "native-source-r2/control", fmt.Sprintf("point-%03d.palette", i))), mode: 0x13}
		for k := range p.glyph {
			p.glyph[k] = model.Glyph[k>>3]&(1<<uint(k&7)) != 0
		}
		for k := range p.border {
			p.border[k] = model.Border[k>>3]&(1<<uint(k&7)) != 0
		}
		p.frames[2].decoded = 0
		p.frames[2].native = nil
		if p.selectFrame(f) != nil {
			t.Fatal("未解碼原圖仍選中")
		}
		frame := p.frames[2]
		raw := hdNewGameRead(t, filepath.Join("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels", fmt.Sprintf("%04d.idx", frame.id)))
		if hash(raw) != frame.nativeSHA {
			t.Fatal("原始索引不同")
		}
		frame.native = raw
		frame.decoded = 1
		if p.selectFrame(f) != frame {
			t.Fatal("正常畫面未選中")
		}
		for _, k := range []int{0, 319, 320, 63999} {
			bad := f
			bad.canvas = append([]byte(nil), f.canvas...)
			bad.canvas[k] ^= 1
			if p.selectFrame(bad) != nil {
				t.Fatal("改變畫面仍匹配", k)
			}
		}
		for k := 0; k < 768; k++ {
			bad := f
			bad.palette = append([]byte(nil), f.palette...)
			bad.palette[k] ^= 1
			if p.selectFrame(bad) != nil {
				t.Fatal("改變色盤仍匹配", k)
			}
		}
		for k, v := range p.glyph {
			if v {
				p.glyph[k] = false
				if p.selectFrame(f) != nil {
					t.Fatal("字形證據失效仍匹配")
				}
				p.glyph[k] = true
				break
			}
		}
		copy(h.m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000], f.canvas)
		h.m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, old, v byte) { p.memoryWrite(a, old, v) })
		for k, v := range p.glyph {
			if v {
				h.m.CPU.Seg[golem.CS] = 0x1000
				h.m.CPU.IP = 0
				h.m.CPU.Seg[golem.ES] = 0x2cae
				h.m.CPU.R[golem.DI] = uint16(k)
				h.m.CPU.R[golem.AX] = uint16(f.canvas[k])
				h.m.Mem[0x10000] = 0xaa
				hdNewGameNeed(t, h.m.Step())
				if p.glyph[k] || p.selectFrame(f) != nil {
					t.Fatal("未知同值字形寫入沒有回退")
				}
				p.glyph[k] = true
				break
			}
		}
		for k, v := range p.border {
			if v {
				h.m.CPU.Seg[golem.CS] = 0x1000
				h.m.CPU.IP = 0
				h.m.CPU.Seg[golem.ES] = 0x2cae
				h.m.CPU.R[golem.DI] = uint16(k)
				h.m.CPU.R[golem.AX] = uint16(f.canvas[k])
				h.m.Mem[0x10000] = 0xaa
				hdNewGameNeed(t, h.m.Step())
				if p.border[k] || p.selectFrame(f) != nil {
					t.Fatal("未知同值邊框寫入沒有回退")
				}
				p.border[k] = true
				break
			}
		}
		bad := f
		bad.mode = 0x12
		if p.selectFrame(bad) != nil {
			t.Fatal("錯模式仍匹配")
		}
		bad = f
		bad.canvas = f.canvas[:63999]
		if p.selectFrame(bad) != nil {
			t.Fatal("短畫布仍匹配")
		}
	}
}

func TestHDCustomWorldDecodeGuards(t *testing.T) {
	game, root, assets := hdCustomWorldFixtures(t)
	_ = root
	source := hdNewGameRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/0311.idx")
	for _, name := range []string{"full", "missing-first", "hole", "duplicate", "wrong-code", "wrong-pixel", "unknown-write"} {
		t.Run(name, func(t *testing.T) {
			m := golem.New()
			h := &hdRuntime{m: m}
			p, err := loadHDNewGameRuntime(h, game, assets)
			hdNewGameNeed(t, err)
			m.WatchWrite(0x3c500, 0x3c500+63999, func(_ *golem.Machine, a uint32, old, v byte) { p.memoryWrite(a, old, v) })
			m.CPU.Seg[golem.ES] = 0x3c50
			write := func(k int, v byte, known bool) {
				m.CPU.Seg[golem.CS] = 0x11b5
				if !known && name == "unknown-write" {
					m.CPU.Seg[golem.CS] = 0
				}
				m.CPU.IP = 0x54a
				m.CPU.R[golem.DI] = uint16(k)
				m.CPU.R[golem.AX] = uint16(v)
				code := append([]byte(nil), hdPictureWriterCodes[0x54a]...)
				if !known && name != "unknown-write" {
					code[1] ^= 1
				}
				copy(m.Mem[uint32(m.CPU.Seg[golem.CS])*16+0x54a:], code)
				hdNewGameNeed(t, m.Step())
			}
			for k, v := range source {
				if name == "missing-first" && k == 0 || name == "hole" && k == 1234 {
					continue
				}
				if name == "wrong-pixel" && k == 1234 {
					v ^= 1
				}
				write(k, v, !(name == "wrong-code" && k == 1234))
				if name == "duplicate" && k == 1234 {
					write(k, v, true)
				}
				if name == "unknown-write" && k == 1234 {
					write(k, v, false)
				}
			}
			if (p.frames[2].decoded == 1) != (name == "full") {
				t.Fatal("解碼守門不同", name, p.frames[2].decoded)
			}
			if p.frames[1].decoded != 0 {
				t.Fatal("錯認另一來源")
			}
		})
	}
}

func hdCustomWorldFixtures(t *testing.T) (string, string, string) {
	t.Helper()
	game, _, assets := hdNewGameFixtures(t)
	root := os.Getenv("TEST_CUSTOM_WORLD_ROOT")
	if root == "" {
		t.Skip("需要自訂地圖來源與模型")
	}
	return game, root, assets
}
