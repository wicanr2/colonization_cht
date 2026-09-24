# 目標124：真視窗方向鍵與離頁鍵的正常玩家路徑

狀態：完成（限此輪輸入通道驗收）；日期：2026-09-24。承接[規格024](../spec/024-window-keyboard-input.md)已限定驗收的姓名輸入、[目標110](110-tutorial-hints-player-trigger.md)／[目標111](111-tutorial-hints-state-and-first-help.md)的原版海上左方向鍵、Esc 與 Space 消費證據，以及[目標123](123-retire-confirmation-and-help-route.md)對 help 尚未正式顯示的停止線。對應既有 [Issue #14](https://github.com/wicanr2/colonization_cht/issues/14) 與 [Issue #29](https://github.com/wicanr2/colonization_cht/issues/29)；不建立同義 Issue。

## 玩家問題與證據邊界

現行 Ebitengine 視窗可把字母、數字、空格、退格與 Enter 送進原版，但未送方向鍵或 Esc。dosgolem 固定提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f` 的具名 BIOS 鍵表已有 `Left`／`Right`／`Up`／`Down`／`Escape`，不需在本專案另猜掃描碼。原版英格蘭海上左方向鍵、選項視窗 Esc 在正常玩家路徑已證實被消費；其餘方向鍵在本遊戲的效果仍未知。畫面文字仍只有十七段正式中文，24則 help 僅譯稿、正式顯示零則。

## 工作與退出條件

1. 核對乾淨 Git、PRIVATE 遠端、既有 Issue、合法原版 SHA、隔離 dosgolem 禁推與固定 Docker 映像；**先推送本 goal Markdown**，再改前端或新增重播。分析、建置、測試、GUI 與原版只在無網路、限資源、非 root 的一次性 Docker；原版唯讀，輸出只在已忽略且目前使用者持有的 `workplace/`。
2. 先回讀規格024、原版左鍵／Esc／Space 收據、dosgolem 具名鍵映射及鎖版 Ebitengine 按鍵 API；把五個具名鍵的輸入事件、焦點、按下一次、舊收據相容、未知鍵拒絕及回退條件審查進規格024的**獨立擴充段**。現有姓名輸入 CONFORMED 範圍不因草案被降級；新範圍未 READY 前不得接正式前端。
3. 若擴充達 READY，只在 `tools/window_prototype.go` 加入 Esc 與四方向鍵的 Ebitengine→dosgolem 具名鍵轉送與可重播事件；空格沿既有單字元路徑，驗證不會雙送。不得注入 RAM、改原版 EXE／TXT 或替遊戲定義新鍵語意。鍵盤焦點或非法事件須安全拒絕；測試覆蓋 BIOS 字組、事件序列、舊收據、失焦及鼠鍵回歸。
4. 由合法 DOS 原版冷啟動，以真 Ebitengine／Xvfb 視窗沿已驗滑鼠與 Enter 路徑走到英格蘭海上畫面，實際送左方向鍵並觀察原版鍵盤佇列及畫面；另到 `Game Options` 實際按 Esc 離頁。保存視窗輸入收據，分別重播中文與英文控制；核對原版 CPU、完整 RAM、索引／畫布／色盤、時間、開檔及終點畫面一致。若受前端工具限制，明列限制並保持擴充未 CONFORMED，不能拿無頭輸入冒充真視窗。
5. 建立獨立正反例與缺合法原版 `SKIP 77`；只在上述真視窗和同狀態契約均通過後把規格024的新範圍標限定 CONFORMED。回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、唯一 `docs/worklist.json` 並重生 `WORKLIST.md`，私有推送、更新並回讀 Issue #14／#29。核對原版素材未入 Git、輸出 UID/GID、誤建 root-owned 目錄和 Docker 容器清理。

## 停止線

這輪只擴展**玩家輸入通道**，不宣稱四方向在殖民地或所有選單都有相同效果，不增加正式中文段數，不把 `@TUTORIAL1` 預讀提升為顯示。若真視窗只能抵達已驗早期頁面，仍須保留具體缺口；正常玩家 GUI 路徑不能由直接注入事件或無頭收據取代。第三難度卡、遊戲選項和字幕的 A／B 字級仍各自待使用者決定，與本目標無關。

## 執行收據與結果

- 目標文件先以 `3018096` 推送私有 `origin/main`，才修改前端。隔離 dosgolem `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；視窗來源 SHA-256 `2e6d4238d4ed0a49797e6750c2ca5135345c2120a17bbd93aafce01f992ee1eb`。固定原版檔案 SHA 見規格024及驗證器；不符即拒絕。
- 真 Ebitengine／Xvfb 視窗的玩家輸入 SHA-256 `dfc4d5cb870efd45c173f7b2eb8fede711bb2951d2204053af92701a8dde5c98`；五次 Enter 到英格蘭海上，於1,225,400,000步實按左鍵、於1,290,400,000步在 `Game Options` 實按 Esc。前後真視窗圖呈現船隻左移、選項視窗開啟及關閉。相同收據重播英文控制，原版 CPU、完整 RAM、原版索引與色盤、開檔與終點相同；終點索引 SHA-256 `95e4fb3efcd7cf0391f46767711274096221d305da97885ed7a1d2f1e06d61c0`。
- 各自只拿掉左鍵／Esc 的本機反向收據，終點原版索引分別為 `52b9f726c7406a05ce924cda118ff64bb2d909e947a710e4ec972b2ab6a6d1df`／`8351344cd5e04e6600b115b2ddb8b8cae8c80350cad5973d922d65e12d4cf427`，均與真路徑不同。失焦真視窗左鍵沒有進收據或於聚焦後補送，與英文控制完整原版狀態相同。舊姓名真視窗收據由新前端重播，原版狀態、開檔、完整 RAM、索引及色盤均與舊控制完全相同。
- `tools/check_goal124_keyboard.py` 正例 PASS；`tools/test_goal124_keyboard.py` 缺原版 `SKIP 77` 及八類錯版、篡改與失焦負例 PASS。Go 測試與建置於有界 Xvfb／Docker 通過；第一次沒有 `DISPLAY` 的 GLFW 初始化失敗只屬測試環境。原版截圖、記憶體與輸入收據留在已忽略的 `workplace/reports/goal124-keyboard/`，不加入 Git。新鍵僅此固定路徑限定 CONFORMED；右／上／下的遊戲效果、首則 help 及正式中文新增均未驗。
