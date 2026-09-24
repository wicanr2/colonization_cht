// 規格013：僅Linux可撤回視窗原型；由build_window_prototype.py與既有適配器接合。
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"os"
	"strings"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	golem "github.com/wicanr2/dosgolem"
)

var windowSteps = flag.Uint64("window-steps", 100000000, "原型執行上限，不修改DOS時鐘")
var replayPath = flag.String("replay-inputs", "", "僅驗收：重播先前真實視窗輸入")
var activeWindow *windowGame

func init() {
	frontendFrameSink = frontendFrame
	frontendRunner = runWindow
}

type windowInput struct {
	Step   uint64 `json:"step"`
	Kind   string `json:"kind"`
	X      int    `json:"x"`
	Y      int    `json:"y"`
	Button int    `json:"button"`
	Text   string `json:"text,omitempty"`
}
type windowReceipt struct {
	Inputs   []windowInput `json:"inputs"`
	End      uint64        `json:"end"`
	Rejected []string      `json:"rejected,omitempty"`
}
type windowGame struct {
	m            *golem.Machine
	d            *golem.DOS
	out          string
	latest       *image.RGBA
	record       map[string]any
	texture      *ebiten.Image
	dirty        bool
	held         [3]bool
	lastX, lastY int
	inputs       []windowInput
	rejected     []string
}

func logicalMouse(x, y int) (int, int, bool) {
	if x < 0 || y < 0 || x >= 1280 || y >= 800 {
		return 0, 0, false
	}
	return x / 4, y / 4, true
}
func frontendFrame(im *image.RGBA, rec map[string]any) {
	if activeWindow != nil {
		activeWindow.latest, activeWindow.record, activeWindow.dirty = im, rec, true
	}
}
func supportedDOSChar(s string) bool {
	if len(s) != 1 {
		return false
	}
	c := s[0]
	return c >= 'a' && c <= 'z' || c >= 'A' && c <= 'Z' ||
		c >= '0' && c <= '9' || c == ' '
}
func validWindowInput(e windowInput) bool {
	switch e.Kind {
	case "move":
		return e.Text == "" && e.Button == 0 && e.X >= 0 && e.X < 320 && e.Y >= 0 && e.Y < 200
	case "press", "release":
		return e.Text == "" && e.X == 0 && e.Y == 0 && e.Button >= 0 && e.Button <= 2
	case "text":
		return supportedDOSChar(e.Text) && e.X == 0 && e.Y == 0 && e.Button == 0
	case "backspace", "enter", "escape", "left", "right", "up", "down":
		return e.Text == "" && e.X == 0 && e.Y == 0 && e.Button == 0
	default:
		return false
	}
}
func applyWindowInput(d *golem.DOS, e windowInput) {
	if !validWindowInput(e) {
		panic("無效視窗輸入")
	}
	switch e.Kind {
	case "move":
		d.MoveMouse(e.X, e.Y)
	case "press":
		d.PressMouse(e.Button)
	case "release":
		d.ReleaseMouse(e.Button)
	case "enter":
		if !d.PushKeyNamed("Return") {
			panic("dosgolem 缺少 Return 鍵")
		}
	case "backspace":
		if !d.PushKeyNamed("Backspace") {
			panic("dosgolem 缺少 Backspace 鍵")
		}
	case "escape", "left", "right", "up", "down":
		name := map[string]string{
			"escape": "Escape", "left": "Left", "right": "Right",
			"up": "Up", "down": "Down",
		}[e.Kind]
		if !d.PushKeyNamed(name) {
			panic("dosgolem 缺少 " + name + " 鍵")
		}
	case "text":
		if !d.PushText(e.Text) {
			panic("dosgolem 拒絕已審核字元")
		}
	}
}

var specialWindowKeys = [...]struct {
	key  ebiten.Key
	kind string
}{
	{ebiten.KeyBackspace, "backspace"}, {ebiten.KeyEnter, "enter"},
	{ebiten.KeyEscape, "escape"},
	{ebiten.KeyArrowLeft, "left"}, {ebiten.KeyArrowRight, "right"},
	{ebiten.KeyArrowUp, "up"}, {ebiten.KeyArrowDown, "down"},
}

// 每次 Update 只取按下邊緣；空格仍由 AppendInputChars 轉送一次。
func specialWindowInputs(justPressed func(ebiten.Key) bool) []windowInput {
	var events []windowInput
	for _, key := range specialWindowKeys {
		if justPressed(key.key) {
			events = append(events, windowInput{Kind: key.kind})
		}
	}
	return events
}
func (g *windowGame) emit(e windowInput) {
	e.Step = g.m.Steps
	applyWindowInput(g.d, e)
	g.inputs = append(g.inputs, e)
}
func (g *windowGame) release() {
	for i, v := range g.held {
		if v {
			g.emit(windowInput{Kind: "release", Button: i})
			g.held[i] = false
		}
	}
}
func (g *windowGame) Update() error {
	if ebiten.IsWindowBeingClosed() || g.m.Steps >= *windowSteps || g.d.Exited || g.m.CPU.Halted {
		g.release()
		return ebiten.Termination
	}
	x, y, inside := logicalMouse(ebiten.CursorPosition())
	focused := ebiten.IsFocused()
	chars := ebiten.AppendInputChars(nil)
	specials := specialWindowInputs(inpututil.IsKeyJustPressed)
	if !focused || !inside {
		g.release()
	} else {
		if x != g.lastX || y != g.lastY {
			g.emit(windowInput{Kind: "move", X: x, Y: y})
			g.lastX, g.lastY = x, y
		}
		for i, button := range []ebiten.MouseButton{ebiten.MouseButtonLeft, ebiten.MouseButtonRight, ebiten.MouseButtonMiddle} {
			down := ebiten.IsMouseButtonPressed(button)
			if down != g.held[i] {
				kind := "release"
				if down {
					kind = "press"
				}
				g.emit(windowInput{Kind: kind, Button: i})
				g.held[i] = down
			}
		}
	}
	if focused {
		for _, r := range chars {
			s := string(r)
			if !supportedDOSChar(s) {
				g.rejected = append(g.rejected, s)
				fmt.Fprintf(os.Stderr, "不支援的 DOS 輸入字元 %q，未送入原版；請用英文字母、數字或空格\n", s)
				continue
			}
			g.emit(windowInput{Kind: "text", Text: s})
		}
		for _, event := range specials {
			g.emit(event)
		}
	}
	end := g.m.Steps + 200000
	if end > *windowSteps {
		end = *windowSteps
	}
	for g.m.Steps < end && !g.d.Exited && !g.m.CPU.Halted {
		if err := g.m.Step(); err != nil {
			return err
		}
	}
	stage := "opening"
	if g.record != nil && g.record["events"].(int) >= 5 {
		stage = "menu"
	}
	for _, name := range g.d.Opened {
		if strings.EqualFold(name, "DIFFICUL.PIK") {
			stage = "difficulty"
		}
	}
	dumpJSON(g.out+".status.tmp", map[string]any{"step": g.m.Steps, "stage": stage, "frame": g.record,
		"rejected_input_count": len(g.rejected)})
	must(os.Rename(g.out+".status.tmp", g.out+".status.json"))
	return nil
}
func (g *windowGame) Draw(screen *ebiten.Image) {
	if g.latest == nil {
		return
	}
	if g.texture == nil {
		g.texture = ebiten.NewImage(1280, 800)
	}
	if g.dirty {
		g.texture.WritePixels(g.latest.Pix)
		g.dirty = false
	}
	screen.DrawImage(g.texture, nil)
}
func (g *windowGame) Layout(int, int) (int, int) { return 1280, 800 }
func runWindow(m *golem.Machine, d *golem.DOS, render func(string), out string) {
	g := &windowGame{m: m, d: d, out: out, lastX: -1, lastY: -1}
	activeWindow = g
	if *replayPath != "" {
		var receipt windowReceipt
		must(json.Unmarshal(read(*replayPath), &receipt))
		if receipt.End > *windowSteps {
			panic("重播終點超出明示上限")
		}
		previous := uint64(0)
		for _, e := range receipt.Inputs {
			if e.Step < previous || e.Step > receipt.End || !validWindowInput(e) {
				panic("無效輸入收據")
			}
			previous = e.Step
		}
		for _, e := range receipt.Inputs {
			for m.Steps < e.Step {
				must(m.Step())
			}
			applyWindowInput(d, e)
		}
		for m.Steps < receipt.End {
			must(m.Step())
		}
		return
	}
	dumpJSON(out+".status.json", map[string]any{"step": 0, "stage": "opening"})
	ebiten.SetWindowSize(1280, 800)
	ebiten.SetWindowTitle("Colonization CHT prototype")
	ebiten.SetWindowClosingHandled(true)
	ebiten.SetRunnableOnUnfocused(true)
	ebiten.SetCursorMode(ebiten.CursorModeHidden)
	must(ebiten.RunGame(g))
	dumpJSON(out+".inputs.json", windowReceipt{Inputs: g.inputs, End: m.Steps, Rejected: g.rejected})
}
