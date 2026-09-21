# 目標 040：dosgolem 遠呼叫觀測對齊最小重現

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 039](039-mouse-producer-body-dataflow.md)

## 目的

目標 039 在固定原版 state 的 `0924` 段觀測到：raw `-dump-seg` 與 trace IP 對同一遠呼叫後序列有穩定的
4-byte 對齊差異。dosgolem 是本專案原版收據的權威，故在繼續追動態文字前，必須以最小、唯讀、可重播的
實驗釐清這是 trace 表示、dump 表示、指令 fetch 或 state 載入何者的觀測限制。

本輪不是修正 CPU、DOS、probe 或遊戲；也不是座標掃描、hit-test、文字抽取或中文覆蓋設計。

## 執行項目

1. 從固定 #5,465,772 state，以零輸入短窗擷取遠呼叫前後的 trace，並取得 trace label 的前後相鄰 raw
   ranges；每份輸出保存檔名、SHA-256、真實模式 segment:offset 與取得時點。
2. 以 dosgolem 目前原始碼的 trace／`-dump-seg` 實作交叉核對：明確列出「trace label」「原始 far pointer」
   「dump 位址」與觀測到的暫存器狀態，不以反組譯器導覽名稱替代原始定位。
3. 將結論限於 confirmed、強推論或未知：若差異仍存在，只提出下一個最小證據／DRAFT 規格門檻；不得直接修正
   dosgolem，亦不得將遊戲專屬位址、文本或座標移入 dosgolem。

## 結果

- **confirmed**：零指令前與零輸入短窗後的五組相鄰 dumps 完全一致。`0924:0588:32` 的前／後 SHA-256 都是
  `b2627ddfa5c50da777bea0a052f4afcec23cc5a632f8cef076b1cf2f52c8d7f1`；短窗 trace SHA-256 為
  `743614e10222443ffc0d4ee56a58969164b1bb1603b9ea55d04aacd87f411b8f`。
- **confirmed**：同一次零指令執行的 `0924:0560:128` dump（SHA-256
  `538c4844e4c927b347a8f7fd5df991d1344356c7c2428c9732dbae91687acca7`）從 byte `0x28` 取出的 32 bytes，與
  獨立 `0924:0588:32` dump 的 SHA-256 相同。前者的 byte `0x28` 對應 `0560h + 28h = 0588h`，其 raw 為
  `C8 00 00 00`；trace 的 `0924:0588 → 058C` 同樣呈現此 `ENTER` 的 BP/SP transition，接著 raw／trace 的
  `058C = 33 DB` 清零 BX。`0110:094A` 的 raw far pointer `0924:0588` 因而與 trace 和 dump 三者一致。
- **結論**：目標 039 的「4-byte 對齊差異」是人工讀取 hexdump 行內位移時的錯誤，不是 dosgolem 缺陷、state
  載入問題或遊戲自修改。dosgolem 的 `doDumpMem`、`CPU.fetch8` 與 `CALL far ptr16:16` 原始碼亦都與這個
  對應相容。本輪不需要 DRAFT、READY 或任何 dosgolem 變更。

## 退出條件

- [x] 固定 state、原版唯讀、零輸入 trace、相鄰 raw dumps 與雜湊可重現。
- [x] trace label／far pointer／dump 位址／frame-transition 的關係逐項記錄，且沒有過度解釋。
- [x] 已判定觀測限制被證據排除；本輪沒有改動 dosgolem，不需要通用 DRAFT。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。
