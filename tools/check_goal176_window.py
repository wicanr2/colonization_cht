#!/usr/bin/env python3
"""目標176（Issue #49，規格040）：獨立核對前端音訊；原版缺失回 SKIP 77。

- 開關音訊不影響原版：重播 A（數位音效＋音訊）與 B（只開數位音效）、C（只開音訊）與 D（都不開），
  終點狀態、檢查點、完整記憶體與截圖逐位元組相同。
- 真 GUI 錄下的 WAV 與同輸入重播 A 的 WAV 逐位元組相同。
- A 在開場、海上、建城木刻三段的 RMS 明顯高於靜音；建城木刻那段 A 高於沒有數位音效的 C。
- 真 GUI 的播放器存在、有被讀取、沒有錯誤。
"""

import argparse
import hashlib
import json
import struct
import wave
from pathlib import Path

from check_goal134_window import load

STEPS_PER_SECOND = 165000 * (315e6 / 264) / 17000
# 區段（指令數）：開場字幕、海上航行、建城木刻畫面（規格039 取證：約 9.52 億步起播放約 5.5 秒）。
WINDOWS = {"opening": (100e6, 300e6), "sea": (560e6, 620e6), "woodcut": (955e6, 1010e6)}


def need(ok, reason):
    if not ok:
        raise ValueError(reason)


def rms(path, t0, t1):
    with wave.open(str(path)) as w:
        rate = w.getframerate()
        w.setpos(int(t0 / STEPS_PER_SECOND * rate))
        n = int((t1 - t0) / STEPS_PER_SECOND * rate)
        raw = w.readframes(n)
    s = struct.unpack("<%dh" % (len(raw) // 2), raw)
    return (sum(x * x for x in s) / max(1, len(s))) ** 0.5


def pair(r, a, b, label):
    x, y = load(r / a), load(r / b)
    need(x[0]["state"] == y[0]["state"] and x[1] == y[1] and x[2].tobytes() == y[2].tobytes(),
         f"{label}：原版狀態、記憶體或最終畫面不同")
    ca = {c["label"]: c.get("memory_sha256") for c in x[0]["checkpoints"]}
    cb = {c["label"]: c.get("memory_sha256") for c in y[0]["checkpoints"]}
    need(ca == cb and len(ca) > 0, f"{label}：檢查點不同")
    for c in x[0]["checkpoints"]:
        if not c["label"].startswith("cp-"):
            continue
        step = c["label"][3:]
        pa, pb = r / f"{a}.cp-{step}.png", r / f"{b}.cp-{step}.png"
        if pa.is_file():
            need(pa.read_bytes() == pb.read_bytes(), f"{label}：{c['label']} 截圖不同")
    return x[0]["state"]["memory_sha256"], len(ca)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game", type=Path, required=True)
    p.add_argument("--reports", type=Path, required=True)
    a = p.parse_args()
    if not (a.game / "OPENING.EXE").is_file():
        print("SKIP：缺合法原版，未宣稱前端音訊通過")
        return 77
    r = a.reports
    raw = (r / "gui-audio.inputs.json").read_bytes()
    need(not json.loads(raw).get("rejected"), "現場輸入有被拒絕")
    sab, nab = pair(r, "replay-a", "replay-b", "數位音效開音訊／不開")
    scd, ncd = pair(r, "replay-c", "replay-d", "預設設定開音訊／不開")

    gui_wav, a_wav = (r / "gui-audio.wav").read_bytes(), (r / "replay-a.wav").read_bytes()
    need(gui_wav == a_wav, "真 GUI 與重播的 WAV 不同")
    levels = {k: round(rms(r / "replay-a.wav", *w)) for k, w in WINDOWS.items()}
    need(all(v > 300 for v in levels.values()), f"區段音量過低：{levels}")
    wood_c = round(rms(r / "replay-c.wav", *WINDOWS["woodcut"]))
    need(levels["woodcut"] > wood_c * 1.5, f"建城木刻的數位音效不明顯：A {levels['woodcut']}、C {wood_c}")

    st = json.loads((r / "gui-audio.status.json").read_text()).get("audio") or {}
    need(st.get("player") and st.get("played_bytes", 0) > 0 and not st.get("error"), f"播放器狀態不符：{st}")
    print(json.dumps({"result": "PASS", "inputs_sha256": hashlib.sha256(raw).hexdigest(),
                      "wav_sha256": hashlib.sha256(gui_wav).hexdigest(), "wav_bytes": len(gui_wav),
                      "rms": levels, "woodcut_without_digital": wood_c, "checkpoints": [nab, ncd],
                      "final_state_sha256": {"digital": sab, "default": scd}, "player": st}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
