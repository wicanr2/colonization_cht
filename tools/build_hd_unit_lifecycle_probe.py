"""規格070 DRAFT：131種ICONS來源的唯讀逐寫探針；不安裝HD。"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
parser = argparse.ArgumentParser(description=__doc__)
for name in ['catalog', 'gui-capture', 'inputs', 'reference', 'output']:
    parser.add_argument('--' + name, type=Path, required=True)
a = parser.parse_args()
out = a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid() != 0
assert out.is_relative_to('/out') and out.parent.stat().st_uid == os.getuid() and (not out.exists())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
repo = Path(__file__).resolve().parents[1]
base = repo / 'tools/probe_hd_building_batch.go'
assert sha(base) == '5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6'
assert sha(a.catalog) == 'e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d'
d = json.loads(a.catalog.read_bytes())
sources = [f for f in d['frames'] if f['file'] == 'ICONS.SS']
assert len(sources) == 131 and sorted((f['ordinal'] for f in sources)) == list(range(131))
original = next((f for f in d['files'] if f['file'] == 'ICONS.SS'))
for f in sources:
    assert f['file_sha256'] == original['sha256']
    assert sha(a.catalog.parent / 'pixels' / f"{f['research_id']:04d}.idx") == f['indexed_sha256']
capture = json.loads(a.gui_capture.read_bytes())
points = [f['state'] for f in capture['samples']]
assert all((points[i]['step'] < points[i + 1]['step'] for i in range(len(points) - 1)))
out.mkdir()
points_path = out / 'points.json'
points_path.write_text(json.dumps(points, ensure_ascii=False, indent=2) + '\n')
input_path = a.inputs
input_sha = sha(input_path)
point_sha = sha(points_path)
end_step = points[-1]['step']
assert capture['original_pixels_only'] is True and capture['production_connected_new_sources'] is False
assert len(points) > 1 and all((p['current'] == {'language': 'en', 'graphics': 'original'} and p['action'] == 'open' for p in points))
assert all((len(p['registers']) == 8 and len(p['segments']) == 4 for p in points))
assert all((len(p[k]) == 64 for p in points for k in ['memory_sha256', 'indexed_sha256', 'palette_sha256']))
replay = json.loads(input_path.read_bytes())
assert replay['end'] >= end_step and points[-1]['dos_input_count'] <= len(replay['inputs'])
assert all((e['kind'] in ['move', 'press', 'release', 'enter', 'escape', 'backspace', 'up', 'down', 'left', 'right', 'text'] for e in replay['inputs']))
assert all((replay['inputs'][i]['step'] <= replay['inputs'][i + 1]['step'] for i in range(len(replay['inputs']) - 1)))
s = base.read_text()
start = s.index('var buildingSources = []buildingSource{')
end = s.index('\n}\n', start) + 2
rows = ['var buildingSources = []buildingSource{']
for f in sources:
    rows.append('\t{%d,%d,%d,%d,%d,%s,%s,%d,nil},' % (f['research_id'], *f['size'], f['opaque_pixels'], f['encoded_length'], json.dumps(f['encoded_sha256']), json.dumps(f['indexed_sha256']), f['ordinal']))
rows.append('}')
s = s[:start] + '\n'.join(rows) + s[end:]

def one(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new, 1)
aliases = {f['research_id']: [g['research_id'] for g in d['frames'] if g.get('encoded_sha256') == f['encoded_sha256'] and g['size'] == f['size']] for f in sources}
declaration = '\nvar iconsSourceCandidates = map[int][]int{\n' + '\n'.join((str(k) + ':{' + ','.join(map(str, v)) + '},' for k, v in aliases.items())) + '\n}\n'
s += declaration
one('Ordinal         int               ' + chr(96) + 'json:"ordinal"' + chr(96), 'Ordinal int ' + chr(96) + 'json:"ordinal"' + chr(96) + '\n SourceCandidates []int ' + chr(96) + 'json:"source_candidates"' + chr(96))
one('b.calls = append(b.calls, c)', 'c.SourceCandidates=iconsSourceCandidates[source.Ordinal]\n b.calls = append(b.calls, c)\n if len(c.SourceCandidates)!=1 {c.Mismatch="完整來源清冊有編碼別名，未確認ICONS來源";return}')
one('Raw                                    []byte', 'Native int\n Raw []byte')
one('b == nil || b.m.Steps < 50000000', 'b == nil')
one('if b.m.Steps < 50000000 {\n\t\treturn\n\t}', '')
one('candidate := &buildingSources[i]', 'candidate := &buildingSources[i]\n if int(m.CPU.R[golem.AX]&0x7fff)!=candidate.Native+1 {continue}')
one('wantInput := "9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979"', 'wantInput := ' + json.dumps(input_sha))
one('wantInput = "3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca"', 'wantInput = ' + json.dumps(input_sha))
one('"821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901"', json.dumps(point_sha))
one('len(points) != 49', 'len(points) != ' + str(len(points)))
one('case "enter", "escape", "backspace":', 'case "enter", "escape", "backspace", "up", "down", "left", "right":')
one('"Backspace"}[e.Kind]', '"Backspace", "up":"Up", "down":"Down", "left":"Left", "right":"Right"}[e.Kind]')
one('end := uint64(75900000)', 'end := uint64(' + str(end_step) + ')')
one('end = 134600000', 'end = ' + str(end_step))
one('"BUILDING.SS": "e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4",', '"ICONS.SS": ' + json.dumps(original['sha256']) + ',')
one('candidate := &buildingSources[i]', 'candidate := &buildingSources[i]\n' + ' if int(record[4])!=candidate.Width || int(record[5])!=candidate.Height {continue}')
one('"building-%03d.pixels"', '"%04d.idx"')
one('`json:"ordinal"`', '`json:"research_id"`')
one('import (', 'import (\n "bufio"')
s, count = re.subn('events\\s+\\[\\]map\\[string\\]any', 'eventCount int\n eventLog *bufio.Writer\n eventFile *os.File', s)
assert count == 1
s, count = re.subn('b\\.events\\s*=\\s*append\\(b\\.events,\\s*(map\\[string\\]any\\{[^\\n]+\\})\\)', 'b.event(\\1)', s)
assert count == 2
s = s.replace('len(b.events)', 'b.eventCount').replace('len(observer.events)', 'observer.eventCount')
one('>= 1000000', '>= 8000000')
s, count = re.subn('(observer = &buildingObserver\\{[^\\n]+\\})', '\\1\\n observer.openEvents(filepath.Join(*out,"writes.json"))\\n defer observer.closeEvents()', s)
assert count == 1
one('buildingJSON(filepath.Join(*out, "writes.json"), observer.events)', 'observer.closeEvents()\n result["raw_event_count"]=observer.eventCount')
s += '\nfunc (b *buildingObserver) openEvents(path string) {\n var err error;b.eventFile,err=os.Create(path);buildingNeed(err)\n b.eventLog=bufio.NewWriterSize(b.eventFile,65536);_,err=b.eventLog.WriteString("[\\n");buildingNeed(err)\n}\nfunc (b *buildingObserver) event(value map[string]any) {\n if b.eventCount>=8000000 {panic("小圖像原始事件超過8M有界上限")}\n if b.eventCount>0 {_,err:=b.eventLog.WriteString(",\\n");buildingNeed(err)}\n raw,err:=json.Marshal(value);buildingNeed(err);_,err=b.eventLog.Write(raw);buildingNeed(err);b.eventCount++\n}\nfunc (b *buildingObserver) closeEvents() {\n if b.eventLog==nil{return};_,err:=b.eventLog.WriteString("\\n]\\n");buildingNeed(err)\n buildingNeed(b.eventLog.Flush());buildingNeed(b.eventFile.Close());b.eventLog=nil\n}\n'
s = s.replace('// 規格064 DRAFT：十種城內建築的唯讀正常路徑探針。', '// 規格070 DRAFT：131種ICONS候選的唯讀逐寫探針。')
s = s.replace('readonly-colony-building-batch-normal-input-research', 'readonly-small-images-normal-input-write-research')
s = s.replace('Ten exact decoded sources; no production HD, animation, cursor or RAM restoration claim.', '131 fixed ICONS.SS sources; AX and source must match; unknown writes revoke ownership including same values. No HD, animation, cursor or RAM restoration claim.')
(out / 'main.go').write_text(s)
for name in ['go.mod', 'go.sum', 'go.work']:
    shutil.copyfile(a.reference / name, out / name)
subprocess.run(['gofmt', '-w', 'main.go'], cwd=out, check=True, timeout=30)
subprocess.run(['go', 'build', '-trimpath', '-o', 'small-probe', '.'], cwd=out, check=True, timeout=120)
subprocess.run(['go', 'vet', '.'], cwd=out, check=True, timeout=60)
meta = {'kind': 'DRAFT-all-ICONS-source-native-write-collector', 'gui_inputs_sha256': input_sha, 'dos_inputs_at_end': points[-1]['dos_input_count'], 'gui_points_sha256': point_sha, 'gui_points': len(points), 'end_step': end_step, 'source_count': 131, 'source_receipt_sha256': sha(a.catalog), 'entry_report_sha256': sha(a.gui_capture), 'generator_sha256': sha(Path(__file__)), 'source_base_sha256': sha(base), 'original_file': 'ICONS.SS', 'original_sha256': original['sha256'], 'sources': sources, 'source_sha256': sha(out / 'main.go'), 'binary_sha256': sha(out / 'small-probe'), 'event_storage': 'streamed JSON array', 'event_limit': 8000000, 'production_connected': False, 'ownership': 'unknown writes revoke, including same value'}
(out / 'build.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2) + '\n')
print('PASS_ALL_ICONS_NATIVE_COLLECTOR_BUILD', meta['binary_sha256'], flush=True)
