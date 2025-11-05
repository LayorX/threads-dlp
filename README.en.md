# threads-dlp

[中文說明](./README.md)

---

A command-line tool designed for downloading videos from Threads.net. It integrates a full suite of features including scraping, downloading, database management, AI-powered metadata generation, automated YouTube uploading, and cloud deployment.

It doesn't rely on the official API or brittle HTML parsing. Instead, it uses **cookie-based authentication** to log in and **intelligently intercepts network traffic** to accurately capture videos. This approach ensures stable and efficient operation in a dynamic, login-required web environment.

The entire project has been fully containerized and configured for automated deployment on the **Zeabur** platform.

## ✨ Features

- **Secure Cookie Authentication**: No need to enter your username and password. Uses your browser's session cookie for secure login, protecting your account privacy.
- **Intelligent Network Sniffing**: Unlike traditional HTML scrapers, this tool directly analyzes network traffic to accurately capture video resources, resulting in a higher success rate.
- **Multi-Mode Scraping**: Supports scraping from a specific user's profile, keyword search results, or your personal home feed.
- **Automated Uploading**: Integrates with `youtubeuploader` to automatically upload downloaded videos to YouTube.
- **AI Smart Tags**: Uses the Google Gemini API to automatically generate titles, descriptions, and tags for videos.
- **Scheduled Publishing**: Supports multiple YouTube publishing strategies, including immediate, scheduled, and interval-based releases.
- **Database Management**: Uses SQLite to store video metadata, preventing duplicate downloads.
- **Web Dashboard**: Integrates `Datasette` to provide a web interface for browsing and querying the data stored in SQLite.
- **Cloud-Native**: Comes with a complete `Dockerfile` and `Procfile` for one-click deployment to container-supporting cloud platforms like [Zeabur](https://zeabur.com/).

## 🚀 Local Quick Start

**Prerequisites:**
- [Python 3.12+](https://www.python.org/downloads/) installed
- [Google Chrome](https://www.google.com/chrome/) installed
- [Git](https://git-scm.com/downloads/) installed

**Installation Steps:**

1.  **Clone the Project**
    ```bash
    git clone https://github.com/LayorX/threads-dlp.git
    cd threads-dlp
    ```

2.  **Install `uv`**
    `uv` is an extremely fast Python package manager.
    ```bash
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3.  **Create Virtual Environment and Sync Dependencies**
    ```bash
    uv sync
    ```

4.  **Set Up Environment Variables (`.env` file)**
    In the project root directory, create a file named `.env` and fill in the essential variables for local execution:
    ```env
    # Required: The sessionid cookie from Threads
    THREADS_SESSION_COOKIE="your_sessionid_here"

    # --- The following are for the auto-upload feature (optional) ---

    # Required: Google Gemini API Key
    GEMINI_API_KEY="your_gemini_api_key_here"

    # Optional: Paste the content of client_secrets.json as a single line
    YT_CLIENT_SECRETS='{"web":{"client_id":"...", "client_secret":"...", ...}}'

    # Optional: Paste the content of request.token as a single line
    YT_REQUEST='{"token": "...", "refresh_token": "...", ...}'
    ```
    > **Tip:** `YT_CLIENT_SECRETS` and `YT_REQUEST` are primarily designed for cloud deployment. For local development, you can simply place the `client_secrets.json` and `request.token` files in the project's root directory.

## 📖 Local Usage

Make sure you have activated the virtual environment (`.venv\Scripts\activate`).

**Mode 1: Download Videos from a Specific User**
```bash
# Download only
uv run python main.py zuck

# Download and then auto-upload
uv run python main.py zuck --upload
```

**Mode 2: Download Videos from a Keyword Search**
```bash
uv run python main.py --search "your_keyword_here" --upload
```

**Mode 3: Download Videos from Your Home Feed**
```bash
uv run python main.py --upload
```

**Mode 4: Run Uploader Only**
Execute the uploader independently to upload videos that are in the database but not yet published.
```bash
uv run python uploader.py
```

**Mode 5: View the Database**
Start the Datasette web interface to view the database content at `http://127.0.0.1:8001/`.
```bash
uv run datasette threads_dlp.db
```

---

## ☁️ Zeabur Cloud Deployment Guide

This project is fully optimized for Zeabur, enabling one-click deployment and automated operation.

### Step 1: Fork the Project

Click the **Fork** button in the upper-right corner of this GitHub repository to copy this project to your own GitHub account.

### Step 2: Create a Project on Zeabur

1.  Log in to the [Zeabur](https://zeabur.com/) console.
2.  Create a new project and authorize Zeabur to access your GitHub repositories.
3.  Select the `threads-dlp` repository you just forked to deploy.

### Step 3: Service Configuration and Start Commands

Zeabur will automatically detect the `Dockerfile` and deploy it as a service. It uses the `Procfile` to understand how to launch the different processes:

- **`web`**: Runs the `Datasette` service. Zeabur automatically injects the `PORT` environment variable and assigns a public domain name to it.
- **`worker`**: Runs the main scraper scheduler (`scheduler.py`). This is a background service that periodically executes scraping tasks according to the schedule.

You do not need to manually configure the start commands; Zeabur handles this automatically.

### Step 4: Configure Environment Variables

This is the most critical step of the deployment. In your Zeabur project's **Variables** tab, add all of the following environment variables:

| Variable Name             | Description                                                                                                     | How to Obtain                                                                                                                                                                                                              |
| ------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `THREADS_SESSION_COOKIE`  | **(Required)** The `sessionid` cookie for logging into Threads.                                                    | Refer to the "Get Your Threads Cookie" guide in the "Local Quick Start" section of this document.                                                                                                                    |
| `GEMINI_API_KEY`          | **(Required)** Google Gemini API key, used for generating video titles and descriptions.                           | Obtain it from [Google AI Studio](https://aistudio.google.com/).                                                                                                                                                         |
| `YT_CLIENT_SECRETS`       | **(Required)** The content of the `client_secrets.json` file for the YouTube API.                                     | Follow the instructions at the top of the `uploader.py` file to download `client_secrets.json`, then **copy its entire content as a single line** and paste it here.                                                  |
| `YT_REQUEST`              | **(Required)** The content of the `request.token` file for the YouTube API.                                         | After successfully running `--upload` **locally** and completing the browser authorization, a `request.token` file will be generated. **Copy its entire content as a single line** and paste it here.                 |
| `ADMIN_PASSWORD_HASH`     | **(Optional)** The password hash for the Datasette web dashboard.                                                  | If password protection is needed, you can generate a hash using the `datasette-auth-passwords` tool. If left empty, the dashboard will not be accessible for login from the public internet. Default value is `password!`. |
| `UPLOAD_THRESHOLD`        | (Optional) Triggers an upload cycle when the number of videos pending upload exceeds this threshold. Default is `5`. | -                                                                                                                                                                                                                          |
| `UPLOAD_TIME_UTC`         | (Optional) The fixed time (UTC) to run the upload task daily. E.g., `10:00`.                                      | -                                                                                                                                                                                                                          |
| `THREADS_SCROLL_COUNT`    | (Optional) The number of times to simulate scrolling down the page during each scrape. A larger number means a deeper scrape. Default is `5`. | -                                                                                                                                                                                                                          |
| `PUBLISH_NOW`             | (Optional) Whether to set the first video in the upload queue for immediate publishing. `true` or `false`. Default is `true`. | -                                                                                                                                                                                                                          |
| `PUBLISH_START_FROM_HOURS`| (Optional) If `PUBLISH_NOW` is `false`, the first video will be published after N hours. Default is `0`.             | -                                                                                                                                                                                                                          |
| `PUBLISH_INTERVAL_HOURS`  | (Optional) The time interval (in hours) between video publications in the upload queue. Default is `4`.            | -                                                                                                                                                                                                                          |

### Step 5: Complete the Deployment

After saving all environment variables, Zeabur will automatically redeploy your service. Once successful:
- You can access your Datasette dashboard via the `*.zeabur.app` URL provided by Zeabur.
- The `worker` service will run automatically in the background, periodically scraping, downloading, and uploading videos according to your schedule settings.

## ⚠️ Disclaimer

This tool is for technical research and educational purposes only. The copyright of the downloaded videos belongs to the original author. Please respect copyright and adhere to the Threads Terms of Service. The developer is not responsible for any copyright disputes or legal issues arising from the use of this tool.