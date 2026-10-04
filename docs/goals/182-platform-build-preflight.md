# 目標182：三平台建置預檢

macOS ZIP 建置、簽章資料與封包契約見[規格043](../spec/043-macos-zip.md)。本機中間物沿 `workplace/reports/goal182-platform-preflight/20261004-macos-zip/`，不作發行入口。

狀態：建置預檢完成；正式交付見[目標183](183-release-and-promo.md)。日期：2026-10-04。對應 [Issue #50](https://github.com/wicanr2/colonization_cht/issues/50)、[Issue #51](https://github.com/wicanr2/colonization_cht/issues/51)、[Issue #52](https://github.com/wicanr2/colonization_cht/issues/52)。目前入口為 [CONTEXT.md](../../CONTEXT.md)。

在其餘中文畫面驗證期間，先核對現行前端的跨平台建置能力。只有建置中間物，不能當成完整版封包、實機驗收或下載入口；不建立正式版本、tag、Release 或 dist-all 交付目錄。

固定來源為目標180的 `workplace/reports/goal180-pedia-rest/sync-final-build/`；來源已經 Linux 正常 GUI 及同狀態驗證。本輪中間物保存於 `workplace/reports/goal182-platform-preflight/`，全數忽略。原始來源唯讀、輸出與快取先核對 UID/GID，容器明確使用1000:1000、無網路及資源／時間上限。

- Windows x86_64：既有驗證映像 `colonization-verification:20260930-r1`，Go1.26.7、Ebitengine2.9.9。前端組裝與dosgolem不含C/C++來源；先用 `GOOS=windows GOARCH=amd64 CGO_ENABLED=0`、`go build -mod=readonly -trimpath`核對純Go建置。入口為 [tools/build_goal182_platforms.sh](../../tools/build_goal182_platforms.sh)。
- macOS：已確認既有 `eob-remake-macos:1.26.7-ebiten2.9.9-audio`（映像 `sha256:83f12672f4ac06bed37683a9e9eba49980302ba84be11c8042a4dbf4f571761f`）具有Go1.26.7、osxcross兩種架構與lipo；交叉建置與結構檢查另驗，不等同真機通過。
- Linux AppImage：既有 `eob-remake-release:1.26.7-ebiten2.9.9-audio`（`sha256:062a3f974738894bd8abf0789ff527aa7a2123c5a29eafc3dcae7e3e35d09e8e`）具有Go1.26.7、mksquashfs，以及 `/opt/appimage-tools/appimagetool.AppImage`／`linuxdeploy.AppImage`。封包與實際啟動另驗。
- Windows驗證沿用 `psychicwar-wine:latest`（`sha256:4e41c4dca4d6a4450945fe13d0ebc198d07d36090fac87929d7f3696f79315ce`）的Wine與Xvfb；它缺少Python與xdotool，因此以[tools/Dockerfile.windows-verification](../../tools/Dockerfile.windows-verification)建立明確修訂映像`colonization-windows-verification:20261001-r1`（`sha256:7d3c7ff554db39300e3e7a92a7b79c2d5fcd647289596d22fa10899baac61201`）。Python與xdotool版本釘住，完整套件清單在映像`/usr/local/share/colonization-verification-packages.txt`。原Wine映像仍為固定父層，沒有重建替代Wine或掛入主機runtime。其Go companion是Go1.24.13，本輪不混用。

正式封包仍需補齊平台啟動器、同一完整版號、必要授權、合法資料匯入、存檔位置、manifest及SHA-256，並在實際封包中走正常玩家路徑。正式輸出依 `~/.codex/knowledge-base/local/retro-remake-dist-all-output.md`，版本依相同目錄的 `retro-remake-release-versioning.md`；前述入口有子目錄與版號完整契約。Issue #53的全文中文化依賴尚未完成，不提前發布。

## 2026-10-01：已完成的技術預檢

[tools/check_goal182_binaries.py](../../tools/check_goal182_binaries.py)實讀PE／Mach-O／通用檔與Go建置資訊，結果`binary-structure.json`為`PASS_BUILD_STRUCTURE`。Windows為PE32+／0x8664、Go1.26.7、Ebitengine2.9.9、CGO=0。macOS分別為x86_64與arm64，通用檔每個切片逐位元組等於兩個獨立產物。Mach-O載入版本標記為x86_64最低10.13／arm64最低11.0、SDK15.5；這只記錄檔案標記，不代表Go與前端實際支援該最低系統，真機及最低版本相容性未驗。

| 中間物 | SHA-256 |
|---|---|
| Windows x86_64 | `4cc619bb46e17c7e066cd3443c3f9629975843ef4531aef9ec65e02e9d74e160` |
| macOS x86_64 | `826f6ad948a9758448f35d8eaffdb0a37ffae23f66df708a4a41239ba113053a` |
| macOS arm64 | `1616f759b8953743f6e6d6c326ee4af87659699d17dcb30ae724f933fccf2cec` |
| macOS通用檔 | `5ed4de342e1ea5296b1f1bb7037ea8dff0c40c25257e4eb4d6463cf84e585f25` |

Windows啟動`-h`及正常GUI已通過；[tools/probe_goal182_windows.sh](../../tools/probe_goal182_windows.sh)從正式Linux啟動器取得唯一旗標組，再轉為Wine磁碟路徑，載入當前目標180圖集。`windows-gui-v2`正常鍵鼠進入主選單，完整1280×800截圖保存在本機。前版桌面高度裁掉26像素，舊截圖保留，不當成完整畫布驗收。缺Python、未建立scratch目錄、太早選取未映射視窗的三次失敗均發生於驗證環境／包裝入口；修正後以同映像重跑。

[tools/probe_goal182_replays.sh](../../tools/probe_goal182_replays.sh)的`windows-gui-v2.linux-summary.json`為`PASS_WINDOWS_WINE_MENU`：正常GUI輸入SHA-256 `6921125d499014f08d9b805fc8e1de116774d7ca4ff3b8d5029be822415a3a40`，50M終點RAM `599a732f2a40af0902a6a9968814101a6810c285898918c919669fa88d412f98`；CPU完整狀態、1MiB RAM、原版64000位元組索引與768位元組色盤相同。主選單五項及版本六個已啟用欄位，真Wine GUI安全區`[320,356,968,584]`與Linux中文重播逐像素相同。開檔記錄只在七個宿主檔名的大小寫不同，清單順序、數量及按DOS檔名規則正規化後均相同；原始名稱與差異逐項保存，沒有更改原版行為或忽略RAM差異。第一版比較器對大小寫拒絕的原收據保留。

重跑入口：在對應有界容器掛repo→`/repo`、原版→`/game:ro`；建置另掛隔離副本→`/dosgolem:ro`、Go快取→`/cache`並設定`GOCACHE=/cache`，原建置來源重疊唯讀掛載。先建立本機中間物父目錄並核對UID/GID，建置入口`bash /repo/tools/build_goal182_platforms.sh windows-amd64`或`macos-universal`；預設拒絕既有產物。結構入口`python3 /repo/tools/check_goal182_binaries.py --out /repo/workplace/reports/goal182-platform-preflight --source /repo/workplace/reports/goal180-pedia-rest/sync-final-build`。GUI入口`bash /repo/tools/probe_goal182_windows.sh`；跨平台重播入口`bash /repo/tools/probe_goal182_replays.sh`。如要重生，先以新的本機輸出版本保存既有收據，不能覆蓋原收據冒充重跑。

本輪沒有新增正式平台啟動器、打包或公開原版畫面；Win／Mac真機、Linux AppImage、新版正式封包與影片仍未完成。技術預檢不提高761列中文完成數、不關閉#50～#54。
## 2026-10-04 現行選項接線的建置入口

`tools/build_goal182_platforms.sh`新增`COLONIZATION_GOAL182_SOURCE`與`COLONIZATION_GOAL182_OUT`，保留拒絕覆蓋既有產物。預設來源改為`workplace/reports/goal181-colony-rest/20261004-dialog-links/formal/stable-build`，由公開組裝器產生，包含現行港口文字與正文來源選項接線；不再默默建置舊百科版本。現行中間物另存`workplace/reports/goal182-platform-preflight/20261004-current-text/`，不改正式版號或建立發行包。建置來源另外唯讀掛載，工具鏈沿本頁固定映像；既有真機／封包限制仍保留。

本批`binary-structure.json`為`PASS_BUILD_STRUCTURE`，SHA-256 `1dd442241225a5f76e095b888b92bc479223088fd181d9f3f4ffaee605da1a47`。
Windows x86_64為`db6c58788e42722738c3fa3231d96b2519de9272f95bf1162a959d09931fa710`；
macOS x86_64為`24933bc00dd16ec835fb0cd8f5c1ddab3304a66beef274c1f58f2145df079a6d`，
arm64為`b4c2890b9e907b3e5cd06f263eaf0d4008d6da5a93cd5f491861c565ef652ae4`，
通用檔為`03f411ce2f0511821687170fb82085e21e4c2bfd2899e4e0d52fc7a61eea7c80`。
本批只做建置與結構核對，沒有以舊Wine收據冒稱新版GUI通過。檢查器將JSON輸出至標準輸出，需明確保存：

```sh
python3 /repo/tools/check_goal182_binaries.py \
  --out /repo/workplace/reports/goal182-platform-preflight/20261004-current-text \
  --source /repo/workplace/reports/goal181-colony-rest/20261004-dialog-links/formal/stable-build \
  > /repo/workplace/reports/goal182-platform-preflight/20261004-current-text/binary-structure.json
```

命令須在本頁驗證容器與掛載契約內執行；既有收據留存，重跑時改用新輸出目錄。

## 2026-10-04 事件版畫接線的建置預檢

現行來源更新為目標160索引的`20261004-woodcut-titles/formal/stable-build`，含有來源防護的事件版畫三色標題。沿同一公開組裝器與本頁工具鏈，輸出到本機`workplace/reports/goal182-platform-preflight/20261004-woodcut-text/`；只做新版建置與結構核對，不覆寫前一批收據或產生正式封包。建置時將來源另掛`/source:ro`，設定`COLONIZATION_GOAL182_SOURCE=/source`、`GOWORK=/source/go.work`與新的`COLONIZATION_GOAL182_OUT`。結構檢查仍用`tools/check_goal182_binaries.py`；新版Wine、macOS真機與三平台封包另待驗。

本批`binary-structure.json`為`PASS_BUILD_STRUCTURE`。Windows x86_64為`34d20ce5feedee2d5ace28a7ff8bc3dc7a6c9a068939c27d78e03fe96fb858ba`；macOS x86_64為`09ff99e8a92559d895bdaf3d679e6c4a7ad3989b2d5799e8745299205665a0fa`，arm64為`0af073b2f6b49464285d092343c9bc5db8f32a4675db4f6a4f7dee2083f8e5ea`，通用檔為`8ed0421088fc14ac411e5dcdbe14fb222107c12c97a939fedc8acb88bd61c096`。通用檔切片與兩個獨立產物逐位元組相同，Go1.26.7／Ebitengine2.9.9與來源程式指紋核對通過。本批不宣稱新版Wine或真機驗收，舊平台收據保留。

同日事件頁清底修正後，現行來源轉為`20261004-woodcut-titles/formal-modal/stable-build`，另存`workplace/reports/goal182-platform-preflight/20261004-woodcut-page/`。沿前一批來源唯讀、固定工具鏈與輸出拒絕覆寫的契約，只重建受來源改動影響的建置中間物；結構及新版執行限制仍分開記錄。

事件頁最終抽樣通過後，現行來源為`20261004-woodcut-titles/formal-modal2/stable-build`，由目標160索引，平台輸出另存`workplace/reports/goal182-platform-preflight/20261004-woodcut-final/`。建置腳本預設來源同步到此版；沿既有唯讀來源、工具鏈及新輸出契約，不覆寫前版產物。這一批只核對建置與二進位結構，Windows新版執行、macOS真機、Linux AppImage及正式封包仍待驗。

最終建置與結構檢查PASS_BUILD_STRUCTURE，摘要SHA-256 `e7da3946f3db322caf416f3e6dbffea542b4a99e1a98fde181bfd492a493d49c`。Windows x86_64為`fbb87a2f8f7eb1cc495052eb533c33a4e9c7a941e36251ed341a9aa0a6a2eae9`，macOS x86_64為`23e8341076be5128d67f0640977079fc202b0a20c9a4257101af4b12e9f257fb`，arm64為`58fdc1f5a70396f410f018d8a083616a2b6fb32fc95abdb19be32c7b6da4ad95`，通用檔為`9df308b2ca6be08abfce4122f4b6389733fb5e759be39959dec95727797f0f6d`。切片逐位元組相同；來源指紋、Go1.26.7與Ebitengine2.9.9相符。最低系統欄位只記錄Mach-O資料，不宣稱真機相容。最終擁有權與Docker收據沿目標160的`20261004-woodcut-titles/hygiene.json`。

## 2026-10-04 AppImage封裝候選

主機唯讀核對Issue #50仍OPEN，明確要求固定時間戳、乾淨容器解包啟動、manifest與授權告知，不含原版。本機工作區為`workplace/reports/goal182-platform-preflight/20261004-appimage/`，只保存候選腳本、第三方runtime來源與授權、封裝及啟動收據；不作正式交付入口。候選輸入為上列formal-modal2公開組裝入口，既有Linux啟動旗標、TSV、字模及原版指紋守門沿用。測試識別碼`v.0.0.0-19700101`只供本機重建比較，不是決定正式發行版號。

沿既有`eob-remake-release:1.26.7-ebiten2.9.9-audio`，AppImage工具與runtime固定指紋：appimagetool `a6d71e2b6cd66f8e8d16c37ad164658985e0cf5fcaa950c90a482890cb9d13e0`，linuxdeploy `421ca71d5c69ea97c6309276232990d43df1dcece0edfaa26bbf926ff96ed12e`，runtime-x86_64 `1cc49bcf1e2ccd593c379adb17c9f85a36d619088296504de95b1d06215aebbf`。runtime實際回報提交75849dc；來源、靜態第三方元件與授權先核對，再封裝。尚未產生正式AppImage、dist-all新版本或Release。

候選入口為本批`prepare-appimage.py`、`check-candidate.py`與`run-smoke.sh`；固定runtime來源及授權副本保存於`tools/release/appimage-runtime/`，來源索引為其中`manifest.json`。這些是公開開源元件及其授權，不含原版遊戲；libfuse來源、runtime修補與重建腳本一同隨包，其他元件的授權也附在包內。ALSA、X11、glibc與OpenGL沿既有Linux桌面需求由系統提供，本候選不複製它們的共享函式庫，不宣稱任意Linux系統皆已驗。

第一輪gzip選項被固定工具拒絕；第二輪SOURCE_DATE_EPOCH與手動時間選項衝突。`prepare-appimage-v1.py`／`v2.py`及candidate-a～d的build.log保留失敗。依工具實際說明改用zstd、SOURCE_DATE_EPOCH=0、單執行緒、256M壓縮快取與無xattrs，candidate-e／f各18520568bytes，SHA-256皆`9fb9346c0a4ab00f2ad4683715321c513f313ee699ef2c80f9d38dd529ae5fd6`。新容器解包核對110檔、清單、授權及原版排除通過，入口為`extraction-check.json`；包內啟動器正常玩家主選單及正式工具接線仍待驗。這些失敗屬封裝工具設定，不是中文化或原版行為缺陷。

候選正常主選單已成功，完整1280×800畫面已目視，50M紀錄與輸入保存smoke/，不是新遊戲全流程驗收。[規格041](../spec/041-linux-appimage.md)完成DRAFT證據審查後READY，授權[AppImage組裝器](../../tools/appimage_bundle.py)及既有封裝器的`--format appimage`，圖示與桌面項目保存tools/release/。正式來源接線後的重建、清單及啟動抽樣另存本批formal-a／formal-b／formal-smoke，不覆寫候選。

## 2026-10-04 AppImage正式封裝入口驗證

現行Linux二進位為formal-modal2/stable-build的`82d1041f093ff02eb83ceb28aec9e3b2e77bd7a2af9440e153a7180b70a13314`，譯稿與字模均沿現行來源。正式封裝器兩次輸出到本批formal-a／b，AppImage各18520568bytes，SHA-256 `375019a92c20c59a2cef726aeba9e3e77181b1b69bdccfec46df94e6b6b91fcf`，逐位元組相同。formal-check.json為PASS_FORMAL_APPIMAGE_REBUILD_AND_EXTRACTION，指紋`7381007c703caaf5fb3743a4868825896f4984e300dcd2a553404c860e09d315`。

獨立解包110檔，完整manifest、SHA256SUMS、13份TSV、字模、二進位、啟動器及所有第三方授權／來源全等，沒有原版素材。SquashFS在AppImage檔案偏移944632，建立時間0；一般檔案mtime0。這是檔案結構定位，不是CPU地址。解包後目錄mtime由解包器建立，未納入固定時間聲明。runtime只借用系統ALSA、X11、glibc、OpenGL及bash，不隨包散布它們的共享函式庫。

正式單檔`--appimage-extract-and-run`在乾淨Debian12驗證容器，正常鍵鼠進入中文主選單。formal-smoke-v3於26M擷取完整1280×800視窗，選單安全區`[320,356,968,584]`與50M終點精確相同；五列已套用中文，對話框及字串圖集載入正常，原版唯讀、存檔位置沿啟動器規則。check.json為PASS_FORMAL_APPIMAGE_GUI_MENU，SHA-256 `ee363464327051fcb8416b2cd9257d5c1f545980fb1c93219c2939417316d4b5`；輸入`93461d52c45aa9663d248acb3dce629f3f2ef9987d03b189a80ed97a0da4e2a6`，完整RAM `599a732f2a40af0902a6a9968814101a6810c285898918c919669fa88d412f98`。沒有重跑全遊戲、提高畫面普查或以相同RAM雜湊代替跨平台對拍。

formal-smoke較早的即時圖仍在第一列英文重繪，終點已中文；延後擷取即通過，不改正式程式。formal-smoke-v2掛載拼寫錯誤被啟動器拒絕，誤建三層空目錄經逐層確認後清除；v3先確認來源，再用不存在時會拒絕的`--mount type=bind`重跑。初次唯讀文件檢查映像沒有rg，改用Python／sed讀取必要內容；不算產品缺陷。各失敗與舊收據保留。

重跑正式組裝時沿本頁Docker資源／UID與工具鏈契約，先核對repo、唯讀原版、隔離dosgolem及Go快取掛載。使用新的本機輸出目錄，舊收據不可覆寫；測試版號仍只作fixture：

```sh
python3 /repo/tools/package_release.py --format appimage \
  --version v.0.0.0-19700101 --repo /repo \
  --binary /repo/workplace/reports/goal181-colony-rest/20261004-woodcut-titles/formal-modal2/stable-build/colonization-window \
  --readme /repo/tools/release/README.txt \
  --output /repo/workplace/reports/goal182-platform-preflight/appimage-replay-a
```

本批獨立驗證入口為check-formal.py、run-formal-smoke-v3.sh及check-formal-smoke.py。它們在上列本機工作區，不是正式遊戲資料。授權破壞、工具指紋不符、非法版號及覆寫既有版本均拒絕，refusals.json指紋`049d82b1a013f0e16a29c0e18b9b5a48e57119f67f00dd92dfe074edde796889`。[規格041](../spec/041-linux-appimage.md)只升封裝格式與正常主選單CONFORMED，#50在本機清單進行中，遠端仍OPEN。

第三方來源入口為[manifest.json](../../tools/release/appimage-runtime/manifest.json)，同目錄files.json核對12份來源／告知檔案。runtime75849dc完整來源31040bytes，指紋`3efa7575abc43d3867db75a0e5168ba835b5acc9ca4248f6e879a2f11b7c1de8`；libfuse3.15.0及squashfuse0.5.2完整來源與runtime修補腳本隨包。其他靜態元件只記錄授權來源版本，不聲稱其二進位內版本已證實。未重建工具映像，未定正式版號、建立dist-all新版、tag或Release。最終Docker／檔案衛生收據為本批hygiene.json。

## 2026-10-04 Windows ZIP候選入口

[規格042](../spec/042-windows-zip.md)為DRAFT，沿使用者既有Windows x86_64平台決定與Issue #51的可重現建置、Wine／Linux重播要求。候選、現行來源重建、包內批次啟動器與編碼檢查保存於`workplace/reports/goal182-platform-preflight/20261004-windows-zip/`；這是本機測試工作區，不是正式交付根目錄。待候選驗證完成後才升READY及正式接線。

## 2026-10-04 Windows ZIP正式接線與抽樣

本批沿現行formal-modal2/stable-build及固定Go1.26.7驗證映像再交叉建置，Windows二進位逐位元組等於前批，SHA-256仍`fbb87a2f8f7eb1cc495052eb533c33a4e9c7a941e36251ed341a9aa0a6a2eae9`。公開[封裝器](../../tools/package_release.py)新增`--format windows-zip`，平台守門按格式核對Go建置資訊；[Windows組裝器](../../tools/windows_bundle.py)從Linux唯一完整命令產生ASCII／CRLF批次檔，保留旗標、譯稿與字模。[Windows說明](../../tools/release/README.windows.txt)在包內寫為UTF-8 BOM／CRLF。模組授權依實際Windows二進位收集，包括hideconsole，不沿用Linux模組清單。

候選a／b兩份一致但正常驗證失敗，保留舊Windows組裝器、ZIP及記錄。最小參數探針證實CMD拆開`--play=false`，Go讀到false位置參數後忽略後續旗標；修正啟動器在收集時重組true／false。修正候選c／d各13973262bytes，SHA-256 `65a607e316926f28851e6aaff776d9573dc0511cbd3a8c91a5b647e0494ae916`，candidate-check-v2.json核對95檔及中文ZIP根目錄UTF-8旗標通過。

初次Wine CMD引號呼叫與CALL返回碼差異屬驗證腳本問題：cmd-diagnostic.json及cmd-exit-control.json保留原測試與最小exit /b 2控制。原批次檔拒絕缺原版仍返回2；本Wine CALL把非零值轉1，不能拿其外層值當產品退出碼。正確GUI呼叫沿CALL及C.UTF-8，缺原版探針使用同字節批次檔的ASCII路徑直接核對。另一個過早開始GUI的驗證在ZIP核對前拒絕，無產物；沒有替換工具映像或放寬產品驗收。

candidate-smoke-v4在含中文、空白、驚嘆號與&的包路徑／原版路徑正常鍵鼠進主選單。Windows與Linux再無頭重播同一實際輸入，50M完整CPU、1MiB RAM、原版索引／色盤全等，五列及版本安全區逐像素相同。兩平台WAV全等，49715Hz、雙聲道16bit、214642frames，指紋`457e773b1465840fc481c7e004cf20255522ed7ab4b14841cb4826760caded15`。candidate-summary.json為PASS_WINDOWS_CANDIDATE_GUI_AND_REPLAY，指紋`4bde596b05b03b7c71dc1f53d4bd7040e0e1b4fafec054c186ac9798983c5be2`；七個開檔名稱大小寫差異逐項保存，按DOS規則核對同名與順序，不忽略原版記憶體差異。它不是人耳或全遊戲驗收。

候選審查使規格042升READY，公開工具formal-a／b乾淨重建各13973331bytes，SHA-256 `2fa9630f26f195257170bcc86c78b6f60a5e4a743740e448f4719939e9cfe100`。獨立解包95檔、完整manifest／SHA256SUMS、編碼、授權／原版排除通過，資料、字模、二進位、啟動器及授權與候選全等。formal-check.json指紋`750be6b4a9fd709f705c001d1f9b5f61fe855b330badf61ba98bc08dcf5e759a`。正式單檔ZIP解包後的包內批次檔另走正常GUI，完整1280×800圖已目視；實際輸入與候選相同，完整原版與安全區精確相同，formal-smoke/check.json指紋`f3452cdd0821f4ab84eb2514d6a66906ae40ae6b8088323b281b6ba3c4b29136`。

未設定COLONIZATION_CHT_SAVE的1000步冷啟動另驗LOCALAPPDATA預設位置，default-save-check.json只記預設目錄與執行成功，不當正常存讀檔證據。正式入口拒絕錯平台、非法版號與既有版本覆寫，refusals.json指紋`ff6a76fef1b094ed88017c4589b084c955e572e3804efdf4d29c5066ba8174a0`。共用守門改動後，Linux AppImage只重建一次，與上輪375019a9…正式驗證包位元組相同；沒有重跑整個GUI矩陣。

重跑組裝沿本頁Go映像、資源上限、UID1000:1000與唯讀來源契約，使用新本機輸出保存舊收據：

```sh
python3 /repo/tools/package_release.py --format windows-zip \
  --version v.0.0.0-19700101 --repo /repo \
  --binary /repo/workplace/reports/goal182-platform-preflight/20261004-woodcut-final/colonization-window.exe \
  --readme /repo/tools/release/README.windows.txt \
  --output /repo/workplace/reports/goal182-platform-preflight/windows-zip-replay-a
```

本批私有驗證入口為check-candidate-v2.py、run-candidate-smoke-v4.sh、run-replay-v2.sh、check-replays.py、check-formal.py、run-formal-smoke.sh及check-formal-smoke.py。Wine仍固定`colonization-windows-verification:20261001-r1`，正常GUI顯示1600×1000且有trap／外層逾時；重播分Windows／Linux獨立存檔輸出，不同時共用Wine prefix。正式驗證將原版/game與repo內別名一同唯讀掛載。[規格042](../spec/042-windows-zip.md)僅封裝、主選單及同輸入重播CONFORMED，#51本機進行中，遠端仍OPEN。未選正式版號、建dist-all新版、commit、push或Release；譯稿／字模／遊戲程式及普查信用均未變。最終檔案／Docker衛生收據為本批hygiene.json。

## 2026-10-04 macOS ZIP正式封裝入口驗證

主機唯讀核對#52仍OPEN，要求osxcross兩架構universal、lipo／簽章檢查，沒有真機時明確記錄驗證層級。沿既有macOS映像交叉編譯，ZIP組裝沿固定Go1.26.7／Python3.11驗證映像，不另建重複映像。來源仍formal-modal2/stable-build；source-identity.json與前批全部Go／模組來源指紋相同，SHA-256 `083ad1c74e07e2e470e3d8877c9f4b17c2feb05609b8a3931608f46858fc1a2b`。

Intel舊切片未簽章；加ld64-711的-adhoc_codesign後，Go追加DWARF但不重簽，signed-a的簽署範圍與最終檔案不同，檢查器拒絕。失敗產物與stderr保留。正式macOS建置採規格043的 `-w -extldflags=-Wl,-adhoc_codesign`，兩架構簽章資料與全部頁雜湊通過；signed-c／d及formal-build通用檔逐位元組相同，SHA-256 `1c17376afc9e55013a0528a65f30bd4ebf6a26d535cbfe73dd2a7215c2f748ef`。切片、載入命令及簽章數字均屬Mach-O檔案偏移，不是DOS CPU地址。最低系統欄位仍只記錄檔案標記。

公開工具formal-a／b ZIP各14177251bytes，與候選完整位元組相同，SHA-256 `b6a1b5fc9d40098a02808f23b185dec92301adff711b7619da1b265273804d1f`。94檔、完整MANIFEST／SHA256SUMS、13份譯稿、字模、兩側實際依賴授權、檔案模式及原版排除通過。formal-check.json為PASS_FORMAL_MACOS_REBUILD_AND_EXTRACTION，SHA-256 `71b1b4f0ee6c9f9c3065d54c9f65b79fe4676b48394371b9cf0f0cb8583d0750`。入口為[規格043](../spec/043-macos-zip.md)、[macOS組裝器](../../tools/macos_bundle.py)及[macOS說明](../../tools/release/README.macos.txt)。

macOS終端機啟動器由既有唯一Linux命令產生，預設存檔參數為~/Library/Application Support/colonization-cht/save；沒有改原版流程。GNU Bash3.2.57與5.2以argv／mkdir記錄替身驗證，中文與空白／!／&路徑、空額外參數、有額外參數、指定與預設存檔參數、help／缺目錄拒絕及退出碼均通過。這只驗shell接線，不宣稱實際建立預設存檔、執行Mac二進位或原版遊戲。正式ZIP全等於已驗候選，因此沿用相同接線收據，不重跑同一測試。

GNU Bash3.2.57官方原始碼SHA-256 `3fa9daf85ebf35068f090ce51283ddeeb3c75eb5bc70b1a4a7cb05868bfe06a4`；在原驗證映像用固定Debian Bison3.8.2及M4 1.4.19真正重生語法分析器。套件指紋分別`a414afd7519c53bfa33415ba5b951bc8b4906877004c49723ffda50a6033c3e8`、`b2dd7bfca426712416e651bb5ff6dabe7d05e4caebbac61d714dbe261b31e4c3`。這些工具只留忽略的本機工作區，不放入遊戲封包。缺curl／Git／模組快取位置／yacc／M4，以及ZIP尚未完成時的提前檢查，均為工具或驗證流程問題；舊紀錄保留，不算中文化產品缺陷。重複候選執行被拒絕，未覆寫原包。

兩側壞簽署頁、錯平台、舊未簽章／失效簽章、macOS誤用Windows／Linux格式、非法版號與既有版本覆寫均拒絕。refusals.json指紋`cf60dff6a27f878d48240b1fa763c6a10feee1bcb715fb3edb742d35ead09182`。共用封裝器的Windows ZIP回歸13973331bytes，仍`2fa9630f26f195257170bcc86c78b6f60a5e4a743740e448f4719939e9cfe100`，與前批全等。Linux封裝分支與前端／譯稿／字模未改，不擴大GUI或全文矩陣重跑。

重跑正式入口時依本頁Docker掛載與資源契約，先核對來源及新輸出目錄擁有權；macOS建置由tools/build_goal182_platforms.sh macos-universal產生。本機封裝測試命令如下，fixture不是正式版號：

```sh
python3 /repo/tools/package_release.py --format macos-zip \
  --version v.0.0.0-19700101 --repo /repo \
  --binary /repo/workplace/reports/goal182-platform-preflight/20261004-macos-zip/formal-build/colonization-window-macos-universal \
  --readme /repo/tools/release/README.macos.txt \
  --output /repo/workplace/reports/goal182-platform-preflight/macos-replay-a
```

本批獨立入口為prepare-candidate.py、check-candidate.py、check-formal.py、check-refusals.py，位於本頁開頭索引的20261004-macos-zip工作區。規格043只限建置／簽章資料／封包／shell接線CONFORMED。沒有macOS執行、真機、Gatekeeper、音訊或鍵鼠驗收；不提高翻譯、882畫面普查或全遊戲完成數。#52本機仍進行中，遠端未寫入；未選正式完整版號、建立dist-all新版、commit、push、tag或Release。

本批收尾衛生通過：2009個本機批次檔案／目錄均1000:1000，全工作樹無root-owned或.md目錄，無原版素材誤入Git。WORKLIST重生及核對、文件入口與本輪Git差異檢查通過；dosgolem乾淨且upstream推送DISABLED。簽章工具來源指紋見本批go-signing-source.json，收尾見hygiene.json。未重建映像；本輪有界容器均使用--rm，主機另作最後清理核對。
