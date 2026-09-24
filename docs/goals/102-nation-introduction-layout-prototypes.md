# 目標102：四國介紹的原始底圖與繁中排版原型

狀態：completed（僅完成 DRAFT 證據與排版原型）；日期：2026-09-24。承接[目標101](101-nation-introduction-player-path.md)
已驗的四國八節正常玩家路徑、[規格025](../spec/025-first-nation-introduction-draft.md)
與 [Issue #30](https://github.com/wicanr2/colonization_cht/issues/30)。

## 玩家問題與本輪界線

八節介紹已有固定原版來源、實際印字與繁中草稿，但畫面仍是英文。
原始 `Cubic_11.ttf` 曾遺失，使字級、最長譯文換行與真實墨跡無法
量測；且各國 A／B 頁的文字高度不同，不能套用其他畫面的固定字級。
本輪先恢復**相同 SHA-256 的本機字型來源**，由 dosgolem 正常路徑
取得印字前底圖，再在四倍畫布製作八節可丟棄的中文排版對照，
量出各頁的實際字形、安全矩形、行距、換行與不足之處。

本輪只授權 DRAFT 原型與證據；未經版面確認、完整回退與同狀態
正式驗證，不接入 `tools/live_menu.go`，不增加十七段正式中文顯示數。
原版 EXE、TXT、圖像、規則、姓名與存檔一律不改。

## 已知輸入與權利邊界

- `GAME.TXT` SHA-256 為 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
  四國八節的原版印字、索引畫面與雙次冷啟動收據見目標101。
- 主機其他專案及 Go 模組快取各有 `Cubic_11.ttf`，兩份 SHA-256 均為
  先前候選所用的 `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`。
  模組 `github.com/hajimehoshi/bitmapfont/v4@v4.1.0` 的 README 將
  Cubic 11 標為 OFL-1.1；本輪只做本機唯讀量測，不把字型檔、
  衍生字模或原版畫素加入 Git，不把模組整體的 Apache 授權誤套到字型。
- 原版資料與上述字型均唯讀掛載，研究輸出只寫入已忽略的
  `workplace/`，容器以目前 UID/GID 執行。

## 工作與退出條件

1. 先核對 `origin` 為 PRIVATE、Git 身分與乾淨工作樹，將本目標
   **先推送**至私有 `origin/main`，再做探針及排版程式修改。
2. 固定兩份字型的實際 SHA、來源、授權聲明位置與檔內字形覆蓋；
   若版本不符即停止使用，不用近似字型替代。只記錄可重現的本機
   入口，不在未釐清完整發行條件前提交字型。
3. 沿目標101的四國正常滑鼠及 A→B 玩家路徑，讓 dosgolem 在
   第一個 `0D21:012C` 印字寫入前擷取各頁 320×200 原始底圖。
   與原版索引／色盤及無額外觀測控制比對；若新探針擾動 CPU、
   RAM、畫布或時間，先修探針，不拿錯相位底圖作正式原型。
4. 以固定 TSV 的八節繁中稿和真實 Cubic 11，按各頁原版標題／
   正文墨跡高度量測四倍畫布候選字級。每頁明記標題與正文各自的
   安全矩形、內距、實際字形 bbox、行距、行數、最長行、換行與
   溢出策略；大括號只作顯示強調，不交回原版。至少比較兩套
   可丟棄字級／排版，不能用裁切掩蓋溢出。
5. 產生八頁帶原版木紋背景的本機對照圖，檢查安全區外零差異、
   原文可逆、標題／內文互不碰撞與上下邊界。若有候選不合適，
   把具體超界與可見差異記在規格025，不強行升 READY。
6. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md` 與唯一
   `docs/worklist.json`，由工具重生 `WORKLIST.md`；更新並回讀
   Issue #30，推送成果。收尾核對原版與字型未入 Git、獨立
   dosgolem `upstream` 推送仍為 `DISABLED`、輸出擁有權、
   root-owned／誤建目錄及 Docker 容器清理狀態。

## 實作與驗收結果

- 已核對兩份本機 `Cubic_11.ttf` 的 SHA-256 均為
  `8de9c249b92bc414cb73f09ddb76c7cb327edb3907b638f0d0bd22691237fd5c`；
  來源及 OFL 條件見[字型入口](../../font/README.md)。本輪沒有提交字型。
- `tools/probe_goal098_intro.go -preprint` 在 `0D21:012C` 首次改色寫入前
  複製畫布；八頁底圖 SHA-256 均為
  `f31602f9a239a4f83fd6e27e644384009d628517185aeb80bb248479e67d0e71`。
  `tools/check_goal102_preprint.py` 將新探針的既有欄位逐項與目標101
  收據比對，並驗證實際改色寫入數及 bbox；PASS 收據 SHA-256 為
  `6bb468a0ba798ad2a175f542ad77666db780dbd0da8151bada366e3a400374af`。
- 原版標題墨跡高8、正文高9原版像素。八頁排版均以各角色獨立字級
  做兩套候選：貼近原版字高為標題34px／正文38px，較緊湊為
  30px／34px；不是全專案的固定字級。八頁兩版均無缺字、無裁切、
  無安全區外變動。A 頁行數（英／法／西／荷）為貼近版
  8／8／10／9、緊湊版8／7／9／8；B 頁為2／2／3／3，兩版相同。
- `tools/preview_goal102_nation_intro.py` 產生逐頁原文、兩版中文和
  `layout.json`；`tools/check_goal102_layout.py` 逐像素核對原文與
  dosgolem 畫布、中文與印字前底圖，且標題／正文各限本欄安全矩形。
  兩項檢查 PASS；版面資料 SHA-256
  `542b5540fb32712cbc43f216b4d2184ac241d73fbf53a13c6ef380e3468d4f87`，
  排版驗證收據 SHA-256
  `2e467bffb704a33d4a0034310de697dd4ed5904eeb7ec3ad9902ab895e9e0d2d`。
- 私有研究對照：[四國 A 頁](../screenshots/nation-intro-layout-draft-a.png)、
  [四國 B 頁](../screenshots/nation-intro-layout-draft-b.png)。每列依序是
  原版、貼近原版字高、較緊湊；這些圖含原版像素，只可留在私有儲存庫，
  不是 Ebitengine 正式畫面。逐頁原始收據與圖片留在忽略的
  `workplace/reports/goal102-intro/`。

## 停止線與下一閘門

仍待使用者選擇介紹長文的版面；事件鍵、頁相位、游標、離頁、
缺鍵／錯版回退及真視窗同狀態都未達 READY。此目標完成不增加
十七段正式中文顯示數，Issue #30 保持 OPEN。

排版原型、字型相符與原版底圖可逆，仍不等於正式輸出。
若視覺取捨需要使用者選擇，提供同狀態對照，不自行把偏好寫成
正式字級。只有規格025就版面、事件鍵、頁相位、失敗回退及正常
玩家路徑達 READY 後，才能把介紹長文接正式 Ebitengine 顯示；
最終仍需中文／英文控制與 dosgolem 同狀態驗證。
