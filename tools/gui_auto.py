#!/usr/bin/env python3
"""目標167：真 GUI 自動應答。只在有界 Docker/Xvfb 內、由 probe 腳本呼叫。

依前端狀態檔（$out.status.json）的畫面資訊行動，不依固定步數：
- 最近一段像訊息框的印字（dialog_seq 增加）印完後隔 --delay 步，依文字片段選按鍵應答（未列者按 Return），
  應答前先截圖並把名稱與步數寫入 $out.shots；--after 大於 0 時，應答後隔這麼多步且沒有新訊息框，再截一張 after-N（目標169）；
- 沒有待應答的訊息框、且距上次輸入已過 --idle 步時，依序送出 --intents 的意圖鍵；
  意圖寫成 click:XxY（輸出座標 1280×800，例如 click:1190x374）時改為移動滑鼠並按左鍵，move:XxY 只移動滑鼠，wait 不送任何輸入、只佔一個閒置間隔（目標170）。
每個按鍵都以 xdotool 真按，並等前端讀到（狀態步數前進兩次 Update）才放開，與 tools/gui_step_input.sh 相同。
"""

import argparse
import hashlib
import signal
from pathlib import Path
from PIL import Image
import json
import os
import subprocess
import time

UPDATE = 200000
HOLD = 600000


def status(path):
    for _ in range(50):
        try:
            with open(path) as f:
                return json.load(f)
        except (OSError, ValueError):
            time.sleep(0.02)
    raise RuntimeError("讀不到狀態檔")


def capture_frame(out, window, name):
    """量測實際生成畫面的步數；擷取跨畫面時保留嘗試，不以像素結果挑圖。"""
    path = out + ".status.json"
    for attempt in range(8):
        before = status(path)
        s = (before.get("frame") or {}).get("step")
        if not isinstance(s, int) or s <= 0:
            raise RuntimeError("缺少原版畫面步數，不能建立 GUI 擷取收據")
        target = f"{out}.{name}.attempt-{attempt}.png"
        subprocess.run(["import", "-window", window, target], check=True)
        after = status(path)
        stable = s == (after.get("frame") or {}).get("step")
        with open(out + ".capture-attempts.jsonl", "a") as f:
            f.write(json.dumps({"name": name, "attempt": attempt, "frame_step": s,
                                "update_step": before["step"], "stable": stable}) + "\n")
        if stable:
            os.replace(target, f"{out}.{name}.png")
            with open(out + ".shots", "a") as f:
                f.write(f"{name} {s}\n")
            return
        time.sleep(0.02)
    raise RuntimeError("GUI 擷取期間畫面持續前進，未建立未對齊的收據")


def _validate_capture_pid(pid):
    proc=Path('/proc')/str(pid)
    if proc.stat().st_uid!=os.getuid() or (proc/'exe').readlink().name!='colonization-window':
        raise RuntimeError('非本使用者的指定遊戲程序')

def _freeze(pid):
    proc=Path('/proc')/str(pid)
    os.kill(pid,signal.SIGSTOP)
    deadline=time.monotonic()+2
    while True:
        states=[(p/'status').read_text().split('State:',1)[1].splitlines()[0].strip()[0] for p in (proc/'task').iterdir()]
        if states and all(s=='T' for s in states):return
        if time.monotonic()>=deadline:raise RuntimeError('指定遊戲執行緒未全部停止')
        time.sleep(.01)

def _resume(pid):os.kill(pid,signal.SIGCONT)
def _grab(window,target):subprocess.run(['import','-window',str(window),str(target)],check=True)

def capture_frame_synced(out,window,name,pid):
    _validate_capture_pid(pid)
    path=out+'.status.json'
    for attempt in range(32):
        try:
            _freeze(pid)
            before=status(path); frame_step=(before.get('frame') or {}).get('step')
            expected=before.get('canvas_rgba_sha256'); size=before.get('canvas_size')
            if not isinstance(frame_step,int) or frame_step<=0 or not isinstance(expected,str) or len(expected)!=64 or not isinstance(size,list) or len(size)!=2:
                raise RuntimeError('缺少畫面步數或畫布指紋，不建立收據')
            target=Path(f'{out}.{name}.attempt-{attempt}.png')
            _grab(window,target)
            with Image.open(target) as im:
                actual_size=list(im.size); actual=hashlib.sha256(im.convert('RGBA').tobytes()).hexdigest()
            after=status(path)
            stable=frame_step==(after.get('frame') or {}).get('step') and expected==after.get('canvas_rgba_sha256')
            aligned=stable and actual==expected and actual_size==size
            receipt={'name':name,'attempt':attempt,'frame_step':frame_step,'update_step':before['step'],'stable':stable,'canvas_rgba_sha256':expected,'capture_rgba_sha256':actual,'canvas_size':size,'capture_size':actual_size,'aligned':aligned}
            with open(out+'.capture-attempts.jsonl','a') as f:f.write(json.dumps(receipt)+'\n')
            if aligned:
                os.replace(target,f'{out}.{name}.png')
                with open(out+'.shots','a') as f:f.write(f'{name} {frame_step}\n')
                return
        finally:
            _resume(pid)
        # 只讓指定前端完成下一次呈現；不送任何原版輸入。
        time.sleep(.05)
    raise RuntimeError('32次有界取樣均未與發布畫布對齊，保留所有失敗嘗試')

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", required=True)
    p.add_argument("--window", required=True)
    p.add_argument("--pid", type=int, required=True)
    p.add_argument("--intents", default="")
    p.add_argument("--answers", default="")
    p.add_argument("--idle", type=int, default=15000000)
    p.add_argument("--delay", type=int, default=4000000)
    p.add_argument("--start", type=int, required=True, help="意圖鍵最早送出的步數")
    p.add_argument("--end", type=int, required=True)
    p.add_argument("--after", type=int, default=0)
    p.add_argument("--intent-shots-from", type=int, default=0,
                   help="目標170：大於 0 時，此步數之後每個意圖送出前截一張 intent-N（拍到上一個意圖造成的畫面）")
    a = p.parse_args()
    path = a.out + ".status.json"
    intents = [k for k in a.intents.split(",") if k]
    answers = [x.split("=", 1) for x in a.answers.split(";") if "=" in x]

    def step():
        return status(path)["step"]

    def alive():
        try:
            os.kill(a.pid, 0)
            return True
        except OSError:
            return False

    def wait_until(target):
        while step() < target:
            if not alive():
                raise SystemExit("前端已結束")
            time.sleep(0.05)

    def act(args, need):
        s0 = step()
        subprocess.run(["xdotool"] + args, check=True)
        wait_until(s0 + need)

    def key(name):
        # 按住至少兩個畫格，放開後再等兩次 Update 確定讀到。
        act(["keydown", name], HOLD)
        act(["keyup", name], 2 * UPDATE)

    def click(x, y):
        act(["mousemove", "--window", a.window, str(x), str(y)], 2 * UPDATE)
        act(["mousedown", "1"], HOLD)
        act(["mouseup", "1"], 2 * UPDATE)

    def shot(name):
        capture_frame_synced(a.out, a.window, name, a.pid)

    seen, pending, pending_at, text, last_input, n, after_due = 0, False, 0, "", step(), 0, 0
    while alive():
        st = status(path)
        now = st["step"]
        if now >= a.end:
            break
        dlg = st.get("dialog") or {}
        if dlg.get("dialog_seq", 0) > seen:
            seen = dlg["dialog_seq"]
            # 目標170：少於三個英文字母的印字（例如港口畫面的數字）不是訊息框，不等待應答。
            if sum(ch.isalpha() for ch in dlg.get("dialog_text", "")) >= 3:
                pending, pending_at = True, dlg["dialog_step"]
                text += dlg.get("dialog_text", "") + " "
        if pending and now - pending_at >= a.delay:
            keys = ["Return"]
            for frag, ks in answers:
                if frag in text:
                    keys = ks.split("+")
            n += 1
            shot(f"answer-{n}")
            print(f"應答 {now}：{text!r} → {keys}", flush=True)
            for k in keys:
                if k != "none":  # 目標171：none 表示不按鍵（例如下拉選單，交給下一個點擊意圖）
                    key(k)
            pending, text, last_input = False, "", step()
            after_due = last_input + a.after if a.after > 0 else 0
        elif after_due and not pending and now >= after_due:
            shot(f"after-{n}")
            after_due = 0
        elif not pending and now >= a.start and now - last_input >= a.idle and intents:
            k = intents.pop(0)
            if a.intent_shots_from and now >= a.intent_shots_from:
                n += 1
                shot(f"intent-{n}")
            print(f"意圖 {now}：{k}", flush=True)
            if k == "wait":
                pass
            elif k.startswith("click:"):
                x, y = k[6:].split("x")
                click(int(x), int(y))
            elif k.startswith("move:"):
                x, y = k[5:].split("x")
                act(["mousemove", "--window", a.window, x, y], 2 * UPDATE)
            else:
                key(k)
            last_input = step()
        else:
            time.sleep(0.05)
    shot("final")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
