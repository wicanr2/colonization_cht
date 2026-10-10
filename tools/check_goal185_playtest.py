#!/usr/bin/env python3
"""在 Docker 內核對目標185的本機玩家收據；遊玩阻塞仍回 FAIL。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

from PIL import Image


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def rgba(path):
    with Image.open(path) as image:
        return image.size, image.convert("RGBA").tobytes()


def review(reports, game):
    original = load(reports / "existing-control-aligned/run.json")
    translated = load(reports / "existing-zh-aligned/run.json")
    fallback = load(reports / "existing-missing-aligned/run.json")
    for name, want in original["input_hashes"].items():
        assert digest(game / name) == want, f"原版版本不符：{name}"
    sides = [original, translated, fallback]
    assert all(side["state"] == original["state"] for side in sides)
    assert load(reports / "existing/gui.json")["state"] == original["state"]
    maps = [{row["label"]: row for row in side["checkpoints"]} for side in sides]
    assert all(set(mapping) == set(maps[0]) for mapping in maps)
    points = []
    for line in (reports / "existing/gui.shots").read_text().splitlines():
        name, step = line.split()
        label = "cp-" + step
        rows = [mapping[label] for mapping in maps]
        for key in ("step", "memory_sha256", "raw_sha256", "palette_sha256"):
            assert all(row[key] == rows[0][key] for row in rows), f"原版差異：{name}/{key}"
        assert rows[0]["step"] == int(step), f"畫面步數不符：{name}"
        translated_png = reports / "existing-zh-aligned" / f"run.{label}.png"
        assert rgba(reports / "existing" / f"gui.{name}.png") == rgba(translated_png), name
        assert rgba(reports / "existing-control-aligned" / f"run.{label}.png") == rgba(
            reports / "existing-missing-aligned" / f"run.{label}.png"
        ), f"回退畫面不符：{name}"
        points.append({"name": name, "step": int(step), "result": "PASS"})
    assert len(points) == 15, "正常操作收據不完整"
    for filename in ("COLONY00.SAV", "COLONY03.SAV"):
        paths = [reports / side / "save" / filename for side in
                 ("existing", "existing-control-aligned", "existing-zh-aligned",
                  "existing-missing-aligned", "reload", "reload-control")]
        assert len({digest(path) for path in paths}) == 1, filename
    assert digest(reports / "existing-seed/COLONY03.SAV") == digest(
        reports / "existing/save/COLONY03.SAV"
    ), "原始存檔遭改寫"
    assert len({digest(reports / side / "raw.wav") for side in
                ("existing", "existing-control-aligned", "existing-zh-aligned",
                 "existing-missing-aligned")}) == 1
    reload_gui = load(reports / "reload/gui.json")
    reload_control = load(reports / "reload-control/run.json")
    assert reload_gui["state"] == reload_control["state"], "重啟讀檔原版狀態不符"
    assert digest(reports / "reload/raw.wav") == digest(reports / "reload-control/raw.wav")
    probe = load(reports / "audio-clock-200m-run/run.json")
    audio_control = load(reports / "audio-current-control/run.json")
    assert probe["state"] == audio_control["state"], "音訊觀測改變原版狀態"
    assert digest(reports / "audio-clock-200m-run/raw.wav") == digest(
        reports / "audio-current-control/raw.wav"
    )
    clock = load(reports / "audio-clock-200m-run/raw.wav.clock.json")
    assert clock["music"]["music_underrun_bytes"] == 0
    assert clock["music"]["music_dropped_bytes"] == 0
    assert clock["music"]["commands"] > 0
    stats = load(reports / "audio-playback-stats.json")
    assert stats["nonzero_samples"] > 0
    newgame = load(reports / "newgame/gui.json")
    for side in ("newgame-control", "newgame-release", "newgame-trace-v4"):
        assert load(reports / side / "run.json")["state"] == newgame["state"], side
    exit_state = load(reports / "trace-exit-v4.json")
    blocked = exit_state["halted"] and not exit_state["exited"]
    return {
        "goal": 185,
        "overall": "FAIL" if blocked else "UNREVIEWED",
        "issues_closed": [],
        "core_operations": {"result": "PASS", "points": points,
                            "state": original["state"],
                            "save_sha256": digest(reports / "existing/save/COLONY00.SAV")},
        "restart_load": {"result": "PASS", "state": reload_gui["state"]},
        "audio_supply": {"result": "PASS", "clock": clock, "wave": stats,
                         "hardware_and_listening_verified": False},
        "newgame": {"result": "FAIL" if blocked else "UNREVIEWED",
                    "state": newgame["state"], "exit": exit_state,
                    "release_reproduces_same_state": True,
                    "root_cause": "unknown; allocation failure precedes invalid return and IVT overwrite"},
        "provenance": {"input_hashes": original["input_hashes"],
                       "core_inputs_sha256": digest(reports / "existing/gui.inputs.json"),
                       "newgame_inputs_sha256": digest(reports / "newgame/gui.inputs.json"),
                       "method": "real X11 input, published-frame captures, identical-input dosgolem replay"},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not (args.game / "VICEROY.EXE").is_file():
        print("SKIP77：缺少使用者提供的原版 DOS 輸入")
        return 77
    assert args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid()
    if args.output.exists():
        assert args.output.stat().st_uid == os.getuid()
    result = review(args.reports, args.game)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(f"{result['overall']}：核心操作與重啟讀檔 PASS，新遊戲 {result['newgame']['result']}，Issue 未關閉")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
