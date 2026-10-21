# 工作歷程

既有工程歷程已[封存](docs/archive/WORKLOG-through-20261021.md)。原首頁工程說明見[首頁封存](docs/archive/README-engineering-20261021.md)，現況入口為[CONTEXT.md](CONTEXT.md)。

## 2026-10-21 R147 首頁整理、工程紀錄封存與Issue核對

- 使用者要求首頁保留截圖及Remastered已完成內容，工程與既有WORKLOG封存。知識路由命中README完成度、文件職責及未完成項入口，沿目前程式與現有驗收收斂，沒有重新開啟原版調查或遊戲測試。
- 首頁保留原有32張截圖，圖檔位元組不變，改寫圖說與玩家可見的已完成內容。保留現行本機版與舊公開版的差別，不將來源接線或尚待人工驗證的畫面聲稱為全遊戲百分之百完成。
- 舊README及R146以前工程歷程移至docs/archive，新增首頁與現況入口，調整相對連結、工作清單引用與兩個歷史檢查器的檔案讀取路徑。根目錄WORKLOG作為後續唯一歷程入口，不複製封存正文。
- 片頭MPS旋轉標誌16幀及遊戲標題已於規格069 R113接線並通過來源測試畫面，船隻、太陽、雲、煙與魚形的既有正常路徑驗收保持。這是原版動畫的HD影格覆蓋，未增加完整片頭或獨立3D模型驗收聲明。
- 主機gh auth status成功，讀回遠端未關閉Issue。#61已有既定功能完成審查，依使用者本輪明確關閉授權，於2026-10-21T04:52:29Z關閉並回讀CLOSED。#53、#55、#58至#60、#62至#64仍有對應未完成或未確認範圍，保持OPEN；沒有將所有Issue直接標成完成。
- WORKLIST由docs/worklist.json重生，#61同步completed，靜態完成入口不取代既有GUI證據。本輪只核對文件連結、圖片雜湊、狀態資料、語法及擁有權，沒有新GUI、遊戲、Go測試或全矩陣。
- 文件整理與核對使用有界非root、無網路Docker，容器由--rm清除，無專案殘留。原版資料與本機AppImage保持，只有文件、狀態及必要引用修正提交與推送。32張圖片雜湊、封存前後379個連結的來源與UID／GID1000已核對，無root-owned檔或錯誤.md目錄。收據見既有R84工作根r147-readme-archive-r1.json。

## 2026-10-21 R148 三平台雙類完整版、建城實錄與人工待驗交接

- 使用者要求三平台各交付「HD＋原版＋中文化」與「原版＋中文化」，推廣片包含進入新局及建立第一座城鎮，相關Issue結案，剩餘人工待驗。路由載入dist-all、版號、FFmpeg與原版影音來源契約；收尾另載入README及機器可讀工作清單入口。沒有恢復全矩陣、Go測試、vet或額外原版調查。
- 正式版號v.1.0.8-20261021，81份既定Go組裝來源不變，僅重建內嵌版號。Linux程式SHA-256為5c07ef50b8679fc3eda85cc7dca22c533e1aa664dbf4300decefd8b591c900ac，Windows為85d337066f36eaa320f37bd33ad1a3c8cb4a011af067956923c470d0bfd0a7aa；macOS雙切片與通用檔指紋見r148-build-macos-r1.json。
- 共用封裝器新增Windows／macOS的成對本機完整版，保留原版資料日期、平台啟動器與各自存檔位置。六包均實際解出逐檔核對版號、288個原版、328個語言資源、Noto與素材清冊；HD三包各387素材檔，原版三包沒有graphics目錄。Windows說明UTF-8 BOM／CRLF、啟動器ASCII／CRLF，macOS兩架構簽章頁已核對。這些是封包證據，Windows／macOS真機與Gatekeeper留人工。
- 正常空存檔新局以本版程式及原版圖像錄下航海、登陸、單位輪替與B建立Jamestown，正常選單存成COLONY00.SAV，SHA-256為5d0792f58601807a3e64285cd464c1b21781f9ac9c821359987acd7b2f5fed8e。沒有RAM改寫、direct-entry或載入既有存檔冒充建城。其後從同版HD AppImage解出內容，在Ada正常載入同一存檔，錄製HD城鎮與建築操作。兩段版本與程式指紋相同；原始影片、正常輸入、截圖與存檔只留本機。
- 依使用者後續要求降低本機CPU，停止本機遊戲錄影，改用指定Ada主機。RTX 2000 Ada 16GB／NVIDIA 595.91.07、VirtualGL EGL的OpenGL實際列出NVIDIA renderer，GPU程序同時可見colonization-window與NVENC ffmpeg。只確認前端顯示與編碼能力，DOS模擬與來源覆蓋不宣稱移至GPU。沿既有kdzz-gpu-verify:20261021-r1映像，無新映像；Pillow11.1.0依遠端cp312 ABI及固定輪檔SHA安裝到當次工作區。
- 先前錄影控制器有摘要null、啟動變數與驗證模式等工具問題，4GiB錄影容器另遭cgroup OOM；這些分類為錄影環境，失敗輸出保留。改為正常play模式及8GiB後完成新局。遠端SSH最初未掛代理而無法登入，掛入既有代理後成功；直接Docker權限不足，使用現有sudo -n Docker。自動核准審查先拒絕含原版完整包傳送，使用者另外明確授權暫存並要求完工刪除，才實際傳送。
- 影片90秒、1920×1080／30fps H.264＋48kHz雙聲道AAC，含78秒實際遊玩，部分剪接加速。原版OPL既有連續錄音作後製配樂，非同步音效。格式、非靜音、最高音量-2.3dB、無黑幀與13張畫面及字幕抽樣通過；靜止段對照原版回合、對話與片頭片尾，未以圖片代替建城。成片12019601 bytes，SHA-256為66af7b19631579d928480d01a9506e31b8d8bcd239939966489b4c365e6cc3e6。人耳與未抽樣畫面保持人工待驗。
- 六包、影片、完整SHA256SUMS與驗證摘要已由tools/package_full_release.py彙整到dist-all/v.1.0.8-20261021。tools/build_gameplay_promo.py保存影音核對與可選NVENC入口，兩支工具由規格044及目標186索引。完整包、原版與影片不提交、不上傳公開端，沒有新tag或Release；既有公開v.1.0.3及本機v.1.0.4／v.1.0.6／v.1.0.7保留。
- 主機gh auth status成功後，依使用者本輪結案決定關閉#53、#55、#58至#60、#62至#64，八項遠端回讀CLOSED。現行譯稿、1975項普查／933shown／950pending／92unreachable與HD證據等級保持，不將結案聲稱為全中文、全HD或原版精確對拍驗收。錄影仍可見部分原文回退，後續由使用者人工登記。docs/worklist.json同步交付狀態，WORKLIST.md由工具重生。
- README保留32張截圖，更新三平台交付與實錄成果；CONTEXT目前狀態表與目標186記錄交付、GPU能力及人工限制。歷史封存不重寫。Ada的原版、完整版、存檔與錄影暫存回傳核對後，1330檔／1751476331 bytes已刪除；本機只清掉本輪已核對的重複封包、傳輸tar與Go快取，共2406387222 bytes。舊交付、原始輸入、HD原PNG、正常輸入與建城存檔保持。

本機收據沿既有R84工作根：r148-six-package-inventory-r1.json、r148-first-colony-capture-r5/first-colony.json、r148-first-colony-hd-r6/gpu-runtime.json、r148-promo-r1/validation.json、r148-issue-close-readback-r1.json、r148-ada-cleanup-r1.json及r148-local-cleanup-r1.json。

收尾靜態檢查：64項工作清單訊號、32張原有圖片連結、變更文件本機連結、生成素材清冊指紋與UID／GID已核對。無原版檔案或dist-all／workplace被追蹤，無root-owned檔或錯誤.md目錄。本機專案容器與Ada本輪容器均無殘留，遠端當次目錄確認不存在。入口r148-final-checks-r1.json；這些檢查不增加遊戲畫面驗收。
