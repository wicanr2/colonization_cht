package main

// 規格054：只供原版守門已通過的六列精簡ORDERS；本檔不存取機器狀態。
import (
	"bytes"
	"crypto/sha256"
	"encoding/csv"
	"encoding/json"
	"fmt"
	"image"
	"strings"
	"unicode/utf8"
)

const notoOrdersFontSHA = "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a"
const notoOrdersMenuSHA = "5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702"
const notoOrdersLayoutSHA = "35cecc614308c691b82b817b12e4717486986a5a39b95adf67714a1c743870e9"
const notoOrdersLicenseSHA = "6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2"

var notoOrdersKeys = []string{
	"MENU.TXT:0x00000264", "MENU.TXT:0x00000276", "MENU.TXT:0x00000299",
	"MENU.TXT:0x000002A5", "MENU.TXT:0x00000384", "MENU.TXT:0x000003BC",
}

const notoOrdersAlias = "MENU.TXT:0x0000028D"

type notoOrdersDisplay struct {
	locale, reason string
	fonts          map[int]*dialogFont
	items          []string
}

func notoOrdersHash(b []byte) string { return fmt.Sprintf("%x", sha256.Sum256(b)) }

func notoOrdersBindings(locale string, baseline, draft []byte) (map[string]string, bool) {
	faces := map[string]int{"zh-Hant": 3, "zh-Hans": 2, "ja": 0, "ko": 1}
	families := map[string]string{"zh-Hant": "TC", "zh-Hans": "SC", "ja": "JP", "ko": "KR"}
	face, ok := faces[locale]
	if !ok {
		return nil, false
	}
	profile, _ := json.Marshal(map[string]any{"locale": locale, "face": face, "family": "Noto Sans CJK " + families[locale]})
	return map[string]string{
		"draft": notoOrdersHash(draft), "baseline": notoOrdersHash(baseline),
		"source": notoOrdersMenuSHA, "layout": notoOrdersLayoutSHA,
		"license": notoOrdersLicenseSHA, "locale_profile": notoOrdersHash(profile),
	}, true
}

// 基準沿舊TSV的引號相容讀法；新七列輸入須遵守標準TSV quoting。
func notoOrdersRows(data []byte, legacy bool) (map[string][]string, bool) {
	if len(data) == 0 || len(data) > 16<<20 || !utf8.Valid(data) || bytes.ContainsRune(data, 0) || bytes.HasPrefix(data, []byte{239, 187, 191}) {
		return nil, false
	}
	r := csv.NewReader(bytes.NewReader(data))
	r.Comma, r.LazyQuotes = '\t', legacy
	records, err := r.ReadAll()
	header := []string{"candidate_id", "source_file", "source_sha256", "byte_offset", "source_bytes_sha256", "source_byte_length", "zh_hant", "status", "notes"}
	if err != nil || len(records) < 2 || len(records[0]) != len(header) {
		return nil, false
	}
	for i, h := range header {
		if records[0][i] != h {
			return nil, false
		}
	}
	rows := map[string][]string{}
	for _, row := range records[1:] {
		if len(row) != len(header) || row[0] == "" || rows[row[0]] != nil {
			return nil, false
		}
		rows[row[0]] = row
	}
	return rows, true
}

// 不以譯文識別命令；此簽章只保留顯示控制的順序及熱鍵字元。
func notoOrdersMarkup(s string) (string, bool) {
	rs := []rune(s)
	var result strings.Builder
	for i, ch := range rs {
		if ch < 32 || strings.ContainsRune("{}^%@\\", ch) {
			return "", false
		}
		if ch == '~' {
			if i+1 >= len(rs) || rs[i+1] < 32 || rs[i+1] > 126 || rs[i+1] == '~' {
				return "", false
			}
			result.WriteRune(ch)
			result.WriteRune(rs[i+1])
		}
		if ch == '#' {
			result.WriteRune(ch)
		}
	}
	return result.String(), strings.TrimSpace(s) != ""
}

func loadNotoOrders(locale string, baseline, draft, atlas, menu []byte) *notoOrdersDisplay {
	p := &notoOrdersDisplay{locale: locale, reason: "invalid-translation"}
	bind, ok := notoOrdersBindings(locale, baseline, draft)
	if !ok {
		p.reason = "unsupported-locale"
		return p
	}
	base, validBase := notoOrdersRows(baseline, true)
	rows, validRows := notoOrdersRows(draft, false)
	if !validBase || !validRows || len(rows) != 7 || notoOrdersHash(menu) != notoOrdersMenuSHA {
		return p
	}
	keys := append(append([]string(nil), notoOrdersKeys...), notoOrdersAlias)
	var checked bytes.Buffer
	checked.WriteString("candidate_id\tsource_file\tsource_sha256\tbyte_offset\tsource_bytes_sha256\tsource_byte_length\tzh_hant\tstatus\tnotes\n")
	for _, key := range keys {
		a, b := base[key], rows[key]
		if a == nil || b == nil {
			return p
		}
		for i := 0; i < 6; i++ {
			if a[i] != b[i] {
				return p
			}
		}
		am, av := notoOrdersMarkup(a[6])
		bm, bv := notoOrdersMarkup(b[6])
		if !av || !bv || am != bm || b[1] != "MENU.TXT" || (b[7] != "draft" && b[7] != "translated") {
			return p
		}
		// 只將已核對七列送入既有原檔／片段驗證；備註不參與顯示。
		checked.WriteString(strings.Join(b[:8], "\t") + "\t\n")
	}
	if strings.TrimSpace(rows[notoOrdersAlias][6]) != strings.TrimSpace(rows[notoOrdersKeys[2]][6]) {
		p.reason = "ambiguous-source-translation"
		return p
	}
	cat := &dialogCatalog{seen: map[string]bool{}}
	if cat.addDraft(checked.Bytes(), map[string][]byte{"MENU.TXT": menu}, nil) != nil || len(cat.lines) != 7 {
		return p
	}
	for _, key := range notoOrdersKeys {
		p.items = append(p.items, menuZh(strings.TrimSpace(rows[key][6])))
	}
	p.fonts, p.reason = loadAtlasFonts(atlas, notoOrdersFontSHA, bind, 18, 18)
	if p.reason != "" {
		return p
	}
	f := p.fonts[18]
	for ch := rune(32); ch < 127; ch++ {
		if f.glyphs[ch] == nil || f.widths[ch] <= 0 {
			p.reason = "missing-glyph"
			return p
		}
	}
	for _, text := range p.items {
		glyphs, valid := dialogMarked(text)
		if !valid {
			p.reason = "invalid-markup"
			return p
		}
		for _, glyph := range glyphs {
			if f.glyphs[glyph.r] == nil || f.widths[glyph.r] <= 0 {
				p.reason = "missing-glyph"
				return p
			}
		}
	}
	return p
}

// 既有來源、外框、色層守門全部通過後才呼叫。錯誤須由呼叫者整欄回原文。
func (p *notoOrdersDisplay) field(items []string, fonts *dialogCatalog, lines []runLine, canvas []byte, safe image.Rectangle) ([]string, *dialogCatalog, string) {
	if p == nil || !compactOrdersStyle(lines, canvas) {
		return items, fonts, ""
	}
	if p.reason != "" {
		return nil, nil, "noto-orders-" + p.reason
	}
	if safe != image.Rect(80, 12, 159, 77) {
		return nil, nil, "noto-orders-geometry"
	}
	return p.items, &dialogCatalog{fonts: p.fonts}, ""
}
