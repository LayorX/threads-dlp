# Threads 影片下載器

一個功能強大的命令列工具，可透過模擬真人登入，從 Threads.net 下載指定用戶頁面上的所有影片。

---

[English Version](./README.en.md)

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
    git clone https://github.com/your-username/theads2yt.git
    cd theads2yt
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

1.  在專案的根目錄 (`theads2yt`) 中，手動建立一個新的文字檔案。
2.  將檔案重新命名為 `.env` (注意，檔案名稱只有一個點和 env)。
3.  用文字編輯器打開 `.env` 檔案，在裡面只寫下面這一行，並將 `你的Cookie值` 替換成你剛才複製的那一長串文字：
    ```
    THREADS_SESSION_COOKIE="你的Cookie值"
    ```
4.  儲存並關閉檔案。您的設定已完成！

## 💡 使用方法

所有指令都在專案根目錄下，透過 `uv run` 執行。

**基本用法：**

爬取 `zuck` 的頁面，預設滾動 3 次，並下載到 `downloads` 資料夾。
```bash
uv run python main.py zuck
```

**進階用法：**

爬取 `threads` 的頁面，滾動 10 次，並下載到 `D:\MyVideos` 資料夾。
```bash
uv run python main.py threads --scroll 10 --output D:\MyVideos
```

### 命令列參數

- `target`: (必需) 要處理的 Threads 使用者名稱 (例如 `zuck`)。
- `--scroll`: (可選) 模擬頁面向下滾動的次數。滾動次數越多，能載入的貼文越多。預設為 `3`。
- `--output`: (可選) 指定儲存影片的資料夾路徑。預設為 `downloads`。

## ⚠️ 免責聲明

本工具僅供技術研究與學習之用。下載的影片版權歸原作者所有。請尊重版權，並遵守 Threads 的服務條款。任何因使用本工具而導致的版權糾紛或法律問題，開發者概不負責。
