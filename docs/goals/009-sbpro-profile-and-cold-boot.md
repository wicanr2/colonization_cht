# 目標 009：依 READY 規格實作 SBPro／OPL 設定檔並重播冷啟動

狀態：completed（最小 profile 已驗證；後續控制流 blocker 交給 Issue #24）<br>
日期：2026-09-20<br>
對應 Issue：[ #23 ](https://github.com/wicanr2/colonization_cht/issues/23)<br>
授權規格：[READY 規格 002](../spec/002-colonization-sbpro-opl-profile-ready.md)

## 目的

在 `workplace/dosgolem` 的隔離 Git 副本，依 READY 規格 002 將最小的 base `0x220`
Sound Blaster Pro／OPL 設定檔接到一般 `Machine` 與 `cmd/probe -sbpro`。以固定的正式
`OPENING.EXE → PSOUND.COL` state 重播，確認 DSP reset 的第一個有效回應是 `0xAA`，並取得
下一個可見畫面、程式轉交或新的最小 blocker 收據。

## 固定前提

- 原始輸入只讀取使用者指定的 DOS `COLONIZE/` 目錄；`OPENING.EXE` SHA-256 為
  `3c08c4af3a709e155cb0ae043c9a2813b5cd34ed4bb0a1a3a0b12e7fa54d0d39`，`PSOUND.COL`
  SHA-256 為 `8d5069fab621abfa5a4df4071612aa0d9f159c0907e51f0b1a193b73fa8b5c87`。
- 起點固定為 `workplace/reports/opening-1000000-visible-20260920.state`，SHA-256
  `21a8fc960cb71e806391d6637e16f735a18767dd588e87f221bdeda71aabc2ab`；這是正常冷啟動
  的延續，不使用 `VICEROY.EXE` direct-entry。
- 改動只可在 `workplace/dosgolem`（起始 commit
  `d9c0c27ca9af8239c7e96272a7165e03d7da04bf`）進行；不得修改
  `/home/anr2/cht/dosgolem`、原始資料或把原版輸入加入 Git。

## 執行項目

1. 新增預設為關閉的 `cmd/probe -sbpro`；啟用後直接設定一般 `Machine` 的 base `0x220`
   profile，並啟用既有 AdLib timer 模型。不得挪用帶有 DMA／PIC／時鐘狀態的 `LEOPLPorts`。
2. 將 `0x220/0x221`、`0x222/0x223` 分別接到既有 primary／secondary OPL bank；`0x220`
   讀取使用既有 OPL status，`0x222` 明確固定為本遊戲 delay 的 `0xFF` 回退。
3. 只將 `0x226`、`0x22A`、`0x22C`、`0x22E` 接到既有受限 `SoundBlasterDSP`，保留實體 port
   的讀取計數、寫入記錄與每次 I/O 恰好一次 tick。未證實的 mixer、DMA、PCM、PIT、IRQ、
   DAC 與其他基址不納入本輪。
4. 新增機器層測試：預設關閉的回退不變、primary 偵測、兩個 OPL bank 獨立、`0x222=0xFF`
   的受限差異、DSP reset／`0xAA` handshake、`0x22C` busy／ready，以及實體 port 恰好一次記錄。
5. 用同一 clone commit 對固定 state 執行預設與 `-sbpro` 兩組 probe（至少到第 2,000,000
   指令），記錄完整命令、輸入／state 雜湊、關鍵 `CS:IP`、`0x22A` 回應、EXEC、VRAM 與未實作
   服務；若已跨過本來 blocker，再延長正式路徑以取得可見／轉交收據。

## 停止線

- 任一原版第一次 DSP command 不屬於既有受限模型時，記錄 command、callsite、consumer 與
  可見後果，回到新的 DRAFT；不得猜測支援。
- `0x222=0xFF` 是未被本版控制流消費的決定性回退，不能稱為 OPL3 硬體 parity。
- 成功的單元測試或 reset 不等於首畫面、可玩性、音訊完成或中文化完成。

## 退出條件

- [x] dosgolem 隔離副本的程式與測試通過，且有可回查的本地 commit `1b0efdf`；上游推送仍為 `DISABLED`。
- [x] 固定 state 的預設／`-sbpro` 同狀態收據證明 profile 組在第一個可用 reply 讀到 `0xAA`，
  而非耗盡 64 次；所有差異均有範圍註記。
- [x] 無首畫面或轉交；`RESEARCH-LOG.md` 與 [Issue #24](https://github.com/wicanr2/colonization_cht/issues/24)
  記錄新的最小控制流 blocker，而沒有擴張裝置模型。
- [x] `README.md`、`CONTEXT.md`、`docs/worklist.json`、`WORKLIST.md`、`WORKLOG.md` 與 Issue
  #23 同步，Docker 容器清理、權利邊界及 Git 狀態均已核對後提交推送。
