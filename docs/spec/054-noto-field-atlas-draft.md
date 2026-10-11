# 四語Noto六列命令欄字模與正式接線

狀態：限定CONFORMED。2026-10-11使用者要求正式接線，先依下方證據審查升為READY，再完成正式驗收。
下方原型紀錄維持當時DRAFT狀態。
只授權已量測的六列精簡ORDERS欄位，不授權完整語言包或其他欄位。
入口：[目標186](../goals/186-display-settings-and-gameplay-video.md)，
字型決定及固定輸入見[字型來源](../../font/README.md)。

## 來源與範圍

- 原版六列的來源、字格、色層、安全區及Fortify同文來源限制沿[規格035](035-dialog-overlay-draft.md)的精簡ORDERS段落。
- 四語完整TSV來源、控制碼及字集沿[規格053](053-language-catalogs.md)。
- 只處理原型已量測的六列、18px與95個可見ASCII；每語整數字格獨立產生。
- 字模沿現有`loadAtlasFonts`的`w`與Alpha格式，不改正式圖集、原版資料、存檔或操作。

## 待查證的字模邊界

現有Cubic烘製器以四捨五入後字距作字格寬度。Noto18px在相同裁切方式下，
`V、f、j、v、y`有少量實際墨跡落在字格外。字元對照表含字不代表烘製後字形完整。

私用原型以有界、加邊界的實際渲染量測左右墨跡，擴大必要字格並保留左伸出的墨跡。
字格寬仍為整數，同時作既有消費端字距；須記錄原字距、舊字格、平移量及擴展量。
每字的全部Alpha須與加邊界的參考圖相同。整數字格與原字型小數字距不同，
此原型不能證明長文排版、字距品質或其他欄位可用。

## 正式六列契約

證據審查採規格035的原版來源及正常路徑收據、規格053完整TSV驗證，
以及本頁文末四語遮罩與裁字反例。使用者已確認四地區Noto並要求正式接線。

- 來源鍵依序為`MENU.TXT:0x00000264`、`0x00000276`、`0x00000299`、
  `0x000002A5`、`0x00000384`、`0x000003BC`。Fortify的`0x0000028D`與
  `0x00000299`仍無法區分，兩列譯文須相等；此條件只限制顯示，不能用譯文識別原版命令。
- 沿原版六列文字、座標、5px大寫墨跡、完整黑框及68／149／8色層守門。
  原版列頂為13、21、29、37、53、69，安全區`[80,12,159,77]`放大四倍為316×260。
- 只此欄位選18px，沿量測的候選22～15px及20px原版放大墨跡高度。
  左右內距各4px；以各face的CJK墨跡上緣對齊原版列頂，基線為列頂減墨跡頂加ascent。
  最長列與實際整數字格須重新量測；不截斷、不縮小猜補、不跨列重排。超界整欄回原文。
- [正式烘製器](../../tools/bake_noto_orders.py)驗證完整語言TSV，再組成既有譯稿TSV及圖集。
  不新增玩家文字JSON格式。圖集綁定實際譯稿、繁中基準、MENU來源、欄位量測、
  字型、OFL及地區face。保留全部可見ASCII與必要左右伸出墨跡。
- [欄位載入器](../../tools/noto_orders.go)只接入上述完整六列。
  `--noto-orders-locale`選四語，`--noto-orders-draft`與`--noto-orders-atlas`指定私用輸入；
  未指定語言沿用既有顯示。英文沿`--control`原版字體，不在此欄另造英文字模。
- 載入時逐鍵驗證原版檔案、片段、基準元資料、熱鍵及完整字模。
  缺資料、錯綁定、歧義譯文不一致、缺字或超界均整欄回原文，命中原因寫入既有缺譯紀錄。
  未通過幾何守門的其他欄位不得使用本圖集。原版來源存活及VGA階段守門照常生效。
- 譯文只進放大畫布的遮罩；原版命令、輸入、記憶體、亂數、存檔均不讀譯文。
  建置沿[視窗組裝器](../../tools/build_window_prototype.py)，
  回歸入口為[欄位測試](../../tools/noto_orders_test.go)。

轉為CONFORMED前，須以實際建置跑四語正常開單、停用列、關單及啟用單位，
保留GUI收據；並將正常GUI輸入重播至英文對照，核對CPU、RAM、VGA、色盤、音訊與存檔。
單元測試或私用字模探針不能取代此驗收。完整五語、設定列切換與HD仍由目標186追蹤。

## 可重現入口

[字模原型工具](../../tools/preview_language_field_atlas.py)在固定Pillow9.4.0容器執行。
參數`--layout`、`--coverage`分別指定規格053文末的已驗排版與字集收據；
`--noto`、`--license`指定字型入口的固定OTC與OFL，`--output`指定新的workplace子目錄。
工具核對來源、字型、授權及兩份Go正式來源指紋，拒絕覆寫。

產物含四份`atlas.<locale>.json`、逐字與逐列量測、Python參考遮罩及`go-probe/`。
探針逐字複製目前正式`loadAtlasFonts`、`menuZh`、`lineLayerMasks`等函式，
在既有`hr-go-ebiten:1.26.7-2.9.9-r1`容器內執行`go run .`，只核對資料與遮罩。
兩容器皆唯讀掛載專案，只開放明確輸出目錄，使用目前UID/GID、無網路、資源上限與外層逾時。

## 驗收邊界

1. 四語六列全部實際墨跡及字距在安全區內，逐字圖集不裁墨跡。
2. 原Go消費端讀取四圖集，選18px；一般、熱鍵及停用三層與獨立Python遮罩相同。
3. 錯字型、錯區域綁定、錯字級、缺字及超長列拒絕；重生輸出全等。
4. 尚須正式欄位規格審查、執行期語言包接線及正常GUI／原版同狀態驗收，才可另授權正式顯示。

本原型不增加普查shown，不把孤立字模或探針通過計為五語完成。

## 2026-10-11實測

狀態保持DRAFT，正式來源未改。四語各烘115／115／122／117字，均含95個可見ASCII。
五個裁字問題在四地區face均可重現；舊字格每語合計損失7個非零Alpha像素。
私用擴展字格全部保留參考圖的字形；六列相較舊整數字格最多增加1px，24列皆未超界。

目前正式Go來源的`loadAtlasFonts`、`menuZh`、`dialogMarked`、`dialogBlit`與
`lineLayerMasks`等函式逐字抽取後執行，四語均選18px。一般、熱鍵及停用三層
的原始Alpha bytes與Python獨立參考完全相同。20項Go反例與7項CLI錯誤輸入全部拒絕；
兩套乾淨產物的34個檔案逐位元組相同。已檢視三層比較圖，示意配色不作原版DAC色盤證據。

本機根為`workplace/reports/goal186-display-hd/`，現行圖集在
`language-field-atlas-20261011-r2/`，重複產物在`language-field-atlas-20261011-repeat/`。
初版沒有比較圖，保留在`language-field-atlas-20261011/`；以r2及下表收據為目前證據。

| 收據 | SHA-256 |
|---|---|
| `language-field-atlas-20261011-r2/atlas-check.json` | `8956fe6c658e09e052f6a9dae189bce13924de2c3198d818b34f6bdf500203ad` |
| `language-field-atlas-20261011-r2/go-check.json` | `7f00a7ced85411bc29db1775197292015abead0f13b3687363e8f0588f7a6de7` |
| `language-field-atlas-20261011-r2/field-atlas-noto.png` | `01b52f49cd1c5f98e8a04fcc083678530c68d8f8593d3be411749e80fedd9ea1` |
| `language-field-atlas-20261011-verify.json` | `daa67d12995c92222695bea780aaacb6876c47b52d67e6cae86e027330e6c9b0` |

總收據保存逐檔雜湊、固定映像ID、Go1.26.7、原型驗證腳本指紋及字距擴展量，
同名`.py`保留私用重驗腳本。烘製器另記錄Pillow9.4.0、FreeType2.12.1及逐字墨跡。
原版MENU來源及位址空間沿規格035；本輪沒有執行原版，沒有新的正常GUI或同狀態收據。

重生先依字型入口驗證各掛載來源與輸出父目錄，以固定Python映像執行：

```bash
python3 -B /repo/tools/preview_language_field_atlas.py \
  --layout /repo/workplace/reports/goal186-display-hd/language-layout-preview-20261011/layout.json \
  --coverage /repo/workplace/reports/goal186-display-hd/language-glyph-check-20261011/coverage.json \
  --noto /repo/workplace/reports/goal186-display-hd/font-candidates/NotoSansCJK-Regular.ttc \
  --license /repo/workplace/reports/goal186-display-hd/font-candidates/NotoSansCJK-LICENSE.txt \
  --output /repo/workplace/reports/goal186-display-hd/new-field-atlas
```

再驗證新輸出目錄及`go-probe/`存在且屬目前使用者，將新輸出掛為`/out`可寫，
以固定Go映像、`--workdir /out/go-probe`及`--env GOCACHE=/tmp/colonization-noto-cache`
執行`go run .`。外層逾時180秒、記憶體1GiB、CPU2、PID128、目前UID/GID及無網路。
Go探針拒絕覆寫自己的PNG與收據；每次重驗都使用全新的圖集輸出目錄。

## 正式重生與驗收入口

沿上節固定Python映像、唯讀專案與明確可寫workplace父目錄執行；輸出名稱每次另換：

```bash
python3 -B /repo/tools/bake_noto_orders.py \
  --noto /repo/workplace/reports/goal186-display-hd/font-candidates/NotoSansCJK-Regular.ttc \
  --license /repo/workplace/reports/goal186-display-hd/font-candidates/NotoSansCJK-LICENSE.txt \
  --measurement /repo/workplace/reports/goal185-player-experience/orders-compact-candidate-v2/compact-orders-layout.json \
  --review /repo/workplace/reports/goal185-player-experience/orders-compact-formal-review.json \
  --output /repo/workplace/reports/goal186-display-hd/new-formal-orders
```

每語產生`draft.<locale>.tsv`、`atlas.<locale>.json`及三層參考PNG，
`bake-check.json`記錄完整語料來源、逐字墨跡與全部產物指紋。
前端仍須載入既有完整覆蓋參數及Cubic圖集，再加上述三個`--noto-orders-*`參數。
不能把七列TSV當作全遊戲的`--dialog-draft`，也不能將本圖集交給`--dialog-atlas`。

視窗組裝器將正式欄位及測試一併複製到新的workplace建置目錄。
在固定Go映像，以`TEST_NOTO_ORDERS_DIR`指向烘製輸出、`TEST_GAME_ROOT=/game`，
唯讀掛載原版及隔離dosgolem，執行`go test -json ./...`、`go vet ./...`與`go build`。
既有音樂／保留英數測試另需原版、字串圖集與規格052的唯讀fixture；缺少時明確skip，
正式本頁驗收須提供完整輸入，不能把skip計為通過。

正常GUI仍使用既有`play_orders_compact_formal.py`的15張同步畫面路徑，
由真鍵鼠讀COLONY02、View陸上單位、開ORDERS、點停用列、兩次Escape及啟用單位。
本機驅動器保存於目標186工作根的`verify-noto-orders-formal-20261011.py`，
同側GUI輸入分別重播Noto、英文對照、未啟用Noto及錯地區圖集。
它只替換前端執行檔與顯示參數，不注入原版座標、記憶體或測試入口。
四語各自的輸入、初始存檔與二進位指紋保存在驗收目錄。

[正式檢查器](../../tools/check_noto_orders.py)的`--reports`指向四語驗收目錄，
`--build`指向實際建置、`--atlas`指向烘製目錄、`--output`指定新的workplace JSON。
驗收容器須同時將驗收目錄掛為`/out`，供重播命令中的絕對路徑回查。
它逐張核對GUI／重播像素、欄外零變更、四個停用列、關單、整欄原文回退與缺譯紀錄，
並核對四側原版完整狀態、輸入指紋、RAM、VGA、色盤、WAV與原有存檔。
此輪存檔均保持原樣，不新增存檔格式或存檔流程的完成信用。

## 2026-10-11正式驗收

confirmed範圍為四語各六列、18px及既有原版來源守門。正式前端新增三個欄位參數，
七列TSV沿用既有格式，Fortify兩個同文來源須同譯；缺檔、來源、標記、地區、字模或
排版不符時整欄回原文，記錄既有缺譯原因。其他欄位不讀此圖集，也不改原版命令識別。

240項Go測試、零skip及go vet通過，含四語實際來源／三層遮罩、56個錯誤輸入反例及
欄位隔離測試。兩次正式烘製21個檔案全等；原型抽取的九個Go渲染區塊與52f2924時相同。
正式建置SHA-256為`14a003cce886b70b793b28b71bd037bdaa18937fac74031519158e0fb41035f3`。

四語各15張正常GUI，共60張，均與自己的實際輸入重播逐像素相同。
每語Noto、英文對照、未啟用Noto及錯地區圖集四側，完整CPU／RAM／VGA／DAC、
輸入指紋、WAV及原有存檔相同。每語六張開單畫面只在安全區變動；停用色保留，
錯地區整欄等於原版英文，欄外等於既有顯示；關單、兩次取消及啟用單位後無新增殘影。
四語實際GUI並排圖已檢視，沒有將示意配色當作原版色盤。

| 本機收據，根為`workplace/reports/goal186-display-hd/` | SHA-256 |
|---|---|
| `noto-orders-formal-check-20261011.json` | `f75330b765495d8a3ca2af47f7c80a075e111ce380ae11daab1c174a16ce5b83` |
| `noto-orders-formal-atlas-20261011/bake-check.json` | `6d4d887dde28eaf8ed70c31695b909f6cb66be359af4bc2d2fcccba9f5a8af56` |
| `noto-orders-formal-build-20261011-r2/tests-with-fixtures.json` | `d44fd117efa234ff05598d7282fb6b92b7ef2198ca51f1f4a365c1b438ca53c2` |
| `noto-orders-formal-verify-20261011/noto-orders-normal-gui-r2.png` | `6415b7e5311e690667e3938a8c4712947d7d6e63bb3ef71f6a30d362a41e9f4c` |
| `verify-noto-orders-formal-20261011.py` | `185ceeceb9f98adc77c3b1f27f8fdf5d7acc68958645c687aa8c7592db9f2e6a` |

私用驗收根保存四個`gui-<locale>`及16個`replay-<locale>-<mode>`、同步截圖、輸入、
來源事件與原版狀態。沿前述固定Python／Go映像，原版MENU輸入SHA與位址空間仍依規格035。
GUI在Xvfb1360×960、軟體繪圖、UID/GID1000、無網路、資源上限與外層逾時執行；
工作完成結束自有Xvfb並刪除一次性容器。沒有修改dosgolem或公開字型、原版及私用截圖。

此輪沒有新增亂數規則或亂數比較點，只重播固定起始存檔及已記錄輸入。
Fortify真實來源偏移仍未知，母語校閱、其他欄位、設定列正式切換、完整五語、HD及新交付仍待完成。
不增加來源普查shown，不把既有版本重新標為五語或HD完成。
