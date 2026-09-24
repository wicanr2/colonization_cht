# 目標115：遊戲選項來源鏈訂正與可重播驗證

狀態：completed（限定來源鏈訂正與驗證；正式覆蓋未完成）；日期：2026-09-24。承接[目標114](114-game-options-print-buffer-dataflow.md)已建立但尚未交接的原版監看與獨立檢查器，對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)。本輪不新增同義 Issue，也不把草稿接入正式顯示。

## 問題與工作

先前目標113把印字緩衝監看的零筆寫入當作受限負證據；目標114追查發現 `WatchWrites` 同時只允許一個範圍，後設畫布監看覆蓋了前設緩衝監看。此輪須以固定原版與正常滑鼠開窗輸入，重跑修正後探針，核對緩衝寫入／讀取、格式化來源與高位址 RAM 候選。每項結論保留原版 `CS:IP`、20-bit 線性 RAM、檔案位移及指令步數的不同位址空間，未觀測的資料邊不能由相同字串猜補。

1. 先推送本目標與 `CONTEXT.md` 入口，保留既有未提交的114探針與檢查器，再執行 Docker-only 驗證。
2. 使雙次冷啟動、無監看控制與獨立正反例驗證通過；在原版缺失時明確 `SKIP 77`。若檢查器本身有錯，修正後重跑，不用薄弱斷言代替原版收據。
3. 將113的零筆監看原因追加勘誤；更新[規格027](../spec/027-game-options-window-draft.md)、`RESEARCH-LOG.md`、`CONTEXT.md`、`WORKLOG.md` 與唯一工作清單，區分已閉合與仍缺的來源邊。
4. 檢查本機輸出擁有權、原版素材版控邊界、Docker 殘留；推送私有儲存庫並更新、回讀既有 Issue。

## 退出條件與停止線

此輪至少要產生可重播的來源鏈訂正與獨立負例，不能直接宣稱九欄已正式中文化。即使原版印字來源已接近閉合，只要選取／反白、核取圖示、游標、ESC 離頁或中文字級仍未定案，規格027保持 DRAFT、正式顯示維持十七段。原版收據及畫素只留在已忽略的 `workplace/`。

## 本輪驗證結果

`tools/check_goal114_options_dataflow.py` 對固定原版、雙次冷啟動及無監看控制 PASS：150個可見字元有先前同址同值的原版印字緩衝寫入，九段高位址 RAM 共有142個原始正文 byte 的變更寫入；格式化來源134筆中有133筆直接配對，餘下一筆保持未知。兩組觀測收據 SHA-256 分別為 `182882984edff3167e3faad61a32ee71cacd489b8094780b818b1acaf1e6e960`、`e91b07baca88c207b3757ef363df53d8c2aba08d4c01fce70173fe97cd7f7036`，1,300M 原版索引畫面 SHA-256 `7093e83e87169f8eb15e733c3d69ec68afd5b78a5d304fa384819c987192a546`。`tools/test_goal114_options_dataflow.py` 正例與九項拒絕／缺原版 `SKIP 77` 通過。探針在隔離 dosgolem Go 模組內 `gofmt` 檢查與 `go build -p 1` 通過。`tools/prepare_goal113_options_preview.py` 不再把舊假陰性當成預覽必要條件。

本輪只提升已觀測的窄來源邊，不把原始檔案至最終畫面整條資料流冒稱完全證實；缺口及互動／版面閘門列於[規格027](../spec/027-game-options-window-draft.md)。
