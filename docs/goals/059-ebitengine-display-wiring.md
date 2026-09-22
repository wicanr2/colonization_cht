# 目標059：Ebitengine畫面接線

狀態：completed（有限視窗接線；正式玩家版未完成）<br>
日期：2026-09-22<br>
Issue：[#26](https://github.com/wicanr2/colonization_cht/issues/26)

## 起點與範圍

[目標058](058-translation-corpus-and-player-window.md)已證明Ebitengine真視窗可顯示五列中文，
並用原生DOS滑鼠進入難度畫面。但當時組裝器靠字串替換改寫無頭測試程式，來源稍變就需
重新猜接點。本輪依使用者指定保留Ebitengine作為畫面與輸入前端，把接線改成明確Go介面。
不新增原版鍵、翻譯、靜態圖覆蓋、規則、存檔或發行包。

## 工作與驗收

- `tools/live_menu.go`提供可選的每幀RGBA接收點與視窗runner註冊點；單檔無頭建置保留。
  `tools/window_prototype.go`註冊Ebitengine實作，`--window`才啟動真視窗；未連結時拒絕。
- `tools/build_window_prototype.py`仍驗固定SHA，但只原樣複製Go來源，不改寫測試排程。
  合法原版、字模與共用專案快取只讀，輸出只在本案忽略的`workplace`。
- `tools/probe_window_prototype.sh`接受本輪獨立前綴；
  `tools/verify_window_prototype.py`用相同前綴核對真視窗圖片與同輸入三組狀態。

Docker內Ebitengine編譯及座標／三鍵釋放單元測試通過；單獨無頭建置成功，
要求未連結視窗時以退出碼2失敗即關閉。真Xvfb視窗九筆輸入從冷啟動到難度頁，
中文、同輸入中文重播與英文無hook控制於100,000,000步原版狀態一致：606幀、
5213虛擬tick、1,395,189,090 CPU cycles，完整RAM SHA-256
`c6588ff4781df0f05dc255f42c37422b11cd5e2fdd89d43a854dd691b366ce65`。
兩張真視窗截圖逐像素對照通過。收據在`workplace/reports/goal059-ebiten-receipt.json`；
步號依每輪X輸入而定，不能拿不同輸入的RAM雜湊作產品差異。

## 保留缺口

中文實際顯示仍只限已驗證五列，189筆譯稿不是189筆畫面覆蓋。真實失焦／關窗、
一般鍵盤、音訊、存讀檔、牆鐘速度、難度頁文字覆蓋與完整遊玩均未驗證；
[規格013](../spec/013-window-prototype.md)仍是限定原型的READY，不宣稱正式前端CONFORMED。
此輪曾先用舊預設前綴重跑，覆寫被忽略的本機目標058收據；隨即改成可指定前綴並以
`goal059-ebiten`獨立重跑，歷史數值保留於規格013，避免將兩輪輸入步號混稱同一收據。
