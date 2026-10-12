# 首座 HD 建築的來源與繪製生命週期

狀態：DRAFT。只記錄原版證據及隔離原型要求，尚未授權正式 HD 覆蓋。
入口為[目標186](../goals/186-display-settings-and-gameplay-video.md)，工作項目為
[Issue #63](https://github.com/wicanr2/colonization_cht/issues/63)。
本專案只覆蓋顯示，不修改原版 RAM、遊戲規則、資料或存檔。

## 輸入與定位

| 輸入 | SHA-256 |
| --- | --- |
| VICEROY.EXE | a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3 |
| BUILDING.SS | e91784542982216a1921b219967f0856a2a246721c5097a3e0e1e771ea9d6fe4 |
| 正常 GUI 輸入 | 9b246ee6e4aa2fc36e3db4eae8fa8487527e7b4393afff9fdcfe19e61c741979 |
| 初始 COLONY09.SAV | 52ae8b7bd4bea1869afb825af165a8edc50882fc176d49985d4fb3c362d5469b |
| 第032幀完整534bytes編碼 | 7c34170632e995ebfb281e451f340d14faec5fa25970ca0479493d99758afb2a |

原始編碼位於 BUILDING.SS 解壓 part3 的位移22616，該完整片段唯一。
原始輸入與像素只留本機。工具版本為 Go1.26.7、隔離 dosgolem
82a14b266e1b5bc904e2d0fe507daf6bea41a013、IDA9.4與Python3.12.3。
IDA 使用已驗證的 ida-pro-9.4-idapython:py312-v1，映像ID為
4ac62de83339c215bab10e455cee3a22d9c6efed9fd0d8ed0f068327b83a06ab。

位址空間分開記錄：

- 原版執行位置是 dosgolem real-mode CS:IP，RAM是20bit線性位址。
- IDA位置是從唯讀原版新建MZ資料庫的線性EA，不能直接當執行位置。
- 已證實16bytes寫入碼唯一對應原版0D46:01D2與IDA EA0x1C532。
  自動導覽名sub_1C36A及範圍EA0x1C36A至0x1C563保留原樣，不作語意證據。

## 已證實的三次未裁切呼叫

confirmed僅限本次正常玩家路徑。原版入口0D46:000A，返回121D:1554。
首次67569117至67579078步，後兩次見下節。原始ENTER、保存暫存器、
讀取指令及retf 6與實際數值共同支持以下對應：

| 原始定位 | 本次值與用途 | IDA讀取證據 |
| --- | --- | --- |
| 入口DX，保存於[BP-2Ah] | x=56 | EA0x1C3E7及後續水平裁切／目的位移 |
| 入口SS:SP+4，進入後[BP+6] | y=13 | EA0x1C433及後續垂直裁切／列位移 |
| 入口DS:BX，保存於[BP-2Ch] | 1C6A:2DA8，目的畫布描述 | EA0x1C3BE至0x1C3D0 |
| DS:BX+0、+2 | 高200、寬及列步長320 | EA0x1C373、0x1C37A、0x1C3CD、0x1C53E |
| DS:BX+4、+6 | 目的遠指標2CAE:0000，線性0x2CAE0 | EA0x1C3C1、0x1C3C4、0x1C45E |
| 入口AX，保存於[BP-2Eh] | 33，本素材對應解碼第032幀 | EA0x1C383至0x1C3A8 |
| 入口SS:SP+6、+8 | 圖像記錄表遠指標4F22:A6C4 | EA0x1C3A2、0x1C3A5 |
| 記錄表+((AX & 7FFFh)×12)+36h | 4F22:A886 | 同上原始乘法與加法指令 |
| 記錄+0、+2 | 來源遠指標5F3B:000E，完整534bytes一致 | EA0x1C3B1、0x1C3B4、0x1C480 |
| 記錄+8、+Ah | 圖像寬23、高27 | EA0x1C3D3、0x1C3DA及目的像素差分 |
| retf 6 | 首次SP59358至59368，增10 | EA0x1C560及實際返回 |

矩形為[56,13,79,40)，440個不透明像素各寫一次，透明索引253與矩形外底圖不變。
本次來源指紋才是素材身分，不能把AX與幀號的關係外推到其他SS。
AX高位的翻轉語意仍屬強推論；負座標、裁切、其他畫布及其他素材未驗。
記錄+4、+6的228與149不賦予用途。

## 後續寫入與重畫

confirmed：首次返回至75900000步，同矩形有2122筆寫入，涵蓋全部621點。
其中366筆寫入前後同值。按時間與舊值逐筆重播，可完整重建原版終點矩形；
終點矩形等於首次繪製結果，不能用這項終點相等否定中間重畫。

| 原版寫入CS:IP | 次數 |
| --- | --- |
| 0CBA:00CA | 1242 |
| 0D46:01D2 | 772 |
| 0D46:01B4 | 108 |

| 同來源同位置重畫 | 返回 | 驗證 |
| --- | --- | --- |
| 67867911步 | 67877872步 | 完整來源、座標及畫布一致，440點各一次 |
| 72099553步 | 72109500步 | 完整來源、座標及畫布一致，440點各一次 |

兩次進入前的621點等於首次建築前底圖，返回後等於首次建築後畫面。
這足以支持本切片的底圖保存與重畫原型，尚未證實遮擋、離城或重進。
後兩次返回位置的16bytes碼各有一byte不同；完整碼在新IDA資料庫沒有匹配。
差異成因未知。來源、幾何及逐點畫布證據不依賴猜測該呼叫者的用途。

## 隔離原型要求

- 只接受已驗原版指紋、入口碼、完整來源、畫布與幾何；未知來源維持原版。
- 在已辨識呼叫進入時保存該次底圖，返回後核對實際寫入與像素，才建立顯示覆蓋。
  保存畫面、清除原圖與HD合成都在前端記憶體，不寫入DOS。
- 後續原版寫入必須使受影響的顯示覆蓋失效，包含同值寫入。
  已辨識的同素材重畫在返回並核對後重新建立；未知寫入保留原版內容。
  逐像素還是整素材撤銷，須以遮擋原型比較後定案。
- HD目的矩形沿原版放大四倍，點擊範圍由原版決定。候選的輪廓、透明邊界、
  底圖恢復與遮擋安全範圍待審；目前alpha涵蓋率不是正式通過門檻。
- 合成需驗證原版底圖、HD、所選語言、原版游標與畫面外設定列的順序。
  現有文字清除與繪字仍在同一介面，分層介面須經本規格審查後實作。
- 開關HD不得推進DOS、改寫存檔或混用上一畫面的底圖；缺件回原版並記錄原因。

## READY前尚缺

1. 一座可用且指紋明確的正式候選，確認尺寸、透明邊界與底圖恢復。
2. 正常GUI進城、懸停／視窗遮擋、離城及重進，驗證撤除與重畫順序。
3. 原版與候選合成的同狀態畫面，五語、游標、設定列及HD開關抽樣。
4. 來源／畫布／幾何錯誤、過期底圖與未知寫入反例，以及比例相稱的效能量測。
5. 證據審查後限定READY範圍。地形、人物與動畫不因本建築通過而取得信用。

## 重生與收據

研究入口為[畫布探針](../../tools/probe_hd_canvas_writes.go)、
[IDA參數查詢](../../tools/ida_hd_draw_parameters.py)與
[參數及寫入稽核](../../tools/check_hd_draw_parameters.py)。
先用既有--draw-query收據，加--draw-parameters及--draw-write-stream取有限事件；
不加新參數時維持舊觀測結果。另跑參數、舊觀測與--control，共四組。
IDA查詢從唯讀VICEROY.EXE新建容器暫存資料庫，輸出只留workplace。
六個錯誤證據反例全拒絕，四組CPU、完整RAM、VGA與DAC相同。
本工具不記錄WAV，沒有以本輪聲稱音訊對拍通過。

本機根目錄為workplace/reports/goal186-display-hd/hd-building032-draw-boundary-20261012。
IDA重生指令為parameters-r1/run-ida.sh，Go重生腳本為run-parameters-r3.py，
稽核指令為parameters-r3/run-audit.sh。Docker掛載、資源與UID契約沿[AGENTS.md](../../AGENTS.md)。

| 收據 | SHA-256 |
| --- | --- |
| parameters-r1/ida-parameters.json | f891aeed6b49d0aab9448cb10bfc7b63ead2762360e62b31f8c99abcc4ab08eb |
| parameters-r3/stream/draw-boundary.json | 581013a3496a1228eb49ce17da494748601840a41ed1337612172ab0000e8e8a |
| parameters-r3/parameter-audit-v2.json | ce321a3e3e5a11520a76661e9754417bdebd97240748236cd44adf65f00d211e |
| parameters-r3/negative-audit.json | 8ee3fdc1b7d92a6c4bc9500bf2ccda4b620502e51795a7b4183c9b0616469ff0 |
| parameters-r3/probe-check.json | cfd3f4f6a758dac71bb44f02d60130d4c076cd3054375b9c51c42ad1d8b15f96 |

完整指令與原版快照只保存在本機。歷史GUI的完整RAM差異仍未知；
本次正常GUI輸入重播不冒充該歷史GUI同狀態，也未增加文字shown、HD或新版交付完成信用。
