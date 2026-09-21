# 目標 038：開場滑鼠 boolean 的上游產生者

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 037](037-opening-mouse-poll-first-divergence.md)

## 目的

目標 037 已確認 `0110:0952–0954` 只消費 AX boolean，並非座標 hit-test。本輪只回溯其最近上游：
在相同固定 state、無輸入下擷取 `0110:0920–094E` 的原始 bytes 與短 trace，確認呼叫／回傳邊是否將滑鼠服務
結果放入 AX。這仍不等於確認座標比較、互動矩形、按鈕或文字。

## 執行項目

1. 由第 #5,465,772 state 無輸入重播至 #5,466,200，傾印 `0110:0920–094E` 最小原始範圍並保留 lifecycle；
   原版輸入唯讀，產物只寫入 gitignore 的 `workplace/reports/`。
2. 將 raw bytes 與目標 037 的 `CS:IP` trace 對照，記錄最近的 call／return 邊、AX／BX／CX／DX 可見資料流及
   位址空間。只對已執行 bytes 做指令解讀。
3. 在找到 AX 的直接產生呼叫或明確無法判定邊界時停止；不注入座標、不建立互動區清冊、DRAFT／READY、譯文、字型
   或覆蓋程式。

## 結果

- `0110:0920–094F` 的 48-byte dump（dosgolem real-mode segment:offset，SHA-256 `671e7ed3e7e30d221e5b36c20bbfa402ebed656d2a075288b12c54bf4baa1430`）確認：`0110:0942`／`0946` 取 `[BP-8]`／`[BP-6]` 位址壓棧，`0110:094A` 以 raw `9A 88 05 24 09` 遠呼叫 `0924:0588`，並於 `0110:094F` 回到 caller。
- 目標 037 的對照 trace 證明這個 return point 的 AX 直接送入 `0110:0952–0954` boolean consumer。因此 `0924:0588` 是 AX 的 confirmed 直接 producer call，但其內的 BX/CX/DX／指標資料流、座標比較、互動語意與文字輸出均未知。

## 退出條件

- [x] 原始 bytes、trace 與固定輸入／state 雜湊可重現，原版維持唯讀。
- [x] AX producer 的 call／return 邊或未知邊界保留原始定位、bytes、位址空間與推論等級。
- [x] 沒有把 boolean producer 升格為座標 hit-test、按鈕語意、動態文字或中文覆蓋資格。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
