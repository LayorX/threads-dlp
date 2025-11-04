# uploader.py

import os
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
import logging
import sys
from dotenv import load_dotenv

from modules.database import init_db, get_all_videos_to_upload, update_upload_status

def setup_logging():
    """設定日誌，確保在被匯入時不會重複加入 handler。"""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler("upload_log.txt", encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
        console_handler = logging.StreamHandler(sys.stdout)
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except TypeError:
            pass
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
    
    

def load_config() -> dict:
    """從環境變數和 config.json 載入設定，環境變數優先。"""
    # 為了本地開發，先載入 .env 檔案
    load_dotenv()

    # 先從 config.json 讀取基本設定 (如果存在)
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}

    # 用環境變數覆寫設定，提供雲端部署的靈活性
    # 秘密金鑰
    config['api_key'] = os.getenv('GEMINI_API_KEY', config.get('api_key'))
    
    # 路徑設定
    config['youtube_uploader_path'] = os.getenv('YOUTUBE_UPLOADER_PATH', config.get('youtube_uploader_path', './youtubeuploader'))
    
    # 排程邏輯
    config['is_publish_now'] = os.getenv('PUBLISH_NOW', str(config.get('is_publish_now', False))).lower() in ['true', '1', 't']
    config['publish_start_from'] = int(os.getenv('PUBLISH_START_FROM_HOURS', config.get('publish_start_from', 0)))
    config['time_increment_hours'] = int(os.getenv('PUBLISH_INTERVAL_HOURS', config.get('time_increment_hours', 2)))

    # 檢查關鍵設定是否存在
    if not config.get('api_key') or "GEMINI API" in config.get('api_key', ''):
        logging.warning("警告: Gemini API 金鑰未設定。請設定 GEMINI_API_KEY 環境變數或在 config.json 中填寫。")

    return config

def generate_metadata(full_caption: str, video_filename: str, publish_time_iso: str, config: dict):
    if not full_caption or not full_caption.strip():
        full_caption = os.path.splitext(video_filename)[0].replace('_', ' ').replace('-', ' ').strip()
        logging.info(f"原始描述為空，使用檔名 '{full_caption}' 作為備用。")

    if not full_caption or not full_caption.strip():
        full_caption = "A fun video" # Final fallback
        logging.warning(f"備用描述依然為空，強制使用通用描述: '{full_caption}'")
        
    api_key = config.get("api_key")
    if not api_key:
        raise ValueError("Gemini API 金鑰未設定。")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    prompt = f"""
    As a professional YouTube content strategist, generate metadata in JSON format for a video based on the following information.
    **Strict Requirements:**
    1.  **JSON Only:** Your response MUST only contain the JSON content, with no extra text or markdown like ```json ... ```.
    2.  **Publish Time:** The `publishAt` field MUST be `{publish_time_iso}`.
    3.  **Localization:** 
        - Main language (`language`) must be `en`.
        - `title` and `description` must be in English.
        - Provide localizations for `zh-TW`, `ja`, `ko`, `fr`, `zh-CN`.
    4.  **Content Optimization:**
        - The title should be catchy, relevant to the video theme, suitable for YouTube Shorts, and occasionally include an emoji.
        - The description should be detailed and include 3-5 relevant hashtags at the end.
    5.  **Video Context:** `{full_caption}`
    6.  **JSON Structure:** Adhere strictly to the provided JSON structure.
    ```json
    {{
      "title": "Engaging English Title",
      "description": "Detailed English description of the video, ending with #hashtags.",
      "tags": ["tag1", "tag2", "tag3"],
      "privacyStatus": "private",
      "madeForKids": false,
      "embeddable": true,
      "license": "youtube",
      "publicStatsViewable": true,
      "publishAt": "{publish_time_iso}",
      "language": "en",
      "localizations": {{
        "zh-TW": {{"title": "影片的繁體中文標題", "description": "影片的繁體中文詳細描述，包含 #hashtags。"}},
        "ja": {{"title": "ビデオの日本語タイトル", "description": "詳細な日本語の説明と #ハッシュタグ。"}},
        "ko": {{"title": "비디오의 한국어 제목", "description": "자세한 한국어 설명과 #해시태그."}},
        "fr": {{"title": "Titre français de la vidéo", "description": "Description détaillée en français avec #hashtags."}},
        "zh-CN": {{"title": "视频的简体中文标题", "description": "视频的简体中文详细描述，包含 #hashtags。"}}
      }}
    }}
    ```
    """

    try:
        logging.info("Generating metadata for the video...")
        response = model.generate_content(prompt, safety_settings=safety_settings)
        cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        return json.loads(cleaned_text)
    except Exception as e:
        logging.error(f"Failed to generate metadata: {e}")
        return None

def upload_video(video_path: str, meta_path: str, config: dict):
    uploader_path = config.get("youtube_uploader_path")
    if not uploader_path or not os.path.exists(uploader_path):
        logging.error(f"Uploader executable not found at '{uploader_path}'. Please set YOUTUBE_UPLOADER_PATH environment variable or configure in config.json.")
        return False
    command = [uploader_path, "-filename", video_path, "-metaJSON", meta_path]
    try:
        logging.info(f"Uploading '{video_path}'...")
        process = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info(f"Successfully uploaded: {video_path}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to upload '{video_path}'. Uploader exited with error.")
        logging.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"An unexpected error occurred during upload: {e}")
        return False

def _ensure_file_from_env(file_path: str, env_var: str):
    """Helper function to ensure a file exists, creating it from an environment variable if not.
    Raises FileNotFoundError if both the file and the environment variable are missing.
    """
    if not os.path.exists(file_path):
        logging.info(f"'{file_path}' not found. Attempting to create from environment variable '{env_var}'.")
        file_data = os.getenv(env_var)
        
        if file_data:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_data)
                logging.info(f"Successfully created '{file_path}' from environment variable.")
            except IOError as e:
                logging.error(f"Failed to write to '{file_path}': {e}")
                raise  # Re-raise the exception as this is a critical failure
        else:
            message = f"FATAL: '{file_path}' not found and '{env_var}' environment variable is not set. Cannot proceed."
            logging.critical(message)
            raise FileNotFoundError(message)

def ensure_token_file_exists():
    """
    Checks for 'request.token' and 'client_secrets.json'. If they don't exist,
    creates them from their respective environment variables.
    This supports storing secrets in the deployment environment.
    """
    _ensure_file_from_env("request.token", "YT_REQUEST")
    _ensure_file_from_env("client_secrets.json", "YT_CLIENT_SECRETS")

def run_upload_task():
    """Core task for uploading videos."""
    setup_logging()
    
    try:
        ensure_token_file_exists()
    except Exception as e:
        logging.error(f"Stopping upload task due to an error in token setup: {e}")
        return

    config = load_config()
    init_db()
    videos_to_upload = get_all_videos_to_upload()
    if not videos_to_upload:
        logging.info("No new videos to upload.")
        return
    logging.info(f"Found {len(videos_to_upload)} videos to upload.")

    is_publish_now = config.get("is_publish_now")
    publish_start_from = config.get("publish_start_from")
    time_increment_hours = config.get("time_increment_hours")

    first_publish_time = datetime.now(timezone.utc) + (timedelta(minutes=5) if is_publish_now else timedelta(hours=publish_start_from))

    for i, video_data in enumerate(videos_to_upload):
        video_id = video_data['video_id']
        video_path = video_data['local_path']
        if not os.path.exists(video_path):
            logging.warning(f"Skipping video ID {video_id}, file not found: {video_path}")
            continue
        
        logging.info(f"--- Processing video {i+1}/{len(videos_to_upload)}: {os.path.basename(video_path)} ---")
        
        publish_time = first_publish_time + timedelta(hours=i * time_increment_hours)
        publish_time_iso = publish_time.isoformat()
        
        video_filename = os.path.basename(video_path)
        meta_filename = f"{os.path.splitext(video_filename)[0]}.json"
        meta_path = os.path.join(os.path.dirname(video_path), meta_filename)
        
        metadata = generate_metadata(video_data['caption'], video_filename, publish_time_iso, config)
        if not metadata:
            logging.warning(f"Skipping video '{video_id}' due to metadata generation failure.")
            continue
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        if upload_video(video_path, meta_path, config):
            try:
                update_upload_status(video_id, status=True)
            except Exception as e:
                logging.critical(f"FATAL: Failed to update database for video {video_id}: {e}")
                break 
        else:
            logging.error(f"Upload failed for video '{video_id}'. Aborting current run.")
            break
        time.sleep(5)
    logging.info("All upload tasks finished.")

def main():
    """CLI entrypoint."""
    run_upload_task()

if __name__ == "__main__":
    main()
