// 規格060 DRAFT。由tools/build_language_resource_index.py產生；不要手動修改。
// 僅保留來源鍵、檔名、幾何與指紋；譯文仍以TSV為準。
package main

import (
	_ "embed"
	"encoding/json"
	"fmt"
)

//go:embed language-catalogs.json
var draftCatalogRegistry []byte

func draftIndexedRequirements() (draftBundleRequirements, error) {
	needs := draftBundleRequirements{
		Font:    "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a",
		License: "6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2",
		Fields:  "2be579643f7655f635a6bec4adcbae9a1fb11a4734d3b8daf80177934e15b61d",
		Masks: map[string]draftMaskRequirement{
			"menu/GAME.TXT-0x000001B0.json":             {ID: "GAME.TXT:0x000001B0", Safe: [4]int{344, 428, 928, 456}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/GAME.TXT-0x000001CB.json":             {ID: "GAME.TXT:0x000001CB", Safe: [4]int{344, 460, 928, 488}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/GAME.TXT-0x000001E4.json":             {ID: "GAME.TXT:0x000001E4", Safe: [4]int{344, 492, 928, 520}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/GAME.TXT-0x000001F9.json":             {ID: "GAME.TXT:0x000001F9", Safe: [4]int{344, 524, 928, 552}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/GAME.TXT-0x00000204.json":             {ID: "GAME.TXT:0x00000204", Safe: [4]int{344, 556, 928, 584}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/LABELS.TXT-0x00000888.json":           {ID: "LABELS.TXT:0x00000888", Safe: [4]int{156, 56, 304, 104}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/LABELS.TXT-0x00000890.json":           {ID: "LABELS.TXT:0x00000890", Safe: [4]int{80, 108, 384, 160}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/LABELS.TXT-0x0000086E.json":           {ID: "LABELS.TXT:0x0000086E", Safe: [4]int{40, 316, 420, 352}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/NAMES.TXT-0x00000C0C.json":            {ID: "NAMES.TXT:0x00000C0C", Safe: [4]int{552, 176, 744, 204}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/LABELS.TXT-0x000008A9.json":           {ID: "LABELS.TXT:0x000008A9", Safe: [4]int{584, 208, 720, 240}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/NAMES.TXT-0x00000C18.json":            {ID: "NAMES.TXT:0x00000C18", Safe: [4]int{988, 176, 1148, 204}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/LABELS.TXT-0x000008B2.json":           {ID: "LABELS.TXT:0x000008B2", Safe: [4]int{1024, 208, 1116, 240}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"third-card/NAMES.TXT-0x00000C22.json":      {ID: "NAMES.TXT:0x00000C22", Safe: [4]int{116, 556, 336, 592}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"third-card/LABELS.TXT-0x000008B8.json":     {ID: "LABELS.TXT:0x000008B8", Safe: [4]int{152, 592, 304, 628}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/LABELS.TXT-0x000008D3.json":           {ID: "LABELS.TXT:0x000008D3", Safe: [4]int{156, 140, 292, 184}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"menu/LABELS.TXT-0x000008DB.json":           {ID: "LABELS.TXT:0x000008DB", Safe: [4]int{68, 192, 380, 236}, Shadow: 0, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"card/NAMES.TXT-0x000008EA.json":            {ID: "NAMES.TXT:0x000008EA", Safe: [4]int{500, 48, 760, 96}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"card/LABELS.TXT-0x000008F2.json":           {ID: "LABELS.TXT:0x000008F2", Safe: [4]int{500, 332, 760, 384}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"cards-rest/NAMES.TXT-0x00000906.json":      {ID: "NAMES.TXT:0x00000906", Safe: [4]int{900, 48, 1160, 96}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"cards-rest/LABELS.TXT-0x000008FF.json":     {ID: "LABELS.TXT:0x000008FF", Safe: [4]int{900, 332, 1160, 384}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"cards-rest/NAMES.TXT-0x00000921.json":      {ID: "NAMES.TXT:0x00000921", Safe: [4]int{500, 412, 760, 460}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"cards-rest/LABELS.TXT-0x0000090C.json":     {ID: "LABELS.TXT:0x0000090C", Safe: [4]int{500, 696, 760, 748}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"cards-rest/NAMES.TXT-0x0000093D.json":      {ID: "NAMES.TXT:0x0000093D", Safe: [4]int{900, 412, 1160, 460}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"cards-rest/LABELS.TXT-0x00000916.json":     {ID: "LABELS.TXT:0x00000916", Safe: [4]int{900, 696, 1160, 748}, Shadow: 4, Layered: false, Catalog: "nation-card-fragments.zh-Hant.tsv"},
			"menu/GAME.TXT-0x00000A7A.json":             {ID: "GAME.TXT:0x00000A7A", Safe: [4]int{400, 340, 876, 392}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"build1.json":                               {ID: "GAME.TXT:0x000153CC", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x0001542B.json":         {ID: "GAME.TXT:0x0001542B", Safe: [4]int{48, 108, 1228, 208}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x00015482.json":         {ID: "GAME.TXT:0x00015482", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x000154CB.json":         {ID: "GAME.TXT:0x000154CB", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x00015522.json":         {ID: "GAME.TXT:0x00015522", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x0001555D.json":         {ID: "GAME.TXT:0x0001555D", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x00015597.json":         {ID: "GAME.TXT:0x00015597", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x000155F5.json":         {ID: "GAME.TXT:0x000155F5", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x0001563F.json":         {ID: "GAME.TXT:0x0001563F", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"captions/GAME.TXT-0x00015695.json":         {ID: "GAME.TXT:0x00015695", Safe: [4]int{48, 108, 1228, 168}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"options-title.json":                        {ID: "GAME.TXT:0x000004CD", Safe: [4]int{260, 176, 1012, 236}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x000004E9.json":      {ID: "GAME.TXT:0x000004E9", Safe: [4]int{320, 236, 1008, 284}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x000004FD.json":      {ID: "GAME.TXT:0x000004FD", Safe: [4]int{320, 284, 1008, 332}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x00000512.json":      {ID: "GAME.TXT:0x00000512", Safe: [4]int{320, 332, 1008, 380}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x00000525.json":      {ID: "GAME.TXT:0x00000525", Safe: [4]int{320, 380, 1008, 428}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x00000533.json":      {ID: "GAME.TXT:0x00000533", Safe: [4]int{320, 428, 1008, 476}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x0000053E.json":      {ID: "GAME.TXT:0x0000053E", Safe: [4]int{320, 476, 1008, 524}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x00000550.json":      {ID: "GAME.TXT:0x00000550", Safe: [4]int{320, 524, 1008, 572}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"option-rows/GAME.TXT-0x00000566.json":      {ID: "GAME.TXT:0x00000566", Safe: [4]int{320, 572, 1008, 620}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"retire/GAME.TXT-0x00000122.json":           {ID: "GAME.TXT:0x00000122", Safe: [4]int{472, 300, 736, 396}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"retire/GAME.TXT-0x00000141.json":           {ID: "GAME.TXT:0x00000141", Safe: [4]int{488, 396, 576, 448}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"retire/GAME.TXT-0x00000146.json":           {ID: "GAME.TXT:0x00000146", Safe: [4]int{488, 448, 568, 500}, Shadow: 4, Layered: false, Catalog: "draft.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION0A.json":             {ID: "GAME.TXT:@NATION0A", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION0B.json":             {ID: "GAME.TXT:@NATION0B", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION1A.json":             {ID: "GAME.TXT:@NATION1A", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION1B.json":             {ID: "GAME.TXT:@NATION1B", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION2A.json":             {ID: "GAME.TXT:@NATION2A", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION2B.json":             {ID: "GAME.TXT:@NATION2B", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION3A.json":             {ID: "GAME.TXT:@NATION3A", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"intro/GAME.TXT-@NATION3B.json":             {ID: "GAME.TXT:@NATION3B", Safe: [4]int{32, 32, 1248, 768}, Shadow: 4, Layered: true, Catalog: "nation-introduction.zh-Hant.tsv"},
			"help/GAME.TXT-@TUTORIAL1.json":             {ID: "GAME.TXT:@TUTORIAL1", Safe: [4]int{272, 416, 1024, 676}, Shadow: 4, Layered: true, Catalog: "help-bilingual.tsv"},
			"static/OPENCRD1.SS-role-adventure.json":    {ID: "OPENCRD1.SS:role:adventure", Safe: [4]int{264, 704, 1012, 732}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
			"static/OPENCRD1.SS-role-design.json":       {ID: "OPENCRD1.SS:role:design", Safe: [4]int{320, 704, 956, 732}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
			"static/OPENCRD1.SS-role-programming.json":  {ID: "OPENCRD1.SS:role:programming", Safe: [4]int{320, 704, 956, 732}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
			"static/OPENCRD1.SS-role-graphics.json":     {ID: "OPENCRD1.SS:role:graphics", Safe: [4]int{320, 704, 956, 732}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
			"static/OPENCRD1.SS-role-music.json":        {ID: "OPENCRD1.SS:role:music", Safe: [4]int{320, 704, 956, 732}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
			"static/OPENCRD1.SS-role-sound.json":        {ID: "OPENCRD1.SS:role:sound", Safe: [4]int{320, 704, 956, 732}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
			"static/OPENCRD1.SS-role-qa.json":           {ID: "OPENCRD1.SS:role:qa", Safe: [4]int{320, 704, 956, 732}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
			"static/OPENING.TXT-@MESSAGES-loading.json": {ID: "OPENING.TXT:@MESSAGES:loading", Safe: [4]int{492, 748, 788, 792}, Shadow: 0, Layered: false, Catalog: "static-overlay.zh-Hant.tsv"},
		},
	}
	var index struct {
		Schema int    `json:"schema"`
		Total  int    `json:"total"`
		Source string `json:"source_binding_sha256"`
		Tables []struct {
			File string `json:"file"`
		} `json:"tables"`
	}
	if hash(draftCatalogRegistry) != "7dc96f7915e091791b4f4fc01b64f5516cafd890d892d50abf9929eb24095209" {
		return needs, fmt.Errorf("compiled catalog index mismatch")
	}
	if err := json.Unmarshal(draftCatalogRegistry, &index); err != nil {
		return needs, err
	}
	if index.Schema != 1 || index.Total != 2022 || len(index.Tables) != 13 {
		return needs, fmt.Errorf("compiled catalog index shape")
	}
	needs.Source = index.Source
	for _, table := range index.Tables {
		needs.Tables = append(needs.Tables, table.File)
	}
	return needs, nil
}
