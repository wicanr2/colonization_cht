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
active=sorted(int(name[6:9]) for name in json.loads((formal_bundle/'graphics/manifest.json').read_bytes())['assets'] if name.startswith('icons-'))
assert active==[5, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 42, 53, 56, 59, 62, 67, 68, 69, 94, 122, 123, 124]
city_active=[n for n in active if n not in {38,53}]
city_targets=[('005', (139, 154)), ('022', (8, 185)), ('023', (29, 187)), ('024', (45, 185)), ('025', (63, 186)), ('026', (83, 185)), ('027', (101, 188)), ('028', (120, 187)), ('029', (139, 188)), ('030', (157, 185)), ('031', (179, 186)), ('032', (200, 185)), ('033', (216, 186)), ('034', (235, 185)), ('035', (254, 187)), ('036', (273, 187)), ('037', (294, 185)), ('042', (132, 171)), ('056', (57, 169)), ('059', (23, 150)), ('062', (70, 169)), ('067', (311, 139)), ('068', (310, 153)), ('069', (310, 168)), ('094', (6, 150)), ('122', (156, 171)), ('123', (8, 137)), ('124', (110, 137))]
s=s.replace('for n in [22,24]),"小圖像來源沒有完整HD合成"','for n in '+repr(city_active)+'),"小圖像來源沒有完整HD合成"')
s=s.replace('[22,24]',repr(active))
s=s.replace('[("022",(4,186)),("024",(47,186)),("022-again",(4,186))]',repr(city_targets))
s=s.replace('terrain_snapshot(label,locale="zh-Hant"):','terrain_snapshot(label,locale="zh-Hant",ordinal=22):').replace('"ordinal":22,"locale":locale','"ordinal":ordinal,"locale":locale')
s=s.replace('terrain_snapshot("small-%s-%s"%(action,part))','terrain_snapshot("small-%s-%s"%(action,part),ordinal=int(part))')
s=s.replace('scene in terrain_scenes else','scene in terrain_scenes or scene in {"world","saved-world","hd-exited-again"} else')
old='need(terrain.get("painted",0)==0,"離開世界後殘留小圖像來源")'
assert s.count(old)==1
s=s.replace(old,'need(all(source.get("painted",0)==0 for n,source in terrain.get("sources",{}).items() if int(n) not in {5,36,38,42,53}),"非城內殘留城內專用來源")\n                    if scene=="main-menu":need(terrain.get("painted",0)==0,"主選單殘留小圖像")\n                    if scene in {"world","saved-world","hd-exited-again"} and not fallback:need(all(terrain.get("sources",{}).get(str(n),{}).get("painted",0)>0 for n in [5,36,38,42,53]),"世界小圖像未恢復")')
old='            switch_round("world")\n'
assert s.count(old)==1
s=s.replace(old,old+'''            for ordinal,xy in [(5, (153, 112)), (36, (282, 158)), (38, (274, 157)), (42, (266, 123)), (53, (293, 159))]:
                for action,target in [("hover",xy),("away",(112,160)),("return",xy)]:
                    before=status()["step"];x,y=target;move(x*4,y*4+48)
                    wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"世界小圖像游標未到達")
                    terrain_snapshot("small-world-%s-%03d"%(action,ordinal),ordinal=ordinal)
''')
old='            switch_round("saved-world")\n';assert s.count(old)==1
s=s.replace(old,old+'            terrain_snapshot("small-world-saved",ordinal=36)\n')
s=s.replace('"--hd-small-prototype-assets",str(args.small_assets),','')
s=s.replace('terrain.get("prototype") is True','terrain.get("formal") is True')
s=s.replace('icons-%03d-candidate-v1.png','icons-%03d.png')
s=s.replace('PASS_SMALL_RAM_FOCUSED_FIVE_LANGUAGE_GUI','PASS_SMALL_FORMAL_FOCUSED_FIVE_LANGUAGE_GUI')
s=s.replace('"prototype_entry"','"formal_entry"').replace('"prototype_flags": True','"diagnostics_only": True')
s=s.replace('正式十四種素材保持；小圖像022、024隔離原型的102組必要GUI，19張HD快照及1張原版模式快照。獨立原版與四側重播另驗，不授予完整HD或正式接線信用。','正式四十四種素材的102組五語GUI；三十張小圖像沿正式loader。110張HD快照及1張原版模式快照；獨立原版與四側重播另驗，完整HD未完成。')
(out/'probe-gui-r1.py').write_text(s)
s=files['run-gui-r1.sh'].replace('/out/bundle','/out/gui-bundle-r1').replace('--small-assets /out/assets','--small-assets /out/gui-bundle-r1/graphics')
(out/'run-gui-r1.sh').write_text(s)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
report={'kind':'formal-small-read-only-GUI-probe','formal_binary_sha256':sha(formal_bundle/'bin/colonization-window'),'probe_binary_sha256':sha(bundle/'bin/colonization-window'),'base_go_sources_unchanged':{p.name:sha(p)==sha(module/p.name) for p in reference.glob('*.go') if p.name!='adapter.go'},'only_changed_go':['adapter.go','small_probe_helpers.go'],'production_assets':True,'prototype_asset_flags':False}
assert all(report['base_go_sources_unchanged'].values()) and len(list(module.glob('*.go')))==44
(out/'gui-build-r1.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS_SMALL_FORMAL_READ_ONLY_GUI_BUILD',report['probe_binary_sha256'],flush=True)
