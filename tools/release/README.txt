殖民帝國繁體中文化（Colonization CHT）{VERSION}
======================================================

這是 MicroProse 1994 年 DOS 版《Sid Meier's Colonization》的繁體中文顯示層。
原版程式與資料不做修改，由內建的 dosgolem 模擬執行，本程式只在畫面上疊加中文。

目前內容
--------------------
- 開場製作名單的職稱、主選單、難度與國家選擇、姓名提示、四國首次介紹
- 英國開局的十張開場字幕、首則教學提示（發現者難度）
- 海上主畫面的選單列、回合訊息與右側狀態欄
- 遊戲選項視窗、退休確認框
- 對話框、原住民學習選項、存讀檔標題與正常槽位、成功提示
- 殖民地、歐洲港口、議會與已抽樣報表，百科六類150篇正文
- 下拉選單、貿易路線與三種事件版畫標題

全遊戲文字譯稿已完成，仍有部分畫面接線與情境待驗，會保留原文。
詳細顯示範圍見原始碼儲存庫 README.md 與 CONTEXT.md。

你需要準備
----------
1. Linux x86_64桌面，有X11、OpenGL、ALSA、glibc及bash。
   AppImage封裝已在Debian12隔離桌面驗證；其他系統未逐一驗證。
2. 自己合法取得的 DOS 版原版遊戲目錄（含 VICEROY.EXE 的 COLONIZE 目錄）。
   本包不含任何原版檔案。原版檔案的 SHA-256 必須與 MANIFEST.json 列出的相同，
   否則程式會拒絕啟動，不會套用中文。

執行
----
AppImage格式：
    chmod +x colonization-cht-{VERSION}-linux-x86_64.AppImage
    ./colonization-cht-{VERSION}-linux-x86_64.AppImage --game /你的路徑/COLONIZE

FUSE不可用時，在檔名後先加 --appimage-extract-and-run。
tar.gz格式解包後：
    ./colonization-cht.sh --game /你的路徑/COLONIZE

- 原版目錄只會被讀取，不會被寫入。
- 存檔寫到 ~/.local/share/colonization-cht/save（可用環境變數
  COLONIZATION_CHT_SAVE 改位置）。

操作與限制
--------------
- 預設開啟音樂與音效；需要靜音時可加 --audio-mute。
- 鍵盤轉送可列印字元、Backspace、Enter、Esc、方向鍵、F1～F10（含 Shift／Ctrl／Alt
  組合）、數字鍵盤、Home／End／PgUp／PgDn 與 Alt／Ctrl 加字母；輸入法與非英數字元不轉送。
- 遊戲節奏以模擬器步數推進，與原版實機速度不同。
- 此封包是Linux版本；其他平台的驗證範圍另行記錄。

授權
----
本作品採「復古重製 source-available 授權條款 1.0（RRSAL-1.0）」，全文見 LICENSE。
非商業用途免費，可修改與再散布；實況、影片、評論不算商業使用。商業用途請先洽
wicanr2@gmail.com，歡迎來談。這不是開放原始碼（open source）授權。

- 原版遊戲的檔案、畫面、文字與說明書屬於 MicroProse 及其權利承繼人或各自的權利人，
  不在本授權範圍內。
- 中文字型俐方體11號（Cubic 11）與以它烘製的字模依其授權散布，見
  LICENSES/Cubic-11-OFL.txt。
- AppImage格式另附runtime及其靜態元件授權；runtime重建腳本、libfuse修補與
  完整來源附在LICENSES/AppImage-sources。X11、ALSA、glibc與OpenGL由系統提供。
- 本作品與 MicroProse、其權利承繼人及第三波沒有任何隸屬或授權關係。

原始碼與問題回報：https://github.com/wicanr2/colonization_cht
