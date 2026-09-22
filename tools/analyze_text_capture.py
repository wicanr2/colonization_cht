"""整理原版印字前後的實際差異；只分析本機研究輸入。"""
import collections
import hashlib
import json
from pathlib import Path

base = Path('/out/goal054-clear-events.json.event0')
before = Path(str(base) + '.before').read_bytes()
after = Path(str(base) + '.after').read_bytes()
changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
pages = collections.Counter(i // 4096 for i in changed)
vram = [i - 0xa0000 for i in changed if 0xa0000 <= i < 0xafa00]
canvas_base = 0x2cae0
canvas = [i - canvas_base for i in changed if canvas_base <= i < canvas_base + 64000]
frame = Path('/out/goal054-clear-events.json.idx').read_bytes()
result = {
    'before_sha256': hashlib.sha256(before).hexdigest(),
    'after_sha256': hashlib.sha256(after).hexdigest(),
    'total_changed': len(changed),
    'pages': {hex(p * 4096): n for p, n in sorted(pages.items())},
    'vram_changed': len(vram),
    'vram_bounds': ([min(i % 320 for i in vram), min(i // 320 for i in vram),
                     max(i % 320 for i in vram), max(i // 320 for i in vram)] if vram else None),
    'drawing_descriptor_ds_2da8': before[0x1c6a0 + 0x2da8:0x1c6a0 + 0x2db8].hex(),
    'first_addresses': [hex(i) for i in changed[:40]],
    'canvas_base': hex(canvas_base),
    'canvas_changed': len(canvas),
    'canvas_bounds': ([min(i % 320 for i in canvas), min(i // 320 for i in canvas),
                       max(i % 320 for i in canvas), max(i // 320 for i in canvas)] if canvas else None),
    'all_changed_canvas_pixels_survive_in_final_frame': all(after[canvas_base+i] == frame[i] for i in canvas),
    'text_color_counts': dict(collections.Counter(after[canvas_base+i] for i in canvas)),
    'final_colors_at_changed_pixels': dict(collections.Counter(frame[i] for i in canvas)),
    'mismatch_count': sum(after[canvas_base+i] != frame[i] for i in canvas),
    'mismatch_samples': [[i % 320,i // 320,after[canvas_base+i],frame[i]] for i in canvas if after[canvas_base+i]!=frame[i]][:20],
}
Path('/out/goal054-clear-text-diff.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
