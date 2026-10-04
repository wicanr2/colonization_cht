#!/usr/bin/env python3
"""Docker/Xvfb 用：以單調時鐘讀音訊，僅修改隔離來源副本。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

HELPER = r'''package main

import (
    "encoding/binary"
    "encoding/json"
    "os"
    "time"
)

type audioClockProbe struct {
    stop chan struct{}
    done chan struct{}
    pcm []byte
    seconds float64
    calls uint64
    maxLateSeconds float64
}

func startAudioClockProbe(a *frontendAudio) {
    p := &audioClockProbe{stop: make(chan struct{}), done: make(chan struct{})}
    a.clockProbe = p
    go func() {
        defer close(p.done)
        ticker := time.NewTicker(10 * time.Millisecond)
        defer ticker.Stop()
        start := time.Now()
        var frames int64
        pull := func() {
            elapsed := time.Since(start)
            target := int64(elapsed) * audioPlayRate / int64(time.Second)
            target -= target % (audioPlayRate / 100)
            missing := target - frames
            if missing <= 0 { return }
            if late := float64(missing) / audioPlayRate - 0.01; late > p.maxLateSeconds { p.maxLateSeconds = late }
            buf := make([]byte, missing * 4)
            a.stream.Read(buf)
            p.pcm = append(p.pcm, buf...)
            frames = target
            p.calls++
        }
        for {
            select {
            case <-ticker.C: pull()
            case <-p.stop:
                pull()
                p.seconds = time.Since(start).Seconds()
                return
            }
        }
    }()
}

func stopAudioClockProbe(a *frontendAudio) {
    p := a.clockProbe
    if p == nil { return }
    close(p.stop)
    <-p.done
    a.clockProbe = nil
    if *audioWAVPath == "" { return }
    data := make([]byte, 44 + len(p.pcm))
    copy(data, "RIFF")
    binary.LittleEndian.PutUint32(data[4:], uint32(36 + len(p.pcm)))
    copy(data[8:], "WAVEfmt ")
    binary.LittleEndian.PutUint32(data[16:], 16)
    binary.LittleEndian.PutUint16(data[20:], 1)
    binary.LittleEndian.PutUint16(data[22:], 2)
    binary.LittleEndian.PutUint32(data[24:], audioPlayRate)
    binary.LittleEndian.PutUint32(data[28:], audioPlayRate * 4)
    binary.LittleEndian.PutUint16(data[32:], 4)
    binary.LittleEndian.PutUint16(data[34:], 16)
    copy(data[36:], "data")
    binary.LittleEndian.PutUint32(data[40:], uint32(len(p.pcm)))
    copy(data[44:], p.pcm)
    must(os.WriteFile(*audioWAVPath + ".playback.wav", data, 0644))
    a.stream.mu.Lock()
    rec := map[string]any{
        "wall_seconds": p.seconds,
        "read_calls": p.calls,
        "max_reader_lateness_seconds": p.maxLateSeconds,
        "source_rate": a.rate,
        "source_frames": a.stream.srcBase,
        "read_bytes": a.stream.ReadBytes,
        "underrun_bytes": a.stream.UnderrunBytes,
        "dropped_bytes": a.stream.Dropped,
        "output_rate": audioPlayRate,
        "hardware_verified": false,
        "method": "10ms monotonic-clock reads; missed ticks caught up by elapsed time; no simulation feedback",
    }
    a.stream.mu.Unlock()
    b, err := json.MarshalIndent(rec, "", "  "); must(err)
    must(os.WriteFile(*audioWAVPath + ".clock.json", append(b, '\n'), 0644))
}
'''

p = argparse.ArgumentParser()
p.add_argument('--source', type=Path, required=True)
p.add_argument('--inputs', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert a.source.is_dir() and a.inputs.is_file()
assert not a.output.exists() and a.output.parent.stat().st_uid == os.getuid()
a.output.mkdir()
src = a.output / 'source'
shutil.copytree(a.source, src)
f = src / 'window.go'
t = f.read_text()
assert 'clockProbe' not in t
old = 'type frontendAudio struct {'
assert t.count(old) == 1
t = t.replace(old, old + '\n clockProbe *audioClockProbe')
old = 'a := &frontendAudio{rate: m.AudioRate(), stream: &audioStream{rate: uint64(m.AudioRate())}}'
assert t.count(old) == 1
t = t.replace(old, old + '\n startAudioClockProbe(a)')
old = 'func (a *frontendAudio) writeWAV() {'
assert t.count(old) == 1
t = t.replace(old, old + '\n if a != nil { stopAudioClockProbe(a) }')
f.write_text(t)
(src / 'audio_clock_probe.go').write_text(HELPER)
subprocess.run(['gofmt', '-w', 'window.go', 'audio_clock_probe.go'], cwd=src, check=True)
subprocess.run(['go', 'build', '-o', str(a.output / 'probe-window'), '.'], cwd=src, check=True, timeout=150)
subprocess.run(['python3', '/repo/tools/replay_linux_checks.py', '--binary', str(a.output / 'probe-window'), '--inputs', str(a.inputs), '--output', str(a.output / 'run')], check=True, timeout=450)
print((a.output / 'run' / 'original.wav.clock.json').read_text())
