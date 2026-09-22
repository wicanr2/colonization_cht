# 目標069：百科「職業」整段譯稿

狀態：in_progress；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#10](https://github.com/wicanr2/colonization_cht/issues/10)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

本切片只處理固定 `PEDIA.TXT` 的 `@JOB0` 至 `@JOB26` 共27篇職業百科文章。既有94篇
資料必須完整保留；完成後由同一原版重生為121篇雙語草稿。職業、產物、建築需求與
工作效果只翻譯顯示文字，不修改原版規則、資料或存檔。

## 工作與退出條件

1. 每篇保留可回查的原始檔SHA、章節／文字檔案位移、長度、片段SHA、英文原文與繁中
   譯文；跨行文章保留字面 `\\n`。
2. 精確保留 `^`、`{}`、`%%`與變數占位符。職業、殖民、原住民與宗教相關用語維持
   `draft`，不把暫定譯語外推成已確認的術語表。
3. 在 Docker 以固定原版重跑來源、鍵、欄位、控制碼、占位符與 Cubic 11 24px 字型覆蓋；
   預期筆數為121，任一不符即失敗。

本切片不處理另外42篇百科文章、EXE、靜態圖文或畫面覆蓋。資料驗證不能取代dosgolem
輸出事件、安全矩形、Ebitengine畫面或正常玩家路徑驗收。

## 完成收據

完成時，`text/pedia-bilingual.tsv` 與既有建立器、回歸測試、字型覆蓋檢查應可在 Docker
重生並驗證121篇資料。結果寫入 `RESEARCH-LOG.md`、`WORKLOG.md`、`CONTEXT.md` 和
`docs/worklist.json`；README 只在穩定語料現況改變時更新，不列本輪目標。
