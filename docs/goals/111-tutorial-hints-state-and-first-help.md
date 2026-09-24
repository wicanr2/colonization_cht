# 目標111：確認教學提示開關並追首則正常玩家顯示

狀態：進行中；日期：2026-09-24。承接[目標110](110-tutorial-hints-player-trigger.md)
已驗的 `GAME` → `Game Options` → `Tutorial Hints` 原版畫面、
海上左方向鍵及[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)
的 `@TUTORIAL1` 預讀；對應
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與固定起點

使用者要求完整繁體中文顯示，24則 help 雖有可追溯雙語草稿，
目前仍沒有任何一則正常玩家路徑的實際畫面命中。目標110
確認選項最後一列可點、原版圖示與背景變化，但**沒有**確認
圖示代表啟用還是停用，也沒有看到 `@TUTORIAL1` 正文。
本輪要由這個已驗起點找到可重播的首則教學顯示事件，
或以有限玩家操作縮小下一個可驗觸發條件。

固定原版 DOS `MENU.TXT` SHA-256
`5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`，
`GAME.TXT` SHA-256
`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
正常英格蘭十六筆玩家輸入 SHA-256
`a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`。
本專案隔離 dosgolem 固定提交
`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，
推送位址 `DISABLED`。所有原版位址／文字來源須區分
檔案位移、DOS 線性 RAM、實模式 `CS:IP`、原版320×200
畫布及四倍輸出畫布。

## 本輪工作與退出條件

1. 核對目前 Git／PRIVATE 遠端／Issue／原版與探針版本，
   **先將本目標 Markdown 推送私人儲存庫**，再做新的
   原版重播或探針變更。所有分析、建置、測試及遊戲執行
   限於無網路、限資源、非 root 的一次性 Docker 容器；
   原版唯讀，完整原文與像素只留已忽略的 `workplace/`。
2. 以目標110的原版設定視窗為起點，取得未點、點一次、
   必要時點兩次的同輸入對照；查核圖示狀態和離開視窗
   後是否持續，不把「圖示變化」直接命名為啟用／停用。
   若需判斷語意，使用玩家可見結果或原版明確資料流，
   不以任意色號猜測。
3. 由已見原版介面選擇一個明確的正常玩家遊戲動作，
   優先試結束回合；確認原版確實消費該輸入、畫面／
   狀態進入預期相位，再比較未點與兩種選項狀態。
   不注入 RAM、修改原版設定檔或使用測試專用直達路徑
   冒充玩家操作。探索須有界；若玩家動作無效，先修正
   操作座標／鍵值的證據，不反覆盲目加鍵。
4. 若首則 help 出現，固定 `GAME.TXT:@TUTORIAL1` 的原始
   bytes／SHA、當次 DOS 讀入、`0D21:00C6` 或實際印字
   常式的 RAM 讀取、原版畫布與正常玩家視窗；關鍵分支
   各做雙冷啟動和無監看控制，再建立獨立正反例。若仍
   未出現，明列各選項狀態、實際動作、停止指令數與
   下一個可驗操作，不把預讀當顯示或聲稱 help 已完成。
5. 回填規格026、`CONTEXT.md`、`RESEARCH-LOG.md`、
   `WORKLOG.md` 與唯一 `docs/worklist.json`，重生
   `WORKLIST.md`。正式 Ebitengine 覆蓋仍須另過
   READY、逐欄字級與安全矩形、同狀態顯示及回退閘門；
   本輪不代選 `@BUILD1` 的38／42px。私有 push 後更新
   並回讀 Issue；收尾核對原版素材未入 Git、檔案 UID/GID、
   root-owned／誤建 `.md` 目錄及 Docker 容器清理。

## 停止線

目標110的1,225M–1,350M畫面抽樣只支持已見選項與輸入，
不能排除中途短暫畫面，也不能當作首則 help 不可達證據。
本輪若只得到選項語意或另一個有效玩家動作，須誠實維持
規格 DRAFT、help 正式顯示零則；後續仍以正常玩家路徑
與 dosgolem 原版收據作權威，不深挖與玩家顯示無關的
硬體逐週期時序。
