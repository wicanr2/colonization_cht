#!/usr/bin/env python3
"""組裝本機顯示設定原型；原版畫面只寫入 workplace，不進版控。"""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from PIL import Image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--zh", type=Path, required=True)
    parser.add_argument("--english", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent.parent
    target = args.output.resolve()
    if not target.is_relative_to(root / "workplace"):
        parser.error("含原版像素的原型只能輸出至本專案 workplace")
    if target.exists():
        parser.error("不覆寫既有原型")
    if not target.parent.is_dir():
        parser.error("先建立並核對輸出目錄擁有者")
    data = {"images": {}, "provenance": {"kind": "disposable-interface-prototype", "images": {}}}
    for locale, source in (("zh-Hant", args.zh), ("en", args.english)):
        image = Image.open(source)
        if image.size != (1280, 800):
            parser.error(f"{source} 的畫布不是 1280×800")
        raw = source.read_bytes()
        data["images"][locale] = {"url": "data:image/png;base64," + base64.b64encode(raw).decode("ascii")}
        data["provenance"]["images"][locale] = {
            "path": str(source), "sha256": hashlib.sha256(raw).hexdigest(), "size": list(image.size)
        }
    template = Path(__file__).with_name("prototype_display_settings.html").read_text(encoding="utf-8")
    data["provenance"]["template_sha256"] = hashlib.sha256(template.encode()).hexdigest()
    encoded = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    target.write_text(template.replace("__PROTOTYPE_DATA__", encoded), encoding="utf-8")
    print(json.dumps({"path": str(target), "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
