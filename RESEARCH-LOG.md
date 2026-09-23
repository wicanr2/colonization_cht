# 研究紀錄

## 2026-09-20：目標輸入、Windows 3.x 格式與 dosgolem probe

### 輸入與權利邊界

| 本機唯讀封存檔 | SHA-256 | 清冊結果 | 等級 |
|---|---|---|---|
| `Sid Meiers Colonization (1994).zip` | `6700c6af873bc13f18a9bee7171d20f80974b6b8dfd34123a57961c2f97fc316` | ZIP，971 檔／24 目錄，解包總計 455,916,470 bytes；內容根為 `SMCol3x/`。 | confirmed |
| `第三波-殖民帝國.rar` | `a7263e4176d329a74de6572b4e2539ff0121bd6c8e293573013fdcb227287161` | RAR，86 檔／1 目錄，內容為 `Image001.jpg`–`Image084.jpg`、`Thumbs.db` 與說明書掃描計劃文字檔；未含遊戲執行檔。 | confirmed |

原始封存檔只以唯讀掛載讀取。ZIP 僅解包至 gitignore 的
`workplace/original/colwin/`；RAR 未解包。Git 追蹤清單沒有任何原版封存檔、解包內容或畫面。

### 目標執行檔

| 定位 | 大小 | SHA-256 | `file` 結果 | 等級 |
|---|---:|---|---|---|
| `SMCol3x/MPS/COLWIN/COLONIZE.EXE` | 1,175,040 bytes | `ae7d9149f056766a534fe8f0006c9512aac1e1004e9776ab3cca818e4833b650` | `MS-DOS executable, NE for MS Windows 3.x (3.10) (EXE)` | confirmed |

`COLWIN.PRF` 位於 `SMCol3x/COLWIN.PRF`（412 bytes）。ZIP 的遊戲候選 EXE 是上述
`COLONIZE.EXE`；其餘列出的 EXE 主要屬 Windows 3.x、音效驅動或安裝環境。這是封存檔清冊結論，
不是對所有遊戲版本的宣稱。

### 工具鏈

- `colonization-research:20260920-r1`：以
  `golang@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac`
  為基底，安裝 `file`、`p7zip-full`、`unrar-free`、`unzip`。
- `colonization-research:20260920-r2`：唯一替代 r1 的執行映像，僅加入
  `/usr/local/go/bin` 至 PATH；實測 Go `go1.24.13 linux/amd64`、7-Zip 26.02、`unzip` 與
  `file` 可用。所有研究執行容器均使用 `--network none`、目前 UID/GID、記憶體／CPU／PID 限制。
- `workplace/dosgolem`：獨立 clone，提交
  `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`；其 `upstream` fetch 指向原始工作樹，push URL 是
  `DISABLED`。沒有修改 `/home/anr2/cht/dosgolem`。

### dosgolem probe 收據

輸入：上述 `COLONIZE.EXE` 與其 `MPS/COLWIN` 目錄。工具：`workplace/dosgolem` 的
`go run ./cmd/probe -exe <COLONIZE.EXE> -root <COLWIN> -steps 10000 -trace 5`。
完整本機輸出在 gitignore 的 `workplace/reports/probe-colwin-ne-20260920.txt`。

結果：probe 執行 7 道指令，最後在 16 位元實模式 `CS:IP = 0110:000E`
（線性位址 `0x110E`）以 `INT 21h AH=4Ch`、離開碼 1 結束。主控台輸出：
`This program must be run under Microsoft Windows.`；開檔 0；未實作服務 0；視訊模式 03h。

結論：**confirmed**——現有 dosgolem 路徑執行的是 NE 檔的 DOS stub，尚未進入 Windows 3.10
應用程式本體。`未實作服務 0` 的觀察範圍只有 7 指令 stub，不能推論 Windows 3.x、NE loader、
Windows API、實際遊戲畫面或文字輸出已受支援。

後續：執行策略由 [Issue #18](https://github.com/wicanr2/colonization_cht/issues/18) 等待使用者決定；
在此之前不得開啟正式的動態輸出攔截實作。

## 2026-09-20：固定 Windows NE 載入面清冊

### 問題與方法

為量化固定目標的靜態載入面、而不將它誤稱為可執行 Windows 3.x 路徑，使用受版控的
`tools/ne_inventory.py` 唯讀解析同一個 `COLONIZE.EXE` 雜湊。工具輸出只含 header、表格、
模組、ordinal 與資源中繼資料，完整 JSON 留在 gitignore 的
`workplace/reports/ne-inventory-colwin-ne-20260920.json`。

執行環境為 `colonization-research:20260920-r2`（原始輸入唯讀）與
`retro-runtime-study-tools:1`（Python 3）。容器均使用 `--network none`、`--rm`、目前
UID/GID 及資源上限。命令語意如下：

```text
python3 /project/tools/ne_inventory.py \
  --exe /original/SMCol3x/MPS/COLWIN/COLONIZE.EXE \
  --output /reports/ne-inventory-colwin-ne-20260920.json
```

地址空間：此節所有 `0x...` 都是**絕對檔案偏移**；NE header 裡的 table offset 先依 NE
header 相對位址解讀，再轉成絕對檔案偏移輸出。

### 格式交叉核對

| 證據 | 結果 | 等級 |
|---|---|---|
| 自有 parser | MZ `e_lfanew` 讀為 `0x250`，NE signature 位於該偏移。 | confirmed |
| 原始位元組 | 檔案偏移 `0x3C` 為 `50 02 00 00`，偏移 `0x250` 為 ASCII `NE`（`4E 45`）。 | confirmed |
| 獨立 `file` 分類 | `MS-DOS executable, NE for MS Windows 3.x (3.10) (EXE)`。 | confirmed |

### 靜態結果

| 欄位 | 值 | 等級 |
|---|---|---|
| 輸入 | `COLONIZE.EXE`，1,175,040 bytes，SHA-256 `ae7d9149f056766a534fe8f0006c9512aac1e1004e9776ab3cca818e4833b650` | confirmed |
| NE linker | 6.1 | confirmed |
| 初始位置 | CS:IP = `0001:0000`（NE header 欄位；尚未解釋 loader 執行語意） | confirmed |
| 區段 | 33 個，其中 18 個宣告 relocation table | confirmed |
| 模組 | `WING`、`COMMDLG`、`GDI`、`KERNEL`、`MMSYSTEM`、`USER`、`WIN87EM` | confirmed |
| 匯入 relocation | 25,825 筆 relocation 中有 176 個 imported ordinal target；沒有 import-by-name target | confirmed（僅限解析到的 relocation record） |
| 資源 | 42 個項目；type ordinal 1、2、3、4、5、12、14 | confirmed |

這些資料只證實固定檔案**宣告**的靜態載入面。各 import 是否會在遊戲實際路徑呼叫、其參數、
GDI 文字輸出位置、畫面或玩家流程仍是 `unknown`；它們不能用來宣稱 dosgolem 已支援 Windows
3.x，也不能替代 Issue #18 的架構決定。

## 2026-09-20：使用者指定 DOS 輸入與 dosgolem 冷啟動

### 輸入與權利邊界

使用者指定 `Sid Meier's Colonization (1994)/SMColoni/` 為目前正式研究輸入。來源只讀掛載，
整個父目錄由 `.gitignore` 排除；完整逐檔 SHA-256 manifest 僅寫入 gitignore 的
`workplace/reports/dos-input-manifest-20260920.sha256`。

| 項目 | 結果 | 等級 |
|---|---|---|
| 目錄清冊 | 291 個檔案，390,317,887 bytes；manifest SHA-256 `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。 | confirmed |
| 啟動批次檔 | `COLONIZE.BAT` SHA-256 `4ea071484153da2716f77446fc6c7545645493fd369daf62fba8f395fa0bd9db`；其命令選擇 `OPENING.EXE` 作為 DOS 冷啟動入口。 | confirmed |
| 冷啟動 EXE | `OPENING.EXE`，87,731 bytes，SHA-256 `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`，`file` 為 MS-DOS MZ。 | confirmed |
| 後續候選 | `VICEROY.EXE`，494,910 bytes，SHA-256 `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`，`file` 為 MS-DOS MZ。 | confirmed |
| 主要載入資料 | `COLDIG.BIN` SHA-256 `19a10611d8c0e250610c37df7a92b9c28723274b6f3c9ec0d6a225c8bf54b915`。 | confirmed |

### dosgolem 收據

工具是 `workplace/dosgolem` commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`，以
`colonization-research:20260920-r2` 的 Docker 容器、唯讀 `/game`、可寫 gitignore `workplace/`
快取／報告、`--network none`、目前 UID/GID 與資源上限執行。命令語意：

```text
go run ./cmd/probe -exe /game/OPENING.EXE -root /game -steps <100000|1000000|10000000> -trace 20
```

| 指令上限 | 結果 | 等級 |
|---:|---|---|
| 100,000 | 程式仍存活，讀取 `CONFIG.COL`、`PATH.DAT`，無未實作服務、尚未切入畫面。 | confirmed |
| 1,000,000 | 程式仍存活，切入 mode 13h（#812328）、初始化 PIT／滑鼠，載入 `PSOUND.COL` overlay，完整讀取 `COLDIG.BIN`；無未實作服務，A0000 非零像素為 0。 | confirmed |
| 10,000,000 | 程式仍存活，已送 484 次 timer、維持 mode 13h 並持續資產路徑；無未實作服務，A0000 仍為 0，尚未有 `VICEROY.EXE` 的 EXEC 收據。 | confirmed |

以上結果證實 dosgolem 可以走入此 DOS 版的原始冷啟動，而不是只執行 Windows stub；但尚未證實
可見畫面、文字輸出或正常玩家路徑。報告位於 `workplace/reports/probe-colonize-dos-opening-*.txt`。

### 診斷性 direct-entry

對 `VICEROY.EXE` 的 1,000,000 指令 probe 只作比較：它完成 EMS 初始化後停留在
`CS:IP = 0020:402A`，IF=false、無開檔、mode 03h、無未實作服務、A0000 為零。這是
`confirmed` 的診斷觀察，但不代表原始啟動鏈會在同一狀態停住，也不是冷啟動或玩家路徑證據。

下一個問題是從正式 `OPENING.EXE` 路徑取得第一個可見畫面、文字輸出或可證實的轉交；由
[Issue #21](https://github.com/wicanr2/colonization_cht/issues/21) 處理。

## 2026-09-20：DOS OPENING.EXE 首個可見檢查點 blocker

### 固定方法與輸出邊界

輸入仍是唯讀 `COLONIZE/OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）與其同目錄資料。執行器為
`workplace/dosgolem` commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`；容器為固定 digest 的
`golang:1.24-bookworm`（Go 1.24.13）。所有命令均為 `--network none`、`--rm`、UID/GID 1000:1000、
1 CPU、1 GiB、PID 128，且只把 gitignore 的 `workplace/` 設為可寫。

由於使用 UID 後登入 shell 會重設 PATH，正式命令以非登入 `sh -c` 並明示
`PATH=/usr/local/go/bin:…` 執行；先前兩份僅含 `go: not found` 的暫存報告不屬遊戲收據。此為容器
啟動環境修正，不是產品或原版行為差異。

正式 probe 先在第 1,000,000 指令存下狀態：

```text
go run ./cmd/probe -exe /game/OPENING.EXE -root /game -steps 10000000 \
  -watch-video -watch-screen 500000 -screen-delta 1 -vram-sites -seg-log \
  -save-state 1000000:/workplace/reports/opening-1000000-visible-20260920.state
```

再以同一個 state（所有步數仍是絕對值）跑至 100,000,000：

```text
go run ./cmd/probe -load-state /workplace/reports/opening-1000000-visible-20260920.state \
  -root /game -steps 100000000 -watch-video -watch-screen 5000000 -screen-delta 1 \
  -vram-sites -dump-vram /workplace/reports/opening-100000000-visible-20260920.vram
```

狀態檔 SHA-256 為 `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`。10,000,000 與
100,000,000 指令的 320×200 索引 VRAM 都是 64,000 bytes、全零，且 SHA-256 同為
`4f7988030a00d082fe445e00a2ac5dab502300ff1b80e8592dd569867b60ef74`。這些原版衍生輸出均留在
gitignore 的 `workplace/reports/`，不加入 Git。

### 正式路徑觀察

| 觀察 | 結果 | 等級 |
|---|---|---|
| 實際 EXEC | 唯一 `EXEC` 為 `PSOUND.COL`，PSP `1C43`、exit 255；沒有 `VICEROY.EXE` EXEC。 | confirmed |
| 1 億指令終點 | 程式仍活著，`CS:IP=1C43:0087`、mode 13h、timer 5,215 次、A0000 0／64,000、視訊記憶體寫入 0、主控台 0 bytes、字型服務 0 次。 | confirmed |
| COLDIG 資料 | `COLDIG.BIN` 讀入 EMS page frame `D000:0000`；報告的 `@0xA0000` 是**檔案位移**，不是 VRAM 目的位址。 | confirmed |
| 視訊斷言 | 因 COLDIG 的檔案位移先前容易被誤讀為 VRAM，已從第 1,000,000 state 跑至 #1,003,543，另存線性 A0000 raw 與索引 VRAM；兩者均全零。 | confirmed |

上述明確排除 `VICEROY.EXE` direct-entry、靜態檔案資料或未對齊截圖作為正常啟動完成證據；也不宣稱
已到主選單。

### 音效埠候選與限制

從同一 state 量測第 1,000,000–2,000,000 指令區間：

```text
go run ./cmd/probe -load-state /workplace/reports/opening-1000000-visible-20260920.state \
  -root /game -steps 2000000 \
  -dump-ports 220,221,222,223,226=/workplace/reports/opening-1000000-2000000-audio-ports-20260920.tsv
```

TSV（SHA-256 `cfe22ede3c12e99839dc095adebda040af5bf87cbebc0fb5fdc9b449c813620e`）有 38,852 筆寫入：
`0x220` 9,802、`0x221` 9,802、`0x222` 9,621、`0x223` 9,621、`0x226` 6。前四組以成對
address/data 寫入 OPL 樣式暫存器。這只證實遊戲選用的 port 與序列，沒有從序列重建 PCM、DMA、PIT
或真實 wall-clock。

同一 dosgolem commit 的 `cmd/probe` 用 `machine.New()`；其預設 OPL 處理只在 `0x388`–`0x38B`。
另一個 LE/DOS4GW 專用 `LEOPLPorts` 有 `0x220`–`0x223` 的 OPL alias 與受限 DSP，但 probe 沒有接上
該裝置。故「缺少 Sound Blaster 相容 OPL 行為導致 `PSOUND.COL` 未能完成」為 **strong inference**，
不是 confirmed 因果；預設 `Machine.In8` 對未特別處理的埠回 `0xFF` 是已證實的執行器行為。

依平台規格優先停止線，公開 OPL／Sound Blaster／DMA／PIT 語意不重新由遊戲反組譯。後續只追遊戲實際
port 序列與最小玩家可見結果：先由 [Issue #22](https://github.com/wicanr2/colonization_cht/issues/22)
建立 DRAFT → READY 規格，才可由 [Issue #23](https://github.com/wicanr2/colonization_cht/issues/23) 實作與
重跑正式冷啟動。

## 2026-09-20：PSOUND.COL 的 Sound Blaster Pro OPL DRAFT 證據審查

### 固定輸入與工具

本節仍以正式 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）冷啟動，並固定
`PSOUND.COL`（48,599 bytes，SHA-256
`8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`）和第 1,000,000 指令 state
（SHA-256 `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`）。所有探測都在
`workplace/dosgolem` commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf` 的無網路、一次性 Docker
容器中執行；原版目錄唯讀、暫存收據只寫入 gitignore 的 `workplace/`。

為避免把 raw binary loader 的線性位置和真實 DOS 載入位置混為一談，使用 IDA Pro 9.4 image
`ida-pro-9.4-idapython:locked-v1`（image SHA-256
`6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`）把同一雜湊的唯讀 bytes
複製成容器內暫存 `.COM`，以 16 位元 metapc 解碼。匯出
`workplace/psound-ida-io-com-20260920.json`（SHA-256
`6d4456fc2b308ce3e47495efc7793690a10da2daa4a5ac1b373272b52ee9d6d6`）記錄 processor `metapc`、
bitness 16、IDA 線性範圍 `0x10000`–`0x1BDD7` 與輸入雜湊。先前以 `.COL` 副檔名直接載入而得到
64 位元資料庫的嘗試已拒絕，未作為證據。

地址映射：IDA `.COM` 線性 EA 是 `0x10000 + 檔案位移`；正式冷啟動的 overlay segment 是 `1C43`。
因此檔案位移 `0x82` 的相同 bytes 是 IDA `0x10082` 與這次執行的 `1C43:0082`。這是該原始位元組的
定位對照，不代表對整個 overlay 做了未驗證的 relocation 推論。

### 動態與靜態交叉證據

IDA 在 `0x1007D`–`0x10087` 解碼 `mov cx, 0Ah`、`in al, dx`（`0x10082`，bytes `EC`）和
`loop 0x10082`。從固定 state 跑 200 指令的暫存器收據
`workplace/reports/probe-colonize-dos-opening-psound-io-regs-20260920.txt`（SHA-256
`b1ebba500d9a120fa39233ac6b6df99db877e032d693ccb1836ef887d4bff484`）顯示同一 `1C43:0082` 先以
`DX=0220` 讀十次，再以 `DX=0222` 讀十次；`0x222` 的第一次讀取使 `AX=0300` 變成 `AX=03FF`。

| 證據 | 結果 | 等級 |
|---|---|---|
| 動態 PC 與原始 bytes | `1C43:0082` 對應 IDA `0x10082` 的 `EC`／`in al, dx`。 | confirmed |
| 第一、第二組 status 使用 | 正常冷啟動確實對 `0x220`、`0x222` 各執行十次讀取。 | confirmed |
| 預設回傳 | 預設 `Machine.In8` 對這兩個未處理 port 讓 `AL=FF`；`0x222` 的前後 AX 收據直接可見。 | confirmed |
| address/data 與 reset 寫入 | 固定 TSV SHA-256 `cfe22e…620e` 有 `0x220` 9,802、`0x221` 9,802、`0x222` 9,621、`0x223` 9,621、`0x226` 6 筆；三組 reset 都是 `01 → 00`。 | confirmed |
| 缺少相容層是停止原因 | port 使用、`0xFF` 回退與停在 overlay 相容，但尚未做同狀態 A/B。 | strong inference |

同一 commit 的 `cmd/probe` 只接 `machine.New()`；其一般 OPL 路徑只處理 `0x388`–`0x38B`，未知讀取回
`0xFF`。`LEOPLPorts` 雖 alias `0x220`–`0x223`，但不是 probe 的已掛載裝置，且底層測試刻意保持
`0x38A` status 回 `0xFF`。現有 `SoundBlasterDSP` 的 reset handshake 測試通過，卻沒有本輪直接觀察到
reset 後 `0x22A`／`0x22E` 的遊戲讀取；不能把可重用元件誤記成遊戲需求。

### 公開契約與審查結論

Creative 的 [Sound Blaster Series Hardware Programming Guide](https://www.ardent-tool.com/sound/Sound_Blaster_HW_Programming_Guide_1st.pdf)
附錄 A 表 A-10／A-11 定義預設 base `0x220` 的兩組 OPL address/data/status port 及 base + 6 DSP reset。
這份公開硬體契約支持埠角色，不取代遊戲的實際 trace，也不提供第二組 OPL status 的位元值。

已建立 [規格草案 001](docs/spec/001-colonization-sbpro-opl-profile.md)。它明確要求設定檔預設關閉、只
接受已證實 base `0x220`，且禁止把 LE helper 或固定 `0xFF` 當成第二組 status 的已驗證語意。READY 的
阻擋是第二組／advanced status 定義、reset 後是否讀 DSP port，以及相應單元測試和正式同狀態 A/B 收據。
因此本節不聲稱音效、OPL3、PCM、DMA、PIT、第一個畫面或主程式轉交已完成；後續仍在 Issue #22。

## 2026-09-20：PSOUND.COL 的 OPL status 與 DSP reset READY 證據

### 固定收據與位址契約

輸入仍是 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）、`PSOUND.COL`
（48,599 bytes，SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`）及第 1,000,000
指令 state（SHA-256 `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`）。執行器固定為
`workplace/dosgolem` commit `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`，所有 probe 在無網路、
一次性、唯讀原版掛載的 Docker 容器中執行。

IDA Pro 9.4 image `ida-pro-9.4-idapython:locked-v1` 對容器內暫存 `.COM` 副本作 16 位元
metapc 匯出。`workplace/psound-ida-window-20260920.json` SHA-256 為
`72430df84e4b47683e077007d7c9481e5f61d158f29ef8b5735796b00a06947b`，schema
`colonization-psound-ida-window/1`、輸入 SHA 與上述 `PSOUND.COL` 相符。IDA EA 是
`0x10000 + 檔案位移`；例如 `0x121E6` 是 file offset `0x21E6`，正式 overlay 的同一 bytes 在
`1C43:21E6`。這個映射只定位相同原始 bytes，不推測整份 overlay relocation。

從同一 state 跑至第 2,000,000 指令，將既有 140 個已解碼 I/O 候選全部設為暫存器觀察點；完整
gitignore 收據 `workplace/reports/probe-colonize-dos-opening-psound-all-io-regs-20260920.txt` SHA-256
`b251321deddcdeb60c964cfe14e704bb8a46399d322dbfb75cf7f67b7d117294`。候選中未命中者不當作使用證據。

### 實際 OPL 路徑

| 原始定位／執行期 | 行為 | 等級 |
|---|---|---|
| IDA `0x1041C`／`0x1043E`（均為 `EC`），`1C43:041C`／`043E` | base `0x220` status 讀取；前者 45 hit，後者 9,001 hit。隨後 `AND 0xE0`、`CMP 0xC0`，並比較第一個結果為零。 | confirmed |
| IDA `0x1050A`–`0x10532`，`1C43:05AE`–`05D5` | base + 0／+ 1 與 base + 2／+ 3 的 OPL address/data 寫入；`0x222` 的四個 `IN` 後未消費 `AL`，直接覆寫為 data byte。 | confirmed |
| 預設 machine | `0x220`／`0x222` 未處理回 `0xFF`；因此 primary status 偵測不可能滿足 `0x00 → 0xC0`。 | confirmed |

這確認 primary status 是原版的條件分支，second／advanced status 在此版本的實際 I/O 片段只作 delay。
它不確認 advanced status 的硬體位元值，也不確認 OPL failure 是整個無畫面的唯一因果。

### 實際 DSP reset 路徑

動態 hit 為 `1C43:2119` 的 `IN 0x22C` 1,500 次、`21E6`／`21ED` 三組 `OUT 0x226=1 → 0`、
`2135` 的 `IN 0x22E` 192 次及 `2142` 的 `IN 0x22A` 192 次。192 等於三組 reset 各 64 次輪詢。

IDA `0x121DD`–`0x12205` 的直接 bytes 顯示：high reset、四個 `IN` delay、low reset、最多 64 次
`0x22E` poll、讀 `0x22A`、`CMP AL,0xAA`；成功回傳零，失敗設定 `AX=2` 後帶 carry。在預設
machine，`0x22E`／`0x22A` 都回 `0xFF`，所以每組都完整跑 64 次並失敗。這是「預設埠模型使
PSOUND 的 DSP reset 常式失敗」的 **confirmed** 結論；對首畫面的總體影響仍為 **strong inference**。

Creative 的 [Sound Blaster Series Hardware Programming Guide](https://www.ardent-tool.com/sound/Sound_Blaster_HW_Programming_Guide_1st.pdf)
表 2-1、reset 程序及表 A-11 定義 base + 6 reset、base + E read-buffer status、base + A `0xAA`
response、base + C write-buffer status，以及 OPL3 base + 0／+ 2 的 port 角色。這是公開硬體契約；
時間、PCM、DMA、IRQ 與音訊波形未由遊戲反推。

### READY 審查

現有 `SoundBlasterDSP` 的 `TestDSPResetHandshake`、`TestOPLDetectionSequence`、
`TestOPLSecondBankStatusPortUnchanged` 與 `TestLEOPLAliasesAndDetection` 在固定 dosgolem commit
以 `go test ./internal/machine` 通過。這只確認可重用的受限模型，不是原版成功播放證據。

由於 `0x220` 的消費者、`0x222` 的無 consumer delay、`0x226 → 0x22E → 0x22A=0xAA` 的狀態轉移、
預設關閉、未證實埠的回退與同狀態驗收均已有明確契約，已建立
[READY 規格 002](docs/spec/002-colonization-sbpro-opl-profile-ready.md)。它只授權 Issue #23 的最小
`-sbpro` profile；若開啟後出現未觀察的 DSP command 或新的玩家可見差異，必須回到新的 DRAFT。

## 2026-09-20：完成目標 009 的最小 SBPro／OPL profile 與新的控制流 blocker

### 實作邊界與機器層驗證

依 READY 規格 002，僅修改 gitignore 的隔離副本 `workplace/dosgolem`，由
`d9c0c27ca9af8239c7e96272a7165e03d7da04bf` 建立本地 commit
`1b0efdf`（`feat: add optional SBPro OPL profile`）。副本 upstream 的 push URL 維持 `DISABLED`；
沒有修改 `/home/anr2/cht/dosgolem`、原始輸入或本儲存庫外的專案。

`cmd/probe -sbpro` 預設關閉，載入 state 後才明確啟用一般 `Machine` 的 base `0x220` profile。啟用時：
`0x220/0x221` 與 `0x222/0x223` 分別使用既有的 primary／secondary OPL bank，`0x220` 共用既有
AdLib status，`0x222` 固定回 `0xFF` 作本版未消費 delay；只有 `0x226`、`0x22A`、`0x22C`、`0x22E`
接既有受限 `SoundBlasterDSP`。沒有接入 `LEOPLPorts`、mixer、DMA、PCM、PIT、DAC、IRQ 或其他基址。

新增 profile 關閉回退、primary 偵測、兩 bank 獨立、`0x222` 決定性回退、DSP reset／`0xAA`、
write-buffer busy／ready 和實體 port 單筆記錄測試。隔離副本以 `colonization-research:20260920-r2`
無網路一次性容器執行 `go test ./... -count=1` 全數通過；此結果只證明 dosgolem 內部契約，不是
原版音效或首畫面 parity。

### 同狀態正式冷啟動延續

固定輸入仍是 `OPENING.EXE` SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`、`PSOUND.COL` SHA-256
`8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`（48,599 bytes），以及
`opening-1000000-visible-20260920.state` SHA-256
`21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`。所有下列 probe 均以唯讀
`COLONIZE/`、可寫 gitignore `workplace/reports/`、UID/GID 1000:1000、`--network none`、`--rm`、
2 GiB、2 CPU、PID 256 的 Docker 容器執行。

同一組第 2,000,000 指令 probe 只差 `-sbpro`：預設收據 SHA-256
`0f2a06093e7c9756ca3100a8c93826f177dd0ebb662226f0d4aa61bf089ba6c6`，profile 收據 SHA-256
`0a77100abd16183b4aee5e549ae2724ecec43bd30f288bcf1367736b4f78b324`；受限 port TSV 分別為
`cfe22ede3c12e99839dc095adebda040af5bf87cbebc0fb5fdc9b449c813620e` 與
`8edce24d7b78620cc978e1d95dddc29a842cac618a6b327de0749f9fe9366374`。原版衍生收據均留在
gitignore 的 `workplace/reports/`，不加入 Git。

| 對照點 | 預設 | `-sbpro` | 等級 |
|---|---|---|---|
| reset 首次 `1C43:2135` 的 `IN 0x22E` 後 | `AL=FF`，`BX` 從 `0x40` 繼續遞減 | 第 `1,004,424` 指令為 `AL=80`，仍是第一次輪詢 | confirmed |
| 隨後 `1C43:2142` 的 `IN 0x22A` 後 | `AL=FF`，重覆至 64 次上限 | 第 `1,004,428` 指令在 `1C43:2143` 為 `AL=AA`；該 reset 沒有耗盡輪詢 | confirmed |
| 第 2,000,000 指令開檔 | 只反覆 `COLDIG.BIN` | `COLDIG.BIN` 後讀到 `MPSLOGO.SS`、`MPSNAME.SS` | confirmed |
| 服務與畫面 | 無未實作服務、A0000 全零 | 無未實作服務、A0000 仍全零；但已有 495 次寫入 `0xAFC03`–`0xAFE03` | confirmed |

profile 路徑也實際輸出既有受限 DSP 的 `D3`、`E1`、`40` 與 `14` command 序列；本輪沒有為
`0x14` 擴張 DMA，亦不把無音訊輸出誤報為音效完成。

### 新的最小 blocker

同一 profile 從固定 state 直接重播至第 100,000,000 指令，正式收據 SHA-256 是
`2ad3495495f6673c2c3a2fa1c9011823ae795a36adb777bc762af4f37392d40d`；mode 13h VRAM 的 64,000-byte
輸出 SHA-256 是 `4f7988030a00d082fe445e00a2ac5dab502300ff1b80e8592dd569867b60ef74`，仍全零。診斷收據
SHA-256 `3f21c0edf9f365951ec1b28ca700402e8a0b40b6be9058a13fc8ea8a868814e1` 額外保留最後 128 指令、
`1C43:FA57` 暫存器命中與 runtime bytes；所有檔案仍只在 `workplace/reports/`。

`PSOUND.COL` 的固定檔案範圍是 offset `0x0000`–`0xBDD6`。profile 路徑第一次觀測到
`1C43:FA57` 是第 `1,451,566` 指令，因此該 offset 已在固定映像外；不是本節已定位的原始
`PSOUND.COL` byte。第 100,000,000 指令時 CPU 仍位於 `1C43:FA57`，最後 128 指令重覆
`1C43:FA44`–`FA5F`，採樣的 SP 持續下降，A0000 非零像素仍為 0，沒有新的 EXEC 或未實作 DOS
服務。這些執行位置與控制流狀態為 **confirmed**；第一個跨入該範圍的 transfer、它應載入的內容，
以及根因仍為 **unknown**。因此建立 [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24)
只定位該 transfer／堆疊邊，證據足夠時才建立新的 DRAFT；不以此收據宣稱首畫面、主程式轉交、音效、
中文化輸出或可玩性。

## 2026-09-20：目標 010 的 PSOUND 清零後遠跳轉（far jump）證據

本節固定輸入仍為 `OPENING.EXE` SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` 與 `PSOUND.COL` SHA-256
`8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`，執行器為隔離副本
`workplace/dosgolem` commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，只以 `probe -sbpro` 從
`OPENING.EXE` 冷啟動。所有收據都由 UID/GID 1000:1000 的一次性、無網路 Docker 容器產生，原版目錄
唯讀掛載；收據留在 gitignore 的 `workplace/reports/`，不含原版資料。

| 原始定位／執行期 | 觀測 | 等級與證據 |
|---|---|---|
| `086C:005D`、第 `834,342` 指令 | 寫入線性 `1D000`–`1D200` 的非零 bytes，涵蓋 `1C43:0BF9`（線性 `1D029`）。 | confirmed；dosgolem 寫入監看。 |
| `03B1:00A6`、第 `1,114,003` 指令 | IDA 16 位元解碼 `F3 AB` 為 `rep stosw`。當下 `AX=0000`、`DX=00A0`、`SI=00C8`、`ES:DI=1C43:0000`；依反覆迴圈清零 `0xFA00` bytes。監看寫入報告在指令後以 `03B1:00A8` 標示。 | confirmed；暫存器、動態寫入與 IDA runtime raw-binary 三者交叉。 |
| `087E:005D`、第 `1,230,846` 指令 | raw bytes `FF 2E 1A 62`，IDA 解碼 `jmp dword ptr ds:621Ah`；下一步第 `1,230,847` 進入 `1C43:0BF9`。 | confirmed；IP log、暫存器及 IDA bytes。 |
| `0C41:621A` | bytes `F9 0B 43 1C`，遠指標（far pointer）是 `0BF9:1C43`。固定 state 的監看沒有後續改寫該表。 | confirmed；執行期 bytes 與寫入監看。 |
| `1C43:FA57` | 已清零的 `1C43:0BF9` 順序執行後才落入此處；它不是直接控制轉移目的地。 | confirmed；上述入口與連續 IP 收據。 |

控制流報告 SHA-256 為
`e7ff23bc6241782f9ff0d27e0783bef74b96f01fc4d2f938428cf0091e24f861`，其 IP log 是
`f084305312a1e35e448e863f9e764ff58f44314c51990a2abdc86baa3c0949f8`。`03B1` 呼叫端傾印 SHA-256 為
`80387f118eaf01bb4b570581986abc76d85c4cbb7aded8e2ef970676423d19f9`，IDA Pro 9.4 JSON 是
`c2a1cb372c449dc9aa656f7801c9ba36a1a45446888769aa7c2075ecf96ab130`。IDA 的 EA 是原始二進位（raw-binary）位址，
JSON 每列附帶 runtime 段:位移；它們不可與 `PSOUND.COL` file offset 混用。

結論是 **confirmed** 的「清零後舊遠指標遠跳轉」現象，分類為執行期初始化／覆蓋區記憶體
生命週期與控制流 blocker。`int 33h AX=0014` 是本冷啟動中唯一未實作服務，但其與此現象的因果為
**unknown**。`03CC → 03B1` 清零呼叫的參數來源及 `0C41:621A` 的選擇條件亦為 **unknown**；不得據此
修改 dosgolem、建立 DRAFT、擴張音效／硬體範圍，或宣稱已達首畫面、主程式轉交或中文化輸出。

## 2026-09-20：目標 011 的 PSOUND 清零引數與舊遠指標來源

輸入固定為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）與 `PSOUND.COL`（SHA-256
`8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`）。原版以唯讀掛載交由
dosgolem 隔離副本（commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`）冷開機重播；靜態結構
以 IDA Pro 9.4 的安全 JSON 匯出交叉驗證。以下「已證實」同時保留原始段位址與執行期段位址，
未以語意改名覆蓋原始定位。

| 推論等級 | 原始／執行期定位 | 觀察 |
| --- | --- | --- |
| 已證實 | `0110:0DB3` | 依序讀取 `DS:3910`、`3912`、`3914`、`3916`，傳遞 `00C8`、`0140`、`0000`、`1C43` 至 `03AF:0006`。 |
| 已證實 | `03AF:0006` → `03B1:0008` | 前者保留四字組與零填充值；`03B1:00A6` 以 `rep stosw` 清零。 |
| 已證實 | `03CC:0008`、`09F5:0008` | 前者以描述元欄位與範圍參數計算；後者將 `DX:AX=1C43:0000` 正規化，`03B1:0068` 以 `les di` 載入。 |
| 已證實 | `03A7:000A` | 以 `AX=0140`、`DX=00C8` 乘得 `0000:FA00`，呼叫 `03D9:02E4`，並把回傳的 `1C43:0000` 與寬高寫回 `3910` 描述元。 |
| 已證實 | `086C:00DA`、`086C:00DB` | 第 834405 至 834406 步寫入 `0C41:621A` 的遠指標 `1C43:0BF9`；第 834342 步已將目標位元組寫到該段。 |
| 已證實 | `087E:005D` | 第 1230847 步讀取同一遠指標表並間接跳往 `1C43:0BF9`；自表建立後未觀察到再寫入。 |
| 強推論 | `086C` 的行為 | 它看似動態載入程式碼；現有收據只證實寫入程式碼與指標表，不足以證實完整語意或預期服務契約。 |

時序為：描述元於第 816813 步完成寫入，目標程式碼於第 834342 步寫入，遠指標表於第 834405 至
834406 步寫入，清零於第 1114003 步發生，最後於第 1230847 步跳轉。這證實兩條資料流獨立卻共用
`1C43` 段，使可執行目標在跳轉前被原程式的明確清零覆蓋。尚未證實是哪個覆蓋層／載入生命週期條件
應防止或修正這個順序；不得據此推出 DOS、滑鼠或音訊服務的 DRAFT。

主要收據：清零呼叫者報告 SHA-256
`8d6eede9229ba267cc7afe551fee5aaf1fe30f98f735a70f453fdd42deba73df`；全域描述元報告 SHA-256
`e2e9256e5ca8109b5ddfa63520a90f24bef6977fe96d3f4c9f8f076de66a150a`；遠指標表監控報告 SHA-256
`02da48615342961b8ae43f418b9a201dbcb13efaad4b8fb64eaf4e6baff1e445`。IDA 匯出分別為 `03A7` SHA-256
`ce98a83277a96cf49281e5eae0bf1000fdaa3249fd430d44cc1bde1f29aea43e`、`0110` SHA-256
`f57f9b6dd3d0c396577178c8e5b77dad88c79764d33f742f204ba23d4cbfe403`、`03B1` SHA-256
`cd31ae429df6d51dee429d1266ed93d63b9360f5185fc3abaaf1463d131bd6f9`。

## 2026-09-21：目標 012 的 PSOUND overlay 與客體 MCB 鏈生命週期

固定輸入為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）及 `PSOUND.COL`
（48,599 bytes，SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`）。所有動態
收據由 `workplace/dosgolem` commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665` 的 `probe -sbpro`
從 `OPENING.EXE` 零冷啟動產生；原版目錄唯讀、報告只寫入 gitignore 的 `workplace/reports/`。
IDA 使用 `ida-pro-9.4-idapython:locked-v1`、16 位元 raw-binary 匯出；原始位址與 runtime 段:位移
並列，未以推測名稱取代定位。

| 推論等級 | 原始定位／步數 | 觀測 |
| --- | --- | --- |
| confirmed | `02B2:00AF → 086C:0004 → 02B2:00B4`；834,304 | 正常冷啟動的 caller／return 邊。`02B2:00A9` 將 `SS:BP-0A0` 以 far 參數傳入，動態進入時 `DS=0C41`、`DX=849C`。 |
| confirmed | `086C:0011`–`005D`；834,313–834,342 | 先 `AH=48h BX=FFFFh` 取得 `AX=8,BX=83BC`，再 `AH=48h BX=83BAh` 得資料段 `1C43`；parameter block `0C41:3945` 的 load／relocation 皆 `1C43`，接著 `AH=4Bh AL=03h` 載入 `PSOUND.COL → 1C43:0000`。 |
| confirmed | `086C:0092`–`0094`；834,362–834,363 | `AH=4Ah ES=1C43,BX=0C05` 成功；`086C:00DA`–`00DB` 隨後寫 `0C41:621A=0BF9:1C43`。 |
| confirmed | `03D9:005A`–`007D`；816,657–816,661 | raw bytes 直接把 `0x4D`、size、owner 寫入 `1C42` 的 MCB 欄位；此路徑前後使用 `AH=52h` 取得 DOS 結構，並將 `1C43:0000` 回傳至 `03A7` 的 `00C8×0140=FA00` 描述元。 |
| confirmed | `03D9:0340`–`0347`；833,824 | `AH=49h ES=2C9A` 在現行 dosgolem 回 `AX=9`。隨後 `syncMCB()` 將客體 MCB 的 owner `01→00`、size `0FA1→83BC` 並清空名稱；下一個 `AH=48h` 遂重發出 `1C43`。 |
| unknown | 真 DOS 對同一客體直接 MCB 變更與 `AH=49h ES=2C9A` 的精確服務結果 | 現有收據只證實 dosgolem 的結果；沒有以 DOSBox／DOSBox-X 或猜測性服務特例取代此未知。 |

主要收據 SHA-256：overlay lifecycle report
`4642d04be9a5df78cda90d2e2b43b4c902651712de1a2045b4ec9ad12f4c6d38`、trace
`57b8d0549b013e7f4124fd52ad2c18b080d30794c42f43243c186b7c24c2105b`、目標寫入 TSV
`a251a52033db890d94ec6d0176a9313ad878333951f32fc25e3eaf45a5ed3d7c`、caller report
`9d850d7aa9c3fd88a52c90cf5b61a991c330e39a7872e7a5ac86cf2f3c6a7cd6`、MCB report
`3c2e7ea9d42bf0a02a6167d35ac3622ab4eba66a17b815e09cc4c78e232a38c8`、MCB 寫入 TSV
`ae57b7037cd7d9089f97897e28811bb0b544158808f604991f9f53e6dc5a2bd7`。IDA JSON 分別為 `086C`
`ec997284cd45afc58a39d87b8fada14cb2cad856790d012a3894164f7db1d324`、`02B2`
`11e4826f75fe5d6afd866564b52690cc0f53673c42587641770979aa8e0af7b7` 與 `03D9`
`80116e6722036591dea4586383b83ec6fe28517b4ab332faa2bab220a8b2cae5`。

一次早期 `03D9` raw dump 將線性基底誤寫為 `0x3D900`；在產出結論前已捨棄，並以正確
`03D9×16 = 0x3D90` 重取 1,280-byte runtime 視窗（SHA-256
`bb6c042374688f10bbb1a2a7d1929edf12a3f967c2c40542d2ce5063da8d4f65`）。該錯誤樣本未用於表中任何
結論或規格。

結論：`086C` 的 overlay 載入已由 callsite、parameter block、DOS service 與寫入收據交叉確認；
客體直接改 MCB 但 dosgolem 仍以私有 arena 回應並覆寫鏈，也是 confirmed。據此建立
[DRAFT 規格 003](docs/spec/003-colonization-mcb-arena-reconciliation-draft.md)，只提出通用的鏈驗證與
重新協調契約。它不授權實作，也不宣稱真 DOS 的 `AH=49h` parity、首畫面、主程式轉交、音效、
中文化輸出或可玩性。

## 2026-09-21：目標 013 的 MCB DRAFT caller 與活躍鏈審查

固定輸入、dosgolem commit、冷啟動方式與權利邊界同目標 012。新的動態收據
`probe-opening-03d9-release-lifecycle-20260921.txt`（SHA-256
`e6277db64a272db0a944755a2695bf166d742ce3c880a52e3245480f5ae57e50`）在第 810,000 至
835,000 指令觀測所有 `03D9:0312` 進入；其中兩個 callsite 與返回邊如下。

| 推論等級 | 步數／原始定位 | 觀測 |
| --- | --- | --- |
| confirmed | 833,812；`0B35:0348 → 03D9:0312` | stack far pointer 令 `les ax,[bp+6]` 取得 `ES=2C9A`；現行 `AH=49h` 回 `AX=0009`，wrapper 轉為 `FFFF`。返回後先無條件跳到 `0B35:034E`，再以 `mov ax,[bx]` 覆寫返回值。 |
| confirmed | 833,861；`08D2:0207 → 03D9:0312` | stack far pointer 令 `ES=2C5D`；同樣 `AX=0009 → FFFF`。返回後 `08D2:0207` 以 `mov ax,[bp-0Eh]`、`mov dx,[bp-0Ch]` 覆寫，才比較自己的 pair。 |
| confirmed | `03D9:0340`–`035F` | IDA raw bytes 顯示 `AH=49h` 後依序為 `rcr al,1`、`cbw`、`mov al,ah`、儲存 local、最後回傳 local；這解釋本路徑的 `FFFF`，但不推論真 DOS 對任一請求的結果。 |
| unknown | 真 DOS 的 `AH=49h ES=2C9A`／`2C5D` | 本輪只有 dosgolem 正式冷啟動收據；兩個 caller 忽略 wrapper 的 register return，不能據此宣稱原版要求成功釋放。 |

`AH=52h` 與直接寫入的交叉收據是 `probe-opening-ah52-mcb-20260921.txt`（SHA-256
`562d798ad3919c8cca53173efed28671106a948cb738c5e595e0c7e0d00ac6ea`）及 trace（SHA-256
`356a759a3f2e5ec16efa51b5efc614f8c44d45e06819d090a5f048cea41f04de`）。第 816,494 指令的
`AH=52h` 回 `ES:BX=0070:0010`；List-of-Lists `0070:000E` 在直接寫入前後一致。IDA Pro 9.4
runtime raw 匯出 `ida-opening-0419-ah52-runtime-20260921.json`（SHA-256
`1073e393b37ad9b23c5fd31a1d189d6d1446d6b6d9c33a6fb0ee0f64a3a8dd2d`）顯示
`0419:0005`–`0009` 呼叫 `AH=52h` 後讀 `ES:[BX-2]`，再以 owner、type、size 和下一段公式走訪。

| 推論等級 | 原始定位／步數 | 觀測 |
| --- | --- | --- |
| confirmed | `03D9:006D`、`0071`、`0079`；816,657–816,661 | runtime raw 依序以 `mov byte ptr es:[di],4Dh`、`mov es:[di+3],dx`、`mov es:[di+1],ax` 改寫 `1C42` 的 type、size、owner；動態值為 `ES=1C42`、`DI=0`、`DX=0FA1`、`AX=0001`。 |
| confirmed | `03D9:007D`–`0083` | 將 `ES+1` 回傳為資料段 `1C43`。 |
| confirmed | 816,674；`0419:005A` | 直接寫入後立刻呼叫前述鏈走訪 helper，與 `AH=52h` 的 active chain 相連。 |
| confirmed | `1C42` 監看 | type、size、owner 後續填入 `$sys$` 名稱。監看 IP 為寫入後的下一取樣點，故以 IDA raw bytes 決定實際 store 指令，不能倒置兩者。 |

結論：`1C42` 是活躍（active）MCB 鏈的 confirmed 成員，並非私有暫存；現行 dosgolem 在無關的
`AH=49h` 失敗後以過期 arena 重發佈該鏈，才讓下一次 `AH=48h` 重用 `1C43`。DRAFT 規格 003 因而
保留並修訂為「先接受已驗證鏈，且服務失敗不可覆寫已接受鏈」；它仍未具備完整驗證、owner／多行程、
失敗回傳、state round-trip 與同狀態冷啟動驗收，狀態保持 DRAFT，未實作任何 dosgolem 或遊戲特例。

## 2026-09-21：目標 014 的 MCB 完整快照與可表示性審核

固定輸入仍是 `OPENING.EXE` SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`、`PSOUND.COL` SHA-256
`8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`，執行器是隔離副本
`workplace/dosgolem` commit `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`。一次性、無網路、UID/GID
1000:1000 的 Docker `probe -sbpro` 在第 816,800 指令（客體直接寫 MCB 後）與第 833,760 指令
（下一次 `AH=49h` 前）各擷取 `00000h`–`9FFFFh` 的完整記憶體。過程報告
`probe-opening-mcb-full-snapshots-20260921.txt` SHA-256 為
`c86ab527bd9bad511fd0df18e87a8b2c3d256a63758e039efebd39da70972531`；兩個 655,360-byte 快照分別為
`dca049b8d138b930d4e68f45b9c411efdc4d2a22a5092dfb530a9ab1d604ff2a` 與
`f284882deffd50af9a1294b75b12287100bb7a9f771efed7a0c4101ec7b8fa37`。離線 MCB 解析收據
`opening-mcb-chain-audit-20260921.json` SHA-256 為
`03d192246084c4564e1d247fb5b025596bc5cfc4f2fd406f746d4944ccd37c3f`。收據皆留在 gitignore 的
`workplace/reports/`，不含原版檔案。

| 推論等級 | 時點 | 從 `0070:000E` 讀出的鏈 | 觀測 |
|---|---|---|---|
| confirmed | 816,800 | `00FF` M/owner `0100`/size `1B42`/8 空白 → `1C42` M/`0100`/`0FA1`/`$sys$` → `2BE4` Z/`0000`/`741A`/全零 | 每步依 `next=segment+1+size` 前進，最後抵達 `9FFF`。 |
| confirmed | 833,760 | 前兩格相同，接 `2BE4` M/`0100`/`0077`/`FONTINTR` → `2C5C` M/`0100`/`003C`/`$sys$` → `2C99` M/`0100`/`0001`/`$pack$` → `2C9B` Z/`0000`/`7363`/全零 | 同樣連續並終止於 `9FFF`；客體寫入的 name 不是可丟棄欄位。 |

這只確認固定冷啟動可被「根 PSP `0100` 的單一 owner、free owner `0000`、連續 M/Z 鏈」嚴格表示，
不確認非根 owner、child EXEC、TSR 或多行程鏈。固定 dosgolem commit 的 `memBlock`／state block 只含
`seg`、`size`、`free`，`syncMCB()` 又把已配置 owner 重寫成全域根 PSP，故目前狀態會遺失 owner/name。
雖然 `AH=4Bh AL=00h` 已有 child PSP／程序堆疊路徑，既有 allocator、MCB walk、state 與 EXEC 測試也
通過，但它們不驗證客體鏈反向匯入，更不是此遊戲的 parity 收據。

以 Microsoft 的 [MS-DOS 3.10 Programmer's Reference](https://ftpmirror.your.org/pub/misc/bitsavers/pdf/microsoft/msdos_3.10/8411-310-02_MSDOS_3.10_Programmers_Reference_Manual_1984.pdf)
交叉查核，`AH=49h` 以 `ES` 指向要釋放的區塊，失敗回傳 carry 與 `AX=7`（損壞 MCB）或 `AX=9`
（不正確區段／未配置）；[Undocumented DOS](https://www.bitsavers.org/pdf/microsoft/msdos_4.0/Schulman_-_Undocumented_DOS_1990.pdf)
亦支持 `AH=52h` 後由 `ES:[BX-2]` 取得首 MCB。這些公開服務契約不能決定手動建立後的
`ES=2C9A`／`2C5D` 在原始目標 DOS 版本會成功或失敗，該題仍標記 unknown。

結論：DRAFT 規格 003 現可清楚提出兩個互斥範圍：僅接受固定樣本所符合、保存 owner/name 的單一 PSP
canonical 匯入，或先研究通用多行程 owner 匯入。這是會改變資料模型、state migration、回歸範圍與
READY 時程的架構決策；本輪不自行選擇，未改任何 dosgolem 或原版資料。

## 2026-09-21：目標 015 的通用多行程 owner／生命週期證據

使用者已明確選擇通用多行程 MCB 匯入（B），排除只處理 root PSP `0100` 的 canonical 路線。這是
executor 架構範圍決定，不會把固定遊戲尚未觀測到的 child `EXEC`、終止或 TSR 模式冒稱為原版需求。
輸入與原版雜湊沿用目標 014；executor 固定於隔離副本 `workplace/dosgolem` commit
`1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，upstream push URL 是 `DISABLED`。

| 推論等級 | 證據 | 觀測 |
|---|---|---|
| confirmed（executor） | 一次性 Docker test `dosgolem-goal015-multiprocess-audit-20260921.txt`，SHA-256 `a5685e095456439500562907d5f51f96af5bccf146b9109e418149964a709f85` | 父 PSP `0100`、`freeSeg=2000` 執行 child 後得到 child PSP／MCB owner `2001`；child `AH=48h` 配得 `2014`，但其 MCB owner 與可走鏈首 owner 都是 `0100`。 |
| confirmed（executor） | 同一探針 | child 結束後 `freeSeg` 回 `2000`，arena 仍有 3 格；父下一次配置得 `2016`，不是新鮮回收位置 `2001`。這是沒有 owner 欄位的 arena 與 LIFO 游標不同步。 |
| confirmed（source） | `internal/dos/dos.go:875`、`int21.go:786`、`state.go:45`、`state.go:84` | `memBlock`／`blockState` 只有 seg/size/free；`syncMCB()` 對非 free arena block 固定寫 `machine.PSPSeg`，`WriteMCB()` 固定清空 name。process stack/current PSP 可存，block owner/name／owner-to-process 關係不可存。 |
| confirmed（內部測試） | `dosgolem-goal015-existing-contracts-20260921.txt`，SHA-256 `20c0a7c726f780ffd11dcbf755a4404a6966f76672829b245bc3eab40a79abd6` | allocator、MCB、child EXEC、TSR、handle、overlay 與 root-state 的既有選定測試皆通過；這些綠燈沒有覆蓋 child 配置後結束再由父配置的 owner-lifecycle。 |

固定 `OPENING.EXE` 的 DOS 原版收據以 `probe -sbpro` 從冷啟動跑到第 2,000,000 指令：
`probe-opening-exec-mode-audit-20260921.txt` SHA-256
`876d66ae6a8776f74deb2183de6da06e196a26b6120f5d7e72c3d54e9bb352bc`。其服務統計有一次
`AH=4Bh`，沒有 `AH=4Ch` 或 `AH=31h`；唯一 EXEC 紀錄是 overlay。再以 IDA Pro 9.4 的
raw-binary loader 用 `ida-pro-9.4-idapython:locked-v1`（image ID
`sha256:6f6d59af49d0008c4109a5295b5f374bdc007e2d1ab28cb9de08779584de2780`）輸出
`ida-opening-086c-exec-mode-20260921.json` SHA-256
`75a9da2e08543e53382ac4650f96e017314d67228b52bff30fca1549a9f39c30`。其輸入是
`opening-086c-runtime-20260920.bin` SHA-256
`67c854c8b188aa74ba617636dc749557518d3d6ef8d77d3ba1a12eafdff5efc9`，320 bytes；IDA raw-binary EA
逐列映射 runtime `086C:0057`／`0059`／`005B`，bytes `B0 03`、`B4 4B`、`CD 21`，確認為
`AL=03` overlay callsite。未觀測只限於該固定窗口，不能外推為原版永不 child EXEC／終止／TSR。

結論：B 的 DRAFT 至少必須保存每個 MCB 的 owner/name、process 存活與 parent 關係、客體 header snapshot
及其 versioned state；`AH=48h`／`49h`／`4Ah` 的跨 process 轉移不能再由 root PSP 或 `freeSeg` 猜補。
TSR、外部 owner、跨程序失敗回傳與 state migration 仍是 unknown，故沒有實作，規格 003 保持 DRAFT。

## 2026-09-21：目標 016 的多行程 service transition DRAFT 證據

本輪沿用原版輸入／dosgolem commit／隔離與權利邊界；沒有新增原版執行宣稱。目標是量現行 executor
對使用者已選 B 的 process／owner 模型缺口，並把它與固定 `OPENING.EXE` 已見的 `AL=03h` overlay 分開。

一次性、無網路的 Docker 探針 `dosgolem-goal016-process-service-audit-20260921.txt` SHA-256
`1f7a7abc73d588a124debcc926d2a65efb0917d1289439a7b2f3196f21bc7202`，以 child PSP `2001` 量得：

| 推論等級 | 受控 executor 觀測 |
|---|---|
| confirmed | child `AH=48h` 配得 `2014`，其 MCB owner 是 root `0100`；child `AH=4Ah` 後 owner 仍為 `0100`，child `AH=49h` 後才為 `0000`。這吻合 `syncMCB()` 對 arena 固定使用 `machine.PSPSeg`。 |
| confirmed | SaveState encode、gob decode 及 LoadState 都保留 child `curPSP=2001`、stack=1、arena=2、`freeSeg=2013`；`blockState` 的原始欄位只有 `Seg/Size/Free`，故 wire format 無 owner/name。 |
| confirmed | 上述 child 先 release 再 normal exit 後，`freeSeg=2000`、arena=2，父可重新配置 `2014`。這與目標 015「未 release 就 exit」後父得到 `2016` 不矛盾，兩者都顯示 `freeSeg` 與 arena 不是 owner-aware lifecycle。 |
| confirmed | TSR child `AH=48h` 配得 `2014`、owner 是 `0100`；`AH=31h DX=40h` 後 `freeSeg=2041`、arena=3，父隨後 `AH=48h` 得 `2035`。該資料段位於 PSP `2001` 起保留 0x40 段的範圍內，是現行 executor 的 retained-range overlap。 |

原始 source 定位：`int21.go:205`–`213` 在 `48h/49h/4Ah` 後均 `syncMCB()`；`786`–`800` 以 root
PSP 發布 owner；`468`–`530` 的 `4Ah` 使用 `curPSP` 移動游標但不驗證既有 arena；`exec.go:112`–`171`
建立 child 的初始 owner，`277`–`322` normal exit 只還原 `freeSeg`，`304`–`311` TSR 只上推游標；
`state.go:18`–`48` 的 v2 blockState 沒有 owner/name，`int21.go:221`–`225` 的 `AH=51h/62h` 固定回
`machine.PSPSeg`。這些均為 source／executor confirmed，不是原版 address 空間結論。

選定既有契約重跑收據 `dosgolem-goal016-existing-contracts-20260921.txt` SHA-256
`76df8429c28e3a8590863cd01eccf76805a435f467b0ff28551edf4c06cdeffe`，通過 allocator、free/coalesce、
resize、MCB walk、normal EXEC return、TSR、child PSP resize、連續 EXEC 回收及 root-state。其範圍不包含
owner/name round-trip、TSR retained range 後 parent allocation、或外部 owner／跨程序服務，不能當作這些
行為的 parity 證明。

結論：B 的下一份 READY 候選必須以 owner/name/process registry 同時驅動 MCB 發布、`AH=51h/62h`、
`48h/49h/4Ah`、`4Bh/4Ch/31h` 與 state migration；在 external owner、跨程序錯誤、客體手改 MCB、TSR
及原版同狀態收據前，規格 003 保持 DRAFT，沒有修改 dosgolem。

## 2026-09-21：目標 017 的 MS-DOS 3.10 平台契約

Microsoft 1984 *MS-DOS 3.10 Programmer's Reference Manual* PDF SHA-256
`0955283261ffdae38bc70e152be660774c68276febc325e3b11c222e77b993e1`，由 Poppler `pdftotext -layout`
擷取的文字 SHA-256 `5915e90c80d670c18796d96833d6be2a19cf571fb76077da623160682390db83`。手冊 1-183–188
明示 `48h` 配給 current process、`49h` 只釋放先前 `48h` 配得的 block、`4Ah` 的 CF/AX/BX 失敗契約；
1-196 明示 `4Ch` 關 handles、結束 current process 並回 invoking process；1-236 明示 `62h` 回 active PSP。
這些是 confirmed platform contract，與目標 016 已證實的 root owner 發布、無 owner release、寬鬆 resize、
TSR overlap、固定 root PSP 不一致。手冊未定義的跨程序／手改 MCB 行為仍 unknown，未實作。

## 2026-09-21：目標 018 的 MCB wire format 與直接改寫證據

同一份 MS-DOS 3.10 手冊 1-4–1-5 明示 MCB 的 size、owner process name、鏈及配置／釋放／縮小的
header 更新，並警告未配置記憶體的直接改寫會毀損 MCB chain。固定 `OPENING.EXE` 已證實
`03D9:006D/0071/0079` 直接寫 `1C42` 的 M/Z、size、owner，後續填 `$sys$` name 並由 active chain
consumer 使用；現行 `WriteMCB()` 卻將 `+5..+7` 清零、`+8..+15` 清空並由 `syncMCB()` 重發 root owner。
因此 importer 必須將 raw 16-byte header、typed owner/name、連續鏈與 process registry 一起驗證；矛盾
必須 fail-closed。跨程序／TSR／external owner 後果仍 unknown，未實作。

## 2026-09-21：目標 019 的 generic importer READY 審查

Docker child 診斷收據 SHA-256 `353c81a5b8ceb1c341a681df9cbd47b1efb885702bc2fa7d62798d595ac42813`：
`curPSP=2001` 但 `AH=62h=0100`，child `48h` block `2014` 的 owner=0100/name=八個空白，state v2
只有 arena/stack/curPSP。這是 confirmed executor 現況；證實 B 尚無 raw-header parser、owner-aware
registry、current-PSP service 或可表示的 state，DRAFT 003 不可升 READY、沒有實作。

目標 020 將這些 confirmed 缺口與平台契約轉成[READY 規格 004](docs/spec/004-colonization-registered-process-mcb-importer-ready.md)：
只對 registry 中 root／child owner 授權實作，external／unknown lifecycle 一律 fail-closed。這是有界的
executor spec，不是固定遊戲 child／TSR parity；實作仍尚未開始。

## 2026-09-21：目標 021 的 registered-process MCB importer 驗收

隔離 `workplace/dosgolem` 以 READY 規格 004 實作，基底提交為
`1b0efdf98ac3ab85c90cb80c3e489e935fb45665`、本地實作提交為 `1435f17`，`upstream` push URL 維持
`DISABLED`。實作把每個 MCB 的
raw 16-byte header、owner、opaque name、程序 parent/lifecycle/blocks 寫入 typed model 與 state v3；
List-of-Lists importer 對 M/Z、段落嚴格前進、唯一 Z、MemTop、free owner 與已登錄 owner 驗證，拒絕只記錄
診斷 snapshot，不改客體 bytes。這是 executor 實作結論，不是遊戲地址空間的新增結論。

| 推論等級 | 證據 | 結論 |
| --- | --- | --- |
| confirmed（內部契約） | 無網路 Docker `go test ./...` | 新增 direct `$sys$` 匯入、失敗 `49h` 不重發、unregistered owner bytes 不變、child current PSP/owner、TSR rejection、v3 round-trip/v2 rejection 測試；所有 dosgolem package 通過。 |
| confirmed（固定原版） | `dosgolem-goal021-opening-overlay-20260921.txt`，SHA-256 `2fa18b931afac4bf15f7d89a1712cb7e98de2a7e29a054097202589cb4a58e00` | `OPENING.EXE` SHA-256 `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` 以 `-sbpro` 至 2,000,000 指令仍存活，`PSOUND.COL` 在 834,342 載入並後續讀取 MPS assets；ArenaDump 保留 `$sys$`、`FONTINTR`、`$sound$`、`S$MPSLOG`、`S$MPSNAM`、`$sp-load` raw names。 |
| unknown | child EXEC／TSR 的固定遊戲路徑 | 固定原版窗口仍只見 `AH=4Bh AL=03h`；synthetic child/TSR 僅驗證 executor 的有界合約，不能外推原版需求。 |

規格狀態升為 [CONFORMED 規格 005](docs/spec/005-colonization-registered-process-mcb-importer-conformed.md)。
未登錄 owner、cross-process release/resize、未知手改 lifecycle 與 v2 state 維持 fail-closed；這並未解開
映像外控制流、產生畫面或建立文字輸出證據，Issue #24 仍開放。

## 2026-09-21：目標 022 的 MCB 修正後首個 mode 13h 畫面

固定原版仍為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`），執行器為隔離
`workplace/dosgolem` commit `1435f175e785ea096a9268cd1021a4222300bd43`，研究映像為
`colonization-research:20260920-r2`。所有命令以無網路、UID/GID 1000:1000、CPU／記憶體／PID 上限的
一次性 Docker 容器執行；原版目錄只讀掛載為 `/game`，收據留在 gitignore 的 `workplace/reports/`。

`cmd/probe` 的 state／shot callback 在迴圈執行下一道指令**之前**比對絕對步數，故以 `-steps 2000001`
搭配 `-save-state 2000000:...` 保存精確第 2,000,000 指令的狀態，而非將第 2,000,001 指令後的狀態誤稱為
檢查點。state v3 `dosgolem-goal022-opening-2m-state-v3-20260921.state` SHA-256 為
`1f9b3822fc5ad2c041714a95527a230096cee97c69181fc82f0d9feec165de6b`；冷啟動收據 SHA-256 為
`8dc607ae8d6f0abbb6b53aed38cfab76e180606d295487fa52b3065cdfa40c37`。由同一 `/game` 路徑重載 state 後，
5M、10M、20M 收據的 SHA-256 依序為
`736b9923397af4babf1b2ba685cd51523b9e8a0f917e1975c4a77d135b381f7d`、
`2c663263aa70c0ccee54d85da55d090fa48a0de09d2852ddf87674f57ab10578`、
`fe7461e1a44c0bd15e4aca4cccd8273c06759a11652731e86d9650d80d0fbf98`。

| 推論等級 | 固定 state 的觀測 | 結論 |
| --- | --- | --- |
| confirmed | 2.70M 的 VRAM-watch 收據 SHA-256 `da7b369f264d08aa1e1b1d67ae6306a16c71541154c97b8aa8c55346bb0f5f55`：A0000 0／64,000、0 筆寫入 | 首畫面尚未開始，不能把已進入 mode 13h 當成已顯示畫面。 |
| confirmed | 2.75M 的 VRAM-watch 收據 SHA-256 `cc99ad7bd806998672c02b2903d583429bcd759481d0bdf7454a4b67d5e2f152`：18,445／64,000 非零像素、18,445 筆未丟棄寫入 | 首個可見 mode 13h 畫面落在 2.70M–2.75M 指令的有界窗口；收據末段的寫入來源是 `0557:0090`。這不證實畫面語意或靜態文字內容。 |
| confirmed | 同 state 的 5M／10M／20M 皆為 18,445／64,000 非零像素，無 B8000 文字、全形／半形字型 hook 或主控台字元 | 首畫面至 20M 穩定，且尚未取得可用於動態文字鍵的輸出事件。 |
| unknown | `VICEROY.EXE` EXEC、畫面的具體語意、圖內是否含可中文化靜態文字 | 本輪沒有這些證據；不能由 `MPSLOGO.SS` 檔名或像素數推論。 |

第 2.75M 指令另由 `-shots` 匯出 320×200 色號與同時色盤；`.idx`、`.pal`、僅本地 PNG 的 SHA-256 分別為
`d78fbfe1711c5115e73d5a29b456bd5cafef42c99405408c23b711a87c8f46fc`、
`ef115a0e0c15cdc41958ca46b5b14b456115f4baec5e3ca68599d2a8f435e3b8`、
`8ef6bda61c7ae6ba2e411405edd87056782337a996a73a93099365cff25ceeb0`。它們含原版衍生像素，沒有加入 Git、
GitHub 或發行包。結論是 #24 的映像外控制流 blocker 已解除；下一步是動態輸出與靜態文字的獨立 RE，不是直接
實作中文覆蓋。

## 2026-09-21：目標 023 的首畫面繪製來源與動態文字邊界

固定輸入、state v3、執行器 commit 與 Docker 隔離條件完全沿用目標 022。從第 2,000,000 指令 state v3
重載至 2,750,000 指令，以 `-regs-at 0557:0090 -regs-from 2700000 -watch A0000-AFFFF` 重播；收據
`dosgolem-goal023-first-frame-regs-20260921.txt` SHA-256 為
`847ab8cadafa9b25203a74e46ccc5902a066bf6491da3f43ad79ef35b7cfc2d8`，所有原版衍生輸出仍只在
gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 第 2,747,686 指令 `0557:0090`：`DS:SI=1DFB:00F8`、`ES:DI=A000:1C78`、`SS:SP=0C41:84D4`；後七次 `SI` 與 `DI` 均增加 `0x140`，ES 固定 A000 | 這是從記憶體來源跨列搬運至 mode 13h VRAM 的首畫面 raster 寫入端。 |
| strong inference | 上述 raster 遞進、18,445 筆 VRAM 寫入，及目標 022 的無字型 hook／B8000／主控台字元 | 首畫面 payload 較可能是靜態點陣資料，而不是本輪可辨識的動態文字輸出。 |
| unknown | `1DFB:00F8` 與 `MPSLOGO.SS`／任何其他檔案的精確對應、畫面語意、圖內文字，以及後續玩家輸入路徑的印字常式 | 不由檔名、像素數或人眼觀感猜測；Issue #5 仍在進行中。 |

「無文字輸出」的 confirmed 範圍只限目標 022 固定 state 的無輸入 2M–20M 路徑；不能外推到其餘畫面或整個遊戲。
沒有建立 DRAFT／READY 規格，也沒有修改 dosgolem、原版或中文覆蓋。

## 2026-09-21：目標 024 的首畫面正常輸入與開場資產分支

固定輸入為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`），起點 state v3 為
`dosgolem-goal022-opening-2m-state-v3-20260921.state`（SHA-256
`1f9b3822fc5ad2c041714a95527a230096cee97c69181fc82f0d9feec165de6b`），執行器為隔離
`workplace/dosgolem` commit `1435f175e785ea096a9268cd1021a4222300bd43`。所有重播在
`colonization-research:20260920-r2`、無網路、UID/GID 1000:1000、唯讀 `/game` 與可寫
`workplace/reports/` 中執行；原版衍生 report 與 VRAM 都未加入 Git。

先以無輸入及 `-press enter -press-at 3000000` 對照。兩者的最後 mode 13h VRAM SHA-256 均為
`5e65e98edfa907abec6c33df05957cdb8716b2471e6093dbf6fa5ecd5f64822f`；後者的 probe 報告顯示 `int 09h`
未安裝，兩個掃描碼事件留在佇列，故 IRQ1 注入不構成原版消費輸入的證據。接著從同一 state 分別執行：

```text
go run ./cmd/probe -load-state /workplace/reports/dosgolem-goal022-opening-2m-state-v3-20260921.state \
  -root /game -steps 12000000 -bios-keys '\\n' -bios-key-from 3000000 -bios-key-every 2000000 \
  -watch-video -watch-screen 250000 -screen-delta 1 -log-calls -seg-log -vram-sites \
  -dump-vram /workplace/reports/goal024-bios-enter-12000000.vram

go run ./cmd/probe -load-state /workplace/reports/dosgolem-goal022-opening-2m-state-v3-20260921.state \
  -root /game -steps 12000000 -click-x 160 -click-y 100 -click-at 3000000 -click-polls 1 \
  -watch-video -watch-screen 250000 -screen-delta 1 -log-calls -seg-log -vram-sites \
  -dump-vram /workplace/reports/goal024-center-left-12000000.vram
```

完整本地 report 的 SHA-256 依序為 BIOS Enter
`83e694300a71d842fa7f0acaeb0ef7721e29c29f9aa7de17e5ec76b55605d528`、中央左鍵
`e01431d7243374723960a6924e379a081eeacec30662a5fbb9f006bae0891941`；兩個輸出 VRAM 的 SHA-256 同為
`d2add3f193e10c0b9d4d65b7fc59b10e6bd967a81bbfe1eb93a5ad4bf41166b0`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | BIOS Enter 在第 3,000,121 指令由 `int16-AH00-bda` 取走（鍵值 `0D`），第 3,000,226 指令首見 `0110:1064 → 03A7:000A`，第 3,001,287 指令首次開啟 `OPENING.PIK` | BIOS 鍵盤緩衝區的單一 Enter 使首畫面流程進入開場資產載入。 |
| confirmed | 中央左鍵在第 3,000,022 指令由 `int 33h AX=0003` 觀測為按下；第 3,000,166 指令首見同一條 `0110:1064 → 03A7:000A`，第 3,001,227 指令首次開啟 `OPENING.PIK` | 這一筆固定位置的單次左鍵也使流程進入同一開場資產載入。 |
| confirmed | 兩條分支均開啟 `OPENING.PIK`、`OPENBORD.PIK`、`OPENSHIP.SS`、`OPENCRD1.SS` 至 `OPENCRD3.SS`、`OPENWND1.SS` 至 `OPENWND2.SS`、`OPENSUN.SS`、`OPENMON1.SS` 至 `OPENMON3.SS`、`OPENFISH.SS`、`OPENGUY.SS`、`OPENLOGO.SS`、`OPENBONK.SS`；終點為 64,000／64,000 非零 mode 13h 像素 | 這兩筆輸入在本觀測窗口產生同一個開場圖像載入分支。 |
| confirmed | 兩條 2M–12M 輸入分支均為全形／半形字型 hook 0、B8000 非零 byte 0、主控台 0 bytes | 在此輸入及指令窗口仍未觀測可用的動態文字輸出事件。 |
| unknown | 首畫面的語意、Enter／左鍵是否代表相同的遊戲操作語意、`OPEN*.SS` 是否含文字、其圖像內容與後續玩家輸入序列 | 不由檔名、座標或兩條路徑輸出相同而猜測；不建立 DRAFT／READY 規格。 |

本輪只取得正常輸入與靜態資產候選序列的 RE 證據；沒有修改 dosgolem、原版檔案、遊戲行為或中文覆蓋。

## 2026-09-21：目標 025 的開場靜態圖像候選清冊

固定輸入、state v3、`OPENING.EXE` SHA-256、隔離 dosgolem commit 與 Docker 條件沿用目標 024。本輪從同一
state 以 BIOS 緩衝區 Enter（第 3,000,000 指令排入）重播至第 5,500,000 指令，使用 `-reads-of OPEN`
保留實際 DOS 檔案服務，並以 `-watch-video -vram-sites` 記錄整體畫面路徑：

```text
go run ./cmd/probe -load-state /workplace/reports/dosgolem-goal022-opening-2m-state-v3-20260921.state \
  -root /game -steps 5500000 -bios-keys '\\n' -bios-key-from 3000000 -bios-key-every 2000000 \
  -reads-of OPEN -watch-video -watch-screen 100000 -screen-delta 1 -vram-sites \
  -dump-vram /workplace/reports/goal025-opening-assets-5500000.vram
```

本地 report `goal025-opening-assets-5500000.txt` 的 SHA-256 是
`c68b153a3d68fb3e6fc481433e165012a5b6842975186339e69dd83c6760f83c`；其原版衍生 VRAM 的 SHA-256 是
`304ffd302045969ddad4a6c5e3c139a1af5f9f1bdbc1a060600b981ef26faeaf`。兩者只留在 gitignore 的
`workplace/reports/`。

| 實際載入資產 | bytes | SHA-256 | 首次開啟與主要 payload 讀取（絕對指令） |
| --- | ---: | --- | --- |
| `OPENING.PIK` | 102080 | `80ea1dd4a00a4029052112882305e573bd7e20066eb095ceabe273a217689185` | #3,001,287；#3,004,029 @193+61,440、#3,004,090 @61,633+39,640、#4,096,844 @101,273+768 |
| `OPENBORD.PIK` | 11245 | `53f73ae336b5eaca30fa190ec9059426712de6c9c0c181d085814d45c96dab03` | #4,100,718；#4,103,486 @193+10,245 |
| `OPENSHIP.SS` | 2067 | `eee07bfee9a7abf512d6bd9688409427149df3226edd024342871f41e143af10` | #4,399,346；#4,406,969 @1,037+1,030 |
| `OPENCRD1.SS` | 6320 | `6807ae8a1fd12588fd2f90699f771bdb5bd88ca9317ea49f376253e9a447a062` | #4,431,694；#4,439,735 @1,063+5,257 |
| `OPENCRD2.SS` | 14549 | `0ba68fa51daf8a801161ebaebd26015da8a4f069199c2f1bf01ba1b5d1065f96` | #4,554,793；#4,563,049 @1,074+13,475 |
| `OPENCRD3.SS` | 9426 | `179257b925ddaa4141dd89dd3ae10bbf6763219d57545643310efd9e712ada18` | #4,756,727；#4,764,757 @1,051+8,375 |
| `OPENWND1.SS` | 2467 | `774dc50231443957d2e051a39765ea1652daae7317c517ba77094b67e07d1afb` | #4,896,194；#4,904,946 @1,064+1,403 |
| `OPENSUN.SS` | 1119 | `639e0ff1eaf4fb4a9b649557c63658b0ba611caeb3ebf46da75affd342ed30bd` | #4,928,382；#4,936,926 @1,040+79 |
| `OPENMON1.SS` | 3983 | `5da6ea59ab914fe4f73947c6925bbebb85815a5213e63bbcc6cdf6d44b61e1cd` | #4,939,849；#4,950,341 @1,143+2,840 |
| `OPENWND2.SS` | 4015 | `af84ca1b7fa3deb5c93401562277c858dd4b6ef66b158ff2b2480c4e1b5578f3` | #5,003,474；#5,013,201 @1,088+2,927 |
| `OPENMON2.SS` | 3918 | `4a56a5a3646e98a51de1f0b4c3376ab9db12c00d42972b58857ff485b634a490` | #5,054,800；#5,067,822 @1,205+2,713 |
| `OPENMON3.SS` | 4975 | `4eca6df7b101b0d0ed02d9867c3c63c013ab2e4809e47ae4750ba4e33402e76a` | #5,111,944；#5,124,417 @1,209+3,766 |
| `OPENFISH.SS` | 1782 | `ee656204f4800cdd14c79a40894bd5285b6e20e0b41c574fea26c1535ce35f20` | #5,181,631；#5,192,795 @1,151+631 |
| `OPENGUY.SS` | 5292 | `5252b30f8dfa4258956a843a4e3c480969a25144564fa0944a7ac435e0889666` | #5,205,737；#5,224,861 @1,498+3,794 |
| `OPENLOGO.SS` | 5162 | `8168d9d749b8a399b8ab545cf341ad79036a09b81bae68a1758285c6bc540e1f` | #5,298,406；#5,306,518 @999+4,163 |
| `OPENBONK.SS` | 3453 | `65facf06dad88e9d5d17989a6488c74e76ffbab1b15d7c5ca0abe9c81ab74910` | #5,369,498；#5,381,831 @1,163+2,290 |

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 上表 16 項均由同一次正常輸入分支的 DOS `open`／`read` 服務讀取；不是從目錄掃描列出。每個 `file` 格式辨識均只回報 `data`。 | 它們是固定版本的實際開場資源候選；尚無通用檔案型別名稱或 decoder 結論。 |
| confirmed | 兩個 `.PIK` 均先讀 16+30 bytes、seek 至 offset 176 後讀 17 bytes；14 個 `.SS` 均先讀 16+40 bytes、seek 至 offset 176 後讀 39 或 40 bytes，再讀取不同的 metadata 與 payload 範圍。 | 這是可重播的存取表面；不能由共同讀取型態推論完整格式語意。 |
| confirmed | 第 5.5M 終點為 mode 13h 64,000／64,000 非零像素，101,639 筆 VRAM 寫入於 A0000h–AFEFDh；活躍 MCB 名稱含 `S$OPENSH`、三個 `S$OPENCR`、兩個 `S$OPENWN`、`S$OPENSU`、三個 `S$OPENMO`、`S$OPENFI`、`S$OPENGU`、`S$OPENLO`、`S$OPENBO`。 | 正常開場資源序列伴隨可見畫面繪製；八字元 MCB name 會截斷，不能單靠它建立每檔至矩形的直接對應。 |
| confirmed | 此分支全形／半形字型 hook 均為 0、B8000 非零 bytes 為 0、主控台輸出為 0。 | 本輪沒有觀測到可替換的動態文字輸出。 |
| unknown | 每一個上表資產的點陣內容、是否含文字、畫面矩形、與 VRAM 寫入端的一對一資料流，以及其中文安全覆蓋區。 | 不以檔名、大小、MCB 截斷名稱或一般畫面活動假設靜態文字；Issue #8 保持進行中，未建立 DRAFT／READY 或原型。 |

本輪沒有匯出原版內容、像素、標頭位元組或 decoder 產物到版控，亦未修改 dosgolem、原版或中文覆蓋。

## 2026-09-21：目標 026 的 `OPENING.PIK` 繪製資料流

固定輸入、`OPENING.EXE` SHA-256、2M state v3、隔離 dosgolem commit 與 Docker 條件沿用目標 024。
本輪另由無輸入重播建立第 3,000,000 指令 state
`goal026-pre-input-3000000.state`（SHA-256
`0239ae38feff005105ab769a322e5a6c87622d531f9283b84575031c63e3b7e3`），只以 BIOS 緩衝區 Enter 在
第 3,000,000 指令起排入。所有 receipt、state 與 VRAM 只留在 gitignore 的 `workplace/reports/`。

主要重播由此 state 分別限定至 4.2M 與 5.5M 指令；前者保留 `OPENING.PIK` 讀取與 `1C430h–2C42Fh`
畫布寫入，後者保留 A0000h–AFFFFh 寫入及 `0557:00A1` 暫存器。`-watch` 與 `-watch-video` 不能同時
用於此證據：probe 的 `WatchWrites` 只有一個回呼（callback），後註冊者會覆蓋前者。因此最後的精確範圍監看只用
`-watch`；這是已確認的 probe 命令組態限制，不是遊戲的繪圖缺口。

```text
go run ./cmd/probe -load-state /workplace/reports/goal026-pre-input-3000000.state \
  -root /game -steps 4200000 -bios-keys '\\n' -bios-key-from 3000000 -reads-of OPENING.PIK \
  -watch 1C430-2C42F -regs-at 0AC2:04F5 -regs-from 4090000

go run ./cmd/probe -load-state /workplace/reports/goal026-opening-post-pik-4200000.state \
  -root /game -steps 5500000 -regs-at 0557:00A1 -regs-from 4200000 \
  -dump-vram /workplace/reports/goal026-post-pik-5500000.vram
```

本地 receipt 的 SHA-256 為：A000 寫入 `0c8c6e42e7e5dab218b7d995971bfbeeeab6f9f7a2195754a09d2aa5b2a71d6e`、
canvas 寫入 `00abbe84e9ba705a7915e6ba289bae8d6c1905dfca8595068c1d4d699d97ba26`、canvas writer 暫存器
`c3ab6416446627b8c2596931a3f45a67528c132cab7fbbefcdc2754025993da0`、canvas writer bytes
`a08ebf4e6cac99798259dc4344073d9c1a9fa1083a45eb106ad13c470151d130`、VRAM writer bytes
`491fab91274734fe570b931ad297fc208f4a99c49ed059bf0a7c8441116e3c5b`、較後 VRAM writer 暫存器
`b13ce7ee95cbd632bf31cfd19b90e22d868da79e01612684df4470d24a49e32f`。4.2M post-PIK state 的 SHA-256 是
`f022f99f7a184ff0a1491e89e9ec12f8b76ff70d49d4924981ada10890671f50`；5.5M VRAM SHA-256 是
`304ffd302045969ddad4a6c5e3c139a1af5f9f1bdbc1a060600b981ef26faeaf`。

地址均為 dosgolem 的執行期 segment:offset；讀取／canvas／VRAM 範圍分別為線性 `57550h–70027h`、
`1C430h–2C42Fh`、`A0000h–AFFFFh`。程式 bytes 是同一執行期位址空間：`0AC2:04E8`（線性 `0B108h`）
之後的 `0AC2:04F4` 是 `A4`／`MOVSB`，`0557:008E`（線性 `055FEh`）之後的 `0557:009F` 是
`F3 A5`／`REP MOVSW`。監看列出的 IP 是實際寫入後的下一個 IP，分別為 `0AC2:04F5`、`0557:00A1`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | `OPENING.PIK` 在 #3,004,029 讀入 61,440 bytes 至 `5755:0000`（線性 `57550h`），並在 #3,004,090 讀入 39,640 bytes 至 `5755:F000`（線性 `66550h`）。 | 主要 payload 的 DOS 讀取目的範圍已固定。 |
| confirmed | #4,104,159 的寫入後 IP `0AC2:04F5`，`DS=5755`、`ES=1C43`、`SI=0007`、`DI=0001`；直接前一位元組 `0AC2:04F4` 是 `MOVSB`。畫布監看也保留此窗口的實際 `1C430h–2C42Fh` 寫入。 | 至少取樣的 `OPENING.PIK` 原始緩衝資料以 `MOVSB` 寫進畫布。 |
| confirmed | #5,464,375 的寫入後 IP `0557:00A1`，`DS=1C43`、`ES=A000`、`SI=0140`、`DI=0140`；後續樣本各按 `0x140` 遞進，直接前一指令 `0557:009F` 是 `REP MOVSW`。5.5M 終點的 mode 13h VRAM 為 64,000／64,000 非零像素。 | 較後有從畫布到 A000 VRAM 的完整跨列搬運。 |
| strong inference | 上述兩個已證實搬運事件分別發生在 #4.104M 與 #5.464M，且中間有 `OPENBORD.PIK` 及 `.SS` 資產載入。 | `OPENING.PIK` 的原始資料參與開場畫布建構；不能把此事升格為任何最終像素歸屬。 |
| unknown | `OPENING.PIK` 格式與圖像語意、哪一些位元組未被後續資產改寫、對應的最終矩形、是否含文字、中文安全覆蓋區，以及其他候選的同類資料流。 | 本輪沒有文字候選、DRAFT／READY 規格、覆蓋原型或可發布資產。 |

這個切片只收斂 raw-buffer→canvas→VRAM 的時間順序與原始定位；不修改 dosgolem、原版或中文覆蓋，亦不將原版衍生內容納入版控。

## 2026-09-21：目標 027 的共享緩衝區覆寫勘誤與畫布窗口

本輪由目標 026 的第 3,000,000 指令 state 建立第 4,099,000 指令快照
`goal027-pre-opening-pik-draw-4099000.state`（SHA-256
`6c0e7d69018b7590e8fbe1f1bc1bbbcac69305a90e64aae2fa1234bd844be999`），同樣只以 BIOS Enter 正常輸入。
從該 state 至第 4,157,000 指令的完整 stdout 監看收據 SHA-256 是
`13b448a5c5d326cf1361e5c34232141f78b8c2fe769e62f37b14721b5374a29d`；完整 `MOVSB` 暫存器／
`OPENBORD.PIK` 讀取收據 SHA-256 是
`f2455ea1ca2ee8e9e535d8b1eec9d320143acd41fa5bfe0b85d9e8a1c956065e`。所有原版衍生 state、
記憶體傾印與 report 仍只在 `workplace/reports/`。

目標 026 原先只對照 `OPENING.PIK` 的早期 `5755` 讀取與稍後 `MOVSB` 的 `DS=5755`，沒有驗證中間共享
緩衝區是否已改寫。第 027 輪的 DOS 服務收據補上此缺口：`OPENBORD.PIK` 在 #4,103,486 由 `AH=3Fh` 讀取
10,245 bytes 至 `5755:0000`，即執行期線性 `[57550h,59D55h)`；這在第一個畫布 `MOVSB` #4,104,159 前完成。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | `0AC2:04E8`（執行期線性 `0B108h`）的 `0AC2:04F4` byte 為 `A4`／`MOVSB`；其寫入後 IP `0AC2:04F5` 的 40 個樣本橫跨 #4,104,159–#4,156,836，均為 `DS=5755`、`ES=1C43`，`SI=0007h–0BD9h`。 | 取樣來源都落在 `OPENBORD.PIK` 已覆寫的 `[0000h,2805h)` 緩衝區區間；目標 026 不得再把它歸屬於 `OPENING.PIK`。 |
| confirmed | 完整 stdout 的 `-watch 1C430-2C42F` 有 7,680 筆不同位址、舊值均為零，範圍 `1C430h–1E22Fh`。其中 `0AC2:04F5` 672 筆、`0AC2:0551` 7,008 筆；後者前一 byte `0AC2:0550` 是 `AA`／`STOSB`。 | 這個窗口恰覆蓋 320×24 logical pixel 的第一至第 24 列；672 筆 `MOVSB` 本身是多段、非矩形分布。 |
| confirmed | 目標 026 的 #5,464,375 `0557:009F`／`REP MOVSW` 以 `DS=1C43` 至 `ES=A000` 並每列搬運 `0x140` bytes。 | 畫布位址的 320×200 座標換算只在這個共用 canvas→VRAM 契約下有效；不建立資產歸屬。 |
| strong inference | `OPENBORD.PIK` 的完整讀取、覆寫、同一緩衝區來源與其後 320×24 畫布窗口在時間上閉合。 | 這是 `OPENBORD.PIK` 載入後的處理窗口；仍未解出其格式或圖像內容。 |
| unknown | `OPENING.PIK` 的有效繪製緩衝、任何資產的最終像素矩形、文字存在、圖像語意、中文安全矩形及靜態覆蓋條件。 | 本輪不能授權 DRAFT／READY 規格、覆蓋原型或中文化實作。 |

`-watch-file` 在這個 probe 版本最後只輸出 200 筆，因此完整分布只採同次 stdout 的 7,680 筆 `[watch]` 行。
此外，`-dump-mem-at` 的裸 `1C430` 被 probe 解釋為 IDA 線性位址並轉為執行期 `0D530h`；這兩份傾印不是
畫布，已排除於所有上表結論。這是工具／命令位址空間修正，不是原版行為差異。目標 026 的錯誤結論保留在其
歷史段落與提交 `aab8652`，但目前真相已由本節、目標 027、`CONTEXT.md`、README 與工作清單取代。

## 2026-09-21：目標 028 的 `OPENBORD.PIK` 緩衝區存續與取樣畫布資料流

固定輸入、2M state v3、隔離 dosgolem commit 與第 4,099,000 指令 state 沿用目標 027。以同一 state 重播至
第 4,157,000 指令，對 `[57550h,59D55h)` 同時啟用 `-watch`、`-read-watch` 與粒度 1；原版輸入維持 `/game:ro`。
生命周期 report 的 SHA-256 是
`0b57893bf4f9e6be3d1230e3a03746572c2231a9b905e55201fcaab01f14e827`，讀取監看 TSV 的 SHA-256 是
`61e845f0fedb89696fb9e9981e3768d64695e5855bac1a6e319374ed1a50e9d2`，共 3,244 筆，低於 probe 的
200,000 筆保留上限。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | #4,103,486 `OPENBORD.PIK` 以 DOS `AH=3Fh` 將 10,245 位元組讀至 `5755:0000`，即 `[57550h,59D55h)`；其後到 #4,157,000，`-watch` 沒有記錄該範圍內容改變的寫入。 | payload 內容沒有被觀測為改變。watch 不記錄值相同寫入，故不將此表述成「完全沒有寫入」。 |
| confirmed | `-read-watch` 於 #4,104,159–#4,156,836 記錄 673 次 `0AC2:04F5` 讀取，範圍 `[57556h,58129h)`、673 個不同 cell；raw `A4`／`MOVSB` 在前一位址 `0AC2:04F4`。 | `MOVSB` 實際從未被觀測為改變的 `OPENBORD.PIK` payload 範圍取樣。 |
| confirmed | 目標 027 同一窗口有 672 次 `0AC2:04F5` 的不同畫布內容變更，且 `MOVSB` 的取樣目的段為 `ES=1C43`。 | 至少 672 次 `OPENBORD.PIK` 原始緩衝區→畫布內容變更的資料流已閉合；第 673 次讀取目的端未改變，故不在畫布變更計數內。 |
| unknown | 完整 320×24 畫布窗口的資產歸屬、較後 canvas→VRAM copy 前的存續、最終像素矩形、圖像語意、文字存在與中文安全矩形。 | 取樣資料流不授權 DRAFT／READY 規格、覆蓋原型或中文化實作。 |

本輪只使用 dosgolem 的記憶體讀寫觀測；沒有匯出／提交原版內容、修改 dosgolem、修改原版或改變遊戲流程。

## 2026-09-21：目標 029 的 `OPENBORD.PIK` 取樣畫布至一次 VRAM copy 存續

固定輸入、dosgolem commit `1435f175e785ea096a9268cd1021a4222300bd43` 與 post-window state
`goal027-post-opening-pik-writes-4156900.state`（SHA-256
`472bc110c556131b90989cad18280fd633be6f5e8d311eb17518d6d94f864089`）沿用先前目標。由第 4,156,900 指令
重播至第 5,500,000 指令，原版目錄維持 `/game:ro`。生命周期 report SHA-256 為
`afac0060be50bd828419e1811bd9d6a13f2a6feecdb60dd7cf5f613a2a27cf78`；畫布內容變更 TSV 為零 bytes
（SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）；粒度 1 讀取 TSV SHA-256 為
`73e1dfdc83560d4e758098232b7e60bd5aaea9394c754f9d46455fe22dac31c6`，共 7,680 筆，低於 probe 的 200,000 筆
保留上限。所有 report 都只在 gitignore 的 `workplace/reports/`。

`-watch` 與 `-read-watch` 的範圍均為執行期線性 `1C430h–1E22Fh`。讀取事件完全在
#5,464,375–#5,464,536，分成 24 組、每組 320 bytes，從第一組 `1C430h–1C56Fh` 到最後一組
`1E0F0h–1E22Fh`，均報告執行後 IP `0557:00A1`。執行期 `0557:0090` 的 raw bytes 顯示
`0557:009F = F3 A5`／`REP MOVSW`；其前置樣本為 `DS=1C43`、`ES=A000`、`CX=00A0`，`SI`／`DI` 每列
遞增 `0140h`。`-watch` 僅回報內容改變，零筆不表示沒有值相同寫入。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 第 4,156,900–5,500,000 指令對 `1C430h–1E22Fh` 的內容變更監看保留零筆，沒有截斷。 | 在此窗口未觀測到該 320×24 canvas 範圍的內容改變；值相同寫入未被排除。 |
| confirmed | 7,680 筆讀取完整覆蓋該範圍，均在 #5,464,375–#5,464,536 的 `0557:00A1`；前一 `0557:009F` 是 `F3 A5`，且 24 個 pre-instruction 樣本是 `DS=1C43`、`ES=A000`、`CX=00A0`。 | 這個完整 canvas 範圍在一次逐列 `REP MOVSW` 中搬往 mode 13h A000 VRAM。 |
| confirmed | 目標 028 的 672 次 `OPENBORD.PIK` 原始緩衝區→canvas 內容變更都在此 7,680-byte 範圍內；本輪未觀測內容改變且讀取完整覆蓋。 | 已確認的 672 次資料流延續至這一次 A000 VRAM copy。 |
| unknown | copy 後 VRAM 的存續、`OPENBORD.PIK` 的完整資產歸屬、圖像或文字語意、中文安全矩形。 | 不建立 DRAFT／READY 規格、覆蓋原型或中文化實作。 |

本輪沒有匯出原版畫面／像素、修改 dosgolem 或原版，亦未用 asset 名稱或畫布範圍推測文字存在。

## 2026-09-21：目標 030 的 `OPENBORD.PIK` 可視矩形與文字存在檢查

固定輸入、dosgolem commit 與目標 029 的第 4,156,900 指令 state 沿用。probe 的 `-shots` callback 只會在
下一次 loop 取得執行機會，故以 `-steps 5464537` 觸發 `#5,464,536` 的 snapshot；那是第 24 次
`REP MOVSW`／`0557:00A1` 完成後、下一道指令前的畫面。report SHA-256 為
`ce9a23c492dc9b75d98b2e795bd1f8240280ff9d23a960a2fa3484414d1652a7`；320×200 indexed frame（64,000 bytes）為
`a3b946092e5bf8322128d904302d8e3910f724e07fd298cb25a4d3872fd5b609`；768-byte palette 為
`000ee1dfbfba6afc159d4e39dca09e5202e68bebc931cd4d50bfb3f998e1f1e3`；全畫面 PNG 為
`7ea9d10aac638e89c23a4a344cf550e31b68cc39b830fc3b3303dbc62831e749`。

以 `tools/render_indexed.go`（純 Go 標準函式庫）將 dosgolem 的 indexed frame 及 palette 轉為 PNG；該工具已以
上述輸入成功建置與執行，不含遊戲專屬位址或原版資料。從 indexed frame 的 offset 0 取 7,680 bytes，也就是
目標 029 已確認的 A000 首 320×24 bytes，得到 crop indexed SHA-256
`fc4bce77b6d8fab5c43f89eba754b904e623f180932a623da994a472f87871a3` 與 crop PNG SHA-256
`97afec1b7b951423ba59b3db679708469cb122de9294e550111b2880c150c7e4`。所有原版衍生檔案僅留在
`workplace/reports/`，沒有加入 Git 或對外端點。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 目標 029 的 `1C430h–1E22Fh` 逐列 copy 對應到 A000 的 offset `0000h–1DFFh`；該 7,680 bytes crop 與同時 palette 由固定 step frame 重生。 | 可視檢查的矩形是 mode 13h 螢幕 `(0,0)–(319,23)`，其定位來自資料流而非視覺猜測。 |
| confirmed | 放大 crop 是單一連續、重複的金色幾何邊框，沒有字元輪廓、字距、文字群組、可辨識字形或可讀文字。 | 此 `OPENBORD.PIK` 資料流範圍是非文字靜態裝飾，不是中文覆蓋候選。 |
| unknown | `OPENBORD.PIK` 的其餘內容、copy 後 VRAM 存續、其他 `.PIK`／`.SS` 資產的圖像或文字語意、中文安全矩形。 | 不建立 DRAFT／READY、覆蓋原型、譯文或中文字型。 |

本輪直接檢視的是可重播的本機收據，沒有 OCR、人工轉錄、資產解碼或原版修改；「非文字」只適用上述精確矩形。

## 2026-09-21：目標 031 的完整 composite frame 與可見靜態文字候選

固定輸入、dosgolem commit 與第 4,156,900 指令 state 沿用目標 029。對執行期線性
`1C430h–2BE2Fh`（`DS=1C43` 的 `0000h–F9FFh`）啟用粒度 1 `-read-watch` 至 #5,467,000；完整 TSV 有
172,140 筆（SHA-256 `086248d62c61dfc8b1e94db9a41a840e1a62581af7c388b11262c46c8383ea38`），其中含 copy 前處理
與 copy 後局部重畫。只篩選 `#5,464,375–#5,465,772`、post-IP `0557:00A1`，得到 200 組、每組 320 bytes、
共 64,000 bytes，連續 `1C430h–2BE2Fh`；第一與最後事件分別是
`5464375 1c430 0 0557:00a1`、`5465772 2be2f 63999 0557:00a1`。`0557:0090` raw bytes 中的
`0557:009F` 是 `F3 A5`／`REP MOVSW`；200 個 pre-instruction 暫存器樣本的目的 `DI` 為
`0000h–F8C0h`、每列 `0140h`，目的段均為 `A000`。因此這個篩選區間是 confirmed 的第一個完整 320×200
composite canvas→A000 copy，而不是把 172,140 筆全部誤當成同一 copy。

以 callback 時序校正的 `-steps 5465773` 保存 #5,465,772 state，report SHA-256 為
`c8ecaeb7d71794a02cdc53db603f18158dcb94a2b71281c8cb4bc327e9a7fcca`；indexed frame SHA-256 為
`304ffd302045969ddad4a6c5e3c139a1af5f9f1bdbc1a060600b981ef26faeaf`；palette 為
`000ee1dfbfba6afc159d4e39dca09e5202e68bebc931cd4d50bfb3f998e1f1e3`；全畫面 PNG 為
`eefb4d5c46e06657106202ff83727da5079e27e8897587ed399dd2aff1d62247`。兩個本機列帶／放大 PNG 的雜湊為
`2461cc41dc35b1f7fcb0185278b2f7082aba5c2b257c62ba7c41239c740dc022`（地圖標籤列帶）、
`ee8e3be3c75753c4aac2346b218a96eee9d3201de53249d18727a89a16d7e245`（卷軸列帶）與
`7ae06c737f6dceddf7ff0e582be8f766c1edd48adef3734252fa8128fa578621`（卷軸精確裁切放大）。
`tools/render_indexed.go` 已擴充為可重現的最近鄰 `-scale` 與來源畫布裁切
`-source-width`／`-source-height`／`-x`／`-y`；工具本身不含遊戲資料或位址。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 上述 200×320 `REP MOVSW` 讀取、`A000` 目的段與 fixed-step indexed frame。 | `(0,0)–(319,199)` 是此次完整 composite copy 的可視檢查範圍。其後 132 列局部 copy 存在，故本輪不稱此為穩定最終畫面。 |
| confirmed | 本機 frame 的約 `(53,49)–(174,61)` 有清楚、連續的字形，直接可讀為 `OCEANVS OCCIDENTALIS`。 | `opening-map-ocean-label` 是可見靜態文字候選。來源資產、資料流、copy 後存續與中文安全矩形未知。 |
| confirmed | 本機 frame 的約 `(148,123)–(208,146)` 有兩行字形；精確 crop 放大仍不能可靠辨識全部原文。 | `opening-scroll-two-line-text` 是可見靜態文字候選；原文、來源資產、資料流、copy 後存續與中文安全矩形未知。 |
| unknown | 視覺候選與每個 `.PIK`／`.SS` 的載入／繪製資料流尚未閉合。 | 畫面文字不能據此歸屬於特定檔案，也不能建立 DRAFT／READY、覆蓋原型或譯文。 |

所有 frame、palette、crop 與 PNG 僅存在 gitignore 的 `workplace/reports/`；沒有公開、提交或附到 Issue。文字候選
僅供私有研究清冊使用，不是資產解碼或原文文本輸出。

## 2026-09-21：目標 032 的 `OCEANVS OCCIDENTALIS` 畫布（canvas）寫入與部分來源鏈

固定輸入是 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`），輸入 manifest SHA-256 為
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`，dosgolem 隔離副本 commit 是
`1435f175e785ea096a9268cd1021a4222300bd43`。所有 probe 在 `colonization-research:20260920-r2` 的無網路一次性
容器中執行，原版目錄唯讀掛載為 `/game`；產物只留在 gitignore 的 `workplace/reports/`。

從第 4,156,900 指令 state（SHA-256
`472bc110c556131b90989cad18280fd633be6f5e8d311eb17518d6d94f864089`）重播，先以外包範圍
`[201A5h,2111Eh)` 監看，再按每列 320-byte stride 篩回可見標籤 `x∈[53,174)`、`y∈[49,61)`。完整 stdout 收據
`goal032-ocean-label-writer-lifecycle-4156900-5465773.txt` 的 SHA-256 是
`37af08325a7d554b14efadf799ac1b7d4fb6529d0e15b137548726123d318bfd`；writer 前置暫存器與 raw bytes 收據
`goal032-ocean-label-writer-pre-regs-5432000-5448000.txt` 的 SHA-256 是
`f7eba746b946a9f0dff68e9e2698e74e8e569272391051ad00959745b8f92a5f`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 真正標籤矩形有 2,345 筆內容變更，位於 #5,432,823–#5,447,038，post-IP 全為 `03BD:00CA`；raw `03BD:00C8` 是 `F3 A5`／`REP MOVSW`。第一個完整標籤列的前置暫存器是 `DS:SI=388B:5DF5`、`ES:DI=1E23:1F40`、`CX=00A0`。 | 此 `REP MOVSW` 是標籤進入畫布的真實 writer，而非可見文字或檔名推測。該列的來源標籤切片是 `[3E6A5h,3E71Eh)`，目的畫布切片是 `[201A5h,2021Eh)`。 |
| confirmed | 從第 3,000,000 指令 pre-input state（SHA-256 `0239ae38feff005105ab769a322e5a6c87622d531f9283b84575031c63e3b7e3`）以 BIOS Enter 重播，`[3E6A5h,3E71Eh)` 在 #3,225,029–#3,225,927 有 120 筆內容變更：`0AC2:04F5` 15 筆、`0AC2:0551` 105 筆。其完整 watch TSV SHA-256 是 `8ce01ce4864f68cf46779724b4fb1eb4d769c287941f07959dfa4c654cbc3da9`，lifecycle 收據 SHA-256 是 `c174af03f6ce66171e896b4948c2d1f783d67cc198af7f83971d1ce552ab34f5`。 | 這是標籤畫布來源暫存切片的已觀測內容生成窗口；到第一次標籤畫布寫入前未再觀測內容變更。監看不能排除值相同寫入。 |
| confirmed | `OPENING.PIK` 的主要 payload 在 #3,004,029／#3,004,090 讀至 `[57550h,70028h)`。在來源生成窗口，15 筆 `0AC2:04F5` 暫存寫入可與同一步數的原始緩衝讀取精確配對：第一筆 #3,225,029 `5C457h → 3E6A5h`，最後一筆 #3,225,927 `5C497h → 3E71Dh`。raw read TSV SHA-256 是 `fb100fb0acf91644fcb8ca66be567c86eb0e7133b7aa4ed7a2d98a457032eb55`，lifecycle SHA-256 是 `5b7a916dd91b0f7dce2d51f4596cf8c8c31bef5ab3c8ec151aed5e6be80c9331`。 | `OPENING.PIK` 是這 15 個標籤暫存 bytes 的 confirmed 直接來源。 |
| 強推論 | 同一 `DS=5755` 解碼迴圈以 `0AC2:04F5` 的 `MOVSB` 與 `0AC2:0551` 的 `STOSB` 共同生成上述 120 筆變更；後者 105 筆尚未建立每像素的原始讀取配對。 | 整個標籤為 `OPENING.PIK` 解碼產物是強推論，不升格為完整逐像素資料流或唯一資產歸屬。 |
| 未知 | 第一次完整 composite copy 之後的穩定畫面、中文文字的實際安全矩形、完整資產歸屬與其反向辨識條件。 | 不建立 DRAFT／READY、覆蓋原型、譯文或中文字型。 |

這條較早的 `OPENING.PIK`→暫存→畫布路徑不推翻目標 027 的勘誤：被 `OPENBORD.PIK` 覆寫的是較晚的
共享 `5755` 緩衝區取樣；本輪確認的暫存切片已在覆寫前生成且未觀測內容改變至 label writer 使用。
所有記憶體位址均為 dosgolem 執行期線性位址，`CS:IP`、`DS:SI`、`ES:DI` 則為 16-bit real-mode segment:offset。

## 2026-09-21：目標 033 的海洋標籤 copy 後存續

固定輸入、`OPENING.EXE` SHA-256、輸入 manifest、dosgolem commit 與第 4,156,900 指令的正常 BIOS Enter state
均沿用目標 032。以 `-steps 5465774 -save-state 5465773:...` 校正 probe callback 邊界，取得第 #5,465,772
指令後的完整 copy state；state SHA-256 是
`c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba`，建立收據 SHA-256 是
`6b82eb73ce8b4ac34386fe394b2d0ceabc14de08ed904777ed0fd7b04a92c47b`。兩個從此 state 重載的無網路 Docker
probe 都執行 34,228 道指令至 #5,500,000，保持 mode 13h、無未實作服務與無新檔案開啟。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 從 #5,465,772 至 #5,500,000 的畫布外包監看，以每列 320-byte stride 篩回 `x∈[53,174)`、`y∈[49,61)`，其精確列範圍是 `201A5h–20FDDh`。watch TSV 為零位元組（SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）；lifecycle 收據 SHA-256 是 `59161947ac65beb2afebe0c73653206c6faf9c11e56525a044d7f8ded3019865`。 | 該標籤畫布範圍在此窗口沒有內容變更。watch 不能排除值相同寫入。 |
| confirmed | 相同窗口獨立監看 A000 對應精確列範圍 `A3D75h–A4BADh`，watch TSV 同為零位元組（SHA-256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`）；lifecycle 收據 SHA-256 是 `f97253d746a15571fb97238a3288fa97daf4a6d72b889d91713b88a0507611ef`。 | 該標籤 A000 顯示範圍在此窗口沒有內容變更；畫布與 VRAM 的結論獨立取得。 |
| confirmed | 起點的 `goal033-ocean-label-canvas-5465772.idx/.pal` 與終點的 `goal033-ocean-label-postcopy-5500000.idx/.pal` 以 `cmp` 逐位元組相同；色號陣列 SHA-256 為 `304ffd302045969ddad4a6c5e3c139a1af5f9f1bdbc1a060600b981ef26faeaf`，調色盤 SHA-256 為 `000ee1dfbfba6afc159d4e39dca09e5202e68bebc931cd4d50bfb3f998e1f1e3`。 | 不只標籤範圍，這兩個固定時點的完整 320×200 色號畫面與 palette 亦相同。 |
| confirmed | 既有通用 `tools/render_indexed.go` 從上述兩份 indexed frame 各重生 `x=53,y=49,121×12` 的 8 倍最近鄰裁切；兩個 PNG SHA-256 同為 `816fb640eef2583dfc3471cf92db4ed15fb80c0ee795f67917d3de6c04bf4875`。 | 標籤精確裁切在兩個固定時點的視覺色號／palette 結果相同；PNG 只保留在 gitignore 的 `workplace/reports/`。 |
| unknown | #5,500,000 之外的後續畫面、每一次值相同寫入、完整 `OPENING.PIK` 像素依賴、可清除的背景遮罩、中文安全矩形與反向辨識條件。 | 此收據不授權 DRAFT／READY、覆蓋原型、譯文或中文字型。 |

第一次從 #4,156,900 state 起跑的長窗 canvas watch 因 probe 的 200 筆容量而截斷，故沒有被用於 copy 後零變更
結論；本輪改用完整 copy 後 state 的短窗口，兩個零位元組 watch TSV 才是上述結論的唯一監看依據。
所有位址均為 dosgolem 執行期線性位址；frame、palette、state、TSV 與 PNG 均未加入 Git 或 Issue。

## 2026-09-21：目標 034 的完整開場畫面後單次 Enter 探測

固定輸入、`OPENING.EXE` SHA-256、輸入 manifest、dosgolem commit 與目標 033 的第 #5,465,772 state
`goal033-post-full-copy-5465772.state`（SHA-256
`c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba`）沿用不變。兩組均以無網路、一次性
Docker 容器、唯讀 `/game` 掛載從同一 state 展開；預定上限同為 #7,000,000，只有實驗組以 BIOS 緩衝區在
#5,465,773 排入一個 Enter。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 控制組執行至 #7,000,000（1,534,228 道指令）仍在 mode 13h、`0557:00B4`；沒有鍵取走、檔案開啟、主控台、B8000、全形／半形字型 hook 或未實作服務。report SHA-256 為 `65b32d5ffbdfbd642657b42f9f2864c542e7f075880faf0c2cf83618ddb12a94`，終點 indexed frame SHA-256 為 `ff3b73f1e327e09549e6f347d59f1f227e139b63db20c317d8f5138423f20279`。 | 無輸入時，這個開場程序在觀測窗口持續圖形路徑。 |
| confirmed | 實驗組的 Enter 在 #5,465,827 由 `int16-AH00-bda` 取走；#5,511,173 切到 mode 03h，#5,511,796 終止，離開碼為 `0x6C`。report SHA-256 為 `381da331bb379770fe9e037c6fcfff52b4f11d81cd14b03f0b737105c7309d0b`。 | 這個固定畫面上的單一 Enter 觸發 `OPENING.EXE` 的退出，而非到達共同的 #7,000,000 終點。 |
| confirmed | 有界 trace 在 `0562:0396` 前記錄 `AX=4C6C`；raw `0562:0394–0397` 是 `B4 4C CD 21`。trace SHA-256 為 `bc022c9f814f3c9af993194c3ebf4366823f0fade95f4a3e1beda2cdf399f498`，raw-byte 收據 SHA-256 為 `f703e999cfc07e2841dc42d38441cf6229218c5979303b074c46660d76762708`。 | `0562:0396` 是 confirmed 的 DOS `int 21h AH=4Ch` 終止指令，回傳 `AL=6Ch`。 |
| confirmed | Enter 組沒有新檔案開啟、主控台輸出、B8000 或全形／半形字型 hook；唯一未實作服務是終止前 #5,511,000 的 `int 21h AH=2Dh` 一次。其 `-dump-vram` 在 mode 03h 後仍含 A000 色號陣列。 | 這個 A000 傾印是終止後殘留，不能當成 Enter 後的新可見畫面或文字輸出證據；`AH=2Dh` 的語意與其是否影響路徑維持 unknown。 |
| unknown | 哪個 DOS 父程序／啟動器消費 `0x6C`、其後續正式執行檔、其他正常遊戲入口，以及任何動態印字呼叫點、文字來源與幾何。 | 不建立動態文字 DRAFT／READY、譯文、字型或覆蓋程式。 |

本輪只比較同一快照的正常無輸入與單一 BIOS Enter，沒有盲注、掃描點擊、記憶體改寫或原版修改。固定 state、
report、trace 與畫面傾印均只保留在 gitignore 的 `workplace/reports/`。

## 2026-09-21：目標 035 的批次啟動鏈與 `0x6C` 消費者邊界

固定 DOS 輸入 manifest SHA-256 是
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`；所有檔案盤點與 probe 在
`colonization-research:20260920-r2` 的無網路一次性 Docker 容器中進行，原版目錄唯讀掛載為 `/game`。
dosgolem 是 `workplace/dosgolem` 的 commit `1435f175e785ea096a9268cd1021a4222300bd43`，未修改。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 根層的 DOS batch 檔只有 `COLONIZE.BAT`（50 bytes，SHA-256 `4ea071484153da2716f77446fc6c7545645493fd369daf62fba8f395fa0bd9db`）與 `COLDEMO.BAT`（52 bytes，SHA-256 `ccc44d5c31aef794eea0b27f240970e31839923c10e487c4b1923f80ce7da97d`）。兩者都是 CRLF ASCII batch 檔；未保存原文的行數／命令詞盤點各得兩個非空行，第一行為回音控制，最後一行命令詞是 `opening`。 | 兩個候選皆以最後一行直接啟動開場；它們沒有其後的 batch source-level 離開碼消費／分派行。 |
| 強推論 | `COLONIZE.BAT` 的檔名與其直接啟動開場的內容形狀。 | 它是一般 DOS 啟動入口候選；沒有從原版說明文字或 shell 執行收據證實「一般」身分。 |
| confirmed | dosgolem `cmd/probe -h` 的 `-exe` 說明只接受 MZ 或 COM。以 `/game/COLONIZE.BAT`、`-root /game`、`-steps 1` 重現時，報告從 `CS:IP=0100:0100` 執行到 `0100:0101`，`AX=0001`，沒有 EXEC、檔案、主控台或未實作服務；report SHA-256 `373d74d8458f002241b69b62d47133210368efb722638b3f51520d9bd26921b6`。 | `cmd/probe` 未執行 batch 直譯，而是以 COM 式入口執行批次位元組。batch／`COMMAND.COM` 正式重播是本輪精確的工具缺口。 |
| unknown | 既有目標 034 的 `OPENING.EXE` `AH=4Ch, AL=6Ch` 收據，及本輪兩個批次檔的靜態結構。 | 沒有已證實的父程序消費者、DOS shell 回傳碼語意、其他 `OPENING.EXE` 互動分支或動態文字輸出。 |

批次檔原文、遊戲 EXE／資料及 probe report 均未加入 Git、GitHub Issue 或公開輸出；report 僅在 gitignore 的
`workplace/reports/`。本輪不建立 DRAFT／READY、譯文、字型或覆蓋程式。

## 2026-09-21：目標 036 的完整開場畫面中央左鍵

固定輸入、`OPENING.EXE` SHA-256、DOS manifest、dosgolem commit 與第 #5,465,772 state
`goal033-post-full-copy-5465772.state`（SHA-256
`c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba`）均沿用目標 034。兩組都以無網路、
一次性 Docker 容器從唯讀 `/game` 與同一 state 展開；實驗組唯一輸入是在 #5,465,773 排入的左鍵 `(160,100)`，
並以首個滑鼠輪詢後放開。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 無輸入控制組從 #5,465,772 續跑 1,534,227 道指令至 #7,000,000，仍為 `0557:00B3` mode 13h；有 1,255 次滑鼠輪詢，沒有新檔案、主控台、B8000、字型 hook 或未實作服務。lifecycle SHA-256 `d0a8cd67143ac3be9aed7cf305657a77250d88333a9d1fb78a27b1fb008d1934`，trace SHA-256 `43f6de26513635fcca14edf8f69b037cae03b39699171cf44d501a44749b3e25`。 | 控制組在固定終點持續開場圖形路徑；它不單獨證明左鍵路徑。 |
| confirmed | 實驗組的 `int 33h AX=0003` 在 #5,465,840 回報 `CX=160, DX=100, 鍵=01`；按下只在這一次輪詢出現。#5,509,215 切為 mode 03h，#5,509,826 由 `0562:0396` 的 `AH=4Ch, AL=6Ch` 終止。lifecycle SHA-256 `67fe069da80f493a64297e6d088268db676ec4a666d668fcd2455c8190ba5e18`，trace SHA-256 `10f817804f348258c03ac239776841424e5c1ff3093c788f8e866b3514743dd6`。 | 這一個既有中央左鍵被程式讀取後走向 `OPENING.EXE` 退出；與目標 034 的 Enter 退出結果分開記錄。 |
| confirmed | 實驗組沒有開新檔、主控台、B8000 或全形／半形字型 hook；終止前 #5,508,989–#5,509,826 的關閉序列有一次未實作 `int 21h AH=2Dh`，並釋放 EMS handle。mode 03h 後的 A000 indexed frame SHA-256 為 `304ffd302045969ddad4a6c5e3c139a1af5f9f1bdbc1a060600b981ef26faeaf`。 | 終止後 A000 是殘留，不能當作左鍵後新畫面，亦不能和較晚的控制組 mode 13h endpoint 比較。 |
| unknown | 中央點的畫面／按鈕語意、其他可點區、其 hit-test 資料／常式及任何動態印字、文字來源與安全矩形。 | 此結果不建立 DRAFT／READY、譯文、字型或覆蓋程式。 |

所有 lifecycle、trace、frame 與 palette 僅保存在 gitignore 的 `workplace/reports/`，沒有提交、附加或公開任何原版素材。

## 2026-09-21：目標 037 的滑鼠輪詢第一個控制流分歧

固定輸入、`OPENING.EXE` SHA-256、DOS manifest、dosgolem commit 與第 #5,465,772 state均沿用目標 036。
兩組各以無網路、一次性 Docker 容器從唯讀 `/game` 重播 427 道指令至 #5,466,200；唯一實驗輸入仍是
`(160,100)` 左鍵，沒有注入其他座標、按鍵或記憶體修改。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 兩組都在 #5,465,840 呼叫一次 `int 33h AX=0003`。控制組回傳後為 `BX=0000,CX=0000,DX=0000`；左鍵組為 `BX=0001,CX=0140h,DX=0064h`。短窗 trace SHA-256 分別為 `5d3a16c509fd4eaf02c520ec7f199f3c8638f2d7aa542a88c85106fbee904d46` 與 `c75aa5a0401da3ac6eda860bf2ec852ecc4740e674dd0720a5c5308bce316de6`。 | `CX=0140h` 是 mode 13h 的滑鼠回報倍率後值；它不是遊戲邏輯 X 或區域幾何。 |
| confirmed | 延長至 #5,466,200 的 control／left-click trace SHA-256 分別為 `f7ec4b0c7453569c9068572c7cce161cd5cb61df89f1392d12222a524bf264c9` 與 `a51b0ac380e1826039b11a3b58bc0bfdc8465dc48d4a6eeebb721fb3270146cd`。trace record #95 是第一個 `CS:IP` 分歧：control `0110:0960, AX=0000`，left-click `0110:0956, AX=0001`。 | 第一個已觀測的控制流條件只依 AX 是否為零分支。 |
| confirmed | dosgolem real-mode `0110:094F` 的 96-byte dump SHA-256 為 `0880c0b81d4745f3ec7c3f077e5a8248fe23669e6fed0210b77c31a1ebb6acf1`。raw `0110:0952 = 0B C0`、`0110:0954 = 74 0A`；左鍵路徑 `0110:0956` 的 `C7 46 F6 1B 00` 寫入 `001Bh` 至 `[BP-0Ah]`。 | AX boolean 被消費，左鍵非零路徑寫入一個常數；常數與框架欄位的語意未知。 |
| unknown | AX 如何從 `int 33h` 的 BX/CX/DX 形成、座標比較／矩形、按鈕語意、其他互動路徑與任何動態文字。 | 不建立互動區清冊、DRAFT／READY、譯文、字型或覆蓋程式。 |

技能 `use-ida-pro-9-4` 指定的工具專案 README 與 `ida-94-tools.md` 在預期位置不可讀，故現有 IDA 映像沒有被
當作已驗證環境；本節沒有使用 IDA 產物。所有 trace、raw dump 與 lifecycle 只留在 gitignore 的
`workplace/reports/`。

## 2026-09-21：目標 038 的 AX boolean producer call

固定 state 無輸入重播 427 道指令至 #5,466,200；`0110:0920` 的 48-byte raw dump SHA-256 為 `671e7ed3e7e30d221e5b36c20bbfa402ebed656d2a075288b12c54bf4baa1430`，lifecycle SHA-256 為 `baa22131f936042482f80cb4756f55c49d1a3466b63d1e3548fb9fe302e01c39`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | raw `0110:0942 = 8D 46 F8`、`0945 = 50`、`0946 = 8D 46 FA`、`0949 = 50`、`094A = 9A 88 05 24 09`；trace 進入 `0924:0588` 並在 `0110:094F` 返回。 | `[BP-8]`／`[BP-6]` 位址作為引數傳給 `0924:0588`，而該 call 是 boolean consumer 的直接 AX producer。 |
| unknown | call 內的 BX/CX/DX、兩個 pointer、座標矩形、互動與文字語意。 | 不建立互動區清冊、DRAFT／READY、譯文、字型或覆蓋程式。 |

raw dump、trace 與 lifecycle 只存在 gitignore 的 `workplace/reports/`。

## 2026-09-21：目標 039 的滑鼠 producer 資料流與觀測對齊限制

固定輸入、`OPENING.EXE` SHA-256、DOS manifest、dosgolem commit 與第 #5,465,772 state 均沿用目標 038。
零指令前的 `0924:0560:128` dump 與重播 428 道指令至 #5,466,200 後的 dump 均為 SHA-256
`538c4844e4c927b347a8f7fd5df991d1344356c7c2428c9732dbae91687acca7`；前者 lifecycle SHA-256 是
`245668c2218fdf4b075f3d885e7a8f67ccabd16dddcb046e0cc1c5a29a30a67b`，後者為
`a7384664ca22dd71fffc579b8620465d04dfb440771b430cdd34403a0ae4ee6d`。所有輸入唯讀掛載，產物只在
gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | caller raw `0110:094A = 9A 88 05 24 09`；控制與左鍵 trace 都在該 call 後由 `0110:094F` 返回。控制組的 `int 33h AX=0003` 回傳 `BX=0000,CX=0000,DX=0000`，caller return 是 `AX=0000,CX=00A0h,DX=0064h`；左鍵組相應為 `BX=0001,CX=0140h,DX=0064h` 與 `AX=0001,CX=00A0h,DX=0064h`。既有延長 trace SHA-256 分別是 `f7ec4b0c7453569c9068572c7cce161cd5cb61df89f1392d12222a524bf264c9` 與 `a51b0ac380e1826039b11a3b58bc0bfdc8465dc48d4a6eeebb721fb3270146cd`。 | 此 call 的觀測行為將控制／左鍵狀態分別帶回 AX zero／nonzero consumer；不含座標或控制項語意。 |
| confirmed（限制） | `0924:0560:128` raw dump 的 SHA 在零指令前後相同，且 raw `0924:0584` 是 `C8 00 00 00`；trace 卻以 `0924:0588` 標籤記錄隨後 BP/SP 的 frame-transition，並將 `CD 33` 的 trace 標籤置於相對 raw 位置 +4 bytes。 | 此窗口沒有該 raw 範圍的自修改；raw dump 與 trace 的此處對齊差異可重現，但成因未知。不能用 raw bytes 直接宣稱 trace IP 的 opcode 或資料寫入。 |
| unknown | 此 call body 的 pointer 寫入、BX→AX 的確切步驟、CX/DX 座標處理、hit-test、按鈕、動態印字與文字來源。 | 在最小重現／工具規格釐清前，這些不得成為 DRAFT／READY 或覆蓋設計依據。 |

前輪目標 038 的 far-call／return 邊仍保留，但「`0924:0588` 是 raw body 的精確起點」不得視為已證實；它目前只可指
raw far pointer 目標與 trace label。這是一筆追加勘誤，不重寫前輪原始 dump 或 trace。

## 2026-09-21：目標 040 的 dosgolem 遠呼叫觀測對齊勘誤

目標 039 的 4-byte 對齊限制已被最小重現**推翻**。在相同固定 state、唯讀原版、零輸入與零指令的同一次
`cmd/probe` 中，`0924:0560:128` dump SHA-256 是
`538c4844e4c927b347a8f7fd5df991d1344356c7c2428c9732dbae91687acca7`；從其 byte `0x28` 取 32 bytes 的 SHA-256 是
`b2627ddfa5c50da777bea0a052f4afcec23cc5a632f8cef076b1cf2f52c8d7f1`，與獨立 `0924:0588:32` dump 完全相同。
`0560h + 28h = 0588h`，先前的問題是將 hexdump 行內位置誤讀為 `0x24`。零輸入至 #5,465,900 的 trace SHA-256 是
`743614e10222443ffc0d4ee56a58969164b1bb1603b9ea55d04aacd87f411b8f`；五組相鄰 pre／post dumps 均同雜湊，沒有自修改。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | caller `0110:094A` raw `9A 88 05 24 09` 指向 `0924:0588`；該 raw 是 `C8 00 00 00`，trace 的 `0588 → 058C` BP/SP transition 相符；`058C` raw／trace 均為 `33 DB`。 | far pointer、raw dump 和 trace 完全對齊；不存在這裡的 dosgolem 位址觀測缺口。 |
| confirmed | `doDumpMem` 以 `cpu.Addr(seg,off)` 讀取，`CPU.fetch8` 在無 A20／read watch 時從同一 `m.Mem` fast path 取指；`CALL far ptr16:16` 直接載入 immediate `seg:off`。 | 原始碼與重疊收據都不支持 state 載入、dump 或 fetch 的額外位移。 |
| confirmed | raw `05BA/05BD`、`05BF/05C2`、`05C4/05C5` 分別讀取 caller pointer、寫回 CX／DX、再以 `BX OR [DS:5AB4]` 形成 AX。 | 目標 039 的 pointer body 與 AX 公式可恢復為已證實的指令資料流；資料位址語意仍 unknown。 |

因此本輪不建立 DRAFT／READY、不修改 dosgolem，也不把此工具勘誤外推為遊戲、按鈕、座標或動態文字語意。

## 2026-09-21：目標 041 的滑鼠 producer 狀態閘門與 caller locals

固定輸入、`OPENING.EXE` SHA-256、DOS manifest、dosgolem commit 與第 #5,465,772 state 均沿用目標 040。
兩組均在 #5,465,825（`0110:094A` far call 執行前）及 #5,465,864（`0110:094F` return 後、consumer 前）
以同一次重播的 `-dump-mem-at` 取樣 `0C41:5AB4`、`5E6C`、`61B0`、`853A`；左鍵組唯一輸入仍是
#5,465,773 的 `(160,100)`，並在首個滑鼠輪詢後放開。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed（固定 state） | 兩組前／後的 `5AB4` dump 都是 bytes `00 00`（SHA-256 `96a296d224f285c67bee93c30f8a309157f0daa35dc5b87e410b78630a09cfc7`）；`5E6C` 都是 `FF FF`（`ca2fd00fa001190744c15c317643ab092e7048ce086a243e2be9437c898de1bb`）；`61B0/61B2` 都是 `A0 00 64 00`（`26c36e6f0efe64b53be41719cdf25339f4a77cfcd98de963a52bf27e3a06e695`）。 | 此 state 的 `AX = BX OR [DS:5AB4]` 中記憶體項為零，且 nonzero `5E6C` 選擇快取座標資料流。資料位址語意未知。 |
| confirmed（固定 state） | `SS:853A–853D` 兩組均由 pre bytes `66 03 10 01`（`e77f5b72f343c3827538106fc258c1849a2098b5c31f079da4a7c114f08e023e`）變為 post `64 00 A0 00`（`437893f4a9a4d6c391aedbbb0cbf2ac93c3c937cf3d155ab82fe83e1b514ef1b`）。 | raw body 所示的 CX／DX caller-local 寫回實際發生；兩個 final locals 是 `0064h,00A0h`。 |
| confirmed（固定 state） | 控制 trace 在 service 後、`05B0`、`05C5`、`0110:094F` 依序保持 BX/AX 0；左鍵組相應為 service 後 `BX=1,CX=0140h,DX=0064h`，並於 `05C5`／caller return 得 `AX=1`。trace SHA-256 依序為 `743614e10222443ffc0d4ee56a58969164b1bb1603b9ea55d04aacd87f411b8f`、`bf811495bffd0198fdf662d692c7413d3e46328dcdfec9703d1f4bfd59ef9a90`。 | 本 state 的 AX zero／one 由 service 後 BX zero／one 的差異貢獻；不外推其他 state。 |
| unknown | DS word 的遊戲語意、其他值、hit-test、按鈕、動態印字、原文來源、訊息鍵與中文覆蓋資格。 | 不建立 DRAFT／READY、譯文、字型或覆蓋程式。 |

所有 lifecycle、trace 與 dumps 僅在 gitignore 的 `workplace/reports/`，沒有提交、附加或公開原版素材。

## 2026-09-21：目標 042 的海洋標籤背景安全幾何

固定 state、輸入雜湊與 dosgolem commit 沿用目標 033。零指令 state dump 的 canvas `1C43:3840:6400` 與
A000 `A000:3840:6400` 分別是邏輯 y=`45..64` 的 320×20 色號 rows，兩份逐位元組相同，SHA-256 均為
`c13081ba2d6fbe514e6eae7b6b75eb27d1a0eddbca644ee759961f6d20746c51`；lifecycle SHA-256 為
`83b049a48e94967359e3b4d552db90fcb7cb53ccd4f44d5a8fda0bb45504a41e`。色號／連通性 report SHA-256 為
`c0a9a0e0ca8ad1e60626543bdcd981013d14438bcec7adf8ad80fd9fc5c151c6`，僅存在 gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 唯一候選幾何是 `(x=53,y=49,w=121,h=12)`；有限外框為 `x=[45,182)、y=[45,65)`。候選有 61 色、外框有 67 色、共享 48 色；候選主色 `136`／`173` 為 736／359 pixels。 | 可見外框不是均一背景，也不能作中文安全矩形。 |
| confirmed（安全否定） | 把 `{136}`、`{173}`、`{136,173}` 分別當背景時，4-連通的非背景 component 跨越候選與外框的數量為 10、1、19；兩色集合最大跨界 component 為 183 pixels。 | 這些最常見色號的遮罩不能安全隔離字形與相鄰地圖圖像；不允許平面填色、擴大不透明矩形或根據色號自行生成清除遮罩。 |
| unknown | pre-text 每像素背景、可逆清除策略、中文安全矩形、完整資產歸屬與排版。 | 必須另有可重播背景證據或另一候選，才能做可丟棄原型；目前不建立 DRAFT／READY。 |

原版 frame、色盤、pixels、PNG 或遮罩均未進 Git、Issue 或外部輸出。

## 2026-09-21：目標 043 的中央卷軸候選 canvas writer

固定輸入仍為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）。所有重播在 UID/GID 1000:1000、無網路、
一次性 Docker 容器完成；原版 `/game` 唯讀，收據只輸出至 gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | #4,156,900 state 至 #5,465,773 的 `A9A54h–A9A90h` VRAM watch 在 #5,465,240 留下 61 筆內容變更，皆是 `0557:00A1`。raw `0557:009F=F3 A5`、`00A1=A4`；該時收據為 `DS=2443, ES=A000, SI=1B00, DI=9B00`。VRAM watch SHA-256 `a197807033c4097a6f603ce9a5c49d08dd4017c62929444003440c02f44557d1`。 | 這是 `DS:SI → ES:DI` 的靜態 canvas→VRAM copy 末端。 |
| confirmed | #2,000,000 state 以 `lin:25E84` 至 #4,156,900 追蹤，候選像素在 #2,000,001→#3,000,000 變更 1,080 bytes、#3,000,000→#4,000,000 變更 316 bytes、#4,000,000→#4,156,900 為零。#2M→#4.1569M 的 CPU watch 有 200 筆，位於 #3,756,652–#3,759,074，均為 `04A2:017A`；sample `DS=3960,SI=10A8,ES=2343,BX=3E84`，raw `04A2:0150` 含 `AC … 26 88 07`。watch SHA-256 `02592072b8f376734e7720ef09ccd79b9aa1669c839c197605880af170c61172`。 | `04A2:017A` 是已見的解碼串流 canvas writer；watch 僅計 CPU content-changing writes，不是完整 decode 計數。 |
| confirmed | #5,465,772 的 `lin:25E84:7420` 與 `lin:A9A54:7420` dumps 逐位元組相同，SHA-256 都是 `e7bf4a7e6bbed1a5a086773573558061311967bcab747bb10fa739076b04b946`。 | 固定完整 composite state 的候選外包範圍可由 canvas 同狀態重生至 A000。 |
| unknown | 此輪起始 #2M state 不含候選建立前的可觀測檔案讀取；解碼串流無法與特定原版檔、原文或字元邊界閉合。 | 禁止將其命名為文字解碼器、歸屬 `OPENING.PIK`／`.SS`，或建立安全矩形、中文、DRAFT／READY 或覆蓋程式。 |

勘誤：早期 `-dump-mem-at` 的裸 `25E84` 按 IDA 基準轉成 `16F84h`，不是執行期 canvas 位址；所有採用的
快照改用 `lin:25E84`。這是量測格式更正，不是遊戲行為差異。

## 2026-09-21：目標 044 的中央卷軸候選輸入與 `MPSLOGO.SS` 來源鏈

固定輸入仍為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）與 DOS manifest
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。所有重播在 UID/GID 1000:1000、
無網路、一次性 Docker 容器完成，原版 `/game` 唯讀；原版衍生 reports 均留在 gitignore 的
`workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 固定 #2,000,000 state 的 `3A000h–3B000h` read watch 在 #3,757,195 記錄 `3A6A8h` 由 `04A2:01EB` 讀取（SHA-256 `38c9157a36c314186adfb39c3715a3ee8e4401e4168f3262c0c838396092788f`）。 | 這是目標 043 已見 `04A2` candidate canvas writer 實際消費的一段 input。 |
| confirmed | 冷啟動在 #1,062,435 從 `MPSLOGO.SS` file offset `863` 讀取 55,286 bytes 到 `4DC3:0000`（線性 `[4DC30h,5B426h)`）；#1,135,873 的 raw `0AC2:0550=AA`／`STOSB` 從 `DS=4DC3` 寫到 `ES:DI=3873:1F78`，即 `3A6A8h`。target watch SHA-256 `b13ab97c15fc55d77f5c5de7674a8cc67b523791d31d1e8ef16169a16b9f832f`。 | 一段 candidate input 由該檔案的 runtime buffer 解碼寫入。 |
| confirmed | 同一 decoder 讀取 `4F091h`（#1,135,789，`0AC2:0556`）及 `4F092h`（#1,135,892，`0AC2:04F5`），兩者都在 `MPSLOGO.SS` 載入範圍；read report SHA-256 `509155e13ef50ca543a5d4f6f336029c7b79e3a4f2b58449fcf5fc8abbb2f278`。 | 此處的資料來源是已實測的 raw buffer read，不是僅從暫存器或檔名猜測。 |
| 強推論 | `3A6A8h` 隨後由 `04A2` 消費並走入目標 043 的 canvas→A000 candidate chain；尚未為候選圖所有 input bytes 做一對一 raw-byte→pixel 映射。 | `MPSLOGO.SS` 是整個 `opening-scroll-two-line-text` 候選的來源資產，暫列強推論。 |
| unknown | 原始文字、字元邊界、完整解碼格式、完整候選圖邊界、背景、安全矩形與覆蓋資格。 | 不 OCR、不讀出原版內容、不建立譯文／字型／遮罩／DRAFT／READY／覆蓋程式，也不修改 dosgolem。 |

冷啟動 broad input-write report 的 SHA-256 是
`40049b9d08a6e54f15809f4bb15e134259099ca1795afaa40e34fec1737669a6`；上述 reports 僅記錄位址、值、步數與
指令定位，沒有保存或公開原版資產內容。

## 2026-09-21：目標 045 的中央卷軸候選 pre-text 背景安全否定

固定輸入仍為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）與 DOS manifest
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。由 writer 前 #3,756,000 state 重播，
第一筆 `04A2:017A` content-changing write 為 #3,756,004；在 #3,756,003 對 `lin:25E84:7420` 取 pre snapshot，
最後一筆在 #3,759,074，於 #3,759,075 取 post snapshot。前／後 snapshot SHA-256 分別為
`0b7e7cd03768152053903bc605a7eb6a4ab1cf25beb3815bac33a71c292cde67` 與
`6191b68d2acfd063256874dd21874928163d8a2b4a8318c121579d8383ffa41e`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 前後差分有 254 bytes，所有 pre 值都是 `00`；bbox 是 `x=[86,241)、y=[139,141)`。row 139 的 99 bytes 為 `x=[142,241)`，row 140 的 155 bytes 為 `x=[86,241)`，兩列重疊。delta report SHA-256 `4f0cc26a6009f31246d2623da90734043c6017b6e626fb352294b0887b2f31b3`。 | 這是單一連通的 zero-fill writer 區，不是獨立、已知可見背景。 |
| confirmed（安全否定） | 約略候選 `x=[148,208)、y=[123,146)` 內僅有 120 個變更、外有 134 個；writer register 從第一筆 `DS=3960,SI=10A8,ES=2343,BX=3E4E` 至最後一筆 `DS=3960,SI=10AC,ES=2343,BX=3FF0`。 | 零值前狀態與約略候選外框都不能成為清除遮罩或中文安全矩形。 |
| confirmed（工具限制） | lifecycle（SHA-256 `867325570bb195bf1446c513f1cd960a8cf9b393b2de9f70cc12d5cf3e588bae`）保留完整 254 筆、無前段遺失；`-watch-file` 只保存最後 200 筆（SHA-256 `02592072b8f376734e7720ef09ccd79b9aa1669c839c197605880af170c61172`）。 | 總數與首／尾定位以 lifecycle 為準；200-line file 不可被當作完整清冊。 |
| unknown | zero-fill 是否代表任何可見背景、原文、精確文字幾何、完整候選圖邊界、可逆背景、安全矩形與覆蓋資格。 | 不 OCR、不輸出原版圖、不建立譯文、字型、遮罩、DRAFT／READY、覆蓋程式，也不修改 dosgolem。 |

所有 state、snapshot 與 reports 只存在 gitignore 的 `workplace/reports/`；本輪沒有提交原版衍生內容。這是安全否定，
不表示整體靜態文字候選已窮盡。

## 2026-09-21：目標 046 的開場既有左鍵後續退出鏈

固定輸入是 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）、DOS manifest
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`、state
`goal033-post-full-copy-5465772.state`（SHA-256
`c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba`）與隔離 dosgolem commit
`1435f175e785ea096a9268cd1021a4222300bd43`。唯一實驗輸入是 #5,465,773 的 `(160,100)` 左鍵，首個輪詢後放開；
所有容器無網路、以 UID/GID 1000:1000 執行，原版 `/game` 唯讀。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | control／click IP timeline 的第一個差異為 record 96／#5,465,867：`0110:0960` 對 `0110:0956`。click raw `0110:094F:96` 的 SHA-256 是 `0880c0b81d4745f3ec7c3f077e5a8248fe23669e6fed0210b77c31a1ebb6acf1`，其中 `0956=C7 46 F6 1B 00`、`095B=C7 46 FC 01 00`、`0960=83 7E F6 00`、`0964=75 03`。 | local `001Bh` 寫入後確實進入 nonzero 分派；資料／控制項語意未知。 |
| confirmed | click timeline 在 #5,465,909 首次進入 `2C5D:0B18`，最後 lifecycle 在 #5,511,211 切 mode 03h，#5,511,836 以 `int 21h AH=4Ch, AL=6Ch` 終止。baseline lifecycle SHA-256 `33332e0f2cf41bc956d6a763a95d8f9370f15338849f1c308bf5bf0b7267baf0`；timeline lifecycle／trace SHA-256 是 `801711afe97d3d00b8c14091e0c49dd054408edf2ec25259031ba16e9407c437`／`3dcf2a4f9c63dc9f82308efc03bb1bc22fabdffa038c73934b0806b537728019`。 | 此固定 state 的單次左鍵最終離開 `OPENING.EXE`；不以段名或 exit code 推論遊戲語意。 |
| confirmed（無文字） | lifecycle 的主控台為 0 bytes、B8000 非零 bytes 為 0、全形／半形字型 hook 均為 0、沒有開檔事件。 | 此退出鏈不是動態文字輸出，沒有文本鍵或中文覆蓋資格。 |
| confirmed（勘誤） | 目標 036 的舊 lifecycle 以同名 state 記錄 #5,509,826 終止；現行無 observer baseline 於 #5,511,836 終止。舊收據未保存 state SHA-256 和 dosgolem commit。 | 舊精確步數不再是現行可重現收據；最終退出／無文字結論保留。 |
| unknown | `001Bh`、後續條件、`2C5D` 段、exit code、控制項、`VICEROY.EXE` 轉交與動態文字來源。 | 不以 batch、direct-entry、檔名或畫面外觀補猜。 |

所有 raw、timeline、trace 與 lifecycle 僅在 gitignore 的 `workplace/reports/`；沒有提交原版衍生內容。本輪不建立
譯文、字型、DRAFT／READY 或覆蓋程式，也不修改 dosgolem。

## 2026-09-21：目標 047 的海洋標籤 pre-text canvas 安全否定

固定輸入仍為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）與 DOS manifest
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。以隔離 dosgolem commit
`1435f175e785ea096a9268cd1021a4222300bd43` 從 #5,432,800 state
`goal047-ocean-label-prewriter-5432800.state`（SHA-256
`eb68cfc2630f1a17e6a75f6ebd14725d33ff375d5bcde1aff2297e1fcfbbb468`）重播至 #5,447,041。原版 `/game` 唯讀；
所有容器無網路、以 UID/GID 1000:1000 執行，收據僅在 gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 對 canvas 外包 `[201A5h,2111Eh)` 在 #5,432,822／#5,447,039 同次取 3,961-byte snapshot；SHA-256 是 `920b7d966cbebb51532944ac935683a783a13e2b689ccd40840a40ea7518da68`／`b7a87818cacd2da711dab6ef7db84ad01af450fade015140164075f0d0e8a59b`。差分 3,961 bytes，以 320-byte stride 篩回 `x=[53,174)、y=[49,61)` 後恰有 1,452 pixels，每列 121，bbox 完全相符；標籤外有 2,509 bytes。 | 這是實際幾何與外包區分開的同次寫入收據；不能把外包視為文字矩形。 |
| confirmed | 精確標籤矩形的 writer 前 1,452 bytes 均為零值，writer 後有 61 種非零色號。完整 lifecycle 的 6,724 筆 write 首於 #5,432,823 `201A5h`、末於 #5,447,038 `2106Fh`，全為 `03BD:00CA`；前一指令 `03BD:00C8` raw 是 `F3 A5`／`REP MOVSW`。 | zero-fill 是這個合成窗口的 pre-writer canvas 狀態，不是已證實的可見背景；writer 跨越標籤外未知圖像。 |
| confirmed（工具限制） | lifecycle、outer write TSV、分析 report SHA-256 分別為 `7f8a371b3b133988114cf866890c8f8f0977fa630a5b864339c3145dd0049cf3`、`555ce41d9ba1ffec5887e31ddfa962cd283f04900f5a2eb08e67f473c013ee49`、`d182761faece2a88f42bdac0bbf27a94f3072497ce3f7be8920477e868401602`。`-watch-file` 僅保留最後 200 筆，完整 6,724 筆計數與第一／末筆以 lifecycle 為準。register report 的 #5,432,823 post record 為 `DS:SI=388B:5F00`、`ES:DI=1E23:2080`、`CX=0000`；raw／register 皆只留本機。 | 不以 200-line TSV 推斷完整時序，且不公開原版衍生 raw／pixel。 |
| confirmed（安全否定） | 本輪沒有獨立、可回復且不跨未知圖像的 pre-text 背景；現有值是 zero-fill，且完整 writer 改寫標籤外 2,509 bytes。 | 拒絕用零值、單色、主色、外包或可見外框建立清除／遮罩／中文安全矩形。 |
| unknown | 英文字形前的可見背景、完整資產歸屬、可逆清除策略、中文安全矩形與靜態覆蓋資格。 | 不 OCR、不轉存原版圖、不建立譯文、字型、遮罩、DRAFT／READY、覆蓋程式，亦不修改 dosgolem。 |

## 2026-09-22：目標 048 的 `VICEROY.EXE` direct-entry 停滯診斷

固定輸入是 `VICEROY.EXE`（SHA-256
`a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`）與 DOS manifest
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。工具是隔離 dosgolem commit
`1435f175e785ea096a9268cd1021a4222300bd43`；所有實驗無網路、UID/GID 1000:1000、原版 `/game` 唯讀。這是
direct-entry 診斷，不是 `OPENING.EXE` 的已證實後續、正常玩家路徑或動態文字收據。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | #1,000,000 cold state SHA-256 `ab91f84efba8e9264d3643701526ce64da486e7cd9c8ecd2a37f5dfb59c98258`；#1,000,001 lifecycle SHA-256 `4eefdaba9a206e68be53c25a02b2a8bb469a36b2b1c4b9c488bd796cd8c5538f`。終點 `0020:402A`、IF=false、mode 03h，無未實作服務、檔案、A000／B8000、主控台、字型 hook 或 I/O。 | 可重生的是無輸入 direct-entry 停滯，不是可見遊戲／文字畫面。 |
| confirmed | #1,700–#3,001 IP timeline（SHA-256 `cf3f6d68297619a11a47bd4178a04f84343320c0b1810b5587a76bfda4f7f12f`）在 #2,216 為 `0020:00D3`，#2,217 為 `0020:4028`，#2,218 起停在 `0020:402A`。runtime raw `0020:00D3=FF D4`；該次 `SS:SP=26F5:4028`，下一筆 SP 為 `4026`。caller raw `4026h–4028h=83 C4 04`，隨後 `402Ah=7E FE`。`CALL SP` lifecycle／trace SHA-256 為 `3c4273beb6f4616ab1a25745127eebe262ae7cb681e8f936b4a75d75608eed04`／`89ee903750964f8341a0d591ea145b637c71439a995c2bb6cde80b778b13778e`。 | direct-entry 實際以 stack pointer 作 call target，落到 caller immediate byte，再進入自迴圈；這是直接觀測的控制流，不是推測性的 emulator fault。 |
| confirmed（診斷停止線） | 從 #1M state 重播至 #5,000,001，4,000,001 道指令後同為 `0020:402A`，沒有服務、檔案、畫面或 I/O 事件；VRAM SHA-256 `4f7988030a00d082fe445e00a2ac5dab502300ff1b80e8592dd569867b60ef74` 與 #1M 終點相同。lifecycle／trace SHA-256 `9ab0b3ed3e7b363f621022df24877114fc63917ed188261492d8aec25576db61`／`188cea8698593edfe5593ab2b7ce834210ba0c0328ffc681bb9a1d76d9c5bb30`。 | 不存在可由此 direct-entry 指定的未實作 CPU、DOS、BIOS 或 EMS 服務。 |
| unknown | 原始 launcher／parent 建立的正確 stack、call target、程序關係與文字路徑。 | 不建立 dosgolem DRAFT／READY 或實作；必須先取得正常 path 的 parent context 證據。 |

所有 state、raw、trace、timeline 與 indexed dump 僅在 gitignore 的 `workplace/reports/`，沒有附上 Git 或 Issue。本輪不 OCR、
不建立文本鍵、譯文、字型、覆蓋、原型或規格，也不修改 dosgolem。

## 2026-09-22：目標 049 的根層啟動引用候選清冊

固定 DOS manifest 是 `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。以隔離
`colonization-research:20260920-r2` 對唯讀 `/game` 的根層 `.BAT`、`.COM`、`.EXE` 做檔名、大小、SHA-256、
MZ／非 MZ 與精確大寫 ASCII `OPENING`／`VICEROY` metadata 盤點。輸出報告僅保留在 gitignore 的
`workplace/reports/goal049-root-launch-reference-inventory.json`，SHA-256 是
`c9a6327b505fffb2046a662365ec886658b72dd9b3245d983a6d8aebeebc36c0`；不含原版 bytes 或畫面。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 範圍有 9 檔：`CLOSING.EXE`（MZ，`2d0f0fa9cb8256fda6c967f2821379d37ca5552b6d621f74115b532aa147fedc`）、`COLDEMO.BAT`（非 MZ，`ccc44d5c31aef794eea0b27f240970e31839923c10e487c4b1923f80ce7da97d`）、`COLONIZE.BAT`（非 MZ，`4ea071484153da2716f77446fc6c7545645493fd369daf62fba8f395fa0bd9db`）、`INSTALL.EXE`（MZ，`bef03fdc07971402aa66e5bba9b42569d262cf6329be8905afcebc460c235a99`）、`MAPEDIT.EXE`（MZ，`b5b71b88b344be28c71d60325b35fc93221785b49099a9ce5f93195f6fefbab5`）、`MPSCOPY.EXE`（MZ，`ed359697da5bb6fc6983cab203eee5b1980df787aee30cf9c1224b901976b043`）、`OPENING.EXE`（MZ，`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）、`PKUNZJR.COM`（非 MZ，`44acfeeb1c68df328c2a4a39b0af453b06b0a1a8b7e8b2b1e19f81e9d253a11e`）、`VICEROY.EXE`（MZ，`a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`）。 | 這是雜湊綁定的窄範圍候選集合，不是完整啟動鏈清冊。 |
| confirmed | `OPENING.EXE` 有 5 筆 `OPENING` ASCII metadata（offset `49145,49153,49161,49178,49222`），全部無副檔名、無緊鄰路徑分隔；`VICEROY.EXE` 有 4 筆 `VICEROY` metadata（offset `104785,130260,130916,130931`），僅 `104785` 緊接 `.EXE`，全部無緊鄰路徑分隔。其他 7 檔均為零筆。 | 只有同名檔案內的靜態命中，沒有不同根層候選含 token；命中不說明語意。 |
| confirmed | 正常 `OPENING.EXE` 路徑已觀測到的唯一 DOS EXEC 仍是 `PSOUND.COL`；目標 035 的批次靜態結構與本輪 token metadata 都沒有 DOS shell 或 parent replay。 | 不將靜態字串、批次命令詞或 direct-entry 升格為 EXEC、exit-code 消費、stack setup、父程序情境或動態文字證據。 |
| unknown | 根層以外的候選、動態組字、環境／磁碟 launcher、實際 parent、`VICEROY.EXE` 正常轉交與文字路徑。 | 不執行候選、不建立 batch interpreter、不建立 DRAFT／READY，亦不修改 dosgolem。 |

所有容器無網路、以 UID/GID 1000:1000 執行；原版 `/game` 唯讀。這是 metadata 停止線，不能用「沒有不同根層命中」
宣稱不存在 launcher 或遊戲路徑。

## 2026-09-22：目標 050 的子目錄啟動引用候選清冊

固定 DOS manifest 是 `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。正式唯讀輸入根目錄是
`SMColoni/COLONIZE`。隔離 `colonization-research:20260920-r2` 對其中至少一層子目錄的 `.BAT`、`.COM`、`.EXE`
做相對路徑、大小、SHA-256、MZ／非 MZ 與精確大寫 ASCII `OPENING`／`VICEROY` metadata 盤點。報告只留在 gitignore
的 `workplace/reports/goal050-subdirectory-launch-reference-inventory.json`，SHA-256 是
`30f15c4490e6728f77783e38c5ff1c4c8d131df413ea899625ef274fc72d4836`；不含原版 bytes 或畫面。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | schema `colonization-goal050-subdirectory-launch-reference-inventory/1` 固定範圍為「排除根層」的 `.BAT`／`.COM`／`.EXE`；entries 為 0，兩個 token 的命中數均為 0。 | 此固定版本中沒有符合本輪副檔名與子目錄條件的靜態候選。 |
| confirmed（範圍修正） | 第一次探針將父目錄 `SMColoni` 掛為 `/game`，使 `COLONIZE/` 的 9 個根層檔重現目標 049 結果。它未作為證據寫入文件、Git 或 Issue，正確根目錄重跑後同名 report 已覆蓋該暫時輸出。 | 只採用正確 `SMColoni/COLONIZE` report；目標 049 根層與目標 050 子目錄範圍不重疊。 |
| confirmed | 正常 `OPENING.EXE` 路徑唯一已觀測 DOS EXEC 仍是 `PSOUND.COL`。 | zero-entry 與靜態清冊都不是 EXEC、父程序情境（parent context）、stack setup 或玩家路徑證據。 |
| unknown | 非 `.BAT`／`.COM`／`.EXE` 的資料、動態組字、環境／磁碟 launcher、實際 parent、`VICEROY.EXE` 正常轉交與文字路徑。 | 不以本輪 zero-entry 排除其他 launcher；不執行候選、不建立 batch interpreter、DRAFT／READY 或 dosgolem 修改。 |

所有容器無網路、以 UID/GID 1000:1000 執行，原版 `/game` 唯讀。這是窄範圍 metadata 停止線，不是動態文字或
中文覆蓋的實作證據。

## 2026-09-22：目標 051 的開場畫面座標格視覺清冊

固定 DOS manifest 是 `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。輸入使用既有完整
composite frame 的 indexed frame、palette 與 state；SHA-256 分別是
`304ffd302045969ddad4a6c5e3c139a1af5f9f1bdbc1a060600b981ef26faeaf`、
`000ee1dfbfba6afc159d4e39dca09e5202e68bebc931cd4d50bfb3f998e1f1e3`、
`c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba`。它綁定隔離 dosgolem commit
`1435f175e785ea096a9268cd1021a4222300bd43` 與 #5,465,772 state。

Python 3.11.2 標準函式庫 encoder 產生本機、gitignore 的
`workplace/reports/goal051-opening-frame-coordinate-grid-x2.png`（SHA-256
`24abdb08a2d7c72c22f80e19999fd1638cb345e447ee84f928e822571a412f7c`）與 metadata
`workplace/reports/goal051-opening-frame-coordinate-grid.json`（SHA-256
`aa81ec34a37cfda4c16f5f12e8f4cc83bbc85f90014c164e54a71e4997097a56`）。PNG signature 是
`89504e470d0a1a0a`，尺寸 672×432；輸入為 320×200 logical image 的 2 倍放大，格線每 16 logical pixels、
標示每 32 logical pixels。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | metadata schema `colonization-goal051-opening-frame-coordinate-grid/1` 記錄固定 manifest、dosgolem commit、state step、4 份輸入／輸出 SHA-256、尺寸、格線、tool 與限制；獨立檢查確認 PNG signature 和尺寸。 | 此本機圖片是可重現的既有畫面檢視材料。 |
| confirmed（視覺限制） | 只以 `view_image` 檢視本機 PNG；沒有 OCR、文字轉錄、語意命名、鍵盤／滑鼠輸入、`VICEROY.EXE` direct-entry、batch interpreter 或狀態轉移。 | 格線或畫面位置不是按鈕、玩家路徑、文字、文本鍵或翻譯／覆蓋資格。 |
| unknown | 所有未試操作位置的控制語意、輸入結果、正常轉交與動態文字輸出。 | 下一個輸入需要使用者先基於實際畫面選定正常操作意圖；不得用盲掃或 agent 猜測替代。 |

所有容器無網路、原版與既有 reports input 唯讀、以 UID/GID 1000:1000 執行；產圖器為一次性 `/tmp` 工具，未加入
儲存庫。這是一個可丟棄 prototype，不是 production path 或 READY 規格。

## 2026-09-22：目標 052 的已知退出輸入座標標記

固定 DOS manifest 是 `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。基底是目標 051
local grid PNG／metadata，SHA-256 為 `24abdb08a2d7c72c22f80e19999fd1638cb345e447ee84f928e822571a412f7c`／
`aa81ec34a37cfda4c16f5f12e8f4cc83bbc85f90014c164e54a71e4997097a56`，並回查相同 indexed frame、palette、state、
#5,465,772 state 與隔離 dosgolem commit `1435f175e785ea096a9268cd1021a4222300bd43`。

Python 3.11.2 標準函式庫 encoder 先從 indexed inputs 重建目標 051 grid，要求所得 SHA-256 完全等於基底 PNG，
再建立 gitignore 的 `workplace/reports/goal052-known-exit-marker-x2.png`（SHA-256
`862875cb3d253f11fc83689f11bcbf450ff190ce77ad57df9dd5c85b9ca73693`）與 metadata
`workplace/reports/goal052-known-exit-marker.json`（SHA-256
`76cdbca266cb2ab8c16acf9322a3c90b072f52066edaefb2be882afdfabea071`）。PNG signature 是
`89504e470d0a1a0a`，尺寸 672×432。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | metadata mapping `x=left_margin+logical_x×scale`、`y=logical_y×scale`，其中 `left_margin=32`、`scale=2`。logical `(160,100)` 得 output pixel `(352,200)`；紅色 3-pixel thick cross 的 half-length 是 14，白色角點在 ±15。`view_image` 檢視顯示 cross 落於該格線位置。 | 這是既有左鍵座標的幾何標記，未執行新輸入。 |
| confirmed（限制） | 目標 046 已獨立觀測固定 state 的 `(160,100)` 左鍵走非文字退出；本輪沒有鍵盤／滑鼠注入、OCR、控制項命名、direct-entry、batch interpreter 或狀態轉移。 | marker 只表示那一筆已知退出結果，不是按鈕、正常玩家路徑、文字、文本鍵或翻譯／覆蓋證據。 |
| unknown | 其他座標的操作意圖、控制語意、輸入結果、正常轉交與動態文字輸出。 | 需由使用者先依本機畫面選定下一個正常操作；不得盲掃或 agent 猜選座標。 |

所有容器無網路、原版與 reports input 唯讀、以 UID/GID 1000:1000 執行；產圖器是一次性 `/tmp` 工具，未加入
儲存庫。這是可丟棄 prototype，不是 production path 或 READY 規格。

## 2026-09-22：目標 053，正常啟動鏈與滑鼠操作解除阻塞

入口：[目標 053](docs/goals/053-mouse-and-gameplay-route-replan.md)、Issue #25。
本段訂正上輪的推論，不抹除其原始觀測。先前要求使用者猜座標的結論撤回；
同狀態測試及原版批次檔提供足夠證據由工具查清，不屬產品價值決策。

### 輸入、工具、位址空間

| 輸入 | SHA-256 |
|---|---|
| `OPENING.EXE` | `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` |
| `VICEROY.EXE` | `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3` |
| `COLONIZE.BAT` | `4ea071484153da2716f77446fc6c7545645493fd369daf62fba8f395fa0bd9db` |
| 舊 `goal033-post-full-copy-5465772.state` | `c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba` |
| BIOS 等待點 160-byte runtime dump | `b11e4e6a599ce3b38dc2c44bfeb30785d1d45ec07c2baad1a085b17988111cde` |

歷史滑鼠對照使用 dosgolem `1435f175e785ea096a9268cd1021a4222300bd43`；最終驗證使用
`22664265ea7d55ea8706448149908c79d3f0897b`。研究映像 `colonization-research:20260920-r2`，
Go 1.24；反組譯使用既有 `ida-pro-9.4-idapython:locked-v1`，IDA Pro 9.4。
IDA 匯入 raw dump 的資料庫零點對應執行期 `0562:0000`，並附加執行期位址；本文段:位移
皆為 dosgolem runtime 位址，不是檔案 offset，也未對原始函式做推測性改名。

### 舊無參數開場的同狀態因果對照

`tools/probe_opening_mouse.py` 已重跑。快照實際還原步數是 #5,465,773，雖然檔名寫
5465772；與控制組的首個 IP 分歧是記錄第 95 格、絕對步數 #5,465,868。
先前文件的 #5,465,867 是步數基底誤差，不是新的控制流分歧。

| 實驗 | confirmed 結果 |
|---|---|
| 無輸入、僅移至 `(16,16)` | #7M 仍在 mode 13h；IP 軌跡 SHA `fbaf2e21163bace06fbb2a0ae26563ca25c912b6e026ad76d382cb40464f2052`。 |
| `(160,100)`、`(16,16)`、`(300,180)` 單次左鍵 | 全部 #5,511,836 以 `0x6C` 結束；IP 軌跡 SHA 同為 `41ced31cc9fa3b8d750e4ef9f9525a25444816bbebb4c321ffb377c4392fd81b`。 |
| `0924:05AD`，剛從 int33 返回 | 三組 CX:DX 分別 `0140:0064`、`0020:0010`、`0258:00B4`，BX 均為 1。注入座標確實不同，不是輸入沒送到。 |

有限結論：固定舊開場狀態中，三個受測位置的按下結果沒有座標差異。
不能外推到遊戲主選單；後者已以實際位置點選第一列。
文字報告含執行耗時，整份 `.txt` 雜湊不是決定性驗收訊號；比較使用 IP、索引畫面與色盤。

### 啟動鏈與通用缺口

confirmed：原版 `COLONIZE.BAT` 為 `opening -g %1 ... %9`，既有研究直接啟動 OPENING 卻省略
`-g`。舊輪次關於 batch 不消費 `0x6C` 的有限觀測，不足以排除「batch 傳入參數」的作用。
補正參數後才是本輪正常入口，不需要先實作 shell 或直接啟動 VICEROY。

1. **BIOS 倒數**：在 runtime `0562:002E` 寫 `0000:0440=1`，`0032–0037` 等待其改變。
   舊執行器會鏈回 BIOS timer，但不遞減此值。依平台規格新增非零倒數與歸零清除 motor bits；
   #12,368,859 的 0→1 在 #12,836,218 由 BIOS 變成 0，隨後正常載入 VICEROY。
   原始收據 `goal053-fixed-g-30m.txt`，規格 [006](docs/spec/006-bios-motor-timeout.md)。
2. **滑鼠服務**：主選單呼叫的 `int33 AX=0014` 原先未實作，現依標準交換舊／新事件回呼。
   連續冷啟動後 `(128,110)` 點擊進入難度畫面，服務不再列入未實作；規格
   [007](docs/spec/007-mouse-handler-exchange.md)。
3. **快照**：DOS v3 漏存回呼、座標限制、按鍵位置及相對位移，令續跑失去操作。
   v4 保存行為狀態並拒絕 v3；機器層不完整保存 callback queue，因此明確拒絕有待執行／執行中
   回呼時的檔案快照，不悄悄遺失。規格 [008](docs/spec/008-mouse-snapshot.md)。

規格先經 DRAFT→READY 審查再實作；全套 `go test ./...` 已通過，原版重播後升為 CONFORMED。
累積源碼補丁由上游 `d9c0c27` 重建後，Git tree 完全等於
`2189d114214649c6f60074f70d853ff5bd04af0d`；不依賴只有本機才存在的未提交修正。

### 正式 dosgolem 收據與輔助對照

`tools/probe_gameplay_route.py`：冷啟動 #3M Enter、#12,000,001 開場左鍵，#30,000,001
主選單 `(128,110)` 左鍵，#40,000,001 擷取。連續與安全選單快照重播皆開啟 `DIFFICUL.PIK`，
實際檢視兩側畫面為難度選擇。兩者索引 SHA 同為
`e491233e037fa69b0498fc9415688b4491124d0ae687f45b17b46e8bf57b6446`，色盤 SHA 同為
`7c025d5be0f0851b285fe8d7fce2f4cfa44a28d0da3ca0d74eecfb3276c373c7`。
不點擊的控制組不開啟該資產，實際畫面留在主選單，索引 SHA
`915991ed8898747e7c635fee6596e64e9f6aee7928b021b4a35b945453e7241f`。
本次選單快照 SHA `20c1a81b368dad9b0b8dae7d7283927244883a899cc78d47eb476d40018cc353`；
完整命令與各次實際雜湊在本機 `goal053-route.json`。

輔助 DOSBox-X 使用既有 `wolong-dosboxx:latest`，image ID
`sha256:b75822ea1a4a9151abdee0992b854f5cd86524ccdbf9a71df624e7c91fcc3198`，
啟動入口 `tools/dosbox_probe.sh`／`.conf`。原版複製到容器 `/tmp` 後由 `colonize` 啟動，
Enter 到主選單，再以畫面上的第一列點擊到難度畫面。Xvfb 根座標 `(447,420)`，
遊戲 client 原點 `(192,200)`、2 倍縮放，約對應邏輯 `(127.5,110)`。
圖片 `goal053-dosbox-after-enter.png`／`goal053-dosbox-new-world.png` 僅作畫面類別輔助，
不是相同虛擬時間、相同內部狀態或逐像素對拍。容器已停止並由 `--rm` 清除。

### 停止線與下一步

目標 053 已達成；不再把開場退出當作正常啟動受阻。尚未定位本遊戲動態印字，
其他遊戲預置字型 hook 的零次命中不能證明「沒有動態文字」。
`int21 AH=2D` 及 `AH=58 AL=81/83` 仍出現在診斷，沒有證據顯示其阻擋本輪路徑；不順手深挖。
下一步為 [目標 054](docs/goals/054-main-menu-text-provenance.md)，只追一則真正可見選單文字，
接到來源鍵 DRAFT 和第一則中文覆蓋，不宣稱整局可玩、中文化完成或任意快照全面正確。

## 2026-09-22：目標 054 的第一列主選單文字證據

### 輸入與工具

正常入口仍為 `OPENING.EXE -g`，不使用 VICEROY direct-entry。檔案 SHA-256：

| 輸入 | SHA-256 |
|---|---|
| OPENING.EXE | `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` |
| VICEROY.EXE | `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3` |
| GAME.TXT | `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a` |

dosgolem 隔離提交 `22664265ea7d55ea8706448149908c79d3f0897b`，研究映像
`colonization-research:20260920-r2`、Go 1.24；重跑入口見
[目標 054](docs/goals/054-main-menu-text-provenance.md)。探針源碼 `tools/trace_text.go`
SHA-256 `368c673e82746152a1f195e3ea4d6f41619266b84978b206a862454b9978c4bf`。
3M 指令送 Enter，12,000,001 開始正常左鍵按放，25M 將滑鼠移至 `(16,16)`，
30,000,001 結束；輸入時序完整保存在探針，不改遊戲記憶體或亂數。
本輪只驗選單，不宣稱新地圖生成的亂數對拍。

### confirmed：來源、事件、背景與最終畫面

檔案位移 `GAME.TXT:0x1B0` 的 25 bytes，片段 SHA-256
`6d3dbc785cd2b8fe343ae1345d6371b637867083e45f7f50f76eb3ee67fec427`，
執行期 far pointer `6F16:00DF`（dosgolem 線性位址 `0x6F23F`）。
印字入口 `937C:0538`／步數 21,384,086；返回 `937C:1D50`／步數 21,402,955。
入口 AX=86、DX=107、BX=0，原始堆疊：
`501ddf00166f7400166f2ce9020000006b00c700166f82726a0056008600c600`。
原始 caller `937C:1D4D` bytes `e8e8e7`，near call 至 `0538`；入口 bytes `c8080000`。
這些均為執行期段:位移，不能當成 EXE 檔案位移。

畫布在 `2CAE:0000`（線性 `0x2CAE0`），320×200。描述區原始定位
`DS=1C6A:2DA8`，bytes `c80040010000ae2c1700180019001a00`。
呼叫前後整體記憶體改變 277 bytes，其中畫布 180 bytes，A000 顯存沒有改變。
180 個文字像素全為色號 254，包圍盒含端點 `x=86..176,y=107..112`。
其餘記憶體差異不能併作文字遮罩；`tools/analyze_text_capture.py` 可重生差異報告。

滑鼠原停 `(160,100)` 時，23 個文字像素被游標色號覆蓋；正常移開至 `(16,16)` 後，
180 個文字像素全都存續到最終畫面。原型僅接受移開後的精確畫面，不直接抹除游標。
兩次獨立冷啟動的事件、所有讀取紀錄、整體記憶體及下列輸出一致：

| 本機產物（workplace/reports/） | SHA-256 |
|---|---|
| goal054-clear-events.json.idx | `559df11e83c1fb01e2d844a4379af6369e279bf4ea7b4b30c95cbf2d4062c4a1` |
| goal054-clear-events.json.pal | `243ca37172f22fbfb4182d6d495ad129b9a524f093d67f0d1c5e6d215434ee5f` |
| goal054-clear-events.json.event0.before | `da6844a1f1d9c64254f23051e27bc33e5b1f5316c861e8d1beff69dbb90235c2` |
| goal054-clear-events.json.event0.after | `cf70e897c2e9ae93b4e2babb1e6ce7daa34d53525cc02d8b9e59308a2d3b115b` |
| goal054-clear-events.json.memory | `abe37ffcf541ab771e297795989742339c611ddfb0a873405765713ca8656df1` |

### IDA 9.4 非破壞性定位

從最終記憶體取 `[0x937C0,0x967C0)` 得 `goal054-runtime-937c.bin`，12,288 bytes，
SHA-256 `a199bf5285da8b0ecb0a4bed80f14c772068a3b2212d8077577bda1cf4b2bf21`。
IDA raw-binary EA 0 對應 dosgolem runtime `937C:0000`；不是原始 EXE file offset。
沿用 `ida-pro-9.4-idapython:locked-v1`，`tools/ida_text_export.py` 匯出 bytes、原始地址、
推論等級與證據，並保存本機 `goal054-text.i64` 及 `goal054-ida-text.json`。
`sub_538` 是 IDA 自動導覽名稱；函式邊界與其他候選入口保持未知，不自行改名成語意。
資料庫有來自 `1D4D` 與 `1DAA` 的 xref；只有前者已由本輪動態鏈驗證。
`1D24` 是選定的分析視窗，不宣稱已證實函式入口。

目標 054 的 `tools/probe_text.py` 會將上述範圍寫至 `/out/goal054-runtime-937c.bin` 並驗證雜湊；
掛載前先確認 tools／reports 是目錄，輸出擁有者為目前使用者，再執行：

```sh
test -d tools && test -d workplace/reports &&
timeout 60 docker run --rm --network none --memory 1g --cpus 1 --pids-limit 128 \
  --user "$(id -u):$(id -g)" \
  -v "$PWD/tools:/tools:ro" -v "$PWD/workplace/reports:/inputs:ro" \
  -v "$PWD/workplace/reports:/out" \
  -e IDA_EXPORT=/out/goal054-ida-text.json -e IDA_DATABASE=/out/goal054-text.i64 \
  -e IDA_RUNTIME_SEGMENT=937c -e IDA_RUNTIME_OFFSET=0000 \
  -e IDA_ENTRY_OFFSETS=0538,1d24 -e IDA_WINDOW_BYTES=320 \
  ida-pro-9.4-idapython:locked-v1 \
  idat -A -pmetapc -T"Binary file" -o/tmp/text.i64 \
    -S/tools/ida_text_export.py /inputs/goal054-runtime-937c.bin
```

目標 054 停止於最小充分證據。後續規格 009／目標 055 只做本機離線原型；
Issue #6 的三種輸出情境、正式來源鍵及重繪生命週期仍未完成。

### 中文原型與字型限制

版本化 UTF-8 TSV 含 50 筆來源候選；只第一列已動態驗證，其餘不是已命中或正式術語。
Cubic 11 本機字型 SHA-256 `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`，
內嵌版本 1.430；許可為自訂條款，不是 OFL。此處只確認本機內容，正式散布仍需權利審查。
不沿用 psychic-war 倚天字型的個別授權決定。完整本機查核為 `workplace/goal054-font-audit.md`。
離線中文圖片、14 項測試及雜湊見 [目標 055](docs/goals/055-first-text-prototype.md)；
任何圖片、字型、原文盤點與執行期傾印均未納入 Git。

## 2026-09-22：目標 056 的執行中顯示證據

完整入口、固定輸入、命令與收據見 [目標 056](docs/goals/056-live-menu-overlay.md)，
有限正式契約見 [規格 009](docs/spec/009-first-text-overlay-draft.md)。本輪未新增 IDA 語意命名。

- 輸入沿用目標 054：OPENING.EXE SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；VICEROY.EXE
  `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`；GAME.TXT
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`。
- confirmed：dosgolem `22664265ea7d55ea8706448149908c79d3f0897b` 兩次正常啟動各
  16 個印字事件、13 個檢查點；71 份二進位輸出一致。只證實展開變數的標題與一般選項
  兩種情境，不能將多個同類選項充作第三種。
- confirmed：執行期實模式 `937C:0538` 至 `937C:1D50`，首列三次繪製各改變 180 個
  索引值 254 的像素。畫布為實模式 `2CAE:0000`（線性 0x2CAE0），來源為
  `6F16:00DF`（線性 0x6F23F）；GAME.TXT 0x1B0 是檔案位移，不是 CPU 位址。
  新指令觀測器在實際 CPU.Step 前觸發，計數比舊迴圈觀測記錄多 1，不能混用步號。
- confirmed：移入游標不產生新印字事件，且遮到原文字像素；移開可恢復。
  本輪保守回退原文，不推測游標背景。開啟 DIFFICUL.PIK 時撤銷補片。
- confirmed：新 dosgolem `315d17f6697bcd4040b12749a1038fdf677338f8` 的中文與六個
  控制組於 45,000,001 步原版狀態一致。完整 RAM SHA-256
  `6e94f669e9854c3ea306e70c3135ebf4997ff3ed86ec7892be5901701543a45d`；原始畫面
  `6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae`。
  七組共 105 張檢查點圖逐像素驗證；此結果不是完整遊戲或互動視窗驗收。
- 字型沿用上述固定 Cubic 11，本輪使用者確認大小。50 筆來源與占位符驗證通過，
  缺字 0；首列字模 208×22 在 584×28 安全框內。其他 49 筆幾何仍未知，正式散布權未定。

## 2026-09-22：目標057五列重繪與逐列中文

原始定位、輸入SHA、位址基準及勘誤見[規格012](docs/spec/012-five-menu-lines.md)，
可重跑命令及前端入口見[目標057](docs/goals/057-menu-coverage-and-interaction.md)。
這是顯示層擴展，不新增遊戲規則或未知欄位語意。

- confirmed：執行期 `937C:0538 → 937C:1D50`，五列來源 `6F16:00DF/0111/0141/016D/018F`，
  各三次事件；GAME.TXT檔案位移 `0x1B0/0x1CB/0x1E4/0x1F9/0x204` 的bytes各自相等。
  只證明固定字串與檔案片段對應，不把bytes搜尋冒稱新載入器資料流證據。
- confirmed：參數描述皆 `6F16:0074`，14 bytes `0000fe000800fc00fd0000000000`。
  描述區線性 `0x1F448` 新探針取前14 bytes，原守門仍用16 bytes，兩種長度不混稱。
  探針SHA `d05d3d615de3f4abc5cab8eebf244cded4a800d2981f6da736507e131c1891bf`；
  dosgolem `22664265ea7d55ea8706448149908c79d3f0897b` 雙次71份二進位一致。
- 勘誤：第三列英文墨跡沒有被游標改變，不代表中文可安全覆蓋。原版hover圖中
  (133,123)背景45→0、(134,123)背景44→0；完整安全區失配，前三列需回退。
  原先第三列可覆蓋的測試假設已撤回，產品的逐列失配守門未更動。
- confirmed：新隔離引擎 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f` 五列七組原版
  最終狀態一致，RAM SHA `6e94f669e9854c3ea306e70c3135ebf4997ff3ed86ec7892be5901701543a45d`。
  15事件／272幀／15檢查點，105張圖的獨立原底及字模合成完全相同。
  幾何已驗證的草稿由1筆增至5筆，其餘45筆仍未知；兩種文字情境不等於三種。
## 2026-09-22：目標058文字表面盤點與顯示分母

- 輸入為合法DOS版`Sid Meier's Colonization (1994)/SMColoni/COLONIZE/`，
  `tools/inventory_text_surface.py`以位元組讀取18個`*.TXT`，保存各檔SHA-256、大小與
  粗略資料行於本機`workplace/reports/goal058-text-surface.json`。總計4,119個粗略
  資料行；排除空行、`;`註解與`@`指令，但不解析跨行訊息，不含EXE或靜態圖文，
  因此不可稱為玩家可見訊息分母。GAME.TXT為3,421物理行、約1,664粗略資料行。
- `text/draft.zh-Hant.tsv`的定位是檔案位元組位移與原始片段SHA，不是DOS實模式位址；
  本輪189筆全部按其各自檔案SHA驗證。`tools/catalog_progress.py`僅比對目標056／057
  固定收據，得到五個已接受並顯示的主選單鍵、184筆未在該路徑命中及一個未建檔
  來源片段。後者可能為變數展開內容，不可推論成全遊戲缺譯數。
- 難度頁可見兩行標題的原始ASCII字串在LABELS.TXT檔案位移`0x888`與`0x890`；
  既有譯稿為「選擇／難度」。這只證實檔案候選與畫面文字相符，尚未追得該畫面
  的印字事件、輸出安全矩形或中文覆蓋條件。輸入SHA及研究工具版本以本輪本機
  語料收據、`docs/goals/058-translation-corpus-and-player-window.md`與各譯稿欄位為準。
## 2026-09-22：目標060說明訊息原文位元組清冊

- 輸入是合法DOS版`SMColoni/COLONIZE/GAME.TXT` SHA-256
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`，以及
  `MAPEDIT.TXT` SHA-256
  `764a67a9ff8f45b9ac9d82809ad616e2c350ff0172d9147ad34478828af57516`。
  工具為`colonization-research:20260920-r2`內Python 3.11.2與
  [雙語語料建置器](tools/build_help_bilingual.py)；位址欄均為**檔案位元組位移**，不是DOS
  實模式、IDA線性或畫布位址。首個`@TUTORIAL1`章節位移`0x1316A`，文字起點
  `0x13190`；最後的`@HELP5`章節位移`0x1231`，文字起點`0x1251`。
- confirmed（檔案來源）：19段`GAME.TXT @TUTORIAL`與5段`MAPEDIT.TXT @HELP`皆唯一，
  原文、CRLF、區塊位移、片段SHA可從固定輸入重生。繁中為**譯文草稿**，只核對
  占位符與`{}`／`^`等控制碼，尚無dosgolem呼叫點、畫面安全矩形或玩家路徑命中。
  詳細每筆原始定位與指紋在[雙語TSV](text/help-bilingual.tsv)；原文只推私有repo。

## 2026-09-22：目標061難度頁執行期原文定位

- 輸入為合法DOS版`LABELS.TXT`（SHA-256
  `e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`）
  及本機正常視窗收據`goal059-ebiten.memory`；研究工具為
  `colonization-research:20260920-r2`內Python 3.11.2，dosgolem隔離副本提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`。
- confirmed：檔案位元組空間`0x888`／`0x890`的標題原文，分別在DOS線性記憶體空間
  `0x4DF72`／`0x4DF79`出現；完成提示在DOS線性空間`0x2A7B5`及`0x4DF59`出現。
  單次結束快照不能證實印字呼叫點、文字來源指標、圖像分類或安全矩形；詳見
  [規格014](docs/spec/014-difficulty-text-output-draft.md)。

## 2026-09-22：難度頁兩段標題的印字與畫布證據

- 原版輸入版本：`OPENING.EXE` SHA-256 `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；
  `VICEROY.EXE` SHA-256 `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`；
  `GAME.TXT` SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
  `LABELS.TXT` SHA-256 `e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`。
  工具：隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`、
  `colonization-research:20260920-r2`、[唯讀探針](tools/probe_difficulty_writes.go)。
- 位址空間：`LABELS.TXT` `0x888`／`0x890` 是**檔案位元組位移候選**；
  `0x4DF72`／`0x4DF79` 是 DOS **20-bit 線性記憶體**；`0D3A:0015` 是 DOS
  **實模式 CS:IP** 首字讀取，`0E2D:1194` 再讀同來源，`0D21:012C` 是
  畫布寫入位址；(x,y) 是 **320×200 原始畫布座標**，不能與其他基準混用。
- confirmed：真視窗同輸入首次原文讀取後，兩段墨跡分別改變 126／284 點，
  bbox (42,16)–(72,23) 與 (23,29)–(91,37)。兩次獨立重播的讀寫事件、
  七份畫布／索引檢查點及最終 RAM 雜湊完全相同；完整差分都在各自安全矩形。
  檔案至執行期的載入器資料流尚未完整追畢，來源檔位移仍為候選而非證實載入邊。
- 規格014限定兩行升至 CONFORMED。Ebitengine 真視窗九筆實際輸入中文、中文重播、
  英文控制的原版完整狀態一致；中文字圖與英文控制比較，安全矩形外零差異。
  本機完整收據 `workplace/reports/goal061-ebiten-clear-receipt.json`，私有 README
  只選兩張可見成果圖，不公開原版輸入或原始快照。

## 2026-09-22：難度頁完成提示的獨立輸出事件

- 固定原版 `LABELS.TXT` SHA-256 為 `e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`；
  檔案位元組位移 `0x86E` 的 24-byte 原文為 `Click Here When Finished`，其後為 CR。
  執行期 DOS 20-bit 線性記憶體 `0x4DF59` 的同文其後為 NUL；檔案至記憶體完整載入邊仍未證實。
- 工具為隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`、
  `colonization-research:20260920-r2` 與 `tools/probe_difficulty_writes.go`。兩次正常滑鼠路徑
  重播於 DOS 實模式 `0E2D:11CF` 讀取原文，後續 `0D21:012C` 寫出 167 個變更像素；
  320×200 原始畫布 bbox 為 (13,81)–(101,85)，變更色號全為 254，安定後不再變動。
  兩次事件、畫布檢查點與最終原版 RAM 一致。原始輸入其餘雜湊與地址空間見
  [規格015](docs/spec/015-difficulty-finish-prompt.md)；本結論僅對固定版本及該畫面 confirmed。
- Ebitengine／Xvfb 真視窗九筆滑鼠輸入的中文原跑、重播與英文控制原版狀態一致；
  輸出圖差異只在三個獨立安全矩形，完成提示區佔 2,856 個 4 倍畫布像素。
  原版截圖只留私有儲存庫；完整本機收據 `workplace/reports/goal062-ebiten-receipt.json`。

## 2026-09-22：第一張難度卡片文字的未閉合輸出路徑

- 固定輸入雜湊、工具版本與地址空間見[規格016](docs/spec/016-difficulty-card-text-draft.md)。
  使用 `tools/probe_difficulty_writes.go` 從 `OPENING.EXE -g` 及九筆既有真視窗
  滑鼠輸入兩次重播到 3,200 萬步；輸入、最終 RAM、索引畫面、色盤、原始畫布
  雜湊相同。檢查點路徑不同，故 JSON 整體不能逐 byte 比較。
- confirmed：第一張卡片文字區在 2,980 萬步附近的前後原始畫布差分為 224 點，
  bbox `(141,45)–(182,58)`；最終畫面可見 `Discoverer`／`Easiest`。
  DOS 線性 RAM 候選分別為 `0x4CC6A`／`0x4DF90`，但完整來源路徑未知。
- confirmed（觀測限制）：從冷啟動監看兩處線性 RAM 讀取均零命中；卡片區
  `WatchWrites` 亦零命中。不可將此解讀為原版沒讀寫或卡片一定是靜態圖，
  更不可用字串存在 RAM 當作輸出掛鉤的證據。下輪須追批次畫布複製、
  其他字串副本或圖像來源；未達 READY 前保持英文。

## 2026-09-22：百科建國元勳文章來源語料

- 固定 `PEDIA.TXT` SHA-256 為
  `cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1`。
  `@FATHER0` 至 `@FATHER24` 是25個唯一、連續的文章章節鍵；其每篇章節位移、
  文字位移、長度和片段SHA-256都由[語料建置器](tools/build_pedia_bilingual.py)
  從唯讀原版重生至私有 `text/pedia-bilingual.tsv`。
- confirmed（來源與格式）：25／25篇的繁中草稿保留 `^`、大括號、`%%`與變數；
  三項合成回歸、固定來源驗證及 Cubic 11 24px 字型覆蓋均通過，缺字0。
  此結果只證實私有語料的來源與格式；執行期輸出事件、畫面安全矩形、變數實值與
  歷史／術語定稿皆為未知或待審，不能計入八段畫面中文數。

## 2026-09-22：百科貨物文章來源語料

- 輸入仍為合法DOS版 `PEDIA.TXT`，SHA-256
  `cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1`；
  `@CARGO0` 至 `@CARGO15` 是16個唯一、連續的文章章節鍵。每篇章節／文字位移、
  長度與片段SHA-256都在[百科雙語TSV](text/pedia-bilingual.tsv)中，以**檔案位元組
  位移**記錄，並非DOS實模式、線性記憶體或畫布座標。
- confirmed（來源與格式）：選定的25篇`@FATHER`加16篇`@CARGO`可由
  `colonization-research:20260920-r2` 的[建立器](tools/build_pedia_bilingual.py)從唯讀
  輸入重生。41篇逐列核對原文、變數、`^`、大括號與`%%`；4項合成回歸及 Cubic 11
  24px字型覆蓋均通過，缺字為0。
- unknown（畫面與術語）：這只驗證私有TSV的來源與格式，不能證實百科輸出事件、變數
  實值、中文安全矩形或玩家路徑。所有貨物譯文維持`draft`；「原住民」等用語是草稿，
  不是術語定稿，不能外推成完整中文化或改變原版機制。

## 2026-09-22：百科單位文章來源語料

- 輸入仍為合法DOS版 `PEDIA.TXT`，SHA-256
  `cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1`；
  `@UNIT0` 至 `@UNIT23` 是24個唯一、連續的文章章節鍵。每篇章節／文字位移、長度與
  片段SHA-256都在[百科雙語TSV](text/pedia-bilingual.tsv)中，以**檔案位元組位移**
  記錄，並非DOS實模式、線性記憶體或畫布座標。
- confirmed（來源與格式）：選定的25篇`@FATHER`、16篇`@CARGO`加24篇`@UNIT`可由
  `colonization-research:20260920-r2` 的[建立器](tools/build_pedia_bilingual.py)從唯讀
  輸入重生。65篇逐列核對原文、變數、`^`、大括號與`%%`；4項合成回歸及 Cubic 11
  24px字型覆蓋均通過，缺字為0。`@UNIT23`原文只有標題，目錄也只保存該標題。
- unknown（畫面與術語）：這只驗證私有TSV的來源與格式，不能證實百科輸出事件、變數
  實值、中文安全矩形或玩家路徑。兵種、船型、殖民與原住民相關譯語全是`draft`，
  不能外推成術語定稿、完整中文化或改變原版機制。

## 2026-09-22：百科地形文章來源語料

- 輸入仍為合法DOS版 `PEDIA.TXT`，SHA-256
  `cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1`；
  `@TERRAIN0` 至 `@TERRAIN28` 是29個唯一、連續的文章章節鍵。每篇章節／文字位移、
  長度與片段SHA-256都在[百科雙語TSV](text/pedia-bilingual.tsv)中，以**檔案位元組位移**
  記錄，並非DOS實模式、線性記憶體或畫布座標。
- confirmed（來源與格式）：選定的25篇`@FATHER`、16篇`@CARGO`、24篇`@UNIT`加
  29篇`@TERRAIN`可由`colonization-research:20260920-r2`的[建立器](tools/build_pedia_bilingual.py)
  從唯讀輸入重生。94篇逐列核對原文、變數、`^`、大括號與`%%`；4項合成回歸及 Cubic 11
  24px字型覆蓋均通過，缺字為0。相近的森林文章仍各以固定鍵與片段指紋保存。
- unknown（畫面與術語）：這只驗證私有TSV的來源與格式，不能證實百科輸出事件、變數
  實值、中文安全矩形或玩家路徑。地形、資源與效果相關譯語全是`draft`，不能外推成
  術語定稿、完整中文化或改變原版機制。

## 2026-09-22：百科職業文章與 Tab／marker 來源契約

- 輸入仍為合法DOS版 `PEDIA.TXT`，SHA-256
  `cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1`；
  `@JOB0` 至 `@JOB26` 是27個文章鍵。`@JOB12`的原始marker是 `@JOB12 `，尾端帶一個
  ASCII空白；建立器以該精確marker定位，並把固定章節位移、文字位移、長度與片段SHA-256
  寫入[百科雙語TSV](text/pedia-bilingual.tsv)。這些位置全是**檔案位元組位移**，不是DOS
  實模式、線性記憶體或畫布座標。
- confirmed（原始格式）：同一固定檔有且只有一個Tab，位於檔案位元組位移`0x00008429`，
  原始行 bytes 為`^\\t\\r\\n`，位於`@JOB8`文章。`PEDIA.TXT`沒有反斜線字元；同目錄
  `README.TXT`另有17個Tab但不在本批語料範圍。使用者選定原始Tab位元組保留，因此TSV用
  字面`\\t`逃脫、解碼後必須在原文與譯文有相同控制序列；不把它正規化為空白，也不略過文章。
- confirmed（來源與格式）：選定的25篇`@FATHER`、16篇`@CARGO`、24篇`@UNIT`、29篇
  `@TERRAIN`加27篇`@JOB`可由`colonization-research:20260920-r2`的
  [建立器](tools/build_pedia_bilingual.py)從唯讀輸入重生。121篇逐列核對原文、變數、
  `^`、大括號、`~`、`_`、Tab與`%%`；13項合成回歸及 Cubic 11 24px字型覆蓋均通過，
  缺字為0。`@JOB18`原文只有標題，目錄也只保存該標題。
- unknown（畫面與術語）：這只驗證私有TSV的來源與格式，不能證實百科輸出事件、變數實值、
  中文安全矩形或玩家路徑。職業、殖民、原住民與宗教相關譯語全是`draft`，不能外推成
  術語定稿、完整中文化或改變原版機制。

## 2026-09-22：百科建築文章與 CP437 `0xF9` 正規化

- 輸入仍為合法 DOS 版 `PEDIA.TXT`，SHA-256
  `cd0bf6880d62df13b5f9fb4212a7ac20e60032db9de7aa3ad00862c422bb34d1`。`@BUILDING0`至
  `@BUILDING41`是42個唯一文章鍵；其章節與文字位移、長度及片段 SHA-256 均由
  `colonization-research:20260920-r2` 的[建立器](tools/build_pedia_bilingual.py)寫入
  [百科雙語TSV](text/pedia-bilingual.tsv)，位址基準一律是**檔案位元組位移**。
- confirmed（原始位元組）：固定檔中的高位元組僅有22個 CP437 `0xF9`，皆在
  `@BUILDING12`、`@BUILDING13`、`@BUILDING14` 的清單行，且緊隨 `^`。原始輸入未修改；
  原文區塊與其 SHA 仍可由固定檔重生。
- 使用者決定（非原版推論）：將這個顯示控制符號正規化為 U+2022 `•`，而非 CP437 直接
  解碼的 U+2219；排除新增 U+2219 字型或 fallback。建立器先拒絕其他未確認高位元組，再把
  `0xF9` 正規化，並要求譯文在相同順序保留 `•`。這使 Cubic 11 24px 審核可繪製而不改變
  原始 byte 證據。
- confirmed（來源與格式）：25篇建國元勳、16篇貨物、24篇單位、29篇地形、27篇職業與42篇
  建築，共163篇可由唯讀輸入重生。15項 help／百科回歸通過；`rich2-py:latest` 審核收據為
  `source_and_control_passed: 163`、`rows_with_missing_glyphs: 0`。
- unknown（執行期與版面）：收據的 `runtime_display_verified` 為 false。尚無 PEDIA 的
  dosgolem 輸出事件、中文安全矩形、Ebitengine畫面或正常玩家路徑，所有163篇維持`draft`，
  不計入八段已顯示中文或全遊戲完成度。

## 2026-09-22：`NAMES.TXT` 複合資料的分類停止點

- 輸入為合法 DOS 版 `NAMES.TXT`，SHA-256
  `4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061`，大小13,820 bytes、
  473個 CRLF 實體行。檔首原始註解警告修改內容可能導致遊戲故障，故原版只以唯讀掛載盤點。
- confirmed（檔案分類）：430個非空行中，246個含逗號；其中14個是註解，其餘232個為資料。
  214個在地形／資源／國家／等級／建國元勳等區段，名稱欄後接數值規則或權重；18個在
  `Extra tribe names` 部族別名區段。70個無逗號的資料行均已存在主譯稿，沒有可再擴充的
  單行候選。
- confirmed（格式限制）：主譯稿 `text/draft.zh-Hant.tsv` 以整個原始行的位移、長度與 SHA
  驗證候選，無法只替複合行的第一欄建立可回查、又不誤認為原版整行顯示文字的資料列。
  在新的欄位識別 DRAFT 規格與使用者確認前，不翻譯這232行，也不修改原版資料。
- unknown（執行期）：目前沒有 dosgolem 證據指出上述任一欄在何畫面或以何種輸出呼叫顯示；
  此分類既不證實規則資料完全不會顯示，也不授權把顯示譯文套進語意／查找路徑。

## 2026-09-22：目標071單行文字的來源與控制碼收據

- 輸入為合法 DOS 版 `MAPMENU.TXT`、`WOODCUT.TXT`、`OPENING.TXT` 與`CLOSING.TXT`；其固定
  檔案 SHA-256 見[目標071](docs/goals/071-mapmenu-woodcut-corpus.md)。建立器在各自檔案位元組
  空間定位44個獨立資料行，並將檔案 SHA、行首位移、行長與行片段 SHA 寫入
  [主譯稿](text/draft.zh-Hant.tsv)；這些位移不是 DOS 實模式、線性記憶體或畫布座標。
- confirmed（來源與格式）：28個地圖編輯器選單／說明入口、14個具語意過場標題及兩個載入訊息
  皆可從唯讀輸入重生。建立器拒絕逗號複合資料、註解、`@` 指令、行中位移與重複候選；全目錄
  368筆經 CRLF、原始與片段 SHA、變數、`{}`、`^`、`~`、`_`、`#` 逐序驗證。
- confirmed（字型）：`rich2-py:latest` 以 Cubic 11、24px 審核368筆，
  `source_and_placeholder_passed` 為368、`rows_with_missing_glyphs` 為0。完整報告只在已忽略的
  `workplace/reports/goal071-draft-review.json`，字型本體不入版控。
- unknown（執行期與語意）：44筆都沒有 dosgolem 輸出事件、中文安全矩形、Ebitengine畫面、
  正常玩家路徑、變數展開或術語定稿證據；它們全為`draft`，不能計入已顯示中文或完整翻譯。

## 2026-09-22：目標072 README 玩家說明範圍證據

- 輸入：使用者提供、唯讀的 `Sid Meier's Colonization (1994).zip`；成員為
  `SMColoni/COLONIZE/README.TXT`。以 `colonization-research:20260920-r2` 的 Python 3.11
  `zipfile` 讀取，成員 SHA-256 為
  `d78a219bfd041e3d4f3327d6b012dc433fd3734472c68cbace0490b9e46ac19e`、長度7,477 bytes、195行。
- 原始 CP437 位元組段落已確認：版本前言／修正 `0x0000`–`0x0712`；技術排錯
  `0x0712`–`0x0b76`；地圖編輯器 `0x0b76`–`0x0e7e`；作弊說明 `0x0e7e`–`0x1a79`；音效排錯
  `0x1a79`–`0x1d35`。此為 `confirmed` 的檔案邊界與內容分類，不是執行期輸出或畫面命中證據。
- 作弊說明中的按鍵和符號是原文操作契約：`Alt-W`、`Alt-I`、`Alt-N`、`Shift-F1` 至
  `Shift-F7`、`T`、`S`、`$`、`%`、`^`、`!`、`[`、`]`、`Space`。建立器須逐序驗證，不能由
  譯者自由改寫。

## 2026-09-22：目標072 README 譯稿完成收據

- confirmed（來源）：`text/readme-bilingual.tsv` 的7列由 `build_readme_bilingual.py` 從固定 ZIP
  與唯一成員重建。建立器核對封存檔 SHA-256
  `8aa93f219a6166712933bc60e402fe78024df1de821605c3036e1ae14e619867`、成員 SHA-256、CRLF、
  七個已排序且不重疊範圍、範圍長度與每段原始位元組 SHA；任何不符皆失敗即關閉。
- confirmed（格式）：六項無原版單元測試覆蓋重疊範圍、合成 ZIP 指紋、按鍵重排、符號遺漏與
  Tab 遺漏。Docker 以唯讀 ZIP 暫時解包驗證34項語料測試，以及368筆主譯稿、24則help、
  163篇百科和7則README的固定來源。
- confirmed（字型）：`rich2-py:latest`、Cubic 11、24px 的
  `workplace/reports/goal072-readme-review.json` 顯示 `source_and_control_passed: 7`、
  `rows_with_missing_glyphs: 0`。
- unknown（執行期與版面）：報告的 `runtime_display_verified` 為 false。七則 README 仍未取得
  dosgolem 輸出事件、覆蓋鍵、中文安全矩形、Ebitengine 視窗或正常玩家路徑；不計入八段已顯示
  中文、完整說明文字或全文中文化完成度。

## 2026-09-23：目標073殖民地名稱來源與呈現決定

- confirmed（來源）：唯讀 DOS ZIP 的 `SMColoni/COLONIZE/COLONY.TXT` SHA-256 為
  `2996f8a9d53a7f7a93e4a238bfd2ba727c4cf5cdabc334c4059c6860c9e4ae36`，長2,540 bytes。
  四個 `@` 章節的資料筆數為 ENGLISH 36、FRENCH 66、SPANISH 39、DUTCH 32，共173筆；僅
  ENGLISH 有18筆 `名稱,四位年份` 的資料行。
- confirmed（使用者決定）：玩家顯示譯稿採「中文名稱（原名，年份）」；無年份者採
  「中文名稱（原名）」。這是顯示文案政策，不是原版資料格式或執行期命中證據。
- unknown（執行期與版面）：尚未驗證 `COLONY.TXT` 每筆名稱的畫面輸出、最大同時可見數、中文安全
  矩形、字級或基線。原始名稱檔頭的23字元儲存限制不證實中文覆蓋的可用版面；未來須依欄位量測，
  不得套用固定字級。

## 2026-09-23：目標073殖民地名稱譯稿完成收據

- confirmed（來源與格式）：`build_colony_bilingual.py` 從固定 ZIP 唯讀重建173列，核對封存檔與
  `COLONY.TXT` SHA、CRLF、ENGLISH／FRENCH／SPANISH／DUTCH 四個章節、各自36／66／39／32筆、
  `名稱`或`名稱,四位年份`、章節與行首位置、原始資料行 SHA。它拒絕未知章節、複合資料、重複鍵、
  缺譯或不符「中文名稱（原名，年份）」格式的譯文。
- confirmed（回歸）：六項無原版單元測試覆蓋指紋、複合資料、年份、原名與中文前綴；Docker 以唯讀
  ZIP 暫時解包重跑40項測試，並通過368筆主譯稿、24則help、163篇百科、7則README與173筆名稱
  的固定來源驗證。
- confirmed（字型字元）：`rich2-py:latest` 以 Cubic 11 cmap 審核的
  `workplace/reports/goal073-colony-review.json` 顯示 `source_and_format_passed: 173`、
  `rows_with_missing_glyphs: 0`。此檢查不載入字級；它不是排版或覆蓋驗收。
- unknown（執行期與版面）：`runtime_display_verified` 與 `per_field_font_selection_verified` 都為 false。
  沒有名稱輸出事件、欄位安全矩形、原版字級／基線、Ebitengine畫面或正常玩家路徑；173筆不計入
  已顯示中文或全文中文化完成度。

## 2026-09-23：目標074難度卡片監看勘誤與重播

- 問題與舊結論：目標063報告第一張難度卡片的兩段候選原文讀取與卡片畫布寫入均為零。
  檢查隔離 dosgolem `internal/machine/machine.go` 的 `WatchWrites`／`WatchReads`（程式來源位址
  `machine.go:707`／`:722`）確認兩者各只有一組註冊槽；舊 `tools/probe_difficulty_writes.go`
  對每種各註冊兩次，後一次覆蓋前一次。舊零命中是探針缺陷，不能當原版沒有讀寫的反向證據。
- 固定輸入與工具：合法 DOS 版 `OPENING.EXE` SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`、
  `VICEROY.EXE` `a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`、
  `GAME.TXT` `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`、
  `LABELS.TXT` `e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`。
  九筆正常玩家輸入 `goal059-ebiten.inputs.json` SHA-256 為
  `51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc`。
  隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；Docker 映像
  `colonization-research:20260920-r2` ID `sha256:5d99f8754e9f9099b7f263268c485c73043aee1a9d9d29231417ccb5b5da02e1`；
  修正探針 SHA-256 `dfeb232a6effb70f6609b5fa5f300a08b4174f369c08761d49f35eea10671fb1`，
  收據內標示 `goal074-unified-watch-v1`。
- confirmed（DOS 真實模式 `CS:IP` 與20-bit 線性記憶體）：兩次獨立冷啟動皆於步數
  `29,797,568` 的 `0E2D:11CF` 讀取線性 `0x4CC6A..0x4CC74`，位元組為
  `Discoverer\0`；步數 `29,813,172` 同址讀取 `0x4DF90..0x4DF97`，位元組為
  `Easiest\0`。原文後段 NUL 是資料，不是譯文文字。上述線性位址不是 TXT 檔案位移。
- confirmed（320×200 原始畫布）：`0D21:012C` 在第一張卡片區於步數
  `29,798,340..29,819,570` 有292次變更值寫入，bbox `(141,45)–(182,58)`；
  第一段讀取後且第二段讀取前有192次，第二段讀取後有100次。
  標題／提示另有4個畫布寫入位置與11個來源讀取位置，證明兩路觀測同時有效。
  `DIFFICUL.PIK` 在正常路徑確有開啟；兩次最終完整 RAM、畫布、索引畫面、色盤與事件一致。
  最終 SHA-256 依序為 `09e9fbf961b8b50115fa0c8b707d4a220cf7f12b3e2a359311073f85786ad109`、
  `08edaac74a54263b8e093010d8cbc97d3f9820c3c151f28d80beded5c5a8a650`、
  `6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae`、
  `762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82`。
  這四項最終雜湊也與舊 `goal063-card-reads.json` 相同，排除本次監看修正造成
  玩家狀態或影像軌跡偏移的疑慮；舊收據中的讀寫零命中仍須撤回。
- 強推論／未知：時間順序與同區畫布寫入支持兩段原文驅動卡片文字，但尚無來源讀取到
  `0D21:012C` 的直接呼叫／資料流鏈，亦未證明 `GAME.TXT` 或 `NAMES.TXT` 哪個提供執行期字串。
  原版字級、基線、可逆背景、中文安全矩形、其餘卡片與游標遮擋仍未知；
  [規格016](docs/spec/016-difficulty-card-text-draft.md)保持 DRAFT，八段已顯示中文計數不變。
- 重現：在 `colonization-research:20260920-r2` 以目前 UID/GID、唯讀原版與隔離 dosgolem，
  由 `workplace/dosgolem` 執行 `go run /work/tools/probe_difficulty_writes.go`，指定原版根目錄、
  上述輸入檔、`-end 32000000`，分別輸出本機
  `workplace/reports/goal074-card-observer-a.json` 與 `-b.json`；再執行
  `tools/check_difficulty_observer.py` 比對。原始 `.canvas`／`.idx` 及完整 JSON 只留本機。

## 2026-09-23：目標075第一張難度卡片原文到像素的直接鏈

- 問題：目標074已同時觀測原文讀取與後續畫布寫入，但其先後順序不能單獨證明
  是同一條資料流。目標075只追第一張卡片兩行的正常玩家輸出；不改原版檔、記憶體、
  遊戲規則、輸入或正式中文疊圖。
- 固定輸入與工具：原版四檔與 SHA 見[規格016](docs/spec/016-difficulty-card-text-draft.md)；
  九筆正常玩家輸入 `goal059-ebiten.inputs.json` SHA-256
  `51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc`。
  隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，其
  `upstream` 推送位址為 `DISABLED`；Go `1.24.13 linux/amd64`；映像
  `colonization-research:20260920-r2` ID
  `sha256:5d99f8754e9f9099b7f263268c485c73043aee1a9d9d29231417ccb5b5da02e1`。
  探針 `tools/probe_card_flow.go` SHA-256
  `7a43c7787c2913d8bb01ab804304ba78b011644836a7651cadd72bdcc828826e`，
  檢查器 `tools/check_card_flow.py` SHA-256
  `8a35948a88679e7fac8f55586c6c7fc68343d1b68057cff89965a77dc24aaea0`。
  以下 `CS:IP` 是 dosgolem 執行期真實模式指令位址，`0x2...`／`0x4...` 是
  DOS 20-bit 線性 RAM，畫布座標是320×200邏輯像素；都不是 TXT 檔案位移。
- confirmed（來源與複製）：`0E2D:11CF` 於步數 `29,797,568` 讀取線性
  `0x4CC6A..0x4CC74` 的 `Discoverer\0`；`0E2D:11EB` 在 `29,797,579`
  將10個可見字元按序寫至 `0x2A74C` 起。另一行於 `29,813,172` 讀取
  `0x4DF90..0x4DF97` 的 `Easiest\0`，在 `29,813,183` 複製到相同共用緩衝。
  這是同一步原文讀取／寫入的位元組與指令位置配對，不是文字相同的猜測。
- confirmed（格式化後的真正輸出字節）：第一行共用緩衝後續被整理為
  `DISCOVERER:`；`0E2D:11A5` 在步數 `29,798,246` 從 `0x2A74C` 讀取該
  字串並同一步複製 `DISCOVERER:\0` 至 `0x2A6B0` 局部副本。第二行在
  `29,813,648` 同路徑複製 `Easiest\0`。`0D21:00C6` 逐字讀取局部副本，
  第一行 `DISCOVERER:\0`、第二行 `Easiest\0` 各完整遍歷兩次；同一
  `0D21` 印字常式的 `0D21:012C` 在其後分別寫入192／100次卡片畫布像素。
- confirmed（位置與字高）：`0D21:000C` 進入繪製時 `(AX,DX)` 在兩次遍歷為
  第一行 `(142,45)`／`(141,45)`，第二行 `(151,53)`／`(150,53)`。
  繪製前後畫布差分皆只落在第一張卡片觀測區，第一行164個最終不同像素、
  bbox `(141,45)–(182,49)`、墨跡高5個原始像素；第二行83個、bbox
  `(150,53)–(174,58)`、墨跡高6個原始像素。第一行結束與第二行開始前的
  原始畫布完全相同。入口 `DX` 與墨跡頂列相符，但尚無獨立字型 baseline 證據。
- confirmed（權利與背景限制）：原版卡片內候選矩形
  `(138,44)–(185,50)`、`(146,52)–(179,59)` 在文字寫入前分別有75、78種
  色盤索引。純色抹底會破壞原版紋理；正式翻譯須保存同狀態可逆背景，不能用
  主選單純色清底或全域24px字級外推。
- confirmed（決定性）：兩次 `goal075-card-flow-v5-a.json`／`-b.json` 的
  JSON 位元組及 SHA-256 完全相同，均為
  `67f416ce61db7bec2cf3fbd71bb3336e68354b88c97b9a24a9f357ef6986ed9e`。
  結束於3,200萬步，最終完整 RAM、原始畫布、索引畫面與色盤 SHA 與目標074
  四項完全相同。`tools/check_card_flow.py`、`go vet` 與 dosgolem
  `internal/machine`／`oracle` 測試均通過。
- unknown／下一閘門：`Discoverer` 在 `GAME.TXT`／`NAMES.TXT` 都有同文；
  尚未追到哪個檔案載入該執行期地址。`Easiest` 在 `LABELS.TXT` 有唯一文字候選，
  仍未證實載入邊。第一張卡片的背景擷取／游標遮擋、穩定顯示鍵、中文安全矩形、
  分欄中文字級和第二張以後的玩家輸入與輸出均未驗證；規格016維持 DRAFT，
  八段已顯示中文計數不變。
- 重現：Docker 將合法 DOS 輸入及隔離 dosgolem 以唯讀掛至 `/work`，僅
  `workplace/reports/` 可寫，使用目前 UID/GID、`--network none` 和資源上限；
  從 `/work/workplace/dosgolem` 執行
  `go run /work/tools/probe_card_flow.go -root <原版COLONIZE目錄> -inputs /work/workplace/reports/goal059-ebiten.inputs.json -out <a或b報告>`，
  再以 `tools/check_card_flow.py` 的 `--inputs`／`--first`／`--second` 核對。
  完整 JSON 含原版局部指令與快照，只留已忽略的本機目錄，不入 Git。

## 2026-09-23：目標076第一張難度卡片的可逆背景及逐欄字級預覽

- 固定輸入與工具：合法 DOS 原版 `OPENING.EXE`／`VICEROY.EXE`／`GAME.TXT`／
  `LABELS.TXT` 的 SHA-256 見[規格016](docs/spec/016-difficulty-card-text-draft.md)；
  正常玩家九筆輸入 `goal059-ebiten.inputs.json` SHA-256
  `51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc`，
  目標075雙次收據各為
  `67f416ce61db7bec2cf3fbd71bb3336e68354b88c97b9a24a9f357ef6986ed9e`。
  dosgolem 隔離副本提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；
  研究映像 `colonization-research:20260920-r2`，字型量測映像 `rich2-py:latest`
  ID `sha256:e5c73862da40d1e0c26d9d5f6a62491c75ddfe8ada5c77677e1e445f13d85a71`，
  Ebitengine 2.9.9 映像 `psychicwar-go-ebiten:latest` ID
  `sha256:083e45e6bc0f01ca46ba0774581572c80a607120431b530de72cdd6ffb36f2f7`。
  Cubic 11 本機字型 SHA-256
  `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`；
  字型與完整原版快照均不入 Git。
- 地址空間與 confirmed 證據：目標075的 `0E2D:11CF`、`0D21:012C` 為原版 DOS
  真實模式 `CS:IP`；`0x4CC6A`／`0x4DF90` 為20-bit 線性 RAM；本輪所有矩形是
  320×200 邏輯畫布的**半開像素座標**，不是原始 TXT 檔案偏移。
  原版稱號畫布差分 `(141,45)–(182,49)` 高5像素，副標 `(150,53)–(174,58)`
  高6像素。稱號恢復候選區 `(138,44)–(186,51)` 由 `before-first` 取得，
  副標 `(146,52)–(180,60)` 由 `before-second` 取得。原版最終真視窗畫面
  SHA-256 `6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae`
  的這兩區與 `after-second` 快照相同；色盤 SHA-256
  `762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82`。
  最後游標不在擴大卡片區，無按鍵保持。這證明固定終點可逆，不證明其他輸入或時刻。
- 字型量測與強推論：原版 5／6 像素墨跡經4倍輸出為20／24px；Cubic 11
  的 21px 候選「發現者」墨跡 `69×19px`、位置 `(614,180)`，25px 候選
  「最簡單」墨跡 `81×23px`、位置 `(612,212)`。兩者各比相應原版放大墨跡
  低1px，且在安全區內保留邊界；這是視覺設計候選，不是原版獨立 baseline
  或最終玩家偏好。文字來自唯一 `text/draft.zh-Hant.tsv`，前者暫用
  `GAME.TXT:0x00000A26`，但來源檔載入邊未知，不能以這個候選當正式鍵。
- confirmed（原型像素）：Ebitengine 在 Xvfb 產生 `goal076-card-control.png` 和
  `goal076-card-zh.png`，再由獨立檢查器逐像素比對。原文控制圖完全等於固定
  原版畫布的最近鄰放大；中文圖只有上述兩個矩形與控制圖不同，稱號區2,752點、
  副標區1,860點；透明中文字模下的每個像素都恢復原版背景。PNG SHA-256 依序
  `df65ae068485d5c785ce3130fb136bb781f4116e262238788fe10d8f2f0953e5`、
  `65d808bcfdd6c5c2afc3be1c46166429cb113903aaa222c2e14b01b038df8463`。
  首次失敗因原型透明像素錯用 RGBA，出現亮色滲出；修正為 NRGBA 後同資料重跑 PASS。
  這是畫布讀回，不是 `import -window` 真實視窗截圖或正式 runtime 覆蓋收據。
- unknown／停止線：任意時刻的執行期背景擷取與游標／後續繪圖回退、原始 TXT
  載入邊、穩定顯示鍵、第二張以後的卡片仍缺。規格016維持 DRAFT；現有八段
  已顯示中文不增加。重跑入口為 `tools/prepare_card_preview.py`（固定原版收據
  與字型）→ `tools/card_preview.go`（Ebitengine／Xvfb 的 `-control`／中文圖）→
  `tools/verify_card_preview.py`（逐像素核對）；完整資料及 PNG 只在
  `workplace/reports/goal076-card-*`，不入 GitHub。

## 2026-09-23：目標077原始 TXT 載入至第一張難度卡片 RAM

- 輸入與工具：正常玩家九筆輸入 `goal059-ebiten.inputs.json` SHA-256
  `51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc`；
  原版 `OPENING.EXE`／`VICEROY.EXE`／`GAME.TXT`／`LABELS.TXT` 指紋見
  [規格016](docs/spec/016-difficulty-card-text-draft.md)，新增核對 `NAMES.TXT`
  SHA-256 `4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061`。
  隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；
  `colonization-research:20260920-r2` 映像 ID
  `sha256:5d99f8754e9f9099b7f263268c485c73043aee1a9d9d29231417ccb5b5da02e1`。
  `tools/probe_card_load.go` 使用 dosgolem `DOS.Reads`／`FileOps` 與單一讀、寫監看器；
  `tools/check_card_load.py` 獨立驗證，並串接目標075原文至像素檢查器。
- 位址空間：`0xC0C`／`0x8A9`／`0xA26` 是對應原始 TXT 的**檔案位移**；
  `0E2D:1F76`、`1F86`、`09F4`、`09F5`、`11A5` 是 dosgolem 中原版
  DOS 真實模式 `CS:IP`；`0x2B00E` 等是 20-bit 線性 RAM，不是 IDA 位址。
  `AH=3Fh` 的 `DS:DX`、成功讀取長度及檔案偏移由同一步 DOS 收據核對；
  寫入來源的 `DS:SI` 與目的的 `ES:DI` 由監看事件的原始暫存器驗證。
- confirmed（稱號）：`NAMES.TXT:0xC0C` 的十個原文字節 `Discoverer`
  於步數16,208,974 從檔案偏移 `0xC00` 起的讀取塊進入 `0x2B00E`；
  原版 `0E2D:1F76` 讀取，`0E2D:1F86` 就地整理到 `0x2B00D`；
  `0E2D:09F4` 再讀、`0E2D:09F5` 寫入中間緩衝 `0x249DC`；
  `0E2D:11A5` 於步數16,215,523 寫入目標 `0x4CC6A`。
  原版 `GAME.TXT` 首次成功讀取在步數21,820,870，晚於稱號寫入；
  同文的 `GAME.TXT:0xA26` 不能當此固定玩家路徑第一張卡片稱號來源。
- confirmed（副標）：`LABELS.TXT:0x8A9` 的七個原文字節 `Easiest`
  於步數18,648,994 從檔案偏移 `0x800` 起的讀取塊進入 `0x2B0AB`；
  同組原版指令先整理至 `0x2B09B`，再經 `0x249DC` 中間緩衝，
  由 `0E2D:11A5` 於步數18,682,724 寫入 `0x4DF90`。
  目標075的 `0E2D:11CF`／`0D21:00C6`／`0D21:012C` 已將兩個目標 RAM
  位址接到格式化文字、逐字字形和畫布像素；來源至像素的固定路徑因此閉合。
- 兩次冷啟動收據 `goal077-card-load-v4-{a,b}.json` 位元組完全一致，
  各 SHA-256 `580f2f92475a12db9c065a3476e20f4fd315f27521030ac794dedf7aa3b71790`；
  3,200萬步、423筆窄範圍寫入、57筆相關 DOS 讀取，無觀測截斷。
  最終完整 RAM／畫布／索引畫面／色盤 SHA-256 依序為
  `09e9fbf961b8b50115fa0c8b707d4a220cf7f12b3e2a359311073f85786ad109`、
  `08edaac74a54263b8e093010d8cbc97d3f9820c3c151f28d80beded5c5a8a650`、
  `6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae`、
  `762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82`，
  與既有正常玩家終點相同。
- 訂正工具判讀：舊 DOS 實作註解宣稱 `WriteBytes` 繞過寫入監看，但目前隔離版
  `Machine.WriteBytes` 逐位元組呼叫 `Write8`；本次 `WatchWrites` 確實記下
  DOS 緩衝區寫入。檔名與位移仍以 `ReadOp`／`FileOp` 為權威，監看事件與
  讀後 RAM 是獨立交叉核對；不以一項工具註解代替實測。
- 改用 `NAMES.TXT:0x00000C0C` 的既有 `draft` 譯文重建可丟棄 Ebitengine 預覽。
  原文控制 PNG／中文 PNG SHA-256 依序仍為
  `df65ae068485d5c785ce3130fb136bb781f4116e262238788fe10d8f2f0953e5`、
  `65d808bcfdd6c5c2afc3be1c46166429cb113903aaa222c2e14b01b038df8463`；
  安全區外零變更，兩欄變更2,752／1,860點。原型像素相同不代表來源鍵可忽略；
  格式化顯示鍵、執行期背景與游標守門及其他卡片仍未知，規格016維持 DRAFT。
- 重跑：於 Docker 唯讀掛載隔離 dosgolem、合法 DOS 目錄、此專案，僅本機
  `workplace/reports/` 可寫，以目前 UID/GID 及無網路、資源上限執行
  `go run /repo/tools/probe_card_load.go -root /game -inputs /out/goal059-ebiten.inputs.json -out /out/goal077-card-load-v4-a.json`
  （第二次改為 `-b.json`），接著執行
  `tools/check_card_load.py --inputs ... --first ... --second ... --flow-first ... --flow-second ...`。
  預覽入口 `tools/prepare_card_preview.py` 另外必須提供 `--load-first`、
  `--load-second`；完整 JSON、PNG 與原版像素只留本機忽略目錄。

## 2026-09-23：目標078執行期底圖擷取、游標像素與安全回退

- 問題與固定輸入：目標077已閉合第一張卡片的 `NAMES.TXT`／`LABELS.TXT`
  原始位元組至執行期 RAM；目標076卻只用固定終點快照恢復有紋理底圖。
  本輪沿用合法 DOS `OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、`NAMES.TXT`、
  `LABELS.TXT` 的 SHA-256（完整值見[規格016](docs/spec/016-difficulty-card-text-draft.md)），
  九筆真視窗輸入 SHA-256
  `51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc`，
  目標077本機字模預覽 JSON SHA-256
  `c2700c24bec4bccd5d1481660f4bcca3259337c888b0fff772328c892b70d57a`。
  隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，
  研究映像 `colonization-research:20260920-r2` ID
  `sha256:5d99f8754e9f9099b7f263268c485c73043aee1a9d9d29231417ccb5b5da02e1`。
  工具 `tools/probe_card_runtime.go` SHA-256
  `369a31cf5eb07dc84406b6c90fe6bdbacebe0b638ffb1d4cba9b5747dc690f7c`；
  `tools/check_card_runtime.py` SHA-256
  `23c4b7f29c1e98905a72d1f2d31de0f6652b448a6920706ea5de34deb4a3abd3`。
- 位址空間：`0E2D:11CF` 是原版 DOS 真實模式 `CS:IP`；`0x4CC6A`／
  `0x4DF90` 是20-bit 線性 RAM；安全矩形 `(138,44)–(186,51)` 與
  `(146,52)–(180,60)` 為 320×200 原始畫布半開座標；輸出為4倍的
  1280×800 RGBA。原始畫布線性 RAM 起點 `0x2CAE0`，與 VGA 索引輸出
  `0xA0000` 不同；不能以任一者的雜湊代替另一者的游標遮擋驗證。
- confirmed（當次繪製前背景）：dosgolem 的 `WatchReads` 僅於
  `0E2D:11CF` 分別讀 `Discoverer\0`／`Easiest\0` 的線性來源起點時擷取
  完整原版畫布；事件步數29,797,568／29,813,172。稱號／副標候選安全矩形
  背景 SHA-256 各為
  `c5508aad20916fc12bb68638723f6d84799a0ff1744017d71577ec14264cd99b`／
  `d68c4ccc2a32f9b6f4fb2114c033e597b621b8f5981f63c5738f3852529e129b`，
  獨立檢查器從目標075的 `before-first`／`before-second` 原版快照重算一致。
  步數29,865,000的第一個完整輸出幀，原文畫布差分精確符合164／83點及
  bbox `(141,45)–(182,49)`／`(150,53)–(174,58)`，才建立兩欄補片。
- confirmed（輸出守門）：本輪兩次完整正常重播報告位元組相同，SHA-256
  `f8c8ebe95e09c4f8793f6dff2c72fedff9bd251e209ea887aedfb437e86c8fc6`。
  完成前一幀兩欄均 `missing-patch`；自29,865,000起13幀兩欄的完整原文與 NUL、
  視訊模式及開檔脈絡均符合當次擷取條件，且原始索引像素與補片繪製後資料相同，
  才能合成。相同輸入的無觀測控制組，CPU 暫存器、
  flags、完整 RAM、畫布、索引畫面、色盤、ticks、frames 與 cycles 逐項相同；
  正常終點完整 RAM／索引畫面仍為目標077的
  `09e9fbf961b8b50115fa0c8b707d4a220cf7f12b3e2a359311073f85786ad109`／
  `6072d7cf64633f93d2ad86a363ad73cd586f24bdacff51b406a84c52354924ae`。
- confirmed（游標進出）：第一張卡片完成後，原版滑鼠從 `(16,16)` 移到
  `(160,48)`；索引畫面改變160點，bbox `(16,16)–(169,61)`，其中稱號／副標
  安全矩形分別有7／60點交疊，當時索引畫面 SHA-256
  `0230058d7acbdf6cd6db53f40907459cc4096082ee421b6da28714a43e235901`；
  底層畫布仍為
  `08edaac74a54263b8e093010d8cbc97d3f9820c3c151f28d80beded5c5a8a650`。
  不加保守游標矩形時，通用 `overlay.ComposeLayers` 已對兩欄回報
  `frame-mismatch`；加上候選外包 `(112,24)–(212,80)` 後，游標停留25幀
  全數回退原文。移回 `(16,16)` 後，索引畫面與初次可套用幀逐像素相同，
  24幀兩欄重新合成。游標變體與其**同輸入**的無觀測控制組 CPU／RAM／原版
  畫面相同；不同輸入的 RAM 不拿來要求同雜湊。此收據證實本例游標進入
  VGA 索引畫面，不證明任意游標形狀或位置的精確外包。
- 反向條件與限制：在同一輸出幀模擬兩欄缺譯／缺字模，通用合成器返回
  `disabled`／`missing-ink` 且整張圖逐像素等於原文；刻意翻轉一點補片所預期
  的舊畫面，該欄回報 `frame-mismatch`。以一次性唯讀連結把 `NAMES.TXT`
  指向錯誤指紋的 `GAME.TXT`，探針啟動前拒絕未知版本。
  「缺譯」是停用圖層的原型反向對照，**未**驗證正式執行期 TSV 缺鍵讀取。
  輸出的原文／中文 PNG SHA-256 依序為
  `df65ae068485d5c785ce3130fb136bb781f4116e262238788fe10d8f2f0953e5`／
  `0fb76ee5ef2e526cb84543f7ad9917e616e7fdd850c91f4d48d120c991fb4966`；
  `tools/verify_card_preview.py` 逐像素確認兩個安全區外不變、透明字模下回復
  原背景，兩欄各變更2,752／1,860點。這是軟體合成的本機原型輸出，
  不是正式 Ebitengine 玩家視窗截圖；規格016維持 DRAFT，正式八段計數不變。
- 可重播入口：Docker 以目前 UID/GID、無網路、CPU／記憶體／PID 限額，
  唯讀掛載本專案 `/repo`、隔離 dosgolem（在 `/repo/workplace/dosgolem`）、
  合法 DOS 原版 `/game`，只讓已忽略的 `workplace/reports/` 掛至 `/out` 可寫。
  於隔離 dosgolem 模組根執行
  `go build -o /out/goal078-card-runtime-probe /repo/tools/probe_card_runtime.go`；
  以相同 `-root /game -inputs /out/goal059-ebiten.inputs.json -preview /out/goal077-card-preview.json -catalog /repo/text/draft.zh-Hant.tsv`
  分別指定 `-out /out/goal078-card-runtime-a`、`-b`、`-control -out ...-control`、
  `-hover -out ...-hover`、`-hover -control -out ...-hover-control`。
  `tools/check_card_runtime.py` 以五組報告、目前 TSV（`--catalog`）、目標075／077收據及
  `tools/verify_card_preview.py` 的 PNG 驗證報告交叉核對。
  這些 JSON、PNG、字型與研究執行檔均只留本機，不能推送至 GitHub。

## 2026-09-23：目標079第一張難度卡片正式輸出驗收

- 固定輸入：合法 DOS `OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、
  `NAMES.TXT`、`LABELS.TXT` 的完整 SHA-256 見[規格017](docs/spec/017-first-difficulty-card-overlay.md)
  與[規格016](docs/spec/016-difficulty-card-text-draft.md)；九筆真視窗輸入 SHA-256
  `51837a0ed11cfcc316b4e2c9dce7064403cafdd0c1af2efecf59f30319eb5efc`。
  隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，
  研究映像 `colonization-research:20260920-r2`，Ebitengine 2.9.9 映像
  `psychicwar-go-ebiten:latest` ID
  `sha256:083e45e6bc0f01ca46ba0774581572c80a607120431b530de72cdd6ffb36f2f7`；
  Cubic 11 字型 SHA-256
  `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`。
  正式適配器 `tools/live_menu.go` SHA-256
  `fefc92abbd3ceb66b425577551bb1a077f49b8ecca51aaabf658526525597171`。
- 位址空間：`0E2D:11CF`、`0D21:00C6` 是 DOS 實模式 `CS:IP`；
  `0x4CC6A`／`0x4DF90` 是 DOS 20-bit 線性 RAM；`0xC0C`／`0x8A9`
  是原始 TXT 檔案位移；安全矩形是 320×200 邏輯畫布半開座標，輸出畫面
  1280×800。這些基準不可互換。目標075至078已證實來源載入、格式化字串、
  寫像素、當次底圖與游標改變索引畫面，故本輪只將第一張卡片升 READY；
  其餘卡片沒有等量證據，仍屬規格016 DRAFT。
- confirmed（正式接線）：單一 `WatchReads` 分流既有難度文字與新增兩行；
  原始來源及 NUL、開檔 `DIFFICUL.PIK`、模式13h、格式化後的
  `DISCOVERER:`／`Easiest`、164／83點原版畫布差分及各自 bbox 必須吻合，
  才建立有紋理背景補片。`tools/bake_card_fonts.py` SHA-256
  `e3e221d5a0eb499c9311c7ffcab1a088cc0a3d2f448d818887829a4df495feee`
  從唯一真實 TSV 與本機字型產生稱號21px／69×19、副標25px／81×23字模；
  字模只在已忽略的本機目錄。缺鍵時不把其他同文來源當替代鍵。
- confirmed（無頭正常路徑）：兩行各接受一次原始事件，79幀套用；
  中文與無觀測英文控制在4,500萬步的完整 RAM SHA-256 同為
  `6e94f669e9854c3ea306e70c3135ebf4997ff3ed86ec7892be5901701543a45d`，
  CPU、原版索引畫面、色盤、ticks／cycles亦一致。真 Ebitengine／Xvfb
  視窗以九筆實際滑鼠輸入到1億步，中文原跑、重播與英文控制的原版
  CPU／完整 RAM／索引畫面／色盤／虛擬時間相同；畫面新增差異只在兩欄
  安全區，分別2,752／1,860點。`tools/verify_window_prototype.py` 收據
  `workplace/reports/goal079-ebiten-receipt.json` SHA-256
  `cc34a9bf751e20ff2419ec7d407709818978fc4fa5891b5408891b56b707f988`。
- confirmed（反向條件）：`tools/probe_goal079_replays.py` SHA-256
  `678b226c09fc666d2497d8285e063df6879d33b48cac57876ed832f4498a9b84`
  從九筆已驗輸入建立40M步正常與游標變體，以測試用 TSV **真正移除**
  `NAMES.TXT:0x00000C0C` 或複製成同鍵重複列。兩種情況稱號逐幀記錄
  `missing-or-invalid-translation`，
  安全區逐像素等於英文控制，副標仍等於中文組。游標入卡片兩欄各回退25幀，
  移出後恢復；正常三組與游標兩組分別和各自同輸入英文控制原版狀態一致。
  `tools/verify_goal079_replays.py` SHA-256
  `8c8b8d3d7100669d7c5be5cb01d4b4da1c3cd260de2fabf4f1858eb0e710b6c6`
  本機收據 `goal079-replay-receipt.json` SHA-256
  `3486c2a2f60a85ffcf878846cf8c397280368710d852b39789aa0461335fbe70`。
  將固定版本的 `NAMES.TXT` 暫指向錯誤指紋的 `GAME.TXT` 時，正式適配器
  在啟動前拒絕且不生成畫面收據。
  此為已記錄輸入的受控重播，不證明所有滑鼠／鍵盤操作或其餘卡片。
- 真視窗截圖已在**私有**儲存庫原有 `docs/screenshots/difficulty-zh.png`
  位置更新，SHA-256
  `7173203276c778f8a71578e2256497069c0192edf18008ca9c978bcd59ecf054`；
  它含原版像素，不能公開散布。`go test ./...` 首次因沒有 DISPLAY 失敗，
  同一前端在有界 Xvfb 容器重跑通過；Xvfb wrapper 的探測命令在映像內缺失，
  已改用 `xdotool` 並由 trap 清理，屬環境／驗證工具問題，不是原版遊戲缺陷。

## 2026-09-23：目標080難度標題版式量測與可丟棄預覽

- 證據與地址空間：原始 `LABELS.TXT` SHA-256
  `e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`，
  `Choose`／`Difficulty Level` 位於檔案位移 `0x888`／`0x890`；規格014記載的
  來源讀取 `0D3A:0015`、畫布寫入 `0D21:012C` 為 DOS 實模式 `CS:IP`。
  `goal061-difficulty-writes-replay` 的 `choose-before`／`choose-after` 與
  `level-before`／`level-after` 是 320×200 原版畫布快照；
  `goal079-headless-control.difficulty.idx` 是同狀態原版索引畫面，SHA-256
  `e491233e037fa69b0498fc9415688b4491124d0ae687f45b17b46e8bf57b6446`；
  色盤 SHA-256 為
  `762b10807954069aa97266465cff2d72be0d1da568b668a19d15c3a5d0524e82`。
  這些地址、檔案位移與畫布座標不可混用。
- confirmed：兩行原版前後畫布全區差分分別126／284點、半開 bbox
  `(42,16)-(73,24)`／`(23,29)-(92,38)`；安全矩形
  `(39,14)-(76,26)`／`(20,27)-(96,40)` 在穩定索引畫面與 `level-after`
  快照相同。兩行共用四倍畫布 x=230 的墨跡中心，字高32／36px，頂列
  y=64／116；兩行間20px空白。這些是畫布墨跡，不是精確字型基線。
- 工具與原型：隔離 dosgolem 既有收據由提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f` 產生；本輪以
  `colonization-research:20260920-r2` 核對來源，以 `rich2-py:latest`
  及 Pillow 量測 Cubic 11 字型 SHA-256
  `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`；
  既有 `tools/card_preview.go` 編譯本機執行檔在 Ebitengine 2.9.9／
  `psychicwar-go-ebiten:latest` 映像中以有界 Xvfb 合成四組預覽。
  `tools/prepare_heading_preview.py` 固定來源雜湊、原版差分與安全矩形，
  並使用真實印字前的有紋理補片；所有預覽及報告留於已忽略的
  `workplace/reports/goal080-heading-preview/`。
- 候選與驗證：目前正式版24／24px兩個52×22字模沿英文左起點
  `(168,64)`／`(92,116)` 放置；候選 A 用34／38px字級、74×32／82×35
  墨跡置中於 x=230；候選 B 用相同逐欄字級但仍保留原文左起點。
  英文原型與既有英文控制 PNG 逐像素相同；目前版原型在標題安全區與
  既有中文真視窗圖逐像素相同。相對英文控制，A／B／目前版分別變更
  7,402／7,539／6,732個像素，全部在兩個已證實標題安全矩形內。
  本原型不執行原版 CPU，不可當作新的同狀態正常玩家路徑收據。
- 強推論：共同置中比保留左起點更貼近原版兩行共用中心線；視覺偏好仍須
  使用者看四格圖判斷。規格018維持 DRAFT、Issue #28 保持開放，正式
  `tools/live_menu.go` 與現行私有截圖沒有修改。這輪只檢查同頁既有
  完成提示24px、第一張卡片稱號／副標21／25px；沒有推論全畫面固定字級。

## 2026-09-23：目標081第二張難度卡片來源至畫素

- 問題與固定輸入：第一張卡片已正式中文化，但第二張的來源鍵及畫面事件
  尚無證據。合法 DOS `OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、
  `NAMES.TXT`、`LABELS.TXT` SHA-256 見規格016首節；隔離 dosgolem 提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，Go 1.24.13、
  `colonization-research:20260920-r2` image ID
  `sha256:5d99f8754e9f9099b7f263268c485c73043aee1a9d9d29231417ccb5b5da02e1`。
  Ebitengine 2.9.9／Xvfb 使用既有
  `psychicwar-go-ebiten:latest` image ID
  `sha256:083e45e6bc0f01ca46ba0774581572c80a607120431b530de72cdd6ffb36f2f7`；
  獨立驗證用 Pillow 12.3.0。
- confirmed（玩家輸入）：固定九筆真視窗輸入抵達難度頁後，受控
  `move(265,55)` 本身不切卡，`press`／`release` 後藍框移到第二張卡片，
  原版顯示 `EXPLORER:`／`Easy`。另以真 Ebitengine 視窗及 xdotool
  從冷啟動送鍵／滑鼠取得12筆實際輸入；此輸入 SHA-256
  `490584a346fdcbb560fc4c9fb933efa0ac720c0a427fdd90fb31cb3b54ce5922`。
  真視窗中文與同輸入無觀測英文控制在1億步的 CPU 暫存器、完整 RAM、
  原始索引畫面、色盤、ticks／cycles 完全相同；終點索引畫面也與
  4,000萬步受控原文點擊相同。既有中文差異只在舊標題／完成提示安全區
  5,048個輸出像素，第二張卡片本身仍是原文。本機真視窗截圖 SHA-256
  `e878be186529690ae7cbcfd3d2351c8db35adee7bc94885a82afe51428895fec`，
  含原版像素，不入 Git。
- confirmed（檔案位移 → DOS 20-bit 線性 RAM → 原始實模式 `CS:IP`）：
  `NAMES.TXT:0xC18` 的 `Explorer` 隨 DOS `AH=3Fh` 於步16,208,974
  從檔案位移3072起的512-byte區塊讀入 `0x2B01A`；原版 `0E2D:1F76`
  逐字讀 `Explorer\r`，`0E2D:11A1/11A5` 於步16,217,289／292 寫到
  來源 RAM `0x4CC75`。`LABELS.TXT:0x8B2` 的 `Easy` 於步18,648,994
  讀入 `0x2B0B4`；`0E2D:1F76` 逐字讀 `Easy\r`，`0E2D:11A5`
  於步18,684,475 寫到 `0x4DF98`。`tools/probe_card_load.go -second`
  雙次32M步收據位元組相同，SHA-256
  `63cdd7305a8901bca903cbff090e3a9033df29c44d06c17d1a96f8320c813e20`；
  回退預設模式時仍逐位元組重生目標077第一張卡片舊收據，未破壞原探針。
- confirmed（原始 `CS:IP` → 畫布）：第二張卡片點擊後，`0E2D:11CF`
  各三次讀取 `0x4CC75` 的 `Explorer\0` 與 `0x4DF98` 的 `Easy\0`；
  `0D21:00C6` 從局部副本 `0x2A718` 各兩次讀到實際顯示
  `EXPLORER:\0`／`Easy\0`，一共三輪重畫。`0D21:012C`
  每輪對稱號／副標各有156／68次原始畫布值變更寫入，色號0／9。
  精確印字前後快照全畫布差分為134／55點，bbox（含終點）
  `(250,45)–(283,49)`／`(260,53)–(275,58)`；安全候選半開
  `(247,44)–(287,51)`／`(256,52)–(279,60)` 無框外差分，
  各有65種原版底圖色號。終點索引畫面在兩欄安全區與印字後畫布相同。
  這些座標是320×200邏輯像素，字高為5／6原始像素，不是字型基線。
  `tools/probe_second_card_output.go` 雙次40M步收據位元組相同，SHA-256
  `ba7c3e43d047d94797eed53854223071628dd74387cff81ff3e23c51f89423f4`；
  與同輸入無觀測控制的 CPU、完整 RAM、原始索引畫面、色盤、ticks／cycles
  完全相同。第一版探針沿用第一張卡片的緩衝位址而零命中；擴大觀測後
  證實第二張走 `0x2A718`，舊零命中已訂正，不能當成「沒有緩衝」的證據。
- 獨立核對與限制：`tools/check_second_card_output.py` 對固定原版檔案、
  雙次載入／輸出、來源讀取／目標寫入、格式化位元組、文字像素、背景、
  游標僅移入反例、真視窗點擊及英文控制逐項檢查；本機
  `workplace/reports/goal081-second-card/verification.json` SHA-256
  `a1a6c7e19dcb062e4131332802030764bb810ebf26ecece607b67e2fafde6b45`。
  第二張卡片譯稿「探險家／簡單」仍 DRAFT：尚無欄位專屬字模、執行期
  可逆背景與游標回退、真實缺譯／重複鍵反例或正式中文 Ebitengine 驗收。
  本輪不是新 CONFORMED 覆蓋，已顯示中文仍十段。

## 2026-09-23：目標082第二張難度卡片的逐欄覆蓋與正式驗收

- 固定原版檔名及 SHA-256 沿用[規格016](docs/spec/016-difficulty-card-text-draft.md)；
  `NAMES.TXT:0xC18`／`LABELS.TXT:0x8B2` 是檔案位移，`0x4CC75`／
  `0x4DF98`／`0x2A718` 是 DOS 20-bit 線性 RAM，`0E2D:11CF`、
  `0D21:00C6` 與 `0D21:012C` 是原版實模式 CS:IP；不可互換為同一位址。
  工具為隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`、
  Go 1.24.13、Ebitengine 2.9.9、Pillow 12.3.0；研究與視窗映像 ID
  沿用上一節。Cubic 11 字型 SHA-256
  `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`。
- confirmed（欄位幾何）：稱號原版墨跡 `(250,45)–(283,49)` 134點，
  副標 `(260,53)–(275,58)` 55點；原版邏輯像素高5／6，實際基線未知。
  四倍畫布的安全區內，「探險家」以21px得到69×19字模，
  「簡單」以25px得到54×23字模；兩欄上下內距至少4／5px。
  可丟棄 Ebitengine 預覽只變更兩欄2,280／1,233個輸出像素，
  `preview.json` SHA-256
  `6ba90835097e49c7d6cf0d721cc173a67336f1def6f8bc761ff289e71835e693`。
- confirmed（執行期守門）：`tools/probe_card_runtime.go -second` 雙次40M步
  收據位元組相同，SHA-256
  `f38301ef0f954e9fcf5255c31e103fae301fdd4a418fbd2c9f2b02878a9028b5`。
  當次印字前安全區原版畫布與目標081快照一致；原版點擊保持5幀回退，
  移開後30幀套用。游標再移入 `(265,55)` 時副標區原版索引變17點，
  兩欄24幀回退，移開24幀恢復。原版 CPU、完整 RAM、畫布、索引畫面、
  色盤及虛擬時間與同輸入控制相同；缺譯／舊背景反例安全回退。
- confirmed（正式 Ebitengine 真視窗）：由冷啟動實際點擊產生12筆輸入，
  SHA-256 `34d8ec6046830793b2e336ed41a638b533bb0782f5634263d0a1c338adda0f4b`。
  正式中文與同輸入英文控制組原版狀態相同；擷取的視窗 PNG 與輸出幀
  逐像素相同，截圖 SHA-256
  `26b821c3f45c0b558fc7494ff403a9b3b9fcb5832eb13f1ca3af7937bb0349f0`。
  第二張兩欄改變2,280／1,233點；先前欄位差異只在既有核准區，
  其他區域為零。真 TSV 各欄缺鍵／重複鍵各自回退原文，另一欄仍中文；
  游標移入、移開各有24幀回退／恢復。八組變體均與各自控制組原版同狀態，
  `tools/verify_goal082_replays.py` 的本機收據為 PASS。
- 錯版本暫存反例只將 `NAMES.TXT` 複本變更一個位元組，前端啟動前以
  「原版版本不符」退出且無輸出；第一張卡片以新前端重播時，PNG、原版
  索引、色盤、完整 RAM 與目標079逐位元組一致。以上證據僅讓
  [規格019](docs/spec/019-second-difficulty-card-overlay.md)的第二張兩行
  CONFORMED；第三至第五張、標題新版式與全遊戲仍未知。

## 2026-09-23：目標083國家選擇頁的正常路徑與標題來源

- 固定原版檔案名、SHA-256、Go／dosgolem／Ebitengine版本與不同位址空間
  見[規格020](docs/spec/020-nation-heading-overlay.md)。本節的 `0x8D3`／
  `0x8DB` 是 `LABELS.TXT` 檔案位移，`0x4DFB5`／`0x4DFBC`／`0x2A710`
  是 DOS 20-bit 線性 RAM，`0D3A:0015`／`0D21:00C6`／`0D21:012C`
  是原版實模式 CS:IP；畫面座標則是320×200邏輯像素。
- confirmed（玩家路徑）：從目標082真視窗12筆輸入延伸的控制、只移入、
  點擊三組重播，只有點擊 `(55,83)` 開啟 `NATIONS.PIK`。另一組17筆
  真 Ebitengine 視窗輸入也抵達相同國家選擇畫面；該頁目前在正式
  前端仍為英文，同輸入無中文觀測控制組在原版 CPU、完整 RAM、索引
  畫面、色盤、ticks／cycles 全同。真視窗輸入 SHA-256
  `67494a4ea961836e57b3c546638032497c3e019c30f0aa62a70f006dd96ec96d`。
- confirmed（檔案到畫素）：DOS `AH=3Fh` 於步18,077,763把
  `LABELS.TXT` 檔案位移0x800的512 bytes載入線性 `0x2B002`，
  原版從中讀 `Select`／`European Power`，再寫入 `0x4DFB5`／
  `0x4DFBC`。選國畫面原版 `0D3A:0015` 讀來源，`0D21:00C6`
  讀格式化 `0x2A710`，`0D21:012C` 分別改寫120／270個畫布點；
  bbox（含終點）是 `(42,36)–(69,44)`／`(20,49)–(91,57)`。
  載入與輸出雙次收據各自逐位元組一致，SHA-256 分別為
  `77cfef073a94fa8815136b0bf7de67a4a9050f12357ccb2ad990a7336bafcbc2`／
  `af48f6f0177696cb8c7bce12692eee61fe5c3f92212f57f4525fc4566cdf9b74`；
  `tools/check_goal083_nation_evidence.py` 獨立驗證 PASS，收據 SHA-256
  `3fa9ee6b2b1b66b4e745cc7123bedf1aa7a0e3b80c719d82b6b73014743a8017`。
- confirmed（版面限制）：兩行原文四倍墨跡高36px，同以輸出 x=224
  置中。Cubic 11 38px 的繁中字模各為82×35／164×35；可丟棄
  Ebitengine 對照只在兩行各自安全區變更2,610／5,502個輸出像素，
  透明處保留印字前紋理底圖。游標移入兩行安全區會遮住原版索引像素，
  移開後逐位元組恢復；這要求正式覆蓋有逐幀守門，不能單靠靜態圖。
- 受控 F1 鍵於此國家選擇畫面至80M步未新增開檔或可見文字；這不是
  help 全局不可達的證據，且現有前端未提供 F1 鍵轉送。規格020
  保持 DRAFT，候選中文、預覽圖與兩張原版畫面不計入十二段正式命中；
  原始快照、收據與含原版像素的圖片都只留本機 `workplace/`。

## 2026-09-23：目標084國家頁標題執行期守門與正式顯示

- 輸入固定為合法 DOS `OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、
  `LABELS.TXT`、`NAMES.TXT`；各 SHA-256 見[規格020](docs/spec/020-nation-heading-overlay.md)。
  隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，
  Go 1.24.13、Ebitengine 2.9.9、Pillow 12.3.0；Cubic 11 字型
  SHA-256 `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`。
  `0x8D3`／`0x8DB` 是 `LABELS.TXT` 檔案位移，`0x4DFB5`／
  `0x4DFBC`／`0x2A710` 是 DOS 20-bit 線性 RAM，`0D3A:0015`／
  `0D21:00C6`／`0D21:012C` 是原版實模式 CS:IP；安全矩形以
  320×200原始邏輯畫布定義，再換算1280×800輸出畫布。
- confirmed（當次原版背景）：`tools/probe_goal084_nation_runtime.go` 於
  原版 `0D3A:0015` 來源讀取時逐欄保存印字前畫布；安全區原版索引
  SHA-256 分別為
  `7092302ca905ced59a9839c528df5f28a0dc2823618f4f0d99cdd729c6bd5251`／
  `ec7ea1fd43546a53a09172591abbd89269e9b146db2bd591fd98b12f860543a0`。
  原版格式化輸出後變更120／270個畫布點。雙次60M步收據逐位元組
  相同，SHA-256
  `b3ae3b234fe473dc5f9501d903f69b67455d9db3734198a6dfa983871bc75da9`；
  `tools/check_goal084_nation_runtime.py` 獨立驗證 PASS，收據 SHA-256
  `74d6f26df4b66318e732ee606a1c5d0408d91f2019269dc811884c8bd4708022`。
- confirmed（正式真視窗）：16筆原生鍵鼠輸入 SHA-256
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`；
  中文圖 SHA-256
  `2337a9bd9d1a6449103b57f38d5cfb0ebe5e12f8e99102cc9a8fcb0283accb1d`。
  中文與同輸入英文控制組 CPU、完整 RAM、原版索引畫面、色盤、虛擬
  時間一致；中文只在兩個安全矩形改變2,611／5,502個 RGBA 像素。
  真 TSV 兩欄各自缺鍵／重複鍵、游標24幀與滑鼠按住24幀的逐欄
  回退、切場清除、錯版本拒絕，以及舊15個選單／難度檢查點回歸
  均由 `tools/verify_goal084_replays.py` 核對 PASS，收據 SHA-256
  `84da4515020fbccddb2c927deeb99d68261ff1da17d74be62dd20e677d30e678`。
  現行 TSV SHA-256
  `14b2cc51df1d42ccd938d8fab334c0b90b1cf63314746df19d80449c3865f3f1`
  僅與原受測 TSV 的 `notes` 不同；現行 TSV 重烘14欄字模後的同輸入
  PNG、索引、色盤與原正式真視窗逐位元組相同。
- 限制：`confirmed` 僅涵蓋國家頁左側兩行及列出的輸入、狀態、反例。
  原版真正字型 baseline、其他國家卡片、help、後續玩家路徑及完整
  操作仍未知；不得把14段正式顯示當作全遊戲覆蓋率。

## 2026-09-23：目標085第一張國家旗卡紅字的限定來源調查

- 輸入為合法 DOS 版 `OPENING.EXE`、`VICEROY.EXE`、`GAME.TXT`、
  `LABELS.TXT`、`NAMES.TXT`（SHA-256 逐檔見[規格020](docs/spec/020-nation-heading-overlay.md)）；
  `NATIONS.PIK` SHA-256 為
  `bd31e62d7b7652e6903aaea76b1641f11d5333ff6a6da13fd26411c9f080bf54`。
  工具為 Go 1.24.13、隔離 dosgolem 提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f` 的
  `tools/probe_goal085_nation_card.go`（原始碼 SHA-256
  `525273e2aac495c13d5b261ec245b112ad848df7f53ccae3f1d2aa05384ac40c`）；
  位址空間分別是原始 TXT
  檔案位移、DOS 實模式 `CS:IP`、20-bit 線性 RAM 與320×200
  索引畫布，數值不可互換。16筆正常玩家輸入 SHA-256
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`。
- confirmed（畫布事件與同狀態）：兩次各自從冷啟動至50M步的觀測
  JSON 逐位元組相同，SHA-256
  `21010532ff6211a1dfe693f5a3436b4454a3ba98147f9118e4343dff379f9b5e`；
  無觀測控制組的 CPU、完整 RAM、原版索引畫面、色盤、虛擬時間及
  開檔序列相同。原版於步42,222,735開啟 `NATIONS.PIK`；
  上方紅字區在 `0D21:012C`（原版實模式 CS:IP）有144個變更點，
  原始畫布 bbox 為 x141–170、y15–19；下方有172點，bbox
  x135–177、y87–92。兩處另觀測到 `0D3A:0015` 來源讀取與
  `0D21:00C6` 格式化文字讀取。因此兩處當次可見紅字由動態印字
  形成；較早的 `NATIONS.PIK` 圖像繪製仍可能構成其底圖。
- 強推論（尚未閉合載入邊）：兩處格式化緩衝位於線性 RAM
  `0x2A6AE`，來源候選 `0x2A74A`；文字內容與原始檔案位移
  `NAMES.TXT:0x8EA`、`LABELS.TXT:0x8F2` 對應。但此探針只截取
  來源讀取與畫布寫入，尚未追到檔案讀取後寫入上述 RAM 的邊，
  不能把檔案候選升格為 `confirmed` 的正式覆蓋鍵。兩次收據、
  畫布快照與原版像素只在本機 `workplace/reports/goal085-nation-card/`。
  下次須補 DOS 載入邊、相鄰旗卡反例與安全區背景證據，才可
  提出 DRAFT 規格；本輪未更改正式覆蓋或十四段顯示計數。

## 2026-09-23：目標086難度標題 A 版同狀態驗收

- 輸入為[規格018](docs/spec/018-difficulty-heading-layout-draft.md)固定的
  合法 DOS 五檔、隔離 dosgolem 提交、真 TSV 與 Cubic 11 字型；
  Go 1.24.13、Ebitengine 2.9.9、Pillow 12.3.0。原文鍵
  `LABELS.TXT:0x888`／`0x890` 是檔案位移，`0D3A:0015`／
  `0D21:012C` 是原版實模式 CS:IP；安全區在1280×800輸出畫布，
  不能與320×200原始索引畫布座標混用。
- confirmed（版式與未改範圍）：完整十四欄字模與前版逐檔比對，
  只有兩個標題欄變動；「選擇」34px、實際墨跡74×32，左上
  `(193,64)`；「難度」38px、82×35，左上 `(189,116)`，兩行
  均以 x=230 置中。真 Ebitengine 視窗從冷啟動至第一張難度卡，
  游標移離標題後擷取的 PNG 與視窗最終輸出逐像素一致；與舊版
  相同輸入重播，只有兩個安全矩形改變1,450／2,059個輸出像素，
  卡片、完成提示與其他區域保持舊版畫素。
- confirmed（原版同狀態與反例）：真視窗輸入 SHA-256
  `c92890083d2b97bfd7ae4b983a3eaf595a5a0761a69c582272089c5403a5c112`；
  新版、舊版及無覆蓋英文控制組原版 CPU、完整 RAM、索引、色盤、
  ticks／cycles 和開檔序列相同。舊主選單／難度頁十五檢查點的
  原版索引、色盤與終點狀態相同；真視窗第二張卡片與完成區路徑
  仍抵達 `NATIONS.PIK`，游標遮住第二行時僅該欄回退英文，移開
  恢復。同輸入第二張卡片新舊版只在「選擇」安全區改變1,450像素，
  卡片與提示畫素不變；國家頁新舊版最終 PNG、原版索引、色盤及
  完整 RAM 均逐位元組相同。兩欄各自的缺鍵／重複鍵／缺字模／錯字級
  反例均逐欄回退，
  `LABELS.TXT` 暫存單位元組錯版在啟動前拒絕。
- `tools/verify_goal086_heading.py` 本機獨立 PASS 收據 SHA-256
  `83c6668d942034193bec084fcf53fa52ec0a2775ae9c5296a6f663bd7ffb9a2f`；
  收據、原版畫布與全部反例只在已忽略的
  `workplace/reports/goal086-heading/`。驗後才替換私有截圖
  `docs/screenshots/difficulty-zh.png`，SHA-256
  `86b2c08465ed67fc57202e7490a7ac274185c78bf464e2a0e773b120bb196e07`。
  原版 baseline 精確字型仍未知；本 CONFORMED 僅是使用者核定的
  中文版式與限定正常路徑，不是全遊戲或公開素材驗收。
