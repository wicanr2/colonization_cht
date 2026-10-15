"""規格067 DRAFT：十二個真實來源各做單項錯件，最後重驗正向模型。"""
import argparse,copy,json,os
from pathlib import Path
import check_hd_terrain_batch_ram_lifecycle as batch

model=batch.model

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['reference','sources','game','baseline','output']:p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();root=a.output.resolve()
 model.need(Path('/.dockerenv').is_file() and os.getuid()!=0 and root.is_relative_to('/out') and root.parent.stat().st_uid==os.getuid() and not root.exists(),'需新的非root本機輸出')
 root.mkdir();observed=a.reference/'gui-oracle-r1/observed/draws.json';read0=model.read
 cases=[]
 for ordinal in sorted(batch.TARGETS):
  for kind in ['encoded-source','writer-code','ax-ordinal']:
   def read(path):
    value=read0(path)
    if path!=observed:return value
    value=copy.deepcopy(value);call=next(c for c in value['calls'] if c['ordinal']==ordinal)
    if kind=='encoded-source':call['source_encoded_sha256']='0'*64
    elif kind=='writer-code':call['writer_code16'][next(iter(call['writer_code16']))]='00'*16
    else:call['registers'][0]+=1
    return value
   dest=root/f'{ordinal:03d}-{kind}';dest.mkdir();model.read=read
   try:
    batch.check(a.reference,a.sources,a.game,dest)
   except ValueError as error:
    cases.append({'ordinal':ordinal,'case':kind,'result':'PASS_INVALID_EVIDENCE_REJECTED','reason':str(error)})
   else:raise AssertionError('錯誤來源未拒絕：'+dest.name)
   finally:model.read=read0
  print('PASS_TERRAIN_BATCH_SOURCE_NEGATIVES',ordinal,3,flush=True)
 positive=root/'positive-after-negatives';positive.mkdir()
 report=batch.check(a.reference,a.sources,a.game,positive);baseline=model.read(a.baseline/'check.json')
 model.need(model.read(positive/'check.json')['sources']==baseline['sources'],'反例後逐來源結果不同')
 for i in range(29):
  name=f'point-{i:03d}.terrain-model.json'
  model.need((positive/'model'/name).read_bytes()==(a.baseline/'model'/name).read_bytes(),'反例後29點模型不同')
 result={'result':'PASS_TERRAIN_BATCH_36_SOURCE_NEGATIVES_AND_POSITIVE_RECHECK',
  'cases':cases,'positive_after_negatives':True,'all_29_positive_models_equal':True,
  'checker_sha256':model.sha_file(Path(batch.__file__)),
  'model_checker_sha256':model.sha_file(Path(model.__file__)),
  'test_sha256':model.sha_file(Path(__file__)),'production_connected':False}
 (root/'check.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print(result['result'],flush=True)

if __name__=='__main__':main()
