# 目標146：靜態內嵌文字普查與覆蓋候選（Issue #8）

狀態：完成；開始與完成：2026-09-26。對應 [Issue #8](https://github.com/wicanr2/colonization_cht/issues/8)。

## 方法（可重跑）

- 正常玩家路徑：前端 `--control` 以目標132 輸入（`workplace/reports/goal132-options-title-event/window-prefix-1280000000.inputs.json`）重播到 1280M，於 1M～1275M 共 25 個 `--checkpoint-steps` 擷取原版畫面，去重得 18 個相異畫面。
- 不按鍵的開場動畫：`tools/goal146-opening.inputs.json`（只有一筆游標移動，終點 1000M），每 5M／10M 擷取。
- 動態／靜態判別：`tools/probe_goal141_captions.go -from 10000000`（輸入 `tools/goal146-early.inputs.json`）記錄 10M～80M 所有 `0D21:00C6` 印字事件與其他寫入者範圍，雙冷啟動 JSON 相同、無監看控制一致。畫面上有字、但同期沒有任何印字事件者判為靜態。
- 原版像素與截圖只在已忽略的 `workplace/reports/goal146-static/`。

## 靜態文字清冊（原版圖檔內嵌）

| 編號 | 來源圖檔（SHA-256 前 16） | 邏輯座標（半開） | 內容 | 正常路徑可見 | 可安全覆蓋 | 證據 |
|---|---|---|---|---|---|---|
| ST1 | `OPENING.PIK`（`80ea1dd4a00a4029`） | (50,57)–(173,63) | 拉丁文地圖題字 OCEANVS OCCIDENTALIS | 是（跳過開場後的海圖 8M～12.5M；不跳過時 285M 起） | 不建議：古地圖裝飾字，屬美術 | 畫面 confirmed；圖檔歸屬強推論（開檔序列） |
| ST2 | `OPENING.PIK` | (145,135)–(208,155) | 卷軸飾框 CARTE MICROPROSE 1994 | 同上 | 不建議：品牌與美術 | 同上 |
| ST3 | `MPSLOGO.SS`（`b4c805281404638c`） | 畫面上方中央 | MPS LABS 標誌 | 僅不跳過開場（約 1M～230M） | 否：品牌標誌 | 畫面 confirmed |
| ST4 | `MPSNAME.SS`（`32a28079209ec3e8`） | 標誌下方 | The MicroProse Design Group | 僅不跳過開場 | 否：公司名 | 畫面 confirmed |
| ST5 | `OPENCRD1～3.SS`（`6807ae8a…`／`0ba68fa5…`／`179257b9…`） | (36,172)–(284,192) 卷軸橫幅 | 製作名單：A MicroProse Adventure、Game Design by、Programming by、Computer Graphics by、Original Music by、Sound Programming by、Quality Assurance by 與人名 | 僅不跳過開場（310M 起） | 可：職稱橫幅可覆蓋，人名保留 | 畫面 confirmed；橫幅與 `OPENING.TXT @CREDITS` 影格對應屬強推論 |
| ST6 | `OPENLOGO.SS`（`8168d9d749b8a399`） | 未觀測 | 遊戲標題標誌（`OPENING.TXT` 影格 767） | 僅不跳過開場，1000M 內未出現 | 未知 | 假說（檔名與註解） |

正常路徑其餘圖檔（`DIFFICUL.PIK`、`NATIONS.PIK`、`WOODPANL.PIK`、`KINGLSS1.PIK`、`LEVN0001～0010.PIK`、海上介面）在已擷取畫面中沒有看到內嵌文字；畫面上的字都有同期印字事件，屬動態。

## 普查時發現的動態文字（尚未中文化，歸動態路徑）

- `Loading Game...`（15M）：`OPENING.TXT @MESSAGES`，由開場程式印出；印字常式未驗。
- 主選單版本字串 `COLONIZATION Version 3.0 -- 7-Feb-95`（與五列選單同一事件群）。
- 國王接見畫面（約 67M）：`0D21:00C6` 印字，色號 0／242，bbox `(232,29)–(308,148)`，使用 `FONTKING.FF`。
- 海上 `GAME` 下拉選單各項（`MENU.TXT`，已有譯稿草稿）。

## 未普查

歐洲港口、殖民地、報表、百科、原住民村莊、交易、獨立等畫面不在目前的正常玩家路徑上，尚未普查。
