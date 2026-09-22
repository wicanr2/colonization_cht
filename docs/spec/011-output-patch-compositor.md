# 規格 011：不寫回原版的畫面補片合成器

狀態：CONFORMED（通用合成契約；非遊戲辨識規格）<br>
日期：2026-09-22<br>
入口：[目標 056](../goals/056-live-menu-overlay.md)、Issue #26

## 證據與分層

[規格 009](009-first-text-overlay-draft.md) 已證實印字前後的真實背景與 180 個變更像素。
原型 `tools/prototype_overlay.py` 的背景還原、雙軸幾何及回退已通過 14 項測試。
使用者已確認 4 倍畫布／Cubic 11 24px。通用部分移至隔離 dosgolem 的 `overlay` 套件，
不搬入遊戲來源、位址、譯文、字型檔、場景識別或控制流程。

此契約定義輸入陣列上的純函式，不聲稱任何特定場景生命週期已證實；
遊戲適配器仍須獨立辨認版本、印字入口與返回、來源鍵及適用場景。

## 資料與運算

- `NewPatch(before, after []byte, width, height int, safe image.Rectangle)`：
  兩個索引畫布必須為恰好 width×height，尺寸正值、最多 1,048,576 像素；
  safe 必須非空且完整位於畫布。深拷貝 safe 中的 before／after，不持有機器記憶體。
  safe 中至少有一個差異才能建立補片；只還原這些實際差異像素，不能抹平整個矩形。
- `Compose(indexed []byte, palette []byte, width, height, scale int, patch *Patch,
  ink *image.Alpha, position image.Point, colorIndex byte, enabled bool)`
  回傳新 RGB(A) 圖片、applied、reason 與解碼錯誤。
  palette 是 768 bytes、每通道 0..63 的 VGA DAC 值，轉 8-bit 採 `(v<<2)|(v>>4)`。
  scale 限 1..8 且輸出最多 16,777,216 像素；最近鄰放大。
- 先產生原版放大副本。disabled、nil patch／ink、場景局部不吻合或字模越界時，
  回傳完全未改的副本與原因；無效原始尺寸／色盤／scale 回傳錯誤而不猜補。
- 套用前，raw 畫面的 safe 全部像素必須逐一等於 patch 的 after；
  包含背景，而非只比較舊文字色。這只是一項局部保護，不是場景辨識的替代品。
  任何游標、反白、重繪造成的不符都不覆蓋；不猜哪個色號是游標。
- 字模是外部提供、從譯文 TSV 與確認字型產生的 Alpha 圖，不內嵌譯文。
  position 為放大後墨跡左上角；整張 Alpha 須完全位於放大的 safe，雙軸不能裁切。
  缺譯／缺字／溢出由適配器不提交字模，回退原文；本套件不自行截字或更換字型。
  Alpha 的 Stride／Pix 長度亦須驗證，壞字模回退 `invalid-ink`，不得繪製途中 panic。
- 合成先只恢復補片中 before≠after 的原像素，再以目前 palette[colorIndex]
  繪製 Alpha。兩個輸入畫布、palette、patch 與 Alpha 均不得被修改。
- 本套件不持有事件佇列或持久畫面；每次以本次原始畫面重新合成，不能疊上前一幀中文。
  場景、版本、恢復快照及事件失效由遊戲適配器先撤下 patch。

## 驗收與停止線

單元測試含：真實非純色背景還原、未變像素保持、缺補片／字模、disabled、
局部畫面改變、不同畫布尺寸、雙軸越界、無差異、壞色盤、非法scale、輸入不可變。
單元 fixture 只證明純運算契約；本案正常路徑還須用即時觀測產生 patch，
並比較觀測／合成開關前後原版完整狀態相同。

READY 審查：所有運算可由輸入與既有原型確定，無需猜測原版語意；
此規格不授權把三種輸出情境、正式字型散布或完整中文化標為完成。

## 驗收收據

實作提交 `315d17f6697bcd4040b12749a1038fdf677338f8` 的 `overlay/compositor.go` 與測試。
`go test -count=1 -cover ./overlay` 及 `go vet ./overlay` 通過，敘述覆蓋率100%；
此數字僅代表合成器程式測試，不是遊戲中文化覆蓋率。
本案七組正常路徑原版狀態一致；105 張檢查點圖由獨立 Pillow 解碼比對，
不覆蓋時逐像素等於原版，覆蓋時差異只在安全區，且清晰中文畫面與使用者確認的原型像素一致。
入口：[目標 056](../goals/056-live-menu-overlay.md)、`tools/verify_live_images.py`。
