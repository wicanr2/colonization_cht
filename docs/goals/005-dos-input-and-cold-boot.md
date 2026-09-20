# 目標 005：DOS 輸入與 dosgolem 冷啟動基線

狀態：completed（以 DOS 冷啟動能力收據結束）
日期：2026-09-20
對應 Issue：[ #20 ](https://github.com/wicanr2/colonization_cht/issues/20)

## 目的

使用者已選定本機 `Sid Meier's Colonization (1994)` 目錄中的 DOS 版，取代無法由 dosgolem
進入本體的 Windows 3.x NE 版本。本輪要為此 DOS 版建立固定輸入清冊、確認實際遊戲入口，並
以 `workplace/dosgolem` 的獨立副本取得可重跑的冷啟動能力收據。

## 範圍

1. 對唯讀 `SMColoni/` 目錄產生完整檔案 manifest 雜湊；不將 manifest 或原始資料加入 Git。
2. 以啟動批次檔、檔案格式與固定 SHA-256 確認主遊戲候選，而不憑檔名猜測。
3. 對固定候選以 dosgolem `cmd/probe` 執行冷啟動；記錄已開檔案、視訊模式、停止點與未實作服務。
4. 若 probe 可前進，定義下一個最小冷啟動收據；若不能，記錄服務缺口與最小重現，不改用 DOSBox
   當作最終證據。

## 排除項目

- 不修改原始 DOS 目錄、CD 映像、遊戲 EXE、資料檔或存檔。
- 不抽取／翻譯文本，不建立中文覆蓋程式，也不宣稱已到主選單。
- 不修改 `/home/anr2/cht/dosgolem`；只可使用 `workplace/dosgolem` 的獨立副本。
- 不把 Windows 3.x 靜態 NE 清冊套用到這份 DOS 版。

## 初始證據

唯讀來源根目錄為 `Sid Meier's Colonization (1994)/SMColoni/`。其下有 `COLONIZE/` 遊戲資料
目錄與 `cd/Colonize.bin`／`.cue`。`COLONIZE.BAT` 已確認以 `opening -g ...` 啟動，因此 DOS 的
原始冷啟動入口是 `COLONIZE/OPENING.EXE`；`VICEROY.EXE` 是後續遊戲候選，不可在沒有轉交證據時
直接取代入口。兩者均待以固定雜湊與 dosgolem 實測記錄。

## 結果

完整 `SMColoni/` 唯讀 manifest 有 291 個檔案、390,317,887 bytes；manifest SHA-256 是
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。啟動批次檔的 SHA-256 是
`4ea071484153da2716f77446fc6c7545645493fd369daf62fba8f395fa0bd9db`，其啟動命令解析為
`OPENING.EXE`。固定 `OPENING.EXE` 的 SHA-256 是
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；`VICEROY.EXE` 的 SHA-256
是 `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`。

dosgolem 的 100,000、1,000,000 與 10,000,000 指令 probe 都從 `OPENING.EXE` 的原始冷啟動
路徑執行，沒有未實作服務。1,000,000 指令時已進入 13h、初始化 PIT／滑鼠、載入
`PSOUND.COL` overlay 並完整讀取 `COLDIG.BIN`；10,000,000 指令時仍存活，但 A0000 為零，
尚未取得可見畫面或轉交 `VICEROY.EXE` 的證據。這是可繼續的 DOS 基線，不是主選單收據。

`VICEROY.EXE` 的 1,000,000 指令 direct-entry probe 僅作診斷：它在 EMS 初始化後固定於
`0020:402A`、沒有開檔或畫面，不能取代正常 `OPENING.EXE` 路徑。第一個可見畫面或可證實
轉交事件移交 [Issue #21](https://github.com/wicanr2/colonization_cht/issues/21)。完整收據見
[`RESEARCH-LOG.md`](../../RESEARCH-LOG.md)。

## 退出條件

- [x] DOS 輸入 manifest、檔案數、總量與 manifest SHA-256 已寫入 `RESEARCH-LOG.md`。
- [x] 主遊戲入口有批次檔啟動證據、固定 SHA-256 與檔案格式佐證。
- [x] `workplace/dosgolem` 對固定 `OPENING.EXE` 有 Docker 可重跑的 `cmd/probe` 收據。
- [x] probe 結果已明確記錄為可繼續的 DOS 冷啟動路徑；後續可見收據由 #21 處理，並已回填
  `CONTEXT.md`、`docs/worklist.json`、Issue #18／#20。
