#!/usr/bin/env python3
"""獨立核對 Game Options 第2／3／5／6列同焦點原版畫面。"""

import argparse
import hashlib
import json
from pathlib import Path

from check_goal101_nation_intro import FILE_SHA, INPUT_SHA
from check_goal112_options_source import MENU_SHA, SCREEN_SHA
from check_goal117_same_focus import CANVAS_BEFORE, LABELS, PALETTES


FIXTURES = {
    "second": ("goal118-second-then-first.inputs.json", "c5cd75914394f83bbec7f97ec242850e613630537d1e37fe0b6ddef84e798b9c", 71, 83),
    "third": ("goal118-third-then-first.inputs.json", "f17aaa5398abded23152ee8a9c9e4cd4bd0dff8156a962b20f46d60bb82c0562", 83, 95),
    "fifth": ("goal118-fifth-then-first.inputs.json", "296bf4af579a183b083952e1b035bb169f1ebcd61ee42b109f8a95802dd790de", 107, 119),
    "sixth": ("goal118-sixth-then-first.inputs.json", "9977be8d84ee9e3f35836920ae7f3bb30bd15f6fff536d9222b60bf49296b2f2", 119, 131),
}
BASELINE_JSON_SHA = "2a9fc9def5f756f863dd9e889aecb97b2fab6a2919421ed986c7e31671ac49c2"
BASELINE_FINAL_INDEXED = "7b6bf011f389933ce5a09553f10a1f069a6d3bf5f26fe7978bf130897e80f450"
BASELINE_FINAL_CANVAS = "b88bf062e32c968caeb6856a16b74b8f60924b232b322d3ad90a4502929bd008"
EXPECTED = {
    "second": {"receipt": "f2f4d4059f3f08af2e3844c478c8e52b2835f3c08101f2ac73111cad6a3803ac",
               "mid": ("2bb91cdb6a693985334686f19e76eaee7025b8ce3f9cbf049e8a142c1a7592a1", "d6db0b1158dd493e66fcfb5cee3e798c262c30ffba99ca13a5400d34a6f4d291"),
               "final": ("31eea5f66483af83d2980234e7cc699be8b5c7953453738b624b161f89f400b4", "3d2ae3e2bab67581450812e706405e7bd5e43cc6cf5cdb8d202e3ba7ee7b47c4"),
               "mid_counts": (3305, 1659), "icon": (76, 149, 47)},
    "third": {"receipt": "1527b67ac8d91e371c55e465b65f05e79a0b803bd915312ab9bde8f23bad5f48",
              "mid": ("fe8a4c5a1356a41730c0465b7c9168576c8d84266f0a0a033299134945d16c26", "4ff05f6733e66ad6e355627f7c6fe97acdc535e0190371a6001b370d84123726"),
              "final": ("f93263e24943f7c5c91da6b5fcd54dee721d822e8a08b84f01049a46ce305a87", "0778d814f72ce8ad635520cc959cc0982c2737b90d4da901b2e8e4198363359f"),
              "mid_counts": (3350, 1704), "icon": (88, 47, 149)},
    "fifth": {"receipt": "593f4c8ae93148217f7908742764a2beca5160d2b8d0191357caf8f405da5c2e",
              "mid": ("7f1e00c0ee6afb6bad1534d1162c4c80518b6ad191ff2d8bb8763cae48b0d8d7", "61a02479fc5e9d997b3feace754e292fedd34dedf16f2d7f029da8b9dc49623f"),
              "final": ("e22f8ab08fbe69044a34c02db56eefa1842fe01a9e75d764ec2ebf04332b196d", "7828d8d7270fcba0a0c553440876e9e00c4eb5d835f61b4fdba863a105bbdf13"),
              "mid_counts": (3459, 1813), "icon": (112, 149, 47)},
    "sixth": {"receipt": "6790fc9d236213ec95bd14994ae4b1608adfcce93e9ff1988a40287ca6af0eb6",
              "mid": ("ee67c76e3874059b61faa6470eb752c322b0455cffa0c19fd38a01d23dfd9b39", "3c9a33a55e3beb4299f2824e7eb0c01436d4038212177de204e29f39d14b3b65"),
              "final": ("4ab8d3b687dd1182749c7a5440807f708b27d664daa4724e29a50a1bebcdd40d", "95b03bbbf045a2a38230524045dd7f7e2f4e1df9480a9f284f84dabdde69512d"),
              "mid_counts": (3338, 1692), "icon": (124, 149, 47)},
}


def need(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def raw(prefix, label, sample):
    result = {}
    for suffix, field, size in (("idx", "indexed_sha256", 64000),
                                ("canvas", "canvas_sha256", 64000),
                                ("pal", "palette_sha256", 768)):
        data = Path(f"{prefix}.{label}.{suffix}").read_bytes()
        need(len(data) == size and sha(data) == sample[field],
             f"{prefix.name}/{label}: 原版 {suffix} 與收據不符")
        result[suffix] = data
    return result


def changes(left, right):
    need(len(left) == len(right) == 64000, "原版畫布尺寸不符")
    return [(i % 320, i // 320, a, b)
            for i, (a, b) in enumerate(zip(left, right)) if a != b]


def check(game, inputs, fixtures, reports, baseline):
    if not inputs.is_file() or not all((game / name).is_file()
                                       for name in (*FILE_SHA, "MENU.TXT")):
        return {"result": "SKIP", "reason": "合法原版或固定玩家輸入缺失"}
    for name, expected in (*FILE_SHA.items(), ("MENU.TXT", MENU_SHA)):
        need(sha((game / name).read_bytes()) == expected, "原版版本不符：" + name)
    need(sha(inputs.read_bytes()) == INPUT_SHA, "正常玩家開局輸入版本不符")
    for filename, expected, _, _ in FIXTURES.values():
        need(sha((fixtures / filename).read_bytes()) == expected,
             "玩家事件檔版本不符：" + filename)

    base_prefix = baseline / "baseline-a"
    base_bytes = Path(f"{base_prefix}.json").read_bytes()
    need(sha(base_bytes) == BASELINE_JSON_SHA,
         "目標117同焦點基線 JSON 版本不符")
    base_report = json.loads(base_bytes)
    need(base_report["samples"]["1300m"]["indexed_sha256"] == SCREEN_SHA and
         base_report["samples"]["1300m"]["canvas_sha256"] == CANVAS_BEFORE and
         base_report["samples"]["1375m"]["indexed_sha256"] == BASELINE_FINAL_INDEXED and
         base_report["samples"]["1375m"]["canvas_sha256"] == BASELINE_FINAL_CANVAS,
         "目標117基線畫面指紋不符")
    base = {label: raw(base_prefix, label, base_report["samples"][label])
            for label in LABELS}

    receipts = {}
    observations = {}
    for branch, (_, fixture_sha, target_lo, target_hi) in FIXTURES.items():
        prefixes = [reports / f"{branch}-{variant}"
                    for variant in ("a", "b", "control")]
        observed_bytes = Path(f"{prefixes[0]}.json").read_bytes()
        need(observed_bytes == Path(f"{prefixes[1]}.json").read_bytes(),
             branch + ": 雙冷啟動收據不一致")
        need(sha(observed_bytes) == EXPECTED[branch]["receipt"],
             branch + ": 原版收據指紋不符")
        observed = json.loads(observed_bytes)
        control = json.loads(Path(f"{prefixes[2]}.json").read_bytes())
        for report, is_control in ((observed, False), (control, True)):
            need(report["version"] == "goal112-game-options-source-v2" and
                 report["control"] is is_control and report["nation"] == "england" and
                 report["next_enter"] is True and
                 report["after_b"] == report["after_follow"] == "enter" and
                 report["follow_until"] == 1_400_000_000 and
                 report["input_sha256"] == INPUT_SHA and
                 report["game_inputs_sha256"] == fixture_sha and
                 report["input_hashes"]["MENU.TXT"] == MENU_SHA and
                 len(report["opened"]) == 94,
                 branch + ": 原版、探針或玩家路徑不符")
        need(not control["print_reads"] and not control["writers"] and
             not control["option_source_reads"], branch + ": 控制組仍有監看")
        for field in ("route", "sources", "transfers", "samples", "opened",
                      "key_events", "game_inputs"):
            need(observed[field] == control[field],
                 branch + ": 監看擾動原版狀態：" + field)
        scene = {}
        for label in LABELS:
            sample = observed["samples"][label]
            need(sample["step"] == int(label[:-1]) * 1_000_000,
                 branch + "/" + label + ": 步數不符")
            if label in PALETTES:
                need(sample["palette_sha256"] == PALETTES[label],
                     branch + "/" + label + ": 色盤相位不符")
            if label in ("1325m", "1350m", "1375m", "1400m"):
                indexed, canvas = EXPECTED[branch]["mid" if label in ("1325m", "1350m") else "final"]
                need(sample["indexed_sha256"] == indexed and
                     sample["canvas_sha256"] == canvas,
                     branch + "/" + label + ": 固定畫面指紋不符")
            for prefix in prefixes:
                actual = raw(prefix, label, sample)
                if prefix == prefixes[0]:
                    scene[label] = actual
        need(scene["1300m"] == base["1300m"],
             branch + ": 點擊前原版畫面不同")
        need(observed["samples"]["1300m"] == base_report["samples"]["1300m"],
             branch + ": 點擊前 CPU／RAM／時間狀態不同")
        need(scene["1325m"]["idx"] == scene["1350m"]["idx"] and
             scene["1325m"]["canvas"] == scene["1350m"]["canvas"] and
             scene["1375m"]["idx"] == scene["1400m"]["idx"] and
             scene["1375m"]["canvas"] == scene["1400m"]["canvas"],
             branch + ": 固定取樣相位未穩定")
        for label in ("1375m", "1400m"):
            need(scene[label]["pal"] == base[label]["pal"],
                 branch + "/" + label + ": 同時點色盤不同")
        mid = changes(base["1325m"]["canvas"], scene["1325m"]["canvas"])
        first = sum(59 <= y < 71 for _, y, _, _ in mid)
        target = sum(target_lo <= y < target_hi for _, y, _, _ in mid)
        need(len(mid) == first + target and
             (len(mid), first, target) ==
             (EXPECTED[branch]["mid_counts"][0], 1646,
              EXPECTED[branch]["mid_counts"][1]),
             branch + ": 暫態差分越出第一列或被點列")
        final = changes(base["1375m"]["canvas"], scene["1375m"]["canvas"])
        indexed = changes(base["1375m"]["idx"], scene["1375m"]["idx"])
        y, old, new = EXPECTED[branch]["icon"]
        expected_icon = [(73, y, old, new), (74, y, old, new),
                         (73, y + 1, old, new), (74, y + 1, old, new)]
        need(final == indexed == expected_icon,
             branch + ": 同焦點底層與合成索引差分不一致")
        receipts[branch] = sha(observed_bytes)
        observations[branch] = {"mid_pixels": len(mid), "first_row_pixels": first,
                                "target_row_pixels": target,
                                "mid_indexed_sha256": observed["samples"]["1325m"]["indexed_sha256"],
                                "mid_canvas_sha256": observed["samples"]["1325m"]["canvas_sha256"],
                                "final_indexed_sha256": observed["samples"]["1375m"]["indexed_sha256"],
                                "final_canvas_sha256": observed["samples"]["1375m"]["canvas_sha256"],
                                "final_delta": final}
    return {"result": "PASS", "receipt_sha256": receipts,
            "baseline_sha256": sha(base_bytes), "observations": observations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, required=True)
    parser.add_argument("--inputs", type=Path, required=True)
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent)
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.game, args.inputs, args.fixtures,
                       args.reports, args.baseline)
    except (OSError, KeyError, IndexError, TypeError, ValueError) as exc:
        parser.exit(1, f"FAIL：{exc}\n")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 77 if result["result"] == "SKIP" else 0


if __name__ == "__main__":
    raise SystemExit(main())
