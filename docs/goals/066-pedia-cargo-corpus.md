# 目標066：百科「貨物」整段譯稿

狀態：completed（限定16篇貨物草稿）；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#10](https://github.com/wicanr2/colonization_cht/issues/10)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

本切片承接目標065，僅處理 `PEDIA.TXT` 的 `@CARGO0` 至 `@CARGO15`：食物、原料、
製成品、貿易品、工具與火槍共16篇整段百科文字。既有 `text/pedia-bilingual.tsv`
會由固定原版檔重生為41篇（原25篇建國元勳加本16篇貨物）可回查的雙語草稿；它
仍不是執行期鍵，不能直接驅動輸出覆蓋。

## 工作與退出條件

1. 每篇保留固定 `PEDIA.TXT` 雜湊、章節／文字位移、長度與片段 SHA-256；英文與繁中
   段落以 UTF-8 TSV 的同一列相連。
2. 譯文精確保留 `^`、`{}`、`%%`、變數占位符與段落換行，並維持遊戲中貨物、職業、
   地形及效果的語意；術語尚未經使用者定案，一律標示 `draft`。
3. 以固定原版重跑來源、唯一鍵、欄位、控制碼、占位符與 Cubic 11 字型覆蓋驗證，
   並以41篇為預期筆數。任何一項不符即失敗，不以人工修補來源資料掩蓋。

本切片不處理其餘122篇百科文章、EXE與靜態圖文；不改原版檔案、規則、存檔或
dosgolem 顯示行為。通過資料驗證不代表已取得原版輸出事件、中文安全矩形、
Ebitengine 截圖或畫面中文化。

## 完成收據

完成時，`text/pedia-bilingual.tsv`、`tools/build_pedia_bilingual.py`、
`tools/test_pedia_bilingual.py` 與 `tools/review_pedia_bilingual.py` 應能在 Docker
中重生並驗證41篇資料，且目標字型沒有缺字。完成結果應寫入 `RESEARCH-LOG.md`、
`WORKLOG.md`、`CONTEXT.md` 與唯一工作清單；README 不記錄本輪流水帳。

## 完成收據

固定原版重生後，`text/pedia-bilingual.tsv` 含41篇：既有25篇 `@FATHER` 與本批16篇
`@CARGO`。建立器確認每列的原始檔與片段 SHA、欄位、唯一鍵、字面 `\\n`、`^`、
`{}`、`%%`及占位符；4項合成回歸測試也通過。`review_pedia_bilingual.py` 以已確認
的 Cubic 11 24px 字型測得41／41篇無缺字。

這是語料品質收據，不是畫面收據。16篇貨物文章仍沒有 dosgolem 輸出事件、中文安全
矩形、Ebitengine 截圖或正常玩家路徑命中；全數維持 `draft`，PEDIA另有122篇文章未譯。
