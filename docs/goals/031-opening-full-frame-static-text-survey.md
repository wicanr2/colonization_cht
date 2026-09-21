# 目標 031：開場 composite frame 的完整 copy 與可見靜態文字普查

狀態：completed（建立兩筆可見候選；Issue #8 保持進行中）<br>
日期：2026-09-21<br>
對應 Issue：[Issue #8](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 030](030-openingbord-visible-rectangle-and-text-check.md)

## 目的

目標 030 已排除最先複製的頂端 `OPENBORD.PIK` 320×24 裝飾邊框。其餘實際載入的 `.SS` 候選仍可能位於同一
1C43 canvas 的其餘列。本輪只找出第一個完整 320×200 canvas→A000 copy 的確切終點，並在該同一 state 產生
僅限本機的 full-frame 檢視收據，普查**可見**靜態文字群組與其畫面矩形候選；不以畫面文字反向推定檔案來源。

## 執行項目

1. 從固定第 4,156,900 指令 state 監看完整可見畫布 `1C430h–2BE2Fh`（`DS=1C43` 的
   `0000h–F9FFh`，320×200×1 byte）的粒度 1 讀取，依步數、位址與
   `CS:IP` 分組，確認 `0557:009F`／`REP MOVSW` 是否以 200 組、每組 320 bytes 完整複製至 A000，並定位最後
   一組的 post-instruction step。
2. 以 callback 時序校正後的精確步數保存 indexed 320×200 frame 與 palette，再以
   `tools/render_indexed.go` 在 Docker 中轉為檢視 PNG；全部只留在 `workplace/reports/`。
3. 用已確認的 VRAM copy 作定位基礎，建立可見畫面中的靜態文字候選清冊：每個候選只記邏輯矩形、可見原文／
   無法辨識狀態、與「尚無資產來源」的明確界線。裝飾圖樣、模糊圖形或不能可靠辨識的區域一律不登錄為文字。
4. 回填雜湊、原始位址、copy 範圍、檢視判準與未知界線至研究紀錄、現況、工作清單、Issue #8、工作歷程與 Git；
   沒有單一候選的來源資料流與中文安全矩形前，不建立 DRAFT／READY 規格、覆蓋原型或譯文。

## 結果

完整 read monitor 共留下 172,140 筆，包含 copy 前的處理讀取及其後局部重畫；只篩選
`#5,464,375–#5,465,772`、`0557:00A1` 後，恰為 200 組、每組 320 bytes、共 64,000 bytes，連續從
`1C430h` 至 `2BE2Fh`。前一原始指令 `0557:009F` 是 `F3 A5`／`REP MOVSW`，而 200 個前置暫存器樣本的
`DI` 從 `0000h` 至 `F8C0h`，每列遞增 `0140h`。這是第一個完整 composite canvas→A000 copy；其後另有
132 列局部重畫，沒有混入本輪 frame。

在最後一列 copy 完成後的 #5,465,772 state，重生 indexed 320×200 frame、palette 與 PNG。以此**可視**收據
登錄兩筆靜態文字候選：

| 候選鍵 | 可視邏輯矩形（約略） | 原文狀態 | 已知／未知界線 |
| --- | --- | --- | --- |
| `opening-map-ocean-label` | `(53,49)–(174,61)` | 已辨識為 `OCEANVS OCCIDENTALIS` | confirmed 為可見靜態字；來源 `.PIK`／`.SS`、載入／繪製資料流、copy 後存續與中文安全矩形均 unknown。 |
| `opening-scroll-two-line-text` | `(148,123)–(208,146)` | confirmed 有兩行字形；原文未可靠辨識 | confirmed 為可見靜態字；來源、完整轉錄、copy 後存續與中文安全矩形均 unknown。 |

這兩個矩形是用於下一輪資料流追溯的畫面候選，不是安全矩形、資產矩形或覆蓋資格。沒有建立 DRAFT／READY、
中文覆蓋原型、譯文或字型。

## 停止線

- 不因全畫面可見某段英文就假定它來自任一 `.PIK`／`.SS`；每個資產來源必須在後續獨立閉合。
- 不 OCR、人工臆測轉錄、資產解碼、修改原版或直接在原版記憶體注入資料；沒有可辨識文字就維持 unknown。
- 不將第一個完整 copy 誤稱為穩定最終畫面；其後 VRAM 改寫、動畫與玩家可見停留狀態各須獨立驗證。
- 不公開、提交或在 Issue 嵌入原版像素、frame、palette、PNG 或任何原版衍生 bytes。

## 退出條件

- [x] 完整 320×200 canvas→A000 copy 的讀取收據能以 200 組×320 bytes、原始指令與暫存器交叉確認，或有明確缺口。
- [x] copy 完成的 fixed-step indexed frame、palette 與 PNG 都有雜湊且僅在 `workplace/reports/`。
- [x] 可見靜態文字候選清冊只登錄可可靠辨識者，且每筆明列尚未證實的來源與中文安全矩形。
- [x] 未建立 DRAFT／READY、覆蓋原型或原版衍生版控內容；文件、Issue #8、Git、Docker 清理與權利邊界一致。
