"""正式43個來源加一個唯讀快照工具，素材仍由正式loader載入。"""
from pathlib import Path
import argparse,ast,hashlib,json,os,shutil,subprocess
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo',type=Path,default=Path('/repo'))
for name in ['reference','bundle','output']:parser.add_argument('--'+name,type=Path,required=True)
a=parser.parse_args();repo,out=a.repo.resolve(),a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and not out.exists() and out.parent.stat().st_uid==os.getuid()
reference,formal_bundle=a.reference.resolve(),a.bundle.resolve()
assert reference.is_dir() and formal_bundle.is_dir() and len(list(reference.glob('*.go')))==43
binding=json.loads((reference/'observation-sources.json').read_bytes())['source_sha256']
assert len(binding)==26 and all(hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest for name,digest in binding.items())
tree=ast.parse((repo/'tools/prepare_hd_small_image_prototype.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FILES' for t in n.targets))
files=ast.literal_eval(node.value);out.mkdir()
module=out/'runtime-gui-r1';assert not module.exists();shutil.copytree(reference,module)
s=files['small_probe_helpers.go'].replace('hdSmallPrototype','hdSmallRuntime').replace('"prototype":true','"formal":true').replace('"prototype": true','"formal": true').replace('DRAFT診斷輸出目錄','正式來源的唯讀診斷輸出目錄')
s='\n'.join(l for l in s.splitlines() if not l.startswith('var hdSmallRuntimeAssets='))+'\n'
assert 'hd-small-prototype-assets' not in s
(module/'small_probe_helpers.go').write_text(s)
p=module/'adapter.go';s=p.read_text()
old='\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }'
assert s.count(old)==1;s=s.replace(old,''' if *hdSmallProbeRoot!="" {
  if hd==nil || hd.small==nil {panic("正式小圖像診斷需要已載入HD")}
  hdSmallActive=hd.small;hd.small.trace=true;defer smallProbeDump(*out)
 }
'''+old,1)
old='\t\tif label == "" {\n\t\t\tif frontendFrameSink != nil {';assert s.count(old)==1;s=s.replace(old,'\t\tif label == "" {\n smallProbeFrame(output,rec)\n\t\t\tif frontendFrameSink != nil {',1);p.write_text(s)
subprocess.run(['gofmt','-w','adapter.go','small_probe_helpers.go'],cwd=module,check=True,timeout=20)
bundle=out/'gui-bundle-r1';shutil.copytree(formal_bundle,bundle,symlinks=True)
subprocess.run(['go','build','-trimpath','-o',str(bundle/'bin/colonization-window'),'.'],cwd=module,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
s=files['probe-gui-r1.py']
s=s.replace('"--hd-small-prototype-assets",str(args.small_assets),','')
s=s.replace('terrain.get("prototype") is True','terrain.get("formal") is True')
s=s.replace('icons-%03d-candidate-v1.png','icons-%03d.png')
s=s.replace('PASS_SMALL_RAM_FOCUSED_FIVE_LANGUAGE_GUI','PASS_SMALL_FORMAL_FOCUSED_FIVE_LANGUAGE_GUI')
s=s.replace('"prototype_entry"','"formal_entry"').replace('"prototype_flags": True','"diagnostics_only": True')
s=s.replace('正式十四種素材保持；小圖像022、024隔離原型的102組必要GUI，19張HD快照及1張原版模式快照。獨立原版與四側重播另驗，不授予完整HD或正式接線信用。','正式十六種素材的102組五語GUI；022、024沿正式loader，不使用原型素材旗標。19張HD快照及1張原版模式快照；獨立原版與四側重播另驗，完整HD未完成。')
(out/'probe-gui-r1.py').write_text(s)
s=files['run-gui-r1.sh'].replace('/out/bundle','/out/gui-bundle-r1').replace('--small-assets /out/assets','--small-assets /out/gui-bundle-r1/graphics')
(out/'run-gui-r1.sh').write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'kind':'formal-small-read-only-GUI-probe','formal_binary_sha256':sha(formal_bundle/'bin/colonization-window'),'probe_binary_sha256':sha(bundle/'bin/colonization-window'),'base_go_sources_unchanged':{p.name:sha(p)==sha(module/p.name) for p in reference.glob('*.go') if p.name!='adapter.go'},'only_changed_go':['adapter.go','small_probe_helpers.go'],'production_assets':True,'prototype_asset_flags':False}
assert all(report['base_go_sources_unchanged'].values()) and len(list(module.glob('*.go')))==44
(out/'gui-build-r1.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS_SMALL_FORMAL_READ_ONLY_GUI_BUILD',report['probe_binary_sha256'],flush=True)
