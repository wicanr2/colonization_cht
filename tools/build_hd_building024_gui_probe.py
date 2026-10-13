"""規格064 DRAFT：木棚五語切換、懸停及按住拖曳的正常視窗驗證。"""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output",type=Path,required=True)
a=parser.parse_args();repo=Path(__file__).resolve().parents[1];dest=a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(repo/"workplace")
assert dest.parent.stat().st_uid==os.getuid() and not dest.exists()
base=dest.with_name(dest.name+".base.py");assert not base.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_person_gui_probe.py"),"--formal","--output",str(base)],check=True,timeout=30)
assert hashlib.sha256(base.read_bytes()).hexdigest()=="13528dd54f5eb601258d7bcf134d23de3ba4e66264f66eaf22d3e938b6a527c8"
s=base.read_text()
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
one("    args = parser.parse_args()",'    parser.add_argument("--shelter-asset",type=Path,required=True)\n    args = parser.parse_args()')
one('    log = (output / "process.log").open("wb")','''    shelter_root=output/"shelter"
    shelter_root.mkdir()
    need(sha(args.shelter_asset.read_bytes())=="cb83a56cde5f06bb13bc69237fe5476efb6b40eb8ea6cfb2fe0942f3fd3da462","木棚候選不同")
    command += ["--hd-shelter-prototype-asset",str(args.shelter_asset),"--hd-shelter-probe-root",str(shelter_root)]
    log = (output / "process.log").open("wb")''')
helper='''def shelter_mask(hd):
    shelter=hd.get("shelter") or {}
    if not shelter:return Image.new("1",(1280,800))
    need(shelter.get("prototype") is True,"木棚不是隔離原型")
    raw=base64.b64decode(shelter["mask"],validate=True)
    need(len(raw)==8000,"木棚來源遮罩不同")
    data=[bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)]
    need(sum(data)==shelter["valid"] and shelter.get("painted",0)<=shelter["valid"],"木棚遮罩或合成不同")
    result=Image.new("1",(320,200));result.putdata(data)
    return result.resize((1280,800),Image.Resampling.NEAREST)

'''
one("def main():",helper+"def main():")
old="ImageChops.logical_or(sea_mask(hd),person_mask(hd))"
assert s.count(old)>=2;s=s.replace(old,"ImageChops.logical_or("+old+",shelter_mask(hd))")
one('or hd.get("person",{}).get("painted")):', 'or hd.get("person",{}).get("painted") or hd.get("shelter",{}).get("painted")):')
one('or c["native_live"].get("hd", {}).get("person",{}).get("painted")):', 'or c["native_live"].get("hd", {}).get("person",{}).get("painted") or c["native_live"].get("hd", {}).get("shelter",{}).get("painted")):')
one('        map_recoveries=[]','''        shelter_targets={"shelter-hover-roof":(42,57),"shelter-away-roof":(112,160),"shelter-return-roof":(42,57),
                         "shelter-hover-post":(49,69),"shelter-away-post":(112,160),"shelter-return-post":(49,69)}
        def shelter_snapshot(label,buttons=0):
            before=status()["step"]
            marker=shelter_root/"shelter-request.json"
            need(not marker.exists(),"前一木棚診斷尚未完成")
            marker.write_text(json.dumps({"label":label,"buttons":buttons,"min_step":before+200000}))
            wait(lambda state:(shelter_root/label/"check.json").is_file(),"木棚診斷未保存："+label)
            return json.loads((shelter_root/label/"check.json").read_bytes())

        map_recoveries=[]''')
one('                person=hd.get("person") or {}','''                shelter=hd.get("shelter") or {}
                if graphics=="hd" and scene in shelter_targets and not fallback:
                    need(shelter.get("prototype") is True and shelter.get("valid",0)>0,"木棚懸停缺少來源")
                    need(shelter["owned"]==shelter["valid"],"木棚來源已過期")
                    if scene in {"shelter-away-roof","shelter-away-post"}:
                        need(shelter["valid"]==263 and shelter["cursor_restore_points"]>0,"游標離開後木棚未完整還原")
                person=hd.get("person") or {}''')
one('if scene in person_targets else', 'if scene in person_targets or scene in shelter_targets else')
one('                if scene in person_targets:\n                    hover_start','''                if scene in shelter_targets:
                    hover_start=status()["step"]
                    x,y=shelter_targets[scene]
                    move(x*4,y*4+48)
                    wait(lambda state:state.get("step",0)>=hover_start+2000000,"木棚正常懸停未完成")
                if scene in person_targets:
                    hover_start''')
one('        switch_round("colony")','''        switch_round("colony")
        for label,(x,y) in shelter_targets.items():
            before=status()["step"];move(x*4,y*4+48)
            wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"木棚懸停座標未到達")
            shelter_snapshot(label)
            switch_round(label)
        need(status()["display"]["current"]["graphics"]=="hd","木棚拖曳前未保持HD")
        before=status()["step"];move(112*4,160*4+48);xdo("mousedown",1)
        wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("buttons")==1,"木棚路徑按住未送到原版")
        shelter_snapshot("shelter-drag-held",1)
        before=status()["step"];move(42*4,57*4+48)
        wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==42 and state.get("dos_mouse",{}).get("y")==57,"按住移至木棚未完成")
        shelter_snapshot("shelter-drag-moved",1)
        before=status()["step"];move(112*4,160*4+48)
        wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==112 and state.get("dos_mouse",{}).get("y")==160,"木棚拖曳返回未完成")
        shelter_snapshot("shelter-drag-returned",1)
        before=status()["step"];xdo("mouseup",1)
        wait(lambda state:state.get("step",0)>=before+2000000 and state.get("dos_mouse",{}).get("buttons")==0,"木棚拖曳未放開")
        shelter_snapshot("shelter-drag-released")
        switch_round("shelter-drag-complete")''')
one("PASS_FORMAL_PERSON_HD_FIVE_LANGUAGE_GUI","PASS_SHELTER_PROTOTYPE_FIVE_LANGUAGE_GUI")
one('result["formal_entry"] =','result["prototype_entry"] =')
one('"prototype_flags": False','"prototype_flags": True')
one('"person_asset":sha(args.person_asset.read_bytes())','"person_asset":sha(args.person_asset.read_bytes()),"shelter_asset":sha(args.shelter_asset.read_bytes())')
one("正式首座、海洋與第100幀人物；限本批正常GUI，其他人物、動畫及完整HD未完成。","木棚DRAFT及正式首座、海洋與人物；來源／游標獨立稽核及同輸入重播另驗，不授予木棚正式HD信用。")
# 既有252組到458M步；新增70組與診斷約增加180M步，保留有界餘量。
assert s.count('"--window-steps", "500000000"')==2
s=s.replace('"--window-steps", "500000000"','"--window-steps", "900000000"')
compile(s,str(dest),"exec");dest.write_text(s)
dest.with_name(dest.name+".build.json").write_text(json.dumps({"kind":"DRAFT-shelter-gui","base_sha256":hashlib.sha256(base.read_bytes()).hexdigest(),"generated_sha256":hashlib.sha256(dest.read_bytes()).hexdigest()},indent=2)+"\n")
print("PASS_SHELTER_GUI_PROBE_BUILD",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
