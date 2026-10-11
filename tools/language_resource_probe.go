package main

// 規格060 DRAFT：僅由隔離組裝器連結。正式載入後匯出逐欄證據，不執行DOS。
import (
	"flag"
	"fmt"
	"image"
	"path/filepath"
	"strings"
)

var resourceExportPath = flag.String("draft-resource-export", "", "規格060隔離原型：固定顯示欄位盤點")

type displayResourceEvidence struct {
	ID          string          `json:"id"`
	Group       string          `json:"group"`
	File        string          `json:"file"`
	Text        string          `json:"text"`
	Safe        image.Rectangle `json:"safe"`
	NativeInk   image.Rectangle `json:"native_ink"`
	Position    image.Point     `json:"position"`
	Shadow      int             `json:"shadow_offset"`
	FontSize    int             `json:"cubic_font_size"`
	MaskSize    image.Point     `json:"cubic_mask_size"`
	Reason      string          `json:"reason"`
	SourceValid bool            `json:"source_valid"`
}

func resourceFile(group, id string) string {
	return filepath.Join(group, strings.ReplaceAll(id, ":", "-")+".json")
}

func resourceMaskSize(mask *image.Alpha) image.Point {
	if mask == nil {
		return image.Point{}
	}
	return mask.Bounds().Size()
}

func exportDisplayResources(path string, lines []*menuLine, difficulty []*difficultyLine,
	captions []*buildCaption, title *optionsTitle, rows *optionRows, retire []*retireEvent,
	intro *introState, help *helpState, statics []*staticItem) {
	var result []displayResourceEvidence
	for _, l := range lines {
		result = append(result, displayResourceEvidence{ID: l.id, Group: "menu", File: resourceFile("menu", l.id), Text: l.translation,
			Safe: l.safe(), NativeInk: image.Rect(86, l.y, l.maxX+1, l.maxY+1), Position: image.Pt(344, l.y*4),
			MaskSize: resourceMaskSize(l.ink), Reason: l.fontReason, SourceValid: l.catalogValid && l.matches == 1})
	}
	for _, l := range difficulty {
		group, shadow := "menu", 0
		if l.nationCard {
			group, shadow = "card", 4
		}
		if l.thirdCard {
			group, shadow = "third-card", 4
		}
		if l.restCard {
			group = "cards-rest"
		}
		if l.prompt {
			shadow = 4
		}
		result = append(result, displayResourceEvidence{ID: l.id, Group: group, File: resourceFile(group, l.id), Text: l.translation,
			Safe: l.safe, NativeInk: l.bbox, Position: l.position, Shadow: shadow, FontSize: l.fontSize,
			MaskSize: resourceMaskSize(l.ink), Reason: l.fontReason, SourceValid: l.valid && l.matches == 1})
	}
	for _, c := range captions {
		group, file := "captions", resourceFile("captions", c.id)
		if c.id == "GAME.TXT:0x000153CC" {
			group, file = "build1", "build1.json"
		}
		result = append(result, displayResourceEvidence{ID: c.id, Group: group, File: file, Text: c.translation,
			Safe: c.safe, NativeInk: c.inkBBox, Position: c.fgPos, Shadow: 4, FontSize: 38,
			MaskSize: resourceMaskSize(c.ink), Reason: c.fontReason, SourceValid: c.displayOK})
	}
	if title != nil {
		result = append(result, displayResourceEvidence{ID: title.id, Group: "options-title", File: "options-title.json", Text: title.translation,
			Safe: image.Rect(65, 44, 253, 59), NativeInk: image.Rect(67, 47, 147, 56), Position: image.Pt(268, 188),
			Shadow: 4, FontSize: 34, MaskSize: resourceMaskSize(title.ink), Reason: title.fontReason, SourceValid: title.valid && title.matches == 1})
	}
	if rows != nil {
		for i, r := range rows.rows {
			result = append(result, displayResourceEvidence{ID: r.id, Group: "option-rows", File: resourceFile("option-rows", r.id), Text: r.translation,
				Safe: optionRowSafe(i), Position: image.Pt(328, 244+48*i), Shadow: 4, FontSize: optionRowSizes[i],
				MaskSize: resourceMaskSize(r.ink), Reason: r.fontReason, SourceValid: r.valid && r.matches == 1})
		}
	}
	for _, ev := range retire {
		for _, r := range ev.fields {
			result = append(result, displayResourceEvidence{ID: r.id, Group: "retire", File: resourceFile("retire", r.id), Text: r.translation,
				Safe: r.rect, NativeInk: r.bbox, Position: r.position, Shadow: 4, FontSize: 34,
				MaskSize: resourceMaskSize(r.ink), Reason: r.fontReason, SourceValid: r.valid && r.matches == 1})
		}
	}
	if intro != nil {
		for _, r := range intro.pages {
			result = append(result, displayResourceEvidence{ID: r.id, Group: "intro", File: resourceFile("intro", r.id), Text: r.translation,
				Safe: introPanel, NativeInk: r.bbox, Position: introPanel.Min.Mul(4), Shadow: 4,
				MaskSize: resourceMaskSize(r.normal), Reason: r.fontReason, SourceValid: r.valid && r.matches == 1})
		}
	}
	if help != nil {
		result = append(result, displayResourceEvidence{ID: help.id, Group: "help", File: resourceFile("help", help.id), Text: help.translation,
			Safe: helpText, NativeInk: image.Rect(69, 106, 250, 165), Position: helpText.Min.Mul(4), Shadow: 4,
			FontSize: 30, MaskSize: resourceMaskSize(help.normal), Reason: help.fontReason, SourceValid: help.valid && help.matches == 1})
	}
	for _, r := range statics {
		result = append(result, displayResourceEvidence{ID: r.id, Group: "static", File: resourceFile("static", r.id), Text: r.zh,
			Safe: r.band, Position: r.pos, MaskSize: resourceMaskSize(r.mask), Reason: r.reason, SourceValid: r.mask != nil})
	}
	seen := map[string]bool{}
	for _, r := range result {
		if seen[r.File] || !r.SourceValid || r.Reason != "" || r.MaskSize.X <= 0 || r.MaskSize.Y <= 0 {
			panic(fmt.Sprintf("固定欄位基準不完整：%s / %s / %s", r.Group, r.ID, r.Reason))
		}
		seen[r.File] = true
	}
	if len(result) != 64 {
		panic(fmt.Sprintf("固定欄位缺件：%d/64", len(result)))
	}
	dumpJSON(path, map[string]any{"kind": "DRAFT-fixed-field-source-evidence-not-language-bundle", "fields": result,
		"limitations": []string{"Cubic layout is a comparison only; Noto sizes must be measured from each original field.", "No original DOS execution or normal GUI credit."}})
}
