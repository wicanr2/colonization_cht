// 可丟棄的 Ebitengine 難度卡片畫面對照；只讀已核對的本機收據，不接正式遊戲路徑。
package main

import (
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"image"
	"image/color"
	"image/png"
	"os"

	"github.com/hajimehoshi/ebiten/v2"
)

type previewLayer struct {
	Name        string `json:"name"`
	Safe        [4]int `json:"safe"`
	InkWidth    int    `json:"ink_width"`
	InkHeight   int    `json:"ink_height"`
	Position    [2]int `json:"position"`
	Background  string `json:"background"`
	Mask        string `json:"mask"`
	ColorIndex  *int   `json:"color_index,omitempty"`
	ShadowIndex *int   `json:"shadow_index,omitempty"`
	ShadowDX    int    `json:"shadow_dx,omitempty"`
}
type previewData struct {
	Prototype bool           `json:"prototype"`
	Indexed   string         `json:"indexed"`
	Palette   string         `json:"palette"`
	Layers    []previewLayer `json:"layers"`
}
type previewGame struct {
	canvas *ebiten.Image
	out    string
	frame  int
}

func fail(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
func decode(value string, expected int) []byte {
	data, err := base64.StdEncoding.Strict().DecodeString(value)
	fail(err)
	if len(data) != expected {
		fail(fmt.Errorf("預覽資料長度 %d，不等於 %d", len(data), expected))
	}
	return data
}
func rgb(palette []byte, index byte) color.RGBA {
	i := int(index) * 3
	return color.RGBA{R: palette[i]<<2 | palette[i]>>4,
		G: palette[i+1]<<2 | palette[i+1]>>4,
		B: palette[i+2]<<2 | palette[i+2]>>4, A: 255}
}
func scaled(indexed, palette []byte, width, height int) *ebiten.Image {
	imageData := image.NewRGBA(image.Rect(0, 0, width*4, height*4))
	for y := 0; y < height; y++ {
		for x := 0; x < width; x++ {
			c := rgb(palette, indexed[y*width+x])
			for dy := 0; dy < 4; dy++ {
				for dx := 0; dx < 4; dx++ {
					imageData.SetRGBA(x*4+dx, y*4+dy, c)
				}
			}
		}
	}
	return ebiten.NewImageFromImage(imageData)
}
func newPreview(data previewData, out string, control bool) *previewGame {
	if !data.Prototype || len(data.Layers) != 2 {
		fail(fmt.Errorf("只接受固定兩欄可丟棄收據"))
	}
	indexed := decode(data.Indexed, 320*200)
	palette := decode(data.Palette, 256*3)
	canvas := scaled(indexed, palette, 320, 200)
	if !control {
		for _, layer := range data.Layers {
			x0, y0, x1, y1 := layer.Safe[0], layer.Safe[1], layer.Safe[2], layer.Safe[3]
			if x0 < 0 || y0 < 0 || x1 > 320 || y1 > 200 || x0 >= x1 || y0 >= y1 ||
				layer.InkWidth <= 0 || layer.InkHeight <= 0 || layer.Position[0] < x0*4 ||
				layer.Position[1] < y0*4 || layer.Position[0]+layer.InkWidth > x1*4 ||
				layer.Position[1]+layer.InkHeight > y1*4 {
				fail(fmt.Errorf("欄位安全矩形不符：%s", layer.Name))
			}
			background := decode(layer.Background, (x1-x0)*(y1-y0))
			mask := decode(layer.Mask, layer.InkWidth*layer.InkHeight)
			patch := scaled(background, palette, x1-x0, y1-y0)
			patchOp := &ebiten.DrawImageOptions{}
			patchOp.GeoM.Translate(float64(x0*4), float64(y0*4))
			canvas.DrawImage(patch, patchOp)
			ink := image.NewNRGBA(image.Rect(0, 0, layer.InkWidth, layer.InkHeight))
			foregroundIndex := 254
			if layer.ColorIndex != nil {
				foregroundIndex = *layer.ColorIndex
			}
			if foregroundIndex < 0 || foregroundIndex > 255 {
				fail(fmt.Errorf("前景色索引不合法：%s", layer.Name))
			}
			if layer.ShadowIndex != nil {
				if *layer.ShadowIndex < 0 || *layer.ShadowIndex > 255 || layer.ShadowDX < 0 ||
					layer.Position[0]+layer.InkWidth+layer.ShadowDX > x1*4 {
					fail(fmt.Errorf("陰影超出安全矩形：%s", layer.Name))
				}
				shadowColor := rgb(palette, byte(*layer.ShadowIndex))
				shadow := image.NewNRGBA(image.Rect(0, 0, layer.InkWidth, layer.InkHeight))
				for y := 0; y < layer.InkHeight; y++ {
					for x := 0; x < layer.InkWidth; x++ {
						shadow.SetNRGBA(x, y, color.NRGBA{R: shadowColor.R, G: shadowColor.G,
							B: shadowColor.B, A: mask[y*layer.InkWidth+x]})
					}
				}
				shadowOp := &ebiten.DrawImageOptions{}
				shadowOp.GeoM.Translate(float64(layer.Position[0]+layer.ShadowDX), float64(layer.Position[1]))
				canvas.DrawImage(ebiten.NewImageFromImage(shadow), shadowOp)
			}
			foreground := rgb(palette, byte(foregroundIndex))
			for y := 0; y < layer.InkHeight; y++ {
				for x := 0; x < layer.InkWidth; x++ {
					ink.SetNRGBA(x, y, color.NRGBA{R: foreground.R, G: foreground.G,
						B: foreground.B, A: mask[y*layer.InkWidth+x]})
				}
			}
			inkOp := &ebiten.DrawImageOptions{}
			inkOp.GeoM.Translate(float64(layer.Position[0]), float64(layer.Position[1]))
			canvas.DrawImage(ebiten.NewImageFromImage(ink), inkOp)
		}
	}
	return &previewGame{canvas: canvas, out: out}
}
func (g *previewGame) Update() error {
	g.frame++
	if g.frame > 1 {
		return ebiten.Termination
	}
	return nil
}
func (g *previewGame) Draw(screen *ebiten.Image) {
	screen.DrawImage(g.canvas, nil)
	if g.frame != 1 {
		return
	}
	frame := image.NewRGBA(image.Rect(0, 0, 1280, 800))
	g.canvas.ReadPixels(frame.Pix)
	output, err := os.Create(g.out)
	fail(err)
	fail(png.Encode(output, frame))
	fail(output.Close())
}
func (g *previewGame) Layout(int, int) (int, int) { return 1280, 800 }

func main() {
	in := flag.String("in", "", "本機已核對預覽資料")
	out := flag.String("out", "", "本機輸出 PNG")
	control := flag.Bool("control", false, "只顯示原版畫布")
	flag.Parse()
	if *in == "" || *out == "" {
		fail(fmt.Errorf("必須指定 -in 與 -out"))
	}
	bytes, err := os.ReadFile(*in)
	fail(err)
	var data previewData
	fail(json.Unmarshal(bytes, &data))
	ebiten.SetWindowSize(1280, 800)
	ebiten.SetWindowTitle("Colonization card prototype")
	fail(ebiten.RunGame(newPreview(data, *out, *control)))
}
