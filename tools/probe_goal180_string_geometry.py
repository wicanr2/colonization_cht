#!/usr/bin/env python3
"""只在 Docker 組裝可丟棄漏譯量測前端；不改正式來源或原版。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--source", type=Path, required=True)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--pedia-bullet-prototype", action="store_true", help="只在可丟棄組裝試驗DRAFT項目符號配對")
a = p.parse_args()
if a.output.exists() or a.output.parent.stat().st_uid != os.getuid():
    raise ValueError("輸出已存在或父目錄擁有者不符")
source = (a.source / "strings.go").read_text()
if source != Path("/repo/tools/string_overlay.go").read_text():
    raise ValueError("可丟棄前端必須使用當前正式字串來源")
start = source.index("func (s *stringRuntime) finish(")
end = source.index("// 地圖視窗", start)
body = source[start:end]
old = '\tif why != "" {\n\t\treturn nil, why\n\t}'
if body.count(old) != 1:
    raise ValueError("量測掛鉤位置不唯一")
new = '''\tif why != "" {
        raw, _ := json.Marshal(map[string]any{
            "entry_ip": "0D21:00C6", "source_linear": r.base,
            "start": r.start, "step": step, "shown": text, "reason": why,
            "ink": [4]int{ink.Min.X, ink.Min.Y, ink.Max.X, ink.Max.Y},
            "safe": [4]int{safe.Min.X, safe.Min.Y, safe.Max.X, safe.Max.Y},
            "cap_height": capH, "color": color, "pedia_header_visible": pediaHeaderVisible,
        })
        fmt.Fprintln(os.Stderr, "STRING_DIAGNOSTIC " + string(raw))
        return nil, why
    }'''
source = source[:start] + body.replace(old, new) + source[end:]
anchor = '\tzh, id, why := s.translateObserved(text, canvas)'
start = source.index("func (s *stringRuntime) finish(")
end = source.index("// 地圖視窗", start)
body = source[start:end]
if body.count(anchor) != 1:
    raise ValueError("場景量測掛鉤位置不唯一")
body = body.replace(anchor, '''    pediaHeaderVisible := false
    for _, item := range s.items {
        if item.text == "ENCYCLOPEDIA OF COLONIZATION" && !item.safe.Empty() &&
            bytes.Equal(stringRect(canvas, item.safe), item.after) {
            pediaHeaderVisible = true
        }
    }
''' + anchor, 1)
source = source[:start] + body + source[end:]
start = source.index("func (s *stringRuntime) finish(")
end = source.index("// 地圖視窗", start)
body = source[start:end]
old = '\tif n == nil {\n\t\treturn nil, "does-not-fit"\n\t}'
if body.count(old) != 1:
    raise ValueError("未適配欄位掛鉤位置不唯一")
new = '''    if n == nil {
        raw, _ := json.Marshal(map[string]any{
            "entry_ip": "0D21:00C6", "source_linear": r.base,
            "start": r.start, "step": step, "shown": text, "reason": "does-not-fit", "zh": zh,
            "ink": [4]int{ink.Min.X, ink.Min.Y, ink.Max.X, ink.Max.Y},
            "safe": [4]int{safe.Min.X, safe.Min.Y, safe.Max.X, safe.Max.Y},
            "cap_height": capH, "color": color, "pedia_header_visible": pediaHeaderVisible,
        })
        fmt.Fprintln(os.Stderr, "STRING_DIAGNOSTIC " + string(raw))
        return nil, "does-not-fit"
    }'''
source = source[:start] + body.replace(old, new) + source[end:]
extra = ''.join(' "' + name + '"\n' for name in ("bytes", "encoding/json", "os") if '"' + name + '"' not in source)
source = source.replace('import (\n', 'import (\n' + extra, 1)
dialog = (a.source / "dialog.go").read_text()
if a.pedia_bullet_prototype:
    anchor = '\tif r := d.run; r != nil && step-r.last < dialogGap {'
    if dialog.count(anchor) != 1:
        raise ValueError("項目符號候選位置不唯一")
    dialog = dialog.replace(anchor, anchor + '''
        if !r.contig && r.readPos%2 == 1 && a == r.base && len(r.chars)>0 {
            last := r.chars[len(r.chars)-1]
            if last.c == 0xF9 && last.box.Empty() { r.readPos++ }
        }
''', 1)
    anchor = 'if ch.c != 0 && !dialogHotkeyMark(ch) {'
    if dialog.count(anchor) != 2:
        raise ValueError("非印字來源候選位置不唯一")
    dialog = dialog.replace(anchor, 'if ch.c != 0 && !dialogHotkeyMark(ch) && !(ch.c == 0xF9 && ch.box.Empty()) {')
    anchor = 'shownBody := strings.ReplaceAll(string(body), "%%", "%")'
    if dialog.count(anchor) != 1:
        raise ValueError("百科来源候選位置不唯一")
    dialog = dialog.replace(anchor, 'shownBody := strings.NewReplacer("%%", "%", "\\u00F9", "").Replace(string(body))', 1)
anchor = '\t\t\t\t\td.run = nil // 連續字串'
if dialog.count(anchor) != 1:
    raise ValueError("丟棄段落掛鉤位置不唯一")
dialog = dialog.replace(anchor, '\t\t\t\t\tprobePediaRun(r, step, "onRead-continuous-drop")\n' + anchor, 1)
anchor = '\tif r == nil || r.readPos%2 == 1 {\n\t\treturn nil, "", ""\n\t}'
if dialog.count(anchor) != 1:
    raise ValueError("段落完整性掛鉤位置不唯一")
dialog = dialog.replace(anchor, '\tprobePediaRun(r, step, "finish-entry")\n' + anchor, 1)
dialog += '''
// probePediaRun 只記錄原始事件與幾何，不修改機器、段落或覆蓋狀態。
func probePediaRun(r *dialogRun, step uint64, where string) {
    if r == nil || len(r.chars) < 100 { return }
    raw := make([]byte, len(r.chars))
    var ink image.Rectangle
    for i, ch := range r.chars { raw[i] = ch.c; ink = ink.Union(ch.box) }
    b, _ := json.Marshal(map[string]any{
        "where": where, "source_linear": r.base, "read_pos": r.readPos,
        "start": r.start, "step": step, "raw_hex": fmt.Sprintf("%x", raw),
        "ink": [4]int{ink.Min.X, ink.Min.Y, ink.Max.X, ink.Max.Y},
    })
    fmt.Fprintln(os.Stderr, "PEDIA_RUN_DIAGNOSTIC " + string(b))
}
'''
anchor = "\tnormalC, accentC, shadowC := runStyle(r)"
if dialog.count(anchor) != 1:
    raise ValueError("正文幾何掛鉤位置不唯一")
dialog = dialog.replace(anchor, '''    if len(shown) > 100 {
        capH := 0
        for _, line := range lines { capH = max(capH, line.capH) }
        safe := ink.Inset(-2).Intersect(image.Rect(0,0,320,200))
        raw, _ := json.Marshal(map[string]any{
            "entry_ip": "0D21:00C6", "source_linear": r.base,
            "start": r.start, "step": step,
            "shown_sha256": fmt.Sprintf("%x", sha256.Sum256([]byte(shown))),
            "ink": [4]int{ink.Min.X, ink.Min.Y, ink.Max.X, ink.Max.Y},
            "safe": [4]int{safe.Min.X, safe.Min.Y, safe.Max.X, safe.Max.Y},
            "cap_height": capH, "pitch": observedPitch(lines,10),
        })
        fmt.Fprintln(os.Stderr, "PEDIA_BODY_DIAGNOSTIC " + string(raw))
    }
''' + anchor, 1)
dialog = dialog.replace('import (\n', 'import (\n "os"\n', 1)
a.output.mkdir()
hashes = {}
for file in a.source.iterdir():
    if file.suffix == ".go" or file.name in ("go.mod", "go.sum", "go.work"):
        raw = file.read_bytes()
        hashes[file.name] = hashlib.sha256(raw).hexdigest()
        (a.output / file.name).write_bytes(raw)
(a.output / "strings.go").write_text(source)
(a.output / "dialog.go").write_text(dialog)
(a.output / "diagnostic-source.json").write_text(json.dumps({
    "original_sources": hashes,
    "instrumented_sha256": hashlib.sha256(source.encode()).hexdigest(),
    "instrumented_dialog_sha256": hashlib.sha256(dialog.encode()).hexdigest(),
    "pedia_bullet_prototype": a.pedia_bullet_prototype,
    "scope": "DRAFT項目符號分段候選；只在可丟棄組裝啟用，不修改機器狀態" if a.pedia_bullet_prototype else "只記錄未翻譯字串的原始墨跡與安全區；不改翻譯或機器狀態",
}, ensure_ascii=False, indent=1) + "\n")
print(a.output)
