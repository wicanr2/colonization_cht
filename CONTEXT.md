# 目前脈絡

日期：2026-09-21

## 已確認

- 目標是《Sid Meier's Colonization》（1994）的繁體中文**輸出階段轉譯層**，不是 remake。
- 動態輸出文字與靜態圖像內嵌文字都在研究範圍；原版檔案不修改。
- GitHub 儲存庫 `wicanr2/colonization_cht` 是私有儲存庫。
- 本機兩份原始封存檔僅能唯讀使用，已由 `.gitignore` 排除；雜湊與清冊見 `RESEARCH-LOG.md`。
- 未完成項的唯一機器可讀來源是 `docs/worklist.json`；每筆都有 GitHub Issue。
- `README.md` 是專案首頁；第一輪目標見 `docs/goals/001-foundation-and-evidence.md`。
- `workplace/dosgolem` 是提交 `1435f175e785ea096a9268cd1021a4222300bd43` 的獨立副本，push URL 為 `DISABLED`；不得修改其他
  專案使用的 `/home/anr2/cht/dosgolem`。
- 固定雜湊的 `COLONIZE.EXE` 是 Windows 3.10 NE 程式。dosgolem probe 只走到 DOS stub，
  無法進入 Windows 應用程式本體；這是可重現 blocker，不是已支援的冷啟動。
- 固定 NE 的靜態載入面已完成清冊：33 個區段、7 個模組、176 個 ordinal import target、
  42 個資源項目；這只描述檔案結構，不能證實任何 Win16 API 的實際呼叫或文字輸出。
- 使用者已選定本機 `Sid Meier's Colonization (1994)/SMColoni/` 的合法 DOS 輸入作為正式研究目標；
  該目錄由 `.gitignore` 排除，291 個檔案／390,317,887 bytes 的 manifest SHA-256 是
  `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。
- 正常 DOS 冷啟動入口是 `OPENING.EXE`（SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）。目標 022 以 `-sbpro` 的正常
  冷啟動在第 2,000,000 指令保存 state v3（SHA-256
  `1f9b3822fc5ad2c041714a95527a230096cee97c69181fc82f0d9feec165de6b`），並由同一路徑／同一唯讀素材
  目錄重載。2.70M 收據仍是 A0000 全零，2.75M 收據已是 18,445／64,000 個非零 mode 13h 像素；完整 VRAM
  watch 有 18,445 筆、未丟棄的寫入，末段的 confirmed 寫入端是 `0557:0090`。10M、20M 均維持同一個
  非零像素數並持續輪詢滑鼠。這是首個可見畫面收據；尚未觀測文字常式、主控台文字或 `VICEROY.EXE` 轉交。
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
- 目標 016 的 service 探針進一步確認：child 的 `48h` 與 `4Ah` 後 MCB owner 均為 root `0100`；child
  先 `49h` 再 normal exit 時，arena 雖仍有兩格但父可重取 `2014`。更嚴重的是 child `AH=31h DX=40h`
  後 `freeSeg=2041`，父 `AH=48h` 卻配得 `2035`，落入宣告保留範圍。state v2 可 round-trip child
  PSP／stack／arena／freeSeg，卻根本沒有 owner/name；`AH=51h`／`62h` 又固定回根 PSP。這些均是
  confirmed executor 缺口，絕非 Colonization child／TSR parity。
- 目標 017 的 MS-DOS 3.10 原始手冊交叉確認：`48h` 屬 current process、`49h` 僅釋放先前 `48h`
  block、`4Ah` 有 CF/AX/BX 失敗契約、`4Ch` 結束 current process 並回父、`62h` 回 active PSP。它們
  支持 B 必須有 owner-aware registry，但未定義跨程序或手改 MCB 細節，故 DRAFT 仍未 READY。
- 目標 020 的 READY 規格 004 已在目標 021 實作並由 [CONFORMED 規格 005](docs/spec/005-colonization-registered-process-mcb-importer-conformed.md)
  驗收：已註冊 root／child owner 的 raw 16-byte header、owner/name、registry、state v3、current PSP
  services、normal child 回收與有限 TSR retain 均由 typed model 驅動；未登錄 owner、cross-process、未知
  lifecycle 與 v2 state 一律 fail-closed。實作位於隔離副本的本地提交 `1435f17`，其 `upstream` 仍為
  `DISABLED`。先前目標 015–016 的 root-owner 重發佈、TSR overlap、固定 root
  PSP 回傳均是實作前基線，不再是現行行為。
- 固定 `OPENING.EXE` 以 `-sbpro` 至 2,000,000 指令的前一輪收據（SHA-256
  `2fa18b931afac4bf15f7d89a1712cb7e98de2a7e29a054097202589cb4a58e00`）已確認 overlay、後續資料讀取與
  `$sys$`、`FONTINTR`、`$sound$` 等 raw MCB name；目標 022 的 state v3 續跑進一步證實這些狀態能到達首個
  mode 13h 可見畫面，沒有 importer 拒絕或舊 arena 重發布跡象。
- 目標 023 在第 2,747,686 指令確認 `0557:0090` 以 `DS:SI=1DFB:00F8` 向 `ES:DI=A000:1C78` 寫入首畫面；
  後續來源與目的各以 `0x140` 跨列遞進。這是 confirmed 的 raster 搬運定位；由無字型 hook／B8000／主控台輸出
  與該搬運型態，只能作「首畫面較可能是靜態點陣資料」的強推論，不能確認圖像語意、資產檔對應或動態文字路徑。
- 目標 024 以同一個第 2,000,000 指令 state v3 證實首畫面的正常前進輸入：BIOS 鍵盤緩衝區的一個 Enter 在
  第 3,000,121 指令由 `int 16h AH=00` 取走；位於 `(160,100)` 的單次左鍵則在第 3,000,022 指令由
  `int 33h AX=0003` 觀測為按下。兩者都進入相同開場資產路徑，最後的 mode 13h VRAM SHA-256 都是
  `d2add3f193e10c0b9d4d65b7fc59b10e6bd967a81bbfe1eb93a5ad4bf41166b0`，並載入 `OPENING.PIK`、
  `OPENBORD.PIK` 及 14 個 `OPEN*.SS`。這證實這兩筆輸入使流程前進，不證實畫面／按鈕語意或資產內容。
  此 2M–12M 輸入分支仍無全形／半形字型 hook、B8000 或主控台字元；動態文字路徑仍是 unknown。探針的
  IRQ1 `-press enter` 因 `int 09h` 未安裝而留在佇列，不能當作此程式的可用鍵盤收據。
- 目標 025 以同一個 BIOS Enter 路徑至第 5,500,000 指令，建立 16 項實際載入資產的清冊：`OPENING.PIK`、
  `OPENBORD.PIK` 與 14 個 `OPEN*.SS`，每項均有檔案大小、SHA-256、開啟步數與主要讀取 offset／長度。
  此時 mode 13h 為 64,000／64,000 非零像素、總 VRAM 寫入 101,639 筆（範圍 A0000h–AFEFDh），且無字型 hook、
  B8000 或主控台文字。這些資料只確認正常開場分支載入候選並伴隨可見繪製；單一資產至螢幕矩形、是否包含文字、
  圖像語意與可覆蓋幾何皆維持 unknown。
- 目標 026 的 `OPENING.PIK`→畫布結論已由目標 027 勘誤撤回。雖然 `OPENING.PIK` 的主要 payload 曾讀至
  `5755:0000`／`5755:F000`，但在第 4,104,159 指令 `0AC2:04F5`（前一位元組 `0AC2:04F4` 為 `MOVSB`）之前，
  `OPENBORD.PIK` 已於第 4,103,486 指令覆寫 `[57550h,59D55h)`。取樣 `MOVSB` 的 `SI=0007h–0BD9h` 均落在
  該覆寫區，故不能將它歸屬於 `OPENING.PIK`。第 5,464,375 指令 `0557:00A1`（前一指令 `0557:009F` 為
  `REP MOVSW`）的 `DS=1C43`、`ES=A000` 與每列 `0x140` 遞進，仍只證明共用畫布→VRAM 整屏搬運。
  此前曾記錄為 `OPENING.PIK` 資料流的主張不再有效。
- 目標 027 從第 4,099,000 至第 4,157,000 指令確認後續畫布窗口有 7,680 個不同位址由零變更，恰為
  邏輯像素（logical pixel）`(0,0)–(319,23)` 的 320×24 範圍；672 次來自 `MOVSB`，7,008 次來自相鄰 `STOSB`。
  它是 `OPENBORD.PIK` 覆寫後的共用處理窗口，不是 `OPENING.PIK` 幾何，且不表示文字、圖像語意或中文安全矩形。
- 目標 028 對相同窗口進一步確認：`OPENBORD.PIK` 的 10,245 位元組 payload 在 #4,103,486 讀入
  `[57550h,59D55h)` 後，沒有被監看到改變內容的寫入；讀取監看於 #4,104,159–#4,156,836 記錄 673 次
  `0AC2:04F5`（前一位元組 `0AC2:04F4` 為 `MOVSB`）從 `[57556h,58129h)` 讀取，這完全位於 payload 範圍。
  同窗口的 672 次 `MOVSB` 畫布變更因而是 confirmed 的 `OPENBORD.PIK` 原始緩衝區→取樣畫布資料流。監看只能
  排除內容改變，不能排除值相同寫入；此限制不影響已觀測的來源讀取，但禁止延伸為完整圖像、文字或最終像素歸屬。
- 目標 029 從第 4,156,900 指令 state 至第 5,500,000 指令對 `1C430h–1E22Fh` 記錄零筆內容變更，並在
  #5,464,375–#5,464,536 取得 7,680 筆讀取（24 組、每組 320 bytes），均在 `0557:00A1`；前一指令
  `0557:009F` 是 `F3 A5`／`REP MOVSW`，前置暫存器為 `DS=1C43`、`ES=A000`、`CX=00A0`，每列 `SI`／`DI`
  遞增 `0140h`。完整 320×24 canvas 範圍因此 confirmed 地存續並被搬至這一次 A000 VRAM copy，目標 028 的
  672 次來源資料流也包含其中。值相同寫入與 copy 後 VRAM 改寫未被此輪排除；完整資產、穩定最終畫面、文字與
  中文安全矩形仍是 unknown。
- 目標 030 以 #5,464,536 copy 完成後的同一 indexed frame 與 palette，將其開頭 7,680 bytes（320×24）轉為
  僅限本機的 PNG 檢視收據。它與目標 029 的 canvas／VRAM 範圍一致，畫面是連續重複的幾何裝飾邊框，沒有
  可辨識字形或可讀文字。因此該範圍是 confirmed 的非文字靜態裝飾，不能成為中文覆蓋目標；此結論不涵蓋
  `OPENBORD.PIK` 全檔或其他 `.PIK`／`.SS` 候選。
- 目標 031 從同一第 4,156,900 指令 state 篩出第一個完整 composite canvas→A000 copy：
  #5,464,375–#5,465,772 的 `0557:00A1` 恰有 200 組×320 bytes，從 `1C430h` 至 `2BE2Fh`；前一位址
  `0557:009F` 是 `F3 A5`／`REP MOVSW`。copy 完成 frame 的可視清冊有兩筆 confirmed 靜態文字候選：
  `opening-map-ocean-label`（約 `(53,49)–(174,61)`，`OCEANVS OCCIDENTALIS`）與
  `opening-scroll-two-line-text`（約 `(148,123)–(208,146)`，兩行字形、原文未可靠辨識）。兩者皆僅有畫面
  定位；來源資產、繪製資料流、copy 後存續與中文安全矩形仍 unknown。
- 目標 032 確認 `opening-map-ocean-label` 真正的 canvas writer：#5,432,823–#5,447,038 的 2,345 筆矩形內
  內容變更全由 `03BD:00C8`／`F3 A5`（post-IP `03BD:00CA`）產生。其第一列從暫存線性
  `[3E6A5h,3E71Eh)` 搬至 canvas 的 `[201A5h,2021Eh)`。該來源切片曾在 #3,225,029–#3,225,927 被同一
  解碼器寫入 120 次內容變更，之後至畫布使用前未見內容變更。當中 15 筆可在同一步數直接配對
  `OPENING.PIK` raw buffer `5C457h–5C497h` 的讀取至暫存切片，故這 15 個像素的檔案來源為 confirmed；另外
  105 筆為同一 `DS=5755` 解碼迴圈的 `STOSB` 分支，整則標籤歸屬 `OPENING.PIK` 僅為強推論。這是早於
  `OPENBORD.PIK` 覆寫共享緩衝區的獨立資料流，不恢復目標 026 已撤回的較晚路徑。完整檔案歸屬、copy 後穩定
  存續與中文安全矩形仍 unknown。
- 目標 033 從 #5,465,772 第一個完整 composite copy 後 state，沿同一條正常 BIOS Enter 路徑重播至
  #5,500,000。畫布精確標籤範圍 `201A5h–20FDDh` 和 A000 對應範圍 `A3D75h–A4BADh` 的內容變更日誌均為空；
  起點與終點的全畫面色號陣列及調色盤亦逐位元組相同。因此標籤在這個有限窗口的畫布與顯示狀態存續為
  confirmed，但值相同寫入、窗口以外行為、完整資產歸屬、中文安全矩形與反向辨識條件仍是 unknown。
- 目標 034 從同一 state 比較無輸入與單一 BIOS Enter。控制組至 #7,000,000 持續 mode 13h；Enter 在
  #5,465,827 由 `int16-AH00-bda` 取走，#5,511,173 切回 mode 03h，並在 #5,511,796 由
  `0562:0396` 的 `CD 21`／`AH=4Ch, AL=6Ch` 終止。兩組都沒有主控台、B8000、字型 hook 或新檔案開啟，故
  這是 confirmed 的 `OPENING.EXE` 離開分支，不是動態文字證據。離開碼的正式消費者、其他正常入口與動態文字
  輸出路徑均為 unknown。
- 目標 035 盤點 DOS 安裝根層的兩個批次候選：`COLONIZE.BAT`（SHA-256
  `4ea071484153da2716f77446fc6c7545645493fd369daf62fba8f395fa0bd9db`）與 `COLDEMO.BAT`
  （SHA-256 `ccc44d5c31aef794eea0b27f240970e31839923c10e487c4b1923f80ce7da97d`）。兩者僅以最終命令詞
  `opening` 直接啟動開場，沒有後續批次分派行。dosgolem 的 `cmd/probe` 對 `.BAT` 會從 `0100:0100` 將其
  當作 COM 式程式碼執行，不支援 batch／`COMMAND.COM` 重播；因此沒有已證實的 `0x6C` 消費者，且不能把
  這個工具缺口或腳本靜態結構外推為 DOS shell／遊戲語意。
- 目標 036 從同一完整 composite state 對照控制組與目標 024 已記錄的 `(160,100)` 左鍵：該左鍵在
  #5,465,840 由 `int 33h AX=0003` 讀到，#5,509,215 切回 mode 03h，並在 #5,509,826 以
  `0562:0396`／`AH=4Ch, AL=6Ch` 終止。控制組至 #7,000,000 仍為 mode 13h。這是 confirmed 的輸入消費與
  退出結果，但既不確認按鈕語意，也沒有動態文字、主控台、B8000、字型 hook 或新檔案證據。
- 目標 037 將上述單點縮到 `0110:0952` 的 `OR AX,AX` 與 `0110:0954` 的 `JZ 0960`：控制組的
  `AX=0000` 跳至 `0110:0960`，左鍵組的 `AX=0001` 落入 `0110:0956`，後者寫入 `001Bh` 到 `[BP-0Ah]`。
  這是 confirmed 的按下 boolean consumer；`001Bh`、`AX` 的上游、座標 hit-test、矩形與按鈕語意均為 unknown。
  IDA 9.4 映像的技能指定工具契約文件目前不可定位，故本輪沒有使用未驗證 IDA 輸出。

## 尚未確認

- 可見畫面的語意、印字常式、文字來源、靜態文字資產、字型來源、術語政策與中文化完成門檻。
- `VICEROY.EXE` 轉交，以及字型來源、術語政策、中文化完成門檻、授權、公開發布與封裝範圍。

## 下一閘門

Issue #23 已完成 READY profile 的實作與同狀態收據，#24 的 MCB importer 與首個 mode 13h 畫面證據亦已完成。
正式 batch 啟動鏈已排除為可觀測的 `0x6C` 消費者，且目前 dosgolem 沒有 batch／`COMMAND.COM` 重播層；完整
開場 state 的單一 Enter 與既有中央左鍵皆已確認為退出路徑。已知左鍵的第一個 boolean consumer 是
`0110:0952–0954`，但座標命中判斷尚在上游。下一個動態前沿應追溯該 `AX` 如何從滑鼠服務的 `BX/CX/DX`
產生，再以證實區域測試單一路徑；不得盲注、掃描或猜測 shell／按鈕語意。
`OPENBORD.PIK` 的
已確認 320×24 範圍已排除為文字候選；下一個
靜態前沿已取得 `opening-map-ocean-label` 的部分原始像素→暫存→畫布→有限窗口 A000 存續鏈；下一個切片要為它
建立可逆的清除／覆蓋幾何證據，再與其他實際載入的 `.PIK`／`.SS` 候選各自確認完整檔案歸屬與安全矩形，才能
進入字型／版面原型的使用者評估；不得把共用畫布搬運、檔名或可見外框當成覆蓋目標。目前仍沒有任何中文覆蓋實作
授權。不得將 external owner、cross-process
或未知 TSR 行為擴張成新實作。Windows NE 清冊（#19）只保留為歷史輸入證據；Issue #10 與 #15 仍需在真實證據與原型具備後由使用者決定。
