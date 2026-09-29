# 規格037：OPL3 音樂合成（DRAFT）

狀態：READY（2026-09-28，驗收見下）；DRAFT 2026-09-28（[Issue #47](https://github.com/wicanr2/colonization_cht/issues/47)）。本規格授權的是 dosgolem 的通用能力（機器層與 `audio/opl` 套件），不含本遊戲位址；本遊戲的證據只用來選擇晶片型態與驗收。

> 程序勘誤：`audio/opl` 移植與機器接線在本規格 READY 前已於隔離副本 `workplace/dosgolem` 完成（見 WORKLOG 2026-09-28）。驗收通過後才在隔離副本的本地分支 `colonization-audio` 提交 `a3a5609`（未推送；上游推送位址維持 DISABLED）。

## 原版證據（探針 `tools/probe_goal165_dialogs.go`，英國 Explorer 路徑 `e9d5cc09…`，到 7.2 億步）

| 項目 | 觀測 | 等級 |
|---|---|---|
| 音效卡 | PSOUND.COL 以 Sound Blaster Pro 的 base 0x220 偵測（規格002） | confirmed |
| OPL 寫入埠 | 0x220／0x221（第一組）、0x222／0x223（第二組）；7.2 億步內共 8,300 次寫入，其中第二組 1,985 次 | confirmed |
| 晶片模式 | 第一次 OPL 寫入即為第二組暫存器 0x05 ← 1（OPL3 NEW 模式開啟），之後在 14.9M 關閉、19.7M 再開啟；第二組寫過 0x04（四運算子連接選擇）與 0x20～0x45 等運算子暫存器 | confirmed：本遊戲以 OPL3（YMF262）模式驅動音樂 |
| 計時器 | 0.9M 步把 PIT 通道 0 分頻設為 1960（約 608.8 Hz）；dosgolem 的計時器中斷間隔隨分頻改為 19,024 道指令 | confirmed |

## 設計

1. **合成核心：**`audio/opl` 為 ymfm（Aaron Giles，commit `81aec25`，BSD-3-Clause）OPL2／OPL3 核心的 Go 移植，只用標準函式庫；10 組固定暫存器序列與 ymfm C++ 原版逐樣本相同（`audio/opl/opl_test.go`、`workplace/reports/goal167-opl/ref.cpp`）。授權全文在 `audio/opl/LICENSE.ymfm`，發行包須附上。
2. **機器接線：**`Machine.EnableOPLSynth(opl3 bool)` 建立晶片並寫入目前暫存器檔；每次 OPL 資料埠寫入前，先把聲音補產到當下指令數，再把暫存器寫進晶片。OPL3 四路輸出取 A 為左、B 為右聲道；OPL2 單聲道左右相同。
3. **時間基準：**與計時器中斷相同的指令數時鐘。第 S 道指令時應已產生的取樣數為 ⌊S × rate × 264 × 17000 ÷ (165000 × 315,000,000)⌋（315e6/264 為 PIT 基頻的精確分數），整數運算、跨平台逐位元組相同。OPL3 取樣率 14318181/288 = 49,715 Hz。
4. **不影響原版：**合成器只讀寫入序列、不回寫任何機器狀態；開啟與否，原版 CPU、RAM、畫面與時間必須完全相同。合成器狀態不進快照，從快照還原後重新開啟。
5. **介面：**`AudioRate()`、`FlushAudio()`、`DrainAudio()`（交錯 int16 立體聲）。前端的播放、音量與取樣率轉換屬 #49。

## 驗收結果

- **開關合成不影響原版：**同一輸入開啟與不開啟合成，終點 CPU 暫存器、旗標、完整 RAM、索引畫面、畫布、色盤、指令數、計時器次數、畫格數全部相同。
- **與 ymfm 原版逐樣本相同：**把本遊戲路徑的實際 OPL 寫入序列（`w.opl.json`，含每筆的指令數），以同一取樣換算公式轉成 ymfm C++ 參考程式的序列（`workplace/reports/goal168-audio/to_seq.py`），原版合成的 3,090,852 個取樣（62.2 秒）與 dosgolem 機器輸出的左右聲道逐樣本相同。這一次同時驗證了移植核心、機器接線與時間換算。
- **決定性：**同一輸入兩次合成的 WAV 逐位元組相同。
- **音量：**每 5 秒區段 RMS 約 700～1,600、峰值 3,900～9,200，全段連續、無削波。
- **dosgolem 既有測試：**`go test ./...` 全部通過（含新增的 `internal/machine/opl_synth_test.go`、`audio/opl`）。
- **未做：**DOSBox-X 錄音交叉檢查。本機 DOSBox-X 映像要靠映射鍵觸發錄音，無法無人值守；音色與速度的正確性改由「與 ymfm 原版逐樣本相同」加上「dosgolem 計時器與步數時鐘一致」保證。樂器音色是否與實機 OPL3 相同，取決於 ymfm 本身的準確度（ymfm 為 MAME 採用的 FM 核心）。

## 未知

- 數位音效（Sound Blaster DSP／DMA）是否被本遊戲使用：#48 取證。
