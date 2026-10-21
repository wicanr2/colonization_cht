#!/usr/bin/env python3
"""Docker內以正常遊玩實錄製作90秒推廣片，保留完整遊戲區與可追溯音源。"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    output = args.output
    assert not output.exists()
    output.mkdir()
    video, music, font = (Path(config[key]) for key in ['video', 'music', 'font'])
    assert sha(video) == config['video_sha256'] and sha(music) == config['music_sha256']
    assert sha(font) == 'b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a'
    capture = json.loads(Path(config['capture_receipt']).read_text())
    proof = json.loads(Path(config['first_colony_receipt']).read_text())
    assert capture['initial_saves'] == [] and capture['version'] == config['version']
    assert proof['result'] == 'FIRST_COLONY_CREATED_VIA_NORMAL_INPUTS'
    assert proof['video_sha256'] == config['video_sha256']
    assert sha(Path(proof['screenshot'])) == proof['screenshot_sha256']
    assert sha(Path(config['normal_inputs'])) == capture['normal_inputs_sha256']
    clips = config['clips']
    assert len(clips) >= 3 and abs(sum(clip['seconds'] for clip in clips) - 78) < .001
    assert any(clip.get('first_colony') and Path(clip.get('video', str(video))) == video
               and clip['start'] <= proof['video_time'] < clip['end'] for clip in clips)
    assert all(0 <= clip['start'] < clip['end'] and clip['seconds'] <= clip['end'] - clip['start'] for clip in clips)
    sources = {}
    for clip in clips:
        path = Path(clip.get('video', str(video)))
        expected = clip.get('video_sha256', config['video_sha256'])
        if str(path) not in sources:
            assert sha(path) == expected
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(path)]))
            source = next(stream for stream in probe['streams'] if stream['codec_type'] == 'video')
            assert source['width'] == 1280 and source['height'] in {800, 848}
            sources[str(path)] = {'sha256': expected, 'seconds': float(probe['format']['duration']),
                                  'width': source['width'], 'height': source['height']}
        assert clip['end'] <= sources[str(path)]['seconds']
    additional = [json.loads(Path(path).read_text()) for path in config.get('additional_capture_receipts', [])]
    for receipt in additional:
        assert receipt['version'] == config['version'] and receipt['binary_sha256'] == capture['binary_sha256']
        assert receipt['initial_save_sha256']['COLONY00.SAV'] == proof['save_sha256']
    music_seconds = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(music)]))
    assert music_seconds >= 93
    from PIL import Image, ImageDraw, ImageFont
    bounds, commands = [], []

    def background():
        image = Image.new('RGB', (1920, 1080), '#251b12')
        draw = ImageDraw.Draw(image)
        draw.rectangle((34, 28, 1885, 1051), outline='#af894c', width=2)
        return image

    def text(image, words, y, size, fill='#f3cd63'):
        face = ImageFont.truetype(str(font), size, index=3)
        draw = ImageDraw.Draw(image)
        ink = draw.textbbox((0, 0), words, font=face)
        x = (1920 - ink[2] + ink[0]) // 2 - ink[0]
        position = (x, y - ink[1])
        box = draw.textbbox(position, words, font=face)
        assert 50 <= box[0] < box[2] <= 1870 and 30 <= box[1] < box[3] <= 1040
        draw.text(position, words, font=face, fill=fill)
        bounds.append({'text': words, 'font_px': size, 'box': box})

    def run(command):
        commands.append(command)
        with (output / 'encode.log').open('a') as log:
            subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=600, check=True)

    prefix = ['ffmpeg', '-y', '-hide_banner', '-nostdin', '-loglevel', 'warning', '-threads', '2', '-filter_threads', '2', '-filter_complex_threads', '2']
    encoder = config.get('video_encoder', 'libx264')
    assert encoder in {'libx264', 'h264_nvenc'}
    preset = config.get('cpu_preset', 'veryfast')
    assert preset in {'ultrafast', 'veryfast'}
    settings = ['-preset', 'p4', '-rc', 'vbr', '-b:v', '0', '-cq', '18'] if encoder == 'h264_nvenc' else ['-preset', preset, '-crf', '18']
    encoding = ['-an', '-c:v', encoder] + settings + ['-threads', '2', '-pix_fmt', 'yuv420p']
    with tempfile.TemporaryDirectory(prefix='colonization-gameplay-promo-') as temp:
        temp = Path(temp)
        title = background()
        text(title, '殖民帝國 Remastered', 270, 96)
        text(title, '航向新世界，建立第一座城鎮', 480, 52, '#e8d6b5')
        text(title, '繁體中文 · 精細像素 HD · 原版玩法', 640, 38, '#e8d6b5')
        text(title, config['version'], 875, 28)
        title.save(temp / 'opening.png')
        closing = background()
        text(closing, '殖民帝國 Remastered', 170, 76)
        text(closing, 'Linux · Windows · macOS', 340, 48, '#e8d6b5')
        text(closing, 'HD＋原版＋中文化', 500, 46)
        text(closing, '原版＋中文化', 590, 46)
        text(closing, '航海、登陸，開拓你的新世界', 740, 34, '#e8d6b5')
        text(closing, config['version'], 910, 28)
        closing.save(temp / 'closing.png')
        parts = []
        for name, image in [('opening', temp / 'opening.png'), *[(str(i), None) for i in range(len(clips))], ('closing', temp / 'closing.png')]:
            target = temp / (name + '.mp4')
            if image is not None:
                fade = 'fade=t=in:d=0.5' if name == 'opening' else 'fade=t=out:st=5.5:d=0.5'
                run(prefix + ['-loop', '1', '-framerate', '30', '-i', str(image), '-t', '6', '-vf', fade] + encoding + [str(target)])
            else:
                clip = clips[int(name)]
                canvas = background()
                text(canvas, clip['title'], 45, 40)
                text(canvas, clip['caption'], 991, 30, '#e8d6b5')
                ImageDraw.Draw(canvas).rectangle((318, 102, 1601, 953), outline='#af894c', width=2)
                still = temp / (name + '.png')
                canvas.save(still)
                speed = (clip['end'] - clip['start']) / clip['seconds']
                clip_video = Path(clip.get('video', str(video)))
                top = 104 + (848 - sources[str(clip_video)]['height']) // 2
                filters = f'[0:v]setpts=(PTS-STARTPTS)/{speed:.12f},fps=30[game];[1:v][game]overlay=320:{top}:shortest=1,format=yuv420p[out]'
                run(prefix + ['-ss', str(clip['start']), '-t', str(clip['end'] - clip['start']), '-i', str(clip_video),
                              '-loop', '1', '-framerate', '30', '-i', str(still), '-filter_complex', filters, '-map', '[out]',
                              '-t', str(clip['seconds'])] + encoding + [str(target)])
            parts.append(target)
        listing = temp / 'concat.txt'
        listing.write_text(''.join("file '" + str(path) + "'\n" for path in parts))
        silent = temp / 'silent.mp4'
        run(prefix + ['-f', 'concat', '-safe', '0', '-i', str(listing), '-c', 'copy', str(silent)])
        edit = 'atrim=start=3:duration=90,asetpts=PTS-STARTPTS,aresample=48000,afade=t=in:d=1,afade=t=out:st=87:d=3'
        # 音量量測需要FFmpeg的資訊輸出。
        measure_cmd = prefix.copy()
        measure_cmd[measure_cmd.index('warning')] = 'info'
        measurement = subprocess.run(measure_cmd + ['-i', str(music), '-af', edit + ',loudnorm=I=-18:TP=-2:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True, timeout=120, check=True).stderr
        measured = json.loads(measurement[measurement.rfind('{'):measurement.rfind('}') + 1])
        (output / 'audio-loudness.json').write_text(json.dumps(measured, indent=2) + '\n')
        norm = (f"loudnorm=I=-18:TP=-2:LRA=11:measured_I={float(measured['input_i'])}:measured_TP={float(measured['input_tp'])}:"
                f"measured_LRA={float(measured['input_lra'])}:measured_thresh={float(measured['input_thresh'])}:"
                f"offset={float(measured['target_offset'])}:linear=true")
        film = output / f"colonization-cht-{config['version']}-promo.mp4"
        run(prefix + ['-i', str(silent), '-i', str(music), '-filter_complex', '[1:a]' + edit + ',' + norm + ',aresample=48000[score]',
                      '-map', '0:v', '-map', '[score]', '-t', '90', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', str(film)])
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(film)]))
    (output / 'ffprobe.json').write_text(json.dumps(probe, indent=2) + '\n')
    streams = {stream['codec_type']: stream for stream in probe['streams']}
    assert streams['video']['codec_name'] == 'h264' and streams['video']['r_frame_rate'] == '30/1'
    assert (streams['video']['width'], streams['video']['height']) == (1920, 1080)
    assert streams['audio']['codec_name'] == 'aac' and streams['audio']['sample_rate'] == '48000' and streams['audio']['channels'] == 2
    assert abs(float(probe['format']['duration']) - 90) < .1
    quality = subprocess.run(['ffmpeg', '-hide_banner', '-nostdin', '-threads', '2', '-filter_threads', '2', '-i', str(film),
                              '-vf', 'blackdetect=d=0.4:pix_th=0.05,freezedetect=n=-60dB:d=2', '-af', 'volumedetect', '-f', 'null', '-'],
                             capture_output=True, text=True, check=True, timeout=300).stderr
    (output / 'quality.log').write_text(quality)
    assert 'mean_volume:' in quality and 'mean_volume: -inf' not in quality
    peak = float(re.search(r'max_volume: ([\d.\-]+) dB', quality).group(1))
    assert peak < -.1
    black = [(float(a), float(b)) for a, b in re.findall(r'black_start:([\d.]+) black_end:([\d.]+)', quality)]
    assert all(start < 1 or start >= 89 for start, end in black)
    samples = [3, 9, 16, 23, 30, 37, 44, 51, 58, 65, 72, 81, 87]
    for index, second in enumerate(samples):
        subprocess.run(['ffmpeg', '-v', 'error', '-threads', '2', '-ss', str(second), '-i', str(film), '-frames:v', '1', str(output / f'frame-{index:02}.png')], check=True)
    sheet = Image.new('RGB', (1920, 4 * 290), '#251b12')
    for index in range(len(samples)):
        frame = Image.open(output / f'frame-{index:02}.png').convert('RGB')
        frame.thumbnail((480, 270))
        sheet.paste(frame, ((index % 4) * 480, (index // 4) * 290))
    sheet.save(output / 'contact-sheet.png')
    (output / 'layout.json').write_text(json.dumps({'canvas': [1920, 1080], 'game_rect': [320, 104, 1600, 952], 'bounds': bounds}, ensure_ascii=False, indent=2) + '\n')
    (output / 'encode-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    (output / 'capture.json').write_text(json.dumps({'version': config['version'], 'capture': capture,
        'additional_captures': additional, 'sources': sources, 'first_colony': proof, 'clips': clips}, ensure_ascii=False, indent=2) + '\n')
    (output / 'rights.json').write_text(json.dumps({'version': config['version'], 'private_only': True,
        'video_method': capture['method'],
        'editing': '剪接及部分加速，保留完整遊戲區；各段來源與擷取方式見capture.json',
        'audio_method': '既有原版OPL連續錄音取3至93秒，響度正規化及淡入淡出；後製配樂，非同步實錄音效',
        'music_source': config['music_source'], 'font_sha256': sha(font), 'raw_video_sha256': sha(video),
        'game': "Sid Meier's Colonization (MicroProse, 1994)，原版部分不屬於專案授權", 'publication': '本次僅本機交付，未上傳'}, ensure_ascii=False, indent=2) + '\n')
    result = {'result': 'PROMO_TECHNICAL_CHECKS_PASS_VISUAL_PENDING', 'version': config['version'], 'seconds': 90,
              'bytes': film.stat().st_size, 'sha256': sha(film), 'includes_first_colony': True, 'gameplay_seconds': 78, 'video_encoder': encoder,
              'black_intervals': black, 'max_volume_db': peak, 'visual_sampling': 'pending',
              'freeze_review': '回合制操作與對話閱讀可自然靜止，需對照實錄段落及quality.log檢視', 'manual_validation': 'pending'}
    (output / 'validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
