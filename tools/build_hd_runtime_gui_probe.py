"""規格061 DRAFT：從已固定的五語GUI探針組裝可丟棄HD視窗驗證。"""
import argparse
import hashlib
import os
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument("--output", type=Path, required=True)
p.add_argument("--formal", action="store_true", help="規格061 READY：驗證正式啟動器")
p.add_argument("--building-only", action="store_true", help="只重生歷史首座檢查，供舊收據工具使用")
a = p.parse_args()
repo = Path(__file__).resolve().parents[1]
out = a.output.resolve()
assert Path("/.dockerenv").is_file() and os.getuid() != 0
assert out.is_relative_to(Path("/out")) or out.is_relative_to(repo / "workplace")
assert out.parent.stat().st_uid == os.getuid() and not out.exists()
source = repo / "tools/probe_language_live_gui.py"
assert hashlib.sha256(source.read_bytes()).hexdigest() == "b4f1a7579b33cfc247663c97f2bf298a229407031ad24fcb95132f5857ca4106"
s = source.read_text()
def one(old, new):
    global s
    assert s.count(old) == 1, old
    s = s.replace(old, new, 1)

one('ROOT = Path(__file__).resolve().parent.parent', 'ROOT = Path("/repo")')
one('output.is_relative_to((ROOT / "workplace").resolve())',
    '(output.is_relative_to((ROOT / "workplace").resolve()) or output.is_relative_to(Path("/out")))')
one('    args = parser.parse_args()', '''    parser.add_argument("--hd-asset", type=Path, required=True)
    args = parser.parse_args()
    need(not args.formal_launcher and not args.reload_save, "HD DRAFT只使用隔離入口")''')
one('    log = (output / "process.log").open("wb")',
    '    command += ["--hd-prototype-asset", str(args.hd_asset)]\n    log = (output / "process.log").open("wb")')
one('    env = os.environ.copy()', '    env = os.environ.copy()\n    env["GOMEMLIMIT"] = "1200MiB"')
one('            for locale in ["zh-Hans", "ja", "ko", "en", "zh-Hant"]:',
    '''            locales = ["en"] if scene == "hd-quit-confirmation" else ["zh-Hans", "ja", "ko", "en", "zh-Hant"]
            for locale, graphics in [(l, g) for l in locales for g in ["hd", "original"]]:''')
one('                click(363 + 136 * LOCALES.index(locale), 374)',
    '                click(363 + 136 * LOCALES.index(locale), 374)\n                click(464 if graphics == "original" else 808, 480)')
one('                first, step = open_settings()', '''                if scene == "hd-building-hover":
                    hover_start = status()["step"]
                    move(65 * 4, 25 * 4 + 48)
                    wait(lambda s: s.get("step", 0) >= hover_start + 2000000, "正常重新懸停未完成")
                first, step = open_settings()''')
s = s.replace('{"language": locale, "graphics": "original"}', '{"language": locale, "graphics": graphics}')
one('f"{scene}-{locale}.png"', 'f"{scene}-{locale}-{graphics}.png"')
one('                if locale == "en":', '''                hd = record.get("hd", {})
                if graphics == "hd":
                    need(hd.get("prototype") is True, "未由HD執行期合成")
                    fallback = hd.get("painted") == 0 and hd.get("reason") == "unverified-cursor-or-native-surface"
                    if scene in {"colony", "hd-reentered-colony", "hd-encyclopedia-closed"} and not fallback:
                        need(hd.get("painted") == 621, "進城或重進沒有完整HD建築")
                    if scene == "hd-building-hover" and not fallback:
                        need(hd.get("painted") == 460, "浮標遮擋後HD擁有權不同")
                    if scene in {"main-menu", "world", "save-slots", "save-success", "saved-world", "hd-building-encyclopedia", "hd-exited-again", "hd-quit-confirmation"}:
                        need(hd.get("painted") == 0, "離開建築後殘留HD")
                else:
                    need(not hd, "原版模式仍有HD合成")
                if locale == "en":''')
one('                    need(actual.tobytes() == original.tobytes(), "英文沒有使用原版像素")', '''                    if graphics == "original" or not hd.get("painted"):
                        need(actual.tobytes() == original.tobytes(), "英文原版像素不同")
                    else:
                        safe = Image.new("1", actual.size)
                        ImageDraw.Draw(safe).rectangle((224, 52, 315, 159), fill=1)
                        difference = ImageChops.difference(actual, original)
                        outside = Image.composite(difference, Image.new("RGB", actual.size), safe.point(lambda v: 0 if v else 255, "1"))
                        need(outside.getbbox() is None and difference.getbbox() is not None, "HD英文未限定於建築矩形")''')
one('                    difference = ImageChops.difference(actual, original)\n                    outside',
    '''                    if graphics == "hd" and hd.get("painted"):
                        draw.rectangle((224, 52, 315, 159), fill=1)
                    difference = ImageChops.difference(actual, original)
                    outside''')
one('checks.append({"scene": scene, "locale": locale, "step": step,',
    'checks.append({"scene": scene, "locale": locale, "graphics": graphics, "step": step,\n'
    '                               "presentation_path": e["presentation_path"], "indexed_path": e["indexed_path"],\n'
    '                               "palette_path": e["palette_path"], "dos_mouse": e["dos_mouse"],')
one('print("PASS_NATIVE_LIVE_GUI_SWITCH", scene, locale, step, len(record.get("items", [])), flush=True)',
    'print("PASS_HD_RUNTIME_GUI_SWITCH", scene, locale, graphics, step, hd.get("painted", 0), flush=True)')
one('if scene in {"world", "saved-world"}:', 'if scene in {"world", "saved-world", "hd-exited-again"}:')
one('                    if scene == "colony":', '''                    if scene == "hd-building-encyclopedia":
                        need(any(i.get("id") == "PEDIA.TXT:@BUILDING32" for i in record["items"]), "不是已驗建築百科")
                    if scene == "colony":''')
one('        final_live = live(status())', '''        # 正常重進、重新懸停、右鍵百科、返回殖民地與世界。
        before = status()["step"]
        click(152 * 4, 112 * 4 + 48)
        wait(lambda s: s.get("step", 0) >= before + 8000000, "正常返回殖民地未完成")
        switch_round("hd-reentered-colony")
        before = status()["step"]
        move(65 * 4, 25 * 4 + 48)
        wait(lambda s: s.get("step", 0) >= before + 2000000, "建築懸停未完成")
        switch_round("hd-building-hover")
        before = status()["step"]
        move(65 * 4, 25 * 4 + 48)
        xdo("mousedown", 3)
        time.sleep(0.08)
        xdo("mouseup", 3)
        wait(lambda s: s.get("step", 0) >= before + 4000000 and
             any(i.get("id") == "PEDIA.TXT:@BUILDING32" for i in live(s).get("items", [])), "正常右鍵未開啟建築百科")
        switch_round("hd-building-encyclopedia")
        before = status()["step"]
        xdo("keydown", "Escape")
        time.sleep(0.08)
        xdo("keyup", "Escape")
        wait(lambda s: s.get("step", 0) >= before + 4000000 and
             any(i.get("id") == "STRING:template:colony-title" for i in live(s).get("items", [])), "百科關閉未返回殖民地")
        switch_round("hd-encyclopedia-closed")
        before = status()["step"]
        xdo("keydown", "Escape")
        time.sleep(0.08)
        xdo("keyup", "Escape")
        wait(lambda s: s.get("step", 0) >= before + 4000000 and
             any(i.get("kind") == "sea-bar" for i in live(s).get("items", [])), "離城未返回世界")
        switch_round("hd-exited-again")
        before = status()["step"]
        sequence = status().get("dialog", {}).get("dialog_seq", 0)
        xdo("keydown", "Escape")
        time.sleep(0.08)
        xdo("keyup", "Escape")
        wait(lambda s: s.get("step", 0) >= before + 4000000 and
             s.get("dialog", {}).get("dialog_seq", 0) > sequence, "原版退出確認框未開啟")
        switch_round("hd-quit-confirmation")
        for scene, painted in [("colony", 621), ("hd-building-hover", 460)]:
            covered = {c["locale"] for c in checks if c["graphics"] == "hd" and
                       c["scene"] in ({"colony", "hd-reentered-colony"} if scene == "colony" else
                                      {"hd-building-hover"}) and
                       c["native_live"].get("hd", {}).get("painted") == painted}
            need(covered == set(LOCALES), "五語HD正向場景不完整：" + scene + str(covered))
        final_live = live(status())''')
one('"result": "PASS_NATIVE_LIVE_FIVE_LANGUAGE_GUI"', '"result": "PASS_HD_RUNTIME_FIVE_LANGUAGE_GUI"')
one('"probe": sha(Path(__file__).read_bytes())',
    '"probe": sha(Path(__file__).read_bytes()), "hd_asset": sha(args.hd_asset.read_bytes())')
one('        (output / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n")',
    '''        memory = prefix.with_suffix(".memory").read_bytes()
        cursor = memory[0x1cd74:0x1ce74]
        need(sha(cursor) == "47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03", "游標來源不同")
        cursor_points = 0
        for c in checks:
            if c["graphics"] != "hd" or not c["native_live"].get("hd", {}).get("painted"):
                continue
            native = Image.frombytes("P", (320, 200), Path(c["indexed_path"]).read_bytes())
            native.putpalette([v << 2 | v >> 4 for v in Path(c["palette_path"]).read_bytes()])
            original = native.convert("RGB").resize((1280, 800), Image.Resampling.NEAREST)
            with Image.open(c["presentation_path"]) as im:
                actual = im.convert("RGB")
            for k, value in enumerate(cursor):
                if value == 255:
                    continue
                x, y = c["dos_mouse"]["x"] + k % 16, c["dos_mouse"]["y"] + k // 16
                if 0 <= x < 320 and 0 <= y < 200:
                    rect = (x * 4, y * 4, x * 4 + 4, y * 4 + 4)
                    need(actual.crop(rect).tobytes() == original.crop(rect).tobytes(), "HD或文字蓋住不透明游標")
                    cursor_points += 1
        result["verified_cursor_points"] = cursor_points
        (output / "check.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\\n")''')
one('["隔離視窗；完整來源生命週期、正式接線、HD及同輸入重播仍須另外驗證。"]',
    '["規格061 DRAFT隔離原型；單座候選未定稿，正式HD、其他素材及本輪同輸入重播仍未完成。"]')
one('        if process.poll() is None:\n            os.killpg(process.pid, signal.SIGTERM)', '''        if process.poll() is None:
            try:
                subprocess.run([sys.executable, str(ROOT / "tools/gui_close_window.py"), "--window", window], check=True, timeout=5)
                process.wait(timeout=10)
            except (subprocess.SubprocessError, UnboundLocalError):
                pass
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)''')
if a.formal:
    one('need(not args.formal_launcher and not args.reload_save, "HD DRAFT只使用隔離入口")',
        'need(args.formal_launcher and not args.reload_save, "正式HD驗收需要正式啟動器")\n'
        '    need(args.hd_asset.resolve() == (args.formal_launcher.parent / "graphics/building-032.png").resolve(), "正式HD素材路徑不同")')
    one('    command += ["--hd-prototype-asset", str(args.hd_asset)]\n', '')
    one('hd.get("prototype") is True', 'hd.get("formal") is True')
    one('result["limitations"] = ["正式入口與本次正常路徑；其他未驗欄位及HD仍未完成。"]',
        'result["limitations"] = ["正式入口、單座HD與本次正常路徑；其他素材、動畫及完整五語仍未完成。"]')
    one('"result": "PASS_HD_RUNTIME_FIVE_LANGUAGE_GUI"', '"result": "PASS_FORMAL_HD_FIVE_LANGUAGE_GUI"')
if a.formal and not a.building_only:
    from build_hd_sea_gui_probe import extend_sea_checks
    s = extend_sea_checks(s, formal=True)
compile(s, str(out), "exec")
out.write_text(s)
print("PASS_HD_RUNTIME_GUI_PROBE_BUILD", hashlib.sha256(out.read_bytes()).hexdigest())
