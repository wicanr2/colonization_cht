// 規格052：只在隔離副本加入的私有英數觀測。
package main

import "image"

var retainedASCIIObservations []map[string]any
var retainedASCIIOverflow int
var retainedASCIIReads []map[string]any
var retainedASCIIReadOverflow int

func observeRetainedASCII(s *stringRuntime, r *stringRun, step uint64, it *stringItem, baselineWhy, finalWhy string) {
	if !retainedPrintable(r.text) {
		return
	}
	if len(retainedASCIIObservations) >= 8192 {
		retainedASCIIOverflow++
		return
	}
	var ink image.Rectangle
	for _, box := range r.boxes {
		ink = ink.Union(box)
	}
	event := map[string]any{"source_linear": r.base, "source_entry": "0D21:00C6", "start_step": r.start,
		"complete_step": step, "text": string(r.text), "char_ink": r.boxes, "ink": ink, "colors": r.colors,
		"outline": r.outline, "mixed": r.mixed, "buffer2": r.buf2, "other_writer": r.others,
		"baseline_reason": baselineWhy, "final_reason": finalWhy, "owned": s.cat.isOwned(string(r.text))}
	event["native_cursors"], event["native_segments"] = r.retainedCursor, r.retainedSegments
	if it != nil {
		event["item_id"], event["display"], event["font_px"], event["safe"] = it.id, it.zh, it.size, it.safe
		if it.id == "STRING:retained-ascii" {
			layout, _ := retainedASCIILayout(r, ink)
			plan := planRetainedASCII(s.cat.fonts, it.zh, layout)
			event["layout"] = layout
			event["font_ink"] = plan.bounds
			event["mask_sha256"] = hash(it.norm.Pix)
		}
	}
	retainedASCIIObservations = append(retainedASCIIObservations, event)
}

func saveRetainedASCIIObservations(output string) {
	dumpJSON(output+".retained-ascii.json", map[string]any{"kind": "draft-retained-ascii-font-observations",
		"enabled": *retainedASCIIEnabled, "overflow": retainedASCIIOverflow, "events": retainedASCIIObservations,
		"read_overflow": retainedASCIIReadOverflow, "reads": retainedASCIIReads})
}

func observeRetainedASCIIRead(address uint32, value byte, step uint64, registers, segments any) {
	if len(retainedASCIIReads) >= 32768 {
		retainedASCIIReadOverflow++
		return
	}
	retainedASCIIReads = append(retainedASCIIReads, map[string]any{"source_linear": address,
		"value": value, "step": step, "registers": registers, "segments": segments})
}
