# 規格043：macOS universal ZIP

狀態：CONFORMED（限建置、簽章資料、封包與 shell 接線）；日期：2026-10-04。對應 [Issue #52](https://github.com/wicanr2/colonization_cht/issues/52)，入口為[目標182](../goals/182-platform-build-preflight.md)。

## 範圍與證據

沿用已授權的 macOS Intel 與 Apple Silicon 交付。ZIP 保留既有終端機 `--game` 工作流程，包含同一中文前端、譯稿、字模、授權及清單。原版目錄只讀，包內不含原版素材。測試識別碼只在 workplace 使用，不決定正式發行版號。

現行來源為 `workplace/reports/goal181-colony-rest/20261004-woodcut-titles/formal-modal2/stable-build`。工具沿既有 `eob-remake-macos:1.26.7-ebiten2.9.9-audio`，映像 SHA-256 `83f12672f4ac06bed37683a9e9eba49980302ba84be11c8042a4dbf4f571761f`，Go1.26.7、ld64-711、SDK15.5。證據與候選置於 `workplace/reports/goal182-platform-preflight/20261004-macos-zip/`，不可覆寫既有收據。

已證實：前版 x86_64 沒有 LC_CODE_SIGNATURE；arm64 有單一 CodeDirectory、SHA-256、4096-byte 頁及 adhoc／linker-signed 標記。這是檔案結構觀察，尚未逐頁核對，也不證明 macOS 接受執行。

簽章格式參照 [Go codesign 原始碼](https://go.dev/src/cmd/internal/codesign/codesign.go)；實際版本來源以映像內 `/usr/local/go/src/cmd/internal/codesign/codesign.go` 的雜湊為準。只使用既有連結器建立臨時簽章，不加入 Developer ID、Apple 公證或憑證需求。

## 候選契約

- 兩個獨立 Mach-O 切片由同一唯讀來源建置。lipo 只組合兩側原始位元組。
- 包裝前逐側檢查 GOOS／GOARCH、Go 版本、依賴版本、系統函式庫、CodeDirectory 與所有簽署頁。缺簽章、壞頁、未知切片或兩側依賴不同時拒絕。
- macOS 啟動器沿唯一 Linux 啟動旗標，預設存檔置於 `$HOME/Library/Application Support/colonization-cht/save`，可由 `COLONIZATION_CHT_SAVE` 指定。額外參數及含中文／空白的路徑須完整保留。
- ZIP 依檔名排序、固定 1980-01-01 時戳、Unix 一般檔案模式。兩次乾淨封裝須逐位元組相同；獨立解包核對清單、授權、全部譯稿與字模，並排除原版素材。
- 沒有 Mac 真機時，只驗建置、簽章資料與包結構。Linux 上的啟動器參數記錄替身只驗 shell 接線，不算 macOS 啟動、音訊、鍵鼠或存讀檔驗收。

## READY 證據審查

既有 ld64-711 的 `-adhoc_codesign` 選項由[固定版本原始碼](https://raw.githubusercontent.com/apple-oss-distributions/ld64/ld64-711/src/ld/Options.cpp)確認。Go1.26.7 在 Intel 合併 DWARF 後不重簽，候選 signed-a 的 CodeDirectory 涵蓋範圍因此失效；失敗產物與 stderr 保留。採 `go build -mod=readonly -trimpath -ldflags="-w -extldflags=-Wl,-adhoc_codesign"`，只省略除錯資料，不改前端來源或原版資料。

signed-c／d 的兩個切片與通用檔分別逐位元組相同。通用檔 SHA-256 `1c17376afc9e55013a0528a65f30bd4ebf6a26d535cbfe73dd2a7215c2f748ef`。逐側 CodeDirectory、每頁 SHA-256、切片對齊、系統依賴及 Go 依賴均通過；破壞任一側已簽署頁會拒絕。這只證明簽章資料自洽，不證明 macOS 接受執行。

candidate-c／d ZIP 各14177251bytes，SHA-256 `b6a1b5fc9d40098a02808f23b185dec92301adff711b7619da1b265273804d1f`。獨立解包94檔、完整清單、13份譯稿、字模、全部授權與原版排除通過。candidate-check.json 為 PASS_MACOS_CANDIDATE_STRUCTURE_AND_SHELL，SHA-256 `6e5995d8dc627feed593974ee06f7e0ecefd04a1f65b86f651953dedf739d757`。GNU Bash3.2.57與5.2各驗空／有額外參數及預設／指定存檔路徑參數；空字串、中文、空白、驚嘆號與 & 均保留，退出碼沿用。mkdir 為記錄替身，只驗請求，不冒稱存檔成功。

本規格授權[macOS 組裝器](../../tools/macos_bundle.py)、[共用封裝器](../../tools/package_release.py)的 `--format macos-zip`、[macOS 操作說明](../../tools/release/README.macos.txt)，以及[跨平台建置入口](../../tools/build_goal182_platforms.sh)的上述 macOS 連結旗標。封裝映像沿既有 `colonization-verification:20260930-r1`，Go1.26.7、Python3.11；交叉編譯仍用本頁 macOS 映像。正式入口重建、解包與拒絕守門另驗後才可限定 CONFORMED。

## 限定 CONFORMED 收據

正式建置入口產生的通用檔與 signed-c／d 相同。正式封裝器 formal-a／b ZIP 與候選全等，各14177251bytes，指紋仍為上述 b6a1b5fc…。SHA256SUMS、獨立解包94檔及完整 MANIFEST 通過；formal-check.json 為 PASS_FORMAL_MACOS_REBUILD_AND_EXTRACTION，SHA-256 `71b1b4f0ee6c9f9c3065d54c9f65b79fe4676b48394371b9cf0f0cb8583d0750`。位元組相同，沿用候選 Bash3.2／5.2 接線證據，不冒稱已執行 Mac 程式。

兩側壞簽署頁、Windows 錯平台、舊 Intel 未簽章、舊失效簽章、macOS 誤用 Windows／Linux 格式、非法版號與覆寫既有版本均拒絕。refusals.json 為 PASS_MACOS_PACKAGING_REFUSALS，SHA-256 `cf60dff6a27f878d48240b1fa763c6a10feee1bcb715fb3edb742d35ead09182`。共用封裝器的 Windows ZIP 回歸仍13973331bytes，指紋 `2fa9630f26f195257170bcc86c78b6f60a5e4a743740e448f4719939e9cfe100`，與前批逐位元組相同。

驗收不包含 macOS 執行、真機、Gatekeeper、音訊、鍵鼠或存讀檔。未建立正式版號、dist-all 交付或 Release；#52 維持進行中。重跑入口與所有本機收據由目標182索引。
