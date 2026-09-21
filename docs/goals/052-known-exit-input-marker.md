# 目標 052：已知退出輸入座標標記

狀態：completed<br>
日期：2026-09-22<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 046](046-opening-click-nonzero-downstream-dataflow.md)、[目標 051](051-opening-frame-coordinate-grid.md)

## 目的

目標 046 已在固定完整開場 state 確認單次 `(160,100)` 左鍵走入非文字退出；目標 051 已建立本機座標格，
但沒有在圖片上指出這筆已排除輸入。本輪只在同一張本機座標格建立一個可丟棄的紅色標記，協助使用者選擇下一個
正常操作時避開已知退出路徑。

標記只表示「此固定 state 的既有左鍵測得非文字退出」，不是按鈕、控制項、玩家路徑、文字或翻譯證據；不藉此
推斷任何其他位置的語意。

## 執行項目

1. 驗證目標 051 本機 PNG／metadata 與目標 046 固定 `(160,100)` 左鍵退出收據的雜湊、state 與 dosgolem commit
   可回查；不符即 skip，不重建遊戲或猜測套用。
2. 在無網路、唯讀 reports input 的 Docker 容器中，將 logical `(160,100)` 依目標 051 的 margin／scale 映射到
   本機 PNG；產生 gitignore 的標記 PNG、metadata 與輸入／輸出 SHA-256。
3. 以 `view_image` 檢視本機標記是否落在座標 `(160,100)`；只驗證幾何，不注入新的滑鼠／鍵盤輸入、不 OCR、不命名
   任何控制項或畫面語意。
4. 回填 marker 的 confirmed 限制、正常玩家路徑仍未知與下一個需使用者決定的操作；不得建立 DRAFT／READY、
   翻譯、字型、覆蓋或 dosgolem 修改。

## 退出條件

- [x] 已知退出座標、來源／輸出 metadata、雜湊與本機 marker PNG 可重現，且像素不受 Git 追蹤。
- [x] marker、已知退出結果、控制項語意、正常玩家路徑與動態文字證據明確分離。
- [x] 沒有新輸入、OCR、DRAFT／READY、翻譯、字型、覆蓋實作或 dosgolem 修改。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。

## 結果

本機 marker PNG 是 `workplace/reports/goal052-known-exit-marker-x2.png`，SHA-256
`862875cb3d253f11fc83689f11bcbf450ff190ce77ad57df9dd5c85b9ca73693`；metadata 是
`workplace/reports/goal052-known-exit-marker.json`，SHA-256
`76cdbca266cb2ab8c16acf9322a3c90b072f52066edaefb2be882afdfabea071`。兩者只留在 gitignore 的
`workplace/reports/`，不提交原版或衍生像素。

| 推論等級 | 範圍與觀測 | 結論 |
| --- | --- | --- |
| confirmed | metadata 綁定目標 051 grid PNG／metadata SHA-256 `24abdb08a2d7c72c22f80e19999fd1638cb345e447ee84f928e822571a412f7c`／`aa81ec34a37cfda4c16f5f12e8f4cc83bbc85f90014c164e54a71e4997097a56`，以及相同 manifest、dosgolem commit、#5,465,772 state、indexed frame、palette、state 雜湊。 | marker 的輸入版本與 base grid 可回查，版本不符時不套用。 |
| confirmed | mapping 是 `x=32 + logical_x×2`、`y=logical_y×2`；logical `(160,100)` 得輸出 pixel `(352,200)`。產出紅色 3-pixel thick cross（half-length 14），`view_image` 檢視與 metadata 均確認其幾何。 | 畫面上唯一的紅 marker 是既有 `(160,100)` 左鍵位置，不是新輸入。 |
| confirmed（限制） | 目標 046 已獨立確認此固定 state 的單次左鍵是非文字退出；本輪只重建 grid 並標示此座標，沒有向 dosgolem 發送輸入。 | marker 只表示既有退出結果，不能命名按鈕、控制項、文字或正常玩家路徑。 |
| unknown | 其他座標的操作意圖、控制語意、輸入結果、`VICEROY.EXE` 轉交與動態文字輸出。 | 使用者需先依本機畫面選擇下一個正常操作；不得盲掃或 agent 自行挑選座標。 |

本輪產圖器是一次性本機工具，未加入儲存庫；所有容器無網路、原版／reports input 唯讀、以 UID/GID 1000:1000 執行。
