# 四語Noto六列命令欄字模原型

狀態：DRAFT。只生成私用圖集與消費端探針，不授權正式前端或完整語言包。
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
