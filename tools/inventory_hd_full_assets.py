"""R49 DRAFT：全SS與PIK的唯讀形狀、指紋與別名清冊，不授予HD完成信用。"""
import argparse,collections,contextlib,hashlib,io,json,os,platform,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,__version__ as pillow_version

parser=argparse.ArgumentParser(description=__doc__)
for name in ['game','decoder','baseline','output']:parser.add_argument('--'+name,type=Path,required=True)
a=parser.parse_args();out=a.output.resolve()
assert Path('/.dockerenv').is_file() and os.getuid()!=0
assert out.is_relative_to('/out') and out.parent.is_dir() and out.parent.stat().st_uid==os.getuid() and not out.exists()
sha=lambda b:hashlib.sha256(b).hexdigest()
for name,want in {'VICEROY.EXE':'a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3','OPENING.EXE':'3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39'}.items():
 p=a.game/name
 if not p.is_file():print('SKIP: missing legal original '+name);raise SystemExit(77)
 assert sha(p.read_bytes())==want
manifest_bytes=(a.decoder/'source-manifest.json').read_bytes()
assert sha(manifest_bytes)=='340f980355615cbe88659b72748296657982b4802ade1d41eebcc21d84af6e18'
manifest=json.loads(manifest_bytes);assert manifest['commit']=='8c30544b51d1b4ab68f3a465784239c24b660e24'
for name,want in manifest['files_sha256'].items():assert sha((a.decoder/name).read_bytes())==want
baseline=json.loads(a.baseline.read_bytes());assert baseline['source_count']==206 and baseline['frame_count']==1517 and not baseline['failed_files']
baseline={r['file']:r for r in baseline['files']}
sys.path.insert(0,str(a.decoder))
import ss,pik
from madspack import read_madspack
from palette import read_palette_col,read_palette_rex
out.mkdir();(out/'pixels').mkdir();(out/'previews').mkdir()
frames=[];files=[];errors=[];previews=collections.defaultdict(list);source_id=0
font=ImageFont.truetype('DejaVuSans.ttf',12)
def palette_png(im,palette,path,transparent):
 image=im.copy();flat=[x for rgb in palette for x in rgb];assert len(flat)<=768
 image.putpalette(flat+[0]*(768-len(flat)))
 if transparent is not None:image.info['transparency']=transparent
 image.save(path)
 return image.convert('RGBA')
for file in sorted(p for p in a.game.iterdir() if p.is_file()):
 blob=file.read_bytes();record={'file':file.name,'sha256':sha(blob),'size_bytes':len(blob),'format':'unclassified','frames':[]}
 files.append(record)
 if file.suffix.upper() not in ['.SS','.PIK']:continue
 try:
  with contextlib.redirect_stdout(io.StringIO()):parts=read_madspack(str(file))
  record['part_sizes']=[len(p.getbuffer()) for p in parts]
  record['part_sha256']=[sha(p.getbuffer()) for p in parts]
  if file.suffix.upper()=='.SS':
   assert file.name in baseline and record['sha256']==baseline[file.name]['sha256'] and len(parts)==4
   header=ss.read_ss_header(parts[0]);assert header.mode in [0,1]
   palette=(read_palette_col if header.pflag else read_palette_rex)(parts[2])
   record.update(format='SS',mode=header.mode,palette_flag=header.pflag,frame_count=header.nsprites)
   assert header.nsprites==baseline[file.name]['frame_count'] and header.nsprites*16<=len(parts[1].getbuffer())
   data=bytes(parts[3].getbuffer())
   for ordinal in range(header.nsprites):
    source_id+=1;parts[1].seek(ordinal*16);h=ss.read_sprite_header(parts[1])
    old=baseline[file.name]['frames'][ordinal]
    frame={'research_id':source_id,'file':file.name,'file_sha256':record['sha256'],'ordinal':ordinal,'size':[h.width,h.height],'header_part1_offset':ordinal*16,'data_part3_offset':h.start_offset,'encoded_length':h.length,'other_header_fields':[h.width_padded,h.height_padded],'runtime_identity':'not_assessed_by_inventory','animation':'not_assessed_by_inventory','production_hd':'not_assessed_by_inventory'}
    record['frames'].append(source_id);frames.append(frame)
    assert frame['size']==old['size'] and h.length==old['encoded_length_field'] and h.start_offset==old['data_offset_in_part3']
    if not h.width or not h.height:
     frame['decode_status']='zero-dimension';continue
    assert 0<h.width<=4096 and 0<h.height<=4096 and 0<=h.start_offset<len(data) and 0<=h.length<=len(data)-h.start_offset
    im=ss.read_sprite(h,parts[3],palette,mode=header.mode);pixels=im.tobytes()
    assert im.mode=='P' and im.size==(h.width,h.height) and sha(pixels)==old['decoded_indexed_sha256']
    encoded=data[h.start_offset:h.start_offset+h.length]
    frame.update(decode_status='decoded',encoded_sha256=sha(encoded),indexed_sha256=sha(pixels),opaque_pixels=sum(v!=253 for v in pixels),transparency_index=253)
    assert frame['opaque_pixels']==old['opaque_pixels']
    (out/'pixels'/f'{source_id:04d}.idx').write_bytes(pixels)
    if file.name in ['ICONS.SS','CURSOR.SS']:
     preview=palette_png(im,palette,out/'previews'/f'{file.name}-{ordinal:03d}.png',253)
     previews[file.name].append((f'{ordinal:03d} {h.width}x{h.height}',preview))
  else:
   assert len(parts)>=2
   header=bytes(parts[0].getbuffer());assert len(header)>=8
   h=pik.read_pik_header(parts[0]);assert 0<h.width<=4096 and 0<h.height<=4096 and h.width*h.height<=len(parts[1].getbuffer())
   palette=read_palette_col(parts[2]) if len(parts)>=3 else None
   pixels=bytes(parts[1].getbuffer())[:h.width*h.height]
   im=Image.frombytes('P',(h.width,h.height),pixels)
   assert im.mode=='P' and im.size==(h.width,h.height) and len(pixels)==h.width*h.height
   source_id+=1;record.update(format='PIK',frame_count=1,embedded_palette=palette is not None);record['frames'].append(source_id)
   frame={'research_id':source_id,'file':file.name,'file_sha256':record['sha256'],'ordinal':0,'size':[h.width,h.height],'header_part0_hex':header.hex(),'other_header_fields':[h.unk1,h.unk2],'pixel_part1_offset':0,'pixel_bytes':len(pixels),'part1_trailing_bytes':len(parts[1].getbuffer())-len(pixels),'indexed_sha256':sha(pixels),'decode_status':'decoded','transparency_index':None,'runtime_transparency':'unknown','embedded_palette':palette is not None,'runtime_palette':'unknown','runtime_identity':'not_assessed_by_inventory','animation':'not_assessed_by_inventory','production_hd':'not_assessed_by_inventory'}
   frames.append(frame);(out/'pixels'/f'{source_id:04d}.idx').write_bytes(pixels)
   if palette is not None:
    preview=palette_png(im,palette,out/'previews'/f'{file.name}.png',None)
    previews['PIK'].append((f'{file.name} {h.width}x{h.height}',preview))
 except Exception as error:
  record['error']=f'{type(error).__name__}: {error}';errors.append(file.name)
aliases=collections.defaultdict(list)
for f in frames:
 if f.get('decode_status')=='decoded' and 'encoded_sha256' in f:
  aliases[(tuple(f['size']),f['encoded_length'],f['encoded_sha256'])].append(f['research_id'])
alias_groups=[ids for ids in aliases.values() if len(ids)>1]
for name,images in previews.items():
 cols=8 if name!='PIK' else 5;cw,ch=(128,112) if name!='PIK' else (256,192)
 sheet=Image.new('RGB',(cols*cw,((len(images)+cols-1)//cols)*ch),'#eee7d4');draw=ImageDraw.Draw(sheet)
 for index,(label,im) in enumerate(images):
  x,y=index%cols*cw,index//cols*ch;draw.text((x+4,y+3),label,font=font,fill='#302a20')
  scale=min(4,(cw-8)/im.width,(ch-28)/im.height);im=im.resize((max(1,int(im.width*scale)),max(1,int(im.height*scale))),Image.Resampling.NEAREST)
  sheet.paste(im,(x+(cw-im.width)//2,y+24),im)
 sheet.save(out/f'{name.lower()}-archive-palette-sheet.png')
summary={'file_count':len(files),'ss_files':sum(r['format']=='SS' for r in files),'pik_files':sum(r['format']=='PIK' for r in files),'ss_frame_records':sum(len(r['frames']) for r in files if r['format']=='SS'),'pik_images':sum(len(r['frames']) for r in files if r['format']=='PIK'),'decoded_frames':sum(f.get('decode_status')=='decoded' for f in frames),'zero_dimension_frames':sum(f.get('decode_status')=='zero-dimension' for f in frames),'decoded_zero_opaque_ss_frames':sum(f.get('decode_status')=='decoded' and f.get('opaque_pixels')==0 for f in frames),'declared_encoding_alias_groups':len(alias_groups),'unclassified_other_files':sum(r['format']=='unclassified' for r in files),'failed_files':errors}
catalog={'kind':'DRAFT-full-SS-PIK-inventory-other-files-unclassified','tools':{'python':platform.python_version(),'pillow':pillow_version,'script_sha256':sha(Path(__file__).read_bytes()),'decoder_commit':manifest['commit'],'decoder_manifest_sha256':sha(manifest_bytes),'baseline_ss_inventory_sha256':sha(a.baseline.read_bytes())},'address_spaces':{'headers':'decoded MADSPACK part offsets','pixels':'decoded indexed bytes; not EXE, IDA or runtime RAM'},'summary':summary,'files':files,'frames':frames,'declared_encoding_alias_groups':alias_groups,'limitations':['Decoded source metadata only; no runtime source, animation or HD credit.','Archive palette sheets are previews, not verified runtime DAC references.','Zero-size, zero-opaque and encoding aliases are preserved without a player-visibility conclusion.','Other file formats remain unclassified; complete player-visible graphics denominator is unknown.','Original pixels and previews stay private.']}
(out/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n')
print('PASS_FULL_SOURCE_DECODE_INVENTORY' if not errors else 'FAIL_FULL_SOURCE_DECODE_INVENTORY',json.dumps(summary,ensure_ascii=False),flush=True)
if errors:raise SystemExit(1)
