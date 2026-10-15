"""規格062 R58：45個正式Go來源加一個唯讀079快照工具，素材沿正式loader。"""
from pathlib import Path
import argparse,ast,hashlib,json,os,shutil,subprocess
GUI_BASE_SHA='76d10c37c6eaef74f455f61166e145d232d38ac6a7127250e82dbbc1d892f43c'
GUI_PATCH=[(1, 2, ['"""規格060 DRAFT：以真實X11輸入驗隔離視窗五語，不修改原版狀態。"""\n']), (101, 103, ['def terrain079_mask(hd):\n', '    terrain=hd.get("terrain079") or {}\n']), (104, 105, ['    need(terrain.get("formal") is True,"地形不是隔離原型")\n']), (106, 107, ['    need(len(raw)==8000,"地形遮罩長度不同")\n']), (108, 109, ['    need(sum(bits)==terrain["painted"]<=terrain["owned"],"地形遮罩不同")\n']), (127, 128, ['    parser.add_argument("--terrain079-assets",type=Path,required=True)\n']), (207, 209, ['    terrain_root=output/"terrain079";terrain_root.mkdir()\n', '    command += ["--hd-terrain079-probe-root",str(terrain_root)]\n']), (317, 318, ['                need(not any(hd.get(k,{}).get("painted",0) for k in ["sea","person","shelter","nine","center","terrain079"]) and not hd.get("painted",0),"未知游標仍繪HD")\n']), (354, 355, ['        terrain_scenes={"terrain079-start","terrain079-return","terrain079-saved-return"}\n']), (356, 360, ['            before=status()["step"];marker=terrain_root/"terrain079-request.json"\n', '            need(not marker.exists(),"地形快照尚未完成")\n', '            marker.write_text(json.dumps({"label":label,"buttons":0,"min_step":before+200000,"require_hd":bool(locale),"ordinal":79,"locale":locale}))\n', '            wait(lambda state:(terrain_root/label/"check.json").is_file() and not marker.exists(),"地形快照未完整保存："+label)\n']), (367, 369, ['                    before=status()["step"];move(144*4,56*4+48)\n', '                    wait(lambda state:state.get("step",0)>=before+2000000,"地形正常懸停未完成")\n']), (445, 446, ['                terrain=hd.get("terrain079") or {}\n']), (447, 450, ['                    need(terrain.get("formal") is True and terrain.get("painted",0)==1129,"地形來源沒有完整HD合成")\n', '                if graphics=="hd" and scene in {"main-menu","colony","center-start","center-return","hd-reentered-colony","hd-building-hover","hd-encyclopedia-closed","hd-building-encyclopedia"}:\n', '                    need(terrain.get("painted",0)==0,"離開世界後殘留地形來源")\n']), (487, 488, ['                    if graphics == "original" or not (hd.get("painted") or hd.get("sea",{}).get("painted") or hd.get("person",{}).get("painted") or hd.get("shelter",{}).get("painted") or hd.get("nine",{}).get("painted") or center_record(hd).get("painted") or hd.get("terrain079",{}).get("painted")):\n']), (492, 493, ['                        safe=ImageChops.logical_or(safe,ImageChops.logical_or(ImageChops.logical_or(ImageChops.logical_or(ImageChops.logical_or(ImageChops.logical_or(sea_mask(hd),person_mask(hd)),shelter_mask(hd)),nine_mask(hd)),center_mask(hd)),terrain079_mask(hd)))\n']), (499, 500, ['                    if scene in {"world", "saved-world", "hd-exited-again", "sea-hover-near", "sea-hover-far", "sea-cursor-returned"} or scene in terrain_scenes:\n']), (542, 543, ['                    if graphics=="hd":safe=ImageChops.logical_or(safe,ImageChops.logical_or(ImageChops.logical_or(ImageChops.logical_or(ImageChops.logical_or(ImageChops.logical_or(sea_mask(hd),person_mask(hd)),shelter_mask(hd)),nine_mask(hd)),center_mask(hd)),terrain079_mask(hd)))\n']), (549, 551, ['                if graphics=="hd" and scene in {"terrain079-return","terrain079-saved-return"}:\n', '                    label=("terrain079-saved-proof-" if scene=="terrain079-saved-return" else "terrain079-proof-")+locale.lower();proof=terrain_snapshot(label,locale)\n']), (552, 553, ['                    need(recovered["locale"]==locale and recovered["hd"]["terrain079"]["painted"]>0,"地形關閉設定後未恢復")\n']), (607, 614, ['            switch_round("terrain079-start")\n', '            # R47 原版 point-004 確認的三個完整256像素來源區塊。\n', '            for part,xy in [("north",(144,56)),("west",(112,88)),("south",(128,104))]:\n']), (616, 621, ['                    wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"地形游標位置未到達")\n', '                    terrain_snapshot("terrain079-%s-%s"%(action,part))\n', '            switch_round("terrain079-return")\n']), (649, 655, ['        switch_round("terrain079-saved-return")\n']), (663, 669, ['        terrain_snapshot("terrain079-quit-original",locale="")\n', '        need({c["locale"] for c in terrain_recoveries}==set(LOCALES),"地形五語恢復不完整")\n', '        need(len(checks)==82,"地形必要GUI範圍不同")\n', '        need(len(terrain_recoveries)==10,"地形正常恢復數不同")\n', '        for scene in ["terrain079-return","terrain079-saved-return"]:\n', '            need({r["locale"] for r in terrain_recoveries if r["scene"]==scene}==set(LOCALES),"地形存檔前後五語恢復不完整")\n']), (677, 678, ['        result = {"result": "PASS_TERRAIN079_FORMAL_FOCUSED_FIVE_LANGUAGE_GUI", "checks": checks, "final_live": final_live,\n']), (679, 680, ['                                    "seed": sha(seed), "normal_path": sha(inputs), "probe": sha(Path(__file__).read_bytes()), "hd_asset": sha(args.hd_asset.read_bytes()),"sea_asset":sha(args.sea_asset.read_bytes()),"person_asset":sha(args.person_asset.read_bytes()),"shelter_asset":sha(args.shelter_asset.read_bytes()),"center_asset":sha((args.center_assets/"building-009.png").read_bytes()),"terrain079_asset":sha((args.terrain079_assets/"terrain-079.png").read_bytes()),"nine_assets":{"building-%03d.png"%n:sha((args.nine_assets/("building-%03d.png"%n)).read_bytes()) for n in [16,21,27,35,39,42,43,44,45]}},\n']), (684, 684, ['        result["graphics_manifest_sha256"]=sha((args.formal_launcher.parent/"graphics/manifest.json").read_bytes())\n', '        result["formal_assets"]=45\n']), (686, 687, ['            result["terrain079_normal_recoveries"] = terrain_recoveries\n']), (689, 692, ['            result["formal_entry"] = {"launcher_sha256": sha(args.formal_launcher.read_bytes()),\n', '                                     "command": command, "diagnostics_only": True}\n', '            result["limitations"] = ["正式45種素材與079正式loader的82組五語GUI，19張HD快照及1張原版模式快照；獨立原版與四側重播另驗，全量HD未完成。"]\n']), (699, 700, ['            if c["graphics"] != "hd" or not (c["native_live"].get("hd", {}).get("painted") or c["native_live"].get("hd", {}).get("sea",{}).get("painted") or c["native_live"].get("hd", {}).get("person",{}).get("painted") or c["native_live"].get("hd", {}).get("shelter",{}).get("painted") or c["native_live"].get("hd", {}).get("nine",{}).get("painted") or center_record(c["native_live"].get("hd", {})).get("painted") or c["native_live"].get("hd",{}).get("terrain079",{}).get("painted")):\n'])]
HELPER='package main\n\nimport (\n\t"encoding/json"\n\t"flag"\n\t"fmt"\n\tgolem "github.com/wicanr2/dosgolem"\n\t"image"\n\t"image/png"\n\t"os"\n\t"path/filepath"\n\t"regexp"\n)\n\nvar hdTerrain079ProbeRoot = flag.String("hd-terrain079-probe-root", "", "正式079來源的唯讀診斷輸出目錄")\nvar hdTerrain079Active *hdTerrain079Runtime\n\nfunc terrain079ProbeDump(prefix string) {\n\tp := hdTerrain079Active\n\tif p == nil || !p.trace {\n\t\treturn\n\t}\n\tdumpJSON(prefix+".terrain079.json", map[string]any{"formal": true, "calls": p.calls, "cursor_pairs": p.pairs, "accepted": p.accepted, "rejected": p.rejected})\n}\nfunc terrain079ProbeFrame(im *image.RGBA, record map[string]any) {\n\tp := hdTerrain079Active\n\tif p == nil || *hdTerrain079ProbeRoot == "" || activeWindow == nil || im == nil {\n\t\treturn\n\t}\n\tmarker := filepath.Join(*hdTerrain079ProbeRoot, "terrain079-request.json")\n\tinfo, err := os.Lstat(marker)\n\tif os.IsNotExist(err) {\n\t\treturn\n\t}\n\tmust(err)\n\tif !info.Mode().IsRegular() || info.Mode()&os.ModeSymlink != 0 || info.Size() > 1024 {\n\t\tpanic("地形來源診斷請求不是有界檔案")\n\t}\n\tvar req struct {\n\t\tLabel     string `json:"label"`\n\t\tMinStep   uint64 `json:"min_step"`\n\t\tButtons   uint16 `json:"buttons"`\n\t\tOrdinal   int    `json:"ordinal"`\n\t\tLocale    string `json:"locale"`\n\t\tRequireHD bool   `json:"require_hd"`\n\t}\n\tmust(json.Unmarshal(read(marker), &req))\n\tif !regexp.MustCompile("^[a-z0-9-]{1,64}$").MatchString(req.Label) {\n\t\tpanic("地形來源診斷標籤不同")\n\t}\n\tm, d := p.h.m, activeWindow.d\n\tif m.Steps < req.MinStep || d.Mouse.Buttons != req.Buttons {\n\t\treturn\n\t}\n\tif req.RequireHD {\n\t\tlive, _ := record["native_live"].(map[string]any)\n\t\thd, _ := live["hd"].(map[string]any)\n\t\tterrain079, _ := hd["terrain079"].(map[string]any)\n\t\tpainted,_:=terrain079["painted"].(int)\n\t\tif live["locale"] != req.Locale || hd["reason"] != "known-building" || painted <= 0 {\n\t\t\treturn\n\t\t}\n\t}\n\tdestination := filepath.Join(*hdTerrain079ProbeRoot, req.Label)\n\tmust(os.Mkdir(destination, 0755))\n\tstate := map[string]any{"step": m.Steps, "cycles": m.CPU.Cycles, "memory_sha256": hash(m.Mem), "indexed_sha256": hash(m.Indexed()), "palette_sha256": hash(m.DAC[:]),\n\t\t"registers": m.CPU.R, "segments": m.CPU.Seg, "ip": m.CPU.IP, "flags": m.CPU.Flags, "dos_input_count": len(activeWindow.inputs),\n\t\t"dos_mouse": map[string]any{"x": d.Mouse.X, "y": d.Mouse.Y, "buttons": d.Mouse.Buttons}}\n\tf := draftNativeFrame{canvas: m.Mem[hdBuildingCanvas : hdBuildingCanvas+64000], indexed: m.Indexed(), palette: m.DAC[:], cursor: image.Rect(int(d.Mouse.X), int(d.Mouse.Y), int(d.Mouse.X)+16, int(d.Mouse.Y)+16), step: m.Steps, mode: m.VideoMode()}\n\tcells := map[int]map[string]any{}\n\tfor i, c := range p.visible {\n\t\tif c.owned {\n\t\t\tcells[i] = map[string]any{"ordinal": 79, "local": int(c.k), "native": c.native}\n\t\t}\n\t}\n\tfor n, data := range map[string][]byte{"memory": m.Mem, "indexed": m.Indexed(), "canvas": f.canvas, "palette": m.DAC[:], "cursor-background": m.Mem[0xafa00:0xafb00], "cursor-final": m.Mem[0xafb00:0xafc00], "cursor-source": m.Mem[0x1cd74:0x1ce74]} {\n\t\tmust(os.WriteFile(filepath.Join(destination, n), data, 0644))\n\t}\n\tfile, err := os.Create(filepath.Join(destination, "display.png"))\n\tmust(err)\n\tmust(png.Encode(file, im))\n\tmust(file.Close())\n\tdumpJSON(filepath.Join(destination, "check.json"), map[string]any{"formal": true, "state": state, "frame": record, "terrain079": p.receipt(f), "cells": cells, "cursor_source_sha256": hash(m.Mem[0x1cd74:0x1ce74]), "call_count": len(p.calls), "cursor_pair_count": len(p.pairs)})\n\tmust(os.Remove(marker))\n\tfmt.Println("TERRAIN079_SNAPSHOT", req.Label, m.Steps, len(activeWindow.inputs))\n}\n\nvar _ *golem.Machine\n'
RUN='set -euo pipefail\nXvfb :89 -screen 0 1440x1000x24 -nolisten tcp >/out/terrain079-formal-gui-xvfb-r1.log 2>&1 &\nxpid=$!\ntrap \'kill "$xpid" 2>/dev/null || true; wait "$xpid" 2>/dev/null || true\' EXIT\nexport DISPLAY=:89\npython3 /out/probe-gui-r1.py --binary /out/gui-bundle-r1/bin/colonization-window --formal-launcher /out/gui-bundle-r1/colonization-cht.sh --launcher /repo/workplace/reports/goal186-display-hd/language-resources-20261011/map-source-padding-r27/formal-legacy-probe-launcher.sh --game /game --seed /repo/workplace/reports/goal186-display-hd/language-resources-20261011/formal-save-gui-r25/save/COLONY09.SAV --inputs /repo/workplace/reports/goal185-player-experience/issue56-wagon-sample-gui/gui.inputs.json --ui-font /out/gui-bundle-r1/ui/NotoSansCJK-Regular.ttc --ui-catalog /out/gui-bundle-r1/text/frontend-ui.tsv --bundles /out/gui-bundle-r1/languages --hd-asset /out/gui-bundle-r1/graphics/building-032.png --sea-asset /out/gui-bundle-r1/graphics/sea-148.png --person-asset /out/gui-bundle-r1/graphics/person-100.png --shelter-asset /out/gui-bundle-r1/graphics/building-024.png --nine-assets /out/gui-bundle-r1/graphics --center-assets /out/gui-bundle-r1/graphics --terrain079-assets /out/gui-bundle-r1/graphics --output /out/gui-r1 --input-edit --save-cycle > /out/gui-r1.log 2>&1\n'
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--repo',type=Path,default=Path('/repo'))
for name in ['reference','bundle','output']:p.add_argument('--'+name,type=Path,required=True)
a=p.parse_args();repo,out=a.repo.resolve(),a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and not out.exists() and out.parent.stat().st_uid==os.getuid()
reference,bundle=a.reference.resolve(),a.bundle.resolve()
assert reference.is_dir() and bundle.is_dir() and len(list(reference.glob('*.go')))==45
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bindings=json.loads((reference/'observation-sources.json').read_bytes())['source_sha256']
assert len(bindings)==28 and all(sha(repo/name)==digest for name,digest in bindings.items())
tree=ast.parse((repo/'tools/prepare_hd_small_image_prototype.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='FILES' for t in n.targets))
files=ast.literal_eval(node.value);base=files['probe-gui-r1.py']
assert hashlib.sha256(base.encode()).hexdigest()==GUI_BASE_SHA
lines=base.splitlines(keepends=True)
for start,end,new in reversed(GUI_PATCH):lines[start:end]=new
gui=''.join(lines);compile(gui,'formal_world_gui','exec')
assert 'hd-terrain079-prototype-assets' not in gui
old_capture='subprocess.run(["import","-window",window,str(shown_path)],check=True,timeout=5)'
assert gui.count(old_capture)==1
gui=gui.replace(old_capture,old_capture.replace('timeout=5','timeout=15'))
small_helper='''def formal_small_mask(hd):
    import base64
    native=Image.new("1",(320,200));draw=ImageDraw.Draw(native)
    group=hd.get("small") or {}
    if not group:return native.resize((1280,800),Image.Resampling.NEAREST)
    need(group.get("formal") is True,"小圖像遮罩沒有正式來源")
    for source in group.get("sources",{}).values():
        if not source.get("art_available"):continue
        mask=base64.b64decode(source["mask"],validate=True)
        need(len(mask)==8000,"小圖像來源遮罩長度不同")
        for pos in range(64000):
            if mask[pos>>3]&(1<<(pos&7)):draw.point((pos%320,pos//320),fill=1)
    return native.resize((1280,800),Image.Resampling.NEAREST)

'''
gui=gui.replace('def main():',small_helper+'def main():',1)
mask_tail='terrain079_mask(hd)))'
assert gui.count(mask_tail)==2
gui=gui.replace(mask_tail,'ImageChops.logical_or(terrain079_mask(hd),formal_small_mask(hd))))')
english_tail='or hd.get("terrain079",{}).get("painted")):'
assert gui.count(english_tail)==1
gui=gui.replace(english_tail,'or hd.get("terrain079",{}).get("painted") or hd.get("small",{}).get("painted")):')
compile(gui,'formal_world_gui_complete_masks','exec')
city_flow='''            before=status()["step"]
            click(152*4,112*4+48)
            wait(lambda state:state.get("step",0)>=before+8000000,"正常進城未完成")
            switch_round("colony")
            before=status()["step"];xdo("keydown","Escape");time.sleep(0.08);xdo("keyup","Escape")
            wait(lambda state:state.get("step",0)>=before+4000000 and any(i["kind"]=="sea-bar" for i in (live(state).get("items") or [])),"地形驗證未正常離城")
'''
old='            switch_round("terrain079-return")'
assert gui.count(old)==1
gui=gui.replace(old,city_flow+old,1)
gui=gui.replace('len(checks)==82','len(checks)==92').replace('82組五語GUI','92組五語GUI')
old='                center=center_record(hd)'
if old not in gui:old='                center = center_record(hd)'
assert gui.count(old)==1
guard='''                if graphics=="hd" and scene=="colony" and not fallback:
                    need(hd.get("terrain079",{}).get("painted",0)==0,"城內殘留世界079")
                    small=hd.get("small") or {}
                    need(small.get("formal") is True and all(small.get("sources",{}).get(str(n),{}).get("painted",0)>0 for n in [5,*range(22,38),42,56,59,62,67,68,69,94,122,123,124]),"正常城內小圖像未完整合成")
'''
gui=gui.replace(old,guard+old,1)
compile(gui,'formal_world_gui_with_city','exec')
out.mkdir();module=out/'runtime-gui-r1';shutil.copytree(reference,module)
(module/'terrain079_probe_helpers.go').write_text(HELPER)
p=module/'adapter.go';s=p.read_text()
old='\tfrontendDisplayStartupOptions = func(options displayOptions) displayOptions { return hdStartupOptions(hd, options) }'
assert s.count(old)==1
prefix=' if *hdTerrain079ProbeRoot!="" { if hd==nil || hd.terrain079==nil {panic("正式079診斷需要已載入HD")}; hdTerrain079Active=hd.terrain079; hd.terrain079.trace=true; defer terrain079ProbeDump(*out) }\n'
s=s.replace(old,prefix+old,1)
old='\t\tif label == "" {\n\t\t\tif frontendFrameSink != nil {'
assert s.count(old)==1
s=s.replace(old,'\t\tif label == "" {\n terrain079ProbeFrame(output,rec)\n\t\t\tif frontendFrameSink != nil {',1);p.write_text(s)
subprocess.run(['gofmt','-w','adapter.go','terrain079_probe_helpers.go'],cwd=module,check=True,timeout=30)
dest=out/'gui-bundle-r1';shutil.copytree(bundle,dest,symlinks=True)
subprocess.run(['go','build','-trimpath','-o',str(dest/'bin/colonization-window'),'.'],cwd=module,check=True,timeout=180)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
RUN=RUN.replace('Xvfb :89 -screen','Xvfb :89 -noreset -screen')
RUN=RUN.replace('export DISPLAY=:89\n','export DISPLAY=:89\nfor attempt in $(seq 1 100); do if xdotool getdisplaygeometry >/dev/null 2>&1; then break; fi; sleep 0.1; done\nxdotool getdisplaygeometry >/dev/null\n')
(out/'probe-gui-r1.py').write_text(gui);(out/'run-gui-r1.sh').write_text(RUN)
unchanged={p.name:sha(p)==sha(module/p.name) for p in reference.glob('*.go') if p.name!='adapter.go'}
assert all(unchanged.values()) and len(list(module.glob('*.go')))==46
report={'kind':'formal-world079-read-only-GUI-probe','formal_binary_sha256':sha(bundle/'bin/colonization-window'),'probe_binary_sha256':sha(dest/'bin/colonization-window'),'base_go_sources_unchanged':unchanged,'only_changed_go':['adapter.go','terrain079_probe_helpers.go'],'production_assets':True,'prototype_asset_flags':False,'gui_script_sha256':sha(out/'probe-gui-r1.py')}
(out/'gui-build-r1.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS_TERRAIN079_FORMAL_READ_ONLY_GUI_BUILD',report['probe_binary_sha256'],flush=True)
