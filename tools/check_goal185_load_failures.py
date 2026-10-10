#!/usr/bin/env python3
"""四種來源限定讀檔提示的新正式GUI驗收；缺合法原版回77。"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops
from check_goal185_remaining import EXPECTED, pixels, read, sha

BINARY = 'ed5444ea648d551cf8d512d282c1a9b970b6737dd9d5596f048c1869f4d7ad8c'
BASELINE = 'f39336c61f72b27fafb8dd2717d6ed0035c2b1fdb7603167b2d501bbc3193337'
CASES = {
    'error': {'session': 'load-family-error-gui', 'input': '2d0b597df45a20f3f508cf8506cf306107d6518493f48ff7e9c239e8b4043e32', 'samples': 3,
              'shot': 'load-error', 'id': 'GAME.TXT:0x00000971', 'safe': [66,94,233,106], 'offset': 0x971, 'length': 28,
              'source_sha': '3e57ec4ec97e1f19e060fe85e56704bc1f18fec357fcb053f8c4423d48dec53a'},
    'invalid': {'session': 'load-family-invalid-gui', 'input': '91e3fba1c44c9c1de71fb99145734247c791f71b11d11d6293c3508515bcff52', 'samples': 3,
                'shot': 'load-result', 'id': 'GAME.TXT:0x0000088B', 'safe': [66,94,248,106], 'offset': 0x88B, 'length': 34,
                'source_sha': 'e35a1a140176f9b2d726851129a705bacc09b6ebf15cf47a78d54d6c1df359c3'},
    'obsolete': {'session': 'load-family-obsolete-gui', 'input': '0b5292fb51068ab77f9837e5f7500092d27832c2fa5714b7d021b686b6d3df24', 'samples': 3,
                 'shot': 'load-result', 'id': 'GAME.TXT:0x000008C7', 'safe': [66,94,253,106], 'offset': 0x8C7, 'length': 34,
                 'source_sha': '0bc46b070b022832e503f1cac7755f0e037fbc1387906619ea08742d1556301b'},
    'map-size': {'session': 'load-family-map-size-gui', 'input': 'b89b721f428d03bea5acd4f4d52ecaf17263b2f471a34bde62764e8becb7b8ac', 'samples': 7,
                 'shot': 'load-result', 'id': 'GAME.TXT:@LOADSIZE:0x00000904', 'safe': [65,82,254,116], 'offset': 0x904, 'length': 81,
                 'source_sha': 'bf636a831f7676d0669a32481ac9ca783f03c13f0c0ae308389b39815e064d41'},
}


def check_case(game, reports, kind, config):
    gui = reports/config['session']
    assert sha(gui/'gui.inputs.json') == config['input']
    assert sha(Path(read(gui/'session.json')['binary'])) == BINARY
    record = read(gui/'gui.json')
    fault = read(gui/'fault.json')
    assert fault['kind'] == ('remove_private_save_after_slot_list' if kind == 'error' else 'explicit_invalid_header_after_slot_list')
    peers = {mode: reports/('load-family-'+kind+'-'+mode) for mode in ('zh','control','missing','baseline')}
    data = {}
    for mode, root in peers.items():
        data[mode] = read(root/'run.json')
        assert data[mode]['state'] == record['state']
        assert (root/'run.memory').read_bytes() == (gui/'gui.memory').read_bytes()
        assert (root/'raw.wav').read_bytes() == (gui/'raw.wav').read_bytes()
        assert data[mode]['input_hashes'] == record['input_hashes']
        assert {p.name: sha(p) for p in (root/'save').glob('COLONY*.SAV')} == {p.name: sha(p) for p in (gui/'save').glob('COLONY*.SAV')}
        command = read(root/'command.json')
        assert sha(Path(command[0])) == (BASELINE if mode == 'baseline' else BINARY)
        assert Path(command[command.index('--replay-inputs')+1]).samefile(gui/'gui.inputs.json')
        assert ('--control' in command) == (mode == 'control')
        assert ('--missing' in command) == (mode == 'missing')
        assert read(root/'fault-applied.json')['applied']
    assert sha(gui/'save/COLONY03.SAV') == 'd3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
    shots = [line.split() for line in (gui/'gui.shots').read_text().splitlines()]
    assert len(shots) == len({name for name, step in shots}) == config['samples']
    captures = {r['name']: r for r in map(json.loads, (gui/'gui.capture-attempts.jsonl').read_text().splitlines()) if r.get('aligned')}
    cps = {mode: {r['label']: r for r in data[mode]['checkpoints']} for mode in peers}
    changes = []
    for name, step in shots:
        stem = 'run.cp-'+step
        actual = pixels(gui/f'gui.{name}.png')
        assert hashlib.sha256(actual).hexdigest() == captures[name]['capture_rgba_sha256']
        assert captures[name]['frame_step'] == int(step)
        assert actual == pixels(peers['zh']/(stem+'.png'))
        assert pixels(peers['missing']/(stem+'.png')) == pixels(peers['control']/(stem+'.png'))
        for mode, root in peers.items():
            for key in ('memory_sha256','raw_sha256','palette_sha256'):
                assert cps[mode]['cp-'+step][key] == cps['control']['cp-'+step][key]
            for suffix in ('idx','pal'):
                assert (root/(stem+'.'+suffix)).read_bytes() == (peers['control']/(stem+'.'+suffix)).read_bytes()
        with Image.open(gui/f'gui.{name}.png') as im:
            current = im.convert('RGB')
        with Image.open(peers['baseline']/(stem+'.png')) as im:
            old = im.convert('RGB')
        diff = ImageChops.difference(current, old).getbbox()
        if name == config['shot']:
            safe = tuple(v*4 for v in config['safe'])
            assert diff and safe[0] <= diff[0] < diff[2] <= safe[2] and safe[1] <= diff[1] < diff[3] <= safe[3]
            restored = current.copy(); restored.paste(old.crop(safe), safe[:2])
            assert restored.tobytes() == old.tobytes()
            changes.append({'name':name,'safe':safe,'difference':diff})
        else:
            assert diff is None, (kind, name, diff)
    source = (game/'GAME.TXT').read_bytes()[config['offset']:config['offset']+config['length']]
    assert hashlib.sha256(source).hexdigest() == config['source_sha']
    shown = ' '.join(source.decode('cp437').replace('%STRING0','COLONY03.SAV').split())
    events = [r for r in data['zh']['events'] if r.get('stage') == 'source' and r.get('shown') == shown]
    assert len(events) == 1 and events[0]['candidate_id'] == config['id']
    assert events[0]['font_px'] == 30 and events[0]['safe'] == config['safe']
    assert not any(r.get('stage') == 'fallback' and r.get('shown') == shown for r in data['zh']['events'])
    return {'kind':kind,'samples':len(shots),'input_sha256':config['input'],'changes':changes,'state':record['state']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if any(not (a.game/name).is_file() for name in EXPECTED):
        print('SKIP：缺合法原版輸入'); return 77
    for name, expected in EXPECTED.items():
        assert sha(a.game/name) == expected
    results = [check_case(a.game,a.reports,kind,config) for kind,config in CASES.items()]
    result = {'status':'PASS_LOAD_FAILURES_FORMAL','scope':'四種已取證檔名來源、既有槽位標題與原版退出；不外推全文或整個Issue',
              'binary_sha256':BINARY,'cases':results}
    a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(result['status'],sum(r['samples'] for r in results));return 0


if __name__ == '__main__':
    raise SystemExit(main())
