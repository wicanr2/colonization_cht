#!/usr/bin/env python3
"""規格062 DRAFT：組裝可丟棄海洋原型；不修改正式前端。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path, required=True)
parser.add_argument("--reference", type=Path, required=True, help="含固定go.sum的既有正式組裝目錄")
args = parser.parse_args()
repo = Path(__file__).resolve().parents[1]
out = args.output_dir.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo / "workplace")
assert out.parent.is_dir() and (out.parent.stat().st_uid, out.parent.stat().st_gid) == (os.getuid(), os.getgid())
assert not out.exists() and (args.reference / "go.sum").is_file()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
out.mkdir()
module = out / "runtime"
subprocess.run(["python3", str(repo / "tools/build_window_prototype.py"), "--repo", str(repo),
                "--output", str(module), "--reference", str(args.reference)], check=True, timeout=45)
bindings = json.loads((module / "observation-sources.json").read_bytes())["source_sha256"]
assert len(bindings) == 16
for name, digest in bindings.items():
    assert sha(repo / name) == digest, name
base_sources = {p.name: sha(p) for p in module.glob("*.go")}
for src, dest in [("hd_sea_prototype.go", "hd_sea_runtime_prototype.go"),
                  ("hd_sea_prototype_test.go", "hd_sea_runtime_prototype_test.go")]:
    shutil.copyfile(repo / "tools" / src, module / dest)

def one(s, old, new):
    assert s.count(old) == 1, old
    return s.replace(old, new, 1)

p = module / "adapter.go"
s = one(p.read_text(), "\tfrontendDisplayStartupOptions =", """ if *hdSeaPrototypeAsset!="" {
  if hd==nil {panic("sea prototype requires verified building runtime")}
  var err error
  hd.sea,err=loadHDSeaPrototype(hd,*root,*hdSeaPrototypeAsset);must(err)
 }
\tfrontendDisplayStartupOptions =""")
p.write_text(s)
p = module / "hd_runtime.go"
s = one(p.read_text(), "type hdRuntime struct {", "type hdRuntime struct {\n sea *hdSeaPrototype")
s = one(s, 'return fmt.Sprintf("/hd/%d", h.revision)',
        'if h.sea!=nil{return fmt.Sprintf("/hd/%d/sea/%d",h.revision,h.sea.revision)}\n return fmt.Sprintf("/hd/%d", h.revision)')
s = one(s, "\tm := h.m\n\tc := m.CPU", "\th.sea.beforeInstruction()\n\tm := h.m\n\tc := m.CPU")
s = one(s, "\towned, painted := 0, 0", '\tif h.sea!=nil {receipt["sea"]=h.sea.paint(out,f)}\n\towned, painted := 0, 0')
p.write_text(s)
subprocess.run(["gofmt", "-w", "adapter.go", "hd_runtime.go", "hd_sea_runtime_prototype.go",
                "hd_sea_runtime_prototype_test.go"], cwd=module, check=True, timeout=30)
binary = out / "colonization-sea-prototype"
subprocess.run(["go", "build", "-trimpath", "-o", str(binary), "."], cwd=module, check=True, timeout=180)
subprocess.run(["go", "vet", "."], cwd=module, check=True, timeout=120)
record = {"kind": "DRAFT-isolated-sea-prototype", "production_connected": False,
          "base_source_bindings": bindings, "base_module_sha256": base_sources,
          "binary_sha256": sha(binary), "builder_sha256": sha(Path(__file__)),
          "prototype_sha256": sha(repo / "tools/hd_sea_prototype.go"),
          "test_sha256": sha(repo / "tools/hd_sea_prototype_test.go"),
          "module_sha256": {p.name: sha(p) for p in module.glob("*.go")}}
(out / "build.json").write_text(json.dumps(record, indent=2) + "\n")
assert all((p.stat().st_uid, p.stat().st_gid) == (os.getuid(), os.getgid()) for p in out.rglob("*"))
print("PASS_SEA_PROTOTYPE_BUILD_AND_VET", sha(out / "build.json"), flush=True)
