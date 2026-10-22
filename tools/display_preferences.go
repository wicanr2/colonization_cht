package main

// 規格056：只保存前端顯示與速度選項，不接觸原版資料或存檔。
import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"unicode/utf8"
)

func displayPreferencePath(explicit string) (string, error) {
	if explicit != "" {
		return filepath.Abs(explicit)
	}
	dir, err := os.UserConfigDir()
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, "colonization-cht", "display.json"), nil
}

func decodeDisplayPreferences(data []byte) (displayOptions, error) {
	var options displayOptions
	if len(data) > 4096 || !utf8.Valid(data) {
		return options, fmt.Errorf("invalid display settings encoding or length")
	}
	d := json.NewDecoder(bytes.NewReader(data))
	token, err := d.Token()
	if err != nil || token != json.Delim('{') {
		return options, fmt.Errorf("display settings must be an object")
	}
	seen := map[string]bool{}
	for d.More() {
		token, err := d.Token()
		if err != nil {
			return options, err
		}
		key, ok := token.(string)
		if !ok || seen[key] || (key != "language" && key != "graphics" && key != "speed") {
			return options, fmt.Errorf("invalid or repeated display setting: %v", token)
		}
		seen[key] = true
		if key == "speed" {
			var speed int
			if err := d.Decode(&speed); err != nil || speed <= 0 {
				return options, fmt.Errorf("invalid CPU speed")
			}
			options.Speed = speed
			continue
		}
		token, err = d.Token()
		value, ok := token.(string)
		if err != nil || !ok {
			return options, fmt.Errorf("display setting must be a string: %s", key)
		}
		if key == "language" {
			options.Language = value
		} else {
			options.Graphics = value
		}
	}
	token, err = d.Token()
	if err != nil || token != json.Delim('}') || !seen["language"] || !seen["graphics"] {
		return options, fmt.Errorf("incomplete display settings")
	}
	if _, err = d.Token(); err != io.EOF {
		return options, fmt.Errorf("trailing display settings data")
	}
	return options, options.validate()
}

func readDisplayPreferences(path, language, graphics string, speed ...int) (displayOptions, error) {
	options := displayOptions{Language: "zh-Hant", Graphics: "original"}
	file, err := os.Open(path)
	if err == nil {
		defer file.Close()
		data, readErr := io.ReadAll(io.LimitReader(file, 4097))
		if readErr != nil {
			return options, readErr
		}
		options, err = decodeDisplayPreferences(data)
	}
	if err != nil && !os.IsNotExist(err) {
		return options, err
	}
	if language != "" {
		options.Language = language
	}
	if graphics != "" {
		options.Graphics = graphics
	}
	if len(speed) > 1 || len(speed) == 1 && speed[0] < 0 {
		return options, fmt.Errorf("invalid CPU speed override")
	}
	if len(speed) == 1 && speed[0] != 0 {
		options.Speed = speed[0]
	}
	return options, options.validate()
}

func writeDisplayPreferences(path string, options displayOptions) error {
	if err := options.validate(); err != nil {
		return err
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return err
	}
	file, err := os.CreateTemp(dir, ".display-*.tmp")
	if err != nil {
		return err
	}
	name := file.Name()
	defer os.Remove(name)
	data, err := json.Marshal(options)
	if err == nil {
		_, err = file.Write(append(data, '\n'))
	}
	if err == nil {
		err = file.Sync()
	}
	closeErr := file.Close()
	if err != nil {
		return err
	}
	if closeErr != nil {
		return closeErr
	}
	return os.Rename(name, path)
}

// prepare只讀取、驗證並準備資料；commit不再做I/O或其他可能失敗的工作。
func applyDisplayPreferences(path string, options displayOptions, prepare func(displayOptions) (func(), error)) error {
	if err := options.validate(); err != nil {
		return err
	}
	if prepare == nil {
		return fmt.Errorf("ui.error.unavailable")
	}
	commit, err := prepare(options)
	if err != nil {
		return err
	}
	if commit == nil {
		return fmt.Errorf("ui.error.unavailable")
	}
	if err := writeDisplayPreferences(path, options); err != nil {
		return fmt.Errorf("ui.error.save")
	}
	commit()
	return nil
}
