# 目標 044：中央卷軸候選的解碼輸入與資產歸屬

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #8](https://github.com/wicanr2/colonization_cht/issues/8)<br>
前置證據：[目標 043](043-scroll-text-canvas-writer-provenance.md)

## 目的

目標 043 已確認 `opening-scroll-two-line-text` 候選由 `04A2:017A` 寫入 canvas，並由 `0557:00A1` 複製至
A0000；但其 `DS:SI` 解碼輸入尚未與某個原版檔案、原文字節或字元邊界閉合。本輪只追這段輸入 buffer 的讀取與
生產者，嘗試建立最小的「原版 read → runtime buffer → 04A2 writer → canvas」證據鏈。

## 執行項目

1. 從固定 #2,000,000 state，對已見 `04A2:017A` sample 的輸入線性範圍建立 read watch，確認實際消費位址、
步數與 raw 指令；不得將 register snapshot 單獨當檔案來源。
2. 以 `OPENING.EXE -sbpro` 的正常冷啟動重播，記錄候選 writer 前的 DOS read、輸入 buffer producer 與檔案名稱；
只有同一步數、同一 buffer bytes 的 read/write 關係才能為特定檔案提供 confirmed 或強推論歸屬。
3. 輸入來源無法閉合時，保留 `unknown` 並記錄最小工具／state 缺口；不 OCR、不讀取或轉存原文、不解包資產，
不建立文字鍵、譯文、清除策略、字型、DRAFT／READY 或覆蓋程式。

## 退出條件

- [x] 固定 state／冷啟動、原版唯讀、輸入 read/write watch、raw／register 與檔案事件有可重現收據及雜湊。
- [x] 資產歸屬以 confirmed、強推論或 unknown 明確標示，未將檔名或畫面外觀誤作證據。
- [x] 原文、字元邊界、精確文字幾何、安全矩形、中文覆蓋及 dosgolem 修改均保持未推定。
- [x] 文件、Issue #8、Git、Docker 清理與權利邊界一致。

## 收據與結論

固定輸入仍為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`），固定 manifest 是
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`。所有工作在 UID/GID 1000:1000、
無網路、一次性 Docker 容器內執行，原版 `/game` 唯讀；以下原版衍生 report 均只留在 gitignore 的
`workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 由第 #2,000,000 state 到 #3,759,100 的 `3A000h–3B000h` read watch 在 #3,757,195 記錄 `3A6A8h` 被 `04A2:01EB` 讀取；report SHA-256 為 `38c9157a36c314186adfb39c3715a3ee8e4401e4168f3262c0c838396092788f`。目標 043 已獨立確認同一候選由 `04A2:017A` 寫入 canvas。 | `3A6A8h` 是這條既有候選畫布鏈實際消費的解碼輸入位址；它不是原文字元或文字邊界。 |
| confirmed | 正常冷啟動中，`MPSLOGO.SS` 最後一次 DOS read 在 #1,062,435，把檔案 offset `863` 起的 55,286 bytes 載入 `4DC3:0000`（線性 `[4DC30h,5B426h)`）。窄範圍 target watch 在 #1,135,873 記錄 `3A6A8h` 由 `0AC2:0551` 變更；raw `0AC2:0550=AA` 是 `STOSB`，其前置暫存器為 `DS=4DC3, ES=3873, DI=1F78`，故輸出物理位址是 `3A6A8h`。target report SHA-256 為 `b13ab97c15fc55d77f5c5de7674a8cc67b523791d31d1e8ef16169a16b9f832f`。 | 這一候選輸入位址由讀取 `MPSLOGO.SS` 後的解碼器寫入；這是檔案讀入、runtime buffer 與 candidate input 的已觀測鏈。 |
| confirmed | 同一解碼窗以 `DS=4DC3` 讀取線性 `4F091h`（#1,135,789，`0AC2:0556`）與 `4F092h`（#1,135,892，`0AC2:04F5`）；後者在上述檔案載入範圍內。窄範圍 source-read report SHA-256 為 `509155e13ef50ca543a5d4f6f336029c7b79e3a4f2b58449fcf5fc8abbb2f278`。 | 解碼器確實從該 `MPSLOGO.SS` runtime buffer 消費資料；沒有輸出原版資料或重建資產。 |
| 強推論 | 已觀測的 `3A6A8h` input bytes 經 `04A2` 消費並落入 `opening-scroll-two-line-text` 候選畫布鏈，而該 input 由上述 `MPSLOGO.SS` buffer 解碼而來。尚未對候選的每一個 input byte 建立一對一 raw-byte→pixel 對照。 | `MPSLOGO.SS` 是此靜態候選的來源資產，而非 `OPENING.PIK`；完整候選圖的資產歸屬僅為強推論。 |
| unknown | 原文、字元邊界、完整解碼格式、完整候選圖邊界、pre-text 背景、中文安全矩形、反向辨識條件與覆蓋資格。 | 不 OCR、不建立文本鍵、譯文、字型、遮罩、DRAFT／READY、覆蓋程式，也不修改 dosgolem。 |

冷啟動的 broad input-write report SHA-256 是 `40049b9d08a6e54f15809f4bb15e134259099ca1795afaa40e34fec1737669a6`；
target watch 的 17 筆內容變更與 source-read report 都只登錄位址、值與指令定位，未保存原版檔案內容。
