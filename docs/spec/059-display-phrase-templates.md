# 完整語言包的組句資料

狀態：READY，限定既有來源的組句與守門。入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)。
將現行顯示組句移至既有string-templates.zh-Hant.tsv及三語game譯稿，沿用原格式。
不修改原版TXT、規則、存檔、資料角色或欄位幾何。

## 證據與範圍

confirmed：fc040ba的live_menu.go與string_overlay.go仍在程式組合日期、海上狀態、
VIEW側欄、存檔描述及港口／航行頂列。來源、角色及字格契約沿
[規格032](032-sea-menu-and-status-draft.md)、[規格035](035-dialog-overlay-draft.md)及
[規格038](038-string-overlay-draft.md)的已驗欄位。本規格只搬移顯示詞序與標點，
不擴張原版輸入比對、場景、位置、字色、字高、名稱角色或玩家輸入守門。

原版GAME.TXT、NAMES.TXT與LABELS.TXT的SHA-256依序為
67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a、
4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061、
e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204。
原始位移、片段及正常路徑沿上述規格，不能由組句模板推定其他遊戲資料角色。

| 新增模板ID | 槽位 | 使用入口 |
|---|---|---|
| display-sea-gold | w1,n1,w2,n2 | 已驗Gold／Tax兩標籤與原數值。 |
| display-sea-location | w1,n1,n2 | 已驗海上座標，數值原樣。 |
| display-sea-moves | w1,w2 | 移動標籤及原版剩餘值。 |
| display-sea-inbound | w1,w2,w3,w4 | 已驗國籍、船種、方向標籤及港口。 |
| display-sea-date | w1,n1 | 已驗季節與年份。 |
| display-sea-unit | w1,w2 | 國籍縮寫與單位名稱。 |
| display-sea-terrain | w1 | 已驗地形括號列。 |
| display-sea-goods | n1,w1 | 貨物數量與名稱。 |
| display-view-location | w1,n1,n2,n3 | VIEW座標及未知尾值，尾值不解讀。 |
| display-view-tribe-land | w1 | 已驗TRIBES主名稱。 |
| display-save-description | w1,person,w2,w3,n1 | 難度、玩家原名、國籍、季節、年份。 |
| display-port-ship-header | w1,w2,w3 | 已驗國籍、船種、港口。 |
| display-voyage-go-to | w1 | 已驗目的地。 |
| display-voyage-ship-header | w1,w2,w3,w4 | 已驗國籍、船種、航行狀態、目的地。 |

## 契約與驗收

- display-前綴只供既有來源守門通過後的組句；一般字串比對器不得使用它解除其他欄位的歧義。
- 文字與標點只在TSV。載入核對模板ID唯一、完整14筆與槽位多重集合；缺件、
  重複、未知ID、缺槽、額外槽或控制碼拒絕。沒有組句資料時保留原文，沒有程式內譯文回退。
- 字詞仍沿既有來源角色查譯。數字只保留ASCII十進位；玩家名稱仍沿原ASCII及控制碼限制。
  代入值不再被解讀成模板或強調碼。
- 繁中14則輸出須與原組句相同；新語言詞序由完整譯稿決定。
  教學Caravel另從已綁定的術語表取得定稿譯名，不在程式複製顯示文字。
- 語料仍13表，增加14筆至2022；既有2008筆譯稿內容不變。
  重新綁定字串圖集並乾淨重生，不能沿用舊表雜湊冒充新資料。
- Go驗真實四語TSV、已驗原始名稱角色、未知角色／位置／樣式回退及一般入口隔離；
  再驗代表性正常GUI與原版完整狀態。沒有逐欄Noto及GUI證據，不增加完整五語或HD信用。

2026-10-11審查：逐分支核對fc040ba的原始正規式、名稱角色、場景與回退，
14則繁中格式均可由現行程式直接重生；移動剩餘值仍是原版字串，不改成推算數值。
新增列沿用既有模板及三語譯稿格式。只授權資料移出、專屬入口隔離與既有欄位接線，
不授權變更語言顯示範圍或以母語校閱、Noto字形、正常畫面已驗為由外推完成。

## 2026-10-11接線與抽驗

組句載入與代入入口為[display_phrases.go](../../tools/display_phrases.go)，
[四語及回退測試](../../tools/display_phrases_test.go)直接讀實際譯稿。
原版來源、角色、位置與樣式判斷維持原契約；display-列不加入一般模板。
教學Caravel從terms表的ship類別唯一鍵取得，烘製器使用相同來源。
Cubic既有字串圖集與教學字模已重新綁定；舊發行包與舊驗收收據未改。

438項Go測試零skip、go vet及正式建置通過。五語各兩次文本組裝全等，
四語每語18051個非顯示欄位逐格相同，原有2008筆外語譯稿位元組前綴不變。
正常存檔路徑八組設定GUI及兩次重開通過；25筆實際DOS輸入重播至76200000步。
新程式、fc040ba前版與原文控制的CPU、完整RAM、VGA、DAC、時鐘、存檔及WAV全同，
兩個翻譯重播的終點RGB亦與GUI相同。前版沿自身舊文本及字模，不餵入新模板冒充比較。
[重播檢查器](../../tools/check_display_settings_replay.py)新增可選前版啟動器，並比較解碼RGB。

本機收據皆位於workplace/reports/goal186-display-hd/display-phrases-20261011/：

| 收據 | SHA-256 |
|---|---|
| go-check.json | cfebf8da48bdfcff5aef6064a108393328ea1f5d1fc5188edb2b84ef7e0012ef |
| text-rebuild-check.json | b5c5dd480bf07e9acb1f597ece1e60be77afd5e481cc48774be025cff366a022 |
| gui/check.json | 0c5e5b44cb011fccc24502141c6c8e4d89fd2fae595aa6e8e7616a42f7913494 |
| replays/check.json | 6d67c05efef516f384984969b3cfe8d9c61421f600bea70b5d9ea561bb4fb874 |
| catalog-additions.json | 2d96113d027aedd9dfd090eeb5953b8a61d4759fb6e6aecbd1ad0f5bbe62d790 |
| bundle/masks/string-atlas.json | 765f35727e3ad40a5b89c000944b5487b66195cb0522b3442764e2b560a4b3ae |
| bundle/masks/help/GAME.TXT-@TUTORIAL1.json | 45c761469c251377ab9785320a2f5787460ac43e43e4eb4f5cc47e0af89f9009 |

正式程式SHA-256為740a7f08ff6a91b5a117224340b08918fe281b329909f1cce6c66051df48c371，
Go測試收據為fcad4afb17f05f45b6b93324fed60c756e8f189a269cdb0bbdbcdc83e7237cf0。
來源登錄489f2aff5d0bba6ba4795571b3f5405e86ce198b295dba0bec3fb7538b2642ac。
工具為hr-go-ebiten:1.26.7-2.9.9-r1及colonization-verification:20261007-runtime-r2；
Go1.26.7、Python3.11.2、Pillow9.4.0、FreeType2.12.1。原版及dosgolem版本沿規格058。

規格保持READY。此批正常GUI抽驗繁中既有欄位，沒有逐項驗完14種情境、
四語Noto排版或完整切換；教學字模已重生，定稿船名的新正常GUI仍待抽驗。
冷啟動RAM的歷史未知限制留在規格058，不由本次存檔路徑通過推定已解決。
