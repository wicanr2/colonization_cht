package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDisplayPreferencesStrictFormat(t *testing.T) {
	for _, input := range []string{
		"", "[]", "null", "{}", `{"language":"en"}`, `{"graphics":"hd"}`,
		`{"language":"en","graphics":"original","extra":1}`,
		`{"language":"en","language":"ja","graphics":"original"}`,
		`{"language":"en","graphics":"original","graphics":"hd"}`,
		`{"language":null,"graphics":"original"}`,
		`{"language":["en"],"graphics":"original"}`,
		`{"language":1,"graphics":"original"}`,
		`{"language":"en","graphics":"bad"}`,
		`{"language":"bad","graphics":"original"}`,
		`{"language":"en","graphics":"original"} {}`,
		"\xef\xbb\xbf" + `{"language":"en","graphics":"original"}`,
		"\xff", strings.Repeat(" ", 4097),
	} {
		t.Run(fmt.Sprintf("%x", []byte(input)[:min(len(input), 28)]), func(t *testing.T) {
			if _, err := decodeDisplayPreferences([]byte(input)); err == nil {
				t.Fatal("格式反例接受", input)
			}
		})
	}
	for _, language := range []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"} {
		for _, graphics := range []string{"original", "hd"} {
			input := fmt.Sprintf("{ \"graphics\":%q, \"language\":%q }\n", graphics, language)
			got, err := decodeDisplayPreferences([]byte(input))
			if err != nil || got != (displayOptions{language, graphics, 0}) {
				t.Fatal(got, err)
			}
		}
	}
}

func TestDisplayPreferencesFilesAndOverrides(t *testing.T) {
	path := filepath.Join(t.TempDir(), "config", "display.json")
	got, err := readDisplayPreferences(path, "", "")
	if err != nil || got != (displayOptions{"zh-Hant", "original", 0}) {
		t.Fatal(got, err)
	}
	if _, err = os.Stat(path); !os.IsNotExist(err) {
		t.Fatal("啟動讀取寫入了設定檔")
	}
	want := displayOptions{"ja", "hd", 0}
	if err = writeDisplayPreferences(path, want); err != nil {
		t.Fatal(err)
	}
	saved, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if got, err = readDisplayPreferences(path, "", ""); err != nil || got != want {
		t.Fatal(got, err)
	}
	got, err = readDisplayPreferences(path, "en", "")
	if err != nil || got != (displayOptions{"en", "hd", 0}) {
		t.Fatal(got, err)
	}
	got, err = readDisplayPreferences(path, "", "original")
	if err != nil || got != (displayOptions{"ja", "original", 0}) {
		t.Fatal(got, err)
	}
	if _, err = readDisplayPreferences(path, "invalid", ""); err == nil {
		t.Fatal("無效明確參數接受")
	}
	if after, _ := os.ReadFile(path); !bytes.Equal(saved, after) {
		t.Fatal("讀取或參數覆蓋寫回設定")
	}
	if info, err := os.Stat(path); err != nil || info.Mode().Perm() != 0600 {
		t.Fatal("設定檔權限錯誤", err)
	}
	if err = os.WriteFile(path, []byte("damaged"), 0600); err != nil {
		t.Fatal(err)
	}
	if _, err = readDisplayPreferences(path, "en", "original"); err == nil {
		t.Fatal("明確參數掩蓋損毀保存檔")
	}
	if extras, err := filepath.Glob(filepath.Join(filepath.Dir(path), ".display-*.tmp")); err != nil || len(extras) != 0 {
		t.Fatal("留下暫存設定檔", extras, err)
	}
}

func TestDisplayPreferencesAtomicActivation(t *testing.T) {
	root := t.TempDir()
	path := filepath.Join(root, "display.json")
	old := displayOptions{"zh-Hant", "original", 0}
	target := displayOptions{"en", "original", 0}
	if err := writeDisplayPreferences(path, old); err != nil {
		t.Fatal(err)
	}
	before, _ := os.ReadFile(path)
	active, commits := old, 0
	prepare := func(o displayOptions) (func(), error) { return func() { active = o; commits++ }, nil }
	for _, kind := range []string{"unavailable", "nil-commit", "bad-settings", "write-error"} {
		t.Run(kind, func(t *testing.T) {
			p := path
			o := target
			preflight := prepare
			switch kind {
			case "unavailable":
				preflight = func(displayOptions) (func(), error) { return nil, fmt.Errorf("ui.error.unavailable") }
			case "nil-commit":
				preflight = func(displayOptions) (func(), error) { return nil, nil }
			case "bad-settings":
				o.Language = "invalid"
			case "write-error":
				p = filepath.Join(path, "display.json")
			}
			if err := applyDisplayPreferences(p, o, preflight); err == nil {
				t.Fatal("失敗交易接受", kind)
			}
			after, _ := os.ReadFile(path)
			if active != old || commits != 0 || !bytes.Equal(before, after) {
				t.Fatal("失敗交易改變生效設定或保存檔")
			}
		})
	}
	if err := applyDisplayPreferences(path, target, prepare); err != nil {
		t.Fatal(err)
	}
	saved, err := readDisplayPreferences(path, "", "")
	if err != nil || active != target || saved != target || commits != 1 {
		t.Fatal(active, saved, commits, err)
	}
}

func TestCPUSpeedPreferencesCompatibilityAndFailures(t *testing.T) {
	old, err := decodeDisplayPreferences([]byte(`{"language":"zh-Hant","graphics":"hd"}`))
	if err != nil || old.speed() != 1 {
		t.Fatal(old, err)
	}
	for _, speed := range displaySpeeds {
		input := fmt.Sprintf(`{"language":"ja","graphics":"hd","speed":%d}`, speed)
		got, err := decodeDisplayPreferences([]byte(input))
		if err != nil || got.speed() != speed {
			t.Fatal(got, err)
		}
		path := filepath.Join(t.TempDir(), "display.json")
		if err := writeDisplayPreferences(path, got); err != nil {
			t.Fatal(err)
		}
		loaded, err := readDisplayPreferences(path, "", "", 32)
		if err != nil || loaded.Language != "ja" || loaded.Graphics != "hd" || loaded.Speed != 32 {
			t.Fatal(loaded, err)
		}
	}
	for _, bad := range []string{`0`, `-1`, `3`, `64`, `1.0`, `"2"`, `null`, `true`, `[]`} {
		input := `{"language":"en","graphics":"original","speed":` + bad + `}`
		if _, err := decodeDisplayPreferences([]byte(input)); err == nil {
			t.Fatal("非法CPU速度被接受", input)
		}
	}
	if _, err := decodeDisplayPreferences([]byte(`{"language":"en","graphics":"hd","speed":2,"speed":4}`)); err == nil {
		t.Fatal("重複CPU速度被接受")
	}
	path := filepath.Join(t.TempDir(), "display.json")
	before := displayOptions{Language: "zh-Hant", Graphics: "hd", Speed: 2}
	if err := writeDisplayPreferences(path, before); err != nil {
		t.Fatal(err)
	}
	want := before
	want.Speed = 32
	active := before
	err = applyDisplayPreferences(filepath.Join(path, "unwritable"), want, func(o displayOptions) (func(), error) { return func() { active = o }, nil })
	if err == nil || active != before {
		t.Fatal("速度保存失敗仍提交", active, err)
	}
	loaded, err := readDisplayPreferences(path, "", "", -1)
	if err == nil {
		t.Fatal("非法覆蓋接受", loaded)
	}
}
