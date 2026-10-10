#!/usr/bin/env python3
"""規格051 DRAFT：只在新的workplace目錄組裝設定列執行原型，不改正式Go來源。"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parent.parent
SOURCE_HASHES = {
    "tools/live_menu.go": "7d136aef0b2acbe34ea030f63e01240f1c7a033e193f512871368fc26a09a61e",
    "tools/window_prototype.go": "cd287840cfd35cdac4846eb93b5c0dff78860e58a0ecd05d1cd1be119d338fd2",
    "tools/build_window_prototype.py": "28f7b023f63b3cfd07583b78e372ebe74983f016c097e40531d2bc9e96968a39",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(source, old, new):
    if source.count(old) != 1:
        raise ValueError(f"原型替換點失配：{old[:100]!r}")
    return source.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not Path("/.dockerenv").is_file():
        raise SystemExit("請在Docker內執行")
    output = args.output.resolve()
    if (not output.is_relative_to((ROOT / "workplace").resolve()) or output.exists() or
            not output.parent.is_dir() or output.parent.stat().st_uid != os.getuid()):
        raise SystemExit("輸出須為新的workplace目錄，父目錄擁有者須相同")
    for name, expected in SOURCE_HASHES.items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise SystemExit(f"正式來源版本不符：{name}")
    subprocess.run([sys.executable, str(ROOT / "tools/build_window_prototype.py"), "--repo", str(ROOT),
                    "--output", str(output), "--reference", str(args.reference)], check=True, timeout=30)
    adapter = (output / "adapter.go").read_text()
    adapter = replace_once(adapter, '\t\tif *control {\n\t\t\t// 對照組',
                           '\t\tif *control || prototypeDisplayLanguage == "en" {\n\t\t\t// 對照組')
    adapter = replace_once(adapter, '\t\tif strOn && !*control {\n\t\t\t// 規格038：最後繪製',
                           '\t\tif strOn && !*control && prototypeDisplayLanguage != "en" {\n\t\t\t// 規格038：最後繪製')
    (output / "adapter.go").write_text(adapter)
    window = (output / "window.go").read_text()
    edits = [
        ('\taudio        *frontendAudio\n', '\taudio        *frontendAudio\n\tdisplay *displayUIPrototype\n\trender func(string)\n'),
        ('\tx, y, inside := logicalMouse(ebiten.CursorPosition())',
         '\tif g.display != nil && g.display.update(g) { return g.publishStatus() }\n'
         '\tx, y, inside := g.display.logicalMouse(ebiten.CursorPosition())'),
        ('\tg.audio.drain(g.m)\n\tstage := "opening"',
         '\tg.audio.drain(g.m)\n\treturn g.publishStatus()\n}\n\n'
         'func (g *windowGame) publishStatus() error {\n\tstage := "opening"'),
        ('\tif frontendStatusExtra != nil {',
         '\tif g.display != nil { status["display"] = g.display.status() }\n\tif frontendStatusExtra != nil {'),
        ('func (g *windowGame) Draw(screen *ebiten.Image) {\n\tif g.latest == nil {\n\t\treturn',
         'func (g *windowGame) Draw(screen *ebiten.Image) {\n\tif g.latest == nil {\n\t\tg.display.draw(screen)\n\t\treturn'),
        ('\tscreen.DrawImage(g.texture, nil)',
         '\tvar options ebiten.DrawImageOptions\n\toptions.GeoM.Translate(0, prototypeToolbarHeight)\n'
         '\tscreen.DrawImage(g.texture, &options)\n\tg.display.draw(screen)'),
        ('func (g *windowGame) Layout(int, int) (int, int) { return 1280, 800 }',
         'func (g *windowGame) Layout(int, int) (int, int) { return 1280, 800+prototypeToolbarHeight }'),
        ('g := &windowGame{m: m, d: d, out: out, lastX: -1, lastY: -1}',
         'g := &windowGame{m: m, d: d, out: out, lastX: -1, lastY: -1, render: render}'),
        ('\tdumpJSON(out+".status.json", map[string]any{"step": 0, "stage": "opening"})',
         '\tg.display = newDisplayUIPrototype()\n'
         '\tdefer func() { for _, face := range g.display.fonts.faces { face.Close() } }()\n'
         '\tdumpJSON(out+".status.json", map[string]any{"step": 0, "stage": "opening"})'),
        ('ebiten.SetWindowSize(1280, 800)', 'ebiten.SetWindowSize(1280, 800+prototypeToolbarHeight)'),
    ]
    for old, new in edits:
        window = replace_once(window, old, new)
    (output / "window.go").write_text(window)
    for source, target in [("display_settings_ui_prototype.go", "display_ui.go"),
                           ("display_settings_ui_prototype_test.go", "display_ui_test.go")]:
        (output / target).write_bytes((ROOT / "tools" / source).read_bytes())
    mod = (output / "go.mod").read_text()
    mod = replace_once(mod, 'require github.com/hajimehoshi/ebiten/v2 v2.9.9',
                       'require (\n github.com/hajimehoshi/ebiten/v2 v2.9.9\n golang.org/x/image v0.31.0\n)')
    (output / "go.mod").write_text(mod)
    subprocess.run(["gofmt", "-w", *map(str, sorted(output.glob("*.go")))], check=True, timeout=30)
    sources = {name: sha((ROOT / name).read_bytes()) for name in SOURCE_HASHES}
    for name in [Path(__file__).name, "display_settings_ui_prototype.go", "display_settings_ui_prototype_test.go"]:
        sources["tools/" + name] = sha((ROOT / "tools" / name).read_bytes())
    sources["text/frontend-ui.tsv"] = sha((ROOT / "text/frontend-ui.tsv").read_bytes())
    result = {"kind": "draft-display-settings-runtime-prototype-not-release", "source_sha256": sources,
              "assembled_sha256": {p.name: sha(p.read_bytes()) for p in output.iterdir() if p.is_file()},
              "limitations": ["UI font is a candidate; game font choice remains pending.",
                              "Only existing zh-Hant and original English gameplay display can activate.",
                              "Other game language packs and HD are not installed."]}
    (output / "prototype-sources.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("ASSEMBLED_DRAFT_DISPLAY_SETTINGS_PROTOTYPE", output)


if __name__ == "__main__":
    main()
