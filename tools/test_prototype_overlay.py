"""離線原型回歸；真實輸入缺失會 skip，不使用合成資料冒充原版。"""
import copy
import os
from pathlib import Path
import unittest

from PIL import ImageChops, ImageFont

import prototype_overlay as p


class GeometryTests(unittest.TestCase):
    def test_both_axes_and_ellipsis(self):
        # 這裡只驗通用布局，不宣稱是原版或中文字型驗收。
        font = ImageFont.load_default(size=24)
        self.assertIsNone(p.fit_text("ABC", font, 1, 1))
        fitted = p.fit_text("A" * 100, font, 80, 30)
        self.assertTrue(fitted.endswith("…"))
        box = font.getbbox(fitted)
        self.assertLessEqual(box[2] - box[0], 80)
        self.assertLessEqual(box[3] - box[1], 30)
        self.assertIsNone(p.fit_text("A\nB", font, 80, 30))


class OriginalInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = [os.environ.get("OVERLAY_EVENTS", "/out/goal054-clear-events.json"),
                 os.environ.get("OVERLAY_GAME", "/game"),
                 os.environ.get("OVERLAY_TRANSLATIONS", str(Path(__file__).resolve().parents[1] / "text/draft.zh-Hant.tsv")),
                 os.environ.get("OVERLAY_FONT", "/fonts/Cubic_11.ttf")]
        if not all(Path(path).exists() for path in paths):
            raise unittest.SkipTest("缺少本機原版證據／譯稿／候選字型")
        cls.original = p.load_inputs(*paths)

    def setUp(self):
        self.inputs = copy.deepcopy(self.original)

    def fallback(self, reason, enabled=True):
        output, receipt = p.compose(self.inputs, enabled)
        self.assertFalse(receipt["applied"], receipt)
        self.assertEqual(receipt["reason"], reason)
        self.assertEqual(output.tobytes(), p.original_image(self.inputs.indexed, self.inputs.palette).tobytes())

    def test_real_overlay_and_restored_region(self):
        output, receipt = p.compose(self.inputs)
        self.assertTrue(receipt["applied"], receipt)
        self.assertEqual(receipt["changed_pixels"], 180)
        self.assertEqual(receipt["text"], self.inputs.translation)
        baseline = p.original_image(self.inputs.indexed, self.inputs.palette)
        bounds = ImageChops.difference(output, baseline).getbbox()
        self.assertIsNotNone(bounds)
        self.assertGreaterEqual(bounds[0], p.SAFE[0])
        self.assertGreaterEqual(bounds[1], p.SAFE[1])
        self.assertLessEqual(bounds[2], p.SAFE[2])
        self.assertLessEqual(bounds[3], p.SAFE[3])
        # 獨立字模遮罩外：英文差異的180像素均須回復事件前背景。
        from PIL import Image, ImageDraw
        mask = Image.new("L", output.size)
        font = ImageFont.truetype(str(self.inputs.font_path), 24)
        box = font.getbbox(receipt["text"])
        ImageDraw.Draw(mask).text((p.SAFE[0] - box[0], p.SAFE[1] - box[1]),
                                 receipt["text"], font=font, fill=255)
        before = self.inputs.before[p.CANVAS:p.CANVAS + p.PIXELS]
        after = self.inputs.after[p.CANVAS:p.CANVAS + p.PIXELS]
        restored = p.original_image(before, self.inputs.palette)
        changed = [i for i in range(p.PIXELS) if before[i] != after[i]]
        self.assertEqual(len(changed), 180)
        self.assertTrue(all(self.inputs.indexed[i] == after[i] for i in changed))
        for i in changed:
            for dy in range(4):
                for dx in range(4):
                    xy = (i % 320 * 4 + dx, i // 320 * 4 + dy)
                    if mask.getpixel(xy) == 0:
                        self.assertEqual(output.getpixel(xy), restored.getpixel(xy))

    def test_disabled(self):
        self.fallback("disabled", False)

    def test_missing_translation(self):
        self.inputs.translation = ""
        self.fallback("missing-translation")

    def test_wrong_version(self):
        self.inputs.files["VICEROY.EXE"] += b"wrong"
        self.fallback("wrong-version")

    def test_wrong_frame_and_scene_transition(self):
        self.inputs.indexed = bytes([self.inputs.indexed[0] ^ 1]) + self.inputs.indexed[1:]
        self.fallback("wrong-frame-or-palette")

    def test_wrong_palette(self):
        self.inputs.palette = bytes([self.inputs.palette[0] ^ 1]) + self.inputs.palette[1:]
        self.fallback("wrong-frame-or-palette")

    def test_incomplete_event(self):
        del self.inputs.event_log["events"][0]["return_step"]
        self.fallback("incomplete-or-wrong-event")

    def test_wrong_source(self):
        self.inputs.translation_source = "different"
        self.fallback("wrong-translation-source")

    def test_wrong_source_length(self):
        self.inputs.source_byte_length += 1
        self.fallback("wrong-translation-source")

    def test_wrong_memory(self):
        self.inputs.before = bytes([self.inputs.before[0] ^ 1]) + self.inputs.before[1:]
        self.fallback("wrong-event-memory")

    def test_missing_glyph(self):
        self.inputs.translation += "\U0010ffff"
        self.fallback("missing-glyph")

    def test_long_text_with_real_font(self):
        self.inputs.translation *= 40
        _, receipt = p.compose(self.inputs)
        self.assertTrue(receipt["applied"], receipt)
        self.assertTrue(receipt["truncated"])
        box = receipt["ink_rect"]
        self.assertLessEqual(box[2], p.SAFE[2])
        self.assertLessEqual(box[3], p.SAFE[3])

    def test_cmap_real_coverage(self):
        coverage = p.cmap_coverage(self.inputs.font_path.read_bytes())
        self.assertTrue(all(ord(char) in coverage for char in self.inputs.translation + "…"))
        self.assertNotIn(0x10FFFF, coverage)


if __name__ == "__main__":
    unittest.main()
