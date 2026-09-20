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
