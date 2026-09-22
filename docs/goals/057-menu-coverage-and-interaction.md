# 目標 057：擴展主選單中文與互動入口

狀態：completed（五列無頭切片及前端缺口查核；互動前端仍未實作）<br>
日期：2026-09-22<br>
Issue：[#6](https://github.com/wicanr2/colonization_cht/issues/6)、[#7](https://github.com/wicanr2/colonization_cht/issues/7)、[#11](https://github.com/wicanr2/colonization_cht/issues/11)、[#26](https://github.com/wicanr2/colonization_cht/issues/26)

## 起點與範圍

承接 [目標 056](056-live-menu-overlay.md)：第一列已能在原版執行中逐幀合成中文，
七組原版狀態一致；尚無互動前端，游標遮擋時回退英文。基底提交為 `94ea38d`，
隔離 dosgolem 為 `315d17f6697bcd4040b12749a1038fdf677338f8`。
沿用使用者確認的 Cubic 11 24px、4 倍畫布；只改輸出副本，不改原版規則、輸入或存檔。

## 執行順序

1. 先提交並推送本目標，再進入研究及實作。
2. 對既有正常路徑收據中的其餘主選單選項，逐列核對來源位移、呼叫／返回、
   實際墨跡與背景、參數、重繪及安全矩形；不得僅由相似文字或等距座標外推。
3. 校對對應 TSV 譯文與確認字型的雙軸幾何；未知術語保留草稿，不新增重複譯文來源。
4. 證據足夠後，另以窄規格通過 DRAFT → READY，再擴展適配器及正常路徑驗證。
   各列獨立回退；缺譯、缺字模、版本不符、切場不得殘留或吞字。
5. 查核既有 dosgolem／psychic-war 前端入口及 Docker 工具鏈。先確認輸入座標、按鍵、
   視窗關閉與原版狀態隔離契約；必要時只做可撤回原型，不擅定新平台或操作方式。
6. 保留中／英文同輸入的 CPU、RAM、原始畫面、虛擬時間比較及逐像素安全區驗證。
   更新現況、唯一工作清單及上述 Issue，不將主選單完成外推為全遊戲完成。

## 分工

- 主代理：來源及生命週期證據審查、窄規格、整合與回歸驗證。
- 翻譯子代理：唯讀核對主選單候選、用詞與幾何；不代替使用者決定術語政策。
- 工程子代理：唯讀查核可沿用的互動前端與隔離工具鏈，提出最小接線及測試缺口。

## 退出條件與停止線

- 每個新增正式覆蓋項都有來源、事件、背景、安全矩形與正常路徑收據；不符者保持原文。
- 原版中英文差分及首列既有回歸通過；新增覆蓋數與未知數分開記錄。
- 互動前端有可回查的可用入口與驗證，或明確列出缺件與下一個最小步驟；
  不能以無頭圖片宣稱可手動遊玩。
- 第三種文字情境仍是獨立缺口，不以同類選項數量湊數。靜態圖、字型散布、正式打包
  不在本輪交付範圍；新產品取捨才詢問使用者，已確認字體不重問。
- 收尾記錄 Git／Issue 同步、原版素材未追蹤與 Docker 清理狀態。

## 結果

目標已先以 `0532568` 推送，隨後開工。
規格012已CONFORMED：五列、每列三次實際印字事件；七組正常路徑原版狀態一致。
272幀中55幀至少一列中文，15檢查點；105張圖與獨立背景／字模合成逐像素相同。
首列模式另七組／105張圖回歸及14項離線測試通過；未驗其餘選項的後續遊戲分支。
游標在(128,110)時前三列回退、後兩列維持中文；第三列只被遮到兩個背景像素，
測試初次誤將墨跡完整當成可覆蓋，勘誤見規格012，未放寬產品守門。
隔離引擎提交為 `9dd36726eeaf9c1f3a745aabdcbb84413791d90f`；完整Go測試通過，
累積補丁重建tree為 `8e775d62bc0642da4ecd5adf0d6c0eb3a0245162`，與提交一致。
證據核對入口：[tools/check_menu_evidence.py](../../tools/check_menu_evidence.py)，
從目標 056 的雙次收據逐列核對墨跡、背景、重繪與安全矩形候選，不修改原始收據。
擴展契約：[規格 012](../spec/012-five-menu-lines.md)，未 READY 前不接正式五列模式。

本輪驗收入口：

- [tools/bake_local_font.py](../../tools/bake_local_font.py)：沿用唯一 TSV，逐列產生字模。
- [tools/probe_multi_menu.py](../../tools/probe_multi_menu.py)：五列模式及七個控制組。
- [tools/verify_multi_images.py](../../tools/verify_multi_images.py)：獨立逐列像素驗證。
- [tools/live_menu.go](../../tools/live_menu.go)：仍保留首列模式，五列模式依規格 012 啟用。

本機收據：`workplace/reports/goal057-menu-evidence.json`、`goal057-live-receipt.json`、
`goal057-live-images.json`；清晰畫面為 `goal057-live-zh.menu-clear.png`。
目前無本專案殘留容器；原版及字型衍生物未提交。後續前端實作仍歸Issue #26，不提前關閉。

## 互動前端查核結果（非完成聲明）

- 可沿用 `/home/anr2/cht/psychic-war/cmd/psychicwar/main.go` 的 Ebitengine 視窗生命週期，
  以及該案 `tools/frontend-playthrough.sh` 的 Xvfb／xdotool 驗證方法；不直接執行其掛載腳本。
- 既有 `psychicwar-go-ebiten:latest` 映像可用，SHA-256
  `083e45e6bc0f01ca46ba0774581572c80a607120431b530de72cdd6ffb36f2f7`，
  Go 1.24.13，無 entrypoint，預設 bash；來源為該案 `tools/docker/go-ebiten.Dockerfile`。
  Ebitengine v2.9.9 的既有快取只能唯讀取用或複製到本案，不寫入別案工作區。
- Psychic War 的滑鼠熱區轉按鍵不適用本案。殖民帝國要用目前根公開 API 的
  `DOS.MoveMouse`／`PressMouse`／`ReleaseMouse`；4倍視窗先轉320×200座標，
  不再額外乘DOS滑鼠倍率，負值不可直接轉uint16。
- 本案欠前端包裝，不是平台沒有滑鼠。下一個最小工程步驟為把 `live_menu.go` 的
  觀測／合成從有界測試主迴圈抽離成可重用適配器，再接可撤回 Linux／Xvfb 視窗。
  不直接移植其他分支的 RunCycles、750 cycles/ms、快捷鍵或自動存檔語意。
- 正式前端仍須驗證座標邊界、按下／放開、失焦釋放、退出、鍵盤及同輸入狀態比較；
  本輪沒有視窗交付，也不以五列截圖取代人工操作驗收。

## 重跑入口

沿用目標056的Docker掛載與UID／資源限制，原版、字型及隔離執行器唯讀；
`workplace/reports` 與 `workplace/gocache` 為本機可寫輸出，掛載前確認存在及擁有權。
以下命令均為**容器內**命令，不可直接在主機執行Python：

```sh
# rich2-py:latest；/font 是已驗證存在的 psychic-war/workplace/font-cmp 唯讀目錄。
mkdir -p /out/goal057-fonts
for key in 000001B0 000001CB 000001E4 000001F9 00000204; do
  python3 /repo/tools/bake_local_font.py --game /game --font /font/Cubic_11.ttf \
    --candidate GAME.TXT:0x$key --output /out/goal057-fonts/GAME.TXT-0x$key.json || exit
done

# colonization-research:20260920-r2；/dosgolem 是本案隔離副本。
python3 /repo/tools/check_menu_evidence.py --reports /out --output /out/goal057-menu-evidence.json
python3 /repo/tools/probe_multi_menu.py --dosgolem-commit 9dd36726eeaf9c1f3a745aabdcbb84413791d90f
python3 /repo/tools/probe_live_menu.py --dosgolem-commit 9dd36726eeaf9c1f3a745aabdcbb84413791d90f

# rich2-py:latest
python3 /repo/tools/verify_multi_images.py --out /out
python3 /repo/tools/verify_live_images.py --out /out
```

五列字模、PNG、原始indexed／palette及記憶體均只留本機，不加入Git。
參數補證使用 `probe_menu_lifecycle.py --prefix goal056-params`，第二次加
`--prefix goal056-params-replay --compare goal056-params`；不覆寫既有歷史收據。
