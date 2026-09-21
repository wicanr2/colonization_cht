# 目標 039：滑鼠 boolean producer 本體資料流

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 037](037-opening-mouse-poll-first-divergence.md)、[目標 038](038-opening-mouse-boolean-producer.md)

## 目的

目標 038 已確認 `0924:0588` 是 AX boolean 的直接 producer call。本輪只讀取該 call 本體附近的原始 bytes，
配合第 037 輪控制／左鍵短 trace，追蹤 `int 33h AX=0003` 的 `BX/CX/DX` 何時被讀取、兩個 stack-local
pointer 的寫入與 AX 回傳。它仍不是座標 hit-test、按鈕名稱或文字輸出研究。

## 執行項目

1. 從固定 #5,465,772 state 無輸入重播至 #5,466,200，傾印 `0924:0560` 起的最小原始範圍與 lifecycle；
   原版唯讀，產物只進 gitignore 的 `workplace/reports/`。
2. 使用原始 bytes 與既有控制／左鍵 trace 記錄服務入口、輸入暫存器、pointer 寫入與 AX return 的可回查邊；
   每項標示 confirmed、強推論或未知及 dosgolem real-mode segment:offset。
3. 只追到本體的直接輸入／輸出邊；不向外推導矩形、控制項、文字、中文安全矩形或覆蓋設計。

## 結果

- 固定 state 的零指令前與重播到 #5,466,200 後，`0924:0560` 的 128-byte dump 都是 SHA-256
  `538c4844e4c927b347a8f7fd5df991d1344356c7c2428c9732dbae91687acca7`；因此在本輪窗口沒有觀測到
  此範圍的自修改。零指令 lifecycle SHA-256 為
  `245668c2218fdf4b075f3d885e7a8f67ccabd16dddcb046e0cc1c5a29a30a67b`，短窗 lifecycle 為
  `a7384664ca22dd71fffc579b8620465d04dfb440771b430cdd34403a0ae4ee6d`。
- **confirmed（觀測行為）**：兩組 trace 都由 caller 的 raw `0110:094A = 9A 88 05 24 09` 進入其報告為
  `0924:0588` 的遠呼叫目標。控制組的 `int 33h AX=0003` 後為 `BX=0000,CX=0000,DX=0000`，最終於
  `0110:094F` 回傳 `AX=0000,CX=00A0h,DX=0064h`；既有左鍵組則為 `BX=0001,CX=0140h,DX=0064h`，並於
  同一 caller return 邊回傳 `AX=0001,CX=00A0h,DX=0064h`。這證實按下狀態流至既有 AX boolean consumer，
  但不命名座標、控制項或文字。
- **confirmed（觀測限制）**：本機器 state 的 `-dump-seg 0924:0560:128` raw bytes 在 `0924:0584` 有
  `C8 00 00 00`，但 trace 在報告 `0924:0588` 後呈現相符的 BP/SP frame-transition，後續 `int 33h` trace
  標籤亦相對 raw `CD 33` 位置高 4 bytes。此差異在零指令前／短窗後都存在，故不是本輪自修改；其成因是
  **unknown**。在修正或以最小重現釐清 dosgolem 的 raw dump／指令 fetch 對齊前，不能以本段 raw bytes
  指定 trace 位址的精確 opcode、pointer 寫入或座標正規化語意。
- **unknown**：兩個 caller stack-local pointer 的 body 內寫入、`BX` 如何轉為 AX、`CX/DX` 的遊戲邏輯座標、
  hit-test、按鈕與動態文字。這些都沒有因暫存器回傳或 byte 形狀而升格。

## 退出條件

- [x] 原始 bytes、固定 state、trace 與雜湊可重現，原版維持唯讀。
- [x] `0924:0588` 的可確認 BX/CX/DX 與 AX 回傳邊已保留原始定位與推論等級；pointer body 寫入因 trace/raw
  對齊限制維持未知。
- [x] 未將本體資料流升格為座標 hit-test、按鈕、動態文字或中文覆蓋資格。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
