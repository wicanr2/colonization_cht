package main

import (
	"bytes"
	"encoding/binary"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/png"
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
	t.Run("all885-scenes", func(t *testing.T) {
		m := golem.New()
		before := append([]byte(nil), m.Mem...)
		p, e := loadHDSceneRuntime(&hdRuntime{m: m}, game, assets)
		if e != nil || p == nil || len(p.frames) != 885 {
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
		if sprites != 856 {
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
					closing, e := os.ReadFile(filepath.Join(game, "CLOSING.EXE"))
					if e != nil {
						t.Fatal(e)
					}
					if e = os.WriteFile(filepath.Join(temp, "CLOSING.EXE"), closing, 0644); e != nil {
						t.Fatal(e)
					}
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
	if h.scenes == nil || len(h.scenes.frames) != 885 {
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

// 規格069 R124。來源記錄與游標條件由fixture提供，實際執行既有原版D46。
// 此項只授予正式素材載入與來源fixture顯示，不是正常BDARK玩家路徑。
func TestHDBDarkDisplay(t *testing.T) {
	game, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS")
	root, path, output := os.Getenv("TEST_HD_EVENT_FIXTURES"), os.Getenv("TEST_HD_BDARK_FIXTURE"), os.Getenv("TEST_HD_BDARK_OUTPUT")
	if game == "" || assets == "" || root == "" || path == "" || output == "" {
		t.Skip("需要合法原版、既有解碼器收據、BDARK來源fixture與新輸出")
	}
	read := func(path string) []byte {
		t.Helper()
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
		return b
	}
	raw := read(path)
	if hash(raw) != "fa884813b24ef8c1366f07947aaccc612b6decdc65c44ab8493067bf67ac7ede" {
		t.Fatal("BDARK fixture fingerprint")
	}
	var fixtures struct {
		Palette []byte
		Frames  []struct {
			ID              int
			Encoded, Pixels []byte
		}
	}
	if e := json.Unmarshal(raw, &fixtures); e != nil {
		t.Fatal(e)
	}
	if len(fixtures.Frames) != 45 || len(fixtures.Palette) != 768 {
		t.Fatal("BDARK fixture scope")
	}
	name := "r98-decoder-1061-2cae0.json"
	metadata := read(filepath.Join(root, name))
	expected, known := hdEventFixtureSHAs[name]
	if !known || hash(metadata) != expected[0] {
		t.Fatal("original decoder metadata")
	}
	var base hdEventFixture
	if e := json.Unmarshal(metadata, &base); e != nil {
		t.Fatal(e)
	}
	memory := read(filepath.Join(root, base.MemoryFile))
	if hash(memory) != expected[1] || hash(memory) != base.MemorySHA {
		t.Fatal("original decoder memory")
	}
	if e := os.Mkdir(output, 0755); e != nil {
		t.Fatal(e)
	}
	m := golem.New()
	empty := hash(m.Mem)
	h, e := loadHDRuntime(m, game, assets)
	if e != nil {
		t.Fatal(e)
	}
	if hash(m.Mem) != empty || h.scenes == nil || len(h.scenes.frames) != 885 {
		t.Fatal("full loader mutation or scope")
	}
	p := h.scenes
	records := []map[string]any{}
	images := map[int]string{}
	for _, fixture := range fixtures.Frames {
		t.Run(fmt.Sprint(fixture.ID), func(t *testing.T) {
			var selected *hdSceneFrame
			for _, frame := range p.frames {
				if frame.id == fixture.ID {
					selected = frame
					break
				}
			}
			if selected == nil || selected.file != "BDARK.SS" || selected.sprite == nil {
				t.Fatal("missing formal BDARK source")
			}
			s := selected.sprite
			if hash(fixture.Encoded) != s.encodedSHA || hash(fixture.Pixels) != s.indexedSHA {
				t.Fatal("source data fingerprint")
			}
			copy(m.Mem, memory)
			m.CPU.R, m.CPU.Seg = base.Entry.Registers, base.Entry.Segments
			m.CPU.IP, m.CPU.Flags, m.CPU.Cycles, m.Steps = 0xa, base.Flags&^0x0200, 0, base.Steps
			m.CPU.R[golem.AX], m.CPU.R[golem.DX] = uint16(s.ordinal+1), 40
			header := int(base.Entry.Stack[4])*16 + int(base.Entry.Stack[3])
			copy(m.Mem[0x70000:0x70036], memory[header:header+0x36])
			stack := int(m.CPU.Seg[golem.SS])*16 + int(m.CPU.R[golem.SP])
			word := func(at, n int, v uint16) { binary.LittleEndian.PutUint16(m.Mem[at+n*2:], v) }
			word(stack, 2, 40)
			word(stack, 3, 0)
			word(stack, 4, 0x7000)
			record := 0x70000 + 0x36 + int(m.CPU.R[golem.AX])*12
			for i, v := range []uint16{0x2000, 0x7000, s.nominal[0], s.nominal[1], uint16(s.width), uint16(s.height)} {
				word(record, i, v)
			}
			copy(m.Mem[0x72000:], fixture.Encoded)
			p.visible, p.stage, p.published = [64000]hdSceneCell{}, [64000]hdSceneCell{}, [64000]hdSceneCell{}
			p.backing, p.pending, p.publishedPending = map[uint32]hdSceneCell{}, map[int]hdSceneCursorPair{}, map[int]hdSceneCursorPair{}
			p.spriteCall, p.spriteAccepted, p.spriteRejected = nil, 0, 0
			hdEventRun(t, m, p)
			if p.spriteAccepted != 1 || p.spriteRejected != 0 || hash(selected.native) != selected.nativeSHA {
				t.Fatal("actual D46 source transaction", p.spriteAccepted, p.spriteRejected)
			}
			canvas := append([]byte(nil), m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000]...)
			source, valid := h.cursorSource()
			if !valid {
				t.Fatal("original cursor fixture source")
			}
			for k, v := range source {
				m.Mem[0xafa00+k] = 0
				if v == 255 {
					v = 0
				}
				m.Mem[0xafb00+k] = v
			}
			native := draftNativeFrame{mode: 0x13, canvas: canvas, indexed: append([]byte(nil), canvas...), palette: fixtures.Palette, cursor: image.Rect(-32, -32, -16, -16)}
			before := draftRGB(native.indexed, native.palette)
			out, info := h.baseExisting(native)
			scene, yes := info["scene_picture"].(map[string]any)
			if !yes {
				t.Fatal("integrated formal renderer", info)
			}
			state := scene["sources"].(map[string]any)[fmt.Sprint(fixture.ID)].(map[string]any)
			if state["painted"] != s.opaque || state["palette_supported"] != true {
				t.Fatal("formal source did not paint", state)
			}
			changed := 0
			for i := 0; i < len(out.Pix); i += 4 {
				if !bytes.Equal(out.Pix[i:i+4], before.Pix[i:i+4]) {
					changed++
				}
			}
			if changed == 0 {
				t.Fatal("HD source produced no visible pixels")
			}
			filename := filepath.Join(output, fmt.Sprintf("bdark-%03d.png", s.ordinal))
			f, e := os.Create(filename)
			if e != nil {
				t.Fatal(e)
			}
			e = png.Encode(f, out)
			closeErr := f.Close()
			if e != nil || closeErr != nil {
				t.Fatal(e, closeErr)
			}
			images[fixture.ID] = hash(out.Pix)
			records = append(records, map[string]any{"id": fixture.ID, "ordinal": s.ordinal, "file": filename, "asset": selected.asset, "opaque": s.opaque, "painted": state["painted"], "changed_HD_pixels": changed, "rgba_sha256": images[fixture.ID]})
		})
	}
	if len(records) != 45 || images[18] != images[19] {
		t.Fatal("all sources or original alias coverage", len(records))
	}
	result := map[string]any{"result": "PASS_BDARK45_PRODUCTION_SOURCE_FIXTURE_DISPLAY", "frames": records, "full_loader_scenes": 885, "fixture_sha256": hash(raw), "scope": "typed BDARK source records and offscreen cursor conditions with actual original D46 execution and integrated production renderer; no normal BDARK path or original-exact claim"}
	b, e := json.MarshalIndent(result, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(output, "check.json"), append(b, '\n'), 0644); e != nil {
		t.Fatal(e)
	}
}

func TestHDDeclarationGlyphDisplay(t *testing.T) {
	game, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS")
	root, path, output := os.Getenv("TEST_HD_EVENT_FIXTURES"), os.Getenv("TEST_HD_DEC_FIXTURE"), os.Getenv("TEST_HD_DEC_OUTPUT")
	if game == "" || assets == "" || root == "" || path == "" || output == "" {
		t.Skip("需要合法原版、既有解碼器收據、DEC來源fixture與新輸出")
	}
	read := func(path string) []byte {
		t.Helper()
		b, e := os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
		return b
	}
	raw := read(path)
	if hash(raw) != "20de6fcdb1b32eb94828a9f035ededce03fbc121abf8a5af00595afb1f2706d3" {
		t.Fatal("DEC fixture fingerprint")
	}
	var fixtures struct {
		Palette []byte
		Frames  []struct {
			ID              int
			Encoded, Pixels []byte
		}
	}
	if e := json.Unmarshal(raw, &fixtures); e != nil {
		t.Fatal(e)
	}
	if len(fixtures.Frames) != 452 || len(fixtures.Palette) != 768 {
		t.Fatal("DEC fixture scope")
	}
	name := "r98-decoder-1061-2cae0.json"
	metadata := read(filepath.Join(root, name))
	expected, known := hdEventFixtureSHAs[name]
	if !known || hash(metadata) != expected[0] {
		t.Fatal("original decoder metadata")
	}
	var base hdEventFixture
	if e := json.Unmarshal(metadata, &base); e != nil {
		t.Fatal(e)
	}
	memory := read(filepath.Join(root, base.MemoryFile))
	if hash(memory) != expected[1] || hash(memory) != base.MemorySHA {
		t.Fatal("original decoder memory")
	}
	if e := os.Mkdir(output, 0755); e != nil {
		t.Fatal(e)
	}
	m := golem.New()
	empty := hash(m.Mem)
	h, e := loadHDRuntime(m, game, assets)
	if e != nil {
		t.Fatal(e)
	}
	if hash(m.Mem) != empty || h.scenes == nil || len(h.scenes.frames) != 885 {
		t.Fatal("full loader mutation or scope")
	}
	p := h.scenes
	records := []map[string]any{}
	images := map[int]string{}
	for _, fixture := range fixtures.Frames {
		t.Run(fmt.Sprint(fixture.ID), func(t *testing.T) {
			var selected *hdSceneFrame
			for _, frame := range p.frames {
				if frame.id == fixture.ID {
					selected = frame
					break
				}
			}
			if selected == nil || !strings.HasPrefix(selected.file, "DEC-") || selected.sprite == nil {
				t.Fatal("missing formal DEC source")
			}
			s := selected.sprite
			if hash(fixture.Encoded) != s.encodedSHA || hash(fixture.Pixels) != s.indexedSHA {
				t.Fatal("source data fingerprint")
			}
			copy(m.Mem, memory)
			m.CPU.R, m.CPU.Seg = base.Entry.Registers, base.Entry.Segments
			m.CPU.IP, m.CPU.Flags, m.CPU.Cycles, m.Steps = 0xa, base.Flags&^0x0200, 0, base.Steps
			m.CPU.R[golem.AX], m.CPU.R[golem.DX] = uint16(s.ordinal+1), 40
			header := int(base.Entry.Stack[4])*16 + int(base.Entry.Stack[3])
			copy(m.Mem[0x70000:0x70036], memory[header:header+0x36])
			stack := int(m.CPU.Seg[golem.SS])*16 + int(m.CPU.R[golem.SP])
			word := func(at, n int, v uint16) { binary.LittleEndian.PutUint16(m.Mem[at+n*2:], v) }
			word(stack, 2, 40)
			word(stack, 3, 0)
			word(stack, 4, 0x7000)
			record := 0x70000 + 0x36 + int(m.CPU.R[golem.AX])*12
			for i, v := range []uint16{0x2000, 0x7000, s.nominal[0], s.nominal[1], uint16(s.width), uint16(s.height)} {
				word(record, i, v)
			}
			copy(m.Mem[0x72000:], fixture.Encoded)
			background := byte(0)
			brightness := -1
			for index := 0; index < 253; index++ {
				v := int(fixtures.Palette[index*3]) + int(fixtures.Palette[index*3+1]) + int(fixtures.Palette[index*3+2])
				if v > brightness {
					background, brightness = byte(index), v
				}
			}
			for pos := 0; pos < 64000; pos++ {
				m.Mem[hdBuildingCanvas+uint32(pos)] = background
			}
			p.visible, p.stage, p.published = [64000]hdSceneCell{}, [64000]hdSceneCell{}, [64000]hdSceneCell{}
			p.backing, p.pending, p.publishedPending = map[uint32]hdSceneCell{}, map[int]hdSceneCursorPair{}, map[int]hdSceneCursorPair{}
			p.spriteCall, p.spriteAccepted, p.spriteRejected = nil, 0, 0
			hdEventRun(t, m, p)
			if p.spriteAccepted != 1 || p.spriteRejected != 0 || hash(selected.native) != selected.nativeSHA {
				t.Fatal("actual D46 source transaction", p.spriteAccepted, p.spriteRejected)
			}
			canvas := append([]byte(nil), m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000]...)
			source, valid := h.cursorSource()
			if !valid {
				t.Fatal("original cursor fixture source")
			}
			for k, v := range source {
				m.Mem[0xafa00+k] = 0
				if v == 255 {
					v = 0
				}
				m.Mem[0xafb00+k] = v
			}
			native := draftNativeFrame{mode: 0x13, canvas: canvas, indexed: append([]byte(nil), canvas...), palette: fixtures.Palette, cursor: image.Rect(-32, -32, -16, -16)}
			before := draftRGB(native.indexed, native.palette)
			out, info := h.baseExisting(native)
			scene, yes := info["scene_picture"].(map[string]any)
			if !yes {
				t.Fatal("integrated formal renderer", info)
			}
			state := scene["sources"].(map[string]any)[fmt.Sprint(fixture.ID)].(map[string]any)
			if state["painted"] != s.opaque || state["palette_supported"] != true {
				t.Fatal("formal source did not paint", state)
			}
			changed := 0
			for yy := 0; yy < 800; yy++ {
				for xx := 0; xx < 1280; xx++ {
					a, b := out.RGBAAt(xx, yy), before.RGBAAt(xx, yy)
					sx, sy := xx/4-40, yy/4-40
					owned := sx >= 0 && sx < s.width && sy >= 0 && sy < s.height && fixture.Pixels[sy*s.width+sx] != 253
					if !owned && a != b {
						t.Fatal("outside original glyph outline", xx, yy)
					}
					if a.R > b.R || a.G > b.G || a.B > b.B {
						t.Fatal("native color modulation")
					}
					if a != b {
						changed++
					}
				}
			}
			if changed == 0 {
				t.Fatal("HD source produced no visible pixels")
			}
			filename := filepath.Join(output, fmt.Sprintf("declaration-%04d.png", fixture.ID))
			f, e := os.Create(filename)
			if e != nil {
				t.Fatal(e)
			}
			e = png.Encode(f, out)
			closeErr := f.Close()
			if e != nil || closeErr != nil {
				t.Fatal(e, closeErr)
			}
			images[fixture.ID] = hash(out.Pix)
			records = append(records, map[string]any{"id": fixture.ID, "ordinal": s.ordinal, "file": filename, "asset": selected.asset, "opaque": s.opaque, "painted": state["painted"], "changed_HD_pixels": changed, "rgba_sha256": images[fixture.ID]})
		})
	}
	if len(records) != 452 {
		t.Fatal("all452 source coverage", len(records))
	}
	result := map[string]any{"result": "PASS_DEC452_PRODUCTION_SOURCE_FIXTURE_DISPLAY", "frames": records, "full_loader_scenes": 885, "fixture_sha256": hash(raw), "scope": "typed DEC records, supplied light background and offscreen cursor conditions with actual original D46 execution and integrated Main HD renderer; native outlines/color ratios preserved; no normal declaration, Noto, translation or original-exact claim"}
	b, e := json.MarshalIndent(result, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(output, "check.json"), append(b, '\n'), 0644); e != nil {
		t.Fatal(e)
	}
}
