# 目標 022：MCB 修正後的 PSOUND 正常路徑與首個可見檢查點

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置證據：[CONFORMED 規格 005](../spec/005-colonization-registered-process-mcb-importer-conformed.md)

## 目的

在已註冊多行程 MCB importer 驗收後，從固定的 DOS `OPENING.EXE` 冷啟動正常路徑建立第 2,000,000
指令的可重載檢查點，並以該檢查點向後觀測實際控制流與畫面。這輪只回答：MCB 修正後何時首次出現可見
輸出、可觀測文字輸出或 `VICEROY.EXE` 轉交；若仍受阻，將最小缺口縮小為可驗證證據。

固定輸入為 `OPENING.EXE`，SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；探針使用隔離
`workplace/dosgolem` 的 commit `1435f175e785ea096a9268cd1021a4222300bd43` 與
`colonization-research:20260920-r2`。所有原版檔與畫面收據只留在 gitignore 的 `workplace/`。

## 執行項目

1. 以 `-sbpro` 從固定原版冷啟動跑至絕對第 2,000,000 指令，保存 state v3 檢查點與摘要收據，驗證它可被
   `cmd/probe -load-state` 重載。
2. 從同一檢查點分段續跑至絕對第 5,000,000、10,000,000 與 20,000,000 指令；使用畫面雜湊、CS 段變更、
   檔案服務與必要的最後軌跡，記錄第一個可見畫面、文字輸出、程式轉交或可重現停滯點。
3. 若已有可見輸出，保留正常冷啟動的本地畫面／控制流收據，僅將雜湊、定位和結果寫入受版控研究文件；
   不把原版像素或素材提交到 GitHub。
4. 若仍無可見輸出，將下一個最小 simulator 缺口以 `confirmed`、`強推論`、`假說` 或 `未知` 分級；只有證據
   足以定義行為時才建立 DRAFT 規格，這輪不實作新的 dosgolem 行為。
5. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、工作清單、README 與 Issue #24，完成 Git 推送及
   Docker／權利邊界自檢。

## 停止線

- 不用直接跳轉、寫記憶體、偽造畫面、DOSBox 收據或未受控鍵盤輸入取代正常冷啟動證據。
- 不因未在 20,000,000 指令內出畫面而推論完整遊戲故障；只報告這個有界窗口的觀察。
- 不修改原版、遊戲專屬資料或 dosgolem；若發現可能缺口，只產生證據與必要的 DRAFT，不跳過規格閘門。

## 退出條件

- [x] 第 2,000,000 指令 state v3 可從原版冷啟動生成並由獨立 `-load-state` 收據成功重載。
- [x] 同一初始狀態的 5M／10M／20M 分段續跑有畫面與控制流觀測收據，且所有結論標示證據等級。
- [x] 首個可見輸出已定位：2.70M 仍為零、2.75M 為 18,445 個非零 mode 13h 像素；寫入端可回查為
  `0557:0090`，未把畫面語意、文字或 `VICEROY.EXE` 轉交當成已證實。
- [x] 文件、Issue #24、Git、Docker 清理與原版素材權利邊界一致。
