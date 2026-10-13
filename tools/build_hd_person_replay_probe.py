"""規格063 DRAFT：重播人物GUI的同一組正常輸入，核對四側原版狀態。"""
import argparse,hashlib,os,subprocess
from pathlib import Path
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output",type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[1];dest=args.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid()!=0
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(repo/"workplace")
assert dest.parent.is_dir() and dest.parent.stat().st_uid==os.getuid() and not dest.exists()
base=dest.with_name(dest.name+".base.py")
assert not base.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_runtime_replay_probe.py"),"--formal","--output",str(base)],check=True,timeout=30)
assert hashlib.sha256(base.read_bytes()).hexdigest()=="7e4d0e5a4c4f0fc303990a49134a6f1257a05eeff0ace67584022394eff0b8a2"
s=base.read_text()
def one(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a))
 s=s.replace(a,b,1)
one('    args = parser.parse_args()','    parser.add_argument("--person-asset",type=Path,required=True)\n    args = parser.parse_args()')
one('    expected = [(s, l, g)','    scenes += ["person-hover-main","person-away-main","person-return-main","person-hover-garrison","person-away-garrison","person-return-garrison","person-drag-complete"]\n    expected = [(s, l, g)')
one('PASS_FORMAL_HD_FIVE_LANGUAGE_GUI','PASS_PERSON_PROTOTYPE_FIVE_LANGUAGE_GUI')
one('    require(sha(args.binary.read_bytes())','    require(sha(args.person_asset.read_bytes()) == gui["source_sha256"]["person_asset"], "人物原圖不同")\n    require(sha(args.binary.read_bytes())')
one('gui.get("formal_entry", {})','gui.get("prototype_entry", {})')
one('gui["formal_entry"].get("prototype_flags") is False','gui["prototype_entry"].get("prototype_flags") is True')
one('        if name == "live":\n            command.extend','        if name == "live":\n            command.extend(["--hd-person-prototype-asset",str(args.person_asset)])\n        if name == "live":\n            command.extend')
one('PASS_FORMAL_HD_GUI_FOUR_REPLAYS','PASS_PERSON_PROTOTYPE_GUI_FOUR_REPLAYS')
one('result["formal_entry"] =','result["prototype_entry"] =')
one('"prototype_flags": False','"prototype_flags": True')
one('正式首座建築與第148幀海洋；限本次正常GUI輸入，其他素材、動畫及完整五語未完成。','規格063 DRAFT人物與正式首座建築、海洋；限本次正常GUI輸入，尚未授予人物正式接線信用。')
compile(s,str(dest),"exec");dest.write_text(s)
print("PASS_PERSON_REPLAY_PROBE_BUILD",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
