package main

// 規格060 DRAFT：只用於隔離載入驗證，正式組裝器不連結本檔。
import (
	"bytes"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"strconv"
	"strings"
)

type draftBundleManifest struct {
	Schema      int               `json:"schema"`
	Kind        string            `json:"kind"`
	Locale      string            `json:"locale"`
	Original    bool              `json:"original_rendering"`
	Face        int               `json:"face"`
	Family      string            `json:"family"`
	Font        string            `json:"font_sha256"`
	License     string            `json:"license_sha256"`
	Source      string            `json:"source_binding_sha256"`
	Files       map[string]string `json:"files_sha256"`
	Limitations []string          `json:"limitations"`
}

type draftBundleRequirements struct {
	Source, Font, License, Fields string
	Tables                        []string
	Masks                         map[string]draftMaskRequirement
}

type draftMaskRequirement struct {
	ID      string
	Safe    [4]int
	Shadow  int
	Layered bool
	Catalog string
}

type draftPreparedBundle struct {
	manifest draftBundleManifest
	files    map[string][]byte
}

func draftDigest(data []byte) string { return fmt.Sprintf("%x", sha256.Sum256(data)) }

func draftRead(fsys fs.FS, name string, limit int64) ([]byte, error) {
	if !fs.ValidPath(name) {
		return nil, fmt.Errorf("invalid bundle path")
	}
	f, err := fsys.Open(name)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	stat, err := f.Stat()
	if err != nil || !stat.Mode().IsRegular() || stat.Size() > limit {
		return nil, fmt.Errorf("invalid bundle file: %s", name)
	}
	data, err := io.ReadAll(io.LimitReader(f, limit+1))
	if err != nil || int64(len(data)) > limit {
		return nil, fmt.Errorf("bundle read failed: %s", name)
	}
	return data, nil
}

func draftStrictJSON(data []byte, target any) error {
	d := json.NewDecoder(bytes.NewReader(data))
	d.DisallowUnknownFields()
	if err := d.Decode(target); err != nil {
		return err
	}
	if err := d.Decode(new(any)); err != io.EOF {
		return fmt.Errorf("trailing JSON")
	}
	return nil
}

func draftPrepareBundle(fsys fs.FS, locale string, needs draftBundleRequirements) (*draftPreparedBundle, error) {
	face, family := 0, ""
	switch locale {
	case "zh-Hant":
		face, family = 3, "Noto Sans CJK TC"
	case "zh-Hans":
		face, family = 2, "Noto Sans CJK SC"
	case "ja":
		face, family = 0, "Noto Sans CJK JP"
	case "ko":
		face, family = 1, "Noto Sans CJK KR"
	case "en":
	default:
		return nil, fmt.Errorf("unsupported locale")
	}
	data, err := draftRead(fsys, locale+"/manifest.json", 1<<20)
	if err != nil {
		return nil, err
	}
	p := &draftPreparedBundle{files: map[string][]byte{}}
	if err := draftStrictJSON(data, &p.manifest); err != nil {
		return nil, err
	}
	m := &p.manifest
	if m.Schema != 1 || m.Kind != "DRAFT-display-language-bundle" || m.Locale != locale || m.Source != needs.Source || m.Original != (locale == "en") {
		return nil, fmt.Errorf("bundle identity mismatch")
	}
	if locale == "en" {
		if len(m.Files) != 0 || m.Font != "" || m.License != "" || m.Family != "" || m.Face != 0 {
			return nil, fmt.Errorf("English must render original")
		}
		return p, nil
	}
	if m.Face != face || m.Family != family || m.Font != needs.Font || m.License != needs.License || len(needs.Tables) != 13 || len(needs.Masks) != 64 {
		return nil, fmt.Errorf("font profile or requirements mismatch")
	}
	expected := map[string]bool{}
	for _, name := range needs.Tables {
		expected["text/"+name] = true
	}
	for name := range needs.Masks {
		expected["masks/"+name] = true
	}
	for _, consumer := range []string{"sea", "dialog", "string"} {
		expected["masks/"+consumer+"-atlas.json"] = true
	}
	if len(expected) != 80 || len(m.Files) != 80 {
		return nil, fmt.Errorf("incomplete bundle")
	}
	for name, hash := range m.Files {
		if !expected[name] || !fs.ValidPath(name) || len(hash) != 64 {
			return nil, fmt.Errorf("unexpected bundle file")
		}
		data, err := draftRead(fsys, locale+"/"+name, 96<<20)
		if err != nil || draftDigest(data) != hash {
			return nil, fmt.Errorf("bundle file binding mismatch: %s", name)
		}
		p.files[name] = data
	}
	for name, requirement := range needs.Masks {
		var mask struct {
			ID        string `json:"candidate_id"`
			MessageID string `json:"message_id"`
			Locale    string `json:"locale"`
			Face      int    `json:"face"`
			Family    string `json:"family"`
			Font      string `json:"font_sha256"`
			Catalog   string `json:"catalog_sha256"`
			Width     int    `json:"width"`
			Height    int    `json:"height"`
			X         int    `json:"x"`
			Y         int    `json:"y"`
			Alpha     []byte `json:"alpha"`
			Normal    []byte `json:"normal"`
			Shadow    []byte `json:"shadow"`
			Highlight []byte `json:"highlight"`
			Bindings  struct {
				Source  string            `json:"source_binding_sha256"`
				Fields  string            `json:"fields_sha256"`
				License string            `json:"license_sha256"`
				Text    map[string]string `json:"text"`
			} `json:"bindings"`
			Measurement struct {
				Safe     []int `json:"safe_scaled"`
				Position []int `json:"position"`
				Chosen   struct {
					Fits bool `json:"fits"`
				} `json:"chosen"`
			} `json:"measurement"`
		}
		if json.Unmarshal(p.files["masks/"+name], &mask) != nil {
			return nil, fmt.Errorf("invalid fixed mask")
		}
		if mask.ID == "" {
			mask.ID = mask.MessageID
		}
		r := mask.Measurement.Safe
		pos := mask.Measurement.Position
		if mask.ID != requirement.ID || mask.Locale != locale || mask.Face != face || mask.Family != family || mask.Font != needs.Font ||
			mask.Width <= 0 || mask.Width > 1280 || mask.Height <= 0 || mask.Height > 800 || !mask.Measurement.Chosen.Fits ||
			len(r) != 4 || len(pos) != 2 || mask.X != pos[0] || mask.Y != pos[1] || mask.X < r[0] || mask.Y < r[1] ||
			mask.X+mask.Width > r[2] || mask.Y+mask.Height > r[3] {
			return nil, fmt.Errorf("fixed mask profile or geometry mismatch: %s", name)
		}
		if [4]int(r) != requirement.Safe {
			return nil, fmt.Errorf("fixed mask native safe rectangle mismatch")
		}
		if mask.Catalog != m.Files["text/"+requirement.Catalog] || mask.Bindings.Source != needs.Source ||
			mask.Bindings.Fields != needs.Fields || mask.Bindings.License != needs.License || len(mask.Bindings.Text) != 13 {
			return nil, fmt.Errorf("fixed mask source binding mismatch")
		}
		for _, table := range needs.Tables {
			if mask.Bindings.Text[table] != m.Files["text/"+table] {
				return nil, fmt.Errorf("fixed mask text binding mismatch")
			}
		}
		area := mask.Width * mask.Height
		if requirement.Layered {
			if len(mask.Alpha) != 0 || len(mask.Normal) != area || len(mask.Shadow) != area || len(mask.Highlight) != area ||
				mask.X != r[0] || mask.Y != r[1] || mask.X+mask.Width != r[2] || mask.Y+mask.Height != r[3] {
				return nil, fmt.Errorf("invalid fixed layered mask")
			}
		} else if len(mask.Alpha) != area || len(mask.Normal)+len(mask.Shadow)+len(mask.Highlight) != 0 ||
			mask.X+mask.Width+requirement.Shadow > r[2] || mask.Y+mask.Height+requirement.Shadow > r[3] {
			return nil, fmt.Errorf("invalid fixed mask layers")
		}
	}
	for _, consumer := range []string{"sea", "dialog", "string"} {
		if err := draftVerifyAtlas(p.files["masks/"+consumer+"-atlas.json"], consumer, *m); err != nil {
			return nil, err
		}
	}
	return p, nil
}

func draftVerifyAtlas(data []byte, consumer string, manifest draftBundleManifest) error {
	var atlas struct {
		Locale   string            `json:"locale"`
		Face     int               `json:"face"`
		Family   string            `json:"family"`
		Font     string            `json:"font_sha256"`
		License  string            `json:"license_sha256"`
		Source   string            `json:"source_binding_sha256"`
		Catalog  string            `json:"catalog_sha256"`
		Bindings map[string]string `json:"bindings"`
		Sizes    map[string]struct {
			Height int `json:"height"`
			Glyphs map[string]struct {
				Width int    `json:"w"`
				Alpha string `json:"alpha"`
			} `json:"glyphs"`
		} `json:"sizes"`
	}
	if json.Unmarshal(data, &atlas) != nil || atlas.Locale != manifest.Locale || atlas.Face != manifest.Face ||
		atlas.Family != manifest.Family || atlas.Font != manifest.Font || atlas.License != manifest.License || atlas.Source != manifest.Source {
		return fmt.Errorf("atlas profile mismatch")
	}
	start, end := 12, 30
	if consumer == "sea" {
		start, end = 15, 22
		if atlas.Catalog != manifest.Files["text/sea-status.zh-Hant.tsv"] {
			return fmt.Errorf("sea atlas text binding mismatch")
		}
	} else {
		bindings := map[string]string{"corpus": "corpus.zh-Hant.tsv", "terms": "terms.zh-Hant.tsv", "draft": "draft.zh-Hant.tsv"}
		if consumer == "dialog" {
			bindings["values"], bindings["help"], bindings["pedia"] = "variable-values.zh-Hant.tsv", "help-bilingual.tsv", "pedia-bilingual.tsv"
		} else {
			bindings["templates"], bindings["sea"], bindings["colony"] = "string-templates.zh-Hant.tsv", "sea-status.zh-Hant.tsv", "colony-bilingual.tsv"
		}
		if len(atlas.Bindings) != len(bindings) {
			return fmt.Errorf("atlas text bindings incomplete")
		}
		for key, table := range bindings {
			if atlas.Bindings[key] != manifest.Files["text/"+table] {
				return fmt.Errorf("atlas text binding mismatch")
			}
		}
	}
	if len(atlas.Sizes) != end-start+1 {
		return fmt.Errorf("atlas sizes missing")
	}
	for px := start; px <= end; px++ {
		size, ok := atlas.Sizes[strconv.Itoa(px)]
		if !ok || size.Height <= 0 || size.Height > 128 {
			return fmt.Errorf("invalid atlas height")
		}
		for ch := ' '; ch <= '~'; ch++ {
			if _, ok := size.Glyphs[string(ch)]; !ok {
				return fmt.Errorf("atlas ASCII missing")
			}
		}
		for key, glyph := range size.Glyphs {
			raw, err := base64.StdEncoding.Strict().DecodeString(glyph.Alpha)
			if len([]rune(key)) != 1 || strings.ContainsRune(key, '\x00') || glyph.Width <= 0 || glyph.Width > 128 || err != nil || len(raw) != glyph.Width*size.Height {
				return fmt.Errorf("invalid atlas glyph")
			}
		}
	}
	return nil
}
