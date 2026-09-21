# 目標 047：海洋標籤的 pre-text canvas 背景

狀態：in_progress<br>
日期：2026-09-21<br>
對應 Issue：[Issue #8](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 032](032-ocean-label-canvas-writer-provenance.md)、[目標 033](033-ocean-label-post-copy-persistence.md)、[目標 042](042-ocean-label-background-safety-geometry.md)

## 目的

海洋標籤 `OCEANVS OCCIDENTALIS` 已有畫布 writer 與有限顯示存續證據，但單色／主色背景清除已被目標 042
否定。本輪只對 `03BD:00C8`／`REP MOVSW` writer 的完整時窗前後取同次 canvas 快照，檢驗可見標籤矩形是否有
獨立、逐像素可回復的 pre-text 資料。

## 執行項目

1. 從 #4,156,900 的既有 state 建立 writer 前的可重播短 state；以精確標籤幾何
   `x=[53,174)、y=[49,61)` 對應的連續外包範圍取第一筆 writer 前與最後一筆後 snapshot，並以 320-byte stride
   篩回真正矩形，不能把列間鄰近圖像當作標籤。
2. 收集短窗口 write watch、`03BD:00C8` raw／register 與 snapshot 差分；分開記錄「畫布前值」和「已證實
   可見背景」。只有前值可由同次資料回復、且不跨越未知圖像時，才可列為 pre-text 背景候選。
3. 若前值是 zero-fill、writer 仍跨越幾何邊界、或無法確認前值與顯示背景關係，明確拒絕清除／遮罩策略。
   不 OCR、不讀出原文、不轉存圖像、不建立文本鍵、譯文、字型、DRAFT／READY、覆蓋程式或 dosgolem 修改。

## 結果

- 固定輸入仍是 `OPENING.EXE`（SHA-256
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）與 DOS manifest
  `fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。從 #5,432,800 state
  `goal047-ocean-label-prewriter-5432800.state`（SHA-256
  `eb68cfc2630f1a17e6a75f6ebd14725d33ff375d5bcde1aff2297e1fcfbbb468`）以隔離 dosgolem commit
  `1435f175e785ea096a9268cd1021a4222300bd43` 同次重播；原版目錄唯讀，所有產物只留在 gitignore 的
  `workplace/reports/`。
- **confirmed**：#5,432,822 與 #5,447,039 的 3,961-byte 外包 snapshot SHA-256 分別是
  `920b7d966cbebb51532944ac935683a783a13e2b689ccd40840a40ea7518da68` 與
  `b7a87818cacd2da711dab6ef7db84ad01af450fade015140164075f0d0e8a59b`。差分正好有整個外包範圍的
  3,961 bytes；以 320-byte stride 篩回後，真正 `x=[53,174)、y=[49,61)` 的 1,452 pixels 全數變更，
  每列均為 121 pixels，bbox 與既有幾何一致，外部另有 2,509 bytes 變更。
- **confirmed（安全否定）**：標籤矩形的 writer 前 1,452 bytes 全為零值，writer 後有 61 種非零色號；這只證實
  canvas zero-fill 後的合成輸入，並非已證實的可見海圖背景或可逆 per-pixel 背景。完整 lifecycle 有 6,724 筆
  寫入，首筆 #5,432,823 `201A5h`、末筆 #5,447,038 `2106Fh`，全部是 `03BD:00CA`；`03BD:00C8` raw 是
  `F3 A5`／`REP MOVSW`。因此 writer 亦跨越標籤候選外的未知圖像，未達可覆蓋條件。
- lifecycle、snapshot 差分、watch 與 analysis report 的 SHA-256 依序為
  `7f8a371b3b133988114cf866890c8f8f0977fa630a5b864339c3145dd0049cf3`、
  `920b7d966cbebb51532944ac935683a783a13e2b689ccd40840a40ea7518da68`／
  `b7a87818cacd2da711dab6ef7db84ad01af450fade015140164075f0d0e8a59b`、
  `555ce41d9ba1ffec5887e31ddfa962cd283f04900f5a2eb08e67f473c013ee49` 與
  `d182761faece2a88f42bdac0bbf27a94f3072497ce3f7be8920477e868401602`。`-watch-file` 只保留最後 200 筆，
  寫入總數與首／尾定位以完整 lifecycle 為準。
- **unknown**：英文圖樣之前的可見背景、可逆清除策略、中文安全矩形、覆蓋資格與完整資產歸屬。不得把本輪零值、
  可見畫面色號或外包範圍升格為遮罩或安全矩形。

## 退出條件

- [x] 固定 state、原版唯讀、前／後 snapshot、write watch、raw／register 與 report 雜湊可重現。
- [x] 真正標籤矩形和外包區分開量化，背景結論以 confirmed、強推論或 unknown 標示。
- [x] 中文安全矩形與覆蓋資格只有在可逆 pre-text 證據成立時才討論；本輪保持 unknown。
- [x] 文件、Issue #8、Git、Docker 清理與權利邊界一致。
