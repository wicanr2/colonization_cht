#!/usr/bin/env python3
"""規格 009 的可丟棄離線原型；不是即時轉譯器，不寫入遊戲或快照。"""
import argparse
import csv
import hashlib
import json
import struct
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

VERSIONS = {
    "OPENING.EXE": "3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39",
    "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
}
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
FRAME_SHA = "559df11e83c1fb01e2d844a4379af6369e279bf4ea7b4b30c95cbf2d4062c4a1"
PALETTE_SHA = "243ca37172f22fbfb4182d6d495ad129b9a524f093d67f0d1c5e6d215434ee5f"
BEFORE_SHA = "da6844a1f1d9c64254f23051e27bc33e5b1f5316c861e8d1beff69dbb90235c2"
AFTER_SHA = "cf70e897c2e9ae93b4e2babb1e6ce7daa34d53525cc02d8b9e59308a2d3b115b"
CANVAS, PIXELS, SCALE = 0x2CAE0, 64000, 4
SAFE = (86 * SCALE, 107 * SCALE, 232 * SCALE, 114 * SCALE)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def cmap_coverage(data):
    """僅解 Unicode cmap 4/12；glyph 0 算缺字，未知／破損格式拒絕。"""
    def u16(o):
        return struct.unpack_from(">H", data, o)[0]

    def u32(o):
        return struct.unpack_from(">I", data, o)[0]

    cmap = None
    for i in range(u16(4)):
        o = 12 + i * 16
        if data[o:o + 4] == b"cmap":
            cmap = u32(o + 8)
            if cmap + u32(o + 12) > len(data):
                raise ValueError("cmap 長度越界")
            break
    if cmap is None:
        raise ValueError("缺少 cmap")
    result = set()
    for i in range(u16(cmap + 2)):
        o = cmap + 4 + i * 8
        platform, encoding, sub = u16(o), u16(o + 2), cmap + u32(o + 4)
        if not (platform == 0 or (platform == 3 and encoding in (1, 10))):
            continue
        fmt = u16(sub)
        if fmt == 12:
            end = sub + u32(sub + 4)
            groups = u32(sub + 12)
            if end > len(data) or sub + 16 + groups * 12 > end:
                raise ValueError("cmap 12 長度越界")
            for j in range(groups):
                start, stop, glyph = struct.unpack_from(">III", data, sub + 16 + j * 12)
                if stop < start or stop > 0x10FFFF:
                    raise ValueError("cmap 12 範圍錯誤")
                result.update(range(start + (glyph == 0), stop + 1))
        elif fmt == 4:
            end = sub + u16(sub + 2)
            count = u16(sub + 6) // 2
            ends, starts = sub + 14, sub + 16 + count * 2
            deltas, offsets = starts + count * 2, starts + count * 4
            if end > len(data) or offsets + count * 2 > end:
                raise ValueError("cmap 4 長度越界")
            for j in range(count):
                start, stop = u16(starts + j * 2), u16(ends + j * 2)
                delta, offset = u16(deltas + j * 2), u16(offsets + j * 2)
                for cp in range(start, stop + 1):
                    if cp == 0xFFFF:
                        continue
                    if offset:
                        pos = offsets + j * 2 + offset + (cp - start) * 2
                        if pos + 2 > end:
                            raise ValueError("glyph 索引越界")
                        glyph = u16(pos)
                        glyph = (glyph + delta) & 0xFFFF if glyph else 0
                    else:
                        glyph = (cp + delta) & 0xFFFF
                    if glyph:
                        result.add(cp)
    if not result:
        raise ValueError("沒有支援的 Unicode cmap")
    return result


def fit_text(text, font, width, height):
    """同一字型量雙軸；溢出採尾端省略，無法安全顯示則回 None。"""
    def fits(s):
        box = font.getbbox(s)
        return box[2] - box[0] <= width and box[3] - box[1] <= height

    if not text or "\n" in text or "\r" in text:
        return None
    if fits(text):
        return text
    if not fits("…"):
        return None
    while text:
        text = text[:-1]
        if fits(text + "…"):
            return text + "…"
    return None


def original_image(indexed, palette):
    if len(indexed) != PIXELS or len(palette) != 768 or max(palette) > 63:
        raise ValueError("無法解碼原始畫面／DAC 色盤")
    image = Image.frombytes("P", (320, 200), indexed)
    image.putpalette(bytes((v << 2) | (v >> 4) for v in palette))
    return image.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)


@dataclass
class Inputs:
    indexed: bytes
    palette: bytes
    before: bytes
    after: bytes
    event_log: dict
    files: dict
    translation: str
    translation_source: str  # 來源 bytes 的 SHA-256，不保存原文。
    font_path: Path
    translation_sha: str
    source_byte_length: int


def compose(inputs, enabled=True):
    """所有 gate 在恢復背景前完成；失敗輸出等於原版最近鄰放大圖。"""
    base = original_image(inputs.indexed, inputs.palette)
    receipt = {"prototype": True, "applied": False, "reason": "", "scale": SCALE,
               "frame_sha256": sha(inputs.indexed), "palette_sha256": sha(inputs.palette),
               "translation_file_sha256": inputs.translation_sha, "safe_rect": SAFE}

    def fallback(reason):
        receipt["reason"] = reason
        return base, receipt

    if not enabled:
        return fallback("disabled")
    if not inputs.translation:
        return fallback("missing-translation")
    if any(sha(inputs.files.get(k, b"")) != v for k, v in VERSIONS.items()):
        return fallback("wrong-version")
    if sha(inputs.indexed) != FRAME_SHA or sha(inputs.palette) != PALETTE_SHA:
        return fallback("wrong-frame-or-palette")
    source = inputs.files["GAME.TXT"][0x1B0:].splitlines()[0]
    if inputs.translation_source != sha(source) or inputs.source_byte_length != len(source):
        return fallback("wrong-translation-source")
    events = inputs.event_log.get("events", [])
    expected = {"entry_ip": "937C:0538", "entry_step": 21384086,
                "return_ip": "937C:1D50", "return_step": 21402955,
                "source": "6F16:00DF", "source_hex": source.hex()}
    if (len(events) != 1 or any(events[0].get(k) != v for k, v in expected.items())
            or inputs.event_log.get("exited") is not False
            or inputs.event_log.get("end", 0) < expected["return_step"]):
        return fallback("incomplete-or-wrong-event")
    if len(inputs.before) != 1 << 20 or len(inputs.after) != 1 << 20:
        return fallback("wrong-memory-size")
    if sha(inputs.before) != BEFORE_SHA or sha(inputs.after) != AFTER_SHA:
        return fallback("wrong-event-memory")
    ptr = 0x6F16 * 16 + 0xDF
    if any(mem[ptr:ptr + len(source)] != source for mem in (inputs.before, inputs.after)):
        return fallback("wrong-runtime-source")
    before = inputs.before[CANVAS:CANVAS + PIXELS]
    after = inputs.after[CANVAS:CANVAS + PIXELS]
    changed = [i for i in range(PIXELS) if before[i] != after[i]]
    if (len(changed) != 180 or any(after[i] != 254 for i in changed)
            or any(not (86 <= i % 320 <= 176 and 107 <= i // 320 <= 112) for i in changed)
            or any(inputs.indexed[i] != after[i] for i in changed)):
        return fallback("changed-pixels-not-confirmed-or-occluded")
    try:
        font_data = inputs.font_path.read_bytes()
        if sha(font_data) != FONT_SHA:
            return fallback("wrong-font")
        coverage = cmap_coverage(font_data)
        if any(ord(c) not in coverage for c in inputs.translation):
            return fallback("missing-glyph")
        font = ImageFont.truetype(str(inputs.font_path), 24)
        text = fit_text(inputs.translation, font, SAFE[2] - SAFE[0], SAFE[3] - SAFE[1])
        if text is None:
            return fallback("text-does-not-fit")
        if any(ord(c) not in coverage for c in text):
            return fallback("missing-glyph")
    except (OSError, ValueError, struct.error) as error:
        receipt["detail"] = str(error)
        return fallback("font-unavailable")
    restored = bytearray(inputs.indexed)
    for i in changed:
        restored[i] = before[i]
    output = original_image(bytes(restored), inputs.palette)
    box = font.getbbox(text)
    position = (SAFE[0] - box[0], SAFE[1] - box[1])
    color = tuple((v << 2) | (v >> 4) for v in inputs.palette[254 * 3:255 * 3])
    ImageDraw.Draw(output).text(position, text, font=font, fill=color)
    receipt.update(applied=True, reason="applied-offline-prototype", text=text,
                   truncated=text != inputs.translation, changed_pixels=len(changed),
                   font_sha256=sha(font_data), glyph_bbox=box,
                   ink_rect=(SAFE[0], SAFE[1], SAFE[0] + box[2] - box[0],
                             SAFE[1] + box[3] - box[1]))
    return output, receipt


def load_inputs(events_path, game, translations, font):
    events_path, game, translations, font = map(Path, (events_path, game, translations, font))
    draft = translations.read_bytes()
    rows = list(csv.DictReader(draft.decode("utf-8").splitlines(), delimiter="\t"))
    selected = [r for r in rows if r["candidate_id"] == "GAME.TXT:0x000001B0"
                and r["source_file"] == "GAME.TXT"
                and int(r["byte_offset"], 16) == 0x1B0]
    row = selected[0] if len(selected) == 1 else {}
    if row and row.get("source_sha256") != VERSIONS["GAME.TXT"]:
        row = {}
    def read(suffix):
        return Path(str(events_path) + suffix).read_bytes()
    return Inputs(read(".idx"), read(".pal"), read(".event0.before"), read(".event0.after"),
                  json.loads(events_path.read_text()), {name: (game / name).read_bytes() for name in VERSIONS},
                  row.get("zh_hant", ""), row.get("source_bytes_sha256", ""), font, sha(draft),
                  int(row.get("source_byte_length", 0)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--events", required=True)
    parser.add_argument("--game", required=True)
    parser.add_argument("--translations", default=str(Path(__file__).resolve().parents[1] / "text/draft.zh-Hant.tsv"),
                        help="版本化譯文草稿（不含原文，預設 text/draft.zh-Hant.tsv）")
    parser.add_argument("--font", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--off", action="store_true")
    args = parser.parse_args()
    inputs = load_inputs(args.events, args.game, args.translations, args.font)
    output, receipt = compose(inputs, not args.off)
    output.save(args.output)
    receipt["output_sha256"] = sha(Path(args.output).read_bytes())
    Path(args.output + ".json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
