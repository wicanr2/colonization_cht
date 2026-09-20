#!/usr/bin/env python3
"""從 docs/worklist.json 產生並檢查專案的唯一工作清單。"""
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "docs" / "worklist.json"


def load():
    data = json.loads(DATA_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != "colonization-cht-worklist/1":
        raise ValueError("不支援的工作清單 schema")
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("工作清單必須含有至少一筆項目")
    ids = [item.get("id") for item in items]
    issues = [item.get("issue") for item in items]
    if any(not isinstance(value, str) or not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("每筆項目必須有唯一且非空的 id")
    if any(not isinstance(value, int) or value < 1 for value in issues) or len(issues) != len(set(issues)):
        raise ValueError("每筆項目必須有唯一且正整數的 GitHub Issue 編號")
    known = set(ids)
    for item in items:
        if item.get("state") not in {"planned", "in_progress", "blocked", "completed"}:
            raise ValueError(f"{item['id']} 的 state 不合法")
        if any(dependency not in known for dependency in item.get("depends_on", [])):
            raise ValueError(f"{item['id']} 引用了不存在的依賴")
        verify = item.get("verify", {})
        if verify.get("kind") not in {"manual", "absent", "all_present"}:
            raise ValueError(f"{item['id']} 的 verify kind 不合法")
        if verify.get("kind") == "absent" and (not verify.get("paths") or not verify.get("pattern")):
            raise ValueError(f"{item['id']} 的 absent verify 缺少 paths 或 pattern")
        if verify.get("kind") == "all_present":
            checks = verify.get("checks")
            if not isinstance(checks, list) or not checks or any(not check.get("path") or not check.get("pattern") for check in checks):
                raise ValueError(f"{item['id']} 的 all_present verify 缺少 checks")
    return data


def issue_link(data, number):
    return f"{data['repository']}/issues/{number}"


def render(data):
    lines = [
        "# 工作計畫",
        "",
        "<!-- 由 tools/worklist.py render 從 docs/worklist.json 產生；請勿手動修改。 -->",
        "",
        "所有未完成工作以 GitHub Issue 為執行入口；本檔只呈現其機器可讀索引。",
        "尚未自動驗證的條目一律標為人工驗證（manual），代表它們仍未完成；已完成條目必須有可重跑的訊號。",
        "",
        "| Issue | 狀態 | 工作項目 | 依賴 | 驗收摘要 |",
        "|---:|---|---|---|---|",
    ]
    for item in data["items"]:
        dependencies = ", ".join(f"`{value}`" for value in item["depends_on"]) or "—"
        title = f"[{item['title']}]({issue_link(data, item['issue'])})"
        lines.append(f"| #{item['issue']} | {item['state']} | {title} | {dependencies} | {item['acceptance']} |")
    lines += ["", "## 驗證", "", "```text", "tools/worklist.py verify", "```", ""]
    return "\n".join(lines)


def absent_signal(verify):
    for relative_path in verify["paths"]:
        path = ROOT / relative_path
        if path.is_file() and re.search(verify["pattern"], path.read_text(encoding="utf-8")):
            return relative_path
    return None


def all_present_signals(verify):
    signals = []
    for check in verify["checks"]:
        path = ROOT / check["path"]
        if not path.is_file() or not re.search(check["pattern"], path.read_text(encoding="utf-8")):
            return None
        signals.append(check["path"])
    return signals


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"render", "verify", "write"}:
        raise SystemExit("用法：tools/worklist.py render|write|verify")
    try:
        data = load()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise SystemExit(f"工作清單無效：{error}")
    if sys.argv[1] == "render":
        print(render(data), end="")
        return
    if sys.argv[1] == "write":
        (ROOT / "WORKLIST.md").write_text(render(data), encoding="utf-8")
        return
    stale = False
    for item in data["items"]:
        verify = item["verify"]
        if verify["kind"] == "manual":
            print(f"{item['id']}: 仍未完成（manual；{verify['note']}）")
            continue
        if verify["kind"] == "absent":
            signal = absent_signal(verify)
            completed = bool(signal)
            detail = f"訊號位於 {signal}" if signal else verify["note"]
        else:
            signal = all_present_signals(verify)
            completed = bool(signal)
            detail = f"訊號位於 {', '.join(signal)}" if signal else verify["note"]
        if item["state"] == "completed" and completed:
            print(f"{item['id']}: 已完成（{detail}）")
        else:
            stale = True
            print(f"{item['id']}: 完成狀態可能過期（{detail}）")
    if stale:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
