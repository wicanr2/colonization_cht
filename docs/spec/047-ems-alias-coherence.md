# 規格047：EMS 同頁映射一致性

狀態：限定 CONFORMED。入口為[目標185](../goals/185-player-experience.md)。範圍為 EMS 同頁映射、英國發現者新局及既有存檔回歸，不外推全部遊玩或三平台交付。

## 問題與證據

dosgolem 的 EMS 使用複製式分頁。同一個邏輯頁映射到不同實體頁時，各處內容可能分歧，之後寫回也可能覆蓋較新的內容。

| 等級 | 證據 |
|---|---|
| confirmed | 隔離 dosgolem `c5953b90a0fc76c57f8dbbe0555f7a85d3198fe8` 的合成測試重現三項失敗：第二映射沒有取得第一映射的最新內容、別名寫入不可見、重新映射覆蓋較新內容。測試沒有原版資料。 |
| confirmed | 新局 v7 追蹤顯示 handle 5 的邏輯頁 1 同時映射到實體頁 0、1；隨後實體頁 0 在邏輯頁 1、2 之間切換。 |
| confirmed | 第635057869步的 `D036:3C9D` 位於實體位址 `0xD3FFD`，當時三個位元組為零。後續跳入錯誤處理尾端，沒有有效堆疊框，最終 LEAVE／RETF 返回零位址。 |
| 假說 | EMS 別名內容分歧造成新局停止。通用契約缺口已重現，但尚未完成遊戲因果驗證。 |

工具為 `colonization-verification:20260930-r1`、Go 1.26.7。地址為 dosgolem 執行時 CS:IP 或實體記憶體，不是 EXE 檔案偏移。原版輸入雜湊及正常輸入見目標185。

本機證據位於 `workplace/reports/goal185-player-experience/`：`ems-alias-contract.log`、`trace-source/ems_alias_probe_test.go`、`ems-boundary-writes-v7.jsonl`、`before-copy-ring-v7.json`、`trace-exit-v7.json`。v7 終點記憶體 SHA-256 為 `21d7dbf83ae80b7bf06b9112e48a3b8e6bca68e3b1fb88694eb6740209b896a7`，與原文控制組一致。

可重生的合成測試保存於[tools/ems_alias_contract_test.go](../../tools/ems_alias_contract_test.go)。在驗證容器中複製到獨立暫存 Go module，以 `go.work` 指向 `/repo/workplace/dosgolem`，再執行 `go test -run TestGoal185EMSAliasContract -count=1 -v .`。正式副本預期三項 FAIL，不能把這項診斷當作現行矩陣的 PASS。

標準契約參照 [DOSBox-X 的 EMM_MapPage](https://github.com/joncampbell123/dosbox-x/blob/master/src/ints/ems.cpp)：相同 handle／邏輯頁的映射指向同一份後端頁。此處只借用公開 EMS 契約，不以 DOSBox-X 畫面代替 dosgolem 收據。

## 原型契約

- 邏輯頁以 handle 與頁號識別。不同實體頁映射到相同識別時，寫入任一處後，其他映射立即讀到相同內容。
- 建立第二映射時，必須取得目前映射中的最新內容。
- 換頁、存回映射表及釋放前的寫回不能以舊別名內容覆蓋較新的資料。
- 映射載入與客體寫入須分開處理，避免把新載入內容同步到舊映射。
- 通用實作不包含本遊戲的地址、handle、步數或檔名。遊戲專屬追蹤保留於本儲存庫。

## 下一閘門

先在隔離工作樹驗合成契約，再以凍結的新局正常輸入測試原型是否解除停止。若新局仍停，不將別名缺口稱為本次根因，也不加入正式路徑。

升 READY 前須補足機器寫入觀測、快照還原、跨頁存取、映射表與非別名路徑的邊界證據。正式驗收須包含新正常 GUI、中文／原文完整原版狀態、存讀檔與既有路徑回歸。只通過合成測試不能宣稱遊戲修復。

## READY 審查，2026-10-07

- 新合成契約與既有 EMS 測試通過。初版原型即時更新後端頁，違反 `EMSPages` 的既有延遲寫回介面；該版未採用。修正版只同步實體別名，建立新映射前才將目前映射寫回，原有延遲寫回測試保持有效。
- 跨頁 word 寫入、換到不同邏輯頁、四處同頁映射、保存／恢復映射表、全新機器與 DOS 的快照還原、重複 DOS 還原及 Close 清理均通過。監看由 DOS 實例持有，Install／LoadState 安裝，Close 移除；不將監看識別碼寫入快照格式。
- DOS、機器與 CPU 三套既有回歸及 `go vet` 通過。通用源碼沒有遊戲地址、步數、handle 或檔名。
- 修正版正常輸入重播到800000000步，CPU.Halted=false、DOS.Exited=false；畫面由第一段字幕前進到第二段。新正常 GUI 另已進入世界，1492年春季、1000$、輕帆船位置(49,20)、行動4。證據為 `newgame-ems-candidate-v3/` 及 `newgame-ems-gui-v3/gui.continue-11.png`。尚未以此宣稱正式修復或全部遊玩驗收通過。

公開 EMS 契約與獨立合成失敗已證實通用缺口，原型的單一機制改動也解除新局 CPU 停止。最早的記憶體碎片形成過程仍未完整逆向；正式修復不改配置容量、配置策略、原版指令、亂數、規則或存檔，也不忽略 HLT。

正式接入後，使用本輪新正常 GUI 的相同輸入比較原型與正式程式，並驗中文／原文／缺字模三側完整原版狀態、截圖、關窗與既有存檔回歸。通過後才追加限定 CONFORMED。

通用改動及測試保存於[補丁](../../tools/dosgolem-ems-alias-coherence.patch)，以隔離副本 `c5953b90a0fc76c57f8dbbe0555f7a85d3198fe8` 為基底。補丁包含通用規格198及其索引，不含本遊戲地址。正式收據由[檢查器](../../tools/check_goal185_ems_repair.py)核對；舊[遊玩檢查器](../../tools/check_goal185_playtest.py)保留歷史失敗收據，不以新結果改寫舊紀錄。

GUI 後續驗證沿[執行期 revision r2](../../tools/Dockerfile.verification-runtime-r2)恢復。原 `colonization-verification:20260930-r1` 與其鎖定 Go 基底在正式重播完成後已不存在；原因未查明。r2 只執行已驗二進位，使用 Debian Python 與同 ABI 的 Pillow，不代替原 Go 建置契約。

## 限定 CONFORMED，2026-10-07

隔離 dosgolem 提交為 `82a14b266e1b5bc904e2d0fe507daf6bea41a013`，未推送，shared dosgolem 未修改。正式組裝二進位 SHA-256 為 `f4042b3db4b808e8d768502b5a6b521dcfbf1e104b3e6cd59f60f3ee4fafa3e6`，Go 測試及 `go vet` 通過。

25 張新正常 GUI 與正式中文重播逐像素相同。中文、原文與缺字模三側所有取樣點 RAM／索引／色盤，以及終點完整 CPU／RAM／VGA、原始 WAV 相同；缺字模逐像素回原文。重播到1745600000步，終點記憶體 SHA-256 為 `8d4818ec34bb78f506955b827473e2168b640e9efe50fd910b2043ef29440f22`。這批 GUI 使用原型二進位，正式程式另錄真視窗 `ems-formal-gui/`，已進入世界並接受船隻移動；不能將原型二進位稱為正式二進位。

既有15張正常 GUI 的正式中文重播也逐像素相同，中文／原文終點 CPU／RAM／VGA、原始 WAV 與舊 GUI 全等，COLONY00／03逐位元組相同。原始COLONY03沒有改寫。新正式 GUI 的操作腳本誤把高海確認畫面命名為存檔畫面，沒有取得新的手動存檔成功收據；只記世界入口及移動，不採計這些命名。存檔回歸依既有正常存檔會話判定。

彙整為 `ems-repair-review-final.json`，由上述檢查器重生。沒有改原版輸入、規則、資料或存檔格式，沒有增加記憶體或忽略 HLT。舊v.1.0.2與三平台封包尚未收進本修復；Issue #53及#55～61保持未完成。
