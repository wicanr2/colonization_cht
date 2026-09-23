package main

import (
	"encoding/json"
	golem "github.com/wicanr2/dosgolem"
	"testing"
)

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
		{Kind: "text", Text: "7"}, {Kind: "text", Text: " "}, {Kind: "backspace"}, {Kind: "enter"}} {
		applyWindowInput(d, e)
	}
	want := []uint16{0x2d78, 0x1e41, 0x0837, 0x3920, 0x0e08, 0x1c0d}
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
		{Kind: "backspace", Text: "x"}} {
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
