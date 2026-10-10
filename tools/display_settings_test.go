package main

import (
	"bytes"
	"errors"
	"testing"
)

func TestDisplaySettingsRequiresReleaseAndPreservesDrag(t *testing.T) {
	s := displaySettings{current: displayOptions{"zh-Hant", "original"}}
	if s.open(true) || s.paused() {
		t.Fatal("拖曳時開啟設定或停止原版")
	}
	if !s.open(false) || !s.paused() {
		t.Fatal("設定未立刻暫停")
	}
	s.released(false)
	if s.phase != displayOpening || s.apply(func(displayOptions) error {
		t.Fatal("開啟按鍵未放開就套用")
		return nil
	}) {
		t.Fatal("開啟按鍵穿透到設定")
	}
	s.released(true)
	s.draft = displayOptions{"ko", "hd"}
	s.cancel()
	if s.current != (displayOptions{"zh-Hant", "original"}) || !s.paused() {
		t.Fatal("取消更動生效設定或提早恢復")
	}
	s.released(false)
	if !s.paused() {
		t.Fatal("取消按鍵仍按住時恢復")
	}
	s.released(true)
	if s.paused() {
		t.Fatal("全部放開後沒有恢復")
	}
	if !s.open(false) || s.draft != s.current {
		t.Fatal("重開設定帶入已取消草稿")
	}
}

func TestDisplayPausePreservesAudioStream(t *testing.T) {
	samples := make([]int16, 2000)
	for i := range samples {
		samples[i] = int16(i*7 - 6000)
	}
	s, control := &audioStream{rate: audioPlayRate}, &audioStream{rate: audioPlayRate}
	s.push(samples)
	control.push(samples)
	first, want := make([]byte, 64), make([]byte, 64)
	s.Read(first)
	control.Read(want)
	if !bytes.Equal(first, want) {
		t.Fatal("初始音訊不同")
	}
	a := &frontendAudio{stream: s}
	a.setPaused(true)
	before := append([]byte(nil), s.out...)
	read, underrun, dropped := s.ReadBytes, s.UnderrunBytes, s.Dropped
	for _, size := range []int{1, 256, 8192} {
		b := bytes.Repeat([]byte{0xff}, size)
		if n, err := s.Read(b); n != size || err != nil || !bytes.Equal(b, make([]byte, size)) {
			t.Fatal("暫停沒有回傳等長靜音")
		}
	}
	if !bytes.Equal(before, s.out) || s.ReadBytes != read || s.UnderrunBytes != underrun || s.Dropped != dropped {
		t.Fatal("暫停消耗音訊或更動播放計數")
	}
	a.setPaused(false)
	next, nextControl := make([]byte, len(before)), make([]byte, len(before))
	s.Read(next)
	control.Read(nextControl)
	if !bytes.Equal(next, nextControl) {
		t.Fatal("恢復跳過、重複或改變音訊")
	}
}

func TestDisplayPausePreservesNativeMusicAndCommands(t *testing.T) {
	n, controlNative := musicForTest(t), musicForTest(t)
	makePlayback := func(native *nativeMusic) *musicPlayback {
		return &musicPlayback{native: native, stream: &audioStream{rate: uint64(native.m.AudioRate())},
			digital: &audioStream{rate: uint64(native.m.AudioRate())}, fallback: &audioStream{rate: uint64(native.m.AudioRate())}}
	}
	p, control := makePlayback(n), makePlayback(controlNative)
	p.enqueue(musicCommand{Command: 0x34, Parameter: 2})
	control.enqueue(musicCommand{Command: 0x34, Parameter: 2})
	a := &frontendAudio{stream: p.fallback, music: p}
	a.setPaused(true)
	steps, memory := n.m.Steps, append([]byte(nil), n.m.Mem...)
	for i := 0; i < 5; i++ {
		b := bytes.Repeat([]byte{0xff}, 1920)
		if count, err := p.Read(b); count != len(b) || err != nil || !bytes.Equal(b, make([]byte, len(b))) {
			t.Fatal("獨立音樂暫停沒有回傳靜音")
		}
	}
	if n.m.Steps != steps || !bytes.Equal(memory, n.m.Mem) || p.commands != 0 || len(p.queue) != 1 || p.stream.ReadBytes != 0 {
		t.Fatal("設定期間音樂繼續推進或消耗命令")
	}
	a.setPaused(false)
	got, want := make([]byte, 19200), make([]byte, 19200)
	if _, err := p.Read(got); err != nil {
		t.Fatal(err)
	}
	if _, err := control.Read(want); err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got, want) || n.m.Steps != controlNative.m.Steps || !bytes.Equal(n.m.Mem, controlNative.m.Mem) || p.commands != 1 {
		t.Fatal("音樂恢復後與無暫停對照不同")
	}
}

func TestDisplaySettingsFailedActivationKeepsCurrentAndDraft(t *testing.T) {
	s := displaySettings{current: displayOptions{"zh-Hant", "original"}}
	s.open(false)
	s.released(true)
	s.draft = displayOptions{"ja", "hd"}
	calls := 0
	activate := func(o displayOptions) error {
		calls++
		if o != s.draft {
			t.Fatal("未驗證完整草稿")
		}
		return errors.New("圖像包校驗失敗")
	}
	if s.apply(activate) || calls != 1 || s.current != (displayOptions{"zh-Hant", "original"}) ||
		s.draft != (displayOptions{"ja", "hd"}) || s.problem != "圖像包校驗失敗" || s.phase != displayEditing {
		t.Fatal("載入失敗沒有保留設定與面板")
	}
	if !s.apply(func(displayOptions) error { return nil }) || s.current != s.draft || !s.paused() || s.problem != "" {
		t.Fatal("重試成功未整包更新或未等待放開")
	}
	s.released(false)
	if !s.paused() {
		t.Fatal("套用點擊穿透")
	}
	s.released(true)
	if s.paused() {
		t.Fatal("成功套用後無法恢復")
	}
}

func TestDisplaySettingsRejectsInvalidOptionsBeforeBackend(t *testing.T) {
	for _, bad := range []displayOptions{{"xx", "original"}, {"en", "filter"}, {"", "hd"}} {
		s := displaySettings{current: displayOptions{"en", "original"}}
		s.open(false)
		s.released(true)
		s.draft = bad
		if s.apply(func(displayOptions) error {
			t.Fatal("無效選項進入顯示後端")
			return nil
		}) || s.problem == "" || s.current != (displayOptions{"en", "original"}) {
			t.Fatal("無效選項改變設定")
		}
	}
	for _, lang := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		for _, mode := range []string{"original", "hd"} {
			if err := (displayOptions{lang, mode}).validate(); err != nil {
				t.Fatal("語言與圖像模式不獨立：", err)
			}
		}
	}
}
