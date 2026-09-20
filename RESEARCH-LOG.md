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
