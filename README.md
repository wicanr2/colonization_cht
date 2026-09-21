# 殖民地帝國繁體中文化

《Sid Meier's Colonization》（1994）是以歐洲殖民新世界為題材的歷史策略遊戲：玩家經營殖民地、
處理資源與貿易、與其他勢力互動，並在獨立目標前作出一連串治理選擇。

本專案希望降低玩家面對這些選擇時的語言隔閡，讓繁體中文讀者能理解選單、訊息、狀態與說明，
而不必在遊玩過程中反覆離開遊戲查找翻譯。

## 中文化方式

這不是 remake。原版 DOS 執行檔、遊戲規則、資料與存檔格式維持原樣，由
[dosgolem](https://github.com/wicanr2/dosgolem) 執行。本專案只在原版輸出文字到畫面的階段，
以可追溯的來源鍵辨識**整則訊息**，再於放大後的畫布覆蓋繁體中文。

畫面上有兩種文字來源，兩者都會研究：

- 程式動態輸出的選單、訊息、狀態與說明文字。
- 已烘進按鈕、標籤、告示或其他圖像中的靜態文字。

後者同樣在輸出畫面階段覆蓋，不改寫原版圖檔。版本、雜湊、輸出事件或圖像指紋不符時，
轉譯層必須失敗即關閉（fail-closed），保留原版畫面而不猜測套用。

## 目前狀態

使用者已指定合法 DOS 輸入作為正式研究目標。dosgolem 能沿 `OPENING.EXE` 的原始冷啟動路徑進入
13h 圖形模式、計時器、滑鼠、overlay 與資料讀取；目前另觀測到一個尚未實作的滑鼠
`int 33h AX=0014`，但尚未證實它造成目前受阻點（blocker）。這是 DOS 能力基線，不是主選單或可遊玩宣稱。

目標 006 已把正式啟動卡住的位置收斂至 `PSOUND.COL` overlay 的相容 OPL 埠行為；它不是首畫面、
也不是遊戲主程式轉交。目標 008 已完成可實作的 [最小 READY 規格](docs/spec/002-colonization-sbpro-opl-profile-ready.md)：
它只處理已證實的 `0x220` primary OPL 偵測、`0x222` delay 與 `0x226 → 0x22E → 0x22A=0xAA` DSP reset
handshake，不宣稱完整音效或 OPL3 parity。目前依 [目標 009](docs/goals/009-sbpro-profile-and-cold-boot.md)
在隔離的 dosgolem 副本完成可選 profile；正式路徑已跨過 DSP reset，並載入 `MPSLOGO.SS`、
`MPSNAME.SS`。原程式直接建立的活躍（active）MCB 鏈已由
[MCB 重新協調 DRAFT 規格](docs/spec/003-colonization-mcb-arena-reconciliation-draft.md)、
[已註冊多行程 READY 規格](docs/spec/004-colonization-registered-process-mcb-importer-ready.md) 與
[CONFORMED 規格 005](docs/spec/005-colonization-registered-process-mcb-importer-conformed.md) 收斂：隔離
dosgolem 現可保存 raw header／owner／name、current PSP、state v3，並拒絕未登錄 owner、未知 lifecycle
與 v2 state。固定冷啟動的第 2,000,000 指令 state v3 可重載；從同一 state 續跑確認 mode 13h 在
2.70M–2.75M 指令間首次寫入 18,445 個非零 A0000 像素，至 20M 仍保留。這是首個可見畫面收據，已解除
[Issue #24](https://github.com/wicanr2/colonization_cht/issues/24) 的映像外控制流 blocker；但尚未定位動態文字、
靜態文字語意或 `VICEROY.EXE` 轉交，不能宣稱可遊玩或中文化完成。
範圍、固定輸入與證據界線見 [目標 022](docs/goals/022-psound-post-mcb-visible-checkpoint.md)。此前沒有可下載中文化程式或任何完成度宣稱。先前 Windows 3.x NE
輸入只保留為歷史研究證據，不是目前實作目標。

[目標 023](docs/goals/023-first-frame-draw-provenance.md) 已把首個 VRAM 寫入精確定位到第 2,747,686
指令的 `0557:0090`，其 `DS:SI=1DFB:00F8` 至 `ES:DI=A000:1C78` 為跨列點陣資料搬運；這是靜態首幀的
強推論，不是動態文本鍵。[目標 024](docs/goals/024-first-screen-normal-input-observation.md) 進一步確認首幀後的
單一 BIOS 緩衝區 Enter 或中央左鍵，皆進入同一段 `OPENING.PIK` 與 15 個 `OPEN*.SS` 資產的載入序列；截至
第 12M 指令仍未命中字型、B8000 或主控台文字。因此正常輸入前沿已取得，但尚不能宣稱已定位任何動態文本。

[目標 025](docs/goals/025-opening-static-asset-inventory.md) 已將同一開場分支收斂為兩個 `.PIK` 與 14 個
`.SS` 的固定雜湊、大小與 DOS 讀取清冊。它們是可重播的靜態圖像**調查候選**，不是已證實含文字的資產；每一項的
文字存在、畫面矩形與中文安全覆蓋區仍未知，尚未建立覆蓋原型或規格。
[目標 026](docs/goals/026-opening-pik-render-provenance.md) 已確認 `OPENING.PIK` 的取樣資料會由 `5755`
原始緩衝區寫入 `1C43` 畫布，且較後整張畫布會複製到 mode 13h 的 `A000` VRAM。其間有其他資產載入，
因此這不是任何特定最終像素、文字或覆蓋矩形的證據；靜態文字仍待各候選另行確認。

第一輪的範圍與退出條件見 [目標 001](docs/goals/001-foundation-and-evidence.md)。目前等待使用者
確認的執行策略見 [目標 002](docs/goals/002-win16-execution-strategy.md)；實際工作順序與 Issue
連結見 [工作計畫](WORKLIST.md)。最新已知事實與限制見 [目前脈絡](CONTEXT.md)。

DOS 輸入的固定雜湊、probe 與限制見 [目標 005](docs/goals/005-dos-input-and-cold-boot.md)。
首個可見檢查點的 blocker 收據與後續閘門見 [目標 006](docs/goals/006-dos-first-visible-checkpoint.md)。
相容 OPL 埠的規格閘門見 [目標 007](docs/goals/007-colonization-opl-compatibility-spec.md)。
Windows 3.x NE 的靜態清冊與舊 blocker 保留在 [目標 003](docs/goals/003-ne-load-surface-inventory.md)
及 [目標 004](docs/goals/004-execution-strategy-blocker-audit.md)，不混入目前 DOS 路徑。

## 原版與權利邊界

玩家必須自行持有合法的原版。本儲存庫不會包含或散布原版 EXE、資料檔、圖像、字型、音樂、
磁碟映像、存檔或解包輸出；需要原版的驗證在輸入缺失時會明確跳過。

本專案目前是私有研究儲存庫。任何公開發布、授權、封裝與原文／原版畫面處理，都會在有可驗證
成果後另行確認，不能由這份 README 推定。

## 文件

- [專案規則](AGENTS.md)
- [目前脈絡](CONTEXT.md)
- [工作計畫](WORKLIST.md)（由 `docs/worklist.json` 產生）
- [第一輪目標](docs/goals/001-foundation-and-evidence.md)
- [第二輪目標](docs/goals/002-win16-execution-strategy.md)
- [第三輪目標](docs/goals/003-ne-load-surface-inventory.md)
- [第四輪目標](docs/goals/004-execution-strategy-blocker-audit.md)
- [第五輪目標](docs/goals/005-dos-input-and-cold-boot.md)
- [第六輪目標](docs/goals/006-dos-first-visible-checkpoint.md)
- [第七輪目標](docs/goals/007-colonization-opl-compatibility-spec.md)
- [第八輪目標](docs/goals/008-psound-ready-evidence.md)
- [第九輪目標](docs/goals/009-sbpro-profile-and-cold-boot.md)
- [第十輪目標](docs/goals/010-psound-out-of-range-control-flow.md)
- [第十一輪目標](docs/goals/011-psound-clear-argument-provenance.md)
- [第十二輪目標](docs/goals/012-psound-overlay-writer-lifecycle.md)
- [第十三輪目標](docs/goals/013-mcb-arena-draft-evidence-review.md)
- [第十四輪目標](docs/goals/014-mcb-arena-ready-scope-audit.md)
- [第十五輪目標](docs/goals/015-mcb-multiprocess-ownership-evidence.md)
- [第十六輪目標](docs/goals/016-mcb-process-service-draft-audit.md)
- [第十七輪目標](docs/goals/017-mcb-platform-contract-evidence.md)
- [第十八輪目標](docs/goals/018-mcb-wire-format-and-direct-write-evidence.md)
- [第十九輪目標](docs/goals/019-mcb-generic-importer-ready-review.md)
- [第二十輪目標](docs/goals/020-mcb-registered-process-ready-spec.md)
- [第二十一輪目標](docs/goals/021-mcb-registered-process-implementation.md)
- [第二十二輪目標](docs/goals/022-psound-post-mcb-visible-checkpoint.md)
- [第二十三輪目標](docs/goals/023-first-frame-draw-provenance.md)
- [第二十四輪目標](docs/goals/024-first-screen-normal-input-observation.md)
- [第二十五輪目標](docs/goals/025-opening-static-asset-inventory.md)
- [第二十六輪目標](docs/goals/026-opening-pik-render-provenance.md)
- [Sound Blaster Pro OPL 規格草案](docs/spec/001-colonization-sbpro-opl-profile.md)
- [Sound Blaster Pro OPL READY 規格](docs/spec/002-colonization-sbpro-opl-profile-ready.md)
- [MCB 記憶體 arena 重新協調規格草案](docs/spec/003-colonization-mcb-arena-reconciliation-draft.md)
- [已註冊多行程 MCB importer READY 規格](docs/spec/004-colonization-registered-process-mcb-importer-ready.md)
- [已註冊多行程 MCB importer CONFORMED 規格](docs/spec/005-colonization-registered-process-mcb-importer-conformed.md)
- [工作歷程](WORKLOG.md)
