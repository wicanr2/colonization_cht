package main

import (
	"bytes"
	"encoding/json"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	golem "github.com/wicanr2/dosgolem"
)

type hdMiniMapSavedContext struct {
	MemorySHA  string `json:"memory_sha256"`
	IndexedSHA string `json:"indexed_sha256"`
	PaletteSHA string `json:"palette_sha256"`
	Rows       []struct {
		Kind  string          `json:"kind"`
		Step  uint64          `json:"step"`
		Ink   image.Rectangle `json:"ink"`
		After map[int]byte    `json:"after_pixels"`
		Runs  []struct {
			Raw    []byte          `json:"raw"`
			Box    image.Rectangle `json:"box"`
			Colors map[byte]int    `json:"colors"`
		} `json:"runs"`
	} `json:"visible_source_rows"`
}

func hdMiniMapNativeRGBA(f draftNativeFrame) *image.RGBA {
	im := image.NewRGBA(image.Rect(0, 0, 1280, 800))
	for y := 0; y < 200; y++ {
		for x := 0; x < 320; x++ {
			at := int(f.indexed[y*320+x]) * 3
			c := color.RGBA{f.palette[at]<<2 | f.palette[at]>>4, f.palette[at+1]<<2 | f.palette[at+1]>>4, f.palette[at+2]<<2 | f.palette[at+2]>>4, 255}
			for dy := 0; dy < 4; dy++ {
				for dx := 0; dx < 4; dx++ {
					im.SetRGBA(x*4+dx, y*4+dy, c)
				}
			}
		}
	}
	return im
}
func hdMiniMapCloneFrame(f draftNativeFrame) draftNativeFrame {
	f.canvas = bytes.Clone(f.canvas)
	f.buffer = bytes.Clone(f.buffer)
	f.indexed = bytes.Clone(f.indexed)
	f.palette = bytes.Clone(f.palette)
	if f.journal != nil {
		j := *f.journal
		j.items = nil
		for _, o := range f.journal.items {
			n := *o
			n.seaRuns = nil
			for _, r := range o.seaRuns {
				s := *r
				s.raw = bytes.Clone(r.raw)
				n.seaRuns = append(n.seaRuns, &s)
			}
			j.items = append(j.items, &n)
		}
		f.journal = &j
	}
	return f
}
func TestHDNativeMiniMapDisplay(t *testing.T) {
	root, game, assets := os.Getenv("TEST_HD_MINIMAP_FIXTURE"), os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS")
	if root == "" || game == "" || assets == "" || os.Getenv("TEST_HD_EVENT_FIXTURES") == "" {
		t.Skip("需合法原版、HD素材及既有正常GUI收據")
	}
	read := func(name, want string) []byte {
		t.Helper()
		b, e := os.ReadFile(filepath.Join(root, name))
		if e != nil {
			t.Fatal(e)
		}
		if want != "" && hash(b) != want {
			t.Fatal("fixture fingerprint", name)
		}
		return b
	}
	for _, name := range hdResourceOriginalFiles() {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版", name)
		}
	}
	raw := read("r140-minimap-visible-context-r1.json", "7457514cc6120c737415f95fe11fe2ea7aa2d6dc745a330ffaa94907d444cc8e")
	var context hdMiniMapSavedContext
	if e := json.Unmarshal(raw, &context); e != nil {
		t.Fatal(e)
	}
	if context.MemorySHA != "6925ad21a48c43ebfb7fa9625b09ea3ff7c144bf5f89f839cdb2e718512fe5d0" || context.IndexedSHA != "42da4cb45e40d8ac7f98389540aca32ad20642f05729f2328beaa62e6473f3e6" || context.PaletteSHA != "5ecdcd2c19fcae321e023247d51caaa7be8546d2c979110a174646b418be2cba" {
		t.Fatal("unreviewed context")
	}
	memory := read("r138-formal-gui-r1/gui.memory", context.MemorySHA)
	indexed := read("r138-formal-gui-r1/gui.final.idx", context.IndexedSHA)
	palette := read("r138-formal-gui-r1/gui.final.pal", context.PaletteSHA)
	m := golem.New()
	if len(memory) != len(m.Mem) {
		t.Fatal("RAM shape", len(memory), len(m.Mem))
	}
	copy(m.Mem, memory)
	h, e := loadHDRuntime(m, game, assets)
	if e != nil {
		t.Fatal(e)
	}
	if h.miniMapMaterial() == nil || len(h.scenes.frames) != 895 {
		t.Fatal("full reviewed HD loader/material", len(h.scenes.frames))
	}
	if !bytes.Equal(m.Mem, memory) {
		t.Fatal("resource load modified original RAM")
	}
	f := draftNativeFrame{canvas: bytes.Clone(memory[0x2cae0 : 0x2cae0+64000]), buffer: bytes.Clone(memory[0x3bb00 : 0x3bb00+64000]), indexed: indexed, palette: palette, cursor: image.Rect(16, 16, 32, 32), mode: 0x13, journal: &nativeJournal{enabled: true}}
	for _, r := range context.Rows {
		o := &nativeObservation{kind: r.Kind, step: r.Step, ink: r.Ink, after: r.After}
		for _, v := range r.Runs {
			o.seaRuns = append(o.seaRuns, &seaEvent{raw: v.Raw, bbox: v.Box, colors: v.Colors})
		}
		if !o.visible(f.canvas, f.buffer, f.indexed) {
			t.Fatal("source observation no longer visible", r.Kind, r.Ink)
		}
		f.journal.items = append(f.journal.items, o)
	}
	native := hdMiniMapNativeRGBA(f)
	painted := hdMiniMapNativeRGBA(f)
	record := h.paintNativeMiniMap(painted, f)
	if record["reason"] != "verified-native-world-minimap" || record["painted"] != 2378 || record["white_pixels"] != 50 {
		t.Fatal("original normal output was not painted", record)
	}
	changed, white := 0, 0
	for y := 0; y < 800; y++ {
		for x := 0; x < 1280; x++ {
			a, b := native.RGBAAt(x, y), painted.RGBAAt(x, y)
			in := image.Pt(x/4, y/4).In(hdMiniMapBounds)
			if !in && a != b {
				t.Fatal("changed outside minimap", x, y)
			}
			if in {
				if b.A != 255 {
					t.Fatal("revealed lower surface", x, y)
				}
				v := f.canvas[y/4*320+x/4]
				if v == 15 {
					if a != b {
						t.Fatal("viewport changed", x, y)
					}
					white++
				}
				if v == 0 && (b.R < 8 || b.R > 20 || b.R != b.G || b.R != b.B) {
					t.Fatal("unknown map not opaque charcoal", x, y, b)
				}
			}
			if a != b {
				changed++
			}
		}
	}
	if changed == 0 || white != 800 || record["changed_RGBA_points"] != changed {
		t.Fatal("display change/viewport accounting", record, changed, white)
	}
	pack := &draftPreparedBundle{}
	pack.manifest.Locale = "en"
	pack.manifest.Original = true
	target := &draftLanguageTarget{pack: pack}
	backend := &draftLanguageBackend{hd: h}
	original, _, e := backend.rebuildWithHD(target, displayOptions{Language: "en", Graphics: "original"}, f)
	if e != nil || !bytes.Equal(original.Pix, native.Pix) {
		t.Fatal("English original mode changed", e)
	}
	integrated, integratedRecord, e := backend.rebuildWithHD(target, displayOptions{Language: "en", Graphics: "hd"}, f)
	if e != nil {
		t.Fatal(e)
	}
	slot, known := hdOpeningSpriteSlot(1031)
	if !known {
		t.Fatal("material carrier slot")
	}
	savedArt := h.opening.sprites.art[slot]
	h.opening.sprites.art[slot] = nil
	baseline, _, e := backend.rebuildWithHD(target, displayOptions{Language: "en", Graphics: "hd"}, f)
	h.opening.sprites.art[slot] = savedArt
	if e != nil {
		t.Fatal(e)
	}
	integratedChanges := 0
	for y := 0; y < 800; y++ {
		for x := 0; x < 1280; x++ {
			a, b := baseline.RGBAAt(x, y), integrated.RGBAAt(x, y)
			if a != b {
				if !image.Pt(x/4, y/4).In(hdMiniMapBounds) {
					t.Fatal("integration modified another field", x, y)
				}
				integratedChanges++
			}
		}
	}
	if integratedChanges == 0 {
		t.Fatal("formal rebuild did not include minimap", integratedRecord)
	}
	before := bytes.Clone(m.Mem)
	cases := []struct {
		name, reason string
		change       func(*draftNativeFrame)
	}{
		{"wrong-mode", "native-shape", func(v *draftNativeFrame) { v.mode = 3 }},
		{"short-main", "native-shape", func(v *draftNativeFrame) { v.canvas = v.canvas[:10] }},
		{"short-palette", "native-shape", func(v *draftNativeFrame) { v.palette = v.palette[:10] }},
		{"used-color-changed", "native-palette", func(v *draftNativeFrame) { v.palette[6*3] ^= 1 }},
		{"missing-material", "material", func(v *draftNativeFrame) { h.opening.sprites.art[slot] = nil }},
		{"wrong-material-bounds", "material", func(v *draftNativeFrame) { h.opening.sprites.art[slot] = image.NewNRGBA(image.Rect(0, 0, 1, 1)) }},
		{"missing-journal", "world-context-or-text", func(v *draftNativeFrame) { v.journal = nil }},
		{"missing-world-menu", "world-context-or-text", func(v *draftNativeFrame) {
			for _, o := range v.journal.items {
				if o.kind == "sea-bar" {
					o.kind = "unknown"
				}
			}
		}},
		{"wrong-original-menu", "world-context-or-text", func(v *draftNativeFrame) {
			for _, o := range v.journal.items {
				if o.kind == "sea-bar" {
					o.seaRuns[0].raw[0] = 'X'
				}
			}
		}},
		{"missing-date", "world-context-or-text", func(v *draftNativeFrame) {
			for _, o := range v.journal.items {
				if o.kind == "sea-panel" {
					o.kind = "unknown"
				}
			}
		}},
		{"wrong-original-date", "world-context-or-text", func(v *draftNativeFrame) {
			for _, o := range v.journal.items {
				if o.kind == "sea-panel" && o.ink.Min == image.Pt(242, 51) {
					o.seaRuns[0].raw[len(o.seaRuns[0].raw)-2] = 'X'
				}
			}
		}},
		{"stale-world-menu", "world-context-or-text", func(v *draftNativeFrame) {
			for _, o := range v.journal.items {
				if o.kind == "sea-bar" {
					o.after = nil
				}
			}
		}},
		{"text-over-map", "world-context-or-text", func(v *draftNativeFrame) {
			pos := 10*320 + 253
			v.journal.items = append(v.journal.items, &nativeObservation{kind: "dialog", ink: image.Rect(253, 10, 254, 11), after: map[int]byte{pos: v.canvas[pos]}})
		}},
		{"different-visible-map", "visible-surface", func(v *draftNativeFrame) { v.indexed[10*320+253] ^= 1 }},
		{"unknown-cursor-on-map", "unverified-cursor", func(v *draftNativeFrame) { v.cursor = image.Rect(253, 10, 269, 26) }},
		{"incomplete-frame", "frame-incomplete", func(v *draftNativeFrame) { pos := 8*320 + 251; v.canvas[pos] = 0; v.indexed[pos] = 0 }},
		{"unknown-map-color", "unclassified-map-pixel", func(v *draftNativeFrame) { pos := 10*320 + 253; v.canvas[pos] = 200; v.indexed[pos] = 200 }},
		{"native-white-point-removed", "verified-native-world-minimap", func(v *draftNativeFrame) { pos := 22*320 + 287; v.canvas[pos] = 0; v.indexed[pos] = 0 }},
		{"native-white-points-absent", "verified-native-world-minimap", func(v *draftNativeFrame) {
			for i, b := range v.canvas {
				if image.Pt(i%320, i/320).In(hdMiniMapInterior) && b == 15 {
					v.canvas[i] = 0
					v.indexed[i] = 0
				}
			}
		}},
		{"extra-native-white-point", "verified-native-world-minimap", func(v *draftNativeFrame) { pos := 28*320 + 294; v.canvas[pos] = 15; v.indexed[pos] = 15 }},
		{"unknown-bitmap-owner", "bitmap-owner", func(v *draftNativeFrame) { h.scenes.visible[10*320+253] = hdSceneCell{slot: 65535} }},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			clone := hdMiniMapCloneFrame(f)
			tc.change(&clone)
			out := image.NewRGBA(native.Rect)
			copy(out.Pix, native.Pix)
			previous := bytes.Clone(out.Pix)
			if tc.reason == "verified-native-world-minimap" {
				out = hdMiniMapNativeRGBA(clone)
				previous = bytes.Clone(out.Pix)
			}

			r := h.paintNativeMiniMap(out, clone)
			h.opening.sprites.art[slot] = savedArt
			h.scenes.visible = [64000]hdSceneCell{}
			if tc.reason == "verified-native-world-minimap" {
				if r["reason"] != tc.reason || r["painted"] != 2378 || bytes.Equal(previous, out.Pix) {
					t.Fatal("native white variation blocked", r)
				}
				reference := hdMiniMapNativeRGBA(clone)
				for y := 8; y < 49; y++ {
					for x := 251; x < 309; x++ {
						if clone.canvas[y*320+x] == 15 {
							for dy := 0; dy < 4; dy++ {
								for dx := 0; dx < 4; dx++ {
									if out.RGBAAt(x*4+dx, y*4+dy) != reference.RGBAAt(x*4+dx, y*4+dy) {
										t.Fatal("original white point changed")
									}
								}
							}
						}
					}
				}
			} else if r["reason"] != tc.reason || r["painted"] != 0 || !bytes.Equal(previous, out.Pix) {
				t.Fatal("rejected input painted or wrong guard", r, tc.reason)
			}

		})
	}
	t.Run("unrelated-palette-change", func(t *testing.T) {
		clone := hdMiniMapCloneFrame(f)
		clone.palette[200*3] ^= 1
		out := hdMiniMapNativeRGBA(clone)
		r := h.paintNativeMiniMap(out, clone)
		if r["reason"] != "verified-native-world-minimap" {
			t.Fatal("unrelated palette blocked map", r)
		}
	})
	t.Run("existing-bitmap-preserved", func(t *testing.T) {
		// 既有合法D46收據在第二台隔離機器解碼；只借用經原生指紋核對的bitmap資料。
		dm, decoded, _ := hdEventFixtureLoad(t, 1060, "")
		hdEventRun(t, dm, decoded)
		var source *hdSceneFrame
		for _, fr := range decoded.frames {
			if fr.id == 1060 {
				source = fr
			}
		}
		if source == nil || len(source.native) == 0 || hash(source.native) != source.nativeSHA {
			t.Fatal("verified decoder owner unavailable")
		}
		sourceSlot := -1
		for i, fr := range h.scenes.frames {
			if fr.id == source.id {
				sourceSlot = i
			}
		}
		if sourceSlot < 0 {
			t.Fatal("source not loaded")
		}
		fr := h.scenes.frames[sourceSlot]
		previous := fr.native
		fr.native = bytes.Clone(source.native)
		defer func() { fr.native = previous; h.scenes.visible = [64000]hdSceneCell{} }()
		local := -1
		for i, v := range fr.native {
			if v == 0 {
				local = i
				break
			}
		}
		pos := 10*320 + 253
		if local < 0 || f.canvas[pos] != 0 {
			t.Fatal("shared black bitmap pixel unavailable")
		}
		h.scenes.visible[pos] = hdSceneCell{slot: uint16(sourceSlot + 1), local: uint16(local), value: 0}
		out := hdMiniMapNativeRGBA(f)
		r := h.paintNativeMiniMap(out, f)
		if r["painted"] != 2377 || r["bitmap_cells_preserved"] != 1 {
			t.Fatal("bitmap ownership not retained", r)
		}
		for dy := 0; dy < 4; dy++ {
			for dx := 0; dx < 4; dx++ {
				if out.RGBAAt(253*4+dx, 10*4+dy) != native.RGBAAt(253*4+dx, 10*4+dy) {
					t.Fatal("bitmap overwritten")
				}
			}
		}
	})

	if !bytes.Equal(m.Mem, before) || !bytes.Equal(memory, m.Mem) {
		t.Fatal("display modified original state")
	}
	if output := os.Getenv("TEST_HD_MINIMAP_OUTPUT"); output != "" {
		if e := os.MkdirAll(output, 0755); e != nil {
			t.Fatal(e)
		}
		for name, im := range map[string]*image.RGBA{"native.png": native, "minimap.png": painted, "integrated-hd.png": integrated, "integrated-original.png": original} {
			file, e := os.Create(filepath.Join(output, name))
			if e != nil {
				t.Fatal(e)
			}
			e = png.Encode(file, im)
			file.Close()
			if e != nil {
				t.Fatal(e)
			}
		}
		summary := map[string]any{"result": "PASS_NATIVE_MINIMAP_SOURCE_DISPLAY", "source_memory_sha256": hash(memory), "scene_frames_loaded": len(h.scenes.frames), "native_cells_painted": record["painted"], "changed_RGBA_points": changed, "viewport_RGBA_points_unchanged": white, "integrated_changed_RGBA_points": integratedChanges, "original_RAM_unchanged": true, "scope": "Renderer fixture from an existing normal GUI endpoint. No new normal-player-path or original-parity claim."}
		b, e := json.MarshalIndent(summary, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(output, "check.json"), append(b, '\n'), 0644); e != nil {
			t.Fatal(e)
		}
	}
}
