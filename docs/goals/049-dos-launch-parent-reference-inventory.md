# 目標 049：DOS 啟動父程序情境（parent context）／引用候選清冊

狀態：completed<br>
日期：2026-09-22<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 035](035-opening-exit-code-launcher-chain.md)、[目標 046](046-opening-click-nonzero-downstream-dataflow.md)、[目標 048](048-viceroy-direct-entry-stall-diagnostic.md)

## 目的

目標 048 已確認直接執行 `VICEROY.EXE` 只會用未建立的 stack context 走入自迴圈，不能再被當作動態文字或
dosgolem 缺口。本輪不執行任何新 direct-entry；只在固定 DOS 目錄中，對根層啟動候選及其對 `OPENING`／
`VICEROY` 的 ASCII 檔名引用建立唯讀、雜湊綁定的清冊，尋找可被後續**正常父程序情境（parent context）**實驗驗證的最小候選。

檔名引用只能證實 bytes 出現，不證實 EXEC、控制流、exit-code 消費、stack setup 或玩家路徑。找不到引用亦只限
已檢查的檔案集合；不得以此排除磁碟／環境、overlay、間接組字或未知啟動器。

## 執行項目

1. 對固定 DOS manifest 內的根層 `.BAT`、`.EXE`、`.COM` 做唯讀 filename、大小、SHA-256、MZ／COM 類型與
   檔名引用清冊；僅保存 metadata、相對檔名、offset、命中數與檔案雜湊，不能輸出或提交原版內容。
2. 對每個包含 `OPENING` 或 `VICEROY` 的固定檔案，記錄引用的字節格式（ASCII、含／不含副檔名、是否有路徑分隔）
   與檔案內 offset；將「靜態引用」與「已觀測 DOS EXEC」明確分開。既有 `OPENING.EXE` 正常路徑的唯一
   `PSOUND.COL` EXEC 不可被覆寫。
3. 若有候選，僅提出下一個必需的正常父程序情境（parent context）證據與失敗即關閉（fail-closed）版本條件；若無候選，明確記錄此
   窄清冊的停止線。不得執行候選、不得建立 batch interpreter、DRAFT／READY、翻譯、字型、覆蓋或 dosgolem 修改。
4. 回填雜湊、位址空間、證據等級、限制與下一個合法前沿；原版唯讀，結果只留在 gitignore
   `workplace/reports/`，文件與 Issue #5 不嵌入原版 bytes。

## 退出條件

- [x] 根層啟動候選清冊、檔案雜湊、搜尋範圍與引用 metadata 可重現，且原版內容不受版控。
- [x] 靜態檔名引用、已觀測 EXEC、正常父程序情境（parent context）與玩家路徑的證據等級明確分離。
- [x] 沒有 direct-entry、batch 假設、DRAFT／READY、覆蓋實作或原版衍生版控內容。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。

## 結果

固定 DOS manifest `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3` 的根層 `.BAT`、`.COM`、
`.EXE` 唯讀 metadata 清冊有 9 個檔案。報告
`workplace/reports/goal049-root-launch-reference-inventory.json` 的 SHA-256 是
`c9a6327b505fffb2046a662365ec886658b72dd9b3245d983a6d8aebeebc36c0`；它只留在 gitignore 的
`workplace/reports/`，不含或不提交原版 bytes。

| 推論等級 | 範圍與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 固定根層共 9 個候選：`CLOSING.EXE`、`COLDEMO.BAT`、`COLONIZE.BAT`、`INSTALL.EXE`、`MAPEDIT.EXE`、`MPSCOPY.EXE`、`OPENING.EXE`、`PKUNZJR.COM`、`VICEROY.EXE`；每檔大小、SHA-256、MZ／非 MZ 類型均在報告。 | 本輪窄範圍清冊可由固定輸入與報告雜湊重現。 |
| confirmed | 精確大寫 ASCII `OPENING` 只在 `OPENING.EXE` 出現 5 次（offset `49145, 49153, 49161, 49178, 49222`）；每次均無副檔名、無緊鄰路徑分隔。精確大寫 ASCII `VICEROY` 只在 `VICEROY.EXE` 出現 4 次（offset `104785, 130260, 130916, 130931`）；第一筆有 `.EXE` 副檔名，其餘無副檔名，皆無緊鄰路徑分隔。 | 根層沒有**不同檔名的第三方候選**包含任一 token；這只是固定檔案集合中的靜態引用清冊。 |
| confirmed | 既有 `OPENING.EXE` 正常冷啟動唯一觀測到的 DOS EXEC 是 `PSOUND.COL`；目標 035 的兩個批次檔也只有靜態最終 `opening` 命令詞，未形成可觀測的 DOS shell 重播。 | 靜態 token 命中不是 EXEC、控制流、exit-code 消費、stack setup、父程序情境或正常玩家路徑證據。 |
| unknown | 子目錄候選、動態組字、環境／磁碟啟動器、實際父程序與 stack 建立方式，以及任何 `VICEROY.EXE` 正常轉交。 | 本輪不把「根層無第三方 token」外推為不存在 launcher；沒有 DRAFT／READY、程式修改或翻譯／覆蓋資格。 |

本輪在無網路、UID/GID 1000:1000 的一次性 Docker 容器中完成，原版 `/game` 唯讀。後續若繼續探查，只能以
新的固定範圍 metadata 證據建立候選；不得執行候選、建立 batch interpreter，或將 direct-entry 代替正常路徑。
