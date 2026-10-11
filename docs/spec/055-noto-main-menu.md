# 主選單五列的四地區 Noto 字模

狀態：限定CONFORMED。2026-10-11先完成DRAFT量測及READY審查，再實作並通過下述五列驗收。

承接[規格012](012-five-menu-lines.md)的來源、呼叫、游標及撤銷守門。
使用者已選定四地區 Noto；本規格只改五列顯示，不改點擊區域、輸入或原版資料。
入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)。

## 固定輸入與量測

- `GAME.TXT` SHA-256：`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`。
- `VICEROY.EXE` SHA-256：`a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`。
- 原版索引畫面：目標186六列驗收的正常 GUI 輸入控制組，步數32835000，
  `noto-orders-formal-verify-20261011/replay-zh-Hant-control/run.cp-32835000.idx`，
  SHA-256 `559df11e83c1fb01e2d844a4379af6369e279bf4ea7b4b30c95cbf2d4062c4a1`。
- Noto Sans CJK Regular 2.004：SHA-256
  `b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`。
  地區 face 與授權入口見[字型來源](../../font/README.md)。

矩形為原版320×200的半開區間，墨跡色為254。下表在上述原版畫面重新計數，
與規格012相符，證據等級為 confirmed。位移是 `GAME.TXT` 檔案位移。

| 來源鍵尾碼 | 位移 | 長度 | 墨跡矩形 | 點數 | 安全矩形 |
|---|---|---|---|---|---|
| 0x000001B0 | 0x1b0 | 25 | [86,107,177,113] | 180 | [86,107,232,114] |
| 0x000001CB | 0x1cb | 23 | [86,115,169,121] | 163 | [86,115,232,122] |
| 0x000001E4 | 0x1e4 | 19 | [86,123,161,128] | 152 | [86,123,232,130] |
| 0x000001F9 | 0x1f9 | 9 | [86,131,121,136] | 77 | [86,131,232,138] |
| 0x00000204 | 0x204 | 17 | [86,139,145,145] | 112 | [86,139,232,146] |

## 候選與資料契約

各列各語獨立試14至28px。原版墨跡高度放大四倍為24、24、20、20、24px。
安全區584×28px，右及下各留4px，左上沿原版位置對齊，不加陰影。
完整文字以真正字形繪製，保留負 bearing 與基線以下墨跡，不依字格裁切。
在寬≤580、高≤24的候選中，選墨跡高度最接近該列原版高度者，同分選較大字級。
每列記錄候選、墨跡、基線與最長實際譯文。無候選時回原文並記錄。

四語各列獨立選出的字級均為24、24、20、20、24px，墨跡高度為24、24、20、20、24px。
裁切後基線距頂端依序21、21、18、18、21px。左上對齊原版墨跡，基線隨各列記錄定位。
各語五列墨跡寬度如下，沒有換行、截斷或缺字。私用樣張已檢查完整筆畫。

| 語言 | 各列墨跡寬度px |
|---|---|
| 繁中 | 192、168、97、79、118 |
| 簡中 | 191、167、97、80、119 |
| 日文 | 165、234、199、136、117 |
| 韓文 | 159、181、93、112、160 |

量測收據為`workplace/reports/goal186-display-hd/noto-menu-formal-atlas-20261011/bake-check.json`，
SHA-256 `9e17581d5f9e26788973c2f7a6e297d75c38fde4efee7e2827b83d6d549d1923`。
工具為`colonization-verification:20261007-runtime-r2`內Pillow9.4.0與FreeType2.12.1。
這些數值只適用此五列，不能外推到其他欄位。

譯文只讀既有完整 TSV。烘製器產生五列既有九欄格式的私用 TSV，
保留來源六欄。每列遮罩沿 `fontMask` 格式，另綁定基準及五列 TSV、
原版畫面、地區 face、授權、墨跡雜湊。不能把顯示譯文用作來源辨識或點擊路由。
未知地區、錯誤來源、重複／缺列、舊字型、錯誤字級、空白或越界遮罩，整組五列回原文。
既有版本、印字來源、畫面及游標守門仍需逐列通過；換場與重繪沿規格012撤銷。

## 驗收

烘製兩次逐位元組相同；實際四語 TSV 與遮罩載入、來源／地區／字級反例；
四語正常冷啟動、五列懸停、移開、開啟載入頁與返回主選單、切入新遊戲頁。
同輸入重播核對 CPU、RAM、VGA、DAC、WAV 與既有存檔；
輸出差異限五列安全區，錯誤地區組與原文組相同。其他欄位及六列命令欄不受影響。

## 重生與啟用入口

正式收據為`workplace/reports/goal186-display-hd/noto-menu-formal-check-20261011.json`，
SHA-256 `551ef86711d04879cb915c6bbed909317d1f6730dff93135f0ab6de4cae47a1f`。
四語40張正常GUI與16組四側重播通過；每語每列六個原版來源事件通過規格012守門。
五列懸停、移開、載入頁返回及切入新遊戲均由正常鍵鼠完成。
各次懸停82／82／82／82／80個實際原版游標像素保留，切場後五列撤銷。
差異只在五列安全矩形；CPU、完整RAM、VGA、DAC、輸入、WAV及原有存檔相同。
錯地區圖集整組五列回原文並逐列記錄，其他欄位維持既有顯示。

325項Go測試零skip、go vet通過，包含四語80個錯誤輸入及來源／幾何守門反例。
六列命令欄的既有真字模測試同時保留。45個烘製檔案及收據重生全同。
正式二進位SHA-256 `6078ddc2565860a6ba17b48ab64ff8fa269bf92b6b1206ddc4f6b95f51174d78`；
Go測試收據SHA-256 `b4024d677a90c9d6f1d7cd7cbb8e15372d1a960857898017db610ce879a19453`。
Go／GUI工具沿既有映像，dosgolem隔離副本為`82a14b266e1b5bc904e2d0fe507daf6bea41a013`，未修改。
日韓未經母語校閱；本輪不增加來源普查shown，不代表完整五語、設定切換、HD或新發行完成。

烘製使用上述固定Python映像；合法原版目錄唯讀掛為`/game`、專案唯讀掛為`/repo`，
只開放輸出父目錄寫入，設定目前UID/GID、無網路、資源上限及外層逾時。
所有掛載來源先確認存在；以下輸出名稱必須改成尚不存在的目錄。

```bash
python3 /repo/tools/bake_noto_menu.py \
  --game /game \
  --native-frame /repo/workplace/reports/goal186-display-hd/noto-orders-formal-verify-20261011/replay-zh-Hant-control/run.cp-32835000.idx \
  --noto /repo/workplace/reports/goal186-display-hd/font-candidates/NotoSansCJK-Regular.ttc \
  --license /repo/workplace/reports/goal186-display-hd/font-candidates/NotoSansCJK-LICENSE.txt \
  --output /repo/workplace/reports/goal186-display-hd/new-menu-atlas
```

缺原版畫面證據時停止，不以自製畫面代替。正式前端由
[既有組裝器](../../tools/build_window_prototype.py)組裝，Go1.26.7／Ebitengine2.9.9
容器`hr-go-ebiten:1.26.7-2.9.9-r1`內建置，dosgolem隔離副本唯讀掛為`/dosgolem`。
保留既有完整顯示參數與`--all-menu`，新增下列三參數才啟用此五列：

```text
--noto-menu-locale ja
--noto-menu-draft /repo/workplace/reports/goal186-display-hd/new-menu-atlas/draft.ja.tsv
--noto-menu-font-dir /repo/workplace/reports/goal186-display-hd/new-menu-atlas/ja
```

地區可改`zh-Hant`、`zh-Hans`、`ja`或`ko`，TSV及目錄須一起對應。
缺檔或混用時五列回原文並記錄`noto-menu-`原因；未提供參數沿既有顯示，
英文使用既有`--control`原版畫布。三參數只選啟動時的五列顯示，沒有完整五語或設定列切換。

正式測試須提供`TEST_NOTO_MENU_DIR`、`TEST_NOTO_ORDERS_DIR`、`TEST_GAME_ROOT`，
並沿規格054的音樂、英數及建造標題夾具，缺原版會明確skip，正式驗收不可有skip。
本機正常GUI驅動為`workplace/reports/goal186-display-hd/verify-noto-menu-formal-20261011.py`，
SHA-256 `3183024f15fa6ac8ae62f11be299bad2866033164b5a1a48fd48e8c966faac42`，
沿既有probe同步真實滑鼠、鍵盤與截圖。其`setup`、`gui <地區>`及
`replay <地區> <locale|control|default|invalid>`產生原始收據；只在`/out`掛新的私用目錄。
驗收時將同一收據目錄唯讀掛回`/out`，核對記錄中的絕對輸入路徑，再執行：

```bash
python3 /repo/tools/check_noto_menu.py \
  --reports /out \
  --build /repo/workplace/reports/goal186-display-hd/noto-menu-formal-build-20261011 \
  --atlas /repo/workplace/reports/goal186-display-hd/noto-menu-formal-atlas-20261011 \
  --repeat /repo/workplace/reports/goal186-display-hd/noto-menu-formal-atlas-20261011-repeat \
  --output /repo/workplace/reports/goal186-display-hd/new-menu-check.json
```
