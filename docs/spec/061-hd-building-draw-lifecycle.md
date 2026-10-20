# 首座 HD 建築的來源與繪製生命週期

狀態：限定CONFORMED。僅涵蓋下列單座建築、固定位置及本次正式正常路徑。
入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)，工作項目為
[Issue #63](https://github.com/wicanr2/colonization_cht/issues/63)。
本專案只覆蓋顯示，不修改原版 RAM、遊戲規則、資料或存檔。

## 輸入與定位

| 輸入 | SHA-256 |
| --- | --- |
| VICEROY.EXE | a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3 |
| BUILDING.SS | e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4 |
| 正常 GUI 輸入 | 9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979 |
| 初始 COLONY09.SAV | 52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b |
| 第032幀完整534bytes編碼 | 7c34170632e995ebfb281e451f340d14faec5fa25970ca0479493d99758afb2a |

原始編碼位於 BUILDING.SS 解壓 part3 的位移22616，該完整片段唯一。
原始輸入與像素只留本機。工具版本為 Go1.26.7、隔離 dosgolem
82a14b266e1b5bc904e2d0fe507daf6bea41a013、IDA9.4與Python3.12.3。
IDA 使用已驗證的 ida-pro-9.4-idapython:py312-v1，映像ID為
4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab。

位址空間分開記錄：

- 原版執行位置是 dosgolem real-mode CS:IP，RAM是20bit線性位址。
- IDA位置是從唯讀原版新建MZ資料庫的線性EA，不能直接當執行位置。
- 已證實16bytes寫入碼唯一對應原版0D46:01D2與IDA EA0x1C532。
  自動導覽名sub_1C36A及範圍EA0x1C36A至0x1C563保留原樣，不作語意證據。

## 已證實的三次未裁切呼叫

confirmed僅限本次正常玩家路徑。原版入口0D46:000A，返回121D:1554。
首次67569117至67579078步，後兩次見下節。原始ENTER、保存暫存器、
讀取指令及retf 6與實際數值共同支持以下對應：

| 原始定位 | 本次值與用途 | IDA讀取證據 |
| --- | --- | --- |
| 入口DX，保存於[BP-2Ah] | x=56 | EA0x1C3E7及後續水平裁切／目的位移 |
| 入口SS:SP+4，進入後[BP+6] | y=13 | EA0x1C433及後續垂直裁切／列位移 |
| 入口DS:BX，保存於[BP-2Ch] | 1C6A:2DA8，目的畫布描述 | EA0x1C3BE至0x1C3D0 |
| DS:BX+0、+2 | 高200、寬及列步長320 | EA0x1C373、0x1C37A、0x1C3CD、0x1C53E |
| DS:BX+4、+6 | 目的遠指標2CAE:0000，線性0x2CAE0 | EA0x1C3C1、0x1C3C4、0x1C45E |
| 入口AX，保存於[BP-2Eh] | 33，本素材對應解碼第032幀 | EA0x1C383至0x1C3A8 |
| 入口SS:SP+6、+8 | 圖像記錄表遠指標4F22:A6C4 | EA0x1C3A2、0x1C3A5 |
| 記錄表+((AX & 7FFFh)×12)+36h | 4F22:A886 | 同上原始乘法與加法指令 |
| 記錄+0、+2 | 來源遠指標5F3B:000E，完整534bytes一致 | EA0x1C3B1、0x1C3B4、0x1C480 |
| 記錄+8、+Ah | 圖像寬23、高27 | EA0x1C3D3、0x1C3DA及目的像素差分 |
| retf 6 | 首次SP59358至59368，增10 | EA0x1C560及實際返回 |

矩形為[56,13,79,40)，440個不透明像素各寫一次，透明索引253與矩形外底圖不變。
本次來源指紋才是素材身分，不能把AX與幀號的關係外推到其他SS。
AX高位的翻轉語意仍屬強推論；負座標、裁切、其他畫布及其他素材未驗。
記錄+4、+6的228與149不賦予用途。

## 後續寫入與重畫

confirmed：首次返回至75900000步，同矩形有2122筆寫入，涵蓋全部621點。
其中366筆寫入前後同值。按時間與舊值逐筆重播，可完整重建原版終點矩形；
終點矩形等於首次繪製結果，不能用這項終點相等否定中間重畫。

| 原版寫入CS:IP | 次數 |
| --- | --- |
| 0CBA:00CA | 1242 |
| 0D46:01D2 | 772 |
| 0D46:01B4 | 108 |

| 同來源同位置重畫 | 返回 | 驗證 |
| --- | --- | --- |
| 67867911步 | 67877872步 | 完整來源、座標及畫布一致，440點各一次 |
| 72099553步 | 72109500步 | 完整來源、座標及畫布一致，440點各一次 |

兩次進入前的621點等於首次建築前底圖，返回後等於首次建築後畫面。
這份早期收據足以支持本切片的底圖保存與重畫原型；後續正常GUI證據見下節。
後兩次返回位置的16bytes碼各有一byte不同；完整碼在新IDA資料庫沒有匹配。
差異成因未知。來源、幾何及逐點畫布證據不依賴猜測該呼叫者的用途。

## 正常GUI生命週期與游標

2026-10-12新增原版正常GUI收據。正式前端329d56d6…使用實際X11輸入，
沒有注入遊戲狀態。55組檢查含原有十場景五語及新增五張英文原版畫面；
53筆實際DOS輸入至134600000步。49個不同檢查點及終點的CPU暫存器、
完整RAM、VGA索引與DAC均與觀測、無觀測重播一致，兩個原版存檔相同。
本輪未比較WAV，不增加音訊對拍信用。

confirmed限此正常路徑：首次建築68901370至68911317步，後續九次同來源重畫
各寫440點；首次返回後19463筆矩形寫入含5986筆同值，逐筆可重建全部GUI檢查點。
正常改名、取消、存檔、離城與重進均已觀察。
懸停顯示Fur Trader's House浮標；右鍵沒有開啟建築對話框。
第一次Escape離城，第二次開啟Exit to DOS確認框。
保留原始場景標籤，不能將hd-building-context誤稱建築視窗。

游標的已證實範圍如下，位址空間分開記錄：

| 原始定位 | 證據與本次語意 |
| --- | --- |
| 原版0B68:0547 | 寫入16bytes碼26880547e2f007c3c800000006c44606，唯一匹配IDA EA0x1AAC7。 |
| IDA sub_1AAAD，EA0x1AAAD至0x1AACF | 保留原始名稱，僅作導覽；EA0x1AAB4設定SI=06D4h，EA0x1AAB7設定DI=FB00h，EA0x1AABA設定CX=256。 |
| IDA EA0x1AABD／0x1AABE／0x1AAC0／0x1AAC2／0x1AAC7 | lodsb、cmp al,0FFh、jnz、讀es:[di-100h]、寫es:[di]。FF分支取背景，其餘取來源色。 |
| 原版RAM 1C6A:06D4，線性0x1CD74 | 完整256bytes指紋47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03，174個FF、82個不透明點。 |
| 原版A000:FA00及A000:FB00 | 本次49個檢查點分別與16×16游標區的底圖及合成結果逐點相同；114次256點寫入共29184筆，來源全同。 |
| 原版0B68:051C | 建築矩形內2100筆寫入形成五組暫繪／還原配對；每組兩側各210點，地址一致、舊新值互逆，區間內沒有其他矩形寫入，檢查點均在配對完成後。 |

畫面差分只有78至82點，與背景同色時仍有82個游標不透明點。
不能用indexed與canvas的差分取代來源透明遮罩。
也不能因本次五組配對可還原，就全域忽略0B68:051C或同值寫入。
未完成配對、來源不同、其他寫入交錯及未知游標維持原版回退。

私有離線原型逐點撤除其他寫入的HD擁有權，只對上述已完整驗證的配對保留底層。
浮標遮擋161點後保留其餘460點；游標82點放在最上層，修正先前整個游標矩形露出原圖的缺口。
重進恢復621點；存檔頁、離城與退出確認框沒有HD殘留。
這是原版GUI收據加離線合成，尚非HD執行期或切換驗收。

v4候選以原版完整不透明點提取圖及已定稿畫風為參考，由內建imagegen生成，
原樣保存在本機building-032-candidate-v4.png，SHA-256為
c33885bd2570cc5ec0eb204aece69f1363b66fab5c1f16da82786f3b7e5139d8。
原始尺寸1158×1359，92×108原型按最近鄰取樣；本輪alpha>0量測為
5853點覆蓋、1187點未覆蓋、331點外溢，與早期alpha≥128收據的門檻不同。
完整提示、來源指紋與本輪量測保存在本機JSON；v3與v4均未定為正式素材。
數字不是美術通過門檻，含原版像素的參考與對照不入Git。

## 隔離原型要求

執行期蒐證入口為[可丟棄HD原型](../../tools/hd_runtime_prototype.go)及
[隔離組裝器](../../tools/build_hd_runtime_prototype.py)。兩者不由正式建置引用。
原版重播檢查為[生命週期測試](../../tools/hd_runtime_prototype_test.go)，
須提供合法原版與本機53筆實際GUI輸入；原版重播不取代HD正常GUI驗收。
真視窗入口由[HD視窗探針組裝器](../../tools/build_hd_runtime_gui_probe.py)從固定版
五語探針建立，追加原版／HD切換、重進、浮標及退出驗證，只寫本機workplace。
完成後由[HD四側重播組裝器](../../tools/build_hd_runtime_replay_probe.py)沿固定版既有檢查器，
比較原型HD、原型未啟用HD、正式前端及原文控制的原版狀態、WAV與存檔。

- 只接受已驗原版指紋、入口碼、完整來源、畫布與幾何；未知來源維持原版。
- 在已辨識呼叫進入時保存該次底圖，返回後核對實際寫入與像素，才建立顯示覆蓋。
  保存畫面、清除原圖與HD合成都在前端記憶體，不寫入DOS。
- 後續原版寫入必須使受影響的顯示覆蓋失效，包含同值寫入。
  已辨識的同素材重畫在返回並核對後重新建立；未知寫入保留原版內容。
  逐像素還是整素材撤銷，須以遮擋原型比較後定案。
- HD目的矩形沿原版放大四倍，點擊範圍由原版決定。候選的輪廓、透明邊界、
  底圖恢復與遮擋安全範圍待審；目前alpha涵蓋率不是正式通過門檻。
- 合成需驗證原版底圖、HD、所選語言、原版游標與畫面外設定列的順序。
  現有文字清除與繪字仍在同一介面，分層介面須經本規格審查後實作。
- 開關HD不得推進DOS、改寫存檔或混用上一畫面的底圖；缺件回原版並記錄原因。

## 執行期與真視窗隔離驗證（2026-10-12）

原型6fefe32f…由正式R27前端的可丟棄副本組裝，只改adapter及語言合成介面，
另加兩份原型Go；33份Go來源有完整指紋。14項正式來源綁定沒有改動。
原版程式、輸入、音訊、存檔與已發布版沒有改寫。

confirmed限本路徑：

- 原版53筆輸入重播至134600000步，49個檢查點的CPU、完整RAM、VGA及DAC相同；
  原型合成沒有改寫CPU、cycles或RAM，兩個原版存檔相同。
- 10次建築來源／參數／440點實際寫入通過，1050點游標暫繪完成互逆還原。
  440筆依局部位移排序，以uint16小端位移加色號編碼成1320bytes，指紋為
  1c5978b8b131150ba8abecca42a240282344553352195d683ad827e51b4fbef1。
- 18反例全拒絕：錯x、幀、y、畫布、寬、來源指標、來源bytes、入口碼及逾時返回；
  未知同值／改值寫入、過期像素、未完成游標配對交錯、未知游標來源、未完成游標緩衝；
  重複繪點、矩形外寫入及錯繪點。反例只改Machine私有複本。
- 676項既有Go零skip及go vet通過，既有原版模式未退步。
- 152組真X11原版／HD及五語檢查通過。各次open、ready、apply、resume共608筆事件，
  都在各自同一步數保持CPU暫存器、完整RAM、VGA、DAC、DOS輸入數及滑鼠狀態。
  五語進城及重進為621點，正常重新懸停的浮標保留460點，百科及離城為0點，
  關閉百科恢復621點。3280點不透明游標逐4×4像素等於原版。
- 本批67筆實際DOS輸入重播至193000000步，原型HD、原型未啟用HD、正式R27及
  原文控制的完整CPU、RAM、VGA、DAC、WAV與存檔全同；HD重播終點合成畫面與真視窗相同。

本批右鍵確實開啟PEDIA.TXT:@BUILDING32，來源鍵、正文及實際畫面同時核對。
第一次Escape關閉百科並返回殖民地，第二次返回世界，第三次開退出確認框。
前批R29固定路徑只顯示浮標的收據仍保留，不將本批結果回填成前批已開啟。

繪製順序為原版VGA、當次底圖恢復與HD、所選語言、82點原版游標；
畫面外設定列最後顯示。原版模式沿既有介面逐像素恢復，不寫DOS。
未知來源或游標／畫布不同步時回原版並記錄具體原因。本批完成的152組沒有同步回退；
早期失敗樣張曾記錄不同步，保留在本機，不能宣稱所有暫態皆已閉合。

單一有界容器的四側重播牆鐘為42.213／34.759／25.544／23.781秒，
順序沿上列四側。各側含不同觀測與合成工作，這是探索量測，不能當作純HD成本或平台FPS。
R4視窗抽樣1.328GiB，容器上限2GiB；R3起GOMEMLIMIT為1200MiB。
未做跨平台效能或真硬體音訊驗收。

## 正式接線契約（2026-10-12）

證據審查：上述原版來源、逐點寫入、遮擋、游標、152組正常GUI及四側重播，
足以授權本切片。沿使用者已確認的精細像素畫風及正式接線指示，採用已驗v4原圖。
這是該畫風內的素材實作，不擴張地形、人物、動畫或其他座標的已驗範圍。
前節「未定正式素材」保留為當時的研究狀態。

- 正式素材入口為[graphics/manifest.json](../../graphics/manifest.json)，
  PNG為[building-032.png](../../graphics/building-032.png)。保留v4原始位元組，
  來源、完整生成提示、參考指紋、尺寸、透明邊界及權利分類同存清冊。
  只加入imagegen生成圖，不加入原版參考圖、解碼像素或存檔。
- [正式HD載入及合成](../../tools/hd_runtime.go)只接受固定清冊、PNG、VICEROY.EXE
  與BUILDING.SS指紋。清冊及PNG是小型有界檔案；符號連結、缺件、損壞、尺寸錯誤
  或HD來源版本不同均停用HD，記錄原因，保留原版。既有原版啟動指紋守門先行，
  VICEROY.EXE等必要檔案不符時仍拒絕啟動。啟動後只用已驗的記憶體素材。
- 沿原型的當次底圖、440點實際寫入及621點擁有權。任何未知寫入逐點撤銷，
  包含同值寫入；只有完整且無交錯的已驗游標互逆配對可還原底層擁有權。
  素材按像素中心最近鄰取樣至92×108，只畫在已驗[224,52,316,160)範圍。
  透明處使用當次底圖，浮標及其他原版內容保留在上層。互動範圍不變。
- 合成介面由原版VGA建立底圖，依序恢復當次建築底圖、畫HD、畫語言文字、
  還原82點原版游標，最後顯示畫面外設定列。原版模式沿原有合成介面。
  游標或畫布暫態不符時，只對本次畫面回原版並在收據記錄原因。
- HD缺件時，遊玩中的Apply沿既有準備／保存／提交交易拒絕，生效選項、畫面
  及偏好檔不變。啟動讀到HD偏好時，只將當次有效圖像模式回退original，
  保留選定語言，不寫偏好檔。設定列與後端必須使用同一個有效選項。
  有效素材恢復後，下次啟動可再次使用原保存的HD偏好。
- 正式組裝入口為[build_window_prototype.py](../../tools/build_window_prototype.py)
  及其共用語言接線器；正式啟動器以--hd-assets指定包內graphics目錄。
  [封裝器](../../tools/package_release.py)只收固定清冊列出的生成素材，
  逐檔核對指紋後記入包內manifest。不得全面開放PNG或其他原版檔案。

驗收須包含正式啟動器正常GUI、五語原版／HD切換、浮標、百科、離城、重進、
存檔、缺件／錯件與保存HD後重啟，以及相同實際輸入的原版狀態、WAV與存檔重播。
[正式HD測試](../../tools/hd_runtime_test.go)驗載入守門及偏好回退交易；
另由[啟動缺件GUI探針](../../tools/probe_hd_startup_fallback.py)以正式啟動器走
缺目錄、缺圖、錯圖、錯清冊及素材恢復五個新行程，驗證有效選項與原偏好檔。
綠色測試不單獨授予CONFORMED。地形、人物、動畫及其他建築仍未完成。

## 正式正常路徑驗收（2026-10-12，R31）

正式組裝器產生1783c5ef…前端，33份Go與16項來源綁定逐檔保存。
建築觀測、底圖、擁有權及游標方法與R30已驗核心在識別字正規化後相同。
685項Go零skip及go vet通過，正式素材清冊、PNG及五個封裝拒絕反例通過。
Linux、Windows及macOS啟動參數均含固定graphics入口；本輪未重建發行包。

confirmed僅限下列正式路徑：

- 正式啟動器沒有研究HD或隔離語言旗標。152組真X11五語原版／HD檢查，
  608筆設定事件保持原版狀態，3280點不透明游標相同；本批沒有畫布／游標回退。
  進城、重進與關百科為621點，浮標460點，百科、存檔頁及離城0點。
  已目視繁中浮標及韓文關百科後畫面。
- 本批65筆實際DOS輸入至205400000步。正式HD、同版純觀測、舊正式R27及原文控制，
  完整CPU、RAM、VGA、DAC、WAV及兩份存檔全同；HD終點合成與真GUI相同。
  五語停止重建及取消／保存失敗／整包交易檢查保留。此處不替代歷史不同路徑收據。
- 五個新行程走缺目錄、缺圖、錯圖、錯清冊與恢復。前四個以日文及原版圖像啟動，
  Apply HD失敗保留生效資料及原偏好；恢復後以原保存日文／HD啟動。
  共24筆設定事件各自維持原版狀態，五次偏好檔位元組全同。
- 封裝只收清冊及生成PNG。缺圖、錯圖、錯清冊、連結圖與額外原版檔名均拒絕。
  原版參考圖與解碼像素未公開，生成PNG原始位元組保持不變。

本機根為workplace/reports/goal186-display-hd/hd-formal-r31。
重生依run-build-test.sh、run-gui.sh、run-replays.sh及run-startup-r3.sh，
核心與封裝稽核為audit-core-package.py。各項需要新的輸出目錄，原版及研究輸入唯讀，
UID／資源／清理契約沿AGENTS.md。GUI及四側重播組裝器加--formal才走正式入口。
完整三平台交付、跨平台效能、其他素材、動畫及完整五語均未完成。

| 正式收據 | SHA-256 |
| --- | --- |
| 前端 | 1783c5efee7944e2c8b6c30480846464d1885d9a34589f0584c64d0d94a6b653 |
| build-tests.json | 9f37e5a280eed4b5b187ee71b9e9ddedcfc2c975e337157bffc2d8eeb5bbfbf1 |
| gui-r1/check.json | 10939de2f8fbeb3f5f5ae55aaf2358f2291fb3ddcae92827211081a77b6e7db4 |
| gui-r1/gui.inputs.json | b209f8023085f5b6f7f7bbe206b6c8589f6c9ab8603615bca1b3f07a068ac26a |
| gui-r1/gui.display-events.json | 4d3b585657893e0dd416d602ae43eb9980f7e78c525f507a33ea2baac14b6466 |
| replays-r1/check.json | 720ed3cf05f7e6bef8204e306221c4d917f29be7b170b1c2ad9a0753d3dcd2b9 |
| startup-r3/check.json | 101c3b7a9a021a996090cdda083f131a320885f2877ea0a4a3c8f91f9bc22233 |
| core-package-audit.json | 4da66e7b0e82d4617689f8a2205389fc8240f4ee267918254f00598f3e35e8b6 |

## 重生與收據

研究入口為[畫布探針](../../tools/probe_hd_canvas_writes.go)、
[IDA參數查詢](../../tools/ida_hd_draw_parameters.py)與
[參數及寫入稽核](../../tools/check_hd_draw_parameters.py)。
先用既有--draw-query收據，加--draw-parameters及--draw-write-stream取有限事件；
不加新參數時維持舊觀測結果。另跑參數、舊觀測與--control，共四組。
IDA查詢從唯讀VICEROY.EXE新建容器暫存資料庫，輸出只留workplace。
六個錯誤證據反例全拒絕，四組CPU、完整RAM、VGA與DAC相同。
本工具不記錄WAV，沒有以本輪聲稱音訊對拍通過。

本機根目錄為workplace/reports/goal186-display-hd/hd-building032-draw-boundary-20261012。
IDA重生指令為parameters-r1/run-ida.sh，Go重生腳本為run-parameters-r3.py，
稽核指令為parameters-r3/run-audit.sh。Docker掛載、資源與UID契約沿[AGENTS.md](../../AGENTS.md)。

| 收據 | SHA-256 |
| --- | --- |
| parameters-r1/ida-parameters.json | f891aeed6b49d0aab9448cb10bfc7b63ead2762360e62b31f8c99abcc4ab08eb |
| parameters-r3/stream/draw-boundary.json | 581013a3496a1228eb49ce17da494748601840a41ed1337612172ab0000e8e8a |
| parameters-r3/parameter-audit-v2.json | ce321a3e3e5a11520a76661e9754417bdebd97240748236cd44adf65f00d211e |
| parameters-r3/negative-audit.json | 8ee3fdc1b7d92a6c4bc9500bf2ccda4b620502e51795a7b4183c9b0616469ff0 |
| parameters-r3/probe-check.json | cfd3f4f6a758dac71bb44f02d60130d4c076cd3054375b9c51c42ad1d8b15f96 |

完整指令與原版快照只保存在本機。歷史GUI的完整RAM差異仍未知；
本次正常GUI輸入重播不冒充該歷史GUI同狀態，也未增加文字shown、HD或新版交付完成信用。

### 正常GUI收據的重生

入口為[生命週期探針組裝器](../../tools/build_hd_lifecycle_probe.py)、
[生命週期稽核器](../../tools/check_hd_lifecycle.py)及
[IDA游標查詢](../../tools/ida_hd_cursor.py)。只接受本次已驗53筆GUI收據；
不是任意遊戲輸入重播器。缺原版時前兩個工具明示SKIP並回傳77。
下列命令在既有Docker內執行，掛載契約沿AGENTS.md；/out為上述本機證據根。

```bash
python3 /repo/tools/build_hd_lifecycle_probe.py \
  --gui-dir /out/lifecycle-r29-r1/gui \
  --output-dir /out/lifecycle-public-r29-r1 \
  --draw-query /out/query.json
python3 /repo/tools/check_hd_lifecycle.py \
  --evidence-dir /out/lifecycle-public-r29-r1 \
  --gui-dir /out/lifecycle-r29-r1/gui \
  --cursor-ida /out/ida-cursor-public-r29-r2.json \
  --game-root /game --output /out/lifecycle-public-r29-r1/audit-v3.json
```

組裝器沿Go1.26.7既有映像、/dosgolem唯讀副本與離線Go快取，執行go build、go vet及兩組重播。
IDA沿相同已驗9.4映像，在/tmp複製唯讀VICEROY.EXE新建資料庫；
設定COLONIZATION_HD_IDA_OUTPUT=/out/ida-cursor-public-r29-r2.json後，
以idat -A -S/repo/tools/ida_hd_cursor.py /tmp/VICEROY.EXE執行。
公開工具重生的既有原版檔案與先前私有收據逐位元組相同。
六種錯誤證據均拒絕：錯原版、假GUI狀態、刪同值寫入、錯游標來源、錯舊值與錯IDA分支。

| 本輪收據 | SHA-256 |
| --- | --- |
| lifecycle-r29-r1/gui/check.json | 3966749913e10f1d9f7b1c5c1a509486ab74ffdbcadfdb036696604597c0319a |
| lifecycle-r29-r1/gui/gui.inputs.json | 3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca |
| lifecycle-public-r29-r1/observed/draw-boundary.json | dd0da78185958acb9e9cb3acfd2965493e3ff74a4cbc9ddadfda8b40e1df129b |
| lifecycle-public-r29-r1/observed/cursor-writes.json | f63993b47a9f632d02a650bd7cfe8bf08f1d46973995727dca52f2588421d991 |
| ida-cursor-public-r29-r2.json | 7afbde56cffa45438a6a9638996487413c0a72b3dc202d5b29405bcaddf63726 |
| lifecycle-public-r29-r1/audit-v3.json | 74247994a1ffa7ff3971d5ce3e3bd5fe83da8709f72053d352dd308a97bbca81 |
| lifecycle-public-r29-r1/negative-audit.json | 085d6c386cb18b238b9651320a4753226fedc48c38caacd8872f7015e04eaee1 |
| lifecycle-r29-replay-r3/lifecycle-audit-v4.json | 8c0be41f1573771af630ff6826fb3855691d088292d52f1e1a2dacf64db4cac5 |
| tools/build_hd_lifecycle_probe.py | e9c136d12c6004db0c13c08cfb235a2a168fcfa0b174ba569f1a553a281ae451 |
| tools/check_hd_lifecycle.py | b0117769d6a93c81b238c073317a13c92340508548b6337ce122f76c96fe8210 |
| tools/ida_hd_cursor.py | 3a43dd5c92f93c5b5face1b6d78c99ce44d36091c6e63d7f07411c325066a6d2 |

新收據只解除本路徑的原版遮擋、離城、重進與游標來源未知。
歷史GUI完整RAM差異、返回附近碼成因及其他游標狀態仍保持原等級。

### HD執行期原型的重生

本機根為workplace/reports/goal186-display-hd/hd-runtime-r30-r2。
先在既有Go容器執行build_hd_runtime_prototype.py的--output-dir，檢查build.json，
再用上述生命週期測試、HD視窗組裝器及四側重播組裝器。輸出必須是新的workplace路徑，
原版、正式R27副本、dosgolem及研究輸入唯讀；只開本輪輸出與離線Go快取可寫。
完整GUI與重播命令分別保存在本機run-gui-r5.sh、run-replays-r5.sh；
Docker沿AGENTS.md，GUI沿既有verification映像，建置沿Go1.26.7映像。

| 執行期收據 | SHA-256 |
| --- | --- |
| hd-runtime-prototype | 6fefe32f41fe019b30b0496ae2906a8ed8ae7e0f091d82266b5799eebf475545 |
| build.json | 409f84524b6277e5d3255ee298943b8ba0e6b1c880b3f5ee1921a5faa6a571f4 |
| native-replay/check.json | 2cc7ba747985437b5ccb45affe4a0c0ef24c53e0e7c49b84c0012352fe2fbf0d |
| regression-check.json | eef1909d0610e6bab1ea4ff15590038ca2b7da2ed25118d58f94fb520e1d3bf4 |
| gui-r5/check.json | 1d7d70fd5563143d570c2c493a4606eed23c50cdefebcfe7d6bc65f09aaaa4ae |
| gui-r5/gui.inputs.json | d6cb0158fac68cfc208bed2dcdac82a8e48c1cbc21ebfa03c4f5058dcba763ee |
| gui-r5/gui.display-events.json | 7bd3e4311d7f22973ca40c56b22e31bfb044fb512f4b31a78fca5aa6d4b2eab4 |
| replays-r5/check.json | fe217de8c613506af0a848498d5364f3325b19851865d5c79ad1a429c42c8ffd |
| tools/hd_runtime_prototype.go | d5135dc7fcbd69ad3d1234910b8d89e0243ce468523c601afae9703164a30c43 |
| tools/hd_runtime_prototype_test.go | d4fbab7aed428169c46296694e8eff7ae10471024ed70cb0d47ffff78b0a532d |
| tools/build_hd_runtime_prototype.py | 00fa2577b2ab4de59f5a936dd4255c7a61976910a6a171f1026705fd7fab7f17 |
| tools/build_hd_runtime_gui_probe.py | c611e88ee9d516490e3074cf93b7f33ea74288ed7516708140be91c28dbf63a2 |
| tools/build_hd_runtime_replay_probe.py | 966b0892d865a4ddafef0b94a816ab00edd5d9fdfc969029176ff1588c9ae82c |

## 2026-10-13共用HD清冊擴充

首座原始生成圖、440點來源、621點幾何與游標方法不變。
共用載入器新增海洋第148幀，完整清冊、PHYS0.SS、生成海洋與整組缺件回退
依[規格062正式契約](062-hd-sea-draw-lifecycle.md#2026-10-13正式接線契約)。
R35正式GUI重驗首座進城、懸停、百科、離城與重進，並重跑原有偏好守門；
本次來源暫態回退另記，不外推持續HD或其他素材完成。歷史R31收據保留。

## 2026-10-19 R91剩餘建築與百科來源DRAFT

目前BUILDING.SS固定原檔e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4，
48幀中31個已解碼非空幀尚無正式素材連結，尺寸包含23×27、44×22、73×18等。
此為來源清冊差額，不等於31種正常玩家路徑已驗證。

既有PEDIA.TXT有42個BUILDING文字鍵。沿已驗正常讀檔與百科選單操作，
從Colonial Buildings逐頁取得原版畫面，保留當次輸入與終點。
頁標籤使用中性page編號，後續以實際完整來源及寫入判定圖像，不以頁號對應原始幀。
已有建築的城內信用保持原範圍，不先外推到百科、其他位置或未觀測幀。

本機根workplace/reports/goal186-display-hd/hd-building-pedia-remainder-r91，
原版入口capture-r91-building-pedia-r2.py；r1因舊抓圖腳本的25秒等待不足而中止，沒有驗收信用。
目前新增候選仍在本機，尚無正式接線，
不增加218張原圖與218個完成連結。來源、幾何、遮擋與正常原版狀態通過後才審READY。


### R91正常原版來源審查，仍為DRAFT

confirmed僅限原版來源觀測，不增加生成圖顯示或HD完成數：

- bfa70a90…正式組建以英文／原版模式走正常讀檔及百科，54項GUI，1018筆實際DOS輸入，終點1412200000步。中性page標籤重複時照實保留，不以42個文字鍵或43次開頁推出圖像分母。
- 隔離dosgolem固定82a14b266e1b5bc904e2d0fe507daf6bea41a013，以Go1.26.7重播同一操作。控制／觀測／GUI的CPU、完整RAM雜湊、IDX及DAC逐點相同；控制與觀測週期相同，四種原始畫布檔逐byte相同，終點完整RAM與GUI逐byte相同，存檔相同。沒有本輪WAV信用。
- 87次0D46:000A完整呼叫均匹配BUILDING.SS的完整編碼、寬高及全清冊唯一候選。當次AX均為原始ordinal加1；保留原值，不用研究ID取代AX。入口碼c828000052535057568b4702，返回時SP加10，DS:BX目的為200×320的Main畫布0x2CAE0，DX與堆疊y均和完整實際寫入相符。
- 寫入入口0D46:0181、01B4、01D2的16 bytes逐次核對。完整不透明寫入各一次、色號與來源全同，透明點與矩形外不變。每個來源保存實際出現的入口位元集合，未觀測分支不自動開放。
- 獨立Python從103177個來源寫入／撤銷事件重建54點擁有權，包含51545次撤銷及182次同值撤銷，與原版畫布及探針收據相同。事件只省略已無擁有者且不在繪製中的無關寫入；32M上限保持。
- 42個非空來源已見，其中新未連結的30幀為0、1、2、3、4、5、6、7、8、12、13、14、15、18、19、20、22、23、25、26、28、29、33、34、36、37、38、40、41、46。第47幀仍未知；本次Warehouse Expansion百科頁沒有該圖像，不能把候選補進原版沒有的位置。
- 37個百科圖像完成完整不透明索引比對；其餘五個已觀測來源來自同一路徑的城內畫面。此處不把原版來源信用外推為其他位置的正式HD。

原始輸入仍為本節固定BUILDING.SS，OPENING.EXE為3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39，
VICEROY.EXE為a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3。
位址空間為dosgolem實模式CS:IP及20-bit線性RAM，未與IDA位址混用。
原版圖像、記憶體、索引及參考圖仍在忽略的workplace，不加入Git。

| 本機收據 | SHA-256 |
|---|---|
| r91-native-replay-r3-check.json | e10e2715e8fc653bdd59289f60050b56609baa9080d14469977ad560366b6c02 |
| r91-building-source-audit-r1.json | 5284c510afea1096259d29cf332d3a13f0618a7ae46d80b9e5c521f2637085c4 |
| r91-building-native-source-r3/main.go | c2251e66b58ff3fedd64397c5b9723d52dad24db19764ae360a00117597f2c97 |
| 當次gui.inputs.json | a386d0832e02b4a36ef5d7ac6c7ce7a7a7b7cb94c8a1ce858ffd9e0978b91e96 |

本機重生順序為capture-r91-building-pedia-r2.py、run-r91-native-source-r3.py與
check-r91-native-sources-r1.py，沿本節本機根及AGENTS.md的Docker／唯讀輸入／UID契約。
R2探針先前記錄已失去來源的矩形重畫而達32M上限，完整信用只給R3；
首次探針的原檔名稱檢查與後處理的RAM快照檔名錯誤，均保留為工具失敗，
沒有更改原版狀態或放寬GUI雜湊比較。R3使用原版完整RAM雜湊及終點bytes，
不宣稱不存在的逐點RAM檔。

### R91生成候選與幾何原型

首十張候選為0、1、2、3、4、5、12、13、14、15，沿定稿畫風及各自原圖生成。
每張保留原PNG及alpha，來源、提示、尺寸、雜湊及權利在本機building-NNN-generation-r1.json。
取樣區只用於像素中心取樣，不改原PNG或alpha；目標內容區依該幀原始不透明邊界，
各候選仍裁在實際來源擁有的4倍像素。已目視building-first10-geometry-prototype-r1.png，
幾何紀錄building-first10-geometry-r1.json為292df015e614450c3ea6cf55107f9345256fc51982e817b8570ae14f67a67751。

其餘23×27小建築候選持續製作。第40、41幀首版加入來源未見的煙囪／鍛造標記，
不選用，重繪另留版本；第47幀即使生成，也須待正常原版來源才審READY。
私有原型只擴充既有[建築核心](../../tools/hd_building_nine_runtime.go)的資料列，
不由正式組裝器引用。私有來源、幾何、完整RGBA及守門審查通過才授予READY；
正式正常GUI、游標、封裝及當次原版重播通過後才授予CONFORMED。
上述DRAFT階段的正式素材與來源連結為218。


### R91三十個新增建築來源READY

本次READY只授權前述30個已正常觀測來源的生成圖，排除第47幀。
原始來源、位址及版本沿上節，型別資料為
[建築核心的固定來源列](../../tools/hd_building_nine_runtime.go)及
[生成素材清冊](../../graphics/manifest.json)。既有十來源的資料與所有核心函式保持，
只擴充30列；R42九來源的49點沿其固定模型回歸；R44第十列沿既有獨立收據，
不把未收錄它的R42模型混用。R91新列另由本輪收據驗證。

- 每列保存原始ordinal、寬高、完整編碼長度／雜湊、不透明點數、排序寫入雜湊、
  實際writer位元集合、生成PNG雜湊／尺寸，以及逐幀取樣與原始內容區。
  入口須匹配原版指紋、AX、完整來源、DS:BX Main描述、合法完整矩形及原入口bytes。
- 只在原版呼叫完整返回，且各不透明寫入各一次、值及排序雜湊全同時取得擁有權。
  未知或同值寫入撤銷，游標只沿既有固定來源及成對bytes恢復；不以畫面像素相同重授來源。
  未驗分支、錯源、裁切、錯碼、缺寫或重寫保持原版。
- 生成原PNG與alpha原樣保存。依每列內容區及取樣區作像素中心取樣，
  只在實際擁有的4倍像素合成；不改原檔、原索引、原色盤、規則、輸入、音效或存檔。
  不把圖像HD授權擴張為文字字級、語言包或原版流程變更。
- 私有候選只啟用本輪30列，走當次1018筆正常輸入及全部54個檢查點。
  原版CPU、完整RAM雜湊、IDX及DAC保持；每個新來源都有正常可見正例。
  獨立Python從原始來源擁有權與原PNG重建55296000個完整RGBA，
  包含23247個原始格及355387個alpha像素，480個來源／寫入／撤銷守門通過。
- 老十列的游標還原仍沿R44證據，不和本輪只記未知撤銷的稀疏來源模型混比。
  首個混合原型因未替老列載入游標還原模型而中止，未放寬新30列的逐點比較；
  後續候選原型只啟用本輪30列。嵌入JSON與DISPLAY缺漏先修正工具環境，
  不列產品缺陷。所有首次失敗收據保留。
- 第40、41幀使用第二版原PNG，第一版未選用；第47幀只留本機候選。
  30張正式原圖使素材數為248張／249檔，舊218張及metadata保持。
  來源清冊仍為218個CONFORMED連結，待正式驗收才增加。

正式載入與封裝逐項固定清單及雜湊，不全面開放PNG。
缺件、錯件、非普通檔、錯清冊或額外原版檔仍失敗回退原版，不改已保存偏好。
正常五語／兩模式、各新增來源、游標進出、離頁與關頁、完整GUI／X11像素、
當次原版／音訊／存檔重播及封裝拒絕另作CONFORMED閘門，目前均未外推完成。

| READY收據 | SHA-256 |
|---|---|
| r91-building-ready-r1.json | 794cf0a7b32fbb1c9b5520c275e0e7c8cea291d76ddd55a0686d5a6dfcc33128 |
| 三十張私有完整RGBA審查 | 2324ebd68af626deeec3d126c721f5356aa577b9f36b5b5175036e116989c7d3 |
| 三十張私有原版／守門審查 | 160b409061fc1319e19df496a25fc96866bedb94a679cb03dc52cbdf589d319a |
| 三十一候選逐幀幾何，47未接線 | 69fe1541a294da689b239f1b4773fe41c07b5d9b6c7e328724a7d773c9875279 |
| 正式生成素材清冊 | 1439ee4c2a8554768e1b0b28ec55a687c2289c18d2aca60529fc87dbb02c2ce7 |


### R91正式組建與適用範圍回歸

正式71份Go、54項來源綁定完成建置及go vet。
三十列資料以外的建築核心函式保持；修正測試副本與模型範圍後，
程式二進位仍為4059a066c3f8ef4370687dbbcd6e715325518f906b7e1f5793407222de6e5248。
新原PNG與清冊共249檔逐byte封裝通過，30張及manifest的缺件／錯件／連結、
額外檔及連結根目錄共97個拒絕通過。

完整249檔正式載入保持原版RAM；三個新增圖像代表、三種清冊錯誤、
兩種原版版本錯誤及偏好交易，共十個具名範圍零失敗、零skip。
這是比例抽樣的執行期守門；逐檔封裝97項另列，沒有稱為90次全程載入。

舊模型只收九個來源16、21、27、35、39、42、43、44、45。
其固定模型65e5e83ac8ba6cfe6788b4dec7fc7f9b2349e392c06a8ad6053c2c9a390e3d93，
本次原版49點、120次接受、零拒絕、180個反例重跑通過。
此測試只啟用該九列並比較原物件圖層，後來新增的整幅背景依規格069驗證；
不再把第十列或全新背景混入沒有收錄它們的舊模型。正式程式仍載入四十列，
R44第十列的既有CONFORMED證據不重開。

首次完整測試副本漏了OPENSHIP等片頭逐幀原檔；
現已由固定片頭定義去重補入，另包含KING1.SS。tmpfs預設執行限制先阻擋Go測試，
只修正容器內測試暫存的執行設定後重跑，未更改正式程式。
正式GUI首輪誤要求Main圖像的游標配對計數增加；當次663個原圖格在Main保持，
VGA游標覆蓋其中61格，整個游標82格。新抓取驗證實際VGA游標與完整X11，
不要求不適用的Main計數。首輪保留部分收據，完整GUI與當次音訊／存檔仍待完成。

| 正式檢查 | SHA-256 |
|---|---|
| r91-building-formal-build-r4.json | ddfac8297d7a7d7b2a838ad22e45acd2319d534f4453c24d0b0ce6a9840a09dd |
| r91-formal-guards-r3-check.json | 04bb88aa9607a8b9cf4d482d71d9de5af23d481107a11c730b9b0d082a72f06e |
| r91-package-check-r1.json | f5b9885ff2698fe5e0fab1f76ef473aeaf54c1452db9bb9198fadb46864179da |
| 舊九來源49點回歸 | 655c03b7c74b669483e180cab75d21a3ebccfedca662f83fb19ee6d2b8dff033 |

### 2026-10-19 R91三十個建築來源限定CONFORMED

confirmed限本頁READY的30個來源、固定原版與正式4059a066…組建，原始碼為888c2df。
建築核心函式與R90逐byte相同，只有已審查的資料列擴充。第47幀仍未知，不接線。

| 驗收 | 已通過範圍 |
|---|---|
| 正常GUI | 159項實拍，30個新來源各英文原圖／HD；0、3、6、19、38五個代表各五語／兩模式，四種非英文各有游標移入與返回；正常換頁、返回列表及關閉百科。 |
| 當次原版來源 | 154個獨立狀態與控制、GUI全等。25341561筆事件獨立重建78次木紋解碼、1562次完整SS呼叫；含38442次背景同值撤銷及223次SS同值撤銷。 |
| 完整畫面 | 158張完整RGBA共161792000點、159張X11共162816000點相同，含1134819個建築alpha像素、65745個小圖像alpha像素及400個Noto欄位。預期由當次原版來源、原PNG與綁定字模獨立產生，不取正式輸出作預期。 |
| 離頁限制 | 最後返回世界的畫面驗X11全等、建築來源與繪製均歸零；繼承海面與地形不在本輪百科獨立畫素模型內。該畫面仍納入完整原版狀態及音訊／存檔重播。 |
| 三側重播 | 848筆當次GUI輸入至1010800000步，原文控制、原圖模式及正式play=true的CPU、完整RAM、IDX、DAC、WAV、存檔與GUI全等。全部288份原始檔案指紋保持。 |
| 載入與索引 | 前述十個具名範圍、249檔封裝／97拒絕及舊九來源49點／180反例保持。索引新增30個來源至248連結，其他1522列及舊218連結保持；8種未完成／錯誤審查均拒絕。舊國王分支索引逐byte重生不變。 |

WAV為4339213個立體聲frame、49715Hz、16bit且非靜音，SHA-256
7992ac70274940a973eea1df786497bbe974efd4f16bddda670e79fce02593e5。
相同限技術輸出，不增加人耳或硬體逐週期信用。正式PNG、alpha、版本與原版行為保持。
README新增本輪繁中軍械室實拍，原圖不裁切或重編碼，來源見[截圖清冊](../screenshots/readme-captures.json)。

原版記錄器只省略已驗正向搬運中來源與位元組皆相同的107374867次重複寫入；
所有來源繪製、字形、游標、未知寫入及同值撤銷仍保留，120M事件上限不變。
針對性反例另驗同值來源／目的失效、改碼、反向搬運及特殊寫入，不改正式程式。
首兩個追蹤失敗仍無信用。完整畫素檢查器先後補正百科專用譯表、既有側欄兩像素陰影、
規格036的百分號跳脫，再由乾淨輸入重跑；不把驗證工具缺項算成產品缺陷。

本機根沿本頁R91目錄。重生入口為capture-r91-building-formal-r2.py、
run-r91-formal-native-source-r3.py、check-r91-formal-sources-r1.py、
check-r91-formal-pixels-r4.py、verify-r91-gui-replays-r2.py與make-r91-conformance-r1.py。
來源索引使用[擴充器](../../tools/extend_hd_story_source_index.py)的--buildings分支，
--baseline指R90的218連結，--ready及--conformed指本批審查，--assets指graphics，
--output指定尚不存在的輸出。只接受完整的本批CONFORMED審查。

| 本機收據 | SHA-256 |
|---|---|
| r91-building-conformance-r1.json | 2a061644c4eccb08cd2d28974a8bc90127d895cb64620fd753229ab7245bfcfa |
| r91-building-formal-gui-r2/capture.json | 326033a8986cefeefbf62621b97507e1340ef16147d175795c0b1b5b4274b7b8 |
| r91-formal-native-source-state-r3.json | 9f158736da110a041168eba8daac547ea3ccde086825cd77685627b4f923220d |
| r91-formal-source-model-r1/check.json | 86f26d3d4da9daf4d82565149cb7c797d8b90a8949aab8d143cc0ee94f658a5e |
| r91-formal-pixels-r4-check.json | 1f996eef51eb2c9e9f213b932f390032bbd88012443a59175c41efe0535e43a0 |
| r91-building-replay-r2-check.json | 8be527042cc4d0c101fb2aeef35da746b9b4023d2f6cdbee46580314007dbe8e |
| r91-building-source-index-r1.json | c09f53237609e443c64651d9cde9c6d3ddcbb665365b1e4c53003544d56dab5b |
| r91-building-source-index-check-r1.json | dbc352bf596461ba4f5be2d1c468dbe6029e1ad116bf4dd5d214035facce0b49 |

工具為Go1.26.7、Python3.11.2／Pillow9.4.0及隔離dosgolem
82a14b266e1b5bc904e2d0fe507daf6bea41a013，位址沿實模式CS:IP與20-bit線性RAM。
其他來源、動畫、完整五語、全量HD、影片與新版交付未完成，既有發行版本不變。

### R103第47幀接線READY

使用既有building-047-candidate-r1.png原圖與BUILDING.SS清冊來源94，原生44×22、710個不透明格，接入現有完整D46印圖及建築HD繪圖介面。原圖保持1774×887 RGBA與原始alpha，以完整原圖對應原生44×22範圍；原版來源形狀、位置與透明索引保持。來源雜湊、完整寫入指紋及原圖指紋均固定，無新增來源調查。接線後以正式介面測試畫面有出現驗收，限顯示，不新增原版精確對拍或正常玩家路徑聲明。

### R103第47幀顯示通過

正式素材載入、D46編碼來源選擇、完整來源finish及HD繪圖介面的來源fixture通過，第47幀圖像已在測試畫面出現並目視確認。測試提供原生寫入樣本，記為DISPLAY-PASS，不新增原版CPU、正常玩家路徑或原版精確對拍聲明。BUILDING.SS的非空來源已全部有正式素材連結。

正式程式SHA-256：3dddd1dca192b02da8af86437f6dd2d2a994e88ac21bd1c17f38d03141074ea9。建置與go vet、完整HD載入及332檔封裝指紋通過。本機收據在既有hd-opening-animation-sources-r84工作根的r103-formal-display-r1/check.json，SHA-256：e9abfdd76ef23374e2696a77618d62e58c439b36c22b52913cfb21026428b7db。
