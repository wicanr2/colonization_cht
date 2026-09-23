# 規格023：選國後姓名提示畫面的文字與玩家路徑

狀態：DRAFT；日期：2026-09-24。來源：[目標092](../goals/092-neighbor-card-runtime-and-nation-route.md)、
[研究紀錄](../../RESEARCH-LOG.md)與本機
`workplace/reports/goal092-neighbor-runtime/`。本規格只確認一個
正常玩家可達的原版畫面；不授權正式中文輸出或修改姓名輸入。

## 固定原版與重播

合法 DOS `OPENING.EXE` SHA-256
`3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`、
`VICEROY.EXE`
`a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3`、
`GAME.TXT`
`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`、
`NAMES.TXT`
`4bf5ba261f71e9215450801d0ac4b00a66e91b046a3b592516524bea03bd6061`、
`LABELS.TXT`
`e4af0da201eb4df5ecdc2033d711d30f975c752f2967dc97b6a8159004582204`、
`NATIONS.PIK`
`bd31e62d7b7652e6903aaea76b1641f11d5333ff6a6da13fd26411c9f080bf54`。
當次另開啟的 `WOODPANL.PIK` 為19,257 bytes，SHA-256
`0858856ad5b5dd0b6ab8e7a8f815fa602a9cf0237d8d323cd2b5ca141b32bc69`。
隔離 dosgolem 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`、
Go 1.24.13、研究映像 `colonization-research:20260920-r2`；
原16筆真視窗輸入 SHA-256
`a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`。

原版從冷啟動至43M步的正常輸入維持不變；43M步移到右卡
`(255,50)`、44M步左鍵按下、45M步放開，46M步右卡畫布穩定。
接著移到選國頁左下可見的完成提示 `(65,184)`，47M步按下、
48M步放開。49M步與55M步的320×200索引畫面、底層畫布及
色盤完全相同；不需要 direct-entry、記憶體修改或測試旗標。

## 已證實、待證與權利界線

- **confirmed**：48M步按下時仍為選國頁，放開後開檔序列新增
  `WOODPANL.PIK`、`GAME.TXT`；49M至55M步畫面穩定，
  索引 SHA-256
  `128280c6bc9b0c3622b4d27642fdf7d2ecbf3866f068ddd87f20a2b6f096c58e`，
  底層畫布 SHA-256
  `4182cf7454d507e9dda76e4d81bde65ded7508314c5c518892508f8cddfb1b37`。
  原版位址空間分別是 DOS 實模式 `CS:IP`、20-bit 線性 RAM、
  320×200索引畫布及原始檔案位移；不能把上述畫布雜湊當成
  文字的檔案來源。
- **confirmed（畫面目視）**：以 Ebitengine 從同一原版索引與
  色盤作四倍最近鄰控制圖，可見提示 `Please Enter Your Name.`
  與畫面中的 `Jacques Cartier_`。獨立驗證器已逐像素核對
  控制圖等於原版索引／色盤。原文只為辨識下一研究目標而記，
  不是原始文字位移、格式化規則或可直接覆蓋的鍵。
- **未知**：兩則文字是動態印字、資產烘入或混合；若為動態，
  TXT／EXE 檔名、原始位移、RAM 流向、輸出呼叫點與安全矩形
  尚未追查。`Jacques Cartier` 是否為該國預設名、是否可編輯、
  Enter／滑鼠確認後的狀態也未驗證。畫面看似有輸入游標，
  只能列為假說，不得據此改原版語意或譯寫玩家姓名。

兩次獨立冷啟動的四條路徑收據各自逐位元組一致，無逐幀
觀測控制組的 CPU、完整 RAM、索引、色盤、虛擬時間、開檔及
各檢查點畫布相同。原版畫面與 PNG 只留已忽略的 `workplace/`，
不得放入公開散布包；獨立 PASS 收據 SHA-256
`08014a9e6355dc3569ffc6cf3469c69852158164c1e2fe2e255c2277e09a8149`，
沒有增加十四段已驗正式中文顯示。

## READY 前提

先沿玩家路徑確認姓名欄的輸入／確認行為，再以原始 bytes、
載入／格式化／輸出事件找出提示與預設名各自的來源。
每欄需另外量原版墨跡、當次多色底圖、四倍安全矩形、
逐欄中文字級、最長譯文與原文回退。原版輸入欄位不應因
顯示譯文而改寫查找、規則或存檔；未達 READY 前維持原文。
