# Cubic 11 字型來源與本機使用界線

使用者 2026-09-26 決定全案維持「俐方體11號」（Cubic 11，見[目標148](../docs/goals/148-font-terms-scope-decisions.md)）。本專案的中文畫面採此字型；字型檔與烘製字模**不放進 Git**。使用者只確認過部分畫面的視覺方向；
每個覆蓋欄位仍須依原版墨跡與安全矩形另量字級，不能把 24px
當成全域規則。

## 固定輸入

- 字型檔名：`Cubic_11.ttf`
- SHA-256：`8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`
- 檔內名稱版本：`Version 1.430`；此份字型的 Unicode 對照表含 10,250 個字形碼點。
- 本機已核對的兩個唯讀來源：
  - `/home/anr2/cht/tmp/gocache-104/mod/github.com/hajimehoshi/bitmapfont/v4@v4.1.0/internal/cubic11/Cubic_11.ttf`
  - `/home/anr2/cht/psychic-war/workplace/font-cmp/Cubic_11.ttf`
- 可重取的版本入口：Go 模組
  [`github.com/hajimehoshi/bitmapfont/v4@v4.1.0`](https://github.com/hajimehoshi/bitmapfont/tree/v4.1.0)，
  檔案位於 `internal/cubic11/Cubic_11.ttf`。取得模組後仍須驗證
  上述 SHA-256；同名但指紋不同即停止，不以近似字型代替。

原始作者的[字型專案](https://github.com/ACh-K/Cubic-11)與
[OFL 授權全文](https://github.com/ACh-K/Cubic-11/blob/main/OFL.txt)
說明字型採 SIL Open Font License 1.1；`bitmapfont` 模組的
Apache-2.0 程式碼授權**不能**取代字型本身的授權。

## 發行包中的字形

依 Issue #15 的發布決定（2026-09-27），發行包收錄以本字型烘製的字模（Alpha 遮罩與字元圖集，
不含 TTF 字型檔），並隨包附上字型授權全文 `LICENSES/Cubic-11-OFL.txt`。儲存庫中的
[`Cubic-11-OFL.txt`](Cubic-11-OFL.txt) 取自原作者儲存庫 `main` 分支的 `OFL.txt`
（2026-09-27 取得，SHA-256 `2b6e5938e5cffa0b9e183bd05f8c363e174e7ebed1a0556e2855fd1707fa2188`），
內含 Cubic 11 與其所依據的 JF Dot M+H 12、M+ BITMAP FONTS 聲明及 OFL 條文。字型檔與烘製
字模仍不加入 Git。

## 十七欄本機重烘入口

[目標103](../docs/goals/103-font-rebuild-and-mask-parity.md)已在本機以
固定原始 TTF、合法 DOS 版與兩份真 TSV 重烘現行十七欄字模：
十五欄沿用 [`tools/bake_goal084_fonts.sh`](../tools/bake_goal084_fonts.sh)，
第一張旗卡兩欄使用
[`tools/bake_nation_card_a_from_font.py`](../tools/bake_nation_card_a_from_font.py)。
後者**直接烘製**，不把目標088的舊原型字模當輸入。獨立
[`tools/verify_goal103_font_rebuild.py`](../tools/verify_goal103_font_rebuild.py)
對照歷史已驗字模：十五欄整份 JSON 逐位元組相同；旗卡
「英格蘭：」21px／「移民」25px 的 Alpha bytes 逐位元組相同。
正反例見 [`tools/test_goal103_font_rebuild.py`](../tools/test_goal103_font_rebuild.py)。

容器內將專案掛為 `/repo` 可寫、合法原版 `COLONIZE` 目錄掛為
`/game` 唯讀、上述 TTF 所在**目錄**掛為 `/font` 唯讀，先驗證
三個 host 來源存在且型態正確，再以目前 UID/GID、`--rm`、
`--network none` 與 CPU／記憶體／PID 上限執行。使用本機已驗
`rich2-py:latest`（映像 ID
`sha256:e5c73862da40d1e0c26d9d5f6a62491c75ddfe8ada5c77677e1e445f13d85a71`；
Python 3.12.13、Pillow 12.3.0、FreeType 2.14.3）。在容器中：

```sh
mkdir /repo/workplace/reports/goal103-replay-001
COLONIZATION_GOAL084_FONT_OUT=/repo/workplace/reports/goal103-replay-001 \
  bash /repo/tools/bake_goal084_fonts.sh
python3 /repo/tools/bake_nation_card_a_from_font.py \
  --catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --game /game --font /font/Cubic_11.ttf \
  --output /repo/workplace/reports/goal103-replay-001
python3 /repo/tools/verify_goal103_font_rebuild.py \
  --game /game --font /font/Cubic_11.ttf \
  --catalog /repo/text/draft.zh-Hant.tsv \
  --card-catalog /repo/text/nation-card-fragments.zh-Hant.tsv \
  --new /repo/workplace/reports/goal103-replay-001 \
  --old-standard /repo/workplace/reports/goal096-fonts-verified \
  --old-card /repo/workplace/reports/goal099-card-fonts \
  --receipt /repo/workplace/reports/goal103-replay-001.verify.json
```

範例中的 `goal103-replay-001` 必須改成尚不存在的工作目錄名稱；既有烘製腳本拒絕
覆寫其中的 JSON。最後兩個 `--old-*` 是本機歷史對拍基準，
**生成十七欄不依賴它們**；缺少歷史基準時可重烘，但不能宣稱
新舊位元組對拍通過。Python／Pillow 映像目前只有本機固定 ID，
尚無專案內獨立可重建來源；其他機器需取得同 SHA 字型及相容
工具環境後重新驗證，不能把這輪結果寫成無外部依賴的公開包。

目標102的八頁量測入口為
[`tools/preview_goal102_nation_intro.py`](../tools/preview_goal102_nation_intro.py)；
原版畫素與原型輸出留在忽略的 `workplace/`，字型只從上述
本機外部來源唯讀掛載；
私有對照截圖只供版面審查，不是正式遊戲畫面或散布許可。
