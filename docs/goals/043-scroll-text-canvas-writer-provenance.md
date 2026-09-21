# 目標 043：中央卷軸兩行字的 canvas writer 追溯

狀態：in_progress（證據已收集，待文件／Issue／Git 收尾）<br>
日期：2026-09-21<br>
對應 Issue：[Issue #8](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 031](031-opening-full-frame-static-text-survey.md)、[目標 042](042-ocean-label-background-safety-geometry.md)

## 目的

另一筆 `opening-scroll-two-line-text` 候選目前只知約略畫面範圍 `x∈[148,208)、y∈[123,146)`，原文、精確文字
幾何、資產來源、copy 後存續與安全矩形都未知。海洋標籤已排除平面清除策略，故本輪先追這個候選的 canvas writer
與資料來源，不能由卷軸外觀推定可覆蓋背景。

## 執行項目

1. 先由既有 #4,156,900 正常 BIOS Enter state 重播至完整 composite copy。其 canvas envelope watch 的 200 筆尾端
僅落在 y=145–146 的整列重畫，不能當成此候選的 writer；故改以最終 VRAM 的精確候選列定位輸出 writer。
2. 從可載入的 #2,000,000 state，以明確 `lin:` 執行期線性位址擷取 canvas 分段快照，再對已收斂的
`0x25E84–0x27B80` 範圍收集 CPU 內容變更。對真正 writer 的 `CS:IP`、步數、raw bytes 與
`DS:SI`／`ES:DI` 建立最小收據；資產歸屬只按實際讀檔證據分級。
3. 不 OCR、不依畫面猜測原文、不建立清除策略、中文、字型、遮罩、DRAFT／READY 或覆蓋程式。

## 結果

固定輸入仍是 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`），原版目錄唯讀掛載；所有 dumps、watch
與 lifecycle 只存在 gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與收據 | 結論 |
| --- | --- | --- |
| confirmed | 從 #4,156,900 state 重播時，候選 VRAM 範圍 `A9A54h–A9A90h` 在 #5,465,240 有 61 筆 `00→非零` 變更，全部由 `0557:00A1` 寫入；watch TSV SHA-256 `a197807033c4097a6f603ce9a5c49d08dd4017c62929444003440c02f44557d1`。 | 這筆候選畫面像素由靜態 canvas→VRAM copy 路徑輸出，不是已發現的動態印字 hook。 |
| confirmed | `0557:0080` raw 中 `009F=F3 A5`、`00A1=A4`；#5,465,240 的 `0557:00A1` 收據記錄 `DS=2443, ES=A000, SI=1B00, DI=9B00`。 | 此端點為 `DS:SI → ES:DI` 的 `REP MOVSW`／`MOVSB` copy loop；候選相對位置映回 canvas 線性 `25E84h`。 |
| confirmed | 以 `lin:25E84`（不是會套用映像偏移的裸 IDA 位址）取樣：#2,000,001→#3,000,000 有 1,080 個候選列位元組變更；#3,000,000→#4,000,000 有 316 個；#4,000,000→#4,156,900 為零。四份 SHA-256 依序為 `6e705b584712528fbd486f1e39e76c5965b7e4c7788daf356d3ab00312e3a7ca`、`b210ad55b2bd9884e07080c2967b5df9c5ad26f646040289e78f5b0e493b804c`、`6191b68d2acfd063256874dd21874928163d8a2b4a8318c121579d8383ffa41e`、相同的 `6191…a41e`。 | 候選 canvas 像素在 #4,000,000 前建立，並在 #4,156,900 前已穩定；不得以晚期整列重畫當作其來源。 |
| confirmed | #2,000,000→#4,156,900 的 canvas watch 收據有 200 筆內容變更，位於 #3,756,652–#3,759,074，皆為 `04A2:017A`；TSV SHA-256 `02592072b8f376734e7720ef09ccd79b9aa1669c839c197605880af170c61172`。sample registers 為 `DS=3960,SI=10A8,ES=2343,BX=3E84`；raw `04A2:0150` 包含 `AC … 26 88 07`。 | `04A2:017A` 是將解碼串流寫入 canvas 的已觀測 CPU writer。CPU watch 只記內容變更，故不能用 200 筆冒稱候選所有像素的完整解碼紀錄。 |
| confirmed | #5,465,772 的 `lin:25E84:7420` canvas 與 `lin:A9A54:7420` VRAM dumps 逐位元組相同，SHA-256 都是 `e7bf4a7e6bbed1a5a086773573558061311967bcab747bb10fa739076b04b946`。 | 在完整 composite 的這個 state，候選外包範圍可由 canvas 同狀態重生至畫面。 |
| unknown | 本輪從 #2,000,000 state 開始時已不保留建構前的原始讀檔事件；已觀測的 `04A2` 解碼輸入未能與特定原版檔案、原文或字元邊界閉合。 | 不能把 `04A2:017A` 命名為文字解碼器或指派 `OPENING.PIK`／任何 `.SS` 資產；原文、精確文字幾何、中文安全矩形和覆蓋資格仍未知。 |

### 勘誤與方法限制

- 最初 `-dump-mem-at` 使用裸 `25E84`；該旗標會將裸位址依映像 IDA 基準換算，實際讀到 `16F84h`，不是 canvas。
  本目標所有採用的快照均改為 `lin:25E84`。先前的裸位址快照比較不得作畫面結論。
- `-watch` 只在 CPU 寫入使 byte 值改變時記錄，且不涵蓋以非 CPU byte write 實作的搬移；它是 writer 定位證據，
  不是完整像素計數器。

## 退出條件

- [x] 固定 state、原版唯讀、VRAM／canvas watch、明確線性位址與 stride 檢驗、writer raw／register 收據與雜湊可重現。
- [x] 候選內真正 writer 與 canvas→VRAM 來源定位已確認；資產歸屬明確標為 unknown，外包鄰近像素未混作文字證據。
- [x] 精確文字幾何、安全矩形、原文、覆蓋及 dosgolem 修改均保持未推定。
- [ ] 文件、Issue #8、Git、Docker 清理與權利邊界一致（待收尾）。
