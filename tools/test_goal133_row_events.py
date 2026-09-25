#!/usr/bin/env python3
"""對目標133九欄事件驗證器做雙冷啟動、讀字、改色、底圖與位址的篡改負例。"""

import argparse
import copy
import json
from pathlib import Path
import tempfile

from check_goal133_row_events import analyze, verify


def must_reject(name, action):
    try:
        action()
    except (ValueError, IndexError):
        print(name, "PASS：拒絕篡改")
        return
    raise AssertionError(f"{name}：錯誤收據未被拒絕")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--name", default="toggle")
    args = p.parse_args()
    good = analyze(args.reports, args.game, args.name)
    verify(copy.deepcopy(good))

    def tampered(edit):
        bad = copy.deepcopy(good)
        edit(bad)
        return lambda: verify(bad)

    groups = lambda r: [item for item in r["prints"] if item["read_count"] == 268]

    def text(r):
        item = groups(r)[0]
        item["text"] = item["text"].replace("Autosave", "Autosavf")
    must_reject("讀字內容", tampered(text))

    def prefix(r):
        item = groups(r)[0]
        item["text"] = "X" + item["text"][1:]
    must_reject("核取前綴", tampered(prefix))

    def writes(r):
        groups(r)[-1]["write_rows"]["4"] -= 1
    must_reject("逐列改色點數", tampered(writes))

    def address(r):
        groups(r)[0]["read_linear"] = [0x2AC78, 0x2AC79]
    must_reject("印字緩衝位址", tampered(address))

    def background(r):
        entry = next(e for e in r["reprint_backgrounds"] if not e.get("skipped"))
        entry["rows"][1]["pre_sha256"] = entry["rows"][0]["pre_sha256"]
    must_reject("奇偶列底圖", tampered(background))

    with tempfile.TemporaryDirectory(prefix="goal133-rows-") as temp:
        temp = Path(temp)
        for path in args.reports.glob(f"{args.name}-*"):
            if path.suffix == ".json" or path.name.endswith(".row-events.json"):
                (temp / path.name).symlink_to(path.resolve())
        target = temp / f"{args.name}-b.row-events.json"
        data = json.loads(target.read_text())
        data["events"][0]["v"] ^= 1
        target.unlink()
        target.write_text(json.dumps(data))
        must_reject("雙冷啟動不一致", lambda: analyze(temp, args.game, args.name))
    print("goal133-rows：六項篡改負例 PASS")


if __name__ == "__main__":
    main()
