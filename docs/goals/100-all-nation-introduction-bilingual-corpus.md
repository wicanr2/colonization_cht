# 目標100：四國介紹八節的可追溯繁中語料

狀態：進行中；日期：2026-09-24。承接[目標098](098-first-nation-introduction-source.md)
已驗的法國 A／B 兩頁來源與[規格025](../spec/025-first-nation-introduction-draft.md)，
對應 [Issue #30](https://github.com/wicanr2/colonization_cht/issues/30) 與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與本輪界線

目前首次介紹只有 `GAME.TXT:@NATION1A`／`@NATION1B` 兩節法國繁中草稿。
唯讀初盤顯示合法 DOS `GAME.TXT` 另有英格蘭、西班牙、荷蘭各 A／B 節，
共八節。若只研究已到達的法國頁，玩家選其他國家仍缺介紹譯稿。
本輪完成八節的來源固定雙語語料及獨立檢查；**不**把尚未取得
正常路徑畫面命中、字級、安全區或回退的其他六節宣稱已顯示。
原版 EXE／TXT、規則、存檔與玩家流程均不改；暫不以替代字型
猜測長文排版。

## 固定輸入與初盤邊界

合法 `GAME.TXT` SHA-256 是
`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
下列均為**檔案位移候選**，不是 RAM 或實模式位址，須由獨立
檢查器回讀原始 bytes 與下一個頂層節標記才算本輪證實：

| 節 | 初盤起點 | 下一頂層節起點 |
|---|---:|---:|
| `@NATION0A` 英格蘭 | `0xAE7C` | `0xB204` |
| `@NATION0B` 英格蘭 | `0xB204` | `0xB2DB` |
| `@NATION1A` 法國 | `0xB2DB` | `0xB641` |
| `@NATION1B` 法國 | `0xB641` | `0xB73E` |
| `@NATION2A` 西班牙 | `0xB73E` | `0xBB46` |
| `@NATION2B` 西班牙 | `0xBB46` | `0xBC28` |
| `@NATION3A` 荷蘭 | `0xBC28` | `0xC032` |
| `@NATION3B` 荷蘭 | `0xC032` | `0xC191`（下一節 `@PICKACARGO`） |

原版資料只唯讀掛載至限資源 Docker；完整原文與執行畫面只可放
已忽略的 `workplace/` 或已核對 PRIVATE 的研究儲存庫，不能公開。
本專案 dosgolem 只使用 `workplace/dosgolem` 隔離副本，上游
推送位址保持 `DISABLED`。

## 工作與退出條件

1. 先推送本目標至已核對 PRIVATE 的 `origin/main`，回讀遠端
   Issue #27／#30 均為 OPEN；確認 Git 身分、工作樹與合法輸入。
2. 以真實 `GAME.TXT` 建立八節的完整邊界、節 SHA-256、標題、
   原版控制標記與可見原文清冊；保留原始定位與推論等級，最後
   `@NATION3B` 必須止於下一頂層節，不能吞入後續資料。
3. 在現有 `text/nation-introduction.zh-Hant.tsv` 加入其餘六節
   繁體中文草稿，保留兩筆已驗法國內容。沿用原有欄位與可追溯
   來源鍵；地名、人名、原住民族稱與遊戲機制術語參照既有語料，
   不確定譯法在 notes 誠實標註，不默認術語已定稿。
4. 建立獨立驗證器：對八節逐筆核對固定原版雜湊、連續不重疊
   位移與長度、原始節 SHA、標題／換行／強調標記、大括號數量、
   TSV 唯一鍵、譯文非空與不含會破壞欄位的控制字元。抽查
   兩次輸入讀取結果一致；不得以譯文進入原版查找或規則。
5. 如仍有時間，獨立追查英／西／荷 A／B 的正常玩家命中方式；
   任何未親自重播的頁只標「有原版節，畫面未驗」。不因語料
   完成而把規格025升 READY 或增加十七段已顯示數。
6. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、唯一
   `docs/worklist.json`（並重生 `WORKLIST.md`），更新並回讀
   GitHub Issue #27／#30，推送 PRIVATE `origin/main`。收尾檢查
   原版素材未入 Git、UID/GID、誤建目錄與 Docker 容器清理。

## 停止線

這是**語料輪**，不是長文顯示完成輪。四國 A／B 在 `GAME.TXT`
存在，只證明文本候選的邊界；未經 dosgolem 正常玩家路徑命中、
原版印字與安全矩形驗證，不能推論其實際畫面順序、完成頁數或
翻頁語意。固定 Cubic 11 原始字型未恢復，不以其他字型的測量
冒充正式中文字級。第一張旗卡 A 版、右卡待決字級及姓名欄待決
選項均不受本輪翻譯變更影響。
