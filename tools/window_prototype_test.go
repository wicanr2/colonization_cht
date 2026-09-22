package main

import (
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
