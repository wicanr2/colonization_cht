"""規格061 DRAFT：沿固定五語重播工具建立HD隔離原型的四側驗證。"""
import argparse
import hashlib
import os
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--output", type=Path, required=True)
a = p.parse_args()
repo = Path(__file__).resolve().parents[1]
out = a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo / "workplace")
assert out.parent.stat().st_uid == os.getuid() and not out.exists()
source = repo / "tools/check_language_live_replay.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "4c0ba813868f03ea00f35fa7c7879f36cddb9becee2442e9bbd5914d70b73d68"
s = source.read_text()
def one(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new, 1)

one("from check_language_observation_replay import", 'import sys\nsys.path.insert(0, "/repo/tools")\nfrom check_language_observation_replay import')
one("ROOT = Path(__file__).resolve().parent.parent", 'ROOT = Path("/repo")')
one("import subprocess", "import subprocess\nimport time")
one("root.is_relative_to((ROOT / \"workplace\").resolve())",
    '(root.is_relative_to((ROOT / "workplace").resolve()) or root.is_relative_to(Path("/out")))')
one("    args = parser.parse_args()", '''    parser.add_argument("--hd-asset", type=Path, required=True)
    args = parser.parse_args()
    require(not args.formal_launcher, "DRAFT HD只使用隔離入口")''')
one('    require(gui["result"] == "PASS_NATIVE_LIVE_FIVE_LANGUAGE_GUI" and\n'
    '            sorted((c["scene"], c["locale"]) for c in gui["checks"]) ==\n'
    '            sorted((s, l) for s in scenes for l in ["zh-Hant", "zh-Hans", "ja", "ko", "en"]),\n'
    '            "隔離五語GUI尚未通過")',
    '''    scenes += ["hd-reentered-colony", "hd-building-hover", "hd-building-encyclopedia", "hd-encyclopedia-closed", "hd-exited-again"]
    expected = [(s, l, g) for s in scenes for l in ["zh-Hant", "zh-Hans", "ja", "ko", "en"] for g in ["original", "hd"]]
    expected += [("hd-quit-confirmation", "en", g) for g in ["original", "hd"]]
    require(gui["result"] == "PASS_HD_RUNTIME_FIVE_LANGUAGE_GUI" and
            sorted((c["scene"], c["locale"], c["graphics"]) for c in gui["checks"]) == sorted(expected),
            "隔離五語HD正常GUI尚未通過")
    require(sha(args.hd_asset.read_bytes()) == gui["source_sha256"]["hd_asset"], "HD候選不同")''')
one('"--display-language", "zh-Hant", "--display-graphics", "original"]),',
    '"--display-language", "en", "--display-graphics", "hd",\n                                                              "--hd-prototype-asset", str(args.hd_asset)]),')
one("        env = os.environ.copy()", '        env = os.environ.copy()\n        env["GOMEMLIMIT"] = "1200MiB"')
one('        with (run / "process.log").open("wb") as log:',
    '        started = time.monotonic()\n        with (run / "process.log").open("wb") as log:')
one('        report = json.loads((run / "run.json").read_bytes())',
    '        elapsed = time.monotonic() - started\n        report = json.loads((run / "run.json").read_bytes())')
one('results[name] = {"state": report["state"], "binary_sha256": sha(binary.read_bytes()),',
    'results[name] = {"state": report["state"], "binary_sha256": sha(binary.read_bytes()), "wall_seconds": elapsed,')
one('"result": "PASS_NATIVE_LIVE_GUI_FOUR_REPLAYS"', '"result": "PASS_HD_RUNTIME_GUI_FOUR_REPLAYS"')
one('["隔離視窗及本次正常路徑；完整來源生命週期、正式接線及HD未完成。"]',
    '["規格061 DRAFT單座候選及本次正常路徑；正式素材、正式HD及完整五語仍未完成。"]')
compile(s, str(out), "exec")
out.write_text(s)
print("PASS_HD_RUNTIME_REPLAY_PROBE_BUILD", hashlib.sha256(out.read_bytes()).hexdigest())
