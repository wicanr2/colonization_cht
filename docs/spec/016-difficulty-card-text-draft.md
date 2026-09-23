# 規格016：難度卡片文字輸出定位

狀態：DRAFT；日期：2026-09-23。入口：[目標063](../goals/063-difficulty-card-text.md)、
[目標074](../goals/074-difficulty-card-observation-repair.md)、
[目標075](../goals/075-difficulty-card-source-to-pixels.md)。

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
  `0x4CC6A`，`Easiest` 位於 `0x4DF90`。`Discoverer` 同時出現在 `GAME.TXT` 與
  `NAMES.TXT`；`Easiest` 出現在 `LABELS.TXT`。實際畫面 consumer 已由目標075追到，
  但從哪個原版 TXT 載入 `Discoverer` 的檔案邊仍**未知**。
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
- 目標075的雙次原版追蹤已把上述來源讀取連到第一張卡片的文字畫布寫入；
  原始位址與中間緩衝詳見下節。舊「可能只有靜態圖像」假說不再適用於這兩行。
  `GAME.TXT` 與 `NAMES.TXT` 的同文譯稿仍不可任選為正式鍵。

## 目標075：第一張卡片的直接資料流與版面

- confirmed（DOS 20-bit 線性 RAM／原始 `CS:IP`）：`0E2D:11CF` 讀取
  `0x4CC6A` 的 `Discoverer\0` 後，`0E2D:11EB` 在同一步把原文字元複製至
  `0x2A74C` 起的共用緩衝；副標 `0x4DF90` 的 `Easiest\0` 也走相同複製路徑。
  第一段在後續顯示路徑被整理為 `DISCOVERER:`，不是直接顯示來源檔的小寫混合形式；
  副標維持 `Easiest`。`0E2D:11A5` 分別把這兩個實際顯示位元組序列複製到
  `0x2A6B0` 起的局部副本。
- confirmed（同一印字呼叫）：`0D21:00C6` 從局部副本逐字讀取
  `DISCOVERER:\0` 和 `Easiest\0`，各有兩次完整遍歷；同常式的 `0D21:012C`
  對第一行有192次、第二行有100次原始畫布值變更寫入。這閉合了來源 → 緩衝 →
  局部副本 → 字形迴圈 → 像素的正常玩家路徑；不是用截圖的文字外觀倒猜鍵。
- confirmed（320×200 原始畫布）：兩次繪製入口的 `(AX,DX)` 為稱號 `(142,45)`／`(141,45)`，
  副標 `(151,53)`／`(150,53)`；字形墨跡差分分別是164點、bbox
  `(141,45)–(182,49)`（5個原始像素高）與83點、bbox `(150,53)–(174,58)`
  （6個原始像素高）。兩行之間的畫布快照完全相同；每次前後的所有變更均在
  第一張卡片觀測區 `(128,40)–(195,63)` 內。`DX` 與墨跡頂列相同，
  可以當頂列錨點；是否另有字型基線參數仍未證實，不能把墨跡底列冒稱為基線。
- confirmed（背景）：兩行文字下方的候選內矩形在原版繪製前分別有75及78種色盤索引，
  屬於有紋理的卡片圖像，不可用單一純色抹除英文。相同玩家狀態下的繪製前快照
  可逐像素恢復兩行原始背景，但正式覆蓋尚未建立可重播的背景擷取／游標遮擋守門。
- unknown（中文顯示）：上述5與6像素是原版墨跡高度，不是可直接套用的全域中文字級。
  放大四倍後仍須分別量測譯文的字型墨跡、基線／頂列、安全矩形、內距與最長文案；
  不得把主選單的 Cubic 11 24px 套到此卡片，也不得把這兩行計入八段已顯示中文。

## READY 前缺口

須為固定版本建立格式化後的穩定顯示鍵與缺譯回退守門，驗證原版來源檔的載入邊、
兩行有紋理背景的執行期可逆擷取、游標遮擋與欄位安全矩形；再依各自5／6像素原版
墨跡高度測試中文字級、頂列／基線對齊及最長譯文。其餘難度卡片仍要逐張確認，
不能外推第一張。只有這些守門可獨立核對時
才能升 READY。此 DRAFT 不授權新增正式覆蓋、修改原版資料或聲稱卡片中文化。

本機完整收據：`workplace/reports/goal063-card-writes.json` 與
`workplace/reports/goal063-card-reads.json`；對應 `.canvas`／`.idx` 中間物
不納入 Git。訂正收據為 `goal074-card-observer-a.json` 與
`goal074-card-observer-b.json`，由 `tools/check_difficulty_observer.py` 驗證；
兩份收據除輸出檔路徑外事件、檢查點與最終狀態一致，原始快照仍只保留本機。
目標075另有 `workplace/reports/goal075-card-flow-v5-a.json`／`-b.json`；
`tools/check_card_flow.py` 驗證雙次原文、兩層緩衝、逐字字形讀取、兩行像素與畫布差分。
完整 JSON 含原版局部指令與快照，故只保留在已忽略的本機研究目錄。
