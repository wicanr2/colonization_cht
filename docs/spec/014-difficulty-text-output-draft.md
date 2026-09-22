# 規格014：難度畫面文字輸出追查（DRAFT）

狀態：DRAFT；不可用於正式覆蓋。日期：2026-09-22。關聯：[目標061](../goals/061-next-visible-text-slice.md)。

## 已證實的界線

- 固定 DOS 輸入的 `LABELS.TXT` SHA-256 為
  `e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`；
  `Choose`、`Difficulty Level` 位於檔案位元組位移 `0x888`、`0x890`。
- dosgolem 隔離副本 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`、
  Ebitengine 正常滑鼠路徑的本機 `goal059-ebiten.memory`（DOS 線性記憶體空間）
  含 `Choose` 於 `0x4DF72`、`Difficulty Level` 於 `0x4DF79`；
  `Click Here When Finished` 於 `0x2A7B5` 及 `0x4DF59`。
  這是執行結束快照中的位元組出現位置，不是字串繪製呼叫點。
- 本機 `goal059-ebiten.difficulty.png` 真視窗截圖可見前兩段文字分兩行，
  另有完成提示與難度卡片上的文字。既有 `937C:0538` 主選單掛勾沒有證明
  這些字串由它印出；也不能據此判定它們是靜態圖像。

## 待驗證契約

先在固定輸入的正常路徑，以只讀觀測記下文字首次出現在原始索引畫面的
指令前後、呼叫堆疊、來源位元組與畫布差異；再判斷動態印字或烘入圖像。
兩種分支都須取得精確安全矩形、滑鼠遮擋及畫面撤銷條件，並以原版索引畫面、
色盤、CPU、RAM 和虛擬時間對照中文／英文兩組。未取得這些證據前，
`text/draft.zh-Hant.tsv` 的「選擇／難度」只維持草稿，不設定覆蓋鍵。

此規格不授權修改原版資料、畫面控制流或遊戲狀態；未知輸出路徑保留英文。
