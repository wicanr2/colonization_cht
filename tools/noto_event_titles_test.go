package main

import (
	"bytes"
	"encoding/json"
	"image"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDraftNotoWoodcutMeasuredAlpha(t *testing.T) {
	root := os.Getenv("TEST_HD_EVENT_ROOT")
	if root == "" {
		t.Skip("需要已驗原版欄位與固定Noto字模")
	}
	read := func(path string) []byte {
		t.Helper()
		raw, e := os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
		return raw
	}
	var report struct {
		Rows []struct {
			Locale, Title, Text string
			FontSHA             string `json:"font_sha256"`
			AtlasSHA            string `json:"atlas_sha256"`
			Geometry            struct {
				Ink  [4]int `json:"original_ink"`
				Safe [4]int `json:"safe"`
			}
			Candidate struct{ Size int } `json:"measured_candidate"`
		}
	}
	if e := json.Unmarshal(read(filepath.Join(root, "r97-noto-title-measurements-r1.json")), &report); e != nil {
		t.Fatal(e)
	}
	if len(report.Rows) != 12 {
		t.Fatal("twelve measured fields")
	}
	fontsByLocale := map[string]map[int]*dialogFont{}
	records := []map[string]any{}
	for _, row := range report.Rows {
		t.Run(row.Locale+"/"+row.Title, func(t *testing.T) {
			fonts := fontsByLocale[row.Locale]
			if fonts == nil {
				raw := read(filepath.Join(root, "r97-event-formal-bundle-r1/languages", row.Locale, "masks/string-atlas.json"))
				if hash(raw) != row.AtlasSHA {
					t.Fatal("atlas fingerprint")
				}
				var atlas struct{ Bindings map[string]string }
				if e := json.Unmarshal(raw, &atlas); e != nil {
					t.Fatal(e)
				}
				var why string
				fonts, why = loadAtlasFonts(raw, row.FontSHA, atlas.Bindings, 30, 12)
				if why != "" {
					t.Fatal(why)
				}
				fontsByLocale[row.Locale] = fonts
			}
			ink, safe := image.Rect(row.Geometry.Ink[0], row.Geometry.Ink[1], row.Geometry.Ink[2], row.Geometry.Ink[3]), image.Rect(row.Geometry.Safe[0], row.Geometry.Safe[1], row.Geometry.Safe[2], row.Geometry.Safe[3])
			oldMetrics := map[int][2]int{}
			for size, font := range fonts {
				oldMetrics[size] = [2]int{font.cjkTop, font.cjkBottom}
			}
			catalog := &stringCatalog{fonts: fonts}
			_, old, _, _ := catalog.woodcutMasks(row.Text, ink, safe, 7)
			if old != nil {
				t.Fatal("original Noto regression no longer reproduced")
			}
			sh, n, ac, size := draftNotoWoodcutMasks(fonts, row.Title, row.Text, ink, safe, 7)
			if sh == nil || n == nil || ac == nil || size != row.Candidate.Size || n.Rect != image.Rect(0, 0, safe.Dx()*4, 36) {
				t.Fatal("measured Noto title did not fit", size, row.Candidate.Size)
			}
			for px, font := range fonts {
				if oldMetrics[px] != [2]int{font.cjkTop, font.cjkBottom} {
					t.Fatal("shared font metrics changed")
				}
			}
			counts := [3]int{}
			for i, v := range n.Pix {
				if v != 0 {
					counts[0]++
					if sh.Pix[i] != 0 || ac.Pix[i] != 0 {
						t.Fatal("relief overlaps normal ink")
					}
				}
				if sh.Pix[i] != 0 {
					counts[1]++
					if ac.Pix[i] != 0 {
						t.Fatal("relief overlap")
					}
				}
				if ac.Pix[i] != 0 {
					counts[2]++
				}
			}
			if counts[0] == 0 || counts[1] == 0 || counts[2] == 0 {
				t.Fatal("missing title layer", counts)
			}
			records = append(records, map[string]any{"locale": row.Locale, "title": row.Title, "text": row.Text, "size": size, "width": n.Rect.Dx(), "height": n.Rect.Dy(), "normal": n.Pix, "shadow": sh.Pix, "highlight": ac.Pix})
			for _, kind := range []string{"unknown-title", "wrong-ink", "wrong-safe", "wrong-cap-height", "empty", "missing-glyph", "too-long"} {
				t.Run(kind, func(t *testing.T) {
					id, text, box, area, height := row.Title, row.Text, ink, safe, 7
					switch kind {
					case "unknown-title":
						id = "WOODCUT.TXT:0x0000000A"
					case "wrong-ink":
						box = box.Add(image.Pt(1, 0))
					case "wrong-safe":
						area = area.Inset(-1)
					case "wrong-cap-height":
						height = 6
					case "empty":
						text = ""
					case "missing-glyph":
						text = string(rune(0x10ffff))
					case "too-long":
						text = strings.Repeat(row.Text, 100)
					}
					sh, n, ac, size := draftNotoWoodcutMasks(fonts, id, text, box, area, height)
					if sh != nil || n != nil || ac != nil || size != 0 {
						t.Fatal("unverified title accepted", kind, size)
					}
				})
			}
		})
	}
	if len(records) != 12 {
		t.Fatal("field coverage")
	}
	if output := os.Getenv("TEST_HD_EVENT_TITLE_OUTPUT"); output != "" {
		raw, e := json.MarshalIndent(records, "", "  ")
		if e != nil {
			t.Fatal(e)
		}
		if e = os.WriteFile(output, raw, 0644); e != nil {
			t.Fatal(e)
		}
	}
}

func TestDraftNotoWoodcutOriginalSourceLifecycle(t *testing.T) {
	root := os.Getenv("TEST_HD_EVENT_ROOT")
	if root == "" {
		t.Skip("需要合法原版三個標題來源收據")
	}
	read := func(path string) []byte {
		t.Helper()
		raw, e := os.ReadFile(path)
		if e != nil {
			t.Fatal(e)
		}
		return raw
	}
	raw := read(filepath.Join(root, "r97-title-source-fixtures-r1.json"))
	if hash(raw) != "a85b32f3097e7fe8625c5846bea82fa6cd5f874df6bb73ef3ff996b3345b1ec2" {
		t.Fatal("original title fixture fingerprint")
	}
	var fixtures []struct {
		Title     string
		Native    string `json:"native_text"`
		Canvas    string
		CanvasSHA string `json:"canvas_sha256"`
		Ink, Safe [4]int
		First     map[int]byte `json:"first_old"`
		Last      map[int]byte `json:"last_value"`
	}
	if e := json.Unmarshal(raw, &fixtures); e != nil {
		t.Fatal(e)
	}
	var measured struct {
		Rows []struct {
			Locale, Title, Text string
			FontSHA             string             `json:"font_sha256"`
			AtlasSHA            string             `json:"atlas_sha256"`
			Candidate           struct{ Size int } `json:"measured_candidate"`
		}
	}
	if e := json.Unmarshal(read(filepath.Join(root, "r97-noto-title-measurements-r1.json")), &measured); e != nil {
		t.Fatal(e)
	}
	if len(fixtures) != 3 || len(measured.Rows) != 12 {
		t.Fatal("source field scope")
	}
	fontsByLocale := map[string]map[int]*dialogFont{}
	for _, row := range measured.Rows {
		t.Run(row.Locale+"/"+row.Title, func(t *testing.T) {
			fonts := fontsByLocale[row.Locale]
			if fonts == nil {
				raw := read(filepath.Join(root, "r97-event-formal-bundle-r1/languages", row.Locale, "masks/string-atlas.json"))
				if hash(raw) != row.AtlasSHA {
					t.Fatal("font artifact fingerprint")
				}
				var atlas struct{ Bindings map[string]string }
				if e := json.Unmarshal(raw, &atlas); e != nil {
					t.Fatal(e)
				}
				var why string
				fonts, why = loadAtlasFonts(raw, row.FontSHA, atlas.Bindings, 30, 12)
				if why != "" {
					t.Fatal(why)
				}
				fontsByLocale[row.Locale] = fonts
			}
			for _, fixture := range fixtures {
				if fixture.Title != row.Title {
					continue
				}
				canvas := read(filepath.Join(root, fixture.Canvas))
				if hash(canvas) != fixture.CanvasSHA || len(canvas) != 64000 {
					t.Fatal("original canvas fingerprint")
				}
				unchanged := append([]byte(nil), canvas...)
				catalog := &stringCatalog{fonts: fonts, woodcut: map[string]woodcutTitle{fixture.Native: {id: row.Title, zh: row.Text}}}
				calls := 0
				catalog.woodcutPlan = func(id, text string, ink, safe image.Rectangle, capH int) (*image.Alpha, *image.Alpha, *image.Alpha, int) {
					calls++
					return draftNotoWoodcutMasks(fonts, id, text, ink, safe, capH)
				}
				runtime := &stringRuntime{cat: catalog}
				run := &stringRun{text: []byte(fixture.Native), firstOld: fixture.First, lastVal: fixture.Last, colors: map[byte]int{}}
				for _, value := range fixture.Last {
					run.colors[value]++
				}
				ink := image.Rect(fixture.Ink[0], fixture.Ink[1], fixture.Ink[2], fixture.Ink[3])
				item, why := runtime.finishWoodcut(run, ink, 7, canvas, 1)
				if why != "" || item == nil || calls != 1 || item.size != row.Candidate.Size || item.zh != row.Text || item.id != "STRING:woodcut:"+row.Title || item.phase != "waiting-screen" {
					t.Fatal("original source to Noto item", why, calls)
				}
				if !bytes.Equal(canvas, unchanged) {
					t.Fatal("Noto assembly wrote original canvas")
				}
				background := append([]byte(nil), canvas...)
				for pos, value := range fixture.First {
					background[pos] = value
				}
				if !bytes.Equal(item.before, stringRect(background, item.safe)) || !bytes.Equal(item.after, stringRect(canvas, item.safe)) {
					t.Fatal("native source underlay or current title lost")
				}
				item.phase = "active"
				runtime.items = []*stringItem{item}
				if !runtime.woodcutVisible(canvas, image.Rect(0, 0, 16, 16)) {
					t.Fatal("normal visible source did not activate")
				}
				for pos, value := range fixture.Last {
					canvas[pos] = value ^ 1
					if runtime.woodcutVisible(canvas, image.Rect(0, 0, 16, 16)) {
						t.Fatal("changed native title stayed active")
					}
					rejected, reason := runtime.finishWoodcut(run, ink, 7, canvas, 2)
					if rejected != nil || reason != "woodcut-source-changed" || calls != 1 {
						t.Fatal("changed original source reached Noto")
					}
					canvas[pos] = value
					break
				}
			}
		})
	}
}
