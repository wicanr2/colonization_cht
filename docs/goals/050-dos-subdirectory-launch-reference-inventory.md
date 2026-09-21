# 目標 050：DOS 子目錄啟動引用候選清冊

狀態：in_progress<br>
日期：2026-09-22<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 035](035-opening-exit-code-launcher-chain.md)、[目標 048](048-viceroy-direct-entry-stall-diagnostic.md)、[目標 049](049-dos-launch-parent-reference-inventory.md)

## 目的

目標 049 已以固定根層 9 個 `.BAT`、`.COM`、`.EXE` 釘住靜態清冊，未找到不同根層候選對 `OPENING` 或
`VICEROY` 的 ASCII 引用。這不排除子目錄、動態組字、環境或磁碟啟動器。本輪只將範圍可重現地擴到固定 DOS
目錄中**至少一層子目錄**的 `.BAT`、`.COM`、`.EXE`，以尋找後續正常父程序情境（parent context）研究的
靜態候選；不把 filename token 誤當 DOS EXEC、控制流、stack setup 或玩家路徑。

## 執行項目

1. 對固定 DOS manifest 內、相對路徑含至少一個目錄分隔的 `.BAT`、`.COM`、`.EXE` 做唯讀 filename、大小、
   SHA-256、MZ／非 MZ 類型與精確大寫 ASCII `OPENING`／`VICEROY` 的 metadata 清冊；只保存相對檔名、
   雜湊、offset、編碼、緊鄰副檔名與路徑分隔旗標，不能輸出或提交原版 bytes。
2. 將目標 049 的根層範圍與本輪子目錄範圍嚴格分開；記錄靜態命中、既有已觀測 `PSOUND.COL` DOS EXEC、
   正常父程序情境與玩家路徑各自的證據等級。
3. 若出現不同檔名候選，只提出下一個最小、雜湊綁定且正常路徑優先的證據需求；不得執行候選、不得建立
   batch interpreter、不得以 direct-entry 或靜態引用推定語意。
4. 回填報告雜湊、範圍、結果、限制與下一個合法前沿；所有結果只留在 gitignore 的 `workplace/reports/`。

## 退出條件

- [ ] 子目錄候選清冊、檔案雜湊、搜尋範圍與引用 metadata 可重現，且原版內容不受版控。
- [ ] 根層與子目錄的靜態引用、已觀測 EXEC、父程序情境與玩家路徑的證據等級明確分離。
- [ ] 沒有執行候選、batch 假設、DRAFT／READY、翻譯、字型、覆蓋實作或原版衍生版控內容。
- [ ] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
