#!/usr/bin/env python3
"""十七欄重烘驗證器的正反例；暫存變造只在容器 /tmp。"""

import argparse
import base64
import json
import shutil
import tempfile
from pathlib import Path
from types import SimpleNamespace

from bake_nation_card_a_from_font import bake
from verify_goal103_font_rebuild import filename, verify


def rejected(call, error, label):
    try:
        call()
    except error:
        return
    raise AssertionError(label + " 未拒絕")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("game", "font", "catalog", "card_catalog", "new",
                 "old_standard", "old_card"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    args = parser.parse_args()
    good = SimpleNamespace(**vars(args))
    assert verify(good)["field_count"] == 17
    with tempfile.TemporaryDirectory(prefix="colonization-goal103-") as temporary:
        root = Path(temporary)

        wrong_font = root / "wrong.ttf"
        wrong_font.write_bytes(args.font.read_bytes() + b"not the fixed version")
        rejected(lambda: verify(SimpleNamespace(**{**vars(args), "font": wrong_font})),
                 ValueError, "錯 TTF")

        wrong_catalog = root / "wrong.tsv"
        wrong_catalog.write_bytes(args.catalog.read_bytes() + b"\n")
        rejected(lambda: verify(SimpleNamespace(**{**vars(args), "catalog": wrong_catalog})),
                 ValueError, "錯主譯稿")

        rejected(lambda: verify(SimpleNamespace(**{**vars(args), "game": root / "absent"})),
                 FileNotFoundError, "缺原版")

        changed = root / "masks"
        changed.mkdir()
        for path in args.new.glob("*.json"):
            shutil.copyfile(path, changed / path.name)
        assert len(list(changed.glob("*.json"))) == 17
        missing = changed / filename("NAMES.TXT:0x000008EA")
        missing.unlink()
        rejected(lambda: verify(SimpleNamespace(**{**vars(args), "new": changed})),
                 ValueError, "缺旗卡欄")
        shutil.copyfile(args.new / missing.name, missing)

        payload = json.loads(missing.read_bytes())
        alpha = bytearray(base64.b64decode(payload["alpha"], validate=True))
        alpha[-1] ^= 1
        payload["alpha"] = base64.b64encode(alpha).decode("ascii")
        missing.write_text(json.dumps(payload, ensure_ascii=False) + "\n", encoding="utf-8")
        rejected(lambda: verify(SimpleNamespace(**{**vars(args), "new": changed})),
                 ValueError, "改動 Alpha")

        output = root / "bake"
        output.mkdir()
        bake_args = SimpleNamespace(output=output, font=wrong_font,
                                    game=args.game, catalog=args.card_catalog)
        rejected(lambda: bake(bake_args), ValueError, "烘製器錯 TTF")
        assert not list(output.iterdir()), "錯 TTF 留下部分字模"
        bake_args.font = args.font
        bake_args.catalog = wrong_catalog
        rejected(lambda: bake(bake_args), ValueError, "烘製器錯旗卡 TSV")
        assert not list(output.iterdir()), "錯 TSV 留下部分字模"
    print("PASS：十七欄正例；錯 TTF、錯 TSV、缺原版、缺欄、改動 Alpha 均拒絕且不留部分字模")


if __name__ == "__main__":
    main()
