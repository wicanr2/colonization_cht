"""規格064 R44 DRAFT：中央原型正常GUI實際輸入的四側重播。"""
import argparse,hashlib,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
p.add_argument('--formal',action='store_true',help='規格064 R44 READY：重播正式第009幀，不加原型旗標')
a=p.parse_args();repo=Path(__file__).resolve().parents[1];dest=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0
assert dest.is_relative_to('/out') and dest.parent.stat().st_uid==os.getuid() and not dest.exists()
base=dest.with_name(dest.name+'.base.py');assert not base.exists()
subprocess.run(['python3',str(repo/'tools/build_hd_building_nine_replay_probe.py'),'--formal','--output',str(base)],check=True,timeout=60)
s=base.read_text()
def one(old,new):
    global s
    assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
one('    args = parser.parse_args()','    parser.add_argument("--center-asset",type=Path,required=True)\n    args = parser.parse_args()')
one('    expected = [(s, l, g)','    scenes += ["center-start","center-return"]\n    expected = [(s, l, g)')
one('    require(sha(args.binary.read_bytes())','    require(sha(args.center_asset.read_bytes())==gui["source_sha256"]["center_asset"],"中央素材不同")\n    require(sha(args.binary.read_bytes())')
s=s.replace('formal_entry','prototype_entry').replace('"prototype_flags") is False','"prototype_flags") is True').replace('"prototype_flags": False','"prototype_flags": True')
one('        if name == "live":\n            command.extend(["--display-config", str(run / "display.json")])','        if name == "live":\n            command.extend(["--hd-center-prototype-assets",str(args.center_asset.parent)])\n            command.extend(["--display-config", str(run / "display.json")])')
s=s.replace('PASS_FORMAL_NINE_FIVE_LANGUAGE_GUI','PASS_CENTER_PROTOTYPE_FIVE_LANGUAGE_GUI').replace('PASS_FORMAL_NINE_GUI_FOUR_REPLAYS','PASS_CENTER_PROTOTYPE_GUI_FOUR_REPLAYS')
s=s.replace('正式十三種HD素材；限本批實際GUI輸入，其他來源、動畫與完整HD未完成。','中央DRAFT及正式十三種素材；限本批實際輸入，不授予中央正式接線或完整HD信用。')
if a.formal:
    one('            command.extend(["--hd-center-prototype-assets",str(args.center_asset.parent)])\n','')
    s=s.replace('prototype_entry','formal_entry').replace('"prototype_flags") is True','"prototype_flags") is False').replace('"prototype_flags": True','"prototype_flags": False')
    s=s.replace('PASS_CENTER_PROTOTYPE_FIVE_LANGUAGE_GUI','PASS_FORMAL_CENTER_FIVE_LANGUAGE_GUI').replace('PASS_CENTER_PROTOTYPE_GUI_FOUR_REPLAYS','PASS_FORMAL_CENTER_GUI_FOUR_REPLAYS')
    s=s.replace('中央DRAFT及正式十三種素材；限本批實際輸入，不授予中央正式接線或完整HD信用。','正式十四種素材；限本批實際輸入，其他來源、動畫及完整HD未完成。')
    assert '--hd-center-' not in s
compile(s,str(dest),'exec');dest.write_text(s)
print('PASS_CENTER_REPLAY_PROBE_BUILD',hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
