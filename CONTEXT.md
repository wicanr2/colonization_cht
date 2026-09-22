# 目前脈絡

更新：2026-09-22；本檔只記目前真相，逐輪證據見 [RESEARCH-LOG.md](RESEARCH-LOG.md)，歷程見 [WORKLOG.md](WORKLOG.md)。

## 已確認決定

- 使用者已選定本機 `Sid Meier's Colonization (1994)/SMColoni/` 的合法 DOS 輸入作為正式研究目標。
- 中文化是 dosgolem 輸出階段的繁體中文覆蓋，不是 remake；不修改原版程式、資料、規則或存檔。
- 儲存庫 `wicanr2/colonization_cht` 維持 PRIVATE；原版素材、畫面、快照只保留本機。
- dosgolem 只修改 `workplace/dosgolem` 獨立副本；`upstream` 推送位址保持 `DISABLED`。
- 2026-09-22 使用者已確認原型的 Cubic 11、24px 字級（4 倍輸出畫布），不再等待字體大小決策。
  此決定僅適用顯示樣式，不代表術語、完成範圍或字型散布授權已定案。

## 目前狀態表

| 項目 | 狀態與證據 |
|---|---|
| 正常 DOS 啟動 | confirmed：原版 `COLONIZE.BAT` 使用 `OPENING.EXE -g`；已轉交 `VICEROY.EXE` 並顯示主選單。 |
| 主選單滑鼠 | confirmed：正常冷啟動後點選「新世界」可到難度畫面，不是 direct-entry 或記憶體改寫。 |
| 快照重播 | confirmed：連續路徑與安全選單快照續跑的索引畫面及色盤一致；無輸入留在主選單。 |
| 平台修正 | BIOS 馬達倒數、`int33 AX=0014` 回呼交換、DOS v4 滑鼠狀態與不安全回呼保存拒絕；規格 006–008。 |
| 動態文字 | confirmed：GAME.TXT 檔案位移 0x1B0 → 執行期 6F16:00DF → 937C:0538 印字 → 180 個畫布像素；兩次冷啟動收據一致。目標 054 完成。 |
| 靜態文字 | 開場海洋標籤等候選仍缺完整來源／可逆背景證據；Issue #8 開放，不阻擋動態路徑。 |
| 翻譯草稿 | `text/draft.zh-Hant.tsv` 共189筆；原始來源／控制碼及Cubic 11缺字檢查通過。新增139筆皆未取得畫面驗收；五列主選單為唯一已命中並驗證中文的候選。18個TXT／4,119粗略資料行不是全遊戲訊息分母。 |
| 說明雙語語料 | `text/help-bilingual.tsv`另含24則教學／地圖編輯說明的原文及繁中草稿，兩個固定原版檔案與每則位元組指紋可回查；僅限私有repo，未整合正式執行期語料，也未取得畫面命中。不可與前列189筆直接相加當顯示完成度。 |
| 中文顯示 | 五列已接原版執行事件及逐幀合成；七組狀態一致、105張圖獨立像素核對通過。規格012為CONFORMED；Ebitengine／Xvfb真視窗經明確Go介面接線，滑鼠可進難度，同輸入中英文原版狀態一致；仍非正式互動版，Issue #26保持開放。 |
| 完整可玩／正式發行 | 未驗證、未發布；本輪僅驗證至難度選擇。 |

## 工具與重播入口

- 研究映像：`colonization-research:20260920-r2`；分析、建置、測試、遊戲執行均在 Docker 內。
- 隔離 dosgolem 程式提交：`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`。
- 累積補丁：[tools/dosgolem-platform-fixes.patch](tools/dosgolem-platform-fixes.patch)，
  基底為 `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`，包含 SBPro／MCB／滑鼠修正、精確指令前觀測及通用合成器。
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

最近完成入口：[目標060](docs/goals/060-help-bilingual-corpus.md)：
24則遊戲內說明建立原文／繁中TSV，仍是待畫面驗收的草稿。
[目標059](docs/goals/059-ebitengine-display-wiring.md)讓Ebitengine視窗以明確Go介面
接到原版五列顯示，九筆真視窗輸入與中英文同狀態對拍通過。[目標058](docs/goals/058-translation-corpus-and-player-window.md)
保留189筆草稿及五筆畫面命中的分母。全遊戲中文化、第三種輸出情境與正式玩家前端仍未完成。

已完成 [目標 054](docs/goals/054-main-menu-text-provenance.md) 的最小證據鏈；
[目標 055](docs/goals/055-first-text-prototype.md) 保存中文原型、測試與重跑入口。
目前原型為 4 倍畫布、使用者已確認 Cubic 11 的 24px 顯示，中文為「在新世界開始遊戲」。
字型僅本機使用，內嵌許可不是 OFL，尚未完成正式散布權利審查。

目標056首列已由[規格012](docs/spec/012-five-menu-lines.md)擴至五列，每列三次事件一致。
滑鼠在(128,110)時前三列的完整安全區受遮擋而回退，後兩列仍中文；移開恢復。
不宣稱游標可跨過中文而不回退。已有以`tools/build_window_prototype.py`組裝的
可撤回Ebitengine視窗，經真視窗點擊與英文控制組對拍；它仍依賴目前有限的五列適配器，尚未抽離成
正式玩家前端，也未驗失焦／關窗。下一步取得難度畫面文字的輸出情境與安全矩形，
再按證據閘門擴大顯示；並繼續取得第三種
真正不同輸出情境；難度畫面已到達，但937C:0538沒有命中該畫面文字，不猜入口。
不得直接移植 psychic-war 的整個 xlate：其 3 倍數縮放與純色抹底假設不符目前原型。
不重新開啟整個開場研究；不以無頭切片關閉要求互動交付的 Issue #26。

術語、完成範圍與授權／公開方式仍需使用者依成果決定，不能把字型大小同意擴張解讀。
