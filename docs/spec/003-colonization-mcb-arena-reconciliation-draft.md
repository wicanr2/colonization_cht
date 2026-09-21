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
| 目標 013 動態收據 | `probe-opening-03d9-release-lifecycle-20260921.txt` SHA-256 `e6277db64a272db0a944755a2695bf166d742ce3c880a52e3245480f5ae57e50`；`probe-opening-ah52-mcb-20260921.txt` SHA-256 `562d798ad3919c8cca53173efed28671106a948cb738c5e595e0c7e0d00ac6ea`；兩者皆為 `probe -sbpro` 正式冷啟動 | confirmed |
| 目標 013 IDA 匯出 | `ida-opening-03d9-release-helper-runtime-20260921.json` SHA-256 `ee7add64f8b9eb98624353b13afd724f16d9a25a2caba6e336afb5e536df8a7d`、`ida-opening-03d9-mcb-writer-runtime-20260921.json` SHA-256 `ccb5bebb72cb810c5d59e19eb335e76853127c36b0810a3420af57bd6b92aca1`、`ida-opening-0419-ah52-runtime-20260921.json` SHA-256 `1073e393b37ad9b23c5fd31a1d189d6d1446d6b6d9c33a6fb0ee0f64a3a8dd2d` | confirmed |

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

`03D9:02E4` 包裝器進入 `03D9:0138`，後者在 `03D9:0156` 呼叫 `0419:005A`。目標 013 對實際
runtime raw bytes 補上鏈定位的完整交叉證據：`0419:0005`–`0009` 以 `AH=52h` 取得
list-of-lists，立即讀取 `ES:[BX-2]`；再以 `0419:0015` 的 owner、`0419:0048` 的 type 與
`0419:004E`／`0052` 的 size＋下一段公式逐格走訪。第 816,494 指令的 `AH=52h` 回傳
`ES:BX=0070:0010`，`0070:000E` 保持指向首格 `00FF`，走訪最終抵達 `1C42`。這條路徑把
`1C42` 分類為**活躍（active）客體 MCB 鏈**的 confirmed 成員，而非私有暫存。

同一段 raw bytes 在 `03D9:006D` 以 `mov byte ptr es:[di],4Dh` 寫 type、在 `03D9:0071`
以 `mov es:[di+3],dx` 寫 size、在 `03D9:0079` 以 `mov es:[di+1],ax` 寫 owner，接著
`03D9:007D`–`0083` 以 `ES+1` 回傳資料段。動態暫存器在此時給出 `ES=1C42`、`DI=0`、
`DX=0FA1`、`AX=0001`，返回 `1C43:0000`；監看在第 816,657–816,661 指令看見同一記錄的
type、size、owner 變化，並在第 816,768–816,784 指令填入 `$sys$` 名稱。監看 IP 是寫入後的
下一個取樣點，故不可把它的 `03D9:0071`／`0075`／`007D` 標記倒灌為實際寫入指令。這是
「客體程式直接修改活躍 MCB 型態資料」的 confirmed 證據，不是假設 DOS 自動替它配置。

### 3. 現行 arena 與客體鏈在 `AH=49h` 邊界分歧

目標 013 補足了此服務返回的 caller／consumer。`03D9:0312` 兩次進入皆經
`03D9:0340`–`0345`（`les ax,[bp+6]`、`AH=49h`、`int 21h`）：第 833,812 指令從
`0B35:0348` 傳入 `ES=2C9A`，第 833,861 指令從 `08D2:0207` 傳入 `ES=2C5D`。兩次在現行
dosgolem 都得 `AX=0009`；`rcr al,1`、`cbw`、`mov al,ah` 將其 wrapper 返回轉為 `AX=FFFF`。

這個 `AX=FFFF` 沒有被兩個 caller 當成「釋放成功」：第一個返回 `0B35:0348` 後無條件跳到
`0B35:034E`，隨即以 `mov ax,[bx]` 覆寫；第二個返回 `08D2:0207` 後以
`mov ax,[bp-0Eh]`、`mov dx,[bp-0Ch]` 覆寫，才比較自己的 pair。因而不得以這兩次呼叫推論真 DOS
應成功釋放任何區塊，或把 `AH=49h` 無條件改為成功；真 DOS 對兩個請求的精確語意仍是 unknown。

但每次失敗服務之後，現行 `syncMCB()` 都會把已確認活躍的 `1C42` 記錄重發佈為舊 arena 的全空閒區：
owner 由 `01` 變 `00`、size `0FA1h` 回 `83BCh`、名稱清空。接著第 834,319 指令 `086C` 的
`AH=48h` 再次發出資料段 `1C43`，並在第 834,342 指令把 overlay 寫入該段。因此本草案保留的
最小缺口是「服務邊界沒有吸收已驗證的活躍鏈，且連失敗服務也可用過期 arena 抹除它」，不是
「遊戲依賴這兩個 `AH=49h` 成功」。第 1,114,003 指令的 `rep stosw` 隨後按原程式描述元清零
`1C43:0000`，與遠指標的舊目標相衝突；這是此差異的可觀測後果，而不是本草案可直接修改的遊戲規則。

### 4. 現有 dosgolem 邊界

固定 commit 的 `internal/dos/int21.go` 在 `AH=48h`／`49h`／`4Ah` 服務後一律呼叫 `syncMCB()`；
`release()` 只從 Go 端 `arena` 尋找 `ES` 對應資料段，找不到就回 `AX=9`。`arena` 與 `freeSeg`
會儲存在 state，但沒有讀取客體 MCB 的反向匯入步驟。這是上述可重播差異的執行器側必要條件，
不是對其他 DOS 行為的泛稱。

## DRAFT 重新協調契約

下列是供證據審查的提案，尚未授權程式碼：

1. 記憶體服務邊界：在 `AH=48h`、`49h`、`4Ah` 處理前，dosgolem 必須能辨識目前客體可見的
   MCB 鏈是否已與內部 arena 分歧；不得先用過期 arena 回應、再以 `syncMCB()` 覆寫差異。這項
   契約同樣適用於服務失敗：已驗證的客體鏈不能因另一個失敗請求被舊 arena 抹除。
2. 鏈定位：實作不得硬編 Colonization 的段位址。必須由 dosgolem 已公開給客體的 list-of-lists／
   `AH=52h` 路徑取得鏈起點，並使用鏈上的下一段公式逐格前進。
3. 可接受鏈：只有在簽章、尺寸、單調前進、無迴圈、可配置範圍、終止記錄與 MCB 連續性均通過
   驗證時，才可把客體鏈轉成新的內部配置狀態。轉入時必須保留每格的原始段、owner、size、八位元組
   program name 與 free/allocated 判定，不能只把 `1C43` 特判成已配置。
4. 協調原子性：接受有效客體鏈後，該次 `AH=48h`／`49h`／`4Ah` 必須以協調後狀態運作，並只在
   服務完成後發布與新狀態相符的 MCB 鏈。失敗服務不得把**已接受**的客體鏈悄悄重置為另一張
   地圖；未驗證鏈則依失敗即關閉規則保留 bytes 與診斷資訊。
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
6. 以一般性回歸測試分別覆蓋成功與失敗的 `48h`／`49h`／`4Ah`：失敗的無關請求不可抹除已接受
   的客體鏈，也不得據此推論原版要求該失敗請求成功。

READY 審查前，Issue #24 維持進行中；動態文字與靜態圖像工作仍分別由 #5、#8 阻塞。

## 目標 014：可表示性與 READY 範圍審核

本節只記錄審核結果，**不**選定實作架構、**不**把本草案升為 READY，也不授權修改 dosgolem。
所有下列原始執行收據仍以固定 `OPENING.EXE`、`probe -sbpro`、隔離副本 commit
`1b0efdf98ac3ab85c90cb80c3e489e935fb45665` 為輸入；快照由一次性、無網路、UID/GID 1000:1000
的 Docker 容器寫入 gitignore 的 `workplace/reports/`。

### 固定路徑的完整 MCB 快照

`probe-opening-mcb-full-snapshots-20260921.txt`（SHA-256
`c86ab527bd9bad511fd0df18e87a8b2c3d256a63758e039efebd39da70972531`）在客體直接建立 MCB 後的
第 816,800 指令，以及下一個 `AH=49h` 前的第 833,760 指令，各擷取線性 `00000h`–`9FFFFh`。
兩個 655,360-byte 快照 SHA-256 分別為 `dca049b8d138b930d4e68f45b9c411efdc4d2a22a5092dfb530a9ab1d604ff2a`
與 `f284882deffd50af9a1294b75b12287100bb7a9f771efed7a0c4101ec7b8fa37`。離線解析收據
`opening-mcb-chain-audit-20260921.json` 的 SHA-256 為
`03d192246084c4564e1d247fb5b025596bc5cfc4f2fd406f746d4944ccd37c3f`。

兩個時點皆從 list-of-lists `0070:000E` 讀到首格 `00FF`，每格均符合
`next = segment + 1 + size`，且終止於 `9FFF`；此段的 `M`／`Z`、owner、size 與 name 如下。這是
此固定冷啟動的 **confirmed** 觀測，不是任意 DOS 程式都會符合的前提。

| 時點 | MCB（type，owner，size，name） | 結論 |
|---|---|---|
| 第 816,800 指令 | `00FF`（M，`0100`，`1B42`，8 個空白）→ `1C42`（M，`0100`，`0FA1`，`$sys$`）→ `2BE4`（Z，`0000`，`741A`，全零） | 連續且以 `9FFF` 結束。 |
| 第 833,760 指令 | `00FF`（M，`0100`，`1B42`，8 個空白）→ `1C42`（M，`0100`，`0FA1`，`$sys$`）→ `2BE4`（M，`0100`，`0077`，`FONTINTR`）→ `2C5C`（M，`0100`，`003C`，`$sys$`）→ `2C99`（M，`0100`，`0001`，`$pack$`）→ `2C9B`（Z，`0000`，`7363`，全零） | 同樣連續且以 `9FFF` 結束；客體 name 是可見鏈的一部分，不能由重發佈清空。 |

此固定樣本的配置 owner 都是目前根 PSP `0100`，自由區 owner 是 `0000`；它**只**證實一個可嚴格
表示的單一 PSP 例子。它不證實任意 owner、常駐程式（TSR）或多行程鏈可由目前模型表示。

### 目前模型與既有契約的界限

固定 commit 的 `memBlock` 與 SaveState `blockState` 目前只保存 `seg`、`size`、`free`，
`syncMCB()` 會把已配置區的 owner 一律寫成全域 `machine.PSPSeg`，並未保存客體的 program name。
因此即使鏈的區段與大小能讀回，現行狀態格式仍會遺失 owner/name；任何可接受的匯入設計都必須把
這些欄位與 state round-trip 一併納入，而不能只修當次 `AH=48h`／`49h`／`4Ah`。

同一份程式已有 `AH=4Bh AL=00h` 的 child PSP／程序堆疊（process stack）路徑，但 arena 發布仍以
全域根 PSP 為 owner。既有單元測試已通過 allocator、MCB walk、free/coalesce、state root、EXEC
回收與 overlay load 的內部契約；它們不含客體反向匯入，也不是這個 `OPENING.EXE` 的原版同狀態
parity 收據。故不能用既有 EXEC 測試推論「任意 owner 的 MCB 匯入」已安全。

公開 DOS API 文件可作服務前置條件的交叉參考：Microsoft 的 MS-DOS 3.10 Programmer's Reference
記錄 `AH=49h` 以 `ES` 傳入待釋放區塊，失敗時設定 carry，並列出 `AX=7`（損壞 MCB）與
`AX=9`（不正確區段／未配置）。[原始手冊 PDF](https://ftpmirror.your.org/pub/misc/bitsavers/pdf/microsoft/msdos_3.10/8411-310-02_MSDOS_3.10_Programmers_Reference_Manual_1984.pdf)
與 [Undocumented DOS](https://www.bitsavers.org/pdf/microsoft/msdos_4.0/Schulman_-_Undocumented_DOS_1990.pdf)
對 `AH=52h` 的 `ES:[BX-2]` 首 MCB 定位相互支持。這些公開契約**不能**決定本遊戲手動建立鏈後
兩個 `AH=49h` 請求在目標 DOS 版本的實際結果；該項仍為 unknown。

### 待選定的 READY 邊界

本草案在下列架構範圍中尚未作選擇，故尚不能寫出唯一的資料模型、拒絕條件與服務回傳契約。

| 選項 | READY 候選邊界 | 保障與代價 |
|---|---|---|
| A：單一 PSP 的 canonical 匯入 | 僅在目前 PSP 為根 `0100`、無 child process、首 MCB 為 `00FF`、owner 僅為 `0000`／`0100`、鏈連續並於 `9FFF` 終止時接受；保存 owner/name，其他鏈失敗即關閉且不覆寫客體 bytes。 | 已涵蓋本節固定樣本；必須完成資料模型、state migration、`48h`／`49h`／`4Ah` 失敗語意與同狀態驗收，但不宣稱通用多行程支援。 |
| B：通用多行程匯入 | 允許非根 PSP owner 與 child／EXEC 狀態下的鏈匯入，並維護 parent/child 所有權與持久化。 | 功能範圍較廣，但需先補齊程序生命週期、非目前 owner、TSR 與回收語意的獨立證據與測試；本輪證據不足以直接進 READY。 |

不論選 A 或 B，任何不符合所選邊界的鏈都必須在 `syncMCB()` 前被偵測、保留原始 bytes 與可診斷快照，
並以有明確依據的服務失敗結束；不得重寫為舊 arena。選 A 後才能形成狹窄且可驗證的 READY 規格；
選 B 則先開啟其程序／owner 證據工作，維持本草案 DRAFT。此決策是產品與架構範圍選擇，等待使用者確認。

## 目標 015：已採用通用多行程匯入，仍為 DRAFT

使用者已在 2026-09-21 明確選擇上節 **B：通用多行程匯入**。A 的單一 root PSP 限制不再是
實作範圍，但上節表格保留為決策歷史；這項選擇不會把 fixed `OPENING.EXE` 尚未跑到的 child `EXEC`、
`AH=4Ch`、`AH=31h` 或 TSR 升格為原版已證實行為。

### 已確認的執行器內部缺口

以下分析固定於隔離副本 `workplace/dosgolem` commit
`1b0efdf98ac3ab85c90cb80c3e489e935fb45665`。一次性測試探針
`dosgolem-goal015-multiprocess-audit-20260921.txt`（SHA-256
`a5685e095456439500562907d5f51f96af5bccf146b9109e418149964a709f85`）由 Docker 執行，
不進版控的探針程式已刪除；它只量現有 executor，不是原版 oracle。

| 事項 | 觀測 | 等級／影響 |
|---|---|---|
| child 初始 MCB | 父 `0100` 從 `freeSeg=2000` 執行 child 後，child PSP 是 `2001`，其 MCB owner 是 `2001`。 | confirmed；`spawn()` 直接 `WriteMCB(freeSeg, false, psp, ...)`。 |
| child `AH=48h` 後發布 | child 配得 `2014`，其前一格 MCB owner 是 `0100`；重新發布後鏈首 owner 也是 `0100`，size `1F13` 將 child 區納入 root 區。 | confirmed；`memBlock` 沒有 owner，`syncMCB()` 對所有已配置 arena block 固定寫 `machine.PSPSeg`。 |
| child 結束後 | `terminate()` 將 `freeSeg` 回 `2000`，但 arena 仍有 3 格；下一次父 `AH=48h` 配得 `2016`，不是乾淨回收後的 `2001`。 | confirmed；現行 LIFO 游標回退沒有按 owner 移除／重建 arena。 |
| SaveState | `procStack`、`CurPSP` 與 frame 的 PSP／`freeSeg` 會儲存；`blockState` 只有 `Seg`、`Size`、`Free`。 | confirmed；state 無法保存每一 MCB 的 owner、name 或擁有程序關係。 |

既有 allocator、MCB、child EXEC、TSR、handle、overlay 與 root-state 契約測試另以
`dosgolem-goal015-existing-contracts-20260921.txt`（SHA-256
`20c0a7c726f780ffd11dcbf755a4404a6966f76672829b245bc3eab40a79abd6`）通過。這只證明它們目前
分別覆蓋的內部行為；其中沒有「child 先 `AH=48h`、結束、父再配置」的 owner-lifecycle 契約，
故不能抵銷上表缺口。

### 固定原版路徑的邊界

`probe-opening-exec-mode-audit-20260921.txt`（SHA-256
`876d66ae6a8776f74deb2183de6da06e196a26b6120f5d7e72c3d54e9bb352bc`）以固定 `OPENING.EXE`、
`probe -sbpro` 跑至第 2,000,000 指令。服務統計只有一次 `AH=4Bh`，動態紀錄與 IDA Pro 9.4 runtime
raw-binary 匯出 `ida-opening-086c-exec-mode-20260921.json`（SHA-256
`75a9da2e08543e53382ac4650f96e017314d67228b52bff30fca1549a9f39c30`）共同確認它是
`086C:0057` `mov al,3`、`086C:0059` `mov ah,4Bh`、`086C:005B` `int 21h`，即 `AL=03h` overlay。
該觀測窗口沒有 `AH=4Ch` 或 `AH=31h`。此為**有界的未觀測**，不證明它們永不會出現，更不能變成
child／TSR 的原版 parity 聲明。IDA 輸入是 320-byte runtime 傾印
`opening-086c-runtime-20260920.bin`（SHA-256
`67c854c8b188aa74ba617636dc749557518d3d6ef8d77d3ba1a12eafdff5efc9`），地址空間是 raw-binary EA，
每列另附 runtime `086C:offset`；工具為 `ida-pro-9.4-idapython:locked-v1`（image ID
`sha256:6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`）。

### B 的最低資料模型與 READY 前缺口

這不是 READY 實作設計，而是 B 不可再省略的資料表示條件：

1. 每個 arena record 必須能保留 MCB 段、資料段數、free、owner PSP 與不解讀的 8-byte name；
   客體原始 header bytes 與此 typed state 的一致性必須能在服務邊界驗證。
2. process state 必須能把 current PSP、parent／suspended frame、每個 owner 的存活狀態與可回收
   blocks 連起來；不能由全域 `machine.PSPSeg` 推導 owner。
3. `AH=48h`、`49h`、`4Ah` 在 child／parent／TSR 情境的輸入 owner、合法轉移、失敗回傳與發布後鏈
   都須逐項定義；現有 `freeSeg` LIFO 只能作為舊行為證據，不可當通用回收演算法。
4. SaveState 必須版本化地保存上述 owner/name/process 關係與任何驗證過的客體 MCB snapshot；舊 v2
   state 的遷移與無法表示狀態必須失敗即關閉，不能靜默補 root owner。

READY 前仍是 unknown：外部／非 child PSP owner 的接受集合、TSR 在直接修改 MCB 後的完整回收規則、
跨程序 `AH=49h`／`4Ah` 的精確 DOS 回傳、state migration 格式，以及能把這些內部契約接回固定
`OPENING.EXE` 的同狀態驗收。故本規格維持 DRAFT，禁止依本節修改 dosgolem。
