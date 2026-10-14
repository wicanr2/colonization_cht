"""規格064 R42 DRAFT：九來源正常GUI實際輸入的四側完整重播。"""
import argparse,hashlib,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];dest=a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(repo/"workplace")
assert dest.parent.stat().st_uid==os.getuid() and not dest.exists()
base=dest.with_name(dest.name+".base.py");assert not base.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_building024_replay_probe.py"),"--formal","--output",str(base)],check=True,timeout=45)
assert hashlib.sha256(base.read_bytes()).hexdigest()=="a9436fd6fd8c06fc529fcbe27dc801cdbaf252c0dde65d43f73f6563c7bb83fc"
s=base.read_text()
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old));s=s.replace(old,new,1)
one("    args = parser.parse_args()", '    parser.add_argument("--nine-assets",type=Path,required=True)\n    args = parser.parse_args()')
one('ROOT = Path("/repo")','from check_hd_building_nine_display import read_native_state\nfrom check_hd_building_nine_lifecycle import sha_file\n\nROOT = Path("/repo")')
one('baseline = json.loads((args.gui / "gui.json").read_bytes())["state"]','baseline = read_native_state(args.gui / "gui.json")')
one('"transaction_checker": sha((ROOT / "tools/check_language_observation_replay.py").read_bytes())', '"transaction_checker": sha((ROOT / "tools/check_language_observation_replay.py").read_bytes()),"native_gui_report":sha_file(args.gui/"gui.json"),"native_state_reader":sha_file(ROOT/"tools/check_hd_building_nine_display.py"),"file_hasher":sha_file(ROOT/"tools/check_hd_building_nine_lifecycle.py")')
one("    expected = [(s, l, g)",'    scenes += ["nine-start","hd-building-hover-return"]+["nine-return-%03d"%n for n in [16,21,27,35,39,42,43,44,45]]\n    expected = [(s, l, g)')
one("PASS_FORMAL_SHELTER_HD_FIVE_LANGUAGE_GUI","PASS_NINE_PROTOTYPE_FIVE_LANGUAGE_GUI")
one('    require(sha(args.binary.read_bytes())','    require({p.name:sha(p.read_bytes()) for p in sorted(args.nine_assets.glob("building-*-candidate-v1.png"))}==gui["source_sha256"]["nine_assets"],"九來源素材不同")\n    require(sha(args.binary.read_bytes())')
one('gui.get("formal_entry", {})','gui.get("prototype_entry", {})')
one('gui["formal_entry"].get("prototype_flags") is False','gui["prototype_entry"].get("prototype_flags") is True')
one('        if name == "live":\n            command.extend','        if name == "live":\n            command.extend(["--hd-nine-prototype-assets",str(args.nine_assets)])\n        if name == "live":\n            command.extend')
one("PASS_FORMAL_SHELTER_HD_GUI_FOUR_REPLAYS","PASS_NINE_PROTOTYPE_GUI_FOUR_REPLAYS")
one('result["formal_entry"] =','result["prototype_entry"] =')
one('"prototype_flags": False','"prototype_flags": True')
one("正式首座、海洋、人物及第024幀木棚；限本次正常GUI輸入，其他建築、動畫及完整HD未完成。","九來源DRAFT及既有四種正式HD；限本批實際GUI輸入，不授予正式接線或完整HD信用。")
compile(s,str(dest),"exec");dest.write_text(s)
print("PASS_NINE_REPLAY_PROBE_BUILD",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
