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
`MPSNAME.SS`，但尚未有可見畫面或主程式轉交。目標 013 已確認原程式以 `AH=52h` 取得的活躍（active）MCB
鏈直接建立 `1C42` 記錄；目前 dosgolem 的內部記憶體 arena 沒有吸收該修改，失敗的 `AH=49h` 服務又
重發佈過期鏈，使 overlay 重用 `1C43`。兩個呼叫端都覆寫服務回傳值，不能把它誤稱為遊戲要求成功釋放。
這已收斂為僅供審查的 [MCB 重新協調 DRAFT 規格](docs/spec/003-colonization-mcb-arena-reconciliation-draft.md)，
尚不授權實作；使用者已選定通用多行程 MCB 匯入範圍。目標 016 確認現行 arena 會遺失 child owner/name，
且 TSR 宣告保留後仍可能讓父配置落入保留範圍；固定遊戲路徑目前仍只觀測到 `AH=4Bh AL=03h` overlay，
這不會被誤稱成 child EXEC 或 TSR 的原版需求。[Issue #24](https://github.com/wicanr2/colonization_cht/issues/24) 仍在 DRAFT 閘門，不會實作猜測性的
DOS、滑鼠或音訊服務。範圍、固定輸入與證據界線見
[目標 016](docs/goals/016-mcb-process-service-draft-audit.md)。此前沒有可下載中文化程式或任何完成度宣稱。先前 Windows 3.x NE
輸入只保留為歷史研究證據，不是目前實作目標。

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
- [Sound Blaster Pro OPL 規格草案](docs/spec/001-colonization-sbpro-opl-profile.md)
- [Sound Blaster Pro OPL READY 規格](docs/spec/002-colonization-sbpro-opl-profile-ready.md)
- [MCB 記憶體 arena 重新協調規格草案](docs/spec/003-colonization-mcb-arena-reconciliation-draft.md)
- [工作歷程](WORKLOG.md)
