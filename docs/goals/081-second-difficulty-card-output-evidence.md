# 目標081：第二張難度卡片的正常輸出證據

狀態：完成（僅第二張卡片原文輸出證據）；日期：2026-09-23。承接[規格016](../spec/016-difficulty-card-text-draft.md)、
[目標079](079-first-card-formal-overlay.md)；對應 Issue
[#6](https://github.com/wicanr2/colonization_cht/issues/6)、
[#7](https://github.com/wicanr2/colonization_cht/issues/7)及
[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

第一張卡片的「發現者／最簡單」已正式驗收，但其餘卡片仍無來源至畫素的
同等證據。這輪從固定九筆真視窗輸入抵達難度頁後，嘗試以原版滑鼠事件
選中第二張卡片，確認玩家實際看到的原文、來源與畫布變化。標題重排
Issue #28 等待使用者選版，本輪不依賴也不修改該版式。

## 工作與退出條件

1. 先將本目標推送私有儲存庫，再在唯讀原版與隔離 dosgolem 上試驗第二張
   卡片的滑鼠座標、按下／放開與移開；保留固定輸入、原版檔案 SHA-256、
   工具提交、步數與輸出畫面。若卡片不切換，記錄反例，不猜測顯示鍵。
2. 以同輸入無觀測控制組及至少兩次獨立重播，確認原版 CPU、完整 RAM、
   320×200 索引畫面、色盤與時間一致；把游標像素與底層文字畫布分開。
3. 若第二張卡片顯示新文字，追查原始 TXT 候選、DOS 線性 RAM、原始
   `CS:IP` 讀取／寫畫布事件、實際格式化顯示字節、墨跡與安全矩形；
   每個結論標明已證實、強推論、假說或未知。不得只因同文就借用
   第一張卡片的覆蓋鍵、字級或有紋理背景補片。
4. 更新規格016的 DRAFT 進度、研究紀錄、現況、工作歷程與 Issue；只有
   來源、輸出、背景、游標和字級證據齊全並經 READY 審查，才可另階段
   接入正式 `tools/live_menu.go`。原版畫面及完整資料只留已忽略的
   `workplace/reports/`，不加入 Git。
5. 核對 `tools/worklist.py verify`、權利邊界、工作樹、輸出擁有權與
   Docker 容器清理狀態；推送私有儲存庫並回填對應 Issue。

## 停止線

這不是 remake；不修改原版 EXE、TXT、規則、存檔、卡片命中區或玩家流程。
受控重播／探針不是原版真視窗玩家操作的替代品；沒有畫面證據時不要把
第二張卡片的草稿翻譯計入正式中文段數。Issue #28 的視覺決策保持待定。

## 結果與下一閘門

- `tools/prepare_second_card_inputs.py` 從已驗九筆真視窗路徑產生控制、
  僅移入與點擊第二張卡片三組受控輸入；只有點擊 `(265,55)` 會使原版
  出現 `EXPLORER:`／`Easy`。另由
  `tools/probe_second_card_window.sh` 真 Ebitengine 視窗記下12筆實際輸入，
  同樣到達第二張卡片；中文視窗與英文控制原版同狀態。
- `tools/probe_card_load.go -second` 及 `tools/probe_second_card_output.go`
  各雙次冷啟動，證明 `NAMES.TXT:0xC18`／`LABELS.TXT:0x8B2` 經原版
  DOS 讀入、執行期來源、格式化顯示至兩行原始畫布；
  `tools/check_second_card_output.py` 獨立核對來源雜湊、未截斷、雙次收據、
  英文控制同狀態、畫布差分、紋理背景和真視窗畫面。
- 已於[規格016](../spec/016-difficulty-card-text-draft.md)追加第二張卡片
  的已證實欄位與未知。尚缺逐欄中文預覽、游標／缺譯回退及正式 Ebitengine
  覆蓋驗收；下一個實作目標須先做 READY 審查。本輪不修改
  `tools/live_menu.go`，不增已顯示中文數，原版畫面只留本機。
