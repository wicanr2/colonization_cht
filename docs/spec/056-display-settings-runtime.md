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

## R151：上方選項與六段速度（限定CONFORMED）

2026-10-22使用者明確要求上方工具列提供HD Theme、多語系及1x、2x、4x、8x、16x、32x，HD輸出至少30fps。本節擴充既有前端契約，不新增原版攔截點或修改原版資料。

- 已證實：現行正式前端已有48px工具列、五語及original／hd後端。`window_prototype.go`在同一Update同步執行200000道指令，`publishStatus`每次雜湊畫布並寫檔；`live_menu.go`的OnFrame同步呼叫HD合成。這些工作會占住視窗更新。
- 工具列保留既有顯示設定入口，另提供語言、圖像主題及速度入口，顯示目前選項。共用既有暫停面板及準備／保存／提交交易。設定點擊、按鍵與恢復放開均不轉送DOS，拖曳契約保持。
- 速度只控制每秒期望執行的指令預算。1x沿現行60次Update乘200000道指令，即每秒12000000道；其餘為該預算的倍數，實際速度受設備能力限制。不得變更IRQ、PIT、DOS時鐘、步數語意、遊戲規則或存檔。既有獨立音樂維持原速。
- 前端偏好JSON新增可選整數`speed`，只接受1、2、4、8、16、32。舊有兩欄檔案視為1x，不重寫。程式內零值代表舊設定的1x；明確JSON零值、非整數、重複或未知欄位仍拒絕。新增`--display-speed`只覆蓋速度，明確參數不掩蓋損毀檔案。
- 正常遊玩以單一背景擁有者依序推進DOS與合成。每批指令有數量與牆鐘上限；原版觀測照常執行，主視窗只接收已完成且不再修改的畫布。畫面合成、設定準備及原版輸入不並行存取機器。視窗輸入先排隊，批次完成後依序處理，禁止遺失按下／放開或使用中的畫布。
- 合成可依牆鐘省略尚未到期的無標籤顯示，但每個原版畫面的來源觀測仍執行。標記檢查點、設定套用與最後畫面不省略；驗收重播維持既有同步路徑與固定音訊取樣邊界。
- 即時狀態寫檔限頻，設定事件及結束狀態立即保存。分別記錄視窗Draw輸出、畫布更新及實際指令速率，不以編碼30fps或重複靜止畫面冒稱動畫有30個不同影格。
- 驗收以正式HD資源的實際視窗量測為準：記錄設備、容器CPU限制、暖機區間、Draw頻率與最長間隔。至少30fps的聲明限於實測設備與場景；開檔載入不計入穩態。另驗六段速度、五語／主題切換、舊偏好相容、取消與保存失敗、原版輸入隔離及正常關窗。

正式入口仍為[設定介面](../../tools/display_ui.go)、[偏好設定](../../tools/display_preferences.go)與[視窗](../../tools/window_prototype.go)。本節只授權前端調度與選項，不新增翻譯或HD素材，也不外推全遊戲與三平台的幀率。

重跑入口為[工具列與幀率探針](../../tools/probe_toolbar_performance.py)。在固定前端Docker映像內，以`--repo`指定儲存庫、`--bundle`指定既有正式資源包、`--binary`指定本輪程式、`--game`指定唯讀原版目錄、`--output`指定新的workplace輸出；`--sample-seconds`預設12秒。探針建立隔離偏好及空存檔，正常啟動HD視窗、實際點擊六段速度／五語／兩個主題、檢查暫停及取消、正常關窗，保存Draw量測、畫面與輸入收據。軟體OpenGL與靜音條件如實記錄，不冒稱GPU或音訊效能測試。

軟體繪圖使用`LP_NUM_THREADS=1`，避免半核心配額下依主機全部核心數建立繪圖執行緒。此參數只限制LLVMpipe執行緒，不關閉光柵化或降低畫質，依[Mesa環境變數文件](https://docs.mesa3d.org/envvars.html#lp-num-threads)。首次未限制執行緒的6.448fps收據保留為未達標；當時尚未出現可見遊戲內容，不能當成HD畫面通過。後續量測先等待原版正常啟動出現可見畫面，再計時。

R151前端節奏補充READY：正式視窗以`ebiten.SetVsyncEnabled(false)`及可休眠的60Hz牆鐘節流限制輸出上限，禁止無限重畫忙迴圈；TPS明確維持60。DOS每批牆鐘上限隨請求速度由8ms增至最多32ms，讓加速可使用額外執行時間，輸入仍於批次邊界處理。這些節奏只影響前端排程，固定重播、DOS時鐘與HD像素不變。

硬體測試r151-toolbar-r5已見正式HD畫面，1x47.149fps，32x19.059fps，故高倍速仍未達標。補充READY：每批實際上限初值8ms，速度切換時回到不超過8ms；每秒依真實Draw輸出調整。低於40fps時縮為四分之三，達50fps且有餘裕時增加1ms；限制在1ms與該速度8至32ms上限內，暫停時不調整。30fps為目標，40fps門檻提供餘裕；硬體本身不足仍如實回報，不能保證任意裝置。請求的1x至32x與保存值不變，實際加速受可用效能限制。這是前端排程回饋，不修改原版CPU、IRQ、PIT或遊戲計算。

效能勘誤：Go CPU取樣15.77秒僅1.51秒，不代表整個行程閒置。原生Mesa執行緒不在該取樣的完整計數內；cgroup實耗49.06%已用滿50%配額，另見llvmpipe-0執行緒。R151 r3堆疊停在OpenGL DrawElements，移除垂直同步後仍約3至6fps，故撤回「垂直同步是主因」推論，不將60Hz限頻當作已證實的軟體繪圖修法。該次SIGQUIT由代理對隔離測試行程主動送出以保存堆疊，並非產品自行崩潰。

本機已確認`/dev/dri/renderD128`為i915，現成`superfighter-local-capture:noble-egl-20261021-r2`含VirtualGL。以UID1000、附加群組992及該render裝置，`vglrun -d egl0 glxinfo -B`回報Intel／Mesa Intel Graphics (MTL)／OpenGL4.6／Mesa25.2.8。硬體驗收使用探針`--renderer vgl-egl`，原版與儲存庫唯讀、只有workplace輸出可寫；半核心與8GiB上限保持。探針核對正式前端行程的render檔案描述符，採無壓縮X11 proxy、停用frame spoiling，避免將僅有glxinfo或被丟棄的影格計成正式前端GPU輸出。30fps仍須以當次實際HD畫面及1x／32x收據判定。

### R151當次驗收與限制

正式Linux程式4e2c4a05acacb42ceccdf40908a7582bacc1c45e951a04e41317ba4fa1a80c69，來源r151-formal-runtime-r5與r151-source-r5.json。Go1.26.7／Ebitengine2.9.9完成41項相關測試，零失敗零skip；新增執行時間回饋測試驗證低幀率會讓出CPU、有餘裕才增加、不超過所選上限。

在本機Intel MTL GPU、VirtualGL EGL、半核心配額、8GiB、GOMAXPROCS=1、播放裝置靜音的實際1280×848視窗，以正常GUI收據的第一個Enter跳過片頭，未直接進入或修改RAM。原版正常走到可見且當次HD繪製計數為正的畫面後，1x輸出48.451fps，每秒樣本46.456至50.820；32x輸出50.567fps，每秒樣本45.929至56.022。Source canvas更新及指令速率另記，不冒稱動畫每秒有30張不同原版影格。前端行程實際開啟renderD128，無壓縮X11傳輸且停用frame spoiling。

六段速度、五語、兩類圖像、取消與保存共14組操作通過；設定時步數不變，工具列輸入未穿透DOS，正常關窗為0且沒有產生遊戲存檔。收據在既有R84根的r151-toolbar-r6/receipt.json、benchmark.json與gpu-runtime.json，README沿原有32張只替換設定畫面，來源清冊同步。此CONFORMED限於前端控制與上述HD輸出場景；軟體OpenGL、未抽樣場景、音訊裝置及Windows／macOS真機不包含在本次30fps聲明。舊版全HD診斷匯出中止的限制保持。
