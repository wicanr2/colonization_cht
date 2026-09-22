# 目前脈絡

更新：2026-09-22；本檔只記目前真相，逐輪證據見 [RESEARCH-LOG.md](RESEARCH-LOG.md)，歷程見 [WORKLOG.md](WORKLOG.md)。

## 已確認決定

- 使用者已選定本機 `Sid Meier's Colonization (1994)/SMColoni/` 的合法 DOS 輸入作為正式研究目標。
- 中文化是 dosgolem 輸出階段的繁體中文覆蓋，不是 remake；不修改原版程式、資料、規則或存檔。
- 儲存庫 `wicanr2/colonization_cht` 維持 PRIVATE；原版素材、畫面、快照只保留本機。
- dosgolem 只修改 `workplace/dosgolem` 獨立副本；`upstream` 推送位址保持 `DISABLED`。

## 目前狀態表

| 項目 | 狀態與證據 |
|---|---|
| 正常 DOS 啟動 | confirmed：原版 `COLONIZE.BAT` 使用 `OPENING.EXE -g`；已轉交 `VICEROY.EXE` 並顯示主選單。 |
| 主選單滑鼠 | confirmed：正常冷啟動後點選「新世界」可到難度畫面，不是 direct-entry 或記憶體改寫。 |
| 快照重播 | confirmed：連續路徑與安全選單快照續跑的索引畫面及色盤一致；無輸入留在主選單。 |
| 平台修正 | BIOS 馬達倒數、`int33 AX=0014` 回呼交換、DOS v4 滑鼠狀態與不安全回呼保存拒絕；規格 006–008。 |
| 動態文字 | 尚未定位本遊戲印字常式與來源鍵；已到達可觀測的真實選單，下一輪為目標 054／Issue #5。 |
| 靜態文字 | 開場海洋標籤等候選仍缺完整來源／可逆背景證據；Issue #8 開放，不阻擋動態路徑。 |
| 中文顯示 | 未實作；Issue #26 為第一則真實訊息的垂直切片。 |
| 完整可玩／正式發行 | 未驗證、未發布；本輪僅驗證至難度選擇。 |

## 工具與重播入口

- 研究映像：`colonization-research:20260920-r2`；分析、建置、測試、遊戲執行均在 Docker 內。
- 隔離 dosgolem 程式提交：`22664265ea7d55ea8706448149908c79d3f0897b`。
- 累積補丁：[tools/dosgolem-platform-fixes.patch](tools/dosgolem-platform-fixes.patch)，
  基底為 `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`，包含先前 SBPro／MCB 修正及本輪修正。
- [目標 053](docs/goals/053-mouse-and-gameplay-route-replan.md) 保存 Docker 重播命令、版本與驗收結果。
  `tools/probe_gameplay_route.py` 建立新的 DOS v4 選單快照。
- 舊 v3 快照不能交給現行程式猜補；歷史對照工具 `tools/probe_opening_mouse.py` 在容器暫存目錄
  建置原始 `1435f17`，不切換目前工作樹、不修改原快照。
- `go test ./...` 已通過；不代表所有 DOS 遊戲或任意指令邊界快照全面相容。

## 訂正與證據限制

先前缺少 `-g` 的開場點擊只證明該啟動情境下的退出，不代表主選單操作。
目標 053 固定舊狀態的三個不同座標有相同控制流；不能外推成所有畫面不依賴座標。
撤回「由使用者猜下一個座標」的門檻。舊觀測保留在目標 034–052 與研究紀錄，不再充當目前阻塞點。

DOSBox-X 僅提供啟動鏈及畫面類別的輔助基準，正式收據由 dosgolem 重生。
主選單沒有命中其他遊戲專用的字型 hook，不代表沒有動態文字。
未實作的 DOS 日期／記憶體策略服務另有紀錄，但本輪沒有證據顯示它們阻擋已驗證路徑。

## 下一閘門

執行 [目標 054](docs/goals/054-main-menu-text-provenance.md)：一則可見選單文字的
來源 → 印字事件 → 畫面證據，接到 Issue #6 的訊息鍵 DRAFT，再進入 Issue #26 中文原型。
達到最小充分證據即停止逆向，不重開整個開場研究。

字型、術語、完成範圍與授權／公開方式仍需使用者依原型及成果決定，不能代為定案。
