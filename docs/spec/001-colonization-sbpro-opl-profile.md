# 規格草案 001：Colonization 的 Sound Blaster Pro OPL 埠設定檔

狀態：SUPERSEDED（固定 `OPENING.EXE → PSOUND.COL` 路徑已由
[READY 規格 002](002-colonization-sbpro-opl-profile-ready.md) 取代；本 DRAFT 證據保留）
日期：2026-09-20  
對應 Issue：[ #22 ](https://github.com/wicanr2/colonization_cht/issues/22)  
前置收據：[目標 006](../goals/006-dos-first-visible-checkpoint.md)  
後續實作閘門：[Issue #23](https://github.com/wicanr2/colonization_cht/issues/23)

## 目的與邊界

本草案只定義讓 dosgolem 在**明確啟用**時，能向《Sid Meier's Colonization》的
`PSOUND.COL` 提供最小 Sound Blaster Pro 相容 OPL 埠面。它是取得首個可見／轉交收據的
執行器相容性前置條件，不是中文化功能、音訊模擬器重寫，也不是「音效已正確播放」的聲明。

設定檔預設必須關閉；未選用時既有 `machine.New()` 與 `cmd/probe` 的埠行為不得改變。原版檔案、
`workplace/dosgolem` 以外的專案工作樹，以及輸出階段的中文轉譯層均不在本規格修改範圍。

## 固定輸入、工具與位址空間

| 項目 | 固定值／意義 | 等級 |
|---|---|---|
| 遊戲入口 | `OPENING.EXE`，SHA-256 `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` | confirmed |
| 音效 overlay | `PSOUND.COL`，48,599 bytes，SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87` | confirmed |
| 執行器 | 獨立副本 `workplace/dosgolem` commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf` | confirmed |
| 重播 state | `opening-1000000-visible-20260920.state`，SHA-256 `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab` | confirmed |
| 埠寫入 TSV | `opening-1000000-2000000-audio-ports-20260920.tsv`，SHA-256 `cfe22ede3c12e99839dc095adebda040af5bf87cbebc0fb5fdc9b449c813620e` | confirmed |
| 動態暫存器收據 | `probe-colonize-dos-opening-psound-io-regs-20260920.txt`，SHA-256 `b1ebba500d9a120fa39233ac6b6df99db877e032d693ccb1836ef887d4bff484` | confirmed |
| IDA 匯出 | IDA Pro 9.4 image `ida-pro-9.4-idapython:locked-v1`（image SHA-256 `6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`）；輸出 `psound-ida-io-com-20260920.json` SHA-256 `6d4456fc2b308ce3e47495efc7793690a10da2daa4a5ac1b373272b52ee9d6d6` | confirmed |

地址空間不可混用：IDA 以同一原始 bytes 的 `.COM` 載入副本，線性位址為
`0x10000 + 檔案位移`；正式冷啟動把 `PSOUND.COL` 載入 `CS=1C43`，因此同一 bytes 的
檔案位移 `0x82` 對應 IDA `0x10082` 與該次執行的 `1C43:0082`。I/O port 則是獨立的
16 位元 port 空間，不能當作記憶體位址。

## 已審查的證據

### 遊戲實際行為

IDA 在 `0x1007D`–`0x10087` 解碼出：`push ax`、`push cx`、`mov cx, 0Ah`、
`in al, dx`（`0x10082`，原始 bytes `EC`）、`loop 0x10082`、復原暫存器後返回。固定 state
的正常 `OPENING.EXE` 路徑確實反覆執行這個位置：先以 `DX=0x220` 讀十次，再以
`DX=0x222` 讀十次。這是動態位置與同一原始位元組的對照，並非只由靜態掃描推測。

在目前預設機器，第一個 `0x222` 讀取前為 `AX=0x0300`，下一指令可見
`AX=0x03FF`；亦即 `AL` 得到未處理埠預設回傳值 `0xFF`。`0x220` 的十次讀取同樣維持
`AL=0xFF`。同一重播區間的寫入數為：`0x220` 9,802、`0x221` 9,802、`0x222` 9,621、
`0x223` 9,621、`0x226` 6；`0x226` 的三組 reset 邊緣是 `01 → 00`，其起始指令為
1,006,406、1,034,291、1,060,853。

上述讀取迴圈只作固定次數延遲，沒有依 `AL` 分支；它證實這兩個 status port 在實際路徑被讀取，
但不證實此迴圈的回傳值造成目前停止，也不證實之後沒有其他會檢查 status 的路徑。

### 公開硬體契約

Creative 的 [Sound Blaster Series Hardware Programming Guide](https://www.ardent-tool.com/sound/Sound_Blaster_HW_Programming_Guide_1st.pdf)
附錄 A、表 A-10／A-11 將工廠預設基址列為 `0x220`，並定義 Sound Blaster Pro 的 OPL port
角色如下；這只提供裝置介面，不提供本遊戲已成功啟動的證明。

| 埠 | 公開角色 | 本版觀察 |
|---:|---|---|
| `0x220`（base + 0） | 第一組 OPL status 讀取／暫存器位址寫入 | 讀取與寫入皆已觀察到 |
| `0x221`（base + 1） | 第一組 OPL 資料寫入 | 寫入已觀察到 |
| `0x222`（base + 2） | 第二組／advanced OPL status 讀取／暫存器位址寫入 | 讀取與寫入皆已觀察到 |
| `0x223`（base + 3） | 第二組 OPL 資料寫入 | 寫入已觀察到 |
| `0x226`（base + 6） | DSP reset 寫入 | 三組 `01 → 00` 邊緣已觀察到 |

### dosgolem 現況

同一 commit 的 `cmd/probe` 只建立 `machine.New()`，而 `-adlib` 只會呼叫
`SetAdLib(true)`。預設 `Machine.In8`／`Out8` 只對 `0x388`–`0x38B` 提供 OPL 路徑；未處理
讀取回 `0xFF`。既有 `LEOPLPorts` 雖把 `0x220`–`0x223` alias 至 `0x388`–`0x38B`，但 probe
沒有掛載它，且其底層 `Machine` 刻意讓第二組 status port `0x38A` 回 `0xFF`
（`TestOPLSecondBankStatusPortUnchanged`）。因此它不是可直接宣稱符合本草案的實作。

既有 `SoundBlasterDSP` 已有受限的 `0x226` reset 與 `0x22A`／`0x22E` 讀取握手模型；
`TestDSPResetHandshake` 在目前 commit 通過。這只證明可重用元件及其測試，尚未證明
`PSOUND.COL` 在本次 200 指令動態窗內讀取了這些 DSP port。

## DRAFT 介面契約

Issue #23 若進入實作，必須以新的、明確選用的「Sound Blaster Pro OPL 設定檔」掛載至
`cmd/probe` 所用的 `Machine`，且只支援已被本版輸入證實的基址 `0x220`。不得默默把所有
`machine.New()` 都改成有 Sound Blaster。

設定檔在啟用後至少必須攔截下列 port；其他未證實 port 保持既有失敗即關閉（fail-closed）行為。

| 遊戲 port | 所需路由 | DRAFT 要求 |
|---:|---|---|
| `0x220` | 第一組 OPL status／address | address 寫入送至第一組 OPL；status 讀取不得再落入通用未處理 `0xFF` 回退。 |
| `0x221` | 第一組 OPL data | data 寫入送至第一組 OPL。 |
| `0x222` | 第二組／advanced OPL status／address | address 寫入送至第二組 OPL；status 讀取需有明示、可測的第二組語意，不可把既有 `0x38A → 0xFF` 當成已驗證硬體行為。 |
| `0x223` | 第二組 OPL data | data 寫入送至第二組 OPL。 |
| `0x226` | DSP reset | `01 → 00` 必須進入既有 DSP reset 狀態；若之後觀察到 `0x22A`／`0x22E`，才把對應握手列入同一設定檔的必要驗收。 |

不要求 PCM、DMA、PIT、DAC、取樣率或音訊輸出；它們一旦成為玩家可見阻塞，應依公開規格做
hardware-spec approximation，而不是重啟逐週期硬體考古。

## READY 升級條件與目前阻擋

本文件**尚未升級為 READY**。下列任一項未補足前，Issue #23 不得實作：

1. 以 OPL3 的權威文件或可重播的偵測／控制流，定義 `0x222` status 的位元語意與測試期望值；
   公開 port 角色本身不足以把 `0x38A` 的既有 `0xFF` 回退替換成任意常數或複製第一組 status。
2. 以較長但有界的正式路徑 trace，確認 `0x226` reset 後是否實際讀取 DSP reply／write-buffer
   status，以及那些 port 是否是本遊戲首畫面前的必要最小集。
3. READY 必須列出單元測試：設定檔關閉時完整維持既有 port 行為、`0x220`–`0x223` 兩組獨立
   address/data 暫存器、`0x226` reset 邊緣，以及本節第 1 項的兩組 status 讀取。
4. READY 必須列出同狀態驗收：固定 state、輸入雜湊、設定檔開／關、步數、可見 VRAM／EXEC／
   停點比較。只有啟用後取得新的正式 `OPENING.EXE` 收據，才能把「缺少相容層導致停止」從
   strong inference 改寫為有範圍的 confirmed 結論。

因此本輪的審查結論是：`0x220`–`0x223` 與 `0x226` 的使用及預設回退已獲確認；缺少
Sound Blaster 相容 OPL 面仍是 **strong inference** 的 blocker 候選，不能宣稱為原因、不能宣稱
OPL3 status 已正確建模，也不能宣稱遊戲已能顯示畫面。

## 2026-09-20 回填：READY 收斂理由

目標 008 將本節的兩個未知項回填到同一固定輸入與正常冷啟動路徑。`0x222` 的四次讀取在
`0x1052B`–`0x1052E` 後立即覆寫 `AL` 為 data byte，沒有 consumer；READY 因而把它降為明示的
決定性 delay 回退，而不是虛構 hardware status。相反地，`0x220` 的 `0x00 → 0xC0` 檢查和
`0x226 → 0x22E → 0x22A=0xAA` reset handshake 都有原始 bytes、動態 hit 與公開契約。

因此 [READY 規格 002](002-colonization-sbpro-opl-profile-ready.md) 只授權這個有界 profile；它沒有
解除 PCM／DMA、advanced status parity 或首畫面驗收的限制。
