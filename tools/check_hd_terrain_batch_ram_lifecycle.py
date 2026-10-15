"""規格067 DRAFT：從R61真實GUI的原版收據重建十三來源，逐種列出還原信用。"""
import argparse,json,os
from collections import Counter
from pathlib import Path
import check_hd_terrain_ram_lifecycle as model

TARGETS=model.ORDINALS-{79}
FINGERPRINTS={
 'gui-oracle-r1/observed/draws.json':'cd72855e8b4c840e40a4d02da15657fa624893c5878da968f492282d2e100784',
 'gui-oracle-r1/observed/writes.json':'4427836964187acaf4d4ef93c7a64975cc4d04fadffbb28e52d48cb8ad8b384f',
 'gui-oracle-r1/control/draws.json':'827a704cdae605f3de75dda96d611fca902af3010a539d3defa0d687418ecd6d',
}

def check(reference,sources,game,out):
 for name,digest in FINGERPRINTS.items():
  model.need(model.sha_file(reference/name)==digest,'固定R61收據不同：'+name)
 for name,digest in {
  'VICEROY.EXE':'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3',
  'PHYS0.SS':'deac746ad65292ebadd83b8ace7d2cea298741111dcdda13e184049516f1ef16',
 }.items():model.need(model.sha_file(game/name)==digest,'原版輸入不同：'+name)
 fixture=model.read(reference/'gui-oracle-fixture.json');points=model.read(reference/'gui-oracle-points.json')
 model.need(fixture['point_count']==len(points)==29 and fixture['dos_inputs']==109 and fixture['end']==218130001,'GUI前綴不同')
 model.need(fixture['prefix_sha256']=='63b8cc52610760adf4a63e4d8351a262d6c4007db45e3939f24ce94de1f20cfb' and fixture['points_sha256']==model.sha_file(reference/'gui-oracle-points.json'),'GUI輸入或檢查點不同')
 observed,control=reference/'gui-oracle-r1/observed',reference/'gui-oracle-r1/control'
 native=out/'model';native.mkdir()
 result=model.check(observed,control,sources,native,expected_points=29,all_ram=True)
 model.need(result['source_calls']==101 and result['raw_events']==194628 and result['verified_stage_main_transfers']==12823,'原版事件數不同')
 copies=model.read(native/'terrain-batch-ram-copies.json');pairs=model.read(native/'cursor-pairs.json')
 saves=Counter(r['cell']['ordinal'] for r in copies if r['kind']=='save')
 restores=Counter(r['cell']['ordinal'] for r in copies if r['kind']=='restore')
 model.need(sum(saves.values())==result['ram_saves_verified']==5886 and sum(restores.values())==result['ram_restorations_accepted']==4370,'逐種RAM計數不同')
 proof=model.read(observed/'draws.json');calls=proof['calls'];catalog=model.read(sources/'source-catalog.json')
 rows={r['ordinal']:r for r in catalog['sources'] if r['file']=='PHYS0.SS' and r['ordinal'] in model.ORDINALS}
 summaries={};visible=Counter();visible_points=Counter()
 for i,point in enumerate(result['points']):
  name=f'point-{i:03d}.terrain-model.json'
  model.need((native/name).read_bytes()==(reference/'gui-model-r1'/name).read_bytes(),'新舊逐寫模型不同：'+name)
  owners=model.read(native/name);idx=(observed/f'point-{i:03d}.idx').read_bytes();canvas=(observed/f'point-{i:03d}.canvas').read_bytes()
  model.need(len(idx)==len(canvas)==64000 and model.sha(idx)==points[i]['indexed_sha256'],'原版畫面指紋不同')
  counts=Counter()
  for position,cell in owners.items():
   pos=int(position)
   # 可見信用只授予原版畫布與VGA均吻合的像素。遮擋不猜補。
   if canvas[pos]==idx[pos]==cell['native']:counts[cell['ordinal']]+=1
  visible.update(counts);visible_points.update(counts.keys());point['vga_visible_by_ordinal']=dict(counts)
 for ordinal in sorted(model.ORDINALS):
  r=rows[ordinal];entries=[c for c in calls if c['ordinal']==ordinal]
  identity={(c['record_far'],c['source_far'],tuple(c['record_words'])) for c in entries}
  model.need(len(identity)==1,'同一來源的定位不唯一');record,source,words=next(iter(identity))
  writes={c['sorted_local_offset_value_sha256'] for c in entries};model.need(len(writes)==1,'逐寫來源不一致')
  summaries[ordinal]={
   'ordinal':ordinal,'new_target':ordinal in TARGETS,'size':r['size'],'opaque_cells':r['opaque'],
   'encoded_sha256':r['encoded_sha256'],'indexed_sha256':r['indexed_sha256'],
   'encoded_length':r['length'],'decoded_part3_offset':r['decoded_part3_offset'],
   'record_far':record,'source_far':source,'record_words':list(words),
   'sorted_local_offset_value_sha256':next(iter(writes)),'draw_calls':len(entries),
   'stage_main_transfers':result['transfers_by_ordinal'].get(ordinal,0),
   'ram_saves':saves[ordinal],'ram_restores':restores[ordinal],
   'cursor_restores':sum(p['cell']['ordinal']==ordinal for p in pairs),
   'vga_visible_pixels':visible[ordinal],'vga_visible_points':visible_points[ordinal],
  }
 model.need(all(summaries[n]['draw_calls'] and summaries[n]['stage_main_transfers'] and summaries[n]['vga_visible_pixels'] for n in TARGETS),'新來源沒有正常可見證據')
 report={
  'result':'PASS_TERRAIN_BATCH_NATIVE_SOURCE_RAM_AND_29_GUI_POINTS','new_targets':sorted(TARGETS),
  'sources':summaries,'points':result['points'],'source_calls':result['source_calls'],'raw_events':result['raw_events'],
  'stage_main_transfers':result['verified_stage_main_transfers'],'ram_saves':sum(saves.values()),
  'ram_restores':sum(restores.values()),'cursor_restores':len(pairs),'original_state_and_saves_equal':True,
  'source_catalog_sha256':model.sha_file(sources/'source-catalog.json'),
  'oracle_build':model.read(reference/'gui-oracle-r1/build.json'),
  'checker_sha256':model.sha_file(Path(__file__)),'model_checker_sha256':model.sha_file(Path(model.__file__)),
  'input_sha256':proof['input_sha256'],'dos_inputs':proof['dos_inputs'],'end':fixture['end'],
  'receipts_sha256':{n:model.sha_file(reference/n) for n in FINGERPRINTS},'production_connected':False,'ready':False,
  'limitations':['沿R61實際GUI輸入的29點原版前綴，沒有重跑或製造新遊玩路徑。',
   '逐來源列出正向RAM及游標信用，零例不外推；未知同值後畫撤銷。',
   '只驗來源與顯示鏈，尚無新素材、正式接線、HD像素或動畫驗收。'],
 }
 (out/'check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');return report

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['reference','sources','game','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve()
 model.need(Path('/.dockerenv').is_file() and os.getuid()!=0 and out.is_relative_to('/out') and out.parent.stat().st_uid==os.getuid() and not out.exists(),'需新的非root本機輸出')
 out.mkdir();report=check(a.reference,a.sources,a.game,out)
 print(report['result'],len(report['new_targets']),report['source_calls'],flush=True)

if __name__=='__main__':
 try:main()
 except (ValueError,KeyError,TypeError,OSError,StopIteration,json.JSONDecodeError) as e:raise SystemExit('地形批次來源驗證拒絕：'+str(e))
