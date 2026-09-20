# 規格草案 003：客體 MCB 鏈與 dosgolem 記憶體 arena 的重新協調

狀態：DRAFT（不授權實作）  
日期：2026-09-21  
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)  
前置收據：[目標 012](../goals/012-psound-overlay-writer-lifecycle.md)；前一個控制流收據：[目標 011](../goals/011-psound-clear-argument-provenance.md)

## 目的與嚴格邊界

本草案處理一個通用 DOS 執行器問題：客體程式可經 `int 21h AH=52h` 找到記憶體控制區塊（MCB）鏈，
直接修改其記憶體內容，再呼叫 `AH=48h`、`49h` 或 `4Ah`。dosgolem 目前將自己的記憶體
arena 發布成 MCB 鏈，但不會在上述服務邊界讀回客體對該鏈的有效修改；下一個服務呼叫會以過期
arena 回應，並以 `syncMCB()` 覆寫客體鏈。

本文件的目的是定義可審查的「鏈—arena 重新協調」契約，讓固定 `OPENING.EXE` 正常冷啟動得以
繼續取得下一個原版收據。它不是中文覆蓋、記憶體編輯器、完整 DOS 記憶體管理重寫，也不授權改動
`workplace/dosgolem`、原版檔、`INT 33h`、音效、DMA、PCM、PIT、DAC 或 IRQ。

只有本草案升為 READY 後，才可新增或修改 dosgolem 的服務行為。READY 前不得用針對 `1C43`、
`03D9`、`086C`、`PSOUND.COL` 或某個檔名的特例掩蓋差異。

## 固定輸入、工具與地址空間

| 項目 | 固定值／意義 | 等級 |
|---|---|---|
| 正式入口 | `OPENING.EXE`，SHA-256 `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` | confirmed |
| overlay | `PSOUND.COL`，48,599 bytes，SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87` | confirmed |
| 執行器 | `workplace/dosgolem` commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，upstream push URL `DISABLED` | confirmed |
| 動態收據 | `workplace/reports/probe-opening-086c-lifecycle-20260920.txt`，SHA-256 `4642d04be9a5df78cda90d2e2b43b4c902651712de1a2045b4ec9ad12f4c6d38` | confirmed |
| MCB 收據 | `probe-opening-mcb-lifecycle-20260920.txt` SHA-256 `3c2e7ea9d42bf0a02a6167d35ac3622ab4eba66a17b815e09cc4c78e232a38c8`；`opening-mcb-lifecycle-writes-20260920.tsv` SHA-256 `ae57b7037cd7d9089f97897e28811bb0b544158808f604991f9f53e6dc5a2bd7` | confirmed |
| IDA 匯出 | IDA Pro 9.4 image `ida-pro-9.4-idapython:locked-v1`；`ida-opening-086c-overlay-runtime-20260920.json` SHA-256 `ec997284cd45afc58a39d87b8fada14cb2cad856790d012a3894164f7db1d324`、`ida-opening-02b2-overlay-caller-20260920.json` SHA-256 `11e4826f75fe5d6afd866564b52690cc0f53673c42587641770979aa8e0af7b7`、`ida-opening-03d9-mcb-runtime-20260920.json` SHA-256 `80116e6722036591dea4586383b83ec6fe28517b4ab332faa2bab220a8b2cae5` | confirmed |

本文件的 `03D9:xxxx`、`086C:xxxx` 與 `02B2:xxxx` 都是這一次 DOS 執行期的段:位移。
IDA 匯出採從執行期記憶體取出的 raw-binary 視窗，JSON 每列同時保留 runtime 段:位移、原始 bytes
與匯出位址；它們不是 `PSOUND.COL` 檔案位移，也不可與線性位址混用。`0x4D`／`0x5A`、owner、size
等 MCB 欄位形狀則依 dosgolem 已有的 `docs/spec/012-mcb-chain.md`，本草案不以新名詞覆蓋原始位址。

## 已審查的原版與執行器證據

### 1. `086C` 是已證實的 overlay 載入呼叫者

正常冷啟動在第 834,304 指令由 `02B2:00AF` 呼叫 `086C:0004`，回到 `02B2:00B4`。IDA raw-binary
bytes 與動態暫存器交叉顯示下列序列：

| 步數／原始定位 | 觀測 | 等級 |
|---|---|---|
| 834,313–834,319；`086C:0011`–`002C` | 先以 `AH=48h, BX=FFFFh` 探測（回 `AX=8, BX=83BCh`），再以 `BX=83BAh` 配置，回傳資料段 `1C43`。 | confirmed |
| 834,339–834,342；`086C:004C`–`005B` | 設定 `ES:BX=0C41:3945` 的 parameter block：load segment 與 relocation factor 都是 `1C43`；`DS:DX=0C41:849C` 指向 `PSOUND.COL`，再以 `AX=4B03h` 呼叫 DOS。 | confirmed |
| 834,342；`086C:005D` | dosgolem 的 overlay 載入紀錄為 `PSOUND.COL → 1C43:0000`、relocation `1C43`、48,599 bytes；目標區開始被寫入。 | confirmed |
| 834,362–834,363；`086C:0092`–`0094` | `AH=4Ah` 將同一區塊調整為 `0C05h` 段後成功返回。 | confirmed |
| 834,405–834,406；`086C:00DA`–`00DB` | 從已載入段複製遠指標，寫入 `0C41:621A = 0BF9:1C43`。 | confirmed |

因而「`086C` 是透過 `AH=4Bh AL=03h` 載入 `PSOUND.COL` 的原始呼叫者」為 confirmed；並非僅由
目標段中出現程式碼推測。這不表示 overlay 後所有原版控制流或聲音行為均已解出。

### 2. 原程式會直接建立與操作客體 MCB 鏈

`03D9:02E4` 包裝器進入 `03D9:0138`，後者在 `03D9:0156` 呼叫 `0419:005A`。動態收據中，
`0419:005A` 於第 816,494 與 816,683 指令發出 `AH=52h`，取得 DOS 的 list-of-lists 結構；
`03D9:0138` 路徑最後回傳 `1C43:0000`，由 `03A7:000A` 寫入 `00C8 × 0140 = FA00h` 描述元。

同一段 raw bytes 的 `03D9:005A`–`007D` 直接寫入 MCB 欄位：`03D9:006D` 寫入 `0x4D`，
`03D9:0071` 寫入 size，`03D9:0075` 寫入 owner，並由 `03D9:007D` 回傳資料段。監看在第
816,657–816,661 指令看見 `1C42` 的簽章、size 與 owner 依此順序改變，後續亦寫入名稱區。這是
「客體程式直接修改 MCB 型態資料」的 confirmed 證據，不是假設 DOS 自動替它配置。

### 3. 現行 arena 與客體鏈在 `AH=49h` 邊界分歧

第 833,824 指令，`03D9:0340`–`0345` 以 `ES=2C9A` 發出 `AH=49h`。dosgolem 回 `AX=0009`，且隨後的
`syncMCB()` 將監看中的 `1C42` 改回既有 arena 所描述的全空閒區：owner 由 `01` 變 `00`、size
`0FA1h` 回 `83BCh`、名稱清空。接著第 834,319 指令 `086C` 的 `AH=48h` 便將資料段 `1C43` 再次
發出，並在第 834,342 指令把 overlay 寫進同一段。

這些結果證實「客體鏈的直接修改沒有被現行內部 arena 吸收，`AH=49h` 回錯後又重發佈過期鏈」；它們
不證實真 DOS 對每個 `ES=2C9A` 請求的精確回傳，也不授權把 `AH=49h` 無條件改成成功。第 1,114,003
指令的 `rep stosw` 隨後按原程式描述元清零 `1C43:0000`，與遠指標的舊目標相衝突；這是此差異的
可觀測後果，而不是本草案可直接修改的遊戲規則。

### 4. 現有 dosgolem 邊界

固定 commit 的 `internal/dos/int21.go` 在 `AH=48h`／`49h`／`4Ah` 服務後一律呼叫 `syncMCB()`；
`release()` 只從 Go 端 `arena` 尋找 `ES` 對應資料段，找不到就回 `AX=9`。`arena` 與 `freeSeg`
會儲存在 state，但沒有讀取客體 MCB 的反向匯入步驟。這是上述可重播差異的執行器側必要條件，
不是對其他 DOS 行為的泛稱。

## DRAFT 重新協調契約

下列是供證據審查的提案，尚未授權程式碼：

1. 記憶體服務邊界：在 `AH=48h`、`49h`、`4Ah` 處理前，dosgolem 必須能辨識目前客體可見的
   MCB 鏈是否已與內部 arena 分歧；不得先用過期 arena 回應、再以 `syncMCB()` 覆寫差異。
2. 鏈定位：實作不得硬編 Colonization 的段位址。必須由 dosgolem 已公開給客體的 list-of-lists／
   `AH=52h` 路徑取得鏈起點，並使用鏈上的下一段公式逐格前進。
3. 可接受鏈：只有在簽章、尺寸、單調前進、無迴圈、可配置範圍、終止記錄與 MCB 連續性均通過
   驗證時，才可把客體鏈轉成新的內部配置狀態。轉入時必須保留每格的原始段、owner、size 與
   free/allocated 判定，不能只把 `1C43` 特判成已配置。
4. 協調原子性：接受有效客體鏈後，該次 `AH=48h`／`49h`／`4Ah` 必須以協調後狀態運作，並只在
   服務完成後發布與新狀態相符的 MCB 鏈。失敗服務不得把尚未接受的客體資料悄悄重置為另一張
   地圖。
5. 失敗即關閉：鏈無效、範圍不符、owner 表意無法安全表示、或與目前行程／EXEC 所有權模型衝突時，
   實作必須保留客體 bytes、紀錄可診斷的原始鏈資訊，並回傳有明確依據的服務失敗；不得猜測
   chain head、靜默合併區塊、重寫鏈或以遊戲位址修補。
6. 狀態快照：任何 READY 實作都必須讓 SaveState／LoadState 同時保存已協調的 arena 與客體 MCB
   bytes 的一致關係；載回後的下一次服務不得重新從過期 Go 狀態覆寫已存鏈。

## READY 前必須完成的審查與驗收

1. 列出客體 MCB 鏈的完整驗證演算法與每一種失敗的 DOS 回傳語意；目前只證實 `AX=9` 是現行
   dosgolem 結果，尚未量得真 DOS 對這個直接修改後狀態的精確規則。
2. 釐清 arena 資料模型如何保存非目前 PSP 的 owner、EXEC／TSR 與既有 PSP 特例；不能因
   Colonization 只走一條鏈就破壞 dosgolem 已有的多行程行為。
3. 新增一般性單元測試：有效客體 MCB 變更被一次且僅一次匯入；`48h`／`49h`／`4Ah` 結果與發布鏈
   相符；惡意／截斷／迴圈鏈不被接受且不被覆寫；state round-trip 後仍一致。這些測試只證明
   執行器內部契約，不能取代原版收據。
4. 以本文件固定 `OPENING.EXE` 冷啟動重跑至越過第 834,363 指令，記錄輸入與 dosgolem commit、
   `AH=49h` 回傳、完整 MCB 前後差異、下一次 `AH=48h` 結果、`PSOUND.COL` overlay 紀錄、
   `0C41:621A`、VRAM 與未實作服務。合格條件是沒有由過期 arena 造成的 `1C43` 重發佈；不預先
   宣稱應得到哪一個段、首畫面、主程式轉交或中文化輸出。
5. 以相同輸入做一次未協調舊行為的對照，且在報告中只對比本契約實際驗證的字段；若出現新的
   原版控制流差異，停在新的最小 blocker，不擴張硬體或遊戲規則研究。

READY 審查前，Issue #24 維持進行中；動態文字與靜態圖像工作仍分別由 #5、#8 阻塞。
