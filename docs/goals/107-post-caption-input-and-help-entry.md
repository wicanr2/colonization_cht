# 目標107：開場字幕後的鍵盤消費與首則教學畫面入口

狀態：in_progress；日期：2026-09-24。承接[目標105](105-first-tutorial-player-path.md)
對 `@TUTORIAL1` 僅預讀的證據、[目標106](106-build-opening-caption-overlay-gate.md)
對 `@BUILD1` 真正顯示的證據；對應
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與範圍

英格蘭介紹 B 頁後，正常 Enter 已到英文 `@BUILD1` 字幕；探索性的
100M／115M 再按 Enter 至150M，索引畫面未變。尚不知道後續按鍵有無
被消費，也不知道首則教學何時真正印字。本輪從同一正常玩家路徑，
用 dosgolem 把送鍵、鍵盤待取數、原版畫布變化與開檔相位對齊；
若顯示教學，追其原始來源至實際輸出。不改原版 EXE、資料、規則、
存檔或正式 Ebitengine 中文層。`@BUILD1` 的38／42px版式選擇、
四國介紹長文與姓名顯示仍分別待使用者決定，本輪不代選。

## 工作與退出條件

1. 核對 Git 身分、PRIVATE 遠端、遠端 Issue、固定原版／玩家輸入
   SHA、隔離 dosgolem 禁推；**先推送本目標**，才修改探針或執行
   新重播。分析、建置、測試一律限資源、無網路、非 root Docker；
   原版唯讀，原始畫面與全文收據留在忽略版控的 `workplace/`。
2. 為既有正常玩家探針加入**選用**的字幕後診斷，不變更不帶新旗標
   的舊輸出：在送鍵瞬間及有界檢查點記鍵盤待取數、原版 CS:IP、
   原始索引畫面／畫布／色盤、開檔與 `GAME.TXT` 印字事件。先用
   既有150M資料縮小觀測，再視實際狀態延伸，禁止無界重試或
   修改 RAM 冒充玩家操作。
3. 比較無額外鍵與至少一條正常 Enter 後續分支。關鍵結論須兩次
   冷啟動與無讀寫監看控制同狀態；若命中首則 help，固定檔案
   位移、實際印字、原版文字墨跡和當次畫面。若未命中，記錄
   已觀測窗口及待取鍵數，不把預讀當顯示，也不推論全程不可達。
4. 建立獨立檢查器和必要負例：固定版本、同輸入重播、畫面／鍵盤
   相位、缺原版明示 SKIP。更新[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)
   的證據等級；沒有實際顯示與 READY 規格前，help 不接正式覆蓋。
5. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、唯一
   `docs/worklist.json` 並重生 `WORKLIST.md`；必要時只更新穩定
   README 現況。推送私有成果，更新且回讀 Issue；核對原版未入
   Git、檔案擁有權與 Docker 容器清理。

## 固定證據與停止線

- `GAME.TXT` SHA-256：
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
  `@TUTORIAL1` 標記位移 `0x1316A`、正文位移 `0x13190`，目前
  只證實在88,380,281步預讀。`@BUILD1` 在88,689,021–
  88,754,524步由 `0D21:00C6` 逐字讀取並由 `0D21:012C`
  寫原版320×200畫布。地址基準、版本與推論界線詳規格026。
- 既有16筆正常玩家輸入 SHA-256：
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`；
  隔離 dosgolem 提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`。
- 只追玩家可見的下一畫面與鍵盤消費。若剩餘差異只涉及
  PCM／DAC／PIT 或 Sound Blaster 逐週期等待，依專案硬體時序
  停止線採公開規格與合理近似，不深挖原版硬體驅動。
- 本輪即使只取得一則實際教學，也不代表24則 help 全部顯示、
  全遊戲文字已譯完或正式中文畫面增加。由 DRAFT 進 READY
  仍需來源鍵、逐欄字級、安全矩形與回退審查。

## 本輪結果

待依以上步驟實測回填；本節不得先填入預期結果。
