# 目標 018：MCB wire format 與直接改寫界線證據

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[ #24 ](https://github.com/wicanr2/colonization_cht/issues/24)<br>
前置收據：[目標 017](017-mcb-platform-contract-evidence.md)；待修訂規格：[DRAFT 規格 003](../spec/003-colonization-mcb-arena-reconciliation-draft.md)

## 目的

從已固定的 MS-DOS 3.10 原始手冊擷取 MCB header、owner、鏈與程式直接改寫的公開說明，並與
`OPENING.EXE` 已證實會直接改寫客體 MCB 的路徑及 dosgolem 現行 `WriteMCB()` 比對。目標是定義
B 的匯入驗證與 fail-closed 邊界，不將手冊未明示的跨程序結果猜成 DOS 或遊戲事實。

## 執行項目

1. 在 Docker 中從目標 017 固定文字收據擷取 MCB 格式、owner、鏈與 direct-write 的頁面／段落。
2. 對照固定 `OPENING.EXE` 的客體 MCB 收據、`03D9` direct writes 與現行 machine `WriteMCB()` 的
   位元組布局；每項標示 platform、original 或 executor 證據來源。
3. 修訂 DRAFT 003：定義 importer 需保留／驗證的 raw header bytes、可接受與拒絕的矛盾形狀，以及
   尚無法驗證的 owner lifecycle；不升 READY。
4. 更新文件、Issue #24、Git 與 Docker 清理狀態。

## 停止線

- 不修改 dosgolem、原版或中文覆蓋；不以手冊猜測直接改 MCB 的後續跨程序語意。
- 不把固定 `OPENING.EXE` 的單一 root-owner 快照泛化為任意 owner 或 TSR。

## 退出條件

- [x] MCB wire format／owner／direct-write 的原始手冊證據與 hash 可回查。
- [x] 平台、固定遊戲與 executor 的 header 行為已分層比較，矛盾不被靜默吸收。
- [x] DRAFT 003 有 importer raw-byte／拒絕前沿，仍未 READY、未實作。
- [x] 文件、Issue #24、Git 推送與 Docker 清理一致。

完成收據：Issue #24 的[目標 018 回填](https://github.com/wicanr2/colonization_cht/issues/24#issuecomment-5755285987)
與提交 `35a86f0`；收尾提交另記錄本檔 completed 狀態。
