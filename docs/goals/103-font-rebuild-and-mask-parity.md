# 目標103：以固定原始字型重烘十七欄本機字模

狀態：進行中；日期：2026-09-24。承接[目標102](102-nation-introduction-layout-prototypes.md)
找回的 Cubic 11 固定來源與[字型入口](../../font/README.md)，對應
[Issue #12](https://github.com/wicanr2/colonization_cht/issues/12)及
[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)。

## 玩家問題與本輪界線

目前十七段正式中文顯示使用本機字模；其中十五段已有原始字型的
烘製腳本，但第一張國家旗卡兩欄曾因原始 TTF 遺失，只能從固定
的已驗原型提取。現已找回相同 SHA-256 的原始字型，本輪要證明
**全部十七欄能從合法原版、真實 TSV 與固定字型獨立重烘**，
而不是只重用歷史本機字模。成果只改善重現性，不擴張正式中文
覆蓋欄位、不改任何字級或玩家流程。

四國介紹長文仍待使用者從目標102的對照圖選版；本輪不替使用者
選擇，也不把其 DRAFT 原型接入 Ebitengine。原版 EXE／資料、
存檔、規則與原始字型都不進 Git。

## 工作與退出條件

1. 核對私有遠端、Git 身分、Issue 現況及乾淨工作樹；**先推送
   本目標**，再修改字模工具。保留 `workplace/dosgolem` 的
   `upstream` 推送位址 `DISABLED`。所有分析／烘製／檢查僅在
   限資源、無網路、非 root 的一次性 Docker 容器內執行。
2. 以 SHA-256 固定 `Cubic_11.ttf`、`GAME.TXT`、相關 TXT 與
   TSV；沿既有 `tools/bake_goal084_fonts.sh` 重烘十五欄，
   逐欄比較原有已驗字模的尺寸、字級、譯文指紋及 Alpha bytes。
   任一輸入缺失或指紋不符時失敗即關閉，不以相似字型替代。
3. 只為第一張旗卡使用者已選 A 的兩欄建立原始 TTF → Alpha
   的可重跑入口；沿[規格021](../spec/021-nation-card-red-text-draft.md)
   固定 21／25px、譯文、原版安全矩形及字形尺寸，與目標099
   兩份歷史已驗字模的 Alpha bytes 逐位元組比對。若不相同，
   分析版本或繪製環境差異並維持既有正式字模，不改產品輸出。
4. 建立獨立驗證器與正反例：正例須覆蓋十七欄及來源／輸出
   指紋；錯 TTF、缺原版、錯 TSV、缺欄或改動 Alpha 必須拒絕。
   只有比較通過才能宣稱「本機可重烘」；Git 不含 TTF 或字模。
5. 回填 `font/README.md`、`CONTEXT.md`、研究與工作紀錄、
   `docs/worklist.json`；由工具重生工作清單。核對原版及衍生
   資產未入 Git、輸出 UID/GID、root-owned／誤建目錄與
   Docker 容器清理；推送私有成果並回讀相關 GitHub Issue。

## 停止線

字模重烘通過只能證明固定輸入與固定繪製環境下的本機資產一致，
不等於字型可公開散布、完整遊戲中文化或新欄位同狀態驗收。
若第一張旗卡新舊 Alpha 不一致，保留差異與原有 CONFORMED
驗收範圍，不以「看起來相近」替代逐位元組證據。
