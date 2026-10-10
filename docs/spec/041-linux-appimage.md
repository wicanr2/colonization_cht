# 規格041：Linux AppImage封裝

狀態：CONFORMED，限封裝格式與正常主選單啟動；日期：2026-10-04。對應[Issue #50](https://github.com/wicanr2/colonization_cht/issues/50)，入口為[目標182](../goals/182-platform-build-preflight.md)。正式完整版與Release依Issue #53另行驗收。

## 決定與證據

使用者2026-09-27已決定Linux以AppImage發行；2026-10-04主機唯讀核對Issue #50要求固定時間戳、乾淨容器解包啟動、manifest、授權及原版排除。這項封裝不改DOS原版、中文顯示規則或玩家流程。

私有DRAFT原型在`workplace/reports/goal182-platform-preflight/20261004-appimage/`。candidate-e／f各18520568bytes，SHA-256皆`9fb9346c0a4ab00f2ad4683715321c513f313ee699ef2c80f9d38dd529ae5fd6`；獨立新容器解包110檔，各檔指紋、授權、runtime來源與原版排除通過。包內啟動器以正常鍵鼠到中文主選單，50M終點、輸入及完整截圖留smoke/。對話框與字串圖集載入理由均空，主選單五列及版本文字啟用。這是封裝啟動驗證，不是全遊戲中文化驗收。

固定工具為`eob-remake-release:1.26.7-ebiten2.9.9-audio`，SHA-256 `062a3f974738894bd8abf0789ff527aa7a2123c5a29eafc3dcae7e3e35d09e8e`；Go1.26.7。appimagetool與runtime指紋見目標182及[tools/appimage_bundle.py](../../tools/appimage_bundle.py)。runtime回報75849dc，來源與授權保存於[來源索引](../../tools/release/appimage-runtime/manifest.json)與同目錄files.json；libfuse3.15.0／squashfuse0.5.2來源雜湊依runtime固定重建腳本。其他元件只保存授權全文，不聲稱runtime內精確版本。

## READY契約

- [tools/package_release.py](../../tools/package_release.py)新增明確的`--format appimage`。原有tar.gz入口保留。兩種格式都沿同一份二進位、13份TSV、字模、原版指紋、Go與第三方授權核對；不另造遊戲資料包。
- 只接受Linux x86_64及與封裝工具相同的Go版本。完整版本識別碼沿既有規則；拒絕既有版本目錄，不覆寫已發布產物。只有選定正式版本後才輸出到`dist-all/<版本>/patch/`，測試產物留workplace。
- AppDir包含原封裝資料及AppRun、桌面項目、自製向量圖示、runtime授權與來源。AppRun只呼叫原Linux啟動器，參數原樣轉送。原版目錄仍只讀，存檔沿COLONIZATION_CHT_SAVE／XDG_DATA_HOME的既有規則。
- ALSA、X11、glibc及OpenGL由Linux桌面系統提供，不複製它們的共享函式庫。已驗環境為Debian12；不宣稱任意Linux或最低系統相容已驗。音訊、顯示服務及bash需求列於說明與manifest。
- AppImage使用固定type2 runtime。檢查工具及所有來源副本雜湊；附runtime來源、libfuse修補／重建腳本、libfuse與squashfuse完整來源及全部靜態元件授權。沒有原版EXE、資料、圖像、字型、音樂或存檔。
- SOURCE_DATE_EPOCH固定0，輸入檔時間固定0，zstd壓縮、單執行緒、256M壓縮快取，不存xattrs。固定工具只支援zstd；SOURCE_DATE_EPOCH不可再和手動時間選項混用，原失敗紀錄保留。
- manifest重新計算AppDir每個一般檔案的大小與SHA-256，加入AppImage格式、系統需求、工具指紋及runtime授權／來源索引。manifest自身不納入自己的雜湊；工具建立的.DirIcon只允許指向包內向量圖示。
- 正式工具接線後再做兩次乾淨重建、獨立解包與正常主選單抽樣。核對包內檔案、授權、二進位、TSV與字模，確認啟動旗標及存檔位置。缺原版不假造通過；這項驗收不提高畫面普查或關閉整體中文化Issue。

## 限制

原型測試版本`v.0.0.0-19700101`沒有正式發行意義。未選正式版號，未建立dist-all新版本、tag、Release或公開原版畫面。Windows、macOS封包與macOS簽章另行處理；此規格不外推它們的完成狀態。

## 2026-10-10 封裝工具恢復

狀態：CONFORMED。原封裝映像已不存在，本機也沒有原 appimagetool。改用官方固定版 1.9.0，下載入口為 `https://github.com/AppImage/appimagetool/releases/download/1.9.0/appimagetool-x86_64.AppImage`，SHA-256 為 `46fdd785094c7f6e545b61afcfb0f3d98d8eab243f644b4b17698c01d06083d1`。實際恢復檔以工具內白名單的完整指紋為準，原指紋繼續保留。

沿用現存 `eob-remake-release:1.26.7-ebiten2.9.9-20261008-r2` 的 Go、Python 與 appimagetool，不另建映像。runtime 由 `hr-appimage:runtime-recovery-r1` 的 `/opt/runtime-x86_64` 恢復，仍須符合原 SHA-256 `1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf`。工具存於目標185已索引的 `release/tools/`，覆掛 `/opt/appimage-tools:ro`。入口仍為 `tools/package_three_platforms.sh`。

只增加固定版封裝器的白名單，manifest 記錄實際工具指紋。runtime、來源與授權、payload、啟動器及原版排除契約沿用原規格。完成條件是兩次乾淨重建全等、獨立解包清冊全等與正常 GUI 啟動通過。

1.9.0 會把 `SOURCE_DATE_EPOCH` 轉成 mksquashfs 命令參數，同時繼承該環境變數時，現有 mksquashfs 明確拒絕。這個固定版分支移除該環境變數，明示 `-mkfs-time 0 -all-time 0`，維持相同的零時間戳契約；其他工具分支不變。失敗紀錄留目標185發行工作區，不列為前端缺陷。

v.1.0.3-20261010 兩次乾淨重建全等，18606584 bytes、SHA-256 `e41a46b5db821e9573bcc42f40e15fea7c905a87e2d17d67b5eccd1ef6d1fffa`。獨立解包110檔、manifest、授權與原版排除通過，SquashFS建立時間與一般檔案時間均0。正式包正常GUI及與Wine同輸入的完整原版、音訊及中文安全區通過；收據由[目標185](../goals/185-player-experience.md)索引。

## 2026-10-04 正式工具驗證

公開封裝器的`--format appimage`在固定映像內兩次從相同乾淨輸入組裝，formal-a／b各18520568bytes，SHA-256皆`375019a92c20c59a2cef726aeba9e3e77181b1b69bdccfec46df94e6b6b91fcf`。測試版本與輸出均留上述本機工作區。獨立容器解包110檔，manifest、SHA256SUMS、13份TSV、字模、二進位及啟動器核對通過，未含原版素材；授權全文與來源完整。一般檔案時間與SquashFS建立時間均0，擷取後目錄時間由解包器決定，不宣稱目錄時間固定。

正式單檔AppImage透過`--appimage-extract-and-run`與包內啟動器，以正常鍵鼠至主選單。formal-smoke-v3在26M步擷取完整1280×800視窗，五列中文安全區`[320,356,968,584]`與50M終點逐像素相同，對話框與字串圖集均載入。輸入SHA-256 `93461d52c45aa9663d248acb3dce629f3f2ef9987d03b189a80ed97a0da4e2a6`，RAM `599a732f2a40af0902a6a9968814101a6810c285898918c919669fa88d412f98`，視窗截圖`825ff1acf6a68314b850b2003af62017f71d76b8145a07217e4ce1628eefe9cc`。原版唯讀、存檔寫本機save/；容器靜音不作人耳音訊驗收。

收據formal-check.json為PASS_FORMAL_APPIMAGE_REBUILD_AND_EXTRACTION，SHA-256 `7381007c703caaf5fb3743a4868825896f4984e300dcd2a553404c860e09d315`；formal-smoke-v3/check.json為PASS_FORMAL_APPIMAGE_GUI_MENU，SHA-256 `ee363464327051fcb8416b2cd9257d5c1f545980fb1c93219c2939417316d4b5`。授權破壞、工具指紋不符、非法版號與覆寫既有版本皆拒絕，refusals.json為PASS_PACKAGING_REFUSALS。

formal-smoke的即時截圖早於中文重繪，終點五列已中文；延後擷取後精確核對通過，未修改產品。formal-smoke-v2因掛載來源拼寫錯誤被啟動器拒絕；只清除該次產生的三層空目錄，改用先核對來源的bind mount重跑。所有舊失敗與原收據保留。#50仍進行中，正式版號及最終完整版封包待驗。
