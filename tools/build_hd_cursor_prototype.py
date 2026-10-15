"""規格066 DRAFT：複製已驗45份正式Go來源，僅在隔離副本加入游標原型。"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess

p=argparse.ArgumentParser(description=__doc__)
for name in ['reference','bundle','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and not out.exists() and out.parent.stat().st_uid==os.getuid()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
binding=json.loads((a.reference/'observation-sources.json').read_bytes())['source_sha256']
assert len(binding)==28 and len(list(a.reference.glob('*.go')))==45 and all(sha(repo/n)==h for n,h in binding.items())
out.mkdir();module=out/'runtime-r1';shutil.copytree(a.reference,module)
for name in ['hd_cursor_prototype.go','hd_cursor_prototype_test.go']:shutil.copyfile(repo/'tools'/name,module/name)
path=module/'hd_runtime.go';s=path.read_text()
changes=[('type hdRuntime struct {','type hdRuntime struct {\n cursorPrototype *hdCursorPrototype'),
 ('\treturn h, nil','\tif *hdCursorPrototypeAsset!="" {h.cursorPrototype,err=loadHDCursorPrototype(game,*hdCursorPrototypeAsset);if err!=nil{return nil,err}}\n\treturn h, nil'),
 ('\tb.hd.restoreCursor(out, f)','\tb.hd.restoreCursor(out, f)\n if b.hd.cursorPrototype!=nil {hd["cursor"]=b.hd.cursorPrototype.paint(b.hd,out,f)}')]
for old,new in changes:assert s.count(old)==1;(s:=s.replace(old,new,1))
path.write_text(s)
subprocess.run(['gofmt','-w','hd_runtime.go','hd_cursor_prototype.go','hd_cursor_prototype_test.go'],cwd=module,check=True,timeout=20)
bundle=out/'bundle-r1';shutil.copytree(a.bundle,bundle,symlinks=True)
subprocess.run(['go','build','-trimpath','-o',str(bundle/'bin/colonization-window'),'.'],cwd=module,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
unchanged={p.name:sha(p)==sha(module/p.name) for p in a.reference.glob('*.go') if p.name!='hd_runtime.go'}
assert all(unchanged.values()) and len(list(module.glob('*.go')))==47
report={'kind':'DRAFT-standard-cursor-prototype','formal_assets_unchanged':45,'formal_binary_sha256':sha(a.bundle/'bin/colonization-window'),'prototype_binary_sha256':sha(bundle/'bin/colonization-window'),'formal_sources_unchanged_except_hd_runtime':unchanged,'prototype_sources_sha256':{n:sha(module/n) for n in ['hd_runtime.go','hd_cursor_prototype.go','hd_cursor_prototype_test.go']},'changes':['private hdRuntime field and optional loader','candidate alpha after original cursor restoration'],'production_connected':False}
(out/'build-r1.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS_DRAFT_CURSOR_PROTOTYPE_BUILD',flush=True)
