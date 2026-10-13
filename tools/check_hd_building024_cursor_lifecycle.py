"""規格064 DRAFT：獨立重建木棚逐點來源與游標配對，核對10張實際視窗收據。"""
import argparse,base64,hashlib,json,os,struct
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
PIXELS="c22c2d5aa17d28373e7588832295924ccafeb15c93576bee89312baf00c28898"
ENCODED="91a6a162404b43e2c17d13bd1ffe5818286e27763ffab2a776f24bc1fbf70c03"
CURSOR="47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03"
CODE="f3a48ac82bf92bf103f303fafecc75f0"
WRITERS={"0D46:01D2":"268807035ef042ebb5905a5b035efe79"}
LABELS=["shelter-hover-roof","shelter-away-roof","shelter-return-roof","shelter-hover-post","shelter-away-post","shelter-return-post","shelter-drag-held","shelter-drag-moved","shelter-drag-returned","shelter-drag-released"]
def need(v,msg):
 if not v:raise ValueError(msg)
def read(p):return json.loads(p.read_bytes())
def sha(b):return hashlib.sha256(b).hexdigest()
def check(gui,observed,pixels):
 proof=read(observed/"draws.json");events=read(observed/"writes.json")
 receipt=read(gui/"check.json");trace=read(gui/"gui.shelter.json")
 raw=pixels.read_bytes()
 need(len(raw)==621 and sha(raw)==PIXELS,"木棚索引來源不同")
 need(receipt["result"]=="PASS_SHELTER_PROTOTYPE_FIVE_LANGUAGE_GUI" and len(receipt["checks"])==322,"五語GUI未通過")
 need(proof["control"] is False and proof["input_sha256"]==sha((gui/"gui.inputs.json").read_bytes())==receipt["gui_inputs_sha256"],"原版探針與GUI輸入不同")
 snapshots=[(label,read(gui/"shelter"/label/"check.json")) for label in LABELS]
 snapshots.sort(key=lambda item:(item[1]["state"]["step"],item[1]["state"]["dos_input_count"]))
 need(len(proof["checkpoints"])==10,"原版診斷點數不同")
 calls=proof["calls"];opaque={i:v for i,v in enumerate(raw) if v!=253}
 write_sha=sha(b"".join(struct.pack("<HB",i,v) for i,v in opaque.items()))
 need(len(calls)==proof["source_matches"]>=1,"木棚來源未走完")
 for call in calls:
  need(call["selected"] and not call.get("geometry_or_write_mismatch"),"木棚原版繪製失敗")
  need(call["source_encoded_sha256"]==ENCODED and call["record_far"]=="4F22:A826"
       and call["record_words"]==[2,0x5e6b,84,149,23,27] and call["source_far"]=="5E6B:0002","木棚完整來源不同")
  need(call["entry_code12"]=="c828000052535057568b4702" and call["writer_code16"]==WRITERS
       and call["writer_sites"]=={"0D46:01D2":263},"木棚原始指令不同")
  x,y,right,bottom=call["rect"]
  need(call["rect"] in [[37,45,60,72]] and right-x==23 and bottom-y==27
       and call["canvas_linear"]==0x2cae0 and call["ds_bx_words"]==[200,320,0,0x2cae]
       and call["registers"][0]==25 and call["registers"][2]==x and call["ss_sp_words"][2]==y,"木棚畫布或位置未驗")
  need(call["return_segments"][1]==call["ss_sp_words"][1] and call["return_ip"]==call["ss_sp_words"][0]
       and call["return_registers"][4]==(call["registers"][4]+10)&65535
       and 0<call["return_step"]-call["entry_step"]<=100000,"木棚返回不同")
  need(call["unique_writes"]==call["write_count"]==263 and call["sorted_local_offset_value_sha256"]==write_sha
       and call["transparent_background_unchanged"] and call["outside_rectangle_unchanged"],"木棚寫入或底圖不同")
  before,after=[base64.b64decode(call[k],validate=True) for k in ["private_before_roi","private_after_roi"]]
  need(len(before)==len(after)==621 and all(after[k]==(before[k] if v==253 else v) for k,v in enumerate(raw)),"木棚透明底圖不同")
 owner={};pending={};native={};restores={};summaries=[];cursor=None;fallbacks=[]
 at=next_call=drawn=last_step=0
 for index,((label,snapshot),point) in enumerate(zip(snapshots,proof["checkpoints"])):
  state=snapshot["state"]
  for key in ["memory_sha256","indexed_sha256","palette_sha256","registers","segments","ip","flags","dos_input_count"]:
   need(point[key]==state[key],"原版與GUI檢查點不同："+key)
  need(point["steps"]==state["step"] and point["snapshot_prefix"]==f"point-{index:03d}","原版診斷時點不同")
  prefix=point["snapshot_prefix"]
  for a,b,size in [(".idx","indexed",64000),(".canvas","canvas",64000),(".palette","palette",768)]:
   data=(observed/(prefix+a)).read_bytes()
   need(len(data)==size and data==(gui/"shelter"/label/b).read_bytes(),"原版與GUI底圖不同")
  canvas=(observed/(prefix+".canvas")).read_bytes()
  memory=(gui/"shelter"/label/"memory").read_bytes()
  need(sha(memory)==state["memory_sha256"] and sha(memory[0x1cd74:0x1ce74])==snapshot["cursor_source_sha256"],"GUI原始RAM或游標來源不同")
  need(at<=point["event_count"]<=len(events),"事件序號不同")
  while at<point["event_count"]:
   e=events[at];need(last_step<=e["step"]<=point["steps"],"事件步數倒退");last_step=e["step"]
   while next_call<len(calls) and calls[next_call]["entry_step"]<=e["step"]:
    c=calls[next_call];x,y,_,_=c["rect"];before=base64.b64decode(c["private_before_roi"],validate=True)
    for k,v in enumerate(before):
     pos=(y+k//23)*320+x+k%23
     need(pos not in native or native[pos]==v,"木棚繪製前底圖不能重建");native[pos]=v
    next_call+=1
   if e["kind"]=="cursor-init":
    need(cursor is None and e["linear"]==0x1cd74 and e["step"]==49999999,"游標初始來源不同")
    cursor=bytearray(base64.b64decode(e["bytes"],validate=True));need(len(cursor)==256,"游標初始長度不同")
   elif e["kind"]=="cursor-write":
    local=e["linear"]-0x1cd74
    need(cursor is not None and 0<=local<256 and cursor[local]==e["old"] and 0<=e["value"]<=255 and len(bytes.fromhex(e["code16"]))==16,"游標來源寫入不同")
    cursor[local]=e["value"]
   elif e["kind"]=="draw":
    drawn+=1;need(e["call"]==drawn and calls[drawn-1]["return_step"]==e["step"],"木棚建立順序不同")
    c=calls[drawn-1];x,y,_,_=c["rect"];after=base64.b64decode(c["private_after_roi"],validate=True)
    for k,v in enumerate(after):need(native[(y+k//23)*320+x+k%23]==v,"木棚返回像素不能重建")
    for k,v in opaque.items():owner[(y+k//23)*320+x+k%23]={"call":drawn,"local":k,"native":v}
   elif e["kind"]=="write":
    need(e["surface"]==0 and 0<=e["offset"]<64000 and len(bytes.fromhex(e["code16"]))==16,"木棚ROI寫入越界")
    pos=e["offset"];need(native.get(pos)==e["old"],"逐筆寫入舊值不同");native[pos]=e["value"]
    cell=owner.pop(pos,None);r,g=e["registers"],e["segments"]
    delta=0x2cae0+pos-(g[0]*16+r[7]);src=r[6]+delta
    known_cursor=cursor is not None and sha(bytes(cursor))==CURSOR and e["site"]=="0B68:051C" and e["code16"]==CODE and g[3]==0xa000 and g[0]==0x2cae and 0xfa00<=src<0xfc00
    if known_cursor:
     k=src&255
     if src>=0xfb00:pending[pos]=(cell,e["old"],e["value"],k)
     else:
      prior=pending.pop(pos,None)
      if prior and prior[1]==e["value"] and prior[2]==e["old"] and prior[3]==k and prior[0]:
       owner[pos]=prior[0];restores[(e["step"],0x2cae0+pos)]={"event":e,"cell":prior[0],"cursor":k}
    else:pending.clear()
   else:raise ValueError("未審查的背景RAM轉送")
   at+=1
  need(cursor is not None and bytes(cursor)==memory[0x1cd74:0x1ce74],"游標來源不能由原始寫入重建")
  if sha(bytes(cursor))!=CURSOR:
   need(label in {"shelter-drag-moved","shelter-drag-returned"} and state["dos_mouse"]["buttons"]==1,"未審查的未知游標場景")
   record=snapshot["frame"]["native_live"];hd=record.get("hd") or {}
   need(hd.get("reason")=="unverified-cursor-or-native-surface" and hd.get("painted",0)==0 and all(not (hd.get(k) or {}).get("painted") for k in ["sea","person","shelter"]),"未知游標仍繪製HD素材")
   indexed=(gui/"shelter"/label/"indexed").read_bytes();palette=(gui/"shelter"/label/"palette").read_bytes()
   original=Image.frombytes("P",(320,200),indexed);original.putpalette(bytes((v<<2)|(v>>4) for v in palette))
   original=original.convert("RGB").resize((1280,800),Image.Resampling.NEAREST)
   with Image.open(gui/"shelter"/label/"display.png") as image:actual=image.convert("RGB")
   need(actual.size==(1280,800) and record.get("items") and record.get("locale")=="zh-Hant","未知游標回退遺失語言或畫面")
   safe=Image.new("1",actual.size);draw=ImageDraw.Draw(safe)
   for item in record["items"]:
    rect=item["safe"];draw.rectangle((rect["Min"]["X"]*4,rect["Min"]["Y"]*4,rect["Max"]["X"]*4-1,rect["Max"]["Y"]*4-1),fill=1)
   difference=ImageChops.difference(actual,original)
   outside=Image.composite(difference,Image.new("RGB",actual.size),safe.point(lambda v:0 if v else 255,"1"))
   need(outside.getbbox() is None and difference.getbbox() is not None,"未知游標回退未保留原版圖像與語言安全區")
   x,y=state["dos_mouse"]["x"],state["dos_mouse"]["y"];box=(x*4,y*4,(x+16)*4,(y+16)*4)
   need(actual.crop(box).tobytes()==original.crop(box).tobytes(),"未知游標整個矩形未保留原版")
   fallbacks.append({"label":label,"cursor_sha256":sha(bytes(cursor)),"locale":record["locale"],"language_items":len(record["items"]),"original_graphics_outside_text":True,"original_cursor_rectangle_pixels":4096})
  need(all(canvas[pos]==v for pos,v in native.items()),"全部ROI底圖不能重建")
  actual={int(k):v for k,v in snapshot["cells"].items()};shelter=snapshot["shelter"]
  need(len(actual)==shelter["owned"]==shelter["valid"],"GUI木棚來源已過期")
  for pos,cell in actual.items():
   need(pos in owner and {k:owner[pos][k] for k in ["local","native"]}==cell and canvas[pos]==cell["native"],"HD木棚沒有原始寫入來源")
  mask=base64.b64decode(shelter["mask"],validate=True)
  need(len(mask)==8000 and {i for i in range(64000) if mask[i>>3]&(1<<(i&7))}==set(actual),"GUI木棚遮罩不同")
  if label in ["shelter-away-roof","shelter-away-post"]:
   need(len(actual)==263 and shelter["cursor_restore_points"]>0,"游標離開後木棚未完整還原："+label)
  need(state["dos_mouse"]["buttons"]==(1 if label in ["shelter-drag-held","shelter-drag-moved","shelter-drag-returned"] else 0),"正常按住／放開路徑不同")
  summaries.append({"label":label,"step":point["steps"],"dos_input_count":point["dos_input_count"],"owned":len(actual),"oracle_owned":len(owner),"cursor_restores":shelter["cursor_restore_points"]})
 need(at==len(events) and drawn==next_call==len(calls),"仍有未驗證的原版事件")
 pairs=[p for p in trace["cursor_pairs"] if p["step"]<=proof["end"]["steps"]]
 need(pairs,"沒有原版木棚游標配對")
 for p in pairs:
  found=restores.get((p["step"],p["linear"]));need(found,"HD游標配對沒有原版寫入")
  e,c=found["event"],found["cell"]
  need(p["code16"]==e["code16"]==CODE and p["registers"]==e["registers"] and p["segments"]==e["segments"]
       and p["local"]==c["local"] and p["native"]==c["native"] and p["source_cursor_index"]==found["cursor"]
       and p["paint_old"]==p["restore_value"]==e["value"] and p["paint_value"]==p["restore_old"]==e["old"],"HD木棚游標配對原始參數不同")
 need(len(fallbacks)==2,"兩張未知拖曳游標的回退證據不同")
 return {"result":"PASS_SHELTER_CURSOR_10_GUI_POINTS_AND_RAW_WRITES","production_connected":False,"unknown_cursor_fallbacks":fallbacks,
         "source_calls":len(calls),"raw_events":len(events),"verified_cursor_restores":len(pairs),"points":summaries,
         "input_sha256":proof["input_sha256"],"end":proof["end"]["steps"],
         "limitations":["單一第024幀木棚來源；未授予其他建築、動畫或正式接線信用。","未知寫入仍撤銷；未接受RAM背景副本轉送。"]}
def main():
 parser=argparse.ArgumentParser(description=__doc__)
 for name in ["gui","observed","pixels","output"]:parser.add_argument("--"+name,type=Path,required=True)
 a=parser.parse_args();out=a.output.resolve()
 need(Path("/.dockerenv").is_file() and os.getuid()!=0,"需非root容器")
 need((out.is_relative_to(Path("/out")) or out.is_relative_to(ROOT/"workplace")) and out.parent.stat().st_uid==os.getuid() and not out.exists(),"需新的本機輸出")
 result=check(a.gui,a.observed,a.pixels);result["checker_sha256"]=sha(Path(__file__).read_bytes())
 result["receipts_sha256"]={str(p):sha(p.read_bytes()) for p in [a.gui/"check.json",a.gui/"gui.shelter.json",a.observed/"draws.json",a.observed/"writes.json"]}
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n");print(result["result"],sha(out.read_bytes()))
if __name__=="__main__":
 try:main()
 except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as e:raise SystemExit("木棚游標驗證拒絕："+str(e))
