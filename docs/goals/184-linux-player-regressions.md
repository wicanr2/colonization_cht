# 目標184：Linux 正常啟動的速度、爆音與主選單恢復

狀態：v.1.0.2音樂修正版已驗收及發布。原速獨立音樂即時缺樣0；曲尾等待下一首及數位音效路徑保留，主選單持續英文未重現。入口為[目前脈絡](../../CONTEXT.md)，對應[Issue #53](https://github.com/wicanr2/colonization_cht/issues/53)。

合成效能契約見[規格045](../spec/045-linux-runtime-performance.md)，使用者選定的原速獨立播放見[規格046](../spec/046-independent-music.md)。

dosgolem基底為`b0bf25963ce5a29fb3a3fcf92e211423d4cd4ac8`，本輪作品中立的輸出優化保存於[補丁](../../tools/dosgolem-overlay-performance.patch)，只套用到本專案隔離副本；shared dosgolem與upstream推送設定不變。

使用者實際執行 `v.1.0.0-20261005/full-local/` 的 Linux `start.sh`，回報速度慢、音樂爆音，以及主選單滑鼠移開後中文仍回退英文。先以同一個啟動器重現並量測，不用先前 ALSA null 播放或 WAV 解碼成功替代即時播放驗收。

- [正常啟動探針](../../tools/probe_linux_regression.py)：有界 Docker/Xvfb 執行實際啟動器，保存懸停前、懸停中、移開後的畫面、狀態與時間。
- [CPU 採樣器](../../tools/profile_linux_replay.py)：在忽略的工作目錄複製來源，僅採樣副本加入分析掛勾，不修改正式程式。
- 中間證據位於 `workplace/reports/goal184-linux/`。原版唯讀，所有輸出由 UID/GID 1000:1000 建立。

退出條件為找到各現象的可重現原因，依既有或補充 READY 規格修正；主選單五列懸停後恢復、正常點擊與原版狀態相同；同輸入原始 WAV 不變，播放供給與耗用依真實時間量測。修正版另立版號，不覆寫已發布版本。README 百科截圖與影片配樂改善延續使用者先前要求。

## 2026-10-05 已驗結果與限制

| 項目 | 結果與本機收據 |
|---|---|
| 舊版瓶頸 | `old-gui/timing.json`：正常50M指令115.890秒。`old-profile/cpu-top.txt`：重複整幀解碼占CPU主要成本。 |
| 合成器 | 隔離提交`c83740bc5fcb2f2d8f2afb5d57cee6e92bd12f75`；`oracle-result-v2.json`的128例RGBA與逐欄結果全等。25停用層20幀約快114倍，僅限合成器局部。 |
| 正式正常GUI | `final-gui/timing.json`：50M指令36.203秒，約快3.2倍；五列中文移開後恢復。不同主機負載與軟體繪圖會影響耗時。 |
| 私用一鍵入口 | `private-gui/`：實際新版`start.sh`正常50M指令12.208秒，懸停後五列恢復中文。此批與另一批AppRun耗時不同，保留兩筆，不外推固定倍率。 |
| 預設執行上限 | `unbounded-gui/`不傳`--window-steps`，執行110.2M指令後正常關窗。修正已發布前端仍用原型100M上限的問題。 |
| 主選單恢復 | `sweep-gui/`14組正常懸停、邊界及移到空白操作全部恢復五列。正式GUI再驗通過。使用者所述的持續英文未重現，不宣稱已修好。 |
| 使用者輸入 | `user-run/`是使用者本機last-run紀錄的唯讀副本；`user-replay-taipei/`在台北時區重播後，完整原版狀態、事件及終點PNG全等。兩個空白處檢查點均有五列中文。 |
| 百科抽樣 | `pedia-replay/`對`pedia-control/`：正常百科輸入的CPU、RAM、索引、色盤及原始WAV全等，建築正文顯示中文。比較摘要為`same-state-final.json`。 |
| 播放層 | 缺樣與恢復採5ms連續淡出／淡入，增加`underrun_bytes`；Go測試與go vet通過。原始錄音、音高、取樣率及DOS時鐘不變。仍可能停頓，沒有即時音訊人耳驗收。 |

使用者實際舊版播放器讀取17625600位元組，對應約91.8秒；原版只產生267872幀、約5.39秒音訊。這證實供給明顯不足，與音訊檔案能解碼是不同問題。容器ALSA null也不能作為硬體實聽證據。

首輪使用者重播只有RAM線性偏移`0x67688`一位元組不同。dosgolem `internal/dos/find.go`以當地時區打包檔案時間；原使用者為台北，首輪容器為UTC，兩者差8小時。改用`TZ=Asia/Taipei`後完整RAM相同。原始失敗收據保留，這是驗證環境差異。

## README 截圖與配樂

使用者本輪明確授權README中文百科截圖。公開[皮衣廠截圖](../screenshots/colonizopedia-zh.png)來自既有正常GUI第330600000步，正文與建築先決條件為中文。PNG SHA-256 `e05b0d761d226a2743666f93925251ad47b0e69f42d72d9a2e09f0af4deedd95`；來源為`goal180-pedia-rest/building-final-v3/gui-pedia.building-article-14.png`及`gui-pedia.shots`，正常輸入SHA-256 `217af6321b916e9e79f236dc3ed78d03329e5f80c913387a79689b945a7c4eba`。其他原始畫面不新增公開。

影片改錄原版連續約95秒音樂，使用第3～93秒，取消舊版四段26秒循環。二階段響度校正目標−18 LUFS、峰值上限−2 dBTP，首1秒淡入、尾3秒淡出，沒有改音高或節奏。成片實測−17.9 LUFS、真峰值−2.5 dBFS，90秒1920×1080／30fps H.264／AAC。八幀字幕與中文百科畫面抽看通過，黑幀0；仍是正常玩家截圖剪輯，音樂未人耳確認。

長錄音原始WAV SHA-256 `eb247dfde548651797f76d6b9e1b934b59c112d17f2de454ce660a857d1b0263`，前50M音訊與舊正式版全等。原始WAV及收據只留`music-continuous/`；公開只附成片，沿用使用者既有影片音樂授權。

## 修正版重建入口

沿[目標183](183-release-and-promo.md)的容器與三平台流程，設定`COLONIZATION_RELEASE_WORK=/repo/workplace/reports/goal184-linux/release`，版號使用`v.1.0.1-20261005`。源碼先以`tools/build_window_prototype.py`組裝，dosgolem基底套用本頁補丁，`upstream`推送仍為`DISABLED`。共享dosgolem不修改。

| 工作 | 入口與必要參數 |
|---|---|
| 獨立合成比較 | [verify_compositor_optimization.go](../../tools/verify_compositor_optimization.go)。在隔離Go模組`compositor-oracle`內以`git show b0bf259:overlay/...`取舊package到`legacy/`，目前dosgolem模組用replace指向已套補丁的副本；完整暫存模組在`oracle/`。 |
| 正式封包 | [package_three_platforms.sh](../../tools/package_three_platforms.sh)傳版號；[檢查器](../../tools/check_release_packages.py)傳`--batch`與`--version`。 |
| 啟動與同輸入 | [smoke_release.sh](../../tools/smoke_release.sh)、[replay_release.py](../../tools/replay_release.py)沿上述環境變數；[check_release_smoke.py](../../tools/check_release_smoke.py)傳`--batch`與`--version`。 |
| 回歸重播 | [replay_linux_checks.py](../../tools/replay_linux_checks.py)傳二進位、真實輸入、獨立輸出，可傳存檔種子及檢查點；只有此輪譯稿／字模未變時才沿用目標183圖集。 |
| 連續音樂 | [record_promo_music.py](../../tools/record_promo_music.py)傳舊正式二進位、封包圖集及正式GUI輸入，`--steps 1100000000 --raw-control`；先核對原50M前段音訊；此段捕錄在dosgolem仍為`b0bf259`時執行，錄完再套本輪補丁。 |
| 影片 | [promo-scenes.json](../../tools/release/promo-scenes.json)綁定本輪音源與百科圖；[build_promo.py](../../tools/build_promo.py)依`prepare/encode/check`執行。 |
| 正式與私用包 | [assemble_release.py](../../tools/assemble_release.py)排他建立新版`dist-all/`；[smoke_full_local.py](../../tools/smoke_full_local.py)另設`COLONIZATION_RELEASE_VERSION`，Linux／Wine驗原版狀態，macOS只驗清單與shell。 |

正式Linux二進位SHA-256 `214ab372640fd064a721b890255120c00df4af32dcad06cc8e9cb15072f9ca90`。公開三包均重建兩次逐位元組相同；Linux／Wine正常GUI、相同輸入原版全狀態與WAV相同，RAM `599a732f2a40af0902a6a9968814101a6810c285898918c919669fa88d412f98`。macOS限兩架構建置、臨時簽章資料、封包與shell，未真機或Gatekeeper。

正式根目錄為`dist-all/v.1.0.1-20261005/`。SHA-256見根目錄清單，私用包另見`full-local/SHA256SUMS.json`。Linux新的一鍵入口為`full-local/colonization-cht-v.1.0.1-20261005-full-local-linux-x86_64/start.sh`。舊版原封保留。

Linux／Wine私用完整包正常輸入通過，macOS清單與shell通過。Windows第一輪Wine拒絕在root-owned `/tmp`下建立設定目錄，改用已核對1000:1000的工作根目錄，原封包與命令乾淨重跑通過；第一份失敗保留。此為驗證環境問題。

## 遠端交付與收尾

`PASS_RELEASE_PUBLISHED`：提交`0b9a791fd48a06da455373891aeeb529c5e541cc`與tag `v.1.0.1-20261005`已推送，[修正版Release](https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.1-20261005)五個資產名稱、大小與遠端SHA-256全等。舊`v.1.0.0-20261005`資產與tag未改；私用包、原始WAV及其他PNG未上傳。

`PASS_RELEASE_PROMO`：新版MP4格式、音量、黑幀、八幀布局與遠端附件完成，不含人耳驗收。[Issue #53更新](https://github.com/wicanr2/colonization_cht/issues/53#issuecomment-5983206247)保持OPEN；[Issue #54更新](https://github.com/wicanr2/colonization_cht/issues/54#issuecomment-5983207110)維持CLOSED。未驗的全文清冊不變。

| 公開檔案 | 位元組 | SHA-256 |
|---|---:|---|
| `patch/colonization-cht-v.1.0.1-20261005-linux-x86_64.AppImage` | 18516472 | `5d6c558b71704071ffb23ff3faaa9e3fe84f0c8cfaa6eef3e9e28574792f7441` |
| `patch/colonization-cht-v.1.0.1-20261005-macos-universal.zip` | 14179419 | `d58a755a668c0ca24a24f29e7de858bd04d3a05ca0b784eea100a2fd5e24783b` |
| `patch/colonization-cht-v.1.0.1-20261005-windows-x86_64.zip` | 13977717 | `66bc9c22c3fda54e468bf5d198dd5a1869965bf96574bee0e24c343e71b239e3` |
| `promo/colonization-cht-v.1.0.1-20261005-promo.mp4` | 3939570 | `1204dd2d89829de7c6c6b172af31bd3c02a012e6b67d637b2a801eedd4423276` |

所有本輪輸出擁有權1000:1000，沒有root-owned檔案或.md目錄；容器與背景程序已回收。隔離dosgolem乾淨且upstream推送DISABLED，共享dosgolem未改。Git差異檢查對補丁必要context空白的誤報另以精確補丁比對及反向套用檢查通過，其他來源空白檢查通過。

## 音樂停頓續修與播放分支

2026-10-05使用者要求「解決音樂停頓的問題」。目前來源及隔離dosgolem均沿v.1.0.1，不回到舊版重新普查。依音訊／試玩路由與平台規格停止線，先量測模擬產生取樣的速度。

`audio-stop-profile/run.cpu.pprof`的50M採樣顯示，CPU執行累積63.68%，字串指令34.96%，普通記憶體讀寫的自身CPU占比約22.6%；OPL合成約2%。這批剩餘成本主要在模擬器，不能由增加播放緩衝解決。既有規格037的指令數時鐘不變，200k指令約產生17.27ms音訊。

`audio-phase-probe/inputs.json`沿正式正常選單輸入，終點延長為200M。每10M指令產生約0.864秒音訊，基準共17.27秒音訊／35.78秒耗時；主選單停留段每10M仍需1.33～1.99秒。這是實際耗時與原始供給量的對帳，不是音效卡驗收。

| 可丟棄試驗 | 結果 |
|---|---|
| 普通記憶體批次搬移 | 第一版保守排除整個平面模式，200M約39.40秒；無足夠改善。 |
| 閒置寫入觀測早退 | 只在原callback必定無作用時排除寫入觀測，200M約35.20秒；無足夠改善。 |
| 只排除VGA記憶體範圍 | 修正第一版適用條件，200M約44.83秒；仍不達即時門檻。與UTC基準的RAM只差DOS檔案時間`0x67688`，此批使用台北時區；其他終點狀態、事件、索引、色盤、PNG與原始WAV相同。 |
| 採樣導引編譯（PGO） | 正式dosgolem來源不變，使用Go1.26.7 `-pgo=audio-stop-profile/run.cpu.pprof`；200M約44.52秒。完整RAM、終點狀態、事件、索引、色盤、PNG與原始WAV相同，供給仍不足。 |

各批受主機負載影響，不拿單次耗時推論一般加速率。收據為`audio-phase-probe/audio-supply-comparison.json`，保存原始輸入及採樣雜湊、分段耗時、逐檔比較與限制。這些原型沒有進正式dosgolem或正式包。PGO契約引用[Go官方文件](https://go.dev/doc/pgo)。

[實際時間音訊探針](../../tools/probe_realtime_audio.py)只複製組裝後來源，在隔離副本增加每10ms的48k串流讀取。以單調時鐘的累積時間追上錯過的讀取，不按ticker次數假裝時間停住；消費者不回饋到模擬。使用同一有界Docker/Xvfb，參數為`--source /repo/workplace/reports/goal184-linux/source-release --inputs /repo/workplace/reports/goal184-linux/audio-phase-probe/inputs.json --output <全新輸出>`，另掛唯讀`/game`、`/dosgolem`及可寫Go cache。結果保存`original.wav.clock.json`與`.playback.wav`，原始WAV另存；它可驗供給與缺樣，不能代替硬體實聽。

下一個未決分支會改變音訊節奏或播放架構，依[共同決策技能](/home/anr2/.codex/skills/grilling/SKILL.md)先讓使用者決定。原速獨立播放需要確認曲目與切換，音效沿原路徑；保音高慢速播放會拉長音樂與音效。兩者均不得回饋原版CPU、時鐘或存檔。正式實作仍需補充READY規格，不由「繼續」猜定。

本機試聽`audio-phase-probe/music-original-tempo.wav`為16秒原速；`music-half-tempo-same-pitch.wav`為同段約32秒的保音高半速。由既有私用原始WAV第5～21秒，用FFmpeg5.1.9 `atempo=0.5`製作，方法見[FFmpeg官方契約](https://ffmpeg.org/ffmpeg-filters.html#atempo)。`music-tempo-prototype.json`保存來源與輸出SHA-256。試聽只展示節奏取捨，沒有接入遊戲、不公開、不作修復成功的證據。

時鐘探針基準位於`audio-clock-baseline/`：50.712秒、需求9736320位元組、缺樣6423832位元組，缺樣約66%；來源858569幀，約17.27秒，無積壓丟棄。完整原版RAM、終點狀態、事件、索引、色盤、PNG與原始WAV均與基準相同。原始收據與比較見`run/original.wav.clock.json`及`comparison.json`。播放器錄音僅為容器內的時鐘消費者，沒有音效卡或人耳驗收。

本批已[更新Issue #53](https://github.com/wicanr2/colonization_cht/issues/53#issuecomment-5985306618)，維持OPEN。隔離dosgolem乾淨、upstream推送DISABLED；本輪未建新映像，本輪容器全回收，未清理其他專案容器。全工作樹沒有root-owned產物或.md目錄，新增探針與本機輸出均1000:1000。

## 原速獨立音樂修正版 v.1.0.2-20261005

使用者選擇獨立播放，契約與限定驗證見[規格046](../spec/046-independent-music.md)。主DOS原狀態、原始WAV及數位音效路徑不變；FM音樂／音效由同一原版命令在私用聲音機合成。曲譜與驅動從自備資料讀取，不入公開封包。

本機入口為`workplace/reports/goal184-linux/music-independent/`。`music-verification.json` SHA-256 `3eb1042260009754c57b36a3bf3d6a5829c2b2de7b18f1964b8933503b21081e`記錄83.892秒音樂缺樣0、丟棄0、非靜音及50M完整同狀態比較；`clock-800m/run/original.wav.clock.json`記錄實際讀取。原始JSON頂層保留未使用的fallback-buffer數據，獨立音樂要讀music子欄位；現行探針已分開名稱。曲尾約12秒等待下一首及數位音效缺樣不冒稱已消除。

重跑：[組裝器](../../tools/build_window_prototype.py)加入原速播放器；隔離dosgolem先依規格046套分流補丁。Docker/Xvfb掛唯讀`/game`及`/dosgolem`、可寫`/cache`，以`COLONIZATION_MUSIC_ROOT=/game go test ./...`驗原版API；[時鐘探針](../../tools/probe_realtime_audio.py)傳`--source <組裝目錄> --inputs music-independent/inputs-800m.json --output <全新目錄>`。800M輸入沿本頁正常主選單輸入，延長end，沒有測試注入或改鐘。

三平台打包沿本頁入口，改設`COLONIZATION_RELEASE_WORK=/repo/workplace/reports/goal184-linux/music-independent/release`及版號`v.1.0.2-20261005`。公開三包各封裝兩次全等，Linux／Wine正常GUI與同輸入CPU、RAM及原始WAV全等，RAM `ca45ba3539c3b961291ac97c19dd6f1d4a65ac782b1e5fbadb54e487b05950c7`，WAV `3062c132ffb18df60e4fe435c9eea613e0aa8f1a41f35b2c7a3c0375983f3f39`。這套新GUI輸入與舊輪不同，不要求其終態雜湊等於舊輪。Linux二進位 `91c035367143f0d83b5e1e0adc151fc4fdb83f815e31696c2511cafd4e55f4db`。

正式根目錄`dist-all/v.1.0.2-20261005/`，私用Linux已展開的一鍵入口為`full-local/colonization-cht-v.1.0.2-20261005-full-local-linux-x86_64/start.sh`。Windows、macOS完整ZIP同在full-local，不公開。三種完整包已核對檔案與manifest；Linux／Wine實際啟動及原版狀態相同，macOS限清單／shell。

影片沿已驗連續原版音源與中文百科畫面重新生成版號，90秒H.264／AAC、1920×1080／30fps、黑幀0、非靜音，八幀檢視無字幕裁切。成片SHA-256 `e01ece1635e5f539fe318cc5cdc3fe8595961e7c753f940b55d8df209f96adce`；原始捕錄commit仍如實記錄為b0bf259，不冒稱新版錄影。

`PASS_RELEASE_PUBLISHED`：程式提交`e5b606e37a4e25a0a061194435c533e56aeee21c`及不可變tag `v.1.0.2-20261005`已推送，[Release](https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.2-20261005)五附件的名稱、大小與官方SHA-256全等。[Issue #53留言](https://github.com/wicanr2/colonization_cht/issues/53#issuecomment-5988602216)已更新，Issue保持OPEN。機器核對收據為`music-independent/release-remote.json`及`remote-verification.json`。舊版、私用包與原始音訊未公開或覆寫。

本輪容器全回收，未建新映像，其他專案資源保留；工作根無root-owned檔案或.md目錄，新增程式、文件及交付均1000:1000。兩個Git工作樹乾淨，隔離dosgolem upstream推送DISABLED。

## 2026-10-05：百科殘留英文與游標重繪續修

使用者指出 README 百科截圖的標題、副標題與三個圖示名稱仍是英文，要求由印字例程替換並避免滑鼠覆寫。[保留文字原型](../../tools/probe_text_retention.py)只修改可丟棄組裝副本，先量測完成印字到 VGA 同步的延遲，並試驗主選單中文合成後還原游標。原版 CPU、RAM、輸入、存檔與音訊不改；正式來源尚未採用候選。

已證實：`building-final-v3/gui-pedia.json`在325.87M～325.95M步取得五欄完整原文與譯文，全部在328.02M步因2M等待上限被撤銷。這五欄皆經`0D21:00C6`讀字，不是烘入圖像。`string_misses=0`只證明有譯文，不能證明已顯示；舊38篇正文／22欄先決條件驗收範圍維持原記錄。

正式抽樣入口沿[百科GUI腳本](../../tools/probe_goal179_gui.sh)，設定`COLONIZATION_PEDIA_FIRST=14`、`COLONIZATION_PEDIA_COUNT=15`、`COLONIZATION_PEDIA_HOVER=1`及建築類別222座標，只正常進入使用者指出的篇目並測五個文字欄位。中英／缺圖集三側由[重播工具](../../tools/replay_text_retention.py)在有界Docker/Xvfb、唯讀`/game`內執行；參數`--binary <正式二進位> --gui <正常GUI輸出> --output <新目錄>`。正式來源與收據位於本機`text-retention/`，不注入百科或記憶體。

独立檢查使用[收據檢查器](../../tools/check_text_retention.py)`--reports /repo/workplace/reports/goal184-linux/text-retention`，核對11張百科GUI、五欄啟用、缺圖集回原文、30張主選單往返、完整原版狀態、共同VGA／色盤及存檔。此範圍不重算全遊戲普查完成數。

`PASS_TEXT_RETENTION`（2026-10-05）：正式候選已接入（游標分層見規格012附記，等待保留見規格038附記），正式二進位與工作樹來源雜湊一致，Go vet／測試通過。首輪正式收據因`shot_after`移開游標後立即擷取，GUI仍留舊欄位游標而重播已就緒，對拍在`building-away-0`失敗（舊收據保留於`pedia-gui-formal-race`／`pedia-replays-formal-race`）；已在腳本補足移開後4M步重繪等待並新增`COLONIZATION_FONT_DIR`覆寫，全部素材指向正式包萃取的`extracted-v2`遮罩。重擷取（建築類別選單Y取輸入錄得的220）與三側重播後檢查器通過：11張百科GUI五欄中文、缺圖集回原文、30組主選單游標檢查、中英缺三側完整原版狀態及存檔一致。摘要為本機`text-retention/verification.json`；矩陣列與普查計數維持不變。

## 2026-10-06：游標精靈定位收尾（預防性）

工作樹留有未提交的精靈實際差異定位修正（`menuCursorDisturbance`、單元測試、組裝雜湊、規格012附記），三個舊二進位經符號檢查皆未含新函式；早場舊二進位選單重跑另覆寫檢查器輸入。本輪在驗證映像`colonization-verification:20260930-r1`（Go1.26.7、dosgolem`c5953b9`）完成收尾，收據位於本機`text-retention/menuwrap-*`。

新組裝`menuwrap-new`通過`go vet`與全部`go test`（含`TestMenuCursorDisturbance`三種情境）；新二進位`newcode-window` SHA-256 `091b2c68d69ede42f083f232ef7cf600cd1379ada746b48c9d3089bbda5a06db`。新二進位真視窗掃描`menuwrap-gui`（31張，終點`a8615132…`）：列內規則全過，無英文列。新重播／新對照／舊重播同輸入三路原版終點全等`a8615132…`，`run.memory`／`original.wav`／`run.final.idx`／`run.final.pal`全等，與GUI終點四路一致。百科三側新重播`menuwrap-pedia`與`pedia-replays-formal`狀態、檢查點圖及記憶體全等，無回歸。

延遲機制定位為未重現假說：舊二進位積極掃描（截圖間隔0.5M）`menuwrap-gui-old`同樣無英文列；`menu-transit`六個VGA檢查點精靈皆靜止；密集檢查點`menuwrap-dense`（移動後每0.2M）在首幀精靈已就位，輪詢更新在0.2M步內；新舊實拍的框外小差異皆為`import`擷取撕裂。規格012附記已改列預防性強固。使用者持續英文仍追蹤中，不冒稱已修復。

檢查器修復：早場`menu-replay-formal`／`menu-control-v2`移為`menu-replay-newinputs-80m`／`menu-control-newinputs-80m`，由`*-cursorbox`還原後重跑通過`PASS_TEXT_RETENTION`。

重跑：工作區輔助`menuwrap-sweep.py --binary <二進位> --out <全新基底> --scratch <全新暫存>`（GUI需Xvfb、`--audio-mute`及完整正式旗標）、`menuwrap-replay.py`（重播／對照／舊重播三路比對）、`menuwrap-pixels.py --dir`（列內精靈框規則）、`menuwrap-transit.py --dir`（VGA精靈定位）。容器掛唯讀`/repo`／`/game`／`/dosgolem`、可寫Go cache，`--network none`，UID/GID 1000:1000。
