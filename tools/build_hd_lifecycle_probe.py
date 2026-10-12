"""重播已驗的53筆正常GUI輸入，唯讀觀測首座建築與游標；只供研究。"""
import argparse
from pathlib import Path
import os
import json
import hashlib
import shutil
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--gui-dir", type=Path, required=True)
parser.add_argument("--output-dir", type=Path, required=True)
parser.add_argument("--game-root", type=Path, default=Path("/game"))
parser.add_argument("--draw-query", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
gui = args.gui_dir.resolve()
dest = args.output_dir.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
if not all((args.game_root / n).is_file() for n in ["VICEROY.EXE", "BUILDING.SS"]):
    print("SKIP: 缺少合法原版 VICEROY.EXE 或 BUILDING.SS")
    raise SystemExit(77)
assert dest.is_relative_to(Path("/out")) or dest.is_relative_to(root / "workplace")
assert dest.parent.stat().st_uid == os.getuid() and not dest.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
check=json.loads((gui/'check.json').read_bytes())
assert check['result']=='PASS_NATIVE_GUI_BUILDING_LIFECYCLE_INPUTS'
assert len(check['checks'])==55
assert check['source_sha256']['binary']=='329d56d6b1e7f85c4d3f2e9e4bfe6d7b10e82d8e47c13d39fd4e324beb9ad396'
inputs=gui/'gui.inputs.json';events=gui/'gui.display-events.json'
assert sha(inputs)==check['gui_inputs_sha256']=='3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca'
assert sha(events)=='842e59ed45429998c83112ac1c106023d47d1c5a77e5bf92b74059f83a6fc1a1'
replay=json.loads(inputs.read_bytes());assert replay['end']<=200000000 and len(replay['inputs'])<=96
source=root/'tools/probe_hd_canvas_writes.go'
assert sha(source)=='e111ea99043e3d19d2b63badee41d081dee67025a0d5653b67d07082323f5feb'
s=source.read_text()
def replace(a,b):
 global s
 assert s.count(a)==1,a;s=s.replace(a,b,1)
replace('"path/filepath"','"path/filepath"\n"sort"')
replace('Button int `json:"button"`','Button int `json:"button"`\nText string `json:"text"`')
replace('9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979',sha(inputs))
replace('const end = uint64(75900000)',f'const end = uint64({replay["end"]})')
old='''if b.parameters && m.Steps == 67569117 {
		b.record["parameter_reads"] = hdParameterSnapshot(m, b.retCS, b.retIP)
	}'''
new='''if b.parameters && m.CPU.R[golem.AX] == 33 && m.CPU.R[golem.DX] == 56 {
        at := uint32(m.CPU.Seg[golem.SS])*16 + uint32(b.sp)
        if binary.LittleEndian.Uint16(m.Mem[at+4:at+6]) == 13 {
            reads := hdParameterSnapshot(m, b.retCS, b.retIP)
            words, rec := reads["ds_bx_words"].([]uint16), reads["record_words"].([]uint16)
            if reads["record_first_534_sha256"] == "7c34170632e995ebfb281e451f340d14faec5fa25970ca0479493d99758afb2a" &&
                words[0] == 200 && words[1] == 320 && uint32(words[3])*16+uint32(words[2]) == 0x2cae0 &&
                rec[4] == 23 && rec[5] == 27 {
                b.record["parameter_reads"] = reads
                b.selected = true
                b.record["source_far_pointer"] = reads["record_first_far"]
                b.record["source_encoded_sha256"] = reads["record_first_534_sha256"]
                b.record["source_encoded_length"] = 534
            }
        }
    }'''
replace(old,new)
start=s.index('\tif b.m.Steps != 67569346 || cs != 0xd46 || ip != 0x1d2 {')
end=s.index('\n}\n\nfunc main()',start)
s=s[:start]+'''    if !b.selected { return }
    if _, exists := b.record["writer_step"]; !exists {
        b.record["writer_step"] = b.m.Steps
        b.record["writer_cs_ip"] = fmt.Sprintf("%04X:%04X", cs, ip)
    }'''+s[end:]
replace('''		case "enter":
			d.PushKey(golem.Key{Scan: 0x1c, ASCII: 13})''','''        case "enter", "escape", "backspace":
            name := map[string]string{"enter":"Return","escape":"Escape","backspace":"Backspace"}[e.Kind]
            if !d.PushKeyNamed(name) { panic("缺少已驗原版按鍵") }
        case "text":
            if e.Text != "n" || !d.PushText(e.Text) { panic("正常GUI字元失配") }''')
helper=r'''
type hdGUICheck struct {
    m *golem.Machine
    rows []map[string]any
    at int
    out string
    captured []map[string]any
}
func hdNewGUICheck(m *golem.Machine, out string) *hdGUICheck {
    p := "/out/lifecycle-r29-r1/gui/gui.display-events.json"
    raw := hdRead(p)
    if hdHash(raw) != "EVENT_HASH" { panic("正常GUI事件指紋失配") }
    var events []map[string]any
    hdNeed(json.Unmarshal(raw,&events))
    seen := map[[2]uint64]map[string]any{}
    rows := []map[string]any{}
    keys := []string{"step","memory_sha256","indexed_sha256","palette_sha256","registers","segments","ip","flags","dos_input_count"}
    for _,e := range events {
        key := [2]uint64{uint64(e["step"].(float64)),uint64(e["dos_input_count"].(float64))}
        v := map[string]any{}
        for _,name := range keys { v[name] = e[name] }
        if old,ok := seen[key]; ok {
            a,_ := json.Marshal(old); b,_ := json.Marshal(v)
            if !bytes.Equal(a,b) { panic("同一步數與輸入數有不同GUI狀態") }
        } else { seen[key]=v; rows=append(rows,v) }
    }
    sort.Slice(rows,func(i,j int) bool {
        if rows[i]["step"] == rows[j]["step"] { return rows[i]["dos_input_count"].(float64)<rows[j]["dos_input_count"].(float64) }
        return rows[i]["step"].(float64)<rows[j]["step"].(float64)
    })
    return &hdGUICheck{m:m,rows:rows,out:out}
}
func (g *hdGUICheck) capture(count uint64) {
    if g.at == len(g.rows) { return }
    e := g.rows[g.at]
    step, n := uint64(e["step"].(float64)),uint64(e["dos_input_count"].(float64))
    if g.m.Steps > step || (g.m.Steps == step && count > n) { panic("略過正常GUI檢查點") }
    if g.m.Steps != step || count != n { return }
    m := g.m
    actual := map[string]any{"step":m.Steps,"dos_input_count":count,
        "memory_sha256":hdHash(m.Mem),"indexed_sha256":hdHash(m.Indexed()),"palette_sha256":hdHash(m.DAC[:]),
        "registers":m.CPU.R,"segments":m.CPU.Seg,"ip":m.CPU.IP,"flags":m.CPU.Flags}
    want,_ := json.Marshal(e); got,_ := json.Marshal(actual)
    actual["gui_state_equal"] = bytes.Equal(want,got)
    actual["expected_state"] = e
    prefix := fmt.Sprintf("gui-point-%03d",g.at)
    actual["snapshot_prefix"] = prefix
    hdNeed(os.WriteFile(filepath.Join(g.out,prefix+".idx"),m.Indexed(),0644))
    hdNeed(os.WriteFile(filepath.Join(g.out,prefix+".canvas.idx"),m.Mem[0x2cae0:0x2cae0+64000],0644))
    hdNeed(os.WriteFile(filepath.Join(g.out,prefix+".pal"),m.DAC[:],0644))
    g.captured=append(g.captured,actual)
    g.at++
}
func (g *hdGUICheck) finish(count uint64) {
    g.capture(count)
    if g.at != len(g.rows) { panic("正常GUI檢查點未完成") }
    data,err:=json.MarshalIndent(g.captured,"","  ");hdNeed(err)
    hdNeed(os.WriteFile(filepath.Join(g.out,"gui-points.json"),append(data,'\n'),0644))
}
'''
helper=helper.replace('EVENT_HASH',sha(events))
helper=helper.replace('/out/lifecycle-r29-r1/gui/gui.display-events.json',str(events))
replace('\nfunc main() {','\n'+helper+'\nfunc main() {')
replace('step := func() { boundary.beforeStep(); hdNeed(m.Step()) }','''inputCount := uint64(0)
    guiCheck := hdNewGUICheck(m,*out)
    step := func() { guiCheck.capture(inputCount); boundary.beforeStep(); hdNeed(m.Step()) }''')
replace('''		default:
			panic("本研究收據未支援輸入：" + e.Kind)
		}
	}''','''        default:
            panic("本研究收據未支援輸入：" + e.Kind)
        }
        inputCount++
        guiCheck.capture(inputCount)
    }''')
replace('''		switch e.Kind {''','''		guiCheck.capture(inputCount)
		switch e.Kind {''')
replace('''	if boundary != nil {
		if !boundary.complete {''','''    guiCheck.finish(inputCount)
    if boundary != nil {
        if !boundary.complete {''')

replace('hdNeed(os.WriteFile(filepath.Join(g.out,prefix+".pal"),m.DAC[:],0644))',
        'hdNeed(os.WriteFile(filepath.Join(g.out,prefix+".pal"),m.DAC[:],0644))\n    hdNeed(os.WriteFile(filepath.Join(g.out,prefix+".vga-tail.idx"),m.Mem[0xafa00:0xafe00],0644))')
replace('previous := uint64(0)', "var cursorEvents [][6]uint64\n var cursorSourceGroups []map[string]any\n cursorSites := map[string]uint64{}\n cursorSamples := map[string][]map[string]any{}\n if !*control {\n m.WatchWrite(0xafb00, 0xafbff, func(_ *golem.Machine, addr uint32, old, value uint8) {\n  if len(cursorEvents) >= 2000000 { panic(\"游標研究事件超出界限\") }\n  cs, ip := m.CPU.OpAddr()\n  cursorEvents = append(cursorEvents, [6]uint64{m.Steps,uint64(cs),uint64(ip),uint64(addr),uint64(old),uint64(value)})\n  site := fmt.Sprintf(\"%04X:%04X\",cs,ip)\n  cursorSites[site]++\n  if addr == 0xafb00 {\n   pc := uint32(cs)*16+uint32(ip)\n   sa := uint32(m.CPU.Seg[golem.DS])*16+uint32(m.CPU.R[golem.SI])-1\n   if sa+256>uint32(len(m.Mem)) || pc<64 || pc+16>uint32(len(m.Mem)) { panic(\"游標觀測範圍越界\") }\n   cursorSourceGroups=append(cursorSourceGroups,map[string]any{\"step\":m.Steps,\"source_linear\":sa,\"source_sha256\":hdHash(m.Mem[sa:sa+256]),\"source_hex\":fmt.Sprintf(\"%x\",m.Mem[sa:sa+256]),\"code_before_64_hex\":fmt.Sprintf(\"%x\",m.Mem[pc-64:pc+16])})\n  }\n  if cursorSites[site] <= 4 {\n   pc:=uint32(cs)*16+uint32(ip)\n   cursorSamples[site]=append(cursorSamples[site],map[string]any{\"step\":m.Steps,\"registers\":m.CPU.R,\"segments\":m.CPU.Seg,\"code_hex\":fmt.Sprintf(\"%x\",m.Mem[pc:pc+16])})\n  }\n })\n }\n previous := uint64(0)")
replace('guiCheck.finish(inputCount)', '''guiCheck.finish(inputCount)
 cursorData, cursorErr := json.MarshalIndent(map[string]any{"events":cursorEvents,"sites":cursorSites,"samples":cursorSamples,"source_groups":cursorSourceGroups},"","  ")
 hdNeed(cursorErr)
 hdNeed(os.WriteFile(filepath.Join(*out,"cursor-writes.json"),append(cursorData,'\\n'),0644))''')
dest.mkdir();module=dest/'module';module.mkdir()
base=root/'workplace/reports/goal186-display-hd/language-resources-20261011/map-source-padding-r27/formal-runtime'
for name in ['go.mod','go.sum','go.work']:shutil.copyfile(base/name,module/name)
(module/'main.go').write_text(s)
subprocess.run(['gofmt','-w',str(module/'main.go')],check=True,timeout=30)
binary=dest/'lifecycle-probe'
subprocess.run(['go','build','-trimpath','-o',str(binary),'.'],cwd=module,check=True,timeout=120)
subprocess.run(['go','vet','.'],cwd=module,check=True,timeout=120)
meta={'kind':'private-normal-gui-building-lifecycle-observation','base_source_sha256':sha(source),
 'generated_source_sha256':sha(module/'main.go'),'binary_sha256':sha(binary),
 'gui_check_sha256':sha(gui/'check.json'),'gui_inputs_sha256':sha(inputs),'gui_events_sha256':sha(events),
 'inputs':len(replay['inputs']),'end':replay['end']}
(dest/'build.json').write_text(json.dumps(meta,indent=2)+'\n')
common=[str(binary),'--root',str(args.game_root.resolve()),'--seed',str(root/'workplace/reports/goal186-display-hd/language-resources-20261011/formal-save-gui-r25/save/COLONY09.SAV'),'--inputs',str(inputs)]
for name,extra in [('observed',['--draw-query',str(args.draw_query.resolve()),'--draw-parameters','--draw-write-stream']),('control',['--control'])]:
 with (dest/(name+'.log')).open('wb') as log:subprocess.run(common+['--out',str(dest/name)]+extra,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=240)
 print('LIFECYCLE_REPLAY_DONE',name,flush=True)
