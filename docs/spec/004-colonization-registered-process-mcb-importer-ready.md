# READY 規格 004：已註冊多行程 MCB importer

狀態：READY<br>
日期：2026-09-21<br>
前置：DRAFT 規格 003、目標 015–019<br>
授權範圍：僅 `workplace/dosgolem` 的通用 DOS MCB／程序模型；不得加入 Colonization 位址、文本或遊戲規則。

## 1. 範圍與證據

本規格支援根 PSP 與由 `AH=4Bh AL=00h` 建立、仍在 process registry 的 child PSP owner；這是使用者選定
的 B（通用多行程）所需最小集合。它不是僅接受 root `0100` 的特例。固定輸入的 `OPENING.EXE` SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39` 只提供 root direct-write／overlay
同狀態驗收，不能證明 child／TSR 遊戲行為。

已證實來源：MS-DOS 3.10 Programmer's Reference（PDF SHA-256
`0955283261ffdae38bc70e152be660774c68276febc325e3b11c222e77b993e1`）1-4–1-5、1-183–188、1-196、1-236；
固定遊戲 `03D9:006D/0071/0079` 對 active MCB 的 direct writes；目標 015–019 的隔離 executor 收據。

不在範圍：external／未註冊 owner、無法對應 process 的 raw header、跨程序 `49h/4Ah`、手改後 TSR
lifecycle、v2 state 遷移。它們均失敗即關閉（fail-closed），不能被新模型改寫。

## 2. Typed state 與 raw header

每個 `MCBRecord` 必須同時保存 `seg`、`last`、`size`、`free`、`ownerPSP`、8-byte opaque `name` 與完整
raw 16-byte header；`ProcessRecord` 必須保存 `psp`、parent PSP（或 root）、lifecycle（active/suspended/
terminated/TSR）及每個擁有 block 的 segment。state version 升為 v3，序列化兩種 record；v2 一律拒絕，
不得補 root owner 或空 name。

匯入從 list-of-lists 首 MCB 走到唯一 `Z`：每格只接受 M/Z、`next=seg+1+size` 嚴格前進且不超過 MemTop；
free block owner 必為 0，配置 block owner 必為 registry 的 active/suspended PSP。raw bytes 與 typed
欄位不一致、name 缺失、owner 不存在、重複／環狀 segment、無 Z、或無法表示的 process 狀態，都保存
診斷 snapshot 並拒絕，原客體 bytes 不變。

## 3. 服務轉移

`48h` 僅從 current PSP 的 `ProcessRecord` 配置，所建 header owner 為 current PSP，name 取該 record 的
opaque name；`49h`／`4Ah` 僅接受 owner 等於 current PSP 的既有 block。對缺 block、owner 不符、未註冊
owner 或 raw/type 不一致，CF=1、AX=9，且不得發布新鏈；容量不足沿用平台契約 CF=1、AX=8、BX 最大值。
`4B00` 建 child record、parent link、child 初始 MCB 與名稱；`4Ch` 僅回收該 child owner blocks；`31h`
只在 keep 範圍、child blocks、raw chain 與 registry 一致時保留，否則拒絕。`51h/62h` 回 current PSP。

每次成功服務只從 typed records 產生 header，保留 name；不得以 root PSP 或全域 `freeSeg` 推導 owner。任何
rejection 都不覆寫已接受的客體 MCB chain。

## 4. 驗收

1. synthetic root＋child：child `62h` 回 child PSP，`48h/4Ah/49h` 的 owner/name 與 raw header 一致；
   normal exit 回收 child blocks，parent allocation 不重疊。
2. TSR：僅在 scope 內一致的 retained blocks 時成功；矛盾 snapshot 拒絕而不覆寫。
3. state v3 round-trip 保留 raw header、owner/name、registry 與 parent relation；v2 被拒絕。
4. fixed `OPENING.EXE`：direct MCB writes 後 importer 保存 `$sys$` 等 raw name，`AH=49h` failure 不重發
   舊 arena；重生同一 `AL=03h` overlay 收據。這只驗固定原版實際觸及路徑。

完成後才可修改 dosgolem；實作後需同一份驗收通過才可另立 CONFORMED 規格。
