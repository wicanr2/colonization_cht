#!/usr/bin/env python3
"""核對規格060 R143原住民人物後方側欄、正常X11與原版狀態。在Docker內以非root執行。"""
from pathlib import Path
import base64, json, hashlib, gzip
from PIL import Image

def raw(p):
    return p.read_bytes() if p.exists() else gzip.decompress(p.with_name(p.name + '.gz').read_bytes())

def read(p):
    return json.loads(raw(p))

def rect(d):
    return (d['Min']['X'], d['Min']['Y'], d['Max']['X'], d['Max']['Y'])

def pixels(mask):
    return [(i % 320, i // 320) for i in range(64000) if mask[i >> 3] & 1 << (i & 7)]

def check_gui(reports, folder, build_name, binary_name):
    out = reports
    root = folder
    cap = read(root / 'capture.json')
    build = read(out / build_name)
    assert cap['source_binary_sha256'] == build['binary_sha256']
    assert hashlib.sha256(raw(out / binary_name)).hexdigest() == build['binary_sha256']
    assert cap['normal_player_path_only'] and cap['actual_X11_gameplay_inputs'] and cap['display_settings_native_state_invariant']
    samples = cap['samples']
    assert len(samples) == 25
    lookup = {s['label']: s for s in samples}
    images = {}
    native = {}
    fields = []
    measurements = {}
    portrait_points = 0
    for s in samples:
        im = Image.open(sample_file(root, s['image'])).convert('RGBA')
        shot = Image.open(sample_file(root, s['x11'])).convert('RGBA')
        assert im.size == (1280, 800) and shot.size == (1280, 848)
        assert im.tobytes() == shot.crop((0, 48, 1280, 848)).tobytes()
        assert hashlib.sha256(im.tobytes()).hexdigest() == s['state']['presentation_rgba_sha256']
        idx = raw(sample_file(root, s['state']['indexed_path']))
        pal = raw(sample_file(root, s['state']['palette_path']))
        assert hashlib.sha256(idx).hexdigest() == s['state']['indexed_sha256']
        assert hashlib.sha256(pal).hexdigest() == s['state']['palette_sha256']
        pic = Image.frombytes('P', (320, 200), idx)
        pic.putpalette([v << 2 | v >> 4 for v in pal])
        pic = pic.convert('RGBA').resize((1280, 800), Image.Resampling.NEAREST)
        images[s['label']] = im
        native[s['label']] = pic
        if s['locale'] == 'en' and s['graphics'] == 'original':
            assert im.tobytes() == pic.tobytes()
        if s['label'].startswith('normal-closed'):
            assert not any((i.get('foreground_source') == 975 for i in s['native_live']['items'] or []))
    for page in [4, 5]:
        for locale in ['en', 'zh-Hant', 'zh-Hans', 'ja', 'ko']:
            for graphics in ['original', 'hd']:
                label = 'command-%02d-%s-%s' % (page, locale, graphics)
                s = lookup[label]
                hd = lookup['command-%02d-%s-hd' % (page, locale)]
                source = hd['native_live']['hd']['sources']['975']
                assert source['painted'] == 5503
                mask = base64.b64decode(source['mask'])
                assert len(mask) == 8000
                points = pixels(mask)
                assert len(points) == 5503
                im = images[label]
                reference = images['command-%02d-en-hd' % page] if graphics == 'hd' else native[label]
                for x, y in points:
                    box = (x * 4, y * 4, x * 4 + 4, y * 4 + 4)
                    assert im.crop(box).tobytes() == reference.crop(box).tobytes(), (label, 'portrait changed', x, y)
                if locale == 'en':
                    continue
                body = 'GAME.TXT:@INDIANWELCOME:0x00003D13' if page == 4 else 'GAME.TXT:@INDIANPEACE:0x000040A6'
                assert any((item.get('kind') == 'dialog' and item.get('id') == body for item in s['native_live']['items'] or [])), (label, 'dialog body absent')
                if page == 4:
                    assert any((item.get('id') == body + '#2+list' for item in s['native_live']['items'] or [])), (label, 'choices absent')
                portrait_points += len(points) * 16
                rows = [r for r in s['native_live']['items'] or [] if r.get('kind') == 'sea-panel' and r.get('foreground_source') == 975]
                required = ['Spring ', 'Gold:', 'Moves:', 'Locat:']
                assert all((any((r['source'].startswith(prefix) for r in rows)) for prefix in required)), (label, 'four status fields absent')
                baseline = images['command-%02d-en-%s' % (page, graphics)]
                changed = 0
                for r in rows:
                    safe = rect(r['safe'])
                    ink = rect(r['native_ink'])
                    assert 242 <= safe[0] < safe[2] <= 319 and 50 <= safe[1] < safe[3] <= 200
                    assert safe[1] == ink[1] and safe[3] == ink[3]
                    assert 15 <= r['font_px'] <= 22 and r['part_font_px'] == [r['font_px']]
                    assert r['baseline_shift_px'] >= 0 and r['foreground_pixels'] > 0
                    count = 0
                    for yy in range(safe[1] * 4, safe[3] * 4):
                        for xx in range(safe[0] * 4, safe[2] * 4):
                            pos = yy // 4 * 320 + xx // 4
                            if not mask[pos >> 3] & 1 << (pos & 7) and im.getpixel((xx, yy)) != baseline.getpixel((xx, yy)):
                                count += 1
                    fields.append({'label': label, 'source': r['source'], 'text': r['text'], 'font_px': r['font_px'], 'native_ink': list(ink), 'safe': list(safe), 'baseline_shift_px': r['baseline_shift_px'], 'uncovered_changed_RGBA_points': count})
                    key = (locale, r['source'], ink[1])
                    record = {k: r[k] for k in ['source', 'text', 'font_px', 'native_ink', 'safe', 'baseline_shift_px']}
                    if key in measurements:
                        assert measurements[key] == record, (label, 'unstable field typography')
                    else:
                        measurements[key] = record
                    changed += count
                assert changed > 0, (label, 'no visible panel changes')
    events = read(root / 'gui.display-events.json')
    first = None
    keys = ['step', 'memory_sha256', 'indexed_sha256', 'palette_sha256', 'registers', 'segments', 'ip', 'flags', 'dos_input_count', 'dos_mouse']
    for e in events:
        if e['action'] == 'open':
            first = e
        if first is not None:
            assert all((e[k] == first[k] for k in keys))
        if e['action'] == 'resume':
            first = None
    assert first is None
    r = {'result': 'PASS_R143_NATIVE_PANEL_GUI_INDEPENDENT', 'GUI_samples': 25, 'X11_RGBA_points': 25 * 1280 * 800, 'CJK_foreground_field_records': len(fields), 'CJK_unique_measured_fields': len(measurements), 'CJK_portrait_RGBA_points_preserved': portrait_points, 'fields': fields, 'measurements': [{'locale': k[0], **v} for k, v in measurements.items()], 'normal_input_count': cap['normal_input_count'], 'capture_sha256': hashlib.sha256(raw(root / 'capture.json')).hexdigest(), 'build_sha256': hashlib.sha256(raw(out / build_name)).hexdigest(), 'scope': 'Current pre-village original state, native IND4A0 complete 5503-point foreground and existing translated single-row sidebar fields. Occluded text is not credited as visible; per-field uncovered changes are recorded. Other 32 IND sources are connected under the same strict whole-foreground gates but are not new normal GUI evidence.'}
    return r

READY_SHA = "9bd6fb5da0237eb914da4fcf1f7ed96bc71ee8c81969ebb57846bcd71ba12689"
PROGRAM_SHA = "a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3"
PORTRAIT_SHA = "c1bbbdff68b54700d5f3de08ac0f08d0c69c3ff7c851627da5ba44de0771573b"

def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()

def sample_file(folder, value):
    path = Path(value)
    assert path.parent.name == folder.name and path.name not in ("", ".", "..")
    result = folder / path.name
    assert result.is_file() and not result.is_symlink()
    return result

def check(game, reports, repo):
    assert digest(game / "VICEROY.EXE") == PROGRAM_SHA
    assert digest(game / "IND4A0.SS") == PORTRAIT_SHA
    assert digest(reports / "r143-ready-review-r1.json") == READY_SHA
    ready = read(reports / "r143-ready-review-r1.json")
    build = read(reports / "r143-formal-build-r1.json")
    assert build["ready_sha256"] == READY_SHA
    assert build["source_files"] == ready["source_files"]
    for name, wanted in ready["source_files"].items():
        assert digest(repo / "tools" / name) == wanted, name
    module = reports / "r143-formal-runtime-r1"
    for name, wanted in build["compiled_go_sources"].items():
        assert digest(module / name) == wanted, name
        source = repo / "tools" / name
        if source.is_file():
            assert digest(source) == wanted, name
    assert digest(repo / "graphics/manifest.json") == build["manifest_sha256"]
    assert build["formal_binary_byte_equal_to_tested_candidate"]
    assert build["formal_test_binary_byte_equal_to_tested_candidate"]
    assert digest(reports / "r143-formal-window-r1") == ready["binary_sha256"] == build["binary_sha256"]
    assert digest(reports / "r143-formal-tests-r1") == ready["test_binary_sha256"] == build["test_binary_sha256"]
    units = read(reports / build["test_evidence"])
    assert (units["pass_count"], units["root_tests"], units["skip_count"]) == (203, 22, 0)
    assert units["binary_sha256"] == build["test_binary_sha256"]
    assert digest(reports / "r143-prototype-guards-r5.stdout") == units["stdout_sha256"]
    for name, wanted in ready["proofs"].items():
        assert digest(reports / name) == wanted, name
    folder = reports / build["gui_evidence"]
    proof = check_gui(reports, folder, build["prototype_build"], "r143-prototype-window-r5")
    old = read(reports / build["gui_review"])
    assert proof == old
    cap = read(folder / "capture.json")
    assert cap["build_sha256"] == digest(reports / build["prototype_build"])
    assert digest(folder / "gui.inputs.json") == cap["inputs_sha256"]
    controller = reports / build["pre_fix_control"]
    control = read(controller / "check.json")
    assert control["result"] == "PASS_R143_PRE_FIX_ORIGINAL_CONTROL"
    assert control["binary_sha256"] == digest(reports / "r140-formal-window-r1")
    assert control["inputs_sha256"] == digest(folder / "gui.inputs.json")
    actual_state = read(folder / "gui.json")
    original_state = read(controller / "gui.json")
    assert actual_state["state"] == original_state["state"] == control["final_state"]
    assert actual_state["input_hashes"] == original_state["input_hashes"]
    for name, key in [("gui.memory", "memory_sha256"), ("gui.final.idx", "frame_sha256"), ("gui.final.pal", "palette_sha256")]:
        assert digest(folder / name) == digest(controller / name) == actual_state["state"][key]
    def saves(root):
        return {str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file() and not p.is_symlink()}
    assert saves(folder / "save") == saves(controller / "save") == control["saves"]
    assert proof["CJK_foreground_field_records"] == 144 and proof["CJK_unique_measured_fields"] == 36
    proof.update(result="PASS_NATIVE_PORTRAIT_PANEL", formal_sources_and_executable_equal_to_tested_candidate=True,
                 formal_source_test_passes=203, source_test_skips=0,
                 whole_original_state_and_saves_equal=True, final_memory_sha256=control["final_state"]["memory_sha256"])
    return proof

def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--reports", required=True, type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    if not all((args.game / name).is_file() for name in ("VICEROY.EXE", "IND4A0.SS")):
        print(json.dumps({"result": "SKIP", "reason": "缺少合法原版輸入"}, ensure_ascii=False))
        return 77
    try:
        result = check(args.game, args.reports, args.repo)
    except (AssertionError, OSError, KeyError, ValueError, TypeError) as error:
        print(json.dumps({"result": "FAIL", "reason": str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps({k: v for k, v in result.items() if k not in ("fields", "measurements")}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
