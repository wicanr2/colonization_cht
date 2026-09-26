#!/usr/bin/env python3
"""目標152（Issue #14）：依 tools/verification-matrix.json 逐列跑獨立檢查器並盤點收據，產生通過／待驗報告。

只讀收據；輸出含雜湊、數量與鍵的報告（可提交的 Markdown 與完整 JSON）。原版缺失時每列記為 SKIP，整體回 77。
同一份收據重跑必須得到相同報告，因此不寫入時間或路徑以外的環境資訊。
"""

import argparse
import fnmatch
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

COLUMNS = ("baseline", "zh", "control", "negative")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_head(repo):
    head = (repo / ".git/HEAD").read_text().strip()
    if not head.startswith("ref: "):
        return head
    ref = head[5:]
    loose = repo / ".git" / ref
    if loose.is_file():
        return loose.read_text().strip()
    for line in (repo / ".git/packed-refs").read_text().splitlines():
        if line.endswith(" " + ref):
            return line.split()[0]
    raise ValueError("無法解析 dosgolem 版本")


def receipts(base, patterns):
    """回傳符合樣式的收據前綴（不含 .json）。"""
    # 重播收據一定有完整 RAM（.memory）；字模、輸入、摘要等 JSON 不算。
    names = sorted(str(p.relative_to(base))[:-5] for p in base.rglob("*.json")
                   if p.with_suffix(".memory").is_file() and "attempts" not in p.parts)
    return sorted({n for pat in patterns for n in names if fnmatch.fnmatch(n, pat)})


def describe(base, name):
    report = json.loads((base / f"{name}.json").read_text())
    out = {"json_sha256": sha((base / f"{name}.json").read_bytes()), "control": report.get("control")}
    state = report.get("state") or {}
    out["memory_sha256"] = state.get("memory_sha256")
    out["steps"] = state.get("steps")
    png = base / f"{name}.final.png"
    if png.is_file():
        with Image.open(png) as im:
            out["frame"] = f"{im.size[0]}x{im.size[1]} {im.mode}"
        out["index_bytes"] = (base / f"{name}.final.idx").stat().st_size
        out["palette_bytes"] = (base / f"{name}.final.pal").stat().st_size
    return out, report.get("input_hashes")


def run_row(row, a):
    args = [x.replace("{game}", str(a.game)).replace("{reports}", str(a.reports)).replace("{repo}", str(a.repo))
            for x in row["args"]]
    proc = subprocess.run([sys.executable, str(a.repo / "tools" / row["checker"]), *args], cwd=a.repo / "tools",
                          capture_output=True)
    status = {0: "PASS", 77: "SKIP"}.get(proc.returncode, "FAIL")
    out = {"id": row["id"], "path": row["path"], "title": row["title"], "specs": row["specs"], "flags": row["flags"],
           "checker": row["checker"], "checker_sha256": sha((a.repo / "tools" / row["checker"]).read_bytes()),
           "status": status, "checker_output_sha256": sha(proc.stdout), "known_diffs": row["known_diffs"],
           "regenerate": row["regenerate"]}
    if status == "FAIL":
        out["error_tail"] = proc.stderr.decode("utf-8", "replace")[-400:]
    if row["dir"]:
        base = a.reports / row["dir"]
        adapter = base / "window-src" / "adapter.go"
        out["frontend_sha256"] = sha(adapter.read_bytes()) if adapter.is_file() else None
        hashes = []
        for col in ("zh", "control", "negative", "baseline"):
            items = {}
            for name in receipts(base, row.get(col, [])):
                items[name], h = describe(base, name)
                if h and h not in hashes:
                    hashes.append(h)
            out[col] = items
        if not row.get("baseline"):
            # 原版基線：英文控制收據的原版狀態（前端不改寫原版 RAM／索引／色盤）
            out["baseline"] = {k: {"memory_sha256": v["memory_sha256"], "from": "control"} for k, v in out["control"].items()}
        out["input_hash_sets"] = hashes
        out["gui_inputs"] = {p.name: sha(p.read_bytes()) for pat in row["gui_inputs"] for p in sorted(base.glob(pat))}
    return out


def markdown(report):
    lines = ["# 驗證矩陣", "",
             "由 `tools/verification_matrix.py` 依 `tools/verification-matrix.json` 產生；不要手改。收據只在已忽略的 `workplace/reports/`，本頁只列雜湊與數量。", "",
             f"- dosgolem：`{report['dosgolem_rev']}`",
             "- 原版輸入（各收據記錄的檔案雜湊合併，同名檔衝突 " + str(len(report["input_conflicts"])) + " 個）：" +
             "、".join(f"`{k}` `{v[:12]}…`" for k, v in sorted(report["input_files"].items())),
             f"- 結果：{report['summary']}", "",
             "原版基線指英文控制收據的原版 RAM／VGA 索引／色盤；中文模式必須與它相同，差異只在中文安全區（由各檢查器核對）。", "",
             "| 列 | 路徑 | 規格 | 檢查器 | 結果 | 基線 | 中文 | 英文 | 負例 | GUI 輸入 | 畫面格式 | 已知差異 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["rows"]:
        frames = sorted({v.get("frame", "") for c in ("zh", "control") for v in r.get(c, {}).values() if v.get("frame")})
        lines.append("| {} | {} | {} | `{}` | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["title"], {"dynamic": "動態", "static": "靜態", "both": "兩者"}[r["path"]], "、".join(r["specs"]) or "—",
            r["checker"], r["status"], len(r.get("baseline", {})), len(r.get("zh", {})), len(r.get("control", {})),
            len(r.get("negative", {})), len(r.get("gui_inputs", {})), "；".join(frames) or "—", r["known_diffs"] or "—"))
    lines += ["", "## 未驗範圍", ""] + [f"- {x}" for x in report["not_covered"]]
    lines += ["", "## 重產收據", "", "各列收據由表中 `regenerate` 腳本在 Docker 內重產（每列數十分鐘到數小時）；本矩陣只重跑檢查器，不重跑模擬。完整清單見 JSON 報告。", ""]
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--repo", type=Path, default=Path("/repo"))
    p.add_argument("--dosgolem", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    spec = json.loads((a.repo / "tools/verification-matrix.json").read_text(encoding="utf-8"))
    rows = [run_row(r, a) for r in spec["rows"]]
    # 合併各收據記錄的原版檔案雜湊；同名檔雜湊不同即為版本混用。
    inputs, conflicts = {}, set()
    for r in rows:
        for h in r.get("input_hash_sets", []):
            for k, v in h.items():
                if inputs.setdefault(k, v) != v:
                    conflicts.add(k)
    counts = {s: sum(r["status"] == s for r in rows) for s in ("PASS", "SKIP", "FAIL")}
    paths = {k: {c: sum(len(r.get(c, {})) for r in rows if r["path"] == k) for c in COLUMNS} for k in ("dynamic", "static")}
    complete = all(all(paths[k][c] > 0 for c in COLUMNS) for k in paths)
    report = {"matrix_sha256": sha((a.repo / "tools/verification-matrix.json").read_bytes()), "dosgolem_rev": git_head(a.dosgolem),
              "input_files": inputs, "input_conflicts": sorted(conflicts), "rows": rows, "path_totals": paths, "not_covered": spec["not_covered"],
              "summary": f"PASS {counts['PASS']}、SKIP {counts['SKIP']}、FAIL {counts['FAIL']}；原版輸入衝突 {len(conflicts)}；動態與靜態四類收據齊備：{'是' if complete else '否'}"}
    body = json.dumps(report, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    (a.output / "matrix.json").write_text(body, encoding="utf-8")
    md = markdown(report)
    (a.output / "verification-matrix.md").write_text(md, encoding="utf-8")
    print(json.dumps({"summary": report["summary"], "report_sha256": sha(body.encode()), "markdown_sha256": sha(md.encode())}, ensure_ascii=False))
    if counts["FAIL"] or conflicts:
        return 1
    return 77 if counts["SKIP"] == len(rows) else 0


if __name__ == "__main__":
    raise SystemExit(main())
