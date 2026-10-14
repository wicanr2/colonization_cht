"""規格064 R44 DRAFT：中央第009幀隔離顯示，正式十三素材保持。"""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
for name in ['output','reference','base-bundle']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0
assert out.is_relative_to('/out') and out.is_dir() and out.stat().st_uid==os.getuid()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# R42已驗快照工具只存在本機原型副本，不加入正式組裝。
reference_helper=repo/'workplace/reports/goal186-display-hd/hd-building-nine-r42/public-r3/runtime-r1/nine_probe_helpers.go'
helper=reference_helper.read_text().replace('nine','center').replace('Nine','Center').replace('NINE','CENTER').replace('九來源','中央來源')
(out/'center_probe_helpers.go').write_text(helper)
module=out/'runtime-r1';assert not module.exists()
subprocess.run(['python3',str(repo/'tools/build_window_prototype.py'),'--repo',str(repo),'--output',str(module),'--reference',str(a.reference.resolve())],check=True,timeout=60)
for name in ['hd_building009_prototype.go','hd_building009_prototype_test.go']:shutil.copyfile(repo/'tools'/name,module/name)
shutil.copyfile(out/'center_probe_helpers.go',module/'center_probe_helpers.go')
def edit(name,pairs):
    path=module/name;s=path.read_text()
    for old,new in pairs:
        assert s.count(old)==1,(name,old,s.count(old));s=s.replace(old,new,1)
    path.write_text(s)
anchor='return fmt.Sprintf("/hd/%d/sea/%d/person/%d/shelter/%d/nine/%d", h.revision, h.sea.revision, h.person.revision, h.shelter.revision, h.nine.revision)'
edit('hd_runtime.go',[
    ('type hdRuntime struct {','type hdRuntime struct {\n center *hdCenterPrototype'),
    (anchor,'if h.center!=nil { return fmt.Sprintf("/hd/%d/sea/%d/person/%d/shelter/%d/nine/%d/center/%d",h.revision,h.sea.revision,h.person.revision,h.shelter.revision,h.nine.revision,h.center.revision) }\n'+anchor),
    ('\th.nine.beforeInstruction()','\th.nine.beforeInstruction()\n h.center.beforeInstruction()'),
    ('\tif h.person != nil {\n\t\treceipt["person"] = h.person.paint(out, f)','\tif h.center!=nil { receipt["center"]=h.center.paint(out,f) }\n\tif h.person != nil {\n\t\treceipt["person"] = h.person.paint(out, f)'),
])
edit('adapter.go',[
    ('\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }',''' if *hdCenterPrototypeAssets!="" {
 var err error
 if hd==nil{panic("中央DRAFT需要既有HD組")}
 hd.center,err=loadHDCenterPrototype(hd,*root,*hdCenterPrototypeAssets);must(err)
 hdCenterActive=hd.center;hd.center.trace=*hdCenterProbeRoot!=""
 defer centerProbeDump(*out)
 }
\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }'''),
    ('\t\tif label == "" {\n\t\t\tif frontendFrameSink != nil {','\t\tif label == "" {\n centerProbeFrame(output,rec)\n\t\t\tif frontendFrameSink != nil {'),
])
subprocess.run(['gofmt','-w',*[p.name for p in module.glob('*.go')]],cwd=module,check=True,timeout=30)
binary=out/'colonization-window-prototype'
subprocess.run(['go','build','-trimpath','-o',str(binary),'.'],cwd=module,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
shutil.copytree(a.base_bundle,out/'bundle',symlinks=True);shutil.copyfile(binary,out/'bundle/bin/colonization-window')
meta=dict(kind='DRAFT-center-009-private-assembly',binary_sha256=sha(binary),prototype_source_sha256=sha(repo/'tools/hd_building009_prototype.go'),helper_reference_sha256=sha(reference_helper),go_sources={p.name:sha(p) for p in module.glob('*.go')},base_bindings=json.loads((module/'observation-sources.json').read_text()))
(out/'build.json').write_text(json.dumps(meta,indent=2)+'\n');print('PASS_CENTER_PROTOTYPE_BUILD_AND_VET',sha(binary),flush=True)
