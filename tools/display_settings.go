// 規格050：畫面外設定狀態；語言包與HD驗證由顯示後端提供。
package main

import "fmt"

type displayOptions struct {
	Language string `json:"language"`
	Graphics string `json:"graphics"`
}

func (o displayOptions) validate() error {
	switch o.Language {
	case "zh-Hant", "zh-Hans", "ja", "ko", "en":
	default:
		return fmt.Errorf("不支援的顯示語言：%q", o.Language)
	}
	switch o.Graphics {
	case "original", "hd":
	default:
		return fmt.Errorf("不支援的圖像模式：%q", o.Graphics)
	}
	return nil
}

type displayPhase uint8

const (
	displayPlaying displayPhase = iota
	displayOpening
	displayEditing
	displayResuming
)

type displaySettings struct {
	phase   displayPhase
	current displayOptions
	draft   displayOptions
	problem string
}

// 原版仍按住滑鼠時不接受設定，避免中斷拖曳。
// 成功後立刻暫停；呼叫者須停止DOS輸入、主機器指令與音訊讀取。
func (s *displaySettings) open(originalMouseHeld bool) bool {
	if s.phase != displayPlaying || originalMouseHeld {
		return false
	}
	s.draft, s.problem = s.current, ""
	s.phase = displayOpening
	return true
}

func (s *displaySettings) paused() bool { return s.phase != displayPlaying }

// allReleased必須涵蓋所有實體鍵與滑鼠按鈕，不能只檢查原版已支援的鍵。
func (s *displaySettings) released(allReleased bool) {
	if !allReleased {
		return
	}
	switch s.phase {
	case displayOpening:
		s.phase = displayEditing
	case displayResuming:
		s.phase = displayPlaying
	}
}

func (s *displaySettings) cancel() {
	if s.phase == displayEditing {
		s.draft, s.problem = s.current, ""
		s.phase = displayResuming
	}
}

// activate須先完整驗證目標資料，再整包交換。失敗時不得改目前的顯示後端。
func (s *displaySettings) apply(activate func(displayOptions) error) bool {
	if s.phase != displayEditing {
		return false
	}
	err := s.draft.validate()
	if err == nil {
		if activate == nil {
			err = fmt.Errorf("顯示設定無法載入")
		} else {
			err = activate(s.draft)
		}
	}
	if err != nil {
		s.problem = err.Error()
		return false
	}
	s.current, s.problem = s.draft, ""
	s.phase = displayResuming
	return true
}
