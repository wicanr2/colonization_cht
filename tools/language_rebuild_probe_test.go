package main

import (
	"bytes"
	"encoding/json"
	"image"
	"image/color"
	"os"
	"strings"
	"testing"
)

func TestDraftRebuildRequiresWholeSafeArea(t *testing.T) {
	canvas := make([]byte, 64000)
	vga := bytes.Clone(canvas)
	safe, cursor := image.Rect(20, 20, 50, 40), image.Rect(22, 22, 24, 24)
	if !draftSameExceptCursor(vga, canvas, safe, cursor) {
		t.Fatal("identical native frame rejected")
	}
	vga[22*320+22] = 15
	if !draftSameExceptCursor(vga, canvas, safe, cursor) {
		t.Fatal("cursor pixel rejected")
	}
	vga[21*320+21] = 15
	if draftSameExceptCursor(vga, canvas, safe, cursor) {
		t.Fatal("changed background outside source ink accepted")
	}
	if draftSameExceptCursor(vga[:100], canvas, safe, cursor) || draftSameExceptCursor(canvas, canvas, image.Rect(-1, 0, 4, 4), cursor) {
		t.Fatal("unsafe frame accepted")
	}
}

func TestDraftFixedActualBundleMasks(t *testing.T) {
	root := os.Getenv("DRAFT_BUNDLE_ROOT")
	if root == "" {
		t.Skip("需明確指定本機完整Noto候選包")
	}
	needs, err := draftTargetRequirements(root)
	if err != nil {
		t.Fatal(err)
	}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			pack, err := draftPrepareBundle(os.DirFS(root), locale, needs)
			if err != nil {
				t.Fatal(err)
			}
			fixed, err := draftPrepareFixed(pack, needs)
			if err != nil || len(fixed) != 64 {
				t.Fatal("complete fixed preparation failed", err)
			}
			for _, f := range fixed {
				if f.text == "" || f.size <= 0 || f.safe.Empty() || (f.alpha == nil) == (f.normal == nil) {
					t.Fatal("incomplete typed fixed mask", f.id)
				}
			}
			name := "menu/GAME.TXT-0x000001B0.json"
			var mask draftFixedJSON
			if err = json.Unmarshal(pack.files["masks/"+name], &mask); err != nil {
				t.Fatal(err)
			}
			mask.Translation = strings.Repeat("0", 64)
			if _, err = draftFixedText(pack, needs.Masks[name], "menu", mask); err == nil {
				t.Fatal("wrong displayed text hash accepted")
			}
			if err = json.Unmarshal(pack.files["masks/"+name], &mask); err != nil {
				t.Fatal(err)
			}
			mask.Keys = []string{"unreviewed-native-key"}
			if _, err = draftFixedText(pack, needs.Masks[name], "menu", mask); err == nil {
				t.Fatal("missing source key accepted")
			}
		})
	}
}

func TestDraftFixedPaintUsesMeasuredPositionAndNativeGuards(t *testing.T) {
	before := bytes.Repeat([]byte{1}, 64000)
	canvas := bytes.Clone(before)
	i := 21*320 + 21
	canvas[i] = 68
	safe := image.Rect(20, 20, 50, 40)
	j := &nativeJournal{enabled: true}
	def := nativeFixed{id: "fixed-key", safe: safe, foreground: 68, shade: 47, shadow: image.Pt(4, 4), buttonGuard: true, mouseRule: "target-ink"}
	if !j.captureFixed(def, before, canvas, canvas, 1) {
		t.Fatal("source rejected")
	}
	alpha := image.NewAlpha(image.Rect(0, 0, 2, 2))
	alpha.SetAlpha(0, 0, color.Alpha{255})
	mask := &draftFixedMask{id: def.id, text: "display fixture", safe: safe, position: image.Pt(100, 96), size: 24, alpha: alpha}
	palette := make([]byte, 768)
	palette[68*3] = 63
	palette[47*3+1] = 63
	paint := func(vga []byte, cursor image.Rectangle) (*image.RGBA, map[string]any, string) {
		im := draftRGB(vga, palette)
		record, why := draftPaintFixed(im, mask, j.items[0], j, canvas, vga, palette, cursor)
		return im, record, why
	}
	im, record, why := paint(canvas, image.Rectangle{})
	if record == nil || why != "" || im.RGBAAt(100, 96) != draftColor(68, palette) || im.RGBAAt(104, 100) != draftColor(47, palette) || im.RGBAAt(84, 84) != draftColor(1, palette) {
		t.Fatal("measured target position, native erase or shadow lost", why)
	}
	unchanged := bytes.Clone(canvas)
	j.buttons = true
	if _, record, why = paint(canvas, image.Rectangle{}); record != nil || why != "fixed-button-held" {
		t.Fatal("held button accepted", why)
	}
	j.buttons = false
	if _, record, why = paint(canvas, image.Rect(25, 24, 41, 40)); record != nil || why != "fixed-cursor-over-field" {
		t.Fatal("cursor over target ink accepted", why)
	}
	vga := bytes.Clone(canvas)
	vga[20*320+20] = 2
	if _, record, why = paint(vga, image.Rectangle{}); record != nil || why != "fixed-vga-safe-changed" {
		t.Fatal("changed VGA background accepted", why)
	}
	mask.position = image.Pt(199, 159)
	if _, record, why = paint(canvas, image.Rectangle{}); record != nil || why != "fixed-ink-out-of-bounds" {
		t.Fatal("oversize target accepted", why)
	}
	if !bytes.Equal(canvas, unchanged) {
		t.Fatal("fixed rebuild mutated native state")
	}
}

func TestDraftFixedLayeredColorsPreserved(t *testing.T) {
	before := make([]byte, 64000)
	canvas := bytes.Clone(before)
	canvas[11*320+11] = 68
	j := &nativeJournal{enabled: true}
	def := draftFixedLayered("layered-key", image.Rect(10, 10, 20, 20))
	if !j.captureFixed(def, before, canvas, canvas, 1) {
		t.Fatal("source rejected")
	}
	makeLayer := func(x int) *image.Alpha {
		m := image.NewAlpha(image.Rect(0, 0, 40, 40))
		m.SetAlpha(x, 0, color.Alpha{255})
		return m
	}
	mask := &draftFixedMask{id: def.id, text: "layered fixture", safe: def.safe, position: image.Pt(40, 40), size: 28, shadow: makeLayer(0), normal: makeLayer(1), accent: makeLayer(2)}
	palette := make([]byte, 768)
	palette[47*3] = 63
	palette[68*3+1] = 63
	palette[149*3+2] = 63
	im := draftRGB(canvas, palette)
	if record, why := draftPaintFixed(im, mask, j.items[0], j, canvas, canvas, palette, image.Rectangle{}); record == nil || why != "" {
		t.Fatal("layered mask rejected", why)
	}
	for x, ink := range []byte{47, 68, 149} {
		if im.RGBAAt(40+x, 40) != draftColor(ink, palette) {
			t.Fatal("native layer color lost", x, ink)
		}
	}
	mask.alpha = mask.normal
	mask.normal = nil
	if record, why := draftPaintFixed(im, mask, j.items[0], j, canvas, canvas, palette, image.Rectangle{}); record != nil || why != "fixed-field-binding" {
		t.Fatal("layered identity accepted flat glyph", why)
	}
}

func TestDraftEnglishRebuildUsesNativePixels(t *testing.T) {
	canvas, buffer, vga, palette := make([]byte, 64000), make([]byte, 64000), make([]byte, 64000), make([]byte, 768)
	vga[6430], palette[3], palette[4], palette[5] = 1, 63, 32, 16
	target := &draftLanguageTarget{pack: &draftPreparedBundle{manifest: draftBundleManifest{Locale: "en", Original: true}}}
	before := bytes.Join([][]byte{canvas, buffer, vga, palette}, nil)
	im, record, err := draftRebuildTarget(target, &nativeJournal{}, canvas, buffer, vga, palette, image.Rectangle{}, 123, 0x13)
	if err != nil || im.Rect != image.Rect(0, 0, 1280, 800) || record["step"] != uint64(123) {
		t.Fatal("native English rebuild failed", err)
	}
	if im.RGBAAt(30*4, 20*4) != draftColor(1, palette) || im.RGBAAt(31*4, 20*4) != draftColor(0, palette) {
		t.Fatal("native pixel position or DAC changed")
	}
	if !bytes.Equal(before, bytes.Join([][]byte{canvas, buffer, vga, palette}, nil)) {
		t.Fatal("native state mutated")
	}
	if _, _, err = draftRebuildTarget(target, &nativeJournal{}, canvas[:100], buffer, vga, palette, image.Rectangle{}, 123, 0x13); err == nil {
		t.Fatal("truncated frame accepted")
	}
}

func TestDraftDialogRebuildExpiresChangedBackground(t *testing.T) {
	canvas := make([]byte, 64000)
	st := &dialogShown{safe: image.Rect(20, 20, 50, 40), phase: "active", afterSafe: rectBytes(canvas, image.Rect(20, 20, 50, 40))}
	d := &dialogRuntime{cur: st}
	draftExpireRebuilt(d, canvas)
	if st.phase != "active" {
		t.Fatal("unchanged complete safe area expired")
	}
	canvas[21*320+21] = 15
	draftExpireRebuilt(d, canvas)
	if st.phase != "expired" {
		t.Fatal("changed background retained old dialog")
	}
}

// 自建字模只驗欄位縮字及失敗分支，不作原版或Noto排版證據。
func draftSeaTestFonts() *seaState {
	st := &seaState{fonts: map[int]*seaFont{}}
	for size := 15; size <= 22; size++ {
		f := &seaFont{glyphs: map[rune]*image.Alpha{}, widths: map[rune]int{}, height: 5}
		for _, r := range "()GVORTCZ" {
			mask := image.NewAlpha(image.Rect(0, 0, size, 5))
			mask.SetAlpha(0, 0, color.Alpha{255})
			f.glyphs[r], f.widths[r] = mask, size
		}
		st.fonts[size] = f
	}
	return st
}

func TestDraftSeaMenuMeasuresEachNativeSlot(t *testing.T) {
	st := draftSeaTestFonts()
	for _, key := range "GVORTC" {
		st.menu = append(st.menu, "("+string(key)+")\x00Z")
	}
	var runs []*seaEvent
	xs := []int{13, 34, 77, 115, 157, 255}
	k := 0
	for word, count := range seaMenuWords {
		for n := 0; n < count; n++ {
			runs = append(runs, &seaEvent{raw: []byte{seaMenuText[k], 0}, bbox: image.Rect(xs[word]+n*3, 1, xs[word]+n*3+2, 6),
				firstOld: map[int]byte{320 + xs[word] + n*3: 1}, lastVal: map[int]byte{320 + xs[word] + n*3: 68}})
			k++
		}
	}
	row, why := draftSeaMenu(st, runs)
	if why != "" || row == nil || len(row.parts) != 12 || row.parts[0].size != 20 || row.parts[2].size != 22 {
		t.Fatal("native slot widths not measured independently", row, why)
	}
	if row.parts[0].color != 149 || row.parts[1].color != 68 || row.parts[1].x != row.parts[0].x+60 {
		t.Fatal("hotkey color or measured advance lost")
	}
	if _, why = draftSeaMenu(st, runs[:len(runs)-1]); why != "incomplete-menu" {
		t.Fatal("partial menu accepted", why)
	}
	runs[0].raw[0] = 'X'
	if _, why = draftSeaMenu(st, runs); why != "menu-source-mismatch" {
		t.Fatal("different native menu accepted", why)
	}
	runs[0].raw[0] = 'G'
	st.menu[0] = "(G)\x00" + strings.Repeat("Z", 100)
	if _, why = draftSeaMenu(st, runs); why != "menu-does-not-fit" {
		t.Fatal("oversize menu accepted", why)
	}
}

func TestDraftSeaPaintRequiresSourceAndWholeSafeArea(t *testing.T) {
	st := draftSeaTestFonts()
	canvas := bytes.Repeat([]byte{1}, 64000)
	i := 51*320 + 242
	canvas[i] = 68
	ink := image.Rect(242, 51, 251, 57)
	o := &nativeObservation{kind: "sea-panel", ink: ink, canvas: bytes.Clone(canvas), after: map[int]byte{i: 68}}
	row := &seaRow{bbox: ink, text: "source", parts: []seaPart{{"Z", 68, 968, 22}}, firstOld: map[int]byte{i: 1}, lastVal: map[int]byte{i: 68}}
	candidate := &draftSeaRow{o, row, seaPanelRect}
	palette := make([]byte, 768)
	palette[68*3] = 63
	before := bytes.Clone(canvas)
	im := draftRGB(canvas, palette)
	record, why := draftPaintSea(im, st, candidate, canvas, canvas, palette, image.Rectangle{})
	if record == nil || why != "" || record["text"] != "Z" {
		t.Fatal("valid sea row rejected", why)
	}
	if !bytes.Equal(canvas, before) {
		t.Fatal("sea rebuild mutated native pixels")
	}
	canvas[i] = 2
	if record, why = draftPaintSea(im, st, candidate, canvas, canvas, palette, image.Rectangle{}); record != nil || why != "sea-source-changed" {
		t.Fatal("overwritten source accepted", why)
	}
	canvas[i] = 68
	canvas[i+1] = 2
	if record, why = draftPaintSea(im, st, candidate, canvas, canvas, palette, image.Rectangle{}); record != nil || why != "sea-safe-changed" {
		t.Fatal("changed safe background accepted", why)
	}
	canvas[i+1] = 1
	vga := bytes.Clone(canvas)
	vga[i+1] = 2
	if record, why = draftPaintSea(im, st, candidate, canvas, vga, palette, image.Rectangle{}); record != nil || why != "sea-safe-changed" {
		t.Fatal("VGA obstruction accepted", why)
	}
	if record, why = draftPaintSea(im, st, candidate, canvas, vga, palette, image.Rect(243, 51, 244, 52)); record == nil || why != "" {
		t.Fatal("known cursor rejected", why)
	}
	row.firstOld[i] = 149
	if record, why = draftPaintSea(im, st, candidate, canvas, canvas, palette, image.Rectangle{}); record != nil || why != "sea-source-background" {
		t.Fatal("text-colored background erased", why)
	}
}
