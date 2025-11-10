<div align="center">
<img src="./images/banner.jpg" alt="Project Banner" style="border-radius: 10px; margin-top: 10px; margin-bottom: 10px;width: 500px; height: 250px;">

# threads-dlp

**A video downloader and automated publishing tool designed for Threads.net.**

[![PyPI Version](https://img.shields.io/pypi/v/threads-dlp-layorx.svg?style=for-the-badge&logo=pypi)](https://pypi.org/project/threads-dlp-layorx/)
[![Python Version](https://img.shields.io/pypi/pyversions/threads-dlp-layorx.svg?style=for-the-badge&logo=python)](https://pypi.org/project/threads-dlp-layorx/)
[![License](https://img.shields.io/pypi/l/threads-dlp-layorx.svg?style=for-the-badge)](https://github.com/LayorX/threads-dlp/blob/main/LICENSE)
[![Live Demo](https://img.shields.io/badge/📊-Live_Dashboard-blue?style=for-the-badge&logo=datasette)](https://101.zeabur.app/)

[中文版](./README.md)

</div>

---

`threads-dlp` is a powerful command-line tool that integrates scraping, downloading, database management, AI metadata generation, automated YouTube uploading, and cloud deployment.

Instead of relying on official APIs or fragile HTML parsing, it logs in via **Cookie Authentication** and **intelligently intercepts network traffic** to accurately capture videos. This method ensures stable and efficient operation in highly dynamic, login-required website environments.

The entire project is fully containerized and configured for automated deployment on the **Zeabur** platform.

> **Live Dashboard**
>
> **Click the blue badge above to view the database of popular videos automatically scraped and analyzed by this project.**
> > **Account:** `admin` / **Password:** `password!`

---

## ✨ Features

- **Secure Cookie Authentication**: Log in securely with browser cookies without entering your username and password, protecting your account privacy.
- **Intelligent Network Sniffing**: Unlike traditional HTML scrapers, this tool directly analyzes network traffic to capture video resources with higher accuracy and success rates.
- **Multi-Mode Scraping**: Supports scraping from specific user profiles, keyword search results, or your personal home feed.
- **Automated Uploading**: Integrates with `youtubeuploader` to automatically upload downloaded videos to YouTube.
- **AI-Powered Metadata**: Uses the Google Gemini API to automatically generate titles, descriptions, and tags for your videos.
- **Scheduled Publishing**: Supports various YouTube publishing strategies, including immediate, scheduled, and interval-based releases.
- **Database Management**: Uses SQLite to store video metadata, preventing duplicate downloads.
- **Web Dashboard**: Integrates with `Datasette` to provide a web interface for browsing and querying data stored in SQLite.
- **Cloud-Native**: Comes with a complete `Dockerfile` and `Procfile` for one-click deployment to container-supported cloud platforms like [Zeabur](https://zeabur.com/).
- **Disk Space Management**: Automatically monitors and cleans up uploaded video files to prevent disk space exhaustion.

## 🚀 Quick Start

**Prerequisites:**
- [Python 3.10+](https://www.python.org/downloads/)
- [Google Chrome](https://www.google.com/chrome/)
- (Recommended) [uv](https://github.com/astral-sh/uv) - A high-speed Python package installer.

### 1. Install the Tool

The easiest way is to install it directly from PyPI using `uv` or `pip`.

```bash
# Using uv (Recommended)
uv pip install threads-dlp-layorx

# Or using pip
pip install threads-dlp-layorx
```

### 2. Create `.env` Configuration File

In the directory where you plan to run the tool, create a file named `.env` and add the following content:

```env
# Required: Your Threads sessionid cookie
# How to get it: Log in to Threads, open browser developer tools (F12), go to Application -> Cookies, and find the value of 'sessionid'.
THREADS_SESSION_COOKIE="your_sessionid_here"

# --- Optional variables for the auto-upload feature ---

# Required for upload: Google Gemini API Key (for generating video titles and descriptions)
# How to get it: Visit Google AI Studio (https://aistudio.google.com/).
GEMINI_API_KEY="your_gemini_api_key_here"
```
> **Tip:** The full YouTube API variables (`YT_CLIENT_SECRETS`, `YT_REQUEST`) are primarily for cloud deployment. For local use, you just need to generate `client_secrets.json` and `request.token` files and place them in the same directory, as explained in the guide below.

### 3. Start Using It!

You can now run the `threads-dlp` command.

```bash
# Download videos from a specific user (e.g., zuck)
threads-dlp -t zuck

# Download and automatically upload to YouTube
# (The first run will guide you through YouTube API authorization)
threads-dlp -t zuck --upload
```

---
## 🐳 Local Docker Deployment (Advanced)

If you prefer using Docker for an environment consistent with the cloud deployment, follow these steps to run it locally.

**Prerequisites:**
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed

### 1. Clone the Project and Prepare the Environment

You need to clone the project locally first, as Docker needs to read the `Dockerfile` and your configuration file.

```bash
git clone https://github.com/LayorX/threads-dlp.git
cd threads-dlp
```

### 2. Create `.env` Configuration File

Same as in the Quick Start, create a `.env` file in the project root and fill in at least the `THREADS_SESSION_COOKIE`. Docker will load all variables from this file into the container.

```env
THREADS_SESSION_COOKIE="your_sessionid_here"
GEMINI_API_KEY="your_gemini_api_key_here"
# You can also add YT_CLIENT_SECRETS and YT_REQUEST if needed
```

### 3. Build the Docker Image

Run the following command in the project root to build the Docker image.

```bash
docker build -t threads-dlp .
```

### 4. Run the Docker Container

This command starts a container in the background and mounts your local `db` and `downloads` folders into it to ensure data persistence.

```bash
# Ensure local db and downloads folders exist
mkdir -p db downloads

docker run -d \
  --name threads-dlp-container \
  --env-file ./.env \
  -v "$(pwd)/db:/home/appuser/db" \
  -v "$(pwd)/downloads:/home/appuser/downloads" \
  -p 8081:8080 \
  threads-dlp
```
> **Note for Windows Users:** In Command Prompt (CMD), replace `$(pwd)` with `%cd%`.

### 5. Verify and Manage

- **Check Logs**:
  ```bash
  docker logs -f threads-dlp-container
  ```
- **Access Dashboard**:
  Open your browser and go to `http://localhost:8081`.

- **Stop and Remove the Container**:
  ```bash
  docker stop threads-dlp-container
  docker rm threads-dlp-container
  ```

## 📖 Usage

### `threads-dlp` (Main Program/Downloader)

| Short | Long | Description | Default |
| :--- | :--- | :--- | :--- |
| `-t` | `--target` | Specify the Threads username to scrape. | `None` (scrapes home feed) |
| `-s` | `--search` | Search and scrape results based on a keyword. | `None` |
| `-r` | `--scroll` | Number of times to simulate scrolling down the page. | `3` |
| `-o` | `--output` | The folder path to save downloaded videos. | `downloads` |
| `-l` | `--language` | Set the language for log output. | `en-US` |
| `-u` | `--upload` | Automatically run the upload task after downloading. | `False` |
| `-du`| `--deleteupload` | **(Use with `-u`)** Set cleanup threshold (GB). Deletes **uploaded** videos when the `downloads` folder exceeds this size. | `0.8` |
| `-n` | `--num_videos` | **(Use with `-u`)** The maximum number of videos to upload. | No limit |
| `-d` | `--debug` | Enable detailed debug logging. | `False` |

#### Examples

```bash
# Download videos from a user, specifying output and scroll depth
threads-dlp -t zuck -r 10 -o zuck_videos

# Search and download based on a keyword
threads-dlp -s "funny cats"

# Download recommended videos from your home feed
threads-dlp

# Download and auto-upload, setting the disk cleanup threshold to 0.5 GB
threads-dlp -t zuck -u -du 0.5
```

### `uploader` (Standalone Uploader)

This command checks the database for videos that haven't been uploaded yet and publishes them to YouTube.

| Short | Long | Description | Default |
| :--- | :--- | :--- | :--- |
| `-du`| `--deleteupload` | Set the cleanup threshold (GB). | `0.8` |
| `-n` | `--num_videos` | The maximum number of videos to upload in this run. | No limit |

#### Examples
```bash
# Run the upload task independently
threads-dlp uploader

# Run upload with a custom cleanup threshold of 1.5 GB
threads-dlp uploader -du 1.5
```

### `view_db` (Database Viewer)

A simple tool to quickly view the database contents in your terminal.

```bash
threads-dlp view_db
```

## 🔑 YouTube API Setup (For Auto-Upload)

> **Important:**
> If your Google Cloud project's OAuth consent screen is in "Testing" mode, the generated `request.token` will only be valid for **7 days**. For a long-term token, you must **"Publish"** your app in the Google Cloud Console. After publishing, you will need to regenerate the `request.token` one more time.

To use the auto-upload feature (`--upload`), you must first set up Google API authorization. This process follows the official `youtubeuploader` guide and involves two main steps: obtaining `client_secrets.json` and generating `request.token`.

### Step 1: Get `client_secrets.json`

This file acts as the "key" for your application, letting Google know it's your program making the upload request.

1.  **Go to the Google Cloud Console**:
    *   Log in to your Google account and navigate to the [Google Cloud Console](https://console.cloud.google.com/).

2.  **Create a New Project**:
    *   Click the project dropdown at the top of the page and select "New Project".
    *   Name your project (e.g., `Threads Uploader`) and click "Create".

3.  **Enable the YouTube Data API v3**:
    *   In the left navigation pane, go to "APIs & Services" > "Enabled APIs & services".
    *   Click "+ ENABLE APIS AND SERVICES".
    *   Search for "YouTube Data API v3", select it, and click "Enable".

4.  **Configure the OAuth Consent Screen**:
    *   In the left navigation pane, click "OAuth consent screen".
    *   Choose "External" and click "Create".
    *   Fill in the app name (e.g., `My Uploader`) and select your email. You can leave other fields blank for now.
    *   In the "Test users" step, click "+ ADD USERS" and **enter the email address of the Google account you will use for uploading videos**. This is a critical step.
    *   Save and continue until the setup is complete.

5.  **Create Credentials (OAuth client ID)**:
    *   In the left navigation pane, click "Credentials".
    *   Click "+ CREATE CREDENTIALS" and select "OAuth client ID".
    *   For "Application type", choose "**Web application**".
    *   Give it a name (e.g., `youtubeuploader-creds`).
    *   Under "Authorized redirect URIs", click "+ ADD URI" and enter `http://localhost:8080/oauth2callback`.
    *   Click "Create".

6.  **Download the Credentials File**:
    *   After creation, you will see the new client ID in your credentials list.
    *   Click the download JSON icon on the far right.
    *   **Rename the downloaded file to `client_secrets.json`** and place it in the directory where you run `threads-dlp`.

### Step 2: Generate `request.token`

This file is the "pass" that grants your application permission to act on behalf of your personal account.

1.  **Run an Upload Command**:
    *   Make sure `client_secrets.json` is in the current directory.
    *   Run a command that triggers an upload, for example:
        ```bash
        threads-dlp -t zuck --upload
        ```
2.  **Complete Browser Authorization**:
    *   The program will automatically open a Google authorization page in your browser and display a `localhost` URL in the terminal.
    *   **Copy that URL** and open it in your browser.
    *   Log in with the Google account you added as a "Test user".
    *   Approve the authorization request.
    *   After successful authorization, the page will redirect to an unavailable `localhost` page. This is normal. **Copy the full URL of this redirected page**.
3.  **Paste the Authorization Code**:
    *   Return to your terminal. The program will prompt you to paste the URL you just copied.
    *   Paste the URL and press Enter.
4.  **Token Generation**:
    *   Upon successful validation, the program will automatically create a file named `request.token` in the current directory.

After completing these steps, your setup will have full permission to upload videos automatically. Both `client_secrets.json` and `request.token` should be treated as confidential files and should not be committed to a public Git repository.

---

## ☁️ Zeabur Cloud Deployment Guide

This project is fully optimized for Zeabur, allowing for one-click deployment and automated operation.

### Step 1: Fork the Project

Click the **Fork** button in the top-right corner of this GitHub repository to copy it to your own GitHub account.

### Step 2: Create a Project on Zeabur

1.  Log in to your [Zeabur](https://zeabur.com/) dashboard.
2.  Create a new project and authorize Zeabur to access your GitHub repositories.
3.  Select your forked `threads-dlp` repository for deployment.

### Step 3: Configure Services and Start Command

Zeabur will automatically detect the `Dockerfile` and use the `Procfile` to determine how to start the different processes:

- **`web`**: Runs the `Datasette` service, providing a public web dashboard.
- **`worker`**: Runs the main scraper scheduler (`scheduler.py`), which executes tasks in the background.

### Step 4: Configure Persistent Volumes (Crucial)

To ensure your database and videos are not lost on service restarts and to avoid unnecessary memory charges from using the ephemeral filesystem, you must mount persistent volumes.

1.  In your Zeabur project page, go to the **Volumes** tab.
2.  Click **Create Volume**.
3.  Create two volumes and mount them to the following paths:
    *   **Mount Path 1:** `/home/appuser/db` (for the database file)
    *   **Mount Path 2:** `/home/appuser/downloads` (for downloaded videos)

> **Warning:** If you skip this step, all your downloaded videos and database records will be **permanently lost** after each service restart or redeployment.

### Step 5: Set Environment Variables

In the **Variables** tab of your Zeabur project, add the following environment variables:

| Variable Name | Description |
| :--- | :--- |
| `THREADS_SESSION_COOKIE` | **(Required)** The `sessionid` cookie for logging into Threads. |
| `GEMINI_API_KEY` | **(Required)** Your Google Gemini API key. |
| `YT_CLIENT_SECRETS` | **(Required)** The **single-line** content of your `client_secrets.json`. |
| `YT_REQUEST` | **(Required)** The **single-line** content of your `request.token`. |
| `ADMIN_PASSWORD_HASH` | (Optional) The password hash for the Datasette dashboard. Default is `password!`. |
| `UPLOAD_THRESHOLD` | (Optional) Number of pending videos to trigger an upload cycle. Default is `5`. |
| `UPLOAD_TIME_UTC` | (Optional) Fixed time (UTC) to run the upload task daily. E.g., `10:00`. |
| `THREADS_SCROLL_COUNT` | (Optional) Number of scrolls per scraping task. Default is `5`. |
| `PUBLISH_NOW` | (Optional) Whether to publish the first video immediately. `true` or `false`. Default is `true`. |
| `PUBLISH_START_FROM_HOURS`| (Optional) Delay in hours for the first scheduled video. Default is `0`. |
| `PUBLISH_INTERVAL_HOURS` | (Optional) Interval in hours between video publications. Default is `4`. |

### Step 6: Complete Deployment

After saving the environment variables, Zeabur will automatically redeploy your service. Once successful, you can access your dashboard via the provided URL, and the `worker` service will run automatically in the background.

## 🔩 Core Dependencies & Development

### YouTube Uploader

The auto-upload feature is powered by the excellent open-source tool [youtubeuploader](https://github.com/porjo/youtubeuploader) by [porjo](https://github.com/porjo). The project includes a cross-platform strategy for convenience:
- **Windows (Local):** Includes the `youtubeuploader.exe` executable.
- **Linux (Cloud):** The `Dockerfile` automatically downloads the latest Linux version during the image build process.

### Installing from Source (For Developers)

If you want to contribute or modify the project, follow these steps:

1.  **Clone the repository**
    ```bash
    git clone https://github.com/LayorX/threads-dlp.git
    cd threads-dlp
    ```

2.  **Install `uv`**
    ```bash
    # Windows (PowerShell)
    irm https://astral.sh/uv/install.ps1 | iex
    # macOS / Linux
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

3.  **Create a virtual environment and sync dependencies**
    ```bash
    uv sync
    ```
4.  **Run the program**
    ```bash
    uv run python main.py --help
    ```

## ⚠️ Disclaimer

This tool is for educational and research purposes only. The copyright of the downloaded videos belongs to the original creator. Please respect copyright laws and the Threads terms of service. The developer is not responsible for any copyright infringement or legal issues that may arise from the use of this tool.
