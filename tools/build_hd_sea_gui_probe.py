"""規格062 DRAFT：產生隔離海洋五語真視窗探針。"""
import argparse,hashlib,os,subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1]
dest=args.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(repo/"workplace")
assert dest.parent.is_dir() and dest.parent.stat().st_uid==os.getuid() and not dest.exists()
source=dest.with_name(dest.name+".base.py")
assert not source.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_runtime_gui_probe.py"),"--formal","--output",str(source)],check=True,timeout=30)
assert hashlib.sha256(source.read_bytes()).hexdigest()=="e20481882eafa24066c56f2c68533ba84b90b73b6ed05d89cfb2cb1bd100184f"
s=source.read_text()
def one(old,new):
 global s
 assert s.count(old)==1,old
 s=s.replace(old,new,1)
one('import argparse','import argparse\nimport base64')
one('    args = parser.parse_args()','    parser.add_argument("--sea-asset",type=Path,required=True)\n    args = parser.parse_args()')
one('    log = (output / "process.log").open("wb")','    command += ["--hd-sea-prototype-asset",str(args.sea_asset)]\n    log = (output / "process.log").open("wb")')
one('    need(args.formal_launcher and not args.reload_save, "正式HD驗收需要正式啟動器")','    need(args.formal_launcher and not args.reload_save, "DRAFT海洋需要隔離啟動器副本")\n    need(sha(args.sea_asset.read_bytes())=="27deaccd2785a85d5ba45c462ee7ca47d160ec48683b291b379573fded5f9674","海洋候選不同")')
helper='''def sea_mask(hd):
    sea=hd.get("sea",{})
    if not sea:return Image.new("1",(1280,800))
    need(sea.get("prototype") is True,"海洋未由隔離原型繪製")
    raw=base64.b64decode(sea["mask"],validate=True)
    need(len(raw)==8000,"海洋遮罩尺寸不同")
    data=[bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)]
    need(sum(data)==sea["painted"],"海洋遮罩與實際繪點不同")
    im=Image.new("1",(320,200));im.putdata(data)
    return im.resize((1280,800),Image.Resampling.NEAREST)

'''
one('def main():',helper+'def main():')
one('                    if graphics == "original" or not hd.get("painted"):','                    if graphics == "original" or not (hd.get("painted") or hd.get("sea",{}).get("painted")):')
one('                        ImageDraw.Draw(safe).rectangle((224, 52, 315, 159), fill=1)','                        if hd.get("painted"): ImageDraw.Draw(safe).rectangle((224, 52, 315, 159), fill=1)\n                        safe=ImageChops.logical_or(safe,sea_mask(hd))')
one('                    difference = ImageChops.difference(actual, original)\n                    outside','                    if graphics=="hd":safe=ImageChops.logical_or(safe,sea_mask(hd))\n                    difference = ImageChops.difference(actual, original)\n                    outside')
one('                if locale == "en":','''                sea=hd.get("sea",{})
                sea_targets={"sea-hover-near":(32,32),"sea-hover-far":(96,48),"sea-cursor-returned":(32,32)}
                if scene in sea_targets:
                    need((e["dos_mouse"]["x"],e["dos_mouse"]["y"])==sea_targets[scene],"海面收據沒有保留實際游標位置")
                if graphics=="hd" and not fallback and scene in {"world","saved-world","hd-exited-again","sea-hover-near","sea-hover-far","sea-cursor-returned"}:
                    need(sea.get("painted",0)>0,"正常世界缺海洋HD")
                if graphics=="hd" and not fallback and scene in {"world","saved-world","hd-exited-again"}:
                    need(sea.get("owned")==33123 and sea.get("painted")==33123,"背景還原後海洋來源不完整")
                if graphics=="hd" and scene in {"colony","hd-reentered-colony","hd-building-hover","hd-encyclopedia-closed","hd-building-encyclopedia"}:
                    need(sea.get("painted",0)==0,"城內仍有海洋HD")
                if locale == "en":''')
s=s.replace('"world", "saved-world", "hd-exited-again"','"world", "saved-world", "hd-exited-again", "sea-hover-near", "sea-hover-far", "sea-cursor-returned"')
one('            switch_round("world")','''            switch_round("world")
            for scene,x,y in [("sea-hover-near",32,32),("sea-hover-far",96,48),("sea-cursor-returned",32,32)]:
                switch_round(scene)''')
one('                if scene == "hd-building-hover":','''                sea_targets={"sea-hover-near":(32,32),"sea-hover-far":(96,48),"sea-cursor-returned":(32,32)}
                if scene in sea_targets:
                    hover_start=status()["step"]
                    x,y=sea_targets[scene]
                    move(x*4,y*4+48)
                    wait(lambda state:state.get("step",0)>=hover_start+2000000,"海面正常游標移動未完成")
                if scene == "hd-building-hover":''')
one('        def switch_round(scene):','        map_recoveries=[]\n        def switch_round(scene):')
one('                record = live(s)','                map_fallback=False\n                record = live(s)')
one('''                        need(len(maps) == 1 and maps[0].get("source") == "Jamestown" and
                             "Jamestown" in maps[0].get("text", "") and maps[0].get("font_px") == expected,
                             "正常世界或返回世界缺少完整地區字型城名")''','''                        map_fallback=(not maps and (graphics=="original" or fallback) and
                                      record.get("string_misses",{}).get("map-source-or-occlusion-changed\\tJamestown",0)>0)
                        if map_fallback:
                            if graphics=="original":
                                rect=(136*4,118*4,203*4,130*4)
                                need(actual.crop(rect).tobytes()==original.crop(rect).tobytes(),"失配城名未完整回原圖")
                        else:
                            need(len(maps) == 1 and maps[0].get("source") == "Jamestown" and
                                 "Jamestown" in maps[0].get("text", "") and maps[0].get("font_px") == expected,
                                 "正常世界或返回世界缺少完整地區字型城名")''')
one('                event_actions = same_state(first, step)','''                event_actions = same_state(first, step)
                if map_fallback:
                    recovered=wait(lambda state:any(i.get("native_surface")=="map" and i.get("source")=="Jamestown" and
                                       i.get("font_px")==expected for i in live(state).get("items",[])),"原版來源完成後城名未恢復")
                    need(recovered["display"]["current"]=={"language":locale,"graphics":graphics},"恢復時顯示設定不同")
                    map_recoveries.append({"scene":scene,"locale":locale,"graphics":graphics,"fallback_step":step,
                                           "recovered_step":recovered["step"],"reason":"map-source-or-occlusion-changed"})''')
one('        result["verified_cursor_points"] = cursor_points','        result["map_source_recoveries"]=map_recoveries\n        result["verified_cursor_points"] = cursor_points')
one('if c["graphics"] != "hd" or not c["native_live"].get("hd", {}).get("painted"):','if c["graphics"] != "hd" or not (c["native_live"].get("hd", {}).get("painted") or c["native_live"].get("hd", {}).get("sea",{}).get("painted")):')
one('"result": "PASS_FORMAL_HD_FIVE_LANGUAGE_GUI"','"result": "PASS_SEA_PROTOTYPE_FIVE_LANGUAGE_GUI"')
one('result["formal_entry"] =','result["prototype_entry"] =')
one('"prototype_flags": False','"prototype_flags": True')
one('result["limitations"] = ["正式入口、單座HD與本次正常路徑；其他素材、動畫及完整五語仍未完成。"]','result["limitations"] = ["規格062 DRAFT海洋原型，正式入口副本；完整動畫、其他地形、即時效能及本輪重播尚未驗收。"]')
one('"hd_asset": sha(args.hd_asset.read_bytes())','"hd_asset": sha(args.hd_asset.read_bytes()),"sea_asset":sha(args.sea_asset.read_bytes())')
one('        final_live = live(status())','''        for scene in ["world","sea-hover-near","sea-hover-far","sea-cursor-returned","saved-world","hd-exited-again"]:
            covered={c["locale"] for c in checks if c["graphics"]=="hd" and c["scene"]==scene and c["native_live"].get("hd",{}).get("sea",{}).get("painted",0)>0}
            need(covered==set(LOCALES),"五語海洋正向不完整："+scene+str(covered))
        final_live = live(status())''')
# 原版切場時items可序列化為null；等待條件須把它視為尚未出現文字。
for obj in ['live(s)','live(state)']:
    for tail in ['.get("items", [])','.get("items",[])']:
        s=s.replace(obj+tail,'('+obj+'.get("items") or [])')
compile(s,str(dest),"exec")
dest.write_text(s)
print("PASS_SEA_GUI_PROBE_BUILD",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
