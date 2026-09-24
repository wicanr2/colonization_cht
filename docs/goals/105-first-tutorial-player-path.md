# 目標105：從國家介紹走向首則遊戲內教學訊息

狀態：進行中；日期：2026-09-24。承接[目標104](104-nation-introduction-exit-phase.md)
已驗的四國介紹 B 頁後離頁，以及[目標060](060-help-bilingual-corpus.md)
已建但尚未驗畫面的 help 雙語草稿；對應
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與界線

`text/help-bilingual.tsv` 已保存19則 `GAME.TXT:@TUTORIAL1–19` 與
5則 `MAPEDIT.TXT:@HELP1–5` 原文／繁中草稿，但沒有任何一則
dosgolem 正常玩家畫面命中。上一輪已在85M步抵達國家介紹後續
可見頁；本輪由此繼續真實按鍵，追查可否到首則教學訊息。
`@TUTORIAL1` 的原版檔案標記位移是 `GAME.TXT:0x1316A`，
文字位移 `0x13190`，目前**僅證實檔案來源**，不能當作輸出事件鍵。

本輪不變更原版 EXE／TXT、遊戲規則、存檔、正式 Ebitengine
中文圖層或四國介紹長文版式；沒有原版輸出事件與安全矩形前，
help 仍維持英文。原版、完整原文、索引畫布與中間收據只在
已忽略的 `workplace/`，不得加入 Git。

## 工作與退出條件

1. 核對 Git 作者、PRIVATE 遠端、Issue #7／#27、原版與輸入
   指紋、隔離 dosgolem 的 `upstream` 禁推設定。**先推送本目標**
   再改探針；分析、重播與畫面轉換只在限資源、無網路、非 root
   Docker，原版唯讀。
2. 從目標104英格蘭85M的同一正常玩家路徑出發，分別做無鍵
   與真實 Enter 的後續重播；明確記錄新輸入步數、100M前
   開檔、CPU／RAM、索引畫面、色盤與虛擬時間。必要時延長
   有界觀測，但不得注入座標或記憶體冒充玩家流程。
3. 若畫面實際命中教學，追 `GAME.TXT` 固定原始 bytes／DOS
   讀入／實模式印字／320×200畫布，核對兩次冷啟動與無讀寫
   監看控制，記錄原版文字幾何、字高及本機譯稿占位符。
   若未命中，記錄最窄的當前畫面與下一個可驗輸入，不把
   `@TUTORIAL1` 推測為已顯示。
4. 建立獨立失敗即關閉檢查：固定原版與玩家輸入 SHA、
   真實索引／畫布／色盤 bytes、控制組與負例；原版缺失須
   明確 SKIP。DRAFT 證據足夠才更新顯示規格；任何正式
   覆蓋需另經 READY 與真視窗同狀態驗證。
5. 修正 README／CONTEXT 中目標104後已過期的離頁現況，
   更新 RESEARCH-LOG、WORKLOG 與 `docs/worklist.json`，由
   工具重生 `WORKLIST.md`。推送私有成果、回讀相關 Issue，
   檢查原版未入 Git、輸出擁有權及 Docker 容器清理。

## 停止線

這次只在原版正常玩家路徑補 help 畫面入口；即使看見第一則，
也不能把24則譯稿一併宣稱為可見或已中文化。介紹長文版式
是獨立的使用者視覺決定，本輪不選擇候選字級。
