#!/usr/bin/env python3
"""#57完成審查：全部來源接線、保留逐類驗收、正常代表GUI與版本入口限制。"""
import argparse
import csv
import hashlib
import json
from pathlib import Path
from check_goal185_pedia_boundary import check as check_boundary

AUDIT_SHA='b4a3117552389ef59467ef47425c6fd3eeee11ad6c54e7684cc745de3c813157'
BASELINE_SHA='a2a7be55c47c3084527d6169627d80a9206970069170c830922d004a89999c3c'
META_SHA='7b1b8c10a523965333d7c6eedfbf16859fb85f552632f3e65c9bc3442495181e'
ACCEPTED=['pedia-cargo-all','pedia-unit-all','pedia-terrain-all','pedia-job-all','pedia-father-all','pedia-building-all']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def check(game,reports,repo):
    boundary=check_boundary(game,reports)
    # 已完成百科的後續共用角色回歸：必須仍是相同內容及當前正式來源。
    source_pairs=[('dialog.go','dialog_overlay.go'),('strings.go','string_overlay.go'),('adapter.go','live_menu.go')]
    candidates=[reports/'pedia-current-connection-audit',reports/'pedia-one-port-connection-audit',
                reports/'menu-survival-connection-audit', reports/'port-family-connection-audit',
                reports/'build-transaction-connection-audit', reports/'reprint-frame-connection-audit',
                reports/'unit-caption-city-connection-audit',reports/'orders-compact-connection-audit',
                reports/'sea-city-variable-connection-audit',reports/'trade-fields-connection-audit',
                reports/'issue56-source-connection-audit']
    matching=[directory for directory in candidates
              if (directory/'pedia-connection-audit.json').is_file() and sha(directory/'pedia-connection-audit.json')==AUDIT_SHA
              and all((directory/name).read_bytes()==(repo/'tools'/formal).read_bytes() for name,formal in source_pairs)]
    assert matching, '缺與目前正式來源相同的完整百科接線審查'
    audit_directory=matching[0]
    audit_path=audit_directory/'pedia-connection-audit.json'
    audit=read(audit_path);assert audit['body_count']==164 and audit['label_count']==19
    assert all(r['connected'] for r in audit['bodies']+audit['labels'])
    bodies=list(csv.DictReader((repo/'text/pedia-bilingual.tsv').open(),delimiter='\t'))
    expected={row['message_id'] for row in bodies if row['source_file']=='PEDIA.TXT'}
    assert {r['id'] for r in audit['bodies']}==expected and len(expected)==164
    adapter=(repo/'tools/live_menu.go').read_text()
    assert 'dlg.cat.addPedia(' in adapter
    assert sha(repo/'docs/text-census-baseline.tsv')==BASELINE_SHA and sha(repo/'docs/text-census-baseline.json')==META_SHA
    meta=read(repo/'docs/text-census-baseline.json')
    for name,digest in meta['originals'].items():assert sha(game/name)==digest
    config=read(repo/'tools/verification-matrix.json')
    assert set(ACCEPTED)<=set(meta['historical_row_ids'])
    assert set(ACCEPTED)<={r['id'] for r in config['rows']}
    # 保留使用者已接受的六類正常逐篇驗收；不冒稱舊目錄又重新走過。
    assert '歷史矩陣報表原文封存' in (repo/'WORKLOG.md').read_text()
    census={r['id']:r for r in csv.DictReader((repo/'docs/text-census.tsv').open(),delimiter='\t')}
    for key in boundary['unavailable_source_ids']:
        assert census[key]['status']=='unreachable' and census[key]['reach']=='unreachable'
        assert census[key]['evidence']=='confirmed 正常類別入口限制'
    protected=['PEDIA.TXT:@TERRAIN16','PEDIA.TXT:@TERRAIN17','PEDIA.TXT:@TERRAIN18','PEDIA.TXT:@TERRAIN19','PEDIA.TXT:@TERRAIN23']
    assert all(census[key]['status']!='shown' for key in protected)
    return {'result':'PASS','status':'PASS_ISSUE57_COMPLETION_AUDIT','issue':57,
        'requirements':{'all_164_bodies_connected':True,'all_19_labels_connected':True,
            'six_category_normal_acceptance_retained':ACCEPTED,'current_representative_gui_samples':boundary['gui_samples'],
            'same_state_and_reverse_fallback':True,'misc_complete_version_limit_confirmed':boundary['unavailable_category_entries'],
            'matrix_and_census_updated':True},
        'connection_audit_sha256':AUDIT_SHA,'census_sha256':sha(repo/'docs/text-census.tsv'),
        'limitations':['歷史六類逐篇驗收保留，不聲稱全164來源都新正常命中。','同文地形原始段落歸屬保留強推論，不提高shown數。','未建立的兩個類別入口不修改原版；概念情境提示不由此宣稱不可達。']}

def main():
    p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--repo',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not all((a.game/n).is_file() for n in ['VICEROY.EXE','MENU.TXT','PEDIA.TXT','GAME.TXT','NAMES.TXT','OPENING.EXE']):print(json.dumps({'result':'SKIP','reason':'original-files-missing'}));return 77
    result=check(a.game,a.reports,a.repo)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
