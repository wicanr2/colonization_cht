# 目標078：第一張難度卡片的執行期背景與游標守門

狀態：in progress；日期：2026-09-23。承接
[目標075](075-difficulty-card-source-to-pixels.md)、
[目標076](076-difficulty-card-reversible-prototype.md)、
[目標077](077-difficulty-card-load-provenance.md)與
[規格016](../spec/016-difficulty-card-text-draft.md)；對應 Issue
[#6](https://github.com/wicanr2/colonization_cht/issues/6)及
[#26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 問題與範圍

第一張卡片兩行的原始 TXT → 執行期字串 → 字形 → 像素鏈已閉合；
離線 Ebitengine 預覽也能恢復有紋理底圖。但固定終點的預先存檔畫布，
不能證明正常執行中每次重畫都可取回原始底圖，也未驗證滑鼠遮擋與後續繪圖。
本輪只在隔離 dosgolem 的真實正常玩家路徑，建立可重播的執行期擷取與回退實驗；
不預先把 DRAFT 原型接入正式 `live_menu.go`。

## 工作與退出條件

1. 固定原版檔案雜湊、九筆真視窗輸入及 dosgolem 版本，於兩行原文真實讀取
   與字形畫布寫入附近收集執行期前後畫布、索引畫面、色盤、游標座標／按鍵及
   20-bit RAM／真實模式 `CS:IP`。觀測者不得改原版記憶體或玩家輸入。
2. 以遊戲專屬、可丟棄的守門探針從當次原文繪製前畫布建立兩欄有紋理背景補片，
   對每個候選顯示幀核對完整原文、字形差分、半開安全矩形、背景與游標／後續繪圖。
   橫跨不同時刻的舊補片、遮擋、缺譯／缺字模或版本不符均須回退原文並記錄原因；
   不得改原版畫布來讓測試通過。
3. 至少以兩次獨立正常玩家重播及一組卡片游標進出或同等反向條件驗證：
   原版 CPU／RAM／索引畫面／色盤不因觀測與輸出合成改變；合成差異只在兩欄
   安全矩形。若游標由原版畫在畫布之外，須明確記錄能力邊界，不能假稱已測遮擋。
4. 依實測更新規格016的 confirmed／unknown、可重跑工具與本機收據；
   只有 READY 審查能授權正式覆蓋。更新 `CONTEXT.md`、`RESEARCH-LOG.md`、
   `WORKLOG.md`、私有 GitHub 儲存庫與對應 Issue，保留 Docker 清理與權利邊界。

## 停止線

不修改原版 DOS 檔案、存檔或規則，不修改 dosgolem 上游，也不把原版畫布快照、
原版素材、字型或含原版像素的 PNG 加入 Git。第一張卡片的結論不能外推其餘卡片；
本輪沒有足夠證據時維持規格016 DRAFT 與原文回退，已顯示中文數量不增加。
