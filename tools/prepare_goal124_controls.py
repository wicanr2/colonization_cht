#!/usr/bin/env python3
"""從真視窗收據製作兩個只少一鍵的本機反向對照；不得冒充玩家實錄。"""

import argparse
import json
import os
from pathlib import Path


def prepare(source: Path, output: Path) -> dict[str, Path]:
    if not output.is_dir() or output.stat().st_uid != os.getuid():
        raise ValueError("本機對照輸出目錄不存在或擁有者不符")
    receipt = json.loads(source.read_text(encoding="utf-8"))
    if receipt.get("rejected") or not isinstance(receipt.get("end"), int):
        raise ValueError("真視窗輸入被拒絕或缺結束步數")
    events = receipt.get("inputs")
    if not isinstance(events, list) or [event.get("kind") for event in events].count("left") != 1 or [event.get("kind") for event in events].count("escape") != 1:
        raise ValueError("真視窗必須恰有一筆左鍵及一筆 Esc")
    result = {}
    for kind in ("left", "escape"):
        path = output / f"without-{kind}.inputs.json"
        if path.exists():
            raise ValueError(f"不覆寫既有對照：{path}")
        candidate = {"inputs": [event for event in events if event["kind"] != kind],
                     "end": receipt["end"]}
        path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        result[kind] = path
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    for kind, path in prepare(args.inputs, args.output).items():
        print(f"只移除 {kind} 的本機對照：{path}")
