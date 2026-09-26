# 驗證矩陣

由 `tools/verification_matrix.py` 依 `tools/verification-matrix.json` 產生；不要手改。收據只在已忽略的 `workplace/reports/`，本頁只列雜湊與數量。

- dosgolem：`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`
- 原版輸入（各收據記錄的檔案雜湊合併，同名檔衝突 0 個）：`GAME.TXT` `67a6b5e22d1a…`、`LABELS.TXT` `e4af0da201eb…`、`NAMES.TXT` `4bf5ba261f71…`、`OPENING.EXE` `3c08c4af3a70…`、`VICEROY.EXE` `a17ed64c2767…`
- 結果：PASS 14、SKIP 0、FAIL 0；原版輸入衝突 0；動態與靜態四類收據齊備：是

原版基線指英文控制收據的原版 RAM／VGA 索引／色盤；中文模式必須與它相同，差異只在中文安全區（由各檢查器核對）。

| 列 | 路徑 | 規格 | 檢查器 | 結果 | 基線 | 中文 | 英文 | 負例 | GUI 輸入 | 畫面格式 | 已知差異 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 遊戲選項標題與八列 | 動態 | 030、031 | `check_goal134_window.py` | PASS | 3 | 3 | 3 | 6 | 1 | 1280x800 RGB | GUI 截圖與重播可有一幀延遲，只比安全區 |
| 英格蘭首次介紹兩頁 | 動態 | 025 | `check_goal135_window.py` | PASS | 3 | 3 | 3 | 2 | 1 | 1280x800 RGB | — |
| 法國、西班牙、荷蘭首次介紹 | 動態 | 025 | `check_goal136_window.py` | PASS | 9 | 9 | 9 | 2 | 3 | 1280x800 RGB | — |
| 其他國家遊戲選項、快捷鍵與讀檔路徑 | 動態 | 031 | `check_goal137_window.py` | PASS | 5 | 5 | 5 | 0 | 6 | 1280x800 RGB | 只驗英格蘭存檔一例；本列無專屬負例，回退由目標134負例涵蓋 |
| 退休確認框三欄 | 動態 | 028 | `check_goal138_window.py` | PASS | 2 | 2 | 2 | 2 | 1 | 1280x800 RGB | — |
| 第三張難度卡 | 動態 | 016 | `check_goal139_window.py` | PASS | 4 | 4 | 4 | 3 | 1 | 1280x800 RGB | — |
| 其餘三張國家旗卡 | 動態 | 022 | `check_goal140_window.py` | PASS | 6 | 6 | 6 | 3 | 1 | 1280x800 RGB | — |
| 十張開場字幕 | 動態 | 026、029 | `check_goal141_window.py` | PASS | 1 | 1 | 1 | 4 | 1 | 1280x800 RGB | 介紹頁後按鍵會讓原版跳過第五張起的字幕 |
| 首則教學提示 | 動態 | 026 | `check_goal142_window.py` | PASS | 1 | 1 | 1 | 3 | 1 | 1280x800 RGB | GUI 截圖一幀延遲，只比安全區 |
| 海上選單列、回合訊息與狀態欄 | 動態 | 032 | `check_goal143_window.py` | PASS | 2 | 2 | 2 | 4 | 1 | 1280x800 RGB | — |
| 全部動態欄位同時開：Explorer 無跳過路徑與 Discoverer 路徑 | 動態 | 033 | `check_goal150_window.py` | PASS | 2 | 2 | 2 | 1 | 0 | 1280x800 RGB | 主選單第一列在錄製路徑因游標遮擋保留原文；輸入來自 tools/goal150-full-path.inputs.json 與目標142 現場輸入 |
| 規格033 資料模型：每則事件只歸一組鍵 | 動態 | 033 | `check_goal144_text_model.py` | PASS | 0 | 0 | 0 | 0 | 0 | — | 探針收據，不含中文畫面 |
| 開場製作名單七個職稱橫幅 | 靜態 | 034 | `check_goal151_window.py` | PASS | 1 | 1 | 1 | 4 | 1 | 1280x800 RGB | 人名橫幅 GUI 截圖與重播有一幀動畫差，該畫面不套用 |
| 全面回歸六點（主選單至旗卡、@BUILD1、遊戲選項、英格蘭介紹） | 兩者 | — | `check_regression.py` | PASS | 0 | 6 | 0 | 0 | 0 | 1280x800 RGB | 基準為目標138收據；候選為目前前端 |

## 未驗範圍

- 國王接見畫面（0D21:00C6 動態印字）
- GAME 下拉選單
- Loading Game... 訊息
- 主選單版本字串
- 首則以外的 help（23 則）
- 海上以外的遊戲畫面：殖民地、歐洲港口、報告、外交、百科
- 開場以外的靜態圖文字（清冊其餘五項依決定不覆蓋）
- 按鍵跳過開場時職稱橫幅不出現（覆蓋不觸發，非缺陷）
- 整局遊玩、存讀檔、音訊與正式玩家節奏

## 重產收據

各列收據由表中 `regenerate` 腳本在 Docker 內重產（每列數十分鐘到數小時）；本矩陣只重跑檢查器，不重跑模擬。完整清單見 JSON 報告。
