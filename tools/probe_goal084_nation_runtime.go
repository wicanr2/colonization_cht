// 目標084可丟棄探針：只觀測國家選擇頁標題當次底圖及兩層合成守門。
// 原版輸入唯讀；不修改 DOS 記憶體、畫布或正式前端。
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
	"path/filepath"
	"strings"

	golem "github.com/wicanr2/dosgolem"
	"github.com/wicanr2/dosgolem/overlay"
)

type input struct {
	Step         uint64 `json:"step"`
	Kind         string `json:"kind"`
	X, Y, Button int
}
type replay struct {
	Inputs []input `json:"inputs"`
	End    uint64  `json:"end"`
}
type preview struct {
	Prototype               bool   `json:"prototype"`
	SourceReceiptSHA256     string `json:"source_receipt_sha256"`
	SourceLoadReceiptSHA256 string `json:"source_load_receipt_sha256"`
	CatalogSHA256           string `json:"catalog_sha256"`
	FontSHA256              string `json:"font_sha256"`
	Layers                  []struct {
		Name        string `json:"name"`
		CandidateID string `json:"candidate_id"`
		Mask        string `json:"mask"`
		Safe        [4]int `json:"safe"`
		InkWidth    int    `json:"ink_width"`
		InkHeight   int    `json:"ink_height"`
		Position    [2]int `json:"position"`
	} `json:"layers"`
}
type field struct {
	name, id        string
	source, display []byte
	linear          uint32
	safe            image.Rectangle
	bbox            [4]int
	pixels          int
	ink             *image.Alpha
	position        image.Point
	before          []byte
	startStep       uint64
	openedCount     int
	formatted       bool
	patch           *overlay.Patch
	accepted        int
}

func must(e error) {
	if e != nil {
		panic(e)
	}
}
func read(path string) []byte { b, e := os.ReadFile(path); must(e); return b }
func hash(b []byte) string    { return fmt.Sprintf("%x", sha256.Sum256(b)) }
func save(path string, im image.Image) {
	f, e := os.Create(path)
	must(e)
	must(png.Encode(f, im))
	must(f.Close())
}
func rectBytes(b []byte, r image.Rectangle) []byte {
	out := make([]byte, 0, r.Dx()*r.Dy())
	for y := r.Min.Y; y < r.Max.Y; y++ {
		out = append(out, b[y*320+r.Min.X:y*320+r.Max.X]...)
	}
	return out
}
func delta(before, after []byte, r image.Rectangle) (int, [4]int, bool) {
	n, box, colors := 0, [4]int{320, 200, -1, -1}, true
	for y := r.Min.Y; y < r.Max.Y; y++ {
		for x := r.Min.X; x < r.Max.X; x++ {
			i := y*320 + x
			if before[i] == after[i] {
				continue
			}
			n++
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
			if after[i] != 0 && after[i] != 253 && after[i] != 254 {
				colors = false
			}
		}
	}
	return n, box, colors
}

func main() {
	root := flag.String("root", "/game", "合法 DOS 原版唯讀目錄")
	inputs := flag.String("inputs", "", "已固定的正常玩家輸入")
	previewPath := flag.String("preview", "", "已驗本機字模預覽")
	catalog := flag.String("catalog", "/repo/text/draft.zh-Hant.tsv", "真實譯稿")
	out := flag.String("out", "", "本機收據前綴")
	control := flag.Bool("control", false, "不裝觀測或合成的原版控制組")
	flag.Parse()
	if *inputs == "" || *previewPath == "" || *out == "" {
		panic("需明示輸入、預覽與輸出")
	}
	wants := map[string]string{
		"OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
		"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
		"GAME.TXT":    "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
		"LABELS.TXT":  "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
		"NAMES.TXT":   "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
	}
	for name, want := range wants {
		if hash(read(filepath.Join(*root, name))) != want {
			panic("原版版本不符：" + name)
		}
	}
	inputData := read(*inputs)
	allowed := map[string]bool{
		"bb86566b14d73136e27a096b35ba6b1e2e84ef011122ac817dd989dd7727e550": true,
		"44dc7ed1f4b6c321b67e39d62d7c973d2f9ade79e8159e4893d3f0814bca4d37": true,
		"4ac6c8ebeadec85b5ec650422e7b20fc9095020531f100ca2ad1bedabbf8b2d6": true,
		"27fe020f415a137f1c6cea3cb1da57d515e23bbd8a2bd129c952fe220794ceda": true,
	}
	if !allowed[hash(inputData)] {
		panic("玩家輸入版本不符")
	}
	var route replay
	must(json.Unmarshal(inputData, &route))
	if route.End != 60000000 && route.End != 68000000 {
		panic("重播終點不符")
	}
	previewData := read(*previewPath)
	if hash(previewData) != "6d530c7164df76ac4ab923bad296df3823299b77feb76a64441a6f017748efe7" {
		panic("預覽版本不符")
	}
	var p preview
	must(json.Unmarshal(previewData, &p))
	if !p.Prototype || p.SourceReceiptSHA256 != "af48f6f0177696cb8c7bce12692eee61fe5c3f92212f57f4525fc4566cdf9b74" ||
		p.SourceLoadReceiptSHA256 != "77cfef073a94fa8815136b0bf7de67a4a9050f12357ccb2ad990a7336bafcbc2" ||
		p.CatalogSHA256 != hash(read(*catalog)) || p.FontSHA256 != "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c" || len(p.Layers) != 2 {
		panic("字模來源與前輪證據不符")
	}
	fields := []*field{
		{name: "select", id: "LABELS.TXT:0x000008D3", source: []byte("Select"), display: []byte("Select"), linear: 0x4dfb5,
			safe: image.Rect(39, 35, 73, 46), bbox: [4]int{42, 36, 69, 44}, pixels: 120},
		{name: "power", id: "LABELS.TXT:0x000008DB", source: []byte("European Power"), display: []byte("European Power"), linear: 0x4dfbc,
			safe: image.Rect(17, 48, 95, 59), bbox: [4]int{20, 49, 91, 57}, pixels: 270},
	}
	for i, l := range fields {
		layer := p.Layers[i]
		if layer.Name != l.name || layer.CandidateID != l.id || layer.Safe != [4]int{l.safe.Min.X, l.safe.Min.Y, l.safe.Max.X, l.safe.Max.Y} ||
			layer.InkWidth <= 0 || layer.InkHeight <= 0 || layer.Position[0] < l.safe.Min.X*4+4 || layer.Position[1] < l.safe.Min.Y*4+4 ||
			layer.Position[0]+layer.InkWidth > l.safe.Max.X*4-4 || layer.Position[1]+layer.InkHeight > l.safe.Max.Y*4-4 {
			panic("字模欄位或幾何不符")
		}
		mask, e := base64.StdEncoding.Strict().DecodeString(layer.Mask)
		must(e)
		if len(mask) != layer.InkWidth*layer.InkHeight {
			panic("字模長度不符")
		}
		l.ink = image.NewAlpha(image.Rect(0, 0, layer.InkWidth, layer.InkHeight))
		copy(l.ink.Pix, mask)
		l.position = image.Pt(layer.Position[0], layer.Position[1])
	}
	m := golem.New()
	must(m.LoadEXE(read(filepath.Join(*root, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, *root)
	d.Install()
	defer d.Close()
	m.SetSoundBlasterPro(true)
	canvas := func() []byte { return m.Mem[0x2cae0 : 0x2cae0+64000] }
	frames := []map[string]any{}
	firstBoth := false
	hoverFallback := false
	awayRecovered := false
	negative := map[string]any{}
	firstBefore := map[string]string{}
	sourceEvents := map[string]any{}
	if !*control {
		m.WatchReads(0x4dfb5, 0x4dfca, func(a uint32, _ uint8) {
			cs, ip := m.CPU.OpAddr()
			if cs != 0x0d3a || ip != 0x0015 || m.VideoMode() != 0x13 {
				return
			}
			if len(d.Opened) == 0 || !strings.EqualFold(d.Opened[len(d.Opened)-1], "NATIONS.PIK") {
				return
			}
			for _, l := range fields {
				if a != l.linear || l.patch != nil || l.before != nil {
					continue
				}
				addr := int(l.linear)
				if !bytes.Equal(m.Mem[addr:addr+len(l.source)], l.source) || m.Mem[addr+len(l.source)] != 0 {
					continue
				}
				l.before = bytes.Clone(canvas())
				l.startStep = m.Steps
				l.openedCount = len(d.Opened)
				firstBefore[l.name] = hash(rectBytes(l.before, l.safe))
			}
		})
		m.SetBeforeInstruction(func() {
			if m.CPU.Seg[golem.CS] != 0x0d21 || m.CPU.IP != 0x00c6 {
				return
			}
			for _, l := range fields {
				if l.before == nil || m.Steps-l.startStep > 500000 {
					continue
				}
				const addr = 0x2a710
				if bytes.Equal(m.Mem[addr:addr+len(l.display)], l.display) && m.Mem[addr+len(l.display)] == 0 {
					l.formatted = true
				}
			}
		})
		m.SetOnFrame(func() {
			if m.Steps < 42000000 {
				return
			}
			for _, l := range fields {
				if l.before == nil || l.patch != nil {
					continue
				}
				if m.Steps-l.startStep > 500000 {
					l.before = nil
					continue
				}
				count, box, colors := delta(l.before, canvas(), l.safe)
				if count != l.pixels {
					continue
				}
				if !l.formatted || !colors || box != l.bbox {
					l.before = nil
					continue
				}
				var e error
				l.patch, e = overlay.NewPatch(l.before, canvas(), 320, 200, l.safe)
				must(e)
				l.accepted++
				sourceEvents[l.name] = map[string]any{"read_step": l.startStep, "patch_step": m.Steps, "before_safe_sha256": firstBefore[l.name], "changed_pixels": count, "bbox": box, "formatted_seen": l.formatted}
				l.before = nil
			}
			indexed := m.Indexed()
			cursorInTitle := image.Pt(int(d.Mouse.X), int(d.Mouse.Y)).In(image.Rect(0, 25, 110, 70))
			buttonGuard := d.Mouse.Buttons != 0
			layers := make([]overlay.Layer, len(fields))
			valid := make([]bool, len(fields))
			for i, l := range fields {
				addr := int(l.linear)
				valid[i] = l.patch != nil && len(d.Opened) == l.openedCount &&
					strings.EqualFold(d.Opened[len(d.Opened)-1], "NATIONS.PIK") && m.VideoMode() == 0x13 &&
					bytes.Equal(m.Mem[addr:addr+len(l.source)], l.source) && m.Mem[addr+len(l.source)] == 0
				// 每欄由合成器比對當幀原版像素；游標只遮住哪欄就只讓該欄回退。
				layers[i] = overlay.Layer{Patch: l.patch, Ink: l.ink, Position: l.position, ColorIndex: 254, Enabled: valid[i] && !buttonGuard}
			}
			output, results, e := overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, layers)
			must(e)
			reasons := []string{results[0].Reason, results[1].Reason}
			applied := 0
			for i, r := range results {
				if r.Applied {
					applied++
				}
				if buttonGuard && valid[i] {
					reasons[i] = "mouse-button-held"
				}
			}
			if applied == 2 && !firstBoth {
				firstBoth = true
				save(*out+".control.png", mustBase(indexed, m.DAC[:]))
				save(*out+".zh.png", output)
				stale := bytes.Clone(indexed)
				stale[fields[0].safe.Min.Y*320+fields[0].safe.Min.X] ^= 1
				_, sr, e := overlay.ComposeLayers(stale, m.DAC[:], 320, 200, 4, layers)
				must(e)
				negative["stale-first"] = [2]string{sr[0].Reason, sr[1].Reason}
				stale2 := bytes.Clone(indexed)
				stale2[fields[1].safe.Min.Y*320+fields[1].safe.Min.X] ^= 1
				_, sr2, e := overlay.ComposeLayers(stale2, m.DAC[:], 320, 200, 4, layers)
				must(e)
				negative["stale-second"] = [2]string{sr2[0].Reason, sr2[1].Reason}
				for i := range layers {
					layers[i].Ink = nil
				}
				missing, mr, e := overlay.ComposeLayers(indexed, m.DAC[:], 320, 200, 4, layers)
				must(e)
				negative["missing-ink"] = map[string]any{"reasons": [2]string{mr[0].Reason, mr[1].Reason}, "original_pixels": bytes.Equal(missing.Pix, mustBase(indexed, m.DAC[:]).Pix)}
			}
			if cursorInTitle && firstBoth && applied < 2 {
				hoverFallback = true
			}
			if hoverFallback && !cursorInTitle && applied == 2 {
				awayRecovered = true
			}
			if len(frames) < 2000 {
				frames = append(frames, map[string]any{"step": m.Steps, "mouse": [3]uint16{d.Mouse.X, d.Mouse.Y, d.Mouse.Buttons}, "cursor_in_title": cursorInTitle, "button_guard": buttonGuard, "valid": valid, "applied": applied, "reasons": reasons, "indexed_sha256": hash(indexed), "canvas_sha256": hash(canvas())})
			}
		})
	}
	apply := func(e input) {
		switch e.Kind {
		case "move":
			d.MoveMouse(e.X, e.Y)
		case "press":
			d.PressMouse(e.Button)
		case "release":
			d.ReleaseMouse(e.Button)
		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})
		default:
			panic("未知輸入")
		}
	}
	var prior uint64
	for _, e := range route.Inputs {
		if e.Step < prior || e.Step > route.End || e.Button < 0 || e.Button > 2 || e.Kind == "move" && (e.X < 0 || e.X >= 320 || e.Y < 0 || e.Y >= 200) {
			panic("玩家輸入格式不符")
		}
		for m.Steps < e.Step && !d.Exited && !m.CPU.Halted {
			must(m.Step())
		}
		if d.Exited || m.CPU.Halted {
			panic("輸入前原版提前結束")
		}
		apply(e)
		prior = e.Step
	}
	for m.Steps < route.End && !d.Exited && !m.CPU.Halted {
		must(m.Step())
	}
	if m.Steps != route.End {
		panic("未抵達重播終點")
	}
	state := map[string]any{"steps": m.Steps, "cycles": m.CPU.Cycles, "ticks": m.Ticks, "registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags, "memory_sha256": hash(m.Mem), "canvas_sha256": hash(canvas()), "indexed_sha256": hash(m.Indexed()), "palette_sha256": hash(m.DAC[:])}
	report := map[string]any{"version": "goal084-nation-runtime-v2", "control": *control, "input_sha256": hash(inputData), "input_hashes": wants, "preview_sha256": hash(previewData), "state": state, "opened": d.Opened, "source_events": sourceEvents, "frames": frames, "first_both_applied": firstBoth, "hover_fallback": hoverFallback, "away_recovered": awayRecovered, "negative": negative, "limitations": "可丟棄輸出層逐欄守門探針；非正式 Ebitengine 接線或 help 驗收"}
	b, e := json.MarshalIndent(report, "", "  ")
	must(e)
	must(os.WriteFile(*out+".json", append(b, '\n'), 0644))
	fmt.Printf("steps=%d frames=%d two=%v hover=%v away=%v\n", m.Steps, len(frames), firstBoth, hoverFallback, awayRecovered)
}

func mustBase(indexed, palette []byte) *image.RGBA {
	im, _, _, e := overlay.Compose(indexed, palette, 320, 200, 4, nil, nil, image.Point{}, 0, false)
	must(e)
	return im
}
