#!/usr/bin/env python3
"""目標180：有限確認TERRAIN8查詢、DOS讀入、標題讀取與已驗GUI；不外推其他同文段落。"""
import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from check_goal179_window import INPUT_SHA, SAVE_SHA, need
from check_goal171_window import dialog_spans


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check_ida_bytes(db, raw):
    """本匯出契約的 EA 0 對應 runtime 9320:0000；逐筆核對而非猜載入基址。"""
    need(db['runtime_mapping']['segment'] == '9320', 'IDA runtime 段不同')
    count = 0
    for window in db['entrypoint_windows']:
        for ins in window['instructions']:
            ea, size = ins['evidence']['ida_raw_ea'], ins['size']
            need(0 <= ea < ea + size <= len(raw) and
                 raw[ea:ea + size].hex() == ins['raw_bytes'] and
                 ins['runtime_address'] == f'9320:{ea:04X}', 'IDA EA／runtime 映射或原始位元組不同')
            count += 1
    need(count > 0, 'IDA 匯出沒有原始指令')
    return count


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--game', type=Path, required=True)
    p.add_argument('--reports', type=Path, required=True)
    p.add_argument('--all-markers', action='store_true', help='另驗全部21次正常地形查詢及其GUI模板關聯')
    p.add_argument('--lookup-reports', type=Path, help='將21項身份關聯綁定另一份已驗正常GUI及其source-query觀測')
    a = p.parse_args()
    if a.lookup_reports and not a.all_markers:
        p.error('--lookup-reports 必須搭配 --all-markers')
    b = a.reports
    if not all((a.game / n).is_file() for n in INPUT_SHA):
        print('SKIP：缺合法原版，未宣稱來源確認')
        return 77
    for name, value in INPUT_SHA.items():
        need(digest(a.game / name) == value, '原版指紋不同：' + name)
    need(digest(b / 'terrain-fixed/scratch/COLONY00.SAV') == SAVE_SHA, '正常存檔指紋不同')
    check = subprocess.run([sys.executable, str(Path(__file__).with_name('check_goal180_window.py')),
                            '--game', str(a.game), '--reports', str(b / 'terrain-fixed'),
                            '--category', 'terrain'], capture_output=True, text=True)
    need(check.returncode == 0, '既有正常GUI與中英／負例檢查未通過：' + check.stderr[-300:])
    image_check = json.loads(check.stdout)
    control = json.loads((b / 'terrain-fixed/replay-control.json').read_text())
    cp = next(c for c in control['checkpoints'] if c['step'] == 76065000)
    for name in ('key-reads', 'key-lookup', 'key-compare', 'key-match', 'key-body-source', 'key-body-read'):
        st = json.loads((b / (name + '.log.state.json')).read_text())
        need(st['step'] == cp['step'] and st['memory_sha256'] == cp['memory_sha256'], name + '原版檢查點不同')
    original = (a.game / 'PEDIA.TXT').read_bytes()
    marker = b'@TERRAIN8\r\n'
    offset = original.index(marker)
    body_offset = offset + len(marker)
    need(original.count(marker) == 1, 'TERRAIN8標記不唯一')
    raw = (b / 'key-body-read.log.raw-read.bin').read_bytes()
    need(raw == original[25600:26112], 'DOS原始512位元組不同')
    io = json.loads((b / 'key-body-source.log.sources.json').read_text())
    need(any(x['Name'] == 'PEDIA.TXT' and x['Step'] == 72495279 and x['Pos'] == 25600 and x['Len'] == 512
             and x['Op'] == 'read' for x in io['file_ops']), '缺原版檔案位移讀取紀錄')
    need(any(x['Name'] == 'PEDIA.TXT' and x['Step'] == 72495279 and x['Seg'] == 0x1C6A
             and x['Off'] == 0xE962 and x['Got'] == 512 for x in io['reads']), '缺DOS讀入RAM定位')
    normalized = raw.replace(b'\r\n', b'\n')
    converted = (b / 'key-body-source.log.stdio-buffer.bin').read_bytes()
    need(converted[:len(normalized)] == normalized, '文字模式有效前綴不同；不能把512位元組全部當有效資料')
    trace = (b / 'key-match.log').read_text().splitlines()
    exact = next(x for x in trace if x.startswith('72515484 0E2D:0832'))
    comparison = exact.split(' |')[-1].split()
    key = b'@TERRAIN8\0'
    pairs = [f'{src:05X}={v:02X}' for i, v in enumerate(key) for src in (0x249DC + i, 0x2AC86 + i)]
    need(comparison[-20:] == pairs, '標記／局部查詢鍵沒有全部同值比較')
    path = {int(x.split()[0]): x for x in trace}
    need('0E2D:083B' in path[72515486] and '9320:00DE' in path[72515493]
         and 'SI=0001' in path[72515493], '未走已確認的匹配成功分支')
    body = original[offset + len(marker):]
    heading = b''.join(body.splitlines(keepends=True)[:2]).replace(b'\r\n', b'\n')
    values = []
    for line in (b / 'key-body-read.log').read_text().splitlines():
        fields = line.split()
        if fields[0] == 'READ' and fields[2] == '0E2D:09F4' and int(fields[1]) > 72515485:
            values.append(int(fields[4].split('=')[1], 16))
    need(bytes(values[:len(heading)]) == heading, '比對後沒有讀取TERRAIN8的版面與標題')
    db = json.loads((b / 'ida-pedia/runtime-lookup-final.json').read_text())
    need(db['tool'] == 'IDA Pro 9.4' and db['input']['sha256'] == digest(b / 'key-body-source.log.lookup-runtime.bin'),
         'IDA工具或runtime輸入不同')
    ida_instructions = check_ida_bytes(db, (b / 'key-body-source.log.lookup-runtime.bin').read_bytes())
    need(any(x['runtime_entry'] == '9320:001A' and x['function_end_exclusive'] == '9320:0106'
             for x in db['database_relations']), '缺實際查找函式邊界')
    evidence_files = ['key-match.log', 'key-compare.log', 'key-body-read.log',
                      'key-body-read.log.raw-read.bin', 'key-body-source.log.sources.json',
                      'key-body-source.log.stdio-buffer.bin', 'ida-pedia/runtime-lookup-final.json']
    aliases = {}
    if a.all_markers:
        lookup_dir = a.lookup_reports or b / 'terrain-fixed'
        match_path = lookup_dir / 'source-query.log.matches.json' if a.lookup_reports else b / 'key-matches-caller.log.matches.json'
        lookup_check, lookup_control = image_check, control
        if a.lookup_reports:
            result = subprocess.run([sys.executable, str(Path(__file__).with_name('check_goal180_window.py')),
                                     '--game', str(a.game), '--reports', str(lookup_dir), '--category', 'terrain',
                                     '--require-no-string-misses'], capture_output=True, text=True)
            need(result.returncode == 0, '目前地形GUI驗收未通過：' + result.stderr[-300:])
            lookup_check = json.loads(result.stdout)
            lookup_control = json.loads((lookup_dir / 'replay-control.json').read_text())
        records = json.loads(match_path.read_text())
        need(records['inputs_sha256'] == lookup_check['inputs_sha256'], '完整查詢觀測使用了另一份GUI輸入')
        need(records['final_step'] == lookup_control['state']['steps'] and
             records['memory_sha256'] == lookup_control['state']['memory_sha256'], '完整查詢觀測原版終點不同')
        matches = records['matches']
        expected_keys = {f'@TERRAIN{i}' for i in list(range(16)) + list(range(24, 29))}
        need(len(matches) == 21 and {x['key'] for x in matches} == expected_keys, '正常查詢不是預期21項')
        zh = json.loads((lookup_dir / 'replay-zh.json').read_text())
        spans = [s for s in dialog_spans(zh) if s[0].startswith('PEDIA.TXT:')]
        shots = dict(line.split() for line in (lookup_dir / 'gui-pedia.shots').read_text().splitlines())
        catalog = Path(__file__).resolve().parents[1] / 'text/pedia-bilingual.tsv'
        table = {x['message_id']: x for x in csv.DictReader(catalog.open(), delimiter='\t', quoting=csv.QUOTE_NONE)}
        normalize = lambda text: ' '.join(text.replace('^', '').replace('{', '').replace('}', '').split())
        previous = 0
        for i, rec in enumerate(matches):
            need(rec['original_cs_ip'] == '0E2D:0832' and rec['code_bytes'] == 'f3a6' and rec['cx'] == 1 and
                 rec['return_cs'] == 0x9320 and rec['return_ip'] == 0xD7 and rec['header'] == rec['key'],
                 '不是已審查找函式的完整匹配')
            marker = (rec['key'] + '\r\n').encode()
            need(original.count(marker) == 1, '原始查詢標記不唯一')
            loc = original.index(marker)
            op, read = rec['file_op'], rec['read_op']
            need(op['Name'] == read['Name'] == 'PEDIA.TXT' and op['Step'] == read['Step'] and
                 op['Step'] <= rec['step'] and op['Pos'] <= loc + len(marker) - 1 < op['Pos'] + op['Len'],
                 '查詢標記沒有對應PEDIA讀入位置')
            step = int(shots[f'terrain-article-{i}'])
            active = [(cid, lo) for cid, lo, hi, safe in spans if lo <= step < hi]
            need(len(active) == 1 and previous < rec['step'] <= active[0][1] <= step, '匹配與GUI頁面沒有唯一時序關聯')
            source, template = 'PEDIA.TXT:' + rec['key'], active[0][0]
            need(normalize(table[source]['source_en']) == normalize(table[template]['source_en']) and
                 normalize(table[source]['zh_hant']) == normalize(table[template]['zh_hant']), '查詢段落與顯示模板內容不同')
            if source != template:
                aliases[template] = source
            previous = step
        need(len(aliases) == 5, '同文模板與查詢來源關聯不是預期五組')
        evidence_files.append(str(match_path.relative_to(b)))
    print(json.dumps({'result': 'PASS', 'grade': 'confirmed', 'source_key': 'PEDIA.TXT:@TERRAIN8',
                      'source_marker_file_offset': offset, 'source_body_file_offset': body_offset,
                      'template_key': 'PEDIA.TXT:@TERRAIN16', 'heading_bytes_verified': len(heading),
                      'original_checkpoint_step': cp['step'], 'original_memory_sha256': cp['memory_sha256'],
                      'ida_instructions_verified': ida_instructions,
                      'gui_inputs_sha256': image_check['inputs_sha256'], 'input_fingerprints': INPUT_SHA,
                      'evidence_sha256': {n: digest(b / n) for n in evidence_files},
                      'normal_lookup_count': 21 if a.all_markers else 1, 'observed_template_source_aliases': aliases,
                      'lookup_gui_inputs_sha256': lookup_check['inputs_sha256'] if a.all_markers else None,
                      'lookup_original_step': lookup_control['state']['steps'] if a.all_markers else None,
                      'lookup_original_memory_sha256': lookup_control['state']['memory_sha256'] if a.all_markers else None,
                      'limit': ('確認本路徑21次查詢與GUI模板關聯；只有TERRAIN8初始29位元組具直接讀取補證，未驗其他路徑或全文每位元組鏈'
                                if a.all_markers else '只確認本路徑TERRAIN8查詢及後續標題；跨緩衝正文全位元組鏈未驗，不外推其他同文鍵')},
                     ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
