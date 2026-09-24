#!/usr/bin/env python3
"""第122目標正反例；竄改只在容器暫存目錄，絕不改原版收據。"""

import argparse
import base64
import hashlib
import json
import tempfile
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA
from check_goal116_options_phases import check as check116
from check_goal122_options_field_guard import (
    PREVIEW_SHA, check, classify, load_preview, preview_payload, read_frame,
)


def reject(name, action):
    try:
        result = action()
    except (OSError, ValueError, KeyError, IndexError, TypeError):
        print("PASS", name)
        return
    raise AssertionError(f"{name} 應拒絕，卻回傳 {result}")


def statuses(matrix, key):
    return {name: value["status"] for name, value in matrix[key]["fields"].items()}


def same_statuses(matrix, key, expected):
    actual = statuses(matrix, key)
    for field, status in expected.items():
        assert actual[field] == status, (key, field, actual[field], status)


def linked_report_dir(source, target):
    target.mkdir()
    for file in source.iterdir():
        if file.is_file():
            (target / file.name).symlink_to(file)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports-root", type=Path, required=True)
    args = parser.parse_args()
    root = args.reports_root
    result = check(args.game, args.inputs, args.fixtures, root)
    assert result["result"] == "PASS"
    matrix = result["matrix"]
    for branch in ("hover-first", "hover-last"):
        same_statuses(matrix, f"goal116-options/{branch}/1375m",
                      {f"option-{i:02d}": "safe-at-sample" for i in range(9)})
    same_statuses(matrix, "goal116-options/hover-first/1325m",
                  {"option-01": "cursor-occluded", "option-02": "cursor-occluded"})
    same_statuses(matrix, "goal116-options/hover-last/1325m",
                  {"option-08": "cursor-occluded"})
    same_statuses(matrix, "goal118-options/second/1325m",
                  {"option-01": "background-changed", "option-02": "background-changed",
                   "option-03": "cursor-occluded", "option-00": "safe-at-sample"})
    same_statuses(matrix, "goal119-options/eighth/1325m",
                  {"option-01": "background-changed", "option-08": "background-changed",
                   "option-07": "safe-at-sample"})
    for label in ("1375m", "1400m"):
        same_statuses(matrix, f"goal116-options/exit/{label}",
                      {f"option-{i:02d}": "window-exited" for i in range(9)})
    for branch in ("first", "eighth"):
        for phase in range(12):
            same_statuses(matrix, f"goal119-options/{branch}/phase-{phase:02d}",
                          {f"option-{i:02d}": "unknown-transition" for i in range(9)})
    assert result["preview_candidates"]["second-1325m"]["fallback_original"] == [
        "option-01", "option-02", "option-03"]
    assert result["preview_candidates"]["eighth-1325m"]["fallback_original"] == [
        "option-01", "option-08"]
    print("PASS 固定畫面逐欄、游標、離頁及細相位未知分類")

    base = bytes(64000)
    cursor = bytearray(base)
    cursor[60 * 320 + 80] = 1
    altered = bytearray(base)
    altered[60 * 320 + 80] = 2
    safe = [80, 59, 252, 71]
    assert classify(base, base, cursor, safe)["status"] == "cursor-occluded"
    assert classify(base, altered, altered, safe)["status"] == "background-changed"
    assert classify(base, base, base, safe, exiting=True)["status"] == "window-exited"
    assert classify(base, base, base, safe, transitional=True)["status"] == "unknown-transition"
    print("PASS 游標／變動底圖／離頁／未知細相位失敗即回退")

    with tempfile.TemporaryDirectory(prefix="colonization-goal122-") as temp:
        tmp = Path(temp)
        assert check(tmp / "missing-game", args.inputs, args.fixtures, root)["result"] == "SKIP"
        print("PASS 缺合法原版 SKIP 77")
        game = tmp / "wrong-game"
        game.mkdir()
        for name in (*FILE_SHA, "MENU.TXT"):
            if name == "GAME.TXT":
                data = (args.game / name).read_bytes()
                (game / name).write_bytes(data[:-1] + bytes((data[-1] ^ 1,)))
            else:
                (game / name).symlink_to(args.game / name)
        reject("錯版原版來源", lambda: check(game, args.inputs, args.fixtures, root))

        wrong_input = tmp / "wrong-input.json"
        wrong_input.write_bytes(args.inputs.read_bytes() + b" ")
        reject("錯玩家輸入", lambda: check(args.game, wrong_input, args.fixtures, root))

        reports = tmp / "goal116-options"
        linked_report_dir(root / "goal116-options", reports)
        filename = "hover-first-a.1325m.canvas"
        (reports / filename).unlink()
        damaged = bytearray((root / "goal116-options" / filename).read_bytes())
        damaged[60 * 320 + 100] ^= 1
        (reports / filename).write_bytes(damaged)
        reject("壞原版畫面", lambda: read_frame(reports, "hover-first-a", "1325m"))
        (reports / filename).unlink()
        (reports / filename).symlink_to(root / "goal116-options" / filename)

        b_name = "hover-first-b.json"
        (reports / b_name).unlink()
        (reports / b_name).write_bytes((root / "goal116-options" / b_name).read_bytes() + b" ")
        reject("雙冷啟動分歧", lambda: check116(args.game, args.inputs, args.fixtures,
                                              reports, root / "goal111-help"))
        (reports / b_name).unlink()
        (reports / b_name).symlink_to(root / "goal116-options" / b_name)

        c_name = "hover-first-control.json"
        (reports / c_name).unlink()
        control = json.loads((root / "goal116-options" / c_name).read_bytes())
        control["samples"]["1325m"]["memory_sha256"] = "0" * 64
        (reports / c_name).write_text(json.dumps(control) + "\n", encoding="utf-8")
        reject("無監看控制分歧", lambda: check116(args.game, args.inputs, args.fixtures,
                                                  reports, root / "goal111-help"))

        preview_path = root / "goal113-options" / "options-faithful.json"
        preview = tmp / "options-faithful.json"
        preview.write_bytes(preview_path.read_bytes() + b" ")
        reject("預覽來源版本分歧", lambda: load_preview(
            tmp, "faithful", bytes(64000), bytes(768), "0" * 64))
        altered_preview = json.loads(preview_path.read_bytes())
        altered_preview["layers"][1]["safe"][0] += 1
        preview.write_text(json.dumps(altered_preview, ensure_ascii=False) + "\n",
                           encoding="utf-8")
        original_sha = PREVIEW_SHA["faithful"]
        PREVIEW_SHA["faithful"] = hashlib.sha256(preview.read_bytes()).hexdigest()
        try:
            source = json.loads(preview_path.read_bytes())
            reject("錯安全矩形", lambda: load_preview(
                tmp, "faithful", base64.b64decode(source["indexed"]),
                base64.b64decode(source["palette"]), source["source_receipt_sha256"]))
        finally:
            PREVIEW_SHA["faithful"] = original_sha

        fields = {f"option-{i:02d}": {"status": "safe-at-sample"} for i in range(9)}
        fields["option-01"]["status"] = "cursor-occluded"
        payload = preview_payload(json.loads(preview_path.read_bytes()),
                                  {"idx": bytes(64000), "pal": bytes(768)},
                                  "test", fields)
        assert "option-01" not in [layer["name"] for layer in payload["layers"]]
        fields["option-00"]["status"] = "background-changed"
        payload = preview_payload(json.loads(preview_path.read_bytes()),
                                  {"idx": bytes(64000), "pal": bytes(768)},
                                  "test", fields)
        assert "option-00" not in [layer["name"] for layer in payload["layers"]]
        print("PASS 預覽安全矩形／游標／變動底圖逐欄拒絕")


if __name__ == "__main__":
    main()
