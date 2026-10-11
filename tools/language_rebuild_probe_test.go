package main

import (
	"bytes"
	"encoding/json"
	"image"
	"image/color"
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
