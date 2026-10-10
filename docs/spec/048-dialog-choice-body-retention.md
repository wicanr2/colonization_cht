# 規格048：選項重繪時保留同框正文

狀態：限定CONFORMED。入口為[目標185](../goals/185-player-experience.md)。已驗SAILHOME正文、兩選項、重繪／懸停及正常取消；其他正文組未抽樣。

## 已有證據

- confirmed：現行程式已載入並命中 SAILHOME 正文。首次正文與選項同時啟用，選項稍後反覆重繪，正文因 `superseded-by-new-dialog` 撤銷；原版正文仍可見。問題不是缺譯或未載入模板。
- 正文執行時印字入口 `0D21:00C6`、線性 RAM175222；來源鍵 `GAME.TXT:@SAILHOME:0x00001B6F` 綁定 GAME.TXT SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`。
- 原型觀察使用 dosgolem `82a14b266e1b5bc904e2d0fe507daf6bea41a013`、Go1.26.7、Ebitengine2.9.9。地址是執行時 CS:IP／線性 RAM；鍵中的0x1B6F是檔案偏移，兩者分開記錄。
- 私用收據位於 `workplace/reports/goal185-player-experience/ems-formal-gui/`。首次正文與選項於759165000步啟用；選項重繪後，正文於769230000步撤銷。原版圖片、輸入與存檔不提交。

## 原型條件

新清單替換目前清單時，只在以下條件全部成立才保留前一正文：

1. 正文仍 active，與新清單安全區不重疊，原版正文安全區完整像素與啟用時的 `afterSafe` 快照相同。初次辨識時的 `optionBody` 可能尚未完成頁面同步，不能用它驗證後續保留。
2. 舊、新清單的來源身份、安全區、原文項目與順序完全相同。
3. 清單身份屬於該正文已核對的完整選項組；任何列的來源匹配不成立即拒絕。

保留只延續已驗證正文的覆蓋。首次正文／選項身份建立仍沿規格036的2M步守門，不擴張首次匹配時限，也不新增文本、字級、資料格式或原版行為。

## 字級與驗收

正式收據由[check_goal185_choice_retention.py](../../tools/check_goal185_choice_retention.py)核對，重生入口為目標185的私用證據根。

沿已命中的欄位：正文安全區[67,111,256,135]、選項[72,137,229,161]，目前候選30px。正式審查前補原版字高／基線、中文墨跡容納與最長現行譯文量測；不把30px外推到其他欄位。

原型需驗正文改印／過期、身份不同、清單缺列／錯序、安全區不同及未知選項拒絕。正常高海確認與懸停／選擇後，正文和選項都應保持中文；正常關框不得殘留。相同輸入的原版完整CPU／RAM／VGA、音訊及存檔不變，缺字模回原文。通過證據審查才升READY並接入正式來源。

## READY 審查，2026-10-08

原型的正文失效、原版像素改印、缺啟用快照、不同清單身份／安全區、缺列、錯序、不同正文組及未知選項全部拒絕。Go回歸與go vet通過。診斷確認初次 `optionBody` 尚未完成頁面同步，而 active的 `afterSafe` 與原版現畫布完整相同；修正只使用後者，不改首次2M步守門。

`retention-proof-v3/`同輸入完整CPU／RAM／VGA、原始WAV、存檔與舊GUI相同，四次重繪保留正文；新增差異只在正文safe[268,444,1024,540]內，其餘畫面不變，缺字模回原文。原型清冊 `sailhome-retention/private-review.json` SHA-256 `775f8199fe2ead58af6c8680deb620c92018163d665e366bb57cde69463a17fa`。

欄位原版两行墨跡為[69,114,234,123]與[69,124,239,133]，cap8、pitch10；中文沿本欄既有30px，保留規格035的30～20px容量候選及超界原文回退。現行SAILHOME正文無變數，最長現行譯文即本則，實際中文墨跡[275,448,990,476]，字高28、寬715，安全區756×96，左內距7／頂內距4。中文以既有正文頂端內距排版，原版兩行改成中文一行，沒有裁切。量測清冊 `sailhome-retention/font-review.json`，色盤依正式 `(v << 2) | (v >> 4)` 契約，不以猜測的縮放公式量測。

原型只授權保留已啟用正文，不增加文本、字模或來源匹配範圍。正式實作後需驗新正常高海GUI、選項反覆懸停與正常取消、關框無殘字及三側同狀態；只有實際驗過的來源可限定CONFORMED。

## 限定CONFORMED，2026-10-08

正式來源為[dialog_overlay.go](../../tools/dialog_overlay.go)的 `retainChoiceBody` 及[live_menu.go](../../tools/live_menu.go)的一處保留條件；必要拒絕測試在[dialog_overlay_test.go](../../tools/dialog_overlay_test.go)。穩定組裝指紋同步，145項含子項Go及go vet通過。正式二進位 SHA-256 `fe58445ee2dd33a891c8ab2ec6ee509b2289bf86a83b67737d1de6cb7c5e4be0`。

`sailhome-formal-gui-v3/`正常主選單載入新局手動存檔、航行到高海、反覆懸停Yes／No／Yes及選No取消，共10張新同步GUI。正式中文與GUI逐像素相同；中文／原文／缺字模／舊版四側取樣RAM／索引／色盤、完整CPU／RAM／VGA、原始WAV及存檔全等。缺字模回原文，取消後與舊版逐像素相同，正文及選項於104940000步原版關框後撤銷。

正文在進入高海及三次懸停的整個矩形逐位元組相同。初次圖片判讀以為正文空白，直接像素核對、逐層觀測及矩形指紋全部否定此判斷，沒有改合成器或放寬容差。觀測收據 `retention-render-audit/`、`retention-stage-audit/`及`retention-pane-audit/`保留。

最初失敗輸入另由正式程式重生於 `retention-formal-old-route/`，全部截圖與已審原型逐像素相同，完整原版狀態、音訊與存檔相同；四次選項重繪不再撤銷仍可見正文。原始完整狀態RAM `a1a110d4876e1b937b58eaf377e125ac0b9e5a3b51b01266f8003ac8590693b6`，新GUI終點RAM `4066510b6c21f5a54d228ee0854a8eb996efb7f9e0944dd66676fd6e6ad4a7d7`，兩條輸入不混作同一狀態。

彙整 `sailhome-retention/formal-review.json` SHA-256 `8ee922c12521c2ef244354cbe0614d5f591f47595dda42a211bd9a26789ceefb`；由上列檢查器重生。普查完成數及歷史63列矩陣不增加；未推送或發行。
