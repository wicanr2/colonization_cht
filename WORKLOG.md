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
