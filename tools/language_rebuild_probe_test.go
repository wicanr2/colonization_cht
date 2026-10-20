package main

import (
	"bytes"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDraftSlotReprintRequiresIntactSourceTitle(t *testing.T) {
	fixture := func(rows int) (*dialogRuntime, *dialogRun, []byte) {
		canvas := make([]byte, 64000)
		title := &dialogShown{id: "GAME.TXT:0x00000826", phase: "active", safe: image.Rect(1, 1, 5, 5)}
		title.afterSafe = rectBytes(canvas, title.safe)
		d := &dialogRuntime{cur: &dialogShown{id: "STRING:save-slot+list", phase: "expired"}, prev: title}
		r := &dialogRun{readPos: rows * 4}
		for row := 0; row < rows; row++ {
			r.chars = append(r.chars, dialogChar{c: 'A', box: image.Rect(10, 10+row*6, 13, 15+row*6)},
				dialogChar{c: 'B', box: image.Rect(14, 10+row*6, 17, 15+row*6)})
		}
		return d, r, canvas
	}
	for _, rows := range []int{8, 10} {
		d, r, canvas := fixture(rows)
		context := draftDialogContext(d, r, canvas)
		if context == d || context.cur != d.prev || context.prev != nil || d.cur.phase != "expired" {
			t.Fatal("完整重印未借用原版標題，或復活了舊清單", rows)
		}
	}
	for name, damage := range map[string]func(*dialogRuntime, *dialogRun, []byte){
		"other title":   func(d *dialogRuntime, _ *dialogRun, _ []byte) { d.prev.id = "OTHER" },
		"expired title": func(d *dialogRuntime, _ *dialogRun, _ []byte) { d.prev.phase = "expired" },
		"changed title": func(_ *dialogRuntime, _ *dialogRun, c []byte) { c[321] = 1 },
		"other list":    func(d *dialogRuntime, _ *dialogRun, _ []byte) { d.cur.id = "STRING:line+list" },
		"pending read":  func(_ *dialogRuntime, r *dialogRun, _ []byte) { r.readPos-- },
		"wrong rows":    func(_ *dialogRuntime, r *dialogRun, _ []byte) { r.chars = r.chars[:18] },
		"title overlap": func(_ *dialogRuntime, r *dialogRun, _ []byte) { r.chars[0].box = image.Rect(1, 1, 4, 4) },
	} {
		t.Run(name, func(t *testing.T) {
			d, r, canvas := fixture(10)
			damage(d, r, canvas)
			if draftDialogContext(d, r, canvas) != d || d.cur.phase != "expired" {
				t.Fatal("失效來源借用插槽身份或復活舊清單")
			}
		})
	}
}

func TestDraftSlotPaintBoundsPreservesNativeClipping(t *testing.T) {
	safe := image.Rect(10, 10, 18, 18)
	fixture := func() (*nativeObservation, *image.Alpha, []byte, []byte) {
		canvas := make([]byte, 64000)
		o := &nativeObservation{after: map[int]byte{}, dialogRun: &dialogRun{chars: []dialogChar{
			{c: 'A', box: image.Rect(11, 11, 12, 14)}, {c: 'B', box: image.Rect(15, 11, 16, 14)},
		}}}
		for _, p := range []image.Point{{11, 11}, {11, 13}, {15, 11}, {15, 13}} {
			pos := p.Y*320 + p.X
			o.after[pos], canvas[pos] = 68, 68
		}
		indexed := bytes.Clone(canvas)
		indexed[13*320+11], indexed[13*320+15] = 5, 5
		mask := image.NewAlpha(image.Rect(0, 0, 32, 32))
		for y := 4; y < 12; y++ {
			for x := 4; x < 24; x++ {
				mask.SetAlpha(x, y, color.Alpha{A: 255})
			}
		}
		return o, mask, canvas, indexed
	}
	o, mask, canvas, indexed := fixture()
	beforeCanvas, beforeVGA := bytes.Clone(canvas), bytes.Clone(indexed)
	paint, clipped, ok := draftSlotPaintBounds(o, []*image.Alpha{mask}, safe, canvas, indexed, image.Rectangle{})
	if !ok || paint != image.Rect(11, 11, 16, 13) || clipped != 2 ||
		!bytes.Equal(canvas, beforeCanvas) || !bytes.Equal(indexed, beforeVGA) {
		t.Fatal("底緣裁切量測錯誤或改寫原版", paint, clipped, ok)
	}
	for name, damage := range map[string]func(*nativeObservation, *image.Alpha, []byte, []byte){
		"interior obstruction": func(_ *nativeObservation, _ *image.Alpha, _ []byte, v []byte) { v[11*320+12] = 5 },
		"invisible glyph":      func(_ *nativeObservation, _ *image.Alpha, _ []byte, v []byte) { v[11*320+15] = 5 },
		"new ink at clipped row": func(_ *nativeObservation, m *image.Alpha, _ []byte, _ []byte) {
			m.SetAlpha(4, 12, color.Alpha{A: 255})
		},
		"changed source": func(_ *nativeObservation, _ *image.Alpha, c []byte, _ []byte) { c[13*320+11] = 0 },
		"outside source": func(o *nativeObservation, _ *image.Alpha, _ []byte, _ []byte) { o.after[0] = 0 },
		"invalid source": func(o *nativeObservation, _ *image.Alpha, _ []byte, _ []byte) { o.after[-1] = 0 },
		"empty mask": func(_ *nativeObservation, m *image.Alpha, _ []byte, _ []byte) {
			clear(m.Pix)
		},
	} {
		t.Run(name, func(t *testing.T) {
			o, mask, canvas, indexed := fixture()
			damage(o, mask, canvas, indexed)
			if _, _, ok := draftSlotPaintBounds(o, []*image.Alpha{mask}, safe, canvas, indexed, image.Rectangle{}); ok {
				t.Fatal("裁切或遮擋仍啟用覆蓋")
			}
		})
	}
}

func draftActualTargetsForTest(t *testing.T) map[string]*draftLanguageTarget {
	t.Helper()
	root, game := os.Getenv("DRAFT_BUNDLE_ROOT"), os.Getenv("TEST_GAME_ROOT")
	if root == "" || game == "" {
		t.Skip("需明確指定完整Noto候選包及合法原版")
	}
	files := map[string][]byte{}
	for _, name := range []string{"LABELS.TXT", "NAMES.TXT", "WOODCUT.TXT", "COLONY.TXT", "MENU.TXT", "GAME.TXT", "PEDIA.TXT", "VICEROY.EXE"} {
		data, err := os.ReadFile(filepath.Join(game, name))
		if os.IsNotExist(err) {
			t.Skip("缺少合法原版輸入", name)
		}
		if err != nil {
			t.Fatal(err)
		}
		// 其餘文字檔的指紋由各資料表載入器核對；versions只列冷啟動的五檔。
		if want := versions[name]; want != "" && hash(data) != want {
			t.Fatal("原版來源版本不同", name)
		}
		files[name] = data
	}
	targets, err := draftPrepareTargets(root, files, nil, nil)
	if err != nil {
		t.Fatal(err)
	}
	return targets
}

func TestDraftPortableLanguageResources(t *testing.T) {
	if os.Getenv("DRAFT_EXPECT_NO_REPO") == "1" {
		if _, err := os.Stat("/repo"); !os.IsNotExist(err) {
			t.Fatal("portability container still exposes /repo", err)
		}
		if _, err := os.Stat(filepath.Join(filepath.Dir(os.Getenv("DRAFT_BUNDLE_ROOT")), "fields.json")); !os.IsNotExist(err) {
			t.Fatal("portability container still exposes research evidence", err)
		}
	}
	targets := draftActualTargetsForTest(t)
	if len(targets) != 5 {
		t.Fatal("missing prepared languages")
	}
	for locale, target := range targets {
		if locale == "en" {
			if !target.pack.manifest.Original || len(target.pack.files) != 0 {
				t.Fatal("English resources changed")
			}
			continue
		}
		if target.pack.manifest.Locale != locale || len(target.pack.files) != 80 || len(target.fixed) != 64 ||
			len(target.dlg.fonts) == 0 || len(target.str.fonts) == 0 || target.sea == nil {
			t.Fatal("incomplete relocated language", locale)
		}
	}
}

func TestDraftInputASCIIBoundsAndLiteralText(t *testing.T) {
	// 結構fixture只驗證守門與排版；原版證據另由正常GUI及同輸入重播驗證。
	widths := []int{6, 6, 7, 5, 3, 3, 6, 6, 7, 5, 6, 4, 5, 7, 5, 7}
	makeInput := func(value string) (*nativeObservation, *dialogShown) {
		canvas := bytes.Repeat([]byte{128}, 64000)
		r := &dialogRun{firstOld: map[int]byte{}, lastText: map[int]bool{}}
		o := &nativeObservation{dialogRun: r, canvas: canvas}
		o.after = map[int]byte{}
		x := 62
		for i, c := range []byte("Name: " + value + "_") {
			if i == 6 {
				x += 3
			}
			end := x + widths[i]
			box := image.Rect(x, 103, end-1, 111)
			if c == ' ' {
				box = image.Rectangle{}
			}
			r.chars = append(r.chars, dialogChar{c: c, box: box, colors: map[byte]int{68: 1}})
			if !box.Empty() {
				pixel := 103*320 + x
				r.firstOld[pixel], r.lastText[pixel], o.after[pixel], canvas[pixel] = 128, true, 68, 68
			}
			o.dialogCells = append(o.dialogCells, nativeDialogCell{uint16(103*320 + x), uint16(103*320 + end), 0x2cae, 0x2cae, true, true})
			x = end
		}
		prompt := &dialogShown{id: "GAME.TXT:0x00000F5C", safe: image.Rect(61, 86, 219, 98)}
		prompt.afterSafe = rectBytes(canvas, prompt.safe)
		return o, prompt
	}
	for locale, target := range draftActualTargetsForTest(t) {
		if locale == "en" {
			continue
		}
		t.Run(locale, func(t *testing.T) {
			for _, value := range []string{"Jamestown", "Jam{town}", "jam  town"} {
				o, prompt := makeInput(value)
				original := bytes.Clone(o.canvas)
				st, why := draftInputASCII(o, prompt, target.str.fonts)
				if st == nil || why != "" || st.zh != value || st.safe.Max.X != 146 || st.size < 18 {
					t.Fatalf("input rejected or altered: %+v %s", st, why)
				}
				if !bytes.Equal(original, o.canvas) || st.safe.Overlaps(image.Rect(146, 103, 153, 119)) {
					t.Fatal("original source or caret changed")
				}
				if draftAlphaInk(st.normal).Empty() || draftAlphaInk(st.shadow).Empty() {
					t.Fatal("missing input glyphs")
				}
				for name, change := range map[string]func(){
					"unknown cursor":  func() { o.dialogCells[6].EndKnown = false },
					"wrong segment":   func() { o.dialogCells[6].StartES = 0xa000 },
					"unknown context": func() { prompt.id = "OTHER" },
					"expired context": func() { prompt.phase = "expired" },
					"source changed":  func() { o.canvas[87*320+62]++ },
				} {
					oldCell, oldID, oldPhase := o.dialogCells[6], prompt.id, prompt.phase
					change()
					if got, _ := draftInputASCII(o, prompt, target.str.fonts); got != nil {
						t.Fatal("accepted", name)
					}
					copy(o.canvas, original)
					o.dialogCells[6], prompt.id, prompt.phase = oldCell, oldID, oldPhase
				}
				if got, _ := draftInputASCII(o, prompt, nil); got != nil {
					t.Fatal("missing font accepted")
				}
				o.dialogRun.lastText[103*320+95] = false
				delete(o.after, 103*320+95)
				if got, _ := draftInputASCII(o, prompt, target.str.fonts); got != nil {
					t.Fatal("erased source revived")
				}
			}
		})
	}
}

func TestDraftActualLanguageBundleTransaction(t *testing.T) {
	targets := draftActualTargetsForTest(t)
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		t.Run(locale, func(t *testing.T) {
			canvas, buffer, indexed, palette := make([]byte, 64000), make([]byte, 64000), make([]byte, 64000), make([]byte, 768)
			indexed[6430], palette[3] = 1, 63
			j := &nativeJournal{enabled: true}
			nativeBefore := bytes.Join([][]byte{canvas, buffer, indexed, palette}, nil)
			backend := &draftLanguageBackend{targets: targets, sample: func() draftNativeFrame {
				return draftNativeFrame{j, canvas, buffer, indexed, palette, image.Rectangle{}, 123, 0x13}
			}}
			path := filepath.Join(t.TempDir(), "display.json")
			initial, options := displayOptions{"en", "original"}, displayOptions{locale, "original"}
			if err := applyDisplayPreferences(path, initial, backend.prepare); err != nil {
				t.Fatal(err)
			}
			old, saved := backend.active, read(path)
			pixels := bytes.Clone(old.frame.Pix)
			candidate, err := backend.prepare(options)
			if err != nil || candidate == nil || backend.active != old || !bytes.Equal(pixels, old.frame.Pix) || !bytes.Equal(saved, read(path)) {
				t.Fatal("準備改變生效資料", err)
			}
			s := displaySettings{current: initial}
			s.open(false)
			s.released(true)
			s.draft = options
			s.cancel()
			if backend.active != old || s.current != initial || !bytes.Equal(saved, read(path)) {
				t.Fatal("取消改變生效語言包")
			}
			s.released(true)
			s.open(false)
			s.released(true)
			s.draft = options
			if s.apply(func(o displayOptions) error {
				return applyDisplayPreferences(filepath.Join(path, "blocked"), o, backend.prepare)
			}) ||
				s.current != initial || s.phase != displayEditing || s.problem != "ui.error.save" || backend.active != old ||
				!bytes.Equal(pixels, old.frame.Pix) || !bytes.Equal(saved, read(path)) {
				t.Fatal("保存失敗改變生效語言包、畫面或設定")
			}
			if !s.apply(func(o displayOptions) error { return applyDisplayPreferences(path, o, backend.prepare) }) {
				t.Fatal("成功交易失敗", s.problem)
			}
			persisted, err := readDisplayPreferences(path, "", "")
			if err != nil || persisted != options || s.current != options || s.phase != displayResuming ||
				backend.active == old || backend.active.options != options || backend.active.target != targets[locale] ||
				backend.active.receipt["locale"] != locale || !bytes.Equal(pixels, old.frame.Pix) {
				t.Fatal("未共同提交語言包、畫面與設定", err)
			}
			if locale != "en" && (len(backend.active.target.fixed) != 64 || backend.active.target.dlg == nil ||
				backend.active.target.str == nil || backend.active.target.sea == nil) {
				t.Fatal("提交的語言包不完整")
			}
			// 已準備的提交不再取用後端清冊或原版取樣函式。
			backend.targets = nil
			backend.sample = func() draftNativeFrame { panic("提交重新讀取原版") }
			candidate()
			if backend.active.target != targets[locale] || backend.active.options != options ||
				!bytes.Equal(nativeBefore, bytes.Join([][]byte{canvas, buffer, indexed, palette}, nil)) {
				t.Fatal("提交重新查找資料或改變原版")
			}
		})
	}
}

func TestDraftLanguageTransactionRejectsIncompleteCandidate(t *testing.T) {
	target := &draftLanguageTarget{pack: &draftPreparedBundle{manifest: draftBundleManifest{Locale: "en", Original: true}}}
	old := &draftLanguageDisplay{options: displayOptions{"en", "original"}, target: target}
	for _, kind := range []string{"invalid-language", "hd", "missing-target", "wrong-locale", "missing-sample", "missing-journal", "truncated-frame"} {
		t.Run(kind, func(t *testing.T) {
			options := displayOptions{"en", "original"}
			b := &draftLanguageBackend{active: old, targets: map[string]*draftLanguageTarget{"en": target}, sample: func() draftNativeFrame {
				return draftNativeFrame{journal: &nativeJournal{}}
			}}
			switch kind {
			case "invalid-language":
				options.Language = "invalid"
			case "hd":
				options.Graphics = "hd"
			case "missing-target":
				b.targets = nil
			case "wrong-locale":
				b.targets["en"] = &draftLanguageTarget{pack: &draftPreparedBundle{manifest: draftBundleManifest{Locale: "ja"}}}
			case "missing-sample":
				b.sample = nil
			case "missing-journal":
				b.sample = func() draftNativeFrame { return draftNativeFrame{} }
			}
			commit, err := b.prepare(options)
			if err == nil || commit != nil || b.active != old {
				t.Fatal("不完整候選進入生效資料", err)
			}
		})
	}
}

func TestDraftLiveCacheTracksAllNativeInputs(t *testing.T) {
	target := &draftLanguageTarget{pack: &draftPreparedBundle{manifest: draftBundleManifest{Locale: "en", Original: true}}}
	f := draftNativeFrame{journal: &nativeJournal{}, canvas: make([]byte, 64000), buffer: make([]byte, 64000),
		indexed: make([]byte, 64000), palette: make([]byte, 768), step: 1, mode: 0x13}
	b := &draftLanguageBackend{targets: map[string]*draftLanguageTarget{"en": target}, sample: func() draftNativeFrame { return f }}
	commit, err := b.prepare(displayOptions{"en", "original"})
	if err != nil {
		t.Fatal(err)
	}
	commit()
	first := b.active.frame
	f.step++
	im, record, err := b.renderCurrent()
	if err != nil || im != first || record["step"] != f.step || record["live_reused"] != true || b.rebuilds != 0 || b.active.receipt["step"] != uint64(1) {
		t.Fatal("unchanged native frame not reused or cached receipt mutated", err)
	}
	for _, kind := range []string{"canvas", "map", "vga", "palette", "cursor", "button", "source", "eviction", "expiry", "mode"} {
		t.Run(kind, func(t *testing.T) {
			before := b.active.frame
			n := b.rebuilds
			switch kind {
			case "canvas":
				f.canvas[6430]++
			case "map":
				f.buffer[6430]++
			case "vga":
				f.indexed[6430]++
			case "palette":
				f.palette[0]++
			case "cursor":
				f.cursor = image.Rect(10, 10, 26, 26)
			case "button":
				f.journal.buttons = true
			case "source":
				f.journal.accepted++
			case "eviction":
				f.journal.lost++
			case "expiry":
				f.journal.items = append(f.journal.items, &nativeObservation{fixed: &nativeFixed{expired: true}})
			case "mode":
				f.mode = 3
			}
			im, record, err := b.renderCurrent()
			if err != nil || im == before || b.rebuilds != n+1 || record["live_reused"] != false {
				t.Fatal("changed native input reused old display", err)
			}
			if kind == "vga" && im.RGBAAt(30*4, 20*4) != draftColor(f.indexed[6430], f.palette) {
				t.Fatal("English live frame lost native pixels")
			}
		})
	}
	old := b.active
	f.canvas = f.canvas[:1]
	if _, _, err := b.renderCurrent(); err == nil || b.active != old {
		t.Fatal("invalid live frame accepted or replaced active view")
	}
	if _, _, err := (&draftLanguageBackend{}).renderCurrent(); err == nil {
		t.Fatal("uninitialized live backend accepted")
	}
}

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

func TestDraftRetainedNumeralsUseCurrentNativeVisibility(t *testing.T) {
	targets := draftActualTargetsForTest(t)
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			canvas, palette := make([]byte, 64000), make([]byte, 768)
			palette[45], palette[46], palette[47] = 63, 63, 63
			r := retainedFixture("90", image.Rect(83, 194, 90, 199))
			r.lastVal = map[int]byte{}
			for y := 194; y < 199; y++ {
				for x := 83; x < 90; x++ {
					if x == 86 && y == 195 { // 字格內的背景反例，與透明外緣分開。
						continue
					}
					i := y*320 + x
					canvas[i], r.firstOld[i], r.lastVal[i] = 15, 0, 15
				}
			}
			j := &nativeJournal{enabled: true}
			if !j.captureString(r, canvas, nil, 1) {
				t.Fatal("numeric source rejected")
			}
			before := bytes.Clone(canvas)
			for _, kind := range []string{"visible", "canvas-overwritten", "background-changed", "padding-changed", "vga-covered"} {
				t.Run(kind, func(t *testing.T) {
					current, vga := bytes.Clone(canvas), bytes.Clone(canvas)
					switch kind {
					case "canvas-overwritten":
						current[194*320+83] = 0
					case "background-changed":
						current[195*320+86], vga[195*320+86] = 15, 15
					case "padding-changed":
						current[193*320+82], vga[193*320+82] = 15, 15
					case "vga-covered":
						vga[194*320+83] = 0
					}
					im, record, err := draftRebuildTarget(targets[locale], j, current, make([]byte, 64000), vga, palette, image.Rectangle{}, 2, 0x13)
					if err != nil {
						t.Fatal(err)
					}
					items := record["items"].([]map[string]any)
					if kind == "visible" || kind == "padding-changed" {
						if len(items) != 1 || items[0]["id"] != "STRING:retained-ascii" || items[0]["text"] != "90" || bytes.Equal(im.Pix, draftRGB(vga, palette).Pix) {
							t.Fatal("visible native numerals not rendered with target font", record)
						}
						if kind == "padding-changed" && (items[0]["unused_padding_changed"] != true || items[0]["safe"] != image.Rect(83, 194, 90, 199)) {
							t.Fatal("透明外緣未裁至原版排版區", record)
						}
					} else if len(items) != 0 || !bytes.Equal(im.Pix, draftRGB(vga, palette).Pix) {
						t.Fatal("changed native source or background accepted", kind)
					}
				})
			}
			if !bytes.Equal(canvas, before) || j.items[0].stringRun == nil || string(j.items[0].stringRun.text) != "90" {
				t.Fatal("rebuilding mutated native source")
			}
		})
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
	candidate := &draftSeaRow{observation: o, row: row, layer: seaPanelRect}
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

func TestLanguageRuntimeSelection(t *testing.T) {
	for _, test := range []struct {
		name, formal, probe              string
		live, capture, settings, control bool
		wantRoot                         string
		wantLive, wantError              bool
	}{
		{"formal", "/languages", "", false, false, true, false, "/languages", true, false},
		{"formal-no-ui", "/languages", "", false, false, false, false, "/languages", true, false},
		{"formal-control", "/languages", "", false, false, true, true, "/languages", false, false},
		{"legacy", "", "", false, false, false, false, "", false, false},
		{"observed", "", "/probe", false, true, false, false, "/probe", false, false},
		{"probe-live", "", "/probe", true, true, true, false, "/probe", true, false},
		{"mixed-roots", "/languages", "/probe", false, true, true, false, "", false, true},
		{"mixed-live", "/languages", "", true, true, true, false, "", false, true},
		{"missing-capture", "", "/probe", false, false, true, false, "", false, true},
		{"missing-bundle", "", "", true, true, true, false, "", false, true},
		{"missing-ui", "", "/probe", true, true, false, false, "", false, true},
		{"probe-control", "", "/probe", true, true, true, true, "", false, true},
	} {
		t.Run(test.name, func(t *testing.T) {
			root, live, err := languageRuntimeSelection(test.formal, test.probe, test.live, test.capture, test.settings, test.control)
			if (err != nil) != test.wantError || root != test.wantRoot || live != test.wantLive {
				t.Fatalf("got %q/%t/%v", root, live, err)
			}
		})
	}
}

// 規格052：正常城內數值的未繪字外緣會被後續原版繪圖改動。
// 以實際Noto字型及原版單字字格檢查裁切，內部來源仍須逐點完整。
func TestDraftRetainedPaddingActualNoto(t *testing.T) {
	for locale, target := range draftActualTargetsForTest(t) {
		if locale == "en" {
			continue
		}
		t.Run(locale, func(t *testing.T) {
			for _, sample := range []struct {
				text       string
				ink        image.Rectangle
				start, end image.Point
				padding    image.Point
			}{
				{"1", image.Rect(272, 194, 273, 199), image.Pt(272, 194), image.Pt(275, 194), image.Pt(275, 195)},
				{"4", image.Rect(9, 194, 12, 199), image.Pt(9, 194), image.Pt(13, 194), image.Pt(9, 199)},
			} {
				canvas := make([]byte, 64000)
				r := retainedFixture(sample.text, sample.ink)
				r.retainedCursor = []image.Point{sample.start, sample.end}
				o := &nativeObservation{kind: "string", step: 42, ink: sample.ink, stringRun: r, after: map[int]byte{}}
				for y := sample.ink.Min.Y; y < sample.ink.Max.Y; y++ {
					pos := y*320 + sample.ink.Min.X
					canvas[pos], o.after[pos], r.firstOld[pos] = 15, 15, 0
				}
				s := &stringRuntime{cat: target.str}
				it, why := finishRetainedASCII(s, r, canvas, 42, "")
				if it == nil {
					t.Fatal(sample.text, why)
				}
				canvas[sample.padding.Y*320+sample.padding.X] = 47
				indexed := bytes.Clone(canvas)
				sourceBefore, sourceAfter := bytes.Clone(it.before), bytes.Clone(it.after)
				oldMask := bytes.Clone(it.norm.Pix)
				oldCanvas, oldVGA := bytes.Clone(canvas), bytes.Clone(indexed)
				got := draftFitRetainedASCII(it, o, canvas, indexed, image.Rectangle{})
				layout, ok := retainedASCIILayout(r, it.ink)
				if !ok || got == nil || got.safe != layout || got.size != it.size {
					t.Fatal("完整字格未保留", sample.text, got)
				}
				if !bytes.Equal(it.before, sourceBefore) || !bytes.Equal(it.after, sourceAfter) || !bytes.Equal(it.norm.Pix, oldMask) ||
					!bytes.Equal(canvas, oldCanvas) || !bytes.Equal(indexed, oldVGA) {
					t.Fatal("修改了原始項目或原版畫布")
				}
				// 世界座標下，每一個alpha值都相同；外緣只准原本就是透明。
				for layer, original := range []*image.Alpha{it.norm, it.shadow, it.accent} {
					cropped := []*image.Alpha{got.norm, got.shadow, got.accent}[layer]
					for y := 0; y < original.Rect.Dy(); y++ {
						for x := 0; x < original.Rect.Dx(); x++ {
							p := image.Pt(x, y).Add(it.safe.Min.Mul(4)).Sub(got.safe.Min.Mul(4))
							if original.AlphaAt(x, y) != cropped.AlphaAt(p.X, p.Y) {
								t.Fatal("裁切改變字形", sample.text, layer, x, y)
							}
						}
					}
					if len(cropped.Pix) > 0 {
						cropped.Pix[0] ^= 1
					}
				}
				got.before[0] ^= 1
				got.after[0] ^= 1
				if !bytes.Equal(it.before, sourceBefore) || !bytes.Equal(it.after, sourceAfter) || !bytes.Equal(it.norm.Pix, oldMask) {
					t.Fatal("裁切共用可寫來源")
				}
			}
		})
	}
}

func TestDraftRetainedPaddingRejectsChangedSource(t *testing.T) {
	fixture := func() (*stringItem, *nativeObservation, []byte, []byte) {
		ink := image.Rect(272, 194, 273, 199)
		layout := image.Rect(272, 194, 275, 199)
		safe := layout.Inset(-1)
		canvas := make([]byte, 64000)
		r := retainedFixture("1", ink)
		r.retainedCursor = []image.Point{image.Pt(272, 194), image.Pt(275, 194)}
		o := &nativeObservation{kind: "string", step: 42, ink: ink, stringRun: r, after: map[int]byte{}}
		for y := 194; y < 199; y++ {
			canvas[y*320+272] = 15
			o.after[y*320+272] = 15
		}
		rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
		n := image.NewAlpha(rect)
		n.SetAlpha(4, 4, color.Alpha{A: 255})
		it := &stringItem{id: "STRING:retained-ascii", text: "1", zh: "1", complete: 42, ink: ink, safe: safe,
			before: make([]byte, safe.Dx()*safe.Dy()), after: stringRect(canvas, safe),
			norm: n, shadow: image.NewAlpha(rect), accent: image.NewAlpha(rect)}
		canvas[195*320+275] = 47
		return it, o, canvas, bytes.Clone(canvas)
	}
	for name, damage := range map[string]func(*stringItem, *nativeObservation, []byte, []byte){
		"wrong item":            func(it *stringItem, _ *nativeObservation, _, _ []byte) { it.id = "STRING:colony" },
		"wrong source kind":     func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.kind = "string-map" },
		"wrong source ink":      func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.ink.Min.X-- },
		"wrong step":            func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.step++ },
		"wrong text":            func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.stringRun.text = []byte("2") },
		"wrong segment":         func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.stringRun.retainedSegments[0] = 0x3bb0 },
		"missing run":           func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.stringRun = nil },
		"empty pixels":          func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.after = nil },
		"invalid pixel":         func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.after[64000] = 0 },
		"source outside layout": func(_ *stringItem, o *nativeObservation, _, _ []byte) { o.after[195*320+275] = 47 },
		"erased digit": func(_ *stringItem, _ *nativeObservation, c, v []byte) {
			for y := 194; y < 199; y++ {
				c[y*320+272] = 0
				v[y*320+272] = 0
			}
		},
		"changed inner background": func(_ *stringItem, _ *nativeObservation, c, v []byte) { c[195*320+274] = 3; v[195*320+274] = 3 },
		"changed VGA":              func(_ *stringItem, _ *nativeObservation, _ []byte, v []byte) { v[195*320+272] = 3 },
		"invalid safe":             func(it *stringItem, _ *nativeObservation, _, _ []byte) { it.safe.Min.X-- },
		"missing before":           func(it *stringItem, _ *nativeObservation, _, _ []byte) { it.before = nil },
		"missing after":            func(it *stringItem, _ *nativeObservation, _, _ []byte) { it.after = nil },
		"missing mask":             func(it *stringItem, _ *nativeObservation, _, _ []byte) { it.shadow = nil },
		"incorrect mask rectangle": func(it *stringItem, _ *nativeObservation, _, _ []byte) {
			it.accent = image.NewAlpha(image.Rect(0, 0, 1, 1))
		},
		"ink in padding": func(it *stringItem, _ *nativeObservation, _, _ []byte) { it.norm.SetAlpha(0, 0, color.Alpha{A: 255}) },
		"empty mask":     func(it *stringItem, _ *nativeObservation, _, _ []byte) { clear(it.norm.Pix) },
	} {
		t.Run(name, func(t *testing.T) {
			it, o, c, v := fixture()
			damage(it, o, c, v)
			if draftFitRetainedASCII(it, o, c, v, image.Rectangle{}) != nil {
				t.Fatal("不完整來源未拒絕")
			}
		})
	}
	it, o, c, v := fixture()
	if draftFitRetainedASCII(nil, o, c, v, image.Rectangle{}) != nil || draftFitRetainedASCII(it, nil, c, v, image.Rectangle{}) != nil ||
		draftFitRetainedASCII(it, o, c[:1], v, image.Rectangle{}) != nil || draftFitRetainedASCII(it, o, c, v[:1], image.Rectangle{}) != nil {
		t.Fatal("非法輸入未拒絕")
	}
	v[195*320+272] = 3
	if draftFitRetainedASCII(it, o, c, v, image.Rect(272, 195, 273, 196)) == nil {
		t.Fatal("原版游標未沿既有例外")
	}
	c[195*320+272] = 3
	if draftFitRetainedASCII(it, o, c, v, image.Rect(272, 195, 273, 196)) != nil {
		t.Fatal("游標例外允許來源損壞")
	}
}

func draftMapFixtureForTest() (*stringItem, *nativeObservation, *nativeJournal, []byte, []byte) {
	ink, safe := image.Rect(146, 120, 196, 129), image.Rect(136, 118, 206, 130)
	canvas := bytes.Repeat([]byte{10}, 64000)
	r := &stringRun{text: []byte("Jamestown"), buf2: true, colors: map[byte]int{0: 1, 15: 1}, firstOld: map[int]byte{}}
	o := &nativeObservation{kind: "string-map", step: 42, ink: ink, stringRun: r, after: map[int]byte{}}
	for pos, value := range map[int]byte{120*320 + 146: 15, 121*320 + 147: 0} {
		r.firstOld[pos], o.after[pos], canvas[pos] = 10, value, value
	}
	o.buffer = bytes.Clone(canvas)
	before := bytes.Clone(canvas)
	for pos, value := range r.firstOld {
		before[pos] = value
	}
	rect := image.Rect(0, 0, safe.Dx()*4, safe.Dy()*4)
	n, sh := image.NewAlpha(rect), image.NewAlpha(rect)
	n.SetAlpha(40, 8, color.Alpha{A: 255}) // 原版墨跡內的完整正文。
	n.SetAlpha(4, 8, color.Alpha{A: 180})  // 擴寬後的正文。
	for y := 4; y < 8; y++ {
		for x := 48; x < 52; x++ {
			sh.SetAlpha(x, y, color.Alpha{A: 120})
		}
	}
	sh.SetAlpha(45, 5, color.Alpha{A: 200})
	it := &stringItem{id: "STRING:colony", text: "Jamestown", zh: "字", ink: ink, safe: safe, color: 15,
		shadowOff: -stringLabelOutline, size: 23, norm: n, shadow: sh,
		before: stringRect(before, safe), after: stringRect(canvas, safe), complete: 42}
	canvas[119*320+148] = 68
	return it, o, &nativeJournal{items: []*nativeObservation{o}}, canvas, bytes.Clone(canvas)
}

func TestDraftMapLabelPreservesNativeForeground(t *testing.T) {
	it, o, j, canvas, indexed := draftMapFixtureForTest()
	before, after, norm, shadow := bytes.Clone(it.before), bytes.Clone(it.after), bytes.Clone(it.norm.Pix), bytes.Clone(it.shadow.Pix)
	oldCanvas, oldVGA, oldBuffer := bytes.Clone(canvas), bytes.Clone(indexed), bytes.Clone(o.buffer)
	got, changed, clipped := draftFitMapLabel(it, o, j, canvas, indexed, image.Rectangle{})
	if got == nil || changed != 1 || clipped != 16 || got.safe != it.safe || got.size != it.size || !bytes.Equal(got.norm.Pix, norm) {
		t.Fatal("原正文、字級或後畫像素優先權未保留", changed, clipped)
	}
	if !stringSame(canvas, got, image.Rectangle{}) || draftMapMaskAt(got.shadow, got.safe, image.Pt(148, 119)) {
		t.Fatal("舊背景或描邊覆蓋後畫內容")
	}
	for y := 0; y < it.shadow.Rect.Dy(); y++ {
		for x := 0; x < it.shadow.Rect.Dx(); x++ {
			if x >= 48 && x < 52 && y >= 4 && y < 8 {
				continue
			}
			if got.shadow.AlphaAt(x, y) != it.shadow.AlphaAt(x, y) {
				t.Fatal("改變了其他描邊")
			}
		}
	}
	palette := make([]byte, 768)
	palette[15*3], palette[68*3+1] = 63, 63
	out := draftRGB(indexed, palette)
	k := 0
	for y := got.safe.Min.Y; y < got.safe.Max.Y; y++ {
		for x := got.safe.Min.X; x < got.safe.Max.X; x++ {
			if got.before[k] != got.after[k] {
				draftPaintPixel(out, y*320+x, got.before[k], palette)
			}
			k++
		}
	}
	draftPaintLayers(out, got.safe, []*image.Alpha{got.shadow, got.norm}, []byte{0, 15}, palette)
	for y := 119 * 4; y < 120*4; y++ {
		for x := 148 * 4; x < 149*4; x++ {
			if out.RGBAAt(x, y) != draftColor(68, palette) {
				t.Fatal("原版後畫像素被覆蓋")
			}
		}
	}
	if !bytes.Equal(it.before, before) || !bytes.Equal(it.after, after) || !bytes.Equal(it.norm.Pix, norm) || !bytes.Equal(it.shadow.Pix, shadow) ||
		!bytes.Equal(canvas, oldCanvas) || !bytes.Equal(indexed, oldVGA) || !bytes.Equal(o.buffer, oldBuffer) {
		t.Fatal("候選修改了來源")
	}
	got.before[0] ^= 1
	got.after[0] ^= 1
	got.norm.Pix[0] ^= 1
	got.shadow.Pix[0] ^= 1
	if !bytes.Equal(it.before, before) || !bytes.Equal(it.after, after) || !bytes.Equal(it.norm.Pix, norm) || !bytes.Equal(it.shadow.Pix, shadow) {
		t.Fatal("候選與來源共用可寫資料")
	}
}

func TestDraftMapLabelRejectsUnsafeSource(t *testing.T) {
	for name, damage := range map[string]func(*stringItem, *nativeObservation, *nativeJournal, []byte, []byte){
		"wrong id":      func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.id = "STRING:dictionary" },
		"wrong surface": func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.kind = "string" },
		"wrong step":    func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.step++ },
		"wrong ink":     func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.ink.Min.X-- },
		"wrong text": func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) {
			o.stringRun.text = []byte("Other")
		},
		"missing run":        func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.stringRun = nil },
		"main canvas":        func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.stringRun.buf2 = false },
		"mixed":              func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.stringRun.mixed = true },
		"other outline":      func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.stringRun.outline = true },
		"hotkey":             func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.stringRun.keyColor = 5 },
		"other color":        func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.stringRun.colors[5] = 1 },
		"wrong fill":         func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.color = 5 },
		"wrong shade":        func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.shadowColor = 5 },
		"wrong outline size": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.shadowOff-- },
		"accent": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) {
			it.accent = image.NewAlpha(it.norm.Rect)
		},
		"outside map":             func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.safe.Min.Y = 0 },
		"missing before":          func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.before = nil },
		"missing after":           func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.after = nil },
		"missing buffer":          func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.buffer = nil },
		"missing pixels":          func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.after = nil },
		"invalid pixel":           func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.after[64000] = 10 },
		"writer outside ink":      func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.after[119*320+148] = 68 },
		"wrong source background": func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) { o.buffer[118*320+136] = 5 },
		"wrong source before": func(_ *stringItem, o *nativeObservation, _ *nativeJournal, _, _ []byte) {
			o.stringRun.firstOld[120*320+146] = 5
		},
		"restore outside ink": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.before[0] = 5 },
		"erased glyph": func(_ *stringItem, _ *nativeObservation, _ *nativeJournal, c, v []byte) {
			c[120*320+146] = 10
			v[120*320+146] = 10
		},
		"inner background": func(_ *stringItem, _ *nativeObservation, _ *nativeJournal, c, v []byte) {
			c[123*320+160] = 5
			v[123*320+160] = 5
		},
		"VGA":            func(_ *stringItem, _ *nativeObservation, _ *nativeJournal, _ []byte, v []byte) { v[118*320+136] = 5 },
		"missing normal": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.norm = nil },
		"missing shadow": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { it.shadow = nil },
		"wrong mask shape": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) {
			it.norm = image.NewAlpha(image.Rect(0, 0, 1, 1))
		},
		"empty normal": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) { clear(it.norm.Pix) },
		"native covers normal": func(it *stringItem, _ *nativeObservation, _ *nativeJournal, _, _ []byte) {
			it.norm.SetAlpha(48, 4, color.Alpha{A: 1})
		},
		"other live map glyph": func(_ *stringItem, _ *nativeObservation, j *nativeJournal, _, _ []byte) {
			j.items = append(j.items, &nativeObservation{kind: "string-map", stringRun: &stringRun{text: []byte("Other")}, after: map[int]byte{120*320 + 137: 10}})
		},
	} {
		t.Run(name, func(t *testing.T) {
			it, o, j, c, v := draftMapFixtureForTest()
			damage(it, o, j, c, v)
			if fitted, _, _ := draftFitMapLabel(it, o, j, c, v, image.Rectangle{}); fitted != nil {
				t.Fatal("未拒絕不安全來源")
			}
		})
	}
	it, o, j, c, v := draftMapFixtureForTest()
	if fit, _, _ := draftFitMapLabel(nil, o, j, c, v, image.Rectangle{}); fit != nil {
		t.Fatal("nil item")
	}
	if fit, _, _ := draftFitMapLabel(it, nil, j, c, v, image.Rectangle{}); fit != nil {
		t.Fatal("nil source")
	}
	if fit, _, _ := draftFitMapLabel(it, o, nil, c, v, image.Rectangle{}); fit != nil {
		t.Fatal("nil journal")
	}
	v[120*320+146] = 5
	if fit, _, _ := draftFitMapLabel(it, o, j, c, v, image.Rect(146, 120, 147, 121)); fit == nil {
		t.Fatal("既有游標例外未保留")
	}
	c[120*320+146] = 5
	if fit, _, _ := draftFitMapLabel(it, o, j, c, v, image.Rect(146, 120, 147, 121)); fit != nil {
		t.Fatal("游標例外破壞來源守門")
	}
}

func TestDraftNotoMapCompleteLabels(t *testing.T) {
	for _, tc := range []struct {
		locale string
		size   int
	}{{"zh-Hant", 23}, {"zh-Hans", 23}, {"ja", 17}, {"ko", 22}} {
		t.Run(tc.locale, func(t *testing.T) {
			target := draftActualTargetsForTest(t)[tc.locale]
			text := target.str.colony["Jamestown"]
			if !strings.Contains(text, "Jamestown") || target.str.labelPlan == nil {
				t.Fatal("遺失完整雙語名或Noto回退")
			}
			fill, ink := image.Rect(146, 120, 195, 128), image.Rect(146, 120, 196, 129)
			if _, old, _, _ := target.str.labelMasks(text, fill, ink, 7); (old == nil) != (tc.locale == "ja") {
				t.Fatal("夾具未重現舊規劃器結果")
			}
			sh, n, safe, size := target.str.labelPlan(text, fill, ink, 7)
			if n == nil || sh == nil || size != tc.size || !safe.In(stringMapView) {
				t.Fatal("完整日文沒有選最大可用字級", size, safe)
			}
			width := func(px int) int {
				w := 0
				for _, ch := range text {
					w += target.str.fonts[px].widths[ch]
				}
				return w
			}
			if width(size) > 264 || width(size+1) <= 264 {
				t.Fatal("17px不是既定寬度內的最大候選")
			}
			f := target.str.fonts[size]
			// 從各字形逐點建立完整正文，獨立核對沒有任何字形被安全矩形裁掉。
			raw := map[image.Point]byte{}
			x, minY := 0, 1000
			for _, ch := range text {
				g := f.glyphs[ch]
				for y := g.Rect.Min.Y; y < g.Rect.Max.Y; y++ {
					for gx := g.Rect.Min.X; gx < g.Rect.Max.X; gx++ {
						value := g.AlphaAt(gx, y).A
						if value != 0 {
							p := image.Pt(x+gx, y)
							if value > raw[p] {
								raw[p] = value
							}
							minY = min(minY, y)
						}
					}
				}
				x += f.widths[ch]
			}
			startX := (fill.Min.X+fill.Max.X)*2 - width(size)/2 - safe.Min.X*4
			startY := fill.Min.Y*4 - minY - safe.Min.Y*4
			for p, value := range raw {
				if n.AlphaAt(p.X+startX, p.Y+startY).A != value {
					t.Fatal("完整字形遭裁切", p)
				}
			}
			count := 0
			for _, value := range n.Pix {
				if value != 0 {
					count++
				}
			}
			if count != len(raw) {
				t.Fatal("正文像素增加或遺失", count, len(raw))
			}

			// 完整正文的全域墨跡上緣必須與實測原版白色填色上緣一致。
			actualTop := 1000
			for y := n.Rect.Min.Y; y < n.Rect.Max.Y; y++ {
				for x := n.Rect.Min.X; x < n.Rect.Max.X; x++ {
					if n.AlphaAt(x, y).A != 0 {
						actualTop = min(actualTop, y+safe.Min.Y*4)
					}
				}
			}
			if actualTop != 480 {
				t.Fatal("完整正文未對齊原版填色上緣", actualTop)
			}
			_, source, _, canvas, _ := draftMapFixtureForTest()
			run := source.stringRun
			run.colors = map[byte]int{0: 109, 15: 92}
			black := []image.Rectangle{image.Rect(146, 120, 151, 128), image.Rect(152, 122, 157, 128), image.Rect(158, 122, 164, 128), image.Rect(165, 122, 169, 128), image.Rect(170, 122, 175, 128), image.Rect(176, 121, 179, 129), image.Rect(180, 122, 184, 128), image.Rect(185, 122, 191, 128), image.Rect(192, 122, 196, 128)}
			white := []image.Rectangle{image.Rect(146, 120, 150, 127), image.Rect(152, 122, 156, 127), image.Rect(158, 122, 163, 127), image.Rect(165, 122, 168, 127), image.Rect(170, 122, 174, 127), image.Rect(176, 121, 178, 128), image.Rect(180, 122, 183, 127), image.Rect(185, 122, 190, 127), image.Rect(192, 122, 195, 127)}
			for i, b := range black {
				run.boxes = append(run.boxes, b)
				run.charColor = append(run.charColor, map[byte]image.Rectangle{0: b, 15: white[i]})
			}
			runtime := &stringRuntime{cat: target.str}
			item, why := runtime.finishLabel(run, source.buffer, canvas, source.step)
			if item == nil || why != "" || item.size != size || item.safe != safe || !bytes.Equal(item.norm.Pix, n.Pix) || !bytes.Equal(item.shadow.Pix, sh.Pix) {
				t.Fatal("正式組裝未使用完整文案規劃", why)
			}
			bare := *target.str
			bare.labelPlan = nil
			legacy := &stringRuntime{cat: &bare}
			old, reason := legacy.finishLabel(run, source.buffer, canvas, source.step)
			if tc.locale == "ja" {
				if old != nil || reason != "does-not-fit" {
					t.Fatal("未保留原規劃器拒絕")
				}
			} else {
				if old == nil || reason != "" || bytes.Equal(old.norm.Pix, n.Pix) {
					t.Fatal("未保留原規劃器行為")
				}
			}

			for _, bad := range []struct {
				text      string
				fill, ink image.Rectangle
				cap       int
			}{
				{strings.Repeat(text, 8), fill, ink, 7},
				{text, image.Rect(240, 120, 289, 128), image.Rect(240, 120, 290, 129), 7},
				{text, fill, ink, 1},
			} {
				if _, mask, _, _ := target.str.labelPlan(bad.text, bad.fill, bad.ink, bad.cap); mask != nil {
					t.Fatal("不可讀或越界候選未拒絕")
				}
			}
		})
	}
}

func TestDraftSoldierDialogForeground(t *testing.T) {
	root := os.Getenv("TEST_SOLDIER_ROOT")
	if root == "" {
		t.Skip("需要合法原版士兵正文與正常輸入收據")
	}
	read := func(name string) []byte {
		t.Helper()
		v, e := os.ReadFile(filepath.Join(root, name))
		if e != nil {
			t.Fatal(e)
		}
		return v
	}
	var src struct {
		Base           uint32
		ReadPos        int          `json:"read_pos"`
		FirstOld       map[int]byte `json:"first_old"`
		LastText       map[int]bool `json:"last_text"`
		Canvas, Buffer []byte
		Step           uint64
		Native         struct {
			Items []struct {
				Kind   string
				Step   uint64
				Ink    image.Rectangle
				Text   string
				Shadow bool            `json:"shadow_written"`
				Others image.Rectangle `json:"other_writes"`
				After  map[int]byte    `json:"after_pixels"`
				Chars  []struct {
					Byte       byte
					Box        image.Rectangle
					Colors     map[byte]int
					Contiguous bool
					Prefix     bool `json:"prefix_continuation"`
				} `json:"characters"`
			}
		} `json:"native_export"`
	}
	raw := read("r120-soldier-evidence-r1/gui.soldier-source.json")
	if hash(raw) != "f918305b821fac28a5679fc739490cfeba674c1313e4c3ba9c1634638c9e33cf" {
		t.Fatal("source evidence fingerprint")
	}
	if e := json.Unmarshal(raw, &src); e != nil {
		t.Fatal(e)
	}
	row := src.Native.Items[len(src.Native.Items)-1]
	run := &dialogRun{base: src.Base, readPos: src.ReadPos, firstOld: src.FirstOld, lastText: src.LastText, shadowWritten: row.Shadow, others: row.Others}
	for _, c := range row.Chars {
		run.chars = append(run.chars, dialogChar{c: c.Byte, box: c.Box, colors: c.Colors, contig: c.Contiguous, prefixContinuation: c.Prefix})
	}
	obs := &nativeObservation{kind: "dialog", step: row.Step, ink: row.Ink, canvas: src.Canvas, buffer: src.Buffer, after: row.After, dialogRun: run}
	mem := read("r120-soldier-baseline-r1/gui.memory")
	canvas := bytes.Clone(mem[0x2cae0 : 0x2cae0+64000])
	indexed := read("r120-soldier-baseline-r1/gui.final.idx")
	palette := read("r120-soldier-baseline-r1/gui.final.pal")
	if hash(mem) != "8a046c4c7c07c18a45b9fafde1f2833c3fdea6de854a4f4bddcabb3b82c3f12a" || hash(src.Canvas) != "c7189a02fd83b3d8f5264749a7c82b4699ef7e5147a13b810e8db26e13c8007d" {
		t.Fatal("native state fingerprint")
	}
	m, p, _ := hdEventFixtureLoad(t, 1061, "")
	hdEventRun(t, m, p)
	copy(m.Mem, mem)
	targets := draftActualTargetsForTest(t)
	cursor := image.Rect(16, 16, 32, 32)
	journal := &nativeJournal{enabled: true, items: []*nativeObservation{obs}}
	records := []map[string]any{}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			target := targets[locale]
			target.portraits = p
			d := &dialogRuntime{cat: target.dlg}
			st, _, why := d.finish(cloneNativeDialog(run), src.Canvas, src.Step)
			if st == nil || why != "" || st.id != "GAME.TXT:@TUTORIAL14" {
				t.Fatal("complete original paragraph", why)
			}
			draftKeepDialog(d, st, src.Canvas)
			if bytes.Equal(rectBytes(canvas, st.safe), st.afterSafe) {
				t.Fatal("original overlap regression no longer reproduced")
			}
			fixed, changed := draftFitSoldierDialog(target, st, obs, canvas, indexed, palette, cursor)
			if fixed == nil || changed != 54 || fixed.size != 30 || fixed.safe != image.Rect(42, 86, 261, 190) {
				t.Fatal("field layout", changed, "safe", st.safe, "ink", obs.ink, "step", st.complete, obs.step, "portrait", p.soldierDialogForeground(canvas, indexed, palette, cursor) != nil)
			}
			bounds := draftAlphaBounds([]*image.Alpha{fixed.shadow, fixed.normal, fixed.accent})
			if !bounds.In(image.Rect(0, 0, 664, 416)) {
				t.Fatal("text leaves measured column", bounds)
			}
			before := hash(m.Mem)
			im, report, err := draftRebuildTarget(target, journal, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 258000000, 19)
			if err != nil || hash(m.Mem) != before {
				t.Fatal("rebuild state", err)
			}
			items, _ := report["items"].([]map[string]any)
			if len(items) != 1 || items[0]["foreground_pixels"] != 4429 || items[0]["native_occluded_pixels"] != 54 {
				t.Fatal("production text path", report["dialog_misses"], items)
			}
			mask := p.soldierDialogForeground(canvas, indexed, palette, cursor)
			native := draftRGB(indexed, palette)
			protected := 0
			for pos := range canvas {
				if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
					for yy := 0; yy < 4; yy++ {
						for xx := 0; xx < 4; xx++ {
							x, y := pos%320*4+xx, pos/320*4+yy
							if im.RGBAAt(x, y) != native.RGBAAt(x, y) {
								t.Fatal("portrait overwritten", x, y)
							}
							protected++
						}
					}
				}
			}
			if output := os.Getenv("TEST_SOLDIER_OUTPUT"); output != "" {
				f, e := os.Create(filepath.Join(output, locale+".png"))
				if e != nil {
					t.Fatal(e)
				}
				e = png.Encode(f, im)
				f.Close()
				if e != nil {
					t.Fatal(e)
				}
			}
			records = append(records, map[string]any{"locale": locale, "font_px": fixed.size, "native_occluded_pixels": changed, "protected_rgba_pixels": protected, "text_ink": bounds})
			for _, kind := range []string{"missing-tracker", "wrong-id", "wrong-geometry", "unknown-background", "changed-VGA", "wrong-palette", "missing-source", "unknown-source-owner", "unknown-same-value-write"} {
				t.Run(kind, func(t *testing.T) {
					local := *target
					item := *st
					c, v, pal := bytes.Clone(canvas), bytes.Clone(indexed), bytes.Clone(palette)
					saved := p.visible
					defer func() { p.visible = saved }()
					switch kind {
					case "missing-tracker":
						local.portraits = nil
					case "wrong-id":
						item.id = "GAME.TXT:@TUTORIAL13"
					case "wrong-geometry":
						item.safe = item.safe.Add(image.Pt(1, 0))
					case "unknown-background":
						c[180*320+50] ^= 1
						v[180*320+50] = c[180*320+50]
					case "changed-VGA":
						v[180*320+50] ^= 1
					case "wrong-palette":
						for i := range pal {
							pal[i] ^= 1
						}
					case "missing-source":
						p.visible[6*320+210] = hdSceneCell{}
						for i, cell := range p.visible {
							if cell.slot != 0 {
								p.visible[i] = hdSceneCell{}
								break
							}
						}
					case "unknown-source-owner":
						for i, cell := range p.visible {
							if cell.slot != 0 {
								cell.slot = 0
								p.visible[i] = cell
								break
							}
						}
					case "unknown-same-value-write":
						for i, cell := range p.visible {
							if cell.slot != 0 {
								m.CPU.Seg[1] = 0x1234
								m.CPU.IP = 0x500
								p.memoryWrite(hdBuildingCanvas+uint32(i), c[i], c[i])
								break
							}
						}
					}
					if got, _ := draftFitSoldierDialog(&local, &item, obs, c, v, pal, cursor); got != nil {
						t.Fatal("unverified change accepted", kind)
					}
				})
			}
		})
	}
	english, report, err := draftRebuildTarget(targets["en"], journal, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 258000000, 19)
	if err != nil || !bytes.Equal(english.Pix, draftRGB(indexed, palette).Pix) || report["original_rendering"] != true {
		t.Fatal("English changed", err)
	}
	if output := os.Getenv("TEST_SOLDIER_OUTPUT"); output != "" {
		raw, _ := json.MarshalIndent(map[string]any{"result": "PASS_R120_SOLDIER_NOTO_AND_FOREGROUND", "records": records, "english_unchanged": true}, "", "  ")
		if e := os.WriteFile(filepath.Join(output, "check.json"), append(raw, '\n'), 0644); e != nil {
			t.Fatal(e)
		}
	}
}

func TestDraftSoldierMenuForeground(t *testing.T) {
	root := os.Getenv("TEST_MENU_ROOT")
	if root == "" {
		t.Skip("需要合法原版選單來源與士兵快照")
	}
	read := func(name string) []byte {
		t.Helper()
		v, e := os.ReadFile(filepath.Join(root, name))
		if e != nil {
			t.Fatal(e)
		}
		return v
	}
	raw := read("r121-priority-replay-r3/gui.sea-bar-sources.json")
	if hash(raw) != "13f2b60a2414e96cd965d72bbf281de14aff5915cd650b0e95e9b740ef77f4da" {
		t.Fatal("menu source fingerprint")
	}
	var sources []struct {
		Kind           string
		Step           uint64
		Ink, Cursor    image.Rectangle
		Canvas, Buffer []byte
		After          map[int]byte
		Runs           []struct {
			Raw    []byte
			First  map[int]byte    `json:"first_old"`
			Last   map[int]byte    `json:"last_val"`
			Box    image.Rectangle `json:"bbox"`
			Colors map[byte]int
			Tick   uint64 `json:"last"`
			Next   uint32
			Writes int
		}
	}
	if e := json.Unmarshal(raw, &sources); e != nil {
		t.Fatal(e)
	}
	if len(sources) != 3 {
		t.Fatal("complete captured menu sources")
	}
	src := sources[len(sources)-1]
	obs := &nativeObservation{kind: src.Kind, step: src.Step, ink: src.Ink, cursor: src.Cursor, canvas: src.Canvas, buffer: src.Buffer, after: src.After}
	for _, r := range src.Runs {
		obs.seaRuns = append(obs.seaRuns, &seaEvent{raw: r.Raw, firstOld: r.First, lastVal: r.Last, bbox: r.Box, colors: r.Colors, last: r.Tick, next: r.Next, writes: r.Writes})
	}
	mem := read("r120-soldier-baseline-r1/gui.memory")
	canvas := bytes.Clone(mem[0x2cae0 : 0x2cae0+64000])
	indexed := read("r120-soldier-baseline-r1/gui.final.idx")
	palette := read("r120-soldier-baseline-r1/gui.final.pal")
	if hash(mem) != "8a046c4c7c07c18a45b9fafde1f2833c3fdea6de854a4f4bddcabb3b82c3f12a" {
		t.Fatal("current original frame")
	}
	m, p, _ := hdEventFixtureLoad(t, 1061, "")
	hdEventRun(t, m, p)
	copy(m.Mem, mem)
	targets := draftActualTargetsForTest(t)
	cursor := image.Rect(16, 16, 32, 32)
	records := []map[string]any{}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			target := targets[locale]
			target.portraits = p
			candidate, why := draftSeaObserve(target.sea, obs)
			if candidate == nil || why != "" {
				t.Fatal("actual complete menu", why)
			}
			baseline := draftRGB(indexed, palette)
			if got, why := draftPaintSea(baseline, target.sea, candidate, canvas, indexed, palette, cursor); got != nil || why != "sea-safe-changed" {
				t.Fatal("menu overlap regression", why)
			}
			beforeSource, guest, cpu, step := hash(obs.canvas), hash(m.Mem), *m.CPU, m.Steps
			protected := draftPreserveSoldierMenu(target, candidate, canvas, indexed, palette, cursor)
			out := draftRGB(indexed, palette)
			before := bytes.Clone(out.Pix)
			got, why := draftPaintSea(out, target.sea, protected, canvas, indexed, palette, cursor)
			if got == nil || why != "" || got["foreground_pixels"] != 10 || got["source_background_changes"] != 7 || got["font_px"] != 22 {
				t.Fatal("verified menu not drawn", got, why)
			}
			if hash(obs.canvas) != beforeSource || hash(m.Mem) != guest || m.Steps != step || m.CPU.R != cpu.R || m.CPU.Seg != cpu.Seg || m.CPU.IP != cpu.IP || m.CPU.Flags != cpu.Flags {
				t.Fatal("display modified original source or DOS")
			}
			if bytes.Equal(before, out.Pix) {
				t.Fatal("menu did not visibly change")
			}
			mask := p.soldierDialogForeground(canvas, indexed, palette, cursor)
			native := draftRGB(indexed, palette)
			kept := 0
			for pos := range canvas {
				if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
					for yy := 0; yy < 4; yy++ {
						for xx := 0; xx < 4; xx++ {
							x, y := pos%320*4+xx, pos/320*4+yy
							if out.RGBAAt(x, y) != native.RGBAAt(x, y) {
								t.Fatal("foreground damaged", x, y)
							}
							kept++
						}
					}
				}
			}
			records = append(records, map[string]any{"locale": locale, "menu": got["text"], "font_px": got["font_px"], "foreground_pixels": 10, "source_changes": 7, "protected_full_figure_rgba": kept})
			for _, kind := range []string{"unknown-background", "unknown-VGA", "wrong-palette", "unknown-same-value-write", "source-glyph-changed", "other-layer", "malformed-mask", "other-kind"} {
				t.Run(kind, func(t *testing.T) {
					c, v, pal := bytes.Clone(canvas), bytes.Clone(indexed), bytes.Clone(palette)
					local := *candidate
					source := *obs
					local.observation = &source
					cells := p.visible
					oldCPU := *m.CPU
					defer func() { p.visible = cells; *m.CPU = oldCPU }()
					switch kind {
					case "unknown-background":
						c[7*320+40] ^= 1
						v[7*320+40] = c[7*320+40]
					case "unknown-VGA":
						v[7*320+40] ^= 1
					case "wrong-palette":
						for i := range pal {
							pal[i] ^= 1
						}
					case "unknown-same-value-write":
						for at, cell := range p.visible {
							if cell.slot != 0 {
								m.CPU.Seg[1] = 0x1234
								m.CPU.IP = 0x500
								p.memoryWrite(hdBuildingCanvas+uint32(at), c[at], c[at])
								break
							}
						}
					case "source-glyph-changed":
						at := 64000
						for pos := range obs.after {
							at = min(at, pos)
						}
						c[at] ^= 1
						v[at] = c[at]
					case "other-layer":
						local.layer = seaPanelRect
					case "other-kind":
						source.kind = "sea-panel"
					}
					checked := draftPreserveSoldierMenu(target, &local, c, v, pal, cursor)
					if kind == "malformed-mask" {
						checked.foreground = []byte{1}
					}
					im := draftRGB(v, pal)
					oldPixels := bytes.Clone(im.Pix)
					if got, _ := draftPaintSea(im, target.sea, checked, c, v, pal, cursor); got != nil || !bytes.Equal(im.Pix, oldPixels) {
						t.Fatal("unknown source changed display", kind)
					}
				})
			}
		})
	}
	if out := os.Getenv("TEST_MENU_OUTPUT"); out != "" {
		j, _ := json.MarshalIndent(map[string]any{"result": "PASS_R121_FOUR_MENU_FOREGROUND_FIELDS", "records": records, "negative_cases": 32}, "", "  ")
		if e := os.WriteFile(filepath.Join(out, "check.json"), append(j, '\n'), 0644); e != nil {
			t.Fatal(e)
		}
	}
}

func TestDraftDialogSeaForeground(t *testing.T) {
	root := os.Getenv("TEST_PANEL_ROOT")
	if root == "" {
		t.Skip("需要合法原版狀態欄來源與人物快照")
	}
	read := func(name string) []byte {
		t.Helper()
		v, e := os.ReadFile(filepath.Join(root, name))
		if e != nil {
			t.Fatal(e)
		}
		return v
	}
	raw := read("r122-panel-replay-r1/gui.sea-sources.json")
	if hash(raw) != "a9baffb1841b256f55074da6614647f8a8bdd2c2152d848ebc51c8f7fd4594c8" {
		t.Fatal("panel source fingerprint")
	}
	var sources []struct {
		Kind           string
		Step           uint64
		Ink, Cursor    image.Rectangle
		Canvas, Buffer []byte
		After          map[int]byte
		Runs           []struct {
			Raw    []byte
			First  map[int]byte    `json:"first_old"`
			Last   map[int]byte    `json:"last_val"`
			Box    image.Rectangle `json:"bbox"`
			Colors map[byte]int
			Tick   uint64 `json:"last"`
			Next   uint32
			Writes int
		}
	}
	if e := json.Unmarshal(raw, &sources); e != nil {
		t.Fatal(e)
	}
	var observations []*nativeObservation
	for _, src := range sources {
		if src.Kind != "sea-panel" {
			continue
		}
		o := &nativeObservation{kind: src.Kind, step: src.Step, ink: src.Ink, cursor: src.Cursor, canvas: src.Canvas, buffer: src.Buffer, after: src.After}
		for _, r := range src.Runs {
			o.seaRuns = append(o.seaRuns, &seaEvent{raw: r.Raw, firstOld: r.First, lastVal: r.Last, bbox: r.Box, colors: r.Colors, last: r.Tick, next: r.Next, writes: r.Writes})
		}
		observations = append(observations, o)
	}
	if len(observations) != 4 {
		t.Fatal("four actual panel observations", len(observations))
	}
	mem := read("r120-soldier-baseline-r1/gui.memory")
	if hash(mem) != "8a046c4c7c07c18a45b9fafde1f2833c3fdea6de854a4f4bddcabb3b82c3f12a" {
		t.Fatal("original state fingerprint")
	}
	canvas := bytes.Clone(mem[0x2cae0 : 0x2cae0+64000])
	indexed := read("r120-soldier-baseline-r1/gui.final.idx")
	palette := read("r120-soldier-baseline-r1/gui.final.pal")
	m, p, _ := hdEventFixtureLoad(t, 1061, "")
	hdEventRun(t, m, p)
	copy(m.Mem, mem)
	cursor := image.Rect(16, 16, 32, 32)
	mask, id := p.seaDialogForeground(canvas, indexed, palette, cursor)
	if id != 1061 || !bytes.Equal(mask, p.soldierDialogForeground(canvas, indexed, palette, cursor)) {
		t.Fatal("complete original foreground differs")
	}
	targets := draftActualTargetsForTest(t)
	records := []map[string]any{}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			target := targets[locale]
			target.portraits = p
			out := draftRGB(indexed, palette)
			for n, o := range observations {
				t.Run(fmt.Sprint(n), func(t *testing.T) {
					candidate, why := draftSeaObserve(target.sea, o)
					if candidate == nil || why != "" {
						t.Fatal("actual panel not translated", why)
					}
					old := draftRGB(indexed, palette)
					if got, _ := draftPaintSea(old, target.sea, candidate, canvas, indexed, palette, cursor); got != nil {
						t.Fatal("expected original occluded source")
					}
					guest, source, step, cpu := hash(m.Mem), hash(o.canvas), m.Steps, *m.CPU
					protected := draftPreserveDialogSea(target, candidate, canvas, indexed, palette, cursor)
					if protected.foregroundSource != 1061 || len(protected.foreground) != 8000 {
						t.Fatal("foreground not established", candidate.row.text)
					}
					got, why := draftPaintSea(out, target.sea, protected, canvas, indexed, palette, cursor)
					if got == nil || why != "" || got["foreground_source"] != 1061 {
						t.Fatal("panel not painted", got, why)
					}
					if hash(m.Mem) != guest || hash(o.canvas) != source || m.Steps != step || m.CPU.R != cpu.R || m.CPU.Seg != cpu.Seg || m.CPU.IP != cpu.IP || m.CPU.Flags != cpu.Flags {
						t.Fatal("display changed original state/source")
					}
					native := draftRGB(indexed, palette)
					for pos := range canvas {
						if mask[pos>>3]&(1<<uint(pos&7)) == 0 {
							continue
						}
						for yy := 0; yy < 4; yy++ {
							for xx := 0; xx < 4; xx++ {
								x, y := pos%320*4+xx, pos/320*4+yy
								if out.RGBAAt(x, y) != native.RGBAAt(x, y) {
									t.Fatal("figure changed", x, y)
								}
							}
						}
					}
					alpha := image.NewAlpha(image.Rect(0, 0, seaPanelRect.Dx()*4, seaPanelRect.Dy()*4))
					for _, part := range protected.row.parts {
						x, y := part.x-seaPanelRect.Min.X*4, candidate.row.bbox.Min.Y*4-target.sea.fonts[part.size].cjkTop-seaPanelRect.Min.Y*4+protected.textOffsetY
						if target.sea.seaDraw(alpha, part.text, x, y, part.size) {
							t.Fatal("measured panel clipped")
						}
					}
					uncovered, totalGlyphPixels := 0, 0
					for y := 0; y < alpha.Rect.Dy(); y++ {
						for x := 0; x < alpha.Rect.Dx(); x++ {
							pos := (y/4+seaPanelRect.Min.Y)*320 + x/4 + seaPanelRect.Min.X
							if alpha.AlphaAt(x, y).A != 0 {
								totalGlyphPixels++
								if mask[pos>>3]&(1<<uint(pos&7)) == 0 {
									uncovered++
								}
							}
						}
					}
					if totalGlyphPixels == 0 {
						t.Fatal("translated row mask is empty")
					}
					safe := got["safe"].(image.Rectangle)
					if safe.Min.Y != o.ink.Min.Y || safe.Max.Y != o.ink.Max.Y {
						t.Fatal("text exceeds original row height", safe, o.ink)
					}
					records = append(records, map[string]any{"locale": locale, "source": got["source"], "text": got["text"], "font_px": got["font_px"], "baseline_shift_px": got["baseline_shift_px"], "safe": safe, "native_ink": got["native_ink"], "uncovered_glyph_pixels": uncovered, "glyph_pixels": totalGlyphPixels, "fully_occluded": uncovered == 0, "foreground_source": 1061})
					for _, kind := range []string{"unknown-background", "unknown-glyph", "unknown-VGA", "wrong-palette", "unknown-same-value-write", "inconsistent-source", "missing-tracker"} {
						t.Run(kind, func(t *testing.T) {
							c, v, pal := bytes.Clone(canvas), bytes.Clone(indexed), bytes.Clone(palette)
							local := *candidate
							obs := *o
							obs.canvas = bytes.Clone(o.canvas)
							local.observation = &obs
							cells, oldCPU, tracker := p.visible, *m.CPU, target.portraits
							defer func() { p.visible = cells; *m.CPU = oldCPU; target.portraits = tracker }()
							find := func(glyph bool) int {
								for y := safe.Min.Y; y < safe.Max.Y; y++ {
									for x := safe.Min.X; x < safe.Max.X; x++ {
										pos := y*320 + x
										_, isGlyph := o.after[pos]
										if mask[pos>>3]&(1<<uint(pos&7)) == 0 && isGlyph == glyph {
											return pos
										}
									}
								}
								t.Fatal("required uncovered test point", kind)
								return 0
							}
							switch kind {
							case "unknown-background":
								at := find(false)
								c[at] ^= 1
								v[at] = c[at]
							case "unknown-glyph":
								at := find(true)
								c[at] ^= 1
								v[at] = c[at]
							case "unknown-VGA":
								v[find(false)] ^= 1
							case "wrong-palette":
								for i := range pal {
									pal[i] ^= 1
								}
							case "unknown-same-value-write":
								for at, cell := range p.visible {
									if cell.slot != 0 {
										m.CPU.Seg[1] = 0x1234
										m.CPU.IP = 0x500
										p.memoryWrite(hdBuildingCanvas+uint32(at), c[at], c[at])
										break
									}
								}
							case "inconsistent-source":
								for at := range obs.after {
									obs.canvas[at] ^= 1
									break
								}
							case "missing-tracker":
								target.portraits = nil
							}
							checked := draftPreserveDialogSea(target, &local, c, v, pal, cursor)
							im := draftRGB(v, pal)
							before := bytes.Clone(im.Pix)
							if got, _ := draftPaintSea(im, target.sea, checked, c, v, pal, cursor); got != nil || !bytes.Equal(before, im.Pix) {
								t.Fatal("unknown source accepted", kind)
							}
						})
					}
					c, v := bytes.Clone(canvas), bytes.Clone(indexed)
					at := 199*320 + 319
					c[at] ^= 1
					v[at] = c[at]
					checked := draftPreserveDialogSea(target, candidate, c, v, palette, cursor)
					if got, why := draftPaintSea(draftRGB(v, palette), target.sea, checked, c, v, palette, cursor); got == nil || why != "" {
						t.Fatal("unrelated outside-row update blocked", why)
					}
				})
			}
			if dir := os.Getenv("TEST_PANEL_OUTPUT"); dir != "" {
				fd, e := os.Create(filepath.Join(dir, "panel-"+locale+".png"))
				if e != nil {
					t.Fatal(e)
				}
				e = png.Encode(fd, out)
				fd.Close()
				if e != nil {
					t.Fatal(e)
				}
			}
		})
	}
	if len(records) != 16 {
		t.Fatal("missing field/locale", len(records))
	}
	if dir := os.Getenv("TEST_PANEL_OUTPUT"); dir != "" {
		raw, e := json.MarshalIndent(map[string]any{"result": "PASS_R122_FOUR_PANEL_FIELDS_FOUR_LOCALES", "fields": records, "negative_cases": 112, "native_state_unchanged": true}, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(dir, "check.json"), append(raw, '\n'), 0644); e != nil {
			t.Fatal(e)
		}
	}
}

func TestDraftSeaDialogSixForegroundSources(t *testing.T) {
	root := os.Getenv("TEST_PANEL_ROOT")
	if root == "" {
		t.Skip("需要合法原版人物來源")
	}
	paletteRaw, e := os.ReadFile("/repo/workplace/reports/goal186-display-hd/hd-dialog-figures-r98/r98-embedded-palette-expectations-r1.json")
	if e != nil || hash(paletteRaw) != "fa1ae2c74ab6bbffe6ce9e9fe8ce2d9f8dfce6e0a1c813767a82e1c28edec18c" {
		t.Fatal("six source palette fingerprint", e)
	}
	var palettes struct {
		Rows []struct {
			ID  int    `json:"research_id"`
			DAC string `json:"DAC_base64"`
		}
	}
	if e = json.Unmarshal(paletteRaw, &palettes); e != nil {
		t.Fatal(e)
	}

	var ready struct {
		Rows []struct {
			ID      int
			Palette string `json:"palette_base64"`
		}
	}
	raw, e := os.ReadFile(filepath.Join(root, "r101-scene-wiring-ready-r1.json"))
	if e != nil {
		t.Fatal(e)
	}
	if e = json.Unmarshal(raw, &ready); e != nil {
		t.Fatal(e)
	}
	for _, rid := range []int{1060, 1061, 1062, 1063, 1064, 1065} {
		t.Run(fmt.Sprint(rid), func(t *testing.T) {
			var p *hdSceneRuntime
			var canvas, palette []byte
			if rid == 1062 || rid == 1065 {
				m := golem.New()
				p = &hdSceneRuntime{h: &hdRuntime{m: m}, pending: map[int]hdSceneCursorPair{}}
				for _, d := range hdSceneDefinitions {
					p.frames = append(p.frames, &hdSceneFrame{hdSceneDefinition: d})
				}
				var frame *hdSceneFrame
				slot := 0
				for n, f := range p.frames {
					if f.id == rid {
						frame = f
						slot = n + 1
						break
					}
				}
				if frame == nil {
					t.Fatal("typed figure missing")
				}
				s := frame.sprite
				pixels, e := os.ReadFile(fmt.Sprintf("/repo/workplace/reports/goal186-display-hd/hd-full-assets-r49/decoded-public-r3/pixels/%04d.idx", rid))
				if e != nil {
					t.Fatal(e)
				}
				if len(pixels) != s.width*s.height || hash(pixels) != s.indexedSHA {
					t.Fatal("decoded original fingerprint")
				}
				frame.native = bytes.Repeat([]byte{253}, 64000)
				used := [256]bool{}
				canvas = make([]byte, 64000)
				for y := 0; y < s.height; y++ {
					for x := 0; x < s.width; x++ {
						local := y*320 + x
						value := pixels[y*s.width+x]
						frame.native[local] = value
						if value == 253 {
							continue
						}
						used[value] = true
						pos := (y+40)*320 + x + 100
						canvas[pos] = value
						p.visible[pos] = hdSceneCell{slot: uint16(slot), local: uint16(local), value: value}
					}
				}
				if hash(frame.native) != frame.nativeSHA {
					t.Fatal("padded original fingerprint")
				}
				for n, yes := range used {
					if yes {
						frame.indices = append(frame.indices, byte(n))
					}
				}
				frame.decoded = 1
				for _, r := range ready.Rows {
					if r.ID == rid {
						palette, e = base64.StdEncoding.DecodeString(r.Palette)
						if e != nil {
							t.Fatal(e)
						}
					}
				}
			} else {
				m, original, _ := hdEventFixtureLoad(t, rid, "")
				hdEventRun(t, m, original)
				p = original
				canvas = bytes.Clone(m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000])
				for _, row := range palettes.Rows {
					if row.ID == rid {
						palette, e = base64.StdEncoding.DecodeString(row.DAC)
						if e != nil {
							t.Fatal(e)
						}
					}
				}
			}
			mask, id := p.seaDialogForeground(canvas, canvas, palette, image.Rectangle{})
			if len(mask) != 8000 || id != rid {
				t.Fatal("complete foreground rejected", rid, id)
			}
			count := 0
			for _, b := range mask {
				for bit := uint(0); bit < 8; bit++ {
					if b&(1<<bit) != 0 {
						count++
					}
				}
			}
			var expected int
			for _, f := range p.frames {
				if f.id == rid {
					expected = f.sprite.opaque
				}
			}
			if count != expected {
				t.Fatal("opaque source count", count, expected)
			}
			for at, cell := range p.visible {
				if cell.slot != 0 {
					original := p.visible[at]
					p.visible[at] = hdSceneCell{}
					if got, _ := p.seaDialogForeground(canvas, canvas, palette, image.Rectangle{}); got != nil {
						t.Fatal("incomplete foreground accepted")
					}
					p.visible[at] = original
					p.visible[at].local = 64000
					if got, _ := p.seaDialogForeground(canvas, canvas, palette, image.Rectangle{}); got != nil {
						t.Fatal("invalid source coordinate accepted")
					}
					p.visible[at] = original
					break
				}
			}
		})
	}
}

func TestDraftLandfallDialogForeground(t *testing.T) {
	root := os.Getenv("TEST_LANDFALL_ROOT")
	if root == "" {
		t.Skip("需要合法原版正常登陸觀測及快照")
	}
	read := func(name string) []byte {
		t.Helper()
		b, e := os.ReadFile(filepath.Join(root, name))
		if e != nil {
			t.Fatal(e)
		}
		return b
	}
	raw := read("landfall-observations.json")
	if hash(raw) != "6181a2ef6bc0bc4ea0713c03204ca5de4ffce54f022798820fee1b67166c16d7" {
		t.Fatal("normal observation fingerprint")
	}
	var rows []struct {
		Kind       string
		Step       uint64
		Ink        image.Rectangle
		SourceBase uint32          `json:"source_base"`
		ReadPos    int             `json:"read_pos"`
		Canvas     []byte          `json:"source_canvas"`
		Buffer     []byte          `json:"source_buffer"`
		FirstOld   map[int]byte    `json:"first_old"`
		LastText   map[int]bool    `json:"last_text"`
		After      map[int]byte    `json:"after_pixels"`
		Shadow     bool            `json:"shadow_written"`
		Others     image.Rectangle `json:"other_writes"`
		Chars      []struct {
			Byte       byte
			Box        image.Rectangle
			Colors     map[byte]int
			Contiguous bool
			Prefix     bool `json:"prefix_continuation"`
		} `json:"characters"`
	}
	if e := json.Unmarshal(raw, &rows); e != nil {
		t.Fatal(e)
	}
	if len(rows) != 2 {
		t.Fatal("complete body and choices", len(rows))
	}
	journal := &nativeJournal{enabled: true}
	for _, row := range rows {
		if len(row.Canvas) != 64000 || len(row.Buffer) != 0 {
			t.Fatal("complete native observation")
		}
		run := &dialogRun{base: row.SourceBase, readPos: row.ReadPos, firstOld: row.FirstOld, lastText: row.LastText, shadowWritten: row.Shadow, others: row.Others}
		for _, c := range row.Chars {
			run.chars = append(run.chars, dialogChar{c: c.Byte, box: c.Box, colors: c.Colors, contig: c.Contiguous, prefixContinuation: c.Prefix})
		}
		journal.items = append(journal.items, &nativeObservation{kind: "dialog", step: row.Step, ink: row.Ink, canvas: row.Canvas, buffer: row.Buffer, after: row.After, dialogRun: run})
	}
	obs, options := journal.items[0], journal.items[1]
	mem := read("gui.memory")
	indexed := read("gui.final.idx")
	palette := read("gui.final.pal")
	if hash(mem) != "c8bd66614154a760819b03b454fc85cd3bbe24eebca757b20901fd2c522e3283" || hash(indexed) != "5e1c5d3f40c00f5a5436fbd292aa81fea9f19e0a55b54401eb62e02462634dae" || hash(palette) != "7fc2f577301f1a337ed658470b425d9ec907c0278b1f7732fc018bb3ab28aa7a" {
		t.Fatal("native state fingerprint")
	}
	canvas := bytes.Clone(mem[0x2cae0 : 0x2cae0+64000])
	cursor := image.Rect(16, 16, 32, 32)
	m, p, _ := hdEventFixtureLoad(t, 1063, "")
	hdEventRun(t, m, p)
	copy(m.Mem, mem)
	targets := draftActualTargetsForTest(t)
	records := []map[string]any{}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			target := targets[locale]
			target.portraits = p
			d := &dialogRuntime{cat: target.dlg}
			body, _, why := d.finish(cloneNativeDialog(obs.dialogRun), obs.canvas, obs.step)
			if body == nil || why != "" || body.id != "GAME.TXT:@LANDFALL:0x00000FAD" {
				t.Fatal("body identity", why)
			}
			draftKeepDialog(d, body, obs.canvas)
			scoped := draftLandfallDialogContext(target, d, body, obs, options, palette, cursor, false)
			choice, _, why := scoped.finish(cloneNativeDialog(options.dialogRun), options.canvas, options.step)
			if choice == nil || why != "" {
				t.Fatal("choice identity", why)
			}
			draftKeepDialog(d, choice, options.canvas)
			if len(choice.items) != 2 {
				t.Fatal("complete choices", choice.items)
			}
			fixed, changed := draftFitLandfallDialog(target, body, obs, choice, canvas, indexed, palette, cursor)
			if fixed == nil || changed != 5 || fixed.size != 30 || fixed.safe != image.Rect(65, 119, 254, 143) {
				t.Fatal("measured field", fixed, changed)
			}
			bounds := draftAlphaBounds([]*image.Alpha{fixed.shadow, fixed.normal, fixed.accent})
			layout := image.Rect(65, 124, 254, 143)
			relative := image.Rect(0, 20, 756, 96)
			if !bounds.In(relative) {
				t.Fatal("text leaves portrait-free layout", bounds)
			}
			before := hash(m.Mem)
			im, report, e := draftRebuildTarget(target, journal, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 80800000, 19)
			if e != nil || hash(m.Mem) != before {
				t.Fatal("display changed original memory", e)
			}
			items, _ := report["items"].([]map[string]any)
			found := false
			for _, it := range items {
				if it["id"] == body.id {
					found = true
					if it["foreground_source"] != 1063 || it["foreground_pixels"] != 5910 || it["native_occluded_pixels"] != 5 || it["layout_safe"] != layout {
						t.Fatal("foreground record", it)
					}
				}
			}
			if !found {
				t.Fatal("body absent from integrated renderer", report["dialog_misses"], items)
			}
			mask, id := p.seaDialogForeground(canvas, indexed, palette, cursor)
			if id != 1063 {
				t.Fatal("portrait identity")
			}
			native := draftRGB(indexed, palette)
			for pos := range canvas {
				if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
					for yy := 0; yy < 4; yy++ {
						for xx := 0; xx < 4; xx++ {
							x, y := pos%320*4+xx, pos/320*4+yy
							if im.RGBAAt(x, y) != native.RGBAAt(x, y) {
								t.Fatal("portrait overwritten", x, y)
							}
						}
					}
				}
			}
			if out := os.Getenv("TEST_LANDFALL_OUTPUT"); out != "" {
				f, e := os.Create(filepath.Join(out, locale+".png"))
				if e != nil {
					t.Fatal(e)
				}
				e = png.Encode(f, im)
				f.Close()
				if e != nil {
					t.Fatal(e)
				}
			}

			t.Run("initial-window-and-paired-redraw", func(t *testing.T) {
				late := *options
				late.step = body.complete + 2000000
				if got := draftLandfallDialogContext(target, d, body, obs, &late, palette, cursor, false); got != d {
					t.Fatal("initial pairing deadline was widened")
				}
				source := *options
				source.step += 4000000
				redrawn := &nativeJournal{enabled: true, items: []*nativeObservation{obs, options, &source}}
				_, receipt, err := draftRebuildTarget(target, redrawn, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 84800000, 19)
				if err != nil {
					t.Fatal(err)
				}
				present := false
				for _, item := range receipt["items"].([]map[string]any) {
					present = present || item["id"] == body.id
				}
				if !present {
					t.Fatal("paired redraw lost body", receipt["dialog_misses"])
				}
				unpaired := &nativeJournal{enabled: true, items: []*nativeObservation{obs, &source}}
				_, receipt, err = draftRebuildTarget(target, unpaired, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 84800000, 19)
				if err != nil {
					t.Fatal(err)
				}
				for _, item := range receipt["items"].([]map[string]any) {
					if item["id"] == body.id {
						t.Fatal("unpaired late choice revived body")
					}
				}
			})
			t.Run("unknown-option-source", func(t *testing.T) {
				source := *options
				source.dialogRun = cloneNativeDialog(source.dialogRun)
				source.dialogRun.chars[0].c = '?'
				if got := draftLandfallDialogContext(target, d, body, obs, &source, palette, cursor, true); got != d {
					t.Fatal("unknown original option narrowed catalog")
				}
			})
			font := target.dlg.fonts[fixed.size]
			records = append(records, map[string]any{"locale": locale, "font_px": fixed.size, "source_safe": fixed.safe, "layout_safe": layout, "ink_local_to_source_safe": bounds, "glyph_origin_y": layout.Min.Y*4 + 4 - font.cjkTop, "native_occluded_pixels": changed, "foreground_source": 1063, "foreground_pixels": 5910})
			for _, kind := range []string{"missing-tracker", "wrong-key", "wrong-geometry", "unknown-background", "changed-vga", "wrong-palette", "lost-owner", "wrong-choice", "erased-choice", "missing-font", "closed-dialog"} {
				t.Run(kind, func(t *testing.T) {
					local := *target
					item := *body
					pick := *choice
					c, v, pal := bytes.Clone(canvas), bytes.Clone(indexed), bytes.Clone(palette)
					saved := p.visible
					defer func() { p.visible = saved }()
					switch kind {
					case "missing-tracker":
						local.portraits = nil
					case "wrong-key":
						item.id = "GAME.TXT:@LANDFALL2:0x0000103C"
					case "wrong-geometry":
						item.safe = item.safe.Add(image.Pt(1, 0))
					case "unknown-background":
						c[140*320+66] ^= 1
						v[140*320+66] = c[140*320+66]
					case "changed-vga":
						v[140*320+66] ^= 1
					case "wrong-palette":
						for i := range pal {
							pal[i] ^= 1
						}
					case "lost-owner":
						for pos := range c {
							if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
								p.visible[pos] = hdSceneCell{}
								break
							}
						}
					case "wrong-choice":
						pick.items = append([]string(nil), pick.items...)
						pick.items[0], pick.items[1] = pick.items[1], pick.items[0]
					case "erased-choice":
						pick.afterSafe = bytes.Clone(pick.afterSafe)
						pick.afterSafe[0] ^= 1
					case "missing-font":
						cat := *target.dlg
						cat.fonts = nil
						local.dlg = &cat
					case "closed-dialog":
						for y := 119; y < 168; y++ {
							for x := 65; x < 254; x++ {
								c[y*320+x] = 0
								v[y*320+x] = 0
							}
						}
					}
					if got, _ := draftFitLandfallDialog(&local, &item, obs, &pick, c, v, pal, cursor); got != nil {
						t.Fatal("unverified source accepted", kind)
					}
				})
			}
		})
	}
	english, report, e := draftRebuildTarget(targets["en"], journal, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 80800000, 19)
	if e != nil || !bytes.Equal(english.Pix, draftRGB(indexed, palette).Pix) || report["original_rendering"] != true {
		t.Fatal("English changed", e)
	}
	if out := os.Getenv("TEST_LANDFALL_OUTPUT"); out != "" {
		b, _ := json.MarshalIndent(map[string]any{"result": "PASS_R127_LANDFALL_NOTO_AND_FOREGROUND", "records": records, "english_original_unchanged": true}, "", "  ")
		if e := os.WriteFile(filepath.Join(out, "check.json"), append(b, '\n'), 0644); e != nil {
			t.Fatal(e)
		}
	}
}

func TestDraftAttackConfirmationForeground(t *testing.T) {
	root := os.Getenv("TEST_ATTACK_ROOT")
	if root == "" {
		t.Skip("需要合法原版正常攻擊確認的觀測與快照")
	}
	read := func(name string) []byte {
		t.Helper()
		b, e := os.ReadFile(filepath.Join(root, name))
		if e != nil {
			t.Fatal(e)
		}
		return b
	}
	raw := read("attack-observations.json")
	if hash(raw) != "72cc4231391979945ace0dbaa2323d04185db5ffbda4d7ca50b8c3934900dad0" {
		t.Fatal("normal source fingerprint")
	}
	var rows []struct {
		Kind       string
		Step       uint64
		Ink        image.Rectangle
		SourceBase uint32          `json:"source_base"`
		ReadPos    int             `json:"read_pos"`
		Canvas     []byte          `json:"source_canvas"`
		Buffer     []byte          `json:"source_buffer"`
		FirstOld   map[int]byte    `json:"first_old"`
		LastText   map[int]bool    `json:"last_text"`
		After      map[int]byte    `json:"after_pixels"`
		Shadow     bool            `json:"shadow_written"`
		Others     image.Rectangle `json:"other_writes"`
		Chars      []struct {
			Byte       byte
			Box        image.Rectangle
			Colors     map[byte]int
			Contiguous bool
			Prefix     bool `json:"prefix_continuation"`
		} `json:"characters"`
	}
	if e := json.Unmarshal(raw, &rows); e != nil {
		t.Fatal(e)
	}
	if len(rows) != 2 {
		t.Fatal("body and complete choices")
	}
	j := &nativeJournal{enabled: true}
	for _, row := range rows {
		if len(row.Canvas) != 64000 || len(row.Buffer) != 0 {
			t.Fatal("native snapshot")
		}
		r := &dialogRun{base: row.SourceBase, readPos: row.ReadPos, firstOld: row.FirstOld, lastText: row.LastText, shadowWritten: row.Shadow, others: row.Others}
		for _, c := range row.Chars {
			r.chars = append(r.chars, dialogChar{c: c.Byte, box: c.Box, colors: c.Colors, contig: c.Contiguous, prefixContinuation: c.Prefix})
		}
		j.items = append(j.items, &nativeObservation{kind: "dialog", step: row.Step, ink: row.Ink, canvas: row.Canvas, buffer: row.Buffer, after: row.After, dialogRun: r})
	}
	mem, indexed, palette := read("gui.memory"), read("gui.final.idx"), read("gui.final.pal")
	if hash(mem) != "82ea1776111e7a3eceda78193df15bb4030f67623a4f18ab60a3bbed034cd6d7" || hash(indexed) != "20c74321bc57d8c00837310481bf8e885072689998788c11de36934e7eb30e11" || hash(palette) != "675559f7a1c3b272181164709310dbfe3642fc7b8aa7cad97a3dc811b3c04dcd" {
		t.Fatal("normal endpoint fingerprint")
	}
	canvas := bytes.Clone(mem[0x2cae0 : 0x2cae0+64000])
	cursor := image.Rect(16, 16, 32, 32)
	m, p, _ := hdEventFixtureLoad(t, 1061, "")
	// 位移只用於已驗D46局部來源fixture，目的位置來自當次正常GUI完整持有權遮罩。
	p.spriteCall = nil
	m.CPU.R[2] -= 15
	stack := int(m.CPU.Seg[2])*16 + int(m.CPU.R[4])
	y := binary.LittleEndian.Uint16(m.Mem[stack+4:])
	binary.LittleEndian.PutUint16(m.Mem[stack+4:], y+28)
	hdEventRun(t, m, p)
	copy(m.Mem, mem)
	targets := draftActualTargetsForTest(t)
	records := []map[string]any{}
	for _, locale := range []string{"zh-Hant", "zh-Hans", "ja", "ko"} {
		t.Run(locale, func(t *testing.T) {
			target := targets[locale]
			target.portraits = p
			d := &dialogRuntime{cat: target.dlg, misses: map[string]int{}}
			obs, options := j.items[0], j.items[1]
			body, _, why := d.finish(cloneNativeDialog(obs.dialogRun), obs.canvas, obs.step)
			if body == nil || why != "" || body.id != "GAME.TXT:@WHACKINDIANS:0x000038BD" {
				t.Fatal("body identity", why)
			}
			draftKeepDialog(d, body, obs.canvas)
			scoped := draftAttackDialogContext(target, d, body, obs, options, canvas, indexed, palette, cursor, false)
			if scoped == d {
				t.Fatal("source-scoped choice context rejected")
			}
			choice, _, why := scoped.finish(cloneNativeDialog(options.dialogRun), options.canvas, options.step)
			if choice == nil || why != "" || !draftAttackChoice(target, choice) {
				t.Fatal("complete choice identity", why)
			}
			draftKeepDialog(d, choice, options.canvas)
			fixed, changed := draftFitAttackDialog(target, body, obs, choice, canvas, indexed, palette, cursor)
			if fixed == nil || changed != 13 || fixed.size != 30 || fixed.safe != image.Rect(57, 114, 246, 138) {
				t.Fatal("measured field", fixed, changed)
			}
			bounds := draftAlphaBounds([]*image.Alpha{fixed.shadow, fixed.normal, fixed.accent})
			if !bounds.In(image.Rect(0, 12, 544, 96)) {
				t.Fatal("text leaves portrait-free field", bounds)
			}
			before := hash(m.Mem)
			im, report, e := draftRebuildTarget(target, j, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 237800000, 19)
			if e != nil || hash(m.Mem) != before {
				t.Fatal("display changed native memory", e)
			}
			foundBody, foundChoice := false, false
			for _, it := range report["items"].([]map[string]any) {
				if it["id"] == body.id {
					foundBody = true
					if it["foreground_source"] != 1061 || it["foreground_pixels"] != 4429 || it["native_occluded_pixels"] != 13 || it["layout_safe"] != image.Rect(57, 117, 193, 138) {
						t.Fatal("foreground diagnostic", it)
					}
				}
				if it["id"] == choice.id {
					foundChoice = true
				}
			}
			if !foundBody || !foundChoice {
				t.Fatal("integrated body or choices absent", foundBody, foundChoice, report["dialog_misses"])
			}
			mask, id := p.seaDialogForeground(canvas, indexed, palette, cursor)
			if id != 1061 {
				t.Fatal("source identity")
			}
			original := draftRGB(indexed, palette)
			foregroundPixels := 0
			for pos := 0; pos < 64000; pos++ {
				if mask[pos>>3]&(1<<uint(pos&7)) != 0 {
					for y := 0; y < 4; y++ {
						for x := 0; x < 4; x++ {
							if im.RGBAAt(pos%320*4+x, pos/320*4+y) != original.RGBAAt(pos%320*4+x, pos/320*4+y) {
								t.Fatal("portrait changed", pos)
							}
							foregroundPixels++
						}
					}
				}
			}
			if foregroundPixels != 4429*16 {
				t.Fatal("incomplete foreground")
			}

			t.Run("partial-portrait-in-choice-snapshot", func(t *testing.T) {
				partial := *options
				partial.canvas = bytes.Clone(options.canvas)
				partial.dialogRun = cloneNativeDialog(options.dialogRun)
				partial.dialogRun.others = image.Rect(195, 34, 266, 129)
				removed := 0
				for pos := 0; pos < 64000; pos++ {
					if pos/320 >= 129 && mask[pos>>3]&(1<<uint(pos&7)) != 0 {
						partial.canvas[pos] = obs.canvas[pos]
						removed++
					}
				}
				if removed == 0 || bytes.Equal(partial.canvas, options.canvas) ||
					!bytes.Equal(rectBytes(partial.canvas, choice.safe), choice.afterSafe) {
					t.Fatal("partial source fixture must keep all original choice pixels")
				}
				scoped := draftAttackDialogContext(target, d, body, obs, &partial, canvas, indexed, palette, cursor, false)
				if scoped == d {
					t.Fatal("complete current source rejected because the older choice snapshot was partial")
				}
				candidate, _, reason := scoped.finish(cloneNativeDialog(partial.dialogRun), partial.canvas, partial.step)
				if candidate == nil || reason != "" || !draftAttackChoice(target, candidate) {
					t.Fatal("partial snapshot choices", reason)
				}
				draftKeepDialog(d, candidate, partial.canvas)
				if fit, changed := draftFitAttackDialog(target, body, obs, candidate, canvas, indexed, palette, cursor); fit == nil || changed != 13 {
					t.Fatal("complete current field missing", changed)
				}
				clone := &nativeJournal{enabled: true, items: []*nativeObservation{obs, &partial}}
				im, report, err := draftRebuildTarget(target, clone, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 237800000, 19)
				if err != nil || im == nil {
					t.Fatal(err)
				}
				found := false
				for _, field := range report["items"].([]map[string]any) {
					found = found || field["id"] == body.id
				}
				if !found {
					t.Fatal("partial snapshot integration lost body")
				}
			})

			for _, name := range []string{"body-id", "body-safe", "source-ink", "source-step", "short-source", "unknown-background", "vga", "palette", "missing-source", "choice-id", "choice-safe", "choice-expired", "choice-items", "choice-before-body"} {
				t.Run(name, func(t *testing.T) {
					local := *target
					item := *body
					source := *obs
					pick := *choice
					c, v, pal := bytes.Clone(canvas), bytes.Clone(indexed), bytes.Clone(palette)
					switch name {
					case "body-id":
						item.id += "?"
					case "body-safe":
						item.safe.Max.X--
					case "source-ink":
						source.ink.Max.X--
					case "source-step":
						source.step++
					case "short-source":
						item.afterSafe = item.afterSafe[:len(item.afterSafe)-1]
					case "unknown-background":
						at := 114*320 + 57
						c[at] ^= 1
						v[at] = c[at]
					case "vga":
						v[114*320+57] ^= 1
					case "palette":
						for i := range pal {
							pal[i] ^= 1
						}
					case "missing-source":
						local.portraits = nil
					case "choice-id":
						pick.id += "?"
					case "choice-safe":
						pick.safe.Max.X++
					case "choice-expired":
						pick.phase = "expired"
					case "choice-items":
						pick.items = []string{choice.items[1], choice.items[0]}
					case "choice-before-body":
						pick.complete = body.complete - 1
					}
					if got, _ := draftFitAttackDialog(&local, &item, &source, &pick, c, v, pal, cursor); got != nil {
						t.Fatal("unsafe field accepted")
					}
				})
			}
			t.Run("first-choice-2M-boundary", func(t *testing.T) {
				late := *options
				late.step = body.complete + 2000000
				if got := draftAttackDialogContext(target, d, body, obs, &late, canvas, indexed, palette, cursor, false); got != d {
					t.Fatal("late first pair accepted")
				}
			})
			t.Run("paired-redraw", func(t *testing.T) {
				late := *options
				late.step = body.complete + 4000000
				if got := draftAttackDialogContext(target, d, body, obs, &late, canvas, indexed, palette, cursor, true); got == d {
					t.Fatal("valid redraw rejected")
				}
			})
			if output := os.Getenv("TEST_ATTACK_OUTPUT"); output != "" {
				writeAttackPreviewPNG(t, filepath.Join(output, "attack-"+locale+".png"), im)
			}
			records = append(records, map[string]any{"locale": locale, "safe": fixed.safe, "layout": image.Rect(57, 117, 193, 138), "font_px": fixed.size, "bounds": bounds, "foreground_pixels": foregroundPixels, "native_occluded_pixels": changed})
		})
	}
	t.Run("english-original", func(t *testing.T) {
		im, _, e := draftRebuildTarget(targets["en"], j, canvas, mem[0x3bb00:0x3bb00+64000], indexed, palette, cursor, 237800000, 19)
		if e != nil || !bytes.Equal(im.Pix, draftRGB(indexed, palette).Pix) {
			t.Fatal("English changed", e)
		}
	})
	if output := os.Getenv("TEST_ATTACK_OUTPUT"); output != "" {
		b, e := json.MarshalIndent(records, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(filepath.Join(output, "attack-profile-results.json"), append(b, '\n'), 0644); e != nil {
			t.Fatal(e)
		}
	}
}

func writeAttackPreviewPNG(t *testing.T, name string, im image.Image) {
	t.Helper()
	f, e := os.Create(name)
	if e != nil {
		t.Fatal(e)
	}
	err := png.Encode(f, im)
	closeErr := f.Close()
	if err != nil {
		t.Fatal(err)
	}
	if closeErr != nil {
		t.Fatal(closeErr)
	}
}
