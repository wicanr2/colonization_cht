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
