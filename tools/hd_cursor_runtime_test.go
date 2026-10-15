package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"testing"

	golem "github.com/wicanr2/dosgolem"
)

// 這是既有正常原版快照的元件測試，不當作新正常GUI或新原版重播。
func TestHDCursorRuntimeActualFrames(t *testing.T) {
	game, assets, fixtures, receipts, out := os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_ASSETS"), os.Getenv("TEST_CURSOR_FRAMES"), os.Getenv("TEST_HD_RECEIPTS"), os.Getenv("TEST_CURSOR_OUTPUT")
	asset := filepath.Join(assets, "cursor-000.png")
	if game == "" || assets == "" || fixtures == "" || receipts == "" || out == "" {
		t.Skip("需要合法原版、正式素材與已驗原版49點快照")
	}
	for _, name := range []string{"VICEROY.EXE", "CURSOR.SS"} {
		if _, err := os.Stat(filepath.Join(game, name)); os.IsNotExist(err) {
			t.Skip("缺少合法原版", name)
		}
	}
	need := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	read := func(path string) []byte { t.Helper(); b, err := os.ReadFile(path); need(err); return b }
	if hash(read(filepath.Join(game, "VICEROY.EXE"))) != "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3" {
		t.Fatal("原版不同")
	}
	p, err := loadHDCursorRuntime(game, assets)
	need(err)
	pointBytes := read(filepath.Join(receipts, "lifecycle-public-r29-r1/observed/gui-points.json"))
	if hash(pointBytes) != "821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901" {
		t.Fatal("正常原版49點不同")
	}
	var points []struct {
		Step    uint64 `json:"step"`
		Count   int    `json:"dos_input_count"`
		Memory  string `json:"memory_sha256"`
		Indexed string `json:"indexed_sha256"`
		Palette string `json:"palette_sha256"`
	}
	need(json.Unmarshal(pointBytes, &points))
	if len(points) != 49 {
		t.Fatal("原版點數不同")
	}
	input := read(filepath.Join(receipts, "lifecycle-r29-r1/gui/gui.inputs.json"))
	if hash(input) != "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca" {
		t.Fatal("正常輸入不同")
	}
	var replay struct{ Inputs []windowInput }
	need(json.Unmarshal(input, &replay))
	if _, err := os.Stat(out); !os.IsNotExist(err) {
		t.Fatal("需要新輸出目錄")
	}
	need(os.Mkdir(out, 0755))
	var rows []map[string]any
	for i, point := range points {
		prefix := filepath.Join(fixtures, fmt.Sprintf("point-%03d", i))
		mem, indexed, palette := read(prefix+".memory"), read(prefix+".idx"), read(prefix+".palette")
		if hash(mem) != point.Memory || hash(indexed) != point.Indexed || hash(palette) != point.Palette {
			t.Fatal("原版快照不同", i)
		}
		m := golem.New()
		if len(mem) != len(m.Mem) {
			t.Fatal("原版RAM大小不同")
		}
		copy(m.Mem, mem)
		h := &hdRuntime{m: m}
		mouse := image.Point{}
		moved := false
		for _, e := range replay.Inputs[:point.Count] {
			if e.Kind == "move" {
				mouse = image.Pt(e.X, e.Y)
				moved = true
			}
		}
		if !moved {
			t.Fatal("未明示滑鼠位置")
		}
		f := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: indexed, palette: palette, cursor: image.Rect(mouse.X, mouse.Y, mouse.X+16, mouse.Y+16), mode: 0x13, step: point.Step}
		if _, reason := h.cursorProof(f); reason != "" {
			t.Fatal("原版游標證據未通過", i, reason)
		}
		original := draftRGB(f.indexed, f.palette)
		after := draftRGB(f.indexed, f.palette)
		h.restoreCursor(after, f)
		record := p.paint(h, after, f)
		if record["painted"] != 82 || record["source_cells"] != 82 {
			t.Fatal("候選未覆蓋所有來源格", i, record)
		}
		if !bytes.Equal(mem, m.Mem) {
			t.Fatal("合成改變原版RAM", i)
		}
		for suffix, im := range map[string]*image.RGBA{".before.png": original, ".after.png": after} {
			file, err := os.Create(filepath.Join(out, fmt.Sprintf("point-%03d", i)+suffix))
			need(err)
			need(png.Encode(file, im))
			need(file.Close())
		}
		record["point"], record["step"], record["mouse"], record["memory_sha256"] = i, point.Step, mouse, hash(m.Mem)
		rows = append(rows, record)
		if i == 4 {
			for _, test := range []struct {
				name   string
				change func(*hdRuntime, *draftNativeFrame)
			}{
				{"source", func(n *hdRuntime, g *draftNativeFrame) { n.m.Mem[0x1cd74] ^= 1 }},
				{"composition", func(n *hdRuntime, g *draftNativeFrame) { n.m.Mem[0xafb00] ^= 1 }},
				{"background", func(n *hdRuntime, g *draftNativeFrame) { n.m.Mem[0xafa00] ^= 1 }},
				{"mode", func(n *hdRuntime, g *draftNativeFrame) { g.mode = 3 }},
				{"size", func(n *hdRuntime, g *draftNativeFrame) { g.cursor.Max.X-- }},
				{"outside", func(n *hdRuntime, g *draftNativeFrame) { g.indexed[0] ^= 1 }},
			} {
				n := &hdRuntime{m: golem.New()}
				copy(n.m.Mem, m.Mem)
				g := f
				g.canvas = n.m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000]
				g.indexed = append([]byte(nil), f.indexed...)
				test.change(n, &g)
				before := draftRGB(g.indexed, g.palette)
				dst := draftRGB(g.indexed, g.palette)
				r := p.paint(n, dst, g)
				if r["painted"] != 0 || r["reason"] == nil || !bytes.Equal(before.Pix, dst.Pix) {
					t.Fatal("未拒絕不完整游標證據", test.name, r)
				}
			}
		}
	}
	scratch := t.TempDir()
	bad := filepath.Join(scratch, "bad")
	linked := filepath.Join(scratch, "linked")
	missing := filepath.Join(scratch, "missing")
	need(os.Mkdir(bad, 0755))
	need(os.Mkdir(linked, 0755))
	need(os.Mkdir(missing, 0755))
	raw := append([]byte(nil), read(asset)...)
	raw[len(raw)/2] ^= 1
	need(os.WriteFile(filepath.Join(bad, "cursor-000.png"), raw, 0644))
	need(os.Symlink(asset, filepath.Join(linked, "cursor-000.png")))
	for _, directory := range []string{bad, linked, missing, asset} {
		if _, err := loadHDCursorRuntime(game, directory); err == nil {
			t.Fatal("未拒絕錯誤游標素材", directory)
		}
	}
	for _, kind := range []string{"missing", "bad", "linked"} {
		directory := filepath.Join(scratch, "source-"+kind)
		need(os.Mkdir(directory, 0755))
		path := filepath.Join(directory, "CURSOR.SS")
		if kind == "bad" {
			need(os.WriteFile(path, []byte("damaged"), 0644))
		}
		if kind == "linked" {
			need(os.Symlink(filepath.Join(game, "CURSOR.SS"), path))
		}
		if _, err := loadHDCursorRuntime(directory, assets); err == nil {
			t.Fatal("未拒絕錯誤原版游標來源", kind)
		}
	}

	report := map[string]any{"result": "PASS_FORMAL_CURSOR_49_ORIGINAL_FRAME_COMPONENTS", "points": rows, "frame_guard_negatives": 6, "loader_negatives": 7, "original_ram_unchanged": true, "normal_gui_claim": false, "production_connected": true}
	data, err := json.MarshalIndent(report, "", "  ")
	need(err)
	need(os.WriteFile(filepath.Join(out, "check.json"), append(data, '\n'), 0644))
}
