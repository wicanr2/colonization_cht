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
	for _, n := range []string{"OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK"} {
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
	files := []string{"OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK"}
	for _, d := range hdOpeningDefinitions {
		files = append(files, d.asset)
	}
	for _, name := range files {
		for _, kind := range []string{"missing", "wrong", "symlink"} {
			t.Run(kind+"/"+name, func(t *testing.T) {
				g, a := t.TempDir(), t.TempDir()
				for _, f := range []string{"OPENING.EXE", "OPENING.PIK", "OPENBORD.PIK"} {
					if e := os.WriteFile(filepath.Join(g, f), hdOpeningRead(t, filepath.Join(game, f)), 0644); e != nil {
						t.Fatal(e)
					}
				}
				for _, f := range hdOpeningDefinitions {
					if e := os.WriteFile(filepath.Join(a, f.asset), hdOpeningRead(t, filepath.Join(assets, f.asset)), 0644); e != nil {
						t.Fatal(e)
					}
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
