"""規格064 R44 DRAFT：中央來源正常懸停、移開、返回與五語恢復。"""
import argparse,hashlib,os,subprocess
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
p.add_argument('--formal',action='store_true',help='規格064 R44 READY：驗證正式第009幀，不加原型旗標')
a=p.parse_args();repo=Path(__file__).resolve().parents[1];dest=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0
assert dest.is_relative_to('/out') and dest.parent.stat().st_uid==os.getuid() and not dest.exists()
base=dest.with_name(dest.name+'.base.py');assert not base.exists()
subprocess.run(['python3',str(repo/'tools/build_hd_building_nine_gui_probe.py'),'--formal','--output',str(base)],check=True,timeout=60)
s=base.read_text()
def one(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
one('    args = parser.parse_args()','    parser.add_argument("--center-assets",type=Path,required=True)\n    args = parser.parse_args()')
one('    log = (output / "process.log").open("wb")','''    center_root=output/"center";center_root.mkdir()
    command += ["--hd-center-prototype-assets",str(args.center_assets),"--hd-center-probe-root",str(center_root)]
    log = (output / "process.log").open("wb")''')
one('def main():','''def center_mask(hd):
    center=hd.get("center") or {}
    if not center:return Image.new("1",(1280,800))
    need(center.get("prototype") is True,"中央不是隔離原型")
    raw=base64.b64decode(center["mask"],validate=True)
    need(len(raw)==8000,"中央遮罩長度不同")
    bits=[bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)]
    need(sum(bits)==center["valid"] and center["painted"]<=center["valid"],"中央遮罩不同")
    need(set(center["sources"])=={"9"},"中央來源清冊不同")
    im=Image.new("1",(320,200));im.putdata(bits)
    return im.resize((1280,800),Image.Resampling.NEAREST)

def main():''')
mask='ImageChops.logical_or(ImageChops.logical_or(ImageChops.logical_or(sea_mask(hd),person_mask(hd)),shelter_mask(hd)),nine_mask(hd))'
assert s.count(mask)==2;s=s.replace(mask,'ImageChops.logical_or('+mask+',center_mask(hd))')
one('or hd.get("nine",{}).get("painted")):', 'or hd.get("nine",{}).get("painted") or hd.get("center",{}).get("painted")):')
one('or c["native_live"].get("hd", {}).get("nine",{}).get("painted")):', 'or c["native_live"].get("hd", {}).get("nine",{}).get("painted") or c["native_live"].get("hd", {}).get("center",{}).get("painted")):')
one('        map_recoveries=[]','''        center_recoveries=[]
        def center_snapshot(label,locale="zh-Hant"):
            before=status()["step"];marker=center_root/"center-request.json"
            need(not marker.exists(),"中央快照尚未完成")
            marker.write_text(json.dumps({"label":label,"buttons":0,"min_step":before+200000,"require_hd":bool(locale),"ordinal":9,"locale":locale}))
            wait(lambda state:(center_root/label/"check.json").is_file() and not marker.exists(),"中央快照未完整保存："+label)
            return json.loads((center_root/label/"check.json").read_bytes())
        map_recoveries=[]''')
one('scene in person_targets or scene in shelter_targets or scene in nine_targets else','scene in person_targets or scene in shelter_targets or scene in nine_targets or scene in {"center-start","center-return"} else')
one('                if scene in nine_targets:', '''                if scene in {"center-start","center-return"}:
                    before=status()["step"];move(110*4,30*4+48)
                    wait(lambda state:state.get("step",0)>=before+2000000,"中央正常懸停未完成")
                if scene in nine_targets:''')
one('\n                nine=hd.get("nine") or {}\n','''
                center=hd.get("center") or {}
                if graphics=="hd" and scene in {"center-start","center-return"} and not fallback:
                    need(center.get("prototype") is True and center.get("painted",0)>0,"中央來源沒有HD合成")
                if graphics=="hd" and scene in {"main-menu","world","save-slots","save-success","saved-world","hd-building-encyclopedia","hd-exited-again","hd-quit-confirmation"}:
                    need(center.get("painted",0)==0,"離城後殘留中央來源")
                nine=hd.get("nine") or {}
''')
one('                if graphics=="hd" and scene.startswith("nine-return-"):', '''                if graphics=="hd" and scene=="center-return":
                    label="center-proof-"+locale.lower();proof=center_snapshot(label,locale)
                    recovered=proof["frame"]["native_live"]
                    need(recovered["locale"]==locale and recovered["hd"]["center"]["painted"]>0,"中央關閉設定後未恢復")
                    center_recoveries.append({"locale":locale,"snapshot":label,"step":proof["state"]["step"],"paused_fallback":fallback})
                if graphics=="hd" and scene.startswith("nine-return-"):''')
one('        switch_round("colony")','''        switch_round("colony")
        switch_round("center-start")
        for part,xy in [("left",(100,25)),("body",(110,30)),("right",(130,32))]:
            for action,target in [("hover",xy),("away",(112,160)),("return",xy)]:
                before=status()["step"];x,y=target;move(x*4,y*4+48)
                wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"中央游標位置未到達")
                center_snapshot("center-%s-%s"%(action,part))
        switch_round("center-return")''')
one('        final_live = live(status())','''        need({c["locale"] for c in center_recoveries}==set(LOCALES),"中央五語恢復不完整")
        final_live = live(status())''')
one('            result["nine_normal_recoveries"] = nine_recoveries','            result["center_normal_recoveries"] = center_recoveries\n            result["nine_normal_recoveries"] = nine_recoveries')
one('"shelter_asset":sha(args.shelter_asset.read_bytes())','"shelter_asset":sha(args.shelter_asset.read_bytes()),"center_asset":sha((args.center_assets/"building-009-candidate-v1.png").read_bytes())')
one('        move(65 * 4, 25 * 4 + 48)\n        xdo("mousedown", 3)', '''        move(65 * 4, 25 * 4 + 48)
        # 原版對照證實立即右鍵可被忽略；先等實際懸停與原版推進。
        wait(lambda state:state.get("step",0)>=before+2000000 and
             state.get("dos_mouse",{}).get("x")==65 and state.get("dos_mouse",{}).get("y")==25 and
             any(item.get("source")=="Fur Trader's House" for item in live(state).get("items",[])),"右鍵前建築懸停尚未就緒")
        xdo("mousedown", 3)''')
s=s.replace('["sea","person","shelter","nine"]','["sea","person","shelter","nine","center"]')
s=s.replace('PASS_FORMAL_NINE_FIVE_LANGUAGE_GUI','PASS_CENTER_PROTOTYPE_FIVE_LANGUAGE_GUI')
s=s.replace('result["formal_entry"]','result["prototype_entry"]').replace('"prototype_flags": False','"prototype_flags": True')
s=s.replace('正式十三種HD素材；限本批正常GUI與狀態抽樣，原型72點原版收據沿R42，正式同輸入重播另驗。','中央DRAFT及正式十三種素材；14點中央原始快照、五語恢復與同輸入重播另驗，不授予正式信用。')
if a.formal:
    one('        def open_settings():','''        def choose_setting(x,y,key,value):
            if status().get("display",{}).get("draft",{}).get(key)==value:return
            move(x,y);xdo("mousedown",1)
            try:
                wait(lambda state:state.get("display",{}).get("phase")==2 and state["display"]["draft"].get(key)==value,"設定草稿尚未選取："+key+"="+value)
            finally:
                xdo("mouseup",1)
            time.sleep(0.08)

        def open_settings():''')
    one('                click(363 + 136 * LOCALES.index(locale), 374)\n                click(464 if graphics == "original" else 808, 480)', '                choose_setting(363 + 136 * LOCALES.index(locale),374,"language",locale)\n                choose_setting(464 if graphics == "original" else 808,480,"graphics",graphics)')
    one('    command += ["--hd-center-prototype-assets",str(args.center_assets),"--hd-center-probe-root",str(center_root)]','    # 中央來源由既有正式來源群組載入。')
    one('def center_mask(hd):','''def center_record(hd):
    # 只投影既有第009項診斷，不新增正式觀測器或收據欄位。
    nine=hd.get("nine") or {};source=nine.get("sources",{}).get("9")
    if source is None:return {}
    need(nine.get("formal") is True,"中央來源群組不是正式版本")
    return dict(source,formal=True,sources={"9":source})

def center_mask(hd):''')
    s=s.replace('hd.get("center") or {}','center_record(hd)')
    s=s.replace('hd.get("center",{})','center_record(hd)')
    s=s.replace('c["native_live"].get("hd", {}).get("center",{})','center_record(c["native_live"].get("hd", {}))')
    s=s.replace('center.get("prototype") is True','center.get("formal") is True')
    s=s.replace('recovered["hd"]["center"]["painted"]','center_record(recovered["hd"])["painted"]')
    start=s.index('        def center_snapshot(label,locale="zh-Hant"):')
    end=s.index('        map_recoveries=[]',start)
    s=s[:start]+'''        def center_snapshot(label,locale="zh-Hant"):
            before=status()["step"]
            def ready(state):
                if state.get("step",0)<before+200000:return False
                current=live(state);hd=current.get("hd") or {}
                return current.get("locale")==locale and hd.get("reason")=="known-building" and center_record(hd).get("painted",0)>0
            state=wait(ready,"正式中央來源未恢復："+label)
            proof={"state":state,"frame":state["frame"],"formal_status_sample":True}
            directory=center_root/label;directory.mkdir()
            (directory/"check.json").write_text(json.dumps(proof,ensure_ascii=False)+"\\n")
            return proof
'''+s[end:]
    s=s.replace('building-009-candidate-v1.png','building-009.png')
    s=s.replace('PASS_CENTER_PROTOTYPE_FIVE_LANGUAGE_GUI','PASS_FORMAL_CENTER_FIVE_LANGUAGE_GUI')
    s=s.replace('result["prototype_entry"]','result["formal_entry"]').replace('"prototype_flags": True','"prototype_flags": False')
    s=s.replace('中央DRAFT及正式十三種素材；14點中央原始快照、五語恢復與同輸入重播另驗，不授予正式信用。','正式十四種素材；14筆中央現況診斷，原型原始快照沿R44；正式49點獨立模型與同輸入四側重播另驗。')
    assert '--hd-center-' not in s and 'center-request.json' not in s
compile(s,str(dest),'exec');dest.write_text(s)
print('PASS_CENTER_GUI_PROBE_BUILD',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
