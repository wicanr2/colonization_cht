# 目標 027：`OPENING.PIK` 畫布變更的幾何邊界

狀態：completed（否定原先 `OPENING.PIK` 歸屬，並勘誤目標 026）<br>
日期：2026-09-21<br>
對應 Issue：[ #8 ](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 026](026-opening-pik-render-provenance.md)

## 目的

目標 026 已確認 `OPENING.PIK` 的取樣原始緩衝區會寫入 `1C43` 畫布，且較後該畫布會複製到 mode 13h
VRAM。本輪只量測這個已確認寫入事件影響的畫布位址範圍，並在已證實的跨列複製條件下換算為 logical pixel
座標。目標是為後續逐一確認靜態候選建立可回查的幾何界線，不判讀圖像、不做 OCR、不判斷文字存在，也不設計
中文覆蓋。

## 執行項目

1. 由固定 `OPENING.EXE`／state v3 以已確認 BIOS Enter 正常輸入重播；限定 `OPENING.PIK` 主要讀取、
   `0AC2:04F4` 的 `MOVSB` 及其最近畫布寫入窗口，避免以完整開場的共同 VRAM 活動代替候選證據。
2. 對每一個保留的 `1C430h–2C42Fh` 寫入，以原始 `CS:IP`、步數、DS:SI、ES:DI、位址與前後狀態分組；
   僅將已由 `DS=5755` 且直接 `MOVSB` 證實的事件歸為 `OPENING.PIK` 取樣寫入。
3. 僅在同一畫布與 `0557:009F` 的已確認 `REP MOVSW`／每列 `0x140` bytes 契約閉合時，將位址換算為
   320×200 logical pixel 座標及有界範圍；若寫入未形成單一矩形，保留多段範圍，不強迫合併成覆蓋區。
4. 對照前後 canvas／VRAM 的雜湊與 changed-address 分布，記錄是否能區分 `OPENING.PIK` 影響與其他資產的
   後續改寫。所有原版衍生 bytes、快照與影像只留在 `workplace/reports/`。
5. 將收據、輸入雜湊、dosgolem commit、位址空間、推論分級與不能得出的結論追加至研究紀錄；回填現況、
   工作清單、Issue #8、工作歷程與 Git。沒有已確認文字與中文安全矩形前，不建立 DRAFT／READY 規格。

## 結果與勘誤

這輪否定了目標 026 的資產歸屬。`OPENBORD.PIK` 在第 4,103,486 指令以 DOS 讀取將 10,245 bytes 寫入
`5755:0000`，亦即線性 `[57550h,59D55h)`；它在第 4,104,159 指令的第一個畫布 `MOVSB` 之前，覆寫了
目標 026 當作 `OPENING.PIK` 來源的共享緩衝區開頭。`0AC2:04F4` 的 raw byte `A4` 是 `MOVSB`，其寫入後
IP `0AC2:04F5` 的 40 個暫存器樣本均為 `DS=5755`、`ES=1C43`，且 `SI=0007h–0BD9h`，完全落在
`OPENBORD.PIK` 覆寫範圍內。因此「`OPENING.PIK` 原始資料寫入畫布」沒有成立的資料流證據，必須撤回。

由第 4,099,000 指令快照至第 4,157,000 指令的完整 stdout 監看，共有 7,680 個不同的畫布位址從零變更，
恰覆蓋 `1C430h–1E22Fh`，即 logical pixel `(0,0)–(319,23)` 的 320×24 範圍。其中 `0AC2:04F5`
有 672 次 `MOVSB` 寫入，分散在第 0–22 列的多段範圍；相鄰 `0AC2:0551` 有 7,008 次寫入，直接前一 byte
`0AC2:0550` 是 `AA`／`STOSB`。這是 `OPENBORD.PIK` 載入後的共用畫布處理窗口，**不是** `OPENING.PIK`
的幾何，亦不是文字、圖像語意或中文安全矩形。

本輪曾以 `-dump-mem-at` 傾印 `1C430`，但 probe 將此值解為 IDA 線性位址並轉成執行期 `0D530h`；該前後
傾印不是畫布，沒有用於任何結論。有效的幾何收據只採固定 state、完整 stdout `-watch` 紀錄、DOS 讀取目的地、
暫存器與 raw instruction bytes。`-watch-file` 在此版本最後只留下 200 筆，故也未被當作完整分布來源。

## 停止線

- 不以檔案大小、螢幕非零像素、載入順序、畫面觀感或共同 VRAM copy 推測 `OPENING.PIK` 的圖像／文字矩形。
- 不對原版記憶體使用 `poke`、direct-entry、解包轉檔、人工辨識、OCR 或原版素材輸出；不修改原版、dosgolem、
  遊戲行為或中文覆蓋。
- 不將同一畫布上之 `OPENBORD.PIK` 或 `.SS` 後續寫入混入 `OPENING.PIK` 的已證實範圍；無法分離時應回報 unknown。
- 不將幾何界線誤稱為文字存在、中文安全矩形或正式覆蓋資格。

## 退出條件

- [x] `OPENING.PIK` 的取樣畫布寫入無法成立；已以 `OPENBORD.PIK` 的中間覆寫、完整暫存器與指令 bytes
  收據記錄最小反證，並勘誤目標 026。
- [x] 已以已證實的每列 `0x140` bytes copy 契約換算監看窗口的 320×24 logical pixel 範圍；它只屬
  後續共享畫布窗口，不作為 `OPENING.PIK` 幾何。
- [x] 結論明確分開 confirmed／強推論／unknown，且不宣稱任何圖像、文字、覆蓋安全矩形或其他資產的結果。
- [x] 未建立 DRAFT／READY 規格、覆蓋原型或原版衍生版控內容；文件、Issue #8、Git、Docker 清理與權利邊界一致。
