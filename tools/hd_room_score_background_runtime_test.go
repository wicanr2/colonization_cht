package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"os"
	"path/filepath"
	"strconv"
	"testing"
)

func TestHDRoomScoreDecodePaletteAndUnderlay(t *testing.T) {
	game, root, assets := hdReportFixtures(t)
	model := os.Getenv("TEST_HD_REPORT_MODEL")
	if model == "" {
		t.Skip("需要國會室內及計分來源收據")
	}
	for _, id := range []int{120, 1551} {
		t.Run(fmt.Sprint(id), func(t *testing.T) {
			h := &hdRuntime{m: golem.New()}
			p, err := loadHDSceneRuntime(h, game, assets)
			hdNewGameNeed(t, err)
			index := -1
			for i, f := range p.frames {
				if f.id == id {
					index = i
				}
			}
			if index < 0 {
				t.Fatal("缺背景來源")
			}
			f := p.frames[index]
			raw := hdNewGameRead(t, filepath.Join("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels", fmt.Sprintf("%04d.idx", id)))
			if len(raw) != 64000 || hash(raw) != f.nativeSHA {
				t.Fatal("背景原版資料不同")
			}
			bases := []uint32{0x3c500}
			if id == 1551 {
				bases = append(bases, hdBuildingCanvas)
			}
			for _, base := range bases {
				before := f.decoded
				copy(h.m.Mem[base:base+64000], raw)
				p.decodedAt(base, 0)
				if f.decoded != before+1 {
					t.Fatal("已驗畫布未解碼", base)
				}
				t.Run(fmt.Sprintf("corrupt-%X", base), func(t *testing.T) {
					visible, stage := p.visible, p.stage
					h.m.Mem[base+12345] ^= 1
					p.decodedAt(base, 0)
					if f.decoded != before+1 || p.visible != visible || p.stage != stage {
						t.Fatal("錯IDX仍授權")
					}
					h.m.Mem[base+12345] ^= 1
				})
			}
			rejected := []uint32{0x3d500}
			if id == 120 {
				rejected = append(rejected, hdBuildingCanvas)
			}
			for _, base := range rejected {
				t.Run(fmt.Sprintf("wrong-canvas-%X", base), func(t *testing.T) {
					before := f.decoded
					visible, stage := p.visible, p.stage
					copy(h.m.Mem[base:base+64000], raw)
					p.decodedAt(base, 0)
					if f.decoded != before || p.visible != visible || p.stage != stage {
						t.Fatal("未知畫布仍授權")
					}
				})
			}
			point := 9
			if id == 1551 {
				point = 25
			}
			pal := hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control", fmt.Sprintf("point-%03d.palette", point)))
			if !f.paletteSupported(pal) {
				t.Fatal("原版色盤被拒絕")
			}
			used := [256]bool{}
			for _, v := range raw {
				used[v] = true
			}
			t.Run("all-palette-channels", func(t *testing.T) {
				for i := 0; i < 256; i++ {
					for ch := 0; ch < 3; ch++ {
						bad := append([]byte(nil), pal...)
						bad[i*3+ch] ^= 1
						if f.paletteSupported(bad) == used[i] {
							t.Fatal("使用色號守門不同", i, ch)
						}
					}
				}
			})
			var owners map[string][]any
			hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(model, fmt.Sprintf("point-%03d.owners.json", point))), &owners))
			canvas := hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control", fmt.Sprintf("point-%03d.canvas", point)))
			found := false
			for key, c := range owners {
				if int(c[0].(float64)) != id || (id == 1551 && c[3].(string) != "glyph") {
					continue
				}
				pos, e := strconv.Atoi(key)
				hdNewGameNeed(t, e)
				cell := hdSceneCell{slot: uint8(index + 1), local: uint16(c[1].(float64)), value: byte(c[2].(float64)), glyph: c[3].(string) == "glyph"}
				p.visible[pos] = cell
				frame := draftNativeFrame{canvas: canvas, palette: pal, mode: 0x13}
				out := image.NewRGBA(image.Rect(0, 0, 1280, 800))
				value := raw[cell.local]
				if !p.paintBackground(out, frame, pos, value, pal) {
					t.Fatal("已驗背景或字底不可回畫")
				}
				t.Run("wrong-underlay", func(t *testing.T) {
					if p.paintBackground(out, frame, pos, value^1, pal) {
						t.Fatal("錯字底仍回畫")
					}
				})
				t.Run("changed-visible", func(t *testing.T) {
					bad := frame
					bad.canvas = bytes.Clone(canvas)
					bad.canvas[pos] ^= 1
					if p.paintBackground(out, bad, pos, value, pal) {
						t.Fatal("未知前景仍回畫")
					}
				})
				t.Run("wrong-mode", func(t *testing.T) {
					bad := frame
					bad.mode = 3
					if p.paintBackground(out, bad, pos, value, pal) {
						t.Fatal("未知模式仍回畫")
					}
				})
				found = true
				break
			}
			if !found {
				t.Fatal("缺實際背景或字底正例")
			}
		})
	}
}

func TestHDScenePublishedWriteGuards(t *testing.T) {
	game, _, assets := hdReportFixtures(t)
	for _, name := range []string{"known", "normalized-source", "wrong-code", "wrong-source", "source-value", "same-value-revoke", "post-publication-main-write"} {
		t.Run(name, func(t *testing.T) {
			m := golem.New()
			h := &hdRuntime{m: m}
			p, err := loadHDSceneRuntime(h, game, assets)
			hdNewGameNeed(t, err)
			h.scenes = p
			raw := hdNewGameRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/1551.idx")
			copy(m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000], raw)
			p.decodedAt(hdBuildingCanvas, 0)
			pos := 40000
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
				m.CPU.R[golem.AX] = uint16(raw[pos])
				hdNewGameNeed(t, m.Step())
				if name == "same-value-revoke" && p.published[pos].slot != 0 {
					t.Fatal("未知VGA同值寫入未撤銷")
				}
				if name == "post-publication-main-write" && (p.published[pos] != before || p.visible[pos].slot != 0) {
					t.Fatal("主畫布後寫污染已發布來源")
				}
			}
		})
	}
}

func TestHDScenePublishedSurfaceGuards(t *testing.T) {
	game, root, assets := hdReportFixtures(t)
	model := os.Getenv("TEST_HD_PUBLISHED_MODEL")
	if model == "" {
		t.Skip("需要已發布來源模型")
	}
	h := &hdRuntime{m: golem.New()}
	p, err := loadHDSceneRuntime(h, game, assets)
	hdNewGameNeed(t, err)
	h.scenes = p
	raw := hdNewGameRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/1551.idx")
	copy(h.m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000], raw)
	p.decodedAt(hdBuildingCanvas, 0)
	memory := hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control/point-001.memory"))
	copy(h.m.Mem, memory)
	var cells map[string][]any
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(model, "point-001.published.json")), &cells))
	pos := -1
	for key, c := range cells {
		at, e := strconv.Atoi(key)
		hdNewGameNeed(t, e)
		if int(c[0].(float64)) != 1551 || c[3].(string) != "background" || image.Pt(at%320, at/320).In(image.Rect(16, 16, 32, 32)) {
			continue
		}
		for i, f := range p.frames {
			if f.id == 1551 {
				p.published[at] = hdSceneCell{slot: uint8(i + 1), local: uint16(c[1].(float64)), value: byte(c[2].(float64))}
				pos = at
			}
		}
		if pos >= 0 {
			break
		}
	}
	if pos < 0 {
		t.Fatal("缺背景正例")
	}
	f := draftNativeFrame{canvas: bytes.Clone(memory[hdBuildingCanvas : hdBuildingCanvas+64000]), indexed: hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control/point-001.idx")), palette: hdNewGameRead(t, filepath.Join(root, "report-source-probe-r2/control/point-001.palette")), cursor: image.Rect(16, 16, 32, 32), mode: 0x13}
	im := draftRGB(f.indexed, f.palette)
	if p.paintPublished(im, f)["painted"] != 1 {
		t.Fatal("已驗背景正例被拒")
	}
	for _, name := range []string{"vga-changed", "indexed-changed", "published-value-changed", "palette-changed", "short-indexed", "short-canvas", "wrong-mode", "wrong-cursor", "blocked", "cursor-source-changed"} {
		t.Run(name, func(t *testing.T) {
			copy(h.m.Mem, memory)
			p.blocked = false
			bad := f
			bad.indexed = bytes.Clone(f.indexed)
			bad.canvas = bytes.Clone(f.canvas)
			bad.palette = bytes.Clone(f.palette)
			switch name {
			case "vga-changed":
				h.m.Mem[0xa0000+pos] ^= 1
			case "indexed-changed":
				bad.indexed[pos] ^= 1
			case "published-value-changed":
				bad.indexed[pos] ^= 1
				h.m.Mem[0xa0000+pos] ^= 1
			case "palette-changed":
				bad.palette[int(p.published[pos].value)*3] ^= 1
			case "short-indexed":
				bad.indexed = bad.indexed[:63999]
			case "short-canvas":
				bad.canvas = bad.canvas[:63999]
			case "wrong-mode":
				bad.mode = 0x12
			case "wrong-cursor":
				bad.cursor = image.Rect(16, 16, 31, 32)
			case "blocked":
				p.blocked = true
			case "cursor-source-changed":
				h.m.Mem[0x1cd74] ^= 1
			}
			out := draftRGB(f.indexed, f.palette)
			before := bytes.Clone(out.Pix)
			got := p.paintPublished(out, bad)
			if got["painted"] != 0 || !bytes.Equal(before, out.Pix) {
				t.Fatal("未知來源仍畫HD", name, got)
			}
		})
	}
}
