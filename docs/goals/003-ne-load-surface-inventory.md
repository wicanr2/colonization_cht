# 目標 003：固定 Windows NE 載入面清冊

狀態：completed
日期：2026-09-20
對應 Issue：[ #19 ](https://github.com/wicanr2/colonization_cht/issues/19)

## 目的

在不實作 Windows 3.x、也不改變 Issue #18 的使用者決策前提下，為固定雜湊的
`COLONIZE.EXE` 建立可重跑的靜態載入面證據：NE header、區段、匯入模組、import
relocation 與資源表的中繼資料。這可量化「擴充 dosgolem」選項的已知表面，並防止
把 DOS stub 的七道指令誤當作遊戲所需能力。

## 範圍

1. 唯讀解析 MZ→NE header 指標、NE table offset、區段表及 relocation 資料。
2. 清冊匯入模組與 ordinal／名稱匯入型態；僅記錄系統匯入中繼資料。
3. 清冊資源 type／數量／檔案範圍，不解出資源內容、文字或像素。
4. 使用獨立 `file` 分類與原始 header bytes 交叉核對格式與 NE 偏移。

## 排除項目

- 不把靜態 import 表推論為某 API 已在遊戲玩家流程中呼叫。
- 不實作 NE loader、Windows 3.x 核心、GDI、USER、音訊或遊戲程式。
- 不擷取原版資源、文字、字型、圖像或可散布的衍生內容。

## 可重現證據

輸入是 `SMCol3x/MPS/COLWIN/COLONIZE.EXE`，SHA-256 為
`ae7d9149f056766a534fe8f0006c9512aac1e1004e9776ab3cca818e4833b650`。使用
`colonization-research:20260920-r2` 的唯讀原始輸入掛載與
`retro-runtime-study-tools:1` 的 Python 執行環境，執行：

```text
python3 tools/ne_inventory.py --exe <COLONIZE.EXE> --output <gitignore workplace report>
```

輸出位置為 gitignore 的 `workplace/reports/ne-inventory-colwin-ne-20260920.json`；工具來源是
[`tools/ne_inventory.py`](../../tools/ne_inventory.py)。所有位址均是檔案偏移；NE table offset
先以 NE header 為基準解析，再輸出為絕對檔案偏移。

## 結果

| 項目 | 結果 | 等級 |
|---|---|---|
| MZ→NE 定位 | `MZ.e_lfanew = 0x250`；原始 bytes 為 `50 02 00 00`，`0x250` 處為 `NE`。 | confirmed |
| 交叉格式識別 | `file` 回報 `MS-DOS executable, NE for MS Windows 3.x (3.10) (EXE)`。 | confirmed |
| NE 基本結構 | linker 6.1、33 個區段、18 個帶 relocation 的區段、7 個 module reference。 | confirmed |
| 匯入模組 | `WING`、`COMMDLG`、`GDI`、`KERNEL`、`MMSYSTEM`、`USER`、`WIN87EM`。 | confirmed |
| 匯入型態 | 176 個 imported ordinal target；未發現 import-by-name target。 | confirmed（僅指 relocation table） |
| relocation／資源 | 共 25,825 筆 relocation；42 個資源項目，type ordinal 為 1、2、3、4、5、12、14。 | confirmed |
| 遊戲實際執行 API、視窗／GDI／文字路徑 | 靜態清冊沒有執行期 trace，無法證實。 | unknown |

完整方法與結果見 [`RESEARCH-LOG.md`](../../RESEARCH-LOG.md)。

## 退出條件

- [x] 固定輸入雜湊與檔案偏移位址空間已記錄。
- [x] Docker 可重跑的 NE 清冊工具已加入版控，報告只寫到 gitignore 工作區。
- [x] NE 格式與 header 偏移已由 `file` 與原始 bytes 交叉核對。
- [x] 已明列靜態證據無法回答的執行期問題，沒有把清冊升格為 Windows 支援宣稱。
