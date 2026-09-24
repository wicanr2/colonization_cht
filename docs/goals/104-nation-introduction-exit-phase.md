# 目標104：其餘三國介紹 B 頁離頁與輸出相位

狀態：completed（僅三國 B 頁離頁原版證據）；日期：2026-09-24。承接[目標101](101-nation-introduction-player-path.md)
的四國八節正常玩家路徑、[目標102](102-nation-introduction-layout-prototypes.md)
的印字前底圖及[規格025](../spec/025-first-nation-introduction-draft.md)，
對應 [Issue #30](https://github.com/wicanr2/colonization_cht/issues/30)。

## 玩家問題與範圍

法國第二頁後的無輸入／Enter／ESC 只有有限原版收據；英格蘭、
西班牙與荷蘭的 B 頁後離頁尚未驗。若中文長文在離頁後仍留下，
會遮住下一個畫面；但不能由法國的畫面結果推定其他國家或兩個
按鍵的內部語意相同。本輪沿既有 dosgolem 正常滑鼠／姓名／
A→B 路徑，逐國量 B 頁留置與按鍵後的原版畫面、記憶體、
開檔和畫布寫入相位，補足 DRAFT 的**離頁守門證據**。

本輪不選擇目標102的中文排版，不修改正式 Ebitengine 輸出、
原版 EXE／TXT、姓名、規則或存檔；正式中文顯示仍是十七段。

## 工作與退出條件

1. 先核對 Git 身分、PRIVATE 遠端、Issue #30 OPEN 與乾淨
   工作樹，**先推送本目標**再修改探針。沿用固定合法 DOS
   版 SHA、十六筆玩家輸入與 `workplace/dosgolem` 隔離副本；
   原版唯讀，收據只留已忽略的 `workplace/`。
2. 讓既有 `tools/probe_goal098_intro.go` 在 `-after-b` 分支
   可觀測 75M–85M 指令的原版印字和畫布改色，但將該相位
   與 A、B 本文分開；不增加原版輸入、不改機器行為。預設
   `-after-b none` 收據必須保持與目標101一致。
3. 對英格蘭、西班牙、荷蘭各由正常玩家路徑實際進入 B 頁，
   分別做無輸入、Enter、ESC 到 85M。每一分支至少兩次
   獨立冷啟動與一次無讀寫觀測控制，核對 75M 的共同起點、
   80M／85M 索引畫面、色盤、CPU、完整 RAM、虛擬時間、
   開檔序列與有無下一畫面事件；不能只靠檔名猜畫面。
4. 建立獨立驗證器，逐分支核對原始 `.idx`／`.canvas`／`.pal`
   bytes、兩次重播、無觀測控制，以及對照各國已驗 B 頁。
   若不同國家或按鍵結果不同，逐國記錄；即使下一可見畫面
   一樣，也不可宣稱 RAM／CPU 或遊戲語意等價。原版缺失
   時明確 SKIP；錯版或錯相位失敗即關閉。
5. 更新規格025、`CONTEXT.md`、`RESEARCH-LOG.md`、
   `WORKLOG.md` 及唯一 `docs/worklist.json`，由工具重生
   `WORKLIST.md`。推送私有成果並回讀 Issue #30；檢查
   原版素材未入 Git、輸出擁有權、誤建目錄、隔離上游禁推
   與 Docker 容器清理。

## 停止線

B 頁離頁證據只支援正式覆蓋將來的反向守門，不會自動授權
中文字級、事件鍵或正式圖層。使用者尚未選定長文版式；
規格025維持 DRAFT，直到版面、頁相位、游標、缺譯回退與
真視窗同狀態各自取得適用證據。

## 結果與限制

- 目標101的 `-after-b none` 英格蘭新舊 JSON 逐位元組一致。
  本輪英、西、荷三國的無輸入、Enter、ESC 各有兩次獨立
  冷啟動及一次無讀寫監看控制，共27份新報告；75M 的
  完整樣本與三種原始畫布對回目標101，80M／85M 各分支穩定。
- 無輸入仍留原 B 頁；Enter／ESC 各經原版 `0C9F:00CA`
  清屏、`0D21:012C` 新頁印字，開檔從55增至60。
  三國的兩鍵可見索引、畫布、色盤相同，但完整 RAM 不同，
  不推論內部或後續玩法等價。
- `tools/check_goal104_nation_intro_exit.py` 核對固定原版版本、
  玩家輸入、雙重播、無監看控制、各樣本的原始 bytes、
  開檔及事件；`tools/test_goal104_nation_intro_exit.py` 的
  缺原版 SKIP、錯版本及改動單一畫素的反例通過。
  本機 `workplace/reports/goal104-intro/receipt.json` SHA-256
  `92bdc7335ced5740da04c6a2d7707520f85f832d7aa8174a9c71aaa2f6646ccf`。
- [規格025](../spec/025-first-nation-introduction-draft.md)仍為
  DRAFT，正式長文中文覆蓋與真 Ebitengine 驗證尚未完成；
  第一張旗卡 A 版21／25px不自動決定這組長文的字級。
