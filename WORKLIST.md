# 工作計畫

<!-- 由 tools/worklist.py render 從 docs/worklist.json 產生；請勿手動修改。 -->

所有未完成工作以 GitHub Issue 為執行入口；本檔只呈現其機器可讀索引。
尚未自動驗證的條目一律標為人工驗證（manual），代表它們仍未完成；已完成條目必須有可重跑的訊號。

| Issue | 狀態 | 工作項目 | 依賴 | 驗收摘要 |
|---:|---|---|---|---|
| #1 | completed | [建立原始輸入指紋與權利邊界清冊](https://github.com/wicanr2/colonization_cht/issues/1) | — | 可重跑的雜湊與權利清冊，且 Git 未追蹤原版素材。 |
| #2 | completed | [建立可重現的隔離研究工具鏈](https://github.com/wicanr2/colonization_cht/issues/2) | — | Docker 入口可重跑、輸入唯讀、沒有 root-owned 產物或殘留容器。 |
| #3 | completed | [探測 dosgolem 對目標版本的冷啟動能力](https://github.com/wicanr2/colonization_cht/issues/3) | `input-inventory`, `research-toolchain` | 特定雜湊有可重跑的服務缺口報告。 |
| #4 | completed | [建立原版冷啟動至主選單的基線收據](https://github.com/wicanr2/colonization_cht/issues/4) | `dosgolem-probe` | dosgolem 可重生含輸入、快照與索引畫面的基線，或有可重現 blocker。 |
| #5 | blocked | [追溯動態文字輸出常式與文字來源](https://github.com/wicanr2/colonization_cht/issues/5) | `dos-input-cold-boot-probe`, `dos-first-visible-checkpoint` | 每條輸出路徑有原始定位、證據等級與重播 trace。 |
| #6 | planned | [制定動態文字抽取與訊息鍵 DRAFT 規格](https://github.com/wicanr2/colonization_cht/issues/6) | `dynamic-print-re` | DRAFT 規格定義來源鍵、回退和幾何資料模型。 |
| #7 | planned | [建立動態文本清冊與覆蓋率量測](https://github.com/wicanr2/colonization_cht/issues/7) | `dynamic-text-draft` | 可重跑報表列出抽取、翻譯與未知鍵數。 |
| #8 | blocked | [普查靜態內嵌文字與覆蓋候選](https://github.com/wicanr2/colonization_cht/issues/8) | `dos-first-visible-checkpoint` | 靜態文字清冊可重現候選定位與證據等級。 |
| #9 | planned | [制定靜態文字覆蓋 DRAFT 規格與最小原型](https://github.com/wicanr2/colonization_cht/issues/9) | `static-text-survey` | 一個可丟棄原型具命中與反向條件對照。 |
| #10 | blocked | [確認中文字型、術語政策與中文化完成範圍](https://github.com/wicanr2/colonization_cht/issues/10) | `dynamic-coverage`, `static-overlay-draft` | 使用者確認字型、術語與完成門檻並回填 CONTEXT／READY 規格。 |
| #11 | planned | [將動態文字覆蓋設計升為 READY 規格](https://github.com/wicanr2/colonization_cht/issues/11) | `dynamic-text-draft`, `dynamic-coverage`, `l10n-decision` | 所有正式輸出類別有可回查 evidence 與 READY 規格。 |
| #12 | planned | [實作並驗證動態文字中文疊加](https://github.com/wicanr2/colonization_cht/issues/12) | `dynamic-overlay-ready` | 中文、英文、缺譯和最長譯文都有固定快照與玩家路徑驗證。 |
| #13 | planned | [實作並驗證靜態文字圖像中文覆蓋](https://github.com/wicanr2/colonization_cht/issues/13) | `static-overlay-draft`, `l10n-decision` | 每個項目有圖像指紋、反向條件與玩家路徑收據。 |
| #14 | planned | [建立中文化驗證矩陣與正常玩家路徑收據](https://github.com/wicanr2/colonization_cht/issues/14) | `dynamic-overlay-implementation`, `static-overlay-implementation` | 動態與靜態路徑都有原版、中文、英文與反向條件收據。 |
| #15 | blocked | [定義封裝、授權與發布界線](https://github.com/wicanr2/colonization_cht/issues/15) | `verification-matrix` | 使用者確認授權與發布方式，且可散布包不含原版素材。 |
| #16 | completed | [建立機器可讀工作清單與驗證入口](https://github.com/wicanr2/colonization_cht/issues/16) | — | JSON、render 與 verify 可在 Docker 內重跑，且每筆都連到 Issue。 |
| #17 | completed | [建立專案 README 與第一輪目標文件](https://github.com/wicanr2/colonization_cht/issues/17) | — | README 與目標 001 說明範圍、邊界、Issue 與可驗證退出條件。 |
| #18 | completed | [確認目標版本執行策略](https://github.com/wicanr2/colonization_cht/issues/18) | `boot-baseline` | 使用者確認 DOS 輸入策略，並回填 CONTEXT、目標與受影響工作依賴。 |
| #19 | completed | [盤點固定 Windows 3.x NE 版本的載入、匯入與資源證據](https://github.com/wicanr2/colonization_cht/issues/19) | `input-inventory`, `research-toolchain` | 固定雜湊的 NE header、區段、匯入與資源有 Docker 可重跑清冊、交叉格式核對與未知界線。 |
| #20 | completed | [盤點使用者提供的 DOS 版並建立 dosgolem 冷啟動收據](https://github.com/wicanr2/colonization_cht/issues/20) | `input-inventory`, `research-toolchain`, `win16-execution-decision` | DOS 輸入 manifest、固定啟動入口、Docker probe 收據與下一個可見檢查點都可回查。 |
| #21 | blocked | [建立 DOS OPENING.EXE 的第一個可見畫面或轉交收據](https://github.com/wicanr2/colonization_cht/issues/21) | `dos-input-cold-boot-probe` | 正式 OPENING.EXE 冷啟動有可重播的非零畫面、可觀測文字輸出、經確認的 VICEROY.EXE 轉交，或最小具體 blocker。 |

## 驗證

```text
tools/worklist.py verify
```
