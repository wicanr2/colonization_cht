#!/usr/bin/env python3
"""Docker內製作90秒原版畫面剪輯。prepare需Pillow，encode/check需FFmpeg。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('mode', choices=['prepare', 'encode', 'check'])
p.add_argument('--config', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
c = json.loads(a.config.read_text())
b = a.output
assert b.is_dir() and b.stat().st_uid == os.getuid()
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
durations = [8] + [12] * 6 + [10]
assert sum(durations) == 90 and len(c['scenes']) == 6

if a.mode == 'prepare':
    from PIL import Image, ImageDraw, ImageFont
    font = Path(c['font'])
    assert sha(font) == '8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c'
    assert not (b / 'slides').exists()
    (b / 'slides').mkdir()
    bounds = []
    def text(im, words, y, size, color='#e4d5ac'):
        draw = ImageDraw.Draw(im)
        face = ImageFont.truetype(str(font), size)
        box = draw.textbbox((0, 0), words, font=face)
        x = (1920 - (box[2] - box[0])) // 2 - box[0]
        yy = y - box[1]
        actual = draw.textbbox((x, yy), words, font=face)
        assert 50 <= actual[0] < actual[2] <= 1870 and 0 <= actual[1] < actual[3] <= 1080
        draw.text((x, yy), words, font=face, fill=color)
        bounds.append({'text': words, 'size': size, 'box': actual})
    def base():
        im = Image.new('RGB', (1920, 1080), '#172b2b')
        d = ImageDraw.Draw(im)
        d.rectangle((40, 30, 1880, 1050), outline='#877345', width=2)
        return im
    opening = base()
    text(opening, '殖民帝國', 280, 110, '#efcc78')
    text(opening, '繁體中文化', 450, 66)
    text(opening, '讓經典策略遊戲，讀起來更熟悉。', 650, 38)
    text(opening, c['version'], 830, 28)
    opening.save(b / 'slides/00.png')
    receipts = []
    for i, scene in enumerate(c['scenes'], 1):
        path = Path(scene['path'])
        assert sha(path) == scene['sha256']
        frame = Image.open(path).convert('RGB')
        assert frame.size == (1280, 800), (path, frame.size)
        im = base()
        im.paste(frame, (320, 140))
        text(im, scene['title'], 58, 44, '#efcc78')
        text(im, scene['caption'], 984, 32)
        im.save(b / f'slides/{i:02}.png')
        receipts.append(scene)
    closing = base()
    text(closing, '殖民帝國繁體中文化', 210, 72, '#efcc78')
    text(closing, 'Linux AppImage / Windows / macOS', 390, 44)
    text(closing, '音樂、音效與目前全部中文顯示功能', 530, 38)
    text(closing, '需自備合法原版資料。部分畫面仍保留原文。', 650, 32)
    text(closing, 'github.com/wicanr2/colonization_cht', 795, 34)
    text(closing, c['version'], 900, 28)
    closing.save(b / 'slides/07.png')
    (b / 'concat.txt').write_text(''.join(f"file 'slides/{i:02}.png'\nduration {d}\n" for i, d in enumerate(durations)) + "file 'slides/07.png'\n")
    (b / 'layout.json').write_text(json.dumps({'canvas': [1920, 1080], 'game_rect': [320, 140, 1600, 940], 'bounds': bounds}, ensure_ascii=False, indent=2) + '\n')
    (b / 'rights.json').write_text(json.dumps({
        'version': c['version'], 'publication': '使用者授權此MP4隨本次完整版Release公開；原始PNG與WAV不公開',
        'game': "Sid Meier's Colonization (MicroProse, 1994)，原版部分不屬於RRSAL授權",
        'method': '正常玩家路徑實際截圖的固定畫面剪輯，並非連續動態遊玩錄影',
        'font': {'name': 'Cubic 11', 'sha256': sha(font), 'license': 'font/Cubic-11-OFL.txt'},
        'scenes': receipts, 'durations': durations,
        'audio_method': c.get('audio_method', '實際dosgolem原版OPL音樂四段循環，接縫交疊0.5秒，音量2倍，淡入1秒與淡出3秒；無自製配樂'),
        'audio_receipt': c['audio_receipt'], 'original_files': c['original_files'],
        'dosgolem_commit': c['dosgolem_commit'],
    }, ensure_ascii=False, indent=2) + '\n')
elif a.mode == 'encode':
    wav = Path(c['audio'])
    receipt = json.loads(Path(c['audio_receipt']).read_text())
    assert sha(wav) == receipt['wav_sha256']
    film = b / f"colonization-cht-{c['version']}-promo.mp4"
    assert not film.exists()
    score = '[1:a]asplit=4[a0][a1][a2][a3];[a0][a1]acrossfade=d=0.5:c1=tri:c2=tri[a01];[a01][a2]acrossfade=d=0.5:c1=tri:c2=tri[a012];[a012][a3]acrossfade=d=0.5:c1=tri:c2=tri,aresample=48000,volume=2,afade=t=in:d=1,afade=t=out:st=87:d=3[score]'
    if c.get('audio_mode') == 'continuous':
        start = float(c['audio_start_seconds'])
        assert 0 <= start <= 10
        duration = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=nw=1:nk=1', str(wav)]))
        assert duration >= start + 90, '連續錄音長度不足，不能補循環'
        edit = f'atrim=start={start}:duration=90,asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=1,afade=t=out:st=87:d=3'
        measurement = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-threads', '2', '-i', str(wav), '-af',
                                      edit+',loudnorm=I=-18:TP=-2:LRA=11:print_format=json', '-f', 'null', '-'],
                                     capture_output=True, text=True, check=True, timeout=90).stderr
        measured = json.loads(measurement[measurement.rfind('{'):measurement.rfind('}')+1])
        (b / 'audio-loudness-measurement.json').write_text(json.dumps(measured, indent=2)+'\n')
        norm = (f"loudnorm=I=-18:TP=-2:LRA=11:measured_I={float(measured['input_i'])}:"
                f"measured_TP={float(measured['input_tp'])}:measured_LRA={float(measured['input_lra'])}:"
                f"measured_thresh={float(measured['input_thresh'])}:offset={float(measured['target_offset'])}:linear=true")
        score = '[1:a]'+edit+','+norm+',aresample=48000[score]'
    args = ['ffmpeg', '-hide_banner', '-nostdin', '-threads', '2', '-filter_threads', '2',
            '-filter_complex_threads', '2', '-f', 'concat', '-safe', '0', '-i', str(b / 'concat.txt'), '-i', str(wav),
            '-t', '90', '-vf', 'fps=30,format=yuv420p,fade=t=in:d=0.8,fade=t=out:st=89:d=1',
            '-filter_complex', score,
            '-map', '0:v', '-map', '[score]',
            '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-threads', '2',
            '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(film)]
    with (b / 'encode.log').open('w') as log:
        subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
    (b / 'encode-command.json').write_text(json.dumps(args, indent=2) + '\n')
else:
    film = b / f"colonization-cht-{c['version']}-promo.mp4"
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(film)]))
    (b / 'ffprobe.json').write_text(json.dumps(probe, indent=2) + '\n')
    streams = {s['codec_type']: s for s in probe['streams']}
    v, au = streams['video'], streams['audio']
    assert v['codec_name'] == 'h264' and (v['width'], v['height']) == (1920, 1080) and v['r_frame_rate'] == '30/1'
    assert au['codec_name'] == 'aac' and au['sample_rate'] == '48000' and au['channels'] == 2
    assert abs(float(probe['format']['duration']) - 90) < 0.1
    check = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-threads', '2', '-filter_threads', '2', '-i', str(film),
                            '-vf', 'blackdetect=d=0.4:pix_th=0.05,freezedetect=n=-60dB:d=2', '-af', 'volumedetect', '-f', 'null', '-'],
                           capture_output=True, text=True, check=True, timeout=300).stderr
    (b / 'quality.log').write_text(check)
    assert 'mean_volume: -inf' not in check and 'mean_volume:' in check
    # 固定畫面是剪輯設計；黑幀只允許首尾淡入淡出。
    import re
    assert float(re.search(r'max_volume: ([\d.\-]+) dB', check).group(1)) < -0.1, '影音輸出削波'
    black = [(float(x), float(y)) for x, y in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', check)]
    assert all(x < 1 or x >= 89 for x, y in black), black
    for i, second in enumerate([4, 14, 26, 38, 50, 62, 74, 85]):
        subprocess.run(['ffmpeg', '-v', 'error', '-threads', '2', '-ss', str(second), '-i', str(film), '-frames:v', '1', str(b / f'frame-{i}.png')], check=True)
    result = {'result': 'PASS_MP4_STRUCTURE_AUDIO_AND_LAYOUT', 'version': c['version'], 'seconds': 90, 'bytes': film.stat().st_size,
              'sha256': sha(film), 'black_intervals': black, 'freeze': '固定畫面章節為預期；quality.log保留完整檢測',
              'visual_sampling': '抽樣八幀，需另行檢視', 'audio_source_sha256': sha(Path(c['audio']))}
    (b / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))
