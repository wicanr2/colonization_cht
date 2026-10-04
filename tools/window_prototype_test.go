package main

import (
	"encoding/json"
	"image"
	"testing"

	"github.com/hajimehoshi/ebiten/v2"
	golem "github.com/wicanr2/dosgolem"
)

func TestSeaRowOcclusionRecovery(t *testing.T) {
	r := &seaRow{parts: []seaPart{{text: "測試"}}, bbox: image.Rect(0, 0, 10, 1), firstOld: map[int]byte{}, lastVal: map[int]byte{}}
	cur := make([]byte, 10)
	for i := range cur {
		r.firstOld[i], r.lastVal[i], cur[i] = 12, 68, 68
	}
	check := func(paint, retain, whole bool) {
		t.Helper()
		p, k, w := r.visibility(cur, true)
		if p != paint || k != retain || w != whole {
			t.Fatalf("可畫／保留／完整 = %v／%v／%v，預期 %v／%v／%v", p, k, w, paint, retain, whole)
		}
	}
	check(true, true, true)
	for i := 0; i < 8; i++ {
		cur[i] = 1
	}
	check(false, true, false) // 被遮住八成，保留來源但不繪製。
	for i := 0; i < 7; i++ {
		cur[i] = 68
	}
	check(false, true, false) // 九成相似仍不能恢復舊來源。
	cur[7] = 68
	check(true, true, true)
	r.firstOld[0] = 149
	check(false, false, false) // 無法證明印前底圖時丟棄，不能以保留來源繞過。
}

func TestWindowCoordinates(t *testing.T) {
	for _, v := range []struct {
		x, y, dx, dy int
		ok           bool
	}{{0, 0, 0, 0, true}, {1279, 799, 319, 199, true}, {512, 440, 128, 110, true}, {-1, 0, 0, 0, false}, {0, -1, 0, 0, false}, {1280, 1, 0, 0, false}, {1, 800, 0, 0, false}} {
		x, y, ok := logicalMouse(v.x, v.y)
		if x != v.dx || y != v.dy || ok != v.ok {
			t.Fatalf("%+v got %d,%d,%v", v, x, y, ok)
		}
	}
}
func TestWindowRelease(t *testing.T) {
	m := golem.New()
	d := golem.NewDOS(m, t.TempDir())
	defer d.Close()
	g := &windowGame{m: m, d: d, held: [3]bool{true, true, true}}
	for i := 0; i < 3; i++ {
		d.PressMouse(i)
	}
	g.release()
	g.release()
	if len(g.inputs) != 3 || g.held != [3]bool{} {
		t.Fatal("釋放不完整或重複")
	}
}
func TestWindowKeyboardQueue(t *testing.T) {
	m := golem.New()
	d := golem.NewDOS(m, t.TempDir())
	defer d.Close()
	for _, e := range []windowInput{{Kind: "text", Text: "x"}, {Kind: "text", Text: "A"},
		{Kind: "text", Text: "7"}, {Kind: "text", Text: " "}, {Kind: "backspace"}, {Kind: "enter"},
		{Kind: "escape"}, {Kind: "left"}, {Kind: "right"}, {Kind: "up"}, {Kind: "down"}} {
		applyWindowInput(d, e)
	}
	want := []uint16{0x2d78, 0x1e41, 0x0837, 0x3920, 0x0e08, 0x1c0d,
		0x011b, 0x4b00, 0x4d00, 0x4800, 0x5000}
	if d.KeysPending() != len(want) {
		t.Fatalf("佇列有 %d 鍵，要 %d", d.KeysPending(), len(want))
	}
	for i, word := range want {
		got, ok := m.PopKey()
		if !ok || got != word {
			t.Fatalf("第 %d 鍵為 %04x（存在=%v），要 %04x", i, got, ok, word)
		}
	}
	if d.KeysPending() != 0 {
		t.Fatal("讀完後 BIOS／DOS 鍵盤佇列仍有殘留")
	}
}
func TestWindowInputValidation(t *testing.T) {
	for _, e := range []windowInput{{Kind: "text", Text: "!"}, {Kind: "text", Text: "中"},
		{Kind: "text", Text: ""}, {Kind: "text", Text: "xy"}, {Kind: "unknown"},
		{Kind: "move", X: 320}, {Kind: "move", Button: 1},
		{Kind: "press", Button: 3}, {Kind: "release", X: 1},
		{Kind: "backspace", Text: "x"}, {Kind: "escape", Button: 1},
		{Kind: "left", X: 1}, {Kind: "up", Text: "x"}} {
		if validWindowInput(e) {
			t.Fatalf("非法事件被接受：%+v", e)
		}
	}
	var old windowReceipt
	if err := json.Unmarshal([]byte(`{"inputs":[{"step":12,"kind":"enter","x":0,"y":0,"button":0}],"end":20}`), &old); err != nil ||
		len(old.Inputs) != 1 || !validWindowInput(old.Inputs[0]) {
		t.Fatalf("舊 Enter 收據不再相容：%v，%+v", err, old)
	}
}

func TestSpecialWindowInputs(t *testing.T) {
	pressed := map[ebiten.Key]bool{ebiten.KeyEscape: true, ebiten.KeyArrowLeft: true,
		ebiten.KeySpace: true}
	none := func(ebiten.Key) bool { return false }
	events := specialWindowInputs(func(key ebiten.Key) bool { return pressed[key] }, none)
	if len(events) != 2 || events[0].Kind != "escape" || events[1].Kind != "left" {
		t.Fatalf("特殊鍵次序或空格雙送：%+v", events)
	}
	if got := specialWindowInputs(none, none); len(got) != 0 {
		t.Fatalf("沒有新按下邊緣卻送鍵：%+v", got)
	}
}

func TestBIOSKeyWords(t *testing.T) {
	m := golem.New()
	d := golem.NewDOS(m, t.TempDir())
	defer d.Close()
	cases := []struct {
		name string
		word uint16
	}{{"f1", 0x3b00}, {"f10", 0x4400}, {"shift-f1", 0x5400}, {"ctrl-f2", 0x5f00}, {"alt-f10", 0x7100},
		{"home", 0x4700}, {"pgdn", 0x5100}, {"tab", 0x0f09}, {"kp5", 0x4c00}, {"kp1", 0x4f00},
		{"alt-x", 0x2d00}, {"ctrl-a", 0x1e01}, {"ctrl-z", 0x2c1a}}
	for _, c := range cases {
		applyWindowInput(d, windowInput{Kind: "key", Text: c.name})
	}
	for _, c := range cases {
		got, ok := m.PopKey()
		if !ok || got != c.word {
			t.Fatalf("%s 鍵字為 %04x（存在=%v），要 %04x", c.name, got, ok, c.word)
		}
	}
	for _, bad := range []windowInput{{Kind: "key", Text: "f11"}, {Kind: "key", Text: ""}, {Kind: "key", Text: "kp1", X: 1}} {
		if validWindowInput(bad) {
			t.Fatalf("非法按鍵被接受：%+v", bad)
		}
	}
}

func TestModifierAndKeypadInputs(t *testing.T) {
	just := map[ebiten.Key]bool{ebiten.KeyF1: true, ebiten.KeyNumpad8: true, ebiten.KeyX: true}
	held := map[ebiten.Key]bool{ebiten.KeyShift: true}
	events := specialWindowInputs(func(k ebiten.Key) bool { return just[k] }, func(k ebiten.Key) bool { return held[k] })
	if len(events) != 2 || events[0].Text != "shift-f1" || events[1].Text != "kp8" {
		t.Fatalf("Shift+F1 或數字鍵盤轉送錯誤：%+v", events)
	}
	if got := filterWindowChars([]rune("8a"), events, func(k ebiten.Key) bool { return held[k] }); string(got) != "a" {
		t.Fatalf("數字鍵盤重複字元未去除：%q", string(got))
	}
	alt := map[ebiten.Key]bool{ebiten.KeyAlt: true}
	events = specialWindowInputs(func(k ebiten.Key) bool { return just[k] }, func(k ebiten.Key) bool { return alt[k] })
	if len(events) != 3 || events[0].Text != "alt-f1" || events[2].Text != "alt-x" {
		t.Fatalf("Alt 組合轉送錯誤：%+v", events)
	}
	if got := filterWindowChars([]rune("x"), events, func(k ebiten.Key) bool { return alt[k] }); len(got) != 0 {
		t.Fatalf("Alt 組合仍送出字元：%q", string(got))
	}
}

// 目標176：49,715 Hz 換算到 48,000 Hz；定值訊號換算後不變，不足時補靜音，積壓超過 0.25 秒只留 0.1 秒。
func TestAudioStreamResample(t *testing.T) {
	s := &audioStream{rate: 49715}
	in := make([]int16, 49715/10*2)
	for i := range in {
		in[i] = 1000
	}
	s.push(in)
	frames := len(s.out) / 4
	if frames < 4790 || frames > 4800 {
		t.Fatalf("0.1 秒應換出約 4,800 個取樣，得 %d", frames)
	}
	for i := 0; i < len(s.out); i += 2 {
		if v := int16(uint16(s.out[i]) | uint16(s.out[i+1])<<8); v != 1000 {
			t.Fatalf("定值訊號換算後應不變：%d", v)
		}
	}
	p := make([]byte, len(s.out)+8)
	for i := range p {
		p[i] = 0xff
	}
	if n, _ := s.Read(p); n != len(p) || p[len(p)-1] != 0 || s.ReadBytes != uint64(len(p)) {
		t.Fatal("不足時應補靜音並回報完整長度")
	}
	s.push(make([]int16, 49715/2*2)) // 0.5 秒
	if len(s.out) != audioPlayRate*4/10 || s.Dropped == 0 {
		t.Fatalf("積壓應截到 0.1 秒：%d 位元組、丟 %d", len(s.out), s.Dropped)
	}
}

func TestSeaPanelWholeLineRecovery(t *testing.T) {
	r := &seaRow{parts: []seaPart{{text: "測試"}}, firstOld: map[int]byte{}, lastVal: map[int]byte{}}
	cur := make([]byte, 10)
	for i := range cur {
		r.firstOld[i], r.lastVal[i], cur[i] = 12, 68, 68
	}
	check := func(paint, retain, whole bool) {
		t.Helper()
		p, k, w := r.visibility(cur, false)
		if p != paint || k != retain || w != whole {
			t.Fatalf("整行可畫／保留／完整 = %v／%v／%v", p, k, w)
		}
	}
	check(true, true, true)
	cur[0] = 1
	check(false, true, false) // 九成原字仍在：整行暫藏，不能保留中文碎字。
	cur[1] = 1
	check(false, true, false)
	cur[0] = 68
	check(false, true, false) // 部分恢復不能提前繪製。
	cur[1] = 68
	check(true, true, true)
	r.firstOld[0] = 149
	check(false, false, false) // 缺合格底圖時仍撤銷，不得用暫藏放寬來源證據。
}
