# 目標145：文本清冊與覆蓋率報表（Issue #7）

狀態：完成；開始與完成：2026-09-26。對應 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)，依[規格033](../spec/033-dynamic-text-model-draft.md)的資料模型。

## 做法

`tools/coverage_report.py` 在容器內讀九份譯稿 TSV、原版檔案與各目標的同輸入重播收據，重跑即得相同報表：

- **已抽取**：TSV 列的檔案 SHA-256、位移、長度與片段 SHA-256 和原版逐字核對通過。
- **已翻譯**：已抽取且譯文非空。
- **正常路徑中文顯示**：目標136、138～143 與全面回歸收據中，前端實際套用過中文的鍵（海上兩層另以參考實作追到的詞典鍵計入）。
- **命中但未建檔**：規格033 參考實作在三條正常路徑探針中歸不到任何鍵的字串。
- **重複／別名**：同一英文原文出現在多筆清冊列。

含英文原文的明細只寫到已忽略的 `workplace/reports/goal145-coverage/detail.json`；可公開的摘要只含數量與鍵（`summary.json`，SHA-256 `23c8a1c0bb79443b4e0201f638cc5f765ce411ffb1dfd84c07725c9e2bb265db`）。

## 2026-09-26 結果

| 清冊 | 列數 | 已抽取 | 已翻譯 |
|---|---:|---:|---:|
| draft.zh-Hant.tsv | 379 | 379 | 379 |
| colony-bilingual.tsv | 173 | 173 | 173 |
| pedia-bilingual.tsv | 163 | 163 | 163 |
| help-bilingual.tsv | 24 | 24 | 24 |
| build-caption-values.zh-Hant.tsv | 24 | 24 | 24 |
| sea-status.zh-Hant.tsv | 24 | 24 | 24 |
| nation-card-fragments.zh-Hant.tsv | 8 | 8 | 8 |
| nation-introduction.zh-Hant.tsv | 8 | 8 | 8 |
| readme-bilingual.tsv | 7 | 7 | 7 |
| **合計** | **810** | **810** | **810** |

- 正常路徑中文實際顯示：73 個鍵；探針追到的來源鍵 29 個（只涵蓋字幕、help、海上三條路徑的探針）。
- 命中但未建檔：17 種字串，多為目標143 以前只記偶數位讀取、無法還原的狀態欄字串，以及圖示字母 `-`、`S`、Discoverer 版 `@BUILD2`。
- 重複／別名：61 組（例如同一詞同時在百科與名稱表）。

## 缺譯紀錄

所有正式欄位缺譯時都保留原文並在輸出 JSON 記錄原因（各欄 `reason`，海上欄另有 `sea_misses`），沒有靜默遺漏。

## 限制

「已翻譯」是草稿層級，不等於畫面顯示；分母只含已建清冊的來源，全遊戲玩家可見文字的總分母屬 #27。
