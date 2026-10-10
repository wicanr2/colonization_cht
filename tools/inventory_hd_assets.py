#!/usr/bin/env python3
"""研究用 SS 盤點。原版與外部解碼器唯讀，輸出限於本專案 workplace。"""

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import sys

from PIL import Image, ImageDraw, ImageFont, __version__ as pillow_version


ROOT = Path(__file__).resolve().parent.parent
DECODER_COMMIT = "8c30544b51d1b4ab68f3a465784239c24b660e24"
DECODER_MANIFEST = "340f980355615cbe88659b72748296657982b4802ade1d41eebcc21d84af6e18"
FOCUS = {"BUILDING.SS", "PHYS0.SS", "ICONS.SS", "TERRAIN.SS"}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-root", type=Path, required=True)
    parser.add_argument("--decoder-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to((ROOT / "workplace").resolve()), "輸出必須位於 workplace")
    require(not output.exists(), "拒絕覆寫已有輸出")
    require(output.parent.is_dir(), "先建立並核對輸出父目錄")
    require(output.parent.stat().st_uid == os.getuid(), "輸出父目錄擁有者不符")
    require(args.game_root.is_dir() and args.decoder_root.is_dir(), "原版或解碼器目錄不存在")
    manifest_bytes = (args.decoder_root / "source-manifest.json").read_bytes()
    require(digest(manifest_bytes) == DECODER_MANIFEST, "解碼器清冊版本不符")
    manifest = json.loads(manifest_bytes)
    require(manifest["commit"] == DECODER_COMMIT, "解碼器 commit 不符")
    for name, expected in manifest["files_sha256"].items():
        require(digest((args.decoder_root / name).read_bytes()) == expected, f"解碼器檔案失配：{name}")
    sys.path.insert(0, str(args.decoder_root.resolve()))
    import ss
    from madspack import read_madspack
    from palette import read_palette_col, read_palette_rex

    sources = sorted(args.game_root.glob("*.SS"))
    require(bool(sources), "找不到實際 SS 原版輸入")
    output.mkdir()
    records, failures = [], []
    label_font = ImageFont.truetype("DejaVuSans.ttf", 14)
    for source in sources:
        record = {"file": source.name, "sha256": digest(source.read_bytes()), "frames": []}
        records.append(record)
        try:
            with contextlib.redirect_stdout(io.StringIO()):
                parts = read_madspack(str(source))
            require(len(parts) == 4, "SS 部分數不是四")
            header = ss.read_ss_header(parts[0])
            require(header.mode in (0, 1), "未知 SS 圖像模式")
            record.update(frame_count=header.nsprites, mode=header.mode,
                          part_sizes=[len(part.getbuffer()) for part in parts])
            require(header.nsprites * 16 <= record["part_sizes"][1], "圖像標頭表越界")
            palette = (read_palette_col if header.pflag else read_palette_rex)(parts[2])
            previews = []
            for ordinal in range(header.nsprites):
                sprite_header = ss.read_sprite_header(parts[1])
                frame = {"ordinal": ordinal, "header_offset_in_part1": ordinal * 16,
                         "data_offset_in_part3": sprite_header.start_offset,
                         "encoded_length_field": sprite_header.length,
                         "size": [sprite_header.width, sprite_header.height],
                         "padded_size_fields": [sprite_header.width_padded, sprite_header.height_padded]}
                record["frames"].append(frame)
                if sprite_header.width == 0 or sprite_header.height == 0:
                    frame["empty"] = True
                    continue
                require(sprite_header.width <= 4096 and sprite_header.height <= 4096, "異常圖像尺寸")
                require(0 <= sprite_header.start_offset < record["part_sizes"][3], "圖像資料起點越界")
                sprite = ss.read_sprite(sprite_header, parts[3], palette, mode=header.mode)
                pixels = sprite.tobytes()
                require(sprite.size == tuple(frame["size"]) and sprite.mode == "P", "解碼尺寸或模式失配")
                frame.update(decoded_indexed_sha256=digest(pixels),
                             opaque_pixels=sum(v != ss.transparency_index for v in pixels),
                             transparency_index=ss.transparency_index)
                if source.name in FOCUS:
                    sprite.info["transparency"] = ss.transparency_index
                    sprite.save(output / f"{source.name}.{ordinal:03}.png")
                    previews.append((ordinal, sprite.convert("RGBA")))
            if previews:
                cols, cell_w, cell_h = 8, 168, 168
                sheet = Image.new("RGB", (cols * cell_w, ((len(previews) + cols - 1) // cols) * cell_h), "#eee7d4")
                draw = ImageDraw.Draw(sheet)
                for n, (ordinal, sprite) in enumerate(previews):
                    x, y = n % cols * cell_w, n // cols * cell_h
                    scale = min(4, (cell_w - 8) / sprite.width, (cell_h - 34) / sprite.height)
                    size = (max(1, int(sprite.width * scale)), max(1, int(sprite.height * scale)))
                    preview = sprite.resize(size, Image.Resampling.NEAREST)
                    sheet.paste(preview, (x + (cell_w - size[0]) // 2, y + 28), preview)
                    draw.text((x + 5, y + 4), f"{ordinal:03} {sprite.width}x{sprite.height}", font=label_font, fill="#302a20")
                sheet.save(output / f"{source.name}.sheet.png")
        except Exception as error:
            record["error"] = f"{type(error).__name__}: {error}"
            failures.append(source.name)
    result = {"kind": "research-ss-inventory-not-runtime-asset-contract",
              "tools": {"python": platform.python_version(), "pillow": pillow_version,
                        "inventory_script_sha256": digest(Path(__file__).read_bytes()),
                        "decoder_commit": DECODER_COMMIT, "decoder_manifest_sha256": DECODER_MANIFEST},
              "address_spaces": {"header": "decoded MADSPACK part1 byte offset",
                                 "data": "decoded MADSPACK part3 byte offset; not EXE or runtime RAM"},
              "source_count": len(records), "frame_count": sum(r.get("frame_count", 0) for r in records),
              "failed_files": failures, "files": records,
              "limitations": "Decoded shape and hashes only. Gameplay identities, placement, animation and drawing calls remain unverified. Original pixel outputs stay private."}
    (output / "inventory.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ["source_count", "frame_count", "failed_files"]}))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
