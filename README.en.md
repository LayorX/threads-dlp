# threads-dlp

<div align="center">
<img src="./images/banner.jpg" alt="Project Banner" style="border-radius: 10px; margin-top: 10px; margin-bottom: 10px;width: 500px; height: 250px;">

[中文說明](./README.md)
</div>

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

## Core Dependencies

### YouTube Uploader

The automated upload functionality of this project is powered by the excellent open-source tool [youtubeuploader](https://github.com/porjo/youtubeuploader), developed by [porjo](https://github.com/porjo).

#### Cross-Platform Strategy (Windows vs. Linux)

To balance the convenience of local development with the compatibility requirements of cloud deployment, we have adopted the following strategy:

- **Windows (Local Development):** The project repository directly includes the `youtubeuploader.exe` executable. When you run `uploader.py` in a Windows environment, it defaults to using this file, allowing you to test the upload functionality locally without extra setup.
- **Linux (Cloud Deployment):** The `Dockerfile` is configured to automatically download the latest **Linux (amd64)** version from the official `youtubeuploader` releases page during the Docker image build process. This ensures that the upload command executes correctly in Linux-based cloud environments like Zeabur.

This approach guarantees seamless use of the upload feature, whether you are developing locally or deploying to the cloud.

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

Make sure you have activated the virtual environment (`.venv\Scripts\activate` on Windows). The project consists of two main executable scripts: `main.py` (the primary downloader) and `uploader.py` (the standalone uploader).

### `main.py` (Downloader)

This is the main entry point for scraping and downloading videos. It can also trigger the upload process upon completion.

#### Arguments

| Short | Long | Description | Default |
| :--- | :--- | :--- | :--- |
| `-t` | `--target` | Specify the Threads username to scrape. | `None` (scrapes the home feed if omitted) |
| `-s` | `--search` | Scrape based on a search query instead of a user. | `None` |
| `-r` | `--scroll` | Number of times to scroll down the page for more content. | `3` |
| `-o` | `--output` | Specify the directory to save downloaded videos. | `downloads` |
| `-l` | `--language` | Set the language for log output. | `zh-TW` |
| `-u` | `--upload` | Automatically execute the uploader after download tasks are complete. | `False` |
| `-du`| `--deleteupload` | (Used with `--upload`) Sets the cleanup threshold (GB). If the `downloads` folder size exceeds this value, already **uploaded** video files will be automatically deleted to free up space. | `0.8` |
| `-n` | `--num_videos` | (Used with `--upload`) Specifies the maximum number of videos to upload. | Unlimited |
| `-d` | `--debug` | Enable detailed log output mode for debugging. | `False` |
| `-v` | `--version`| Show the current version of the program. | - |

#### Examples

**1. Download Videos from a Specific User (Basic)**
```bash
# Download videos from user 'zuck' with the default scroll count (3)
uv run python main.py -t zuck
```

**2. Specify Output Directory and Scrape Depth**
```bash
# Download from 'zuck', scroll 10 times, and save videos to the 'zuck_videos' folder
uv run python main.py -t zuck -r 10 -o zuck_videos
```

**3. Search and Download by Keyword**
```bash
# Search for "cats" and download the resulting videos
uv run python main.py -s "cats"
```

**4. Download from Your Home Feed**
```bash
# Simply run the script without -t or -s
uv run python main.py
```

**5. Download and Automatically Trigger Upload**
```bash
# Download videos from 'zuck' and start the upload process immediately after
uv run python main.py -t zuck -u
```

### `uploader.py` (Standalone Uploader)

This script checks the database for downloaded videos that have not yet been uploaded and publishes them to YouTube. It can be run independently to process a backlog of videos.

#### Arguments

| Short | Long | Description | Default |
| :--- | :--- | :--- | :--- |
| `-du`| `--deleteupload` | Sets the cleanup threshold (GB). If the `downloads` folder size exceeds this value, already **uploaded** video files will be automatically deleted to free up space. | `0.8` |
| `-n` | `--num_videos` | Specifies the maximum number of videos to upload in this run. | Unlimited |

#### Examples

**1. Run the Uploader with Default Cleanup Threshold**
```bash
# Check the database and upload pending videos.
# Before uploading, it checks if the 'downloads' folder exceeds 0.8 GB and cleans up if necessary.
uv run python uploader.py
```

**2. Run the Uploader with a Custom Cleanup Threshold**
```bash
# Set the cleanup threshold to 1.5 GB.
# Cleanup will only be triggered if the folder size is over 1.5 GB.
uv run python uploader.py -du 1.5
```

**3. Use Custom Cleanup Threshold in a Download-Upload Workflow**
```bash
# Download from 'zuck', then trigger the uploader.
# During the upload phase, use a 0.5 GB cleanup threshold.
uv run python main.py -t zuck --upload --deleteupload 0.5
```

### `view_db.py` (Database Viewer)

A simple utility to quickly view the database content in your terminal.

```bash
uv run python view_db.py
```

## 🔑 YouTube API Setup (for Auto-Upload Feature)

> **Important Note:**
> If your Google Cloud project's OAuth consent screen is in "Testing" status, the generated `request.token` will only be valid for **7 days**. To obtain a long-term valid token, you must "**Publish**" your application to production status in the Google Cloud Console. After publishing, you will need to regenerate `request.token` once.

To use the automatic YouTube upload feature (`--upload`), you must first complete the Google API authorization setup, following the official guide for `youtubeuploader`. This process involves two main steps: obtaining `client_secrets.json` and generating `request.token`.

### Step 1: Obtain `client_secrets.json`

This file acts as the "key" for your application, letting Google know it's your program making the upload requests.

1.  **Go to the Google Cloud Console**:
    *   Log in to your Google account and navigate to the [Google Cloud Console](https://console.cloud.google.com/).

2.  **Create a New Project**:
    *   At the top of the page, click the project dropdown menu and select "New Project".
    *   Give the project a name (e.g., `Threads Uploader`) and click "Create".

3.  **Enable the YouTube Data API v3**:
    *   In the left navigation panel, go to "APIs & Services" > "Enabled APIs & services".
    *   Click "+ ENABLE APIS AND SERVICES" at the top.
    *   Search for "YouTube Data API v3", click on it, and then click "Enable".

4.  **Configure the OAuth Consent Screen**:
    *   In the left navigation panel, click on "OAuth consent screen".
    *   Choose "External" and click "Create".
    *   Fill in an application name (e.g., `My Uploader`) and select your email. You can leave the other fields blank for now.
    *   In the "Test users" step, click "+ ADD USERS" and **enter the email address of the Google account you will use for uploading videos**. This is a critical step; otherwise, the authorization will fail later.
    *   Save and continue until the setup is complete.

5.  **Create Credentials (OAuth Client ID)**:
    *   In the left navigation panel, click on "Credentials".
    *   Click "+ CREATE CREDENTIALS" at the top and select "OAuth client ID".
    *   For "Application type", choose "**Web application**".
    *   Give it a name (e.g., `youtubeuploader-creds`).
    *   Under the "Authorized redirect URIs" section, click "+ ADD URI" and enter `http://localhost:8080/oauth2callback`.
    *   Click "Create".

6.  **Download the Credential File**:
    *   After creation, you will see the new client ID in your credentials list.
    *   Click the "Download JSON" icon on the far right.
    *   **Rename the downloaded file to `client_secrets.json`** and place it in the root directory of your `threads-dlp` project.

### Step 2: Generate `request.token`

This file is the "pass" that grants your application permission to act on behalf of your personal account.

1.  **Run an Upload Command Once**:
    *   Make sure `client_secrets.json` is in your project's root directory.
    *   Run a command that includes the upload flag in your terminal, for example:
        ```bash
        uv run python main.py zuck --upload
        ```
2.  **Complete the Browser Authorization**:
    *   The program will print a URL starting with `localhost` in your terminal and wait.
    *   **Copy this URL** and paste it into your browser.
    *   Log in with the same Google account you added as a "Test user".
    *   Grant the requested permissions.
    *   After authorization, the page will redirect to a `localhost` URL that cannot be reached. This is expected. **Copy this entire redirected URL from your browser's address bar**.
3.  **Paste the Authorization Code**:
    *   Return to your terminal. The program will be prompting you to paste the URL.
    *   Paste the URL you just copied and press Enter.
4.  **Token Generation**:
    *   Upon successful validation, the uploader will automatically generate a file named `request.token` in your project's root directory.

After completing these steps, your project will have full permission to upload videos automatically. Both `client_secrets.json` and `request.token` should be treated as confidential files and should never be committed to a public Git repository (the project's `.gitignore` already ignores them by default).

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

### Step 4: Configure Persistent Volumes (Very Important)

To ensure your database (`threads_dlp.db`) and downloaded videos are not lost when the service restarts, and to avoid unnecessary memory charges from using the ephemeral filesystem, you must mount a persistent volume for your storage paths.

1.  In your Zeabur project page, click on the **Volumes** tab.
2.  Click **Create Volume**.
3.  Create two volumes and mount them to the following paths respectively:
    *   **Mount Path 1:** `/home/appuser/db` (for storing the database file)
    *   **Mount Path 2:** `/home/appuser/downloads` (for storing downloaded videos)

> **Warning:** If you skip this step, all your downloaded videos and database records will be **permanently lost** every time the service restarts or redeploys.

### Step 5: Configure Environment Variables

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