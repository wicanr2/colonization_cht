# 目標 002：Windows 3.x 執行策略

狀態：等待使用者決定
日期：2026-09-20
對應 Issue：[ #18 ](https://github.com/wicanr2/colonization_cht/issues/18)

## 目的

將目標版本的執行器限制轉化為一項明確、可追溯的使用者決定。專案的既定目標是以
dosgolem 在原版輸出階段覆蓋繁體中文；在能進入遊戲程式本體前，不能研究動態印字、
建立畫面收據或假稱中文化可運作。

## 本輪範圍

1. 重核固定輸入、dosgolem 獨立副本與其公開能力矩陣，確認 blocker 仍然成立。
2. 將可行執行策略、各自影響與不相容邊界寫成單一決策前沿。
3. 使用者作出選擇後，才回填 `CONTEXT.md`、工作清單、受影響 Issue 與下一輪目標。

## 排除項目

- 不在未決定前實作 Windows 3.x、NE loader、Windows API 或遊戲專屬位址。
- 不以 DOS stub 的退出結果當成遊戲冷啟動、正常玩家路徑或文字輸出證據。
- 不改用其他執行器；那會違背目前「使用 dosgolem」的專案目標，除非使用者明確修改目標。
- 不抽取、翻譯、覆蓋或散布原版文字、圖像或執行檔。

## 已確認證據

| 事項 | 證據 | 等級 |
|---|---|---|
| 遊戲目標格式 | `COLONIZE.EXE` SHA-256 `ae7d9149f056766a534fe8f0006c9512aac1e1004e9776ab3cca818e4833b650` 是 Windows 3.x 3.10 NE 執行檔。 | confirmed |
| 現有實際執行結果 | dosgolem probe 只執行 7 道 DOS stub 指令，輸出 `This program must be run under Microsoft Windows.` 後以 code 1 結束。 | confirmed |
| 現有能力邊界 | dosgolem 官方 README 將其定義為 DOS 執行器；獨立副本 `d9c0c27ca9af8239c7e96272a7165e03d7da04bf` 未含 Windows 3.x、Win16、NE loader、`USER.EXE` 或 `GDI.EXE` 的實作／宣告。 | confirmed（限於此提交與關鍵字範圍） |
| 不能由 probe 推論的內容 | Windows 3.x 應用程式載入、GDI 繪圖、文字輸出事件、可互動畫面及遊戲流程。 | unknown |

完整輸入與 probe 收據見 [`RESEARCH-LOG.md`](../../RESEARCH-LOG.md)。

## 決策前沿

此時只有兩個仍符合「使用 dosgolem」目標的選項：

1. **擴充 dosgolem 的 Windows 3.x 最小執行路徑。** 在 `workplace/dosgolem` 獨立副本中，先以
   DRAFT／READY 規格界定足以載入此固定 NE 程式並取得第一個文字輸出事件的最小通用能力，再逐項
   建立收據。這保留目前輸入版本，但範圍、風險與維護成本最大；不能把完整 Windows 實作當成未經
   驗證的承諾。
2. **由使用者提供合法 DOS 版輸入。** 重新盤點該版本、固定雜湊並以 dosgolem probe 建立新的
   冷啟動收據。這保留「以 dosgolem 做輸出階段轉譯」架構，且最可能直接進入文字研究；代價是目前
   Windows 3.x 版本不再是本輪研究標的。

建議選項 2：它最直接保留專案的核心技術目標，同時避免在尚未有最小可行 Windows 3.x 規格時，
把大型執行器擴張誤當作中文化進度。

## 退出條件

本輪在下列條件滿足前保持等待狀態：

- [x] 固定輸入、DOS stub 結果與 dosgolem 能力邊界有可回查證據。
- [x] 決策選項只包含仍符合目前專案目標的路徑，排除未授權的執行器替換。
- [ ] 使用者明確選擇選項 1 或選項 2（或明確修改專案目標）。
- [ ] 已將採用與排除項、受影響工作分支回填 `CONTEXT.md`、`docs/worklist.json` 與 Issue #18。
