import argparse, hashlib, os, subprocess
from pathlib import Path

def extend_sea_checks(s, formal=False):

    def one(old, new):
        nonlocal s
        assert s.count(old) == 1, old
        s = s.replace(old, new, 1)
    one('import argparse', 'import argparse\nimport base64')
    one('    args = parser.parse_args()', '    parser.add_argument("--sea-asset",type=Path,required=True)\n    args = parser.parse_args()')
    one('    log = (output / "process.log").open("wb")', '    command += ["--hd-sea-prototype-asset",str(args.sea_asset)]\n    log = (output / "process.log").open("wb")')
    one('    need(args.formal_launcher and not args.reload_save, "正式HD驗收需要正式啟動器")', '    need(args.formal_launcher and not args.reload_save, "DRAFT海洋需要隔離啟動器副本")\n    need(sha(args.sea_asset.read_bytes())=="27deaccd2785a85d5ba45c462ee7ca47d160ec48683b291b379573fded5f9674","海洋候選不同")')
    helper = 'def sea_mask(hd):\n    sea=hd.get("sea",{})\n    if not sea:return Image.new("1",(1280,800))\n    need(sea.get("prototype") is True,"海洋未由隔離原型繪製")\n    raw=base64.b64decode(sea["mask"],validate=True)\n    need(len(raw)==8000,"海洋遮罩尺寸不同")\n    data=[bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)]\n    need(sum(data)==sea["painted"],"海洋遮罩與實際繪點不同")\n    im=Image.new("1",(320,200));im.putdata(data)\n    return im.resize((1280,800),Image.Resampling.NEAREST)\n\n'
    one('def main():', helper + 'def main():')
    one('                    if graphics == "original" or not hd.get("painted"):', '                    if graphics == "original" or not (hd.get("painted") or hd.get("sea",{}).get("painted")):')
    one('                        ImageDraw.Draw(safe).rectangle((224, 52, 315, 159), fill=1)', '                        if hd.get("painted"): ImageDraw.Draw(safe).rectangle((224, 52, 315, 159), fill=1)\n                        safe=ImageChops.logical_or(safe,sea_mask(hd))')
    one('                    difference = ImageChops.difference(actual, original)\n                    outside', '                    if graphics=="hd":safe=ImageChops.logical_or(safe,sea_mask(hd))\n                    difference = ImageChops.difference(actual, original)\n                    outside')
    one('                if locale == "en":', '                sea=hd.get("sea",{})\n                sea_targets={"sea-hover-near":(32,32),"sea-hover-far":(96,48),"sea-cursor-returned":(32,32)}\n                if scene in sea_targets:\n                    need((e["dos_mouse"]["x"],e["dos_mouse"]["y"])==sea_targets[scene],"海面收據沒有保留實際游標位置")\n                if graphics=="hd" and not fallback and scene in {"world","saved-world","hd-exited-again","sea-hover-near","sea-hover-far","sea-cursor-returned"}:\n                    need(sea.get("painted",0)>0,"正常世界缺海洋HD")\n                if graphics=="hd" and not fallback and scene in {"world","saved-world","hd-exited-again"}:\n                    need(sea.get("owned")==33123 and sea.get("painted")==33123,"背景還原後海洋來源不完整")\n                if graphics=="hd" and scene in {"colony","hd-reentered-colony","hd-building-hover","hd-encyclopedia-closed","hd-building-encyclopedia"}:\n                    need(sea.get("painted",0)==0,"城內仍有海洋HD")\n                if locale == "en":')
    s = s.replace('"world", "saved-world", "hd-exited-again"', '"world", "saved-world", "hd-exited-again", "sea-hover-near", "sea-hover-far", "sea-cursor-returned"')
    one('            switch_round("world")', '            switch_round("world")\n            for scene,x,y in [("sea-hover-near",32,32),("sea-hover-far",96,48),("sea-cursor-returned",32,32)]:\n                switch_round(scene)')
    one('                if scene == "hd-building-hover":', '                sea_targets={"sea-hover-near":(32,32),"sea-hover-far":(96,48),"sea-cursor-returned":(32,32)}\n                if scene in sea_targets:\n                    hover_start=status()["step"]\n                    x,y=sea_targets[scene]\n                    move(x*4,y*4+48)\n                    wait(lambda state:state.get("step",0)>=hover_start+2000000,"海面正常游標移動未完成")\n                if scene == "hd-building-hover":')
    one('        def switch_round(scene):', '        map_recoveries=[]\n        def switch_round(scene):')
    one('                record = live(s)', '                map_fallback=False\n                record = live(s)')
    one('                        need(len(maps) == 1 and maps[0].get("source") == "Jamestown" and\n                             "Jamestown" in maps[0].get("text", "") and maps[0].get("font_px") == expected,\n                             "正常世界或返回世界缺少完整地區字型城名")', '                        map_fallback=(not maps and (graphics=="original" or fallback) and\n                                      record.get("string_misses",{}).get("map-source-or-occlusion-changed\\tJamestown",0)>0)\n                        if map_fallback:\n                            if graphics=="original":\n                                rect=(136*4,118*4,203*4,130*4)\n                                need(actual.crop(rect).tobytes()==original.crop(rect).tobytes(),"失配城名未完整回原圖")\n                        else:\n                            need(len(maps) == 1 and maps[0].get("source") == "Jamestown" and\n                                 "Jamestown" in maps[0].get("text", "") and maps[0].get("font_px") == expected,\n                                 "正常世界或返回世界缺少完整地區字型城名")')
    one('                event_actions = same_state(first, step)', '                event_actions = same_state(first, step)\n                if map_fallback:\n                    recovered=wait(lambda state:any(i.get("native_surface")=="map" and i.get("source")=="Jamestown" and\n                                       i.get("font_px")==expected for i in live(state).get("items",[])),"原版來源完成後城名未恢復")\n                    need(recovered["display"]["current"]=={"language":locale,"graphics":graphics},"恢復時顯示設定不同")\n                    map_recoveries.append({"scene":scene,"locale":locale,"graphics":graphics,"fallback_step":step,\n                                           "recovered_step":recovered["step"],"reason":"map-source-or-occlusion-changed"})')
    one('        result["verified_cursor_points"] = cursor_points', '        result["map_source_recoveries"]=map_recoveries\n        result["verified_cursor_points"] = cursor_points')
    one('if c["graphics"] != "hd" or not c["native_live"].get("hd", {}).get("painted"):', 'if c["graphics"] != "hd" or not (c["native_live"].get("hd", {}).get("painted") or c["native_live"].get("hd", {}).get("sea",{}).get("painted")):')
    one('"result": "PASS_FORMAL_HD_FIVE_LANGUAGE_GUI"', '"result": "PASS_SEA_PROTOTYPE_FIVE_LANGUAGE_GUI"')
    one('result["formal_entry"] =', 'result["prototype_entry"] =')
    one('"prototype_flags": False', '"prototype_flags": True')
    one('result["limitations"] = ["正式入口、單座HD與本次正常路徑；其他素材、動畫及完整五語仍未完成。"]', 'result["limitations"] = ["規格062 DRAFT海洋原型，正式入口副本；完整動畫、其他地形、即時效能及本輪重播尚未驗收。"]')
    one('"hd_asset": sha(args.hd_asset.read_bytes())', '"hd_asset": sha(args.hd_asset.read_bytes()),"sea_asset":sha(args.sea_asset.read_bytes())')
    one('        final_live = live(status())', '        for scene in ["world","sea-hover-near","sea-hover-far","sea-cursor-returned","saved-world","hd-exited-again"]:\n            covered={c["locale"] for c in checks if c["graphics"]=="hd" and c["scene"]==scene and c["native_live"].get("hd",{}).get("sea",{}).get("painted",0)>0}\n            need(covered==set(LOCALES),"五語海洋正向不完整："+scene+str(covered))\n        final_live = live(status())')
    for obj in ['live(s)', 'live(state)']:
        for tail in ['.get("items", [])', '.get("items",[])']:
            s = s.replace(obj + tail, '(' + obj + '.get("items") or [])')
    if formal:
        one('    command += ["--hd-sea-prototype-asset",str(args.sea_asset)]\n', '')
        one('27deaccd2785a85d5ba45c462ee7ca47d160ec48683b291b379573fded5f9674', '2c5d3edc8d38e44dc02d7ccb88e79e4f749edd8a0b1d3dfd54ec04b467ba61ff')
        one('sea.get("prototype") is True', 'sea.get("formal") is True')
        one('result["prototype_entry"] =', 'result["formal_entry"] =')
        one('"prototype_flags": True', '"prototype_flags": False')
        one('PASS_SEA_PROTOTYPE_FIVE_LANGUAGE_GUI', 'PASS_FORMAL_HD_FIVE_LANGUAGE_GUI')
        one('DRAFT海洋需要隔離啟動器副本', '正式海洋需要正式啟動器')
        one('海洋候選不同', '正式海洋素材不同')
        a = '    need(sha(args.sea_asset.read_bytes())'
        one(a, '    need(args.sea_asset.resolve()==(args.formal_launcher.parent/"graphics/sea-148.png").resolve(),"正式海洋素材路徑不同")\n' + a)
        one('規格062 DRAFT海洋原型，正式入口副本；完整動畫、其他地形、即時效能及本輪重播尚未驗收。', '正式首座建築與第148幀海洋；其他素材、動畫及完整五語未完成，本輪重播另驗。')
    return s
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='規格062歷史DRAFT海洋GUI；正式共用檢查由正式產生器引用。')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    dest = args.output.resolve()
    assert Path('/.dockerenv').is_file() and os.getuid() != 0
    assert dest.is_relative_to(Path('/out')) or dest.is_relative_to(repo / 'workplace')
    assert dest.parent.is_dir() and dest.parent.stat().st_uid == os.getuid() and (not dest.exists())
    source = dest.with_name(dest.name + '.base.py')
    assert not source.exists()
    subprocess.run(['python3', str(repo / 'tools/build_hd_runtime_gui_probe.py'), '--formal', '--building-only', '--output', str(source)], check=True, timeout=30)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == 'e20481882eafa24066c56f2c68533ba84b90b73b6ed05d89cfb2cb1bd100184f'
    s = extend_sea_checks(source.read_text())
    compile(s, str(dest), 'exec')
    dest.write_text(s)
    print('PASS_SEA_GUI_PROBE_BUILD', hashlib.sha256(dest.read_bytes()).hexdigest(), flush=True)
