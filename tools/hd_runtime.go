// 規格061／062／063 READY：已驗建築、海洋與人物的HD顯示層；不寫入DOS。
package main

import (
	"bytes"
	"encoding/binary"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/draw"
	"image/png"
	"io"
	"os"
	"path/filepath"

	golem "github.com/wicanr2/dosgolem"
)

var hdAssets = flag.String("hd-assets", "", "已驗HD生成素材目錄；缺件時保留原版")

const hdAssetSHA = "c33885bd2570cc5ec0eb204aece69f1363b66fab5c1f16da82786f3b7e5139d8"
const hdBuildingFileSHA = "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4"

func hdReadFile(path string, limit int64) ([]byte, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > limit {
		return nil, fmt.Errorf("HD resource is not a bounded regular file: %s", path)
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	raw, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil {
		return nil, err
	}
	if int64(len(raw)) > limit {
		return nil, fmt.Errorf("HD resource too large: %s", path)
	}
	return raw, nil
}

func loadHDRuntime(m *golem.Machine, game, directory string) (*hdRuntime, error) {
	if directory == "" {
		return nil, fmt.Errorf("HD assets not installed")
	}
	info, err := os.Lstat(directory)
	if err != nil {
		return nil, err
	}
	if !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		return nil, fmt.Errorf("HD asset directory is not a real directory")
	}
	manifest, err := hdReadFile(filepath.Join(directory, "manifest.json"), 16<<20)
	if err != nil {
		return nil, err
	}
	if hash(manifest) != hdManifestSHA {
		return nil, fmt.Errorf("HD manifest fingerprint mismatch")
	}
	for name, want := range map[string]string{"VICEROY.EXE": versions["VICEROY.EXE"], "BUILDING.SS": hdBuildingFileSHA} {
		raw, err := hdReadFile(filepath.Join(game, name), 8<<20)
		if err != nil {
			return nil, err
		}
		if hash(raw) != want {
			return nil, fmt.Errorf("HD original fingerprint mismatch: %s", name)
		}
	}
	raw, err := hdReadFile(filepath.Join(directory, "building-032.png"), 8<<20)
	if err != nil {
		return nil, err
	}
	if hash(raw) != hdAssetSHA {
		return nil, fmt.Errorf("HD asset fingerprint mismatch")
	}
	im, err := png.Decode(bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	if im.Bounds() != image.Rect(0, 0, 1158, 1359) {
		return nil, fmt.Errorf("HD asset dimensions mismatch")
	}
	art := image.NewRGBA(image.Rect(0, 0, 92, 108))
	for y := 0; y < 108; y++ {
		for x := 0; x < 92; x++ {
			sx, sy := (2*x+1)*1158/(2*92), (2*y+1)*1359/(2*108)
			art.SetRGBA(x, y, color.RGBAModel.Convert(im.At(sx, sy)).(color.RGBA))
		}
	}
	h := &hdRuntime{m: m, art: art, pending: map[int]hdBuildingPixel{}}
	h.opening, err = loadHDOpeningRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.cursor, err = loadHDCursorRuntime(game, directory)
	if err != nil {
		return nil, err
	}
	h.texture, err = loadHDTextureRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.worldTexture, err = loadHDTextureVariant(h, game, directory, true)
	if err != nil {
		return nil, err
	}
	h.newGame, err = loadHDNewGameRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.scenes, err = loadHDSceneRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.royal, err = loadHDRoyalRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.parch, err = loadHDTextureKind(h, game, directory, "parch")
	if err != nil {
		return nil, err
	}
	h.terrainTextures, err = loadHDTerrainTextureRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}

	h.smallTerrain, err = loadHDSmallTerrainRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.terrainBatch, err = loadHDTerrainBatchRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.terrain079, err = loadHDTerrain079Runtime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.sea, err = loadHDSeaRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	m.WatchWrite(hdBuildingCanvas, hdBuildingCanvas+63999, func(_ *golem.Machine, a uint32, old, value byte) { h.write(a, old, value) })
	h.person, err = loadHDPersonRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.shelter, err = loadHDShelterRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.nine, err = loadHDNineRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	h.small, err = loadHDSmallRuntime(h, game, directory)
	if err != nil {
		return nil, err
	}
	return h, nil
}

// 僅正規化本次啟動選項；不保存、不提交，也不把其他準備錯誤當成素材缺件。
func hdStartupOptions(h *hdRuntime, options displayOptions) displayOptions {
	if h == nil && options.Graphics == "hd" {
		options.Graphics = "original"
	}
	return options
}

const hdManifestSHA = "b2cff76717ebcd1bbdc9568a9c9a7dc3107edb945fc5511791dd08bea41bd10e"

const hdBuildingSourceSHA = "7c34170632e995ebfb281e451f340d14faec5fa25970ca0479493d99758afb2a"
const hdBuildingOpaqueSHA = "1c5978b8b131150ba8abecca42a240282344553352195d683ad827e51b4fbef1"
const hdBuildingCursorSHA = "47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03"
const hdBuildingCanvas = uint32(0x2cae0)

type hdBuildingPixel struct {
	old, value  byte
	owned       bool
	cursorIndex int
}
type hdRuntime struct {
	terrainTextures *hdTerrainTextureRuntime
	opening         *hdOpeningRuntime
	royal           *hdRoyalRuntime
	scenes          *hdSceneRuntime
	newGame         *hdNewGameRuntime

	parch                                            *hdTextureRuntime
	worldTexture                                     *hdTextureRuntime
	texture                                          *hdTextureRuntime
	smallTerrain                                     *hdSmallTerrainRuntime
	terrainBatch                                     *hdTerrainBatchRuntime
	cursor                                           *hdCursorRuntime
	terrain079                                       *hdTerrain079Runtime
	small                                            *hdSmallRuntime
	nine                                             *hdNineRuntime
	shelter                                          *hdShelterRuntime
	person                                           *hdPersonRuntime
	sea                                              *hdSeaRuntime
	m                                                *golem.Machine
	art                                              *image.RGBA
	owned                                            [621]bool
	opaque                                           [621]bool
	background, after                                [621]byte
	pending                                          map[int]hdBuildingPixel
	active                                           bool
	retCS, retIP, sp                                 uint16
	start, revision                                  uint64
	before                                           [621]byte
	writes                                           map[int]byte
	counts                                           map[int]int
	outside                                          bool
	accepted, rejected, cursorPaints, cursorRestores uint64
}

func hdBuildingIndex(addr uint32) (int, bool) {
	if addr < hdBuildingCanvas || addr >= hdBuildingCanvas+64000 {
		return 0, false
	}
	i := int(addr - hdBuildingCanvas)
	x, y := i%320, i/320
	if x < 56 || x >= 79 || y < 13 || y >= 40 {
		return 0, false
	}
	return (y-13)*23 + x - 56, true
}
func hdBuildingCanvasIndex(i int) int { return (13+i/23)*320 + 56 + i%23 }
func hdBuildingRegion(mem []byte) (out [621]byte) {
	for i := range out {
		out[i] = mem[int(hdBuildingCanvas)+hdBuildingCanvasIndex(i)]
	}
	return
}
func hdBuildingWords(mem []byte, seg, off uint16, n int) ([]uint16, bool) {
	at := int(seg)*16 + int(off)
	if int(off)+n*2 > 65536 || at+n*2 > len(mem) {
		return nil, false
	}
	words := make([]uint16, n)
	for i := range words {
		words[i] = binary.LittleEndian.Uint16(mem[at+i*2 : at+i*2+2])
	}
	return words, true
}
func (h *hdRuntime) baseKey() string {
	if h == nil {
		return ""
	}
	if h.sea != nil {
		if h.person != nil {
			if h.shelter != nil {
				if h.nine != nil {
					return fmt.Sprintf("/hd/%d/sea/%d/person/%d/shelter/%d/nine/%d", h.revision, h.sea.revision, h.person.revision, h.shelter.revision, h.nine.revision)
				}
				return fmt.Sprintf("/hd/%d/sea/%d/person/%d/shelter/%d", h.revision, h.sea.revision, h.person.revision, h.shelter.revision)
			}
			return fmt.Sprintf("/hd/%d/sea/%d/person/%d", h.revision, h.sea.revision, h.person.revision)
		}
		return fmt.Sprintf("/hd/%d/sea/%d", h.revision, h.sea.revision)
	}
	return fmt.Sprintf("/hd/%d", h.revision)
}
func (h *hdRuntime) beforeInstruction() {
	if h == nil {
		return
	}
	if h.opening != nil {
		h.opening.sprites.beforeInstruction()
	}
	if h.scenes != nil {
		h.scenes.beforeSpriteInstruction()
	}
	h.sea.beforeInstruction()
	h.terrain079.beforeInstruction()
	h.terrainBatch.beforeInstruction()
	h.smallTerrain.beforeInstruction()
	h.texture.beforeInstruction()
	h.worldTexture.beforeInstruction()
	h.parch.beforeInstruction()
	h.terrainTextures.beforeInstruction()
	h.person.beforeInstruction()
	h.shelter.beforeInstruction()
	h.nine.beforeInstruction()
	h.small.beforeInstruction()
	h.royal.beforeInstruction()
	m := h.m
	c := m.CPU
	cs, ip := c.Seg[golem.CS], c.IP
	if h.active && (m.Steps-h.start > 100000 || (cs == 0xd46 && ip == 0xa)) {
		h.active = false
		h.rejected++
	}
	if h.active && cs == h.retCS && ip == h.retIP && c.R[golem.SP] == h.sp+10 {
		h.finish()
	}
	if cs != 0xd46 || ip != 0xa || c.R[golem.AX] != 33 || c.R[golem.DX] != 56 {
		return
	}
	pc := int(cs)*16 + int(ip)
	prefix := []byte{0xc8, 0x28, 0, 0, 0x52, 0x53, 0x50, 0x57, 0x56, 0x8b, 0x47, 0x02}
	if !bytes.Equal(m.Mem[pc:pc+len(prefix)], prefix) {
		h.rejected++
		return
	}
	stack, ok := hdBuildingWords(m.Mem, c.Seg[golem.SS], c.R[golem.SP], 5)
	if !ok || stack[2] != 13 {
		return
	}
	dest, ok := hdBuildingWords(m.Mem, c.Seg[golem.DS], c.R[golem.BX], 4)
	if !ok || dest[0] != 200 || dest[1] != 320 || uint32(dest[3])*16+uint32(dest[2]) != hdBuildingCanvas {
		return
	}
	off := uint16(33*12 + uint32(stack[3]) + 0x36)
	record, ok := hdBuildingWords(m.Mem, stack[4], off, 6)
	if !ok || record[4] != 23 || record[5] != 27 {
		return
	}
	at := int(record[1])*16 + int(record[0])
	if int(record[0])+534 > 65536 || at+534 > len(m.Mem) || hash(m.Mem[at:at+534]) != hdBuildingSourceSHA {
		h.rejected++
		return
	}
	h.active = true
	h.start = m.Steps
	h.retCS, h.retIP, h.sp = stack[1], stack[0], c.R[golem.SP]
	h.before = hdBuildingRegion(m.Mem)
	h.writes = map[int]byte{}
	h.counts = map[int]int{}
	h.outside = false
}
func (h *hdRuntime) finish() {
	h.active = false
	var encoded []byte
	for i := 0; i < 621; i++ {
		if v, ok := h.writes[i]; ok {
			if h.counts[i] != 1 {
				h.rejected++
				return
			}
			encoded = append(encoded, byte(i), byte(i>>8), v)
		}
	}
	current := hdBuildingRegion(h.m.Mem)
	if h.outside || len(h.writes) != 440 || hash(encoded) != hdBuildingOpaqueSHA {
		h.rejected++
		return
	}
	for i, v := range current {
		expected := h.before[i]
		if n, ok := h.writes[i]; ok {
			expected = n
		}
		if v != expected {
			h.rejected++
			return
		}
	}
	h.background, h.after = h.before, current
	for i := range h.owned {
		_, h.opaque[i] = h.writes[i]
		h.owned[i] = true
	}
	h.pending = map[int]hdBuildingPixel{}
	h.accepted++
	h.revision++
}
func (h *hdRuntime) cursorSource() ([]byte, bool) {
	if len(h.m.Mem) < 0xafe00 {
		return nil, false
	}
	source := h.m.Mem[0x1cd74:0x1ce74]
	return source, hash(source) == hdBuildingCursorSHA
}
func (h *hdRuntime) write(addr uint32, old, value byte) {
	i, inside := hdBuildingIndex(addr)
	if h.active {
		if !inside {
			h.outside = true
		} else {
			h.counts[i]++
			h.writes[i] = value
		}
	}
	if !inside {
		return
	}
	h.revision++
	cs, ip := h.m.CPU.OpAddr()
	if cs == 0xb68 && ip == 0x51c && h.m.CPU.Seg[golem.DS] == 0xa000 && h.m.CPU.Seg[golem.ES] == 0x2cae {
		pc := int(cs)*16 + int(ip)
		code := []byte{0xf3, 0xa4, 0x8a, 0xc8, 0x2b, 0xf9, 0x2b, 0xf1, 0x03, 0xf3, 0x03, 0xfa, 0xfe, 0xcc, 0x75, 0xf0}
		if bytes.Equal(h.m.Mem[pc:pc+16], code) {
			c := h.m.CPU
			at := uint32(c.Seg[golem.ES])*16 + uint32(c.R[golem.DI])
			sourceOffset := int(c.R[golem.SI]) + int(int64(addr)-int64(at))
			if _, ok := h.cursorSource(); ok && sourceOffset >= 0xfa00 && sourceOffset < 0xfc00 &&
				h.m.Mem[0xa0000+sourceOffset] == value {
				k := sourceOffset & 255
				if sourceOffset >= 0xfb00 {
					h.pending[i] = hdBuildingPixel{old, value, h.owned[i], k}
					h.owned[i] = false
					h.cursorPaints++
					return
				}
				prior, ok := h.pending[i]
				delete(h.pending, i)
				if ok && prior.cursorIndex == k && old == prior.value && value == prior.old {
					h.owned[i] = prior.owned
					h.cursorRestores++
					return
				}
			}
		}
	}
	h.owned[i] = false
	// 任何其他矩形寫入使未完成游標配對失效，不能還原過期擁有權。
	clear(h.pending)
}
func (h *hdRuntime) cursorValid(f draftNativeFrame) ([]byte, bool) {
	source, reason := h.cursorProof(f)
	return source, reason == ""
}
func (h *hdRuntime) cursorPixelsProof(f draftNativeFrame) ([]byte, string) {
	source, ok := h.cursorSource()
	if !ok {
		return nil, "source"
	}
	if f.mode != 0x13 || f.cursor.Dx() != 16 || f.cursor.Dy() != 16 {
		return nil, "mode-or-size"
	}
	tail := h.m.Mem[0xafa00:0xafc00]
	for k, v := range source {
		expected := v
		if v == 255 {
			expected = tail[k]
		}
		if tail[256+k] != expected {
			return nil, fmt.Sprintf("cursor-composition:%d", k)
		}
		x, y := f.cursor.Min.X+k%16, f.cursor.Min.Y+k/16
		if x < 0 || y < 0 || x >= 320 || y >= 200 {
			continue
		}
		i := y*320 + x
		if f.canvas[i] != tail[k] {
			return nil, fmt.Sprintf("cursor-background:%d", k)
		}
		if f.indexed[i] != tail[256+k] {
			return nil, fmt.Sprintf("cursor-indexed:%d", k)
		}
	}
	return source, ""
}
func (h *hdRuntime) cursorProof(f draftNativeFrame) ([]byte, string) {
	source, reason := h.cursorPixelsProof(f)
	if reason != "" {
		return nil, reason
	}
	for i, v := range f.indexed {
		if !image.Pt(i%320, i/320).In(f.cursor) && v != f.canvas[i] {
			return nil, fmt.Sprintf("outside-cursor:%d", i)
		}
	}
	return source, ""
}
func (h *hdRuntime) baseExisting(f draftNativeFrame) (*image.RGBA, map[string]any) {
	out := draftRGB(f.indexed, f.palette)
	receipt := map[string]any{"formal": true, "asset": "building-032", "accepted": h.accepted, "rejected": h.rejected,
		"cursor_paint_points": h.cursorPaints, "cursor_restore_points": h.cursorRestores, "owned": 0, "painted": 0}
	_, reason := h.cursorProof(f)
	if reason != "" {
		receipt["reason"] = "unverified-cursor-or-native-surface"
		receipt["cursor_reject"] = reason
		return out, receipt
	}
	if h.scenes != nil {
		receipt["scene_picture"] = h.scenes.paint(out, f)
	}
	if h.sea != nil {
		receipt["sea"] = h.sea.paint(out, f)
	}
	if h.terrain079 != nil {
		receipt["terrain079"] = h.terrain079.paint(out, f)
	}
	if h.terrainBatch != nil {
		receipt["terrain_batch"] = h.terrainBatch.paint(out, f)
	}
	if h.smallTerrain != nil {
		receipt["small_terrain"] = h.smallTerrain.paint(out, f)
	}
	owned, painted := 0, 0
	for i, v := range h.owned {
		if !v {
			continue
		}
		owned++
		pos := hdBuildingCanvasIndex(i)
		if f.canvas[pos] != h.after[i] {
			continue
		}
		if h.opaque[i] {
			draftPaintPixel(out, pos, h.background[i], f.palette)
		}
		x, y := i%23*4, i/23*4
		rect := image.Rect(224+x, 52+y, 228+x, 56+y)
		draw.Draw(out, rect, h.art, image.Pt(x, y), draw.Over)
		painted++
	}
	if h.shelter != nil {
		receipt["shelter"] = h.shelter.paint(out, f)
	}
	if h.nine != nil {
		receipt["nine"] = h.nine.paint(out, f)
	}
	if h.small != nil {
		receipt["small"] = h.small.paint(out, f)
	}
	if h.person != nil {
		receipt["person"] = h.person.paint(out, f)
	}
	receipt["owned"], receipt["painted"], receipt["reason"] = owned, painted, "known-building"
	return out, receipt
}
func (h *hdRuntime) restoreCursor(out *image.RGBA, f draftNativeFrame) {
	source, ok := h.cursorValid(f)
	if !ok {
		return
	}
	for k, v := range source {
		if v == 255 {
			continue
		}
		x, y := f.cursor.Min.X+k%16, f.cursor.Min.Y+k/16
		if x >= 0 && y >= 0 && x < 320 && y < 200 {
			draftPaintPixel(out, y*320+x, f.indexed[y*320+x], f.palette)
		}
	}
}
func (b *draftLanguageBackend) rebuildWithHD(t *draftLanguageTarget, o displayOptions, f draftNativeFrame) (*image.RGBA, map[string]any, error) {
	if len(f.canvas) != 64000 || len(f.buffer) != 64000 || len(f.indexed) != 64000 || len(f.palette) != 768 {
		return nil, nil, fmt.Errorf("invalid native frame")
	}
	if o.Graphics != "hd" {
		return draftRebuildTarget(t, f.journal, f.canvas, f.buffer, f.indexed, f.palette, f.cursor, f.step, f.mode)
	}
	if b.hd == nil {
		return nil, nil, fmt.Errorf("ui.error.unavailable")
	}
	base, hd := b.hd.base(f)
	if hd["reason"] == "unverified-cursor-or-native-surface" && b.hd.scenes != nil {
		hd["published_scene_picture"] = b.hd.scenes.paintPublished(base, f)
	}
	if hd["reason"] == "unverified-cursor-or-native-surface" {
		for key, p := range map[string]*hdTextureRuntime{"published_texture": b.hd.texture, "published_world_texture": b.hd.worldTexture, "published_parch": b.hd.parch} {
			if p != nil {
				hd[key] = p.paintPublished(base, f)
			}
		}
	}
	if hd["reason"] == "unverified-cursor-or-native-surface" && b.hd.terrainTextures != nil {
		hd["published_terrain_texture"] = b.hd.terrainTextures.paintPublished(base, f)
	}
	if b.hd.royal != nil {
		hd["royal"] = b.hd.royal.paint(base, f)
	}
	var hdBG draftHDBackground
	terrainBGMask := make([]byte, 8000)
	terrainBGPainted := 0
	publishedTerrainBGMask := make([]byte, 8000)
	publishedTerrainBGPainted := 0
	bgMask := make([]byte, 8000)
	bgPainted := 0
	worldBGMask := make([]byte, 8000)
	worldBGPainted := 0
	newGameBGMask := make([]byte, 8000)
	newGameBGPainted := 0
	parchBGMask := make([]byte, 8000)
	parchBGPainted := 0
	sceneBGMask := make([]byte, 8000)
	sceneBGPainted := 0
	publishedBGMask := make([]byte, 8000)
	publishedBGPainted := 0
	if hd["reason"] != "unverified-cursor-or-native-surface" && ((b.hd.terrainTextures != nil && b.hd.terrainTextures.paletteSupported(f.palette)) || (b.hd.scenes != nil) || (b.hd.newGame != nil && b.hd.newGame.frame != nil) || (b.hd.texture != nil && b.hd.texture.paletteSupported(f.palette)) || (b.hd.worldTexture != nil && b.hd.worldTexture.paletteSupported(f.palette)) || (b.hd.parch != nil && b.hd.parch.paletteSupported(f.palette))) {
		hdBG = func(out *image.RGBA, i int, v byte, palette []byte) bool {
			if b.hd.terrainTextures != nil && b.hd.terrainTextures.paintBackground(out, f, i, v, palette) {
				terrainBGMask[i>>3] |= 1 << uint(i&7)
				terrainBGPainted++
				return true
			}
			if b.hd.scenes != nil && b.hd.scenes.paintBackground(out, f, i, v, palette) {
				sceneBGMask[i>>3] |= 1 << uint(i&7)
				sceneBGPainted++
				return true
			}
			if b.hd.newGame != nil && b.hd.newGame.paintBackground(out, f, i, v, palette) {
				newGameBGMask[i>>3] |= 1 << uint(i&7)
				newGameBGPainted++
				return true
			}
			if b.hd.parch != nil && b.hd.parch.paintBackground(out, f, i, v, palette) {
				parchBGMask[i>>3] |= 1 << uint(i&7)
				parchBGPainted++
				return true
			}

			if b.hd.worldTexture != nil && b.hd.worldTexture.paintBackground(out, f, i, v, palette) {
				worldBGMask[i>>3] |= 1 << uint(i&7)
				worldBGPainted++
				return true
			}
			if b.hd.texture == nil {
				return false
			}
			ok := b.hd.texture.paintBackground(out, f, i, v, palette)
			if ok {
				bgMask[i>>3] |= 1 << uint(i&7)
				bgPainted++
			}
			return ok
		}
	}
	if hdBG == nil && b.hd.scenes != nil {
		if group, ok := hd["published_scene_picture"].(map[string]any); ok && group["reason"] == "published-scene-background-only" {
			hdBG = func(out *image.RGBA, pos int, value byte, palette []byte) bool {
				if b.hd.scenes.paintPublishedBackground(out, f, pos, value, palette) {
					publishedBGMask[pos>>3] |= 1 << uint(pos&7)
					publishedBGPainted++
					return true
				}
				return false
			}
		}
	}
	if hd["reason"] == "unverified-cursor-or-native-surface" {
		for _, v := range []struct {
			key   string
			p     *hdTextureRuntime
			mask  []byte
			count *int
		}{
			{"published_texture", b.hd.texture, bgMask, &bgPainted},
			{"published_world_texture", b.hd.worldTexture, worldBGMask, &worldBGPainted},
			{"published_parch", b.hd.parch, parchBGMask, &parchBGPainted},
		} {
			v := v
			if group, ok := hd[v.key].(map[string]any); ok && group["reason"] == "published-texture-background-only" {
				previous := hdBG
				hdBG = func(out *image.RGBA, pos int, value byte, palette []byte) bool {
					if previous != nil && previous(out, pos, value, palette) {
						return true
					}
					if v.p.paintPublishedBackground(out, f, pos, value, palette) {
						v.mask[pos>>3] |= 1 << uint(pos&7)
						*v.count++
						return true
					}
					return false
				}
			}
		}
	}
	if hd["reason"] == "unverified-cursor-or-native-surface" && b.hd.terrainTextures != nil {
		if group, ok := hd["published_terrain_texture"].(map[string]any); ok && group["reason"] == "published-texture-background-only" {
			previous := hdBG
			hdBG = func(out *image.RGBA, pos int, value byte, palette []byte) bool {
				if previous != nil && previous(out, pos, value, palette) {
					return true
				}
				if b.hd.terrainTextures.paintPublishedBackground(out, f, pos, value, palette) {
					publishedTerrainBGMask[pos>>3] |= 1 << uint(pos&7)
					publishedTerrainBGPainted++
					return true
				}
				return false
			}
		}
	}
	nativeCursorBackgroundMask := make([]byte, 8000)
	nativeCursorBackgroundPainted := 0
	if hdBG != nil {
		cursorSource, cursorReason := b.hd.cursorPixelsProof(f)
		cursorVerified := cursorReason == "" && len(b.hd.m.Mem) >= 0xa0000+64000 && bytes.Equal(b.hd.m.Mem[0xa0000:0xa0000+64000], f.indexed)
		background := hdBG
		hdBG = func(out *image.RGBA, pos int, value byte, palette []byte) bool {
			if background(out, pos, value, palette) {
				return true
			}
			if cursorVerified && pos >= 0 && pos < 64000 && image.Pt(pos%320, pos/320).In(f.cursor) && cursorSource[(pos/320-f.cursor.Min.Y)*16+pos%320-f.cursor.Min.X] == 255 {
				draftPaintPixel(out, pos, value, palette)
				nativeCursorBackgroundMask[pos>>3] |= 1 << uint(pos&7)
				nativeCursorBackgroundPainted++
				return true
			}
			return false
		}
	}
	out, record, err := draftRebuildTargetOn(t, f.journal, f.canvas, f.buffer, f.indexed, f.palette, f.cursor, f.step, f.mode, base, hdBG)
	if group, ok := hd["published_scene_picture"].(map[string]any); ok {
		group["background_repaints"] = publishedBGPainted
		group["background_mask"] = publishedBGMask
	}
	if group, ok := hd["scene_picture"].(map[string]any); ok {
		group["background_repaints"] = sceneBGPainted
		group["background_mask"] = sceneBGMask
	}
	if texture, ok := hd["texture"].(map[string]any); ok {
		texture["background_repaints"] = bgPainted
		texture["background_mask"] = bgMask
	}
	if group, ok := hd["world_texture"].(map[string]any); ok {
		group["background_repaints"] = worldBGPainted
		group["background_mask"] = worldBGMask
	}
	if group, ok := hd["new_game_picture"].(map[string]any); ok {
		group["background_repaints"] = newGameBGPainted
		group["background_mask"] = newGameBGMask
	}
	if group, ok := hd["parch"].(map[string]any); ok {
		group["background_repaints"] = parchBGPainted
		group["background_mask"] = parchBGMask
	}
	for _, v := range []struct {
		key   string
		mask  []byte
		count int
	}{
		{"published_texture", bgMask, bgPainted}, {"published_world_texture", worldBGMask, worldBGPainted}, {"published_parch", parchBGMask, parchBGPainted},
	} {
		if g, ok := hd[v.key].(map[string]any); ok {
			g["background_mask"], g["background_repaints"] = v.mask, v.count
		}
	}
	if err != nil {
		return nil, nil, err
	}
	b.hd.restoreCursor(out, f)
	if b.hd.cursor != nil {
		hd["cursor"] = b.hd.cursor.paint(b.hd, out, f)
	}
	// 規格069 R85 READY：有效文字矩形皆在滑鼠框外時，恢復框內已驗開場來源。
	// 共用語言引擎的VICEROY畫布在OPENING階段不能用於判定游標。
	items, itemsKnown := record["items"].([]map[string]any)
	if b.hd.opening != nil && itemsKnown && hdOpeningCursorUncovered(f.cursor, items) {
		if b.hd.opening.sprites != nil {
			hd["opening_cursor_background"] = b.hd.opening.sprites.paintWithin(out, f, f.cursor)
		} else {
			hd["opening_cursor_background"] = b.hd.opening.paintWithin(out, f, f.cursor)
		}
	}
	hd["native_cursor_text_background_repaints"] = nativeCursorBackgroundPainted
	hd["native_cursor_text_background_mask"] = nativeCursorBackgroundMask

	hd["terrain_texture_background"] = map[string]any{"painted": terrainBGPainted, "mask": terrainBGMask}
	hd["published_terrain_texture_background"] = map[string]any{"painted": publishedTerrainBGPainted, "mask": publishedTerrainBGMask}
	record["hd"] = hd
	return out, record, nil
}

func (h *hdRuntime) key() string {
	base := h.baseKey()
	if h != nil && h.opening != nil && h.m != nil {
		base = fmt.Sprintf("%s/opening/%d/%s/%s/%s", base, h.opening.revision,
			hash(h.m.Mem[0x5570+0x9f:0x5570+0x9f+32]), hash(h.m.Mem[0xafc00:0xaff00]),
			hash(h.m.Mem[hdOpeningMain:hdOpeningMain+64000]))
	}
	if h != nil && h.m != nil && h.cursor != nil && len(h.m.Mem) >= 0xafc00 {
		base = fmt.Sprintf("%s/cursor-source/%s", base, hash(bytes.Join([][]byte{h.m.Mem[0x1cd74:0x1ce74], h.m.Mem[0xafa00:0xafc00]}, nil)))
	}

	if h != nil && h.scenes != nil {
		base = fmt.Sprintf("%s/scene-picture/%d", base, h.scenes.revision)
	}
	if h != nil && h.newGame != nil {
		base = fmt.Sprintf("%s/new-game/%d", base, h.newGame.revision)
	}
	if h != nil && h.terrainTextures != nil {
		base = fmt.Sprintf("%s/terrain-textures/%d", base, h.terrainTextures.revision)
	}
	if h != nil && h.parch != nil {
		base = fmt.Sprintf("%s/parch/%d", base, h.parch.revision)
	}
	if h != nil && h.worldTexture != nil {
		base = fmt.Sprintf("%s/world-texture/%d", base, h.worldTexture.revision)
	}
	if h != nil && h.texture != nil {
		base = fmt.Sprintf("%s/texture/%d", base, h.texture.revision)
	}
	if h != nil && h.terrain079 != nil {
		base = fmt.Sprintf("%s/terrain079/%d", base, h.terrain079.revision)
	}
	if h != nil && h.terrainBatch != nil {
		base = fmt.Sprintf("%s/terrain-batch/%d", base, h.terrainBatch.revision)
	}
	if h != nil && h.smallTerrain != nil {
		base = fmt.Sprintf("%s/small-terrain/%d", base, h.smallTerrain.revision)
	}
	if h != nil && h.small != nil {
		return fmt.Sprintf("%s/small/%d", base, h.small.revision)
	}
	if h != nil && h.royal != nil {
		base = fmt.Sprintf("%s/royal/%d", base, h.royal.revision)
	}
	return base
}

func hdOpeningCursorUncovered(cursor image.Rectangle, items []map[string]any) bool {
	for _, item := range items {
		safe, ok := item["safe"].(image.Rectangle)
		if !ok || safe.Empty() || !safe.In(image.Rect(0, 0, 320, 200)) || cursor.Overlaps(safe) {
			return false
		}
		if value, present := item["source_safe"]; present {
			source, ok := value.(image.Rectangle)
			if !ok || source.Empty() || !source.In(image.Rect(0, 0, 320, 200)) || cursor.Overlaps(source) {
				return false
			}
		}
	}
	return true
}
