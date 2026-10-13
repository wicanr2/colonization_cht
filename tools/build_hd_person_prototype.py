"""規格063 DRAFT：組裝使用者已確認的人物原型，不更動正式入口。"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
parser=argparse.ArgumentParser(description=__doc__)
for name in ["output","reference","base-bundle"]:
 parser.add_argument("--"+name,type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];out=args.output.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo/"workplace")
assert out.is_dir() and out.stat().st_uid==os.getuid()
assert args.reference.is_dir() and args.base_bundle.is_dir()
helper="package main\nimport (\n \"encoding/json\"\n \"flag\"\n \"fmt\"\n \"image\"\n \"image/png\"\n \"os\"\n \"path/filepath\"\n \"regexp\"\n golem \"github.com/wicanr2/dosgolem\"\n)\nvar hdPersonPrototypeAsset=flag.String(\"hd-person-prototype-asset\",\"\",\"規格063 DRAFT：使用者確認的人物原圖，僅供隔離驗證\")\nvar hdPersonProbeRoot=flag.String(\"hd-person-probe-root\",\"\",\"DRAFT診斷輸出目錄\")\nvar hdPersonActive *hdPersonPrototype\nfunc personProbeDump(prefix string) {\n p:=hdPersonActive;if p==nil||!p.trace {return}\n dumpJSON(prefix+\".person.json\",map[string]any{\"prototype\":true,\"calls\":p.calls,\"cursor_pairs\":p.pairs,\"accepted\":p.accepted,\"rejected\":p.rejected,\"cursor_paints\":p.cursorPaints,\"cursor_restores\":p.cursorRestores})\n}\nfunc personProbeFrame(im *image.RGBA,record map[string]any) {\n p:=hdPersonActive\n if p==nil||*hdPersonProbeRoot==\"\"||activeWindow==nil||im==nil {return}\n marker:=filepath.Join(*hdPersonProbeRoot,\"person-request.json\")\n info,err:=os.Lstat(marker);if os.IsNotExist(err){return};must(err)\n if !info.Mode().IsRegular()||info.Mode()&os.ModeSymlink!=0||info.Size()>1024 {panic(\"人物診斷請求不是有界檔案\")}\n var req struct { Label string `json:\"label\"`; MinStep uint64 `json:\"min_step\"`; Buttons uint16 `json:\"buttons\"` }\n must(json.Unmarshal(read(marker),&req))\n if !regexp.MustCompile(\"^[a-z0-9-]{1,64}$\").MatchString(req.Label) {panic(\"人物診斷標籤不同\")}\n m,d:=p.h.m,activeWindow.d\n if m.Steps<req.MinStep||d.Mouse.Buttons!=req.Buttons {return}\n destination:=filepath.Join(*hdPersonProbeRoot,req.Label);must(os.Mkdir(destination,0755))\n state:=map[string]any{\"step\":m.Steps,\"cycles\":m.CPU.Cycles,\"memory_sha256\":hash(m.Mem),\"indexed_sha256\":hash(m.Indexed()),\"palette_sha256\":hash(m.DAC[:]),\n  \"registers\":m.CPU.R,\"segments\":m.CPU.Seg,\"ip\":m.CPU.IP,\"flags\":m.CPU.Flags,\"dos_input_count\":len(activeWindow.inputs),\n  \"dos_mouse\":map[string]any{\"x\":d.Mouse.X,\"y\":d.Mouse.Y,\"buttons\":d.Mouse.Buttons}}\n f:=draftNativeFrame{canvas:m.Mem[hdBuildingCanvas:hdBuildingCanvas+64000],indexed:m.Indexed(),palette:m.DAC[:],cursor:image.Rect(int(d.Mouse.X),int(d.Mouse.Y),int(d.Mouse.X)+16,int(d.Mouse.Y)+16),step:m.Steps,mode:m.VideoMode()}\n cells:=map[int]map[string]any{}\n for i,c:=range p.visible {if c.owned {cells[i]=map[string]any{\"local\":c.local,\"native\":c.native}}}\n for n,data:=range map[string][]byte{\"memory\":m.Mem,\"indexed\":m.Indexed(),\"canvas\":f.canvas,\"palette\":m.DAC[:],\"cursor-background\":m.Mem[0xafa00:0xafb00],\"cursor-final\":m.Mem[0xafb00:0xafc00],\"cursor-source\":m.Mem[0x1cd74:0x1ce74]} {must(os.WriteFile(filepath.Join(destination,n),data,0644))}\n file,err:=os.Create(filepath.Join(destination,\"display.png\"));must(err);must(png.Encode(file,im));must(file.Close())\n dumpJSON(filepath.Join(destination,\"check.json\"),map[string]any{\"prototype\":true,\"state\":state,\"frame\":record,\"person\":p.receipt(f),\"cells\":cells,\"cursor_source_sha256\":hash(m.Mem[0x1cd74:0x1ce74]),\"call_count\":len(p.calls),\"cursor_pair_count\":len(p.pairs)})\n must(os.Remove(marker))\n fmt.Println(\"PERSON_SNAPSHOT\",req.Label,m.Steps,len(activeWindow.inputs))\n}\nvar _ *golem.Machine\n"
(out/"person_probe_helpers.go").write_text(helper)
module=out/"runtime-r1";assert not module.exists()
subprocess.run(["python3",str(repo/"tools/build_window_prototype.py"),"--repo","/repo","--output",str(module),"--reference",str(args.reference.resolve())],check=True,timeout=45)
shutil.copyfile(repo/"tools/hd_person_prototype.go",module/"hd_person_prototype.go")
shutil.copyfile(out/"person_probe_helpers.go",module/"person_probe_helpers.go")
p=module/"hd_runtime.go";s=p.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,a
 s=s.replace(a,b,1)
one("type hdRuntime struct {","type hdRuntime struct {\n person *hdPersonPrototype")
one('\tif h.sea != nil {\n\t\treturn fmt.Sprintf("/hd/%d/sea/%d", h.revision, h.sea.revision)\n\t}', '\tif h.sea != nil {\n if h.person!=nil {return fmt.Sprintf("/hd/%d/sea/%d/person/%d",h.revision,h.sea.revision,h.person.revision)}\n\t\treturn fmt.Sprintf("/hd/%d/sea/%d", h.revision, h.sea.revision)\n\t}')
one("\th.sea.beforeInstruction()","\th.sea.beforeInstruction()\n h.person.beforeInstruction()")
one('\treceipt["owned"], receipt["painted"], receipt["reason"] = owned, painted, "known-building"', '\tif h.person!=nil {receipt["person"]=h.person.paint(out,f)}\n\treceipt["owned"], receipt["painted"], receipt["reason"] = owned, painted, "known-building"')
p.write_text(s)
p=module/"adapter.go";s=p.read_text()
one('\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }',''' if *hdPersonPrototypeAsset!="" {
  var err error
  if hd==nil {panic("人物DRAFT需要既有HD組")}
  hd.person,err=loadHDPersonPrototype(hd,*root,*hdPersonPrototypeAsset);must(err)
  hdPersonActive=hd.person;hd.person.trace=*hdPersonProbeRoot!=""
  defer personProbeDump(*out)
 }
\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }''')
one('\t\tif label == "" {\n\t\t\tif frontendFrameSink != nil {','\t\tif label == "" {\n personProbeFrame(output,rec)\n\t\t\tif frontendFrameSink != nil {')
p.write_text(s)
test=repo/"tools/hd_person_prototype_test.go"
if test.exists():shutil.copyfile(test,module/test.name)
subprocess.run(["gofmt","-w",*[p.name for p in module.glob("*.go")]],cwd=module,check=True,timeout=30)
binary=out/"colonization-window-prototype"
subprocess.run(["go","build","-trimpath","-o",str(binary),"."],cwd=module,check=True,timeout=180)
subprocess.run(["go","vet","."],cwd=module,check=True,timeout=120)
shutil.copytree(args.base_bundle.resolve(),out/"bundle",symlinks=True)
shutil.copyfile(binary,out/"bundle/bin/colonization-window")
metadata={"kind":"DRAFT-person-100-v2-private-assembly","base_bindings":json.loads((module/"observation-sources.json").read_text()),"go_sources":{p.name:sha(p) for p in module.glob("*.go")},"binary_sha256":sha(binary),"person_source_sha256":sha(repo/"tools/hd_person_prototype.go"),"helper_source_sha256":sha(out/"person_probe_helpers.go")}
(out/"build-r1.json").write_text(json.dumps(metadata,indent=2)+"\n")
print("PASS_PERSON_PROTOTYPE_BUILD_AND_VET",sha(binary),flush=True)
