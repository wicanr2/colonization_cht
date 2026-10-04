#!/usr/bin/env python3
"""在 Docker 內核對正常船隻／VIEW 中文與逐列 MENU 來源；原版衍生收據只留 workplace。"""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageChops
from check_goal178_ship import check, sha, ORIGINALS, png_for

PINNED = {
    'source-query.log.matches.json': '84a15f536aa3c5469b008df7f1f915982b8811ff27647b8ebe08d972159821fd',
    'source-query.log.copies.json': '6318ce01584806a6f9b51be19772b8b7e5a8dac3dda9cedc4ccae3b1235b52fd',
}
VIEW_LAYOUT_SHA = '85a6a64e27cf36330fd79ec64bfd81046ac3c263531083fcb40ad89b3f47044c'


def menu_sources(game, p, selection):
    """核對指定MENU列的查詢、載入與實際印字；每路徑自行綁定輸入及終點。"""
    assert sha(game/'MENU.TXT')==ORIGINALS['MENU.TXT'], 'MENU 原版指紋不符'
    obs=json.loads((p/'source-query.log.matches.json').read_text())
    d=json.loads((p/'source-query.log.copies.json').read_text())
    original=(game/'MENU.TXT').read_bytes();sections={};pos=0;key=''
    for line in original.splitlines(keepends=True):
        text=line.rstrip(b'\r\n')
        if text.startswith(b'@'):key=text.decode();sections[key]=[]
        elif text and not text.startswith(b';') and key:sections[key].append((pos,text))
        pos+=len(line)
    groups=[];g=[]
    for row in d['body_reads']:
        if row['destination']==149980 and g:groups.append(g);g=[]
        g.append(row)
        if row['value']==10:groups.append(g);g=[]
    assert not g
    by_section={}
    for key in selection:
        selected=[]
        for g in groups:
            if g[0]['key']!=key:continue
            values={x['destination']-149980:x['value'] for x in g}
            raw=bytes(values.get(i,63) for i in range(max(values)+1))
            if raw.strip() and not raw.startswith(b'@'):selected.append((g,raw))
        assert len(selected)==len(sections[key]),(key,len(selected),len(sections[key]))
        by_section[key]=selected
    source_ids={key:[] for key in selection};details=[]
    for key,(offsets,glyph_start,cp) in selection.items():
        query=[q for q in obs['matches'] if q['key']==key and q['file_op'] is not None and q['file_op']['Name']=='MENU.TXT']
        assert len(query)==1
        q=query[0];assert q['header']==key and q['code_bytes']=='f3a6' and q['cx']==1 and q['original_cs_ip']=='0E2D:0832' and q['return_cs']==0x9320 and q['return_ip']==0xd7
        marker=(key+'\r\n').encode();marker_off=original.index(marker)
        assert original.count(marker)==1
        assert q['file_op']['Name']==q['read_op']['Name']=='MENU.TXT' and q['file_op']['Step']==q['read_op']['Step']
        assert q['file_op']['Pos']<=marker_off<q['file_op']['Pos']+q['file_op']['Len']
        for off in offsets:
            i=next(i for i,(n,text) in enumerate(sections[key]) if n==off)
            orig=sections[key][i][1];g,read=by_section[key][i]
            assert read==orig+b'\n',(key,off,read,orig)
            lo=g[-1]['step'];hi=by_section[key][i+1][0][0]['step']
            raw=orig.strip()+b'\0'
            writes=[w for w in d['heap_writes'] if lo<=w['step']<hi and w['cs_ip'] in ('0E2D:11A1','0E2D:11A5','0E2D:11A9')]
            by_addr={w['destination']:w for w in writes}
            candidates=[]
            for start in sorted(by_addr):
                if all(start+j in by_addr and by_addr[start+j]['value']==v for j,v in enumerate(raw)):
                    candidates.append(start)
            assert len(candidates)==1,(key,off,candidates)
            start=candidates[0]
            for j,v in enumerate(raw):
                w=by_addr[start+j];delta=w['destination']-(w['es']*16+w['di']);src=w['ds']*16+w['si']+delta
                assert 0<=delta<=1 and any(x['Step']==w['step'] and x['Addr']==src and x['Value']==v for x in w['recent_reads'])
            assert (p/'source-query.log.memory').read_bytes()[start:start+len(raw)]==raw
            glyphs=[x for x in d['glyph_reads'] if glyph_start<=x['step']<=cp and start<=x['origin']['Addr']<start+len(raw)-1]
            needed={start+j for j,v in enumerate(raw[:-1]) if v not in b'~#'}
            assert needed<={x['origin']['Addr'] for x in glyphs},(key,off,needed-{x['origin']['Addr'] for x in glyphs})
            for x in glyphs:
                origin=x['origin'];assert x['value']==origin['Value']==raw[origin['Addr']-start] and origin['Step']<x['step']
                assert (origin['CS'],origin['IP']) in ((0x9cd1,0x01ac),(0x9cd1,0x01f2),(0x0e2d,0x11a1),(0x0e2d,0x11a5),(0x0e2d,0x11a9))
                assert x['cs_ip']=='0D21:00C6' and 175684<=x['source']<175820
                if origin['CS']==0x9cd1:
                    assert any(h['step']==origin['Step'] and h['source']==origin['Addr'] and h['value']==origin['Value'] and h['cs_ip']==f"{origin['CS']:04X}:{origin['IP']:04X}" for h in d['heap_reads'])
            cid=f'MENU.TXT:{key}:0x{off:08X}';source_ids[key].append(cid)
            details.append({'id':cid,'ram':start,'load_step':by_addr[start]['step'],'glyph_reads':len(glyphs),'first_glyph_step':glyphs[0]['step']})
    return source_ids, details, obs


def verify(game, root, p, ship_layout, view_layout):
    for name, expected in PINNED.items():
        assert sha(p/name)==expected, '來源收據指紋不符：'+name
    assert sha(view_layout)==VIEW_LAYOUT_SHA, 'VIEW 欄位量測指紋不符'
    proof=check(game,root,ship_layout)
    source_ids,details,obs=menu_sources(game,p,{
        '@ORDERS':((0x299,0x2a5,0x30e,0x31d),50000000,91245000),
        '@VIEW':((0x1aa,0x1bb),50000000,56265000),
    })
    assert obs['inputs_sha256']==proof['inputs_sha256'] and obs['final_step']==proof['final_step'] and obs['memory_sha256']==proof['final_memory_sha256']
    assert (p/'source-query.log.memory').read_bytes()==(root/'replay-control.memory').read_bytes()
    zh=json.loads((root/'replay-zh.json').read_text());shot_steps=dict(line.split() for line in (root/'gui-colony.shots').read_text().splitlines())
    views=[e for e in zh['events'] if e.get('stage')=='source' and len(e.get('items',[]))==12 and e['safe']==[48,12,120,141] and e['step']<56265000]
    assert views;view=views[-1];assert view['entry_ip']=='0D21:00C6' and view['source_linear']==175684 and view['font_px']==21
    cp=next(x for x in zh['checkpoints'] if x['step']==56265000)
    assert any(x['candidate_id']==view['candidate_id'] and x.get('applied') for x in cp['lines'])
    assert any(e.get('stage')=='active' and e.get('candidate_id')==view['candidate_id'] and view['step']<=e['step']<=56265000 for e in zh['events'])
    raw=(root/'replay-control.cp-56265000.idx').read_bytes();assert len(raw)==64000
    ys=[]
    for y in range(13,141):
        if sum(raw[y*320+x] in (68,149,8) for x in range(49,119))>=2:ys.append(y)
    bands=[]
    for y in ys:
        if not bands or y>bands[-1][-1]+1:bands.append([y])
        else:bands[-1].append(y)
    bands=[b for b in bands if len(b)>=5]
    assert len(bands)==12,(bands,ys)
    en=Image.open(root/'replay-control.cp-56265000.png').convert('RGB');zhim=Image.open(png_for(root,'replay-zh',cp)).convert('RGB')
    geometry=[]
    for band in bands:
        rect=(192,band[0]*4,480,(band[-1]+1)*4)
        assert ImageChops.difference(en.crop(rect),zhim.crop(rect)).getbbox(),band
        ink=[(x,y) for y in band for x in range(49,54) if raw[y*320+x] in (68,149,8)]
        assert ink
        geometry.append({'row_top':band[0],'row_bottom':band[-1]+1,'first_cap_height':max(y for x,y in ink)-min(y for x,y in ink)+1})
    proof['verified_fields'][0]['source_ids']=source_ids['@ORDERS']
    proof['verified_fields'].append({'candidate_id':view['candidate_id'],'shown':view['shown'],'safe':view['safe'],'source_ids':source_ids['@VIEW']})
    proof.update(source_details=details,view_geometry=geometry,grade='confirmed')

    layout=json.loads(view_layout.read_text())
    assert layout['selected_px']==view['font_px']==21
    assert [x['Text'] for x in layout['original_lines']]==view['items']
    assert layout['output_safe_width']==288 and layout['output_safe_height']==516
    assert layout['candidate21_ink_height']==19 and layout['candidate22_ink_height']==21
    assert layout['longest_advance']==max(layout['advance_widths'])==187
    assert layout['longest_advance']+8<=layout['output_safe_width']
    assert layout['safe']=={'Min':{'X':48,'Y':12},'Max':{'X':120,'Y':141}}
    ink=layout['mask_ink'];assert 0<=ink['Min']['X']<ink['Max']['X']<=288 and 0<=ink['Min']['Y']<ink['Max']['Y']<=516
    assert all(g['first_cap_height']==line['cap_h']==5 and g['row_top']==line['Box']['Min']['Y'] and g['row_bottom']==line['Box']['Max']['Y'] for g,line in zip(geometry,layout['original_lines']))
    assert sha(p/'scratch/COLONY03.SAV')=='d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77'
    assert sha(p/'inputs.json')==proof['inputs_sha256']
    proof.update(scope='只驗此正常船隻／VIEW欄位與六個原始MENU來源；其他同文與局勢仍待驗', evidence_sha256={n:sha(p/n) for n in PINNED}, view_layout_sha256=sha(view_layout))
    return proof


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('game','reports','provenance','ship-layout','view-layout'):
        parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args()
    if any(not (args.game/name).is_file() for name in ORIGINALS):
        print('SKIP：缺合法原版輸入')
        return 77
    try:
        proof=verify(args.game,args.reports,args.provenance,args.ship_layout,args.view_layout)
    except (AssertionError,OSError,KeyError,ValueError,TypeError,StopIteration) as error:
        print('FAIL：'+str(error))
        return 1
    print(json.dumps(proof,ensure_ascii=False))
    return 0


if __name__=='__main__':
    raise SystemExit(main())
