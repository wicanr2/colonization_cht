#!/usr/bin/env python3
"""本版正常PEDIA只建立六類：原檔初始化、原版標記、heap鏈與既有GUI。"""
import argparse
import hashlib
import json
from pathlib import Path
from check_goal185_representatives import check as check_representatives

EXE_SHA='a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3'
MEM_SHA='dc72e31004fd8afcdaec14873233f26611f4b4d2b4bfae1844bbfd261e09774f'
MARKER_SHA='40fbf74057eb125676157ae98db130cd7b423e1da1daad7e027d2f2627a524c8'
INIT_SHA='6bec9609b21472ae00b8ffee8044f96536f9af9a26766a675f22dffbddc5d049'
NAMES=['Cargo Types','Unit Types','Terrain Types','Colonist Skills','Colony Buildings','Founding Fathers']
PUSHES=[0x72ad3,0x72aee,0x72b09,0x72b3c,0x72b57,0x72b72]
READS=[0x72ad5,0x72af0,0x72b0b,0x72b3e,0x72b59,0x72b74]
ADDS=[0x72ae6,0x72b01,0x72b1c,0x72b4f,0x72b6a,0x72b85]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):return json.loads(path.read_text())

def check(game,reports):
    binary=(game/'VICEROY.EXE').read_bytes();assert hashlib.sha256(binary).hexdigest()==EXE_SHA
    assert sha(game/'MENU.TXT')=='5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702'
    assert sha(game/'PEDIA.TXT')=='cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1'
    proof=check_representatives(game,reports)
    init_path=reports/'ida-pedia-normal-init-20261009/init.json';assert sha(init_path)==INIT_SHA
    init=read(init_path);assert init['input_sha256']==EXE_SHA and init['ida_version']=='9.4'
    by_offset={int(r['file_offset'],16):r for r in init['records']}
    for index,offset in enumerate(PUSHES):
        expected=bytes([0x6a,0x70+index]);assert binary[offset:offset+2]==expected
        assert bytes.fromhex(by_offset[offset]['bytes'])==expected
    for offset in READS:assert binary[offset:offset+5]==bytes.fromhex('9a1c091f19')
    for offset in ADDS:assert binary[offset:offset+5]==bytes.fromhex('9a3e031f1a')
    assert binary[0x72b8d:0x72b9a]==bytes.fromhex('2bf69ab80f1f198bc65e5fc9cb')
    assert binary[0x23904:0x23910]==bytes.fromhex('8b46062d7000509a72031f19')
    marker_path=reports/'pedia-marker-probe/markers.log.matches.json';assert sha(marker_path)==MARKER_SHA
    marker=read(marker_path);assert len(marker['matches'])==1
    match=marker['matches'][0]
    assert match['header']==match['key']=='@PEDIA' and match['code_bytes']=='f3a6'
    assert match['file_op']['Name']==match['read_op']['Name']=='MENU.TXT'
    assert match['step']==94154050 and match['file_op']['Pos']==1536 and match['file_op']['Len']==265
    memory_path=reports/'pedia-print-stack-observer-v2/memory-104683167.bin';assert sha(memory_path)==MEM_SHA
    memory=memory_path.read_bytes();region=memory[0x73320:0x75320];positions=[]
    for index,name in enumerate(NAMES):
        needle=name.encode()+b'\0';assert region.count(needle)==1
        position=0x73320+region.index(needle);positions.append(position)
        assert int.from_bytes(memory[position-18:position-16],'little')==0x70+index
        name_off=int.from_bytes(memory[position-16:position-14],'little')
        name_seg=int.from_bytes(memory[position-14:position-12],'little')
        assert name_seg*16+name_off==position
    for index,position in enumerate(positions):
        offset=int.from_bytes(memory[position-8:position-6],'little')
        segment=int.from_bytes(memory[position-6:position-4],'little')
        next_node=segment*16+offset
        if index==2:
            # 原版在地形與技能之間插入空白分隔節點，命令0、文字空白。
            assert int.from_bytes(memory[next_node+4:next_node+6],'little')==0
            name_off=int.from_bytes(memory[next_node+6:next_node+8],'little')
            name_seg=int.from_bytes(memory[next_node+8:next_node+10],'little')
            assert memory[name_seg*16+name_off]==0
            offset=int.from_bytes(memory[next_node+14:next_node+16],'little')
            segment=int.from_bytes(memory[next_node+16:next_node+18],'little')
            next_node=segment*16+offset
        assert next_node==(positions[index+1]-22 if index<5 else 0)
    assert b'Miscellaneous\0' not in region and b'Complete\0' not in region
    menu=(game/'MENU.TXT').read_bytes();assert b'  Miscellaneous' in menu and b'  Complete' in menu
    # 正常GUI的六類來源與原版資料鏈相符；靜態6／7分支不當作正常入口。
    runtime=read(reports/'representatives-v2-zh/run.json')
    expected=' '.join(NAMES)
    sources=[e for e in runtime['events'] if e.get('stage')=='source' and e.get('shown')==expected]
    assert sources and all(e['items']==NAMES for e in sources)
    menu_source=sources[0]
    assert menu_source['candidate_id']=='MENU.TXT:0x000006D0+list' and menu_source['safe']==[253,12,314,69] and menu_source['font_px']==21
    menu_ids=['MENU.TXT:@PEDIA:0x'+format(offset,'08X') for offset in [0x67b,0x68a,0x698,0x6a9,0x6bc,0x6d0]]
    menu_bytes=(game/'MENU.TXT').read_bytes()
    for cid,name in zip(menu_ids,NAMES):
        offset=int(cid.rsplit('0x',1)[1],16)
        assert menu_bytes[offset:offset+len(name)+2]==('  '+name).encode()
    original=json.loads((reports/'remaining-representatives-v2-gui/gui.json').read_text())
    result={'result':'PASS','status':'PASS_PEDIA_NORMAL_CATEGORY_BOUNDARY','grade':'confirmed','input':'VICEROY.EXE','input_sha256':EXE_SHA,
        'normal_commands':list(range(0x70,0x76)),'normal_categories':NAMES,'heap_memory_sha256':MEM_SHA,
        'original_initializer_offsets':PUSHES,'dispatcher_offset':0x23904,
        'gui_samples':proof['samples'],'gui_inputs_sha256':proof['input_sha256'],
        'inputs_sha256':proof['input_sha256'],'final_step':original['state']['steps'],
        'final_memory_sha256':original['state']['memory_sha256'],
        'verified_fields':[{'candidate_id':menu_source['candidate_id'],'shown':expected,'safe':menu_source['safe'],'source_ids':menu_ids}],
        'unavailable_category_entries':['Miscellaneous','Complete'],
        'unavailable_source_ids':['MENU.TXT:@PEDIA:0x000006E4','MENU.TXT:@PEDIA:0x000006F5','PEDIA.TXT:@MISCELLANEOUS'],
        'limit':'此版正常百科類別選單無6／7入口；靜態類別分支存在，不宣稱所有概念情境提示都不可達。'}
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--game',type=Path,required=True);p.add_argument('--reports',type=Path,required=True);p.add_argument('--output',type=Path)
    a=p.parse_args()
    if not all((a.game/n).is_file() for n in ['VICEROY.EXE','MENU.TXT','OPENING.EXE','GAME.TXT','LABELS.TXT','NAMES.TXT']):print(json.dumps({'result':'SKIP','reason':'original-files-missing'}));return 77
    result=check(a.game,a.reports)
    if a.output:a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(result,ensure_ascii=False));return 0
if __name__=='__main__':raise SystemExit(main())
