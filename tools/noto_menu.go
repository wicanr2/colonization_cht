package main

// 規格055：五列顯示資料。只接受來源守門已確認的menuLine，不接觸機器或輸入。
import (
	"encoding/json"
	"image"
	"strconv"
	"strings"
)

const notoMenuGameSHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
const notoMenuFrameSHA = "559df11e83c1fb01e2d844a4379af6369e279bf4ea7b4b30c95cbf2d4062c4a1"

var notoMenuKeys = []string{"GAME.TXT:0x000001B0", "GAME.TXT:0x000001CB", "GAME.TXT:0x000001E4", "GAME.TXT:0x000001F9", "GAME.TXT:0x00000204"}
var notoMenuOffsets = []int{0x1b0, 0x1cb, 0x1e4, 0x1f9, 0x204}
var notoMenuLengths = []int{25, 23, 19, 9, 17}
var notoMenuSizes = []int{24, 24, 20, 20, 24}

type notoMenuMask struct {
	fontMask
	Bindings map[string]string `json:"bindings"`
}

type notoMenuDisplay struct {
	locale, reason string
	texts          []string
	inks           []*image.Alpha
}

func loadNotoMenu(locale string, baseline, draft, game []byte, masks map[string][]byte) *notoMenuDisplay {
	p := &notoMenuDisplay{locale: locale, reason: "invalid-translation"}
	bind, ok := notoOrdersBindings(locale, baseline, draft)
	if !ok {
		p.reason = "unsupported-locale"
		return p
	}
	delete(bind, "layout")
	bind["source"], bind["frame"] = notoMenuGameSHA, notoMenuFrameSHA
	base, bv := notoOrdersRows(baseline, true)
	rows, rv := notoOrdersRows(draft, false)
	if !bv || !rv || len(rows) != 5 || len(masks) != 5 || notoOrdersHash(game) != notoMenuGameSHA {
		return p
	}
	for i, key := range notoMenuKeys {
		a, b := base[key], rows[key]
		if a == nil || b == nil {
			return p
		}
		for c := 0; c < 6; c++ {
			if a[c] != b[c] {
				return p
			}
		}
		off, err := strconv.ParseUint(b[3], 0, 32)
		length, le := strconv.Atoi(b[5])
		if err != nil || le != nil || int(off) != notoMenuOffsets[i] || length != notoMenuLengths[i] ||
			b[1] != "GAME.TXT" || b[2] != notoMenuGameSHA || b[4] != notoOrdersHash(game[int(off):int(off)+length]) ||
			(b[7] != "draft" && b[7] != "translated") || strings.TrimSpace(b[6]) != b[6] || b[6] == "" {
			return p
		}
		for _, ch := range b[6] {
			if ch < 32 || strings.ContainsRune("~#{}^%@\\", ch) {
				return p
			}
		}
		var mask notoMenuMask
		if json.Unmarshal(masks[key], &mask) != nil || mask.CandidateID != key || mask.FontHash != notoOrdersFontSHA ||
			mask.TranslationHash != notoOrdersHash([]byte(b[6])) || mask.CatalogHash != notoOrdersHash(draft) ||
			mask.FontSize != notoMenuSizes[i] || len(mask.Bindings) != len(bind) {
			p.reason = "font-binding"
			return p
		}
		for k, value := range bind {
			if mask.Bindings[k] != value {
				p.reason = "font-binding"
				return p
			}
		}
		if mask.Width <= 0 || mask.Width > 580 || mask.Height != notoMenuSizes[i] || len(mask.Alpha) != mask.Width*mask.Height ||
			mask.ValuesHash != notoOrdersHash(mask.Alpha) {
			p.reason = "font-geometry"
			return p
		}
		ink := image.NewAlpha(image.Rect(0, 0, mask.Width, mask.Height))
		copy(ink.Pix, mask.Alpha)
		// 完整裁切遮罩的四邊都應有墨跡，拒絕空白或額外填充而改變基線。
		var left, right, top, bottom bool
		for y := 0; y < mask.Height; y++ {
			left = left || ink.AlphaAt(0, y).A != 0
			right = right || ink.AlphaAt(mask.Width-1, y).A != 0
		}
		for x := 0; x < mask.Width; x++ {
			top = top || ink.AlphaAt(x, 0).A != 0
			bottom = bottom || ink.AlphaAt(x, mask.Height-1).A != 0
		}
		if !left || !right || !top || !bottom {
			p.reason = "empty-or-padded-ink"
			return p
		}
		p.texts, p.inks = append(p.texts, b[6]), append(p.inks, ink)
	}
	p.reason = ""
	return p
}

func (p *notoMenuDisplay) apply(lines []*menuLine, missing bool) {
	if p == nil {
		return
	}
	reason := p.reason
	if len(lines) != 5 {
		reason = "incomplete-scope"
	} else {
		for i, l := range lines {
			if l.id != notoMenuKeys[i] || l.offset != notoMenuOffsets[i] || l.length != notoMenuLengths[i] ||
				l.matches != 1 || !l.catalogValid || l.safe() != image.Rect(86, 107+8*i, 232, 114+8*i) {
				reason = "source-guard"
			}
		}
	}
	if missing {
		reason = "missing-ink"
	}
	for i, l := range lines {
		l.ink = nil
		l.fontReason = "noto-menu-" + reason
		if reason == "" {
			l.translation, l.ink, l.fontReason = p.texts[i], p.inks[i], ""
		}
	}
	p.reason = reason
}
