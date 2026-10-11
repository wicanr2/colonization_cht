# 顯示設定列正式接線與保存

狀態：限定CONFORMED於設定列、保存及既有繁中／英文後端。前端資料與交易契約沿規格050的既有選項與操作。
不授權尚未驗證的語言包或HD圖層。入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)。

## 已有證據

[規格050](050-display-settings.md)已確認畫面外設定列、開啟暫停及全部放開後恢復。
[規格051](051-display-settings-runtime-prototype.md)保存隔離原型的原版同狀態與GUI收據。
工具列沿已展示的48px起點，遊戲區仍1280×800；不占用原版快捷鍵與命中範圍。
原版觀測資料、翻譯快取、顯示選擇分開；英文以當次原版畫面重合成，不改DOS。

## 輸入與後端交易

沿規格050四態狀態機。原版拖曳經過工具列時保留已送入DOS的按住狀態，
直到實體放開；不開設定、不送額外座標。失焦或離開整個視窗沿原有放開契約。
設定已開啟時失焦，原版仍暫停；回焦且實體輸入全部放開後才進入下一狀態。

後端先準備完整顯示資料，回傳不會失敗的提交函式。準備失敗不保存、不換畫布。
準備成功後先原子保存，再於同一Update邊界提交並從目前原版畫面重合成。
保存失敗則不呼叫提交函式，不改生效設定或畫布，面板顯示TSV的保存失敗訊息。
取消與Escape不保存。沒有重啟原版、假按鍵、RAM回填或強制原版重畫。

## 保存契約

使用[現有選項結構](../../tools/display_settings.go)的兩個JSON欄位，UTF-8編碼。
欄位必須恰為language與graphics，值沿既有五語與original／hd列舉；不增加原版資料格式。
拒絕重複／未知／缺欄、非字串、損毀UTF-8、超過4096bytes及尾隨資料。

預設路徑是Go標準庫os.UserConfigDir()下的colonization-cht/display.json：
Linux使用XDG_CONFIG_HOME或家目錄的.config，Windows使用AppData，
macOS使用Library/Application Support。獨立於原版與COLONY存檔。
測試與可攜環境可用明確的--display-config指定JSON路徑。
未保存過時預設zh-Hant／original；明確--display-language或--display-graphics只覆蓋相應欄。
已存在但無法讀取或損毀的設定，啟動時明確報錯，不偷偷改用另一組設定。
啟動載入本身不寫檔；選項是否可用仍由完整後端驗證。

保存以同目錄0600暫存檔完整寫入、同步及關閉，再rename；失敗清理暫存檔，
保留原設定檔。只保證避免部分檔案，不宣稱斷電後的檔案系統耐久性。

## 驗收與完成邊界

- 真實檔案往返、明確參數優先、取消無寫入、格式反例、保存失敗保留與後端準備失敗保留。
- 原版世界與殖民地正常GUI：拖曳經工具列，開啟／編輯／恢復時失焦，等待輸入放開。
- 設定動作前後CPU、完整RAM、VGA、DAC與DOS輸入數不變，音訊沿規格050暫停。
- 真視窗內容與當次合成相同；正常關窗、重開後讀回保存選項，原版存檔不變。
- 同一實際輸入由正式前端與原文控制重播，核對原版完整狀態、WAV及存檔。

目前只有既有繁中及英文後端可準備。其他語言或HD缺完整資料時仍須拒絕，
不能以五個可選按鈕或已保存的選項宣稱完整五語／HD完成。

## 2026-10-11正式接線驗收

實作入口為[設定介面](../../tools/display_ui.go)、[偏好設定](../../tools/display_preferences.go)
及[視窗](../../tools/window_prototype.go)。使用--display-settings啟用畫面外設定列，
並以--display-ui-catalog指定text/frontend-ui.tsv、--display-ui-font指定
[固定Noto字型](../../font/README.md)。--display-diagnostics只供驗收，預設不輸出設定事件圖像。
目前發布包保持原版入口，尚未收進這組參數或完整五語包。

- Go1.26.7／Ebitengine2.9.9固定映像完成353項測試，零skip，go vet無輸出。
  含真實18筆五語介面與固定TTC排版、JSON反例、真檔案往返、明確參數覆蓋、
  保存失敗及後端準備失敗不提交。五語介面新增保存失敗訊息後均無缺字。
- 真實X11操作八組通過。世界與殖民地的拖曳、失焦、等待放開、取消、
  語言／HD缺包拒絕與繁中／英文切換不推進DOS。以不可寫設定目錄測試保存失敗，
  仍維持英文與原設定檔；恢復寫入後正常切回繁中。
- 兩次新行程各經正常開場至選單。第一次讀回繁中並從設定列保存英文，
  第二次讀回英文且維持原版像素字體，取消不寫回。原版存檔全程不變。
- 主GUI的24筆實際DOS輸入與23筆設定事件，重播至77000000步。
  本輪正式前端、前版前端及原文控制的CPU、完整RAM、VGA、DAC、時鐘、
  存檔及WAV全同；兩個繁中終點PNG與真GUI全同。

本機收據均在workplace/reports/goal186-display-hd/，不加入Git：

| 收據 | SHA-256 |
|---|---|
| runtime-ui-formal-20261011-r2/colonization-window | 6f747fa6cdfd0d380d03c3ec699eb1e633f5beb5901cd8608ae83d21b560ce8d |
| runtime-ui-formal-20261011-r2/tests.json | c51491f489e3055e277cbb23298fb3b96ee447010113f5c05b978e3bbe26773b |
| runtime-ui-formal-20261011-r2/prototype-sources.json | 4773e3bfc9755a3e2dbfff19b66e1ee6441bd00f02ceb145bd9c3d935667dbf1 |
| runtime-ui-formal-gui-20261011/check.json | 818cb101d4dbf6899b4e52875e25dad0245532f853d690059862c9ec180c6909 |
| runtime-ui-formal-replays-20261011/check.json | ed206fe3e85eb827c7f8d9a5921db0b629cecc7c4c62452ace0db26dda3d53e4 |
| runtime-ui-formal-glyphs-20261011/coverage.json | ec1f8c233ca77a8984d23cab39f46ecd72f1dea225f566d39784d1e401a17ca7 |

重跑沿[正式組裝器](../../tools/build_window_prototype.py)，舊名
[設定列組裝入口](../../tools/build_display_settings_runtime_prototype.py)現只核對正式來源並複製，
不再修補Go程式。於固定Go容器以--reference指定
workplace/reports/goal186-display-hd/retained-ascii-build-20261011-r4，--output指定新目錄，
依前述字型、原版與既有字模清冊設定測試環境後執行go test -json、go vet、go build。
[真GUI探針](../../tools/probe_display_settings_gui.py)的--binary指定新程式，
--launcher指定goal185-player-experience/issue56-formal-gui/launch.sh，
--seed指定runtime-ui-gui-20261011-r2/save/COLONY09.SAV，
--inputs指定goal185-player-experience/issue56-wagon-sample-gui/gui.inputs.json，
--ui-font及--ui-catalog指定上述TTC與TSV，--game指定唯讀原版目錄。
launcher與inputs的路徑均相對workplace/reports/，seed相對本節的goal186根目錄。
最後以[三側檢查器](../../tools/check_display_settings_replay.py)的--gui指定新GUI目錄，
--prototype指定本輪程式、--formal指定noto-menu-formal-build-20261011/colonization-window，
其餘同前。各--output必為新workplace目錄，GUI與重播需有界Xvfb。
工具中prototype為沿用的參數名稱，不代表本輪仍以原型補丁接線。

重播WAV相等不等於人耳或牆鐘同步確認，macOS真機亦未驗。
六列ORDERS與主選單五列的Noto旗標仍獨立；完整語言資料與HD後端另驗。
