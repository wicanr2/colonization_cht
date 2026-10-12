"""規格062 DRAFT：以實際GUI終點設定重播四側原版狀態。"""
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
base=dest.with_name(dest.name+".base.py")
assert not base.exists()
subprocess.run(["python3",str(repo/"tools/build_hd_runtime_replay_probe.py"),"--formal","--output",str(base)],check=True,timeout=30)
assert hashlib.sha256(base.read_bytes()).hexdigest()=="67636e42cb769c6bf1ea3766458db543ef076c4bf433339ba8a2511630dd9404"
s=base.read_text()
pairs=[
('parser.add_argument("--hd-asset", type=Path, required=True)','parser.add_argument("--hd-asset", type=Path, required=True)\n    parser.add_argument("--sea-asset", type=Path, required=True)'),
('    expected = [(s, l, g)', '    scenes += ["sea-hover-near", "sea-hover-far", "sea-cursor-returned"]\n    expected = [(s, l, g)'),
('PASS_FORMAL_HD_FIVE_LANGUAGE_GUI','PASS_SEA_PROTOTYPE_FIVE_LANGUAGE_GUI'),
('    require(sha(args.binary.read_bytes())', '    require(sha(args.sea_asset.read_bytes()) == gui["source_sha256"]["sea_asset"], "海洋候選不同")\n    require(sha(args.binary.read_bytes())'),
('gui.get("formal_entry", {})','gui.get("prototype_entry", {})'),
('gui["formal_entry"].get("prototype_flags") is False','gui["prototype_entry"].get("prototype_flags") is True'),
('"--native-text-diagnostics", "--display-language", "en", "--display-graphics", "hd"]','"--native-text-diagnostics", "--display-language", "en", "--display-graphics", "hd",\n                       "--hd-sea-prototype-asset", str(args.sea_asset)]'),
('"--native-text-diagnostics", "--display-language", "en", "--display-graphics", "hd",', '"--native-text-diagnostics", "--display-language", "en", "--display-graphics", gui["checks"][-1]["graphics"],'),
('    baseline = json.loads', '    require(gui["checks"][-1]["locale"] == "en" and gui["checks"][-1]["graphics"] == "original", "終點顯示設定不同")\n    baseline = json.loads'),
('PASS_FORMAL_HD_GUI_FOUR_REPLAYS','PASS_SEA_PROTOTYPE_GUI_FOUR_REPLAYS'),
('result["formal_entry"] = {"launcher_sha256": sha(args.formal_launcher.read_bytes()), "prototype_flags": False}','result["prototype_entry"] = {"launcher_sha256": sha(args.formal_launcher.read_bytes()), "prototype_flags": True}'),
('result["limitations"] = ["正式入口、單座HD及本次正常路徑；其他素材、動畫與完整五語仍未完成。"]','result["limitations"] = ["規格062 DRAFT海洋候選與正式首座建築；限本次正常GUI輸入，未宣稱完整HD或五語完成。"]'),
]
for a,b in pairs:
    assert s.count(a)==1,(a,s.count(a))
    s=s.replace(a,b,1)
compile(s,str(dest),"exec")
dest.write_text(s)
print("PASS_SEA_REPLAY_PROBE_BUILD",hashlib.sha256(dest.read_bytes()).hexdigest(),flush=True)
