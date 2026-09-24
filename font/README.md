# Cubic 11 字型來源與本機使用界線

本專案目前的中文畫面原型採「俐方體11號」（Cubic 11），但**沒有把
字型檔或烘製字模放進 Git**。使用者只確認過部分畫面的視覺方向；
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
Apache-2.0 程式碼授權**不能**取代字型本身的授權。若將來要
散布字型或含其字形的可散布套件，應先核對實際版本、授權文件、
保留名稱與包內告知；本輪只在本機唯讀量測，不作發行決定。

目標102的八頁量測入口為
[`tools/preview_goal102_nation_intro.py`](../tools/preview_goal102_nation_intro.py)；
原版畫素、字型檔與原型輸出皆留在忽略的 `workplace/`，
私有對照截圖只供版面審查，不是正式遊戲畫面或散布許可。
