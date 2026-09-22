# 目標071：地圖編輯器選單、過場標題與載入訊息譯稿

狀態：in_progress；日期：2026-09-22。對應 Issue [#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#10](https://github.com/wicanr2/colonization_cht/issues/10)、[#27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 範圍

本切片以既有單行候選 TSV 契約，建立44筆可追溯繁中草稿：

- `MAPMENU.TXT` 的28個地圖編輯器選單與說明入口；固定檔 SHA-256 為
  `6b5db279365974c5315c9da51ae9257d8fcac8b2669a56c08e65b7717869cd2d`。
- `WOODCUT.TXT` 的14個具語意的過場圖標題；固定檔 SHA-256 為
  `32c813604a57fada85c591d2dd5ed6d29486ca1b0273fce544e6dd5b6b6fc8d2`。
- `OPENING.TXT` 與 `CLOSING.TXT` 各一則載入訊息；固定檔 SHA-256 分別為
  `17b329d8241fb72a706488cb309668439448d78df5cccc75650620b702dafcc5` 與
  `99bfce33e69cb0290a53bd67dfec27c21e6cd6a84d55e024864039c100ccf512`。

這些皆是來源檔中獨立、無逗號的資料行；候選識別仍只是檔案位元組定位，不是正式執行期
訊息鍵。`MAPMENU.TXT` 的 `~` 熱鍵與 `#` 格式記號必須逐序保留。所有譯文為 `draft`，
不修改原版、遊戲規則、存檔或資料格式。

## 明確排除

- `OPENING.TXT`／`CLOSING.TXT` 的動畫、影格、座標與重複次數資料。
- `TRIBE.TXT` 的座標，以及各檔的作者註解、命令列與內部註記。
- `WOODCUT.TXT` 的 `woodcut 14` 至 `woodcut 16`：它們是意義未證實的佔位名稱，不能為湊數
  猜補翻譯。
- `NAMES.TXT` 剩餘232列複合資料：214列為名稱加數值規則欄位、18列為部族別名；它們不符合
  既有「整行即顯示候選」模型，須另行建立 DRAFT 欄位識別方案後才可處理。

## 工作與退出條件

1. 以既有單行 TSV 欄位新增44筆，保存固定原始檔 SHA、行首檔案位元組位移、行片段 SHA、
   長度、繁中草稿與來源限制註記；不得複製原文進程式碼或正式 runtime。
2. 建立器／驗證器必須失敗即關閉：拒絕重複候選、非行首定位、註解／指令、逗號複合列、
   未知來源或缺譯；`~` 熱鍵、`#` 格式記號、占位符與既有控制符號均逐序核對。
3. 在 Docker 用唯讀原版重跑44筆合成及全目錄來源驗證，預期主譯稿由324增至368筆；再以
   Cubic 11、24px 做字型覆蓋檢查。任何缺字、格式或來源不符都不得更新正式TSV。

本切片不建立 dosgolem 輸出事件、中文安全矩形、Ebitengine畫面或正常玩家路徑收據；
368筆主譯稿也不是全文翻譯或畫面中文化完成數。
