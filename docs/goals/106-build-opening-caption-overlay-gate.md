# 目標106：開場字幕 `@BUILD1` 的中文覆蓋閘門

狀態：active；日期：2026-09-24。承接[目標105](105-first-tutorial-player-path.md)
已證實英格蘭正常玩家路徑上的英文開場字幕，對應
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、
[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)及
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與範圍

國家介紹 B 頁後，原版 `GAME.TXT:@BUILD1` 在畫面上顯示一行英文，
目前只有來源、逐字印字及畫布差分證據；繁中「主後一千四百九十二年，」
仍只是 TSV 草稿。本輪要讓這個實際可見的訊息向正式中文顯示邁進，
但不把預讀的 `@TUTORIAL1` 當成已顯示，也不改原版 EXE／TXT、
遊戲規則、存檔或玩家輸入。其餘國家、其他 `@BUILD` 字幕與
四國介紹長文不自動套用本欄字級或事件鍵。

## 工作與退出條件

1. 先核對 Git 作者、PRIVATE 遠端、Issue 狀態、原版與玩家輸入
   SHA、隔離 dosgolem 的禁推設定；**先推送本目標**，再更動探針
   或正式程式。原版、完整原文、印前畫布與字模只留 `workplace/`。
2. 在已驗英格蘭正常玩家路徑，以 dosgolem 雙次冷啟動及無讀寫
   監看控制，擷取 `@BUILD1` 第一筆 `0D21:012C` 畫布寫入前的
   真正背景；固定原文來源、`0D21:00C6` 逐字讀取、印字後
   320×200 索引畫面、調色盤及印字範圍。觀測不得改原版機器狀態。
3. 由原版 9px 墨跡高度與單行畫面空間，逐欄量測 Cubic 11
   的繁中字級、墨跡寬高、位置、基線與安全矩形；製作可丟棄
   的四倍畫布樣本，明列超界、背景、游標及缺譯回退策略。
   若存在實質不同的視覺取捨，先交由使用者依樣本決定。
4. 審查[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)
   是否具備 READY 所需來源鍵、頁相位、輸入／輸出及失敗模式。
   未達 READY 只保存 DRAFT 證據與樣本，**不**接正式輸出層；
   達 READY 後才實作 Ebitengine 字幕覆蓋，與同輸入英文控制、
   既有十七欄回歸做同狀態驗證，通過才限縮標為 CONFORMED。
5. 建立獨立失敗即關閉檢查及錯版／缺原版 SKIP 負例；更新
   `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、唯一
   `docs/worklist.json` 並重生 `WORKLIST.md`。推送私有成果、
   更新並回讀相關 GitHub Issue；核對沒有原版素材入 Git、
   沒有 root-owned 殘留及 Docker 容器清理。

## 證據與停止線

- 原始 `GAME.TXT` SHA-256：
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`。
  字幕 `@BUILD1` 的檔案標記位移 `0x153B0`、可見英文起點
  `0x153CE`、印字呼叫點 `0D21:00C6`、寫畫布點 `0D21:012C`；
  上輪已驗可見 bbox `[16,30,303,39)`。詳細收據見規格026。
- 既有十六筆玩家輸入 SHA-256：
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`；
  dosgolem 僅用 `workplace/dosgolem` 的隔離副本。
- 本目標只處理一條字幕的輸出層。它不能使24則 help、其餘字幕、
  國家介紹長文或整款遊戲取得「中文化完成」聲明。
