package main

// 規格060 DRAFT：原文觀測只由隔離組裝器連結，不持有譯文或字模。
import (
	"bytes"
	"flag"
	"fmt"
	"image"
	"maps"
	"reflect"
	"slices"

	"github.com/wicanr2/dosgolem/overlay"
)

var draftNativeCapture = flag.Bool("draft-native-capture", false, "規格060隔離原型：保存完整原文觀測")

const draftNativeMaxItems = 256
const draftNativeMaxCost = 32 << 20

type nativeDialogCell struct {
	StartDI    uint16 `json:"start_di"`
	EndDI      uint16 `json:"end_di"`
	StartES    uint16 `json:"start_es"`
	EndES      uint16 `json:"end_es"`
	StartKnown bool   `json:"start_known"`
	EndKnown   bool   `json:"end_known"`
}

type nativeObservation struct {
	kind           string
	step           uint64
	ink            image.Rectangle
	cursor         image.Rectangle
	canvas, buffer []byte
	after          map[int]byte
	stringRun      *stringRun
	dialogRun      *dialogRun
	dialogCells    []nativeDialogCell
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
	sample                   func() nativeSurfaces
	coalesced                int
	evictedNonvisible        int
	evictedVisible           int
	evictedUnclassified      int
	pendingDialog            *dialogRun
	pendingCells             []nativeDialogCell
}

// 只記錄原版逐字、零結尾配對的游標，不從墨跡或連續字串猜補字格。
func (j *nativeJournal) observeDialogCursor(r *dialogRun, value byte, di, es uint16) {
	if !j.enabled {
		return
	}
	if r == nil || len(r.chars) == 0 || len(r.chars) > 4096 {
		j.pendingDialog, j.pendingCells = nil, nil
		return
	}
	if j.pendingDialog != r {
		j.pendingDialog, j.pendingCells = r, nil
	}
	for len(j.pendingCells) < len(r.chars) {
		j.pendingCells = append(j.pendingCells, nativeDialogCell{})
	}
	i := len(r.chars) - 1
	if r.contig || r.chars[i].contig {
		return
	}
	c := &j.pendingCells[i]
	if value != 0 && r.readPos%2 == 1 {
		*c = nativeDialogCell{StartDI: di, StartES: es, StartKnown: true}
	} else if value == 0 && r.readPos%2 == 0 && c.StartKnown {
		c.EndDI, c.EndES, c.EndKnown = di, es, true
	}
}

type nativeSurfaces struct {
	canvas, buffer, indexed, palette []byte
	mode                             byte
}

func (f nativeSurfaces) valid() bool {
	return len(f.canvas) == 64000 && len(f.buffer) == 64000 && len(f.indexed) == 64000 && len(f.palette) == 768
}

func (f nativeSurfaces) visible(o *nativeObservation) bool {
	if f.mode != 0x13 || !o.visible(f.canvas, f.buffer, f.indexed) {
		return false
	}
	return o.fixed == nil || o.fixed.paletteSHA == "" || hash(f.palette) == o.fixed.paletteSHA
}

// 完整原文與原版樣式相同的重印只保留最近事件；不比較譯文或目標字模。
func nativeSameSource(a, b *nativeObservation) bool {
	if a.stringRun == nil && a.dialogRun == nil && a.fixed == nil && len(a.seaRuns) == 0 {
		return false
	}
	if a.kind != b.kind || a.ink != b.ink || a.cursor != b.cursor || !maps.Equal(a.after, b.after) {
		return false
	}
	if (a.stringRun == nil) != (b.stringRun == nil) || (a.dialogRun == nil) != (b.dialogRun == nil) ||
		(a.fixed == nil) != (b.fixed == nil) || len(a.seaRuns) != len(b.seaRuns) {
		return false
	}
	if a.stringRun != nil {
		x, y := *a.stringRun, *b.stringRun
		x.start, x.last, y.start, y.last = 0, 0, 0, 0
		if !reflect.DeepEqual(x, y) {
			return false
		}
	}
	if a.dialogRun != nil {
		x, y := *a.dialogRun, *b.dialogRun
		x.start, x.last, y.start, y.last = 0, 0, 0, 0
		if !reflect.DeepEqual(x, y) || !slices.Equal(a.dialogCells, b.dialogCells) {
			return false
		}
	}
	for i := range a.seaRuns {
		x, y := *a.seaRuns[i], *b.seaRuns[i]
		x.last, y.last = 0, 0
		if !reflect.DeepEqual(x, y) {
			return false
		}
	}
	if a.fixed != nil {
		x, y := *a.fixed, *b.fixed
		x.expired, y.expired = false, false
		if !reflect.DeepEqual(x, y) {
			return false
		}
	}
	return true
}

func (j *nativeJournal) remove(index int) {
	j.cost -= j.items[index].cost
	copy(j.items[index:], j.items[index+1:])
	j.items[len(j.items)-1] = nil
	j.items = j.items[:len(j.items)-1]
}

// 固定欄位只存原版鍵、前後像素及原版樣式，不保存舊譯文或舊字模。
type nativeFixed struct {
	id                         string
	safe                       image.Rectangle
	before, after              []byte
	foreground, shade, accent  byte
	shadow                     image.Point
	layered, vga, expired      bool
	buttonGuard                bool
	mouseRule                  string
	guard                      image.Rectangle
	fingerprint                image.Rectangle
	fingerprintSHA, paletteSHA string
}

func (j *nativeJournal) captureFixed(def nativeFixed, before, after, canvas []byte, step uint64) bool {
	if !j.enabled {
		return false
	}
	if def.id == "" || len(def.id) > 256 || len(before) != 64000 || len(after) != 64000 || len(canvas) != 64000 ||
		def.safe.Empty() || !def.safe.In(image.Rect(0, 0, 320, 200)) ||
		(!def.fingerprint.Empty() && (!def.fingerprint.In(image.Rect(0, 0, 320, 200)) ||
			!def.safe.In(def.fingerprint) || len(def.fingerprintSHA) != 64 || len(def.paletteSHA) != 64)) {
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
func (j *nativeJournal) expireFixed(canvas, indexed []byte, mode byte, palette ...[]byte) {
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
		} else if !f.fingerprint.Empty() && hash(rectBytes(source, f.fingerprint)) != f.fingerprintSHA {
			f.expired = true
		} else if f.paletteSHA != "" && (len(palette) != 1 || hash(palette[0]) != f.paletteSHA) {
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

// 規格034及bake_static_masks.py的原版指紋、紋理補回與選色；不讀取中文字模。
func (j *nativeJournal) observeStatics(items []*staticItem, canvas, indexed, palette []byte, step uint64, mode byte) {
	if !j.enabled || mode != 0x13 || len(canvas) != 64000 || len(indexed) != 64000 || len(palette) != 768 {
		return
	}
	for _, it := range items {
		if it == nil || !it.nativeSource || it.fp.Empty() || !it.fp.In(image.Rect(0, 0, 320, 200)) ||
			it.band.Empty() || !it.band.In(it.fp) || hash(rectBytes(indexed, it.fp)) != it.sha {
			continue
		}
		active := false
		for _, o := range j.items {
			if o.fixed != nil && o.fixed.vga && o.fixed.id == it.id && o.fixed.paletteSHA == hash(palette) && o.visible(canvas, nil, indexed) {
				active = true
				break
			}
		}
		if active {
			continue
		}
		lum := func(v byte) int { return int(palette[int(v)*3]) + int(palette[int(v)*3+1]) + int(palette[int(v)*3+2]) }
		var ink byte
		if it.nativePrimary != nil {
			ink = *it.nativePrimary
		} else {
			counts := map[byte]int{}
			var order []byte
			for _, v := range rectBytes(indexed, it.band) {
				if counts[v] == 0 {
					order = append(order, v)
				}
				counts[v]++
			}
			found := false
			for _, v := range order {
				if counts[v] >= 10 && (!found || lum(v) < lum(ink)) {
					ink, found = v, true
				}
			}
			if !found {
				j.rejected++
				continue
			}
		}
		isText := func(v byte) bool {
			if it.inkSet != nil {
				return it.inkSet[v]
			}
			return lum(v) < 122
		}
		clean := bytes.Clone(indexed)
		for y := it.band.Min.Y; y < it.band.Max.Y; y++ {
			for x := it.band.Min.X; x < it.band.Max.X; x++ {
				if !isText(indexed[y*320+x]) {
					continue
				}
			search:
				for dx := 1; dx < it.band.Dx(); dx++ {
					for _, nx := range []int{x - dx, x + dx} {
						if nx >= it.band.Min.X && nx < it.band.Max.X && !isText(indexed[y*320+nx]) {
							clean[y*320+x] = indexed[y*320+nx]
							break search
						}
					}
				}
			}
		}
		j.captureFixed(nativeFixed{id: it.id, safe: it.band, foreground: ink, vga: true,
			fingerprint: it.fp, fingerprintSHA: it.sha, paletteSHA: hash(palette)}, clean, indexed, canvas, step)
	}
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
	// 滿載時保留當次可見來源；回收或合併都維持其餘完成事件的相對順序。
	var current nativeSurfaces
	if j.sample != nil && (len(j.items) >= draftNativeMaxItems || j.cost+o.cost > draftNativeMaxCost) {
		current = j.sample()
		if !current.valid() {
			j.rejected++
			return false
		}
		for i := len(j.items) - 1; i >= 0; i-- {
			if nativeSameSource(j.items[i], o) {
				j.remove(i)
				j.coalesced++
			}
		}
	}
	for len(j.items) > 0 && (len(j.items) >= draftNativeMaxItems || j.cost+o.cost > draftNativeMaxCost) {
		victim := 0
		if j.sample == nil {
			j.evictedUnclassified++
		} else {
			victim = -1
			for i, old := range j.items {
				if !current.visible(old) {
					victim = i
					break
				}
			}
			if victim < 0 {
				victim = 0
				j.evictedVisible++
			} else {
				j.evictedNonvisible++
			}
		}
		j.remove(victim)
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
	var cells []nativeDialogCell
	if j.pendingDialog == r && len(j.pendingCells) == len(r.chars) {
		cells = slices.Clone(j.pendingCells)
	}
	j.pendingDialog, j.pendingCells = nil, nil
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
	cost := (len(r.firstOld)+len(r.lastText)+len(after))*32 + len(r.chars)*64 + len(cells)*16
	for _, ch := range r.chars {
		cost += len(ch.colors) * 32
	}
	return j.add(&nativeObservation{kind: "dialog", step: step, ink: ink, after: after,
		dialogRun: cloneNativeDialog(r), dialogCells: cells, cost: cost}, canvas, nil)
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
		return !f.expired && len(source) == 64000 && bytes.Equal(rectBytes(source, f.safe), f.after) &&
			(f.fingerprint.Empty() || hash(rectBytes(source, f.fingerprint)) == f.fingerprintSHA)
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
			row["dialog_cells"] = o.dialogCells
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
			if !f.fingerprint.Empty() {
				row["fingerprint"], row["fingerprint_sha256"], row["source_palette_sha256"] = f.fingerprint, f.fingerprintSHA, f.paletteSHA
			}
		}
		items = append(items, row)
	}
	return map[string]any{"kind": "DRAFT-native-observations-not-language-rebuild", "items": items,
		"cost": j.cost, "accepted": j.accepted, "rejected": j.rejected, "evicted_by_limit": j.lost,
		"coalesced_reprints": j.coalesced, "evicted_nonvisible": j.evictedNonvisible,
		"evicted_visible": j.evictedVisible, "evicted_unclassified": j.evictedUnclassified,
		"max_items": draftNativeMaxItems, "max_cost": draftNativeMaxCost, "video_mode": mode}
}
