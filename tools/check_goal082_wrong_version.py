#!/usr/bin/env python3
"""在容器暫存目錄驗證第二張卡片前端的原版雜湊拒絕閘門。"""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile


REQUIRED = ("OPENING.EXE", "VICEROY.EXE", "GAME.TXT", "LABELS.TXT", "NAMES.TXT")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--target", choices=REQUIRED, default="NAMES.TXT",
                        help="只改動暫存副本中的單一原版檔案；預設維持目標082")
    args = parser.parse_args()
    if not all((args.game / name).is_file() for name in REQUIRED):
        print("SKIP：原版輸入不完整")
        return 77
    with tempfile.TemporaryDirectory(prefix="colonization-goal082-version-") as temp:
        temp_dir = Path(temp)
        for name in REQUIRED:
            (temp_dir / name).symlink_to((args.game / name).resolve())
        # 僅覆蓋暫存目錄的符號連結；絕不寫入原版檔案。
        (temp_dir / args.target).unlink()
        original = (args.game / args.target).read_bytes()
        (temp_dir / args.target).write_bytes(bytes((original[0] ^ 1,)) + original[1:])
        prefix = temp_dir / "rejected"
        result = subprocess.run(
            [str(args.binary), "--root", str(temp_dir), "--out", str(prefix)],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        passed = (
            result.returncode == 2
            and "原版版本不符" in result.stderr
            and not list(temp_dir.glob("rejected.*"))
        )
        receipt = {
            "result": "PASS" if passed else "FAIL",
            "scope": f"僅暫存 {args.target} 單位元組異動；原版輸入唯讀",
            "exit_code": result.returncode,
            "version_rejected": "原版版本不符" in result.stderr,
            "stderr": result.stderr.strip()[:500],
            "output_files": [p.name for p in temp_dir.glob("rejected.*")],
        }
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
