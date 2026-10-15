"""規格066 READY：正式來源加唯讀GUI與九個正常邊界樣本。"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess
import argparse
parser=argparse.ArgumentParser(description='規格066 READY：正式來源的五語游標與邊界GUI')
for name in ['reference','bundle','gui-reference-root','output']:parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args();repo=Path(__file__).resolve().parents[1];out=args.output.resolve();r58=args.gui_reference_root.resolve();proto=args.reference.resolve();formal_bundle=args.bundle.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and not out.exists() and out.parent.stat().st_uid==os.getuid()
binding=json.loads((proto/'observation-sources.json').read_bytes())['source_sha256']
assert len(binding)==30 and all(hashlib.sha256((repo/name).read_bytes()).hexdigest()==digest for name,digest in binding.items())
assert len(list(proto.glob('*.go')))==47 and not list(proto.glob('*cursor_prototype*'))
original_gui=json.loads((r58/'gui-r5/check.json').read_bytes())
assert original_gui['source_sha256']['binary']=='b9d34771cf7cb5433b8e747845fadaacd470527f247bdde793bac678db2db6d9'
assert original_gui['source_sha256']['probe']==hashlib.sha256((r58/'probe-gui-r5.py').read_bytes()).hexdigest()
assert len(json.loads((formal_bundle/'graphics/manifest.json').read_bytes())['assets'])==46
out.mkdir()
module=out/'runtime-gui-r1';assert not module.exists();shutil.copytree(proto,module)
for name in ['adapter.go','terrain079_probe_helpers.go']:shutil.copyfile(r58/'runtime-gui-r5'/name,module/name)
subprocess.run(['gofmt','-w','adapter.go','terrain079_probe_helpers.go'],cwd=module,check=True,timeout=20)
bundle=out/'gui-bundle-r1';shutil.copytree(formal_bundle,bundle,symlinks=True)
subprocess.run(['go','build','-trimpath','-o',str(bundle/'bin/colonization-window'),'.'],cwd=module,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
unchanged={p.name:sha(p)==sha(module/p.name) for p in proto.glob('*.go') if p.name!='adapter.go'};assert all(unchanged.values()) and len(list(module.glob('*.go')))==48
script=(r58/'probe-gui-r5.py').read_text()
CURSOR_GUI_HELPER="CURSOR_CANDIDATE=Path('__CURSOR_ASSET__')\n_cursor_art=None\ndef cursor_mask(hd):\n    c=hd.get('cursor') or {}\n    if not c.get('painted'):return Image.new('1',(1280,800))\n    need(c.get('formal') is True,'游標不是正式來源')\n    raw=base64.b64decode(c['mask'],validate=True)\n    need(len(raw)==8000 and sum(v.bit_count() for v in raw)==c['painted']<=c['source_cells']<=82,'游標遮罩不符')\n    im=Image.new('1',(320,200));im.putdata([bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)])\n    return im.resize((1280,800),Image.Resampling.NEAREST)\ndef cursor_expected(original,hd,mouse,cursor):\n    global _cursor_art\n    if not hd.get('cursor',{}).get('painted'):return original\n    if _cursor_art is None:\n        need(sha(CURSOR_CANDIDATE.read_bytes())=='2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4','候選游標指紋不同')\n        with Image.open(CURSOR_CANDIDATE) as im:_cursor_art=im.convert('RGBA')\n    art=_cursor_art;expected=original.copy()\n    for k,v in enumerate(cursor):\n        if v==255:continue\n        x,y=mouse['x']+k%16,mouse['y']+k//16\n        if not(0<=x<320 and 0<=y<200):continue\n        for dy in range(4):\n            for dx in range(4):\n                sx,sy=k%16*4+dx,k//16*4+dy\n                rgba=art.getpixel((106+(2*sx+1)*615//80,188+(2*sy+1)*859//112));a=rgba[3]\n                premult=[(c*257*a//255)>>8 for c in rgba[:3]];dst=original.getpixel((x*4+dx,y*4+dy))\n                color=tuple((c*257+d*(255-a)*257//255)>>8 for c,d in zip(premult,dst))\n                expected.putpixel((x*4+dx,y*4+dy),color)\n    return expected\n\n"
helper=CURSOR_GUI_HELPER.replace("'__CURSOR_ASSET__'",repr(str(bundle/'graphics/cursor-000.png')))
assert script.count('def terrain079_mask(hd):')==1;script=script.replace('def terrain079_mask(hd):',helper+'def terrain079_mask(hd):',1)
old='ImageChops.logical_or(terrain079_mask(hd),formal_small_mask(hd))))';assert script.count(old)==2
script=script.replace(old,old.replace('formal_small_mask(hd)','ImageChops.logical_or(formal_small_mask(hd),cursor_mask(hd))'))
lines=script.splitlines();english=final=0
for i,line in enumerate(lines):
 if line.strip().startswith('if graphics == "original" or not ('):
  assert line.endswith('):');lines[i]=line[:-2]+' or hd.get("cursor",{}).get("painted")):';english+=1
 if line.strip().startswith('if c["graphics"] != "hd" or not ('):
  assert line.endswith('):');lines[i]=line[:-2]+' or c["native_live"].get("hd",{}).get("cursor",{}).get("painted")):';final+=1
assert english==final==1;script='\n'.join(lines)+'\n'
old='        cursor_points = 0';assert script.count(old)==1
old='            for k, value in enumerate(cursor):';assert script.count(old)==1
script=script.replace(old,'            expected=cursor_expected(original,c["native_live"].get("hd",{}),c["dos_mouse"],cursor)\n'+old,1)
old='need(actual.crop(rect).tobytes() == original.crop(rect).tobytes(), "HD或文字蓋住不透明游標")';assert script.count(old)==1
script=script.replace(old,'need(actual.crop(rect).tobytes() == expected.crop(rect).tobytes(), "游標原alpha合成不符")',1)
old='    command += ["--hd-terrain079-probe-root",str(terrain_root)]';assert script.count(old)==1
script=script.replace(old,old+'\n    command += ["--hd-cursor-prototype-asset",str(CURSOR_CANDIDATE)]',1)
script=script.replace('PASS_TERRAIN079_FORMAL_FOCUSED_FIVE_LANGUAGE_GUI','PASS_DRAFT_CURSOR_FIVE_LANGUAGE_GUI').replace('"formal_entry"','"prototype_entry"').replace('"diagnostics_only": True','"prototype_only": True')
old='正式45種素材與079正式loader的92組五語GUI，19張HD快照及1張原版模式快照；獨立原版與四側重播另驗，全量HD未完成。';assert old in script
script=script.replace(old,'45種正式素材加DRAFT游標原型的92組GUI；游標依原alpha疊既有原版輪廓。原型不進正式路徑，四側重播、邊界及全量HD另驗。')
script=script.replace('def terrain_snapshot(label,locale="zh-Hant"):', 'def terrain_snapshot(label,locale="zh-Hant",require_hd=None):')
old='"require_hd":bool(locale),"ordinal":79';assert script.count(old)==1
script=script.replace(old,'"require_hd":bool(locale) if require_hd is None else require_hd,"ordinal":79',1)
old='            switch_round("terrain079-start")\n';assert script.count(old)==1
edge='''            cursor_edges=[]
            for label,xy in [('nw',(0,0)),('ne',(319,0)),('sw',(0,199)),('se',(319,199)),('north',(160,0)),('east',(319,100)),('south',(160,199)),('west',(0,100)),('recovered',(144,56))]:
                before=status()['step'];x,y=xy;move(x*4,y*4+48)
                wait(lambda state:state.get('step',0)>=before+1000000 and state.get('dos_mouse',{}).get('x')==x and state.get('dos_mouse',{}).get('y')==y,'游標邊界正常移動未完成')
                proof=terrain_snapshot('cursor-edge-'+label,require_hd=(label=='recovered'))
                current=proof['frame']['native_live'];hd=current.get('hd') or {}
                cursor_edges.append({'label':label,'mouse':[x,y],'step':proof['state']['step'],'cursor':hd.get('cursor'),'hd_reason':hd.get('reason'),'cursor_reject':hd.get('cursor_reject')})
'''
script=script.replace(old,old+edge,1)
old='        result["presentation_waits"]=presentation_waits';assert script.count(old)==1
script=script.replace(old,'        need(len(cursor_edges)==9,"游標邊界樣本不完整")\n        result["cursor_edges"]=cursor_edges\n'+old,1)

old='    command += ["--hd-cursor-prototype-asset",str(CURSOR_CANDIDATE)]';assert script.count(old)==1
script=script.replace(old,'',1).replace('PASS_DRAFT_CURSOR_FIVE_LANGUAGE_GUI','PASS_CURSOR_FORMAL_FIVE_LANGUAGE_GUI')
script=script.replace('"prototype_entry"','"formal_entry"').replace('"prototype_only": True','"diagnostics_only": True')
script=script.replace('result["formal_assets"]=45','result["formal_assets"]=46')
script=script.replace('45種正式素材加DRAFT游標原型的92組GUI；游標依原alpha疊既有原版輪廓。原型不進正式路徑，四側重播、邊界及全量HD另驗。','46種正式素材的92組五語GUI與九個正常邊界／恢復；完整原版重播及全量HD另驗。')
assert 'hd-cursor-prototype-asset' not in script

compile(script,'formal_cursor_GUI','exec');(out/'probe-gui-r1.py').write_text(script)
shell=(r58/'run-gui-r5.sh').read_text().replace('/out/probe-gui-r5.py','/out/probe-gui-r1.py').replace('/out/gui-bundle-r5','/out/gui-bundle-r1').replace('/out/gui-r5','/out/gui-r1').replace('terrain079-formal-gui-xvfb-r5','cursor-prototype-gui-xvfb-r1')
shell=shell.replace('/out/probe-gui-r1.py',str(out/'probe-gui-r1.py')).replace('/out/gui-bundle-r1',str(out/'gui-bundle-r1')).replace('/out/gui-r1',str(out/'gui-r1')).replace('/out/cursor-prototype-gui-xvfb-r1.log',str(out/'cursor-prototype-gui-xvfb-r1.log'))
(out/'run-gui-r1.sh').write_text(shell)
report={'result':'PASS_CURSOR_FORMAL_READ_ONLY_GUI_BUILD','formal_binary_sha256':sha(formal_bundle/'bin/colonization-window'),'gui_binary_sha256':sha(bundle/'bin/colonization-window'),'unchanged_formal_sources_except_adapter':unchanged,'source_gui_python_sha256':sha(r58/'probe-gui-r5.py'),'source_adapter_sha256':sha(r58/'runtime-gui-r5/adapter.go'),'source_snapshot_helper_sha256':sha(r58/'runtime-gui-r5/terrain079_probe_helpers.go'),'generated_gui_python_sha256':sha(out/'probe-gui-r1.py'),'production_sources':True}
(out/'gui-build-r1.json').write_text(json.dumps(report,indent=2)+'\n');print(report['result'],flush=True)
