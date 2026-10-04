#!/usr/bin/env bash
# Docker內：以當前Linux前端重播Windows正常GUI輸入，檢查跨平台原版終點。
set -euo pipefail
base=/repo/workplace/reports/goal182-platform-preflight
gui=${1:-$base/windows-gui-v2}
out=$base/linux-$(basename "$gui")
[[ -f "$gui.json" && -f "$gui.inputs.json" && -f /game/OPENING.EXE ]]
[[ $(stat -c %u "$base") == $(id -u) && $(stat -c %g "$base") == $(id -g) && ! -e "$out.json" ]]
export DISPLAY=:99 LIBGL_ALWAYS_SOFTWARE=1
Xvfb :99 -screen 0 1280x800x24 -nolisten tcp >/tmp/colonization-cross-platform-xvfb.log 2>&1 &
xp=$!
trap 'kill "$xp" 2>/dev/null || true; wait "$xp" 2>/dev/null || true' EXIT
python3 - "$base" "$out" "$gui" <<'PY'
from pathlib import Path
import json, subprocess, sys
base,out,gui=map(Path,sys.argv[1:])
args=json.loads(Path(str(gui)+'.arguments.json').read_text())
assert args[0]=='wine' and args[1].endswith('/colonization-window.exe')
args=[str(Path('/repo/workplace/reports/goal180-pedia-rest/sync-final-build/colonization-window'))]+[
    token[2:] if token.startswith('Z:/') else token for token in args[2:]]
args[args.index('--out')+1]=str(out)
args.extend(['--replay-inputs',str(gui)+'.inputs.json'])
Path(str(out)+'.arguments.json').write_text(json.dumps(args,ensure_ascii=False,indent=2)+'\n')
with Path(str(out)+'.log').open('w') as log:
    subprocess.run(args,stdout=log,stderr=subprocess.STDOUT,check=True)
win=json.loads(Path(str(gui)+'.json').read_text())
linux=json.loads(Path(str(out)+'.json').read_text())
assert win['state']['steps']==linux['state']['steps']==50000000
assert win['state']==linux['state'] and win['input_hashes']==linux['input_hashes']
# 開檔觀測記錄使用宿主回傳的檔名大小寫；保留原清單，另按DOS檔名規則比較。
assert all(name.isascii() and not any(ch in name for ch in '/\\:') for name in win['opened']+linux['opened'])
assert [name.upper() for name in win['opened']]==[name.upper() for name in linux['opened']]
opened_case_differences=[{'index':i,'windows':a,'linux':b} for i,(a,b) in enumerate(zip(win['opened'],linux['opened'])) if a!=b]
for ext in ('memory','final.idx','final.pal'):
    assert Path(str(gui)+'.'+ext).read_bytes()==Path(str(out)+'.'+ext).read_bytes(),ext
for item in (win,linux):
    assert not item['dialog_reason'] and not item['string_reason']
    final=next(c for c in item['checkpoints'] if c['label']=='final')
    keys={x['candidate_id'] for x in final['lines'] if x['applied']}
    assert {'GAME.TXT:0x000001B0','GAME.TXT:0x000001CB','GAME.TXT:0x000001E4',
            'GAME.TXT:0x000001F9','GAME.TXT:0x00000204','GAME.TXT:0x00000179'}<=keys
import hashlib
result={'result':'PASS_WINDOWS_WINE_MENU', 'steps':50000000,
        'inputs_sha256':hashlib.sha256(Path(str(gui)+'.inputs.json').read_bytes()).hexdigest(),
        'state':win['state'],'same_full_memory':True,'same_original_index_palette':True,
        'opened_case_differences':opened_case_differences,'same_raw_opened':win['opened']==linux['opened'],
        'scope':'完整旗標載入與正常主選單；Windows原生與後續玩家路徑尚未驗收'}
from PIL import Image, ImageChops
image=Image.open(str(gui)+'.main-menu.png').convert('RGB')
composed=Image.open(str(out)+'.final.png').convert('RGB')
assert image.size==composed.size==(1280,800)
safe=(320,356,968,584)
assert ImageChops.difference(image.crop(safe),composed.crop(safe)).getbbox() is None
result['gui_safe']=list(safe)
result['same_gui_menu_pixels']=True
Path(str(gui)+'.linux-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(result,ensure_ascii=False))
PY
