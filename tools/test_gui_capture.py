from pathlib import Path
import hashlib,json,tempfile,sys
from PIL import Image
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent));import gui_auto as capture

with tempfile.TemporaryDirectory() as tmp:
    proc=Path(tmp)/'123';proc.mkdir();(proc/'exe').symlink_to('/verified/colonization-window')
    task=proc/'task';task.mkdir()
    for tid in ('123','456'):
        thread=task/tid;thread.mkdir();(thread/'status').write_text('State:\tT (stopped)\n')
    real_path=Path
    with patch.object(capture,'Path',lambda value:real_path(tmp) if value=='/proc' else real_path(value)),patch.object(capture.os,'kill') as send:
        capture._validate_capture_pid(123)
        capture._freeze(123)
        capture._resume(123)
        assert [c.args for c in send.call_args_list]==[(123,capture.signal.SIGSTOP),(123,capture.signal.SIGCONT)]

with tempfile.TemporaryDirectory() as tmp:
    out=str(Path(tmp)/'fake'); expected=Image.new('RGBA',(2,2),(20,60,90,255)); wrong=Image.new('RGBA',(2,2),(90,30,20,255))
    digest=hashlib.sha256(expected.tobytes()).hexdigest()
    meta={'step':200000,'frame':{'step':165000},'canvas_rgba_sha256':digest,'canvas_size':[2,2]}
    capture.status=lambda _:meta
    actions=[];capture._validate_capture_pid=lambda p:None;capture._freeze=lambda p:actions.append('stop');capture._resume=lambda p:actions.append('continue')
    images=iter([wrong,expected]);capture._grab=lambda _,target:next(images).save(target)
    capture.capture_frame_synced(out,'fake','delayed',123)
    receipts=[json.loads(l) for l in Path(out+'.capture-attempts.jsonl').read_text().splitlines()]
    assert [x['aligned'] for x in receipts]==[False,True] and all(x['stable'] for x in receipts)
    assert Path(out+'.delayed.attempt-0.png').exists() and Path(out+'.delayed.png').exists()
    assert Path(out+'.shots').read_text()=='delayed 165000\n' and actions==['stop','continue','stop','continue']
    # 穩定標記也不能讓永久錯圖或缺指紋建立收據。
    capture._grab=lambda _,target:wrong.save(target)
    try:capture.capture_frame_synced(out,'fake','wrong',123)
    except RuntimeError:pass
    else:raise AssertionError('永久錯圖被接受')
    assert not Path(out+'.wrong.png').exists() and 'wrong' not in Path(out+'.shots').read_text()
    del meta['canvas_rgba_sha256']
    try:capture.capture_frame_synced(out,'fake','unbound',123)
    except RuntimeError:pass
    else:raise AssertionError('缺指紋仍建立收據')
    assert actions[-1]=='continue'
    # PID驗證失敗時，不得向未授權程序送出恢復訊號。
    before=len(actions)
    def invalid_pid(pid):raise RuntimeError('非指定程序')
    capture._validate_capture_pid=invalid_pid
    try:capture.capture_frame_synced(out,'fake','unauthorized',123)
    except RuntimeError:pass
    else:raise AssertionError('非指定程序仍被接受')
    assert len(actions)==before
print('PASS：穩定舊圖拒絕、正確呈現接受、永久錯圖及缺指紋拒絕、指定程序必恢復')
