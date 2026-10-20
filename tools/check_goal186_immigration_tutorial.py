#!/usr/bin/env python3
"""核對歐洲移民通知的正常視窗、四語Noto及顯示設定暫停。"""
import argparse, base64, gzip, hashlib, json
from pathlib import Path, PurePosixPath
from PIL import Image
BODY = 'GAME.TXT:@TUTORIAL5'
LOCALES = ('zh-Hant', 'zh-Hans', 'ja', 'ko')

def raw(path):
    if path.is_file():
        return path.read_bytes()
    with gzip.open(path.with_name(path.name + '.gz'), 'rb') as f:
        return f.read()

def digest(path):
    return hashlib.sha256(raw(path)).hexdigest()

def read(path):
    return json.loads(raw(path))

def rect(r):
    return [r['Min']['X'], r['Min']['Y'], r['Max']['X'], r['Max']['Y']]

def sample_path(folder, value):
    p = PurePosixPath(value)
    assert p.parent.name == folder.name and p.name not in ('', '.', '..')
    target = folder / p.name
    assert target.is_file() and (not target.is_symlink())
    return target

def native_image(folder, state):
    indexed = raw(sample_path(folder, state['indexed_path']))
    palette = raw(sample_path(folder, state['palette_path']))
    assert len(indexed) == 64000 and len(palette) == 768
    im = Image.frombytes('P', (320, 200), indexed)
    im.putpalette([v << 2 | v >> 4 for v in palette])
    return im.convert('RGBA').resize((1280, 800), Image.Resampling.NEAREST)

def check_gui(reports, folder, binary, build_name, points_name):
    build = read(reports / build_name)
    capture = read(folder / 'capture.json')
    assert digest(reports / binary) == capture['source_binary_sha256'] == build['binary_sha256']
    assert capture['build_sha256'] == digest(reports / build_name)
    assert capture['normal_player_path_only'] and capture['actual_X11_gameplay_inputs']
    assert build['extra_diagnostic_exports_absent']
    command = read(folder / 'command.json')
    assert '--replay-inputs' not in command and '--play=true' in command and ('--display-diagnostics' in command)
    points_data = read(reports / points_name)
    points = {r['locale']: r['solid_text_points'] for r in points_data['records']}
    assert set(points) == set(LOCALES) and all((len(v) > 500 for v in points.values()))
    inputs = read(folder / 'gui.inputs.json')
    assert digest(folder / 'gui.inputs.json') == capture['inputs_sha256']
    reference = read(reports / 'r130-war-gui-r1/gui.inputs.json')
    assert capture['source_R130_inputs_sha256'] == digest(reports / 'r130-war-gui-r1/gui.inputs.json')
    strip = lambda rows: [{k: v for k, v in r.items() if k != 'step'} for r in rows]
    body_count = capture['body_input_count']
    assert body_count == 65 and strip(inputs['inputs'][:65]) == strip(reference['inputs'][:65]), 'X11 player actions differ'
    assert len(inputs['inputs']) == 66 and inputs['inputs'][65]['kind'] == 'enter'
    expected_labels = {loc + '-' + mode for loc in (*LOCALES, 'en') for mode in ('original', 'hd')} | {'closed-zh-Hant-hd', 'closed-en-original'}
    assert {s['label'] for s in capture['samples']} == expected_labels and len(capture['samples']) == 12
    owners = raw(reports / 'r138-native-replay-r1/source-1060.owners')
    assert hashlib.sha256(owners).hexdigest() == '074228ece53f310039442c6c8fa5c11679405b7f2c94b87c23eb3ef831addff8'
    mask = [pos for pos in range(64000) if owners[pos >> 3] & 1 << (pos & 7)]
    assert len(mask) == 3306
    seen = {loc: set() for loc in LOCALES}
    opaque = rgba = body_frames = original_portrait = hd_portrait = 0
    images = {}
    fields = []
    closed = set()
    occlusions = set()
    for s in capture['samples']:
        image = Image.open(sample_path(folder, s['image'])).convert('RGBA')
        shot = Image.open(sample_path(folder, s['x11'])).convert('RGBA')
        assert image.size == (1280, 800) and shot.size == (1280, 848)
        assert image.tobytes() == shot.crop((0, 48, 1280, 848)).tobytes(), 'X11 presentation differs'
        assert hashlib.sha256(image.tobytes()).hexdigest() == s['state']['presentation_rgba_sha256']
        rgba += 1280 * 800
        images[s['label']] = image
        native = s['native_live']
        items = native.get('items', [])
        bodies = [v for v in items if v.get('id') == BODY]
        if s['tutorial5_required']:
            assert s['state']['dos_input_count'] == body_count
            if s['locale'] in LOCALES:
                assert len(bodies) == 1, 'tutorial missing'
                item = bodies[0]
                assert item['font_px'] == 30 and rect(item['safe']) == [52, 108, 271, 162]
                assert rect(item['layout_safe']) == [52, 125, 271, 162]
                assert (item['foreground_source'], item['foreground_pixels']) == (1060, 3306)
                assert item['native_occluded_pixels'] in (0, 1)
                occlusions.add(item['native_occluded_pixels'])
                seen[s['locale']].add(s['graphics'])
                for p in points[s['locale']]:
                    assert image.getpixel((p['x'], p['y'])) == tuple(base64.b64decode(p['rgb'])) + (255,), 'Noto strokes missing'
                opaque += len(points[s['locale']])
                body_frames += 1
                if s['label'] == 'zh-Hant-original':
                    fields.append({'candidate_id': BODY, 'shown': item['text'], 'safe': [52, 108, 271, 162], 'font_px': 30, 'source_ids': [BODY]})
            else:
                assert native.get('original_rendering') and (not items)
            if s['graphics'] == 'original':
                assert not native.get('hd')
                original = native_image(folder, s['state'])
                for pos in mask:
                    for dy in range(4):
                        for dx in range(4):
                            xy = (pos % 320 * 4 + dx, pos // 320 * 4 + dy)
                            assert image.getpixel(xy) == original.getpixel(xy), 'native portrait changed'
                            original_portrait += 1
            else:
                assert native['hd']['scene_picture']['sources']['1060']['painted'] == 3306
        else:
            assert not bodies and s['state']['dos_input_count'] == body_count + 1
            closed.add(s['label'])
        if s['locale'] == 'en' and s['graphics'] == 'original':
            assert native_image(folder, s['state']).tobytes() == image.tobytes(), 'English original differs'
    assert all((v == {'original', 'hd'} for v in seen.values())) and body_frames == 8 and (len(closed) == 2)
    reference_hd = images['en-hd']
    for loc in LOCALES:
        im = images[loc + '-hd']
        for pos in mask:
            for dy in range(4):
                for dx in range(4):
                    xy = (pos % 320 * 4 + dx, pos // 320 * 4 + dy)
                    assert im.getpixel(xy) == reference_hd.getpixel(xy), 'HD portrait changed across languages'
                    hd_portrait += 1
    events = read(folder / 'gui.display-events.json')
    assert len(events) == 48
    keys = ('step', 'memory_sha256', 'indexed_sha256', 'palette_sha256', 'registers', 'segments', 'ip', 'flags', 'dos_input_count', 'dos_mouse')
    for i in range(0, len(events), 4):
        rows = events[i:i + 4]
        assert [r['action'] for r in rows] == ['open', 'ready', 'apply', 'resume']
        assert all((all((r[k] == rows[0][k] for k in keys)) for r in rows))
    old = Image.open(reports / 'r130-war-gui-r1/gui.display-086.png').convert('RGBA')
    old_points = points['zh-Hant']
    old_matched = sum((old.getpixel((p['x'], p['y'])) == tuple(base64.b64decode(p['rgb'])) + (255,) for p in old_points))
    assert old_matched < len(old_points), 'original English defect was not rejected'
    return {'result': 'PASS', 'status': 'PASS_IMMIGRATION_TUTORIAL_GUI', 'samples': 12, 'body_frames': 8, 'Noto_solid_points_verified': opaque, 'X11_RGBA_pixels_equal': rgba, 'native_portrait_RGBA_points_verified': original_portrait, 'HD_portrait_RGBA_points_equal_across_languages': hd_portrait, 'source_snapshot_occluded_counts': sorted(occlusions), 'display_groups_native_state_unchanged': 12, 'actual_X11_inputs': len(inputs['inputs']), 'inputs_sha256': digest(folder / 'gui.inputs.json'), 'same_R130_player_actions_excluding_step': True, 'old_bug_matched_points': old_matched, 'old_bug_expected_points': len(old_points), 'verified_fields': fields, 'final_step': inputs['end'], 'scope': 'Only the observed Master Carpenters/London tutorial5 body, two image modes, English original display, complete existing MSS0 portrait and normal dismissal. No full-language or full-HD claim.'}
BINARY_SHA256 = '2bbd0e9da26bc686964d63bd9797835314ad2e06e6a4deec46b4c777c61e3310'
READY_SHA256 = '2fd4042941379f525ba82a24172b4ffa05080778865a6a732a105d899a561ffb'
CONTROL_BINARY_SHA256 = '0f96b219cce1856eb301cdfbcbab1ceb60c9184c21b9a0358117a3eea054f605'
GUI = 'r138-formal-gui-r1'
CONTROL = 'r138-original-control-r1'

def check(game, reports, repo):
    originals = {'GAME.TXT': '67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a', 'MSS0.SS': '8966f5680e2281ce2f3311e25199b7984d5fac1c4d9361ac21cfa08011b4b8a4', 'VICEROY.EXE': 'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3'}
    for name, want in originals.items():
        assert digest(game / name) == want, 'original fingerprint: ' + name
    assert digest(reports / 'r138-ready-review-r1.json') == READY_SHA256
    build = read(reports / 'r138-formal-build-r1.json')
    assert build['binary_sha256'] == digest(reports / 'r138-formal-window-r1') == BINARY_SHA256
    assert digest(repo / 'tools/language_rebuild_probe.go') == build['source_sha256']
    assert digest(repo / 'graphics/manifest.json') == build['manifest_sha256']
    assert build['private_exporter_excluded'] and build['tested_prototype_runtime_source_identical']
    units = read(reports / 'r138-formal-source-review-r1.json')
    assert (units['pass_count'], units['new_field_pass_count'], units['existing_source_guard_pass_count'], units['skip_count']) == (253, 70, 183, 0)
    assert digest(reports / 'r138-formal-tests-r1') == units['binary_sha256'] == build['test_binary_sha256']
    assert digest(reports / units['log']) == units['log_sha256']
    assert digest(reports / 'r138-formal-field-r1/check.json') == units['field_check_sha256'] == 'dc8b6547f4a1d67eeb49ad4564cca2ace8c0061670e2f25f61a78e4cf29b4f36'
    assert digest(reports / 'r137-formal-window-r1') == CONTROL_BINARY_SHA256
    folder, control = (reports / GUI, reports / CONTROL)
    control_receipt = read(control / 'check.json')
    inputs_sha = digest(folder / 'gui.inputs.json')
    assert control_receipt['binary_sha256'] == CONTROL_BINARY_SHA256 and control_receipt['inputs_sha256'] == inputs_sha
    zh, original = (read(folder / 'gui.json'), read(control / 'gui.json'))
    assert zh['state'] == original['state'], 'complete original CPU state differs'
    assert zh['input_hashes'] == original['input_hashes'], 'original input file fingerprints differ'
    assert read(folder / 'gui.inputs.json')['end'] == zh['state']['steps']
    for name, key in (('gui.memory', 'memory_sha256'), ('gui.final.idx', 'frame_sha256'), ('gui.final.pal', 'palette_sha256')):
        assert digest(folder / name) == digest(control / name) == zh['state'][key], name

    def saves(path):
        return {str(p.relative_to(path)): digest(p) for p in path.rglob('*') if p.is_file() and (not p.is_symlink())}
    assert saves(folder / 'save') == saves(control / 'save'), 'original saves differ'
    seed = repo / 'workplace/reports/goal186-display-hd/hd-dialog-figures-r98/r98-mss-formal-gui-r4/save/COLONY09.SAV'
    assert digest(seed) == 'b5e9391cc6d7407bbd0899686141f483d7764f947afd027182c3699d52bad472'
    proof = check_gui(reports, folder, 'r138-formal-window-r1', 'r138-formal-build-r1.json', 'r138-formal-field-r1/check.json')
    sources = [e for e in zh.get('events', []) if e.get('stage') == 'source' and e.get('candidate_id') == BODY]
    assert len(sources) == 1
    source = sources[0]
    assert source['safe'] == [52, 108, 271, 162] and source['source_linear'] == 175250
    assert 'Master Carpenters' in source['shown'] and 'London' in source['shown']
    assert any((e.get('stage') == 'active' and e.get('candidate_id') == BODY for e in zh['events']))
    proof['displayed_text'] = proof['verified_fields'][0]['shown']
    proof['verified_fields'][0]['shown'] = source['shown']
    proof.update(status='PASS_IMMIGRATION_TUTORIAL', whole_original_state_and_saves_equal=True, final_memory_sha256=zh['state']['memory_sha256'], formal_source_tests=253, skip_count=0)
    return proof

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', required=True, type=Path)
    p.add_argument('--reports', required=True, type=Path)
    p.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    a = p.parse_args()
    if not all(((a.game / n).is_file() for n in ('GAME.TXT', 'MSS0.SS', 'VICEROY.EXE'))):
        print(json.dumps({'result': 'SKIP', 'reason': '缺少合法原版輸入'}, ensure_ascii=False))
        return 77
    try:
        r = check(a.game, a.reports, a.repo)
    except (AssertionError, OSError, KeyError, ValueError, TypeError) as error:
        print(json.dumps({'result': 'FAIL', 'reason': str(error)}, ensure_ascii=False))
        return 1
    print(json.dumps(r, ensure_ascii=False))
    return 0
if __name__ == '__main__':
    raise SystemExit(main())
