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


def extend_terrain_foreground(a):
    """規格067 R93：只登錄已驗八個Main前景，保留原Stage與發布邊界。"""
    baseline, ready, review = read(a.baseline), read(a.ready), read(a.conformed)
    manifest = read(a.assets / 'manifest.json')
    ordinals = [22, 26, 64, 81, 82, 84, 85, 149]
    ids = [1288 + n for n in ordinals]
    names = {'terrain-%03d.png' % n for n in ordinals}
    assert ready['result'] == 'PASS_R93_FOREGROUND_EIGHT_READY_REVIEW' and ready['spec_state'] == 'READY'
    assert ready['source_frames'] == ordinals and ready['source_research_ids'] == ids
    assert review['result'] == 'PASS_R93_EIGHT_FOREGROUND_CONFORMANCE' and review['spec_state'] == 'CONFORMED'
    assert review['sources'] == ids and review['ready_sha256'] == sha(a.ready)
    assert review['inherited_source_index_sha256'] == sha(a.baseline)
    assert review['inherited_manifest_sha256'] == baseline['formal_manifest_sha256']
    assert review['manifest_sha256'] == sha(a.assets / 'manifest.json')
    assert review['formal_assets'] == len(manifest['assets']) == 269
    assert review['old_raw_pngs_preserved'] == review['old_metadata_preserved'] == 261
    assert review['go_named_passed'] == 14 and review['go_failed'] == review['go_skipped'] == 0
    assert review['package_files'] == 270 and review['package_faults'] == 31
    assert review['gui_samples'] == 42 and review['unique_native_points'] == 39
    assert review['gui_full_rgba'] == 41 * 1280 * 800
    assert review['gui_x11_rgba'] == 42 * 1280 * 800 and review['gui_noto_fields'] == 330
    assert review['foreground_alpha_pixels'] == 329859 and review['foreground_water_pixels'] == 9936
    assert review['actual_inputs'] == 58 and review['replay_end'] == 105800000
    for key in ['full_project_loader_positive', 'all8_normal_pedia_HD',
                'five_languages_both_modes', 'all8_TC_cursor_hover_return',
                'SC_JP_KR_representative_cursor_hover_return', 'normal_close_removes_foreground',
                'native_unknown_foreground_and_cursor_preserved', 'water_palette_and_raw_alpha_preserved',
                'three_replays_state_audio_save_equal_GUI', 'native_inputs_rules_and_save_unchanged']:
        assert review[key]
    assert not review['new_stage_scope'] and not review['new_published_scope']
    assert not review['complete_hd'] and not review['new_release']
    out = copy.deepcopy(baseline)
    assert len(out['formal_bindings']) == 261 and len(out['frames']) == 1552
    old = {f['research_id']: f for f in baseline['frames']}
    frames = {f['research_id']: f for f in out['frames']}
    for b in out['formal_bindings']:
        assert manifest['assets'][b['asset']]['sha256'] == b['asset_sha256'] == sha(a.assets / b['asset'])
    assert set(manifest['assets']) - {b['asset'] for b in out['formal_bindings']} == names
    for n, ident in zip(ordinals, ids):
        name = 'terrain-%03d.png' % n
        frame, meta, asset = frames[ident], manifest['assets'][name], ready['assets'][str(n)]
        assert frame['file'] == 'PHYS0.SS' and frame['ordinal'] == n and frame['size'] == [16, 16]
        assert not frame['formal_assets'] and frame['decode_status'] == 'decoded'
        original = meta['original_source']
        assert original['file'] == frame['file'] and original['ordinal'] == n
        assert original['sha256'] == frame['file_sha256']
        assert original['encoded_sha256'] == frame['encoded_sha256'] and original['indexed_sha256'] == frame['indexed_sha256']
        assert original['encoded_length'] == frame['encoded_length'] and original['opaque_cells'] == frame['opaque_pixels']
        assert sha(a.assets / name) == meta['sha256'] == asset['SHA']
        assert meta['sample_rect'] == asset['Sample'] and meta['native_content_rect'] == asset['Content']
        out['formal_bindings'].append({
            'asset': name, 'asset_sha256': meta['sha256'], 'source_research_id': ident,
            'source_file': frame['file'], 'source_ordinal': n,
            'source_encoded_sha256': frame['encoded_sha256'], 'source_indexed_sha256': frame['indexed_sha256'],
            'spec': 'docs/spec/067-hd-world-terrain-batch.md',
            'claim': 'R93 normal Main Pedia scope only; complete current RGBA/X11, palette and alpha retained'})
        frame['formal_assets'] = [name]
        frame['runtime_source_evidence'] = 'confirmed complete D46 Main decode, verified backing copy, cursor handling and unknown same-value revocation; normal Grassland5'
        frame['source_contract_reference'] = {
            'state': 'CONFORMED', 'spec': 'docs/spec/067-hd-world-terrain-batch.md',
            'formal_connected': True, 'review_sha256': sha(a.conformed),
            'scope': 'R93 GUI42/native39; Main only; no new world Stage, published fallback, other images or full HD credit'}
    assert len(out['formal_bindings']) == 269
    assert all(f == old[f['research_id']] for f in out['frames'] if f['research_id'] not in ids)
    out['formal_manifest_sha256'] = sha(a.assets / 'manifest.json')
    out['coverage_limits']['formal_asset_bindings'] = 269
    out['coverage_limits']['complete_hd'] = False
    out['terrain_foreground_conformance'] = {
        'ready_sha256': sha(a.ready), 'review_sha256': sha(a.conformed), 'sources': ids,
        'formal_assets': 269, 'gui_samples': 42, 'unique_native_points': 39,
        'claim': 'eight Main Pedia foregrounds only; complete Pedia pixels and X11; new Stage/published scope and full HD incomplete'}
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('PASS_TERRAIN_FOREGROUND8_CONFORMED_SOURCE_INDEX', 269, sha(a.output), flush=True)


def extend_terrain_remainder(a):
    """規格067 R94：只登錄已驗三十三個Main前景，保留原Stage與發布邊界。"""
    baseline, ready, review = read(a.baseline), read(a.ready), read(a.conformed)
    manifest = read(a.assets / 'manifest.json')
    ordinals = [37,38,39,41,42,43,45,46,47,53,54,55,57,58,59,61,62,63,69,70,73,75,90,91,92,93,94,95,97,98,99,101,102]
    ids = [1288 + n for n in ordinals]
    names = {'terrain-%03d.png' % n for n in ordinals}
    assert ready['result'] == 'PASS_R94_READY_33_MAIN_FOREGROUNDS' and ready['state'] == 'READY'
    assert ready['source_ordinals'] == ordinals and ready['source_cells'] == 5265
    assert sha(a.ready) == 'f6d3c9b209cf7e29c4d95795dbe7b01f2e7c55d840889dcc95655f0cf86b9265'
    assert review['result'] == 'PASS_R94_THIRTYTHREE_FOREGROUND_CONFORMANCE' and review['spec_state'] == 'CONFORMED'
    assert review['sources'] == ids and review['ready_sha256'] == sha(a.ready)
    assert review['inherited_source_index_sha256'] == sha(a.baseline)
    assert review['inherited_manifest_sha256'] == baseline['formal_manifest_sha256']
    assert review['manifest_sha256'] == sha(a.assets / 'manifest.json')
    assert review['formal_assets'] == len(manifest['assets']) == 302
    assert review['old_raw_pngs_preserved'] == review['old_metadata_preserved'] == 269
    assert review['go_named_passed'] == 682 and review['go_failed'] == review['go_skipped'] == 0
    assert review['package_files'] == 303 and review['package_faults'] == 106
    assert review['gui_samples'] == 96 and review['unique_native_points'] == 86
    assert review['gui_full_rgba'] == 95 * 1280 * 800
    assert review['gui_x11_rgba'] == 96 * 1280 * 800 and review['gui_noto_fields'] == 816
    assert review['remaining_alpha_pixels'] == 720534 and review['foreground_alpha_pixels'] == 1165193 and review['foreground_water_pixels'] == 16560
    assert review['actual_inputs'] == 163 and review['replay_end'] == 278600000
    for key in ['full_project_loader_positive', 'all33_normal_pedia_HD',
                'five_languages_both_modes', 'representative_CJK_cursor_hover_return',
                'all33_have_independent_generated_RGBA', 'normal_close_removes_foreground',
                'native_unknown_foreground_and_cursor_preserved', 'water_palette_and_raw_alpha_preserved',
                'three_replays_state_audio_save_equal_GUI', 'native_inputs_rules_and_save_unchanged']:
        assert review[key]
    assert not review['new_stage_scope'] and not review['new_published_scope']
    assert not review['complete_hd'] and not review['new_release']
    out = copy.deepcopy(baseline)
    assert len(out['formal_bindings']) == 269 and len(out['frames']) == 1552
    old = {f['research_id']: f for f in baseline['frames']}
    frames = {f['research_id']: f for f in out['frames']}
    for b in out['formal_bindings']:
        assert manifest['assets'][b['asset']]['sha256'] == b['asset_sha256'] == sha(a.assets / b['asset'])
    assert set(manifest['assets']) - {b['asset'] for b in out['formal_bindings']} == names
    for n, ident in zip(ordinals, ids):
        name = 'terrain-%03d.png' % n
        frame, meta = frames[ident], manifest['assets'][name]
        assert frame['file'] == 'PHYS0.SS' and frame['ordinal'] == n and frame['size'] == [16, 16]
        assert not frame['formal_assets'] and frame['decode_status'] == 'decoded'
        original = meta['original_source']
        assert original['file'] == frame['file'] and original['ordinal'] == n
        assert original['sha256'] == frame['file_sha256']
        assert original['encoded_sha256'] == frame['encoded_sha256'] and original['indexed_sha256'] == frame['indexed_sha256']
        assert original['encoded_length'] == frame['encoded_length'] and original['opaque_cells'] == frame['opaque_pixels']
        assert sha(a.assets / name) == meta['sha256']
        assert meta['ready_review_sha256'] == sha(a.ready)
        assert len(meta['sample_rect']) == len(meta['native_content_rect']) == 4 and meta['size'] == [1254,1254]
        out['formal_bindings'].append({
            'asset': name, 'asset_sha256': meta['sha256'], 'source_research_id': ident,
            'source_file': frame['file'], 'source_ordinal': n,
            'source_encoded_sha256': frame['encoded_sha256'], 'source_indexed_sha256': frame['indexed_sha256'],
            'spec': 'docs/spec/067-hd-world-terrain-batch.md',
            'claim': 'R94 normal Main Pedia scope only; complete current RGBA/X11, palette and alpha retained'})
        frame['formal_assets'] = [name]
        frame['runtime_source_evidence'] = 'confirmed complete D46 Main decode, verified backing copy, cursor handling and unknown same-value revocation; normal eleven terrain pages'
        frame['source_contract_reference'] = {
            'state': 'CONFORMED', 'spec': 'docs/spec/067-hd-world-terrain-batch.md',
            'formal_connected': True, 'review_sha256': sha(a.conformed),
            'scope': 'R94 GUI96/native86; Main only; no new world Stage, published fallback, other images or full HD credit'}
    assert len(out['formal_bindings']) == 302
    assert all(f == old[f['research_id']] for f in out['frames'] if f['research_id'] not in ids)
    out['formal_manifest_sha256'] = sha(a.assets / 'manifest.json')
    out['coverage_limits']['formal_asset_bindings'] = 302
    out['coverage_limits']['complete_hd'] = False
    out['terrain_remaining_conformance'] = {
        'ready_sha256': sha(a.ready), 'review_sha256': sha(a.conformed), 'sources': ids,
        'formal_assets': 302, 'gui_samples': 96, 'unique_native_points': 86,
        'claim': '33 Main Pedia foregrounds only; complete Pedia pixels and X11; new Stage/published scope and full HD incomplete'}
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('PASS_TERRAIN_REMAINDER33_CONFORMED_SOURCE_INDEX', 302, sha(a.output), flush=True)


def extend_terrain_textures(a):
    """規格071／065 R92：只登錄已驗十二材質與施工槌，保持世界畫素邊界。"""
    baseline, ready, review = read(a.baseline), read(a.ready), read(a.conformed)
    manifest = read(a.assets / 'manifest.json')
    ids = [881, *range(1477, 1489)]
    names = {'icons-054.png', *('terrain-texture-%03d.png' % n for n in range(12))}
    assert ready['state'] == 'READY' and {v['file'] for v in ready['assets']} == names
    assert review['result'] == 'PASS_R92_TERRAIN12_HAMMER54_CONFORMANCE'
    assert review['spec_state'] == 'CONFORMED' and review['sources'] == ids
    assert review['ready_sha256'] == sha(a.ready)
    assert review['inherited_source_index_sha256'] == sha(a.baseline)
    assert review['inherited_manifest_sha256'] == baseline['formal_manifest_sha256']
    assert review['manifest_sha256'] == sha(a.assets / 'manifest.json')
    assert review['formal_assets'] == len(manifest['assets']) == 261
    assert review['old_raw_pngs_preserved'] == review['old_metadata_preserved'] == 248
    assert review['go_named_passed'] == 11 and review['go_failed'] == review['go_skipped'] == 0
    assert review['package_files'] == 262 and review['package_faults'] == 46
    assert review['gui_samples'] == 135 and review['unique_native_points'] == 112
    assert review['gui_full_rgba'] == 114 * 1280 * 800
    assert review['gui_x11_rgba'] == 135 * 1280 * 800 and review['gui_noto_fields'] == 160
    assert review['world_new_terrain_rgba'] == 2421136 and review['actual_inputs'] == 375
    assert review['hammer_positive_GUI_samples'] == 14
    assert {k: (v['actual_inputs'], v['end']) for k, v in review['cohorts'].items()} == {
        'main': (177, 304200000), 'supplement': (76, 131400000), 'remaining': (122, 191200000)}
    for key in ['full_project_loader_positive', 'all20_terrain_topics',
                'all12_materials_have_normal_pedia_HD', 'two_hammer_pedia_positions',
                'five_languages_both_modes_world_arctic_hammer',
                'four_cjk_cursor_hover_return_three_contexts', 'normal_close_removes_hammer',
                'native_foreground_and_cursor_preserved', 'eight_water_palette_rotations_preserved',
                'three_replays_each_cohort_state_audio_save_equal_GUI', 'raw_png_alpha_preserved',
                'native_inputs_rules_and_save_unchanged']:
        assert review[key]
    assert not review['complete_hd'] and not review['new_release']
    out = copy.deepcopy(baseline)
    assert len(out['formal_bindings']) == 248 and len(out['frames']) == 1552
    old = {f['research_id']: f for f in baseline['frames']}
    frames = {f['research_id']: f for f in out['frames']}
    for binding in out['formal_bindings']:
        name = binding['asset']
        assert manifest['assets'][name]['sha256'] == binding['asset_sha256'] == sha(a.assets / name)
    assert set(manifest['assets']) - {b['asset'] for b in out['formal_bindings']} == names
    for asset in ready['assets']:
        name, ident = asset['file'], asset['research_id']
        frame, meta = frames[ident], manifest['assets'][name]
        terrain = ident >= 1477
        assert ident in ids and not frame['formal_assets'] and frame['decode_status'] == 'decoded'
        assert frame['file'] == ('TERRAIN.SS' if terrain else 'ICONS.SS')
        assert frame['size'] == ([16, 16] if terrain else [8, 12])
        assert frame['opaque_pixels'] == (256 if terrain else 40)
        assert meta['native_ordinal'] == frame['ordinal'] == asset['native_ordinal']
        assert meta['native_size'] == frame['size']
        assert meta['original_binding'][frame['file']] == frame['file_sha256']
        assert meta['original_binding']['encoded_frame_sha256'] == frame['encoded_sha256']
        assert sha(a.assets / name) == meta['sha256'] == asset['raw_sha256']
        spec = 'docs/spec/071-hd-terrain-texture-tiles.md' if terrain else 'docs/spec/065-hd-small-images.md'
        out['formal_bindings'].append({
            'asset': name, 'asset_sha256': meta['sha256'], 'source_research_id': ident,
            'source_file': frame['file'], 'source_ordinal': frame['ordinal'],
            'source_encoded_sha256': frame['encoded_sha256'], 'source_indexed_sha256': frame['indexed_sha256'],
            'spec': spec, 'claim': 'R92 normal Main-source scope only; complete Pedia pixels and scoped world material pixels'})
        frame['formal_assets'] = [name]
        frame['runtime_source_evidence'] = (
            'confirmed complete 16x16 auxiliary D46 source, verified forward copies, same-value revocations and eight DAC rotations; normal20 Pedia topics'
            if terrain else 'confirmed complete D46 source and shared small-image lifecycle; two normal Pedia positions')
        frame['source_contract_reference'] = {
            'state': 'CONFORMED', 'spec': spec, 'formal_connected': True, 'review_sha256': sha(a.conformed),
            'scope': 'R92 GUI135/native112; world new-material pixels only; published-VGA fallback, other images and full HD not newly conformed'}
    assert len(out['formal_bindings']) == 261
    assert all(f == old[f['research_id']] for f in out['frames'] if f['research_id'] not in ids)
    out['formal_manifest_sha256'] = sha(a.assets / 'manifest.json')
    out['coverage_limits']['formal_asset_bindings'] = 261
    out['coverage_limits']['complete_hd'] = False
    out['terrain_texture_conformance'] = {
        'ready_sha256': sha(a.ready), 'review_sha256': sha(a.conformed), 'sources': ids,
        'formal_assets': 261, 'gui_samples': 135, 'unique_native_points': 112,
        'claim': 'twelve material sources and one hammer; full Pedia pixels, scoped new world material pixels and complete X11; full HD incomplete'}
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('PASS_TERRAIN12_HAMMER_CONFORMED_SOURCE_INDEX', 261, sha(a.output), flush=True)


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


def extend_terrain_main_surfaces(a):
    """規格067 R95：追加六個已驗Main表面，保留所有既有Stage契約。"""
    baseline, ready, review = read(a.baseline), read(a.ready), read(a.conformed)
    manifest = read(a.assets / 'manifest.json')
    ordinals = [71, 74, 77, 78, 79, 96]
    ids = [1288 + n for n in ordinals]
    assert ready['result'] == 'PASS_R95_READY_SIX_MAIN_SURFACE_EXTENSIONS'
    assert ready['spec_state'] == 'READY' and ready['source_ordinals'] == ordinals
    assert sha(a.ready) == 'c34a4004a984b92c1a26b7f67cb7b65bd5a3b8c9892d23508877d68c3f44dac3'
    assert review['result'] == 'PASS_R95_SIX_MAIN_SURFACE_CONFORMANCE'
    assert review['spec_state'] == 'CONFORMED' and review['sources'] == ids
    assert review['ready_sha256'] == sha(a.ready)
    assert review['inherited_source_index_sha256'] == sha(a.baseline)
    assert review['inherited_manifest_sha256'] == baseline['formal_manifest_sha256']
    assert review['manifest_sha256'] == sha(a.assets / 'manifest.json')
    assert review['formal_assets'] == len(manifest['assets']) == 302
    assert review['new_raw_pngs'] == 0 and review['all_raw_pngs_preserved'] == 302
    assert review['other_metadata_preserved'] == 296
    assert review['go_named_passed'] == 850 and review['go_failed'] == review['go_skipped'] == 0
    assert review['loader_frames'] == 54 and review['current_loader_faults'] == 7
    assert review['inherited_loader_faults'] == 163 and review['full_project_loader_positive']
    assert review['package_files'] == 303 and review['package_faults'] == 25
    assert review['gui_samples'] == 54 and review['unique_native_points'] == 44
    assert review['gui_full_rgba'] == 54272000 and review['gui_x11_rgba'] == 55296000
    assert review['gui_noto_fields'] == 560 and review['legacy_Main_alpha_pixels'] == 289751
    assert review['actual_inputs'] == 68 and review['replay_end'] == 117800000
    for key in ['all6_five_languages_both_modes', 'all6_TC_cursor_hover_return',
                'representative_other3_CJK_cursor_hover_return', 'normal_close_removes_Main_origins',
                'source_Main_Stage_identity_independently_verified', 'existing_Stage_policy_preserved',
                'dedicated79_Stage_runtime_unchanged', 'raw_png_alpha_preserved',
                'three_replays_state_audio_save_equal_GUI', 'native_inputs_rules_and_save_unchanged']:
        assert review[key]
    assert not review['new_stage_scope'] and not review['new_published_scope']
    assert not review['complete_hd'] and not review['new_release']
    out = copy.deepcopy(baseline)
    assert len(out['frames']) == 1552 and len(out['formal_bindings']) == 302
    frames = {f['research_id']: f for f in out['frames']}
    for binding in out['formal_bindings']:
        name = binding['asset']
        assert binding['asset_sha256'] == manifest['assets'][name]['sha256'] == sha(a.assets / name)
        if binding['source_research_id'] not in ids:
            continue
        frame = frames[binding['source_research_id']]
        extension = manifest['assets'][name]['main_surface_extension']
        assert frame['file'] == extension['source_file'] == 'PHYS0.SS'
        assert frame['ordinal'] == extension['source_ordinal'] in ordinals
        assert extension['source_research_id'] == frame['research_id']
        assert extension['source_file_sha256'] == frame['file_sha256']
        assert extension['encoded_sha256'] == frame['encoded_sha256']
        assert extension['indexed_sha256'] == frame['indexed_sha256']
        assert extension['ready_review_sha256'] == sha(a.ready)
        assert extension['destination_linear'] == '0x2CAE0'
        assert frame['formal_assets'] == [name]
        contract = {
            'state': 'CONFORMED', 'spec': 'docs/spec/067-hd-world-terrain-batch.md',
            'formal_connected': True, 'review_sha256': sha(a.conformed),
            'origin_surface': 'Main',
            'scope': 'R95 GUI54/native44; existing PNG reused; prior Stage contracts retained; no new Stage, published or full HD credit'}
        binding['additional_source_contracts'] = [contract]
        frame['additional_source_contract_references'] = [contract]
    old = {f['research_id']: f for f in baseline['frames']}
    assert all(f == old[f['research_id']] for f in out['frames'] if f['research_id'] not in ids)
    out['formal_manifest_sha256'] = sha(a.assets / 'manifest.json')
    out['coverage_limits']['formal_asset_bindings'] = 302
    out['coverage_limits']['complete_hd'] = False
    out['terrain_main_surface_conformance'] = {
        'ready_sha256': sha(a.ready), 'review_sha256': sha(a.conformed), 'sources': ids,
        'formal_assets': 302, 'new_raw_pngs': 0, 'gui_samples': 54, 'unique_native_points': 44,
        'claim': 'six additional Main Pedia surfaces only; all prior source contracts retained; full HD incomplete'}
    a.output.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
    print('PASS_TERRAIN_MAIN6_CONFORMED_SOURCE_INDEX', 302, sha(a.output), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['baseline', 'assets', 'ready', 'conformed', 'output']:
        parser.add_argument('--' + name, type=Path, required=True)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument('--royal', action='store_true', help='規格069 R90：只擴充已完成的國王與獵犬來源')
    scope.add_argument('--buildings', action='store_true', help='規格061 R91：只擴充已驗三十個建築來源')
    scope.add_argument('--terrain-textures', action='store_true', help='規格071／065 R92：只擴充已驗十二材質與施工槌')
    scope.add_argument('--terrain-foreground', action='store_true', help='規格067 R93：只擴充已驗八個Main前景')
    scope.add_argument('--terrain-remainder', action='store_true', help='規格067 R94：只擴充已驗三十三個Main前景')
    scope.add_argument('--terrain-main-surfaces', action='store_true', help='規格067 R95：追加六個既有素材的Main表面')
    a = parser.parse_args()
    assert Path('/.dockerenv').exists() and os.getuid() != 0
    assert not a.output.exists() and a.output.parent.stat().st_uid == os.getuid()
    if a.terrain_main_surfaces:
        extend_terrain_main_surfaces(a)
        return
    if a.terrain_remainder:
        extend_terrain_remainder(a)
        return
    if a.terrain_foreground:
        extend_terrain_foreground(a)
        return
    if a.terrain_textures:
        extend_terrain_textures(a)
        return
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
