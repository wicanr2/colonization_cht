package main

import (
	"encoding/json"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/png"
	"os"
	"path/filepath"
	"strconv"
	"testing"
)

func TestHDSceneNormal96(t *testing.T) {
	root, game, assets, output := os.Getenv("TEST_HD_EVENT_ROOT"), os.Getenv("TEST_GAME_ROOT"), os.Getenv("TEST_HD_EVENT_ASSETS"), os.Getenv("TEST_HD_EVENT_NORMAL_OUTPUT")
	if root == "" || game == "" || assets == "" || output == "" {
		t.Skip("需要合法原版、來源模型與新輸出目錄")
	}
	need := func(e error) {
		t.Helper()
		if e != nil {
			t.Fatal(e)
		}
	}
	read := func(p string) []byte { t.Helper(); b, e := os.ReadFile(p); need(e); return b }
	var oracle struct {
		Checkpoints []hdNewGameOracleState
		End         hdNewGameOracleState
	}
	need(json.Unmarshal(read(filepath.Join(root, "r97-full-normal-r3/observed/draws.json")), &oracle))
	if len(oracle.Checkpoints) != 12 || oracle.End.Steps != 1100000000 {
		t.Fatal("original scope")
	}
	var replay windowReceipt
	input := read("/repo/workplace/reports/goal181-colony-rest/colony-v3/gui-colony.inputs.json")
	if hash(input) != "253c62a1f30387d76b736fc17cd22b7040ad53263088fe51e0cd6c5f81fee122" {
		t.Fatal("input fingerprint")
	}
	need(json.Unmarshal(input, &replay))
	need(os.Mkdir(output, 0755))
	save := filepath.Join(output, "saves")
	need(os.Mkdir(save, 0755))
	seed := read("/repo/workplace/reports/goal186-display-hd/hd-terrain-main-surfaces-r95/r95-Main-formal-gui-r1/save/COLONY09.SAV")
	if hash(seed) != "52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b" {
		t.Fatal("normal seed")
	}
	need(os.WriteFile(filepath.Join(save, "COLONY09.SAV"), seed, 0644))
	m := golem.New()
	need(m.LoadEXE(read(filepath.Join(game, "OPENING.EXE"))))
	m.Write8(uint32(golem.PSPSeg)*16+0x80, 2)
	m.WriteBytes(uint32(golem.PSPSeg)*16+0x81, []byte{'-', 'g', 13})
	d := golem.NewDOS(m, game)
	d.Scratch = save
	d.Install()
	closed := false
	defer func() {
		if !closed {
			d.Close()
		}
	}()
	m.SetSoundBlasterPro(true)
	if !m.EnableSBDigital() {
		t.Fatal("digital audio")
	}
	m.EnableOPLSynth(true)
	h := &hdRuntime{m: m}
	p, e := loadHDSceneRuntime(h, game, assets)
	need(e)
	h.scenes = p
	count, point := uint64(0), 0
	records := []map[string]any{}
	checkState := func(s hdNewGameOracleState) {
		t.Helper()
		c := m.CPU
		if m.Steps != s.Steps || hash(m.Mem) != s.Memory || hash(m.Indexed()) != s.Indexed || hash(m.DAC[:]) != s.Palette || c.R != s.Registers || c.Seg != s.Segments || c.IP != s.IP || c.Flags != s.Flags || c.Cycles != s.Cycles {
			t.Fatal("observer changed complete original state", m.Steps)
		}
	}
	capture := func() {
		if point == len(oracle.Checkpoints) {
			return
		}
		state := oracle.Checkpoints[point]
		if m.Steps > state.Steps || (m.Steps == state.Steps && count > state.Count) {
			t.Fatal("skipped point", point)
		}
		if m.Steps != state.Steps || count != state.Count {
			return
		}
		checkState(state)
		prefix := fmt.Sprintf("cp-%d", m.Steps)
		var model map[string][]any
		need(json.Unmarshal(read(filepath.Join(root, "r97-independent-main-model-r1", prefix+".owners.json")), &model))
		dialogRoot := os.Getenv("TEST_HD_DIALOG_MODEL")
		if dialogRoot == "" {
			t.Fatal("explicit independent MSS model required")
		}
		var dialogModel map[string][]any
		need(json.Unmarshal(read(filepath.Join(dialogRoot, prefix+".owners.json")), &dialogModel))
		for pos, cell := range dialogModel {
			if _, exists := model[pos]; exists {
				t.Fatal("independent model source overlap", pos)
			}
			model[pos] = cell
		}

		seen := 0
		for pos, cell := range p.visible {
			frame, known := p.frame(cell)
			expected, yes := model[strconv.Itoa(pos)]
			if known && frame.sprite != nil {
				seen++
				if !yes || frame.id != int(expected[0].(float64)) || int(cell.local) != int(expected[1].(float64)) || int(cell.value) != int(expected[2].(float64)) || cell.glyph != expected[3].(bool) {
					t.Fatal("independent Main owner differs", m.Steps, pos, cell, expected)
				}
			} else if yes {
				t.Fatal("model source missing", m.Steps, pos, expected)
			}
		}
		if seen != len(model) {
			t.Fatal("owner total", seen, len(model))
		}
		f := draftNativeFrame{mode: 0x13, canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16)}
		rendered := image.NewRGBA(image.Rect(0, 0, 1280, 800))
		receipt := p.paint(rendered, f)
		pngPath := filepath.Join(output, prefix+".png")
		file, e := os.Create(pngPath)
		need(e)
		need(png.Encode(file, rendered))
		need(file.Close())
		records = append(records, map[string]any{"steps": m.Steps, "input_count": count, "sources": seen, "scene": receipt, "rgba_sha256": hash(rendered.Pix)})
		encoded, e := json.MarshalIndent(records, "", "  ")
		need(e)
		need(os.WriteFile(filepath.Join(output, "points.json"), encoded, 0644))
		t.Log("complete original state and independent owners", m.Steps, "sources", seen, "accepted", p.spriteAccepted, "rejected", p.spriteRejected)
		point++
	}
	step := func() { p.beforeSpriteInstruction(); capture(); need(m.Step()) }
	previous := uint64(0)
	for _, input := range replay.Inputs {
		if input.Step < previous || input.Step > 1100000000 {
			t.Fatal("input order or range")
		}
		previous = input.Step
		for m.Steps < input.Step {
			step()
		}
		capture()
		switch input.Kind {
		case "move":
			d.MoveMouse(input.X, input.Y)
		case "press":
			d.PressMouse(input.Button)
		case "release":
			d.ReleaseMouse(input.Button)
		case "enter", "escape", "backspace", "up", "down", "left", "right":
			name := map[string]string{"enter": "Return", "escape": "Escape", "backspace": "Backspace", "up": "Up", "down": "Down", "left": "Left", "right": "Right"}[input.Kind]
			if !d.PushKeyNamed(name) {
				t.Fatal("BIOS key", name)
			}
		case "key":
			word, ok := map[string]uint16{"kp1": 0x4f00, "kp2": 0x5000, "kp4": 0x4b00, "kp6": 0x4d00, "kp7": 0x4700, "kp8": 0x4800, "kp9": 0x4900}[input.Text]
			if !ok {
				t.Fatal("unknown BIOS key")
			}
			d.PushKey(golem.Key{Scan: uint8(word >> 8), ASCII: uint8(word)})
		case "text":
			if !d.PushText(input.Text) {
				t.Fatal("text input")
			}
		default:
			t.Fatal("unsupported input", input.Kind)
		}
		count++
		capture()
	}
	for m.Steps < 1100000000 {
		step()
	}
	p.beforeSpriteInstruction()
	capture()
	checkState(oracle.End)
	if point != 12 || count != 96 || p.spriteAccepted != 55 || p.spriteRejected != 0 || p.spriteCall != nil {
		t.Fatal("normal route coverage", point, count, p.spriteAccepted, p.spriteRejected)
	}
	d.Close()
	closed = true
	reference := filepath.Join(root, "r97-entry-normal-r1/control/saves")
	expected, e := os.ReadDir(reference)
	need(e)
	actual, e := os.ReadDir(save)
	need(e)
	if len(expected) != len(actual) {
		t.Fatal("save inventory")
	}
	saves := map[string]string{}
	for _, entry := range expected {
		if entry.IsDir() {
			t.Fatal("unexpected directory")
		}
		a, b := read(filepath.Join(reference, entry.Name())), read(filepath.Join(save, entry.Name()))
		if hash(a) != hash(b) {
			t.Fatal("save changed", entry.Name())
		}
		saves[entry.Name()] = hash(b)
	}
	result := map[string]any{"result": "PASS_R98_SCENE_NORMAL96_ORIGINAL12_AND_ELEVEN_INDEPENDENT_MAIN_OWNERS", "points": point, "inputs": count, "complete_calls": p.spriteAccepted, "rejected": p.spriteRejected, "end": m.Steps, "saves": saves, "formal_GUI_credit": false, "production_connected": false}
	encoded, e := json.MarshalIndent(result, "", "  ")
	need(e)
	need(os.WriteFile(filepath.Join(output, "result.json"), encoded, 0644))
}
