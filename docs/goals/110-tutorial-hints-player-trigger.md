# 目標110：從遊戲選項查證首則教學提示的正常玩家觸發

狀態：進行中；日期：2026-09-24。承接
[目標105](105-first-tutorial-player-path.md)的 `@TUTORIAL1` 預讀、
[目標107](107-post-caption-input-and-help-entry.md)的十張英文字幕與海上
畫面，以及[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)；
對應 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與證據起點

英格蘭正常玩家路徑約1,225M步已顯示可操作的海上介面，
但1,200M、1,225M、1,275M、1,325M四個抽樣沒有首則
教學視窗。`GAME.TXT:@TUTORIAL1` 在88,380,281步被 DOS
讀入 RAM，**不**代表顯示。現在原版 `MENU.TXT` 固定
SHA-256 `5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`
於檔案位移 `0xC6` 有 `Game Options`；原版 `GAME.TXT`
固定 SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`
於 `0x4A8` 有 `@GAMEOPTIONS`，`0x566` 有
`~Tutorial Hints`。這只證實檔案文字；「選項預設關閉」
及「勾選後立刻顯示首則教學」都仍是假說。

本輪不修改原版 EXE、TXT、規則、存檔或正式 Ebitengine
中文層；不代選 `@BUILD1` 的38／42px，也不把這個
教學選項的文字來源冒充實際點擊命中。完整原版畫素、
RAM 和重播 JSON 只留已忽略的 `workplace/`。

## 工作與退出條件

1. 核對 Git 作者、PRIVATE 遠端、Issue、原版與十六筆
   正常玩家輸入 SHA，以及隔離 dosgolem 禁推；
   **先推送本目標文件**，才改探針或執行新重播。
   研究工作只用限資源、無網路、非 root Docker，
   合法原版唯讀。
2. 從已驗1,225M海上畫面，以原版滑鼠移動、按下、
   放開操作頂端 `GAME`，觀測選單；再進 `Game Options`
   讀原版核取狀態。以可重播玩家輸入比較「不改選項」
   與「實際點 Tutorial Hints」分支，先做有界探索；
   不注入 RAM、改設定檔或用猜測座標偽稱點選成功。
3. 若教學顯示，閉合固定 `GAME.TXT:@TUTORIAL1` bytes、
   當次 DOS 讀入、實模式逐字印字、320×200原版畫布與
   玩家可見視窗；對關鍵分支各做兩次冷啟動及無讀寫
   監看控制。若未顯示，明列選項畫面、輸入消費、
   有界停止步數和下一個可驗操作，不把預讀當顯示。
4. 建立獨立檢查與負例，固定原版／探針版本、輸入、
   原始畫面及控制狀態；原版缺失回 `SKIP 77`。
   回填規格026、`CONTEXT.md`、`RESEARCH-LOG.md`、
   `WORKLOG.md` 和 `docs/worklist.json`，重生
   `WORKLIST.md`，私有推送並讀回 Issue。
5. 收尾核對沒有原版素材誤入 Git、研究輸出 UID/GID、
   root-owned／誤建 `.md` 目錄及 Docker 容器殘留。

## 停止線

`Tutorial Hints` 是可驗的候選開關，未證實其預設值、
效果或適用於哪一則教學。一次選項視窗、DOS 預讀、
單張畫面或遊戲內其他說明頁，都不能替代
`@TUTORIAL1` 的同狀態印字與畫布證據。即使找到首則
提示，也只增加一則原版顯示命中；24則 help 全文、
逐欄字級、中文安全矩形與正式 Ebitengine 覆蓋仍需
各自的 READY 規格與驗收。
