# 目標073：殖民地預設名稱雙語譯稿

狀態：completed；日期：2026-09-23。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

本切片只處理使用者提供第一份 DOS ZIP 的 `SMColoni/COLONIZE/COLONY.TXT`。固定成員 SHA-256 為
`2996f8a9d53a7f7a93e4a238bfd2ba727c4cf5cdabc334c4059c6860c9e4ae36`，大小 2,540 bytes。
它有173個預設名稱：英國36（其中18個附年份）、法國66、西班牙39、荷蘭32。

使用者已選定玩家可見的 `draft` 譯法：有年份者為「中文名稱（原名，年份）」；沒有年份者為
「中文名稱（原名）」。原始名稱、逗號及年份是穩定來源資料，絕不能使用中文譯文作查找、
存檔、規則或其他語意用途。

新 `text/colony-bilingual.tsv` 每列保存國籍章節、章節及資料行位元組位置、整行原始 SHA、
原始名稱、可選年份、繁中顯示譯稿、狀態與限制。建立器只接受 `名稱` 或 `名稱,四位年份`；
任何其他逗號資料、重複鍵、未知章節、來源雜湊不符、缺譯或不符使用者指定格式者皆失敗。

## 明確排除

- 原版 `COLONY.TXT` 的修改、名稱寫回、規則／查找／存檔資料、以及對原版「最多23字元」儲存限制的
  任何改變。
- 未有可靠繁中名稱依據時的任意杜撰；疑義項須保留原名並在譯稿註記，不以看似中文的音譯掩蓋不確定性。
- 將譯稿當作 dosgolem 輸出事件、中文安全矩形、字級、Ebitengine畫面或正常玩家路徑驗收。

## 工作與退出條件

1. 建立受限來源解析器與無原版回歸測試，核對固定 ZIP／成員、CRLF、四個章節、173筆記錄、
   行首／片段雜湊與年份欄位；解析器不得將整行複合資料錯當成可直接替換的字串。
2. 產生173筆原文／繁中草稿，逐筆驗證「中文（原名）」或「中文（原名，年份）」格式；年份不得
   遺漏或改值，原名不得由譯文鍵取代。
3. 以 Docker 的唯讀 ZIP 重跑建立器及既有全語料回歸；以字型 cmap 檢查繁中草稿可繪字元。
   此字型檢查不設定全域顯示字級：日後每個真正覆蓋欄位仍須依原版文字量測、安全矩形與最長譯文
   選定個別中文字級。

## 完成收據

- `text/colony-bilingual.tsv` 已由唯讀 ZIP 重建173筆 `draft`。建立器鎖定封存檔、成員檔、
  CRLF、四個章節、173筆計數、行首／片段 SHA、原名、年份與使用者指定的全形括號格式；
  不符即拒絕。
- 六項無原版單元測試及主譯稿、help、百科、README、殖民地名稱合計40項回歸通過。Docker 另以
  唯讀 ZIP 暫時解包，重驗368筆主譯稿、24則help、163篇百科、7則README與173筆名稱來源。
- `rich2-py:latest` 的本機忽略收據 `workplace/reports/goal073-colony-review.json` 顯示
  `source_and_format_passed: 173`、`rows_with_missing_glyphs: 0`。報告沒有設定字級，並明示
  `per_field_font_selection_verified: false` 與 `runtime_display_verified: false`。

本目標只可宣稱173筆可追溯 `draft`，不能宣稱名稱已在畫面替換或已有可用中文字級。
