# 規格026：開場字幕與首則教學預讀（DRAFT）

狀態：DRAFT；日期：2026-09-24。證據入口為
[目標105](../goals/105-first-tutorial-player-path.md)、
[原始 help 雙語草稿](../../text/help-bilingual.tsv)與
[字幕譯文草稿](../../text/draft.zh-Hant.tsv)。本規格不授權
正式中文覆蓋，不把預讀當作顯示。

## 範圍與固定輸入

使用者自備 DOS `COLONIZE` 中 `GAME.TXT` SHA-256
`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
`OPENING.EXE`、`VICEROY.EXE`、`NAMES.TXT`、`LABELS.TXT`、
`NATIONS.PIK` 另由[獨立驗證器](../../tools/check_goal105_tutorial_route.py)
固定各自雜湊。十六筆正常玩家輸入 SHA-256
`a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`；
隔離 `workplace/dosgolem` 提交
`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，
`colonization-research:20260920-r2`／Go 1.24.13。原版唯讀，
原始索引畫面、色盤與完整原文收據只在忽略版控的
`workplace/reports/goal105-tutorial/`。

正常玩家路徑為主選單、難度、英格蘭旗卡、姓名 Enter、
介紹 A→B、B 後 Enter，在85M步進入已驗後續頁；再於
85M步分別等待、按 Enter 或按 ESC。三分支各有兩次
獨立冷啟動及一次無讀寫監看控制，觀察到100M步。

## 原始來源與可見結果

地址須分開讀：`GAME.TXT` 檔案位移、20-bit DOS 線性 RAM、
原版實模式 `CS:IP`、320×200 索引畫布和四倍中文輸出畫布
不是同一座標系。

| 原始定位與事件 | 觀測 | 等級 |
|---|---|---|
| `GAME.TXT:0x1316A` 的 `@TUTORIAL1`，首段自 `0x13190` 的 `Our {%STRING0}`；DOS 讀位置 `0x13000`，88,380,281步送至線性 RAM `0x2B16C`／`0x2B192` | Enter／ESC 後都載入，無鍵沒有；到100M沒有這則教學的實際印字 | 已證實：固定路徑的**預讀**，不是已顯示 |
| `GAME.TXT:0x153B0` 的 `@BUILD1`，行自 `0x153CC`，去掉 `^^` 後文字自 `0x153CE`；61-byte原文 SHA-256 `c1feca9ed16dd6cf8cfd36a118536afd25b86f6677f3ec81d056fad6e78a6db6` | 原文跨 `0x15400` 的512-byte讀取邊界；`0x153CE–0x153FF` 從讀位置 `0x15200` 送至 RAM `0x2B1D0`，`0x15400–0x1540A` 從讀位置 `0x15400` 送至 `0x2B002` | 已證實：檔案 bytes、兩次 DOS 讀取與目的 bytes |
| 實模式 `0D21:00C6` 從線性 RAM `0x2A560`／`0x2A561` 交替讀取，88,689,021–88,754,524步 | 去掉交錯零位後，恰為 `@BUILD1` 的61-byte英文字幕；沒有教學正文 | 已證實：當次逐字印字 |
| 實模式 `0D21:012C` 寫 320×200 原版畫布 | 1,040次改色，半開 bbox `[16,30,303,39)`，原版墨跡高9邏輯像素；90M／95M／100M索引 SHA-256 均為 `b8c0d43983c95415071e83513628fc90e8de3236f3e75eb699ed4d87dfc8c772` | 已證實：當次畫布；尚非中文安全矩形 |

印字緩衝 `0x2A560/1` 與前兩次 DOS 讀入目的地址不同；
此處證實原始文字、讀入及最後印字 bytes 相同，**未逐指令
追完中間搬運**。整段來源歸屬為強推論，不能只靠相同字串
將 DOS 讀取冒稱為完整資料流。字幕底圖含原版像素；不因
已在私有工作區重建 PNG 就取得公開散布權。

無鍵分支85M–100M留原頁且開檔數60；Enter／ESC在90M
顯示同一字幕，依序另開 `LEVN0001.PIK`、`GAME.TXT`、
`PHYS0.SS`、`ICONS.SS`、`BUILDING.SS`，100M開檔數65。
兩鍵畫面相同但完整 RAM 不同，不能推論後續規則等價。
一次**探索性**延伸至150M，於100M／115M再送 Enter；
索引畫面與色盤仍為同一字幕，130M另讀三項 `.SS`。
這不是雙重播控制收據，不可宣稱教學永遠無法到達或
推論硬體播放時序。後續應先檢查按鍵消費與玩家可見
動畫相位；若只剩 PCM／DAC／PIT 細節，遵守專案硬體
時序停止線，不深挖原版 driver。

## 繁中候選與正式閘門

主譯稿新增 `GAME.TXT:0x000153CC` 草稿「主後一千四百九十二年，」，
保留原版 `^^` 控制碼；`tools/validate_translation_draft.py`
驗證原始行位移、完整檔案與行 SHA、CRLF 和控制符號。
此譯文不參與原版條件比較，也不輸入原版 RAM。

原版墨跡高9像素只給出約36px的四倍畫布參考高度；
**尚未**量中文字模、當次多色印前底圖、文字安全矩形、
游標遮擋、最長字幕、缺譯回退或 Ebitengine 真視窗。
正式字幕與教學各需獨立來源鍵、頁相位和按鍵守門；
依 `RE → DRAFT → READY → implementation → 同狀態 → CONFORMED`
逐一驗收。這輪中文正式顯示仍為十七段，24則 help
仍只有雙語草稿，沒有顯示命中。

## 重播入口

`tools/probe_goal098_intro.go` 只有指定 `-after-follow` 才在
85M後開啟新觀測窗；不帶旗標的英格蘭預設 JSON 與目標101
逐位元組一致。`tools/check_goal105_tutorial_route.py` 核對
雙重播、無監看控制、三種原始畫布、原版版本、兩段跨界讀取、
實際印字及開檔；`tools/test_goal105_tutorial_route.py` 核對
原版缺失 SKIP、錯版、畫布與印字串破損。受控本機
`workplace/reports/goal105-tutorial/receipt.json` SHA-256
`97e92bd05ce8ff6fd97778e3a70ad4d76de6daf6fc44b08dd6e7fc802d697da7`。
