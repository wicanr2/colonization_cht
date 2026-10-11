package main

// 下列為觀測資料結構的單元fixture，不作原版行為或同狀態證據。
import (
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
