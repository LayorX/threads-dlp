# threads-dlp

<div align="center">
<img src="./images/banner.jpg" alt="Project Banner" style="border-radius: 10px; margin-top: 10px; margin-bottom: 10px;width: 500px; height: 250px;">

[English Version](./README.en.md)

---

### ✨ 線上儀表板 (Live Dashboard)

[![Live Demo](https://img.shields.io/badge/📊-Live_Dashboard-blue?style=for-the-badge&logo=datasette)](https://101.zeabur.app/)

**點擊上方徽章，查看此專案自動抓取並分析的熱門影片資料庫。**
> **帳號:** `admin` / **密碼:** `password!`

</div>



---

一個專為從 Threads.net 下載影片而設計的命令列工具。它整合了爬取、下載、資料庫管理、AI 元數據生成、自動化 YouTube 上傳以及雲端部署等完整功能。

它不依賴官方 API 或脆弱的 HTML 解析，而是透過 **Cookie 認證** 登入，並 **智慧地攔截網路流量** 來精準獲取影片。這個方法確保了在高動態、需要登入的網站環境下，依然能穩定、高效地運作。

整個專案已針對 **Zeabur** 平台進行了完整的容器化與自動化部署設定。

## ✨ 功能特性

- **安全的 Cookie 認證**：無需輸入帳號密碼，透過瀏覽器 Cookie 安全登入，保護您的帳號隱私。
- **智慧型網路嗅探**：不同於傳統的 HTML 爬蟲，本工具直接分析網路流量，精準捕獲影片資源，成功率更高。
- **多模式爬取**：支援針對特定用戶、關鍵字搜尋結果或個人首頁推薦進行爬取。
- **自動化上傳**：整合 `youtubeuploader`，可將下載的影片自動上傳至 YouTube。
- **AI 智慧標籤**：使用 Google Gemini API 自動為影片生成標題、描述與標籤。
- **排程發布**：支援立即發布、預約發布以及間隔發布等多種 YouTube 發布策略。
- **資料庫管理**：使用 SQLite 儲存影片元數據，避免重複下載。
- **網頁儀表板**：整合 `Datasette`，提供一個網頁介面來瀏覽與查詢儲存在 SQLite 中的資料。
- **雲端原生**：提供完整的 `Dockerfile` 與 `Procfile`，可一鍵部署至 [Zeabur](https://zeabur.com/) 等支援容器的雲端平台。

## 核心依賴

### YouTube Uploader

本專案的自動上傳功能，是透過呼叫由 [porjo](https://github.com/porjo) 開發的強大開源工具 [youtubeuploader](https://github.com/porjo/youtubeuploader) 來實現的。

#### 跨平台策略 (Windows vs. Linux)

為了兼顧本地開發的便利性與雲端部署的相容性，我們採用了以下策略：

- **Windows (本地開發):** 專案中直接包含了 `youtubeuploader.exe` 執行檔。當您在 Windows 環境下執行 `uploader.py` 時，程式會預設使用此檔案，讓您無需額外設定即可在本地測試上傳功能。
- **Linux (雲端部署):** `Dockerfile` 被設定為在建置 Docker 映像時，自動從 `youtubeuploader` 的官方發布頁面下載最新的 **Linux (amd64)** 版本。這確保了程式在 Zeabur 等基於 Linux 的雲端環境中能夠正確執行上傳命令。

這種方式確保了無論您在何種平台進行開發或部署，都能無縫使用上傳功能。

## 🚀 本地端快速開始

**先決條件:**
- 已安裝 [Python 3.10+](https://www.python.org/downloads/) (建議使用 3.10 或更高版本)
- 已安裝 [Google Chrome](https://www.google.com/chrome/)
- 已安裝 [Git](https://git-scm.com/downloads/)

**安裝步驟：**

1.  **克隆專案**
    ```bash
    git clone https://github.com/LayorX/threads-dlp.git
    cd threads-dlp
    ```

2.  **安裝 `uv` (推薦)**
    `uv` 是一個極速的 Python 套件管理工具。如果你已經安裝了 `pip`，也可以直接使用 `pip`。
    ```bash
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3.  **建立虛擬環境並同步依賴 (如果從原始碼安裝)**
    ```bash
    uv sync
    ```

4.  **從 PyPI 安裝 (推薦)**
    如果你只想使用這個工具，可以直接從 PyPI 安裝，無需克隆整個專案。
    ```bash
    uv pip install threads-dlp-layorx
    # 或者使用 pip
    # pip install threads-dlp-layorx
    ```

5.  **設定環境變數 (`.env` 檔案)**
    在專案根目錄下，建立一個名為 `.env` 的檔案，並填入最基本的本地端執行所需變數：
    ```env
    # 必填：Threads 的 sessionid Cookie
    # 如何獲取：登入 Threads 網站，打開瀏覽器開發者工具 (F12)，在 Application -> Cookies 中找到 sessionid 的值。
    THREADS_SESSION_COOKIE="填入你的 sessionid"

    # --- 以下為自動上傳功能所需變數 (可選，但若使用上傳功能則必填) ---

    # 必填：Google Gemini API 金鑰 (用於生成影片標題和描述)
    # 如何獲取：前往 Google AI Studio (https://aistudio.google.com/) 取得。
    GEMINI_API_KEY="填入你的 Gemini API 金鑰"

    # 選填：將 client_secrets.json 的內容轉為單行字串貼上
    # 參考下方 "YouTube API 設定" 獲取
    YT_CLIENT_SECRETS='{"web":{"client_id":"...", "client_secret":"...", ...}}'

    # 選填：將 request.token 的內容轉為單行字串貼上
    # 參考下方 "YouTube API 設定" 獲取
    YT_REQUEST='{"token": "...", "refresh_token": "...", ...}'
    ```
    > **提示:** `YT_CLIENT_SECRETS` 和 `YT_REQUEST` 主要為雲端部署而設計。在本地端，你也可以直接將 `client_secrets.json` 和 `request.token` 檔案放置在專案根目錄下。

## 📖 本地端使用方法

如果你是從 PyPI 安裝，可以直接使用 `threads-dlp` 命令。如果你是從原始碼克隆並使用 `uv sync`，則需要啟用虛擬環境 (`.venv\Scripts\activate`) 並使用 `uv run python main.py`。

### `threads-dlp` (主程式/下載器)

這是最主要的進入點，負責執行爬取和下載任務，並可選擇在下載完成後觸發上傳。

#### 參數說明

| 短格式 | 長格式 | 功能說明 | 預設值 |
| :--- | :--- | :--- | :--- |
| `-t` | `--target` | 指定要爬取的 Threads 用戶名稱。 | `None` (若未指定，則爬取首頁) |
| `-s` | `--search` | 根據關鍵字進行搜尋並爬取結果。 | `None` |
| `-r` | `--scroll` | 模擬頁面向下滾動的次數，數字越大爬取越深。 | `3` |
| `-o` | `--output` | 指定儲存下載影片的資料夾路徑。 | `downloads` |
| `-l` | `--language` | 設定日誌輸出的語言。 | `zh-TW` |
| `-u` | `--upload` | 在下載任務完成後，自動執行上傳任務。 | `False` |
| `-du`| `--deleteupload` | **(需與 `--upload` 一起使用)** 設定清理閾值 (GB)。當 `downloads` 資料夾大小超過此值，將自動刪除**已上傳**的影片檔案以釋放空間。 | `0.8` |
| `-n` | `--num_videos` | **(需與 `--upload` 一起使用)** 指定上傳影片的數量上限。 | 無限制 |
| `-d` | `--debug` | 啟用詳細日誌輸出模式，方便偵錯。 | `False` |

#### 使用範例

**1. 下載指定用戶的影片 (基本)**
```bash
# 從 PyPI 安裝後直接執行
threads-dlp -t zuck

# 從原始碼執行
# uv run python main.py -t zuck
```

**2. 下載並指定儲存位置與爬取深度**
```bash
# 從 PyPI 安裝後直接執行
threads-dlp -t zuck -r 10 -o zuck_videos

# 從原始碼執行
# uv run python main.py -t zuck -r 10 -o zuck_videos
```

**3. 根據關鍵字搜尋並下載**
```bash
# 從 PyPI 安裝後直接執行
threads-dlp -s "cats"

# 從原始碼執行
# uv run python main.py -s "cats"
```

**4. 下載首頁推薦的影片**
```bash
# 從 PyPI 安裝後直接執行 (不帶 -t 或 -s 參數)
threads-dlp

# 從原始碼執行
# uv run python main.py
```

**5. 下載後自動觸發上傳**
```bash
# 從 PyPI 安裝後直接執行
threads-dlp -t zuck -u

# 從原始碼執行
# uv run python main.py -t zuck -u
```

### `uploader.py` (獨立上傳器)

這個腳本負責檢查資料庫中哪些影片尚未上傳，並將它們發布到 YouTube。它也可以獨立執行，處理之前已下載但未上傳的影片。

#### 參數說明

| 短格式 | 長格式 | 功能說明 | 預設值 |
| :--- | :--- | :--- | :--- |
| `-du`| `--deleteupload` | 設定清理閾值 (GB)。當 `downloads` 資料夾大小超過此值，將自動刪除**已上傳**的影片檔案以釋放空間。 | `0.8` |
| `-n` | `--num_videos` | 指定本次上傳影片的數量上限。 | 無限制 |

#### 使用範例

**1. 獨立執行上傳 (使用預設清理閾值)**
```bash
# 從 PyPI 安裝後直接執行
threads-dlp uploader

# 從原始碼執行
# uv run python uploader.py
```

**2. 上傳時自訂清理閾值**
```bash
# 從 PyPI 安裝後直接執行
threads-dlp uploader -du 1.5

# 從原始碼執行
# uv run python uploader.py -du 1.5
```

**3. 在下載+上傳流程中自訂清理閾值**
```bash
# 從 PyPI 安裝後直接執行
threads-dlp -t zuck --upload --deleteupload 0.5

# 從原始碼執行
# uv run python main.py -t zuck --upload --deleteupload 0.5
```

### `view_db.py` (資料庫查看器)

一個簡單的工具，用於在命令列中快速查看資料庫內容。

```bash
# 從 PyPI 安裝後直接執行
threads-dlp view_db

# 從原始碼執行
# uv run python view_db.py
```

## 🔑 YouTube API 設定 (自動上傳功能)

> **重要提醒：**
> 如果您的 Google Cloud 專案的 OAuth 同意畫面處於「測試」狀態，則生成的 `request.token` 只有 **7 天** 的有效期。若要獲得長期有效的 token，請務必在 Google Cloud Console 中將您的應用程式「**發布**」為正式版。發布後，您需要重新生成一次 `request.token`。

若要使用自動上傳至 YouTube 的功能 (`--upload`)，您必須先完成 Google API 的授權設定。此過程遵循 `youtubeuploader` 的官方指南，分為兩大步：獲取 `client_secrets.json` 和生成 `request.token`。

### 步驟 1：獲取 `client_secrets.json`

此檔案相當於您的應用程式的「鑰匙」，讓 Google 知道是您的程式在請求上傳。

1.  **前往 Google Cloud Console**:
    *   登入您的 Google 帳號，然後進入 [Google Cloud Console](https://console.cloud.google.com/)。

2.  **建立新專案**:
    *   在頁面頂部，點擊專案選單，然後選擇「新增專案」。
    *   為專案命名（例如 `Threads Uploader`），然後點擊「建立」。

3.  **啟用 YouTube Data API v3**:
    *   在左側導覽列中，找到「API 和服務」 > 「已啟用的 API 和服務」。
    *   點擊頂部的「+ 啟用 API 和服務」。
    *   搜尋「YouTube Data API v3」並點擊進入，然後點擊「啟用」。

4.  **設定 OAuth 同意畫面**:
    *   在左側導覽列中，點擊「OAuth 同意畫面」。
    *   選擇「外部」，然後點擊「建立」。
    *   填寫應用程式名稱（例如 `My Uploader`），並選擇您的電子郵件。其他欄位暫時可以留空。
    *   在「測試使用者」步驟中，點擊「+ ADD USERS」，然後**輸入您要用來上傳影片的那個 Google 帳號的 Email**。這是非常重要的一步，否則後續授權會失敗。
    *   儲存並繼續，直到完成設定。

5.  **建立憑證 (OAuth 用戶端 ID)**:
    *   在左側導覽列中，點擊「憑證」。
    *   點擊頂部的「+ 建立憑證」，然後選擇「OAuth 用戶端 ID」。
    *   在「應用程式類型」中，選擇「**Web 應用程式**」(Web application)。
    *   為其命名（例如 `youtubeuploader-creds`）。
    *   在「已授權的重新導向 URI」部分，點擊「+ 新增 URI」，然後輸入 `http://localhost:8080/oauth2callback`。
    *   點擊「建立」。

6.  **下載憑證檔案**:
    *   建立成功後，您會在憑證列表中看到剛剛建立的用戶端。
    *   點擊最右側的「下載 JSON」圖示。
    *   將下載的檔案**重新命名為 `client_secrets.json`**，並將它放置在 `threads-dlp` 專案的根目錄下。

### 步驟 2：生成 `request.token`

此檔案是您個人帳號授權給此應用程式的「通行證」。

1.  **執行一次上傳指令**:
    *   確保 `client_secrets.json` 已經放在專案根目錄。
    *   在命令列中執行一次需要上傳的指令，例如：
        ```bash
        uv run python main.py zuck --upload
        ```
2.  **完成瀏覽器授權**:
    *   程式會自動在您的瀏覽器中打開一個 Google 授權頁面，並在命令列中顯示一個 `localhost` 開頭的網址。
    *   **複製該網址**，並在瀏覽器中打開。
    *   登入您在「測試使用者」步驟中設定的那個 Google 帳號。
    *   同意授權請求。
    *   授權成功後，頁面會重新導向到一個無法顯示的 `localhost` 頁面，這是正常的。**請將這個重新導向後的網址完整複製下來**。
3.  **貼上授權碼**:
    *   回到您的命令列，程式會提示您貼上剛剛複製的網址。
    *   貼上網址並按下 Enter。
4.  **生成 Token**:
    *   驗證成功後，`uploader` 會自動在專案根目錄下生成一個名為 `request.token` 的檔案。

完成以上步驟後，您的專案就擁有了完整的自動上傳權限。`client_secrets.json` 和 `request.token` 都應被視為機密檔案，切勿將它們提交到公開的 Git 倉庫中（專案的 `.gitignore` 已預設忽略它們）。

---

## ☁️ Zeabur 雲端部署指南

本專案已完全針對 Zeabur 進行優化，可實現一鍵部署與自動化運行。

### 步驟 1：Fork 專案

點擊本 GitHub 倉庫右上角的 **Fork** 按鈕，將此專案複製到你自己的 GitHub 帳號下。

### 步驟 2：在 Zeabur 上建立專案

1.  登入 [Zeabur](https://zeabur.com/) 控制台。
2.  建立一個新專案，並授權 Zeabur 讀取你的 GitHub 倉庫。
3.  選擇你剛剛 Fork 的 `threads-dlp` 倉庫進行部署。

### 步驟 3：設定服務與啟動指令

Zeabur 會自動偵測到 `Dockerfile`，並將其部署為一個服務。它會根據 `Procfile` 來了解如何啟動不同的進程。

- **`web`**: 運行 `Datasette` 服務。Zeabur 會自動將 `PORT` 環境變數注入，並為其指派一個公開的網域名稱。
- **`worker`**: 運行主要的爬蟲排程器 (`scheduler.py`)。這是一個背景服務，會根據排程定時執行爬取任務。

你不需要手動設定啟動指令，Zeabur 會自動處理。

### 步驟 4：設定永久性磁碟 (非常重要)

為了確保你的資料庫 (`threads_dlp.db`) 和下載的影片不會因為服務重啟而遺失，也為了避免因使用暫存檔案系統而被收取不必要的記憶體費用，你必須為儲存路徑掛載一個永久性磁碟。

1.  在 Zeabur 專案頁面，點擊 **Volumes** 分頁。
2.  點擊 **Create Volume**。
3.  建立兩個磁碟區，並將它們分別掛載到以下路徑：
    *   **Mount Path 1:** `/home/appuser/db` (用於儲存資料庫檔案)
    *   **Mount Path 2:** `/home/appuser/downloads` (用於儲存下載的影片)

> **警告:** 如果你跳過這一步，所有下載的影片和資料庫紀錄都會在每次服務重啟或重新部署後**全部遺失**。

### 步驟 5：設定環境變數

這是部署中最關鍵的一步。在 Zeabur 專案的 **Variables** 分頁中，新增以下所有環境變數：

| 變數名稱                  | 說明                                                                                                             | 如何獲取                                                                                                                                                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `THREADS_SESSION_COOKIE`  | **(必填)** 用於登入 Threads 的 `sessionid` Cookie。                                                                   | 參考本文「本地端快速開始」中的「獲取 Threads Cookie」教學。                                                                                                                                                           |
| `GEMINI_API_KEY`          | **(必填)** Google Gemini API 金鑰，用於生成影片標題和描述。                                                          | 前往 [Google AI Studio](https://aistudio.google.com/) 取得。                                                                                                                                                      |
| `YT_CLIENT_SECRETS`       | **(必填)** YouTube API 的 `client_secrets.json` 內容。                                                                | 參考 `uploader.py` 文件頂部的教學，下載 `client_secrets.json` 後，將其**全部內容複製成一行**貼入。                                                                                                         |
| `YT_REQUEST`              | **(必填)** YouTube API 的 `request.token` 內容。                                                                    | 在**本地端**成功執行一次 `--upload` 並完成瀏覽器授權後，會在專案根目錄下生成 `request.token` 檔案。將其**全部內容複製成一行**貼入。                                                                    |
| `ADMIN_PASSWORD_HASH`     | **(可選)** Datasette 網頁儀表板的登入密碼雜湊值。                                                                  | 如果需要密碼保護，可以使用 `datasette-auth-passwords` 工具生成。若留空，儀表板將無法從公網登入。预设值为 `password!`。|
| `UPLOAD_THRESHOLD`        | (可選) 當資料庫中待上傳影片數量超過此閥值時，觸發一次上傳循環。預設為 `5`。                                        | -                                                                                                                                                                                                                   |
| `UPLOAD_TIME_UTC`         | (可選) 每日固定執行上傳任務的時間（UTC 標準時間）。例如 `10:00`。                                                   | -                                                                                                                                                                                                                   |
| `THREADS_SCROLL_COUNT`    | (可選) 每次爬取時，模擬頁面向下滾動的次數。數字越大，爬取越深。預設為 `5`。                                          | -                                                                                                                                                                                                                   |
| `PUBLISH_NOW`             | (可選) 是否將上傳佇列中的第一部影片設定為立即發布。`true` 或 `false`，預設為 `true`。                                 | -                                                                                                                                                                                                                   |
| `PUBLISH_START_FROM_HOURS`| (可選) 如果 `PUBLISH_NOW` 為 `false`，第一部影片將從 N 小時後發布。預設為 `0`。                                        | -                                                                                                                                                                                                                   |
| `PUBLISH_INTERVAL_HOURS`  | (可選) 上傳佇列中，影片之間的發布時間間隔（小時）。預設為 `4`。                                                    | -                                                                                                                                                                                                                   |

### 步驟 5：完成部署

儲存所有環境變數後，Zeabur 會自動重新部署你的服務。部署成功後：
- 你可以透過 Zeabur 提供的 `*.zeabur.app` 網址訪問你的 Datasette 儀表板。
- `worker` 服務會在背景自動執行，根據你的排程設定，定時爬取、下載並上傳影片。

## ⚠️ 免責聲明

本工具僅供技術研究與學習之用。下載的影片版權歸原作者所有。請尊重版權，並遵守 Threads 的服務條款。任何因使用本工具而導致的版權糾紛或法律問題，開發者概不負責。