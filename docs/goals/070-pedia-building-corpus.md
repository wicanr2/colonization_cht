# 目標070：百科「建築」整段譯稿

狀態：in_progress；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#10](https://github.com/wicanr2/colonization_cht/issues/10)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

本切片只處理固定 `PEDIA.TXT` 的 `@BUILDING0` 至 `@BUILDING41` 共42篇建築百科文章。
既有121篇資料必須完整保留；完成後由同一原版重生為163篇雙語草稿，覆蓋目前已盤點的
所有 PEDIA 編號文章。建築、職業需求、產量、效果與殖民歷史敘述只翻譯顯示文字，
不修改原版規則、資料或存檔。

## 工作與退出條件

1. 每篇保留可回查的原始檔SHA、章節／文字檔案位移、長度、片段SHA、英文原文與繁中
   譯文；跨行文章保留字面 `\\n`，如有原始Tab則使用已確認的 `\\t` 逃脫。
2. 精確保留 `^`、`{}`、`%%`、Tab與變數占位符。建築、殖民、原住民與宗教相關用語
   維持 `draft`，不把暫定譯語外推成已確認的術語表。
3. 在 Docker 以固定原版重跑來源、鍵、欄位、控制碼、占位符與 Cubic 11 24px 字型覆蓋；
   預期筆數為163，任一不符即失敗。

本切片不處理 EXE、靜態圖文、其餘TXT資料或畫面覆蓋。163篇資料驗證不能取代dosgolem
輸出事件、安全矩形、Ebitengine畫面或正常玩家路徑驗收；也不能宣稱全遊戲翻譯完成。

## 完成收據

完成時，`text/pedia-bilingual.tsv` 與既有建立器、回歸測試、字型覆蓋檢查應可在 Docker
重生並驗證163篇資料。結果寫入 `RESEARCH-LOG.md`、`WORKLOG.md`、`CONTEXT.md` 和
`docs/worklist.json`；README 只在穩定語料現況改變時更新，不列本輪目標。
