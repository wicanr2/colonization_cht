"""規格063：重生正式或隔離人物的五語懸停與拖曳視窗驗證。"""
from pathlib import Path
import argparse,hashlib,json,os,subprocess
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output",type=Path,required=True)
parser.add_argument("--formal",action="store_true",help="依規格063 READY驗證正式人物接線")
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];dest=args.output.resolve();out=dest.parent
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(repo/"workplace")
assert out.is_dir() and out.stat().st_uid==os.getuid() and not dest.exists()
source=dest.with_name(dest.name+".base.py")
assert not source.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_runtime_gui_probe.py"),"--formal","--output",str(source)],check=True,timeout=30)
assert hashlib.sha256(source.read_bytes()).hexdigest()=="be587a6d46f742f30081c8edf1c86c34c137a610c7c1d96d22a26c0fea69c6fd"
s=source.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,a
 s=s.replace(a,b,1)
one('    args = parser.parse_args()','    parser.add_argument("--person-asset",type=Path,required=True)\n    args = parser.parse_args()')
one('    log = (output / "process.log").open("wb")','''    person_root=output/"person"
    person_root.mkdir()
    need(sha(args.person_asset.read_bytes())=="be2ace90ee85444af2fdaabb568a4ec1c67b3d327e30122c1b30ac471f514346","人物原圖不同")
    command += ["--hd-person-prototype-asset",str(args.person_asset),"--hd-person-probe-root",str(person_root)]
    log = (output / "process.log").open("wb")''')
helper='''def person_mask(hd):
    person=hd.get("person") or {}
    if not person:return Image.new("1",(1280,800))
    need(person.get("prototype") is True,"人物未由DRAFT原型繪製")
    raw=base64.b64decode(person["mask"],validate=True)
    need(len(raw)==8000,"人物來源遮罩長度不同")
    data=[bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)]
    need(sum(data)==person["valid"] and person.get("painted",0)<=person["valid"],"人物遮罩與來源不同")
    im=Image.new("1",(320,200));im.putdata(data)
    return im.resize((1280,800),Image.Resampling.NEAREST)

'''
one("def main():",helper+"def main():")
old='safe=ImageChops.logical_or(safe,sea_mask(hd))'
assert s.count(old)>=2
s=s.replace(old,'safe=ImageChops.logical_or(safe,ImageChops.logical_or(sea_mask(hd),person_mask(hd)))')
one('if graphics == "original" or not (hd.get("painted") or hd.get("sea",{}).get("painted")):',
    'if graphics == "original" or not (hd.get("painted") or hd.get("sea",{}).get("painted") or hd.get("person",{}).get("painted")):')
one('or c["native_live"].get("hd", {}).get("sea",{}).get("painted")):', 'or c["native_live"].get("hd", {}).get("sea",{}).get("painted") or c["native_live"].get("hd", {}).get("person",{}).get("painted")):')
one('        map_recoveries=[]','''        def person_snapshot(label,buttons=0):
            before=status()["step"]
            request={"label":label,"buttons":buttons,"min_step":before+200000}
            marker=person_root/"person-request.json"
            need(not marker.exists(),"前一人物診斷尚未完成")
            marker.write_text(json.dumps(request))
            wait(lambda state:(person_root/label/"check.json").is_file(),"人物診斷未保存："+label)
            return json.loads((person_root/label/"check.json").read_bytes())

        person_targets={"person-hover-main":(239,39),"person-away-main":(112,160),"person-return-main":(239,39),
                        "person-hover-garrison":(12,142),"person-away-garrison":(112,160),"person-return-garrison":(12,142)}
        map_recoveries=[]''')
one('                sea=hd.get(', '''                person=hd.get("person") or {}
                if graphics=="hd" and scene in person_targets and not fallback:
                    need(person.get("prototype") is True and person.get("valid",0)>=60,"人物懸停缺少已驗來源")
                    need(person["owned"]==person["valid"],"人物來源已過期")
                    if scene in {"person-away-main","person-away-garrison"}:
                        need(person["valid"]==120,"游標離開後人物來源未完整還原")
                        need(person["cursor_restore_points"]>0,"人物還原沒有實際配對")
                sea=hd.get(''')
one('for locale, graphics in [(l, g) for l in locales for g in ["hd", "original"]]:',
    'for locale, graphics in [(l, g) for l in locales for g in (["original","hd"] if scene in person_targets else ["hd", "original"])]:')
one('                sea_targets={"sea-hover-near":(32,32),"sea-hover-far":(96,48),"sea-cursor-returned":(32,32)}\n                if scene in sea_targets:\n                    hover_start',
'''                if scene in person_targets:
                    hover_start=status()["step"]
                    x,y=person_targets[scene]
                    move(x*4,y*4+48)
                    wait(lambda state:state.get("step",0)>=hover_start+2000000,"人物正常懸停未完成")
                sea_targets={"sea-hover-near":(32,32),"sea-hover-far":(96,48),"sea-cursor-returned":(32,32)}
                if scene in sea_targets:
                    hover_start''')
one('        switch_round("colony")','''        switch_round("colony")
        for label,(x,y) in person_targets.items():
            before=status()["step"]
            move(x*4,y*4+48)
            wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==x and state.get("dos_mouse",{}).get("y")==y,"人物懸停座標未到達")
            person_snapshot(label)
            switch_round(label)
        need(status()["display"]["current"]["graphics"]=="hd","拖曳前未保持HD")
        before=status()["step"]
        move(15*4,150*4+48)
        xdo("mousedown",1)
        wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("buttons")==1,"人物按住未送到原版")
        person_snapshot("person-drag-held",1)
        before=status()["step"];move(42*4,150*4+48)
        wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==42,"人物拖曳移動未完成")
        person_snapshot("person-drag-moved",1)
        before=status()["step"];move(15*4,150*4+48)
        wait(lambda state:state.get("step",0)>=before+1000000 and state.get("dos_mouse",{}).get("x")==15,"人物拖曳返回未完成")
        person_snapshot("person-drag-returned",1)
        before=status()["step"];xdo("mouseup",1)
        wait(lambda state:state.get("step",0)>=before+2000000 and state.get("dos_mouse",{}).get("buttons")==0,"人物拖曳未放開")
        person_snapshot("person-drag-released")
        switch_round("person-drag-complete")''')
one('"result": "PASS_FORMAL_HD_FIVE_LANGUAGE_GUI"','"result": "PASS_PERSON_PROTOTYPE_FIVE_LANGUAGE_GUI"')
one('result["formal_entry"] =','result["prototype_entry"] =')
one('"prototype_flags": False','"prototype_flags": True')
one('result["limitations"] = ["正式首座建築與第148幀海洋；其他素材、動畫及完整五語未完成，本輪重播另驗。"]',
    'result["limitations"] = ["規格063 DRAFT人物；首座及海洋正式來源沿用。人物直接懸停與拖曳、本輪同狀態重播另驗，不授予正式接線信用。"]')
one('"sea_asset":sha(args.sea_asset.read_bytes())','"sea_asset":sha(args.sea_asset.read_bytes()),"person_asset":sha(args.person_asset.read_bytes())')
if args.formal:
 one('    person_root=output/"person"\n    person_root.mkdir()\n','')
 one('    command += ["--hd-person-prototype-asset",str(args.person_asset),"--hd-person-probe-root",str(person_root)]',
     '    need(args.person_asset.resolve()==(args.formal_launcher.parent/"graphics/person-100.png").resolve(),"正式人物素材路徑不同")')
 start=s.index('        def person_snapshot(label,buttons=0):')
 end=s.index('        person_targets={',start)
 s=s[:start]+'        def person_snapshot(label,buttons=0):\n            return None\n\n'+s[end:]
 assert s.count('person.get("prototype") is True')==2
 s=s.replace('person.get("prototype") is True','person.get("formal") is True')
 one('人物未由DRAFT原型繪製','人物未由正式執行期繪製')
 one('PASS_PERSON_PROTOTYPE_FIVE_LANGUAGE_GUI','PASS_FORMAL_PERSON_HD_FIVE_LANGUAGE_GUI')
 one('result["prototype_entry"] =','result["formal_entry"] =')
 one('"prototype_flags": True','"prototype_flags": False')
 one('規格063 DRAFT人物；首座及海洋正式來源沿用。人物直接懸停與拖曳、本輪同狀態重播另驗，不授予正式接線信用。',
     '正式首座、海洋與第100幀人物；限本批正常GUI，其他人物、動畫及完整HD未完成。')
p=dest;assert not p.exists();compile(s,str(p),"exec");p.write_text(s)
dest.with_name(dest.name+".build.json").write_text(json.dumps({"kind":"formal-person-gui" if args.formal else "person-prototype-gui","base_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),"generated_sha256":hashlib.sha256(p.read_bytes()).hexdigest()},indent=2)+"\n")
print("PASS_FORMAL_PERSON_GUI_PROBE_BUILD" if args.formal else "PASS_PERSON_GUI_PROBE_BUILD",hashlib.sha256(p.read_bytes()).hexdigest())
