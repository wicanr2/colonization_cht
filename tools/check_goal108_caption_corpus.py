#!/usr/bin/env python3
"""核對十張開場字幕的十一行譯稿來源與 dosgolem 實際印字。"""

import argparse
import hashlib
import json
import pathlib
import re
import sys

from validate_translation_draft import Invalid, read_catalog, validate_sources


GAME_SHA = "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a"
INPUT_SHA = "a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
VERSION = "goal107-post-caption-audit-v1"
# (GAME.TXT 標記位移、原文行位移／長度／SHA-256)。位址均為檔案位移。
BLOCKS = (
    (0x153B0, ((0x153CC, 63, "9f1a8fcf633289c9ad2185268a41573a2482b72bcdbea62df1b6ec12b57a06ce"),)),
    (0x1540F, ((0x1542B, 42, "9679dcf58b49e5dcf34b664fe4c10ec8735fc71e5711d708d5ff6ab1dc482b6f"),
               (0x15457, 11, "61ecc08ec7bfc5a2614b5266ff25b78f7b26378fb30bcbadb776dc58927f3868"))),
    (0x15466, ((0x15482, 41, "264829c19d39ef54d4e35f06f6421bc8df8b6cd25cb699bfa28a3d68ca596255"),)),
    (0x154AF, ((0x154CB, 55, "83f7d54872bc54541c0bcae2076f517154168953361a42bbe097e67cfaf54ebc"),)),
    (0x15506, ((0x15522, 27, "c46adc07e89dc853f75888b5799426773196b67a07978b4b256ea97ebdbac65b"),)),
    (0x15541, ((0x1555D, 26, "a099cfe2640fbb5304bb0bd7475f44a4fcdba76d06eaa5da8e1c280721df72f3"),)),
    (0x1557B, ((0x15597, 62, "2e90b5e3be0abbf53a26fbdabf6392265dd43e06d122264b8c5e385588c22e2e"),)),
    (0x155D9, ((0x155F5, 42, "9023a3d04fbf8edf3e2ca845a38d3b7e003b2df5a6f080176207cae3d59f266b"),)),
    (0x15623, ((0x1563F, 53, "4c00972091554381550b2883dfcf2d92cbf7365b52597fd229367bb95937489c"),)),
    (0x15678, ((0x15695, 14, "d5c69fbd3d8dc11c9f790ecdb8c9ecf66f352f6f17c81b269a0d8f00a6b0a019"),)),
)
# (印字首末指令數、展開後位元組長度、SHA-256)，不是原始檔案位移。
PRINTS = (
    (88_689_021, 88_754_524, 61, "c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6"),
    (199_163_156, 199_222_763, 55, "0cfc5ab07ea787de0d84826366302ef1810044e8e34094a67b557daeda9fc937"),
    (307_692_550, 307_731_762, 37, "bbbbdd6e1a3539314ea015d7764af6ed6451f5a4534c169bba1f882ce560d767"),
    (427_644_076, 427_695_982, 48, "c6e372958c2d98a8b53e59d58dac57d7de1eeaab01e145b71c40b9fcf6e373d5"),
    (536_921_911, 536_948_638, 25, "ee8b6569c2bba4b57ce2133fd1f0ac9fe52f62db4f5621ce73fa40898f1a78d5"),
    (645_341_112, 645_366_503, 24, "b8cb47fdb1c13aa34a0fce30e333a1232d7991ded6a9daedd8b210cf24cc27c2"),
    (753_776_679, 753_839_172, 59, "53f1e7991791074f9e5a1f54f9a40abc9b4b1957ff168e01d502f2f52b21eda6"),
    (862_217_356, 862_259_926, 40, "0d3ec9226fae1b8b33356f299e2726dc109db51904c5409d1c71b7a3360abf13"),
    (970_656_140, 970_708_177, 51, "65e7fb3ace0f3a3b37f53d6410ee6de05bacab86a2ead7e37e81608fd4bbca5a"),
    (1_079_093_013, 1_079_105_807, 12, "cff475dbcfaf09ea9edf40efa8a40350da7eba8e0f0f0983175eef16e479480e"),
)


def need(condition, message):
    if not condition:
        raise Invalid(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(game, catalog, reports, font=None):
    source = game / "GAME.TXT"
    if not source.is_file():
        return {"result": "SKIP", "reason": "合法原版 GAME.TXT 缺失"}
    data = source.read_bytes()
    need(sha(data) == GAME_SHA, "GAME.TXT 原版版本不符")
    rows = read_catalog(catalog)
    missing = sorted({row["source_file"] for row in rows if not (game / row["source_file"]).is_file()})
    if missing:
        return {"result": "SKIP", "reason": "合法原版缺少：" + "、".join(missing)}
    validate_sources(rows, game)
    by_id = {row["candidate_id"]: row for row in rows}
    caption_rows = []
    for number, (marker, lines) in enumerate(BLOCKS, 1):
        label = f"@BUILD{number}".encode("ascii")
        need(data[marker:marker + len(label)] == label, f"{label.decode()} 標記位移不符")
        for offset, length, digest in lines:
            line = data[offset:offset + length]
            key = f"GAME.TXT:0x{offset:08X}"
            need(data[offset - 2:offset] == b"\r\n" and
                 data[offset + length:offset + length + 2] == b"\r\n" and
                 line.startswith(b"^^") and len(line) == length and sha(line) == digest,
                 key + " 原始行位移、控制符或雜湊不符")
            need(key in by_id and by_id[key]["source_bytes_sha256"] == digest and
                 by_id[key]["status"] == "draft" and
                 any("\u4e00" <= char <= "\u9fff" for char in by_id[key]["zh_hant"]),
                 key + " 譯稿缺行或來源不符")
            caption_rows.append(by_id[key])

    prefixes = [reports / f"england-no-extra-1350m-{suffix}"
                for suffix in ("explore", "b", "control")]
    a_raw, b_raw, control_raw = (pathlib.Path(f"{prefix}.json").read_bytes()
                                 for prefix in prefixes)
    need(a_raw == b_raw, "dosgolem 雙重播報告不同")
    observed, control = json.loads(a_raw), json.loads(control_raw)
    need(observed["version"] == control["version"] == VERSION and
         observed["nation"] == control["nation"] == "england" and
         observed["input_sha256"] == control["input_sha256"] == INPUT_SHA and
         observed["input_hashes"]["GAME.TXT"] == GAME_SHA and
         observed["control"] is False and control["control"] is True and
         not control["print_reads"], "dosgolem 版本、輸入或無監看控制不符")
    for field in ("route", "sources", "transfers", "samples", "opened", "key_events"):
        need(observed[field] == control[field], f"dosgolem 監看改變原版狀態：{field}")
    events = [item for item in observed["print_reads"]
              if 85_000_000 <= item["step"] < 1_180_000_000 and
              item["cs_ip"] == "0D21:00C6"]
    groups = []
    for item in events:
        if not groups or item["step"] - groups[-1][-1]["step"] > 1_000_000:
            groups.append([])
        groups[-1].append(item)
    need(len(groups) == len(PRINTS), "原版實際字幕段數不符")
    for number, (group, (first, last, length, digest)) in enumerate(zip(groups, PRINTS), 1):
        need(group[0]["step"] == first and group[-1]["step"] == last and
             len(group) == length * 2 and
             all(item["value"] == 0 for item in group[1::2]) and
             sha(bytes(item["value"] for item in group[::2])) == digest,
             f"@BUILD{number} 原版實際印字不符")
    result = {"result": "PASS", "game_sha256": GAME_SHA,
            "dosgolem_report_sha256": sha(a_raw),
            "catalog_sha256": sha(catalog.read_bytes()),
            "caption_count": len(BLOCKS),
            "source_line_count": sum(len(lines) for _, lines in BLOCKS),
            "draft_total": len(rows),
            "scope": "僅逐行草稿與原版印字；未驗正式中文畫面"}
    if font is not None:
        need(sha(font.read_bytes()) == FONT_SHA, "字幕字型版本不符")
        from fontTools.ttLib import TTFont
        cmap = TTFont(font).getBestCmap()
        glyphs = set("".join(re.sub(r"%STRING[0-9]+", "", row["zh_hant"]).replace("^", "")
                             for row in caption_rows))
        missing_glyphs = sorted(char for char in glyphs if ord(char) not in cmap)
        need(not missing_glyphs,
             "字幕字型缺字：" + "、".join(f"{char}(U+{ord(char):04X})" for char in missing_glyphs))
        result["font_sha256"] = FONT_SHA
        result["covered_glyphs"] = len(glyphs)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=pathlib.Path, required=True)
    parser.add_argument("--catalog", type=pathlib.Path,
                        default=pathlib.Path(__file__).resolve().parents[1] / "text/draft.zh-Hant.tsv")
    parser.add_argument("--reports", type=pathlib.Path, required=True)
    parser.add_argument("--font", type=pathlib.Path, help="固定 Cubic 11 TTF；提供時檢查十一行字形")
    parser.add_argument("--out", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        result = check(args.game, args.catalog, args.reports, args.font)
        if args.out:
            need(args.out.parent.is_dir(), "收據輸出目錄不存在")
            args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                encoding="utf-8")
    except (Invalid, OSError, ValueError, KeyError, TypeError, UnicodeError, ImportError) as error:
        print("驗證失敗：" + str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    sys.exit(main())
