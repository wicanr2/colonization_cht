package main

import (
	"testing"

	golem "github.com/wicanr2/dosgolem"
)

// Synthetic EMS contract probe, independent of game bytes or game state.
// Source: DOSBox-X src/ints/ems.cpp, EMM_MapPage. Aliases share backing pages.
// Copy this file to a temporary Go module that imports the isolated dosgolem.
func TestGoal185EMSAliasContract(t *testing.T) {
	m := golem.New()
	if err := m.LoadCOM([]byte{0xcd, 0xf6, 0xf4}); err != nil {
		t.Fatal(err)
	}
	d := golem.NewDOS(m, t.TempDir())
	d.Install()
	call := func(ax, bx, dx uint16) uint16 {
		m.CPU.Seg[golem.CS], m.CPU.IP = golem.PSPSeg, 0x100
		m.CPU.R[golem.AX], m.CPU.R[golem.BX], m.CPU.R[golem.DX] = ax, bx, dx
		if err := m.Step(); err != nil {
			t.Fatal(err)
		}
		if m.CPU.R[golem.AX]>>8 != 0 {
			t.Fatalf("EMS call %04X returned %04X", ax, m.CPU.R[golem.AX])
		}
		return m.CPU.R[golem.DX]
	}
	h := call(0x4300, 2, 0)
	call(0x4400, 0, h)
	m.Write8(0xd0123, 0x11)
	call(0x4401, 0, h)
	if got := m.Read8(0xd4123); got != 0x11 {
		t.Errorf("mapping a second alias lost the live byte: got %02X, want 11", got)
	}
	m.Write8(0xd4123, 0x22)
	if got := m.Read8(0xd0123); got != 0x22 {
		t.Errorf("write through alias 1 is invisible through alias 0: got %02X, want 22", got)
	}
	call(0x4400, 1, h)
	call(0x4400, 0, h)
	if got := m.Read8(0xd0123); got != 0x22 {
		t.Errorf("remapping overwrote the newer alias byte: got %02X, want 22", got)
	}
}
