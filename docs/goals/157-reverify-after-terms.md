# 目標157：改稿後正式欄位重烘與重驗（Issue #27）

狀態：完成（重烘與綁定）；視覺重驗依使用者決定延到 [Issue #38](https://github.com/wicanr2/colonization_cht/issues/38)。開始與完成：2026-09-26。接續[目標156](156-apply-terms.md)。

## 範圍

- 以現行 TSV 重烘全部正式欄位的字模、圖集與遮罩。
- 譯文沒變的欄位：新舊字模逐欄比對 alpha、位置與色號相同，既有收據仍有效。
- 譯文有變的欄位（第一張旗卡、@BUILD4／@BUILD7 字幕變數、海上欄、四國介紹八頁、@TUTORIAL1、遊戲選項 0x4E9 列）：量測新譯文寬度、重跑真 GUI、中英同輸入重播與檢查器。
- 更新全面回歸基準與驗證矩陣。

## 退出條件

- 全部旗標載入時沒有 `font-binding-mismatch`。
- 受影響各列檢查器 PASS；驗證矩陣全數 PASS。

## 結果

- 補漏：術語檢查的複數規則沒涵蓋 colony／colonies，補上後多出 21 列（多為「殖民地」→「殖民領地」），以第八批改稿處理；「殖民地時期」指時代，維持原文。術語檢查最終剩 33 列，全部有不換理由。
- 重烘：`tools/rebake_goal157.sh` 以現行 TSV 重烘遊戲選項九欄、首張字幕、退休框、其餘九張字幕、第一張旗卡、四國介紹、@TUTORIAL1 與海上圖集。新舊字模逐欄比對：譯文沒變的欄位 alpha、尺寸、位置完全相同；有變的是選項列 0x4E9、@BUILD4／@BUILD7／@BUILD8、@TUTORIAL1、介紹七頁（@NATION3B 未變）、第一張旗卡上欄與海上圖集。
- 版面：
  - 選項列 0x4E9「(I) 顯示印地安人行動」25px 墨跡 256×25，仍在 672×36 安全矩形內（規格031 已更新）。
  - 第一張旗卡上欄「英國：」21px 69×19，左上 `(590,60)`，維持兩欄共同中心 x=624（規格021 已更新）。
  - @BUILD7「並建立殖民領地，使英國更加榮耀。」638×35，仍是單行。
- 閘門更新：`tools/validate_nation_card_fragments.py`、`tools/validate_nation_introduction_corpus.py` 的英格蘭譯名改為「英國」；`tools/bake_local_font.py` 與前端 `optionRowInk` 的 0x4E9 墨跡改為 256×25；前端第一張旗卡位置與墨跡同步。
- 前端 `tools/live_menu.go` SHA-256 `0babd2974ec63e837dfb7f604b86a5b530a4db30e24b0a5b2559788a638e1ace`。全部旗標載入 1M 步：沒有 `font-binding-mismatch` 或超界（收據在 `workplace/reports/goal157-reverify/bind/`）。舊字模備份在 `workplace/reports/goal157-reverify/old-fonts/`。

## 未做（依使用者決定）

譯文變動欄位的真 GUI、中英同輸入重播與檢查器，以及新的全面回歸基準，延到 #27 語料定稿後在 [Issue #38](https://github.com/wicanr2/colonization_cht/issues/38) 一次做。驗證矩陣相關列標為「待重驗」。
