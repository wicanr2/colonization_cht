// 規格066 READY：一般游標原alpha顯示層，不寫入DOS。
package main

import (
	"bytes"
	"encoding/base64"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"path/filepath"
	"strings"
)

const hdCursorAssetSHA = "2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4"

type hdCursorRuntime struct{ art *image.RGBA }

func loadHDCursorRuntime(game, directory string) (*hdCursorRuntime, error) {
	source, err := hdReadFile(filepath.Join(game, "CURSOR.SS"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(source) != "3ff5a4b70f08780f845b1e973d7dce3ff34868bb73279174210fce76332fffcb" {
		return nil, fmt.Errorf("HD cursor original fingerprint mismatch")
	}
	raw, err := hdReadFile(filepath.Join(directory, "cursor-000.png"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != hdCursorAssetSHA {
		return nil, fmt.Errorf("HD cursor asset fingerprint mismatch")
	}
	im, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	if im.Bounds() != image.Rect(0, 0, 1254, 1254) {
		return nil, fmt.Errorf("HD cursor dimensions mismatch")
	}
	bbox := image.Rectangle{}
	for y := 0; y < 1254; y++ {
		for x := 0; x < 1254; x++ {
			_, _, _, a := im.At(x, y).RGBA()
			if a >= 128*257 {
				r := image.Rect(x, y, x+1, y+1)
				if bbox.Empty() {
					bbox = r
				} else {
					bbox = bbox.Union(r)
				}
			}
		}
	}
	if bbox != image.Rect(106, 188, 721, 1047) {
		return nil, fmt.Errorf("HD cursor alpha geometry mismatch")
	}
	p := &hdCursorRuntime{art: image.NewRGBA(image.Rect(0, 0, 64, 64))}
	for y := 0; y < 56; y++ {
		for x := 0; x < 40; x++ {
			sx, sy := bbox.Min.X+(2*x+1)*bbox.Dx()/80, bbox.Min.Y+(2*y+1)*bbox.Dy()/112
			p.art.SetRGBA(x, y, color.RGBAModel.Convert(im.At(sx, sy)).(color.RGBA))
		}
	}
	return p, nil
}

// 規格066／069 R80 READY：原版不透明游標先還原，再依既有原alpha合成。
// 已發布表面須另驗完整VGA與局部游標；來源與暫存參與HD快取鍵。
// 未寫入原版RAM，也沒有新增來源觀測或滑鼠事件。
func (p *hdCursorRuntime) paint(h *hdRuntime, out *image.RGBA, f draftNativeFrame) map[string]any {
	r := map[string]any{"formal": true, "asset_sha256": hdCursorAssetSHA, "source_cells": 0, "painted": 0}
	source, reason := h.cursorProof(f)
	if strings.HasPrefix(reason, "outside-cursor:") && len(f.indexed) == 64000 && len(h.m.Mem) >= 0xa0000+64000 && bytes.Equal(h.m.Mem[0xa0000:0xa0000+64000], f.indexed) {
		source, reason = h.cursorPixelsProof(f)
		r["published_surface_cursor"] = reason == ""
	}

	if reason != "" {
		r["reason"] = reason
		return r
	}
	mask := make([]byte, 8000)
	cells, painted := 0, 0
	for k, v := range source {
		if v == 255 {
			continue
		}
		x, y := f.cursor.Min.X+k%16, f.cursor.Min.Y+k/16
		if x < 0 || y < 0 || x >= 320 || y >= 200 {
			continue
		}
		if r["published_surface_cursor"] == true {
			draftPaintPixel(out, y*320+x, f.indexed[y*320+x], f.palette)
		}
		cells++
		sx, sy := k%16*4, k/16*4
		active := false
		for dy := 0; dy < 4; dy++ {
			for dx := 0; dx < 4; dx++ {
				if p.art.RGBAAt(sx+dx, sy+dy).A > 0 {
					active = true
				}
			}
		}
		if active {
			painted++
			pos := y*320 + x
			mask[pos>>3] |= 1 << uint(pos&7)
		}
		draw.Draw(out, image.Rect(x*4, y*4, x*4+4, y*4+4), p.art, image.Pt(sx, sy), draw.Over)
	}
	r["source_cells"], r["painted"], r["mask"], r["source_sha256"] = cells, painted, base64.StdEncoding.EncodeToString(mask), hash(source)
	return r
}
