#!/usr/bin/env python3
"""從已驗 A 版原型提取第一張旗卡兩欄本機字模；不複製原版畫素。"""

import argparse
import base64
import csv
import hashlib
import json
import os
from pathlib import Path


PREVIEW_SHA = "c3fbdabfab91e03ed5b3c4231dc35f8172ee947e85633cfd8e04f43aa76d55eb"
VERIFIED_SHA = "27b15fa6e225a157f4167d4509639d7d9cbb3f54af756274d6b0f4b76b7c3a44"
CATALOG_SHA = "d4cf454a4851778546b90a778f2966f9cfa6cc9e2a2b01fae9e261844d0f64b6"
PREVIEW_CATALOG_SHA = "dbca48dc62c04c2b1197b495c786411f18abd8996fd561a150ddc43d5ee5cfd4"
FONT_SHA = "8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c"
SOURCE_RECEIPT_SHA = "cc4221d50718fe981a8836672f7ee8eda07cb6b2fbc95894b5cacc3d0f63ec86"
FIELDS = {
    "upper": {"key": "NAMES.TXT:0x000008EA", "file": "NAMES.TXT", "offset": 0x8EA,
              "raw": b"England", "size": 21, "dimensions": (92, 19),
              "position": [578, 60], "safe": [125, 12, 190, 24],
              "mask_sha": "29ef858ea29168dba4d493f82429e8df3e7c4ba9be65eec511f7894987249d42"},
    "lower": {"key": "LABELS.TXT:0x000008F2", "file": "LABELS.TXT", "offset": 0x8F2,
              "raw": b"Immigration", "size": 25, "dimensions": (54, 23),
              "position": [597, 348], "safe": [125, 83, 190, 96],
              "mask_sha": "9bd96a25dcd72d9d10709279c3509e9ee93ead8fe0c900564a2c8c02aa5bf471"},
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def prepare(args):
    require(args.output.is_dir() and args.output.stat().st_uid == os.getuid(),
            "輸出目錄不存在或擁有者不符")
    require(sha(args.preview.read_bytes()) == PREVIEW_SHA and
            sha(args.verified.read_bytes()) == VERIFIED_SHA and
            sha(args.catalog.read_bytes()) == CATALOG_SHA,
            "A 版原型、PASS 收據或唯一片段 TSV 指紋不符")
    preview, verified = json.loads(args.preview.read_bytes()), json.loads(args.verified.read_bytes())
    require(preview["prototype"] is True and preview["variant"] == "faithful" and
            preview["font_sha256"] == FONT_SHA and
            preview["catalog_sha256"] == PREVIEW_CATALOG_SHA and
            preview["source_receipt_sha256"] == SOURCE_RECEIPT_SHA and
            verified["result"] == "PASS" and len(preview["layers"]) == 2,
            "A 版原型來源或逐像素驗證狀態不符")
    with args.catalog.open(encoding="utf-8", newline="") as handle:
        catalog = {row["candidate_id"]: row for row in csv.DictReader(handle, delimiter="\t")}
    require(len(catalog) == 4, "旗卡 TSV 筆數不符")
    outputs = []
    for layer in preview["layers"]:
        name = layer["name"]
        require(name in FIELDS and name not in outputs, "A 版欄位重複或未知")
        outputs.append(name)
        expect = FIELDS[name]
        row = catalog[expect["key"]]
        source = (args.game / expect["file"]).read_bytes()
        translated = row["zh_hant"] + ("：" if name == "upper" else "")
        mask = base64.b64decode(layer["mask"], validate=True)
        width, height = expect["dimensions"]
        require(row["source_file"] == expect["file"] and
                int(row["byte_offset"], 0) == expect["offset"] and
                row["status"] == "draft" and
                row["source_sha256"] == sha(source) and
                row["source_bytes_sha256"] == sha(expect["raw"]) and
                source[expect["offset"]:expect["offset"] + len(expect["raw"])] == expect["raw"] and
                layer["candidate_id"] == expect["key"] and
                layer["font_size"] == expect["size"] and
                (layer["ink_width"], layer["ink_height"]) == (width, height) and
                layer["position"] == expect["position"] and
                layer["safe"] == expect["safe"] and
                layer["color_index"] == 12 and layer["shadow_index"] == 0 and
                layer["shadow_dx"] == 4 and
                layer["translation_sha256"] == sha(translated.encode()) and
                len(mask) == width * height and sha(mask) == expect["mask_sha"],
                "來源、譯文、A 版字級／位置或字模不符：" + name)
        output = {"candidate_id": expect["key"],
                  "translation_sha256": layer["translation_sha256"],
                  "font_sha256": FONT_SHA, "font_size": expect["size"],
                  "width": width, "height": height, "alpha": layer["mask"],
                  "source_preview_sha256": PREVIEW_SHA,
                  "local_only": True}
        path = args.output / (expect["key"].replace(":", "-") + ".json")
        path.write_text(json.dumps(output, ensure_ascii=False) + "\n", encoding="utf-8")
    require(set(outputs) == set(FIELDS), "未取得精確兩欄 A 版字模")
    print("PASS：A 版兩欄來源固定字模已提取；只供本機正式驗收，不含原版畫素")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path, required=True)
    parser.add_argument("--verified", type=Path, required=True)
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args())
