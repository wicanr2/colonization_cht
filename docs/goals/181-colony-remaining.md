# 目標181：殖民地與港口其餘欄位

狀態：進行中；日期：2026-10-03。對應 [Issue #56](https://github.com/wicanr2/colonization_cht/issues/56)，目前入口為 [CONTEXT.md](../../CONTEXT.md)。百科其他入口仍由[目標180](180-pedia-remaining.md)追蹤；遮擋策略已選定整行暫藏、關框恢復，限定驗收與其餘選單分支由[目標178](178-orders-disabled-map-labels.md)及[規格032](../spec/032-sea-menu-and-status-draft.md)追蹤。

本次正常路徑續查入口為本機 `workplace/reports/goal181-colony-rest/soldier-city-probe-v31.sh`，收據目錄 `soldier-city-v31/`；沿 v30 議會框以正常 Return 選任，再觀察下一年度。只作入口探勘，尚未驗收新增文字，不改矩陣或普查。

v31 選任後的正常畫面已為1495年、作用中輕帆船；士兵圖像在殖民地西北方，仍未證明進城。續查副本為同目錄 `soldier-city-probe-v32.sh`／`soldier-city-v32/`，以Space切換、標準kp3嘗試東南移動，再由正常點擊觀察殖民地；不得依腳本名稱宣稱抵達。

v32切換後原版側欄確認士兵在(50,28)、行動1；kp3後到移民通知，點城位置只推進至移民教學框，沒有進城。續查 `soldier-city-probe-v33.sh`／`soldier-city-v33/` 先正常Return關閉教學，再嘗試kp3；新增事件只作探勘，不提高完成數。

可丟棄的有界控制副本為 `soldier-city-live-v34.sh`／`soldier-city-live-v34/`：沿v33正常GUI入口，只在操作批次間以程序暫停等待觀察，控制期上限240秒。`control-ready`表示可提交`control-actions`；操作僅接受`key`、`click`、`drag`、`wait`、`shot`及`close`，全部經既有GUI輸入函式。不得寫原版RAM、變更存檔內容或把暫停當成中文驗收；正式收據仍須由完整GUI輸入重播驗證。

v33勘誤：關閉移民教學後已到1496年、作用中船隻；第二次kp3確實作用於船隻，側欄變為(54,30)，不算士兵重試。正常點城後已見城內駐留士兵與碼頭單位圖像，才取得抵達的畫面證據；仍為一名居民，未驗加入居民與裝備。較早v32的「沒有進城」僅表示尚未開啟城內畫面，不足以否定先前kp3已完成移動。原始收據保留，不改寫歷史輸入。

v34兩次正常拖放未見新增居民；點擊只顯示駐留單位選取框。控制期有界結束且正常關窗，不當成裝備或多人口完成。另存入口為 `soldier-city-save-v35.sh`／`soldier-city-save-v35/`，沿v33正常城內畫面離城，再由GAME→SAVE選單選第三個空欄位；必須核對實際選單、成功畫面、新檔名及雜湊後才能採用。原版存檔只留本機，不入版控。

v35私有入口比對為同目錄 `check-soldier-save-v35.py`，在驗證容器呼叫 `python3 /repo/workplace/reports/goal181-colony-rest/check-soldier-save-v35.py --game /game --reports /repo/workplace/reports/goal181-colony-rest/soldier-city-save-v35`。先以[既有三側入口](../../tools/probe_goal181_replays.sh)重生收據，逐點及完整原版RAM／檔案指紋／新舊存檔位元組一致才採用；缺合法原版返回SKIP 77。這只驗正常存檔入口，不授權新增中文完成數。

短控制副本為 `soldier-city-live-v36.sh`／`soldier-city-live-v36/`，只在v35三側通過後採用原版正常生成的COLONY02.SAV，以主選單第三欄正常讀取；預設先停在實際世界畫面，再觀察及送入正常操作。控制期480秒，新增`right`只傳送滑鼠右鍵；不寫原版RAM。執行時須明確設定COLONIZATION_GOAL179_SAVE為v35的scratch/COLONY02.SAV，其他正式前端／圖集沿v25。

v36已正常載入COLONY02.SAV。初次圍欄拖放移動原居民至市政廳；右鍵圍欄則開啟老手級士兵百科。返回後先左鍵選取圍欄士兵，再拖入市政廳，88200000步實際顯示兩名城內工作者、圍欄士兵消失與50火槍；仍未驗裝備或增加中文完成數。後段另存點擊落在世界地圖，沒有生成COLONY03.SAV，標為未命中測試路徑，不列產品缺陷。

保存入口為 `soldier-city-save-v37.sh`／`soldier-city-save-v37/`，由已驗COLONY02.SAV正常第三欄載入，開城、先選取圍欄士兵再拖入建築，離城／GAME／SAVE等每個畫面轉換都沿v35的shot_after等待後才送下一段輸入。v37已正常執行且有兩居民／50火槍畫面，保存選單也已到達；原版成功訊息顯示COLONY03.SAV，實際卻更新該批工作副本COLONY02.SAV，未生成03檔。差異原因未知，下一步以原文控制及DOS檔案呼叫核對，不改原版規則或存檔格式。已驗初始入口仍用v35原始COLONY02.SAV（f683eb…），不可誤用v37已更新的副本。

v36的`normal-state-summary.json`通過13個共同原版取樣點及GUI／中文／原文／缺圖集完整狀態；初始COLONY02.SAV未變。控制期暫停觀察沒有改變本次原版執行。v37結果及檔案差異見自己的`exploration-summary.json`，尚未完成原文控制；兩者都不增加正式中文完成數。

已驗COLONY02.SAV的私有三側重播副本為 `seed02-replays.sh`，沿既有目標179入口，只把初始指紋及保留檔名綁定到已驗COLONY02.SAV；明確設定COLONIZATION_GOAL179_OUT、COLONIZATION_GOAL179_SAVE、COLONIZATION_WINDOW_BIN與當前圖集。在同一驗證映像及有界Xvfb執行，不讀取或注入快照。用於v36／v37正常GUI輸入的完整原版狀態比對，不取代中文欄位與存檔驗收。

保存檔名觀測入口為本機 `save-source-v38/probe.go`，由已索引的 `tools/probe_goal181_buy_sources.go` 派生，只增匯出dosgolem既有FileOps／Wrote紀錄，標記觀測改用既有`--marker-prefix @SAVEGOOD`。沿v37完整GUI輸入與v35原始COLONY02.SAV，到同一107400000步終點，必須先比對完整RAM及實際文件指紋再解讀事件；不得把原文控制或觀測器成功執行當成保存檔名原因已確定。

v38觀測與v37的GUI、中英及缺圖集三側完整狀態一致；保存開檔94818562步的DOS AH=3Dh參數為COLONY02.SAV，Wrote亦只有該檔。SAVEGOOD查詢94947242步與原始GAME.TXT讀入定位已確認，檔名差異並非本次翻譯模式造成。保存選項墨跡縱區間為300～319、332～351、364～383、396～415等，相隔32像素；v37點384不在第四列墨跡內，尚不能用它驗第四欄。下一步以列中間或鍵盤選取核對，不先改DOS或原版。

讀檔成功欄位續查使用同觀測器的`--marker-prefix @LOADGOOD`，輸出`load-source-v39/`；私有顯示原型為`load-prototype-v40/`，只讓已知GAME.TXT:0x00000854的%STRING0保留COLONY兩位數.SAV原值，其他模板及非該格式維持回退。正式程式尚未變更，須先取得來源、欄位量測及DRAFT→READY，再實作與正常GUI／三側驗收。

原型量測重播入口為本機 `load-prototype-v40/replay.sh`，沿v37完整正常GUI輸入執行至107400000步，取樣37000000／44200000步。初始存檔仍為v35的原始COLONY02.SAV；只複製原檔名，不注入快照。第一次明示上限短於輸入終點被拒絕，`prototype.log`保留；乾淨重跑使用`prototype-full`與獨立`scratch-full`。這是DRAFT欄位量測，不能取代正式正常GUI收據。

保存列中心續驗入口為本機 `soldier-city-save-v41.sh`／`soldier-city-save-v41/`，從v37腳本派生，只將保存點選y384改為已量測第四列墨跡中心y408；主選單讀檔仍用原第三欄及v35初始指紋。保存後須重新核對實際檔案與DOS呼叫，不能用畫面訊息代替檔案驗收，不能覆寫v37失敗紀錄。

v41正常GUI已生成COLONY03.SAV（24343位元組，d3a462e709e59845af7d2f56a6a504429bc899ebc751964e647a2be69b381c77），初始COLONY02.SAV未改。保存檔名差異的v37紀錄保留；第四列中心修正只改驗證輸入，不改產品或原版。三側重播沿`seed02-replays.sh`，尚未以GUI檔案存在單獨宣稱驗收。

讀檔原型的墨跡觀測與壓力量測入口為`load-prototype-v40/geometry-replay.sh`及`zz_layout_test.go`，均只在驗證容器執行。正常GUI印字的字元墨跡／基線／色號及安全區輸出至`geometry.log`，100個候選檔名與格式拒絕案例輸出至`layout.json`；原版局勢仍只驗實際正常COLONY02入口，不把100個排版案例當作100個局勢。

讀檔欄位READY後的正式組裝入口為本機 `load-final-build-v42/`，沿 `tools/build_window_prototype.py` 及現行字模；正常GUI入口 `load-normal-v43.sh`／`load-normal-v43/`，由v41腳本只保留主選單正常讀檔、成功提示及回世界。三側重播仍用`seed02-replays.sh`。存檔完整狀態檢查器為本機 `check-soldier-save-v41.py`；讀檔中文欄位正式檢查器為 `tools/check_goal181_load.py`，須連同同GUI來源觀測結果核對。

正式正常讀檔來源觀測輸出至本機 `load-source-v44/`，沿`save-source-v38/probe.go`，指定v43的GUI輸入、`--marker-prefix @LOADGOOD --from 37000000 --to 45000000`及GUI明示完整終點。觀測scratch複製v35初始存檔；同一完整RAM與輸入綁定必須由檢查器重驗，不能沿用v39的不同終點作正式收據。

第四列保存的DOS來源續驗輸出為本機 `save-source-v45/`，沿同一觀測器，以v41正常GUI輸入、`--marker-prefix @SAVEGOOD --from 88000000 --to 103000000`及107400000步完整終點驗證實際開檔與寫入；只確認本次保存名稱，不接入SAVEGOOD中文正文。讀檔檢查器的負例副本放在本機 `load-negative-v46/`，以受控錯誤收據驗證像素、來源鍵、讀取位移、輸入及RAM守門，不更改正常收據。

讀檔欄位通過後的矩陣／普查重生輸出為本機 `matrix-v47/`／`census-v47/`，由現有驗證腳本產生；至少重跑普查並移除本次矩陣列核對計數差異。不以手改報表數字代替驗收。

可提交的讀檔重生入口為 `tools/probe_goal181_load.sh gui`／`replays`，設定COLONIZATION_LOAD_OUT、COLONIZATION_LOAD_SAVE、COLONIZATION_WINDOW_BIN及本目標現行圖集；它沿v43已驗輸入與v35存檔指紋，不依賴私有腳本。原版來源觀測仍由 `tools/probe_goal181_buy_sources.go` 在獨立Go模組內執行，指定LOADGOOD與本次輸入／終點；將其原始`.matches.json`保留為同收據目錄的`trace.json.matches.json`，再執行 `tools/check_goal181_load.py`。缺原版或已驗正常存檔須SKIP77，不自行合成。

雙居民讀回與裝備選單探勘入口為本機 `equip-two-v48.sh`／`equip-two-v48/`。只複製v41正常生成的COLONY03.SAV，指紋d3a462…，由主選單第四欄正常讀取、進Jamestown，點原居民再開職業更多頁；須先看實際居民、火槍及選項是否啟用，不在未確認選項前猜補裝備行為。前端沿load-final-build-v42，沒有注入狀態或更改存檔。

v48正常讀回已見兩居民與50火槍，職業第二頁士兵為原版可選綠色，斥候／龍騎兵因缺馬仍灰色。下一個正常裝備入口為本機 `equip-two-v49.sh`／`equip-two-v49/`，只在已確認的更多頁點士兵並截圖；三側重播副本為 `seed03-replays.sh`，只將已驗初始指紋及保留檔名改成正常COLONY03.SAV。原版執行結果、訊息與取樣點須另驗，不將選單顏色當作已完成裝備。

範圍沿 Issue #56：殖民地、歐洲港口、報告、國會與貿易路線的待接文字，包含 BUY 說明框、武裝面板、多人口殖民地與建造清單捲動。現行路徑由主選單正常讀檔、指定陸上單位並建城。初期讀檔與新局探勘未進入殖民地，原收據保留於下方歷史；不得注入地形、修改存檔或猜補規則。

正常探勘入口為 [tools/probe_goal181_gui.sh](../../tools/probe_goal181_gui.sh)。在既有 `colonization-verification:20260930-r1` 映像，以目前 UID/GID、唯讀原版與有界 Xvfb 執行 `bash /repo/tools/probe_goal181_gui.sh`；由主選單正常讀取目標178手動保存的原版存檔，切換移動模式、啟用陸上單位，再正常建城。輸出預設 `workplace/reports/goal181-colony-rest/load-unit-v6/`，可由 `COLONIZATION_GOAL181_OUT` 指定不存在的新目錄。`COLONIZATION_GOAL181_ROUTE`另接受load-unit-v4至load-unit-v10或colony-v3，各版本的實際入口副本保存於自身`probe-source.sh`，不得用新版腳本推定舊版操作。

固定前端與圖集沿目標180的 `sync-final-build`、`formatted-dialog-atlas`、`final-string-atlas`、`final-string-templates.tsv`；原版與正常存檔指紋沿目標179。所有原版畫面、資料與探勘中間物只保存在已忽略的 workplace。

正式修改沿規格035／036／038；新判定或欄位先取得原版事件、來源與個別字級／安全區量測，補 DRAFT→READY 才實作。退出條件為正常 GUI 逐欄中文、中文重播安全區相同、中英及缺譯負例完整原版狀態相同，接入矩陣並重產普查。探勘畫面與譯稿不能當成中文驗收完成。


## 初期探勘歷史

第一版select-v1正常讀檔與關窗成功，選取登陸位置後仍為輕帆船，並重新置中；沒有建城，不提高完成數。確切操作腳本保留`select-v1/probe-source.sh`。下一版`skip-v2`改用原版Space略過當前單位，先抓下一個作用中單位，確認後才建立後續建城輸入；兩版各從同一正常存檔冷啟動。


目前入口切換為colony-v3，沿目標172已驗的正常主選單新局、登陸、建城與殖民地操作，使用目標180當前正式來源。初次切換包裝腳本未落實，仍由舊skip-v2入口因既有輸出而在啟動前拒絕；已用明確檔案補丁更正，尚未執行原版，不列產品缺陷。v3每次固定操作腳本到/tmp並保存輸出目錄副本。Space標準3920字組的既有兩項鍵盤測試PASS，未宣稱遊戲已輪替單位。

## 2026-10-01：正常存檔建城已到達

前述v3歷史入口已退出至1,100,000,000步，原版RAM `da66142720bb89c1eef376e20b7ddf1db273ed43d666b0561229c6cbafe81715`，GUI輸入`253c62a1f30387d76b736fc17cd22b7040ad53263088fe51e0cd6c5f81fee122`。實際走到切羅基交涉、交易與學習職業，沒有建城；不採腳本通用的「殖民地操作完成」訊息判定命中。收據保留，可供#58後續窄驗；尚未三側比較，不提高完成數。

核對第三波說明書`Image020.jpg`第24頁的「指定單位／建立領地」操作及原版MENU.TXT的VIEW選項後，v4由正常存檔切換移動模式，點取陸上單位並收到TUTORIAL13。65200000步的截圖仍為船，不能把點擊意圖當成陸上啟用已完成；70600000步實際已顯示拓荒者。v4終點70800000步，RAM `078d0e3c3ac40de529fcfb2a47783e6434601f95e8df22c21fb1cb58d11eb81c`，輸入`53ceeef86f1dfdf2d9cebfaaec00dfc259845be497cdc72277863da7f27001d5`。

v5沿相同正常讀檔，等待提示完成後在80M按b、接受預設名稱、關閉木刻與教學提示。`after-5`的115400000步真GUI及240M的最後截圖實際為Jamestown殖民地；240400000步正常關窗終點RAM `78387f8d7c618a52ff2f2b11bf53fcc70dbdbb2b5680791d68db7221688e9321`。路徑只透過原版GUI，不修改原始資料、地形或存檔；來源與工具版本沿本目標固定指紋。v6再開建造面板與BUY，收據另存。這些是探勘命中，尚未新欄位的字級／安全區、三側同狀態或正式中文驗收，不變更普查。

## BUY欄位驗證入口

正常新存檔讀入／居民工作選單的續驗入口為 [tools/check_goal181_city.py](../../tools/check_goal181_city.py)，對應city-load-v1及city-jobs-v2；工作選單加--require-jobs。GUI與重播使用原始COLONY01.SAV及c27b4466…固定完整雜湊，重播另設定COLONIZATION_GOAL181_SAVE指向v10的已驗原始檔。這些續驗不改原版工作或生產規則；生產與可支付選項另取正常路徑證據。

正常建城後另存的檢查入口為 [tools/check_goal181_save.py](../../tools/check_goal181_save.py)，搭配v10真GUI及[三側重播](../../tools/probe_goal181_replays.sh)。只驗原版完整狀態、逐點索引／色盤與新舊存檔位元組；存檔成功訊息仍英文，不藉此提高其中文完成數。

同文來源補證入口為 [tools/probe_goal181_buy_sources.go](../../tools/probe_goal181_buy_sources.go)：沿已記錄正常GUI輸入，只觀測原始BUY查詢標記、比較指令位元組與GAME.TXT讀取定位，另核對完整原版終點。BUYME0與BUYME1正文相同，事件的模板鍵不單獨證明原始段落；選項與來源識別補證前不提高普查完成數。

v6在正常殖民地開啟建造面板，於251800000步真GUI收到資金不足的碼頭費用正文，來源鍵`GAME.TXT:@BUYME1:0x00002F09`，原版1352$及1000$原樣保留。建造面板三個短欄與兩行正文已有中文；尚未收到可支付的選項，不由正文推定整個四行來源已完成。252200000步正常關窗RAM `df275d5e68e8556cca0baf60295ab2445fd5f101eda16d08fec15f3b4e1e0dfb`，輸入`d2e1ae9ff7c45d1bdb02506060def51860656177d9287d5006c5dc480649adc1`。

三側入口[tools/probe_goal181_replays.sh](../../tools/probe_goal181_replays.sh)沿原版存檔與完整GUI輸入，固定腳本副本後生成中文、英文控制與缺對話框圖集負例。檢查入口[tools/check_goal181_window.py](../../tools/check_goal181_window.py)，原版缺失明確SKIP；要求所有取樣點及終點完整原版狀態一致、BUY正文GUI安全區與重播相同、負例回原文、建造面板三欄逐像素相同。

欄位量測入口[tools/measure_goal181_buy.py](../../tools/measure_goal181_buy.py)，在既有驗證映像掛隔離副本及Go快取、原版唯讀；執行`python3 /repo/tools/measure_goal181_buy.py --reports /repo/workplace/reports/goal181-colony-rest/load-unit-v6`，只在本機組裝副本呼叫正式排版函式。原版第一個大寫字墨跡`[82,121,86,128]`，大寫高7、基線127／137、行距10；安全區`[80,119,228,142]`。27位數只作譯文排版壓力，不主張原版價格範圍。初跑Go初始化因沒有DISPLAY而失敗，後加有界Xvfb及原組裝指紋核對的`--resume`重跑，不列產品缺陷。

三側檢查`buy-summary-v2.json`PASS，18個共同原版取樣點與終點完全相同，GUI正文安全區和建造面板三欄與中文重播相同，缺對話框圖集時正文回原文。檢查器首版誤以四欄解包既有字串區間的五欄回傳，修正介面後同收據通過，沒有放寬原版／像素條件。實際譯文30px、墨跡`[6,4,376,77]`；27位數壓力譯文縮至22px、墨跡`[6,4,579,69]`，均在592×92輸出安全區，超界情境回退0px。Cubic 11 30px的上升部25、中文墨跡2～30；本欄採原版兩行10邏輯像素行距，中文首行墨跡在安全區上緣+4、後一行基線前進40輸出像素，沒有全域套用此字級。

原始`BUYME1`普查單位含正文兩行與選項兩行，共四行；本次選項未出現，保留整列pending。未直接接入會把整列算完成的通用普查，不提高761數字。下一步由正常建造清單選較低成本項目，取得可支付分支的選項實際GUI與相同狀態收據；不得以資金不足正文替代選項驗收。

## 2026-10-01：BUY來源勘誤與後續路徑

v6的中文模板鍵BUYME1不是原版來源鍵。新來源觀測在247889018步記錄實模式0E2D:0832的F3 A6、CX=1，RAM0x249DC標記與0x2AC5E查詢鍵均為@BUYME0；返回9B94:00D7。247878189步GAME.TXT位移11776讀取512位元組至1C6A:E962，涵蓋原始標記檔案位移0x2E93。原始正文0x2EA8、60位元組、片段SHA-256 4d7b50c35be4f0b6c0f947e02da53f73aa4e3cdfcfd6c15bf755c4cb58660250，只有兩行，沒有選項。來源觀測GUI輸入與252200000步完整RAM和v6控制相同。已證實僅為本次原版BUYME0查詢、讀取定位及已驗畫面；不宣稱全文每位元組搬運已追完。

前述「四行來源仍pending」保留為當時按模板鍵判斷的歷史。目前更正為：本次BUYME0兩行正文已完整驗收，BUYME1四行及可支付選項仍待驗。模板同文同譯可以共用排版，普查只歸屬已確認的原始來源；加強檢查器須每次重跑原始標記、檔案指紋、GUI輸入、RAM及安全區條件，不能只相信人工別名。

v7正常開出12項建造清單，最後為貨車，畫面需求40榔頭；沒有以需求數推算價格公式。v7完整終點263600000步RAM 7a51a83a89810d2aef85d0eeaebdf6cff347fcdbd4cfa5eaa1ccb3091c3a2393，GUI輸入 b6ce64d285ae73dc7c4d65a056eb2fe447d8f3ebe0f604e9bb59bf9547836384。v8按End仍停在碼頭，Return後建造面板仍開啟；再按鎚子反而關閉面板，後續購買點擊未命中。這是測試路徑問題，不宣稱原版不支援其他鍵或新增特殊鍵盤規則。v9改由當前碼頭逐次Down九次到最後一列，再購買；另用正常Ctrl+S保存建城狀態，仍須核對實際截圖及存檔後才採用。

## 本批正式結果與下一個正常入口

來源映射限定CONFORMED。matrix-v7為35PASS、0SKIP／FAIL／舊收據／原版輸入衝突；census-v8為762已顯示、1015待接、89無法正常觸發，分母1866。只有BUYME0由pending升shown，BUYME1仍pending；偽造標記、錯原版終點、省略位移的錯別名及換GUI目錄都拒絕。正式普查兩次逐位元組相同，移除BUY矩陣列後已顯示降至761；刪除／重疊分類樣式的負例仍拒絕。檢查入口沿tools/check_goal173_census.py及本目標的矩陣、重播與來源工具鏈，沒有採用帶未驗港口選項的候選765數字。

v9真正選中貨車後，原版報價1040$、國庫1000$，仍未達可支付選項；沒有改價格或資金。Ctrl+S測試未產生新檔，原存檔雜湊不變，不以截圖名稱判定成功。v10改由已驗GAME選單、Save Game及第二個空欄另存，真GUI收到COLONY01.SAV成功訊息。30個共同原版取樣點、三側完整終點與新舊存檔位元組相同，成功畫面整張GUI與中文重播相同。成功訊息仍英文，狀態欄遮擋仍待驗，本存檔測試不提高這些欄位的中文完成數。

後續可正常讀取本機load-unit-v10/scratch/COLONY01.SAV；保留原始檔名、使用第二個存檔欄並驗證SHA-256，不注入快照或修改資金。新入口仍須從主選單正常讀檔並核對畫面，不能僅用檔案存在宣稱已進城。入口tools/check_goal181_save.py；三側重播時設定COLONIZATION_GOAL181_OUT指向load-unit-v10，再執行probe_goal181_replays.sh。

正式收據與雜湊：

- load-unit-v6/buy-summary-v4.json：4fcb57d56e70ab7ab48b5afb2575a559e8c2f9d282b717b31b5fea96831299bb
- matrix-v7/matrix.json：08bb5ff793ba684896846f532f4d7af71ed0da93ac6ade14211eb5ae6e43ce67
- census-v8/repeat-and-negative.json：eafaed5baf6a43ecef9b21fab5c5267feed41b4eee26b0e12260bf21d5a08949
- load-unit-v10/save-summary-v2.json：e3ed87957f4c9010abbb28f7af1c5424b7f6da5edf9a4f6a1a986761a4d0aed3

正常存檔24343位元組，SHA-256 c27b44665f1a229ca5257ac8f23b2f63dc025d5814aa5172742ffcd69939e647；原始COLONY00.SAV維持cf25bb51d818e6dd30a7437e14e4be32bce1eb68b0db4864c0cff0b9f0e4fe8e。GUI輸入SHA-256 d359306d4fe6176ef4f4d8bf4eaf15740ea372bc0e76aab5e8f4b15e6d374b1f，完整原版終點329200000步、RAM c22dedaaba179919a6823bbad07b30b2a95a3a250fdd1dc64bae5803a9e56022。


## 2026-10-01：正常職業選單與議會續驗

city-jobs-v2的進城截圖仍留舊游標，安全區逐像素檢查拒絕；保留收據，未放寬條件。city-turn-v5在移開游標後增加有界呈現等待，正常進城三欄與17項職業清單通過12個共同取樣點、中英及缺圖集完整原版狀態。輸入4a45e9734f897cdb3071182f7356737125150d38e85a7549e4f53436450309a7；終點151400000步RAM d9af66f504c0d94597020ca6803730286f7782d8f7fe07bcefeeb6386e917635。檢查入口仍為check_goal181_city.py --require-jobs。

Space先切至士兵，不能直接當成結束回合；city-join-v4的B實際開出另一座殖民地命名，沒有加入Jamestown，未接受命名。city-stock-v6選取原版預設議會候選後實際到1495年，殖民地畫面顯示食物2、木材8；這是正常探勘，尚未三側驗收，不推定價格或生產公式。

正常議會五項顧問選擇的模板已依[規格036新READY段](../spec/036-line-list-and-centered-text.md)補接，尚未正式GUI驗收。量測與可丟棄Go實驗保存在city-turn-v5/father-layout；只增補原版顯示翻譯，不改選任或回合規則。city-buy-v7再走正常木匠與回合路徑，探勘有建造進度後的可支付BUY。


### 議會與可支付BUY正式續驗

city-father-v8的議會正文／五項、既有進城三欄與職業17項已通過12個共同取樣點；city-buy-v9再沿正常兩次回合、關閉兩個連續提示、進城開BUY，實際價格481$、國庫1000$。26個原版取樣點、GUI正文／兩選項安全區與三側完整原版狀態相同，原始查詢確認BUYME1。入口仍為check_goal181_city.py，加--require-fathers或--require-buy；BUY來源映射加--lookup-reports同目錄。字級、原始定位與限定CONFORMED見規格036。

v7的連續移民／木匠提示使後續點擊未進城，原收據保留；v9修正關閉順序後才達可支付分支。量測工具的局部變數撞名曾造成Go實驗編譯失敗，修正後在同組裝指紋與同映像通過；屬驗證腳本問題，沒有修改正式顯示邏輯。未驗地形懸停不由本列提高普查，正式範圍由檢查器verified_fields逐次綁定。

現行議會字串圖集為father-string-atlas/string-atlas.json，GUI或三側續驗設定COLONIZATION_STRING_ATLAS指向它、COLONIZATION_STRING_TEMPLATES指向現行text/string-templates.zh-Hant.tsv。預設180封存模板入口保留供舊收據重生，不能當成新議會模板的驗收。


## 本輪採用的正式收據

matrix-v16：37PASS、0SKIP／FAIL／舊收據／原版輸入衝突。census-v17：788已顯示、1014待接、89無法正常觸發，分母1891；未歸類與未使用樣式均0。普查兩次重跑與提交內容逐位元組相同；移除資金不足收據後已顯示降至787、BUYME0恢復pending，移除可支付收據後降至785、BUYME1及兩個年度標題失去完成證據。沒有採用未驗懸停或未分類的候選。

分母新增25種實際觀測的執行期字串，其中24種已驗、1種讀檔彙總仍pending；兩個既有TXT來源WHICHFREEDOM／BUYME1亦已驗。新增已顯示26不代表26個既有待辦都完成。其他殖民地、武裝、多人口、港口／報告／貿易路線、存讀檔缺譯仍由Issue #56／#61續驗，沒有提前關閉Issue或發布版本。

正式雜湊：

- city-father-v8/city-summary.json：7c21148b7a92fb82be092fd1fbaf1b19143b50e7735404ca6dbb22698bc4db60
- city-buy-v9/city-summary.json：c91feff16c6a4aff9b393cd512aaacfeb7a99ad6947f9ac522b2d5e134c45114
- city-buy-v9/buy-source.log.matches.json：3b1f78b6d4b65c4ebe210ef6a2dafe381590ae543ab35a72eed4023d09c9c5ca
- matrix-v16/matrix.json：8cef5b727f1bb792ac816fa97fc42dfbf50c61bd278a64b3f80d55a0022501d5
- census-v17/repeat-and-negative.json：9b62dc05ecf588878ccbabb68d31035a8643966ab1842d67c59d0a7b22aa25c3
- father-string-atlas/string-atlas.json：8583aa79ae02fccd669875d55c5c24c998ec2129e6ad6706ae17174059ed3cf5

## 正常職業第二頁與裝備操作探勘

city-more-v18由正常COLONY01.SAV第二欄讀檔、進城、居民選單、更多，第二頁標題及六項清單已通過六個共同原版取樣點、GUI安全區、中英與缺圖集完整狀態；三個停用列保留原版灰色。欄位字級與原始來源限定CONFORMED見[規格036](../spec/036-line-list-and-centered-text.md)，只驗裝備選單顯示，不宣稱已裝備。

重生仍使用probe_goal181_gui.sh與probe_goal181_replays.sh；GUI設定COLONIZATION_GOAL181_ROUTE=city-more-v18、COLONIZATION_STRING_ATLAS指向father-string-atlas/string-atlas.json、COLONIZATION_STRING_TEMPLATES指向text/string-templates.zh-Hant.tsv；重播另指定COLONIZATION_GOAL181_SAVE為原始load-unit-v10/scratch/COLONY01.SAV及相同OUT。驗證用check_goal181_city.py --require-jobs --require-more。source／像素／停用色／RAM負例及原版缺失拒絕結果保存在city-more-v18/negative-checks.json；檢查器每次核對來源、完整狀態與GUI，不憑摘要算完成。

city-equip-v19選取可用前鋒後實際收到棄城ABANDON2確認，因本城只有一名居民；歷史截圖名pioneer-equipped不能當成裝備已完成。正文因Jamestown名稱變數variable-without-term仍英文，兩選項中文。沒有接受棄城或修改資源。city-arms-v20正常點第二個選項取消，回到殖民地；再點零存量武器欄沒有開出面板。這兩版只有探勘，不接入矩陣／普查，不宣稱武裝功能完成；下一步先補棄城正文的名稱變數證據與排版，再找正常可裝備的居民／庫存路徑。

矩陣首次時間預算不足而終止；增加預算後因呼叫端漏建輸出目錄而無法保存報告。已修正verification_matrix.py在批次前建立輸出目錄；兩次失敗均是驗證執行問題，不列原版或中文顯示缺陷，正式矩陣須以乾淨完整重跑結果為準。

## 本批正式採用結果

matrix-v20為38PASS、0SKIP／FAIL／待重驗／原版輸入衝突；census-v18為分母1896、已顯示793、待接1014（正常642／特定局勢372）、無法正常觸發89，未歸類與未使用樣式均0。新增五種已驗裝備需求執行期組合，不是五個既有待接來源完成；移除第二頁收據後完整回到前次788／1891，普查兩次重跑與docs逐位元組相同。移除BUYME0後792已顯示，移除可支付BUYME1列後790；刪除／重疊分類樣式仍拒絕。

- matrix-v20/matrix.json：e9913b24bde9015d9fb82eab5ef77fc39e1c8fdd398f62c1dfd0b450018851a9
- census-v18/census.tsv：1bcea87069de719958763a01f8d575588adcae0682933f3a55fd4f032871cd38
- census-v18/report.md：ff662ea5f3d0982eea3138dd52743479f20771492d15a86942efd0e9894888ac
- census-v18/repeat-and-negative.json：c0a287d0165af522976e5a83ce55e1de4d6d78bdf69bce0c4ba7c3a72a924311
- census-v18/without-more-summary.json：57b8fac0e241813973ee9cf7217a39a7f1d420930dad7714c05dcb0c3e846351

最新棄城正文變數缺口見[規格035的DRAFT補證](../spec/035-dialog-overlay-draft.md)，沒有未審實作。Issue #56遠端回讀仍OPEN、無留言；未關閉Issue、未commit／push或發布新版本。本批Docker容器已清空，原版素材未追蹤，輸出UID/GID1000:1000，未發現root-owned檔案或同名.md目錄。

## 棄城來源訂正與取消結尾續驗

原版查詢證據已訂正：本次正文為ABANDON，選項同文模板ABANDON2不能證明ABANDON2正文曾觸發。名稱欄位已依[規格035的READY補審](../spec/035-dialog-overlay-draft.md)正式實作，Go回歸通過；175個名稱排版案例與原始來源定位分別保存在abandon-prototype-v22／abandon-source-v21。正式前端組裝入口為abandon-final-build；原型不作正式交付。

city-abandon-v23正常從主選單讀COLONY01.SAV、進城、更多頁、點前鋒後顯示中文正文；八個GUI取樣點與三側完整原版狀態相同。終點87200000步、RAM a69cdacf4fe81fc89a625890c360535e75fa23b0948b353f825d0e1f73d0fb52，輸入aeaa22add1a36b0b668f6693e530422752d00676917500abe42cee74767d68a1。原始ABANDON查詢來源收據在同目錄abandon-source.log.matches.json，與上述輸入及完整終點綁定。

check_goal181_city.py --require-jobs --require-more --require-abandon --lookup-reports同收據目錄拒絕：正常取消後兩個中文選項殘留；英文控制畫面沒有選項。保留失敗GUI與重播，不加入矩陣／普查。可丟棄時序原型入口abandon-lifecycle-prototype-v24/replay.sh；量測紀錄位於city-abandon-v23/lifecycle-baseline.log及lifecycle.log，原型沿同一輸入、原版與名稱欄位契約。第一次原型缺DISPLAY屬環境問題，失敗紀錄另存lifecycle-display-failed.log，補Xvfb後乾淨重跑；不視為產品缺陷。

下一閘門：補審印字候選撤銷證據，再以正式來源重建、重新正常GUI與三側驗收。ABANDON2警告、接受棄城結果、武裝操作仍待驗；目前正式完成數維持matrix-v20／census-v18。

## 棄城正式採用結果（2026-10-01）

city-abandon-v25已通過check_goal181_city.py --require-jobs --require-more --require-abandon --lookup-reports同目錄。正文名稱依READY正式顯示，候選印字已完全被原版重畫抹除時不再啟用覆蓋；正常取消後城市三欄恢復，原棄城區扣除城市欄位後與英文控制逐像素相同。八個共同原版取樣點、三側完整CPU／RAM／索引／色盤、正常COLONY01.SAV及輸入相同。正式前端與欄位字級限定CONFORMED見[規格035](../spec/035-dialog-overlay-draft.md)，Go回歸全部通過。

原版實際73876380步查詢ABANDON，73860584步GAME.TXT位移6144讀512位元組至1C6A:E962；正文原始來源174672，74036409步開始，選項74150826步開始。初始存檔c27b44665f1a229ca5257ac8f23b2f63dc025d5814aa5172742ffcd69939e647，正常輸入48041fe90d4a4b7f4272dc1b6bea460e2c3dafd7d455d9407af59b164d050f5c；終點86800000步RAM 3a2a2f6271ee237570af64c244805325f798f6658f4299a8573151277ce7ed61。原版檔案指紋與實模式地址基準沿本目標及規格035，不將RAM當成檔案位移。

重生：probe_goal181_gui.sh設定COLONIZATION_GOAL181_ROUTE=city-abandon-v23、OUT為尚不存在的新收據目錄、WINDOW_BIN指向abandon-final-build-v25/colonization-window；字串圖集及現行模板沿本目標的議會接線。probe_goal181_replays.sh指定同OUT及原始COLONY01.SAV。來源探針probe_goal181_buy_sources.go在獨立模組內執行，指定--marker-prefix @ABANDON、--from 70000000 --to 82000000、--verify-step為該GUI輸入終點，scratch由正常COLONY01.SAV複製；其輸入／完整終點與同目錄三側控制均須一致。範例可丟棄模組為abandon-source-v21，沒有注入快照。原始比較位置0E2D:0832、F3A6／CX1及返回9320:00D7由檢查器每次重驗，不相信人工別名。

matrix-v25為39PASS、0SKIP／FAIL／過期／指紋衝突；census-v25為1896列、794已顯示／1013待接（正常642／特定局勢371）／89不可達。只將ABANDON由待接升已顯示；ABANDON2不由同文選項提高完成數。普查兩次與docs相同；移除棄城後793、移除資金不足BUY後793、移除可支付BUY後791；分類刪除／重疊均拒絕。確認像素、取消殘像、錯來源鍵、錯位移、錯輸入綁定及偽造RAM六個負例拒絕，原版缺失SKIP77。

正式收據SHA-256：

- matrix-v25/matrix.json：4821af3136e9911df2d3bba780cb876610862986957c565762619a3e5fbb4585
- census-v25/census.tsv：8ad49e94872145943fe64739593a6400cdb7390f6d999c66e61a5d8c1ba891b0
- census-v25/report.md：7500e2c3af681c06c2de98cf65469a709394b2c4e3330420ca2291e1b55aaf08
- census-v25/repeat-and-negative.json：4f16b0319341a6d2ccb6984e502343ffd6d8ab353c9a02450bbdb504baca549c
- city-abandon-v25/city-summary.json：3706514c656f85fddc3e3cd070057ac04917b25abb116a75b467433dbc307e63
- city-abandon-v25/negative-checks.json：b61c69a1190d8a39d135b145547090658bba3f31a3786e02a96e870a55a10040
- city-abandon-v25/abandon-source.log.matches.json：b0f7a0221ea301991954140a21c9f37ed0d66363adc47d278335ea19984dfab2

正式二進位abandon-final-build-v25/colonization-window：8ac21a84e0792917a6e20c13ff0239a1f3a2c8c1300c41774ee71e94591465ec；它是本機中間物，非dist-all交付。舊Windows／macOS預檢沒有本次修正，須後續重建與驗收，不外推平台完成。Issue #56主機遠端回讀仍OPEN、無留言；不宣稱接受棄城、ABANDON2警告、已裝備、武裝、多人口或全部殖民地文字完成。本輪未commit／push／發Release。

## 下一個正常單位入口探勘

既有city-join-v4截圖顯示士兵在位置(51,27)，B實際開出新殖民地命名，不能視為加入Jamestown。已另建可丟棄soldier-city-probe-v26.sh，正常主選單讀原始COLONY01.SAV後只按Space啟用下一單位、Down一步，再截圖並正常關窗；收據目錄soldier-city-v26。使用已驗abandon-final-build-v25及現行字串圖集／模板，沒有修改存檔、注入單位或地形。先核對實際移動與畫面，再選後續正常進城操作；這是探勘，尚不接入正式矩陣或增加普查數字。

v26第一次Space先觸發已驗TUTORIAL14，Down當時仍在教學提示，沒有移動士兵；保留收據，不把截圖名稱soldier-south視為已移動。終點64200000步RAM d2b52be935b4a1c67d508efdf86a995cce0616d111677333d764392b41ce5bf2，輸入f31207260eda644b9605bdbc30c5763dcc6e3eac28189b0cc9e6cb7fad155547。下一版soldier-city-probe-v27.sh先用正常Enter關閉提示、取樣，再Down；收據soldier-city-v27。這是GUI操作順序修正，不改正式轉譯程式或原版移動規則。

v27已正常關閉教學，但Down輸入收據雖已送達，取樣畫面仍在(51,27)、行動1；不稱已向南移動。終點70800000步RAM fecb01ea36d0f383982a4ceea2a2110e0dec13c92923d621c7cf07f2ace22bfb，輸入a93fb2eb852fb6e993db33bd2d20ff0cb7f21f091ca10b1e3aba5726a1745ffc。v28用soldier-city-probe-v28.sh保留上述序列，另送正常數字2並取樣比較；收據soldier-city-v28。只探索原版接受的玩家操作，不據此猜改正式鍵盤映射。

v28數字2後畫面地圖平移，士兵仍(51,27)、行動1；未進城，不能歸因於前端鍵盤錯誤。已回查正常玩家路徑路由與既有load-unit-v5的View選單證據，首項為移動單位。v29沿已驗View→Home→Enter入口，再啟用士兵、關教學、Down，另試數字鍵盤1；腳本soldier-city-probe-v29.sh、收據soldier-city-v29。須看新圖確認當前模式及可通行格，不推定方向鍵應穿越水面，不改遊戲規則或正式映射。

v29正常送達kp1後，士兵圖像向西南移到另一格並露出新地形；但末張取樣右側仍(51,27)、行動1，不用中途圖像宣稱移動完成。輸入5d0a5e4465921e6fdab8cdf22b25ee6b0484e338d4cfb4054ef89d6c7109bb8d；終點92400000步RAM 00655d0445c9ba7ca70c07c3e1a6bbb4c9d92fa1820f2f12843595f0925200a5。v30使用soldier-city-probe-v30.sh、收據soldier-city-v30，增加20M有界等待與soldier-settled取樣，核對原版動畫／重畫完成後的畫面；沒有新增遊戲或前端行為。

v30增加等待後實際出現議會選擇框，候選為Adam Smith、Henry Hudson、Francis Drake、Benjamin Franklin及William Brewster，均由既有圖集顯示中文；這組尚未做三側／安全區驗收，不提高普查。沒有正常進城或加入第二居民。終點118000000步RAM 664cb9d2c99981f0d6a56ba139e0dc329ee8c24c664f1f99fd7f10f1e523c6b7，輸入1e9641a1f8d318a8d98072cc62aaff74c3e7f87ba3af1f54ef4ff17f237aafee。下一步沿正常選任與下一年度，確認士兵完成移動後的位置，再走進Jamestown；不能從動畫中的右側舊欄位推定未移動，也不修改地形來通行。上述所有探勘只在忽略的workplace，現行矩陣／普查仍matrix-v25／census-v25。

## 讀檔成功正式採用與雙居民保存勘誤（2026-10-01）

load-normal-v43通過tools/check_goal181_load.py；正式前端load-final-build-v42的全部Go回歸通過，LOADGOOD限定CONFORMED見規格035。三個原版取樣點與四側完整終點／初始COLONY02相同，正文30px，中文差異只在安全區，關閉提示後無殘留。六個破壞收據負例拒絕、缺原版SKIP77，正式負例採negative-final.json；先前夾具改寫輸入JSON的紀錄保留。可提交正常GUI／重播入口為tools/probe_goal181_load.sh，來源工具沿tools/probe_goal181_buy_sources.go；私有v38只增加DOS檔案操作匯出。

matrix-v47為40PASS、無SKIP／FAIL／過期／指紋衝突。census-v47兩次逐位元組相同：1897列，795已顯示／1013待接（正常642／特定局勢371）／89不可達、EXE346，未歸類與未使用樣式0。只新增LOADGOOD已完成；正常槽位清單合併觀測e4351e498b79另列pending，原始來源位址未知，不能稱為獨立新模板或已中文化。移除本次矩陣列後完整回到v25的1896／794／1013，分類並沒有虛增其他已完成來源。第一次完整矩陣180秒逾時為驗證資源問題，timeout-attempt.txt保留；相同檢查器命令增加進度輸出後有界乾淨重跑通過。

v41正常第四列墨跡中心已生成COLONY03.SAV，11個共同取樣點及四側完整原版狀態／新舊存檔位元組相同。v45觀測的94628375步DOS AH=3Ch建立COLONY03.SAV，94628415步AH=3Dh開啟同檔，Wrote只有03；94757031步實際查詢SAVEGOOD。原始查詢0E2D:0832、F3A6／CX1、返回9320:00D7，GAME.TXT讀入位移1536／512位元組至1C6A:E962；完整107400000步RAM b16aa0a125e455172585e26d7fca028e3a23714525ea1f7d66346b6ebbfdebd0、輸入5fc362812c6b1d17d083c2000edf137889ac4d97b0ede17fcd5ee25be57e29ca與正常GUI相同。DOS操作未記錄CS:IP，不把查詢位址冒充檔案呼叫位址。這只確認正常保存入口，SAVEGOOD中文正文仍待驗。

正式收據SHA-256：

- matrix-v47/matrix.json：9034f01c8f4d26dc7c60061dd6e2a35f199b1f86873ed2fd243489d6f13babef
- census-v47/census.tsv：435b7177020f4446d4fdb2309641d96cca1e361de256e8a775468f7e248b7203
- census-v47/report.md：7fed6ec2b7ead080bec29583336d49518423add6ed0c727f08b8c5d750e46b5e
- load-normal-v43/load-summary.json：831babea02a6177378867b88d9bef43ed257fce838c7adf7ab96d31c0b98a0b8
- load-normal-v43/trace.json.matches.json：82c2f995eecdc94007e02e3ce546d717172ef0f3c7f8be5ba03513c30d1c5881
- load-negative-v46/negative-final.json：f9abe49bc09a9bb15ecd03814dbc079c8bf9ab306f00e229a69afa3d4835bc89
- soldier-city-save-v41/normal-save-summary.json：11f66730f7201c88dd38f05b005c463fbbd6b889b616dd0c6bcf9ba4eccc0051
- save-source-v45/trace.json.matches.json：19d32059438ad5e6cdcc735e44db60bbcf052a2ae8c008490eba0dc9396a3be1

v48正常主選單第四欄讀回03後見兩居民／50火槍。v49點職業第二頁士兵後，原版圍欄士兵出現、火槍庫存0；仍須完成三側原版狀態核對，沒有新增中文完成數。後續武裝、單位選項、港口、報告、國王／事件、其他存讀檔與三平台封包／推廣片仍待驗。

v49續驗已完成：七個共同原版取樣點、正常GUI／中文／原文／缺圖集完整CPU、RAM、索引、色盤、輸入與開檔一致，初始COLONY03.SAV四側不變；正常讀回兩居民／50火槍，點士兵後原版圍欄出現士兵、火槍0。結果見equip-two-v49/normal-state-summary.json，不增加中文完成數。正式check_goal173_census.py通過，移除BUYME0／BUYME1／ABANDON後顯示數分別794／792／794，刪除或重疊分類負例均拒絕。主機gh核對Issue #50～#61均OPEN，#61仍要求其他存讀檔、教學與版畫逐列驗收；未寫入遠端。

## 2026-10-02：城市改名正常來源移交

目標178的codex-audit/colony-orders-gui-v91已正常開出城市改名框，十二張真GUI／共同原版點、四側完整原版及存檔通過；正文GAME.TXT:0x00000F5C及STRING:input-label顯示中文，但沒有兩欄獨立字級量測、原始來源歸屬及正常取消的欄位驗收，維持DRAFT，不提高清冊。收據、固定輸入／工具／來源指紋與位址基準由[目標178](178-orders-disabled-map-labels.md)的v91限定結論索引。下一步沿正常城市標題開框並取消，補字高／基線、最長譯文、來源及安全矩形後再審READY；不改姓名英文或原版存檔。

## 城市改名正常取消續驗（2026-10-02）

`workplace/reports/goal181-colony-rest/rename-gui-v50.sh`／`rename-gui-v50/` 從正常主選單第四欄讀已驗COLONY03、進城、點城市標題開改名框，取樣後用Backspace與英文字母n編輯，再Escape取消、返回世界並正常關窗。不裝備士兵，不藉其他選單意圖推定命中。編輯內容是原版玩家資料，中文只覆蓋提示及標籤；不保存或更改原始COLONY03。

沿未改v65正式前端與既有圖集；私有有界暫停擷取沿目標178 v91已逐像素對齊的方法，finally必恢復，外層240秒／Xvfb trap。改名來源GAME.TXT:@RENAMECOLONY目前pending，原始兩行為提示及Name標籤。規格035輸入標籤機制已READY，但此新來源的字高／基線、兩欄量測、來源歸屬及正常取消尚待驗，不提高807完成數。

同目錄replays.sh／check-state.py保存中英與缺圖集原版／GUI核對；`rename-source-v51/`沿probe_goal181_buy_sources.go的@RENAMECOLONY原始查詢、原始讀取與同輸入完整終點補證。`rename-layout-v52/`複製v65未改的Go來源，透過正式排版函式量測本兩欄的字級、基線、最長譯文與超界回退；原始資料及像素只存workplace。正式檢查器與source_ids需證據審查READY後才接矩陣，兩個觀測欄位只對應一個原始段落。

城市改名欄位已依[規格035](../spec/035-dialog-overlay-draft.md)／[規格036](../spec/036-line-list-and-centered-text.md)審查READY。正式檢查器入口為[check_goal181_rename.py](../../tools/check_goal181_rename.py)，只採兩欄及正常編輯／取消。後續收據存rename-check-v53/、rename-matrix-v54/、rename-census-v54/；這些目錄只保存本輪檢查、負例、矩陣與可反向核對的普查中間物。正式矩陣採tools/verification-matrix.json，清冊仍由tools/text_census.py生成，不另建現況表。

## 城市改名正式採用（2026-10-02）

rename-check-v53/rename-summary.json正例與negative-summary.json十種偽造拒絕、缺原版SKIP77通過；rename-matrix-v54/matrix.json為43PASS。rename-census-v54/a.tsv及a.md兩次重產相同，只有RENAMECOLONY的完成狀態提高；移除新矩陣列，TSV／報表逐位元組恢復v83的807／1001。最新為808已顯示／1000待接／89無法正常觸發，分母1897。其他五列只追加本收據的命中／既有欄位紀錄，狀態不變。規格035／036已限定CONFORMED；接受改名、其他姓名長度與其餘城市／港口／報告仍待驗，Issue #56維持進行中。

rename-layout-v52/audit.go只附加觀測，measure-second.sh重播相同正常輸入；第一次診斷退出保留attempt1.log，第二輪完整原版終點一致。rename-check-v53/check-negative.py保存可重跑負例；rename-census-v54/census-check.py保存三次普查與反向核對。來源工具沿tools/probe_goal181_buy_sources.go --marker-prefix @RENAMECOLONY --from 55000000 --to 85000000 --verify-step 89000000；正常GUI及圖集／存檔掛載沿rename-gui-v50.sh與同目錄replays.sh，均只在有界Docker內執行。正式使用入口不改，原始素材與所有畫面只留workplace。

收據SHA-256：

- `rename-matrix-v54/matrix.json`：`14c283fa5c32fab98b38d1d2e657151d2fa5740617ea153621a244e94460e96f`
- `rename-matrix-v54/verification-matrix.md`：`f48d05bfd9e001cd1fdb6fa1ca33805a106ca99c1e007fd8d591abe6023be44c`
- `rename-census-v54/a.tsv`：`d40e36f797da79661c1c682c923fae00973c76cd86fff5ab3749449d8a0a35c6`
- `rename-census-v54/a.md`：`77180af1d39c1ef0840588cf2cbfea440d6977053c536a4f78c7d3b93fb52a0a`
- `rename-census-v54/census-summary.json`：`d5080bc2b9637a6e7180b00df4fda729bf98bd5b366e2a1640c27b65d8ed6b2f`
- `rename-check-v53/rename-summary.json`：`7244097e0715388ca6aec9412910735552c0b21952d2e72eb423f0b535936728`
- `rename-check-v53/negative-summary.json`：`2698a38df757c35e299b88abffb6f6794db09bd33f5bf59445345f26be24e551`

排版邊界補驗入口：rename-layout-v52/rename_boundary_test.go、boundary-test.log。標籤長字串改為單一前綴欄分隔符加200次中文字，避免先因重複分隔符缺字回退；實際正文30px／標籤29px及真正寬度回退通過。audit.go已同步，原版GUI與正式來源不變。

下一個玩家阻塞為已正常命中的SAVEGOOD：v41在95040000步顯示Discoverer Walter Raleigh of the English (Spring 1496) saved as COLONY03.SAV.，仍因複合值未匹配而回原文；v45已確認正常保存與來源查詢。原始正文位移1977、長27、SHA-256 68950b5338b58ed3b14b56bcc94333d8794be024547b7be88d4323e44ed64284。兩個STRING變數含複合描述與檔名，不直接沿用只驗LOADGOOD的檔名例外；先拆分原版描述來源與玩家姓名資料，再補逐欄量測與DRAFT／READY。原版資料與存檔格式維持不變。

## 存檔成功提示私有原型（2026-10-02，DRAFT）

既有正常v41／來源v45已確認SAVEGOOD兩個STRING變數。完整提示尚未載入：addDraft只加入單行清冊，原版把提示折成三行，不能逐行還原變數；複合描述也尚未對應。F10既有score-title已展示難度、姓名、國籍、季節及年份的相同成分。原始NAMES.TXT的DIFFICULTY／LEADERNAME／NATIONALITY／SEASONS列可作角色與譯名來源，玩家姓名沿已決定保留原文。

`save-prototype-v55/`複製未改v65正式來源，僅在私有副本讓已核對GAME.TXT:0x000007B9加入完整模板；存檔描述的難度／國籍／季節查既有詞典，姓名及數字保留，檔名限定已取證COLONY兩位數.SAV。其他格式或不可繪字元回原文，不猜補。原版SAVEGOOD模板的兩變數只在此欄處理，不擴張LOADGOOD／ABANDON。私有排版與正常同輸入重播為DRAFT證據，正式來源不改；未審READY不得接矩陣或提高808完成數。

原型重播保存同v41輸入與107400000步完整終點，字高、基線、安全矩形及候選量測同目錄保留；正常GUI收據預留`save-gui-v56/`，同GUI輸入來源`save-source-v57/`及正式欄位排版`save-layout-v58/`。這些目錄只用於本輪存檔提示的來源、排版、GUI及反向驗證，不另建現況表。既有原版資料／輸入唯讀，保存只寫各自scratch工作副本。

SAVEGOOD已依[規格035](../spec/035-dialog-overlay-draft.md)／[規格038](../spec/038-string-overlay-draft.md)審查READY。私有v55完整原版與v41原文控制逐位元組一致，提示30px、100檔名及160描述組合量測通過；只有一條舊正常原版輸入，沒有把候選組合當成原版路徑數。正式來源將在save-final-build-v55/組裝與回歸，save-gui-v56/正常另存新空列驗收；此來源只用於存檔提示驗證，不作新的發行版。

正式驗證入口為[check_goal181_savegood.py](../../tools/check_goal181_savegood.py)。本輪檢查、負例、完整矩陣與反向普查分別存於save-check-v59/、save-matrix-v60/、save-census-v60/。v58的候選量測須在diagnostic之後執行correct-candidates.sh，以正式換行及高度契約補算各候選；原版重播與正式選定30px不受此量測夾具修正影響。

## 存檔成功提示正式採用（2026-10-02）

save-final-build-v55全部Go回歸通過；正常save-gui-v56的七張GUI與三側原版取樣、四側完整CPU／RAM／索引／色盤／輸入／開檔一致，舊COLONY03不變、新COLONY00逐位元組相同。v57同GUI輸入的SAVEGOOD查詢、GAME.TXT來源讀取及DOS建立／寫入新00均已核對；v58逐欄安全區與原版大寫／數字高、30～20px候選、最長候選及超界回退通過。規格035／038限定CONFORMED；只新增一個SAVEGOOD原始段落，其他存檔結果、槽位清單及Issue #61仍未完成。

save-check-v59正例、十二種偽造拒絕及缺原版SKIP77通過。save-matrix-v60為44PASS；save-census-v60重產兩次及反向對照通過，最新809已顯示／999待接／89不可達、分母1897，正常待接629／特定局勢370。去除SAVEGOOD列，TSV與報表逐位元組恢復808／1000。候選量測缺30px圖集及原有中文狀態欄殘字斷言均為驗證夾具問題，已按正式函式及開框前／後同差異修正，未改原版。來源工具缺Go模組設定的兩次失敗沒有執行原版，修正為v51已驗模組後同容器乾淨重跑通過。

正式二進位save-final-build-v55/colonization-window SHA-256 `a186f310dd170a479c0de4348376126747b9c957a12205bcd5c80c6e348f1406`。正常GUI入口save-gui-v56.sh與同目錄replays.sh；來源入口save-source-v57/probe.go，參數 `--from 63000000 --to 68000000 --verify-step 77200000 --marker-prefix @SAVEGOOD`。量測入口save-layout-v58/prepare-measurement.py、diagnostic與correct-candidates.sh；驗證入口tools/check_goal181_savegood.py，負例save-check-v59/check-negative.py，普查save-census-v60/census-check.py。均在既有有界Docker工具鏈內執行，所有原版素材／存檔／畫面只留workplace。

收據SHA-256：

- `save-matrix-v60/matrix.json`：`994778027c6cda2d48a2f2fbc7f2ca08427342319267eecc422eb7204d9efd4f`
- `save-matrix-v60/verification-matrix.md`：`8576fcc71802f1d0507d3380fc9715f0c37dacf1e9fed5d99064ae04ccb2d1c6`
- `save-census-v60/a.tsv`：`f7c525c9c7a63c3a9318f757dd75aa397984b6c579a7f83f27f578d9c0e10277`
- `save-census-v60/a.md`：`80e7c3008522aac459ed3533269fd846fb0f09ed0c81583ffd94e41c3e9a1ef7`
- `save-census-v60/census-summary.json`：`63d247cae950c389d8c85fb38c78a9a923e8f2d302b20a1382b313b2062b594c`
- `save-check-v59/save-summary.json`：`f2f7acefd277a4b9c064672718895eb3eb4cddb5263d7a43b3201e4c044c2eb1`
- `save-check-v59/negative-summary.json`：`28311f26e77e4d1462df9e522730ca84b1b2c943426729907f1b54235870d015`
- `save-source-v57/source-query.log.matches.json`：`499c5596897be7538a33b06dc6c5781797aa3002c451158d4879ea3b72989563`
- `save-layout-v58/save-measurement.json`：`c95347164caec255d6755b60d16b72dd6d51212ce5d38661deb8b4ef05dfc82b`

## 存讀檔標題與槽位清單續驗（2026-10-02，DRAFT）

目前v56正常讀檔標題LOADGAME因screen-sync-timeout回原文，SAVEGAME標題已顯示中文；兩邊槽位清單均因line-no-template回原文。不能以來源事件或譯稿存在推定已顯示。Issue #61主機遠端回讀仍OPEN，要求正常GUI／同輸入原版與反向對照，不只成功提示。

`slot-diagnostic-v61/`沿v56正常輸入及現行正式v55副本，僅附加標題同步、印字逐欄與槽位來源觀測；`slot-source-v62/`重生LOADGAME／SAVEGAME原始查詢及同輸入終點。原始資料、存檔與畫面只留workplace，正式來源不改。先確認讀檔畫面使用的原始畫布及不匹配原因，再按規格035／036／038補DRAFT及READY；槽位合併EXE觀測仍pending，不猜新的來源鍵。

v61完整診斷與正常v56原版終點相同。讀檔標題僅安全區左下角(64,74)一點在真VGA與邏輯畫布不同，整段等待均未同步；存檔標題已同步。`slot-source-v62/read-diagnostic/`只追該點原始寫入者及槽位原始字串讀取，不以加長逾時或容許像素不符猜補。

`slot-prototype-v63/`為可丟棄顯示原型。LOADGAME標題候選安全區底緣限於原文字形後一列，避開下一槽位反白區；槽位列表原型只在緊接LOADGAME／SAVEGAME標題時使用已驗描述角色，空欄與姓名保留既有語意。字級與安全矩形由原版cap高5、讀檔行距6／存檔8逐欄量測，不改原版畫布、滑鼠座標、存檔或選項。此原型不進正式來源，不接矩陣，不提高清冊。

v63已在兩個原版取樣點顯示中文，完整原版終點與v56相同；仍有反白重印時回原文的缺口。`slot-prototype-v64/`沿v63加驗重印時的已觀測標題生命週期及每列字級候選，不把同文列表在其他畫面套譯。只有來源、反白、關閉、原版完整狀態與字級／超界全部證據齊備後才審READY。

v64已驗反白重印及160描述／七種拒絕／七種來源生命週期守門。關閉期間的最後一次清單仍有部分墨跡存活，不能只依原有alive判定啟用整份清單；`slot-prototype-v65/`加驗本清單所有已觀測文字像素完整存活的條件，保留v64收據，不把部分存活當成完整欄位。

## 存讀檔欄位證據審查READY（2026-10-02）

v61～v65完整原版與v56正式控制逐位元組相同。v65來源／墨跡完整存活、標題安全區、反白重印、六個啟用取樣點、兩首屏區外無差異及關閉後四畫面相同均通過；最後部分清單拒絕。v64／v65的160描述、七種拒絕與七種生命週期守門通過，兩清單各160候選最長516像素，超長ASCII姓名確實由寬度回退0。已依規格035／036／038審READY，下一步依本契約實作來源綁定空欄值、欄位回呼及安全區／生命週期，重烘受新譯稿綁定影響的字模後做新正常GUI／三側驗收。

正式來源／譯稿／矩陣未改，仍44PASS／809已顯示／999待接。沒有把私有回放當新真GUI，沒有把原型測試當CONFORMED；合併EXE觀測與其他存讀檔結果仍待驗。各目錄replay.sh、prepare-*.py、check-prototype.py及Go測試保存重生入口，需沿既有Docker／Go／圖集／COLONY03唯讀種子契約執行。

證據SHA-256：

- `slot-prototype-v65/prototype.json`：`bf1ec929385551411f9868bdc4de7727609d2923834710ffda807d31a212c107`
- `slot-prototype-v65/measurements.jsonl`：`71557b732d7869a3b48a361900cfb43943bebd27f82f48bd3bb627436ed5777a`
- `slot-prototype-v64/grammar-scope-cases.json`：`fe0a32cb5560352792ccf93464eddb4a22753b589b0be4f75638d285b345ee10`
- `slot-source-v62/title-query.log.matches.json`：`930e99960cbd70c8e58e36252341fab9ec7c71038308b5f32d4ef688cd5a544b`
- `slot-source-v62/read-diagnostic/reads.log.matches.json`：`e6299461afd7ececa5ae5c7c8795776e93d03ce2ed807bc08e823efc386206a8`
- `slot-prototype-v65/layout-cases.json`：`51569e36d08cc591a0537b644a3329fed860238e097ed4de846a37f902aa0497`
- `slot-prototype-v65/prototype-summary.json`：`d777936d8d9a1ffc1d86fecb61a9edf784d229139a501487ee77df118e1071a6`

## 2026-10-02：READY 槽位覆蓋正式接入

- `workplace/reports/goal181-colony-rest/slot-formal-build-v66/`：規格035、036、038的 READY 實作、完整 Go 測試與建置；驗收前不取代現行 v55。
- `workplace/reports/goal181-colony-rest/slot-fonts-v66/`：固定 rich2-py 映像重烘，保存現行譯稿綁定的圖集與專用欄位字模。
- `workplace/reports/goal181-colony-rest/slot-gui-v67/`：新正常 GUI 輸入與畫面，供三側同狀態及來源重播。

操作入口為 `workplace/reports/goal181-colony-rest/slot-gui-v67.sh` 與 `slot-replays-v67.sh`，沿用有界程序、正常滑鼠輸入及三側獨立原版存檔。

`workplace/reports/goal181-colony-rest/slot-source-v68/` 以 v67 新正常 GUI 輸入，重播兩個標題原版查詢、空槽讀取與完整原版終點。探針沿用 v62 的受控觀測；前100筆讀取只涵蓋先遇到的清單，不宣稱涵蓋所有原版讀取。

限定檢查入口為 [`tools/check_goal181_slots.py`](../../tools/check_goal181_slots.py)。
`workplace/reports/goal181-colony-rest/slot-verify-v69/` 保存正例、破壞性反例及缺原版略過結果。
`slot-matrix-v70/` 與 `slot-census-v70/` 保存全矩陣及普查兩次重生、移除新列後的反向比對。

### 正式驗收結果

v66～v70存讀檔標題及槽位清單已限定CONFORMED。九GUI、三側及v55程式同現行譯稿／字模對照、獨立原版來源重播、五側完整原版／存檔與核准區外像素均通過。v69正例及16種破壞性反例、缺原版SKIP77，矩陣45PASS。普查815／997／89、分母1901；兩標題升shown，四筆新實際觀測為 EXE:1cea698b230c, EXE:9251e2d6e3d0, EXE:960a3ebe1267, EXE:ebff9ad62c02。EXE:e4351e498b79保持pending，未加別名。完整程式、二進位、圖集、GUI、來源及報表SHA-256保存在 `slot-census-v70/formal-hashes.json`。

重生新GUI先用 `slot-gui-v67.sh` 的未使用輸出，設定COLONIZATION_WINDOW_BIN為v66二進位、COLONIZATION_DIALOG_ATLAS與COLONIZATION_STRING_ATLAS為slot-fonts-v66各圖集；初始scratch只含v41的COLONY03。三側走 `slot-replays-v67.sh`，來源走v68 `prepare.py`／`replay.sh` 的新輸出。已生成COLONY00的scratch與舊收據不可覆寫。v55程式同輸入對照的命令另保存在 `slot-gui-v67/baseline-replay.sh` 及WORKLOG記錄，這不是舊發布包對拍。

## 2026-10-02：歐洲港口與報告短正常路徑

遠端Issue #56仍OPEN，三份舊港口組合與其他港口／報告欄位待驗。`workplace/reports/goal181-colony-rest/europe-gui-v71/` 由合法正常COLONY03讀檔後按E進港，取消招募／購買／訓練，返回世界再依原版F2～F10正常報告與翻頁，不注入原版狀態。操作入口為同層 `europe-gui-v71.sh`；原版來源與逐字幾何待本批收據補足。正式三個Go來源與字模沿v66不改，驗收前不提高815完成數。

`europe-measure-v72/` 是正式v66的私有只觀測副本，記錄逐字字色／陰影像素、各清單與字串原版字高、候選字級及實際／超寬回退；不修改原版或正式顯示行為。`europe-source-v72/` 以相同新GUI輸入匯出原版標題查詢，僅用已有原版查詢定位與其實際檔案讀取作來源，不能把其他資源的標記猜掛至GAME.TXT。

港口短正常路徑三側重播入口為 `workplace/reports/goal181-colony-rest/europe-replays-v71.sh`，終點與取樣步數讀取v71新GUI輸入收據，scratch各側只含初始COLONY03。

`europe-prototype-v73/` 沿v71正常GUI輸入，私有候選修正木紋清單的第二陰影色分類及兩個報告模板。固定rich2-py烘製其私有字串圖集，觀測逐欄候選字級、超界回退與陰影／真正混色拒絕；通過審查前不改正式來源或完成數。重生入口為prepare.py、bake.sh、replay.sh及Go測試。

`europe-formal-build-v74/` 是規格036／038 READY的正式來源組裝、完整Go測試及實際字模回歸；`europe-fonts-v74/` 只重烘受模板綁定影響的字串圖集，其他v66圖集不變。`europe-gui-v75/` 由正式新二進位與圖集重新執行正常讀檔、港口及F2～F10；`europe-verify-v76/` 保存限定檢查、反例及矩陣／普查候選。未驗收前仍以v66及815已顯示為目前交付。

正式新GUI入口europe-gui-v75.sh沿v71有界操作；europe-verify-v76下observer／source子目錄重生v75實際輸入的字級候選及原版查詢，baseline-templates.tsv固定舊模板供v66程式對照。三側及舊程式對照各使用獨立原版存檔，不混用舊GUI步數。

限定驗收入口為[tools/check_goal181_europe.py](../../tools/check_goal181_europe.py)，固定v75正常GUI、v76逐欄量測及原版查詢雜湊。v76/batch.json只保存在忽略目錄，含完整原文、實際來源與字級，不能公開或把尚未取樣的欄位算shown。prepare.py、source/replay.sh、observer/replay.sh及v75/replays.sh保存重生入口。

`europe-matrix-v77/` 保存46列全矩陣重跑；`europe-census-v77/` 保存目前清冊快照、兩次逐位元組重生及移除europe-cancel-and-report-fields後的反向比對。入口各為matrix.py及census-check.py，採用前不提高正式完成數。

### 歐洲正式驗收採用

v74～v77限定CONFORMED，109個逐欄量測與26新正常GUI、五側完整原版／存檔、來源查詢及十二偽造拒絕通過。全矩陣46PASS；普查850／995／89、分母1934，兩既有完整清單升shown及33筆新顯示觀測，舊招募EXE:8f3daa9aec62與讀檔EXE:e4351e498b79仍pending。兩次重生與移除新列反向逐位元組相同。三個報表城市名回原文、其他港口局勢／購入成功與全文收尾待驗。目前正式二進位europe-formal-build-v74，menu／dialog／release字模沿slot-fonts-v66，string改europe-fonts-v74/string。完整SHA-256在europe-census-v77/formal-hashes.json，採用腳本adopt-documents.py與綁定檢查font-binding-check.json均由本入口索引。

前述v73候選首次差異夾具誤把report-f3-b當成仍有會期文字；該圖實際已切到議會空房間，原版事件128040000步已suspended。查回路由、原版畫面及啟用區間後訂正為三個新增畫面，不改產品。凍結清冊另排除198M後關閉報表的未量測海上城市名，這不屬本批港口／報表範圍。失敗嘗試與原始收據保留。

收尾稽核入口為 `europe-census-v77/hygiene-check.py`，結果保存於 `hygiene-summary.json`；`worklist-verify.txt` 保存工作清單核驗。

## 2026-10-03：三個報表城市名排版探勘

`workplace/reports/goal181-colony-rest/city-name-prototype-v78/` 只保存可丟棄觀測與版面比較。沿v75正常輸入及正式來源的私有副本，記錄三個Jamestown的原版文字底圖、字高、安全區與相鄰欄位。正式來源、譯文、字模、矩陣及850已顯示計數均不變；未經版面決定與READY審查，不接入正式路徑。重生入口為prepare.py、replay.sh及measure.py。

`workplace/reports/goal181-colony-rest/purchase-gui-v79/` 由正式v74二進位正常讀COLONY03、進歐洲、選500$砲台並觀測後續畫面。這是尚未採用的正常玩家路徑收據，與待選城名版面無相依；未完成來源／字級／同狀態檢查前不接矩陣或普查。操作入口為同層 `purchase-gui-v79.sh`，生成方法保存在v78的prepare-purchase.py。

三側同輸入入口為同層 `purchase-replays-v79.sh`；`purchase-observer-v80/` 保存v79實際輸入的私有逐欄字級觀測與完整終點。生成／操作入口為prepare.py及replay.sh，來源／字級未驗完前保持未採用。

`purchase-source-v80/` 沿v79正常輸入重生原版GAME.TXT標題查詢及完整終點，入口為prepare.py及replay.sh。只記錄探針實際匯出的檔案讀取，不把未查到的LABELS／NAMES來源掛進GAME.TXT。

量測與核驗入口另為v78的update-documents.py、v80的check.py／purchase-summary.json及update-documents.py。v80正例9GUI、五側完整原版、四側共同取樣與實際查詢通過；其餘正式採用閘門見規格035本日DRAFT節，不外推其他購入結果。

`purchase-layout-v81/` 保存六種已知購入單位及數值邊界的實際字模量測。`purchase-verify-v82/` 保存三個正常顯示欄位的凍結來源清冊、來源／字級收據、限定檢查及破壞性反例；原始資料只留workplace，入口各為prepare.py、test.sh及freeze.py／negative.py。通過前不更改正式普查；預定限定檢查入口為 `tools/check_goal181_purchase.py`。

`purchase-matrix-v83/` 與 `purchase-census-v83/` 保存本批全矩陣及普查兩次重生、移除新列的反向比較；入口各為matrix.py及census-check.py。限定檢查入口為[tools/check_goal181_purchase.py](../../tools/check_goal181_purchase.py)，v82正例三欄及十三種破壞收據拒絕、缺原版SKIP77通過後才接矩陣。正式來源／二進位／字模仍沿v74，驗收採用前仍850／995。

### 砲台購入正式採用

v79～v83限定CONFORMED，正常500$砲台購入確認與Enter接受，三欄、九GUI、五側完整原版及四側九共同取樣、原版查詢及不變存檔、13種破壞收據拒絕通過。全矩陣47PASS；普查852／994／89、分母1935，僅REALLYBUY提升及EXE:e9b353ec7941新增實際觀測。兩次重生與移除新列反向逐位元組相同；24個合成排版不計命中。其他單位、取消、稅率與城名A／B未驗。

完整來源、二進位、圖集、GUI、來源探針與生成清冊的SHA-256在purchase-census-v83/formal-hashes.json，採用入口為adopt-documents.py，收尾稽核入口為hygiene-check.py／hygiene-summary.json。重生沿v79的新輸出及初始只含COLONY03的scratch，不覆寫既有收據。

## 2026-10-03：殖民地單位操作及水域工作探勘

`workplace/reports/goal181-colony-rest/unit-gui-v84/` 保存正式v74正常讀COLONY03進城、點城外單位、取消及拖曳既有工作者到水域的探索畫面。只以實際原版回應決定來源，不假定某一點擊必然觸發UNITOPTIONS或NODOCKS；驗收前仍852已顯示／994待接。操作入口為同層 `unit-gui-v84.sh`，生成方法為 `purchase-census-v83/prepare-unit.py`。

v84實際點擊的是工作者，出現職業清單；正常拖到水域只改位置，沒有NODOCKS提示，舊收據保留。`unit-gui-v85/` 改由正常職業清單選Fisherman，只以原版實際回應判定來源；同層 `unit-gui-v85.sh` 為操作入口，生成方法保存於v84的prepare-fisherman.py。

v85正常職業清單選Fisherman已出現NODOCKS中文；`unit-observer-v86/` 與 `unit-source-v86/` 分別保存同一v85實際輸入的逐欄字級／超界觀測及原版GAME.TXT查詢。入口各為prepare.py／replay.sh；同層 `unit-replays-v85.sh` 重生中文、原文及缺圖集三側。只在來源、幾何、原版狀態與正常GUI全部驗證後採用，不外推v84拖曳或UNITOPTIONS。

`unit-right-gui-v86/` 只探勘正常殖民地工作者的右鍵回應，與NODOCKS正式驗收分開。正式前端已轉送三個滑鼠按鈕，腳本仍以有界步數同步輸入；不假定右鍵一定產生COLONYUNIT。操作入口為同層 `unit-right-gui-v86.sh`，生成方法為v84的prepare-right-click.py。

`unit-verify-v87/` 保存v85的NODOCKS單欄凍結來源、字級與原版查詢、限定檢查及破壞收據反例。入口為freeze.py／negative.py，限定檢查入口為 `tools/check_goal181_nodocks.py`；通過前維持852／994，不採用職業清單的新變體或右鍵探索。

`unit-matrix-v88/` 與 `unit-census-v88/` 保存未建碼頭的全矩陣與普查兩次重生、移除新列後的反向比對。入口各為matrix.py及census-check.py；只有限定檢查通過的NODOCKS正文可以提高完成數。v87另保存購買檢查器回歸，舊檢查器來源保留於purchase-checker-before.py。

v88首次有界驗證逾時，兩次普查結果已成功保留；兩目錄resume.py只重跑未完成的全矩陣或反向普查，timeout-attempt.json保存程序逾時範圍，不作產品缺陷或PASS證據。

`unit-options-gui-v89/` 沿既有正常COLONY03讀檔與士兵選任，再點圍欄士兵探勘單位選項。只記錄實際原版回應，操作入口為同層unit-options-gui-v89.sh，生成方法為unit-verify-v87/prepare-unit-options.py。尚未來源／幾何／同狀態驗收前不採用其新欄位。

v89圍欄士兵仍開職業清單，沒有COLONYUNIT／UNITOPTIONS命中。第三波說明書Image028.jpg第41頁指出右下多功能區的單位顯示模式才是單位命令入口；`unit-panel-gui-v90/` 沿正常士兵選任切換該模式，再點其中單位，只以實際回應判定。操作入口為同層unit-panel-gui-v90.sh，生成方法為unit-verify-v87/prepare-unit-panel.py。手冊是操作線索，不代替原版輸出或正式覆蓋驗收。

v90已正常開出士兵選項，當次只有警戒／登船、駐守、不做更動三列，標題及清單回原文。`unit-source-v91/` 沿同一實際GUI輸入追原版標記查詢與完整終點；入口為prepare.py／replay.sh。仍待來源與逐欄幾何，不先增加完成數或將完整五列套到三列畫面。

`unit-observer-v91/` 保存同一v90實際輸入的原版逐字幾何與原版完整終點，入口為prepare.py／replay.sh。未翻譯欄位仍按原文觀測，不以已有圖集自行猜補；v91原版已查到COLONYUNIT及UNITOPTIONS，規格035另開限定DRAFT。

v91的adjacent_test.go／adjacent-test.sh是既有標題匹配器的窄重現，只驗變數拆分，不當成原版或正式修法驗收。套件初始化仍需有界Xvfb，首次缺DISPLAY結果保留adjacent-test-no-display.log。

v91的state-and-gui-check.py／state-and-gui-summary.json核對正常GUI與未改顯示的觀測副本的完整狀態及逐像素畫面，來源探針另核對完整RAM。這是未改顯示的證據，不宣稱三側或新覆蓋驗收。

本批追加現況與歷程的入口為unit-census-v88/close-documents.py；只記錄v89～v91尚未採用的探勘，不改48PASS／853已顯示的正式結果。

## 2026-10-03：士兵標題及三列清單可丟棄原型

`workplace/reports/goal181-colony-rest/unit-prototype-v92/` 保存v90正常輸入的私有候選、逐欄字級與回退觀測。只合併已取證COLONYUNIT同一強調群組的相鄰變數，並加入UNITOPTIONS當次三列的來源綁定分列模板；其他標題或未觀測兩列不據此授權。入口為prepare.py、replay.sh及test.sh。正式Go、譯稿、字模、矩陣與853完成數均不改，規格035仍DRAFT。

v92中文已顯示且原版終點不變，但標題安全區包括單位圖示，尚不能採用。`unit-prototype-v93/` 沿同一輸入改以原版文字墨跡左緣／上緣限制標題安全區，另驗證原始NAMES.TXT的UNIT資料列後才接受單位名稱；不沿用一般術語或數值回退。入口為prepare.py、replay.sh、test.sh及check.py，保留v92重疊收據，不改正式來源。

### 未建碼頭正文正式採用

v85～v88限定CONFORMED，正常職業清單選Fisherman的單欄正文與關閉、30px兩行、八GUI及五側完整原版與四側八取樣、來源查詢／存檔一致。13種破壞收據拒絕、缺原版SKIP77及購買正負例回歸通過。全矩陣48PASS；普查853／993／89、分母1935，只提升NODOCKS，無新來源。兩次重生及移除新列反向逐位元組相同。

正式v74程式、二進位與圖集不改；其他職業、拖曳與右鍵單位選項不外推。完整雜湊、採用及稽核入口為unit-census-v88/formal-hashes.json、adopt-documents.py、hygiene-check.py／hygiene-summary.json。unit-verify-v87/prepare-regression-census.py、purchase-negative-regression.py及census-generator.py保存本批生成入口。

v93原型及22個合成名稱量測通過後，規格035／036已限定READY。`unit-formal-build-v94/` 保存正式來源組裝、完整Go回歸及二進位，入口為prepare.py／build.sh；`unit-formal-gui-v95/` 保存新正式正常單位面板GUI與中英／缺圖集重播，入口為同層unit-formal-gui-v95.sh／unit-formal-replays-v95.sh；`unit-formal-verify-v96/` 保存同輸入逐欄、原版來源、限定檢查與反例，入口為prepare.py／check.py。只有全部閘門通過才採用，48PASS／853已顯示仍是目前正式結果。

士兵選項限定檢查入口為[tools/check_goal181_unit.py](../../tools/check_goal181_unit.py)，凍結／反例入口為unit-formal-verify-v96/freeze.py／negative.py；正式採用前還須矩陣及普查反向比對。

`unit-formal-matrix-v97/` 保存新士兵選項列的全矩陣，入口為matrix.py；`unit-formal-census-v97/` 保存兩次普查、移除新列的反向比對與採用／稽核，入口為census-check.py、adopt-documents.py與hygiene-check.py。段落單位沿既有普查定義，UNITOPTIONS只記當次三列命中，不表示其餘兩列或其他狀態已驗。


## 2026-10-03：士兵當次標題及三列正式採用

v94～v97限定CONFORMED：新正常GUI、兩欄30px、11GUI、六側完整原版、五側11共同取樣、來源、存檔、圖示及兩核准區外一致。22個名稱實際字模與來源拒絕，19種破壞收據及缺原版SKIP77通過。全矩陣49PASS；普查855／991／89、分母1935，只提升COLONYUNIT與UNITOPTIONS段落，沒有新來源。兩次重生與移除新列反向逐位元組相同，三列命中不表示其餘兩列或其他局勢完成。

正式版本來源／二進位／字模、凍結清冊與生成文件的SHA-256保存於unit-formal-census-v97/formal-hashes.json；採用／稽核入口為adopt-documents.py與hygiene-check.py。v95首次缺DISPLAY及批次外層逾時、v96多餘診斷欄位的失敗收據保留，各只重跑未完成的部分。重生使用新的輸出根及乾淨初始COLONY03，不覆寫既有證據。


## 2026-10-03：駐守後選單與船隻入港路徑探勘

`workplace/reports/goal181-colony-rest/unit-fortify-gui-v98/` 沿正式v94正常讀COLONY03、選任士兵及右下單位面板，選駐守後重新開啟選單，只觀測原版實際變化；入口為同層unit-fortify-gui-v98.sh。`ship-port-gui-v99/` 沿同一正常存檔的作用中輕帆船，核對原版Go to Port熱鍵及目的地選單，入口為同層ship-port-gui-v99.sh。生成／操作入口另保存於unit-formal-census-v97/prepare-next.py與probe-next.sh。原版存檔只唯讀取初始種子，各工作副本獨立；新欄位在來源、字級及同狀態驗收前不採用，49PASS／855已顯示保持現況。


v98駐守後原版仍只有三列，Clear orders取代Fortify；標題已中文，整份清單因新列未接而回原文。v99已正常開Go to Port目的地，倫敦／Jamestown兩列仍原文。`ship-harbor-gui-v100/` 沿v99實際位置選Jamestown，等待原版航行，再正常點殖民地，只觀測是否進港，不注入座標或狀態；入口為同層ship-harbor-gui-v100.sh，生成／操作入口保存於unit-formal-census-v97/prepare-harbor.py與probe-harbor.sh。未驗收前不提高855。


v100原版顯示Caravel Docks At Jamestown，正常到港，第一次點城市未開城市畫面。`ship-city-gui-v101/` 沿同一正常路徑再點一次城市，入口為同層ship-city-gui-v101.sh。`unit-fortify-observer-v102/` 重播v98實際輸入，保存未改顯示的逐欄幾何與原版標記查詢；入口為observer/replay.sh及source/replay.sh。兩者生成入口為unit-formal-census-v97/prepare-101-102.py與run-101.sh／run-102.sh。只探勘，不修改正式程式或完成數。


`unit-clear-prototype-v103/` 是v98正常駐守後三列的可丟棄原型，只加入同一已驗證UNITOPTIONS來源第2列Clear orders，不加入未觀測的Move to front。入口為prepare.py、replay.sh及test.sh。正式來源、譯稿、字模與49PASS／855不變，規格036新增DRAFT限定此狀態。


v101第二次普通點擊造成原版航行／回合推進，未開城市，不能當成城市驗收。原始MENU.TXT的VIEW包含~View Pieces。`ship-view-city-gui-v104/` 沿v100正常到港後以該v熱鍵切入檢視，再點城市；入口為同層ship-view-city-gui-v104.sh，生成／操作入口為unit-formal-census-v97/prepare-104.py／run-104.sh。原版自行處理模式與回合，不寫座標或狀態。


v103的check.py／prototype-summary.json驗13張正常GUI、完整原版與存檔一致，唯一改變為駐守後清單安全區；正式來源尚未變時已通過審查。`clear-formal-build-v105/` 按規格036限定READY組裝正式清除命令分列，入口prepare.py／build.sh；`clear-formal-gui-v106/` 保存新正常GUI，入口同層clear-formal-gui-v106.sh。正式驗收前維持49PASS／855，不外推其他單位局勢。生成／操作入口另保存於v105/run-gui.sh。

v105首次Go回歸在歷史unit_layout_test.go仍將Clear orders列為未驗而拒絕，tests-before-new-state.log保留。依本輪READY證據只更新v105副本的該舊負例，未驗Move to front及Fortify Extra拒絕仍保留，新增Clear orders來源正例另驗。更新腳本首次預期清單順序不符，未變更檔案；其後重讀實際測試並限定更新。v94歷史測試不改，再用相同設定及build.sh乾淨重跑。

v104的original-final-local.png只由同次原版final.idx／final.pal重建本機查看，不帶中文覆蓋，不當新增正式截圖。入口同層GUI腳本及原始索引／色盤。


v105正式全Go及go vet已通過，v106新正常GUI實際三列已中文。新GUI輸入與v98獨立保存，不以歷史終點套用。`clear-formal-verify-v107/` 沿v106實際輸入重生原版來源、逐欄觀測及中文／原文／缺圖集／v94舊程式四側。入口prepare.py、observer/replay.sh、source/replay.sh及replays.sh／observe.sh。正式限定檢查通過前不升CONFORMED，49PASS／855保持已驗結果。


第三波說明書Image025.jpg第34頁明載，選取方塊位於殖民地時按Enter可進入城市；v100到港後不再以普通點擊試移動。`ship-enter-city-gui-v108/` 沿正常到港以Enter開城市，入口同層ship-enter-city-gui-v108.sh，生成／操作入口為unit-formal-census-v97/prepare-108.py／run-108.sh。這是正常鍵盤操作，來源只是路徑線索，仍以實際原版畫面判定。


v108未開城市，不能僅憑Docks標題認定當前選取方塊就是殖民地。`ship-select-enter-gui-v109/` 按手冊第34頁完整條件，先沿v104檢視模式點殖民地以選取方塊，再按Enter，觀測是否進城；入口同層ship-select-enter-gui-v109.sh，生成／操作入口unit-formal-census-v97/prepare-109.py／run-109.sh。v100／v101／v104／v108均只作路徑探勘，不提高正式完成數或宣稱船隻選項已驗。

駐守後選項限定檢查入口為[tools/check_goal181_clear.py](../../tools/check_goal181_clear.py)，凍結及破壞反例入口為clear-formal-verify-v107/freeze.py／negative.py。只有完整檢查、矩陣及普查驗證後才正式採用。


v109原版回到1497春、輕帆船4行動值，旁欄顯示Jamestown與有道路的陸地；尚未城市畫面。`ship-next-turn-city-gui-v111/` 沿該正常新回合再點既有城市位置，觀測是否開出港口，不把旁欄名稱當成船隻選項驗收。入口同層ship-next-turn-city-gui-v111.sh，生成／操作入口unit-formal-census-v97/prepare-111.py／run-111.sh。


`clear-formal-census-v110/` 保存駐守後三列的全矩陣、兩次普查及移除新列的反向比對，入口matrix-census.py；採用與衛生另以adopt-documents.py及hygiene-check.py記錄。新列只增加已驗狀態，不把已shown的UNITOPTIONS再算一次。完整閘門通過前不更新正式狀態。


v111已正常開1497春Jamestown，港口有被選取的輕帆船，原文Landing: Caravel可見。它由原版正常Go to Port、回合推進、再點城市而得，不注入存檔或座標。`ship-options-gui-v112/` 沿此路徑再點當次被選取的船隻圖示，只觀測實際選單；入口同層ship-options-gui-v112.sh，生成／操作入口unit-formal-census-v97/prepare-112.py／run-112.sh。尚未驗原版來源與中文欄位，不提高855或宣稱SHIPOPTIONS完成。


v105～v110限定CONFORMED：正常駐守後三列30px，13GUI、六側完整原版、五側13取樣、來源與存檔一致，只有清單區改變，圖示及其他畫面不變；19種破壞收據與缺原版SKIP77通過。全矩陣50PASS，普查855／991／89不變，只加已shown段落的局勢收據。完整指紋與收尾入口為clear-formal-census-v110/formal-hashes.json、adopt-documents.py與hygiene-check.py。未驗Move to front／其他單位狀態／SHIPOPTIONS不外推。


v112首次點港口船隻實際觸發抵達殖民地／裝貨教學框，不能當SHIPOPTIONS。`ship-after-tutorial-gui-v113/` 沿同一路徑正常Enter關教學，再點被選取的船隻追實際選項；入口同層ship-after-tutorial-gui-v113.sh，生成／操作入口unit-formal-census-v97/prepare-113.py／run-113.sh。新教學及船隻欄位仍待來源／字級，不提高855。v110正式清除命令驗收與本探勘互相獨立。


v113正常關抵港教學後，實際開出Options for Caravel及Sentry、Anchor in harbor（Fortify）、No changes三列原文，沒有其他三列。`ship-source-observer-v114/` 沿同一實際輸入追原版來源與未改顯示的逐欄幾何；入口prepare.py、source/replay.sh與observer/replay.sh。這批不修改正式Go或增加855，教學、Caravel標題及SHIPOPTIONS在新來源／候選字級與READY前保持原文。Caravel已在共享海上短名／術語清冊，不新增重複譯稿。


v114/check.py與discovery-summary.json通過13GUI／未改顯示觀測、完整原版／存檔及來源RAM核對；規格035／036追加TUTORIAL12、Caravel標題與SHIP當次3列DRAFT。Caravel及教學已在別份既有清冊，不能重複新增譯稿；同文No changes的來源鍵與23個名稱來源範圍須先原型審查。正式50PASS／855不變。探勘與文件追加入口為v114/close-documents.py。


`workplace/reports/goal181-colony-rest/ship-prototype-v115/` 保存正常v113實際輸入的私有Caravel名稱及三列SHIPOPTIONS候選。名稱只補已驗證NAMES.TXT的UNIT首欄與既有核准術語交集；船隻三列另存獨立模板，完整三列同時命中才採用，避免同文No changes改寫士兵來源鍵。入口prepare.py、replay.sh及test.sh。正式來源、字模、50PASS及855均不變；抵港教學本批仍保留原文。


`workplace/reports/goal181-colony-rest/ship-tutorial-prototype-v116/` 沿v115私有候選，另對已取證TUTORIAL12的STRING0使用既有殖民地名稱顯示回呼。只在完整教學來源驗證、名稱回呼存在且玩家名稱沒有強調控制符時代入；其他教學不外推。入口prepare.py、test.sh及replay.sh。仍屬DRAFT原型，不修改正式Go、譯稿、字模或完成數。


v115船隻兩欄原型及兩種士兵11／13圖回歸通過，仍未正式採用。v116教學的字模及完整原版重播一致，但當時GUI取樣沒有教學框；教學原版在進城後自動出現，舊腳本緊接著點船隻，於108570000步關掉教學，不能把讀字事件當可見中文。`ship-tutorial-gui-prototype-v117/` 改在進城後先等待並抓抵港教學，再正常Enter關框及開船隻選項、Escape關閉。入口同層ship-tutorial-gui-prototype-v117.sh；生成／操作入口v116/prepare-visible-gui.py、run-visible-gui.sh。只修正驗證操作，不改原版或正式來源。


v115船隻兩欄及兩種士兵回歸通過後，規格035／036限定READY。`ship-formal-build-v118/` 按已審查差分接入Caravel名稱與SHIPOPTIONS完整三列，入口prepare.py／build.sh；尚未正式GUI及同狀態驗收，不提高50PASS／855。教學仍使用v116／v117私有原型，不寫入正式來源。


`ship-formal-gui-v119/` 使用限定READY的v118正式二進位，正常進城後先等待抵港教學、正常關閉，再開船隻選項及Escape關閉。入口同層ship-formal-gui-v119.sh，生成／操作入口v118/prepare-gui.py、run-gui.sh。教學仍原文；此批只驗Caravel標題及當次三列，不把教學原型帶入正式程式。尚待新正常GUI、同輸入原版及字級驗收，50PASS／855為v105已驗基準。


v117已取得正常可見抵港中文教學、船隻選單及Escape關閉共14張GUI。`ship-tutorial-prototype-verify-v120/` 重播該次實際輸入的中文／原文／缺圖集並追原版來源，入口prepare.py、replays.sh及source/replay.sh。只驗v116私有候選，不提高正式50PASS／855；TUTORIAL12在同狀態與正常GUI審查前仍DRAFT。


v120另沿v117實際輸入重播v118正式候選作教學未接基準，只審查TUTORIAL12安全區差異、關閉後無殘留及原版不變；入口prepare-baseline.py／baseline.sh，不覆寫其餘三側。


v118正式候選完整Go／go vet通過，v119新正常14GUI已完成船隻選單及Escape關閉。`ship-formal-verify-v121/` 沿v119實際輸入重生逐欄字級、原版來源與中英／缺圖集／v105舊正式對照；入口prepare.py、replays.sh、observer/replay.sh及source/replay.sh。尚未限定檢查與矩陣，維持先前50PASS／855，不外推TUTORIAL12正式完成。


船隻兩欄限定檢查入口為[tools/check_goal181_ship.py](../../tools/check_goal181_ship.py)，凍結入口為v121/freeze.py。正常路徑原版會新增COLONY09；凍結清冊逐檔驗證初始03與新增09，舊案例仍預設僅03。其他原版查詢只保存context_not_adopted，不作新增來源命中。新矩陣及普查通過前不升CONFORMED。


v121限定檢查已通過新正常14GUI、六側完整原版、五側14取樣、兩欄30px、來源及03／原版新增09存檔，左側船隻圖示與核准區外不變。破壞收據入口prepare-negative.py／negative.py，另驗新增09的破壞及缺失；限定CONFORMED仍待矩陣與普查。教學私有v120有一張海上過渡GUI不對齊，TUTORIAL12仍DRAFT；保留差異，不另挑有利畫面。


`ship-formal-census-v122/` 保存船隻兩欄正式驗收的全矩陣、兩次普查與移除新列的反向比對，入口matrix-census.py；只允許SHIPOPTIONS由pending升shown，Caravel標題父段落已shown只加收據。21種破壞收據、原版缺失SKIP77及舊案例未知存檔拒絕已通過；教學仍DRAFT，不採TUTORIAL12。全閘門通過後才更新正式現況。


v118～v122船隻兩欄已限定CONFORMED：新正常14GUI、六側完整原版、五側14取樣，來源及初始03／原版新增09一致，圖示與兩核准區外不變。21種破壞收據拒絕、原版缺失SKIP77及舊案例未知新增存檔拒絕通過。全矩陣51PASS；普查856／990／89，只提升SHIPOPTIONS，兩次與移除新列反向逐位元組相同。採用／稽核入口v122/adopt-documents.py與hygiene-check.py，完整指紋formal-hashes.json。教學v120仍INCOMPLETE_GUI_ALIGNMENT，13／14GUI且不採用；下一步先驗呈現與畫面步數對齊，保留既有差異及DRAFT。


`gui-capture-prototype-v123/` 在v116私有教學候選加入畫布RGBA指紋觀測，取樣以指定遊戲PID暫停全部執行緒，真GUI圖片須與同一發布畫布的指紋及尺寸完全一致才記錄；未呈現圖保留嘗試、恢復程序並等下一次呈現，不送原版輸入。入口prepare.py、build.sh、capture.py與capture-tests.py。正式來源、字模與51PASS／856不改；v120差異保留，不靠挑中文結果或擴大像素容忍值通過。


v124私有正常GUI驗證沿用v117玩家輸入路徑，使用v123畫布指紋同步抓圖。入口 `workplace/reports/goal181-colony-rest/gui-capture124.sh`，輸出 `gui-capture-normal-v124/`，由capture.py自行暫停與恢復指定前端，不送額外遊戲輸入。不改正式51PASS與856來源。


v124首次執行在Xvfb就緒前啟動前端，GLFW初始化失敗；無輸入或截圖，分類為驗證環境。原失敗輸出保存於 `gui-capture-normal-v124-xvfb-startup-failed/`，修正入口等待顯示器就緒後以同一命令乾淨重跑。


v125沿v124真GUI實際輸入，比較v123中文／原文／缺圖集與v118未接教學基準，並獨立查原版來源。入口 `gui-capture-verify-v125/prepare.py`、`replays.sh`、`source/replay.sh` 與 `check.py`。要求14張GUI全等、原版狀態與所有存檔相同，只允許TUTORIAL12安全區改變。私有驗證不提高正式完成數。


v125首次檢查錯用v117輸入的新增09預期，六側實際存檔一致。保留check-before-current-input-save-manifest.py，改固定本次獨立原版來源產生的source-save-manifest.json逐檔清冊，正常03仍原指紋；不更動遊戲或重跑取樣。


TUTORIAL12與截圖同步已完成私有審查，規格035／013限定READY。`tutorial-formal-build-v126/prepare.py` 與 `build.sh` 接入最小名稱分支及觀測指紋；完整正式Go與實際名稱字模待重跑。同步反例公開重生入口 `tools/test_gui_capture.py`；正式正常GUI與同狀態／矩陣前不提高51PASS或856。


正式v126完整Go／go vet與同步反例通過。新正常GUI入口 `tutorial-gui127.sh` 及v126/run-normal-gui.sh，輸出 `tutorial-formal-gui-v127/`；使用正式tools/gui_auto.py的capture_frame_synced，沿正常讀檔／航行／抵港教學／Enter關閉／船隻選單／Escape關閉。正式同狀態及矩陣前完成數維持51PASS／856。


v127首次正式抓圖發現暫停helper漏定義proc，第一張圖前中止。已修正tools/gui_auto.py並在tools/test_gui_capture.py補實際helper的雙執行緒停止／恢復測試，訊號以mock觀測，不送至真程序。失敗輸出留 `tutorial-formal-gui-v127-before-freeze-helper-fix/`；同一命令乾淨重跑。此錯誤屬驗證工具，正式Go來源／二進位不改，先前86個Go測試無SKIP。


正式新正常v127共14GUI已取得。`tutorial-formal-verify-v128/prepare.py`、replays.sh、observer/replay.sh、source/replay.sh沿此次實際輸入驗證中文／原文／缺圖集／v118舊正式、獨立字級觀測與原版來源；使用本次來源產生的03／09清冊。公開限定檢查及矩陣前不升CONFORMED。


v128四側均已正常完成，外層wrapper在結束後報shell語法錯誤。當時修改正在執行的wrapper以補Xvfb等待，造成讀取位置偏移；目前腳本bash -n通過。completed-replays.json獨立核對四側完整原版、RAM及14取樣全齊，只標PASS_COMPLETED_REPLAYS_ONLY，不宣稱整批命令通過。resume-after-wrapper-edit.py保留此分類，後續觀測／來源由相同容器工具鏈乾淨執行，再由公開限定檢查逐像素核對全部既有重播。未刪除或重選原始取樣。


教學限定檢查入口 [tools/check_goal181_tutorial.py](../../tools/check_goal181_tutorial.py)，凍結入口v128/freeze.py。來源查詢、字模與正式來源／二進位、14張正常GUI指紋及本次03／09清冊均固定雜湊。其他查詢保留context_not_adopted，不增加來源完成數。矩陣與反向普查前不升CONFORMED。


v128破壞收據入口prepare-negative.py／negative.py，23項涵蓋正文／來源／生命週期、GUI／原版狀態／存檔、正式來源／二進位、字模與同步收據；portrait反例改在教學安全區外的原版人物上。缺原版檢查明確SKIP77，不替代通過。


`tutorial-formal-census-v129/` 保存正式抵港教學的全矩陣、兩次普查及移除新列的反向比對，入口matrix-census.py；只允許TUTORIAL12由pending升shown。公開限定檢查、23種破壞收據拒絕及缺原版SKIP77通過後才執行；全閘門通過後才更新現況與限定CONFORMED。


v126～v129抵港教學與截圖同步已限定CONFORMED：86個Go測試、go vet、新正常14GUI及畫布指紋與重播全等，六側完整原版／五側14取樣、來源與初始03／原版新增09一致；教學安全區外及Enter關閉後不變。23種破壞收據拒絕與缺原版SKIP77。全矩陣52PASS，普查857／989／89，只提升TUTORIAL12，兩次與移除新列反向逐位元組相同。採用入口v129/adopt-documents.py，完整指紋formal-hashes.json；整體Issue與Goal仍進行中。


v129收尾入口post-worklist.py／hygiene-check.py，將存讀檔／教學共用工作項中的46PASS明示為當時紀錄，補此次TUTORIAL12，未變更完成狀態；WORKLIST重新由JSON生成並核對。正式21份指紋、UID/GID、root-owned與原版追蹤檢查在hygiene-summary.json。Docker主機狀態由收尾docker ps獨立核對。


v130正常港口裝卸貨物探勘沿正式v126與v127讀檔／抵港路徑，從可見倉庫毛皮拖到空貨艙，再開原版船隻選單、正常取消／卸貨，另觀測Shift拖曳。入口同層 `cargo-gui130.sh` 與 `tutorial-formal-build-v126/run-cargo-gui130.sh`，輸出 `cargo-normal-gui-v130/`。只是真GUI輸入與來源探勘，不猜原版規則、不提高52PASS／857，也不加入新的正式模板。


v130早期cargo-loaded取樣沒有貨物轉移，loaded-ship-options仍是空貨艙三列，腳本名稱不作成功證據；shift-cargo-drop才可見27 Furs moved to Caravel、倉庫毛皮0與貨艙圖示。Shift完整規則未知，不改原版。`cargo-source-observer-v131/` 沿v130實際20GUI輸入重播逐欄觀測與原版來源，入口prepare.py／observer/replay.sh／source/replay.sh；只作confirmed觀測與完整原版比對，不提高完成數。後續v132須真正載貨後才開選單，並觀測卸貨。


v132正常載货船隻選單與卸貨探勘沿正式v126與v127入口，按v130已觀測的Shift拖曳裝入27毛皮後才開選單，再正常取消與Shift拖回倉庫。入口同層cargo-gui132.sh與v126/run-cargo-gui132.sh，輸出 `cargo-loaded-gui-v132/`；不把輸入名稱當操作成功，確認貨艙／倉庫與原版事件才採證據，不改正式程式或提高52PASS／857。


v132已載貨四列原文为Sentry／Anchor／Unload all cargo／No changes，卸回倉庫後恢復三列。v133另用正常選單的Unload all cargo命令、Anchor與Clear orders探勘，不改規則；入口cargo-gui133.sh與v126/run-cargo-gui133.sh，輸出 `cargo-orders-gui-v133/`。各命令只在原版既有項目點擊，成功與否由實際畫面／來源核對，不由腳本名稱推定。移貨提示在sea_misses與string_misses為no-template，沿既有印字點觀測，尚未覆蓋。完成數維持52PASS／857。


v133正常卸下所有貨物、下錨與清除命令已取得23GUI。`cargo-source-observer-v134/` 沿該次實際輸入獨立重播觀測與原版來源，入口prepare.py、observer/replay.sh、source/replay.sh、check.py。私有觀測器另記錄未建模板的裝卸貨提示原文、墨跡、字級與來源指標，僅取證，不改原版或正式覆蓋。完成數維持52PASS／857。


`cargo-options-prototype-v135/` 是可丟棄的DRAFT船隻原型。沿v133正常23GUI實際輸入，只增加載貨第3／4／5／6列與下錨第2／3／6列兩種完整組合；既有空貨艙第3／4／6列及士兵來源鍵保留。入口prepare.py、test.sh、replay.sh及check.py。正式程式、譯稿、圖集與52PASS／857不改；原版來源、逐欄字級、安全區、原型差異及回歸通過後才審READY。


v135首次準備在私有observer註解仍寫「私有原型」時錯用正式註解作定位，未寫入Go或建置。保留原始錯誤分類，改以實際私有註解定位，resume-preparation.py只續做尚未寫入的私有Go與入口，不重寫既有規格、索引或原版證據。


v135首次go vet發現私有量測器euInk與正式既有排版測試的同名helper衝突，未執行遊戲。原vet輸出保留，fix-audit-helper.py只將量測helper改為cargoAuditInk／cargoAuditWide，再以相同test.sh乾淨重跑；不更改正式測試或產品行為。


v135正常23圖與兩種士兵24圖、來源／存檔及87Go回歸通過後，規格036限定READY。`cargo-options-formal-build-v136/` 接入最小兩組完整船隻列表，入口prepare.py／build.sh。新正常GUI入口cargo-gui137.sh及v136/run-normal-gui.sh，輸出cargo-options-formal-gui-v137。正式來源已變，限定驗收／矩陣前不升CONFORMED或增加52PASS／857。


正式v136完整87Go與go vet、新正常v137載貨／卸貨／下錨／清除／關框23GUI已完成。`cargo-options-formal-verify-v138/` 沿v137實際輸入獨立重生中文／原文／缺圖集／v126基準、逐欄觀測及原版來源，入口prepare.py、replays.sh、observer/replay.sh、source/replay.sh。正式限定檢查、破壞收據及矩陣前不升CONFORMED，52PASS／857保持已驗基準。


正式載貨與下錨限定檢查入口 [tools/check_goal181_shipcargo.py](../../tools/check_goal181_shipcargo.py)，凍結入口v138/freeze.py。新正常23GUI、來源、逐欄量測、正式來源／二進位、指紋同步與該次03／新增09清冊均固定SHA-256。其他來源只保留context_not_adopted，SHIPOPTIONS父段落已shown不重算；矩陣及破壞收據前不升CONFORMED。


`cargo-options-formal-census-v139/` 保存正式載貨與下錨選單的全矩陣、兩次普查及移除新列的反向比對，入口matrix-census.py；只允許SHIPOPTIONS既有shown段落增加條件狀態收據。公開限定檢查、22種破壞收據拒絕及缺原版SKIP77通過後才執行；全閘門通過後才更新現況與限定CONFORMED。


v139全矩陣53PASS、兩次普查與移除新列反向均已逐位元組一致。首次摘要檢查錯把未採用命中的reached_unapplied附註也限制為SHIP段落，並誤用含位移的父鍵；原始驗證腳本保留。resume-metadata-check.py只重驗既有輸出，不重跑已通過的矩陣與普查：完成狀態零變動，SHIPOPTIONS只加本案例receipts，其餘8列只加本案例的未採用命中附註。來源、譯文與完成度不變。報表scoped_unverified由20至27是本限定案例排除的觀測附註，不冒充新增缺譯或完成數。


v136～v139載貨四列與下錨三列已限定CONFORMED：正式87Go／go vet、新正常23GUI指紋與重播全等、六側完整原版／五側23取樣、來源及03／原版新增09一致；僅兩清單區改變，圖示／其他21圖及關框恢復不變。22種破壞收據拒絕與缺原版SKIP77。全矩陣53PASS，857／989／89不變，只補已shown的SHIPOPTIONS條件狀態，兩次／反向普查逐位元組相同。採用與衛生入口v139/adopt-documents.py／hygiene-check.py，完整指紋formal-hashes.json。移貨提示、Loading短標題、Move to front、其他局勢與整體Goal仍未完成。


v139收尾入口post-worklist.py／hygiene-check.py，將存讀檔／教學共用項的52PASS明示為當時紀錄並補目前53PASS，未變更該Issue完成狀態；WORKLIST由JSON重生並核對。完整21份正式指紋、root-owned、原版追蹤、擁有權及隔離dosgolem上游禁推在hygiene-summary.json。Loading短標題的辨讀圖與勘誤索引見RESEARCH-LOG最新節。


`cargo-message-source-v140/` 沿已驗正式v137實際輸入追移貨及Loading: Caravel原版印字來源。入口prepare.py／replay.sh；在原版0D21:00C6首次讀取每則完整字串時唯讀保存來源指標、暫存器、原始stack words與少量RAM快照，另保留既有GAME來源查詢及完整終點。棧框語意尚未知，不依猜測分類目的地。只是原版證據，正式v136／53PASS／857不改。


v140唯讀探針原版終點與正式v137相同。WatchReads會觀測同字元的多次讀取，原始log含部分後綴；只將完整Loading／27 Furs訊息作正文證據，不把每筆raw都當完整訊息。`cargo-fragment-source-v141/` 在同一正常輸入100～160M區間記錄RAM中兩份Loading、moved to、Furs、Caravel、Jamestown來源片段的實際讀取指令、暫存器與原始棧框，入口prepare.py／replay.sh。指標角色仍待資料流審查，正式v136／53PASS／857不改。


v141的實際輸入、完整終點RAM及03／09存檔均等於正式v137。`cargo-concat-source-v142/` 只在原版0E2D:11CF及11E7／11EB觀測組字參數，限定100～160M步與實際訊息暫存區，保存所有來源片段及複製前後原始bytes。入口prepare.py／replay.sh，目的為區分固定船名與玩家城市名，不以字面同名推定角色。正式v136／53PASS／857不改。


`cargo-cityname-gui-v143/` 沿正式v136正常讀檔／抵港，在城市畫面正常開改名框，將Jamestown改為Caravel，再以原版操作裝貨及Unload all cargo。只觀測固定船名與同字面玩家城市名，不注入RAM／存檔或採正式中文候選。入口同層cargo-gui143.sh，生成／操作入口cargo-concat-source-v142/prepare-cityname-gui.py／run-cityname-gui.sh。原版是否接受改名及是否真正移貨以現場畫面與事件核對，不以腳本名稱作成功證據。


`cargo-strings-prototype-v145/` 是規格038的私有DRAFT候選，唯讀觀測原版0E2D:11CF組字來源，將固定船名與玩家城市名分角色後供既有字串覆蓋。入口prepare.py／test.sh／replay.sh；字型入口bake.sh仍使用font/README.md固定工具鏈。只採已觀測Furs／Caravel，不泛化其他商品與船型；正式程式、譯稿、字模及53PASS／857不改，待正常同名城市、GUI、字級、來源與原版不變性審查。


v143正常改名已接受Caravel，26張GUI與實際輸入已保存，仍待獨立原版來源與狀態核對。`cargo-cityname-source-v144/` 沿該次實際輸入，記錄同字面Caravel的固定船名／城市名來源及原版組字後bytes；入口prepare.py／replay.sh。觀測區间改為100～260M以涵蓋正常改名增加的輸入，不改既有v142收據，不將尚未核對結果列入正式53PASS。


v145初次測試容器漏掛/game，原版相關測試skip及排版讀檔失敗，分類驗證環境；tests-before-game-mount.log保留，補既有唯讀掛載後以相同test.sh乾淨重跑，Go／go vet與來源角色反例已通過。字模由固定rich2-py重烘四模板，只供私有候選。cityname/replay.sh沿v143實際輸入獨立驗同名城市；`cargo-strings-prototype-gui-v146/` 沿正常讀檔／抵港移貨，增加按住拖曳時的Loading提示現場截圖，入口cargo-gui146.sh與v145/run-normal-gui.sh。v145額外入口生成於extra-branches.py；仍DRAFT，不提高53PASS／857。


v145的normal／cityname重播受400秒外層時限中止，部分檢查點保留，沒有完整終點，不作PASS。v146外層500秒亦回124，但原版正常GUI已關閉並完整輸出204200000步、24圖、輸入／RAM／終點JSON；逐張指紋及全部RAM自校對已獨立通過，只標PASS_COMPLETED_GUI_ARTIFACTS，不冒稱整批命令成功。原版模式查詢為單一RAM byte讀取，無等待；兩次逾時後重查試玩契約，不放寬遊戲步數、來源或像素守門。

`cargo-strings-prototype-verify-v147/` 以相同二進位／原版／實際輸入在乾淨輸出重驗normal及cityname，另沿v146新24GUI輸入重生中文／control／缺圖集三側。單批時限按已觀測約500秒的完整GUI耗時設定為900秒，虛擬步数與原版輸入不改，不在執行中修改wrapper。入口prepare.py、run-normal.sh、run-cityname.sh、run-gui146.sh及check.py；本批仍私有DRAFT。


`cargo-held-prototype-v148/` 是規格038的局部DRAFT候選，只讓完整、未遮擋的Loading Furs在按住拖曳時中文；其他滑鼠按住守門保持原契約。入口prepare.py／test.sh，沿用v145同字模／模板綁定並新增部分VGA、游標／對話框及錯來源拒絕；同時修正原型nil詞典分支對非貨物字串的隔離。v145／v147二進位與原始收據不改，正式v136／53PASS／857不改。


v148私有窄守門104個Go案例與go vet通過，零SKIP。新正常GUI輸出`cargo-held-prototype-gui-v149/`，入口cargo-gui149.sh與v148/run-normal-gui.sh，增加按住移貨的可見Loading提示後正常放開／卸貨／下錨／清除／關閉，不送原版測試專用輸入。字模／模板沿v145同指紋，不重烘相同glyph。正式v136、53PASS與857不變。


`cargo-match-scope-prototype-v151/` 在v148私有候選上限制移貨辨識必須以原版格式的十進位數量開頭，普通句子含moved to仍交給原有翻譯；不改四種已觀測Cargo正文或按住例外。入口prepare.py／test.sh，新增普通句子隔離反例。v145／v148二進位及既有GUI收據保留，正式v136／53PASS／857不改；v150將沿v149實際輸入驗新候選與v148／v145差異。


v149新正常24GUI與完整終點已完成，按住拖曳可見裝載中毛皮。`cargo-held-prototype-verify-v150/` 沿此次實際輸入，以v151候選、control、缺圖集、v148及v145重生五側；另沿v143實際輸入回歸同名城市，唯讀來源探針亦重生v149組字參數。入口prepare.py、run-main.sh、run-baselines.sh、run-city-source.sh及check.py。須所有原版／存檔／GUI指紋全等、與v145只差完整Loading提示區，才審READY；正式v136／53PASS／857不改。


v150證據審查後規格038升限定READY，`cargo-messages-formal-build-v152/` 由正式來源接入四個來源角色模板及完整Loading提示的按住例外。入口prepare.py／bake.sh／build.sh；只烘新綁定，不改字形。正式接線已變，但新GUI與限定驗收前不稱CONFORMED，矩陣53PASS／普查857保持。舊歐洲量測測試沿其v73原模板與v74圖集配對，歷史收據不變。


`cargo-messages-formal-gui-v153/` 是正式v152新正常24GUI，入口cargo-gui153.sh及v152/run-normal-gui.sh。`cargo-messages-formal-verify-v154/` 保存正式／原文／缺圖集、未改顯示觀測、副本來源及v136基準；另沿v143正常輸入回歸同名城市。入口prepare.py／build-observer.sh／run-city.sh；新GUI後再建立同輸入重播與檢查器。v152共105Go測試通過，字模逐位元組與v74相同、僅模板綁定改變；目前仍待限定CONFORMED，53PASS／857不增。


正式貨物訊息檢查沿既有tools/check_goal181_shipcargo.py的--cargo-messages入口，原船隻清單入口不變。檢查器須審查清冊綁定、五側完整原版／24取樣、GUI指紋、字級、缺圖集回退、安全區、26圖同名城市及來源／存檔全通過才PASS；本段只索引待驗工具，不代表已驗收。


v153新正常24GUI及畫布指紋完整結束，v154正式同名城市回歸亦exit0。新同輸入重播入口prepare-replays.py、run-main.sh、run-baseline.sh、run-observer-source.sh；v136明確配對其原模板及圖集。原版來源探針與未改顯示觀測分開核對，不把只有RAM的探針說成完整CPU。限定檢查及矩陣仍待完成。


v154/freeze.py將正常來源、四欄量測、GUI指紋、原版輸入、同名城市及來源收據綁定batch.json，公開檢查器審查雜湊由此更新。尚須check.log、破壞收據拒絕、缺原版SKIP77及全矩陣／普查，才更新現況及CONFORMED。


`cargo-messages-formal-census-v155/` 由正式四欄PASS、23個破壞收據拒絕及缺原版SKIP77後建立，入口matrix-census.py。保存全矩陣、兩次普查及移除貨物訊息列的反向逐位元組核對；只採檢查器四欄與三個固定LABELS來源片段，合成壓力及同名城市回歸不增加原版分母。執行期完整字串依既有普查模型另記已觀測變體，數量由實際輸出核對，不預設860。所有閘門通過後才CONFORMED及更新現況。


v155/build-entry-check.sh核對穩定tools/build_window_prototype.py的適配器雜湊已跟上驗過的v152來源，並在stable-build/以原入口組裝、測試及建置。只更新來源雜湊，不改Go module、資料格式或前端行為。舊雜湊入口留build-entry-before.py；現行正式GUI仍以v152二進位為準。


v152～v155四個貨物訊息限定CONFORMED：24正常GUI、五側完整原版／24原版取樣、來源RAM／所有存檔及26圖同名城市回歸通過；四安全區外相對v136不變，缺字模回原文。23破壞收據拒絕、缺原版SKIP77，全矩陣54PASS；普查864／986／89、分母1939，重複與移除新列反向一致。三個固定來源及四個已觀測完整訊息變體分開記錄，回歸與合成不增加分母。採用入口v155/adopt-documents.py；本目標仍進行中，其他貨物／船型、Move to front、報表城市版式及未驗路徑保留。


2026-10-03接續貿易路線：遠端Issue #56仍OPEN，原版TRADE有Edit／Create／Delete三項；清冊ROUTE九欄仍pending。`trade-route-gui-v156/` 使用已驗v152來源與字模、正常主選單讀COLONY03後點TRADE，入口trade-gui156.sh／run-trade-gui156.sh及prepare-trade156.py。沿既有有界控制器，批次間暫停程序以查看畫面，只接受正常GUI輸入，不寫原版RAM。控制期900秒、整批有外層逾時，所有Xvfb／遊戲程序有trap；目前只探勘，不增矩陣或普查。


`trade-route-observer-v157/` 從正式v152複製來源，僅附加貿易路線原始印字與既有欄位字級觀測，未改覆蓋條件或原版RAM。入口prepare.py／build.sh；須沿v156實際GUI輸入重播並驗完整終點，才作來源與量測證據。正式54PASS／864不變。


v156正常GUI已關閉並輸出完整終點；v157/prepare-replays.py先核對每張同步GUI指紋、輸入終點及RAM，run-observer.sh／run-main.sh沿此次實際輸入重生唯讀觀測、正式、原文及缺圖集。來源與完整原版不變性待獨立核對，不增矩陣／普查。先前「未顯示Sea／Land」推定已撤回：實際順序是第一目的地、Sea／Land、命名、第二目的地、編輯器。


`trade-land-gui-v158/` 以正式v152、相同正常COLONY03入口選擇Land，核對另一條正常路線分支；入口prepare-trade158.py／trade-land-gui158.sh／run-trade-land-gui158.sh。截圖前將游標移出欄位，控制期600秒，原版只接受正常輸入。海上v156已存22張GUI，不改舊收據或其誤導的截圖檔名，實際畫面角色由事件與步數核對。正式54PASS／864不變。


`trade-route-source-v159/` 延伸v157的唯讀觀測，補完整含編號標題、Land衝突與清單逐行字級／墨跡。入口prepare.py／build.sh／run-sea.sh／run-land.sh。DRAFT_ONLY字級計算不改畫面，原始run與清單字元分開記錄；沿v156／v158兩份正常GUI實際輸入重播，仍須完整原版終點與畫面核對。原版資料只在忽略的workplace，正式54PASS／864不變。


`trade-native-source-v160/` 沿v156／v158的正常GUI輸入，唯讀觀測九個LABELS片段、港名與國名的實際讀取位址／原指令bytes，並沿既有0E2D:0832查詢探針保存GAME標記。入口prepare.py／run-sea.sh／run-land.sh。原始讀取列標confirmed_raw_read，來源池定位另審查；探針只輸出RAM終點，不冒稱完整CPU證據。正式54PASS／864不變。


v160兩側完成查詢及RAM終點，但九片段讀取紀錄為空；原因是dosgolem的WatchReads只有一個回呼槽，後掛查詢觀測取代了前掛片段觀測。這是探針接線失敗，不能據此推定原版沒有讀取。`trade-native-source-v161/` 保留v160收據，將兩種觀測合併在同一回呼；私有查詢前綴允許@，補貨物提示的GAME來源。入口prepare.py／run-sea.sh／run-land.sh；正式程式及54PASS／864不變。


v161/check.py核對海22／陸13正常GUI、兩側唯讀觀測完整原版／像素／存檔、九個固定LABELS來源池及CARGOLOAD／UNLOAD查詢通過，source-summary.json是原始證據及DRAFT排版，沒有新覆蓋驗收。`trade-route-prototype-v162/` 是規格035／038的可丟棄候選，入口prepare.py／bake.sh／test.sh；只修含數字標題、第一路線Land歧義、London (England)清單列及兩個城市名提示。正式程式／字模／模板及54PASS／864不變，兩側原型與反例驗完才審READY。


v162私有候選111個Go案例、go vet與新模板字模通過，字集及各字級字模與正式v152逐位元組相同，只更新私有模板綁定。初次測試漏DISPLAY，保留環境失敗紀錄，補有trap的Xvfb後乾淨重跑，不記為產品缺陷。`trade-route-prototype-verify-v163/` 入口prepare.py／build-observer.sh／run-sea.sh／run-land.sh，以兩份既有正常輸入驗私有畫面、唯讀實際字級、完整原版／缺圖集；新增body量測只用來補DRAFT。正式54PASS／864不變。


`trade-title-scope-prototype-v164/` 保留v162二進位及v163收據，將標題模板限於已驗原生欄位，避免新模板匹配同文字玩家命名。入口prepare.py／test.sh，字型與私有模板資料逐位元組沿v162，不重烘。限定規格038仍DRAFT，須與v162同輸入像素等值、反例及後續正常GUI；正式54PASS／864不變。


v164新增欄位隔離後112個Go案例及go vet通過，標題譯文仍由私有TSV提供。`trade-title-scope-verify-v165/` 入口prepare.py／build-observer.sh／run-sea.sh／run-land.sh，沿同兩份正常輸入驗欄位限定版、唯讀量測及缺圖集，與v162正向像素／完整原版比對。v162／v163及v164較早字面譯文二進位保留，不覆寫舊收據。正式54PASS／864不變。


`trade-same-name-gui-v166/` 以私有v164從正常COLONY03建立海上第一路線，在原版命名框輸入EDIT TRADE ROUTE 1，核對同文玩家名稱與標題的欄位隔離，再正常開裝卸貨及港口清單。入口prepare-trade166.py／trade-same-name-gui166.sh／run-trade-same-name-gui166.sh。只用正常鍵盤與滑鼠，截圖前移至32,740，控制期600秒。這是實際玩家輸入反例，不作原版固定文本的額外普查信用；正式54PASS／864不變。


v165/check.py兩側35GUI、六側完整原版、共同原版取樣／存檔、與v162正向像素及新安全區／缺字模回退通過。初版檢查器誤以為frames逐項保存STRING安全區，實際只有聚合STRING；改用已審畫面角色與當次來源事件。route-add-destination是第二次港口選單，現場截圖及第二個SAILPORT來源證實，補正分類後通過，不改遊戲或放寬矩形。

v166新正常GUI已接受玩家路線名EDIT TRADE ROUTE 1，標題中文、名字原字；正常Save Game到COLONY00。`trade-same-name-verify-v167/` 入口prepare.py／run-main.sh／run-observer-baseline.sh，先核對全部GUI指紋及兩份存檔，再沿實際輸入核對新原型／原文／缺字模／唯讀觀測／v162。舊v162預期只在同名玩家欄位不同，原版仍須全等；名字輸入不增加原版清冊。仍私有DRAFT，不提高正式54PASS／864。


v167/check.py通過21正常GUI、六側完整原版及新COLONY00／03全等；v164只在原生標題翻譯，同文字玩家名稱仍原字，舊v162的變化僅在名字欄。規格035／038依v161、v165及v167升限定READY。`trade-formal-build-v168/` 是正式來源接線，入口prepare.py／bake.sh／build.sh；新圖集只更新正式來源綁定，不改字形。仍須新正常GUI及正式檢查／矩陣／普查才CONFORMED，54PASS／864保持。


`trade-formal-sea-gui-v169/` 從正式v168、正常COLONY03建立第一海上路線，正常輸入同標題名字、開裝卸／目的地、選倫敦後存到第一槽COLONY00。`trade-formal-land-gui-v170/` 同入口建立陸上路線，開目的地／刪目的地及刪除路線選擇後取消，再正常Save Game。入口v168/prepare-gui.py、run-gui-sea.sh／gui-sea.sh與run-gui-land.sh／gui-land.sh；操作從v166／v158已驗批次重生，抓圖前游標移出欄位，全程有步數界線及Xvfb／遊戲trap，不寫原版RAM。新正常GUI及獨立正式重播未完成前，不增加54PASS／864。


`trade-formal-verify-v171/` 保存正式v168與原文、缺圖集、未改顯示唯讀字級觀測及舊v152，將沿新海／陸正常GUI的實際輸入獨立重生。入口prepare.py／build-observer.sh；重播腳本在GUI完整終點後產生。正式與私有字模／各字級形狀一致，舊v152模板由已保留v162檔去掉唯一新增標題列後驗既有圖集SHA，歷史收據不改。新正常Save Game仍須各側存檔全等及限定驗收，54PASS／864不增加。


v168/build-entry-check.sh沿tools/build_window_prototype.py穩定組裝入口核對新來源指紋並重建stable-build/；只更新已審適配器雜湊，舊入口留build-entry-before.py，原module格式與工具鏈不改。此入口驗證獨立於新正常GUI，不能替代畫面或原版驗收。


v169／v170正常GUI已完整關閉，v171/prepare-replays.py逐張核對畫布／PNG／步數與新COLONY00、初始03後建立新同輸入五側。重播入口run-sea-main.sh／run-sea-observer-baseline.sh與run-land-main.sh／run-land-observer-baseline.sh；舊v152明確使用已驗模板與圖集配對。全批原版／存檔／GUI／欄位審查前維持54PASS／864，兩側新存檔預期以本次GUI結果為準。


正式第一路線的限定檢查入口[tools/check_goal181_trade.py](../../tools/check_goal181_trade.py)，參數--side sea／land、--reports各新正常GUI與--evidence v171。v171/freeze.py將40GUI、六側原版／存檔、字級觀測、112Go及既有來源／同名反例綁定batch.json，兩側檢查器各自只輸出已驗欄位與固定來源；玩家名字與網格城名不採用。仍待公開檢查、破壞收據、缺原版SKIP77及矩陣／普查，不稱CONFORMED。


`trade-formal-census-v172/` 在v171兩側公開限定檢查、24種破壞收據拒絕及缺原版SKIP77後，將海上10／陸上8個已驗欄位分兩列接入矩陣，入口matrix-census.py。只採九個ROUTE固定來源與兩個城市提示；清單與含數字標題的完整執行期變體依既有普查模型另記。玩家命名、網格城名及其他編號／母港不採用。全矩陣、兩次普查及移除兩新列反向逐位元組一致後才CONFORMED，不預設新增完成數或分母。


v172全矩陣56PASS，但首輪普查拒絕帶位移的CARGO來源鍵。原版是一行37／39bytes模板，畫面依原字寬換成兩行；普查完整段落的唯一鍵為GAME.TXT:@CARGOLOAD／@CARGOUNLOAD。公開檢查器的candidate_id與語料offset不改，只把source_ids映射到既有完整段落鍵，不放寬普查唯一鍵守門。舊檢查器／freeze／公開輸出與a.stderr保留；須新公開檢查、破壞拒絕及原兩次／反向普查完成才採用。


v172/resume-canonical.py保留首輪矩陣及普查錯誤輸出，依相同Go／GUI／來源收據與修正後的公開source_ids重新產生矩陣、兩次普查及反向核對。不重跑原版、不改分母模型或唯一鍵規則。


v172重新普查通過：56PASS，1943項中879已顯示、975待驗、89不可達；兩次及移除貿易列反向逐byte一致。尚未採用。定案前追加`trade-port-role-prototype-v173/`，入口prepare.py／build.sh，只在私有副本補港口清單首列定位，其他同文列不得借用港口譯文。依v171正常觀測的第一列來源與y91墨跡，不猜玩家城市資料或原版儲存結構；實際同名城市GUI尚未驗。舊v168～v172收據不改。


`trade-port-role-verify-v174/` 入口prepare.py、run-sea.sh／run-land.sh、check.py；v173私有索引候選使用已凍結v169／v170正常GUI輸入，與v168已驗完整狀態、40共同畫面和兩側所有存檔逐byte比較。只驗防護不影響原正常路徑，不把測試同名列稱成正常城市命名GUI。


`trade-port-role-build-v175/` 入口prepare.py／build.sh，在v174審查通過及來源第0列限定READY後接正式防護，圖集字形與綁定沿v168。`trade-port-role-sea-gui-v176/`／`trade-port-role-land-gui-v177/` 由v175/run-gui-sea.sh／run-gui-land.sh重走正常路徑及Save Game。`trade-port-role-formal-v178/` 保存新GUI、五個獨立重播側與唯讀觀測，入口prepare.py／prepare-replays.py／check.py／freeze.py；公開checker與全矩陣／普查之前不採用v172完成數。


`trade-port-role-formal-v178/` 保存正式v168與原文、缺圖集、未改顯示唯讀字級觀測及舊v152，將沿新海／陸正常GUI的實際輸入獨立重生。入口prepare.py／build-observer.sh；重播腳本在GUI完整終點後產生。正式與私有字模／各字級形狀一致，舊v152模板由已保留v162檔去掉唯一新增標題列後驗既有圖集SHA，歷史收據不改。新正常Save Game仍須各側存檔全等及限定驗收，54PASS／864不增加。


v169／v170正常GUI已完整關閉，v171/prepare-replays.py逐張核對畫布／PNG／步數與新COLONY00、初始03後建立新同輸入五側。重播入口run-sea-main.sh／run-sea-observer-baseline.sh與run-land-main.sh／run-land-observer-baseline.sh；舊v152明確使用已驗模板與圖集配對。全批原版／存檔／GUI／欄位審查前維持54PASS／864，兩側新存檔預期以本次GUI結果為準。


正式第一路線的限定檢查入口[tools/check_goal181_trade.py](../../tools/check_goal181_trade.py)，參數--side sea／land、--reports各新正常GUI與--evidence v171。v171/freeze.py將40GUI、六側原版／存檔、字級觀測、113Go及既有來源／同名反例綁定batch.json，兩側檢查器各自只輸出已驗欄位與固定來源；玩家名字與網格城名不採用。仍待公開檢查、破壞收據、缺原版SKIP77及矩陣／普查，不稱CONFORMED。


`trade-port-role-census-v179/` 在v171兩側公開限定檢查、24種破壞收據拒絕及缺原版SKIP77後，將海上10／陸上8個已驗欄位分兩列接入矩陣，入口matrix-census.py。只採九個ROUTE固定來源與兩個城市提示；清單與含數字標題的完整執行期變體依既有普查模型另記。玩家命名、網格城名及其他編號／母港不採用。全矩陣、兩次普查及移除兩新列反向逐位元組一致後才CONFORMED，不預設新增完成數或分母。


v175～v179第一海陸貿易路線限定CONFORMED。採用入口v179/adopt-documents.py；113Go與穩定入口107Go、40新正常GUI、每條六側完整原版／取樣／存檔、25破壞拒絕、缺原版SKIP77、56PASS及重複／反向普查通過。1943項／879已顯示／975待驗／89不可達。本目標與Issue #56仍進行中，未驗路線編號、母港、網格城市名、自動跑商及報表城市版式保留。原版收據均在忽略的workplace；最終衛生記錄v179/hygiene-summary.json。


`trade-grid-source-v180/` 為第一路線網格城市名稱的唯讀來源／版面觀測，入口prepare.py／build-observer.sh／run-sea.sh／run-land.sh。沿v176／v177已凍結正常GUI輸入及v175正式程式，擴充觀測完整1.  Jamestown／2.  Jamestown及2.  London，記原版墨跡、cap、來源buffer與首欄邊界；候選城市文字只做私有量測，不改正式顯示。須完整原版、所有取樣、GUI像素與存檔同v178後才作confirmed證據。城市角色與母港角色分開，London不因文字相同就推定為城市；普查879不增加。


v180首輪檢查錯把表格下方y142／162空白當第五、六列欄界。穩定正常GUI原始索引確認x115黑線只在y61～141，表格為四列；y142起回背景34。舊檢查保留check-before-column-review.py，改核對已驗前兩列及完整四列線界，不改來源／GUI／候選字級。


`trade-grid-prototype-v181/` 入口prepare.py／build.sh，是私有DRAFT網格候選。原版第一／二列face起點[11,69]／[10,89]、cap5／色15，首欄黑線x115、表格y61～141四列；候選右界114、22～15px，Jamestown對照實際22px。城市只問已驗colony字典，不借單位或母港片段；首列／第二列完整prefix及原VGA第一編輯器標題必須匹配。既有字模／譯稿不變。Default清冊的其他名稱可按既有規則嘗試放入同欄，但正常GUI本輪僅驗Jamestown，不將其他名稱算完成。母港London、自訂名、未驗行與錯誤位置回原文；其他writer與擴大區重疊亦拒絕。正式v175與879保持。


`trade-grid-verify-v182/` 入口prepare.py／build-observer.sh／run-sea.sh／run-land.sh／run-sea-observer.sh／run-land-observer.sh／check.py。沿v176海21／v177陸19正常輸入，私有v181、缺三圖集及唯讀字級觀測共六次重播。需原版／全部存檔與既有control全等；相對v175只新增首兩城市欄核准區，母港London與路線名原字；缺圖集原文，對話框遮擋／返回世界／存檔區不得留新中文字。尚未READY或採用879之外計數。


v182私有驗收失敗：海上改選London後第二列殘留Jamestown中文。stringFinish只在新文字有譯文時透過str.add移除舊覆蓋，未翻譯的改印只讓舊項暫停，原像素保留比例仍足以重畫。原版狀態與存檔沒有改變。失敗收據保留v182/check-failed.py；不進READY。`trade-grid-lifetime-prototype-v183/` 入口prepare.py／build.sh，將完整原版改印的移除移到翻譯判斷之前，只處理已核准網格城市項。`trade-grid-lifetime-verify-v184/` 入口prepare.py／六側重播腳本／check.py，重新驗海陸40畫面與全部原版、存檔、字級及限定像素；不覆寫v182收據。


v182私有驗收失敗：海上改選London後第二列殘留Jamestown中文。stringFinish只在新文字有譯文時透過str.add移除舊覆蓋，未翻譯的改印只讓舊項暫停，原像素保留比例仍足以重畫。原版狀態與存檔沒有改變。失敗收據保留v182/check-failed.py；不進READY。`trade-grid-lifetime-prototype-v183/` 入口prepare.py／build.sh，將完整原版改印的移除移到翻譯判斷之前，只處理已核准網格城市項。`trade-grid-lifetime-verify-v184/` 入口prepare.py／六側重播腳本／check.py，重新驗海陸40畫面與全部原版、存檔、字級及限定像素；不覆寫v182收據。


v184限定海陸40畫面、原版與存檔、缺圖集及字級驗收通過，London殘留已修正。正式接入前追加`trade-grid-field-prototype-v185/`，入口prepare.py／build.sh，把完整改印資格收緊到1.  ／2.  與對應原版墨跡起點，取消兩個英文字母門檻；數字／單字母自訂名也應移除舊中文，對話框無列號或錯誤位置不能取代城市。此為同一DRAFT生命週期邊界修正，未進正式碼。`trade-grid-field-verify-v186/` 入口prepare.py／六側重播腳本／check.py，沿同一海陸正常輸入，確認完整前綴防護不改已驗顯示／原版／存檔；數字及單字母只為合成反例，不稱正常GUI已驗。


`trade-grid-build-v187/` 入口prepare.py／build.sh／build-entry-check.sh／run-gui-sea.sh／run-gui-land.sh，依v186通過的限定READY規格接正式網格覆蓋及未翻譯改印移除。新正常GUI在`trade-grid-sea-gui-v188/`／`trade-grid-land-gui-v189/`。`trade-grid-formal-v190/` 入口prepare.py／prepare-replays.py／check.py／freeze.py，保存新GUI的完整六側原版、存檔、缺圖集與舊v175差異限定。公開限定檢查入口[tools/check_goal181_tradegrid.py](../../tools/check_goal181_tradegrid.py)，只採實際兩列預設城名。`trade-grid-census-v191/` 入口matrix-census.py／adopt-documents.py，只有所有正式gate通過才更新目前狀態；不覆寫v175～v186，879暫不增加。


v190補充字模容量入口measure-catalog.py／measure-catalog.sh／catalog-layout.json，來源為同一已驗COLONY雙語清冊與正式v187圖集，量測兩列、兩個允許底線的全部預設名候選與1000字回退。這是字模投影，不是其他城名正常GUI或原版字級證據；原版cap／欄界仍只沿v180已驗profile。測試檔catalog_layout_test.go只在私有observer中，正式程式／二進位與活動重播腳本不改。


v191初次整批矩陣與普查的外層600秒不足，保留matrix-census.py及既有輸出。續跑入口resume-timeout.py，只延長有界容器時間並將三個獨立、唯讀普查同時執行，各自輸出互不覆寫。正式原版／程式／收據與通過條件不變。


v191初輪56PASS／2FAIL的根因是新公開檢查器缺少final_step／final_memory_sha256介面欄位，普查拒絕採用；與原版GUI驗收失敗不同。矩陣與檢查器修正前輸出保留before-interface-*。補欄位由已核對的control完整終點讀取，原版與正式程式及v190清冊不改。修正後公開兩側與25破壞反例另存v191，續跑矩陣／重複／反向普查後才採用。


封裝字型入口由舊europe-fonts-v74改為已驗v187，v191/package-atlas-summary.json核對六份譯稿與固定字型指紋；舊圖集被拒絕。只修封裝接線，不建立版本、封包或Release。


v187～v191第一路線前兩列預設Jamestown限定CONFORMED。119Go與穩定入口113Go，40新正常GUI／各六側完整原版／全部存檔、逐欄字級／缺圖集／改印／刪除、公開限定檢查及25破壞拒絕／缺原版SKIP77通過；58PASS與重複／反向普查，採用1945項／881已顯示／975待驗／89不可達。採用入口v191/adopt-documents.py，最終衛生v191/hygiene-summary.json。Issue #56仍進行中，第三／四列、其他編號、網格母港、正常同名城市及自動跑商未驗；不稱全文或三平台完成。


`europe-dock-ship-gui-v192/` 為歐洲碼頭／船隻操作正常探勘，入口prepare.py／gui.sh／run-gui.sh。沿已驗COLONY03與v187正式前端，由主選單讀檔，正常開歐洲，點已見碼頭單位，關閉選項，再從實際購買清單選1000$輕帆船、確認、回世界並Save Game。所有像素／輸入／RAM／存檔只在忽略的workplace；探勘不提高881或58PASS，不改原版或正式覆蓋。須以實際畫面／原版事件確認命中，不以點擊意圖當完成。


v192已正常開出EUROPEARM碼頭標題與六個英文選項，購船1000$成功，購船後港口標題仍殘留舊No ships中文。`europe-dock-ship-verify-v193/` 入口run-zh.sh／run-control.sh／run-noatlas.sh／source/replay.sh；核對16GUI、三側完整原版／所有取樣及全部存檔，來源探針沿既有purchase-source-v80的唯讀查詢方法、使用本次真GUI輸入與完整RAM終點。殘字先作原版畫面與覆蓋事件差分，不猜補生命週期規則；尚未READY或增加完成數。


v193/observer/ 是正式v187的唯讀字級與覆蓋生命週期觀測副本，入口build-observer.sh／run-observer.sh。原版印字與碼頭選项保留逐字墨跡及色號；No ships和Loading港口標題另記當次舊覆蓋項、原像素匹配及階段。新增JSON只在workplace，不改原版或中文繪製；須完整原版／全部存檔／所有GUI與重播像素相同才作證據。


v193完整核對入口check.py／source-summary.json。首輪字級觀測未記錄No Ships In Port及未翻譯碼頭選項，因篩選詞用harbor、且選項觀測設在匹配成功之後；原觀測及二進位保留。`europe-dock-ship-observe-v194/` 入口build-observer.sh／run-observer.sh，在查譯之前記錄六列逐字墨跡／色號，並按實際No Ships In Port記舊項與原像素保留比例。沿同一v192正常輸入，不改正式顯示與原版；須與五側及16GUI相同後才採觀測結果。

v194觀測完整核對入口check.py／measurement-summary.json。`europe-dock-prototype-v195/` 為私有DRAFT候選，入口prepare.py／build.sh／replay.sh／check.py。只嘗試已觀測ARMOPTIONS第1／4／6／8／10／12列的完整六列組合，以及原版歐洲Loading標題改印時移除已過期No Ships In Port覆蓋。逐欄字級、來源與完整原版／存檔、原文回退、核准區差分和反例通過前不審READY；正式v187、881與58PASS保持。

v195首輪量測測試漏帶v194已確認的shadowWritten旗標，line-colors拒絕。保留tests-before-shadow-fixture.log，補測試輸入後相同build.sh通過121Go／go vet與抓圖同步；未改正式顯示或原版。`europe-dock-states-gui-v196/` 入口prepare.py／gui.sh／run-gui.sh，正常從03進歐洲，開碼頭列表、切換登船／裝備及傳教士選項，逐次抓圖後正常回世界並Save Game。點擊意圖不當成功證據；實際狀態、原始來源與完整原版核對前不增加完成數。

v195原型沿v192實際輸入的16取樣、完整原版及兩份存檔相同；相對v187只改碼頭六列安全區與移除購船後舊港口中文，其他14圖相同。首版檢查器把reason=superseded誤當stage，保留check-before-event-interface.py，按既有stage=expired介面修正後通過，沒有更改產品。缺圖集候選重播入口run-noatlas.sh，仍須獨立核對回原文後才審READY。

`europe-dock-source-v197/` 入口prepare.py／source/replay.sh／check.py，沿v192正常購船輸入唯讀追蹤原版0E2D:11CF組字與0D21:00C6首次讀取，補港口Loading船名角色。探針由cargo-concat-source-v142沿用，僅調至此次89～94M實際時段及175xxx訊息暫存區；原始棧框／參數仍標角色待審，不以字面相同宣稱來源。全RAM終點及存檔須與v192相同。v196碼頭其他狀態的觀測入口將於正常GUI完成後接入，不修改活動腳本或原版。

v195缺圖集完整核對入口check-noatlas.py／noatlas-summary.json。v197/check.py／source-summary.json核對固定Loading來源、固定單位Caravel來源、複製前後字串、首次原版讀取及完整原版RAM／兩份存檔；只有該次港口標題可採此角色，不泛化其他船型或新規則。

`europe-dock-states-verify-v198/` 入口prepare.py／build-observer.sh／run-control.sh／run-observer.sh／source/replay.sh／check.py。沿v196實際GUI輸入重生原文、僅附量測的v195候選及原版查詢。清單縮為四列後既有固定點擊會命中其他選項，v196檔名只表示原探勘意圖；來源及量測以實際畫面和輸出事件採用。完整狀態、全部存檔、同步GUI及測量一致前不審READY或增加完成數。

`europe-loading-prototype-v199/` 入口prepare.py／build.sh／replay.sh／check.py，為v197來源證明後的私有DRAFT標題候選。沿v195六列碼頭與舊標題移除，只為已觀測雙空白歐洲Loading:  Caravel加入既有固定船名角色模板；原版兩個空白保持原樣，只在該來源／欄位的中文模板匹配前正規化空白。字模、譯稿與正式v187保持，未泛化其他船型或普通句子。

v198正常33GUI／三側完整原版／全部存檔、11次ARMOPTIONS查詢及六種字格量測通過。`europe-dock-profiles-v200/` 入口prepare.py／build.sh／replay.sh／check.py，為六個已確認完整碼頭清單與v199港口標題的私有候選。三列拓荒者清單的line-colors源於通用強調色推斷，私有候選只在六個來源／字格／已觀測色層組合成立時採68一般／149強調／47陰影。其他組合和Move to front／取消傳教士未採用；正式v187、58PASS與881保持。

v200初次欄位測試發現守門讀取了lineRoles回傳的新accentC，三列仍拒絕；另一舊反例把已新取證Board next ship當未驗列。初次tests-before-native-accent.log保留，fix-native-accent.py只改為讀lineRoles之前保存在st的149、將舊反例改為未驗Move to front，其他對話框的lineRoles不變；相同build.sh乾淨重跑後才做同輸入重播。

v199港口標題的16取樣／完整原版／來源／兩份存檔及核准區通過，實際22px、safe[153,119,214,127]；仍私有候選。v200增加六組缺圖集整份回退測試後，prepare-replays.py建立run-purchase.sh／run-noatlas.sh與各自正常03暫存入口；正向state沿v196，購船與缺圖集沿v192。所有重播前固定同一已建候選，不在活動程序中更改來源或二進位。

v200首次缺圖集容器exit143，在77M後收到SIGTERM，無完整JSON／終點、time檔空白；原因未知，不能列PASS或產品缺陷。部分noatlas.*及暫存完整保留。resume-noatlas.py／run-noatlas-clean.sh在新的noatlas-clean正常03暫存入口，以相同映像／資源上限／二進位／輸入／原版與命令參數重跑，只改輸出名稱；不放寬原版／像素／存檔判準，未審READY。

v200/check.py --states-only核對21筆覆蓋來源逐筆綁定v198原版印字start／RAM／全文／逐列值；11次開框会因懸停與點選重印，初版每框一次假設保留check-before-print-count.py。33取樣只在已驗清單安全區改變，關框／結果／保存畫面不變。乾淨缺圖集重跑exit0，與v195回退全16圖相同；購船候選與v199全16圖相同。完整check.py通過PASS_PRIVATE_SIX_DOCK_PROFILES_AND_EUROPE_LOADING，正式完成數不增加。freeze-ready.py／ready-evidence.json固定來源、字模、布局與收據，審查後規格035／038只對這六種組合及固定輕帆船標題升READY；正式實作與新GUI／公開檢查／矩陣尚待完成。

`europe-dock-formal-build-v201/` 入口prepare.py／build.sh，依v200限定READY接入tools/dialog_overlay.go、tools/string_overlay.go及tools/live_menu.go；適配器雜湊同步tools/build_window_prototype.py。先核對正式來源與v187逐位元組相同才更新，變更前副本保留before-source/；字模／譯稿不改。正式建置123Go／go vet與新正常GUI、限定公開檢查及矩陣／普查前不升CONFORMED，目前採用計數881／58PASS保持。

`europe-purchase-formal-gui-v202/` 與`europe-dock-formal-gui-v203/` 入口各自prepare.py／gui.sh／run-gui.sh，由正式v201正常讀03開始。v202沿既有購船正常操作，驗新22px港口標題；v203用v198實測的六／四／三列位置，正常切換登船、配備槍、士兵取消自動登船、賣槍、配備／賣工具、配備馬、開騎馬單位清單並Escape關閉，最後Save Game。三列賣工具選第二列的424，四列賣槍選第二列400，不沿用v196探勘意圖錯位。原版命中及完成信用仍以新GUI／事件核對，不以腳本名稱作證。

`europe-dock-formal-verify-v204/` 入口prepare.py／build-observer.sh／run-<分支>-<側>.sh／<分支>-source/replay.sh及check.py，沿v202／v203實際正常GUI輸入重生中文、原文、缺圖集、v187基準與唯讀字格觀測。完整原版、所有存檔、同步GUI、來源與核准區差分通過前不升CONFORMED；v202另重生固定Loading／Caravel組字來源，六種碼頭清單維持完整組合守門。

正式限定檢查入口[tools/check_goal181_dock.py](../../tools/check_goal181_dock.py)，核對v204凍結清冊、原版版本、所有側的完整狀態／存檔、45張正常GUI、原版來源與六種完整清單及一個固定船名標題；不將未命中的列、其他船型或傳教士取消算作完成。v204/freeze.py保存已核對產物指紋，negative-checks.py以私有副本破壞收據並驗缺原版SKIP77；通過後才能接矩陣與普查。

`europe-dock-census-v205/` 入口matrix-census.py／adopt-documents.py／hygiene.py，接入v204通過的限定碼頭及購船欄位，再跑全矩陣與重複／反向普查。原版段落完成數沿普查的段落單位，只有檢查器給出的來源鍵與正常可見欄位採用；不能據此聲稱ARMOPTIONS全部12列、歐洲全畫面或Issue #56完成。

`europe-missionary-probe-gui-v206/` 入口prepare.py／gui.sh／run-gui.sh，正常由03進歐洲，選已驗六列的祝福成為傳教士，再重新開碼頭清單觀測實際變化，Escape關閉並Save Game。未量測的新清單保持原文；此入口只蒐證，不算新增完成，也不預定取消傳教士的位置。

`europe-missionary-source-v207/` 入口prepare.py／run-control.sh／run-observer.sh／source/replay.sh／check.py，沿v206實際輸入核對15GUI、三側完整原版與存檔及ARMOPTIONS原版查詢／三列字格。沿已驗v204唯讀觀測二進位，不改正式顯示；取消身分的實際操作與新中文覆蓋仍待驗。

v207/source-summary.json通過PASS_NORMAL_MISSIONARY_SOURCE_AND_FIELD。新三列原版起點為x82、y91／103／115，cap8／行距12／68、149、47色層；取消身分列右界203。`europe-missionary-cancel-gui-v208/` 入口prepare.py／gui.sh／run-gui.sh，依此正常祝福、選第一列取消自動登船、重新開框觀測Board變體，再選第二列取消傳教士並重開檢查復原。新中文尚未READY；原版實際狀態與來源核對前不採用操作結果。

`europe-missionary-cancel-source-v209/` 入口prepare.py／run-replays.sh／source/replay.sh／check.py，沿v208實際19GUI核對三側完整原版／存檔、四次ARMOPTIONS查詢及兩種傳教士三列和正常取消後六列。仍沿正式v201與v204唯讀觀測，不接新中文；字級與整份回退將另由私有候選量測。

v209/source-summary.json通過PASS_NORMAL_MISSIONARY_CANCEL_AND_TWO_FIELDS。`europe-missionary-prototype-v210/` 入口prepare.py／build.sh，僅增加已證實的ARMOPTIONS第1／11／12與第2／11／12列兩組，逐欄30～20px與缺字模／超界／錯誤字格量測；不改正式v201、譯稿或字模。`europe-missionary-prototype-verify-v211/` 入口prepare.py／run-replays.sh／check.py，沿v208實際輸入核對私有中文與缺圖集、原版／存檔／安全區與關框復原，通過前不審READY。

`europe-missionary-formal-build-v212/` 入口prepare.py／build.sh／build-entry-check.sh，v211/freeze-ready.py固定完整私有證據後，依規格035限定READY只增加兩個來源組合；字模、譯稿、字串與適配器保持。`europe-missionary-formal-gui-v213/` 入口prepare.py／gui.sh／run-gui.sh，從正式v212重新正常祝福、切登船、取消身分、重開及Save Game。完成驗收前仍採v201～v205的882項／60PASS。

`europe-missionary-formal-verify-v214/` 入口prepare.py／build-observer.sh／run-<側>.sh／source/replay.sh／freeze.py／negative-checks.py，沿v213新實際GUI重生中文、原文、缺圖集、v201基準與唯讀觀測；限定檢查由tools/check_goal181_dock.py的missionary側執行。核對兩個新安全區與正常取消後復原，通過前不升CONFORMED。`europe-missionary-census-v215/` 入口matrix-census.py／adopt-documents.py／hygiene.py，只有獨立正例／破壞拒絕／缺原版與全矩陣／重複／反向普查通過才採用；ARMOPTIONS已shown，不預定增加882計數。

`europe-dock-recruit-probe-v216/` 入口prepare.py／gui.sh／run-gui.sh，正常從03進歐洲招募畫面，依v71已觀測的自由移民列選擇，抓取招募結果後正常關閉前端。用途是確認第二個碼頭單位與下一步位置；不預定招募成功、移到碼頭最前面的選項或新中文，不增加完成信用。

v216實際招募自由移民後，畫面金錢由1000$變864$，碼頭出現第二單位；點擊意圖與畫面均保留，完整原版比對尚待下一入口。`europe-dock-rear-options-gui-v217/` 入口prepare.py／gui.sh／run-gui.sh，沿相同正常招募操作後，按v216實際第二單位位置開清單、Escape關閉並Save Game。`europe-dock-rear-options-source-v218/` 入口prepare.py／run-replays.sh／source/replay.sh／check.py，沿v217實際輸入，以既有v214唯讀觀測重生原版查詢與逐字墨跡／完整原版及存檔。新清單保持原文，未取得字級與正常結果證據前不升READY。

`europe-dock-front-action-gui-v219/` 入口prepare.py／gui.sh／run-gui.sh，依v218確認的七列y67起、行距12，正常選第二列Move to front；重新開第一與第二單位清單、Escape關閉並Save Game。`europe-dock-front-action-source-v220/` 入口prepare.py／run-<側>.sh／source/replay.sh／check.py，以v219實際輸入核對原版來源與結果，仍不接新中文或增加完成信用。

`europe-dock-seven-prototype-v221/` 入口prepare.py／build.sh，為v218／v220確認的七列來源及字格建立私有候選，只增加完整[0,2,3,5,7,9,11]組合與y67起點，測30～20px／超界／缺圖集／錯字格。`europe-dock-seven-prototype-verify-v222/` 入口prepare.py／run-<側>.sh／check.py，沿v219正常移到最前面的實際輸入核對完整原版／存檔、19取樣及安全區／回退。通過前不審READY，正式v212及882項／61PASS保持。

`europe-dock-seven-formal-build-v223/` 入口prepare.py／build.sh／build-entry-check.sh，只有v222/freeze-ready.py限定READY後，才接入七列來源及字格。`europe-dock-seven-formal-gui-v224/` 入口prepare.py／gui.sh／run-gui.sh，正式前端新正常招募、移到最前面、重開兩清單及Save Game。`europe-dock-seven-formal-verify-v225/` 入口prepare.py／build-observer.sh／run-<側>.sh／source/replay.sh／freeze.py／negative-checks.py，沿v224實際輸入驗新正常GUI與六側原版／存檔／來源／字級／核准區，公開檢查由tools/check_goal181_dock.py的front側執行。`europe-dock-seven-census-v226/` 入口matrix-census.py／adopt-documents.py／hygiene.py，獨立正例、破壞拒絕與缺原版通過後才接矩陣及重複／反向普查；不預定增加882計數。


v201～v205限定CONFORMED：碼頭六組30px與固定輕帆船港口裝載標題22px。45新正常GUI、各六側完整原版／所有存檔、字級與來源／缺圖集／核准區、31破壞拒絕與缺原版SKIP77、60PASS與重複／反向普查通過。採用1945項／882已顯示／974待驗／89不可達，程式5fb225cd4baae4dce17e7f37cdc3cbc42f379cd0e86537d059cce6984955bbd3，清冊9a17519fd79e2df51263ea271c5276d229a49e74791ba4f37d1a4e22eae0a051。取消傳教士、Move to front、其他船型與Issue #56其餘仍未完成；v206只探勘。採用入口v205/adopt-documents.py，衛生入口v205/hygiene.py。


v206～v215兩組傳教士三列與正常取消後復原限定CONFORMED。19新正常GUI、各六側完整原版／所有存檔、逐欄30px／來源／缺圖集／安全區、29破壞拒絕與缺原版SKIP77、61PASS及重複／反向普查通過。採用1945項／882已顯示／974待驗／89不可達，新增段落完成信用0；正式程式0a1bf028ea6ea0a57050cae438576565b94ec95fb4c88113457b5c771e112a5e，清冊f78d6fd6c608e89aba8101a5f7cb17dd0eaddaca536956d668ca64d030efd4b3。Move to front、港口單位標題與Issue #56其餘仍待驗。採用入口v215/adopt-documents.py，衛生入口v215/hygiene.py；歷史v201～v205不重開。


v216～v226碼頭七列與正常移到最前面限定CONFORMED。19新正常GUI、六側完整原版／全部取樣／新舊存檔、逐欄30px／來源／核准區／回退、29破壞拒絕與缺原版SKIP77、62PASS及重複／反向普查通過。採用1945項／882已顯示／974待驗／89不可達不變，完成信用0；正式程式e84d4c157a190ae04c5a1c3f291e105abaff8b336006f0de29423ed37e31558c，清冊4b65c62b9c8c1840d79ae197605590d13e485dcdba01270717e9aa2536e3b5df。Board七列與港口單位標題等未驗，Issue #56未完成。採用入口v226/adopt-documents.py，衛生入口v226/hygiene.py；歷史碼頭與傳教士驗收保留。


## 2026-10-04 港口欄位整批接線

工作入口`workplace/reports/goal181-colony-rest/20261004-port-fields/`。
`prepare.py`／`build-observer.sh`／`run-observer.sh`先沿既有正常GUI實際輸入，
只觀測港口單位標題、買賣價格與說明提示的原版字串、墨跡、字高及色號。
`raw-fields.jsonl`保存本機來源與字級證據；新覆蓋仍待規格038限定READY，
不以文字命中或單元測試冒稱已顯示。後續正式建置、字模與抽樣收據沿同一入口，
依使用者已確認的整批接線、最後抽樣順序，不新增逐詞條多側驗收輪次。


本批已依規格038的2026-10-04 READY接入三類欄位，十點抽樣限定CONFORMED。
`ready-evidence.json`保存來源與候選審查，指紋46494b4eb9dd73707405e1a7babea518f1b48eec1ceb8d954673f6ec73506c6f；
`adopt.py`記錄正式組裝來源，`formal/build.sh`／`formal/build-entry-check.sh`建置正式與穩定入口。
現行二進位為`formal/colonization-window`，指紋f45271c2d644e6347e183298046aa15e8e2140a7af813843f244f399d861c028；
現行字串圖集`font/string-atlas.json`指紋f824c6c74de5aae77a64623861e799d8f30c2ad129adedd01958179449777a3b。
字模重生使用固定rich2-py映像的`tools/bake_string_atlas.py`，本批模板為現行text/string-templates.zh-Hant.tsv。
`candidate/port_fields_test.go`與`candidate/port-layout.json`保留原版三欄量測和112組容量投影，正式量測在`formal/port-layout.json`。
`sample/prepare.py`／`sample/run-zh.sh`／`sample/run-control.sh`／`sample/run-missing.sh`／`sample/check.py`為十點抽樣入口；
`sample/summary.json`指紋6522cc69da3adb38e229bde724fa9aa72305d99378c7abf17be3be3626cffcf0，新畫面差異只在頂列與價格安全區。
`text-validation.json`重新核對3561行與66個模板，零缺譯與缺字；
`record.py`保存本批文件採用方式，`hygiene.json`保存收尾擁有權／容器／原版版控檢查。
全部原版像素、RAM、存檔、原始資料與候選字模只留忽略的workplace。
重播使用v224實際正常輸入，未重新錄GUI，未重算62項矩陣與畫面普查；其他值、F1提示與報表版式保留待驗。

`hygiene.py`重跑擁有權、版控、私有證據忽略與dosgolem清潔檢查；Docker殘留另以主機docker ps -a核對。
