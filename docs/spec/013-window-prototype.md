# 規格 013：可撤回 Linux 視窗原型

狀態：READY（真視窗與滑鼠已驗；失焦、關窗及正式玩家版尚未驗）<br>
日期：2026-09-22<br>
入口：[目標058](../goals/058-translation-corpus-and-player-window.md)；Issue #26。承接[規格012](012-five-menu-lines.md)。

## 證據與限界

confirmed：隔離 dosgolem 的 `internal/dos/bios.go:593–617`，MoveMouse 接受
邏輯像素並自行處理 DOS 比例；PressMouse／ReleaseMouse 的 0/1/2 是左／右／中鍵。
既有正常路徑已用這三個 API 點新世界至難度。根公開型別別名可直接使用，不缺平台功能。
Ebitengine v2.9.9 的本機原始碼提供 CursorPosition、IsFocused、IsMouseButtonPressed、
IsWindowBeingClosed、SetWindowClosingHandled。沿用既有 psychicwar-go-ebiten 映像，
只讀另一專案模組快取，不改其程式或時鐘。

## 窄契約

- 原型視窗固定1280×800，邏輯畫布亦同；原版為320×200。座標先驗證0≤x<1280、
  0≤y<800，再整除4，不把負數轉unsigned；視窗外不移動／按下，但必須釋放既有按鍵。
- 滑鼠狀態變更逐項轉原生DOS事件，不轉鍵盤或直接呼叫遊戲常式。
  失焦釋放已按下的滑鼠；不自動存檔，不修改原版退出規則。
- 鍵盤原型只支援此次冷啟動所需Enter，一次按下送一筆既有PushKey；其他按鍵明列未支援。
- Machine.Step沿用本案預設虛擬時鐘；每次視窗更新只分批執行固定數量指令，
  不設定其他專案的cycles/ms、RunCycles或忙等修補。此節奏不是正式效能／實機速度承諾。
- 視窗輸入與繪圖在同一更新執行緒，指令觀測保持唯讀；Draw只顯示獨立RGBA副本。
- Ebitengine前端透過`frontendRunner`與`frontendFrameSink`兩個明確的Go註冊點接入；
  單獨建置原有無頭驗證器仍不依賴視窗。組裝器以固定SHA驗證`tools/live_menu.go`，
  只複製檔案到ignored workplace，不再改寫Go原始碼或複製第二份位址／譯文適配器。
- 每筆輸入記錄當下Step、類別、座標／按鍵；支援冷啟動逐指令重播同一收據。
  英文無hook控制組與中文組須在相同輸入／終點達到相同CPU、RAM、原圖、虛擬時間。
- 原型有明示指令上限，或視窗關閉退出；關閉不代表原版遊戲退出／存檔。
  原版／字模唯讀掛載。截圖、執行輸入及記憶體僅本機保存。

## 驗收與停止線

Docker／Xvfb／xdotool 的真實視窗輸入須冷啟動點新世界至難度；保留真正視窗截圖，
不得以PNG寫檔冒充視窗顯示。測座標邊界、釋放和重播；限制為Linux、Enter與滑鼠原型，
不宣稱完整鍵盤、音訊、存讀檔、速度調校或可完整遊玩。

## READY 審查

已核對公開API、本機固定v2.9.9來源及規格009–012的既有事件適配。
本輪先保存DRAFT再提升READY，只授權上述有限原型；組裝器綁定來源SHA，
任一來源變動即拒絕。目標059將原先的字串替換接線改成明確Go註冊，
同輸入畫面與狀態對拍通過；正式前端生命週期及更多鍵盤仍需後續工作。

## 原型與重跑入口

- [組裝器](../../tools/build_window_prototype.py)：固定`live_menu.go` SHA-256
  `c7d208aafb0fba6522799ddeaffc1b0df633419e959db85be27fb488b8aef5e4`，
  原樣複製至`workplace/reports/window-prototype`，不可當成正式共用適配器。
- [視窗程式](../../tools/window_prototype.go)與[座標／釋放測試](../../tools/window_prototype_test.go)。
- [Xvfb流程](../../tools/probe_window_prototype.sh)：外部X輸入，無遊戲記憶體注入。
- [獨立驗收](../../tools/verify_window_prototype.py)：三組完整狀態相同，兩張真視窗截圖逐像素對照。

以下皆為容器內命令；主機不得直接執行。容器使用`--rm --network none`、目前UID/GID、
`--memory 2g --cpus 2 --pids-limit 256`及外層120秒建置／300秒GUI逾時。
每個掛載來源先核對存在及形態，只有`/out`、`/app`建置產物、`/cache`可寫。
`/repo`是本案唯讀；`/reference`是psychic-war唯讀；`/dosgolem`是本案隔離副本唯讀；
`/gomodcache`為psychic-war/workplace/gomodcache唯讀；`/game`為固定DOS原始目錄唯讀。

```sh
# colonization-research:20260920-r2；/out=本案workplace/reports。
python3 /repo/tools/build_window_prototype.py
# psychicwar-go-ebiten:latest；/app=/out/window-prototype，工作目錄/app。
# 環境：GOCACHE=/cache GOMODCACHE=/gomodcache GOTOOLCHAIN=local GOPROXY=off
go build -o window .
xvfb-run -a go test ./...
# GUI容器要以sh包住xvfb-run並回收；不可讓xvfb-run成為PID1而等不到啟動信號。
sh -c 'xvfb-run -a -s "-screen 0 1280x800x24 -nolisten tcp" bash /repo/tools/probe_window_prototype.sh; result=$?; exit "$result"'
# rich2-py:latest
python3 /repo/tools/verify_window_prototype.py
```

`window --window`是固定指令上限的Ebitengine原型；未加`--window`保留原有無頭排程。
直接啟動參數見Xvfb流程，只有Enter、滑鼠及關窗，
沒有加入F鍵語言切換等可能占用原版按鍵的新產品設計。整局遊玩、存檔、音訊及正式節奏皆未交付。

## 有限收據與未驗項目

2026-09-22：最終來源`window_prototype.go` SHA-256
`16b6993415dee6c1c41c8ba9ebc602f123dd284e006fc845027d0d2cc7ba88ef`；
本機二進位`da727de9a0193c05412556ecc27add80f30a5736d45933ceb44cb02afefa466d`。
既有映像`psychicwar-go-ebiten:latest`，Go1.24.13、Ebitengine2.9.9、隔離dosgolem
`9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；不涉及反組譯位址變更。

confirmed：Xvfb真實視窗從冷啟動收到9筆輸入，Enter在3,800,000步，新世界按下在
28,200,000步、放開在29,000,000步，移開在29,800,000步；正常進入原版難度畫面。
真實視窗、同輸入中文重播、無指令hook／無中文合成的英文控制，終點100,000,000步
的CPU、完整RAM、原版indexed／palette、虛擬時間全部相同：606 frames、5213 ticks、
1,395,189,090 cycles，RAM SHA-256
`c6588ff4781df0f05dc255f42c37422b11cd5e2fdd89d43a854dd691b366ce65`。
各次新的GUI操作可能落在不同步號，不能拿不同輸入收據的RAM差異判產品缺陷。

兩張`import -window`真實視窗截圖均1280×800：
`workplace/reports/goal058-window.menu.png`與目標057清晰五列圖逐像素相同，
`goal058-window.difficulty.png`與同路徑最終原版圖逐像素相同；代理已目視。
獨立驗收收據為`goal058-window-receipt.json`，輸入為`goal058-window.inputs.json`，
三組原始收據為`goal058-window{,-replay,-control}.json`。五列均有實際OnFrame中文命中。

座標邊界與三鍵釋放單元測試通過；**尚未驗真實失焦／關窗事件**，規格保持READY，
不把此原型提升為正式前端CONFORMED。原型只支援Enter與滑鼠，尚無一般鍵盤、
中文切換操作、存讀檔、音訊、發行包或牆鐘速度驗收。
已確認無相關Docker容器殘留，輸出UID/GID為1000:1000，無root-owned或異常.md目錄。

環境勘誤：第一次讓xvfb-run成為Docker PID1導致啟動信號等待；改用外層sh持有並回收。
第二次status檔尚未生成時腳本set-e提前退出；修正為缺檔等待。兩者都是環境／測試腳本，
不是遊戲缺陷；修正後同容器／命令乾淨重跑通過，未改原版或放寬中文守門。

## 目標059：Ebitengine明確接線

confirmed：在`tools/live_menu.go`明確註冊視窗runner與每幀RGBA接收點後，
`tools/build_window_prototype.py`不再搜尋／替換Go測試排程文字，只核驗固定來源SHA並複製。
無頭單檔仍可獨立編譯；若要求`--window`卻未連結Ebitengine，明確以退出碼2拒絕。
此改動不新增原版文字鍵、覆蓋區或遊戲行為；文字仍只在已驗證五列疊加。

以獨立`goal059-ebiten`收據在真Xvfb視窗重跑：九筆輸入進難度畫面，中文重播與英文
無hook控制於100,000,000步終點的CPU、完整RAM、原始索引畫面、色盤及虛擬時間相同；
606幀、5213 ticks、1,395,189,090 cycles，RAM SHA-256
`c6588ff4781df0f05dc255f42c37422b11cd5e2fdd89d43a854dd691b366ce65`。
兩張真視窗截圖與基準逐像素相同。參見[目標059](../goals/059-ebitengine-display-wiring.md)。
重跑時設定`COLONIZATION_WINDOW_OUT=/out/goal059-ebiten`，驗收器加
`--prefix goal059-ebiten`；不得再覆寫目標058原始本機收據。前一次未改前綴的
初次重跑曾覆寫本機目標058檔，故舊收據的數值仍以本規格上節歷史記錄為準。
真實失焦／關窗及完整玩家版未驗，規格狀態維持READY。
