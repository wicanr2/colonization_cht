# 規格069：主選單背景與重複底紋

狀態：DRAFT。目標186／Issue #63。正式顯示仍為規格068的66種素材。
本規格不授權改動原版程式、規則、資料、存檔或玩家操作。

## 範圍與來源

先處理正常冷啟動的主選單底紋與背景。三種底紋均先解碼到獨立的32×24 RAM畫布，
只有OPENTILE在本批四個主選單檢查點有可見複製。檔名只作定位，未見內容不推定用途。
來源列編號是研究清冊的鍵，原版三種底紋的AX均為1、幀序號均為0。

| 檔案 | SHA-256 | 研究列 | 原生尺寸 |
|---|---|---:|---|
| VICEROY.EXE | a17ed64c27671e5e95236e54a7ddc85803a96ba822fbed05e1dad34d3917e2e3 | 不適用 | 不適用 |
| OPENTILE.SS | 078cc88895ca523498cdcb90d29684ceb0f311007a53a4a20d16b17db7514402 | 1265 | 32×24 |
| PARCH.SS | 5ba57f44f97e5616dc0fb3d4755de9d1dd75a7e060f4e601c286230d17b72113 | 1287 | 32×24 |
| WOODTILE.SS | 7b689b766b0f9027627b1a731d8e813a38678b21be41e00d294ecb2cd41ec89c | 1552 | 32×24 |
| OPENMENU.PIK | f25c313c66a8f49bf79487fcecbcf76dafff2a81b713f2f3cb2e2d4349fd2004 | 1181 | 320×200 |

原版引擎為獨立dosgolem副本82a14b266e1b5bc904e2d0fe507daf6bea41a013。
Go 1.26.7；研究解碼沿固定mpskit 8c30544b51d1b4ab68f3a465784239c24b660e24。
解碼清冊e0b14a6ba8a8bec5cae3fd165ea6d88de384dc4f61c1ec67ca8504c29189aa5d。
以下位址均為dosgolem實模式CS:IP或20位元線性RAM，沒有混用IDA位址。

## 原版證據

本機根為`workplace/reports/goal186-display-hd/hd-cold-start-sources-r65/`。
原版畫面、色盤、逐寫資料與生成候選只留本機；公開索引不含原版像素。

- confirmed：R49入口探針原本只在50000000步後觀測。本次從步數0觀測，
  同一53筆正常GUI輸入與49個檢查點得到2022次入口呼叫，比原先多17次。
  1948次唯一匹配、74次保留別名集合，沒有未匹配呼叫。後50000000步的2005次
  呼叫與R49逐筆相同。來源命中不等於玩家可見或HD已完成。
- confirmed：預設起點重生的Go與R49原來源逐byte相同。
  原版有／無觀測的49個完整狀態、影像、色盤與兩份存檔相同。
  `entry-start0-r1/check.json`記錄工具版本、來源與二進位指紋。
- confirmed：三個底紋均從0D46:000A進入，入口12bytes為
  `c828000052535057568b4702`。各768個像素由原版寫一次，
  返回後整個32×24畫布與解碼來源相同。原版索引253為透明標記，但三張均全不透明。

| 來源 | 入口步數 | 返回步數 | 目的線性RAM |
|---|---:|---:|---|
| WOODTILE | 17662267 | 17675992 | 404160 |
| PARCH | 17705268 | 17719757 | 404960 |
| OPENTILE | 17750547 | 17764234 | 181952 |

- confirmed：0CBA:009C、009E及00CA的逐byte／word複製，可由實際DS:SI、
  ES:DI、原始碼及來源位元組重建。OPENTILE有8320筆來源複製，
  四個正常主選單檢查點各6332個可見來源格。未知寫入包含同值寫入均撤銷來源。
  WOODTILE與PARCH在此7筆輸入／4點前綴沒有可見複製，不推定它們不可達。
- confirmed：OPENMENU.PIK在17840250至18362970步，由11B5:04EE與054A
  對線性RAM 0x3c500寫入64000個像素，每點一次。重建指紋
  5325a3501b83df510cee60c134952130fdb9dfd4bdc00d9eb853fb7ae6021eff
  與解碼來源完全相同。
- confirmed：18369329步的0C9F:00CA複製開始時，直接讀取
  `Mem[0xa0000:0xafa00]`與PIK來源有1838個差異，整張比對未命中。
  原始資料與拒絕結果保存在`background-public-r5/observed/`。
  這份線性記憶體讀值未被宣稱為平面模式的實際可見索引畫面。
- 未知：PIK解碼後的上傳、顏色轉換與VGA往返來源生命週期。不得以局部相似度、
  忽略差異或把直接RAM讀值當成可見畫面，強行接入整張HD背景。

R5逐寫範圍包含普通RAM及A0000視窗，但dosgolem的平面模式寫入會走獨立VGA資料，
不保證都出現在一般WatchWrite。原版前綴狀態與原R1／R2保持，沒有修改dosgolem。
需要平面顯示時應使用dosgolem的可見索引介面，讀取VGA硬體視窗可能改變latch，
不可為了蒐證額外讀取而改變原版執行。

## 可重現入口

- [全SS入口組裝器](../../tools/build_hd_full_entry_probe.py)：`--start-step 0`
  包含啟動初段；預設50000000保持原有R49範圍。負值與超過50000000拒絕。
- [背景逐寫組裝器](../../tools/build_hd_background_source_probe.py)：
  `--entry`指定上述步數0輸出，`--reference`指定既有Go模組，
  `--output`指定新的`/out`子目錄。輸出Go、固定前綴檢查點與建置指紋。
  PIK缺失明確回傳77，錯誤版本拒絕；不安裝HD。
- [獨立來源檢查器](../../tools/check_hd_background_sources.py)：
  `--root`指定有`observed/`及`control/`的探針輸出，
  `--decoded`指定R49固定解碼根，`--output`指定新目錄。
  核對完整原版狀態、寫入、每個目的來源格及拒絕的整張比對。
- [來源索引](../../tools/build_hd_source_index.py)可追加
  `--cold-start-entry-report`及`--background-source-report`。
  新證據與既有正式66種素材分開記錄，不增加完成數。

Docker使用既有`hr-go-ebiten:1.26.7-2.9.9-r1`建置與執行，檢查器可用
`colonization-verification:20261007-runtime-r2`。工作樹、原版及dosgolem唯讀掛載，
輸出目錄用UID/GID 1000:1000寫入，預設斷網並設定資源與外層逾時。
本機`commands-r65.json`保留確切命令。

## 生成候選與下一個閘門

沿使用者已定稿的精細像素風，以內建imagegen產生背景v1、v2及深色木紋v1。
原PNG未裁切或重編碼；提示、參考指紋與輸出指紋見本機
`generation-results-v1.json`及`candidates-index-v1.json`。

| 候選 | 原PNG尺寸 | SHA-256 |
|---|---|---|
| 主選單v1 | 1586×992 | 29566b6b9f0921b05cd715aaddabe41c818508b3aa6bd10d823e72173f4acf34 |
| 主選單v2 | 1586×992 | 2d688773ecc1bf1a1555d53d632f33fa571cf25a0ea930d38b5219b61ddc819f |
| 深色木紋v1 | 1448×1086 | cb2a8af8077d1e6fd0082d753e7cc0251192df0705ebe34496f1954f5cdc4547 |

v2沿原版下方金邊的位置修訂。三張都是DRAFT候選，沒有加入正式清冊或README。
下一步先將已驗OPENTILE做隔離合成，採32×24來源幾何、128×96顯示取樣與逐寫撤銷。
欄位文字、游標、設定切換及其他覆蓋先後順序須有正常GUI證據。
768個來源格的局部索引不能沿用既有8×8來源的byte欄位。
色盤不同時須維持原版並記錄，未量測的新色盤不能套用候選。
背景分支另補PIK上傳與VGA往返證據，再審查READY；不得因候選圖已生成而跳過。
