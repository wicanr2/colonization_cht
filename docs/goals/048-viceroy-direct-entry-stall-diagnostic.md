# 目標 048：`VICEROY.EXE` direct-entry 停滯診斷

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 005](005-dos-input-and-cold-boot.md)、[目標 035](035-opening-exit-code-launcher-chain.md)、[目標 046](046-opening-click-nonzero-downstream-dataflow.md)

## 目的

目前已證實的 `OPENING.EXE` 正常輸入都走向非文字離開，正式 launcher／`VICEROY.EXE` 轉交仍未知。
早期診斷性 direct-entry 在第 1,000,000 指令停於 `0020:402A`、IF=false，卻沒有足以定位是 CPU、DOS、
BIOS、EMS 或程式自我等待的最小原因。本輪只在固定 `VICEROY.EXE` 版本重生該**診斷**狀態，收集同一條無輸入
direct-entry 的控制流、原始 bytes、服務與畫面／檔案事件，判定是否存在具體、通用且可規格化的 dosgolem 缺口。

這不是正常玩家路徑、不是 `OPENING.EXE` 的已證實後續，也不是動態文字輸出證據；即使 direct-entry 有可見結果，
也不得將其升格為正式流程或中文覆蓋資格。

## 執行項目

1. 對固定 `VICEROY.EXE` SHA-256 `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`
   從冷啟動、無鍵鼠輸入重播；保存第 1,000,000 指令 state，並以絕對步數展開短控制流窗口與較長無輸入窗口。
   原版目錄唯讀，所有 state／raw／trace／畫面收據只留在 gitignore 的 `workplace/reports/`。
2. 記錄停滯點的實際 `CS:IP`、FLAGS、raw bytes、短 IP timeline、DOS／BIOS call 統計、未實作服務、檔案、
   mode／VRAM／B8000 與 segment 變化；每項固定到輸入雜湊、dosgolem commit、位址空間和步數。
3. 僅在同一可重播狀態可證實「特定通用服務／CPU 行為缺失」時，提出最小 DRAFT 所需證據；若只是無法由
   direct-entry 解釋的等待或無缺口，記錄診斷停止線。不得修改 dosgolem、原版或遊戲專屬資料。
4. 不 OCR、不讀取／轉存原文或圖像、不建立文本鍵、譯文、字型、DRAFT／READY、覆蓋原型或輸出攔截；不以
   direct-entry 結果取代另一條已觀測的正常玩家路徑。

## 結果

- 固定輸入為 `VICEROY.EXE`（SHA-256
  `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`）與 DOS manifest
  `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`；工具是隔離 dosgolem commit
  `1435f175e785ea096a9268cd1021a4222300bd43`。所有容器無網路、以 UID/GID 1000:1000 執行，原版 `/game`
  唯讀，state、trace、raw 與畫面傾印都只在 gitignore 的 `workplace/reports/`。
- **confirmed**：無輸入冷啟動在 #1,000,000 的 state SHA-256 是
  `ab91f84efba8e9264d3643701526ce64da486e7cd9c8ecd2a37f5dfb59c98258`。#1,000,001 的 lifecycle 是
  `4eefdaba9a206e68be53c25a02b2a8bb469a36b2b1c4b9c488bd796cd8c5538f`，其結果為
  `CS:IP=0020:402A`、IF=false、mode 03h，A000／B8000／主控台／開檔／滑鼠／字型 hook／I/O 寫入皆為零，
  未實作服務亦為零。
- **confirmed**：#1,700–#3,001 的 IP timeline（SHA-256
  `cf3f6d68297619a11a47bd4178a04f84343320c0b1810b5587a76bfda4f7f12f`）有 1,301 筆、472 個不同 IP；
  #2,216 的 `0020:00D3` 後在 #2,217 到 `0020:4028`，#2,218 起為 `0020:402A`。`0020:00C8` raw 中的
  `00D3h=FF D4` 是 `CALL SP`；該次 register record 的 `SS:SP=26F5:4028`，下一筆 `SP=4026`，與以原本
  SP 為呼叫目標、壓入返回位址後的轉移相符。`0020:401E` raw 顯示 `4026h–4028h=83 C4 04`，故 direct-entry
  從其立即值 byte `4028h` 開始，再將 `04 8B` 解碼並落入 `402Ah=7E FE` 的自迴圈。`CALL SP` lifecycle／trace
  SHA-256 為 `3c4273beb6f4616ab1a25745127eebe262ae7cb681e8f936b4a75d75608eed04`／
  `89ee903750964f8341a0d591ea145b637c71439a995c2bb6cde80b778b13778e`。
- **confirmed（診斷停止線）**：從 #1,000,000 state 無輸入續跑至 #5,000,001，4,000,001 道指令後仍是
  `0020:402A`，沒有服務、檔案、畫面或 I/O 事件；終點 VRAM SHA-256 仍為
  `4f7988030a00d082fe445e00a2ac5dab502300ff1b80e8592dd569867b60ef74`，與 #1M 終點逐位元組相同。
  lifecycle／trace SHA-256 為 `9ab0b3ed3e7b363f621022df24877114fc63917ed188261492d8aec25576db61`／
  `188cea8698593edfe5593ab2b7ce834210ba0c0328ffc681bb9a1d76d9c5bb30`。
- **unknown**：正常 `OPENING.EXE`／launcher 進入 `VICEROY.EXE` 時應建立的 stack、call target、程序關係與
  後續文字路徑。當前證據只確認 direct-entry 採用了此堆疊值，沒有特定未實作 CPU、DOS、BIOS 或 EMS 服務的
  證據，故不建立 dosgolem DRAFT／READY 或任何實作。

## 退出條件

- [x] 固定輸入、冷啟動 state、工具提交、步數、raw／trace／服務收據與雜湊可重現，且原版維持唯讀。
- [x] 停滯分類為 direct-entry 的已證實堆疊控制流與正常路徑 unknown；未把程式位址、檔名或 direct-entry 誤稱為正常路徑。
- [x] 沒有建立任何中文化實作、規格、原型或原版衍生版控內容。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
