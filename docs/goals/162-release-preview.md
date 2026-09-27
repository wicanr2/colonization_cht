# 目標162：封裝、授權與技術預覽發布（Issue #15）

狀態：進行中；開始：2026-09-27。對應 [Issue #15](https://github.com/wicanr2/colonization_cht/issues/15)。

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
