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
- 成果以 `154888e` 推送至再次核對為 PRIVATE 的 `origin/main`；
  主機真正 `gh` 已分別留言並回讀 Issue #27／#30，兩者仍
  OPEN。Git 工作樹乾淨，最近提交作者 `wicanr2@gmail.com`；
  追蹤檔沒有原版封存檔、解包物、字型或 `workplace/`。
  隔離 dosgolem 的 `upstream` 推送位址仍是 `DISABLED`；
  本輪檔案 UID/GID `1000:1000`，工作根沒有 root-owned 檔案
  或誤建 `.md` 目錄，專案 Docker 執行中／停止容器均無殘留。

## 2026-09-24：目標101四國介紹原版玩家路徑

- 上一輪目標100確實新增八節可追溯語料，屬有效進度；但
  其他六節當時只有檔案來源。本輪先以 `be755bc` 把
  [目標101](docs/goals/101-nation-introduction-player-path.md)
  推送至再次核對 PRIVATE 的 `origin/main`，Issue #30 遠端
  OPEN。知識路由命中復古遊戲逆向、規格閘門、dosgolem 與
  README 證據標準；中文覆蓋仍待 READY。
- 已驗私有選國畫面為四張旗卡；擴充既有目標098探針，以正常
  滑鼠分選英 `(155,50)`、法 `(255,50)`、西 `(155,150)`、
  荷 `(255,150)`，各經完成區、姓名 Enter、A→B Enter。
  原版素材只讀、收據只在已忽略 `workplace/reports/goal101-intro/`。
  第一次建置因 `sh -lc` 覆寫研究映像的 Go PATH 而失敗，
  判為 shell 環境問題；改同一映像的 `sh -c`，`gofmt`、
  離線 Go build 通過，未另建映像或掛主機 Go。
- 四國各兩次冷啟動 JSON 逐位元組一致，各國無觀測控制的
  CPU、完整 RAM、索引、色盤、時間與開檔相同；八節實際
  印字與固定來源文本比對通過。西班牙 B 的 `50%%` 在原版
  實際印為 `50%`，已更新雙語 TSV 註記。法國舊收據的
  來源、轉存、印字、畫布及開檔欄位與擴充探針逐項相同。
  法國 B 後無鍵留原頁；Enter／ESC 到相同下一可見頁但
  CPU／RAM 不同，不聲稱兩鍵語意等價。
- `tools/check_goal101_nation_intro.py` 獨立驗證 PASS：本機
  `verified.json` SHA-256
  `dd2154447657e15c0964481d50392c9f5e3b531cce07d799376df3fbf6737937`；
  錯版輸入與錯誤 TSV 均拒絕。舊法國譯稿檢查器在更新
  八節註記後回歸 PASS。`tools/worklist.py write`／`verify`
  PASS；CONTEXT、規格025、研究紀錄與 README 現況已
  訂正，正式中文顯示仍十七段、Issue #30 不關閉。
- 原始 Cubic 11 TTF 仍未恢復；四國中文長文的安全矩形、
  最長譯文換行、真 Ebitengine 第二頁及回退未驗，規格025
  保持 DRAFT。工作根 root-owned／誤建 `.md` 目錄數為0；
  本輪檔案與收據 UID/GID `1000:1000`，隔離 dosgolem
  `upstream` 推送位址仍 `DISABLED`。本輪一次性 Docker
  容器無殘留；`docker ps -a` 僅有其他專案容器，未觸碰。
- 目標101程式、證據、規格與現況以 `4cec24c` 推送 PRIVATE
  `origin/main`；主機真正 `gh` 已留言並回讀 Issue #30／#27，
  兩者仍 OPEN。Git 未追蹤原版素材、字型或本機收據；
  下一輪先處理長文欄位字型來源與逐頁版面，不把原版
  命中誤當中文顯示完成。

## 2026-09-24：目標102四國介紹長文離線排版

- 先核對 Git 身分、私有遠端與 Issue #30；以 `a5a0136` 將
  [目標102](docs/goals/102-nation-introduction-layout-prototypes.md)
  推送私有 `origin/main`，再修改探針及排版工具。知識路由命中
  復古遊戲規格閘門、文件職責、README 與資料化工作清單入口。
- 從本機 Go 模組快取及另一研究副本找回同 SHA-256 的 Cubic 11
  原始 TTF；只唯讀量測，將版本與授權來源記在 `font/README.md`。
  以 dosgolem 正常玩家流程重播四國 A／B，新增首字印前底圖擷取；
  八頁原始背景一致，新探針既有收據與目標101一致。
- 以實字型產生貼近原版字高與緊湊兩套四國八節離線中文排版，
  逐頁驗證原版重建、字形、換行、標題／正文安全矩形及裁切；
  兩套八頁 PASS，僅兩張含原版像素的對照表格進私有儲存庫。
  原版輸入、字型及完整收據保持在 Git 之外。規格025仍 DRAFT，
  Ebitengine 正式顯示維持十七段，Issue #30 不關閉。
- 重跑檢查時，第一次把排版圖片誤指定到不存在的 `previews/`
  子目錄，屬命令路徑錯誤；以同一映像、同一檢查器改用實際
  `workplace/reports/goal102-intro/` 目錄後，印前底圖與八頁雙候選
  均 PASS，安全區外0像素。`tools/worklist.py write` 重生後
  `verify` 通過；附帶誤呼叫不存在的 `check` 子命令只顯示用法，
  不當成清單或產品驗證失敗。

## 2026-09-24：目標103十七欄字模獨立重烘

- 前一目標102已推送八頁 DRAFT 對照與 Issue #30 更新，屬有效
  進度；本輪在乾淨 `ca42ff0`、正確 Git 身分、PRIVATE 遠端及
  Issue #12 OPEN 下，以 `829d9db` 先推送[目標103](docs/goals/103-font-rebuild-and-mask-parity.md)。
  知識路由命中復古遊戲技能、規格閘門、README／文件職責與
  資料化工作清單；未自行選擇四國長文版式。
- 在限資源、無網路、非 root 的 `rich2-py:latest` 容器中，
  唯讀掛載固定原版與 Cubic 11，從真 TSV 重烘前十五欄，
  全部與目標096本機已驗 JSON 逐位元組相同；新增直接由
  原始 TTF 重烘第一張旗卡 A 版兩欄的工具，與目標099字模
  Alpha bytes 逐位元組相同。未修改 `tools/live_menu.go` 或
  `workplace/dosgolem`，現行正式中文顯示仍十七段。
- 獨立驗證器的十七欄正例及錯字型、錯譯稿、缺原版、缺欄、
  改動 Alpha 反例均通過，錯輸入不留部分字模；收據見
  `workplace/reports/goal103-font-parity.json`。本機工具映像
  只有固定 ID，尚無專案內可重建來源，因此不宣稱跨機獨立
  打包或字型可公開散布。後續仍要處理四國介紹正式版式選擇、
  事件／頁相位守門及真視窗同狀態，Issue #12／#26 保持 OPEN。
- `tools/worklist.py write`／`verify` 與三支新工具的語法檢查
  通過；`workplace/reports/goal103-font-rebuild/`、收據及兩欄
  字模均為 UID/GID 1000:1000。工作根 root-owned 檔案及
  誤建 `.md` 目錄為0，專案相關 Docker 執行中／已停止容器
  均無殘留；原版 EXE／TXT／封存檔、字型和本機字模未入 Git，
  隔離 dosgolem 的 `upstream` 推送位址仍為 `DISABLED`。
- 原版缺失的命令列負例另外確認烘製器與驗證器都回 `SKIP 77`，
  不留下成功收據；這與錯字型、錯 TSV 的失敗即關閉分開計算。
- 工具、驗證與文件以 `68ec5ad` 推送 PRIVATE `origin/main`；
  主機真正 `gh` 已留言並回讀 Issue #12／#26，兩者仍 OPEN。

## 2026-09-24：目標104三國介紹 B 頁離頁守門

- 本輪先核對第一張旗卡的 A 版21／25px早於目標099已限定
  CONFORMED，不重做或擴張到長文。於乾淨工作樹、正確 Git
  身分、PRIVATE 遠端與 Issue #30 OPEN 下，先以 `a0e6a8e`
  推送[目標104](docs/goals/104-nation-introduction-exit-phase.md)，
  再修改探針。知識路由命中復古遊戲／中文化、規格閘門與
  資料化工作清單；長文版面仍待使用者另行選擇。
- 在無網路、限資源、非 root 的研究容器，以隔離 dosgolem
  為英、西、荷三國各跑無鍵／Enter／ESC、雙重播與無觀測
  控制共27份報告。`-after-b none` 的英格蘭舊新 JSON
  逐位元組一致；九分支在75M與目標101同國 B 頁一致。
- 獨立驗證器逐分支比對原始索引／畫布／色盤、完整 CPU／RAM
  與虛擬時間、開檔、清屏和新頁印字；正例通過。缺原版
  SKIP、錯版本與單一原始畫素改動均被拒絕。三國無鍵仍留
  B 頁；Enter／ESC 抵達各國下一可見頁但 RAM 不同。
  [規格025](docs/spec/025-first-nation-introduction-draft.md)仍
  DRAFT；沒有改正式 Ebitengine，正式中文維持十七段。
- 收據只在已忽略的 `workplace/reports/goal104-intro/`；
  `docs/worklist.json` 更新後由工具重生 `WORKLIST.md`。
  原版檔案、字型、原始畫面與完整報告均不入 Git。
- 收尾回歸重跑目標101及104檢查器、目標104負例、
  `tools/worklist.py verify` 均 PASS。目標104輸出檔擁有者為
  UID/GID 1000:1000，工作根無 root-owned 項目或誤建
  `.md` 目錄，專案研究映像的執行中／已停止容器均無殘留；
  隔離 dosgolem 的 `upstream` 推送位址仍為 `DISABLED`。

## 2026-09-24：目標105首則教學入口與開場字幕

- 先核對乾淨工作樹、`wicanr2@gmail.com`、PRIVATE 遠端、
  Issue #7／#27 OPEN 與隔離 dosgolem 禁推，以 `c0caf66`
  **先推送**[目標105](docs/goals/105-first-tutorial-player-path.md)
  才修改探針。知識路由命中復古遊戲／中文化、spec 閘門、
  README 現況聲明與資料化工作清單；沒有替使用者選長文版式。
- 研究映像初次用登入 shell 啟動，把映像設定的 Go PATH
  重設；改為明確 `/usr/local/go/bin/` 後又發現非 root
  預設 `GOCACHE=/.cache/go-build` 不可寫。分類為容器命令
  環境問題；同一既有映像改用容器內 `/tmp/goal105-go-build`
  重新建置通過，未建立重複映像、未用主機 Go。
- 原版正常玩家路徑從英格蘭介紹 B 後 85M 頁面分無鍵／
  Enter／ESC，各雙次冷啟動與無觀測控制；舊探針預設
  JSON 與目標101逐位元組相同。`@TUTORIAL1` 在88.38M
  確實被 DOS 讀入，卻沒有顯示；實際印出的是 `@BUILD1`
  英文開場字幕。第一次來源收據漏掉跨512-byte邊界的
  字幕後段；把觀測分兩次讀取並重跑，兩段均對回 RAM、
  當次61-byte印字及1,040次原版畫布改色。
- [規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)
  保持 DRAFT；主譯稿新增一筆字幕繁中候選，原版來源／
  控制碼驗證共369筆 PASS。獨立驗證器及缺原版 SKIP、
  錯版本、原始畫布破損、改動實際印字反例均 PASS。
  探索性延伸至150M且在100M／115M再按 Enter，畫面
  仍是同一字幕，但未把單次觀測當作教學不可到達的結論。
- 修正 README／CONTEXT 已過期的「其他國家 B 後未驗」
  與368筆斷言。沒有修改正式 Ebitengine；中文顯示維持
  十七段，24則 help 尚無顯示命中。原版與本機 PNG、
  完整收據保持在 Git 之外，未新增公開素材。
- 收尾以相同 Docker 研究映像重跑目標101／104／105
  獨立檢查器、目標105錯版／畫布／印字負例、369筆
  主譯稿來源驗證及 `tools/worklist.py verify`，全數 PASS；
  原版缺失命令列回 `SKIP 77` 且不留成功收據。本機
  `receipt.json` SHA-256
  `97e92bd05ce8ff6fd97778e3a70ad4d76de6daf6fc44b08dd6e7fc802d697da7`。
  目標105輸出 UID/GID 1000:1000；工作根無 root-owned
  項目或誤建 `.md` 目錄，兩個本輪映像均無容器殘留，
  隔離 dosgolem `upstream` 推送位址仍為 `DISABLED`。

## 2026-09-24：目標106開場字幕印前背景與繁中字級對照

- 上一個使用者確認第一張旗卡 A 版的回合只核對既有
  CONFORMED 狀態，未新增中文化進度；本輪改接目標105
  真正顯示的 `GAME.TXT:@BUILD1` 字幕。核對
  `wicanr2@gmail.com`、乾淨工作樹、PRIVATE 遠端、
  Issue #7／#26／#27 OPEN 與隔離 dosgolem `upstream`
  禁推後，以 `d787aa4` **先推送**
  [目標106](docs/goals/106-build-opening-caption-overlay-gate.md)。
  知識路由命中規格閘門、顯示／語意隔離、dosgolem、
  文件職責與資料化工作清單；使用了
  `reverse-engineer-retro-game-remake` 的證據／驗證方法，
  未把本案改為 remake。
- 擴充 `tools/probe_goal098_intro.go -preprint`，只在啟用
  `-after-follow` 時另存字幕首筆 `0D21:012C` 寫入前
  畫布；未帶新旗標的英格蘭75M JSON 與目標101舊收據
  逐位元組相同。兩次獨立英格蘭冷啟動與一次無讀寫
  監看控制到100M；雙重播 JSON 完全相同，控制組
  CPU／完整 RAM／原始畫布／色盤／時間／開檔一致。
  原版印前畫布 SHA-256
  `d8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab`；
  印後差1,040點，bbox `[16,30,303,39)`，新色號
  14／47／54。
- 以固定 SHA 的 Cubic 11 TTF、真實 TSV 草稿和原版
  多色印前底圖做38px／42px兩個本機可丟棄樣本，
  實際墨跡分別430×35／482×39px，兩者前景與暗影
  均位於四倍安全矩形 `[48,108,1228,168)`。
  首次樣本檢查把 Pillow `getbbox` 的留白當成實際
  Alpha 墨跡，正確地拒絕；改為裁出真實非零墨跡後
  用同一固定輸入重跑通過，屬量測腳本修正而非
  原版行為差異。並列圖、原版畫素及字模留在忽略
  版控的 `workplace/reports/goal106-caption/`。
- 視覺取捨依 `grill-me`／`grilling` 先展示原版／
  A 38px／B 42px並列原型，只問這一欄的正式字級；
  使用者尚未回答，因此規格026仍 DRAFT、正式
  Ebitengine 保持原文，既有十七段顯示數不變。
  此技能使「是否放大這行字幕」未被樣本悄悄寫成
  正式版式，四國長文的另一待決版式也未被外推。
- `tools/check_goal106_caption.py` 獨立正例 PASS；
  `tools/test_goal106_caption.py` 的缺原版 SKIP、
  錯版、錯字級、印前畫布單點破損及雙重播變異
  負例 PASS，命令列缺原版回 `SKIP 77` 且未留
  假成功收據。本機 `receipt.json` SHA-256
  `54b1e99255e49848eaa8810fc0063c5dcae38d990dbb84cd3ec147ec7ba4cf6b`。
  舊目標105收據、369筆主譯稿來源及
  `tools/worklist.py verify` 回歸 PASS；
  `WORKLIST.md` 已由 JSON 重生，內容未因只改
  JSON 驗證註記而變。另更正規格022中第一張
  旗卡 A 仍待決及十四段的過期現況，不改其
  相鄰右卡 DRAFT 事實。
- 原版 EXE／TXT／封存檔、字型、原版索引與
  畫布均未入 Git；本輪輸出 UID/GID 1000:1000，
  工作根無 root-owned 或誤建 `.md` 目錄；
  `colonization-research:20260920-r2` 與
  `rich2-py:latest` 無執行中或已停止容器殘留，
  隔離 dosgolem `upstream` 推送位址保持 `DISABLED`。
- 本輪成果以 `735a262` 推送 PRIVATE `origin/main`；主機已登入
  的 `gh` 分別更新並回讀 Issue #7、#26、#27，三者仍 OPEN。
  遠端留言只記目標106的 DRAFT 證據與待選版式，未聲稱
  正式字幕或 help 已完成。

## 2026-09-24：目標107字幕後按鍵與海上畫面

- 上一個回合僅核對已完成的第一張旗卡 A 版，沒有
  新中文化進展；本輪依工作樹與遠端現況，先以
  `7858358` 推送[目標107](docs/goals/107-post-caption-input-and-help-entry.md)。
  讀取 `reverse-engineer-retro-game-remake` 的證據、
  規格與驗證方法，以及 dosgolem 能力、README、
  文件職責和唯一工作清單路由；本案仍是原版輸出
  階段中文覆蓋，不改寫遊戲規則。
- `tools/probe_goal098_intro.go` 新增選用
  `-post-caption-audit`：追鍵盤待取數，允許有界延伸，
  500M後每25M取原版畫面檢查點。不帶旗標的
  英格蘭100M JSON與目標105逐位元組相同。
  85M及100M送 Enter都被原版取走；無額外鍵自動
  走完十張 `@BUILD` 字幕，約1,185M進入海上
  遊戲介面。`@BUILD2`含原版變數，不能直接重用
  `@BUILD1`字幕來源鍵或38／42px候選。
- 1,350M原版雙冷啟動、無讀寫監看控制與100M
  額外鍵250M雙重播／控制一致；
  `tools/check_goal107_post_caption.py`核對全部
  raw indexed／canvas／palette、印字、標記、開檔、
  CPU／RAM與鍵盤收據 PASS。驗證器最初把
  空的 `follow_enter_at` 當成缺欄、另把
  `@BUILD1`讀入步數誤記為下一標記；查原始
  報告修正後以同容器同命令重跑 PASS，沒有
  修改原版或取巧放寬比較。負例含缺原版 SKIP、
  錯版、500M／1,200M索引破損、前後字幕
  印字破損、控制 RAM及鍵盤待取變異，均 PASS。
- 以 `rich2-py:latest` 在 Docker 內把四個原版
  索引檢查點轉成只留 `workplace/` 的本機 PNG；
  1,200M船／海面與1,225M上方選單已目視，
  沒有首則教學框。這是原版診斷，不是 Ebitengine
  正式中文截圖。規格026維持 DRAFT，十七段
  已驗中文畫面數不增加；下一窄任務是從正常
  海上畫面查證教學觸發或設定。
- 本機完整收據 SHA-256
  `e120301bb08f05b5a3461cd6fba5334ed25588a5896fa442f50bfd16d647ec58`。
  原版資料、畫素及字型未加入 Git。新輸出與文件
  UID/GID皆1000:1000；工作根沒有 root-owned
  殘留或誤建 `.md` 目錄，兩個本輪映像沒有
  執行中／已停止容器殘留；隔離 dosgolem
  `upstream`推送位址仍為`DISABLED`。
- 本輪成果以 `a606fe5` 推送 PRIVATE `origin/main`；主機
  `gh` 已登入並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5807959390)、
  [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5807959520) 與
  [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5807959662) 的留言，
  三者仍為 OPEN。使用者再次選定第一張國家旗卡 A
  （「英格蘭：」21px、「移民」25px）；核對規格021、
  目標099及正式 Ebitengine 同狀態收據，確認該決定
  已有限定 CONFORMED 實作，未重做或外推到其他旗卡。

## 2026-09-24：目標108十張開場字幕逐行譯稿

- 先核對 `main` 潔淨、Git 作者、PRIVATE 遠端及
  [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)，
  再以 `dbe8882` 推送[目標108](docs/goals/108-build-opening-caption-translation.md)
  與 `CONTEXT.md` 入口，之後才建立譯稿。
- 固定原版 `GAME.TXT` 的十張字幕有十一個 `^^` 行；
  本輪新增 `@BUILD2–10` 十行，主譯稿由369增至379筆。
  依目標107實際印字檢查英格蘭變數例值，`@BUILD4`
  以繁中語序調換具名占位符；只將草稿驗證改為
  核對占位符種類及次數，不修改原版或正式輸出。
- 全379筆原始來源／控制碼檢查與15個既有驗證器
  測試 PASS。`tools/check_goal108_caption_corpus.py`
  核對十一行原始位移、CRLF、雜湊與 dosgolem
  十段實際印字，七個正反例 PASS；目標107完整
  檢查重新 PASS，缺原版 CLI 回 `SKIP 77`。
  固定 Cubic 11 TTF 的81個用到字元均在 cmap。
  本機收據 SHA-256
  `95a1172326ea151c9df56332fc9d75e50d72c8af109d682e54c7fcba616d453a`。
- 第一版獨立檢查器誤把一筆原始行 SHA 後多貼
  `3a`，真原版正例因此失敗；核對原始 bytes 後
  更正。印字篡改反例最初改到非字幕事件而未觸發，
  後改為兩份重播同時篡改實際 `0D21:00C6` 字元，
  原版印字 SHA 閘門才正確拒絕。目標107舊檢查器
  要求非 root 擁有的輸出目錄，故改用本輪
  `workplace/` 目錄重驗；這些是驗證腳本／收據
  路徑修正，非原版或產品行為差異。
- 規格026仍 DRAFT；變數展開值的本地化、逐欄
  字級、安全區、正式 Ebitengine 中文顯示與 help
  觸發未完成。更新 README 現況、唯一工作清單、
  研究紀錄與本目標結果；正式已驗畫面保持十七段。
- 成果以 `76ca7f4` 推送 PRIVATE `origin/main`；主機
  `gh` 已更新並回讀 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5808215642)
  與 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5808215633)，
  兩者仍為 OPEN。原版／字型／索引畫面未加入 Git；
  本輪收據及新檔 UID/GID 1000:1000，隔離 dosgolem
  的 `upstream` 推送位址為 `DISABLED`；工作根沒有
  root-owned 或誤建 `.md` 目錄，本輪 Docker 映像
  沒有執行中或已停止容器殘留。

## 2026-09-24：目標109四國開場字幕變數值

- `da956bf` 已先把目標109及 CONTEXT 入口推送 PRIVATE
  `origin/main`，之後才以隔離 dosgolem 開始新探針。
  使用者再次選定第一張旗卡 A：核對目標099、規格021
  與既有 Ebitengine 收據，21／25px兩欄早已正式限定
  CONFORMED，沒有重做，也沒有擴張到其他旗卡。
- 法國、西班牙、荷蘭各用固定16筆正常玩家輸入至800M步，
  雙冷啟動與無監看控制共九份新報告；英格蘭沿用
  目標107三份。四國前七張字幕及24處占位值與
  `GAME.TXT` 模板逐字核對。荷蘭的原始候選
  `Netherlands` 與實際 `the Netherlands` 不同，
  因此 TSV 分成檔案與展開兩欄，冠詞來源列未知。
- 新增24筆來源候選可追溯繁中草稿；獨立核對器 PASS、
  八個正反例 PASS，缺原版 SKIP、錯國／錯版／錯欄
  均失敗即關閉。正式 Ebitengine 已驗十七段不變，
  規格026仍 DRAFT，help 觸發和字幕逐欄版式仍待後續。
  詳細原始定位與推論等級見 RESEARCH-LOG；本機
  `receipt.json` SHA-256
  `fda3cd28d14c2ae09c94b51c5e74a638e0e15daa16202940c9d23845b3554b0c`。
- 成果以 `dbade4b` 推送 PRIVATE `origin/main`；主機
  `gh` 已留言並讀回 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5808523496)
  與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5808522160)，
  兩者仍 OPEN。原版／字型／畫布未入 Git；本輪收據、
  probe 與譯稿均由 UID/GID 1000:1000 持有，
  `workplace/` 無 root-owned 或誤建 `.md` 目錄，
  `colonization-research:20260920-r2` 沒有執行中或
  已停止容器殘留；隔離 dosgolem `upstream` 推送
  位址仍為 `DISABLED`。

## 2026-09-24：目標110教學選項的正常玩家輸入

- 先以私有 `origin/main` 推送目標110入口，再從目標107
  已驗的1,225M海上畫面延伸選用滑鼠／鍵盤事件。
  使用者再次確認第一張旗卡 A 的21／25px：核對
  目標099、規格021與 `CONTEXT.md`，先前已正式
  限定 CONFORMED，本輪沒有重做或外推到其他旗卡。
- 原版滑鼠實際打開 `GAME` 下拉選單、`Game Options`
  視窗並點 `Tutorial Hints` 最後一列；原版核取圖示
  與背景畫素變化。另一分支不進選單，左方向鍵先
  入列再被原版消費，海上船舶畫面改變。兩分支各
  兩次冷啟動及一次無監看控制，報告逐位元組一致，
  主要狀態檢查點同狀態；未見首則教學正文視窗。
  不宣稱核取預設語意，也不把抽樣未見推成全程未顯示。
- `tools/check_goal110_tutorial_hints.py` 正例 PASS，
  `tools/test_goal110_tutorial_hints.py` 四例 PASS，
  包括原版缺失 SKIP、改事件檔與壞原始索引畫面。
  不帶新旗標的100M探針 JSON 與目標105歷史收據
  逐位元組相同。選項／向西原始報告 SHA-256 分別為
  `56b6bbc19ecbfe46a6b0837fa07d869a69d048ff047d542ec9566efb8a474ca4`／
  `11a99ec088b3c322bb9f2c035b7cbae2e3ea48d50ee8a80221b76899832e55fb`。
- 規格026仍 DRAFT；主譯稿379筆、help 24則草稿與
  正式已驗十七段均不因選項點擊而改變。已更新
  `CONTEXT.md`、`RESEARCH-LOG.md`、`docs/worklist.json`
  及目標110，`WORKLIST.md` 由 JSON 重生並 `verify`。
  原版資料／完整畫素只留已忽略的 `workplace/`，
  抽查收據與工作清單皆為 UID/GID 1000:1000；
  `workplace/` 無 root-owned 或誤建 `.md` 目錄，
  研究映像無執行中／已停止容器殘留。

## 2026-09-24：目標111教學選項狀態與正常玩家後續

- 先核對乾淨工作樹、Git 作者、PRIVATE 遠端、
  Issue #7／#27、合法原版、隔離 dosgolem 禁推；
  以 `e19e380` 先推送[目標111](docs/goals/111-tutorial-hints-state-and-first-help.md)
  與 `CONTEXT.md` 入口，之後才執行新重播。
- 初探「只移入／點文字／點圖示」發現整列3,407
  像素差分含選取焦點，不能直接當開關證據。
  改成兩條分支最終都點第一列；原版圖示中心
  僅四點色號47→149，且點前同狀態。各分支
  雙冷啟動逐位元組相同、無監看控制所有檢查點
  同狀態；確認點擊會持續切換選項圖示。
- ESC、海上左鍵與 `ORDERS` 選單明示的 Space
  均被原版消費；兩種選項狀態在1,375M、1,425M、
  1,500M的 Space 取樣畫面相同，未見首則 help。
  `GAME → Retire` 僅見「真的要離開嗎？」確認框，
  未按 Yes；不能宣稱已找到重開新局入口。
  因此 help 正式顯示仍零則，十七段中文畫面不變。
- 探針只新增選用 Space 鍵，使用 dosgolem 現有
  `0x39/0x20` 對應；不帶 Space 的既有路徑 JSON
  與舊版探針逐位元組相同。`tools/check_goal111_tutorial_state.py`
  PASS，`tools/test_goal111_tutorial_state.py` 五例
  PASS；缺原版、改事件檔、壞畫面及無監看控制
  狀態差異都有反例。原版與完整畫面／RAM只在
  已忽略的 `workplace/reports/goal111-help/`。
- 規格026仍 DRAFT；已回填 `CONTEXT.md`、
  `RESEARCH-LOG.md`、唯一工作清單與目標111。
  下一步應查新局起點前能否由正常介面啟用提示，
  或把已驗 `Game Options` 八列逐欄建立中文顯示
  的來源與版面證據；不使用全域固定中文字級。
- `tools/worklist.py write` 後 `verify` PASS；目標110
  既有獨立收據重新 PASS。`git diff --check`通過，
  本輪沒有原版／字型／完整畫素進 Git；收據、探針
  和工作清單抽查 UID/GID 均為1000:1000，
  `workplace/` 沒有 root-owned 或誤建 `.md` 目錄，
  研究／畫面檢視映像沒有執行中或已停止容器殘留；
  隔離 dosgolem `upstream` 推送位址仍為 `DISABLED`。
- 實質成果以 `7958a3d` 推送 PRIVATE `origin/main`；
  主機 `gh` 已留言且回讀
  [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5809975529)
  與[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5809979608)，
  兩者維持 OPEN；此條收尾紀錄於後續文件提交補入。

## 2026-09-24：目標112遊戲選項來源階段

- 上一輪僅重核已完成的第一張旗卡 A 版，沒有新增中文化進展。本輪選正常玩家已打開的 `Game Options` 九處英文為新切片；核對 Git 作者、乾淨工作樹、PRIVATE 儲存庫與 Issue #7／#26／#27 後，先以 `171eb7b` 推送[目標112](docs/goals/112-game-options-chinese-display.md)及 `CONTEXT.md` 入口，再執行新探針。
- 在既有 `colonization-research:20260920-r2` 內擴充預設關閉的 `-options-audit`，沿固定英格蘭開局及正常滑鼠開窗輸入，用隔離 dosgolem 取九處 `GAME.TXT` 當次 DOS 來源、168-byte原版解析讀取、九段印字及1,300M索引畫面。雙冷啟動及無監看控制通過；獨立[來源檢查器](tools/check_goal112_options_source.py) PASS、七項正反例 PASS。Go 首次在非 root 容器因預設 `/.cache/go-build` 不可寫而失敗；改將 `GOCACHE` 指向容器 `/tmp/colonization-go-build-cache` 後重跑成功。收尾重新建置時碰到容器 PID 配額，改為 `go build -p 1` 即通過；兩者都是容器環境設定，不是遊戲缺陷。
- 新建[規格027](docs/spec/027-game-options-window-draft.md)保存各原版位移、來源與逐欄墨跡／候選安全矩形；把既有九筆譯稿「正常路徑輸出事件未驗證」註記訂正，沒有新增譯稿筆數或改掉 `~` ASCII 熱鍵標記。`validate_translation_draft.py` 驗379筆 PASS；目標110舊原版收據回歸 PASS。解析到印字緩衝最後搬運、印前底圖、反白／游標回退與中文字級未閉合，規格維持 DRAFT，正式顯示仍十七段，沒有更新正式截圖。
- 原始 DOS、完整 RAM 與原版畫素只留唯讀原版及已忽略 `workplace/reports/goal112-options/`；本機檢視用 PNG 亦不入 Git。輸出與研究工具 UID/GID 均為1000:1000；`workplace/` 無 root-owned 檔案或誤建 `.md` 目錄，研究及圖像映像無執行中／已停止容器殘留。隔離 dosgolem 提交仍為 `9dd36726`，`upstream` 推送位址 `DISABLED`。下一步是補來源最後搬運與逐欄印前底圖、用固定 Cubic 11 做可丟棄 Ebitengine 對照，再審查 READY。私有成果推送及 Issue 回讀於本輪收尾核對。
- 實質成果以 `db9cb8d` 推送 PRIVATE `origin/main`；主機 `gh` 已留言且回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5810493052)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5810493811) 及 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5810492932)，三者皆維持 OPEN。此收尾紀錄另推送一筆文件提交；規格027與目標112仍 in_progress／DRAFT，不把來源階段冒稱中文覆蓋完成。

## 2026-09-24：目標113遊戲選項逐欄底圖與可丟棄對照

- 使用者再次確認第一張國家旗卡 A（「英格蘭：」21px、「移民」25px，排除B）。先查目前程式、規格021與目標099，該選擇先前已限定 CONFORMED；本輪未重做、未修改旗卡截圖。接續前一輪尚在進行的遊戲選項，已先以 `6080a59` 推送[目標113](docs/goals/113-game-options-background-and-preview.md)及現況入口至 PRIVATE `origin/main`。
- 沿固定正常滑鼠開窗輸入，用隔離 dosgolem 探針加預設關閉的 `-options-preprint`；原版兩次冷啟動 JSON、九欄各自印前畫布逐 byte 相同，無監看控制的路徑及1,300M索引／色盤相同。九欄完整差分及對應步數見[規格027](docs/spec/027-game-options-window-draft.md)。窄監看沒有抓到解析→印字字元緩衝的最後寫入，不能因此推成已閉合，規格維持 DRAFT。
- 固定合法原版、真 TSV 與既有 Cubic 11 SHA，在 `workplace/reports/goal113-options/` 產出 A（貼近原版）／B（較大）兩套逐欄 Ebitengine 本機預覽及英文控制；沒有把原版像素、字型或字模放進 Git。`tools/verify_card_preview.py` 對兩組逐像素 PASS：原文控制符合原始索引、九欄外零差異、各欄透明區恢復印前多色底圖。`tools/test_goal113_options_preview.py` 的雙重播正例、錯原版／字型、過長譯文、壞底圖、控制分歧及缺原版 SKIP 77 都通過。第一次建置選用的既有 Ebitengine 映像缺離線模組；改沿用已含 v2.9.9 的既有 `eob-remake-go:1.26.7-ebiten2.9.9`，沒有開網路或新增重複映像。
- 對照只屬 DRAFT 的可丟棄畫面，使用者尚未為**遊戲選項九欄**選 A／B；真視窗動態守門、反白／游標／離頁回退未驗，正式中文維持十七段。更新規格、研究紀錄、目前脈絡與 Issue 工作項目，不更新 README 正式截圖。
- 自製程式與證據提交 `55c655c` 已推送 PRIVATE `origin/main`；主機 `gh` 留言並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5810957455)、[#26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5810957328)、[#27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5810957821)，三者均 OPEN。`tools/worklist.py write/verify`、Python AST、原版雙重播與正反例、Ebitengine A／B 逐像素收據均 PASS；`git diff --check` 通過。輸出抽查 UID/GID 1000:1000、`workplace/` 無 root-owned 或誤建 `.md` 目錄，研究／Ebitengine 專案相關一次性容器無執行中或已停止殘留，隔離 dosgolem `upstream` 推送仍為 `DISABLED`。本條交接紀錄另推送文件提交。

## 2026-09-24：目標114／115遊戲選項來源鏈勘誤

- 上一個 goal 續回合只核對已完成的第一張旗卡 A 版，沒有新增中文化進度。本輪先讀本機路由、逆向技能及 dosgolem 能力入口；以 `41a1d8b` 先推送[目標115](docs/goals/115-game-options-source-chain-correction.md)及 `CONTEXT.md` 入口到 PRIVATE `origin/main`，再驗證目標114未提交的探針與收據。
- 目標113「印字緩衝零筆寫入」係 `WatchWrites` 只保留一組 active range、畫布監看覆蓋緩衝監看的探針假陰性。改用單範圍分流後，原版九欄150個可見字元均有57步前同址同值的緩衝寫入，7步前有對應中繼讀取；另一次互斥高位址 RAM 監看證實九段正文142個 byte 的變更寫入。雙冷啟動、無監看控制與1,300M畫面相同；仍有一筆格式化來源讀取及 DOS 解析緩衝至高位址 RAM 的中間逐 byte 搬運未閉合。目標113勘誤與[規格027](docs/spec/027-game-options-window-draft.md)已回填，規格保持 DRAFT、正式十七段及 help 零則不變。
- `tools/check_goal114_options_dataflow.py` PASS（150個讀寫配對、133／134格式來源配對、142個高位址來源 byte）；`tools/test_goal114_options_dataflow.py` 正例與九項拒絕／缺原版 `SKIP 77` PASS。修正舊預覽器不再要求假陰性的零寫入後，`tools/test_goal113_options_preview.py` 的 A／B 原文與逐像素負例仍 PASS。Go 探針 `gofmt` 與 `go build -p 1` 在隔離 dosgolem 模組內 PASS；第一次在 `/repo` 編譯因非 Go 模組失敗，調整工作目錄後乾淨重跑，屬工具設定而非遊戲缺陷。`tools/worklist.py write/verify`、Python AST 及 `git diff --check` 均通過。
- 原版、TTF、原版畫素與完整 JSON 只在唯讀來源及已忽略 `workplace/`。抽查收據和 `WORKLIST.md` 為 UID/GID 1000:1000；`workplace/` 無 root-owned 或誤建 `.md` 目錄，研究／字型映像無執行中或已停止容器殘留；隔離 dosgolem 固定 `9dd36726`、`upstream` 推送位址 `DISABLED`。下一步需在原版正常玩家路徑補選取／反白、游標與 ESC 離頁相位，再逐欄視覺定案；九欄尚不可接正式中文圖層。
- 實質成果 `9731d3a` 已推送 PRIVATE `origin/main`；主機 `gh` 留言並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5811848479) 與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5811848070)，兩者均保持 OPEN。本條收尾紀錄另以文件提交推送。

## 2026-09-24：目標116遊戲選項互動畫面相位

- 上輪完成目標114／115來源鏈訂正、私有推送及 Issue 更新，屬實質進展。本輪先核對乾淨工作樹、Git 作者、PRIVATE 遠端、隔離 dosgolem `9dd36726`／禁推與目標原版；讀取復古遊戲路由、逆向技能及 dosgolem 能力入口後，以 `7b4d422` 先推送[目標116](docs/goals/116-game-options-selection-and-exit-phases.md)與現況入口。
- 新增第一列／末列純移鼠、ESC 離頁三份固定玩家事件檔及 `tools/probe_goal116_options_phases.sh`，沿既有正常開局、海上 `GAME` → `Game Options` 路徑，使用隔離 dosgolem 每支各兩次冷啟動與無監看控制。第一次批次在最後控制組輸出完成訊息時剛好碰外層600秒逾時；九份 JSON、原始索引／畫布／色盤均已存在並核對 SHA，放寬外層時間重跑同一入口正常結束；這是批次外層逾時，不是原版或產品失敗。
- 第一列與末列純移鼠同時點底層畫布完全相同，游標合成索引畫面相差160點；移到框外後兩支畫面完全合流。與目標111已驗的實際點擊末列收據在同時點、同游標位置比較，底層畫布多3,407點差異；但焦點與核取圖示混合，未把全部差異命名為單一效果。ESC 於1,351M由原版取走，1,375M回海上畫面，底層差22,885點，bbox `(62,41)–(258,159)`。本機原版 PNG 僅存已忽略 `workplace/`，人工檢視確認游標遮住末列文字及 ESC 後視窗消失。
- `tools/check_goal116_options_phases.py` PASS，`tools/test_goal116_options_phases.py` 正例與九項拒絕／缺原版 `SKIP 77` PASS；既有 `tools/check_goal111_tutorial_state.py` PASS，Python AST 與 `tools/worklist.py write/verify` PASS。[規格027](docs/spec/027-game-options-window-draft.md)維持 DRAFT；其他六列、按下／放開和首個重繪瞬間、正式中文字級與逐欄回退未驗，九欄仍英文、正式中文維持十七段。工作清單 Issue #7／#26 註記已回填；README 不記輪次，也不以本機原版 PNG 更新正式截圖。
- `git diff --check` 通過；原版 EXE／TXT、TTF、完整畫布／PNG 皆未由本輪加入 Git。新收據、檢視 PNG 與 `WORKLIST.md` 抽查 UID/GID 1000:1000；`workplace/` 無 root-owned 或誤建 `.md` 目錄，研究／圖像映像的專案相關執行中或已停止容器無殘留。隔離 dosgolem `upstream` 推送位址仍是 `DISABLED`。
- 實質成果 `b007a1a` 已推送 PRIVATE `origin/main`；主機 `gh` 留言並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5812354533) 與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5812354538)，兩者均保持 OPEN。本條收尾紀錄另以文件提交推送。

## 2026-09-24：目標117選項視窗同焦點核取圖示

- 前一個 goal 續回合只重核第一張旗卡 A 版，沒有新進度。本輪核對乾淨工作樹、Git 作者、PRIVATE 遠端、原版、隔離 dosgolem `9dd36726`／禁推、路由與規格閘門後，先以 `7bfbad5` 推送[目標117](docs/goals/117-game-options-same-focus-checkmarks.md)和現況入口，再新增兩份玩家輸入與重播腳本。
- 既有研究映像 `colonization-research:20260920-r2` 內，由原版唯讀 DOS 和隔離 dosgolem 重播只點第1列、先第4列再第1列、先第7列再第1列，每支兩次冷啟動及無監看控制。1,325M暫態差分只在第1列及被點列；全部點回第1列後，1,375M／1,400M第4與第7列各只留下自身圖示中心四點差異，分別47→149與149→47，原文與共同焦點畫素不變。圖示方向不等於已證實的開／關語意。
- `tools/check_goal117_same_focus.py` PASS，`tools/test_goal117_same_focus.py` 正例與八類負例／缺原版 `SKIP 77` PASS；修訂[規格027](docs/spec/027-game-options-window-draft.md)、研究紀錄與唯一 Issue 工作清單。規格仍 DRAFT、選項九欄仍英文、正式中文十七段不變；其餘第2／3／5／6列、按下／放開瞬間、中文字級／快捷鍵與逐欄正式回退仍需完成。本輪沒有更新 README 或正式截圖，也沒有把原版畫素推入 Git。
- 唯讀掛載下第一次用 `py_compile` 做語法檢查，因需寫入 `__pycache__` 而被拒；改用不寫檔的 `ast.parse` 和 `sh -n` 後通過，屬驗證環境設定而非產品缺陷。`tools/worklist.py write/verify` PASS、`git diff --check` PASS；原版素材未追蹤，收據與 `WORKLIST.md` 均為 UID/GID 1000:1000，`workplace/` 無 root-owned／誤建 `.md` 目錄，研究容器無執行中或已停止殘留；其他專案容器未碰。隔離 dosgolem `upstream` 推送位址仍為 `DISABLED`。
- 實質成果提交 `007a3e2` 已推送 PRIVATE `origin/main`；主機 `gh` 更新並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5812771927) 與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5812771979)，兩者均保持 OPEN。本條 Issue 交接另以文件提交推送。

## 2026-09-24：目標118補齊遊戲選項同焦點穩定相位

- 前一輪目標117已完成原版第4／7列同焦點收據、私有推送及 Issue 更新，屬實質進展。本輪核對乾淨工作樹、Git 作者、PRIVATE 遠端與既有 Issue、固定原版及隔離 dosgolem `9dd36726`／禁推；復古遊戲路由命中證據／規格閘門。先以 `cc49cdb` 將[目標118](docs/goals/118-game-options-remaining-rows.md)與現況入口推送，再新增四份玩家事件、重播腳本與獨立檢查器。
- 在既有 `colonization-research:20260920-r2` 中以唯讀原版、正常英格蘭玩家路徑各重播第2／3／5／6列兩次冷啟動及無監看控制，共十二條有界分支。各列點回第1列後，在1,375M／1,400M與目標117同焦點基線相比，只有本列圖示中心四點保留差異；第2／5／6列149→47，第3列47→149。1,325M／1,350M暫態差分僅在第1列與被點列。未以色號猜選項啟用語意，也未將索引相同誤稱跨時點 RGB 相同。
- `tools/check_goal118_remaining_rows.py` PASS，`tools/test_goal118_remaining_rows.py` 正例與八類拒絕／缺原版 `SKIP 77` PASS；目標111、117檢查器回歸 PASS，`tools/worklist.py write/verify`、AST 與 shell 語法、`git diff --check` 通過。已回填[規格027](docs/spec/027-game-options-window-draft.md)、研究紀錄與唯一 Issue 工作清單；九欄仍英文，正式中文十七段，規格維持 DRAFT。另依 `grill-me` 的視覺共同決策方式向使用者展示本機原文／A／B 同狀態對照並只問一題；答覆前不替選項視窗定字級，不把第一張旗卡 A 外推。
- 原版 EXE／TXT、TTF、原版畫素與完整收據沒有加入 Git；新輸出與 `WORKLIST.md` 抽查 UID/GID 1000:1000，`workplace/` 無 root-owned 或誤建 `.md` 目錄，本專案研究映像無執行中／已停止容器殘留，其他專案容器未碰。下一閘門是正式逐欄可逆底圖、游標／離頁失效與快捷鍵呈現；按鍵瞬間仍需有限原版取證，A／B 字級待使用者選擇。
- 實質成果提交 `714a5a9` 已推送 PRIVATE `origin/main`；主機 `gh` 更新並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5813129943) 與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5813129488)，兩者均保持 OPEN。本條 Issue 交接另以文件提交推送。

## 2026-09-24：目標119遊戲選項點擊細相位

- 前一 goal 續回合只核對已完成的第一張旗卡 A 版，未產生新中文化證據。本輪核對乾淨工作樹、Git 作者、PRIVATE 遠端及 OPEN 的 Issue #7／#26；知識路由命中復古遊戲規格閘門與 dosgolem 原版對拍。先以 `3a6ad42` 推送[目標119](docs/goals/119-game-options-click-phase.md)和現況入口，再開發可丟棄探針。
- 在既有 `tools/probe_goal098_intro.go` 加入預設關閉的 `-options-phase-samples`，把有界取樣插在原版正常玩家滑鼠事件之間，不改輸入或正式前端。第一列及 `Tutorial Hints` 各兩次冷啟動、另有無監看控制，共六條隔離 dosgolem 重播。1,302M按下後，1,302,001,000步底層仍未變、1,302,100,000步已變；1,303M放開後，1,303,100,000步仍未新增變化、1,303,500,000步各列只新增本列圖示中心四點。這是有界相位，非精確首條重繪指令，也不證色號對啟用語意。
- `tools/check_goal119_options_click.py` PASS；`tools/test_goal119_options_click.py` 正例、六類拒絕及缺原版 `SKIP 77` 通過。修正檢查器對 Go JSON 欄位大小寫的初始假設後，按原收據乾淨重跑 PASS；此為驗證器問題，不是原版缺陷。新增旗標關閉時重跑目標117同輸入，412份舊 JSON／索引／畫布／色盤與歷史收據逐 byte 一致。Go `gofmt`／`go build -p 1`、Python AST、shell 語法、`tools/worklist.py write/verify` 及 `git diff --check` 均已核對；首次 AST 命令的 shell 引號錯誤已改用直接 Python 入口重跑通過。
- 已回填[規格027](docs/spec/027-game-options-window-draft.md)、`RESEARCH-LOG.md`、`CONTEXT.md` 與唯一 `docs/worklist.json`。規格仍 DRAFT；正式遊戲選項九欄仍英文、中文總數十七段。使用者的第一張旗卡 A 決定已在目標099實作，未外推至此視窗 A／B 字級；README 及正式截圖未變。原版畫素和完整收據僅在忽略的 `workplace/reports/goal119-options/`，沒有提交原版素材。
- 本輪收據與 `WORKLIST.md` 擁有者抽查均為 UID/GID 1000:1000；`workplace/` 未見 root-owned 或誤建 `.md` 目錄，研究映像無相關執行中／已停止容器殘留。隔離 dosgolem `upstream` 推送位址仍為 `DISABLED`，提交 `9dd3672`。實質成果提交 `3933b25` 已推送 PRIVATE `origin/main`；主機 `gh` 留言並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5813631583) 與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5813631978)，兩者均保持 OPEN。本條遠端交接紀錄另以文件提交推送。

## 2026-09-24：目標120第三張難度卡片原文輸出

- 使用者再次選定第一張國家旗卡 A（「英格蘭：」21px／「移民」25px），核對[目標099](docs/goals/099-first-nation-card-a-overlay.md)與[規格021](docs/spec/021-nation-card-red-text-draft.md)已限定實作及驗收，故不重做、不把此 A 外推到 Game Options。依復古遊戲規格閘門與 dosgolem 路由，在PRIVATE儲存庫先以 `e586ace` 推送[目標120](docs/goals/120-third-difficulty-card-output-evidence.md)後才執行原版。遊戲選項 A／B 字級仍待另行決定。
- 新增固定真視窗九筆前綴的第三張卡片三分支重播、只讀 Go 探針及獨立 Python 檢查器。原版滑鼠點擊 `(55,145)` 後，`NAMES.TXT:0xC22`／`LABELS.TXT:0x8B8` 的 `Conquistador`／`Moderate` 經原版 DOS 載入、來源 RAM 讀取、格式化印字與畫布事件呈現；墨跡205／116點，印前背景100／80種色盤索引。雙次冷啟動報告逐 byte 一致，同輸入無監看控制原版完整狀態與逐時點畫布相同；僅移鼠／未點選沒有第三卡印字。中間完整逐 byte 搬運仍標強推論，規格016維持 DRAFT，正式中文仍十七段。
- `tools/check_goal120_third.py --self-test` 正例及六類拒絕 PASS；真原版草稿 TSV 379筆驗證、11個既有翻譯驗證單元測試、`tools/worklist.py write/verify`、Python AST、Go `gofmt`／`go build` 和 `git diff --check` 通過。初次 `gofmt` 因研究映像 shell PATH 未含 Go 目錄失敗，改以映像內固定 `/usr/local/go/bin/gofmt` 後乾淨重跑；探針初版把副標來源候選起點高估一 byte，依直接讀取改為 `0x4DF9D` 並升收據版本，沒有以初版錯位資料寫入正式規格。這些是工具／觀測修正，不是遊戲產品缺陷。
- 實質成果 `0ff3f51` 已推送 PRIVATE `origin/main`；主機已登入 `gh` 回讀 [Issue #6](https://github.com/wicanr2/colonization_cht/issues/6#issuecomment-5814201801)、[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5814201547)與[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5814202326)的最新留言，三者保持 OPEN。原版、字型、完整報告與畫布只留唯讀來源／已忽略 `workplace/`；輸出及 `WORKLIST.md` 擁有者1000:1000，未見 root-owned 或誤建 `.md` 目錄，`colonization-research:20260920-r2` 無專案殘留容器，隔離 dosgolem `upstream` 推送位址仍為 `DISABLED`。下一閘門是第三張卡片逐欄 Ebitengine 預覽與游標／按鍵回退，未驗前不增加正式中文段數。

## 2026-09-24：目標121第三張難度卡可逆排版與滑鼠守門

- 使用者再次選第一張國家旗卡 A（「英格蘭：」21px／「移民」25px）；查明[目標099](docs/goals/099-first-nation-card-a-overlay.md)與規格021已在正式 Ebitengine 畫面限定驗收，不重複改動，也不把這個 A 外推到第三張難度卡或 Game Options。依復古遊戲規格閘門、dosgolem 原版與 `grill-me`／`grilling` 的可丟棄視覺對照方式，先以 `fe33392` 將[目標121](docs/goals/121-third-difficulty-card-layout-and-guards.md)推送 PRIVATE `origin/main`，才執行本輪研究。
- 用目標120固定雙重播原版印字收據、真 TSV、合法 DOS、同 SHA Cubic 11，獨立量測第三張卡 A 21／25px及 B 25／29px。沿用既有 `tools/card_preview.go`，真 Ebitengine 產生原文／兩版本機 PNG；`tools/verify_card_preview.py` 兩版逐像素 PASS，安全區外零變動且透明字模恢復不同的原版紋理。`tools/test_goal121_card_preview.py` 的正例與八類錯版／錯鍵／缺字／溢出／壞底圖等負例 PASS，缺合法原版可明示 `SKIP 77`。最初在 dosgolem Go 模組直接建 Ebitengine 預覽缺離線依賴，改用既有含 v2.9.9 的 `eob-remake-go` 映像及現成鎖版 module；`xvfb-run` 缺 `xauth`，改用同映像既有直接 Xvfb 啟動加 trap／有界執行。兩者是工具環境問題，修正後原命題重驗通過，未新建映像。
- 原版滑鼠三支輸入 `(55,132)`／`(55,135)`／`(55,151)` 各有兩次 dosgolem 冷啟動及無監看控制；只遮上行、跨兩行、只遮下行的合成 indexed／底層 canvas 像素差明確分開，按下前、按住、放開後及移開各有收據。`tools/check_goal121_card_guards.py --self-test` 驗證原版版本、事件與相位實檔，負例拒絕；印字中途的索引與底層不同步，故只提出穩定幀逐欄原文回退的 DRAFT 候選，沒有接正式 `live_menu.go`。規格016、研究紀錄、目前脈絡和唯一 Issue 工作清單已回填；譯文仍 draft、正式中文十七段，README 和正式截圖不改。第三卡 A／B 待使用者決定，Game Options A／B 仍是另一件事。
- 實質成果 `d3c8c46` 已推送 PRIVATE `origin/main`；主機 `gh` 留言並回讀 [Issue #6](https://github.com/wicanr2/colonization_cht/issues/6#issuecomment-5814868982)、[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5814869141)與[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5814868958)，三者保持 OPEN。`tools/worklist.py write/verify`、Python AST、兩版逐像素驗證、排版八類負例、原版三支雙重播／控制與 `git diff --check` 均 PASS。原版、TTF、畫布、字模及 PNG 只在唯讀來源／已忽略 `workplace/`；輸出與 `WORKLIST.md` 抽查 UID/GID 1000:1000，`workplace/` 無 root-owned 或誤建 `.md` 目錄，研究／Ebitengine／圖像映像無本專案容器殘留，隔離 dosgolem `upstream` 推送位址維持 `DISABLED`。本條遠端交接紀錄另以文件提交推送。

## 2026-09-24：目標122遊戲選項九欄狀態矩陣與部分欄位原型

- 已確認第一張國家旗卡 A（21／25px）早於目標099正式驗收，不重做、不外推到未定的第三難度卡及遊戲選項。開工時 Git 乾淨、作者 `wicanr2@gmail.com`、遠端 PRIVATE、Issue #7／#26 OPEN、隔離 dosgolem `9dd3672` 且 `upstream` 推送位址 `DISABLED`；先以 `1c0d0c3` 推送[目標122](docs/goals/122-game-options-nine-field-state-guard.md)。復古遊戲知識路由命中規格閘門、dosgolem 原版對拍與文件職責；遵守 DRAFT→READY 前不接正式前端。

- 在既有非 root、無網路、限資源 Docker 中，重用目標111／113／116～119的固定 dosgolem 雙冷啟動、無監看控制與原版實檔，生成13支路徑85個取樣狀態的九欄矩陣。第2列點擊1,325M保留六欄中文候選、第8列點擊保留七欄；其餘欄原文，純移鼠遮字逐欄回退，ESC離頁全窗失效。第一／第八列12個細相位皆標未知。沒有重跑或改動原版遊戲與執行器，也未把抽樣安全冒稱每幀安全。

- 沿用 `tools/card_preview.go` 與既有 Ebitengine v2.9.9 映像，用有界 Xvfb 為兩狀態各輸出原文控制、A／B 本機可丟棄 PNG。`tools/verify_card_preview.py` 四版逐像素 PASS；未選欄及安全區外零差異、透明文字處恢復原版多色底圖。`tools/test_goal122_options_field_guard.py` 正例及錯原版／錯輸入／壞畫面／雙重播／控制／錯安全矩形／游標與離頁回退、缺原版 `SKIP 77` 通過；Python AST、`tools/worklist.py write/verify`、`git diff --check` 均通過。首次執行所用檢查映像沒有 Pillow，改沿用既有 `rich2-py:latest`；初次指定的開局輸入與遊戲資料夾各少一層，查既有 probe 路徑後以正確唯讀來源乾淨重跑。這些是環境／命令路徑錯誤，不是產品缺陷。

- 已回填[規格027](docs/spec/027-game-options-window-draft.md)、`RESEARCH-LOG.md`、`CONTEXT.md`、唯一 `docs/worklist.json` 並重生 `WORKLIST.md`；規格仍 DRAFT、九欄原文、正式中文十七段。原版素材、字型、畫素與 PNG 只在合法唯讀來源／已忽略 `workplace/`。本輪輸出和 `WORKLIST.md` 為 UID/GID 1000:1000，`workplace/` 無 root-owned 或誤建 `.md` 目錄，三種本輪映像無執行中／已停止容器殘留。下一閘門是使用者另行選定此視窗 A／B 字級、再設計執行期每幀失效契約及 READY 同狀態驗收；本目標完成不等於全遊戲中文化完成。
- 實質成果提交 `5155cba` 已推送 PRIVATE `origin/main`；主機已登入 `gh` 留言並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5815378447)與[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5815378288)，兩者保持 OPEN。本條遠端交接紀錄另以文件提交推送。

## 2026-09-24：目標123退休確認框後續路徑

- 使用者再次選第一張國家旗卡 A（「英格蘭：」21px／「移民」25px）；目標099及規格021早已正式同狀態驗收，未重改旗卡，也未把 A 外推到第三難度卡或遊戲選項。復古遊戲路由命中規格閘門、dosgolem 原版對拍與文件職責；[目標123](docs/goals/123-retire-confirmation-and-help-route.md)先以 `199b4a2` 推送 PRIVATE `origin/main`，才新增原版玩家探針。
- 正常滑鼠 Yes／No 原版分支各雙次冷啟動及無監看控制：No 回海上畫面；Yes 到分數頁，Enter 到名人堂，再按 Enter 正常結束 DOS。初版探針因預設期待1,500M仍執行，把正常結束報為「提前停止」；增設預設關閉的 `-allow-early-exit` 記錄實際終止步數和畫面。關旗標重播目標111歷史 JSON 逐 byte 不變。此為探針分類修正，不是遊戲或中文前端缺陷。
- `tools/check_goal123_retire_route.py` 核對四分支原版檔案／輸入／雙重播／無監看控制與所有實際索引、畫布、色盤檔；`tools/test_goal123_retire_route.py` 正例、缺原版 SKIP 及錯版／錯事件／壞畫面／假終止等九類負例通過。Go 格式與編譯、Python AST、唯一工作清單重生與驗證、Git diff 檢查亦於本輪收尾核對。正式中文仍十七段，help 零則，規格026 DRAFT；新局／教學觸發要另尋正常玩家路徑，不以 Retire 假定返回新局。
- 原版與完整畫面收據只在合法唯讀來源及已忽略 `workplace/`；收據與 `WORKLIST.md` 擁有者均 UID/GID 1000:1000，`workplace/` 無 root-owned 或誤建 `.md` 目錄，研究映像無本專案殘留容器，隔離 dosgolem `upstream` 推送位址 `DISABLED`。實質成果 `fd3db4b` 已推送 PRIVATE `origin/main`；主機已登入 `gh` 留言並回讀 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5816432759) 與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5816433499)，兩者仍 OPEN。本條遠端交接紀錄另以文件提交推送。

## 2026-09-24：目標124真視窗 Left／Esc 輸入路徑

- 使用者選定第一張國家旗卡 A（「英格蘭：」21px、「移民」25px）；目標099早已實作驗收，故未重改。復古遊戲路由命中規格閘門、dosgolem 原版對拍及文件職責，先把[目標124](docs/goals/124-gameplay-keyboard-window-route.md)以 `3018096` 推送 PRIVATE `origin/main`，再實作前端五種具名鍵轉送。未修改原版或共用 dosgolem。
- 固定 Ebitengine v2.9.9／隔離 dosgolem，在規格024獨立 READY 擴充後接線：Esc、Left、Right、Up、Down 僅在聚焦按下邊緣送入 BIOS 佇列，Space 保留單字元路徑。Go 單元測試核對 BIOS 字組、非法事件及焦點／重複鍵，`go test -p 1 ./...` 與 `go build -p 1` 在有界 Xvfb／Docker 通過。首次沒設 `DISPLAY` 的 GLFW 初始化失敗是環境問題，修正後同一工具鏈乾淨重跑；最早真視窗探針等待預算不足在約887M步停下，增大有界等待後重新冷啟動完成，不把它算遊戲失敗。
- 真 Ebitengine 視窗與英格蘭 DOS 原版，冷啟動穿過滑鼠選單／介紹及字幕，實按海上 Left、實開 `GAME → Game Options` 再按 Esc。中文／英文控制之 CPU、完整 RAM、原版索引／色盤、時間和開檔相同；兩個只少一鍵的本機反向重播各改變終點原版畫面。失焦 Left 真視窗沒有延遲補送；目標095真姓名輸入舊收據以新前端重播，原版實檔逐 byte 與舊英文控制一致。`tools/check_goal124_keyboard.py` PASS，`tools/test_goal124_keyboard.py` 缺原版 `SKIP 77` 與八類負例 PASS。規格024只把已驗輸入通道升為限定 CONFORMED，正式中文十七段、help 零則；第三難度卡和 Game Options 字級待各自決定。
- 原版截圖、RAM、輸入及字模僅保留已忽略 `workplace/`。`docs/worklist.json` 重生／驗證 PASS，Python AST、Shell 語法及最終有界 Xvfb 下的 `go test -p 1 ./...` PASS；前兩次補跑分別漏掛隔離 dosgolem、未指定容器可寫 Go 快取，修正掛載與 `GOCACHE=/tmp/goal124-gocache` 後乾淨重跑，屬容器設定問題。原版收據及工作清單 UID/GID 均1000:1000，`workplace/` 沒有 root-owned 或誤建 `.md` 目錄；本專案研究／Ebitengine 映像無殘留執行中或已停止容器，其他專案容器未碰。隔離 dosgolem `upstream` 推送位址仍為 `DISABLED`，Git 未追蹤原版素材。本段不以 GUI 輸入完成冒稱全文中文化或完整可玩。
- 2026-09-25 收尾：實質成果 `ab93ee9` 已推送私有 `origin/main`；主機 `gh auth status` 成功，遠端仍 PRIVATE。[Issue #14](https://github.com/wicanr2/colonization_cht/issues/14#issuecomment-5817656771)及[Issue #29](https://github.com/wicanr2/colonization_cht/issues/29#issuecomment-5817657237)均已留言並回讀，保持 OPEN。此遠端交接紀錄另以文件提交推送。

## 2026-09-25：目標125教學選項跨次啟動

- 本輪先查復古遊戲知識路由，命中規格閘門、dosgolem 原版收據與文件職責；完整讀逆向工程技能與所需參考。第一張國家旗卡 A（21／25px）已由目標099正式驗收，未重做。先以 `d956d89` 將[目標125](docs/goals/125-tutorial-hints-persistence-and-help-entry.md)與 `CONTEXT.md` 入口推送 PRIVATE `origin/main`，再做工程。主機 `gh auth status` 通過，Issue #7／#27 既存且保持開啟。
- 原計畫複製原版目錄，但隔離 dosgolem 的預設寫入僅記意圖、不落地；依其 `docs/spec/009-scratch-writes.md` 改用三支獨立 `DOS.Scratch`，原版 `Root` 始終唯讀，並在 goal 追加訂正，不以原計畫產生假陰性。探針只新增預設關閉的 `-scratch` 及有界正常 DOS 終止收據；未修改共用 dosgolem 或原版程式。固定玩家事件、首輪及重啟腳本均留在 `tools/`。
- 未切換／切換一次／切換兩次各跑首輪 A/B 冷啟動及無監看控制，再把各自暫存層精確複製到第二輪三支 A/B/控制冷啟動。首輪同焦點教學圖示47／149／47，全部由正常 `Retire → Yes → 分數 → 名人堂` 退出；三支暫存檔相同。第二輪九份完整原版狀態合流、教學圖示均47，固定觀測未見 help。獨立檢查器讀實際索引／畫布／色盤及暫存檔，正例、缺原版 SKIP77 與篡改負例均通過。初次獨立檢查器有一字元事件 SHA 筆誤，核對真檔後修正並重跑；重啟腳本初次直接執行遭權限拒絕，改用 `/bin/sh` 成功。兩者均是檢查／呼叫問題，不是原版遊戲缺陷。
- 不開 `-scratch` 重跑舊目標123名人堂路徑，JSON 與舊收據 SHA `902d557aaf7f86d4fb913d4891e4c7e584f10963e8b0217e2afc8401bde20efa` 逐 byte 相同。結論只限這條跨次新局路徑，不把未見 help 擴大為全遊戲沒提示，也不宣稱第二次啟動讀了哪個暫存檔；規格026仍 DRAFT，正式中文十七段、help 零則。詳細檔案雜湊、版本與收據見 `RESEARCH-LOG.md`；原版與畫面只留已忽略 `workplace/reports/goal125-help/`。
- 收尾重跑檢查器正例、缺原版 SKIP77 與十類篡改負例均通過；唯一 `docs/worklist.json` 已重生並驗證，Shell 語法及 Python 編譯通過，`git diff --check` 無誤。收據、暫存層及 `WORKLIST.md` 為 UID/GID 1000:1000；`workplace/` 沒有 root 擁有檔案或誤建 `.md` 目錄。`docker ps -a` 無本專案殘留容器，其他專案容器未碰；隔離 dosgolem `upstream` 推送位址仍 `DISABLED`，Git 未新增原版程式、存檔或原始畫面。
- 實質成果 `cbe504c` 已推送 PRIVATE `origin/main`；主機 `gh auth status` 通過、遠端仍 PRIVATE。[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5818529271)與 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5818534280)已留言並全文回讀，兩者仍 OPEN。此遠端交接紀錄另以文件提交推送。

## 2026-09-25：目標126退休確認框三欄中文原型

- 上輪目標125的跨次玩家實驗屬實質進度，但固定 `Retire` 路徑沒有帶出 help，故這輪轉向已在正常玩家流程可見的三筆退休確認框譯稿。查復古遊戲知識路由，命中規格閘門、dosgolem 原版收據及文件職責；視覺版式另使用 `grill-me`／`grilling` 技能，先做對照再讓使用者選。主機 Git 身分 `wicanr2@gmail.com`、工作樹乾淨、遠端 PRIVATE、Issue #7／#11／#12 均 OPEN；先把[目標126](docs/goals/126-retire-confirmation-three-field-overlay.md)與 `CONTEXT.md` 入口以 `723a6a7` 推送私有 `origin/main`，再動工程。
- 探針新增預設關閉的 `-retire-audit`，從 `GAME.TXT` 三個固定檔案位移取得 DOS 讀入，於三個原版印字首字讀取前各存64,000-byte底圖；雙冷啟動和無監看控制同狀態。問句／Yes／No 三欄改色441／64／54點，三色、bbox及地址空間見 `RESEARCH-LOG.md` 與[規格028](docs/spec/028-retire-confirmation-overlay-draft.md)。新旗標關閉時同路徑舊報告逐 byte 與 SHA `182e815897b6f6f1ff2dd4f6bcad3ee7dcf0394dc3a59bdb99b5b400ef7f952a` 相同；原版從未改寫。
- 以固定 Cubic 11、唯一 TSV 和三張各自印前底圖產生本機 A（34px共同置中）及 B（38px問句與34px按鈕保留原版左起點）原型，鎖版 Ebitengine v2.9.9／Xvfb 抓原文控制與兩張中文圖；獨立逐像素核對兩版安全區外零差異、透明處恢復底圖及前景／陰影 PASS。正反例涵蓋缺原版 SKIP77、錯版／輸入／字型／譯稿／雙重播／控制 RAM／實檔變造。第一次測試把 Pillow advance bbox 當實際 Alpha 墨跡，量測後收緊為逐欄實測邊界；首次 `go` 不在映像 PATH、`xvfb-run` 缺 `xauth`，改用鎖版 `/usr/local/go/bin/go` 及有界、trap 管理的 Xvfb 後同工具鏈成功，均屬驗證環境／腳本問題，不是遊戲缺陷。
- A/B 只供使用者選原版忠實度：A較整齊，B問句高與各行左起點更貼近原版，建議 B；本輪不替使用者決定。`@RETIRE` 中間逐 byte 搬運、真 Ebitengine 玩家視窗動態回退與同輸入英文控制尚缺，[規格028](docs/spec/028-retire-confirmation-overlay-draft.md)仍 DRAFT，三欄仍英文；正式中文十七段、help 零則。原版索引、含原版像素 PNG、字模與報告只在已忽略 `workplace/reports/goal126-retire/`，不推送。
- 本輪收尾：`docs/worklist.json` 重生／驗證、Python AST、Go 格式差分、Git diff 檢查均通過；工作清單、原版收據和兩張原型圖均為 UID/GID 1000:1000，`workplace/` 沒有 root-owned 或誤建 `.md` 目錄。`docker ps -a` 無本專案殘留容器；其他專案容器未碰。隔離 dosgolem `upstream` 推送位址仍 `DISABLED`，Git 未新增原版 EXE／DAT／SAV 或本輪原始畫面。
- 實質證據與原型程式 `771d659` 已推送 PRIVATE `origin/main`；主機 `gh auth status` 成功，遠端仍 PRIVATE。[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5819154703)、[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5819158909)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5819162916) 已留言並全文回讀，三者均 OPEN。此遠端交接紀錄另以文件提交推送；A/B 問題待使用者看本機同狀態原型圖選擇，不在 Issue 或文件中代選。

## 2026-09-25：目標127退休確認框資料流補證

- 使用者再次選定第一張國家旗卡 A（「英格蘭：」21px、「移民」25px）；核對目標099與規格021，該兩欄早已正式同狀態驗收，故本輪不重做、不改截圖、不外推至其他版面。復古遊戲知識路由命中規格閘門、dosgolem 原版收據及文件職責；讀取相符入口與逆向技能後，先以 `c491976` 將[目標127](docs/goals/127-retire-source-to-print-dataflow.md)及 `CONTEXT.md` 入口推送 PRIVATE `origin/main`，再動探針。開工時工作樹乾淨、作者 `wicanr2@gmail.com`、遠端 PRIVATE；主機 `gh auth status` 通過，Issue #7 OPEN；隔離 dosgolem `9dd36726`、`upstream` 推送位址 `DISABLED`。
- 探針只新增預設關閉、互斥的 `-retire-flow-audit`／`-retire-resident-audit`，原版唯讀。第一次近端監看以過寬事件範圍碰到上限，收據未輸出；收斂到來源解析／格式化／真印字指令後，用同一原版與玩家輸入乾淨重跑，不把監看器限制當產品失敗。新檢查器初版把色盤 SHA 誤抄為另一時點，核對本次實檔與樣本後訂正並同命令重跑通過。兩者都保留為工具／驗證腳本問題。
- 兩種互斥監看各雙冷啟動報告逐 byte 相同，無監看控制的 CPU、完整 RAM、索引／色盤、虛擬時間與開檔相同。`GAME.TXT` 三筆32 byte經原版解析器實讀；解析區31／32筆變更寫入、常駐字串35筆寫入、31個真印字字元31筆近端讀取與30筆變更寫入已驗。其餘同值 byte 的寫入無回呼，完整來源歸屬保持強推論；精確位址、工具版本、SHA 與界線見[規格028](docs/spec/028-retire-confirmation-overlay-draft.md)及 `RESEARCH-LOG.md`。獨立正例、缺原版 `SKIP 77`、錯版／輸入／雙重播／監看上限／缺讀寫／控制 RAM／畫面變造等負例均通過。新旗標全關時，同輸入舊 JSON 仍為歷史 SHA `182e815897b6f6f1ff2dd4f6bcad3ee7dcf0394dc3a59bdb99b5b400ef7f952a`，逐 byte 相同。
- 規格028仍 DRAFT，退休框 A/B 版式、正式真 Ebitengine 玩家視窗及逐欄回退尚未定案；三欄仍英文，正式中文十七段、help 零則。`docs/worklist.json` 的 Issue #11 工作項已回填並重生／驗證 `WORKLIST.md`；Python 編譯及探針建置通過。原版資料、字型、像素與完整 JSON 只在已忽略 `workplace/`。本輪收據及 `WORKLIST.md` UID/GID 均1000:1000，`workplace/` 無 root-owned 或誤建 `.md` 目錄；`docker ps -a` 無本專案殘留執行中或已停止容器，其他專案容器未碰。私有推送與 Issue 回讀另在本節後續記錄。
- 收尾：本輪成果 `5e247d2` 已推送 PRIVATE `origin/main`。主機登入 `gh` 後已在既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7#issuecomment-5820216079)、[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5820221386)及[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5820225770) 留言，逐則全文回讀成功且三者保持 OPEN；遠端仍 PRIVATE。本交接補記另行提交推送，不擴張使用者第一張旗卡 A 決定到其他畫面。

## 2026-09-25：目標128兩處 A 字級與 `@BUILD1` 離頁候選

- 依使用者兩項獨立答覆，首張開場字幕選38px A、遊戲選項九欄選34／25／28／28／25／28／28／27／28px A，各排除 B；第一張旗卡 A 已由目標099驗收，不重做。復古遊戲知識路由命中規格閘門、dosgolem 原版收據及文件職責，已讀所需入口與逆向技能；先以 `9ebff1d` 推送[目標128](docs/goals/128-a-layout-decisions-and-build1-runtime-gate.md)和目前脈絡到 PRIVATE `origin/main`，再動工程。主機 `gh auth status` 通過，遠端 PRIVATE、Git 作者 `wicanr2@gmail.com`；隔離 dosgolem `upstream` 推送位址 `DISABLED`。
- 先前 `@BUILD1` A 原型綁定舊版**整份**主譯稿雜湊，舊獨立檢查器因語料後來增加而拒絕；確認本行譯文未變後，以現行 TSV 與同一原版印前底圖重烘38px A，不放寬檢查。原有目標106字幕印前、雙重播及目標107後續畫面檢查器再次 PASS。遊戲選項 A 資料亦用現行 TSV 重烘，九個 layer 及原版索引／色盤與舊 A 逐 byte 相同；原有 Ebitengine 中英文圖按新資料重跑逐像素 PASS。所有預覽、原版像素、字型及完整 JSON 只留已忽略 `workplace/reports/goal128-a-layout/`。
- 新增 `tools/check_goal128_a_layout.py` 與負例測試：逐欄固定 A 字級、真譯文、來源鍵、ASCII 快捷鍵標記、字模／暗影安全區及 Ebitengine 畫素收據；`@BUILD1` 另沿正常玩家原版雙重播／無監看控制，85M拒絕、90M／175M／195M候選、200M換頁拒絕。錯來源／版本／畫面／色盤、B 字級、越界、熱鍵消失和缺原版 `SKIP 77` 均通過；本機總結收據 SHA-256 `cf336f597a189f6fbbf68d2cdf46c5b4157aba3a8bc1affb7fbd7f280d580f21`。這是**固定取樣的 DRAFT 守門候選**，不是逐幀正式畫面；下一步仍需事件生命週期、當幀可逆補片、真視窗中文／英文同狀態與缺譯回退。規格026／027維持 DRAFT，字幕與九欄仍英文，正式中文十七段、help 零則。
- 收尾：成果 `2285e8a` 已推送 PRIVATE `origin/main`。[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5820693094)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5820693309)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5820692936)、[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27#issuecomment-5820694356) 已留言、全文回讀且均保持 OPEN。`docs/worklist.json` 重生／驗證、Python 編譯與 `git diff --check` 通過；本輪收據與 `WORKLIST.md` 均為 UID/GID 1000:1000，`workplace/` 無 root-owned 或誤建 `.md` 目錄。`docker ps -a` 無本專案殘留，其他專案容器未碰；隔離 dosgolem `upstream` 推送位址仍 `DISABLED`，原版程式、資料、字型及本輪 PNG 沒有入 Git。本遠端交接補記另行提交推送。

## 2026-09-25：目標129首張開場字幕逐幀相位

- 使用者再次確認遊戲選項九欄 A（34／25／28／28／25／28／28／27／28px）；查核目標128與規格027，已記錄並驗過本機版面，不重做或把原型算正式中文。知識路由本輪命中規格閘門、dosgolem 原版對拍、中文顯示語意隔離及文件職責；已讀相符入口與逆向技能。先以 `fd66121` 將[目標129](docs/goals/129-build1-runtime-frame-lifecycle.md)及目前脈絡推送 PRIVATE `origin/main`，再改探針。主機 `gh auth status` 成功，Issue #11／#12 均 OPEN；隔離 dosgolem 提交 `9dd36726`、`upstream` 推送位址 `DISABLED`。
- 原版探針新增預設關閉的 `-caption-frame-audit`；合法 DOS `COLONIZE` 唯讀，工具與輸出在無網路、限資源、非 root 的一次性 Docker 內。英格蘭正常玩家 Enter 路徑雙次冷啟動報告逐 byte 相同，無監看控制34個取樣的 CPU、完整 RAM、畫布／索引／色盤、時間與開檔一致；61字元印字、1,040點畫布改色及647個字幕畫格、第195,525,000步離頁失效見[規格026](docs/spec/026-build-intro-and-tutorial-prefetch-draft.md)與 `RESEARCH-LOG.md`。獨立檢查器 PASS、13項負例及缺原版 `SKIP 77`通過；探針預設關閉與目標105舊收據逐 byte 相同。
- 本輪只完成 DRAFT 原版事件／逐幀相位證據；正式 Ebitengine 事件權杖、可逆多色底圖、游標回退及同輸入中文／英文驗收仍缺，規格026不升 READY，字幕與遊戲選項九欄仍英文，正式中文十七段、help 零則。原版畫素、完整報告與可執行探針僅留已忽略 `workplace/reports/goal129-caption-frame/`；`docs/worklist.json` 的既有 Issue #26 項已回填，不新增同義工作項。私有推送、Issue 回讀及 Docker 清理另於收尾補記。
- 收尾：成果 `7c70a0c` 已推送 PRIVATE `origin/main`；[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5821118061)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5821118059)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5821119539) 已留言且全文回讀，均維持 OPEN。工作清單重生／驗證、Python AST、Go 格式、獨立正反例與 `git diff --check` 通過；本輪輸出及 `WORKLIST.md` 均為 UID/GID 1000:1000，`workplace/` 沒有 root-owned 或誤建 `.md` 目錄。`docker ps -a` 無本專案殘留容器，其他專案資源未碰；隔離 dosgolem `upstream` 推送位址仍 `DISABLED`。原版 EXE／TXT、字型、原始畫素、完整報告與可執行探針未加入 Git；本遠端交接補記另行提交。

## 2026-09-25：目標130首張開場字幕正式 A 版

- 使用者已選 `Game Options` 九欄 A 字級；目標128與規格027已記錄，本輪只重申、不把九欄原型當正式顯示。依知識路由命中復古遊戲規格閘門、dosgolem原版證據、中文顯示語意隔離與文件職責，已讀相符入口及逆向技能。先把[目標130](docs/goals/130-build1-ready-and-ebitengine-overlay.md)與現況入口提交 `98210c7`、推送 PRIVATE `origin/main`，再研究與實作；Git作者 `wicanr2@gmail.com`、主機 `gh auth status` 與遠端 PRIVATE 已核對。
- 原版探針 `-caption-screen-audit` 預設關閉，在隔離 dosgolem 與唯讀原版以兩次冷啟動、無監看控制確認61字元／122筆來源運算元、1,040點底圖改色與真 VGA慢六幀同步；雙重播報告 SHA-256 `f0bc1a1747c5086bd1598ec39a6eca4490b44bb6d4b6dcc17e6d6a6bacd647dc`，18項篡改及缺原版 `SKIP 77` 通過。初版把底圖／VGA差異誤稱游標，查 dosgolem `Indexed()` 後更正並保留勘誤。由此只把英格蘭首張字幕升[規格029](docs/spec/029-build1-caption-window-ready.md) READY，其他字幕/help所在規格026仍 DRAFT。
- READY後才在正式 Ebitengine前端加預設關閉的 `-build1-a`，只用 TSV、固定字型本機字模及原版當次輸出事件；字型預留寬451px與實際墨跡430px的差異經目標106對照查明，以墨跡裁切維持使用者選的 A／38px。既有映像 `xvfb-run` 缺 `xauth`，改用同映像有 trap、有界的 `Xvfb`，不是產品缺陷。真視窗錄製路徑其實在78.9M先印字幕、85.8M離頁，和獨立探針的88.7M屬不同輸入路徑；前述「同路徑重印」猜測已訂正，程式只在新完整印字事件才可重新建立權杖。
- 中／英文控制於82M字幕中、86M離頁、120M後續的原版完整狀態、索引與色盤同狀態；82M只改安全區，前七個真 VGA等待幀保持英文。缺字模、缺譯、重複鍵及一筆明示合成游標遮擋的正式真視窗負例均回退原文；最後版正常PNG逐 byte不變，十七欄前727幀與29個事件不退步。獨立檢查器正例、七項篡改拒絕、缺原版 `SKIP 77`通過，本機摘要 SHA-256 `1344a244196abf1fd304a3a57111c628876dfb71bc33f6563a21e154e6e061ce`。獨立 Pillow重建僅858個字模抗鋸齒邊緣因跨繪圖庫捨入差至多2色階，安全區外、空白、實心墨跡精確相同。規格029僅此欄限定 CONFORMED；其餘九張字幕、遊戲選項九欄與help仍未正式中文。
- 原版資料、固定 TTF、PNG、RAM、完整 JSON與執行檔均只在已忽略 `workplace/`，不更新含原版像素的正式截圖或對外封包。`docs/worklist.json`、工作歷程及研究紀錄已回填，`tools/worklist.py write/verify` 與八份 Python語法檢查通過；Ebitengine `go test` 首次因未給 `DISPLAY`而非產品失敗，於同一映像加有界 `Xvfb` 後乾淨重跑 PASS。輸出抽查UID/GID 1000:1000、`workplace/` 無 root-owned或誤建 `.md`目錄，三個本專案工具映像無殘留容器；隔離 dosgolem仍是`9dd36726`、`upstream`禁推`DISABLED`。私有推送及 Issue回讀另於本節收尾補記。
- 收尾：成果 `a8c7281` 已推送 PRIVATE `origin/main`；主機 `gh auth status` 成功、遠端仍 PRIVATE。[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5822243001)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5822243317)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5822242415) 的限定完成與未完成邊界已留言、全文回讀且三者皆維持 OPEN。主提交作者為 `wicanr2@gmail.com`，工作樹於補記前乾淨；此遠端交接補記另行提交並推送，不附原版素材。

## 2026-09-25：目標130實際 Ebitengine 視窗截圖補驗

- 主提交與三筆 Issue 留言回讀後，依正式真視窗畫面閘門再用有界 Xvfb、真 `xdotool` 鍵鼠從冷啟動實際開啟 Ebitengine 視窗，84M現場擷取 `workplace/reports/goal130-build1/gui-real.caption.png`。25筆現場輸入無拒絕，末畫格中文字幕有啟用；1280×800現場 PNG與82M已驗重播中文字幕PNG逐像素一致。兩支不是相同輸入時點，僅核對可見畫面，不冒稱跨組CPU同狀態。真GUI檢查已納入獨立驗證器並重跑正例、七項篡改測試 PASS，本機新摘要 SHA-256 `1344a244196abf1fd304a3a57111c628876dfb71bc33f6563a21e154e6e061ce`。圖片含原版像素，留本機不推送；補驗工具與文件另以後續私有提交交接。

## 2026-09-25：目標131選項標題逐幀審計（進行中）

- 使用者已再次確認遊戲選項九欄 A（標題34px、八列25／28／28／25／28／28／27／28px），排除 B；目標128已記錄此決定，不重做字級原型。知識路由本輪命中復古遊戲規格閘門、dosgolem對拍與文件職責；已讀入口、必要參考及逆向技能。主機 `gh auth status`成功，既有 Issue #11／#12／#26仍 OPEN，目標131與 `CONTEXT.md`入口先以 `4f26284` 推送 PRIVATE `origin/main`。
- 新增預設關閉的 `-options-title-screen-audit`與可重播腳本、獨立檢查器。在隔離 dosgolem、唯讀原版、有界非 root Docker內完成雙冷啟動及無監看控制；真 VGA比底層畫布晚一幀，ESC後失效。收據 SHA-256 `1889868e1abe56533c0f97f1219353d8683bb378b244a6a7bf3a96d6d995c83e`，正例、四項篡改拒絕、缺原版 `SKIP 77`通過。原版詳證見 `RESEARCH-LOG.md`與[規格027](docs/spec/027-game-options-window-draft.md)。本輪沒有 READY、Ebitengine正式中文、截圖或新翻譯筆數；九欄仍英文，目標131保持進行中。
- 收尾：證據提交 `4daf5a0` 已推送 PRIVATE `origin/main`；[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5822630749)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5822631170)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5822630923) 的進度、DRAFT邊界與未完閘門均已留言、全文回讀，三者維持 OPEN。工作清單狀態未變，`tools/worklist.py verify`通過；Go編譯／格式、Python語法、獨立正反例與 `git diff --check`通過。本輪原版畫素、完整收據與可執行探針僅在已忽略 `workplace/`，輸出 UID/GID為1000:1000；`docker ps -a` 無本專案殘留，其他專案容器未動。隔離副本禁推設定與整個 `workplace/` 權限異常再於最後工作樹稽核確認。

## 2026-09-25：目標132遊戲選項標題 A 限定 CONFORMED

- 接手上一輪未提交的目標132：原版標題當次事件探針、規格030限定 READY、正式前端 `-game-options-title-a`、錄製輸入重播中英對拍、ESC／游標／載入回退負例均已在本機完成，但真 GUI 現場兩次未達標題。原因是 `tools/probe_goal132_gui.sh` 漏送錄製路徑1225M的 Left、選單點擊提早約20M步，且外層時限於1107M中止。修正相位並給足時限後，在有界 Xvfb 以真鍵鼠從冷啟動走到標題，1280M 現場 PNG 與重播逐像素一致；失敗日誌封存於 `workplace/reports/goal132-options-title-event/gui-attempts/`。
- 檢查器新增 `check_gui`，測試新增現場截圖篡改負例；正例、六項負例、缺原版 `SKIP 77` 在 `rich2-py:latest` 容器 PASS。`gofmt`、shell 與 Python 語法、`git diff --check`、`tools/worklist.py write/verify` 通過。window-src 內 `adapter.go`／`window.go`／`window_test.go` 與 `tools/live_menu.go`／`window_prototype.go`／`window_prototype_test.go` 逐 byte 相同，確認受驗二進位來自提交原始碼。
- 規格030升限定 CONFORMED；目標131、132標完成；規格027補標題指標、其餘八列仍 DRAFT；README 現況由十七段更正為十九段（含目標130字幕與本欄，均需明示旗標）；worklist Issue #11／#12／#14／#26 備註回填。
- 稽核：本輪容器皆 `--rm`，`docker ps -a` 無本專案殘留，其他專案容器未動；原版 zip／rar／解包目錄仍為忽略狀態；隔離 dosgolem 仍為 `9dd36726`、`upstream` 推送 `DISABLED`。repo 根目錄有一個 2026-09-24 22:44 由 root 建立的空目錄 `original/`，推測是先前 docker 掛載來源不存在時由 dockerd 代建；本輪未刪，待使用者處理。原版像素、截圖、RAM 與完整收據只在忽略的 `workplace/`。
- 收尾：成果 `5326216` 已推送 PRIVATE `origin/main`；主機 `gh auth status` 成功、遠端仍 PRIVATE。[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5825680739)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5825680912)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5825681077) 已留言並回讀，三者維持 OPEN。

## 2026-09-25：目標133遊戲選項八列證據與規格031限定 READY

- 使用者決定八列快捷鍵：先問位置再問顏色，定為字母前置、半形括號、同色（例：「(I) 顯示原住民行動」）。已記入 CONTEXT、規格027、目標133 與 TSV 備註；`prepare_goal113_options_preview.py` 的格式檢查同步改為新格式。
- 改 TSV 後確認只有字幕與標題兩個字模綁整份 TSV，重烘後 Alpha 不變；兩個既有回歸點重播與目標132收據逐項相同。
- 探針首跑兩次失敗：缺 `-post-caption-audit`、逐列點擊輸入超過原有 12 筆上限（只在新模式放寬到 40）。分析器首版按單字分組、又誤把被快速重印取代的中間事件當錯，均已修正並寫成規則：只對事件後穩定畫布重建底圖。
- 新增規格031（限定 READY）與目標134；README 未改（正式中文數不變）。本輪容器皆 `--rm`，無殘留；隔離 dosgolem 仍 `9dd36726`、`upstream` 推送 `DISABLED`。原版像素、畫布、RAM 與截圖只在 `workplace/`。

## 2026-09-25：目標134遊戲選項八列 CONFORMED

- 烘字模工具加入八列（字母前置格式、A 字級、已量尺寸）；前端加入 `-game-options-rows-a`，標題與八列可同幀並存。
- 真 GUI 共跑三次才通過，前兩次都保留在 `workplace/reports/goal134-options-rows/gui-attempts/` 與 `attempts-*`：（1）腳本點擊後立刻移開游標，模擬慢於牆鐘，移動與按下同批送達而點到視窗外、關閉選項；改為等步數前進再移開。（2）閘門把重印中途 `0CAE:00A8` 畫反白底圖當成錯誤寫入者，另游標壓列時同步逾時；以快速點擊探針補證據後修正閘門與規格031，最終版重跑全部重播、負例與 GUI。
- 勘誤：目標133 曾記「逐列點擊 24 次整組事件、第5列按下未重印原因未知」。實為分析器以讀字間隔分組，把一次中途停頓的重印切散；改以讀滿 268 次分組後為 25 次，第5列按下有重印。規格031、研究紀錄已改為現況；Issue 留言另行更正。
- 驗證：最終前端 `gofmt`／`go vet` 無輸出，檢查器 PASS，舊欄位回歸另見下條。本輪容器皆 `--rm`，無殘留；隔離 dosgolem 禁推設定不變。原版像素、截圖與收據只在 `workplace/`。
- 最終前端舊欄位回歸：標題 1280M 與字幕 82M 的 PNG、完整 RAM、索引、狀態、套用畫格數（54／151）與目標132 收據相同；`go test`（有界 Xvfb）、`gofmt`、Python 與 shell 語法檢查通過。
- 收尾：`bfc31c6` 已推送 PRIVATE `origin/main`；[Issue #11](https://github.com/wicanr2/colonization_cht/issues/11#issuecomment-5826938744)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12#issuecomment-5826938906)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26#issuecomment-5826939123) 已留言（含目標133 事件計數更正）並回讀，三者維持 OPEN。

## 2026-09-25：未完成工作登記為 Issue

- 對照 GitHub Issue 與 CONTEXT 待辦，新建 [#31](https://github.com/wicanr2/colonization_cht/issues/31)～[#37](https://github.com/wicanr2/colonization_cht/issues/37)：遊戲選項後續驗證、退休確認框（待選版式）、第三張難度卡（待選 A／B）、其餘三張旗卡、其餘九張開場字幕、首則 help、海上主畫面介面；並加入 `docs/worklist.json`，`tools/worklist.py write/verify` 通過。
- 使用者決定（2026-09-25）：#29 姓名欄維持原名、#30 長文貼近原版、#32 退休框 A、#33／#34 卡片 A；已寫入規格016／022／023／025／028、CONTEXT 與 worklist（worklist 統一為緊湊格式）。#29 依規格023 完成關閉。

## 2026-09-25：目標135英格蘭介紹兩頁 CONFORMED（#30）

- 目標102 預覽工具拆出 `layout()`，以舊 `layout.json` 逐 byte 相同作回歸；新增三層字模烘製工具與前端 `-england-intro-a`。
- 以探針畫布與真 VGA 比對確認游標只在 VGA，改用「游標畫在中文之上」合成，避免游標停在面板內時整頁退回英文。
- 首次真 GUI 截圖發現年份被拆行，補換行規則後重烘並重跑 A 頁重播與 GUI；首次收據封存於 `attempts-wrap/`。
- 負例批次第一次在容器 `wait` 後未執行，單獨重跑兩個負例後完成。
- 新前端回歸：標題 1280M、字幕 82M、遊戲選項八列 1280M 的 PNG、完整 RAM、狀態與套用畫格數（54／151／54）和既有收據相同；`go vet`／`go test`（有界 Xvfb）、Python 與 shell 語法檢查通過；容器皆 `--rm`。

## 2026-09-25：目標136其餘三國介紹頁 CONFORMED，#30 完成

- 前端擴充四國八頁（`-nation-intro-a`），三國字模以同版式烘製，行數與規格025 一致。
- 真 GUI 三國各跑三次才到位：第一次移動與按下同畫格未改選國家；第二次停在姓名畫面；第三次補「停留後按住」與姓名 Enter 後通過。前兩次收據封存於 `gui-attempts/1`、`gui-attempts/2`；中途停止的是本輪自建容器。
- 驗證：三國檢查器 PASS；全面回歸（英格蘭三點、標題、字幕、八列）逐項相同；`go vet`／`go test`、缺原版 `SKIP 77` 通過；容器皆 `--rm`，無殘留。

## 2026-09-25：目標137遊戲選項後續驗證，#31 完成

- 快捷鍵、三國、讀存檔三項以真 GUI 與中英重播驗收通過；正式前端只新增 `-scratch`，閘門邏輯不變。
- 真 GUI 重跑原因（都是操作時序）：並行時 30 分鐘等待上限不足（改兩小時）、主選單需停留後按住、主選單出現步數不固定（改相對等待）、讀檔訊息框需關閉。另有一次產生腳本時切片為空、`replace('')` 把內容插進每個字元之間，已停止該自建容器並以精確替換重建。
- 全面回歸（標題、字幕、八列、英格蘭介紹三點）以目標137前端重播，結果與既有收據逐項相同；`go vet`／`go test` 另行補跑通過。回歸容器以外層 timeout 結束：`wait` 同時等待背景 Xvfb 而不會返回（目標135、136 的回歸容器同樣如此，當時也都另補跑單元測試），結果檔已完整；此後改為只等待指定 PID。

## 2026-09-25：目標138退休確認框 CONFORMED，#32 完成

- 以九欄事件探針取得退休框事件結構與底圖白名單；烘字模工具沿用目標126 A 版字模；前端新增 `-retire-a`。
- 第一次真 GUI 發現游標常式暫寫造成撤銷，加入游標例外後重跑通過；另有診斷用重播把撤銷原因加上寫入者 `CS:IP` 與座標，保留在正式程式中方便日後追查。
- 全面回歸（標題、字幕、八列、英格蘭介紹三點）與既有收據逐項相同；`go vet`／`go test` 在同一容器內通過（改為只等待指定 PID 後不再卡在 Xvfb）；容器皆 `--rm`。

## 2026-09-25：目標139第三張難度卡 CONFORMED，#33 完成

- 前端在既有 `difficultyLine` 清單以 `-third-card-a` 追加兩欄，加入色號 14／0 白名單、陰影寬度與前景色；烘字工具加 `--third-card`，字模烘到獨立目錄，不動前兩張卡字模集。
- 第一次檢查器直接拿中文與英文控制比畫面，因同頁其他正式欄位也是中文而判為越界；改為加一組同輸入、不開旗標的中文基準比畫面，英文控制只比原版狀態。另把「游標只壓上欄時下欄仍中文」的預期改為整卡守門（兩欄一起回原文），與前兩張卡設計一致。
- 驗證：真 GUI、四點中英重播、三項負例、缺原版 SKIP 77；`go vet`／`go test`（Xvfb）通過；全面回歸六點與目標138收據逐項相同。window-src 與提交原始碼逐 byte 相同。容器皆 `--rm`，無殘留。

## 2026-09-25：目標140其餘三張旗卡 CONFORMED，#34 完成

- 新探針以目標136真 GUI 輸入觀測三國旗卡印字，雙冷啟動與控制一致；確認前景色號即 `NAMES.TXT` 行尾值，西、荷位置為英、法下移 91 像素。
- 前端把旗卡前景色改成逐欄 `cardColor`，新增 `-nation-cards-rest-a` 六欄；片段 TSV 與驗證器擴為八筆，烘字工具加 `--rest`。
- 第一次重播有三組英文控制因與探針收據同名被跳過（腳本以「輸出不存在」為前置條件，背景行程失敗未中止整體）；探針收據移入 `probe/` 並改探針腳本輸出路徑，法國控制手動補跑、西荷控制以新增的 `COLONIZATION_GOAL140_ONLY` 補跑，參數與腳本相同。
- 驗證：真 GUI、六點中英重播、三項負例、缺原版 SKIP 77、`go vet`／`go test` 通過；全面回歸六點與目標138收據相同。window-src 與提交原始碼逐 byte 相同。容器皆 `--rm`。
- 相容性：`tools/verify_goal103_font_rebuild.py` 同時釘住主譯稿（早已是歷史版 `9c9efe39…`）與旗卡片段 TSV（`d4cf454a…`）；片段 TSV 擴為八筆後，兩者都只能對目標103當時的版本（以 `git show` 取出）重現，不代表現行檔案錯誤。`bake_nation_card_a_from_font.bake()` 以 `getattr` 讀 `rest`，舊測試呼叫方式不變。

## 2026-09-25：目標141開場字幕 @BUILD2～10 CONFORMED，#35 完成

- 新探針沿 GUI 錄製路徑取證時只看到四張字幕：該路徑在 85.2M 多一次 Enter，原版在第四張後跳過其餘字幕。改用介紹頁後不按鍵的輸入（`tools/goal141-captions.inputs.json`）後十張全數取證。
- 前端把 `@BUILD1` 單張閘門推廣為逐張資料表（`@BUILD1` 參數不變），字幕變數以唯一 TSV 英格蘭列展開並核對執行期顯示字串；新增只供驗收的 `-checkpoint-steps`，一次重播取得十個檢查點。字幕變數 TSV 的四國姓名依 #29 改回原版英文。
- 第一輪重播發現 `@BUILD1` 在 85.8M、`@BUILD4` 在 535M 提前撤銷，原因是原版背景預載資源造成開檔數改變，畫面其實未變；字幕撤銷條件改為只看底層畫布、色盤、模式（每幀仍核真 VGA）。首輪收據封存於 `attempts/1/`；負例首輪因輸入檔終點超過負例步數上限而未跑，補產 350M 前綴後重跑。
- 勘誤：規格029 原寫「真視窗錄製路徑 85,800,001 步離頁」與「86M 離頁後 PNG 與英文控制相同」。該步數實為背景開檔觸發的撤銷，英文字幕仍在畫面上直到約 203M；規格029 正文已改寫為現況並加現行撤銷條件一節。`tools/check_goal130_window.py` 的 86M 期望屬舊前端，只能對目標130當時的收據重現。
- 變數 TSV 負例的回退原因是「@BUILD3 缺譯 + 其餘字模綁定不符」，屬預期的失敗即關閉；檢查器預期改為此組合。
- 驗證：真 GUI 十張截圖與重播逐像素相同、十檢查點中英原版狀態相同、四項負例、缺原版 SKIP 77、`go vet`／`go test` 通過；全面回歸六點（含 `@BUILD1` 82M）與目標138收據相同。容器皆 `--rm`。

## 2026-09-26：目標142首則教學提示 CONFORMED，#36 完成

- 假設「原版只在 Discoverer 難度預設開啟教學提示」並以探針驗證成立；先前各輪都選 Explorer。
- 使用者看過 A（30px）／B（34px）預覽後選 A。
- help 讀字期間原版同時畫顧問肖像並壓到木紋框，介紹頁閘門的「其他寫入者即撤銷／以印前底圖還原」不適用；另寫 help 閘門，逐點記錄最後寫入者重建印前底圖。
- 第一次真 GUI 顯示缺譯：help TSV 欄內含雙引號，Go csv 嚴格模式整份拒讀；改為逐行 tab 切欄。首輪收據在 `attempts/gui-1/`，首輪回歸在 `attempts/regress-1/`。
- 檢查器初版要求現場截圖整張等於重播；575M 那張截圖晚一幀，框外船隻閃爍不同。改為文字區逐像素相同並記錄整張差異範圍。
- 驗證：真 GUI、四檢查點中英原版狀態相同、三項負例、缺原版 SKIP 77、`go vet`／`go test`；全面回歸六點與目標138收據相同。容器皆 `--rm`。

## 2026-09-26：目標143海上選單列與狀態欄 CONFORMED，#37 完成

- 使用者決定本輪一起做選單列與狀態欄、選單寫成「(G)遊戲」字母黃色、22px 加黑影。
- 狀態欄含動態值，現行「每欄預烘一張字模」不適用；新增執行期字元圖集拼字：每次讀字事件記錄改色像素，依模板與詞典 TSV 轉中文，再以圖集拼出遮罩。每區只用一個補片層（`ComposeLayers` 每層都解碼整張畫面，逐行開層太慢）。
- 確認原版重印狀態欄前會先清掉舊字，改寫前值是乾淨木紋；仍加上「改寫前值不得是文字色號」的保險。
- 缺詞負例需另烘對應缺詞詞典的圖集（圖集綁定詞典雜湊），腳本以前置檢查要求該檔存在。
- 驗證：真 GUI 六張、六檢查點中英原版狀態相同、四項負例、與遊戲選項並用的組合重播、缺原版 SKIP 77、`go vet`／`go test`；全面回歸與目標138收據相同。容器皆 `--rm`。

## 2026-09-26：目標144動態文字資料模型 DRAFT，#6 完成

- 使用者指示剩餘 Issue 依序執行、封裝（#15）最後。
- 規格033 把各欄位規格歸納為訊息記錄、三種輸出類別（固定單行、逐字事件列、模板動態行）、整則替換與回退、同文異境規則。
- 參考實作初版把沒有改色的空白逐字事件濾掉，字幕整列字串少了空格而對不上；改為逐字事件不論有無改色都保留。
- 驗證：`tools/check_goal144_text_model.py` 三情境 PASS、缺原版 SKIP 77。

## 2026-09-26：目標145清冊與覆蓋率報表，#7 完成

- `tools/coverage_report.py` 彙整九份 TSV、原版來源核對、各目標重播收據與三條探針路徑；明細（含原文）只在 workplace，摘要只含數量與鍵。
- 驗證：容器內重跑，810 列全部來源核對通過；收據清單無缺檔。

## 2026-09-26：目標146靜態內嵌文字普查，#8 完成

- 以控制重播檢查點擷取正常路徑 18 個相異畫面與不按鍵的開場動畫（到 1000M），探針加 `-from` 與其他寫入者範圍以判別動態／靜態。
- 國王接見畫面初看像圖內文字，探針證實是 `0D21:00C6` 動態印字；`Loading Game...` 來自 `OPENING.TXT @MESSAGES`。
- 靜態候選六項，只有製作名單職稱橫幅建議覆蓋；原版截圖只留 workplace。

## 2026-09-26：目標147靜態覆蓋 DRAFT 與原型，#9 完成

- 原型以畫面指紋觸發；初版整塊平塗太生硬，改為文字帶內清除暗色像素並補回卷軸底色，門檻由色號亮度分布決定。
- 驗證：命中／兩張別的畫面／改一像素四組對照 PASS。

## 2026-09-26：目標148字型、術語、範圍與版面決定，#10 完成

- 使用者決定：Cubic 11；第三波說明書優先；所有可達文字；超界自動縮字、下限欄位字級 2/3。
- 以最長教學 help 做縮字壓力測試供確認（185 字縮到 23px）。

## 2026-09-26：目標149規格033升 READY，#11 完成

- 逐類列出原版證據、資料模型、安全矩形、超界政策與已 CONFORMED 欄位；通用行為連回前端程式與收據；強推論逐項標示。

## 2026-09-26：目標150動態覆蓋實作與綜合驗證，#12 完成

- 海上圖集改多字級、前端依剩餘寬度選字級；縮字測試先用 14 字（剛好放得下，未觸發縮字），改為 16 字與 23 字。
- 多字級修改初次套用時，gofmt 改過欄位對齊使字串比對失敗而整批未寫入；改用空白不敏感比對後套用。
- 全部欄位旗標同時開跑兩條路徑，中英原版狀態相同；help 路徑終點與目標142 收據相同。

## 2026-09-26：目標151靜態覆蓋正式實作，#13 完成

- 前端加入靜態引擎（`--static-credits-a`），重複鍵改為整組停用。
- 第一輪真 GUI 發現「音效程式」右端殘留原文「Y」、「電腦美術」殘一點：文字帶只取原文墨跡中段，漏了「BY」。改以卷軸內部亮區（第176～182列）為文字帶並納入 Q 尾巴所在的第182列，重烘字模後重跑。首輪收據在 `workplace/reports/goal151-static/attempts/band-1/`。
- 全面回歸六點與目標138收據相同。

## 2026-09-26：目標152驗證矩陣，#14 完成

- 矩陣首跑時綜合動態列傳錯收據根目錄而 FAIL；另發現部分收據多記 `NATIONS.PIK`，改為合併檔案雜湊並檢查同名衝突。
- 回歸列初次把字模 JSON 當收據；改以 `.memory` 存在判定重播收據。
- 同一環境連跑兩次，JSON 與 Markdown 報告位元組相同。

## 2026-09-26：目標153第一個中文垂直切片收尾，#26 完成

- 靜態圖檔雜湊不符原本併在「缺譯或無效」原因裡，拆成 `image-version-mismatch`。
- 首次圖檔負例改最後一個位元組並跑到 470M：原版開場解碼跑進未實作的 80186 指令而中止。守門在載入時判定，改為只跑到 2M 步。
- 驗證矩陣回歸列改以目標153 前端為候選，新增版本守門列。

## 2026-09-26：目標154第三波說明書術語表（#27 第一輪）

- 解包：`colonization-research` 的 p7zip 缺 RAR 解碼器、`unrar-free` 無法轉換 UTF-16 檔名；借用的 `7zz` 也不認這個封存檔。新增只裝 `unar` 的 `tools/Dockerfile.manual` 後解包成功。建置時開網路，執行 `--network none`。
- 84 張影像分四段派子代理判讀，各自只寫一個輸出檔；子代理自行加了「僅英文」證據值（說明書只印英文的元勳姓名、選單字），保留。
- 衝突檢查初版把同一英文的不同譯名當成互相衝突，改為任一譯名都算一致。

## 2026-09-26：目標155定稿譯名（#27 第二輪）

- 子代理初選 252 列並列出 15 項需人工確認的取捨；其中四類（錯字誤譯、國名、多譯名取法、人名格式）交使用者決定後套用，另補四個國名形容詞形。
- 殖民地地名首跑時產生 45 列假衝突（地名中的 Fort 等），改為地名不套術語。

## 2026-09-26：目標156譯稿套用定稿譯名（#27 第三輪）

- 依批次在地化流程：試作一批審閱後補「不換的情形」規則，再平行五批；批次 6 首次派工停滯無輸出，單獨重派。
- 合併驗證攔下：「鎯」缺字、兩列未換也未說明、字幕變數同占位符多列。
- 審閱改動摘要時發現 @UNIT19 句尾「戰士」被改成「印地安人」、「資深斥候」恢復時誤傷一般「斥候」，逐列還原。
- 檢查器修正後多出 29 列漏網，以補充批次處理。
- 改稿後 34 個正式欄位字模綁定失效（fail-closed 回原文），重烘重驗獨立為目標157。

## 2026-09-26：目標157改稿後重烘

- 首次重烘在第一張旗卡中止：旗卡片段驗證器與規格021 釘住「英格蘭」與其墨跡，依新譯名重新量測後更新；國家介紹驗證器同樣更新。
- 重烘時發現 @BUILD7 仍是「殖民地」，追到術語檢查沒處理 colony／colonies 複數，補規則後以第八批改稿處理。
- 第一次全部旗標載入時選項列 0x4E9 記 `font-mask-out-of-bounds`：前端 `optionRowInk` 也釘了舊墨跡，改為 256×25 後重建。
- 使用者決定視覺重驗延到語料定稿後，開 Issue #38 並在 worklist 登記；#15 依賴它。

## 2026-09-26：目標158全遊戲 TXT 分母

- 以「含字母的顯示行」為單位盤點 18 個 TXT，依來源位移對照十份譯稿；遊戲畫面 3,561 行、已翻譯草稿 1,764 行。首版把開場與結局動畫參數表行尾的 `;` 註解算成文字（多 26 行），改為分號前無字母的行視為資料行。

## 2026-09-26：目標159未建檔遊戲文字語料

- 試作批次發現：子代理把字面 `\n` 寫成實體換行（合併時正規化）、原文有 `%NUMBERn`／`%COUNTRY` 等控制碼（驗證規則擴充）。
- 原規則要求占位符順序與英文相同，逼出「一座%STRING0，屬於{%STRING1}」這類生硬句；改為有編號的占位符可移動，已完成的批次不回頭重譯。
- 英文冠詞等片段允許留空，但必須寫理由（狀態 `omit`）。
- 一批（批次 6 前一目標的教訓）以分段暫存避免長輸出停滯，本目標 16 批皆完成。

## 2026-09-26：目標160全遊戲語料收尾，#27 完成

- 覆蓋率報表納入語料清冊時發現預設 CSV 引號規則把含英文雙引號的列併讀（867 讀成 865），改為 `QUOTE_NONE`；舊清冊數字不變。

## 2026-09-27：目標161語料定稿後重驗，#38 完成

- 八個目標分派子代理平行重跑；主機負載 40～60，多支 GUI 腳本的牆鐘等待上限不夠，子代理以只放大上限的複本完成，事後把上限改成可用環境變數覆寫。
- 勘誤：目標137 的「西班牙」收據其實走了英國路徑（介紹頁事件為 @NATION0A／0B，截圖與本輪誤選英國的失敗例逐位元組相同）；當時檢查器沒有核對國別。現況以目標161 收據為準，檢查器已加國別斷言。
- 目標150 檢查器原本逐像素比對舊目標143 海上畫面；改稿後必然不同，且前端已不接受單一字級圖集，改為比原版狀態與安全區外畫面。
- 一個子代理在主機以 python3 讀了一次輸入檔的 end 欄位（唯讀），違反「分析在容器」規則，已記錄。

## 2026-09-27：目標162封裝、授權與技術預覽發布（#15）

- 使用者決定：公開儲存庫並發預覽版、保留原版英文對照、截圖與說明書術語保留並於授權點名、先只做 Linux。
- 第一次 smoke 終點記憶體與驗證收據差 27 位元組：啟動器預設開啟存檔層，全流程的自動存檔在存檔層寫入成功，驗證收據當時原版目錄唯讀、寫檔失敗。拆成「不開存檔層須逐位元組相同」與「開存檔層須寫入存檔目錄」兩項重跑。
- 字模檔內 `scope` 原寫「不加入散布包」，與發布決定矛盾；封裝時改寫複本的聲明，原檔不動。

## 2026-09-27：目標163功能鍵轉送（#39）

- 前端新增 `key` 輸入種類，只用 dosgolem 既有 `PushKey`；單元測試、真 GUI（數字鍵盤 8／7、F1、Esc）、中英同輸入重播、移除按鍵反向對照、六點回歸對 `goal161-regress-a` 全部 PASS。
- 驗證矩陣改用 `rich2-py:latest` 執行（研究映像沒有 Pillow）；`--output` 是目錄，產物複製回 `docs/verification-matrix.md`。

## 2026-09-28：目標164 GUI 步數對齊（#40）

- 第一版只把點擊改成步數對齊，高負載下法國仍選成英國；逐點截圖發現 43.5M 的 `click 220 200` 落在選國頁左側被當成「完成」。改為等 `NATIONS.PIK` 畫完再點旗卡並刪除該點擊後，兩輪六次全對。第一次嘗試封存在 `workplace/reports/goal164-step-clicks/attempts/wallclock-card-race/`。
- 第二輪曾在腳本檔被改寫時仍在執行，已停止並整輪重跑，未採用其結果。

## 2026-09-28：目標165 通用對話框正文（#41）

- 探針沿英國海上路徑往西，找出正常路徑上的新大陸木刻畫、Land Ho、登陸詢問與原住民訊息；對話框與 help 是同一個逐字印字常式，讀字基址隨堆疊變動，不能當鍵。
- 缺譯名反向對照改了兩次：只刪術語表的 Sioux 不夠（NAMES.TXT 對照也能解出）；真 GUI 路徑遇到的是 Iroquois 不是 Sioux。最後以「移除現場遇到的部落名，兩處來源都刪」並讓檢查器比對中文重播的原住民字串。
- 真 GUI 與腳本版路徑分歧（船停河口，出現 `@LANDFALL2`），檢查器接受兩種登陸詢問。
- 真 GUI 以全部旗標執行、重播只開 `--dialog-a`，所以兩者只比對對話框安全區；原版狀態另以中英重播比對。

## 2026-09-28：目標166 四處動態文字（#42）

- 真 GUI 前兩次截圖時機錯：固定步數截圖在步數對齊的點擊後落在畫面出現之前（主選單 23.6M 才出現、載入訊息晚於 14M）。改為依前端狀態檔的畫面階段截圖並記錄步數，重播與檢查器共用這份步數；前兩次嘗試封存在 `workplace/reports/goal166-spots/attempts/`。
- 靜態覆蓋原本只處理「淺底深字」，載入訊息是深色木紋上的亮綠字，改以清冊的原文色號集合判斷；製作名單字模重烘後像素不變。
- 目標151 檢查器原以清冊列數比對製作名單欄位數，改為只數製作名單前綴的列。

## 2026-09-28：目標167 其餘教學提示（#43）

- 固定步數的 GUI 腳本在遊戲自行延遲後與畫面脫節，改寫 `tools/gui_auto.py` 依前端狀態檔的對話框文字應答；過程嘗試封存在 `workplace/reports/goal167-tutorial/attempts/`。
- `@TUTORIAL2` 首次回原文（`ink-outside-box`）：顧問肖像擋住首字左側的框線掃描，改由最後一行起掃。
- `Caravel` 在術語表與 NAMES 對照譯名不同而查無，改為定稿術語優先。
- `@TUTORIAL5`、`11` 的母港 `London` 只在譯稿 NAMES.TXT 列，未進變數對照；補上並加單元測試。
- 重播前兩次把反向對照圖集目錄 `neg-nohelp-atlas` 連同舊收據一起移進 attempts，重播腳本前置檢查失敗；移回後重跑。
- 前端以 `workplace/dosgolem` 的 `colonization-audio` 分支（`a3a5609`，含未啟用的 OPL 合成）建置；前端不呼叫 `EnableOPLSynth`，驗證矩陣記錄此提交。
- 回歸：六點回歸以新前端對 `goal161-regress-a` PASS（`workplace/reports/goal167-regress/`）；驗證矩陣 PASS 19。
- 流程勘誤：OPL 合成（#47）的移植與機器接線在規格037 READY 之前完成，違反規格閘門；已補規格並以驗收決定是否保留。子代理曾在主機執行一次空的 python heredoc（無輸出、無寫入），違反「分析只在容器」；之後派工 prompt 明列此限制。
- 驗證：真 GUI、中英重播、兩項負例、缺原版 SKIP 77、`go vet`／`go test` 通過。容器皆 `--rm`。

## 2026-09-28：目標169 通用字串覆蓋與殖民地畫面（#44 第一部分）

- 探針原本只收「字元、0」交錯的偶數位元組，連續字串看起來缺字；新增逐串紀錄後確認殖民地畫面、狀態欄都是 `0D21:00C6` 連續讀取。
- 首版重播：難度頁完成提示與旗卡 `Immigration` 被字串層與專屬欄位重複處理；專屬欄位的原文判定補上「去一層外括號」與旗卡片段表。
- 狀態欄相鄰兩行安全區相接被當成重印而互相撤銷，改以原版墨跡重疊判定；安全區延伸到欄右緣時把之後才畫的圖示納入比對而撤銷 `With:`，改為只延伸到中文實際寬度。
- 殖民地畫面的 `@TUTORIAL4` 顧問肖像壓住上框中段，規格035 的上框掃描穿過肖像，中文錯畫到畫面頂端；改為首行寬度逐欄取眾數。
- 真 GUI 第一次：建城後剩餘的自動意圖（Return、KP_9）進了殖民地畫面，原版在 `@TUTORIAL4` 上屏前就被緩衝按鍵關掉（英文控制同樣沒有顯示）。第二次：按住 b 期間 Xvfb 自動重複把 `b` 送進命名欄，且木刻畫沒有按鍵可關而卡住；改為意圖尾端補一個 Return、Xvfb 以 `-ardelay 60000` 關閉自動重複。第三次：前端在 673.2M 因 CPU 跳進圖形資料（`3E94:BF2B` 的 `66 69`）而中止，當時前端只在正常結束時寫輸入收據，無法重現；已改為出錯時先寫輸入收據與 `crash.json`。嘗試收據封存在 `workplace/reports/goal169-colony/attempts/`。
- 使用者提示空白鍵或 Enter 可加快進度：以探針實測，開場字幕期間連按空白鍵或 Escape 都不會縮短（字幕約每 110M 步一張），只能縮短遊戲內的意圖間隔。
- 流程勘誤：規格038 仍是 DRAFT 時就開始實作，違反規格閘門（與 #47 同類）；以逐串探針收據補證據後才升 READY。
- 探勘子代理完成歐洲港口、報告與百科的字串清冊（`workplace/reports/goal170-census-explore/REPORT.md`），子代理的寫檔權限不含報告檔，由主迴圈依其交回內容寫入。
- 回歸：六點回歸對 `goal161-regress-a` PASS；目標167 教學提示路徑以新前端重播並對舊真 GUI 截圖核對 PASS（上框掃描改動不影響五則）；驗證矩陣 PASS 20。
- 驗證：真 GUI、中英重播、兩項負例、缺原版 SKIP 77（檢查器）、`go vet`／`go test` 通過。容器皆 `--rm`。

## 2026-09-29：目標170 歐洲港口與顧問報告（#44 第二部分）

- 新增前端乾跑旗標，以探勘清冊 268 串逐串檢查：首輪命中 215 串；補模板、比對前去頭尾空白、改為整串精確相符優先、加收 PEDIA／MENU 單行列、元首名槽位後為 262 串，其餘 6 串由執行期的熱鍵合併與海上層處理。
- 真 GUI 第一版：意圖以逗號分隔，`click:x,y` 被拆開而中止；改為 `click:XxY`。第二版：`e` 在 `@TUTORIAL4` 上屏前送出、Escape 太早；改把 Escape 併入教學提示應答並以 `wait` 空出閒置間隔。第三版：港口畫面的數字 `3` 被當成訊息框而一直等待應答，gui_auto 改為少於三個字母的印字不等待。第四版：港口說明框與訓練對話框沒有陰影色而回原文（`no-box-style`），且說明框墨跡延伸到 x≥240 不被視為訊息框、被第一次點擊誤關；對話框引擎改為有外框即可、字級依原版字高，GUI 判斷取消 x<240 限制。嘗試收據封存在 `workplace/reports/goal170-eu/attempts/`。
- F9 部族名以同一字串 1 像素位移重印四次做描邊，首版只擦掉最後一次；新增描邊字合併。
- 回歸：六點回歸 PASS；目標167 教學提示路徑、目標169 殖民地路徑以新前端重播並對舊真 GUI 截圖核對 PASS（目標167 的反向對照圖集依新字級範圍重烘）；驗證矩陣 PASS 21。
- 驗證：真 GUI、中英重播、兩項負例、缺原版 SKIP 77、`go vet`／`go test` 通過。容器皆 `--rm`。

## 2026-09-29：目標171 殖民百科（#44 第三部分）

- 置中段落型版面原本把單一 `^` 開頭的行併入前段，百科標題行會與內文黏在一起；改為自成一段（國王接見無此類行）。
- 百科稿有 CP437 0xF9 項目符號，模板正規式以原始位元組編譯而失敗；改為逐位元組轉碼位，與執行期重組顯示字串一致。
- 真 GUI 第一次：在工具呼叫內以 `&` 啟動的容器隨呼叫結束而停止；第二次：開窗前載入兩份約 25MB 圖集超過腳本等待 10 秒；第三次：百科下拉選單被當成訊息框按 Return 關掉，之後的點擊落在小地圖、Escape 叫出「Exit to DOS?」並被 Return 確認而結束遊戲。改為下拉選單應答 `none`（不按鍵）、「Exit to DOS」一律 Escape、視窗等待延長為 60 秒。嘗試收據封存在 `workplace/reports/goal171-pedia/attempts/`。
- 檢查器首版把雪茄條目的鍵寫成 `@CARGO1`（實為 `@CARGO10`），反向對照也移錯了條目；改正後只重跑該反向對照。缺對話框圖集時字串層依設計一併停用（`dialog-catalog-unavailable`），檢查器原本誤期待字串層照常，已改正。
- 回歸：六點回歸 PASS；目標167／169／170 路徑以新前端重播並對舊真 GUI 截圖核對 PASS（各反向對照圖集依新綁定重烘）；驗證矩陣 PASS 22。
- 驗證：真 GUI、中英重播、兩項負例、缺原版 SKIP 77、`go vet`／`go test` 通過。容器皆 `--rm`。

## 2026-09-29：目標172 殖民地畫面內操作與對話框選項列（#44 第四部分、#46）

- 探勘子代理完成殖民地內操作清冊（`workplace/reports/goal172-census-explore/REPORT.md`），其寫檔權限不含報告檔，由主迴圈依交回內容寫入。
- 選項列首版 `layout-overflow`：後備譯文用到字串層模板的字（例如「費」），對話框圖集沒有；對話框圖集改為也收字串層來源的字。一度同時綁定其雜湊，使改動模板的反向對照也必須另烘對話框圖集，改為只收字、不綁雜湊。
- 逐行文字把連續空白壓成一個，模板補單一空白寫法；建造清單 `ARMORY (52 Hammers)` 同時命中泛用與專用模板而被判為不明確，改為譯文相同即接受。
- 對話框引擎只保留一段，選單標題被隨後印出的清單取代而回原文；改為保留不重疊、先後完成的前一段。
- 真 GUI 第一版：工作者所在方格隨路徑而異，點方格沒開到職業選單；改點左下碼頭單位。BUY 說明框因第二次點鎚子鈕把面板切回預設而沒開到，移交 #45。
- 港口購買、訓練清單價格欄沒有 `=` 標記，原版靠行內空隙右對齊；加入行內空隙欄（16 邏輯像素或連續空白）與右欄模板 `col-*`。長名稱的建造清單行空隙只剩約 9 點，只靠像素門檻不會分欄，補上連續空白條件。模板表雜湊變動，七份字串圖集（含三個反向對照）重烘。
- 目標167／171 兩條真 GUI 以新前端重拍時世界不同（部族由易洛魁變成切羅基），覆蓋內容不足，不作基準。舊路徑回歸改用 `tools/check_rebase_replay.py`：舊基準通過時真 GUI 與舊中文重播逐像素相同，所以新舊中文重播相同的檢查點仍與真 GUI 相同；原版狀態與英文控制必須全同，中文改變的檢查點逐一列出並目視確認。不給允許清單時檢查器失敗（反向對照）。
- 驗證：目標172 真 GUI 重拍兩次（前端改兩次），最後一次檢查器 PASS；目標169／170 檢查器 PASS；四條路徑重播比對 PASS（改變的檢查點：167 三個、169 兩個、170 六個、171 兩個）；六點回歸 PASS；驗證矩陣 PASS 23。
- Docker：全部 `--rm`，本工作容器以 `colonization-goal172*` 命名，結束後無殘留。

## 2026-09-29：目標173 全可達文字普查（#45）

- 子代理起草段落對照表（786 段、155 條樣式，附反向對照），主迴圈定稿為 `text/census-map.tsv`，把「其他」細分為多畫面共用、貿易路線、事件版畫、不顯示。
- 普查工具第一版以事後配對與模糊比對（子字串、無空白分段、單字重疊）歸屬顯示文字，補了五次仍有誤判，其中字串層以 source 事件配 active 事件時，同一泛用鍵會被後來的字串覆蓋，把已顯示中文的「Docks」誤報為英文。整支打掉重寫：證據只取收據自己記錄的鍵與 `shown`，歸屬只用精確比對，歸不到者交人工分類。
- 沿用 `text_inventory.units()` 時發現它把以逗號結尾的一般句子當成「名稱,數值」資料行截斷（TUTORIAL13 因此對不上）；普查改用自己的逐行抽取（資料尾巴須含數字）。`text_inventory.py` 只計行數，不受影響，未改。
- 驗證：`tools/check_goal173_census.py` PASS（重跑一致、等於提交版本、三個反向對照）。建立 #55～#61。
- Docker：全部 `--rm`，無殘留容器。

## 2026-09-29：目標174 輸入欄標籤（#46）

- 決定：輸入框內是玩家正在編輯的英文字元（含預填預設名），保留原樣；只翻譯標籤 `Name:`、`Colony:`、`Amount:`。`Amount:` 五處補入 draft 單行列。
- 規格035 附記：單行、標籤後接輸入內容與游標 `_` 的逐字印字視為輸入列，只在標籤墨跡內排版，中文右緣對齊原標籤右緣。fallback 事件另記引擎切出的各行，回原文時可直接看切行結果。
- 真 GUI 第一版：VIEW 下拉選單被 gui_auto 當成訊息框按了 Return，Find Colony 沒開到，最後的 Escape 還開出離開確認框；改為對下拉選單應答 none、直接點第 4 列，並拿掉地圖上的 Escape。
- 反向對照第一版只拿掉 draft 的標籤譯名，字串層仍以 `{w1}:` 模板與片段字典翻出標籤；改為同時拿掉 label-trailing 模板，並只以來源較少的 `Colony:` 作反向對照（`Name:` 另可由語料多行譯文拆出的片段字典取得）。
- 發現（已留言 #53）：發行啟動腳本 `tools/release/colonization-cht.sh` 沒有啟用 `--dialog-a`、`--string-a`；各驗證路徑也從未以完整旗標組合跑過。開局姓名提示由規格023 處理，只開對話框層的路徑中是英文。
- 發現（歸 #55）：VIEW 下拉選單、地圖上的殖民地名稱、海上狀態欄被教學框肖像壓住時露出的英文殘字。
- 背景回歸第一版在容器內用了不帶參數的 `wait`，連背景的 Xvfb 一起等而永不返回，空等約一小時；改為 `wait "${pids[@]}"`。

### 程序勘誤

- 輸入列規則先實作、後寫規格035 附記，違反「規格 READY 後才實作」。附記內容與實作一致，已補寫；之後新規則先寫附記再動程式。

## 2026-09-30：目標168 收尾、目標175 數位音效（#47、#48）

- 目標168 驗收早已完成，補結果段並關閉 #47；ymfm 授權列入 #53。
- 目標175 取證：目標168 探針顯示 DSP 只有兩次初始化、之後不播放。查 dosgolem 發現真實模式機器的 DSP 沒有 DMA 與 IRQ，初始化 DMA 測試永遠得不到 IRQ；開啟後驅動判定數位音效可用，建城木刻畫面播放 `COLDIG.BIN` 的取樣。原本「正常路徑沒有數位音效」是模擬器假象。
- dosgolem 規格 197 與規格039 先寫、升 READY 後才實作；在隔離副本本地分支提交 `b0bf259`，未推送。
- 探針 `tools/probe_goal165_dialogs.go` 加 `-sb-digital`，建置以臨時模組＋go.work 指向隔離副本（`workplace/reports/goal175-sb/probe-src`）；舊版對照以 `git archive a3a5609` 建另一支。
- 驗證：舊新 dosgolem 關閉時狀態相同；新前端關閉時重播目標174 與收據逐位元組相同；dosgolem `go test ./...` 全過；同輸入兩次 WAV 相同。
- Docker：全部 `--rm`，無殘留容器。

## 2026-09-30：目標176 前端音訊輸出（#49）

- 規格040 先寫、升 READY 後才實作。設計時發現數位音效在取樣當下讀記憶體，前端取樣的時點會影響內容；重播改在與真 GUI 相同的 200,000 步邊界取樣，兩邊 WAV 才能逐位元組相同。
- 檢查器第一版誤用 `same_state`（它要求第二組是英文控制），改為直接比對狀態、記憶體與最終畫面；檢查點標籤另有非 `cp-` 的終點列。
- 普查：矩陣新增收據後出現 VIEW 下拉選單的第三種重複次數，併入同一條 EXE 對照列。以文字雜湊分類重複輸出的選單文字較脆弱，之後各畫面 Issue 會碰到同樣情形。
- 驗證：檢查器 PASS；驗證矩陣 PASS 25；普查檢查器 PASS。
- Docker：全部 `--rm`，無殘留容器。

## 2026-09-30：目標177 海上地圖、下拉選單與名稱（#55 第一部分）

- 下拉選單：VIEW 選單 fallback 切行顯示整份重畫三次、`~`／`#` 列被略過；補重畫去重與選單熱鍵「(X)」樣式。真 GUI 第一版在選單開著時按 Escape 開出離開確認框並被按 Return 結束遊戲；改為連點下一個選單標題切換。
- 名稱：前端加 `--string-selftest` 離線自測，NAMES／LABELS 547 個名稱只有 12 個查不到（人名依設計保留原名、冠詞刻意留空、Land／General／Moderate 同字異譯待各畫面處理）；`(Major River)` 在完整旗標下由字串層翻譯，目標167 路徑沒開字串層才回原文。
- 引號變數：`@NOCITY` 的玩家輸入原樣代入，允許空字串。
- 部分遮擋：字串層與海上層改為逐點遮擋。第一版讓狀態欄疊字（改印的舊行被當成遮擋保留），補「新印字取代重疊舊行／舊項」並限定字串層開啟時才放寬；字串層與對話框重疊時改為照畫、重疊處還原對話框結果。
- ORDERS 選單停用（灰色）項目只讀一半字元，對話框層「讀取位置為奇數」時整段靜默略過，上半段因此英文；地圖上的殖民地名稱標籤不在畫布印字路徑（強推論：先畫在螢幕外緩衝再搬上畫面）；教學框壓住狀態欄時仍有三行殘字。三項移交目標178。

### 程序勘誤

- 下拉選單熱鍵與重畫去重又是先實作、後寫規格附記；之後的引號變數與逐點遮擋已改為先寫附記。
- 選單反向對照的 draft 變體在主機上以 Python 讀了 MENU.TXT 位元組判斷 `~`／`#`，應在容器內做；只讀、未改檔。
- 清理快速重播舊檔時用了 `quick.*[!n].json`，誤刪了截短輸入檔；改用明確檔名。

## 2026-09-30：Codex 接手 Claude 未提交工作與收尾驗證

- 路由：中文顯示與遊戲語意隔離命中 `local/localization-display-semantic-isolation.md`；文件現況命中 `local/project-document-responsibilities.md`；封包與版號讀取 `local/retro-remake-dist-all-output.md`、`local/retro-remake-release-versioning.md`。沿用專案顯示轉譯層定位及已決定的全可達文字、音訊、鍵鼠與三平台交付範圍。
- 先查 Git 身分、既有作者與未提交差異；Claude 的目標178 修改與既有前端副本相同，保留並逐項審查。以真正主機 `gh auth status`、Issue 及儲存庫現況確認公開性與尚未完成的 #50～#61；未寫入遠端、未 commit 或 push。
- ORDERS 停用列及英國 Jamestown 地圖標籤的既有檢查器 PASS；真 GUI／中英原版狀態與負例齊備。矩陣 PASS 27、SKIP 0、FAIL 0；普查重跑與反向對照 PASS，已顯示中文 409、待接 1,149、無法正常觸發 96。同步產生文件與唯一目前狀態表，#55 保持進行中。
- 修正封裝漏掉對話框、字串及音訊參數，補齊 13 份 TSV、兩份圖集與 ymfm 授權；版號採完整格式並拒絕覆寫既有輸出。新增 `tools/rebake_release_fonts.sh`，正式工具鏈重烘 22 份字模；新舊像素、尺寸與位置相同，僅更新譯稿綁定。更換過期靜態遮罩來源。本機暫存封包 50M 步啟動驗證沒有字模／圖集綁定失敗，原版狀態一致；未建立新正式包或 Release。
- 既有研究映像缺 Pillow／GUI，沿用既有 Ebitengine 映像並新增有固定來源的 `tools/Dockerfile.verification`。此映像只做檢查；正式字模使用 `font/README.md` 指定的 `rich2-py` 映像，不互換 Pillow／FreeType 版本。
- 程序修正：第三層混色停用列只有自製測試、沒有原版證據；規格先補 READY 回退，再移除未取證的配色分支。`probe_goal178_rebase.sh` 改為前景重播，避免裸 `wait` 把背景失敗報成成功，並排除輸出目錄的自我連結。
- 大河補證：原有正常玩家輸入加上 1,060M 檢查點，畫面顯示「（大河）」；完整原版記憶體與既有英文控制相同。`check_goal178_window.py --river-reports … --tutorial-reports …` 回 `PASS_REPLAY`，明確保留「新增檢查點未做真 GUI 截圖核對」限制，不提高普查完成數。
- 遮擋取證：可丟棄診斷副本在同狀態檢查點找出 `@TUTORIAL14` 單字元 `y`／`c`／`h` 誤刪森林、道路與 `With:` 項目。先將最低兩個英文字母的取代資格寫入規格038 READY，再修正程式；重建前端 `go vet`／`go test` PASS。完整受影響文字層重播正在驗證，不將仍低於三成墨跡的遮擋問題視為已解。

### 本輪驗證環境勘誤

- 矩陣曾因相對路徑找不到收據而失敗；改絕對路徑，在同一容器乾淨重跑 PASS，非產品缺陷。
- 初次字模重烘使用不同 Pillow 版本，尺寸守門正確拒絕；改回正式映像後 PASS，未放寬尺寸條件。
- 新前端單元測試初跑缺 `DISPLAY`；加入有界 Xvfb 後，以同一映像、同一測試重跑 PASS。
- 補拍大河時檢查點未排序，背景重播錯誤被裸 `wait` 掩蓋；排序並改前景執行後完成。失敗日誌保留於 `codex-audit/`。
- 兩條 600 秒舊基準分離重播及一條完整旗標新前端重播未完成；保留局部產物，不作通過證據。受影響層診斷省略其他覆蓋旗標，993,300,001 步的原版完整 RAM、索引與色盤仍和原收據相同；不得外推為全旗標封包驗收。

本輪收據入口為 `workplace/reports/goal178-orders/codex-audit/`。所有分析、建置與測試使用 UID/GID 明確的 `docker run --rm`，原版唯讀掛載；已確認歷史 root-owned 的 `original/` 是空目錄並僅移除該目錄。各批容器均清理後再前進；整輪清理狀態於驗證完成後補記。

## 2026-10-01：來源恢復、存讀檔與封裝續驗

- 規格032 READY 後實作暫停來源保留；只有完整墨跡恢復才重新繪製。加入有意義的生命週期測試，`go vet`／`go test`／重建通過。完整既有覆蓋旗標重播完成，68 個原版檢查點相同，45 張中文差異只在頂列／狀態欄。既有 GUI 的 ORDERS 四張、地圖標籤 35 張通過；沒有把遮擋期間殘字標成完成。
- 新來源真 GUI 與中英、負例重播已完成，原版終點相同。`intent-36` 地圖標籤安全區的 141 點差異仍由檢查器拒絕；色盤診斷支持水面動畫相位差，尚未解決外部抓圖與步數的同步，保留失敗收據。
- 用原版正常主選單讀檔與 GAME 選單手動存檔建立較短驗證入口；三側終點 RAM、原始與新存檔逐位元組相同。六張 GUI 安全區通過，首次恢復世界的圖未對齊；存讀檔缺譯仍歸 #61。所有存檔與原版畫面只留 `workplace/`。
- 封裝依實際二進位的 Go／模組版本收集完整授權，共 12 份；拒絕 Go 工具版本、平台不符或隔離 dosgolem 有未提交修改。當前暫存包以正式啟動器跑全部旗標的 50M 步短程啟動，字模與圖集綁定正常、原版 RAM 與舊短程控制相同；未建立新正式版號或發行包。
- 矩陣更新為當前來源的 `recovery-178` 收據後 PASS 27、SKIP 0、FAIL 0、原版輸入衝突 0；普查仍為 409 已顯示、1,149 待接、96 無法正常觸發。新 GUI 失敗圖與存讀檔探索未拿來增加完成數。
- 共同決策先做可丟棄的暫藏原型；第二版仍有黃色殘字，正在查來源，未問使用者替技術未知作選擇，也未把新策略寫入正式程式。

### 驗證環境補充勘誤

- 兩次前景命令串與背景 Xvfb 的括號範圍錯誤造成只等待 Xvfb；已停止該批容器並以明確程序擁有者重跑，不算產品缺陷。
- 存檔探索第一版的自動應答誤把 GAME 選單當離開確認，且步數上限前未完成手動欄位選擇；第二次正常 GUI 存讀檔流程才取得完整功能收據，兩者分開保存。
- 局部遮擋診斷初次沿用完整輸入的終點，卻明示較短上限，前端正確拒絕；改用保留同一輸入前綴的局部診斷收據重跑，不改原現場輸入。

- 新 GUI 狀態欄改以受版控 `check_goal178_window.py --status-reports` 重驗：53 張安全區 PASS，包含遮擋後恢復；規格032僅來源恢復功能升限定 CONFORMED。地圖水面差異仍保留，不讓狀態欄驗收替代地圖驗收。
- 已完成整行暫藏與保留框外中文片段的兩個可丟棄原型，三個檢查點的原版狀態相同、原型間差異只在狀態欄；先展示實際對照，再依 grill-me 要求詢問使用者。待答分支不進正式來源，沒有代答。
- 百科探勘第一版反覆開第二篇；原版每次返回清單都重設到第一項。修正後以正常 GUI 逐篇進入全部 16 篇貨物條目，建立目標179與受版控 GUI／重播／檢查入口，掛入 CONTEXT 與 #57 工作清單；中英與負例驗證完成前不提高普查數。
- 矩陣更新曾在印出 PASS 後外層回 124；同一映像、同一命令放寬有界時間重跑，正常退出 0，結果與前次逐位元組相同。這是時間上限問題，非產品缺陷。

## 2026-10-01：目標179貨物百科完成與普查更新

- 以當前正式來源、正常原版存檔入口逐篇驗完全部 16 篇貨物百科。真 GUI、中英及缺圖集負例同狀態，正文與 50 個字串欄位安全區逐像素驗證，包含 16 個效率表格標籤；沒有把正文以外的新欄位只靠事件紀錄算成完成。
- 將 GUI、重播及獨立檢查器納入版控，目標179掛入 CONTEXT／工作清單；#57 保持進行中。原版 PEDIA 與 EXE 全指紋守門，缺原版 SKIP 77、PEDIA 單位元組異動拒絕。
- 矩陣新增貨物範圍後 PASS 28；移除已由既有矩陣列驗到的過時「未驗範圍」敘述，仍保留全局、其餘文字、遮擋策略與三平台限制。
- 普查增加 29 個已顯示的執行期變體及 1 個未翻譯的讀檔清單，補驗 15 個貨物段落。最新為 1,684 列、453 已顯示、1,135 待接、96 無法正常觸發；已分類新增缺口，未歸類 0。可重跑與反向對照 PASS。
- 普查初次明細指向不存在的目錄，改到既有本機收據目錄後重跑；新增存檔描述彙總字串使驗收先拒絕未歸類，核對原版畫面後明列 #61 待完成，沒有放寬檢查器。

### 本輪收尾核對

- 最終矩陣正常退出 0：PASS 28、SKIP 0、FAIL 0、原版輸入衝突 0。JSON SHA-256 `483a42b0505cfa53c2cd2991f6a6abc26ada5ae5184a0a13583942eb39503ae7`，Markdown `52d3771f4570d4035fb9607e554cdc8e746d75c6c2633adb1eb400171139ca2a`。普查與工作清單驗證通過，未完成的人工驗證項維持未完成。
- 格式核對最初誤以為 TSV 最後一欄永遠空白；實際是可選的 `reached_unapplied`，有未套用收據時會有內容。已按既定十欄、唯一鍵、狀態總數與可選空欄重新核對通過，未修改格式或刪掉尾端分隔字元。
- `git diff --check` 除既定 TSV 可選空欄外通過；原版 EXE、封存檔、存檔、索引／色盤與二進位資料未被 Git 追蹤。新增原版畫面與存檔只在忽略的 `workplace/`，未對外發布。
- 正式來源仍為 `25a91067d94f22be59fb23325c75c76aea3b055c0f936e56d62f5ad6d5e3a481`，未混入暫藏／裁切原型。dosgolem 隔離副本工作樹乾淨，`upstream` 推送位址仍為 `DISABLED`。
- Docker 本輪全部使用 UID/GID 1000:1000、有資源與時間上限的 `--rm`；原版唯讀掛載。最後檢查無本專案執行中或已停止容器，無 root-owned 產物或 `.md` 空目錄，抽查文件與正式收據擁有權正確。未全域清理其他專案資源。
- 遮擋顯示策略的單一共同決策仍待使用者回答；選項、原型及證據入口已在 CONTEXT 保存。其餘可達文字與三平台發行尚未完成，未關閉 #55／#57，未 commit、push 或發布新 Release。


## 2026-10-01：目標180百科缺口取證與READY修正

- 原始五類正常走訪與三側重播完成；單位／地形的現有覆蓋檢查通過，職業、元勳、建築檢查按實際漏譯失敗，不降低預期項數。建築首跑逾時缺完整輸入，正常關閉的building-v2乾淨重跑才採用。
- 七篇正文及18個單位／地形短欄量測通過，補規格036／038 READY後修顯示轉譯。百科稿補JOB27為164篇；TSV的Tab、%%與占位符仍受原檢查器保護。一次百分比自測揭露通用未解變數守門也拒絕字面%，先回規格補審後只接受百科已確認的字面百分比數量。
- Go vet／Go test、七個百科來源控制測試通過；正式字模使用固定版本工具鏈。新GUI單位23、地形21、職業27、元勳25篇已全部啟用正文；同輸入與負例重播尚在執行，矩陣與普查維持原值。
- 職業及元勳的第一版重驗因執行中修改Bash檔案而中斷，缺完整收據，不採用。容器入口改為固定腳本副本，第二版正常退出。沒有DISPLAY的量測失敗分類為環境問題，加有界Xvfb後同一命令通過。
- 建築原始診斷81個共同取樣點與控制相同；52個候選欄位均能容納。學校／學院／大學的F9不印字且不讀結尾0已有窄追蹤與同RAM證據，仍先做DRAFT可丟棄分段原型，不直接修正式分段。
- 已完成批次容器均為--rm；後續四類重播與兩項診斷仍有界執行中。未commit、push、Issue寫入或發布；最終Docker與權利稽核待本批完成後補記。


### 2026-10-01：目標180正文收斂與同步驗收缺口

- 乾淨建築／地形最後正常GUI完成，退出碼均0、耗時801／333秒；38篇建築正文、53個已啟用字串欄位及21篇地形、96個欄位的GUI安全區與中文重播一致，中英及缺圖集完整原版狀態相同。三篇教育建築條列的實際GUI文字完整、無裁切。F9與五篇百分比建築正文限定CONFORMED；地形海岸／河流限定CONFORMED。
- 生命週期補查發現先決條件22個來源只有5個active，17個screen-sync-timeout；string_misses=0不能證明欄位已完成。補`--require-pedia-fields`，對既有收據的負例正確拒絕；同步修法仍DRAFT，候選只留本機。
- 矩陣重產PASS33、SKIP0、FAIL0、輸入衝突0，建築列明列部分驗收；普查1,849列／已顯示744／待接1,016／不可達89／未歸類0。地形五個等價模板鍵降為強推論，森林不可達舊假說撤回，保留未知原始來源與情境路徑待驗。
- 地形寫入探針沿完整原版正常輸入，500400000步完整RAM與控制相同；已版控指紋守門版本與候選log／state逐位元組相同。只證明TERRAIN鍵的RAM寫入，不把查找角色升confirmed。
- 封裝圖集改取現行164篇正文與八模板圖集，新增圖集與隨包譯稿／字型指紋核對；現行圖集接受，舊綁定及異版字型拒絕。沒有建立新版交付或Release；遠端Issue #57回讀為OPEN，未寫入遠端。
- 已完成的GUI、重播、矩陣、探針容器均`--rm`退出；同步候選量測仍在有界容器執行，收尾時再核對清理。原版始終唯讀，沒有修改主dosgolem或公開新原版素材。


## 建築正式v3驗收（2026-10-01）

`building-final-v3`正常GUI退出碼0、705秒；加強檢查`--require-no-string-misses --require-pedia-fields`PASS：38篇正文、70個字串安全區、全部22個先決條件在逐篇取樣點啟用。中英／缺圖集完整原版狀態及81個共同取樣點一致。GUI輸入SHA-256 `217af6321b916e9e79f236dc3ed78d03329e5f80c913387a79689b945a7c4eba`，終點RAM `fca0c413fe8cf37004db2078fd6917a21459c5bd1ea986a80b71451918203d66`；正式二進位 `b2813d1db94cc329f5fb93221fc0669b7f3dedd8b33e6f254e763efd1015b31f`。規格038先決條件與同步等待限定CONFORMED；v2的17欄失效已解決，舊失敗與候選量測仍保留。

矩陣改取v3並要求全部先決條件，另納入正常下拉選單六項環繞收據。最新重產報告入口為本機`matrix-v3/`、`census-v3.json`；以生成後的矩陣／普查數字為準。Miscellaneous／Complete其他入口與同文同譯地形的原始來源仍待窄查，Issue #57尚未完成。


## 2026-10-01：v3矩陣與普查重產

矩陣34PASS、0SKIP、0FAIL、0原版輸入衝突；彙整JSON SHA-256 `24ff75c8a6449f8b4e92c2a5be5c1698b3a7eec219ae9decf5e604a754530a4e`，可讀矩陣 `ee533b4b11893e90373fe2a62dee2eea55b21b421ce840ac61ec9c9ebf1657fb`。普查分母1,866列，已顯示761、待接1,016（正常649／特定局勢367）、無法正常觸發89；未分類及未使用樣式0。新增17列來自v3實際啟用的先決條件執行期字串，不是取消待接項或推定其他來源完成。普查TSV `d4a9472715ad6bbf3acba72d0fd4a4cb4250453d1a48f6b55206ca6f884eaa04`，報表 `306c7e1fd22b536c7afbdad2ad2730f5b1ba96a6ce2efd68a5e4476dd734fa69`；本機`matrix-v3/`、`census-v3.json`。

首次普查命令誤以矩陣彙整JSON取代原始矩陣定義，缺少dir欄位而停止；改用`tools/verification-matrix.json`後於同一容器工具鏈乾淨重跑通過。這是命令輸入問題，非產品缺陷。


## 2026-10-01：TERRAIN8來源有限補證通過

`tools/check_goal180_source_identity.py`PASS，本機`source-identity.json`：原版PEDIA.TXT標記檔案位移`0x65A5`、正文起點`0x65B0`。72495279步，DOS由PEDIA位移`0x6400`讀入512位元組至實模式`1C6A:E962`／20-bit線性RAM `0x2B002`，剛讀入內容逐位元組相同；原始讀入SHA-256 `130bfa6dbd8e58eda11f639a942febd3879bea89fc7c4c8ae424ab8dc58db27b`。稍後文字模式刪除CRLF的CR，有效489位元組前綴相同；尾端23位元組是殘留，不當成有效來源。

72515484步，`0E2D:0832`的原始`F3 A6`將RAM `0x249DC`標記與`0x2AC86`局部查詢鍵的`@TERRAIN8`及零字元完整同值比較。隨後走`0E2D:083B`與`9320:00DE`匹配成功分支；後續`0E2D:09F4`讀取正文最前29位元組（版面指令及標題），與該原始段落完全相同。跨下一個stdio緩衝的全文並未逐位元組串接驗證，不能把只取09F4時漏掉的邊界字元當成原版文字缺失。

IDA Pro 9.4 runtime原始二進位EA `0x001A`映射實模式`9320:001A`，函式原名`sub_1A`、邊界至`9320:0106`；無推測改名。正式關係庫`ida-pedia/runtime-lookup-final.i64`、匯出`runtime-lookup-final.json`，輸入片段SHA-256 `25adc1a8eefe200749aa0aff70c0c0c0a1255f99c4252c80f17519813e073825`，匯出 `ee89eb8a805ff3edbff87569b3d4ac5673ccea7cdffb30def24df5ab468e9b71`；此空間不是原始EXE的MZ EA。

已證實僅限本正常路徑查詢並讀取TERRAIN8初始正文；GUI字典選中的TERRAIN16只是同文同譯模板，不能據此宣稱原版讀取16。既有21頁／95已啟用欄位GUI、中英與缺圖集檢查仍通過；六個窄觀測在76065000步的RAM皆為`7a1b5da22c71b95e8d38a8de0590cc7cebb89cd176125c58aded6bbbd955e8f5`。原版、dosgolem、Go與正常存檔指紋沿目標180；精確工具及收據SHA由來源檢查JSON列出。

其餘四組同文來源與特殊森林仍未提高證據等級。完整正常路徑的標記比較補查入口本機`key-matches-all.go`，輸出`key-matches-all.log.matches.json`，每筆保留原CS:IP、兩個RAM參數、比較原bytes及最近PEDIA DOS讀取位置；追蹤58M～500400000步，原版終點須與terrain-fixed控制相同。此工具只觀測，尚未授權正式覆蓋條件／資料格式或普查改鍵。


## 2026-10-01：百科來源歸屬接入自動驗證

正常地形21次查詢與正式GUI來源已核對，五組同文模板只算實際查詢來源；READY後矩陣與普查加入source_identity自動檢查，偽造映射／錯輸入／錯列均拒絕。來源更正限定CONFORMED，不改前端或原版。矩陣34 PASS，普查761已顯示、1,016待接（normal644、conditional372）、89無法正常觸發；不提高同文完成數。正式生成頁與目前狀態表已更新。

本機重產入口`goal180-pedia-rest/matrix-v4/`、`census-v4/`與`source-identity-negative.json`；舊匯出正文位移多1勘誤另記RESEARCH-LOG。F1情境來源窄觀測進行中；首跑Go不在bash登入PATH，改既有映像`/usr/local/go/bin/go`，保留environment-error.log，不當成產品缺陷。一次性報表／負例容器均--rm退出；情境觀測容器本節寫入時仍執行，批次結束另驗Docker與檔案擁有權。



2026-10-01位址守門補驗：IDA情境初版`-b16`使檔案位移0載入EA0x160，runtime映射不能採用；更正`-b0`後的selector-function-v2每筆bytes與原始傾印相同，函式原名sub_EAC、IDA EA0x0EAC～0x1820映射實模式8C35:0EAC～1820。原始8C35:17D7的FF 76 06在59637458步讀取RAM0x2AF40／2AF41為12；這只證實本次地形參數，不外推呼叫者全集。既有查找資料庫96筆原始指令核對全部通過，偽造位元組拒絕；加強後matrix-v5仍34 PASS、census-v5仍761／1,016／89，來源映射限定CONFORMED不變。原版VICEROY與PEDIA、dosgolem及工具版本沿目標180固定指紋。

## 2026-10-01：正常建城續驗與跨平台技術預檢

- 目標181新局v3實際到切羅基交涉，未建城，沒有增加完成數。改由正常存檔切換移動模式、指定陸上單位；第三波說明書及原版選單操作已核對。v5真正進入Jamestown，真GUI取樣115400000步、正常關窗240400000步，RAM 78387f8d7c618a52ff2f2b11bf53fcc70dbdbb2b5680791d68db7221688e9321，GUI輸入 9cc5e96a86616abce6d323ed3310aef3d9d06a050a024a44255dd2ff52fa4009。v6延伸建造面板／BUY，當時仍在有界容器取證；三側及新欄位驗收待補。
- 目標182 Windows Go1.26.7／Ebitengine2.9.9／CGO=0建置通過，Wine正常主選單六個正式欄位中文安全區與Linux重播逐像素相同；50M完整CPU、RAM、原版索引與色盤相同。宿主開檔名稱七項大小寫差異逐項保留，按DOS檔名規則比較後清單順序與數量相同。前次比較器對觀測名稱大小寫拒絕，不是RAM或遊戲規則差異。
- macOS兩架構與通用檔建置通過，PE／Mach-O／Go建置資訊與通用檔兩切片實讀驗證通過。Mach-O最低版本只作載入標記，沒有宣稱真機相容；輸入及產物SHA-256由目標182與本機binary-structure.json索引。Windows原生／Mac真機、簽章、正式封包、Linux AppImage與影片均未完成，未新建版本或Release。
- 平台環境失敗保留：macOS缺/dosgolem掛載、GOPATH未指/go/pkg/mod；Wine缺Python／xdotool、未建scratch、搜尋到未映射視窗；首張Wine截圖被桌面裁掉26像素。逐項修正後用相同工具鏈乾淨重跑。Wine修訂映像沿固定既有Wine父層，Dockerfile.windows-verification只補鎖版驗證工具，不掛入主機runtime。
- 遠端#50～#61以真正host gh回讀均OPEN，未寫入遠端。現有正式矩陣34PASS及普查761／1016／89維持原值；跨平台主選單與建城探勘不冒稱全文完成。沒有改原版或主dosgolem，沒有commit、push或公開新原版素材。
- 已結束的跨平台建置、Wine、重播與v3～v5探勘容器均--rm；本段寫入時只有v6 BUY容器有界執行中，最終清理狀態在本批結束後續記。

### 2026-10-01：BUY正文限定驗收通過

目標181 v6正常建城後開建造面板及BUY，資金不足碼頭正文已有中文。18個原版共同取樣點與三側完整終點一致，GUI安全區及面板三欄與中文重播逐像素相同，負例回原文。字級量測30px、27位數壓力22px、超界回退；數值壓力不是原版價格上限。實際模板confirmed為規格036置中段落，不把BUY畫面名稱當成規格035無框回退證據。四行來源的選項未到，整列pending，矩陣34PASS／普查761不變。

量測首跑少DISPLAY、檢查器首版解包欄數錯誤，以及第二行大寫字矩形夾入相鄰字的錯誤，已改有界Xvfb、正確五欄介面與獨立墨跡連通區後通過。首次完整量測與最新metadata均保留，收據及指紋入口為目標181／規格036。

### 本批最終衛生核對（2026-10-01）

文件職責路由與reference已重新載入；工作清單由JSON重產、verify通過，人工未完成項未升格。新腳本Bash語法通過，缺合法原版的BUY檢查明確SKIP 77。Git身分及最近作者為wicanr2@gmail.com；非TSV差異檢查通過，原版EXE／DAT／存檔／封存檔及workplace未被追蹤。dosgolem隔離副本乾淨，upstream推送維持DISABLED。

本批建置、Wine、正常GUI、三側重播、量測及文書容器已全部--rm回收；無專案執行中或停止容器，無懸空映像。既有固定父映像及目前可重建工具鏈保留，未全域prune或刪其他專案資源。工作根無root-owned產物或錯掛載.md目錄；新增工具、文件、收據與Windows產物抽查UID/GID為1000:1000。原版始終唯讀，沒有修改主dosgolem，未commit、push、Issue寫入或發布新版本。

本批BUY正文與Win／Mac建置結果已索引；四行BUY來源的選項、其餘#55～#61文字及#50～#54正式發行仍未完成。下一步正常建造清單的可支付BUY選項，並沿相同玩家路徑取得殖民地正常存檔，避免重新以固定移動序列猜地圖。

## 2026-10-01：BUY來源訂正、普查守門與正常殖民地存檔

- 原版查詢已確認BUYME0，BUYME1只是同文模板；保留舊收據並追加RESEARCH／規格036勘誤，來源映射由READY限定CONFORMED，沒有改原版、正式模板、字級或存檔格式。
- 候選v6的別名漏位移，沒有命中完整candidate_id，錯把BUYME1算完成；逐列審查拒絕。v7帶extra又把三份未完整GUI驗收的港口選項升完成，765候選不採。正式v8只取已驗矩陣，762／1015／89，新增只有BUYME0；check_goal173的正式來源與反向對照同步修正，兩次重產、拿掉BUY減1、分類刪除／重疊拒絕均通過。
- 完整矩陣35PASS，來源偽造標記、錯終點、錯完整鍵及錯目錄均拒絕。首輪外層120秒回124，候選v6不採；最終全新matrix-v7及census-v8完整通過，後續長批次加容器內timeout -k與外層逾時，沒有採用半份報表。
- v7建造清單到達。v8按End未改選取，再按鎚子反而關閉面板；屬測試路徑問題。v9按Down九次真正選貨車，報價1040$仍高於1000$，不猜公式或注入資金。快捷鍵未產生新存檔，v10改用已驗GAME選單另存至空欄COLONY01.SAV。
- v10及三側完整終點、30個原版取樣點與新舊存檔位元組相同；GUI成功畫面整張與中文重播相同。原版新存檔留本機，指紋及重生入口由目標181索引。首版存檔檢查將訊息右側狀態欄也要求中英像素相同而失敗；存檔驗收改為原版狀態／存檔及同模式整張GUI，既有遮擋限制仍交#55，成功訊息仍英文，不提高其中文完成數。
- 現況、矩陣及普查已更新，未關閉#56或聲稱全文完成；未commit、push、Issue寫入或發布。正式封包與影片仍待後續；最終容器及擁有權檢查見本節末。

本批最終衛生核對：Git身分及近三筆作者均wicanr2@gmail.com，差異檢查通過；原版EXE／DAT／SAV／封存檔及workplace未被Git追蹤，dosgolem隔離副本乾淨、upstream推送DISABLED。分析、GUI、重播、來源及普查容器均--rm退出；控制面已查無專案容器與懸空映像，最後文書容器亦--rm。工作根無root-owned產物或錯掛載的.md目錄；新增工具、文件、收據與存檔抽查均1000:1000。原版缺失的正常存檔檢查SKIP77；未全域prune、遞迴chown、修改主dosgolem或公開原版新素材。目標仍未完成，繼續#55～#61及三平台發行，勿將本批來源補證當成全文驗收。


## 2026-10-01：目標181職業、議會與可支付購買續驗

命中規格閘門／正常玩家路徑、文件職責及README現況路由，實際載入對應入口。沿固定原版COLONY01.SAV由主選單正常讀檔；先處理進城截圖舊游標，增加移開後呈現等待，同安全區條件重跑通過。Space實際先切士兵；先前B開的是新城命名而非加入Jamestown，保留未完成探勘，不修改資金、地形或存檔。

新增五種議會顧問模板，依原版字高7／行距12、五項與25姓名最長組合量測DRAFT→READY，正常GUI及三側後限定CONFORMED。沿固定rich2-py字模工具重烘字串圖集，封裝改取新綁定；新圖集通過、過期圖集拒絕。可支付路徑正常伐木、選任元勳、木匠、兩次回合及關閉連續移民／木匠提示，實際1496年貨車481$、國庫1000$，正文和兩項選擇中文。原版BUYME1查詢、GAME.TXT讀取、完整終點與GUI輸入已核對。正文30px、27位數壓力26px、超界回退；原資金不足30／22px結果回歸相同。

議會12個、可支付BUY26個共同取樣點與GUI／中文／英文／缺圖集完整原版狀態相同，安全區逐像素相同；1495／1496標題另驗。GUI像素、來源標記及原版終點偽造全部拒絕，缺原版SKIP77。候選普查曾把未取GUI的懸停算入，未採用；新增census_scope=checker，逐次重跑檢查器並綁定同列GUI輸入及完整原版終點，只採已驗鍵／原文／安全區。未驗懸停排除及錯收據目錄拒絕通過。讀檔彙總只補分類，仍pending。

最新正式矩陣37PASS；普查788已顯示／1014待接／89無法正常觸發，分母1891，未分類0。分母新增25個執行期字串，含24已驗及1未驗讀檔彙總；另完成兩個既有TXT來源。普查兩次重跑等於提交內容，移除資金不足／可支付收據的負例分別降至787／785，刪除與重疊分類均拒絕。現況、生成矩陣／普查、README、唯一JSON工作清單與生成WORKLIST已同步；完整中文化及三平台發行未完成。

驗證環境問題：矩陣候選外層CLI逾時回124但已完成輸出，查無殘留；以同映像及同檢查入口增加容器內逾時後乾淨重跑成功。量測Go實驗局部變數撞名修正後同組裝重跑成功；均不列產品缺陷。遠端Issue #56實際仍OPEN；本輪沒有commit、push、Issue寫入或Release。

Docker清理：本輪所有一次性容器--rm且UID/GID1000:1000，專案執行中／已停止容器均0；find無root-owned檔或*.md同名目錄，抽查輸出擁有權1000:1000。沒有追蹤原版EXE、SAV、dump、封存檔或字型；dosgolem隔離副本乾淨、upstream push仍DISABLED。原版畫面、存檔及中間物仍僅留忽略的workplace。詳細來源與雜湊見目標181／RESEARCH-LOG。

## 2026-10-01：接手續驗居民職業第二頁

沿目標181既有固定前端、字串圖集與正常COLONY01.SAV新增city-more-v18入口，完成職業第二頁標題、六項裝備需求及三個停用灰色列的正常GUI／三側驗收。check_goal181_city.py新增--require-more，精確核對來源、字級、逐欄安全區與停用色，回報七欄verified_fields；GUI像素、來源位址、停用色、RAM偽造都拒絕，缺原版SKIP77。沒有修改正式遊戲規則、譯稿、來源檔或字模。

矩陣38PASS、0SKIP／FAIL／待重驗／輸入衝突；正式matrix-v20與census-v18由目標181索引。普查793／1896已顯示、1014待接、89無法正常觸發，兩次重跑與docs相同；移除第二頁收據後完整回到788／1891，新增五種裝備執行期組合，不是完成五個既有待接來源。移除資金不足／可支付BUY列後各減1／3，刪除與重疊分類樣式仍拒絕。README、CONTEXT、JSON工作清單與生成WORKLIST已同步。

第一次完整矩陣預算不足，增加預算後因呼叫端漏建輸出目錄而保存失敗；修正verification_matrix.py在重檢前建立輸出目錄，於同映像乾淨重跑38項通過。停用色檢查按實際6-bit色盤轉RGB的四捨五入修正，未放寬像素與狀態條件；屬驗證腳本問題。Bash/Python語法及worklist verify通過，沒有重跑不相關Go建置。

後續city-equip-v19實際觸發棄城確認，沒有完成前鋒裝備；city-arms-v20正常取消後回城，點零存量武器欄未開出面板。ABANDON2正文名稱變數仍英文，規格035只補DRAFT，未審實作不進正式路徑。武裝、多人口、港口／報告／貿易路線與#55～#61其餘文字、三平台封包及影片仍未完成。

遠端#56只讀核對仍OPEN、無留言，未commit／push、Issue寫入或發行。原版素材未被追蹤，dosgolem隔離副本upstream推送仍DISABLED。所有工作容器--rm、UID/GID1000:1000、唯讀原版與有界逾時；本批結束時專案執行中／停止容器皆空，輸出擁有權正確，未發現root-owned檔或誤建的.md目錄，未清理其他專案資源。

## 2026-10-01：棄城正文與取消顯示收尾

接續目標181，原始查詢確認正文為ABANDON，訂正同文選項模板導致的ABANDON2誤歸屬並保留歷史。先補規格035 READY，再正式接入僅ABANDON名稱欄位的顯示回呼；不改原版規則、資料或存檔。175個預設／自訂名稱排版案例沿固定圖集通過。

city-abandon-v23實際驗收抓到取消後中文選項殘留；保留失敗收據，不加完成數。生命週期原型確認讀字結束至真正收尾之間的重畫未被監看，補READY後持續觀測到收尾，完全抹除的候選拒絕啟用；部分墨跡／游標沿既有規則。新正式前端abandon-final-build-v25全部Go回歸通過，正常GUI重新讀檔、確認與取消，city-abandon-v25八個取樣點及三側完整原版狀態／GUI安全區通過，取消後無殘像。六個來源／像素／RAM破壞負例均拒絕，缺原版SKIP77。原型初次缺DISPLAY、驗證腳本混用稀疏取樣清單、矩陣編輯器誤判頂層欄名均屬環境／腳本問題，修正後同容器工具鏈重跑，未放寬產品驗收。

矩陣39PASS、0SKIP／FAIL／過期／指紋衝突；普查1896列、794已顯示／1013待接／89不可達，只完成ABANDON一個既有來源。兩次普查與docs逐位元組一致；拿掉棄城／資金不足BUY／可支付BUY後分別793／793／791，ABANDON2仍pending，分類缺失／重疊拒絕。已同步CONTEXT、README穩定摘要、規格、目標173／181、字型封裝交接與工作清單，WORKLIST由JSON生成，verify通過。收據及完整雜湊統一連至[目標181](docs/goals/181-colony-remaining.md)。

主機gh登入及Issue #56只讀回查正常，仍OPEN、無留言；未commit／push／發布。舊Windows／macOS預檢不包含本次修正；#55策略待決定、其餘文字與三平台／影片交付仍待完成。原版與dosgolem上游未修改。所有工作容器--rm、network none、UID/GID1000:1000並有資源限制及逾時；收尾檢查：本專案容器無執行中／停止殘留，無root-owned檔案或同名.md目錄，抽查輸出1000:1000；Git未追蹤原版EXE／SAV／封存檔／字型／dump。正式來源與已驗二進位組裝一致，矩陣／普查生成文件逐位元組一致，工作清單verify通過。diff --check排除TSV後通過；生成TSV末欄可為空，保留必要tab並驗欄數，不以去空白破壞資料格式。

### 同日續查正常第二居民入口

棄城正式驗收收妥後，續從原始COLONY01.SAV探索士兵進城。v26先遇TUTORIAL14，方向鍵尚在教學；v27正常Enter關閉後方向鍵未改士兵位置；v28數字2使地圖平移。保留全部收據並回查正常玩家路徑及既有View選單，不猜改鍵盤。v29正常View→移動單位後kp1出現西南移動圖像，末張右側仍舊位置；v30多等20M後實見議會選擇框，沒有把中途動畫當成穩定狀態。這些只是正常入口探勘，不增加正式完成數，也不宣稱新議會候選或武裝已驗。最新指紋、下一年度入口與腳本統一在目標181；原版／存檔唯讀，正式程式未再改動。

## 2026-10-01：士兵駐留正常入口續查（Codex）

目標181沿既有COLONY01.SAV正常讀取、切換單位、移動及議會選任。v31到1495年；v32確認士兵在(50,28)，後續碰上移民通知與教學；v33關閉教學後已到1496年，後段kp3實際作用於船隻，另記為測試輸入偏離意圖。正常點城後已見士兵駐留圖像，尚未加入第二居民或完成裝備。每段私有`exploration-summary.json`綁定原版、工具、輸入、截圖及完整終點；入口與勘誤見[目標181](docs/goals/181-colony-remaining.md)。

私有v34加入有界GUI探勘控制，僅在正常輸入批次間暫停程序以供觀察；不寫入原版RAM或改造存檔。正式來源、圖集與普查未變，矩陣維持39PASS，已顯示794／待接1013。Docker清理及控制結果待本批結束追加。

目標181的v35原版正常另存已通過25個取樣點、GUI／中文／原文／缺圖集完整狀態及新舊存檔位元組一致。新COLONY02.SAV為24371位元組、SHA-256 f683eb9132406e1dc7de5c90372f933b724b71b78a327551a305ba19d9a7d991；初始COLONY01.SAV未被覆寫。新入口只用於本機探勘，不增加中文完成數。原版TUTORIAL15指出由圍欄拖入田地或建築的居民加入方式；v36依此續查。

v36正常控制收據已通過13個原版取樣點、GUI／中英／缺圖集完整原版狀態及初始存檔未變；正常畫面取得兩居民與50火槍，但未新增中文驗收。v37逐畫面重跑已開出保存選單；原版成功訊息顯示COLONY03.SAV，實際更新的是該批工作副本COLONY02.SAV，未生成03檔，原因待原文控制與DOS檔案呼叫追查。上游dosgolem未修改，正式前端／圖集及39PASS、794已顯示／1013待接不變。

本批收尾：全部一次性Docker容器已回收，沒有專案執行中或停止殘留；未重建或新增映像。全工作根未見root-owned檔案或同名.md目錄，抽查輸出1000:1000。非TSV的git diff --check通過，原版EXE／SAV／封存檔及原始字型未被Git追蹤。保留既有未提交工作，未commit、push、修改Issue或發布Release。

## 2026-10-01：讀檔成功收尾與正常保存列中心勘誤

接續Claude／Codex未提交工作樹，保留既有變更；Git身分wicanr2@gmail.com、HEAD f6f0ab7。本輪依正常玩家路徑與顯示／語意隔離入口核對來源；讀檔成功LOADGOOD依RE→DRAFT→READY完成只作用於該模板STRING0的原值檔名守門，逐欄30px／100檔名量測、全部Go回歸、正常GUI三個取樣點、三側完整狀態與提示關閉驗收均通過。六個負例拒絕、缺原版SKIP77。未改原版、dosgolem、存檔格式或譯稿。

v37保存點落在列間隙，原文／中文／缺圖集／觀測器都實際寫02；保留失敗收據。v41改用第四列中心，正常生成03、11個取樣點與四側完整狀態／新舊檔案相同；v45 DOS建立／寫入也指向03。v48正常讀回兩居民／50火槍；v49正常士兵選取結果已觀察，三側續驗中，不增加完成數。

矩陣40PASS；普查1897列、795已顯示／1013待接／89不可達，未歸類及未使用樣式0。新增待接槽位清單合併觀測，不把正文成功當整個列表完成；兩次普查相同，移除本次列回到舊基準。矩陣首次180秒逾時、原型明示上限不足、保存容器漏映像名稱及量測TSV載入入口不符均保留並分類為驗證問題；修正後乾淨重跑。完整入口、雜湊與原始位址在目標181及規格035，不將不同步數RAM或不同位址空間當同狀態。

使用者明確採用遮擋整行暫藏／關框恢復，排除框外碎片，已回填CONTEXT與規格032；下一輪可審查READY並實作，不再重問同一決定。未commit／push、關閉Issue或發新Release；Docker清理與工作樹稽核於本批完成後追加。

v49續驗已完成：七個共同原版取樣點、正常GUI／中文／原文／缺圖集完整CPU、RAM、索引、色盤、輸入與開檔一致，初始COLONY03.SAV四側不變；正常讀回兩居民／50火槍，點士兵後原版圍欄出現士兵、火槍0。結果見equip-two-v49/normal-state-summary.json，不增加中文完成數。正式check_goal173_census.py通過，移除BUYME0／BUYME1／ABANDON後顯示數分別794／792／794，刪除或重疊分類負例均拒絕。主機gh核對Issue #50～#61均OPEN，#61仍要求其他存讀檔、教學與版畫逐列驗收；未寫入遠端。

本批收尾稽核：Git差異格式檢查通過（保留TSV刻意的空欄），未追蹤原版EXE／SAV／封存檔／字型／PIK／DAT；新來源、正式文件與輸出UID/GID1000:1000，沒有root-owned檔案或同名.md目錄。驗證容器使用--rm且主機回查沒有本專案執行中或停止容器；未全域清理其他專案。


### 2026-10-01：整行暫藏正式續驗與擷取步數勘誤

使用者已明確選定整行暫藏，規格032／038補READY後只修改右側狀態欄的暫藏、未變英文清除與字串所有權；保留讀檔檔名、棄城及來源恢復修正。正式build-v51全部Go測試通過，正常GUI v52跑完1210000000步，四側重播待完成。

舊intent-36的141點水面／邊緣差異，由執行前固定1112925001步重播後清零，原版終點相同；GUI記下1113000000更新步數，重播取到1113090001下一幅畫面，原失敗證據保留。gui_auto.py改取實際frame.step並檢查擷取前後來源穩定，v54新正常GUI待驗，不放寬像素檢查。

一次主機自動核准審查逾時，命令未執行；改為檔案設定後單次重試成功。尚有本輪有界重播容器，收尾時另記終態及Docker清理。

## 2026-10-02：整行暫藏限定驗收與讀檔城名追查

沿已確認的整行暫藏決定續驗，未重問。v52長重播退出124，僅控制與缺圖集有完整終點；v54在922M退出143、原因未定位，保留部分收據，不誤記產品缺陷。改採原版正常生成COLONY03.SAV短入口，主選單讀回、開關報告與百科選單；v55 GUI與四側序列重播均正常結束，八個共同取樣點、七張完整GUI像素、缺圖集原文、五側完整原版狀態及初始存檔不變全部通過。關框後整區完整恢復，只將此分支升限定CONFORMED，#55繼續進行。

gui_auto.py擷取改以frame.step且要求前後穩定，七張真GUI已使用並驗證；不放寬像素驗收。正式適配器、二進位與摘要雜湊見規格032及目標178。普查仍1897列／795已顯示／1013待接／89不可達，矩陣仍40PASS；遮擋策略不增加原始來源完成數。

讀檔城名仍英文，但已確認原版印字事件與候選，失效為canvas-copy-timeout。v56唯觀測副本完整原版狀態相同；112點安全區差異持續存在，正在正常移船v57核對遮擋假說，正式來源未再改。觀測第一次引用組裝前檔名失敗，核對strings.go後同容器工具鏈乾淨重跑；摘要列印誤將字典切片只影響列印，已另生成正式觀測摘要。完整diff檢查僅TSV刻意空欄有尾tab，程式／文件／JSON差異格式檢查通過；不刪空欄破壞TSV格式。

工作清單已從JSON重新生成；未commit、push、寫入Issue或發新Release，未修改原版或dosgolem。目前仍有有界GUI工作，批末另追加容器與擁有權稽核。

同日續驗完成：普通移船v57確認安全區53295000步才全部相同，來源卻先在52800000撤銷。v58可丟棄保留來源原型的六點同狀態、城名安全區及來源取代／模式切換／VGA守門通過；規格038補READY後正式實作，v59全部Go測試與建置通過。v60新正常GUI五張、六個共同原版點、五側完整狀態、存檔不變、缺圖集原文全部通過，僅讀檔城名恢復升限定CONFORMED。

v59對v55回歸八點原版狀態相同，全部狀態欄像素相同。新城名在關閉報告選單完整同步後啟用，與舊來源的差異只在原城名安全區；初次要求整張圖與舊版相同的過寬斷言保留，訂正後仍嚴格檢查區外與完整狀態。未重新開啟已確認顯示決定。

驗證失敗均保留：v58缺DISPLAY屬環境；補Xvfb後舊TestStringLabel的3M撤銷要求與新契約衝突，原失敗保留並只依原版新證據訂正此斷言，其他拒絕測例保留；v59的-mod=mod與Go工作區模式衝突，依Go明示訊息以GOWORK=off及隔離副本replace乾淨重跑。不是透過改原版資料或挑結果取得通過。遠端主機gh回讀#55仍OPEN，未寫入遠端；當前來源與收據入口已回填CONTEXT／規格／目標178及工作清單，普查795與矩陣40不變。

本批最終稽核：所有具名colonization容器均已結束並由--rm移除，無本專案執行中或停止容器；未清理其他專案資源。新正式來源、測試、文件、二進位與摘要UID/GID均1000:1000，整個專案沒有root-owned產物或同名.md目錄。未追蹤原版EXE／SAV／封存檔／字型／PIK／DAT；程式、文件與JSON差異格式通過，TSV空欄按格式保留。工作清單重新生成且與JSON一致，當前正式來源與v59快照逐位元組一致。仍未完成#55其餘範圍及整體發行，不標全面完成。

## 2026-10-02：船隻 ORDERS 收尾與普查來源範圍

沿正常 COLONY03 存檔入口確認船隻選單前十一行仍英文；無墨跡熱鍵前綴令逐行候選中斷。v63 可丟棄續讀原型恢復十四行，但關框後部分像素偶然存活使候選重新啟用；v64 要求前綴候選的全部記錄文字點仍存活，殘字消失。規格036先升READY，才修改正式來源，不改遊戲資料或存檔。

v65全部Go測試與乾淨建置通過；v66新正常GUI走讀檔、VIEW縮放及船隻ORDERS開關。十張GUI與中文重播相同，十四行中文、六個停用灰色列與關框完整恢復通過；GUI加中文／英文／缺圖集／v59五側完整原版終點及初始存檔相同。偽造來源、完整RAM、GUI像素及停用色均拒絕，缺原版SKIP77。來源與原始版本指紋、量測及重生腳本由目標178索引。

矩陣新增一列，41PASS、0SKIP、0FAIL、0過期、0輸入衝突。普查初稿含三個未驗診斷片段，未發布。第一限制原型丟失兩個既有EXE列，第二原型丟失歷史未套用觀測，均拒絕；第三原型保留既有來源及觀測，移除船隻收據後舊清冊逐位元組恢復。補READY後正式保留未驗片段於私有明細，不新增人工分類或原始來源映射。正式普查800已顯示、1008待接、89不可達，分母1897；只新增五列唯一MENU來源，同文歧義仍待驗。正式普查重跑與BUY／棄城來源反向對照、分類缺漏／重疊拒絕通過。

環境與輔助檢查失敗保留：量測輔助程式首次未初始化字模快取，另次未提供字串回退；補齊同一工具鏈後乾淨重跑。反向檢查首次漏複製結尾圖片、灰色變更只修改重播未同步GUI，不能作對應拒絕證據；補完整正例基線及兩側相同色修改後，灰色專用拒絕通過。控制收據不與自己套用非控制旗標斷言。未降低原版／像素守門。報表繁體字用字修正與生成檔不一致時，保留首次失敗，再由正式程式重新生成後重跑。

CONTEXT、規格、目標178及JSON工作清單已同步，WORKLIST只由工具生成。未commit、push、寫Issue或發Release；#55仍OPEN，整體中文化與三平台交付尚未完成。
本批收尾稽核：正式來源與v65快照逐位元組一致；JSON工作清單生成及驗證通過，普查與生成報表指紋相同。所有本批容器均由--rm移除，主機回查沒有殖民帝國執行中或停止容器；仍運行的fd2及其他專案容器未動。整個專案沒有root-owned產物或同名.md目錄，輸出UID/GID1000:1000；Git沒有追蹤原版EXE、SAV、封存檔、DAT、PIK或字型。程式、文件與JSON差異格式通過，TSV刻意空欄保留。

## 2026-10-02：MENU 六列同文來源限定收尾

續驗v69～v74確認MENU預載與逐列來源，沒有改dosgolem、正式前端或原版。兩個讀取掛鉤覆蓋及相同值寫入漏報的失敗收據保留；修正唯觀測探針後六列來源與正常GUI及完整原版終點相同。v75另量測VIEW十二列，21px、最長advance187及288×516安全區通過；一像素分隔線不誤算文字列。

規格036先DRAFT／READY，才接入內部欄位source_ids。v76正式來源與41項矩陣全部PASS，來源、輸入、完整狀態與字級偽造負例及缺原版SKIP77通過。v77普查只新增六列，806已顯示／1002待接／89不可達，分母1897；移除新授權逐位元組恢復800列完成數，欄位安全區／原文／無active拒絕、重產及BUY／棄城／分類反向對照通過。此兩欄限定CONFORMED，#55仍OPEN。

第一次正式檢查因掛載引號錯誤而SKIP，未取得原版；dockerd誤建三層空目錄。先確認正確原始路徑，再用同一命令重跑PASS；三個空目錄已精確刪除，未改使用者原始目錄。這是操作失誤，不記為遊戲缺陷。

陸地單位短GUI v78由正常第一存檔欄讀COLONY00、點拓荒者及開關ORDERS，正在探勘剩餘命令來源，不增加完成數。CONTEXT／JSON工作清單／README穩定摘要及規格已同步，歷史證據保留。沒有commit、push、遠端Issue寫入或新Release。批末另記Docker清理與擁有權稽核。

陸地後續：v78正常選取的是士兵，原版教學框接走開選單點擊，未命中ORDERS；意圖誤寫拓荒者已追加勘誤，不覆寫收據。v79先Enter正常關提示再開選單，十列中文命中，七張GUI與中英／缺圖集重播及四側完整原版／存檔通過。v80確認第一Fortify28D的完整讀行／搬運／印字來源，v81獨立欄位量測21px、最長252及316×452安全區通過。規格036補READY，正式前端未改；尚待獨立檢查器、矩陣與普查，完成數維持806，不算Join Colony／Pillage或百科其他入口。

本批稽核命令首次自動核准審查逾時，未執行；改為檔案化短命令重試一次通過。正式來源與v65指紋相同，清冊／報表與v77生成物相同，輸出UID/GID1000:1000；整個工作根沒有root-owned產物或同名.md目錄。Git身分仍wicanr2@gmail.com，未追蹤原版EXE／SAV／封存檔／字型／DAT／PIK／i64。JSON工作清單重新生成並驗證，文件／程式／JSON差異格式通過。所有本批工作已正常結束，由--rm移除；不清理其他專案容器。未commit、push、寫Issue或發布新版，整體Goal仍進行中。

## 2026-10-02：陸地第一Fortify正式收尾與輸入探勘

v82首輪灰色負例因檢查器讀JSON的舊絕對圖片路徑而誤通過，失敗保留；修正共用圖片解析為指定收據目錄與檢查點標籤後，八種偽造拒絕、缺原版SKIP77及船隻／VIEW輸出相同通過。正式前端、圖集及原版未改。42列矩陣PASS，v83普查只新增28D一列，807已顯示／1001待接／89不可達；移除陸地列逐位元組恢復v77，重產及來源／分類反向對照通過。規格036限定CONFORMED，現況及JSON工作清單同步。

正常COLONY03進城裝備士兵的v84回世界仍選船；v85加Space亦未見加入殖民地或新ORDERS清單。保留兩次真GUI與實際輸入，轉以既有KeyReads觀測原版是否消耗鍵字，不猜輸入模式或更改規則。Join Colony／Pillage仍待驗。沒有遠端Issue寫入或新Release，整體Goal仍進行中；批末補Docker及擁有權稽核。

### 同批續驗與停止線

v86唯觀測確認Space確實被原版讀取，輸入及完整RAM與v85一致；說明書第24／105頁證實Space是略過、W才是等待，已追加意圖勘誤。M／W、駐軍職業選單及地圖旗標均未命中Join Colony，不改正式鍵盤或猜單位規則。

v88互動探勘300秒逾時只有局部收據；v90旗標擷取八次皆步數漂移，guard拒絕。保留失敗。v91僅私有擷取原型於截圖時有界暫停該前端PID，finally恢復；十二張GUI與中文重播逐像素相同，十二個共同原版點與四側完整狀態／存檔通過。實際進城並開改名框，交目標181補兩欄字級／來源及正常取消驗收；維持DRAFT及807完成數。準備命令的自動核准逾時未執行，按工具允許重試一次成功，未請使用者重複批准。

本批現況、規格限定CONFORMED、兩目標索引與JSON工作清單已同步。遠端只讀核對#55仍OPEN，未commit、push、寫Issue或發布版本；整體Goal仍進行中。收尾命令另驗工作清單、擁有權、原版指紋及Docker清理。

收尾稽核通過：WORKLIST生成內容與JSON一致，完成訊號驗證通過；正式807列清冊／報表及v65二進位指紋相同。全工作根沒有root-owned產物或同名.md目錄，抽查輸出UID/GID1000:1000。Git沒有追蹤原版EXE、SAV、封存檔、DAT、PIK、i64或字型，文件／程式／JSON差異格式通過。所有本批容器正常結束或由外層逾時移除，主機回查沒有此驗證映像的執行中或停止容器；其他專案容器未動。

交接來源核對：正式清冊的GAME.TXT:@RENAMECOLONY仍pending，原始段落兩行。v91只提供這個未完成來源的新正常畫面，不重新開啟已CONFORMED項目；下一步須核對正文與名稱標籤的原始來源及完整段落覆蓋，不把兩個觀測欄位算成兩個原始來源。

## 2026-10-02：城市改名兩欄正式驗收

完成正常COLONY03讀檔、進城點標題、英文姓名Backspace／n編輯、Escape取消並返回世界。v50九GUI與三側原版點及四側完整狀態／存檔相同；v51實際RENAMECOLONY查詢同輸入終點，v52逐欄字高／基線／最長譯文與超界量測經READY，v53正例及十種偽造拒絕、缺原版SKIP77通過。正式v65、譯文與圖集未改；只新增check_goal181_rename.py及矩陣接線。新檢查器的控制模式、事件前綴與來源工具輸出假設已按實際契約修正，不當作產品缺陷。私有字級診斷首輪錯把姓名重印當新標籤而退出，第二輪相同容器／命令修正後完整通過，舊log保留。

完整43列矩陣PASS，沒有SKIP／FAIL／過期或原版指紋衝突。普查兩次逐位元組相同，808已顯示／1000待接／89無法正常觸發、分母1897，僅RENAMECOLONY完成狀態改變；移除新收據後清冊與報表逐位元組恢復807／1001。其他五列只追加命中或已驗收據。普查首輪夾具假設全部欄位僅改一列而失敗，核對確認是追加命中紀錄；修正狀態／metadata分別核對後同一組收據通過，沒有重跑或挑選結果。矩陣未驗範圍移除已決定的遮擋問題，保留名稱、Join／Pillage等實際待驗項。

規格035／036限定CONFORMED，CONTEXT與生成文件更新，Issue #56維持進行中。沒有commit／push、Issue寫入、新版本或Release。其餘文字、三平台完整交付及推廣片仍待完成。原始像素／素材只留忽略的workplace。重生入口及完整SHA-256見[目標181](docs/goals/181-colony-remaining.md)；Docker清理與工作樹衛生在本批收尾補記。

收尾補驗：rename-layout-v52/rename_boundary_test.go以單一欄分隔符及200次重複中文字驗證真正寬度回退，兩個實際字級仍30／29px，TestRenameMeasuredBoundary通過。首版私有標籤壓力字串含重複分隔符，可能先由缺字回退，已修正audit.go並以純排版量測補證；原版同狀態結論與正式矩陣／普查不變，未因此重跑正常玩家路徑。量測結果JSON指紋未變，boundary-test.log及Go測試同目錄保留。

工作樹衛生通過：Git身分wicanr2@gmail.com、HEAD f6f0ab7作者一致，原版EXE／SAV／壓縮檔／字型／索引／RAM沒有被追蹤，git diff --check扣除既有TSV尾空欄通過。整個工作根未發現root-owned檔或*.md目錄，本輪六個輸出目錄UID1000；正式對話框／字串／適配器指紋沿v65不變。專案驗證映像的執行中及已停止容器均無殘留，沒有全域清理或chown。工作樹既有修改保留，未commit／push或寫入Issue。

## 2026-10-02：正常另存成功提示正式驗收

SAVEGOOD原版折三行而draft只載單行，加上複合描述尚未匹配，導致回原文。私有v55先補完整模板與限定描述回呼，重播完整原版與舊v41相同；證據審READY後才改正式dialog／string／adapter，全部Go回歸通過。正常v56讀COLONY03、另存第一空列00、成功提示及Enter關閉；七GUI／原版點及四側完整狀態、新舊存檔一致。v57原始查詢及DOS建立／寫入由同GUI輸入重生，v58逐欄字高、候選及超界回退通過。來源工具缺模組的兩次失敗修正為v51已驗設定；候選缺起始字級與既有中文狀態欄殘字斷言屬驗證夾具，按正式函式與開框前／後差異訂正，原版與正式排版不改。一次Docker掛載把單引號寫成字面反斜線轉義，誤建空目錄；已用rmdir逐層移除該唯一空目錄，未動原始輸入。

v59正例、十二種破壞收據拒絕及缺原版SKIP77；v60完整44列矩陣PASS、無SKIP／FAIL／過期／指紋衝突。普查兩次與反向逐位元組核對通過，809已顯示／999待接／89不可達、分母1897，唯一完成變化為SAVEGOOD。規格035／038限定CONFORMED，更新CONTEXT／README／工作清冊及生成文件，Issue #56／#61仍進行中。原版素材、存檔與畫面只留忽略的workplace。本輪未commit／push、Issue寫入、新版或Release；三平台完整交付與推廣影片未完成。Docker與擁有權收尾補記於本批後續檢查。

本批收尾：已存檔的correct-candidates.sh在相同工具链重新執行通過，量測指紋不變；三個正式Go來源指紋與目前表一致。worklist write／verify及Git差異空白檢查通過，生成TSV依既有規則排除空欄尾端Tab。沒有原始EXE／存檔／封存檔或workplace輸出被誤追蹤，root-owned檔案與誤建Markdown目錄均0；抽查輸出UID/GID為1000:1000。colonization-verification映像的執行中與停止容器均0，未碰其他專案容器；dosgolem upstream推送仍DISABLED，Git身分wicanr2@gmail.com。

## 2026-10-02：存讀檔槽位來源、同步真因與READY

上一輪為實際進展，SAVEGOOD已正式採用。這輪依知識路由載入規格閘門與文件職責，以目前v55／44PASS／809已顯示為基準。主機gh auth status通過，遠端Issue #61仍OPEN、無留言，未寫入遠端。v56正常讀檔標題因screen-sync-timeout回英文，存檔標題中文但兩份列表因line-no-template回原文；來源事件不當作顯示完成。

v61私有觀測原版標題與槽位：LOADGAME僅安全區邊角一點不同，v62同正常輸入重生兩標題查詢及完整終點。VICEROY唯一EMPTY片段／RAM對應及原始讀取已確認。原版0CAE:00A8於32059113步改邏輯畫布(64,74)，VGA保留130，造成嚴格矩形同步失敗；該點沒有標題墨跡。v63在私有副本縮小標題底緣留白及加入限定槽位描述，完整原版不變；v64補反白重印與仍有效標題保留；v65只採全部已觀測墨跡完整存活的清單，64845000步部分擦除拒絕，避免把關閉時的殘留當整份清單。

v61／63／64／65完整原版終點與正式v56逐位元組相同；v65新舊存檔同字節、兩首屏差異只在新增核准區、六個反白取樣啟用，四個關閉後畫面與正式結果逐像素相同。四欄原版cap高5，候選22～15px選21px；兩清單各160描述候選最長516像素、七種格式拒絕與七種來源生命週期守門通過，1000個ASCII姓名確由欄寬回退0。組合測試不冒稱原版輸入範圍或320條GUI路徑。

規格035／036／038已審READY。正式Go、譯稿、圖集與矩陣未變，完成數仍809／999，EXE合併列表仍pending。下一步為來源綁定空欄值與限定槽位回呼、安全區／生命週期正式實作，受譯稿綁定影響字模重烘，再走新正常GUI、三側／負例、矩陣及普查。沒有把回放當新GUI或把原型當CONFORMED，沒有commit／push、Issue寫入、新版本、Release或公開原始畫面。完整來源指紋、原始位址基準、字級與重生入口見[規格035](docs/spec/035-dialog-overlay-draft.md)及[目標181](docs/goals/181-colony-remaining.md)。

診斷首輪使用錯誤旗標，原版未執行；保留flags-attempt.log，修正為既有--window／--replay-inputs／--window-steps／--checkpoint-steps後在同一工具鏈乾淨重跑。所有Xvfb有trap與有界擁有程序，容器--rm、UID/GID1000:1000、網路關閉。工具腳本均歸入已索引的收據目錄；本批Docker清理、Git與擁有權自檢另追加。

本批收尾：worklist write／verify與Git差異空白檢查通過；原版輸入／存檔／workplace產物無誤追蹤，root-owned與誤建Markdown目錄均0，抽查規格與收據UID/GID為1000:1000。colonization-verification執行中及停止容器均0，未動其他專案容器。Git身分與最近作者均wicanr2@gmail.com，未新增commit。正式普查SHA仍f7c525c9c7a63c3a9318f757dd75aa397984b6c579a7f83f27f578d9c0e10277。新收據與腳本為一次性研究入口，重生須使用乾淨輸出與只含初始COLONY03的scratch，不從生成COLONY00後的scratch重播；不得覆寫既有收據。

## 2026-10-02：槽位 READY 正式接入與限定驗收

依規格閘門路由及既有READY接入空槽專用來源驗證、逗號描述回呼、8／10列上下文、LOADGAME底緣安全區與完整墨跡／標題保留。正式v66完整Go回歸通過。字模首跑遇到舊驗證器只接受TXT完整行，依READY僅開放唯一EXE片段及零結尾邊界；保留失敗log，用同一固定rich2-py重跑，全部譯稿及字模通過。GUI v67是新正常讀03、存空列00及關框，含兩張移入槽位取樣，不把移入畫面稱作不同反白已證實；沿既有v65實際重印及生命週期證據。源端v68同輸入重生，三側及v55程式同現行譯稿／字模對照完整原版及存檔相同。檢查器首輪引用來源探針沒有匯出的save_file_ops欄位，屬腳本問題；改用實際匯出的查詢／讀取及五側存檔字節，沒有補造原版DOS寫入記錄。

v69正例、16個破壞性反例拒絕及缺原版SKIP77；v70矩陣45PASS，無略過／失敗／過期／指紋衝突。普查兩次及反向逐位元組相同，815已顯示／997待接／89不可達、分母1901；兩標題提升與四筆新實際觀測，舊第三列合併EXE觀測保持pending。規格035／036／038限定CONFORMED，更新唯一目前狀態、生成清冊及封裝字模來源。譯稿與字模為本機中間物，沒有commit／push、Issue寫入、新版、Release或公開新原版畫面。整體Goal保持active，其他997待接、未完成玩家入口及三平台完整版／影片繼續。

v55程式對照命令使用slot-gui-v67的新GUI輸入、九取樣步數及終點88600000，scratch初始僅COLONY03；字模與draft均現行v66，輸出baseline-v55，命令於該收據目錄由本批另存重生腳本。Docker與UID/GID自檢於本批最後追加。

本批收尾：新對話框／字串圖集與舊實際GUI圖集的字模像素完全相同，只更新整份譯稿綁定；封裝接受現行綁定、拒絕舊圖集。封裝反例腳本已改為捕捉實際ValueError並核對錯誤訊息，結果保存在slot-census-v70/font-binding-check.json。文件同步腳本初次誤用matrix.md，已按實際verification-matrix.md修正並完成，沒有留下兩份現況。worklist write／verify與Git差異空白檢查通過，既有TSV空欄尾端Tab按原規則排除。原版EXE／存檔／壓縮檔／字型／索引及workplace輸出沒有被誤追蹤；全工作根未發現root-owned檔或Markdown目錄，抽查程式、生成清冊、二進位及新圖集均1000:1000。掛載本專案的執行中與停止容器均0，隔離dosgolem的upstream推送仍DISABLED，未清理其他專案資源。未commit／push或修改遠端Issue；Goal保持active。

## 2026-10-02：歐洲港口與報表正常路徑續驗

- 接手v66基準，原版只讀，主機gh auth與Issue50～61回讀保持OPEN；沒有對外寫入。命中規格閘門、文件職責與README路由，均依現況與新收據前進。
- v71新正常GUI取得港口及F2～F10，v72觀測119字元、880個右側47及466個下方128陰影點，全部符合相對原版前景一像素位置。lineRoles把128誤當次色導致灰色購買列回退；v73私有候選與25姓名／四數字量測、未知與混色反例後審READY，v74正式接入兩處陰影分類及兩個精確報表模板，完整Go測試PASS。
- v75從正常主選單讀COLONY03重新操作，26GUI逐像素與中文重播相同；原文／缺圖集／v66對照及v76觀測六份原版終點、26原版點相同。五份存檔不變。新增像素限三欄，23其他畫面相同；字串新圖集與v66字形全等，只變模板綁定，封裝引用及過期拒絕同步。
- v76 check_goal181_europe正例109欄、十二種偽造拒絕、缺原版77；v77矩陣46PASS、普查兩次與反向逐位元組通過。最新850已顯示／995待接／89不可達、分母1934。只有兩舊清單pending→shown；33新增是實際GUI顯示的組合或片段，不是25合成姓名。
- 驗證夾具兩次失敗在F3-b；實際為已切換的空議會房間，查回規格路由／原版狀態後同容器乾淨重跑通過。凍結清冊最初包含關閉後未量測海上Jamestown，按原定港口與報表範圍排除。均未改原版或猜補來源。
- 三個報表城市名仍因欄寬回原文，購入成功、其他局勢、Join／Pillage及其餘中文化與三平台／影片未完成；Goal維持active。沒有commit、push、Issue寫入、版號或Release。Docker最後衛生檢查另記本批收據，所有新增輸出UID1000，原版畫面與存檔只留workplace。

2026-10-03收尾稽核：worklist write／verify通過；16份正式指紋及生成普查逐位元組一致。全工作根root-owned檔與Markdown目錄均0，Git未追蹤原版EXE／SAV／封存檔／字型或workplace，抽查1000:1000，隔離dosgolem推送仍DISABLED。Git差異檢查除既有生成TSV的空尾欄通過；colonization-verification執行中及停止容器均0，未動其他專案資源。完整結果及重生腳本已掛目標181入口。


## 2026-10-03：報表城市名原型與正常購入續探

依規格路由與grilling視覺取捨入口，建立v78可丟棄副本，只加三次文字底圖觀測。正式來源、譯文、圖集、46PASS矩陣與850／995普查不變。原版完整終點與26畫面和v75一致，固定字模A22px單行／B15px雙行已量測並展示；版面選擇待答，尚未READY。量測首輪把VGA6-bit色盤當8-bit RGB而拒絕，核對既有adapter的左移2位及右移4位公式後，同一映像／命令重跑通過，沒有重跑或挑選原版結果。準備腳本首次把replay.sh寫入容器暫存，已改寫既有輸出目錄並保存重生入口。

同步開啟不依賴版面選擇的v79正常GUI：讀COLONY03進歐洲，選實際可負擔的500$砲台，觀測後續。來源、字級與同狀態尚待取得；不提高普查，也不把可玩探勘稱正式驗收。沒有commit／push、Issue寫入、版本或Release；Goal保持active。


## 2026-10-03：砲台正常購入收據核對完成，尚未採用

v79九張正常GUI及v80逐欄／源端重播取得@REALLYBUY確認、是／否、國庫1000$→500$與碼頭砲台。三側原版及觀測完整終點／存檔相同，四側九原版取樣、GUI與中文／觀測畫面全等；兩欄30px及超界拒絕。核驗腳本先誤認GUI有逐點CP、final有RAM欄位，回讀路由及既有europe檢查器後修正；另只在匹配candidate_id時讀生命週期步數，避開其他沒有step的事件。收據未重跑或挑選，正式來源／圖集未改。

規格035本日僅DRAFT證據，不把@REALLYBUY的pending改shown；下一步為名稱／數值排版邊界、可重生限定檢查與反例、矩陣及反向普查。城市名A／B選擇仍待答，其相依正式實作暫停；其他原定中文化工作繼續。工作清單與唯一現況已同步，完整Goal保持active，沒有commit／push、Issue寫入或Release。

本批收尾：worklist write／verify、Git差異格式檢查及16份正式指紋核對通過，生成清冊與850／995快照完全相同。全工作根root-owned檔與Markdown目錄均0，Git沒有追蹤原版素材或workplace；輸出1000:1000，隔離dosgolem推送DISABLED。最後核對colonization-verification的執行中及停止容器均0，沒有清理其他專案容器。


## 2026-10-03：正常砲台購入正式驗收採用

v81六種單位／四金額24組實際字模量測通過，全部30px、最長551px；未知單位及1000位數字拒絕。測試初兩次分別為Go陣列語法與未使用匯入，回查規格路由後修正私有測試、保存log，同一工具鏈／命令重跑；正式程式與原版收據未改。v82凍結三個GUI仍啟用欄位，公開check_goal181_purchase正例、13種破壞收據拒絕與缺原版SKIP77通過；初輪把英文控制自己送入僅接受中英不同側的same_state，依共用契約修正，不當作產品缺陷。

v83完整47列矩陣PASS，零SKIP／FAIL／過期／指紋衝突。普查兩次與移除新列逐位元組相同；852已顯示／994待接／89不可達、分母1935，唯一既有提升REALLYBUY，新增實際500$港口標題EXE:e9b353ec7941；六個其他來源只追加命中metadata。24合成量測不算原版命中。規格035／036／038限定CONFORMED，現況、README及生成文件／工作清單同步。

GitHub主機auth及Issue #56只讀核對通過，仍OPEN，未寫入Issue。正式v74來源／二進位／譯稿／字模沿用；沒有commit／push、版號或Release，原版素材、存檔及畫面只留workplace。城名版面仍待答，其他原定中文化、三平台完整交付與影片繼續；Goal保持active。Docker與擁有權最後稽核另補本批記錄。

本批收尾：worklist write／verify及Git差異格式檢查通過，15份正式指紋與生成矩陣／普查逐位元組相同。全工作根root-owned及Markdown目錄均0，Git沒有追蹤原版素材或workplace；抽查1000:1000、Git身分wicanr2@gmail.com，隔離dosgolem推送DISABLED。colonization-verification執行中及停止容器均0，未動其他專案資源；Goal仍active。


## 2026-10-03：正常未建碼頭正文正式採用

v84點工作者實際開職業清單，拖到水域沒有未建碼頭提示；v85改從職業清單選Fisherman，正常觸發NODOCKS。v86原版來源及逐欄字級／超界觀測、v87限定單欄驗收、13種破壞收據拒絕與缺原版SKIP77通過。負面測試首次在保存結果時引用不存在的/task腳本，改用__file__重跑同一工具鏈與案例，分類為收據腳本問題。共享購買檢查器只增加固定呼叫參數，預設守門保留；原三欄購買正例與13種負例另存v87回歸。正式顯示程式、二進位、譯稿與字模不改。

v88全矩陣與普查首次分別超過220／120秒的外層界限；已成功的兩次普查保留，重跑未完成的全矩陣及反向普查時改為逐項執行、相同工具鏈與驗收命令，保存timeout-attempt.json。程序逾時不當成產品缺陷。

v88全矩陣48PASS，零失敗、略過、過期及原版指紋衝突。普查兩次及移除新列反向逐位元組相同，853已顯示／993待接／89不可達、分母1935，僅NODOCKS升shown，無新增來源。八GUI、五側完整原版、四側八共同取樣、來源查詢與存檔一致。v86右鍵工作者實際開百科，未當成COLONYUNIT命中。規格035限定CONFORMED，現況與生成文件／工作清單同步。城名決策尚待答，其他中文化及三平台／影片繼續；Goal保持active，沒有commit、push、Issue寫入、版號或Release。原版畫面與存檔只留workplace，Docker與擁有權最後稽核另補本批記錄。


## 2026-10-03：未建碼頭收尾與士兵單位面板續查

v88稽核通過19份正式來源／產物雜湊及生成文件逐位元組一致，root-owned、錯誤md目錄、被追蹤原版素材均0；抽查1000:1000，dosgolem upstream推送DISABLED，Git身分正確。48PASS與853／993正式採用後，未建碼頭驗證容器均清理。

v89沿正常選任士兵後點圍欄，仍開職業清單，不計單位選項。查第三波說明書Image028第41頁後，v90改切右下單位面板並點士兵，正常開出標題及警戒／登船、駐守、不做更動三列原文。v91原版兩次查詢及完整RAM相同，逐字觀測三列cap8／行距12；11GUI與未改顯示的觀測副本全畫面、完整狀態／RAM／讀檔相同。這不是三側或新覆蓋驗收，普查不加數。

既有匹配器把相鄰變數拆成S與oldiers，窄Go重現通過。測試首次缺DISPLAY導致套件GLFW初始化失敗，補有界Xvfb後同一映像／命令乾淨重跑，保留失敗log，不列產品缺陷。正式Go、二進位、譯稿與圖集不改，規格035追加DRAFT，下一步先做已取證士兵標題及當次三列的可丟棄原型、逐欄候選字級與回退守門。未經READY不接正式路徑。城名決策及其他既定中文化／三平台／影片仍待完成；未commit、push或寫入Issue。最後Docker與擁有權稽核另補本批記錄。

本批最後稽核：v88正式19份雜湊與生成文件一致，root-owned／錯誤md目錄／誤追蹤原版素材均0；擁有權1000:1000，上游推送DISABLED，Git差異檢查除生成TSV空末欄格式外通過。主機docker ps -a確認沒有殖民帝國專案的執行中或停止容器，其他專案資源保持原樣。Goal保持active，未將DRAFT或窄重現計入完成數。

## 2026-10-03：士兵標題與三列正式候選

v92原型已翻譯士兵標題及當次三列，但中文字覆蓋左側單位圖示。保留失敗原型，v93改按原版文字墨跡起點縮安全區，並以完整原版NAMES.TXT及UNIT資料列片段驗證完整名稱。v93原版11取樣／完整狀態／存檔相同、兩核准區外及圖示不變；22個名稱實際字模量測、來源與未知／缺字／超界回退測試通過。

名稱測試首次原版來源掛錯，結果SKIP而非通過；已確認並逐一清除錯誤掛載產生的三個空root目錄，修正來源後同工具鏈／同測試乾淨PASS。規格035／036按審查證據升限定READY，v94正式最小修正、完整Go回歸、go vet及建置通過。譯稿及圖集不改。

v95新正式正常GUI已完成士兵選任、右下單位面板開關與返回世界。重播首次缺DISPLAY而啟動失敗，保留replay-zh-no-display.log與初始scratch，補有界Xvfb後同一命令重跑。正式驗收、矩陣與普查尚未完成，目前仍48PASS／853已顯示。Goal保持active；沒有commit、push、Issue寫入、新版號或Release。Docker及最後擁有權稽核待本批收尾補記。


## 2026-10-03：正常士兵標題與當次三列正式採用

v94正式完整Go回歸、go vet與22個名稱量測通過。v95新正常GUI與中英重播全等；三側批次外層300秒在缺圖集側完成前逾時，已完成兩側保留，部分neg-noatlas收據保存於neg-noatlas-timeout，只重跑未完成的一側並通過。v96由正式來源生成觀測首次引用不存在的diagPixels而編譯失敗，保留audit-with-extra-field.go.txt／build-attempt.json，移除多餘像素紀錄後同工具鏈乾淨重跑。這些是環境／收據生成問題，沒有因此改產品或挑選測試結果。

v96限定檢查兩欄、11GUI、六側完整原版終點、五側11共同取樣、原版來源、所有COLONY03、單位圖示及兩核准區外通過。19種破壞收據拒絕、缺原版SKIP77通過；v97全矩陣49PASS、零略過／失敗／過期／指紋衝突。普查兩次及移除新列反向逐位元組相同，855已顯示／991待接／89不可達、分母1935。只提升COLONYUNIT與UNITOPTIONS，無新增來源；段落計數只代表當次士兵標題與可見三列，不外推完整五列或其他單位。

規格035／036限定CONFORMED，唯一現況、README穩定摘要與生成文件同步。字模及譯稿不改；主機gh auth通過並讀Issue #56，仍OPEN且沒有留言。其他中文化、城名版面、三平台完整版與影片繼續；Goal保持active，未commit、push、寫入Issue、定新版本或Release。最後擁有權／原版誤追蹤及Docker清理另補本批稽核。

本批最後稽核：v97正式31份指紋及生成文件逐位元組一致，root-owned／錯誤md目錄／誤追蹤原版素材均0；抽查擁有權1000:1000，dosgolem upstream推送DISABLED，Git身分及差異檢查通過。主機完整docker ps -a及已用研究／驗證映像核對，本批容器全部退出並刪除，其他專案資源保持原樣。Goal保持active，全文中文化、剩餘單位狀態、城名選擇及三平台／影片未完成。


## 2026-10-03：正常駐守後清除命令三列正式採用

v98～v103正常駐守後三列來源與逐欄量測、單一清單區原型通過，規格036限定READY後接入v105正式。完整Go回歸首次碰到v94歷史測試仍把Clear orders列為未驗，保留tests-before-new-state.log，依新證據只更新v105該負例；Move to front與未知文字拒絕保留，新增來源正例另驗。更新腳本首次清單順序不符而未改檔，其後重讀實際內容。乾淨重跑完整Go／go vet通過。v94歷史證據不改。

v106新正常GUI、v107中文／原文／缺圖集／v94舊正式、逐欄與原版來源均完成，六側完整原版終點、五側13共同取樣、13GUI逐像素、來源、存檔與圖示通過。只改駐守後清單區，其他12張不變。19種破壞收據迴圈首次在最後自複製腳本時SameFileError，修正執行入口相同時略過複製後同工具鏈乾淨重跑，19種全拒絕；分類為驗證腳本問題。缺原版SKIP77通過。

v110全矩陣50PASS、零失敗／略過／過期／原版指紋衝突。普查兩次及移除新列反向逐位元組相同，855／991／89、分母1935保持現況，UNITOPTIONS只增加已驗駐守後三列收據，不增加來源完成數。完整命令外層回傳124，全部結果已產出，追加短檢查確認50PASS與重生／反向逐位元組相同；pipeline-completion.json保存分類，不重跑已完成工作。規格036限定CONFORMED，目前狀態表、README與生成文件同步。譯稿及字模不變；v111已正常抵港進城，船隻選項仍探勘，未驗SHIPOPTIONS。城名決策及其他中文化、三平台／影片繼續，Goal保持active；沒有commit、push、Issue寫入、版本或Release。最後衛生稽核另補本批記錄。


v99～v114船隻正常路徑續查：Go to Port選Jamestown、原版回合推進至1497春再點城市，v111已實際進有船停泊的Jamestown。v112首次點船為抵港教學，v113正常Enter關閉後再點船才開Caravel標題與警戒／下錨／不做更動三列。v114原版TUTORIAL12／COLONYUNIT／SHIPOPTIONS查詢、13GUI與觀測全畫面及完整原版／存檔一致，來源探針RAM相同。規格035／036追加限定DRAFT；新教學、Caravel綁定與船隻三列仍待原型，不改正式Go、譯稿、字模或50PASS／855。準備與操作入口都在目標181；未公開新增原版畫面或資料。

本批最後稽核：v110正式38份來源／產物指紋與生成矩陣／普查逐位元組一致，工作清單verify通過，root-owned／錯誤md目錄／誤追蹤原版素材均0；抽查1000:1000。主機Git身分wicanr2@gmail.com、隔離dosgolem推送DISABLED，差異格式檢查除生成TSV空末欄外通過。主機完整docker ps -a已核對，本批研究／驗證容器全部退出並刪除，未動其他專案資源。Goal保持active；正式50PASS／855，新船隻與教學只保留DRAFT，不以來源觀測冒稱中文完成。


## 2026-10-03：船隻原型與教學取樣修正

命中復古遊戲規格閘門與文件職責入口，沿既有目標181與規格035／036。v115私有Caravel名稱綁定及SHIPOPTIONS三列30px通過13圖安全區／完整原版；兩種士兵11／13圖的來源鍵、畫面、取樣及存檔完全相同。23個原始UNIT名稱的實際字模與來源拒絕測試通過。沒有正式Go、字模、譯稿、矩陣或普查狀態改動，50PASS／855保持現況。

v116加入私有TUTORIAL12城市名稱回呼。首次測試把match回傳的字串當成模板指標，go vet拒絕；修正測試API用法後同容器、同test.sh乾淨通過，失敗vet-before-test-api.log保留。原型正文30px五行能排版、原版完整狀態不變，但正常13圖均未顯示教學，visible-check-before-gui.py拒絕。state-only-summary.json只採狀態一致，沒有中文命中。原版進城自動開教學，下一次點船隻已關閉，v117改先等教學抓圖再正常關閉及船隻選單，仍DRAFT。

中間物只留workplace；未commit／push／Issue寫入／發行。Docker有界容器及擁有權於批次結束再核對，尚不作已清理聲明。


v117改等待後已抓到正常中文抵港教學；v120重播三側、v118教學未接基準及原版來源完成。原版在此正常路徑新增COLONY09，所有側含原版來源探針逐位元組相同，初始03不變。原型舊存檔只允許03的假設不適用；check.py改精確03／09清冊後再比對GUI，仍拒絕一張海上過渡圖不對齊。verification-limit.json記為INCOMPLETE_GUI_ALIGNMENT，13／14GUI相同，教學可見但仍DRAFT，不提高完成數。可能的status發布與Draw先後差異是強推論，未假稱根因已實機證實。


## 2026-10-03：正常港口輕帆船兩欄正式採用

依規格035／036 READY接入v118，完整Go／go vet與23名稱實際字模、兩種士兵原型回歸通過。新正常v119共14GUI及v121六側完整原版、五側14取樣、來源與03／原版新增09、船隻圖示及核准區外通過；21種破壞收據及缺原版SKIP77通過。驗收函式新增明確案例存檔清冊選項，舊案例預設03不放寬；舊案例反例初次忘掛/game，保留INVALID_TEST_ENVIRONMENT，補掛原版後確認已先通過舊收據，再因未知新增存檔拒絕。GUI準備初次把非詳細go test的ok輸出當成必須含PASS，未建立GUI目錄；修正成功收據檢查後同設定重跑，不列產品失敗。

v122全矩陣51PASS、兩次普查及移除新列反向逐位元組相同。1935列中856已顯示／990待接／89不可達，只提升當次三列SHIPOPTIONS；不外推完整六列、其他船隻或教學。現況表、規格、穩定README與唯一機器worklist同步，WORKLIST由工具生成。教學私有v120保留13／14GUI對齊限制，不提高數字。未commit／push／Issue寫入／新版本／發行。收尾稽核與Docker清理另保存hygiene-summary.json。

收尾稽核通過19個正式指紋；root-owned檔案、誤建.md目錄與被追蹤原版素材均0，擁有權1000:1000。主機docker ps -a的colonization篩選未列容器，本批有界容器均已移除；映像未重建，未作全域清理。Git差異空白檢查通過，既有TSV空尾欄不納此檢查。


## 2026-10-03：正常抵港教學與截圖同步正式採用

私有v123～v125正常14GUI及原版審查通過後，按規格035／013 READY接入TUTORIAL12名稱回呼與畫布指紋同步。v126完整86個Go測試無SKIP、go vet、實際名稱字模及同步反例通過；新正常v127共14GUI與v128六側完整原版、五側14取樣、來源及本次03／新增09存檔全等，只教學安全區改變且正常Enter關閉無殘留。23種破壞收據全部拒絕，缺原版SKIP77。

v123初次工具匯入路徑、v124初次Xvfb未就緒、v127初次暫停helper漏proc均已定位並修正，失敗紀錄留原位置或已索引的失敗目錄。helper已補實際雙執行緒停止／恢復測試；首次名稱測試將64個連續W錯當必須排入，改按原有回退契約驗證，未放大安全區或改排版規則。v125固定本次獨立來源清冊後，原來錯用舊輸入09的檢查通過；不重跑取樣或挑圖。

v129全矩陣52PASS，兩次普查及移除新列反向逐位元組相同；857已顯示／989待接／89不可達，只提升抵港TUTORIAL12，不外推其他教學或裝貨結果。現況、規格、穩定README與JSON同步，WORKLIST由工具生成。未commit／push／Issue寫入／新版本／發行。Docker與權限收尾結果另存hygiene-summary.json。


v128外層wrapper因執行中被編輯，在四側重播正常完成後中止；目前語法檢查與四側完整原版／14取樣獨立核對均通過，completed-replays.json只標已完成四側。後續觀測／來源由相同容器工具鏈乾淨執行，最終公開限定檢查逐像素核對全部子結果通過；不將首次整批命令記為PASS。

收尾檢查通過：21份正式指紋一致，無root-owned、異常.md目錄或原版素材誤追蹤，輸出UID/GID為1000:1000。主機docker ps -a以專案名稱與驗證映像核對，均無執行中或停止容器。差異格式檢查通過，TSV既有空欄保留。


## 2026-10-03：港口載貨與下錨選單正式採用

v130～v134正常裝卸貨與下錨／清除命令探勘取得原版來源、23GUI與完整原版／存檔一致。v135私有原型87Go／go vet與兩種士兵24圖回歸通過，只有載貨四列及下錨三列清單安全區改變；按規格036限定READY接入v136，正式新正常v137／v138六側完整原版、五側23取樣與來源／存檔／GUI指紋通過，關框無殘留且船隻圖示不變。22種破壞收據拒絕，缺原版SKIP77。

私有準備的註解定位與量測helper重名均已定位並修正，未執行原版前的失敗輸出保留；同設定乾淨重跑。正式Go與譯文、字模及原版資料之外，只改已驗完整選單匹配，未猜裝卸規則。v139矩陣53PASS，857／989／89不變，只補SHIPOPTIONS條件狀態收據；兩次普查與移除新列反向逐位元組相同。現況、規格、README、JSON同步，WORKLIST由工具生成。未commit／push／Issue寫入／新版本／發行。Docker與權限收尾另存hygiene-summary.json。


v139首次摘要檢查誤把未採用命中的附註也限制為SHIPOPTIONS父段落，且誤用含位移的父鍵；原始腳本保留。全矩陣、兩次普查及移除新列反向原已通過，未重跑；resume-metadata-check.py重新審查既有輸出，完成狀態零改變、SHIPOPTIONS只增加本次receipts，其餘8列只增加本次reached_unapplied。scoped_unverified由20至27是本限定案例排除的觀測附註，不算新增缺譯或完成數。

港口短標題的Loading: Caravel已由正式v137卸貨後真GUI放大辨讀確認，與原版0D21:00C6、線性175614的字串觀測及墨跡位置一致。先前將像素讀為Harbor的說法是辨讀錯誤，後續不另開Harbor印字路徑。放大本機像素留v138/view-loading-crop.png，原始圖在v137/gui-colony.unload-all-command.png；只作辨讀，不當中文收據。Loading來源片段與角色綁定、移貨訊息目的地的typed來源仍待驗。


v139收尾正式21份指紋、UID/GID 1000、root-owned／錯誤.md目錄／誤追蹤原版素材皆為0，隔離dosgolem版本與upstream禁推不變。主機docker ps -a依專案名稱及驗證image兩項核對均空；無留置容器。Git差異檢查通過，TSV既有空欄保留。


## 2026-10-03：貨物提示原型審查與正式接線

- v142唯讀組字來源及v143正常同名城市26GUI／v144來源角色補證通過。v145私有四模板95案例，v147核對73張GUI，仍有按住Loading原文限制。v148窄例外104案例；v151普通句子隔離105案例、go vet及同步擷取測試通過。v149新正常24GUI按住提示中文；v150五側完整原版／各取樣／存檔、同名城市26圖及與v145差異限定Loading區通過。
- 環境分類：v145第一次測試缺/game掛載，原版測試skip及教學量測讀取失敗；修正唯讀掛載後同test.sh乾淨重跑95案例、零skip。v145兩次400秒牆鐘逾時沒有終點收據，保留，不算PASS。v146外層500秒逾時，但已寫完24GUI及終點；只驗完成檔案完整性，不宣稱外層命令通過。v147依工具入口修正逾時預算後各側exit0，原命令收據保留。
- v147初版檢查器誤用v138原始畫面路徑；既有原始檔實際在v137。修正驗證路徑後核對通過，不重跑或修改遊戲。容器沒有/usr/bin/time，正式工作前改用Bash time，沒有把工具缺件當產品缺陷。這輪第一次來源掛載存在性檢查曾把單引號寫成字面跳脫序列，exit1且未掛載；正確路徑確認後才掛原版。
- v152依規格038限定READY接入四個貨物來源角色模板與完整Loading提示按住例外。正式105Go案例、go vet、同步擷取測試及乾淨建置通過。固定rich2-py／Cubic 11重烘字模，與v74字形、字集及各字級完全相同，只有新模板綁定改變。舊歐洲量測fixture改用原v73模板與v74圖集配對，沒有重寫歷史收據。
- v153新正常GUI與v154正式獨立驗收進行中；此checkpoint未提高53PASS／857，也未稱全文中文化、整局可玩或發布。先前工作樹與原版輸入保留。Docker只用有界--rm、非root、原版唯讀；本批運行中的GUI驗收容器完成後需核對清理，尚不記最終清理PASS。


## 2026-10-03：四個貨物欄位正式收尾

- v152正式來源105Go案例及go vet通過；新v153正常24GUI、v154五側完整原版／24取樣、GUI畫布指紋、四安全區、缺字模原文回退與所有存檔通過。來源RAM／存檔與前端相同；26張同名城市回歸原版及畫面全等。四欄22／20px、各自cap高5及原安全區量測通過，按住例外只放行完整未遮擋Loading提示。
- 公開檢查器沿tools/check_goal181_shipcargo.py --cargo-messages，審查清冊SHA-256 a497850bfb01f4b53f89009dbce7a078bb19de45700ff1e490075e51ac951716；23個破壞收據拒絕，缺合法原版SKIP77。新工具不改原船隻清單驗收入口。
- v155完整矩陣54PASS，零SKIP／FAIL／過期／原版指紋衝突。普查兩次一致，移除新列逐位元組回到舊1,935列／857；採用三個固定來源片段及四個正常訊息變體後為1,939列／864已顯示／986待接／89無法觸發。限定規格038 CONFORMED，Issue #56本機項目仍in_progress，不寫遠端Issue或宣布全部中文化。
- tools/build_window_prototype.py原來源雜湊仍停在較舊適配器；更新為本次已驗SHA後，經原入口組裝、go vet、Go測試及建置通過，Go module格式不改。正式GUI收據仍使用v152二進位。字模綁定、CONTEXT唯一現況、README穩定摘要、字型入口、生成矩陣／普查與JSON工作清單均更新；WORKLIST只由工具產生。
- git diff --check的報告來自TSV結尾空欄位的tab，保留資料格式；排除TSV後檢查通過。沒有修改原版、dosgolem母本、公開發行、push或commit；Docker最終清理與擁有權另由本輪hygiene-summary.json記錄。


本輪最終衛生檢查PASS：工作根find未見root-owned檔或*.md目錄，v152～v155輸出與公開修改檔UID／GID皆1000／1000，正式文件雜湊一致，穩定組裝的adapter／strings與正式來源逐位元組相同。主機git未追蹤workplace、dist-all或兩份原版輸入；本批驗證、字模與GUI容器均已--rm移除，沒有留下運行中或停止的本批容器。隔離dosgolem提交仍b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8，upstream推送DISABLED；Git身分wicanr2@gmail.com，未commit／push／改遠端Issue／發行。


## 2026-10-03：貿易路線來源、命名反例與限定READY

- 遠端#50～#61以主機gh重新核對仍OPEN，沒有寫入。v156海上22／v158陸上13正常GUI，v157／v159未改顯示的完整原版／像素／存檔全等。原版順序確認為第一目的地、Sea／Land、命名、第二目的地、編輯器；早期推定與原始截圖檔名保留並追加勘誤。
- v160片段觀測空紀錄源於WatchReads單一回呼被後掛取代，不能說原版未讀。v161合併回呼後九片段與兩貨物查詢正常命中、來源RAM與存檔一致；來源／字級審查通過，探針只有RAM，不冒稱完整CPU。
- v162私有111Go、v164欄位隔離112Go／go vet；v165兩側35GUI、六側原版／取樣／存檔與核准像素／缺字模回退通過。v162初次缺DISPLAY為環境失敗；v165檢查器逐項STRING假設與第二次港口清單分類訂正後通過，未放寬矩形或遊戲守門，原收據保留。
- v166正常玩家路線名EDIT TRADE ROUTE 1與新COLONY00，v167共21GUI、六側完整原版與兩存檔全等。新標題只在原生欄位翻譯；v162多出的中文只在名字欄。規格035／038據此升限定READY，既有城市角色回呼與未知名原字保留，不改原版輸入或存檔。
- v168正式112Go、go vet、抓圖同步及固定字型烘製通過。字集與所有字級形狀逐位元組同v152，只改正式模板綁定。穩定組裝入口來源指紋更新並準備獨立建置；新v169／v170海陸正常GUI與v171獨立驗收進行中，不稱CONFORMED或增加54PASS／864。
- 本輪仍保留既有工作樹，沒有commit／push／Release／公開新原版像素。Docker均非root、有界且原版唯讀；正在執行的正式GUI容器待完成後再記最終清理。


## 2026-10-03：第一海陸貿易路線限定收尾

- v168～v172正常40GUI／六側原版與存檔、24破壞拒絕及候選普查879通過，收據保留。來源鍵校正只把兩CARGO來源映射到既有完整段落鍵，不放寬唯一來源規則。
- 收尾前識別港口文字回呼缺列身分；原版正常觀測確認母港第0列，同名城市可建立性仍未知。v173私有113Go、v174正常40取樣及原版／存檔／中文像素同v168後升限定READY；正式v175只向完整清單行傳索引，其他回呼維持。
- v173首輪漏掛/game造成來源測試失敗／skip，補掛後同命令乾淨113Go及go vet通過，保留tests-missing-mount.log，分類環境。正式v175與穩定入口113／107Go、go vet與建置通過。v176／v177重走正常40GUI與Save Game，v178各六側完整原版、所有共同取樣及存檔全等，中文GUI與正式／觀測逐像素相同，新增差異僅核准區。原生標題與同文字路線名分離；玩家名稱原字。
- 公開checker兩側、25破壞拒絕、缺原版SKIP77；v17956PASS與兩次／反向普查通過。採用1943項／879已顯示／975待驗／89不可達。規格035／038限定CONFORMED，Issue #56仍in_progress，全文、三平台與發行未完成。
- 程式SHA-256 853fbbdb77b00452850844614f7fa7425f72c69bc841b04c5b88273eb0f06e6d，清冊ae74120db1d7534117e003d80f72978b9df57282fe976c110a0a408912512cf4。CONTEXT唯一現況、README、字型入口、生成普查／矩陣／WORKLIST同步。沒有commit／push／遠端Issue寫入或新公開原版素材；最終擁有權及Docker清理另由v179/hygiene-summary.json記錄。


## 2026-10-03：第一路線城市欄與改印生命週期

- v180唯讀觀測確認首欄四列、x115邊線、兩Jamestown原版face與cap5，22～15px量測及長文回退；首輪把表格外背景誤當額外列，修正檢查後完整原版／存檔／GUI相同。
- v181～v182私有候選發現改選London後舊中文殘留：未翻譯字串跳過str.add，暫停覆蓋可由仍存的原像素重畫。失敗圖片與檢查保留。v183～v184改在翻譯前移除舊項，118Go與六次重播、40取樣／原版／存檔／字級／限定像素通過。漏掛/game及檢查器自複製是環境／腳本問題，補正後同命令乾淨重跑；保留修正前檢查入口。
- v185～v186改印資格收緊為完整列前綴與原版起點，數字／單字母未知值可移除舊覆蓋，對話框錯誤位置不能移除。119Go與同正常海陸輸入六次重播通過；合成邊界不稱正常原版命名驗收。
- READY後正式v187／穩定入口119／113Go與vet，v188／v189新正常40GUI及Save Game；v190各六側完整原版、全部存檔與原版取樣相同，GUI／正式／觀測像素相同，只有首兩城市欄新增中文，London改印與刪除無殘留。公開兩側、25破壞拒絕、缺原版SKIP77，v19158PASS及重複／反向普查通過。採用1945項／881已顯示／975待驗／89不可達。
- 程式526d83ad297b46c63c240255b6cd6b8193d56a3b93ec00ef9d19aab651b36c88，清冊a1c623fa4d4fd0fb2743dce01c8616fca8a9bd61f6509e0f5e8949b1438e5602。唯一目前狀態、規格038、README、字型入口及生成矩陣／普查／WORKLIST同步；Issue #56繼續進行。沒有commit／push／Issue寫入或新公開原版素材，最終擁有權及Docker清理見v191/hygiene-summary.json；全文、三平台與發行未完成。

- 初輪矩陣56PASS／2FAIL是新檢查器缺少final_step／final_memory_sha256介面。修正只由已核對的完整control終點補欄位；修正前矩陣保留，修正後公開兩側、25破壞反例、缺原版與完整矩陣／普查皆重跑。封裝腳本改取v187字串圖集，六份譯稿與字型綁定通過，舊v74圖集被拒絕，未建立封包。

- 收尾核對：生成普查／矩陣與採用檔逐位元組一致；普查1,945列均有10欄。git diff --check的TSV尾端tab是空末欄分隔符，保留格式；排除TSV後無空白錯誤。主機Docker檢查確認本輪驗證容器全數移除，沒有停止或執行中殘留。


## 2026-10-04：歐洲碼頭六組與購船標題

- v192～v194正常購船16GUI與原版／存檔／來源／唯讀字級全等，確認舊港口中文殘留根因。v196～v198正常狀態33GUI、六種原版清單、11次ARMOPTIONS查詢與原版／存檔全等；固定點擊在短清單會改命中位置，檔名只留原探勘意圖。v197補固定Loading／Caravel組字來源，不以字面相同代替角色。
- v195／v199／v200私有候選123Go、33狀態與16購船取樣、完整原版／存檔／安全區與缺圖集通過後升限定READY。三列工具清單用原先保留的native149強調，其他lineRoles不改。首次缺圖集exit143部分收據保留，原因未知；同映像／資源／命令乾淨重跑完成，不算產品缺陷。
- 正式v201與穩定入口123／113Go通過。新正常v20216／v20329GUI、v204各六側完整原版／取樣與所有存檔、來源查詢與固定船名組字、逐欄字級及缺圖集通過；只改六清單安全區與裝載標題，舊港口中文不再殘留。檢查器控制側比較及active不帶shown的介面假設已訂正，保留修正前入口；凍結完成前提早啟動檢查的無效紀錄亦保留。兩個建置初輪漏掛/game，補掛後同命令乾淨重跑，未把skip算通過。
- 獨立兩側與31個破壞／錯版拒絕、缺原版SKIP77通過，v20560PASS與重複／反向普查通過，採用1945項／882已顯示／974待驗／89不可達。規格035／038限定CONFORMED，Issue #56保持in_progress；v206～v207三列來源核對通過，v208取消身分只探勘，不加分。
- 正式程式5fb225cd4baae4dce17e7f37cdc3cbc42f379cd0e86537d059cce6984955bbd3，清冊9a17519fd79e2df51263ea271c5276d229a49e74791ba4f37d1a4e22eae0a051。現況表、穩定摘要、字型入口、生成矩陣／普查／WORKLIST同步；原版唯讀，沒有commit／push／遠端Issue寫入或新公開原版素材。Docker清理與擁有權最終記錄見v205/hygiene-summary.json；全文、三平台與發行未完成。

- 正式v201～v205批次的建置、GUI、重播與矩陣容器均已--rm移除，沒有停止容器。v205/hygiene-summary.json確認無root-owned檔、*.md目錄及被追蹤原版素材，隔離dosgolem仍b0bf259／upstream推送DISABLED。後續v208～v211只在新的有界工作區探勘與私有候選驗證，未增加882完成數。普查首輪正文鍵到段落鍵介面失敗保留；映射GAME.TXT:@ARMOPTIONS後，正例、31拒絕、60列及重複／反向普查均重新通過。


## 2026-10-04：傳教士清單與正常取消身分

- v206～v209正常祝福、切登船、取消身分與復原，15／19GUI、三側完整原版／存檔及四次ARMOPTIONS查詢確認兩種新三列。v210／v211私有124Go、字級／安全區／缺圖集與原版／存檔通過後，規格035升限定READY；正式v212只增加兩個完整來源組合，譯稿、字模、字串及適配器未改。
- 新正常v21319GUI與v214六側完整原版、所有取樣及全部存檔相同。GUI、中文與唯讀觀測全圖相同；相對v201只改兩清單安全區，其餘17圖相同，取消後復原、關框與保存無殘字。30px、原版cap8／pitch12與68／149／47逐欄重驗；缺圖集回原文。
- 獨立missionary側、29破壞／錯版拒絕與缺原版SKIP77通過。v21561PASS，重複與反向普查逐位元組相同，1945項／882已顯示／974待驗／89不可達不變；ARMOPTIONS已shown，不因新增組合加段落信用。規格035限定CONFORMED，Issue #56保持in_progress。
- 正式程式0a1bf028ea6ea0a57050cae438576565b94ec95fb4c88113457b5c771e112a5e，清冊f78d6fd6c608e89aba8101a5f7cb17dd0eaddaca536956d668ca64d030efd4b3。現況表、穩定摘要、字型入口、生成矩陣／普查／WORKLIST同步。原版唯讀，無commit／push／遠端Issue寫入／新公開原版素材；Docker與擁有權見v215/hygiene-summary.json及收尾清理記錄。全文與三平台交付仍未完成。


## 2026-10-04：碼頭七列與正常移到最前面

- v216正常招募，v217／v218第二單位七列15GUI、三側完整原版／存檔與原版來源通過；v219／v220正常Move to front與重開前後兩清單，19GUI、三側完整原版／存檔及三次查詢通過。移到第一位後變六列，原第一位變第二位後出現Move選項，沒有自行重寫規則。
- v221125Go、逐欄30～20px與缺字模／超界／錯字格，v22219取樣、五側原版／存檔及僅前後七列safe新增通過後升限定READY。v223只增加完整七列組合與y67字格，譯稿、字模、字串與適配器保持。
- 正式v223125Go與穩定入口113Go，新v22419GUI、v225六側原版／取樣／所有存檔與來源、30px／安全區／缺圖集通過。準備腳本的舊命令定位文字及續接列印變數失誤保留原檔；核對全部入口後再啟動，屬準備工具問題，沒有放寬產品判準。共享檢查器改為限定分支參數，原傳教士側結果逐位元組相同。
- front獨立檢查、29破壞／錯版拒絕與缺原版SKIP77通過；v22662PASS與重複／反向普查全等，1945項／882已顯示／974待驗／89不可達不變，完成信用0。規格035限定CONFORMED，Issue #56保持in_progress。
- 正式程式e84d4c157a190ae04c5a1c3f291e105abaff8b336006f0de29423ed37e31558c，清冊4b65c62b9c8c1840d79ae197605590d13e485dcdba01270717e9aa2536e3b5df，生成普查／矩陣／WORKLIST與現況／字型入口同步。沒有commit／push／遠端Issue寫入或新公開原版素材。擁有權與Docker清理見v226/hygiene-summary.json及收尾記錄；全文與三平台交付仍未完成。


2026-10-04 收尾勘誤與清理：v215衛生沒有單獨執行，續作後由v226統一檢查；v215/hygiene-summary.json明列NOT_INDEPENDENTLY_RUN並指向最終檢查，不冒充舊輪PASS。v226擁有權／root檔／誤追蹤原版／dosgolem隔離副本／目前來源與文件一致性全通過。主機Docker核對本專案執行中與停止容器均為0，全部本輪一次性容器已自動移除；其他專案未動。主機唯讀核對Issue #56仍OPEN，更新時間2026-09-29T11:39:16Z，沒有遠端寫入。Git差分格式檢查通過，既有未提交修改保留，沒有commit／push／發行。


## 2026-10-04：先完成譯文，最後代表性抽樣

- 使用者決定「先把文字都翻譯完成，最後抽樣對拍」。已更新CONTEXT目前狀態表及本機Issue #55～#61工作項目的驗收順序，既有CONFORMED與62列矩陣收據保留，不逐詞條再跑完整多側GUI／全矩陣。遠端Issue未寫入、未關閉，未commit／push／發行。
- 現行TXT分母重算為3561行，全部已建檔，3558行有譯文，3行已登錄英文冠詞刻意省略。譯文已齊，所以本輪沒有重譯既有語料；974待驗項是畫面證據狀態，不是974筆漏譯。說明書術語表36個空白表示來源只印英文，不填入自行推定的說明書對照。玩家姓名保留原字的既有決定維持。
- 新增tools/validate_text_catalogs.py，直接核對現行十份來源清冊，不依舊翻譯批次或歷史顯示收據。TSV雙引號是原文內容，以QUOTE_NONE解析；一般CSV方言曾將現行867筆語料誤讀成865筆。工具檢查來源檔／片段SHA-256與範圍、鍵與欄數、占位符／樣式／熱鍵、Cubic 11缺字、補充字串模板及整個TXT分母；只准已登錄的三個冠詞省略。來源1684鍵全部核對通過，1681鍵有譯文；字串模板63、靜態圖譯文8、定稿術語256及變數譯名1均非空且無缺字。字型與原版均唯讀，未重烘正式字模或改原版資料。
- 工具SHA-256：4a91668f6fa143d123882109576745ef28de0f26a8925a035b7310eec057def3。整批收據workplace/reports/goal160-coverage/20261004-text-validation.json，SHA-256：30661881122a68e13f9bd458c397f6db42a6d529538343ff465476989bd3e192。缺譯、錯誤片段雜湊、改占位符、重複鍵、刪除來源列均拒絕，缺原版回77。六個反例及現行正例通過；腳本20261004-audit-checks.py及JSON同目錄，入口掛在目標160，沒有新增同義文件。
- 抽樣沿目前v223前端e84d4c157a190ae04c5a1c3f291e105abaff8b336006f0de29423ed37e31558c與v224既有正常GUI實際輸入，重新跑中文及原文。選7點：讀檔清單、海上、歐洲港口、招募、七列碼頭、移到最前面後六列、存檔成功。全部取樣原版RAM／索引／色盤相同，中文逐像素等於既有正常GUI；160800000步完整終點CPU／RAM／VGA、輸入／開檔及COLONY00／03存檔相同。終點RAM d524dd7ac626e5d3f37c10905ae0f21df8c0abbb0d8f1c9addd2ddfa9ff85515，輸入c3b69af723dd708aff78d236f0a6d89f15775ad2156936725ac180bc33d2521b。收據20261004-sample/summary.json，SHA-256：0028c80491d25aa1c67ed91f0cf0c0e9e671625b0c1f38d940038fbef5cfcdf8。不是新錄GUI，不外推其他局勢、完整中文顯示或三平台驗收，不增加882已顯示數。
- 視覺抽查招募與七列碼頭，港口單位標題仍英文，確認為接線缺口；不算漏譯或本輪完成。其餘真正接線缺口與未抽樣情境保留在既有工作項目。README修正為3558譯文與3冠詞省略，將翻譯完成與畫面接線分開。
- 反例腳本首次假設CLOSING來源在corpus而中止，改依現行分母明細挑選獨有來源後同容器命令全重跑通過。抽樣首次缺少工作存檔副本，兩側在執行原版前退出；保存first-startup紀錄並補已驗COLONY03種子後，同容器與命令重跑通過。兩者屬驗證準備問題，未改產品來迎合測試。Xvfb都有有界trap，抽樣容器--rm。
- tools/worklist.py verify通過，WORKLIST.md由JSON重生。Docker最終清理與檔案衛生結果見同目錄20261004-hygiene.json。


## 2026-10-04 港口三類文字整批接線

- 依使用者先整批接線、最後抽樣的順序，將國籍與殖民地居民頂列、職業頂列、商品出價／開價三個模板接入正式字串層。只查已驗NAMES分類與原版港口指紋／字格，價格保留原數值；不修改原版資料、輸入、規則與存檔。
- 原版三欄cap5，各量測22～15px，實際22px；112組職業投影皆容納，最長384px，只作容量量測。固定Cubic 11工具鏈重烘後，字模形狀／字集不變，模板增至66。全文來源3561行、3558譯文及3冠詞省略均維持通過。
- 正式程式f45271c2d644e6347e183298046aa15e8e2140a7af813843f244f399d861c028，127項Go測試／go vet／抓圖同步，穩定入口114項Go測試通過。組裝曾重複帶入string測試檔，已修正來源選擇；穩定入口初次缺/game導致兩項來源測試略過，補唯讀掛載乾淨重跑後無SKIP。兩者皆為驗證組裝問題。
- 十點代表性重播採既有v224正常GUI實際輸入；三側完整原版／各點RAM及索引色盤／輸入開檔／所有存檔相同，新增像素只在三欄，返回世界與存檔無殘字，缺字模回原文。收據6522cc69da3adb38e229bde724fa9aa72305d99378c7abf17be3be3626cffcf0，目視確認三類中文。沒有新錄GUI，不重跑逐詞條六側或新增普查信用。
- 本批入口為docs/goals/181-colony-remaining.md的20261004-port-fields，正式譯文／程式／封裝圖集入口與CONTEXT同步。Issue #56仍未完成；F1提示容量、報表城市名及其他單位／商品正常情境待處理。未push、未發行、未寫遠端Issue。Docker與版控衛生見同入口hygiene.json。

本批收尾衛生通過：942個檔案擁有權均1000:1000，無root-owned或.md目錄，無原版二進位／存檔／字型誤入Git；本批容器已退出自刪，未重建映像，dosgolem副本乾淨且上游推送DISABLED。

### 2026-10-04：同正文完整選項接線與原住民抽樣診斷

- 整批來源索引79組，140項正式Go／go vet／抓圖同步與公開入口115項Go通過；譯文核對仍3561已建檔／3558已翻譯／3冠詞省略，未建檔及缺譯0。正常原住民十點中英重播的完整原版、開檔／輸入及COLONY09全等，學習兩選項已中文，但整張舊GUI對拍未通過，不升CONFORMED或增加普查。
- 比較器第一版錯把預定抓圖步數當實際步數，保留check-v1-scheduled-step.py／check-v1-failure.json；改用唯一標籤並嚴格核對兩側實際幀步數後，發現右側132點差異。第二版來源觀測確認均來自海上或通用字串的舊墨跡清底，同色CPU覆寫需額外保護。寫入世代候選141項Go及go vet通過，仍DRAFT，不替失敗放寬區外檢查。候選組裝先遇檔名與旗標作用域錯誤，已在同一映像的新目錄乾淨重建；兩者是工具組裝問題。
- 更正前一港口段落的F1容量判斷：完整提示18px已在66330000啟用；兩次does-not-fit僅是cap1局部重繪。證據入口f1-correction.json，不重開已顯示欄位。
- 平台腳本來源改取現行公開組裝器；20261004-current-text的Win與Mac三種中間物建置／結構核對通過，僅技術預檢。未新建正式版本、封包、Release或遠端Issue寫入。
- 完整入口與所有原版畫面／來源包留在docs/goals/160-corpus-closure.md索引的本機工作區；Docker及權限收尾於本批最終衛生收據記錄。

### 2026-10-04：原住民抽樣通過與清底假說勘誤

- 原人物IND4A0.SS獨立解碼，在原版索引畫布唯一匹配[250,26]；5503個不透明像素與中文畫面全部不變。整圖137個舊英文清除點中45點在透明區、92點在圖像外，逐點匹配印前值。先前132點只查x≥243，漏列左邊5點。上一條「同色CPU覆寫需額外保護」是假說，本例已由圖像證據否定；寫入世代原型無效果且不需要，未採用。
- 保留兩版比較器失敗及原型內部見證收據。最終比較器只允許兩列安全區與137個有來源證據的清底點，其他整圖完全相同；正常十點抽樣、學習完成與關框失效、完整中英原版及COLONY09全等均通過。摘要2b8b8924456314e3b1e05092d782e2b5ebaec8e701c0fe448c5e506f272a8e1a，規格036只將實際學習兩列升限定CONFORMED。
- 全譯文檢查完成，79組來源接線已實作；未抽樣組合維持證據限制，不重跑逐詞條六側、全矩陣或普查。README、CONTEXT、字型入口、規格與待辦同步。未push、未寫遠端Issue、未發行；Docker及檔案衛生收據由目標160本批入口索引。

本批收尾衛生通過：554個工作產物均1000:1000，全工作樹無root-owned檔案或.md目錄，沒有原版檔案／存檔／字型誤入Git。所用Docker工具鏈沒有殘留容器，未新建映像；隔離dosgolem乾淨、upstream推送DISABLED。Git差異檢查通過，TSV原有空尾欄保留；最終收據20261004-dialog-links/hygiene.json。

## 2026-10-04 事件版畫三色標題接線與抽樣

- 沿顯示隔離路由與規格038的DRAFT／READY審查，從唯讀WOODCUT來源接入17則既有譯文。三種實際來源各以cap7、標題帶、三色及安全區量測30～20px，採30px；51組容量投影與缺字、錯來源、超界回原文通過，不外推全部17種正常事件。字模、譯稿與字集未變。
- 第一輪4／7個清底斑點是舊色號碰到新事件圖的產品缺陷。加入三種已驗事件頁的原版VGA底圖並暫藏舊覆蓋後，原圖及畫框完整保留。前輪原住民137點為合法舊英文清除，兩者分開記錄，不重開已完成項目。
- 現行formal-modal2/colonization-window指紋aae282aa3dccea70ab10773bf04f6f19bef4e882beb2810ab5ca1c920d5fd38d，160個Go案例、公開組裝入口133個Go案例、go vet及抓圖同步通過。十一點沿既有正常新局、登陸、入村與完成學習的GUI實際輸入重播；三張完整事件圖僅標題安全區改變，區內背景及獨立遮罩逐像素相同，區外等於原版。關閉及後續畫面與前版相同；完整原版CPU／RAM／VGA、輸入／開檔及COLONY09全等，摘要3bbaebeab6dd8371c8fa8f954fc0ffa608b911e3bf3da70091e7f0d05a1fde7b。已目視三圖，僅三種事件升限定CONFORMED。
- 比較器先誤要求關閉即expired，按實際suspended／下一標題superseded修正，原失敗保留。後續Pillow與Go透明度取整差異造成16個單通道差1的假失敗，改按Go1.26.7標準庫整數契約重算，196608組公式核對通過，沒有像素容差。兩版三張中文圖完全相同，撤回把此拒絕歸因於對話框保留區的判斷；現行明確排除該保留區符合READY，但本例無新增圖像效果。勘誤與失敗保留於compositor-review.json及舊比較器。
- 觀測準備曾遇Go PATH、字模目錄、模組組裝及檢查點欄位問題，修正隔離環境後重跑；它們是工具準備問題，未列產品缺陷。現行公開來源的Windows、macOS兩架構與通用中間物建置及結構通過，平台摘要e7da3946f3db322caf416f3e6dbffea542b4a99e1a98fde181bfd492a493d49c。未新增Wine、真機、AppImage或正式封包驗收。
- README、CONTEXT、規格、字型入口、目標160／182與本機Issue #61索引同步；WORKLIST由JSON重生並核對。譯文仍3558行完成、3冠詞省略；974畫面待驗項不當缺譯。未新錄GUI、重跑全矩陣、提高882普查數、commit、push、寫遠端Issue或建立Release。原版資料只留本機，最終Docker／檔案衛生收據見目標160索引的20261004-woodcut-titles/hygiene.json。

## 2026-10-04 Linux AppImage封裝接線

- 沿Linux封裝及交付路由，唯讀核對遠端#50要求與既有工具映像。規格041先由候選重建、授權／來源及正常主選單證據升READY，再新增tools/appimage_bundle.py與封裝器的--format appimage；原tar.gz入口保留。包內說明更新現行中文、音訊與系統需求，新增自製SVG／桌面項目及固定第三方runtime來源／授權，未放入原版素材。
- 固定appimagetool只支援zstd，SOURCE_DATE_EPOCH又不能與手動時間選項混用；candidate-a～d失敗及兩版腳本保留。修正實際工具設定後，候選e／f全等；正式工具formal-a／b再乾淨重建全等，18520568bytes，SHA-256 375019a92c20c59a2cef726aeba9e3e77181b1b69bdccfec46df94e6b6b91fcf。獨立解包110檔，manifest、二進位／13份TSV／字模／啟動器、完整授權及來源核對通過，原版排除通過；SquashFS建立時間及一般檔案mtime0。
- 正式單檔AppImage正常鍵鼠至中文主選單，formal-smoke-v3在26M步擷取1280×800實際視窗，五列安全區與50M終點逐像素相同，RAM完整收據保存。初次即時截圖早於重繪，延後擷取後通過；另一次掛載拼寫錯誤被啟動器拒絕，只清除確認為空的三層誤建目錄，改先核對來源並用bind mount重跑。沒有改正式程式或放寬圖像檢查，舊失敗保留。
- 授權破壞、工具指紋不符、非法版號與覆寫既有版本四項拒絕通過。規格041限格式與正常主選單CONFORMED；#50本機進行中，遠端未寫入或關閉。CONTEXT、README、目標182及JSON工作計畫同步，WORKLIST由工具重生。譯文及字模未變，不重跑全矩陣或逐詞條多側驗收。
- 產物只在workplace測試版本，未選正式完整版號、建立dist-all新版、commit、push、tag或Release。Windows／macOS封包、新版執行、全遊戲接線與最終完整發行仍待處理；容器靜音不作人耳驗收。驗證與最終Docker／權限收據均由目標182索引的20261004-appimage工作區保存。

本批收尾衛生通過：1167個檔案／目錄擁有權均1000:1000，全工作樹無root-owned或.md目錄，無原版素材誤入Git。三份新增來源存檔均為有授權與雜湊索引的AppImage第三方完整原始碼。WORKLIST重生及核對通過，Git差異檢查保留TSV空尾欄；dosgolem乾淨且upstream推送DISABLED。主機最後核對無殘留專案容器，未重建映像。README入口依README標準路由再次核對，沒有新增正式下載或全文中文化完成聲明。

## 2026-10-04 Windows ZIP封裝接線

- 前一輪AppImage已具正式工具與限定驗收，本輪沿Windows ZIP、交付與試玩路由續做#51。主機唯讀核對#51／#53要求；現行來源再交叉建置，Windows二進位仍fbb87a2f…且逐位元組相同。DRAFT候選完成資料、正常GUI及同輸入重播審查後升READY，再接入公開封裝器的windows-zip、Windows組裝器與專用說明，最後限定CONFORMED。
- 批次啟動器由Linux唯一完整命令產生，ASCII／CRLF，包內README為UTF-8 BOM／CRLF，中文ZIP根目錄0x800旗標另驗。95檔的原版排除、13份TSV／字模及實際Windows模組授權通過；hideconsole獨立收授權，不複製Linux依賴表。
- 初次CMD引號與Wine CALL返回碼是驗證腳本問題，最小控制與失敗保留。原型參數探針另找到真正啟動器缺陷：CMD拆開--play=false，Go忽略後續旗標，v3因此逾時。重組true／false後候選c／d全等，v4正常GUI通過；沒有改譯稿、字模或遊戲程式。
- Windows真GUI、Windows與Linux同輸入無頭重播的50M完整原版全等，中文安全區逐像素相同；兩平台WAV全等，指紋457e773b…，不冒稱人耳確認。七個宿主開檔名稱的大小寫差異保存，按DOS語意比較，原始記錄不改寫。正式工具兩份ZIP各13973331bytes，指紋2fa9630f26f195257170bcc86c78b6f60a5e4a743740e448f4719939e9cfe100；獨立解包與正式包內批次檔再走正常GUI，輸入及原版與已驗候選相同。
- 正式入口拒絕錯平台、非法版號與既有版本覆寫。LOCALAPPDATA預設存檔位置另做1000步空輸入冷啟動，只驗位置，不算存讀檔或正常玩家路徑。Linux AppImage共用守門回歸與先前375019a9…包完全一致；不重跑整個矩陣或提高882普查數。
- 規格042、目標182、CONTEXT、README與#51本機工作計畫同步，WORKLIST由JSON重生。所有封包／原版畫面留workplace測試版號；未建立dist-all新版、commit、push、寫遠端Issue或發Release。Windows真機、macOS封包、其餘中文接線與最終完整交付仍待驗。完整入口及最終Docker／權限收據見目標182的20261004-windows-zip工作區。

本批收尾衛生通過：1486個檔案／目錄擁有權均1000:1000，全工作樹無root-owned或.md目錄，沒有原版素材誤入Git。WORKLIST與JSON渲染相同，Git差異檢查保留TSV空尾欄；隔離dosgolem乾淨、upstream推送DISABLED。主機最後核對無殘留專案容器，未重建映像；新公開來源與規格均由目標182及README索引。

## 2026-10-04 macOS ZIP封裝接線

- 沿交付、版號及封裝／驗證路由續做#52。DRAFT規格043先驗兩側臨時簽章、重建與私有ZIP，再升READY接入公開macOS組裝器、macos-zip格式、macOS說明及正式建置旗標，最後限建置／簽章資料／封包／shell接線CONFORMED。全部來源與前批相同，不改dosgolem、譯文、字模或原版資料。
- 既有Intel切片未簽章；直接要求連結器簽章後，Go合併DWARF使涵蓋範圍失效。保留signed-a失敗，改省略除錯資料後，signed-c／d與正式建置通用檔全等。兩側每頁SHA-256、CodeDirectory、切片布局、實際Go依賴與系統函式庫核對通過，不冒稱macOS或Gatekeeper接受執行。
- 正式ZIP兩份各14177251bytes，全等於已驗候選，SHA-256 b6a1b5fc9d40098a02808f23b185dec92301adff711b7619da1b265273804d1f。獨立解包94檔、清單、全部譯稿／字模／授權、固定時戳與模式、原版排除通過。Bash3.2.57與5.2的argv／mkdir替身確認中文路徑、空參數、預設與指定存檔參數及退出碼；沒有Mac二進位或原版執行。
- 舊版shell驗證工具的缺curl、yacc與M4，及封裝映像的Git／Go模組快取位置已查明並修正。沿現有映像，固定GNU／Debian輸入雜湊，真正重生語法分析器，不另建重複映像。ZIP提前檢查與重複執行的失敗保留，未覆寫產物；這些是環境或驗證流程問題。
- 兩側壞簽署頁、錯平台、舊未簽章／失效簽章、非法版號與覆寫拒絕通過。共用封裝器Windows回歸仍13973331bytes與2fa9630f…，與已驗前批全等。macOS真機、Gatekeeper、音訊與鍵鼠未驗；規格與文件保持限制，#52仍進行中。
- CONTEXT、README、規格043、目標182及JSON工作計畫同步；WORKLIST由工具重生。收據只在workplace，未選完整版號、建立dist-all新版、commit、push、tag、寫遠端Issue或發Release。譯稿與畫面普查不重算，後續仍按使用者要求抽樣。

本批收尾衛生通過：2009個本機批次檔案／目錄均1000:1000，全工作樹無root-owned或.md目錄，無原版素材誤入Git。WORKLIST重生及核對、文件入口與本輪Git差異檢查通過；dosgolem乾淨且upstream推送DISABLED。簽章工具來源指紋見本批go-signing-source.json，收尾見hygiene.json。未重建映像；本輪有界容器均使用--rm，主機另作最後清理核對。

## 2026-10-05：三平台正式功能版與推廣影片

使用者授權commit、push、更新Issue、Linux AppImage、Windows、macOS與推廣影片。路由載入版號、dist-all、原版影片素材與FFmpeg契約。[目標183](docs/goals/183-release-and-promo.md)與[規格044](docs/spec/044-release-and-promo.md)為本輪入口。

`v.1.0.0-20261005`三平台正式包內嵌版號一致；110／95／94檔、兩次重建位元組相同、manifest與譯稿／字模／授權／原版排除通過。Linux與Wine正式正常GUI、同輸入完整原版及WAV相同。macOS雙架構臨時簽章資料及封包通過，真機、Gatekeeper與最低系統未驗。公開來源Go測試與go vet通過，未改譯文或字型，不重跑整份普查。

90秒1080p影片使用正常玩家截圖剪輯與原版OPL音樂。字幕與八幀抽看、影音格式、音量、黑幀、固定畫面凍結分類通過；音樂中文版與原文控制側逐位元組相同。首版懸停英文與音樂接縫已修正，舊中間物保留。自帶原版三平台包留full-local，公開只有patch、MP4及雜湊。

長錄音在有界時間前停止，改錄300M片段循環。AppImage合法圖示連結、Docker stdin、聯絡圖字型及掃描舊負例的失效symlink等驗證工具問題修正後重跑。私用包第一輪日期歸零及Python ZIP解包未還原時間造成3／4位元組RAM差異，已由dosgolem檔案日期契約定位；保留失敗收據，重建原版時間戳與重跑另記。所有輸出1000:1000，原版未誤追蹤，隔離dosgolem乾淨且推送DISABLED；本輪背景程序皆trap回收，最終容器清理另記。

私用包時間戳修正後，Linux與Wine從自帶資料的一鍵入口重播正常輸入，完整原版狀態與正式公開包全等；macOS實際私用包清單與shell通過，未真機。正式Release五資產與GitHub digest相同。Issue #50／51／52／54關閉，#53及#55～61已更新且保持OPEN。程式提交898d4e1與版號tag已推送，發行收據同步為本輪第二份文件提交；沒有移動tag。Docker本輪容器已結束並回收，無root-owned輸出或md目錄，dosgolem隔離乾淨，原版沒有誤追蹤。

## 2026-10-05：Linux 玩家回報與修正版

沿中文化驗收、試玩、README、版號、交付與影片素材路由，續做[目標184](docs/goals/184-linux-player-regressions.md)及[規格045](docs/spec/045-linux-runtime-performance.md)。使用者確認問題發生在主選單，移到視窗內空白仍是英文，並提供私用Linux目錄。以其正式`start.sh`正常操作量測50M指令115.890秒，CPU採樣確認多層合成反覆解碼及配置完整畫布。隔離dosgolem改為單次解碼，各層仍對原始索引守門；獨立舊版oracle的128例RGBA與結果全等。補丁與隔離提交已保存，共享dosgolem未改。

正式前端另整理既有指令觀測的早退、相同畫面不重傳texture，解除原型100M預設退出上限。缺樣與恢復播放邊界用5ms連續淡出／淡入，記錄缺樣數，不改原始WAV、音高或DOS時鐘。Go與go vet通過。新版正式AppRun正常50M耗時36.203秒，實際私用`start.sh`另一批為12.208秒；保留不同主機負載下兩筆量測，不承諾固定倍率。預設正常執行110.2M後關窗通過。

14組主選單正常懸停／移開，以及正式包與私用一鍵入口均恢復五列中文。使用者last-run紀錄唯讀取樣後，正常輸入重播在台北時區下完整原版狀態、事件與終點PNG相同；兩個空白處檢查點均為中文。首輪容器UTC只造成DOS檔案時間高位一位元組差異，定位後改相同時區重跑，失敗保留。使用者所述持續英文未重現，不寫成已修好。實際舊版約91.8秒播放讀取只收到5.39秒原版音訊，供給不足已證實；優化與淡入淡出仍不能代表人耳驗收或完全無停頓。

依使用者授權將既有正常GUI皮衣廠中文百科截圖加入README及精確gitignore例外。影片新捕錄約95秒原版音樂，使用連續90秒，取消26秒拼接循環；二階段響度校正後−17.9 LUFS、真峰值−2.5 dBFS。八幀字幕與百科畫面抽看、影音與黑幀技術檢查通過，仍無人耳確認。原始WAV與其他PNG只留本機。

三平台`v.1.0.1-20261005`公開包各重建兩次位元組全等，版號／manifest／授權／原版排除通過。Linux／Wine正式正常GUI及同輸入完整原版與WAV相同；私用完整包Linux／Wine也全等。Windows第一輪Wine因`/tmp`父目錄擁有權拒絕設定初始化，改在使用者工作根目錄後同映像、同封包乾淨重跑通過。macOS只驗雙架構、臨時簽章資料、清單與shell，未真機。正式輸出位於`dist-all/v.1.0.1-20261005/`，舊版不覆寫。遠端交付與最終衛生核對另追加。

修正版提交0b9a791、新tag與Release已推送，遠端五個公開資產名稱、大小與SHA-256全等。#53留言保持OPEN，#54留言維持CLOSED。CONTEXT、目標184與唯一JSON工作計畫回填最新交付，WORKLIST由工具重生。新tag建立首次被sandbox的.git唯讀限制拒絕，按既有發行授權改主機權限後成功；沒有覆寫舊tag。補丁必要context空白改用精確差異及反向套用核對，其他來源Git空白檢查通過。沒有原版誤追蹤，本輪輸出1000:1000、無root-owned或.md目錄，無殘留專案容器，未重建映像；隔離dosgolem乾淨且upstream推送DISABLED。

## 2026-10-05：音樂停頓續修的供給量測

沿平台音訊與正常試玩入口量測v.1.0.1正式來源。原版時鐘固定，每200k指令產生約17.27ms音訊；200M正常選單輸入共17.27秒聲音，基準耗時35.78秒。CPU採樣主要為執行器、字串指令與記憶體讀寫，OPL約2%；主選單停留也持續供給不足。增加緩衝或5ms邊界處理不能補足這個缺口。

普通記憶體批次搬移、閒置觀測早退、修正平面模式範圍與採樣導引編譯均只在可丟棄副本測試，未達即時門檻，沒有進正式來源或封包。範圍修正版與UTC基準的RAM只差DOS檔案時間0x67688，原因與前輪一致；PGO完整RAM、終點狀態、事件與原始WAV相同。各批受主機負載影響，不宣稱PGO一定變慢或記憶體加速一律無效。

新增隔離時鐘探針，按48k真實時間消耗播放串流，不以ALSA null或原始WAV完整取代缺樣驗證。原速與保音高半速的本機試聽已生成，只有既有私用音源，未公開。音樂獨立原速播放／跟隨模擬放慢的分支已詢問使用者，沒有預先改正式音訊、原版時鐘或存檔。全部入口由目標184索引，驗證與最終衛生另追加。

時鐘探針200M基準完成：50.712秒需求9736320位元組，缺樣6423832位元組，約66%；無積壓丟棄。來源858569幀約17.27秒；完整原版RAM、狀態、事件、索引、色盤、PNG與原始WAV均與原基準全等。此收據證實供給缺口，沒有硬體實聽，也未宣稱停頓已修好。

本批供給證據已更新Issue #53留言5985306618，維持OPEN。WORKLIST由唯一JSON重生，未變更舊Release或tag。隔離dosgolem乾淨且upstream推送DISABLED；本輪未重建映像，全部有界容器已回收。全工作樹無root-owned產物或.md目錄，輸出1000:1000；其他專案容器保留。

## 2026-10-05：原速獨立音樂與 v.1.0.2修正版

使用者選擇「獨立播放」。依平台規格、READY閘門及文件路由，最小RE確認PSOUND命令／查詢與更新節拍；原型90秒供給足夠、前111筆OPL音符暫存器順序相同後，規格046升READY再接入。獨立聲音機只執行原版驅動與曲譜，主DOS不回寫；SB數位音效分流每幀只取一次，原混音與DMA不變。原版曲尾等待下一首，不人工循環。

正式接線、所有支援命令範圍、通用音效分流、65秒串流、Go測試與go vet通過。600M首輪36位元組缺樣收據保留；修正按實際提供取樣續接後，800M真實時間讀取83.892秒需求16106880位元組，音樂缺樣0、丟棄0。最大Read12.610ms、讀取者延誤50ms；數位音效缺樣仍明載，59.0～71.1秒曲尾等待也分開記錄。50M新版／舊版CPU、RAM、事件、畫面及原始WAV全等。規格046限定CONFORMED，沒有音效卡或人耳驗收。

隔離dosgolem提交c5953b90a0fc76c57f8dbbe0555f7a85d3198fe8，通用補丁保存tools/dosgolem-digital-audio-tap.patch；shared dosgolem未改，upstream推送DISABLED。三平台各封裝兩次逐位元組相同，Linux/Wine正式正常GUI及同輸入原版CPU/RAM/WAV全等，私用完整版start入口也通過。macOS只驗雙架構、臨時簽章資料、封包與shell。

正式根目錄dist-all/v.1.0.2-20261005，Linux完整包已展開供直接start.sh。公開包排除原版檔案，full-local與原始音訊留本機。推廣片沿已驗95秒原版長錄音與中文百科畫面，重新生成首尾版號，90秒H.264/AAC、黑幀0、八幀檢視無裁切；README仍保留已授權的百科圖。來源擷取commit如實保留b0bf259。

本機證據與命令入口見docs/goals/184-linux-player-regressions.md及music-independent/music-verification.json。Git身分wicanr2@gmail.com已核對；主機gh auth成功。一次Issue唯讀請求的自動審核逾時，依工具允許有界重試成功，不算憑證或產品缺陷。準備提交／推送及更新Issue #53與新Release，舊tag及封包不改。Docker容器均一次性且背景程序有trap，收尾仍需核對擁有權與清理狀態。

交付收尾：程式提交e5b606e37a4e25a0a061194435c533e56aeee21c與v.1.0.2-20261005 tag已推送，[Release](https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.2-20261005)五個資產名稱／大小／SHA-256全等，沒有full-local上傳。[Issue #53](https://github.com/wicanr2/colonization_cht/issues/53#issuecomment-5988602216)已更新並回讀OPEN。Linux已驗start.sh展開至dist-all，新版Windows與macOS私用ZIP同在full-local。原版排除與擁有權檢查通過，兩個工作樹提交後乾淨，隔離dosgolem推送DISABLED；本輪一次性容器全回收，沒重建映像，不清理其他專案資源。

## 2026-10-06：游標精靈定位收尾（預防性）

- 使用者選定收尾工作樹未提交的游標精靈修正。確認三個舊二進位皆不含新函式，新碼尚未編譯驗證；早場舊二進位重跑另覆寫檢查器輸入。
- 驗證容器內新組裝通過go vet與全部go test（含TestMenuCursorDisturbance）；新二進位091b2c68…。新二進位31張真視窗掃描列內無英文列；新重播／新對照／舊重播／GUI四路原版狀態全等a8615132…；百科三側與舊收據全等，無回歸。
- 延遲機制否定：舊二進位積極掃描亦無英文列；transit檢查點精靈皆靜止；密集檢查點證實移動後0.2M步內精靈已就位；實拍框外小差異為import截圖撕裂。規格012附記改列未重現假說的預防性強固；使用者持續英文仍追蹤，不冒稱修復。
- 早場檢查器輸入移位保存並由cursorbox還原，重跑通過PASS_TEXT_RETENTION。Git身分wicanr2@gmail.com已核對；本輪一次性容器全回收（均--rm、--network none、UID/GID 1000:1000），輸出擁有權正常，不清理其他專案資源。提交待推送由使用者確認。


## 2026-10-06：碼頭Board七列

- v227正常走訪碼頭各清單未見Board（祝福段Escape離港只作勘誤），v228登船切換後重開命中Board七列[1,2,3,5,7,9,11]，現英文fail-closed；v229四次原版查詢、21GUI、四側完整原版／存檔及字格通過，正式無source事件。
- v230現行源只加Board組合，142Go、逐欄30～20px與缺字模／超界／錯字格，v231六側原版／存檔及僅切換後七列safe新增通過後升限定READY。v232一行採用，譯稿、字模、字串與適配器保持。
- 正式v232142Go與穩定入口138Go，新v23321GUI（click拖曳致選單取消兩次，覆寫click等2Update後通過）、v234六側原版／取樣／所有存檔與來源、30px／安全區／缺圖集通過。檢查器增board側，舊側零動；基線改上一版正式v223。
- board獨立檢查、29破壞／錯版拒絕與缺原版SKIP77通過；v23563PASS與重複／反向普查全等，1945項／882已顯示／974待驗／89不可達不變，完成信用0。規格035限定CONFORMED，Issue #56保持in_progress。
- 正式程式a10dbd94e357d56c8fbaec55ea189ebb6e2ad75cfd14ad58542cc3100aca4f6e，清冊d0818ae05f94b94d64c9e96747efe3ef9c9f47b077c9ac439f71ded9b06cea8b，生成普查／矩陣／WORKLIST與現況／字型入口同步。沒有commit／push／遠端Issue寫入或新公開原版素材。擁有權與Docker清理見v235/hygiene-summary.json及收尾記錄；全文與三平台交付仍未完成。


2026-10-06 收尾清理：v235擁有權／root檔／誤追蹤原版／dosgolem隔離副本／目前來源與文件一致性全通過。主機Docker核對本專案執行中與停止容器均為0，全部本輪一次性容器已自動移除；其他專案未動。主機唯讀核對Issue #56仍OPEN，沒有遠端寫入。Git差分格式檢查通過，既有未提交修改保留，沒有commit／push／發行。

## 2026-10-07：接手核對

- 知識路由命中文件分工、工作清單與dosgolem原版驗證，已讀相應入口。Git身分為`wicanr2@gmail.com`，既有作者一致；保留上一輪14份未提交修改。隔離dosgolem為`c5953b90a0fc76c57f8dbbe0555f7a85d3198fe8`，工作樹乾淨，`upstream`推送仍為`DISABLED`。
- 主機`gh auth status`通過，遠端#53及#55～61仍OPEN，與JSON八項未完成工作一致。唯讀核對#56正文及留言，沒有commit、push、Issue寫入或發行。
- 在`colonization-verification:20260930-r1`重跑`tools/check_goal181_dock.py --side board`，採v233 GUI與v234凍結證據，結果PASS。21張正常GUI、六側原版狀態與存檔、單欄安全區及回退仍通過；清冊SHA-256為`d0818ae05f94b94d64c9e96747efe3ef9c9f47b077c9ac439f71ded9b06cea8b`。本次只重查收據，未重跑遊戲或全矩陣。研究映像缺Pillow屬驗證環境問題，改用既有驗證映像，未新增或重建映像。
- 核對v235矩陣設定雜湊、63列既有PASS、零過期與輸入衝突、普查與衛生收據雜湊。發現`docs/text-census.tsv`的`GAME.TXT:@ARMOPTIONS`少了空尾欄的Tab；其餘內容相同。從已驗生成檔`v235/a.tsv`恢復後，TSV、普查Markdown與矩陣Markdown皆與生成收據逐位元組相同。1945項、882已顯示、974待驗、89不可達不變。TSV依完整欄數核對，Git空白檢查只對該檔排除空尾欄，其餘檔案維持嚴格檢查。
- `tools/worklist.py verify`的61項通過，`render`與`WORKLIST.md`相同。更新`CONTEXT.md`日期與目前下一閘門，將末尾較早交接明列歷史，避免重新開啟已完成事項。接續入口為#56／目標181的港口其他單位標題；報表城市名仍保留版面決策與READY限制。
- 全工作樹無root-owned檔案或`.md`目錄，原版素材未誤追蹤，修改文件擁有權為1000:1000。全部容器使用`--rm`、`--network none`及UID/GID與資源上限；主機核對本專案執行中與停止容器均為0，其他專案容器未動。

## 2026-10-07：正常遊玩與Issue關閉審查

- 知識路由命中正常玩家路徑、存讀檔與dosgolem驗證，沿既有入口讀取試玩方法與DOS配置／覆疊READY規格。主機`gh auth status`成功後直接讀取遠端八個OPEN Issue及完整正文，沒有遠端寫入。依最新使用者決定區分譯稿、接線與代表性抽樣，不把974筆pending當作缺譯，也不重開已有驗收。
- 目前正式來源與v232二進位一致，以Xvfb真視窗／xdotool新錄主選單讀檔、歐洲港口招募取消、殖民地職業清單、海上移動及正常GAME存檔。15張同步GUI與中文重播逐像素相同，中文／原文／缺字模三側全部檢查點RAM、索引、色盤與終點完整原版狀態、原始WAV及COLONY00／03全等，回退圖等於原文。原始COLONY03未改。
- 正常關窗、重啟新行程並讀回COLONY00；船位置(55,30)、行動2、1496年春季與1000$一致，原版控制組完整狀態與原始WAV全等。音訊另以200M步單調時鐘驗24.143秒，6個原版音樂命令，音樂缺樣0、丟棄0，輸出非靜音；觀測副本與正式程式完整狀態及原始WAV相同。數位音效缺樣另記，未音效卡、人耳或macOS真機驗收。
- 新錄英國發現者新局在635086794步提前停止，未到可操作世界。中文、原文、診斷副本與已發行v.1.0.2完整狀態相同；關閉數位音效仍在同一步停止。DOS未退出、CPU.Halted；停止前64016 bytes申請失敗、最大空塊49232 bytes，隨後RETF跳0000:0000、REP MOVSW覆蓋IVT。最初原因未知，沒有把配置失敗當作已證實的配置器缺陷，也沒有加入忽略HLT或增大記憶體的修補。
- 目標185保存八項Issue的關閉條件、已驗範圍及缺口。#53及#55～61全部保持未完成，#53／#61另受新局阻塞影響。新增`tools/check_goal185_playtest.py`，收據完整時仍以退出碼1回報遊玩FAIL；缺原版SKIP77。既有63列中文矩陣保留，沒有以本輪少數抽樣增加普查完成數。README、CONTEXT與工作清單同步，沒有commit／push／Issue寫入或發行。
- 容器首批到有界時限時中止了兩個尚未完成重播，分類為驗證環境中止；沿同一映像、掛載與命令乾淨重跑成功，未寫成產品缺陷。所有原版輸入唯讀、UID/GID 1000:1000，沒有新建或重建映像。Docker與擁有權收尾另記於本節。

收尾：61項工作清單verify及render一致，八項未完成；新增檢查器正常收據返回預期FAIL／退出碼1，缺原版返回SKIP77。全工作根無root-owned檔案或`.md`目錄，原版EXE、存檔、音訊與圖像資料未誤追蹤，修改檔UID/GID為1000:1000。隔離dosgolem乾淨、upstream推送DISABLED。主機Docker回讀本輪容器數0，沒有殘留遊戲或Xvfb；其他專案資源未動。彙整收據`playtest-review.json` SHA-256 `e739439452cbbe98993d76b78e0969ff68da5d3094da78f01090a82e81fa416d`，本輪沒有發行或遠端寫入。


## 2026-10-07：重啟後接手與新局停止修復

- 接手保留既有未提交修改，Git身分wicanr2@gmail.com及既有作者核對。主機gh auth成功，#53及#55～61仍OPEN；沒有遠端寫入。
- 新局診斷v7於接手時仍在執行，完成後沿標準EMS契約找到同頁映射缺口。依DRAFT→READY→正式接入→限定CONFORMED完成修復。最小合成測試、補丁、通用規格198及本專案規格047保存，可從c5953b9重生；隔離dosgolem本機提交82a14b2，shared未改、upstream推送DISABLED。
- Go／go vet與三套核心回歸通過。正式f4042b3d…的新局25GUI／三側完整狀態與缺字回退、既有15GUI／兩側及舊GUI完整狀態、存檔及原始WAV通過。正式真視窗另已進新世界及移動；新會話未驗手動存檔，誤命名圖不採計。驗收入口及雜湊見規格047和RESEARCH-LOG。
- 原Go驗證映像與其基底於正式重播後已不存在，原因未查明，不宣稱由本輪清理造成。沿既有Debian基底建立有明確替代關係的colonization-verification:20261007-runtime-r2，來源tools/Dockerfile.verification-runtime-r2；僅恢復GUI／Pillow／收據驗證，Python與Pillow ABI自洽。Go建置鏈仍須依原來源恢復，未以主機runtime代替。
- GUI首場達時限而中止，分類為驗證環境中止；第二場過早回收Xvfb，輸入收據先完成而終點尚未寫完。第三場等程序退出與完整檔案後才回收，取得完整正常關窗收據。80M延長初輪未改輸入收據end欄，實際仍635M；後續只延長觀察期限，不改任何輸入。上述腳本問題未寫成產品缺陷。
- README、CONTEXT、目標185與#53／#61工作項目回填修復與剩餘限制。公開v.1.0.2尚未包含本修復，三平台未重建或發行；沒有root專案commit、push、Issue留言或關閉。歷史矩陣與普查不增加，剩餘接線繼續由既有工作項目管理。
- Docker擁有權、原版誤追蹤及最終清理核對追加於本節末尾。

2026-10-08 收尾：工作清單61項verify通過、render一致，八項未完成。新局及既有存檔彙整PASS，缺原版返回SKIP77，檢查通過。全工作根無root-owned檔案或.md目錄，原版EXE／存檔／封存檔／音訊未誤追蹤，修改檔1000:1000。隔離dosgolem82a14b2已本機提交且乾淨、upstream推送DISABLED；root儲存庫保留既有未提交修改及本輪文件／工具，沒有push、遠端寫入或發行。本輪容器均有界且--rm，主機回讀專案容器0；目前僅保留驗證執行期r2，其他專案資源未動。自動審核一次唯讀Docker請求逾時，依工具允許重試一次成功。衛生收據ems-final-hygiene.json。


## 2026-10-08：接續收尾

- 核對現況、工作樹與映像，保留既有修改。直接沿用已有固定hr-go-ebiten映像，Go建置環境恢復；Dockerfile.verification轉向其固定指紋，沒有建立相同功能映像。離線重建f4042b3d…全等，Go與go vet通過。
- 新正常GUI英國開局、向西移動、GAME手動存檔與正常關窗成功，新行程正常載入新COLONY00。三側20GUI／完整原版／取樣／原始WAV／存檔與回退，以及重啟原文控制組通過。先前誤點高海失敗收據保留；新操作改為保持滑鼠兩個Update及已驗GAME點擊。入口目標185與check_goal185_newgame_save.py。
- 伺服器重啟中斷後，先回讀容器與收據，沒有重跑已完成工作。高海正文已有模板與30px來源事件，問題定位為重複選項重繪撤銷前一正文；新規格048目前DRAFT，私用原型測正文像素／身份／安全區／清單順序與拒絕反例，正式程式尚未修改。


2026-10-08 高海正文收尾：規格048限定CONFORMED，正式fe58445e、145Go／go vet、10新正常GUI／四側完整原版、WAV、存檔與正常No取消通過。原始失敗輸入也由正式程式重生，全部畫面與已審原型相同。初次optionBody快照尚未同步，依診斷改用active的afterSafe；正式首次匹配時限不變。圖像判讀曾誤判空白，直接像素、逐層及正文矩形指紋一致後勘誤，未加合成器猜補。整合缺bytes匯入、未映射視窗BadMatch及一次診斷漏原版掛載均已分類與乾淨重跑，不當產品缺陷。來源、容量與證據入口見規格048；工作清單維持八項，普查與矩陣不增加。沒有commit、push、Issue寫入或發行。

2026-10-08接續收尾清理：工作清單61項verify及render一致，八項未完成。兩個新檢查器缺原版明確SKIP77。全工作根無root-owned檔案或.md目錄，原版EXE／存檔／音訊／封存檔未誤追蹤，修改檔1000:1000。隔離dosgolem82a14b2乾淨、upstream推送DISABLED；root工作樹保留既有及本輪修改。所有本輪容器有界且--rm，主機回讀專案容器0，沿用既有HR工具映像，沒有新建映像或清理其他專案。沒有commit、push、遠端Issue寫入或發行。衛生入口continue-final-hygiene.json。

## 2026-10-08：指定完成#55、#56、#57、#61

直接讀遠端四項Issue與現行JSON，保留既有修改。沿固定HR映像與dosgolem82a14b2，沒有新建映像。使用者選城名A；173個預設名三欄全容納，原型四側26點只改三處、其他23圖相同。規格038經DRAFT→READY→正式接入→限定CONFORMED；baa1eac7、147Go／go vet、新正常10GUI／四側原版、WAV、存檔與回退通過，只改三處、其他7圖不變。

新百科22GUI三側限定PASS。IDA9.4一次性16位元DB的775筆原始指令逐byte核對，只導航sub_EAC，不判定額外地形不可達。708詞接線诊斷分清專屬欄位、玩家名、冠詞與Land語意；164百科與全部教學、五個存讀檔錯誤模板已載入，載入仍不證明顯示。

#61私用目錄0555的正常儲存失敗GUI確認SAVEERROR檔名被當術語而回英文，規格035保持DRAFT。三側9GUI完整原版、WAV、存檔與回退相同，檢查器以FAIL／退出碼1保留。目錄恢復0755，原版與客體資料不改。save-description才是實際錯誤截圖，save-error已回世界；保留原名與勘誤。空槽誤點與22點誤寫24點已按原收據訂正，不當產品缺陷。

check_goal185_remaining.py由目標185與規格035／038索引。61項worklist verify與render一致，八項仍未完成，不增加882普查或63全矩陣。沒有commit、push、Issue寫入或發行。全部本批容器有界且--rm，GUI及Xvfb已關閉並停止；最終衛生收據closure-final-hygiene.json。

## 2026-10-08：儲存失敗檔名修正與讀檔缺口

沿上一輪已取證SAVEERROR，私用來源限定檔名原型148Go／go vet通過，100檔名容量全容納；原版cap8、pitch12、660×48安全區與30px實際墨跡已量測。原型九點四側只改實際錯誤框，其他8圖不變。規格035審READY後正式接入，f39336c6、148Go／go vet、新8GUI與四側完整原版／WAV／存檔及回退通過，只改錯誤框、其他7圖不變，限定CONFORMED。新check_goal185_save_failure.py與較早英文FAIL分開並由目標185索引。

正常讀檔清單後暫移私用COLONY03，原版LOADERROR仍英文，原因同為檔名術語守門；三GUI、三側完整原版與全部取樣、音訊與還原存檔相同，規格035維持DRAFT。原版按Return後終了，腳本誤預期回選單而報前端結束，完整收據已保存，不作產品缺陷；重播依檢查點暫停自有程序施加同檔案缺失條件，客體資料不改。初始magic byte無效副本在清單階段被排除，未驗到LOADNOT。一次GUI數量誤把終點圖當第四張，已依原始shots更正為三張。

本輪未關閉四項Issue、不改882普查或63全矩陣。工作樹保留既有修改，沒有commit、push、遠端Issue寫入或發行。所有輸出1000:1000、原版唯讀；本批容器--rm，GUI／重播已結束後清理，沒有新映像。衛生收據save-error-final-hygiene.json。

## 2026-10-08：四種讀檔來源與代表性畫面續驗

取得LOADNOT／LOADOLD／LOADSIZE正常GUI，明示清單後私用標頭測試副本並还原；byte9改動正常載入，不當版本證據，byte10改動觸發舊版，byte12由主選單得到LOADERROR、由世界GAME讀檔才得LOADSIZE。沒有改正式規則或格式。四欄各自cap8／cap9、安全區、30px、400檔名容量與標題cur／prev像素完整守門已審DRAFT→READY。最初候選只延伸retainSlotTitle仍失效，追原始cur／prev後改來源限定獨立標題，未放寬區外比較。

正式ed5444ea、149Go／go vet、四種新16GUI／四側完整原版、取樣、WAV、還原存檔及回退PASS；只改四框、其他12圖不變，LOADERROR原版Return退出保持。SAVEERROR8圖與報表10圖回歸逐像素／狀態／WAV相同。check_goal185_load_failures.py已由規格035與目標185索引；彙整0e76d0136bf6aff8d2b0310576bda2277bff957986ac76b1bd7de67783f45ee9，限定CONFORMED。原版確認後寫出完整輸出的時序曾讓腳本太早檢查，完整收據已核對；等待改為全部檔案及程序退出，不當產品缺陷。

必要代表性GUI首份停留閱讀而逾容器期限，缺輸入／終點，不採驗。改自動關窗的新31GUI与三側全等，六類百科、F1雨林頁、河流欄位中文命中；View座標與原住民領土兩類仍no-template，作真正接線缺口。第一輪F1選到未探索格、Escape開離開確認，已按實際畫面取消並重新定位，不把它們當百科或產品缺陷。check_goal185_representatives.py已由目標185索引，彙整dd5ea3f4c2e3508ccc440ef6961336b83532dfe2fdf45cd7bad1bb2bfb2f8a2c。

四項目標保留完整範圍，仍未關閉Issue，未增加882普查與63全矩陣。沒有commit、push、遠端Issue寫入或發行。所有工作有界、UID1000且原版唯讀；容器均已終止／rm，首兩批期限結束已回讀終止狀態，末批自動關窗与重播完清理。最終衛生load-family-final-hygiene.json。

## 2026-10-08：View欄位回填與港口船隻接線

接手先核對目前程式、正常收據及四筆遠端Issue，沿工作清單資料與驗收交接路由；Git身分正確，gh auth成功，只讀遠端。View座標與領土兩欄已有正式新10GUI／四側PASS，按規格038回填目前狀態；地圖雙語城名在正常畫面已顯示，不因單色診斷未收離屏事件重新開啟。

從目標181 v192正常購船後存檔冷啟動，取證8GUI並正常關窗，找到船隻頂列及EUROPESHIPOPTIONS三列實際接線缺口。原型v1借尚未形成的afterSafe而拒絕，v2既有同框框界仍未匹配；回查規格閘門與正文原始像素，原型v3以來源、港口指紋、固定三列cap8／位置／內容及optionBody共同辨識。失敗收據保留，沒有提高等待常數或修改原版流程。

96個名稱組合容量20～22px、分類與場景拒絕通過；原型8GUI／三側及原觀測副本原版、取樣、WAV、存檔全等，新像素限定頂列／選項。規格035／038審READY後正式接線，另錄11正常GUI、三次懸停、取消與返回世界。正式d392c602…四側的完整原版、每點RAM／索引／色盤、WAV及兩份存檔全等，GUI與重播逐像素相同；四張選船／懸停只改核准區，其他7圖不變。實際頂列22px／三選項30px，獨立check_goal185_port_units.py PASS，摘要816e8374…；153項Go先通過，原先因COLONIZATION_MUSIC_ROOT未設定而skip的兩項以/game補跑PASS，合計155項，go vet通過。

矩陣設定新增第64列，單列及欄位普查守門PASS，摘要5b9bf1a1…；只採實際頂列，三列子集不提升完整四列來源。全矩陣／普查未重跑，舊63PASS及1945／882仍是歷史證據。四項worklist的verify.note改為目前真相，移除已被新收據否定的未完成敘述；歷史仍在規格、Goal與本日誌。61項verify通過，渲染與WORKLIST逐位元組相同。

Goal #55／#56／#57／#61保持進行中。下一個實際接線分支為港口帶貨四列，其他範圍按當前工作清單審查。沒有commit、push、遠端Issue寫入或新版發行。原版與正常種子唯讀，輸出UID/GID1000，專案全樹未見root-owned或.md目錄；本批容器均已完成並由--rm清除，映像未增建，dosgolem副本乾淨且upstream推送DISABLED。一次日誌附加命令因引號造成Python語法錯誤，未寫入；渲染仍已核對，本腳本補寫成功後再核對擁有權。

## 2026-10-08：目前狀態表的歷史快照整理

舊表混有已被本輪來源与驗證取代的敘述，以下逐字保留整理前全文；sha256 1985e1321be55913fd736520f7adba213927af1197323df6b29c4c9daf90e120。新現況只在CONTEXT，以下不重新開啟已完成項。

## 目前狀態表（2026-10-08，接手收尾）

本表是目前狀態的唯一入口；後面的較舊交接與歷史狀態只保存當時證據，不重新開啟已完成事項。

| 項目 | 目前狀態與證據 |
|---|---|
| 指定四項收尾 | 完整目標仍為#55、#56、#57、#61。報表三處、SAVEERROR及四種讀檔檔名／槽位標題限定CONFORMED；最新讀檔16GUI／四側只改四框、原版／WAV／存檔與回退一致，既有18圖回歸不變。六類百科／可見河流新31GUI三側PASS。View座標與原住民領土兩類接線也已限定CONFORMED：新10GUI／四側只改三張已量測欄位，原版、WAV、存檔與缺字模回退一致；29項容量投影不算正常命中。#55名稱／選單接線審查、#56其餘港口標題、#57百科完整接線／可達限制、#61教學／事件範圍及矩陣／普查登錄仍在進行，四項Issue未關閉。 |
| 遊玩驗證 | [目標185](docs/goals/185-player-experience.md)的新局停止已依[規格047](docs/spec/047-ems-alias-coherence.md)修復。新局25GUI／三側、既有15GUI／存檔回歸保留；2026-10-08再完成新局20GUI／三側、向西移動、正常GAME手動存檔及關窗後新行程讀回，完整原版狀態、WAV、COLONY00／09與回退通過。新存檔a043119c…，入口check_goal185_newgame_save.py。原先誤點高海的失敗收據保留，已由新正常會話補足。高海正文選項重繪保留另列[規格048](docs/spec/048-dialog-choice-body-retention.md)限定CONFORMED，10新GUI／四側同狀態及取消無殘字通過。#53及#55～61仍未完成，沒有遠端寫入或發行。 |
| 接手核對 | 2026-10-07保留上一輪14份未提交修改，重查碼頭Board七列收據PASS、61項工作清單驗證及渲染一致。現行矩陣設定與v235收據雜湊相符，63列PASS為既有結果，本次未重跑全矩陣或遊戲。GitHub未完成項仍為#53、#55～61，本次只讀。普查TSV已恢復生成檔的空尾欄，1945項與完成數不變。重查入口為[目標181](docs/goals/181-colony-remaining.md)與[工作歷程](WORKLOG.md)。 |
| 音樂獨立播放 | 使用者選定原速獨立播放，正式接線及83.892秒即時消費驗證通過，音樂缺樣0、丟棄0。主DOS數位音效保持原路徑，FM音效沿原命令在私用原版驅動播放。CPU、RAM、中文畫面與原始WAV同輸入全等。原版有限曲目結束後仍等主DOS下一首指令，本次曲尾空白約12秒。未音效卡或人耳驗收。[規格046](docs/spec/046-independent-music.md)與[目標184](docs/goals/184-linux-player-regressions.md)保存證據；v.1.0.2已發布。 |
| Linux 玩家回報 | [目標184](docs/goals/184-linux-player-regressions.md)修正重複整幀解碼瓶頸，正式50M正常GUI由115.890秒降至36.203秒；畫面合成與5ms播放邊界修正保留，音樂改依規格046獨立播放；未人耳驗收。主選單14組懸停及使用者實際輸入的兩個空白處檢查點均恢復五列；持續英文未重現，保留追蹤。 |
| 本輪交付 | [v.1.0.2-20261005](https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.2-20261005)已發布，程式提交`e5b606e`與新tag已推送，遠端五附件大小／SHA-256全等。[Issue #53](https://github.com/wicanr2/colonization_cht/issues/53#issuecomment-5988602216)已更新並保持OPEN。三平台公開包、私用完整包與90秒影片已驗；Linux新start.sh已展開到dist-all對應full-local，macOS未真機。舊版tag與封包不改。 |
| 工作順序 | 2026-10-04使用者決定「先把文字都翻譯完成，最後抽樣對拍」。先整批處理譯文與接線，最後以代表性正常玩家路徑驗證；不再以每個待驗詞條的完整多側GUI驗收作為下一筆翻譯的前置。既有驗收保留，未抽樣欄位不冒稱已顯示或CONFORMED。 |
| 全語料譯文 | 2026-10-04以現行來源重算：遊戲畫面3561行全部已建檔，3558行已翻譯，3行英文冠詞有理由刻意省略，未建檔與缺譯均為0。現行十份來源清冊1684鍵，1681鍵有譯文、3鍵省略；字串模板66、靜態圖譯文8、定稿術語256與變數譯名1也已檢查。來源、占位符、控制碼、熱鍵及字型缺字檢查通過，與畫面普查882／1945分開統計。[重跑入口](docs/goals/160-corpus-closure.md)。 |
| 翻譯收尾抽樣 | 同日v223七點既有正常GUI輸入抽樣保留；本批再以目前程式抽樣十點，涵蓋港口買賣價格、木匠／無職業頂列、招募／碼頭、關閉港口、存檔及返回世界。中文／原文／缺字模三側各點RAM／索引／色盤、完整終點CPU／RAM／VGA、開檔／輸入及COLONY00／03存檔相同。新增差異只在三欄安全區，關框無殘字，缺字模回原文。重播既有正常GUI實際輸入，沒有新錄GUI；不提高882計數。[本批入口](docs/goals/181-colony-remaining.md)。 |
| 目前程式 | 正式來源d392c602de2e31177a25abf6420ba8dbeb3d379a6332345757209e9914eb2a44，155項含子項Go通過；先跑153項，再以唯讀原版路徑補跑原先因環境變數未設定而skip的兩项音樂測試，go vet通過。新增港口船隻頂列22px／三選項30px，新11GUI／四側及矩陣欄位守門通過；其他7圖不變。先前View兩欄、五種存讀檔檔名與槽位標題、報表三處、規格048與EMS修正保留。隔離dosgolem82a14b2不變，三平台新版未打包／發行。 |
| 港口欄位 | 原先殖民者／職業／商品三類欄位與F1提示保留。新增船隻頂列及空貨艙三選項已限定CONFORMED：實際英國輕帆船／倫敦頂列22px、三選項30px，11新GUI／四側只改四張核准區、其他7圖相同。96個船隻名稱組合容量20～22px不算正常命中。驗證矩陣新增該列且單列PASS，全矩陣及普查未重算。帶貨四列仍未接，其他單位標題與商品／職業正常情境仍列審查範圍；入口check_goal185_port_units.py及規格035／038。 |
| 原住民／一般訊息接線 | [目標160](docs/goals/160-corpus-closure.md)的20261004-dialog-links建立79組來源限定選項。正常和平交涉、入村、接受學習、完成與關閉十點抽樣通過，兩側完整原版狀態及COLONY09全等。學習選項30px限定CONFORMED；28職業只做容量投影。原版人物圖像唯一定位於[250,26]，5503個不透明像素與原版完全相同；137個舊英文清除點中45點在透明區、92點在圖像外，全部有印前值證據。先前132點只查x≥243；整圖補足x=242的5點。寫入世代候選無圖像效果且本案例不需要，未採用。不提高882計數，#58／#60進行中。抽樣摘要SHA-256 2b8b8924456314e3b1e05092d782e2b5ebaec8e701c0fe448c5e506f272a8e1a。 |
| 貿易路線／Issue #56 | 規格035／038第一路線原有九ROUTE來源、兩Jamestown裝卸提示及目的地／母港清單維持CONFORMED；另v187～v191前兩列預設Jamestown中文限定CONFORMED。40新正常GUI、各六側完整原版及全部存檔相同，新增差異只在城市欄；改選London及刪除第二目的地無舊中文，玩家路線名原字。25破壞拒絕、缺原版SKIP77。其他編號、第三／四列、網格母港、自動跑商與正常同名城市反例仍未驗。[目標181](docs/goals/181-colony-remaining.md)。 |
| 歐洲碼頭續驗 | v201～v205六種碼頭清單與固定輕帆船港口裝載標題、v206～v215兩種傳教士三列及正常取消後復原保留限定CONFORMED。v216～v226再驗正常招募、七列與移到最前面後兩清單：30px、19新正常GUI、六側完整原版／全部取樣／新舊存檔全等，只改前後七列核准區，其他17圖相同，缺圖集回原文。29破壞拒絕與缺原版SKIP77；62PASS與重複／反向普查，ARMOPTIONS已shown，882不增加。v227～v232 Board七列探勘、來源、私有、驗證與限定READY接線完成（一行組合，正式a10dbd94…），v233新正常GUI中文已現、存檔通過；v234五側正式驗證通過（board側檢查、29破壞拒絕、凍結清冊）。v235矩陣普查通過，限定CONFORMED；其他單位頂列與其他未驗局勢待驗。[目標181](docs/goals/181-colony-remaining.md)。 |
| 貨物提示 | 規格038限定CONFORMED：Loading標題、按住拖曳提示、移至船／城市四欄。v153正常24GUI指紋及正式重播全等；五側完整原版、24取樣及全部存檔相同，來源RAM／存檔相同。v154另回歸同名城市26圖，船名輕帆船與自訂Caravel城市不混譯；23種破壞收據拒絕、缺原版SKIP77。只驗Furs／Caravel，其他商品與船型未驗。 |
| 三平台建置與封裝 | [目標184](docs/goals/184-linux-player-regressions.md)採`v.1.0.2-20261005`。Linux AppImage110檔、Windows ZIP95檔、macOS通用ZIP94檔，各重建兩次逐位元組相同。每個二進位與macOS兩切片版號一致，Go1.26.7、Ebitengine2.9.9及授權／譯稿／字模核對通過，原版不入公開包。Linux與Wine正式啟動、同輸入完整原版狀態與WAV相同；macOS只驗建置、臨時簽章資料、封包與shell，未真機或Gatekeeper。 |
| 殖民地續驗／Issue #56 | [目標181](docs/goals/181-colony-remaining.md)進行中。新局v3只到原住民交涉，不算殖民地命中；正常存檔v5已啟用拓荒者、接受命名並實際進入Jamestown殖民地。資金不足碼頭BUY正文及三個面板短欄已通過18個原版取樣點、GUI安全區與三側驗收；本欄30px、長數值壓力22px及超界回退通過。已確認原版查詢BUYME0、模板BUYME1只是同文正文；BUYME0兩行維持已驗；正常兩次回合後的貨車BUYME1正文與兩選項另通過26個原版取樣點、GUI安全區與三側完整狀態，實際481$／國庫1000$，原版BUYME1查詢已確認。議會五項顧問選擇、職業17項、更多頁六項裝備需求及棄城確認正文／正常取消也已正常GUI／三側驗收，普查只採檢查器實際驗過的欄位。v10另以正常GAME選單存為COLONY01.SAV，30個原版取樣點與三側完整狀態／新舊存檔逐位元組相同；當時成功訊息仍英文；SAVEGOOD現已由v55～v60驗收。不注入存檔或地形。 城市改名提示30px／標籤29px、英文姓名編輯及Escape取消已限定CONFORMED；九張正常GUI、四側完整原版／存檔不變，來源RENAMECOLONY已核對。 歐洲v74～v77新增正常取消三清單／正文、教學及F2～F10的109欄限定CONFORMED。128下方陰影分類修正、會期／反叛加分精確模板已正式接入；26GUI、五側完整原版與存檔、來源、十二拒絕反例通過。三個報表城市名仍回原文；v78僅有A22px延伸／B15px雙行比較，版面選擇及相鄰欄界待驗，未READY。v79～v83正常500$砲台購入確認／Enter接受已限定CONFORMED：9GUI／五側完整原版、四側9共同取樣／原版查詢與不變存檔，確認／兩選項30px及購入後標題22px，13種破壞收據拒絕與24組排版量測通過。三個實際欄位採用；其他單位、取消及稅率事件未驗。 v85～v88正常職業清單選漁夫的未建碼頭正文已限定CONFORMED：30px／兩行、八GUI、五側完整原版與四側八取樣、原版查詢及不變存檔，13種破壞收據拒絕通過。右鍵工作者實際開百科，拖到水域沒有本提示；兩種探索均不提高完成數。 v90正常士兵選任後切右下單位面板，已找到標題與當次三列原文選項；v91原版查詢COLONYUNIT／UNITOPTIONS、11GUI與未改顯示的觀測副本完整狀態全等，來源探針RAM相同。相鄰變數拆成S與oldiers已用既有Go匹配器重現；三列原版cap8／行距12。v94～v97正常士兵標題與當次三列已限定CONFORMED：11GUI、六側完整原版、五側11共同取樣與來源／存檔通過，圖示與兩核准文字區外不變。19種破壞收據拒絕、缺原版SKIP77及22個合成名稱量測通過。49PASS、855已顯示；段落計數只採當次三列，不外推其餘兩列或其他單位狀態。Issue #56主機遠端核對仍OPEN，其他範圍繼續。 v105～v110另驗正常駐守後清除命令／警戒或登船／不做更動三列：30px、13GUI、六側完整原版／五側13取樣，來源與存檔一致，單位圖示及清單區外不變；19種破壞收據拒絕。全矩陣50PASS，UNITOPTIONS已shown只增加收據，855完成數不變。v113／v114已正常關TUTORIAL12後開Caravel選項，來源COLONYUNIT／SHIPOPTIONS已確認，當次只警戒／下錨／不做更動三列；13GUI與未改顯示觀測／完整原版、來源RAM及存檔相同，v118～v122船隻兩欄限定CONFORMED：30px、新正常14GUI、六側完整原版／五側14取樣，來源、初始03／新增09存檔相同，圖示及核准區外不變；21種破壞收據拒絕、缺原版SKIP77。51PASS／856已顯示，只提升SHIPOPTIONS，不外推未驗三列或其他船隻局勢。v126～v129抵港TUTORIAL12已限定CONFORMED：30px五行、新正常14GUI及指紋／重播全等，六側完整原版／五側14取樣與03／新增09、來源一致，教學安全區外不變且Enter關閉無殘留；23種破壞收據拒絕與缺原版SKIP77。52PASS／857，只提升此次教學，不外推其他教學或裝貨。v120舊取樣限制保留。 v136～v139正常載貨四列、下錨三列限定CONFORMED：23GUI指紋與重播全等、六側完整原版／五側23取樣及來源／03／新增09一致，只改兩安全區且船隻圖示不變。正常卸貨／清除後恢復三列、Escape關閉無殘留，22種破壞收據拒絕。53PASS，857／989／89不變；Move to front、其他商品／船型與未驗船隻組合仍待驗。 |
| 目標178／Issue #55 | 進行中。整行暫藏、關框恢復已限定 CONFORMED，v55 正常 GUI 與五側驗收保留；讀檔城名恢復 v60 已限定 CONFORMED。船隻 ORDERS 前置熱鍵與關框殘字修正已限定 CONFORMED，v66 十張正常 GUI、十四行中文及六個停用灰色列通過，五側完整原版狀態與存檔不變。六個同文 MENU 來源與 VIEW 已限定驗收；陸地 v79 七張 GUI、四側完整狀態及存檔不變、v80 第一 Fortify28D來源與 v81 獨立21px／316×452量測，經 v82／v83 正式檢查、矩陣及普查後限定 CONFORMED。其他名稱與海上詞彙待接，#55 未完成。[目標178](docs/goals/178-orders-disabled-map-labels.md)。 |
| 驗證 | 矩陣設定目前64列；[既有矩陣報表](docs/verification-matrix.md)保留v235的63列歷史PASS，本次只重跑新港口船隻列及欄位守門，結果PASS，未重跑全矩陣。目標185其餘新收據仍待登錄，普查1945／882不因此增加。[規格047](docs/spec/047-ems-alias-coherence.md)的新局與既有存檔限定PASS保留。 |
| 全可達文字 | 最新目標181 europe-board-seven-census-v235分母1945項：已顯示882、待驗974、不可達89。重複普查相同，移除新Board七列碼頭列逐位元組還原原普查，完成信用0。只採檢查器實際驗過欄位，不外推ARMOPTIONS全部12列；全文中文化與完整交付未完成。 |
| 百科續驗／Issue #57 | [目標179](docs/goals/179-pedia-cargo.md)與[目標180](docs/goals/180-pedia-remaining.md)：貨物16、單位23、地形21、職業27、建築38、元勳25篇正文全部通過正常GUI、中英與缺圖集同狀態驗收，共150篇。地形海岸／河流已驗，三篇教育建築條列正文限定CONFORMED；先決條件22欄全部在`building-final-v3`正常GUI取樣點啟用，70個字串安全區與三側完整原版狀態通過；限定3M同步等待已CONFORMED。正常地形21次查詢來源已核對；Miscellaneous及額外16～23地形的情境路徑未完成，#57不關閉。正常F1已另驗兩頁與28個原版取樣點，但不增加原始來源完成數。 |
| 大河補證 | 正常 GUI 輸入的新增檢查點顯示「（大河）」22px，原版終點及既有檢查點與英文控制一致。補充檢查 `PASS_REPLAY`；新增檢查點尚未做真 GUI 截圖核對，不提高普查完成數。 |
| 遮擋顯示決策 | 已採用整行暫藏、關框恢復，排除框外碎片，不重問。規格032／038已限定CONFORMED；hide-formal-build-v51全部Go測試及hide-save-gui-v55正常GUI五側驗收通過。已驗適配器52e744725b95ae63aa289c6b9607e7e74c80052d8de1b2b5e7ffc5c644b2ed4c；當時二進位25388c520231acd8de73ce687d5f858ef6cce9a365225b7cd37bfc5ea01d50c1。v52長重播只兩側完整，v54退出原因未定位，部分收據保留不冒充通過。 |
| 存讀檔成功／Issue #61 | LOADGOOD原有正常第三欄讀COLONY02、提示及關閉驗收保留。新增SAVEGOOD：正常讀COLONY03、另存第一空列COLONY00、中文成功提示及關閉已限定CONFORMED；七張GUI逐像素相同、三側原版點與四側完整狀態／新舊存檔一致，同輸入原始查詢與DOS寫入已確認，正文30px。姓名／檔名保留原文，未知描述回退。兩標題與正常槽位清單另已限定CONFORMED，其他存讀檔結果未驗，#61維持進行中。 |
| 存讀檔槽位／Issue #61 | [目標181](docs/goals/181-colony-remaining.md)兩標題與8／10列空槽及描述已限定CONFORMED。正式v66全部Go回歸、固定工具鏈新字模、v67九張正常GUI、三側與v55程式對照／完整原版及存檔一致，v68同輸入原版查詢及片段讀取確認；v69正例及16種偽造拒絕、缺原版SKIP77。四欄21px與真正超寬回退通過；EXE:e4351e498b79舊合併觀測仍pending。其他存讀檔結果未驗，#61仍進行中。 |
| 存讀檔探索 | 由主選單正常載入原版 `COLONY09.SAV`，再選第一個欄位手動儲存成 `COLONY00.SAV` 並回到海上畫面，未注入快照。真 GUI、中英重播的終點 RAM 與兩份存檔逐位元組相同，六張安全區相同；首次回到世界畫面的抓圖未對齊，未算通過。收據在 `codex-audit/load-route-v2/`、`load-replays-v2/` 與 `load-save-summary.json`。空欄位與兩標題現已限定CONFORMED，其他存讀檔結果仍待驗；讀檔成功COLONY02提示另已驗，不能標為整個存讀檔完成；原版存檔只留本機。 |
| 封裝接線／Issue #53 | 全部中文顯示、輸入與音訊旗標及13份TSV／字模已收進三平台包，依實際二進位附12份授權與平台資料。正式封包、私用Linux／Wine正常輸入及macOS清單／shell通過；#53仍因974項未抽樣清冊與玩家回報待確認而保持OPEN，不宣稱全文中文化或全部即時音訊已驗。 |
| 工具鏈 | Go建置已恢復：直接沿用hr-go-ebiten固定SHA-256 1430a2cfb652c5733914e8116dd2011da21da53ec6b4de3a1482b2a94472f5b5，Go1.26.7／Ebitengine2.9.9／Xvfb／Pillow9.4.0已核對。[Dockerfile.verification](tools/Dockerfile.verification)記錄替代來源；離線重建與目前f4042b3d…逐位元組相同，Go與go vet通過，不另建重複映像。正式字模仍沿[font/README.md](font/README.md)契約。 |
| 發行 | [v.1.0.1-20261005](https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.1-20261005)已發布：三平台patch、90秒MP4與SHA-256清單，tag指向`0b9a791`。#53維持OPEN，#54維持CLOSED；玩家持續英文及即時音訊實聽待確認。正式輸出`dist-all/v.1.0.1-20261005/`，自帶原版完整包只留full-local。舊Release與tag未改動。 |
| 原版與隔離副本 | 原版唯讀；dosgolem隔離副本82a14b266e1b5bc904e2d0fe507daf6bea41a013，upstream推送DISABLED。通用補丁為[EMS修復](tools/dosgolem-ems-alias-coherence.patch)，未修改/home/anr2/cht/dosgolem。 |
| 游標精靈定位 | 精靈改以安全區實際差異定位（規格012附記），不再依前端滑鼠框。go vet／全測試通過，新二進位`091b2c68…`；31張實拍列內無英文、四路原版狀態全等、百科三側全等。延遲機制未重現（密集檢查點0.2M步內就位、實拍差異為截圖撕裂），列為預防性強固；檢查器輸入已還原並重過`PASS_TEXT_RETENTION`。使用者持續英文仍追蹤。 |

接手驗證中間物與摘要：`workplace/reports/goal178-orders/codex-audit/`；正式矩陣與普查以生成後的 `docs/verification-matrix.md`、`docs/text-census.md` 為準。

百科續驗入口：[目標180](docs/goals/180-pedia-remaining.md)。項目符號已依READY正式實作並通過正文正常GUI驗收；先決條件同步候選完成量測，正式3M等待修正已依READY實作並通過回歸，`sync-final-build`已完成正常GUI與三側驗收，全部22個先決條件通過加強檢查。歷史 v67／v68 為41列PASS及800已顯示；歷史v77為46列PASS、850已顯示／995待接；最新正式報告與分母以上方目前狀態表為準。船隻清單新增五個唯一來源；先前棄城驗收只將ABANDON由待接升為已顯示；同文選項不使ABANDON2完成。先前五種裝備需求仍是執行期組合，不是五個既有待辦完成。讀檔彙總仍pending。本次三份實際港口選項組合已計入；其他懸停與港口局勢未計入。

棄城確認正文已依原始查詢訂正為ABANDON；名稱顯示及取消後殘留修正已限定CONFORMED。city-abandon-v25正常GUI、八個取樣點、中文／原文／缺圖集完整原版狀態、來源定位及六個拒絕負例通過。候選讀字結束後仍觀測寫入至真正收尾，完全抹除即拒絕啟用。棄城驗收當時前端為goal181-colony-rest/abandon-final-build-v25/colonization-window，當時後續正式前端為europe-formal-build-v74；舊平台預檢尚未包含此修正，不外推三平台驗收。ABANDON2的1600年警告未觸發，保持待驗。零存量武器欄點擊未開出面板，不列武裝驗收。探勘city-equip-v19與city-arms-v20不計入普查，來源與後續入口見目標181。

最近正常入口探勘已到goal181-colony-rest/soldier-city-v33：正常選任、移民提示關閉後1496年，再正常點城確認Jamestown有士兵駐留。第二次kp3實際作用於船隻，勘誤保留於目標181；v34未增加居民；v36已先選取圍欄士兵再拖入建築，正常畫面為兩居民與50火槍，13個原版取樣點及三側完整狀態相同，未驗裝備或新增中文欄位。v35正常GAME→SAVE第三個空欄位已生成COLONY02.SAV（24371位元組，SHA-256 f683eb9132406e1dc7de5c90372f933b724b71b78a327551a305ba19d9a7d991），25個原版取樣點、完整原版狀態及三側新舊存檔位元組已通過；短入口v36由主選單第三欄正常讀取。探勘只留本機，不提高矩陣或普查；未接受新命名、棄城或完成裝備。可重生腳本見目標181。 v37逐畫面保存已命中正常選單，但原版訊息顯示COLONY03.SAV、實際更新工作副本COLONY02.SAV；未生成新03檔，原因未定。此差異已由v38核對：四側相同，DOS實際寫02；v37點選落在第四列之前的間隙。v41改用第四列墨跡中心正常生成COLONY03.SAV（24343位元組，d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77），11個共同取樣點及四側新舊存檔位元組相同；v45 DOS紀錄確認建立／寫入03，初始02未改。不需要修改原版行為或存檔格式。v48正常讀回見兩居民／50火槍；v49正常點士兵後已見圍欄士兵與庫存0；七個共同取樣點、四側完整原版狀態及初始03不變已通過，未新增中文欄位驗收，不增加普查。

陸地單位後續入口為 `goal178-orders/codex-audit/land-orders-gui-v78/`，正常主選單第一欄讀取 COLONY00、點選陸地士兵後觸發教學框，原選單點擊只關閉提示，尚未命中 ORDERS。v79 正常 Enter 關提示後已開出十列；v80／v81 七張GUI、四側完整狀態及存檔不變、第一個 Fortify 的28D來源及316×452安全區／21px量測已通過。規格036已由 v82／v83 正式驗收升限定 CONFORMED，清冊只新增第一 Fortify28D，完成數807。正常 COLONY03 裝備士兵後的 v84～v89 仍選船，未命中 Join Colony；Space意圖已按說明書更正為略過，W才是等待。v91旗標實際進城並開出改名框，十二張GUI與四側完整原版／存檔通過，該輪兩欄維持DRAFT，交由目標181；現在rename-gui-v50／v51來源／v52量測及v53／v54正式驗收已補齊，兩欄限定CONFORMED，只有RENAMECOLONY升shown。v88／v90只有局部失敗收據，不作完成證據。


SAVEGOOD已由目標181 v55～v60正式驗收。存讀檔標題與正常槽位清單已由v66～v70限定CONFORMED。下一步處理未完成入口，保留舊第三列合併觀測的pending。改名接受結果、Join／Pillage、其他存讀檔錯誤、港口購入成功／其他報告局勢及百科其他入口仍待驗；不重開已驗提示或遮擋決策。




歷史三個Go來源與GUI二進位／圖集指紋見目標181 europe-census-v77/formal-hashes.json；當時前端為 `workplace/reports/goal181-colony-rest/europe-formal-build-v74/colonization-window`，對話框與選單沿slot-fonts-v66，字串使用europe-fonts-v74/string/string-atlas.json，尚未收進已發布預覽版。



## 2026-10-08：碼頭灰色裝備欄正式驗收

上一輪分類為進展，四項Goal與遠端狀態未縮小。沿正常玩家路徑路由，核對工作樹、固定映像及現況。正常種子嘗試拖曳與取消碼頭預約；原版只有搭乘下一艘船，沒有立即登船，未取得帶貨四列，不偽稱完成。這些有完整GUI／終點的取證保留。另發現資金不足兩組六列回line-colors，原文／譯文已有，辨識器不接受色8且通用強調色判斷與本欄不符。

觀測cap8、行距12、正常68／強調149／灰色8／陰影47及128。原型加入固定港口／完整六列／色層／位置／來源守門，按各裝備列原版色分層，不按金錢或譯文決定可選性。兩組原型八取樣／三側全等，兩張六列安全區改變、其他6圖不變。各八灰色組合、九位數容量30px與破壞拒絕通過；逗號不在原數字模板而保留拒絕。兩次字模測試設定錯誤已按實際floor12修正，不當產品缺陷或放寬綁定。

規格035審READY後正式接線，新13GUI兩清單、灰列懸停／點選、取消與返回世界；四側完整原版、每點RAM／索引／色盤、WAV／存檔全等，GUI與重播逐像素相同，灰色前景索引8逐列確認且未混入68／149。只改五張清單安全區、其他8圖相同。正式2f0fbafd…、154項含子項Go／go vet，check_goal185_port_dim.py PASS，摘要8338305e…。船隻11圖與原版／WAV／存檔回歸也PASS。

矩陣新增第65列與欄位守門PASS，摘要e673e819…。只採完整標題，六列子集不提升完整12列來源；全矩陣與普查不因本輪提高。現況表已整理為唯一最新摘要，整理前全文逐字附在前條工作日誌，不用過時表重開已完成項。四項Goal仍進行，尚需帶貨四列、其餘範圍接線審查及收據整合。

沒有commit、push、遠端Issue寫入或新版發行。原版與健康種子唯讀，輸出UID/GID1000；所有本批容器已完成並由--rm清除，未新增映像，共用dosgolem未改，隔離副本乾淨。回合末自檢與工作清單渲染另留私用證據。

## 2026-10-08：正常返歐與港口帶貨四列

上一輪為實作進展，完整四項Goal保留。從目標181 v153正常自動存檔09進Jamestown，Shift拖27噸毛皮入船艙，回移動模式以G選London，再正常略過／推進回合返歐。首次仍在View按G未開清單，按實際畫面切回Move；不當產品缺陷。來自新世界貨物版畫中文命中，首次點船先開歐洲教學，不能把教學截圖叫四列完成。原版正常存為00，重啟後取得完整四列。

長旅程JSON在關窗後被容器結束截斷，原腳本只等檔案出現而未等程序退出。已修正private probe等待自有PID終止、可解析JSON／記憶體／inputs end一致；截斷檔保留失敗，未重命名成PASS。原版同輸入控制重播確認全部存檔，正常00 c9655cc2…／09 8a70bc0e…／原03 d3a462e7…一致。

四列完整來源誤中正文模板，中文擠在框頂一段。原版cap8、行距12、68／149／47／128，正文[63,68,265,82]、四列[81,84,207,132]。原型v1分流標記不被既有switch接受而回原文，v2使用既有no-template清單分支，八點／三側全等，只改四列一頁、其他7圖不變；來源／位置／cap／時序／正文像素與字模容量拒絕通過。審READY後正式只優先分流已驗四列，三列保留已驗子集。

正式8e27f92b…、154項含子項Go／go vet，新13GUI與四側完整原版、每點RAM／索引／色盤、WAV／存檔及回退全等。四列各30px，四次懸停與取消／返回無殘字；只修五張頁面的錯誤段落／清單區，其他8圖相同。check_goal185_port_four.py PASS，摘要36706c6b…；三列11圖與灰列13圖回歸均逐像素相同。矩陣第66列與完整來源守門PASS，c876f64f…，全矩陣／普查未重算。

本輪另核PEDIA原始形狀：164正文只在六類，MISCELLANEOUS只有12名稱且無MISC／COMPLETE正文鍵，不由此推論所有入口不可達。旅程實際命中三種整串未接：Sailing For、Now Arriving In、Go To London，兩列目的地清單也回英文；下一步按來源與欄位量測補接。四項Goal保持進行，未commit／push／遠端Issue寫入或發行。全批Docker有界、原版唯讀、UID/GID1000，所有工作容器完成／rm，未新建映像。

## 2026-10-09：返歐航程與G兩列目的地

完成正常裝27噸毛皮返歐所遇到的三個整串欄位及兩列目的地顯示，規格035／038依DRAFT、原型、READY至限定CONFORMED。航程三欄22px；G兩列27px，預設雙語城名與停用灰色保留。原型v1的同色重印被誤畫為4px描邊，機械同狀態通過但目視糊成色塊，未採用。依原版兩次149色、同位置墨跡與既有合併函式，在航程欄限定取消偽外框，v2三側與目視通過後才接正式來源。

正式07ba16de…，153項含子項Go、go vet、原版音樂測試通過且無skip。新14GUI／四側完整原版、每點RAM／索引／色盤、原始WAV、存檔與回退一致，GUI與中文重播逐像素相同。只有目的地、航行、抵達三張核准區改變，其餘11張相同；另回歸三列11張與四列13張港口，全部像素與原版、WAV、存檔相同。入口tools/check_goal185_voyage.py，正式摘要c5963bf0…、回歸1d62fb38…，完整指紋見規格038。192組容量只作量測，其他G目的地形狀／名稱仍回原文，不外推完整Issue。

矩陣第67列及四欄限定普查守門PASS，摘要04f63ee9…；歷史63PASS報表與1945／882／974／89普查未重算。工作清單61筆驗證執行通過，仍有manual未完成項；render與WORKLIST.md相同。四個遠端Issue仍OPEN，沒有遠端寫入、commit、push或發行。剩餘為接線範圍總審查、其他目的地／百科入口限制、其餘新收據登錄及普查更新。

私用fixture首版多餘image匯入與30px斷言已按實際27px量測訂正；首次正式檢查使用/out別名造成來源存檔父目錄無法定位，改用矩陣的/repo/workplace/reports路徑後通過。均為驗證環境／腳本問題。全部工作在既有固定Docker image內、原版唯讀、UID/GID1000，有界且--rm。所有本批容器已結束，無專案殘留容器、root-owned檔或.md目錄，原版素材未追蹤。隔離dosgolem乾淨、upstream推送DISABLED；本輪未寫入共用副本，其cmd/probe/main.go另有未提交修改，保留。

## 2026-10-09：歷史矩陣報表原文封存

以下保存原63PASS生成報告；新報告將明列42列本輪重驗及36列歷史證據，這段不能當作78列新PASS。

```markdown
# 驗證矩陣

由 `tools/verification_matrix.py` 依 `tools/verification-matrix.json` 產生；不要手改。收據只在已忽略的 `workplace/reports/`，本頁只列雜湊與數量。

- dosgolem：`c5953b90a0fc76c57f8dbbe0555f7a85d3198fe8`
- 原版輸入（各收據記錄的檔案雜湊合併，同名檔衝突 0 個）：`GAME.TXT` `67a6b5e22d1a…`、`LABELS.TXT` `e4af0da201eb…`、`NAMES.TXT` `4bf5ba261f71…`、`OPENING.EXE` `3c08c4af3a70…`、`VICEROY.EXE` `a17ed64c2767…`
- 結果：PASS 63、SKIP 0、FAIL 0；收據待重驗 0 列；原版輸入衝突 0；動態與靜態四類收據齊備：是

「待重驗」表示該列收據早於現行譯文（目標156 改稿）：字模已重烘、全部旗標載入綁定通過，但真 GUI 與重播尚未依新譯文重跑。

原版基線指英文控制收據的原版 RAM／VGA 索引／色盤；中文模式必須與它相同，差異只在中文安全區（由各檢查器核對）。

| 列 | 路徑 | 規格 | 檢查器 | 結果 | 基線 | 中文 | 英文 | 負例 | GUI 輸入 | 畫面格式 | 已知差異 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 遊戲選項標題與八列 | 動態 | 030、031 | `check_goal134_window.py` | PASS | 3 | 3 | 3 | 6 | 1 | 1280x800 RGB | GUI 截圖與重播可有一幀延遲，只比安全區；目標161 以定稿譯名重驗 |
| 英格蘭首次介紹兩頁 | 動態 | 025 | `check_goal135_window.py` | PASS | 3 | 3 | 3 | 2 | 1 | 1280x800 RGB | 目標161 以定稿譯名重驗 |
| 法國、西班牙、荷蘭首次介紹 | 動態 | 025 | `check_goal136_window.py` | PASS | 15 | 15 | 15 | 2 | 3 | 1280x800 RGB | 目標161 以定稿譯名重驗 |
| 其他國家遊戲選項、快捷鍵與讀檔路徑 | 動態 | 031 | `check_goal137_window.py` | PASS | 5 | 5 | 5 | 0 | 6 | 1280x800 RGB | 只驗英國存檔一例；檢查器驗證國別（介紹頁事件）；本列無專屬負例，回退由目標134負例涵蓋 |
| 退休確認框三欄 | 動態 | 028 | `check_goal138_window.py` | PASS | 2 | 2 | 2 | 2 | 1 | 1280x800 RGB | — |
| 第三張難度卡 | 動態 | 016 | `check_goal139_window.py` | PASS | 4 | 4 | 4 | 3 | 1 | 1280x800 RGB | — |
| 其餘三張國家旗卡 | 動態 | 022 | `check_goal140_window.py` | PASS | 6 | 6 | 6 | 3 | 1 | 1280x800 RGB | — |
| 十張開場字幕 | 動態 | 026、029 | `check_goal141_window.py` | PASS | 1 | 1 | 1 | 4 | 1 | 1280x800 RGB | 介紹頁後按鍵會讓原版跳過第五張起的字幕；目標161 以定稿譯名重驗 |
| 首則教學提示 | 動態 | 026 | `check_goal142_window.py` | PASS | 1 | 1 | 1 | 3 | 1 | 1280x800 RGB | GUI 截圖一幀延遲，只比安全區；目標161 以定稿譯名重驗 |
| 海上選單列、回合訊息與狀態欄 | 動態 | 032 | `check_goal143_window.py` | PASS | 1 | 1 | 1 | 4 | 1 | 1280x800 RGB | 目標161 以定稿譯名重驗 |
| 全部動態欄位同時開：Explorer 無跳過路徑與 Discoverer 路徑 | 動態 | 033 | `check_goal150_window.py` | PASS | 2 | 2 | 2 | 1 | 0 | 1280x800 RGB | 海上路徑與目標143 比對原版狀態相同、畫面差異只在海上安全區（目標156 改稿）；主選單第一列在錄製路徑因游標遮擋保留原文 |
| 規格033 資料模型：每則事件只歸一組鍵 | 動態 | 033 | `check_goal144_text_model.py` | PASS | 0 | 0 | 0 | 0 | 0 | — | 探針收據，不含中文畫面 |
| 開場製作名單七個職稱橫幅 | 靜態 | 034 | `check_goal151_window.py` | PASS | 1 | 1 | 1 | 4 | 1 | 1280x800 RGB | 人名橫幅 GUI 截圖與重播有一幀動畫差，該畫面不套用 |
| 功能鍵、數字鍵盤與組合鍵轉送 | 兩者 | 024 | `check_goal163_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 只驗數字鍵盤 8／7 與 F1；其餘鍵的遊戲語意未逐項驗 |
| 通用對話框正文（Land Ho、登陸詢問、原住民三則） | 兩者 | 035 | `check_goal165_window.py` | PASS | 1 | 1 | 1 | 2 | 1 | 1280x800 RGB | 只驗正文；選項列與輸入欄維持原文 |
| 載入訊息、主選單版本字串、國王接見、GAME 下拉選單 | 兩者 | 034、036 | `check_goal166_window.py` | PASS | 1 | 1 | 1 | 2 | 1 | 1280x800 RGB | 只驗英國國王接見與 GAME 下拉選單 |
| 全面回歸六點（主選單至旗卡、@BUILD1、遊戲選項、英格蘭介紹） | 兩者 | — | `check_regression.py` | PASS | 0 | 6 | 0 | 0 | 0 | 1280x800 RGB | 基準為目標161 以現行前端建立的回歸收據，兩次獨立重跑逐位元組相同 |
| 原版版本不符 fail-closed（五個核心檔拒絕啟動、製作名單圖檔回原文）與新前端下靜態重播不變 | 兩者 | 034 | `check_goal153_slice.py` | PASS | 1 | 1 | 1 | 1 | 0 | 1280x800 RGB | 改動圖檔會讓原版開場解碼失敗，故圖檔負例只跑到 2M 步（守門在載入時判定） |
| 其餘教學提示（顧問肖像木紋框）：@TUTORIAL2、5、11、13、14 | 兩者 | 035 | `check_goal167_window.py` | PASS | 1 | 1 | 1 | 2 | 1 | 1280x800 RGB | 只驗本路徑觸發的五則；其餘 13 則與地圖編輯器說明移交 #44／#45 |
| 連續字串通用覆蓋：殖民地畫面首屏、海上狀態欄補齊與 @TUTORIAL4 | 兩者 | 035、038 | `check_goal169_window.py` | PASS | 1 | 1 | 1 | 2 | 1 | 1280x800 RGB | 只驗殖民地首屏字串；殖民地內操作、歐洲、報告、百科與木刻畫標題牌（多色）另行處理 |
| 歐洲港口（主畫面、熱鍵按鈕、說明框與三個對話框提示）與顧問報告 F1～F10 | 兩者 | 035、038 | `check_goal170_window.py` | PASS | 1 | 1 | 1 | 2 | 1 | 1280x800 RGB | 對話框選項列（#46）維持原文；報告表格內放不下的殖民地名回原文；百科正文另案 |
| 殖民百科：六個類別的清單與首篇條目（標題、副標、數值行與正文段落） | 兩者 | 036、038 | `check_goal171_window.py` | PASS | 1 | 1 | 1 | 2 | 1 | 1280x800 RGB | 只驗六類首篇；其餘條目同一機制未逐篇真 GUI；Miscellaneous／Complete 類別未出現 |
| 殖民地畫面內操作：職業選單（兩欄）、建造清單、懸停標籤；對話框選項列改問字串層 | 兩者 | 035、038 | `check_goal172_window.py` | PASS | 1 | 1 | 1 | 2 | 1 | 1280x800 RGB | BUY 說明框未走到；武裝面板、多人口殖民地未到達 |
| 輸入欄標籤：命名新陸地、命名殖民地、Find Colony（輸入內容保留原樣） | 動態 | 035 | `check_goal174_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 改名、貿易路線命名、貨物數量輸入欄未觸發；Name: 另有字串層片段字典來源，反向對照只驗 Colony: |
| 前端音訊：OPL3 音樂與數位音效播放、錄音與開關音訊不影響原版 | 動態 | 037、039、040 | `check_goal176_window.py` | PASS | 2 | 2 | 2 | 0 | 1 | 1280x800 RGB | 容器以 ALSA null 裝置驗證播放器；實際聽感需在有音效卡的環境試聽 workplace 的 WAV；本列無專屬負例，以開關音訊兩兩比對與 WAV 有無數位音效區隔代替 |
| 下拉選單六個、引號變數訊息、狀態欄部分遮擋仍顯示中文 | 動態 | 032、035、036、038 | `check_goal177_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 本列保存較早的部分遮擋收據；當時超過七成遮擋仍露原文。現行整行暫藏已由目標178 v55／規格032限定CONFORMED，本列不作新策略驗收；Issue #55其餘詞彙仍待接。 |
| 船隻命令／VIEW中文、關閉恢復與六個MENU來源 | 動態 | 036 | `check_goal178_menu_sources.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 限定COLONY03正常船隻／VIEW欄位；六個MENU來源逐列核對，第一個Fortify及其他局勢仍待驗。 |
| ORDERS 選單停用項目（含可用項目整份）與地圖殖民地名稱標籤中文 | 動態 | 036、038 | `check_goal178_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 當前來源的完整既有覆蓋旗標重播通過：68 個原版檢查點相同；ORDERS 四張、地圖標籤 35 張與原 GUI 安全區相同。修正單字元誤取代與遮擋後來源恢復，45 張中文變化均只在狀態欄。控制、反向對照與原 GUI 取自原基準；另以 recovery-gui 的 53 張狀態欄驗證當前來源，來源恢復限定 CONFORMED。新 GUI 地圖標籤 34 張相同、1 張水面色盤差異仍待對齊，未冒充全過。遮擋期間殘字、其他國家名稱及正式封包全部旗標仍未驗收，阻擋目標178／Issue #55。玩家自訂殖民地名保持原樣（使用者 2026-09-28 決定） |
| 正常讀檔後逐篇貨物百科（16 篇） | 動態 | 036、038 | `check_goal179_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 只驗 16 篇貨物條目，包含真 GUI、中英同狀態與缺圖集反向對照。使用原版正常 GUI 儲存的檔案，不注入快照；存檔只留本機，其指紋由檢查器核對。其餘百科仍由 Issue #57 逐列驗收。 |
| 正常讀檔後逐篇單位百科（23篇） | 動態 | 036、038 | `check_goal180_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 真 GUI、中文重播的 23 篇正文及 75 個已啟用字串欄位安全區相同；中英與缺圖集負例完整原版狀態相同。固定來源為本機 goal180-pedia-rest/strings-fixed-build、formatted-dialog-atlas、six-string-templates.tsv；重產須指定這些已留存來源，當前預設入口是較新的 final-build。六個附欄模板與百科 Savannah 守門已驗；項目符號修正不屬此組來源。 |
| 正常讀檔後逐篇地形百科（21篇） | 動態 | 036、038 | `check_goal180_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正式 final-build、formatted-dialog-atlas、final-string-atlas、final-string-templates.tsv：正常GUI的21篇正文與96個字串欄位安全區與中文重播一致；包括海岸／河流，未翻譯字串0。中英、缺圖集負例完整原版狀態相同。21次正常查詢來源已確認，五組同文模板只歸屬實際來源8～11／15；16～23其他情境仍待驗，不是29個原始地形段落全部完成。 |
| 正常讀檔後逐篇職業百科（27篇） | 動態 | 036、038 | `check_goal180_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 真 GUI、中文重播的 27 篇正文及 118 個已啟用字串欄位安全區相同；中英與缺圖集負例完整原版狀態相同。固定來源為本機 goal180-pedia-rest/formatted-build-v2、formatted-dialog-atlas、baseline-string-templates.tsv；重產須指定這些已留存來源，當前預設入口是較新的 final-build。包含 JOB8 空白段與 JOB27；JOB18 仍無清單命中。 |
| 正常讀檔後逐篇開國元勳百科（25篇） | 動態 | 036、038 | `check_goal180_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 真 GUI、中文重播的 25 篇正文及 52 個已啟用字串欄位安全區相同；中英與缺圖集負例完整原版狀態相同。固定來源為本機 goal180-pedia-rest/formatted-build-v2、formatted-dialog-atlas、baseline-string-templates.tsv；重產須指定這些已留存來源，當前預設入口是較新的 final-build。包含五篇百分比；不涵蓋後續建築分段修正。 |
| 正常讀檔後逐篇建築百科（38篇正文與全部22個先決條件） | 動態 | 036、038 | `check_goal180_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正式sync-final-build：38篇正文、70個字串欄位與正常GUI安全區一致；22個先決條件均在逐篇GUI取樣點實際啟用。全部81個原版取樣點、中英及缺圖集完整狀態相同，未翻譯字串0。先決條件限定3M同步等待已驗，其餘字串仍2M；不涵蓋其他百科入口與重複地形來源。 |
| 正常百科下拉選單六項鍵盤環繞與進入單位清單 | 動態 | 036、038 | `check_goal180_menu_options.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 八次Down驗證六類循環，Enter進入單位清單，14個原版取樣點與三側完整狀態相同；此下拉選單不顯示Miscellaneous／Complete，不由此宣稱其他路徑無讀取端。 |
| 正常建城後資金不足BUYME0正文與三個建造面板欄位 | 動態 | 036、038 | `check_goal181_window.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常建城後資金不足碼頭正文與三個面板欄位，18個共同原版取樣點、GUI安全區、中英及缺圖集完整狀態相同；正文30px、長數值壓力22px、超界回原文。原版實際查詢BUYME0，事件BUYME1只是同文模板；來源映射只綁定本收據，可支付BUYME1選項仍待驗，不代表Issue #56完成。 |
| 正常讀檔進城、職業17項與議會五項元勳選擇 | 動態 | 036、038 | `check_goal181_city.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常COLONY01.SAV讀檔，12個共同取樣點與完整原版狀態相同；進城三欄、21px職業標題／17項清單、30px議會正文／五項選擇的GUI安全區相同，缺對話框圖集回原文。GUI設定city-turn-v5及新議會綁定字串圖集、現行模板；範圍不包含生產、更多職業、武裝與可支付BUY。 普查僅計入檢查器通過的七個欄位，不採未取GUI安全區的懸停事件。 |
| 正常伐木與木匠後的可支付BUYME1正文及兩項選擇 | 動態 | 036、038 | `check_goal181_city.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常讀入COLONY01.SAV、伐木、選任元勳、木匠與回合操作，1496年貨車481$／國庫1000$；26個共同取樣點、GUI安全區及中英／缺圖集完整原版狀態相同。正文30px、27位數排版壓力26px、超界回原文；原版實際查詢BUYME1與兩項選擇已驗。僅計檢查器通過的十一欄，不推定生產或價格公式。 1495／1496標題另已取正常GUI安全區驗收。 |
| 正常居民職業第二頁六項裝備需求與停用灰色 | 動態 | 036、038 | `check_goal181_city.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常主選單讀COLONY01.SAV、進城、居民職業及更多；六個原版取樣點、GUI安全區、中英與缺圖集完整原版狀態相同。第二頁標題及六項21px，士兵／斥候／龍騎兵保留原版色8停用灰色。重生設定city-more-v18、新議會字串圖集與現行模板；只採檢查器七欄，不代表已裝備或武裝操作完成。 |
| 正常棄城確認正文、兩選項及取消返回城市 | 動態 | 035、036、038 | `check_goal181_city.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常主選單讀COLONY01.SAV、進城、職業第二頁點前鋒、棄城確認及正常取消；八個共同取樣點、GUI安全區、中文／英文／缺圖集完整原版狀態相同。正文及兩選項30px，名稱欄位沿已審殖民地名稱顯示。候選完全抹除即回原文，取消後無殘像；只採檢查器九欄。重生指定city-abandon-v23路徑、city-abandon-v25輸出、abandon-final-build-v25正式二進位及新議會字串圖集。來源探針指定--marker-prefix @ABANDON並綁定同輸入與完整終點，不推定ABANDON2或接受棄城結果。 |
| 正常第三欄讀檔成功提示與關閉返回世界 | 動態 | 035、036 | `check_goal181_load.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常主選單讀v35合法COLONY02.SAV、讀檔成功與關閉提示；三個共同取樣點、正常GUI中文安全區、三側完整原版狀態相同。檔名僅在LOADGOOD的STRING0保留COLONY兩位數.SAV原值；30px與100個格式候選已量測，其他格式回原文。正式來源load-final-build-v42與現行圖集；不外推SAVEGOOD、其他讀檔欄位或存檔格式。 |
| 陸地命令十列中文、兩個停用灰色與第一Fortify來源 | 動態 | 036 | `check_goal178_land.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 限定COLONY00正常點士兵、關教學框後的十列；僅原始28D來源，不外推Join Colony、Pillage或其他單位。 |
| 正常城市改名兩欄、英文姓名編輯及取消 | 動態 | 035、036 | `check_goal181_rename.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常主選單第四欄讀COLONY03、進城點標題；九張GUI逐像素與中文重播相同，三側完整原版／存檔不變。提示30px，標籤因欄寬選29px；只採兩個已驗欄位及實際RENAMECOLONY段落，姓名英文保留。未驗接受改名或其他姓名長度。 |
| 正常另存檔成功中文提示與關閉 | 動態 | 035、038 | `check_goal181_savegood.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常讀COLONY03、另存第一空列COLONY00，七張GUI逐像素與中文重播相同，四側完整原版及新舊存檔一致。SAVEGOOD正文30px；只採GAME.TXT:@SAVEGOOD，姓名／檔名保留原文，未知描述回原文。其他存檔錯誤未驗。 |
| 正常存讀檔標題、空槽與描述清單 | 動態 | 035、036、038 | `check_goal181_slots.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常讀 COLONY03、存第一空列00，九GUI逐像素與中文重播相同，五側完整原版及新舊存檔一致。LOADGAME安全區底緣縮一列，兩標題及10／8列清單21px；空槽來源只供槽位回呼，未知描述、列數、字模不足或文字部分抹除均整段原文。v55程式同現行譯稿／字模、同新輸入對照，新增中文只在核准矩形，五個關框後畫面完全相同。其他存讀檔錯誤仍待驗。 |
| 正常歐洲港口取消、教學與F2至F10已量測欄位 | 動態 | 035、036、038 | `check_goal181_europe.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常讀COLONY03、E進港、取消招募／購買／訓練，再按F2至F10；109欄與26GUI逐像素／五側完整原版及存檔一致。購買7列30px，訓練18列21px，新報表2欄22px；原版128為下方陰影，真正混色停用列仍回原文。只採實際完整組合，不把25姓名合成排版當命中；三個城市名因欄寬回原文，未驗購入成功或其他局勢。 |
| 正常歐洲砲台購入確認、接受與金錢標題 | 動態 | 035、036、038 | `check_goal181_purchase.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常COLONY03讀檔、E進港、選500$砲台及Enter接受，金錢1000$→500$，碼頭出現砲台，再返回世界；僅確認正文、是／否選項及500$港口標題三欄。九GUI與中文／觀測畫面全等，五側完整原版、四側九共同取樣與原版存檔不變。正文／選項30px，標題22px；24組合成量測不計原版命中，不外推其他單位、取消、稅率事件。 |
| 正常職業清單選漁夫的未建碼頭正文 | 動態 | 035 | `check_goal181_nodocks.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常COLONY03進城、工作者職業清單選Fisherman，顯示NODOCKS正文並Escape關閉返回世界；一欄30px、兩行，safe[67,118,256,152]、墨跡[6,4,731,76]。八GUI與中文／觀測畫面全等，五側完整原版、四側八取樣與存檔一致。只採實際正文，不外推其他職業、拖曳或單位選項。 |
| 正常單位面板士兵標題及當次三列選項 | 動態 | 035、036 | `check_goal181_unit.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常COLONY03選任士兵、切右下單位面板並點士兵，中文標題及當次警戒／登船、駐守、不做更動三列30px；圖示及兩個核准文字區外不變。11GUI與中文／觀測全畫面相同，六側完整原版與五側11取樣、來源查詢及存檔一致。22個名稱只有合成字模量測，不外推其餘兩列、其他單位或其他選項狀態。 |
| 正常士兵駐守後的清除命令三列選項 | 動態 | 035、036 | `check_goal181_clear.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常COLONY03選任士兵、駐守後再開清單，清除命令／警戒或登船／不做更動三列30px。13GUI、六側完整原版、五側13取樣、來源與存檔一致；只改一個核准清單區，圖示與其他畫面不變。未觀測Move to front及其他單位狀態不外推；UNITOPTIONS已shown，不增加來源完成數。 |
| 正常港口輕帆船標題、三列選項及Escape關閉 | 動態 | 035、036 | `check_goal181_ship.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常COLONY03航向Jamestown、進城、關原文教學後的Caravel標題及原始第3／4／6列選項30px。14GUI、六側完整原版、五側14取樣、來源與03／原版新增09存檔相同；圖示與兩核准區外不變。23個合成名称量測不計正常命中；其他船隻局勢、未驗三列及TUTORIAL12不外推。 |
| 正常抵港教學、Enter關閉與畫布指紋同步 | 動態 | 013、035 | `check_goal181_tutorial.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常COLONY03航向Jamestown、進城後的抵港教學，原版cap9、876×456安全區、30px五行及Enter關閉。14GUI全畫面與畫布指紋一致；六側完整原版、五側14取樣、來源及本次03／原版新增09存檔相同，只有教學安全區相對v118改變。五個合成名稱不計正常命中；其他教學及裝貨操作未驗。 |
| 正常船隻載貨四列、下錨三列與卸貨／清除後恢復 | 動態 | 036 | `check_goal181_shipcargo.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 正常Jamestown港口Caravel載27毛皮後第3／4／5／6列，以及下錨後第2／3／6列；正常卸貨／清除後恢復及Escape關閉。兩清單各按原版cap8、pitch12量測30px，23GUI指紋全等，六側完整原版、五側23取樣與來源／03／新增09一致，僅兩安全區改變且圖示／其他畫面不變。SHIPOPTIONS父段落已shown，只補條件狀態收據。其他組合、船隻、Move to front與移貨提示未驗。 |
| 港口裝貨標題、按住提示與毛皮移入船隻／城市 | 動態 | 038 | `check_goal181_shipcargo.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 只驗Furs／Caravel來源池、四種貨物訊息及完整Loading Furs按住例外。24GUI指紋／五側完整原版及24原版取樣、來源RAM／03／09存檔全等；四欄原版cap5，三欄22px、Jamestown對照20px，差異只在原安全區。26圖同名城市回歸保留玩家名稱，不依字面套船名。23個破壞收據拒絕及缺原版SKIP77；其他商品／船型與廣泛按住文字未驗。 |
| 第一海上貿易路線、裝卸貨及母港目的地 | 動態 | 035、038 | `check_goal181_trade.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 只驗第一路線1、ROUTE九來源、London (England)與Jamestown兩城市提示。海21／陸19正常GUI與各六側完整原版、所有原版取樣及03／新COLONY00相同。編輯器／兩提示22px、清單30px，新增差異只在核准區，缺字模回原文；同文玩家路線名稱保留原字。113Go、穩定入口107Go、25個破壞收據拒絕、缺原版SKIP77；其他編號、網格城市名、母港及實際自動跑商未驗。 |
| 第一陸上貿易路線與目的地清單 | 動態 | 035、038 | `check_goal181_trade.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 只驗第一路線1、ROUTE九來源、London (England)與Jamestown兩城市提示。海21／陸19正常GUI與各六側完整原版、所有原版取樣及03／新COLONY00相同。編輯器／兩提示22px、清單30px，新增差異只在核准區，缺字模回原文；同文玩家路線名稱保留原字。113Go、穩定入口107Go、25個破壞收據拒絕、缺原版SKIP77；其他編號、網格城市名、母港及實際自動跑商未驗。 |
| 第一海上貿易路線前兩列預設城市 | 動態 | 038 | `check_goal181_tradegrid.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 第一編輯器前兩列實際Jamestown預設名。海21／陸19正常GUI及各六側完整原版、全部存檔相同；22px限定首欄，London改印／刪除沒有舊中文，缺圖集回原文。119Go與穩定入口113Go；合成數字／單字母與錯誤位置防護通過，正常GUI仍只採Jamestown／London。其他編號、網格母港與自動跑商未驗。 |
| 第一陸上貿易路線前兩列預設城市 | 動態 | 038 | `check_goal181_tradegrid.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 第一編輯器前兩列實際Jamestown預設名。海21／陸19正常GUI及各六側完整原版、全部存檔相同；22px限定首欄，London改印／刪除沒有舊中文，缺圖集回原文。119Go與穩定入口113Go；合成數字／單字母與錯誤位置防護通過，正常GUI仍只採Jamestown／London。其他編號、網格母港與自動跑商未驗。 |
| 歐洲購船後輕帆船裝載標題與碼頭清單 | 動態 | 035、038 | `check_goal181_dock.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 六種完整碼頭清單30px與固定Caravel港口裝載標題22px；新正常購船16／狀態29GUI，各六側完整原版、所有取樣與新舊存檔相同。新增差異只在核准區，缺圖集回原文且無舊港口中文。123Go、穩定入口113Go、31破壞拒絕及缺原版SKIP77；傳教士取消、移到碼頭最前面與其他船型未驗。 |
| 歐洲碼頭六種完整清單 | 動態 | 035、038 | `check_goal181_dock.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 六種完整碼頭清單30px與固定Caravel港口裝載標題22px；新正常購船16／狀態29GUI，各六側完整原版、所有取樣與新舊存檔相同。新增差異只在核准區，缺圖集回原文且無舊港口中文。123Go、穩定入口113Go、31破壞拒絕及缺原版SKIP77；傳教士取消、移到碼頭最前面與其他船型未驗。 |
| 歐洲傳教士清單與正常取消身分後復原 | 動態 | 035 | `check_goal181_dock.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 兩組已取證的傳教士三列清單30px；19張新正常GUI與各六側完整原版、所有取樣及新舊存檔相同。只改兩清單安全區；正常取消後恢復六列，關框及存檔畫面相同。124Go與穩定入口113Go、29破壞拒絕與缺原版SKIP77；移到碼頭最前面與單位標題未驗。 |
| 歐洲碼頭七列與正常移到最前面 | 動態 | 035 | `check_goal181_dock.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 一組已取證的碼頭七列清單30px；19張新正常GUI與各六側完整原版、所有取樣及新舊存檔相同。只改前後七列安全區；正常移到最前面後該單位變六列，關框及存檔畫面相同。125Go與穩定入口113Go、29破壞拒絕與缺原版SKIP77；Board七列與單位標題未驗。 |
| 歐洲碼頭Board七列與登船切換後重開 | 動態 | 035 | `check_goal181_dock.py` | PASS | 1 | 1 | 1 | 1 | 1 | 1280x800 RGB | 一組已取證的碼頭Board七列清單30px；21張新正常GUI與各六側完整原版、所有取樣及新舊存檔相同。只改登船切換後七列安全區；其餘20圖與v223基線相同，缺圖集回原文。142Go與穩定入口138Go、29破壞拒絕與缺原版SKIP77；單位標題未驗。 |

## 未驗範圍

- docs/text-census.tsv 中尚未驗到的可達文字，包括國王接見其餘局勢、教學提示、殖民地、歐洲港口、報告、外交及尚未驗收的百科頁面
- 靜態文字與事件版畫清冊中尚未通過覆蓋驗收的項目
- 按鍵跳過開場時職稱橫幅不出現（覆蓋不觸發，非缺陷）
- 其他名稱與海上詞彙、Join Colony及Pillage仍待逐列驗收
- 整局正常玩家路徑、存讀檔缺譯、人耳音訊、正式啟動器全部旗標與三平台交付驗收

## 重產收據

各列收據由表中 `regenerate` 腳本在 Docker 內重產（每列數十分鐘到數小時）；本矩陣只重跑檢查器，不重跑模擬。完整清單見 JSON 報告。

```

## 2026-10-09：範圍接線審查、收據登錄與歷史普查

正式來源核對164篇PEDIA正文及19個索引／概念單行、21教學模板與17版畫標題載入，正常畫面證據與載入證據分開。其餘11組收據由check_goal185_registration.py重跑并限定欄位登錄，不採同文TERRAIN23或伴隨事件提高來源數。五個舊檢查器以同檔案inode比較取代掛載路徑字串比較，修正/repo與/out別名的驗證環境問題。

矩陣78列中42可重驗PASS，35目錄缺失及text-model依賴缺失共36列僅歷史。依規格049從固定基準重產1953項／898shown／966pending／89unreachable，270可重驗、628僅歷史；原882已顯示保留，新增16已驗項與8執行期鍵，同文地形仍待驗。基準修改、重複鍵、錯版拒絕，缺原版77；原63PASS報表全文已封存上段。首次200秒逾時未完成，600秒有界重跑通過，沒有空目錄PASS。

新正常Caravel移動一格後G兩列皆68色，舊第二列只認8色而回英文。原始cap／字格／顏色／標題與原版端點已觀測，原型27px／三側／區外及反例通過後審READY，正式只增加68色。新10GUI含兩次懸停／取消，四側原版／WAV／存檔全等，原灰色及返歐14張回歸全等；153Go／go vet、無skip。正式54a1cf49…，入口check_goal185_coast.py，矩陣新增第79列与欄位守門3f19fa27…PASS。生成矩陣／普查仍為78列設定時的合併結果，新單列下一輪合併，不稱79列全PASS。

四個遠端Issue重新核對仍OPEN，沒有遠端寫入、commit、push或發行。原範圍保留；其他G城市／母港／行數與百科明確未確認入口仍審查。為多城市情境讀取既有正常city-more-v18的COLONY01，確認目前畫面；點左下工作者開的是職業選單，不能把它叫作外部可用殖民者，更未建立第二城。兩組探勘完整關窗，不當新功能完成證據。

所有工作沿既有固定Docker、原版唯讀、UID/GID1000、有界--rm；本批容器已全部完成，沒有專案殘留。基準只含鍵與metadata，含原文／像素／WAV／存檔留workplace。四項Goal保持active，不縮成已完成的局部範圍。

## 2026-10-09：完整職業標題與自訂頁三欄來源

接續完成#55、#56、#57、#61，四項仍in_progress。主機GitHub身分核對成功，四筆遠端Issue仍OPEN，未寫遠端。依知識路由重讀正常玩家路徑、文件職責與spec閘門；保留原版行為、輸入與現有驗收。

職業標題從原本政治家兩行限定修正，續取正常農夫單行與甘蔗兩行。農夫已有中文，甘蔗整則查譯成功卻仍被折行守門拒絕，依規格035完成DRAFT、原型、READY與正式模板分流。7236f28b…、154Go／go vet無skip，新14GUI／四側只改甘蔗標題安全區，政治家9圖及農夫單行12圖回歸全等。第一份連續點擊略過選單及兩次測試介面錯誤保留為探勘／測試問題，不列產品缺陷。來源、輸入與完整雜湊見規格035與check_goal185_profession_family.py。

矩陣加入兩行標題與完整模板第80／81列。以規格049重驗45列PASS並保留36列歷史證據；普查1955項／900已顯示／966待驗／89不可達，272可重驗、628僅歷史，前次已shown全部保留。生成報表已採用，TSV SHA-25686cac242cb6fb8459069f4f6b242b4e30921a19bc5b72b7dde34a9e8f6182eaa；矩陣報表9dfd90f6aea8a3b80d0dd296cd99c70407da1ee228f0b23178a6f7ef9c069e6c。歷史封存不重複追加。

正常主選單自訂新世界另取六張GUI／三側，確認標題、Moderate值及完成提示仍英文。規格038補來源與三欄原型，僅自訂頁標題指紋可繞過錯誤文字所有權；標題30px、值與提示22px，其他五張畫面不變。原型v2補每筆來源索引核對，READY後整合30464b52…；154Go／go vet無skip，正式GUI及四側驗收正在進行，尚未CONFORMED、未加矩陣。

本批全部工作在有界、無網路、UID/GID1000的Docker執行，已完成的一次性容器自刪；自訂正式GUI有界執行中，最終清理另記。原版像素、存檔、音訊與探勘只在忽略的workplace，沒有提交、push、打包或發行。

### 自訂三欄正式驗收補記

30464b52…已完成新6GUI／四側、三個核准区與14張職業回歸，154Go／go vet無skip，規格038限定CONFORMED。檢查器首次早於依賴回歸完成而缺run.json，等待同一容器完整結束後乾淨重跑PASS。第82矩陣列獨立PASS，摘要284a8f0d…；合併報告暫保留81列結果，沒有誤列82列全新PASS。正常四種設定卡入口探勘另在有界容器進行中，尚不作完成證據。

### 設定卡八值與美洲入口補記

正常點上、下縮圖完成四種設定卡八值，10GUI／三側、原版與回退PASS，第83矩陣列守門0398fb62…；首份中間卡片點擊未開清單而Escape退出原版，保留無效探勘，不列產品缺陷。檢查器首次為縮短stdout省略verified_fields，矩陣因此拒絕；恢復完整JSON、同收據與條件重跑PASS，未改遊戲或驗收条件。

美洲原版地圖與編輯器地圖兩條正常入口共7GUI／各三側完整原版、WAV与存檔一致；AMERICA正文及兩選項已有中文，MAPTOLOAD標題仍英文，檔名AMER2.MP原樣。原因線索為既有addDraft排除^^控制碼，正在只讀字格／色層觀測，尚無READY或正式變更。最新正式仍30464b52…，矩陣設定83列，生成報告保存81列合併結果。原版未修改，未提交、push或發行。

### 本批清理與交接

MAPTOLOAD原始字格／色層觀測已完整結束，同狀態通過，規格035新增DRAFT並索引既有來源；沒有根據DRAFT寫正式程式。下一步限0x2C8居中標題原型，不全域放寬^列。設定83列已登錄，生成普查報告仍保存81列合併結果，待後續新收據完成再重產。

工作清單JSON重新生成與WORKLIST一致，git diff --check通過；隔離dosgolem乾淨、upstream推送DISABLED。Git沒有追蹤原版EXE／SAV／MP／WAV／封存檔／PIK／SS／COL，規定find檢查沒有root-owned產物或.md目錄，本批專案容器全部自刪。Python所有權初查跟隨Wine z:連結而列出五個根目錄連結，不是新root-owned檔案；不修權限或刪除既有Wine前綴。未commit、push、發行或寫Issue。四項Goal仍進行中。

### 地圖載入標題原型與READY

原型878437f2…的已驗0x2C8單行居中模板，四正常GUI輸入／三側、原版、WAV与存檔一致，只改標題safe[106,87,214,100]，檔名与其餘三圖不變。30px、CJK28px墨跡及錯欄負例通過，審查31f58a8b…，規格035升READY後整合唯一分支与守門回歸。正式map-title-formal建置在有界容器進行中，尚未新GUI／四側，不稱CONFORMED，不增加矩陣／普查。

### 地圖載入標題正式驗收与本批普查

正式a1d43865…、155Go／go vet無skip，新7GUI／四側與自訂6圖回歸全等；只改0x2C8標題安全区，檔名原樣，正常取消與重新選擇無殘字。入口check_goal185_map_title.py，摘要7df30ac2…，第84列守門fbb54b10…PASS。原型及正式字級均30px，不全域放寬居中控制碼。

設定84列的新批合併普查正在有界無網路容器重驗48列、保留36歷史；尚未覆蓋前81列生成報告。四項Issue保持in_progress，没有提交、push、發行或遠端寫入。

### 84列普查逾時及建造面板續查

首場history-census-84已逐列48PASS，但text_census.py重新跑欄位／來源檢查時超過700秒，沒有完整摘要，未採用部分輸出。按同一image、命令、輸入與驗收条件，另開1200秒有界history-census-84-v2乾淨重跑；未修改證據重用或降低守門。此前建議減少重複工作保留為後續優化，當批採原契約。

正常COLONY03建造面板新8GUI取得，Wagon Train頂列仍英文。點(915,553)實際開BUY资金不足，未開更換清單；不由截圖名build-list-attempt算捲動完成。第二場改按已目視(1138,571)更換按鈕，有界探勘進行中，未改正式程式／矩陣／普查。

### 建造清單十圖基準与兩個DRAFT

正確更換按鈕取得12項中文清單，Down由貨車移到無生產，Escape回面板。新十GUI／三側原版、WAV与存檔一致，但清單標題導航後回英文、Wagon Train頂列啟用前撤銷。build-list-baseline-review.json凍結兩缺口，不新增完成信用。標題實際LABELS:@CTITLE已接，107923065步superseded-by-new-dialog；頂列兩次來源175570／175544，canvas-changed-before-screen。規格035／038新增DRAFT，只追標題當前像素与後續writer，正式尚無修復；原版規則不改。

### 84列合併普查正式採用

history-census-84-v2在相同image／脚本／輸入与條件下完成48列PASS与欄位歸屬；1200秒有界乾淨重跑通過，首場700秒逾時不採用。設定84列、48本輪可重驗、36僅歷史；普查1956／904／963／89，276可重驗、628僅歷史，前次shown全部保留。生成TSV 1567b4462f8d71536f9851ac218711a1b4914ec4a46c27cd621ba3405ceeeb19、Markdown f93825676a59da8774106773fa8cdf6147d55bf7c42c1864c180d4e3f26b08e3、矩陣報表e19f0599a002a5d5e29b7cdbf56f951d965081b5833bad7aab3c50bab4448a81，已採用，不手改生成內容。

新建造清單十圖／三側基準未加矩陣完成數，仍有兩個DRAFT保留缺口；#55、#56、#57、#61全部in_progress。工作清單與現況表已同步，未提交、push、發行或寫遠端。

## 2026-10-09：建造兩欄生命週期只讀觀測与READY

上一Goal輪有實際修正、正式驗收与84列普查採用，非無進度。接续正常十GUI凍結輸入的只讀觀測，完整原版、RAM与WAV全等。貨車face[236,132,277,138]、cap5／57色，僅底邊8像素在0CCC:006A被橫線54→57改色；清單導航時標題active与720byte快照完全相同，但新清單superseded撤銷。完整來源与觀測雜湊見規格035／038。

私用原型005a3aef…，十GUI／三側、原版／WAV／存檔與區外全等；貨車safe底裁138、22px，建造標題21px保留原像素身份与完整列組，格式／位置／像素／行数／時序反例通過。第一份差分清冊只列面板／取消兩張，實際清單右側仍露出原面板，改以同一核准矩形納入四張，未擴大區外容忍。原型審查672b47b4…；另正常改建碼頭，頂列原本中文，不誤列全建造名都缺譯。

READY後整合兩欄及適配器保留回呼，來源SHA從969cd179…更新為caf31e04430d315d9f26733e1890cf0b2380e21939c8511658de514f464bd547，build_window_prototype.py一併更新經審來源指紋。正式建置有界進行中，尚未新GUI／四側，不稱CONFORMED或關閉#56；矩陣与普查維持84列已採用結果。

### 建造兩欄正式限定CONFORMED

正式89e63cae…、156Go／go vet無skip，新14GUI／四側、全部原版与WAV／存檔／取樣一致；7圖只改貨車与建造標題核准區，其他7圖不變，多次導航、末列、取消与返回世界無殘字。碼頭12、職業14、地圖7圖共33回歸通過。公開check_goal185_build_lifecycle.py摘要1174a5e9…，矩陣第85列守門ac037788…PASS；合併普查保留前84列，不反覆全矩陣重跑到下一批。其他建造列組与真正長清單捲動仍待審查，四項Goal保持原範圍且in_progress。

### 本輪收尾狀態

本輪有實際进展：建造兩欄由RE、DRAFT、原型、READY至正式限定CONFORMED，14新GUI／四側及33回歸通過，版本89e63cae…、156Go／go vet、適配器受審caf31e04…，矩陣第85列。已驗碼頭頂列原本中文，沒有把其改算新缺譯。原始存檔盤點1536份沒有可直接讀年份的ASCII描述，未猜偏移；已知正常收據主要1494／1496，真正較長清單入口仍未取得。

四項Goal仍active，未關閉Issue或縮小目標。下一窄工作是其他建造列組／長清單与#55、#57、#61各明列未完範圍；不因個別修正通過宣稱完整完成。原版、字型與資料未改，未提交、push或發行；本輪工作容器均有界且已自刪，最後Git／所有權與清單自檢另核對。

## 2026-10-09：百科入口窄查与大河已驗範圍补登

上一輪建造兩欄正式验收為進度。主機gh核對四Issue仍OPEN，完整条件維持。IDA技能安装連結在容器內首次未掛其來源而讀不到，依router定位/home/anr2/ida_94_official/正式技能，沿現存py312-v1且最小輸出重驗，不重建duplicate image。原檔Miscellaneous舊定位實為大寫區塊名，已RESEARCH-LOG追加勘誤；類別6／全七類程式分支存在，但正常入口仍待參數与caller追查。

#55大河已實際显示（大河），31正常GUI／三側安全區与來源事件已核对。原登錄只採六篇正文，现check_goal185_representatives.py补大河source／22px／安全區与中英差分，registration只納精確(Major River)字段，重驗PASS，river-registration-review.json保存证明；不重翻、不改游戏或字模。全普查仍保存前84列、矩陣85設定，待本批完成再合併。

### 正常百科入口与正式接線目前審查

原PEDIA初始化已對回VICEROY原檔0x72AD3／AE E／B09／B3C／B57／B72六項命令0x70～75，原檔0x23904分派减70後调用類別selector。正常MENU標記94154050步、heap含一个分隔节点與六项终止链，公開入口检查通过；静态类別6／7分支仍保留，不把概念情境提示一併判不可达。

單行分類原型不加override與原分類相同，重疊／未知offset与缺proof／錯鍵／錯版／未confirmed反例全部拒絕，規格049升READY後採正式LIST_FILES行位移優先与入口proof守門。只更新MENU末兩行与PEDIA雜項類別清單三个键，原版MENU不修改。第86矩陣列守门035ca9f3…PASS，六項原始MENU行来源已scope绑定；86列合併普查进行中，旧報告保留。

最新正式来源164正文／19索引接線重验PASS，摘要b4a3117552389ef59467ef47425c6fd3eeee11ad6c54e7684cc745de3c813157；GUI与來源載入信用分開，不因template loaded增加正常命中。#57完整审查表挂在目标180，生成報告通過前保持in_progress。

### #57完整要求審查完成

公開check_goal185_pedia_completion.py逐項核對全部164正文／19索引接線、目前正式來源相同、保留六類歷史逐篇驗收、31正常GUI／三側、原版只建立六項与三個confirmed無類別入口分類、同文地形來源限制。結果PASS，摘要c1a1dbd1871b8006dbfc5b17b4075e7592a281f91ad82930ea6d4c15759448a4，本機工作項#57完成。正常版本限制以原版證據記錄，不修改遊戲或將其他概念提示全部改不可達。四項Goal仍未全部達成，其他三Issue繼續。

### #57遠端完成與本批正式合併

使用者Goal明確完成#57，完整本機審查通过后以主機gh關閉#57，回讀state=CLOSED、closedAt=2026-10-09T03:55:25Z，未修改Issue範圍或其他遠端項。整體Goal仍active，#55／#56／#61继续。

86列50PASS的首場current-census已正確標三個入口不可達，歷史merge原只更新shown而保留舊pending，按規格049補RE／原型／READY。正式merge只從checked-matrix confirmed unavailable keys更新，缺proof不變，未證實或歷史shown衝突拒絕。重用刚完成同一批，验原始、矩陣、檢查器与收據JSON／current-census SHA不變，只重合併三鍵，沒有冒稱新跑50列。1956／905／959／92、284可重驗／621歷史，TSV d122059cf52326d6f64ff826e0c9098ffe0c3176a55196a1cb4c53fd468b4fd1、報表c136ee8717bda8215a7ce77fc30f40e18450398b51df2148099dba7fecbe0a6f、矩陣4c461c12e0ec9c1a568830b8f4d608cdd9f9911b01b06f26d996b3ad5f52ebfc已採用。

正常新局已驗存檔COLONY00另取單列母港六GUI与三側：G標題中文、London (England)仍英文，原版／WAV／存檔一致；這是實際一列形狀缺接線，尚未正式修復，不新增城市或改原版。來源one-port-observer/fields.jsonl已取cap8／68／47／128與單列位置，下一步限定來源角色原型。

### 單列G母港原型／READY与正式進度

正常已驗新局存檔、六GUI／三側与只讀觀測確認單列London (England)仍英文，無城市注入。來源角色原型以NAMES完整hash取得HOMEPORT四名与COUNTRY四名、原標題safe／30px／原像素与2M時效、單列cap8字格守門；六GUI／三側只有一列安全區變，30px完整可讀。十一負例與16容量投影、兩列可選／灰色24GUI回歸通过，投影不當命中。

READY後整合正式70462b91…，156Go／go vet無skip，新九GUI含懸停、取消、重開与重取消，四側與两列回歸正在最後验收，不提前CONFORMED。新增country角色後百科164正文／19索引接線回歸仍同b4a31175…；公開#57完成checker只接受內容與當前正式来源相符的審查，不因已完成就忽略後續共用改動。

### 單列母港正式限定CONFORMED

正式70462b91…、156Go／go vet、新9GUI／四側与兩列24回歸全等，只改三張單列區，另六圖不變；30px、懸停／取消／重開无殘字。check_goal185_one_port.py摘要5bdefe47…、第87矩陣守門acd65ea7…，生成報告保存86列待下一批。四母港／四國名來源角色与16容量投影不當正常命中，其他行数继续原Scope。新增country角色后百科164正文／19索引与公開#57完成回歸仍PASS，未重開已完成Issue。

接续以健康COLONY03、正常職業第二頁選士兵、退出城市与m／c／w觀察陸地單位，建立第二城僅作後續正常入口，尚未命中不稱可行／完成，不注入城市或改存檔。

## 2026-10-09：完成#61與目的地名稱缺口取證

- 依使用者目前Goal繼續#55／#56／#57／#61。載入復古正常玩家路徑、dosgolem能力與文件職責入口；沿固定hr-go-ebiten 1430a2cf、UID/GID1000及隔離dosgolem82a14b2。正式70462b91與原版資料未改，沒有新發行包。
- 當前來源審查通過六項開局27行、21教學及17版畫。來源審查分別為3fc1c56f7983aa1bf43c65bdccf85cceca688ff10b16cfc4c6e0e4eb773ea2b1、072931935c0702b24275272127e38529168bbc3cefa9b77242a801a3e7bb1694；Go兩項審查實際執行PASS。教學與版畫仍採已確認代表抽樣，不宣稱全部原始段落新命中。
- 新公開版畫檢查器重驗三種事件、十一點完整原版與精確標題像素，原圖保留。第88列登錄後完整執行52個可重驗列與普查，全PASS，另36列僅歷史；1956／906／958／92。第89列追加#61完成審查及正常AMERICA兩欄，核對前52列設定、檢查器與JSON收據未變，只作兩欄增量普查；唯一新shown為GAME.TXT:@AMERICA，全部舊shown保留。
- 採用89列設定，52本批PASS加1追加、36歷史。普查1956項／907shown／957pending／92unreachable，286可重驗、621僅歷史；TSV 7af46663e3b901f2c643bd31c57742ef01176b36f3c97599563061bca0931df9。報表明列WOODCUT段落的三種代表標題，沒有將17次模板載入當成17次正常命中。
- #61完成審查涵蓋正常新局存讀、五種失敗、自訂設定與地圖載入、保留開局／教學驗收及版畫抽樣，實際PASS，最終摘要7f193928c3a40e6a8f8884cffc52928d3b7def09273f103ebacc174e8740e80c。#57回歸PASS，摘要5f002ddd222dbe0827f95a523a764a90f8662c5a282abe103bd1577649eb3a1e。兩個新檢查器缺原版皆明確77。
- 主機gh認證成功，依已授權Goal關閉#61，回讀CLOSED／2026-10-09T04:46:57Z；#57仍CLOSED，#55／#56仍OPEN。沒有Issue留言、commit、push或Release。唯一現況表、機器清單與生成WORKLIST已更新。
- 工作清單驗證發現#14與#38的舊靜態訊號仍指向新版矩陣摘要，先以已封存63PASS作正對照，再改連WORKLOG的歷史矩陣，保持既有完成狀態。第一場驗證因缺訊號觸發舊工具的note KeyError；修正證據連結後乾淨重跑PASS，未偽造目前矩陣全PASS。
- #55正常把Jamestown改名為Quebec並由VIEW回移動模式開G。13GUI、中文／原文／缺字模三側及觀測的完整原版、WAV、存檔全等，但兩列仍英文；155265001步line-no-template，Q的cap9與Jamestown的cap8不同。輸入fee75757b770de38b68b1f584efca9f745f737170ec7b55ec33a56b9c369b83b，終點173200000／RAM190ee2baa3aeb012d62d5f3cb79d07b11a363501f73efef46630ae0585d6e3de。DRAFT035已記來源與字格，候選／READY尚未建立。
- 單位切換探勘沒有建立第二城，不當成多城市驗收。第一份改名路徑仍在檢視模式，G未開選單；後續使用可見VIEW選單才成功。縮短前綴未保留各模態等待的交互探勘沒有武裝成功，既有完整武裝證據保留。#56長清單與其餘完整範圍仍待收尾。
- 所有本批容器均有界且以--rm結束，沒有本批殘留；其他專案容器保留。find未見root-owned檔或誤建.md目錄，新增檔與輸出抽查1000:1000，原版EXE／存檔／封存檔／i64／workplace未被追蹤。Git差異檢查通過；隔離dosgolem乾淨、upstream推送DISABLED。工作樹修改保留，Goal仍active。

### 接續私用名稱候選與VIEW殘字

私用variable-two-port-candidate只新增已驗G兩列的角色與城市回呼，正式程式不變。候選09e8b2ba2d0b19e81ff38b6bf7df812a2deef051dfe3cccd615418bf9c999631，157Go／go vet無skip。首場缺COLONIZATION_MUSIC_ROOT而155PASS／2skip，補唯讀/game後同映像乾淨重跑，沒有略過音樂回歸。工具快取只放既有workplace/gocache的專用goal185-go126，UID/GID1000。

沿同13GUI輸入中文／原文／缺字模及基線重播，完整原版、所有取樣索引／色盤、WAV與存檔一致。只有renamed-destinations在safe[76,96,157,120]新增兩列30px中文，其餘12圖不變；已目視。摘要ee21d703251a8c04cfb534cd29605d9775189082f5ea3e12fa1883a1e39e7283。比較器首場錯把逐行source事件當成必有zh欄，改依實際items、已量測文字與畫面驗證後通過，沒有改產品事件格式。

172個唯一預設名均以同一Quebec矩形作容量投影，166可容納、6回退，不外推各名稱原版字寬或正常命中；尚未READY與正式採用。六個名稱及下一閘門寫入規格035與唯一現況表。

同正常路徑另確認VIEW選Move Pieces後殘字：154275001步，原文世界底圖已恢復，中文仍畫十二項選單，木框已關。MENU.TXT:0x00000240+list於145860001 expired，146664144重建source、146850001又active、155100001才expired；中文PNG22ff1044…、原文c26c8b7b…。這是confirmed顯示失敗，來源重活化的根因仍是假說，下一切片限定145～148M；不以目的地候選掩蓋，也不重開#61或既有Escape關閉驗收。

候選與殘字的私用入口已掛進目標185與規格035，工作清單重新產生及verify通過。#55／#56仍in_progress，#57／#61completed；本批不提高907shown、不新增發行或遠端寫入。後續容器均已退出，收尾再核對擁有權、版控與Docker清理。

## 2026-10-09：MENU殘字正式修復與長名稱內框

- 上一Goal輪有實質進展，本輪延續完整#55／#56範圍。載入路由、規格閘門及目前交接；主機gh認證成功並回讀#55／#56原始範圍，兩者仍OPEN，未改完成條件或遠端狀態。
- 只讀窄觀測在146825614步確認12列／178字元、1092個印字位置只剩5點lastText，八列存活0。五點都是新世界地圖的同色68，finish卻仍建立整份MENU。觀測025f7669…與原完整終點相同；直接原因為任一點存活的判定，略過同色寫入造成五點標記殘留屬強推論。
- 真實資料局部回歸與可攜自製字串回歸皆在舊正式FAIL。私用只對最終MENU.TXT來源要求全部印字位置存活，候選444c01b2…、157Go／go vet無skip、13輸入三側只修一區、41回歸PASS。首場31圖舊基線未含已完成VIEW欄位，差異僅右欄；用目前70462b91同輸入基線乾淨重跑，產品未改。
- READY前另走17新GUI、真游標懸停兩列、Escape、重開、點選Move Pieces及G取消，四側原版／WAV／存檔全等。正式僅增加MENU完整存活守門，f8d65786000bbaecd037fbdf17050bb19ed7d1f9cd5e31d5f0e69450f87ff687，157Go／go vet無skip。
- 正式再走17新GUI及四側、31百科與10VIEW回歸全部PASS，只在Move Pieces關框區清除殘字，其餘16圖不變；兩個VIEW關框區逐像素等於原版。輸入98294d85…，194600000／RAM8578cf2d…。公開check_goal185_menu_survival.py摘要cb4e981e…，規格035限定CONFORMED，第90列PASS。版面21px與原版資料／規則／存檔不變。
- 當前正式來源重編三項接線審查：PEDIA164／19摘要仍b4a31175…，教學21／版畫17仍3fc1c56f…，開局27仍07293193…。公開#57／#61檢查器只接受內容指紋與當前來源皆相符的已執行審查；完整回歸PASS，兩Issue不重開。
- 增量普查只重驗第90列與受影響#61列，先核對其他已驗檢查器及收據未變，沿89批合併。狀態變化0，1956／907／957／92，288可重驗、619歷史；54個可重驗列不稱本次全重跑。TSV79dfd26b8f7bf6073e5e668c1ee933175913fc87dc0c301c4b5ef7ec9df838c7。
- 長名稱另正常改名New Amsterdam，13GUI及只讀觀測／原文控制同原版。原文字寬仍短於London，實際內框62／77／257，按三像素內距可到254。私用port-family-candidate 1cead102…按當次完整列組及內框排版，158Go／go vet無skip，172唯一名容量無溢出；短名／長名26取樣三側只改兩張G安全區，33既有目的地圖不變。仍DRAFT，未正式採用，不冒稱三列正常命中。
- 人口探勘點底部圖示取得現有毛皮獵人的職業選單，沒有第三名居民。兩個交互容器到期／handle消失後以docker確認已停止，均缺完整gui.inputs.json／json／memory，只保留診斷，不能採驗人口或SAV。正常返歐探勘已見木匠碼頭選單預設登下一艘船、船隻啟航確認；SailYes後已回世界，再按Escape會開退出DOS確認。下一步有限腳本重走，在世界直接用GAME存檔，並正常關窗，不重複長時間交互等待。
- 首場交互前綴完整等各模態，仍不得由圖示或未完成收據推定加入成功；前輪屋頂拖放等負例不重開。#56真正較長清單與接線總審查、#55名稱候選正式化與總審查仍待完成。#57／#61保持completed，Goal active，未commit／push／Release／Issue留言。
- 一次性建置、重播與探勘均有資源限額及逾時、UID/GID1000；交互到期未當產品崩潰，相關容器已由--rm清理。原版與隔離dosgolem唯讀；新矩陣／普查寫入只掛tools／docs或指定頂層檔，原版輸入保持唯讀。交接與生成WORKLIST verify通過，最後另核對Git、擁有權與Docker。

診斷另見退出確認畫面右欄「回合結束Turn」，尚無完整同輸入控制，先不判根因或提高普查。下一次有限腳本在SailYes後直接存檔、正常關窗，並核對該回合狀態列。現有兩份交互探勘缺收據，不作第三居民、船已運抵或狀態列完成證據。

90列普查採用後再驗公開#57／#61完成檢查均PASS，摘要分別dd8685f31154cd2bf22d54cd136ef63d29765347d3b383f9aecfb1812f685538、46aa4033ec283655ed2210e6d3933e1f79fbee43050f85dc1c75b854eaef892b。新MENU檢查器缺原版明確77；工作清單／語法／Git差異及擁有權檢查通過，無原版素材誤追蹤，相關容器全部清理。Goal仍active，不以個別修復或候選代替#55／#56完整完成。


## 2026-10-09 接手：目的地正式狀態勘誤與教學城市變數

核對Goal為完成#55／#56／#57／#61，持續active。同步CONTEXT與唯一worklist：目的地族群6ea4f982已正式驗收，92批普查1956／908／956／92；#61因正常TUTORIAL15／7城市變數漏接已遠端重開OPEN，保留較早驗收，不以21模板載入當完整變數接線。

私用候選4e0e9058沿正常返航17GUI輸入四側，只改兩提示各自安全區，原版CPU／RAM／索引／色盤／WAV／存檔全等；158Go／go vet無skip。來源與角色依規格035升READY後，正式c30275a8、160Go／go vet無skip，新17正常GUI／四側及真實7／12／15語料測試PASS，限定CONFORMED。公開check_goal185_tutorial_cities.py，審查1965c12686f82aa83d418fb66a85ee67cbf758c2ac36d7a970597dfc2b57e8d2。原版素材、存檔、圖像及測試語料只留忽略的workplace證據根。

第一次候選測試未按正式事件的空白正規化契約呼叫match，出現no-template；改為原始位移讀取並用dialogNormalize後，同工具鏈乾淨重跑通過。差分審查最初誤讀Update步數，改讀既有gui.shots實際frame_step後通過。均是驗證腳本問題，不當產品缺陷。

正常居民探勘已取得完整有限關窗收據；B與V後仍在世界，不聲稱第三居民或長建造清單完成。啟動時曾漏session start及誤用不存在的scratch目錄，查日誌後改用實際save目錄，保留失敗診斷。回合結束重印背景私用候選仍損及彈窗4像素，沒有採用。

矩陣設定新增第93列教學城市驗收；舊#61完整審查新增實際提示與TUTORIAL6未接線閘門。僅這兩列重跑，新增列PASS，完整#61列FAIL，生成矩陣及普查仍保存92批待增量調和。未commit、push、發行或留言Issue。本輪結束的Docker及權利檢查另見接續驗證記錄。

收尾驗證：公開教學檢查器補齊矩陣要求的final_step與final_memory_sha256輸出後，同容器命令乾淨重跑，新增教學列PASS，完整#61列因TUTORIAL6城市變數缺接線明確FAIL。這次初始final_step缺欄是檢查器整合問題，非產品缺陷。審查摘要更新為1965c126…。git diff --check通過；find工作根未見root-owned檔案或偽裝成.md的目錄，抽查來源／工作清單／收據均1000:1000。本輪colonization-goal185容器無執行中或停止殘留，未清理其他專案資源。


## 2026-10-09 接續：教學6來源審查與15項建造清單修復

前輪為進展：兩則城市教學7／15已完成正式修復。本輪核對遠端#55／56／61均OPEN，#56原範圍包含多人口、BUY、武裝及建造捲動，未縮成目前15項清單。主機gh auth status成功，僅讀Issue，未對外寫入。

依IDA技能從既有VICEROY資料庫唯讀複製到容器/tmp，IDA9.4最小輸出schema／SHA及526函式核對成功。TUTORIAL6標記檔案0x1E867、IDA MZ EA0x2C467、無直接xref；不因此宣稱不可達或執行時角色confirmed。私用教學6候選2915ea12通過161Go／go vet，另外對help與corpus兩份真實來源的21教學逐一展開占位符，來源match全部PASS。候選未READY、未進正式，#61保持未完成。

正常到港進城被Adam Smith通知與介紹打斷，先由圖片確認，再處理通知、版畫及百科。完整有限流程取得15項建造清單，標題中文而項目英文。只讀觀測完整CPU／RAM／WAV與原GUI相同：初開36,858步停頓切在T字元與NUL間，readPos奇數導致前段丟棄；Down時WAREHOUSE與成本間38,210步亦超過舊20,000門檻。來源基址未變。初版限定守門仍部分英文，觀測證實初開標題等待VGA、afterSafe尚未建立；第二版另保存來源標題快照，不替代VGA啟用條件。

私用第二版3b0bf4e3…：160Go／go vet、14種守門正反例、29正常GUI三側與14張舊12項回歸PASS。原型依規格035升READY後接正式41107b24…；161Go／go vet無skip，新31正常GUI四側，多次Down／Up／取消，原始失敗29圖正式回歸與舊12項14圖均PASS。新GUI初開舊程式也未分段，驗收因此以實際三張導航差分加原始失敗輸入驗證修復，不虛構每張新圖都應有差異。公開check_goal185_build_transaction.py，摘要ba5e258cbed9929c305d1da5f7d73de8452dd16ac04c63548ccb61ff68414013，限定CONFORMED。

適配器來源b51b76ca2e2ce24ae7d3fb063a01d9f4002c6aefd0aa86e62bb49dd20b075439，隔離dosgolem82a14b2不變。建置來源指紋已同步；沒有修改原版規則、資料、存檔或所有畫面的逾時。既有教學驗收以相關模板載入／編譯／匹配函式逐字一致核對，避免因同檔建造函式改動重開已完成項。新正常31GUI也保留到港與成長提示。矩陣設定94列，生成報告及普查仍保存92批待調和，不冒增shown。

驗收腳本曾誤把新初開必須有像素差異當條件；確認舊程式在該新輸入本來就通過後，另加原始失敗29圖嚴格回歸。其後輸出迴圈覆蓋argparse變數，所有檢查已過但寫報告失敗，修正命名後同容器命令乾淨重跑PASS。這些是驗證腳本問題，不當產品缺陷。正式新素材及截圖只留忽略workplace，未commit、push、發行或留言Issue。

本輪最終驗證：矩陣三列實際為建造來源事務PASS、教學城市PASS、完整#61因教學6未接線FAIL，摘要2139a053fabc23e90a587365f386e7e0effc30c9b2cbd817ca8b2fda9c32efd6。公開包裝器最初將--output設為必填，不符矩陣先讀stdout的契約；改為可選暫存報告後，同命令乾淨重跑得到上述結果。百科完成審查仍PASS，摘要f620f5ff4e021ced5dfd5b1cc5433ea29a2f2a70ca5a7bcd0962f78aaf5339d4。目前來源的164正文／19索引、21教學模板／17版畫、六項開局27行載入審查均實際PASS，輸出指紋與先前相同，未當成教學6變數已正式接線。

收尾git diff --check通過，Git未追蹤EXE／SAV／WAV／zip／rar／i64；工作根find未見root-owned檔案或.md目錄，抽查來源、檢查器及worklist均1000:1000。colonization-goal185容器無執行中或停止殘留，沒有清理其他專案資源。Goal持續active，#55／56／61仍OPEN；未發行本輪修正。


## 2026-10-09 接續：回合結束重印背景與原版彈窗外框

前輪為進展，15項建造來源事務已完成。本輪讀取路由的規格閘門入口，保留目前來源與既有驗收。遠端核對#55／56／61 OPEN、#57 CLOSED，Git身分正確，沒有Issue寫入。

正常教學6前置由新局存檔、海岸命名、下一回合與登陸選項逐步取證，保存COLONY01／02。原文控制與第三波手冊說明確認單位啟用與教學11會影響後續輸入；未建城、未命中教學6，不把檔名與圖片當完成。正常先驅者、士兵選取標籤英文已記DRAFT035，括號內None／Expert角色仍不猜。貿易標題與來源context硬綁路線1、城市列1／2及London限制另記DRAFT038，九標籤shown不證明全接線。

重印背景候選最初已消除英文尾字，卻損壞新彈窗黑框。原版索引量測確定四邊完整封閉矩形；單段safe會遇船隻選取列的黑色，因此合併同框標題／選項safe後仍逐點驗四邊。私用25f6493d候選163Go／go vet無skip，25正常輸入三側與29個原尾字點背景、四種框邊、職業14／港口10回歸通過。港口兩張恢復原版底邊黑線，其他8張不變，沒有把修復當回歸缺陷。

依規格038 READY接正式b4fe380e…，163Go／go vet無skip，適配器7d136aef…、隔離dosgolem82a14b2。新11正常GUI四側、原始25圖正式重播、長建造31圖通過；新11八張只改回合結束區或原版邊線，29尾字點逐點還原背景。長建造只有六張回合結束區改善，建造文字與其他25張不變。公開check_goal185_reprint_background.py，限定CONFORMED，摘要8e130d8fe9c72e4d601ebe655a7486e62f9eb02b439ede99994990daa5652d4c。其他未知多色樣式不外推。

新27GUI全程腳本在1498到歐洲時船未入港，沒有成立碼頭教學前置；保留診斷，不採計27張完成。改從已驗出航存檔取得新11張正常重印／存檔，港口以原始完整25輸入正式重播補足。首次重印與港口回歸曾用了多一個或少一個存檔的種子，核對初始清單後以正確03／09重跑，錯種子只留診斷。Xvfb曾未就緒，新增xdpyinfo就緒檢查後同流程乾淨重跑。私用審查換行轉義錯誤已修復；新來源另有未展示Y64欄，不要求所有source都等於已驗Y91安全區，只驗實際展示欄位。以上不當產品缺陷。

受影響四矩陣列實際PASS重印／建造／教學城市，整體#61因教學6未正式接線FAIL；百科完整審查保留PASS。已驗建造收據仍綁411正式與原dialog來源，後續渲染器以相同31輸入的正式回歸核對，不因同一適配器其他區段變更重開建造。矩陣設定95，生成報告與普查保存92批待調和，不冒增shown或稱95列全新重跑。未commit、push或發行，原版／存檔／圖像／WAV只在忽略目錄。

本輪收尾：四列單獨重驗結果為PASS／PASS／PASS／FAIL，摘要e9c1f47edc264ac4345051bec329aa78127ce689c684cf48323251f9741e01df；百科保留摘要仍f620f5ff…。主機gh核對#55／56／61 OPEN、#57 CLOSED，未改狀態。git diff --check通過，沒有追蹤EXE／SAV／WAV／zip／rar／i64；find工作根未見root-owned檔案或.md目錄，抽查來源／檢查器／worklist均1000:1000。colonization-goal185容器全部結束並清除，沒有清理其他專案。

教學6前置後續的多次建城輸入尚未成功，不再用追加猜測按鍵當下一步。tutorial6-move-mode-gui的最近原始對話為Stay With Ships／Make Landfall，沒有建城或教學6命中。應先核對原版VIEW／Move Pieces模式、單位選擇與登陸狀態的實際控制流程；既有正常COLONY01／02與原文控制收據可重用，不重新從冷新局盤點。這是尚待理解的正常操作前置，不當dosgolem產品缺陷，也不是外部阻塞，Goal維持active。

## 2026-10-09 接續：教學6、單位標籤與97列增量普查

前輪分類為無進展：前輪回覆沒有可採用的專案完成結論。本輪重新核對工作樹、原版與遠端Issue，沿用既有165Go／go vet無skip建置24b7816b…，沒有重啟已終止程序。路由載入規格閘門、文件職責與正常遊玩入口。Git身分正確，遠端開始時#55／56／61 OPEN、#57 CLOSED。

正常tutorial6-later-colony-gui已完整關窗，真正命中教學6，不再沿未成功建城路徑猜測按鍵。正式新13GUI四側、原版完整狀態／WAV／存檔與原文回退PASS，只有一張提示安全區改變；21教學來源逐變數及貨物／城市／母港隔離、實際30px墨跡與超界回退通過。公開check_goal185_tutorial_cargo.py，規格035限定CONFORMED。

單位標籤正式11GUI四側PASS，三張前鋒安全區改變、其餘八張不變；士兵10張正式回歸與既有候選相同，184組只驗容量。公開check_goal185_unit_caption.py，規格035限定CONFORMED。合併教學6後正式24b7816b…的GUI重播與標籤正式6c3f916e…逐像素相同，兩個版本在檢查器分別記錄。當前31張建造回歸與重印正式版全等；保留原check_build_transaction_formal.py，新增check_build_transaction_retained.py核對目前來源及31圖，不覆寫舊證據。

完整#61審查改用實際21則變數測試與正常教學6，移除只查原始碼文字存在的閘門；教學7／12／15以精確比對既有分支保留驗收。目前來源百科164正文／19索引、開局27行及教學21／版畫17審查均PASS。報表三城A方案亦重驗PASS，22px單行及擴大安全區已完成，README的舊英文說明已訂正。

本輪六個新增或受影響矩陣列PASS，沿92批保留其他55可重驗列及36歷史列，採用97列增量普查。1972項／928shown／952pending／92unreachable，其中310可重驗、618歷史。新增20項為三則實際教學、No Production及16種正常執行期形狀，後者含15項建造整組與分列及前鋒標籤；不是20則新譯文，也不把184容量或未驗事件算shown。既有shown全保留，TSV60ce18d14e68b449915fc029ee7a036e0c2ed01e1c32f74539b249a55b7a95e0。重生腳本merge_census_97_delta.py及history-census-97-delta/由目標185索引。

初次xvfb-run因缺xauth未啟動工作，改回既有Xvfb有界trap後同映像重跑。教學墨跡測試起初誤將中文字頂4px當作所有字元內距；讀正式排版器確認拉丁上伸部2px後，按實際契約重跑PASS。單位普查原把重開事件重複登錄，改為唯一欄位加獨立來源事件後單列PASS。普查首輪缺已驗百科不可達佐證，補回原流程必要的類別入口列後同命令乾淨重跑。以上為驗證腳本問題，沒有為通過而改產品行為。

Goal保留完成#55／56／57／61的完整範圍，仍active。#55精簡ORDERS與完整來源審查、#56路線2／其他目的地列及真正超出視窗捲動未完成；不由本輪修復縮小範圍。未commit、push或發行，收尾遠端與Docker核對另追加。

本輪最後核對：教學6、單位標籤與目前來源百科審查均PASS；完整#61採用普查後的最終矩陣列PASS，所有61個可重驗列的檢查器指紋與目前來源一致。WORKLIST由產生器重生，verify及Git差異檢查通過，沒有原版EXE／SAV／WAV／封存檔誤追蹤；find工作根未見root-owned檔或.md目錄，抽查檔案均1000:1000。固定驗證映像無執行中或停止容器殘留，未清理其他專案資源。

關閉#61的主機gh請求被自動核准審查拒絕，理由為完成目標未構成精確的遠端關閉授權。拒絕發生於程序建立前，未執行遠端寫入；其後唯讀核對仍OPEN、closedAt為null。已提出明確授權問題，未改用其他方式繞過。#61本機功能驗收完成、遠端待授權；#55／56仍未完成，Goal active。

## 2026-10-09 接續：精簡ORDERS正式收尾與98列增量

前輪為進展，教學6與單位標籤已完成驗收、97批普查已採用。Goal仍是完成#55／56／57／61，沒有縮小。路由命中規格閘門並載入；Git身分正確。開頭只讀Docker檢查的自動核准審查逾時，工具允許重試一次，重試成功；沒有因此重啟遊戲或當成產品缺陷。

只讀觀測先確認四個停用列走字串層，第一列逐字NUL；原本兩列門檻會丟棄Activate unit首列。首版c80538e4…的166Go及原版狀態通過，但六列仍line-colors，未採用。第二版cc0ec453…按已驗六列與黑框指定68／149／8，167Go／go vet、原始八圖四側、17VIEW與新15GUI四側PASS。DRAFT與READY均在實作前記錄，再由正式組裝腳本接入。

正式新15GUI四側六張選單安全區改變、其他九張不變；21px、原灰色8、懸停、停用點擊關框、兩次取消、重開及啟用均逐圖確認，完整原版、WAV、存檔與缺字模回退全等。當前教學6的13圖、建造31圖及來源接線審查保留，全Goal未完成。公開check_goal185_compact_orders.py，最終900da1e18dbfd3eaba99b318b8f8a0a835b29b2b91be93e40d7a3b8069bfe595，規格035限定CONFORMED。

首次14張新GUI腳本誤以為點灰列會保持選單，後續Escape進退出確認；只留診斷。依原版畫面修正後15圖逐步檢查框線。量測工具比正式addDraft多載入LABELS，導致Fortify假歧義，改用正式檔案集合後PASS。普查首輪把模板鍵當來源完整鍵，改成清冊@ORDERS鍵後同命令乾淨重跑；沒有改產品或放寬證據規則配合測試。Fortify同文來源不新增信用。缺原版SKIP77及錯MENU版本拒絕通過。

第98列及四個受影響列實際PASS，沿97批保留57個可重驗列與36歷史列。98列普查1972項／928shown／952pending／92unreachable，其中315可重驗、613歷史；五個MENU來源由歷史轉可重驗，狀態變化0，舊shown全保留。TSV21619069b037386b4942ec30ebe9fee0bb652fe0748cab73425cfa85c2eb8a09。merge_census_98_delta.py及history-census-98-delta由目標185索引。採用普查後再次檢查#61為PASS，最終矩陣列c3e41c54212beb883202c96e0981906c4bc5c6e48ef24a9f674c16e78c87d9c6。未稱全部98列重跑。

#55共用名稱與完整來源接線仍需審查，清冊範圍564項、413 pending須分成缺接線與未抽樣，不能當缺譯數。#56貿易路線2／其他目的地與真正超出視窗捲動仍未完成。#57遠端CLOSED；#61功能完成、遠端OPEN，先前關閉遭自動核准拒絕，明確授權問題仍待回覆。本輪只有遠端讀取，未繞過拒絕；未commit、push或發行。收尾衛生另追加。

本批收尾：WORKLIST由JSON產生器重生且verify通過；公開檢查器語法、索引正對照、Git差異、原版素材誤追蹤與擁有權檢查通過。工作根find未見root-owned檔或.md目錄，抽查均1000:1000；固定驗證映像無執行中或停止殘留容器，未清理其他專案。HEAD仍a2cb6aa，未commit／push。下一個最小步驟是以正式addDraft檔案集合核對MENU的Join Colony／Pillage兩個完整來源模板，再逐類核對#55共用名稱的來源與回呼，不重錄已驗精簡選單。遠端唯讀確認#55／56／61 OPEN、#57 CLOSED；#61明確關閉授權仍待回覆，Goal active。

## 2026-10-10 接續：來源接線審查、四處城市槽位與路線2取證

前輪為進展，精簡ORDERS已正式完成。Goal仍完整保留#55／56／57／61，active。按路由讀規格閘門，沿既有Docker與正式8e來源取證，沒有將413 pending當缺譯。初次JavaScript呼叫語法錯誤未啟動工作，修正後正常核對工作樹與容器。

558項TXT初查與五則單行／專屬欄位分流已完成；Join Colony／Pillage模板實際匹配。來源已載入仍不代表變數能匹配，查出BUILT／FULL／FOREST2／TOONEAR城市槽位缺口。前三則原文明示城市；TOONEAR以IDA直接讀取端、指標寫入端及正常記憶體202-byte名稱記錄補強，沒有追整個建城或距離算法。locked-v1不存在，沿已驗py312-v1／UID1000，不另建映像；原始DB與EXE唯讀複製到容器tmp。

四槽位DRAFT／私用169Go與go vet、16來源名稱契約、正常13＋31圖回歸後升限定資料READY。接正式來源，補純契約隔離測試，正式8e22e074…／168Go／go vet及當前來源21教學／17版畫／開局27／百科164＋19審查PASS。教學13／建造31／精簡選單15圖與原版全等；四則尚無各自正常GUI，不增shown。公開四槽位檢查器60192165…，原四個畫面仍未驗，不以資料契約代替全#55。

初始變數探針多餘encoding/json匯入已修正；混合正文與單行集合造成FOREST2假歧義，按正式正文優先後確認真缺口。Land組句探針誤用未觀測Arawak別名，改用既有正常Apache主名後PASS，不放寬正式角色。同文Moderate0x7FD與其他Land語序仍oracle未知，不隨意判缺譯／不可達。上述為審查工具問題。

第99列與六個受影響列實際PASS，沿98批保留56可重驗列及36歷史。99列普查1972／928shown／952pending／92unreachable、315可重驗／613歷史，狀態變化0；TSVd60d7930a26c542c0568b5c369230c9d4be1772faa83bcd8cd32f91364b05f9a。採用後完整#61最終列再次PASS並回填生成矩陣。未稱99列全部重跑，也未將新四槽位算正常命中。

#56第一次有界互動700秒到期缺gui.json／inputs／memory，docker確認終止後只留診斷。改play_trade_route2_probe.py有限正常流程，兩條路線與第三／四目的地完成22GUI並正常關窗；中文／原文／缺字與觀測全等，原文標題2而中文舊1、第三London／第四Jamestown英文與選取／刪除列缺口confirmed，DRAFT038已補。不在正式程式猜補，下一步按當次編號、格線內框及角色建原型。來源查詢原先重複讀EXE已改單次讀取，不重跑遊戲。

工作樹修改保留，HEADa2cb6aa；未commit、push、Release或Issue寫入。#57維持完成；#55完整來源／消費端、#56貿易修復及真正超出視窗捲動未完成。#61功能驗收完成、遠端OPEN，明確關閉授權仍待回覆；沒有重試被拒絕遠端動作。收尾衛生另記。

本批最後核對：WORKLIST產生器與verify、公開檢查器語法、索引正對照、Git差異及原版素材誤追蹤檢查通過。工作根find未見root-owned檔或.md目錄，抽查來源／清單均1000:1000；共享dosgolem副本clean，upstream推送DISABLED，HEAD仍a2cb6aa。所有已開句柄已核對terminal，互動到期缺收據未採用；有限22GUI及三側／觀測已完整結束。下一最小步驟是按DRAFT038的實測標題[128,5,193,10]及第三／四列字格建立私用路線範圍原型，另量測目的地選取列實際內框；不重錄已驗名稱資料契約。#55／56／61遠端OPEN、#57 CLOSED，#61明確關閉授權仍待回覆，Goal active。Docker清理由本批最末控制命令核對。

## 2026-10-10 接手：貿易路線2欄位修復與100列增量

按復古遊戲規格閘門及文件職責路由接續上輪22圖證據，使用reverse-engineer-retro-game-remake技能。研究映像已不存在，確認既有hr-go-ebiten:1.26.7-2.9.9-r1及verification runtime-r2後沿用，未重建重複映像。Git身分wicanr2@gmail.com、HEADa2cb6aa；保留原有未提交修改。

候選先依實測字格與角色修復路線2標題、第三London／第四Jamestown、目的地單列及刪除選項。框頂81與真實83、正文沒有逐列items的差異均在私用候選訂正，失敗收據保留，未放寬正式守門。READY後正式0484e99b…通過169Go／go vet無skip；新34GUI四側完整原版與存檔相同，16圖只改安全區，其他18圖不變，含懸停、取消、刪除、重加及GAME手動存檔。規格035／038限定CONFORMED。

教學13、建造31及精簡選單15圖回歸最初用了結束後存檔，原版狀態不同，屬驗證輸入問題。回查原GUI初始存檔集合及年份，改用原正常前置保存後乾淨重跑，畫面、原版與存檔全等；錯誤批次保留，未變更產品來配合錯輸入。重播器補啟動前檔名集合檢查，trade-fields-replay-seeds.json記錄正確來源雜湊。既有全檔來源比較依READY差異縮到未變函式與當前完整來源核對，並保留實際正常回歸。六個負例拒絕、缺原版SKIP77。

第100列與七個受影響列PASS；保留56可重驗列及36歷史列，未聲稱全部100列重跑。普查1975／931shown／952pending／92unreachable，318可重驗、613歷史；本批只新增三個正常執行期鍵，346組城市名容量不算命中。TSV aebb720fa5743006c7673258103ad662e384e966b0b5fbd01523415294bc7318。來源、私用入口與收據由目標185索引，原版素材未新增到公開檔案。

#55完整來源及消費端審查、四城市訊息正常GUI與#56真正超出視窗捲動／其他貿易情境仍未完成。#57維持遠端CLOSED；#61功能驗收完成但遠端OPEN，不重試先前被自動核准拒絕的關閉。無commit、push、Issue寫入、封包或Release。

採用普查後八列再次PASS，矩陣審查指紋已更新。工作清單生成及verify、公開檢查器語法、普查欄位數與索引正對照通過；Markdown／程式Git差異檢查通過，TSV空末欄的分隔符另按格式驗證。沒有誤追蹤原版素材，工作根未見root-owned檔或.md目錄，抽查來源與文件均1000:1000。隔離dosgolem工作樹clean、upstream推送DISABLED；本工作沒有殘留執行中或停止容器，其他專案容器未動。

## 2026-10-10完成#56並準備提交

接續既有目標185修改，沿2026-10-04「完整接線後代表性正常路徑抽樣」決定收尾。288實際TXT來源與三個歷史整段清單鍵分開；250字串查譯、37模板載入、1陸上貿易標籤專屬消費端通過，19變數及19常數模板經真實來源及實際消費端審查。新增ABANDON2、ALREADYHAVE、NOMOREWAREHOUSE、NOMOREWAGONS的城市名稱回呼，限定精確來源與%STRING0；缺回呼／控制碼保留原文。

正式73d863baa358dce354bf2d13b232735c2e9109a48d1b1c15a61d88df031e4ee2，180Go及go vet無skip。以Go1.26.7／Ebitengine2.9.9／dosgolem82a14b2與`go build -trimpath`重建；曾以登入shell導致PATH找不到Go，改用同一映像非登入shell乾淨重跑。未帶trimpath的二進位指紋不同，依正式建置參數重建後與所有GUI收據一致。總檢查腳本曾引用舊建造基線與/out的父目錄，修正為前一已驗版及/repo/workplace/reports，屬驗證腳本問題，沒有因此改產品行為。

新34正常GUI自主選單讀檔，建兩條路線、第三London／第四Jamestown、懸停、取消、刪除／重加及GAME手動存檔。四側終點370000000步、RAM 4cc3452f654d78280d574d83475b4a63cdb00fcc569322828f780cd8040ed4a6一致，WAV、存檔及每點原版畫面一致，中文畫面與前一已驗版全等；輸入ca60373081b955374b902abde61060ca64a4e62eee18c0c98dc3950ec401ff82。93圖當前來源回歸全等，BUY、武裝、多人口、議會、港口及報表10列既有檢查PASS，沒有聲稱重錄其GUI。

完成審查bd42464d1208d4144dc5efd4c6daf5e795a392efd1d751d3bda01b03c6b9e3cc，負例缺原版SKIP77、錯來源／審查資料／原版RAM皆拒絕。矩陣101列，本批9列PASS，另外56可重驗與36歷史列沿用；普查1975／931 shown／952 pending／92 unreachable，318可重驗／613歷史，本批不提高shown。增量入口見目標185，原100批收據與535ee711…貿易摘要保留。

正常人口成長探勘前兩次停在View Pieces／城市；第三次正常到1506年與3人口，未達換頁門檻。舊dialog_text只是最後印字，不代表當前彈窗；停止無益的重複操作，不當產品缺陷或正式驗收。互動容器已停止刪除，其步數上限退出保留診斷。四條件城市訊息與建造換頁仍未各自正常GUI，五類154 shown／137 pending不變；未修改原版SAV或RAM。

遠端#56已依本次明確授權留言並關閉，收尾留言https://github.com/wicanr2/colonization_cht/issues/56#issuecomment-6098434714。本次依使用者授權commit與push；既有目標185修復及驗收一併保存。沒有打包、Release或重試關閉#61。原版衍生收據只留已忽略的workplace，公開僅程式、譯文與證據索引。Docker工作均--rm、UID/GID1000及有界資源；互動容器已刪除，提交前再核對執行中／停止容器、root-owned與誤追蹤原版素材。

提交前驗證：採用後開局收尾列PASS，65個可重驗列的檢查器與收據指紋一致。WORKLIST產生稿與JSON全等，worklist verify、修改的TSV欄數及Python語法檢查通過。補丁的上下文空格按原格式保留，git apply --reverse --check通過；其餘程式與文件diff --check通過。沒有追蹤或暫存原版封存檔、EXE、SAV、RAM、WAV、IDA資料庫或新截圖。全工作根find未見root-owned或誤建的.md目錄；本專案及驗證映像沒有殘留容器，隔離dosgolem工作樹乾淨且upstream推送位址仍為DISABLED。#56遠端CLOSED，closedAt為2026-10-10T14:19:26Z。

## 2026-10-10追加正常抽驗

使用者在#56提交推送後，要求繼續抽驗，完成這輪後commit、push，重新製作推廣影片與三平台完整版加Release。沿既有授權與規格044，完整版自帶原版資料只留本機，公開Release提供完整功能包與MP4。

從原版正常產生的1506春季、人口三人存檔啟動，經主選單讀檔、城市、食物教學、15項建造選單、選貨車、1040$／國庫1000$提示、返回及手動存檔成功。15圖四側CPU、1MiB RAM、索引、色盤、WAV及兩份存檔相同；中文GUI與重播逐像素相同，缺譯回退與原文相同。完整終點173200000步，RAM ab8e2c828bbcb6c4e767475b21cd7f79cc1d28ca4adf7da568cdbff2447a9090；輸入9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979。入口見目標185與check_goal185_wagon_sample.py，沒有修改原版RAM或存檔。

普查只採食物教學與存檔成功。BUY同文模板原始來源不得混用；輔助觀測到@BUYME0，但完整RAM不同，不宣稱同狀態，也不提高BUY來源信用。最初增量歸屬已拒絕並保留，重新從101批合併。現況1975／932 shown／951 pending／92 unreachable，319可重驗／613歷史；矩陣102列，本輪新增1列及採用後開局指紋列PASS，其餘64個可重驗列核對指紋沿用、36列僅歷史。未觸發的四城市條件與建造換頁仍保留待驗。

抽驗容器已清除。新建v.1.0.3-20261010三平台封包兩次重建全等，正式Linux／Wine正常GUI與同輸入原版狀態、音訊、中文選單通過。六個新版畫面及90秒影片已通過技術與八幀目視檢查，三平台本機完整版正在驗證，發行工作尚未結束。

## 2026-10-10三平台重新交付與影片

追加抽驗已以e66770d提交並推送。沿版本與dist-all契約，從唯讀乾淨來源重建v.1.0.3-20261010的Linux、Windows及macOS雙架構。公開組裝器工作區改為已鎖定的Go1.26.7；再次組裝13檔與正式建置輸入全等，前端Go程式未改，沿用180Go與go vet驗收。

舊封裝映像與部分早期字模中間物已不存在。直接使用現存固定映像，不另建功能重複映像；恢復同一AppImage runtime，封裝器改為固定1.9.0白名單，解決SOURCE_DATE_EPOCH與mksquashfs時間參數衝突。字模沿已驗v.1.0.2包的67個授權檔，逐項核對manifest與13份現行譯文及兩圖集綁定，新包字模逐位元組相同。錯manifest、譯文變動、字模缺失／變動／多檔與未知封裝器六負例皆拒絕。規格041／044經READY至實作與驗收，現行附錄CONFORMED。

三平台公開包各兩次封裝全等，全部清冊、SHA-256、平台、內嵌版號、授權與原版排除通過。Linux／Wine正式包正常鍵鼠到主選單，同一實際輸入下完整CPU／RAM、索引、色盤及WAV相同，五列與版本安全區逐像素相同。私用三平台完整版保留原版檔案時間、排除存檔；Linux／Windows一鍵入口正常重播與公開包原版狀態相同，macOS只驗雙架構、簽章、清冊及shell，未聲稱真機或Gatekeeper。

推廣片六個畫面全數用新版正式包重生，三段正常輸入重播的完整原版終點與原GUI一致。沿已驗原版連續音樂收據，音源與畫面dosgolem版本分別記錄。90秒、1080p30、H.264／AAC、非靜音、峰值−2.5dB、無非預期黑幀，八幀及字幕／完整遊戲畫布已目視。MP4為79014291…，固定畫面剪輯已明示，未冒稱連續動態遊玩或新增人耳驗收。

正式根dist-all/v.1.0.3-20261010；三個公開功能包、MP4、三個私用完整版的完整雜湊與重生入口見目標185。交付總檢查cbe26579b1bb32a7b741102010bd841d0c0b78d8ba878d9070a8af716e9fec68為PASS_FINAL_DELIVERY_WITH_MACOS_RUNTIME_LIMITATION。原版資料完整版只留本機；本次Release準備上傳三公開包、MP4及SHA256SUMS.json，舊版tag與Release保留。

發行提交前總檢查PASS：工作清單verify及生成稿全等、TSV十欄、修改Python語法與shell語法、已知入口正對照通過；普查dee3d359…與增量收據一致。Git未追蹤原版封存檔、EXE、存檔、RAM、WAV、TTF或IDA資料庫，未新增原始截圖。全工作樹find沒有root-owned檔或.md目錄；本輪容器均已自動刪除，隔離dosgolem乾淨且upstream推送DISABLED。Markdown／程式diff檢查通過，TSV保留空末欄分隔符並另驗欄數。

發行提交71db6fe5def8c39d0433eb5fe4977835da7beb54與固定tag v.1.0.3-20261010已推送。Release先建草稿並上傳三平台公開功能包、MP4及SHA256SUMS.json，五附件名稱、大小與GitHub伺服器計算的SHA-256逐項和本機相同。按tag讀草稿的API回404，改從已授權帳號的Release清單取得草稿；沒有另建版本。額外附件回下載頻寬過低，停止後清除四個未完成副本，只完整驗了SHA清單副本；未將伺服器雜湊驗證冒稱全部回下載驗收。

Release於2026-10-10T15:17:41Z公開，網址https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.3-20261010。公開後再次核對五附件SHA-256、固定tag及Asia/Taipei版號日期通過。舊v.1.0.2、v.1.0.1、v.1.0.0與預覽版的識別、正文與附件指紋不變。公開後摘要保存於目標185 release/及正式根smoke/；三平台自帶原版資料的完整版仍只留full-local/。最後交接文件另作提交推送，不移動已發布tag。

## 2026-10-10：五語與 HD 規劃、README 歷史背景

使用者要求非英文模式的英數使用該語言字型，另增簡中、日文、韓文與英文切換；英文用原版字體。HD已選重繪地形、人物與建築，先製作風格樣張。切換方式須避開原版操作，推廣片須包含實際遊玩。原發布、#56完成與未抽樣範圍保留。

依知識路由載入README、文件職責、工作清單與推廣片入口，使用grill-me／grilling確認HD範圍，並以imagegen產生精細像素、手繪插畫兩張1536×1024候選。候選只存本機，畫風尚待選定，未接正式程式；事件版畫不擅自納入。已建立#62五語與英數字型、#63 HD、#64動態遊玩影片，清單由JSON重生。

README補遊戲背景、十五世紀末殖民題材起源、十七至十八世紀北美移民、契約僕役及被奴役人口的不同處境。來源為官方遊戲頁、美國國會圖書館與國家公園署，各段附直接連結。修正字型文件中已失效的第二個本機路徑。

目標186整理畫面外工具列、暫停及輸入隔離、語言包整包切換、英文字體回原版與HD圖層草案。已做可操作HTML原型，繁中／英文用同狀態城市截圖，其餘語言明示未提供譯稿。原型含原版像素，只輸出workplace；公開只保存原型程式與組裝器。Cubic11韓文字形抽查缺字，正式日韓字型、設定操作、資料格式與分層架構仍未定案。

本輪驗證：64筆worklist載入與verify通過，生成稿與JSON一致，README已知入口正對照及新目標連結、文件相對連結通過。Python語法、Node22 JavaScript語法、原型內嵌圖片SHA-256、拒絕覆寫及拒絕workplace以外輸出均通過。沒有瀏覽器執行期或正式前端切換驗收；正式遊戲Go來源未改，不將原型檢查稱為產品功能完成。

另沿現行正式版8e6cba67…與正常COLONY09，錄製51.933秒真實X11操作，包含殖民地、建造清單、貨車購買提示及返回世界。40筆正常輸入、104影格抽樣／93次變化、H.264 1280×800 30fps及原版WAV非靜音通過；三張操作截圖已目視到達預期畫面。WAV10.932秒與牆鐘影片不同步，影片仍無音軌，不能冒稱正式90秒成片。首次驗證腳本在正常關窗後解析提示文字失敗，改取最後JSON行並沿同映像／流程乾淨重跑成功，原失敗輸出保留。錄影與收據由目標186索引，#64維持進行中。

收尾驗證通過：最後工作清單64筆、生成稿與文件入口一致，原型證據摘要1e65242a…；本機候選與輸出均1000:1000。全工作樹沒有root-owned檔或.md目錄，未追蹤workplace、dist-all或原版封存檔／EXE／SAV／字型／WAV。所有本輪Docker已自動刪除，隔離dosgolem乾淨且upstream推送DISABLED。依使用者要求提交推送README、規劃、工作清單與原型程式；新語言、HD正式功能及新Release仍未完成，畫風問題保留待答。

## 2026-10-11：精細像素畫風定稿與草稿入庫

使用者明確定稿第一張精細像素風，要求將決定寫入AGENTS.md，草稿加入儲存庫。
已於AGENTS.md新增HD重繪定稿入口，適用地形、人物與建築；正式位置與互動範圍仍依原版證據。
原圖原樣保存至docs/screenshots/hd-pixel-concept.png，1536×1024、3174715位元組，
SHA-256為d9d89edec99584f4032f16a48000aef46d0248b06f85b31418c0f3a81a3ea2bf。
同名JSON保存完整生成提示、參考圖雜湊、生成與定稿日期及本次入庫授權範圍，
由AGENTS.md與目標186共同索引。原版參考截圖及未選用手繪候選未加入Git。

CONTEXT、目標186與HD工作項同步移除畫風待選的現況敘述，WORKLIST由JSON重生。
#63仍為in_progress，本輪沒有將樣張當作遊戲內HD實作完成，也未更動正式前端或既有Release。
依本對話既有授權，這輪紀錄與草稿一併commit、push。

驗證通過：原圖與入庫副本逐位元組相同，PNG可解碼，來源圖與提示紀錄雜湊一致；
64筆工作清單verify及生成稿一致，文件相對連結、已知入口正對照與新圖片紀錄入口皆通過。
所有修改檔與新檔擁有權1000:1000，全工作樹未見root-owned檔或.md目錄。
本輪Docker容器均已自動刪除，專案無殘留容器；隔離dosgolem乾淨、upstream推送位址DISABLED。

## 2026-10-11：設定入口定案、暫停核心與HD來源盤點

使用者確認畫面外設定列、遊玩中切換、開啟暫停與關閉放開後恢復。決定寫入
AGENTS.md，規格050限定READY，授權前端狀態與輸入／音訊隔離，不授權未驗證的
新語言包或HD合成。已實作設定草稿、失敗保留、等待放開與兩條音訊暫停核心，
尚未接入真視窗設定列。174項Go與go vet通過，零skip；獨立音樂暫停讀取不推進
原版機器或命令佇列，恢復與無暫停音訊及完整記憶體相同。

初次全測只有既有建造標題測試找不到硬編碼的收據路徑。新增環境變數唯讀入口、
固定64000bytes與SHA-256守門，缺原版且未指定入口時明確skip；沿同容器映像乾淨
重跑通過。初次失敗JSON保留，不記成產品缺陷。Go探針的格式化掛載與函式型別也
在研究工具中修正，沒有藉此更動dosgolem或原版。

研究盤點實際206個SS與1517幀，1498非空幀。四份焦點檔的345張本機候選圖對照
原版殖民地，取得42素材／71完整位置；世界畫面16素材／139位置。由正常GUI輸入
重播，觀測原版0D46:01D2的BUILDING.SS第032幀完整534bytes來源，與解壓part3的
22616位移唯一匹配。有無觀測CPU、完整RAM、VGA及DAC相同；歷史GUI控制的VGA／
DAC相同，但完整RAM不同、原因未知，不宣稱跨舊前端全面同狀態。

公開研究工具與check_goal186_research.py驗證9項守門，涵蓋一點遮擋、缺圖、損毀、
錯解碼器、截斷畫面、拒絕覆寫與拒絕workplace外輸出。所有原版像素及原始記憶體
觀測維持本機。外部固定mpskit為唯讀研究依賴，AGPL來源沒有複製到正式程式。
已按定稿畫風生成首座建築候選，完整提示及來源雜湊保存本機；輪廓、透明邊界與
零星色點未通過，不算正式HD素材。

官方Noto Sans CJK Sans2.004 Regular OTC與OFL固定commit及雜湊下載完成，四個
區域字型的樣張文字與英數抽查通過。Cubic11韓文缺字已明示。真字型樣張已展示，
使用者的字型選擇待答；新增可重生樣張的公開腳本。下載批次曾卡在未使用的Serif
候選，已停止本輪容器，保留完成的Sans檔，不把整批或Serif稱為下載成功。
五語包、HD正式圖層、GUI與新三平台發行仍未完成，既有Release不變。

本批檢查通過：64筆工作清單與生成稿、Python語法、文件相對連結及新增入口一致；
全工作樹沒有root-owned檔或.md目錄。容器均已自動刪除，隔離dosgolem乾淨、upstream
推送DISABLED。原版素材、字型候選與研究輸出只留workplace；公開提交只有程式、
規格及進度文件。依既有授權保存提交並推送，五語與HD目標維持進行中。

## 2026-10-11：設定列真GUI與三側重播

沿使用者已確認的畫面外設定列，建立規格051隔離執行原型。正式Go來源保持原樣，
組裝器先核對來源指紋，只改workplace副本。新增17key五語設定介面TSV、Noto真字型
排版與工具列座標測試，以及正常鍵鼠GUI和原版狀態重播檢查器，均由目標186索引。

177項Go、零skip及go vet通過。四組真GUI涵蓋開啟按住與移動、Escape取消、語言／
HD缺包失敗保留、繁中與英文切換，以及切換後正常進城與滑鼠取消。18筆設定事件
在各自暫停期間的完整原版狀態與DOS輸入不變；英文遊戲區逐像素等於原版輸出。
實際21筆DOS輸入由原型、正式前端及原文控制重播到73400000步，CPU、完整RAM、
時鐘、VGA、DAC及存檔全同；繁中終點PNG與GUI全同，三種重播WAV全同。

最初組裝的字串條件替換點不唯一，改以既有規格038渲染註解定位，保留英文模式的
原版來源觀測。首次GUI測試直接銷毀X11視窗造成BadWindow，改用既有正常關窗事件
後同映像、新目錄重跑通過。原失敗收據保留，未將工具錯誤寫成遊戲缺陷。

沿imagegen清理首座建築候選的外圍色點，原樣保存在本機building-032-candidate-v2.png，
完整提示與來源保存同名JSON。新增只讀輪廓檢查器，原版7040不透明點中6285點有
候選覆蓋、755點未覆蓋、309點外溢，暫不接正式替換。沒有重編碼或修改原版圖片。
所有新增圖、字型及原始收據只留workplace，公開提交僅程式、規格、TSV及進度文件。

規格051保持DRAFT；正式設定保存、失焦／拖曳GUI、遊戲字型選擇、完整五語包、
非英文保留英數的全欄覆蓋、HD正式圖層與新影片／三平台交付仍未完成。
既有v.1.0.3-20261010 Release與完成普查不變，五語與HD目標保持進行中。

本批收尾檢查PASS：來源及組裝檔逐項SHA-256相同，64筆工作清單與生成稿一致，
515個文件相對連結及已知入口正對照通過，四個Python工具語法與六項輪廓失敗守門
通過。全工作根無root-owned檔或誤建的.md目錄；本輪容器已自動刪除，隔離dosgolem
工作樹乾淨且upstream推送DISABLED。原版素材與新候選未追蹤，diff檢查通過。
依既有授權保存本輪提交並推送；完整五語與HD工作尚未完成。

## 2026-10-11正式接入保留英數字型

沿使用者非英文英數高清字型要求，先保留現有Cubic11，未代替待答的新遊戲字型。原候選的1縮小與離城殘影經真實字格及畫面審查找出；記錄當次ES:DI與結尾游標，改以已證實字格選字級，新英數須完整VGA區域吻合才繪製。規格052依DRAFT、證據審查、READY、正式實作及新GUI至限定CONFORMED，新增--retained-ascii-a，不改發布包。

正式178Go、設定原型181Go、零skip及go vet通過。候選15圖安全區差異19814點，三個反例拒絕；正式新正常GUI經讀檔、城市、建造、貨車資金不足提示與存檔，六張真實抓圖與60筆實際DOS輸入重播逐像素相同。三側CPU、RAM、時鐘、索引、DAC、WAV與存檔相同，7495點顯示差異均在當次英數安全區。英文控制同開旗標仍逐像素保持原版字體。收據、雜湊與重驗入口見規格052。

未增加普查shown，未修改原版、dosgolem或已發布Release。完整五語、多色與輸入欄、地形／人物／建築HD、新推廣影片與三平台新版仍待完成。依既有授權提交並推送本輪正式英數範圍；Docker均--rm、UID/GID1000、有界資源與trap，提交前核對工作樹、來源、文件及容器清理。

提交前核對：正式來源及組裝清冊全同，Python語法、工作清單verify與產生稿全等，已知規格051索引正對照及全部新入口通過；舊測試檔引用已清除。全工作樹find未見root-owned檔或.md目錄，沒有本輪殘留容器。隔離dosgolem乾淨且upstream推送DISABLED；原版封存檔、EXE、SAV、RAM、WAV及字型未加入版控。

## 2026-10-11：多語系文本資料與來源隔離

以現行13個實際消費端為準，建立2006筆來源鍵、完整列指紋及嚴格UTF-8 TSV契約。
新增簡體、日文與韓文遊戲譯稿，不在程式或JSON內複製譯文。簡體由固定OpenCC1.1.9
起稿，39列炮／铺異體字及抵制用語另作修正；逐句人工校對仍未完成。日韓逐項寫出
術語、選單、教學、國家介紹、預設城名、狀態欄及全部模板，各1553筆，尚缺各453筆
對話／百科正文，不使用繁中補齊。正式切換、字型及逐欄排版仍待完成。

規格053由來源盤點、READY至限定CONFORMED於文本檢查與組裝。8項測試及12次真實
文本命令通過；兩次簡體組裝全等，17963個非顯示欄位值及13表來源不變，繁中輸出與
原檔逐位元組相同。英文只出原版顯示清冊，不完整日韓及錯誤OpenCC wheel均拒絕。
本輪沒有執行原版，不增加GUI、原版對拍或普查shown信用，不修改已發布Release。

驗證器攔下韓文範圍誤用~及模板全形空白誤寫。後者先誤讀Python repr，逐字核對
UTF-8 E3 80 80後修正規格與譯稿，新增真實模板反例，不放寬檢查。舊表的特殊引號
只允許在整檔指紋固定的基準讀取，新譯稿仍嚴格檢查。一次容器stdin未轉送屬命令
環境問題，加上-i後同映像重跑，沒有把空輸出視為成功產物。

來源與收據見目標186、規格053及language-text-check-20261011/check.json，摘要SHA-256
為3c21468c374aa233d401d5314fe1483bee9ac2f44a6779b2af6736882a7ae587。工作清單仍進行中。
依既有授權保存並推送這批譯稿；完整五語、HD、新影片與三平台發行仍待完成。

收尾核對PASS：工具與三語譯稿指紋相符，3個Python語法及542個文件相對連結通過，
以既有規格051入口作正對照，8個新檔均有索引；64筆工作清單與生成稿一致。
全工作樹無root-owned檔或.md目錄，沒有本輪殘留容器。隔離dosgolem乾淨且upstream
推送DISABLED；原版EXE、存檔、音訊、封存檔、字型及轉換依賴均未加入版控。

## 2026-10-11：接續日韓對話語料

日文與韓文各補300筆corpus起稿：GAME298、MAPEDIT1、PEDIA1。
各語共1853／2006筆，其中1850筆譯文及3筆明示省略；corpus865／865，
pedia11／164，百科各缺153筆。新增稿以原版英文及繁中對照撰寫，未經母語校閱。
來源鍵、基準列指紋、13表與各語原有1553筆完整位元組不變。

既有8項語料測試及兩語partial檢查通過；正式組裝均因缺153筆拒絕，未產生目錄。
匯入前修正4筆換行與強調標記錯位，維持原驗證條件。最後文字校核保留韓文
LOSING3「超過90%%」及BUY0／BUY1原文of比較寫法，不額外指定金額用途。
初次追加、文字校核及正式CLI收據分別保存，不覆寫先前收據；完整雜湊見規格053文末。

本輪路由載入localization-display-semantic-isolation與project-document-responsibilities。
舊研究映像不存在，先核對並沿用現有colonization-verification:20261007-runtime-r2，
Python3.13.15；沒有重建工具鏈。主機gh auth status通過，遠端#62只讀核對OPEN，未寫入。
沒有執行原版、修改前端或Release，也不增加普查shown或GUI驗收信用。
下一步補日韓各153筆百科正文；字型選擇、逐欄排版、五語切換、HD及新影片仍待完成。

Docker使用--rm、UID/GID1000、無網路與資源上限。收尾再核對工作樹、文件入口、
來源指紋、擁有權及容器清理，結果追加於本節。

收尾核對PASS：64筆工作清單與生成稿全等，248個文件相對連結及規格051入口正對照
通過，git diff --check無誤。全工作根無root-owned檔或誤建.md目錄；本輪容器均已刪除。
隔離dosgolem工作樹乾淨，upstream推送仍為DISABLED。變更僅含兩份日韓TSV及五份既有
狀態／規格文件，沒有新增原版素材、字型或封包；本輪未提交、推送或寫入遠端Issue。

## 2026-10-11：接續日韓百科與全文組裝

沿已展示的下一步，日文與韓文各補153筆百科正文。各語共2006／2006筆，
其中2003筆譯文及3筆既有空白冠詞省略；corpus865／865、pedia164／164。
新增稿涵蓋建築、貨物、建國元勳、職業、地形及單位，未經母語校閱。
日文殖民地名稱沿既有術語表統一為「植民地」。匯入前修正韓文人數範圍的
控制符號誤用，保留原槽位及排版檢查，不放寬驗證器。

8項既有測試、兩語全文檢查及各兩次13表文本組裝全部通過。
各語重複輸出與清冊逐位元組相同；各17963個非顯示欄位值與基準全同，
原有1853筆位元組及13份基準表不變。完整來源、工具、譯稿及輸出雜湊保存於
language-pedia-check-20261011/check.json，SHA-256為
fc3aad3fbdffc3b9fd26fd0e9b48a89056363ca951bd83a31266876fe06ab236，入口見規格053文末。
文本相容檔只留workplace，不當作正式語言包。

路由複核仍為localization-display-semantic-isolation及project-document-responsibilities。
沿用colonization-verification:20261007-runtime-r2與Python3.13.15，未改工具鏈。
沒有執行原版、修改正式前端或Release，不增加普查shown或GUI驗收信用。
完整文本起稿已完成；母語校閱、字型選擇、逐欄排版、正式五語切換、HD及新影片仍待完成。

Docker使用--rm、UID/GID1000、無網路與資源上限。收尾核對工作樹、文件入口、
來源指紋、擁有權及容器清理，結果追加於本節。本輪不提交、推送或寫入遠端Issue。

收尾核對PASS：64筆工作清單verify及生成稿全等，390個文件相對連結與規格051入口
正對照通過；兩語現行TSV、組裝檔及收據指紋一致，git diff --check無誤。
修改檔擁有權1000:1000，全工作根無root-owned檔或誤建.md目錄；本輪容器均自動刪除。
隔離dosgolem乾淨、upstream推送DISABLED。變更仍僅兩份日韓TSV與五份既有文件，
沒有原版素材、存檔、音訊、封存檔或字型被追蹤；本輪未提交、推送或寫入遠端Issue。

## 2026-10-11：四語Noto定案、完整字集與首組欄位原型

使用者看過Cubic 11與Noto真實字型樣張後，明確選定四種非英文都用Noto Sans CJK
對應地區字型。繁中TC、簡中SC、日文JP、韓文KR的文字與保留英數共用同一字型，
英文維持原版字體。已更新AGENTS、CONTEXT、規格050、目標186與字型入口，
不改已發布版。Sans2.004固定commit、OTC face、字型及OFL指紋見font/README.md。

新增完整字集檢查器，從13份固定基準表、三語2006筆完整TSV及17筆設定介面盤點。
Noto四語遊戲字集1833／1809／1386／906碼點，均含95個可見ASCII，遊戲與介面缺字0。
Pillow逐碼點檢查均未命中各自缺字字模；Cubic所缺簡中8字、韓文798字則命中缺字字模。
結果只證明當前字集覆蓋，區域字形品質、母語校閱及執行期變數新字元仍須另驗。

新增六列命令欄排版原型，直接讀既有來源鍵與規格035正常路徑量測／審查收據。
原版cap5、最小行距8、安全區[80,12,159,77]，放大4倍為316×260。候選22至15px，
四語18px的最大墨跡高20px，24列實際墨跡未超界；每列保留基線與內距。
已查看四語比較圖。兩個Fortify同文來源仍未分辨，未渲染熱鍵／停用色，未作正式GUI驗收。
沒有修改正式圖集、前端、原版或dosgolem，不增加普查shown。

兩工具各乾淨重跑一次，JSON及PNG逐位元組相同；錯誤指紋、既有輸出、workplace外
輸出與缺父目錄等10項輸入均拒絕。完整來源、工具版本、指紋、收據及重驗命令見
規格053文末及font/README.md。完整五語切換、其他欄位READY規格、HD與新影片仍待完成。

本輪路由命中localization-display-semantic-isolation與project-document-responsibilities；
更新字型README另載入retro-remake-readme-standard。依grilling技能展示真字型原型並
取得使用者明確選擇後才記錄定案。沿用colonization-verification:20261007-runtime-r2，
Pillow9.4.0、FreeType2.12.1、Fontconfig2.14.1，未重建映像。

Docker使用--rm、UID/GID1000、無網路與資源上限。最後核對文件入口、工作清單、
來源、擁有權、工作樹與容器清理，結果追加於本節。本輪不提交、推送或寫入遠端Issue。

收尾核對PASS：64筆工作清單verify及生成稿全等，432個文件相對連結、規格051入口
正對照與兩個新工具索引通過；兩工具語法、現行譯稿、來源及全部收據指紋一致。
初跑改寫了術語政策的固定驗收句，造成舊完成訊號失配；保留原驗收句後，同映像
乾淨重跑通過，未改工作清單的驗證條件。修改檔及輸出皆1000:1000，全工作根無
root-owned檔或誤建.md目錄，沒有本輪殘留容器。隔離dosgolem乾淨、upstream推送
DISABLED；未追蹤原版素材、存檔、封存檔、音訊或字型。本輪未提交、推送或寫入遠端Issue。

## 2026-10-11：提交前批並接續四語六列字模

使用者明確授權commit及push後，先核對Git身分、來源與收據、64筆工作清單、432個
文件連結及工作樹。前批日韓全文、Noto定案與欄位量測以2c47112提交並推送origin/main，
推送成功後工作樹乾淨，作者為wicanr2@gmail.com。沒有更動tag、Release或遠端Issue。

接續目前六列命令欄。實測現有字模烘製器的整數字寬會裁去Noto18px的V／f／j／v／y
少量邊緣，每語合計7個非零Alpha像素。新增規格054 DRAFT及私用字模工具，沿既有
圖集格式擴展必要字格並保留負左伸出，每字完整Alpha與加邊界的參考渲染相同。
六列相對舊整數字格最多增寬1px，24列墨跡均未超界，不改全域字級或正式圖集。

四語各115／115／122／117字，均含95個可見ASCII；18px只適用目前六列。
從正式來源逐字抽取loadAtlasFonts、menuZh、lineLayerMasks等函式，在固定Go1.26.7
容器執行；四語一般、熱鍵及停用三層原始Alpha bytes與獨立Python參考全同。
20項Go錯字型／綁定／字級、缺字與超長列反例，7項CLI錯輸入拒絕均通過。
兩次乾淨重生34個檔案逐位元組相同。已查看三層比較圖，示意配色不作原版DAC證據。

現行收據位於language-field-atlas-20261011-r2，總收據language-field-atlas-20261011-verify.json
SHA-256為daa67d12995c92222695bea780aaacb6876c47b52d67e6cae86e027330e6c9b0，完整來源、
工具、逐字與逐列指紋及重驗命令見規格054。初版無比較圖，保留原產物；沒有覆寫舊收據。
規格051及組裝器的「字型尚待決定」限制已更新為已選定但未接入，僅修正限制文字。

路由仍命中翻譯顯示隔離與文件職責；字型README沿已載入的README契約。
沿用既有Python及Go映像，UID/GID1000、無網路、資源上限與外層逾時；未重建工具鏈。
一次image inspect因不存在的Entrypoint欄位失敗，讀取完整Config確認無entrypoint後沿用
同映像，不另建重複映像。正式前端與dosgolem均未修改，也沒有本輪原版執行、
正常GUI、同狀態或普查shown信用。後續需完成欄位READY審查及執行期語言包／正常GUI。

本批新增字模工具與規格尚未提交；字型、圖集、參考遮罩及Go探針只留workplace。
收尾再核對工作樹、索引、來源、擁有權與Docker清理，結果追加於本節。

收尾核對PASS：64筆工作清單verify與生成稿全等，418個文件相對連結、規格051入口
正對照及兩個新增入口通過。兩個Python檔語法、34個產物、全部收據與原Go來源指紋
相符；修改檔及產物皆1000:1000。全工作根無root-owned檔或誤建.md目錄，兩個工具
映像均無本輪殘留容器。隔離dosgolem乾淨、upstream推送DISABLED，原版、存檔、
音訊、封存檔及字型均未被追蹤。origin/main為2c47112；續作九個變更檔尚未提交。

## 2026-10-11：推送字模原型並正式接入四語六列

依使用者要求，先將前批九檔提交為52f2924並推送origin/main，作者為
wicanr2@gmail.com，推送後工作樹乾淨。隨後依明確的「正式接線」授權，核對顯示隔離、
文件職責及規格035／053／054，將規格054的六列契約升為READY後實作。

正式載入器只在原版六列文字、座標、完整黑框、68／149／8色層守門後使用Noto。
四語各18px，七列既有格式TSV含Fortify同文別名，原版命令識別仍用原文；
譯文只進放大畫布。新增三個noto-orders參數，預設沿用既有顯示，英文沿control原字體。
完整語言TSV先由烘製器核對，字模綁定基準、譯稿、來源、量測、字型、OFL及地區face；
缺檔、錯綁定、歧義不同譯、缺字及超界整欄回原文並記錄，不影響其他欄位。

第一輪新測試把停用層誤寫為數字2，與正式layerDim值1不同，造成三層遮罩差異；
修正測試夾具用既有常數後，同工具鏈乾淨重跑。初次完整回歸另有11個既有fixture缺失skip，
補上唯讀原版、字串圖集及建造標題收據後，240項Go測試零skip、go vet通過。
56個錯誤輸入反例、四語三層遮罩與獨立Python參考相同。兩次正式烘製21檔全等。

四語各15張正常GUI，依讀COLONY02、View陸上單位、開ORDERS、點停用列、兩次取消及
啟用單位完成。60張同步截圖均與自己實際輸入重播逐像素相同；16組四側重播的CPU、
完整RAM、VGA、DAC、輸入指紋、WAV與原有存檔相同。每語六張開單差異只在安全區，
停用色保留；錯地區整欄回原文、欄外維持既有顯示，關單後無新增殘影。
四語實際GUI並排圖已檢視。沒有新增亂數比較點，不增加來源普查shown。

規格054限定CONFORMED；正式二進位14a003cce886b70b793b28b71bd037bdaa18937fac74031519158e0fb41035f3。
總收據noto-orders-formal-check-20261011.json，SHA-256為
f75330b765495d8a3ca2af47f7c80a075e111ce380ae11daab1c174a16ce5b83，完整來源及重驗入口見規格054。
設定列及保留英數的既有隔離組裝器也重新組裝成功；原型九個抽取渲染區塊不變，
只同步來源守門。完整五語、設定列正式切換、其他欄位、HD及新版交付仍未完成。

沿用既有固定Python／Go工具映像，UID/GID1000、無網路、有界CPU／記憶體／PID與外層逾時。
原版與dosgolem唯讀，輸出只寫明確workplace目錄；Xvfb有trap且隨一次性容器結束。
字型、圖集、原版、存檔、音訊及新GUI均留本機；沒有遠端Issue、tag或Release操作。
本批正式變更尚未提交，收尾狀態追加於下方。

收尾核對PASS：64筆工作清單verify與生成稿全等，429個本輪文件相對連結、
既有規格051入口正對照及四個新增工具入口通過。六個Python來源語法通過，
工作根無root-owned檔或誤建.md目錄，修改檔及輸出皆1000:1000。
兩個工具映像無殘留容器；隔離dosgolem乾淨，upstream推送DISABLED。
850個已追蹤或待審檔案無原版、存檔、封存檔、音訊或字型誤收。
正式接線及本頁驗收紀錄於本輪一併提交、推送；提交號與推送結果以Git紀錄及本輪回覆為準。

## 2026-10-11：接續主選單五列的四語Noto正式接線

從已推送cf9c7ba接續。路由命中翻譯顯示隔離與文件職責，更新字型入口另核對README契約。
沿規格012重數原版五列色254的墨跡，建立規格055 DRAFT，逐語逐列試14至28px，
審查完整墨跡後升READY，再加入正式載入器。五列各選24／24／20／20／24px，
左上沿原版安全矩形，沒有全域套用六列命令欄18px。來源鍵、原版點擊與游標守門不變。

新增bake_noto_menu.py、noto_menu.go、四語來源／遮罩測試與正常GUI檢查器，均由目標186索引。
完整譯文仍只讀既有TSV，生成五列私用既有格式TSV與遮罩；綁定來源、字型、地區、
基準與目標TSV、原版畫面及授權。新增三個noto-menu參數；未啟用沿舊顯示。
錯地區、缺列、錯來源、缺檔、控制碼、錯字級與空白／越界遮罩整組回原文並逐列記錄。

325項Go測試零skip、go vet通過，含80個錯誤輸入與守門反例；六列命令欄測試保留。
45個烘製檔案及收據乾淨重生全同。四語各10張正常GUI，冷啟動、五列懸停、移開、
開載入頁、Escape返回主選單及點新遊戲皆通過。40張同步截圖與自身實際輸入重播全同；
16組四側重播CPU、完整RAM、VGA、DAC、輸入、WAV與既有存檔全同。差異限五列安全區，
每次懸停82／82／82／82／80個原版游標像素保留，重畫後恢復，離開主選單撤銷。

驗證過程修正容器輸出掛載；兩個隔離原型組裝初用沒有gofmt的Python映像，
改回既有Go映像在乾淨r2輸出重跑通過。游標檢查初只允許一處16×16差異，
原始idx證明差分含懸停與移開後兩處游標，依實際錄製座標修正檢查器後通過；
以上均為驗證環境或腳本問題，沒有為此改動前端行為。

規格055限定CONFORMED；二進位6078ddc2565860a6ba17b48ab64ff8fa269bf92b6b1206ddc4f6b95f51174d78。
總收據noto-menu-formal-check-20261011.json為
551ef86711d04879cb915c6bbed909317d1f6730dff93135f0ab6de4cae47a1f，完整重驗入口見規格055。
日韓未經母語校閱；完整五語切換、其他欄位、設定列、HD與新交付仍未完成，不增加shown。

沿既有固定工具映像，UID/GID1000、無網路、資源限制與外層逾時；Xvfb以trap收尾，
原版及dosgolem唯讀。字型、字模、原版、存檔、音訊與新GUI只留workplace。
本輪沒有Issue、tag或Release操作，依既有授權提交並推送本批接線；收尾結果追加於下方。

收尾核對PASS：64筆工作清單verify及生成稿全等，583個文件相對連結、既有規格051
入口正對照與五個新增檔案索引通過。五個Python來源語法及全部收據來源指紋一致。
855個已追蹤或待審檔案無原版、字型、存檔或音訊誤收；全工作根無root-owned檔或
誤建.md目錄，修改檔及產物皆1000:1000。兩個工具映像無本輪殘留容器，隔離dosgolem
乾淨且upstream推送DISABLED。提交號與推送結果以Git紀錄及本輪回覆為準。

## 2026-10-11：正式設定列、保存與重開驗收

從已推送20f27ed接續。使用者目標為完成HD與五語切換，既有commit／push授權沿用。
路由命中字型逐欄、翻譯顯示隔離與文件職責；grilling核對既有五語、Noto及畫面外入口定案，
沒有新增產品取捨。規格050 READY與051歷史原型證據保留，本輪建立056 READY再正式接線。

發現原視窗在拖曳經過設定工具列時提前送出DOS滑鼠放開，與既有契約不同。
先在隔離副本修正，328Go零skip及六組正常操作通過；再移入正式視窗。
工具列只在明確啟用時增加48px，原遊戲仍1280×800；設定開啟與失焦時不推進DOS，
關閉且實體輸入全部放開後恢復。驗收事件預設關閉，避免正式遊玩持續寫入畫面收據。

新增獨立前端JSON保存、嚴格格式讀取、明確參數優先及準備／保存／提交接點。
後端或保存失敗不切換、不損毀舊檔；取消不保存。介面譯文只在既有TSV，新增保存失敗訊息。
正式組裝器納入四個來源；舊設定原型入口改為核對並複製正式程式，不再用字串補丁接線。

353項Go測試零skip、go vet通過。第一次命令誤帶工作區不支援的-mod=mod，修正後重跑；
新增可變工具列高度需轉為float64，修正編譯型別後從乾淨r2輸出通過。
八組真實X11操作通過，包含原版拖曳、三態失焦、等待放開、取消、缺包拒絕、保存失敗及
切回繁中；兩次新行程經正常開場至選單，讀回繁中後從介面保存英文，再重開讀回英文。
原版字體與像素保留，取消不更動前端JSON，原版存檔全程不變。已檢視保存失敗畫面。

24筆實際DOS輸入、23筆設定事件，重播至77000000步；本輪、前版與原文控制三側的CPU、
完整RAM、VGA、DAC、時鐘、WAV及存檔全同，兩個繁中終點PNG與真GUI相同。
GUI總收據818cb101d4dbf6899b4e52875e25dad0245532f853d690059862c9ec180c6909，
重播總收據ed206fe3e85eb827c7f8d9a5921db0b629cecc7c4c62452ace0db26dda3d53e4。
18筆介面與四語全文的固定Noto字集全覆蓋，收據ec1f8c233ca77a8984d23cab39f46ecd72f1dea225f566d39784d1e401a17ca7。
完整來源、輸入與重驗入口見規格056。原型觀測收據與正式收據分開保留，不覆寫歷史。

規格056限定CONFORMED。完整語言包及HD仍缺正式資料與正常GUI，未增加shown或完整五語信用。
沿既有Go／Python工具映像，UID/GID1000、無網路、有界資源及外層逾時，Xvfb有trap。
原版與dosgolem唯讀，字型、字模、存檔、WAV及新GUI只留workplace；未改Issue、tag或Release。
收尾核對與推送結果於下方追加。

收尾核對PASS：64筆工作清單與生成稿全等，319個現行文件相對連結及五個新增入口通過，
規格051入口正對照有效。五個Python來源語法、正式組裝來源與產物指紋全等。
修改檔與輸出皆1000:1000，全工作根無root-owned檔或誤建.md目錄，兩個工具映像無殘留容器。
隔離dosgolem乾淨、upstream推送DISABLED；本輪只提交程式、譯文及文件，原版、字型、
圖集、存檔、WAV與GUI未納入Git。提交號與推送結果以Git紀錄及本輪回覆為準。

## 2026-10-11：完整語言接線前的來源讀法勘誤

設定列與保存已以16489bb推送main。接續完整語言包時，Go語法樹盤點四個正式顯示來源，
115個CJK字串常數中有八處實際文字或譯文判斷，涉及日期、船隻、選項、地圖、土地及航行；
來源、工具及定位見language-runtime-audit-20261011/check.json，SHA-256為
0840ea0dc67d6410c5917640f93a32d6f1dfd98eac08ef086d1e018a7c880475。尚未修改這八處行為。

建立規格057 DRAFT與完整Noto圖集原型工具，沿既有格式及六列已驗的完整墨跡字格。
追查文本消費端時發現規格053清冊讀法錯誤：兩個原文未閉合引號讓CSV合併相鄰實體列。
實際corpus867列、總數2008；原譯文錯綁CHIEFHOWDY／WARMANLY，GUIDES／THREATS缺鍵。
立即停止本輪尚未完成的舊清冊烘製，ABORTED.json標明不能套用；沒有接入正式語言切換。

規格053先回READY補審，改為正式Go的實體列及tab讀法，編輯用外語TSV仍使用標準CSV。
生成消費端文本時不引用CSV引號，不更動來源欄位；禁止實體換行或tab混入欄位。
三語將兩個既有譯文移回正確來源，各補兩筆，既有2006筆譯文內容保留，13份原始繁中表不變。
現各2008筆，2005譯文及3省略，基準完整欄位指紋重算。

10項測試、五語各兩次文本組裝全等、正式Go讀回四語52檔各2008筆通過，
各語17981非顯示欄位與原始實體列完全相同。規格053重新限定CONFORMED於文本契約，
舊865／2006及過去收據保留為歷史，追加勘誤，不把舊測試當作現行完整性證據。
總收據991ac85dbe10472db6c7e5308c3c389535d4ce8900ba4d67f75500eba877cb2b，
遷移收據c2d512c72279681308d2865800338c17457218ec1d32b435d2a8a35bf881a177；
完整指紋及重驗入口見規格053文末。沒有新的原版執行、正常GUI或shown信用。

已在新r2目錄依2008筆重生完整圖集；固定工具映像、UID/GID1000、無網路與有界資源，
來源唯讀，所有中間物只留workplace。完整語言包、八處固定文字、逐欄GUI與HD仍未完成。

完整四語八圖集含30至12px各級及95個ASCII。正式Go載入器讀回152組字級，
字距、字格高度、參考墨跡界與Alpha雜湊均與獨立參考相同；六項CLI錯誤輸入拒絕。
兩次乾淨重生61檔全等，收據aa3890befa37f44867bbeb5ee64ab4a4b530a7a13f8d083f1dacebbcca86e291。
完整字形證據與工具入口見規格057，仍為DRAFT；不增加正常GUI、完整五語或HD信用。

收尾核對PASS：64筆工作清單、生成稿全等，426個文件相對連結及兩個新增入口通過，
規格051入口正對照有效。13份原始文本指紋與61檔重生收據再次核對一致。
修改檔皆1000:1000，全工作根無root-owned檔或誤建.md目錄；三個工具映像無殘留容器。
隔離dosgolem乾淨且upstream推送DISABLED。僅提交程式、三語譯稿與文件，
圖集、字型及原版衍生收據留本機；本輪未寫入Issue、tag或Release。

## 2026-10-11：對話來源識別與冷啟動RAM限制

語料修正及完整字形原型已以c143c8a推送main。接續兩個固定繁中比較，
路由仍命中翻譯顯示隔離及原版對拍；沿規格035已驗來源建立058 DRAFT，
實際四語回歸先重現失敗，證據審查升READY後才修改正式辨識。

COLONYUNIT依原始來源合併完整名稱，另驗唯一強調群組與兩個槽位；
地圖載入標題依原始指紋及來源鍵辨識，另驗非空單行居中段落結構。
不修改譯稿、字模、幾何或原版資料。三個研究工具的來源綁定已重新審查，
Go語法樹證明loadAtlasFonts及dialogFont宣告未改，已知固定文字剩六處。

363項Go測試零skip、go vet及正式建置通過。新正常冷啟動17筆DOS輸入、七張GUI，
包含地圖檔名框、取消、重入與難度頁；標題及檔名已目視。三側重播至90200000步，
修正版、前版與原文控制的完整狀態、WAV及無新存檔一致；七張解碼RGB亦與GUI及前版相同。
初版檢查器誤比較PNG編碼bytes，改為解碼RGB後在同一收據重驗，沒有重跑或挑選GUI。

GUI完整RAM與三側重播在20bit線性位址0x67688有一個byte不同，其餘狀態相同。
移除額外checkpoint後仍重現，原因未知；完整RAM失敗保留，不稱同狀態PASS。
規格058保持READY，單位標題新GUI、四語逐欄及完整切換未完成，不增加shown。
來源、工具、程式與限制收據完整指紋見規格058。後續來源修正與冷啟動差異分開追查。

沿既有Go及驗證映像，UID/GID1000、無網路、有界資源與外層逾時；Xvfb有trap，
原版與隔離dosgolem唯讀。原始收據、圖集、字型、WAV與新GUI只留workplace。
本輪未寫入Issue、tag或Release，收尾核對及commit／push接續記錄。

收尾核對PASS：64筆工作清單與生成稿全等，422個現行文件相對連結及新規格058入口通過，
規格051入口正對照有效。363測試收據與正式來源相同，三個Python來源語法及綁定通過。
修改檔皆1000:1000，全工作根無root-owned檔或誤建.md目錄；三個工具映像無殘留容器。
隔離dosgolem乾淨且upstream推送DISABLED。只提交程式及文件，未知RAM差異明列未完成。

## 2026-10-11：完整語言包的組句接線

接續fc040ba，路由命中中文化顯示隔離與文件職責，載入相應入口。
先依現有來源與角色建立規格059 READY，再將14組日期、海上、VIEW、存檔、港口及航行
顯示詞序移入既有TSV。原有2008筆外語譯稿位元組前綴不變，13表增至2022筆。
display-組句不進一般模板；缺件、錯槽、未知角色與不安全代入皆回原文。
教學船名改讀既有定稿術語，字串圖集及教學字模以新綁定重生。

10項語料測試、五語兩次組裝全等、四語各18051非顯示欄位相同通過。
438Go零skip、go vet及正式建置通過。八組正常設定GUI及兩次重開通過，
25筆實際DOS輸入三側重播至76200000步，完整原版狀態、存檔、WAV及繁中終點RGB全同。
前版保留自身文本與字模；檢查器新增前版啟動器選項，避免以新模板污染舊比較。
完整指紋與工具版本見規格059，總收據留display-phrases-20261011/check.json。

初次字模工作遇到舊預覽主程式的fontTools載入依賴，改為僅在其main匯入，
在同一工具鏈重生通過。Go冷編譯首次逾時，增加有界逾時並用專案私有快取重跑。
文本CLI初次缺少外語--catalog、第二次輸出用了區外別名，均依既有參數與路徑契約修正；
沒有放寬驗證，也沒有把腳本或環境失敗當成產品缺陷。

規格059保持READY，沒有14種情境各自正常GUI與逐欄Noto完成信用。
完整語言包及HD仍未完成，接續新2022筆完整Noto圖集及整包後端。
Docker及文件收尾核對、commit與push結果接續追加。

提交前核對PASS：64筆工作清單與生成稿全等，437個現行文件相對連結通過，
規格051入口正對照及規格059、組句實作與測試入口有效。Python來源語法全通過，
修改檔及工作根皆無root-owned檔或誤建.md目錄，原版、字型、存檔與workplace未追蹤。
完整Noto重生容器仍在有界工作中；其餘本輪測試及GUI容器已自動清除。

組句接線已以182e911推送origin/main。新2022筆Noto圖集重生完成，八圖集152組字級
與前批Alpha、字距及墨跡全同，來源綁定更新。61檔只9檔改動，完整收據見規格057追加。
盤點現有67資源為64份固定字模及3個動態圖集，全部仍綁Cubic基準。
對話快取沒有完整段落原文及字格，字串快取沒有原始run的全部樣式及角色證據。
建立規格060 DRAFT並掛入目標186，作為整包交換與原文重建的接續入口。
沒有把圖集原型或設定可點選當成完整五語功能，HD範圍維持未完成。

本輪所有有界測試、GUI、重播及Noto工作已結束，容器清理狀態於收尾核對。

收尾核對PASS：64筆工作清單與生成稿全等，452個現行文件相對連結及新規格060入口通過。
新增收據指紋一致，修改檔及全工作根無root-owned檔或誤建.md目錄。
本專案掛載的Docker容器零殘留，隔離dosgolem乾淨且upstream推送DISABLED。
原版、字型、圖集、GUI、WAV、存檔與研究收據皆留workplace；未寫入Issue、tag或Release。

## 2026-10-11：四語64固定欄位與整包資源候選

從已推送e828969接續，沿既有commit／push授權。路由命中中文化顯示隔離與文件職責，
載入兩份入口；沒有新增產品取捨。規格060維持DRAFT，所有新載入及烘製工具只走隔離原型。

新增正式載入後的64欄匯出器及隔離組裝器，所有來源及既有字模通過綁定後匯出，
不推進DOS。逐欄保存原版墨跡、安全區及位置，Cubic尺寸只作比對。
新四語烘製器從13表解析譯文、變數及教學術語，以原版字高量測Noto TC／SC／JP／KR，
共256欄無缺字或越界。雙行字幕、離開問句、介紹及教學長文、強調層與英數分開驗證。
墨跡先在有額外留白的畫布量測，沒有用裁切後bbox冒充通過。

獨立檢查器核對完整文字、來源及譯文綁定、字型地區、Alpha、陰影及安全區。
每語13表、64固定字模及3動態圖集組成80檔候選，英文候選只保留原版顯示宣告。
Go隔離載入器驗實際五語候選及25個錯誤輸入，共30子測項零skip，go vet通過。
反例重算外層hash再驗內層，包含錯文本綁定、錯原版安全區、漏字級及缺ASCII。
兩次乾淨重生的固定資源565檔、完整候選包326檔全等；完整工具、指紋及重驗入口見規格060。
已查看韓文短欄及日韓最長介紹頁的本機預覽，這不代替正常GUI驗收。

初次量測把靜態橫幅誤分類為靠左欄位，修正分類後以相同輸入重跑。
初次gofmt遇到檔案可寫、父目錄唯讀的原子替換限制，改成先輸出至本機暫存，
再寫入明確可寫的單檔，於同一工具鏈乾淨重跑。沒有放寬欄位或來源閘門。

正式顯示來源及組裝器沒有修改，也沒有連結新Go原型。尚缺獨立原文觀測、暫停時重建、
正式整包交換、四語正常GUI及完整原版同狀態驗證；海上Noto逐欄排版仍待驗。
沒有新增shown、完整五語或HD完成信用，沒有改發行版。狀態表、目標186及#62本機驗證摘要
同步為目前進度，過去逐輪證據保留於本日誌及各規格。

沿既有固定Go及Python工具映像，UID/GID1000、無網路、有界資源及外層逾時。
原版及字型來源唯讀；所有字模、候選包、字型預覽及收據只留workplace。
未修改遠端Issue、tag或Release；提交、推送及Docker清理核對接續記錄。

收尾核對PASS：64筆工作清單與生成稿全等，1683個儲存庫相對連結及7個新增工具入口有效；
3個歷史私有圖片連結另列，未冒充現存產物。新Python語法、正式來源指紋及30子測項收據一致。
總收據final-check.json為708512744f376fc6839ee9941a2899adbfdbc02a154d67c443b35c1eca9452a9。
全工作根無root-owned檔或誤建.md目錄，本專案Docker容器零殘留，隔離dosgolem乾淨、
upstream推送DISABLED。原版、字型、字模及workplace均未追蹤；提交號與推送結果以Git紀錄為準。

## 2026-10-11：原文觀測與停止DOS後的四語重建

前批完整資源候選已以37697ed提交並推送main，沿既有commit／push授權接續。
路由命中中文化顯示隔離與文件職責。正式顯示來源及dosgolem未改，
新增工具只由規格060的隔離組裝器連結。

原文觀測在翻譯前深拷貝完整run，保留逐字位置、色號、描邊、貨物角色、離屏來源、
當次畫布及游標。字串在快捷鍵與描邊合併後保存，海上選單等待完整39字；
沒有模板或排不下的原文也保存。上限256筆及32MiB估算成本，移除最舊事件時計數。
五項新單元測試與既有回歸共443項通過，零skip、go vet通過。
初跑缺少原版及字型fixture的18項skip已在補齊唯讀輸入後乾淨重跑。

25筆既有正常GUI輸入四側重播至76200000步，觀測開啟、關閉、前版及原文控制的
CPU、完整RAM、VGA、DAC、WAV及存檔全同；三側繁中合成RGB與原GUI一致。
共保留201筆，終點53筆來源像素與完整RAM獨立核對相同，容量移除0筆。
visible只表示來源像素仍相同，不能獨自授權覆蓋。

接續完整候選的實際目錄載入，發現日韓各155筆無年份的殖民地名稱缺括註，
被原有loadStringCatalog拒絕。沿規格038既有「譯名（原名）」決定補齊同列原名，
只改310個顯示欄；來源欄位、原譯名及18筆含年份的名稱保留。
規格053先記錄READY格式補充，再在文本讀取及組裝加入相同守門與反例，11測試通過。
四語字模與圖集重生，256欄圖像及152組字形資料和前批全同，只有文本與綁定更新。
完整候選載入與25反例共30子測項通過；最新原型446Go零skip、go vet及建置通過。

在DOS停止後重建四語對話與字串，使用執行前已準備的完整候選及保留原文。
英文與原版控制逐像素相同；四語8／8／7／8欄差異只在完整安全區。
日文Jamestown排不下，保留原文並記錄；韓文同欄重新量得19px，已檢視日韓畫面。
最新四側重播與重建前後的完整原版狀態全同，沒有原版重啟、重印或額外輸入。
海上及固定欄未接入本切片，歷史VGA同步、部分遮擋、畫面世代及正式交易仍待驗。
規格060維持DRAFT，未增加普查shown、正常GUI、完整五語或HD信用。

初次隔離組裝誤將無go.sum的dosgolem根目錄當作前端模組，修正參數預檢後重跑。
重建初版漏傳字串面板參數，依正式呼叫點補上後在新的模組重建，未放寬正式來源守門。
本機完整工具、版本、指紋與重驗入口見規格053及060；實測檢查器副本保留於workplace，
其後只改限制描述，未為文字修正重跑已通過的原版工作。

沿既有Go與驗證映像，UID/GID1000、無網路、資源上限與外層逾時；Xvfb有trap。
原版與隔離dosgolem唯讀，只有明確輸出及編輯檔可寫。原文畫布、字型、圖集、
存檔、WAV與新畫面只留workplace。本輪未寫Issue、tag或Release。
文件、工作樹、擁有權及Docker清理結果接續追加。

收尾核對PASS：64筆工作清單與生成稿全等，1719個儲存庫相對連結及6個新工具入口有效。
3個歷史私有圖片缺檔另列；Python語法、10份隔離組裝來源指紋及最新實測收據一致。
日韓只改310個顯示欄，原版、字型、字模、存檔、WAV及workplace未追蹤。
修改檔及輸出皆1000:1000，全工作根無root-owned檔或誤建.md目錄。
本專案Docker容器零殘留，隔離dosgolem乾淨、upstream推送DISABLED。
總收據native-final-audit.json為eeaf06037b2749224719117e3250ec5b4df0c2303e3d5cb9d193d483110a0fda。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-11：海上原文重建接線

前批原文觀測與對話／字串切片已以cf58331提交並推送main，工作樹核對乾淨。
沿既有commit／push授權與顯示語意隔離路由接續，不變更原版或正式後端。

隔離重建器加入海上詞典與四地區Noto圖集的實際載入，逐詞核對原版來源。
頂列六欄各自量原版起點及下一欄邊界，快捷鍵與譯文同字型並保留色號。
狀態欄依原版墨跡、圖集頂端與實際字形聯集核對安全區；
來源、背景、VGA或排版不符就回原文，缺譯紀錄保存原文。
成功的海上行才攔下重複字串覆蓋，未命中的內容仍走既有字串規則。

448項Go測試零skip、go vet及建置通過。兩項新增測試涵蓋逐欄縮字、
完整原文、快捷鍵色號、過長、覆寫、背景、VGA遮擋及游標；自建字模不算原版證據。
初跑兩項舊Noto測試因未指定夾具而skip，補齊原有唯讀目錄後全套重跑，未放寬測試。
最終25筆玩家輸入四側重播至76200000步，CPU、完整RAM、VGA、DAC、WAV與存檔全同。
停止DOS後四語各12／12／11／12欄，頂列、日期及金額均實際重建，差異只在安全區；
英文逐像素等於原版，重建前後原版狀態全同。四語畫面與繁中相鄰行放大檢視通過。
補齊缺譯原文紀錄後以最終程式重跑，畫面與前次全同。

收據、工具與雜湊見規格060。固定欄快照的前後像素由overlay.Patch封裝，
還需獨立原文觀測；不能由舊中文字模反推。固定欄、生命週期、正式交換及正常四語GUI仍待驗。
規格060維持DRAFT，不增加shown、完整五語或HD完成信用，未寫遠端Issue、tag或Release。
原版、字型、字模、快照、畫面、存檔及WAV均只留workplace；Docker及文件收尾接續記錄。

收尾核對PASS：64筆工作清單與生成稿全等，1723個儲存庫相對連結有效。
三個已登錄歷史私有圖片缺檔另列，主機絕對路徑不冒充儲存庫相對連結。
10份隔離組裝來源及5份Go檔與實測版本一致，最終五語RGBA與前次全同。
總收據sea-rebuild-final-audit.json為b9c57a690b580aecdf5bc304155e6d02b06d8bc4ccb43e70eda0138f3264db5e。
工作根無root-owned檔或誤建.md目錄，本專案Docker零殘留；隔離dosgolem乾淨、
upstream推送DISABLED。沒有追蹤原版或私用產物，本批依既有授權提交並推送。

## 2026-10-11：固定欄原文快照與四語重建

前批海上接線已以a8f6335提交並推送main，工作樹乾淨。
接續既有commit／push授權；回查顯示語意隔離及文件職責路由，沿用現有工具與文件。

隔離觀測器在既有固定欄接受原版輸出時，保存原版鍵、安全區、印前／印後像素與樣式。
每幀核對整個來源安全區，背景或模式改變後單向失效；相同像素返回不能復用。
四語各64欄實際字模載入後，重解包內TSV的控制碼、字幕槽位、冒號與術語，
核對顯示文字指紋，再依各欄量測位置、字級、前景、陰影與強調色重建。
正式前端、隔離dosgolem與原版資料未修改，規格060仍DRAFT。

457項Go測試零skip、go vet及建置通過，包含實際四語資源及撤銷反例。
r8初次建置因新測試漏匯入bytes失敗，補齊後以新的r9模組乾淨重跑。
原有25筆正常GUI輸入四側重播至76200000步，CPU、完整RAM、VGA、DAC、WAV與存檔全同，
三側合成RGB與GUI基準全同。新增16筆固定事件後共217筆，容量移除0筆；
終點所有固定快照已撤銷，五語RGBA仍與前批海上重建全同。

主選單32000000步、載入12000000步沿既有設定GUI輸入前綴，
難度70290000步及選國77550000步沿已驗新局GUI輸入前綴，各作四側重播。
四語分別重建5、1、5與4個固定欄，英文逐像素等於原版，差異只在安全區。
四語主選單、難度與選國共12張畫面已檢視，另抽看日文載入訊息。
檢查器綁定新局驗證收據與輸入指紋，不將新停點冒充歷史GUI終點或新增現場操作。
加入新局來源前的實測檢查器已逐字保留，收據入口見規格060。

英國介紹88770000步另作四側重播，四語各重建一欄，正文、陰影與強調色保留。
英文逐像素等於原版、四語差異只在安全區，四張畫面已檢視；五個固定欄停點均通過。
介紹頁接受881筆事件，256筆上限移除625筆，當前固定欄仍完整保留。
收尾檢查初版誤把所有停點都假設為零移除；依原始收據改驗上限、成本與移除計數平衡，
不改產品程式或既有重播條件。正式可見來源保存策略仍待驗。

原文接受仍經既有字模初始化，正式接線前須拆開；其他固定欄正常路徑、
完整生命週期、正式整包交換與四語現場GUI仍待驗。不增加shown或HD完成信用。
原文、圖集、字型、畫面、存檔及WAV只留workplace，未寫Issue、tag或Release。
沿既有Go與驗證映像，UID/GID1000、無網路、資源上限及有界Xvfb；收尾核對接續追加。

收尾核對PASS：64筆工作清單與生成稿全等，1728個儲存庫相對連結有效，
三個既有私用圖片缺檔另列。10份隔離來源指紋、5份Go格式及六組四側重播收據一致。
原版、字型、原文快照、字模、畫面、存檔與WAV未被追蹤，修改檔及輸出皆1000:1000。
工作根無root-owned檔或誤建.md目錄，本專案Docker零殘留；隔離dosgolem乾淨、
upstream推送DISABLED。fixed-rebuild-final-audit.json為ef19ebd42394a6ea17c9cba476ed01ab0e330681972dcf2bc1962826e4fdeffe。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-11：原文觀測與舊字模解耦

前批固定欄接線已以abbeaf1提交並推送main，工作樹乾淨。
沿既有授權接續；回查顯示語意隔離及文件職責，先在規格060補DRAFT契約。

隔離組裝器把原文讀寫、事件收尾及靜態辨識從字模可用性與控制模式分開，
原版版本、來源、改色數量與同步條件不變。靜態字色與底圖補回沿規格034及既有烘製器，
不再讀舊中文字模；指紋外框及DAC改變也會撤銷觀測，再由完整原文指紋建立新筆。
正式前端、dosgolem與原版資料未修改，規格060維持DRAFT。

459Go零skip、go vet及建置通過。r10首跑漏設DISPLAY，在視窗初始化失敗，
補齊既有Xvfb後乾淨重跑，未放寬測試。真正缺字模反例另找出海上舊字形建構的nil讀取，
分開原文收尾與字形建構後，以新r11模組完整重測，失敗產物保留供回查。

一般模式與16個舊字模／圖集參數確實缺檔的原文模式各作四側重播，
25筆實際玩家輸入至76200000步，CPU、完整RAM、VGA、DAC、WAV及存檔全同。
兩組完整原文觀測檔逐位元組相同，各218筆、拒絕91筆、容量移除0筆。
五語重建RGBA與r9全同，英文及缺字模觀測畫面逐像素等於原版控制；
既有繁中控制仍與GUI基準全同。載入與選國缺字模停點也四側通過，
各語1／4固定欄的RGBA與既有收據全同，沒有用有效字模加missing旗標代替缺檔。
英國介紹88770000步的缺字模四側比較也通過，四語各一欄及全部五語RGBA與r9全同。

目前可見來源的保存、完整生命週期、正式整包交易及四語現場GUI仍待驗；
本批未增加shown、HD或發行信用。原文、畫面、字型、字模、WAV與存檔只留workplace。
沿既有Go與驗證映像、UID/GID1000、無網路、資源上限及有界Xvfb；收尾核對接續追加。

收尾核對PASS：64筆工作清單與生成稿全等，1730個相對連結有效，
三個既有私用圖片缺檔另列。10份來源指紋、459Go案例、五組四側重播及五份Go格式通過。
完整與缺字模觀測逐位元組相同；所有缺字模路徑在重播前後均確認不存在。
原版與私用產物未被追蹤，修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留；隔離dosgolem乾淨，upstream推送DISABLED。
fontless-observation-final-audit.json為88b2e052cc41962a9133de220351f393f8b5e8e34ec17320a76da35287690ddf。
檢查器實測副本為同根check-language-observation-replay-r11.py，雜湊與規格060一致。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：五語記憶體交易與停留抽樣

舊字模解耦已以4c688bc提交並推送main，接續同一目標與既有授權。
回查顯示語意隔離與文件職責，在規格060先記DRAFT交易及容量反例契約。
隔離後端以單一物件共同提交完整語言包、當次重建畫面與選項，
沿既有applyDisplayPreferences先準備、保存設定，再提交。
取消及保存失敗保留舊物件、畫面與設定；提交不重新讀取語言清冊或原版。
正式前端、dosgolem、原版資料與FIFO策略未改，規格060維持DRAFT。

r12測試將只有五個登錄檔的versions表誤當全部文字檔清冊，屬測試索引錯誤；
修正為已登錄檔先核對，其餘沿既有資料表載入器驗來源。
新r13模組473Go零skip、go vet及建置通過，失敗產物保留。
正常及實際缺少16組舊字模的25筆玩家輸入各作四側重播，
五語準備後取消、保存失敗及成功提交全通過，完整原版狀態、RAM、VGA、DAC、WAV與存檔全同。
兩組原文觀測逐位元組全同，全部五語RGBA與r11全同；獨立交易稽核abb95af3…通過。
英國介紹新局輸入前綴至88770000步的缺字模四側交易也通過，
四語完整長文各一欄及五語RGBA與r11全同，總收據ada7ef1d…。

容量抽樣沿r11及相同25筆輸入延長停留至650000000步，四側完整同狀態通過。
接受368筆、移除112筆、保留256筆，頂列、日期與金額仍在，未重現所懷疑的頂列遺失。
沒有據此調整容量策略或聲稱完整可見來源保存已完成，總收據0bca058b…。
檢查器副本第一次從私用目錄啟動時入口根目錄不符，未執行原版；改回正式工具入口。
舊90秒額度不足以跑延長停留，按原版步數同比例增加後同條件乾淨重跑。
工具版本、完整來源與收據指紋見規格060；全程沿既有Go／驗證映像、資源上限及有界Xvfb。
尚待可見來源保存、完整生命週期、正式後端及四語現場GUI，不增加shown、HD或發行信用。
私用原文、字型、畫面、WAV、設定及存檔只留workplace；收尾稽核與Docker清理接續追加。

收尾稽核PASS：473Go零skip、10份來源綁定、四組四側重播及五語交易收據一致，
64筆工作清單與生成稿全等，1730個相對連結有效，三個既有私用圖片缺檔另列。
原版與私用產物未被追蹤；修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
五份Go格式通過，本專案Docker零殘留，隔離dosgolem乾淨且upstream推送DISABLED。
language-transaction-final-audit-r13.json為5959169d7e2a8f42323d5633242111bb0ea3172332810f87b8860c0ad0816d32。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：隔離視窗五語接線與數值顯示

路由命中中文化顯示隔離及文件職責，沿用兩份契約與規格060 DRAFT。
隔離組裝器新增--draft-native-live，使用已驗記憶體語言包交易與原版觀測。
當次畫布、地圖、VGA、DAC、游標、按鈕、來源計數或固定欄失效改變即重建；
相同輸入重用上一張畫面，收據與生效物件分開。正式來源及dosgolem沒有變動。

最新隔離視窗505Go零skip、go vet及建置通過。主選單、世界與殖民地共15組現場五語切換通過，正常進城及返回世界均保留原版操作；四語殖民地各重建19至20欄，含已驗保留英數。23筆實際DOS輸入重播至77600000步，四側完整原版狀態、RAM、VGA、DAC、存檔與重播WAV全同，即時重播終點與本次GUI逐像素相同。
現場五語切換的按鍵放開、暫停、設定保存、安全區及英文原版像素均通過。
原文狀態與畫面只讀；GUI完成進城、返回世界與正常關閉。
首批r16已通過現場GUI與四側重播，之後目視發現數值仍用原版字，
查明重建英數誤用waiting-screen階段；修正為當次原版可見性並補記略過原因。
r17驗證誤把安全區已改寫的90% (3)列為必須覆蓋，保留失敗收據；
r18確認90與10% (0)的四語Noto，其他改寫欄回原文，未放寬安全條件。
r14／r15開場的失敗是GUI探針輸入前綴不足，使用既有前五筆後重跑。
所有版本各用新的workplace輸出，未覆寫先前證據。

完整指紋、工具版本與重生入口見規格060。本次GUI總收據4c325531a89a390d17bdbc26fef8d325d9bd66f1db9af3a7f09aa3d9a9d613ca，
四側重播總收據0976766f91c2726af84f7da0cf67a9acdf4613935dc1a6ace161ff520b390ccb。
英數新回歸測試使用實際四語Noto候選；自建墨跡只驗可見性守門，不當原版排版證據。
已目視繁中與日文殖民地；地圖地名與部分安全區改寫欄仍是已知缺口。
可見來源保存、完整生命週期、正式接線、其他GUI及存讀檔仍待完成，不增加shown或HD信用。
本批依既有授權接續commit及push，結果以Git紀錄為準；收尾稽核與Docker清理接續追加。

收尾稽核PASS：505Go零skip、10份來源綁定、15組實際X11切換及四側完整原版重播一致。
60筆暫停事件各組原版狀態固定，四語差異只在安全區，英文逐像素等於原版。
64筆工作清單與生成稿全等，1732個相對連結有效，三個既有私用圖片缺檔另列。
原版與私用產物未被追蹤；修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留，隔離dosgolem乾淨且upstream推送DISABLED。
native-live-final-audit-r18.json為e507ecbcbd61136f0e4a6ce7e21eb408108137cad36da8413fd0f61d7544cc65。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：HD首座建築v3輪廓修整

HD素材修整未命中額外知識列，沿目標186與既有文件職責契約。
本輪使用imagegen技能與內建image_gen.imagegen工具；已先檢視v2、定稿畫風及原版幾何。
提示只修整輪廓、透明邊界與殘留色點，要求保留既定筆觸、建築設計、23:27畫布及來源位置。
生成原圖原封不動複製至workplace/reports/goal186-display-hd/building-032-candidate-v3.png，
1158×1359 RGBA；JSON保存完整提示、三份參考指紋及來源路徑。未覆寫v2或定稿樣張。

既有只讀幾何檢查器核對原版BUILDING.SS與第032幀，按同一92×108目的畫布及alpha≥128量測。
原版7040點中6293點有候選覆蓋，747點未覆蓋、328點外溢，比v2多19點外溢。
此結果未證明修整有效，v3未選為正式素材；不以覆蓋百分比當正式通過門檻。
下一步應取得原版繪製前底圖、完整呼叫邊界與遮擋證據，避免在缺少清除契約時繼續改圖。
候選及原版參考只留workplace，不加入Git、發行包或公開圖片；沒有HD完成信用。
工具沿既有驗證映像、唯讀原版及使用者UID，Docker清理與全工作樹擁有權於本輪收尾核對。

## 2026-10-12：九億步容量反例修正與HD呼叫邊界

回查中文化顯示隔離、文件職責與IDA9.4路由，沿既有契約及技能。
預先固定同一25筆正常GUI輸入與900000000步終點，先跑舊r18四側再修正。
舊FIFO接受434筆、移除178筆，原版仍有378點的頂列來源被移除，四語頂列均遺失。
修正隔離觀測器的完整原文重印合併及不可見優先回收，上限仍256筆／32MiB。
不同原文、位置、樣式、墨跡或游標不可合併；取樣缺失保留舊佇列並拒絕新觀測。
唯一來源全部可見時仍有界回退，另記可見來源移除數，沒有宣稱全流程零遺失。

r19的535Go零skip、go vet及建置通過。九億步接受434筆、合併197筆、保留237筆、
17372858bytes、零容量移除；四語頂列恢復，英文逐像素等於原版，差異只在安全區。
修正前後四側CPU、完整RAM、VGA、DAC、WAV及存檔全同，獨立總收據af78a4d7…。
同一r19另跑主選單／世界／殖民地15組實際五語切換，22筆正常DOS輸入四側重播
至76000000步通過，終點與GUI逐像素相同；已目視日文及韓文殖民地。
完整指紋見規格060，規格仍DRAFT；完整生命週期、存讀檔與正式接線接續處理。

HD單建築研究從既有唯讀EXE建立一次性IDA資料庫，唯一16bytes對應EA0x1C532。
IDA自動函式導覽EA0x1C36A，再由原版正常玩家路徑確認0D46:000A入口及121D:1554返回。
第032幀534bytes來源與440個不透明像素完全相同，各點寫一次，透明處與周圍底圖不變。
完整原版狀態與既有無觀測對照相同；參數一般語意、遮擋、重畫及動畫仍待驗。
總收據7d975aec…，原始定位、工具、地址空間及指紋追加RESEARCH-LOG.md，未改歷史紀錄。
未選用v3、未接正式HD、未改原版或dosgolem；原版、字型、快照、畫面、WAV及存檔只留workplace。
本批未寫Issue、tag或Release，依既有授權接續commit與push；收尾核對與Docker清理接續追加。

收尾腳本初次沿用r18的23筆輸入假設；本次r19原始GUI收據實際為22筆。
依該收據修正本次文件及核對腳本後重跑，不修改GUI輸入或產品比較條件。

收尾核對PASS：535Go零skip、10份來源綁定、15組現場切換、四側重播、
容量修正及HD單次呼叫差分收據一致；64筆工作清單與生成稿全等，1738個相對連結有效。
三個已登錄歷史私用圖片缺檔另列。六份Go格式及HD探針go vet通過。
原版與私用產物未被追蹤，修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留，隔離dosgolem乾淨且upstream推送DISABLED。
native-capacity-hd-final-audit-r19.json為cfb6e45c4c771550f12d6d7862ffa6546adf3a73be5a2a571173d2f0aad7cc4e。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：正常存檔五語生命週期抽樣

32eb9e5已提交推送並核對遠端main，工作樹乾淨後接續本批。
沿既有顯示語意隔離與規格060 DRAFT，增加--save-cycle研究驗證，不改正式前端或r19二進位。
以已驗正常玩家操作開啟存檔插槽，原版選槽即保存；成功通知及返回世界另各作五語切換。
初次錯套另一條新局的描述階段；第二次誤讀對話收據未提供的source欄位。
兩次失敗均屬驗證腳本，原版已正常存檔。回查路由、收據格式與既有SAVEGOOD鍵後，
以當次可見GAME.TXT:0x000007B9判定成功，再要求返回世界時撤銷，不用殘留診斷文字。
兩次失敗私用輸出保留，未放寬產品守門或原版比較條件。

r19-c的30組真實五語切換通過，120筆設定事件的原版狀態暫停，英文等於原版，
四語差異只在安全區。35筆實際DOS輸入四側重播至93600000步，
CPU、完整RAM、VGA、DAC、WAV及兩份存檔全同，即時終點與GUI逐像素相同。
新COLONY00.SAV為9fce2ddeebc0298544ddf06b9ed713e23d51e871b85190f7d4a6e19e34d84def，初始檔不變。
已目視日文成功通知及韓文返回世界，通知關閉後沒有舊覆蓋。
GUI總收據3a128128…，四側重播402843ce…，完整指紋與入口追加規格060。
535Go及go vet沿用未改二進位的前批證據；本批只改驗證工具、DRAFT抽樣契約及文件。
新行程讀回新存檔、完整生命週期及正式接線仍待驗，未增加shown、HD或發行信用。
未寫Issue、tag或Release；收尾核對、Docker清理及既有授權的commit／push接續完成。

收尾核對PASS：30組真實GUI、120筆暫停事件、四側重播及兩份存檔一致。
既有535Go與10份來源綁定沿用，64筆工作清單與生成稿全等，1740個相對連結有效。
三個已登錄歷史私用圖片缺檔另列；來源撤銷、英文原版及四語安全區重新核對通過。
原版與私用產物未被追蹤，修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留，隔離dosgolem乾淨且upstream推送DISABLED。
native-save-cycle-final-audit-r19-c.json為d5166eec8801bb24b60624afd935014fd66ebbbf9816d6bbbd72e32bdbd79042。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：新行程讀回及動態清單缺口定位

上一輪32eb9e5及7499cfb已推送，接手時main與工作樹核對乾淨，Git身分正確。
路由命中中文化顯示語意隔離，載入該契約與文件職責；沿現有DRAFT規格及工具。
五語GUI探針新增--reload-save及--reload-proof，先驗前批GUI、重播與兩份存檔指紋，
複製到新目錄並啟動獨立行程，原版正常讀取COLONY00.SAV。
初次點擊只選船，第二次改座標亦未進城；回查路由、原始輸入及原版畫面，
改為正常選船後按原位置進城。兩次失敗屬探針選取狀態假設，沒有修改產品或原版。

25組真實五語切換與100筆暫停事件通過，23筆實際輸入四側重播至46000000步。
CPU、完整RAM、VGA、DAC、WAV及兩份存檔全同，即時終點與GUI逐像素相同。
讀檔通知關閉後撤銷，正常進城及返回世界通過；已目視日文通知與韓文殖民地。
GUI總收據ff495c61…，四側重播5be644f7…，完整指紋見規格060。
535Go及go vet沿用未改的r19二進位，正式前端與dosgolem未修改。

畫面審查另確認讀檔清單十列、162字元已觀測但尚未重建，line-no-template保留原文。
原始字格及20bit線性RAM 0x2AA62只定位本次來源，不能當一般語意身份。
幾何初核錯假設每字墨跡都高5px，改依實際垂直交疊分組才得到十列；
清單缺口收據8d8077b6…保留逐列墨跡及色號，不授權正式行為。
下一個實作重點為動態清單與輸入欄的原文重建、逐列Noto及來源守門；規格060仍DRAFT。
不增加shown、完整五語或HD信用；原版、存檔、字型、畫面及音訊只留workplace。

唯讀來源核對曾遇自動權限審查逾時，按工具回覆重試一次後成功；未因逾時重跑既有原版行程。
沿既有隔離映像、使用者UID、無網路、資源上限及有界Xvfb；未寫Issue、tag或Release。
收尾核對、Docker清理與既有授權的commit／push接續完成。

收尾核對PASS：25組真實GUI、100筆暫停事件、四側重播及兩份讀回存檔一致。
既有535Go與10份來源綁定沿用，64筆工作清單與生成稿全等，1742個相對連結有效。
三個已登錄歷史私用圖片缺檔另列；十列清單缺口保留，未增加完整頁面的完成聲明。
原版與私用產物未被追蹤，修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留，隔離dosgolem乾淨且upstream推送DISABLED。
native-reload-cycle-final-audit-r19-c.json為29da19d39d11274d62ff7dc333baf93b734725a0db0b31f341f1591aa074c40d。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：插槽清單Noto與底緣守門修正

4b4cf2a已提交推送，遠端main核對一致後接續本批。回查路由仍命中文化顯示語意隔離。
短重播確認首份十列清單在22440000步已完整觀測及翻譯；終點佇列回收使它未出現在前批匯出。
另確認原版VGA與邏輯畫布最後一列有十個墨點不同，原有完整安全區守門因此保留原文。
反白重印使舊清單失效，也讓重建器失去仍有效的標題上下文。完整根因追加RESEARCH-LOG.md。

依規格060新增DRAFT契約，隔離重建器借用未改寫標題，只對完整8／10列重新識別插槽。
底緣回退以實際Noto字模及原版可見墨跡量測覆蓋區；每格須仍可見，區內像素完全相同，
區外保留原版。四語讀檔各18px，存檔八列各21px，沒有外推全域字級或裁切字模。
551Go零skip、go vet及建置通過；實際四語Noto獨立量測與缺候選／未知來源／過長譯文回退通過。
新增反例含失效標題、錯列數、未完成來源、內部遮擋、不可見字格及字模伸入差異區。

正常讀檔25組及存檔30組真實GUI通過，兩批共220筆暫停事件。
兩批各自四側重播，分別23筆輸入至44200000步、35筆至92200000步；
完整CPU、RAM、VGA、DAC、WAV及存檔全同，即時終點各與其GUI逐像素相同。
英文等於原版，四語差異只在實際覆蓋區。已目視日文讀檔及韓文存檔清單。
GUI探針新增清單必須實際重建的條件；舊存檔來源二進位與其原四側證明綁定，
允許修正後顯示版本讀回同一已驗存檔，原有來源、輸入、狀態及存檔守門保留。
總收據與重生入口見規格060；規格仍DRAFT，輸入欄、正式接線及HD接續處理。

診斷首建缺少go.work指定的/dosgolem掛載，修正為既有隔離副本的唯讀掛載。
窄重播初次未縮短原GUI收據終點，原版在開始前被明示上限拒絕；保留失敗命令與記錄，
改用同一GUI前綴及相同終點後重跑。字模單測初次缺Xvfb，在相同映像及命令補上有界Xvfb後通過。
這些是工具環境與前置檢查失敗，沒有修改產品比較條件或當成原版缺陷。
正式前端、dosgolem、譯文及原版資料未改；沒有Issue、tag、Release寫入。
收尾核對、Docker清理與既有授權的commit／push接續完成。

收尾核對PASS：551Go零skip、四語實際Noto無裁切、55組真實GUI、220筆暫停事件及八側重播一致。
10份來源綁定正確，64筆工作清單與生成稿全等，1743個相對連結有效。
三個已登錄歷史私用圖片缺檔另列；十個底緣差異點仍保留原版，未知硬體成因沒有猜補。
原版與私用產物未被追蹤，修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留，隔離dosgolem乾淨且upstream推送DISABLED。
native-slot-fit-final-audit-r21.json為ecce1055b2b9f0bb1d7874a6c9fc0e5dfd8aa663eb4a554a867d1661b27fec71。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：改名姓名的四語Noto與原版游標

命中中文化顯示語意隔離與文件職責路由，載入相應契約。
沿正常進城及城市標題改名操作取得35GUI基準。r22補記逐字ES:DI，
同29筆基準輸入的完整原版狀態、RAM、VGA、DAC及WAV全同。
隔離覆蓋保留玩家ASCII原值、空格、大括號及原版底線；逐欄量測字級，
未知字格、來源、缺字或已抹除內容回原文。

r23d完整558Go零skip、go vet及建置通過，針對性45項也通過。
35組真視窗切換、140筆暫停事件及30筆實際輸入至89000000步的四側重播通過。
四語姓名各30px；刪字、重打及取消沿原版操作，完整原版狀態、RAM、VGA、DAC、
WAV與存檔全同。英文保留原版像素。總收據及重生入口見規格060。

首建r23使用不存在的dialogShown欄位，編譯前即被拒絕，修正後r23b完整558項通過。
其後補足原始空格、大小寫基線及已抹除來源守門，再驗r23c／r23d。
r23c首次GUI被2GiB容器OOM終止，Docker事件已確認；沒有將該次當成完成收據。
相同映像與2GiB上限設定GOMEMLIMIT=1200MiB後乾淨重跑通過。
最終r23d GUI峰值1822228480 bytes。失敗輸出保留本機，不當成原版缺陷。

正式前端、dosgolem、原版資料及譯文未改；沒有Issue、tag或Release寫入。
規格060與057保持DRAFT，正式資源入口仍依賴研究路徑，接續移除並審查正式接線。
收尾核對及Docker清理另記於下，依既有授權commit與push。

收尾核對PASS：558Go零skip、35組真視窗、140筆暫停事件、12組原版游標逐像素核對及四側重播一致。
10份來源綁定正確，64筆工作清單與生成稿全等，1748個相對連結有效。
三個既有歷史私用圖片缺檔另列，沒有新增公開素材或追蹤原版。
修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留，未重建映像；隔離dosgolem乾淨且upstream推送DISABLED。
本機native-input-final-audit-r23d.json為4a2519fd42c6010c9362c2b5c6a48a45e86790e03ae37bc55d652ce91f70ee11。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。


## 2026-10-12：可信語言索引與READY審查

命中中文化顯示語意隔離及文件職責路由，沿目前程式與收據確認r23d已有實質進展。
移除載入器對/repo清冊及候選旁fields.json的依賴；產生器只接受既有64欄指紋，
編譯索引僅保存來源鍵、檔名、幾何及指紋。13表清冊以Go內嵌，語言包格式未改。
組裝器補連結先前未包含於完整視窗模組的載入反例測試，來源綁定由10增至14。
完整592Go零skip、go vet及建置通過，無/repo或研究清冊的容器34項通過。
實際程式在沒有研究來源的容器重播30筆舊GUI輸入至89000000步，
原版完整狀態、原文觀測、五語畫面、WAV及存檔與r23d基準相同。

新50組五語GUI含改名、刪字、重打、取消及正常存檔，200筆暫停事件通過。
42筆實際輸入至104200000步的四側完整原版狀態、RAM、VGA、DAC、WAV與兩份存檔全同。
256固定欄獨立全文量測與實際包字模比對通過。2GiB GUI峰值1832480768 bytes。
可攜重播首試因映像內建空/repo而停在前置檢查；確認無來源後改查來源不可取得，
相同程式及原始輸入重跑通過。沒有將前置環境失敗寫成產品缺陷。

逐項審查規格057及060的原有閘門後升READY，授權接正式後端，尚未CONFORMED。
未知樣式、其他未驗欄位及過長譯文維持原文回退；原目標的完整五語及HD範圍不變。
修正CONTEXT與機器工作清單中仍把已驗清單及改名欄列為未完成的舊敘述；
完整歷程留在WORKLOG與規格，不再複製到目前狀態表。
正式前端、dosgolem及原版未改，沒有Issue、tag或Release寫入。
收尾核對與Docker清理另記於下，之後依既有授權commit與push。

收尾核對PASS：592Go零skip、14份來源綁定、50組真視窗、200筆暫停事件及四側重播一致。
12組原版游標逐像素核對、34項無研究來源載入、實際程式可攜重播及256欄全文量測通過。
64筆工作清單與生成稿全等，1752個相對連結有效；三個既有歷史私用缺圖另列。
原版素材未被追蹤，修改檔及輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
本專案Docker零殘留，未重建映像；隔離dosgolem乾淨且upstream推送DISABLED。
本機native-index-final-audit-r24.json為57bc9158eedadedcfaef86777e194c2f785bdf31a2800e6bf1b48ce70c0114cf。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：正式五語整包後端接線

命中本地化顯示語意隔離及文件職責路由，沿規格057／060 READY進行既定實作。
正式組裝器共用既有來源核對、原文觀測及整包後端，保留live_menu.go幾何來源指紋。
正式啟動器直接指定五語資源與設定列；原文觀測及停止重建匯出改由診斷旗標控制。
封裝器核對並收取五語資源、設定列字型與授權，Windows命令沿共用旗標轉換。

605Go零skip、go vet及建置通過。正式入口50組五語GUI完成改名取消與正常存檔；
另25組在新行程讀回這次存檔，含十列清單、成功通知、返回世界及進城。
兩條路徑共300筆暫停事件及八次重播，完整原版CPU、RAM、VGA、DAC、WAV與存檔一致。
不加診斷旗標的正式啟動亦通過同一路徑，原文觀測與五語重建匯出不存在。
六種錯誤封裝拒絕通過。2GiB下兩路GUI峰值1904087040／1791373312 bytes。
初次封裝前置檢查補認既有根目錄check.json，該研究收據不收進套件；語言資源未改。

規格057／060限定CONFORMED於正式整包交換及已驗欄位，現況與目標入口同步更新。
剩餘未驗欄位、過長譯文、HD、影片與三平台新版交付保持原範圍。
沒有Issue、tag、Release或原版修改；本機套件仍為workplace驗收中間物。
收尾核對與Docker清理另附下方，之後依既有授權commit與push。

收尾核對PASS：605Go零skip、14來源、75GUI、300筆暫停事件、八次重播、
12組原版姓名游標逐像素及328檔正式資源清冊通過。
64筆工作清單與生成稿全等，1747個相對連結有效；三個既有歷史私用缺圖另列。
原版素材未被追蹤，工作根無root-owned檔或誤建.md目錄；本批修改與輸出皆1000:1000。
本專案Docker零殘留，未重建映像；dosgolem隔離副本乾淨、upstream推送DISABLED。
正式接線總收據formal-final-audit-r25.json為83e82c7d9edb30e296566cf4c3ac4683833fde62a40c1a56a15e94818fa79388。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：Noto數值透明外緣修正

仍命中本地化顯示語意隔離及文件職責路由，先比對現行正式GUI與只讀原版觀測。
城內百分比與左右數量的完整字形、原版字格及排版區皆存活；差異只在透明外緣。
規格052追加DRAFT證據與READY審查後，只在正式Noto重建中裁去透明外緣，
保留來源逐點檢查、字形、字級、基線、VGA與其他覆蓋擁有權守門。

私有26項測試及四語各1305像素的區內差異驗證通過。第一次完整回歸的舊背景反例
落在外緣，已改為字格內背景破壞，另加外緣接受案例；同容器乾淨重跑635Go、
go vet及建置通過，零skip／fail。初次像素腳本未補DAC低位元，修正為既定
六位元展開公式後，同容器同輸入乾淨重跑通過；兩項皆未當作產品缺陷。

正式啟動器新50組五語GUI與200筆暫停交易通過，含改名刪字、重打、取消及正常存檔。
四語十二個數值欄位皆符合19／27／27px與原版排版矩形；英文逐像素原版相同。
42筆實際DOS輸入四側重播至103600000步，完整CPU、RAM、VGA、DAC、WAV與存檔一致。
已抹除舊年份未復活，離城不留數字。635Go來源與十四筆組裝綁定吻合；
本機正式套件328檔資源逐檔等於前輪，只有二進位更新。
GUI限2GiB，GOMEMLIMIT=1200MiB，峰值1943334912 bytes。

另完成城名只讀稽核：201點字形與原版墨跡區完整，20點差異全在墨跡外，
日文17px只是私有排版容量。來源時序與alpha相交待驗，正式城名守門未改；
證據追加規格038的DRAFT，不算城名或完整五語完成。規格052透明外緣附記限定CONFORMED，
CONTEXT、目標入口、規格060與機器清單同步更新，WORKLIST由JSON重生。

本輪沒有修改原版、dosgolem、Issue、tag、Release或交付版。證據、原版像素與本機套件
只留workplace；收尾稽核與Docker清理另附下方，commit／push依使用者既有授權執行。

收尾PASS_FORMAL_R26_FINAL_AUDIT，指紋873fc724b9aa73df87c949cc12b5f0ffebf742fe62e8497f350894121b3ae357。
十四筆來源綁定、64項機器清單、1759個有效相對連結及原版素材版控邊界吻合；
三個歷史私用截圖缺檔維持既有紀錄。沒有root-owned檔案或誤建.md目錄，擁有權正確。
dosgolem隔離副本乾淨且upstream推送仍為DISABLED。Docker專案容器零個，沒有重建映像。

## 2026-10-12：四語完整城名正式接線

沿本地化顯示語意隔離及文件職責路由，接續前輪地圖城名的20點安全區差異。
只讀alpha與有界寫入追蹤確認32次後畫寫入，原版201點字形及整個墨跡區仍完整。
規格038追加DRAFT；私有v1只放行日文，其他三語被正文遮擋守門拒絕。
量測完整文案後，確認舊CJK參考字使三語正文高出1輸出像素；
四語依實際alpha對齊原版填色上緣，保留完整雙語名、中心及既定寬度上限。

候選41項來源／遮擋與完整字形測試、全部676Go零skip、go vet及建置通過。
四語固定正常畫面保留全部20點後畫內容，只裁相交黑色描邊。
私有50組GUI及本次實際輸入四側重播至107800000步通過後審READY，
才套入正式來源。首輪重播的觀測側因正式語言包與舊探針旗標衝突拒絕啟動，
修正私有腳本後同容器乾淨重跑通過，未當作產品缺陷。

正式組裝31份Go來源及二進位與已驗候選完全相同，十四筆來源綁定通過。
新50組五語GUI、200筆暫停交易及八組世界／返回世界城名通過；
仍有後畫差異的三張GUI共60點逐點保留，另驗四語固定畫面的全部20點。
進城及改名取消沒有舊城名，返回世界重建正確，城內十二個數值欄位保留。
42筆本輪實際輸入四側重播至113400000步，完整CPU、RAM、VGA、DAC、WAV及存檔全等。
二進位329d56d6b1e7f85c4d3f2e9e4bfe6d7b10e82d8e47c13d39fd4e324beb9ad396；
限定審查7a5769e5810ae966b764b79ba440803cab59af867c07fd9f491ef54af85383a2。
328個語言資源逐檔等於前輪，沒有重烘固定字模。

GUI與重播皆設定2GiB容器上限及GOMEMLIMIT=1200MiB。
GUI記錄峰值2147487744 bytes，重播1675120640 bytes；重播oom及oom_kill皆為零。
規格038限定CONFORMED，CONTEXT、規格060、目標186及機器清單同步，
WORKLIST由JSON重生。完整五語、HD、影片與三平台新版交付仍未完成。

本輪沒有修改原版、dosgolem、Issue、tag、Release或交付版。
本機收據、畫面、音訊、存檔及套件只留workplace；腳本入口見規格038。
收尾稽核與Docker清理另附下方，commit／push依使用者既有授權執行。

收尾PASS_FORMAL_R27_FINAL_AUDIT，指紋f78e05673e9f6f5caf336aaa963f03f03bd1de177efdfa513bbbc94bf61ec1c3。
本機重跑與結果為map-source-padding-r27/final-audit.py及final-audit.json。
64項清單、1761個有效相對連結與版控邊界吻合，三個歷史私用截圖缺檔保持原紀錄。
find自檢沒有root-owned檔案或誤建.md目錄，所有修改檔UID/GID正確。
dosgolem副本乾淨且upstream推送仍為DISABLED。Docker專案容器零個，沒有重建映像。

## 2026-10-12：HD首座建築參數與兩次重畫

命中資產考古、IDA／16-bit DOS及文件職責路由，沿既有IDA9.4映像與
隔離dosgolem進行唯讀觀測。新IDA資料庫核對座標、畫布描述、來源記錄與retf 6；
原版完整來源及三次未裁切建築呼叫已確認，原始名稱與運算元保留。

新增可選參數與有界寫入順序觀測，正式前端未變。
兩次後續重畫各440點，繪前回到相同底圖，繪後與首次一致。
首次返回後2122筆寫入涵蓋621點，366筆為同值，完整順序可重建終點。
四組完整CPU、RAM、VGA、DAC相同，舊觀測及首批參數收據逐位元組相同；
Go建置與go vet通過，六項錯誤證據反例全拒絕。本輪未抽驗WAV。
來源、地址空間及完整指紋另追加RESEARCH-LOG，規格061保持DRAFT。

研究執行器曾因引號組裝錯誤在開始前停止，改用獨立Python檔後乾淨重跑。
r2的完成閘門提早返回，未取得後續呼叫；修正後r3取得兩次呼叫並重跑四組。
稽核首版要求返回附近碼完全相同，實際發現一byte差異；保留原始收據，
將成因列未知，參數、像素與寫入順序各自核對，不猜測程式用途。
一段唯讀查詢的括號筆誤修正後重跑，沒有當成原版缺陷。

CONTEXT與唯一工作清單更新為本次事實，WORKLIST由JSON生成。
正式HD素材、遮擋、離城、重進與HD合成仍待驗，完整五語及交付範圍不變。
沒有修改原版、dosgolem、Issue、tag或Release；原版快照與候選只留workplace。
收尾驗證、Docker清理及依既有授權commit／push接續記錄。

收尾核對PASS：四組完整原版狀態、兩次重畫與六項反例通過；14來源綁定、
19份同名公開Go來源及31份已測／正式Go模組全等，正式前端本輪未改。
64筆工作清單與生成稿全等，1772個相對連結有效，三個既有歷史私用缺圖另列。
原版素材未被追蹤，修改檔及研究輸出皆1000:1000，工作根無root-owned檔或誤建.md目錄。
收尾腳本初次把31個模組檔都視為同名公開檔，修正檔名對應核對後於同容器重跑通過。
專案Docker零殘留，未重建映像，隔離dosgolem乾淨且upstream推送DISABLED。
本機parameters-r3/final-audit.json為b7e9a57c74fc4e1aeebe520441cfa6437a5705c057679ccc77bf2ace452c2cc7。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12：HD正常GUI生命週期與游標透明來源

命中資產考古、IDA、正常GUI還原與文件職責路由，沿既有隔離工具鏈接續。
原版正式前端新55組真實X11檢查包含改名、取消、存檔、離城、重進及建築浮標。
53筆實際DOS輸入重播至134600000步；49個不同GUI檢查點及終點的CPU、完整RAM、
VGA、DAC與觀測、無觀測兩側一致，COLONY09與COLONY00相同。
右鍵仍是浮標，第一次Escape離城、第二次開啟退出確認；不誤稱建築對話框。

九次同來源重畫各440點，19463筆矩形寫入含5986筆同值，全部檢查點可逐筆重建。
游標緩衝區114次完整寫入共29184筆，全來自0B68:0547；新IDA資料庫唯一匹配
EA0x1AAC7，確認FF取背景的分支及256bytes來源。82個不透明點包含同背景色，
單靠畫面差分只能找到78至82點。五組建築內暫繪／還原配對互逆，沒有其他寫入交錯。
觀測直接讀RAM，不呼叫會載入VGA latch的硬體讀取。

先前離線原型整個撤掉游標矩形，已改為只對本次已驗的五組配對保留底層，
再將82點游標置頂。浮標遮擋161點，其餘460點保留；重進重建621點，
存檔、世界及退出確認均無HD殘留。原型對照已改為保持裁圖比例。
這些是原版GUI與離線合成，尚非HD執行期、五語分層或開關驗收。

使用內建imagegen技能，以原版小屋提取圖與定稿畫風生成v4候選。
原樣1158×1359、完整提示與來源指紋只留workplace；放回92×108原型抽驗通過。
v3及v4均未定正式素材，alpha量測不作美術通過門檻。
新增公開重生、稽核及IDA工具；go build與go vet通過，原版收據逐位元組相同，
六種錯誤證據全拒絕。正式前端及語言資源未改，不重跑未變更的676Go。

研究重播r1略過同一步輸入前的GUI檢查點；r2補丁未實際插入，兩次均提前停止。
重新查路由、確認捕捉順序後r3乾淨重跑通過，沒有當成原版缺陷。
離線稽核曾以exec啟動而缺__file__，改回同容器python3腳本入口乾淨重跑。
一次自動權限審查逾時未執行，依工具指示重試成功。
六反例已通過後的工作項目查詢誤用數字id，改依實際issue=63讀取；未重跑既有反例。

規格061保持DRAFT，CONTEXT、目標186與唯一工作清單同步，WORKLIST由JSON重生。
沒有修改原版、dosgolem、Issue、tag、Release或交付版；所有原版像素與新候選仍在本機。
收尾檢查與Docker清理接續記錄，commit／push沿使用者既有授權。

收尾PASS_HD_LIFECYCLE_R29_FINAL_AUDIT，指紋
55776d5d94cc00a4b61dfdbf832a16ece07c9950c342f9f45aecc228d6f5d203。
本機重生入口為hd-building032-draw-boundary-20261012/lifecycle-public-r29-r1/final-audit-v2.py。
14來源綁定、19份同名公開Go及31份已測／正式Go全等；64項工作清單重生相同。
1783個相對連結有效，三個歷史私用缺圖保持原紀錄，新增工具皆有目標及規格入口。
缺原版的兩個研究工具明示SKIP及77，原版素材與新候選未被追蹤。
工作根無root-owned檔或誤建.md目錄，修改與輸出皆1000:1000。
收尾腳本對反例來源連結誤用stat，改以lstat檢查輸出連結本身後同容器重跑通過。
隔離dosgolem乾淨且upstream推送DISABLED；專案Docker零殘留，未重建映像。
本批依既有授權提交並推送，提交號與結果以Git紀錄為準。

## 2026-10-12首座HD執行期與五語真視窗

從正式R27複製可丟棄前端，接入來源、幾何、實際寫入與逐點撤銷的HD原型。
正式14項來源綁定未改。49點原版重播、10次繪製、1050點游標還原與18反例通過；
676項既有Go零skip及go vet通過，33份已測Go來源有完整指紋。

152組正常五語原版／HD視窗通過，608筆設定事件保持CPU暫存器、完整RAM、VGA、
DAC與DOS輸入；3280點不透明游標逐4×4像素相同。
五語進城621點、浮標460點、百科與離城0點、關百科621點，切回原版沒有HD殘留。
67筆實際輸入四側重播至193000000步，完整原版狀態、WAV及存檔全同。
收據根為hd-runtime-r30-r2，完整雜湊及公開重生入口見規格061。

驗證腳本修正分開記錄：R1將游標未同步時的安全回退當成完整HD；補原因並保留原版回退。
R2因缺GOMEMLIMIT被容器OOM終止，Docker事件已確認；R3起沿既有1200MiB限制。
R3每次恢復後滑鼠離開建築，原版撤浮標，改為每次先正常重新懸停。
R4五語浮標全通過，但右鍵實際開啟百科，不能沿用R29只有浮標的場景假設。
核對PEDIA.TXT:@BUILDING32及畫面後，R5改依來源鍵等待百科、殖民地及世界，乾淨重跑通過。
一次檔案編輯定位未匹配，未變更檔案；核對原文後修正。
以上為原型回退、環境或驗證腳本分類，沒有補改原版規則。

規格061保持DRAFT。下一步審正式素材及缺件／保存HD偏好的回退，再接正式建置。
地形、人物、其他建築、動畫、完整五語、影片與新版三平台交付仍未完成。
v4與所有原版像素只留本機，沒有新增原版衍生圖入Git。
沒有改dosgolem、Issue、tag、Release或發行版；收尾稽核與Docker清理接續記錄。

收尾PASS_HD_RUNTIME_R30_FINAL_AUDIT，指紋
777e655ecca557a91cf6d9702b0477efce0c18682faff633b2022d734c1efc1e。
本機入口為hd-runtime-r30-r2/final-audit-r30.py，兩個GUI／重播探針重生逐位元組相同。
33份已測來源、14正式綁定及五份公開研究工具均已核對，正式二進位不變。
64項工作清單重生全等；產生器不顯示verify.note，所以WORKLIST內容沒有差異。
稽核曾混用既有328資源紀錄與formal-bundle/languages的325實檔口徑，改以實際目錄計數；
沒有重烘或改寫語言包。所有新增工具均有目標186及規格061入口，相對連結沒有新增缺件。
工作根無root-owned檔或誤建.md目錄，修改及輸出為1000:1000。
隔離dosgolem乾淨、upstream推送DISABLED，專案Docker零殘留，沒有重建映像。
本批沿既有授權commit與push，Git紀錄為提交號及遠端結果的來源。

## 2026-10-12 首座HD正式接線開工

路由命中規格閘門與專案文件職責，沿已載入入口。新增graphics作正式生成圖像來源；text與font各有文字與字型職責，docs/screenshots是參考圖，workplace可刪除，均不能承擔正式圖像來源。入口為規格061及目標186，採已驗v4原始位元組及既定畫風。原版參考圖與解碼像素留本機。規格061經來源、寫入、遮擋、游標與R30正常GUI／四側重播審查，限定READY於第032幀固定位置，不擴張其他素材。

### 正式接線與驗收

正式HD來源、啟動回退及封裝白名單完成，規格061由限定READY經正式驗收至限定CONFORMED。685Go零skip及go vet、152組五語原版／HD真X11、608筆設定事件、3280點不透明游標通過；65筆實際DOS輸入四側重播至205400000步，完整原版狀態、WAV及存檔全同。五個缺件／恢復新行程及五個封裝反例通過。正常路徑包含改名取消、存檔、重進、浮標、百科與離城；目視繁中浮標及韓文返回殖民地。正式建置16項來源綁定與33份Go有完整指紋，已發布版及dosgolem未改。

來源轉換曾有函式定位與語法錯誤，在正式建置前修正。核心與封裝稽核初次把Windows續行當成相鄰參數缺失，修正解析後同容器重跑成功。啟動R1遇X11命令逾時，無Docker OOM，成因未知；保留收據並補探針有界清理。R2已確認缺件回退及偏好不變，但探針把Escape事件誤寫為cancel，實際是cancel-escape；修正後R3五情境通過。產品碼未據此調參數。

路由再核對規格閘門，限定完成範圍只計本建築固定位置。CONTEXT與Issue #63 note回填；WORKLIST依JSON重生，其他工作項目及發布版本不變。各批Docker均--rm、有界Xvfb與UID1000；作業完成後檢查無殘留，最終稽核另記本機final-audit.json。

最終來源稽核發現生成PNG被既有全域*.png規則忽略，已僅對graphics/building-032.png加入版控例外；重新核對完整來源與素材後提交。

## 2026-10-12 海洋來源與暫存畫布研究

路由命中逆向工程、規格閘門與文件職責，載入既有入口及逆向工程技能；生成候選另使用imagegen技能。
新增規格062保持DRAFT，首座建築限定CONFORMED及已發布版不變。
PHYS0.SS第148幀完整263bytes唯一，293次正常輸入繪製全部寫256點並正常返回。
海洋先畫到0x3C500暫存畫布，再由0CBA:00CA轉送到0x2CAE0主畫布，不能套用建築畫布假設。
兩側重播至75900000步，世界及城內完整RAM、CPU、VGA、DAC與兩張畫布相同。
世界131次繪製保留32867點，108個完整矩形與既有定位相同，進城後主畫布0點。
八種證據反例拒絕，缺原版SKIP 77及錯來源建立輸出前拒絕通過。

內建imagegen依定稿畫風生成兩張海洋候選，v2降低對比與密度，完整提示及原始位元組只留本機。
私用64×64圖塊合成只替換525872像素，遮罩外原版全等；目視3×3重複與實際地圖。
本輪未接正式HD，未驗新HD GUI、游標還原、動畫、音訊或即時效能。正式685Go驗收沿用，未重跑未變程式。

研究環境問題另記：首次掛載前檢查發現交接摘要的cache縮寫路徑不存在，未啟動容器或建立錯目錄，
改用既有display-phrases-20261011/go-cache。gofmt -w需在唯讀父目錄建立暫存檔，改由stdout寫回單一可寫來源。
首輪嚴格要求建築畫布，正確拒絕全部293次海洋幾何；後續依原始描述指標追暫存畫布，保留首輪收據。
兩次編輯定位未匹配，均未寫入；核對實際檔案後修正。未當成遊戲缺陷或猜補正式規則。
重生入口及雜湊見規格062；CONTEXT及唯一工作清單更新，WORKLIST由JSON生成。
原版、dosgolem、Issue、tag、Release與交付包未變。Docker及最後來源稽核接續記錄。

收尾PASS_SEA_R32_FINAL_SOURCE_AND_HYGIENE_AUDIT，指紋219ce5b8135a4d8202d5f395333e9598ee0f685d3a0c320cbc4bd5628f902bb0。
八份公開變更皆1000:1000，新增規格及兩個研究工具均有入口，64項工作清單只有#63 note變動。
WORKLIST初次render只印出內容，後改用write重生；因產生器不含note，內容維持相同。
正式前端與上一批二進位不變，隔離dosgolem乾淨且upstream推送DISABLED。
全工作根無root-owned檔或誤建.md目錄，專案Docker零殘留，未重建映像。
本批沿既有授權commit與push，提交號及遠端結果以Git紀錄為準。

## 2026-10-12 海洋即時隔離原型與同輸入驗證

沿已載入的逆向工程、規格閘門及文件職責路由，新增五份研究工具並由規格062與目標186索引。
只修改正式前端的可丟棄副本；海洋仍DRAFT，正式首座、原版、dosgolem與發行包未改。
公開組裝器乾淨重生與GUI相同的二進位，686Go零skip、go vet及23種來源／覆寫／游標反例通過。
另驗缺原版明確skip，未把該次算為通過。53筆正常輸入至134600000步的49點完整狀態及存檔全同；
571次海洋繪製與23040點游標繪製／還原通過。

182組真X11五語原版／HD切換、728筆暫停事件及6642點不透明游標通過。
75筆實際輸入四側重播至220400000步，完整CPU、RAM、VGA、DAC、WAV及存檔相同。
公開GUI及重播產生器逐位元組重生已驗工具，完整雜湊及重生入口見規格062。
目視韓文HD海面與英文原版；存檔返回後仍有部分原圖回退，岸線、其他還原鏈、裁切、動畫及效能待驗。
沒有把隔離prototype_entry或綠色Go測試登錄為正式海洋／完整HD完成。

環境與驗證工具問題保留原收據：測試R1的登入shell重設Go PATH，改bash -c後同映像乾淨重跑。
GUI首次產生器的定位字串未匹配，核對既有來源後修正。重播R1錯用HD終點，
實際GUI已切回原版；R2誤把海洋參數放進未啟用HD的純觀測分支，啟動正確拒絕。
R3沿實際終點設定及既有觀測契約通過，沒有為此改產品行為。
公開組裝器起初多一空行，來源行號造成二進位差異；移除後逐位元組全等，R6完整重驗通過。

CONTEXT與#63 note更新，WORKLIST依JSON重生；Issue、tag、Release及交付包未變。
各批Docker均UID1000、無網路、資源及逾時有界，Xvfb有trap；收尾確認專案容器零殘留，未重建映像。
公開變更擁有權、原版素材版控及文件入口由本機final-audit.json核對；沿既有授權commit及push，遠端結果以Git紀錄為準。

## 2026-10-12 海洋背景保存與還原

路由沿逆向工程技能、規格閘門及文件職責，先追查存檔返回的原圖回退。
唯讀追蹤確認0CBA:00CA三組保存／還原及同一RAM緩衝重用；466列共34294點雙向來源，
49點完整原版狀態保持一致。隔離原型按實際逐byte來源延伸，不以色號或矩形補畫。
686Go零skip、go vet、31反例與缺原版另驗skip通過，49點來源數量亦與獨立觀測相同。
存檔返回恢復33123點，比R33增加12826點；進城仍0點。

182組五語真GUI、728筆暫停事件及6560點不透明游標通過；
海面三位置逐語實際懸停、移動與返回，返回遮罩相同。
117筆實際輸入四側重播至267800000步，完整CPU、RAM、VGA、DAC、WAV及存檔一致。
本次HD守門回退1組，不計為持續覆蓋；首輪城名回退另以受控重播驗恢復。
完整指紋與重生入口由規格062背景還原附記索引。

探針與驗證問題分開記錄：兩次列追蹤混入無關複製達上限，
核對dosgolem REP整列一步後縮窄為帶海洋來源的列，沒有提高上限。
首輪GUI城名回退以相同18筆輸入決定性重現，確認原版安全區20點主畫布／VGA不一致；
腳本加入既有來源守門、原圖回退及恢復驗證。第二輪切場items=null造成TypeError，
改等待條件空值處理後同映像及相同流程乾淨重跑。
重跑包裝器一次仍引用舊腳本，已修正並加輸出防覆寫；R2外層啟動日誌被該次覆寫，
R2原始事件、畫面、存檔及行程日誌保留，TypeError出處保留於本輪工具輸出及本紀錄。
最初唯讀命令自動審核逾時而未執行，縮短同範圍命令後通過。

CONTEXT及唯一工作清單#63 note更新，WORKLIST由JSON重生；未改Issue、tag、Release或交付包。
海洋保持DRAFT；正式首座、原版及dosgolem未改。岸線、其他還原鏈、裁切、動畫與效能待驗。
各批Docker均UID1000、無網路、資源與逾時有界，Xvfb有trap；
收尾原始收據、來源、擁有權與工作根衛生由本機final-audit.json核對，專案容器清理另核對。
沿既有授權commit及push，提交號及遠端結果以Git紀錄為準。

## 2026-10-13海洋正式接線與缺件契約

路由載入逆向工程技能、imagegen技能、規格閘門與文件職責；首頁摘要另核對README規則。
先量測候選與原版海洋色差，內建imagegen沿定稿風格生成v3，只調整自己的v2色盤及對比。
原始1254×1254 RGB原樣保存，私用遮罩外原版全等，目視3×3與地圖。
規格062完成限定READY審查後，新增正式海洋來源／測試、清冊及單檔Git例外，
接入原HD組裝與三檔封裝白名單；缺海洋或錯來源沿原偏好不變及整組原版回退。
首座原圖與幾何不變；七個海洋方法及49點來源資料與R34相同。

692Go零skip、go vet、31反例、49點原版完整狀態與存檔通過，缺原版另驗skip。
182組正式五語GUI、728筆暫停事件與6560點不透明游標通過；
121筆實際輸入四側重播至286400000步，完整CPU、RAM、VGA、DAC、WAV及存檔全同。
八種新行程守門／恢復的39筆事件與原HD偏好不變，八項封裝拒絕通過。
一組來源暫態回原圖，獨立記錄而不當成持續覆蓋。合成五次中位數與環境寫入規格062。

來源產生器首次未匹配識別字大小寫，核對後完成，未改原版語意。
正式重播產生器驗出未執行分支仍留原型參數，移除後重生通過；
歷史GUI及重播內容仍逐位元組相同。未為驗證調整產品規則、來源守門或測試種子。
規格062限定CONFORMED，CONTEXT、唯一清單#63 note及首頁穩定摘要更新，WORKLIST由JSON產生。
其他海岸／地形、裁切、動畫、跨平台效能、完整五語與HD、新版交付仍未完成。

完整命令與證據由本機commands-r35.json及規格062索引，原版比較圖、音訊及存檔只留本機。
各批Docker均UID1000、資源與逾時有界、無網路；Xvfb有trap，收尾核對專案容器零殘留。
來源、擁有權、原始素材版控及清冊由audit-r35.py／final-audit.json核對；未重建映像或發行包。
沿既有授權commit及push，提交號與遠端狀態以Git紀錄為準。

## 2026-10-13人物來源的正常路徑研究

路由命中HD資產、規格與文件職責，載入逆向工程及imagegen技能。
從既有完整像素定位選取ICONS.SS第100幀，建立規格063 DRAFT及索引，不推定職業。
公開唯讀人物探針與獨立來源檢查器加入同一規格入口，沒有接入正式組裝器。
固定來源解碼後，先沿較短正常輸入驗四次來源，再沿R29的53筆輸入驗完整13次繪製。
49點原版完整狀態及存檔相同，4545筆矩形寫入獨立重建；15個錯誤證據拒絕及缺原版77通過。

兩次imagegen候選皆有光暈，原樣及完整提示保存在hd-person-r36，未公開或採用。
沒有以alpha門檻或腳本改圖掩蓋生成問題，也未切換CLI／API。
規格保持DRAFT；下一步是人物直接懸停、游標還原、拖曳與合格素材。
CONTEXT及唯一清單#63 note更新，WORKLIST由JSON產生；README、正式來源、tag及Release未改。

工具問題：兩次搜尋在測試檔找鍵盤分支未命中，改沿實際applyWindowInput定義查證。
一次文件補丁定位不符，整批未寫入，修正定位後完成。
CLI反例首輪因前一步還原了正向像素而執行正常重播，不能當拒絕通過；
保留should-not-exist輸出，修正測資設定順序後以新的r2輸出在同一映像乾淨重跑。
新增返回暫存器後也重新編譯及重生R2收據，未改原版或判定規則。

各批Docker均UID1000、無網路、資源／逾時有界；本輪沒有背景GUI或新映像。
收尾來源、候選、原始素材版控、擁有權與文件由audit-r36-r2.py／final-audit-r2.json核對，
專案容器零殘留另核對。沿既有授權commit及push，提交與遠端結果以Git紀錄為準。

## 2026-10-13 人物v2確認、隔離接線與游標還原 R37

- 使用者要求關閉預覽，確認v2效果可接受並要求依此方式HD化。原圖與alpha原樣採用，
  沒有重新開啟美術選擇。桌面已無候選圖視窗；焦點防護阻止操作其他專案。
- 新增人物隔離顯示層、真實原版測試及五個可重現組裝／驗證入口，索引在規格063。
  正式建置、啟動器、graphics清冊與已發布版保持原狀。
- 首輪GUI發現人物游標配對會被外圍背景還原清除。修正為保存全部已驗游標區域的配對，
  只有原先有來源且舊／新值反向一致的點恢復人物。獨立驗證器拒絕修正前的真實收據。
- 修正後693Go零skip及go vet通過，49點原版狀態／存檔相同，17個人物反例全拒絕。
  正常五語GUI通過252組切換、1008筆原子設定事件與9348個不透明游標像素。
- 獨立原版探針重生78次人物繪製、35418筆事件與2370個人物游標還原點。
  10張懸停／移開／返回／按住拖曳／放開收據的完整RAM／CPU／VGA／DAC相同，
  全部維持120個有效人物來源；沒有接受背景RAM轉送。
- 修正後235筆實際GUI輸入四側重播至455400000步，完整原版狀態、WAV與兩個存檔全同。
  觀測側曾誤帶依賴即時HD的原型旗標，分類為腳本問題；修正後同一容器環境乾淨重跑。
  重跑誤用既有輸出亦保留為歷史失敗，不列產品缺陷。
- 規格063完成限定READY審查。接續正式載入、封裝白名單、缺件回退與正常GUI驗收；
  其他人物、動畫、完整HD、完整五語與新版交付沒有增加完成信用。
- 本機證據根：workplace/reports/goal186-display-hd/hd-person-live-r37。
  修正後收據在public-r2；commands-r37.json索引實際Docker命令，
  final-audit-r37.json保存來源、測試、權利邊界與擁有權稽核。
- Git提交範圍為程式、規格與現況文件；沿用既有commit／push授權。
  原版像素、參考圖、生成候選、RAM、WAV、存檔與私有收據不提交。
  Docker工作均非root、無網路且有界；本輪人物容器已清空，輸出沒有root檔案或誤建的md目錄。

## 2026-10-13 第100幀人物正式HD接線 R38

- R37已提交並推送cacbf3e，遠端main與本機一致後，依規格063 READY接續正式實作。
- 新增人物正式來源與測試，綁定ICONS.SS指紋及已確認v2原圖。
  PNG原樣加入graphics；清冊記錄完整提示、參考指紋與使用者確認，原版參考不提交。
- 正式組裝共37個Go檔與20個來源綁定。既有啟動器沿同一HD目錄載入，
  封裝白名單增加person-100.png；正常入口沒有新增人物原型或診斷旗標。
- 五個人物來源方法與R37相同。699Go零skip、go vet、49點原版狀態／存檔、
  17人物及31海洋反例通過；缺原版另驗兩個明確skip。
- 正式GUI通過252組五語原版／HD切換、1008筆設定事件與9512個不透明游標像素，
  本批沒有HD守門回退。75組城內HD皆120點有效人物來源，
  其中92點含原圖alpha而實際合成；其餘保持原畫面。51組其他畫面人物0點。
- 229筆實際GUI輸入四側重播至458200000步，完整CPU／RAM／VGA／DAC、WAV與存檔全同。
  原始資料、正常懸停／移開／返回、按住拖曳／放開、存檔及重進均在抽樣範圍內。
- 11種新行程缺件／錯件／連結與恢復測試通過，54筆暫停設定事件不改原版，
  原日文HD偏好位元組不變；11項封裝反例全拒絕。
- 規格063限定CONFORMED。依知識路由重查規格閘門、文件職責與README標準，
  同步唯一現況表及工作清單。GitHub Issue #63唯讀核對仍OPEN，不變更Issue。
- 素材安裝初次建立工作目錄時曾把報告父目錄掛為可寫；後續改為只掛本輪輸出。
  收尾核對前輪原圖、原版參考與已知來源指紋未變。
- 本機證據根：workplace/reports/goal186-display-hd/hd-person-formal-r38。
  commands-r38.json索引實際Docker命令，final-audit-r38.json保存來源、權利、驗收與擁有權稽核。
  本輪只提交程式、生成PNG、清冊與文件；原版、RAM、WAV、存檔及私有收據不提交。
- 沿既有commit／push授權提交本輪變更。其他人物、動畫、跨平台效能與完整HD待續；
  不建立tag、Release或新版交付包，已發布v.1.0.3-20261010不變。
- 收尾稽核通過；本輪人物容器已清空，輸出擁有權皆1000:1000，沒有root檔案或誤建的md目錄。

## 2026-10-13 城內十種建築來源與木棚候選 R39

- 人物正式接線ee3f6fb已推送；依使用者連續go接續既定HD範圍。
  重查復古遊戲路由，載入規格閘門與文件職責；沿用imagegen技能及已確認畫風。
- 新增規格064 DRAFT、批次唯讀探針與獨立檢查器，不改正式建置、資料格式或原版行為。
  十種BUILDING.SS來源在正常路徑命中130次完整繪製，涵蓋13個位置。
- 獨立重建344060筆矩形寫入及130筆完成事件，原始底圖、透明處、返回與來源撤除通過。
  新見0D46:0181寫入端及第043幀被後畫遮住的實例，原始定位與推論等級在規格064。
- 53筆實際GUI輸入重播至134600000步，49點完整CPU／RAM／VGA／DAC、終點及兩個存檔
  與無觀測對照相符。21項錯誤證據拒絕，缺原版另驗exit77；go build與go vet通過。
- 內建imagegen依原版第024幀實際調色盤及已定稿畫風生成木棚候選，1158×1359 RGBA原圖原樣保存。
  完整提示、參考指紋、alpha及權利分類留本機。離線合成只在263個來源點內，範圍外零變動。
  已目視原版／候選對照，比例、位置與透明空隙保持；尚未接入即時前端或驗新游標還原。
- 檢查器首次輸出別名位於唯讀掛載，所有檢查通過後寫收據失敗；分類為容器命令問題。
  修正為本輪輸出目錄的精確可寫別名後，同一映像與命令乾淨重跑通過，不列產品缺陷。
- 提交前修正兩個新檔尾端空白行；保存原始檢查器，重新產生R2來源及反例收據，
  讓公開程式與收據精確綁定。R1及候選的原始來源綁定保留。
  歷史連結的外部IDA README已確認存在，另以唯讀掛載補足稽核容器的可見路徑。
- 本機證據根：workplace/reports/goal186-display-hd/hd-building-batch-r39。
  commands-r39.json保存容器與生成入口，final-audit-r39.json保存收尾稽核。
  沿既有commit／push授權提交程式、規格與現況；原版、候選、合成圖、寫入事件與存檔不提交。
- 規格064維持DRAFT。下一步是木棚隔離顯示與正常GUI驗證；其餘生成素材、動畫與正式接線待續。
  已發布版、正式三種HD來源與完整HD完成數不變；不建立tag、Release或交付包。
- Docker均無網路、非root且有界，原版及研究輸入唯讀；本輪容器已清空，輸出皆1000:1000，
  沒有root檔案或誤建的md目錄。

## 2026-10-13 木棚隔離顯示、正常游標與READY R40

- R39已提交推送8b4a7ac；依連續go接續既定HD範圍。重查規格閘門及文件職責，
  沿R39木棚原圖與alpha，不重新生成或變更畫風。
- 新增木棚隔離來源、原版路徑測試及五個組裝／獨立稽核入口，統一索引在規格064。
  正式20個來源綁定、三種圖像、啟動器、封裝器與已發布版未改。
- 700Go零skip、go vet、49點完整原版狀態／存檔及20來源反例通過；缺原版另驗一個明確skip。
  322組正常五語原版／HD、1288筆設定事件與12218個不透明游標像素通過。
  屋頂、柱身、空白區按住拖曳、改名／刪字／取消、存檔、重進、百科與離城均有正常輸入。
- 獨立重建71次木棚繪製、85899筆矩形寫入及768筆游標來源寫入，
  加初始游標共86739事件。十個原版GUI點完整狀態相符，6222個正常游標還原點有原始配對。
  17項錯誤來源、游標切換、語言與回退圖像反例全拒絕。
- GUI兩組來源守門回原圖，另兩張未知拖曳游標診斷亦回原圖，均保留語言。
  未知游標不加入白名單，兩張完整游標矩形8192個輸出點保持原版，放開後HD恢復。
  336筆實際輸入四側重播至609400000步，完整CPU／RAM／VGA／DAC、WAV及存檔全同。
- 首輪GUI重複點人物，觸發原版職業選單；新增流程亦超過舊五億步視窗上限。
  改為空白區拖曳、保留既有人物操作一次，使用九億步有界上限，同一映像及同一二進位乾淨重跑通過。
- 原版MOV反例的全新Machine副本未帶計時器狀態，Machine.Step先送IRQ，造成假失敗。
  查既有CPU API後只以CPU.Step執行單一MOV；測試修正後全套通過，前端二進位未變。
- 首版獨立檢查器假定十張都用一般游標，因未知拖曳游標拒絕。
  補記初始256bytes及768筆游標來源寫入，維持未知來源回退；核對原圖、語言及完整游標後通過。
  沒有猜補未知游標或背景RAM轉送，失敗收據保留，不列產品缺陷。
- 規格064限第024幀READY，其他九種維持DRAFT；下一步正式載入、封裝與缺件驗收。
  更新CONTEXT、目標186及唯一工作清單，WORKLIST由JSON重生；沒有新增正式HD信用。
- 本機根hd-building024-live-r40；commands-r40.json索引實際命令，final-audit-r40.json保存收尾稽核。
  沿既有commit／push授權提交程式與文件，原版、候選、RAM、WAV、存檔及私有收據不提交。
  不建立tag、Release或交付包，v.1.0.3-20261010不變。
- Docker均無網路、UID1000、資源與逾時有界，原版及前輪收據唯讀，Xvfb有trap。
  收尾核對來源、擁有權及容器清理，沒有root輸出或誤建的md目錄。

## 2026-10-13 木棚第024幀正式HD接線 R41

- R40已提交推送de0525a；沿既有正式接線授權及規格064 READY繼續。
  重查規格閘門、文件職責與README標準，不變更既定畫風或原版行為。
- 原始木棚PNG與alpha原樣加入graphics，清冊保留完整提示與參考指紋，原版參考不公開。
  新增正式來源與原版測試，接入39Go檔／22來源綁定、既有啟動器與五檔封裝白名單。
  五個木棚來源方法與R40相同，正常入口沒有原型或木棚診斷旗標。
- 703Go零skip、go vet、49點完整原版狀態／存檔及20木棚／17人物／31海洋反例通過。
  木棚來源、局部位移及游標統計與R40一致；缺原版另驗三個明確skip。
- 322組五語GUI、1288筆設定事件及12218個不透明游標像素通過。
  正常懸停、移開、返回、按住拖曳／放開、改名／刪字／取消、存檔與重進、百科及離城均有實際輸入。
  108組HD木棚263點有效、204區塊含alpha，51組木棚0點，另兩組來源守門回原圖。
  十筆狀態抽樣另有四筆來源守門，首筆仍為原版模式；分開記錄，不宣稱零回退。
  拖曳來源不符回原圖並保留繁中，放開後HD恢復，未接受新游標或背景RAM轉送。
- 332筆實際GUI輸入四側重播至604200000步，完整CPU／RAM／VGA／DAC、WAV及存檔全同。
  14種新行程缺件／錯件／連結與恢復通過，69筆設定事件不改原版，原日文HD偏好位元組保持；
  14項封裝反例全拒絕。目視正式繁中城內木棚，比例、位置與透明空隙符合來源範圍。
- GUI產生器兩次縮排定位不完整；重查實際生成來源的12格縮排後修正。
  同一映像、新輸出路徑重生通過，原失敗腳本與基底保留；沒有因此調整正式產品行為。
  正式與歷史隔離GUI／重播共四個產生結果逐位元組全等。
- 規格064限木棚024 CONFORMED，其他九種DRAFT；同步CONTEXT、目標186、首頁摘要及唯一清單。
  WORKLIST由JSON重生，Issue #63保持OPEN，沒有修改遠端Issue。
- 本機根hd-building024-formal-r41，commands-r41.json索引容器命令，final-audit-r41.json保存收尾稽核。
  沿既有commit／push授權提交程式、生成木棚、清冊與文件；原版、RAM、WAV、存檔及私有收據不提交。
  其他素材、動畫、跨平台效能與完整HD待續；不建立tag、Release或新版交付包。
- Docker均UID1000、無網路、資源與逾時有界，原版及前輪證據唯讀，Xvfb有trap。
  收尾核對本輪容器零殘留、輸出1000:1000，沒有root檔案或誤建的md目錄。


## 2026-10-14 R42九來源隔離顯示與驗證接續

- 沿目標186及規格064，為第016、021、027、035、039、042、043、044及045幀生成九張素材。
  沿已定稿精細像素風，原圖及alpha原樣留本機；兩張未採用修正候選及完整提示保留。
  透明外緣造成完整畫布取樣比例不合，改以逐幀量測的內容座標對齊原版不透明範圍。
  alpha至少128只用於幾何定位；合成仍使用原圖RGBA，不改PNG或alpha。
- 原版120次完整繪製、387259筆事件、49點CPU／RAM／VGA／DAC與存檔相符。
  獨立模型驗480筆一般游標還原，背景RAM只記錄，接受的RAM還原為0。
  隔離原型704Go零skip、180個逐來源反例、23個獨立證據反例及缺原版明確skip通過。
  完整回歸首次受記憶體限制終止，加入Go記憶體上限後，同工具鏈乾淨重跑通過。
- 首輪422組GUI未滿足首座韓文正向懸停；第二輪432組未滿足第045幀英文正向樣本。
  暫停可能落在原版重畫中，兩輪安全範圍均通過，但整體GUI均未通過。
  首輪失敗收尾缺少完整軌跡，保留失敗；第二輪完整軌跡已保存。
  第三輪保留432組切換，另驗45個正常關閉後恢復畫面及共72個原版快照。
  新隔離診斷增加語言／來源／HD恢復條件，41個執行期及測試來源完全不變。
- 原版探針沿用的100萬筆事件上限不足，改成串流標準JSON陣列及800萬筆有界上限。
  以舊387259筆與新緊湊格式逐項核對，八個格式／截斷反例通過。
  原版首輪27點另跑1848次來源與3065162事件，與控制終點相符；整體GUI仍不計通過。
  證據反例首次選到尚未追蹤的舊值，改定位到實際來源繪製內，同一組23反例乾淨通過。
- 九種共同合成的正常城內畫面已目視。正式四種素材、規則、輸入與存檔保持。
  規格064九來源仍DRAFT；正常恢復、72點獨立審查、四側重播及正式接線接續中。
  Issue #63唯讀確認仍OPEN；沒有修改遠端Issue、tag、Release或新版交付包。
- 本checkpoint的Docker驗證仍在有界容器執行，全部UID1000、無網路，原版及前輪證據唯讀。
  GUI的完整診斷曾量到1.45GiB，第二輪提高單一容器上限至4GiB，第三輪從4GiB啟動。
  本機根hd-building-nine-r42；本輪收尾時再核對容器、所有權、正式接線及文件狀態。
- 追加checkpoint：第二輪27個正常快照已獨立核對2004次來源與15134筆實際游標還原。
  第三輪正常恢復已命中，但讀到尚未寫完的JSON而中止。改等請求標記移除後再讀，
  同一10456799二進位重跑中；原版與41個非診斷來源保持。
  檢查器原先錯假設原版每點另存memory及pal檔，改核對實際完整RAM指紋與palette檔名。
  相同真實收據重跑通過；原版hash涵蓋完整RAM，沒有改成局部比較。
  DRAFT提交前稽核確認正式四素材／22來源、八個新工具入口、工作清單及原版素材未追蹤。

## 2026-10-14 R42九來源驗證完成與READY

規格064九來源限定READY，尚未正式接線。704Go零skip、180逐來源反例、23獨立證據／8串流格式／8報告讀取反例通過。正常GUI R5的432組切換、1728設定事件、45關閉後恢復與共72點完整原版狀態通過；2244次來源、3716863原始事件及15340游標配對已獨立核對。590筆實際輸入四側重播至943800000步，完整CPU／RAM／VGA／DAC、WAV與存檔全同。設定有一組安全回退；木棚放開後139點保守保留，正常重進城恢復263點。下一步正式九素材、來源與缺件／封裝反例，其他HD及交付待續。本機根hd-building-nine-r42。

前輪失敗保留，R5才授予完整GUI信用。JSON讀取等診斷標記移除；大檔事件與SHA串流，原版state以有界末端讀取。原版及來源接受規則不變。正式素材仍四種；九張生成原圖及原版參考此刻留本機。

精確收據、取樣契約與SHA由規格064索引。Docker均非root、無網路、有界且原版唯讀；本批容器已清空，輸出1000:1000，無root檔案或誤建md目錄。沿已授權commit／push接續正式接線，不修改Issue、tag、Release或dist-all。

## 2026-10-14 R43九來源正式HD接線

規格064九來源已正式接線並限定CONFORMED，合計十三種HD素材／14檔。41Go檔／24來源綁定、731Go零skip、go vet、49點完整原版狀態／存檔、180來源反例與既有31海洋／17人物／20木棚反例通過；九來源五個方法與R42相同。432組五語GUI、1728設定事件、16810不透明游標像素及45個正常關閉後恢復通過。586筆實際輸入四側重播至924600000步，完整CPU／RAM／VGA／DAC、WAV與存檔全同。41種新行程缺件／恢復及41項封裝拒絕通過，204筆設定事件不改原版，原日文HD偏好不變。設定有一組日文城內安全回退；木棚放開後139點保守保留，正常重進城恢復263點。證據根hd-building-nine-formal-r43。中央009候選與來源研究接續R44 DRAFT，其他地形、人物、動畫、跨平台效能與完整HD未完成；沒有新發行。

原圖及alpha原樣加入graphics，來源與封裝指紋由規格064索引。正常GUI不含原型旗標，原型產生器輸出另驗不變。正式72筆為現況診斷，獨立原版來源沿R42；不冒稱新增72點逐寫收據。原版參考、RAM、WAV、存檔與私有收據不提交。

重查規格閘門、文件職責及README標準；沿既有commit／push授權提交。Docker均非root、無網路、有界且原版唯讀，Xvfb有trap；收尾稽核本批容器已清空，輸出1000:1000，無root檔案或md目錄。R44唯讀入口清冊及中央候選留本機接續，不修改Issue、tag、Release或dist-all。

## 2026-10-14 R44中央第009幀隔離原型接續

中央第009幀仍為DRAFT，正式十三種素材保持。完整1254bytes來源、十次1095點繪製與49點原版狀態／存檔已驗；732Go零skip、20個中央來源及20個獨立證據反例通過。R2已保存14點，29次來源、149129事件及3448筆實際游標還原已獨立核對，圖像與文字安全範圍外零變動；前九張為原版模式，五張為正常HD恢復，不冒稱全14張HD。整體GUI在百科右鍵步驟失敗，僅410組成功前綴，不計整體通過。原版對照證實同一步移入與右鍵會被忽略，等懸停後成功開百科；只修驗證腳本。R3以同一二進位重跑452組，14張均要求正常HD；四側重播及正式接線待續。本機根hd-city-source-catalog-r44。

原版VICEROY.EXE及BUILDING.SS指紋沿規格064；BDARK.SS為3af438d23db8331eb6fe2268207fbece082775f3f7b68fb998cebc439d0b9402。88個非空來源唯讀清冊及2005次入口核對後，中央來源唯一匹配BUILDING.SS第009幀；不由外觀選BDARK。來源5C4D:000F、紀錄4F22:A772、目的[87,11,140,48)，MADSPACK part3位移10617與長1254分開記錄。完整局部位移／色號指紋80e2c7b872906ce4fc27a12926b6a9be2a77c90f75c509f0524346254781f0d6，寫入只命中01B4／01D2。位址沿實模式CS:IP及線性RAM；工具Go1.26.7、Python3.11.2、Pillow9.4.0與dosgolem82a14b266e1b5bc904e2d0fe507daf6bea41a013。

內建image_gen沿原版實際DAC、既有首座與定稿圖生成中央候選。1500×1049 RGBA原圖及alpha原樣留本機，SHA-256為bc7057fa60db21a120f3d2fd81d59f7ae77cfa56ac351aa6df9d455f7bac29b6；完整提示與參考角色見building-009-candidate-v1.json。透明格隱藏RGB原為洋紅，另製RGB歸零的原版參考供生成，原參考保留；生成PNG沒有再編碼。來源取樣及離線／即時畫面已目視，原版後畫圖示與人物保持。

原版木棚探針留下的第2槽斷言不適用中央單來源，R1在執行前拒絕；改為單來源第009幀固定斷言後，R2乾淨重跑。Go零游標配對輸出null，檢查器改為接受null或陣列並拒絕數字／字串／物件／布林；原型49點無直接中央游標，不授予懸停信用，正常GUI另有3448筆真實配對。產生器行定位與來源報告識別字的失敗保留，沒有修改原版或來源接受規則。

原版立即右鍵與等懸停後右鍵的同初始狀態實驗由pedia-timing-r1索引；只改最後兩筆輸入的時間，不算同輸入對拍或整體GUI完成。修正後用新輸出R3及同一d8ca6ed613dc4b5824d9f75e51ccdf4c6d65e6708e0318458710c97ceb874896二進位重跑。

本checkpoint的GUI仍在有界Docker執行，UID1000、無網路、原版唯讀、Xvfb有trap。已完成容器均已清除；收尾再核對容器與所有權。正式來源、十三PNG及清冊保持R43，不建立Issue寫入、tag、Release或交付包。沿既有commit／push授權保存DRAFT工具與文件，候選、原版參考、RAM、WAV、存檔與私有收據不提交。

## 2026-10-14 R44中央原型驗證完成與READY

中央第009幀限定READY，尚未正式接線，正式十三種素材保持。732Go零skip、49點原版狀態／存檔、20個來源反例、20個獨立證據及9個真實游標反例通過。R3的452組五語GUI、1808設定事件、17302不透明游標像素與五語正常恢復通過；14張均有實際HD合成，45次來源、217017事件及6088筆游標還原與完整原版狀態逐筆相符，安全範圍外零變動。649筆實際輸入四側重播至996600000步，完整CPU／RAM／VGA／DAC、WAV與存檔全同。五組暫停守門回原圖保留；未知後畫及游標不猜補。下一步加入既有來源群組、清冊及缺件驗收；本機根hd-city-source-catalog-r44。

同一d8ca6ed6原型完成R3；R2的百科失敗與成功前綴保留。原版對照證實右鍵前需要等懸停，沒有改產品或放寬畫面判準。14張R3都是實際HD，Source與CJK安全範圍外零變動。原版第一輪14點重播到最後中央快照，完整GUI終點另由649筆實際輸入四側核對，不混稱整段逐寫收據。

正式清冊與十來源索引先留本機草稿，規格064記錄固定SHA與正式接線契約；正式十三素材保持。獨立審查命令曾把輸出r3誤套至Docker映像名，沿用既有runtime-r2後乾淨通過，沒有另建映像。所有Docker工作均非root、無網路、有界、原版唯讀且Xvfb有trap；本批容器已清空，輸出1000:1000，無root檔案或md目錄。沿既有commit／push授權接續正式第009幀，不改遠端Issue或既有發行。

## 2026-10-14 R45中央建築正式接線

中央第009幀依58ea769的READY契約加入既有來源群組，原始PNG與alpha不變，正式合計十四種素材／15檔。
734Go零skip、go vet、49點原版狀態／存檔、200來源反例、44啟動／恢復及44封裝反例通過。
452組GUI、1808設定事件與17466游標像素通過；650筆實際輸入四側重播至1005200000步，完整原版狀態、WAV及存檔一致。
三組暫停及木棚拖曳的安全回退保留，未知來源不復活。詳細雜湊、限定信用及重生入口見規格064的R45節。
首輪測試總時限不足，另一次重跑命令重複套輸出前綴，確認後停止；更正後於相同映像乾淨重跑通過。
GUI R1圖像選項未進草稿，保留41組前綴；R2等待草稿確認後全452組通過。這些修正只在驗證操作。
R44原型產生器逐位元組保持；正式沒有中央原型旗標。原版圖像、資料與存檔只留本機。
本批Docker工作均使用非root、有界資源及唯讀原版；結束後無本批殘留容器，輸出未有root檔或.md目錄。
依既有commit／push授權提交本批；未建立新版發行。

## 2026-10-14 R46世界地形來源研究

confirmed限規格062 R46的唯讀來源與轉送證據，正式HD不變。PHYS0.SS與TERRAIN.SS共163個非空來源已綁編碼與索引指紋。
53筆正常輸入的49點完整原版狀態／存檔與無觀測控制相符；2005個入口中1433個清冊命中。
13個PHYS0來源的133次繪製、247763事件及14998個暫存至主畫布像素經獨立模型核對，24反例全拒絕。
TERRAIN.SS未在本批0D46入口命中，8×8別名及其他畫布寫入保留未知，不按像素匹配猜補。
模型首輪誤追未蒐集完整後畫的游標區域，保留56010710步反例；修正追蹤範圍後通過，原版及收據保持。
工具、指紋、位址空間與重生入口見規格062；尚無新地形生成圖、正式HD、游標還原或動畫信用。
Docker均有界、非root及唯讀原版，工作完成無本批殘留容器，輸出未有root檔或.md目錄。

## 2026-10-14 README截圖更新

依使用者追加要求，README換成已驗證正式顯示層的繁中殖民地、世界、主選單及顯示設定四張實際畫面。
前三張採R45正常GUI已與X11遊戲區逐位元組核對的呈現PNG；設定另以相同正式二進位正常開啟繁中面板擷取。
PNG原樣複製，沒有AI生成、合成、裁切或重新編碼。舊研究截圖保留，不覆寫歷史證據。
README明示開發版及未完成範圍，沒有把DRAFT地形候選或已發布封包當作新HD成果。
docs/screenshots/readme-captures.json保存程式、來源、尺寸、SHA及使用者授權；原版部分沿LICENSE第2(c)條。
擷取腳本初次未帶Python模組路徑而停止，補PYTHONPATH後在相同映像乾淨重跑通過。
Docker擷取與檢查均非root、有界資源及唯讀原版，完成後無本次容器殘留。


## 2026-10-14 R47第079幀原型與RAM還原研究

沿定稿精細像素風產生第079幀候選，原PNG、完整提示及原版參考只留本機hd-terrain079-r47。
隔離44Go檔通過建置、go vet及735項零skip；49點原版狀態／存檔及23反例通過。
首輪測試漏列既有海洋遮罩，補正後乾淨重跑；個別重驗缺DISPLAY為驗證環境問題。

72組必要五語GUI、288設定事件、2542不透明游標像素及五語恢復通過。
16點原始快照為14張HD及2張原版模式，15次地形來源、6144筆游標還原與241696個HD輸出像素已獨立核對。
完整GUI首輪只有470組成功前綴，退出確認的零來源斷言錯誤，保留失敗，不算整體通過。
必要流程重跑沿同一二進位、映像與真實玩家操作；未改產品接受規則。

76筆實際輸入四側重播至165800000步，完整CPU、RAM、VGA、DAC、WAV及存檔全同。
呼叫邊界沿既有內外掛鉤差1的契約；實際寫入、快照及原版狀態直接相符。
已目視實際繁中HD海圖。原型存檔返回只有48點，仍為DRAFT，正式十四種素材保持。

RAM唯讀研究重跑原有53筆輸入與49點，證實5886個保存、4370個還原及348筆游標還原。
第079幀有2561保存、1899還原及64筆游標還原，正常返回世界可恢復1129點。
三個公開研究工具已索引至規格062，重生Go／執行檔全等，12反例與49份正向模型重驗通過。
下一步將此來源鏈帶入隔離原型，再驗存檔返回、未知覆寫及正常GUI；尚未正式接線。

README四張已驗截圖已於196c1fb推送；本輪DRAFT地形不進首頁。
本輪Docker均非root、無網路、有界、原版唯讀，Xvfb有trap；結束稽核確認本輪容器清空與1000:1000。
原版像素、候選、RAM、寫入收據、音訊及存檔不提交，不更動Issue、tag、Release或dist-all。
精確指紋與重生入口見規格062、commands-r47.json及final-audit-r47.json。


## 2026-10-14 R48地形RAM還原與全量HD範圍

R47已提交並推送fda0baf，README四張截圖沿196c1fb。接續第079幀RAM還原原型，正式十四種素材保持。
44Go檔通過建置、go vet及735項零skip，49點完整原版狀態／存檔與31反例通過。
存檔返回完整1129點，2561個保存、1899個還原及1816點來源表峰值與R47獨立模型一致。

82組正常五語GUI、328設定事件、2952不透明游標像素及存檔前後十次五語恢復通過。
20點原始快照含19張HD與一張原版模式，15次來源、9280筆游標還原、RAM計數及330992個輸出像素獨立核對通過。
94筆實際輸入四側重播至179600000步，完整CPU、RAM、VGA、DAC、WAV與存檔全同。
第079幀含RAM來源契約限定READY；正式組裝、缺件與效能另驗，不授予正式HD或全量完成信用。

建置首輪缺組裝輸出目錄，補齊後在同一工具鏈乾淨通過。
GUI R1成功19組前綴後抓到仍未退場的設定面板，保留失敗PNG。
R2在同一原版暫停點等待已提交畫面，核對步數、設定交易保持，不重試套用。
R2整體通過，實際無等待重擷取；正式前端、圖像及游標接受規則沒有改動。

使用者明確要求「HD也要包含小圖像，要全量HD」，依grilling記錄既定決定，沒有重問。
更新AGENTS、目標186、目前狀態與既有Issue63工作項目，包含所有玩家可見圖像及動畫幀。
原版SS盤點為206檔／1517幀紀錄，另查到35PIK；ICONS.SS有131幀及2×2／4×4／6×5等小尺寸，
CURSOR.SS有兩個17×17幀。以上只確認檔案與尺寸，未從檔名猜用途或把全部幀當成HD完成分母。
下一步接續全量小圖像、PIK與其他可見來源清冊及正式共享來源接線。

本批Docker均非root、無網路、有界、原版唯讀且Xvfb有trap，收尾核對容器清空、1000:1000及原版未被追蹤。
精確指紋由規格062、commands-r48.json及final-audit-r48.json索引。沒有新Issue寫入、tag、Release或dist-all產物。
## 2026-10-14 R49全量圖像盤點與小圖像來源

依使用者全量HD要求，公開盤點器已解碼全部206個SS與35個PIK，保存1552筆來源紀錄。
原版像素留本機；公開來源索引連結指紋、幾何、別名、十四種正式素材與第079幀READY契約。
19筆空尺寸、69筆零不透明SS幀及33組編碼別名完整保留；47個其他檔案與程式繪圖尚未分類。
原版全部玩家可見圖像的分母仍未知，檔案解碼數不當作全量HD完成比例。

同一53筆正常輸入與49點的全SS唯讀探針命中2005次入口，1931次唯一、74次四候選別名。
來源集合保留，沒有按首筆或AX猜選；正常流程包括31種小圖像與CURSOR第000幀的兩次入口。
小圖像420次完整繪製、131302筆寫入與420次來源建立經獨立模型核對，透明底圖與未知後畫撤銷一致。
完整CPU、RAM、VGA、DAC及兩個原版存檔與無觀測控制相同，40個真實收據反例全部拒絕。
未知後畫含同值都撤銷；沒有增加游標、RAM還原、動畫、WAV或正式HD信用。

PIK首輪假設至少三區段而拒絕COLONY.PIK，保留失敗；確認兩區段後直接讀320×72索引，色盤保持未知。
R3公開盤點器與R1的1532筆及R2的1533筆像素全等，各167張預覽及三張接觸表不變。
同步目前狀態、目標186與唯一工作清單；WORKLIST由工具重生，沒有遠端Issue寫入。
正式十四種素材保持，下一步接續小圖像與游標的HD素材、來源還原及共享接線，不結束全量HD目標。

本機根hd-full-assets-r49，精確指紋見RESEARCH-LOG R49，命令與收尾稽核由commands-r49.json及final-audit-r49.json索引。
Docker均非root、無網路、有界及原版唯讀；收尾核對本批容器清空、1000:1000、沒有root輸出或md目錄。
依既有commit／push授權提交盤點、來源工具與文件；原版、像素、預覽、RAM、存檔及私有收據不提交。
README四張已驗截圖保持，不以本批來源研究替換；沒有新tag、Release或dist-all產物。
## 2026-10-14 R50小圖像首批素材候選

R49已提交並推送6d7f204。沿定稿精細像素風，以內建image_gen獨立生成第022、023、024幀三張候選。
原圖、alpha、完整提示、工具來源與31幀原版DAC參考留本機hd-small-images-r50，不加入正式清冊。
第023幀有柔光，針對此點生成v2後仍可見，兩張均保留，未稱定稿。
沒有為此修改PNG的alpha或刪除原圖；alpha128只定位內容，原RGBA取樣保留。

離線依R49逐寫來源身分在四個原版快照試合成，世界點0變動，三個城內點各11001點差異。
全部差異限於當次第022至024幀的不透明來源區塊，原版、游標與其他圖像沒有改動。
已目視28×48／32×48取樣與正常城內構圖；這是離線候選預覽，不算新增GUI或正式接線。
接續其餘小圖像素材、游標／RAM還原及共用來源接線，完整HD仍未完成。

Docker參考生成、原檔複製與試合成均非root、無網路、有界及唯讀原版；收尾無本輪容器殘留。
本輪只提交目前狀態與研究紀錄。README四張正式截圖與十四種正式HD素材保持，沒有新發行。
## 2026-10-14 R51小圖像還原研究

R50候選紀錄已推送0e68b95，原圖仍留本機。接續31來源的共同游標與RAM觀測，沒有安裝HD。
420次完整繪製與180696事件獨立重建，53筆正常輸入、49點完整原版狀態與存檔保持。
第005幀547保存／422還原；第005及062幀共260筆一般游標還原。其他來源沒有本批還原樣本，不外推。
12反例通過，正向49份來源模型重驗全等。公開組裝器重生Go、執行檔與檢查器全等，同一收據再次通過。

反例R1選到目的舊值未知的首次RAM保存，R2的合併選點條件沒有目標；兩輪均未取得完整反例信用。
重查路由及規格062後，舊值反例改選真正已有前寫紀錄的保存，其他反例仍核對第37點可見還原。
R3完整通過；只修測試取證選點，模型及產品接受規則不變。
一般游標的來源第000幀與原版256bytes有精確對照，但資料流、熱點及未知拖曳仍待查。

來源索引、目前狀態與目標186同步限定研究信用，正式十四種素材、README四張正式截圖及發行保持。
精確指紋見RESEARCH-LOG R51，本機根hd-small-images-ram-r51與公開工具重生-r51-public-r2。
Docker均非root、無網路、有界且原版唯讀；收尾無本批容器，輸出1000:1000且沒有root檔或md目錄。
依既有commit／push授權提交研究工具、索引及文件，未提交原版、像素、RAM、音訊、存檔或候選。

## 2026-10-15 R52小圖像隔離顯示

R51已推送72462cb。本輪命中復古遊戲規格閘門，沿既有R49至R51原版證據建立規格065 DRAFT。
31來源共用一個群組與全RAM觀測器，只有第022、024幀候選實際繪圖；第023幀柔光及其餘未生成幀保持原圖。
735Go零skip、go vet、49點完整原版狀態／存檔、533來源反例與16 RAM反例通過。
缺件、錯件、連結、截斷與空參數另驗13項，載入保持原版RAM。

102組正常五語GUI及408筆設定事件通過。20點獨立原版／控制重建800次來源與270612事件；
339筆游標配對、547保存與422還原同原型，222048個小圖像像素依原RGBA重算全同。
97筆實際輸入四側至208200000步，完整CPU／RAM／VGA／DAC、音訊與存檔一致。
公開重生工具產生同一執行檔；正式十四種素材、41Go／24綁定及README截圖保持。

初次命令用了login shell而失去Go PATH，改同一映像的非login shell後通過。
RAM反例原先只看REP首字，未取到來源；依dosgolem實作改查真正搬移範圍，原型接受規則不變。
獨立像素檢查修正模型欄位與Go16bit合成捨入；GUI模型的呼叫序號保留在原始證據，
逐點比對投影來源序號、局部位置及原版色號，游標offset明確換成主畫布線性位址。
各失敗輸出保留，沒有放寬原版或像素比較。
窄測複製時曾只替換來源檔名，暫時覆蓋隔離目錄的原版測試檔。公開來源稽核抓到差異後，
依保留來源恢復兩個獨立測試檔；45個Go檔與公開重生逐byte相同，13反例另保存JSON收據。

四筆循序效能量測均保持原版狀態，但原型66.340／40.978秒有波動，正式基準37.059／36.437秒。
本輪未將效能或正式接線標完成；後續查明成本，再驗正式新行程缺件／恢復及封裝。
公開工具只含程式與指紋，原版像素、候選PNG、RAM、音訊與存檔都留本機。
Docker均非root、無網路、有界且原版唯讀，輸出1000:1000；本批收尾無殘留容器、root檔或md目錄。

本輪依既有授權commit／push，沒有新發行，完整HD與五語覆蓋繼續進行。
清單驗證另發現README已更新四張畫面，但初始工作項仍搜尋舊difficulty-zh圖名。
已改核對現行四張已驗截圖引用，README內容與原始截圖不變。

## 2026-10-15 R53效能審查與R54小圖像正式接線

R52已提交並推送92aa427。接續CPU採樣發現，開小圖像的驗證報表由147797838增加至485357099bytes，
小圖像追蹤／合成占樣本2.77%；字型載入與結束匯出也含在總時間，不能把差異全算給追蹤器。
查明既有play=true已不累積逐幀歷史，沒有新增診斷資料格式或修改保留邏輯。
同一97筆實際輸入、2CPU／3GiB的遊玩模式ABBA為正式32.535／31.932秒、原型35.892／35.198秒，
均值增加約10.3%，四次完整原版狀態保持。規格065據此限定READY，再進正式實作。

第022、024幀原PNG、alpha、完整提示及權利正式納入graphics，共十六張PNG與清冊17檔。
31來源共用追蹤群組，只有已生成的兩張繪HD，其餘不增加完成數。
正式43Go／26綁定、742Go零skip與go vet通過；49點原版狀態／存檔、549來源／RAM反例及13載入反例通過。
15張原版／小圖像／全部HD樣本PNG與R52逐byte全同，獨立RGBA重算相同。

102組正式五語GUI、408設定事件與3772不透明游標像素通過；唯讀快照副本只增一個診斷來源，
43個正式來源其餘逐檔相同，素材沿正式loader。20點獨立原版／控制重建800次來源、272013事件，
369筆游標還原與547／422 RAM計數相符，222048個小圖像像素重算全同。
103筆實際輸入四側至213200000步，完整CPU／RAM／VGA／DAC、WAV與存檔一致。
正式43Go遊玩模式另用R52的97筆輸入核對全狀態、音訊與存檔，兩個進城檢查點實際繪出兩張素材。

50種新行程缺件／恢復、249設定事件及52項封裝拒絕通過，原日文HD偏好保持。
正常遊玩檢查點保存在run.json的checkpoints；原驗證腳本誤找獨立JSON，修正後重查同一輸出通過。
README設定截圖腳本移至本機輸出後缺模組路徑，補PYTHONPATH並在同一映像乾淨重跑通過，非產品失敗。
R52公開重生工具改用固定R45來源，正式程式前進後仍重生45Go與同一執行檔。

規格065限定CONFORMED；來源索引重生1552列與16個正式綁定，完整玩家可見分母仍未知。
README四張本批正式畫面已擷取；依既有授權原樣更新，來源及限制另存截圖紀錄。
原版參考、RAM、音訊、存檔與未選候選留本機；沒有新Release或全量HD完成聲明。
Docker全程非root、無網路、有界且原版唯讀，收尾無本批殘留容器、root檔或md目錄。
正式程式與畫面已提交e7a7aa5，四張README來源指向此程式版本。
三張未出現新素材的畫面與前批像素相同，殖民地圖已顯示兩種新小圖像；四張皆重新擷取並原樣保存。


## 2026-10-15 R55三張商品HD

接續5ada32c。命中規格閘門、文件分工及README聲明路由，沿已確認的精細像素風生成025棉花、026毛皮、027木材。
原PNG及alpha不變，完整提示與來源入graphics清冊。023新候選仍有柔光，留本機且不計HD。
小尺寸原版遮罩檢查後先擴充規格065 READY，再接入正式loader與封裝；合計十九種素材。
清冊完整提示超過64KiB，依規格將有界讀取及封裝同步提高至128KiB，完整指紋與連結拒絕不變。

751Go零skip與go vet、49點原版全狀態／存檔、558來源／RAM及25載入反例通過。
102組五語GUI、408設定事件及3690不透明游標像素通過；商品游標往返由三組擴為五組。
26點獨立原版／控制模型963次來源、304376事件及413游標還原相符，835664個RGBA像素重算全同。
103筆實際輸入四側至222000000步，完整原版狀態、WAV與存檔相同。
正式play=true另驗五張商品與全狀態，報表1628849bytes，frames為0。
59種新行程缺件／恢復、294設定事件與61項封裝拒絕通過，規格065本批限定CONFORMED。
來源索引首輪沿用舊目錄名而停止，修正本批輸出路徑後以同一映像重跑通過，非產品缺陷。
README截圖使用本批已驗正式畫面，來源版本於程式提交後登錄。沒有新Release，完整HD與五語覆蓋仍待完成。
原版輸入唯讀，原版像素、RAM、音訊、存檔與未選候選只留本機。Docker清理及提交結果於下段記錄。

工作清單首次核對誤用check子命令，依工具既有write／verify入口重跑通過；未修改產品或放寬驗證。

本批Docker均為非root、無網路、有界，原版唯讀。收尾無R55殘留容器；全工作樹未見root檔或md目錄，輸出為1000:1000。依既有commit／push授權提交正式三張商品素材、程式及文件，再登錄README截圖的來源版本。

正式程式與三張原圖已提交230637db901bf69872c839ec2e0e2f71b23c8d6c。README四張畫面由本批正式程式重新擷取並原樣保存，截圖清冊指向此程式版本；殖民地圖顯示新增三種商品，其餘三張像素保持。完整生成提示保存於graphics/manifest.json，使用內建image_gen。


## 2026-10-15 R56十一張小圖像

接續fa1c3cb。命中規格閘門、文件分工與README路由；內建image_gen逐張生成028至038，原PNG與alpha不變。
來源模型先確認036／038也在世界出現，將世界、十五張城內圖像與63點正常GUI列入READY，再接入正式程式。
正式三十種素材／清冊31檔、43Go／26綁定；784Go零skip與go vet、49點原版全狀態／存檔、591來源／RAM及69載入反例通過。
102組五語GUI、408事件及3690不透明游標像素；63點獨立原版／控制模型1580次來源、438381事件及1764游標還原相符，
2381968個RGBA像素重算相同。143筆實際輸入四側至259400000步，完整原版狀態、WAV及存檔相同。
日文進城一組守門回原圖後正常恢復十五來源，未計持續HD。正式play=true另驗十五張城內圖像，frames為0，報表1628894bytes。
36種本批新行程、179事件與94項封裝拒絕通過；舊新行程沿R55，未重標全部92種已重跑。
首輪連結038反例在GLFW初始化無法連X11，保留輸出。命中Xvfb試玩路由，確認-noreset旗標後加就緒檢查與socket目錄，
同一映像乾淨重跑36種通過；沒有修改產品或放寬HD回退。固定像素檢查器舊三張變動假設依世界來源改為五張，逐RGBA條件不變。
README將更新本批實際世界與城內畫面，原版參考不公開。下一批R57準備其餘十四來源，023原圖在正式遮罩下復審可辨識，尚待正式GUI。
沒有新Release或全量HD完成聲明。Docker清理與提交來源於下段記錄。

本批Docker均非root、無網路、有界，原版唯讀。收尾無R56殘留容器，完整工作樹無root檔或md目錄，產物1000:1000。依既有commit／push授權提交三十種正式素材的本批程式及文件，再將README四張實際畫面綁定此程式版本。R57已生成六張原PNG與提示也原樣留在本機工作區，未加入正式清冊。

正式程式與十一張原圖已提交e88e99594328e9f35c9de8cf38e0701dfb250fd7。README四張本批實際畫面原樣保存並指向此程式版本；城內與世界圖顯示新增圖像，主選單及設定列像素保持。內建image_gen的原圖與完整提示在graphics/manifest.json。


## 2026-10-15 R57十四張小圖像

接續fd0eae0。命中規格閘門、文件分工與README路由。先審查十四張實際尺寸及世界／城內／存檔返回預覽，
制定READY後接線；十三張新生成、023沿R55原PNG，alpha不改。完整Go首輪650秒總時限到期，沒有個別測試失敗；保留R1輸出，僅將總時限提高至1200秒，用同一映像／資源及未變動程式乾淨重跑R2。
規格065 R57限定CONFORMED，30張小圖像、世界5種與城內28種，合計44種正式素材／清冊45檔。826Go零skip與go vet、49點原版狀態／存檔、633來源／RAM及125載入反例通過。102組五語GUI、111點獨立原版模型與7529424個RGBA像素相同；187筆實際輸入四側至327600000步，完整原版狀態、WAV及存檔保持。45種本批新行程與136項封裝拒絕通過。守門回退0組另記，不計持續HD，五語城內來源恢復。正式play=true驗28張城內圖像，frames為0。
30張均有正常GUI懸停與像素驗證，其中21張有游標還原正向，其他9張未發生來源還原事件，不外推。005的RAM保存／還原已帶入HD像素比較。
原版參考與執行收據只留本機。README接續更新同批實際畫面，沒有新Release。Docker清理與提交記於下段。

本批Docker均非root、無網路、有界，原版唯讀。收尾無R57殘留容器，完整工作樹無root檔或md目錄，產物1000:1000。依既有commit／push授權提交本批程式及文件，再將README四張實際畫面綁定此程式版本。全量HD目標持續，沒有新發行。

十四張原圖與正式程式已提交8983cd0a8c191b3a04cafac996bce72dd9f2c3b0。README四張實際畫面原樣保存並綁定此程式版本；世界與城內圖顯示本批小船、人物、旗幟及工具框等圖像。原版參考與收據不公開。下一批世界079的原圖與既有READY證據已備妥於本機hd-terrain079-formal-r58，尚未改正式程式。


## 2026-10-15 R58世界079正式接線

接續996abdd。命中規格閘門與文件分工路由；R48來源契約補足正式共享觀測、載入與驗收後接線。原PNG與alpha保持，45種素材／46檔，沒有新增原型素材旗標。
規格062 R58限定CONFORMED，世界079與海洋共用既有觀測，合計45種正式素材／清冊46檔、45Go／28綁定。827Go零skip與go vet、49點原版來源及31反例、92組五語GUI、20點獨立來源／330992個像素、97筆實際輸入四側至199200000步通過。存檔前後十次五語恢復各1129點；沒有守門回退。正式play=true的世界、城內與存檔返回通過，原版狀態／WAV／存檔保持；固定Linux ABBA成本比例1.1623。6種本批新行程與139項封裝拒絕通過。
原版來源與像素、實際X11輸入、正式遊玩與存檔垂直鏈已驗。首輪測試及GUI漏列其他已驗來源遮罩，抓圖工具與檢查點對應問題均保留診斷並修正後乾淨重跑，正式Go執行檔未改。R4只建置未執行GUI，未計信用。README接續更新同批四張實際畫面，沒有新Release。Docker清理與提交記於下段。

R58收尾：來源清冊288項檔案含241項SS／PIK的指紋保持，未追蹤原版資料。完整工作樹無root檔與md目錄，程式及產物1000:1000，無本批殘留容器。依既有提交／推送授權提交程式、原圖與文件，再把README四張實際畫面綁定該程式版本。全量HD繼續，沒有新發行。

R58小圖像GUI工具相容性：來源數45／28已更新，補入079地形在英文及其他語言的安全遮罩與英文HD條件。唯讀工具建置、go vet及20份實際地形快照的獨立模型遮罩通過，19份各1129點、原版模式0點。只授予本次建置及遮罩樣本信用，未重跑111點小圖像GUI；正式程式沿R58的827Go與92組GUI收據。

R58程式與原圖已提交於3e492f54b9e4172fe5f178464be82d4b21acefcb。README四張圖改綁此版本的45種正式素材：世界取正常terrain079-start、城內取正常colony，主選單與設定沿同批實際畫面。PNG原樣保存，實際視窗與顯示畫布的逐byte核對沿R58收據；設定由未加觀測器的正式程式擷取。截圖紀錄保存執行檔、來源收據與圖片指紋；現行發行版不變。


## 2026-10-15 R59一般游標來源與候選

R58程式3e492f5與README f18143d已推送。接續一般游標：公開唯讀探針、獨立收據檢查與14反例已完成，
兩次來源繪圖與RAM複製、53筆輸入／49點原版完整狀態及存檔、定位與來源外像素通過。
公開重生Go／二進位相同。未取得新音訊或其他游標驗收信用。
兩張候選原PNG與alpha原樣留本機；完全替換均有128點缺口，未正式接線。
原版輪廓加原alpha預覽見規格066，下一閘門為隔離GUI、邊界與逐RGBA比較。
正式仍45種素材，原版資料與發行版不變。容器以1000:1000執行，收尾另驗所有權與清理。

R59收尾通過：288份原版輸入指紋保持，三個依賴原版的入口缺件均明確回傳77及SKIP；文件索引與工作計畫驗證通過。完整工作樹無root檔與md目錄，本批無殘留容器。新提交只含來源研究工具與文件，兩張候選及原版參考維持本機保存。


## 2026-10-15 R60一般游標透明合成READY

隔離來源47Go與唯讀GUI48Go、go vet、1項元件Go零skip、6守門與4載入反例通過。
49份元件64288像素、92組正常五語GUI、29份快照31840游標像素、九個邊界／恢復與既有地形489952像素通過。
99筆至214400000步的四側完整原版狀態／WAV／存檔相同，正常play=true及循序ABBA通過；frames為0。
世界與城內實際畫面已目視。R1的既有守門回退、全裁切檢查、舊資產路徑及索引命名空間問題保留，未列為產品缺陷。
v2參考metadata追加勘誤，原PNG與舊收據不改。規格066限定READY；正式45種素材不變，另1個READY來源。
README保持R58已驗正式畫面，原型不混入正式素材。下一步一般游標正式接線與完整回歸，沒有新發行。

R60收尾通過：288份原版輸入指紋保持，45種正式素材與28份正式來源未變；來源索引另列1個READY契約。全部新檔與產物1000:1000，工作樹無root檔或md目錄，本批無殘留容器。獨立dosgolem工作樹乾淨，upstream推送仍為DISABLED。


## 2026-10-15 R61一般游標正式驗收與限定CONFORMED

規格066 R61限定CONFORMED，一般游標已正式接線。原圖／alpha保持，原版輪廓加生成筆觸；46種正式素材／清冊47檔、47Go／30綁定。834Go零skip與go vet、49份元件／64288像素、6守門與7載入拒絕、92組五語GUI及29份快照／31840游標像素通過。九個邊界／恢復有8份可見HD、右下角1份全裁切，沒有守門回退。109筆實際輸入四側至219000000步的完整原版狀態／WAV／存檔相同；未加觀測器的play=true與循序ABBA亦通過。9種本批新行程及142項封裝拒絕通過。其他游標、隱藏狀態、背景、動畫與全量HD仍待接續，沒有新發行。

未加觀測器的四次play=true成本比率1.0177，只記固定Linux樣本。程式、字型、原版及影像均在有界Docker內驗證；README四張已授權圖片另綁本批正式程式提交。
首兩輪組裝為函式名與固定參考路徑錯誤，R3完整通過；新模板換行檢查誤判，實際程式沒有該問題。舊失敗保留，不列產品缺陷。

收尾稽核腳本的字串替換曾把288個原始檔誤改成308，未通過且沒有產生驗收收據；改為實際清冊的288後，以R2乾淨重跑。

R61提交前核對46種素材、30個來源綁定及288個原始檔雜湊保持。未追蹤原版檔案；UID/GID與root-owned掃描通過。隔離dosgolem乾淨且upstream推送維持DISABLED。本批容器已退出，沒有本專案殘留容器。

R61程式提交38eecf7f26a16f5e8fc6d5763b11311e07d4e14c。README四個既有授權圖片路徑均重新驗證，三張遊戲畫面原樣更新；設定圖新擷取的像素與舊圖相同，來源紀錄綁本批正式執行檔。沒有新增原版素材路徑，既有發行版保持。


## 2026-10-15 R62十二來源原版模型審查

規格067 R62 DRAFT：十二種新世界地形及079對照的101次來源、194628事件與12823次轉送重建通過；29份模型與R61相同。5886 RAM保存、4370還原、10012游標配對逐來源列出。080無RAM還原正向例，七種無游標還原正向例；沒有外推。36項逐來源與既有12項RAM反例通過，29／49份正向模型再驗保持。尚無新美術或正式HD，正式數量保持46種。

原版執行、工具版本與位址空間沿規格067及R61；本批沒有修改正式顯示來源或原版輸入。

首輪反例後摘要把記憶體中的整數鍵與JSON字串鍵直接比較，36項拒絕後在摘要步驟失敗。改為兩側已序列化收據比較，R2乾淨重跑通過；原版模型與來源守門沒有修改。

R62收尾核對288個原始輸入保持，正式47檔／30來源綁定未變；未追蹤原版素材，root-owned與UID/GID檢查通過。兩次來源索引輸出逐byte相同；隔離dosgolem乾淨、upstream推送DISABLED。本批Docker容器已退出且無殘留。文件整理腳本的換行錯誤由語法預檢拒絕，修正後才寫入文件。README四張圖仍沿R61正式提交與收據，這輪未修改正式顯示程式。

## 2026-10-16：十二種世界地形由原型進入正式HD

- 沿使用者定稿的精細像素風，以內建imagegen生成十二張候選及五張森林v2。
  選用十二張原PNG；完整提示與指紋寫入graphics/manifest.json，未選候選及原版參考只留workplace。
  十二來源的1652個原版不透明格均有生成alpha；只在實際原版來源格內做Over合成。
- 先以隔離原型核對29點、108來源反例與40載入反例，再審查為READY後正式接線。
  共用既有全RAM觀測回呼，不加原型旗標到正式入口。既有46張素材與原版保持。
- GUI測試問題依證據修正：首次選080時該點受遮擋；066中心未碰到不透明游標。
  改以實際可見格與82格原版游標交集選點。006懸停的RAM配對要求被原版兩側診斷否定，
  依真正事件比較，保留零例限制。後續phase名稱遮蔽、世界標籤漏列與92／96計數皆為驗證腳本問題。
  R7在最後一份來源請求讀到未完整JSON，R8改為完整寫入後原子更名，96組與36份全部通過。
  原失敗收據保留，沒有放寬來源或像素守門。
- 環境／工具問題另記：缺embedded支援檔後補齊並乾淨組裝；
  單檔掛載不支援gofmt原子rename，改以stdout覆寫既有自有檔後重建。
  過長shell參數改為檔案編輯；診斷未新存檔時只驗實際存在的COLONY09.SAV。
  正式封裝數量、重播輸出路徑與像素審查的原型標記修正後，用相同工具鏈乾淨重跑。
  GUI像素審查在說明文字定稿後再生R2收據，程式指紋與執行內容相同。
- 規格067 R63限定CONFORMED，十二種新世界地形已正式接線，合計58種正式素材／清冊59檔、50Go／33綁定。872Go零skip與go vet、29點原版狀態／存檔及823856個RGBA、108來源與40載入反例通過。96組五語GUI、36份來源懸停、65點獨立原版模型與1020160個地形RGBA、47232個游標RGBA通過。143筆實際輸入四側至252000000步，完整原版狀態／WAV／存檔相同。未加擷取器的play=true、frames為0及循序ABBA通過，Linux成本比例1.5285只為有界抽樣。20種啟動回退／恢復與178項封裝拒絕通過。全量HD、其餘單位、背景、特殊游標與動畫未完成，沒有新發行。
- 完整審查432d55e8e0d90418ab09574cc20113236105a13e870af19f73942616f075f405，指令與收據根hd-world-terrain-prototype-r63。GitHub #63遠端OPEN，本機維持in_progress。README四張正式畫面及其來源紀錄接續更新，不改v.1.0.3-20261010發行。
- Docker作業均為非root、限額、預設斷網及唯讀原版；本批一次性容器用--rm，已無殘留本批容器。288原版檔雜湊、33份程式綁定、58張生成素材、誤追蹤與擁有權稽核通過，收據8c57d764af53bc1606db62890253abbe2eadc07fe32e50b4e8538ee8f405159a。隔離dosgolem乾淨，upstream推送仍為DISABLED。

### R63提交與README畫面

正式接線已提交c33d432並推送main。README四張圖更新為本批正式版的HD殖民地、
HD世界、Noto主選單與繁中顯示設定。前三圖沿已驗真X11遊戲區的唯讀擷取，
設定圖來自未加擷取器的正式視窗；四張PNG原樣複製，來源程式固定c33d432。
截圖紀錄保留使用者原授權，58種素材、原PNG指紋與開發版範圍一致，
沒有使用概念圖或DRAFT原型。圖片審查bb205d558e70cd5265a273e19efdf5ee3c61a309a7ee854ab3fc79ba894c9728。
現行v.1.0.3-20261010與原版資料不變；全量HD及新版交付仍待接續。

## 2026-10-16：R64八種8×8世界碎片正式接線

- 原版先重生十五個AX槽位與65點模型。八種有可見彩色格，其他七種本次被後畫蓋住，
  不直接重繪未見內容，也不判定它們不可達。共享編碼以AX及實際來源紀錄分開定位。
- 沿定稿精細像素風，以內建imagegen生成八張原PNG。233個原版彩色格皆有生成alpha，
  原PNG不裁切、不重編碼；原版索引0按原色盤保留，透明格與原版幾何不擴大。
- 先驗隔離原型65點、72來源反例、28載入反例與278608個RGBA，READY後才正式接線。
  原第116及119為全不透明，反例驗矩形外寫入，沒有假造透明格。
- 原版模型的舊「53筆」限制描述修正為143筆／65點，另存source-review-r2.json，
  原R1與模型、資料及收據保持。正式GUI第一次命令的目錄名稱在host test -f被擋住，
  修正後100組正常流程通過。原版收據第一次缺/game掛載，exit77後補唯讀掛載，
  用gui-oracle-r2乾淨重生89點；這些皆為驗證環境問題。
- 完整Go首批套件1800秒期限中斷，417項、84個頂層通過，無named failure或skip。
  來源與輸入不變，以同一映像補跑115個頂層481項，新輸出保存中斷項；
  聯集898個唯一測試覆蓋全部199個頂層，再驗go vet。首批期限紀錄不改成套件通過。
- 規格068 R64限定CONFORMED，八種8×8世界碎片已正式接線，合計66種正式素材／清冊67檔、53Go／36綁定。898Go由417＋481兩批完成，199頂層全覆蓋，零skip與go vet通過；首批1800秒套件期限保留，沒有測試案例失敗。65點元件／278608個RGBA、72來源與28載入反例通過。100組五語GUI、新增24份懸停、89點獨立原版模型、95712個地形RGBA及31488個游標RGBA通過。165筆實際輸入四側至281400000步，完整原版狀態／WAV／存檔相同。正常play=true、frames為0與循序ABBA通過，Linux成本比例1.0918只為有界抽樣。16種啟動回退／恢復與202項封裝拒絕通過。其餘單位、背景、標題、特殊游標、動畫與全量HD未完成，沒有新發行。
- 原58種索引逐byte重生保持ba2bb375…；新66種索引031cf376…不含原版像素。
  審查647c178a57f12d8af166f979293e313b73025ad7f252da5f1a80ac49c5753b0f。唯一指令入口commands-r64.json，根hd-world-small-terrain-r64。
- README實際畫面接續更新，不改v.1.0.3-20261010；全量HD與新版交付仍未完成。
  提交前核對288原版雜湊、36程式綁定、66張生成素材與清冊67檔，原版檔案未被追蹤。
  原型重新組裝的53份Go與已驗版本相同；所有權及全工作樹root-owned掃描通過，
  稽核3120db7d9a3724e8fc0867bcefbaf7646b95a96ccb1b0c8b8c79d92c7d3c34c9。
  隔離dosgolem乾淨且upstream推送仍為DISABLED。本批容器皆以--rm退出，沒有殘留。

### R64提交與README畫面

正式接線468e835ffb5a36f9e012797104bfe19e7dcaec82已推送main。README四張既有授權圖片的來源紀錄
更新為本批66種素材的正式程式，原PNG直接複製；主選單的像素與前批相同。
設定圖重取時一行狀態文字不同，原樣保留；未把新舊畫面相同列為驗收條件。
三張遊戲圖沿已驗X11視窗遊戲區的唯讀擷取，設定圖由未加擷取器的正式程式重取。
圖片審查44497112b236b2709ffc11b36e5a0874ce5cd33a40d8c7b0de6bc5ca951cc0f6。既有發行版保持，全量HD繼續。

## 2026-10-16：R65冷啟動背景與底紋DRAFT

R64程式468e835與README 1f8cf70已推送。R65補驗原49點及啟動初段17次來源，
後段2005次與R49保持。三種32×24底紋及64000點PIK解碼已驗，OPENTILE四點各6332個來源格。
公開重生工具通過go build／vet、正常前綴7輸入／4完整原版狀態與獨立模型。
原版資料與正式53Go／36綁定、66種素材保持。新三張原PNG及完整生成提示只留本機。

首輪建置缺/dosgolem唯讀掛載，沒有執行原版；補掛載後用新輸出乾淨重跑。
R2公開重生Go及二進位與初始探針相同；加入PIK缺件明確skip後重跑正常前綴，原始逐寫相同。
R3至R5逐步補充普通VGA記憶體與整張識別候選，完整原版狀態保持。
R4整張來源未命中，R5保存1838點差異及拒絕結果；沒有把這個拒絕稱為產品缺陷。
四個反例涵蓋缺PIK、錯PIK及不合法起點；現行探針另重驗缺件／錯件。
主選單v1下方金邊位置不符，v2依原版位置修訂，原圖均保持。
整張背景仍需VGA往返契約，下一步先做已驗底紋的隔離合成。

來源清冊新增冷啟動與底紋證據，仍為1552列／66正式素材，完整可見分母未知。
索引bcae9a4fa9a5fd0200f9cf023b732a280ef06f56662884bb7ab77b7f2d821321；驗證與指令見本機commands-r65.json。
本批Docker、原版雜湊與所有權收尾另記。沒有新發行或新原版素材公開。

R65收尾核對288個原版輸入、36份正式綁定及66種素材保持，未追蹤原版資料。
來源檢查器、組裝器與索引指紋相符，文件入口及UID/GID通過。
首次稽核遇sandbox投影目錄在列舉後消失；重試又碰到負向探針已建立的輸出目錄。
以新輸出及find的ignore_readdir_race重跑，只忽略列舉後消失的項目，未忽略權限或root檔案。
稽核44a4a36cbe4b21f63a8fe87d9e11553403a1be5a2ae69739c85ff25ed74072c6。
獨立dosgolem乾淨，upstream推送DISABLED；本批Docker容器均已退出，沒有殘留。

## 2026-10-16 R66：主選單背景、木紋與文字底色正式接線

規格069 R66限定CONFORMED。主選單背景與32×24木紋兩張原PNG已正式接線，合計68種素材／清冊69檔、55Go／38綁定。47個頂層／631個Go測試零skip與go vet通過；首批660秒套件期限保留，只補跑未完成的1＋25個頂層。12點來源／底色與89點原版場景回歸通過；新正式GUI另驗13個原版狀態、10組五語切換及三次懸停。7762560個RGBA、每語749格文字底色、四側至26600000步的CPU／RAM／VGA／DAC／WAV／種子存檔相同。正式play=true、9種缺件／恢復與208項封裝拒絕通過。VGA往返生命週期仍未知，背景改依完整可見索引與原版選單邊框辨識；不改遊戲規則、字型或字級。WOODTILE／PARCH、其他圖像、動畫與全量HD未完成，沒有新發行。

本機證據根沿hd-cold-start-sources-r65。READY審查70a329673b8eeb39dfece2774fb655898229773233b2d24ba82174737e2a5999，正式審查d85cfb2fb95f4b4b47aefa7800d3e295b8400948cbb556fd69d8cd9ce129e5d2。新原PNG原樣加入graphics，未發布原版參考。README主選單截圖在程式commit後更新；其他三張沿R64逐圖指紋保留。

驗證腳本修正：第一版主選單元件測試誤要求不存在的COLONY00.SAV，12點來源及守門已通過後才失敗。改為兩側均不存在才接受，新目錄乾淨重跑通過。第一批原型GUI的RAM還原計數要求與原版VGA事件不符，保留失敗並以獨立原版診斷及來源／像素核對修正驗收。模型第一版的文字替換誤改768及世界89點誤要求主選單正例，均屬檢查器錯誤，修正後同一原版收據通過。初次篩選器的頂層數量假設未達而在執行測試前退出，改為明確必要測試集合。正式Go首批660秒套件期限的原日誌保留；只補跑未完成的1＋25個頂層，631個案例聯集零skip，沒有案例失敗。

Docker皆為斷網、UID/GID1000、有資源與逾時限制的一次性容器，Xvfb有trap。完成後須核對沒有本批殘留容器、root-owned檔案或誤追蹤原版；收尾結果記於本批稽核。沒有新Release。

收尾稽核a6836e74eb2064d8ce671e99e611a6dca955fdbf4f752fa9270e19649ecfa414通過：38來源綁定、68原PNG、288原版檔案指紋與WORKLIST重生相同，沒有誤追蹤原版、root-owned產物或本批殘留容器。獨立dosgolem保持乾淨，upstream推送仍為DISABLED。

R66程式與兩張生成圖已以fe97cf6提交並推送main。README主選單改用同批已驗正式GUI原PNG，沒有裁切、縮放或重編碼；其餘三張R64截圖保持，逐圖加入程式版本與素材數，避免把舊畫面當新建置。已發布v.1.0.3-20261010不變。

## 2026-10-16 R67：世界木紋正式接線與GitHub素材

規格069 R67限定CONFORMED，世界與城內WOODTILE第0幀原PNG正式接線，合計69種素材／清冊70檔、55Go／38綁定。6個頂層／30個含子案例測試零skip及go vet通過；89點來源、字底及RGBA、主選單12點回歸通過。74項五語GUI與6次游標操作，共80樣本、62個原版狀態、56筆輸入；7361264個木紋RGBA相同。四側至136600000步的CPU／RAM／可見索引／DAC／WAV／兩份存檔相同，正式play=true通過。7種啟動缺件／恢復及211項封裝拒絕通過。繁中城內一個樣本觸發既有守門回原圖，不計HD覆蓋。68張繼承原PNG保持；生成素材及清冊納入GitHub。PARCH、其餘圖像、特殊游標、動畫與全量HD未完成，沒有新發行。

本機證據根hd-cold-start-sources-r65。READY審查d69bea4dcf0f53816279187ef52da84b373641ad3502b2efff480cbd174a305a，正式審查4e70453e2a26a44fc08bc701d919e487ff70222848e39c104006f79e2e33487d。原PNG原樣加入graphics/woodtile-000.png，原版參考留本機。README世界圖在程式提交後更新，其他逐圖來源保留。

檢查器修正及限制：第一版觀測閉包誤收CBA脈絡的所有寫入而達事件上限，限三個已驗指令後通過。89點的早期來源計數差由中間RAM漏收造成，閉包模型補齊後全等，沒有放寬正式程式。GUI先後修正phase名稱遮蔽及英文模式誤等翻譯欄位的腳本錯誤；74項正式GUI另重新執行。正式獨立模型遇六筆非ES:DI目的寫入，依READY邊界回未知並撤銷；來源及像素檢查乾淨重跑。啟動腳本漏列wood來源分派已修正，第二批六個缺件通過後恢復視窗未在45秒出現；原輸出保留，第三批同容器映像及同命令七項乾淨重跑通過。首兩批不記整批PASS。

Docker均為斷網、UID/GID1000、有限CPU／記憶體／PID與外層逾時，Xvfb有trap。收尾稽核核對原版288檔、Git追蹤邊界、檔案擁有權及容器清理。沒有建立新Release。

R67程式與第69張正式生成PNG已以d48eb9d提交並推送main。README世界圖原樣複製正式繁中HD樣本，來源程式d48eb9d；主選單R66與城內／設定R64的原PNG及逐圖來源保持。

## 2026-10-17 R68：紙質背景正式接線

規格069 R68限定CONFORMED，PARCH第0幀紙質背景原PNG正式接線，合計70種素材／清冊71檔、55Go／38綁定。6個頂層／30個含子案例測試零skip及go vet通過；62點來源／字底／RGBA與來源區外保持、主選單12點回歸通過。38項正常GUI、五語恢復及6次紙質游標操作，共49樣本、48個原版狀態、55筆輸入，3778480個紙質RGBA相同。四側至138600000步的CPU／RAM／可見索引／DAC／WAV／兩份存檔相同，正式play=true通過。7種啟動缺件／恢復及214項封裝拒絕通過；1個守門回退另記，不計HD。繼承69張原PNG保持。其他圖像、特殊游標、動畫與全量HD未完成，沒有新發行。

READY審查0b537d38d5da2864fe585fff285266f2b96647fb6da982e8f5ef63b872ba9a40，正式審查0f456fb1e2cca8e05ea44fd63f24133f3372a2e9a696a7320e17f3d1b908042e。生成原PNG原樣加入graphics/parch-000.png，原版參考與逐寫資料仍留本機。README城內圖於程式提交後更新。

驗證修正：前兩批45秒開窗期限時仍在既有建築PNG解碼，SIGQUIT診斷保留；只把開窗預算設為120秒。第三批診斷標籤含大寫地區碼而被既有小寫契約拒絕，改為標籤小寫，語言值保持。第四、五批在畫面擷取階段中止，未取得完整收據；PNG離線解碼及遮罩函式獨立檢查通過，保留原輸出。第六批加入進程日誌與即時輸出後，74項正常GUI及17份來源快照乾淨通過；沒有放寬來源、像素或遊戲互動驗收，也不把先前五批記為整批PASS。

像素檢查曾誤指定原型原版資料，已改回正式49樣本對應資料並通過30張核對；檢查器增加GUI索引與色盤指紋綁定，錯配資料立即拒絕。原型與正式批次未混用驗收。

正式驗證聚焦38項正常路徑、五語紙質恢復及6次游標往返，其他來源沿元件區外保持、主選單12點及既有木紋43圖回歸。四側同輸入至138600000步的WAV、完整原版狀態與兩存檔相同。沒有重跑整套歷史測試或發布新Release。Docker為斷網、UID/GID1000與有限資源，Xvfb／進程監測有trap，收尾核對容器、檔案擁有權、288原版指紋及Git追蹤邊界。

收尾檢查已核對38份正式來源綁定、70張生成原PNG、288份唯讀原版指紋、工作清單產生結果、Git素材邊界及UID/GID1000。紙質30圖與木紋43圖均由最終像素檢查器通過，錯配原版批次反例拒絕。沒有本工作遺留容器。

R68程式與第70張正式生成PNG已以691c36c提交並推送main。README城內圖原樣複製正式繁中HD樣本，已與實際X11視窗遊戲區逐byte核對，含15953格紙質背景、10949格木紋及621格中央建築。來源程式691c36c；世界R67、主選單R66與設定R64原PNG及逐圖來源保持。沒有新發行。

## 2026-10-17 R69：新遊戲背景來源與候選

沿規格069接續DIFFICUL.PIK與NATIONS.PIK，正式70素材保持。兩張原PNG由內建imagegen依原版構圖與已定稿像素風生成，原樣保存本機hd-new-game-backgrounds-r69/candidates；提示與指紋見generation-r1.json。原版參考只留本機。

新正常X11路徑取得九點與25輸入，原版有／無觀測的CPU、完整RAM、索引、DAC與初始存檔相同，真視窗遊戲區逐byte相同。每份新PIK均核對64000格一次寫入，來源、工具、位址與限制見規格069 R69 DRAFT。第一批擷取誤在設定面板開啟時比較遊戲區，第二批誤讀status未提供的記憶體指紋欄；修正為關閉面板且保持原版暫停、讀同次顯示事件，第三批乾淨通過，前兩批保留失敗輸出。這些是驗證腳本修正，沒有修改正式遊戲。

## 2026-10-17 R69：新遊戲兩背景正式接線

規格069 R69限定CONFORMED，難度人物卡與國家旗卡背景正式接線，合計72張生成原PNG／清冊73檔、58Go／41綁定。7個頂層／26個含子案例測試零skip與go vet通過；20點新來源元件及紙質62點、主選單12點回歸通過。46項正常五語GUI、32個原版狀態與76筆輸入，26813312個背景RGBA及13383312個保留原版RGBA相同。四側至75400000步的CPU、完整RAM、可見索引、DAC、WAV與初始存檔相同，含正式play=true及實際GUI音訊。4種啟動缺件／恢復、73檔封裝白名單與220項拒絕通過；70張繼承原PNG保持。其他圖像、特殊游標、動畫與全量HD未完成，沒有新發行。

先以20點／69輸入建立所有難度與國家來源，再核對隔離原型及READY，最後接正式路徑。
原型46樣本、41狀態／84輸入與正式46樣本、32狀態／76輸入為不同實際操作，沒有混用。
原型未錄GUI WAV；正式另外錄音，四側WAV與實際GUI音訊逐byte相同。
姓名與國家介紹只驗正常進入／撤銷，沒有宣稱完整新世界生成。

READY審查d9ec5a3f150e1069aadf7e690562890902d07747b054a2586fc931bfd02901ec，
正式審查0c0009ba01f30817d3b0f9194ef9822dffa334ad865201e58dc3b25a4cbac601，命令收據見本機hd-new-game-backgrounds-r69/commands-r69.json。
兩張原PNG原樣加入graphics，70張繼承原PNG指紋保持；原版像素、遮罩與錄音不公開。
來源索引更新為72份正式綁定，1552列仍不是完整玩家可見分母。
README正文補新遊戲背景，四張截圖及各自來源保持。

驗證修正：首次Go測試未設DISPLAY，在Ebitengine初始化前失敗；同映像加入有界Xvfb後通過。
原型第一版取樣多含旗卡下方木底、漏掉少量生成框邊，目視後只修正框位，
兩張原PNG保持。第一版GUI提前停止，未記整批PASS；第二版23個測試與46項GUI乾淨通過。

正式第一批移除私有旗標後留下未使用測試變數，Go建置通過但go vet拒絕；
誤在檢查此失敗前啟動的下游第一批測試／GUI／啟動亦失敗，不記通過。
修正變數後第二批曾誤把繼承R68封包的r1路徑改成不存在的r2，
當時Go建置及go vet已通過，只有封包複製失敗；保留原腳本、模組與二進位，
恢復正確父路徑後以同映像乾淨重跑通過。沒有放寬來源、像素、原版狀態或互動條件。

Docker均斷網、UID/GID1000、有限CPU／記憶體／PID及外層逾時，Xvfb有trap。
收尾稽核核對41份正式來源綁定、58個Go檔、72張生成原PNG、288份唯讀原版指紋、
工作清單產生結果、README圖像原指紋、Git素材邊界及擁有權；專案容器清理另由實際狀態核對。
沒有新Release。

收尾稽核首版誤讀來源模型的checker_sha256欄位，實際欄位為script_sha256；修正檢查器後同映像乾淨重跑通過，未改正式程式或驗收收據。最終稽核final-audit-r2.json指紋ed49befeb1857e3ffab6f43d2239de8966d1b55b2312d890a08f70621393e244，41份綁定、58個Go、72張原PNG、288原版指紋、四張README原圖、文件連結、工作清單與擁有權均通過。Docker實際列舉確認兩個工具映像均無遺留容器。

## 2026-10-17 R70：自訂地圖十二張小圖背景

沿目標186／規格069接續CUSTOMIZ.PIK。原版畫面確認四欄分別為陸地比例、地形、溫度與氣候，
每欄三種，合計81種選取組合。先以正式R69程式正常X11操作取得17份原圖樣本，
再以每次只改一欄的順序驗證全部81組，不透過記憶體注入。
原PNG由內建imagegen生成，保留十二張卡片構圖及既有定稿畫風；
完整提示與指紋在本機generation-r1.json。正式素材數保持72，待READY後才正式接線。

R70來源驗證修正：第二批89份樣本的有／無觀測原版狀態及存檔相同，但第65點起已進入難度頁，
不能算81種自訂地圖驗收。輸入收據確認134800000步按下，135600000步先移到頁尾才放開；
牆鐘80ms不保證原版已收到放開，造成拖曳到完成區。獨立來源檢查器在第一個錯場景立即拒絕，
未放寬來源門檻。路由回查實機方法，沿既有tools/gui_step_input.sh契約改為步數與
dos_mouse／dos_input_count明確確認按下及放開，放開送達前不移動。原版程式保持。
第三批已驗前兩組送達，因估算新增送達等待可能超出原260000000步預算而主動停止143，
不記PASS；第四批只提高有界步數預算到800000000及外層1200秒，沿同一映像與確認機制重跑。

第四批89點／350輸入乾淨通過，81種選項組合的四個框位均符合實際點選。
原版有／無觀測及GUI同狀態，固定解碼64000格與完整色盤相同。
獨立模型驗3405250事件、70132游標還原及81組字形／邊框集合，前景之外整張PIK相同。
82個完整畫布指紋包含操作欄綠／黃色差異，保留原版顏色，不猜選焦點。

第一版隔離GUI32項五語、十二張卡片及取消通過，但目視見底排上方殘留生成框線，
視覺審查記FAIL。只擴充生成框位以包含外框及陰影，原PNG未改；第二版重驗中。
第一版Go元件已核對89點／350輸入及85520512個RGBA、完整原版狀態，
最後統計誤讀不含dos_input_count的end物件而以0比較，整批記FAIL。
改讀原版頂層已驗350筆輸入，未放寬狀態或像素條件，與框位第二版一起乾淨重跑。

## 2026-10-17 R70：自訂地圖十二張小圖正式接線

規格069 R70限定CONFORMED，自訂地圖十二張地圖／景觀卡背景正式接線，合計73張生成原PNG／清冊74檔、59Go／42綁定。10個頂層／42個含子案例測試零skip及go vet通過；89點／350輸入驗81組選項與85520512個RGBA，R69新遊戲20點、紙質62點及主選單12點回歸通過。32項正常五語GUI、23個原版狀態與84筆輸入，21490960個背景RGBA及7676752個保留原版RGBA相同。四側至98600000步的CPU、完整RAM、可見索引、DAC、WAV與初始存檔相同，含正式play=true及實際GUI音訊。4種啟動缺件／恢復、74檔封裝白名單與223項拒絕通過；72張繼承原PNG保持。其他圖像、特殊游標、動畫與全量HD未完成，沒有新發行。

第三版原型28個守門案例、32項正常GUI、27狀態／81輸入及Pillow像素通過；
原始89點／29案例的來源及狀態證據保留於第二版，已核對兩版memoryWrite至paintBackground逐byte相同。
正式另外重跑89點、全部42案例及23狀態／84輸入，沒有借用原型的RGBA或音訊作正式通過。
兩份正式代表畫面目視通過，生成原PNG保持；只是記憶體取樣使用完整木紋空隙，沒有重編素材。

來源清冊延伸腳本首兩版誤把新欄位插入較早的巢狀sum指定，編譯階段拒絕且未寫入公開工具。
確認存在兩個同式指定後，第三版改定位最後的全域指定，乾淨通過；沒有放寬資料或來源條件。
一次工具自動權限審查逾時而未執行準備命令，改用工作樹檔案編輯建立同一腳本後完成，沒有受阻操作。

READY審查f156216235387b758f1109c33760cb156543670a58f116b3ae19a8ac2384b4e9，
正式審查8b384068a1c490d0e6f5f95162b481cdc17ce8c247ab6101bc97a5e75007c357。
完整命令在本機hd-custom-world-background-r70/commands-r70.json。
原版參考、完整RAM、遮罩與錄音不入Git；新原PNG、完整提示與清冊納入graphics。
README本輪新增自訂地圖的正式畫面，既有四張原PNG與逐圖來源保持。
沒有新世界生成、動畫或跨平台的擴大完成聲明，沒有新Release。
Docker使用斷網、UID/GID1000及有限資源，Xvfb有trap；收尾另核對容器、288原版指紋、擁有權與Git邊界。

收尾稽核final-audit-r1.json指紋cda6b48deb352bcb72c2784fe008ae6c06196b9fccb5afb1e98f0824d23fd872。
42份正式綁定、59個Go、73張生成原PNG、288原版指紋、四張既有README原圖與工作清單均通過。
兩個工具映像實際列舉均無遺留容器。程式與原稿先提交，再以該程式commit登錄README新圖來源。

R70程式與第73張生成原PNG已以d6061ce提交並推送main。README新增自訂地圖繁中HD畫面，原樣複製正式程式的標準顯示診斷PNG，與實際X11遊戲區逐byte相同，含十二張卡片及連續木紋。來源程式d6061ce；四張既有原PNG及各自來源保持。沒有新發行。

README收尾稽核readme-final-audit-r1.json指紋2a435d028ef600a5e342c8c78f0e5ff105a843c4f3b869d40a8d630842879da2。
五張原圖與逐圖來源通過；新PNG與正式擷取全檔相同，73張生成原稿均已受Git追蹤。
新實拍已加入單檔白名單，原版參考與其他候選仍不公開；兩個工具映像均無遺留容器。

## 2026-10-17：R71單位小圖像正常來源研究

接續全量HD，新增131個ICONS候選的唯讀組裝器、獨立逐寫檢查器與規格070 DRAFT。
正常歐洲港口選單只命中既有31種；改走百科23種不同條目，確認80種來源，其中49種尚未正式接線。
35截點、353筆實際輸入、196次繪製與5048144事件重建通過，239次同值後畫亦撤銷來源。
至601800000步的CPU、完整RAM、可見索引、DAC與初始存檔相同，六反例拒絕。
Go組裝與go vet通過。沒有修改正式執行期來源，沒有重跑或擴大既有正式測試的聲明。

百科首版探索重複火炮，因原版返回清單會重設選取列；修正正常方向鍵操作後重跑。
最後一次選取回到首列，實際為23種不同條目。
港口檢查初次沿用舊路徑的COLONY00.SAV預期，改為本次只讀取的COLONY09.SAV後，同一模型乾淨重跑。
這些是驗證腳本問題，沒有修改遊戲或放寬來源證據。
生成原型與格式選擇保持待確認，不將五艘船候選加入正式清冊。

公開來源索引只附加80筆數值及雜湊，1552筆既有資料與73張素材連結逐欄保持。
規格070、目標186、目前狀態及#63本機工作清單同步；#63仍in_progress，未操作遠端Issue。
README原五張實拍保持，修正目前範圍摘要的舊數字。
原版資料、生成候選、完整RAM與原始收據均不加入Git，沒有新Release。

收尾final-audit-r1.json指紋e9d404d86dd01c3b000c4ee7c0df4473f9731c7e30194692f74647e4c4fb4084。
73張生成原PNG、288份原版、工作清單、文件入口與擁有權通過。
Docker採斷網、UID/GID1000及有限資源，Xvfb有trap；兩個專案工具映像均無遺留容器。
全量HD仍未完成，接續49種來源的生成素材與正式接線，世界單位、動畫及其他來源繼續由目標186追蹤。

## 2026-10-17 R72：五艘船的單幀原稿與正式百科HD

規格070 R72五艘船限定CONFORMED，正常百科的商船、帆船、私掠船、快速艦與戰船已接線。合計78張生成原PNG／清冊79檔，59Go／42綁定。4個頂層／248個含子案例測試零skip及go vet通過；五船24點／109輸入與100個來源反例、既有31來源49點回歸通過。15個畫面共15360000個RGBA全等；正式109項GUI中100項五船畫面驗343040個來源RGBA、84960個游標RGBA與101710048個區外保留RGBA。264筆實際輸入四側至335800000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。6種啟動回退／恢復、79檔封裝與238項拒絕通過；73張繼承原PNG保持。679格有效來源中653格實際HD繪製，26格沿原alpha透明保留。世界單位、移動、戰鬥與動畫未由百科驗證外推，全量HD未完成，沒有新發行。

沿用已核准的一幀一張原PNG格式。五艘船分別生成，graphics原檔與工具輸出全檔相同，完整提示、參考指紋及權利記於manifest。圖集提問尚未回覆，其候選、BFS延伸取樣及格式原型保持私有DRAFT，沒有阻塞既有格式的授權工作。

READY審查5815102fd348b0f8507ed594b9396e3fd49336230f77c6ab86b4ee5e97446f6d在正式接線前完成。只追加五筆來源資料及原稿，不改既有取樣與逐寫演算法。正式審查fb5400b2190c423b5875e64eec63fcf3b9b4544baceb87b7e80e3dc91117b978，來源索引d01874681e0e8d8ea8884a895c4ddfe2bc4a64b74da715a22946e4364fef9410。來源研究及實作的RAM還原信用分開，百科游標只在輸出畫面覆蓋，主畫布沒有本批RAM還原正例。

驗證腳本修正均保留初次失敗：舊小圖像測試把新增主選單背景算入來源區外，R70舊程式亦重現。改比較小圖像層本身，原版49點、547保存、422還原及260游標配對保持。啟動預期由31改36，新五幀另走24點原版路徑與100個真實來源反例。第二版測試啟動器曾誤呼叫第一版腳本而撞到既有輸出目錄，改回正確第二版腳本後，同映像乾淨跑完248項，沒有放寬正式守門。

GUI像素檢查第一版誤把owned遮罩當作painted遮罩，兩者差26格原alpha透明；改依原契約分開驗。商船原點為[11,33]，其他為[10,33]，原先統一原點漏一欄；改從獨立來源local與位置推得，沒有更動正式座標。公開GUI檢查器初版漏匯入base64，補齊後同映像100項乾淨通過。正式PNG、來源、alpha、像素與原版狀態條件皆保持。

封裝最初只加入指紋清單而漏目錄集合，完整白名單測試前補齊五檔，最後79檔接受與238拒絕通過。新行程實際驗五船各一種缺件／錯件／連結及完整恢復，原HD偏好、語言與設定凍結保持。無新Release。

Docker全斷網、UID/GID1000、有界資源與逾時，Xvfb均有trap。收尾核對全部288原版指紋、78張原稿、來源綁定、文件入口及Git邊界；容器清理依實際列舉另記。README新圖於正式程式提交後以該commit登錄。

R72收尾稽核d2073b216cadc384442523824f78d84dc4a9249cda3ae5432835d99be472aacc，78張原稿、73張繼承清冊紀錄、288份原版、42綁定／59Go、1552筆來源、五張既有README原圖、工作清單與擁有權通過。重跑命令commands-r72.json為611c6080e0475486a286eb7a8265f62a66cd3219d28c90fb9dd39a1bf47790fb。兩個工具映像實際列舉無遺留容器。

R72程式與五張船艦原PNG已以ee66e1f提交。README新增繁中帆船百科HD實拍，原樣複製正式顯示診斷PNG，與實際X11遊戲區全等；來源程式ee66e1f、78張素材。既有五張PNG與逐圖來源保持，新增圖片採單檔白名單，沒有加入原版參考或候選。

README收尾稽核69e50b7e33c93cb4bf0cd17a976c3a3962f7eeea5fb4f503b461c38549a99fd2。六張實拍與各自來源通過，既有五張原檔與metadata逐欄保持。擷取使用R1建置，正式驗收使用R2建置；兩者所有非測試Go來源與二進位相同，metadata分別保存實際擷取及驗收建置指紋。

## 2026-10-17 R73：三種車輛／火炮原稿

接續44種已知未接線來源，先生成008篷車、009火炮及016寶藏車，使用內建imagegen，逐幀單張PNG與alpha保持。
三張原稿已原樣複製至本機R71根的candidates，UID/GID1000；完整提示、來源與框位見r73-three-unit-generation-r1.json。
生成紀錄30ea5503d6b5eb0b689dcb7c0c8d33d00a14a03728eed295c9fbd1f7563d4e81。原版內容框分別為[0,4,14,16]、[0,9,14,16]及[0,7,14,16]。
目前只完成原稿與幾何量測，規格仍DRAFT，正式數78保持；正常來源／游標、READY、正式接線與驗收接續。
複製紀錄首版誤將shell引用用在Python字串，語法檢查拒絕且沒有寫入；改正JSON字串引用後同映像完成，沒有修改圖像或降低驗收。

## 2026-10-17 R73：三種車輛／火炮正式接線

規格070 R73三幀限定CONFORMED，貨車008、砲台009及寶藏016正式接線，合計81張生成原PNG／清冊82檔、59Go／42綁定。5個頂層／259個含子案例分批完成，所有計入案例零skip及go vet通過。新三幀18點／86輸入與60個來源反例、既有31來源49點及五船24點回歸通過；新9畫面9216000個RGBA與繼承五船15360000個RGBA全等。正式69項GUI中60項五語原版／HD及游標畫面驗215040個來源RGBA、50720個游標RGBA及61068416個區外保留RGBA。153筆實際輸入四側至223000000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。4種啟動回退／恢復、82檔封裝及248項拒絕通過。78張繼承原PNG保持；原始290格在後畫字形撤銷3格後剩287格有效，原alpha保持。世界移動、戰鬥、受損砲台065及動畫未由本批外推，全量HD未完成，沒有新發行。

來源READY修訂1f01163ee78a7c042f696f9fa8a55a63b382f80dc1f76fea428204658623ebec，容量READYaea6ea7dea862cbc8066a6669175461694e61e5129d892eb100cc1bd2f059662，
正式審查ba17a1b0aadbdcb5cb5d535685df0498630e6fdbd969cfbed183afd736844fee。
三張原稿與alpha保持，graphics清冊保存完整提示。來源表在既有36幀後追加三幀，取樣及來源撤銷演算法不變。
清冊268375bytes超過原256KiB，先補READY容量契約再同步執行期與封裝至512KiB，新增超限拒絕案例。

驗證修正保留失敗：初版讀錯manifest的prompt欄位，實際為generation_prompt，檢查在任何正式寫入前拒絕。
RGBA工具增固定profile時重複替換同式而在編譯前拒絕，修正後重生；沒有寫出半成品。
第一批正式建置通過，測試／GUI／封裝因清冊容量拒絕，停止該批；不授予通過。
第二批GUI按原圖141格預期貨車，獨立模型實為138，三格已被0D21:012C字形後畫撤銷。
只修正驗收預期，正式來源、撤銷、取樣及PNG不變，修正前後程式二進位皆為fa4307f1388e3bfd953359b501a0513ea0a62c2ba47214156895fb22a7f4f11f。

第二批原31來源測試把新增第008幀算成舊路徑必測來源而拒絕，改按規格065明列31幀，其餘走各自正常路徑。
同批套件500秒期限在載入／啟動測試完整通過後到期；這是驗證工作預算，不記產品缺陷。
後續按案例分開有界重跑，5項頂層／259項計入案例全部完成；未完成與失敗案例保留但不算通過。
實際擷取使用R3，驗收使用R4；R2／R3／R4非測試Go來源與二進位全等，各自保留來源指紋。
舊31幀49點／53輸入、547保存、422還原與260游標配對保持；五船24點／109輸入與100來源反例及15360000RGBA回歸通過。

本批正常GUI採play=true，69項含60項三幀五語畫面，全部X11遊戲區等於標準診斷PNG。
四側使用實際153筆輸入至223000000步，WAV另與實際GUI錄音相同，存檔檔名集合及內容全同。
source-index81只增加三幀正式連結與驗收欄位，原始1552列及78份既有綁定逐欄保持。
原版圖像、完整RAM、遮罩及錄音只留本機，未選圖集仍DRAFT。沒有新Release。
Docker均斷網、UID/GID1000與有界資源，Xvfb有trap；最後原版指紋、擁有權、Git及容器清理另稽核。

R73收尾稽核87b60e2e906c28d84a9caeff0a12203e2c5ce677573b8994fafdaec92145fef5。81張生成原稿、78份繼承清冊紀錄、288份原版、42綁定／59Go、1552筆來源、六張既有README原圖、工作清單與擁有權通過。重跑命令commands-r73.json為4de440ddfb94ee5e3e3b1b2b06a056053f7f83616dc52ff009b18d08a774a112。兩個工具映像實際列舉無遺留容器。

R73程式與三張生成原PNG已以6bccc35提交。README新增繁中貨車百科HD實拍，原樣複製正式診斷PNG並與實際X11遊戲區全等；來源程式6bccc35、81張素材。既有六張PNG與逐圖來源保持，新圖採單檔白名單，原版參考及未選候選不公開。

README收尾稽核a56ac60217e881f85e5e4cd7ef8a5a10f7c162733a45a935cbe97160a4018b57。七張實拍與逐圖來源通過；既有六張原檔及metadata逐欄保持。實際擷取R3、驗收R4的非測試Go來源與二進位相同，兩份建置指紋分別保存。dosgolem隔離副本的upstream推送位址保持DISABLED。


## 2026-10-17 R74：22幀殖民者百科HD限定驗收

- 規格070 R74正常殖民者百科22幀限定CONFORMED。合計103張生成原PNG／清冊104檔，59Go／42綁定；既有81張原稿與清冊紀錄保持。六類Go測試含子案例去重329項完成，計入案例零skip；完整副本逐檔拒絕323項、小圖像資源245項及go vet通過。54點／81輸入、440個真實來源反例及46080000個RGBA全等；既有31來源49點、五船24點、三類18點回歸通過。正式63項GUI中54項為五語原版／HD及22幀游標懸停／返回，驗2405376個來源RGBA、55648個游標RGBA及52737536個區外保留RGBA。97筆實際輸入四側至123800000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。4種啟動回退／恢復、104檔封裝及314項拒絕通過。1381格來源中1353格實際HD繪製，28格沿原alpha透明保留。世界移動、戰鬥與動畫仍待驗，全量HD未完成，沒有新發行。
- 原PNG及完整生成提示加入graphics，清冊338537bytes，仍限512KiB；每張PNG限8MiB。只追加來源資料，不改正式演算法、規則、存檔、語言或互動範圍。
- 正式程式六版二進位一致，SHA-256為7a9470f550b7160ff5ee83dcc83d3fc75ffcea5884d578cc58592fed6684903a。驗收審查70349035b3ca433349d4fe3a6fc8219acef55e1231eadb714443f94500adb6f9；來源索引904f7d6f25f16f640cd7382ea3b867c58662e02c326ea3fa3d3f8e225372d0f6。
- 所有本機收據、精確入口與工具雜湊見hd-sprite-batch-r71/commands-r74.json，SHA-256為e47b9de2dc545f13e5501dbe0704cea579b4504eadfbddff00155267b0654848。四個完整正常來源測試沿R2，小圖像資源沿R4；大資源112個R4完成子案例加R5剩餘208及R6地形079補測3項，全聯集323。中斷父行程、枚舉行程、舊數量預期與逾時複製嘗試均不計通過。
- 勘誤：舊Go資源副本漏複製部分正式圖像及CUSTOMIZ.PIK，相關R72／R73逐檔負向信用撤回。新副本先完整正向載入，每案以新Machine檢查全載入拒絕及原版RAM不變，再逐byte還原所有檔案。沒有硬連結或寫入正式素材。
- 第一次測試誤指R73腳本，失敗輸出覆寫本機r73-vehicles-tests-r3.jsonl。原log不再符合歷史雜湊；原彙整、18點圖像及正式審查保持。失敗另存r74-stale-test-entry-r1.jsonl／JSON，本輪重驗三類18點與9216000個RGBA。
- 全131來源檢查器在游標遮擋點拒絕最終可見等式，分類為驗證範圍不合，未放寬或計入。R71來源正向證據、新22幀完整RAM模型與完整游標表面、正式來源測試及實際GUI各自通過。
- R75其餘19幀原稿已生成，本機清冊r75-unit19-generation-r2.json，SHA-256為5e0f75101623cbdc507df727906090300af5fd2786dea1556ef88981cce83f7e；維持DRAFT，尚未入正式層。新正常操作基準採原版模式擷取，未冒稱HD完成。
- 本輪不建立tag或Release。提交及README實拍另記於本節收尾；Docker與擁有權須完成最終自檢。

R74提交前核對：103張原稿／104檔、81張繼承圖、288個原版輸入及1552筆來源事實均通過，收據r74-final-audit-r1.json為a2ec176aff411a7e39e025cdf985dff7b7772f42c338da075b30cf0041b8e358。UID皆1000，未發現root-owned檔案或同名.md目錄；私有dosgolem維持82a14b2且upstream push為DISABLED。R74已完成的容器均隨--rm清除，僅R75正常來源基準仍在有界容器執行。

R74程式與22張生成原PNG已以38ee34f3c13504cf3d689fdbe5e6da4df3570d25推送origin/main。README新增繁中殖民者百科實拍，原PNG SHA-256為2b89807308bfa4f7c26786160f87aa30b39bda7f8450bba828b3424aaa22c73f，原始bytes與X11遊戲區全等；檢查收據r74-readme-capture-r1-check.json為03c95143f417276a799cbcf5b122ebc95bb59741310b6ba6008227f6d27a67c3。七張既有PNG與逐圖來源保持，共八張，未改目前發行版。R75正常基準61點／137輸入已完成，實際GUI終點310000000步，最後截點309600000步；三側唯讀來源觀測接續執行。

R75接線前來源審查：61點／137輸入、19次完整繪製及80232事件通過獨立原版模型。第065幀48筆游標反向配對還原，其他18幀本批無還原正向樣本；RAM保存／還原及主畫布轉送皆0。1555格有效來源中1539格可繪，16格保留原alpha透明；112幀local 58由原版後畫撤銷。READY收據3a0c4d06a85d481a2fb380c066f8e1324133be20971466b4d950ef0c7eed231a。據此在既有61槽尾追加19槽，正式演算法保持，122張原稿／清冊123檔正在驗收；目前已驗完成數仍103。


## 2026-10-17 R75：其餘19幀正常百科HD限定驗收

- 規格070 R75其餘19幀在正常14頁百科限定CONFORMED，含受損砲台、步行與騎乘人物。合計122張生成原PNG／清冊123檔，59Go／42綁定；103張繼承原稿與紀錄保持。七類Go測試含子案例去重457項完成，計入案例零skip及go vet通過。大資源131項與小資源321種拒絕檢查通過；另249項大資源清單案例未重跑，R74的323項信用維持原批次。新61點／137輸入、380個來源反例及53248000個RGBA全等；既有31來源49點、五船24點、三類18點與22殖民者54點回歸通過。187項正式GUI中178項為14頁五語原版／HD與19幀游標操作，驗710656個來源RGBA、116416個游標RGBA及181146160個區外保留RGBA。232筆實際輸入四側至336600000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。4種啟動回退／恢復、123檔封裝及371項拒絕通過。1555格來源中1539格可繪，16格原alpha透明保留；112幀另有1格由原版後畫撤銷，065幀48筆游標配對還原已驗。世界移動、戰鬥、其他圖像與動畫仍待驗，全量HD未完成，沒有新發行。
- 原稿及完整生成提示加入graphics，清冊400982bytes，仍限512KiB；PNG各限8MiB。正式二進位1f0f2418af3c5164e74c8d037161f27be28e11e00d3bdf1fd3a533ddf62a222c。只追加來源表及清冊指紋，原正式演算法保持；資料及程式一致性收據4a3ac58a393669d9ba1c47ff4df1ee5a3ba1982dd2fba7e28a5bdf97a2fb12ba。
- 原稿取樣、原版逐寫、19幀61點及380反例、178項五語畫面與四側實際GUI重播均通過。正式審查a74c8dece4c569c9ebb1d0947a5b3a892eca8ad676225d3b086689575ae4fdf5；來源索引aa66dd0c11f82de0d12bab4c10d64a94c8da796b14917d1f47d0edaefe1c0a73。精確容器、命令及工具雜湊見本機commands-r75.json，SHA-256為b29b951daea86429e55f4a42f542f39bb1fc2165fc804838b47394ea3d193602。
- 失敗分類：R1車輛因同頁新增065而超出舊三幀測試遮罩；用既有isolatedArt只繪舊三幀，新舊砲台由正式GUI完整核對。R2單案例漏設TEST_HD_RECEIPTS，於模擬前拒絕，R3入口補齊後通過。R1小圖像資源在PNG解碼超過900秒，未計任何未具名部分信用；改為319具名子案例及兩種無效呼叫，保留R3已完成299個子案例，另以R4七批補完20個，全聯集完成；兩個逾時父行程不計信用。三份原失敗log保留，已完成且程式相同的四個R1來源測試未重跑。
- 小資源每批先正向載入全部79張原稿，子案例以完整自有副本執行原錯件操作，拒絕後逐byte復原；4 CPU／8g上限、四worker、R3每批至多32案例、R4補測每批至多3案例，均500秒。大資源只計131項，本批其餘249項清單案例未重跑；R74的323項信用不擴成R75全380項。
- Source槽位uint16及每幀256格界限保持，80槽／最大14×16未越界。第065幀48筆游標配對還原只限本批正常路徑，其他18幀無還原正向樣本；RAM保存／還原與主畫布轉送均0。
- 目前原版可見分母仍未知，其他51個ICONS候選、31個未接線PIK與其餘圖像、世界移動、戰鬥及動畫仍待驗；沒有新tag或Release。README新圖於本批程式commit後附實際程式指紋；最終輸入、擁有權與Docker清理另核對。

R75提交前自檢通過：122張原稿／123檔、103張繼承紀錄、288個原版輸入及1552筆原始事實保持，收據r75-final-audit-r1.json為f6833a0ad11a5609d57f8b1344e6009c36f34d756ad75b51d9d0bdd497568a03。公開RAM觀測器與檢查器逐byte等於已執行腳本；42來源綁定符合現行程式。UID皆1000，未發現root-owned檔案或同名.md目錄；dosgolem維持82a14b2、工作樹乾淨且upstream push為DISABLED。兩個本專案驗證映像均無執行中或停止容器，未清理其他專案。小資源R3兩個父行程500秒期限紀錄保留，44個已復原子案例計入；R4僅補20個，完整聯集319檔案反例加兩種無效呼叫。

R75程式與19張生成原PNG已以8df4de67b2f592733f163bf4093ea51b4ee5be73推送origin/main。README新增繁中龍騎兵百科實拍，原PNG SHA-256為207be0ba41d1440d662fc56ccac6ba49b635194818240557d166d0059032e326，bytes與實際X11遊戲區全等。檢查收據r75-readme-capture-r1-check.json為8ed7e3df59cbd3187bf36029a6254bbe93343350609ece12d52206de477a8fc5；八張既有PNG及逐圖來源保持，共九張，未改目前發行版。

## 2026-10-17至18 R76：殖民地與歐洲港口背景HD

- 規格069 R76殖民地部分背景與歐洲港口背景限定CONFORMED。合計124張生成原PNG／清冊125檔、62Go／45綁定；122張繼承原稿與紀錄保持。31項含子案例Go測試及兩項既有新遊戲回歸零skip，建置與go vet通過。19點／45輸入及19456000個完整RGBA相同；107項正式GUI含60項HD與47項原圖，獨立原版來源模型67點，驗38409504個背景RGBA、78720個游標RGBA與45583104個原圖模式保留RGBA。五語、兩背景游標及招募／購買／訓練開關均有正例。61筆實際輸入四側至158400000步，CPU、完整RAM、索引、DAC、WAV及存檔與實際GUI相同，含play=true。5種啟動回退／恢復、125檔封裝與377項拒絕通過。其他圖像、動畫與完整HD未完成，沒有新發行。
- 生成原稿colony-000.png及europe-000.png原樣保存1586×992 RGB，完整提示、參考指紋、
  原版來源與取樣矩形記入graphics/manifest.json。未裁切、縮放或重新編碼原PNG。
- READY 3aec3bbc6a45b61c4a79943b4f67f6c8a0f1b3e3dcfdfc55243d11927dabc2ed先於正式實作。
  正式審查1cac135ef4f39a48aeefbbd56ae2e166a79d069ad090768cb6fd16607e8f9e6e，二進位d4b7c94d34311c3af7f9ebc19b1bea8a7c475ce278a3e96fcb212289d16f0904，清冊1dba5fd9a5bbf5a8c76861e56709525305857a9a77ae9c988b564119f636333c。
  來源索引21d1e68acac16a3568f6ad2e524f59e520ad733d60f779935b0bf726884719fd只增補兩來源，1550列舊證據與122筆舊綁定保持。
- 完整重跑命令及收據入口見規格069的R76限定CONFORMED；本機根hd-scene-backgrounds-r76。
  來源觀測不寫原版記憶體，全部288個原版輸入SHA相同。公開內容只含生成原稿、
  程式、來源指紋及經授權的實拍，不提交EXE／PIK／SS／RAM／IDX／DAC／WAV／存檔。
- 失敗保留：研究GUI重複E撤回港口標籤信用；正式GUI R1關閉後實體指標進入遊戲、
  R2 PNG壓縮逾時、R3原版畫面搬移尚未完成均不計通過。
  R3固定24筆輸入於59200000步有218個游標外不合點，接續20個無新增輸入的固定截點均完整相符。
  守門未放寬；R4設定暫停期間先移出指標、無壓縮抓圖與有界等待後107項通過，沒有重試取巧。
- 獨立RGBA檢查修正Pillow浮點邊界為READY整數中心取樣。
  研究原圖一次保存上一幀，80×84差異區位於本批來源外；沒有將該研究原圖作完整輸出oracle。
  19點完整RGBA仍嚴格重算，正式47項原圖也核對翻譯安全矩形外的原版RGBA。
- 122張舊原稿與全部清冊物件保持，沒有宣稱整套歷史測試重跑。
  31項新元件、兩項新遊戲回歸及所有本批GUI／來源／RGBA／音訊／存檔／封裝收據已完整結束。
  完整HD、動畫、其他場景與新發行仍未完成。README新圖於本批程式commit後另附實際程式指紋。

R76提交前自檢：1550列舊來源、122張舊原稿／紀錄、288個原版輸入與45個正式來源綁定保持。全工作樹find未發現root-owned檔案或同名.md目錄；隔離dosgolem工作樹乾淨，upstream push維持DISABLED。兩個專案測試映像無執行中或停止容器，沒有清理其他專案資源。公開原稿檔案屬UID1000，原版EXE／SS／PIK／存檔與本機研究輸出未追蹤。

R76程式與兩張生成原PNG已以dbfc95fc2b98654f9f4cf3d0abac946730bfbfce推送origin/main。README新增同版繁中殖民地港口及歐洲港口實拍，共十一張；兩檔原樣複製且與實際X11遊戲區全等，原九張PNG與逐圖來源保持。來源、正式程式指紋及驗收範圍記入readme-captures.json，沒有新tag或Release。

## 2026-10-18 R77：八種報告背景HD

- 沿已定稿畫風完成REPORT1至8八張生成原PNG，逐byte保留於graphics。
  第5張1585×992，其餘1586×992，完整提示、來源、權利與指紋入清冊。
  三張未選寬幅候選留本機，正式圖經imagegen重構圖，未裁切、拉伸或重新編碼。
- 原版研究確認八來源直接解碼到主畫布；只擴充背景來源與解碼基址守門，
  舊COLONY／EUROPE暫存來源、原版資料、規則、輸入、音訊與存檔保持。
  清冊132張原PNG／133檔，63Go／46綁定。
- 163個具名Go案例按R1／R2聯集完成、零skip，建置與go vet通過。
  正常27點全RGBA、既有背景19點全RGBA及新遊戲20點回歸通過。
  149項實際GUI含82HD／67原圖，99點獨立來源與五語、游標、文字字底核對通過。
  四側74筆實際輸入至262000000步的CPU／完整RAM／索引／DAC／WAV／存檔和GUI相同。
  5種啟動回退／恢復、133檔封裝與401項拒絕通過。
- 驗證修正保留原失敗：Go預期終點把最後截圖步數誤作關窗終點，僅更正測試為192600000；
  正式Go與原稿保持。正式觀測首版達6000000日誌上限，改用公開--ram-only省略檢查器未用的顯示記憶體事件。
  完整RAM前綴3684672筆逐byte相同，99個完整原版狀態核對通過；
  第一版已完成控制保持原producer指紋，不計部分觀測信用。
- 四側producer留下舊檔名r76-scenes-replay-r1-check.json，實際位於R77本機根。
  改名複製被自動審查拒絕後保留原名，以四個實際command.json、輸入SHA、
  74筆／262000000終點及逐檔狀態／WAV／存檔重驗確立R77範圍。
  未改名或替換成其他批次收據。
- 正式審查553827bbd2636765fa7d5be57a814bcaf7829911efba4de26ed7e950505e5028。
  清冊與來源增補只更新1442至1449，其他1544列、124張舊原稿／紀錄及288份原版輸入保持。
  README先更新穩定素材摘要，本批實拍將沿正式commit補入，原十一張來源保持。
  完整命令與收據入口見規格069；原版研究輸出不入Git。
- 全量HD仍未完成；21個PIK、51個未觀測ICONS候選、其他格式、特殊游標、
  世界移動、戰鬥、事件圖與動畫待接續。沒有新tag或Release。
  Docker與擁有權收尾檢查隨本批提交記錄。

R77提交前核對：46筆來源綁定與已驗R2建置一致，132張原PNG指紋相符；只更新八筆來源，未追蹤原版資料或本機研究輸出。完整工作樹無root-owned檔案或誤建Markdown目錄，WORKLIST由JSON重生後保持。所有本批一次性容器已結束並刪除，未重建映像或清理其他專案。

R77正式接線已commit並push main：0bce890d3b7ea22a1870870548a3c5854f83bbab。
八張生成原PNG、清冊、正式來源及驗證工具已進GitHub，原版輸入與私有收據不入Git。

README追加兩張實拍，直接複製正式R2視窗呈現，沒有重編PNG：
勞動報告為116400000步的gui.display-162.png，
經濟報告為139600000步的gui.display-222.png。
再次逐byte核對X11遊戲區；每張記錄正式commit、二進位、132張素材、
manifest、CONFORMED、GUI、獨立像素及四側收據指紋。
舊十一張PNG與十一筆來源物件保持，總計十三張。未宣稱全量HD或新版已發布。

## 2026-10-18 R78：國會室內與計分背景原型

- R77報告實拍已commit及push main：e35d625，README共十三張，舊十一張原PNG與來源物件保持。
- 沿使用者全量HD授權接續CCBKGD.PIK與WOODPANL.PIK。三次完整解碼及27點原版來源核對通過，
  公開唯讀檢查器不安裝HD；缺原版SKIP／exit77且不產生假收據。
- 生成室內及木紋候選，原PNG逐byte保留在本機R78根；室內v1太寬，
  v2由imagegen重構圖為1586×992，不拉伸或重編原稿。
  兩張英文原型保留49424／52512個原版前景RGBA，已目視構圖與人物、圖表、游標保留。
- 首版研究因未限完整IDX，把同型writer的其他緩衝寫入歸到最後PIK，來源檢查拒絕；
  修正為完整64000連續bytes與固定IDX才識別來源，其他短run不授予身分。
  JSON布林值與複製檢查器括號的腳本錯誤在執行前修正，原錯誤入口保留，不屬產品缺陷。
- 現行132張原PNG、清冊、1552筆來源索引、正式Go及46筆建置綁定保持。
  規格維持DRAFT；原型未計入全量完成，接續READY審查與正式顯示驗收。
  研究根、公開工具與收據指紋已掛入規格069，未新增同義狀態文件。

R78研究收尾：原版與DRAFT候選維持本機；沒有root-owned檔案或誤建Markdown目錄。Docker一次性來源檢查及原型容器均已結束，沒有背景Xvfb或新映像；本批未動其他專案容器。正式132張及十三張README實拍保持。

## 2026-10-18 R78：國會室內與計分背景正式接線

- 審查後將兩張原PNG原樣放入graphics/ccbkgd-000.png及woodpanl-000.png，
  清冊134張原PNG／135檔、64Go／47綁定。132張繼承原稿與完整資產物件保持。
  WOODPANL以明列第二畫布接受兩個已證實解碼基址，其他來源與資源上限保持。
- 建置、go vet及196個具名Go案例零skip通過；正常27點全RGBA、舊19點全RGBA、
  新遊戲20點、96個完整副本來源／檔案反例通過。
  37項五語GUI與27點獨立來源、17138160背景RGBA、23616游標RGBA、
  433008室內原版前景RGBA及19127232原圖模式保留RGBA通過。
  34筆實際輸入四側至100200000步，完整CPU／RAM／索引／DAC／WAV／存檔與GUI相同。
  5種新行程回退／恢復、135檔封裝與407項拒絕通過。
- 載入選單八點守門未恢復，原GUI r1保留不計信用。原版26個差異追到VGA複製後的
  主畫布填色／字形寫入，沒有改成寬鬆畫布判斷。READY r2把本批HD信用限於國會與計分頁，
  載入選單HD仍掛在原全量目標，不降低Issue #63完成條件。
  九個室內HD點同一人物姿態，保留原版人物，不把它當新人物或動畫完成。
- 驗證工具修正：Xvfb改用映像原生autorepeat參數；來源CLI scope變數獨立保存；
  啟動工具以草稿／拒絕收據確認按下，替代盲等0.08秒；零文字items不排除任何文字區。
  各原失敗均保留且不計通過，正式Go與原PNG不因這些驗證修正改動。
- 現行審查room-score-conformance-r2.json為
  a1049affbd62d15ef7413cd9063e6f0dccb9aafbda199e5a4ee3238e1d38c2de；
  r1保留，r2新增正式室內前景RGBA信用。來源索引只更新120／1551，
  原1552筆事實、其他1550列及132筆繼承資產紀錄保持。
  公開入口、完整命令與收據指紋集中在規格069。
- README先更新134張原稿的穩定摘要，待正式commit後加入兩張實拍並保留舊十三張來源。
  沒有新版本、tag或Release；載入選單、其餘圖像與動畫繼續追蹤。

R78提交前核對：47筆正式來源綁定與已驗R3組裝一致，134張原PNG指紋相符；兩個新PIK的IDX指紋在1552筆清冊中各自唯一。只更新兩列來源，未追蹤原版資料或私有收據。工作樹無root-owned檔案或誤建Markdown目錄；一次性容器已結束並刪除，Xvfb隨擁有程序關閉，映像未重建，未清理其他專案資源。

R78正式接線已commit並push main：d79ec5654fa3376c19f77cd3b142081cef01ac1f。
兩張生成原PNG、清冊、正式來源與驗證工具已進GitHub，原版輸入與私有收據不入Git。

README補兩張實拍，直接複製正式R3視窗的原PNG並再次匹配X11遊戲區：
國會室內74400000步的gui.display-042.png、繁中計分90400000步的gui.display-102.png。
每張記錄正式commit、二進位、134張原稿、manifest、CONFORMED、GUI、獨立像素與四側收據SHA。
舊十三張PNG及十三筆來源物件逐項保持，合計十五張；人物與載入選單限制明列。

## 2026-10-18 R79 讀檔背景顯示來源接線

規格069 R79已發布顯示來源的讀檔背景限定CONFORMED，合計134張生成原PNG／135檔及64Go／47綁定保持。215個具名Go零skip、建置與go vet通過；27點完整已發布來源與27648000個RGBA、既有19點殖民地／港口及20點新遊戲回歸通過。32項五語GUI含18項HD／14項原圖，同輸入獨立原版來源32點；16096592個背景RGBA、1022608個HD場景原版前景RGBA、13460800個原圖模式RGBA與41664個不透明游標RGBA相同，X11共32768000個RGBA全同。31筆實際輸入四側至72800000步，CPU、完整RAM、可見索引、DAC、WAV及存檔與實際GUI全等，含play=true。原版288檔、134張原PNG與清冊保持。讀檔列表及點選後成功訊息背景已可HD；該路徑游標與文字字底仍保留原版，字底接縫待完成。全量HD、其餘19個PIK、51個未觀測ICONS候選、世界移動／戰鬥、其他格式、事件與動畫及新版交付仍未完成。README十五張既有實拍與來源保持。

審查`17128580f3a25ea0b4710f09ddaa4c7cf10bcfc83ff4ec87bef3edd2130ee4e7`，二進位`d385979ee24ec8202f6518a4697a04a21f12a7629150e9991995fd72955503fb`。
首版DS條件不完整、缺xauth外框及繼承包路徑錯誤均保留失敗紀錄；
四側並行r1遭SIGKILL，改逐個執行的r2使用同輸入與上限通過。
未宣稱新的音效卡／人耳驗收。提交前核對134張原稿、288個原版指紋、
1552列來源、Git追蹤邊界、UID/GID與本批Docker清理；既有十五張README實拍保持。
下一項處理已觀察到的讀檔文字字底接縫及原版游標。

R79收尾已驗：原版誤追蹤0、root-owned檔案與異常.md目錄0；專案兩種映像均無殘留容器。隔離dosgolem副本乾淨，upstream推送位址維持DISABLED。

## 2026-10-18 R80 字底與游標READY

已建立32點原版游標VGA當次來源及暫存7656筆sidecar，與正常GUI／無觀測控制CPU、完整RAM、索引及色盤相同。兩個私有原型沿31筆實際輸入重播到72800000步，CPU、RAM、索引、色盤、WAV與存檔皆相同。第二版兩個正常檢查點的背景遮罩與獨立模型相同，列表字底863點、HD游標各82格。透明VGA複製與不透明反向配對模型最高82個未完成點，終點0。規格069／066已READY，審查0b48c02e1ac21824e902bf07e2a18f0956dd7b2ab8ef3b7bf7236967aa57e150；正式程式仍為R79，未知成功訊息字底保留原圖。下一步正式接線、反例與五語GUI。原始sidecar、快照及原型只留本機。

## 2026-10-18 R80 字底與標準游標正式接線

規格069／066 R80已發布字底與標準游標限定CONFORMED，134張生成原PNG／135檔、64Go／47綁定保持。251個具名Go零skip、建置與go vet通過，54個快速案例包含於251內。32點／31輸入至72800000步的獨立來源及32768000個完整RGBA通過；既有27點報告、19點城內／港口、20點新遊戲回歸通過。32項五語GUI含18項HD及14項原圖，32點當次原版來源；16262800個HD背景RGBA、834512個保留原版前景RGBA、13442752個原圖模式RGBA、23616個HD游標RGBA及32768000個X11遊戲區RGBA相同。5152個字底格有獨立來源，透明游標下另21格只回填已驗原版字底，不計HD來源。五語文字、字級及安全矩形在兩模式相同；游標實際進出列表文字及成功訊息。31筆實際GUI輸入四側至80600000步，CPU、完整RAM、索引、DAC、WAV與存檔全等，含play=true。原版288檔、134張原PNG與既有清冊保持。成功訊息其餘字底未知，保留原圖；全量HD、其他圖像／動畫、完整五語及新版交付未完成。

審查`1135c987785e9e07d90aa47f125abe5aebabe4ce5c229fd38a5b07bf33cc110e`，二進位`3b7a7172b48f7c0105f0089da39acb928827f0361097e0c9d0684c98327c45c4`，來源索引`05ad61a4387d9b6b64e0c1cbdc17753a9653bc5be0c3c8a93506afbd1d2a11d9`。
字底及游標原型、來源sidecar和兩份正常輸入均保留；首版研究SHA參數錯誤保留，
以新目錄乾淨重跑。正式r5另補透明游標內已驗原版字底回填，單列21格，
防止替換文字下方殘留舊英文，未授予未知HD來源。
README接續加入已驗列表實拍。提交前檢查原版追蹤邊界、UID/GID與Docker清理；
完整HD及新版交付仍未完成。

R80收尾已驗：原版誤追蹤0、root-owned或異常.md目錄0；原版288檔與134張原稿保持。兩種專案映像無殘留容器，隔離dosgolem乾淨且upstream推送維持DISABLED。四種來源索引錯誤審查均拒絕且未產生索引。

## 2026-10-18 README新增R80列表實拍

直接複製正式GUI的scene-load-menu-zh-Hant-hd，步數35000000，1280×800，SHA-256 e64cfb71d7d3f944feefb11de8ea92831eb6a15ccb2babe10c5f576c85e018b2。X11遊戲區逐位元組相同，程式c97e3a2、二進位3b7a7172b48f7c0105f0089da39acb928827f0361097e0c9d0684c98327c45c4、正式審查1135c987785e9e07d90aa47f125abe5aebabe4ce5c229fd38a5b07bf33cc110e。共十六張，既有十五張原PNG及capture物件逐項保持；未修改134張生成原稿。未知成功訊息字底及完整HD限制保留，沒有新發行。


## 2026-10-18 R81訊息視窗木紋與字底接線

規格069 R81訊息木紋與字底限定CONFORMED。63個具名Go零失敗／零skip、建置及go vet通過；32點／31筆既有正常輸入至80600000步，獨立來源、32768000個完整RGBA及原版CPU／RAM／IDX／DAC／存檔一致。當次9項正常GUI含4HD、5原圖，繁中兩模式與文字內游標移入移出通過；47152個新底紋RGBA、2076格字底來源、5248個HD游標RGBA及9216000個X11遊戲區RGBA相同。24筆當次GUI輸入三側重播至63600000步，含play=true，與實拍的CPU、完整RAM、IDX、DAC、WAV及存檔一致。134張原PNG、清冊135檔、64Go／47綁定及原版288檔保持；只補OPENTILE／WOODTILE兩列來源發布證據，其他1550列及134筆連結保持。PARCH沒有發布正例，維持原有範圍；其他語言排版沿R80，未新增五語GUI信用。其餘圖像、人物、世界移動／戰鬥、事件、動畫、完整五語、實玩影片與新版交付仍待完成。

READY fd3d039cb23437211311d5409eb19d74e540a2d59f073f4f5b15529ad2404205，正式審查d78e8de1959f7df72da0b52b0d107476b5bb6d0177b9051d8087fc475c43d385，來源索引15af41658e2c506ea2c42c113ddd3a52fd45fe8fbfc23dd7eb6090571e3600b0。
所有分析、原型、建置、測試與GUI在既有UID1000的受限Docker執行；原版目錄及兩份輸入封存檔另以巢狀唯讀掛載保護。
xvfb-run的PID1啟動等待改用有界Xvfb與trap；原版及產品沒有因此更改。
R82新增開場原PNG候選只留研究目錄，來源與幾何待驗；不計134張正式素材。
提交前核對工作樹、禁止原版檔、UID及自有容器清理，結果見本機r81-precommit-audit-r1.json。

## 2026-10-18 README新增R81成功訊息實拍

正式程式2479ece已提交並推送。直接複製當次GUI的scene-load-slot-zh-Hant-hd，步數39000000，1280×800，SHA-256 1444e884355bad8650dc56beef1c44010bce311844285238982d1fd920c8d71e，X11遊戲區逐位元組相同。共十七張，既有十六張原PNG及capture物件逐項保持，134張生成原稿不變。來源腳本初版一處舊建置路徑未修，尚未寫清冊；修正後重驗並原樣沿用已複製PNG。沒有新發行。


## 2026-10-18 R82開場來源與候選

原PNG邊框與長圖r1／r2已在UID1000研究目錄保存，未裁切、重編碼或接正式程式。
新增公開唯讀開場探針，80點與無監看控制及R6相同。長圖／邊框完整原版記憶體位置、
複製入口及基準色盤已定位，來源生命週期、遮擋與動畫仍待模型及READY。
先前自然片頭與逐寫日誌的停止原因見RESEARCH-LOG，未計完成。
R81程式2479ece及README第十七張0361d6d均已push，原版資料及134張正式原PNG保持。
本批使用既有一次性Docker工具鏈，原版及輸入封存檔唯讀；收尾核對UID、工作樹及容器清理。

R82收尾稽核通過：134張生成原PNG與17張README實拍雜湊保持，禁止原版檔追蹤0、root-owned及.md目錄0。研究審查d1d450fd61f778685af27b7e88dd68909f00e21f2c7373069c69a37fa5f29972；本次一次性容器均已完成並刪除。完整HD目標維持進行。
