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

## Usage

1.  **Set up the environment:**
    ```bash
    # Install uv (if you haven't already)
    pip install uv

    # Create a virtual environment
    uv venv

    # Activate the virtual environment (Windows)
    .venv\Scripts\activate

    # Install dependencies
    uv sync
    ```

2.  **Create the `.env` file:**
    - In the project root, create a file named `.env`.
    - Add your Threads session cookie to it:
      ```
      THREADS_SESSION_COOKIE="your_session_id_string_here"
      ```

3.  **Run the downloader:**

    - **Mode 1: Target a specific user**
      ```bash
      uv run python main.py zuck
      ```

    - **Mode 2: Search for a keyword**
      ```bash
      uv run python main.py --search "keyword here"
      ```

    - **Mode 3: Scrape the default home feed**
      ```bash
      uv run python main.py
      ```

4.  **(Optional) Run downloader and uploader sequentially:**
    - Add the `--upload` flag to automatically trigger the uploader after the download is complete.
      ```bash
      uv run python main.py zuck --upload
      ```

5.  **(Optional) Run the uploader independently:**
    - To only upload videos that are already in the database but not yet uploaded.
      ```bash
      uv run python uploader.py
      ```

## YouTube API Setup

Talking to the Youtube API requires oauth2 authentication. As such, you must:

1. Create an account on the [Google Developers Console](https://console.developers.google.com)
1. Create a new project for this app
1. Enable the Youtube API (APIs & Services -> Enable APIs and Services -> Click 'ENABLE APIS AND SERVICES' top right). Select 'YouTube Data API v3'
1. Create OAuth consent screen (APIs & Services -> OAuth Consent Screen)
   - Add a test user in "Audience -> Test users". This can be any Google User account but it should correspond with the Youtube account where videos will be uploaded.
1. Create Credentials (APIs & Services -> Credentials -> click 'CREATE CREDENTIALS'), select 'OAuth client ID', select 'Web application'
   - Add an 'Authorized redirect URI' of 'http://localhost:8080/oauth2callback'
1. Download the client secrets JSON file (click download icon next to newly created client ID) and save it as file `client_secrets.json` in the same directory as the utility e.g.

```json
{
  "web": {
    "client_id": "xxxxxxxxxxxxxxxxxxxxxxxx.apps.googleusercontent.com",
    "project_id": "youtubeuploader-yyyyy",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "xxxxxxxxxxxxxxxxxxxx",
    "redirect_uris": [
      "http://localhost:8080/oauth2callback"
    ]
  }
}
```

**NOTE 1** Google will apply 'private' status on videos uploaded to newly created projects - from [Google's Announcement](https://developers.google.com/youtube/v3/revision_history#july-28,-2020):

> All videos uploaded via the videos.insert endpoint from unverified API projects created after 28 July 2020 will be restricted to private viewing mode. To lift this restriction, each project must undergo an audit to verify compliance with the Terms of Service.

## ⚠️ Disclaimer

This tool is for technical research and educational purposes only. The copyright of the downloaded videos belongs to the original author. Please respect copyright and adhere to the Threads Terms of Service. The developer is not responsible for any copyright disputes or legal issues arising from the use of this tool.
