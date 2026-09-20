# 目標 013：審查 MCB 配置區（arena）DRAFT 的原版控制流前提

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 012](012-psound-overlay-writer-lifecycle.md)；待審查規格：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 目的

審查 DRAFT 規格 003 的必要前提：`03D9` 所寫的 MCB 型態資料是否屬於當前客體可見鏈、
第 833,824 指令 `AH=49h ES=2C9A` 的失敗／成功旗標由誰消費，以及「配置區未吸收客體鏈」是否真是
`1C43` 重用的最小通用缺口。結果只能是保留、修訂或以可追溯理由 SUPERSEDE DRAFT；不實作。

## 固定前提

- 原始 DOS 輸入唯讀：`OPENING.EXE` SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`；`PSOUND.COL` 48,599 bytes、
  SHA-256 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 執行器固定為隔離副本 `workplace/dosgolem` commit
  `1b0efdf98ac3ab85c90cb80c3e489e935fb45665`，以 `probe -sbpro` 走正式冷啟動；upstream push URL 必須維持
  `DISABLED`。
- 目標 012 已證實 `02B2:00AF → 086C:0004` 的 `PSOUND.COL` overlay 載入，以及客體 MCB bytes 與
  私有配置區（arena）在 `AH=49h` 後分歧；尚未證實真 DOS 對 `ES=2C9A` 的精確服務語意。

## 執行項目

1. 以有界 dosgolem 正式冷啟動，收集 `03D9:0312` 釋放 helper 的所有進入、caller、`ES`、flags、
   返回值與後續 consumer；直接確認或否定「呼叫端把 `AH=49h` 當成成功」這項前提。
2. 以 IDA Pro 9.4 對實際 runtime raw-binary 匯出 `03D9:0312`、其 caller 視窗及 list-of-lists／
   MCB 走訪點；每筆保留原始段:位移、bytes、地址空間、輸入雜湊及推論等級。
3. 比對 `AH=52h` 所得鏈起點、`03D9` 寫入範圍與第 833,824 指令前的客體 MCB 記錄，分辨它是活躍鏈、
   私有暫存或未知結構；不以欄位形狀或名稱相似作結論。
4. 檢查後續 `AH=48h` 取得 `1C43` 的必要條件是否可由 DRAFT 所提「有效鏈匯入」消除；若尚有獨立
   缺口，明確列為 DRAFT 未知，不能把單一修法當成完成宣稱。
5. 對 DRAFT 003 作最小文件化審查：補足 confirmed 證據、下調過度結論，或維持未知與 READY 阻擋；
   不建立 production code、遊戲位址特例或測試替身。

## 停止線

- 不修改 `workplace/dosgolem`、原始檔、遊戲規則、存檔、文字輸出或中文覆蓋。
- 不把 IDA 偽碼、單一 MCB 欄位形狀、檔名、DOSBox／DOSBox-X、direct-entry 或記憶體注入當成
  dosgolem 正式冷啟動收據的替代品。
- 不重新考古標準 DOS 服務語意；若需平台前提，只引用公開規格並將本遊戲的 callsite、資料流和
  consumer 分開記錄。
- 未取得完整 caller、服務返回與至少一個 consumer 的交叉證據前，DRAFT 003 不得升為 READY。

## 審查結論

- `03D9:0312` 在本冷啟動只由兩個 callsite 進入：第 833,812 指令的 `0B35:0348`
  傳入 `ES=2C9A`，以及第 833,861 指令的 `08D2:0207` 傳入 `ES=2C5D`。兩次 `AH=49h`
  都由 dosgolem 回 `AX=0009`，wrapper 經 `rcr al,1`、`cbw`、`mov al,ah` 轉為
  `AX=FFFF`。這是現行執行器的可重播結果；真 DOS 對這兩個請求的精確語意仍是 unknown。
- 兩個 caller 都未把該 `AX=FFFF` 當成「釋放成功」：`0B35:0348` 無條件跳至
  `0B35:034E` 並以 `mov ax,[bx]` 覆寫它；`08D2:0207` 以 `mov ax,[bp-0Eh]`、
  `mov dx,[bp-0Ch]` 覆寫後才比較。因此 DRAFT 不得把這兩次 `AH=49h` 描述成遊戲要求
  成功釋放 `1C43` 的證據。
- `AH=52h` 回傳的 list-of-lists 是活躍鏈入口：`0419:0005`–`0009` 先呼叫它、再讀
  `ES:[BX-2]`，並以 type／owner／size 逐格走訪。第 816,494 指令回 `0070:0010`，其鏈最終
  到達 `1C42`；`03D9:006D`、`0071`、`0079` 分別寫入 type、size、owner，並在
  `03D9:007F` 回傳資料段 `1C43`。所以 `1C42` 不是私有暫存，而是活躍（active）MCB 鏈的
  confirmed 成員。
- DRAFT 003 維持 DRAFT、未升 READY：它需要的是「在 `48h`／`49h`／`4Ah` 邊界接受已驗證的
  活躍（active）鏈，且即使某次服務失敗也不能用舊 arena 覆寫它」；不是讓這兩個 `AH=49h` 偽裝成成功。
  尚缺完整驗證演算法、owner／多行程模型、失敗回傳契約、state round-trip 與同狀態冷啟動驗收。

## 退出條件

- [x] `03D9:0312` 與其 caller／consumer 有可重跑的動態收據，含 `ES`、`AX`、步數與返回邊。
- [x] IDA Pro 9.4 raw-binary 匯出保留所有關鍵位址、bytes、地址空間、輸入雜湊與推論等級。
- [x] `AH=52h` 鏈定位與 `03D9` 寫入範圍的關係已分類為 confirmed、強推論或未知。
- [x] DRAFT 003 已保留、修訂，且 READY 的阻擋／授權狀態正確；未實作。
- [x] `CONTEXT.md`、`docs/worklist.json`、`WORKLIST.md`、`README.md`、`WORKLOG.md`、`RESEARCH-LOG.md`、
  Issue #24 與 Docker 清理狀態已同步，並完成 Git 提交與推送。
