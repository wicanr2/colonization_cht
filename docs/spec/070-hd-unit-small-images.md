# 單位小圖像的來源與HD覆蓋

狀態：DRAFT，2026-10-17。擴充ICONS.SS唯讀來源研究，正式HD仍為73張生成原PNG。本規格尚未授權新幀的正式覆蓋。

## 範圍與來源

涵蓋尚未接線的船隻、人物、火炮及其他單位小圖像。既有31來源的正式契約維持[規格065](065-hd-small-images.md)；完整範圍與完成條件維持[目標186](../goals/186-display-settings-and-gameplay-video.md#全量覆蓋與完成判準)。

| 輸入或工具 | 固定版本或SHA-256 |
|---|---|
| ICONS.SS | a8a21f052d2e6c9ede34a6cb254b05f2036322031f7ab0ccb0859adf9b6e0716 |
| VICEROY.EXE | a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3 |
| 原版SS／PIK解碼收據 | e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d |
| 唯讀基底探針 | tools/probe_hd_building_batch.go，5d25d74f156f582678abda65745635946884425e81abbc9bea134766399d7bb6 |
| dosgolem隔離副本 | 82a14b266e1b5bc904e2d0fe507daf6bea41a013 |
| 編譯與檢查 | Go1.26.7、Python3.11.2、Pillow9.4.0 |

逐幀原始序號、尺寸、完整編碼、索引指紋與區段位移沿[來源索引](../hd-source-catalog.json)。位址採dosgolem實模式CS:IP與20bit線性RAM，不能當作IDA位址。

## 唯讀研究契約

- [組裝器](../../tools/build_hd_unit_lifecycle_probe.py)載入全部131個ICONS候選及完整SS清冊的編碼別名。原始序號與AX低15bit、尺寸及完整編碼須同時相符。全清冊有多個候選時記錄集合，不授予來源身分。
- 從冷啟動第0步觀測0D46:000A，核對原碼c828000052535057568b4702、堆疊與描述子。返回須符合原CS:IP、SP增加10及100000步上限。
- 主畫布0x2CAE0及暫存畫布0x3C500分別觀測。來源寫入、透明底圖、周圍底圖、實際指令碼、返回邊界及來源撤銷均保存；未知寫入包含同值寫入。
- 高位、裁切、其他描述子及編碼別名保持未驗，不因一張圖看起來相同就套用。未命中幀與空幀不排除全量範圍。
- GUI以既有合法存檔、正常載入與選單操作取得。所有截點由畫面外設定暫停，保留完整CPU、RAM、可見索引、DAC與實際輸入；X11遊戲區須與標準診斷PNG相同。
- 逐寫觀測、無觀測控制及GUI收據須在相同步數與輸入數相符。來源、索引像素、RAM與存檔不寫入原版。
- 逐寫事件以串流JSON保存，上限800萬筆；呼叫與每次繪製也有原有界限。研究工具不被正式組裝器引用。

組裝時指定--catalog為R49本機decoded-public-r3/catalog.json，--gui-capture為正常GUI的capture.json，--inputs為其gui.inputs.json，--reference為R49 small-public-r1模組，--output為新的/out子目錄。輸出包含small-probe、points.json及build.json。探針以--root、--seed、--inputs、--sources、--lifecycle-points及--out執行；另加--control產生無觀測對照。所有命令只在有界Docker內執行，/game與dosgolem唯讀掛載，原版像素與完整收據留在workplace。

[獨立檢查器](../../tools/check_hd_unit_lifecycle.py)以--observed、--control、--build、--sources、--entry-report、--points及--output核對。--entry-report在本切片指定GUI的capture.json。它從原始事件重建每筆寫入、來源建立、未知後畫撤銷與每個截點的來源圖，不以探針輸出的來源圖自行證明相同；未驗暫存轉送或別名命中會拒絕。

## 目前證據與待決格式

歐洲港口的招募、購買與訓練選單已完成正常GUI研究。131候選中只命中既有31種，沒有新增來源完成數。15個原版截點、41筆輸入、324次完整繪製與122252個事件已由獨立模型核對；至124400000步的完整原版狀態與初始存檔相同。檢查收據為本機hd-sprite-batch-r71/icons-europe-check-r1.json，SHA-256為f82a9853d92cdfd01419ecd996120b95a7a1b5209e7fbac9bb2e5905bbd2668e。

百科返回清單會重設選取列。首個探索腳本後續重複開啟火炮，不能算24種單位驗證。修正後以實際方向鍵重新選取各列，確認23個不同條目；第24次選取循環回首列。

R71正常百科研究已confirmed：80種來源、196次完整繪製、5048144個逐寫／撤銷事件、35個GUI截點與353筆實際輸入。獨立模型重建全部來源，239次同值後畫也撤銷來源；暫存轉送為0，沒有增加這條路徑的信用。80種中包含既有31種，另49種尚未正式接線。至601800000步的CPU、完整RAM、可見索引、DAC及初始COLONY09.SAV與無觀測控制相同，六個真實收據反例均拒絕。

本機根為workplace/reports/goal186-display-hd/hd-sprite-batch-r71。正式工具產生的icons-public-probe-r2/build.json為f1146a68f288fece3a1d8d187de6b82429133069d7c6e181c67483bcb0f42c48；獨立檢查icons-pedia-check-r3.json為f47871e4eb52f5ddd74ff2fc977a53f86d8b5df164b3c9e22e7db84b9aba8eaf。六反例收據unit-model-negatives-r1.json為6f8aa5a7195a4629ce24d417190d1ae30eebfdb74a63165afdbb7ce899320404。

船隻用途由百科標題、正常選取及當次完整來源確認：

| ICONS原始序號 | 正常百科條目 | 原版尺寸 |
|---|---|---|
| 006 | Merchantman | 13×16 |
| 007 | Galleon | 14×16 |
| 014 | Privateer | 13×16 |
| 015 | Frigate | 13×16 |
| 127 | Man-o-War | 14×16 |

[來源索引組裝器](../../tools/build_hd_source_index.py)新增--unit-report與--unit-build，分別指定上述檢查及綁定收據。1552筆既有資料、73張正式素材連結與所有舊證據逐欄保持，只附加80種正常百科來源的數值與雜湊；沒有公開像素。原版音訊與動畫在本切片未驗，不授予信用。

五艘船的圖集及取樣比較保存在本機。原稿採單幀PNG或一張圖集對應多幀，已提出具體原型供使用者決定。尚未更動graphics清冊格式，也未公開候選或接入正式程式。無論選哪種格式，生成原PNG原樣保存；生成原稿數、來源幀數與正式覆蓋數分別記錄。

## 升級條件

1. 新幀的完整來源、正常用途、實際寫入、遮擋與撤除有獨立原版證據。
2. 生成素材與取樣方法沿已確認畫風，比例、位置及互動區域依原版。清冊格式與公開範圍已有使用者決定。
3. 每幀的正式來源守門、逐寫指紋、未知後畫撤銷、游標與RAM還原有明確契約及反例。
4. 正常GUI、五語與原版模式、獨立像素、原版狀態／音訊／存檔、缺件回退與封裝白名單驗證通過。

本規格只處理已驗單位幀。百科圖示命中不能取代世界行走、戰鬥、特殊游標或動畫的驗證，也不能宣稱全量HD完成。
