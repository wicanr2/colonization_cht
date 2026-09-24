#!/usr/bin/env python3
"""獨立核對目標120第三張難度卡的來源、原版印字與同狀態收據。"""

import argparse
import copy
import hashlib
import json
from pathlib import Path


ORIGINAL = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
}
INPUTS = {
    "click": "5deec238b41c97773d12516730d7324a7c64b16c12f34b89bc2421c6f039f3a4",
    "hover": "f51cfad1224c659c3b99c4785d64167a17782228021dee1cdcbaae1bc4d04002",
    "control": "d850487192afe3b4b0dc7879e0dcfda537c9222fdffd2aa3f0630a1c9af68ef2",
}
NAMES = ("click-v3-a", "click-v3-b", "click-v3-control", "hover-v3", "control-v3")
SNAPS = ("before-title-ink", "after-title-before-subtitle", "after-second-ink", "away-settled")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def load(reports, game):
    original = {}
    for name, expected in ORIGINAL.items():
        path = game / name
        if not path.is_file():
            raise FileNotFoundError(path)
        original[name] = path.read_bytes()
        require(sha(original[name]) == expected, "原版版本不符：" + name)
    for name, offset, value in (("NAMES.TXT", 0xC22, b"Conquistador"),
                                ("LABELS.TXT", 0x8B8, b"Moderate")):
        require(original[name][offset:offset + len(value)] == value, "TXT 原始位元組不符")
    inputs = {}
    for name, expected in INPUTS.items():
        inputs[name] = (reports / f"{name}.inputs.json").read_bytes()
        require(sha(inputs[name]) == expected, "玩家輸入指紋不符：" + name)
    rows = {name: json.loads((reports / f"{name}.json").read_text()) for name in NAMES}
    images = {(name, snap): (reports / f"{name}.{snap}.canvas").read_bytes()
              for name in ("click-v3-a", "click-v3-b", "click-v3-control") for snap in SNAPS}
    return rows, images, original, inputs


def diff(a, b):
    require(len(a) == len(b) == 64000, "原始畫布長度不符")
    pts = [(i % 320, i // 320) for i in range(64000) if a[i] != b[i]]
    require(bool(pts), "原始文字差分消失")
    return len(pts), (min(x for x, _ in pts), min(y for _, y in pts),
                      max(x for x, _ in pts), max(y for _, y in pts))


def validate(rows, images, original, inputs):
    a, b, no_watch, hover, no_click = (rows[name] for name in NAMES)
    require(a == b, "雙次冷啟動收據不一致")
    for name, row in rows.items():
        route = "click" if name.startswith("click") else "hover" if name.startswith("hover") else "control"
        require(row["version"] == "goal120-third-card-v3" and row["end"] == 40000000,
                "探針版本或終點不符")
        require(row["input_sha256"] == sha(inputs[route]) == INPUTS[route], "玩家事件不符")
        require(row["input_hashes"] == ORIGINAL and row["difficulty_art_opened"], "原版或卡片資產不符")
        require(row["dos_address_space"] == "real-mode CS:IP and 20-bit linear RAM" and
                row["canvas_address_space"] == "320x200 indexed logical pixels", "位址空間不符")
        require(row["source_candidates"]["title_ram_0x4cc7e"] == b"Conquistador\0".hex() and
                row["source_candidates"]["subtitle_ram_0x4df9d"] == b"Moderate\0".hex(),
                "原版 RAM 來源候選不符")
    require(a["observed"] and b["observed"] and not no_watch["observed"] and
            hover["observed"] and no_click["observed"], "觀測／控制旗標不符")
    require(not no_watch["reads"] and not no_watch["writes"], "無監看控制意外有事件")
    require(a["state"] == no_watch["state"] and a["snapshots"] == no_watch["snapshots"] and
            a["file_loads"] == no_watch["file_loads"], "只讀觀測改變原版狀態")
    require(all(not row["reads"] and not row["writes"] for row in (hover, no_click)),
            "僅移鼠／不操作不應印第三張卡")
    for field in ("canvas_sha256", "indexed_sha256", "palette_sha256"):
        require(hover["state"][field] == no_click["state"][field], "移開後背景未回到未點選狀態")
    loads = a["file_loads"]
    for name, offset, text in (("NAMES.TXT", 0xC00, "Conquistador"),
                               ("LABELS.TXT", 0x800, "Moderate")):
        matches = [row for row in loads if row["name"] == name and row["candidate"] == text]
        require(matches and all(row["matched"] and row["file_offset"] == offset and row["got"] == 512
                                for row in matches), "DOS TXT 載入邊未閉合：" + name)
    require(len(loads) == 3, "DOS 載入候選筆數意外變動")
    for step, start, word in ((33090002, 0x4CC7E, b"Conquistador\0"),
                              (33105132, 0x4DF9D, b"Moderate\0")):
        got = [(e["linear"], e["value"]) for e in a["reads"]
               if e["site"] == "0E2D:11CF" and e["step"] == step]
        require(got == [(start + i, value) for i, value in enumerate(word)], "原版當次來源讀取不符")
    visible = [e for e in a["reads"] if e["site"] == "0D21:00C6" and e["step"] < 33115000]
    words, current = [], []
    for e in visible:
        current.append(e["value"])
        if e["value"] == 0:
            words.append(bytes(current))
            current = []
    require(not current and words == [b"CONQUISTADOR:\0"] * 2 + [b"Moderate\0"] * 2,
            "原版格式化印字緩衝不符")
    print_writes = [e for e in a["writes"] if e["site"] == "0D21:012C"
                    and 33090000 <= e["step"] < 33115000]
    require(len(print_writes) == 368 and all(
        (32 <= e["x"] <= 81 and 141 <= e["y"] <= 145) or
        (41 <= e["x"] <= 73 and 149 <= e["y"] <= 154) for e in print_writes),
        "原版印字畫布寫入越出兩行")
    expected = (("before-title-ink", "after-title-before-subtitle", 205, (32, 141, 81, 145)),
                ("after-title-before-subtitle", "after-second-ink", 116, (41, 149, 73, 154)))
    for before, after, count, bbox in expected:
        require(diff(images[("click-v3-a", before)], images[("click-v3-a", after)]) == (count, bbox),
                "原版兩行墨跡差分不符：" + after)
    for snap in SNAPS:
        value = images[("click-v3-a", snap)]
        require(value == images[("click-v3-b", snap)] == images[("click-v3-control", snap)] and
                sha(value) == a["snapshots"][snap]["canvas_sha256"], "畫布快照或控制組不符：" + snap)
    require(original["NAMES.TXT"][0xC22:0xC2E] == b"Conquistador" and
            original["LABELS.TXT"][0x8B8:0x8C0] == b"Moderate", "同文異來源誤判")


def self_test(rows, images, original, inputs):
    def both(reports, edit):
        for name in ("click-v3-a", "click-v3-b"):
            edit(reports[name])

    def rejected(label, change):
        changed = copy.deepcopy(rows)
        pictures = dict(images)
        source = dict(original)
        events = dict(inputs)
        change(changed, pictures, source, events)
        try:
            validate(changed, pictures, source, events)
        except ValueError:
            return
        raise AssertionError("未拒絕負例：" + label)

    rejected("錯原版", lambda r, i, o, e: o.__setitem__(
        "NAMES.TXT", o["NAMES.TXT"][:0xC22] + b"X" + o["NAMES.TXT"][0xC23:]))
    rejected("錯玩家事件", lambda r, i, o, e: e.__setitem__("click", b"{}"))
    rejected("DOS 載入失配", lambda r, i, o, e: both(
        r, lambda report: report["file_loads"][0].update({"matched": False})))
    rejected("缺來源讀取", lambda r, i, o, e: both(r, lambda report: report["reads"].clear()))
    rejected("無監看狀態分歧", lambda r, i, o, e: r["click-v3-control"]["state"].update({"ticks": -1}))
    rejected("畫布多一點", lambda r, i, o, e: i.__setitem__(
        ("click-v3-a", "after-second-ink"),
        i[("click-v3-a", "after-second-ink")][:20000] +
        bytes([i[("click-v3-a", "after-second-ink")][20000] ^ 1]) +
        i[("click-v3-a", "after-second-ink")][20001:]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        rows, images, original, inputs = load(args.reports, args.game)
    except FileNotFoundError as exc:
        print("SKIP 77：缺合法原版或本機收據：", exc)
        raise SystemExit(77)
    validate(rows, images, original, inputs)
    if args.self_test:
        self_test(rows, images, original, inputs)
    print("PASS：第三張卡片原版載入、印字、雙重播、控制及六組負例")


if __name__ == "__main__":
    main()
