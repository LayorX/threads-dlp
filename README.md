# threads-dlp

<div align="center">
<img src="./images/banner.jpg" alt="Project Banner" style="border-radius: 10px; margin-top: 10px; margin-bottom: 10px;width: 500px; height: 250px;">

[English Version](./README.en.md)
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
- 已安裝 [Python 3.12+](https://www.python.org/downloads/)
- 已安裝 [Google Chrome](https://www.google.com/chrome/)
- 已安裝 [Git](https://git-scm.com/downloads/)

**安裝步驟：**

1.  **克隆專案**
    ```bash
    git clone https://github.com/LayorX/threads-dlp.git
    cd threads-dlp
    ```

2.  **安裝 `uv`**
    `uv` 是一個極速的 Python 套件管理工具。
    ```bash
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3.  **建立虛擬環境並同步依賴**
    ```bash
    uv sync
    ```

4.  **設定環境變數 (`.env` 檔案)**
    在專案根目錄下，建立一個名為 `.env` 的檔案，並填入最基本的本地端執行所需變數：
    ```env
    # 必填：Threads 的 sessionid Cookie
    THREADS_SESSION_COOKIE="填入你的 sessionid"

    # --- 以下為自動上傳功能所需變數 (可選) ---

    # 必填：Google Gemini API 金鑰
    GEMINI_API_KEY="填入你的 Gemini API 金鑰"

    # 選填：將 client_secrets.json 的內容轉為單行字串貼上
    YT_CLIENT_SECRETS='{"web":{"client_id":"...", "client_secret":"...", ...}}'

    # 選填：將 request.token 的內容轉為單行字串貼上
    YT_REQUEST='{"token": "...", "refresh_token": "...", ...}'
    ```
    > **提示:** `YT_CLIENT_SECRETS` 和 `YT_REQUEST` 主要為雲端部署而設計。在本地端，你也可以直接將 `client_secrets.json` 和 `request.token` 檔案放置在專案根目錄下。

## 📖 本地端使用方法

確保你已經啟用了虛擬環境 (`.venv\Scripts\activate`)。

**模式一：下載指定用戶的影片**
```bash
# 只下載
uv run python main.py zuck

# 下載後自動上傳
uv run python main.py zuck --upload
```

**模式二：下載搜尋關鍵字的影片**
```bash
uv run python main.py --search "你想搜尋的關鍵字" --upload
```

**模式三：下載首頁推薦的影片**
```bash
uv run python main.py --upload
```

**模式四：僅執行上傳**
單獨執行上傳器，上傳資料庫中已下載但尚未發布的影片。
```bash
uv run python uploader.py
```

**模式五：查看資料庫**
啟動 Datasette 網頁介面，在 `http://127.0.0.1:8001/` 查看資料庫內容。
```bash
uv run datasette threads_dlp.db
```

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

### 步驟 4：設定環境變數

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