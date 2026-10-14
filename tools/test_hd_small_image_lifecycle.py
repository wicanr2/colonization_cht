"""以真實小圖像收據驗證來源混淆、底圖、未知覆寫與截斷拒絕。"""
import argparse
import copy
import json
import os
from pathlib import Path

from check_hd_small_image_lifecycle import check, read, WRITERS
from check_hd_building_nine_lifecycle import event_stream

parser = argparse.ArgumentParser(description=__doc__)
for name in ["observed", "control", "build", "sources", "entry-report", "points", "output"]:
    parser.add_argument("--"+name, type=Path, required=True)
a = parser.parse_args()
out = a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0 and not out.exists()
assert out.is_relative_to("/out") and out.parent.stat().st_uid == os.getuid()
out.mkdir()
draws = read(a.observed / "draws.json")
events = list(event_stream(a.observed / "writes.json"))
first_write = next(i for i, e in enumerate(events) if e["kind"] == "write")
same_unknown = next(i for i, e in enumerate(events) if e["kind"] == "write"
                    and e["old"] == e["value"] and e["site"] not in WRITERS)
positive = check(a.observed, a.control, a.build, a.sources, a.entry_report, a.points)
assert positive["source_calls"] == 420
cases = []


def reject(name, filename, payload, expected):
    case = out / name
    case.mkdir()
    for p in a.observed.iterdir():
        (case / p.name).symlink_to(p.resolve(), target_is_directory=p.is_dir())
    target = case / filename
    target.unlink()
    target.write_bytes(payload)
    try:
        check(case, a.control, a.build, a.sources, a.entry_report, a.points)
    except (ValueError, StopIteration) as error:
        assert expected in str(error), (name, expected, str(error))
        cases.append({"name": name, "rejected": True, "reason": str(error)})
    else:
        raise AssertionError("錯誤收據未被拒絕："+name)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False)+"\n").encode()


for source_id in sorted({c["research_id"] for c in draws["calls"]}):
    altered = copy.deepcopy(draws)
    call = next(c for c in altered["calls"] if c["research_id"] == source_id)
    call["source_encoded_sha256"] = "0"*64
    reject(f"source-{source_id:04d}", "draws.json", encoded(altered), "來源或完整繪製不同")
for name, field, value, reason in [
    ("wrong-width", "record_words", [0, 0, 0, 0, 1, 1], "來源或完整繪製不同"),
    ("wrong-canvas", "canvas_linear", 0x3C500, "原版參數、畫布或幾何不同"),
    ("wrong-return", "return_step", 0, "返回邊界不同"),
    ("lost-transparent-background", "transparent_background_unchanged", False, "完整寫入或底圖不同"),
]:
    altered = copy.deepcopy(draws)
    altered["calls"][0][field] = value
    reject(name, "draws.json", encoded(altered), reason)
for name, index, field, value, reason in [
    ("wrong-old-byte", first_write, "old", (events[first_write]["old"]+1)%256, "原始寫入舊值不能重建"),
    ("wrong-source-byte", first_write, "value", (events[first_write]["value"]+1)%256, "來源逐寫重複、超界或色號不同"),
    ("unverified-writer", first_write, "code16", "00"*16, "來源逐寫重複、超界或色號不同"),
    ("same-value-retains-owner", same_unknown, "after_cell", {"call": 1, "local": 0, "native": 1}, "未知後畫保留過期來源"),
]:
    altered = copy.deepcopy(events)
    altered[index][field] = value
    reject(name, "writes.json", encoded(altered), reason)
truncated = encoded(events)[:-2]
reject("truncated-events", "writes.json", truncated, "事件")
result = {"result": "PASS_SMALL_IMAGE_TRUE_RECEIPT_NEGATIVES", "positive_sources": 31,
          "positive_calls": 420, "negative_cases": len(cases), "cases": cases,
          "same_value_unknown_write_step": events[same_unknown]["step"]}
(out / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
print(result["result"], len(cases), flush=True)
