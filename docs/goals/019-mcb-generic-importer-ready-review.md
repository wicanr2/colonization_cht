# 目標 019：通用多行程 MCB importer READY 審查

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 018](018-mcb-wire-format-and-direct-write-evidence.md)；審查對象：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 目的

審查使用者已選 B 是否已能形成一份最小、通用多行程 MCB importer READY 候選：允許已註冊的
root／child PSP owner、保存 raw header 與 name、建立可序列化 process registry；外部 owner、斷鏈、
raw/type 矛盾與未知 lifecycle 必須 fail-closed。此審查不可用「目前遊戲只見 root」收窄 B，也不可
猜測跨程序服務結果。

## 執行項目

1. 以 DRAFT、平台手冊、固定遊戲 header 收據及 executor child／state 收據建立 READY 最小契約矩陣：
   input、typed state、registry、services、state migration、拒絕輸出與驗收逐項標示證據或 unknown。
2. 用一次性 Docker probe 驗證目前 `WriteMCB()` 的 raw 16-byte 格式、owner/name 清空與 child PSP
   registry 可觀測性；只量現況，不修改 dosgolem。
3. 若每個正式行為均有足夠證據，產生 READY 規格；否則保留 DRAFT 並精確列出唯一缺口。無論結果均不
   實作。
4. 更新文件、Issue #24、Git 與 Docker 清理狀態。

## 停止線

- 外部 owner、直接修改後跨程序 `49h/4Ah`、TSR 回收及不相容舊 state 未有明確契約時，不能標 READY。
- 不修改 dosgolem、原版、遊戲規則、存檔或中文覆蓋。

## 退出條件

- [x] B 的 READY 候選逐項有已證實依據或明確唯一缺口，不把 root-only 樣本當成通用證明。
- [x] raw header／child registry／state 的現行觀測有可重現 Docker 收據。
- [x] 規格正確維持 DRAFT 或在全部契約足夠時升 READY；未實作。
- [x] 文件、Issue #24、Git 推送與 Docker 清理一致。

完成收據：Issue #24 的[目標 019 回填](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755331181)
與提交 `185bb87`；收尾提交另記錄本檔 completed 狀態。
