# 目標162：封裝、授權與技術預覽發布（Issue #15）

狀態：完成；開始與完成：2026-09-27。對應 [Issue #15](https://github.com/wicanr2/colonization_cht/issues/15)。

## 使用者決定（2026-09-27）

- 公開儲存庫並發布預覽版 Release。
- 譯稿保留原版英文對照；截圖與第三波說明書術語保留，於授權第 2 條 (c) 點名。
- 平台先只做 Linux。
- 授權沿用既定的 RRSAL-1.0。

## 範圍

- `LICENSE`（RRSAL-1.0）、`font/Cubic-11-OFL.txt`、README 授權段。
- 前端遊玩模式 `-play`（不累積逐幀驗證紀錄、未指定時不設步數上限），預設關閉。
- `tools/package_release.py` 產生 `dist-all/<版本>/patch/` 可重現封包與 `SHA256SUMS.json`；啟動器 `tools/release/colonization-cht.sh`。
- smoke：乾淨容器解包，以啟動器重播已驗收的全流程輸入，終點原版狀態與畫面須與目標161 收據相同。
- 公開儲存庫、建立 tag 與 GitHub Release（只上傳 patch 封包與雜湊）。

## 退出條件

- 封包兩次產生逐位元組相同；包內無原版檔案。
- smoke 與回歸通過；README、MANIFEST 與授權聲明一致。
- Release 可下載且雜湊相符。

## 結果

- 授權：`LICENSE`（RRSAL-1.0），第 2 條 (c) 點名截圖、譯稿中的原版英文、量測座標與畫面指紋、第三波說明書術語對照；第三方元件為 Cubic 11（含以其烘製的字模）與 Ebitengine。`font/Cubic-11-OFL.txt` 取自原作者儲存庫（SHA-256 `2b6e5938…`）。README 改寫為現況並加授權、致謝與聲明段；AGENTS.md 公開性條文依使用者決定更新。
- 前端 `-play`（預設關閉；前端 SHA-256 `ae45f0bfeb17a507b23829169a02d3eb58fa2eac54e8bbe6106b0eabe8cd7c0f`）：六點回歸與目標161 基準相同。
- 封包 `dist-all/v.0.1.0-20260927/patch/colonization-cht-v.0.1.0-20260927-linux-x86_64.tar.gz`，SHA-256 `ce985dbee5d4722e3cbe2b19aae3ddec0bb8f2c850163c1be1e1e34d7dfe958e`，77 個檔案：前端、啟動器、七份執行期 TSV、以 Cubic 11 烘製的字模、授權檔、說明與 `MANIFEST.json`（含原版五個檔案的必要指紋）。兩次封裝逐位元組相同；包內無原版檔案。字模複本的 `scope` 聲明改寫為隨包散布的授權說明，避免與發布決定矛盾。
- smoke（`dist-all/v.0.1.0-20260927/smoke/smoke-summary.json`）：乾淨容器解包、清單逐檔雜湊相符。以啟動器重播全流程輸入到 12.9 億步：
  - 不開存檔層：終點原版記憶體、索引與輸出圖和目標161 收據逐位元組相同。
  - 開存檔層：畫面相同，自動存檔 `COLONY09.SAV` 寫進存檔目錄，原版目錄沒有新增檔案；記憶體差異只因寫檔成功。

## 已知限制

- 沒有音效；鍵盤只轉送可列印字元、Backspace、Enter、Esc 與方向鍵。
- 只驗 Linux x86_64；需要 X11／OpenGL。

## 發布

- 儲存庫已公開：https://github.com/wicanr2/colonization_cht
- tag `v.0.1.0-20260927`（指向 `db5b7ab`），預覽版 Release：https://github.com/wicanr2/colonization_cht/releases/tag/v.0.1.0-20260927 ，附件只有 patch 封包與 `SHA256SUMS.json`；重新下載後封包 SHA-256 相符。
