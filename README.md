# threads-dlp

[English Version](./README.en.md)

---

一個專為從 Threads.net 下載影片而設計的命令列工具!

它不依賴官方 API 或脆弱的 HTML 解析，而是透過 **Cookie 認證** 登入，並 **智慧地攔截網路流量** 來精準獲取影片。最後，它呼叫強大的 **`yt-dlp`** 引擎來完成下載。這個方法確保了在高動態、需要登入的網站環境下，依然能穩定、高效地運作。

## ✨ 功能特性

- **安全的 Cookie 認證**：無需輸入帳號密碼，透過瀏覽器 Cookie 安全登入，保護您的帳號隱私。
- **智慧型網路嗅探**：不同於傳統的 HTML 爬蟲，本工具直接分析網路流量，精準捕獲影片資源，成功率更高。
- **高度可設定**：可自由指定目標用戶、頁面滾動次數（爬取深度）以及影片儲存位置。
- **穩定可靠**：基於 `Selenium-Wire` 和 `yt-dlp` 兩大成熟開源專案打造。
- **環境標準化**：使用 `uv` 進行套件管理，確保在任何機器上都能有一致的執行環境。

## 🚀 安裝指南

**先決條件:**
- 已安裝 [Python 3.10+](https://www.python.org/downloads/)
- 已安裝 [Google Chrome](https://www.google.com/chrome/)
- 已安裝 [Git](https://git-scm.com/downloads/)

**步驟：**

1.  **克隆專案**
    ```bash
    git clone https://github.com/LayorX/threads-dlp.git
    cd threads-dlp
    ```

2.  **安裝 `uv` (如果尚未安裝)**
    `uv` 是一個極速的 Python 套件安裝與管理工具。
    ```bash
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3.  **建立虛擬環境並同步依賴**
    此指令會自動建立一個 `.venv` 虛擬環境，並安裝 `pyproject.toml` 中定義的所有必要套件。
    ```bash
    uv sync
    ```

## ⚙️ 設定教學

### 1. 獲取 Threads Cookie

本工具需要使用您的 Threads Session Cookie 來進行登入。這個方法安全可靠，您的密碼不會被洩露。

1.  在您的 **Chrome** 瀏覽器中，正常登入您的 Threads 帳號。
2.  登入後，停在 Threads 的任何頁面上，按下鍵盤上的 `F12` 鍵，打開「開發者工具」。
3.  在開發者工具面板中，找到並點擊 `Application` (應用程式) 分頁。
4.  在左側選單的 `Storage` -> `Cookies` 下，點擊 `https://www.threads.net`。
5.  在右側列表中，找到 `Name` 為 **`sessionid`** 的那一項。
6.  點擊 `sessionid` 這一行，在下方 `Cookie Value` 欄位中會顯示一長串文字。**完整地複製**這一整串文字。
7.  在專案根目錄下，手動建立一個名為 `.env` 的檔案，並將以下內容貼入，替換掉 `你的Cookie值`：
    ```
    THREADS_SESSION_COOKIE="你的Cookie值"
    ```

### 2. 自動上傳功能設定 (可選)

如果你想使用下載後自動上傳至 YouTube 的功能，請完成以下設定。

**步驟 1: 設定 Gemini API 金鑰 & 排程**

1.  將專案中的 `config.json.template` 複製一份，並重新命名為 `config.json`。
2.  用文字編輯器打開 `config.json`。
3.  **`api_key`**: 填入你的 Google AI Studio (Gemini) API 金鑰。
4.  **`is_publish_now`**: 設定第一部影片是否要「立即發布」。`true` 表示在 5 分鐘後發布，`false` 表示根據下一個參數進行預約。
5.  **`publish_start_from`**: 如果 `is_publish_now` 為 `false`，這裡的數字代表第一部影片要從**幾小時後**開始發布。
6.  **`time_increment_hours`**: 後續影片之間的時間間隔（以小時為單位）。

**步驟 2: 設定 YouTube API 憑證**

1.  前往 [Google Cloud Console](https://console.developers.google.com)。
2.  建立一個新專案，並為其啟用 **YouTube Data API v3**。
3.  設定「OAuth 同意畫面」，並在「測試使用者」中加入你的 Google 帳號。
4.  前往「憑證」頁面，點擊「建立憑證」，選擇 **OAuth 用戶端 ID**。
5.  在「應用程式類型」中，**務必選擇「電腦版應用程式」(Desktop app)**。
6.  建立後，你會得到一組用戶端 ID 和密鑰。點擊旁邊的「下載 JSON」圖示。
7.  將下載的 JSON 檔案，重新命名為 `client_secrets.json`，並放置在專案的根目錄下。

**步驟 3: 首次執行與授權**

- 當你第一次使用 `--upload` 功能時，程式會自動打開一個瀏覽器視窗，要求你登入 Google 帳號並授權。這是正常且安全的流程。
- 授權成功後，專案目錄下會自動生成一個 `request.token` 檔案。只要這個檔案存在，未來執行上傳就不再需要手動授權。

## 📖 使用方法

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
# 只下載
uv run python main.py --search "你想搜尋的關鍵字"

# 下載後自動上傳
uv run python main.py --search "你想搜尋的關鍵字" --upload
```

**模式三：下載首頁推薦的影片**
```bash
# 只下載
uv run python main.py

# 下載後自動上傳
uv run python main.py --upload
```

**模式四：僅執行上傳**
如果只想上傳資料庫中已下載但尚未上傳的影片，可以單獨執行上傳器。
```bash
uv run python uploader.py
```

## ⚠️ 免責聲明

本工具僅供技術研究與學習之用。下載的影片版權歸原作者所有。請尊重版權，並遵守 Threads 的服務條款。任何因使用本工具而導致的版權糾紛或法律問題，開發者概不負責。
