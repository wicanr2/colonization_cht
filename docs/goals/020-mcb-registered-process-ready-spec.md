# 目標 020：已註冊多行程 MCB importer READY 規格

狀態：in_progress<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 019](019-mcb-generic-importer-ready-review.md)；來源草案：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 目的

以 B 的真正範圍建立 READY 候選：支援 root 與由 `EXEC AL=00h` 建立、仍在 registry 的 child PSP owner；
保存 raw 16-byte MCB header／owner/name／鏈／state，並拒絕外部 owner、矛盾 header、斷鏈與不相容 v2
state。這是通用已註冊多行程模型，不是 root-only 特例；未知跨程序／TSR 規則保持 fail-closed。

## 執行項目

1. 以目標 015–019 的 platform、original、executor 收據逐項寫出 typed data、registry、服務邊界、
   migration、失敗輸出與同狀態驗收。
2. 證據審查每項 READY 契約；若有未被契約化的行為，保留 DRAFT，不實作。
3. 建立 READY 規格（或精確記錄未通過），更新文件、Issue #24、Git 與 Docker 清理。

## 停止線

- 外部／未知 owner、direct-write 後未知 lifecycle、跨程序 `49h/4Ah` 與 TSR 一律 fail-closed，不猜補。
- READY 僅授權明定資料模型與測試；此目標不修改 dosgolem、原版、存檔或中文覆蓋。

## 退出條件

- [ ] 已註冊 root／child owner 的所有輸入、狀態、服務、拒絕與 migration 都有 READY 契約或明確 DRAFT 缺口。
- [ ] READY（若成立）含 raw header、registry、state、固定遊戲 overlay 同狀態與 synthetic child 驗收。
- [ ] 文件、Issue #24、Git 推送與 Docker 清理一致。
