# threads-dlp

[English Version](./README.en.md)

---

一個專為從 Threads.net 下載影片而設計的命令列工具。

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

本工具需要使用您的 Threads Session Cookie 來進行登入。這個方法安全可靠，您的密碼不會被洩露。

### 1. 如何獲取 Cookie

1.  在您的 **Chrome** 瀏覽器中，正常登入您的 Threads 帳號。
2.  登入後，停在 Threads 的任何頁面上，按下鍵盤上的 `F12` 鍵，打開「開發者工具」。
3.  在開發者工具面板中，找到並點擊 `Application` (應用程式) 分頁。
4.  在左側選單的 `Storage` -> `Cookies` 下，點擊 `https://www.threads.net`。
5.  在右側列表中，找到 `Name` 為 **`sessionid`** 的那一項。
6.  點擊 `sessionid` 這一行，在下方 `Cookie Value` 欄位中會顯示一長串文字。**完整地複製**這一整串文字。

### 2. 建立 `.env` 檔案

1.  在專案的根目錄 (`threads-dlp`) 中，手動建立一個新的文字檔案。
2.  將檔案重新命名為 `.env` (注意，檔案名稱只有一個點和 env)。
3.  用文字編輯器打開 `.env` 檔案，在裡面只寫下面這一行，並將 `你的Cookie值` 替換成你剛才複製的那一長串文字：
    ```
    THREADS_SESSION_COOKIE="你的Cookie值"
    ```
4.  儲存並關閉檔案。您的設定已完成！

## 💡 使用方法

所有指令都在專案根目錄下，透過 `uv run` 執行。

**1. 爬取指定用戶的頁面：**
```bash
uv run python main.py zuck
```

**2. 搜尋關鍵字：**
```bash
uv run python main.py --search "funny cats"
```

**3. 爬取你的「為你推薦」首頁：**
```bash
uv run python main.py
```

**查看下載紀錄：**

在命令列中以表格形式，列出所有已成功下載並記錄的影片。
```bash
uv run python view_db.py
```

### 命令列參數 (`main.py`)

本工具支援三種模式，請擇一使用：

1.  **`target`** (可選): 指定一個 Threads 使用者名稱 (例如 `zuck`)。
2.  **`--search`** (可選): 給定一個關鍵字進行搜尋 (例如 `"funny cats"`)。
3.  **(無參數)**: 如果 `target` 和 `--search` 均未提供，則會爬取預設的 Threads 首頁推薦內容。

**其他參數：**

- `--scroll`: (可選) 模擬頁面向下滾動的次數。滾動次數越多，能載入的貼文越多。預設為 `3`。
- `--output`: (可選) 指定儲存影片的資料夾路徑。預設為 `downloads`。

## ⚠️ 免責聲明

本工具僅供技術研究與學習之用。下載的影片版權歸原作者所有。請尊重版權，並遵守 Threads 的服務條款。任何因使用本工具而導致的版權糾紛或法律問題，開發者概不負責。
