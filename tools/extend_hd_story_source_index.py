"""依規格069 R89／R90或規格061 R91的限定驗收擴充來源清冊，不含原版像素。"""
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


def extend_buildings(a):
    """規格061 R91：只登錄已有正式驗收的三十個建築來源。"""
    baseline, ready, review = read(a.baseline), read(a.ready), read(a.conformed)
    manifest = read(a.assets / 'manifest.json')
    ordinals = [0, 1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15, 18, 19,
                20, 22, 23, 25, 26, 28, 29, 33, 34, 36, 37, 38, 40, 41, 46]
    names = {'building-%03d.png' % n for n in ordinals}
    assert ready['status'] == 'READY' and set(ready['new_raw_pngs']) == names
    assert review['result'] == 'PASS_R91_BUILDING30_CONFORMANCE'
    assert review['spec_state'] == 'CONFORMED' and review['new_ordinals'] == ordinals
    assert review['ready_sha256'] == sha(a.ready)
    assert review['inherited_source_index_sha256'] == sha(a.baseline)
    assert review['inherited_manifest_sha256'] == baseline['formal_manifest_sha256']
    assert review['manifest_sha256'] == ready['manifest_sha256'] == sha(a.assets / 'manifest.json')
    assert review['formal_assets'] == len(manifest['assets']) == 248
    assert review['old_raw_pngs_preserved'] == review['old_metadata_preserved'] == 218
    assert review['go_named_passed'] == 10 and review['go_failed'] == review['go_skipped'] == 0
    assert review['package_files'] == 249 and review['package_faults'] == 97
    assert review['gui_samples'] == 159 and review['unique_native_points'] == 154
    assert review['gui_full_rgba'] == 158 * 1280 * 800
    assert review['gui_x11_rgba'] == 159 * 1280 * 800 and review['gui_noto_fields'] == 400
    assert review['actual_inputs'] == 848 and review['replay_end'] == 1010800000
    for key in ['full_project_loader_positive', 'all30_original_hd',
                'representative_five_languages_both_modes', 'four_cjk_cursor_hover_return',
                'normal_page_and_menu_close', 'closed_world_has_no_building_owners',
                'three_replays_state_audio_save_equal_GUI', 'raw_png_alpha_preserved',
                'native_inputs_rules_and_save_unchanged']:
        assert review[key]
    assert not review['complete_hd']
    out = copy.deepcopy(baseline)
    assert len(out['formal_bindings']) == 218 and len(out['frames']) == 1552
    for binding in out['formal_bindings']:
        name = binding['asset']
        assert manifest['assets'][name]['sha256'] == binding['asset_sha256'] == sha(a.assets / name)
    assert set(manifest['assets']) - {b['asset'] for b in out['formal_bindings']} == names
    changed = set()
    for ordinal in ordinals:
        name = 'building-%03d.png' % ordinal
        frame = next(f for f in out['frames'] if f['file'] == 'BUILDING.SS' and f['ordinal'] == ordinal)
        meta = manifest['assets'][name]
        assert not frame['formal_assets'] and frame['decode_status'] == 'decoded'
        assert meta['native_ordinal'] == ordinal and meta['native_size'] == frame['size']
        assert meta['native_opaque_pixels'] == frame['opaque_pixels']
        assert meta['original_binding']['BUILDING.SS'] == frame['file_sha256']
        assert meta['original_binding']['encoded_frame_sha256'] == frame['encoded_sha256']
        assert sha(a.assets / name) == meta['sha256'] == ready['new_raw_pngs'][name]
        out['formal_bindings'].append({
            'asset': name, 'asset_sha256': meta['sha256'], 'source_research_id': frame['research_id'],
            'source_file': frame['file'], 'source_ordinal': ordinal,
            'source_encoded_sha256': frame['encoded_sha256'], 'source_indexed_sha256': frame['indexed_sha256'],
            'spec': 'docs/spec/061-hd-building-draw-lifecycle.md',
            'claim': 'one complete verified Main-canvas building draw; cited R91 normal GUI scope only'})
        frame['formal_assets'] = [name]
        frame['runtime_source_evidence'] = 'confirmed complete D46 source and writes, same-value revocations and native Main ownership; normal GUI159/native154'
        frame['source_contract_reference'] = {
            'state': 'CONFORMED', 'spec': 'docs/spec/061-hd-building-draw-lifecycle.md',
            'formal_connected': True, 'review_sha256': sha(a.conformed),
            'scope': 'observed building draw and original placement; forty-frame kernel unchanged; ordinal47 and full HD remain unverified'}
        changed.add(frame['research_id'])
    old = {f['research_id']: f for f in baseline['frames']}
    assert len(changed) == 30 and len(out['formal_bindings']) == 248
    assert all(f == old[f['research_id']] for f in out['frames'] if f['research_id'] not in changed)
    out['formal_manifest_sha256'] = sha(a.assets / 'manifest.json')
    out['coverage_limits']['formal_asset_bindings'] = 248
    out['coverage_limits']['complete_hd'] = False
    out['building_remainder_conformance'] = {
        'ready_sha256': sha(a.ready), 'review_sha256': sha(a.conformed), 'new_ordinals': ordinals,
        'formal_assets': 248, 'gui_samples': 159, 'unique_native_points': 154,
        'claim': 'thirty building sources; full independent Pedia pixels exclude the final inherited-world image; full HD incomplete'}
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('PASS_BUILDING30_CONFORMED_SOURCE_INDEX', 248, sha(a.output), flush=True)


def extend_royal(a):
    baseline, ready, review = read(a.baseline), read(a.ready), read(a.conformed)
    manifest = read(a.assets / 'manifest.json')
    assert ready['result'] == 'PASS_R90_KING1_READY_REVIEW' and ready['state'] == 'READY'
    assert review['result'] == 'PASS_R90_KING1_CONFORMANCE' and review['spec_state'] == 'CONFORMED'
    assert review['sources'] == [992] and review['ready_sha256'] == sha(a.ready)
    assert review['inherited_source_index_sha256'] == sha(a.baseline)
    assert review['inherited_manifest_sha256'] == baseline['formal_manifest_sha256']
    assert review['manifest_sha256'] == sha(a.assets / 'manifest.json')
    assert review['formal_assets'] == len(manifest['assets']) == 218
    assert review['old_raw_pngs_preserved'] == review['old_metadata_preserved'] == 217
    assert review['go_named_passed'] == 48 and review['go_failed'] == review['go_skipped'] == 0
    assert review['full_project_loader_positive']
    assert review['package_files'] == 219 and review['package_faults'] == 10
    assert review['gui_samples'] == 30 and review['unique_native_points'] == 28
    assert review['gui_full_rgba'] == review['gui_x11_rgba'] == 30720000
    assert review['gui_noto_fields'] == 16 and review['native_source_cells'] == 11930
    assert review['typed_underlay_cells'] == 11053 and review['native_underlay_fallback_cells'] == 877
    for key in ['five_languages_both_modes', 'four_cjk_body_cursor_hover_return',
                'normal_departure_removes_royal', 'original_unknown_foreground_preserved',
                'complete_current_publication_required', 'incomplete_generation_cannot_reuse_prior_pose',
                'three_replays_state_audio_save_equal_GUI', 'raw_png_alpha_preserved',
                'native_inputs_rules_and_save_unchanged']:
        assert review[key]
    assert review['actual_inputs'] == 36 and review['replay_end'] == 82400000
    assert not review['complete_hd']
    out = copy.deepcopy(baseline)
    assert len(out['formal_bindings']) == 217 and len(out['frames']) == 1552
    for binding in out['formal_bindings']:
        name = binding['asset']
        assert manifest['assets'][name]['sha256'] == binding['asset_sha256'] == sha(a.assets / name)
    name = 'king1-000.png'
    assert set(manifest['assets']) - {b['asset'] for b in out['formal_bindings']} == {name}
    frame = next(f for f in out['frames'] if f['research_id'] == 992)
    meta = manifest['assets'][name]
    assert frame['file'] == 'KING1.SS' and frame['ordinal'] == 0 and not frame['formal_assets']
    assert frame['size'] == [189, 187] and frame['opaque_pixels'] == 11930
    assert frame['transparency_index'] == 253 and frame['decode_status'] == 'decoded'
    assert sha(a.assets / name) == meta['sha256'] == ready['raw_asset_sha256']
    for key in ['file', 'ordinal', 'file_sha256', 'encoded_sha256', 'indexed_sha256']:
        assert meta['original_source'][key] == frame[key]
    out['formal_bindings'].append({
        'asset': name, 'asset_sha256': meta['sha256'], 'source_research_id': 992,
        'source_file': frame['file'], 'source_ordinal': 0,
        'source_encoded_sha256': frame['encoded_sha256'],
        'source_indexed_sha256': frame['indexed_sha256'],
        'spec': 'docs/spec/069-hd-menu-background-and-textures.md',
        'claim': 'one complete current KING1 pose with typed or original underlay; cited conformance scope only'})
    frame['formal_assets'] = [name]
    frame['runtime_source_evidence'] = 'confirmed complete D66 decode, typed Stage/Main/VGA publication, cursor pairs and current whole pose; normal GUI30/native28 only'
    frame['source_contract_reference'] = {
        'state': 'CONFORMED', 'spec': 'docs/spec/069-hd-menu-background-and-textures.md',
        'formal_connected': True, 'review_sha256': sha(a.conformed),
        'scope': 'one KING1 king and hound pose, raw94/198/100 arguments and observed origin; unknown foreground and native underlay preserved; other poses unverified'}
    old = {f['research_id']: f for f in baseline['frames']}
    assert all(f == old[f['research_id']] for f in out['frames'] if f['research_id'] != 992)
    out['formal_manifest_sha256'] = sha(a.assets / 'manifest.json')
    out['coverage_limits']['formal_asset_bindings'] = 218
    out['coverage_limits']['complete_hd'] = False
    out['royal_foreground_conformance'] = {
        'ready_sha256': sha(a.ready), 'review_sha256': sha(a.conformed), 'sources': [992],
        'formal_assets': 218, 'gui_samples': 30, 'unique_native_points': 28,
        'claim': 'one king and hound pose only; other images, animation and full HD incomplete'}
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('PASS_ROYAL_CONFORMED_SOURCE_INDEX', 218, sha(a.output), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['baseline', 'assets', 'ready', 'conformed', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--royal', action='store_true', help='規格069 R90：只擴充已完成的國王與獵犬來源')
    scope.add_argument('--buildings', action='store_true', help='規格061 R91：只擴充已驗三十個建築來源')
    a = parser.parse_args()
    assert Path('/.dockerenv').exists() and os.getuid() != 0
    assert not a.output.exists() and a.output.parent.stat().st_uid == os.getuid()
    if a.buildings:
        extend_buildings(a)
        return
    if a.royal:
        extend_royal(a)
        return
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
