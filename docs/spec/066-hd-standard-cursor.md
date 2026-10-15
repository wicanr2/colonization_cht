# 一般游標的HD顯示層

狀態：限定READY，沿2026-10-15 R60一般游標顯示契約；尚未正式接線或CONFORMED。
入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)，工作項目為
[Issue #63](https://github.com/wicanr2/colonization_cht/issues/63)。
本規格只處理一般箭頭游標，不擴張其他游標、隱藏狀態或動畫。

## 原版輸入與位址

工具為dosgolem 82a14b266e1b5bc904e2d0fe507daf6bea41a013、Go 1.26.7、
Python 3.11.2與Pillow 9.4.0。以下位址採dosgolem實模式CS:IP或20bit線性RAM；
EXE常數另標檔案位移，不與IDA位址混用。沒有修改原版名稱或程式。

| 輸入 | SHA-256 |
|---|---|
| VICEROY.EXE | a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3 |
| CURSOR.SS | 3ff5a4b70f08780f845b1e973d7dce3ff34868bb73279174210fce76332fffcb |
| 第000幀124bytes編碼 | d77899f35c0e5f40780af7fddd6918c58ff86005de5ea4ecfbde34f5989e7dde |
| 第000幀17×17索引 | 6ccf457146503ab4a01cdf01147d6bc8f3cb428580a644f93d9b1b6f0b43d553 |
| 一般游標RAM 256bytes | 47fced19d04987d3a0de8b6fd929abae6ba886939a2a7ce408b0213360ef1e03 |
| 53筆正常GUI輸入 | 3947d52a893ae3d6c6f388cefc1e67e4001d41270ca46e65856526a9b97471ca |
| 49點原版收據 | 821f1ba83576013bba52ca53a39273498af64c3269a819e40f2244d036a3e901 |
| 初始COLONY09.SAV | 52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b |

## R59已證實的來源鏈

以下結論均為confirmed，限上述版本與正常53筆輸入。

- 一般游標常數在EXE檔案位移0x1e074唯一出現。MZ header為0x2400bytes，
  載入基址為線性0x1100，對應RAM 0x1cd74至0x1ce74。
  原版在13216877步寫入完整256bytes，逐byte等於此常數。
- CURSOR.SS第000幀的來源記錄為4F0B:0042，來源編碼為4F10:000A，
  記錄六個word為[10,20240,5,23,17,17]。入口0D46:000A的12bytes為
  c828000052535057568b4702，AX為1。
- 第66375174與110890685步各繪一次，分別於66377561與110893072步返回
  0C6E:0051，SP增加10。17×17描述子為[17,17,59216,7274]，
  暫存畫布為線性0x2adf0，繪圖前289bytes全為255。
  每次84個不透明點各寫一次，來源色號及三個writer與原始逐寫事件相同。
  來源253為透明點，保持暫存底圖255；沒有原版逐byte把253改為255的操作。
- 返回後經0C9F:00CA的REP MOVSW逐列複製左上16×16至游標RAM。
  原碼前16bytes為f3a503f3790c81ee00808cd981c10008。
  兩次各256筆逐寫的DS:SI、ES:DI、CX與來源暫存資料吻合。
  這是本游標的已驗來源複製，不授權其他HD來源接受0C9F複製。
- 左上16×16共有82個不透明點，可見矩形為[0,0,10,14]。
  49個原版索引畫面均精確等於未畫游標的主畫布，再於實際輸入位置疊上此來源。
  來源原點與滑鼠位置相同，來源熱點為[0,0]。第一筆輸入已明示[160,100]，
  不依賴未查證的滑鼠預設位置。透明區及游標外全部像素也逐點相同。
- 觀測與無觀測控制的49點完整CPU、RAM、VGA、DAC、終點與存檔相同。
  本批沒有新增WAV收據，不授予音訊或未測游標狀態的額外信用。

原始1706筆事件、兩次來源呼叫與49份索引圖只留本機
`workplace/reports/goal186-display-hd/hd-cursor-source-r59/`。
執行入口為[唯讀探針](../../tools/build_hd_cursor_lifecycle_probe.py)，
[獨立檢查器](../../tools/check_hd_cursor_lifecycle.py)驗來源、逐寫、複製及定位；
[失真反例](../../tools/test_hd_cursor_lifecycle.py)另驗拒絕，不能替代正向原版收據。
原始collector沿用的unique_writes等未填欄位不當作證據；檢查器由原始逐寫另算。
現行證據收據為source-check-r4.json，SHA-256為
bc5d0f8025fa62dffaf33f3f65ccc7a10a9eff37ba549b3537ae68ad855e04dd。

## 候選與合成原型

兩張候選均由內建image_gen沿原版形狀與定稿畫風生成，原PNG及alpha保持。
完整提示、參考指紋與量測保存在本機對應JSON。

| 候選 | SHA-256 | 原圖與量測 |
|---|---|---|
| cursor-000-candidate-v1.png | d47a39d4f1cc70300a5dc9933165305b2c4b5c85b0e6104b1517950803994f16 | 1254×1254 RGBA，alpha≥128矩形[279,228,842,1044]。 |
| cursor-000-candidate-v2.png | 2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4 | 1254×1254 RGBA，alpha≥128矩形[106,188,721,1047]。 |

原版82點放大為1312個輸出像素。依原圖alpha矩形，以像素中心取樣至40×56，
兩版均有1184點alpha≥128，另128點不足。兩版缺口位置不同，均未接受為完全替換。
重查規格閘門後，保留此失敗及量測，不追加無依據的生成重試。

隔離候選方案沿既有原版游標底層，最後在已驗82個來源點的4×4區塊疊上v2原alpha。
這使原版輪廓、透明區、熱點與點擊位置保持；不改圖、不擴張可見矩形或互動範圍。
原型預覽為cursor-v2-original-under-alpha-prototype.png，尚非正式素材或GUI收據。
須在正常世界、城內、主選單與存檔返回實際驗證，並逐RGBA獨立重算後才評估READY。

## 原型審查前的驗證清單

隔離原型入口為[組裝器](../../tools/build_hd_cursor_prototype.py)與
[游標合成來源](../../tools/hd_cursor_prototype.go)，正式組裝器不引用這些檔案。
元件測試位於[hd_cursor_prototype_test.go](../../tools/hd_cursor_prototype_test.go)。
原PNG的獨立RGBA比較為[check_hd_cursor_prototype.py](../../tools/check_hd_cursor_prototype.py)。
正常五語GUI與邊界的唯讀副本由[GUI組裝器](../../tools/prepare_hd_cursor_gui_probe.py)重生。
正常快照的定位、原alpha及來源外比較為[GUI檢查器](../../tools/check_hd_cursor_gui.py)。
原型只在已驗正式來源副本加入欄位、明示候選載入與最後合成；以獨立旗標選取本機原圖。
沒有增加原版觀測或修改原版輸入。元件收據不能取代下列正常GUI驗證。

- 以正式來源的隔離副本製作原型，原版／HD與五語均需正常GUI樣本。
- 原型僅在既有cursorProof完整通過後合成。未知來源、錯誤表面或無法證實的隱藏狀態
  沿既有回原版行為，不猜選其他CURSOR.SS幀。
- 驗左、上、右、下邊界裁切，文字區、設定暫停／恢復、一般點擊與原版選單操作。
- 核對原版資料→暫存→游標RAM→原版定位→HD合成→正常UI→存檔的完整鏈。
  HD不得增加原版寫入、改變滑鼠輸入或存檔內容。
- READY後才可接入正式loader、清冊與封裝。缺件／錯件、原始PNG指紋、完整回歸、
  正式遊玩與同輸入原版狀態另驗；其他游標與全量HD仍待接續。

原版圖像、參考、索引與逐寫輸出只留本機。生成素材公開前須完成既有權利與正式接線檢查，
不得將原版參考像素加入新公開路徑。


## 2026-10-15 R60一般游標顯示契約READY

本節授權上述固定版本的一般箭頭游標正式接線。原版來源與熱點沿R59，
顯示方法以本節為準：先沿既有restoreCursor恢復原版不透明游標，再在已驗來源格內疊v2原alpha。
兩版完全取代的歷史缺口保留；本契約採透明合成，沒有改alpha或猜補外形。
v2的82個來源格均有生成筆觸；1312個目的像素中128個alpha不足128，由既有原版底層保持輪廓。

正式契約如下：

- 原圖固定為2839ce6c635c16af668ce251807e2723ed343052ab12cfa29a9be04cd9dbd8d4，
  原樣保存為graphics/cursor-000.png。1254×1254 RGBA，alpha≥128矩形[106,188,721,1047]。
  以像素中心取樣至40×56，放在64×64原點；只合成原版16×16中不透明的82個來源格。
- 每個來源格映射既有四倍畫布的4×4區塊，游標原點保持[0,0]，不改滑鼠輸入與點擊位置。
  裁切只依320×200可見區；右下角[319,199]僅剩透明首像素，兩側均沒有可見游標。
  來源證據仍有效，這個零點案例不列為守門回退，也不宣稱有可見HD像素。
- 只在既有cursorProof完整通過後繪製，不增加RAM觀測或放寬原版表面守門。
  未知來源、錯誤模式／大小、尾端合成／背景或來源外不符時，沿既有原版回退。
  原版圖像模式不進入本合成，五語共用同一圖像方法，文字字型契約保持。
- PNG只作顯示來源；所有原版EXE、SS、RAM、輸入、音訊、規則與存檔保持原樣。
  通用原圖下層色以當前原版索引與色盤繪製，候選用原alpha在文字之後合成。
- 正式loader沿tools/hd_runtime.go的既有入口，另驗CURSOR.SS完整指紋與PNG完整指紋。
  缺件、錯件與連結使HD整組不可用，保留語言及原HD偏好。正式路徑移除原型旗標，
  由既有graphics清冊自動載入；預期46張PNG及清冊47檔。
- 正式接線後仍須完整Go零skip與go vet、原版來源及像素回歸、正常五語GUI與邊界、
  四側原版狀態／WAV／存檔、未加觀測器的play=true、新圖與CURSOR.SS各三種新行程錯件、
  缺目錄／錯清冊／恢復及全部封裝白名單驗收。通過前不得宣稱正式HD或CONFORMED。

透明合成依Go的NRGBA→RGBA與image/draw：每通道先取P=(C×257×A÷255)右移8位，
再取(P×257+D×(255−A)×257÷255)右移8位，整數除法各自向下取整。
獨立Python檢查逐點相同，未先把兩項各自轉8bit再相加。

| R60驗證 | 結果 |
|---|---|
| 元件 | 49份已驗原版快照、6種表面守門及4種載入拒絕通過；64288個RGBA像素相同。這是元件測試，不當作新正常重播。 |
| 正常GUI | 同一Go版本完成92組五語原版／HD、正常進城／離城／存檔返回。R2的46組HD皆82點，沒有守門回退。 |
| 邊界與像素 | 29份實際快照含九個邊界／恢復樣本，8份有可見HD、1份全裁切；31840個游標輸出像素及來源外條件相同。 |
| 既有地形 | 獨立原版101次十三來源、197794事件、12823暫存轉送、5886保存／4370還原重建通過；079的21次來源、10560個來源游標還原及489952個地形像素相同。 |
| 四側實際輸入 | 99筆至214400000步，完整原版CPU／RAM／VGA／DAC、WAV與存檔相同。29點原始快照另由觀測／無觀測原版重生。 |
| 正常遊玩與成本 | 原型47Go的play=true循序ABBA，兩次候選皆驗世界、城內及存檔返回的82點，frames為0；四次原版狀態、音訊與存檔相同。固定Linux2CPU樣本基準均值35.448秒、候選34.586秒，比例0.9757，不作加速或跨平台FPS聲明。 |

R1 GUI於城內日文暫停遇到既有outside-cursor:3634守門，該組保留原圖，不計HD；
R2加邊界後以同一Go二進位完整重跑，沒有回退。右下角的零點由原版透明首像素及實際索引證實，
首輪離線檢查未區分全裁切，依來源位置訂正，不放寬像素或來源證據。
地形像素首輪沿用舊本機原圖路徑而缺檔，改綁逐byte相同的正式原圖後通過，原失敗保留。

v2的直接參考圖為原版游標與v1候選；定稿圖經v1間接提供畫風。
R59 metadata曾誤列定稿圖為v2直接參考，原紀錄與指紋保留，勘誤見本機
cursor-000-candidate-v2-provenance-r60.json，SHA-256為5b3406c8bbade64b4e7501a03e92a078911ad75e0a610817ca86d45ec852f461。
正式清冊應沿勘誤後的兩份直接參考、完整提示與原圖指紋，不公開原版參考像素。

本機根hd-cursor-prototype-r60，命令入口commands-r60.json。正式素材仍45種，原型不進發行包。
其他游標、隱藏狀態、動畫及全量HD仍待接續。

| 收據 | SHA-256 |
|---|---|
| build-r1/build-r1.json | 9c2370bc948b16dd66e8111dbb730ce8daf73d9eb029c7ebbea67b27785d1e1f |
| components-r1/check.json | cd99076332b024fd2732c289d2a6810c25302958cf907ad686bbc0dc2aa288b7 |
| components-rgba-r1.json | e4cc5569fc97d8ab83f1959e33833fbfce051373a59356b8255a92dc77e042ef |
| public-gui-r2/gui-build-r1.json | 720a1a47227841dd3949148e67d388aa3719a262922c1664fed1e50181db7e7c |
| public-gui-r2/gui-r1/check.json | 583b087ecfdcbad5b2db6ea6292f970ae862a0644297432d4abeb3efe17e0a6e |
| gui-r2-pixels-r2.json | 698f9f80290bf07f547c2544781a9d815be9d7e86b45fc51fd5787e416302583 |
| gui-model-r1/check.json | 8eec45d66932f8f02c389978364e555aa51b3633ea3652b4045e1506b8b47d7e |
| terrain-source-display-r1.json | 22511fed0c4f0a40e97e7e867a5513094e032ecce3f53a0c403a9fc00b4ea1ad |
| replays-r1/check.json | 63a5b4e5658fce9cf0568ad770743ae324cf6562bdd4d8c9706096999119b09a |
| performance-play-r1-check.json | 9735278e25193e62804633c28d0b19531ac2ac4b5c4c422f55e0536f1a7bbd5a |
| prototype-play-r1-check.json | 2c03494ff663af7abb7dc37d422e7d564ee9f211ef1f5ef6482bc055922273a4 |
| cursor-000-candidate-v2-provenance-r60.json | 5b3406c8bbade64b4e7501a03e92a078911ad75e0a610817ca86d45ec852f461 |
