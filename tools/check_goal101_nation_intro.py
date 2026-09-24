#!/usr/bin/env python3
"""獨立驗證四國介紹的 dosgolem 正常玩家路徑、雙頁與離頁收據。"""

import argparse
import hashlib
import json
import os
from pathlib import Path

from validate_nation_introduction_corpus import GAME_SHA, SECTIONS, check as check_catalog


INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
FILE_SHA = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "GAME.TXT": GAME_SHA,
    "NAMES.TXT": "4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061",
    "LABELS.TXT": "e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204",
    "NATIONS.PIK": "bd31e62d7b7652e6903aaea76b1641f11d5333ff6a6da13fd26411c9f080bf54",
}
NATIONS = ("england", "france", "spain", "netherlands")
COORDS = ((155, 50), (255, 50), (155, 150), (255, 150))
SAMPLES = ("55m", "56m", "57m", "60m", "65m", "70m", "75m")
# 固定原版印字收據。bbox 為原版 320×200 畫布半開範圍。
EXPECTED = {
    "england": ((833, "25f3dd22b2d753adc9f66c76c4e8c4dabe0474600d996b6128881552f1122d23", 14193, (10, 20, 305, 179), "2908e03488fa8c0c4ec531bc75d444a0d0cc4ce49df0a3f2421790a67342f75a"),
                (170, "33cadaf8f05359be9c7f3ade81ab3d41ed3583e0c9b3361f9fda9d335e9d84a9", 2932, (10, 75, 292, 124), "010a42d99723c76a55f63f4a0f2b5aabfb5e197b29b2efceef2af49488fc17ee")),
    "france": ((794, "7285983b0263b270b7e952a78aecc40e0fa682e45302ae088371b493da0a258b", 13412, (10, 25, 304, 174), "aa987cee149ab9503b919dccd6747f57c87c94cbdb026fcdd1edb070ad7aafe5"),
               (207, "9018be96a5ab5eb08fcb830beaa493a6090b6aec2eecdd682594065d6a6971d9", 3438, (10, 70, 308, 129), "19c0622b683673f929daedda9dc6b61bfc06d2e048165f376c15af28bb2dbb0a")),
    "spain": ((953, "37df0dda5ca2f142501142b572ff8b7e3e51ec20d2baa7131aaaa236449b4fbe", 16103, (10, 10, 305, 189), "ef33921c006988d0424eb6663e5ac9e651917cffd2a870143b0b0e902f9c71ee"),
              (180, "3dfc072784c1f2728e8a1f514623c54b8320b3185407b4a1ed74c29809ce850e", 3168, (10, 75, 292, 124), "d64964077fb020aeeb5a623417e01479e62d0abf934a4bdb01496e3d836d8d48")),
    "netherlands": ((957, "a13e855de4b202af656d76d6319fd0ecd5a87a81115e27df66b4dae67f938bbd", 16401, (10, 10, 305, 189), "dd14bdfac94b86213c121ad40f344f9f56c69f5324fdcee96758a1979b351e0c"),
                    (299, "6fa75f110995ae368395a39d8b6ee4c8c44ab25ed72ce63342a913cb3e8b8d01", 5262, (10, 65, 307, 134), "3bb0d4025c53716b320231c1631b2dd1e3b98c9fd32dd2c4b29e4d937e34c021")),
}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def visible_source(block):
    parts = []
    for line in block.decode("cp437").splitlines():
        if line.startswith("@") or not line or line.startswith("^^_"):
            continue
        if line.startswith(("^^", "__")):
            line = line[2:]
        parts.append(line.replace("{", "").replace("}", ""))
    return "".join(parts).encode("cp437")


def printed(record, start, end):
    events = [event for event in record["print_reads"]
              if event["cs_ip"] == "0D21:00C6" and start <= event["step"] < end]
    raw = bytes(event["value"] for event in events)
    need(len(raw) % 2 == 0 and all(raw[i] == 0 for i in range(1, len(raw), 2)) and
         all(event["linear"] == (0x2A862 if i % 2 == 0 else 0x2A863)
             for i, event in enumerate(events)), "原版逐字印字讀取模式不符")
    return raw[::2]


def main(args):
    need(args.output.parent.is_dir() and args.output.parent.stat().st_uid == os.getuid(),
         "收據輸出目錄不存在或擁有者不符")
    for name, expected_sha in FILE_SHA.items():
        need(sha((args.game / name).read_bytes()) == expected_sha,
             f"原版檔案版本不符：{name}")
    game = (args.game / "GAME.TXT").read_bytes()
    need(sha(args.inputs.read_bytes()) == INPUT_SHA, "正常玩家輸入版本不符")
    catalog = check_catalog(args.game / "GAME.TXT", args.catalog)
    seen_flags, seen_names, seen_a, seen_b = set(), set(), set(), set()
    result = []
    for index, name in enumerate(NATIONS):
        base = args.reports / name
        a_bytes, b_bytes = (Path(str(base) + "-a.json").read_bytes(),
                            Path(str(base) + "-b.json").read_bytes())
        need(a_bytes == b_bytes, f"{name}: 兩次冷啟動不相同")
        record = json.loads(a_bytes)
        control = load(Path(str(base) + "-control.json"))
        need(record["control"] is False and control["control"] is True and
             record["nation"] == control["nation"] == name and
             record["next_enter"] is control["next_enter"] is True and
             record["after_b"] == control["after_b"] == "none" and
             record["input_sha256"] == control["input_sha256"] == INPUT_SHA and
             record["input_hashes"] == control["input_hashes"] == FILE_SHA and
             record["route"] == control["route"] and
             record["sources"] == control["sources"] and
             record["transfers"] == control["transfers"] and
             record["samples"] == control["samples"] and
             record["opened"] == control["opened"] and
             not control["print_reads"] and not control["writers"],
             f"{name}: 觀測／無觀測控制狀態不同")
        route = record["route"]
        need((route["selected_x"], route["selected_y"]) == COORDS[index],
             f"{name}: 滑鼠座標不是已驗旗卡")
        seen_flags.add(route["nation_indexed_sha256"])
        seen_names.add(route["name_indexed_sha256"])
        first, second = SECTIONS[index * 2:index * 2 + 2]
        source_offsets = [item["offset"] for item in record["sources"]]
        need(len(source_offsets) == 5 and source_offsets[0] == first[1] and
             source_offsets[3] == second[1] and
             [item["file_offset"] for item in record["transfers"]] == source_offsets * 2 and
             all(item["match"] and item["name"].upper() == "GAME.TXT"
                 for item in record["transfers"]),
             f"{name}: 原版檔案標記的 DOS 讀入未閉合")
        for label in SAMPLES:
            sample = record["samples"][label]
            for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                        ("canvas", "canvas_sha256", 64000),
                                        ("pal", "palette_sha256", 768)):
                original = Path(str(base) + f"-a.{label}.{suffix}").read_bytes()
                need(len(original) == size and sha(original) == sample[field] and
                     original == Path(str(base) + f"-b.{label}.{suffix}").read_bytes() and
                     original == Path(str(base) + f"-control.{label}.{suffix}").read_bytes(),
                     f"{name}/{label}: 實際索引／畫布／色盤與雙次或控制不同")
        for phase, (section, lo, hi, stable_labels) in enumerate((
                (first, 55_000_000, 65_000_000, ("60m", "65m")),
                (second, 65_000_000, 75_000_000, ("70m", "75m")))):
            key, start, end = section[:3]
            output = printed(record, lo, hi)
            source = visible_source(game[start:end])
            if name == "spain" and phase == 1:
                # 原版節保留字面 50%%；執行期 DOS 格式化顯示為 50%。
                need(source.count(b"%%") == 1, "西班牙百分號來源數量不符")
                source = source.replace(b"%%", b"%")
            need(source.replace(b" ", b"") == output.replace(b" ", b""),
                 f"{name}/{key}: 檔案節與實際印字不符")
            expected_length, expected_print_sha, ink_count, bbox, screen_sha = EXPECTED[name][phase]
            writer = record["writers"]["first/0D21:012C" if phase == 0 else "second/0D21:012C"]
            need(len(output) == expected_length and sha(output) == expected_print_sha and
                 writer["count"] == ink_count and tuple(writer["bbox"]) == bbox and
                 record["samples"][stable_labels[0]]["indexed_sha256"] ==
                 record["samples"][stable_labels[1]]["indexed_sha256"] == screen_sha,
                 f"{name}/{key}: 印字、畫布或頁面穩定相位不符")
            (seen_a if phase == 0 else seen_b).add(screen_sha)
        result.append({"nation": name, "selected": COORDS[index],
                       "first_section": first[0], "second_section": second[0],
                       "first_print_sha256": EXPECTED[name][0][1],
                       "second_print_sha256": EXPECTED[name][1][1],
                       "first_indexed_sha256": EXPECTED[name][0][4],
                       "second_indexed_sha256": EXPECTED[name][1][4],
                       "report_sha256": sha(a_bytes)})
    need(all(len(group) == 4 for group in (seen_flags, seen_names, seen_a, seen_b)),
         "四國選取、姓名或 A/B 畫面未分開")
    branch = {}
    for action in ("wait", "enter", "esc"):
        record = load(args.reports / f"france-after-{action}.json")
        need(record["nation"] == "france" and record["after_b"] == action and
             record["samples"]["75m"] == load(args.reports / "france-a.json")["samples"]["75m"] and
             record["samples"]["80m"]["indexed_sha256"] ==
             record["samples"]["85m"]["indexed_sha256"],
             f"法國 B 頁後 {action}：共同起點或畫面穩定性不符")
        branch[action] = record
    b_screen = EXPECTED["france"][1][4]
    need(branch["wait"]["samples"]["85m"]["indexed_sha256"] == b_screen and
         branch["wait"]["samples"]["85m"]["opened_count"] == 55,
         "B 頁無輸入控制自行離頁")
    follow = branch["enter"]["samples"]["85m"]["indexed_sha256"]
    need(follow != b_screen and follow == branch["esc"]["samples"]["85m"]["indexed_sha256"] and
         all(branch[action]["samples"]["85m"]["opened_count"] == 60 and
             branch[action]["opened"][-5:] ==
             ["KINGLSS1.PIK", "FRANCE1.SS", "KING1.SS", "FONTKING.FF", "GAME.TXT"]
             for action in ("enter", "esc")) and
         branch["enter"]["samples"]["85m"]["memory_sha256"] !=
         branch["esc"]["samples"]["85m"]["memory_sha256"],
         "B 頁 Enter/ESC 的可見離頁或內部差異與觀測不符")
    receipt = {"result": "PASS", "scope": "四國八節正常玩家原版選國、A/B 印字與畫布；法國 B 後按鍵離頁",
               "game_sha256": GAME_SHA, "input_sha256": INPUT_SHA,
               "catalog_sha256": catalog["catalog_sha256"], "nations": result,
               "after_b": {"no_input_stays": True, "enter_and_esc_visible_screen_equal": True,
                           "enter_and_esc_memory_equal": False, "follow_screen_sha256": follow},
               "limitations": "沒有中文長文覆蓋；ESC 與 Enter 內部狀態不同，不推論同一規則或存檔"}
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8")
    print("PASS：四國八節正常路徑原版印字／畫布、雙重播、無觀測控制及 B 後按鍵分支")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    main(parser.parse_args())
