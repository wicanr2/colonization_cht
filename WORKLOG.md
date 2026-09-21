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
