# 規格016：難度卡片文字輸出定位

狀態：DRAFT；日期：2026-09-23。入口：[目標063](../goals/063-difficulty-card-text.md)、
[目標074](../goals/074-difficulty-card-observation-repair.md)。

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
- 訂正（目標074）：舊探針連續呼叫 `Machine.WatchWrites`、`Machine.WatchReads`，
  而這兩個介面各只保存最後一次註冊；舊卡片監看被標題／提示監看覆蓋。
  上述「零命中」只屬失效探針的歷史結果，**不是**原版沒有讀寫的證據。
- confirmed（修正後來源讀取）：兩次獨立正常玩家冷啟動在步數 `29,797,568`，
  於原始位址 `0E2D:11CF` 依序讀取 DOS 線性 `0x4CC6A..0x4CC74` 的
  `Discoverer` 與尾端 NUL；在步數 `29,813,172` 於同一原始位址讀取
  `0x4DF90..0x4DF97` 的 `Easiest` 與尾端 NUL。這是執行期來源讀取，
  仍未證明文字究竟從 `GAME.TXT` 或 `NAMES.TXT` 載入。
- confirmed（修正後畫布寫入）：原始位址 `0D21:012C` 在第一張卡片區有292次
  值變更寫入，步數 `29,798,340..29,819,570`，bbox `(141,45)–(182,58)`；
  第一串讀取後、第二串讀取前有192次，第二串讀取後有100次。
  標題／提示讀寫位置也同時命中，證明單一監看分流沒有再丟掉原有觀測。
- 強推論：兩串執行期原文依序供給第一張卡片的兩行逐像素文字輸出；
  時序、文字、位置及畫布差分彼此相符，但尚欠來源讀取至 `0D21:012C`
  的直接呼叫／資料流鏈與逐行安全矩形。舊「可能只有靜態圖像」假說不再適用
  於這兩行；`GAME.TXT` 與 `NAMES.TXT` 的同文譯稿仍不可任選為正式鍵。

## READY 前缺口

須把 `0E2D:11CF` 兩次讀取連到 `0D21:012C` 的對應逐行畫布寫入，驗證原文
與版面因果鏈、原版字級／基線、可逆背景、中文安全矩形及欄位專屬中文字級，
並檢查其餘難度卡片及游標遮擋。只有這些守門可獨立核對時
才能升 READY。此 DRAFT 不授權新增正式覆蓋、修改原版資料或聲稱卡片中文化。

本機完整收據：`workplace/reports/goal063-card-writes.json` 與
`workplace/reports/goal063-card-reads.json`；對應 `.canvas`／`.idx` 中間物
不納入 Git。訂正收據為 `goal074-card-observer-a.json` 與
`goal074-card-observer-b.json`，由 `tools/check_difficulty_observer.py` 驗證；
兩份收據除輸出檔路徑外事件、檢查點與最終狀態一致，原始快照仍只保留本機。
