# 目標 030：`OPENBORD.PIK` 取樣資料流的可視矩形與文字存在檢查

狀態：completed（確認為非文字裝飾邊框；Issue #8 保持進行中）<br>
日期：2026-09-21<br>
對應 Issue：[Issue #8](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 029](029-openingbord-canvas-survival-to-frame-copy.md)

## 目的

目標 029 已確認 672 次 `OPENBORD.PIK` 原始緩衝區→canvas 內容變更存續，且位於完整的 320×24 範圍內，
並在一次 `REP MOVSW` 搬至 A000 VRAM。本輪只在同一確定步數保存非公開的 indexed frame 與調色盤、在 Docker
中轉成檢視用畫面，交叉確認該範圍的可視矩形及是否**明顯**含有靜態文字。它不是資產解碼或 OCR，也不對模糊圖樣
強作文字判讀。

## 執行項目

1. 以目標 029 的固定 post-window state 重播，在 #5,464,536（24 組 canvas→A000 copy 完成後）保存 indexed
   320×200 frame 與同時的 VGA palette；保留步數、state、輸入雜湊與 dosgolem commit。
2. 只用容器內可重現的標準函式庫轉譯 indexed frame＋palette 成檢視 PNG，輸出仍在 `workplace/reports/`；不將
   原版像素、調色盤、截圖或轉檔產物加入 Git、Issue、Release 或其他公開端點。
3. 以目標 029 的已確認 canvas／VRAM 對應，檢查螢幕的 `(0,0)–(319,23)` 是否為與資料流一致的可視範圍；
   對文字存在只做 `confirmed`／`unknown` 二分，模糊、裝飾性、非文字或不可重現觀感一律 `unknown`。
4. 回填可重現命令、雜湊、位址空間、視覺判準與推論等級至研究紀錄、現況、工作清單、Issue #8、工作歷程與 Git。
   若沒有已確認文字，不建立 DRAFT／READY 規格、中文覆蓋原型或使用者決策問題。

## 結果

probe 的 `-shots` callback 在指定步數達到 `-steps` 上限後不會執行，因此以 `-steps 5464537` 要求
`#5,464,536` 的畫面；收據仍是 copy 完成後、下一道指令執行前的相同 state。產出的 indexed frame 為
320×200、64,000 bytes，palette 為 768 bytes。從 frame 開頭取得 7,680 bytes 後，以同一 palette 轉成
320×24 PNG，正好對應目標 029 已確認的 `1C430h–1E22Fh`／A000 首 7,680 bytes 範圍。

該精確 crop 是一條連續、重複的金色幾何裝飾邊框，沒有字元輪廓、字距、文字群組、可辨識字形或可讀文字。
結合範圍的已確認資料流，本輪將這個候選分類為 confirmed 的**非文字靜態裝飾**。這個結論只排除該 320×24
範圍作為文字覆蓋目標；它不判定 `OPENBORD.PIK` 的完整內容，也不排除其他 `.PIK`／`.SS` 候選含有文字。

完整畫面、palette、crop 與 PNG 都只在 `workplace/reports/`；未加入 Git 或對外端點。沒有文字存在與安全矩形，
故未建立 DRAFT／READY、原型、譯文、字型或使用者決策問題。

## 停止線

- 不以檔名、畫面上有圖、字形相似、色彩分布或單一截圖推定文字存在；不 OCR、人工臆測轉錄、解碼資產或修改原版。
- 不把一個 step 的 VRAM frame 誤稱為穩定最終畫面；copy 後改寫、完整資產歸屬與中文安全矩形維持各自的證據門檻。
- 不將任何原版衍生 bytes、色盤、截圖或 PNG 加入 Git、GitHub Issue、Release、公開雲端或發行包。
- 文字存在與安全矩形未各自 confirmed 前，不建立 DRAFT／READY 規格、覆蓋原型、譯文或中文化實作。

## 退出條件

- [x] 固定 state 與 copy 完成步數有 indexed frame、palette、轉檢視 PNG 的雜湊收據，全部留在 `workplace/reports/`。
- [x] 320×24 的畫布／VRAM 對應與可視矩形有明確、可回查的確認或反證；不以視覺替代資料流。
- [x] 文字存在結論具明確判準；無法確認時明列 unknown，且不產生覆蓋規格／原型／決策。
- [x] 文件、Issue #8、Git、Docker 清理與權利邊界一致。
