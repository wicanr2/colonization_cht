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

## 現行譯稿核對入口

2026-10-04 使用者決定先完成文字翻譯，最後做代表性抽樣對拍。翻譯分母仍以
`tools/text_inventory.py` 重算；已顯示數與待驗數不能當成缺譯數。

[`tools/validate_text_catalogs.py`](../../tools/validate_text_catalogs.py)直接核對現行十份來源清冊，
另檢查字串模板、靜態圖譯文、定稿術語與變數譯名。使用專案 TSV 的無引號方言，
避免原文雙引號吞掉資料列。檢查來源雜湊、鍵、欄數、占位符、樣式、熱鍵與字型缺字；
只允許已登錄的三個冠詞省略。這些結果不授權新的畫面覆蓋或原版行為。

在 `colonization-verification:20260930-r1` 容器內，將合法原版目錄掛 `/game` 唯讀，
字型依 [`font/README.md`](../../font/README.md)掛 `/font` 唯讀，工作樹掛 `/repo` 可寫：

```sh
python3 /repo/tools/validate_text_catalogs.py --game /game --font /font/Cubic_11.ttf \
  --report /repo/workplace/reports/goal160-coverage/current-text-validation.json
```

本輪重算收據在 `workplace/reports/goal160-coverage/20261004-inventory-summary.json`，
來源明細留同目錄的 `20261004-inventory-detail.json`。現行譯稿核對收據為
`20261004-text-validation.json`；六個驗證器反例由同目錄的
`20261004-audit-checks.py`重生，結果為`20261004-audit-checks.json`。
正常流程七點抽樣留`20261004-sample/`，入口為`prepare.py`、`run-zh.sh`、
`run-control.sh`與`check.py`，結果為`summary.json`。初始存檔與所有原版畫面只留本機。

本輪結果：遊戲畫面3561行全部已建檔，3558行有譯文，3行已登錄冠詞省略；
十份現行來源清冊1684鍵全部來源核對通過，1681鍵有譯文，字型缺字為0。
六個反例確認缺譯、來源雜湊、占位符、重複鍵與刪除語料會拒絕，缺原版回77。
正常流程七點中文／原文重新重播通過，並與既有正常GUI截圖逐像素相同；
未重新錄GUI，不增加已顯示數。當次港口單位標題仍原文；後續三類欄位接線與十點抽樣見[目標181](181-colony-remaining.md)的`20261004-port-fields`。

再次抽樣時，`prepare.py --output <同工作區內尚未使用的目錄>`建立乾淨工作存檔；
依序執行該目錄的兩個`run-*.sh`，再用原`check.py --reports <新目錄>`核對。
原版及字型掛載、UID/GID、資源上限與清理沿專案Docker規則。
本輪最終權限與工作樹衛生收據為同工作目錄的`20261004-hygiene.json`。


## 2026-10-04 對話訊息接線補審

本機入口`workplace/reports/goal181-colony-rest/20261004-dialog-links/`，先由`prepare.py`建立候選，
`candidate/dialog_diagnostic_test.go`核對現行整段與逐行模板的歧義，不以歷史缺譯紀錄當成現行缺口。
正式接線前仍經規格035／036 READY；字級沿實際原版欄位量測，最終採正常玩家輸入代表性抽樣。
原版事件、畫面、存檔與字模只留workplace。

現行診斷另保存`f1-correction.json`：完整F1提示已以18px啟用，兩次容量拒絕只來自cap1局部重繪。
重生資料為`20261004-port-fields/raw-fields.jsonl`與`sample/zh.json`，不把命中紀錄中的局部拒絕當成完整欄位缺口。

本批`sample/check-v1-scheduled-step.py`與`check-v1-failure.json`保留預定／實際抓圖步數錯配；
修正比較器後另發現右側人物區差異，整張舊GUI對拍尚未通過，不移除該限制。
`status-audit/`為原墨跡及遮擋清底診斷，輸入仍採同一份正常GUI實際輸入；
只輸出來源與原版畫布，不把診斷輸出當正式中文收據。入口為`prepare.py`、`run-observer.sh`與`observer-build/`。

`status-audit/prepare.py`第二版另輸出通用字串來源與每次原版寫入，包括同色寫入，保留第一版。
`same-color-erasure.json`將學習圖右側132個差異點全部對回海上／通用字串的舊墨跡清底。
候選入口`prepare-guard.py`與`guard-candidate-v3/`，其寫入世代及完整恢復測試只證明候選；
`prepare-preview.py`建立`guard-preview/`，每幀保留來源／生命週期，僅在代表性檢查點合成。
這是可丟棄原型，通過後仍須READY審查及正式抽樣，不冒稱正式GUI驗收。

第三版觀測器另擷取`observer3.*.primary.idx`，132差異點在主畫布及VGA全部相同。
寫入世代原型目前沒有改變學習抽樣，保留DRAFT；`guard-preview/provenance-check.json`只檢查內部見證，不能當圖像修正通過。
後續直接核對原人物資產的覆蓋範圍；[mpskit](https://github.com/institution/mpskit)為已明列支援Colonization的格式工具，
只作本機研究，程式來源／版本／授權保存於`status-audit/mpskit-source/`，原版人物與解碼輸出只留同一診斷區。

### 本批抽樣結果與重生入口

`sample/summary.json`已通過十點抽樣，SHA-256 `2b8b8924456314e3b1e05092d782e2b5ebaec8e701c0fe448c5e506f272a8e1a`；原住民學習兩列限定CONFORMED，完整原版與唯一自動存檔相同。來源、字級及範圍見規格036本日附記。人物5503個不透明像素完全不變，整圖137個舊英文清除點均有同次印前值證據；原同色誤擦假說由規格032本日勘誤撤回，不修改正式清底。

`status-audit/native-source/`保存`metadata.json`、`sprite-0.png`、`opacity-check.py`與`opacity-check.json`。原版IND4A0.SS、固定mpskit來源及其授權只供本機研究，不進正式程式或發行包。`opacity-check-v1.py`／`opacity-check-v1-failure.json`保留132點窄範圍分析漏掉x=242五點的比較器失敗；`sample/check-v2-outside-options.py`／`check-v2-failure.json`保留舊GUI區外拒絕。新的驗收逐點核對原墨跡與人物透明區，沒有放寬成整個矩形。

在既有驗證映像內，專案掛`/repo`可寫、原版目錄掛`/game`唯讀，沿UID/GID、資源與逾時規則執行：

```sh
batch=/repo/workplace/reports/goal181-colony-rest/20261004-dialog-links
python3 "$batch/status-audit/native-source/opacity-check.py" --batch "$batch" --game /game
python3 "$batch/sample/check.py" --reports "$batch/sample"
```

原版重播入口保留`sample/run-zh.sh`、`sample/run-control.sh`及`selection.json`；重跑前用`sample/prepare-replay.py --output <本批尚不存在的直接子目錄>`建立兩側空存檔目錄與新腳本，再執行新目錄的兩個run腳本及check.py；不重跑會建立候選及寫文件的舊prepare.py。prepare-replay.py的--dry-run只核對來源與路徑，不寫入。預定步數與實際捕捉步數以唯一標籤對應，兩側均嚴格核對。

`guard-preview/preview-review.json`記錄寫入世代原型沒有圖像效果且本例不需要，未採用。最終Docker、擁有權、原版版控邊界及文件檢查由本批`hygiene.json`保存。全語料核對收據`text-validation.json`維持3561已建檔、3558譯文、3冠詞省略及零缺譯；79組接線不當成79種正常畫面完成。

## 2026-10-04 事件版畫多色標題接線

本機工作區`workplace/reports/goal181-colony-rest/20261004-woodcut-titles/`，對應Issue #61與規格038的多色標題缺口。`prepare-observer.py`從現行公開組裝入口建立唯讀觀測器，`run-observer.sh`重播既有colony-v3正常GUI實際輸入，只記錄多色字串的字元、墨跡、印前／印後值及原版畫布。正式譯文沿text/既有WOODCUT來源，不重譯或修改原版。

`observer-build/`、`observer-source.json`、`observer.multicolor.jsonl`與observer畫面／存檔是本機證據；多色拆層與中文字級仍待驗，未READY前不進正式程式。此批先處理實際接線缺口，最後做代表性抽樣，不逐標題重跑完整矩陣或普查。

`evidence.json`確認三則原版完整來源與原版不變性；`preview-layout.py`／`layout.json`及候選的`woodcut-layout.json`保存三欄30px、三色互斥遮罩及51組容量投影。17個來源只接既有譯文，不代表17種正常事件皆已驗。完整多色dump另壓縮為`observer.multicolor-full.jsonl.gz`，原始觀測與壓縮均只留本機。

第一輪`sample/`已完成正常輸入中英重播，原版十一點、完整終點與存檔相同，但有舊狀態欄清底點，未通過圖像驗收。`check-v1.py`／`check-first.log`保留關閉即expired的比較器假設；`first-title-events.json`顯示實際為suspended，再由下一標題superseded。修正比較器後`check-second.log`仍拒絕安全區外像素，沒有放寬核准區。`early-visual-audit.json`保存座標及原圖／中文色值。

`prepare-modal.py`建立三種已驗事件頁的候選，`modal-ready-review.json`為160項Go／實際VGA／來源與改頁拒絕審查。`formal-modal/`是第一版事件頁中間物，包含公開組裝器的`stable-build/`。`prepare-revised-sample.py`當時建立乾淨`modal-sample/`，沿用第一輪同輸入原版收據，只重新執行修正後中文側。舊重播入口為`modal-sample/run-zh.sh`；對應比較命令為：

```sh
batch=/repo/workplace/reports/goal181-colony-rest/20261004-woodcut-titles
python3 "$batch/sample/check.py" --reports "$batch/modal-sample" \
  --formal "$batch/formal-modal" --baseline "$batch/sample"
```

命令須在既有驗證容器，依專案UID/GID、資源與唯讀原版掛載執行。原收據不覆寫；最終程式與抽樣入口如下。

### 最終抽樣與重跑

現行程式為`formal-modal2/colonization-window`，指紋`aae282aa3dccea70ab10773bf04f6f19bef4e882beb2810ab5ca1c920d5fd38d`。`final-sample/`沿用同一原文控制，重新從空存檔目錄執行正常GUI實際輸入；十一點、完整原版與COLONY09全等。三個標題安全區內背景及中文遮罩、區外完整原圖、關閉／後續畫面全部通過逐像素核對，摘要指紋`3bbaebeab6dd8371c8fa8f954fc0ffa608b911e3bf3da70091e7f0d05a1fde7b`，三則限定CONFORMED見規格038。17來源接線與51容量投影不當成17種正常事件驗收。

`sample/check-pillow.py`及`final-sample/exact-mask-failure.json`保留透明度取整造成的假失敗。`compositor-review.json`記錄Go1.26.7標準庫原始碼指紋、196608組公式核對及兩版三張中文圖相同，撤回舊對話框保留區造成此次拒絕的假說。正式檢查器不採像素容差，只按Go整數合成契約重算；首輪清底斑點由原版VGA底圖修正的證據仍保留。

在上述Docker契約內執行：

```sh
batch=/repo/workplace/reports/goal181-colony-rest/20261004-woodcut-titles
python3 "$batch/sample/check.py" --reports "$batch/final-sample" \
  --formal "$batch/formal-modal2" --baseline "$batch/sample"
```

再次重播可用`prepare-sample.py --output <本批尚不存在的直接子目錄> --formal "$batch/formal-modal2"`建立兩側空存檔，再依序執行兩個`run-*.sh`，以同一check.py指定新`--reports`、現行`--formal`與第一輪`--baseline`。若只重跑中文側，使用`prepare-revised-sample.py --output <新子目錄> --formal "$batch/formal-modal2"`；該入口明確記錄重用原文控制的來源與指紋。原版圖像、原文觀測、字模、RAM與存檔只留本機。`hygiene.json`保存本批最終Docker與擁有權檢查；三平台建置中間物另見[目標182](182-platform-build-preflight.md)。

`build-summary.json`記錄現行正式／公開入口的二進位、來源、測試、字模與平台報告指紋；`worklist-verify.log`保存本機待辦核對結果。它們只補驗證索引，不代替GitHub Issue現況，不授權關閉Issue或發布。全語料核對沿前批`20261004-dialog-links/text-validation.json`，譯稿與字型未變，不重跑完整矩陣或普查。
