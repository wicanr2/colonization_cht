# 目標 004：執行策略阻塞稽核

狀態：blocked（等待使用者決定）
日期：2026-09-20
對應 Issue：[ #18 ](https://github.com/wicanr2/colonization_cht/issues/18)

## 目的

確認是否仍有任何不改變專案架構、且能讓「使用 dosgolem 的輸出階段中文化」向前推進的
技術工作；若沒有，明確記錄阻塞原因，避免以重複的靜態盤點或 DOS stub 結果製造進度假象。

## 已完成且不應重做的證據

- 目標輸入、權利邊界、隔離工具鏈與 dosgolem DOS stub 收據已由目標 001 與 Issues #1–#4 完成。
- dosgolem 的固定獨立副本 `d9c0c27` 沒有 Windows 3.x／Win16／NE loader 路徑；這由目標 002
  的能力矩陣核對固定。
- 固定 NE 的 header、區段、匯入與資源清冊已由目標 003 與已關閉的 #19 完成；它不包含可執行
  的 Windows 路徑或任何文字輸出 trace。

## 阻塞判定

`COLONIZE.EXE` 的唯一已驗證執行結果是 DOS stub 輸出
`This program must be run under Microsoft Windows.` 後離開。沒有 Windows 3.x 載入與 API 路徑時，
無法以 dosgolem 進入遊戲本體，因此下列工作均沒有可信的輸入：

- 動態印字呼叫點、訊息來源與輸出攔截鍵（#5–#7、#11–#12）；
- 正常玩家路徑上的靜態文字畫面與覆蓋定位（#8–#9、#13–#14）。

繼續解析靜態 NE 資料不能回答這些執行期問題；把 import 名稱或資源表當成文字輸出證據會違反
本專案的 fail-closed 與證據閘門。因此這不是缺少一次命令或測試，而是需要使用者選擇的架構邊界。

## 唯一解鎖條件

使用者必須在 Issue #18 選擇其一：

1. 授權在 `workplace/dosgolem` 的獨立副本中，先以 DRAFT／READY 規格擴充足以載入此固定 NE
   程式的最小 Windows 3.x 路徑；或
2. 提供合法 DOS 版輸入，以既有 dosgolem 能力重新建立固定雜湊的冷啟動收據。

選項未確定前，不實作、猜測或替換執行器。收到選擇後，本稽核目標即解除阻塞，並以新目標文件
記錄採用／排除項與下一個可驗證工作。
