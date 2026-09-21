// render_indexed 將 dosgolem 的 indexed frame 與獨立 VGA palette 轉成 PNG。
// 它只處理呼叫者指定的檔案，不含任何原版資料或遊戲專屬位址。
package main

import (
	"errors"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"os"
	"path/filepath"
)

func main() {
	indexedPath := flag.String("indexed", "", "dosgolem indexed frame 檔案")
	palettePath := flag.String("palette", "", "dosgolem palette 檔案（256×RGB）")
	outPath := flag.String("out", "", "輸出 PNG 路徑")
	width := flag.Int("width", 320, "畫面寬度")
	height := flag.Int("height", 200, "畫面高度")
	flag.Parse()

	if *indexedPath == "" || *palettePath == "" || *outPath == "" {
		fail(errors.New("-indexed、-palette 與 -out 都是必填"))
	}
	if *width <= 0 || *height <= 0 {
		fail(errors.New("-width 與 -height 必須為正整數"))
	}

	indexed, err := os.ReadFile(*indexedPath)
	if err != nil {
		fail(fmt.Errorf("讀取 indexed frame：%w", err))
	}
	expected := *width * *height
	if len(indexed) != expected {
		fail(fmt.Errorf("indexed frame 長度 %d，不等於 %dx%d = %d", len(indexed), *width, *height, expected))
	}
	paletteBytes, err := os.ReadFile(*palettePath)
	if err != nil {
		fail(fmt.Errorf("讀取 palette：%w", err))
	}
	if len(paletteBytes) != 256*3 {
		fail(fmt.Errorf("palette 長度 %d，不等於 768", len(paletteBytes)))
	}

	palette := make(color.Palette, 256)
	for i := range palette {
		j := i * 3
		palette[i] = color.RGBA{R: paletteBytes[j], G: paletteBytes[j+1], B: paletteBytes[j+2], A: 0xff}
	}
	image := image.NewPaletted(image.Rect(0, 0, *width, *height), palette)
	copy(image.Pix, indexed)

	if err := os.MkdirAll(filepath.Dir(*outPath), 0o755); err != nil {
		fail(fmt.Errorf("建立輸出目錄：%w", err))
	}
	f, err := os.Create(*outPath)
	if err != nil {
		fail(fmt.Errorf("建立 PNG：%w", err))
	}
	if err := png.Encode(f, image); err != nil {
		f.Close()
		fail(fmt.Errorf("編碼 PNG：%w", err))
	}
	if err := f.Close(); err != nil {
		fail(fmt.Errorf("關閉 PNG：%w", err))
	}
}

func fail(err error) {
	fmt.Fprintln(os.Stderr, "render_indexed:", err)
	os.Exit(1)
}
