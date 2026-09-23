# 目標074：修正難度卡片觀測並重驗輸出來源

狀態：completed；日期：2026-09-23。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#26](https://github.com/wicanr2/colonization_cht/issues/26) 與 [#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 起點與範圍

[目標063](063-difficulty-card-text.md)把難度卡片畫布與候選文字讀取的零命中列為觀測限制。
檢查固定的隔離 dosgolem 副本後，發現 `Machine.WatchWrites` 與 `Machine.WatchReads`
各只保存最後一次註冊；`tools/probe_difficulty_writes.go` 卻分別註冊兩次，先前的卡片監看
因此被後面的標題／提示監看覆蓋。這是探針缺陷，不是原版沒有讀寫的證據。

本輪只修本專案研究探針的監看佈線，在單一寫入回呼中分流畫布區域、在單一讀取回呼中
分流候選原文區域；不改 dosgolem、原版資料、難度規則或正式中文覆蓋。

## 工作與退出條件

1. 為多區域分流加入小型回歸測試或等價的可重跑檢查，證明卡片與既有標題／提示兩類
   觀測可在同一次註冊中並存；產出的收據須記錄監看版本與固定輸入雜湊。
2. 由唯讀合法 DOS 輸入及既有九筆正常玩家滑鼠收據，使用 dosgolem 重跑兩次；比較卡片文字
   候選讀取、原始畫布寫入、快照差分、最終 RAM／索引畫面／色盤與開檔結果。
3. 依新收據更新[規格016](../spec/016-difficulty-card-text-draft.md)與 `RESEARCH-LOG.md`，
   保留並訂正舊結論。若只取得其中一側或仍未連到同一輸出事件，維持 DRAFT 與英文回退；
   不以單一命中直接升 READY。
4. Docker 內完成探針測試與兩次收據核對；工作樹不追蹤原版素材、原始快照與字型，確認
   沒有殘留本專案容器或錯誤掛載目錄。完成後更新 Issue 與私有儲存庫。

## 停止線

若修正後仍無卡片監看命中，先檢查 dosgolem 是否有繞過 `Read8`／`Write8` 的批次複製路徑，
將缺口與可重現例子記錄為下一個窄任務；不得猜測文字是靜態圖，也不得把候選譯文直接接入畫面。

## 完成收據

- 修正後的 `tools/probe_difficulty_writes.go` 對讀取與寫入各只註冊一次，按位址與卡片／標題區域
  分流。`tools/check_difficulty_observer.py` 檢查註冊數、固定九筆輸入雜湊、兩次重播狀態、
  `Discoverer`／`Easiest` 原始位元組與卡片文字寫入；Docker 執行通過。
- 兩次獨立 dosgolem 正常玩家路徑均走到3,200萬步，`DIFFICUL.PIK` 確有開啟，完整 RAM、
  原始畫布、索引畫面、色盤及讀寫事件相同；四項最終雜湊亦與舊探針收據相同，
  修正只改觀測結果。執行期原文在步數 `29,797,568` 與
  `29,813,172` 被 `0E2D:11CF` 讀取；`0D21:012C` 在卡片區寫入292個變更像素，
  時間及 bbox 見[規格016](../spec/016-difficulty-card-text-draft.md)。
- 本機完整收據為 `workplace/reports/goal074-card-observer-a.json` 與 `-b.json`；兩份檔案各自
  記錄觀測版本與固定輸入，並由檢查器忽略各自不同的輸出路徑後比較。舊「零命中」已在
  `RESEARCH-LOG.md` 追加勘誤；未因此把規格升 READY，八段中文顯示計數不變。
