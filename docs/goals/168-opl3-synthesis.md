# 目標168：OPL3 音樂合成（Issue #47）

狀態：完成；2026-09-30。對應 [Issue #47](https://github.com/wicanr2/colonization_cht/issues/47)，規格見[規格037](../spec/037-opl3-audio.md)。

## 已知

- 使用者 2026-09-27 決定音訊採 ymfm（BSD-3）移植。
- 本遊戲以 Sound Blaster Pro base 0x220 驅動音樂，第一次 OPL 寫入即開啟 OPL3 模式；PIT 分頻 1960（約 608.8 Hz），dosgolem 的計時器中斷間隔已隨分頻調整。
- `audio/opl`（ymfm OPL2／OPL3 的 Go 移植）與機器接線 `EnableOPLSynth` 已在隔離副本 `workplace/dosgolem` 完成，但**在規格 READY 之前**；本目標補齊規格與驗收，驗收通過前不提交進 dosgolem。

## 範圍

1. 規格037：證據、設計、時間基準、驗收。
2. 驗收：開關合成的原版狀態逐位元組相同；同輸入兩次 WAV 相同；dosgolem 既有測試全過；以 DOSBox-X 錄同段音樂做音高與節奏的交叉檢查。
3. 規格升 READY 後，在隔離副本的本地分支提交（不推送，dosgolem 上游推送位址維持 DISABLED）；本專案記錄該提交雜湊。

## 退出條件

規格037 READY 且上述驗收通過；ymfm 授權告知列入發行包清單（#53）。

## 停止線

不做前端播放（#49）與數位音效（#48）。

## 結果

- 規格037 READY，驗收見規格：開關合成不影響原版狀態；本遊戲實際 OPL 寫入序列 62.2 秒與 ymfm C++ 原版逐樣本相同；同輸入兩次 WAV 逐位元組相同；dosgolem `go test ./...` 全過。
- 提交：隔離副本 `workplace/dosgolem` 本地分支 `colonization-audio` 的 `a3a5609`（未推送，上游推送位址 DISABLED）。
- ymfm 授權（`audio/opl/LICENSE.ymfm`，BSD-3-Clause）須隨發行包附上，已記入 [#53](https://github.com/wicanr2/colonization_cht/issues/53)。
- 未做：DOSBox-X 錄音交叉檢查（見規格037「未做」）。

## 移交

- 音效卡初始化時的 DSP DMA 測試在 dosgolem 中得不到 IRQ，驅動因此判定數位音效不可用；數位音效（`COLDIG.BIN`）的取證與 DMA／IRQ 實作由 [#48](https://github.com/wicanr2/colonization_cht/issues/48) 處理。
