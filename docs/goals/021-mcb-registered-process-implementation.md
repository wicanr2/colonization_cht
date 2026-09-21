# 目標 021：實作已註冊多行程 MCB importer

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
授權規格：[READY 規格 004](../spec/004-colonization-registered-process-mcb-importer-ready.md)

## 目的

在隔離 `workplace/dosgolem` 實作 READY 規格 004：registered root／child owner 的 raw MCB header、
owner/name registry、state v3、current PSP、服務轉移及 fail-closed import。遊戲專屬位址與資料不進
dosgolem，原版檔保持唯讀。

## 執行項目

1. 將 arena／process／state 擴充為 owner/name/raw header 與 registry，實作 v2 state 拒絕。
2. 將 `48h/49h/4Ah/4B00/4Ch/31h/51h/62h` 改由 current PSP／registry 驅動，並在未註冊或矛盾狀態 fail-closed。
3. 實作 MCB raw-chain importer／publisher 與 synthetic root-child、state、TSR rejection 測試。
4. 以固定 `OPENING.EXE` 重跑 overlay 路徑，驗證 direct header name 保留且失敗 `49h` 不重發舊 arena。
5. 更新 CONFORMED／DRAFT、歷程、Issue #24、Git 與 Docker 清理。

## 停止線

- 不支援 external owner、未知 cross-process／TSR lifecycle 或 v2 state；均 fail-closed。
- 實作發現規格缺口時回到 DRAFT，不能在程式或測試默默猜補。

## 退出條件

- [x] READY 規格 004 的 synthetic child、state、rejection 與 fixed overlay 驗收通過；見
  [CONFORMED 規格 005](../spec/005-colonization-registered-process-mcb-importer-conformed.md)。
- [x] 客體 raw header、typed registry 與保存狀態無 owner/name 遺失。
- [x] 不在範圍的 owner/lifecycle 可診斷地 fail-closed。
- [x] 文件、Issue、Git、Docker 與權利邊界一致：文件提交 `550e664` 已推送，
  [Issue #24 回填](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755765894)已確認，
  Docker 無殘留容器、未發現 root-owned 產物或誤建 `.md` 目錄。
