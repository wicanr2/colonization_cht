# 目標065：百科「建國元勳」整段譯稿

狀態：completed（限定25篇建國元勳草稿）；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#10](https://github.com/wicanr2/colonization_cht/issues/10)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

`PEDIA.TXT` 明確有163個編號文章區塊；本切片只處理其中25篇
`@FATHER0` 至 `@FATHER24` 的建國元勳介紹與遊戲效果文字。
文章跨多行且有 `^`、`{}`、`%%` 等格式符號，不能塞進只接受單行候選的
`text/draft.zh-Hant.tsv`。將建立與既有 help 草稿同等的「整段雙語草稿」來源，
但它不是正式執行期鍵，也不得同時驅動輸出層。

## 工作與退出條件

1. 以固定 `PEDIA.TXT` 雜湊與每篇文章的章節／文字位移、長度及片段指紋，
   建立25篇可重生的雙語資料列；文章標題、傳記和遊戲效果都要保留可回查關係。
2. 翻譯保留所有原始變數、`^`、大括號、百分比與必要專名。殖民歷史用語、
   原住民稱呼與遊戲術語如需術語政策，保持 `draft` 並在註記說明，不假裝定稿。
3. 用固定原版重跑來源與片段SHA、UTF-8、唯一鍵、欄位、控制碼、占位符及字型覆蓋；
   只通過這些資料驗證不代表文章已在遊戲畫面中文化。

本切片不處理其他138篇百科文章、EXE或靜態圖文，不改原版檔案、規則、存檔或畫面覆蓋。

## 完成收據

`text/pedia-bilingual.tsv` 由固定 `PEDIA.TXT` 重生25篇完整資料列，包含章節與文字
位移、原始檔與片段SHA-256、英文原文、繁中草稿與狀態。`tools/build_pedia_bilingual.py`
驗證每一篇的來源、鍵、UTF-8、`^`、大括號、百分比跳脫與占位符；
`tools/review_pedia_bilingual.py` 以已確認的 Cubic 11 24px 量測字型覆蓋。
三項回歸測試及資料驗證均通過，25／25篇沒有缺少字形。

這是來源與譯文品質收據，不是畫面收據。文章文字尚未取得 dosgolem 輸出事件、
安全矩形、變數實值或 Ebitengine 截圖；歷史與術語敘述也維持 `draft`。
