# 四語完整字元圖集原型

狀態：DRAFT。只授權workplace原型，不加入正式語言切換。
入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)。

沿[規格053](053-language-catalogs.md)勘誤後的13表及2008筆完整譯稿，
使用[固定四地區Noto](../../font/README.md)建立既有對話框與字串圖集格式。
圖集包含30至12px各級及95個可列印ASCII；字級範圍只代表可用字形，
實際選字仍由每個欄位的原版字高、基線、安全區、最長文案與回退規格決定。
不得把30px、六列18px或主選單尺寸套用其他欄位。

每個字形沿規格054的完整墨跡字格，保留負左緣與超出字距的右緣，
核對有界獨立畫布與字格的Alpha完全相同。記錄字格增寬、字距及墨跡，
不能藉由裁切讓長字串通過。對話框及字串圖集分別綁定既有消費端要求的六表；
地區、來源、譯稿、字型、授權及烘製器另記錄於研究收據。

工具入口為[完整圖集原型](../../tools/preview_noto_runtime_atlas.py)。
於colonization-verification:20261007-runtime-r2容器執行，
--noto及--license指定字型來源頁的固定檔，--output指定新的workplace目錄。
原版、來源及字型唯讀；UID/GID與資源限制依AGENTS.md。
先核對Python3.11、Pillow9.4.0與FreeType2.12.1，不以另一版烘製結果替代。
圖集與組裝後13表只留本機；工具不啟動DOS、不修改正式前端。

正式化前仍須：

- 每欄依原版墨跡與安全區量測最長譯文及英數；多色、離屏與輸入欄分別處理。
- 全部13表、靜態文字字模及固定中文片段整包驗證，切換失敗保留目前設定。
- 從當次原版觀測重建翻譯快取，正常GUI切換不依賴原版重啟或重畫。
- 四語及英文正常路徑、同狀態、存讀檔與錯綁定回退通過。

完整字形與可載入圖集不增加普查shown，也不代表完整五語或HD完成。

## 2026-10-11完整字形與消費格式驗證

勘誤後各語2008筆，繁中／簡中／日文／韓文分別1834／1810／1387／906個字元，
均含95個ASCII。固定地區face的fc-query碼點與每字有界Alpha畫布核對通過。
每語19級共有120個需擴張的字格，最多比原字距增寬2px；未裁去負左緣或右側墨跡。

30px的參考字墨跡為[11,39)，全文非ASCII實際範圍為[9,39)，簡中更達[9,41)。
因此單一參考字不能證明整欄墨跡不超界；正式量測仍須用每欄實際全文及英數。
圖集保留這些完整墨跡，不靠裁切縮進參考字高。

從正式dialog_overlay.go直接抽出dialogFont與loadAtlasFonts，在固定Go1.26.7容器讀取
四語八圖集。152組字級的全部字距、字格高度、參考墨跡界及Alpha雜湊，
與獨立Python參考全同。缺字型、錯字型、錯授權、覆寫、區外輸出及缺父目錄六項拒絕通過，
沒有產生對應錯誤輸出。這些結果只驗證字形及既有格式，沒有原版執行或GUI信用。

另於新的repeat目錄乾淨重生，八圖集、52份文本及總收據共61檔逐位元組相同。

| 本機收據（相對workplace/reports/goal186-display-hd/） | SHA-256 |
|---|---|
| full-noto-atlas-prototype-20261011-r2/check.json | 0464084808f96b98597994dd781f8a7059694b28d038db017c5fe63722a443ca |
| full-noto-atlas-go-check-20261011/check.json | 1d9f30e622c15caff461612ea307a218fcf7a2909b524875c5832b8c34849763 |
| full-noto-atlas-go-check-20261011/negative-cli.json | ff1b79dc89264cb191c422b8fecf939c8913f0f510e68b959eb9f93a7c6bd3f1 |
| full-noto-atlas-go-check-20261011/rebuild.json | aa3890befa37f44867bbeb5ee64ab4a4b530a7a13f8d083f1dacebbcca86e291 |

首次2006筆原型因語料讀法錯誤停止，原目錄ABORTED.json明示不可套用，
未把它當作重生或驗收通過。現行原型使用勘誤後2008筆及新的r2目錄。

接續[規格058](058-dialog-source-identity.md)只修正來源辨識，Go語法樹核對loadAtlasFonts
與dialogFont宣告的位元組未改；完整圖集原型的來源綁定已重新審查。
本頁烘製收據仍保留當時工具與來源指紋，不改標成新版本重生，也不增加逐欄或GUI信用。
