#!/usr/bin/env python3
"""在Docker內壓縮／還原workplace/reports歷史紀錄及舊ELF，核對原始內容SHA-256。

還原單檔：python3 tools/evidence_storage.py restore workplace/reports/.../gui.json
列出封存：python3 tools/evidence_storage.py list workplace/reports
還原整個舊驗證目錄：python3 tools/evidence_storage.py restore workplace/reports/<目錄>
"""

import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import stat


ROOT = Path(__file__).resolve().parents[1] / "workplace/reports"
EXTENSIONS = {".json", ".jsonl", ".owners"}
PROGRAM_EXTENSIONS = {"", ".test"}
BLOCK = 1024 * 1024


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def paths(path, root=ROOT):
    path = Path(path).absolute()
    root = root.resolve()
    if path.suffix == ".gz":
        path = path.with_suffix("")
    if path.suffix not in EXTENSIONS | PROGRAM_EXTENSIONS:
        raise ValueError("只接受歷史紀錄或無副檔名／.test的ELF執行檔")
    if not path.parent.resolve().is_relative_to(root) or path.is_symlink():
        raise ValueError("路徑必須位於本專案workplace/reports，且不能是符號連結")
    path = path.parent.resolve() / path.name
    return path, path.with_name(path.name + ".gz"), path.with_name(path.name + ".gz.meta.json")


def compact(path, root=ROOT):
    path, packed, metadata = paths(path, root)
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or (before.st_uid, before.st_gid) != (os.getuid(), os.getgid()):
        raise ValueError("來源必須是目前使用者擁有的一般檔案")
    program = path.suffix in PROGRAM_EXTENSIONS
    if program:
        with path.open("rb") as stream:
            if stream.read(4) != b"\x7fELF" or not before.st_mode & 0o111:
                raise ValueError("無副檔名與.test來源必須是可執行ELF")
    if packed.exists() or metadata.exists():
        raise FileExistsError("已存在壓縮檔或清冊，保留原檔")
    temporary = packed.with_name(packed.name + ".compressing")
    meta_temp = metadata.with_name(metadata.name + ".writing")
    source_hash = hashlib.sha256()
    total = 0
    created_temp = created_meta = False
    try:
        with temporary.open("xb") as output:
            created_temp = True
            with gzip.GzipFile(filename="", mode="wb", fileobj=output, compresslevel=1, mtime=0) as target:
                with path.open("rb") as source:
                    while block := source.read(BLOCK):
                        source_hash.update(block)
                        total += len(block)
                        target.write(block)
            output.flush()
            os.fsync(output.fileno())
        verified = hashlib.sha256()
        restored_size = 0
        with gzip.open(temporary, "rb") as source:
            while block := source.read(BLOCK):
                verified.update(block)
                restored_size += len(block)
        after = path.stat()
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ) or total != before.st_size or restored_size != total or verified.digest() != source_hash.digest():
            raise ValueError("原始檔變動或壓縮往返驗證失敗，保留原檔")
        row = {
            "format_version": 1,
            "kind": "ELF" if program else "data",
            "original": str(path.relative_to(Path(root).resolve())),
            "sha256": source_hash.hexdigest(),
            "bytes": total,
            "mode": stat.S_IMODE(before.st_mode),
            "uid": before.st_uid,
            "gid": before.st_gid,
            "atime_ns": before.st_atime_ns,
            "mtime_ns": before.st_mtime_ns,
            "compressed_sha256": digest(temporary),
            "compressed_bytes": temporary.stat().st_size,
            "original_allocated_bytes": before.st_blocks * 512,
            "original_links": before.st_nlink,
        }
        with meta_temp.open("x") as stream:
            created_meta = True
            json.dump(row, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        # Atomic, non-overwriting publication. The original is removed last.
        os.link(temporary, packed)
        temporary.unlink()
        os.link(meta_temp, metadata)
        meta_temp.unlink()
        path.unlink()
        row["compressed_allocated_bytes"] = packed.stat().st_blocks * 512
        return row
    finally:
        if created_temp:
            temporary.unlink(missing_ok=True)
        if created_meta:
            meta_temp.unlink(missing_ok=True)


def restore(path, root=ROOT):
    path, packed, metadata = paths(path, root)
    if path.exists():
        raise FileExistsError("原路徑已存在，不覆寫")
    for item in (packed, metadata):
        info = item.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid():
            raise ValueError("壓縮檔與清冊必須是目前使用者擁有的一般檔案")
    row = json.loads(metadata.read_text())
    if row["format_version"] != 1 or row["original"] != str(path.relative_to(Path(root).resolve())):
        raise ValueError("清冊與原路徑不符")
    if packed.stat().st_size != row["compressed_bytes"] or digest(packed) != row["compressed_sha256"]:
        raise ValueError("壓縮檔指紋不符，保留封存")
    temporary = path.with_name(path.name + ".restoring")
    restored_hash = hashlib.sha256()
    total = 0
    created_temp = False
    try:
        with temporary.open("xb") as output:
            created_temp = True
            with gzip.open(packed, "rb") as source:
                while block := source.read(BLOCK):
                    if total == 0 and path.suffix in PROGRAM_EXTENSIONS and not block.startswith(b"\x7fELF"):
                        raise ValueError("還原內容不是ELF，保留封存")
                    total += len(block)
                    if total > row["bytes"]:
                        raise ValueError("還原大小超過清冊")
                    restored_hash.update(block)
                    output.write(block)
            output.flush()
            os.fsync(output.fileno())
        if total != row["bytes"] or restored_hash.hexdigest() != row["sha256"]:
            raise ValueError("還原內容指紋不符，保留封存")
        temporary.chmod(row["mode"])
        os.utime(temporary, ns=(row["atime_ns"], row["mtime_ns"]))
        os.link(temporary, path)
        temporary.unlink()
        packed.unlink()
        metadata.unlink()
        return row
    finally:
        if created_temp:
            temporary.unlink(missing_ok=True)


def restore_tree(folder, root=ROOT):
    folder = Path(folder).resolve()
    if not folder.is_relative_to(Path(root).resolve()):
        raise ValueError("只還原本專案workplace/reports")
    for metadata in sorted(folder.rglob("*.gz.meta.json")):
        original = metadata.with_name(metadata.name.removesuffix(".gz.meta.json"))
        yield restore(original, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["compact", "restore", "list"])
    parser.add_argument("paths", nargs="+", type=Path)
    args = parser.parse_args()
    if not Path("/.dockerenv").exists() or os.getuid() == 0:
        parser.error("必須在Docker內以非root使用者執行")
    for path in args.paths:
        if args.action == "list":
            folder = path.resolve()
            if not folder.is_relative_to(ROOT.resolve()):
                parser.error("只列出本專案workplace/reports")
            for metadata in sorted(folder.rglob("*.gz.meta.json")):
                row = json.loads(metadata.read_text())
                print(row["original"], row["bytes"], row["compressed_bytes"])
        elif args.action == "restore" and path.is_dir():
            for row in restore_tree(path):
                print(json.dumps(row, ensure_ascii=False))
        else:
            row = compact(path) if args.action == "compact" else restore(path)
            print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
