#!/usr/bin/env python3
"""核對正常原住民攻擊確認的四語文字、HD人物與完整原文控制組。"""
import argparse
import gzip
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath
from collections import defaultdict

from PIL import Image

BINARY_SHA256 = "ed5b6a4e1824ab18bd0b100c4f1b5fc9423cf541503519b184f782ba8d2d9a52"
LAYOUT_REVIEW_SHA256 = "879aaf5916e3d63f50f9a5a030742fa89a4303b875491adf8b70bbec8c98ef0d"
BODY = "GAME.TXT:@WHACKINDIANS:0x000038BD"
CHOICES = BODY + "#2+list"
SOURCE_ID = "GAME.TXT:@WHACKINDIANS"
GUI = "r131-attack-formal-gui-r2"
CONTROL = "r131-attack-control-r2"
LOCALES = ("zh-Hant", "zh-Hans", "ja", "ko")


def raw(path):
    if path.is_file():
        return path.read_bytes()
    with gzip.open(path.with_name(path.name + ".gz"), "rb") as stream:
        return stream.read()


def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()


def read(path):
    return json.loads(raw(path))


def rect(box):
    return (box["Min"]["X"], box["Min"]["Y"], box["Max"]["X"], box["Max"]["Y"])


def color(palette, index):
    return tuple((v << 2) | (v >> 4) for v in palette[index * 3:index * 3 + 3]) + (255,)


def sample_path(folder, value):
    source = PurePosixPath(value)
    assert source.parent.name == GUI and source.name not in ("", ".", ".."), "sample path differs"
    result = folder / source.name
    assert result.is_file() and not result.is_symlink(), "sample is missing or linked"
    return result


def check(game, reports, repo):
    originals = {
        "GAME.TXT": "67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",
        "MSS1.SS": "7b580f7ebda2e03d34ca88c19942f6fd3707d044fceed2f8626e66aac62da6ea",
        "VICEROY.EXE": "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3",
    }
    for name, expected in originals.items():
        assert digest(game / name) == expected, "original fingerprint: " + name
    folder, control = reports / GUI, reports / CONTROL
    assert digest(reports / "r131-formal-window-r2") == BINARY_SHA256, "formal program differs"
    build = read(reports / "r131-formal-build-r2.json")
    assert build["binary_sha256"] == BINARY_SHA256 and build["private_exporter_excluded"]
    assert digest(repo / "tools/language_rebuild_probe.go") == build["sources"]["language_rebuild_probe.go"]
    units = read(reports / "r131-formal-test-check-r2.json")
    assert units["pass_count"] == 183 and units["skip_count"] == 0
    assert digest(reports / "r131-formal-tests-r2") == units["binary_sha256"]
    assert digest(reports / units["log"]) == units["log_sha256"]
    assert digest(reports / "r131-ready-review-r2.json") == LAYOUT_REVIEW_SHA256
    review = read(reports / "r131-ready-review-r2.json")

    capture = read(folder / "capture.json")
    assert capture["result"] == "RECORDED_R131_FORMAL_ATTACK_CONFIRMATION_GUI"
    assert capture["source_binary_sha256"] == BINARY_SHA256
    assert capture["runtime_source_build_sha256"] == digest(reports / "r131-formal-build-r2.json")
    assert capture["normal_player_path_only"] is True
    inputs = read(folder / "gui.inputs.json")
    inputs_sha = digest(folder / "gui.inputs.json")
    assert capture["inputs_sha256"] == inputs_sha
    zh, original = read(folder / "gui.json"), read(control / "gui.json")
    assert zh["state"] == original["state"], "original CPU state differs"
    assert inputs["end"] == zh["state"]["steps"]
    assert zh["input_hashes"] == original["input_hashes"]
    for name, key in (("gui.memory", "memory_sha256"), ("gui.final.idx", "frame_sha256"), ("gui.final.pal", "palette_sha256")):
        assert digest(folder / name) == digest(control / name) == zh["state"][key], name
    saves = lambda root: {str(f.relative_to(root)): digest(f) for f in root.rglob("*") if f.is_file() and not f.is_symlink()}
    assert saves(folder / "save") == saves(control / "save"), "original saves differ"
    seed = repo / "workplace/reports/goal186-display-hd/hd-dialog-figures-r98/r98-mss-formal-gui-r4/save/COLONY09.SAV"
    assert digest(seed) == "b5e9391cc6d7407bbd0899686141f483d7764f947afd027182c3699d52bad472"

    palette = raw(reports / "r131-native-replay-r2/gui.final.pal")
    regions = {"body": (228, 468, 772, 552), "choices": (248, 560, 320, 652)}
    expected = {}
    for locale in LOCALES:
        path = reports / "r131-formal-display-r2" / ("attack-" + locale + ".png")
        assert digest(path) == review["previews"][locale], "independent source fixture differs"
        image = Image.open(path).convert("RGBA")
        expected[locale] = {}
        for region, box in regions.items():
            for index in ((68, 149) if region == "body" else (68,)):
                points = [(x, y) for y in range(box[1], box[3]) for x in range(box[0], box[2])
                          if image.getpixel((x, y)) == color(palette, index)]
                assert points, "empty Noto reference"
                expected[locale][region, index] = points

    seen, hover = defaultdict(set), set()
    opaque, game_pixels, body_frames = 0, 0, 0
    closed = set()
    assert len(capture["samples"]) >= 64, "required normal GUI samples are missing"
    for sample in capture["samples"]:
        image_path = sample_path(folder, sample["image"])
        shot_path = sample_path(folder, sample["x11"])
        image = Image.open(image_path).convert("RGBA")
        shot = Image.open(shot_path).convert("RGBA")
        assert image.size == (1280, 800) and shot.size == (1280, 848)
        assert image.tobytes() == shot.crop((0, 48, 1280, 848)).tobytes(), "X11 presentation differs"
        assert hashlib.sha256(image.tobytes()).hexdigest() == sample["state"]["presentation_rgba_sha256"]
        game_pixels += 1280 * 800
        native = sample["native_live"]
        items = native.get("items", [])
        bodies = [field for field in items if field.get("id") == BODY]
        choices = [field for field in items if field.get("id") == CHOICES]
        if sample["label"].startswith("proof-25-") and sample["locale"] in LOCALES:
            assert len(bodies) == len(choices) == 1, "confirmed body or choices absent"
        if bodies:
            assert len(bodies) == len(choices) == 1
            body = bodies[0]
            assert body["font_px"] == 30 and rect(body["safe"]) == (57, 114, 246, 138)
            assert rect(body["layout_safe"]) == (57, 117, 193, 138)
            assert (body["foreground_source"], body["foreground_pixels"], body["native_occluded_pixels"]) == (1061, 4429, 13)
            assert rect(choices[0]["safe"]) == (62, 140, 80, 163)
            locale = sample["locale"]
            seen[locale].add(sample["graphics"])
            pal = raw(sample_path(folder, sample["state"]["palette_path"]))
            mouse = sample["state"]["dos_mouse"]
            skip = (mouse["x"] * 4, mouse["y"] * 4, (mouse["x"] + 16) * 4, (mouse["y"] + 16) * 4)
            for (_, index), points in expected[locale].items():
                visible = [(x, y) for x, y in points if not (skip[0] <= x < skip[2] and skip[1] <= y < skip[3])]
                assert visible, "all reference glyphs occluded"
                wanted = color(pal, index)
                assert all(image.getpixel(point) == wanted for point in visible), "Noto strokes absent: " + sample["label"]
                opaque += len(visible)
            body_frames += 1
            if sample["graphics"] == "hd":
                portrait = native["hd"]["scene_picture"]["sources"]["1061"]
                assert portrait["painted"] == 4429, "HD figure missing"
            if sample["label"].startswith("proof-"):
                number = int(sample["label"].split("-")[1])
                if 26 <= number <= 37:
                    locale_expected = LOCALES[(number - 26) // 3]
                    point = ((70, 145), (70, 157), (70, 145))[(number - 26) % 3]
                    assert locale == locale_expected and (mouse["x"], mouse["y"]) == point
                    assert sample["graphics"] == "hd" and native["hd"]["cursor"]["painted"] > 0
                    hover.add(number)
        if sample["locale"] == "en" and sample["graphics"] == "original":
            pal = raw(sample_path(folder, sample["state"]["palette_path"]))
            idx = raw(sample_path(folder, sample["state"]["indexed_path"]))
            original_image = Image.new("RGBA", (320, 200))
            original_image.putdata([color(pal, value) for value in idx])
            assert original_image.resize((1280, 800), Image.Resampling.NEAREST).tobytes() == image.tobytes()
        if sample["label"] in ("inspect-command-38", "final-war-path-zh-Hant"):
            assert not bodies and not choices
            assert not any(field.get("source") == "COMBAT ANALYSIS" for field in items), "attack was not cancelled"
            assert native["hd"]["scene_picture"]["sources"]["1061"]["painted"] == 0
            closed.add(sample["label"])
    assert all(seen[locale] == {"original", "hd"} for locale in LOCALES)
    assert hover == set(range(26, 38)) and len(closed) == 2 and body_frames == 33
    events = read(folder / "gui.display-events.json")
    groups = defaultdict(list)
    for event in events:
        groups[event["step"]].append(event)
    state_keys = ("step", "memory_sha256", "indexed_sha256", "palette_sha256", "registers", "segments", "ip", "flags", "dos_input_count", "dos_mouse")
    assert all(all(all(event[key] == rows[0][key] for key in state_keys) for event in rows) for rows in groups.values())

    old = Image.open(reports / "r131-attack-formal-gui-r1/inspect-command-25.x11.png").convert("RGBA").crop((0, 48, 1280, 848))
    points = expected["zh-Hant"]["body", 68]
    old_matches = sum(old.getpixel(point) == color(palette, 68) for point in points)
    assert old_matches < len(points), "visible original bug was not rejected"
    sources = [event for event in zh["events"] if event.get("stage") == "source" and event.get("candidate_id") == BODY]
    assert sources and any(event.get("stage") == "active" and event.get("candidate_id") == BODY for event in zh["events"])
    source = sources[-1]
    assert source["safe"] == [57, 114, 246, 138] and source["source_linear"] == 175142
    return {"result": "PASS", "status": "PASS_ATTACK_CONFIRMATION", "inputs_sha256": inputs_sha,
            "final_step": zh["state"]["steps"], "final_memory_sha256": zh["state"]["memory_sha256"],
            "verified_fields": [{"candidate_id": BODY, "shown": source["shown"], "safe": source["safe"],
                                 "font_px": 30, "source_ids": [SOURCE_ID]}],
            "samples": len(capture["samples"]), "body_frames": body_frames, "Noto_opaque_points_verified": opaque,
            "X11_RGBA_pixels_equal": game_pixels, "hover_frames": len(hover),
            "old_bug_matched_points": old_matches, "old_bug_expected_points": len(points),
            "whole_original_state_and_saves_equal": True,
            "scope": "Only the observed Cherokee attack-confirmation body and complete choices; no new battle-result or full-HD claim."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--reports", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not all((args.game / name).is_file() for name in ("GAME.TXT", "MSS1.SS", "VICEROY.EXE")):
        print(json.dumps({"result": "SKIP", "reason": "缺少合法原版輸入"}, ensure_ascii=False))
        return 77
    try:
        result = check(args.game, args.reports, args.repo)
    except (AssertionError, OSError, KeyError, ValueError, TypeError) as error:
        print(json.dumps({"result": "FAIL", "reason": str(error)}, ensure_ascii=False))
        print(str(error), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
