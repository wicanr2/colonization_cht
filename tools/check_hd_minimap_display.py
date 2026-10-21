#!/usr/bin/env python3
"""核對規格069 R140小地圖的正式來源、五語切換及實際X11畫面。"""
import argparse
import gzip
import hashlib
import json
import os
from collections import Counter
from pathlib import Path
from PIL import Image

READY_SHA = "385d7dda183c50e04eaf7df7be62342353c2c3b760d93bafc99aec2a2b74da09"
BINARY_SHA = "cddf437dea2f3d9e71da7e906fb47322a7ebbd85cbe188aa7f60030883097cf2"
PROGRAM_SHA = "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3"
MATERIAL_SHA = "d7bf0ac7048ab765381a582d5fe380267c7186b130ae6237944c7242df0f82ad"
LOCALES = ("en", "zh-Hant", "zh-Hans", "ja", "ko")
COLORS = (0, 6, 12, 15, *range(56, 68))
BOUNDS = (1004, 32, 1236, 196)


def raw(path):
    if path.is_file():
        return path.read_bytes()
    return gzip.decompress(path.with_name(path.name + ".gz").read_bytes())


def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()


def read(path):
    return json.loads(raw(path))


def sample_file(folder, value):
    value = Path(value)
    assert value.parent.name == folder.name and value.name not in ("", ".", "..")
    result = folder / value.name
    assert result.is_file() and not result.is_symlink()
    return result


def native_image(indexed, palette):
    assert len(indexed) == 64000 and len(palette) == 768 and max(palette) <= 63
    result = Image.frombytes("P", (320, 200), indexed)
    result.putpalette([v << 2 | v >> 4 for v in palette])
    return result.convert("RGBA").resize((1280, 800), Image.Resampling.NEAREST)


def check(game, reports, repo):
    assert digest(game / "VICEROY.EXE") == PROGRAM_SHA
    assert digest(reports / "r140-ready-review-r1.json") == READY_SHA
    build = read(reports / "r140-formal-build-r1.json")
    assert digest(reports / "r140-formal-window-r1") == build["binary_sha256"] == BINARY_SHA
    assert digest(repo / "tools/hd_native_minimap.go") == build["runtime_source_sha256"]
    assert digest(repo / "graphics/manifest.json") == build["manifest_sha256"]
    assert digest(repo / "graphics/mpsname-silver-material.png") == MATERIAL_SHA
    units = read(reports / "r140-formal-source-tests-r1.json")
    assert (units["pass_count"], units["new_component_passes"], units["existing_transaction_passes"], units["skip_count"]) == (25, 24, 1, 0)
    assert digest(reports / "r140-formal-tests-r1") == units["binary_sha256"] == build["test_binary_sha256"]
    assert digest(reports / "r140-formal-source-tests-r1.stdout") == units["stdout_sha256"]
    assert units["display_check"]["original_RAM_unchanged"] and units["display_check"]["scene_frames_loaded"] == 895
    missing = read(reports / "r140-formal-missing-original-r1.json")
    assert missing["result"] == "PASS_EXPECTED_ORIGINAL_MISSING_SKIP" and missing["skip_count"] == 1
    folder = reports / "r140-formal-gui-r1"
    capture = read(folder / "capture.json")
    assert capture["result"] == "PASS_R140_NORMAL_X11_MINIMAP_FORMAL"
    assert capture["source_binary_sha256"] == BINARY_SHA
    assert capture["build_sha256"] == digest(reports / "r140-formal-build-r1.json")
    assert capture["normal_player_path_only"] and capture["actual_X11_gameplay_inputs"]
    assert capture["display_settings_native_state_invariant"] and capture["minimap_language_independent"]
    command = read(folder / "command.json")
    assert "--replay-inputs" not in command and "--play=true" in command and "--display-diagnostics" in command
    inputs = read(folder / "gui.inputs.json")
    assert digest(folder / "gui.inputs.json") == capture["inputs_sha256"]
    assert len(inputs["inputs"]) == capture["normal_input_count"] == 15
    samples = capture["samples"]
    assert len(samples) == 10
    assert {(s["locale"], s["graphics"]) for s in samples} == {(loc, mode) for loc in LOCALES for mode in ("original", "hd")}
    groups = {}
    rgba = white_rgba = changed_total = 0
    changes = []
    for s in samples:
        e = s["state"]
        assert e["dos_input_count"] == 15
        indexed = raw(sample_file(folder, e["indexed_path"]))
        palette = raw(sample_file(folder, e["palette_path"]))
        assert hashlib.sha256(indexed).hexdigest() == e["indexed_sha256"]
        assert hashlib.sha256(palette).hexdigest() == e["palette_sha256"]
        image = Image.open(sample_file(folder, s["image"])).convert("RGBA")
        shot = Image.open(sample_file(folder, s["x11"])).convert("RGBA")
        assert image.size == (1280, 800) and shot.size == (1280, 848)
        assert image.tobytes() == shot.crop((0, 48, 1280, 848)).tobytes()
        assert hashlib.sha256(image.tobytes()).hexdigest() == e["presentation_rgba_sha256"]
        native = native_image(indexed, palette)
        crop, original = image.crop(BOUNDS), native.crop(BOUNDS)
        changed = sum(a != b for a, b in zip(crop.getdata(), original.getdata()))
        assert changed == s["changed_RGBA_points"]
        white = 0
        for y in range(8, 49):
            for x in range(251, 309):
                if indexed[y * 320 + x] == 15:
                    box = (x * 4, y * 4, x * 4 + 4, y * 4 + 4)
                    assert image.crop(box).tobytes() == native.crop(box).tobytes()
                    white += 16
        assert white == s["viewport_RGBA_points_unchanged"]
        if s["graphics"] == "hd":
            c = s["component"]
            assert c["reason"] == "verified-native-world-minimap" and c["painted"] > 0
            assert c["changed_RGBA_points"] == changed > 0
            assert c["white_pixels"] * 16 == white
            native_map = bytes(indexed[y * 320 + x] for y in range(8, 49) for x in range(251, 309))
            used = bytes(palette[v * 3 + j] for v in COLORS for j in range(3))
            key = (hashlib.sha256(native_map).hexdigest(), hashlib.sha256(used).hexdigest())
            groups.setdefault(key, set()).add(hashlib.sha256(crop.tobytes()).hexdigest())
            changes.append(changed)
        else:
            assert not s["component"] and changed == 0
            if s["locale"] == "en":
                assert image.tobytes() == native.tobytes()
        rgba += 1280 * 800
        white_rgba += white
        changed_total += changed
    assert all(len(values) == 1 for values in groups.values())
    events = read(folder / "gui.display-events.json")
    assert Counter(e["action"] for e in events) == {"open": 10, "ready": 10, "apply": 10, "resume": 10}
    fields = ("step", "memory_sha256", "indexed_sha256", "palette_sha256", "registers", "segments", "ip", "flags", "dos_input_count", "dos_mouse")
    opening = None
    for e in events:
        if e["action"] == "open":
            opening = e
        if opening is not None:
            assert all(e[k] == opening[k] for k in fields)
        if e["action"] == "resume":
            opening = None
    assert opening is None
    return {"result": "PASS_NATIVE_MINIMAP_DISPLAY", "GUI_samples": 10, "X11_game_RGBA_points": rgba,
            "native_white_RGBA_points_preserved": white_rgba, "HD_changed_RGBA_points": changes,
            "HD_changed_RGBA_points_total": changed_total, "source_component_test_passes": 24,
            "existing_transaction_test_passes": 1, "source_test_skips": 0, "five_languages_both_modes": True,
            "minimap_language_independent": True, "display_settings_native_state_invariant": True,
            "scope": "Native minimap material DISPLAY-PASS in the recorded normal world path. Other HD, translation, timing, audio and release requirements remain separate."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--reports", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not (args.game / "VICEROY.EXE").is_file():
        print(json.dumps({"result": "SKIP", "reason": "缺少合法原版輸入"}, ensure_ascii=False))
        return 77
    try:
        result = check(args.game, args.reports, args.repo)
    except (AssertionError, OSError, KeyError, ValueError, TypeError) as error:
        print(json.dumps({"result": "FAIL", "reason": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
