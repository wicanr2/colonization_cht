//go:build ignore

// Docker-only: run in a disposable module containing the unchanged legacy overlay package.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"image"
	"os"
	"reflect"
	"time"

	old "compositor-oracle/legacy"
	cur "github.com/wicanr2/dosgolem/overlay"
)

func main() {
	checks := 0
	for scale := 1; scale <= 8; scale++ {
		for scenario := 0; scenario < 16; scenario++ {
			before, after := make([]byte, 512), make([]byte, 512)
			palette := make([]byte, 768)
			for i := range palette {
				palette[i] = byte((i*17 + 3) % 64)
			}
			for i := range before {
				before[i], after[i] = byte(i*31), byte(i*31)
			}
			legacy, current := []old.Layer{}, []cur.Layer{}
			for n := 0; n < 4; n++ {
				safe := image.Rect(n*8, 2, n*8+7, 10)
				for y := safe.Min.Y; y < safe.Max.Y; y++ {
					for x := safe.Min.X; x < safe.Max.X; x++ {
						after[y*32+x] ^= 17
					}
				}
				p, e := old.NewPatch(before, after, 32, 16, safe)
				if e != nil {
					panic(e)
				}
				q, e := cur.NewPatch(before, after, 32, 16, safe)
				if e != nil {
					panic(e)
				}
				ink := image.NewAlpha(image.Rect(2, -1, 2+3*scale, -1+4*scale))
				for i := range ink.Pix {
					ink.Pix[i] = byte(i * 19)
				}
				pos := safe.Min.Mul(scale)
				legacy = append(legacy, old.Layer{Patch: p, Ink: ink, Position: pos, ColorIndex: byte(n + 8), Enabled: true})
				current = append(current, cur.Layer{Patch: q, Ink: ink, Position: pos, ColorIndex: byte(n + 8), Enabled: true})
			}
			switch scenario {
			case 1:
				legacy[0].Enabled = false
				current[0].Enabled = false
			case 2:
				legacy[0].Ink = nil
				current[0].Ink = nil
			case 3:
				legacy[0].Patch = nil
				current[0].Patch = nil
			case 4:
				after[2*32] ^= 1
			case 5:
				legacy[0].Position.X = -1
				current[0].Position.X = -1
			case 6:
				legacy[0].Ink.Stride = 0
				current[0].Ink.Stride = 0
			case 7:
				legacy[0].Ink.Pix = nil
				current[0].Ink.Pix = nil
			case 8:
				legacy = append(legacy, legacy[0])
				current = append(current, current[0])
			case 9:
				legacy = nil
				current = nil
			case 10:
				legacy = make([]old.Layer, 32)
				current = make([]cur.Layer, 32)
			case 11:
				legacy = make([]old.Layer, 33)
				current = make([]cur.Layer, 33)
			case 12:
				palette[17] = 64
			case 13:
				palette = nil
			case 14:
				after = nil
			case 15:
				legacy[0].Ink = image.NewAlpha(image.Rect(0, 0, 1, 1))
				current[0].Ink = legacy[0].Ink
			}
			input, pal := append([]byte(nil), after...), append([]byte(nil), palette...)
			left, lr, le := old.ComposeLayers(after, palette, 32, 16, scale, legacy)
			right, rr, re := cur.ComposeLayers(after, palette, 32, 16, scale, current)
			resultsEqual := len(lr) == len(rr) && (lr == nil) == (rr == nil)
			for i := range lr {
				if i >= len(rr) || lr[i].Applied != rr[i].Applied || lr[i].Reason != rr[i].Reason {
					resultsEqual = false
					break
				}
			}
			if fmt.Sprint(le) != fmt.Sprint(re) || !resultsEqual || !reflect.DeepEqual(left, right) ||
				!bytes.Equal(input, after) || !bytes.Equal(pal, palette) {
				fmt.Println("results", lr, rr, "errors", le, re)
				if left != nil && right != nil {
					for i := range left.Pix {
						if left.Pix[i] != right.Pix[i] {
							fmt.Println("pixel byte", i, left.Pix[i], right.Pix[i])
							break
						}
					}
				}
				panic(fmt.Sprintf("scale=%d scenario=%d", scale, scenario))
			}
			checks++
		}
	}
	indexed, palette := make([]byte, 64000), make([]byte, 768)
	measure := func(legacy bool) time.Duration {
		start := time.Now()
		for i := 0; i < 20; i++ {
			if legacy {
				_, _, err := old.ComposeLayers(indexed, palette, 320, 200, 4, make([]old.Layer, 25))
				if err != nil {
					panic(err)
				}
			} else {
				_, _, err := cur.ComposeLayers(indexed, palette, 320, 200, 4, make([]cur.Layer, 25))
				if err != nil {
					panic(err)
				}
			}
		}
		return time.Since(start)
	}
	prior, now := measure(true), measure(false)
	json.NewEncoder(os.Stdout).Encode(map[string]any{"result": "PASS_LEGACY_COMPOSITOR_ORACLE", "cases": checks,
		"old_seconds": prior.Seconds(), "new_seconds": now.Seconds(), "speedup": float64(prior) / float64(now)})
}
