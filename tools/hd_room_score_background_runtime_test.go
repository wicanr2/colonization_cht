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
