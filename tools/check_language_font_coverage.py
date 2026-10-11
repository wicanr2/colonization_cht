#!/usr/bin/env python3
"""盤點四語全文、設定介面與保留ASCII的候選字型碼點覆蓋；不修改正式圖集。"""

import argparse
from collections import Counter, defaultdict
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess

from language_catalog import BaseCatalog, ROOT, load_translation, read_tsv, require, sha
from render_language_font_sample import HASHES


LOCALES = ("zh-Hant", "zh-Hans", "ja", "ko")
FACES = {"zh-Hant": (3, "Noto Sans CJK TC"), "zh-Hans": (2, "Noto Sans CJK SC"),
         "ja": (0, "Noto Sans CJK JP"), "ko": (1, "Noto Sans CJK KR")}
ASCII = set(range(0x20, 0x7f))


def character_sources(rows):
    result = defaultdict(set)
    for key, text in rows:
        # 保守保留來源文字中的全部可見碼點。ASCII包含模板標記與執行期保留文字，
        # 跳脫換行的字母也在其中；不把換行／定位碼當成需要墨跡的字元。
        codes = {ord(character) for character in text if ord(character) >= 0x20}
        codes.update(int(match, 16) for match in re.findall(r"\\+u([0-9a-fA-F]{4})", text))
        for code in codes:
            require(code <= 0x10ffff and not 0xd800 <= code <= 0xdfff, "字集含非法Unicode碼點")
            result[code].add(key)
    return result


def font_charset(path, index, expected_family):
    command = ["fc-query", "--index", str(index), "--format",
               "%{index}|%{family}|%{style}|%{fontversion}|%{charset}", str(path)]
    result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=30)
    fields = result.stdout.split("|")
    require(len(fields) == 5 and fields[0] == str(index), "字型face索引不符")
    require(fields[1].split(",")[0] == expected_family and fields[2] == "Regular", "字型區域或樣式不符")
    codes = set()
    for token in fields[4].split():
        require(re.fullmatch(r"[0-9a-f]+(?:-[0-9a-f]+)?", token), "字型碼點範圍格式不符")
        bounds = token.split("-")
        first, last = int(bounds[0], 16), int(bounds[-1], 16)
        require(0 <= first <= last <= 0x10ffff, "字型碼點範圍越界")
        codes.update(range(first, last + 1))
    require(codes and len(codes) <= 131072 and ASCII <= codes, "字型字集或ASCII覆蓋不完整")
    return codes, {"face_index": index, "family": fields[1], "style": fields[2],
                   "fontversion": int(fields[3]), "mapped_codepoints": len(codes),
                   "charset_sha256": sha(fields[4].encode()), "command": command}


def coverage(required, mapped, sources):
    missing = sorted(required - mapped)
    return {"required": len(required), "covered": len(required & mapped), "missing": len(missing),
            "all_codepoints_present": not missing,
            "missing_codepoints": [{"codepoint": f"U+{code:04X}",
                                     "sources": sorted(sources.get(code, []))} for code in missing]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cubic", required=True, type=Path)
    parser.add_argument("--noto", required=True, type=Path)
    parser.add_argument("--license", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(Path("/.dockerenv").is_file(), "請在Docker執行")
    require(shutil.which("fc-query") is not None, "缺少fontconfig的fc-query")
    for field, expected in HASHES.items():
        path = getattr(args, field)
        require(path.is_file() and sha(path.read_bytes()) == expected, f"字型或授權指紋不符：{field}")
    output = args.output.resolve()
    require(output.is_relative_to((ROOT / "workplace").resolve()) and not output.exists() and
            output.parent.is_dir() and output.parent.stat().st_uid == os.getuid(),
            "輸出須為新的workplace子目錄，父目錄擁有者須相同")
    base = BaseCatalog()
    frontend_data = (ROOT / "text/frontend-ui.tsv").read_bytes()
    _, frontend_rows = read_tsv(frontend_data, ("key", *LOCALES, "en"))
    require(len(frontend_rows) == len({row["key"] for row in frontend_rows}) == 17,
            "前端文字鍵缺少或重複")
    cubic, cubic_info = font_charset(args.cubic, 0, "Cubic 11")
    noto = {}
    for locale, (index, family) in FACES.items():
        noto[locale] = font_charset(args.noto, index, family)
    locales, input_sha = {}, {table["file"]: sha(data) for table, _, _, data in base.tables}
    for locale in LOCALES:
        if locale == "zh-Hant":
            entries = base.entries
            status = {"baseline": len(entries)}
        else:
            data = (ROOT / f"text/game.{locale}.tsv").read_bytes()
            entries, missing = load_translation(base, data, locale, False)
            require(not missing, "完整字形盤點不可使用部分譯稿")
            input_sha[f"game.{locale}.tsv"] = sha(data)
            status = dict(Counter(row["status"] for row in entries.values()))
        game_sources = character_sources((f"{catalog}:{key}", row["text"])
                                         for (catalog, key), row in entries.items())
        frontend_sources = character_sources((row["key"], row[locale]) for row in frontend_rows)
        game_required, frontend_required = set(game_sources) | ASCII, set(frontend_sources) | ASCII
        mapped, info = noto[locale]
        locales[locale] = {
            "game_rows": len(entries), "status_counts": status, "frontend_rows": len(frontend_rows),
            "game_codepoints": [f"U+{code:04X}" for code in sorted(game_required)],
            "frontend_codepoints": [f"U+{code:04X}" for code in sorted(frontend_required)],
            "game_charset_sha256": sha("".join(chr(code) for code in sorted(game_required)).encode()),
            "frontend_charset_sha256": sha("".join(chr(code) for code in sorted(frontend_required)).encode()),
            "cubic": {"game": coverage(game_required, cubic, game_sources),
                      "frontend": coverage(frontend_required, cubic, frontend_sources)},
            "noto": {"face": info, "game": coverage(game_required, mapped, game_sources),
                     "frontend": coverage(frontend_required, mapped, frontend_sources)},
        }
    version = subprocess.check_output(["fc-query", "--version"], stderr=subprocess.STDOUT, text=True).strip()
    report = {
        "kind": "candidate-codepoint-coverage-not-runtime-font-or-layout",
        "source_binding_sha256": base.registry["source_binding_sha256"],
        "input_sha256": input_sha, "frontend_sha256": sha(frontend_data), "font_sha256": HASHES,
        "script_sha256": sha(Path(__file__).read_bytes()), "python": platform.python_version(),
        "fontconfig": version, "cubic_face": cubic_info, "retained_ascii_count": len(ASCII),
        "locales": locales,
        "limits": ["Only Unicode codepoint mapping is checked; no glyph shapes, shaping or visual quality is proved.",
                   "Runtime variable values outside printable ASCII need their own inventory.",
                   "No original game, production atlases, per-field sizes, GUI or language switching are validated."],
    }
    output.mkdir()
    path = output / "coverage.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    require(path.stat().st_uid == os.getuid() and path.stat().st_gid == os.getgid(), "輸出擁有權不符")
    print(json.dumps({"report": str(path), "sha256": sha(path.read_bytes()),
                      "locales": {locale: {"game_codepoints": row["cubic"]["game"]["required"],
                                           "cubic_missing": row["cubic"]["game"]["missing"],
                                           "noto_missing": row["noto"]["game"]["missing"],
                                           "noto_frontend_missing": row["noto"]["frontend"]["missing"]}
                                  for locale, row in locales.items()}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
