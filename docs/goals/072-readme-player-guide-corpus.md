# 目標072：版本 3 玩家補充說明譯稿

狀態：completed；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

本切片只處理使用者提供第一份 DOS ZIP 的
`SMColoni/COLONIZE/README.TXT` 中，能協助玩家理解遊戲功能的版本 3 補充說明。來源 ZIP
與成員檔保持唯讀；成員檔 SHA-256 固定為
`d78a219bfd041e3d4f3327d6b012dc433fd3734472c68cbace0490b9e46ac19e`。

以原始成員檔位元組範圍建立七則原文／繁中雙語草稿：

- 版本 3 前言（`0x0000`–`0x0180`）與 16 項修正（`0x0180`–`0x0712`）。
- 地圖編輯器補充說明（`0x0b76`–`0x0e7e`）。
- 作弊模式總覽、警告與啟閉方式（`0x0e7e`–`0x10a0`）。
- 主地圖、殖民地畫面與歐洲畫面的作弊功能說明（依序
  `0x10a0`–`0x176b`、`0x176b`–`0x19f8`、`0x19f8`–`0x1a79`）。

譯稿只保存於私有儲存庫的新 `text/readme-bilingual.tsv`。每列記錄 ZIP 成員、成員 SHA-256、
範圍起點、長度、原始片段 SHA-256、英文、繁中、狀態與限制。該資料格式只用於追溯說明
文件，不是執行期訊息鍵或畫面覆蓋規格。

## 明確排除

- 當年 DOS 的 `CONFIG.SYS`／`AUTOEXEC.BAT`、`EMM386`、記憶體與音效卡排錯、客服電話；它們是
  已過時的技術支援資訊，不是遊戲操作說明。
- 任何 ZIP 解包輸出、原版檔案修改、遊戲規則、存檔、作弊行為或 runtime 掛鉤修改。
- 以 README 譯稿宣稱已畫面顯示、已命中或已完成說明文字中文化。

## 工作與退出條件

1. 寫入受限建立器與回歸測試：從 ZIP 成員唯讀重建七列，拒絕未知成員、範圍越界、重疊範圍、
   來源雜湊或片段雜湊不符、遺漏譯文，以及未逐序保留必要按鍵／符號。
2. 將七則經校對的繁中譯稿寫入 TSV；`Alt-W`、`Alt-I`、`Alt-N`、`Shift-F1` 至 `Shift-F7`、
   `T`、`S`、`$`、`%`、`^`、`!`、`[`、`]`、`Space` 等操作字面值不得被翻譯、遺漏或改序。
3. 在 Docker 以唯讀 ZIP 重跑建立器與既有 help／百科回歸，並以 Cubic 11 24px 報告所有七列的
   字型覆蓋。缺字、控制字面值或來源不符即失敗。

## 完成收據

- `text/readme-bilingual.tsv` 已由唯讀 ZIP 重建七則 `draft`。建立器鎖定封存檔 SHA-256
  `8aa93f219a6166712933bc60e402fe78024df1de821605c3036e1ae14e619867`、README 成員 SHA-256、
  七個不重疊的位元組範圍與每段片段 SHA；不符即拒絕。
- 建立器的六項無原版單元測試，以及主譯稿、help、百科與 README 合計34項回歸均通過。
  所有368筆主譯稿、24則help、163篇百科與本輪7則 README 固定來源也已由 Docker 重新驗證。
- `rich2-py:latest` 使用 Cubic 11、24px 審核的本機忽略收據
  `workplace/reports/goal072-readme-review.json` 顯示7則來源／控制通過、缺字0；
  `runtime_display_verified` 為 false。

本目標只代表七則 README 說明已成為可追溯 `draft`；它們仍沒有 dosgolem 輸出事件、中文安全矩形、
Ebitengine 視窗截圖或正常玩家路徑收據。
