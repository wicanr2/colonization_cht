# 目標108：十張開場字幕的可追溯繁中草稿

狀態：完成（僅十張字幕的十一行繁中草稿）；日期：2026-09-24。承接[目標107](107-post-caption-input-and-help-entry.md)
已驗的英格蘭正常玩家路徑與[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)；
對應 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27) 與
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)。

## 玩家問題與本輪範圍

`GAME.TXT:@BUILD1–10` 十張開場字幕都已在 dosgolem 正常路徑印出，
但主譯稿目前只有 `@BUILD1` 一行。`@BUILD2` 分成兩行並帶
`%STRING0`／`%STRING1`，其他字幕也可能使用執行期變數；若只翻
已建的一行，玩家仍會依序看到其餘英文字幕。本輪只為缺少的
`@BUILD2–10` 建立逐**原始行**、固定來源的繁中草稿及獨立檢查；
不把草稿直接接入正式 Ebitengine 顯示層，也不替使用者選擇
`@BUILD1` 的38／42px版式或其他字幕的字級。

## 工作與退出條件

1. 核對私有遠端、Git 身分、Issue、固定原版 `GAME.TXT` 雜湊、
   十張字幕的 dosgolem 收據及既有 TSV 契約；**先推送本目標**，
   再建立譯稿或修改驗證程式。原版唯讀，所有分析和驗證只在
   限資源、無網路、非 root Docker 中執行。
2. 在固定 `GAME.TXT` 位元組上列出十張字幕的原始行起點、長度、
   片段 SHA-256、`^^` 控制符與 `%STRING` 占位符；從實際印字
   收據檢查變數展開的可見語意。對不能證實的語意明列假說，
   不把變數誤當常數或把標記預讀誤稱為印字來源全鏈已閉合。
3. 依現有 `text/draft.zh-Hant.tsv` 九欄契約新增缺少的十行草稿，
   保留每行原始縮排、控制符、占位符、標點功能和必要註記。
   翻譯只用於顯示候選，不回寫原版 RAM、TXT 或遊戲規則。
4. 用真實原版執行來源驗證器，另加明確涵蓋 `@BUILD1–10`
   共十一行的獨立檢查與占位符／錯版／缺行反例。草稿通過
   不等於正式輸出鍵、字級、安全矩形或同狀態中文畫面已完成。
5. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md` 與
   `docs/worklist.json`，重生 `WORKLIST.md`；私有推送後更新並
   回讀遠端 Issue。收尾查核譯稿以外的原版資料未入 Git、
   檔案擁有權、隔離 dosgolem 禁推與 Docker 容器清理。

## 固定證據與停止線

- 原版 `GAME.TXT` SHA-256：
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`。
  固定英格蘭十六筆玩家輸入 SHA-256：
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`。
  隔離 dosgolem 提交：`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`。
- 目標107的1,350M雙重播及無監看控制證實十張字幕的印字
  時間與原版畫布；檔案標記至整段印字的中間 RAM 搬運仍是
  **強推論**。本輪新增的譯稿都是 `draft`，不能增加目前十七段
  正式中文顯示數或宣稱 help 已顯示。
- 若變數語意或某行原版位元組不明，該行保持待查；不得用
  自製原文、任意取代字型或單一全域字級湊足數量。

## 本輪結果

固定 `GAME.TXT` 的 `@BUILD1–10` 共十一個 `^^` 原始行已有
十一筆來源固定草稿；本輪新增 `@BUILD2–10` 的十筆，使
[主譯稿](../../text/draft.zh-Hant.tsv)由369增至379筆。
`@BUILD2` 分成兩筆，不能把它誤算成一行；每筆的檔案 SHA、
位移、行長及行 SHA 均由現有全稿驗證器與
[`tools/check_goal108_caption_corpus.py`](../../tools/check_goal108_caption_corpus.py)
交叉核對。後者也重新讀目標107的雙冷啟動／無監看控制報告，
確認十段實際印字的長度、時間與位元組 SHA；原版英文全文、
畫素及字型都只留在本機，不加入 Git。

英格蘭路徑的原版印字有 `Explorer`、`Walter Raleigh`、`London`、
`King of England` 與 `England`；將其對應到各 `%STRING`
是模板與當次印字相符的**強推論**，中間 RAM 搬運未閉合。
譯稿保留所有具名占位符與 `^^`；`@BUILD4` 依中文語序把
`%STRING0` 放在 `%STRING1` 前，驗證器因此改為比對變數
**種類與出現次數**，並有錯名、缺重複次數及熱鍵／控制符
反例；這只調整草稿驗證，不改原版或正式顯示層。

全379筆主譯稿來源驗證 PASS；本輪獨立檢查的真原版正例、
缺原版 SKIP 77、錯版、缺行、錯占位符、錯字型與同時篡改
兩份印字報告的反例均 PASS。目標107完整收據也重新 PASS。
固定 SHA 的 Cubic 11 字型覆蓋十一行中81個不同字元，
缺字為零。本機 `receipt.json` SHA-256
`95a1172326ea151c9df56332fc9d75e50d72c8af109d682e54c7fcba616d453a`；
`workplace/reports/goal108-caption-corpus/` 保留收據與目標107
重驗結果，忽略版控。

未完成：展開後的變數值仍可能是英文；各國變數值本地化、
逐字幕字級／安全矩形、正式 Ebitengine 覆蓋、同狀態中文
畫面及首則 help 觸發需後續規格與驗收。規格026保持 DRAFT，
正式中文顯示仍為十七段，不以十一筆草稿冒稱字幕已中文化。
