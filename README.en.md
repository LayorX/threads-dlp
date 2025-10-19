# threads-dlp

[中文說明](./README.md)

---

A command-line tool for downloading videos from Threads.net.

It doesn't rely on the official API or brittle HTML parsing. Instead, it uses **cookie-based authentication** to log in and **intelligently intercepts network traffic** to accurately capture videos. Finally, it calls the powerful **`yt-dlp`** engine to handle the download. This approach ensures stable and efficient operation in a dynamic, login-required web environment.

## ✨ Features

- **Secure Cookie Authentication**: No need to enter your username and password. Uses your browser's session cookie for secure login, protecting your account privacy.
- **Intelligent Network Sniffing**: Unlike traditional HTML scrapers, this tool directly analyzes network traffic to accurately capture video resources, resulting in a higher success rate.
- **Highly Configurable**: Freely specify the target user, the number of page scrolls (scraping depth), and the video storage location.
- **Stable and Reliable**: Built upon two mature open-source projects: `Selenium-Wire` and `yt-dlp`.
- **Standardized Environment**: Uses `uv` for package management to ensure a consistent execution environment on any machine.

## 🚀 Installation Guide

**Prerequisites:**
- [Python 3.10+](https://www.python.org/downloads/) installed
- [Google Chrome](https://www.google.com/chrome/) installed
- [Git](https://git-scm.com/downloads/) installed

**Steps:**

1.  **Clone the Project**
    ```bash
    git clone https://github.com/LayorX/threads-dlp.git
    cd threads-dlp
    ```

2.  **Install `uv` (if not already installed)**
    `uv` is an extremely fast Python package installer and resolver.
    ```bash
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3.  **Create Virtual Environment and Sync Dependencies**
    This command will automatically create a `.venv` virtual environment and install all the necessary packages defined in `pyproject.toml`.
    ```bash
    uv sync
    ```

## ⚙️ Configuration

This tool requires your Threads session cookie to log in. This method is secure and your password will not be exposed.

### 1. How to Get Your Cookie

1.  In your **Chrome** browser, log in to your Threads account as usual.
2.  After logging in, stay on any Threads page and press the `F12` key to open the "Developer Tools".
3.  In the Developer Tools panel, find and click on the `Application` tab.
4.  In the left-hand menu, under `Storage` -> `Cookies`, click on `https://www.threads.net`.
5.  A list will appear on the right. Find the item where the `Name` is **`sessionid`**.
6.  Click on the `sessionid` row, and a long string of text will be displayed in the `Cookie Value` field below. **Completely copy** this entire string.

### 2. Create the `.env` File

1.  In the project's root directory (`threads-dlp`), manually create a new text file.
2.  Rename the file to `.env` (note the dot at the beginning).
3.  Open the `.env` file with a text editor and write only the following line, replacing `your_cookie_value` with the long string you just copied:
    ```
    THREADS_SESSION_COOKIE="your_cookie_value"
    ```
4.  Save and close the file. Your configuration is complete!

## 💡 Usage

All commands are run from the project root directory via `uv run`.

**Basic Usage:**

Scrape the `@zuck` profile with the default 3 scrolls and download to the `downloads` folder.
```bash
uv run python main.py zuck
```

**Advanced Usage:**

Scrape the `@threads` profile with 10 scrolls and download to the `D:\MyVideos` folder.
```bash
uv run python main.py threads --scroll 10 --output D:\MyVideos
```

### Command-Line Arguments

- `target`: (Required) The Threads username to process (e.g., `zuck`).
- `--scroll`: (Optional) The number of times to scroll down the page. More scrolls load more posts. Defaults to `3`.
- `--output`: (Optional) The directory path to save the downloaded videos. Defaults to `downloads`.

## ⚠️ Disclaimer

This tool is for technical research and educational purposes only. The copyright of the downloaded videos belongs to the original author. Please respect copyright and adhere to the Threads Terms of Service. The developer is not responsible for any copyright disputes or legal issues arising from the use of this tool.
