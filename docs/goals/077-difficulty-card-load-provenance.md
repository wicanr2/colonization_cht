# 目標077：查明第一張難度卡片文字的原始檔載入邊

狀態：in progress；日期：2026-09-23。承接[目標075](075-difficulty-card-source-to-pixels.md)、
[目標076](076-difficulty-card-reversible-prototype.md)與
[規格016](../spec/016-difficulty-card-text-draft.md)；對應 Issue
[#6](https://github.com/wicanr2/colonization_cht/issues/6)、
[#7](https://github.com/wicanr2/colonization_cht/issues/7)及
[#26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 問題與範圍

正常玩家路徑已證明執行期 `Discoverer`、`Easiest` 經字形常式畫在第一張難度卡片上，
但 `Discoverer` 同時出現在 `GAME.TXT` 和 `NAMES.TXT`；僅憑文字相同不能決定正式
TSV 顯示鍵。本輪只追固定原版中「原始 TXT 的 DOS 讀取 → 記憶體載入／轉存 →
目標075的執行期原文地址」這段缺口，不接入正式覆蓋。

## 工作與退出條件

1. 以 dosgolem 同一組九筆正常玩家輸入，唯讀收集 `GAME.TXT`、`NAMES.TXT`、
   `LABELS.TXT` 的 `AH=3Fh` 成功讀取收據（檔名、檔案偏移、目的 `DS:DX`、
   位元組數、步數），並對 `0x4CC6A`、`0x4DF90` 周邊建立單一寫入觀測器。
   DOS 服務使用 `WriteBytes` 時不假稱 `WatchWrites` 必然捕捉；須交叉核對讀後 RAM。
2. 比對每個候選檔案的原始位元組範圍、讀入位置、轉存寫入者和目標075的
   `0E2D:11CF` 消費者；每個已確認的邊都附原始檔 SHA、檔案位移、DOS 真實模式
   指令地址或服務、20-bit 線性 RAM 及兩次重播結果。不能閉合的邊明列未知。
3. 兩次探針不得改變最終 RAM／原始畫布／索引畫面／色盤；檢查器要拒絕僅有同文
   卻沒有載入／轉存證據的聲明。若能閉合來源，更新規格016的候選鍵；若不能，
   維持 DRAFT 與原文回退。不得因此外推其他卡片或宣稱中文正式顯示。
4. 在 Docker 完成重播與清理，原版／完整 RAM／像素收據只留本機；更新現況、
   研究／工作紀錄、私有 GitHub 儲存庫與對應 Issue。

## 停止線

不修改原版 TXT、dosgolem 上游或正式 `live_menu.go`。`d.Reads`／`FileOps` 只是 DOS
服務收據；若檔案先讀入別處，必須另證轉存，不能以檔案曾被開啟或同字串推斷來源。
