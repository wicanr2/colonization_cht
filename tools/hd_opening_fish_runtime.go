// 規格069 R87 READY：完整魚形僅依已驗當前發布來源合成；不改原版狀態。
package main

import (
	"bytes"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"path/filepath"
)

var hdOpeningFishWorld = image.Rect(584, 16, 640, 55)

type hdOpeningFishDefinition struct {
	id         int
	anchor     image.Point
	world, raw image.Rectangle
}
type hdOpeningFishRuntime struct{ art [21]*image.RGBA }
type hdOpeningFishPose struct {
	present, valid bool
	slot           int
	origin         image.Point
	reason         string
	candidates     []int
	foreground     int
}

func loadHDOpeningFish(s *hdOpeningSpriteRuntime, directory string) (*hdOpeningFishRuntime, error) {
	if len(hdOpeningFishDefinitions) != 21 {
		return nil, fmt.Errorf("fish definition count")
	}
	clearRaw, e := hdReadFile(filepath.Join(directory, "opening-fish-clear-000.png"), 8<<20)
	if e != nil {
		return nil, e
	}
	if hash(clearRaw) != hdOpeningFishClearSHA {
		return nil, fmt.Errorf("fish clear fingerprint")
	}
	clean, e := png.Decode(bytes.NewReader(clearRaw))
	if e != nil {
		return nil, e
	}
	if clean.Bounds() != image.Rect(0, 0, 1503, 1047) {
		return nil, fmt.Errorf("fish clear size")
	}
	oldDef := hdOpeningDefinition{}
	for _, d := range hdOpeningDefinitions {
		if d.asset == "opening-fish-top-000.png" {
			oldDef = d
		}
	}
	if len(oldDef.nativeRects) != 1 || len(oldDef.artRects) != 1 || oldDef.nativeRects[0] != image.Rect(584, 24, 633, 55) {
		return nil, fmt.Errorf("fish static source geometry")
	}
	oldRaw, e := hdReadFile(filepath.Join(directory, oldDef.asset), 8<<20)
	if e != nil {
		return nil, e
	}
	if hash(oldRaw) != oldDef.sha {
		return nil, fmt.Errorf("fish static fingerprint")
	}
	old, e := png.Decode(bytes.NewReader(oldRaw))
	if e != nil {
		return nil, e
	}
	background := image.NewRGBA(image.Rect(0, 0, 224, 156))
	draw.Draw(background, background.Bounds(), s.p.art[1], image.Pt(584*4, 16*4), draw.Src)
	for y := 0; y < 156; y++ {
		for x := 0; x < 224; x++ {
			wx, wy := x/4+584, y/4+16
			if !image.Pt(wx, wy).In(oldDef.nativeRects[0]) {
				continue
			}
			r, a := oldDef.nativeRects[0], oldDef.artRects[0]
			tx, ty := x-(r.Min.X-584)*4, y-(r.Min.Y-16)*4
			sx := a.Min.X + (2*tx+1)*a.Dx()/(2*r.Dx()*4)
			sy := a.Min.Y + (2*ty+1)*a.Dy()/(2*r.Dy()*4)
			if color.NRGBAModel.Convert(old.At(sx, sy)).(color.NRGBA).A == 0 {
				continue
			}
			c := color.NRGBAModel.Convert(clean.At((2*x+1)*1503/(2*224), (2*y+1)*1047/(2*156))).(color.NRGBA)
			if c.A != 255 {
				return nil, fmt.Errorf("fish clear alpha")
			}
			background.SetRGBA(x, y, color.RGBA{c.R, c.G, c.B, 255})
		}
	}
	p := &hdOpeningFishRuntime{}
	for i, f := range hdOpeningFishDefinitions {
		d := hdOpeningSpriteDefinitions[36+i]
		if d.id != f.id || f.id != 1182+i || f.world != image.Rect(584, 24, 633, 55).Union(image.Rect(f.anchor.X, f.anchor.Y, f.anchor.X+d.w, f.anchor.Y+d.h)) || f.world.Empty() || !f.world.In(hdOpeningFishWorld) {
			return nil, fmt.Errorf("fish object geometry")
		}
		raw, e := hdReadFile(filepath.Join(directory, d.asset), 8<<20)
		if e != nil {
			return nil, e
		}
		if hash(raw) != d.artSHA {
			return nil, fmt.Errorf("fish art fingerprint")
		}
		im, e := png.Decode(bytes.NewReader(raw))
		if e != nil {
			return nil, e
		}
		if im.Bounds() != image.Rect(0, 0, d.artSize.X, d.artSize.Y) || f.raw.Empty() || !f.raw.In(im.Bounds()) {
			return nil, fmt.Errorf("fish raw geometry")
		}
		dst := image.NewRGBA(background.Bounds())
		copy(dst.Pix, background.Pix)
		target := image.Rect((f.world.Min.X-584)*4, (f.world.Min.Y-16)*4, (f.world.Max.X-584)*4, (f.world.Max.Y-16)*4)
		for y := target.Min.Y; y < target.Max.Y; y++ {
			for x := target.Min.X; x < target.Max.X; x++ {
				sx := f.raw.Min.X + (2*(x-target.Min.X)+1)*f.raw.Dx()/(2*target.Dx())
				sy := f.raw.Min.Y + (2*(y-target.Min.Y)+1)*f.raw.Dy()/(2*target.Dy())
				a := color.NRGBAModel.Convert(im.At(sx, sy)).(color.NRGBA)
				b := dst.RGBAAt(x, y)
				over := func(v, d byte) byte { return byte((uint32(v)*uint32(a.A) + uint32(d)*uint32(255-a.A) + 127) / 255) }
				dst.SetRGBA(x, y, color.RGBA{over(a.R, b.R), over(a.G, b.G), over(a.B, b.B), 255})
			}
		}
		p.art[i] = dst
	}
	return p, nil
}

func (s *hdOpeningSpriteRuntime) fishPose(f draftNativeFrame) hdOpeningFishPose {
	result := hdOpeningFishPose{slot: -1, reason: "no-published-fish"}
	present := [21]bool{}
	originKnown := false
	for pos, c := range s.published {
		if c.id < 1182 || c.id > 1202 {
			continue
		}
		result.present = true
		which := int(c.id - 1182)
		present[which] = true
		d := hdOpeningFishDefinitions[which]
		source := hdOpeningSpriteDefinitions[36+which]
		if !s.nativeValid[36+which] || !s.validUnder(c.under) || c.under.kind != 2 || int(c.local) >= source.w*source.h {
			result.reason = "fish-source"
			return result
		}
		wx, wy := d.anchor.X+int(c.local)%source.w, d.anchor.Y+int(c.local)/source.w
		if int(c.under.local) != wy*960+wx {
			result.reason = "fish-anchor"
			return result
		}
		origin := image.Pt(pos%320-wx, pos/320-wy)
		if originKnown && result.origin != origin {
			result.reason = "mixed-published-fish-origin"
			return result
		}
		result.origin = origin
		originKnown = true
	}
	if !result.present {
		return result
	}
	rect := hdOpeningFishWorld.Add(result.origin)
	if !rect.In(image.Rect(0, 0, 320, 200)) {
		result.reason = "fish-object-clipped"
		return result
	}
	foreground := [2184]bool{}
	for y := 16; y < 55; y++ {
		for x := 584; x < 640; x++ {
			local, pos := y*960+x, (y+result.origin.Y)*320+x+result.origin.X
			a, c := s.published[pos], s.pictures[pos]
			key := (y-16)*56 + x - 584
			if a.id != 0 {
				if !s.validUnder(a.under) || a.under.kind != 2 || int(a.under.local) != local || a.under.value != s.p.native[1][local] {
					result.reason = "unknown-fish-object-underlay"
					return result
				}
				slot, ok := hdOpeningSpriteSlot(a.id)
				if !ok || !s.nativeValid[slot] || int(a.local) >= hdOpeningSpriteDefinitions[slot].w*hdOpeningSpriteDefinitions[slot].h || s.native[slot][a.local] != f.indexed[pos] {
					result.reason = "unknown-fish-object-actor"
					return result
				}
				if a.id < 1182 || a.id > 1202 {
					foreground[key] = true
					result.foreground++
				}
			} else if c.kind != 2 || int(c.local) != local || !s.validUnder(c) || c.value != f.indexed[pos] {
				result.reason = "unknown-fish-object-picture"
				return result
			}
		}
	}
	for which, have := range present {
		if !have || !s.nativeValid[36+which] {
			continue
		}
		d := hdOpeningFishDefinitions[which]
		source := hdOpeningSpriteDefinitions[36+which]
		matched := true
		for y := 16; y < 55 && matched; y++ {
			for x := 584; x < 640; x++ {
				if foreground[(y-16)*56+x-584] {
					continue
				}
				want := s.p.native[1][y*960+x]
				if x >= d.anchor.X && x < d.anchor.X+source.w && y >= d.anchor.Y && y < d.anchor.Y+source.h {
					v := s.native[36+which][(y-d.anchor.Y)*source.w+x-d.anchor.X]
					if v != 253 {
						want = v
					}
				}
				if f.indexed[(y+result.origin.Y)*320+x+result.origin.X] != want {
					matched = false
					break
				}
			}
		}
		if !matched {
			continue
		}
		result.candidates = append(result.candidates, d.id)
		if result.slot >= 0 && !bytes.Equal(s.fish.art[result.slot].Pix, s.fish.art[which].Pix) {
			result.reason = "ambiguous-fish-art"
			return result
		}
		if result.slot < 0 {
			result.slot = which
		}
	}
	if result.slot < 0 {
		result.reason = "mixed-native-fish-pose"
		return result
	}
	result.valid = true
	result.reason = "verified-published-whole-fish"
	return result
}

func hdOpeningOriginalCell(out *image.RGBA, f draftNativeFrame, pos int) {
	at := int(f.indexed[pos]) * 3
	expand := func(v byte) byte { return v<<2 | v>>4 }
	c := color.RGBA{expand(f.palette[at]), expand(f.palette[at+1]), expand(f.palette[at+2]), 255}
	for dy := 0; dy < 4; dy++ {
		for dx := 0; dx < 4; dx++ {
			out.SetRGBA(pos%320*4+dx, pos/320*4+dy, c)
		}
	}
}
