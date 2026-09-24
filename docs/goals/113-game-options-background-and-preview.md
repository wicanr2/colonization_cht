# 目標113：遊戲選項印前底圖與 Ebitengine 中文對照

狀態：in_progress；日期：2026-09-24。承接[目標112](112-game-options-chinese-display.md)與[規格027](../spec/027-game-options-window-draft.md)已驗的九處原版 `GAME.TXT` 位移、DOS 讀入、168-byte解析讀取、印字及1,300M畫面；對應 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)、[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與本輪邊界

遊戲選項九欄仍是英文。要在放大畫布上以繁中取代，首先必須知道原版每欄印字**前**的真實木紋、反白列及核取圖示狀態，而不能在截圖上塗平文字。這輪由正常玩家滑鼠路徑的 `dosgolem` 當次寫入事件擷取印前底圖，核對解析到印字的最後搬運線索，再用固定原始 Cubic 11 與現有真 TSV 做一組**可丟棄**的 Ebitengine 中／英文同狀態對照。原版 EXE、TXT、存檔、滑鼠熱區、快捷鍵及選項功能均不修改；正式覆蓋仍需規格 READY 與逐欄回退驗收。

原版 `GAME.TXT` SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`、`MENU.TXT` SHA-256 `5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`；英格蘭正常開局輸入 SHA-256 `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`，後續開窗輸入 SHA-256 `c4e462678323df8e1915ffcd363f7e7eb83cee4e85e09f618c9206418977e539`。隔離 `workplace/dosgolem` 固定提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，`upstream` 推送位址保持 `DISABLED`。字型只用[字型入口](../../font/README.md)已固定 SHA-256 `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c` 的本機原始 TTF，唯讀掛載，不入 Git。

## 工作與退出條件

1. 核對乾淨工作樹、Git 作者、PRIVATE 遠端、相關 Issue、原版與字型來源；**先推送本目標 Markdown**再修改探針或產生圖。所有分析、建置、測試、抓圖、Ebitengine 與 Xvfb 工作只在限資源、無網路、非 root 的一次性 Docker 執行；原版及 TTF 唯讀。
2. 沿目標112相同正常玩家路徑，於原版 `0D21:012C` 當次視窗第一個字元寫入之前取完整320×200畫布；追標題及八列原始字元印後狀態，核對底圖是否已含核取圖示與反白、各安全矩形的原文差分、來源／畫布相位。至少雙冷啟動與無監看控制；若有背景或控制元件在字間才改寫，改成逐欄印前擷取，不以單張底圖假裝適用全欄。
3. 針對 `0E2D:1F76` 解析讀取到 `0D21:00C6` 印字間的最後搬運，只補能回答此畫面來源鏈的窄觀測。保留檔案 byte 位移、線性 RAM、原版實模式 `CS:IP` 與索引畫布座標各自的基準；沒有直接證據時維持強推論，不為了讓規格過關而猜補。
4. 從真 `text/draft.zh-Hant.tsv` 九筆 `@GAMEOPTIONS` 草稿產生可丟棄預覽資料，保留 ASCII 快捷鍵資訊但不把 `~` 印到畫面。各欄按原版7／8像素字高與安全矩形獨立量測候選 Cubic 11 字級、墨跡、內距及最長文。由 Ebitengine 在四倍畫布恢復當次原版底圖並畫中文，輸出僅限已忽略 `workplace/` 的英文控制／中文候選及差分收據；原型不接正式玩家執行路徑、不更新 README 正式截圖。
5. 建立獨立檢查與負例：錯原版／字型／TSV、底圖相位、缺欄、過長、裁切、安全區外改色與原版狀態分歧都須拒絕。若要在「貼近原版」與「較可讀」間做實質視覺取捨，先保留同狀態 A／B 預覽供使用者選，不代選正式版。證據足夠才更新規格027的 DRAFT／READY 判斷；正式 CONFORMED 必須留給真 Ebitengine 玩家視窗的同輸入、回退與舊十七欄回歸。
6. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、`docs/worklist.json`，由工具重生 `WORKLIST.md`；只推送自製程式、規格及譯文，原版像素、TTF與字模留本機。推送 PRIVATE repo、更新並回讀 Issue，核對輸出 UID/GID、root-owned／誤建目錄及 Docker 容器清理。

## 停止線

圖看起來可讀不等於來源鏈、底圖或反白／游標相位已驗；可丟棄預覽不能計入正式十七段。已驗第一張旗卡的21／25px與難度標題34／38px不得外推至本視窗。若選項譯文熱鍵標示在單列放不下，先量測與提出可丟棄候選，不默默刪除快捷鍵資訊或覆蓋核取圖示。使用者未授權公開原版衍生畫素；對照 PNG 只留已忽略的本機工作區。
