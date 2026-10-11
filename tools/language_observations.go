package main

// 規格060 DRAFT：原文觀測只由隔離組裝器連結，不持有譯文或字模。
import (
	"bytes"
	"flag"
	"fmt"
	"image"
	"maps"
	"slices"

	"github.com/wicanr2/dosgolem/overlay"
)

var draftNativeCapture = flag.Bool("draft-native-capture", false, "規格060隔離原型：保存完整原文觀測")

const draftNativeMaxItems = 256
const draftNativeMaxCost = 32 << 20

type nativeObservation struct {
	kind           string
	step           uint64
	ink            image.Rectangle
	cursor         image.Rectangle
	canvas, buffer []byte
	after          map[int]byte
	stringRun      *stringRun
	dialogRun      *dialogRun
	seaRuns        []*seaEvent
	fixed          *nativeFixed
	cost           int
}

type nativeJournal struct {
	enabled                  bool
	items                    []*nativeObservation
	cost                     int
	cursor                   image.Rectangle
	buttons                  bool
	accepted, rejected, lost int
}

// 固定欄位只存原版鍵、前後像素及原版樣式，不保存舊譯文或舊字模。
type nativeFixed struct {
	id                        string
	safe                      image.Rectangle
	before, after             []byte
	foreground, shade, accent byte
	shadow                    image.Point
	layered, vga, expired     bool
	buttonGuard               bool
	mouseRule                 string
	guard                     image.Rectangle
}

func (j *nativeJournal) captureFixed(def nativeFixed, before, after, canvas []byte, step uint64) bool {
	if !j.enabled {
		return false
	}
	if def.id == "" || len(def.id) > 256 || len(before) != 64000 || len(after) != 64000 || len(canvas) != 64000 ||
		def.safe.Empty() || !def.safe.In(image.Rect(0, 0, 320, 200)) {
		j.rejected++
		return false
	}
	changed := map[int]byte{}
	for y := def.safe.Min.Y; y < def.safe.Max.Y; y++ {
		for x := def.safe.Min.X; x < def.safe.Max.X; x++ {
			i := y*320 + x
			if before[i] != after[i] {
				changed[i] = after[i]
			}
		}
	}
	if len(changed) == 0 {
		j.rejected++
		return false
	}
	def.before, def.after = rectBytes(before, def.safe), rectBytes(after, def.safe)
	def.expired = false
	o := &nativeObservation{kind: "fixed", step: step, ink: def.safe, after: changed, fixed: &def,
		cost: len(def.id) + len(def.before) + len(def.after) + len(changed)*32 + 256}
	if !j.add(o, canvas, nil) {
		return false
	}
	for _, old := range j.items {
		if old != o && old.fixed != nil && old.fixed.id == def.id {
			old.fixed.expired = true
		}
	}
	return true
}

// 當幀撤銷是單向的；之後像素碰巧相同不會重新作用，必須有新的已驗原版事件。
func (j *nativeJournal) expireFixed(canvas, indexed []byte, mode byte) {
	if !j.enabled {
		return
	}
	for _, o := range j.items {
		f := o.fixed
		if f == nil || f.expired {
			continue
		}
		source := canvas
		if f.vga {
			source = indexed
		}
		if mode != 0x13 || len(source) != 64000 || !bytes.Equal(rectBytes(source, f.safe), f.after) {
			f.expired = true
		}
	}
}

func draftFixedPatch(j *nativeJournal, def nativeFixed, before, after []byte, step uint64) (*overlay.Patch, error) {
	p, err := overlay.NewPatch(before, after, 320, 200, def.safe)
	if err == nil {
		j.captureFixed(def, before, after, after, step)
	}
	return p, err
}

func draftFixedMenu(l *menuLine) nativeFixed {
	return nativeFixed{id: l.id, safe: l.safe(), foreground: 254}
}

func draftFixedDifficulty(l *difficultyLine) nativeFixed {
	f := nativeFixed{id: l.id, safe: l.safe, foreground: 254, buttonGuard: l.card || l.nation}
	if l.card {
		f.mouseRule, f.guard = "point", l.cursorGuard
	}
	if l.prompt {
		f.foreground, f.shade, f.shadow = 68, 47, image.Pt(4, 0)
	}
	if l.nationCard {
		f.foreground, f.shade, f.shadow = l.cardColor, 0, image.Pt(4, 0)
		f.mouseRule, f.guard = "overlap", l.safe
	}
	if l.thirdCard {
		f.foreground, f.shade, f.shadow = 14, 0, image.Pt(4, 0)
	}
	return f
}

func draftFixedCaption(c *buildCaption) nativeFixed {
	return nativeFixed{id: c.id, safe: c.safe, foreground: 14, shade: 47, shadow: image.Pt(4, 4), buttonGuard: true, mouseRule: "target-ink"}
}

func draftFixedTitle(t *optionsTitle) nativeFixed {
	return nativeFixed{id: t.id, safe: image.Rect(65, 44, 253, 59), foreground: 68, shade: 47, shadow: image.Pt(4, 4), buttonGuard: true, mouseRule: "target-ink"}
}

func draftFixedRow(r *optionRow, i int) nativeFixed {
	return nativeFixed{id: r.id, safe: optionRowSafe(i), foreground: 68, shade: 47, shadow: image.Pt(4, 4), buttonGuard: true, mouseRule: "target-ink"}
}

func draftFixedRetire(r *retireField) nativeFixed {
	return nativeFixed{id: r.id, safe: r.rect, foreground: 68, shade: 47, shadow: image.Pt(4, 4), buttonGuard: true, mouseRule: "target-ink"}
}

func draftFixedLayered(id string, safe image.Rectangle) nativeFixed {
	return nativeFixed{id: id, safe: safe, foreground: 68, shade: 47, accent: 149, layered: true, buttonGuard: true}
}

func draftFixedStaticPatch(j *nativeJournal, it *staticItem, before, after, canvas []byte, step uint64) (*overlay.Patch, error) {
	p, err := overlay.NewPatch(before, after, 320, 200, it.band)
	if err == nil && !it.on {
		j.captureFixed(nativeFixed{id: it.id, safe: it.band, foreground: it.ink, vga: true}, before, after, canvas, step)
	}
	return p, err
}

func cloneNativeString(r *stringRun) *stringRun {
	if r == nil {
		return nil
	}
	c := *r
	c.text = bytes.Clone(r.text)
	c.boxes = slices.Clone(r.boxes)
	c.colors = maps.Clone(r.colors)
	c.firstOld, c.lastVal = maps.Clone(r.firstOld), maps.Clone(r.lastVal)
	c.retainedCursor, c.retainedSegments = slices.Clone(r.retainedCursor), slices.Clone(r.retainedSegments)
	c.charColor = make([]map[byte]image.Rectangle, len(r.charColor))
	for i, colors := range r.charColor {
		c.charColor[i] = maps.Clone(colors)
	}
	return &c
}

func cloneNativeDialog(r *dialogRun) *dialogRun {
	if r == nil {
		return nil
	}
	c := *r
	c.chars = slices.Clone(r.chars)
	for i := range c.chars {
		c.chars[i].colors = maps.Clone(r.chars[i].colors)
	}
	c.firstOld, c.lastText = maps.Clone(r.firstOld), maps.Clone(r.lastText)
	return &c
}

func cloneNativeSea(r *seaEvent) *seaEvent {
	if r == nil {
		return nil
	}
	c := *r
	c.raw = bytes.Clone(r.raw)
	c.firstOld, c.lastVal = maps.Clone(r.firstOld), maps.Clone(r.lastVal)
	c.colors = maps.Clone(r.colors)
	return &c
}

func validNativePixels(before, after map[int]byte) bool {
	if len(after) == 0 || len(after) > 64000 || len(before) > 64000 {
		return false
	}
	for i := range before {
		if i < 0 || i >= 64000 {
			return false
		}
	}
	for i := range after {
		if i < 0 || i >= 64000 {
			return false
		}
		if _, ok := before[i]; !ok {
			return false
		}
	}
	return true
}

func (j *nativeJournal) add(o *nativeObservation, canvas, buffer []byte) bool {
	if !j.enabled {
		return false
	}
	if len(canvas) != 64000 || o.ink.Empty() || !o.ink.In(image.Rect(0, 0, 320, 200)) ||
		(len(buffer) != 0 && len(buffer) != 64000) || o.cost > draftNativeMaxCost {
		j.rejected++
		return false
	}
	o.canvas, o.buffer = bytes.Clone(canvas), bytes.Clone(buffer)
	o.cursor = j.cursor
	o.cost += len(o.canvas) + len(o.buffer) + 1024
	if o.cost > draftNativeMaxCost {
		j.rejected++
		return false
	}
	// 保留完成事件的時間順序，不以矩形相交猜測原版是否已撤銷整段文字。
	for len(j.items) > 0 && (len(j.items) >= draftNativeMaxItems || j.cost+o.cost > draftNativeMaxCost) {
		j.cost -= j.items[0].cost
		j.items[0] = nil
		j.items = j.items[1:]
		j.lost++
	}
	j.items = append(j.items, o)
	j.cost += o.cost
	j.accepted++
	return true
}

func (j *nativeJournal) captureString(r *stringRun, canvas, buffer []byte, step uint64) bool {
	if !j.enabled || r == nil {
		return false
	}
	if len(r.text) == 0 || len(r.text) > 4096 || len(r.text) != len(r.boxes) ||
		len(r.charColor) > 4096 || len(r.retainedCursor) > 4096 || len(r.retainedSegments) > 4096 ||
		!validNativePixels(r.firstOld, r.lastVal) || ((r.buf2 || r.mixed) && len(buffer) != 64000) {
		j.rejected++
		return false
	}
	kind := "string"
	if r.buf2 || r.mixed {
		kind = "string-map"
	} else {
		buffer = nil
	}
	ink := r.outlineInk
	for _, box := range r.boxes {
		ink = ink.Union(box)
	}
	cost := len(r.text) + len(r.boxes)*32 + (len(r.firstOld)+2*len(r.lastVal))*32 + len(r.retainedCursor)*16 + len(r.retainedSegments)*2
	for _, colors := range r.charColor {
		cost += len(colors) * 48
	}
	return j.add(&nativeObservation{kind: kind, step: step, ink: ink, after: maps.Clone(r.lastVal),
		stringRun: cloneNativeString(r), cost: cost}, canvas, buffer)
}

func (j *nativeJournal) captureDialog(r *dialogRun, canvas []byte, step uint64) bool {
	if !j.enabled || r == nil {
		return false
	}
	if r.readPos%2 != 0 || len(r.chars) == 0 || len(r.chars) > 4096 || len(r.lastText) > 64000 || len(canvas) != 64000 {
		j.rejected++
		return false
	}
	var ink image.Rectangle
	for _, ch := range r.chars {
		ink = ink.Union(ch.box)
	}
	after := map[int]byte{}
	for i, alive := range r.lastText {
		if alive {
			if i < 0 || i >= 64000 {
				j.rejected++
				return false
			}
			after[i] = canvas[i]
		}
	}
	if !validNativePixels(r.firstOld, after) {
		j.rejected++
		return false
	}
	cost := (len(r.firstOld)+len(r.lastText)+len(after))*32 + len(r.chars)*64
	for _, ch := range r.chars {
		cost += len(ch.colors) * 32
	}
	return j.add(&nativeObservation{kind: "dialog", step: step, ink: ink, after: after,
		dialogRun: cloneNativeDialog(r), cost: cost}, canvas, nil)
}

func (j *nativeJournal) captureSea(r *seaEvent, canvas []byte, step uint64) bool {
	if !j.enabled || r == nil || (len(r.raw) == 2 && r.raw[1] == 0) {
		return false // 逐字頂列待完整原文序列到齊才保存。
	}
	return j.captureSeaRuns([]*seaEvent{r}, canvas, step)
}

func (j *nativeJournal) captureSeaRuns(runs []*seaEvent, canvas []byte, step uint64) bool {
	if !j.enabled {
		return false
	}
	if len(runs) == 0 || len(runs) > 128 {
		j.rejected++
		return false
	}
	var ink image.Rectangle
	after := map[int]byte{}
	clones, cost := make([]*seaEvent, len(runs)), 0
	for n, r := range runs {
		if r == nil || len(r.raw) == 0 || len(r.raw) > 4096 || !validNativePixels(r.firstOld, r.lastVal) {
			j.rejected++
			return false
		}
		ink = ink.Union(r.bbox)
		maps.Copy(after, r.lastVal)
		clones[n] = cloneNativeSea(r)
		cost += len(r.raw) + (len(r.firstOld)+len(r.lastVal))*32 + len(r.colors)*32
	}
	cost += len(after) * 32
	kind := "sea-panel"
	if ink.In(seaBarRect) {
		kind = "sea-bar"
	}
	return j.add(&nativeObservation{kind: kind, step: step, ink: ink, after: after, seaRuns: clones, cost: cost}, canvas, nil)
}

func (o *nativeObservation) visible(canvas, buffer []byte, indexed ...[]byte) bool {
	if f := o.fixed; f != nil {
		source := canvas
		if f.vga {
			if len(indexed) != 1 {
				return false
			}
			source = indexed[0]
		}
		return !f.expired && len(source) == 64000 && bytes.Equal(rectBytes(source, f.safe), f.after)
	}
	if o.stringRun != nil && o.stringRun.mixed {
		return false // 混合位置未建立重建契約，保留原文及證據。
	}
	current := canvas
	if o.kind == "string-map" {
		current = buffer
	}
	if len(current) != 64000 || len(o.after) == 0 {
		return false
	}
	for i, value := range o.after {
		if i < 0 || i >= len(current) || current[i] != value {
			return false
		}
	}
	return true
}

func (j *nativeJournal) export(canvas, buffer []byte, mode byte, indexed ...[]byte) map[string]any {
	var items []map[string]any
	for _, o := range j.items {
		row := map[string]any{"kind": o.kind, "step": o.step, "ink": o.ink, "visible": mode == 0x13 && o.visible(canvas, buffer, indexed...),
			"canvas_sha256": hash(o.canvas), "source_pixels": len(o.after), "after_pixels": o.after, "cost": o.cost, "cursor": o.cursor}
		if r := o.stringRun; r != nil {
			row["text"], row["source_base"], row["boxes"], row["colors"] = string(r.text), r.base, r.boxes, r.colors
			row["raw"] = r.text // JSON以base64保存原始byte，不能由UTF-8顯示文字反推。
			row["outline"], row["outline_color"], row["outline_ink"] = r.outline, r.outlineC, r.outlineInk
			row["map"], row["mixed"], row["character_colors"] = r.buf2, r.mixed, r.charColor
			row["retained_cursor"], row["retained_segments"] = r.retainedCursor, r.retainedSegments
			row["cargo_role"], row["cargo_source_base"], row["cargo_text"] = r.cargo.role, r.cargo.base, r.cargo.text
		}
		if r := o.dialogRun; r != nil {
			var text []byte
			var chars []map[string]any
			for _, ch := range r.chars {
				text = append(text, ch.c)
				chars = append(chars, map[string]any{"byte": ch.c, "box": ch.box, "colors": ch.colors,
					"contiguous": ch.contig, "prefix_continuation": ch.prefixContinuation})
			}
			row["text"], row["source_base"], row["characters"] = string(text), r.base, chars
			row["raw"] = text
			row["shadow_written"], row["other_writes"] = r.shadowWritten, r.others
		}
		if len(o.seaRuns) > 0 {
			var text []byte
			var runs []map[string]any
			for _, r := range o.seaRuns {
				text = append(text, bytes.TrimRight(r.raw, "\x00")...)
				runs = append(runs, map[string]any{"raw": r.raw, "box": r.bbox, "colors": r.colors})
			}
			row["text"], row["runs"] = string(text), runs
		}
		if f := o.fixed; f != nil {
			row["text"], row["id"], row["safe"] = f.id, f.id, f.safe
			row["surface"], row["expired"] = "canvas", f.expired
			if f.vga {
				row["surface"] = "vga"
			}
			row["before_safe"], row["after_safe"] = f.before, f.after
			row["foreground"], row["shade"], row["accent"] = f.foreground, f.shade, f.accent
			row["shadow_offset"], row["layered"], row["mouse_rule"], row["cursor_guard"] = f.shadow, f.layered, f.mouseRule, f.guard
			row["identity_basis"] = fmt.Sprintf("reviewed native output / %s", f.id)
		}
		items = append(items, row)
	}
	return map[string]any{"kind": "DRAFT-native-observations-not-language-rebuild", "items": items,
		"cost": j.cost, "accepted": j.accepted, "rejected": j.rejected, "evicted_by_limit": j.lost,
		"max_items": draftNativeMaxItems, "max_cost": draftNativeMaxCost, "video_mode": mode}
}
