package main

import (
	"encoding/binary"
	"os"
	"testing"
)

func musicForTest(t *testing.T) *nativeMusic {
	t.Helper()
	root := os.Getenv("COLONIZATION_MUSIC_ROOT")
	if root == "" {
		t.Skip("需唯讀原版COLONIZE目錄")
	}
	p, err := newNativeMusic(root)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { p.d.Close() })
	return p
}

func TestNativeMusicControlsAndEffects(t *testing.T) {
	p := musicForTest(t)
	cmd := func(c, v uint16) uint16 {
		t.Helper()
		r, e := p.command(c, v)
		if e != nil {
			t.Fatal(e)
		}
		return r
	}
	render := func() []int16 {
		t.Helper()
		s, e := p.render(uint64(p.m.AudioRate()) / 10)
		if e != nil {
			t.Fatal(e)
		}
		return s
	}
	cmd(0x34, 2)
	if cmd(8, 0) == 0 {
		t.Fatal("原版曲譜未開始")
	}
	for _, c := range []uint16{6, 7, 2, 3, 4, 5, 1, 0} {
		cmd(c, 0)
		render()
	}
	if cmd(8, 0) != 0 {
		t.Fatal("原版停止命令未清除聲音")
	}
	for c := uint16(0x20); c <= 0x5d; c++ {
		cmd(c, 0)
		render()
		cmd(0, 0)
	}
	for c := uint16(0x8020); c <= 0x8026; c++ {
		cmd(c, 0)
		render()
		cmd(0, 0)
	}
}

func TestMusicPlaybackLargeReadAndQueryIsolation(t *testing.T) {
	n := musicForTest(t)
	p := &musicPlayback{native: n, stream: &audioStream{rate: uint64(n.m.AudioRate())}, digital: &audioStream{rate: uint64(n.m.AudioRate())}, fallback: &audioStream{rate: uint64(n.m.AudioRate())}}
	p.enqueue(musicCommand{Command: 0x34, Parameter: 2})
	for i := 0; i < 60000; i++ {
		p.enqueue(musicCommand{Command: 8, Parameter: uint16(i)})
	}
	buf := make([]byte, audioPlayRate*4*2)
	if count, e := p.Read(buf); e != nil || count != len(buf) {
		t.Fatal(count, e)
	}
	st := p.status()
	if st["music_underrun_bytes"].(uint64) != 0 || st["music_dropped_bytes"].(uint64) != 0 || p.commands != 1 || p.queries.Load() != 60000 {
		t.Fatal(st)
	}
	nonzero := false
	for i := 0; i < len(buf); i += 2 {
		nonzero = nonzero || binary.LittleEndian.Uint16(buf[i:]) != 0
	}
	if !nonzero {
		t.Fatal("音樂全部靜音")
	}
	for i := 0; i < 6500; i++ {
		if i == 250 {
			p.enqueue(musicCommand{Command: 1})
		}
		if i == 300 {
			p.enqueue(musicCommand{Command: 0x33})
		}
		p.Read(make([]byte, 1920))
	}
	if st := p.status(); st["music_underrun_bytes"].(uint64) != 0 || st["music_dropped_bytes"].(uint64) != 0 {
		t.Fatal(st)
	}
	p.enqueue(musicCommand{Command: 0xffff})
	p.Read(make([]byte, 1920))
	if p.err == "" {
		t.Fatal("未知命令未記錄回退")
	}
}

func TestMusicQueueBound(t *testing.T) {
	p := &musicPlayback{}
	for i := 0; i < 1025; i++ {
		p.enqueue(musicCommand{Command: 0x20})
	}
	if len(p.queue) != 1024 || p.queueError == "" {
		t.Fatal("命令佇列未設上限")
	}
}
