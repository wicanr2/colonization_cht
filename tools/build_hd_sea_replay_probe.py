import argparse, hashlib, os, subprocess
from pathlib import Path

def extend_sea_replay_checks(s, formal=False):

    def one(old, new):
        nonlocal s
        assert s.count(old) == 1, (old, s.count(old))
        s = s.replace(old, new, 1)
    pairs = [('parser.add_argument("--hd-asset", type=Path, required=True)', 'parser.add_argument("--hd-asset", type=Path, required=True)\n    parser.add_argument("--sea-asset", type=Path, required=True)'), ('    expected = [(s, l, g)', '    scenes += ["sea-hover-near", "sea-hover-far", "sea-cursor-returned"]\n    expected = [(s, l, g)'), ('PASS_FORMAL_HD_FIVE_LANGUAGE_GUI', 'PASS_SEA_PROTOTYPE_FIVE_LANGUAGE_GUI'), ('    require(sha(args.binary.read_bytes())', '    require(sha(args.sea_asset.read_bytes()) == gui["source_sha256"]["sea_asset"], "海洋候選不同")\n    require(sha(args.binary.read_bytes())'), ('gui.get("formal_entry", {})', 'gui.get("prototype_entry", {})'), ('gui["formal_entry"].get("prototype_flags") is False', 'gui["prototype_entry"].get("prototype_flags") is True'), ('"--native-text-diagnostics", "--display-language", "en", "--display-graphics", "hd"]', '"--native-text-diagnostics", "--display-language", "en", "--display-graphics", "hd",\n                       "--hd-sea-prototype-asset", str(args.sea_asset)]'), ('"--native-text-diagnostics", "--display-language", "en", "--display-graphics", "hd",', '"--native-text-diagnostics", "--display-language", "en", "--display-graphics", gui["checks"][-1]["graphics"],'), ('    baseline = json.loads', '    require(gui["checks"][-1]["locale"] == "en" and gui["checks"][-1]["graphics"] == "original", "終點顯示設定不同")\n    baseline = json.loads'), ('PASS_FORMAL_HD_GUI_FOUR_REPLAYS', 'PASS_SEA_PROTOTYPE_GUI_FOUR_REPLAYS'), ('result["formal_entry"] = {"launcher_sha256": sha(args.formal_launcher.read_bytes()), "prototype_flags": False}', 'result["prototype_entry"] = {"launcher_sha256": sha(args.formal_launcher.read_bytes()), "prototype_flags": True}'), ('result["limitations"] = ["正式入口、單座HD及本次正常路徑；其他素材、動畫與完整五語仍未完成。"]', 'result["limitations"] = ["規格062 DRAFT海洋候選與正式首座建築；限本次正常GUI輸入，未宣稱完整HD或五語完成。"]')]
    for a, b in pairs:
        assert s.count(a) == 1, (a, s.count(a))
        s = s.replace(a, b, 1)
    if formal:
        one('gui.get("prototype_entry", {})', 'gui.get("formal_entry", {})')
        one('gui["prototype_entry"].get("prototype_flags") is True', 'gui["formal_entry"].get("prototype_flags") is False')
        one('result["prototype_entry"] =', 'result["formal_entry"] =')
        one('"prototype_flags": True', '"prototype_flags": False')
        one(',\n                       "--hd-sea-prototype-asset", str(args.sea_asset)]', ']')
        one('PASS_SEA_PROTOTYPE_FIVE_LANGUAGE_GUI', 'PASS_FORMAL_HD_FIVE_LANGUAGE_GUI')
        one('PASS_SEA_PROTOTYPE_GUI_FOUR_REPLAYS', 'PASS_FORMAL_HD_GUI_FOUR_REPLAYS')
        one('規格062 DRAFT海洋候選與正式首座建築；限本次正常GUI輸入，未宣稱完整HD或五語完成。', '正式首座建築與第148幀海洋；限本次正常GUI輸入，其他素材、動畫及完整五語未完成。')
    if formal:
        one(',\n                                                              "--hd-prototype-asset", str(args.hd_asset)]),', ']),')
    return s
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='規格062歷史DRAFT海洋重播；正式共用檢查由正式產生器引用。')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[1]
    dest = args.output.resolve()
    assert Path('/.dockerenv').is_file() and os.getuid() != 0
    assert dest.is_relative_to(Path('/out')) or dest.is_relative_to(repo / 'workplace')
    assert dest.parent.is_dir() and dest.parent.stat().st_uid == os.getuid() and (not dest.exists())
    base = dest.with_name(dest.name + '.base.py')
    assert not base.exists()
    subprocess.run(['python3', str(repo / 'tools/build_hd_runtime_replay_probe.py'), '--formal', '--building-only', '--output', str(base)], check=True, timeout=30)
    assert hashlib.sha256(base.read_bytes()).hexdigest() == '67636e42cb769c6bf1ea3766458db543ef076c4bf433339ba8a2511630dd9404'
    s = extend_sea_replay_checks(base.read_text())
    compile(s, str(dest), 'exec')
    dest.write_text(s)
    print('PASS_SEA_REPLAY_PROBE_BUILD', hashlib.sha256(dest.read_bytes()).hexdigest(), flush=True)
