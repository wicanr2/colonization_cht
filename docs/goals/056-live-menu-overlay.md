# 目標 056：主選單即時覆蓋與輸出生命週期

狀態：in_progress（第一列無頭即時切片通過；第三種情境與互動前端未完成）<br>
日期：2026-09-22<br>
Issue：[#6](https://github.com/wicanr2/colonization_cht/issues/6)、[#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#11](https://github.com/wicanr2/colonization_cht/issues/11)、[#26](https://github.com/wicanr2/colonization_cht/issues/26)

## 已確認與未確認

使用者已確認 [目標 055](055-first-text-prototype.md) 的 Cubic 11 24px、4 倍輸出大小，
不再等待相同問題。這不是字型散布、全遊戲術語或完成範圍授權。
原版執行檔、資料、規則、輸入與存檔維持原樣；只對輸出副本繪製中文。

## 工作順序與停止線

1. 以同一固定原版及隔離 dosgolem，從正常冷啟動觀測主選單、滑鼠移入／移出、
   反白及點選至難度的事件。至少三種不同輸出情境，不能拿同種選項的三列湊數。
2. 根據真實事件檢查來源鍵、原文字遮罩、背景、重繪、游標遮擋與場景失效；
   不以固定整幀雜湊永久綁住即時畫面，不用猜測的純色矩形抹除文字。
3. 審查最小 READY 規格；正式通用攔截／合成能力只進隔離 dosgolem，遊戲定位留本案。
   未證實情境維持原文並記錄，不把未知直接寫成正式行為。
4. 接通至少一列即時覆蓋；驗證中／英文切換、缺譯／缺字、錯版本、游標、切場與
   實際玩家輸入後原版狀態一致。沒有即時程式證據就只報研究或原型完成。
5. 同步 Issue、來源清單與現況；原版畫面、字型、傾印都留本機，不打包發布。

## 分工與入口

- 主代理：採用決策、規格審查、整合與正常路徑驗收。
- 工程子代理：[tools/trace_menu_lifecycle.go](../../tools/trace_menu_lifecycle.go)、
  [tools/probe_menu_lifecycle.py](../../tools/probe_menu_lifecycle.py)，只讀觀測實際生命週期。
- 翻譯子代理：[tools/review_translation_draft.py](../../tools/review_translation_draft.py)，
  校對既有 50 筆與字型覆蓋，不擅自擴大術語決策。
- 工具查核子代理：檢查現有公開 oracle API 可用性及最小缺口，不自行重設架構。
- [tools/bake_local_font.py](../../tools/bake_local_font.py)：從確認字型與唯一譯文產生本機 Alpha。
- [tools/live_menu.go](../../tools/live_menu.go)：以執行中的原版事件逐幀合成第一列，不讀舊畫面冒充即時輸出。
- [tools/probe_live_menu.py](../../tools/probe_live_menu.py)：建置固定隔離版本並驗證原版狀態未受中文影響。
- [tools/verify_live_images.py](../../tools/verify_live_images.py)：獨立像素對照回退畫面及已確認原型。

基線：[目標 054](054-main-menu-text-provenance.md)、[規格草案 009](../spec/009-first-text-overlay-draft.md)。
精確觀測能力：[規格 010](../spec/010-instruction-observer.md)。
通用合成能力：[規格 011](../spec/011-output-patch-compositor.md)。
本輪的步驟屬於上述既有 Issue，不另造重疊工作清單。結束時填入實際收據與未完成界線。

## 本輪結果

- 固定原版來源／雜湊沿用目標054；舊執行器 `22664265ea7d55ea8706448149908c79d3f0897b`
  兩次冷啟動各有16個印字事件、13檢查點，71份二進位收據完全一致。
- 文字情境目前只有標題（已展開變數）與一般選項；三列同類不算三種情境。
  難度畫面已到達，但此入口未捕捉其文字，Issue #6仍開放。
- 新隔離執行器 `315d17f6697bcd4040b12749a1038fdf677338f8` 增加精確只讀觀測及通用
  合成器；主代理重跑完整 `go test ./...` 通過，補片套件測試敘述覆蓋100%。
- 第一列3次印字完成、272顯示幀，其中22幀安全吻合並即時套用中文；15檢查點中3張中文。
  中文與6個控制組（原文、缺字模、缺譯文、過期字模、過寬字模、缺字模檔）的原版最終
  CPU、完整RAM、畫面、色盤、步數、計時器刻、幀數與CPU週期全部一致。
- 105張圖由獨立Pillow解碼核對；回退畫面與原版逐像素相同，中文差異只落在安全區，
  清晰中文畫面與使用者確認原型逐像素相同。切場後補片已撤銷，不殘留中文。
- 50筆譯稿來源／占位符通過、缺字0；只有第一列有已確認安全矩形，其餘49筆不宣稱版面通過。

已知限制：游標遮到第一列時整列回退英文，移開恢復；未實作游標獨立中文合成。
沒有互動視窗前端，不是完整可遊玩的中文化版；Issue #26不關閉。本輪不另要求已同意的字體大小。

## 重跑命令

專案根目錄執行。沿用既有映像，不安裝主機runtime；各來源須存在，輸出目錄須為目前UID/GID。
字型仍是只讀本機研究來源，衍生Alpha不加入Git。先產生字模：

```sh
test -d tools && test -d workplace/reports &&
test -d "/home/anr2/cht/psychic-war/workplace/font-cmp" &&
test -d "Sid Meier's Colonization (1994)/SMColoni/COLONIZE" &&
timeout 30 docker run --rm --network none --memory 512m --cpus 1 --pids-limit 64 \
  --user "$(id -u):$(id -g)" --entrypoint python3 -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/repo:ro" -v "$PWD/workplace/reports:/out" \
  -v "/home/anr2/cht/psychic-war/workplace/font-cmp:/fonts:ro" \
  -v "$PWD/Sid Meier's Colonization (1994)/SMColoni/COLONIZE:/game:ro" \
  rich2-py:latest /repo/tools/bake_local_font.py --game /game \
  --font /fonts/Cubic_11.ttf --output /out/goal056-font-mask.json
```

再執行正常路徑對照。建置使用容器暫存 Go workspace，不改使用者 go.mod、不下載模組：

```sh
test -d workplace/dosgolem && test -d workplace/gocache && test -d workplace/reports &&
test -d "Sid Meier's Colonization (1994)/SMColoni/COLONIZE" &&
timeout 360 docker run --rm --network none --memory 2g --cpus 2 --pids-limit 256 \
  --user "$(id -u):$(id -g)" -e GOCACHE=/cache -e GOTOOLCHAIN=local \
  -v "$PWD:/repo:ro" -v "$PWD/workplace/dosgolem:/dosgolem:ro" \
  -v "$PWD/workplace/gocache:/cache" -v "$PWD/workplace/reports:/out" \
  -v "$PWD/Sid Meier's Colonization (1994)/SMColoni/COLONIZE:/game:ro" \
  colonization-research:20260920-r2 python3 /repo/tools/probe_live_menu.py \
  --dosgolem-commit 315d17f6697bcd4040b12749a1038fdf677338f8
```

補丁重建版本可傳入重建後的本機commit；權威tree為 `e223a8c97204df98ff444e32cdb0ec205b187e90`。
累積補丁與重建基底見 [CONTEXT](../../CONTEXT.md)；不得改用未識別的dirty工作樹。

最後驗證PNG（只有明確輸出目錄可寫）：

```sh
test -d tools && test -d workplace/reports &&
timeout 30 docker run --rm --network none --memory 512m --cpus 1 --pids-limit 64 \
  --user "$(id -u):$(id -g)" --entrypoint python3 -e PYTHONDONTWRITEBYTECODE=1 \
  -v "$PWD:/repo:ro" -v "$PWD/workplace/reports:/out" \
  rich2-py:latest /repo/tools/verify_live_images.py
```

同研究容器掛載可執行 `probe_menu_lifecycle.py`，再用
`--prefix goal056-lifecycle-replay --compare goal056-lifecycle` 比較兩次舊基線。
字型容器可執行 `review_translation_draft.py --game /game --font /fonts/Cubic_11.ttf
--output /out/goal056-translation-review-mechanical.json` 重生機械校對，不覆蓋人工意見。

本機收據：`goal056-live-receipt.json`、`goal056-live-images.json`、
`goal056-lifecycle-replay-comparison.json`、`goal056-translation-review.json`；
均在 `workplace/reports/`。圖片入口 `goal056-live-zh.menu-clear.png`。
收尾容器、產物擁有權、原版未追蹤狀態另記 WORKLOG。
