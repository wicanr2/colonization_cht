# 目前脈絡

日期：2026-09-21

## 已確認

- 目標是《Sid Meier's Colonization》（1994）的繁體中文**輸出階段轉譯層**，不是 remake。
- 動態輸出文字與靜態圖像內嵌文字都在研究範圍；原版檔案不修改。
- GitHub 儲存庫 `wicanr2/colonization_cht` 是私有儲存庫。
- 本機兩份原始封存檔僅能唯讀使用，已由 `.gitignore` 排除；雜湊與清冊見 `RESEARCH-LOG.md`。
- 未完成項的唯一機器可讀來源是 `docs/worklist.json`；每筆都有 GitHub Issue。
- `README.md` 是專案首頁；第一輪目標見 `docs/goals/001-foundation-and-evidence.md`。
- `workplace/dosgolem` 是提交 `1b0efdf` 的獨立副本，push URL 為 `DISABLED`；不得修改其他
  專案使用的 `/home/anr2/cht/dosgolem`。
- 固定雜湊的 `COLONIZE.EXE` 是 Windows 3.10 NE 程式。dosgolem probe 只走到 DOS stub，
  無法進入 Windows 應用程式本體；這是可重現 blocker，不是已支援的冷啟動。
- 固定 NE 的靜態載入面已完成清冊：33 個區段、7 個模組、176 個 ordinal import target、
  42 個資源項目；這只描述檔案結構，不能證實任何 Win16 API 的實際呼叫或文字輸出。
- 使用者已選定本機 `Sid Meier's Colonization (1994)/SMColoni/` 的合法 DOS 輸入作為正式研究目標；
  該目錄由 `.gitignore` 排除，291 個檔案／390,317,887 bytes 的 manifest SHA-256 是
  `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。
- 正常 DOS 冷啟動入口是 `OPENING.EXE`（SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）。dosgolem 已在此路徑跑過
  1 億指令、進入 mode 13h／PIT／滑鼠／overlay 與資料讀取；最新冷啟動另記錄一個未實作的
  `int 33h AX=0014`，尚未能與 blocker 建立因果。仍還沒有第一個
  非零畫面或 `VICEROY.EXE` 轉交收據。
- 正式路徑唯一已記錄的 `EXEC` 是 `PSOUND.COL`（不是 `VICEROY.EXE`）。未啟用 `-sbpro` 的第
  1,000,000 指令快照延續至第 100,000,000 指令時，A0000 維持全零、沒有視訊寫入、沒有字型服務呼叫，
  且程式停留在 `PSOUND.COL` 的 `1C43:0087`；這是預設 profile 的 confirmed 受阻點收據，不是可見畫面。
- `PSOUND.COL` 的 `0x220` status 讀取是已證實的 `0x00 → 0xC0` AdLib 偵測條件，`0x222` 在此版本
  僅作未消費的 delay；此外它以 `0x226=1 → 0` reset、`0x22E` status 和 `0x22A=0xAA` 判定 DSP 成功。
  最小 READY profile 已以 `-sbpro` 實作於隔離副本：固定 state 的第一組 reset 在第 1,004,428 指令
  直接讀得 `0xAA`，隨後正式路徑載入 `MPSLOGO.SS` 與 `MPSNAME.SS`，且沒有未實作 DOS 服務。
- `-sbpro` 路徑至第 100,000,000 指令仍沒有非零 A0000 像素、`VICEROY.EXE` EXEC 或文字輸出。目標 010
  已確認第 `1,230,846` 指令的 `087E:005D` 以 `jmp dword ptr ds:621Ah` 跳至 `1C43:0BF9`；table bytes
  `F9 0B 43 1C` 對應 `0BF9:1C43`，CPU 遠跳轉（far jump）正確。該目標先在第 `834,342` 指令由 `086C:005D` 載入，
  再於第 `1,114,003` 指令由 `03B1:00A6` 的 `rep stosw` 以 `ES:DI=1C43:0000` 清零 `0xFA00` bytes。
  因此第 1,451,566 指令開始於 `1C43:FA57` 的執行是清零資料的順向落入（fall-through）；這是 confirmed 的執行期
  初始化／覆蓋區記憶體生命週期 blocker，不是已證實的音效、DMA、DOSBox 或中文化問題。清零呼叫的
  參數來源，以及之後仍選擇舊遠指標（far pointer）的條件，維持 unknown。
- 目標 012 已確認 `02B2:00AF → 086C:0004 → 02B2:00B4` 的正常冷啟動 caller／return 鏈：`086C`
  先以 `AH=48h` 配得 `1C43`，再以 `AH=4Bh AL=03h` 將 `PSOUND.COL` 載入 `1C43:0000`，縮放後寫入
  `0C41:621A = 0BF9:1C43`。這是 confirmed 的 overlay 載入，不再只是強推論。
- 目標 013 已確認 `AH=52h` 回傳的 list-of-lists 經 `0419:0009` 讀取 `ES:[BX-2]`，逐格走訪至
  `1C42`；`03D9:006D`、`0071`、`0079` 直接寫入其 type、size、owner，並以 `ES+1` 回傳 `1C43`。
  因而這是 confirmed 的活躍（active）客體 MCB 鏈，不是私有暫存。兩個 `03D9:0312` 的 `AH=49h`
  wrapper 呼叫（`ES=2C9A`、`2C5D`）都在現行 dosgolem 得 `AX=9` 後轉為 `FFFF`，但 caller 隨即覆寫
  回傳暫存器；不可宣稱遊戲要求該服務成功。確認的通用缺口仍是失敗服務後 `syncMCB()` 以過期 arena
  抹除已驗證鏈，令第 834,319 指令的 `AH=48h` 重用 `1C43`。真 DOS 對兩個請求的精確規則與完整後續
  控制流仍是未知。
- [DRAFT 規格 003](docs/spec/003-colonization-mcb-arena-reconciliation-draft.md) 僅提出通用的有效 MCB
  鏈驗證、服務邊界協調、失敗即關閉與 snapshot 一致性契約，未修改 dosgolem 或原版資料。
- 目標 014 的完整記憶體快照已確認固定 `OPENING.EXE` 路徑的 MCB 鏈在直接建立後與下一個
  `AH=49h` 前都連續終止於 `9FFF`；配置 owner 均是根 PSP `0100`，而 `$sys$`、`FONTINTR`、`$pack$`
  等八位元組 name 必須保留。現行 dosgolem 的 arena／state 只保存區段、大小與 free，重發佈會遺失
  owner/name；它雖已有 child EXEC 路徑，卻不能據此推論通用 owner 匯入安全。使用者已選擇**通用多行程
  匯入（B）**、排除單一 PSP canonical 限縮範圍；規格 003 仍是 DRAFT、沒有任何實作。
- 目標 015 的受控 executor 探針已確認 child 初始 MCB owner 是 child PSP，但 child `AH=48h` 後
  `syncMCB()` 把新 arena MCB 發布為 root `0100`，child 結束後 arena 又未隨 `freeSeg` 回收；下一次父
  配置落在 `2016` 而不是 `2001`。SaveState 可保存 process stack／current PSP，卻只保存
  block `seg/size/free`，無法保留 owner/name／生命週期。這是 confirmed 的現行 executor 缺口，不是
  Colonization 原版 child／TSR 需求。固定冷啟動至第 2,000,000 指令只觀測到一次 `AH=4Bh AL=03h`
  overlay，未觀測 `AH=4Ch`／`31h`；該未觀測只限此窗口。

## 尚未確認

- 印字常式、文字來源、靜態文字資產、字型來源、術語政策與中文化完成門檻。
- `OPENING.EXE` 的第一個可見畫面或可證實 `VICEROY.EXE` 轉交（目前需先釐清 #24 的映像外控制流），
  以及字型來源、術語政策、中文化完成門檻、授權、公開發布與封裝範圍。

## 下一閘門

Issue #23 已完成 READY profile 的實作與同狀態收據。#24 已完成首次控制轉移、清零引數、overlay 載入者、
客體活躍 MCB 鏈、過期 arena 重發佈，以及 DRAFT 003 的 caller／consumer／可表示性與多行程 owner
缺口審查；DRAFT 仍未 READY。使用者已選 B，下一個最小前沿是先為通用 process/owner/name/state 模型
定義可驗證的服務轉移、TSR／外部 owner 拒絕條件、state migration 與一般性驗收，再以固定原版同狀態
驗證它實際觸及的部分；絕不直接修正。#5 與 #8 在 #24 之前維持阻塞。Windows NE 清冊（#19）只保留為
歷史輸入證據。Issue #10 與 #15 仍需在真實證據與原型具備後由使用者決定。
