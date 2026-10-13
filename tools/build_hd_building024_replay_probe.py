"""規格064 DRAFT：木棚GUI實際輸入的四側完整原版狀態／音訊／存檔重播。"""
import argparse,hashlib,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument("--output",type=Path,required=True)
a=p.parse_args();repo=Path(__file__).resolve().parents[1];dest=a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(repo/"workplace")
assert dest.parent.stat().st_uid==os.getuid() and not dest.exists()
base=dest.with_name(dest.name+".base.py");assert not base.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_person_replay_probe.py"),"--formal","--output",str(base)],check=True,timeout=30)
assert hashlib.sha256(base.read_bytes()).hexdigest()=="81beab9e77b6a0953ebd2ccc988e6aaf6854d189583900ace7878b17b889b6b0"
s=base.read_text()
def one(old,new):
 global s
 assert s.count(old)==1,(old,s.count(old))
 s=s.replace(old,new,1)
one("    args = parser.parse_args()",'    parser.add_argument("--shelter-asset",type=Path,required=True)\n    args = parser.parse_args()')
one("    expected = [(s, l, g)",'    scenes += ["shelter-hover-roof","shelter-away-roof","shelter-return-roof","shelter-hover-post","shelter-away-post","shelter-return-post","shelter-drag-complete"]\n    expected = [(s, l, g)')
one("PASS_FORMAL_PERSON_HD_FIVE_LANGUAGE_GUI","PASS_SHELTER_PROTOTYPE_FIVE_LANGUAGE_GUI")
one('    require(sha(args.binary.read_bytes())','    require(sha(args.shelter_asset.read_bytes())==gui["source_sha256"]["shelter_asset"],"木棚候選不同")\n    require(sha(args.binary.read_bytes())')
one('gui.get("formal_entry", {})','gui.get("prototype_entry", {})')
one('gui["formal_entry"].get("prototype_flags") is False','gui["prototype_entry"].get("prototype_flags") is True')
one('        if name == "live":\n            command.extend','        if name == "live":\n            command.extend(["--hd-shelter-prototype-asset",str(args.shelter_asset)])\n        if name == "live":\n            command.extend')
one("PASS_FORMAL_PERSON_HD_GUI_FOUR_REPLAYS","PASS_SHELTER_PROTOTYPE_GUI_FOUR_REPLAYS")
one('result["formal_entry"] =','result["prototype_entry"] =')
one('"prototype_flags": False','"prototype_flags": True')
one("正式首座、海洋與第100幀人物；限本次正常GUI輸入，其他人物、動畫及完整HD未完成。","木棚DRAFT及現行正式三種HD來源；限本次正常GUI輸入，不授予木棚正式接線信用。")
compile(s,str(dest),"exec");dest.write_text(s)
print("PASS_SHELTER_REPLAY_PROBE_BUILD",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
