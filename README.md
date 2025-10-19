# threads-dlp

threads-dlp 是一個強大且高韌性的命令列工具，專為從 Threads.net 下載影片而設計。它的誕生源於實際需求，旨在提供一個在其他方法失效時依然穩定可靠的解決方案。

在官方 Threads API 並非所有開發者都能輕易取得、以及通用下載工具無法解析 Threads 現代化動態前端的困境下，threads-dlp 走出了一條自己的路。它不依賴脆弱的 HTML 解析，而是透過自動化一個真實的瀏覽器來模擬人類互動，確保它所看見的網站內容，與一個真實登入的使用者完全相同。

核心功能與哲學：

 * 安全的 Cookie 認證：為了存取需要登入的內容，threads-dlp 使用您瀏覽器的會話 Cookie (Session Cookie)。這個方法既更安全（因為您從不暴露自己的密碼），也更可靠，能輕鬆繞過複雜的登入表單與兩步驟驗證 (2FA)。

 * 智慧型網路嗅探：其提取邏輯的核心在於使用 selenium-wire 攔截來自瀏覽器的所有網路流量。它透過檢查數據回應的 Content-Type 標頭來智慧地篩選和識別影片串流。這種技術遠比搜尋特定的 URL 格式（例如 .mp4）更為穩健，因為無論 URL 如何格式化，它都能找到影片數據本身。

 * 強者驅動：在最終的下載環節，任務被委派給傳奇的 yt-dlp 引擎，充分利用其速度、穩定性與歷經考驗的下載能力。

threads-dlp 這個名字是向經典的 yt-dlp 專案的直接致敬。它繼承了相同的哲學：打造一個強大、專注、且為社群所需要的工具。其中的 'p' 可以代表 Python、Plus (增強版)，或者僅僅是作為其精神繼承者在挑戰新平台時的一個標記。這個專案是一趟深度技術探索之旅的結晶，我們經歷了多重技術挑戰，最終打造出這個穩定、高效的工具，獻給所有創作者與數位資料保存者。

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
