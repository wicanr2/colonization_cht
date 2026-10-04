# 規格042：Windows x86_64 ZIP封裝

狀態：CONFORMED，限封裝、正常主選單與同輸入跨平台重播；日期：2026-10-04。對應[Issue #51](https://github.com/wicanr2/colonization_cht/issues/51)，入口為[目標182](../goals/182-platform-build-preflight.md)。

## 已確認來源

使用者2026-09-27已決定Windows x86_64；2026-10-04主機唯讀核對Issue #51仍OPEN，要求可重現交叉建置、Wine啟動及與Linux無頭重播逐位元組相同，原版不入包。本輪不改原版、顯示規則或既有Linux封裝格式。

現行Windows二進位來自formal-modal2/stable-build，Go1.26.7、CGO=0、PE32+／0x8664，指紋`fbb87a2f8f7eb1cc495052eb533c33a4e9c7a941e36251ed341a9aa0a6a2eae9`；固定Go映像與來源指紋沿目標182。候選工作區`workplace/reports/goal182-platform-preflight/20261004-windows-zip/`。沒有把舊Wine主選單收據當成本版驗收。

## READY契約

- 既有封裝器新增明確`--format windows-zip`，只接受Go建置資訊為Windows amd64的前端，Go版本與工具相同；Linux tar.gz／AppImage守門保持。
- 共用13份TSV、全部必要字模及原版指紋。授權以實際Windows二進位模組收集，包括Windows專用hideconsole；不直接照搬Linux模組清單。只允許包內前端`bin/colonization-window.exe`，原版EXE、存檔及資產仍不得入包。
- 包內批次啟動器從Linux唯一完整命令產生，以ASCII／CRLF寫入。旗標及參數順序不變，路徑轉為Windows分隔符，使用`--game "C:\路徑\COLONIZE"`，其餘前端參數轉送。延遲變數展開關閉，資料路徑含空白、驚嘆號與中文需實測。
- 缺原版目錄或VICEROY.EXE拒絕並返回2；--help在沒有原版時可讀。原版仍只讀，存檔預設`%LOCALAPPDATA%\colonization-cht\save`，COLONIZATION_CHT_SAVE可覆寫；沒有可用位置則拒絕。批次檔不改永久環境與系統設定。
- README.txt採UTF-8 BOM／CRLF，列出資料匯入、存檔、音訊／鍵鼠、授權與Wine／真機驗證限制。ZIP固定檔案順序、權限與1980-01-01時間，使用Python zipfile；所有非ASCII名稱必須有0x800旗標，用額外中文根目錄候選驗證。
- manifest保存每檔SHA-256、大小、平台、ZIP格式、來源啟動器指紋與依賴授權；自身不做遞迴雜湊。正式輸出排他建立版本目錄及SHA256SUMS，測試版本只留workplace。
- 候選須兩次位元組全等、獨立解包清單／編碼／原版排除、包內批次檔的Wine正常主選單、相同GUI實際輸入的Windows／Linux無頭重播。完成DRAFT審查後才授權正式接線；正式接線後重建與抽樣另驗，不覆寫候選。

## 候選證據與審查

現行來源再交叉建置，與前一份Windows二進位逐位元組相同。修正候選c／d各13973262bytes，SHA-256 `65a607e316926f28851e6aaff776d9573dc0511cbd3a8c91a5b647e0494ae916`。獨立解包95檔，manifest、13份TSV、字模、8個實際Go依賴及授權、README BOM／CRLF、批次檔ASCII／CRLF、中文ZIP根目錄0x800旗標與原版排除均通過，入口為candidate-check-v2.json。

CMD將未加引號的`--play=false`拆成`--play false`，Go布林旗標因此提早停止讀後續參數。arguments-probe.json直接列出該差異；候選a／b及未正確轉送驗收旗標的v3逾時保留。候選c／d在參數收集時重組true／false值，保留原命令與其他數值／路徑參數。這是啟動器參數缺陷，不是原版行為缺陷。

Wine的初次CMD引號呼叫失敗保留。cmd-diagnostic.json確認CALL可啟動含中文、空白、驚嘆號與&的路徑；cmd-exit-control.json用最小exit /b 2證實本Wine CALL把非零返回碼轉1。缺原版拒絕仍以同字節啟動器的ASCII路徑直接呼叫核對，返回2；沒有放寬產品契約。驗證容器locale明確為C.UTF-8，不改正式玩家環境。

candidate-smoke-v4從ZIP包內批次檔以正常鍵鼠至主選單，26M擷取完整1280×800視窗，五列及版本已中文。Windows與Linux無頭重播同一實際GUI輸入，到50M完整CPU狀態、1MiB RAM、64000bytes原版索引、768bytes色盤全等；主選單安全區`[320,356,968,584]`逐像素相同。輸入SHA-256 `6921125d499014f08d9b805fc8e1de116774d7ca4ff3b8d5029be822415a3a40`，RAM `599a732f2a40af0902a6a9968814101a6810c285898918c919669fa88d412f98`。兩平台WAV也全等，49715Hz／雙聲道16bit／214642frames，指紋`457e773b1465840fc481c7e004cf20255522ed7ab4b14841cb4826760caded15`；這不是人耳確認。七個宿主開檔名稱大小寫差異逐項保留，DOS名稱正規化後順序與數量相同，不忽略任何記憶體差異。candidate-summary.json為PASS_WINDOWS_CANDIDATE_GUI_AND_REPLAY。

上述證據只授權[Windows組裝器](../../tools/windows_bundle.py)、[Windows說明](../../tools/release/README.windows.txt)與既有封裝器的明確windows-zip分支。正式接線後須另建封包並核對與候選資料／啟動器及已驗收據相同；不擴張正常玩家情境、真機或正式發行聲明。

## 限制

Windows真機與任意系統相容性未驗；正式完整版號、dist-all新版本與Release仍待後續，不改整體中文化Issue狀態。

## 正式工具驗證

公開封裝器兩次輸出formal-a／b，各13973331bytes，SHA-256皆`2fa9630f26f195257170bcc86c78b6f60a5e4a743740e448f4719939e9cfe100`。formal-check.json為PASS_FORMAL_WINDOWS_ZIP，指紋`750be6b4a9fd709f705c001d1f9b5f61fe855b330badf61ba98bc08dcf5e759a`；95檔完整清單、SHA256SUMS、編碼與授權／原版排除通過。二進位、資料、字模、啟動器與授權逐位元組等於已驗候選，差異只有正式說明與manifest。

formal-smoke從正式ZIP包內批次檔，正常鍵鼠至中文主選單，五列與版本全啟用。實際視窗安全區與終點精確相同，輸入及完整原版與候選相同；對話框／字串圖集均載入。check.json為PASS_FORMAL_WINDOWS_GUI_MENU，指紋`f3452cdd0821f4ab84eb2514d6a66906ae40ae6b8088323b281b6ba3c4b29136`。原版在/game與repo內別名皆唯讀，存檔覆寫位置另存formal-smoke/save。

另於未設定COLONIZATION_CHT_SAVE時，正式啟動器使用Wine實際LOCALAPPDATA `C:\users\ubuntu\AppData\Local`，建立colonization-cht/save，並完成1000步空輸入冷啟動。default-save-check.json為PASS_WINDOWS_DEFAULT_SAVE；它只驗預設位置，不當成存讀檔或正常主選單收據。

正式入口拒絕錯平台、非法版號與覆寫既有版本，refusals.json為PASS_WINDOWS_PACKAGING_REFUSALS。共用平台守門改動後，Linux AppImage另重建一次，仍18520568bytes及原指紋`375019a92c20c59a2cef726aeba9e3e77181b1b69bdccfec46df94e6b6b91fcf`。沒有重跑完整GUI矩陣或改譯稿／字模／遊戲程式；#51維持進行中，最終完整版仍待驗。
