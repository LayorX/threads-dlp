# Gemini - Threads 影片分析與下載工具

本文件由 Gemini 技術架構師 (Mentor) 負責維護，旨在記錄專案的規劃、狀態、待辦事項與技術決策。

## 專案狀態

*   **階段：** Phase 3 - 架構強化與功能偵錯
*   **目前進度：** **日誌輸出已大幅優化，上傳器憑證管理更安全靈活。** 我們已完成對核心功能的錯誤處理強化，並基於真實的瀏覽器請求重構了按讚模組。然而，在實測中發現按讚 API 呼叫失敗。為解決此問題，已建立一個獨立的測試腳本 `like_tester.py` 用於精準偵錯。
*   **交接點：** 專案暫停於執行 `like_tester.py` 之前。

## 專案概要 (Spec)

打造一個能透過登入使用者帳號，自動蒐集、分析並下載指定 Threads 用戶頁面影片的工具。此工具旨在為內容創作者提供素材與靈感。

### 核心模組規劃

1.  **`scraper.py` (核心模組):**
    *   **認證:** 使用 `selenium-wire` 啟動背景瀏覽器，並透過注入使用者提供的 `sessionid` Cookie 來安全地完成登入認證。
    *   **抓取:** 透過模擬真人滾動頁面，觸發網站載入影片。`selenium-wire` 會攔截所有瀏覽器網路請求。
    *   **分析:** 程式會遍歷所有網路請求，並檢查其回應的 `Content-Type` 標頭。任何類型為 `video/*` 的資源都會被識別為目標影片，並提取其 URL。

2.  **`downloader.py` (下載模組):**
    *   接收 `scraper.py` 提供的影片 URL 列表。
    *   透過 `uv run` 呼叫 `yt-dlp` 引擎，高效、可靠地完成下載任務，並將影片儲存至指定資料夾。

3.  **`main.py` (命令列介面):**
    *   作為專案的統一入口，使用 `argparse` 提供友善的命令列操作介面。
    *   使用者可以指定目標用戶、滾動次數、輸出資料夾等參數。

## 問題解決日誌 (Troubleshooting Log)

這段開發歷程充滿挑戰，我們透過一系列的偵錯與決策，最終抵達成功。這份日誌記錄了我們的思考路徑。

1.  **方案 A: API 方案**
    *   **問題:** 使用者無法申請到官方 Threads API 金鑰。
    *   **決策:** 放棄 API 方案，轉向爬蟲方案。

2.  **方案 B: `yt-dlp` 直接爬取**
    *   **嘗試:** `yt-dlp` 是最強大的通用下載工具，我們首先嘗試用它直接解析 Threads 頁面。
    *   **結果:** 失敗。`yt-dlp` 返回 `Unsupported URL` 錯誤。

3.  **方案 C: Selenium + HTML 解析**
    *   **嘗試:** 使用 `Selenium` 模擬瀏覽器打開頁面，並從 HTML 原始碼中尋找 `<video>` 標籤。
    *   **結果:** 失敗。Threads 網站沒有使用簡單的 `<video>` 標籤。

4.  **方案 D: Selenium + 網路請求分析 (`.mp4` 過濾)
    *   **嘗試:** 使用 `selenium-wire` 攔截網路請求，並過濾出 URL 結尾是 `.mp4` 的請求。
    *   **結果:** 失敗。匿名訪問時，網站沒有載入任何 `.mp4` 檔案。
    *   **推論:** 必須登入才能看到真正的影片數據。

5.  **方案 E: 登入方案的演進**
    *   **子方案 E1 (帳號密碼):** 最初計畫模擬表單登入，但為了使用者安全，我作為 AI **絕不處理**明文密碼，因此否決了此方案。
    *   **子方案 E2 (Cookie 注入):** 使用者提出了更專業的 Cookie 方案，我們一拍即合。這既安全又可靠。

6.  **依賴地獄 (Dependency Hell) 的挑戰**
    *   在實作 Cookie 方案時，我們遭遇了 `selenium-wire` 的一系列依賴問題。
    *   **`blinker._saferef` 找不到:** 透過在 `pyproject.toml` 中強制鎖定 `blinker==1.7.0` 解決了此問題。
    *   **`pkg_resources` 找不到:** 接著發現缺少 `setuptools` 套件。透過 `uv add setuptools` 將其加入專案依賴，解決了問題。

7.  **情報分析的曲折**
    *   **目標確認:** 我們確認了所有貼文數據都來自 `graphql/query` 這個 API 端點，並以 `zstd` 格式壓縮。
    *   **列印失敗:** 在嘗試印出 JSON 結構時，因 Windows 命令列的 `cp950` 編碼無法處理 emoji 等特殊字元而失敗。
    *   **存檔成功:** 最終我們採用「儲存到檔案」的策略，成功將完整的 JSON 數據寫入 `debug_json_output.json`，獲得了用來開發解析器的精確「地圖」。

8.  **最後一哩路：迴歸 Bug 與檔名淨化**
    *   **迴歸 Bug:** 在實作了完整的資料庫和元數據解析 logique 後，使用者回報程式又無法抓取到影片了。經查，這是一個嚴重的邏輯迴歸：程式只分析了「最大」的一個數據包，而忽略了滾動後載入的其他數據包。
    *   **迴歸修正:** 我們重寫了 `scraper.py` 的核心迴圈，使其能夠正確處理所有捕獲到的數據包，修正了這個問題。
    *   **檔名 Bug:** 在使用者最終實測中，又發現因貼文標題包含換行符、emoji 等特殊字元而導致的 `[Errno 22] Invalid argument` 下載失敗問題。
    *   **最終修正:** 我們在 `main.py` 中加入了一個更強健的 `sanitize_filename` 函式，徹底解決了檔名問題，讓整個流程達到生產級別的穩定性。

9.  **Gemini API 空請求錯誤**
    *   **問題:** 在影片上傳階段，如果一個影片在 Threads 上沒有任何文字描述（或其檔名在處理後也變為空字串），`uploader.py` 會向 Gemini API 發送一個空請求，導致 API 回傳一般文字而非預期的 JSON，進而引發 `JSON 解碼失敗` 錯誤並中斷程式。
    *   **修正:** 我們為 `uploader.py` 中的 `generate_metadata` 函式實作了「雙重保險」機制。第一步，如果原始描述為空，則嘗試使用影片檔名作為備用描述。第二步，會再次檢查描述是否依然為空（以應對檔名處理後變空字串的極端情況），若仍為空，則強制使用一個通用的預設描述（如「一部有趣的影片」）。此策略 100% 確保了 API 請求永不為空，徹底根除了此問題。

10. **按讚功能 `Fetch` 失敗**
    *   **問題:** 在根據使用者提供的 `fetch` 請求，完美重構 `threads_client.py` 以模擬真實 API 呼叫後，實測時遭遇 `TypeError: Failed to fetch` 錯誤。此錯誤表明，儘管請求的參數和標頭都已盡力模擬，但在瀏覽器環境中執行時，仍被某種機制（可能是 CORS、CSP 安全策略或其他頁面腳本的限制）所阻止。
    *   **對策:** 為了隔離變數、專注排錯，我們決定創建一個獨立的、輕量級的測試腳本 `like_tester.py`。此腳本的唯一目的就是針對單一 URL 執行按讚操作，讓我們可以快速、重複地測試並診斷 `fetch` 失敗的根本原因。
    *   **最新進展:** 我們在 `like_tester.py` 中加入了 `driver.get_log('browser')` 來捕獲瀏覽器控制台日誌，並在執行後將日誌寫入 `browser_console.log`。這讓我們能非同步地檢查 `fetch` 呼叫的詳細錯誤，這是解決此問題的關鍵一步。

11. **Docker Build 失敗 (`apt-key` 錯誤)**
    *   **問題:** 在建置 Docker 映像時，出現 `apt-key: not found` 錯誤，導致安裝 Google Chrome 失敗。這是因為 `apt-key` 在較新的 Debian/Ubuntu 版本中已被棄用。
    *   **修正:** 我們更新了 `Dockerfile`，改用 Google 官方推薦的現代化方法。新的指令會將 Chrome 的簽署金鑰直接新增到受信任的目錄中，並在軟體源列表中明確指定金鑰路徑 (`signed-by`)，從而繞過 `apt-key`，確保了建置過程的穩定與安全。

12. **排程器 `ImportError`**
    *   **問題:** 部署後，`scheduler.py` 因 `ImportError: cannot import name 'get_videos_to_upload_count'` 而崩潰。經查，這是因為 `database.py` 中的函式已重構，原函式被 `get_all_videos_to_upload` 取代。
    *   **修正:** 我們修改了 `scheduler.py`，將 `import` 的函式名稱更正為 `get_all_videos_to_upload`，並調整了相關邏輯，改為使用 `len()` 來獲取待上傳影片的數量，從而解決了啟動錯誤。

## 交接手冊與 Todolist

### Phase 1: 核心功能開發 (已全部完成)

- [x] **環境建置:** 初始化 Git 與 Python 虛擬環境 (`uv venv`)。
- [x] **安全設定:** 建立 `.gitignore` 並加入 `.env`，確保憑證安全。
- [x] **安裝依賴:** 使用 `uv add` 與 `uv sync` 成功安裝並鎖定所有必要套件。
- [x] **實作 (爬蟲):** 編寫 `scraper.py`，實現基於 Cookie 認證與 API JSON 解析的完整影片元數據抓取邏輯。
- [x] **實作 (下載):** 編寫 `downloader.py`，並由 `main.py` 負責生成安全的檔名。
- [x] **整合 (CLI):** 重構 `main.py`，建立支援三種模式（用戶、搜尋、首頁）的命令列介面。
- [x] **資料庫:** 建立 `database.py` 模組，並在主流程中整合資料庫初始化、查詢去重、新增紀錄等功能。
- [x] **完整測試:** 完成端到端測試，確認整個專案穩定、可靠。

### Phase 2: YouTube 上傳器整合 (已全部完成)

- [x] **分支管理:** 為上傳器功能建立獨立分支 `feature/youtube-uploader`。
- [x] **資料庫升級:** 為 `videos` 資料表增加 `uploaded_to_youtube` 狀態欄位。
- [x] **架構重構:** 將 `uploader.py` 的資料庫存取模式從「一次性獲取」重構為「一次一筆」，徹底解決 `database is locked` 問題。
- [x] **程式碼整合:** 建立 `uploader.py`，並將使用者既有的上傳邏輯（呼叫外部 .exe、使用 Gemini API）整合進來。
- [x] **依賴管理:** 新增 `google-generativeai` 依賴，並建立 `config.json.template` 範本以保護 API 金鑰。
- [x] **安全強化:** 在 `.gitignore` 中加入對 `config.json`, `request.token`, `client_secrets.json` 等敏感檔案的忽略規則。
- [x] **功能橋接:** 在 `main.py` 中新增 `--upload` 旗標，實現下載後自動上傳的流程。
- [x] **問題修復:** 解決了 Gemini 模型名稱的相容性問題，以及 Windows 環境下的日誌編碼問題。
- [x] **偵錯功能:** 在 `scraper.py` 中新增了將原始 GraphQL 數據儲存到 `last_run_graphql_output.json` 的功能。
- [x] **畫龍點睛:** 實作讀取 `config.json` 的高級排程邏輯，支援立即發布、預約發布與時間間隔。
- [x] **安全加固:** 完善 `.gitignore`，並為 `client_secrets.json` 建立範本，確保敏感資訊絕不外洩。

### Phase 3: 擴充與優化 (進行中)

- [x] **錯誤處理強化:**
    - [x] 為 `scraper.py` 增加了啟動時的 Cookie 有效性驗證。
    - [x] 為 `scraper.py` 增加了處理空 API 回應的日誌警告。
    - [x] 為 `downloader.py` 增加了最多 3 次的下載失敗重試機制。

- [x] **日誌輸出優化:**
    - [x] 調整 `main.py` 和 `scheduler.py` 的日誌配置，將預設日誌等級設定為 `WARNING`，並明確抑制 `seleniumwire` 和 `webdriver_manager` 的 `INFO` 訊息，大幅減少了不必要的日誌輸出，提升了日誌清晰度。

- [x] **上傳器憑證管理:**
    - [x] 在 `uploader.py` 中新增 `ensure_token_file_exists` 函式，用於檢查 `request.token` 檔案。若檔案不存在，則嘗試從 `YT_REQUEST` 環境變數讀取內容並創建該檔案。
    - [x] 將此檢查整合到 `run_upload_task` 的開頭，確保憑證在執行上傳前準備就緒，增強了部署的靈活性和安全性。

- [ ] **修正按讚功能 (日誌分析中):**
    - [x] **重構:** 根據真實 `fetch` 請求重構了 `threads_client.py`。
    *   **問題:** 遭遇 `TypeError: Failed to fetch`，疑似被瀏覽器安全策略阻止。
    *   **對策:** 建立 `like_tester.py` 進行隔離偵錯。
    *   **進展:** 成功修改 `like_tester.py`，在測試結束後自動將瀏覽器控制台日誌儲存到 `browser_console.log` 檔案中。
    *   [!] **交接點:** 我們已經準備好執行 `like_tester.py` 來捕獲最關鍵的錯誤訊息。
    *   [ ] **下一步 (交接任務):** 當你回來時，我們將執行 `uv run python like_tester.py --url "你提供的URL"`，然後**仔細分析新產生的 `browser_console.log` 檔案**，從中找出 `fetch` 失敗的根本原因。

- [ ] **增加多執行緒:** 研究為下載過程加入多執行緒，以加速大量影片的下載。
- [ ] **AI 增強:** 評估 `Whisper` (語音轉文字), `OpenCV` (影片處理) 等 AI 相關函式庫，為未來增加 AI 功能做準備。