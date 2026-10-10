// 規格013：僅Linux可撤回視窗原型；由build_window_prototype.py與既有適配器接合。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"os"
	"strings"
	"sync"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/audio"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	golem "github.com/wicanr2/dosgolem"
)

var windowSteps = flag.Uint64("window-steps", ^uint64(0), "驗收執行上限；正常遊玩預設不設上限，不修改DOS時鐘")
var replayPath = flag.String("replay-inputs", "", "僅驗收：重播先前真實視窗輸入")
var audioWAVPath = flag.String("audio-wav", "", "目標176：結束時把前端取得的 dosgolem 原始音訊（交錯 int16 立體聲）寫成 WAV；需 --audio")
var audioMute = flag.Bool("audio-mute", false, "目標176：只合成與錄音，不開播放裝置（無音效裝置的容器用）")
var independentMusic = flag.Bool("independent-music", true, "規格046：原版音樂獨立原速播放；停用時使用舊音訊串流")

// windowStepsPerUpdate 是每次 Update 推進的指令數；重播在同樣的邊界取音訊（規格040）。
const windowStepsPerUpdate = 200000

// audioPlayRate 是播放串流的取樣率；dosgolem 的 49,715 Hz 以線性內插換算過來。
const audioPlayRate = 48000

// audioStream 是給 Ebitengine 播放器讀的 16 位元立體聲串流。不足時補靜音、積壓超過 0.25 秒時丟最舊的，
// 兩者都只影響播放，不回饋到模擬（規格040）。
type audioStream struct {
	mu                                sync.Mutex
	paused                            bool
	rate                              uint64  // 來源取樣率
	src                               []int16 // 尚未換算的來源（交錯）
	srcBase                           uint64  // src[0] 的來源取樣編號
	outN                              uint64  // 已產生的輸出取樣數
	out                               []byte
	ReadBytes, Dropped, UnderrunBytes uint64
	last, fadeAnchor                  [2]int32
	gap, resuming                     bool
	fadeFrame                         int
}

const audioFadeFrames = audioPlayRate / 200 // 5ms，僅消除斷流邊界的人工跳幅。

func (s *audioStream) push(samples []int16) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.src = append(s.src, samples...)
	for {
		num := s.outN * s.rate
		i, frac := num/audioPlayRate, int64(num%audioPlayRate)
		if i < s.srcBase || i+1-s.srcBase >= uint64(len(s.src)/2) {
			break
		}
		k := int(i-s.srcBase) * 2
		var b [4]byte
		for c := 0; c < 2; c++ {
			a, z := int64(s.src[k+c]), int64(s.src[k+2+c])
			binary.LittleEndian.PutUint16(b[c*2:], uint16(int16(a+(z-a)*frac/audioPlayRate)))
		}
		s.out = append(s.out, b[:]...)
		s.outN++
	}
	if drop := (s.outN*s.rate)/audioPlayRate - s.srcBase; drop > 0 && drop <= uint64(len(s.src)/2) {
		s.src = s.src[drop*2:]
		s.srcBase += drop
	}
	if limit := audioPlayRate * 4 / 4; len(s.out) > limit {
		keep := audioPlayRate * 4 / 10
		s.Dropped += uint64(len(s.out) - keep)
		s.out = append([]byte(nil), s.out[len(s.out)-keep:]...)
		s.gap = true // 下一次讀取漸接被保留的取樣，不直接跳到新位置。
	}
}

func (s *audioStream) Read(p []byte) (int, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	if s.paused {
		clear(p)
		return len(p), nil
	}
	n := copy(p, s.out)
	s.out = s.out[n:]
	clear(p[n:])
	s.UnderrunBytes += uint64(len(p) - n)
	for i := 0; i+4 <= len(p); i += 4 {
		valid := i+4 <= n
		if valid && s.gap {
			s.gap, s.resuming, s.fadeFrame, s.fadeAnchor = false, true, 0, s.last
		} else if !valid && !s.gap {
			s.gap, s.resuming, s.fadeFrame, s.fadeAnchor = true, false, 0, s.last
		}
		if s.gap || s.resuming {
			if s.fadeFrame < audioFadeFrames {
				s.fadeFrame++
			}
			for c := 0; c < 2; c++ {
				v := int32(int16(binary.LittleEndian.Uint16(p[i+c*2:])))
				if s.gap {
					v = s.fadeAnchor[c] * int32(audioFadeFrames-s.fadeFrame) / audioFadeFrames
				} else {
					v = (s.fadeAnchor[c]*int32(audioFadeFrames-s.fadeFrame) + v*int32(s.fadeFrame)) / audioFadeFrames
				}
				binary.LittleEndian.PutUint16(p[i+c*2:], uint16(int16(v)))
			}
			if s.resuming && s.fadeFrame == audioFadeFrames {
				s.resuming = false
			}
		}
		for c := 0; c < 2; c++ {
			s.last[c] = int32(int16(binary.LittleEndian.Uint16(p[i+c*2:])))
		}
	}
	s.ReadBytes += uint64(len(p))
	return len(p), nil
}

// frontendAudio 收集 DrainAudio 的原始取樣（錄 WAV）並餵給播放串流。
type frontendAudio struct {
	rate   uint32
	wav    []int16
	stream *audioStream
	player *audio.Player
	err    string
	music  *musicPlayback
}

// 規格050：設定期間不消耗播放串流，也不推進獨立音樂DOS。
func (a *frontendAudio) setPaused(paused bool) {
	if a == nil {
		return
	}
	a.stream.mu.Lock()
	a.stream.paused = paused
	a.stream.mu.Unlock()
	if a.music != nil {
		a.music.mu.Lock()
		a.music.paused = paused
		a.music.mu.Unlock()
	}
	if a.player != nil {
		if paused {
			a.player.Pause()
		} else {
			a.player.Play()
		}
	}
}

func newFrontendAudio(m *golem.Machine, d *golem.DOS, play bool) *frontendAudio {
	if m.AudioRate() == 0 {
		return nil
	}
	a := &frontendAudio{rate: m.AudioRate(), stream: &audioStream{rate: uint64(m.AudioRate())}}
	if *independentMusic {
		native, err := newNativeMusic(d.Root)
		if err != nil {
			a.err = err.Error()
			fmt.Fprintln(os.Stderr, "獨立音樂無法啟動，沿用原音訊：", err)
		} else {
			a.music = &musicPlayback{native: native, stream: &audioStream{rate: uint64(m.AudioRate())},
				digital: &audioStream{rate: uint64(m.AudioRate())}, fallback: a.stream}
			m.EnableDigitalAudioTap(true)
			frontendBeforeInstruction = a.music.observe(m, d)
		}
	}
	if play {
		ctx := audio.NewContext(audioPlayRate)
		p, err := ctx.NewPlayer(a.playbackReader())
		if err != nil {
			a.err = err.Error()
			fmt.Fprintln(os.Stderr, "音效裝置無法開啟，改為靜音：", err)
			return a
		}
		p.SetBufferSize(100 * 1000 * 1000) // 0.1 秒
		p.Play()
		a.player = p
	}
	return a
}

func (a *frontendAudio) drain(m *golem.Machine) {
	if a == nil {
		return
	}
	s := m.DrainAudio()
	if *audioWAVPath != "" {
		a.wav = append(a.wav, s...)
	}
	a.stream.push(s)
	if a.music != nil {
		a.music.digital.push(m.DrainDigitalAudio())
	}
}

func (a *frontendAudio) status() map[string]any {
	if a == nil {
		return nil
	}
	a.stream.mu.Lock()
	rec := map[string]any{"rate": a.rate, "played_bytes": a.stream.ReadBytes, "dropped_bytes": a.stream.Dropped,
		"underrun_bytes": a.stream.UnderrunBytes, "produced_frames": a.stream.srcBase, "player": a.player != nil, "error": a.err}
	a.stream.mu.Unlock()
	if a.music != nil {
		music := a.music.status()
		rec["music"] = music
		rec["played_bytes"] = music["music_read_bytes"]
		rec["underrun_bytes"] = music["music_underrun_bytes"]
		rec["dropped_bytes"] = music["music_dropped_bytes"].(uint64) + music["digital_dropped_bytes"].(uint64)
	}
	return rec
}

func (a *frontendAudio) writeWAV() {
	if a == nil || *audioWAVPath == "" {
		return
	}
	data := make([]byte, 44+len(a.wav)*2)
	copy(data, "RIFF")
	binary.LittleEndian.PutUint32(data[4:], uint32(36+len(a.wav)*2))
	copy(data[8:], "WAVEfmt ")
	binary.LittleEndian.PutUint32(data[16:], 16)
	binary.LittleEndian.PutUint16(data[20:], 1)
	binary.LittleEndian.PutUint16(data[22:], 2)
	binary.LittleEndian.PutUint32(data[24:], a.rate)
	binary.LittleEndian.PutUint32(data[28:], a.rate*4)
	binary.LittleEndian.PutUint16(data[32:], 4)
	binary.LittleEndian.PutUint16(data[34:], 16)
	copy(data[36:], "data")
	binary.LittleEndian.PutUint32(data[40:], uint32(len(a.wav)*2))
	for i, v := range a.wav {
		binary.LittleEndian.PutUint16(data[44+i*2:], uint16(v))
	}
	must(os.WriteFile(*audioWAVPath, data, 0644))
}

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
	audio        *frontendAudio
}

func logicalMouse(x, y int) (int, int, bool) {
	if x < 0 || y < 0 || x >= 1280 || y >= 800 {
		return 0, 0, false
	}
	return x / 4, y / 4, true
}
func frontendFrame(im *image.RGBA, rec map[string]any) {
	if activeWindow != nil {
		g := activeWindow
		same := im != nil && g.latest != nil && im.Rect == g.latest.Rect && im.Stride == g.latest.Stride && bytes.Equal(im.Pix, g.latest.Pix)
		if !same {
			g.latest, g.dirty = im, true
		}
		g.record = rec
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
	case "key":
		_, ok := biosKeyWords[e.Text]
		return ok && e.X == 0 && e.Y == 0 && e.Button == 0
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
	case "key":
		w := biosKeyWords[e.Text]
		d.PushKey(golem.Key{Scan: uint8(w >> 8), ASCII: uint8(w)})
	}
}

// 目標163：標準 PC BIOS 鍵字（高位元組 set-1 掃描碼、低位元組 ASCII）。
// 只是 PC 鍵盤慣例，不含本遊戲位址；數字鍵盤依 NumLock 關閉時的移動鍵語意。
var letterScanCodes = [26]uint8{0x1E, 0x30, 0x2E, 0x20, 0x12, 0x21, 0x22, 0x23, 0x17, 0x24, 0x25, 0x26, 0x32,
	0x31, 0x18, 0x19, 0x10, 0x13, 0x1F, 0x14, 0x16, 0x2F, 0x11, 0x2D, 0x15, 0x2C}

var biosKeyWords = func() map[string]uint16 {
	w := map[string]uint16{"home": 0x4700, "end": 0x4F00, "pgup": 0x4900, "pgdn": 0x5100,
		"insert": 0x5200, "delete": 0x5300, "tab": 0x0F09,
		"kp7": 0x4700, "kp8": 0x4800, "kp9": 0x4900, "kp4": 0x4B00, "kp5": 0x4C00, "kp6": 0x4D00,
		"kp1": 0x4F00, "kp2": 0x5000, "kp3": 0x5100, "kp0": 0x5200, "kpdot": 0x5300}
	for i := 0; i < 10; i++ {
		n := fmt.Sprint(i + 1)
		w["f"+n] = uint16(0x3B+i) << 8
		w["shift-f"+n] = uint16(0x54+i) << 8
		w["ctrl-f"+n] = uint16(0x5E+i) << 8
		w["alt-f"+n] = uint16(0x68+i) << 8
	}
	for i, scan := range letterScanCodes {
		c := string(rune('a' + i))
		w["alt-"+c] = uint16(scan) << 8
		w["ctrl-"+c] = uint16(scan)<<8 | uint16(i+1)
	}
	return w
}()

var specialWindowKeys = [...]struct {
	key  ebiten.Key
	kind string
}{
	{ebiten.KeyBackspace, "backspace"}, {ebiten.KeyEnter, "enter"},
	{ebiten.KeyEscape, "escape"},
	{ebiten.KeyArrowLeft, "left"}, {ebiten.KeyArrowRight, "right"},
	{ebiten.KeyArrowUp, "up"}, {ebiten.KeyArrowDown, "down"},
}

var namedWindowKeys = func() []struct {
	key  ebiten.Key
	name string
} {
	keys := []struct {
		key  ebiten.Key
		name string
	}{{ebiten.KeyHome, "home"}, {ebiten.KeyEnd, "end"}, {ebiten.KeyPageUp, "pgup"}, {ebiten.KeyPageDown, "pgdn"},
		{ebiten.KeyInsert, "insert"}, {ebiten.KeyDelete, "delete"}, {ebiten.KeyTab, "tab"},
		{ebiten.KeyNumpad7, "kp7"}, {ebiten.KeyNumpad8, "kp8"}, {ebiten.KeyNumpad9, "kp9"},
		{ebiten.KeyNumpad4, "kp4"}, {ebiten.KeyNumpad5, "kp5"}, {ebiten.KeyNumpad6, "kp6"},
		{ebiten.KeyNumpad1, "kp1"}, {ebiten.KeyNumpad2, "kp2"}, {ebiten.KeyNumpad3, "kp3"},
		{ebiten.KeyNumpad0, "kp0"}, {ebiten.KeyNumpadDecimal, "kpdot"}}
	return keys
}()

var functionWindowKeys = [10]ebiten.Key{ebiten.KeyF1, ebiten.KeyF2, ebiten.KeyF3, ebiten.KeyF4, ebiten.KeyF5,
	ebiten.KeyF6, ebiten.KeyF7, ebiten.KeyF8, ebiten.KeyF9, ebiten.KeyF10}

// 每次 Update 只取按下邊緣；空格仍由 AppendInputChars 轉送一次。
// pressed 用來判斷修飾鍵（Shift／Ctrl／Alt）是否按住。
func specialWindowInputs(justPressed, pressed func(ebiten.Key) bool) []windowInput {
	var events []windowInput
	for _, key := range specialWindowKeys {
		if justPressed(key.key) {
			events = append(events, windowInput{Kind: key.kind})
		}
	}
	prefix := ""
	switch {
	case pressed(ebiten.KeyAlt):
		prefix = "alt-"
	case pressed(ebiten.KeyControl):
		prefix = "ctrl-"
	case pressed(ebiten.KeyShift):
		prefix = "shift-"
	}
	for i, key := range functionWindowKeys {
		if justPressed(key) {
			events = append(events, windowInput{Kind: "key", Text: prefix + "f" + fmt.Sprint(i+1)})
		}
	}
	for _, key := range namedWindowKeys {
		if justPressed(key.key) {
			events = append(events, windowInput{Kind: "key", Text: key.name})
		}
	}
	if prefix == "alt-" || prefix == "ctrl-" {
		for i := 0; i < 26; i++ {
			if justPressed(ebiten.KeyA + ebiten.Key(i)) {
				events = append(events, windowInput{Kind: "key", Text: prefix + string(rune('a'+i))})
			}
		}
	}
	return events
}

// filterWindowChars 去掉與同幀特殊鍵重複的字元：Alt／Ctrl 組合不另送字元；
// 數字鍵盤按下時，平台可能另產生數字或小數點字元，一併去掉。
func filterWindowChars(chars []rune, specials []windowInput, pressed func(ebiten.Key) bool) []rune {
	if pressed(ebiten.KeyAlt) || pressed(ebiten.KeyControl) {
		return nil
	}
	keypad := false
	for _, e := range specials {
		keypad = keypad || strings.HasPrefix(e.Text, "kp")
	}
	if !keypad {
		return chars
	}
	var out []rune
	for _, r := range chars {
		if (r < '0' || r > '9') && r != '.' {
			out = append(out, r)
		}
	}
	return out
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
	specials := specialWindowInputs(inpututil.IsKeyJustPressed, ebiten.IsKeyPressed)
	chars := filterWindowChars(ebiten.AppendInputChars(nil), specials, ebiten.IsKeyPressed)
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
	end := g.m.Steps + windowStepsPerUpdate
	if end > *windowSteps {
		end = *windowSteps
	}
	for g.m.Steps < end && !g.d.Exited && !g.m.CPU.Halted {
		if err := g.m.Step(); err != nil {
			return err
		}
	}
	g.audio.drain(g.m)
	stage := "opening"
	if g.record != nil && g.record["events"].(int) >= 5 {
		stage = "menu"
	}
	for _, name := range g.d.Opened {
		if strings.EqualFold(name, "VICEROY.EXE") && stage == "opening" { // 目標166：開場程式印出載入訊息後載入主程式
			stage = "loading"
		}
		if strings.EqualFold(name, "DIFFICUL.PIK") {
			stage = "difficulty"
		}
		if strings.EqualFold(name, "NATIONS.PIK") { // 目標164：選國頁載入旗卡圖
			stage = "nations"
		}
	}
	status := map[string]any{"step": g.m.Steps, "stage": stage, "frame": g.record,
		"rejected_input_count": len(g.rejected)}
	if frontendStatusExtra != nil {
		status["dialog"] = frontendStatusExtra // 目標167：最近一段訊息框印字
	}
	if a := g.audio.status(); a != nil {
		status["audio"] = a // 目標176：播放器已讀取的位元組數等
	}
	// 規格013 READY：只綁定獨立畫布；狀態步數不代表Draw已呈現。
	if g.latest != nil && g.latest.Stride == g.latest.Rect.Dx()*4 {
		status["canvas_rgba_sha256"] = fmt.Sprintf("%x", sha256.Sum256(g.latest.Pix))
		status["canvas_size"] = []int{g.latest.Rect.Dx(), g.latest.Rect.Dy()}
	}
	dumpJSON(g.out+".status.tmp", status)
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
		// 目標176：在與真 GUI 相同的邊界（每 windowStepsPerUpdate 道指令）取音訊，數位音效讀記憶體的時點才相同。
		a := newFrontendAudio(m, d, false)
		defer a.close()
		start := m.Steps
		step := func() {
			must(m.Step())
			if a != nil && (m.Steps-start)%windowStepsPerUpdate == 0 {
				a.drain(m)
			}
		}
		for _, e := range receipt.Inputs {
			for m.Steps < e.Step {
				step()
			}
			applyWindowInput(d, e)
		}
		for m.Steps < receipt.End {
			step()
		}
		a.drain(m)
		a.writeWAV()
		return
	}
	dumpJSON(out+".status.json", map[string]any{"step": 0, "stage": "opening"})
	ebiten.SetWindowSize(1280, 800)
	ebiten.SetWindowTitle("Colonization CHT " + frontendReleaseVersion)
	ebiten.SetWindowClosingHandled(true)
	ebiten.SetRunnableOnUnfocused(true)
	ebiten.SetCursorMode(ebiten.CursorModeHidden)
	g.audio = newFrontendAudio(m, d, !*audioMute)
	defer g.audio.close()
	err := ebiten.RunGame(g)
	g.audio.writeWAV()
	// 目標169：原版執行出錯時也先寫下現場輸入與錯誤位置，才能以重播重現。
	dumpJSON(out+".inputs.json", windowReceipt{Inputs: g.inputs, End: m.Steps, Rejected: g.rejected})
	if err != nil {
		c := m.CPU
		dumpJSON(out+".crash.json", map[string]any{"error": err.Error(), "steps": m.Steps,
			"cs_ip": fmt.Sprintf("%04X:%04X", c.Seg[golem.CS], c.IP), "registers": c.R, "segments": c.Seg})
		panic(err)
	}
}
