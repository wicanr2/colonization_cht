// 目標078／082可丟棄探針：只在輸出合成層觀測指定難度卡片的執行期背景與回退。
// 不修改原版 RAM、畫布、輸入資料或正式 live_menu.go。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/png"
	"os"
	"strings"

	golem "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/overlay"
)

type runtimeInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
}
type runtimeReplay struct {
	Inputs []runtimeInput `json:"inputs"`
	End    uint64         `json:"end"`
}
type runtimePreview struct {
	Prototype               bool   `json:"prototype"`
	SourceLoadReceiptSHA256 string `json:"source_load_receipt_sha256"`
	CatalogSHA256           string `json:"catalog_sha256"`
	FontSHA256              string `json:"font_sha256"`
	Layers                  []struct {
		Name        string `json:"name"`
		CandidateID string `json:"candidate_id"`
		Safe        [4]int `json:"safe"`
		InkWidth    int    `json:"ink_width"`
		InkHeight   int    `json:"ink_height"`
		Position    [2]int `json:"position"`
		Mask        string `json:"mask"`
	} `json:"layers"`
}
type cardField struct {
	name, key, source string
	linear            uint32
	safe              image.Rectangle
	bbox              [4]int
	diffCount         int
	ink               *image.Alpha
	position          image.Point
	before            []byte
	beforeStep        uint64
	afterStep         uint64
	openedCount       int
	patch             *overlay.Patch
}

func need(err error) {
	if err != nil {
		panic(err)
	}
}
func read(path string) []byte   { data, err := os.ReadFile(path); need(err); return data }
func digest(data []byte) string { return fmt.Sprintf("%x", sha256.Sum256(data)) }
func rectBytes(canvas []byte, rect image.Rectangle) []byte {
	result := make([]byte, 0, rect.Dx()*rect.Dy())
	for y := rect.Min.Y; y < rect.Max.Y; y++ {
		result = append(result, canvas[y*320+rect.Min.X:y*320+rect.Max.X]...)
	}
	return result
}
func delta(before, after []byte, rect image.Rectangle) (int, [4]int) {
	count, box := 0, [4]int{320, 200, -1, -1}
	for y := rect.Min.Y; y < rect.Max.Y; y++ {
		for x := rect.Min.X; x < rect.Max.X; x++ {
			i := y*320 + x
			if before[i] != after[i] {
				count++
				if x < box[0] {
					box[0] = x
				}
				if y < box[1] {
					box[1] = y
				}
				if x > box[2] {
					box[2] = x
				}
				if y > box[3] {
					box[3] = y
				}
			}
		}
	}
	return count, box
}
func save(path string, im image.Image) {
	file, err := os.Create(path)
	need(err)
	need(png.Encode(file, im))
	need(file.Close())
}

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀根目錄")
	inputs := flag.String("inputs", "/out/goal059-ebiten.inputs.json", "九筆真視窗輸入")
	previewPath := flag.String("preview", "/out/goal077-card-preview.json", "已核對的本機字模收據")
	catalogPath := flag.String("catalog", "/repo/text/draft.zh-Hant.tsv", "譯稿唯一來源")
	out := flag.String("out", "/out/goal078-card-runtime", "本機報告與 PNG 前綴")
	hover := flag.Bool("hover", false, "在卡片完成後移入再移出游標")
	control := flag.Bool("control", false, "不註冊觀測與合成的原版狀態對照")
	second := flag.Bool("second", false, "目標082：以固定點擊輸入觀測第二張卡片")
	flag.Parse()
	versions := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
	}
	for name, want := range versions {
		if digest(read(*root+"/"+name)) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := read(*inputs)
	inputSHA := "51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc"
	loadReceiptSHA := "580f2f92475a12db9c065a3476e20f4fd315f27521030ac794dedf7aa3b71790"
	if *second {
		inputSHA = "7e89bf0edabb8b26df5168342bfd42226b7a467b8e7c8abdab87e83275a32e7e"
		loadReceiptSHA = "63cdd7305a8901bca903cbff090e3a9033df29c44d06c17d1a96f8320c813e20"
	}
	if digest(inputData) != inputSHA {
		panic("正常玩家輸入版本不符")
	}
	var replay runtimeReplay
	need(json.Unmarshal(inputData, &replay))
	var preview runtimePreview
	need(json.Unmarshal(read(*previewPath), &preview))
	if !preview.Prototype || preview.SourceLoadReceiptSHA256 != loadReceiptSHA ||
		preview.CatalogSHA256 != digest(read(*catalogPath)) ||
		preview.FontSHA256 != "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c" ||
		len(preview.Layers) != 2 {
		panic("字模收據版本或來源不符")
	}
	fields := []*cardField{
		{name: "title", key: "NAMES.TXT:0x00000C0C", source: "Discoverer", linear: 0x4cc6a,
			safe: image.Rect(138, 44, 186, 51), bbox: [4]int{141, 45, 182, 49}, diffCount: 164},
		{name: "subtitle", key: "LABELS.TXT:0x000008A9", source: "Easiest", linear: 0x4df90,
			safe: image.Rect(146, 52, 180, 60), bbox: [4]int{150, 53, 174, 58}, diffCount: 83},
	}
	if *second {
		fields = []*cardField{
			{name: "title", key: "NAMES.TXT:0x00000C18", source: "Explorer", linear: 0x4cc75,
				safe: image.Rect(247, 44, 287, 51), bbox: [4]int{250, 45, 283, 49}, diffCount: 134},
			{name: "subtitle", key: "LABELS.TXT:0x000008B2", source: "Easy", linear: 0x4df98,
				safe: image.Rect(256, 52, 279, 60), bbox: [4]int{260, 53, 275, 58}, diffCount: 55},
		}
	}
	for i, layer := range preview.Layers {
		field := fields[i]
		if layer.Name != field.name || layer.CandidateID != field.key ||
			layer.Safe != [4]int{field.safe.Min.X, field.safe.Min.Y, field.safe.Max.X, field.safe.Max.Y} ||
			layer.InkWidth <= 0 || layer.InkHeight <= 0 ||
			layer.Position[0] < field.safe.Min.X*4 || layer.Position[1] < field.safe.Min.Y*4 ||
			layer.Position[0]+layer.InkWidth > field.safe.Max.X*4 ||
			layer.Position[1]+layer.InkHeight > field.safe.Max.Y*4 {
			panic("字模欄位或幾何不符：" + field.name)
		}
		mask, err := base64.StdEncoding.Strict().DecodeString(layer.Mask)
		need(err)
		if len(mask) != layer.InkWidth*layer.InkHeight {
			panic("中文字模長度不符")
		}
		field.ink = image.NewAlpha(image.Rect(0, 0, layer.InkWidth, layer.InkHeight))
		copy(field.ink.Pix, mask)
		field.position = image.Pt(layer.Position[0], layer.Position[1])
	}
	m := golem.New()
	need(m.LoadEXE(read(*root + "/OPENING.EXE")))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	canvas := func() []byte { return m.Mem[0x2cae0 : 0x2cae0+64000] }
	if !*control {
		watchEnd := uint32(0x4df97)
		if *second {
			watchEnd = 0x4df9d
		}
		m.WatchReads(0x4cc6a, watchEnd, func(address uint32, _ uint8) {
			cs, ip := m.CPU.OpAddr()
			if cs != 0x0e2d || ip != 0x11cf || m.VideoMode() != 0x13 {
				return
			}
			seenArt := false
			for _, name := range d.Opened {
				seenArt = seenArt || strings.EqualFold(name, "DIFFICUL.PIK")
			}
			if !seenArt {
				return
			}
			for _, field := range fields {
				p := int(field.linear)
				if address != field.linear || field.before != nil || !bytes.Equal(m.Mem[p:p+len(field.source)], []byte(field.source)) || m.Mem[p+len(field.source)] != 0 {
					continue
				}
				field.before = bytes.Clone(canvas())
				field.beforeStep = m.Steps
				field.openedCount = len(d.Opened)
			}
		})
	}
	frames := []map[string]any{}
	firstApplied := false
	var firstAppliedIndexed []byte
	negative := map[string]string{}
	negativePixels := map[string]bool{}
	if !*control {
		m.SetOnFrame(func() {
			frameStart := uint64(29700000)
			if *second {
				frameStart = 32000000
			}
			if m.Steps < frameStart {
				return
			}
			for _, field := range fields {
				if field.before == nil || field.patch != nil {
					continue
				}
				if m.Steps-field.beforeStep > 1000000 {
					continue
				}
				count, box := delta(field.before, canvas(), field.safe)
				if count != field.diffCount || box != field.bbox {
					continue
				}
				var err error
				field.patch, err = overlay.NewPatch(field.before, canvas(), 320, 200, field.safe)
				need(err)
				field.afterStep = m.Steps
			}
			layers := make([]overlay.Layer, len(fields))
			sourceValid := make(map[string]bool, len(fields))
			cursorMinX, cursorMaxX := 112, 212
			if *second {
				cursorMinX, cursorMaxX = 225, 304
			}
			cursorGuard := cursorMinX <= int(d.Mouse.X) && int(d.Mouse.X) < cursorMaxX &&
				24 <= int(d.Mouse.Y) && int(d.Mouse.Y) < 80
			for i, field := range fields {
				p := int(field.linear)
				sourceValid[field.name] = bytes.Equal(m.Mem[p:p+len(field.source)], []byte(field.source)) &&
					m.Mem[p+len(field.source)] == 0 && m.VideoMode() == 0x13 &&
					field.before != nil && len(d.Opened) == field.openedCount
				layers[i] = overlay.Layer{Patch: field.patch, Ink: field.ink, Position: field.position,
					ColorIndex: 254, Enabled: !cursorGuard && d.Mouse.Buttons == 0 &&
						(field.patch == nil || sourceValid[field.name])}
			}
			indexed := m.Indexed()
			unguardedLayers := append([]overlay.Layer(nil), layers...)
			for i := range unguardedLayers {
				unguardedLayers[i].Enabled = true
			}
			_, unguardedResults, err := overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, unguardedLayers)
			need(err)
			output, results, err := overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, layers)
			need(err)
			reasons := make([]string, len(fields))
			unguardedReasons := make([]string, len(fields))
			applied := 0
			for i, result := range results {
				reasons[i] = result.Reason
				unguardedReasons[i] = unguardedResults[i].Reason
				if cursorGuard {
					reasons[i] = "cursor-conservative-guard"
				}
				if d.Mouse.Buttons != 0 {
					reasons[i] = "mouse-button-held"
				}
				if fields[i].patch != nil && !sourceValid[fields[i].name] {
					reasons[i] = "source-or-context-changed"
				}
				if result.Applied {
					applied++
				}
			}
			if applied == 2 && !firstApplied {
				firstApplied = true
				firstAppliedIndexed = bytes.Clone(indexed)
				base, _, _, err := overlay.Compose(indexed, m.DAC[:], 320, 200, 4, nil, nil, image.Point{}, 0, false)
				need(err)
				save(*out+".control.png", base)
				save(*out+".zh.png", output)
				stale := bytes.Clone(indexed)
				stale[fields[0].safe.Min.Y*320+fields[0].safe.Min.X] ^= 1
				_, staleResults, err := overlay.ComposeLayers(stale, m.DAC[:], 320, 200, 4, layers)
				need(err)
				negative["stale-frame"] = staleResults[0].Reason
				missingLayers := append([]overlay.Layer(nil), layers...)
				for i := range missingLayers {
					missingLayers[i].Ink = nil
				}
				missingFrame, missingResults, err := overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, missingLayers)
				need(err)
				negative["missing-ink"] = missingResults[0].Reason
				negativePixels["missing-ink"] = bytes.Equal(missingFrame.Pix, base.Pix)
				missingTranslationLayers := append([]overlay.Layer(nil), layers...)
				for i := range missingTranslationLayers {
					missingTranslationLayers[i].Enabled = false
				}
				missingTranslationFrame, missingTranslationResults, err := overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, missingTranslationLayers)
				need(err)
				negative["missing-translation"] = missingTranslationResults[0].Reason
				negativePixels["missing-translation"] = bytes.Equal(missingTranslationFrame.Pix, base.Pix)
				// 模擬後續原文／場景條件失效；不改動機器記憶體。
				negative["source-or-context-changed"] = missingTranslationResults[0].Reason
				negativePixels["source-or-context-changed"] = bytes.Equal(missingTranslationFrame.Pix, base.Pix)
			}
			if m.Steps >= frameStart {
				record := map[string]any{"step": m.Steps, "mouse": [3]uint16{d.Mouse.X, d.Mouse.Y, d.Mouse.Buttons},
					"canvas_sha256": digest(canvas()), "indexed_sha256": digest(indexed), "palette_sha256": digest(m.DAC[:]),
					"reasons": reasons, "unguarded_reasons": unguardedReasons,
					"source_and_context_valid": sourceValid, "applied": applied}
				if firstAppliedIndexed != nil {
					count, box := delta(firstAppliedIndexed, indexed, image.Rect(0, 0, 320, 200))
					intersections := map[string]int{}
					for _, field := range fields {
						intersections[field.name], _ = delta(firstAppliedIndexed, indexed, field.safe)
					}
					record["indexed_delta_from_first_applied"] = map[string]any{"count": count, "bbox_inclusive": box,
						"safe_intersections": intersections}
				}
				frames = append(frames, record)
			}
		})
	}
	apply := func(event runtimeInput) {
		switch event.Kind {
		case "move":
			d.MoveMouse(event.X, event.Y)
		case "press":
			d.PressMouse(event.Button)
		case "release":
			d.ReleaseMouse(event.Button)
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		default:
			panic("未知玩家輸入")
		}
	}
	step := func() { need(m.Step()) }
	baseEnd := uint64(32000000)
	if *second {
		baseEnd = 40000000
	}
	end := baseEnd
	if *hover {
		end = baseEnd + 8000000
	}
	var prior uint64
	for _, event := range replay.Inputs {
		if event.Step < prior || event.Step > baseEnd || event.Button < 0 || event.Button > 2 ||
			(event.Kind == "move" && (event.X < 0 || event.X >= 320 || event.Y < 0 || event.Y >= 200)) {
			panic("玩家輸入收據不符")
		}
		for m.Steps < event.Step {
			step()
		}
		apply(event)
		prior = event.Step
	}
	if *hover {
		for m.Steps < baseEnd {
			step()
		}
		hoverX, hoverY := 160, 48
		if *second {
			hoverX, hoverY = 265, 55
		}
		d.MoveMouse(hoverX, hoverY)
		for m.Steps < baseEnd+4000000 {
			step()
		}
		d.MoveMouse(16, 16)
	}
	for m.Steps < end && !d.Exited && !m.CPU.Halted {
		step()
	}
	sources := map[string]any{}
	for _, field := range fields {
		var beforeRectSHA string
		if field.before != nil {
			beforeRectSHA = digest(rectBytes(field.before, field.safe))
		}
		sources[field.name] = map[string]any{"candidate_id": field.key, "source_linear": field.linear,
			"read_site": "0E2D:11CF", "before_step": field.beforeStep, "after_frame_step": field.afterStep,
			"opened_count_at_capture": field.openedCount,
			"before_rect_sha256":      beforeRectSHA, "expected_changed_pixels": field.diffCount,
			"expected_bbox_inclusive": field.bbox, "patch_ready": field.patch != nil}
	}
	cpu := m.CPU
	report := map[string]any{"version": "goal078-card-runtime-v2", "variant_hover": *hover, "control": *control,
		"input_hashes": versions, "input_sha256": digest(inputData), "preview_sha256": digest(read(*previewPath)),
		"dos_address_space": "real-mode CS:IP and 20-bit linear RAM", "canvas_address_space": "320x200 logical indexed pixels",
		"end": m.Steps, "exited": d.Exited, "frames": frames, "sources": sources,
		"registers": cpu.R, "segments": cpu.Seg, "ip": cpu.IP, "flags": cpu.Flags,
		"ticks": m.Ticks, "frame_count": m.Frames, "cycles": cpu.Cycles,
		"negative_controls": negative, "first_both_applied": firstApplied,
		"negative_original_pixels_unchanged": negativePixels,
		"memory_sha256":                      digest(m.Mem), "canvas_sha256": digest(canvas()),
		"indexed_sha256": digest(m.Indexed()), "palette_sha256": digest(m.DAC[:]),
		"limitations": "可丟棄執行期探針；此路徑游標確實變更索引畫面，但座標外包不是任意游標形狀的精確界線；不授權正式覆蓋"}
	if *second {
		report["version"] = "goal082-second-card-runtime-v1"
		report["variant_second"] = true
	}
	encoded, err := json.MarshalIndent(report, "", "  ")
	need(err)
	need(os.WriteFile(*out+".json", append(encoded, '\n'), 0644))
	fmt.Printf("%d steps; %d relevant frames; first both applied=%v; hover=%v\n", m.Steps, len(frames), firstApplied, *hover)
}
