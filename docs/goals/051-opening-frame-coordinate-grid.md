# 目標 051：開場畫面座標格視覺清冊

狀態：completed<br>
日期：2026-09-22<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 031](031-opening-full-frame-static-text-survey.md)、[目標 033](033-ocean-label-post-copy-persistence.md)、[目標 046](046-opening-click-nonzero-downstream-dataflow.md)、[目標 050](050-dos-subdirectory-launch-reference-inventory.md)

## 目的

動態文字的 parent／batch 分支已到決策閘門；但在不改變 dosgolem 能力、也不注入新的滑鼠座標前，仍可將既有正常
`OPENING.EXE` 完整 composite frame 轉為只供本機檢視的座標格圖，讓使用者以實際畫面辨識下一個**正常玩家操作**。
本輪不把視覺外觀或格線位置命名為按鈕、文字或控制項；它只是後續共同決策的可丟棄觀測材料。

## 執行項目

1. 先確認既有第一個完整 composite frame 的 indexed VRAM、palette、state 雜湊與 dosgolem commit 仍可回查；若
   收據遺失或雜湊不符，明確 skip，不重建遊戲或猜測畫面。
2. 在無網路、唯讀原版輸入的 Docker 容器中，從既有收據產生僅存於 gitignore `workplace/reports/` 的放大座標格
   PNG 與 metadata：logical 320×200、格線間距、frame／palette／輸出 SHA-256、工具版本與推論限制。
3. 以 `view_image` 檢視本機 PNG；只描述可直接看見的版面結構與既有候選，不 OCR、不轉錄原文、不猜按鈕語意、
   不建立文本鍵或中文覆蓋。
4. 不注入新的鍵盤／滑鼠座標、不執行 `VICEROY.EXE` direct-entry、不建立 batch interpreter、DRAFT／READY、
   翻譯、字型、覆蓋或 dosgolem 修改。回填檔案雜湊、限制與下一個需使用者決定的問題。

## 退出條件

- [x] frame 來源、輸出 metadata 與本機座標格 PNG 可重現，且原版／衍生像素不受 Git 追蹤。
- [x] 視覺清冊、已確認控制／退出證據、按鈕語意與動態文字證據明確分離。
- [x] 沒有新座標注入、OCR、DRAFT／READY、翻譯、字型、覆蓋實作或 dosgolem 修改。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。

## 結果

由既有完整 composite frame 收據產生的本機座標格 PNG 是
`workplace/reports/goal051-opening-frame-coordinate-grid-x2.png`，SHA-256
`24abdb08a2d7c72c22f80e19999fd1638cb345e447ee84f928e822571a412f7c`；其 metadata 是
`workplace/reports/goal051-opening-frame-coordinate-grid.json`，SHA-256
`aa81ec34a37cfda4c16f5f12e8f4cc83bbc85f90014c164e54a71e4997097a56`。兩者只留在 gitignore
`workplace/reports/`，不提交原版或衍生像素。

| 推論等級 | 範圍與觀測 | 結論 |
| --- | --- | --- |
| confirmed | indexed frame／palette／state 的 SHA-256 分別為 `304ffd302045969ddad4a6c5e3c139a1af5f9f1bdbc1a060600b981ef26faeaf`、`000ee1dfbfba6afc159d4e39dca09e5202e68bebc931cd4d50bfb3f998e1f1e3`、`c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba`。metadata 綁定 DOS manifest、隔離 dosgolem commit `1435f175e785ea096a9268cd1021a4222300bd43` 與 #5,465,772 state。 | PNG 來源和版本可回查；它是既有正常開場畫面的本機衍生檢視。 |
| confirmed | Python 3.11.2 標準函式庫 PNG encoder 產出 672×432 RGB PNG：畫面本體是 320×200 的 2 倍放大，logical 格線每 16 pixels、座標標示每 32 pixels。PNG signature 與尺寸已由獨立檢查驗證。 | 座標格可供使用者指定或排除下一個操作位置，但不是遊戲介面證據。 |
| confirmed（視覺限制） | 本輪只檢視本機圖片；未進行 OCR、原文轉錄、控制項辨識、輸入注入或狀態轉移。既有 `(160,100)` 中央左鍵只已有「非文字退出」的獨立證據。 | 格線位置、畫面外觀與既有退出路徑都不能被升格為按鈕語意、正常玩家路徑或動態文字證據。 |
| unknown | 任何其他可操作區域、其座標語意、輸入後狀態、`VICEROY.EXE` 轉交與動態文字輸出。 | 下一個輸入實驗須由使用者先依畫面選擇正常操作意圖；不自行掃描或注入座標。 |

本輪產圖器是一次性本機工具，未加入儲存庫；所有容器無網路、原版輸入唯讀、以 UID/GID 1000:1000 執行。
