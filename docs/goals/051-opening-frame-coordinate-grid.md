# 目標 051：開場畫面座標格視覺清冊

狀態：in_progress<br>
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

- [ ] frame 來源、輸出 metadata 與本機座標格 PNG 可重現，且原版／衍生像素不受 Git 追蹤。
- [ ] 視覺清冊、已確認控制／退出證據、按鈕語意與動態文字證據明確分離。
- [ ] 沒有新座標注入、OCR、DRAFT／READY、翻譯、字型、覆蓋實作或 dosgolem 修改。
- [ ] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
