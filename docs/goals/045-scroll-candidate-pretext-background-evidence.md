# 目標 045：中央卷軸候選的 pre-text 背景證據

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #8](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 043](043-scroll-text-canvas-writer-provenance.md)、[目標 044](044-scroll-candidate-input-asset-provenance.md)

## 目的

目標 043／044 已確認中央卷軸候選有 `MPSLOGO.SS → runtime buffer → 3A6A8h → 04A2 → canvas → A000`
的有限鏈，但沒有 pre-text 畫布資料。這一輪只在 candidate writer 時窗前後，對既有 canvas 位址建立可重播的
前／後／差分收據，檢驗是否存在可獨立識別、可逆而且不跨界的 pre-text 背景。

## 執行項目

1. 從固定 #2,000,000 state，重播至已知 `04A2:017A` writer 時窗前後；對 `lin:25E84` 起的候選外包範圍取樣，
   並記錄同時的 CPU write watch、raw／register 與指令步數。
2. 若可重播出前後資料，量化變更位址的行／列分布、候選外包與有限外框的連通性；只有能由前一時刻資料直接
   回復且不跨越未知圖像的區域，才可標為「pre-text 背景候選」。
3. 若前時刻已包含同一不可分離像素、資料不足以識別背景，或位址／畫面對齊不一致，明確拒絕清除／遮罩策略。
   不 OCR、不讀出原文、不解包／轉存原版圖、不建立文本鍵、譯文、字型、DRAFT／READY、覆蓋程式或 dosgolem 修改。

## 退出條件

- [x] 固定 state、原版唯讀、前／後 snapshot、write watch、raw／register 與 report 雜湊可重現。
- [x] 每個背景結論以 confirmed、強推論或 unknown 標示，且不把「writer 前」誤當作「無文字背景」。
- [x] 中文安全矩形與覆蓋資格只有在可逆 pre-text 證據成立時才討論；否則明確保持 unknown。
- [x] 文件、Issue #8、Git、Docker 清理與權利邊界一致。

## 收據與結論

固定輸入仍為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）與 DOS manifest
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。所有重播均在 UID/GID 1000:1000、
無網路、一次性 Docker 容器中執行；原版 `/game` 唯讀，產物只在 gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 從 writer 前 state #3,756,000 重播，第一筆記錄的內容變更是 #3,756,004、`04A2:017A` 對 `2727Eh`；於 #3,756,003 對 `lin:25E84:7420` 取 pre snapshot，最後一筆變更是 #3,759,074，於 #3,759,075 取 post snapshot。前／後 snapshot SHA-256 分別為 `0b7e7cd03768152053903bc605a7eb6a4ab1cf25beb3815bac33a71c292cde67` 與 `6191b68d2acfd063256874dd21874928163d8a2b4a8318c121579d8383ffa41e`。 | 兩份 snapshot 在同次、完整 writer 窗口的確切前／後取得；不是跨次重播比較。 |
| confirmed | 前後差分有 254 bytes；全數 pre 值為 `00`，位於 `x=[86,241)、y=[139,141)`。row 139 的 99 bytes 是 `x=[142,241)`，row 140 的 155 bytes 是 `x=[86,241)`，兩列重疊，構成單一連通區。差分統計 SHA-256 為 `4f0cc26a6009f31246d2623da90734043c6017b6e626fb352294b0887b2f31b3`。 | 這個 writer 對該有限 canvas 區做的是從零值開始的連通繪製，而非取得已確認的可見背景。 |
| confirmed（安全否定） | 以目標 031 的約略候選矩形 `x=[148,208)、y=[123,146)` 比較，254 bytes 中僅 120 筆在矩形內、134 筆在外；連通區跨越其左右邊界。writer register 收據從 #3,756,004 的 `DS=3960,SI=10A8,ES=2343,BX=3E4E` 延續至 #3,759,074 的 `DS=3960,SI=10AC,ES=2343,BX=3FF0`。 | 不可把這個零填充前狀態或既有約略外框當作可逆清除遮罩、中文安全矩形或覆蓋範圍。 |
| confirmed（工具限制） | lifecycle 記錄完整 254 筆且沒有前段遺失；`-watch-file` 僅保存最後 200 筆（SHA-256 `02592072b8f376734e7720ef09ccd79b9aa1669c839c197605880af170c61172`）。 | 254 筆總數與首／尾定位以 lifecycle 為準；不得將 200-line watch file 偽稱完整逐筆清冊。 |
| unknown | 零值是否代表任何可見／原始背景、原文、精確文字幾何、完整候選圖邊界、可逆背景、中文安全矩形與覆蓋資格。 | 不 OCR、不解包或轉存原版圖、不建立文本鍵、譯文、字型、遮罩、DRAFT／READY、覆蓋程式，且不修改 dosgolem。 |

本輪的結論是安全否定，不是 pre-text 背景成功證明；同一 zero-fill writer 已無可推進的實作證據，後續應改查有獨立背景資料流的候選。
