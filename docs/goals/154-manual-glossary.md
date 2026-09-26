# 目標154：依第三波說明書建立術語表（Issue #27 第一輪）

狀態：進行中；開始：2026-09-26。對應 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)；術語政策依[目標148](148-font-terms-scope-decisions.md)使用者決定「第三波中文版說明書優先」。

## 範圍

- 在 Docker 內把 `第三波-殖民帝國.rar` 解包到已忽略的 `workplace/original/manual/`；掃描影像與說明書原文不入 Git。
- 逐頁讀說明書掃描，抽出遊戲專有名詞的英文原文與第三波譯名，記頁碼（影像檔名）與證據等級，建立 `text/glossary.zh-Hant.tsv`。只收術語對照，不收說明書段落。
- 以術語表核對既有十份譯稿，列出與說明書譯名不一致的條目；本輪只列衝突，不改譯稿。

## 退出條件

- 術語表可由影像檔名回查；每筆有英文、第三波譯名、出處頁、證據等級。
- 衝突清單可重跑（`tools/check_glossary.py`）。
