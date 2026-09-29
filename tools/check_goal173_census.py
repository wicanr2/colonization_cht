#!/usr/bin/env python3
"""目標173（Issue #45）：獨立核對全可達文字普查可重跑、與提交版本相同，並做三個反向對照；原版缺失回 SKIP 77。

- 重跑兩次輸出逐位元組相同，且等於提交的 docs/text-census.tsv 與 docs/text-census.md。
- 拿掉驗證矩陣以外的新前端重播收據時，已顯示中文的列數必須減少。
- 對照表刪掉一條樣式（使某段落無人分類）或多加一條重疊樣式時，普查必須失敗。
"""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

EXTRA = "goal17[24]-re*/replay-zh.json"


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def run(repo, game, reports, out, map_path, extra=True):
    out.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(repo / "tools/text_census.py"), "--game", str(game), "--text", str(repo / "text"),
           "--reports", str(reports), "--matrix", str(repo / "tools/verification-matrix.json"), "--map", str(map_path),
           "--census", str(out / "census.tsv"), "--report", str(out / "report.md"), "--detail", str(out / "detail.json")]
    if extra:
        cmd += ["--extra", EXTRA]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (json.loads(p.stdout.strip().splitlines()[-1]) if p.returncode == 0 else p.stderr)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--repo", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱普查通過")
        return 77
    map_path = a.repo / "text/census-map.tsv"
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        rc1, s1 = run(a.repo, a.game, a.reports, t / "a", map_path)
        rc2, s2 = run(a.repo, a.game, a.reports, t / "b", map_path)
        need(rc1 == 0 and rc2 == 0, f"普查失敗：{s1 if rc1 else s2}")
        for name in ("census.tsv", "report.md"):
            need((t / "a" / name).read_bytes() == (t / "b" / name).read_bytes(), f"重跑 {name} 不同")
        need((t / "a/census.tsv").read_bytes() == (a.repo / "docs/text-census.tsv").read_bytes(), "與提交的清冊不同")
        need((t / "a/report.md").read_bytes() == (a.repo / "docs/text-census.md").read_bytes(), "與提交的報表不同")
        need(s1["unclassified"] == 0 and s1["unused_patterns"] == 0, "有待歸類字串或未使用樣式")

        rc3, s3 = run(a.repo, a.game, a.reports, t / "c", map_path, extra=False)
        need(rc3 == 0 and s3["status"]["shown"] < s1["status"]["shown"], "拿掉新前端收據後已顯示列數沒有減少")

        lines = map_path.read_text(encoding="utf-8").splitlines(keepends=True)
        drop = next(i for i, l in enumerate(lines) if l.startswith("GAME.TXT\tTUTORIAL"))
        (t / "drop.tsv").write_text("".join(lines[:drop] + lines[drop + 1:]), encoding="utf-8")
        rc4, e4 = run(a.repo, a.game, a.reports, t / "d", t / "drop.tsv")
        need(rc4 != 0 and "0 條對照樣式" in e4, "刪掉一條樣式後普查沒有失敗")
        (t / "dup.tsv").write_text("".join(lines) + "GAME.TXT\tTUTORIAL1\t教學提示\ttutorial\tnormal\t重疊\n", encoding="utf-8")
        rc5, e5 = run(a.repo, a.game, a.reports, t / "e", t / "dup.tsv")
        need(rc5 != 0 and "2 條對照樣式" in e5, "重疊樣式後普查沒有失敗")
    print(json.dumps({"result": "PASS", "census_sha256": s1["census_sha256"], "report_sha256": s1["report_sha256"],
                      "status": s1["status"], "without_extra_shown": s3["status"]["shown"],
                      "map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest()}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
