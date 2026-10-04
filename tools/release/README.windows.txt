殖民帝國繁體中文化（Colonization CHT）{VERSION}
======================================================

這是 MicroProse 1994 年 DOS 版《Sid Meier's Colonization》的繁體中文顯示層。
原版程式與資料不做修改，由內建的 dosgolem 模擬執行，本程式只在畫面上疊加中文。

目前內容
--------
全遊戲文字譯稿已完成。開場、選單、海上狀態、殖民地、歐洲港口、百科、
存讀檔與三種事件標題已有中文顯示；部分畫面接線與情境待驗，會保留原文。
詳細顯示範圍見原始碼儲存庫 README.md 與 CONTEXT.md。

你需要準備
----------
1. Windows x86_64 桌面及支援遊戲視窗的圖形與音訊裝置。
2. 自己合法取得的 DOS 版原版遊戲目錄，含 VICEROY.EXE 的 COLONIZE 目錄。
   本包不含任何原版檔案。原版 SHA-256 必須與 MANIFEST.json 列出的相同，
   否則程式拒絕啟動，不會套用中文。

執行
----
先用 Windows 內建解壓縮展開整個 ZIP。保留 bin、masks 與 text 目錄。
在解包目錄開啟命令提示字元，執行：

    colonization-cht.bat --game "C:\你的路徑\COLONIZE"

原版目錄只會被讀取，不會被寫入。存檔預設寫到：
    %LOCALAPPDATA%\colonization-cht\save
可用 COLONIZATION_CHT_SAVE 環境變數指定其他存檔位置。

操作與限制
----------
- 預設開啟音樂與音效；需要靜音時可加 --audio-mute。
- 鍵盤支援可列印字元、Backspace、Enter、Esc、方向鍵、F1～F10及修飾鍵、
  數字鍵盤、Home、End、PgUp、PgDn；輸入法與非英數字元不轉送。
- 遊戲節奏以模擬器步數推進，與原版實機速度不同。
- 本包只在容器內以 Wine 驗證，不代表 Windows 真機或所有系統相容性已驗。

授權
----
本作品採「復古重製 source-available 授權條款 1.0（RRSAL-1.0）」，全文見 LICENSE。
非商業用途免費，可修改與再散布；實況、影片、評論不算商業使用。
商業用途請洽 wicanr2@gmail.com。這不是開放原始碼（open source）授權。

原版遊戲的檔案、畫面、文字與說明書屬於各自權利人，不在本授權範圍內。
中文字型俐方體11號（Cubic 11）與字模依 LICENSES/Cubic-11-OFL.txt 散布。
Go、Ebitengine、dosgolem、ymfm及其他模組依 LICENSES/ 內各自授權散布。
本作品與 MicroProse、其權利承繼人及第三波沒有任何隸屬或授權關係。

原始碼與問題回報：https://github.com/wicanr2/colonization_cht
