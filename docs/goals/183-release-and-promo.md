# 目標183：三平台交付與推廣影片

狀態：完成。使用者於2026-10-04授權commit、push、更新Issue、Linux AppImage、Windows、macOS完整版封裝與推廣影片。入口為[目前脈絡](../../CONTEXT.md)，契約為[規格044](../spec/044-release-and-promo.md)。對應Issue [#50](https://github.com/wicanr2/colonization_cht/issues/50)至[#54](https://github.com/wicanr2/colonization_cht/issues/54)。

本版收進目前全部顯示、輸入、音樂及音效功能。譯文完整與畫面已驗範圍分開報告；974項未抽樣清冊及三個報表城市名不宣稱完成。既有技術預覽保持原樣。

準備工作只寫入忽略的`workplace/reports/goal183-release/`。正式輸出依`~/.codex/knowledge-base/local/retro-remake-dist-all-output.md`，版號依同目錄`retro-remake-release-versioning.md`。三種封包先各自組裝與驗證，再以拒絕覆寫方式彙整到同一`dist-all/<版本>/`。

退出條件：三種封包有同一內嵌版號、manifest、授權、雜湊與乾淨解包檢查；Linux及Wine實際啟動，macOS記錄雙架構與簽章資料且明載未真機；90秒MP4有實際dosgolem畫面與原版音樂、來源收據及影音抽樣；提交與推送後建立不可變tag及Release並核對遠端資產。Issue只依實際完成範圍更新。

## 可重現入口

以下全部在容器執行，工作樹與快取先核對1000:1000，原版唯讀掛`/game`。工具映像及資源界線沿[目標182](182-platform-build-preflight.md)，FFmpeg使用既有`eob-remake-go:1.26.7-ebiten2.9.9-video`。外層timeout、`--rm --network none --user 1000:1000`、2CPU、4GiB及256PID為本輪上限；Xvfb必由呼叫腳本trap回收。

| 工作 | 入口 |
|---|---|
| 組裝與版號 | [組裝器](../../tools/build_window_prototype.py)、[版號來源](../../tools/frontend_version.go)、[二進位版號檢查](../../tools/inspect_release_version.go) |
| 三平台建置 | [build_release.sh](../../tools/build_release.sh)，參數`v.1.0.0-20261005 linux/windows/macos`；來源另唯讀掛`/source`，隔離dosgolem掛`/dosgolem:ro`，快取掛`/cache` |
| 重複封裝 | [package_three_platforms.sh](../../tools/package_three_platforms.sh)，參數同版號；[檢查器](../../tools/check_release_packages.py)驗證兩份封包、清單與合法資料 |
| 正常啟動及同輸入 | [smoke_release.sh](../../tools/smoke_release.sh)、[Wine入口](../../tools/smoke_release_windows.py)、[Linux重播](../../tools/replay_release.py)、[比較器](../../tools/check_release_smoke.py) |
| 音樂與剪輯 | [錄製器](../../tools/record_promo_music.py)先重播50M正常GUI輸入，再停留至300M；[剪輯設定](../../tools/release/promo-scenes.json)與[影片工具](../../tools/build_promo.py)的`prepare/encode/check`三步。Cubic 11來源唯讀掛`/font`，指紋見設定。原始收據留workplace。 |
| 正式彙整 | [assemble_release.py](../../tools/assemble_release.py)，三平台暫存根、已驗影片與smoke作輸入，排他建立`dist-all/<版本>/`；`--full-game /game`只產生本機full-local，不供公開 |

本輪正式來源只新增版號字串與視窗標題；轉譯鍵、字模、幾何與原版呼叫點不變。先前160項進階測試及133項公開入口回歸保留；本輪公開來源Go測試與go vet再次通過，不重跑未改動的整份畫面普查。

## 2026-10-05 正式交付證據

正式交付入口為`dist-all/v.1.0.0-20261005/`。下列公開檔案已從實際交付重新計算；本機自帶資料包另存`full-local/`，不進Git或Release。Linux與Wine正式GUI及同輸入CPU／1MiB RAM／64000位元組索引／768位元組色盤／WAV完全相同，RAM `599a732f2a40af0902a6a9968814101a6810c285898918c919669fa88d412f98`，WAV `457e773b1465840fc481c7e004cf20255522ed7ab4b14841cb4826760caded15`。主選單五項及版本實際中文安全區`[320,356,968,584]`完全相同。

| 產物 | 位元組 | SHA-256 |
|---|---:|---|
| `patch/colonization-cht-v.1.0.0-20261005-linux-x86_64.AppImage` | 18516472 | `a32491546e1dd84fcca1d3cc547b98fd7c1cac0b142bc83765084c1369dd0cf1` |
| `patch/colonization-cht-v.1.0.0-20261005-macos-universal.zip` | 14177838 | `8dcf00da66555a5fea5acfd039af2067fa399b67cb23f677de5e4fbf492e5e6b` |
| `patch/colonization-cht-v.1.0.0-20261005-windows-x86_64.zip` | 13974798 | `8695379f269760ff32febc98cd1cd9923f6d46252ace65d069ea2f0a8476b02a` |
| `promo/colonization-cht-v.1.0.0-20261005-promo.mp4` | 2387088 | `dcce9cb008571cb3378263375aa372bb9a944e5fda8036664728fac958cdb9b4` |

封包訊號：`PASS_RELEASE_APPIMAGE`、`PASS_RELEASE_WINDOWS`、`PASS_RELEASE_MACOS_BUILD_PACKAGE`。前兩者包含實際啟動；macOS只包含建置、兩切片臨時簽章資料與封包，沒有真機、Gatekeeper、最低系統或開發者身分簽章驗收。

影片：90秒、1920×1080、30fps、H.264／AAC，八幀抽樣無裁切，黑幀0；固定畫面停留是明示剪輯。原版音樂25.904757秒、49715Hz立體聲，中文版／原文控制側完全相同，WAV `fbad119e3e0ee87a76d492ed917279f21141426565182da0cda85cb4e65ad263`；循環接縫0.5秒，音量2倍，最後檢查平均−23.9dB、峰值−5.4dB。這是技術音量檢查，不冒稱人耳驗收。首版影片主選單含一列英文滑鼠懸停，抽看後改用正式Wine完整中文畫面，舊中間物保留。

原始影片收據、音樂、版號符號地址、完整測試與封包清單都在本機`workplace/reports/goal183-release/`；正式影片收據在交付`promo/`，公開只附MP4。首輪封包檢查漏列AppImage合法`.DirIcon`圖示連結，按原規格修正為精確連結守門，乾淨展開v2通過。容器stdin與聯絡圖預設字型失敗均為工具問題，修正後重跑。

私用完整包抽樣入口：[smoke_full_local.py](../../tools/smoke_full_local.py)，Linux／Wine以同一正常輸入重播，macOS只做檔案與shell檢查。

## 遠端交付與私用包收尾

`PASS_RELEASE_PUBLISHED`：程式提交`898d4e1`已推送main，tag `v.1.0.0-20261005`指向此提交；[正式Release](https://github.com/wicanr2/colonization_cht/releases/tag/v.1.0.0-20261005)已發布。GitHub五個資產的名稱、大小與平台計算SHA-256全等，沒有上傳full-local、原始PNG或WAV；舊版未改動。Issue #50、#51、#52、#54已關閉；#53及#55～#61已留言並保持OPEN。`PASS_RELEASE_PROMO`代表MP4技術驗證、八幀抽看及遠端附件完成，不含人耳或連續遊玩錄影驗收。

私用包第一輪歸零時間戳造成Linux三位元組、Wine四位元組RAM差異，全部位於原始RAM線性偏移`0x67687`至`0x6768A`。dosgolem `internal/dos/find.go`的DOS日期取來源`ModTime()`已查證；私用包改為保留來源時間、Python ZIP解包還原manifest時間後，Linux及Wine相同正常輸入的完整原版狀態皆回到`599a732f…`，原失敗不覆寫。這是封包輸入metadata與解包工具問題，沒有修改原版或dosgolem。macOS仍只驗實際私用包清單與shell，未真機。

| 本機私用包 | 位元組 | SHA-256 |
|---|---:|---|
| `colonization-cht-v.1.0.0-20261005-full-local-linux-x86_64.tar.gz` | 21527043 | `555cc53428e8ee311e7810fa5bb8c6e0e176da7712de767a6580574de49ace93` |
| `colonization-cht-v.1.0.0-20261005-full-local-macos-universal.zip` | 18322999 | `c37e51fdb675da12110f52db1c70229ee93366652833c794396b87a5652af24b` |
| `colonization-cht-v.1.0.0-20261005-full-local-windows-x86_64.zip` | 18108323 | `af0410dfd0925b829ad02d161751f1028f481284e60dc16fd5f214cb13ea1ef7` |

收尾Docker自檢：本輪一次性容器已結束，背景程序已回收；沒有root-owned輸出或`.md`目錄，原版未追蹤，隔離dosgolem乾淨且推送DISABLED。
