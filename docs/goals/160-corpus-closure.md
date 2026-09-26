# 目標160：全遊戲語料收尾（Issue #27）

狀態：完成；開始與完成：2026-09-26。對應 [Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 驗收條件對照

| 條件 | 結果 |
|---|---|
| 可重跑的文字來源清冊與分母 | `tools/text_inventory.py`：遊戲畫面 3,561 行全部已抽取，已翻譯 3,558、刻意留空 3（英文冠詞，notes 有理由）（[目標158](158-text-denominator.md)、[目標159](159-corpus-translation.md)） |
| 每筆譯文有檔案雜湊、位移、長度、片段雜湊 | 十一份清冊皆有；`tools/coverage_report.py` 逐字核對 1,677 筆全部通過 |
| 占位符、控制碼、熱鍵與字型覆蓋驗證 | `tools/merge_corpus.py`、`tools/apply_term_edits.py` 逐筆檢查；Cubic 11 缺字為零 |
| 術語依使用者決定 | 第三波說明書術語表與定稿表（[目標154](154-manual-glossary.md)～[目標157](157-reverify-after-terms.md)）；術語檢查剩餘列都有不換理由 |
| 草稿／正常路徑／顯示分開統計 | 覆蓋率報表：已翻譯草稿 1,674 鍵；探針追到的正常路徑來源鍵 29；正常路徑實際顯示中文 73 鍵（收據早於目標156 改稿，見 [Issue #38](https://github.com/wicanr2/colonization_cht/issues/38)）。摘要 SHA-256 `5109a04840ea11f1a3cc7fa84305fdd41d06be4b35b7a170677c33178c9e35bc` |

## 不列入遊戲畫面分母的文字

| 來源 | 行數 | 理由 |
|---|---:|---|
| README.TXT 技術支援段 | 36 | 1994 年 DOS 記憶體設定、音效卡排錯與客服電話；在 dosgolem 下不適用。玩家說明部分已有 7 段譯稿 |
| DEBUG.TXT | 118 | 除錯訊息；正常遊玩是否可見未取證 |
| AUTOEXEC.TXT、CONFIG.TXT | 19 | DOS 設定範例檔 |
| MEMORY.TXT、MEMORY2.TXT | 13 | 記憶體不足警告，由 DOS 批次檔顯示 |
| 各 EXE 內英文字串 | — | `strings` 掃描只見執行期與覆蓋管理器錯誤（EMS、VM 檔、堆疊溢位）及除錯殘留，不是正常遊玩文字 |

## 限制

- 草稿不等於畫面顯示；各畫面的中文顯示依欄位規格逐項實作與驗證。
- LABELS.TXT 拼接片段與重排的占位符需要整句模板支援，實作顯示時處理。
- 部分專有名詞（曲名、次要部落、傭兵階級）為自譯，notes 已標示。
