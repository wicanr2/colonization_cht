# 目標077：查明第一張難度卡片文字的原始檔載入邊

狀態：completed（僅本輪來源載入邊）；日期：2026-09-23。承接[目標075](075-difficulty-card-source-to-pixels.md)、
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
   DOS 服務使用 `WriteBytes` 時須實測 `WatchWrites` 是否捕捉，並交叉核對讀後 RAM。
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

## 結果與退出判定

- confirmed：兩次獨立冷啟動的 `goal077-card-load-v4-{a,b}.json` 位元組相同，
  SHA-256 為 `580f2f92475a12db9c065a3476e20f4fd315f27521030ac794dedf7aa3b71790`。
  九筆玩家輸入、3,200萬步終點與目標075的完整 RAM／畫布／索引畫面／色盤一致。
- confirmed：`NAMES.TXT` 檔案位移 `0xC0C` 的 `Discoverer` 在步數16,208,974
  讀入 DOS 緩衝，經 `0E2D:1F76`／`1F86` 就地整理、`0E2D:09F4`／`09F5`
  轉入中間緩衝，於步數16,215,523 由 `0E2D:11A5` 寫至線性 RAM `0x4CC6A`。
  `GAME.TXT` 首次讀取在步數21,820,870；它不是此固定路徑第一張卡片稱號的來源。
- confirmed：`LABELS.TXT` 檔案位移 `0x8A9` 的 `Easiest` 在步數18,648,994
  以同一組原版常式轉存，於步數18,682,724 寫至線性 RAM `0x4DF90`。
  目標075已將這兩個目標 RAM 位址接到字形與畫布像素。
- `tools/check_card_load.py` 拒絕只有同文、卻沒有 DOS 讀取與原版搬運事件的來源聲明。
  反向對照移除來源讀取事件後，檢查器如預期拒絕該聲明。
  `tools/prepare_card_preview.py` 的可丟棄預覽鍵已由 `GAME.TXT:0x00000A26`
  改為 `NAMES.TXT:0x00000C0C`；兩欄譯文與21／25px候選字級未改。
  Ebitengine 對照圖逐像素驗證通過，稱號／副標安全區分別變更2,752／1,860點，
  區外不變。這不是正式執行期中文覆蓋，規格016保持 DRAFT。

本機完整原版收據與 PNG 僅在已忽略的 `workplace/reports/goal077-card-*`；
可回查的輸入雜湊、工具版本、地址空間與重跑入口見
[RESEARCH-LOG.md](../../RESEARCH-LOG.md)及[規格016](../spec/016-difficulty-card-text-draft.md)。
