# 目標 017：多行程 MCB 的 DOS 平台契約證據

狀態：in_progress<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 016](016-mcb-process-service-draft-audit.md)；待修訂規格：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 目的

取得版本可識別的原始 MS-DOS 平台文件，建立 `AH=48h`、`49h`、`4Ah`、`4Bh`、`4Ch`、`31h` 與目前
PSP 對 MCB owner／child／TSR 的公開契約邊界。這些證據只用於限制 B 的通用 executor DRAFT；固定
`OPENING.EXE` 尚未觸及的 child／TSR 仍不得冒稱為遊戲原版行為。

## 執行項目

1. 在 Docker 中只讀下載並擷取 Microsoft 的 MS-DOS Programmer's Reference 原始手冊，記錄 URL、
   檔案 SHA-256、版本、頁碼／文字片段與工具版本。
2. 將手冊所明示的輸入、owner／釋放、錯誤回傳、child 結束與 TSR retain 契約，與現行 dosgolem
   source／目標 016 executor 收據逐項比較；未明示的行為保持 unknown。
3. 修訂 DRAFT 003 的 public-platform evidence 與 B 的拒絕／測試前沿，不升 READY、不實作。
4. 更新目前脈絡、研究／工作歷程、worklist，回填 Issue #24 並完成 Git／Docker 收尾。

## 停止線

- 不以手冊填補版本特有或未明示的跨程序／手改 MCB 行為；不修改 dosgolem、原版或中文覆蓋。
- 不把平台契約或 executor synthetic test 稱為 Colonization 原版 same-state parity。

## 退出條件

- [ ] 公開原始手冊的版本、雜湊、頁面／片段及萃取工具可回查。
- [ ] `48h/49h/4Ah/4Bh/4Ch/31h` 與 PSP owner 的已明示／未明示條件已逐項比對現行 executor。
- [ ] DRAFT 003 與目前脈絡保留 unknown、未 READY、未實作。
- [ ] 文件、Issue #24、Git 推送與 Docker 清理狀態一致。
