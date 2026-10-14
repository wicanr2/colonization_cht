"""規格064 R42 DRAFT：獨立重建九來源與一般游標配對，不接受RAM還原。"""
import argparse,base64,hashlib,json,os,struct
from collections import Counter
from pathlib import Path

ORDINALS={16,21,27,35,39,42,43,44,45}
CURSOR="47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03"
COPY="f3a48ac82bf92bf103f303fafecc75f0"
def need(value,message):
 if not value:raise ValueError(message)
def read(path):return json.loads(path.read_bytes())
def sha(data):return hashlib.sha256(data).hexdigest()
def sha_file(path):
 digest=hashlib.sha256()
 with path.open("rb") as file:
  for block in iter(lambda:file.read(1048576),b""):digest.update(block)
 return digest.hexdigest()
def event_stream(path):
 """逐筆讀標準JSON陣列；同時接受歷史縮排及新串流輸出。"""
 decoder=json.JSONDecoder();buffer="";pos=0;eof=False;count=0
 with path.open(encoding="utf-8") as file:
  def fill():
   nonlocal buffer,pos,eof
   chunk=file.read(65536);buffer=buffer[pos:]+chunk;pos=0;eof=not chunk
  def peek():
   nonlocal pos
   while True:
    while pos<len(buffer) and buffer[pos].isspace():pos+=1
    if pos<len(buffer):return buffer[pos]
    if eof:return ""
    fill()
  need(peek()=="[","事件檔不是JSON陣列");pos+=1;first=True
  while True:
   char=peek()
   if char=="]":
    pos+=1;need(peek()=="","事件陣列後有額外資料");return
   if not first:
    need(char==",","事件之間缺少逗號");pos+=1
    need(peek() not in ["", "]"],"事件陣列截斷或多餘逗號")
   else:need(char!="","事件陣列截斷")
   while True:
    try:value,end=decoder.raw_decode(buffer,pos);break
    except json.JSONDecodeError:
     need(not eof and len(buffer)-pos<1048576,"事件JSON截斷或單筆超限");fill()
   pos=end;first=False;count+=1
   need(isinstance(value,dict) and count<=8000000,"事件型別或總數超限")
   yield value
def check(observed,control,sources,output):
 manifest=read(sources/"source.json")
 need(sha((sources/"source.json").read_bytes())=="a7457d86c0e587b8e06a2d94db0ade8c88a8167e4cf74a8d2910ff734f15be72","R39來源清冊不同")
 old=read(sources/"lifecycle-r1/observed/draws.json")
 first={n:next(c for c in old["calls"] if c["ordinal"]==n) for n in ORDINALS}
 rows={r["ordinal"]:r for r in manifest["sources"] if r["ordinal"] in ORDINALS}
 pixels={n:(sources/f"building-{n:03}.pixels").read_bytes() for n in ORDINALS}
 opaque={}
 for n,row in rows.items():
  need(sha(pixels[n])==row["decoded_indexed_sha256"] and len(pixels[n])==row["size"][0]*row["size"][1],"索引來源不同")
  opaque[n]={i:v for i,v in enumerate(pixels[n]) if v!=253}
 proof=read(observed/"draws.json");plain=read(control/"draws.json")
 event_count=proof.get("raw_event_count")
 if event_count is None:event_count=sum(1 for _ in event_stream(observed/"writes.json"))
 need(isinstance(event_count,int) and 0<=event_count<=8000000,"事件總數不同")
 events=iter(event_stream(observed/"writes.json"));kinds=Counter()
 need(proof["control"] is False and plain["control"] is True and proof["end"]==plain["end"],"原版觀測／控制終點不同")
 need(proof["input_sha256"]==plain["input_sha256"] and proof["seed_sha256"]==plain["seed_sha256"],"兩側輸入或種子不同")
 need(len(proof["checkpoints"])==len(plain["checkpoints"]) and set(c["ordinal"] for c in proof["calls"])==ORDINALS,"九來源或檢查點缺漏")
 calls=proof["calls"]
 for c in calls:
  n=c["ordinal"];row=rows[n];known=first[n];w,h=row["size"]
  need(c["selected"] and not c.get("geometry_or_write_mismatch"),"未完整接受原版繪製")
  for key in ["record_far","record_words","source_far","source_encoded_sha256","entry_code12"]:
   need(c[key]==known[key],"原始來源或入口不同："+key)
  need(c["source_encoded_sha256"]==row["encoded_sha256"] and c["entry_code12"]=="c828000052535057568b4702","來源編碼或入口不同")
  writer={k:v for call in old["calls"] if call["ordinal"]==n for k,v in call["writer_code16"].items()}
  need(c["writer_code16"] and all(writer.get(k)==v for k,v in c["writer_code16"].items()),"未驗原始寫入碼")
  x,y,r,b=c["rect"]
  need(0<=x<r<=320 and 0<=y<b<=200 and (r-x,b-y)==(w,h) and c["canvas_linear"]==0x2cae0
       and c["ds_bx_words"]==[200,320,0,0x2cae] and c["registers"][0]==n+1 and c["registers"][2]==x and c["ss_sp_words"][2]==y,"原版幾何或畫布不同")
  need(c["return_segments"][1]==c["ss_sp_words"][1] and c["return_ip"]==c["ss_sp_words"][0]
       and c["return_registers"][4]==(c["registers"][4]+10)&65535 and 0<c["return_step"]-c["entry_step"]<=100000,"返回不同")
  pairs=b"".join(struct.pack("<HB",k,v) for k,v in opaque[n].items())
  need(c["unique_writes"]==c["write_count"]==sum(c["writer_sites"].values())==len(opaque[n])
       and c["sorted_local_offset_value_sha256"]==sha(pairs) and c["transparent_background_unchanged"] and c["outside_rectangle_unchanged"],"完整逐點寫入不同")
  before,after=[base64.b64decode(c[k],validate=True) for k in ["private_before_roi","private_after_roi"]]
  need(len(before)==len(after)==w*h and all(after[k]==(before[k] if v==253 else v) for k,v in enumerate(pixels[n])),"透明底圖不同")
 owner={};pending={};native={};tracked=set();backing={};cursor=None;at=next_call=drawn=last_step=0;restores=[];summaries=[]
 points=proof["checkpoints"]+[dict(proof["end"],event_count=event_count,snapshot_prefix=None)]
 for index,point in enumerate(points):
  final=point["snapshot_prefix"] is None
  if not final:
   baseline=plain["checkpoints"][index]
   for key in ["steps","memory_sha256","indexed_sha256","palette_sha256","registers","segments","ip","flags","cycles","dos_input_count"]:
    need(point[key]==baseline[key],"原版控制檢查點不同："+key)
  need(at<=point["event_count"]<=event_count,"事件序號不同")
  while at<point["event_count"]:
   try:e=next(events)
   except StopIteration:raise ValueError("事件檔提前結束")
   kinds[e["kind"]]+=1
   need(last_step<=e["step"]<=point["steps"],"事件步數倒退");last_step=e["step"]
   while next_call<len(calls) and calls[next_call]["entry_step"]<=e["step"]:
    c=calls[next_call];w,h=rows[c["ordinal"]]["size"];x,y,_,_=c["rect"];before=base64.b64decode(c["private_before_roi"],validate=True)
    for k,v in enumerate(before):
     pos=(y+k//w)*320+x+k%w
     need(pos not in tracked or native[pos]==v,"來源繪製前底圖不能重建")
     tracked.add(pos);native[pos]=v
    next_call+=1
   if e["kind"]=="cursor-init":
    need(cursor is None and e["step"]==49999999 and e["linear"]==0x1cd74,"游標初始來源不同")
    cursor=bytearray(base64.b64decode(e["bytes"],validate=True));need(len(cursor)==256,"游標來源長度不同")
   elif e["kind"]=="cursor-write":
    k=e["linear"]-0x1cd74
    need(cursor is not None and 0<=k<256 and cursor[k]==e["old"] and len(bytes.fromhex(e["code16"]))==16,"游標來源逐筆寫入不同")
    cursor[k]=e["value"]
   elif e["kind"]=="ram-write":
    pos=e["linear"]
    need(pos not in backing or backing[pos]==e["old"],"RAM候選逐筆值不同")
    backing[pos]=e["value"] # Observed only. No source identity is granted.
   elif e["kind"]=="draw":
    drawn+=1;need(e["call"]==drawn and calls[drawn-1]["return_step"]==e["step"],"來源建立順序不同")
    c=calls[drawn-1];n=c["ordinal"];w,h=rows[n]["size"];x,y,_,_=c["rect"]
    after=base64.b64decode(c["private_after_roi"],validate=True)
    need(all(native[(y+k//w)*320+x+k%w]==v for k,v in enumerate(after)),"返回底圖不能重建")
    for k,v in opaque[n].items():owner[(y+k//w)*320+x+k%w]={"ordinal":n,"call":drawn,"local":k,"native":v}
   elif e["kind"]=="write":
    need(e["surface"]==0 and 0<=e["offset"]<64000 and len(bytes.fromhex(e["code16"]))==16,"主畫布寫入越界")
    pos=e["offset"]
    need(pos not in tracked or native[pos]==e["old"],"原始寫入舊值不同")
    if pos in tracked:native[pos]=e["value"]
    cell=owner.pop(pos,None);r,g=e["registers"],e["segments"]
    src=r[6]+0x2cae0+pos-(g[0]*16+r[7])
    known=cursor is not None and sha(bytes(cursor))==CURSOR and e["site"]=="0B68:051C" and e["code16"]==COPY and g[3]==0xa000 and g[0]==0x2cae and 0xfa00<=src<0xfc00
    if known:
     k=src&255
     if src>=0xfb00:pending[pos]=(cell,e["old"],e["value"],k)
     else:
      prior=pending.pop(pos,None)
      if prior and prior[0] and prior[1]==e["value"] and prior[2]==e["old"] and prior[3]==k:
       owner[pos]=prior[0];restores.append({"step":e["step"],"linear":0x2cae0+pos,"cell":prior[0],"cursor":k,"event":e})
    else:pending.clear()
   else:raise ValueError("未知事件種類")
   at+=1
  if not final:
   prefix=point["snapshot_prefix"];canvas=(observed/(prefix+".canvas")).read_bytes()
   need(len(canvas)==64000 and all(canvas[pos]==v for pos,v in native.items()),"完整來源區底圖不能重建")
   need(all(canvas[pos]==c["native"] for pos,c in owner.items()),"來源身分已過期")
   if cursor is not None:need(bytes(cursor)==(observed/(prefix+".cursor")).read_bytes(),"游標來源不能重建")
   name=f"point-{index:03d}.nine-model.json";(output/name).write_text(json.dumps(owner,sort_keys=True)+"\n")
   summaries.append({"point":index,"step":point["steps"],"owned":len(owner),"by_ordinal":dict(Counter(c["ordinal"] for c in owner.values())),"owners_file":name,"owners_sha256":sha((output/name).read_bytes())})
 need(at==event_count and next(events,None) is None and next_call==drawn==len(calls),"仍有未驗原版事件")
 (output/"cursor-pairs.json").write_text(json.dumps(restores)+"\n")
 return {"result":"PASS_NINE_INDEPENDENT_NATIVE_SOURCE_AND_CURSOR_MODEL","source_calls":len(calls),"raw_events":event_count,"event_kinds":dict(kinds),"verified_cursor_restores":len(restores),"points":summaries,"production_connected":False,"ram_restorations_accepted":0,"unknown_backing_addresses_observed":len(backing),"input_sha256":proof["input_sha256"],"limitations":["原版來源模型；尚未授予新素材正式接線或新GUI信用。","RAM事件只記錄，未知後畫與未知游標不授予還原。"]}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ["observed","control","sources","output"]:p.add_argument("--"+name,type=Path,required=True)
 a=p.parse_args();out=a.output.resolve()
 need(Path("/.dockerenv").is_file() and os.getuid()!=0,"需非root容器")
 need((out.is_relative_to(Path("/out")) or out.is_relative_to(Path(__file__).resolve().parents[1]/"workplace")) and out.parent.stat().st_uid==os.getuid() and not out.exists(),"需新的本機輸出")
 out.mkdir();report=check(a.observed,a.control,a.sources,out);report["checker_sha256"]=sha(Path(__file__).read_bytes())
 report["receipts_sha256"]={str(p):sha_file(p) for p in [a.observed/"draws.json",a.observed/"writes.json",a.control/"draws.json",a.sources/"source.json"]}
 target=out/"check.json";target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n");print(report["result"],sha(target.read_bytes()),report["verified_cursor_restores"])
if __name__=="__main__":
 try:main()
 except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as e:raise SystemExit("九來源驗證拒絕："+str(e))
