# 目標 050：DOS 子目錄啟動引用候選清冊

狀態：completed<br>
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

- [x] 子目錄候選清冊、檔案雜湊、搜尋範圍與引用 metadata 可重現，且原版內容不受版控。
- [x] 根層與子目錄的靜態引用、已觀測 EXEC、父程序情境與玩家路徑的證據等級明確分離。
- [x] 沒有執行候選、batch 假設、DRAFT／READY、翻譯、字型、覆蓋實作或原版衍生版控內容。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。

## 結果

固定 DOS manifest `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3` 的實際根目錄是
`SMColoni/COLONIZE`。以此根目錄重跑後，至少一層子目錄中的 `.BAT`、`.COM`、`.EXE` 候選數為 **0**；因此
`OPENING`／`VICEROY` 命中數也都是 0。報告
`workplace/reports/goal050-subdirectory-launch-reference-inventory.json` 的 SHA-256 是
`30f15c4490e6728f77783e38c5ff1c4c8d131df413ea899625ef274fc72d4836`，只留在 gitignore 的
`workplace/reports/`，不含或不提交原版 bytes。

| 推論等級 | 範圍與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 正確 `/game` 唯讀掛載為固定 `SMColoni/COLONIZE` 根目錄；schema `colonization-goal050-subdirectory-launch-reference-inventory/1` 記錄「排除根層」的 `.BAT`／`.COM`／`.EXE` 範圍，entries 與兩個 token 的命中數皆為 0。 | 在此固定版本與副檔名集合，沒有子目錄靜態候選。 |
| confirmed（範圍修正） | 初次探針誤以 `SMColoni` 父目錄作 `/game`，只重複枚舉既有 `COLONIZE/` 根層的 9 檔。該結果未寫入文件、Git 或 Issue 證據，已由正確根目錄 report 覆蓋。 | 不採用父目錄結果；第 049 與第 050 的範圍不重疊。 |
| confirmed | 已觀測的正常 `OPENING.EXE` 路徑唯一 DOS EXEC 仍是 `PSOUND.COL`；目標 049 的根層靜態命中與本輪 zero-entry 都不新增 EXEC 事件。 | 靜態清冊不能作為父程序情境（parent context）、stack setup 或正常玩家路徑證據。 |
| unknown | 非此副檔名的子目錄資料、動態組字、環境／磁碟啟動器、實際 parent、`VICEROY.EXE` 正常轉交與文字路徑。 | 不以 zero-entry 外推不存在 launcher；不執行候選、不建立 batch interpreter、DRAFT／READY、翻譯、覆蓋或 dosgolem 修改。 |

本輪在無網路、UID/GID 1000:1000 的一次性 Docker 容器中完成，原版 `/game` 唯讀。
