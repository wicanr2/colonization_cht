#!/usr/bin/env python3
"""規格060 DRAFT：隔離觀測完整原文run，不修改正式顯示來源。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
PINS = {
    "tools/live_menu.go": "2f5ab4b81a9608a14f05280cfaba5027472e648fda6e34d3db4ba8855d0a0a53",
    "tools/build_window_prototype.py": "4e16cca620b654915d59c044796ace6ce408d66f66623161ff53096c6fbd3a85",
    "tools/dialog_overlay.go": "b93dcf45c424b8aac175f71da0e05d54782d9ccc36774fdd1ac7f0bbd69e8a50",
    "tools/string_overlay.go": "9730c6095bbedb91497e3de0f2a773af32f30c8fdb0dcc9b60d1434d1ac61478",
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("reference", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--with-rebuild", action="store_true", help="連結規格060的暫停重建切片，仍不改正式來源")
    a = p.parse_args()
    output = a.output.resolve()
    if not (a.reference / "go.sum").is_file():
        raise ValueError("--reference需指向既有前端模組的go.sum目錄，不能用無此檔的dosgolem根目錄")
    if not Path("/.dockerenv").is_file() or not output.is_relative_to((ROOT / "workplace").resolve()) or \
            output.exists() or not output.parent.is_dir() or output.parent.stat().st_uid != os.getuid():
        raise ValueError("需Docker及新的workplace輸出，父目錄擁有者須相同")
    for name, digest in PINS.items():
        if sha((ROOT / name).read_bytes()) != digest:
            raise ValueError("正式來源不同：" + name)
    subprocess.run([sys.executable, str(ROOT / "tools/build_window_prototype.py"), "--repo", str(ROOT),
                    "--reference", str(a.reference), "--output", str(output)], check=True, timeout=30)
    s = (output / "adapter.go").read_text()
    replacements = {
        '\trawSource := read(filepath.Join(*root, "GAME.TXT"))\n':
            '\tnativeOn := *draftNativeCapture && validVersion\n\trawSource := read(filepath.Join(*root, "GAME.TXT"))\n',
        "type staticItem struct {\n":
            "type staticItem struct {\n\tnativeSource bool\n\tnativePrimary *byte\n",
        '\t\t\tif it.reason == "" {\n\t\t\t\tvar mask struct {\n':
            '''\t\t\tit.nativeSource = err == nil && hash(img) == get("image_sha256") && ok1 && ok2 && band.In(fp) && get("status") == "draft"
\t\t\tif raw := get("ink_indices"); raw != "" {
\t\t\t\tfor i, part := range strings.Split(raw, ",") {
\t\t\t\t\tv, e := strconv.Atoi(part)
\t\t\t\t\tif e != nil || v < 0 || v > 255 { it.nativeSource = false; break }
\t\t\t\t\tif i == 0 { primary := byte(v); it.nativePrimary = &primary }
\t\t\t\t}
\t\t\t}
\t\t\tif it.reason == "" {
\t\t\t\tvar mask struct {
''',
        '\t\t\t\tit.mask, it.reason = nil, "duplicate-key"\n':
            '\t\t\t\tit.mask, it.reason, it.nativeSource = nil, "duplicate-key", false\n',
        '\t\t\tif err != nil {\n\t\t\t\tstr.reason = "missing-or-invalid-translation"\n':
            '\t\t\tstr.cat = cat\n\t\t\tif err != nil {\n\t\t\t\tstr.reason = "missing-or-invalid-translation"\n',
        "\tseaOn := sea != nil && sea.glyphs != nil\n":
            "\tjournal := &nativeJournal{enabled: nativeOn}\n\tjournal.sample = func() nativeSurfaces { return nativeSurfaces{canvas(), m.Mem[0x3bb00:0x3bb00+64000], m.Mem[0xa0000:0xafa00], m.DAC[:], m.VideoMode()} }\n\tseaOn := sea != nil && (sea.glyphs != nil || nativeOn)\n",
        "\t\tinterleaved := len(ev.raw) == 2 && ev.raw[1] == 0\n":
            "\t\tjournal.captureSea(ev, canvas(), m.Steps)\n\t\tinterleaved := len(ev.raw) == 2 && ev.raw[1] == 0\n",
        "\t\t\tmenuRow := &seaRow{text: got, firstOld: map[int]byte{}, lastVal: map[int]byte{}}\n":
            "\t\t\tjournal.captureSeaRuns(sea.menuRun, canvas(), m.Steps)\n\t\t\tmenuRow := &seaRow{text: got, firstOld: map[int]byte{}, lastVal: map[int]byte{}}\n",
        "\tdialogFinish := func(r *dialogRun) {\n":
            "\tdialogFinish := func(r *dialogRun) {\n\t\tjournal.captureDialog(r, canvas(), m.Steps)\n",
        "\t\t\t\tif done := dlg.onRead(a, m.Mem[a], m.Steps); done != nil {\n\t\t\t\t\tdialogFinish(done)\n\t\t\t\t}\n":
            "\t\t\t\tif done := dlg.onRead(a, m.Mem[a], m.Steps); done != nil {\n\t\t\t\t\tdialogFinish(done)\n\t\t\t\t}\n\t\t\t\tif nativeOn { journal.observeDialogCursor(dlg.run, m.Mem[a], c.R[golem.DI], c.Seg[golem.ES]) }\n",
        "\tstringFinish := func(r *stringRun) {\n\t\tif r.buf2 {\n":
            "\tstringFinish := func(r *stringRun) {\n\t\tif r.buf2 {\n\t\t\tjournal.captureString(r, canvas(), m.Mem[0x3bb00:0x3bb00+64000], m.Steps)\n",
        "\t\tr = str.outline(r) // 目標170：描邊字（同文 1 像素位移重印）併成一串\n":
            "\t\tr = str.outline(r) // 目標170：描邊字（同文 1 像素位移重印）併成一串\n\t\tjournal.captureString(r, canvas(), m.Mem[0x3bb00:0x3bb00+64000], m.Steps)\n",
        "\trender := func(label string) {\n":
            "\trender := func(label string) {\n\t\tjournal.cursor = cursorBox(int(d.Mouse.X), int(d.Mouse.Y))\n\t\tjournal.buttons = d.Mouse.Buttons != 0\n\t\tjournal.expireFixed(canvas(), m.Mem[0xa0000:0xafa00], m.VideoMode(), m.DAC[:])\n\t\tjournal.observeStatics(statics, canvas(), m.Mem[0xa0000:0xafa00], m.DAC[:], m.Steps, m.VideoMode())\n",
        "overlay.NewPatch(p.before, after, 320, 200, l.safe())":
            "draftFixedPatch(journal, draftFixedMenu(l), p.before, after, m.Steps)",
        "overlay.NewPatch(title.before, canvas(), 320, 200, image.Rect(65, 44, 253, 59))":
            "draftFixedPatch(journal, draftFixedTitle(title), title.before, canvas(), m.Steps)",
        "overlay.NewPatch(f.before, canvas(), 320, 200, f.rect)":
            "draftFixedPatch(journal, draftFixedRetire(f), f.before, canvas(), m.Steps)",
        "overlay.NewPatch(before, canvas(), 320, 200, helpText)":
            "draftFixedPatch(journal, draftFixedLayered(help.id, helpText), before, canvas(), m.Steps)",
        "overlay.NewPatch(intro.before, canvas(), 320, 200, introPanel)":
            "draftFixedPatch(journal, draftFixedLayered(intro.page.id, introPanel), intro.before, canvas(), m.Steps)",
        "overlay.NewPatch(r.before, canvas(), 320, 200, optionRowSafe(i))":
            "draftFixedPatch(journal, draftFixedRow(r, i), r.before, canvas(), m.Steps)",
        "overlay.NewPatch(caption.before, canvas(), 320, 200, caption.safe)":
            "draftFixedPatch(journal, draftFixedCaption(caption), caption.before, canvas(), m.Steps)",
        "overlay.NewPatch(l.before, after, 320, 200, l.safe)":
            "draftFixedPatch(journal, draftFixedDifficulty(l), l.before, after, m.Steps)",
        "\tdumpJSON(*out+\".json\", report)\n":
            "\tif *draftNativeCapture {\n\t\tdumpJSON(*out+\".native.json\", journal.export(canvas(), m.Mem[0x3bb00:0x3bb00+64000], m.VideoMode(), m.Mem[0xa0000:0xafa00]))\n\t}\n\tdumpJSON(*out+\".json\", report)\n",
    }
    for old, new in replacements.items():
        if s.count(old) != 1:
            raise ValueError("觀測接點不唯一：" + old.strip())
        s = s.replace(old, new, 1)
    # 原文事件識別獨立於字模；合成部分仍保留原本的字型與控制模式守門。
    boundary = '\t\tif *control || (*displayUIEnabled && displayLanguage == "en") {\n'
    if s.count(boundary) != 1:
        raise ValueError("原文觀測與合成分界不唯一")
    prefix, suffix = s.split(boundary)
    source_gates = {
        "captionAnyInk = captionAnyInk || c.ink != nil": (1, "captionAnyInk = captionAnyInk || c.ink != nil || nativeOn"),
        "rowsAnyInk = rowsAnyInk || r.ink != nil": (1, "rowsAnyInk = rowsAnyInk || r.ink != nil || nativeOn"),
        "introAnyInk = introAnyInk || pg.normal != nil": (1, "introAnyInk = introAnyInk || pg.normal != nil || nativeOn"),
        "retireAnyInk = retireAnyInk || f.ink != nil": (1, "retireAnyInk = retireAnyInk || f.ink != nil || nativeOn"),
        "helpAnyInk := help != nil && help.normal != nil": (1, "helpAnyInk := help != nil && (help.normal != nil || nativeOn)"),
        'dlgOn := dlg != nil && dlg.fontReason == ""': (1, 'dlgOn := dlg != nil && (dlg.fontReason == "" || nativeOn)'),
        'strOn := str != nil && str.reason == ""': (1, 'strOn := str != nil && (str.reason == "" || nativeOn)'),
        "title != nil && title.ink != nil": (3, "title != nil && (title.ink != nil || nativeOn)"),
        "caption.ink == nil ||": (2, "(caption.ink == nil && !nativeOn) ||"),
        "!*control": (11, "(!*control || nativeOn)"),
        "|| *control": (2, "|| (*control && !nativeOn)"),
    }
    for old, (count, new) in source_gates.items():
        if prefix.count(old) != count:
            raise ValueError(f"原文守門數量不同：{old}: {prefix.count(old)} != {count}")
        prefix = prefix.replace(old, new)
    sea_layers = "\t\t\tfor _, layer := range []*seaLayer{sea.bar, sea.panel} {\n"
    if prefix.count(sea_layers) != 1:
        raise ValueError("海上原文收尾與舊字模建構分界不唯一")
    prefix = prefix.replace(sea_layers, sea_layers +
                            "\t\t\t\tif sea.glyphs == nil || *control { continue }\n", 1)
    s = prefix + boundary + suffix
    # 同時保存收尾時的原版游標位置，供重建與遮擋檢查回查。
    for call in ("journal.captureSea(", "journal.captureSeaRuns(", "journal.captureDialog(", "journal.captureString(",
                 "draftFixedPatch("):
        lines = s.splitlines(keepends=True)
        s = "".join((line[:len(line)-len(line.lstrip())] +
                     "journal.cursor = cursorBox(int(d.Mouse.X), int(d.Mouse.Y))\n" + line)
                    if call in line else line for line in lines)
    (output / "adapter.go").write_text(s)
    for name in ("language_observations.go", "language_observations_test.go"):
        (output / name).write_bytes((ROOT / "tools" / name).read_bytes())
    extra_sources = []
    if a.with_rebuild:
        extra_sources = ["tools/language_bundle_probe.go", "tools/language_rebuild_probe.go", "tools/language_rebuild_probe_test.go"]
        for name in extra_sources:
            (output / Path(name).name).write_bytes((ROOT / name).read_bytes())
        old = "\tjournal := &nativeJournal{enabled: nativeOn}\n"
        new = old + """\tvar draftTargets map[string]*draftLanguageTarget
\tif *draftNativeBundles != "" {
\t\tif !*draftNativeCapture { panic("重建原型需要完整原文觀測") }
\t\tfiles := map[string][]byte{}
\t\tfor _, name := range []string{"LABELS.TXT", "NAMES.TXT", "WOODCUT.TXT", "COLONY.TXT", "MENU.TXT", "GAME.TXT", "PEDIA.TXT", "VICEROY.EXE"} {
\t\t\tfiles[name] = read(filepath.Join(*root, name))
\t\t}
\t\thelpOwned := map[string]bool{}
\t\tif help != nil { helpOwned[help.id] = true }
\t\tvar err error
\t\tdraftTargets, err = draftPrepareTargets(*draftNativeBundles, files, dialogOwned, helpOwned)
\t\tmust(err)
\t}
\tvar draftLive *draftLanguageBackend
\tif *draftNativeLive {
\t\tif draftTargets == nil || !*displayUIEnabled || *control { panic("隔離視窗需要完整原文觀測、語言候選及設定列，不能混用原文控制") }
\t\tdraftLive = &draftLanguageBackend{targets: draftTargets, sample: func() draftNativeFrame {
\t\t\treturn draftNativeFrame{journal, canvas(), m.Mem[0x3bb00:0x3bb00+64000], m.Mem[0xa0000:0xafa00], m.DAC[:], cursorBox(int(d.Mouse.X),int(d.Mouse.Y)), m.Steps, m.VideoMode()}
\t\t}}
\t\tfrontendDisplayPrepare = func(options displayOptions) (func(), error) {
\t\t\tcommit, err := draftLive.prepare(options)
\t\t\tif err != nil { return nil, err }
\t\t\treturn func() { commit(); displayLanguage = options.Language }, nil
\t\t}
\t\tpreference, err := displayPreferencePath(*displayUIConfig)
\t\tmust(err)
\t\toptions, err := readDisplayPreferences(preference, *displayUIInitialLanguage, *displayUIInitialGraphics)
\t\tmust(err)
\t\tcommit, err := frontendDisplayPrepare(options)
\t\tmust(err)
\t\tcommit()
\t}
"""
        if s.count(old) != 1:
            raise ValueError("重建準備接點不唯一")
        s = s.replace(old, new, 1)
        old = '\t\tif *control || (*displayUIEnabled && displayLanguage == "en") {\n'
        new = '''\t\tvar draftLiveRecord map[string]any
\t\tif draftLive != nil {
\t\t\tvar err error
\t\t\toutput, draftLiveRecord, err = draftLive.renderCurrent()
\t\t\tmust(err)
\t\t\tlineRecords, _ = draftLiveRecord["items"].([]map[string]any)
\t\t\tapplied, reason = len(lineRecords) > 0, "draft-native-live"
\t\t} else if *control || (*displayUIEnabled && displayLanguage == "en") {
'''
        if s.count(old) != 1:
            raise ValueError("隔離視窗影像分支不唯一")
        s = s.replace(old, new, 1)
        old = '\t\tif strOn && !*control && !(*displayUIEnabled && displayLanguage == "en") {\n'
        if s.count(old) != 1:
            raise ValueError("隔離視窗與舊字串合成分界不唯一")
        s = s.replace(old, old.replace("if strOn", "if draftLive == nil && strOn"), 1)
        old = '\t\tif label == "" {\n'
        new = '\t\tif draftLiveRecord != nil { rec["native_live"] = draftLiveRecord }\n' + old
        if s.count(old) != 1:
            raise ValueError("隔離視窗收據出口不唯一")
        s = s.replace(old, new, 1)
        old = '\tdumpJSON(*out+".json", report)\n'
        new = """\tif draftTargets != nil {
\t\tbeforeRAM, beforeSteps, beforeTicks, beforeFrames := hash(m.Mem), m.Steps, m.Ticks, m.Frames
\t\tbeforeCPU := *m.CPU
\t\tmust(draftExportRebuilds(draftTargets, journal, canvas(), m.Mem[0x3bb00:0x3bb00+64000], m.Mem[0xa0000:0xafa00], m.DAC[:], cursorBox(int(d.Mouse.X),int(d.Mouse.Y)),m.Steps,m.VideoMode(),*out))
\t\tif beforeRAM != hash(m.Mem) || beforeSteps != m.Steps || beforeTicks != m.Ticks || beforeFrames != m.Frames || beforeCPU.R != m.CPU.R || beforeCPU.Seg != m.CPU.Seg || beforeCPU.IP != m.CPU.IP || beforeCPU.Flags != m.CPU.Flags || beforeCPU.Cycles != m.CPU.Cycles {
\t\t\tpanic("暫停重建改變原版狀態")
\t\t}
\t\treport["draft_rebuild_native_state_unchanged"] = true
\t}
""" + old
        if s.count(old) != 1:
            raise ValueError("重建輸出接點不唯一")
        s = s.replace(old, new, 1)
        (output / "adapter.go").write_text(s)
    subprocess.run(["gofmt", "-w", str(output / "adapter.go"), str(output / "language_observations.go"),
                    str(output / "language_observations_test.go")], check=True, timeout=30)
    for name in extra_sources:
        subprocess.run(["gofmt", "-w", str(output / Path(name).name)], check=True, timeout=30)
    sources = {name: sha((ROOT / name).read_bytes()) for name in [*PINS, "tools/build_language_observation_probe.py",
                                                               "tools/language_observations.go", "tools/language_observations_test.go", *extra_sources]}
    (output / "observation-sources.json").write_text(json.dumps({"kind": "DRAFT-native-observation-probe", "source_sha256": sources,
        "reference_go_sum_sha256": sha((a.reference / "go.sum").read_bytes())}, indent=2) + "\n")
    print("ASSEMBLED_DRAFT_NATIVE_OBSERVATION_PROBE", output)


if __name__ == "__main__":
    main()
