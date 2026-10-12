"""規格061 DRAFT隔離組裝：只改正式前端的可丟棄副本，不接正式建置。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--output-dir", type=Path, required=True)
a = p.parse_args()
repo = Path(__file__).resolve().parents[1]
out = a.output_dir.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo / "workplace")
assert out.parent.stat().st_uid == os.getuid() and not out.exists()
formal = repo / "workplace/reports/goal186-display-hd/language-resources-20261011/map-source-padding-r27/formal-runtime"
sha = lambda x: hashlib.sha256(x.read_bytes()).hexdigest()
bindings = json.loads((formal / "observation-sources.json").read_bytes())["source_sha256"]
assert len(bindings) == 14
for name, expected in bindings.items():
    assert sha(repo / name) == expected, name
out.mkdir()
module = out / "runtime"
shutil.copytree(formal, module)
shutil.copyfile(repo / "tools/hd_runtime_prototype.go", module / "hd_runtime_prototype.go")
shutil.copyfile(repo / "tools/hd_runtime_prototype_test.go", module / "hd_runtime_prototype_test.go")
s = (module / "adapter.go").read_text()
def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)

s = replace_once(s, "\tvar draftLive *draftLanguageBackend", """
 var hd *hdPrototype
 if *hdPrototypeAsset != "" {
  if !languageLive || *control { panic("HD prototype requires active language bundles without control") }
  var err error
  hd,err=newHDPrototype(m,*hdPrototypeAsset);must(err)
 }
 var draftLive *draftLanguageBackend""")
s = replace_once(s, "&draftLanguageBackend{targets: draftTargets,", "&draftLanguageBackend{hd:hd,targets: draftTargets,")
anchor = "m.SetBeforeInstruction(func() {"
assert s.count(anchor) == 2
s = s.replace(anchor, anchor + "\n            hd.beforeInstruction()")
(module / "adapter.go").write_text(s)
s = (module / "language_rebuild_probe.go").read_text()
s = replace_once(s, "type draftLanguageBackend struct {", "type draftLanguageBackend struct {\n hd *hdPrototype")
s = replace_once(s, 'options.Graphics != "original" || target == nil', '(options.Graphics != "original" && (options.Graphics != "hd" || b.hd == nil)) || target == nil')
s = replace_once(s, "draftRebuildTarget(target, f.journal, f.canvas, f.buffer, f.indexed, f.palette, f.cursor, f.step, f.mode)",
                 "b.rebuildWithHD(target,options,f)")
s = replace_once(s, "draftRebuildTarget(b.active.target, f.journal, f.canvas, f.buffer, f.indexed, f.palette, f.cursor, f.step, f.mode)",
                 "b.rebuildWithHD(b.active.target,b.active.options,f)")
s = s.replace("nativeKey: f.key()", "nativeKey: f.key()+b.hd.key()")
s = replace_once(s, "key := f.key()", "key := f.key()+b.hd.key()")
signature = "func draftRebuildTarget(t *draftLanguageTarget, j *nativeJournal, canvas, buffer, indexed, palette []byte, cursor image.Rectangle, step uint64, mode byte) (*image.RGBA, map[string]any, error) {"
s = replace_once(s, signature, signature + """
 return draftRebuildTargetOn(t,j,canvas,buffer,indexed,palette,cursor,step,mode,nil)
}
func draftRebuildTargetOn(t *draftLanguageTarget, j *nativeJournal, canvas, buffer, indexed, palette []byte, cursor image.Rectangle, step uint64, mode byte, base *image.RGBA) (*image.RGBA, map[string]any, error) {""")
s = replace_once(s, "out := draftRGB(indexed, palette)", "out := base\n if out == nil {out=draftRGB(indexed,palette)}")
(module / "language_rebuild_probe.go").write_text(s)
subprocess.run(["gofmt", "-w", "adapter.go", "language_rebuild_probe.go", "hd_runtime_prototype.go"], cwd=module, check=True, timeout=30)
binary = out / "hd-runtime-prototype"
subprocess.run(["go", "build", "-trimpath", "-o", str(binary), "."], cwd=module, check=True, timeout=150)
subprocess.run(["go", "vet", "."], cwd=module, check=True, timeout=120)
record = {"kind": "discardable HD runtime prototype", "production_connected": False,
          "base_bindings": bindings, "binary_sha256": sha(binary),
          "prototype_sha256": sha(repo / "tools/hd_runtime_prototype.go"),
          "builder_sha256": sha(Path(__file__)),
          "module_sha256": {x.name: sha(x) for x in module.glob("*.go")}}
(out / "build.json").write_text(json.dumps(record, indent=2) + "\n")
print("PASS_HD_RUNTIME_PROTOTYPE_BUILD_AND_VET", flush=True)
