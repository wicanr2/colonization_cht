# 對話模板以原始來源辨識

狀態：READY，僅來源辨識與模板守門。入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)。
只處理兩個已取證模板的來源辨識，沿用[規格035](035-dialog-overlay-draft.md)
與[規格036](036-line-list-and-centered-text.md)的字格、名稱角色、排版及回退契約。
不授權新欄位、字級或完整語言包。

## 證據

confirmed：正式dialog_overlay.go仍以繁中顯示文字判斷兩個特殊分支，
導致來源及占位符相同的簡中、日文、韓文無法走既有辨識路徑。
來源盤點為goal186本機language-runtime-audit-20261011/check.json，
SHA-256為0840ea0dc67d6410c5917640f93a32d6f1dfd98eac08ef086d1e018a7c880475。
本規格使用Go1.26.7與既有合法GAME.TXT，不重新推測原版變數分界。

原版GAME.TXT的SHA-256為67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a。
下表均為檔案偏移，不是CPU位址；原版正常路徑與字格證據沿規格035對應章節。

| 來源鍵 | 偏移／bytes | 片段SHA-256 | 既有契約 |
|---|---|---|---|
| GAME.TXT:@COLONYUNIT:0x00009A33 | 0x9A33／31 | 98b75b596028b5fb6713ca8044c29433a0af0eaad291bba5cfd3a6780577b90f | 同一強調群組的兩個相鄰槽位，按已顯示完整UNIT名稱匹配；不能猜分界或借一般術語。 |
| GAME.TXT:0x000002C8 | 0x2C8／25 | ad915d9da6889a4865c513ae4f25420af80af59cd87e4387f727236d671ce56b | 唯一已驗單行居中標題，保留開頭兩個段落碼及原版檔名輸入。 |

## 修正契約

- 完整名稱分支只依既有來源鍵及正規化原文辨識，合併槽位不依譯文字面值。
  譯文仍須只有一個{%STRING0%STRING1}群組且恰有兩個槽位；不符整則回原文並記錄。
  名稱仍須命中已綁定UNIT表，未知名稱、純數字或缺來源綁定不翻譯。
- 居中標題仍先核對原始檔案、偏移、長度及片段雜湊，再核對來源鍵與原始片段。
  譯文須有兩個開頭段落碼與非空單行正文；多餘段落碼、控制符或空文不載入。
- 其他來源與一般變數守門不變。譯文只來自既有TSV，不在程式複製四語顯示文字。
- 繁中現有模板及畫面須保持相同；四語模板通過不等於四語正常GUI或即時切換。

## 驗證

在既有Go／Ebiten映像內組裝正式來源。對真實GAME.TXT及四語實際TSV驗證：
整個名稱、來源限定、術語污染、缺綁定、分離或重複槽位與錯誤強調群組；
居中標題的四語載入、錯誤來源鍵、缺段落碼、空文、換行及多餘控制碼。
再核對既有繁中模板及代表性原版輸入重播。未完成正常畫面驗收前保持READY。

2026-10-11審查：兩筆來源指紋、原版正常路徑、完整名稱與居中段落契約均已由
規格035 READY／限定CONFORMED取證，四語現行譯稿保留同一槽位及段落結構。
新增測試在修改前重現三語分支未載入與不合規槽位未拒絕，原版及來源表未改。
據此授權移除兩個繁中顯示值比較，增加結構拒絕；不改幾何、字形或原版狀態。

## 2026-10-11正式來源與有限驗證

正式dialog_overlay.go的SHA-256為b93dcf45c424b8aac175f71da0e05d54782d9ccc36774fdd1ac7f0bbd69e8a50。
363項Go測試零skip，go vet與正式建置通過；四語模板、原始來源限定與結構反例均通過。
Go語法樹確認兩個繁中判斷已移除，已知固定顯示片段剩六處；此盤點不證明全部語序假設已移除。
圖集載入函式與字型型別的宣告位元組均與前版相同，三個研究組裝器的來源綁定已重新審查。

新正常冷啟動含17筆實際DOS輸入，走過地圖檔名框、Escape取消及重入，共七張同步GUI。
修正版與前版重播的七張解碼RGB均與GUI相同，已目視標題及保留檔名。
修正版、前版與原文控制重播至90200000步，三側完整CPU／RAM／VGA／DAC／時鐘及WAV全同，
沒有新存檔。這只證明三個重播之間相同，不能替代GUI完整RAM比較。

未知：GUI完整RAM與三側重播在20bit線性位址0x67688有一個byte不同，
其餘CPU、VGA、DAC與時鐘相同。移除checkpoint取樣後仍重現，原因尚未確認。
未放寬完整RAM門檻，收據標為LIMITED_GUI_RAM_DIFFERENCE_UNRESOLVED。
本規格保持READY；單位標題尚無本輪新GUI，四語逐欄、完整切換與shown皆未增加信用。

| 本機收據（相對workplace/reports/goal186-display-hd/dialog-source-identity-20261011/） | SHA-256 |
|---|---|
| tests.json | 338089d9a605d21a75a8b4efbc17e24c8aa7780fd0bb8f21c3911328ef9c216c |
| source-check.json | 88e872bfe611f52f03f0d27da0bd5d6ed24836c363c273e73dbcc57bf0d9800c |
| ram-diagnosis.json | f87b8467583909c51afb206466067f882508b93764d810a86d5e50ca76843c16 |
| colonization-window | bcf4e14e3f5e2c8fcec22861dce932ee258f758746eaa371c933f59e66ed25c5 |

重生入口為正式build_window_prototype.py與dialog_overlay_test.go；原版只讀，
完整Go測試沿規格056的固定字型、圖集與實測字格，新增測試讀取本頁兩筆真實來源與實際四語TSV。
GUI沿目標185已驗play_map_title_formal.py，四個原樣私用工具與指紋保存在本輪目錄。
check_replays.py保留完整RAM失敗，diagnose_ram.py核對三側與解碼RGB並輸出上述限制收據。
