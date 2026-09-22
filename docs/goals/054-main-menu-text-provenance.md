# 目標 054：主選單文字輸出來源

狀態：completed<br>
日期：2026-09-22<br>
Issue：[#5](https://github.com/wicanr2/colonization_cht/issues/5)，後續規格 [#6](https://github.com/wicanr2/colonization_cht/issues/6)

## 前置條件

[目標 053](053-mouse-and-gameplay-route-replan.md) 已取得正常主選單及滑鼠進入難度畫面，
工具入口為 `tools/probe_gameplay_route.py`。不得使用缺 `-g` 的舊開場狀態替代；
DOS v3 快照只留歷史，正式研究從現行執行器冷啟動重生 v4。

## 最小垂直切片

1. 以原版主選單上一則可見文字為對象，確認 `GAME.TXT`、字型資產或其他實際來源；
   檔名及可見文字只能作搜尋線索，不能直接當動態輸出證據。
2. 固定原版雜湊與執行器版本，從正常冷啟動縮小該文字出現的區間，追蹤來源指標、
   字串長度／終止、印字呼叫、繪製座標及可見存續。若涉及反組譯，使用既有 IDA Pro 9.4。
3. 至少用兩次同起點重播確認輸出事件與畫面對應；保留原始段:位移、位元組、
   來源位置、證據等級，不將其他遊戲專用字型 hook 的零次命中當成沒有文字。
4. 交付 Issue #6 的來源鍵 DRAFT：版本鍵、呼叫情境、文字來源、幾何、命中與不命中條件。
   如果目標其實為烘入圖片，轉交 #8，並從已驗證難度畫面選另一則輸出候選，不猜補。

## 退出與停止條件

一則實際可見文字有「來源 → 印字事件 → 畫面」的最小充分證據，即停止逆向，
轉入 DRAFT 審查與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26) 的中文原型。
若缺通用觀測能力，記錄一個具體缺口及規格，不再開啟整個開場或音效內部研究。

本輪不翻譯全遊戲、不修改原版檔案、不定案字型／術語／發布方式；原型呈現後才請使用者作選擇。
未有真實輸出事件前，不得將任何來源鍵或覆蓋條件升為 READY。

## 本輪平行分工

使用者已授權子代理協作。翻譯支線只產生主選單／開局的來源定位與繁中草稿；
工程支線查核既有攔截及輸出能力；字型支線查核本機字型與授權、供可丟棄原型使用。
主代理負責輸出事件證據、規格審查、整合及正常路徑驗證。子代理不自行定案產品選擇，
也不將草稿翻譯或未證實攔截鍵升格為正式規格。

## 結果與重跑入口

confirmed：`GAME.TXT` 位移 `0x1B0`、25 bytes 對應執行期 `6F16:00DF`；
`937C:0538` 在步數 21,384,086 進入，21,402,955 返回 `937C:1D50`。
離屏畫布 `2CAE:0000` 中 180 個像素改為色號 254，邊界（含端點）
`[86,107]..[176,112]`；滑鼠正常移到 `(16,16)` 後全部存續到最終畫面。
兩次冷啟動的完整記憶體、文字前後記憶體、索引畫面、色盤及事件一致。
這已達本輪退出條件；Issue #6 的三種輸出情境仍未完成，不擴大本結論。

以下在專案根目錄執行；所有掛載來源須已存在。輸出僅留本機 `workplace/reports/`。

```sh
test -d workplace/dosgolem && test -d workplace/gocache &&
test -d workplace/reports && test -d tools &&
test -d "Sid Meier's Colonization (1994)/SMColoni/COLONIZE" &&
timeout 180 docker run --rm --network none --memory 2g --cpus 2 --pids-limit 256 \
  --user "$(id -u):$(id -g)" -e GOCACHE=/cache \
  -v "$PWD/workplace/dosgolem:/dosgolem:ro" \
  -v "$PWD/workplace/gocache:/cache" -v "$PWD/workplace/reports:/out" \
  -v "$PWD/tools:/tools:ro" \
  -v "$PWD/Sid Meier's Colonization (1994)/SMColoni/COLONIZE:/game:ro" \
  colonization-research:20260920-r2 python3 /tools/probe_text.py
```

- [tools/probe_text.py](../../tools/probe_text.py)：固定隔離提交、兩次冷啟動與一致性收據。
- [tools/trace_text.go](../../tools/trace_text.go)：研究專用輸入序列及印字前後觀測。
- [tools/analyze_text_capture.py](../../tools/analyze_text_capture.py)：容器 `/out` 畫布差異報告。
- [tools/ida_text_export.py](../../tools/ida_text_export.py)：IDA 9.4 原始段位移、bytes、交叉參照與 `.i64` 保存。
- 完整輸入／輸出雜湊、位址基準及 IDA 重跑命令見 [研究紀錄](../../RESEARCH-LOG.md)。
- 後續為 [規格 009 草案](../spec/009-first-text-overlay-draft.md) 與 [目標 055](055-first-text-prototype.md)。
