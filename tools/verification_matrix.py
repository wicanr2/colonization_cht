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


def source_identity(row, game, reports, repo):
    """重跑來源證據，並將聲明綁定該列 GUI 輸入與完整原版終點。"""
    claim = row.get("source_identity")
    if not claim:
        return None
    base = reports / row["dir"]
    args = [x.replace("{game}", str(game)).replace("{reports}", str(reports)).replace("{repo}", str(repo))
            for x in claim["args"]]
    checker = repo / "tools" / claim["checker"]
    proc = subprocess.run([sys.executable, str(checker), *args], cwd=repo / "tools", capture_output=True)
    result = {"status": {0: "PASS", 77: "SKIP"}.get(proc.returncode, "FAIL"),
              "checker": claim["checker"], "checker_sha256": sha(checker.read_bytes()),
              "checker_output_sha256": sha(proc.stdout)}
    if result["status"] != "PASS":
        result["error_tail"] = proc.stderr.decode("utf-8", "replace")[-400:]
        return result
    try:
        proof = json.loads(proc.stdout)
        if "--lookup-reports" not in args or Path(args[args.index("--lookup-reports") + 1]).resolve() != base.resolve():
            raise ValueError("來源觀測目錄未綁定矩陣列")
        aliases = proof["observed_template_source_aliases"]
        if proof.get("result") != "PASS" or proof.get("grade") != "confirmed" or not aliases or aliases != claim["aliases"]:
            raise ValueError("來源映射與已驗證據不同")
        inputs = {sha(p.read_bytes()) for pat in row["gui_inputs"] for p in base.glob(pat)}
        if proof["lookup_gui_inputs_sha256"] not in inputs:
            raise ValueError("來源觀測使用了另一份 GUI 輸入")
        controls = [json.loads((base / (name + ".json")).read_text())["state"]
                    for name in receipts(base, row["control"])]
        if not any(s["steps"] == proof["lookup_original_step"] and
                   s["memory_sha256"] == proof["lookup_original_memory_sha256"] for s in controls):
            raise ValueError("來源觀測完整原版終點不同")
        result.update(aliases=aliases, grade=proof["grade"],
                      gui_inputs_sha256=proof["lookup_gui_inputs_sha256"],
                      original_step=proof["lookup_original_step"],
                      original_memory_sha256=proof["lookup_original_memory_sha256"],
                      evidence_sha256=proof["evidence_sha256"], limit=proof["limit"])
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        result.update(status="FAIL", error_tail=str(exc))
    return result


def checked_fields(row, game, reports, repo):
    """普查只採用該列檢查器實際驗過的鍵、原文與安全區。"""
    if row.get('census_scope') != 'checker':
        return None
    base = reports / row['dir']
    args = [x.replace('{game}', str(game)).replace('{reports}', str(reports)).replace('{repo}', str(repo))
            for x in row['args']]
    checker = repo / 'tools' / row['checker']
    proc = subprocess.run([sys.executable, str(checker), *args], cwd=repo / 'tools', capture_output=True)
    result = {'status': {0: 'PASS', 77: 'SKIP'}.get(proc.returncode, 'FAIL'),
              'checker_sha256': sha(checker.read_bytes()), 'checker_output_sha256': sha(proc.stdout)}
    if result['status'] != 'PASS':
        result['error_tail'] = proc.stderr.decode('utf-8', 'replace')[-400:]
        return result
    try:
        proof = json.loads(proc.stdout)
        if proof.get('result') != 'PASS' or '--reports' not in args or Path(args[args.index('--reports') + 1]).resolve() != base.resolve():
            raise ValueError('已驗欄位未綁定該列收據')
        inputs = {sha(p.read_bytes()) for pat in row['gui_inputs'] for p in base.glob(pat)}
        if proof['inputs_sha256'] not in inputs:
            raise ValueError('已驗欄位使用另一份GUI輸入')
        controls = [json.loads((base / (name + '.json')).read_text())['state']
                    for name in receipts(base, row['control'])]
        if not any(s['steps'] == proof['final_step'] and s['memory_sha256'] == proof['final_memory_sha256'] for s in controls):
            raise ValueError('已驗欄位完整原版終點不同')
        fields = proof['verified_fields']
        if not fields or any(not isinstance(f['candidate_id'], str) or not f['candidate_id'] or
                             not isinstance(f['shown'], str) or not f['shown'] or
                             len(f['safe']) != 4 or any(type(v) is not int for v in f['safe']) or
                             not (0 <= f['safe'][0] < f['safe'][2] <= 320 and 0 <= f['safe'][1] < f['safe'][3] <= 200)
                             for f in fields):
            raise ValueError('已驗欄位清冊不完整')
        for field in fields:
            if 'source_ids' in field:
                ids = field['source_ids']
                if (not isinstance(ids, list) or not ids or
                        any(not isinstance(cid, str) or not cid for cid in ids) or len(set(ids)) != len(ids)):
                    raise ValueError('已驗欄位原始來源清冊不合法')
        unique = {(f['candidate_id'], f['shown'], tuple(f['safe'])) for f in fields}
        if len(unique) != len(fields):
            raise ValueError('已驗欄位重複')
        result.update(fields=fields, field_count=len(fields), gui_inputs_sha256=proof['inputs_sha256'],
                      original_step=proof['final_step'], original_memory_sha256=proof['final_memory_sha256'])
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        result.update(status='FAIL', error_tail=str(exc))
    return result


def run_row(row, a):
    args = [x.replace("{game}", str(a.game)).replace("{reports}", str(a.reports)).replace("{repo}", str(a.repo))
            for x in row["args"]]
    proc = subprocess.run([sys.executable, str(a.repo / "tools" / row["checker"]), *args], cwd=a.repo / "tools",
                          capture_output=True)
    status = {0: "PASS", 77: "SKIP"}.get(proc.returncode, "FAIL")
    out = {"id": row["id"], "path": row["path"], "title": row["title"], "specs": row["specs"], "flags": row["flags"],
           "checker": row["checker"], "checker_sha256": sha((a.repo / "tools" / row["checker"]).read_bytes()),
           "status": status, "checker_output_sha256": sha(proc.stdout), "known_diffs": row["known_diffs"],
           "regenerate": row["regenerate"], "stale_since": row.get("stale_since")}
    if row.get("key_evidence"):
        out["key_evidence"] = row["key_evidence"]
    if row.get("source_identity"):
        identity = source_identity(row, a.game, a.reports, a.repo)
        out["source_identity"] = identity
        if status == "PASS" and identity["status"] != "PASS":
            status = out["status"] = identity["status"]
            out["error_tail"] = identity.get("error_tail", "來源證據未通過")
    if row.get('census_scope'):
        scope = checked_fields(row, a.game, a.reports, a.repo)
        out['census_scope'] = scope
        if scope is None or scope['status'] != 'PASS':
            out['status'] = 'FAIL' if scope is None else scope['status']
            out['error_tail'] = '不支援的普查欄位範圍' if scope is None else scope.get('error_tail', '普查欄位未通過')
    if status == "FAIL":
        out.setdefault("error_tail", proc.stderr.decode("utf-8", "replace")[-400:])
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
             "「待重驗」表示該列收據早於現行譯文（目標156 改稿）：字模已重烘、全部旗標載入綁定通過，但真 GUI 與重播尚未依新譯文重跑。", "",
             "原版基線指英文控制收據的原版 RAM／VGA 索引／色盤；中文模式必須與它相同，差異只在中文安全區（由各檢查器核對）。", "",
             "| 列 | 路徑 | 規格 | 檢查器 | 結果 | 基線 | 中文 | 英文 | 負例 | GUI 輸入 | 畫面格式 | 已知差異 |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in report["rows"]:
        frames = sorted({v.get("frame", "") for c in ("zh", "control") for v in r.get(c, {}).values() if v.get("frame")})
        lines.append("| {} | {} | {} | `{}` | {} | {} | {} | {} | {} | {} | {} | {} |".format(
            r["title"], {"dynamic": "動態", "static": "靜態", "both": "兩者"}[r["path"]], "、".join(r["specs"]) or "—",
            r["checker"], r["status"] + ("（待重驗）" if r.get("stale_since") else ""), len(r.get("baseline", {})), len(r.get("zh", {})), len(r.get("control", {})),
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
    # 先建立輸出目錄，避免完整檢查跑完後才因目錄缺失而丟失報告。
    a.output.mkdir(parents=True, exist_ok=True)
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
    stale = sum(bool(r.get("stale_since")) for r in rows)
    paths = {k: {c: sum(len(r.get(c, {})) for r in rows if r["path"] == k) for c in COLUMNS} for k in ("dynamic", "static")}
    complete = all(all(paths[k][c] > 0 for c in COLUMNS) for k in paths)
    report = {"matrix_sha256": sha((a.repo / "tools/verification-matrix.json").read_bytes()), "dosgolem_rev": git_head(a.dosgolem),
              "input_files": inputs, "input_conflicts": sorted(conflicts), "rows": rows, "path_totals": paths, "not_covered": spec["not_covered"],
              "summary": f"PASS {counts['PASS']}、SKIP {counts['SKIP']}、FAIL {counts['FAIL']}；收據待重驗 {stale} 列；原版輸入衝突 {len(conflicts)}；動態與靜態四類收據齊備：{'是' if complete else '否'}"}
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
