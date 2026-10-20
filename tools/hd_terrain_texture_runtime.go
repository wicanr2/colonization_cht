// 規格071 READY：十二種地形材質、來源搬運與原版色盤循環；不寫入DOS。
package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	golem "github.com/wicanr2/dosgolem"
	"image"
	"image/color"
	"image/png"
	"path/filepath"
	"strings"
)

type hdTerrainTextureDefinition struct {
	ordinal, length                          int
	encoded, indexed, writes, file, assetSHA string
}
type hdTerrainTextureFrame struct {
	hdTerrainTextureDefinition
	art      *image.RGBA
	native   [256]byte
	accepted uint64
}
type hdTerrainTextureCell struct {
	local  uint16
	native byte
	slot   uint8
}
type hdTerrainTextureUnderlay struct {
	cell  hdTerrainTextureCell
	glyph byte
}
type hdTerrainTexturePair struct {
	cell       hdTerrainTextureCell
	has        bool
	old, value byte
	cursor     int
	under      hdTerrainTextureUnderlay
	hasUnder   bool
}
type hdTerrainTextureRuntime struct {
	h                                                                         *hdRuntime
	frames                                                                    [12]*hdTerrainTextureFrame
	current                                                                   *hdTerrainTextureFrame
	owners                                                                    map[uint32]hdTerrainTextureCell
	pending                                                                   map[uint32]hdTerrainTexturePair
	underlays                                                                 map[uint32]hdTerrainTextureUnderlay
	published                                                                 [64000]hdSceneCell
	publishedPending                                                          map[int]hdSceneCursorPair
	publicationBlocked, active                                                bool
	base                                                                      uint32
	retCS, retIP, sp                                                          uint16
	start, accepted, rejected, transferred, revoked, revision, cursorRestores uint64
	writes                                                                    [256]byte
	counts                                                                    [256]uint16
	guard                                                                     [64]byte
}

var hdTerrainTextureDefinitions = []hdTerrainTextureDefinition{
	{ordinal: 0, length: 289, encoded: "ed5d9cbfa7e43eefebc36f6380805b1c6fa67a4169ce82b1dc68e95c5d822d63", indexed: "2410d731c633a9f50202c97792df9b9434a222185f3745f9b82afa1065861ba3", writes: "47d9c6cf0b02303031b114585827bb6d020428ac4ab86fb66a96cb50bf4d437e", file: "terrain-texture-000.png", assetSHA: "1cef0ad5f9c5fca566f10f23f6b92e28bc169c515615ebad2868dc93812ef1f2"},
	{ordinal: 1, length: 280, encoded: "f10e6db013b36cee8c4f51734179072caa1c700f42dae9f403d7ac91b084072f", indexed: "987bcf83e76d519d37e8fc045ca01bbc37eaca6dcf0b4e99cfd2a7939b7e3ba2", writes: "9a38b8c07104e1508639369db9d0018a54415d4fcd1cfbffde9179114c48114b", file: "terrain-texture-001.png", assetSHA: "ec509b042efc8d561bd975460b7f3183fcfffa0aa20979417f7d5b8ec490d2fd"},
	{ordinal: 2, length: 289, encoded: "4eaa72647cd4cde516a12c68fbe23a469ee58f5465e6acd1dff6e2ee67b6304c", indexed: "6b05aeb2a66a907405b1fab277e9a99d0fc1794b38950cfcfe6c4e63ef786992", writes: "00d0940673be8f01eab55d097a6a25d058a4d64eb54c7d73f69ddd5d125dc88c", file: "terrain-texture-002.png", assetSHA: "0ec35827e02d910b63218b2b3d8ac46618d45984ba47a790fcd19813b30069ea"},
	{ordinal: 3, length: 287, encoded: "1a533ec3e6e6aa8024b6b244316628ef6cf9c0cb3b657fa23796aa5cf1201f9c", indexed: "5fcdb336305e520a2aa227c10ba9d13ed76833b1bf3b00d67ed76ec2e4f080d2", writes: "10c6c218ed80c61683f0fce7be0a2d5d2547df542daa193c6c57d1503d29bd0a", file: "terrain-texture-003.png", assetSHA: "19bd3b79998db01e26cb8d36bfc8549a23381281436f544d4cc6147a55401944"},
	{ordinal: 4, length: 285, encoded: "667b4eb15dba94d017a44f794e114539fbae6c9e4a18478ed1d170243e88e1a9", indexed: "18671c8af6ba0eb0858305c1ef20e03d9c5560bf68f10e74fe8040e368c81525", writes: "7c85011b7433dc24dad41325687ee853da25a9a5df8fd79d0780677408ef63f0", file: "terrain-texture-004.png", assetSHA: "7eb28c6927c45c8cf316e894876afc90d578532ad185ec5072699eac898345c7"},
	{ordinal: 5, length: 262, encoded: "170af1db639c412cdb55610054c1156f68b221fc7765e3d9dc2fed3c7a021a89", indexed: "6207c0ccc4c08cf448095fdeb02a43c85faee78e905c2082aa5cbdcb7cb368cf", writes: "acbab4fb11c433822e41d37a0a96347bc1fea64602f80dadb0b6338e79f5366e", file: "terrain-texture-005.png", assetSHA: "aed5b8739b8aae9bede8e3b24fb99b0984c1683a3c450648ed111f6016198fb4"},
	{ordinal: 6, length: 289, encoded: "b6f66241a7d235c9491f3979080d93a5b05f590ae7d9685676906c1e89f85125", indexed: "7b7f2a708e0ce0cc9fe63fd9635dd522de3f4ae34670e7ef9fceb9d048684c54", writes: "39882639fb4bb170ea128005f09d810f456eabdbed95e959ad113d9f024f97bf", file: "terrain-texture-006.png", assetSHA: "a06bd0f8d717c68589ff2be53d11b488ba886b768509c989013b8ceca9010621"},
	{ordinal: 7, length: 284, encoded: "e5157406d74b0a8077f8b5f92b26cace67b3f233d17e0f747f242acb9257d6ce", indexed: "a1436ff7e72cfc35e425af2407a7332daa8e2e8c8c1975a215280e995be56ba4", writes: "fdd51a7b5fe1ecf266823141ef7ed52b99147a21339aeaf1f750961b5ed71674", file: "terrain-texture-007.png", assetSHA: "5139e0ac0f4d9373fc2ac98d66379a5fea9cc01a4e9e6fe5291455f6e3a7dcbf"},
	{ordinal: 8, length: 287, encoded: "dd5f241fce90f5c411bc58145db18bc5d1a5348f5eddac5a6f4ba5591bcd0c78", indexed: "f2dabce5c013e1e3092d205d93b1dedb5b2f1077848518441451ac43f948e59b", writes: "907a004630ab11d3e3df1654cda16ebf77b0ce7570dfb9b4d087ec7c4c1968dd", file: "terrain-texture-008.png", assetSHA: "ace86713539fbc3071393d5bae9719bd9bcc4352e04008b55d33b88f57f38eb2"},
	{ordinal: 9, length: 282, encoded: "f693ae1bf22b6f67681581a29448ad07c481c228d4bbb766e4ab760ffabd46c0", indexed: "c56eb09fbfc5b8fa403af835fb230332c327db7669961ef576cf87a70dfb4681", writes: "13711106027d06d76d29347fc868467cad0028efa048e2b8f04db638a2aa95dd", file: "terrain-texture-009.png", assetSHA: "70d84cba2a017956e75114222aab68201c91595aea5519fcc424ea1d3d372f08"},
	{ordinal: 10, length: 263, encoded: "0bec812397cf73ec88ef03ebd8d53429efa2dbc4415189420e0e99a3bc819d23", indexed: "bf261fabd7d38ae671ce75ba94282fb4415670665d19f4907cfd05cf6cd54ff4", writes: "00caa20eb7bed62b7bb4d67fdedbdde3b75dadd30ee4dba699874438de970110", file: "terrain-texture-010.png", assetSHA: "b99151ec34ca369beb34fa41e8fbea3fed582f37b078f3528c955380522c7386"},
	{ordinal: 11, length: 275, encoded: "8570842ee326bec0219f69b162a9b2c29f371abd4531d310a7e10d7274899611", indexed: "81ad65ac9d5126afa62fe6f64fd4a9dc7a13c228f4c24616ea967b26601b2888", writes: "fb28d6d03ff607cb1b776cd46f3cfb8cc44b4d4b2783df7d5ddddff2a286184f", file: "terrain-texture-011.png", assetSHA: "2fbd9b54cff243599b43d441b154da5d1d85aefd2d7cabe0d6e54150c474c562"},
}
var hdTerrainTextureStaticIndices = []byte{7, 8, 18, 19, 20, 21, 35, 36, 37, 38, 39, 49, 50, 56, 57, 58, 59, 60, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 88, 89, 91, 92, 93, 95, 109, 110, 111}
var hdTerrainTextureCycle = [8][3]byte{{11, 15, 37}, {10, 14, 36}, {19, 25, 43}, {20, 26, 44}, {18, 24, 41}, {16, 22, 40}, {14, 19, 39}, {12, 17, 38}}

func loadHDTerrainTextureRuntime(h *hdRuntime, game, dir string) (*hdTerrainTextureRuntime, error) {
	raw, err := hdReadFile(filepath.Join(game, "TERRAIN.SS"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != "a6de9353f2240c214051820369abacf3bb82affbb4736a89c589886fb306f4b6" {
		return nil, fmt.Errorf("terrain original fingerprint")
	}
	p := &hdTerrainTextureRuntime{h: h, owners: map[uint32]hdTerrainTextureCell{}, pending: map[uint32]hdTerrainTexturePair{}, underlays: map[uint32]hdTerrainTextureUnderlay{}, publishedPending: map[int]hdSceneCursorPair{}}
	for _, d := range hdTerrainTextureDefinitions {
		raw, err = hdReadFile(filepath.Join(dir, d.file), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != d.assetSHA {
			return nil, fmt.Errorf("terrain art fingerprint %d", d.ordinal)
		}
		im, err := png.Decode(bytes.NewReader(raw))
		if err != nil {
			return nil, err
		}
		if im.Bounds() != image.Rect(0, 0, 1254, 1254) {
			return nil, fmt.Errorf("terrain art shape")
		}
		f := &hdTerrainTextureFrame{hdTerrainTextureDefinition: d, art: image.NewRGBA(image.Rect(0, 0, 64, 64))}
		for y := 0; y < 64; y++ {
			for x := 0; x < 64; x++ {
				c := color.RGBAModel.Convert(im.At((2*x+1)*1254/128, (2*y+1)*1254/128)).(color.RGBA)
				if c.A != 255 {
					return nil, fmt.Errorf("terrain art alpha")
				}
				f.art.SetRGBA(x, y, c)
			}
		}
		p.frames[d.ordinal] = f
	}
	h.m.WatchWrite(0, 0xaffff, func(_ *golem.Machine, a uint32, old, value byte) { p.memoryWrite(a, old, value) })
	return p, nil
}
func (p *hdTerrainTextureRuntime) beforeInstruction() {
	if p == nil {
		return
	}
	m, c := p.h.m, p.h.m.CPU
	cs, ip := c.Seg[golem.CS], c.IP
	if p.active && cs == p.retCS && ip == p.retIP && c.R[golem.SP] == p.sp+10 {
		p.finish()
	}
	if p.active && (m.Steps-p.start > 100000 || cs == 0xd46 && ip == 0xa) {
		p.active = false
		p.rejected++
	}
	if cs != 0xd46 || ip != 0xa || c.R[golem.AX] < 1 || c.R[golem.AX] > 12 {
		return
	}
	pc := int(cs)*16 + int(ip)
	if !bytes.Equal(m.Mem[pc:pc+12], []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 2}) {
		return
	}
	stack, ok := hdBuildingWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	if !ok || stack[2] != 0 || c.R[golem.DX] != 0 {
		return
	}
	dest, ok := hdBuildingWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok || dest[0] != 16 || dest[1] != 16 {
		return
	}
	recordOff := int(c.R[golem.AX])*12 + int(stack[3]) + 0x36
	if recordOff+12 > 65536 {
		return
	}
	rec, ok := hdBuildingWords(m.Mem, stack[4], uint16(recordOff), 6)
	if !ok || rec[4] != 16 || rec[5] != 16 {
		return
	}
	f := p.frames[int(c.R[golem.AX])-1]
	at := int(rec[1])*16 + int(rec[0])
	if int(rec[0])+f.length > 65536 || at+f.length > len(m.Mem) || hash(m.Mem[at:at+f.length]) != f.encoded {
		return
	}
	base := uint32(dest[3])*16 + uint32(dest[2])
	if base < 32 || base+256+32 >= 0xa0000 {
		return
	}
	p.current, p.base, p.active, p.start, p.retCS, p.retIP, p.sp = f, base, true, m.Steps, stack[1], stack[0], c.R[golem.SP]
	copy(p.guard[:32], m.Mem[base-32:base])
	copy(p.guard[32:], m.Mem[base+256:base+288])
	clear(p.writes[:])
	clear(p.counts[:])
}
func (p *hdTerrainTextureRuntime) finish() {
	p.active = false
	if !bytes.Equal(p.guard[:32], p.h.m.Mem[p.base-32:p.base]) || !bytes.Equal(p.guard[32:], p.h.m.Mem[p.base+256:p.base+288]) {
		p.rejected++
		return
	}
	for k, n := range p.counts {
		if n != 1 || p.h.m.Mem[p.base+uint32(k)] != p.writes[k] {
			p.rejected++
			return
		}
	}
	canonical := make([]byte, 256*3)
	for k, v := range p.writes {
		binary.LittleEndian.PutUint16(canonical[k*3:k*3+2], uint16(k))
		canonical[k*3+2] = v
	}
	if hash(canonical) != p.current.writes {
		p.rejected++
		return
	}
	if hash(p.writes[:]) != p.current.indexed {
		p.rejected++
		return
	}
	for k, v := range p.writes {
		p.owners[p.base+uint32(k)] = hdTerrainTextureCell{local: uint16(k), native: v, slot: uint8(p.current.ordinal + 1)}
	}
	copy(p.current.native[:], p.writes[:])
	p.current.accepted++
	p.accepted++
	p.revision++
}
func (p *hdTerrainTextureRuntime) memoryWrite(addr uint32, old, value byte) {
	if p == nil {
		return
	}
	m := p.h.m
	cs, ip := m.CPU.OpAddr()
	if p.active && cs == 0xd46 {
		if code, known := hdNineWriterCodes[ip]; known {
			pc := int(cs)*16 + int(ip)
			if bytes.Equal(m.Mem[pc:pc+16], code) && (addr < p.base || addr >= p.base+256) {
				p.active = false
				p.rejected++
			}
		}
	}
	if p.active && addr >= p.base && addr < p.base+256 {
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
	if p.accepted > 0 && addr >= 0xa0000 {
		p.publish(addr, old, value)
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
						p.pending[addr] = hdTerrainTexturePair{cell: cell, has: has, old: old, value: value, cursor: k, under: under, hasUnder: hasUnder}
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
				p.underlays[addr] = hdTerrainTextureUnderlay{cell, value}
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
	var cell hdTerrainTextureCell
	known := false
	if code, ok := hdTextureCopyCodes[ip]; (cs == 0xcba || cs == 0xc9f && ip == 0xca) && ok && m.CPU.Flags&0x400 == 0 {
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
	if !known && cs == 0x211 && m.CPU.Flags&0x400 == 0 && addr == uint32(m.CPU.Seg[golem.ES])*16+uint32(m.CPU.R[golem.DI]) {
		codes := map[uint16][]byte{0xa7: {0xf3, 0xa4, 0x03, 0xfa, 0x4b, 0x75, 0xf6, 0x1f, 0x5e, 0x5f, 0xc9, 0xcb, 0x90, 0xc8, 0x0c, 0x00}, 0x112: {0xa4, 0xe2, 0xf6, 0xeb, 0x05, 0x90, 0x47, 0x46, 0xe2, 0xef, 0x03, 0xfa, 0x4b, 0x75, 0xe7, 0x1f}}
		pc := int(cs)*16 + int(ip)
		src := uint32(m.CPU.Seg[golem.DS])*16 + uint32(m.CPU.R[golem.SI])
		if code, ok := codes[ip]; ok && bytes.Equal(m.Mem[pc:pc+16], code) && src < 0xa0000 && m.Mem[src] == value {
			cell, known = p.owners[src]
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

func (p *hdTerrainTextureRuntime) paletteSupported(palette []byte) bool {
	if p == nil || len(palette) != 768 {
		return false
	}
	raw := make([]byte, 0, len(hdTerrainTextureStaticIndices)*4)
	for _, i := range hdTerrainTextureStaticIndices {
		raw = append(raw, i)
		raw = append(raw, palette[int(i)*3:int(i)*3+3]...)
	}
	if hash(raw) != "adcaa5f7f24adf9e35204e87e9f312c48fd1ca0825d3be08f18679eceebdb48c" {
		return false
	}
	for shift := 0; shift < 8; shift++ {
		ok := true
		for i := 0; i < 8; i++ {
			at := (120 + i) * 3
			want := hdTerrainTextureCycle[(i+shift)%8]
			if palette[at] != want[0] || palette[at+1] != want[1] || palette[at+2] != want[2] {
				ok = false
				break
			}
		}
		if ok {
			return true
		}
	}
	return false
}
func (p *hdTerrainTextureRuntime) nativeCell(slot uint8, local uint16) (byte, bool) {
	if slot < 1 || slot > 12 || local >= 256 {
		return 0, false
	}
	f := p.frames[slot-1]
	if f == nil || f.accepted == 0 {
		return 0, false
	}
	return f.native[local], true
}
func (p *hdTerrainTextureRuntime) paintCell(out *image.RGBA, at int, slot uint8, local uint16, palette []byte) {
	f := p.frames[slot-1]
	sx, sy := int(local)%16*4, int(local)/16*4
	var delta [3]int
	v := f.native[local]
	if v >= 120 && v < 128 {
		canon := hdTerrainTextureCycle[v-120]
		for i := 0; i < 3; i++ {
			a, b := palette[int(v)*3+i], canon[i]
			delta[i] = int(a<<2|a>>4) - int(b<<2|b>>4)
		}
	}
	clamp := func(v int) byte {
		if v < 0 {
			return 0
		}
		if v > 255 {
			return 255
		}
		return byte(v)
	}
	x, y := at%320*4, at/320*4
	for j := 0; j < 4; j++ {
		for i := 0; i < 4; i++ {
			c := f.art.RGBAAt(sx+i, sy+j)
			c.R = clamp(int(c.R) + delta[0])
			c.G = clamp(int(c.G) + delta[1])
			c.B = clamp(int(c.B) + delta[2])
			out.SetRGBA(x+i, y+j, c)
		}
	}
}
func (p *hdTerrainTextureRuntime) paint(out *image.RGBA, f draftNativeFrame) map[string]any {
	mask := make([]byte, 8000)
	painted := 0
	by := map[int]int{}
	supported := p.paletteSupported(f.palette)
	if supported && f.mode == 0x13 && len(f.canvas) == 64000 {
		for a, c := range p.owners {
			if a < hdBuildingCanvas || a >= hdBuildingCanvas+64000 {
				continue
			}
			at := int(a - hdBuildingCanvas)
			v, ok := p.nativeCell(uint8(c.slot), c.local)
			if !ok || v != c.native || f.canvas[at] != c.native {
				continue
			}
			p.paintCell(out, at, uint8(c.slot), c.local, f.palette)
			mask[at>>3] |= 1 << uint(at&7)
			painted++
			by[int(c.slot)-1]++
		}
	}
	return map[string]any{"prototype": false, "formal": true, "painted": painted, "by_source": by, "mask": mask, "accepted": p.accepted, "rejected": p.rejected, "transferred": p.transferred, "revoked": p.revoked, "palette_supported": supported, "revision": p.revision, "cursor_source_restores": p.cursorRestores}
}
func (p *hdTerrainTextureRuntime) paintBackground(out *image.RGBA, f draftNativeFrame, pos int, value byte, palette []byte) bool {
	if pos < 0 || pos >= 64000 || len(f.canvas) != 64000 || !p.paletteSupported(palette) {
		return false
	}
	addr := hdBuildingCanvas + uint32(pos)
	c, ok := p.owners[addr]
	if ok {
		ok = f.canvas[pos] == c.native
	} else if u, known := p.underlays[addr]; known && f.canvas[pos] == u.glyph {
		c, ok = u.cell, true
	}
	if !ok || c.native != value {
		return false
	}
	v, valid := p.nativeCell(uint8(c.slot), c.local)
	if !valid || v != value {
		return false
	}
	p.paintCell(out, pos, uint8(c.slot), c.local, palette)
	return true
}
func (p *hdTerrainTextureRuntime) mainCell(at int) hdSceneCell {
	addr := hdBuildingCanvas + uint32(at)
	if cell, ok := p.owners[addr]; ok {
		return hdSceneCell{slot: uint16(cell.slot), local: cell.local, value: cell.native}
	}
	if under, ok := p.underlays[addr]; ok {
		return hdSceneCell{slot: uint16(under.cell.slot), local: under.cell.local, value: under.glyph, glyph: true}
	}
	return hdSceneCell{}
}
func (p *hdTerrainTextureRuntime) validPublishedCell(c hdSceneCell) bool {
	if c.slot > 255 {
		return false
	}
	v, ok := p.nativeCell(uint8(c.slot), c.local)
	return ok && (c.glyph || v == c.value)
}
func (p *hdTerrainTextureRuntime) publish(a uint32, oldValue, value byte) {
	if p.publicationBlocked || a < 0xa0000 || a >= 0xa0000+64000 {
		return
	}
	at := int(a - 0xa0000)
	oldCell := p.published[at]
	p.published[at] = hdSceneCell{}
	pair, paired := p.publishedPending[at]
	delete(p.publishedPending, at)
	m, c := p.h.m, p.h.m.CPU
	cs, ip := c.OpAddr()
	pc := int(cs)*16 + int(ip)
	delta := int(a) - (int(c.Seg[golem.ES])*16 + int(c.R[golem.DI]))
	sourceOffset := int(c.R[golem.SI]) + delta
	cursorCode := []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 3, 0xf3, 3, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}
	if cs == 0xb68 && ip == 0x51c && c.Seg[golem.DS] == 0xa000 && c.Seg[golem.ES] == 0xa000 &&
		delta == 0 && sourceOffset >= 0xfa00 && sourceOffset < 0xfc00 && pc+16 <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+16], cursorCode) {
		if source, known := p.h.cursorSource(); known && m.Mem[0xa0000+sourceOffset] == value {
			k := sourceOffset & 255
			back, composed := m.Mem[0xafa00+k], m.Mem[0xafb00+k]
			if sourceOffset >= 0xfb00 && back == oldValue && composed == value && (source[k] == 255 && value == back || source[k] != 255 && value == source[k]) {
				if source[k] == 255 && oldValue == value && oldCell.slot != 0 && oldCell.value == value {
					p.published[at] = oldCell
				} else if source[k] != 255 && oldCell.slot != 0 && oldCell.value == oldValue {
					p.publishedPending[at] = hdSceneCursorPair{old: oldValue, value: value, k: k, cell: oldCell}
				}
			} else if sourceOffset < 0xfb00 && back == value {
				if source[k] == 255 && composed == oldValue && oldValue == value && oldCell.slot != 0 && oldCell.value == value {
					p.published[at] = oldCell
				} else if paired && pair.old == value && pair.value == oldValue && pair.k == k && composed == oldValue && source[k] == oldValue {
					p.published[at] = pair.cell
				}
			}
		}
	}
	if len(p.publishedPending) > 256 {
		p.publicationBlocked = true
		clear(p.published[:])
		clear(p.publishedPending)
	}
	if cs == 0xe21 && ip == 0x91 && c.Seg[golem.ES] == 0xa000 && pc >= 0 && pc+len(hdSceneVGACopyCode) <= len(m.Mem) && bytes.Equal(m.Mem[pc:pc+len(hdSceneVGACopyCode)], hdSceneVGACopyCode) {
		src := int(c.Seg[golem.DS])*16 + int(c.R[golem.SI]) + delta
		if delta >= 0 && delta < 2 && int(c.R[golem.SI])+delta < 65536 && int(c.R[golem.DI])+delta < 64000 && src == int(hdBuildingCanvas)+at && src < len(m.Mem) && m.Mem[src] == value {
			cell := p.mainCell(at)
			if p.validPublishedCell(cell) && cell.value == value {
				p.published[at] = cell
			}
		}
	}
	if oldCell != p.published[at] {
		p.revision++
	}
}

func (p *hdTerrainTextureRuntime) paintPublished(out *image.RGBA, f draftNativeFrame) map[string]any {
	mask := make([]byte, 8000)
	r := map[string]any{"formal": true, "prototype": false, "surface": "published-vga", "painted": 0, "mask": mask, "palette_supported": false}
	if p != nil {
		r["palette_supported"] = p.paletteSupported(f.palette)
	}
	if p == nil || p.publicationBlocked || f.mode != 0x13 || len(f.canvas) != 64000 || len(f.indexed) != 64000 || len(f.palette) != 768 || f.cursor.Dx() != 16 || f.cursor.Dy() != 16 || len(p.h.m.Mem) < 0xa0000+64000 || !bytes.Equal(p.h.m.Mem[0xa0000:0xa0000+64000], f.indexed) {
		r["reason"] = "unverified-vga-surface"
		return r
	}
	source, reason := p.h.cursorProof(f)
	if reason != "" && !strings.HasPrefix(reason, "outside-cursor:") {
		r["reason"] = "unverified-cursor"
		return r
	}
	if source == nil {
		source, _ = p.h.cursorSource()
	}
	count := 0
	if p.paletteSupported(f.palette) {
		for at, c := range p.published {
			if !p.validPublishedCell(c) || c.glyph || c.value != f.indexed[at] || (image.Pt(at%320, at/320).In(f.cursor) && source[(at/320-f.cursor.Min.Y)*16+at%320-f.cursor.Min.X] != 255) {
				continue
			}
			p.paintCell(out, at, uint8(c.slot), c.local, f.palette)
			mask[at>>3] |= 1 << uint(at&7)
			count++
		}
	}
	r["painted"], r["reason"] = count, "published-texture-background-only"
	return r
}
func (p *hdTerrainTextureRuntime) paintPublishedBackground(out *image.RGBA, f draftNativeFrame, pos int, value byte, palette []byte) bool {
	if p == nil || p.publicationBlocked || pos < 0 || pos >= 64000 || f.mode != 0x13 || len(f.indexed) != 64000 || len(f.canvas) != 64000 || len(p.h.m.Mem) < 0xa0000+64000 {
		return false
	}
	c := p.published[pos]
	if !p.validPublishedCell(c) || c.value != f.indexed[pos] || p.h.m.Mem[0xa0000+pos] != c.value || func() bool { v, ok := p.nativeCell(uint8(c.slot), c.local); return !ok || v != value }() || !p.paletteSupported(palette) {
		return false
	}
	p.paintCell(out, pos, uint8(c.slot), c.local, palette)
	return true
}
