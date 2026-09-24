# 工作歷程

## 2026-09-20：建立專案邊界與工作計畫

- 建立 `AGENTS.md`、私有 GitHub 儲存庫與初始提交 `c29c271`。
- 原始封存檔由 `.gitignore` 排除，未提交或推送。
- 建立 GitHub Issue #1–#16，並以 `docs/worklist.json` 作為其機器可讀索引；#16 已完成，
  其餘未完成項都保留可追溯 Issue。
- 驗證與完整探勘尚未開始；所有尚未自動驗證的工作項目標為 `manual`，不宣稱完成。
- Docker：本輪使用的一次性唯讀容器均以 `--rm` 結束；未清理其他專案的既有容器。

## 2026-09-20：建立首頁與第一輪目標

- 建立 `README.md`，說明遊戲、降低語言隔閡的中文化目的、輸出階段轉譯方式與原版素材邊界。
- 建立 `docs/goals/001-foundation-and-evidence.md`，把第一輪限制為輸入清冊、隔離工具鏈、
  dosgolem 探測與冷啟動基線。
- 對應工作登記為 GitHub Issue #17；尚未處理任何原版遊戲資料。

## 2026-09-20：完成目標 001 的證據與 blocker 收據

- 建立 `workplace/dosgolem` 的獨立 clone（`d9c0c27`），並停用其 upstream push，未改動其他
  專案的 dosgolem 工作樹。
- 建立 `colonization-research:20260920-r1`／`r2` 可重建研究映像；r2 只修正 Go PATH。
- 以唯讀封存檔盤點並解包 ZIP 至 gitignore 的 `workplace/original/colwin/`；完整輸入、格式、
  雜湊、工具和 probe 收據記錄於 `RESEARCH-LOG.md`。
- dosgolem probe 確認目標是 Windows 3.10 NE 程式的 DOS stub，未進入遊戲本體；建立 Issue #18
  等待使用者決定後續執行策略。
- Docker：本輪一次性容器均採 `--rm`；輸出以 UID/GID 1000:1000 建立，未清理其他專案資源。

## 2026-09-20：建立目標 002 的 Windows 3.x 決策前沿

- 重核 `COLONIZE.EXE` 的 NE 格式、DOS stub 收據與 dosgolem 官方能力矩陣；獨立副本仍固定在
  `d9c0c27`，且未含 Windows 3.x／Win16／NE loader 的實作或宣告。
- 建立 `docs/goals/002-win16-execution-strategy.md`，將符合既定 dosgolem 架構的兩個選項、證據
  等級、排除項與使用者決策退出條件明文化，並從 README 建立入口。
- 尚未實作或選定任一策略；等待 Issue #18 的使用者決定後才更新目前脈絡、工作清單與後續 Issue。
- Docker：本輪唯讀查證容器均採 `--rm`、`--network none` 及目前 UID/GID；未建立持續容器或修改
  原始 dosgolem 工作樹。

## 2026-09-20：完成目標 003 的固定 NE 載入面清冊

- 建立受版控的 `tools/ne_inventory.py`，僅解析 MZ／NE header、區段、module reference、import
  relocation 與資源中繼資料；不輸出原版資源、文字或像素。完整 JSON 報告留在 gitignore 的
  `workplace/reports/`。
- 對固定雜湊輸入取得 33 個區段、7 個模組、25,825 筆 relocation、176 個 imported ordinal target
  與 42 個資源項目的收據；詳見 `RESEARCH-LOG.md` 與目標 003。
- `file` 與原始 bytes 交叉確認 `MZ.e_lfanew=0x250` 指向 `NE`。首次語法檢查因專案唯讀掛載而無法
  寫入 `__pycache__`；改將 `PYTHONPYCACHEPREFIX` 指向容器 `/tmp` 後通過，列為環境修正而非產品缺陷。
- Docker：本輪所有容器均採 `--rm`、`--network none` 與目前 UID/GID；未修改原始輸入或其他專案的
  dosgolem 工作樹。

## 2026-09-20：目標 004 執行策略阻塞稽核

- 已連續重核目標輸入、DOS stub 收據、dosgolem 能力矩陣與固定 NE 靜態清冊；沒有未經架構決定即可
  進入遊戲本體、取得文字輸出或建立正常玩家路徑收據的工作。
- 建立 `docs/goals/004-execution-strategy-blocker-audit.md`，把唯一解鎖條件固定為 Issue #18 的使用者
  選擇：擴充獨立 dosgolem 的最小 Windows 3.x 路徑，或提供合法 DOS 版輸入。
- 不重複靜態分析、不替換執行器，也不將 import／資源資料誤報為中文化進度；等待使用者決定。
- Docker：本輪未啟動新的分析容器；既有研究容器均已於前輪以 `--rm` 清理。

## 2026-09-20：完成目標 005 的 DOS 輸入與冷啟動能力收據

- 使用者提供並指定 `Sid Meier's Colonization (1994)/SMColoni/` 的 DOS 輸入；立即加入 `.gitignore`，
  以唯讀掛載建立 291 檔 manifest，完整清冊只保存在 `workplace/reports/`。
- 批次啟動鏈證實正式冷啟動入口是 `OPENING.EXE`，不是跳過流程的 `VICEROY.EXE`。固定雜湊、格式、
  DOS probe 命令與結果已寫入 `RESEARCH-LOG.md` 與目標 005。
- dosgolem 在正式入口走到 mode 13h、PIT、滑鼠、overlay 與資料讀取，1,000 萬指令內沒有未實作
  服務；尚未取得非零 A0000 或主程式轉交，建立 Issue #21 追查第一個可見檢查點。
- `VICEROY.EXE` direct-entry 僅作診斷，確認其 EMS 初始化後的固定停點，未當作玩家路徑或完成證據。
- Docker：本輪容器均採 `--rm`、`--network none`、目前 UID/GID 與資源上限；原始輸入及其他
  dosgolem 工作樹未被修改。

## 2026-09-20：完成目標 006 的 DOS 首個可見檢查點診斷

- 從正式 `OPENING.EXE` 的第 1,000,000 指令快照重播至 100,000,000 指令；沒有第一個可見畫面、
  文字輸出或 `VICEROY.EXE` 轉交。`PSOUND.COL` 是唯一實際 EXEC，並持續停在其 overlay 路徑。
- 以視訊監看、索引 VRAM、段轉移、檔案與音效 port 收據建立最小 blocker；修正一次檔案位移的誤讀：
  `COLDIG.BIN @0xA0000` 是來源檔位移，目的地為 EMS `D000:0000`，不是 VRAM。
- 建立 Issue #22（DRAFT／READY 規格）與 #23（依 READY 的最小實作與首畫面驗證）。未修改
  `workplace/dosgolem`、原版資料或任何其他專案。
- Docker：所有容器均採 `--rm`、`--network none`、目前 UID/GID 與資源上限；輸出皆為 UID/GID
  1000:1000，沒有專案相關持續容器或 root-owned 殘留。

## 2026-09-20：完成目標 007 的 OPL 相容規格草案與證據審查

- 以 IDA Pro 9.4 的 16 位元 `.COM` 副本和固定 dosgolem state 交叉對照，確認 `PSOUND.COL` 在
  `1C43:0082` 實際執行十次 `0x220`、十次 `0x222` status 讀取；預設 probe 對兩者回 `0xFF`。
- 建立 `docs/spec/001-colonization-sbpro-opl-profile.md` DRAFT，記錄公開 Sound Blaster Pro port 契約、
  `0x220`–`0x223` address/data/status 與 `0x226` reset 收據、可重用元件邊界，以及 fail-closed 的
  啟用要求。
- 審查未越級建立 READY：第二組／advanced status 的明示位元語意、reset 後必要 DSP port，以及正式
  同狀態 A/B 尚無足夠證據。Issue #22 保持進行中，Issue #23 不得提前實作。
- Docker：研究與 IDA 容器皆採 `--rm`、`--network none`、目前 UID/GID 與資源上限；未修改原版輸入、
  共用 dosgolem 或其他專案。

## 2026-09-20：完成目標 008 的 PSOUND READY 證據收斂

- 對固定 state 的 140 個 IDA 已解碼 I/O 候選做有界暫存器觀察，分離出真正執行的 OPL status、
  address/data、DSP write-buffer、reset、read-buffer 與 reply port；沒有將未命中的 raw overlay
  解碼誤列為需求。
- 以 IDA 16 位元 bytes、正常路徑 hit 與 Creative 公開 DSP 契約確認：`0x220` 是會比較
  `0x00 → 0xC0` 的偵測、`0x222` 在本版只作 delay、`0x226 → 0x22E → 0x22A=0xAA` 是具體
  reset 成功／失敗分支。
- 將規格草案 001 保留為 SUPERSEDED 歷史證據，建立 `docs/spec/002-colonization-sbpro-opl-profile-ready.md`，
  只授權 Issue #23 加入預設關閉的 `-sbpro` 最小 profile 與同狀態冷啟動收據。
- Docker：所有研究、測試與 IDA 容器均採 `--rm`、`--network none`、目前 UID/GID 與資源上限；未修改
  原版輸入、共用 dosgolem 或其他專案。

## 2026-09-20：完成目標 009 的最小 SBPro profile 與冷啟動收據

- 在 `workplace/dosgolem` 的隔離副本建立本地 commit `1b0efdf`：新增預設關閉的 `probe -sbpro`，直接
  接一般 `Machine` 的最小 `0x220` OPL／DSP profile；沒有使用 `LEOPLPorts`，也沒有擴張 DMA、PCM、
  PIT、DAC、IRQ、mixer 或其他基址。副本 upstream push 維持 `DISABLED`。
- 以 Docker 執行 `go test ./... -count=1` 全數通過。固定第 1,000,000 指令 state 的同狀態 A/B 顯示：
  profile 在第 1,004,428 指令第一次讀到 DSP `0xAA`，不再耗盡 64 次，並進一步載入 `MPSLOGO.SS`、
  `MPSNAME.SS`。這不是首畫面或音效完成宣稱。
- 延長至第 100,000,000 指令仍無非零畫面；CPU 從第 1,451,566 指令起在 `1C43:FA57` 映像外範圍循環且
  SP 遞減。建立 Issue #24 追查最小控制流／堆疊 blocker，#5 與 #8 仍維持阻塞。
- 一次 `-dump-screen-png` 因 mode 13h 不是平面模式而被 probe 拒絕；隨即以 `-dump-vram` 用同一固定
  輸入乾淨重跑，這是驗證輸出選項修正，不是原版或產品缺陷。
- Docker：所有本輪容器均採 `--rm`、`--network none`、目前 UID/GID 與資源上限；輸出皆為 UID/GID
  1000:1000，沒有專案相關持續容器或 root-owned 殘留。

## 2026-09-20：完成目標 010 的映像外控制流定位

- 以 dosgolem 的唯讀 DOS 冷啟動收據確認：第 `1,230,846` 指令 `087E:005D` 的遠跳轉（far jump）進入
  `1C43:0BF9`；`1C43:FA57` 是後續執行零 bytes 的順向落入（fall-through），不是直接跳轉目的地。
- 冷啟動收據也確認目標區先被載入，後由 `03B1:00A6` 的 `rep stosw` 以 `ES:DI=1C43:0000` 清零
  `0xFA00` bytes。IDA Pro 9.4、IP log、暫存器與寫入監看交叉保留於 `RESEARCH-LOG.md`。
- Issue #24 保持進行中：下一個最小問題是 `03CC → 03B1` 的清零參數來源與 `0C41:621A` 選擇條件；
  沒有修改 dosgolem、原版資料、音效模型或中文覆蓋。

## 2026-09-20：完成目標 011 的 PSOUND 清零引數與舊遠指標來源

- dosgolem 正式冷開機重播與 IDA Pro 9.4 非破壞性匯出交叉確認：`0110:0DB3` 從
  `0C41:3910` 讀取四字組描述元，並經 `03AF:0006`、`03B1:0008` 清零 `1C43:0000` 起的
  `FA00` 位元組。
- `03A7:000A` 明確計算 `0140 × 00C8 = FA00`，由 `03D9:02E4` 回傳 `1C43:0000` 寫入描述元；
  `0110:0DC1` 的零值是填充值來源。這排除「dosgolem 未初始化記憶體」作為此清零操作的解釋。
- `086C` 後續寫入 `1C43:0BF9` 的位元組與 `0C41:621A` 遠指標；指標表沒有在清零後更新，仍由
  `087E:005D` 消費。已記錄為同段生命週期衝突，未把未證實的服務假說當成修正依據；Issue #24 保持開放。
- 已將收據與下一前沿回填 [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5750746889)。
  一次性 Docker 容器均以 `--rm` 結束；檢查沒有本專案殘留容器、root 擁有檔案或誤建 `.md` 目錄。

## 2026-09-21：完成目標 012 的 overlay 與 MCB arena 生命週期收斂

- 以正式 `OPENING.EXE` 冷啟動、動態暫存器／寫入監看與 IDA Pro 9.4 raw-binary 匯出，確認
  `02B2:00AF → 086C:0004 → 02B2:00B4`。`086C` 以 `AH=4Bh AL=03h` 將 `PSOUND.COL` 載入 `1C43`，
  不是僅由目標段程式碼推測。
- 確認 `03D9` 先以 `AH=52h` 取得客體 MCB 鏈、直接寫入 `1C42` MCB 欄位，之後的 `AH=49h` 在現行
  dosgolem 回 `AX=9` 並由 `syncMCB()` 重發佈過期 arena，使 `AH=48h` 重用 `1C43`。真 DOS 對該請求的
  精確結果仍標示未知。
- 建立 `docs/spec/003-colonization-mcb-arena-reconciliation-draft.md`：只提出通用 MCB 鏈驗證、服務邊界
  協調、失敗即關閉與 snapshot 一致性 DRAFT；未修改 dosgolem、原版資料、遊戲規則或中文化層。
- 一次早期 `03D9` raw dump 的線性基底多寫一個零；在任何結論前已捨棄，使用正確 `0x3D90` 視窗重跑並
  記入 `RESEARCH-LOG.md`，未把錯誤樣本納入證據。
- Docker：研究與 IDA 均以無網路、UID/GID 1000:1000、資源上限的 `docker run --rm` 執行；已完成文件驗證、
  Issue #24 回填與 Git 推送。收尾檢查確認無本專案持續容器、root 擁有檔案或誤建 `.md` 目錄。

## 2026-09-21：完成目標 013 的 MCB DRAFT caller／鏈審查

- 以 `probe -sbpro` 的正式 `OPENING.EXE` 冷啟動確認 `03D9:0312` 的兩個 `AH=49h` wrapper 呼叫分別
  使用 `ES=2C9A`、`2C5D`。現行 dosgolem 的 `AX=9` 被 wrapper 轉為 `FFFF`，但兩個 caller 都立即
  覆寫該返回值；因此沒有把未證實的真 DOS 成功語意寫入 DRAFT。
- 以 IDA Pro 9.4 runtime raw-binary 與動態 trace 確認 `AH=52h → ES:[BX-2]` 的活躍 MCB 走訪；
  `03D9:006D`／`0071`／`0079` 對 `1C42` 寫入 type／size／owner，並回傳 `1C43`。DRAFT 003 改為
  明確要求：即使無關的服務失敗，也不能讓過期 arena 覆寫已接受的有效鏈。
- DRAFT 003 維持 DRAFT、未建立 dosgolem 程式碼或遊戲位址特例。尚缺通用鏈驗證、所有權／多行程、
  失敗回傳、state round-trip 與同狀態冷啟動驗收。
- Docker：所有 dosgolem／IDA 作業都用 `--rm --network none`、UID/GID 1000:1000 與資源上限；收尾另檢查
  容器與檔案擁有權，沒有保留本專案容器或 root-owned 產物。

## 2026-09-21：完成目標 014 的 MCB 可表示性與範圍審核

- 以固定 `OPENING.EXE` 的兩份完整記憶體快照確認：直接建立後到下一個 `AH=49h` 前，客體 MCB 鏈都
  從 `00FF` 連續走到 `9FFF`；固定樣本的配置 owner 是根 PSP `0100`，而 `$sys$`、`FONTINTR`、`$pack$`
  等 program name 必須保留。
- 查核隔離 dosgolem 的 arena、state 與 EXEC 邊界：目前模型只保存區段、大小、free，且 `syncMCB()`
  會以全域根 PSP／空白 name 重發佈；既有 child EXEC 與測試不等於通用 owner 匯入已安全。
- DRAFT 規格 003 維持 DRAFT，加入完整收據、公開 DOS 服務前置條件與兩個待選範圍。使用者須選擇狹窄
  的單一 PSP canonical 匯入或先擴張為通用多行程匯入；未選定前沒有程式碼修改。
- Docker：快照與測試均在無網路、UID/GID 1000:1000、資源受限的 `docker run --rm` 完成；收尾已確認
  沒有專案相關容器、root-owned 檔案或誤建 `.md` 目錄。

## 2026-09-21：完成目標 015 的通用多行程 MCB 證據

- 使用者選定通用多行程 MCB 匯入（B），排除單一 PSP 限縮範圍；DRAFT 003 與目前脈絡已明確分離
  這項架構需求和 Colonization 固定路徑的原版觀測。
- 受控 child EXEC 探針確認現有 arena 沒有 owner/name：child `AH=48h` 的發布改用 root PSP owner，
  child 結束後 arena 未按 owner 回收。既有 allocator／EXEC／TSR／state 測試通過，但不覆蓋這條生命週期。
- 固定 `OPENING.EXE` 兩百萬指令只觀測一次 `AH=4Bh AL=03h` overlay；IDA Pro 9.4 raw-binary 匯出交叉
  確認 `086C:0057`–`005B` 的 `B0 03 B4 4B CD 21`。未觀測 `AH=4Ch`／`31h` 僅限此窗口。
- DRAFT 維持 DRAFT、未修改 dosgolem 或原版；已將結論回填
  [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755046145)，並推送證據提交
  `90c5cdc`。已刪除一次性探針與 IDA 暫存資料庫；Docker 清理、擁有權與原版素材版控檢查均通過。

## 2026-09-21：目標 016 的多行程 service transition 審核

- 以一次性 child 探針實測 `AH=48h`、`4Ah`、`49h`、normal exit、`AH=31h` 與 SaveState／LoadState。
  收據 SHA-256 `1f7a7abc73d588a124debcc926d2a65efb0917d1289439a7b2f3196f21bc7202` 確認 child owner 被
  root 重發佈，且 TSR retained range 可被父配置重疊；這只描述現行 executor，不是原版 parity。
- 選定 allocator、MCB、resize、normal EXEC、TSR、child PSP resize、連續 EXEC 回收與 state 契約測試均
  通過，收據 SHA-256 `76df8429c28e3a8590863cd01eccf76805a435f467b0ff28551edf4c06cdeffe`；測試範圍不含
  owner/name 或 TSR retain overlap 的現有保證。
- DRAFT 003 已新增 service transition ledger 與 B 進 READY 前的 owner/name/process registry、拒絕、
  state migration 與同狀態驗收條件；保持 DRAFT，未修改 dosgolem 或原版。
- 一次性測試檔已從隔離 dosgolem 副本刪除；已將結論回填
  [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755179775)，並推送證據提交
  `ecd058a`。收尾提交會記錄 completed 狀態；Docker、擁有權與原版素材邊界將再次檢查。

## 2026-09-21：目標 017 的 MS-DOS 平台契約審核

- 以 Docker 從 DRAFT 已列的 Microsoft MS-DOS 3.10 Programmer's Reference Manual URL 取得唯讀研究副本；
  PDF SHA-256 `0955283261ffdae38bc70e152be660774c68276febc325e3b11c222e77b993e1`，並以既有
  `minidocks/poppler:latest` 的 `pdftotext -layout` 擷取文字（SHA-256
  `5915e90c80d670c18796d96833d6be2a19cf571fb76077da623160682390db83`）。兩者留在 gitignore 的
  `workplace/reports/`，沒有加入 Git。
- 手冊頁 1-183–188、1-189–190、1-196、1-236 分別限制 `48h/49h/4Ah`、EXEC／PSP、`4Ch` 與 active
  PSP；已確認現行 root owner 重發佈、無 owner release、寬鬆 resize、TSR overlap 與固定 root PSP 不可
  當成通用 DOS 契約。跨程序與手改 MCB 的細節保持 unknown。
- DRAFT 003 維持 DRAFT、未修改 dosgolem／原版／中文覆蓋；已回填
  [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755254133)，並推送證據提交
  `89c37b6`。收尾提交會記錄 completed 狀態；Docker、擁有權及原版素材邊界將再次檢查。

## 2026-09-21：目標 018 的 MCB wire format 與直接改寫界線

- MS-DOS 3.10 手冊 1-4–1-5 的 MCB size、owner/name、chain 與直接改寫警告，已與 `OPENING.EXE`
  `03D9:006D/0071/0079` 對 `1C42` 的 direct writes、`$sys$` name，以及現行 `WriteMCB()` bytes 分層比對。
- DRAFT 003 現要求 importer 保存／驗證 raw 16-byte header、typed owner/name、連續 M/Z chain 與
  process registry；矛盾一律保留 snapshot 並 fail-closed。跨程序、TSR、external owner 仍 unknown，
  DRAFT 未 READY、未改 dosgolem 或原版。
- 已回填 [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755285987) 並推送證據
  提交 `35a86f0`；收尾提交會記錄 completed 狀態，並再次驗證 Docker、擁有權與原版素材邊界。

## 2026-09-21：目標 019 的 generic importer READY 審查

- 一次性 Docker child 診斷收據 SHA-256 `353c81a5b8ceb1c341a681df9cbd47b1efb885702bc2fa7d62798d595ac42813`
  確認 child `curPSP=2001` 時 `AH=62h` 回 root `0100`，child allocation MCB owner=0100、name 空白，
  state v2 只有 arena/stack/curPSP。探針已刪除。
- 因 raw-header parser、owner-aware registry、current-PSP service 與可表示 owner/name 的 state migration
  都不存在，B 尚未 READY；這是 executor READY gate 結論，不是 Colonization child／TSR parity。
- DRAFT 003 維持 DRAFT，未修改 dosgolem 或原版；已回填
  [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755331181)，並推送證據提交
  `185bb87`。收尾提交會記錄 completed 狀態，並重查 Docker、擁有權及原版素材。

## 2026-09-21：目標 020 的已註冊多行程 MCB READY 規格

- 綜合目標 015–019 的 platform、固定 `OPENING.EXE` direct-header 與 child/state 收據，建立 READY
  規格 004：registered root／child owner 的 raw 16-byte header、typed registry、state v3、current PSP
  service、服務轉移、rejection 與驗收均已契約化。
- external／未註冊 owner、手改後 unknown lifecycle、cross-process `49h/4Ah`、TSR 特例與 v2 state
  明確 fail-closed；不以 root-only 遊戲樣本縮小 B，亦不假稱 child/TSR 遊戲 parity。
- 本規格是唯一授權下一輪 dosgolem 通用實作的依據；本輪沒有程式碼修改。已回填
  [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755401767)，並推送證據提交
  `58fc3fc`；收尾提交會記錄 completed 狀態，並檢查 Docker、擁有權及原版素材邊界。

## 2026-09-21：完成目標 021 的已註冊多行程 MCB importer

- 在隔離 `workplace/dosgolem` 實作 raw 16-byte MCB header、owner/name、程序 registry、state v3、
  current PSP services 與 fail-closed importer；沒有把 Colonization 位址、文本或原版素材放進 dosgolem。
- 新增 synthetic child／direct header／TSR rejection／state v3 契約測試，並在無網路 Docker 中以
  `go test ./...` 通過所有 package。
- 固定 `OPENING.EXE -sbpro` 重跑至 2,000,000 指令，收據
  `workplace/reports/dosgolem-goal021-opening-overlay-20260921.txt` 的 SHA-256 是
  `2fa18b931afac4bf15f7d89a1712cb7e98de2a7e29a054097202589cb4a58e00`；`PSOUND.COL` overlay、後續資料
  讀取與 `$sys$` 等 raw MCB names 均存在，但未宣稱可見畫面或完整遊戲。
- [CONFORMED 規格 005](docs/spec/005-colonization-registered-process-mcb-importer-conformed.md) 記錄本輪
  有效範圍與停止線。隔離 dosgolem 已提交為本地 `1435f17`，其 upstream 仍為 `DISABLED`；Issue、外層 Git
  提交 `550e664` 已推送，並已回填 [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755765894)。
- 收尾 Docker 檢查：無名稱含 `colonization` 的執行中或停止容器；工作根與隔離副本均未發現 root-owned
  產物或誤建 `.md` 目錄。原版輸入維持 gitignore，未進入暫存或提交。

## 2026-09-21：完成目標 022 的 MCB 修正後首畫面檢查點

- 建立並由同一 `/game` 唯讀掛載重載第 2,000,000 指令 state v3。probe callback 的絕對步數在迴圈前觸發，
  所以用 2,000,001 的執行上限保存 2,000,000 的精確 state；這是診斷工具時序，不是原版控制流缺口。
- 自同一 state 分別重跑 2.50M、2.625M、2.70M、2.75M、3M、5M、10M、20M。2.70M 仍無 A0000 寫入；
  2.75M 有 18,445 筆未丟棄的 mode 13h VRAM 寫入、18,445 個非零像素，末段來源為 `0557:0090`。10M、20M
  保持相同像素數且持續輪詢滑鼠，沒有文字 hook、主控台字元或 `VICEROY.EXE` 轉交。
- mode 13h 不適用 planar 的 `-dump-at`，故沒有將失敗的 EGA 傾印當作遊戲證據；改以 probe 的色號與色盤在
  `workplace/reports/` 建立僅本地 PNG，雜湊與證據等級記於 `RESEARCH-LOG.md`。沒有提交原版像素或資料。
- #24 的最小 blocker 已解除，工作清單將 #5／#8 解鎖為 planned；文件、Issue、Git 推送與 Docker／擁有權／
  原版素材檢查在收尾一併完成。

## 2026-09-21：完成目標 023 的首畫面繪製來源邊界

- 由目標 022 的固定 2M state v3 重播至 2.75M，確認首筆 VRAM 搬運在第 2,747,686 指令的 `0557:0090`；
  `DS:SI=1DFB:00F8`、`ES:DI=A000:1C78`，後續以 0x140 跨列遞進。完整收據雜湊記入 `RESEARCH-LOG.md`。
- 點陣搬運與無文字 hook／B8000／主控台字元只支持「首畫面較可能是靜態點陣資料」的強推論；沒有猜測圖像內容、
  原始資產對應或任何動態文字路徑。
- Issue #5 維持進行中：本輪只完成首畫面 provenance 的有界切片。文件、Issue、Git 推送與 Docker／擁有權／
  原版素材檢查在收尾一併完成。

## 2026-09-21：完成目標 024 的首畫面正常輸入觀測

- 從同一 2M state v3 以單一 BIOS 緩衝區 Enter 與 `(160,100)` 單次左鍵各自重播至 12M；兩者都使原版進入
  相同的 `OPENING.PIK` 與 15 個 `OPEN*.SS` 開場資產載入分支。Enter 在 `int 16h AH=00` 取走，左鍵在
  `int 33h AX=0003` 觀測為按下；精確步數、report 與 VRAM 雜湊已記入 `RESEARCH-LOG.md`。
- 同一窗口沒有全形／半形字型 hook、B8000 或主控台字元，因此沒有把開場資產或畫面變化誤稱為動態文本。
  `-press enter` 的 IRQ1 測試因沒有 `int 09h` handler 而未送達遊戲，僅記為 probe 注入途徑限制。
- Issue #5 保持進行中並已更新本輪收據；工作清單、README、CONTEXT 與第 024 輪目標已回填。所有中間 report／
  VRAM／PNG 留在 gitignore 的 `workplace/reports/`，原版素材未被納入版控。

## 2026-09-21：完成目標 025 的開場靜態圖像候選清冊

- 從第 024 輪已確認的 BIOS Enter 路徑重播至 5.5M，以實際 DOS 檔案服務列出 2 個 `.PIK` 與 14 個 `.SS`；
  每項的大小、SHA-256、開啟步數與主要 payload offset／長度已寫入 `RESEARCH-LOG.md`，中間 report 與 VRAM
  仍只在 `workplace/reports/`。
- 終點畫面為 mode 13h 的 64,000 非零像素且有 101,639 筆 VRAM 寫入，但每檔至螢幕矩形的資料流、文字存在與
  幾何均保留 unknown。沒有以檔名、大小或像素存在假設靜態文字，沒有建立 DRAFT／READY、覆蓋程式或原型。
- Issue #8 維持進行中並已更新本輪收據；工作清單、README、CONTEXT 與第 025 輪目標已回填。原版素材維持
  gitignore，收尾將一併檢查 Docker、擁有權與 Git 邊界。

## 2026-09-21：完成目標 026 的 `OPENING.PIK` 繪製資料流

- 從固定 3M state 的正常 BIOS Enter 路徑確認主要 `OPENING.PIK` payload 讀到 `5755` 原始緩衝區；在
  #4,104,159 由 `0AC2:04F4` 的 `MOVSB` 以 `DS=5755`、`ES=1C43` 寫入 canvas，並在 #5,464,375 由
  `0557:009F` 的 `REP MOVSW` 以 `DS=1C43`、`ES=A000` 將 canvas 跨列搬至 VRAM。
- 此兩件已證實事件中間仍有其他開場資產載入，故沒有把共用 canvas／VRAM 搬運誤報為 `OPENING.PIK` 的最終
  像素、螢幕矩形、圖像語意或文字存在證據；Issue #8 保持進行中，未建立 DRAFT／READY、原型或中文覆蓋。
- 更正 probe 使用方式：`-watch` 與 `-watch-video` 會爭用單一 `WatchWrites` callback；本輪以只啟用
  `-watch` 的重跑收據完成定位，這是命令組態修正，不是遊戲或執行器功能缺口。
- 本輪 receipt／state／VRAM 仍只留在 gitignore 的 `workplace/reports/`。文件、Issue、Git 推送與 Docker／
  擁有權／原版素材邊界會在收尾一併核對。

## 2026-09-21：完成目標 027 的共享緩衝區覆寫勘誤

- 目標 026 的 `OPENING.PIK`→畫布結論已撤回：第 4,103,486 指令 `OPENBORD.PIK` 將 10,245 bytes 覆寫至
  `5755:0000`，早於第 4,104,159 指令 `0AC2:04F4` 的 `MOVSB`。其取樣來源 `SI=0007h–0BD9h` 全在覆寫範圍，
  因而不能再主張 `OPENING.PIK` 的資料到達畫布或 VRAM。
- 固定 4.099M–4.157M 窗口的 7,680 個不同畫布變更恰覆蓋 320×24 頂端列；672 次 `MOVSB` 是碎片化寫入，
  7,008 次由相鄰 `STOSB` 寫入。它們只描述 `OPENBORD.PIK` 覆寫後的共用處理窗口，沒有被誤稱為文字、
  圖像語意、`OPENING.PIK` 幾何或中文安全矩形。
- 兩次 `-dump-mem-at` 參數格式修正與一次裸位址空間誤用均已分類為 probe 命令問題；最後的有效結論只採
  固定 state、DOS 讀取、完整 stdout 監看、暫存器與原始指令 bytes。未修改 dosgolem、原版或中文覆蓋。
- 所有中間產物留在 gitignore 的 `workplace/reports/`；文件、Issue、Git 推送與 Docker／擁有權／原版素材邊界
  會在收尾一併核對。

## 2026-09-21：完成目標 028 的 `OPENBORD.PIK` 取樣資料流

- 固定 4.099M–4.157M 監看確認 `OPENBORD.PIK` 完整 payload 讀入共享 `5755` 緩衝區後未被觀測為內容改變；
  673 次 `MOVSB` 從該範圍取樣，並有 672 次對應到 `1C43` 畫布內容變更。
- 這只關閉原始緩衝區→取樣畫布資料流。值相同寫入仍不可由 watch 排除，且畫布變更的較後存續、最終像素、
  圖像語意、文字存在與中文安全矩形都維持 unknown；未建立任何 DRAFT／READY、原型或中文覆蓋。
- 所有 report 只留在 gitignore 的 `workplace/reports/`；文件、Issue、Git 推送與 Docker／擁有權／原版素材邊界
  會在收尾一併核對。

## 2026-09-21：完成目標 029 的畫布存續至一次 VRAM copy

- 從固定 4.1569M state 至 5.5M 監看，`1C430h–1E22Fh` 沒有內容變更事件；讀取監看留下無截斷的 7,680 筆，
  在 #5,464,375–#5,464,536 以 24 組、每組 320 bytes 的方式完整讀取該範圍。
- raw `0557:009F` 是 `F3 A5`／`REP MOVSW`；暫存器確認 `DS=1C43`、`ES=A000`、`CX=00A0` 與每列 `0140h`
  遞進。因此目標 028 的 672 次已確認資料流存續並進入這一次 A000 VRAM copy。值相同寫入、copy 後 VRAM、
  圖像／文字語意與中文安全矩形都維持 unknown，未建立 DRAFT／READY、原型或中文覆蓋。
- report 只留在 gitignore 的 `workplace/reports/`；文件、Issue、Git 推送與 Docker／擁有權／原版素材邊界
  會在收尾一併核對。

## 2026-09-21：完成目標 030 的 `OPENBORD.PIK` 可視文字檢查

- 固定 copy 完成 state 的 320×200 indexed frame 與 palette 在 Docker 中以新 `tools/render_indexed.go` 轉為本機 PNG；
  同時從已確認的 A000 offset `0000h–1DFFh` 建立 320×24 crop。probe 的 `-shots` callback 時序已以 `-steps` 加一
  修正，屬工具旗標時序，不是遊戲差異。
- crop 是重複的幾何裝飾邊框，無可辨識文字；因此該 `OPENBORD.PIK` 資料流範圍被排除為靜態文字候選。完整資產、
  copy 後畫面、其他 PIK／SS、文字與中文安全矩形維持 unknown，未建立 DRAFT／READY、原型或中文字型。
- indexed frame、palette 與 PNG 僅留在 gitignore 的 `workplace/reports/`；文件、Issue、Git 推送與 Docker／
  擁有權／原版素材邊界會在收尾一併核對。

## 2026-09-21：完成目標 031 的完整 composite frame 靜態文字普查

- 從固定 state 的 172,140 筆完整讀取監看中，精確篩出 #5,464,375–#5,465,772 的第一個完整 copy：200 組、
  每組 320 bytes、合計 64,000 bytes，由 `0557:009F`／`REP MOVSW` 搬至 A000。後續 132 列局部重畫已分開，
  不被誤稱為同一 frame。
- fixed-step 本機畫面新增兩筆可見靜態文字候選：`OCEANVS OCCIDENTALIS` 地圖標籤與中央卷軸兩行小字；兩者
  尚未追到來源資產、繪製資料流、copy 後存續或中文安全矩形，未建立 DRAFT／READY、譯文、字型或覆蓋原型。
- `tools/render_indexed.go` 增加最近鄰放大與來源畫布裁切，並以本輪收據成功重跑；所有原版衍生檔仍只在
  gitignore 的 `workplace/reports/`。文件、Issue、Git 推送與 Docker／擁有權／原版素材邊界會在收尾一併核對。

## 2026-09-21：完成目標 032 的海洋標籤 canvas writer 與部分來源追溯

- 從固定 4.1569M state 篩回真正 `opening-map-ocean-label` 矩形的 2,345 筆內容變更：全由
  `03BD:00C8`／`REP MOVSW` 寫入 canvas。前置暫存器、來源與目的切片、step 範圍及 report 雜湊已寫入
  `RESEARCH-LOG.md`；沒有把外包矩形的鄰近像素納入結論。
- 在正常 BIOS Enter 路徑，來源暫存切片的 120 筆內容變更先發生於 #3.225M；其中 15 筆可與
  `OPENING.PIK` 原始緩衝區的同一步數讀取精確配對。其餘 105 筆雖由同一解碼迴圈的填色分支寫入，未被冒稱為
  已完成逐像素原始資料依賴；整則標籤歸屬維持強推論。
- 本輪結果不恢復目標 026 已撤回的較晚共享緩衝區主張；`OPENBORD.PIK` 覆寫發生後，這個更早生成的暫存切片
  已是獨立資料流。完整資產歸屬、copy 後穩定存續與中文安全矩形仍 unknown，未建立 DRAFT／READY、原型、譯文或字型。
- Issue #8 維持進行中；收尾將驗證 worklist render／verify、文件、Git、Docker、擁有權與原版素材邊界，並附上本輪
  提交與 Issue 更新。

## 2026-09-21：完成目標 033 的海洋標籤 copy 後存續

- 長窗 canvas watch 的 200 筆容量不足以支持「copy 後零變更」；此工具限制沒有被當成證據。改用第 #5,465,772
  完整 copy 後的可重載 state，分別監看畫布與 A000 的精確標籤列範圍到 #5,500,000。
- 兩份獨立 watch TSV 都是零位元組，起點／終點全畫面與調色盤也逐位元組相同；兩份 121×12 標籤裁切 PNG 的雜湊
  相同。這只確認此正常路徑的有限窗口存續，不外推為永久畫面、完整資產歸屬或中文安全矩形。
- 沒有建立 DRAFT／READY、覆蓋原型、譯文或字型；原版衍生 state、frame、palette、TSV 與 PNG 皆留在 gitignore
  的 `workplace/reports/`。Issue #8 維持進行中；收尾將驗證文件、Git、Docker、擁有權與原版素材邊界，並附上本輪
  提交與 Issue 更新。

## 2026-09-21：完成目標 034 的完整開場畫面後單次 Enter 探測

- 從同一 #5,465,772 固定 state 重播控制組與單一 BIOS Enter 組。控制組持續 mode 13h 至 #7,000,000；Enter
  在 #5,465,827 取走，之後切回文字模式並以 `AH=4Ch, AL=6Ch` 終止，未到預定終點。
- Enter 路徑沒有新檔案、主控台、B8000 或字型 hook。mode 03h 後 A000 的殘留資料已明確排除為可見畫面證據；
  動態文字呼叫點／來源仍 unknown。下一個最小前沿是正式啟動器或父程序對 `0x6C` 的消費者，而非重複盲注同一畫面。
- 所有 state、report、trace 與畫面傾印保留在 gitignore 的 `workplace/reports/`；未建立 DRAFT／READY、譯文、字型或
  覆蓋程式。worklist render／verify 與 `git diff --check` 通過；commit `6ba7424` 已推送至私有 `main`，
  [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5759322874) 已回填且保持進行中。收尾確認
  無 `colonization` 容器、沒有 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離的 dosgolem 副本乾淨且 push
  URL 仍是 `DISABLED`。

## 2026-09-21：完成目標 035 的批次啟動鏈與 `0x6C` 消費者邊界

- 根層的兩個 batch 候選均以最後一行 `opening` 啟動開場，沒有其後的 source-level 離開碼分派；
  `COLONIZE.BAT` 是一般入口候選而非已證實的啟動器。沒有保存批次原文。
- dosgolem 的最小 probe 將 `.BAT` 從 `0100:0100` 作為 COM 式程式碼執行，沒有 batch／`COMMAND.COM`
  直譯能力；這是能精確重現的工具缺口，未被誤寫成 DOS shell 或遊戲的離開碼語意。
- report 留在 gitignore 的 `workplace/reports/`，原版素材未受版控；未建立 DRAFT／READY、譯文、字型或覆蓋程式。
  worklist render／verify 與 `git diff --check` 通過；commit `b1999e0` 已推送到私有 `main`，
  [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5759528876) 已回填且保持進行中。
  收尾確認沒有 `colonization` 容器、沒有 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本
  乾淨且 push URL 維持 `DISABLED`。

## 2026-09-21：完成目標 036 的完整開場畫面中央左鍵

- 從目標 033 的固定完整畫面 state 對照無輸入與唯一 `(160,100)` 左鍵。控制組保持 mode 13h 至 #7,000,000；
  左鍵在 #5,465,840 被 `int 33h AX=0003` 讀取後，於 #5,509,826 以 `AH=4Ch, AL=6Ch` 終止。
- 左鍵路徑沒有動態文字輸出、檔案、主控台、B8000 或字型 hook；mode 03h 的 A000 殘留不作畫面證據。
  不把此點命名為按鈕或場景，亦不掃描其他座標。
- 所有 report／trace／frame 仍在 gitignore 的 `workplace/reports/`；原版素材未受版控，未建立 DRAFT／READY、
  譯文、字型或覆蓋程式。worklist render／verify 與 `git diff --check` 通過；commit `69df4b6` 已推送至私有
  `main`，[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5759665906) 已回填且保持進行中。
  收尾確認沒有 `colonization` 容器、沒有 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本
  乾淨且 push URL 維持 `DISABLED`。

## 2026-09-21：完成目標 037 的滑鼠輪詢第一個控制流分歧

- 同一固定 state 的 427 指令短窗比較確認 `int 33h AX=0003` 回傳後，在 `0110:0952–0954` 以 AX 是否非零
  分岔；這是按下 boolean consumer，不是座標 hit-test 或按鈕語意。左鍵支路對 `[BP-0Ah]` 寫入 `001Bh`，
  欄位／常數語意仍未知。
- IDA 9.4 映像的技能指定工具契約文件不可定位，故沒有把未驗證 IDA 輸出當成證據；本輪只使用 dosgolem 的
  raw trace／dump，所有產物在 gitignore 的 `workplace/reports/`。
- 原版素材未受版控，未建立互動區清冊、DRAFT／READY、譯文、字型或覆蓋程式。文件、worklist、Issue #5、
  Git 推送與 Docker／擁有權邊界已核對；worklist render／verify 與 `git diff --check` 通過，commit `b3740cc`
  已推送至私有 `main`，[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5759929404)
  已回填且保持進行中。收尾確認沒有 `colonization` 容器、沒有 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，
  隔離 dosgolem 副本乾淨且 push URL 維持 `DISABLED`。

## 2026-09-21：完成目標 038 的 AX boolean producer call

- raw dump／trace 確認 `0110:094A → 0924:0588 → 0110:094F` 是 AX boolean 的直接 producer call／return 邊；兩個 stack-local pointer 為引數，但沒有型別或座標語意結論。
- 沒有新輸入、互動區清冊、DRAFT／READY、譯文、字型或覆蓋程式；所有 raw 產物只留 gitignore 的 `workplace/reports/`。文件、worklist、Issue #5、Git 推送與 Docker／擁有權邊界將在收尾一併核對。

## 2026-09-21：目標 039 的滑鼠 producer 資料流與 trace/raw 對齊勘誤

- 從相同固定 state 取零指令與 428 指令後的 `0924:0560:128` raw dump，兩者雜湊完全相同，排除本輪窗口的
  自修改。控制／左鍵兩組仍可重播至 `0110:094F` 的 AX `0`／`1` 回傳。
- 同時發現 `0924` 段 trace IP 與 raw dump 有可重現的 4-byte 對齊差異；這不是遊戲語意，也沒有被拿來推論
  pointer、座標、hit-test、按鈕或動態文字。下一輪先以最小重現釐清 dosgolem 的觀測契約，未建立
  DRAFT／READY、譯文、字型或覆蓋程式。
- `tools/worklist.py render`／`verify` 與 `git diff --check` 通過；證據文件 commit `6067dbd` 已推送到私有
  `main`，並已回填 [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5760381691)，維持
  OPEN／進行中。收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，
  隔離 dosgolem 副本乾淨且 push URL 為 `DISABLED`。

## 2026-09-21：完成目標 040 的 dosgolem 遠呼叫觀測對齊勘誤

- 同次重疊 dump 證實 `0560h + 28h = 0588h`；先前讀錯 hexdump 行內位移，並沒有 4-byte trace/raw 差異。
  far pointer、raw `ENTER`、BP/SP transition 與後續 `XOR BX` 均相符，沒有修改 dosgolem。
- 這項勘誤恢復目標 039 的 raw 資料流：CX／DX 確實寫回兩個 caller local pointer，AX 是 `BX OR [DS:5AB4]`。
  位址語意、hit-test、控制項、文字與中文覆蓋資格仍未知；未建立 DRAFT／READY、譯文、字型或覆蓋程式。
- `tools/worklist.py render`／`verify` 與 `git diff --check` 通過；勘誤證據 commit `fd376df` 已推送到私有 `main`，
  並已回填 [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5760620262)，維持 OPEN／進行中。
  收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本乾淨且
  push URL 為 `DISABLED`。

## 2026-09-21：目標 041 的滑鼠 producer 狀態閘門與 caller locals

- 在既有控制／中央左鍵兩條固定重播路徑的 call 前後，`DS:5AB4=0`、`DS:5E6C=FFFF`、快取座標 `A0h/64h`
  均不變；兩個 caller locals 都被寫為 `64h/A0h`。左鍵只使 service 後 BX 與 caller AX 從 0 改為 1。
- 這是固定 state 的資料流，未替 DS word、座標、控制項或文字命名；仍無動態文字輸出、譯文、字型、DRAFT／READY
  或覆蓋程式。所有原版衍生收據留在 gitignore 的 `workplace/reports/`。
- `tools/worklist.py render`／`verify` 與 `git diff --check` 通過；證據 commit `8a84269` 已推送到私有 `main`，
  並已回填 [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5760793897)，維持 OPEN／進行中。
  收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本乾淨且
  push URL 為 `DISABLED`。

## 2026-09-21：目標 042 的海洋標籤背景安全幾何

- 固定完整 frame 的 canvas／A000 rows 逐位元組相同，但標籤與有限外框共享大量色號，且主色的非背景連通區跨越
  候選邊界；這排除了目前證據下的均一／主色平面清除策略。
- 沒有製作中文、字型、遮罩、DRAFT／READY 或覆蓋程式。後續必須取得獨立的 pre-text 背景證據或轉查別的靜態候選，
  不能把可見文字外框當安全矩形；所有原版衍生 report 維持 gitignore。
- `tools/worklist.py render`／`verify` 與 `git diff --check` 通過；證據 commit `bc444d5` 已推送到私有 `main`，
  並已回填 [Issue #8](https://github.com/wicanr2/colonization_cht/issues/8#issuecomment-5761020917)，維持 OPEN／進行中。
  收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本乾淨且
  push URL 為 `DISABLED`。

## 2026-09-21：完成目標 043 的中央卷軸候選 canvas writer

- 已把 `opening-scroll-two-line-text` 候選收斂為靜態畫面鏈：`04A2:017A` 是已見的 canvas 解碼 writer，
  `0557:00A1` 是 canvas→A0000 copy 端點；第 #5,465,772 步的 7,420-byte 候選外包範圍兩端逐位元組相同。
- 本輪更正早期快照的位址格式：`-dump-mem-at` 的裸 `25E84` 依 IDA 基準換算，正式收據均使用執行期
  `lin:25E84`。此更正不改變遊戲行為結論。原文、字元邊界、特定資產歸屬、背景、安全矩形與覆蓋資格仍 unknown；
  未 OCR、未建立中文／遮罩／DRAFT／READY，也未修改 dosgolem。
- `tools/worklist.py render`／`verify` 與 `git diff --check` 通過；證據 commit `39acd80` 已推送至私有 `main`，
  [Issue #8](https://github.com/wicanr2/colonization_cht/issues/8#issuecomment-5761640910) 已回填且保持 OPEN／進行中。
  收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本乾淨且
  push URL 為 `DISABLED`。

## 2026-09-21：完成目標 044 的中央卷軸候選來源鏈

- 正常冷啟動確認 `MPSLOGO.SS` 在 #1,062,435 載入 `4DC3:0000`，解碼器在 #1,135,873 以
  `0AC2:0550`／`STOSB` 寫入 `3A6A8`；固定 state 的 `04A2:01EB` 隨後在 #3,757,195 讀取該位址並走向
  既有 canvas→A000 chain。完整候選圖的 `MPSLOGO.SS` 歸屬僅是強推論；原文、完整幾何與安全矩形仍未知。
- 未 OCR、未轉存原版內容、未建立譯文、字型、遮罩、DRAFT／READY 或覆蓋程式，且沒有修改 dosgolem；所有收據仍在
  gitignore 的 `workplace/reports/`。
- `tools/worklist.py render`／`verify`、`git diff --check` 通過；證據 commit `6805441` 已推送至私有 `main`，
  並已回填 [Issue #8](https://github.com/wicanr2/colonization_cht/issues/8#issuecomment-5762030275)，維持 OPEN／進行中。
  收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本乾淨且
  push URL 為 `DISABLED`。

## 2026-09-21：完成目標 045 的中央卷軸候選背景安全否定

- probe 的 `-dump-mem-at`／`-save-state` 在指定步數等於 `-steps` 上限時不會觸發；改以多跑一步、但維持原
  snapshot／state 步數後，取得真正第一筆 writer 前的 #3,756,003 與最後一筆後的 #3,759,075 同次收據。
- `04A2:017A` 寫入 254 bytes，從 zero-fill 改成跨越約略候選的單一連通區；它不是已確認的可見背景。因此拒絕以
  writer 前畫布或候選外框建立遮罩／安全矩形。原文、精確幾何、背景與覆蓋資格仍未知。
- 未 OCR、未轉存原版圖、未建立譯文、字型、遮罩、DRAFT／READY 或覆蓋程式，也未修改 dosgolem；原版衍生收據均維持
  gitignore 的 `workplace/reports/`。
- `tools/worklist.py render`／`verify` 與 `git diff --check` 通過；證據 commit `c79d796` 已推送至私有 `main`，
  並已回填 [Issue #8](https://github.com/wicanr2/colonization_cht/issues/8#issuecomment-5762461615)，維持 OPEN／進行中。
  收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本乾淨且
  push URL 為 `DISABLED`。

## 2026-09-21：完成目標 046 的既有左鍵非文字退出鏈

- 以 state SHA-256、隔離 dosgolem commit 與既有 `(160,100)` 左鍵重播，確認 `0110:0956` 的 `001Bh` local
  寫入後走入非文字退出鏈；現行收據在 #5,511,211 切 mode 03h、#5,511,836 以 `AH=4Ch, AL=6Ch` 終止。
- 補正目標 036 的較早精確終止步數：它未保存可比對的 state 雜湊和 dosgolem commit，故現行無 observer baseline
  無法重現該步數；保留歷史收據與新收據，沒有猜測差異來源。兩份現行收據都沒有主控台、B8000、字型 hook 或開檔
  文字事件，沒有建立訊息鍵、譯文、DRAFT／READY 或覆蓋程式。
- `tools/worklist.py render`／`verify` 與 `git diff --check` 通過；證據 commit `46e1cd1` 已推送至私有 `main`，
  並已回填 [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5762836904)，維持 OPEN／進行中。
  收尾確認無 `colonization` 容器、無 root 擁有檔或誤建 `.md` 目錄，原版素材未受版控，隔離 dosgolem 副本乾淨且
  push URL 為 `DISABLED`。

## 2026-09-21：完成目標 047 的海洋標籤 pre-text canvas 安全審查

- #5,432,822／#5,447,039 的同次 snapshot 顯示外包 3,961 bytes 全變；嚴格篩回後標籤 1,452 pixels 全變，
  並有 2,509 bytes 位於候選外。writer 前矩形全為 zero-fill，writer 後有 61 種非零色號；這不是已知可見背景。
- 完整 lifecycle 有 6,724 筆寫入，首／尾為 #5,432,823／#5,447,038，全部由 `03BD:00CA`（前一指令
  `03BD:00C8 = F3 A5`／`REP MOVSW`）產生。因 writer 跨未知圖像，明確拒絕以零值、單色、主色、外包或外框建立
  清除遮罩或中文安全矩形；不建立 OCR、原型、譯文、字型、DRAFT／READY、覆蓋程式或 dosgolem 修改。
- 證據文件 commit `6803bc5` 已推送私有 `main`，並已回填
  [Issue #8](https://github.com/wicanr2/colonization_cht/issues/8#issuecomment-5763198562)，維持 OPEN／in_progress。
  `tools/worklist.py render`／`verify` 與 `git diff --check` 通過。
- 收尾確認無使用 `colonization-research:20260920-r2` 的殘留容器，無 root 擁有檔或誤建 `.md` 目錄；收據均為
  UID/GID 1000:1000。兩份封存檔、DOS 輸入目錄均未受 Git 追蹤；隔離 dosgolem 副本乾淨、提交
  `1435f175e785ea096a9268cd1021a4222300bd43`，其 `upstream` push URL 為 `DISABLED`。

## 2026-09-22：完成目標 048 的 `VICEROY.EXE` direct-entry 診斷

- 固定 direct-entry 在 #2,216 的 `0020:00D3=FF D4` 以 `SS:SP=26F5:4028` 呼叫 stack pointer，#2,217 轉至
  `0020:4028` 並將 SP 壓為 `4026`，之後由 `0020:402A=7E FE` 永久自迴圈。這是已觀測堆疊控制流，不把它命名為
  遊戲功能、正常入口或 emulator bug。
- #1M–#5M 無輸入收據沒有未實作 CPU／DOS／BIOS／EMS 服務、檔案、畫面、I/O、主控台或字型事件，VRAM 維持
  全零且相同。沒有形成可實作的通用缺口；未建立 DRAFT／READY、文本鍵、譯文、字型、覆蓋、原型或 dosgolem 修改。
- 證據文件 commit `93c38b8` 已推送至私有 `main`，並已回填
  [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5763736686)；固定輸入檔名的
  [勘誤](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5763754028) 已追加。Issue 維持 OPEN／in_progress。
  `tools/worklist.py render`／`verify` 與 `git diff --check` 通過。
- 收尾確認無使用 `colonization-research:20260920-r2` 的殘留容器，無 root 擁有檔或誤建 `.md` 目錄；收據均為
  UID/GID 1000:1000。兩份封存檔、DOS 輸入目錄均未受 Git 追蹤；隔離 dosgolem 副本乾淨、提交
  `1435f175e785ea096a9268cd1021a4222300bd43`，其 `upstream` push URL 為 `DISABLED`。

## 2026-09-22：完成目標 049 的根層啟動引用候選清冊

- 在固定 DOS manifest 的根層 `.BAT`／`.COM`／`.EXE` 中建立 9 檔唯讀 metadata 清冊。精確大寫 ASCII `OPENING`
  只在同名 `OPENING.EXE` 有 5 筆命中，`VICEROY` 只在同名 `VICEROY.EXE` 有 4 筆；沒有不同根層候選含任一 token。
  這是靜態檔名引用，不能升格成 DOS EXEC、父程序情境（parent context）、stack setup、exit-code 消費或玩家路徑。
- 根層以外候選、動態組字、環境／磁碟 launcher、實際 parent 與 `VICEROY.EXE` 正常轉交均維持 unknown；沒有執行候選、
  建立 batch interpreter、DRAFT／READY、譯文、字型、覆蓋或 dosgolem 修改。報告 SHA-256
  `c9a6327b505fffb2046a662365ec886658b72dd9b3245d983a6d8aebeebc36c0` 僅保留在 gitignore 的 `workplace/reports/`。
- 證據文件 commit `b0d225b` 已推送至私有 `main`，並已回填
  [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5763990084)；Issue 維持 OPEN／in_progress。
  `tools/worklist.py render`／`verify` 與 `git diff --check` 通過。
- 收尾確認無使用 `colonization-research:20260920-r2` 的殘留容器，無 root 擁有檔或誤建 `.md` 目錄；收據均為
  UID/GID 1000:1000。兩份封存檔、DOS 輸入目錄均未受 Git 追蹤；隔離 dosgolem 副本乾淨、提交
  `1435f175e785ea096a9268cd1021a4222300bd43`，其 `upstream` push URL 為 `DISABLED`。

## 2026-09-22：完成目標 050 的子目錄啟動引用候選清冊

- 正確固定輸入根目錄 `SMColoni/COLONIZE` 的至少一層子目錄中，`.BAT`／`.COM`／`.EXE` 候選為零，因此
  `OPENING`／`VICEROY` 的靜態 token 命中也為零。這只限副檔名集合，不能外推不存在其他 launcher 或動態文字路徑。
- 初次將 `SMColoni` 父目錄掛為 `/game` 的探針只重複第 049 輪根層結果；它未採用、未寫入 GitHub 證據，已由正確
  根目錄重跑覆蓋。最終報告 SHA-256 `30f15c4490e6728f77783e38c5ff1c4c8d131df413ea899625ef274fc72d4836`
  僅留在 gitignore 的 `workplace/reports/`。
- 證據文件 commit `6267855` 已推送至私有 `main`，並已回填
  [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5764111292)；Issue 維持 OPEN／in_progress。
  沒有執行候選、建立 batch interpreter、DRAFT／READY、翻譯、覆蓋或 dosgolem 修改；`tools/worklist.py render`／`verify`
  與 `git diff --check` 通過。
- 收尾確認無使用 `colonization-research:20260920-r2` 的殘留容器，無 root 擁有檔或誤建 `.md` 目錄；收據均為
  UID/GID 1000:1000。兩份封存檔、DOS 輸入目錄均未受 Git 追蹤；隔離 dosgolem 副本乾淨、提交
  `1435f175e785ea096a9268cd1021a4222300bd43`，其 `upstream` push URL 為 `DISABLED`。

## 2026-09-22：完成目標 051 的開場畫面座標格視覺清冊

- 從既有 #5,465,772 完整 composite frame 的 indexed frame、palette、state 產生本機 672×432 PNG：320×200
  logical 畫面的 2 倍放大，格線每 16、標示每 32 logical pixels。PNG／metadata SHA-256 分別是
  `24abdb08a2d7c72c22f80e19999fd1638cb345e447ee84f928e822571a412f7c`／
  `aa81ec34a37cfda4c16f5f12e8f4cc83bbc85f90014c164e54a71e4997097a56`，均只留在 gitignore reports。
- 相同輸入已重跑並得到同一組雜湊。只以本機檢視確認座標格存在；沒有 OCR、原文轉錄、控制項命名、輸入注入或狀態
  轉移。格線不是按鈕、玩家路徑、文字或翻譯／覆蓋證據；下一個輸入必須由使用者先選擇正常操作意圖。
- 證據文件 commit `a7adf82` 已推送至私有 `main`，並已回填
  [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5764301496)；Issue 維持 OPEN／in_progress。
  未建立 direct-entry、batch interpreter、DRAFT／READY、翻譯、覆蓋或 dosgolem 修改；`tools/worklist.py render`／`verify`
  與 `git diff --check` 通過。
- 收尾確認無使用 `colonization-research:20260920-r2` 的殘留容器，無 root 擁有檔或誤建 `.md` 目錄；收據均為
  UID/GID 1000:1000。兩份封存檔、DOS 輸入目錄均未受 Git 追蹤；隔離 dosgolem 副本乾淨、提交
  `1435f175e785ea096a9268cd1021a4222300bd43`，其 `upstream` push URL 為 `DISABLED`。

## 2026-09-22：完成目標 052 的已知退出輸入座標標記

- 在第 051 輪的本機 grid 重建結果 SHA-256 相符後，以既有 mapping `x=32+logical_x×2`、`y=logical_y×2`
  將目標 046 已觀測的 `(160,100)` 左鍵位置標到 `(352,200)`。紅色 3-pixel cross marker PNG／metadata
  SHA-256 是 `862875cb3d253f11fc83689f11bcbf450ff190ce77ad57df9dd5c85b9ca73693`／
  `76cdbca266cb2ab8c16acf9322a3c90b072f52066edaefb2be882afdfabea071`，僅留在 gitignore reports。
- 相同輸入已重跑並得到同一組雜湊。marker 只提示此 fixed state 左鍵會非文字退出，不是按鈕、控制項、玩家路徑、
  文字或翻譯／覆蓋證據；沒有輸入注入、OCR、direct-entry、batch interpreter、DRAFT／READY、翻譯、覆蓋或 dosgolem 修改。
- 證據文件 commit `a297246` 已推送至私有 `main`，並已回填
  [Issue #5](https://github.com/wicanr2/colonization_cht/issues/5#issuecomment-5764421953)；Issue 維持 OPEN／in_progress。
  `tools/worklist.py render`／`verify` 與 `git diff --check` 通過。
- 收尾確認無使用 `colonization-research:20260920-r2` 的殘留容器，無 root 擁有檔或誤建 `.md` 目錄；收據均為
  UID/GID 1000:1000。兩份封存檔、DOS 輸入目錄均未受 Git 追蹤；隔離 dosgolem 副本乾淨、提交
  `1435f175e785ea096a9268cd1021a4222300bd43`，其 `upstream` push URL 為 `DISABLED`。

## 2026-09-22：重排滑鼠調查與中文化主路徑

- 重新核對目標 034／041／046／048／052：中央左鍵會令開場退出，但現有資料沒有證明 `(160,100)`
  是控制項或座標決定退出。前輪要求使用者猜下一個座標的閘門撤回；舊研究收據保持原樣。
- 建立目標 053 與 Issue #25，以同狀態座標對照及正常遊戲啟動鏈作下一個可驗證關卡。
  Issue #5 改為依賴正常玩家路徑；Issue #8 靜態圖像研究維持獨立。
- 建立 Issue #26 作第一則真實訊息的中文顯示垂直切片；字型、術語、發布方式等真正價值取捨
  仍保留給使用者於有原型或交付證據時決定。本輪只重排計畫，未宣稱已進入遊戲或已有中文覆蓋。

## 2026-09-22：完成目標 053，回到真正的遊戲選單

- 固定舊開場狀態的三個點擊位置有相同控制流；無輸入與只移動不退出。撤回猜座標門檻。
- 查明正常批次入口帶 `-g`，先前漏參數的開場研究不是完整遊戲啟動鏈。
- 規格 006–008 先審查為 READY，在隔離 dosgolem 修正 BIOS 馬達倒數、滑鼠回呼交換與
  檔案快照滑鼠狀態；單元與正常路徑驗收後記為 CONFORMED。
- 由 OPENING 冷啟動到 VICEROY 主選單，滑鼠點新世界進入難度畫面。連續執行與快照重播的
  索引畫面、色盤一致；無輸入控制組留在主選單。DOSBox-X 僅作輔助場景確認。
- 隔離提交 `22664265ea7d55ea8706448149908c79d3f0897b`；未推送或修改共用 dosgolem，
  `upstream` push 仍為 `DISABLED`。新增可重跑的兩個探針及可重建全部本地修正的源碼補丁。
- `go test ./...`、腳本語法、工作清單驗證、補丁重建 tree 比對通過。
  首次新增測試曾用錯 MouseEvent 參數，已修正測試呼叫並在相同容器重跑通過；不是遊戲缺陷。
- README 移除逐輪敘事、保留穩定入口與完整目標索引；CONTEXT 改為目前狀態表。
  歷史依 RESEARCH-LOG、WORKLOG 及各輪目標保留，未覆寫舊證據。
- 建立目標 054／Issue #5 的下一步：一則真實主選單文字的來源、印字事件與畫面，
  不再以靜態開場背景或猜測滑鼠位置阻擋中文化。Issue #26 仍是第一則中文顯示里程碑。
- Docker：所有一次性容器採 `--rm`；輔助 GUI 容器已停止移除。工作根擁有權掃描無
  root-owned 產物或誤建 `.md` 目錄；原版、畫面、快照均留在忽略的本機目錄。

## 2026-09-22：中文化開工，完成第一則文字證據與離線原型

- 依使用者要求先推送既有提交 `ccfeb4c`（遠端已同步），確認儲存庫維持 PRIVATE，
  再派翻譯、工程與字型查核三個子代理；主代理整合證據、規格、測試與交接。
- 目標 054 達成：正常冷啟動追到 GAME.TXT 檔案位移 0x1B0、`937C:0538` 印字事件與
  離屏畫布 180 個像素。滑鼠正常移開後像素全存續；兩次獨立冷啟動的事件、記憶體及畫面一致。
  IDA 9.4 保存原始位址、bytes、xref、推論等級及本機 `.i64`，不改遊戲函式名稱。
- `text/` 是 AGENTS 已指定的譯文層；本輪首次加入 50 筆 UTF-8 TSV 草稿及來源驗證器。
  來源 bytes、CRLF、占位符及控制碼全部通過。只一列已動態命中，不宣稱全遊戲覆蓋率。
  本機完整原文盤點保留歷史，譯文只維護版本化 TSV，避免雙重來源。
- 目標 055 已有一列中文／原文離線對照。首列讀取 TSV，不改遊戲記憶體或存檔；
  只還原經驗證的文字像素。主代理重跑 14 項測試全部通過，並重生 PNG／收據。
  圖片、字型、完整原文、遊戲記憶體均只留本機；原型未接即時執行路徑。
- 字型候選為 Cubic 11 24px，4 倍輸出；使用者尚未確認。規格 009 維持 DRAFT。
  字型內嵌許可不是 OFL，也不沿用 psychic-war 倚天授權；正式散布需獨立審查。
- 調查中的探針初次編譯曾誤用 PushKey 型別／一起編譯既有 observe.go，已修正為
  明確 Key 結構與單檔建置並乾淨重跑；屬研究腳本問題，不是原版遊戲缺陷。
- README 僅更新穩定現況；CONTEXT、目標 054／055、規格及工作清單同步區分：
  已完成一列證據／離線原型、待視覺決策、未完成正式即時覆蓋。Issue #6 仍欠三種輸出情境，
  #7 仍欠覆蓋率與未知命中量測，#26 仍欠互動生命週期，不能提前關閉。
- Docker 即用即刪；研究、渲染與 IDA 映像均無殘留容器。擁有權、原版誤追蹤與文件檢查
  於提交前重驗；隔離 dosgolem 未新增修改，共用 dosgolem 未動，上游推送仍 DISABLED。
- 完成提交 `0ee9449` 並推送私有 `main`；Issue #5 已關閉，#6／#7／#26 更新為 in_progress，
  #10 追加視覺候選與權利限制，維持待使用者決策。遠端留言保留驗收界線，不上傳本機圖片。
  工作清單重生／驗證、Python 語法、IDA 證據欄位、相對連結及 `git diff --check` 全通過；
  工作根擁有權掃描無 root 擁有檔或 `.md` 目錄，原版及本機產物未被追蹤。

## 2026-09-22：採用字體大小，接通第一列執行中中文

- 使用者確認 Cubic 11 24px、4 倍輸出；目標 055 完成。不將此決定延伸為字型散布、
  全遊戲術語或完整中文化範圍授權。
- 三個子代理分工追查印字生命週期、校對 50 筆譯稿及實作觀測／合成機制；主代理審查、
  整合並重跑正常啟動路徑。沿用公開 API，不因研究包裝器限制而重造平台功能。
- 規格 010／011 先 READY 後實作與驗證；規格 009 僅第一列的有限切片達 CONFORMED。
  隔離 dosgolem 提交 `315d17f6697bcd4040b12749a1038fdf677338f8`，共用副本未修改。
- 七組正常路徑的 CPU、完整記憶體、原始畫面與虛擬時間一致；272 幀、15 個檢查點，
  105 張圖獨立像素檢查通過。中文畫面與已確認原型逐像素相同；錯誤執行檔在啟動前拒絕。
- 完整 Go 測試通過；通用合成套件敘述覆蓋率 100%，不是全遊戲覆蓋率。測試資料索引
  錯誤已修正並重跑，未將測試腳本問題誤列為產品缺陷。
- 補丁從既定基底重建的 Git tree 為 `e223a8c97204df98ff444e32cdb0ec205b187e90`，
  與隔離提交相同。可重跑入口及本機收據索引見 [目標 056](docs/goals/056-live-menu-overlay.md)。
- 仍只有兩種文字情境；游標遮擋首列時回退英文，尚無可手動遊玩的視窗前端。
  Issue #6／#7／#11／#26 保持未完成；#10 的字體決策已解決，其他決策仍待適當里程碑。
- 本輪一次性容器均已刪除，未清理其他專案容器；原版畫面、字型、字模與記憶體收據留在
  忽略的 workplace。未建立發行包。
- 提交 `82111b2` 已推送私有 main；Issue #6／#7／#10／#11／#26 已追加進度，
  #11 改為 in_progress，未提前關閉任何未完成項。最終 Go 全套、Python 語法、工作清單
  與差異檢查通過；擁有權掃描無 root 殘留或誤建 `.md` 目錄，隔離上游推送仍為 DISABLED。

## 2026-09-22：先推送目標057，再擴展五列主選單

- 依使用者指定順序建立目標057與現況入口，提交 `0532568` 並先推送，再派翻譯／前端／
  事件補證子代理。後續分工完成通用多層合成與五列適配器，主代理整合、審查與驗收。
- 五列各三次事件，新增原始參數描述區證據；雙次71份二進位一致，也與目標056舊收據一致。
  窄規格012先DRAFT、補證後READY，再實作、同狀態驗收後CONFORMED。
- 主選單中文由一列擴到五列，維持Cubic 11 24px／4倍輸出，未改TSV文案或原版輸入。
  逐列回退、缺譯／缺字模／過期／過寬控制組及切場撤銷全部通過；其餘選項分支未驗。
- 五列七組與首列七組原版最終狀態一致；各105張圖獨立像素驗證通過，首列原型外觀不變。
  完整Go測試、overlay靜態檢查及14項原型測試通過。原型測試首次少掛原版與字型而skip，
  補唯讀掛載後同映像乾淨重跑；不將skip算通過。
- 首次五列測試錯把第三列墨跡完整視為安全區完整；舊原版圖證明游標尾端改變兩個背景像素。
  修正測試期望並重跑七組通過，未放寬程式守門，勘誤保存在規格012。
- 隔離引擎 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，新增通用獨立層合成；
  累積補丁從固定基底重建tree `8e775d62bc0642da4ecd5adf0d6c0eb3a0245162` 通過。
  共用dosgolem未改，上游推送仍DISABLED。
- 互動前端只完成查核：可沿用既有Ebitengine映像及視窗生命週期，但殖民帝國必須使用原生
  滑鼠，不能搬用psychic-war熱區轉按鍵。下一步抽離適配器再接視窗，沒有前端完成聲明。
- 本機字模／原版圖片／記憶體只留忽略的workplace，不製作發布包。Docker即用即刪，
  無本專案殘留容器；工作清單及Issue仍保留第三情境、整體覆蓋與互動前端缺口。
- 成果提交 `a33d17a` 已推送私有main；Issue #6／#7／#11／#26 已同步驗收與未完成界線。
  最終136個相對連結、工作清單、語法、素材版控及擁有權檢查通過，工作樹與遠端一致。
## 2026-09-22：目標058語料批次與真視窗切片

- 使用者要求派子代理翻譯至完整中文化方向；翻譯、語料盤點與前端原型分工，主代理獨立
  核對來源、顯示分母及視窗收據。新增Issue #27；全遊戲完成標準仍未定，不擅稱已完成。
- 18個DOS文字檔有4,119個粗略資料行；這不是訊息數，EXE與靜態圖像另未計。
  譯稿50→189筆，139筆新增；189筆來源位移、SHA、控制碼與熱鍵核對通過，Cubic 11
  缺字0。多義的`Complete`未合併；新譯文未取得畫面命中。
- 正常路徑仍只驗證主選單五筆中文顯示；固定兩份收據有一個未建檔來源片段。
  草稿、事件命中、畫面已驗收三種數量分開，不把資料行當全遊戲分母。
- 規格013限可撤回Linux視窗原型。真實Xvfb視窗與原生DOS滑鼠走五列中文主選單至
  難度畫面；九筆X輸入、100,000,000步、606幀。來源乾淨重建後，中文重播與英文無hook控制的CPU、
  完整RAM、原版索引圖、色盤及虛擬時間相同；兩張視窗圖逐像素對照通過。
  完整鍵盤、音訊、存讀檔、失焦／關窗實測與正式玩家版本仍缺。
- 首次視窗腳本因Xvfb作容器PID1等待及狀態檔未生成即檢查而失敗；只修正有界腳本，
  同環境重跑通過，並未改遊戲時鐘或輸入語意。譯稿進度報告首次掛到
  `SMColoni/` 而非`SMColoni/COLONIZE/`，明確SKIP後修正掛載並重跑189筆。
- 本機原文、字型、畫面、記憶體及暫存稿均在被忽略的`workplace/`，不入版控。
  六項譯稿回歸、189筆原版來源、字型與工作清單驗證通過；本專案無殘留容器、
  root擁有檔或誤建的`.md`目錄。私有儲存庫的提交與Issue同步另以GitHub現況核對。
## 2026-09-22：Ebitengine畫面接線目標059

- 使用者指定畫面配合Ebitengine，沿用既有Go 1.24／Ebitengine 2.9.9專用Docker映像。
  將五列適配器的視窗接點變成明確Go註冊，組裝器只複製固定SHA來源，不再以字串替換
  測試排程。單獨無頭程式仍可建置，未連結視窗卻要求`--window`時退出碼2拒絕。
- 在Xvfb真視窗以九筆實際輸入進入難度頁；中文與英文控制同輸入狀態一致，
  100,000,000步、606幀、5213 ticks、1,395,189,090 cycles。兩張真視窗圖逐像素通過；
  Ebitengine編譯、座標／釋放單元測試通過。收據獨立存為`goal059-ebiten-*`。
- 初次回歸使用工具舊預設前綴覆寫本機忽略的目標058收據，隨即補可指定前綴並以
  `goal059-ebiten`重新完整重跑；目標058歷史數值仍依規格013的當輪紀錄，不混用
  不同X輸入步號。未發布原版畫面、原始資料或字型。
- 真實失焦／關窗、完整鍵盤、存讀檔與難度頁中文仍是開放缺口；不因接線完成
  關閉Issue #26。Docker相關容器全以`--rm`結束，無本案殘留；工作根無root擁有檔
  或誤建`.md`目錄，語法檢查產生的四個pyc已逐一清除。Git與Issue於提交後核對。
## 2026-09-22：目標060說明訊息原文／繁中TSV

- 使用者要求將help訊息原文與譯文先放入GitHub。主機`gh`確認
  `wicanr2/colonization_cht`仍為私有；原文僅在此範圍內提交，不授權公開或封包。
- 唯讀盤點明確區塊後，建立`text/help-bilingual.tsv`：主遊戲19段教學、地圖編輯器
  5段說明，共24則整段訊息。每列保留來源檔SHA、章節／文字檔案位移、文字片段SHA、
  英文原文、繁中草稿及狀態；不複製原版檔或圖像。
- `tools/build_help_bilingual.py`可用固定合法原版重生與驗證；24／24筆來源、UTF-8、
  唯一鍵、占位符與顯示控制碼通過，另六項合成回歸通過。Cubic 11 24px沒有缺少可列印譯文字形。
  這些訊息尚未取得遊戲輸出事件／安全矩形，未加入189筆既有主目錄或五筆畫面命中。
- 本機臨時譯稿放在被忽略的`workplace/`，正式可審校雙語檔及驗證工具入版控。
  本案Docker容器均以`--rm`清理，工作根無root-owned或異常`.md`目錄；
  原版素材追蹤與私有推送於收尾核對。

## 2026-09-22：目標061先推送再追下一段畫面文字

- 先提交目標061與README入口，`27bc32c`已推送私有`main`；後續才開始難度頁追查。
- 使用既有正常滑鼠路徑的本機記憶體收據，確認標題與完成提示的執行期原文位置；
  新增規格014 DRAFT，明定尚缺印字事件與安全矩形，不擅將草稿升格為已顯示中文。

## 2026-09-22：難度標題中文覆蓋、真視窗圖與首頁整理

- 以唯讀 dosgolem 讀寫探針雙次重播同一輸入，確認兩段標題的執行期原文、
  `0D3A:0015` 讀取、`0D21:012C` 畫布寫入與 126／284 點差分；規格014
  經證據審查限縮至兩行 READY，實作後同狀態驗收為 CONFORMED。
- `tools/live_menu.go`只在原版事件及畫布守門通過時覆蓋；本機字模從唯一 TSV 與
  已確認 Cubic 11 24px 烘製。無頭中文／英文／缺字模控制的原版狀態相同；
  缺字模圖片與英文完全一致，游標遮擋時只回退受影響那一行。
- Ebitengine／Xvfb 九筆真實輸入到難度頁，中文原跑／重播／英文控制於一億步的
  完整原版狀態一致。兩行各有 433 個套用幀；獨立像素驗證證明中文圖的新增差異
  僅在兩個已審查安全區。最後截圖時將游標移到不遮字位置，兩行中文均可見。
- 使用者要求 README 不再列逐輪目標，已移除全部目標連結並改為穩定首頁。
  私有 `wicanr2/colonization_cht` 經主機 `gh` 再確認後，將兩張真視窗成果圖
  放入 `docs/screenshots/`，以精確 `.gitignore` 例外納管；公開使用權仍未知，
  不把截圖移入公開發行包。原版檔案、字型、快照均未入版控。
- 本輪 Docker 工作均用 `--rm`；研究、Ebitengine 與圖片驗證映像沒有本案殘留容器。
  工作根無 root-owned 檔案或誤建的 `.md` 目錄；新增圖檔、工具與產生的工作清單
  均由目前使用者擁有。
- 成果提交 `a369e44` 已推送私有 `main`；GitHub Issue #7／#26／#27 已更新，
  全局中文化、正式玩家版及 help 畫面仍保持開放。

## 2026-09-22：啟動完成提示切片

- 建立目標062，將下一個正常路徑目標限於難度頁完成提示。先推送目標與
  `CONTEXT.md` 入口，再按證據閘門追原文讀取、畫布差分與英文回退；
  README 不重列逐輪目標。此時尚未把該提示計為中文畫面。

## 2026-09-22：完成提示中文覆蓋與真視窗驗收

- 目標062起始提交 `8bb8f17` 已先推送私有 `main`。兩次獨立 dosgolem 重播確認
  完成提示的 `0E2D:11CF` 原文讀取、167點畫布差分及安全矩形，規格015由
  DRAFT 經證據審查升 READY，限定實作後以中英文同狀態結果標 CONFORMED。
- 從唯一TSV與已確認Cubic 11 24px烘製本機字模，`tools/live_menu.go` 以固定
  原文、讀取端與像素守門疊加「完成後點此」，原版記憶體不修改。無頭中文、
  英文及缺字模三組同狀態；缺字模英文回退圖與控制組相同。
- Ebitengine／Xvfb九筆真滑鼠輸入、606幀、5,213 tick 到難度頁；中文原跑、
  重播及英文控制於一億步的原版狀態一致，逐像素差異只在三個安全區。
  私有截圖更新至 `docs/screenshots/difficulty-zh.png`，README穩定狀態更新為八段；
  難度卡片及help仍未驗收。
- 工具測試及真視窗收據通過；工作清單由JSON在Docker重生。Docker容器均用
  `--rm`，收尾檢查容器、擁有權與原版檔追蹤狀態。

## 2026-09-22：啟動難度卡片文字切片並保持 DRAFT

- 建立目標063並以 `8a6c2fc` 先推送私有 `main`；本輪只研究選中第一張卡片
  可見的 `Discoverer`／`Easiest`，沒有擴張到難度規則或其他畫面。
- 擴充既有唯讀 dosgolem 探針，兩次正常滑鼠路徑重播；原始畫布文字區有
  224點差分，但候選 RAM 讀取及卡片區逐 byte 寫入監看均零命中。記錄
  [規格016](docs/spec/016-difficulty-card-text-draft.md) 為 DRAFT，不加入正式覆蓋。
- 卡片其他四種難度、動態／靜態來源分類、可逆背景與安全矩形尚待追查；
  八段已驗收中文數維持不變。Docker探針均以`--rm`執行；本機收據保留
  在已忽略的`workplace/reports/`，沒有推送原版畫布或字型。

## 2026-09-22：翻譯優先的三批可追溯譯稿

- 使用者要求先完成翻譯。建立目標064，明確把來源驗證的譯稿、執行期命中與
  畫面驗收分開；不把18份TXT的4,119個粗略資料行或譯稿筆數當成全文完成率。
- `MENU.TXT`新增48筆、`MAPEDIT.TXT`新增31筆（不重複既有help整則）、
  `NAMES.TXT`新增56筆無逗號純文字；主譯稿由189筆增至324筆。`NAMES.TXT`
  232筆含逗號複合資料未直接翻譯，`PEDIA.TXT`163個編號文章區塊多數待處理。
- Docker內重跑固定原版來源／片段SHA、CRLF、縮排、變數、控制碼、熱鍵與Cubic 11
  24px字型覆蓋，324／324通過、缺字0。發現`%Fs`名稱組合占位符未被原驗證規則完整
  辨識，已補強並加入兩個正反回歸測試；八項測試皆通過。
- 所有新增譯文維持`draft`，不加入八段畫面完成數。容器均用`--rm`；驗證收據只在
  忽略的`workplace/reports/goal064-translation-review.json`，不提交原版輸入或字型。

## 2026-09-22：完成百科建國元勳整段草稿切片

- 目標065先以 `8391215` 推送範圍與限制，再從固定 `PEDIA.TXT` 建立25篇
  `@FATHER0`–`@FATHER24` 的私有雙語TSV。原文逐段保存來源與片段指紋，沒有提交
  原版資料檔、字型或工作區暫存譯稿。
- 建立器將跨行文章的字面`\\n`與 `^`、`{}`、`%%`、變數分開核對；字型檢查一度
  將換行誤當缺字，已修正為略過非繪製空白字元並重跑。三項回歸、25篇來源驗證與
  Cubic 11 24px 覆蓋均通過，缺字0。
- 25篇全維持`draft`，未接入輸出層，PEDIA其餘138篇未譯。Docker均以`--rm`執行；
  收據只在 `workplace/reports/goal065-pedia-fathers-review.json`，收尾另核對容器、
  檔案擁有權與原版素材追蹤狀態。

## 2026-09-22：完成百科貨物整段草稿切片

- 目標066將 `@CARGO0`–`@CARGO15` 的16篇貨物文章接到既有25篇建國元勳語料。建立器
  先讀取既有正式TSV，再只接受不重複的新譯文鍵；避免重抄或無聲覆寫既有譯稿。4項
  合成回歸測試通過後，固定原版重生的百科TSV共有41篇。
- 41／41篇的原始檔與片段SHA、UTF-8、鍵、字面`\\n`、`^`、`{}`、`%%`及占位符通過；
  Cubic 11 24px覆蓋為零缺字。譯文一律為`draft`，未取得dosgolem輸出事件、安全矩形、
  Ebitengine畫面或正常玩家路徑命中，故不增加八段畫面完成數。
- Docker均以`--rm`執行，收據僅留在已忽略的
  `workplace/reports/goal066-pedia-cargo-review.json`；正式TSV由目前使用者擁有，
  原版檔案、字型與暫存提案均未納入Git。

## 2026-09-22：完成百科單位整段草稿切片

- 目標067將 `@UNIT0`–`@UNIT23` 的24篇單位文章接到既有41篇百科語料，建立器由
  固定原版重生共65篇TSV。原版只有標題的`@UNIT23`仍只保存標題，沒有為湊篇數增寫正文。
- 65／65篇的原始檔與片段SHA、UTF-8、鍵、字面`\\n`、`^`、`{}`、`%%`及占位符通過；
  Cubic 11 24px覆蓋為零缺字。兵種、船型與殖民歷史用語一律維持`draft`，未取得
  dosgolem輸出事件、安全矩形、Ebitengine畫面或正常玩家路徑命中，故不增加八段畫面完成數。
- Docker均以`--rm`執行，收據僅留在已忽略的
  `workplace/reports/goal067-pedia-unit-review.json`；正式TSV由目前使用者擁有，
  原版檔案、字型與暫存提案均未納入Git。

## 2026-09-22：完成百科地形整段草稿切片

- 目標068將 `@TERRAIN0`–`@TERRAIN28` 的29篇地形文章接到既有65篇百科語料，建立器由
  固定原版重生共94篇TSV。重複而有細微效果差異的森林文章仍各自保留鍵與譯文，不合併。
- 94／94篇的原始檔與片段SHA、UTF-8、鍵、字面`\\n`、`^`、`{}`、`%%`及占位符通過；
  Cubic 11 24px覆蓋為零缺字。地形、資源、方格與效果用語一律維持`draft`，未取得
  dosgolem輸出事件、安全矩形、Ebitengine畫面或正常玩家路徑命中，故不增加八段畫面完成數。
- Docker均以`--rm`執行，收據僅留在已忽略的
  `workplace/reports/goal068-pedia-terrain-review.json`；正式TSV由目前使用者擁有，
  原版檔案、字型與暫存提案均未納入Git。

## 2026-09-22：完成百科職業整段草稿與原始 Tab 契約

- 目標069將 `@JOB0`–`@JOB26` 的27篇職業文章接到既有94篇百科語料，建立器由固定
  原版重生共121篇TSV。`@JOB18`原文只有標題，目錄也只保存標題，沒有為湊篇數增寫正文。
- 原版 `@JOB8` 的 `^\\t` 使既有TSV格式失敗即關閉；使用者選定以字面`\\t`保留原始Tab，
  並要求譯文使用相同結構控制。建立器現在拒絕實際TSV Tab、只接受受控`\\t`逃脫，解碼後
  將其與`^`、`{}`、`~`、`_`逐序比較。`@JOB12 `尾端ASCII空白以固定原始marker定位，
  可見message key保持`@JOB12`；沒有修改原版或無聲strip來源。
- 121／121篇的原始檔與片段SHA、UTF-8、鍵、字面`\\n`／`\\t`、控制碼、`%%`及占位符通過；
  13項回歸與Cubic 11 24px覆蓋為零缺字。所有文章仍為`draft`，未取得dosgolem輸出事件、
  安全矩形、Ebitengine畫面或正常玩家路徑命中，故不增加八段畫面完成數。
- Docker均以`--rm`執行，收據僅留在已忽略的
  `workplace/reports/goal069-pedia-job-review.json`；正式TSV由目前使用者擁有，
  原版檔案、字型與暫存提案均未納入Git。

## 2026-09-22：完成百科建築整段草稿與項目符號正規化

- 目標070把42篇 `@BUILDING0`–`@BUILDING41` 接到既有121篇語料；固定原版重生的
  `text/pedia-bilingual.tsv` 現有163篇 PEDIA 編號文章。原文、譯文及片段指紋均維持
  私有儲存庫範圍，沒有提交原版檔、字型或工作區提案。
- 使用者確認將原始 CP437 `0xF9` 正規化為 Cubic 11 可繪製的 U+2022 `•`；建立器和回歸
  測試拒絕未知高位元組，並逐序驗證原文／譯文控制符號。此正規化保留原始位元組、位址和
  SHA 作證據，不是畫面覆蓋或字型 fallback 實作。
- `colonization-research:20260920-r2` 的15項 help／百科回歸測試及163篇來源驗證通過；
  `rich2-py:latest` 以 Cubic 11 24px 產生的忽略收據
  `workplace/reports/goal070-pedia-building-review.json` 顯示163篇來源／控制碼通過、缺字0、
  執行期畫面未驗證。八段已顯示中文數不變。
- 已更新目標070、目前狀態、README穩定摘要與機器可讀工作清單；本批完成後提交並推送到
  私有 `main`。Docker 容器皆使用`--rm`；收尾另核對容器、檔案擁有權與原版素材追蹤狀態。

## 2026-09-22：建立下一批單行譯稿的證據邊界

- 重新盤點18份 TXT，結果仍為4,119條粗略資料行，不能當成玩家可見訊息分母。`NAMES.TXT`
  的70條無逗號資料行已全數收錄；餘下232條複合列由214條名稱加數值規則資料及18條部族
  別名組成，沒有誤加到單行顯示候選。
- 建立目標071，範圍限定 `MAPMENU.TXT` 28筆選單、`WOODCUT.TXT` 14筆具語意標題及兩筆
  載入訊息，共44筆；動畫／座標資料及三個語意未知佔位名稱保持排除。先推送此範圍與
  退出條件，再建立譯稿與驗證器。Docker分析容器一律使用`--rm`，清冊留在忽略的
  `workplace/reports/goal071-text-inventory.json`。

## 2026-09-22：完成地圖編輯器選單、過場標題與載入訊息草稿

- 新增受限單行建立器；它只讀取原始 CRLF 行首，拒絕逗號複合資料、註解、指令、重複候選、
  缺譯與未知來源。`#` 加入主譯稿控制碼驗證，避免地圖選單的格式記號在翻譯時消失。
- 目標071的44筆由324筆主譯稿合成為368筆：28項地圖編輯器選單／說明入口、14個具語意
  過場標題與兩個載入訊息。`woodcut 14`至`woodcut 16`、動畫／座標與 NAMES 複合資料均未
  被加入；新譯文維持`draft`。
- Docker內全368筆固定來源與控制碼驗證、28項單行／百科／說明回歸通過；Cubic 11、24px
  審核缺字0，收據僅留於忽略的`workplace/reports/goal071-draft-review.json`。未驗證畫面、
  術語或變數展開，八段顯示完成數不變。本批完成後提交並推送私有`main`；收尾另核對
  容器、檔案擁有權與原版素材追蹤狀態。

## 2026-09-22：目標072 README 玩家補充說明譯稿計畫

- 以第一份 DOS ZIP 內 `SMColoni/COLONIZE/README.TXT` 的唯讀成員檔為證據來源；其 SHA-256 為
  `d78a219bfd041e3d4f3327d6b012dc433fd3734472c68cbace0490b9e46ac19e`，共7,477 bytes、195行。
- 依位元組邊界規劃七則玩家補充說明：版本前言／16項修正、地圖編輯器、作弊總覽與啟閉、
  主地圖、殖民地、歐洲三類作弊功能。DOS 設定、音效排錯與客服資料不進翻譯語料。
- 下一步是建立 ZIP 成員範圍的受限雙語 TSV 建置器與譯稿；它們一律維持 `draft`，不聲稱已有
  dosgolem 命中、Ebitengine 畫面或正常玩家路徑驗收。

## 2026-09-22：完成 README 玩家補充說明譯稿

- 新增 `text/readme-bilingual.tsv` 的7則原文／繁中草稿，以及受限 ZIP 成員建立器、六項回歸
  測試與字型審核器。它們固定封存檔／成員 SHA、範圍、片段 SHA，並拒絕重疊範圍、遺漏譯文、
  Tab、按鍵或符號序列不符。
- Docker 由唯讀 ZIP 暫時解包後，34項單元回歸、368筆主譯稿、24則help、163篇百科及7則
  README來源驗證均通過。Cubic 11 24px 審核為7則通過、缺字0；本機報告在
  `workplace/reports/goal072-readme-review.json`。
- 所有README譯稿維持`draft`；沒有新增 dosgolem 事件、Ebitengine畫面、安全矩形、正常玩家路徑
  或已顯示中文計數。已刪除唯一的臨時雙欄譯文提案檔。

## 2026-09-23：確認殖民地名稱與中文字級政策

- 使用者選定 `COLONY.TXT` 的殖民地名稱以「中文名稱（原名，年份）」呈現；沒有年份時省略年份。
  這只授權顯示譯稿，原始名稱與年份仍保留為語意隔離的穩定來源。
- 使用者明確排除全域固定中文字級。`AGENTS.md` 現要求每個覆蓋欄位依原版字級、基線與安全矩形
  選擇中文字級，並在 READY／CONFORMED 規格附上量測與回退證據；既有 Cubic 11 24px 只屬主選單
  原型的限定證據。

## 2026-09-23：目標073殖民地名稱譯稿計畫

- `COLONY.TXT` 的固定來源 SHA-256 為
  `2996f8a9d53a7f7a93e4a238bfd2ba727c4cf5cdabc334c4059c6860c9e4ae36`，有173筆預設名稱，
  其中18筆英國名稱帶四位年份。目標073以分欄來源模型保留名稱、逗號及年份，不直接改寫原版資料。
- 計畫採用使用者確認的「中文名稱（原名，年份）」格式；日後字型覆蓋檢查只驗可繪字元，
  不把固定字級或原版23字元儲存限制當成中文畫面驗收。

## 2026-09-23：完成殖民地名稱譯稿

- 新增分欄的 `text/colony-bilingual.tsv`、固定 ZIP 來源解析器、六項回歸測試及不設定字級的
  字型字元覆蓋審核器。173筆名稱與18個年份均符合「中文名稱（原名，年份）」格式；原名、年份、
  章節、行首及片段雜湊皆可由原始來源重建。
- Docker 內40項單元回歸，以及368筆主譯稿、24則help、163篇百科、7則README和173筆名稱的
  固定來源驗證均通過。Cubic 11字元覆蓋缺字0，報告在
  `workplace/reports/goal073-colony-review.json`，但不設定或驗證固定中文字級。
- 所有名稱維持`draft`，沒有新增 dosgolem 事件、安全矩形、Ebitengine畫面、正常玩家路徑或
  已顯示中文計數；已刪除唯一的臨時雙欄譯文提案檔。

## 2026-09-23：目標074難度卡片監看修正

- 先以提交 `5fc1ef6` 將[目標074](docs/goals/074-difficulty-card-observation-repair.md)推送到私有
  `origin/main`。發現舊探針重複註冊單槽讀寫監看器後，修正為各一次註冊、回呼內分流，
  並加入雙次收據檢查器；未修改 dosgolem 或原版資料。
- Docker 中 `go test ./internal/machine ./oracle` 通過。修正後從相同九筆正常玩家輸入兩次冷啟動
  至3,200萬步，`tools/check_difficulty_observer.py` 通過；兩段卡片原文來源與292次文字畫布寫入
  均命中，最終 RAM／畫布／索引畫面／色盤一致。詳見 `RESEARCH-LOG.md` 與規格016。
- 本輪未接入新的中文覆蓋，也未重開使用者尚未回答的 `NAMES.TXT` 分欄翻譯決策。
  殘餘工作是直接資料流、其餘卡片及欄位專屬字級／安全矩形；規格016維持 DRAFT。
  本機收據留在已忽略的 `workplace/reports/`；原始畫面快照及原版檔案未加入版控。
- 探針、檢查器與證據訂正提交為 `9d30311`，已推送私有 `origin/main`；收尾時工作樹乾淨，
  一次性 Docker 容器均已移除，未發現 root-owned 檔案或錯誤掛載產生的 `.md` 目錄。

## 2026-09-23：目標075追查難度卡片原文到像素

- 先以提交 `fb81bd7` 將[目標075](docs/goals/075-difficulty-card-source-to-pixels.md)推送私有
  `origin/main`。在 dosgolem 的正常九筆玩家輸入旁建立窄時間窗研究探針，分別讀取來源、
  共用緩衝、局部副本、逐字字形與卡片畫布；沒有改 dosgolem、原版檔案、遊戲狀態或正式顯示層。
- 兩次研究收據位元組完全一致；新檢查器驗證兩行完整資料流、兩次字形遍歷與逐行畫布差分。
  `go vet` 及 dosgolem 的 `internal/machine`／`oracle` 測試通過，最終 RAM／畫布／索引畫面／
  色盤 SHA 與目標074相同。原版兩行墨跡高5／6像素，文字底圖多色有紋理；這使純色抹底
  不符合原版忠實度。研究收據保留在已忽略的 `workplace/reports/`，詳見研究紀錄與規格016。
- 不把主選單中文字級固定套用到卡片，不把 `GAME.TXT` 或 `NAMES.TXT` 的同文草稿任選成
  正式卡片鍵。尚缺背景擷取、游標與安全矩形、中文字級、其餘卡片以及來源檔載入邊，
  因此規格016維持 DRAFT，現有八段中文顯示計數不變。`NAMES.TXT` 複合列分欄決策仍待使用者回答。
- 本輪 Docker 一次性容器均已退出且無殘留；未發現 root-owned 檔案或錯誤掛載形成的 `.md`
  目錄。兩份8 MB本機研究收據由目前 UID/GID 擁有、未進 Git；原版素材亦未被追蹤。
- 探針、檢查器及證據文件提交為 `f407e92`，已推送私有 `origin/main`；本紀錄補丁不更動研究結果。

## 2026-09-23：目標076難度卡片可逆中文畫布原型

- 先以提交 `ead615d` 把[目標076](docs/goals/076-difficulty-card-reversible-prototype.md)
  推送私有 `origin/main`，再開始製作本機可丟棄原型。沒有修改原版遊戲、dosgolem
  或正式 `live_menu.go`，也沒有把原版像素、記憶體快照或字型加入 Git。
- 新增固定收據與譯稿準備器、Ebitengine 畫布預覽與逐像素檢查器；以雙次
  dosgolem 目標075收據確認卡片兩行背景可逆，分別量測 21px／25px 候選中文字級，
  產生本機原文／繁中對照圖。第一次檢查在透明字模處抓到亮色滲出；修正
  RGBA→NRGBA 後，以相同輸入重跑 PASS。稱號／副標安全區分別有2,752／1,860點
  與原文控制圖不同，區外逐像素不變；原文圖與原始畫布最近鄰放大完全一致。
- Ebitengine 原型 `go vet`、既有視窗 `go test ./...` 和逐像素收據通過；證據範圍
  見[規格016](docs/spec/016-difficulty-card-text-draft.md)及 `RESEARCH-LOG.md`。
  本輪完成的是**固定終點的可丟棄視覺候選**，不是正式玩家路徑中文卡片；
  來源檔載入邊、執行期背景／游標回退與其餘卡片仍缺，規格016保持 DRAFT，
  已顯示八段計數不變。
- 對照圖與收據只放在已忽略的 `workplace/reports/goal076-card-*`；
  收尾核對四份本機收據／圖均為目前 UID/GID `1000:1000`，原版素材及字型未被
  Git 追蹤，沒有本輪研究／Ebitengine／字型容器殘留，也未發現 root-owned
  產物或錯誤掛載產生的 `.md` 目錄。原型與證據提交 `5a9ed9e` 已推送私有
  `origin/main`；Issue #6／#7／#26 已追加本輪證據與保持開啟的原因。

## 2026-09-23：目標077閉合第一張難度卡片的原始 TXT 載入邊

- 先以提交 `baa8eb5` 推送[目標077](docs/goals/077-difficulty-card-load-provenance.md)
  至私有 `origin/main`。本輪沒有修改原版資料、dosgolem 上游或正式 `live_menu.go`。
- 在隔離 dosgolem 上以相同九筆正常玩家輸入完成兩次3,200萬步冷啟動，
  `tools/probe_card_load.go` 同時記錄 DOS `AH=3Fh` 讀檔、原版位元組讀寫與終點狀態；
  `tools/check_card_load.py` 證明第一張卡片稱號經 `NAMES.TXT` 載入，副標經
  `LABELS.TXT` 載入，並接上目標075的字形／像素鏈。同文的 `GAME.TXT`
  在稱號寫入後才首次讀取，不能作此固定路徑的稱號來源。
- 兩次新收據位元組一致、無截斷、最終 RAM／畫布／索引畫面／色盤與既有正常路徑
  相同。訂正舊 dosgolem 註解對 `WriteBytes` 監看的錯誤推測：隔離版實作
  確實逐位元組經 `Write8`，本輪實測 `WatchWrites` 有捕捉到 DOS 讀入。
- 草稿 TSV 只調整三筆來源註記，譯文數量仍368筆；可丟棄預覽改以
  `NAMES.TXT:0x00000C0C` 取 `發現者`，重新產出 Ebitengine 原文／中文對照圖。
  逐像素檢查通過，兩欄外沒有變更，21／25px 分欄字級與譯文都未改。
  `go vet`、dosgolem `internal/machine`／`oracle` 測試、368筆草稿來源驗證與
  `tools/worklist.py verify` 通過。正式執行期背景、游標及其餘卡片仍缺，
  規格016維持 DRAFT；八段已顯示中文計數不變，Issue #6／#7／#26 保持開放。
- 反向對照從本機收據移除原版來源讀取事件，即使 `Discoverer` 同文仍在，
  檢查器也拒絕其來源聲明；沒有把字串相同當作載入證據。
- 原版收據及 PNG 只保留在已忽略的 `workplace/reports/`，新收據／圖均為目前
  UID/GID `1000:1000`。Docker 檢查未發現本專案 root-owned 產物、錯誤掛載形成的
  `.md` 目錄或本輪殘留容器；未觸碰其他專案容器。本輪文件、程式與驗證細節見
  `RESEARCH-LOG.md`。
- 程式、譯稿註記與證據文件提交 `5d7abfd`，已推送私有 `origin/main`；
  GitHub Issue #6／#7／#26 已追加目標077結果與保持開放的原因。

## 2026-09-23：目標078第一張難度卡片執行期守門實驗

- 先以提交 `94fb631` 將[目標078](docs/goals/078-difficulty-card-runtime-guard.md)
  推送至私有 `origin/main`。依現有規格016的 DRAFT 邊界，只新增可丟棄
  `tools/probe_card_runtime.go`／`tools/check_card_runtime.py`，沒有修改
  原版檔案、隔離 dosgolem、正式 `live_menu.go` 或 Ebitengine 前端。
- 九筆既有真視窗輸入下，兩次獨立原版重播的執行期報告位元組一致；
  `0E2D:11CF` 真實來源讀取時取當次有紋理底圖，第一個完整輸出幀建立
  兩欄可逆補片，該幀及後續共13幀通過原版索引畫面守門。
  同輸入無觀測控制組與觀測／合成組的 CPU、完整 RAM、原始畫布、
  索引畫面、色盤及虛擬時間一致。
- 滑鼠移入第一張卡片後，索引畫面改變160點，其中7／60點觸及兩欄安全矩形，
  底層畫布不變；通用補片未加座標守門也會拒絕兩欄，保守守門回退原文25幀，
  移出後24幀恢復。游標變體另有同輸入無觀測控制組逐項對拍通過。
- 模擬缺譯／缺字模時合成圖逐像素等於原文，舊幀一點差分觸發
  `frame-mismatch`；使用一次性錯誤 `NAMES.TXT` 指紋連結測例，探針在啟動前
  拒絕未知版本。執行期原文／中文 PNG 經 `tools/verify_card_preview.py`
  逐像素通過，差異只在兩欄安全矩形。`go vet`、dosgolem `overlay`／
  `internal/machine`／`oracle` 測試、獨立收據檢查器及工作清單驗證均通過。
- 研究報告、原版像素 PNG、字型與本機探針執行檔都在已忽略的
  `workplace/reports/`，未追蹤進 Git；抽查為目前 UID/GID `1000:1000`。
  Docker 自檢未發現本專案 root-owned 檔案、錯誤掛載 `.md` 目錄或本輪
  殘留容器；未清理其他專案容器。正式鍵、真正 TSV 缺鍵回退、其餘卡片與
  Ebitengine 正常玩家前端仍未完成，規格016維持 DRAFT，已顯示中文仍八段。
- 探針、檢查器與證據訂正提交 `4264c9d`，已推送私有 `origin/main`；
  GitHub Issue #6／#7／#12／#26 均已追加本輪證據與保持開放的原因。

## 2026-09-23：目標079第一張卡片正式覆蓋與下一階段版式 Issue

- 先以提交 `3dc245d` 將[目標079](docs/goals/079-first-card-formal-overlay.md)
  推送私有 `origin/main`，才開始接線。複核目標075至078的來源、格式化文字、
  有紋理底圖、游標及同狀態收據，建立只限第一張卡片兩行的
  [規格017](docs/spec/017-first-difficulty-card-overlay.md)。規格016對其餘卡片維持 DRAFT。
- `tools/live_menu.go` 加入 `NAMES.TXT` 指紋、兩個真實 TSV 來源鍵、
  `0D21:00C6` 格式化顯示守門、當次畫布補片及逐幀游標回退；
  `tools/bake_card_fonts.py` 從本機合法原版和 Cubic 11 生成21px／25px分欄字模。
  沒有修改原版檔案、隔離 dosgolem 或共用 dosgolem。
- 無頭正常路徑兩行各一次事件、79幀套用且與無觀測英文控制同狀態。
  Ebitengine／Xvfb 真視窗九筆輸入的中文、重播與英文控制同狀態，
  最新難度圖只在五個已核准安全矩形變更，第一張卡片兩欄各2,752／1,860點。
  真實 TSV 缺稱號鍵或重複鍵只令稱號回英文；錯誤來源指紋在啟動前遭拒絕；
  游標入卡片25幀回退，離開後恢復，各自同輸入原版控制均一致。
  受控六組重播和逐像素驗證詳見
  [研究紀錄](RESEARCH-LOG.md)。正式顯示數由八段增為十段，並更新私有既有截圖。
- 使用者指出現有難度頁「選擇難度」標題應更貼近原版排版，中文字級須逐畫面調整。
  已建立私有[Issue #28](https://github.com/wicanr2/colonization_cht/issues/28)
  並登記於工作清單，安排在本目標後製作對照原型，不在本輪擅定最後版式。
- Ebitengine 建置初次因離線容器沒有 Go module cache，按已鎖 `go.sum`
  僅於建置與單元測試容器開放網路；執行／抓圖仍無網路。真視窗第一次
  `xvfb-run` wrapper 停在清理；改成有 trap 的 Xvfb 程序後重跑通過。
  單元測試第一次缺 DISPLAY，於同一容器加 Xvfb 後通過；均為環境問題，
  未把失敗收據當成產品缺陷。`tools/worklist.py verify`、新增 Python 工具語法
  與真視窗／反向條件檢查器均通過。
- 仍未完成其他難度卡片、help 畫面、靜態圖、完整鍵盤／音訊／存讀檔與
  正式發行；Issue #6／#7／#12／#26 保持開放。原始報告、字型、執行檔
  只在已忽略的 `workplace/reports/`；私有截圖沿用既有兩張截圖例外。
  收尾核對研究／字型／Ebitengine 映像下無執行中或停止殘留容器，專案內無
  root-owned 項目或錯誤掛載形成的 `.md` 目錄；本輪收據、截圖與重生的
  `WORKLIST.md` 均為目前 UID/GID `1000:1000`。Git 未追蹤原版輸入或
  `workplace/` 中間物。正式程式、截圖與文件提交 `6a857e9` 已推送私有
  `origin/main`；Issue #6／#7／#12／#26 已追加限定完成與未完成範圍，
  下一階段的標題版式及逐欄字級見新 Issue #28（保持 OPEN）。

## 2026-09-23：目標080難度標題排版原型

- 先將[目標080](docs/goals/080-difficulty-heading-layout-prototype.md)以提交
  `925439a` 推送私有 `origin/main`，再開始本輪取證。命中復古 GUI、
  真視窗試玩、規格閘門與工作清單知識路由；依 grill-me 的視覺決策規則，
  先做可丟棄並列預覽，不把代理偏好直接接進正式前端。
- 以原版同狀態印字前後快照量出兩行共用中心 x=230，四倍墨跡高32／36px。
  新增 `tools/prepare_heading_preview.py`，固定原版來源、字型與索引畫面指紋，
  以可逆背景補片產生目前版、共同置中 A 與保留左起點 B；現有 Ebitengine
  預覽器在有界 Xvfb 畫布繪製原文控制及三個中文候選。英文圖與既有控制圖
  完全相同、目前版標題區與既有中文真視窗圖完全相同，三候選差異均限於
  已驗標題安全矩形。詳見[規格018草案](docs/spec/018-difficulty-heading-layout-draft.md)
  與[研究紀錄](RESEARCH-LOG.md)。
- 所有含原版像素 PNG／JSON 留在 gitignore 的本機 `workplace/reports/`；
  既有私有截圖、正式前端及原版檔案均未改。Issue #28 與工作清單轉為
  `in_progress`，等待使用者選 A、B 或另提方向；選定前不升 READY、
  不聲稱新畫面驗收，也不把十段已顯示中文數增加。
- 新預覽工具語法、`tools/worklist.py verify`、四組 PNG／量測收據一致性及
  `git diff --check` 通過。本輪產物皆為目前 UID/GID `1000:1000`；
  專案內未見 root-owned 項目或誤掛形成的 `.md` 目錄。三個相關映像的
  容器檢查無執行中或已停止殘留；沒有清理其他專案資源。

## 2026-09-23：目標081第二張難度卡片原文輸出鏈

- 前輪目標080有實質進展；Issue #28 的標題 A／B 視覺選擇仍待使用者，
  本輪不碰該正式版式。先以提交 `d3a2b85` 將[目標081](docs/goals/081-second-difficulty-card-output-evidence.md)
  推送私有 `origin/main`，再執行取證。採用復古逆向技能的證據分級與
  規格停止線，並按知識路由重查 dosgolem、文件與工作清單入口。
- `tools/prepare_second_card_inputs.py` 從已驗九筆真視窗輸入生成控制、
  只移入及點擊第二張卡片三組本機受控重播；僅點擊使原版顯示
  `EXPLORER:`／`Easy`。`tools/probe_second_card_output.go` 雙次重播、
  `tools/probe_card_load.go -second` 雙次重播閉合來源檔到畫素；
  第一張卡片的舊載入探針預設結果逐位元組不變。
- `tools/probe_second_card_window.sh` 另以 Xvfb 真 Ebitengine 視窗
  實際滑鼠點擊第二張卡片，記錄12筆輸入及本機截圖；同輸入英文控制
  原版 CPU／RAM／索引畫面／色盤／時間一致，終點與受控原版索引畫面
  相同。`tools/check_second_card_output.py` 驗證兩欄印字前後差分、
  格式化文字、可逆紋理背景和真視窗顯示；完整指紋與地址空間見
  [研究紀錄](RESEARCH-LOG.md)。正式 `tools/live_menu.go`、既有私有
  截圖與原版檔案都沒有修改，中文顯示仍十段。
- 第一個 Go 建置命令在既有研究映像使用登入 shell，PATH 被 shell
  重設而找不到 `go`；改用同一映像的非登入 `sh -c` 後乾淨重跑成功，
  不是專案程式缺陷。第一版輸出探針誤沿用第一張卡片緩衝位址，
  擴大只讀觀測後找到第二張的 `0x2A718`，保留舊收據但不採用
  「零緩衝讀取」結論。
- 第二張卡片兩筆 TSV 註記已訂正為「原文輸出已證實、中文仍待驗」。
  規格016保持 DRAFT，尚缺逐欄中文字模、游標與缺譯回退、正式中文
  真視窗驗收；其餘卡片、help 與完整遊玩仍未完成。所有原始收據、
  真視窗 PNG、執行檔與原版位元組留在 gitignore 的
  `workplace/reports/goal081-second-card/`，未加入 Git。
- 提交前在既有容器映像重生並驗證 `WORKLIST.md`、Python／Shell／Go
  語法與格式；368筆 TSV 來源指紋及控制符號驗證通過。完整畫面檢查
  首次因將原版掛載根誤當 `COLONIZE` 子目錄而正確 SKIP（77），
  以實際唯讀 `/game/SMColoni/COLONIZE` 重跑通過，未更換工具或資料。
  私有 Issue #28 已核對含使用者指定的原版風格重排與逐欄字級要求，
  保持下一階段開放，不另開重複項。
- 證據、程式與文件提交為 `ec77716` 並推送私有 `origin/main`；
  已向 Issue #6、#7、#27 回報「原文已證實、中文仍待驗」，並在既有
  Issue #28 再次確認下一階段的版式與逐欄字級要求。提交清單不含
  原版檔案、畫面或本機收據。驗證收據為目前 UID/GID `1000:1000`；
  專案內無 root-owned 項目或誤掛成 `.md` 目錄，三個相關映像均無
  執行中或已停止的殘留容器。

## 2026-09-23：目標082第二張難度卡片限定正式覆蓋

- 先提交並推送[目標082](docs/goals/082-second-difficulty-card-overlay.md)；
  依復古遊戲逆向技能及知識路由先建立可丟棄預覽、原版與執行期反例，
  再將[規格019](docs/spec/019-second-difficulty-card-overlay.md)升至限定 READY。
  Issue #28 已明列使用者要求的原版風格重排與逐欄字級，保持下一階段開放；
  本輪不改難度標題正式版式，也不更新既有含原版像素的私有截圖。
- `tools/prepare_second_card_preview.py` 從固定目標081原版快照與
  真實 TSV 量測稱號21px／副標25px，Ebitengine 原文／中文對照在兩個
  安全區外零差異。`tools/probe_card_runtime.go -second` 雙次重播位元組相同，
  已證實當次背景、格式化顯示鍵、游標與滑鼠按鍵回退；
  `tools/check_second_card_runtime.py` 獨立檢查 PASS。
- `tools/live_menu.go` 已將第二張卡片的來源、格式化緩衝、欄位安全區及
  游標守門接入正式輸出層；`tools/bake_card_fonts.py` 逐欄烘製本機字模。
  真 Ebitengine 視窗由冷啟動實際點選第二張卡片，與同輸入英文控制的
  CPU／RAM／原版畫面／色盤／時間一致；新中文只在兩個核准區。
  真 TSV 各欄缺鍵／重複鍵及游標進出八組反例由
  `tools/verify_goal082_replays.py` 判為 PASS。第一張卡片的 PNG、索引、
  色盤及完整 RAM 與前輪逐位元組相同；錯版本暫存反例在啟動前拒絕。
- 初次建置因使用了不存在的 `Rectangle.Contains` 未通過編譯，改用
  `Point.In` 後通過；Ebitengine 建置初次未掛固定 Go 模組快取而嘗試
  網路，按既有視窗規格掛載唯讀版本快取後於相同映像重跑成功。
  錯版本測試初次在研究映像缺圖形函式庫、第二次未設 DISPLAY；
  改在既有 Ebitengine 映像的受控 Xvfb 中執行才取得有效 PASS。
  這些是建置／驗證環境與測試碼修正，不是原版遊戲缺陷。
- 已顯示中文限於十二段；第三至第五張卡片、help、標題新版式及完整
  玩家版仍未驗。固定雜湊、工具版本、位址空間與證據界線見
  [研究紀錄](RESEARCH-LOG.md)。原版畫面與字型都留在 gitignore 的
  `workplace/`，不納入 Git 或公開發行。
- 收尾以固定研究映像重生並核對 `WORKLIST.md`、368筆主譯稿原文指紋與
  控制碼、Python語法、Shell語法及 Go 格式；`git diff --check` 通過。
  本輪產物和工作目錄均為目前 UID/GID `1000:1000`；專案內未見
  root-owned 項目或誤掛形成的 `.md` 目錄。相關一次性 Docker 容器
  無執行中或已停止殘留，未清理其他專案資源。

## 2026-09-23：目標083離開難度頁與國家標題草案

- 已先提交並推送[目標083](docs/goals/083-post-difficulty-player-path.md)。
  使用目標082已驗輸入建立控制、只移入、點擊三組重播；只有完整滑鼠
  按下／放開會離開難度頁。另用 Xvfb 的真 Ebitengine 視窗由冷啟動
  輸入17筆實際鍵鼠事件，抵達 `NATIONS.PIK`；同輸入英文控制的
  原版 CPU／RAM／索引畫面／色盤／時間一致。
- 新探針 `tools/probe_goal083_label_load.go` 與
  `tools/probe_goal083_nation_text.go` 在隔離 dosgolem 中只讀觀測，
  關閉 `LABELS.TXT:0x8D3`／`0x8DB` 到 DOS RAM、格式化輸出和畫素的
  資料鏈；雙次收據與獨立驗證均通過。工具版本、檔案雜湊、地址基準
  與有限結論集中於[研究紀錄](RESEARCH-LOG.md)。
- 以固定 Cubic 11 字型量得國家頁原文兩行各36px、中文候選各35px
  墨跡，建立38px逐欄 Ebitengine 可丟棄預覽；游標移入／移開與 F1
  限定反例已記錄。[規格020](docs/spec/020-nation-heading-overlay.md)
  維持 DRAFT：執行期守門、正式前端與 help 仍缺，十二段正式中文數
  不變。未更新含原版像素的私有截圖。
- 遠端 [Issue #28](https://github.com/wicanr2/colonization_cht/issues/28)
  已核對為開放，全文包含使用者指定截圖、原版風格重排和依欄位
  調字級的下一階段驗收，未建立重複 Issue；其 A／B 版式仍待使用者
  依本機對照圖決定，本輪未猜選。
- 固定原版與本機收據在唯讀容器重跑 `tools/check_goal083_nation_evidence.py`
  為 PASS；新 Python 語法、Bash 語法、Go 格式及兩支 Go 探針建置通過。
  起初誤用 POSIX `sh -n` 檢查 Bash 專用腳本，出現假語法錯誤；改用
  `bash -n` 並在同一研究映像重跑通過，不是產品缺陷。
  `tools/worklist.py render` 與現存 `WORKLIST.md` 一致；工作樹無
  root-owned 檔案或誤掛的 `.md` 目錄。本輪 `docker run --rm` 容器
  均已退出，沒有殘留的專案容器；未觸碰其他專案的容器。

## 2026-09-23：目標084國家頁左側兩行限定正式覆蓋

- 先提交並推送目標084；依知識路由、逆向技能與規格閘門，雙次 dosgolem
  重播建立兩欄當次印字前木紋、原文格式化輸出與逐欄可逆補片。修正
  最初會讓第二行游標連帶回退第一行的整塊守門後，獨立驗證才將
  [規格020](docs/spec/020-nation-heading-overlay.md)升為限定 READY，
  再修改正式 Ebitengine 顯示層。
- 依固定原版字高及安全矩形，兩欄「選擇／歐洲國家」各用38px Cubic 11；
  新增的字模與舊十二欄一起重烘為14欄完整包。首個僅含卡片與國家
  六欄的包會使舊選單／難度文字回退英文，已棄用並改用完整包，
  不作正式驗收依據。
- 真視窗16筆實際輸入與同輸入英文控制原版 CPU、完整 RAM、索引畫面、
  色盤、虛擬時間相同。各欄缺鍵／重複鍵各自回退、游標兩種位置逐欄
  回退與移開恢復、滑鼠按住及切場清除、錯版 `LABELS.TXT` 輸出前
  拒絕均通過。新中文只改兩個安全矩形2,611／5,502個像素。
  舊版第一、二張難度卡片在同一輸入下終圖、索引、色盤、完整狀態
  逐位元組相同；另核對舊主選單／難度頁15個檢查點逐位元組不變。
  首次誤將不同時序輸入的第一張卡片收據比較，已改為同輸入重播；
  六組目錄反例的第一次批次逾時，只重跑未完成的最後一組並全數驗證。
- 真實 TSV 最後只把兩筆 `notes` 從待驗改為限定 CONFORMED，未改
  原文、譯文、鍵或狀態。從原始重複鍵反例還原受測 TSV，逐列排除
  `notes` 比對，並以現行 TSV 重烘14欄、同輸入重播；終圖、索引、
  色盤與前次真視窗逐位元組相同。`tools/verify_goal084_replays.py`
  收據 PASS、SHA-256 為
  `84da4515020fbccddb2c927deeb99d68261ff1da17d74be62dd20e677d30e678`。
- 已顯示中文限定增至十四段，不含其他國家卡片、help 或完整玩家路徑。
  使用者再次提供難度頁截圖及原版風格／逐欄字級要求；遠端
  [Issue #28](https://github.com/wicanr2/colonization_cht/issues/28)與
  `docs/worklist.json` 已逐項涵蓋且仍開放，留待下一階段，不另開重複項
  或擅自選定 A／B 版式。正式成果截圖未更換，原版像素與字型僅留本機。
- 收尾以既有容器驗證368筆主譯稿來源、工作清單渲染／狀態、Python
  與 Bash 語法、Go 格式及適配器指紋；`git diff --check` 通過。正式
  收據與新字模目錄均由目前 UID/GID `1000:1000` 擁有；已刪除本輪
  兩個生成的 Python 快取檔。工作樹沒有 root-owned 項目或誤掛成
  `.md` 的目錄；所有本輪 `docker run --rm` 容器已退出，未清理
  其他專案資源。
- 正式程式、譯稿備註、規格與現況以提交 `9d10a03` 推送私有
  `origin/main`；相關 Issue #7、#12、#14、#26、#27 已各追加
  限定驗收與未完成範圍。遠端 Issue #28 仍為 OPEN，內容已涵蓋
  使用者再次指定的截圖、原版風格重排及逐欄字級，未另建重複項。

## 2026-09-23：目標085來源調查與目標086難度標題 A 版

- 目標085先用隔離 dosgolem 雙次冷啟動觀測第一張國家旗卡紅字，
  無觀測控制組同狀態。上、下兩處均有原版讀字與畫布寫入，
  由暫定未知訂正為「當次動態印字」；原始檔案候選到 RAM 的載入
  邊仍缺，沒有增加正式中文段數。詳細收據與地址基準見研究紀錄，
  Issue #7／#8 仍保持其他範圍開放。
- 使用者看過四格對照並確認 A：標題「選擇」34px、「難度」38px，
  共用 x=230 中心，只改兩欄。先推送目標086與規格018限定 READY，
  才烘製完整十四欄字模並修改正式前端；舊十二欄字模逐位元組未改。
  真 Ebitengine 視窗第一張卡與第二張卡／完成區路徑、同輸入舊版
  與英文控制、十五檢查點、逐欄缺鍵／重複鍵／缺字模／錯字級、
  游標遮擋及原版錯版拒絕皆驗證 PASS。獨立收據與截圖指紋見
  [規格018](docs/spec/018-difficulty-heading-layout-draft.md)。驗後才
  取代原私有難度截圖；不碰卡片、提示、原版資料或滑鼠命中區。
- 錯版腳本第一次因缺 `DISPLAY` 只得到 GLFW 啟動錯誤，改在同
  一既有映像以明確 Xvfb 重跑才確認版本閘門 PASS；直接把二進位
  程式交給 `xvfb-run` 的兩個輔助容器，其遊戲子程序退出後仍卡在
  Xvfb 收尾，已精確辨認並停止。後續改用容器內 `trap` 管理 Xvfb，
  同一舊版輸入及錯版測試成功。45M反例第一次誤沿用100M終點的
  重播檔而被參數守門拒絕；從原8筆輸入產生保留全部事件、只截
  終點至45M的副本後，同一批矩陣全數通過。這些是驗證環境與
  收據參數問題，不是畫面缺陷。
- 另以相同16筆玩家輸入回到國家頁，A 版與舊版最終 PNG、原版
  索引、色盤、完整 RAM 逐位元組相同；第二張卡片在40M同輸入的
  差異僅位於「選擇」標題安全矩形，卡片與提示保持原狀。更新後的
  獨立收據 SHA-256
  `83c6668d942034193bec084fcf53fa52ec0a2775ae9c5296a6f663bd7ffb9a2f`。
  譯稿368筆來源與控制碼驗證、工作清單產生／驗證、Python／Bash
  語法、Go 格式及 `git diff --check` 均通過。兩個本輪生成的
  Python 快取檔已定點清理；所有本輪 `docker run --rm` 容器已退出，
  沒有觸碰其他專案容器。

## 2026-09-23：目標087國家旗卡檔案來源鏈

- 先建立並推送[目標087](docs/goals/087-nation-card-source-load-edge.md)，
  再於獨立 `workplace/dosgolem` 上執行原版探針；未修改正式前端、
  十四段中文顯示、原版檔案或私有截圖。
- DOS 載入探針確認 `NAMES.TXT:0x8EA` 與 `LABELS.TXT:0x8F2`
  各自進入原版讀取緩衝；RAM 監看先找到共用解析緩衝，隨後補監看
  範圍以覆蓋就地整理搬移起點。較寬監看版本曾截斷事件，未當作
  正式證據；縮窄後兩次冷啟動均未截斷且收據逐位元組一致。
- 新增 `tools/check_goal087_nation_flow.py`，獨立核對原始位元組、
  DOS `AH=3Fh` 傳輸、整理／解析／常駐／格式化的逐字原版指令事件、
  目標085畫布寫入、同文副本負例及無觀測控制組同狀態，結果 PASS。
  來源鏈及限制分別登錄於[規格021](docs/spec/021-nation-card-red-text-draft.md)
  與研究紀錄；目標085／087只以 DRAFT 退出，兩處英文未上線中文。
- `docs/worklist.json` 已訂正 Issue #7／#8／#12 的證據狀態，
  仍保留其他動態、靜態及正式覆蓋工作；下一輪先做背景、逐欄
  字級、安全區、游標／切場反例與可丟棄版面圖，再送 READY 審查。
- 獨立驗證器與工作清單驗證 PASS，Go 格式、Python 語法及
  `git diff --check` 通過；本輪檔案與私有收據均由 UID/GID
  `1000:1000` 擁有，沒有 root-owned 產物或誤建 `.md` 目錄。
  一次性 Docker 容器均已退出，未清理其他專案資源。成果先以
  `85f9c2f` 推送目標、再以 `e4309fa` 推送證據與 DRAFT；
  遠端 Issue #7／#8／#12 各已留言限定成果及未完成範圍，均保持 OPEN。

## 2026-09-23：目標088第一張國家旗卡可逆視覺原型

- 先建立並推送[目標088](docs/goals/088-first-nation-card-reversible-preview.md)
  （`7ebf545`），沿用隔離 dosgolem 與既有研究、字型、Ebitengine
  映像；原版、Cubic 11 及含原版像素的收據均只在本機讀取／輸出。
- 發現目標085較早的42.4M／42.6M／42.8M畫布快照都仍是底圖未完成
  狀態，不能拿來做可逆補片。新增精確印字前後探針，雙次冷啟動
  收據逐位元組相同，無監看控制組 CPU／RAM／索引／色盤／時間及
  開檔序列同狀態；上、下行多色底圖與最終123／156像素原文差分
  均已核對。細節與指紋見[規格021](docs/spec/021-nation-card-red-text-draft.md)
  及研究紀錄。
- `NAMES.TXT` 的 `England` 屬於帶數值的複合行，不能塞進既有
  「完整原始行」譯稿契約；新增限定兩筆、非執行期鍵的
  [片段草稿](text/nation-card-fragments.zh-Hant.tsv)及驗證器，
  核對原始片段、上下文、版本與字形。暫試「英格蘭：／移民」。
- 重用 `tools/card_preview.go` 的 Ebitengine 四倍畫布原型，僅加
  可選紅色索引12與向右一原始像素的黑影；21／25px 分欄字模
  不沿用其他畫面的全域值。獨立預覽驗證 PASS：安全區外零差異，
  透明字模下逐像素恢復紋理，兩欄均有實際中文。舊國家頁預覽
  以新繪製器重跑，輸出 SHA-256 與舊圖相同。原型已目視檢查，
  另做25／29px、仍在安全區內的較易讀 B 版，同樣逐像素 PASS；
  但未取得使用者在 A／B 間定版，不進正式前端或私有截圖目錄。
- 首次 Ebitengine 建置因既有 Go workspace 指向容器內 `/dosgolem`
  而未掛載，屬工具環境缺件；補上已驗存在的隔離副本後，同一
  映像成功建置、抓圖。嚴格色號驗證首次把「半透明紅字覆在
  不透明黑影」誤判為應為純黑，改為僅在紅字透明時檢查純黑，
  同一組輸出重跑 PASS；不是產品畫面修補。
- 規格021與現況仍標 DRAFT／視覺待確認；下一輪須確認版式，
  再補執行期游標、按鍵、切場、其他旗卡與缺譯回退等 READY 閘門。

## 2026-09-24：續完目標088的驗證與交接

- 上輪對已完成的難度標題 A 版只做了現況核對，未推進旗卡；本輪接續
  已先推送的目標088，沒有重開或更動 Issue #28。依知識路由及復古
  遊戲逆向／共同決策技能，原型維持 DRAFT，A／B 樣式不代使用者定版。
- 本機逐一目視 A／B Ebitengine 圖；用現行兩筆片段草稿與固定 Cubic 11
  重跑原始位元組、語境及字形驗證，並重跑唯一工作清單及兩版的
  1280×800 逐像素安全區／可逆背景驗證，均 PASS。來源圖、預覽資料與
  收據只留 `workplace/`，沒有更新正式截圖或十四段正式顯示。
- 首次複驗把字型誤寫為 `Cubic_11_1.013_R.ttf`，驗證器如預期回報
  `SKIP`；查核實際本機檔名為 `Cubic_11.ttf`，在同一既有映像重跑
  PASS。此為驗證參數錯誤，非字型缺失或產品退化。
- `gofmt -d` 無差異；程式、字模、A／B 預覽資料與 PNG 的 SHA-256
  與[規格021](docs/spec/021-nation-card-red-text-draft.md)記載一致。
  repo 已再核對為 PRIVATE，Issue #7／#12／#26／#27 保持 OPEN；
  可丟棄原型與 DRAFT 證據以 `eed527c` 推送 `origin/main`，四個
  Issue 均已附限定成果及未完成範圍的留言，未關閉。提交清單沒有
  原版 EXE、素材、字型或工作區圖像。工作樹無 root-owned 項目或
  誤建 `.md` 目錄，`docker run --rm` 均已退出，沒有其他專案資源清理。

## 2026-09-24：目標089第一張國家旗卡執行期守門蒐證

- 先以提交 `7e0ad81` 推送[目標089](docs/goals/089-first-nation-card-runtime-guard-evidence.md)，
  再重用合法原版、隔離 dosgolem 與16筆真視窗輸入。新唯讀探針
  從43M步第一張旗卡分出游標進出、下欄左鍵與相鄰右上旗卡左鍵
  三條正常輸入路徑，各做雙次獨立冷啟動和無逐幀監看控制。
- 游標上欄／下欄各只遮該欄24個原版索引像素，離開後兩欄恢復；
  底層紅字畫布保持不變。下欄左鍵於本座標與時間窗未重繪；
  點相鄰旗卡時第一幀仍舊畫布，下一幀兩個舊安全區均改變。
  控制組 CPU／RAM／索引／色盤／時間／開檔與畫布快照同狀態，
  獨立九份報告與逐幀驗證 PASS；詳細位址、數量與 SHA 見
  [規格021](docs/spec/021-nation-card-red-text-draft.md)及研究紀錄。
- 初次把 dosgolem 按鍵1誤當左鍵；既有正常輸入證明左鍵是0，
  已明確分離右鍵探索與左鍵正式收據。獨立驗證器初次把相鄰旗卡
  重繪誤假設為按下後第一幀，依實測下一幀變化訂正後重跑 PASS。
  兩者皆保留更正脈絡，不把環境／測試假設寫成遊戲缺陷。
- 目前只完成原版守門事實，正式 Ebitengine 未改、十四段中文數
  未增加；使用者的 A／B 字級選擇仍待確認。工具、規格與證據
  已以 `ce180c8` 推送私有 `origin/main`；Issue #12／#26 都已留言
  限定結論並保持 OPEN。工作樹未追蹤原版檔案、字型、索引畫面、
  含原版像素的收據或探針二進位；Go 格式、Python 語法、
  工作清單驗證與 `git diff --check` 通過。輸出由目前 UID/GID
  `1000:1000` 擁有，無 root-owned 項目、誤建 `.md` 目錄或
  殘留 Docker 容器；未清理其他專案資源。

## 2026-09-24：難度標題決定複核與目標090相鄰旗卡來源

- 使用者再次確認難度標題 A：「選擇」34px、「難度」38px，
  x=230共同置中，只改兩欄。核對目前正式程式仍由
  `tools/live_menu.go` 逐欄採此字級、位置；
  [目標086](docs/goals/086-difficulty-heading-centered-layout.md)與
  [規格018](docs/spec/018-difficulty-heading-layout-draft.md)早已完成
  同輸入英文控制、十五檢查點、卡片／提示不變及正式驗收。
  現行私有 `docs/screenshots/difficulty-zh.png` SHA-256
  `86b2c08465ed67fc57202e7490a7ac274185c78bf464e2a0e773b120bb196e07`
  等於驗後更新版本；原 PASS 收據 SHA-256
  `83c6668d942034193bec084fcf53fa52ec0a2775ae9c5296a6f663bd7ffb9a2f`。
  遠端 Issue #28 已於2026-09-23關閉，本輪不重複修改、重抓圖或
  重開此項。
- 接續先以 `287d89c` 推送的[目標090](docs/goals/090-neighbor-nation-card-source.md)，
  以合法 DOS 原版、隔離 dosgolem、原16筆真視窗輸入，在43M步
  移到相鄰右上旗卡 `(255,50)`、44M步左鍵按下，分別觀測原版
  TXT 載入／RAM 與畫布。新畫布字在右側；左側差分是舊字清除，
  因此沒有沿用第一張旗卡的安全矩形猜鍵或猜座標。
- `NAMES.TXT:0x906` 的 `France` 及 `LABELS.TXT:0x8FF` 的
  `Cooperation` 逐字經 DOS 讀取、RAM 整理／解析／常駐、
  格式化及原版畫布寫入；雙次完整來源流與雙次畫布重播各自
  位元組相同，無監看控制的 CPU／RAM／索引／色盤／時間、
  開檔與畫布取樣相同。獨立驗證器 PASS；詳細地址與本機
  收據 SHA 見[規格022](docs/spec/022-neighbor-nation-card-red-text-draft.md)
  與研究紀錄。
- 初次 Docker 啟動探針將原版目錄掛到 `SMColoni/` 而非其下
  `COLONIZE/`，原版檔案檢查如預期失敗；改正掛載層級後同版
  重跑成功。第一次用登入 shell 讓映像的 Go PATH 被覆蓋，
  改用既有映像原始環境重新建置，沒有新建重複映像。
  第一次獨立來源驗證又因 `WatchWrites` 不回報同值寫入而失敗；
  查通用 dosgolem 契約後，於解析緩衝狹窄位址使用
  `WatchWrite` 記錄每一次寫入，雙次重跑後 PASS。這些均為
  掛載／觀測判準修正，沒有改原版或正式畫面。
- [旗卡片段 TSV](text/nation-card-fragments.zh-Hant.tsv) 新增
  「法國／合作」兩筆來源固定 `draft`，四筆原始片段、行界、
  Cubic 11 字型與字形覆蓋驗證 PASS。規格022仍 DRAFT；
  右側印字前背景、安全矩形、字級與正式逐欄回退未做；第一張
  旗卡 A／B 尚待使用者確認。十四段正式中文數及已驗截圖不變，
  原始 RAM／畫布、探針二進位與字型只留本機 `workplace/`。
- `tools/worklist.py verify`、產生內容與 `WORKLIST.md` 一致、
  Python AST、Go 格式及 `git diff --check` 通過；私有 repo
  仍為 PRIVATE，提交清單只含程式、譯文與文件。成果提交
  `b21fca9` 已推送 `origin/main`；遠端
  [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、
  [#12](https://github.com/wicanr2/colonization_cht/issues/12)、
  [#27](https://github.com/wicanr2/colonization_cht/issues/27)
  各已回填限定成果與未完成範圍並保持 OPEN。
  本輪輸出與程式為 UID/GID `1000:1000`，工作樹沒有
  root-owned 項目或誤建 `.md` 目錄；全部本輪
  `docker run --rm` 容器已退出，未清理其他專案資源。

## 2026-09-24：目標091右側旗卡兩欄可逆視覺原型

- 先將[目標091](docs/goals/091-neighbor-nation-card-reversible-preview.md)
  與工作入口以 `2daa222` 推送至核對為 PRIVATE 的儲存庫，
  然後才做本輪探針。沿用合法 DOS 原版、隔離 dosgolem 與原16筆
  真視窗輸入；原始素材、畫布、字型與 PNG 只在本機。
- 目標090探針增設精確印前／印後擷取，雙次冷啟動的收據逐位元組
  相同；無監看控制的 CPU、完整 RAM、索引、色盤、時間、開檔
  及各精確畫布一致。獨立底圖驗證 PASS：上／下欄可見差分
  100／136點，各安全區印前底圖45／80種色號，原版使用
  藍色9與黑影0。前一輪文件中的「紅字」只是一個色號尚未
  查表時的暫稱，已在規格與研究紀錄訂正。
- 按各欄原版四倍墨跡20／24px測試兩個可丟棄字級：
  21／25px接近原文，25／29px較易讀；都沿用當次藍色
  色盤與黑影。Ebitengine 原文控制及兩種中文預覽的
  1280×800畫面由獨立驗證器逐像素 PASS：安全區外零差異、
  透明字模下恢復原底圖且兩欄各有中文變化。驗證數值與
  收據 SHA 見[規格022](docs/spec/022-neighbor-nation-card-red-text-draft.md)
  及研究紀錄。右側視覺仍未由使用者定案，規格022保持 DRAFT，
  正式中文顯示維持十四段，已驗成果截圖沒有更新。
- 初次 Ebitengine 映像缺少離線 Go 模組；檢查後改用既有、
  已含鎖版 v2.9.9 模組的映像。其 `xvfb-run` 缺少 `xauth`，
  改由同一有界容器的 trap 擁有 Xvfb 背景程序後重跑成功，
  沒有建新映像或開放網路。兩個候選及原文控制均為
  UID/GID `1000:1000`；意外產生的三個精確 Python 快取
  已確認後刪除。工作根沒有 root-owned 項目或誤建 `.md`
  目錄；研究、字型及 Ebitengine 映像的執行／停止容器均無殘留。
- 更新 `docs/worklist.json` 的 Issue #7／#12／#26／#27
  現況並重生 `WORKLIST.md`；`tools/worklist.py verify`、
  Python AST、Go 格式與逐像素驗證已通過。下一步仍是旗卡
  執行期守門、正式回退與 READY 審查；原型不授權直接接前端。
- 成果提交 `9683743` 已推送私有 `origin/main`；
  [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、
  [#12](https://github.com/wicanr2/colonization_cht/issues/12)、
  [#26](https://github.com/wicanr2/colonization_cht/issues/26)與
  [#27](https://github.com/wicanr2/colonization_cht/issues/27)
  已回填限定成果與仍未完成的驗收，均維持 OPEN。

## 2026-09-24：目標092右卡執行期守門與姓名畫面

- 先以 `ff9eee7` 推送[目標092](docs/goals/092-neighbor-card-runtime-and-nation-route.md)
  到確認為 PRIVATE 的 repo，才開始探針。沿用固定合法 DOS
  原版、隔離 dosgolem 與16筆真視窗玩家輸入；`upstream`
  推送位址仍為 `DISABLED`。
- 探針從46M步右卡基準分四條正常滑鼠路徑：游標上下欄／移開、
  再點右卡、點回左卡、點選國頁左下可見完成提示。四條各做
  兩次獨立冷啟動及一份無逐幀觀測控制；逐份原版 CPU、完整
  RAM、索引、底層畫布、色盤、時間、開檔與18／55個輸出幀
  由獨立驗證器 PASS。右卡游標各只遮一欄24／25點；
  再點右卡有短暫底層重繪，終態仍是右卡；點左卡使右卡
  上／下欄失效且畫布回到英格蘭旗卡。
- 右卡選定後點 `(65,184)` 的可見「Click here when finished」
  提示，原版開 `WOODPANL.PIK`／`GAME.TXT`，49M～55M步
  穩定到新姓名畫面。以 Ebitengine 重生原版選國頁與新畫面
  控制圖，獨立像素重建器逐點 PASS；畫面可見「Please Enter
  Your Name.」及「Jacques Cartier_」。這是新正常玩家路徑
  證據，不是新文字來源或姓名輸入規則證據。
- 首次獨立驗證器把進入姓名畫面時的中間載入幀誤判為最終畫布；
  依逐幀收據訂正相位後通過。探針起初未把新開的
  `WOODPANL.PIK` 列入版本指紋；補上19,257-byte原版檔案
  SHA-256 後**全部十二份**原版報告與兩張 Ebitengine 控制圖
  重新產生並再驗 PASS，未沿用舊收據冒稱通過。
- 更新[規格022](docs/spec/022-neighbor-nation-card-red-text-draft.md)
  的原版守門與[規格023](docs/spec/023-player-name-screen-draft.md)
  的新文字 DRAFT 邊界，並修正 `CONTEXT.md`、README 穩定
  現況與 `docs/worklist.json`；`WORKLIST.md` 由工具重生。
  十四段正式顯示、旗卡未決字級及已驗成果截圖均未改。
  原版畫布、RAM 指紋、輸入快照、字型與 PNG 僅留已忽略的
  `workplace/`，不入 Git。Python AST、Go 格式與工作清單
  驗證通過；輸出 UID/GID `1000:1000`，工作根沒有
  root-owned 項目、誤建 `.md` 目錄或殘留 Docker 容器。
- 新姓名畫面的來源、輸入與正式中文覆蓋尚缺，依使用者要求
  建立[Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)，
  並將 `player-name-screen` 登入 `docs/worklist.json`，
  由工具重生 `WORKLIST.md`；新項維持 `planned`／人工驗證。
- 成果提交 `e60fc98` 及 Issue 索引提交 `337db15` 均已推送
  私有 `origin/main`；遠端 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、
  [#12](https://github.com/wicanr2/colonization_cht/issues/12)、
  [#26](https://github.com/wicanr2/colonization_cht/issues/26)、
  [#27](https://github.com/wicanr2/colonization_cht/issues/27)與
  [#29](https://github.com/wicanr2/colonization_cht/issues/29)
  已回填本輪結果及未完成範圍，均維持 OPEN。

## 2026-09-24：目標093姓名畫面來源與鍵盤輸入

- 先以 `4556be8` 推送[目標093](docs/goals/093-player-name-source-and-input.md)
  至 PRIVATE 儲存庫，再於隔離 dosgolem 對固定原版執行雙次冷啟動
  及無觀測控制。原始 `GAME.TXT:0xA7A`（可見提示起於 `0xA7C`）
  與 `NAMES.TXT:0xB4B`（預設姓名片段）分別追至 DOS 讀取、
  RAM 與原版動態畫布寫入；位址空間、時間與雜湊記於
  [規格023](docs/spec/023-player-name-screen-draft.md)及研究紀錄。
- 正常玩家姓名欄的無輸入、輸入 `x`、退格、Enter、輸入後 Enter
  各做兩次獨立冷啟動及無觀測控制。`x` 會取代預設姓名，退格
  只留游標；Enter 進入可見 `FRANCE` 的國家介紹長文。兩種
  Enter 的畫面相同但完整 RAM 不同，未推定存檔語意。五張
  Ebitengine 四倍原文控制圖與 dosgolem 原版索引／色盤逐像素
  PASS；獨立驗證收據 SHA-256
  `ace71383918c6e92efae9bf15d69d6755dbb54b69dc496d11d8127233d32c646`。
- 初版探針在 DOS 讀取後太晚比較已重用的暫存 RAM；改為讀取
  當下記錄來源區，雙次及控制全數重跑。首次產生預覽時檔名
  與控制報告衝突；修正命名並重新產生五條控制報告後才驗收。
  這些是探針／驗證流程修正，不視為原版程式缺陷。
- 主譯稿已有 `^^請輸入您的姓名。`，不另增重複鍵；可編輯的
  預設姓名保留原版資料。提示底圖、安全矩形、中文字級與
  正式回退尚缺，規格023仍 DRAFT、正式中文顯示仍十四段。
  首次國家介紹長文另登[Issue #30](https://github.com/wicanr2/colonization_cht/issues/30)。
  原版 RAM、索引、色盤、PNG 均留在已忽略 `workplace/`。
- 本次也核對先前使用者選定的難度標題 A 版：程式設定為
  「選擇」34px／「難度」38px共同置中；既有
  [規格018](docs/spec/018-difficulty-heading-layout-draft.md)
  記錄同狀態驗收僅改兩個標題安全矩形，卡片與完成提示不變，
  私有截圖於驗收後才更新。這次沒有再次修改該版面或截圖。
- 交付前重核截圖 SHA-256
  `86b2c08465ed67fc57202e7490a7ac274185c78bf464e2a0e773b120bb196e07`
  與規格018一致；姓名畫面獨立驗證器重跑 PASS，工作清單、
  368筆譯稿、Go格式及 Python 語法檢查通過。研究映像沒有
  Pillow，影像驗證改用既有 `rich2-py:latest` 映像完成；
  未變更映像或放寬網路。專案沒有 root-owned 殘留或誤建
  `.md` 目錄，輸出為 UID/GID `1000:1000`；本專案沒有
  執行中／停止的遺留容器，其他專案容器保持原狀。
- 成果提交 `2391d4b` 已推送私有 `origin/main`；遠端
  [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、
  [#26](https://github.com/wicanr2/colonization_cht/issues/26)、
  [#27](https://github.com/wicanr2/colonization_cht/issues/27)、
  [#29](https://github.com/wicanr2/colonization_cht/issues/29)及
  [#30](https://github.com/wicanr2/colonization_cht/issues/30)
  已回填限定成果與未完成項，仍為 OPEN；既有難度標題
  [Issue #28](https://github.com/wicanr2/colonization_cht/issues/28)
  維持 CLOSED，不重開已驗收工作。

## 2026-09-24：目標094姓名提示可逆底圖與中文字級

- 先以 `c18b1e6` 推送[目標094](docs/goals/094-player-name-prompt-layout.md)
  至已核對為 PRIVATE 的 repo。固定原版與隔離 dosgolem
  雜湊不變；從既有正常玩家16筆輸入冷啟動，取得提示
  48,696,982步印前與48,721,827步印後畫布，雙次獨立
  報告及無觀測控制逐項同狀態。
- 原版 `0D21:00C6` 讀回可見提示，`0D21:012C` 僅改415點、
  原版墨跡 `(104,88)–(215,97)`。安全矩形
  `(100,85)–(219,98)` 的印前底圖有10種色號；y=98的
  姓名欄上緣在提示後另重繪119點，不能納入提示遮罩。
  Cubic 11 38px的可見譯文字模為328×35px，位置
  `(474,352)`；主 TSV 的 `^^` 控制碼不作字形。
- 沿用 Ebitengine v2.9.9 在有界 Docker／Xvfb 製作無輸入、
  `x`、退格三組英文控制及中文單欄可丟棄圖。獨立驗證器
  證實三張英文圖逐點等於 dosgolem 原版索引／色盤；
  每張中文圖相對英文僅在提示安全區改9,520畫素，姓名欄
  不變。PASS 收據 SHA-256
  `b682921086f1c92f016ae4095a3d6684af095b40020ce43999c01507e9b31ed1`。
  既有雙欄國家旗卡預覽在改成支援一／兩欄後重生，PNG
  與舊檔逐位元組相同。
- 首次 Go 建置因容器非 root 預設 `/.cache` 不可寫而停止，
  改用專案既有 `workplace/gocache`；Ebitengine 建置另因
  既有 `go.work` 指向未掛載 `/dosgolem` 而停止，對只依賴
  Ebitengine 的可丟棄預覽明確設 `GOWORK=off` 後成功。
  沒有修改其他專案、重建映像或開放網路。
- 修正主譯稿該筆過時的「正常路徑輸出事件未驗證」註記，
  筆數仍368；重生唯一 `WORKLIST.md`。規格023仍 DRAFT：
  正式提示事件守門、視窗前端字元／退格、游標／離頁與
  缺鍵／缺字／錯版回退未驗，十四段正式中文顯示不變。
  原版像素、畫布、預覽 PNG 及字型不入 Git。
- 交付前重跑主譯稿368筆來源／控制碼驗證、工作清單驗證、
  Go格式、Python語法及字型／原型驗證均通過。兩個確定由
  本輪匯入產生的 Python 快取檔已逐一刪除，空目錄亦移除；
  工作根沒有 root-owned 項目或誤建 `.md` 目錄，產物為
  UID/GID `1000:1000`。本專案無執行中或已停止容器，
  其他專案容器維持原狀。
- 成果提交 `13ec24d` 已推送私有 `origin/main`；遠端
  [Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)、
  [#7](https://github.com/wicanr2/colonization_cht/issues/7)、
  [#26](https://github.com/wicanr2/colonization_cht/issues/26)及
  [#27](https://github.com/wicanr2/colonization_cht/issues/27)
  已回填限定成果與仍缺的正式驗收，回讀均為 OPEN。

## 2026-09-24：目標095真視窗姓名鍵盤與提示守門審查

- [目標095](docs/goals/095-player-name-input-and-overlay-gate.md)
  先以 `327f2b2` 推送至核對為 PRIVATE 的儲存庫；本輪沿用
  固定合法 DOS 輸入及隔離 `workplace/dosgolem`，其
  `upstream` 推送仍為 `DISABLED`。讀取 dosgolem 既有
  `PushText`／`PushKeyNamed` 與固定 Ebitengine 字元事件後，
  先審[規格024](docs/spec/024-window-keyboard-input.md)至限定
  READY，才改正式視窗鍵盤接線。支援英文字母、數字、空格、
  Backspace、Enter；不支援字元明確拒絕及記錄，不改原版
  EXE、資料、規則或姓名記憶體。
- 初次 `go test` 因容器未設 `DISPLAY` 停在 GLFW 初始化；
  同一 Ebitengine 映像的 `xvfb-run` 因缺 `xauth` 停止，
  改以同容器有界、trap 管理的 Xvfb 重跑。測試首次揭露
  讀錯鍵盤佇列：dosgolem 先放 BIOS 環形緩衝，並非
  `DOS.Keys` 後備佇列；修正測試後 `go test ./...` 與
  `go build` 通過。沒有新建重複映像或修改上游專案。
- 真 Ebitengine 視窗從冷啟動實際點擊主選單、難度完成、
  選國右卡與完成區，於姓名頁鍵入 `x`、退格、Enter。
  原版畫面相應顯示 `x_`、游標及 `FRANCE` 長文。
  第二次真視窗路徑驗 `!` 拒絕與失焦 `x` 不補送；
  兩次均以相同輸入重播英文無覆蓋控制。CPU、完整 RAM、
  原版索引、色盤、時間與開檔同狀態；圖像與目標093
  dosgolem 控制圖只差滑鼠游標位置。獨立驗證器 PASS
  收據 SHA-256
  `54ffa9db8a3145f9e93391aa3d557b42c58d968cbd86177a631001f5699c0cae`，
  鍵盤規格024升限定 CONFORMED。
  最終版另對輸入收據未使用欄位嚴格拒絕；同一容器重跑
  單元測試與建置，再重播正反兩份真視窗收據，原版狀態
  與先前英文控制逐項相同。
- 固定中文提示仍缺完整來源訊息執行期守門及離頁回退。
  既有 `0x2A864` 只在 `0D21:00C6` 逐字更新；原版
  筆畫含色號68／47／128，不可照搬難度欄的顏色假設。
  [規格023](docs/spec/023-player-name-screen-draft.md)維持
  DRAFT、提示仍顯示原文、正式中文顯示十四段不變。
  詳細位址與推論等級見[研究紀錄](RESEARCH-LOG.md)。
- 原版索引、RAM、真視窗 PNG、字型及測試建置只在
  已忽略的 `workplace/`；文件、唯一工作清單、Issue
  #29／#26 依限定成果更新。交付前已確認合法原版 EXE
  SHA-256 不變、Git 未追蹤原版素材、工作根無 root-owned
  檔案或誤建 `.md` 目錄、隔離 dosgolem 上游推送位址為
  `DISABLED`，本輪三種既有映像無執行中或停止容器。
  成果提交 `3632696` 已推送 PRIVATE `origin/main`；
  真正主機 `gh` 已更新並回讀[Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)
  與[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)，
  兩者均保持 OPEN。收尾文件回填另以後續提交推送。

## 2026-09-24：目標096姓名固定提示正式覆蓋與驗收

- 目標文件先以 `a34aa03` 推送 PRIVATE `origin/main`。本輪以
  隔離 dosgolem 及合法 DOS 原版唯讀輸入完成雙次冷啟動、
  無觀測控制、完整訊息讀取與415點畫布守門；修正來源
  `0E2D:09F4` 為 `DS:SI`、逐字讀取 `0D21:00C6` 為
  `SS:BX` 的位址契約。同文再次出現但開檔世代不同的負例
  已納入守門，沒有改原版 EXE 或資料。
- [規格023](docs/spec/023-player-name-screen-draft.md)先依證據
  升限定 READY，才接 `tools/live_menu.go` 的正式十五欄輸出。
  固定姓名提示用38px、328×35px字模與多色可逆補片；其餘
  十四欄的 alpha／尺寸／字級／譯文不變。真 Ebitengine 視窗
  從冷啟動走正常滑鼠路徑，實際 `x`、退格、Enter 及同輸入
  英文控制的 CPU、完整 RAM、索引、色盤、虛擬時間、開檔一致；
  中文新增畫素僅落在姓名提示安全矩形，姓名資料與下一頁不變。
  三份獨立驗證收據及雜湊詳見[研究紀錄](RESEARCH-LOG.md)。
- 真 TSV 缺鍵／重複鍵、缺字模／錯字級、游標遮住及移開、
  原版單位元組錯版均通過失敗即關閉反例；錯版退出碼2。
  Ebitengine 工具映像內 `xvfb-run` 缺 `xauth`，分類為環境問題，
  改用同容器內有界 Xvfb 並以 trap 收尾；首次使用另一
  Pillow 版本量得329px而非既定328px，故回到既有
  `rich2-py:latest` Pillow 12.3.0 重烘，未新建重複映像。
  規格023通過限定 CONFORMED，正式中文顯示由十四增至十五段。
- 使用者再確認難度標題 A 版（「選擇」34px、「難度」38px、
  共同置中，卡片與完成提示不變）。核對現行
  [規格018](docs/spec/018-difficulty-heading-layout-draft.md)、
  程式及私有截圖 SHA-256
  `86b2c08465ed67fc57202e7490a7ac274185c78bf464e2a0e773b120bb196e07`；
  此版先前已完成同狀態驗收及截圖更新，因此不重抓、不覆寫。
  姓名頁真視窗 PNG／原版畫素仍僅留已忽略的 `workplace/`。
- 本輪更新目標、規格、README 目前狀態、CONTEXT、研究紀錄
  與唯一工作清單；Issue #29 的固定姓名提示範圍完成，
  Issue #26／#27 及長文／help／旗卡後續範圍保持開放。
  Git、Docker 衛生、遠端 Issue 與推送結果於交付前核對。
- 實作與限定收據以 `8767649` 推送私有 `origin/main`；
  真主機 `gh` 已回填 #29／#26。曾將 #29 按固定提示範圍
  關閉，但回讀 Issue 原驗收發現尚含可編輯預設姓名欄的
  逐欄中文幾何／回退；已立即重開並留言訂正。
  #29 與 #26 均保持 OPEN，固定提示的限定 CONFORMED
  不等於整張姓名畫面完成。下一階段須先釐清姓名譯名是否
  只在顯示層處理，不能擅自改原版姓名資料。

## 2026-09-24：目標097姓名欄來源、畫素與顯示選項查證

- [目標097](docs/goals/097-name-field-display-choice.md)先以 `c938bc8`
  推送至已核對為 PRIVATE 的 `origin/main`。沿用合法 DOS 原版唯讀
  輸入、隔離 `workplace/dosgolem`、固定16筆正常玩家輸入及既有
  研究／Ebitengine 映像；上游推送位址保持 `DISABLED`。
- 以有界 Docker 重播無輸入雙次、`x`、退格、Enter 及各自無觀測
  控制，確定預設姓名來源、286筆原版畫布寫入、285點淨墨跡、
  輸入框與安全區。再以 Ebitengine 產生本機 A原名／B中文佔位
  的可丟棄圖；兩圖只差姓名欄，A 圖與既有正式姓名畫面逐像素
  相同。B 的「中文譯名示意_」尚非譯稿；不改十五段正式顯示。
- 最初 Go 執行環境因 shell 登入設定未載入 `/usr/local/go/bin`
  停止，改用映像內明確路徑；早期合成底圖的提示區與現行
  真視窗相差1,266像素，改以目標096已驗真視窗底圖後，
  A 圖逐像素相同。`tools/card_preview.go` 無 `-base` 的舊路徑
  與先前原型輸出逐位元組相同。這些是工具／底圖選擇問題，
  不記為原版產品缺陷。
- 獨立 `tools/check_goal097_name_preview.py` 重跑 PASS，
  收據 SHA-256
  `0e6ece12a6452d56b4e473ebf1f5bcba5e5aa3006a3efc06634ee015332f185f`；
  來源、位址空間與分支差分見[研究紀錄](RESEARCH-LOG.md)。
  另重驗使用者已選難度標題 A 版的既有收據，PASS，
  私有截圖與驗收來源圖 SHA-256 同為
  `86b2c08465ed67fc57202e7490a7ac274185c78bf464e2a0e773b120bb196e07`；
  因目標086已完成，未重複修改或重抓截圖。
- 本輪只把追蹤與原型工具加入版控；所有包含原版畫素的姓名
  畫面、二進位收據與字型仍留在已忽略 `workplace/`。
  姓名欄是否採 B、真正譯名與正式輸入切換仍待使用者決定；
  [Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)
  保持 OPEN，不宣稱整張姓名畫面或全遊戲完成。
- 階段成果提交 `a2becd5` 已推送私有 `origin/main`；真正主機
  `gh` 已留言回填並回讀 Issue #29 為 OPEN。Git 未追蹤原版
  封存檔或 `workplace/`；隔離 dosgolem 的 `upstream` push
  仍為 `DISABLED`。目標097原型與收據均由 UID/GID `1000:1000`
  持有；工作根未見 root-owned／誤建 `.md` 目錄，專案沒有
  執行中或停止的 Docker 容器。

## 2026-09-24：目標098首次法國介紹兩頁來源與譯文草稿

- 目標098先以 `2770aaa` 推送 PRIVATE 儲存庫。沿用 UID/GID
  `1000:1000`、無網路且有限資源的既有研究／Python 容器，合法
  DOS 原版只讀，隔離 dosgolem 提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；其 `upstream`
  推送位址仍是 `DISABLED`。
- `tools/probe_goal098_intro.go` 雙次重播首次 Enter 顯示的 A 頁，
  另以第一次之後的正常 Enter 取得 B 頁；兩頁各有無觀測控制。
  `tools/check_goal098_intro.py` 重跑 PASS，核對來源、預讀反例、
  794／207字印字、CPU／完整 RAM／索引／色盤／時間、畫布與第一頁
  既有 Ebitengine 原文圖。兩節譯稿新增於
  [雙語 TSV](text/nation-introduction.zh-Hant.tsv)，原始段落 SHA、
  正文非空格字元及 `{}` 強調數量通過獨立檢查；本機收據 SHA-256
  `509b61e6c91cdeb24823a22ffea909342ddad9bf6d9f38e55cea52b9bc4bcdef`。
  原版 PNG／JSON 只留已忽略 `workplace/reports/goal098-intro/`。
- [規格025](docs/spec/025-first-nation-introduction-draft.md)維持
  DRAFT：來源節至印字緩衝的完整搬運鏈仍是強推論；安全矩形只
  候選，第二頁真視窗、第三次 Enter／離頁、中文逐欄字級／換行與
  回退未驗。固定 Cubic 11 字型在本次檢查的既有本機位置與映像
  未找到，未用替代字型偽裝量測；十五段正式中文顯示不變。
- 同期使用者選定第一張國家旗卡 A 的「英格蘭：」21px／「移民」
  25px，排除 B 的25／29px；已回填 `CONTEXT.md` 與規格021，
  僅解除該卡視覺方向，不推及相鄰旗卡或直接升 READY。
- 唯一工作清單由 `docs/worklist.json` 在 Docker 重新生成並
  `tools/worklist.py verify` 通過；README 只新增穩定雙語語料入口，
  不記逐輪命令。原版畫素與字型未新增 Git 截圖或資產。
- 目標098成果以 `8304afa` 推送 PRIVATE `origin/main`；主機真正
  `gh` 已留言並回讀 Issue #30／#12／#27 均為 OPEN。重新編譯
  Go 探針後再從冷啟動跑一份第一頁，JSON 與原先雙重播
  `intro-a.json` 逐位元組相同。新增檔與本機畫面均為
  UID/GID `1000:1000`；工作根未見 root-owned 或誤建
  `.md` 目錄，專案 Docker 容器無殘留。下一輪依使用者 A
  決定另建[目標099](docs/goals/099-first-nation-card-a-overlay.md)。

## 2026-09-24：目標099第一張旗卡 A 版正式顯示

- 依使用者明確決定採 A：「英格蘭：」21px、「移民」25px；排除
  B 的25／29px，不外推到相鄰右卡。目標099已先以 `e10dbf0`
  推送 PRIVATE `origin/main`，再作實作。知識路由命中復古中文化
  逆向／規格閘門與 README 標準，保留 RE→READY→CONFORMED
  及 README／CONTEXT／WORKLOG 分工。
- `tools/probe_goal099_card_leave.go` 從正常玩家路徑確認第一張卡
  直接完成區離頁，雙重播與無觀測控制同狀態；先前規格021
  已據此與目標089升限定 READY。固定 Cubic 11 原始 TTF
  在已檢查位置未找到；`tools/prepare_goal099_card_masks.py`
  從原先已驗 A 原型抽出兩個本機同源字模，核對真 TSV／原版
  bytes／字級／尺寸／墨跡 SHA，沒有換用其他字型或提交字模。
- `tools/live_menu.go` 增加預設關閉的 `--nation-card-a` 旗標，
  只對第一張旗卡兩欄從唯一片段 TSV 建鍵；來源讀取、格式化
  原文、原版123／156點印字、安全矩形、色盤、當幀補片及
  游標逐欄守門。正式紅字索引12、黑影索引0；任何失效逐欄
  回原文。組裝器固定來源 SHA 同步更新。
- 真 Ebitengine 視窗從冷啟動經滑鼠抵達第一張旗卡，16筆
  輸入重播中文、英文控制與舊十五欄，原版 CPU、完整 RAM、
  索引、色盤、時間與開檔一致；新差異只在兩欄安全矩形，
  各1,915／2,738個輸出像素，舊十五欄逐幀套用狀態不變。
  真視窗截圖與最後合成逐像素相同。固定43M步的缺上欄
  譯文／字模、下欄重複鍵／錯字級四例逐欄回退且另一欄
  逐像素不變；上／下游標、移開、下欄按住、切右卡與直接
  離頁六例 PASS。切右卡與離頁後整張 PNG／索引／色盤
  均與未開啟新覆蓋的同輸入舊版相同；錯版原版啟動前
  exit 2。當前原始碼與更新 TSV 重建後再跑43M步，原版
  狀態與整張 PNG 和驗收版完全相同。
- Ebitengine `go build` 成功；`go test .` 第一次因容器沒有
  DISPLAY 而失敗，分類為測試環境，補上有界 Xvfb 後同一
  容器／同一命令乾淨重跑 PASS。`tools/worklist.py write`／
  `verify` 通過。[規格021](docs/spec/021-nation-card-red-text-draft.md)
  僅第一張旗卡限定 CONFORMED；本機正式顯示十五增十七段。
  私有[第三張截圖](docs/screenshots/nation-card-first-zh.png)
  已在真視窗同狀態與逐像素驗證後更新 README；不代表公開
  發行許可或整頁／全遊戲已中文化。
- 程式、規格、唯一工作清單、CONTEXT、RESEARCH-LOG 與
  截圖以 `04e9c91` 推送至再次核對為 PRIVATE 的
  `origin/main`。主機真正 `gh` 驗證登入後更新並回讀
  Issue #7／#12／#26／#27，四者均 OPEN。Git 身分與最近
  commit 作者均為 `wicanr2@gmail.com`；原版 EXE／TXT、
  原始 TTF、字模及 `workplace/` 未追蹤。隔離 dosgolem 的
  `upstream` 推送位址仍是 `DISABLED`。所有本輪輸出是
  UID/GID `1000:1000`，工作根未發現 root-owned 或
  誤建 `.md` 目錄，專案相關執行中／停止 Docker 容器無殘留。
  相鄰右卡字級仍待使用者決定；介紹長文、help、靜態字圖
  與發行仍未完成。

## 2026-09-24：目標100四國介紹八節雙語語料

- 使用者再次確認第一張旗卡 A 的21／25px；比對目標099的正式
  實作與同狀態收據後，確認已完成，不重複覆蓋，也不延伸到
  右側旗卡。目標100先以 `b16190d` 推送 PRIVATE `origin/main`，
  再開工本輪語料；主機 Git 身分為 `wicanr2@gmail.com`，
  真正 `gh` 核對儲存庫 PRIVATE 且 Issue #27／#30 OPEN。
- 翻譯協作先唯讀六個尚缺的英格蘭、西班牙、荷蘭介紹節並交回
  繁中草稿；主工作樹逐句校對後加入既有 TSV，原有法國兩列不改。
  `GAME.TXT` SHA 固定，八節檔案位移、下一頂層標記、逐節 SHA、
  原文、雙語標題與強調標記由新檢查器核對；兩個獨立唯讀容器
  均得語料 SHA-256
  `bce0527cc13217b8b97b467ee7852a9b3c96af11eb79463bc4420309ae493817`。
  錯版 GAME 與錯誤語料各被拒絕；原有目標098的法國檢查器在
  八節 TSV 上回歸 PASS。首次在研究映像執行該舊檢查器時因
  缺 Pillow 失敗，歸類為容器依賴不符；改用既有
  `rich2-py:latest` 後同一函式 PASS，未改原版或安裝主機套件。
- 目標100的語料沒有進入正式 Ebitengine；規格025仍 DRAFT，
  新六節缺正常玩家路徑、字級、安全區、換行與回退證據。
  README 僅更新穩定雙語入口，CONTEXT／RESEARCH-LOG／
  唯一 `docs/worklist.json` 同步；由工具重生 `WORKLIST.md`
  並 verify PASS。正式顯示仍十七段，Issue #27／#30 不可關閉。
