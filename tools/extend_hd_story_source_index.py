"""規格069 R89：只在十一背景限定驗收通過後擴充來源清冊，不含原版像素。"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    assert path.is_file() and not path.is_symlink()
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['baseline', 'assets', 'ready', 'conformed', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    a = parser.parse_args()
    assert Path('/.dockerenv').exists() and os.getuid() != 0
    assert not a.output.exists() and a.output.parent.stat().st_uid == os.getuid()
    baseline, ready, review = read(a.baseline), read(a.ready), read(a.conformed)
    manifest = read(a.assets / 'manifest.json')
    ids = [1002, *range(1005, 1015)]
    assert ready['result'] == 'READY_NATION_STORY_DISPLAY_ONLY' and ready['sources'] == ids
    assert review['result'] == 'PASS_R89_NATION_STORY_CONFORMANCE'
    assert review['spec_state'] == 'CONFORMED' and review['sources'] == ids
    assert review['ready_sha256'] == sha(a.ready)
    assert review['inherited_source_index_sha256'] == sha(a.baseline)
    assert review['inherited_manifest_sha256'] == baseline['formal_manifest_sha256']
    assert review['manifest_sha256'] == sha(a.assets / 'manifest.json')
    assert review['formal_assets'] == len(manifest['assets']) == 217
    assert review['old_raw_pngs_preserved'] == review['old_metadata_preserved'] == 206
    assert review['go_named_passed'] == 46 and review['go_failed'] == review['go_skipped'] == 0
    assert review['full_project_loader_positive']
    assert review['package_files'] == 218 and review['package_faults'] == 40
    assert review['gui_samples'] == 66 and review['unique_native_points'] == 60
    assert review['gui_full_rgba'] == review['gui_x11_rgba'] == 67584000
    assert review['gui_noto_fields'] == 26
    assert review['three_replays_state_audio_save_equal_GUI'] and review['actual_inputs'] == 36
    assert review['replay_end'] == 1154200000 and review['native_inputs_rules_and_save_unchanged']
    assert not review['complete_hd']
    out = copy.deepcopy(baseline)
    frames = {f['research_id']: f for f in out['frames']}
    bindings = out['formal_bindings']
    assert len(bindings) == 206 and len(frames) == 1552
    for binding in bindings:
        name = binding['asset']
        assert manifest['assets'][name]['sha256'] == binding['asset_sha256'] == sha(a.assets / name)
    old_names = {b['asset'] for b in bindings}
    new = [(1002, 'kinglss1-000.png'), *[(1004 + i, 'levn%04d-000.png' % i) for i in range(1, 11)]]
    assert set(manifest['assets']) - old_names == {name for _, name in new}
    for ident, name in new:
        frame, meta = frames[ident], manifest['assets'][name]
        assert not frame['formal_assets'] and frame['ordinal'] == 0
        assert frame['size'] == [320, 200] and frame['decode_status'] == 'decoded'
        original = meta['original_source']
        assert original['file'] == frame['file'] and original['ordinal'] == frame['ordinal']
        assert sha(a.assets / name) == meta['sha256']
        bindings.append({'asset': name, 'asset_sha256': meta['sha256'],
                         'source_research_id': ident, 'source_file': frame['file'],
                         'source_ordinal': 0, 'source_encoded_sha256': None,
                         'source_indexed_sha256': frame['indexed_sha256'],
                         'spec': 'docs/spec/069-hd-menu-background-and-textures.md',
                         'claim': 'matches verified formal manifest; conformance scope remains in cited spec'})
        frame['formal_assets'] = [name]
        frame['runtime_source_evidence'] = 'confirmed complete PIK decode, typed RAM copies and current VGA publication; normal GUI66/native60 only'
        frame['source_contract_reference'] = {
            'state': 'CONFORMED', 'spec': 'docs/spec/069-hd-menu-background-and-textures.md',
            'formal_connected': True, 'review_sha256': sha(a.conformed),
            'scope': 'one original story background; native foreground, glyphs, cursor visibility, input and timing preserved; no king sprite or full-HD credit'}
    assert len(bindings) == 217
    assert all(frames[i] == f for i, f in ((f['research_id'], f) for f in baseline['frames']) if i not in ids)
    out['formal_manifest_sha256'] = sha(a.assets / 'manifest.json')
    out['coverage_limits']['formal_asset_bindings'] = len(bindings)
    out['coverage_limits']['complete_hd'] = False
    out['nation_story_conformance'] = {
        'ready_sha256': sha(a.ready), 'review_sha256': sha(a.conformed), 'sources': ids,
        'formal_assets': 217, 'gui_samples': 66, 'unique_native_points': 60,
        'claim': 'eleven story backgrounds only; original king and hound retained; other images, animation and full HD incomplete'}
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('PASS_STORY11_CONFORMED_SOURCE_INDEX', len(bindings), sha(a.output), flush=True)


if __name__ == '__main__':
    main()
