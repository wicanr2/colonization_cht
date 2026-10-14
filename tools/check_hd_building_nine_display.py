"""規格064 R42 DRAFT：原型來源／游標與獨立原版模型的逐筆比較。"""
import argparse,base64,hashlib,json,os,re
from collections import Counter
from pathlib import Path
from check_hd_building_nine_lifecycle import ORDINALS,need,read,sha
RECEIPT_KEY="nine"

def read_native_state(path):
 """讀Go縮排報表的原版state；歷史畫格可很大，只讀有界尾端。"""
 with path.open("rb") as file:
  header=file.read(1024);indent=re.match(rb'\{\r?\n([ \t]+)"',header)
  need(indent is not None,"原版報表不是已驗Go縮排格式")
  file.seek(max(0,path.stat().st_size-(8<<20)));tail=file.read(8<<20)
 matches=list(re.finditer(rb'(?m)^'+re.escape(indent[1])+rb'"state"[ \t]*:[ \t]*',tail))
 need(len(matches)==1,"報表尾端缺少唯一原版state")
 text=tail[matches[0].end():].decode("utf-8");state,end=json.JSONDecoder().raw_decode(text)
 expected={"memory_sha256","registers","segments","ip","flags","steps","ticks","frames","cycles","frame_sha256","palette_sha256"}
 need(end<=4096 and isinstance(state,dict) and set(state)==expected,"原版state形狀不同")
 for key in ["memory_sha256","frame_sha256","palette_sha256"]:
  need(isinstance(state[key],str) and re.fullmatch(r"[0-9a-f]{64}",state[key]),"原版state指紋格式不同")
 for key,size in [("registers",8),("segments",4)]:
  need(isinstance(state[key],list) and len(state[key])==size and all(type(v)is int and 0<=v<=65535 for v in state[key]),"原版state暫存器不同")
 for key in ["ip","flags","steps","ticks","frames","cycles"]:
  limit=65536 if key in ["ip","flags"] else (1<<64)
  need(type(state[key])is int and 0<=state[key]<limit,"原版state數值不同")
 return state

def image_check(path,proof):
 from PIL import Image,ImageChops,ImageDraw
 live=proof["frame"]["native_live"];hd=live.get("hd") or {}
 indexed=(path/"indexed").read_bytes();palette=(path/"palette").read_bytes()
 need(len(indexed)==64000 and len(palette)==768,"快照索引或色盤長度不同")
 native=Image.frombytes("P",(320,200),indexed);native.putpalette([v<<2|v>>4 for v in palette])
 original=native.convert("RGB").resize((1280,800),Image.Resampling.NEAREST)
 with Image.open(path/"display.png") as image:actual=image.convert("RGB")
 need(actual.size==(1280,800),"正常快照顯示尺寸不同")
 safe=Image.new("1",actual.size);draw=ImageDraw.Draw(safe)
 for item in live.get("items") or []:
  rect=item["safe"];a,b=rect["Min"],rect["Max"]
  draw.rectangle((a["X"]*4,a["Y"]*4,b["X"]*4-1,b["Y"]*4-1),fill=1)
 if hd.get("painted",0)>0:draw.rectangle((224,52,315,159),fill=1)
 for key in ["sea","person","shelter","nine","center"]:
  source=hd.get(key) or {}
  if not source:continue
  raw=base64.b64decode(source["mask"],validate=True);need(len(raw)==8000,"顯示來源遮罩長度不同")
  bits=[bool(raw[i>>3]&(1<<(i&7))) for i in range(64000)]
  expected=source["painted"] if key=="sea" else source["valid"]
  need(sum(bits)==expected,"顯示來源遮罩數不同")
  mask=Image.new("1",(320,200));mask.putdata(bits)
  safe=ImageChops.logical_or(safe,mask.resize(actual.size,Image.Resampling.NEAREST))
 difference=ImageChops.difference(actual,original)
 outside=Image.composite(difference,Image.new("RGB",actual.size),safe.point(lambda v:0 if v else 255,"1"))
 need(outside.getbbox() is None,"正常恢復畫面越出來源或文字安全範圍")
 cursor_points=0
 if hd.get("painted",0)>0 or any((hd.get(k) or {}).get("painted",0)>0 for k in ["sea","person","shelter","nine","center"]):
  cursor=(path/"cursor-source").read_bytes()
  need(sha(cursor)=="47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03","HD快照使用未知游標")
  mouse=proof["state"]["dos_mouse"]
  for k,value in enumerate(cursor):
   x,y=mouse["x"]+k%16,mouse["y"]+k//16
   if value==255 or not (0<=x<320 and 0<=y<200):continue
   rect=(x*4,y*4,x*4+4,y*4+4)
   need(actual.crop(rect).tobytes()==original.crop(rect).tobytes(),"正常恢復畫面覆蓋不透明游標")
   cursor_points+=1
 return {"outside_changed":0,"verified_cursor_pixels":cursor_points,"locale":live["locale"],"hd_reason":hd.get("reason")}

def traces(actual,proof,model):
 end=proof["end"]["steps"]
 calls=[c for c in actual["calls"] if c["return_step"]<=end+1]
 expected=proof["calls"]
 need(len(calls)==len(expected),"實際來源呼叫數不同")
 mapped={"record":"record_words","source_sha256":"source_encoded_sha256","stack":"ss_sp_words","writes_sha256":"sorted_local_offset_value_sha256"}
 keys=["ordinal","record_far","source_far","rect","registers","segments","return_registers","return_segments","return_ip"]
 for c,o in zip(calls,expected):
  for k in keys:need(c[k]==o[k],"實際來源參數不同："+k)
  for k,v in mapped.items():need(c[k]==o[v],"實際來源內容不同："+k)
  # 探針在Machine.Step之前讀取；正式同步掛鉤在Steps遞增後讀取。
  need(c["entry_step"]==o["entry_step"]+1 and c["return_step"]==o["return_step"]+1,"來源觀測步數基準不同")
 known={(r["step"],r["linear"]):r for r in read(model/"cursor-pairs.json")}
 raw_pairs=actual["cursor_pairs"]
 need(raw_pairs is None or isinstance(raw_pairs,list),"實際游標配對不是陣列")
 pairs=[p for p in (raw_pairs or []) if p["step"]<=end];seen=set()
 for p in pairs:
  key=p["step"],p["linear"];need(key not in seen and key in known,"實際游標配對無原版事件");seen.add(key);r=known[key];e=r["event"];c=r["cell"]
  for k,v in [("ordinal",c["ordinal"]),("local",c["local"]),("native",c["native"]),("source_cursor_index",r["cursor"]),("restore_old",e["old"]),("restore_value",e["value"]),("paint_old",e["value"]),("paint_value",e["old"]),("registers",e["registers"]),("segments",e["segments"]),("code16",e["code16"])]:
   need(p[k]==v,"實際游標配對內容不同："+k)
 return {"verified_source_calls":len(calls),"verified_cursor_pairs":len(pairs),"oracle_cursor_pairs":len(known),"pair_counts_by_ordinal":dict(Counter(p["ordinal"] for p in pairs)),"source_step_convention":"runtime BeforeInstruction = standalone beforeStep + 1; raw write steps unchanged"}

def mask_cells(receipt,cells,oracle,canvas):
 need(receipt["owned"]==len(cells),"實際逐點身分數不同")
 raw=base64.b64decode(receipt["mask"],validate=True);need(len(raw)==8000,"實際來源遮罩長度不同")
 valid=set()
 for pos,c in cells.items():
  need(pos in oracle and all(c[k]==oracle[pos][k] for k in ["ordinal","local","native"]),"實際來源沒有獨立原版身分")
  at=int(pos);need(0<=at<64000 and canvas[at]==c["native"],"實際來源已過期");valid.add(at)
 got={i for i in range(64000) if raw[i>>3]&(1<<(i&7))}
 need(got==valid and receipt["valid"]==len(valid),"實際逐點遮罩不同")
 need(set(map(int,receipt["sources"]))==ORDINALS,"個別來源清冊不同")
 for ordinal,source in receipt["sources"].items():
  part=base64.b64decode(source["mask"],validate=True);need(len(part)==8000,"個別來源遮罩長度不同")
  points={i for i in range(64000) if part[i>>3]&(1<<(i&7))}
  expected={int(k) for k,c in cells.items() if c["ordinal"]==int(ordinal)}
  need(points==expected and source["owned"]==source["valid"]==len(expected),"個別來源身分或遮罩不同")
 return dict(Counter(c["ordinal"] for c in cells.values()))

def check(observed,model,native=None,gui=None):
 proof=read(observed/"draws.json");baseline=read(model/"check.json")
 expected_model="PASS_CENTER_INDEPENDENT_NATIVE_SOURCE_AND_CURSOR_MODEL" if RECEIPT_KEY=="center" else "PASS_NINE_INDEPENDENT_NATIVE_SOURCE_AND_CURSOR_MODEL"
 need(baseline["result"]==expected_model and baseline["ram_restorations_accepted"]==0,"獨立模型未通過")
 bound=[v for k,v in baseline["receipts_sha256"].items() if k.endswith("observed/draws.json")]
 need(bound==[sha((observed/"draws.json").read_bytes())],"獨立模型與本次原版收據不同")
 for point in baseline["points"]:
  need(sha((model/point["owners_file"]).read_bytes())==point["owners_sha256"],"獨立逐點模型指紋不同")
 summaries=[]
 if native:
  actual=read(native);need(len(actual["points"])==len(proof["checkpoints"]),"原型檢查點數不同")
  for i,p in enumerate(actual["points"]):
   oracle=read(model/f"point-{i:03d}.nine-model.json");receipt=p[RECEIPT_KEY]
   raw=base64.b64decode(receipt["mask"],validate=True)
   need(len(raw)==8000,"原型遮罩長度不同");cells={k:v for k,v in oracle.items() if raw[int(k)>>3]&(1<<(int(k)&7))}
   counts=mask_cells(receipt,cells,oracle,(observed/(proof["checkpoints"][i]["snapshot_prefix"]+".canvas")).read_bytes())
   need(p["original_state_equal"] and p["step"]==proof["checkpoints"][i]["steps"],"原型狀態或步數不同")
   summaries.append({"point":i,"by_ordinal":counts})
 else:
  dirs=sorted((gui/RECEIPT_KEY).glob(RECEIPT_KEY+"-*/check.json"),key=lambda p:(read(p)["state"]["step"],read(p)["state"]["dos_input_count"]))
  need(len(dirs)==len(proof["checkpoints"]) and (3 if RECEIPT_KEY=="center" else 27)<=len(dirs)<=100,"正常GUI快照數不同")
  actual=read(gui/("gui."+RECEIPT_KEY+".json"))
  for i,path in enumerate(dirs):
   p=read(path);state=p["state"];point=proof["checkpoints"][i];prefix=observed/point["snapshot_prefix"]
   for k in ["memory_sha256","indexed_sha256","palette_sha256","registers","segments","ip","flags","cycles","dos_input_count"]:
    need(state[k]==point[k],"GUI完整原版狀態不同："+k)
   need(state["step"]==point["steps"],"GUI步數不同")
   memory=(path.parent/"memory").read_bytes()
   need(len(memory)==(observed/"final.memory").stat().st_size and sha(memory)==point["memory_sha256"],"GUI完整RAM指紋或長度不同")
   for filename,suffix in [("canvas",".canvas"),("indexed",".idx"),("palette",".palette"),("cursor-source",".cursor"),("cursor-background",".cursor-background"),("cursor-final",".cursor-final")]:
    need((path.parent/filename).read_bytes()==Path(str(prefix)+suffix).read_bytes(),"GUI原始資料不同："+filename)
   counts=mask_cells(p[RECEIPT_KEY],p["cells"],read(model/f"point-{i:03d}.nine-model.json"),(path.parent/"canvas").read_bytes())
   summaries.append({"point":i,"label":path.parent.name,"by_ordinal":counts,"image":image_check(path.parent,p)})
 result=traces(actual,proof,model)
 result.update({"result":"PASS_NINE_PROTOTYPE_INDEPENDENT_DISPLAY_COMPARISON","points":summaries,"mode":"native" if native else "normal-gui","production_connected":False,"ram_restorations_accepted":0,"model_sha256":sha((model/"check.json").read_bytes()),"prototype_sha256":sha(native.read_bytes() if native else (gui/("gui."+RECEIPT_KEY+".json")).read_bytes())})
 return result

def main():
 global ORDINALS,RECEIPT_KEY
 p=argparse.ArgumentParser(description=__doc__)
 for name in ["observed","model","output"]:p.add_argument("--"+name,type=Path,required=True)
 group=p.add_mutually_exclusive_group(required=True);group.add_argument("--native",type=Path);group.add_argument("--gui",type=Path)
 p.add_argument("--formal",action="store_true",help="核對正式九來源的49點原版路徑")
 p.add_argument("--central",action="store_true",help="規格064 R44：獨立核對中央第009幀原型")
 p.add_argument("--include-central",action="store_true",help="規格064 R44 READY：獨立核對十來源")
 a=p.parse_args();out=a.output.resolve()
 need(not (a.central and a.include_central),"來源模式互斥")
 if a.include_central:
  ORDINALS=ORDINALS|{9}
  need(read(a.model/"check.json").get("source_profile")=="ten-including-central009","模型來源模式不同")
 need(Path("/.dockerenv").is_file() and os.getuid()!=0 and out.is_relative_to("/out") and out.parent.stat().st_uid==os.getuid() and not out.exists(),"需新的非root本機輸出")
 if a.central:
  need(not a.formal,"中央來源仍為DRAFT原型");ORDINALS={9};RECEIPT_KEY="center"
 result=check(a.observed,a.model,a.native,a.gui);result["checker_sha256"]=sha(Path(__file__).read_bytes())
 if a.central:result["result"]="PASS_CENTER_PROTOTYPE_INDEPENDENT_DISPLAY_COMPARISON"
 if a.formal:
  need(a.native is not None and read(a.native).get("production_connected") is True,"正式審查需要正式原版路徑收據")
  result.update(result="PASS_NINE_FORMAL_INDEPENDENT_DISPLAY_COMPARISON",production_connected=True)
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n");print(result["result"],result["mode"],sha(out.read_bytes()),flush=True)
if __name__=="__main__":
 try:main()
 except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as e:raise SystemExit("九來源顯示驗證拒絕："+str(e))
