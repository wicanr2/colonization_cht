# 目標114：遊戲選項解析至印字緩衝的最後資料流

狀態：in_progress；日期：2026-09-24。承接[目標112](112-game-options-chinese-display.md)已驗的 `GAME.TXT` 九欄 DOS 讀入、168-byte 原版解析讀取與逐欄印字，以及[目標113](113-game-options-background-and-preview.md)九欄印前底圖／可丟棄 Ebitengine 對照。此輪對應既有 [Issue #7](https://github.com/wicanr2/colonization_cht/issues/7) 與 [Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)，不新增同義 Issue。

## 玩家問題與範圍

`Game Options` 九欄仍是英文。檔案、DOS 緩衝、原版解析讀取、印字讀取與畫布各有直接證據，但解析後到印字字元緩衝的**最後搬運**仍只屬強推論。沒有這一段，就不能把同文的不同緩衝當作已閉合的來源鍵。本輪以原版正常滑鼠開窗路徑追實際字元緩衝寫入者及讀取者，辨別暫存、複製、格式化、熱鍵處理或間接取址，留下可重播的每欄來源關係。原版 EXE、TXT、滑鼠熱區、遊戲規則、存檔與正式中文顯示均不改動。

固定合法 DOS `GAME.TXT` SHA-256 `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`、`MENU.TXT` SHA-256 `5a7d2f4bf9f657b68177fb9b38e74ac92a1f191732bbc122c28563a41d7a3702`；英格蘭正常開局輸入 SHA-256 `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`、後續開窗六筆輸入 SHA-256 `c4e462678323df8e1915ffcd363f7e7eb83cee4e85e09f618c9206418977e539`。原版權威為隔離 `workplace/dosgolem` 提交 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`，其 `upstream` 推送位址維持 `DISABLED`。

## 工作與退出條件

1. 核對乾淨工作樹、Git 作者、PRIVATE 遠端、既有 Issue、原版及隔離 dosgolem；**先推送本目標 Markdown 與 `CONTEXT.md` 入口**，再修改探針。所有原版執行、搜尋大量資料、建置、驗證都在限資源、無網路、非 root 的一次性 Docker；原版唯讀。
2. 讀回目標112／113的當次 `0D21:00C6` 印字讀取記錄，從原版實模式 `CS:IP`、20-bit 線性 RAM、檔案 byte 位移與320×200索引畫布四種位址空間分開列出每欄來源候選。先檢查先前窄寫入監看零筆是否只是時間窗過晚、地址範圍太窄或讀取發生在臨時緩衝，而非宣稱「沒有寫入」。
3. 僅在與九欄開窗相鄰的有界步數監看已確認的印字讀取位址、周圍有限緩衝與其寫入者。逐筆保留原始位址、byte、指令 `CS:IP`、步數及前後緩衝快照；若是間接拷貝，追取址端與最小來源鏈。不得大範圍記錄完整 RAM 或對原版任意函式改名。新觀測須可在雙次獨立冷啟動重生，另跑無觀測控制，核對玩家路徑、CPU／RAM、索引畫布、色盤、時間與開檔不受監看擾動。
4. 建立獨立檢查器與負例：錯原版、錯輸入、來源 byte／RAM 讀寫範圍、時間序、漏九欄、無監看控制分歧均須拒絕；原版缺失應明確 `SKIP 77`。若原版事實仍不足，記明**已排除的時間窗與位址窗**，維持強推論，不編造已證實邊；若資料流已閉合，將固定版位址與回退條件補入[規格027](../spec/027-game-options-window-draft.md)，再審查是否具備限定 READY 條件。
5. 更新 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md` 與 `docs/worklist.json`，由 `tools/worklist.py write` 重生 `WORKLIST.md`；推送 PRIVATE repo，更新並回讀既有 Issue。核對無原版 EXE／TXT／畫素／字型被 Git 追蹤、輸出 UID/GID、誤建 root 目錄及 Docker 容器清理。

## 停止線

本輪的最小可驗成果是最後搬運者的直接位址／指令／byte 證據，或對先前零筆監看原因的可重現訂正。相同英文字串、同一張穩定截圖、通過的中文預覽都不能取代原版資料流；即使來源邊找到，選取／游標／關窗相位與遊戲選項中文字級尚未正式定案，規格027仍不能直接標 CONFORMED，正式已驗中文仍十七段。原版完整收據只放已忽略的 `workplace/`，不推送原版畫素或轉存原文。
