package main

// 下列為觀測資料結構的單元fixture，不作原版行為或同狀態證據。
import (
	"bytes"
	"image"
	"testing"
)

func nativeStringFixture() (*stringRun, []byte) {
	i := 20*320 + 30
	canvas := make([]byte, 64000)
	canvas[i] = 68
	r := &stringRun{base: 1234, next: 1235, start: 10, last: 20, text: []byte("A"),
		boxes: []image.Rectangle{image.Rect(30, 20, 31, 21)}, colors: map[byte]int{68: 1},
		firstOld: map[int]byte{i: 9}, lastVal: map[int]byte{i: 68},
		charColor:      []map[byte]image.Rectangle{{68: image.Rect(30, 20, 31, 21)}},
		retainedCursor: []image.Point{image.Pt(30, 25)}, retainedSegments: []uint16{0x1234},
		cargo: cargoProof{text: "A", role: "header", base: 1234}, outline: true, outlineC: 47,
		outlineInk: image.Rect(30, 20, 32, 22), keyColor: 149, keyNext: 68}
	return r, canvas
}

func TestNativeStaticWithoutGlyphs(t *testing.T) {
	canvas := bytes.Repeat([]byte{1}, 64000)
	indexed := bytes.Clone(canvas)
	palette := bytes.Repeat([]byte{63}, 768)
	palette[0], palette[1], palette[2] = 0, 0, 0
	for x := 14; x < 26; x++ {
		indexed[14*320+x], indexed[15*320+x] = 254, 254
	}
	primary := byte(254)
	it := &staticItem{id: "native-static", fp: image.Rect(10, 10, 50, 20), band: image.Rect(12, 12, 40, 18),
		nativeSource: true, nativePrimary: &primary, inkSet: map[byte]bool{254: true, 0: true, 253: true}}
	it.sha = hash(rectBytes(indexed, it.fp))
	j := &nativeJournal{enabled: true}
	j.observeStatics([]*staticItem{it}, canvas, indexed, palette, 1, 0x13)
	if j.accepted != 1 || len(j.items) != 1 || j.items[0].fixed.foreground != 254 ||
		j.items[0].fixed.before[(14-12)*28+2] != 1 || !j.items[0].visible(canvas, nil, indexed) {
		t.Fatal("fontless static source or native color not preserved")
	}
	j.expireFixed(canvas, indexed, 0x13, palette)
	j.observeStatics([]*staticItem{it}, canvas, indexed, palette, 2, 0x13)
	if j.accepted != 1 || j.items[0].fixed.expired {
		t.Fatal("stable native signature recorded repeatedly or expired")
	}
	indexed[10*320+10] = 2 // 指紋矩形改變，文字帶仍完全相同。
	j.expireFixed(canvas, indexed, 0x13, palette)
	j.observeStatics([]*staticItem{it}, canvas, indexed, palette, 3, 0x13)
	if !j.items[0].fixed.expired || j.accepted != 1 || j.items[0].visible(canvas, nil, indexed) {
		t.Fatal("unchanged text band bypassed native fingerprint")
	}
	indexed[10*320+10] = 1
	j.observeStatics([]*staticItem{it}, canvas, indexed, palette, 4, 0x13)
	if j.accepted != 2 || j.items[1].fixed.expired || !j.items[0].fixed.expired {
		t.Fatal("fresh complete signature did not create a new native observation")
	}
	palette[3]--
	j.expireFixed(canvas, indexed, 0x13, palette)
	if !j.items[1].fixed.expired {
		t.Fatal("native palette change did not expire static erasure")
	}
	it.nativeSource = false
	j.observeStatics([]*staticItem{it}, canvas, indexed, palette, 5, 0x13)
	if j.accepted != 2 {
		t.Fatal("invalid original source accepted")
	}
}

func TestNativeStaticCommonColorMatchesBaker(t *testing.T) {
	canvas := bytes.Repeat([]byte{1}, 64000)
	indexed := bytes.Clone(canvas)
	palette := bytes.Repeat([]byte{63}, 768)
	for _, v := range []int{2, 3, 4} {
		for c := 0; c < 3; c++ {
			palette[v*3+c] = 0
		}
	}
	// 兩個同亮度常見色維持掃描先後；最先出現的4只有一個像素，不得入選。
	indexed[12*320+12] = 4
	for x := 13; x < 25; x++ {
		indexed[14*320+x], indexed[15*320+x] = 3, 2
	}
	it := &staticItem{id: "native-credit", fp: image.Rect(10, 10, 50, 20), band: image.Rect(12, 12, 40, 18), nativeSource: true}
	it.sha = hash(rectBytes(indexed, it.fp))
	j := &nativeJournal{enabled: true}
	j.observeStatics([]*staticItem{it}, canvas, indexed, palette, 1, 0x13)
	if j.accepted != 1 || j.items[0].fixed.foreground != 3 {
		t.Fatal("native common color differs from stable baker selection")
	}
	quiet := &nativeJournal{}
	quiet.observeStatics([]*staticItem{it}, canvas, indexed, palette, 1, 0x13)
	j.observeStatics([]*staticItem{it}, canvas[:1], indexed, palette, 2, 0x13)
	j.observeStatics([]*staticItem{it}, canvas, indexed, palette, 2, 0x12)
	if quiet.accepted != 0 || j.accepted != 1 {
		t.Fatal("disabled capture or invalid frame recorded a static source")
	}
}

func TestDraftFixedSnapshotsAndOneWayExpiry(t *testing.T) {
	before := bytes.Repeat([]byte{1}, 64000)
	after := bytes.Clone(before)
	safe := image.Rect(20, 20, 50, 40)
	i := 21*320 + 21
	after[i] = 68
	j := &nativeJournal{enabled: true}
	def := nativeFixed{id: "native-fixed-key", safe: safe, foreground: 68, shade: 47, shadow: image.Pt(4, 4)}
	if !j.captureFixed(def, before, after, after, 1) {
		t.Fatal("valid native fixed field rejected")
	}
	o := j.items[0]
	before[i] = 7
	after[i] = 9
	if o.fixed.before[(21-20)*safe.Dx()+1] != 1 || o.fixed.after[(21-20)*safe.Dx()+1] != 68 || o.canvas[i] != 68 {
		t.Fatal("fixed observation retained caller buffers")
	}
	current := bytes.Clone(o.canvas)
	if !o.visible(current, nil) {
		t.Fatal("unchanged fixed field hidden")
	}
	current[20*320+20] = 9
	j.expireFixed(current, current, 0x13)
	current[20*320+20] = 1
	if !o.fixed.expired || o.visible(current, nil) {
		t.Fatal("stale fixed field resurrected after background returned")
	}
	base := bytes.Repeat([]byte{1}, 64000)
	if !j.captureFixed(def, base, current, current, 2) || j.items[1].fixed.expired || !o.fixed.expired {
		t.Fatal("new reviewed native event did not reactivate")
	}
	if !j.captureFixed(def, base, current, current, 3) || !j.items[1].fixed.expired || j.items[2].fixed.expired {
		t.Fatal("same identity did not replace older native event")
	}
	j.expireFixed(current, current, 0x12)
	if !j.items[2].fixed.expired {
		t.Fatal("video mode change retained fixed field")
	}
}

func TestDraftFixedVGASurfaceAndInvalidInputs(t *testing.T) {
	before := make([]byte, 64000)
	vga := bytes.Clone(before)
	vga[10*320+10] = 14
	j := &nativeJournal{enabled: true}
	def := nativeFixed{id: "native-static-key", safe: image.Rect(10, 10, 20, 20), foreground: 14, vga: true}
	if !j.captureFixed(def, before, vga, before, 1) {
		t.Fatal("VGA fixed source rejected")
	}
	o := j.items[0]
	if o.visible(before, nil) || !o.visible(before, nil, vga) {
		t.Fatal("VGA source confused with canvas")
	}
	j.expireFixed(before, vga, 0x13)
	if o.fixed.expired {
		t.Fatal("unrelated canvas change expired VGA source")
	}
	vga[11*320+11] = 1
	j.expireFixed(before, vga, 0x13)
	if !o.fixed.expired {
		t.Fatal("VGA background rewrite retained static field")
	}
	for _, bad := range []nativeFixed{{id: "x", safe: image.Rect(-1, 0, 2, 2)}, {safe: image.Rect(1, 1, 2, 2)}} {
		if j.captureFixed(bad, before, vga, before, 2) {
			t.Fatal("invalid fixed source accepted")
		}
	}
	if j.captureFixed(def, before[:5], vga, before, 2) || j.captureFixed(def, before, before, before, 2) {
		t.Fatal("truncated or unchanged fixed source accepted")
	}
	quiet := &nativeJournal{}
	if quiet.captureFixed(def, before, vga, before, 2) || quiet.accepted != 0 || quiet.rejected != 0 {
		t.Fatal("disabled capture changed journal")
	}
}

func TestNativeStringRetainsCompleteSource(t *testing.T) {
	r, canvas := nativeStringFixture()
	j := &nativeJournal{enabled: true}
	if !j.captureString(r, canvas, nil, 30) || len(j.items) != 1 {
		t.Fatal("source not retained")
	}
	o := j.items[0]
	r.text[0] = 'B'
	r.boxes[0] = image.Rectangle{}
	r.colors[68] = 99
	r.firstOld[6430], r.lastVal[6430] = 0, 0
	r.charColor[0][68] = image.Rectangle{}
	r.retainedCursor[0], r.retainedSegments[0] = image.Point{}, 0
	r.cargo = cargoProof{}
	canvas[6430] = 0
	c := o.stringRun
	if string(c.text) != "A" || c.boxes[0].Empty() || c.colors[68] != 1 || c.firstOld[6430] != 9 || c.lastVal[6430] != 68 ||
		c.charColor[0][68].Empty() || c.retainedCursor[0] != image.Pt(30, 25) || c.retainedSegments[0] != 0x1234 ||
		c.cargo.role != "header" || !c.outline || c.outlineC != 47 || c.outlineInk.Empty() || c.keyColor != 149 || c.keyNext != 68 || o.canvas[6430] != 68 {
		t.Fatal("native source aliased or lost style/role evidence")
	}
	if o.visible(canvas, nil) {
		t.Fatal("overwritten source remains visible")
	}
	canvas[6430] = 68
	if !o.visible(canvas, nil) {
		t.Fatal("complete original source cannot be re-evaluated")
	}
}

func TestNativeMapSourceAndMixedFallback(t *testing.T) {
	r, canvas := nativeStringFixture()
	r.buf2 = true
	j := &nativeJournal{enabled: true}
	if j.captureString(r, canvas, nil, 30) {
		t.Fatal("map observation accepted without map context")
	}
	buffer := append([]byte(nil), canvas...)
	if !j.captureString(r, make([]byte, 64000), buffer, 30) || !j.items[0].visible(nil, buffer) {
		t.Fatal("map source not checked against map buffer")
	}
	buffer[6430] = 0
	if j.items[0].visible(canvas, buffer) || j.items[0].buffer[6430] != 68 {
		t.Fatal("map source aliased or compared against canvas")
	}
	r.mixed = true
	if !j.captureString(r, canvas, canvas, 40) || j.items[len(j.items)-1].visible(canvas, canvas) {
		t.Fatal("mixed source must retain evidence and decline reconstruction")
	}
}

func TestNativeDialogRetainsCharactersAndErasure(t *testing.T) {
	canvas := make([]byte, 64000)
	canvas[6430], canvas[6431] = 68, 149
	r := &dialogRun{base: 3210, readPos: 4, start: 10, last: 20, shadowWritten: true,
		chars: []dialogChar{{c: 'A', box: image.Rect(30, 20, 31, 21), colors: map[byte]int{68: 1}, prefixContinuation: true},
			{c: 'B', box: image.Rect(31, 20, 32, 21), colors: map[byte]int{149: 1}, contig: true}},
		firstOld: map[int]byte{6430: 9, 6431: 9}, lastText: map[int]bool{6430: true, 6431: false}}
	j := &nativeJournal{enabled: true}
	if !j.captureDialog(r, canvas, 30) {
		t.Fatal("dialog source rejected")
	}
	r.chars[0].c = 'C'
	r.chars[0].colors[68] = 99
	r.firstOld[6430] = 0
	r.lastText[6431] = true
	c := j.items[0].dialogRun
	if c.chars[0].c != 'A' || c.chars[0].colors[68] != 1 || !c.chars[0].prefixContinuation || !c.chars[1].contig ||
		c.firstOld[6430] != 9 || c.lastText[6431] || !c.shadowWritten || len(j.items[0].after) != 1 {
		t.Fatal("dialog character, colors or last-writer evidence lost")
	}
	if j.export(canvas, nil, 3)["items"].([]map[string]any)[0]["visible"].(bool) {
		t.Fatal("old mode13 text visible in another video mode")
	}
}

func TestNativeSeaMenuRetainsOriginalGlyphPositions(t *testing.T) {
	canvas := make([]byte, 64000)
	var runs []*seaEvent
	for n, ch := range []byte(seaMenuText) {
		i := 2*320 + 13 + n
		canvas[i] = 68
		runs = append(runs, &seaEvent{raw: []byte{ch, 0}, bbox: image.Rect(13+n, 2, 14+n, 3),
			firstOld: map[int]byte{i: 9}, lastVal: map[int]byte{i: 68}, colors: map[byte]int{68: 1}, writes: 1})
	}
	j := &nativeJournal{enabled: true}
	if j.captureSea(runs[0], canvas, 10) || !j.captureSeaRuns(runs, canvas, 20) {
		t.Fatal("partial menu retained or complete sequence lost")
	}
	runs[0].raw[0], runs[0].lastVal[653], runs[0].colors[68] = 'X', 0, 99
	c := j.items[0].seaRuns
	if len(c) != len(seaMenuText) || c[0].raw[0] != seaMenuText[0] || c[0].lastVal[653] != 68 || c[0].colors[68] != 1 ||
		c[len(c)-1].bbox.Min.X != 12+len(seaMenuText) || !j.items[0].visible(canvas, nil) {
		t.Fatal("native menu sequence aliased or changed")
	}
}

func TestNativeCaptureBoundsAndDisabledMode(t *testing.T) {
	r, canvas := nativeStringFixture()
	disabled := &nativeJournal{}
	if disabled.captureString(r, canvas, nil, 30) || disabled.accepted+disabled.rejected+disabled.cost != 0 {
		t.Fatal("disabled observation changed state")
	}
	for _, bad := range []int{-1, 64000} {
		r, _ := nativeStringFixture()
		r.firstOld[bad], r.lastVal[bad] = 9, 68
		j := &nativeJournal{enabled: true}
		if j.captureString(r, canvas, nil, 30) || len(j.items) != 0 {
			t.Fatal("invalid source pixels accepted")
		}
	}
	j := &nativeJournal{enabled: true}
	for n := 0; n < 300; n++ {
		if !j.captureString(r, canvas, nil, uint64(n)) {
			t.Fatal("bounded valid source rejected")
		}
	}
	if len(j.items) != draftNativeMaxItems || j.lost != 300-draftNativeMaxItems || j.cost > draftNativeMaxCost || j.items[len(j.items)-1].step != 299 {
		t.Fatal("source journal exceeds bounds or drops newest event")
	}
}
