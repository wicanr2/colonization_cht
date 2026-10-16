// 規格069 READY：主選單背景、底紋與已驗文字底色；不寫入DOS。
package main

import (
	"bytes"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"path/filepath"
)

const hdTexturePixelsSHA = "056247f0cb118421e53a69305625486e1d453cf5179690fb9f5bc7cd57b926c7"
const hdTexturePaletteSHA = "243ca37172f22fbfb4182d6d495ad129b9a524f093d67f0d1c5e6d215434ee5f"

type hdTextureCell struct {
	local  uint16
	native byte
}
type hdTextureUnderlay struct {
	cell  hdTextureCell
	glyph byte
}
type hdTexturePair struct {
	cell       hdTextureCell
	has        bool
	old, value byte
	cursor     int
	under      hdTextureUnderlay
	hasUnder   bool
}
type hdTextureRuntime struct {
	sourceLength                                                              int
	sourceEncodedSHA, sourcePixelsSHA, sourcePaletteSHA                       string
	paletteIndices                                                            []byte
	h                                                                         *hdRuntime
	art                                                                       *image.RGBA
	owners                                                                    map[uint32]hdTextureCell
	pending                                                                   map[uint32]hdTexturePair
	underlays                                                                 map[uint32]hdTextureUnderlay
	picture                                                                   []byte
	pictureArt                                                                *image.RGBA
	active                                                                    bool
	base                                                                      uint32
	retCS, retIP, sp                                                          uint16
	start, accepted, rejected, transferred, revoked, revision, cursorRestores uint64
	writes                                                                    [768]byte
	counts                                                                    [768]uint16
}

var hdTextureCopyCodes = map[uint16][]byte{
	0x9c: {0xf3, 0xa5, 0xa4, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0},
	0x9e: {0xa4, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8, 0x8e},
	0xca: {0xf3, 0xa5, 3, 0xf3, 0x79, 0x0c, 0x81, 0xee, 0, 0x80, 0x8c, 0xd9, 0x81, 0xc1, 0, 8},
}

func loadHDTextureRuntime(h *hdRuntime, game, dir string) (*hdTextureRuntime, error) {
	return loadHDTextureVariant(h, game, dir, false)
}
func loadHDTextureVariant(h *hdRuntime, game, dir string, world bool) (*hdTextureRuntime, error) {
	if world {
		return loadHDTextureKind(h, game, dir, "wood")
	}
	return loadHDTextureKind(h, game, dir, "menu")
}
func loadHDTextureKind(h *hdRuntime, game, dir, kind string) (*hdTextureRuntime, error) {
	if kind != "wood" && kind != "menu" && kind != "parch" {
		return nil, fmt.Errorf("unknown texture kind")
	}
	world, parch := kind == "wood", kind == "parch"
	sourceLength := 722

	sourceName, assetName := "OPENTILE.SS", "opentile-000.png"
	originalSHA := "078cc88895ca523498cdcb90d29684ceb0f311007a53a4a20d16b17db7514402"
	assetSHA := "cb2a8af8077d1e6fd0082d753e7cc0251192df0705ebe34496f1954f5cdc4547"
	encodedSHA := "17bbc06dd4b282eb5d649257f0fb639cda7d73820c0ce05f1db32fdea5203ad7"
	pixelsSHA := hdTexturePixelsSHA
	if world {
		sourceName = "WOODTILE.SS"
		assetName = "woodtile-000.png"
		originalSHA = "7b689b766b0f9027627b1a731d8e813a38678b21be41e00d294ecb2cd41ec89c"
		assetSHA = "8580efcf85a45fa879938b5b73e8d54c58853dd9297e8ecd1f10801e637bb5d9"
		encodedSHA = "e33bfeabb5830cec122f88ea7909f2c0fca49a9ec234b2e622cac584cd73499a"
		pixelsSHA = "5cdc9463574bcab9041271e19a92b8a24af408d9c1e4f59e9b6fefbc23b55ce3"
	}

	if parch {
		sourceName, assetName = "PARCH.SS", "parch-000.png"
		originalSHA = "5ba57f44f97e5616dc0fb3d4755de9d1dd75a7e060f4e601c286230d17b72113"
		assetSHA = "4ef702ede0e2d0a46ea94b54fdca602f01071a36a16a83dd57918b8fab15847e"
		encodedSHA = "81f8779fb3041d7b59c81071b1544d4268d291b824c631ec2898a58ef3463414"
		pixelsSHA = "f937c09473b81e48df5dec86faa1db94a18576408896699b3f663aac0e260831"
		sourceLength = 804
	}

	raw, err := hdReadFile(filepath.Join(game, sourceName), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != originalSHA {
		return nil, fmt.Errorf("texture original fingerprint")
	}
	raw, err = hdReadFile(filepath.Join(dir, assetName), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != assetSHA {
		return nil, fmt.Errorf("texture candidate fingerprint")
	}
	im, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	if im.Bounds() != image.Rect(0, 0, 1448, 1086) {
		return nil, fmt.Errorf("texture candidate shape")
	}
	p := &hdTextureRuntime{h: h, art: image.NewRGBA(image.Rect(0, 0, 128, 96)), owners: map[uint32]hdTextureCell{}, pending: map[uint32]hdTexturePair{}, underlays: map[uint32]hdTextureUnderlay{}}
	p.sourceEncodedSHA, p.sourcePixelsSHA, p.sourcePaletteSHA = encodedSHA, pixelsSHA, hdTexturePaletteSHA
	p.sourceLength = sourceLength
	if world {
		p.paletteIndices = []byte{128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138}
		p.sourcePaletteSHA = "84794389fcc2d6ee1bc645822433a74736551ccd1c8d0ed73507235ac42e3896"
	}
	if parch {
		p.paletteIndices = []byte{98, 99, 100, 106, 107}
		p.sourcePaletteSHA = "7ad1391ceb732163dec0f70b714bd2efd13a53c01e878d90bbb899354ecb22c3"
	}
	for y := 0; y < 96; y++ {
		for x := 0; x < 128; x++ {
			c := color.RGBAModel.Convert(im.At((2*x+1)*1448/256, (2*y+1)*1086/192)).(color.RGBA)
			if c.A != 255 {
				return nil, fmt.Errorf("texture opaque candidate")
			}
			p.art.SetRGBA(x, y, c)
		}
	}
	if world || parch {
		return p, nil
	}
	for name, want := range map[string]string{"VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3", "OPENMENU.PIK": "f25c313c66a8f49bf79487fcecbcf76dafff2a81b713f2f3cb2e2d4349fd2004"} {
		raw, err = hdReadFile(filepath.Join(game, name), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != want {
			return nil, fmt.Errorf("picture original fingerprint")
		}
	}
	raw, err = hdReadFile(filepath.Join(dir, "openmenu-000.png"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != "2d688773ecc1bf1a1555d53d632f33fa571cf25a0ea930d38b5219b61ddc819f" {
		return nil, fmt.Errorf("picture art fingerprint")
	}
	imageBG, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	if imageBG.Bounds() != image.Rect(0, 0, 1586, 992) {
		return nil, fmt.Errorf("picture art shape")
	}
	p.pictureArt = image.NewRGBA(image.Rect(0, 0, 1280, 800))
	for y := 0; y < 800; y++ {
		for x := 0; x < 1280; x++ {
			c := color.RGBAModel.Convert(imageBG.At((2*x+1)*1586/2560, (2*y+1)*992/1600)).(color.RGBA)
			if c.A != 255 {
				return nil, fmt.Errorf("picture alpha")
			}
			p.pictureArt.SetRGBA(x, y, c)
		}
	}
	return p, nil
}
func (p *hdTextureRuntime) beforeInstruction() {
	if p == nil {
		return
	}
	m := p.h.m
	c := m.CPU
	cs, ip := c.Seg[golem.CS], c.IP
	if p.active && cs == p.retCS && ip == p.retIP && c.R[golem.SP] == p.sp+10 {
		p.finish()
	}
	if p.active && (m.Steps-p.start > 100000 || (cs == 0xd46 && ip == 0xa)) {
		p.active = false
		p.rejected++
	}
	if cs != 0xd46 || ip != 0xa || c.R[golem.AX] != 1 {
		return
	}
	pc := int(cs)*16 + int(ip)
	if !bytes.Equal(m.Mem[pc:pc+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	stack, ok := hdBuildingWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	if !ok {
		return
	}
	dest, ok := hdBuildingWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok || dest[0] != 24 || dest[1] != 32 || c.R[golem.DX] != 0 || stack[2] != 0 {
		return
	}
	off := uint16(12 + uint32(stack[3]) + 0x36)
	record, ok := hdBuildingWords(m.Mem, stack[4], off, 6)
	if !ok || record[4] != 32 || record[5] != 24 {
		return
	}
	at := int(record[1])*16 + int(record[0])
	if int(record[0])+p.sourceLength > 65536 || at+p.sourceLength > len(m.Mem) || hash(m.Mem[at:at+p.sourceLength]) != p.sourceEncodedSHA {
		return
	}
	base := uint32(dest[3])*16 + uint32(dest[2])
	if base+768 > 0xa0000 {
		return
	}
	p.base, p.active, p.start, p.retCS, p.retIP, p.sp = base, true, m.Steps, stack[1], stack[0], c.R[golem.SP]
	clear(p.writes[:])
	clear(p.counts[:])
}
func (p *hdTextureRuntime) finish() {
	p.active = false
	for k, n := range p.counts {
		if n != 1 || p.h.m.Mem[p.base+uint32(k)] != p.writes[k] {
			p.rejected++
			return
		}
	}
	if hash(p.writes[:]) != p.sourcePixelsSHA {
		p.rejected++
		return
	}
	for k, v := range p.writes {
		p.owners[p.base+uint32(k)] = hdTextureCell{uint16(k), v}
	}
	p.accepted++
	p.revision++
}
func (p *hdTextureRuntime) memoryWrite(addr uint32, old, value byte) {
	if p == nil {
		return
	}
	m := p.h.m
	cs, ip := m.CPU.OpAddr()
	if p.pictureArt != nil && p.picture == nil && addr == 0x3c500+63999 && cs == 0x11b5 {
		pc := int(cs)*16 + int(ip)
		known := (ip == 0x4ee && bytes.Equal(m.Mem[pc:pc+16], []byte{0xa4, 0xeb, 0xed, 0x33, 0xc9, 0x4a, 0x75, 9, 0xad, 0xb2, 0x10, 0xd1, 0xed, 0x8b, 0xe8, 0xd1})) || (ip == 0x54a && bytes.Equal(m.Mem[pc:pc+16], []byte{0xaa, 0xe2, 0xfa, 0xeb, 0x8f, 0xac, 0x0a, 0xc0, 0x74, 0x32, 0x3c, 1, 0x74, 5, 0x8a, 0xc8}))
		if known && hash(m.Mem[0x3c500:0x3c500+64000]) == "5325a3501b83df510cee60c134952130fdb9dfd4bdc00d9eb853fb7ae6021eff" {
			p.picture = append([]byte(nil), m.Mem[0x3c500:0x3c500+64000]...)
			p.revision++
		}
	}
	if p.active && addr >= p.base && addr < p.base+768 {
		k := int(addr - p.base)
		code, ok := hdNineWriterCodes[ip]
		pc := int(cs)*16 + int(ip)
		if cs != 0xd46 || !ok || !bytes.Equal(m.Mem[pc:pc+16], code) || p.counts[k] == 65535 {
			p.active = false
			p.rejected++
		} else {
			p.counts[k]++
			p.writes[k] = value
		}
	}
	if p.accepted == 0 || addr >= 0xa0000 {
		return
	}
	if addr >= hdBuildingCanvas && addr < hdBuildingCanvas+64000 {
		if cs == 0xb68 && ip == 0x51c && m.CPU.Seg[golem.DS] == 0xa000 && m.CPU.Seg[golem.ES] == 0x2cae {
			pc := int(cs)*16 + int(ip)
			delta := int(addr) - (int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI]))
			src := int(m.CPU.R[golem.SI]) + delta
			if delta == 0 && src >= 0xfa00 && src < 0xfc00 && bytes.Equal(m.Mem[pc:pc+16], []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}) {
				if _, ok := p.h.cursorSource(); ok && m.Mem[0xa0000+src] == value {
					k := src & 255
					if src >= 0xfb00 {
						cell, has := p.owners[addr]
						has = has && cell.native == old
						under, hasUnder := p.underlays[addr]
						hasUnder = hasUnder && under.glyph == old
						p.pending[addr] = hdTexturePair{cell: cell, has: has, old: old, value: value, cursor: k, under: under, hasUnder: hasUnder}
						delete(p.underlays, addr)
						delete(p.owners, addr)
						p.revision++
						return
					}
					prior, ok := p.pending[addr]
					delete(p.pending, addr)
					if ok && prior.cursor == k && old == prior.value && value == prior.old {
						if prior.has {
							p.owners[addr] = prior.cell
							p.cursorRestores++
						}
						if prior.hasUnder {
							p.underlays[addr] = prior.under
						}
						p.revision++
						return
					}
				}
			}
		}
		clear(p.pending)
		pc := int(cs)*16 + int(ip)
		if cs == 0xd21 && ip == 0x12c && bytes.Equal(m.Mem[pc:pc+16], []byte{0x26, 0x88, 0x25, 0x47, 0xfe, 0xca, 0x74, 0x0a, 0xfe, 0xcd, 0x75, 0xdf, 0xac, 0xb5, 4, 0xeb}) {
			cell, ok := p.owners[addr]
			if ok && cell.native == old {
				p.underlays[addr] = hdTextureUnderlay{cell, value}
				p.revision++
			} else if under, ok := p.underlays[addr]; ok && under.glyph == old {
				under.glyph = value
				p.underlays[addr] = under
				p.revision++
			} else {
				delete(p.underlays, addr)
			}
		} else if _, ok := p.underlays[addr]; ok {
			delete(p.underlays, addr)
			p.revision++
		}
	}
	var cell hdTextureCell
	known := false
	if code, ok := hdTextureCopyCodes[ip]; cs == 0xcba && ok && m.CPU.Flags&0x400 == 0 {
		pc := int(cs)*16 + int(ip)
		delta := int(addr) - (int(m.CPU.Seg[golem.ES])*16 + int(m.CPU.R[golem.DI]))
		limit := 2
		if ip == 0x9e {
			limit = 1
		}
		si, di := int(m.CPU.R[golem.SI]), int(m.CPU.R[golem.DI])
		src := int(m.CPU.Seg[golem.DS])*16 + si + delta
		if bytes.Equal(m.Mem[pc:pc+16], code) && delta >= 0 && delta < limit && si+delta < 65536 && di+delta < 65536 && src >= 0 && src < 0xa0000 && m.Mem[src] == value {
			cell, known = p.owners[uint32(src)]
			known = known && cell.native == value
		}
	}
	if _, ok := p.owners[addr]; ok {
		delete(p.owners, addr)
		p.revoked++
		p.revision++
	}
	if known {
		p.owners[addr] = cell
		p.transferred++
		p.revision++
	}
	if len(p.owners) > 200000 {
		clear(p.owners)
		p.rejected++
		p.revision++
	}
}
func (p *hdTextureRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	mask := make([]byte, 8000)
	painted := 0
	supported := p.paletteSupported(f.palette)
	if supported {
		for a, c := range p.owners {
			if a < hdBuildingCanvas || a >= hdBuildingCanvas+64000 {
				continue
			}
			k := int(a - hdBuildingCanvas)
			if f.canvas[k] != c.native {
				continue
			}
			sx, sy := int(c.local)%32*4, int(c.local)/32*4
			x, y := k%320*4, k/320*4
			draw.Draw(out, image.Rect(x, y, x+4, y+4), p.art, image.Pt(sx, sy), draw.Over)
			mask[k>>3] |= 1 << uint(k&7)
			painted++
		}
	}
	return map[string]any{"formal": true, "prototype": false, "painted": painted, "mask": mask, "accepted": p.accepted, "rejected": p.rejected, "transferred": p.transferred, "revoked": p.revoked, "palette_supported": supported, "revision": p.revision, "cursor_source_restores": p.cursorRestores, "pending": len(p.pending)}
}
func (h *hdRuntime) base(f draftNativeFrame) (*image.RGBA, map[string]any) {
	out, record := h.baseExisting(f)
	if h.texture != nil {
		if record["reason"] != "unverified-cursor-or-native-surface" {
			record["picture"] = h.texture.paintPicture(out, f)
			record["texture"] = h.texture.paint(out, f)
		}
	}
	if h.worldTexture != nil && record["reason"] != "unverified-cursor-or-native-surface" {
		record["world_texture"] = h.worldTexture.paint(out, f)
	}
	if h.parch != nil && record["reason"] != "unverified-cursor-or-native-surface" {
		group := h.parch.paint(out, f)
		group["formal"] = true
		group["prototype"] = false
		record["parch"] = group
	}
	if h.newGame != nil && record["reason"] != "unverified-cursor-or-native-surface" {
		record["new_game_picture"] = h.newGame.paint(out, f)
	}
	return out, record
}

func (p *hdTextureRuntime) paintBackground(out *image.RGBA, f draftNativeFrame, pos int, v byte, palette []byte) bool {
	if pos < 0 || pos >= 64000 || len(f.canvas) != 64000 || !p.paletteSupported(palette) {
		return false
	}
	addr := hdBuildingCanvas + uint32(pos)
	cell, ok := p.owners[addr]
	if ok {
		ok = f.canvas[pos] == cell.native
	} else if under, known := p.underlays[addr]; known && f.canvas[pos] == under.glyph {
		cell, ok = under.cell, true
	}
	if !ok || cell.native != v {
		return false
	}
	x, y := pos%320*4, pos/320*4
	sx, sy := int(cell.local)%32*4, int(cell.local)/32*4
	draw.Draw(out, image.Rect(x, y, x+4, y+4), p.art, image.Pt(sx, sy), draw.Src)
	return true
}
func (p *hdTextureRuntime) paintPicture(out *image.RGBA, f draftNativeFrame) map[string]any {
	mask := make([]byte, 8000)
	record := map[string]any{"prototype": false, "formal": true, "painted": 0, "mask": mask, "decoded_source_verified": len(p.picture) == 64000, "matched": false}
	if len(p.picture) != 64000 || len(f.canvas) != 64000 || len(f.indexed) != 64000 || len(f.palette) != 768 || hash(f.palette) != hdTexturePaletteSHA {
		return record
	}
	panel := image.Rect(77, 91, 243, 150)
	border := make([]byte, 0, 884)
	for y := 91; y < 150; y++ {
		for x := 77; x < 243; x++ {
			if x < 79 || x >= 241 || y < 93 || y >= 148 {
				border = append(border, f.canvas[y*320+x])
			}
		}
	}
	if hash(border) != "2baed3992da35e0710dbaca6b1263f2b4a4e7f52f9e1431120a6ec00de5493c5" {
		return record
	}
	for k, v := range p.picture {
		pt := image.Pt(k%320, k/320)
		if pt.In(panel) || pt.In(f.cursor) {
			continue
		}
		if f.indexed[k] != v {
			return record
		}
	}
	for _, rect := range []image.Rectangle{image.Rect(0, 0, 1280, 364), image.Rect(0, 600, 1280, 800), image.Rect(0, 364, 308, 600), image.Rect(972, 364, 1280, 600)} {
		draw.Draw(out, rect, p.pictureArt, rect.Min, draw.Src)
	}
	count := 0
	for k := 0; k < 64000; k++ {
		if !image.Pt(k%320, k/320).In(panel) {
			mask[k>>3] |= 1 << uint(k&7)
			count++
		}
	}
	record["painted"], record["matched"] = count, true
	return record
}

func (p *hdTextureRuntime) paletteSupported(palette []byte) bool {
	if len(palette) != 768 {
		return false
	}
	if len(p.paletteIndices) == 0 {
		return hash(palette) == p.sourcePaletteSHA
	}
	raw := make([]byte, 0, len(p.paletteIndices)*4)
	for _, i := range p.paletteIndices {
		raw = append(raw, i)
		raw = append(raw, palette[int(i)*3:int(i)*3+3]...)
	}
	return hash(raw) == p.sourcePaletteSHA
}
