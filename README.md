# 《殖民帝國》繁體中文化（Colonization CHT）

《Sid Meier's Colonization》（MicroProse，1994）是經營殖民地、調配資源與貿易，最後爭取獨立的歷史策略遊戲。本專案讓繁體中文玩家能直接讀懂遊戲裡的選單、訊息與說明。

做法是「顯示轉譯層」而不是重製：原版 DOS 程式、規則、資料與存檔都不修改，由 [dosgolem](https://github.com/wicanr2/dosgolem) 模擬執行；本專案在原版把文字畫到畫面的那一刻辨識出是哪一句，再於放大後的畫面上疊上中文。辨識不到或證據不足的地方保留英文，不猜。

## 下載與執行（技術預覽版）

[Releases](https://github.com/wicanr2/colonization_cht/releases) 提供 Linux x86_64 技術預覽版。需要：

- 有 X11 與 OpenGL 的 Linux 桌面。
- 自己合法取得的 DOS 版原版遊戲目錄（含 `VICEROY.EXE`）。發行包不含任何原版檔案；原版檔案的 SHA-256 必須與包內 `MANIFEST.json` 相同，否則程式拒絕啟動。

```sh
./colonization-cht.sh --game /你的路徑/COLONIZE
```

原版目錄只讀；存檔寫到 `~/.local/share/colonization-cht/save`。預覽版沒有音效；鍵盤目前只轉送可列印字元、Backspace、Enter、Esc 與方向鍵，功能鍵（F1～F10 顧問報告等）、數字鍵盤與組合鍵尚未轉送，相關操作請改用滑鼠點選單；遊戲節奏與原版實機不同。

## 目前狀態

**畫面上已經是中文的部分**（每一欄都有原版事件或畫面指紋證據，並以中英同輸入重播驗證原版狀態不變）：

- 開場製作名單職稱、主選單、難度頁、國家選擇頁與四張旗卡、姓名提示
- 四國首次國家介紹（各兩頁）
- 英國開局的十張開場字幕、首則教學提示（發現者難度）
- 海上主畫面的選單列、回合訊息與右側狀態欄
- 遊戲選項視窗（標題與八列）、退休確認框

**譯稿已完成、但還沒接到畫面上的部分**：全遊戲 TXT 文字的繁中草稿已齊（遊戲畫面分母 3,561 行全部有譯稿），包括百科、教學說明、殖民地名稱、各種對話與報告。這些要逐一畫面取證後才會顯示。

術語以第三波中文版說明書為準，見[定稿譯名表](text/terms.zh-Hant.tsv)。各畫面的驗證結果見[驗證矩陣](docs/verification-matrix.md)，詳細現況見 [CONTEXT.md](CONTEXT.md)。

## 畫面

![Ebitengine 視窗中的繁體中文主選單](docs/screenshots/menu-zh.png)

主選單五列選項由原版印字事件觸發中文；原版大型標題維持英文。

![Ebitengine 視窗中的繁體中文難度頁](docs/screenshots/difficulty-zh.png)

難度頁：兩行標題依原版共同中心線排版，第一張卡片「發現者／最簡單」。

![Ebitengine 視窗中的第一張國家旗卡](docs/screenshots/nation-card-first-zh.png)

國家頁：旗卡兩行依原版字高分別用 21／25px，保留紅字黑影風格。這張截圖拍攝於國名改用說明書譯名之前，現行版本上欄是「英國：」。

四國介紹長文的早期版面對照：[A 頁](docs/screenshots/nation-intro-layout-draft-a.png)、[B 頁](docs/screenshots/nation-intro-layout-draft-b.png)（每列依序為原版與兩種中文候選）。

## 開發與研究入口

所有建置、遊戲執行、分析與抓圖都在 Docker 容器內進行，需要自備合法原版。

- [目前脈絡](CONTEXT.md)、[工作計畫](WORKLIST.md)（由 `docs/worklist.json` 產生）
- [規格](docs/spec/)與[各輪目標](docs/goals/)
- [驗證矩陣](docs/verification-matrix.md)（`tools/verification_matrix.py` 產生）
- [研究證據](RESEARCH-LOG.md)與[工作歷程](WORKLOG.md)
- [字型來源](font/README.md)、[專案規則](AGENTS.md)
- 封裝：`tools/package_release.py`、啟動器 `tools/release/colonization-cht.sh`

## 授權、致謝與聲明

本專案採[復古重製 source-available 授權條款 1.0（RRSAL-1.0）](LICENSE)：非商業用途免費，可修改與再散布；遊戲實況、影片、評論與報導明示允許（含平台分潤）。商業用途請先洽 wicanr2@gmail.com，歡迎來談。這是 source-available 授權，不是開放原始碼（open source）授權。

- **不在授權範圍內**：原版遊戲的執行檔、資料、畫面、文字與說明書，屬於 MicroProse 及其權利承繼人或各自的權利人。儲存庫裡的截圖、譯稿中的原版英文對照、量測座標與畫面指紋、第三波說明書術語對照，其中屬於原版的部分依授權第 2 條 (c) 處理。
- **第三方元件**：中文字型[俐方體11號（Cubic 11）](https://github.com/ACh-K/Cubic-11)與以它烘製的字模依其授權（[全文](font/Cubic-11-OFL.txt)）；[Ebitengine](https://github.com/hajimehoshi/ebiten) 依 Apache-2.0。
- 本專案與 MicroProse、其權利承繼人及第三波沒有任何隸屬、合作或授權關係。
