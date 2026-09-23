#!/usr/bin/env python3
"""目標096：獨立核對姓名提示來源、畫布事件與無觀測控制。"""

import argparse
import hashlib
import json
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


parser = argparse.ArgumentParser()
parser.add_argument("--reports", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()

raw_a = (args.reports / "a11.json").read_bytes()
raw_b = (args.reports / "b11.json").read_bytes()
require(raw_a == raw_b, "兩次冷啟動探針收據不一致")
a = json.loads(raw_a)
control = json.loads((args.reports / "control11.json").read_bytes())
require(a["version"] == "goal096-prompt-guard-v1" and not a["control"], "探針版本或模式不符")
require(control["control"] and not control["source_reads"] and
        not control["glyph_reads"] and not control["glyph_contexts"] and
        not control["canvas_writes"], "控制組不獨立")
require(a["input_sha256"] == control["input_sha256"] ==
        "d5a0902056911fa13a93f7f5466c27c795d3c12600214ff8be71e2be95ea3fec",
        "真視窗輸入指紋不符")
require(a["input_hashes"] == control["input_hashes"], "原版檔案指紋不一致")
require(a["samples"].keys() - {"prompt_diff"} == control["samples"].keys(),
        "控制組檢查點不同")
for label, state in control["samples"].items():
    require(a["samples"][label] == state, f"探針擾動原版狀態：{label}")

reads = a["source_reads"]
require(len(reads) == 6 and sum(x["matches_full_visible_and_newline"] for x in reads) == 1,
        "來源候選不是唯一完整提示")
source = reads[-1]
visible = b"Please Enter Your Name."
require(source["matches_full_visible_and_newline"] and
        bytes.fromhex(source["candidate_prefix_hex"]) == visible + b"\n" and
        source["first_value"] == ord("P") and source["cs_ip"] == "0E2D:09F4" and
        source["linear"] == 0x2B072 and a["source_read_step"] == source["step"] and
        source["opcode_hex"] == "acaa3a" and
        source["segments"][3] * 16 + source["registers"][6] == 0x2B072,
        "完整提示來源讀取不符")
require(all(not x["matches_full_visible_and_newline"] for x in reads[:-1]),
        "其他候選誤認為姓名提示")
require(a["source_read_step"] == 48_862_601 and a["display_step"] == 48_864_672 and
        a["first_glyph_step"] == 48_887_201 and a["after_step"] == 48_912_046,
        "來源、顯示及畫布相位不符")
require(a["source_before_steps"] == [48_862_601, 63_371_349] and
        a["source_before_step"] == a["source_read_step"] and
        [x["opened_count"] for x in a["source_before_events"]] == [53, 54] and
        all(x["canvas_sha256"] ==
            "f31602f9a239a4f83fd6e27e644384009d628517185aeb80bb248479e67d0e71"
            and x["palette_sha256"] ==
            "898669705f7ec9ad40dd0bfa57eadd2a922a033478ee0a5d1a8ad602ddc2ce65"
            and x["last_opened"] == "GAME.TXT" and x["video_mode"] == 19
            for x in a["source_before_events"]),
        "同文再次出現的來源事件未以開檔世代區分")
require(a["display_tail_byte"] == 0 and
        all(a["samples"][label]["display_tail_byte"] == 0
            for label in ("55m", "58m", "61m")),
        "顯示緩衝不是完整的 NUL 結尾字串")
glyphs = a["glyph_reads"]
require(bytes(x["value"] for x in glyphs) == visible and
        all(x["cs_ip"] == "0D21:00C6" for x in glyphs) and
        a["display_step"] < glyphs[0]["step"] <= glyphs[-1]["step"] < a["after_step"],
        "逐字畫布來源不符")
require(len(a["glyph_contexts"]) == len(glyphs) and
        all(x["opcode_hex"] == "368a17" and
            x["segments"][2] * 16 + x["registers"][3] == 0x2A864
            for x in a["glyph_contexts"]),
        "逐字讀取不是已證實的 SS:BX 運算元")

writes = a["canvas_writes"]
prompt_writes = [x for x in writes if x["step"] <= a["after_step"]]
require(len(prompt_writes) == 415 and
        all(x["cs_ip"] == "0D21:012C" and 100 <= x["x"] < 219 and
            85 <= x["y"] < 98 and x["old"] != x["new"] for x in prompt_writes),
        "提示畫布寫入數量、常式或安全區不符")
diff = a["samples"]["prompt_diff"]
require(diff["changed_pixels"] == 415 and diff["outside_safe"] == 0 and
        diff["bbox_inclusive"] == [104, 88, 214, 96] and
        diff["new_colors"] == {"128": 81, "47": 135, "68": 199},
        "提示印前後差分不符")
require(a["samples"]["55m"]["canvas_sha256"] ==
        "4182cf7454d507e9dda76e4d81bde65ded7508314c5c518892508f8cddfb1b37",
        "姓名畫面未落在既有同狀態收據")
safe_hashes = [a["samples"][label]["prompt_safe_sha256"] for label in
               ("55m", "58m", "61m", "66m", "70m")]
require(safe_hashes[0] == safe_hashes[1] == safe_hashes[2] and
        safe_hashes[3] == safe_hashes[4] != safe_hashes[0],
        "姓名輸入或 Enter 離頁的提示區變化不符")
for label in ("55m", "58m", "61m"):
    require(a["samples"][label]["source_matches_prompt"] and
            a["samples"][label]["display_matches_prompt"] and
            a["samples"][label]["opened_count"] == 53, f"姓名畫面來源失效：{label}")
for label in ("66m", "70m"):
    require(not a["samples"][label]["source_matches_prompt"] and
            not a["samples"][label]["display_matches_prompt"] and
            a["samples"][label]["opened_count"] == 54, f"離頁未失效：{label}")
require(a["opened"] == control["opened"] and a["opened"][-1] == "GAME.TXT",
        "檔案開啟序列不符")

result = {"result": "PASS", "scope": "完整提示來源、顯示逐字、415點畫布及同狀態控制；尚非正式覆蓋",
          "probe_sha256": sha(raw_a), "control_sha256": sha((args.reports / "control11.json").read_bytes()),
          "source_read_step": a["source_read_step"], "display_step": a["display_step"],
          "first_glyph_step": a["first_glyph_step"], "after_step": a["after_step"]}
require(args.out.parent.is_dir(), "輸出目錄不存在")
args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
print("目標096 來源至畫布及無觀測控制：PASS")
