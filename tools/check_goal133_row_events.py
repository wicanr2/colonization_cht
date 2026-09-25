#!/usr/bin/env python3
"""目標133：把九欄原版讀字／改色／逐幀雜湊分組成逐欄印字事件；原版缺失回 SKIP 77。"""

import argparse
import hashlib
import json
from pathlib import Path


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
# 原版 GAME.TXT 檔案位移；~ 為原始快捷鍵標記，畫面不印。
FIELDS = (0x4CD, 0x4E9, 0x4FD, 0x512, 0x525, 0x533, 0x53E, 0x550, 0x566)


# 整組八列印字的逐列 0D21:012C 改色點數（第1至8列）與核取圖示等安全區外點數。
ROW_WRITES = {"1": 338, "2": 349, "3": 283, "4": 186, "5": 172, "6": 316, "7": 343, "8": 246,
              "None": 344}
ROW_BUFFERS = {0x2ADDE, 0x2AE46}  # 20-bit 線性 RAM：開窗與點擊重印的印字緩衝
# 逐列印前底圖（320×200 安全矩形位元組 SHA-256）：奇數列／偶數列各有一般與反白兩種。
ROW_BACKGROUNDS = {
    1: {"3c24c328cb52d0ddfe5da07f462e685f9d41c89fabad06722a38095ff0078947",
        "903ff7549ac31fbb35f8a978ed3072aa4d6c7ab035dcea9ede983aea48490159"},
    0: {"a37541c55677774da71ee04095a82752663fd9e0a24bbaf671d79134a8627bff",
        "96f7592f13131bb6eaf8128df7a612867459f9abe14ebedf18d3810405180807"},
}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def field_texts(game_txt):
    texts = []
    for offset in FIELDS:
        end = game_txt.index(b"\r\n", offset)
        texts.append(game_txt[offset:end].replace(b"~", b"").decode("ascii"))
    return texts


def row_of(point, safe):
    x, y = point
    for index, (x0, y0, x1, y1) in enumerate(safe):
        if x0 <= x < x1 and y0 <= y < y1:
            return index
    return None


def group(events, safe):
    """原版逐字讀一字、畫一字；同一組讀取位址且讀字間隔不超過 GAP 步者歸同一次印字，其間改色屬之。"""
    gap = 5000
    prints, current = [], None
    for event in events:
        if event["k"] == "r":
            base = event["a"] & ~1
            if current is None or base != current["base"] or event["s"] - current["last_read"] > gap:
                current = {"base": base, "reads": [], "writes": [], "last_read": event["s"]}
                prints.append(current)
            current["reads"].append(event)
            current["last_read"] = event["s"]
        elif current is not None:
            current["writes"].append(event)
    result = []
    for item in prints:
        reads = item["reads"]
        chars = bytes(read["v"] for read in reads if read["v"] != 0)
        rows = {}
        for write in item["writes"]:
            index = row_of((write["x"], write["y"]), safe)
            rows[index] = rows.get(index, 0) + 1
        xs = [write["x"] for write in item["writes"]]
        ys = [write["y"] for write in item["writes"]]
        result.append({
            "read_start": reads[0]["s"], "read_end": reads[-1]["s"], "read_count": len(reads),
            "read_linear": sorted({read["a"] for read in reads}),
            "operand_matches_address": all(read["op"] == read["a"] for read in reads),
            "text": chars.decode("latin-1"),
            "write_count": len(item["writes"]),
            "write_start": item["writes"][0]["s"] if item["writes"] else None,
            "write_end": item["writes"][-1]["s"] if item["writes"] else None,
            "write_bbox": [min(xs), min(ys), max(xs) + 1, max(ys) + 1] if xs else None,
            "write_rows": {str(key): value for key, value in sorted(rows.items(), key=lambda kv: str(kv[0]))},
            "new_colors": sorted({write["n"] for write in item["writes"]}),
        })
    return result


def frames_by_row(frames, count):
    """每欄的逐幀相位：底層畫布雜湊與真 VGA 雜湊的變化時點。"""
    rows = []
    for index in range(count):
        changes, last = [], None
        for frame in frames:
            key = (frame["mode"], frame["canvas"][index], frame["vga"][index])
            if key != last:
                changes.append({"s": frame["s"], "mode": frame["mode"],
                                "canvas": frame["canvas"][index], "vga": frame["vga"][index],
                                "vga_equals_canvas": frame["canvas"][index] == frame["vga"][index]})
                last = key
        rows.append(changes)
    return rows


def reprint_backgrounds(reports, name, data, safe, prints):
    """整組八列印字後的第一張另存畫布：核對寫入終值，並逐列以首次寫入前舊值重建印前底圖。"""
    dumps = sorted((int(path.name.split("rowframe-")[1].split(".")[0]), path)
                   for path in reports.glob(f"{name}-a.rowframe-*.canvas"))
    if not dumps:
        return []
    writes = [event for event in data["events"] if event["k"] == "w"]
    result = []
    groups = [item for item in prints if item["read_count"] == 268]
    for number, item in enumerate(groups):
        after = [(step, path) for step, path in dumps if step > item["write_end"]]
        need(after, "整組印字後沒有另存畫布")
        step, path = after[0]
        if number + 1 < len(groups) and groups[number + 1]["read_start"] < step:
            result.append({"read_start": item["read_start"], "canvas_step": None,
                           "skipped": "下一次整組印字早於下一張另存畫布"})
            continue
        post = bytearray(path.read_bytes())
        need(post == (reports / path.name.replace(f"{name}-a.", f"{name}-b.")).read_bytes(),
             "兩次冷啟動另存畫布不同")
        own = [w for w in writes if item["write_start"] <= w["s"] <= item["write_end"]]
        later = [w for w in writes if item["write_end"] < w["s"] < step and
                 60 <= w["x"] < 260 and 59 <= w["y"] < 155]
        last, first_old = {}, {}
        for w in own:
            key = w["y"] * 320 + w["x"]
            last[key] = w["n"]
            first_old.setdefault(key, w["o"])
        if later or any(post[key] != value for key, value in last.items()):
            # 下一次重印先重畫底圖（非 0D21:012C 寫入者）即覆蓋；這種中間事件不會等到 VGA 同步。
            result.append({"read_start": item["read_start"], "canvas_step": step,
                           "skipped": "被下一次重印在另存畫布前取代"})
            continue
        pre = bytearray(post)
        for key, value in first_old.items():
            pre[key] = value
        rows = []
        for index in range(1, 9):
            x0, y0, x1, y1 = safe[index]
            part = b"".join(bytes(pre[y * 320 + x0:y * 320 + x1]) for y in range(y0, y1))
            done = b"".join(bytes(post[y * 320 + x0:y * 320 + x1]) for y in range(y0, y1))
            rows.append({"row": index, "pre_sha256": sha(part), "post_sha256": sha(done),
                         "pre_palette_indices": len(set(part))})
        result.append({"read_start": item["read_start"], "canvas_step": step,
                       "check_prefix": [item["text"][i] for i in range(0, len(item["text"]))
                                        if item["text"][i] in "[]"], "rows": rows})
    return result


def verify(result):
    texts = result["field_texts"]
    groups = [item for item in result["prints"] if item["read_count"] == 268]
    need(groups, "沒有整組八列印字事件")
    for item in groups:
        text = item["text"]
        expected_tail = [" " + texts[index] for index in range(1, 9)]
        pos, prefix = 0, []
        for tail in expected_tail:
            need(text[pos] in "[]" and text[pos + 1:pos + 1 + len(tail)] == tail,
                 "整組印字的讀字內容與原版列文字不符")
            prefix.append(text[pos])
            pos += 1 + len(tail)
        need(pos == len(text), "整組印字含額外字元")
        need(set(item["read_linear"]) <= {base + 1 for base in ROW_BUFFERS} | ROW_BUFFERS and
             len({address & ~1 for address in item["read_linear"]}) == 1 and
             item["operand_matches_address"], "整組印字讀取位址或運算元不符")
        need(item["write_rows"] == ROW_WRITES, "逐列改色點數不符")
        item["check_prefix"] = "".join(prefix)
    stable = [entry for entry in result["reprint_backgrounds"] if not entry.get("skipped")]
    for entry in stable:
        for row in entry["rows"]:
            need(row["pre_sha256"] in ROW_BACKGROUNDS[row["row"] % 2],
                 f"第{row['row']}列印前底圖不屬已知一般／反白底圖")
    return {"row_groups": len(groups), "stable_backgrounds_checked": len(stable),
            "check_prefixes": [item["check_prefix"] for item in groups]}


def analyze(reports, game, name):
    raw_a = (reports / f"{name}-a.row-events.json").read_bytes()
    need(raw_a == (reports / f"{name}-b.row-events.json").read_bytes(), "兩次冷啟動九欄事件不相同")
    report_a = json.loads((reports / f"{name}-a.json").read_bytes())
    report_b = json.loads((reports / f"{name}-b.json").read_bytes())
    control = json.loads((reports / f"{name}-control.json").read_bytes())
    need(report_a == report_b, "兩次冷啟動主報告不相同")
    for key in sorted(set(report_a) & set(control)):
        if key in ("control", "row_event_count", "row_frame_changes", "writers", "print_reads",
                   "transfers", "sources", "preprint"):
            continue
        need(report_a[key] == control[key], "監看擾動原版狀態：" + key)
    data = json.loads(raw_a)
    safe = [tuple(item) for item in data["safe"]]
    texts = field_texts((game / "GAME.TXT").read_bytes())
    prints = group(data["events"], safe)
    for item in prints:
        item["field"] = texts.index(item["text"]) if item["text"] in texts else None
    return {"reprint_backgrounds": reprint_backgrounds(reports, name, data, safe, prints),
            "row_events_sha256": sha(raw_a), "event_count": len(data["events"]),
            "frame_changes": len(data["frames"]), "field_texts": texts,
            "prints": prints, "frames_by_row": frames_by_row(data["frames"], len(safe)),
            "compared_control_keys": sorted(k for k in set(report_a) & set(control)
                                            if k not in ("control", "row_event_count",
                                                         "row_frame_changes", "writers",
                                                         "print_reads", "transfers", "sources",
                                                         "preprint"))}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--reports", type=Path, required=True)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--name", default="row", help="探針輸出前綴：row 或 toggle")
    args = p.parse_args()
    if not (args.game / "GAME.TXT").is_file():
        print("SKIP：缺合法原版，未宣稱九欄事件通過")
        return 77
    need(sha((args.game / "GAME.TXT").read_bytes()) == GAME_SHA, "原版 GAME.TXT 版本不符")
    result = analyze(args.reports, args.game, args.name)
    result["verified"] = verify(result)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"result": "PASS", "prints": len(result["prints"]), **result["verified"],
                      "row_events_sha256": result["row_events_sha256"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
