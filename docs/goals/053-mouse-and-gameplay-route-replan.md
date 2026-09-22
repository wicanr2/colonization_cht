# 目標 053：釐清滑鼠事件並重啟中文化主路徑

狀態：completed<br>
日期：2026-09-22<br>
對應 Issue：[Issue #25](https://github.com/wicanr2/colonization_cht/issues/25)<br>
前置證據：[目標 034](034-opening-post-composite-enter-probe.md)、[目標 041](041-mouse-producer-state-gate-dataflow.md)、[目標 046](046-opening-click-nonzero-downstream-dataflow.md)、[目標 048](048-viceroy-direct-entry-stall-diagnostic.md)

## 目的與更正

先前把下一個滑鼠座標交由使用者選擇，混淆了「玩家偏好」與「原版程式如何消費輸入」兩種問題。
現有證據僅確認完整開場畫面的 `(160,100)` 左鍵令 `OPENING.EXE` 走向 `0x6C` 退出；
`0924:0588` 將 `int 33h AX=0003` 回傳的按鍵狀態併入布林值，尚無證據顯示此分支依賴座標。
目標 052 的紅色標記是既有實驗位置，不代表可點擊控制項，也不能據此要求使用者避開該點。

本輪先證明滑鼠在開場的實際作用，再確認原版如何進入有文字輸出的遊戲畫面。這是可調查的事實，
不需要使用者猜座標；原版遊戲、規則、資料及存檔均不改動。

## 執行順序與退出條件

1. **滑鼠因果對照**：以固定檔案雜湊、dosgolem commit 與同一完整開場 state，對照無輸入、
   `(160,100)` 及一個與其明顯分離的位置之單次左鍵；保持注入時機與按鍵歷程相同。
   記錄第一個分歧、座標欄位、離開碼與畫面。若結果相同，只能在此 state／這些位置判定
   「未觀測到座標依賴」，不可宣稱所有畫面都是任意點擊。
2. **正常啟動鏈**：查證 DOS 原版從開場結束到實際遊戲的啟動方式。dosgolem 為正式收據來源；
   DOSBox-X 可用來觀察缺失的父程序、命令列、環境或服務，但必須標示輔助基準，不能替代
   dosgolem 的同狀態重播。`VICEROY.EXE` direct-entry 自迴圈不得充當正常路徑。
3. **缺口處理**：若遇到 dosgolem 通用能力缺口，先提供固定輸入、首個分歧、最小重現與
   DRAFT 規格；審查為 READY 後才在 `workplace/dosgolem` 隔離副本實作，最後由 dosgolem 重生收據。
4. **文字前沿**：實際遊戲畫面可達後，將真實輸出事件交給 Issue #5、#6；先做一則訊息的
   端到端中文顯示（Issue #26），再擴展文字清冊與覆蓋。靜態圖像普查（Issue #8、#9）可獨立進行，
   不再以開場標籤的安全矩形研究阻住動態路徑。

完成本目標的判準是滑鼠作用有可重播的有限結論，且取得 dosgolem 正常遊戲畫面收據，
或具體記錄阻止它的第一個通用能力缺口與下一個規格閘門。不能僅憑計畫完成而勾選。

## 中文化後續門檻

本輪已定位的通用缺口與修正閘門見 [規格 006：BIOS 馬達倒數](../spec/006-bios-motor-timeout.md)。
主選單滑鼠服務見 [規格 007：滑鼠回呼交換](../spec/007-mouse-handler-exchange.md)。
快照重播見 [規格 008：滑鼠快照](../spec/008-mouse-snapshot.md)。
滑鼠對照工具為 `tools/probe_opening_mouse.py`；DOSBox-X 輔助入口為
`tools/dosbox_probe.sh` 與 `tools/dosbox_probe.conf`。

動態文本採「真實輸出事件 → 來源鍵 DRAFT → 證據審查／READY → 一則中文顯示 →
英文與缺譯回退 → 正常路徑驗證」，再逐類擴展。靜態文字另需來源、可見存續、可逆背景與安全矩形。
字型、術語及完成範圍須待真實原型呈現後由使用者決定；公開與授權仍待獨立確認。

## 驗收結果（2026-09-22）

- 舊無參數開場快照的三個左鍵位置 `(160,100)`、`(16,16)`、`(300,180)` 產生完全相同的
  指令軌跡，於 #5,511,836 以 `0x6C` 結束；無輸入／只移動留在開場。只對這個狀態成立。
- 原版批次檔實際使用 `opening -g`。先前省略 `-g` 的分支不能代替正常遊戲啟動鏈。
- 依規格 006–008 修正通用平台能力後，由 `OPENING.EXE -g` 冷啟動到主選單，
  點選「新世界」進入難度畫面；沒有直接啟動 VICEROY 或改寫原版記憶體／檔案。
- 選單快照重播與連續執行的畫面索引 SHA-256 均為
  `e491233e037fa69b0498fc9415688b4491124d0ae687f45b17b46e8bf57b6446`，色盤均為
  `7c025d5be0f0851b285fe8d7fce2f4cfa44a28d0da3ca0d74eecfb3276c373c7`。
- 無輸入控制組留在主選單，索引 SHA-256
  `915991ed8898747e7c635fee6596e64e9f6aee7928b021b4a35b945453e7241f`。
- 隔離 dosgolem `22664265ea7d55ea8706448149908c79d3f0897b` 通過 `go test ./...`。
  正式收據為 `workplace/reports/goal053-route.json`，圖片及原始 trace 不納入 Git。

## 可重現入口

以下命令在本專案根目錄執行。Docker 控制需主機權限；不在主機執行 Python／Go。
每個掛載先驗證存在；原版與程式唯讀，只有快取及輸出可寫。

```sh
test -d workplace/dosgolem && test -d workplace/gocache &&
test -d workplace/reports && test -d tools &&
test -d "Sid Meier's Colonization (1994)/SMColoni/COLONIZE" &&
timeout 240 docker run --rm --network none --memory 2g --cpus 2 --pids-limit 256 \
  --user "$(id -u):$(id -g)" -e GOCACHE=/cache \
  -v "$PWD/workplace/dosgolem:/dosgolem:ro" \
  -v "$PWD/workplace/gocache:/cache" \
  -v "$PWD/workplace/reports:/out" \
  -v "$PWD/tools:/tools:ro" \
  -v "$PWD/Sid Meier's Colonization (1994)/SMColoni/COLONIZE:/game:ro" \
  colonization-research:20260920-r2 python3 /tools/probe_gameplay_route.py
```

`probe_gameplay_route.py` 驗證三份原版雜湊、拒絕髒的執行器工作樹，並將實際 commit、命令、
快照雜湊與輸出雜湊寫入收據。三個分支均停在 #40,000,001；輸入為 #3M Enter、
#12,000,001 開場左鍵，及 #30,000,001 主選單 `(128,110)` 左鍵（320×200 邏輯座標）。
使用預設決定性虛擬時間；本輪未測試遊戲亂數或生成地圖，沒有宣稱 RND 對拍。
快照只在無 pending／active 回呼的安全時點保存；舊 DOS v3 明確拒絕。
缺少合法原版／歷史輸入時，工具以 `SKIP` 與退出碼 77 明確跳過，不產生通過宣稱。

歷史滑鼠對照可用相同容器與掛載，另加
`-v "$PWD/workplace/reports:/inputs:ro"`，改執行 `python3 /tools/probe_opening_mouse.py`。
它從隔離 Git 儲存庫匯出 `1435f17` 到容器暫存目錄，確保舊快照配原始執行器。

累積平台補丁為 `tools/dosgolem-platform-fixes.patch`，從原始上游
`d9c0c27ca9af8239c7e96272a7165e03d7da04bf` 套用可重建本輪完整源碼，樹雜湊
`2189d114214649c6f60074f70d853ff5bd04af0d`。含先前 SBPro／MCB 及本輪修正，不含原版資產。
只可在新的隔離副本確認基底後執行 `git apply --check` 再套用；不得重套到現有副本或修改共用上游。

## 下一步

啟動與滑鼠阻塞已解除，Issue #25 可關閉。下一個工作入口是
[目標 054：主選單文字來源](054-main-menu-text-provenance.md)／Issue #5。
本輪不宣稱動態文字已定位、已中文化或完整可玩。
