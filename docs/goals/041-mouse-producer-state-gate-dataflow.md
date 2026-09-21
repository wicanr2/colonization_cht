# 目標 041：滑鼠 producer 狀態閘門與 caller locals 資料流

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 039](039-mouse-producer-body-dataflow.md)、[目標 040](040-dosgolem-far-call-observation-alignment.md)

## 目的

已確認的 producer 在 `0924:0588` 回寫 caller locals，並以 `AX = BX OR [DS:5AB4]` 回傳；其內亦讀取
`[DS:5E6C]` 與快取座標 `[DS:61B0]`／`[DS:61B2]`。本輪以既有的無輸入與 `(160,100)` 單一左鍵兩條重播路徑，
記錄這些 word 與 caller locals 在 call 前後的值及 read/write 條件。

本輪不注入新座標、不做座標掃描、不變更原版或 dosgolem，也不將資料位址命名為按鈕、畫面文字或中文覆蓋條件。

## 執行項目

1. 從固定 #5,465,772 state 重播無輸入與既有單一左鍵短窗；在 call 前／後傾印 `DS:5AB4`、`DS:5E6C`、
   `DS:61B0`／`61B2` 與 stack-local 目標範圍，保存 inputs、step、segment:offset 與 SHA-256。
2. 以目標 040 已校正的 raw／trace 對齊，對照 `BX`、`CX`、`DX`、locals 與 AX；分開記錄 confirmed
   instruction dataflow、強推論與未知資料語意。
3. 只判定此固定 state 的 boolean formula 是否由 `BX` 或 `[DS:5AB4]` 貢獻；不外推其他互動點、hit-test、
   選單、文字來源、訊息鍵或中文安全矩形。

## 結果

- 同一輪於 #5,465,825（`0110:094A` caller far call 執行前）及 #5,465,864（`0110:094F` return 後、
  consumer 前）取樣；lifecycle 明確記錄四個真實模式 ranges。控制／左鍵 trace SHA-256 分別為
  `743614e10222443ffc0d4ee56a58969164b1bb1603b9ea55d04aacd87f411b8f` 與
  `bf811495bffd0198fdf662d692c7413d3e46328dcdfec9703d1f4bfd59ef9a90`。
- **confirmed（固定 state）**：兩組前後皆有 `[DS:5AB4]=0000h`、`[DS:5E6C]=FFFFh`、
  `[DS:61B0]=00A0h`、`[DS:61B2]=0064h`。因此本次 raw `AX = BX OR [DS:5AB4]` 的第二項為零；
  控制組的 `int 33h`／return `BX,AX` 都是零，左鍵組分別是 `BX=0001h`（service 後）與 `AX=0001h`
  （caller return）。這只確認此 state 的 AX 非零由 BX 貢獻，不能外推 `[DS:5AB4]` 的其他值或語意。
- **confirmed（固定 state）**：caller `[BP-8]`／`[BP-6]` 對應的 `SS:853A–853D` 在兩組都由
  `6603 1001` 變為 little-endian words `0064h,00A0h`。因 `[DS:5E6C]` 非零，本體先取
  `[DS:61B0]`／`[DS:61B2]`，並在 service 後回填該快取座標至 locals；既有左鍵 service 瞬時回傳的
  `CX=0140h,DX=0064h` 不會使此兩個 final locals 不同。
- **unknown**：四個 DS word 的遊戲語意、何時會取其他值、cache／formula 對 hit-test 的作用，及任何按鈕、
  動態文字、原文來源、訊息鍵與中文覆蓋資格。

## 退出條件

- [x] 固定 state、原版唯讀、兩組既有輸入、前／後 dumps、trace 與雜湊可重現。
- [x] `BX`、`[DS:5AB4]`、`[DS:5E6C]`、快取座標與 caller locals 的本輪資料流有推論等級與原始定位。
- [x] 未將資料位址升格為遊戲語意、按鈕、動態文字或中文覆蓋資格，亦未改動 dosgolem。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
