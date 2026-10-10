# 遊戲語言資料與來源隔離

狀態：限定CONFORMED，僅語料驗證與文本組裝契約。入口：[目標186](../goals/186-display-settings-and-gameplay-video.md)。
本規格先處理完整語料及建置資料，不授權未驗的字型、畫面切換或正式語言包。

## 來源與範圍

confirmed：現行正式消費端讀13份TSV，共2006列、1835種繁中顯示值。
來源欄有`zh_hant`、`zh_hant_draft`及`zh`三種；動態字串、對話框、百科、
開場、靜態字圖、複合變數及城市名都須涵蓋。只提供前端五語選單不能算遊戲五語。

只讀盤點入口：`workplace/reports/goal186-display-hd/locale-catalog-inventory-20261011.json`。
2006個來源鍵與原始列指紋聯集SHA-256為
`a3ea14e763f8a34b9b29794fed96e6a3018bf56881b77c2005305ccdd3daad01`。
工具為固定Go／GUI映像內Python3.11.2；本項不執行原版，也不增加原版對拍信用。
原版檔案指紋及既有輸出事件沿規格033、035、036、038，這裡沒有新增DOS位址語意。

## 資料契約

繁中仍由既有13份TSV保存。簡中、日文、韓文各用一份UTF-8 TSV保存新譯文，
不再複製原版英文、原版來源資料或繁中顯示值。英文模式保持原版畫面與字體。
新譯稿放`text/game.zh-Hans.tsv`、`text/game.ja.tsv`、`text/game.ko.tsv`。

欄位固定為`locale、catalog、key、base_sha256、text、status、notes`，檔內各列locale相同。

| 欄位 | 契約 |
|---|---|
| catalog | 13個已知消費端之一，由`tools/language-catalogs.json`映射原檔。 |
| key | 沿原檔的來源鍵；複合變數用nation／caption／placeholder，海上字典另含role。術語及單一變數值以原鍵UTF-8的完整SHA-256作鍵，不在新檔重存原文。 |
| base_sha256 | 對完整原始TSV列作UTF-8、鍵排序及無額外空白的JSON後取SHA-256；包含來源、譯文及註記。基準列變動即需重新核對。 |
| text | 本語言的顯示文字。保留當次原版變數的槽位識別，不影響原版值或比較。 |
| status | translated表示已提供譯文；omitted只允許既有三筆空白冠詞，且必須有理由。partial檢查可讀draft，正式組裝不可使用draft。 |
| notes | 翻譯或轉換來源與必要說明，不是玩家可見文字。 |

三筆既有空白冠詞為`LABELS.TXT:@MISC:0x000000E7`、`0x000000EA`、
`0x0000029D`。日韓如需顯示對應詞可填譯文；省略時仍須明示原因。

## 驗證與建置邊界

- 固定13份基準檔雜湊、2006個唯一複合鍵及各列指紋。重複鍵、孤兒鍵、錯語言、
  過期基準、UTF-8錯誤、欄數錯誤、控制字元及未明示空白均拒絕。
- 正式組裝要求完整2006列。partial只報目前覆蓋，不生成可用語言包，不補繁中冒充日韓。
- `%STRINGn`、`%NUMBERn`、`%COUNTRY`、`%Fs`、模板變數及格式槽位保持多重集合相同；ASCII命名的
  大括號槽位及快捷鍵代碼也保留，例如`{person}`、`{SHIFT}`。`{}`、`^`、`~`
  與跳脫換行／定位控制保持結構。corpus的217筆NAMES.TXT複合欄保持項目數，
  各獨立數字欄、單字母命令欄及無命令代碼保持原值。
- 組裝時逐列複製原始metadata，只替換該消費端的顯示欄。現行parser相容檔只放
  忽略的workplace，固定寫入13份輸入與輸出雜湊。原檔不改寫。
- 文本組裝結果標為text-only，不能當作含字形、逐欄排版、靜態字圖、來源綁定及
  GUI驗收的可用語言包。正式切換仍須完整驗證後整包交換，依規格050執行。
- 無譯文維持原文並記錄。資料完整不增加普查shown，也不證明原版正常路徑已命中。

驗收以真實13表、錯基準及占位符反例、所有未翻譯欄逐格相同與原檔雜湊不變為準。
新遊戲字型仍待使用者選擇；語料製作不代替該決定。

READY審查：重新從13份唯讀原檔計算欄位、2006個唯一複合鍵及完整列指紋，
與固定清冊全等，沒有消費端或原版變更。後續實作不得把文本組裝升格為正式畫面切換。

READY補審：唯讀重新盤點，ASCII大括號標記為11種快捷鍵與`colony、person、n1～n4、w1～w3`。
217筆ASCII逗號複合列全部來自corpus的NAMES.TXT，draft沒有此類列。
因此複合欄守門必須套在實際corpus來源，不能只檢查draft。
模板`port-title`含三個實際U+3000全形空白，UTF-8為`E3 80 80`。
Python的repr會將它們顯示成`\u3000`，不能據此把譯文改成六個ASCII字元。
新增跳脫控制也會被拒絕，不能用改寫驗證條件讓誤寫通過。

## 2026-10-11文本驗收

正式來源：[登錄表](../../tools/language-catalogs.json)、[檢查與組裝器](../../tools/language_catalog.py)、
[真實語料測試](../../tools/test_language_catalog.py)、[簡體起稿工具](../../tools/build_simplified_catalog.py)。
譯稿為[簡體](../../text/game.zh-Hans.tsv)、[日文](../../text/game.ja.tsv)、[韓文](../../text/game.ko.tsv)。

| 語料 | 已提供／基準 | 限制 |
|---|---|---|
| 簡體 | 2006／2006 | OpenCC1.1.9 tw2sp起稿；39列異體字及抵制用語已核對，未完成逐句人工校對。 |
| 日文 | 1553／2006 | 1550筆譯文、3筆明示省略；尚缺corpus300、pedia153，不可組裝。 |
| 韓文 | 1553／2006 | 同上；與日文缺少相同453個來源鍵，不補繁中。 |

日韓已涵蓋全部385基本欄、8國家卡、8國家介紹、24開場變數、24教學／編輯器說明、
24海上欄、8靜態文字、256術語、1固定變數、66模板及173預設城名。
corpus目前565／865、pedia11／164。已提供譯文不代表母語校閱、正常路徑顯示或字形驗收。

confirmed文本契約：8項測試與12次實際命令通過。兩次簡體13表組裝逐位元組相同，
17963個非顯示欄位值與基準全同；繁中13表輸出與來源逐位元組相同。
英文只生成original_rendering清冊，不生成替換表。日韓正式組裝因缺453筆拒絕且不產生目錄。
固定OpenCC wheel重生起稿SHA-256為`3132b7428424ef0373ca03e8f898092010bd46e14b724befc6e23f1e51db5230`；
錯誤wheel被拒絕。13份基準表的整檔指紋不變。

本機總收據為`workplace/reports/goal186-display-hd/language-text-check-20261011/check.json`，
SHA-256為`3c21468c374aa233d401d5314fe1483bee9ac2f44a6779b2af6736882a7ae587`。
完整基準與工具指紋見登錄表及收據。OpenCC來源為[官方1.1.9](https://github.com/BYVoid/OpenCC/releases/tag/ver.1.1.9)
及[PyPI1.1.9](https://pypi.org/project/OpenCC/1.1.9/)，wheel及Apache2授權只作本機轉換依賴，未打包。

重驗時在既有`hr-go-ebiten:1.26.7-2.9.9-r1`容器內掛載本專案至`/repo`，基準來源唯讀，
只開放明確輸出目錄。執行：

```bash
python3 /repo/tools/language_catalog.py check --locale ja --catalog /repo/text/game.ja.tsv --partial
python3 /repo/tools/language_catalog.py compile --locale zh-Hans --catalog /repo/text/game.zh-Hans.tsv --output /repo/workplace/reports/new-text-check
```

輸出路徑須尚不存在，父目錄須已存在且屬目前使用者。未執行原版，不增加普查shown；
限定CONFORMED不涵蓋完整日韓稿、遊戲字型、逐欄排版、五語切換、GUI、HD或新版交付。
