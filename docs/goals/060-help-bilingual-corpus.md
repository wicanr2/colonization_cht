# 目標060：遊戲內說明訊息雙語語料

狀態：completed（檔案來源與譯文草稿；畫面未驗）<br>
日期：2026-09-22<br>
Issue：[#27](https://github.com/wicanr2/colonization_cht/issues/27)、
[#7](https://github.com/wicanr2/colonization_cht/issues/7)

## 範圍與權利

依使用者要求，先在[雙語TSV](../../text/help-bilingual.tsv)保存原文與繁中譯文：
`GAME.TXT`的`@TUTORIAL1`至`@TUTORIAL19`（19則），以及`MAPEDIT.TXT`的
`@HELP1`至`@HELP5`（5則）。這24則是檔案中明確標示的教學／說明區塊，
不是所有遊戲提示、百科、安裝README或EXE內文字的完整清冊。

原文僅依本輪明確授權存入`wicanr2/colonization_cht`**私有**儲存庫；
不得轉推公開repo、Release或一般發行包。只收這些文字訊息，不納入原版資料檔、
執行檔、圖像或足以重建遊戲素材的輸出。公開散布權仍未知。

## 資料契約與驗證

每列是整則訊息，含來源檔名與SHA-256、章節位移、文字位移／長度、文字片段SHA-256、
原文、繁中譯文與狀態。TSV以UTF-8保存，原始CRLF只在欄內以字面`\n`表示；
原版英文折行照錄，中文折行留待畫面幾何審查，不能將兩者位置一對一套用。
固定輸入為`GAME.TXT` SHA-256
`67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`與
`MAPEDIT.TXT` SHA-256
`764a67a9ff8f45b9ac9d82809ad616e2c350ff0172d9147ad34478828af57516`。

[重建／驗證工具](../../tools/build_help_bilingual.py)在Docker內唯讀讀取合法DOS原版，
核對24個唯一區塊、原文位元組、原始檔與片段SHA、欄數、UTF-8、占位符、
大括號及`^`等控制碼；譯文缺漏或孤兒鍵失敗即關閉。Cubic 11 24px對譯文
沒有缺少可列印字形。[六項回歸測試](../../tools/test_help_bilingual.py)涵蓋控制碼、
變數、重複鍵、BOM及不合法跳脫。重跑時只需提供原版目錄及版控TSV：

```sh
python3 /repo/tools/build_help_bilingual.py --game /game --catalog /repo/text/help-bilingual.tsv
```

容器掛載、UID/GID與資源限制沿用專案`AGENTS.md`，`/game`和`/repo`唯讀；
本輪沒有把原版整檔或解包物加入Git。草稿的`message_id`是檔案章節鍵，
**不是已證實的執行期顯示鍵**。本TSV是審校工作表；正式顯示譯文仍須按
RE證據→READY規格整合到唯一執行期語料，不能讓兩份譯文同時驅動同一訊息。

## 保留缺口

24則均未取得dosgolem實際顯示事件、中文安全矩形或Ebitengine畫面驗收；
`GAME.TXT`其他幫助訊息、地圖編輯以外的說明文字與靜態圖文仍待盤點。
不把這24筆加到既有189筆已來源驗證的主目錄分母，更不宣稱畫面覆蓋由五筆增加。
