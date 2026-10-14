"""規格064 R42 DRAFT：九來源隔離顯示組裝，正式入口不變。"""
import argparse,ast,hashlib,json,os,re,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for name in ["output","reference","base-bundle"]:p.add_argument("--"+name,type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert (out.is_relative_to(Path("/out")) or out.is_relative_to(repo/"workplace")) and out.is_dir() and out.stat().st_uid==os.getuid()
for d in [a.reference,a.base_bundle]:assert d.is_dir()
base_helper=repo/"tools/build_hd_person_prototype.py"
node=next(n for n in ast.parse(base_helper.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="helper" for t in n.targets))
helper=ast.literal_eval(node.value)
helper=helper.replace("hdPerson","hdNine").replace("HDPerson","HDNine").replace("person","nine").replace("PERSON","NINE").replace("人物","九來源").replace("規格063","規格064")
helper=helper.replace("hdNinePrototypeAsset","hdNinePrototypeAssets").replace("hd-nine-prototype-asset","hd-nine-prototype-assets")
helper=helper.replace("使用者確認的九來源原圖","已記錄的九張生成素材目錄")
helper,n=re.subn(r',\s*"cursor_paints"\s*:\s*p\.cursorPaints\s*,\s*"cursor_restores"\s*:\s*p\.cursorRestores',"",helper);assert n==1
helper,n=re.subn(r'"local"\s*:\s*c\.local,','"ordinal":p.frames[c.slot].ordinal,"local":c.local,',helper);assert n==1
old='Buttons uint16 `json:"buttons"` }'
assert helper.count(old)==1
helper=helper.replace(old,'Buttons uint16 `json:"buttons"`; Ordinal int `json:"ordinal"`; Locale string `json:"locale"`; RequireHD bool `json:"require_hd"` }')
old=' destination:=filepath.Join(*hdNineProbeRoot,req.Label);must(os.Mkdir(destination,0755))'
assert helper.count(old)==1
helper=helper.replace(old,''' if req.RequireHD {
  live,_:=record["native_live"].(map[string]any);hd,_:=live["hd"].(map[string]any)
  nine,_:=hd["nine"].(map[string]any);sources,_:=nine["sources"].(map[string]any)
  source,_:=sources[fmt.Sprint(req.Ordinal)].(map[string]any);painted,_:=source["painted"].(int)
  if live["locale"]!=req.Locale || hd["reason"]!="known-building" || painted<=0{return}
 }
'''+old)
(out/"nine_probe_helpers.go").write_text(helper)
module=out/"runtime-r1";assert not module.exists()
subprocess.run(["python3",str(repo/"tools/build_window_prototype.py"),"--repo","/repo","--output",str(module),"--reference",str(a.reference.resolve())],check=True,timeout=45)
for name in ["hd_building_nine_prototype.go","hd_building_nine_prototype_test.go"]:shutil.copyfile(repo/"tools"/name,module/name)
shutil.copyfile(out/"nine_probe_helpers.go",module/"nine_probe_helpers.go")
def edit(path,pairs):
 s=path.read_text()
 for old,new in pairs:
  assert s.count(old)==1,(path,old,s.count(old));s=s.replace(old,new,1)
 path.write_text(s)
anchor='return fmt.Sprintf("/hd/%d/sea/%d/person/%d/shelter/%d", h.revision, h.sea.revision, h.person.revision, h.shelter.revision)'
edit(module/"hd_runtime.go",[
 ("type hdRuntime struct {","type hdRuntime struct {\n nine *hdNinePrototype"),
 (anchor,'if h.nine!=nil{return fmt.Sprintf("/hd/%d/sea/%d/person/%d/shelter/%d/nine/%d",h.revision,h.sea.revision,h.person.revision,h.shelter.revision,h.nine.revision)}\n'+anchor),
 ("\th.shelter.beforeInstruction()","\th.shelter.beforeInstruction()\n h.nine.beforeInstruction()"),
 ('\tif h.person != nil {\n\t\treceipt["person"] = h.person.paint(out, f)','\tif h.nine!=nil{receipt["nine"]=h.nine.paint(out,f)}\n\tif h.person != nil {\n\t\treceipt["person"] = h.person.paint(out, f)'),
])
edit(module/"adapter.go",[
 ('\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }',
  ' if *hdNinePrototypeAssets!="" {\n var err error\n if hd==nil{panic("九來源DRAFT需要既有HD組")}\n hd.nine,err=loadHDNinePrototype(hd,*root,*hdNinePrototypeAssets);must(err)\n hdNineActive=hd.nine;hd.nine.trace=*hdNineProbeRoot!=""\n defer nineProbeDump(*out)\n }\n\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }'),
 ('\t\tif label == "" {\n\t\t\tif frontendFrameSink != nil {','\t\tif label == "" {\n nineProbeFrame(output,rec)\n\t\t\tif frontendFrameSink != nil {'),
])
subprocess.run(["gofmt","-w",*[p.name for p in module.glob("*.go")]],cwd=module,check=True,timeout=30)
binary=out/"colonization-window-prototype"
subprocess.run(["go","build","-trimpath","-o",str(binary),"."],cwd=module,check=True,timeout=180)
subprocess.run(["go","vet","."],cwd=module,check=True,timeout=120)
shutil.copytree(a.base_bundle.resolve(),out/"bundle",symlinks=True);shutil.copyfile(binary,out/"bundle/bin/colonization-window")
meta={"kind":"DRAFT-nine-private-assembly","base_bindings":json.loads((module/"observation-sources.json").read_text()),"go_sources":{p.name:sha(p) for p in module.glob("*.go")},"binary_sha256":sha(binary),"prototype_source_sha256":sha(repo/"tools/hd_building_nine_prototype.go"),"helper_base_sha256":sha(base_helper),"helper_source_sha256":sha(out/"nine_probe_helpers.go")}
(out/"build.json").write_text(json.dumps(meta,indent=2)+"\n");print("PASS_NINE_PROTOTYPE_BUILD_AND_VET",sha(binary),flush=True)
