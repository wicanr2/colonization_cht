殖民帝國繁體中文化（Colonization CHT）技術預覽版 {VERSION}
======================================================

這是 MicroProse 1994 年 DOS 版《Sid Meier's Colonization》的繁體中文顯示層。
原版程式與資料不做修改，由內建的 dosgolem 模擬執行，本程式只在畫面上疊加中文。

目前能看到中文的畫面
--------------------
- 開場製作名單的職稱、主選單、難度與國家選擇、姓名提示、四國首次介紹
- 英國開局的十張開場字幕、首則教學提示（發現者難度）
- 海上主畫面的選單列、回合訊息與右側狀態欄
- 遊戲選項視窗、退休確認框

其餘畫面仍是英文。全遊戲文字的譯稿已完成草稿（見原始碼儲存庫 text/），
但還沒接到畫面上。

你需要準備
----------
1. Linux x86_64，有 X11 與 OpenGL 的桌面環境。
2. 自己合法取得的 DOS 版原版遊戲目錄（含 VICEROY.EXE 的 COLONIZE 目錄）。
   本包不含任何原版檔案。原版檔案的 SHA-256 必須與 MANIFEST.json 列出的相同，
   否則程式會拒絕啟動，不會套用中文。

執行
----
    ./colonization-cht.sh --game /你的路徑/COLONIZE

- 原版目錄只會被讀取，不會被寫入。
- 存檔寫到 ~/.local/share/colonization-cht/save（可用環境變數
  COLONIZATION_CHT_SAVE 改位置）。

技術預覽的限制
--------------
- 沒有音效與音樂。
- 鍵盤目前只轉送可列印字元、Backspace、Enter、Esc 與方向鍵；功能鍵（F1～F10
  顧問報告等）、數字鍵盤與組合鍵尚未轉送，請改用滑鼠點選單。
- 遊戲節奏以模擬器步數推進，與原版實機速度不同。
- 只在 Linux 驗證過。

授權
----
本作品採「復古重製 source-available 授權條款 1.0（RRSAL-1.0）」，全文見 LICENSE。
非商業用途免費，可修改與再散布；實況、影片、評論不算商業使用。商業用途請先洽
wicanr2@gmail.com，歡迎來談。這不是開放原始碼（open source）授權。

- 原版遊戲的檔案、畫面、文字與說明書屬於 MicroProse 及其權利承繼人或各自的權利人，
  不在本授權範圍內。
- 中文字型俐方體11號（Cubic 11）與以它烘製的字模依其授權散布，見
  LICENSES/Cubic-11-OFL.txt。
- 本作品與 MicroProse、其權利承繼人及第三波沒有任何隸屬或授權關係。

原始碼與問題回報：https://github.com/wicanr2/colonization_cht
