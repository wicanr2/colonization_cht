# 目標 058：譯文語料覆蓋與玩家視窗

狀態：completed（本輪語料與有限視窗原型；全遊戲中文化未完成）<br>
日期：2026-09-22<br>
Issue：[#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#10](https://github.com/wicanr2/colonization_cht/issues/10)、[#26](https://github.com/wicanr2/colonization_cht/issues/26)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)

## 起點

[目標 057](057-menu-coverage-and-interaction.md)已讓五列主選單在原版執行中顯示中文。
版本化譯稿有50筆，其中五筆完成正常路徑顯示驗證；其餘不能因已有譯文就算畫面完成。
使用者已確認 Cubic 11 24px、4倍畫布，並要求派翻譯子代理推進全遊戲中文化。

## 本輪工作

1. 翻譯子代理核對並補充來源可追溯的繁中TSV。每筆保留檔案SHA、原始位移、長度、
   片段SHA、占位符與狀態；不能把未證實的字串位置升格成執行期訊息鍵。
2. 語料子代理盤點合法DOS原版的文字記錄與靜態文字候選，建立可重播的分母與未譯／
   未顯示清單。原文全文、解包檔及畫面只留本機workplace。
3. 工程子代理依窄規格製作Linux／Xvfb互動視窗原型，送原生DOS滑鼠事件，沿用已確認
   的五列輸出合成。正常玩家路徑要能以實際視窗點主選單至難度畫面，並比較原版狀態。
4. 主代理審查譯文來源、術語一致性、字型覆蓋、顯示邊界及互動收據；同步工作清單、
   現況與GitHub Issue。譯文草稿數、原版實際命中數、已驗證顯示數分開報告。

## 完成判準與未授權範圍

本輪完成時，新增譯文須通過來源位元組、UTF-8、占位符及字型檢查；前端若做成，
須有玩家視窗的座標／點擊／退出與同輸入狀態收據。未驗證的原版情境保留原文並記錄。
只有已證實來源與READY規格才能進正式覆蓋，不以文字檔抽取數宣稱全遊戲中文化。
本輪不變更原版EXE、資料、規則或存檔；字型與原版素材不發布。全遊戲完成門檻、
術語政策及正式公開／散布方式尚未確認，遇到真正影響成品的取捨時提供具體成果再討論。

## 結果

已建立獨立譯稿Issue #27，與來源清冊#7、術語決策#10、互動切片#26串接。
唯讀清冊入口為[文字表面盤點工具](../../tools/inventory_text_surface.py)，
譯稿與顯示分母入口為[進度報告工具](../../tools/catalog_progress.py)。
本機收據只寫入被忽略的 `workplace/reports/goal058-*.json`。
唯讀盤點找到18個`*.TXT`、4,119個粗略資料行；這不是玩家訊息數，也不含EXE／圖像文字。
翻譯子代理由50筆擴至189筆草稿（GAME 96、LABELS 40、NAMES 14、PEDIA 19、MENU 20），
139筆為本輪新增。189筆均通過原始檔與片段SHA、位移／長度、CRLF、占位符、控制碼、
ASCII熱鍵和前置縮排核對；Cubic 11 24px缺字0，六項回歸測試通過。多義的`Complete`
未合併。正式安全矩形及執行期顯示只驗證既有主選單五筆；其餘184筆仍是未驗畫面的
來源候選。固定路徑收據有一個未建檔來源片段，不能把它推算成全遊戲未知鍵數。

[可撤回Linux視窗原型規格](../spec/013-window-prototype.md)已READY。真實Xvfb視窗在
1280×800畫布以原生DOS滑鼠按下／放開，由五列中文主選單進入難度畫面；九筆實際
視窗輸入可逐指令重播。中文重播及英文無hook控制組均到100,000,000步，606幀、
5213虛擬tick、1,395,189,090 CPU cycles；CPU、完整RAM、原版索引畫面與色盤一致。
兩張真視窗截圖與對照圖逐像素一致。視窗原型只證明目前切片的滑鼠接線，不含完整
鍵盤、音訊、存讀檔、正式速度、失焦／關窗實測或整局遊玩。

重播入口：[譯稿驗證](../../tools/validate_translation_draft.py)、
[譯稿與字型審查](../../tools/review_translation_draft.py)、
[視窗原型產生器](../../tools/build_window_prototype.py)、
[Xvfb滑鼠流程](../../tools/probe_window_prototype.sh)、
[獨立視窗收據驗證](../../tools/verify_window_prototype.py)。
本機收據為`workplace/reports/goal058-text-surface.json`、
`goal058-catalog-progress.json`、`goal058-translation-review.json`、
`goal058-window-receipt.json`及兩張`goal058-window.*.png`；原文、畫面與字型不入版控。
