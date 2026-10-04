#!/usr/bin/env python3
"""Docker內量測正常BUY欄位；壓力數值是排版條件，不是原版價格上限。"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path


def capital_component(raw, top, bottom):
    points = {(x, y) for y in range(top, bottom) for x in range(80, 105)
              if raw[y * 320 + x] in (68, 149)}
    first = min(points, key=lambda point: (point[1], point[0]))
    seen, todo = {first}, [first]
    while todo:
        x, y = todo.pop()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                point = (x + dx, y + dy)
                if point in points and point not in seen:
                    seen.add(point)
                    todo.append(point)
    return [min(x for x, y in seen), min(y for x, y in seen),
            max(x for x, y in seen) + 1, max(y for x, y in seen) + 1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--resume', action='store_true', help='環境失敗後驗證原始組裝未變再重跑')
    parser.add_argument('--payable', action='store_true', help='量測正常貨車可支付正文的專屬安全區')
    args = parser.parse_args()
    root = args.reports
    assert root.stat().st_uid == os.getuid() and root.stat().st_gid == os.getgid()
    report = json.loads((root / 'gui-colony.json').read_text())
    key = 'GAME.TXT:@BUYME1:0x00002F09'
    events = [e for e in report['events'] if e.get('candidate_id') == key and e.get('stage') == 'source']
    safe = [80, 102, 220, 135] if args.payable else [80, 119, 228, 142]
    assert len(events) == 1 and events[0]['safe'] == safe
    if args.payable:
        assert events[0]['shown'] == 'Cost to complete Wagon Train: 481$. Treasury: 1000$.'
    raw = (root / 'gui-colony.final.idx').read_bytes()
    assert len(raw) == 64000
    # 原版第一行第一個大寫字母的獨立墨跡，排除小寫下伸部與陰影。
    bbox = capital_component(raw, 102 if args.payable else 119, 112 if args.payable else 131)
    assert bbox == ([82, 104, 86, 111] if args.payable else [82, 121, 86, 128])
    bbox2 = capital_component(raw, 124 if args.payable else 130, 134 if args.payable else 141)
    assert bbox2 == ([82, 124, 85, 131] if args.payable else [82, 131, 85, 138])
    work = root / 'measure-build'
    assert args.resume or not work.exists()
    work.mkdir(exist_ok=args.resume)
    assert work.stat().st_uid == os.getuid() and work.stat().st_gid == os.getgid()
    source = Path('/repo/workplace/reports/goal180-pedia-rest/sync-final-build')
    for path in source.iterdir():
        if path.suffix == '.go' or path.name in ('go.mod', 'go.sum', 'go.work'):
            target = work / path.name
            if args.resume:
                assert target.read_bytes() == path.read_bytes()
            else:
                shutil.copyfile(path, target)
    cases_path = root / 'buy-layout-source.json'
    cases_path.write_text(json.dumps(dict(events[0], price='481' if args.payable else '1352'), ensure_ascii=False, indent=2) + '\n')
    helper = work / 'zz_goal181_measure_test.go'
    helper.write_text(r'''package main
import ("encoding/json"; "image"; "os"; "strings"; "testing")
func TestGoal181BuyLayout(t *testing.T) {
  read:=func(p string) []byte {b,e:=os.ReadFile(p);if e!=nil {t.Fatal(e)};return b}
  c,e:=loadDialogCatalog(read("/repo/text/corpus.zh-Hant.tsv"),read("/repo/text/terms.zh-Hant.tsv"),read("/game/GAME.TXT"),"67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a",nil);if e!=nil {t.Fatal(e)}
  atlas:=read("/repo/workplace/reports/goal180-pedia-rest/formatted-dialog-atlas/dialog-atlas.json")
  var h struct {Font string `json:"font_sha256"`; Bind map[string]string `json:"bindings"`}
  if e=json.Unmarshal(atlas,&h);e!=nil {t.Fatal(e)}
  if why:=c.loadDialogAtlas(atlas,h.Font,h.Bind);why!="" {t.Fatal(why)}
  var source struct {Shown string `json:"shown"`; Safe [4]int `json:"safe"`; Price string `json:"price"`}
  if e=json.Unmarshal(read(os.Getenv("GOAL181_LAYOUT_SOURCE")),&source);e!=nil {t.Fatal(e)}
  id,zh,why:=c.match(source.Shown);if why!="" || id!="GAME.TXT:@BUYME1:0x00002F09" {t.Fatal(id,why)}
  template,_,why:=c.matchIn(c.templates,source.Shown);if why!="" || !template.centered {t.Fatal("實際模板未走置中段落",why)}
  stress:=strings.ReplaceAll(strings.ReplaceAll(source.Shown,source.Price,strings.Repeat("9",27)),"1000",strings.Repeat("9",27))
  _,long,why:=c.match(stress);if why!="" {t.Fatal(why)}
  cases:=[]struct {Name,Text string; Fits bool}{{"observed",zh,true},{"27-digit-layout-stress",long,true},{"overflow-fallback",strings.Repeat(zh+"\n",40),false}}
  result:=[]map[string]any{}
  layoutWidth,layoutHeight:=(source.Safe[2]-source.Safe[0])*4,(source.Safe[3]-source.Safe[1])*4
  for _,test:=range cases {
    sh,n,a,px:=c.centeredMasks(test.Text,layoutWidth,layoutHeight,40,true)
    if (px!=0)!=test.Fits {t.Fatal(test.Name,px)}
    var ink image.Rectangle
    if px!=0 {
      if px<20 || px>30 {t.Fatal(test.Name,px)}
      for _,m:=range []*image.Alpha{sh,n,a} {if m!=nil {for y:=0;y<m.Rect.Dy();y++ {for x:=0;x<m.Rect.Dx();x++ {if m.AlphaAt(x,y).A!=0 {ink=ink.Union(image.Rect(x,y,x+1,y+1))}}}}}
      if !ink.In(image.Rect(0,0,layoutWidth,layoutHeight)) {t.Fatal("超出安全區",ink)}
    }
    result=append(result,map[string]any{"case":test.Name,"selected_px":px,"fits":px!=0,"ink":[4]int{ink.Min.X,ink.Min.Y,ink.Max.X,ink.Max.Y}})
  }
  b,_:=json.MarshalIndent(result,"","  ");if e=os.WriteFile(os.Getenv("GOAL181_LAYOUT_MEASUREMENTS"),b,0644);e!=nil {t.Fatal(e)}
}
''')
    env = dict(os.environ, GOPROXY='off', GOTOOLCHAIN='local',
               GOAL181_LAYOUT_SOURCE=str(cases_path),
               GOAL181_LAYOUT_MEASUREMENTS=str(root / 'buy-layout-measurements.json'))
    xvfb = None
    try:
        if not env.get('DISPLAY'):
            env.update(DISPLAY=':99', LIBGL_ALWAYS_SOFTWARE='1')
            xvfb = subprocess.Popen(['Xvfb', ':99', '-screen', '0', '1280x800x24', '-nolisten', 'tcp'],
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            deadline = time.monotonic() + 10
            while not Path('/tmp/.X11-unix/X99').exists():
                assert xvfb.poll() is None and time.monotonic() < deadline
                time.sleep(0.02)
        subprocess.run(['/usr/local/go/bin/go', 'test', '-mod=readonly', '-run', '^TestGoal181BuyLayout$',
                        '-count=1', '-v', '.'], cwd=work, env=env, check=True)
    finally:
        if xvfb is not None and xvfb.poll() is None:
            xvfb.terminate()
            try:
                xvfb.wait(timeout=5)
            except subprocess.TimeoutExpired:
                xvfb.kill()
                xvfb.wait(timeout=5)
    metadata = {'key': key, 'original_capital_ink': [bbox, bbox2], 'original_cap_height': 7,
                'template_layout': 'centered',
                'original_baselines': [110, 120, 130] if args.payable else [127, 137], 'original_pitch': 10,
                'safe': events[0]['safe'], 'candidate_px': list(range(30, 19, -1)),
                'scope': ('可支付貨車' if args.payable else '資金不足碼頭') + '正文；27位數為排版壓力條件，非原版價格上限；選項另驗',
                'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (root / 'buy-layout-metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(metadata, ensure_ascii=False))


if __name__ == '__main__':
    main()
