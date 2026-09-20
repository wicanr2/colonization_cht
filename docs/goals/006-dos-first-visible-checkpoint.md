# 目標 006：DOS 首個可見檢查點診斷

狀態：completed（以最小具體 blocker 收據結束）
日期：2026-09-20
對應 Issue：[ #21 ](https://github.com/wicanr2/colonization_cht/issues/21)

## 目的

從使用者指定的 DOS 原版正式冷啟動路徑 `COLONIZE.BAT` → `OPENING.EXE`，以 dosgolem 的通用
`cmd/probe` 取得首個可見畫面、可觀測文字輸出，或原始執行鏈實際轉交的最小可重播收據。這一輪只
縮小阻塞點；不是中文化實作，也不以跳過啟動流程的 direct-entry 代替原始玩家路徑。

## 目前事實

- 固定輸入為 `SMColoni/COLONIZE/OPENING.EXE`，SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`。
- 已在 `workplace/dosgolem`（commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`）以正式入口跑到
  1,000 萬指令：程式進入 13h、設定 PIT／滑鼠、載入 `PSOUND.COL` overlay 並讀取 `COLDIG.BIN`，
  沒有未實作服務；結束時 `A0000` 非零像素仍為零。
- `VICEROY.EXE` 的 direct-entry 停點只屬診斷觀察，沒有原始 `EXEC` 收據，不能當成本輪成功條件。

## 執行方法

1. 對正式 `OPENING.EXE` 以固定步數建立可載入狀態快照，所有原版輸入唯讀掛載，快照、trace 與
   原始 VRAM／埠觀測輸出只寫入 gitignore 的 `workplace/reports/`。
2. 從相同冷啟動與快照位置啟用 `cmd/probe` 的視訊寫入監看、索引畫面採樣、VRAM 寫入來源統計、
   segment 轉換與檔案／`EXEC` trace；比較 1,000,000 至 10,000,000 指令區間的證據。
3. 若取得非零畫面，記錄精確步數、輸入雜湊、工具提交、命令、畫面雜湊與原始輸出位置；若取得
   `EXEC`，記錄呼叫前後的原始檔案路徑與位址。兩者都沒有時，將零 VRAM 寫入、等待／迴圈或其他
   可定位的最小缺口寫成 blocker 收據。
4. 只有證據指出 dosgolem 具體缺口時，才另開 DRAFT 規格與最小重現；本輪不修改 dosgolem。

## 結果

從第 1,000,000 指令的正式冷啟動快照重播到第 100,000,000 指令，程式仍存活於
`PSOUND.COL` overlay 的 `1C43:0087`，已送出 5,215 次 timer；畫面保持 mode 13h，A0000 色號
陣列為 0／64,000，視訊記憶體寫入監看為零，主控台與字型常式呼叫也都是零。兩份 10,000,000 與
100,000,000 指令的色號輸出 SHA-256 同為
`4f7988030a00d082fe445e00a2ac5dab502300ff1b80e8592dd569867b60ef74`。這不是首畫面或正常玩家路徑。

`OPENING.EXE` 的唯一 `EXEC` 收據是 `PSOUND.COL`，不是 `VICEROY.EXE`。在 1,000,000–2,000,000
指令的同一快照分支，`PSOUND.COL` 對 `0x220/0x221` 與 `0x222/0x223` 寫入 38,846 次、對
`0x226` 寫入 6 次；完整 TSV 的 SHA-256 是
`cfe22ede3c12e99839dc095adebda040af5bf87cbebc0fb5fdc9b449c813620e`。固定版本的預設
`cmd/probe` 以 `machine.New()` 建立機器，而其 OPL 模型只處理 `0x388`–`0x38B`；雖有另一條
LE/DOS4GW 專用路徑將 `0x220`–`0x223` 映射為 OPL，但 probe 沒有使用它。

因此「缺少 `0x220`–`0x223` 的 Sound Blaster 相容 OPL 行為使啟動停留在音效 overlay」是
**strong inference**，不是已證實的因果。公開硬體語意不在本專案重做逆向；後續由
[Issue #22](https://github.com/wicanr2/colonization_cht/issues/22) 先建立 DRAFT／READY 規格，才可由
[Issue #23](https://github.com/wicanr2/colonization_cht/issues/23) 作最小實作與正式冷啟動驗證。

## 排除項目

- 不修改原始遊戲、原始資料、存檔或 `/home/anr2/cht/dosgolem`；不把原版素材、快照或報告加入 Git。
- 不以 DOSBox、VICEROY direct-entry、靜態檔案字串或一張未對齊的截圖宣稱正式冷啟動已到主選單。
- 不抽取、翻譯或覆蓋任何文字；Issue #5 與 #8 仍須等待本 Issue 的正式收據。
- 不對 dosgolem 寫程式；若需要修正，必須遵循「量測 → DRAFT → 證據審查 → READY → 實作」流程。

## 退出條件

- [x] 以 `OPENING.EXE` 正式冷啟動完成固定步數、視訊／segment／檔案觀測與可載入快照的收據。
- [x] 結果明確為最小具體 blocker；不以 direct-entry
  代替其中任一項。
- [x] `RESEARCH-LOG.md`、`CONTEXT.md`、`WORKLOG.md`、`docs/worklist.json`、README 與 Issue #21
  同步更新，並在 Docker 清理後提交、推送。
