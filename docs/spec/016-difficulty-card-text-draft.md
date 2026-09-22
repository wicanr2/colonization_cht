# 規格016：難度卡片文字輸出定位

狀態：DRAFT；日期：2026-09-22。入口：[目標063](../goals/063-difficulty-card-text.md)。

## 固定輸入與地址空間

合法 DOS 版 `OPENING.EXE` SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；
`VICEROY.EXE` SHA-256
`a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`；
`GAME.TXT` SHA-256
`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
`LABELS.TXT` SHA-256
`e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`。
工具：隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`、
`colonization-research:20260920-r2` 與 `tools/probe_difficulty_writes.go`。
以下 `0x4...` 是 DOS 20-bit 線性記憶體位址；畫布座標為 320×200 邏輯像素，
並非檔案位移或 IDA 位址。

## 已證實與未知

- confirmed：正常玩家滑鼠路徑的既有最終 RAM 中，`Discoverer` 位於線性
  `0x4CC6A`，`Easiest` 位於 `0x4DF90`。同文也在原版文字檔候選中；
  兩者的檔案來源、載入邊及實際畫面 consumer **未知**。
- confirmed：兩次獨立 dosgolem 重播於 2,980 萬步附近，在第一張卡片的
  原始畫布區出現 224 點差分，bbox `(141,45)–(182,58)`；最終完整 RAM、
  索引畫面、色盤與畫布雜湊一致。畫面可見 `Discoverer`／`Easiest`，
  但差分不證明兩個 RAM 候選就是輸出來源。
- confirmed：從冷啟動至 3,200 萬步，對線性 `0x4CC6A..0x4CC74` 與
  `0x4DF90..0x4DF97` 的 dosgolem `WatchReads` 均無命中；
  對原始畫布第一張卡片區 `(128,40)–(196,64)` 的 `WatchWrites` 也無命中，
  儘管檢查點畫布有差分。這僅說明現有監看介面未觀測到該路徑，
  **不能**斷言原版沒有讀取或寫入，也不能推定字是靜態圖像。
- hypothesis：可能經其他來源副本、畫布批次複製或圖像／sprite 輸出；
  目前沒有足夠證據選定其中任何一條。`GAME.TXT` 與 `NAMES.TXT` 的同文
  譯稿不能直接當本畫面的正式鍵。

## READY 前缺口

須在固定版本與正常玩家路徑追到本卡片的可重播輸出事件，區分動態印字與
已烘入圖像文字；驗證兩行各自來源、原文、畫布／圖像定位、可逆背景與中文
安全矩形，並檢查選中其他難度卡片及游標遮擋。只有這些守門可獨立核對時
才能升 READY。此 DRAFT 不授權新增正式覆蓋、修改原版資料或聲稱卡片中文化。

本機完整收據：`workplace/reports/goal063-card-writes.json` 與
`workplace/reports/goal063-card-reads.json`；對應 `.canvas`／`.idx` 中間物
不納入 Git。
