# 規格040：前端音訊輸出

狀態：READY（2026-09-30；依據為規格037、039 的 dosgolem 介面與 Ebitengine v2.9.9 `audio` 套件）；DRAFT 2026-09-30（[目標176](../goals/176-frontend-audio.md)，[Issue #49](https://github.com/wicanr2/colonization_cht/issues/49)）。

## 旗標

- `--audio`：開啟 dosgolem OPL3 合成（`EnableOPLSynth(true)`）與前端播放。搭配 `--sb-digital` 時數位音效一併混入（規格039）。
- `--audio-wav <路徑>`：結束時把前端從 `DrainAudio()` 取得的全部原始取樣（dosgolem 取樣率、交錯 int16 立體聲）寫成 WAV。需同時開 `--audio`。
- `--audio-mute`：只合成與錄音，不開播放裝置（無音效裝置的容器與測試用）。

## 設計

1. **取樣來源：**每次 `Update` 推進完指令後呼叫一次 `DrainAudio()`，同一批取樣同時交給 WAV 錄製與播放串流。取樣內容只由指令數與 OPL／DSP 寫入決定，所以同輸入的真 GUI 與重播逐位元組相同。
2. **播放：**Ebitengine `audio.NewContext(48000)`，播放器讀一個串流：把 49,715 Hz 取樣以線性內插換成 48,000 Hz 的 16 位元立體聲。串流不足時補靜音；積壓超過 0.25 秒時丟掉最舊的部分，只留 0.1 秒。播放與丟棄都不影響模擬。
3. **時序不回饋：**模擬節奏維持每次 `Update` 200,000 道指令，不因音訊緩衝等待或加速；開關音訊時原版狀態與時間必須完全相同。
4. **失敗不中止：**音效裝置開不起來時記錄錯誤、改為靜音繼續（WAV 照錄）。

## 驗收

1. 同輸入重播，開與不開 `--audio`：終點狀態、檢查點、完整記憶體與截圖逐位元組相同。
2. 真 GUI 以 `--audio --sb-digital --audio-wav` 錄音；同輸入重播錄出的 WAV 逐位元組相同；開場、海上、建城木刻各區段 RMS 明顯高於靜音。
3. 容器內以 ALSA null 裝置跑真 GUI，播放器實際被讀取（記錄已送出的位元組數），程式不中止。
