"""規格064 DRAFT：第024幀木棚的隔離顯示組裝，不改正式入口。"""
import argparse,ast,hashlib,json,os,shutil,subprocess
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
for name in ["output","reference","base-bundle"]:
 parser.add_argument("--"+name,type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];out=args.output.resolve()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo/"workplace")
assert out.is_dir() and out.stat().st_uid==os.getuid()
for p in [args.reference,args.base_bundle]:assert p.is_dir()
base_helper=repo/"tools/build_hd_person_prototype.py"
node=next(n for n in ast.parse(base_helper.read_text()).body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="helper" for t in n.targets))
helper=ast.literal_eval(node.value)
helper=helper.replace("hdPerson","hdShelter").replace("HDPerson","HDShelter").replace("person","shelter").replace("PERSON","SHELTER").replace("人物","木棚").replace("規格063","規格064").replace("使用者確認的人物原圖","第024幀候選原圖")
(out/"shelter_probe_helpers.go").write_text(helper)
module=out/"runtime-r1";assert not module.exists()
subprocess.run(["python3",str(repo/"tools/build_window_prototype.py"),"--repo","/repo","--output",str(module),"--reference",str(args.reference.resolve())],check=True,timeout=45)
for name in ["hd_building024_prototype.go","hd_building024_prototype_test.go"]:
 p=repo/"tools"/name
 if p.is_file():shutil.copyfile(p,module/name)
shutil.copyfile(out/"shelter_probe_helpers.go",module/"shelter_probe_helpers.go")
def edit(path,pairs):
 text=path.read_text()
 for old,new in pairs:
  assert text.count(old)==1,(str(path),old,text.count(old))
  text=text.replace(old,new,1)
 path.write_text(text)
anchor='return fmt.Sprintf("/hd/%d/sea/%d/person/%d", h.revision, h.sea.revision, h.person.revision)'
edit(module/"hd_runtime.go",[
 ("type hdRuntime struct {","type hdRuntime struct {\n shelter *hdShelterPrototype"),
 (anchor,'if h.shelter!=nil {return fmt.Sprintf("/hd/%d/sea/%d/person/%d/shelter/%d",h.revision,h.sea.revision,h.person.revision,h.shelter.revision)}\n'+anchor),
 ("\th.person.beforeInstruction()","\th.person.beforeInstruction()\n h.shelter.beforeInstruction()"),
 ('\tif h.person != nil {\n\t\treceipt["person"] = h.person.paint(out, f)','\tif h.shelter!=nil {receipt["shelter"]=h.shelter.paint(out,f)}\n\tif h.person != nil {\n\t\treceipt["person"] = h.person.paint(out, f)'),
])
edit(module/"adapter.go",[
 ('\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }',
  ' if *hdShelterPrototypeAsset!="" {\n var err error\n if hd==nil {panic("木棚DRAFT需要既有HD組")}\n hd.shelter,err=loadHDShelterPrototype(hd,*root,*hdShelterPrototypeAsset);must(err)\n hdShelterActive=hd.shelter;hd.shelter.trace=*hdShelterProbeRoot!=""\n defer shelterProbeDump(*out)\n }\n\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }'),
 ('\t\tif label == "" {\n\t\t\tif frontendFrameSink != nil {','\t\tif label == "" {\n shelterProbeFrame(output,rec)\n\t\t\tif frontendFrameSink != nil {'),
])
subprocess.run(["gofmt","-w",*[p.name for p in module.glob("*.go")]],cwd=module,check=True,timeout=30)
binary=out/"colonization-window-prototype"
subprocess.run(["go","build","-trimpath","-o",str(binary),"."],cwd=module,check=True,timeout=180)
subprocess.run(["go","vet","."],cwd=module,check=True,timeout=120)
shutil.copytree(args.base_bundle.resolve(),out/"bundle",symlinks=True)
shutil.copyfile(binary,out/"bundle/bin/colonization-window")
metadata={"kind":"DRAFT-building-024-private-assembly","base_bindings":json.loads((module/"observation-sources.json").read_text()),
 "go_sources":{p.name:sha(p) for p in module.glob("*.go")},"binary_sha256":sha(binary),
 "prototype_source_sha256":sha(repo/"tools/hd_building024_prototype.go"),
 "helper_base_sha256":sha(base_helper),"helper_source_sha256":sha(out/"shelter_probe_helpers.go")}
(out/"build-r1.json").write_text(json.dumps(metadata,indent=2)+"\n")
print("PASS_SHELTER_PROTOTYPE_BUILD_AND_VET",sha(binary),flush=True)
