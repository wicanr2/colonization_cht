# 目標106：開場字幕 `@BUILD1` 的中文覆蓋閘門

狀態：completed（印前證據與可丟棄樣本；正式字幕待使用者選擇）；日期：2026-09-24。承接[目標105](105-first-tutorial-player-path.md)
已證實英格蘭正常玩家路徑上的英文開場字幕，對應
[Issue #7](https://github.com/wicanr2/colonization_cht/issues/7)、
[Issue #26](https://github.com/wicanr2/colonization_cht/issues/26)及
[Issue #27](https://github.com/wicanr2/colonization_cht/issues/27)。

## 玩家問題與範圍

國家介紹 B 頁後，原版 `GAME.TXT:@BUILD1` 在畫面上顯示一行英文，
目前只有來源、逐字印字及畫布差分證據；繁中「主後一千四百九十二年，」
仍只是 TSV 草稿。本輪要讓這個實際可見的訊息向正式中文顯示邁進，
但不把預讀的 `@TUTORIAL1` 當成已顯示，也不改原版 EXE／TXT、
遊戲規則、存檔或玩家輸入。其餘國家、其他 `@BUILD` 字幕與
四國介紹長文不自動套用本欄字級或事件鍵。

## 工作與退出條件

1. 先核對 Git 作者、PRIVATE 遠端、Issue 狀態、原版與玩家輸入
   SHA、隔離 dosgolem 的禁推設定；**先推送本目標**，再更動探針
   或正式程式。原版、完整原文、印前畫布與字模只留 `workplace/`。
2. 在已驗英格蘭正常玩家路徑，以 dosgolem 雙次冷啟動及無讀寫
   監看控制，擷取 `@BUILD1` 第一筆 `0D21:012C` 畫布寫入前的
   真正背景；固定原文來源、`0D21:00C6` 逐字讀取、印字後
   320×200 索引畫面、調色盤及印字範圍。觀測不得改原版機器狀態。
3. 由原版 9px 墨跡高度與單行畫面空間，逐欄量測 Cubic 11
   的繁中字級、墨跡寬高、位置、基線與安全矩形；製作可丟棄
   的四倍畫布樣本，明列超界、背景、游標及缺譯回退策略。
   若存在實質不同的視覺取捨，先交由使用者依樣本決定。
4. 審查[規格026](../spec/026-build-intro-and-tutorial-prefetch-draft.md)
   是否具備 READY 所需來源鍵、頁相位、輸入／輸出及失敗模式。
   未達 READY 只保存 DRAFT 證據與樣本，**不**接正式輸出層；
   達 READY 後才實作 Ebitengine 字幕覆蓋，與同輸入英文控制、
   既有十七欄回歸做同狀態驗證，通過才限縮標為 CONFORMED。
5. 建立獨立失敗即關閉檢查及錯版／缺原版 SKIP 負例；更新
   `CONTEXT.md`、`RESEARCH-LOG.md`、`WORKLOG.md`、唯一
   `docs/worklist.json` 並重生 `WORKLIST.md`。推送私有成果、
   更新並回讀相關 GitHub Issue；核對沒有原版素材入 Git、
   沒有 root-owned 殘留及 Docker 容器清理。

## 證據與停止線

- 原始 `GAME.TXT` SHA-256：
  `67a6b5e22d1addc1ae13658d0d7824622f6d21c6c2bfdefc91f9749450cc2e3a`。
  字幕 `@BUILD1` 的檔案標記位移 `0x153B0`、可見英文起點
  `0x153CE`、印字呼叫點 `0D21:00C6`、寫畫布點 `0D21:012C`；
  上輪已驗可見 bbox `[16,30,303,39)`。詳細收據見規格026。
- 既有十六筆玩家輸入 SHA-256：
  `a48ae77b9f6a0c2bdb9b3512625d0c1c4786b1cb64b8deff4bdb603fe422d93e`；
  dosgolem 僅用 `workplace/dosgolem` 的隔離副本。
- 本目標只處理一條字幕的輸出層。它不能使24則 help、其餘字幕、
  國家介紹長文或整款遊戲取得「中文化完成」聲明。

## 本輪結果與下一閘門

已完成本目標的證據與可丟棄樣本階段；正式輸出分支仍待
使用者確認 A／B，規格026保持 DRAFT。探針在英格蘭正常
玩家路徑的88,689,058步取得原版印前底圖 SHA-256
`d8d0d8e5de5655411fd4935d2b96e6e84845ee924658668f9486196ede9882ab`；
雙重播與無監看控制同狀態。印前至90M印後只差原字幕的
1,040點，墨跡高9原版像素，三種新色號為14／47／54。
本機安全矩形候選為原版 `[12,27,307,42)`；固定字型
38px的 A 實際墨跡430×35px，42px的 B 為482×39px，
兩者都不越界。並列對照留在忽略版控的
`workplace/reports/goal106-caption/comparison.png`，
不冒稱 Ebitengine 正式畫面。

`tools/check_goal106_caption.py` 獨立核對原版、雙重播、控制、
TSV、字型與候選 A 的畫素；`tools/test_goal106_caption.py`
的缺原版 SKIP、錯字級、破損畫布、雙重播變異負例 PASS。
本機收據 SHA-256
`54b1e99255e49848eaa8810fc0063c5dcae38d990dbb84cd3ec147ec7ba4cf6b`。
下一步取得使用者單一視覺選擇，再審查 READY 的執行期
事件與失敗即關閉條件；這輪不增加十七段正式中文顯示數。

## 本機重播入口

先依專案 `AGENTS.md` 驗證每個掛載來源，使用限資源、
無網路、非 root 的一次性 Docker；將本儲存庫掛 `/repo`
可寫、隔離 `workplace/dosgolem` 掛 `/dosgolem` 唯讀、
合法 `COLONIZE` 目錄掛 `/game` 唯讀。容器內：

```sh
cd /dosgolem
GOCACHE=/tmp/goal106-go-cache /usr/local/go/bin/go build \
  -o /tmp/goal106-probe /repo/tools/probe_goal098_intro.go
/tmp/goal106-probe -root /game \
  -inputs /repo/workplace/reports/goal083-post-difficulty/goal084-window-full.inputs.json \
  -nation england -next-enter -after-b enter -after-follow enter -preprint \
  -out /repo/workplace/reports/goal106-caption/england-enter-a
```

以新的輸出前綴重播第二次；控制組移除 `-preprint`、
改加 `-control`。不可覆寫本輪已驗收據。字型樣本另在
`rich2-py:latest` 容器中，把[固定字型來源](../../font/README.md)
所在目錄唯讀掛 `/font`，呼叫
`tools/preview_goal106_build_caption.py --help`；
再以 `tools/check_goal106_caption.py --help` 核對三份報告
及樣本。原版、字型或固定輸入缺失時，明確 SKIP，
不以公開 Git 內容冒充原版對拍。
