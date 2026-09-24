# 目標109：四國開場字幕變數的實際值與來源候選

狀態：completed（僅四國固定難度的變數值草稿與來源候選）；日期：2026-09-24。承接
[目標107](107-post-caption-input-and-help-entry.md)的英格蘭十張原版字幕、
[目標108](108-build-opening-caption-translation.md)的十一行繁中草稿及
[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)；
對應 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27) 與
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)。

## 玩家問題與範圍

字幕模板雖已翻譯，`@BUILD2`、`@BUILD3`、`@BUILD4`、
`@BUILD7` 仍有 `%STRING0`／`%STRING1`。若正式輸出層只套用
譯文模板，探險家、出發城市、君主及國名等展開值可能
仍是英文。上一輪只從英格蘭的固定路徑看到五種英文值；
不得把英格蘭值硬套到法國、西班牙或荷蘭，也不得讓譯文
流入原版的條件比較、查找或存檔。

本輪以**四張實際旗卡的正常玩家路徑**，用隔離 dosgolem
擷取上述四張字幕的展開印字，追查固定原版來源與顯示
用途。若來源足夠，建立來源可追溯的繁中值草稿及驗證器；
若部分值由執行期組合或玩家輸入產生，只保留有證據的
範圍與待查鍵，不猜造全域取代規則。本輪不修改原版資料、
遊戲規則或正式 Ebitengine 覆蓋；字幕逐欄字級及
`@BUILD1` 的38／42px選擇仍獨立待決。

## 工作與退出條件

1. 核對 Git 身分、PRIVATE 遠端、Issue、原版與正常玩家
   輸入 SHA、隔離 dosgolem 禁推和現有 probe 能力；
   **先推送本目標**，才啟動新探針。Docker 限資源、
   無網路、非 root，合法 DOS 原版唯讀，研究中間物
   只留在已忽略的 `workplace/`。
2. 沿四國已驗旗卡滑鼠選取、姓名及介紹翻頁，正常輸入
   抵達字幕；只觀測至足以涵蓋 `@BUILD7` 的有界步數。
   新路徑至少兩次冷啟動加一個無記憶體監看控制，
   比對 CPU、完整 RAM、索引、色盤、虛擬時間與開檔。
3. 以固定 `GAME.TXT` 模板、dosgolem `0D21:00C6`
   實際字元及原版檔案查找，逐國分開記錄六處
   占位符的可見值、原始檔案位移／位元組或來源未知，
   並標示已證實、強推論、假說或未知；不能把
   字串相似當成中間 RAM 搬運已閉合。
4. 只有已定位且格式可核對的值才進 `text/` 的
   UTF-8 TSV 草稿；保留原值、譯值、上下文、原版
   指紋、來源定位、衝突／缺值處理。變數翻譯只
   提供顯示候選，不寫入原版 RAM。建獨立正反例，
   尤其拒絕錯版、錯國、錯占位符或缺值時的猜補。
5. 回填規格026、`CONTEXT.md`、`RESEARCH-LOG.md`、
   `WORKLOG.md` 與 `docs/worklist.json`，重生
   `WORKLIST.md`；私有推送後更新並回讀 Issue。
   收尾檢查原版素材未入 Git、輸出 UID/GID、
   root-owned／誤建目錄及 Docker 容器清理。

## 證據界線

- DOS `GAME.TXT` SHA-256：
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
  十六筆正常玩家輸入 SHA-256：
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`；
  隔離 dosgolem 提交：
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`。
- 先分清 `GAME.TXT` 檔案位移、20-bit 線性 RAM、
  原版實模式 `CS:IP`、320×200 原版畫布及四倍
  輸出畫布。`@BUILD` 讀入不等於最後印字或
  正式中文顯示；翻譯草稿與正式十七段分開計數。
- 如正常路徑至限定步數仍未顯示某字幕或某國
  變數來源未確定，保存具體原版收據與負例，
  不改 probe 的玩家輸入、不擅自延長成無界研究。

## 驗收結果與剩餘界線

四國各由正常旗卡滑鼠選取、姓名與介紹翻頁進入字幕。法國、
西班牙、荷蘭各在800M步內印出 `@BUILD1–7`；每國兩次冷啟動
JSON 逐位元組相同，第三次無 RAM 讀寫監看的 CPU、完整 RAM、
索引畫面、色盤、時間、開檔、鍵盤與來源觀測檢查點一致。
英格蘭沿用目標107已驗的1,350M收據。`0D21:00C6` 每國
七段實際英文印字，對上固定 `GAME.TXT` 模板和六處占位符；
不同國家的領袖、港口、國名及荷蘭稱謂均未借用英格蘭值。

[四國字幕變數草稿](../../text/build-caption-values.zh-Hant.tsv)共24筆，
逐筆保存國別、字幕、占位符、檔案候選與 SHA-256、原文
檔案片段、**當次可見展開值**及繁中草稿。`NAMES.TXT`
的 `@DIFFICULTY`、`@LEADERNAME`、`@HOMEPORT`、`@COUNTRY`
和 `GAME.TXT` 的 `@MYLEADER` 提供可回查位移；但它們到
最終印字的中間 RAM 搬運尚未逐指令閉合，故來源連結只屬
強推論。荷蘭兩次國名占位原始候選是 `Netherlands`，
實際畫面為 `the Netherlands`；`the` 的組合來源**未知**，
草稿將兩值分欄，不把它錯認成 `NAMES.TXT` 原始 bytes。

`tools/check_goal109_caption_values.py` 以檔案雜湊、固定來源
位移、雙重播、無監看對照與印字模板獨立核對，四國均 PASS；
`tools/test_goal109_caption_values.py` 八個正反例 PASS，包含
缺原版 SKIP、錯版、錯國、錯占位符、缺筆、荷蘭冠詞與
缺值時不提供譯文。僅本機 `workplace/reports/goal109-caption-values/`
保存完整 JSON，最終 `receipt.json` SHA-256
`fda3cd28d14c2ae09c94b51c5e74a638e0e15daa16202940c9d23845b3554b0c`。
本輪**沒有**正式 Ebitengine 字幕覆蓋、逐欄字級或安全矩形
驗收，正式中文畫面仍十七段；`@BUILD1` 的38／42px選擇
和 help 實際觸發仍待後續工作。
