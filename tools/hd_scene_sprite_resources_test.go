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
	t.Run("all895-scenes", func(t *testing.T) {
		m := golem.New()
		before := append([]byte(nil), m.Mem...)
		p, e := loadHDSceneRuntime(&hdRuntime{m: m}, game, assets)
		if e != nil || p == nil || len(p.frames) != 895 {
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
		if sprites != 866 {
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
	if h.scenes == nil || len(h.scenes.frames) != 895 {
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
	if hash(m.Mem) != empty || h.scenes == nil || len(h.scenes.frames) != 895 {
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
	result := map[string]any{"result": "PASS_BDARK45_PRODUCTION_SOURCE_FIXTURE_DISPLAY", "frames": records, "full_loader_scenes": 895, "fixture_sha256": hash(raw), "scope": "typed BDARK source records and offscreen cursor conditions with actual original D46 execution and integrated production renderer; no normal BDARK path or original-exact claim"}
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
	if hash(m.Mem) != empty || h.scenes == nil || len(h.scenes.frames) != 895 {
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
	result := map[string]any{"result": "PASS_DEC452_PRODUCTION_SOURCE_FIXTURE_DISPLAY", "frames": records, "full_loader_scenes": 895, "fixture_sha256": hash(raw), "scope": "typed DEC records, supplied light background and offscreen cursor conditions with actual original D46 execution and integrated Main HD renderer; native outlines/color ratios preserved; no normal declaration, Noto, translation or original-exact claim"}
	b, e := json.MarshalIndent(result, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(output, "check.json"), append(b, '\n'), 0644); e != nil {
		t.Fatal(e)
	}
}

func TestHDGeometryMainDisplay(t *testing.T) {
	game, assets := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS")
	root, path, output := os.Getenv("TEST_HD_EVENT_FIXTURES"), os.Getenv("TEST_HD_GEOMETRY_MAIN_FIXTURE"), os.Getenv("TEST_HD_GEOMETRY_MAIN_OUTPUT")
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
	if hash(raw) != "ab3a9a72348c25532b1f64c5ce6d07480cdd01c3dfd9923d6c3b910f4c63ccb1" {
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
	if len(fixtures.Frames) != 8 || len(fixtures.Palette) != 768 {
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
	if hash(m.Mem) != empty || h.scenes == nil || len(h.scenes.frames) != 895 {
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
			if selected == nil || selected.file != "PHYS0.SS" || !selected.nativeGeometryMaterial || selected.sprite == nil {
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
					if owned && (a.R < 8 || a.R > 20 || a.R != a.G || a.G != a.B || a.A != 255) {
						t.Fatal("opaque charcoal geometry material")
					}
					if a != b {
						changed++
					}
				}
			}
			if changed == 0 {
				t.Fatal("HD source produced no visible pixels")
			}
			filename := filepath.Join(output, fmt.Sprintf("geometry-%04d.png", fixture.ID))
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
	if len(records) != 8 || images[1396] != images[1397] || images[1396] != images[1398] || images[1396] != images[1399] {
		t.Fatal("all8 geometry sources and shared native content", len(records))
	}
	result := map[string]any{"result": "PASS_R137_GEOMETRY8_MAIN_FIXTURE_DISPLAY", "frames": records, "full_loader_scenes": 895, "fixture_sha256": hash(raw), "scope": "Typed PHYS0 geometry, supplied light background and offscreen cursor, original D46 execution and integrated Main renderer. Fully opaque 8..20 charcoal material inside original geometry only; no normal world path, Noto, translation or original-exact claim."}
	b, e := json.MarshalIndent(result, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(output, "check.json"), append(b, '\n'), 0644); e != nil {
		t.Fatal(e)
	}
}

func TestHDGeometryClosingDisplay(t *testing.T) {
	fixturePath := os.Getenv("TEST_HD_GEOMETRY_CLOSING_FIXTURE")
	if fixturePath == "" {
		t.Skip("private original source fixtures required")
	}
	m := golem.New()
	if e := m.LoadEXE(hdOpeningRead(t, filepath.Join(os.Getenv("TEST_GAME_ROOT"), "CLOSING.EXE"))); e != nil {
		t.Fatal(e)
	}
	if !bytes.Equal(m.Mem[hdClosingSceneDrawPC:hdClosingSceneDrawPC+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		t.Fatal("actual MZ entry")
	}
	if (&hdTerrainTextureRuntime{}).validPublishedCell(hdSceneCell{slot: 257}) {
		t.Fatal("wide scene slot aliased a texture slot")
	}
	beforeLoad := hash(m.Mem)
	h, e := loadHDRuntime(m, os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS"))
	if e != nil {
		t.Fatal(e)
	}
	if hash(m.Mem) != beforeLoad {
		t.Fatal("loader changed DOS")
	}
	p := h.scenes
	if len(p.frames) != 895 {
		t.Fatal("scene source count")
	}
	for _, f := range p.frames {
		if f.sprite != nil && (f.art.Bounds().Dx() != f.sprite.width*4 || f.art.Bounds().Dy() != f.sprite.height*4 || len(f.native) != 0) {
			t.Fatal("sprite cache shape or early source arming", f.id)
		}
	}
	var ready struct {
		Palette []byte
		Frames  []struct {
			ID              int
			Encoded, Pixels []byte
		}
	}
	fixtureRaw := hdOpeningRead(t, fixturePath)
	if hash(fixtureRaw) != "ff27fb709b5abb5486000be3b87a1678d2748d3c0351a4048e63dbcfde22b565" {
		t.Fatal("geometry fixture fingerprint")
	}
	if e = json.Unmarshal(fixtureRaw, &ready); e != nil || len(ready.Frames) != 2 || len(ready.Palette) != 768 {
		t.Fatal("geometry fixture", e)
	}
	background := hdOpeningRead(t, "/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/0142.idx")
	var backgroundFrame *hdSceneFrame
	for _, f := range p.frames {
		if f.closingBackground {
			backgroundFrame = f
		}
	}
	if backgroundFrame == nil || hash(background) != backgroundFrame.nativeSHA {
		t.Fatal("closing background source")
	}
	out := os.Getenv("TEST_HD_GEOMETRY_CLOSING_OUTPUT")
	if e = os.Mkdir(out, 0755); e != nil {
		t.Fatal(e)
	}
	put := func(at int, words []uint16) {
		for i, v := range words {
			binary.LittleEndian.PutUint16(m.Mem[at+i*2:at+i*2+2], v)
		}
	}
	records, images := []map[string]any{}, []map[string]any{}
	const canvas uint32 = 0x70000
	for _, b := range ready.Frames {
		var f *hdSceneFrame
		slot := -1
		for i, frame := range p.frames {
			if frame.id == b.ID {
				f = frame
				slot = i
			}
		}
		if f == nil || f.sprite == nil || !f.sprite.closingContext || !f.nativeGeometryMaterial {
			t.Fatal("closing source", b.ID)
		}
		s := f.sprite
		clear(p.visible[:])
		clear(p.stage[:])
		clear(p.published[:])
		clear(p.backing)
		clear(p.pending)
		clear(p.publishedPending)
		copy(m.Mem[canvas:canvas+64000], background)
		native := b.Pixels
		encoded := b.Encoded
		copy(m.Mem[0x50000:], encoded)
		pal := ready.Palette
		x, y := (320-s.width)/2, (200-s.height)/2
		c := m.CPU
		c.Seg[golem.CS] = uint16(hdClosingSceneDrawPC >> 4)
		c.IP = uint16(hdClosingSceneDrawPC & 15)
		c.Seg[golem.DS] = 0x8800
		c.Seg[golem.SS] = 0x6800
		c.R[golem.SP] = 0x100
		c.R[golem.BX] = 0
		c.R[golem.AX] = uint16(s.ordinal + 1)
		c.R[golem.DX] = uint16(x)
		c.Flags = 2
		put(0x88000, []uint16{200, 320, 0, uint16(canvas >> 4)})
		put(0x68100, []uint16{0x2345, 0x3456, uint16(y), 0, 0x6000})
		put(0x60000+0x36+(s.ordinal+1)*12, []uint16{0, 0x5000, s.nominal[0], s.nominal[1], uint16(s.width), uint16(s.height)})
		m.Mem[hdClosingSceneDrawPC] ^= 1
		p.beforeSpriteInstruction()
		if p.spriteCall != nil {
			t.Fatal("code guard", f.id)
		}
		m.Mem[hdClosingSceneDrawPC] ^= 1
		m.Mem[0x50000] ^= 1
		p.beforeSpriteInstruction()
		if p.spriteCall != nil {
			t.Fatal("source guard", f.id)
		}
		m.Mem[0x50000] ^= 1
		p.beforeSpriteInstruction()
		if p.spriteCall == nil || p.spriteCall.slot != slot || p.spriteCall.canvas != canvas || !p.spriteCall.closingContext {
			t.Fatal("closing selector", f.id)
		}
		if len(backgroundFrame.native) != 64000 {
			t.Fatal("background capture", f.id)
		}
		for k, v := range native {
			if v == 253 {
				continue
			}
			writer := hdClosingSceneDrawPC + 0x177
			c.Seg[golem.CS] = uint16(writer >> 4)
			c.IP = uint16(writer & 15)
			c.Seg[golem.DS] = 0x5000
			c.Seg[golem.ES] = uint16(canvas >> 4)
			c.R[golem.SI] = 0
			c.R[golem.BX] = uint16((y+k/s.width)*320 + x + k%s.width)
			c.R[golem.AX] = uint16(v)
			if e = m.Step(); e != nil {
				t.Fatal(e)
			}
		}
		accepted := p.spriteAccepted
		c.Seg[golem.CS] = 0x3456
		c.IP = 0x2345
		c.R[golem.SP] = 0x10a
		p.beforeSpriteInstruction()
		if p.spriteAccepted != accepted+1 {
			t.Fatal("closing finish", f.id, p.spriteRejected)
		}
		for route, copyPC := range []int{0x2fb2, 0x48b3} {
			clear(p.published[:])
			clear(m.Mem[0xa0000:0xafa00])
			c.Seg[golem.CS] = uint16(copyPC >> 4)
			c.IP = uint16(copyPC & 15)
			endIP := c.IP + 2
			c.Seg[golem.DS] = uint16(canvas >> 4)
			c.Seg[golem.ES] = 0xa000
			c.R[golem.SI] = 0
			c.R[golem.DI] = 0
			c.R[golem.CX] = 32000
			c.Flags = 2
			for n := 0; c.IP != endIP; n++ {
				if n > 32001 {
					t.Fatal("copy bound")
				}
				if e = m.Step(); e != nil {
					t.Fatal(e)
				}
			}
			indexed := append([]byte(nil), m.Mem[0xa0000:0xafa00]...)
			frame := draftNativeFrame{canvas: append([]byte(nil), m.Mem[canvas:canvas+64000]...), indexed: indexed, palette: pal, mode: 19}
			im := draftRGB(indexed, pal)
			before := append([]byte(nil), im.Pix...)
			guest := hash(m.Mem)
			receipt := p.paintPublished(im, frame)
			if hash(m.Mem) != guest {
				t.Fatal("renderer changed DOS")
			}
			all := receipt["sources"].(map[string]any)
			rec := all[fmt.Sprint(f.id)].(map[string]any)
			bg := all[fmt.Sprint(backgroundFrame.id)].(map[string]any)
			if rec["painted"].(int) != s.opaque || bg["painted"].(int) != 64000-s.opaque {
				t.Fatal("published source counts", f.id, rec["painted"], bg["painted"])
			}
			changed := 0
			for i := 0; i < len(im.Pix); i += 4 {
				if string(im.Pix[i:i+3]) != string(before[i:i+3]) {
					changed++
				}
			}
			if changed < 100 {
				t.Fatal("not visible", f.id, changed)
			}
			actorChanged := 0
			for k, v := range native {
				if v == 253 {
					continue
				}
				for dy := 0; dy < 4; dy++ {
					for dx := 0; dx < 4; dx++ {
						at := (y+k/s.width)*4 + dy
						ix := (x+k%s.width)*4 + dx
						off := im.PixOffset(ix, at)
						if !bytes.Equal(im.Pix[off:off+3], before[off:off+3]) {
							actorChanged++
						}
					}
				}
			}
			if actorChanged == 0 {
				t.Fatal("actor art invisible", f.id)
			}
			name := fmt.Sprintf("closing-%04d-copy%d.png", f.id, route)
			fd, e := os.Create(filepath.Join(out, name))
			if e != nil {
				t.Fatal(e)
			}
			e = png.Encode(fd, im)
			fd.Close()
			if e != nil {
				t.Fatal(e)
			}
			badpal := append([]byte(nil), pal...)
			badpal[int(f.indices[0])*3] ^= 1
			badframe := frame
			badframe.palette = badpal
			bad := p.paintPublished(draftRGB(indexed, badpal), badframe)
			if bad["sources"].(map[string]any)[fmt.Sprint(f.id)].(map[string]any)["painted"].(int) != 0 {
				t.Fatal("palette guard", f.id)
			}
			item := map[string]any{"source": f.id, "file": f.file, "ordinal": s.ordinal, "image": name, "copy_linear": copyPC, "painted_cells": rec["painted"], "background_painted_cells": bg["painted"], "changed_HD_pixels": changed, "changed_actor_pixels": actorChanged, "native_source_size": []int{s.width, s.height}, "fixture_origin": []int{x, y}, "guest_RAM_unchanged_by_renderer": true, "rgba_sha256": hash(im.Pix)}
			images = append(images, item)
			if route == 0 {
				records = append(records, item)
			}
		}
	}
	if len(records) != 2 || len(images) != 4 {
		t.Fatal("source count")
	}
	raw, e := json.MarshalIndent(map[string]any{"result": "PASS_R137_CLOSING2_TWO_COPIES_DISPLAY", "sources": records, "images": images, "existing_background_source": 142, "scope": "pinned CLOSING MZ image loaded in dosgolem; production source selector and full-source finish, actual original store and two publication opcodes, existing background capture and published renderer; SS arguments, source values and return state supplied by fixtures", "normal_player_path_claim": false, "original_exact_parity_claim": false}, "", "  ")
	if e != nil {
		t.Fatal(e)
	}
	if e = os.WriteFile(filepath.Join(out, "check.json"), append(raw, '\n'), 0644); e != nil {
		t.Fatal(e)
	}
}
