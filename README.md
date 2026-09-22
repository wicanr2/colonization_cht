# 殖民地帝國繁體中文化

《Sid Meier's Colonization》（1994）是以歐洲殖民新世界為題材的歷史策略遊戲：玩家經營殖民地、
處理資源與貿易、與其他勢力互動，並在獨立目標前作出一連串治理選擇。

本專案希望降低玩家面對這些選擇時的語言隔閡，讓繁體中文讀者能理解選單、訊息、狀態與說明，
而不必在遊玩過程中反覆離開遊戲查找翻譯。

## 中文化方式

這不是 remake。原版 DOS 執行檔、遊戲規則、資料與存檔格式維持原樣，由
[dosgolem](https://github.com/wicanr2/dosgolem) 執行。本專案只在原版輸出文字到畫面的階段，
以可追溯的來源鍵辨識**整則訊息**，再於放大後的畫布覆蓋繁體中文。

畫面上有兩種文字來源，兩者都會研究：

- 程式動態輸出的選單、訊息、狀態與說明文字。
- 已烘進按鈕、標籤、告示或其他圖像中的靜態文字。

後者同樣在輸出畫面階段覆蓋，不改寫原版圖檔。版本、雜湊、輸出事件或圖像指紋不符時，
轉譯層必須失敗即關閉（fail-closed），保留原版畫面而不猜測套用。

## 目前狀態

已由 dosgolem 驗證正常 DOS 啟動鏈：`COLONIZE.BAT` 所指定的 `OPENING.EXE -g`
→ `VICEROY.EXE` 主選單 → 滑鼠點選「新世界」→ 難度選擇。
連續冷啟動與安全快照重播的索引畫面、色盤一致；無輸入控制組保留在主選單。

五個主選單選項已由原版執行事件接到[逐幀中文合成](docs/goals/057-menu-coverage-and-interaction.md)，
字型與大小已獲使用者確認；中文開／關的原版狀態對照通過。另有持續增加的來源可驗證
譯稿，但譯稿不等於遊戲畫面已中文化；本輪數量與限制見[目標 058](docs/goals/058-translation-corpus-and-player-window.md)。
另有[24則教學與地圖編輯說明的原文／繁中對照](text/help-bilingual.tsv)，只存於本私有儲存庫，
目前仍是檔案來源可核對的草稿，尚未接到遊戲畫面。
已有以Ebitengine顯示的Linux／Xvfb可撤回視窗原型，能以實際滑鼠由中文主選單進入難度
畫面，並以同輸入對照原版狀態；[畫面接線](docs/goals/059-ebitengine-display-wiring.md)
已由字串改寫改為明確Go介面，尚非正式玩家版本。游標遮擋時逐列保留原文，
其他畫面與完整遊戲未驗證。
下一步擴展已驗證文字及操作範圍，完成[可互動中文切片](https://github.com/wicanr2/colonization_cht/issues/26)。
靜態圖像中文化另依來源與背景證據推進，不再阻擋動態文字路徑。

## 研究與驗證入口

需自備合法 DOS 原版，所有執行均在 Docker 中進行。
專案只使用 `workplace/dosgolem` 獨立副本，不修改共用 dosgolem；上游推送維持停用。

- [目前真相與工具版本](CONTEXT.md)
- [正常啟動與滑鼠驗證命令](docs/goals/053-mouse-and-gameplay-route-replan.md)
- [可重跑路徑驗證器](tools/probe_gameplay_route.py)
- [通用執行器修正補丁](tools/dosgolem-platform-fixes.patch)
- [研究證據](RESEARCH-LOG.md)、[工作歷程](WORKLOG.md)

目前沒有可下載的中文化正式版；術語、完成範圍、字型散布權利與公開發布仍待確認。

## 原版與權利邊界

玩家必須自行持有合法的原版。本儲存庫不會包含或散布原版 EXE、資料檔、圖像、字型、音樂、
磁碟映像、存檔或解包輸出；需要原版的驗證在輸入缺失時會明確跳過。

本專案目前是私有研究儲存庫。任何公開發布、授權、封裝與原文／原版畫面處理，都會在有可驗證
成果後另行確認，不能由這份 README 推定。

## 文件

- [專案規則](AGENTS.md)
- [目前脈絡](CONTEXT.md)
- [工作計畫](WORKLIST.md)（由 `docs/worklist.json` 產生）
- [第一輪目標](docs/goals/001-foundation-and-evidence.md)
- [第二輪目標](docs/goals/002-win16-execution-strategy.md)
- [第三輪目標](docs/goals/003-ne-load-surface-inventory.md)
- [第四輪目標](docs/goals/004-execution-strategy-blocker-audit.md)
- [第五輪目標](docs/goals/005-dos-input-and-cold-boot.md)
- [第六輪目標](docs/goals/006-dos-first-visible-checkpoint.md)
- [第七輪目標](docs/goals/007-colonization-opl-compatibility-spec.md)
- [第八輪目標](docs/goals/008-psound-ready-evidence.md)
- [第九輪目標](docs/goals/009-sbpro-profile-and-cold-boot.md)
- [第十輪目標](docs/goals/010-psound-out-of-range-control-flow.md)
- [第十一輪目標](docs/goals/011-psound-clear-argument-provenance.md)
- [第十二輪目標](docs/goals/012-psound-overlay-writer-lifecycle.md)
- [第十三輪目標](docs/goals/013-mcb-arena-draft-evidence-review.md)
- [第十四輪目標](docs/goals/014-mcb-arena-ready-scope-audit.md)
- [第十五輪目標](docs/goals/015-mcb-multiprocess-ownership-evidence.md)
- [第十六輪目標](docs/goals/016-mcb-process-service-draft-audit.md)
- [第十七輪目標](docs/goals/017-mcb-platform-contract-evidence.md)
- [第十八輪目標](docs/goals/018-mcb-wire-format-and-direct-write-evidence.md)
- [第十九輪目標](docs/goals/019-mcb-generic-importer-ready-review.md)
- [第二十輪目標](docs/goals/020-mcb-registered-process-ready-spec.md)
- [第二十一輪目標](docs/goals/021-mcb-registered-process-implementation.md)
- [第二十二輪目標](docs/goals/022-psound-post-mcb-visible-checkpoint.md)
- [第二十三輪目標](docs/goals/023-first-frame-draw-provenance.md)
- [第二十四輪目標](docs/goals/024-first-screen-normal-input-observation.md)
- [第二十五輪目標](docs/goals/025-opening-static-asset-inventory.md)
- [第二十六輪目標](docs/goals/026-opening-pik-render-provenance.md)
- [第二十七輪目標](docs/goals/027-opening-pik-canvas-geometry.md)
- [第二十八輪目標](docs/goals/028-openingbord-buffer-survival.md)
- [第二十九輪目標](docs/goals/029-openingbord-canvas-survival-to-frame-copy.md)
- [第三十輪目標](docs/goals/030-openingbord-visible-rectangle-and-text-check.md)
- [第三十一輪目標](docs/goals/031-opening-full-frame-static-text-survey.md)
- [第三十二輪目標](docs/goals/032-ocean-label-canvas-writer-provenance.md)
- [第三十三輪目標](docs/goals/033-ocean-label-post-copy-persistence.md)
- [第三十四輪目標](docs/goals/034-opening-post-composite-enter-probe.md)
- [第三十五輪目標](docs/goals/035-opening-exit-code-launcher-chain.md)
- [第三十六輪目標](docs/goals/036-opening-composite-known-click-probe.md)
- [第三十七輪目標](docs/goals/037-opening-mouse-poll-first-divergence.md)
- [第三十八輪目標](docs/goals/038-opening-mouse-boolean-producer.md)
- [第三十九輪目標](docs/goals/039-mouse-producer-body-dataflow.md)
- [第四十輪目標](docs/goals/040-dosgolem-far-call-observation-alignment.md)
- [第四十一輪目標](docs/goals/041-mouse-producer-state-gate-dataflow.md)
- [第四十二輪目標](docs/goals/042-ocean-label-background-safety-geometry.md)
- [第四十三輪目標](docs/goals/043-scroll-text-canvas-writer-provenance.md)
- [第四十四輪目標](docs/goals/044-scroll-candidate-input-asset-provenance.md)
- [第四十五輪目標](docs/goals/045-scroll-candidate-pretext-background-evidence.md)
- [第四十六輪目標](docs/goals/046-opening-click-nonzero-downstream-dataflow.md)
- [第四十七輪目標](docs/goals/047-ocean-label-pretext-canvas-background.md)
- [第四十八輪目標](docs/goals/048-viceroy-direct-entry-stall-diagnostic.md)
- [第四十九輪目標](docs/goals/049-dos-launch-parent-reference-inventory.md)
- [第五十輪目標](docs/goals/050-dos-subdirectory-launch-reference-inventory.md)
- [第五十一輪目標](docs/goals/051-opening-frame-coordinate-grid.md)
- [第五十二輪目標](docs/goals/052-known-exit-input-marker.md)
- [第五十三輪目標：滑鼠事件與中文化路徑重排](docs/goals/053-mouse-and-gameplay-route-replan.md)
- [第五十四輪目標：主選單文字來源](docs/goals/054-main-menu-text-provenance.md)
- [第五十五輪目標：第一則中文顯示原型](docs/goals/055-first-text-prototype.md)
- [第五十六輪目標：主選單即時覆蓋](docs/goals/056-live-menu-overlay.md)
- [第五十七輪目標：五列覆蓋與互動入口查核](docs/goals/057-menu-coverage-and-interaction.md)
- [第五十八輪目標：譯文語料覆蓋與玩家視窗](docs/goals/058-translation-corpus-and-player-window.md)
- [第五十九輪目標：Ebitengine畫面接線](docs/goals/059-ebitengine-display-wiring.md)
- [第六十輪目標：說明訊息雙語語料](docs/goals/060-help-bilingual-corpus.md)
- [第六十一輪目標：下一個正常路徑中文顯示切片](docs/goals/061-next-visible-text-slice.md)
- [難度畫面文字輸出追查草案](docs/spec/014-difficulty-text-output-draft.md)
- [可撤回 Linux 視窗原型規格](docs/spec/013-window-prototype.md)
- [五列主選單覆蓋規格](docs/spec/012-five-menu-lines.md)
- [第一列文字覆蓋規格與未完成範圍](docs/spec/009-first-text-overlay-draft.md)
- [精確指令觀測規格](docs/spec/010-instruction-observer.md)
- [通用畫面補片合成規格](docs/spec/011-output-patch-compositor.md)
- [繁中翻譯草稿](text/draft.zh-Hant.tsv)（候選來源，不是正式執行期識別）
- [Sound Blaster Pro OPL 規格草案](docs/spec/001-colonization-sbpro-opl-profile.md)
- [Sound Blaster Pro OPL READY 規格](docs/spec/002-colonization-sbpro-opl-profile-ready.md)
- [MCB 記憶體 arena 重新協調規格草案](docs/spec/003-colonization-mcb-arena-reconciliation-draft.md)
- [BIOS 馬達倒數修正規格](docs/spec/006-bios-motor-timeout.md)
- [滑鼠事件回呼交換規格](docs/spec/007-mouse-handler-exchange.md)
- [可重播的滑鼠快照規格](docs/spec/008-mouse-snapshot.md)
- [已註冊多行程 MCB importer READY 規格](docs/spec/004-colonization-registered-process-mcb-importer-ready.md)
- [已註冊多行程 MCB importer CONFORMED 規格](docs/spec/005-colonization-registered-process-mcb-importer-conformed.md)
- [工作歷程](WORKLOG.md)
