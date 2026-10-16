"""規格068的十五個唯讀來源槽位與8×8模型轉接，不改正式顯示程式。"""
import hashlib,importlib.util,json
from pathlib import Path
TARGETS={112,113,116,119,126,127,136,139}
SLOTS={104,105,106,107,109,110,111,112,113,116,119,126,127,136,139}
REPO=Path(__file__).resolve().parents[1]
def raw_builder(output):
 s=(REPO/'tools/build_hd_terrain_ram_lifecycle_probe.py').read_text().replace('repo=Path(__file__).resolve().parents[1]','repo=Path("/repo")')
 old='ordinals={6,9,17,66,71,74,77,78,79,80,96,147,150}';assert s.count(old)==1;s=s.replace(old,'ordinals='+repr(SLOTS),1)
 old="all(r['size']==[16,16] for r in rows)";assert s.count(old)==1;s=s.replace(old,"all(r['size'] in [[16,16],[8,8]] for r in rows)",1)
 old="'{%d,16,16,%d,%d,%s,%s,nil},'%(row['ordinal'],row['opaque'],row['length']";assert s.count(old)==1;s=s.replace(old,"'{%d,%d,%d,%d,%d,%s,%s,nil},'%(row['ordinal'],*row['size'],row['opaque'],row['length']",1)
 anchor='s=base.read_text()';assert s.count(anchor)==1
 addition="""
s=s.replace('if buildingHash(b.read(record[1], record[0], candidate.Length)) == candidate.Encoded {','if m.CPU.R[golem.AX]==uint16(candidate.Ordinal+1) && buildingHash(b.read(record[1], record[0], candidate.Length)) == candidate.Encoded {')
fixture=json.loads(Path(__file__).with_name('fixture.json').read_bytes())
s=s.replace('3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca',fixture['prefix_sha256'])
s=s.replace('821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901',fixture['points_sha256'])
s=s.replace('len(points) != 49','len(points) != '+str(fixture['point_count'])).replace('end = 134600000','end = '+str(fixture['end']))
"""
 s=s.replace(anchor,anchor+addition,1)
 for old,new in [
 ("assert sha(a.points.read_bytes())=='821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901'","assert sha(a.points.read_bytes())==fixture['points_sha256']"),
 ("assert sha(a.inputs.read_bytes())=='3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca'","assert sha(a.inputs.read_bytes())==fixture['prefix_sha256']"),
 ]:assert s.count(old)==1;s=s.replace(old,new,1)
 compile(s,str(output),'exec');output.write_text(s)
def native_model(output):
 s=(REPO/'tools/check_hd_terrain_ram_lifecycle.py').read_text()
 old='ORDINALS={6,9,17,66,71,74,77,78,79,80,96,147,150}';assert s.count(old)==1;s=s.replace(old,'ORDINALS='+repr(SLOTS),1)
 old="len(pixels[n])==256";assert s.count(old)==1;s=s.replace(old,"len(pixels[n])==r['size'][0]*r['size'][1]",1)
 old="len(before)==len(after)==256";assert s.count(old)==1;s=s.replace(old,"len(raw)==len(before)==len(after)==w*h",1)
 assert s.count('k//16')==s.count('k%16')==3
 s=s.replace('k//16',"k//rows[c['ordinal']]['size'][0]").replace('k%16',"k%rows[c['ordinal']]['size'][0]")
 compile(s,str(output),'exec');output.write_text(s)
 spec=importlib.util.spec_from_file_location('small_terrain_native_model',output);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

