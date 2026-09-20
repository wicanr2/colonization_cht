# READY 規格 002：Colonization 的最小 Sound Blaster Pro／OPL 設定檔

狀態：READY（只授權 Issue #23 的最小實作與同狀態驗證）  
日期：2026-09-20  
對應 Issue：[ #22 ](https://github.com/wicanr2/colonization_cht/issues/22)；後續
[Issue #23](https://github.com/wicanr2/colonization_cht/issues/23)  
取代範圍：[規格草案 001](001-colonization-sbpro-opl-profile.md) 的 READY 未知項；DRAFT 與其
證據保留，不刪除。

## 1. 玩家可見範圍與停止線

本規格只授權 dosgolem 的 `cmd/probe` 在明確選用時，為固定版本的
`OPENING.EXE → PSOUND.COL` 冷啟動提供 base `0x220` 的最小 Sound Blaster Pro／OPL 埠面。
目的是讓正式路徑不再因未實作的 Sound Blaster 相容 I/O 立即把裝置偵測視為失敗，並取得下一張
dosgolem 原版收據。

這不是音效完成、PCM／DMA／PIT 模擬、播放品質、首畫面或主程式轉交的完成聲明。若啟用後仍沒有
可見／轉交收據，Issue #23 只能記錄新的最小 blocker，不能擴大成本輪已批准的硬體模型。

## 2. 固定輸入、工具與位址空間

| 項目 | 固定值 | 等級 |
|---|---|---|
| 正式入口 | `OPENING.EXE`，SHA-256 `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` | confirmed |
| 音效 overlay | `PSOUND.COL`，48,599 bytes，SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87` | confirmed |
| 執行器 | `workplace/dosgolem` commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf` | confirmed |
| 起始 state | `opening-1000000-visible-20260920.state`，SHA-256 `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab` | confirmed |
| 全 I/O 動態收據 | `probe-colonize-dos-opening-psound-all-io-regs-20260920.txt`，SHA-256 `b251321deddcdeb60c964cfe14e704bb8a46399d322dbfb75cf7f67b7d117294` | confirmed |
| IDA 窗口匯出 | IDA Pro 9.4 image `ida-pro-9.4-idapython:locked-v1`；`psound-ida-window-20260920.json` SHA-256 `72430df84e4b47683e077007d7c9481e5f61d158f29ef8b5735796b00a06947b` | confirmed |

IDA 的 `.COM` 一次性載入副本以 `0x10000 + 檔案位移` 為線性 EA；正常 cold boot 將同一
`PSOUND.COL` bytes 載入 `CS=1C43`。因此，IDA `0x121E6` 表示檔案位移 `0x21E6`，對應
執行期 `1C43:21E6`；`0x220`、`0x22A` 等則是獨立的 I/O port，不能和 EA 混寫。

## 3. 原版證據與結論等級

### 3.1 OPL primary status 是有效偵測條件

IDA `0x10401`–`0x1047B` 的原始 bytes 顯示，`PSOUND.COL` 在 `0x1041C`（`EC`）先讀 base
status，設定 timer 後在 `0x1043E`（`EC`）再讀一次；`0x1045D`／`0x1045F` 以 `AND 0xE0` 和
`CMP 0xC0` 判斷第二次結果，同時要求第一次的遮罩結果為零。這是可辨識的 AdLib
`0x00 → 0xC0` 偵測序列，不是單純延遲。

固定 state 的動態收據確認 `1C43:041C` 對 `DX=0220` 命中 45 次、`1C43:043E` 對
`DX=0220` 命中 9,001 次。預設 `Machine.In8(0x220)` 是未處理回退 `0xFF`，故此偵測在
現行 probe 不會取得要求的序列。這表示「此偵測常式在預設相容層失敗」是 **confirmed**；
「它是整個無畫面的唯一原因」仍只是 **strong inference**。

### 3.2 OPL advanced status 沒有本版消費者

`0x1050A`–`0x10532` 先後對 base + 0／+ 1 與 base + 2／+ 3 做 address/data 寫入。每次
address 寫入後的四個 `IN AL,DX`（例如 `0x1052B`–`0x1052E`）後沒有讀取、比較或分支 `AL`：
程式直接遞增 `DX`、覆寫 `AL` 為資料位元組、再輸出。因此固定路徑對 `0x222` 的讀取是 delay，
不消費 status 值；這個「不影響本條控制流」結論為 **confirmed**。

Creative 的 [Sound Blaster Series Hardware Programming Guide](https://www.ardent-tool.com/sound/Sound_Blaster_HW_Programming_Guide_1st.pdf)
表 A-11 將 base + 2 定義為 advanced FM status read／address write，但沒有提供本實作所需的
advanced status 位元結果。其硬體精確值在本規格是 **unknown**，不假裝成 OPL3 parity。

### 3.3 DSP reset handshake 是具體的成功／失敗分支

動態收據在正常路徑實際命中：

| 執行期位置 | I/O | 次數／行為 | 等級 |
|---|---|---|---|
| `1C43:2119` | `IN 0x22C` | 1,500 次，輪詢 write-buffer status。 | confirmed |
| `1C43:21E6`、`21ED` | `OUT 0x226` | 三組 `1 → 0` reset。 | confirmed |
| `1C43:2135` | `IN 0x22E` | 192 次，即每組 reset 最多 64 次的 read-buffer 輪詢。 | confirmed |
| `1C43:2142` | `IN 0x22A` | 192 次，讀取 reset reply。 | confirmed |

IDA `0x121DD`–`0x12205` 的 bytes 對應上述位置：寫 `0x226=1`、四個 `IN` delay、寫 `0x226=0`，
接著最多 64 次呼叫；若讀到的 `AL` 不等於 `0xAA`，設 `AX=2` 並帶 carry 返回，否則回傳零。
在預設 probe，`0x22E` 的通用 `0xFF` 回退使讀取立即進入 data path，而 `0x22A` 同樣得到 `0xFF`，
所以每一組均耗盡 64 次。這個 reset 常式失敗為 **confirmed**。

公開指南的表 2-1 與 reset 程序說明 base + 6 的 `1 → 0`、base + E bit 7 表示讀取資料可用、
base + A 回應 `0xAA`；它也規定 base + C bit 7 為零時可寫 command/data。這是
hardware-spec approximation 的平台前提，不冒稱逐週期實機重現。

## 4. READY 介面與狀態契約

### 4.1 明確啟用與失敗即關閉

Issue #23 必須新增 `cmd/probe -sbpro` 布林旗標，預設 `false`。旗標為 `false` 時，
`machine.New()`、所有 port 回退、`-adlib` 行為與既有測試必須位元相同；不得為本遊戲悄悄改變
全域預設。旗標為 `true` 時僅啟用 base `0x220` 的設定檔，並同時啟用既有 AdLib status 模型。
base `0x240` 或其他未證實基址不得由此旗標猜測支援。

設定檔應直接附著於一般 `Machine`，不可把 LE/DOS4GW 的 `LEOPLPorts` 當成可直接掛載的元件；
後者還帶 DMA、PIC、時鐘與另一個 `Machine` 的狀態，會擴張本規格的玩家可見風險。

每次設定檔 I/O 必須保留實體 port 的 `PortsIn`／`PortLog` 與一次 `portTicks` 前進；不得用
遞迴呼叫別的 port 而漏記或雙計時計數。原版 port 不在下表時維持既有 `Machine` 行為。

### 4.2 已授權 port 行為

| port | 啟用後行為 | 證據等級與限制 |
|---:|---|---|
| `0x220` 讀取 | 以既有 `oplStatus()` 回應；必須具有 `SetAdLib(true)` 的 `0x00 → 0xC0` timer 偵測行為。 | confirmed 原版 consumer；既有 `TestOPLDetectionSequence` 覆蓋模型。 |
| `0x220`／`0x221` 寫入 | 分別選擇／寫入既有 OPL primary bank，等價於原 machine 的 `0x388`／`0x389` 狀態更新。 | confirmed 原版 I/O。 |
| `0x222` 讀取 | 固定回傳 `0xFF`，但仍記錄實體讀取與 tick；這是**本版未消費 delay 的決定性回退**，不是硬體 status 宣稱。 | confirmed 無 consumer；硬體精確值 unknown。 |
| `0x222`／`0x223` 寫入 | 分別選擇／寫入既有 OPL secondary bank，等價於 `0x38A`／`0x38B`。 | confirmed 原版 I/O。 |
| `0x226` | 交給既有 `SoundBlasterDSP` reset 狀態機；只接受 `1 → 0`。 | confirmed reset consumer。 |
| `0x22E`／`0x22A` | reset 後依既有 DSP 回應 queue 回傳 status bit 7／`0xAA`，讀取 `0x22A` 消費 reply。 | confirmed 原版 consumer，且符合公開 DSP 契約。 |
| `0x22C` 讀取／寫入 | 未 reset 時讀取回 write-buffer ready（bit 7 clear），寫入交給既有受限 DSP command 模型；reset 中 read 為 busy。 | confirmed status consumer；未在本基線送出的 command 值不宣稱已支援。 |

現有 `SoundBlasterDSP` 已有上述 reset／reply 行為，且 `TestDSPResetHandshake` 通過；實作只可重用其
明示的受限子集。若啟用 profile 後原版第一次送出的 command 不在此子集，Issue #23 必須記錄
command byte、callsite、consumer 和可見後果，回到新的 DRAFT；不得把未知 command 當成成功。

## 5. 實作前後的驗收

### 機器層單元測試

Issue #23 至少新增或調整下列測試；它們只證明 dosgolem 內部契約，不等於原版 parity。

1. profile 關閉時 `0x220`、`0x222`、`0x22A`、`0x22C`、`0x22E` 維持既有回退，且不改 OPL／DSP 狀態。
2. profile 啟用時 `0x220` primary status 通過既有 `0x00 → 0xC0` 偵測；primary 與 secondary
   address/data bank 獨立保存。
3. `0x222` 回傳 `0xFF` 的明示差異只可伴隨讀取計數／tick；測試名稱與註解不得稱它為 OPL3 hardware
   status。
4. `0x226=1`、延遲讀取、`0x226=0` 後，`0x22E` bit 7 設定、`0x22A=0xAA`、再讀 status 清除；
   `0x22C` busy／ready 行為符合既有 DSP 測試。
5. 所有實體 port 只記錄一次，且 `-sbpro` 不改變未選用 profile 的輸出。

### dosgolem 原版 oracle

使用固定輸入與第 1,000,000 指令 state，執行兩組相同參數的 `OPENING.EXE` 重播到至少第
2,000,000 指令：一組預設、另一組 `-sbpro`。收據必須記錄兩組設定、dosgolem commit、輸入與
state SHA-256、完整命令、步數、`1C43:21E6/2135/2142` hit、`0x22A` 回應、`CS:IP`、EXEC、VRAM
非零數與未實作服務。

合格不等於首畫面：至少要顯示 profile 組的 reset 常式在 `0xAA` 首次回應後不再耗盡 64 次；再由
正式冷啟動的可見／轉交收據判定 Issue #23 是否完成。若 profile 組仍無畫面，保留原版 oracle 的
差異，不以綠色機器層測試宣稱中文化可用。

## 6. 已知差異、權利與回退條件

- advanced status 的實機位元值、PCM、DMA、PIT、DAC、IRQ 與音訊輸出均不在此 READY 的實作承諾；
  其中 `0x222=0xFF` 是受限正常路徑的決定性回退，不是 Creative／Yamaha 硬體宣稱。
- 本規格只適用表中固定 SHA-256、base `0x220` 與 `OPENING.EXE` 正式路徑；低階的通用
  `-sbpro` profile 不保存遊戲雜湊，故輸入身分綁定由本專案的 probe 命令、state 收據與交付層負責。
  在其他輸入上使用這個旗標只能是診斷，不能被引用為 Colonization 相容或對拍證據。
- 原版檔、IDA 資料庫、動態報告、原文／畫面與聲音均留在 gitignore 的 `workplace/`，不納入 Git、
  GitHub Release 或公開封包。
