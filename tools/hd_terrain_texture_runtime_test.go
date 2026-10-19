package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"testing"
)

func TestHDTerrainTextureNativeR92(t *testing.T) {
	need := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	read := func(p string) []byte { t.Helper(); b, e := os.ReadFile(p); need(e); return b }
	root := os.Getenv("TEST_TERRAIN_TEXTURE_REFERENCE")
	if root == "" || os.Getenv("TEST_GAME_ROOT") == "" || os.Getenv("TEST_HD_ASSETS") == "" || os.Getenv("TEST_TERRAIN_TEXTURE_OUTPUT") == "" {
		t.Skip("需要合法原版、HD素材與R92正常路徑收據")
	}
	out := os.Getenv("TEST_TERRAIN_TEXTURE_OUTPUT")
	need(os.Mkdir(out, 0755))
	scratch := filepath.Join(out, "saves")
	need(os.Mkdir(scratch, 0755))
	seed := read("/repo/workplace/reports/goal186-display-hd/hd-building032-draw-boundary-20261012/lifecycle-r29-r1/gui/save/COLONY09.SAV")
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("seed")
	}
	need(os.WriteFile(filepath.Join(scratch, "COLONY09.SAV"), seed, 0644))
	type state struct {
		Steps, Cycles uint64
		Count         uint64 `json:"dos_input_count"`
		Memory        string `json:"memory_sha256"`
		Indexed       string `json:"indexed_sha256"`
		Palette       string `json:"palette_sha256"`
		Registers     [8]uint16
		Segments      [4]uint16
		IP, Flags     uint16
	}
	var oracle struct {
		Checkpoints []state
		End         state
	}
	need(json.Unmarshal(read(filepath.Join(root, "r92-native-terrain-r4/control/draws.json")), &oracle))
	var replay struct {
		Inputs []windowInput
		End    uint64
	}
	raw := read(filepath.Join(root, "r92-terrain-baseline-gui-r1/gui.inputs.json"))
	if hash(raw) != "25588f8815e88714d7fac797235b3dcd579ea790b53bb8931f20d295fd5d2f54" {
		t.Fatal("inputs")
	}
	need(json.Unmarshal(raw, &replay))
	if len(oracle.Checkpoints) != 23 || len(replay.Inputs) != 119 || replay.End != 259600000 {
		t.Fatal("range")
	}
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(os.Getenv("TEST_GAME_ROOT"), "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, os.Getenv("TEST_GAME_ROOT"))
	d.Scratch = scratch
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("digital")
	}
	m.EnableOPLSynth(true)
	h := &hdRuntime{m: m}
	p, e := loadHDTerrainTextureRuntime(h, os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"))
	need(e)
	m.SetBeforeInstruction(func() {
		if m.Steps == 16715359 {
			need(os.WriteFile(filepath.Join(out, "entry-1477.memory"), m.Mem, 0644))
			a, e := json.Marshal(map[string]any{"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags, "steps": m.Steps})
			need(e)
			need(os.WriteFile(filepath.Join(out, "entry-1477.state.json"), a, 0644))
		}
		p.beforeInstruction()
	})
	check := func(s state) {
		t.Helper()
		c := m.CPU
		if m.Steps != s.Steps || c.Cycles != s.Cycles || hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags {
			t.Fatal("original state", m.Steps, s.Steps)
		}
	}
	type cell struct {
		ID     int    `json:"source_id"`
		Local  uint16 `json:"local"`
		Native byte   `json:"native"`
		Glyph  byte   `json:"glyph_native"`
	}
	at, count, pixels := 0, uint64(0), 0
	seen := map[int]bool{}
	var records []map[string]any
	expand := func(v byte) byte { return v<<2 | v>>4 }
	clamp := func(v int) byte {
		if v < 0 {
			return 0
		}
		if v > 255 {
			return 255
		}
		return byte(v)
	}
	var cycle struct {
		Canonical [8][3]byte `json:"canonical_cycle_RGB6"`
	}
	need(json.Unmarshal(read(filepath.Join(root, "r92-terrain-palette-r1.json")), &cycle))
	arts := map[int]image.Image{}
	for n := 0; n < 12; n++ {
		im, e := png.Decode(bytes.NewReader(read(filepath.Join(os.Getenv("TEST_HD_ASSETS"), fmt.Sprintf("terrain-texture-%03d.png", n)))))
		need(e)
		arts[n] = im
	}
	capture := func() {
		if at == 23 {
			return
		}
		s := oracle.Checkpoints[at]
		if m.Steps > s.Steps || m.Steps == s.Steps && count > s.Count {
			t.Fatal("skipped", at)
		}
		if m.Steps != s.Steps || count != s.Count {
			return
		}
		check(s)
		var want, under map[int]cell
		model := filepath.Join(root, "r92-terrain-ownership-r3", fmt.Sprintf("point-%03d", at))
		need(json.Unmarshal(read(model+".terrain-owners.json"), &want))
		need(json.Unmarshal(read(model+".terrain-underlays.json"), &under))
		visible := map[int]hdTerrainTextureCell{}
		for a, c := range p.owners {
			if a >= hdBuildingCanvas && a < hdBuildingCanvas+64000 {
				visible[int(a-hdBuildingCanvas)] = c
			}
		}
		if len(visible) != len(want) || len(p.underlays) != len(under) {
			t.Fatal("owner count", at, len(visible), len(want), len(p.underlays), len(under))
		}
		for k, w := range want {
			c, ok := visible[k]
			if !ok || int(c.slot) != w.ID-1476 || c.local != w.Local || c.native != w.Native {
				t.Fatal("owner", at, k, c, w)
			}
		}
		for k, w := range under {
			u, ok := p.underlays[hdBuildingCanvas+uint32(k)]
			if !ok || int(u.cell.slot) != w.ID-1476 || u.cell.local != w.Local || u.cell.native != w.Native || u.glyph != w.Glyph {
				t.Fatal("underlay", at, k)
			}
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), step: m.Steps, mode: m.VideoMode()}
		baseline := image.NewRGBA(image.Rect(0, 0, 1280, 800))
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				v := int(f.indexed[y/4*320+x/4]) * 3
				baseline.SetRGBA(x, y, color.RGBA{expand(f.palette[v]), expand(f.palette[v+1]), expand(f.palette[v+2]), 255})
			}
		}
		im := image.NewRGBA(baseline.Bounds())
		copy(im.Pix, baseline.Pix)
		receipt := p.paint(im, f)
		supported := p.paletteSupported(f.palette)
		verified := 0
		for y := 0; y < 800; y++ {
			for x := 0; x < 1280; x++ {
				k := y/4*320 + x/4
				w, ok := want[k]
				expected := baseline.RGBAAt(x, y)
				if ok && supported {
					n := w.ID - 1477
					tx, ty := int(w.Local)%16*4+x%4, int(w.Local)/16*4+y%4
					expected = color.RGBAModel.Convert(arts[n].At((2*tx+1)*1254/128, (2*ty+1)*1254/128)).(color.RGBA)
					if w.Native >= 120 && w.Native < 128 {
						a := int(w.Native) * 3
						canonical := cycle.Canonical[w.Native-120]
						expected.R = clamp(int(expected.R) + int(expand(f.palette[a])) - int(expand(canonical[0])))
						expected.G = clamp(int(expected.G) + int(expand(f.palette[a+1])) - int(expand(canonical[1])))
						expected.B = clamp(int(expected.B) + int(expand(f.palette[a+2])) - int(expand(canonical[2])))
					}
					seen[n] = true
					verified++
				}
				if im.RGBAAt(x, y) != expected {
					t.Fatal("independent RGBA", at, x, y, im.RGBAAt(x, y), expected)
				}
			}
		}
		if verified != receipt["painted"].(int)*16 {
			t.Fatal("paint count")
		}
		pixels += verified
		bad := f
		bad.palette = append([]byte(nil), f.palette...)
		bad.palette[7*3] ^= 1
		n := image.NewRGBA(im.Bounds())
		copy(n.Pix, baseline.Pix)
		if p.paint(n, bad)["painted"] != 0 || !bytes.Equal(n.Pix, baseline.Pix) {
			t.Fatal("palette fallback")
		}
		// 每個已驗色盤旋轉都要可畫，錯誤循環必須退回原版。
		if supported {
			for shift := 0; shift < 8; shift++ {
				a := append([]byte(nil), f.palette...)
				for j := 0; j < 8; j++ {
					copy(a[(120+j)*3:(121+j)*3], cycle.Canonical[(j+shift)%8][:])
				}
				if !p.paletteSupported(a) {
					t.Fatal("cycle", shift)
				}
				a[120*3] ^= 1
				if p.paletteSupported(a) {
					t.Fatal("invalid cycle", shift)
				}
			}
		}
		// 不改原始PNG；畫面才以原版游標遮罩保持前景。
		if source, ok := h.cursorSource(); ok {
			for y := f.cursor.Min.Y; y < f.cursor.Max.Y; y++ {
				for x := f.cursor.Min.X; x < f.cursor.Max.X; x++ {
					if x < 0 || y < 0 || x >= 320 || y >= 200 || source[(y-f.cursor.Min.Y)*16+x-f.cursor.Min.X] == 255 {
						continue
					}
					for j := 0; j < 4; j++ {
						for i := 0; i < 4; i++ {
							im.SetRGBA(x*4+i, y*4+j, baseline.RGBAAt(x*4+i, y*4+j))
						}
					}
				}
			}
		}
		name := filepath.Join(out, fmt.Sprintf("point-%03d", at))
		file, e := os.Create(name + ".png")
		need(e)
		need(png.Encode(file, im))
		need(file.Close())
		file, e = os.Create(name + ".original.png")
		need(e)
		need(png.Encode(file, baseline))
		need(file.Close())
		receipt["step"], receipt["point"], receipt["verified_component_rgba"] = m.Steps, at, verified
		records = append(records, receipt)
		fmt.Println("R92_COMPONENT_POINT", at, "RGBA", verified, "palette", supported)
		check(s)
		at++
	}
	step := func() { capture(); need(m.Step()) }
	for _, e := range replay.Inputs {
		for m.Steps < e.Step {
			step()
		}
		capture()
		applyWindowInput(d, e)
		count++
		capture()
	}
	for m.Steps < replay.End {
		step()
	}
	capture()
	check(oracle.End)
	if at != 23 || count != 119 || p.accepted != 12 || p.rejected != 0 || len(seen) != 12 {
		t.Fatal("coverage", at, count, p.accepted, p.rejected, len(seen))
	}
	if !bytes.Equal(m.Mem, read(filepath.Join(root, "r92-native-terrain-r4/control/final.memory"))) {
		t.Fatal("final RAM")
	}
	d.Close()
	controlSaves := filepath.Join(root, "r92-native-terrain-r4/control/saves")
	entries, e := os.ReadDir(controlSaves)
	need(e)
	actual, e := os.ReadDir(scratch)
	need(e)
	if len(entries) != len(actual) {
		t.Fatal("save inventory")
	}
	for _, entry := range entries {
		name := entry.Name()
		if !bytes.Equal(read(filepath.Join(scratch, name)), read(filepath.Join(controlSaves, name))) {
			t.Fatal("save", name)
		}
	}
	result := map[string]any{"result": "PASS_HD_TERRAIN_TEXTURE_NATIVE_R92_COMPONENT", "production_connected": false, "normal_points": 23, "actual_inputs": 119, "end": replay.End, "accepted": p.accepted, "rejected": p.rejected, "all12_generated_sources_visible": true, "component_rgba_pixels": pixels, "CPU_RAM_IDX_DAC_cycles_saves_equal": true, "full_formal_HD_GUI_credit": false, "points": records}
	raw, e = json.MarshalIndent(result, "", "  ")
	need(e)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644))
}
