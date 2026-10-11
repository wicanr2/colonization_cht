# 遊戲語言資料與來源隔離

狀態：限定CONFORMED於勘誤後的語料驗證與文本組裝。先前清冊有兩組引號合併列；接續新增14組句後現為2022筆，見[規格059](059-display-phrase-templates.md)。入口：[目標186](../goals/186-display-settings-and-gameplay-video.md)。
本規格先處理完整語料及建置資料，不授權未驗的字型、畫面切換或正式語言包。

## 首次來源盤點（已勘誤，現行數量見文末）

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

- 固定13份基準檔雜湊、2008個唯一複合鍵及各列指紋。重複鍵、孤兒鍵、錯語言、
  過期基準、UTF-8錯誤、欄數錯誤、控制字元及未明示空白均拒絕。
- 正式組裝要求完整2008列。partial只報目前覆蓋，不生成可用語言包，不補繁中冒充日韓。
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

本節保留首次語料驗收；接續補稿的目前數量見文末。

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

## 2026-10-11接續：日韓對話語料補齊

沿既有文本契約，日文與韓文各追加300筆，未改來源鍵、基準列指紋或驗證器。
新增來源為GAME.TXT的298筆、MAPEDIT.TXT的1筆及corpus內PEDIA.TXT的1筆。
兩語corpus均由565增至865筆，涵蓋殖民地、外交、貿易、國王接見及獨立戰爭起稿。
譯稿未經母語校閱，不增加正常畫面命中或普查shown。

| 語料 | 已提供／基準 | 本輪結果 |
|---|---|---|
| 日文 | 1853／2006 | 1850筆譯文、3筆明示省略；pedia正文11／164，尚缺153筆。 |
| 韓文 | 1853／2006 | 同上；缺少相同153個百科來源鍵。 |

confirmed文本檢查：既有8項測試通過，兩語`check --partial`各回傳0；
兩語`compile`均因「譯稿缺少153列」拒絕，沒有建立輸出目錄。
各語原有1553筆的完整位元組前綴不變，13份基準表仍符合登錄雜湊。
換行與強調標記錯位在匯入前修正，沒有放寬控制碼檢查。最後校核保留韓文
LOSING3原文「超過90%%」的界線；BUY0／BUY1保留英文of的比較寫法，不另指定金額用途。

本機收據為`workplace/reports/goal186-display-hd/language-dialog-check-20261011/`：

- `check.json`保留初次追加收據，SHA-256為`fc7b9efa426790b9b8f64e0ded45837a44a1907cb5be94a987dc45f5fcae2854`。
- `final-check.json`保存文字校核後的數量、來源與譯稿雜湊，SHA-256為`451c235d29407ba0d14e63f52c8a1bebafc37024a3a99561a444143399580697`。
- `cli-check.json`保存兩語檢查與不完整組裝拒絕結果，SHA-256為`5157f8260cfa9c219826810755577cd13e1a0394b107b69c315e6f43fb78562c`。

重驗使用既有`colonization-verification:20261007-runtime-r2`，映像ID前綴`c3457c559d90`，
Python3.13.15。專案唯讀掛到`/repo`，以UID/GID1000、無網路及有界資源執行：

```bash
python3 -B /repo/tools/language_catalog.py check --locale ja --catalog /repo/text/game.ja.tsv --partial
python3 -B /repo/tools/language_catalog.py check --locale ko --catalog /repo/text/game.ko.tsv --partial
cd /repo/tools
python3 -B -m unittest -v test_language_catalog
```

本輪只完成corpus補稿；百科、母語校閱、字型、逐欄排版、五語GUI、HD及新版交付仍待完成。
沒有執行原版或修改已發布Release。Issue #62維持OPEN，本輪只讀核對遠端現況。

## 2026-10-11接續：日韓百科與全文組裝

本節為目前文本狀態，前兩節保留補稿前的驗收歷史。日文與韓文各追加153筆百科正文，
涵蓋38筆建築、16筆貨物、25筆建國元勳、27筆職業、25筆地形及22筆單位。
譯稿依既有英文與繁中對照撰寫，未經母語校閱；沒有新增原版文字或圖像副本。

| 語料 | 已提供／基準 | 本輪結果 |
|---|---|---|
| 日文 | 2006／2006 | 2003筆譯文、3筆明示省略；corpus865／865、pedia164／164，缺稿0。 |
| 韓文 | 2006／2006 | 同上；全部來源鍵、基準列指紋、槽位與排版控制結構檢查通過。 |

confirmed文本契約：既有8項測試、兩語全文檢查及各兩次13表組裝全部通過。
各語兩次輸出含清冊逐位元組相同，17963個非顯示欄位值逐格與基準相同。
各語原有1853筆的完整位元組前綴保留，13份基準表仍符合固定登錄雜湊。
匯入前將韓文人數範圍改用文字表達，避免誤用控制符號`~`；日文殖民地名稱
沿現有術語表統一為「植民地」。沒有放寬驗證器或改動原版規則。

| 檔案 | SHA-256 |
|---|---|
| `text/game.ja.tsv` | `72be390204c8348f8b0ec031985e01a51c220dbcb9b8e3fd34a6266894272e92` |
| `text/game.ko.tsv` | `1138ec60c99a9f7077fbcf886a1096cb31864105713240068e24f1ffd3ef623b` |

本機總收據為`workplace/reports/goal186-display-hd/language-pedia-check-20261011/check.json`，
SHA-256為`fc3aad3fbdffc3b9fd26fd0e9b48a89056363ca951bd83a31266876fe06ab236`。
收據保存來源、工具及譯稿指紋、七次命令的回傳碼、逐欄比對與重複組裝結果。
文本相容檔在同目錄的`compiled-ja`、`compiled-ko`及各自`-repeat`，全部只留本機。

重驗沿用`colonization-verification:20261007-runtime-r2`，映像ID前綴`c3457c559d90`，
Python3.13.15。來源唯讀掛到`/repo`，只開放明確的workplace輸出目錄，
以UID/GID1000、無網路及有界資源執行：

```bash
python3 -B /repo/tools/language_catalog.py check --locale ja --catalog /repo/text/game.ja.tsv
python3 -B /repo/tools/language_catalog.py check --locale ko --catalog /repo/text/game.ko.tsv
python3 -B /repo/tools/language_catalog.py compile --locale ja --catalog /repo/text/game.ja.tsv --output /repo/workplace/reports/new-ja-text-check
python3 -B /repo/tools/language_catalog.py compile --locale ko --catalog /repo/text/game.ko.tsv --output /repo/workplace/reports/new-ko-text-check
cd /repo/tools
python3 -B -m unittest -v test_language_catalog
```

每次組裝使用新的輸出路徑，父目錄須已存在且屬目前使用者。全文起稿與文本組裝
已完成；母語校閱、字型、逐欄排版、正式五語GUI、HD及新版交付仍未完成。
沒有執行原版、增加普查shown、修改正式前端或已發布Release，也沒有寫入遠端Issue。

## 2026-10-11字型定案與四語字集驗證

使用者看過真實字型樣張後，選定繁中TC、簡中SC、日文JP、韓文KR四種Noto Sans CJK。
各語言的文字與保留英數使用同一地區字型；英文維持原版字體。固定Sans2.004版本、
OTC face索引、字型與OFL指紋及容器重驗命令見[字型來源](../../font/README.md)。
這次決定適用於目標186，尚未修改正式圖集或前端。

confirmed碼點覆蓋：[檢查器](../../tools/check_language_font_coverage.py)從固定13表及三語
完整TSV讀取2006筆遊戲文字，另讀17筆設定介面。每語均納入95個可見ASCII，
保守保留模板中的文字碼點，並展開Unicode跳脫碼；沒有把模板標記刪除後縮小字集。
來源鍵、基準指紋、譯稿與工具雜湊均保存於本機收據。

| 語言 | 遊戲所需碼點數，含ASCII | Noto遊戲缺字 | Noto設定介面缺字 | Cubic遊戲缺字 |
|---|---|---|---|---|
| 繁中 | 1833 | 0 | 0 | 0 |
| 簡中 | 1809 | 0 | 0 | 8 |
| 日文 | 1386 | 0 | 0 | 0 |
| 韓文 | 906 | 0 | 0 | 798 |

`fc-query`按固定face索引讀取Unicode對照。另以Pillow實際渲染每語全部所需碼點，
均與該字型的缺字字模不同；Cubic所缺簡中8字及韓文798字則與其缺字字模相同。
此檢查只證明目前字集具有對應字形，沒有證明區域字形品質、整段文字塑形或母語校閱。
執行時變數若產生ASCII以外的新字元，仍須另行盤點。

[六列命令欄原型](../../tools/preview_language_field_layout.py)引用規格035既有正常路徑
量測與審查收據：原版cap5、最小行距8、安全區`[80,12,159,77]`，放大4倍後為316×260。
工具直接讀六個既有TSV來源鍵，試22至15px，按實際墨跡高與放大後20px原版字高的
差距選候選。四語均為18px、最大墨跡高20px；保留每列基線座標，左／右留4px。
24列實際墨跡均未超過安全區或下一列，最長列為`MENU.TXT:0x00000384`。
兩個Fortify同文來源尚未分辨，來源鍵僅作模板導覽，沿用原量測的限制。
原型未渲染停用色與熱鍵色，不是正式GUI收據；其他欄位須各自量測，不能套用18px。

兩個工具各重跑一次，JSON與PNG逐位元組相同。錯誤字型／授權／量測／審查指紋、
既有輸出、workplace外輸出及不存在的父目錄等10項輸入均拒絕，沒有覆寫來源或正式圖集。

| 本機收據，皆位於`workplace/reports/goal186-display-hd/` | SHA-256 |
|---|---|
| `language-glyph-check-20261011/coverage.json` | `8ddce673ba704cf37b9f5198d316b0e7e025ca0db909f0c2d4fb3c0847cb6aaf` |
| `language-layout-preview-20261011/layout.json` | `2023597c649abd7570a9e20737410c7635d8029a10e8aa6cbfcd8897114f755b` |
| `language-layout-preview-20261011/compact-orders-noto.png` | `4b109da4fcf00af0a13901790eae7d2b195ba52fea55b8c3d3a47a2502727a9c` |
| `language-font-decision-check-20261011.json` | `0ff40244d7fc4f9953243ead34990d20532fcb2b18f2b49d53a8115f583ca30d` |

原版欄位量測檔SHA-256為`35cecc614308c691b82b817b12e4717486986a5a39b95adf67714a1c743870e9`，
原審查檔為`dc0a9b0ae43c8953d2e8845066e682e20df735b07ba460f2482eb9ef04ef32f8`。
本節不擴張規格053的限定CONFORMED範圍；字形烘製、逐欄READY規格、五語GUI、HD
及新版交付仍待完成。本輪沒有執行原版或增加shown。

## 2026-10-11勘誤：基準引號、遺漏來源鍵及消費端格式

先前2006筆／corpus865筆的清冊使用CSV相容讀法，將原文未閉合引號當作欄位引號。
兩組實體列被合併；舊收據與雜湊保留作為錯誤讀法的歷史，不再證明現行文本完整。
原始13表及正式Go的實體列讀法沒有此變更，已發布繁中不因本次勘誤改寫。

| 錯綁鍵 | 譯文實際所屬、先前遺漏的鍵 |
|---|---|
| GAME.TXT:@CHIEFHOWDY:0x00006E3E | GAME.TXT:@CHIEFGUIDES:0x00006F2F |
| GAME.TXT:@WARMANLY:0x0000E83B | GAME.TXT:@THREATS:0x0000E8D7 |

confirmed：corpus原檔1483f5ce585c43337dbab8118928cff783af936682493e1fc5e5f2b6554c2947，
實有867列；13表共2008筆、1837種繁中顯示值。實體列以tab切欄，引號為原文字元，
只有新語言編輯檔使用標準CSV引號讀寫。基準已固定整檔雜湊後才使用實體列讀法。
給Go消費端的相容檔保持同一讀法，不產生跨列引號或重寫來源欄；譯文含實體tab／換行時拒絕。
原始來源、控制碼與遊戲資料均不變。

三語各將兩筆原譯文移回實際來源鍵，再為原鍵補兩筆譯文；既有2006筆譯文內容全保留。
各語現為2008筆，2005筆譯文與3筆明示省略。基準列指紋依實際完整欄位重算，
完整聯集SHA-256為91bfc5e32a369f8c0a8654fe429a9f07ca386f16ec8fc12dde36d2a7eedbc4c8。
只更新語料登錄與新語言編輯稿，13份原始繁中表的整檔雜湊不變。

10項真資料測試通過，新增四個實體鍵、單邊引號、全部三語輸出及正式Go讀法的反例回歸。
五語文本各兩次組裝全等；四語52個文本檔由正式來源抽出的splitTSV讀回各2008筆，
各語17981個非顯示欄位與原始實體列完全相同。英文只產生原版顯示清冊。
此驗收只證明文本格式與來源隔離，未增加正常GUI、原版對拍或完整五語切換信用。

| 本機收據（相對workplace/reports/goal186-display-hd/） | SHA-256 |
|---|---|
| language-runtime-audit-20261011/tsv-check.json | 05faf64b5d21a12e1c1a2de12a7afe00db50a7d33538dc5fd10ec667a285b2af |
| language-runtime-audit-20261011/tsv-migration.json | c2d512c72279681308d2865800338c17457218ec1d32b435d2a8a35bf881a177 |
| language-flat-tsv-check-20261011/check.json | 991ac85dbe10472db6c7e5308c3c389535d4ce8900ba4d67f75500eba877cb2b |
| language-flat-tsv-check-20261011/go-consumer-result.json | 9140dcd7ba61bdc261ed0829a6bebdd46349de70c574614b125011eeedc4a452 |

重驗仍使用本頁既有check／compile與unittest入口，完整性數量改為2008。
Go收據以同一固定Go1.26.7映像，直接抽取受版控dialog_overlay.go的splitTSV，
來源函式、測試程式與結果保存在上述language-flat-tsv-check目錄。
首次完整Noto原型因使用舊清冊停止，ABORTED.json明示不得套用；重新烘製使用新的r2目錄。
母語校閱、固定中文片段、每欄排版、完整語言包與HD仍未完成。
