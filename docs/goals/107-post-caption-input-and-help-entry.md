# 目標107：開場字幕後的鍵盤消費與首則教學畫面入口

狀態：completed（鍵盤相位、十張字幕與首個海上畫面；help 仍待觸發）；日期：2026-09-24。承接[目標105](105-first-tutorial-player-path.md)
對 `@TUTORIAL1` 僅預讀的證據、[目標106](106-build-opening-caption-overlay-gate.md)
對 `@BUILD1` 真正顯示的證據；對應
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)與
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與範圍

英格蘭介紹 B 頁後，正常 Enter 已到英文 `@BUILD1` 字幕；探索性的
100M／115M 再按 Enter 至150M，索引畫面未變。尚不知道後續按鍵有無
被消費，也不知道首則教學何時真正印字。本輪從同一正常玩家路徑，
用 dosgolem 把送鍵、鍵盤待取數、原版畫布變化與開檔相位對齊；
若顯示教學，追其原始來源至實際輸出。不改原版 EXE、資料、規則、
存檔或正式 Ebitengine 中文層。`@BUILD1` 的38／42px版式選擇、
四國介紹長文與姓名顯示仍分別待使用者決定，本輪不代選。

## 工作與退出條件

1. 核對 Git 身分、PRIVATE 遠端、遠端 Issue、固定原版／玩家輸入
   SHA、隔離 dosgolem 禁推；**先推送本目標**，才修改探針或執行
   新重播。分析、建置、測試一律限資源、無網路、非 root Docker；
   原版唯讀，原始畫面與全文收據留在忽略版控的 `workplace/`。
2. 為既有正常玩家探針加入**選用**的字幕後診斷，不變更不帶新旗標
   的舊輸出：在送鍵瞬間及有界檢查點記鍵盤待取數、原版 CS:IP、
   原始索引畫面／畫布／色盤、開檔與 `GAME.TXT` 印字事件。先用
   既有150M資料縮小觀測，再視實際狀態延伸，禁止無界重試或
   修改 RAM 冒充玩家操作。
3. 比較無額外鍵與至少一條正常 Enter 後續分支。關鍵結論須兩次
   冷啟動與無讀寫監看控制同狀態；若命中首則 help，固定檔案
   位移、實際印字、原版文字墨跡和當次畫面。若未命中，記錄
   已觀測窗口及待取鍵數，不把預讀當顯示，也不推論全程不可達。
4. 建立獨立檢查器和必要負例：固定版本、同輸入重播、畫面／鍵盤
   相位、缺原版明示 SKIP。更新[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)
   的證據等級；沒有實際顯示與 READY 規格前，help 不接正式覆蓋。
5. 回填 `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、唯一
   `docs/worklist.json` 並重生 `WORKLIST.md`；必要時只更新穩定
   README 現況。推送私有成果，更新且回讀 Issue；核對原版未入
   Git、檔案擁有權與 Docker 容器清理。

## 固定證據與停止線

- `GAME.TXT` SHA-256：
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`；
  `@TUTORIAL1` 標記位移 `0x1316A`、正文位移 `0x13190`，目前
  只證實在88,380,281步預讀。`@BUILD1` 在88,689,021–
  88,754,524步由 `0D21:00C6` 逐字讀取並由 `0D21:012C`
  寫原版320×200畫布。地址基準、版本與推論界線詳規格026。
- 既有16筆正常玩家輸入 SHA-256：
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`；
  隔離 dosgolem 提交
  `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`。
- 只追玩家可見的下一畫面與鍵盤消費。若剩餘差異只涉及
  PCM／DAC／PIT 或 Sound Blaster 逐週期等待，依專案硬體時序
  停止線採公開規格與合理近似，不深挖原版硬體驅動。
- 本輪即使只取得一則實際教學，也不代表24則 help 全部顯示、
  全遊戲文字已譯完或正式中文畫面增加。由 DRAFT 進 READY
  仍需來源鍵、逐欄字級、安全矩形與回退審查。

## 本輪結果

從固定英格蘭正常玩家輸入冷啟動，在85M按 Enter 後，鍵盤待取數
由1降至0；100M探索分支再按 Enter，亦於100,898,816步前
被取走。無額外鍵與額外 Enter 在250M前的原版畫面／開檔
檢查點相同；此結論有各自兩次冷啟動和無讀寫監看控制。
因此150M仍留字幕不是鍵盤事件未送達。

無額外鍵路徑延伸至1,350M，原版 `0D21:00C6` 在
88.689M、199.163M、307.693M、427.644M、536.922M、
645.341M、753.777M、862.217M、970.656M及1,079.093M
開始十段相異的逐字印字；各段對應固定 `GAME.TXT:@BUILD1–10`
標記與 `LEVN0001–0010.PIK` 的順序。`@BUILD2`含原版
`%STRING0`／`%STRING1` 變數，不能以固定全文鍵套上同一譯文。
由標記、當次 DOS 讀取與印字內容歸屬字幕節屬**強推論**；
未逐指令閉合所有中間 RAM 搬運，不把它升格完整來源鏈。

約1,185M後原版轉入海上遊戲介面；1,200M原始索引畫面
SHA-256 `6b573d93de2513333a5889bc8e04ff2a81d634b8098482fe4327d6360d1cbb16`，
可見英國船隻、海面、右側狀態與上方標題；1,225M起
上方正常選單可見，另開 `CYCLE.DAT`／`MENU.TXT`。
1,200M／1,225M／1,275M／1,325M本機畫面檢視皆未見
首則教學視窗；這只證明抽樣狀態，不能宣稱所有操作或中間
瞬間都沒有 help。`@TUTORIAL1`仍只具預讀證據，正式 help
顯示與中文覆蓋維持零則。

1,350M路徑兩次完整冷啟動 JSON 逐位元組相同；無讀寫監看
控制於全部檢查點的 CPU、完整 RAM、畫布、索引、色盤、
虛擬時間、開檔與鍵盤待取數一致。100M額外 Enter 路徑的
250M雙重播／控制亦一致。獨立
`tools/check_goal107_post_caption.py` PASS，
`tools/test_goal107_post_caption.py` 的缺原版 SKIP、錯版、
破損遊戲畫面、印字、控制與鍵盤負例 PASS；舊不帶新旗標的
100M探針 JSON 與目標105逐位元組一致。本機完整收據
`workplace/reports/goal107-post-caption/receipt.json`
SHA-256 `e120301bb08f05b5a3461cd6fba5334ed25588a5896fa442f50bfd16d647ec58`。
原版畫素檢視圖留在同一忽略目錄，未加入 Git。

下一步以這個**已驗正常海上畫面**為起點，查證首則教學的
正常玩家觸發／設定及實際輸出事件，不能由預讀或本輪
十張字幕推定 help 已顯示。`@BUILD1` 字級待使用者選擇；
其他九張字幕各須獨立文本鍵、變數與字級審查。

## 本機重播入口

先依專案 `AGENTS.md` 檢查每個掛載來源的存在、類型與 UID/GID；
將儲存庫工作樹掛 `/repo` 可寫、隔離
`workplace/dosgolem` 掛 `/dosgolem` 唯讀、合法 DOS
`COLONIZE` 掛 `/game` 唯讀。限資源、無網路、非 root 的
一次性 Docker 容器內執行：

```sh
cd /dosgolem
GOCACHE=/tmp/goal107-go-cache /usr/local/go/bin/go build \
  -o /tmp/goal107-probe /repo/tools/probe_goal098_intro.go
/tmp/goal107-probe -root /game \
  -inputs /repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json \
  -nation england -next-enter -after-b enter -after-follow enter \
  -post-caption-audit -follow-until 1350000000 \
  -out /repo/workplace/reports/goal107-post-caption/england-no-extra-1350m-explore
```

第二次以不同前綴重跑，第三次另加 `-control`；
100M額外鍵分支改為 `-follow-until 250000000 -follow-enter-at 100`，
同樣重跑兩次及控制組。
檢查器為 `tools/check_goal107_post_caption.py`，反例為
`tools/test_goal107_post_caption.py`，兩者 `--help` 列出
`--game`、`--inputs`、`--reports` 及必要的輸出參數。
若合法原版不存在，檢查器回 `SKIP 77`，不得以自製
輸入取代原版；本機原版畫面 PNG 不推送。
