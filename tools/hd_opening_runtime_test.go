package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	golem "github.com/wicanr2/dosgolem"
)

func hdOpeningFixtures(t *testing.T) (string, string, string) {
	t.Helper()
	g, a, r := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_HD_OPENING_ROOT")
	if g == "" || a == "" || r == "" {
		t.Skip("需要合法原版、生成素材與開場獨立模型")
	}
	for _, n := range []string{"OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK", "OPENSHIP.SS", "OPENSUN.SS", "OPENWND1.SS", "OPENWND2.SS", "OPENMON1.SS", "OPENMON2.SS"} {
		if _, e := os.Stat(filepath.Join(g, n)); os.IsNotExist(e) {
			t.Skip("缺合法原版", n)
		}
	}
	return g, a, r
}
func hdOpeningRead(t *testing.T, p string) []byte {
	t.Helper()
	b, e := os.ReadFile(p)
	if e != nil {
		t.Fatal(e)
	}
	return b
}
func hdOpeningOwners(t *testing.T, p *hdOpeningRuntime, raw []byte) {
	t.Helper()
	if len(raw) != 64000*6 {
		t.Fatal("來源模型長度")
	}
	for i := range p.cells {
		a := i * 6
		p.cells[i] = hdOpeningCell{raw[a], binary.LittleEndian.Uint32(raw[a+1 : a+5]), raw[a+5]}
	}
}

func TestHDOpeningNormalSources(t *testing.T) {
	game, assets, root := hdOpeningFixtures(t)
	output := os.Getenv("TEST_HD_OPENING_OUTPUT")
	if output == "" {
		t.Skip("需要新的本機輸出")
	}
	if e := os.Mkdir(output, 0755); e != nil {
		t.Fatal(e)
	}
	for _, route := range []struct{ name, ref string }{{"native80", "opening-source-model-r8-observed"}, {"exit112", "opening-source-model-r10-observed"}} {
		t.Run(route.name, func(t *testing.T) {
			ref := filepath.Join(root, route.ref)
			var oracle struct {
				End    uint64
				Points []struct {
					Step      uint64
					Memory    string `json:"memory_sha256"`
					Indexed   string `json:"indexed_sha256"`
					Palette   string `json:"palette_sha256"`
					Registers [8]uint16
					Segments  [4]uint16
					IP, Flags uint16
					Cycles    uint64
				}
				Inputs []windowInput
			}
			if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "check.json")), &oracle); e != nil {
				t.Fatal(e)
			}
			var model struct {
				Points []struct {
					Step      uint64
					Owners    map[string]int
					Paintable bool
					Reason    string `json:"guard_reason"`
					File      string `json:"owners_file"`
					MapValid  bool   `json:"map_valid"`
				}
			}
			if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "model.json")), &model); e != nil {
				t.Fatal(e)
			}
			if len(model.Points) != len(oracle.Points) || len(model.Points) < 80 {
				t.Fatal("獨立模型範圍")
			}
			m := golem.New()
			if e := m.LoadEXE(hdOpeningRead(t, filepath.Join(game, "OPENING.EXE"))); e != nil {
				t.Fatal(e)
			}
			m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
			m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
			d := golem.NewDOS(m, game)
			d.Scratch = filepath.Join(output, route.name)
			if e := os.Mkdir(d.Scratch, 0755); e != nil {
				t.Fatal(e)
			}
			d.Install()
			defer d.Close()
			m.SetSoundBlasterPro(true)
			if !m.EnableSBDigital() {
				t.Fatal("缺數位音訊")
			}
			m.EnableOPLSynth(true)
			h := &hdRuntime{m: m}
			p, e := loadHDOpeningRuntime(h, game, assets)
			if e != nil {
				t.Fatal(e)
			}
			h.opening = p
			at, inputAt := 0, 0
			records := []map[string]any{}
			for m.Steps < oracle.End {
				for inputAt < len(oracle.Inputs) && oracle.Inputs[inputAt].Step == m.Steps {
					applyWindowInput(d, oracle.Inputs[inputAt])
					inputAt++
				}
				if at < len(oracle.Points) && oracle.Points[at].Step == m.Steps {
					s, expected := oracle.Points[at], model.Points[at]
					c := m.CPU
					if hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
						t.Fatal("觀測改變原版狀態", m.Steps)
					}
					f := draftNativeFrame{indexed: m.Indexed(), palette: m.DAC[:], mode: m.VideoMode(), step: m.Steps}
					out := draftRGB(f.indexed, f.palette)
					before := hash(m.Mem)
					receipt := p.paint(out, f)
					if hash(m.Mem) != before {
						t.Fatal("顯示改寫原版")
					}
					counts := map[string]int{}
					for _, v := range p.cells {
						if v.kind != 0 {
							counts[fmt.Sprint(v.kind)]++
						}
					}
					if counts["1"] != expected.Owners["1"] || counts["2"] != expected.Owners["2"] || p.mapValid != expected.MapValid {
						t.Fatal("來源模型不符", m.Steps, counts, expected.Owners)
					}
					if expected.Paintable {
						if receipt["painted"] != counts["1"]+counts["2"] {
							t.Fatal("來源繪製數量", receipt)
						}
					} else if receipt["painted"] != 0 || receipt["reason"] != expected.Reason {
						t.Fatal("回退判準", m.Steps, receipt, expected.Reason)
					}
					if expected.File != "" {
						raw := hdOpeningRead(t, filepath.Join(ref, expected.File))
						if len(raw) != 64000*6 {
							t.Fatal("模型長度")
						}
						for i, v := range p.cells {
							a := i * 6
							want := hdOpeningCell{raw[a], binary.LittleEndian.Uint32(raw[a+1 : a+5]), raw[a+5]}
							if v != want {
								t.Fatal("逐格來源不同", m.Steps, i, v, want)
							}
						}
						file := filepath.Join(d.Scratch, fmt.Sprintf("point-%08d.png", m.Steps))
						f, e := os.Create(file)
						if e != nil {
							t.Fatal(e)
						}
						if e = png.Encode(f, out); e != nil {
							t.Fatal(e)
						}
						if e = f.Close(); e != nil {
							t.Fatal(e)
						}
					}
					records = append(records, map[string]any{"step": m.Steps, "opening": receipt})
					at++
				}
				if e := m.Step(); e != nil {
					t.Fatal(e)
				}
			}
			if at != len(model.Points) || inputAt != len(oracle.Inputs) || p.mapBirths != 1 || p.borderBirths != 1 || p.sameValueRevoked == 0 {
				t.Fatal("正常路徑或來源不足")
			}
			if route.name == "exit112" && p.retired != 1 {
				t.Fatal("退場來源未清除")
			}
			raw, e := json.MarshalIndent(map[string]any{"result": "PASS_OPENING_NORMAL_NATIVE_SOURCES", "points": at, "inputs": inputAt, "end": m.Steps, "records": records, "retirements": p.retired}, "", "  ")
			if e != nil {
				t.Fatal(e)
			}
			if e = os.WriteFile(filepath.Join(d.Scratch, "check.json"), append(raw, '\n'), 0644); e != nil {
				t.Fatal(e)
			}
		})
	}
}

func hdOpeningGuardState(t *testing.T) (*hdOpeningRuntime, draftNativeFrame) {
	t.Helper()
	game, assets, root := hdOpeningFixtures(t)
	m := golem.New()
	h := &hdRuntime{m: m}
	p, e := loadHDOpeningRuntime(h, game, assets)
	if e != nil {
		t.Fatal(e)
	}
	ref := filepath.Join(root, "opening-source-model-r8-observed")
	copy(m.Mem, hdOpeningRead(t, filepath.Join(ref, "point-05200000.memory")))
	p.native[0] = bytes.Clone(m.Mem[hdOpeningMain : hdOpeningMain+64000])
	// 邊框已被長圖覆蓋；原始IDX仍須由合法解碼輸入提供。
	decoded := os.Getenv("TEST_HD_DECODED")
	if decoded == "" {
		t.Skip("需要合法原始IDX")
	}
	p.native[0] = hdOpeningRead(t, filepath.Join(decoded, "1092.idx"))
	p.native[1] = hdOpeningRead(t, filepath.Join(decoded, "1179.idx"))
	p.mapValid = true
	hdOpeningOwners(t, p, hdOpeningRead(t, filepath.Join(ref, "model-05200000.owners")))
	f := draftNativeFrame{indexed: hdOpeningRead(t, filepath.Join(ref, "point-05200000.idx")), palette: hdOpeningRead(t, filepath.Join(ref, "point-05200000.palette")), mode: 0x13, step: 5200000}
	if r := p.paint(draftRGB(f.indexed, f.palette), f); r["painted"] != 63488 {
		t.Fatal("缺正向副本", r)
	}
	return p, f
}
func TestHDOpeningPaintGuards(t *testing.T) {
	for _, name := range []string{"code", "mode", "main", "vga", "dac", "ram-palette", "source-local", "source-value", "unknown-same-main", "unknown-same-map"} {
		t.Run(name, func(t *testing.T) {
			p, f := hdOpeningGuardState(t)
			m := p.h.m
			expected := 0
			switch name {
			case "code":
				m.Mem[0x5570+0x9f+31] ^= 1
			case "mode":
				f.mode = 3
			case "main":
				m.Mem[hdOpeningMain+10] ^= 1
			case "vga":
				m.Mem[0xa0000+10] ^= 1
			case "dac":
				f.palette[1] ^= 1
			case "ram-palette":
				m.Mem[0xafc00+1] ^= 1
			case "source-local":
				p.cells[10].local = 126720
			case "source-value":
				p.cells[10].value ^= 1
			case "unknown-same-main":
				p.write(hdOpeningMain+10, m.Mem[hdOpeningMain+10], m.Mem[hdOpeningMain+10])
				expected = 63487
				if p.cells[10].kind != 0 || p.sameValueRevoked == 0 {
					t.Fatal("同值未知來源未撤銷")
				}
			case "unknown-same-map":
				p.write(hdOpeningMap, m.Mem[hdOpeningMap], m.Mem[hdOpeningMap])
				expected = 63488
				if p.mapValid {
					t.Fatal("長圖同值未知寫入仍可移交")
				}
			}
			before := hash(m.Mem)
			r := p.paint(draftRGB(f.indexed, f.palette), f)
			if r["painted"] != expected || hash(m.Mem) != before {
				t.Fatal("守門或唯讀性", r)
			}
			if name == "code" {
				for _, c := range p.cells {
					if c.kind != 0 {
						t.Fatal("退場殘留來源")
					}
				}
			}
		})
	}
}
func TestHDOpeningMapCopyGuards(t *testing.T) {
	for _, name := range []string{"last-local", "wrong-code", "df", "invalid-source", "wrong-value", "invalid-map", "segment-crossing"} {
		t.Run(name, func(t *testing.T) {
			p, _ := hdOpeningGuardState(t)
			m := p.h.m
			pos := 1234
			src := hdOpeningMap + 126718
			copy(m.Mem[0x3bd0+0xc8:], hdOpeningSignature[:16])
			m.CPU.Seg[golem.CS] = 0x3bd
			m.CPU.IP = 0xc8
			m.CPU.Seg[golem.DS] = uint16(src >> 4)
			m.CPU.R[golem.SI] = uint16(src & 15)
			m.CPU.Seg[golem.ES] = uint16(hdOpeningMain >> 4)
			m.CPU.R[golem.DI] = uint16(pos)
			m.CPU.R[golem.CX] = 1
			m.CPU.Flags &^= 0x400
			switch name {
			case "wrong-code":
				m.Mem[0x3bd0+0xc8+15] ^= 1
			case "df":
				m.CPU.Flags |= 0x400
			case "invalid-source":
				m.CPU.Seg[golem.DS] = 0x6000
			case "wrong-value":
				m.Mem[src] ^= 1
				m.Mem[src+1] ^= 1
			case "invalid-map":
				p.mapValid = false
			case "segment-crossing":
				m.CPU.Seg[golem.DS] = uint16((src - 65535) >> 4)
				m.CPU.R[golem.SI] = 65535
			}
			if e := m.Step(); e != nil {
				t.Fatal(e)
			}
			if name == "last-local" {
				if p.cells[pos].kind != 2 || p.cells[pos+1].local != 126719 {
					t.Fatal("長圖高位索引截斷", p.cells[pos], p.cells[pos+1])
				}
			} else if name == "segment-crossing" {
				if p.cells[pos].kind != 2 || p.cells[pos+1].kind != 0 {
					t.Fatal("段界限逐byte守門", p.cells[pos], p.cells[pos+1])
				}
			} else if p.cells[pos].kind != 0 || p.cells[pos+1].kind != 0 {
				t.Fatal("錯誤來源取得所有權", name)
			}
		})
	}
}

func TestHDOpeningDecodeGuards(t *testing.T) {
	for _, name := range []string{"complete", "wrong-code", "gap", "wrong-full-hash", "same-value-invalidation"} {
		t.Run(name, func(t *testing.T) {
			p, _ := hdOpeningGuardState(t)
			m := p.h.m
			p.mapValid = false
			p.mapNext = 126719
			target := hdOpeningMap + 126719
			copy(m.Mem[0xac20+0x550:], []byte{0xaa, 0xe2, 0xfa, 0xeb, 0x8f, 0xac, 0x0a, 0xc0, 0x74, 0x32, 0x3c, 1, 0x74, 5, 0x8a, 0xc8})
			m.CPU.Seg[golem.CS] = 0xac2
			m.CPU.IP = 0x550
			m.CPU.Seg[golem.ES] = uint16(target >> 4)
			m.CPU.R[golem.DI] = uint16(target & 15)
			m.CPU.R[golem.AX] = uint16(p.native[1][126719])
			m.CPU.Flags &^= 0x400
			switch name {
			case "wrong-code":
				m.Mem[0xac20+0x550+15] ^= 1
			case "gap":
				p.mapNext--
			case "wrong-full-hash":
				m.Mem[hdOpeningMap+100] ^= 1
			}
			if e := m.Step(); e != nil {
				t.Fatal(e)
			}
			if name == "complete" || name == "same-value-invalidation" {
				if !p.mapValid || p.mapBirths != 1 {
					t.Fatal("完整來源未授權")
				}
			} else if p.mapValid || p.mapBirths != 0 {
				t.Fatal("不完整來源取得授權")
			}
			if name == "same-value-invalidation" {
				m.CPU.Seg[golem.CS] = 0
				m.CPU.IP = 0
				if e := m.Step(); e != nil {
					t.Fatal(e)
				}
				p.write(hdOpeningMap, m.Mem[hdOpeningMap], m.Mem[hdOpeningMap])
				if p.mapValid {
					t.Fatal("同值來源寫入未失效")
				}
			}
		})
	}
}

func TestHDOpeningCursorSourceBackground(t *testing.T) {
	for _, name := range []string{"known", "unknown-cell", "invalid-palette", "exit"} {
		t.Run(name, func(t *testing.T) {
			p, f := hdOpeningGuardState(t)
			f.cursor = image.Rect(160, 100, 176, 116)
			want := 256
			switch name {
			case "unknown-cell":
				p.cells[100*320+160] = hdOpeningCell{}
				want--
			case "invalid-palette":
				f.palette[1] ^= 1
				want = 0
			case "exit":
				p.h.m.Mem[0x5570+0x9f+31] ^= 1
				want = 0
			}
			original := draftRGB(f.indexed, f.palette)
			before := bytes.Clone(original.Pix)
			memory := hash(p.h.m.Mem)
			r := p.paintWithin(original, f, f.cursor)
			if r["painted"] != want || hash(p.h.m.Mem) != memory {
				t.Fatal("滑鼠框來源不符", r)
			}
			for y := 0; y < 800; y++ {
				for x := 0; x < 1280; x++ {
					if !image.Pt(x/4, y/4).In(f.cursor) {
						at := (y*1280 + x) * 4
						if !bytes.Equal(original.Pix[at:at+4], before[at:at+4]) {
							t.Fatal("框外像素改變")
						}
					}
				}
			}
		})
	}
}

func TestHDOpeningCacheInputs(t *testing.T) {
	for _, at := range []uint32{hdOpeningMain + 77*320 + 218, 0x5570 + 0x9f + 31, 0xafc00} {
		p, _ := hdOpeningGuardState(t)
		p.h.opening = p
		before := p.h.key()
		p.h.m.Mem[at] ^= 1
		if before == p.h.key() {
			t.Fatal("開場守門輸入未進快取鍵", at)
		}
	}
}

func TestHDOpeningAssetRejection(t *testing.T) {
	game, assets, _ := hdOpeningFixtures(t)
	if _, e := loadHDOpeningRuntime(&hdRuntime{m: golem.New()}, game, assets); e != nil {
		t.Fatal("valid opening fixture", e)
	}
	files := []string{"opening-fish-clear-000.png", "OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK", "OPENSHIP.SS", "OPENSUN.SS", "OPENWND1.SS", "OPENWND2.SS", "OPENMON1.SS", "OPENMON2.SS"}
	for _, d := range hdOpeningDefinitions {
		files = append(files, d.asset)
	}
	for _, d := range hdOpeningSpriteDefinitions {
		files = append(files, d.asset)
	}
	for _, name := range files {
		for _, kind := range []string{"missing", "wrong", "symlink"} {
			t.Run(kind+"/"+name, func(t *testing.T) {
				g, a := t.TempDir(), t.TempDir()
				for _, f := range []string{"OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK", "OPENSHIP.SS", "OPENSUN.SS", "OPENWND1.SS", "OPENWND2.SS", "OPENMON1.SS", "OPENMON2.SS"} {
					if e := os.WriteFile(filepath.Join(g, f), hdOpeningRead(t, filepath.Join(game, f)), 0644); e != nil {
						t.Fatal(e)
					}
				}
				for _, f := range hdOpeningDefinitions {
					if e := os.WriteFile(filepath.Join(a, f.asset), hdOpeningRead(t, filepath.Join(assets, f.asset)), 0644); e != nil {
						t.Fatal(e)
					}
				}
				for _, f := range hdOpeningSpriteDefinitions {
					if e := os.WriteFile(filepath.Join(a, f.asset), hdOpeningRead(t, filepath.Join(assets, f.asset)), 0644); e != nil {
						t.Fatal(e)
					}
				}
				if e := os.WriteFile(filepath.Join(a, "opening-fish-clear-000.png"), hdOpeningRead(t, filepath.Join(assets, "opening-fish-clear-000.png")), 0644); e != nil {
					t.Fatal(e)
				}
				target, original := filepath.Join(a, name), filepath.Join(assets, name)
				if filepath.Ext(name) != ".png" {
					target, original = filepath.Join(g, name), filepath.Join(game, name)
				}
				if e := os.Remove(target); e != nil {
					t.Fatal(e)
				}
				switch kind {
				case "wrong":
					if e := os.WriteFile(target, []byte("wrong"), 0644); e != nil {
						t.Fatal(e)
					}
				case "symlink":
					if e := os.Symlink(original, target); e != nil {
						t.Fatal(e)
					}
				}
				m := golem.New()
				before := hash(m.Mem)
				p, e := loadHDOpeningRuntime(&hdRuntime{m: m}, g, a)
				if e == nil || p != nil || hash(m.Mem) != before {
					t.Fatal("錯誤資源未關閉", name, kind, e)
				}
			})
		}
	}
}

func TestHDOpeningSpritesNormalSources(t *testing.T) {
	game, assets, _ := hdOpeningFixtures(t)
	root, output := os.Getenv("TEST_HD_OPENING_SPRITES_ROOT"), os.Getenv("TEST_HD_OPENING_SPRITES_OUTPUT")
	if root == "" || output == "" {
		t.Skip("需要開場八幀獨立模型與新的輸出")
	}
	if e := os.Mkdir(output, 0755); e != nil {
		t.Fatal(e)
	}
	for _, route := range []string{"cold", "exit"} {
		t.Run(route, func(t *testing.T) {
			ref := filepath.Join(root, "opening-actor-public-r6-"+route)
			var oracle struct {
				End    uint64
				Inputs []windowInput
				Points []struct {
					Step      uint64
					Memory    string `json:"memory_sha256"`
					Indexed   string `json:"indexed_sha256"`
					Palette   string `json:"palette_sha256"`
					Registers [8]uint16
					Segments  [4]uint16
					IP, Flags uint16
					Cycles    uint64
				}
			}
			if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "check.json")), &oracle); e != nil {
				t.Fatal(e)
			}
			var model struct {
				Points []struct {
					Step  uint64
					Live  bool   `json:"live_code"`
					Actor string `json:"published_actor_file"`
					PIC   string `json:"published_pic_file"`
					Main  string `json:"owners_file"`
				}
				Calls []struct {
					Verified bool
					Ordinal  int
				}
				VerifiedCalls uint64 `json:"verified_calls"`
			}
			if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "actors.json")), &model); e != nil {
				t.Fatal(e)
			}
			if len(model.Points) != len(oracle.Points) || len(model.Points) < 80 {
				t.Fatal("獨立模型範圍")
			}
			m := golem.New()
			if e := m.LoadEXE(hdOpeningRead(t, filepath.Join(game, "OPENING.EXE"))); e != nil {
				t.Fatal(e)
			}
			m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
			m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
			d := golem.NewDOS(m, game)
			d.Scratch = filepath.Join(output, route)
			if e := os.Mkdir(d.Scratch, 0755); e != nil {
				t.Fatal(e)
			}
			d.Install()
			defer d.Close()
			m.SetSoundBlasterPro(true)
			if !m.EnableSBDigital() {
				t.Fatal("缺數位音訊")
			}
			m.EnableOPLSynth(true)
			h := &hdRuntime{m: m}
			p, e := loadHDOpeningRuntime(h, game, assets)
			if e != nil {
				t.Fatal(e)
			}
			h.opening = p
			s := p.sprites
			m.SetBeforeInstruction(s.beforeInstruction)
			at, inputAt := 0, 0
			records := []map[string]any{}
			selected := map[int]bool{}
			pngCount := 0
			transient := false
			for m.Steps < oracle.End {
				for inputAt < len(oracle.Inputs) && oracle.Inputs[inputAt].Step == m.Steps {
					applyWindowInput(d, oracle.Inputs[inputAt])
					inputAt++
				}
				if at < len(oracle.Points) && oracle.Points[at].Step == m.Steps {
					want, owners := oracle.Points[at], model.Points[at]
					c := m.CPU
					if hash(m.Mem) != want.Memory || hash(m.Indexed()) != want.Indexed || hash(m.DAC[:]) != want.Palette || c.R != want.Registers || c.Seg != want.Segments || c.IP != want.IP || c.Flags != want.Flags || c.Cycles != want.Cycles {
						t.Fatal("來源觀測改變原版", m.Steps)
					}
					f := draftNativeFrame{indexed: m.Indexed(), palette: m.DAC[:], mode: m.VideoMode(), step: m.Steps}
					out := draftRGB(f.indexed, f.palette)
					before := hash(m.Mem)
					receipt := s.paintWithin(out, f, image.Rect(0, 0, 320, 200))
					if hash(m.Mem) != before {
						t.Fatal("顯示寫入原版")
					}
					pic := hdOpeningRead(t, filepath.Join(ref, owners.PIC))
					actor := hdOpeningRead(t, filepath.Join(ref, owners.Actor))
					main := hdOpeningRead(t, filepath.Join(ref, owners.Main))
					if len(pic) != 64000*6 || len(actor) != 64000*12 || len(main) != 64000*12 {
						t.Fatal("模型長度")
					}
					for i, v := range s.pictures {
						a := i * 6
						expected := hdOpeningCell{pic[a], binary.LittleEndian.Uint32(pic[a+1 : a+5]), pic[a+5]}
						if v != expected {
							t.Fatal("發布PIK來源不同", m.Steps, i, v, expected)
						}
						for _, pair := range []struct {
							cell hdOpeningSpriteCell
							raw  []byte
						}{{s.published[i], actor}, {s.cells[i], main}} {
							a = i * 12
							b := pair.raw
							expected := hdOpeningSpriteCell{binary.LittleEndian.Uint16(b[a : a+2]), binary.LittleEndian.Uint16(b[a+2 : a+4]), b[a+4], hdOpeningCell{b[a+6], binary.LittleEndian.Uint32(b[a+7 : a+11]), b[a+11]}}
							if pair.cell != expected {
								t.Fatal("船格來源不同", m.Steps, i, pair.cell, expected)
							}
						}
					}
					frames, _ := receipt["frames"].([8]int)
					save := false
					for i, n := range frames {
						if n == 512 && !selected[i] {
							selected[i] = true
							save = true
						}
					}
					if route == "cold" && m.Steps == 14000000 {
						if receipt["sprite_painted"] != 512 || frames[6] != 512 || bytes.Equal(m.Mem[hdOpeningMain:hdOpeningMain+64000], f.indexed) {
							t.Fatal("重畫瞬間錯誤", receipt)
						}
						save = true
						transient = true
					}
					if route == "cold" && (m.Steps == 4800000 || m.Steps == 5000000) || route == "exit" && (m.Steps == 10200000 || m.Steps == 10600000 || m.Steps == 11200000 || m.Steps == 13400000 || m.Steps == 22200000) {
						save = true
					}
					file := ""
					if save {
						file = fmt.Sprintf("point-%08d.png", m.Steps)
						fd, e := os.Create(filepath.Join(d.Scratch, file))
						if e != nil {
							t.Fatal(e)
						}
						if e = png.Encode(fd, out); e != nil {
							t.Fatal(e)
						}
						if e = fd.Close(); e != nil {
							t.Fatal(e)
						}
						pngCount++
					}
					records = append(records, map[string]any{"step": m.Steps, "opening": receipt, "image": file})
					at++
				}
				if e := m.Step(); e != nil {
					t.Fatal(e)
				}
			}
			if s.accepted != model.VerifiedCalls || s.rejected != 0 || at != len(model.Points) || inputAt != len(oracle.Inputs) {
				t.Fatal("原版繪製不完整", s.accepted, s.rejected, model.VerifiedCalls)
			}
			if route == "cold" && (!transient || len(selected) != 8) {
				t.Fatal("八幀或重畫瞬間缺項")
			}
			if route == "exit" && s.sameVGA == 0 {
				t.Fatal("缺同值撤銷正例")
			}
			raw, e := json.MarshalIndent(map[string]any{"result": "PASS_OPENING_SHIP_NORMAL_PUBLISHED_SOURCES", "points": at, "inputs": inputAt, "end": m.Steps, "records": records, "images": pngCount, "accepted": s.accepted, "rejected": s.rejected, "same_value_vga_revocations": s.sameVGA}, "", "  ")
			if e != nil {
				t.Fatal(e)
			}
			if e = os.WriteFile(filepath.Join(d.Scratch, "check.json"), append(raw, '\n'), 0644); e != nil {
				t.Fatal(e)
			}
		})
	}
}
func hdOpeningSpritesGuardState(t *testing.T) (*hdOpeningSpriteRuntime, draftNativeFrame) {
	t.Helper()
	game, assets, _ := hdOpeningFixtures(t)
	root := os.Getenv("TEST_HD_OPENING_SPRITES_ROOT")
	if root == "" {
		t.Skip("需要獨立八幀模型")
	}
	m := golem.New()
	p, e := loadHDOpeningRuntime(&hdRuntime{m: m}, game, assets)
	if e != nil {
		t.Fatal(e)
	}
	s := p.sprites
	ref := filepath.Join(root, "opening-actor-public-r6-cold")
	step := uint64(14000000)
	copy(m.Mem, hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.memory", step))))
	decoded := os.Getenv("TEST_HD_DECODED")
	if decoded == "" {
		t.Skip("缺合法解碼")
	}
	p.native[0] = hdOpeningRead(t, filepath.Join(decoded, "1092.idx"))
	p.native[1] = hdOpeningRead(t, filepath.Join(decoded, "1179.idx"))
	for i := 0; i < 8; i++ {
		copy(s.native[i][:], hdOpeningRead(t, filepath.Join(decoded, fmt.Sprintf("%04d.idx", 1250+i))))
		s.nativeValid[i] = true
	}
	pic := hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("published-pik-%08d.owners", step)))
	actor := hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("published-actor-%08d.owners", step)))
	for i := range s.pictures {
		a := i * 6
		s.pictures[i] = hdOpeningCell{pic[a], binary.LittleEndian.Uint32(pic[a+1 : a+5]), pic[a+5]}
		a = i * 12
		s.published[i] = hdOpeningSpriteCell{binary.LittleEndian.Uint16(actor[a : a+2]), binary.LittleEndian.Uint16(actor[a+2 : a+4]), actor[a+4], hdOpeningCell{actor[a+6], binary.LittleEndian.Uint32(actor[a+7 : a+11]), actor[a+11]}}
	}
	f := draftNativeFrame{indexed: hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.idx", step))), palette: hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.palette", step))), mode: 0x13, step: step}
	if r := s.paintWithin(draftRGB(f.indexed, f.palette), f, image.Rect(0, 0, 320, 200)); r["painted"] != 64000 || r["sprite_painted"] != 512 {
		t.Fatal("缺完整正向副本", r)
	}
	return s, f
}
func TestHDOpeningSpritesPublishedGuards(t *testing.T) {
	for _, name := range []string{"positive-transient", "unknown-main-same", "unknown-vga-same", "code", "mode", "vga", "dac", "ram-palette", "source-id", "source-local", "source-value", "under-kind", "under-local", "under-value", "native-invalid", "cursor-clip"} {
		t.Run(name, func(t *testing.T) {
			s, f := hdOpeningSpritesGuardState(t)
			m := s.p.h.m
			pos := -1
			for i, c := range s.published {
				if c.id != 0 {
					pos = i
					break
				}
			}
			want := 64000
			bounds := image.Rect(0, 0, 320, 200)
			switch name {
			case "unknown-main-same":
				s.write(hdOpeningMain+uint32(pos), m.Mem[hdOpeningMain+uint32(pos)], m.Mem[hdOpeningMain+uint32(pos)])
			case "unknown-vga-same":
				s.publish(0xa0000+uint32(pos), f.indexed[pos], f.indexed[pos])
				want--
			case "code":
				m.Mem[0x5570+0x9f+31] ^= 1
				want = 0
			case "mode":
				f.mode = 3
				want = 0
			case "vga":
				m.Mem[0xa0000] ^= 1
				want = 0
			case "dac":
				f.palette[1] ^= 1
				want = 0
			case "ram-palette":
				m.Mem[0xafc00] ^= 1
				want = 0
			case "source-id":
				s.published[pos].id = 1258
				want = 0
			case "source-local":
				s.published[pos].local = 1175
				want = 0
			case "source-value":
				s.published[pos].value ^= 1
				want = 0
			case "under-kind":
				s.published[pos].under.kind = 3
				want = 0
			case "under-local":
				s.published[pos].under.local = 126720
				want = 0
			case "under-value":
				s.published[pos].under.value ^= 1
				want = 0
			case "native-invalid":
				s.nativeValid[6] = false
				want = 0
			case "cursor-clip":
				bounds = image.Rect(218, 77, 234, 93)
				want = 256
			}
			out := draftRGB(f.indexed, f.palette)
			original := bytes.Clone(out.Pix)
			before := hash(m.Mem)
			r := s.paintWithin(out, f, bounds)
			if r["painted"] != want || hash(m.Mem) != before {
				t.Fatal("發布守門或唯讀性", r)
			}
			if name == "unknown-vga-same" && (s.published[pos].id != 0 || s.sameVGA != 1) {
				t.Fatal("同值寫入未撤銷")
			}
			if name == "cursor-clip" {
				for y := 0; y < 800; y++ {
					for x := 0; x < 1280; x++ {
						if !image.Pt(x/4, y/4).In(bounds) {
							a := (y*1280 + x) * 4
							if !bytes.Equal(out.Pix[a:a+4], original[a:a+4]) {
								t.Fatal("游標框外改變")
							}
						}
					}
				}
			}
		})
	}
}
func TestHDOpeningSpritesSharedBody(t *testing.T) {
	game, assets, _ := hdOpeningFixtures(t)
	p, e := loadHDOpeningRuntime(&hdRuntime{m: golem.New()}, game, assets)
	if e != nil {
		t.Fatal(e)
	}
	for i := 1; i < 8; i++ {
		d := hdOpeningSpriteDefinitions[i]
		for y := 0; y < 100; y++ {
			for x := 0; x < 188; x++ {
				changed := false
				for _, r := range d.nativeRects {
					if image.Pt(x/4, y/4).In(r) {
						changed = true
						break
					}
				}
				if !changed && p.sprites.art[i].NRGBAAt(x, y) != p.sprites.art[0].NRGBAAt(x, y) {
					t.Fatal("動畫區外船身改變", i, x, y)
				}
			}
		}
	}
}

func TestHDOpeningSpritesPublicationCopyGuards(t *testing.T) {
	for _, name := range []string{"picture", "ship", "wrong-code", "df", "wrong-source", "wrong-value", "unknown-source", "segment-crossing"} {
		t.Run(name, func(t *testing.T) {
			s, _ := hdOpeningSpritesGuardState(t)
			m := s.p.h.m
			pos := 15
			if name == "ship" {
				for i, c := range s.published {
					if c.id != 0 {
						pos = i
						break
					}
				}
				s.cells[pos] = s.published[pos]
			} else {
				s.p.cells[pos] = s.pictures[pos]
				s.p.cells[pos+1] = s.pictures[pos+1]
			}
			for i := pos; i < pos+2; i++ {
				if s.cells[i].id != 0 {
					m.Mem[hdOpeningMain+uint32(i)] = s.cells[i].value
				} else {
					m.Mem[hdOpeningMain+uint32(i)] = s.p.cells[i].value
				}
			}
			m.CPU.Seg[golem.CS] = 0x557
			m.CPU.IP = 0x9f
			m.CPU.Seg[golem.DS] = 0x1c43
			m.CPU.R[golem.SI] = uint16(pos)
			m.CPU.Seg[golem.ES] = 0xa000
			m.CPU.R[golem.DI] = uint16(pos)
			m.CPU.R[golem.CX] = 1
			m.CPU.Flags &^= 0x400
			switch name {
			case "wrong-code":
				m.Mem[0x5570+0x9f+15] ^= 1
			case "df":
				m.CPU.Flags |= 0x400
			case "wrong-source":
				m.CPU.Seg[golem.DS]++
			case "wrong-value":
				m.Mem[hdOpeningMain+uint32(pos)] ^= 1
				m.Mem[hdOpeningMain+uint32(pos+1)] ^= 1
			case "unknown-source":
				s.p.cells[pos] = hdOpeningCell{}
				s.p.cells[pos+1] = hdOpeningCell{}
			case "segment-crossing":
				m.CPU.Seg[golem.DS] = uint16((int(hdOpeningMain) + pos - 65535) / 16)
				m.CPU.R[golem.SI] = 65535
			}
			if e := m.Step(); e != nil {
				t.Fatal(e)
			}
			switch name {
			case "picture":
				if s.pictures[pos].kind == 0 || s.pictures[pos+1].kind == 0 {
					t.Fatal("完整PIK未移交")
				}
			case "ship":
				if s.published[pos].id == 0 {
					t.Fatal("完整船格未移交")
				}
			case "segment-crossing":
				if s.pictures[pos].kind == 0 || s.pictures[pos+1].kind != 0 {
					t.Fatal("段界限未逐byte拒絕")
				}
			default:
				if s.pictures[pos].kind != 0 || s.pictures[pos+1].kind != 0 || s.published[pos].id != 0 {
					t.Fatal("錯誤複製取得來源", name)
				}
			}
		})
	}
}
func TestHDOpeningSpritesCompleteWriteGuards(t *testing.T) {
	for _, name := range []string{"complete", "missing", "duplicate", "transparent-write", "wrong-value", "outside"} {
		t.Run(name, func(t *testing.T) {
			s, _ := hdOpeningSpritesGuardState(t)
			s.selected = 0
			s.x, s.y = 218, 77
			s.active = true
			first, transparent := -1, -1
			for k, v := range s.native[0] {
				if v == 253 {
					transparent = k
					continue
				}
				if first < 0 {
					first = k
				}
				s.counts[k] = 1
				s.writes[k] = v
			}
			switch name {
			case "missing":
				s.counts[first] = 0
			case "duplicate":
				s.counts[first] = 2
			case "transparent-write":
				s.counts[transparent] = 1
				s.writes[transparent] = 253
			case "wrong-value":
				s.writes[first] ^= 1
			case "outside":
				s.outside = true
			}
			s.finish()
			if name == "complete" {
				if s.accepted != 1 || s.rejected != 0 {
					t.Fatal("完整原版寫入被拒絕")
				}
			} else if s.accepted != 0 || s.rejected != 1 {
				t.Fatal("不完整寫入取得來源", name)
			}
		})
	}
}

func TestHDSunVisibleIntersection(t *testing.T) {
	decoded := os.Getenv("TEST_HD_DECODED")
	if decoded == "" {
		t.Skip("需要合法原版太陽IDX")
	}
	raw := hdOpeningRead(t, filepath.Join(decoded, "1263.idx"))
	if len(raw) != 22 {
		t.Fatal("原版形狀")
	}
	for _, name := range []string{"full", "right-nine", "unseen-partial", "missing", "duplicate", "wrong-value", "offscreen-write"} {
		t.Run(name, func(t *testing.T) {
			s := &hdOpeningSpriteRuntime{p: &hdOpeningRuntime{h: &hdRuntime{m: golem.New()}}, selected: 13, x: 310, y: 121, active: true}
			if name == "full" {
				s.x = 309
			}
			for k := range s.native[13] {
				s.native[13][k] = 253
			}
			copy(s.native[13][:], raw)
			s.nativeValid[13] = name != "unseen-partial"
			first := -1
			for k, v := range raw {
				if v == 253 || s.x+k%11 >= 320 {
					continue
				}
				if first < 0 {
					first = k
				}
				s.counts[k] = 1
				s.writes[k] = v
			}
			switch name {
			case "missing":
				s.counts[first] = 0
			case "duplicate":
				s.counts[first] = 2
			case "wrong-value":
				s.writes[first] ^= 1
			case "offscreen-write":
				s.counts[21] = 1
				s.writes[21] = raw[21]
			}
			before := bytes.Clone(s.p.h.m.Mem)
			s.finish()
			if !bytes.Equal(before, s.p.h.m.Mem) {
				t.Fatal("驗證寫入原版")
			}
			count := 0
			for _, c := range s.cells {
				if c.id != 0 {
					count++
				}
			}
			if name == "full" {
				if s.accepted != 1 || count != 10 {
					t.Fatal("完整來源未接受", s.accepted, count)
				}
			} else if name == "right-nine" {
				if s.accepted != 1 || count != 9 || s.cells[123*320].id != 0 {
					t.Fatal("九格裁切不符", s.accepted, count)
				}
			} else if s.accepted != 0 || s.rejected != 1 || count != 0 {
				t.Fatal("錯誤裁切取得來源", name, s.accepted, s.rejected, count)
			}
		})
	}
}

func TestHDOpeningCaptionCursorGuards(t *testing.T) {
	cursor := image.Rect(90, 121, 106, 137)
	cases := []struct {
		name  string
		items []map[string]any
		want  bool
	}{
		{"no-items", nil, true},
		{"far-caption", []map[string]any{{"safe": image.Rect(66, 176, 253, 183)}}, true},
		{"caption-overlap", []map[string]any{{"safe": image.Rect(90, 120, 110, 140)}}, false},
		{"source-overlap", []map[string]any{{"safe": image.Rect(66, 176, 253, 183), "source_safe": image.Rect(90, 120, 110, 140)}}, false},
		{"missing-safe", []map[string]any{{"kind": "fixed"}}, false},
		{"wrong-type", []map[string]any{{"safe": "66,176,253,183"}}, false},
		{"empty-safe", []map[string]any{{"safe": image.Rectangle{}}}, false},
		{"outside-safe", []map[string]any{{"safe": image.Rect(-1, 176, 253, 183)}}, false},
		{"outside-source-safe", []map[string]any{{"safe": image.Rect(66, 176, 253, 183), "source_safe": image.Rect(0, 0, 321, 200)}}, false},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			if hdOpeningCursorUncovered(cursor, c.items) != c.want {
				t.Fatal(c.name)
			}
		})
	}
	if !hdOpeningCursorUncovered(image.Rect(310, 16, 326, 32), []map[string]any{{"safe": image.Rect(66, 176, 253, 183)}}) {
		t.Fatal("clipped cursor outside caption")
	}
}

func TestHDOpeningSpriteSlotSources(t *testing.T) {
	if len(hdOpeningSpriteDefinitions) != 98 {
		t.Fatal("source count")
	}
	for slot, d := range hdOpeningSpriteDefinitions {
		got, ok := hdOpeningSpriteSlot(uint16(d.id))
		if !ok || got != slot {
			t.Fatal("source slot", d.id, got, slot)
		}
	}
	for _, id := range []uint16{0, 1249, 1265, 1287, 65535} {
		if _, ok := hdOpeningSpriteSlot(id); ok {
			t.Fatal("unknown source accepted", id)
		}
	}
}

func TestHDWindCompleteSourceGuards(t *testing.T) {
	decoded := os.Getenv("TEST_HD_DECODED")
	if decoded == "" {
		t.Skip("需要合法原版雲煙索引資料")
	}
	for slot := 15; slot < 36; slot++ {
		d := hdOpeningSpriteDefinitions[slot]
		raw := hdOpeningRead(t, filepath.Join(decoded, fmt.Sprintf("%04d.idx", d.id)))
		if len(raw) != d.w*d.h {
			t.Fatal("native shape", d.id)
		}
		for _, name := range []string{"valid", "missing", "duplicate", "wrong-value", "unknown-write"} {
			t.Run(fmt.Sprintf("%d/%s", d.id, name), func(t *testing.T) {
				m := golem.New()
				s := &hdOpeningSpriteRuntime{p: &hdOpeningRuntime{h: &hdRuntime{m: m}}, selected: slot, x: 100, y: 50, active: true}
				first := -1
				for local, value := range raw {
					if value == 253 {
						continue
					}
					if first < 0 {
						first = local
					}
					s.counts[local], s.writes[local] = 1, value
				}
				if first < 0 {
					t.Fatal("empty source")
				}
				switch name {
				case "missing":
					s.counts[first] = 0
				case "duplicate":
					s.counts[first] = 2
				case "wrong-value":
					s.writes[first] ^= 1
				case "unknown-write":
					s.outside = true
				}
				before := bytes.Clone(m.Mem)
				s.finish()
				if !bytes.Equal(before, m.Mem) {
					t.Fatal("source check wrote native state")
				}
				if name == "valid" {
					if s.accepted != 1 || s.rejected != 0 || !s.nativeValid[slot] {
						t.Fatal("complete source rejected")
					}
					if !bytes.Equal(s.native[slot][:len(raw)], raw) {
						t.Fatal("cached source differs")
					}
				} else if s.accepted != 0 || s.rejected != 1 || s.nativeValid[slot] {
					t.Fatal("malformed source accepted")
				}
			})
		}
	}
}

func TestHDWindResourceGuards(t *testing.T) {
	game, assets, _ := hdOpeningFixtures(t)
	artCopy := filepath.Join(t.TempDir(), "graphics")
	gameCopy := filepath.Join(t.TempDir(), "game")
	if e := os.Mkdir(artCopy, 0755); e != nil {
		t.Fatal(e)
	}
	if e := os.Mkdir(gameCopy, 0755); e != nil {
		t.Fatal(e)
	}
	entries, e := os.ReadDir(assets)
	if e != nil {
		t.Fatal(e)
	}
	for _, entry := range entries {
		if entry.IsDir() {
			t.Fatal("unexpected asset directory")
		}
		raw := hdOpeningRead(t, filepath.Join(assets, entry.Name()))
		if e := os.WriteFile(filepath.Join(artCopy, entry.Name()), raw, 0644); e != nil {
			t.Fatal(e)
		}
	}
	for _, name := range []string{"OPENSHIP.SS", "OPENSUN.SS", "OPENWND1.SS", "OPENWND2.SS", "OPENMON1.SS", "OPENMON2.SS"} {
		raw := hdOpeningRead(t, filepath.Join(game, name))
		if e := os.WriteFile(filepath.Join(gameCopy, name), raw, 0644); e != nil {
			t.Fatal(e)
		}
	}
	initial, e := loadHDOpeningRuntime(&hdRuntime{m: golem.New()}, game, artCopy)
	if e != nil {
		t.Fatal("valid complete opening fixture", e)
	}
	load := func() error {
		p := initial
		_, e := loadHDOpeningSprites(p, gameCopy, artCopy)
		return e
	}
	if e := load(); e != nil {
		t.Fatal("valid fixture", e)
	}
	for slot := 15; slot < 36; slot++ {
		d := hdOpeningSpriteDefinitions[slot]
		path := filepath.Join(artCopy, d.asset)
		original := hdOpeningRead(t, path)
		for _, kind := range []string{"missing", "corrupt", "symlink"} {
			t.Run(d.asset+"/"+kind, func(t *testing.T) {
				if e := os.Remove(path); e != nil {
					t.Fatal(e)
				}
				switch kind {
				case "corrupt":
					bad := bytes.Clone(original)
					bad[len(bad)-1] ^= 1
					if e := os.WriteFile(path, bad, 0644); e != nil {
						t.Fatal(e)
					}
				case "symlink":
					if e := os.Symlink(filepath.Join(assets, d.asset), path); e != nil {
						t.Fatal(e)
					}
				}
				if e := load(); e == nil {
					t.Error("invalid asset accepted")
				}
				if kind != "missing" {
					if e := os.Remove(path); e != nil {
						t.Fatal(e)
					}
				}
				if e := os.WriteFile(path, original, 0644); e != nil {
					t.Fatal(e)
				}
				if !bytes.Equal(hdOpeningRead(t, filepath.Join(assets, d.asset)), original) {
					t.Fatal("original asset changed")
				}
			})
		}
	}
	for _, name := range []string{"OPENWND1.SS", "OPENWND2.SS"} {
		path := filepath.Join(gameCopy, name)
		original := hdOpeningRead(t, path)
		for _, kind := range []string{"missing", "corrupt", "symlink"} {
			t.Run(name+"/"+kind, func(t *testing.T) {
				if e := os.Remove(path); e != nil {
					t.Fatal(e)
				}
				switch kind {
				case "corrupt":
					bad := bytes.Clone(original)
					bad[len(bad)-1] ^= 1
					if e := os.WriteFile(path, bad, 0644); e != nil {
						t.Fatal(e)
					}
				case "symlink":
					if e := os.Symlink(filepath.Join(game, name), path); e != nil {
						t.Fatal(e)
					}
				}
				if e := load(); e == nil {
					t.Error("invalid original accepted")
				}
				if kind != "missing" {
					if e := os.Remove(path); e != nil {
						t.Fatal(e)
					}
				}
				if e := os.WriteFile(path, original, 0644); e != nil {
					t.Fatal(e)
				}
				if !bytes.Equal(hdOpeningRead(t, filepath.Join(game, name)), original) {
					t.Fatal("legal original changed")
				}
			})
		}
	}
	if e := load(); e != nil {
		t.Fatal("restored fixture", e)
	}
	if _, e := loadHDRuntime(golem.New(), game, assets); e != nil {
		t.Fatal("full206 runtime load", e)
	}
}

func TestHDFishPublishedObjectPrototype(t *testing.T) {
	root, assets, out := os.Getenv("TEST_HD_FISH_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_HD_FISH_OUTPUT")
	if root == "" || assets == "" || out == "" {
		t.Skip("需要私有21幀完整物件原型")
	}
	if e := os.Mkdir(out, 0755); e != nil {
		t.Fatal(e)
	}
	ref := filepath.Join(root, "normal57-observed-r1")
	var review struct {
		Points []struct {
			Step    uint64
			Matches []int `json:"native_pose_matches"`
			Reason  string
		}
	}
	if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(root, "fish-published-selected57-r1.json")), &review); e != nil {
		t.Fatal(e)
	}
	selected := map[uint64]bool{}
	seen := map[int]bool{}
	for _, p := range review.Points {
		for _, id := range p.Matches {
			if !seen[id] {
				selected[p.Step] = true
				seen[id] = true
			}
		}
	}
	if len(seen) != 21 {
		t.Fatal("缺21種正常原版姿態", seen)
	}
	var model struct {
		Calls []struct {
			ID       int    `json:"source_id"`
			Return   uint64 `json:"return_step"`
			Verified bool
			Count    int `json:"unique_writes"`
		}
		Points []struct {
			Step  uint64
			PIC   string `json:"published_pic_file"`
			Actor string `json:"published_actor_file"`
		}
	}
	if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "actors.json")), &model); e != nil {
		t.Fatal(e)
	}
	decoded := os.Getenv("TEST_HD_DECODED")
	records := []map[string]any{}
	for _, point := range model.Points {
		if !selected[point.Step] {
			continue
		}
		m := golem.New()
		memory := hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.memory", point.Step)))
		if len(memory) != len(m.Mem) {
			t.Fatal("完整原版RAM長度")
		}
		copy(m.Mem, memory)
		m.Steps = point.Step
		h := &hdRuntime{m: m}
		p, e := loadHDOpeningRuntime(h, os.Getenv("TEST_GAME_ROOT"), assets)
		if e != nil {
			t.Fatal(e)
		}
		p.native[0] = hdOpeningRead(t, filepath.Join(decoded, "1092.idx"))
		p.native[1] = hdOpeningRead(t, filepath.Join(decoded, "1179.idx"))
		p.mapValid = true
		s := p.sprites
		for slot, d := range hdOpeningSpriteDefinitions {
			native := hdOpeningRead(t, filepath.Join(decoded, fmt.Sprintf("%04d.idx", d.id)))
			if len(native) != d.w*d.h {
				t.Fatal("來源尺寸", d.id)
			}
			for i := range s.native[slot] {
				s.native[slot][i] = 253
			}
			copy(s.native[slot][:], native)
			for _, call := range model.Calls {
				if call.Verified && call.Count == d.opaque && call.ID == d.id && call.Return <= point.Step {
					s.nativeValid[slot] = true
					break
				}
			}
		}
		pic := hdOpeningRead(t, filepath.Join(ref, point.PIC))
		actors := hdOpeningRead(t, filepath.Join(ref, point.Actor))
		for pos := 0; pos < 64000; pos++ {
			at := pos * 6
			s.pictures[pos] = hdOpeningCell{pic[at], binary.LittleEndian.Uint32(pic[at+1 : at+5]), pic[at+5]}
			at = pos * 12
			id := binary.LittleEndian.Uint16(actors[at : at+2])
			if _, known := hdOpeningSpriteSlot(id); known {
				s.published[pos] = hdOpeningSpriteCell{id, binary.LittleEndian.Uint16(actors[at+2 : at+4]), actors[at+4], hdOpeningCell{actors[at+6], binary.LittleEndian.Uint32(actors[at+7 : at+11]), actors[at+11]}}
			}
		}
		f := draftNativeFrame{indexed: hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.idx", point.Step))), palette: hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.palette", point.Step))), mode: 19, step: point.Step}
		before := hash(m.Mem)
		imageOut := draftRGB(f.indexed, f.palette)
		receipt := s.paintWithin(imageOut, f, image.Rect(0, 0, 320, 200))
		pose := s.fishPose(f)
		if receipt["reason"] != "verified-published-opening" || !pose.valid || pose.slot < 0 {
			t.Fatal("不能驗完整魚形", point.Step, pose, receipt)
		}
		if hash(m.Mem) != before {
			t.Fatal("繪製寫入原版RAM")
		}
		// The same whole-object decision must restore a bounded cursor area exactly.
		cursor := image.Rect(584+pose.origin.X, 24+pose.origin.Y, 600+pose.origin.X, 40+pose.origin.Y)
		restored := draftRGB(f.indexed, f.palette)
		copy(restored.Pix, imageOut.Pix)
		native := draftRGB(f.indexed, f.palette)
		for y := cursor.Min.Y * 4; y < cursor.Max.Y*4; y++ {
			for x := cursor.Min.X * 4; x < cursor.Max.X*4; x++ {
				restored.SetRGBA(x, y, native.RGBAAt(x, y))
			}
		}
		s.paintWithin(restored, f, cursor)
		if !bytes.Equal(restored.Pix, imageOut.Pix) || hash(m.Mem) != before {
			t.Fatal("有界完整魚形恢復不一致")
		}
		name := fmt.Sprintf("point-%08d.png", point.Step)
		fd, e := os.Create(filepath.Join(out, name))
		if e != nil {
			t.Fatal(e)
		}
		if e = png.Encode(fd, imageOut); e != nil {
			t.Fatal(e)
		}
		if e = fd.Close(); e != nil {
			t.Fatal(e)
		}
		records = append(records, map[string]any{"step": point.Step, "image": name, "opening": receipt, "fish_pose": pose.slot + 1182, "scope": "private injected source model only, no normal rendered GUI or native hook credit"})
	}
	if len(records) != len(selected) {
		t.Fatal("略過選定正常資料", len(records), len(selected))
	}
	proof := map[string]any{"result": "PASS_PRIVATE_FISH21_WHOLE_OBJECT_MODEL_RENDERER", "state": "DRAFT", "images": len(records), "source_frames": 21, "records": records, "production_connected": false, "normal_gui_credit": false}
	raw, e := json.MarshalIndent(proof, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644); e != nil {
		t.Fatal(e)
	}
}
func TestHDFishNormalPublishedSources(t *testing.T) {
	game, assets, _ := hdOpeningFixtures(t)
	root, output := os.Getenv("TEST_HD_FISH_ROOT"), os.Getenv("TEST_HD_FISH_NATIVE_OUTPUT")
	if root == "" || output == "" {
		t.Skip("需要36來源獨立模型與新的輸出")
	}
	if e := os.Mkdir(output, 0755); e != nil {
		t.Fatal(e)
	}
	ref := filepath.Join(root, "normal57-observed-r1")
	var oracle struct {
		End    uint64
		Inputs []windowInput
		Points []struct {
			Step      uint64
			Memory    string `json:"memory_sha256"`
			Indexed   string `json:"indexed_sha256"`
			Palette   string `json:"palette_sha256"`
			Registers [8]uint16
			Segments  [4]uint16
			IP, Flags uint16
			Cycles    uint64
		}
	}
	if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "check.json")), &oracle); e != nil {
		t.Fatal(e)
	}
	type point struct {
		Step   uint64
		Actor  string         `json:"published_actor_file"`
		PIC    string         `json:"published_pic_file"`
		Counts map[string]int `json:"published_actor_counts"`
		Under  map[string]int `json:"published_underlay_counts"`
	}
	var model struct{ Points []point }
	if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "actors.json")), &model); e != nil {
		t.Fatal(e)
	}
	models := map[uint64]point{}
	for _, p := range model.Points {
		models[p.Step] = p
	}
	m := golem.New()
	if e := m.LoadEXE(hdOpeningRead(t, filepath.Join(game, "OPENING.EXE"))); e != nil {
		t.Fatal(e)
	}
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = output
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("數位音訊")
	}
	m.EnableOPLSynth(true)
	h := &hdRuntime{m: m}
	p, e := loadHDOpeningRuntime(h, game, assets)
	if e != nil {
		t.Fatal(e)
	}
	h.opening = p
	s := p.sprites
	m.SetBeforeInstruction(s.beforeInstruction)

	selected := map[uint64]bool{}
	var poseReview struct {
		Points []struct {
			Step    uint64
			Matches []int `json:"native_pose_matches"`
		}
	}
	if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(root, "fish-published-selected57-r1.json")), &poseReview); e != nil {
		t.Fatal(e)
	}
	wanted := map[int]bool{}
	for _, point := range poseReview.Points {
		for _, id := range point.Matches {
			if !wanted[id] {
				selected[point.Step] = true
				wanted[id] = true
			}
		}
	}
	if len(wanted) != 21 {
		t.Fatal("缺完整21種姿態", wanted)
	}
	seen := map[int]bool{}
	at, inputAt := 0, 0
	records := []map[string]any{}
	images := 0
	for m.Steps < oracle.End {
		for inputAt < len(oracle.Inputs) && oracle.Inputs[inputAt].Step == m.Steps {
			applyWindowInput(d, oracle.Inputs[inputAt])
			inputAt++
		}
		if at < len(oracle.Points) && oracle.Points[at].Step == m.Steps {
			want := oracle.Points[at]
			c := m.CPU
			if hash(m.Mem) != want.Memory || hash(m.Indexed()) != want.Indexed || hash(m.DAC[:]) != want.Palette || c.R != want.Registers || c.Seg != want.Segments || c.IP != want.IP || c.Flags != want.Flags || c.Cycles != want.Cycles {
				t.Fatal("原版狀態改變", m.Steps)
			}
			if selected[m.Steps] {
				modelRoot := ref
				expected := models[m.Steps]
				pic := hdOpeningRead(t, filepath.Join(modelRoot, expected.PIC))
				actor := hdOpeningRead(t, filepath.Join(modelRoot, expected.Actor))
				for pos, v := range s.pictures {
					a := pos * 6
					wanted := hdOpeningCell{pic[a], binary.LittleEndian.Uint32(pic[a+1 : a+5]), pic[a+5]}
					if v != wanted {
						t.Fatal("已發布PIK來源不符", m.Steps, pos, v, wanted)
					}
					a = pos * 12
					id := binary.LittleEndian.Uint16(actor[a : a+2])
					wantedActor := hdOpeningSpriteCell{}
					if _, known := hdOpeningSpriteSlot(id); known {
						wantedActor = hdOpeningSpriteCell{id, binary.LittleEndian.Uint16(actor[a+2 : a+4]), actor[a+4], hdOpeningCell{actor[a+6], binary.LittleEndian.Uint32(actor[a+7 : a+11]), actor[a+11]}}
					}
					if s.published[pos] != wantedActor {
						t.Fatal("已發布36來源不符", m.Steps, pos, s.published[pos], wantedActor)
					}
				}
				f := draftNativeFrame{indexed: m.Indexed(), palette: m.DAC[:], mode: m.VideoMode(), step: m.Steps}
				out := draftRGB(f.indexed, f.palette)
				before := hash(m.Mem)
				receipt := s.paintWithin(out, f, image.Rect(0, 0, 320, 200))
				if hash(m.Mem) != before {
					t.Fatal("顯示寫入原版")
				}

				if receipt["reason"] != "verified-published-opening" {
					t.Fatal("來源不能繪製", receipt)
				}
				groups := []struct {
					ids    []int
					counts []int
				}{}
				ship := receipt["frames"].([8]int)
				sun := receipt["sun_frames"].([7]int)
				wind := receipt["wind_frames"].([10]int)
				smoke := receipt["smoke_frames"].([11]int)
				fish := receipt["fish_frames"].([21]int)
				groups = append(groups, struct {
					ids    []int
					counts []int
				}{[]int{1250, 1251, 1252, 1253, 1254, 1255, 1256, 1257}, ship[:]})
				groups = append(groups, struct {
					ids    []int
					counts []int
				}{[]int{1258, 1259, 1260, 1261, 1262, 1263, 1264}, sun[:]})
				groups = append(groups, struct {
					ids    []int
					counts []int
				}{[]int{1266, 1267, 1268, 1269, 1270, 1271, 1272, 1273, 1274, 1275}, wind[:]})
				groups = append(groups, struct {
					ids    []int
					counts []int
				}{[]int{1276, 1277, 1278, 1279, 1280, 1281, 1282, 1283, 1284, 1285, 1286}, smoke[:]})
				groups = append(groups, struct {
					ids    []int
					counts []int
				}{[]int{1182, 1183, 1184, 1185, 1186, 1187, 1188, 1189, 1190, 1191, 1192, 1193, 1194, 1195, 1196, 1197, 1198, 1199, 1200, 1201, 1202}, fish[:]})
				for _, group := range groups {
					for i, count := range group.counts {
						id := group.ids[i]
						want := expected.Counts[fmt.Sprint(id)]
						if count != want {
							t.Fatal("可見來源數不符", m.Steps, id, count, want)
						}
						if count > 0 {
							seen[id] = true
						}
					}
				}
				if m.Steps == 399200000 && sun[5] != 9 {
					t.Fatal("太陽裁切改變", sun)
				}
				file := fmt.Sprintf("point-%08d.png", m.Steps)
				fd, e := os.Create(filepath.Join(output, file))
				if e != nil {
					t.Fatal(e)
				}
				if e = png.Encode(fd, out); e != nil {
					t.Fatal(e)
				}
				if e = fd.Close(); e != nil {
					t.Fatal(e)
				}
				records = append(records, map[string]any{"step": m.Steps, "opening": receipt, "image": file})
				images++
			}
			t.Log("NATIVE", m.Steps, s.accepted, s.rejected)
			at++
		}
		if e := m.Step(); e != nil {
			t.Fatal(e)
		}
	}
	verifiedSources := 0
	for _, valid := range s.nativeValid {
		if valid {
			verifiedSources++
		}
	}
	fishSeen := 0
	for id := range seen {
		if id >= 1182 && id <= 1202 {
			fishSeen++
		}
	}
	if at != len(oracle.Points) || at != 144 || inputAt != 1 || images != len(selected) || fishSeen != 21 || verifiedSources != 57 || s.accepted != 1100 || s.rejected != 0 {
		t.Fatal("正常來源範圍", at, inputAt, images, s.accepted, s.rejected)
	}
	raw, e := json.MarshalIndent(map[string]any{"result": "PASS_PRIVATE_FISH21_NORMAL_NATIVE144_PUBLISHED57", "points": at, "inputs": inputAt, "end": m.Steps, "accepted": s.accepted, "rejected": s.rejected, "images": images, "records": records, "source_frames": verifiedSources, "rendered_fish_sources": fishSeen, "state": "DRAFT", "production_connected": false, "normal_gui_credit": false}, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(output, "check.json"), append(raw, '\n'), 0644); e != nil {
		t.Fatal(e)
	}
}

func hdFishPrototypeSnapshot(t *testing.T, wantID int) (*hdOpeningSpriteRuntime, draftNativeFrame) {
	t.Helper()
	root := os.Getenv("TEST_HD_FISH_ROOT")
	assets := os.Getenv("TEST_HD_ASSETS")
	if root == "" || assets == "" {
		t.Skip("需要私有魚形完整物件資料")
	}
	var review struct {
		Points []struct {
			Step    uint64
			Matches []int `json:"native_pose_matches"`
		}
	}
	if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(root, "fish-published-selected57-r1.json")), &review); e != nil {
		t.Fatal(e)
	}
	var step uint64
	for _, p := range review.Points {
		for _, id := range p.Matches {
			if id == wantID && step == 0 {
				step = p.Step
			}
		}
	}
	if step == 0 {
		t.Fatal("缺正常原版姿態", wantID)
	}
	ref := filepath.Join(root, "normal57-observed-r1")
	var model struct {
		Calls []struct {
			ID       int    `json:"source_id"`
			Return   uint64 `json:"return_step"`
			Verified bool
			Count    int `json:"unique_writes"`
		}
		Points []struct {
			Step  uint64
			PIC   string `json:"published_pic_file"`
			Actor string `json:"published_actor_file"`
		}
	}
	if e := json.Unmarshal(hdOpeningRead(t, filepath.Join(ref, "actors.json")), &model); e != nil {
		t.Fatal(e)
	}
	var picName, actorName string
	for _, p := range model.Points {
		if p.Step == step {
			picName, actorName = p.PIC, p.Actor
		}
	}
	if picName == "" {
		t.Fatal("缺原版來源快照")
	}
	m := golem.New()
	memory := hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.memory", step)))
	if len(memory) != len(m.Mem) {
		t.Fatal("完整RAM長度")
	}
	copy(m.Mem, memory)
	m.Steps = step
	p, e := loadHDOpeningRuntime(&hdRuntime{m: m}, os.Getenv("TEST_GAME_ROOT"), assets)
	if e != nil {
		t.Fatal(e)
	}
	decoded := os.Getenv("TEST_HD_DECODED")
	p.native[0] = hdOpeningRead(t, filepath.Join(decoded, "1092.idx"))
	p.native[1] = hdOpeningRead(t, filepath.Join(decoded, "1179.idx"))
	p.mapValid = true
	s := p.sprites
	for slot, d := range hdOpeningSpriteDefinitions {
		raw := hdOpeningRead(t, filepath.Join(decoded, fmt.Sprintf("%04d.idx", d.id)))
		if len(raw) != d.w*d.h {
			t.Fatal("原始來源長度", d.id)
		}
		for k := range s.native[slot] {
			s.native[slot][k] = 253
		}
		copy(s.native[slot][:], raw)
		for _, c := range model.Calls {
			if c.Verified && c.ID == d.id && c.Count == d.opaque && c.Return <= step {
				s.nativeValid[slot] = true
				break
			}
		}
	}
	pic := hdOpeningRead(t, filepath.Join(ref, picName))
	actor := hdOpeningRead(t, filepath.Join(ref, actorName))
	for pos := 0; pos < 64000; pos++ {
		at := pos * 6
		s.pictures[pos] = hdOpeningCell{pic[at], binary.LittleEndian.Uint32(pic[at+1 : at+5]), pic[at+5]}
		at = pos * 12
		id := binary.LittleEndian.Uint16(actor[at : at+2])
		if _, ok := hdOpeningSpriteSlot(id); ok {
			s.published[pos] = hdOpeningSpriteCell{id, binary.LittleEndian.Uint16(actor[at+2 : at+4]), actor[at+4], hdOpeningCell{actor[at+6], binary.LittleEndian.Uint32(actor[at+7 : at+11]), actor[at+11]}}
		}
	}
	f := draftNativeFrame{indexed: hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.idx", step))), palette: hdOpeningRead(t, filepath.Join(ref, fmt.Sprintf("point-%08d.palette", step))), mode: 19, step: step}
	if pose := s.fishPose(f); !pose.valid {
		t.Fatal("完整原版fixture必須先成功", pose)
	}
	return s, f
}

func TestHDFishWholeObjectGuards(t *testing.T) {
	cases := []string{"unknown-picture", "unknown-underlay", "wrong-anchor", "mixed-origin", "missing-full-shadow", "bad-local", "bad-source-id", "palette", "mode", "video-surface", "program-exit"}
	for _, name := range cases {
		t.Run(name, func(t *testing.T) {
			s, f := hdFishPrototypeSnapshot(t, 1182)
			pose := s.fishPose(f)
			full := draftRGB(f.indexed, f.palette)
			s.paintWithin(full, f, image.Rect(0, 0, 320, 200))
			fishPos, picPos := -1, -1
			for pos, c := range s.published {
				if c.id == 1182 {
					fishPos = pos
					break
				}
			}
			for pos, c := range s.pictures {
				if c.kind == 2 && image.Pt(int(c.local)%960, int(c.local)/960).In(hdOpeningFishWorld) && s.published[pos].id == 0 {
					picPos = pos
					break
				}
			}
			if fishPos < 0 || picPos < 0 {
				t.Fatal("fixture缺來源")
			}
			global := false
			switch name {
			case "unknown-picture":
				s.pictures[picPos] = hdOpeningCell{}
			case "unknown-underlay":
				s.published[fishPos].under = hdOpeningCell{}
			case "wrong-anchor":
				c := s.published[fishPos]
				c.under.local++
				c.under.value = s.p.native[1][c.under.local]
				s.published[fishPos] = c
			case "mixed-origin":
				found := false
				for pos, c := range s.published {
					if c.id != 1182 {
						continue
					}
					local := int(c.local) + 1
					if local >= 27*20 || local%27 == 0 || s.native[36][local] != c.value {
						continue
					}
					c.local = uint16(local)
					c.under.local++
					c.under.value = s.p.native[1][c.under.local]
					s.published[pos] = c
					found = true
					break
				}
				if !found {
					t.Fatal("fixture缺相鄰同值格")
				}
			case "missing-full-shadow":
				s.nativeValid[36] = false
				global = true
			case "bad-local":
				s.published[fishPos].local = 65535
				global = true
			case "bad-source-id":
				s.published[fishPos].id = 65535
				global = true
			case "palette":
				f.palette[0] ^= 1
				global = true
			case "mode":
				f.mode = 3
				global = true
			case "video-surface":
				s.p.h.m.Mem[0xa0000] ^= 1
				global = true
			case "program-exit":
				s.p.h.m.Mem[0x5570+0x9f] ^= 1
				global = true
			}
			before := hash(s.p.h.m.Mem)
			native := draftRGB(f.indexed, f.palette)
			out := draftRGB(f.indexed, f.palette)
			receipt := s.paintWithin(out, f, image.Rect(0, 0, 320, 200))
			if hash(s.p.h.m.Mem) != before {
				t.Fatal("拒絕路徑改寫原版RAM")
			}
			if global {
				if receipt["painted"] != 0 || !bytes.Equal(out.Pix, native.Pix) {
					t.Fatal("全域失效未保持原圖", receipt)
				}
				return
			}
			object := receipt["fish_object"].(map[string]any)
			if object["verified"] != false || receipt["fish_frames"] != ([21]int{}) {
				t.Fatal("未知物件仍有HD信用", object)
			}
			rect := hdOpeningFishWorld.Add(pose.origin)
			for y := 0; y < 800; y++ {
				for x := 0; x < 1280; x++ {
					want := full.RGBAAt(x, y)
					if image.Pt(x/4, y/4).In(rect) {
						want = native.RGBAAt(x, y)
					}
					if out.RGBAAt(x, y) != want {
						t.Fatal("物件回退或區外像素不符", x, y, receipt)
					}
				}
			}
		})
	}
}

func TestHDFishEquivalentNativeAlias(t *testing.T) {
	s, f := hdFishPrototypeSnapshot(t, 1186)
	pose := s.fishPose(f)
	if !pose.valid {
		t.Fatal(pose)
	}
	good := draftRGB(f.indexed, f.palette)
	s.paintWithin(good, f, image.Rect(0, 0, 320, 200))
	replaced := false
	for pos, c := range s.published {
		if c.id == 1186 {
			c.id = 1183
			s.published[pos] = c
			replaced = true
			break
		}
	}
	if !replaced {
		t.Fatal("缺同源別名格")
	}
	next := s.fishPose(f)
	if !next.valid || len(next.candidates) < 2 {
		t.Fatal("等值且同原圖的來源別名應成立", next)
	}
	out := draftRGB(f.indexed, f.palette)
	s.paintWithin(out, f, image.Rect(0, 0, 320, 200))
	if !bytes.Equal(out.Pix, good.Pix) {
		t.Fatal("來源別名改變畫面")
	}
	// Equal native poses with differing generated caches must fail closed.
	s.fish.art[1].Pix[0] ^= 1
	bad := s.fishPose(f)
	if bad.valid || bad.reason != "ambiguous-fish-art" {
		t.Fatal("未拒絕不同原圖類別", bad)
	}
}

func TestHDFishOpeningResourceGuards(t *testing.T) {
	game, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS")
	if game == "" || assets == "" {
		t.Skip("需要合法原版與206原PNG")
	}
	root := t.TempDir()
	g, a := filepath.Join(root, "game"), filepath.Join(root, "graphics")
	if e := os.Mkdir(g, 0755); e != nil {
		t.Fatal(e)
	}
	if e := os.Mkdir(a, 0755); e != nil {
		t.Fatal(e)
	}
	gameNames := map[string]bool{"OPENING.EXE": true, "OPENING.PIK": true, "OPENBORD.PIK": true}
	for _, d := range hdOpeningSpriteDefinitions {
		gameNames[d.sourceFile] = true
	}
	originals := map[string][]byte{}
	rawAssets := map[string][]byte{}
	for name := range gameNames {
		b := hdOpeningRead(t, filepath.Join(game, name))
		originals[name] = b
		if e := os.WriteFile(filepath.Join(g, name), b, 0644); e != nil {
			t.Fatal(e)
		}
	}
	entries, e := os.ReadDir(assets)
	if e != nil {
		t.Fatal(e)
	}
	for _, entry := range entries {
		if entry.IsDir() {
			t.Fatal("非預期資產目錄")
		}
		name := entry.Name()
		b := hdOpeningRead(t, filepath.Join(assets, name))
		rawAssets[name] = b
		if e := os.WriteFile(filepath.Join(a, name), b, 0644); e != nil {
			t.Fatal(e)
		}
	}
	if len(rawAssets) != 207 || len(gameNames) != 9 {
		t.Fatal("opening-only完整fixture", len(rawAssets), len(gameNames))
	}
	full := func() (*hdOpeningRuntime, error) { return loadHDOpeningRuntime(&hdRuntime{m: golem.New()}, g, a) }
	initial, e := full()
	if e != nil {
		t.Fatal("拒絕案例開始前必須完整成功", e)
	}
	// Only new SS/PNG/clear inputs are mutated. All inherited PIK bytes remain
	// verified before and after every case, so their immutable art cache is reused.
	load := func() error { _, e := loadHDOpeningSprites(initial, g, a); return e }
	verify := func() {
		t.Helper()
		for name, want := range rawAssets {
			if !bytes.Equal(hdOpeningRead(t, filepath.Join(a, name)), want) {
				t.Fatal("其他資產漂移", name)
			}
		}
		for name, want := range originals {
			if !bytes.Equal(hdOpeningRead(t, filepath.Join(g, name)), want) {
				t.Fatal("其他原版fixture漂移", name)
			}
		}
	}
	targets := []struct {
		root, name string
		raw        []byte
	}{}
	for _, d := range hdOpeningSpriteDefinitions[36:] {
		targets = append(targets, struct {
			root, name string
			raw        []byte
		}{a, d.asset, rawAssets[d.asset]})
	}
	targets = append(targets, struct {
		root, name string
		raw        []byte
	}{a, "opening-fish-clear-000.png", rawAssets["opening-fish-clear-000.png"]})
	for _, name := range []string{"OPENMON1.SS", "OPENMON2.SS"} {
		targets = append(targets, struct {
			root, name string
			raw        []byte
		}{g, name, originals[name]})
	}
	for _, target := range targets {
		for _, kind := range []string{"missing", "wrong", "symlink"} {
			t.Run(target.name+"/"+kind, func(t *testing.T) {
				verify()
				p := filepath.Join(target.root, target.name)
				if e := os.Remove(p); e != nil {
					t.Fatal(e)
				}
				if kind == "wrong" {
					if e := os.WriteFile(p, []byte("wrong"), 0644); e != nil {
						t.Fatal(e)
					}
				}
				if kind == "symlink" {
					parent := assets
					if target.root == g {
						parent = game
					}
					if e := os.Symlink(filepath.Join(parent, target.name), p); e != nil {
						t.Fatal(e)
					}
				}
				if e := load(); e == nil {
					t.Fatal("錯件未拒絕")
				}
				if _, e := os.Lstat(p); e == nil {
					if e := os.Remove(p); e != nil {
						t.Fatal(e)
					}
				}
				if e := os.WriteFile(p, target.raw, 0644); e != nil {
					t.Fatal(e)
				}
				verify()
			})
		}
	}
	if _, e := full(); e != nil {
		t.Fatal("全部錯件恢復後必須完整成功", e)
	}
}

func r100Root(t *testing.T) string {
	t.Helper()
	p := os.Getenv("TEST_R100_ROOT")
	if p == "" {
		t.Skip("requires private original R100 source receipts")
	}
	return p
}
func TestR100SixPartialFishReuse(t *testing.T) {
	root := r100Root(t)
	m := golem.New()
	p, e := loadHDOpeningRuntime(&hdRuntime{m: m}, os.Getenv("TEST_GAME_ROOT"), "/repo/graphics")
	if e != nil {
		t.Fatal(e)
	}
	type row struct {
		ID, SourceID, W, H, Alpha, Opaque int
		RGBA                              []byte
		Asset                             string
	}
	rows := []row{}
	for i := 57; i < 63; i++ {
		d := hdOpeningSpriteDefinitions[i]
		base := hdOpeningSpriteDefinitions[51+i-57]
		if d.id != 1204+i-57 || d.reuseFish != base.id {
			t.Fatal("wrong explicit source pair", i)
		}
		target := hdOpeningRead(t, fmt.Sprintf("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/%04d.idx", d.id))
		native := hdOpeningRead(t, fmt.Sprintf("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/%04d.idx", base.id))
		if len(target) != d.w*d.h || len(native) != base.w*base.h {
			t.Fatal("native shape")
		}
		opaque, alpha := 0, 0
		for k, v := range target {
			if v == 253 {
				continue
			}
			opaque++
			if native[k/d.w*base.w+k%d.w] != v {
				t.Fatal("inherited native value mismatch", d.id, k)
			}
			for y := 0; y < 4; y++ {
				for x := 0; x < 4; x++ {
					if p.sprites.art[i].NRGBAAt(k%d.w*4+x, k/d.w*4+y).A > 0 {
						alpha++
					}
				}
			}
		}
		if opaque != d.opaque || alpha == 0 {
			t.Fatal("missing verified native or art pixels", d.id, opaque, alpha)
		}
		rows = append(rows, row{d.id, base.id, d.w, d.h, alpha, opaque, p.sprites.art[i].Pix, d.asset})
		t.Run(fmt.Sprint(d.id), func(t *testing.T) {
			if p.sprites.art[i].Bounds() != image.Rect(0, 0, d.w*4, d.h*4) {
				t.Fatal("sample bounds")
			}
		})
	}
	raw, e := json.MarshalIndent(rows, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(root, "r100-tail-formal-samples-r1.json"), raw, 0644); e != nil {
		t.Fatal(e)
	}
}
func TestR100SixPartialFishSourceGuards(t *testing.T) {
	r100Root(t)
	for slot := 57; slot < 63; slot++ {
		d := hdOpeningSpriteDefinitions[slot]
		raw := hdOpeningRead(t, fmt.Sprintf("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/%04d.idx", d.id))
		for _, name := range []string{"valid", "missing", "duplicate", "wrong-value", "unknown-write", "same-value-revoke"} {
			t.Run(fmt.Sprintf("%d/%s", d.id, name), func(t *testing.T) {
				m := golem.New()
				s := &hdOpeningSpriteRuntime{p: &hdOpeningRuntime{h: &hdRuntime{m: m}}, selected: slot, x: 100, y: 50, active: true}
				first := -1
				for k, v := range raw {
					if v == 253 {
						continue
					}
					if first < 0 {
						first = k
					}
					s.counts[k] = 1
					s.writes[k] = v
				}
				switch name {
				case "missing":
					s.counts[first] = 0
				case "duplicate":
					s.counts[first] = 2
				case "wrong-value":
					s.writes[first] ^= 1
				case "unknown-write":
					s.outside = true
				}
				before := bytes.Clone(m.Mem)
				s.finish()
				if !bytes.Equal(before, m.Mem) {
					t.Fatal("source guard changed native RAM")
				}
				if name == "valid" || name == "same-value-revoke" {
					if s.accepted != 1 || s.rejected != 0 || !s.nativeValid[slot] {
						t.Fatal("complete source rejected")
					}
					count := 0
					for k, v := range raw {
						pos := (50+k/d.w)*320 + 100 + k%d.w
						if v == 253 {
							if s.cells[pos].id != 0 {
								t.Fatal("transparent native cell gained ownership")
							}
						} else {
							if s.cells[pos].id != uint16(d.id) || s.cells[pos].value != v {
								t.Fatal("wrong source cell")
							}
							count++
						}
					}
					if count != d.opaque {
						t.Fatal("opaque count")
					}
					if name == "same-value-revoke" {
						pos := (50+first/d.w)*320 + 100 + first%d.w
						v := raw[first]
						s.write(hdOpeningMain+uint32(pos), v, v)
						if s.cells[pos].id != 0 || s.same != 1 {
							t.Fatal("same-value write retained source")
						}
					}
				} else if s.accepted != 0 || s.rejected != 1 || s.nativeValid[slot] {
					t.Fatal("invalid source accepted")
				}
			})
		}
	}
}
func TestR100FishReuseGuards(t *testing.T) {
	r100Root(t)
	d := hdOpeningSpriteDefinitions[57]
	f := image.NewNRGBA(image.Rect(0, 0, d.artSize.X, d.artSize.Y))
	cases := []struct {
		name   string
		change func(*hdOpeningSpriteDefinition)
	}{
		{"unknown-pair", func(x *hdOpeningSpriteDefinition) { x.reuseFish++ }},
		{"wrong-ordinal", func(x *hdOpeningSpriteDefinition) { x.ordinal++ }},
		{"larger-than-source", func(x *hdOpeningSpriteDefinition) { x.w = 320 }},
		{"asset", func(x *hdOpeningSpriteDefinition) { x.asset = "other.png" }},
		{"art-hash", func(x *hdOpeningSpriteDefinition) { x.artSHA = "bad" }},
		{"source-file", func(x *hdOpeningSpriteDefinition) { x.sourceFile = "OTHER.SS" }},
		{"source-hash", func(x *hdOpeningSpriteDefinition) { x.sourceSHA = "bad" }},
		{"rectangles", func(x *hdOpeningSpriteDefinition) { x.nativeRects = []image.Rectangle{image.Rect(0, 0, 1, 1)} }},
		{"dimensions", func(x *hdOpeningSpriteDefinition) { x.artSize.X++ }},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			bad := d
			c.change(&bad)
			if _, e := sampleHDOpeningFishFragment(bad, f); e == nil {
				t.Fatal("unverified sample reuse accepted")
			}
		})
	}
}
