"""規格064 R42 DRAFT：九來源正常游標往返與五語顯示驗證。"""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];dest=a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(repo/"workplace")
assert dest.parent.stat().st_uid==os.getuid() and not dest.exists()
base=dest.with_name(dest.name+".base.py");assert not base.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_building024_gui_probe.py"),"--formal","--output",str(base)],check=True,timeout=45)
assert hashlib.sha256(base.read_bytes()).hexdigest()=="daaf671c5fef5916b7cd465e002bd1d607013141580ecd11b25e5c0760398192"
s=base.read_text()
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
one("    args = parser.parse_args()", '    parser.add_argument("--nine-assets",type=Path,required=True)\n    args = parser.parse_args()')
one('    env["GOMEMLIMIT"] = "1200MiB"','    env["GOMEMLIMIT"] = "2400MiB"')
one('    log = (output / "process.log").open("wb")','''    nine_root=output/"nine"
    nine_root.mkdir()
    command += ["--hd-nine-prototype-assets",str(args.nine_assets),"--hd-nine-probe-root",str(nine_root)]
    log = (output / "process.log").open("wb")''')
one('return hd.get("shelter",{}).get("valid")==263','return hd.get("shelter",{}).get("valid",0)>0 and hd.get("shelter",{}).get("painted",0)>0')
one('        shelter_snapshot("shelter-drag-released")','''        shelter_snapshot("shelter-drag-released")
        # 未知副本撤銷的來源不由同色復活；以正常離城／重進建立完整來源。
        before=status()["step"];xdo("keydown","Escape");time.sleep(0.08);xdo("keyup","Escape")
        wait(lambda state:state.get("step",0)>=before+4000000 and any(i.get("kind")=="sea-bar" for i in live(state).get("items",[])),"木棚拖曳後正常離城未完成")
        before=status()["step"];click(152*4,112*4+48)
        wait(lambda state:state.get("step",0)>=before+8000000 and any(i.get("id")=="STRING:template:colony-title" for i in live(state).get("items",[])),"木棚拖曳後正常重進未完成")
        wait(lambda state:live(state).get("hd",{}).get("shelter",{}).get("valid")==263,"正常重進未建立完整木棚來源")
        shelter_snapshot("shelter-drag-redrawn")''')
one("def main():",'''def nine_mask(hd):
    nine=hd.get("nine") or {}
    if not nine:return Image.new("1",(1280,800))
    need(nine.get("prototype") is True,"九來源不是隔離原型")
    raw=base64.b64decode(nine["mask"],validate=True)
    need(len(raw)==8000,"九來源遮罩長度不同")
    values=[bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)]
    need(sum(values)==nine["valid"] and nine["painted"]<=nine["valid"],"九來源遮罩不同")
    union=bytearray(8000)
    for ordinal,source in nine["sources"].items():
        part=base64.b64decode(source["mask"],validate=True)
        need(len(part)==8000 and sum(v.bit_count() for v in part)==source["valid"],"個別來源遮罩不同："+ordinal)
        for i,v in enumerate(part):
            need(not union[i]&v,"九來源彼此重疊");union[i]|=v
    need(bytes(union)==raw,"九來源聯集不同")
    im=Image.new("1",(320,200));im.putdata(values)
    return im.resize((1280,800),Image.Resampling.NEAREST)

def main():''')
old='ImageChops.logical_or(ImageChops.logical_or(sea_mask(hd),person_mask(hd)),shelter_mask(hd))'
assert s.count(old)==2;s=s.replace(old,'ImageChops.logical_or('+old+',nine_mask(hd))')
one('or hd.get("shelter",{}).get("painted")):', 'or hd.get("shelter",{}).get("painted") or hd.get("nine",{}).get("painted")):')
one('or c["native_live"].get("hd", {}).get("shelter",{}).get("painted")):', 'or c["native_live"].get("hd", {}).get("shelter",{}).get("painted") or c["native_live"].get("hd", {}).get("nine",{}).get("painted")):')
one('        map_recoveries=[]','''        # R42原版第45點的逐點身分選出實際有來源的位置。
        nine_positions={16:(159,116),21:(184,32),27:(156,28),35:(150,63),39:(78,66),
                        42:(92,104),43:(30,77),44:(30,63),45:(150,86)}
        nine_targets={"nine-start":(112,160)}
        nine_targets.update({"nine-return-%03d"%n:xy for n,xy in nine_positions.items()})
        nine_recoveries=[]
        def nine_snapshot(label,ordinal=0,locale=""):
            before=status()["step"];marker=nine_root/"nine-request.json"
            need(not marker.exists(),"前一九來源快照尚未完成")
            marker.write_text(json.dumps({"label":label,"buttons":0,"min_step":before+200000,"require_hd":ordinal>0,"ordinal":ordinal,"locale":locale}))
            wait(lambda state:(nine_root/label/"check.json").is_file() and not marker.exists(),"九來源診斷未完整保存："+label)
            return json.loads((nine_root/label/"check.json").read_bytes())
        map_recoveries=[]''')
one('scene in person_targets or scene in shelter_targets else','scene in person_targets or scene in shelter_targets or scene in nine_targets else')
one('                if scene in shelter_targets:\n                    hover_start','''                if scene in nine_targets:
                    hover_start=status()["step"];x,y=nine_targets[scene]
                    move(x*4,y*4+48)
                    wait(lambda state:state.get("step",0)>=hover_start+2000000,"九來源正常懸停未完成")
                if scene in shelter_targets:
                    hover_start''')
one('                shelter=hd.get("shelter") or {}','''                nine=hd.get("nine") or {}
                if graphics=="hd" and scene in nine_targets and not fallback:
                    need(nine.get("prototype") is True and nine["valid"]>0 and nine["owned"]==nine["valid"],"九來源遺失或過期")
                    if scene.startswith("nine-return-"):
                        ordinal=str(int(scene.rsplit("-",1)[1]));source=nine["sources"][ordinal]
                        need(source["valid"]>0 and source["painted"]>0,"指定九來源沒有合成："+ordinal)
                if graphics=="hd" and scene in {"main-menu","world","save-slots","save-success","saved-world","hd-building-encyclopedia","hd-exited-again","hd-quit-confirmation"}:
                    need(nine.get("painted",0)==0,"離城後殘留九來源")
                shelter=hd.get("shelter") or {}''')
one('                phase(0)\n                event_actions = same_state(first, step)','''                phase(0)
                event_actions = same_state(first, step)
                if graphics=="hd" and scene.startswith("nine-return-"):
                    ordinal=int(scene.rsplit("-",1)[1])
                    label="nine-proof-%03d-%s"%(ordinal,locale.lower())
                    proof=nine_snapshot(label,ordinal,locale)
                    recovered=proof["frame"]["native_live"]
                    source=recovered["hd"]["nine"]["sources"][str(ordinal)]
                    need(recovered["locale"]==locale and source["painted"]>0,"關閉設定後九來源未恢復")
                    nine_recoveries.append({"scene":scene,"ordinal":ordinal,"locale":locale,"paused_fallback":fallback,"step":proof["state"]["step"],"snapshot":label,"painted":source["painted"]})''')
one('        switch_round("colony")','''        switch_round("colony")
        switch_round("nine-start")
        for ordinal,xy in nine_positions.items():
            for action,target in [("hover",xy),("away",(112,160)),("return",xy)]:
                before=status()["step"];x,y=target;move(x*4,y*4+48)
                wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"九來源實際游標位置未到達")
                nine_snapshot("nine-%s-%03d"%(action,ordinal))
            switch_round("nine-return-%03d"%ordinal)''')
one('        final_live = live(status())','''        for ordinal in nine_positions:
            covered={c["locale"] for c in nine_recoveries if c["ordinal"]==ordinal and c["painted"]>0}
            need(covered==set(LOCALES),"九來源五語正向不完整："+str(ordinal)+str(covered))
        final_live = live(status())''')
one('                if scene == "hd-building-hover":','                if scene in {"hd-building-hover","hd-building-hover-return"}:')
one('if scene == "hd-building-hover" and not fallback:', 'if scene in {"hd-building-hover","hd-building-hover-return"} and not fallback:')
one('        switch_round("hd-building-hover")','''        switch_round("hd-building-hover")
        # 固定追加正常移開／返回，保留重畫中的安全回退，不挑選或丟棄失配樣本。
        for x,y in [(112,160),(65,25)]:
            before=status()["step"];move(x*4,y*4+48)
            wait(lambda state:state.get("step",0)>=before+2000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"首座正常返回未完成")
        switch_round("hd-building-hover-return")''')
one('{"hd-building-hover"}) and','{"hd-building-hover","hd-building-hover-return"}) and')
one("PASS_FORMAL_SHELTER_HD_FIVE_LANGUAGE_GUI","PASS_NINE_PROTOTYPE_FIVE_LANGUAGE_GUI")
one('result["formal_entry"] =','result["prototype_entry"] =')
one('            result["prototype_entry"] =','            result["nine_normal_recoveries"] = nine_recoveries\n            result["prototype_entry"] =')
one('                print("PASS_HD_RUNTIME_GUI_SWITCH", scene, locale, graphics, step, hd.get("painted", 0), flush=True)', '''                with (output/"verified-switches.jsonl").open("a") as journal:
                    journal.write(json.dumps(checks[-1],ensure_ascii=False)+"\\n")
                print("PASS_HD_RUNTIME_GUI_SWITCH", scene, locale, graphics, step, hd.get("painted", 0), flush=True)''')
one('"prototype_flags": False','"prototype_flags": True')
one('"shelter_asset":sha(args.shelter_asset.read_bytes())','"shelter_asset":sha(args.shelter_asset.read_bytes()),"nine_assets":{p.name:sha(p.read_bytes()) for p in sorted(args.nine_assets.glob("building-*-candidate-v1.png"))}')
one("正式首座、海洋、人物及第024幀木棚；限本批正常GUI，其他建築、動畫及完整HD未完成。","九來源DRAFT及既有四種正式HD；限本批正常GUI，來源獨立審查與同輸入重播另驗。")
# 既有604M步，加110組、27快照及首座正常返回，保留有界餘量。
assert s.count('"--window-steps", "900000000"')==2;s=s.replace('"--window-steps", "900000000"','"--window-steps", "1200000000"')
compile(s,str(dest),"exec");dest.write_text(s)
dest.with_name(dest.name+".build.json").write_text(json.dumps({"kind":"DRAFT-nine-gui","base_sha256":hashlib.sha256(base.read_bytes()).hexdigest(),"generated_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()},indent=2)+"\n")
print("PASS_NINE_GUI_PROBE_BUILD",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
