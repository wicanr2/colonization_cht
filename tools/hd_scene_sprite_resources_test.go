package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestHDEventResources(t *testing.T) {
	game, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS")
	if game == "" || assets == "" {
		t.Skip("需要合法原版與隔離HD原圖")
	}
	t.Run("all276-scenes", func(t *testing.T) {
		m := golem.New()
		before := append([]byte(nil), m.Mem...)
		p, e := loadHDSceneRuntime(&hdRuntime{m: m}, game, assets)
		if e != nil || p == nil || len(p.frames) != 276 {
			t.Fatal("full scene load", e)
		}
		if !bytes.Equal(before, m.Mem) {
			t.Fatal("loader mutated DOS")
		}
		sprites := 0
		for _, f := range p.frames {
			if f.sprite != nil {
				sprites++
				if f.art.Bounds() != image.Rect(0, 0, f.sprite.width*4, f.sprite.height*4) || len(f.native) != 0 {
					t.Fatal("source armed before original draw")
				}
			}
		}
		if sprites != 247 {
			t.Fatal("all fixed SS scene sources", sprites)
		}
	})
	original := append([]hdSceneDefinition(nil), hdSceneDefinitions...)
	for _, definition := range original {
		if definition.sprite == nil {
			continue
		}
		for _, kind := range []string{"missing", "wrong-byte", "symlink", "wrong-original"} {
			t.Run(fmt.Sprint(definition.id)+"/"+kind, func(t *testing.T) {
				hdSceneDefinitions = []hdSceneDefinition{definition}
				for _, other := range original {
					if other.id != definition.id {
						hdSceneDefinitions = append(hdSceneDefinitions, other)
					}
				}
				defer func() { hdSceneDefinitions = original }()
				temp := t.TempDir()
				directory, gameDir := temp, game
				expected := ""
				switch kind {
				case "missing":
					expected = definition.asset
				case "wrong-byte":
					raw, e := os.ReadFile(filepath.Join(assets, definition.asset))
					if e != nil {
						t.Fatal(e)
					}
					raw[len(raw)/2] ^= 1
					if e = os.WriteFile(filepath.Join(temp, definition.asset), raw, 0644); e != nil {
						t.Fatal(e)
					}
					expected = "scene asset fingerprint: " + definition.asset
				case "symlink":
					if e := os.Symlink(filepath.Join(assets, definition.asset), filepath.Join(temp, definition.asset)); e != nil {
						t.Fatal(e)
					}
					expected = "not a bounded regular file"
				case "wrong-original":
					raw, e := os.ReadFile(filepath.Join(game, definition.file))
					if e != nil {
						t.Fatal(e)
					}
					raw[len(raw)/2] ^= 1
					if e = os.WriteFile(filepath.Join(temp, definition.file), raw, 0644); e != nil {
						t.Fatal(e)
					}
					directory = assets
					gameDir = temp
					expected = "scene original fingerprint: " + definition.file
				}
				p, e := loadHDSceneRuntime(&hdRuntime{m: golem.New()}, gameDir, directory)
				if e == nil || p != nil || !strings.Contains(e.Error(), expected) {
					t.Fatal("resource guard", kind, e)
				}
			})
		}
	}
}

func TestHDEventCursorTransparentBackground(t *testing.T) {
	m, p, _ := hdEventFixtureLoad(t, 1071, "")
	hdEventRun(t, m, p)
	source, known := p.h.cursorSource()
	if !known {
		t.Fatal("original cursor fingerprint")
	}
	k := -1
	for i, v := range source {
		if v == 255 {
			k = i
			break
		}
	}
	if k < 0 {
		t.Fatal("transparent cursor source")
	}
	pos := -1
	var cell hdSceneCell
	for at, c := range p.visible {
		if c.slot != 0 {
			pos = at
			cell = c
			break
		}
	}
	if pos < 0 {
		t.Fatal("source")
	}
	before := append([]byte(nil), m.Mem...)
	m.Mem[0xafa00+k] = cell.value
	m.Mem[0xafb00+k] = cell.value
	c := m.CPU
	c.Seg[golem.CS] = 0xb68
	c.IP = 0x51c
	c.Seg[golem.DS] = 0xa000
	c.Seg[golem.ES] = 0x2cae
	c.R[golem.SI] = uint16(0xfb00 + k)
	c.R[golem.DI] = uint16(pos)
	c.R[golem.CX] = 1
	c.Flags &^= 0x0600
	if e := m.Step(); e != nil {
		t.Fatal(e)
	}
	if p.visible[pos].slot != 0 || p.pending[pos].cell != cell {
		t.Fatal("actual cursor instruction did not save exact source")
	}
	x, y := pos%320-k%16, pos/320-k/16
	f := draftNativeFrame{mode: 0x13, canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], cursor: image.Rect(x, y, x+16, y+16)}
	under, yes := p.spriteCursorCell(pos, f)
	if !yes || under != cell {
		t.Fatal("verified transparent cursor lost HD background")
	}
	checkReject := func(name string, change func(), undo func()) {
		t.Helper()
		change()
		_, yes := p.spriteCursorCell(pos, f)
		undo()
		if yes {
			t.Fatal("unverified cursor background", name)
		}
	}
	pair := p.pending[pos]
	checkReject("wrong-index", func() { v := pair; v.k ^= 1; p.pending[pos] = v }, func() { p.pending[pos] = pair })
	checkReject("changed-buffer", func() { m.Mem[0xafa00+k] ^= 1 }, func() { m.Mem[0xafa00+k] ^= 1 })
	checkReject("changed-source", func() { m.Mem[0x1cd74] ^= 1 }, func() { m.Mem[0x1cd74] ^= 1 })
	checkReject("changed-Main", func() { m.Mem[hdBuildingCanvas+uint32(pos)] ^= 1 }, func() { m.Mem[hdBuildingCanvas+uint32(pos)] ^= 1 })
	checkReject("wrong-placement", func() { f.cursor = f.cursor.Add(image.Pt(1, 0)) }, func() { f.cursor = f.cursor.Sub(image.Pt(1, 0)) })
	// 合法還原仍由實際MOVSB寫回，不能由顯示函式恢復持有權。
	c.Seg[golem.CS] = 0xb68
	c.IP = 0x51c
	c.R[golem.SI] = uint16(0xfa00 + k)
	c.R[golem.DI] = uint16(pos)
	c.R[golem.CX] = 1
	if e := m.Step(); e != nil {
		t.Fatal(e)
	}
	if p.visible[pos] != cell || len(p.pending) != 0 {
		t.Fatal("cursor return did not restore source")
	}
	_ = before
}

func TestHDEventPaletteProjection(t *testing.T) {
	root := os.Getenv("TEST_HD_EVENT_ROOT")
	if root == "" {
		t.Skip("需要當次原版色盤")
	}
	for _, rid := range []int{1060, 1061, 1063, 1064, 1070, 1071, 1072, 1489, 1491, 1495, 1549} {
		t.Run(fmt.Sprint(rid), func(t *testing.T) {
			_, p, _ := hdEventFixtureLoad(t, rid, "")
			hdEventRun(t, p.h.m, p)
			step := 635085001
			if rid == 1491 {
				step = 766425001
			}
			if rid == 1495 {
				step = 907005001
			}
			palette, e := os.ReadFile(filepath.Join(root, "r97-full-normal-r3/observed", fmt.Sprintf("cp-%d.palette", step)))
			if rid >= 1060 && rid <= 1064 {
				dialogRoot := os.Getenv("TEST_HD_DIALOG_ROOT")
				if dialogRoot == "" {
					t.Fatal("explicit original MSS call receipt required")
				}
				raw, readErr := os.ReadFile(filepath.Join(dialogRoot, "r98-full-normal-original-r1/observed/r98-full-complete-calls.json"))
				if readErr != nil {
					t.Fatal(readErr)
				}
				if hash(raw) != "9cfe62a997185fa69a67c84726addc087cc4beda7527654634739c02e1471228" {
					t.Fatal("original MSS palette receipt fingerprint")
				}
				var calls []struct {
					ID      int    `json:"research_id"`
					Palette []byte `json:"entry_palette"`
				}
				if err := json.Unmarshal(raw, &calls); err != nil {
					t.Fatal(err)
				}
				palette = nil
				for _, call := range calls {
					if call.ID == rid {
						palette = call.Palette
						break
					}
				}
				if len(palette) != 768 {
					t.Fatal("original MSS used palette absent", rid)
				}
				e = nil
			}

			if e != nil {
				t.Fatal(e)
			}
			var frame *hdSceneFrame
			for _, f := range p.frames {
				if f.id == rid {
					frame = f
				}
			}
			if frame == nil || !frame.paletteSupported(palette) {
				t.Fatal("actual source palette")
			}
			changed := append([]byte(nil), palette...)
			changed[int(frame.indices[0])*3] ^= 1
			if frame.paletteSupported(changed) {
				t.Fatal("used palette mutation accepted")
			}
			changed = append([]byte(nil), palette...)
			changed[253*3] ^= 1
			if !frame.paletteSupported(changed) {
				t.Fatal("unused transparent palette index affected source")
			}
		})
	}
}

// 規格069 R98 READY。實際取樣與獨立Pillow逐RGBA比較。
func TestHDMSSFullProjectLoader(t *testing.T) {
	game, assets, output := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS"), os.Getenv("TEST_HD_MSS_PIXELS")
	if game == "" || assets == "" || output == "" {
		t.Skip("需要合法原版、正式素材與明確輸出目錄")
	}
	h, err := loadHDRuntime(golem.New(), game, assets)
	if err != nil {
		t.Fatal(err)
	}
	if h.scenes == nil || len(h.scenes.frames) != 276 {
		t.Fatal("four new sources and thirty inherited sources required")
	}
	seen := 0
	for _, f := range h.scenes.frames {
		if f.id != 1060 && f.id != 1061 && f.id != 1063 && f.id != 1064 {
			continue
		}
		w, height := f.sprite.width*4, f.sprite.height*4
		pixels := make([]byte, 0, w*height*4)
		for y := 0; y < height; y++ {
			pixels = append(pixels, f.art.Pix[y*f.art.Stride:y*f.art.Stride+w*4]...)
		}
		if err := os.WriteFile(filepath.Join(output, fmt.Sprintf("mss-%d.rgba", f.id)), pixels, 0644); err != nil {
			t.Fatal(err)
		}
		seen++
	}
	if seen != 4 {
		t.Fatal("missing verified MSS sources", seen)
	}
}
