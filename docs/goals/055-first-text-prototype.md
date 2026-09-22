# 目標 055：第一則中文顯示原型

狀態：工程完成，視覺決策待確認<br>
日期：2026-09-22<br>
Issue：[#26](https://github.com/wicanr2/colonization_cht/issues/26)，字型／術語決策 [#10](https://github.com/wicanr2/colonization_cht/issues/10)

## 範圍

依 [規格草案 009](../spec/009-first-text-overlay-draft.md)，將目標 054 的正常主選單第一列
製成一張可丟棄繁中顯示原型。使用者已授權翻譯與工程子代理；本輪不把視覺候選定案。

1. 整合本機 50 筆可回查來源的繁中譯稿，僅使用已動態驗證的一列。
2. 以原版印字前背景、完成事件及最終畫面建立失敗即關閉的輸出合成器。
3. 製作原文／中文對照，測試缺譯、缺字、錯版本、換畫面、未完成事件與雙軸溢出。
4. 原型可見後請使用者確認字型／字級與用語；正式持續播放覆蓋仍受 READY 閘門限制。

## 完成界線

完成原型與回退測試，並留下可重跑入口、來源與限制，才可結束本輪工程。
本目標不等於 Issue #26 全部完成，不關閉正式中文顯示切片，也不宣稱全遊戲中文化或可完整遊玩。
任何原版畫面、完整原文、字型與 runtime dump 僅保留 `workplace/` 本機，不加入可散布產物。

## 輸入索引

- `workplace/goal054-translation-draft.tsv`：只留歷史來源盤點，不再維護譯文；譯文唯一來源為下列版本化 TSV。
- `workplace/goal054-translation-inventory.py`：來源、控制碼與草稿驗證。
- `workplace/goal054-font-audit.md`：候選字型指紋、內嵌許可及離線渲染工具。
- `tools/trace_text.go`：只讀原版輸出事件與畫布擷取。
- `tools/prototype_overlay.py`：已通過測試的離線原型；不是正式 xlate 引擎。
- `text/draft.zh-Hant.tsv`：可版控的 50 筆來源指紋與繁中譯稿，不含完整原文。
- `tools/validate_translation_draft.py`：驗證來源 bytes、UTF-8、控制碼與占位符。
- `tools/test_prototype_overlay.py`：14 項布局、回退與真實原版輸入測試。

## 已驗證成果

首列「在新世界開始遊戲」在 1280×800 輸出副本上呈現；原版 320×200 邏輯畫面不變。
候選 Cubic 11 24px 的實際字框為 `[0,2,208,24]`，墨跡範圍 `[344,428,552,450]`，
位於安全矩形 `[344,428,928,456)`，未截斷。先恢復原文字的 180 個實際差異像素，
不以純色覆蓋整個文字矩形。原型未修改遊戲／快照，亦未把中文圖像回灌 dosgolem。

14 項測試通過，含中文關閉、缺譯、缺字、錯版本／來源長度／色盤／場景、未完成事件、
錯記憶體及長譯文。缺少本機合法原版或字型時明確 skip，不以替代資料宣稱成功。
本機對照為 `workplace/reports/goal055-first-en.png` 與 `goal055-first-zh.png`，各有 JSON 收據。
中文 PNG SHA-256：`ff47ad685134dae6c28951bc7a796e0bc1ded81781309cf909b31dfe36d325e7`。
英文 PNG SHA-256：`873cb55655bafadfa2dea1baf2afee63d2d1668d2c5dc7fd4fcb48e6f0e29125`。

視覺候選待使用者確認，不把目前字型、字級、術語與超長省略策略寫成正式規格。
Issue #26 仍開放；尚缺即時事件生命週期、玩家操作中的中文／原文切換及正常路徑驗收。

## Docker 重跑

先依目標 054 重生 `/out/goal054-clear-events.json` 及相關檔案。沿用既有 `rich2-py:latest`
（映像 ID `sha256:e5c73862da40d1e0c26d9d5f6a62491c75ddfe8ada5c77677e1e445f13d85a71`，
Pillow 12.3.0／FreeType 2.14.3）。字型目錄只讀，不複製或發布字型。以下是測試命令：

```sh
test -d "$PWD/tools" && test -d "$PWD/workplace/reports" &&
test -d "/home/anr2/cht/psychic-war/workplace/font-cmp" &&
test -d "$PWD/Sid Meier's Colonization (1994)/SMColoni/COLONIZE" &&
timeout 60 docker run --rm --network none --memory 512m --cpus 1 --pids-limit 128 \
  --user "$(id -u):$(id -g)" --entrypoint python3 -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/repo:ro" -v "$PWD/workplace/reports:/out" \
  -v "/home/anr2/cht/psychic-war/workplace/font-cmp:/fonts:ro" \
  -v "$PWD/Sid Meier's Colonization (1994)/SMColoni/COLONIZE:/game:ro" \
  -w /repo/tools rich2-py:latest -m unittest -v test_prototype_overlay
```

相同容器參數，將 `-m unittest -v test_prototype_overlay` 換成以下參數可重生中文圖：

```text
/repo/tools/prototype_overlay.py --events /out/goal054-clear-events.json
--game /game --translations /repo/text/draft.zh-Hant.tsv
--font /fonts/Cubic_11.ttf --output /out/goal055-first-zh.png
```

參數須接成同一行；英文圖另加 `--off` 並改輸出為 `goal055-first-en.png`。
同環境執行 `/repo/tools/validate_translation_draft.py --game /game` 可驗證 50 筆草稿。
每批結束檢查專案容器與輸出 UID/GID；本輪未留下容器、root 擁有檔或誤建 `.md` 目錄。
