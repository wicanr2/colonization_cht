# 目標154：依第三波說明書建立術語表（Issue #27 第一輪）

狀態：完成；開始與完成：2026-09-26。對應 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)；術語政策依[目標148](148-font-terms-scope-decisions.md)使用者決定「第三波中文版說明書優先」。

## 範圍

- 在 Docker 內把 `第三波-殖民帝國.rar` 解包到已忽略的 `workplace/original/manual/`；掃描影像與說明書原文不入 Git。
- 逐頁讀說明書掃描，抽出遊戲專有名詞的英文原文與第三波譯名，記頁碼（影像檔名）與證據等級，建立 `text/glossary.zh-Hant.tsv`。只收術語對照，不收說明書段落。
- 以術語表核對既有十份譯稿，列出與說明書譯名不一致的條目；本輪只列衝突，不改譯稿。

## 退出條件

- 術語表可由影像檔名回查；每筆有英文、第三波譯名、出處頁、證據等級。
- 衝突清單可重跑（`tools/check_glossary.py`）。

## 結果

- 解包：`tools/Dockerfile.manual`（`colonization-manual:20260926`，只加 `unar`）以 `--network none` 解出 86 檔到 `workplace/original/manual/`；檔案清單 SHA-256 在 `workplace/original/manual/manifest.sha256`。
- 術語表 `text/glossary.zh-Hant.tsv`：1,044 列，欄位 `en, zh, image, manual_page, category, evidence`。證據：印出對照 665、僅中文 340、僅英文 36、辨識不確定 3。84 張影像分四段由子代理逐頁判讀；抽樣兩張（Image010、Image044）逐項對回原頁無誤。
- 說明書本身的誤植照印保留（例如 Adem Smith、Scntry、Tabacco）；同一英文的多個譯名全部保留，定稿時擇一。
- 衝突檢查 `tools/check_glossary.py`：537 組印出對照的英文（排除歷史背景名詞）對十份譯稿，列出英文含術語但譯文未用說明書任一譯名的列。

| 清冊 | 列數 | 含術語 | 衝突候選 |
|---|---:|---:|---:|
| draft.zh-Hant.tsv | 379 | 187 | 122 |
| pedia-bilingual.tsv | 163 | 159 | 143 |
| colony-bilingual.tsv | 173 | 50 | 46 |
| help-bilingual.tsv | 24 | 24 | 22 |
| nation-introduction.zh-Hant.tsv | 8 | 8 | 7 |
| sea-status.zh-Hant.tsv | 24 | 12 | 6 |
| readme-bilingual.tsv | 7 | 7 | 6 |
| build-caption-values.zh-Hant.tsv | 24 | 12 | 2 |
| nation-card-fragments.zh-Hant.tsv | 8 | 8 | 1 |
| static-overlay.zh-Hant.tsv | 7 | 0 | 0 |
| 合計 | 837 | 467 | 355 |

摘要（只含鍵與術語對照）只在已忽略的 `workplace/reports/goal154-glossary/summary.json`；含英文原文的明細在同目錄 `detail.json`。

## 解讀與下一步

- 衝突候選含大量雜訊：說明書對介面詞的描述性譯法（`Change=變更鈕`、`Zoom=切換畫面`）、地名中的普通字（殖民地名 `Fort …`）、泛用字（`People`、`Turn`）。不能直接批次替換。
- 下一輪先從術語表定出「定稿譯名」子集（單位、職業、建築、貨物、地形、船、建國之父、原住民族、國家），再逐列改譯稿並重跑正式欄位的字模與回歸。
