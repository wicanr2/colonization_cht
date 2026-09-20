# 目標 011：追溯 PSOUND 清零呼叫的參數與舊遠指標選擇

狀態：completed（Issue #24 保持開放，等待覆蓋層／載入生命週期契約）<br>
日期：2026-09-20<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 010](010-psound-out-of-range-control-flow.md)；授權邊界：[READY 規格 002](../spec/002-colonization-sbpro-opl-profile-ready.md)

## 目的

以正式 `OPENING.EXE → PSOUND.COL` 冷啟動追溯 `03CC → 03B1` 清零呼叫的實際傳參，確認
`ES:DI=1C43:0000`、`0xFA00` 清零長度與其後 `DS:621A → 0BF9:1C43` 舊遠指標選擇，分別由哪個
原始控制流與資料來源產生。此工作要判定最小缺口是在 overlay／配置生命週期、滑鼠中斷、其他
未實作機器契約，或仍屬未知；不是修正 dosgolem、改原版、音效擴張、文字抽取或中文覆蓋。

## 固定前提

- 原始輸入只讀使用者指定的 DOS `COLONIZE/` 目錄：`OPENING.EXE` SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；`PSOUND.COL` 是
  48,599 bytes、SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 執行器固定為 `workplace/dosgolem` commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，以
  `probe -sbpro` 從零冷啟動；原始輸入與 `/home/anr2/cht/dosgolem` 一律不修改。
- 目標 010 已證實：第 `834,342` 指令載入 `1C43:0BF9`，第 `1,114,003` 指令的
  `03B1:00A6` `rep stosw` 清零 `0xFA00` bytes，第 `1,230,846` 指令 `087E:005D` 以
  `jmp dword ptr ds:621Ah` 選擇 `0BF9:1C43`。
- `03B1:00A8` 是寫入指令後的 IP，不得將它誤記為寫入指令本身；既有 `03B1:0060` raw dump
  不是已證實的函式起點，新的解碼必須從動態實際命中的 entrypoint 及其 raw bytes 開始。

## 執行結果

### 已證實的清零資料流

- `03A7:000A` 以 `0140 × 00C8 = FA00` 呼叫 `03D9:02E4`，再把其回傳的
  `1C43:0000` 與寬高寫入 `DS:3910` 描述元。`0110:0DB3` 讀出這四個字組，經
  `03AF:0006` 傳給 `03B1:0008`。因此清零目標與長度來自原程式明確建立的資料流，
  並非 dosgolem 的未初始化記憶體。
- `0110:0DC1` 以 `sub al, al` 建立零填充值。`03AF` 保留引數，`03B1` 經
  `03CC:0008` 計算範圍，`09F5:0008` 將 `DX:AX=1C43:0000` 正規化，最後以
  `les di` 載入目標。在冷開機重播第 1114003 步，`03B1:00A6` 的 `rep stosw`
  明確覆蓋 `FA00` 位元組。

### 舊遠指標與清零的關係

- 執行期寫入者 `086C` 在第 834342 步寫入 `1C43:0BF9` 的位元組，並在第
  834405 至 834406 步寫入 `0C41:621A` 的遠指標 `1C43:0BF9`。
- 該遠指標在第 1230847 步由 `087E:005D` 的間接跳躍讀取；其後未觀察到指標表重寫。
  清零則在第 1114003 步覆蓋 `1C43:0000` 至 `1C43:F9FF`。
- 已證實兩者為獨立資料流、但共用同一段與同一生命週期。`086C` 可能是動態載入者，
  仍屬強推論；尚無證據將根因歸於滑鼠 `INT 33h`、DOS 服務或單一 dosgolem 服務缺口，
  故不建立 DRAFT、也不修改執行器。

### 主要收據

- 清零呼叫者：`probe-opening-clear-callers-20260920.txt`，SHA-256
  `8d6eede9229ba267cc7afe551fee5aaf1fe30f98f735a70f453fdd42deba73df`。
- 全域描述元：`probe-opening-clear-global-init-20260920.txt`，SHA-256
  `e2e9256e5ca8109b5ddfa63520a90f24bef6977fe96d3f4c9f8f076de66a150a`。
- 遠指標表：`probe-opening-far-table-flow-20260920.txt`，SHA-256
  `02da48615342961b8ae43f418b9a201dbcb13efaad4b8fb64eaf4e6baff1e445`。
- IDA Pro 9.4 安全匯出：`03A7` SHA-256
  `ce98a83277a96cf49281e5eae0bf1000fdaa3249fd430d44cc1bde1f29aea43e`，`0110`
  SHA-256 `f57f9b6dd3d0c396577178c8e5b77dad88c79764d33f742f204ba23d4cbfe403`，`03B1`
  SHA-256 `cd31ae429df6d51dee429d1266ed93d63b9360f5185fc3abaaf1463d131bd6f9`。

## 執行項目

1. 在第 `1,113,900`–`1,114,100` 指令建立有界 IP trace、段轉移、`03CC`／`03B1` 命中暫存器、
   堆疊及 runtime bytes 收據；保留每個控制轉移前後的 CS:IP、SS:SP、flags、原始位元組與絕對步數。
2. 對實際執行的 `03CC` 與 `03B1` entrypoint 建立 IDA Pro 9.4 的 16 位元 raw-binary 匯出，逐列附
   runtime 段:位移；直接解碼 `call`／`ret`／`les`／stack operand，不以反編譯器命名或錯位線性掃描判定語意。
3. 追蹤產生 `ES:DI`、block count／stride 與 zero fill 值的 register／stack 資料流，至少用動態暫存器
   與獨立 raw instruction bytes 交叉證實。若資料來自記憶體，記錄原始 operand、基底段與最近寫入端。
4. 獨立追蹤 `0C41:621A` 在清零前後的讀寫與消費；若清零呼叫與遠指標選擇無同一資料流，明確分開兩者，
   不把時間相鄰誤報為因果。
5. 僅在已證實某個缺少的通用機器契約且玩家路徑受其支配時建立 DRAFT 規格；否則將最小未知點與重跑收據
   更新至 Issue #24。不得直接改 dosgolem。

## 停止線

- 不修改 `workplace/dosgolem`、不擴張 `int 33h`、不實作音效、DMA、PCM、PIT、DAC、IRQ 或中文化功能。
- 不以 `VICEROY.EXE` direct-entry、DOSBox／DOSBox-X、記憶體注入或單一靜態反組譯取代正式冷啟動收據。
- `int 33h AX=0014` 在取得時間、callsite、輸入與返回狀態的因果收據前，只能標示假說；不得以它作為修正理由。
- 不把函式名稱、遠跳轉存在、或單一綠色測試提升為根因。

## 退出條件

- [x] `03CC → 03B1` 的動態控制轉移、entrypoint raw bytes、暫存器、堆疊與絕對步數有可重跑收據。
- [x] `ES:DI`、清零長度、填充值的來源各有可回查資料流與推論等級；未閉合部分列為未知。
- [x] `0C41:621A` 的寫入／讀取／消費與清零呼叫是否同因已明確分類。
- [x] 已建立 DRAFT 規格，或 Issue #24／`RESEARCH-LOG.md` 明確記錄最小未知點；未實作。
- [x] `CONTEXT.md`、`docs/worklist.json`、`WORKLIST.md`、`README.md`、`WORKLOG.md`、Issue #24 與 Docker
  清理狀態已同步，並完成 Git 提交與推送。
