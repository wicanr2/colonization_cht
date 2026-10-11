package main

// 規格059：組句只供既有來源與欄位守門後使用，不加入通用字串模板。
import (
	"fmt"
	"strings"
	"unicode"
)

type displayPhrases map[string]string

var displayPhraseSlots = map[string][]string{
	"display-sea-gold":           {"w1", "n1", "w2", "n2"},
	"display-sea-location":       {"w1", "n1", "n2"},
	"display-sea-moves":          {"w1", "w2"},
	"display-sea-inbound":        {"w1", "w2", "w3", "w4"},
	"display-sea-date":           {"w1", "n1"},
	"display-sea-unit":           {"w1", "w2"},
	"display-sea-terrain":        {"w1"},
	"display-sea-goods":          {"n1", "w1"},
	"display-view-location":      {"w1", "n1", "n2", "n3"},
	"display-view-tribe-land":    {"w1"},
	"display-save-description":   {"w1", "person", "w2", "w3", "n1"},
	"display-port-ship-header":   {"w1", "w2", "w3"},
	"display-voyage-go-to":       {"w1"},
	"display-voyage-ship-header": {"w1", "w2", "w3", "w4"},
}

func displayPhraseShape(text string, slots []string) bool {
	if text == "" || strings.ContainsAny(text, "~#^") {
		return false
	}
	for _, r := range text {
		if unicode.IsControl(r) {
			return false
		}
	}
	seen := map[string]int{}
	for _, token := range stringSlot.FindAllString(text, -1) {
		seen[token[1:len(token)-1]]++
	}
	if len(seen) != len(slots) || strings.ContainsAny(stringSlot.ReplaceAllString(text, ""), "{}") {
		return false
	}
	for _, slot := range slots {
		if seen[slot] != 1 {
			return false
		}
	}
	return true
}

func loadDisplayPhrases(data []byte) (displayPhrases, error) {
	rows := tsvRows(data)
	if rows == nil {
		return nil, fmt.Errorf("顯示組句表欄位不符")
	}
	result := displayPhrases{}
	for _, row := range rows {
		id := row["template_id"]
		if !strings.HasPrefix(id, "display-") {
			continue
		}
		slots, ok := displayPhraseSlots[id]
		_, duplicate := result[id]
		if !ok || duplicate || !displayPhraseShape(row["pattern_en"], slots) || !displayPhraseShape(row["zh_hant"], slots) {
			return nil, fmt.Errorf("顯示組句不符：%s", id)
		}
		result[id] = row["zh_hant"]
	}
	// 舊版資料沒有組句列時，專屬入口回原文。新語言包須另驗完整14列。
	if len(result) != 0 && len(result) != len(displayPhraseSlots) {
		return nil, fmt.Errorf("顯示組句缺件：%d/%d", len(result), len(displayPhraseSlots))
	}
	return result, nil
}

func (p displayPhrases) format(id string, values map[string]string) (string, bool) {
	text, ok := p[id]
	slots := displayPhraseSlots[id]
	if !ok || len(values) != len(slots) {
		return "", false
	}
	for _, slot := range slots {
		value := values[slot]
		if value == "" || strings.ContainsAny(value, "{}%~#^") {
			return "", false
		}
		for _, r := range value {
			if unicode.IsControl(r) || strings.HasPrefix(slot, "n") && (r < '0' || r > '9') || slot == "person" && (r < 32 || r > 126) {
				return "", false
			}
		}
	}
	return stringSlot.ReplaceAllStringFunc(text, func(token string) string {
		return values[token[1:len(token)-1]]
	}), true
}

// 定稿術語仍由已綁定的術語表提供；缺件或同名歧義皆回原文。
func displayTerm(data []byte, en, category string) (string, bool) {
	result, count := "", 0
	for _, row := range tsvRows(data) {
		if row["en"] == en && row["category"] == category {
			result, count = row["zh"], count+1
		}
	}
	if count != 1 || result == "" || strings.ContainsAny(result, "{}%~#^") {
		return "", false
	}
	for _, r := range result {
		if unicode.IsControl(r) {
			return "", false
		}
	}
	return result, true
}
