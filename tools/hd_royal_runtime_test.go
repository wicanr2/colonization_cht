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

func hdRoyalFixtureRoots(t *testing.T) (game, assets, root, story, decoded string) {
	t.Helper()
	game = os.Getenv("TEST_GAME_ROOT")
	assets = os.Getenv("TEST_HD_ASSETS")
	root = os.Getenv("TEST_HD_ROYAL_ROOT")
	story = os.Getenv("TEST_HD_STORY_ROOT")
	decoded = os.Getenv("TEST_HD_DECODED_ROOT")
	if game == "" || assets == "" || root == "" || story == "" || decoded == "" {
		t.Skip("SKIP: legal original royal/story fixtures and raw HD assets required")
	}
	return
}
func hdRoyalSnapshot(t *testing.T, at int) (*hdRuntime, *hdSceneRuntime, draftNativeFrame) {
	t.Helper()
	game, assets, _, story, decoded := hdRoyalFixtureRoots(t)
	m := golem.New()
	h := &hdRuntime{m: m}
	p, e := loadHDSceneRuntime(h, game, assets)
	hdNewGameNeed(t, e)
	h.scenes = p
	for _, frame := range p.frames {
		if frame.id != 1002 {
			continue
		}
		raw := hdNewGameRead(t, filepath.Join(decoded, fmt.Sprintf("%04d.idx", frame.id)))
		base := frame.canvas
		if base == 0 {
			base = 0x3c500
		}
		copy(m.Mem[base:base+64000], raw)
		p.decodedAt(base, 0)
	}
	stem := fmt.Sprintf("point-%03d", at)
	dir := filepath.Join(story, "nation-story-source-probe-r3/observed")
	copy(m.Mem, hdNewGameRead(t, filepath.Join(dir, stem+".memory")))
	clear(p.visible[:])
	clear(p.published[:])
	for _, pair := range []struct {
		target *[64000]hdSceneCell
		suffix string
	}{{&p.visible, ".owners.json"}, {&p.published, ".published.json"}} {
		var cells map[string][]any
		hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(story, "nation-story-published-source-model-r4", stem+pair.suffix)), &cells))
		for key, c := range cells {
			pos, e := strconv.Atoi(key)
			hdNewGameNeed(t, e)
			slot := 0
			for i, frame := range p.frames {
				if frame.id == int(c[0].(float64)) {
					slot = i + 1
				}
			}
			if slot == 0 {
				t.Fatal("source", c)
			}
			pair.target[pos] = hdSceneCell{slot: uint16(slot), local: uint16(c[1].(float64)), value: byte(c[2].(float64)), glyph: c[3].(string) == "glyph"}
		}
	}
	var points []struct {
		Mouse struct{ X, Y int } `json:"dos_mouse"`
		Step  uint64             `json:"step"`
	}
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(story, "normal-nation-story-points-r1.json")), &points))
	v := points[at]
	f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: hdNewGameRead(t, filepath.Join(dir, stem+".idx")), palette: hdNewGameRead(t, filepath.Join(dir, stem+".palette")), cursor: image.Rect(v.Mouse.X, v.Mouse.Y, v.Mouse.X+16, v.Mouse.Y+16), mode: 0x13, step: v.Step}
	return h, p, f
}
func royalFixture(t *testing.T) (*hdRuntime, *hdRoyalRuntime, draftNativeFrame) {
	game, assets, root, _, decoded := hdRoyalFixtureRoots(t)
	h, _, f := hdRoyalSnapshot(t, 6)
	q, e := loadHDRoyalRuntime(h, game, assets)
	hdNewGameNeed(t, e)
	copy(q.source[:], hdNewGameRead(t, filepath.Join(decoded, "0992.idx")))
	q.before = hdNewGameRead(t, filepath.Join(root, "king-draw-native-r5/king.before.stage"))
	q.serial = 1
	q.ready = true
	q.accepted = 1
	var prior map[string][]any
	hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "king-prior-typed-background-r1/stage-owners-before-king.json")), &prior))
	for key, c := range prior {
		pos, e := strconv.Atoi(key)
		hdNewGameNeed(t, e)
		for n, frame := range h.scenes.frames {
			if frame.id == int(c[0].(float64)) {
				q.prior[pos] = hdSceneCell{slot: uint16(n + 1), local: uint16(c[1].(float64)), value: byte(c[2].(float64)), glyph: c[3].(string) == "glyph"}
				break
			}
		}
	}
	for local, v := range q.source {
		if v != 253 {
			pos := (local/189+12)*320 + local%189
			c := hdRoyalCell{1, uint16(local), v}
			q.stage[pos] = c
			q.main[pos] = c
			q.published[pos] = c
			q.counts[local] = 1
		}
	}
	return h, q, f
}
func royalSameWrite(t *testing.T, h *hdRuntime, dest uint16, pos int) {
	m := h.m
	m.CPU.Seg[golem.CS] = 0x1000
	m.CPU.IP = 0
	m.Mem[0x10000] = 0xaa
	m.CPU.Seg[golem.ES] = dest
	m.CPU.R[golem.DI] = uint16(pos)
	m.CPU.R[golem.AX] = uint16(m.Mem[uint32(dest)*16+uint32(pos)])
	m.CPU.Flags &^= 0x400
	hdNewGameNeed(t, m.Step())
}
func TestHDRoyalPoseGuards(t *testing.T) {
	for _, name := range []string{"known", "missing-publication", "wrong-local", "wrong-serial", "changed-index", "unknown-same-VGA", "late-main-write", "late-stage-write", "unknown-background", "prior-background-unknown", "palette", "short-index", "short-canvas", "wrong-mode", "blocked", "no-complete-call", "active-decoder", "rejected-generation"} {
		t.Run(name, func(t *testing.T) {
			h, q, f := royalFixture(t)
			pos := 12*320 + 102
			switch name {
			case "missing-publication":
				q.published[pos] = hdRoyalCell{}
			case "wrong-local":
				q.published[pos].local++
			case "wrong-serial":
				q.published[pos].serial++
			case "changed-index":
				f.indexed = bytes.Clone(f.indexed)
				f.indexed[pos] ^= 1
				copy(h.m.Mem[0xa0000:0xa0000+64000], f.indexed)
			case "unknown-same-VGA":
				royalSameWrite(t, h, 0xa000, pos)
			case "late-main-write":
				royalSameWrite(t, h, 0x2cae, pos)
			case "late-stage-write":
				royalSameWrite(t, h, 0x3c50, pos)
			case "unknown-background":
				h.scenes.published[12*320] = hdSceneCell{}
			case "prior-background-unknown":
				q.prior[pos] = hdSceneCell{}
			case "palette":
				f.palette = bytes.Clone(f.palette)
				for _, v := range q.source {
					if v != 253 {
						f.palette[int(v)*3] ^= 1
						break
					}
				}
			case "short-index":
				f.indexed = f.indexed[:63999]
			case "short-canvas":
				f.canvas = f.canvas[:63999]
			case "wrong-mode":
				f.mode = 3
			case "blocked":
				q.blocked = true
			case "active-decoder":
				q.active = true
			case "rejected-generation":
				q.ready = false
			case "no-complete-call":
				q.serial = 0
			}
			im := draftRGB(f.indexed, f.palette)
			if len(f.indexed) != 64000 {
				im = image.NewRGBA(image.Rect(0, 0, 1280, 800))
			}
			before := bytes.Clone(h.m.Mem)
			r := q.paint(im, f)
			if !bytes.Equal(before, h.m.Mem) {
				t.Fatal("native memory mutated")
			}
			accepted := name == "known" || name == "late-main-write" || name == "late-stage-write" || name == "unknown-background" || name == "prior-background-unknown"
			if (r["painted"].(int) > 0) != accepted {
				t.Fatal(name, r["reason"], r["painted"])
			}
			if name == "known" && (r["typed_background_restored"] != 11053 || r["native_underlay_restored"] != 877) {
				t.Fatal("typed restoration", r)
			}
			if name == "prior-background-unknown" && r["native_underlay_restored"] != 878 {
				t.Fatal("native underlay fallback", r)
			}
			if name == "unknown-background" {
				mask := r["mask"].([]byte)
				k := 12 * 320
				if mask[k>>3]>>(k&7)&1 != 0 {
					t.Fatal("unknown transparent foreground painted")
				}
			}
		})
	}
}
func TestHDRoyalEntryGuards(t *testing.T) {
	for _, name := range []string{"known", "wrong-code", "mirrored", "raw-scale", "raw-DX", "raw-Y", "descriptor", "dimensions", "encoded", "record-bounds"} {
		t.Run(name, func(t *testing.T) {
			_, _, root, _, _ := hdRoyalFixtureRoots(t)
			h, q, _ := royalFixture(t)
			copy(h.m.Mem, hdNewGameRead(t, filepath.Join(root, "king-draw-native-r5/decoder-entry.memory")))
			var entry struct {
				Registers [8]uint16 `json:"registers"`
				Segments  [4]uint16 `json:"segments"`
				Stack     [6]uint16 `json:"stack"`
				Record    [6]uint16 `json:"record"`
			}
			hdNewGameNeed(t, json.Unmarshal(hdNewGameRead(t, filepath.Join(root, "king-draw-native-r5/decoder-entry.json")), &entry))
			c := h.m.CPU
			c.R = entry.Registers
			c.Seg = entry.Segments
			c.Seg[golem.CS] = 0xd66
			c.IP = 4
			q.active = false
			stack := uint32(c.Seg[golem.SS])*16 + uint32(c.R[golem.SP])
			rec := uint32(entry.Stack[5])*16 + uint32(entry.Stack[4]) + 0x42
			desc := uint32(c.Seg[golem.DS])*16 + uint32(c.R[golem.BX])
			switch name {
			case "wrong-code":
				h.m.Mem[0xd660+4] ^= 1
			case "mirrored":
				c.R[golem.AX] |= 0x8000
			case "raw-scale":
				h.m.Mem[stack+4] = 99
			case "raw-DX":
				c.R[golem.DX]++
			case "raw-Y":
				h.m.Mem[stack+6]++
			case "descriptor":
				h.m.Mem[desc+2]++
			case "dimensions":
				h.m.Mem[rec+8]++
			case "encoded":
				h.m.Mem[uint32(entry.Record[1])*16+uint32(entry.Record[0])] ^= 1
			case "record-bounds":
				h.m.Mem[stack+8] = 0xff
				h.m.Mem[stack+9] = 0xff
			}
			before := bytes.Clone(h.m.Mem)
			q.beforeInstruction()
			if q.active != (name == "known") {
				t.Fatal(name, q.active)
			}
			if !bytes.Equal(before, h.m.Mem) {
				t.Fatal("entry changed original")
			}
		})
	}
}
func TestHDRoyalFinishGuards(t *testing.T) {
	for _, name := range []string{"known", "partial", "duplicate", "changed-write", "changed-stage", "outside"} {
		t.Run(name, func(t *testing.T) {
			h, q, _ := royalFixture(t)
			q.accepted = 0
			q.rejected = 0
			q.active = true
			switch name {
			case "partial":
				q.counts[102] = 0
			case "duplicate":
				q.counts[102] = 2
			case "changed-write":
				q.source[102] ^= 1
			case "changed-stage":
				h.m.Mem[0x3c500] ^= 1
			case "outside":
				q.bad = true
			}
			before := bytes.Clone(h.m.Mem)
			q.finish()
			if (q.accepted == 1) != (name == "known") {
				t.Fatal(name, q.accepted, q.rejected)
			}
			if !bytes.Equal(before, h.m.Mem) {
				t.Fatal("finish changed original")
			}
		})
	}
}
func TestHDRoyalCursorPairs(t *testing.T) {
	h, q, f := royalFixture(t)
	m := h.m
	f.cursor = image.Rect(102, 12, 118, 28)
	source, _ := h.cursorSource()
	for k, v := range source {
		pos := (12+k/16)*320 + 102 + k%16
		back := f.canvas[pos]
		m.Mem[0xafa00+k] = back
		if v == 255 {
			v = back
		}
		m.Mem[0xafb00+k] = v
	}
	code := []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}
	copy(m.Mem[0xb680+0x51c:], code)
	transfer := func(offset int) {
		for y := 0; y < 16; y++ {
			c := m.CPU
			c.Seg[golem.CS] = 0xb68
			c.IP = 0x51c
			c.Seg[golem.DS] = 0xa000
			c.Seg[golem.ES] = 0xa000
			c.R[golem.SI] = uint16(offset + y*16)
			c.R[golem.DI] = uint16((12+y)*320 + 102)
			c.R[golem.CX] = 16
			c.Flags &^= 0x400
			hdNewGameNeed(t, m.Step())
		}
		f.indexed = m.Indexed()
	}
	transfer(0xfb00)
	if len(q.publishedPending) == 0 {
		t.Fatal("no opaque cursor pairs")
	}
	im := draftRGB(f.indexed, f.palette)
	r := q.paint(im, f)
	if r["source_cells"] != 11930 || r["painted"].(int) == 0 {
		t.Fatal("cursor current pose", r)
	}
	transfer(0xfa00)
	if len(q.publishedPending) != 0 || q.cursorRestores == 0 {
		t.Fatal("restore pairs", len(q.publishedPending), q.cursorRestores)
	}
	r = q.paint(im, f)
	if r["source_cells"] != 11930 {
		t.Fatal("restored pose", r)
	}
	for name, pairs := range map[string]map[int]hdRoyalPair{"published": q.publishedPending, "main": q.pending} {
		if len(pairs) > 256 {
			t.Fatal(name, "unbounded")
		}
	}
}
func TestHDRoyalFixtureFullRGBA(t *testing.T) {
	_, _, root, _, _ := hdRoyalFixtureRoots(t)
	h, q, f := royalFixture(t)
	im, _ := h.base(f)
	r := q.paint(im, f)
	h.restoreCursor(im, f)
	if r["source_cells"] != 11930 {
		t.Fatal(r)
	}
	raw, e := os.Open(filepath.Join(root, "king1-visual-prototype-r2", "king1-hd.png"))
	hdNewGameNeed(t, e)
	defer raw.Close()
	expected, e := png.Decode(raw)
	hdNewGameNeed(t, e)
	for y := 0; y < 800; y++ {
		for x := 0; x < 1280; x++ {
			a := im.RGBAAt(x, y)
			r, g, b, z := expected.At(x, y).RGBA()
			if a.R != byte(r>>8) || a.G != byte(g>>8) || a.B != byte(b>>8) || a.A != byte(z>>8) {
				t.Fatal("full RGBA", x, y)
			}
		}
	}
}

func TestHDRoyalResources(t *testing.T) {
	game, assets, _, _, _ := hdRoyalFixtureRoots(t)
	m := golem.New()
	before := bytes.Clone(m.Mem)
	royal, e := loadHDRoyalRuntime(&hdRuntime{m: m}, game, assets)
	if e != nil || royal == nil || royal.art.Bounds() != image.Rect(0, 0, 756, 748) || !bytes.Equal(before, m.Mem) {
		t.Fatal("royal positive", e)
	}
	for _, name := range []string{"missing-art", "wrong-art", "symlink-art", "oversized-art", "wrong-KING1", "wrong-VICEROY", "missing-KING1"} {
		t.Run(name, func(t *testing.T) {
			tmp := t.TempDir()
			ga := filepath.Join(tmp, "game")
			ar := filepath.Join(tmp, "graphics")
			hdNewGameNeed(t, os.Mkdir(ga, 0755))
			hdNewGameNeed(t, os.Mkdir(ar, 0755))
			for _, file := range []string{"VICEROY.EXE", "KING1.SS"} {
				hdNewGameNeed(t, os.WriteFile(filepath.Join(ga, file), hdNewGameRead(t, filepath.Join(game, file)), 0644))
			}
			target := filepath.Join(ar, "king1-000.png")
			hdNewGameNeed(t, os.WriteFile(target, hdNewGameRead(t, filepath.Join(assets, "king1-000.png")), 0644))
			switch name {
			case "missing-art":
				hdNewGameNeed(t, os.Remove(target))
			case "wrong-art":
				hdNewGameNeed(t, os.WriteFile(target, []byte("wrong"), 0644))
			case "symlink-art":
				hdNewGameNeed(t, os.Remove(target))
				hdNewGameNeed(t, os.Symlink(filepath.Join(assets, "king1-000.png"), target))
			case "oversized-art":
				hdNewGameNeed(t, os.WriteFile(target, bytes.Repeat([]byte{0}, (8<<20)+1), 0644))
			case "wrong-KING1":
				hdNewGameNeed(t, os.WriteFile(filepath.Join(ga, "KING1.SS"), []byte("wrong"), 0644))
			case "wrong-VICEROY":
				hdNewGameNeed(t, os.WriteFile(filepath.Join(ga, "VICEROY.EXE"), []byte("wrong"), 0644))
			case "missing-KING1":
				hdNewGameNeed(t, os.Remove(filepath.Join(ga, "KING1.SS")))
			}
			m := golem.New()
			before := bytes.Clone(m.Mem)
			q, e := loadHDRoyalRuntime(&hdRuntime{m: m}, ga, ar)
			if e == nil || q != nil || !bytes.Equal(before, m.Mem) {
				t.Fatal("royal fault accepted", name, e)
			}
		})
	}
}
