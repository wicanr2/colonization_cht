// 規格051 DRAFT：僅由隔離原型組裝器加入，不連入正式前端。
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/csv"
	"flag"
	"fmt"
	"image"
	"image/color"
	imagedraw "image/draw"
	"io"
	"os"
	"strings"
	"unicode/utf8"

	"github.com/hajimehoshi/ebiten/v2"
	"github.com/hajimehoshi/ebiten/v2/inpututil"
	"golang.org/x/image/font"
	"golang.org/x/image/font/opentype"
	"golang.org/x/image/math/fixed"
)

const prototypeToolbarHeight = 48
const prototypeUIFontSHA = "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a"

var prototypeUIFont = flag.String("prototype-ui-font", "", "規格051：本機固定Noto Sans CJK候選TTC")
var prototypeUICatalog = flag.String("prototype-ui-catalog", "", "規格051：前端五語TSV")
var prototypeDisplayLanguage = "zh-Hant"

var prototypeLanguages = []string{"zh-Hant", "zh-Hans", "ja", "ko", "en"}
var prototypeUIKeys = []string{"ui.settings", "ui.description", "ui.language", "ui.graphics",
	"ui.language.zh-Hant", "ui.language.zh-Hans", "ui.language.ja", "ui.language.ko", "ui.language.en",
	"ui.graphics.original", "ui.graphics.hd", "ui.independent", "ui.apply", "ui.cancel",
	"ui.paused", "ui.release", "ui.error.unavailable"}

type prototypeCatalog map[string]map[string]string

func readPrototypeCatalog(data []byte) (prototypeCatalog, error) {
	if !utf8.Valid(data) {
		return nil, fmt.Errorf("UI catalog is not UTF-8")
	}
	r := csv.NewReader(bytes.NewReader(data))
	r.Comma, r.FieldsPerRecord = '\t', 6
	header, err := r.Read()
	if err != nil || len(header) != 6 || header[0] != "key" || strings.Join(header[1:], ",") != strings.Join(prototypeLanguages, ",") {
		return nil, fmt.Errorf("invalid UI catalog header")
	}
	c := prototypeCatalog{}
	for {
		row, err := r.Read()
		if err == io.EOF {
			break
		}
		if err != nil {
			return nil, err
		}
		if row[0] == "" || c[row[0]] != nil {
			return nil, fmt.Errorf("empty or repeated UI key: %q", row[0])
		}
		c[row[0]] = map[string]string{}
		for i, language := range prototypeLanguages {
			if strings.TrimSpace(row[i+1]) == "" {
				return nil, fmt.Errorf("missing UI translation: %s/%s", row[0], language)
			}
			c[row[0]][language] = strings.ReplaceAll(row[i+1], `\n`, "\n")
		}
	}
	for _, key := range prototypeUIKeys {
		if c[key] == nil {
			return nil, fmt.Errorf("missing UI key: %s", key)
		}
	}
	return c, nil
}

func (c prototypeCatalog) text(key, language string) string {
	if v := c[key][language]; v != "" {
		return v
	}
	if v := c[key]["en"]; v != "" {
		return v
	}
	return key
}

type prototypeFonts struct {
	base  map[string]*opentype.Font
	faces map[string]font.Face
}

func readPrototypeFonts(data []byte, catalog prototypeCatalog) (*prototypeFonts, error) {
	if fmt.Sprintf("%x", sha256.Sum256(data)) != prototypeUIFontSHA {
		return nil, fmt.Errorf("prototype UI font SHA-256 mismatch")
	}
	collection, err := opentype.ParseCollection(data)
	if err != nil {
		return nil, err
	}
	f := &prototypeFonts{base: map[string]*opentype.Font{}, faces: map[string]font.Face{}}
	for language, index := range map[string]int{"ja": 0, "ko": 1, "zh-Hans": 2, "zh-Hant": 3, "en": 3} {
		base, err := collection.Font(index)
		if err != nil {
			return nil, err
		}
		f.base[language] = base
		for key := range catalog {
			for _, ch := range catalog.text(key, language) {
				if ch == '\n' || ch == '\t' {
					continue
				}
				glyph, err := base.GlyphIndex(nil, ch)
				if err != nil || glyph == 0 {
					return nil, fmt.Errorf("missing UI glyph: %s/%s/U+%04X", language, key, ch)
				}
			}
		}
	}
	return f, nil
}

func (f *prototypeFonts) face(language string, pixels int) font.Face {
	key := fmt.Sprintf("%s/%d", language, pixels)
	if face := f.faces[key]; face != nil {
		return face
	}
	face, err := opentype.NewFace(f.base[language], &opentype.FaceOptions{Size: float64(pixels), DPI: 72, Hinting: font.HintingNone})
	must(err)
	f.faces[key] = face
	return face
}

type prototypeTextPlan struct {
	face   font.Face
	lines  []string
	dots   []image.Point
	inks   []image.Rectangle
	pixels int
}

func prototypeWrappedLines(face font.Face, text string, width int) []string {
	var lines []string
	for _, paragraph := range strings.Split(text, "\n") {
		current := ""
		for _, ch := range paragraph {
			trial := current + string(ch)
			if font.MeasureString(face, trial).Ceil() <= width || current == "" {
				current = trial
				continue
			}
			if split := strings.LastIndexAny(current, " \t"); split > 0 {
				lines = append(lines, strings.TrimSpace(current[:split]))
				current = strings.TrimLeft(current[split:], " \t") + string(ch)
			} else {
				lines = append(lines, current)
				current = string(ch)
			}
		}
		lines = append(lines, strings.TrimSpace(current))
	}
	return lines
}

func (f *prototypeFonts) plan(language, text string, rect image.Rectangle, maxPx, minPx, maxLines int) (*prototypeTextPlan, error) {
	safe := rect.Inset(4)
	for pixels := maxPx; pixels >= minPx; pixels-- {
		face := f.face(language, pixels)
		lines := []string{text}
		if maxLines > 1 {
			lines = prototypeWrappedLines(face, text, safe.Dx())
		}
		if len(lines) > maxLines {
			continue
		}
		spacing := face.Metrics().Height.Ceil()
		bounds := make([]image.Rectangle, len(lines))
		var overall image.Rectangle
		for i, line := range lines {
			b, _ := font.BoundString(face, line)
			bounds[i] = image.Rect(b.Min.X.Floor(), b.Min.Y.Floor(), b.Max.X.Ceil(), b.Max.Y.Ceil())
			overall = overall.Union(bounds[i].Add(image.Pt(0, i*spacing)))
		}
		if overall.Dy() > safe.Dy() {
			continue
		}
		p := &prototypeTextPlan{face: face, lines: lines, pixels: pixels}
		y := safe.Min.Y + (safe.Dy()-overall.Dy())/2 - overall.Min.Y
		fits := true
		for i, b := range bounds {
			at := image.Pt(safe.Min.X+(safe.Dx()-b.Dx())/2-b.Min.X, y+i*spacing)
			ink := b.Add(at)
			fits = fits && ink.In(safe)
			p.dots, p.inks = append(p.dots, at), append(p.inks, ink)
		}
		if fits {
			return p, nil
		}
	}
	return nil, fmt.Errorf("UI text does not fit %v", rect)
}

func (p *prototypeTextPlan) paint(dst *image.RGBA, foreground color.RGBA) {
	for i, line := range p.lines {
		d := font.Drawer{Dst: dst, Src: image.NewUniform(foreground), Face: p.face, Dot: fixed.P(p.dots[i].X, p.dots[i].Y)}
		d.DrawString(line)
	}
}

type displayUIPrototype struct {
	settings displaySettings
	catalog  prototypeCatalog
	fonts    *prototypeFonts
	events   []map[string]any
	texture  *ebiten.Image
	cacheKey string
}

func newDisplayUIPrototype() *displayUIPrototype {
	c, err := readPrototypeCatalog(read(*prototypeUICatalog))
	must(err)
	f, err := readPrototypeFonts(read(*prototypeUIFont), c)
	must(err)
	u := &displayUIPrototype{catalog: c, fonts: f, settings: displaySettings{current: displayOptions{"zh-Hant", "original"}}}
	// 先量測全部五語介面，載入失敗不留半個設定面板。
	for _, language := range prototypeLanguages {
		copy := u.settings
		u.settings.current.Language = language
		u.settings.draft = u.settings.current
		u.settings.phase = displayEditing
		_, err := u.canvas()
		must(err)
		u.settings = copy
	}
	return u
}

func (*displayUIPrototype) logicalMouse(x, y int) (int, int, bool) {
	return logicalMouse(x, y-prototypeToolbarHeight)
}

func prototypeAllReleased() bool {
	if !ebiten.IsFocused() || len(inpututil.AppendPressedKeys(nil)) != 0 {
		return false
	}
	for b := ebiten.MouseButton(0); b <= ebiten.MouseButtonMax; b++ {
		if ebiten.IsMouseButtonPressed(b) {
			return false
		}
	}
	return true
}

func (u *displayUIPrototype) record(g *windowGame, action string) {
	prefix := fmt.Sprintf("%s.display-%03d", g.out, len(u.events))
	native := append([]byte(nil), g.m.Indexed()...)
	must(os.WriteFile(prefix+".idx", native, 0644))
	must(os.WriteFile(prefix+".pal", g.m.DAC[:], 0644))
	event := map[string]any{"action": action, "phase": u.settings.phase,
		"current": u.settings.current, "draft": u.settings.draft, "problem": u.settings.problem,
		"step": g.m.Steps, "memory_sha256": hash(g.m.Mem), "indexed_sha256": hash(native),
		"palette_sha256": hash(g.m.DAC[:]), "registers": g.m.CPU.R, "segments": g.m.CPU.Seg,
		"ip": g.m.CPU.IP, "flags": g.m.CPU.Flags, "dos_input_count": len(g.inputs),
		"dos_mouse":    map[string]any{"x": g.d.Mouse.X, "y": g.d.Mouse.Y, "buttons": g.d.Mouse.Buttons},
		"indexed_path": prefix + ".idx", "palette_path": prefix + ".pal"}
	if g.latest != nil {
		event["presentation_rgba_sha256"] = hash(g.latest.Pix)
		event["presentation_path"] = prefix + ".png"
		savePNG(prefix+".png", g.latest)
	}
	u.events = append(u.events, event)
	dumpJSON(g.out+".display-events.json", u.events)
}

func prototypeLanguageButton(i int) image.Rectangle {
	return image.Rect(300+i*136, 348, 426+i*136, 400)
}
func prototypeGraphicsButton(i int) image.Rectangle {
	return image.Rect(300+i*344, 452, 628+i*344, 508)
}

var prototypeToolbarButton = image.Rect(14, 6, 216, 42)
var prototypeCancelButton = image.Rect(704, 620, 832, 668)
var prototypeApplyButton = image.Rect(848, 620, 976, 668)

func (u *displayUIPrototype) update(g *windowGame) bool {
	s := &u.settings
	position := image.Pt(ebiten.CursorPosition())
	click := ebiten.IsFocused() && inpututil.IsMouseButtonJustPressed(ebiten.MouseButtonLeft)
	if !s.paused() {
		if click && position.In(prototypeToolbarButton) && s.open(g.held[0] || g.held[1] || g.held[2]) {
			g.audio.setPaused(true)
			ebiten.SetCursorMode(ebiten.CursorModeVisible)
			u.record(g, "open")
			return true
		}
		return false
	}
	if s.phase == displayEditing {
		if ebiten.IsFocused() && inpututil.IsKeyJustPressed(ebiten.KeyEscape) {
			s.cancel()
			u.record(g, "cancel-escape")
		} else if click {
			for i, language := range prototypeLanguages {
				if position.In(prototypeLanguageButton(i)) {
					s.draft.Language, s.problem = language, ""
				}
			}
			for i, graphics := range []string{"original", "hd"} {
				if position.In(prototypeGraphicsButton(i)) {
					s.draft.Graphics, s.problem = graphics, ""
				}
			}
			if position.In(prototypeCancelButton) {
				s.cancel()
				u.record(g, "cancel")
			} else if position.In(prototypeApplyButton) {
				ok := s.apply(func(options displayOptions) error {
					if options.Graphics != "original" || (options.Language != "zh-Hant" && options.Language != "en") {
						return fmt.Errorf("ui.error.unavailable")
					}
					prototypeDisplayLanguage = options.Language
					g.render("")
					return nil
				})
				action := "apply-error"
				if ok {
					action = "apply"
				}
				u.record(g, action)
			}
		}
	}
	previous := s.phase
	s.released(prototypeAllReleased())
	if s.phase != previous {
		if s.phase == displayPlaying {
			g.audio.setPaused(false)
			// 畫面外工具列要保留可見游標；進入遊戲區後沿用原版游標。
			u.record(g, "resume")
		} else {
			u.record(g, "ready")
		}
	}
	return true // 放開後這一幀仍不轉送，下一個Update才恢復DOS。
}

func (u *displayUIPrototype) canvas() (*image.RGBA, error) {
	im := image.NewRGBA(image.Rect(0, 0, 1280, 800+prototypeToolbarHeight))
	fill := func(rect image.Rectangle, c color.RGBA) {
		imagedraw.Draw(im, rect, image.NewUniform(c), image.Point{}, imagedraw.Src)
	}
	white, dark := color.RGBA{238, 240, 236, 255}, color.RGBA{38, 44, 43, 255}
	language := u.settings.current.Language
	label := func(rect image.Rectangle, key string, max, min, lines int, foreground color.RGBA) error {
		p, err := u.fonts.plan(language, u.catalog.text(key, language), rect, max, min, lines)
		if err == nil {
			p.paint(im, foreground)
		}
		return err
	}
	button := func(rect image.Rectangle, key string, selected bool) error {
		c := color.RGBA{224, 222, 207, 255}
		if selected {
			c = color.RGBA{173, 200, 179, 255}
		}
		fill(rect, c)
		return label(rect, key, 24, 18, 1, dark)
	}
	fill(image.Rect(0, 0, 1280, prototypeToolbarHeight), color.RGBA{38, 44, 43, 255})
	fill(prototypeToolbarButton, color.RGBA{65, 81, 73, 255})
	if err := label(prototypeToolbarButton, "ui.settings", 22, 18, 1, white); err != nil {
		return nil, err
	}
	status := u.catalog.text("ui.language."+language, language) + " / " + u.catalog.text("ui.graphics."+u.settings.current.Graphics, language)
	if u.settings.phase == displayResuming {
		status += "  " + u.catalog.text("ui.release", language)
	}
	p, err := u.fonts.plan(language, status, image.Rect(240, 6, 1264, 42), 22, 18, 1)
	if err != nil {
		return nil, err
	}
	p.paint(im, white)
	if u.settings.phase == displayPlaying || u.settings.phase == displayResuming {
		return im, nil
	}
	fill(image.Rect(0, prototypeToolbarHeight, 1280, 848), color.RGBA{12, 16, 15, 180})
	fill(image.Rect(276, 164, 1004, 684), color.RGBA{244, 239, 224, 255})
	for _, item := range []struct {
		rect            image.Rectangle
		key             string
		max, min, lines int
	}{{image.Rect(300, 184, 980, 232), "ui.settings", 28, 24, 1},
		{image.Rect(300, 236, 980, 304), "ui.description", 22, 18, 2},
		{image.Rect(300, 310, 980, 344), "ui.language", 22, 18, 1},
		{image.Rect(300, 414, 980, 448), "ui.graphics", 22, 18, 1},
		{image.Rect(300, 516, 980, 550), "ui.independent", 20, 18, 1}} {
		if err := label(item.rect, item.key, item.max, item.min, item.lines, dark); err != nil {
			return nil, err
		}
	}
	for i, language := range prototypeLanguages {
		if err := button(prototypeLanguageButton(i), "ui.language."+language, u.settings.draft.Language == language); err != nil {
			return nil, err
		}
	}
	for i, graphics := range []string{"original", "hd"} {
		if err := button(prototypeGraphicsButton(i), "ui.graphics."+graphics, u.settings.draft.Graphics == graphics); err != nil {
			return nil, err
		}
	}
	key := "ui.paused"
	if u.settings.phase == displayOpening {
		key = "ui.release"
	} else if u.settings.problem != "" {
		key = u.settings.problem
	}
	if err := label(image.Rect(300, 556, 980, 606), key, 20, 18, 2, dark); err != nil {
		return nil, err
	}
	if err := button(prototypeCancelButton, "ui.cancel", false); err != nil {
		return nil, err
	}
	if err := button(prototypeApplyButton, "ui.apply", true); err != nil {
		return nil, err
	}
	return im, nil
}

func (u *displayUIPrototype) draw(screen *ebiten.Image) {
	if !u.settings.paused() {
		_, _, inside := u.logicalMouse(ebiten.CursorPosition())
		mode := ebiten.CursorModeVisible
		if inside {
			mode = ebiten.CursorModeHidden
		}
		ebiten.SetCursorMode(mode)
	}
	key := fmt.Sprintf("%d/%s/%s/%s/%s/%s", u.settings.phase, u.settings.current.Language,
		u.settings.current.Graphics, u.settings.draft.Language, u.settings.draft.Graphics, u.settings.problem)
	if u.texture == nil || key != u.cacheKey {
		im, err := u.canvas()
		must(err)
		if u.texture == nil {
			u.texture = ebiten.NewImage(1280, 848)
		}
		u.texture.WritePixels(im.Pix)
		u.cacheKey = key
	}
	screen.DrawImage(u.texture, nil)
}

func (u *displayUIPrototype) status() map[string]any {
	return map[string]any{"phase": u.settings.phase, "paused": u.settings.paused(), "current": u.settings.current,
		"draft": u.settings.draft, "problem": u.settings.problem, "event_count": len(u.events)}
}
