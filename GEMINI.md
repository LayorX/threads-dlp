# Gemini - Threads 影片分析與下載工具

本文件由 Gemini 技術架構師 (Mentor) 負責維護，旨在記錄專案的規劃、狀態、待辦事項與技術決策。

## 專案狀態

*   **階段：** Phase 4 - 雲端部署與自動化
*   **目前進度：** **專案已進入雲端部署階段，正專注於 Zeabur 平台的適配與多進程服務管理。** 先前的本地功能開發與偵錯已全部完成。目前，我們正透過 `honcho` 與 `Dockerfile` 的組合，實現爬蟲、排程器與 `datasette` 網頁介面在雲端環境的並行運作。
*   **交接點：** 專案工作在 `feature/zeabur-deployment` 分支上進行，目標是完成在 Zeabur 平台上的首次成功部署。

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

13. **Datasette 競爭條件 (Race Condition)**
    *   **問題:** 在使用 `Procfile` 啟動多個進程時，`datasette` 服務有時會因為資料庫檔案 `threads.db` 尚未被主程式創建而啟動失敗。
    *   **修正:** 我們在 `Procfile` 中為 `datasette` 的啟動指令加上了 `--create` 旗標。此旗標確保如果資料庫檔案不存在，`datasette` 會自動創建一個空的資料庫檔案，從而解決了這個競爭條件問題，提高了服務啟動的穩定性。

14. **Docker 執行階段錯誤 (`honcho: not found`)**
    *   **問題:** 在 Zeabur 平台部署時，容器啟動失敗，日誌顯示 `exec: "honcho": executable file not found in $PATH`。
    *   **分析:** 這個問題源於我們使用的 Docker 多階段建置 (`multi-stage build`)。在 `builder` 階段，`honcho` 作為 Python 依賴被正確安裝，但它的可執行檔位於 `/usr/local/bin/`。在 `runtime` 階段，我們只從 `builder` 複製了 Python 的函式庫 (`site-packages`)，卻遺漏了包含 `honcho` 在內的可執行檔。
    *   **修正:** 我們修改了 `Dockerfile`，將 `COPY --from=builder /usr/local/bin/uv /usr/local/bin/uv` 指令變更為 `COPY --from=builder /usr/local/bin/ /usr/local/bin/`。這個改動確保了 `builder` 階段安裝的所有指令（`uv`, `honcho`, `datasette` 等）都被完整地複製到最終的運行環境中，從而根除了此問題。

15. **執行階段錯誤 (平台不相容)**
    *   **問題:** 在 Linux 容器中執行上傳腳本時，出現 `[Errno 13] Permission denied: './youtubeuploader.exe'` 錯誤。
    *   **分析:** 應用程式最初在 Windows 環境開發，因此依賴了 Windows 的可執行檔 `youtubeuploader.exe`。該檔案與 Docker 容器的 Linux 環境完全不相容，導致作業系統拒絕執行。
    *   **修正:** 我們採用了務實的「二進位檔案替換」方案。修改 `Dockerfile`，在建置階段從 `youtubeuploader` 的官方 GitHub Release 頁面下載其 Linux (amd64) 版本。同時，修改 `uploader.py`，將預設呼叫的執行檔名稱從 `youtubeuploader.exe` 改為 `youtubeuploader`，使其能正確地在系統 `PATH` 中找到並執行新的 Linux 版本。此方法在最小化程式碼變動的前提下，解決了跨平台部署的關鍵障礙。

16. **雲端部署的資料持久化**
    *   **問題:** 雲端平台 (如 Zeabur) 的檔案系統通常是暫時性的，每次重新部署或重啟服務時，所有未被永久儲存的檔案（如下載的影片和 SQLite 資料庫）都會遺失。
    *   **分析:** 為了確保資料的持久性並降低因暫存檔案系統可能產生的記憶體費用，必須將資料庫和下載目錄與平台的永久性磁碟區 (Volume) 連結。
    *   **修正:** 我們執行了以下架構調整：
        1.  建立了一個新的 `db/` 資料夾來專門存放資料庫檔案。
        2.  修改了 `modules/database.py`, `view_db.py` 和 `Procfile`，將所有對 `threads_dlp.db` 的引用路徑更新為 `db/threads_dlp.db`。
        3.  更新了 `.gitignore` 以正確忽略 `db/` 資料夾內的資料庫檔案，同時確保該資料夾能被 Git 追蹤。
        4.  更新了 `README.md` 和 `README.en.md`，新增了在 Zeabur 上設定磁碟區掛載 (`/home/appuser/db` 和 `/home/appuser/downloads`) 的詳細教學，指導使用者完成此關鍵步驟。

17. **自動化磁碟空間管理**
    *   **問題:** 隨著專案長時間自動運行，`downloads` 資料夾會持續累積影片，最終可能導致磁碟空間耗盡或產生不必要的儲存費用。
    *   **分析:** 需要一個自動化機制，在每次上傳任務執行前，檢查目前的磁碟使用量。如果超過預設閾值，應自動刪除那些已經成功上傳到 YouTube 的影片檔案，以回收空間。
    *   **修正:** 我們為 `uploader.py` 增加了完整的磁碟管理功能：
        1.  **參數化:** 新增了 `-du` / `--deleteupload` 命令列參數，允許使用者自訂清理的磁碟空間閾值（單位為 GB），預設為 0.8 GB。
        2.  **空間檢查:** 在每次執行上傳前，程式會先計算 `downloads` 資料夾的總大小。
        3.  **資料庫查詢:** 在 `database.py` 中新增 `get_all_uploaded_videos` 函式，專門用來獲取所有已上傳影片的本地檔案路徑。
        4.  **自動刪除:** 如果資料夾大小超過閾值，程式會根據從資料庫獲取的路徑列表，自動刪除對應的影片檔案 (`.mp4`) 及其元數據檔案 (`.json`)。
        5.  **排程調整:** 同時，我們將 `scheduler.py` 中的下載任務排程從每 1 小時調整為每 4 小時，以降低檔案累積的速度。

## 交接手冊與 Todolist

### 待辦事項 (Issues)

- [ ] **修復 `-t` (指定用戶) 功能**
    - **問題描述:** 目前使用 `-t <username>` 參數時，程式雖然能正常導航至目標用戶的頁面 (例如 `https://www.threads.net/@zuck`)，但在後續攔截到的 GraphQL API 請求中，似乎無法正確地只包含該用戶的貼文數據，導致抓取到的內容與預期不符（可能抓取到的是首頁推薦內容，或是空的）。
    - **初步 Issue 分析:**
        1.  **前端路由變更:** Threads 網站可能改變了其前端的路由或頁面載入機制。即使 URL 看起來正確，但觸發載入用戶數據的內部 API 呼叫可能需要特定的操作（例如，額外的點擊或特定的 `state`）。
        2.  **GraphQL API 查詢變更:** Threads 的 GraphQL API 可能不再僅僅依賴頁面 URL 來決定要回傳哪個用戶的數據。它現在可能需要一個明確的 `userID` 作為查詢參數。我們需要分析在瀏覽器中手動導航至用戶頁面時，是哪個 `graphql/query` 請求包含了 `userID`，以及這個 `userID` 是如何從用戶名稱轉換而來的。

### Phase 1: 核心功能開發 (已全部完成)
- [x] **資料庫路徑重構:** 為了適應雲端部署的永久性磁碟掛載，建立了 `db` 資料夾，並將所有資料庫檔案的路徑參考都更新至此，同時更新了說明文件。
- [x] **自動化磁碟管理:** 為 `uploader.py` 新增了磁碟空間監控與自動清理功能，可依據 `-du` / `--deleteupload` 參數設定的閾值，自動刪除已上傳的影片檔案，並將下載排程調整為每 4 小時一次。
- [ ] **完成 Zeabur 平台部署:** 微調 `Dockerfile` 與 `Procfile` 設定，確保在 Zeabur 環境中所有服務都能穩定運行。
- [ ] **設定環境變數:** 在 Zeabur 平台上安全地設定 `sessionid`、`YT_REQUEST`、`GEMINI_API_KEY` 等所有必要的環境變數。
- [ ] **端對端測試 (雲端):** 在部署完成後，進行一次完整的端對端測試，驗證從爬取、下載、上傳到排程的整個流程在雲端環境中是否正常。

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

### Phase 3: 擴充與優化 (已全部完成)

- [x] **錯誤處理強化:** 為 `scraper.py` 和 `downloader.py` 增加了更完善的錯誤處理與重試機制。
- [x] **日誌輸出優化:** 大幅減少了不必要的日誌輸出，提升了日誌清晰度。
- [x] **上傳器憑證管理:** 增強了 `request.token` 憑證的處理邏輯，使其在部署環境中更靈活、更安全。
- [x] **修正按讚功能:** 透過獨立的測試腳本 `like_tester.py` 與瀏覽器日誌分析，成功定位並解決了 `fetch` API 呼叫失敗的問題。
- [x] **容器化修正 (Docker):** 解決了 `apt-key` 棄用導致的 Docker build 失敗問題。
- [x] **排程器修正 (Scheduler):** 修正了因模組重構導致的 `ImportError` 問題。

### Phase 4: 雲端部署與自動化 (進行中)

- [x] **架構重構:** 將資料庫初始化邏輯移至主程式入口，確保啟動順序穩定。
- [x] **部署修正 (Datasette):** 為 `datasette` 指令加上 `--create` 旗標，解決了啟動時的競爭條件 (race condition) 問題。
- [x] **多進程管理 (Honcho):** 引入 `honcho` 來管理 `Procfile`，實現在 Docker 環境中同時運行爬蟲、排程器與 `datasette` 網頁介面等多個服務。
- [x] **部署修正 (Dockerfile):** 修正了多階段建置中，因未完整複製可執行檔而導致的 `honcho not found` 執行階段錯誤。
- [x] **部署修正 (Uploader):** 修正了因平台不相容（在 Linux 執行 .exe）導致的上傳器執行失敗問題，改為在 Docker build 階段自動安裝其 Linux 版本。
- [x] **資料庫路徑重構:** 為了適應雲端部署的永久性磁碟掛載，建立了 `db` 資料夾，並將所有資料庫檔案的路徑參考都更新至此，同時更新了說明文件。
- [ ] **完成 Zeabur 平台部署:** 微調 `Dockerfile` 與 `Procfile` 設定，確保在 Zeabur 環境中所有服務都能穩定運行。
- [ ] **設定環境變數:** 在 Zeabur 平台上安全地設定 `sessionid`、`YT_REQUEST`、`GEMINI_API_KEY` 等所有必要的環境變數。
- [ ] **端對端測試 (雲端):** 在部署完成後，進行一次完整的端對端測試，驗證從爬取、下載、上傳到排程的整個流程在雲端環境中是否正常。
- [ ] **增加多執行緒:** 研究為下載過程加入多執行緒，以加速大量影片的下載。
- [ ] **AI 增強:** 評估 `Whisper` (語音轉文字), `OpenCV` (影片處理) 等 AI 相關函式庫，為未來增加 AI 功能做準備。
