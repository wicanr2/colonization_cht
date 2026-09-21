# 目標 052：已知退出輸入座標標記

狀態：in_progress<br>
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

- [ ] 已知退出座標、來源／輸出 metadata、雜湊與本機 marker PNG 可重現，且像素不受 Git 追蹤。
- [ ] marker、已知退出結果、控制項語意、正常玩家路徑與動態文字證據明確分離。
- [ ] 沒有新輸入、OCR、DRAFT／READY、翻譯、字型、覆蓋實作或 dosgolem 修改。
- [ ] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
