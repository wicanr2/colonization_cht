# 目標 026：`OPENING.PIK` 的靜態繪製資料流

狀態：completed（Issue #8 保持進行中，等待文字與幾何證據）<br>
日期：2026-09-21<br>
對應 Issue：[ #8 ](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 025](025-opening-static-asset-inventory.md)

## 目的

針對目標 025 中最早由正常開場分支完整讀取的 `OPENING.PIK`，追蹤其 DOS 讀取目的緩衝區、後續 mode 13h
VRAM 寫入端與原始暫存器，確認或明確否定這項特定候選的資料流關聯。這輪只建立繪製定位，不判讀圖像內容、
不判斷是否含文字，也不設計中文覆蓋。

## 執行項目

1. 從固定 `OPENING.EXE`／state v3 以已確認的 BIOS Enter 正常輸入重播，限定在 `OPENING.PIK` 首次開啟、
   主要 payload 讀取與其後最小的 mode 13h 寫入窗口；記錄原始 DOS 讀取目的段址／線性範圍。
2. 對目標 023 已知的 VRAM 搬運端及由本輪觀測新發現的端點記錄 `CS:IP`、DS:SI、ES:DI、SS:SP、指令步數與
   VRAM 寫入範圍；只有來源指向已確認讀取緩衝區才可稱為 confirmed 資料流。
3. 以相同輸入的無侵入對照驗證時序與畫面輸出；若 shared draw routine、解壓緩衝或快速釋放使一對一關係不可見，
   記錄最小缺口與推論等級，不靠檔名、載入順序或畫面變化猜補。
4. 將命令、固定輸入、檔案與收據雜湊、dosgolem commit、位址空間及結論追加至研究紀錄；回填現況、工作清單、
   Issue #8、工作歷程與 Git。沒有足夠的文字與幾何證據前，不建立靜態覆蓋 DRAFT／READY 規格。

## 結果

在固定的 BIOS Enter 路徑中，`OPENING.PIK` 的兩段主要 payload 由 DOS 服務讀入 `5755:0000` 與
`5755:F000`。第 4,104,159 指令的 `0AC2:04F5` 是 `0AC2:04F4` 的 `MOVSB` 執行後位置；其
`DS=5755`、`ES=1C43`，因此已確認該原始緩衝區的取樣 byte 寫入 `1C43` 畫布。這不是由檔名或載入順序
推論。

第 5,464,375 指令的 `0557:00A1` 是 `0557:009F` 的 `REP MOVSW` 執行後位置；其
`DS=1C43`、`ES=A000`，`SI`／`DI` 均按每列 `0x140` 遞進。這確認較晚的完整畫布寫入 mode 13h VRAM。
其間 `OPENBORD.PIK` 與多個 `.SS` 資產也會讀入並可能改寫畫布，故本輪**不**聲稱 `OPENING.PIK`
的任何特定 byte 保留至最終像素，更不聲稱任何螢幕矩形、圖像語意或內嵌文字。

## 停止線

- 不用 `poke`、direct-entry、記憶體注入、資產轉檔或人工圖像判讀偽造 `OPENING.PIK` 到 VRAM 的關聯。
- 不把共用畫面搬運常式、非零像素或資產載入當作單一檔案的 direct data-flow 證據。
- 不修改原版、dosgolem、遊戲行為、檔案格式或中文覆蓋；原版衍生輸出只能留在 `workplace/`。
- 不從這一個候選外推其他 `.PIK`／`.SS` 資產，其他項目須各自取得可回查證據。

## 退出條件

- [x] `OPENING.PIK` 的 DOS 讀取目的範圍、取樣的 raw-buffer→canvas 搬運，以及較後的 canvas→VRAM
  整屏搬運都有可重播原始收據；未宣稱單一檔案直達任何最終像素。
- [x] 資料流結論具 confirmed／強推論／unknown 分級，並明示不能外推到文字存在、畫面矩形或其他資產。
- [x] 未建立 DRAFT／READY 規格、覆蓋原型或原版衍生版控內容。
- [x] 文件、Issue #8、Git、Docker 清理與原版素材權利邊界一致。
