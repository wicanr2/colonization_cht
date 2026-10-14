"""規格064 R42 DRAFT：原型來源／游標與獨立原版模型的逐筆比較。"""
import argparse,base64,hashlib,json,os
from collections import Counter
from pathlib import Path
from check_hd_building_nine_lifecycle import ORDINALS,need,read,sha

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
 pairs=[p for p in actual["cursor_pairs"] if p["step"]<=end];seen=set()
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
 need(baseline["result"]=="PASS_NINE_INDEPENDENT_NATIVE_SOURCE_AND_CURSOR_MODEL" and baseline["ram_restorations_accepted"]==0,"獨立模型未通過")
 bound=[v for k,v in baseline["receipts_sha256"].items() if k.endswith("observed/draws.json")]
 need(bound==[sha((observed/"draws.json").read_bytes())],"獨立模型與本次原版收據不同")
 for point in baseline["points"]:
  need(sha((model/point["owners_file"]).read_bytes())==point["owners_sha256"],"獨立逐點模型指紋不同")
 summaries=[]
 if native:
  actual=read(native);need(len(actual["points"])==len(proof["checkpoints"]),"原型檢查點數不同")
  for i,p in enumerate(actual["points"]):
   oracle=read(model/f"point-{i:03d}.nine-model.json");receipt=p["nine"]
   raw=base64.b64decode(receipt["mask"],validate=True)
   need(len(raw)==8000,"原型遮罩長度不同");cells={k:v for k,v in oracle.items() if raw[int(k)>>3]&(1<<(int(k)&7))}
   counts=mask_cells(receipt,cells,oracle,(observed/(proof["checkpoints"][i]["snapshot_prefix"]+".canvas")).read_bytes())
   need(p["original_state_equal"] and p["step"]==proof["checkpoints"][i]["steps"],"原型狀態或步數不同")
   summaries.append({"point":i,"by_ordinal":counts})
 else:
  dirs=sorted((gui/"nine").glob("nine-*/check.json"),key=lambda p:(read(p)["state"]["step"],read(p)["state"]["dos_input_count"]))
  need(len(dirs)==len(proof["checkpoints"]) and 27<=len(dirs)<=100,"正常GUI快照數不同")
  actual=read(gui/"gui.nine.json")
  for i,path in enumerate(dirs):
   p=read(path);state=p["state"];point=proof["checkpoints"][i];prefix=observed/point["snapshot_prefix"]
   for k in ["memory_sha256","indexed_sha256","palette_sha256","registers","segments","ip","flags","cycles","dos_input_count"]:
    need(state[k]==point[k],"GUI完整原版狀態不同："+k)
   need(state["step"]==point["steps"],"GUI步數不同")
   memory=(path.parent/"memory").read_bytes()
   need(len(memory)==(observed/"final.memory").stat().st_size and sha(memory)==point["memory_sha256"],"GUI完整RAM指紋或長度不同")
   for filename,suffix in [("canvas",".canvas"),("indexed",".idx"),("palette",".palette"),("cursor-source",".cursor"),("cursor-background",".cursor-background"),("cursor-final",".cursor-final")]:
    need((path.parent/filename).read_bytes()==Path(str(prefix)+suffix).read_bytes(),"GUI原始資料不同："+filename)
   counts=mask_cells(p["nine"],p["cells"],read(model/f"point-{i:03d}.nine-model.json"),(path.parent/"canvas").read_bytes())
   summaries.append({"point":i,"label":path.parent.name,"by_ordinal":counts,"hd_reason":p["frame"].get("native_live",{}).get("hd",{}).get("reason")})
 result=traces(actual,proof,model)
 result.update({"result":"PASS_NINE_PROTOTYPE_INDEPENDENT_DISPLAY_COMPARISON","points":summaries,"mode":"native" if native else "normal-gui","production_connected":False,"ram_restorations_accepted":0,"model_sha256":sha((model/"check.json").read_bytes()),"prototype_sha256":sha(native.read_bytes() if native else (gui/"gui.nine.json").read_bytes())})
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ["observed","model","output"]:p.add_argument("--"+name,type=Path,required=True)
 group=p.add_mutually_exclusive_group(required=True);group.add_argument("--native",type=Path);group.add_argument("--gui",type=Path)
 a=p.parse_args();out=a.output.resolve()
 need(Path("/.dockerenv").is_file() and os.getuid()!=0 and out.is_relative_to("/out") and out.parent.stat().st_uid==os.getuid() and not out.exists(),"需新的非root本機輸出")
 result=check(a.observed,a.model,a.native,a.gui);result["checker_sha256"]=sha(Path(__file__).read_bytes())
 out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n");print(result["result"],result["mode"],sha(out.read_bytes()),flush=True)
if __name__=="__main__":
 try:main()
 except (ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as e:raise SystemExit("九來源顯示驗證拒絕："+str(e))
