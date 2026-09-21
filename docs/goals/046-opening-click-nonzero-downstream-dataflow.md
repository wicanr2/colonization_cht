# 目標 046：開場既有左鍵非零支路的後續資料流

狀態：completed<br>
日期：2026-09-21<br>
對應 Issue：[Issue #5](https://github.com/wicanr2/colonization_cht/issues/5)<br>
前置證據：[目標 037](037-opening-mouse-poll-first-divergence.md)、[目標 041](041-mouse-producer-state-gate-dataflow.md)

## 目的

在固定開場 composite state 中，既有中央左鍵已確認使 `0110:0956` 寫入 `001Bh` 到 caller local，最後使
`OPENING.EXE` 退出；但該 local 寫入後的控制流尚未逐段收據化。本輪只從同一已知左鍵輸入追至第一個可重播的
mode／終止或文字輸出事件，判定此支路是否提供動態文字輸出線索。

## 執行項目

1. 從 #5,465,772 的完整 composite state，以先前已驗證的 `(160,100)` 單次左鍵、相同絕對步數重播；對
   `0110:0956`、其附近 raw bytes、後續 IP timeline 與 mode／DOS 終止事件建立同一次收據。
2. 對照無輸入控制組與左鍵組，定位 local `001Bh` 寫入後第一個可觀測控制流差異及其後果；不注入座標、
   記憶體或新的按鍵。
3. 若支路只導向退出且沒有文字輸出事件，明確記為非動態文字證據；不把 `VICEROY.EXE` direct-entry、
   batch 假設、畫面外觀或 exit code 假稱為文字／轉交語意。

## 退出條件

- [x] 固定 state、控制／左鍵輸入、raw bytes、IP／register、mode／DOS 事件及 report 雜湊可重現。
- [x] local 寫入後的控制流結果以 confirmed、強推論或 unknown 明確分級。
- [x] 是否有動態文字事件明確記錄；沒有時不得建立訊息鍵、譯文、DRAFT／READY 或覆蓋程式。
- [x] 文件、Issue #5、Git、Docker 清理與權利邊界一致。

## 收據與結論

固定輸入為 `OPENING.EXE`（SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`）、DOS manifest
`fbded5601e09889e285294e605df2c306c12a90603e556113b95d2afcf4d5bd3`、state
`goal033-post-full-copy-5465772.state`（SHA-256
`c5cbfb0e184aac21455bdc7a976d83fa84e55af7cde0de36e40861d9bd7a77ba`）與隔離 dosgolem commit
`1435f175e785ea096a9268cd1021a4222300bd43`。所有重播在 UID/GID 1000:1000、無網路、一次性 Docker
容器完成，原版 `/game` 唯讀；reports 僅保存在 gitignore 的 `workplace/reports/`。

| 推論等級 | 原始定位與觀測 | 結論 |
| --- | --- | --- |
| confirmed | 控制與左鍵兩組從同一 state 起跑；左鍵只在 #5,465,773 排入 `(160,100)`，#5,465,840 被唯一一次按下的 `int 33h AX=0003` 讀到。IP timeline 的第一個差異是 record 96／#5,465,867：control `0110:0960`，click `0110:0956`。control／click IP report SHA-256 分別為 `4f0c51eaf9fff26998740c00bf346d3edec8c872a1dded2094123d4bbfe3f75c` 與 `41ced31cc9fa3b8d750e4ef9f9525a25444816bbebb4c321ffb377c4392fd81b`。 | 非零按下分支的第一個已觀測差異是 `0110:0956`；這不是控制項、座標矩形或文字語意。 |
| confirmed | #5,465,800 的 `0110:094F:96` raw dump（SHA-256 `0880c0b81d4745f3ec7c3f077e5a8248fe23669e6fed0210b77c31a1ebb6acf1`）有 `0956 = C7 46 F6 1B 00`、`095B = C7 46 FC 01 00`、`0960 = 83 7E F6 00`、`0964 = 75 03`。timeline 隨後於 #5,465,909 首次到 `2C5D:0B18`。 | local `001Bh` 寫入後，確實經過依該 local 的零／非零條件分派並進入另一段程式碼；local、分支和 `2C5D` 段的遊戲語意未知。 |
| confirmed | 無 observer 的同一左鍵重播到 #7,000,000，實際在 #5,511,211 切 mode 03h，#5,511,836 以 `int 21h AH=4Ch, AL=6Ch` 終止；baseline lifecycle SHA-256 `33332e0f2cf41bc956d6a763a95d8f9370f15338849f1c308bf5bf0b7267baf0`。帶 timeline 的獨立重播有相同終止結果，lifecycle／trace SHA-256 分別為 `801711afe97d3d00b8c14091e0c49dd054408edf2ec25259031ba16e9407c437`／`3dcf2a4f9c63dc9f82308efc03bb1bc22fabdffa038c73934b0806b537728019`。 | 這個固定 state 的既有左鍵支路是 `OPENING.EXE` 的退出路徑；timeline observer 不改變此結果。 |
| confirmed（無文字） | 控制／左鍵 lifecycle 均為主控台 0 bytes、B8000 非零 bytes 0、全形／半形字型常式 0、開檔 0；左鍵組只有既有滑鼠及退出服務，沒有新的文字觀測。 | 此支路不是動態文字輸出證據，不能建立訊息鍵、譯文、DRAFT／READY 或覆蓋程式。 |
| confirmed（勘誤） | 目標 036 舊 lifecycle 曾記錄同名 state 於 #5,509,826 終止；目前 state／dosgolem 可重播的無 observer baseline 在 #5,511,836 才終止。舊收據沒有同次 state SHA-256 與 dosgolem commit，故無法以目前資料判定差異來源。 | 舊的精確終止步數不再可作為現行收據；「同一左鍵最終退出、無文字」仍由目前重播確認。 |
| unknown | `001Bh`、後續條件、`2C5D` 段、exit code、畫面／控制項語意、`VICEROY.EXE` 轉交、動態文字來源與中文覆蓋資格。 | 不以 batch、direct-entry、檔名、畫面外觀或 exit code 猜測；此輪不修改 dosgolem。 |
