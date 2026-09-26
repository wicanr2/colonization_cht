#!/usr/bin/env python3
"""目標153（Issue #26）：版本不符 fail-closed 與新前端下靜態重播不變；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

CORE = ("OPENING.EXE", "VICEROY.EXE", "GAME.TXT", "LABELS.TXT", "NAMES.TXT")
PREFIX = "OPENCRD1.SS:role:"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def checkpoints(report):
    return {c["label"]: c for c in report["checkpoints"] if c.get("label", "").startswith("cp-")}


def statics(cp):
    return {l["candidate_id"]: (l["applied"], l["reason"]) for l in cp["lines"] if l["candidate_id"].startswith(PREFIX)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱版本守門通過")
        return 77
    r, old = a.reports / "goal153-slice", a.reports / "goal151-static"
    versions = {}
    for name in CORE:
        v = json.loads((r / f"version-{name}.json").read_text())
        need(v["result"] == "PASS" and v["exit_code"] == 2 and not v["output_files"], f"{name}：未拒絕啟動")
        versions[name] = "rejected"
    run = json.loads((r / "wrong-image-run.json").read_text())
    cp = checkpoints(run)["cp-1000000"]
    lines = statics(cp)
    need(len(lines) == 7 and all(v == (False, "image-version-mismatch") for v in lines.values()), "改動圖檔後靜態覆蓋未回原文")
    need(not any(e.get("candidate_id", "").startswith(PREFIX) for e in run["events"]) and
         all(statics(f) == lines for f in run["frames"]), "改動圖檔後仍有啟用事件或原因改變")
    same = {}
    for mode in ("zh", "control"):
        x, y = json.loads((old / f"replay/{mode}.json").read_text()), json.loads((r / f"static/replay/{mode}.json").read_text())
        need(x["state"] == y["state"], f"{mode}：終點原版狀態不同")
        cx, cy = checkpoints(x), checkpoints(y)
        need(cx.keys() == cy.keys(), f"{mode}：檢查點不同")
        for label in cx:
            need(cx[label]["memory_sha256"] == cy[label]["memory_sha256"] and cx[label]["raw_sha256"] == cy[label]["raw_sha256"] and
                 statics(cx[label]) == statics(cy[label]), f"{mode} {label}：狀態或套用不同")
            need((old / f"replay/{mode}.{label}.png").read_bytes() == (r / f"static/replay/{mode}.{label}.png").read_bytes(),
                 f"{mode} {label}：輸出畫面不同")
        same[mode] = len(cx)
    reg = subprocess.run([sys.executable, str(Path(__file__).with_name("check_regression.py")), "--game", str(a.game),
                          "--baseline", str(a.reports / "goal138-retire"), "--candidate", str(r)], capture_output=True)
    need(reg.returncode == 0, "全面回歸不同")
    print(json.dumps({"result": "PASS", "core_versions": versions, "wrong_image": "image-version-mismatch",
                      "wrong_image_frames": len(run["frames"]),
                      "static_replay_checkpoints_identical": same, "regression": json.loads(reg.stdout)["result"]},
                     ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
