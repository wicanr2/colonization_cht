"""規格062 R47 DRAFT：獨立重建地形逐寫、游標及RAM來源鏈，只授予研究信用。"""
import argparse,base64,json,os,struct
from collections import Counter
from pathlib import Path
from check_hd_building_nine_lifecycle import need,read,sha,sha_file,event_stream

ORDINALS={6,9,17,66,71,74,77,78,79,80,96,147,150}
CATALOG='4a89951c8a884eb5147d15c7b2a2fd1021f6079183ae5a10a493237c417c2b0e'
ENTRY='c828000052535057568b4702'
COPY='f3a503f3790c81ee00808cd981c10008'
WRITERS={'0D46:0181':'268807035ef042fecc7402ebe7ebd03b',
 '0D46:01B4':'268807035ef042fecc7403ebe790ebcc',
 '0D46:01D2':'268807035ef042ebb5905a5b035efe79'}
BASES=[0x2cae0,0x3c500]

def check(observed,control,sources,out):
 need(sha_file(sources/'source-catalog.json')==CATALOG,'固定來源清冊不同')
 rows={r['ordinal']:r for r in read(sources/'source-catalog.json')['sources'] if r['file']=='PHYS0.SS' and r['ordinal'] in ORDINALS}
 need(set(rows)==ORDINALS,'來源列缺漏')
 pixels={n:(sources/f'building-{n:03d}.pixels').read_bytes() for n in ORDINALS}
 for n,r in rows.items():need(len(pixels[n])==256 and sha(pixels[n])==r['indexed_sha256'],'完整索引來源不同')
 proof=read(observed/'draws.json');plain=read(control/'draws.json');calls=proof['calls']
 entries=sources/'lifecycle-r1/observed/draws.json'
 need(sha_file(entries)=='3d9d7b70a3f6046c0d54ce32aa94189b367cd7f031ea4b8f7c7163bd52bc094f','固定原版入口收據不同')
 known=read(entries)['calls']
 need(proof['control'] is False and plain['control'] is True and proof['end']==plain['end'],'觀測／控制終點不同')
 for key in ['input_sha256','seed_sha256','dos_inputs']:need(proof[key]==plain[key],'兩側輸入或種子不同')
 need(set(c['ordinal'] for c in calls)==ORDINALS and len(proof['checkpoints'])==len(plain['checkpoints'])==49,'來源或檢查點缺漏')
 for c in calls:
  r=rows[c['ordinal']];raw=pixels[c['ordinal']];w,h=r['size'];x,y,right,bottom=c['rect']
  need(c['selected'] and not c.get('geometry_or_write_mismatch'),'來源繪製未完整接受')
  need(c['entry_code12']==ENTRY and c['source_encoded_sha256']==r['encoded_sha256'],'入口或完整來源不同')
  need(any(all(e[k]==c[k] for k in ['record_far','record_words','source_far','source_encoded_sha256']) and e['registers'][0]==c['registers'][0] for e in known),'來源遠指標或原始紀錄不同')
  need(c['registers'][0]==c['ordinal']+1 and c['registers'][2]==x and c['ss_sp_words'][2]==y,'入口參數不同')
  need(c['canvas_linear'] in BASES and c['ds_bx_words']==[200,320,0,c['canvas_linear']//16] and c['record_words'][4:]==[w,h],'畫布或紀錄不同')
  need(0<=x<right<=320 and 0<=y<bottom<=200 and (right-x,bottom-y)==(w,h),'未驗裁切或座標')
  need(c['return_segments'][1]==c['ss_sp_words'][1] and c['return_ip']==c['ss_sp_words'][0] and c['return_registers'][4]==(c['registers'][4]+10)&65535 and 0<c['return_step']-c['entry_step']<=100000,'返回不同')
  need(c['writer_code16'] and all(WRITERS.get(k)==v for k,v in c['writer_code16'].items()),'未知寫入碼')
  opaque={k:v for k,v in enumerate(raw) if v!=253};data=b''.join(struct.pack('<HB',k,v) for k,v in opaque.items())
  need(c['unique_writes']==c['write_count']==sum(c['writer_sites'].values())==len(opaque)==r['opaque'] and c['sorted_local_offset_value_sha256']==sha(data),'完整逐寫不同')
  before,after=[base64.b64decode(c[k],validate=True) for k in ['private_before_roi','private_after_roi']]
  need(len(before)==len(after)==256 and c['transparent_background_unchanged'] and c['outside_rectangle_unchanged'] and all(after[k]==(before[k] if v==253 else v) for k,v in enumerate(raw)),'透明底圖或矩形外不同')
 owner={};native={};pending={};cursor=None;restores=[];at=next_call=drawn=last_step=transfers=0;ram_saves=ram_restores=0;ram_copies=[];by_transfer=Counter();summaries=[]
 count=proof['raw_event_count'];need(type(count) is int and 0<=count<=8000000,'事件總數不同')
 events=iter(event_stream(observed/'writes.json'))
 points=proof['checkpoints']+[dict(proof['end'],event_count=count,snapshot_prefix=None)]
 for index,point in enumerate(points):
  final=point['snapshot_prefix'] is None
  if not final:
   baseline=plain['checkpoints'][index]
   for key in ['steps','memory_sha256','indexed_sha256','palette_sha256','registers','segments','ip','flags','cycles','dos_input_count']:need(point[key]==baseline[key],'控制檢查點不同：'+key)
  need(at<=point['event_count']<=count,'事件序號不同')
  while at<point['event_count']:
   e=next(events);need(last_step<=e['step']<=point['steps'],'事件步數不同');last_step=e['step']
   while next_call<len(calls) and calls[next_call]['entry_step']<=e['step']:
    c=calls[next_call];surface=BASES.index(c['canvas_linear']);x,y,_,_=c['rect'];before=base64.b64decode(c['private_before_roi'],validate=True)
    for k,v in enumerate(before):
     key=(surface,(y+k//16)*320+x+k%16);need(key not in native or native[key]==v,'來源前底圖不能重建');native[key]=v
    next_call+=1
   if e['kind']=='cursor-init':
    need(cursor is None and e['step']==49999999 and e['linear']==0x1cd74,'游標初始來源不同')
    cursor=bytearray(base64.b64decode(e['bytes'],validate=True));need(len(cursor)==256,'游標初始長度不同')
   elif e['kind']=='cursor-write':
    k=e['linear']-0x1cd74
    need(cursor is not None and 0<=k<256 and cursor[k]==e['old'] and len(bytes.fromhex(e['code16']))==16,'游標來源逐寫不同')
    cursor[k]=e['value']
   elif e['kind']=='draw':
    drawn+=1;need(e['call']==drawn and calls[drawn-1]['return_step']==e['step'],'完整來源建立順序不同')
    c=calls[drawn-1];n=c['ordinal'];surface=BASES.index(c['canvas_linear']);x,y,_,_=c['rect'];after=base64.b64decode(c['private_after_roi'],validate=True)
    need(all(native[(surface,(y+k//16)*320+x+k%16)]==v for k,v in enumerate(after)),'返回底圖不能重建')
    for k,v in enumerate(pixels[n]):
     if v!=253:owner[(surface,(y+k//16)*320+x+k%16)]={'ordinal':n,'call':drawn,'local':k,'native':v}
   elif e['kind']=='ram-write':
    addr=e['linear'];need(type(addr) is int and 0<=addr<0xa0000 and all(not base<=addr<base+64000 for base in BASES),'RAM事件越界')
    key=(2,addr);need(key not in native or native[key]==e['old'],'RAM原始舊值不同')
    owner.pop(key,None);cell=None
    r,g=e['registers'],e['segments'];delta=addr-(g[0]*16+r[7]);src=g[3]*16+r[6]+delta
    if e['site']=='0CBA:00CA' and e['code16']==COPY and 0<=delta<2 and r[6]+delta<65536 and r[7]+delta<65536 and BASES[0]<=src<BASES[0]+64000:
     source_key=(0,src-BASES[0]);cell=owner.get(source_key)
     if cell:
      need(native[source_key]==cell['native']==e['value'],'RAM保存來源已過期');ram_saves+=1
      if cell['ordinal']==79:ram_copies.append({'kind':'save','event_index':at,'source':src,'destination':addr,'cell':cell.copy(),'event':e.copy()})
    native[key]=e['value']
    if cell:owner[key]=cell.copy()
   elif e['kind']=='write':
    surface,pos=e['surface'],e['offset'];need(type(surface) is int and surface in [0,1] and type(pos) is int and 0<=pos<64000,'寫入越界')
    key=(surface,pos);need(key not in native or native[key]==e['old'],'原始舊值不同')
    r,g=e['registers'],e['segments'];delta=BASES[surface]+pos-(g[0]*16+r[7]);src=g[3]*16+r[6]+delta
    source_key=next(((s,src-base) for s,base in enumerate(BASES) if base<=src<base+64000),(2,src))
    tracked_copy=surface==0 and e['site']=='0CBA:00CA' and 0<=delta<2 and source_key in native
    cell=None
    if surface==0 and e['site']=='0CBA:00CA' and e['code16']==COPY and 0<=delta<2 and r[6]+delta<65536 and r[7]+delta<65536 and BASES[1]<=src<BASES[1]+64000:
     source_key=(1,src-BASES[1]);cell=owner.get(source_key)
     need(source_key not in native or native[source_key]==e['value'],'複製來源值不同')
     if cell:
      need(cell['native']==e['value'],'複製來源身分已過期');transfers+=1;by_transfer[cell['ordinal']]+=1
    if surface==0 and e['site']=='0CBA:00CA' and e['code16']==COPY and 0<=delta<2 and r[6]+delta<65536 and r[7]+delta<65536 and 0<=src<0xa0000 and all(not base<=src<base+64000 for base in BASES):
     source_key=(2,src);cell=owner.get(source_key)
     if cell:
      need(native[source_key]==cell['native']==e['value'],'RAM還原來源已過期');ram_restores+=1
      if cell['ordinal']==79:ram_copies.append({'kind':'restore','event_index':at,'source':src,'destination':BASES[0]+pos,'cell':cell.copy(),'event':e.copy()})
    if surface==0:
     known_cursor=cursor is not None and sha(bytes(cursor))=='47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03' and e['site']=='0B68:051C' and e['code16']=='f3a48ac82bf92bf103f303fafecc75f0' and g[3]==0xa000 and g[0]==0x2cae and 0xafa00<=src<0xafc00
     if known_cursor:
      k=src&255
      if src>=0xafb00:pending[key]=(owner.get(key),e['old'],e['value'],k)
      else:
       prior=pending.pop(key,None)
       if prior and prior[0] and prior[1]==e['value'] and prior[2]==e['old'] and prior[3]==k:
        cell=prior[0];restores.append({'step':e['step'],'surface':surface,'offset':pos,'cell':cell.copy(),'cursor':k,'event':e})
     else:pending.clear()
    owner.pop(key,None)
    # 全畫面游標事件亦有記錄；未追蹤區域的其他後畫沒有收集，不能據此重建底圖。
    if key in native or tracked_copy:native[key]=e['value']
    if cell:owner[key]=cell.copy()
   else:raise ValueError('未知事件種類')
   at+=1
  if not final:
   prefix=point['snapshot_prefix']
   if cursor is not None:need(bytes(cursor)==(observed/(prefix+'.cursor')).read_bytes(),'游標來源不能重建')
   surfaces=[(observed/(prefix+suffix)).read_bytes() for suffix in ['.canvas','.stage']]
   for surface,data in enumerate(surfaces):
    need(len(data)==64000,'畫布長度不同')
    need(all(data[pos]==v for (s,pos),v in native.items() if s==surface),'原版畫布不能重建')
    need(all(data[pos]==cell['native'] for (s,pos),cell in owner.items() if s==surface),'來源身分已過期')
   memory=(observed/(prefix+'.memory')).read_bytes()
   need(sha(memory)==point['memory_sha256'],'RAM快照指紋不同')
   need(all(memory[pos]==v for (surface,pos),v in native.items() if surface==2),'RAM逐寫不能重建')
   need(all(memory[pos]==cell['native'] for (surface,pos),cell in owner.items() if surface==2),'RAM身分已過期')
   main={pos:cell for (surface,pos),cell in owner.items() if surface==0};name=f'point-{index:03d}.terrain-model.json'
   (out/name).write_text(json.dumps(main,sort_keys=True)+'\n')
   summaries.append({'point':index,'step':point['steps'],'main_owned':len(main),'main_by_ordinal':dict(Counter(c['ordinal'] for c in main.values())),'main_owners_file':name,'main_owners_sha256':sha_file(out/name)})
 need(at==count and next(events,None) is None and next_call==drawn==len(calls),'仍有未驗事件')
 for name in ['COLONY00.SAV','COLONY09.SAV']:need((observed/'saves'/name).read_bytes()==(control/'saves'/name).read_bytes(),'存檔不同')
 need((observed/'final.memory').read_bytes()==(control/'final.memory').read_bytes(),'完整終點RAM不同')
 (out/'terrain079-ram-copies.json').write_text(json.dumps(ram_copies)+'\n')
 (out/'cursor-pairs.json').write_text(json.dumps(restores)+'\n')
 return {'verified_cursor_restores':len(restores),'cursor_restores_by_ordinal':dict(Counter(r['cell']['ordinal'] for r in restores)),'result':'PASS_TERRAIN_RAM_RESEARCH_NATIVE_MODEL','source_calls':len(calls),'raw_events':count,'verified_stage_main_transfers':transfers,'transfers_by_ordinal':dict(by_transfer),'points':summaries,'production_connected':False,'ram_restorations_accepted':ram_restores,'ram_saves_verified':ram_saves,'cursor_restorations_accepted':len(restores),'limitations':['限固定原版及53筆正常輸入；未安裝HD。','未知後畫含同值撤銷；RAM只接受逐寫證實的主畫布保存與原位元組還原；只驗已知游標來源及實際反向舊新值配對。','TERRAIN.SS及8×8別名未建立來源契約。']}

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['observed','control','sources','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve()
 need(Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists(),'需新的非root本機輸出')
 out.mkdir();result=check(a.observed,a.control,a.sources,out);result['checker_sha256']=sha_file(Path(__file__));result['receipts_sha256']={str(f):sha_file(f) for f in [a.observed/'draws.json',a.observed/'writes.json',a.control/'draws.json',a.sources/'source-catalog.json']}
 (out/'check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result['result'],result['source_calls'],result['verified_stage_main_transfers'],flush=True)
if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,TypeError,OSError,StopIteration,json.JSONDecodeError) as e:raise SystemExit('地形來源驗證拒絕：'+str(e))
