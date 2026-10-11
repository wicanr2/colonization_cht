#!/usr/bin/env python3
"""規格060 DRAFT：從已驗欄位清冊產生不含譯文或像素的編譯索引。"""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS_SHA = "2be579643f7655f635a6bec4adcbae9a1fb11a4734d3b8daf80177934e15b61d"
FONT_SHA = "b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a"
LICENSE_SHA = "6a73f9541c2de74158c0e7cf6b0a58ef774f5a780bf191f2d7ec9cc53efe2bf2"


def render(fields, registry):
    if hashlib.sha256(fields).hexdigest() != FIELDS_SHA:
        raise ValueError("欄位證據指紋不同")
    rows = json.loads(fields)["fields"]
    index = json.loads(registry)
    if len(rows) != 64 or len({r["file"] for r in rows}) != 64 or \
            index["schema"] != 1 or index["total"] != 2022 or len(index["tables"]) != 13:
        raise ValueError("欄位或文本清冊形態不同")
    q = lambda value: json.dumps(value, ensure_ascii=False)
    out = '''// 規格060 DRAFT。由tools/build_language_resource_index.py產生；不要手動修改。
// 僅保留來源鍵、檔名、幾何與指紋；譯文仍以TSV為準。
package main

import (
    _ "embed"
    "encoding/json"
    "fmt"
)

//go:embed language-catalogs.json
var draftCatalogRegistry []byte

func draftIndexedRequirements() (draftBundleRequirements, error) {
    needs := draftBundleRequirements{
'''
    for key, value in [("Font", FONT_SHA), ("License", LICENSE_SHA), ("Fields", FIELDS_SHA)]:
        out += f"        {key}: {q(value)},\n"
    out += "        Masks: map[string]draftMaskRequirement{\n"
    catalogs = {"card": "nation-card-fragments.zh-Hant.tsv", "cards-rest": "nation-card-fragments.zh-Hant.tsv",
                "intro": "nation-introduction.zh-Hant.tsv", "help": "help-bilingual.tsv", "static": "static-overlay.zh-Hant.tsv"}
    for row in rows:
        safe = row["safe"]
        rect = [safe["Min"]["X"] * 4, safe["Min"]["Y"] * 4, safe["Max"]["X"] * 4, safe["Max"]["Y"] * 4]
        if not 0 <= rect[0] < rect[2] <= 1280 or not 0 <= rect[1] < rect[3] <= 800:
            raise ValueError("欄位安全區越界")
        out += (f"            {q(row['file'])}: {{ID: {q(row['id'])}, Safe: [4]int{{{', '.join(map(str, rect))}}}, "
                f"Shadow: {row['shadow_offset']}, Layered: {str(row['group'] in ['intro', 'help']).lower()}, "
                f"Catalog: {q(catalogs.get(row['group'], 'draft.zh-Hant.tsv'))}}},\n")
    out += '''        },
    }
    var index struct {
        Schema int `json:"schema"`
        Total int `json:"total"`
        Source string `json:"source_binding_sha256"`
        Tables []struct { File string `json:"file"` } `json:"tables"`
    }
'''
    out += f"    if hash(draftCatalogRegistry) != {q(hashlib.sha256(registry).hexdigest())} {{ return needs, fmt.Errorf(\"compiled catalog index mismatch\") }}\n"
    out += '''    if err := json.Unmarshal(draftCatalogRegistry, &index); err != nil { return needs, err }
    if index.Schema != 1 || index.Total != 2022 || len(index.Tables) != 13 { return needs, fmt.Errorf("compiled catalog index shape") }
    needs.Source = index.Source
    for _, table := range index.Tables { needs.Tables = append(needs.Tables, table.File) }
    return needs, nil
}
'''
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--fields", type=Path, required=True)
    p.add_argument("--output", type=Path, default=ROOT / "tools/language_resource_index.go")
    p.add_argument("--check", action="store_true")
    a = p.parse_args()
    if not Path("/.dockerenv").is_file():
        raise ValueError("只能在Docker產生或核對索引")
    output = a.output.resolve()
    if not output.is_relative_to(ROOT) or not output.parent.is_dir() or \
            output.parent.stat().st_uid != os.getuid() or (output.exists() and output.stat().st_uid != os.getuid()):
        raise ValueError("輸出必須位於既有專案目錄且擁有者相同")
    # gofmt採標準輸入，不建立暫存或覆寫研究來源。
    import subprocess
    content = subprocess.run(["gofmt"], input=render(a.fields.read_bytes(), (ROOT / "tools/language-catalogs.json").read_bytes()),
                             text=True, capture_output=True, check=True, timeout=30).stdout
    if a.check:
        if output.read_text() != content:
            raise ValueError("編譯索引與已驗欄位證據不同")
    else:
        output.write_text(content)
    print("VERIFIED_LANGUAGE_RESOURCE_INDEX" if a.check else "GENERATED_LANGUAGE_RESOURCE_INDEX", hashlib.sha256(content.encode()).hexdigest())


if __name__ == "__main__":
    main()
