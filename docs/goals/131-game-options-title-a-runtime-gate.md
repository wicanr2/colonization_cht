# 目標131：遊戲選項標題 A 字級的執行期閘門

狀態：進行中；開始：2026-09-25。承接[規格027](../spec/027-game-options-window-draft.md)、[目標128](128-a-layout-decisions-and-build1-runtime-gate.md)與[目標122](122-game-options-nine-field-state-guard.md)；對應既有 [Issue #11](https://github.com/wicanr2/colonization_cht/issues/11)、[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)及[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)，不另立同義 Issue。

## 範圍

使用者已選定遊戲選項九欄 A：標題 34px，八列依序 25／28／28／25／28／28／27／28px，排除較大的 B。本輪以**沒有快捷鍵標記的標題** `GAME.TXT:0x4CD` 作第一個可隔離正式閘門；八列的 A 字級與譯文保持既定，不因標題通過就自動顯示中文。原版 EXE、資料、RAM、輸入、規則與存檔不得修改。

## 工作與退出條件

1. 先核對私有遠端、Issue、固定原版及隔離 dosgolem，推送本目標與 `CONTEXT.md` 入口。所有分析、建置、遊戲與抓圖只在有界、非 root 的 Docker 容器內，掛載來源先驗形態。
2. 以 dosgolem 正常滑鼠開窗，確認標題當次原文讀取、畫布寫入、真 VGA 同步、安全區與離頁失效；雙冷啟動及無監看控制同狀態。原始檔案→高位址 RAM 的未閉合中間搬運維持明示「強推論」，不冒稱整條來源鏈完全證實。
3. 對標題 34px 真譯文與固定字型量字模、陰影、實際墨跡和多色底圖。把原版同幀畫布、色盤、游標與事件權杖檢查成逐幀可逆的失敗即回退契約；核取圖示與八列不在本輪改色範圍。
4. 只有標題的窄規格經證據審查達 READY 才加入預設關閉的正式 Ebitengine 覆蓋。以英文控制／中文 A／缺譯、重複鍵、錯版、缺字模、游標、反白與 ESC 離頁反例重播；原版 CPU、完整 RAM、索引／底層畫布、色盤、時間、開檔及輸入須同狀態，中文新畫素只限標題安全矩形。真正視窗驗收通過才標限定 CONFORMED；未達則保留 DRAFT 與具體缺口，不更新正式截圖。
5. 回填規格、研究及工作歷程、`CONTEXT.md`、機器工作清單與產生的 `WORKLIST.md`；推送私有遠端並回讀 Issue。檢查原版素材未追蹤、檔案 UID/GID、隔離 dosgolem 禁推及 Docker 容器清理。

## 停止線

標題成功只增加一個明示開關的正式中文欄位，不宣稱整個九欄視窗完成。八列的 `~` 快捷鍵可見策略、按下／放開完整相位與執行期逐欄守門仍屬規格027 DRAFT；不得猜測快捷鍵標示或以固定取樣原型冒充正式玩家畫面。原版像素、字型、原始收據只留在已忽略的 `workplace/`。
