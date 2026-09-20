# 目標 001：證據與基線

狀態：completed（以可重現的 Windows 3.x blocker 結束）
日期：2026-09-20  
對應 Issue：[ #1 ](https://github.com/wicanr2/colonization_cht/issues/1)、[ #2 ](https://github.com/wicanr2/colonization_cht/issues/2)、[ #3 ](https://github.com/wicanr2/colonization_cht/issues/3)、[ #4 ](https://github.com/wicanr2/colonization_cht/issues/4)

## 目的

在開始抽取、翻譯或覆蓋任何文字前，確認「哪一份原版」是研究目標，以及該版本能否由
dosgolem 重現至少一條冷啟動基線。這輪的產物是可回查的證據與阻塞報告，不是中文化成品。

## 範圍

1. 建立兩份本機原始封存檔及其解包候選的 SHA-256 與權利邊界清冊。
2. 建立可重現的 Docker 研究入口；原始輸入唯讀、`workplace/` 為唯一可寫中間區。
3. 以 dosgolem 的實際能力探測特定雜湊版本的冷啟動路徑，記錄尚未支援服務與最小重現。
4. 若路徑可達，建立最早互動畫面或主選單的 dosgolem 快照、輸入、索引畫面與狀態收據；
   DOSBox／DOSBox-X 只能作輔助交叉驗證。

## 排除項目

- 不抽取或翻譯遊戲文本，不建立正式中文字型或覆蓋程式。
- 不修改原版 EXE、資料、圖像、存檔或任何遊戲規則。
- 不把 dosgolem 尚未走過的服務宣稱為已支援，也不以 DOSBox-X 單獨當作最終收據。
- 不發布、打包或公開原版衍生內容。

## 證據契約

每份收據至少記錄輸入檔名與 SHA-256、解包方法、工具／映像版本、位址或畫面座標的地址空間、
執行輸入與結果。結論必須標為 `confirmed`、`強推論`、`假說` 或 `未知`。

原版缺失或 dosgolem 缺少服務不是失敗宣稱；應以可重現的 blocker 記錄下來，並把需要補足的能力
分為通用機器層與遊戲專屬流程。

## 退出條件

本輪只有在下列條件全部滿足時才完成：

- [x] #1 的輸入與權利清冊可在 Docker 重跑，且 Git 追蹤清單不含原版素材。
- [x] #2 的研究工具入口可重現，沒有 root-owned 專案輸出或本專案殘留容器。
- [x] #3 對固定雜湊版本有 dosgolem 能力報告；每個缺口都有最小重現或明確的已支援證據。
- [x] #4 有 dosgolem 自行重生的冷啟動基線，或有足以阻止該基線的可重現 blocker。

## 結果與下一閘門

`COLONIZE.EXE`（SHA-256 `ae7d9149f056766a534fe8f0006c9512aac1e1004e9776ab3cca818e4833b650`）
是 Windows 3.10 NE 執行檔。dosgolem probe 只執行其 DOS stub 7 道指令，輸出
`This program must be run under Microsoft Windows.` 後以離開碼 1 結束；未實作服務為 0，
只代表 stub 沒碰到缺口，**不代表 Windows 遊戲可執行**。完整可重現證據見
[`RESEARCH-LOG.md`](../../RESEARCH-LOG.md)。

本輪退出不代表遊戲已中文化或可遊玩。由於原定輸出階段執行器無法進入目標程式本體，
動態文字路徑（#5）必須等待 [Issue #18](https://github.com/wicanr2/colonization_cht/issues/18)
的使用者決定；靜態圖像文字路徑（#8）不得被誤報為完整中文化。
