# 目標 007：Colonization 相容 OPL 埠規格閘門

狀態：completed（DRAFT 已完成；READY 升級條件仍由 Issue #22 追蹤）
日期：2026-09-20
對應 Issue：[ #22 ](https://github.com/wicanr2/colonization_cht/issues/22)

## 目的

將 `OPENING.EXE` 正式冷啟動停留於 `PSOUND.COL` 的觀察，收斂為可審查的
`0x220`–`0x223` Sound Blaster 相容 OPL 埠規格。必須把公開硬體契約、遊戲實際 port
序列與 dosgolem 現有行為分開記錄；不可把「看起來像音效」直接升格為卡住原因。

## 已有證據

- 固定原始入口為 `OPENING.EXE`，SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；唯一實際
  `EXEC` 為 `PSOUND.COL`。
- 固定 state `opening-1000000-visible-20260920.state`（SHA-256
  `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`）的
  1,000,000–2,000,000 指令分支有 38,852 筆 `0x220`、`0x221`、`0x222`、`0x223`、
  `0x226` 寫入；TSV SHA-256 為
  `cfe22ede3c12e99839dc095adebda040af5bf87cbebc0fb5fdc9b449c813620e`。
- 既有 `machine.New()` 只將 `0x388`–`0x38B` 接到 OPL；LE/DOS4GW 專用
  `LEOPLPorts` 才有 `0x220`–`0x223` alias。因此相容層缺口目前是 strong inference。

## 執行方法

1. 由既有固定 TSV 擷取 `0x226` reset 與四個 address/data 埠的精確時間序列；將每個數字標記為
   檔案位移、DOS segment:offset、線性位址或 I/O port，避免混用位址空間。
2. 讀取同一 dosgolem commit 的 `machine.New()`、OPL 與 `LEOPLPorts` 實作，證明 probe 實際採用的
   預設行為及可重用 alias 的範圍；不得將 LE/DOS4GW 路徑誤稱為已套用。
3. 以公開 OPL／Sound Blaster 文件只確認標準 port 契約；遊戲 RE 只記錄本版的 port、序列、
   `PSOUND.COL` overlay 位址與可見輸出停止點。PCM、DMA、PIT 時鐘遵守平台規格停止線。
4. 寫入 `docs/spec/` 的 DRAFT，執行證據審查。僅當輸入、啟用條件、port alias、未知讀取行為、
   失敗即關閉條件與驗收方法都充分時，才另建 READY；否則維持 DRAFT 並以未知項交給下一輪。

## 排除項目

- 不修改 `workplace/dosgolem`、原始資料、文字、圖像、翻譯或封裝。
- 不做 Sound Blaster DSP、DMA、PCM 或 PIT 的逐週期實機考古；不把音訊輸出做為本輪完成條件。
- 不以 `VICEROY.EXE` direct-entry、DOSBox 或靜態字串取代正式 `OPENING.EXE` 冷啟動。
- 不因既有 LE/DOS4GW helper 存在，就宣稱 Colonization 的預設 probe 已有同等硬體支援。

## 退出條件

- [x] 固定輸入、state、TSV、程式原始定位、工具提交與四種證據等級已寫入 `RESEARCH-LOG.md`。
- [x] `docs/spec/` 已有 DRAFT，並列出 READY 升級條件與未知項；證據不足，沒有越級建立 READY。
- [x] Issue #22、`CONTEXT.md`、`docs/worklist.json`、README 與 `WORKLOG.md` 已同步；Docker 清理、提交與推送在本輪交付前完成。
