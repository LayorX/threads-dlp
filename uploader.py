# uploader.py

import os
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
import logging
import sys
import shutil

from modules.database import init_db, get_all_videos_to_upload, update_upload_status

# --- 日誌設定 ---
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
if not root_logger.handlers:
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

def load_config():
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error("錯誤: 找不到 config.json 設定檔。請從 config.json.template 複製一份並填寫您的 API 金鑰。")
        return None
    except json.JSONDecodeError:
        logging.error("錯誤: config.json 格式不正確。")
        return None

def generate_metadata(full_caption: str, video_filename: str, publish_time_iso: str, config: dict):
    if not full_caption or not full_caption.strip():
        full_caption = os.path.splitext(video_filename)[0].replace('_', ' ').replace('-', ' ').strip()
        logging.info(f"原始描述為空，嘗試使用處理過的檔案名 '{full_caption}' 作為備用描述。")

    if not full_caption or not full_caption.strip():
        full_caption = "一部有趣的影片"  # Final, hardcoded fallback
        logging.warning(f"備用描述依然為空，強制使用通用描述: '{full_caption}'")
        
    api_key = config.get("api_key")
    if not api_key or "GEMINI API" in api_key:
        raise ValueError("Gemini API 金鑰未在 config.json 中設定。")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # 設定安全等級為最低，以最大程度避免因安全審核而返回空內容
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    prompt = f"""
    請你扮演一位專業的 YouTube 內容策略師。
    根據以下的影片檔案名稱，為我生成一份 YouTube 上傳用的元數據 JSON。

    **嚴格要求：**
    0.  **影片相關文字討論資訊** : `{full_caption}`
    1.  **純JSON輸出**：你的回覆 **只能** 包含 JSON 內容，不要有任何額外的說明文字或 markdown 格式 (例如 ```json ... ```)。
    2.  **發布時間**：`publishAt` 欄位的值 **必須** 是 `{publish_time_iso}`。
    3.  **多語言支援**：
        - 主要語言 (`language`) 設為 `en` (英文)。
        - `title` 和 `description` 需為英文。
        - 在 `localizations` 中，提供 `zh-TW` (繁體中文), `ja` (日文), `ko` (韓文), `fr` (法文), `zh-CN` (簡體中文) 的標題和描述。
    4.  **內容優化**：
        - 標題需吸引人，並偶爾加上emoji，並與影片主題相關適合youtubeshort。
        - 描述內容需詳細，並在結尾處自然地包含 3-5 個相關的 hashtags。
    5.  **JSON 結構**：必須完全遵循您提供的 meta.json 結構。

    ```json
    {{
      "title": "影片的繁體中文標題",
      "description": "影片的繁體中文詳細描述，包含 #hashtags。",
      "tags": ["相關標籤1", "相關標籤2", "相關標籤3"],
      "privacyStatus": "private",
      "madeForKids": false,
      "embeddable": true,
      "license": "youtube",
      "publicStatsViewable": true,
      "publishAt": "{publish_time_iso}",
      "language": "zh-TW",
      "localizations": {{
        "zh-TW": {{
          "title": "影片的繁體中文標題",
          "description": "影片的繁體中文詳細描述，包含 #hashtags。",
          "tags": ["tag1", "tag2", "tag3"]
        }},
        "ja": {{
          "title": "ビデオの日本語タイトル",
          "description": "詳細な日本語の説明と #ハッシュタグ。",
          "tags": ["タグ1", "タグ2", "タグ3"]
        }},
        "ko": {{
          "title": "비디오의 한국어 제목",
          "description": "자세한 한국어 설명과 #해시태그.",
            "tags": ["태그1", "태그2", "태그3"]
        }},
        "fr": {{
          "title": "Titre français de la vidéo",
          "description": "Description détaillée en français avec #hashtags.",
            "tags": ["étiquette1", "étiquette2", "étiquette3"]
        }}
        "zh-CN": {{
          "title": "Titre français de la vidéo",
          "description": "Description détaillée en français avec #hashtags.",
            "tags": ["étiquette1", "étiquette2", "étiquette3"]
        }}
      }}
    }}
    ```

    """

    try:
        logging.info(f"正在為影片生成元數據 (基於原始描述)...")
        response = model.generate_content(prompt, safety_settings=safety_settings)

        # 深入的錯誤檢查
        if not response.text:
            logging.error("Gemini API 返回了空的回覆。這很可能是因為內容安全審核 (即使在最低設定下) 或其他 API 限制。")
            try:
                feedback = response.prompt_feedback
                logging.error(f"API Feedback: {feedback}")
            except Exception as e:
                logging.error(f"無法獲取詳細的 API Feedback: {e}")
            return None

        cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        if not cleaned_text:
            logging.error("清理後的 API 回覆為空字串。")
            return None

        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logging.error(f"JSON 解碼失敗: {e}. 收到的原始文本是: '{response.text}'")
        return None
    except Exception as e:
        logging.error(f"生成元數據時發生未預期錯誤: {e}")
        return None

def upload_video(video_path: str, meta_path: str, config: dict):
    # ... (rest of the function is unchanged)
    uploader_path = config.get("youtube_uploader_path")
    if not os.path.exists(uploader_path):
        logging.error(f"錯誤: 上傳器 '{uploader_path}' 不存在。")
        return False
    command = [uploader_path, "-filename", video_path, "-metaJSON", meta_path]
    try:
        logging.info(f"開始上傳 '{video_path}'...")
        process = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info(f"上傳成功: {video_path}")
        logging.info(f"上傳器輸出: {process.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"上傳 '{video_path}' 失敗，youtubeuploader.exe 返回錯誤。")
        logging.error(f"返回碼: {e.returncode}")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"上傳 '{video_path}' 期間發生未預期的錯誤: {e}")
        return False

def main():
    # ... (rest of the function is unchanged)
    config = load_config()
    if not config:
        return
    init_db()
    videos_to_upload = get_all_videos_to_upload()
    if not videos_to_upload:
        logging.info("資料庫中沒有需要上傳的新影片。")
        return
    logging.info(f"發現 {len(videos_to_upload)} 個待上傳的影片。")

    # --- 排程邏輯 ---
    is_publish_now = config.get("is_publish_now", False)
    publish_start_from = config.get("publish_start_from", 0)
    time_increment_hours = config.get("time_increment_hours", 2)

    if is_publish_now:
        first_publish_time = datetime.now(timezone.utc) + timedelta(minutes=5)
        logging.info(f"排程模式：立即發布。第一部影片將在約 5 分鐘後發布。")
    else:
        first_publish_time = datetime.now(timezone.utc) + timedelta(hours=publish_start_from)
        logging.info(f"排程模式：預約發布。第一部影片將從 {publish_start_from} 小時後開始發布。")
    
    logging.info(f"後續影片的發布時間間隔為 {time_increment_hours} 小時。")

    for i, video_data in enumerate(videos_to_upload):
        post_id = video_data['post_id']
        video_path = video_data['local_path']
        full_caption = video_data['caption']
        if not os.path.exists(video_path):
            logging.warning(f"跳過 Post ID: {post_id}，因為找不到本地檔案: {video_path}")
            continue
        
        logging.info(f"--- 正在處理第 {i+1}/{len(videos_to_upload)} 個影片: {os.path.basename(video_path)} (Post ID: {post_id}) ---")
        
        # 使用新的排程邏輯計算發布時間
        publish_time = first_publish_time + timedelta(hours=i * time_increment_hours)
        publish_time_iso = publish_time.isoformat()
        
        logging.info(f"計算出的發布時間為 (ISO 8601): {publish_time_iso}")
        video_filename = os.path.basename(video_path)
        meta_filename = f"{os.path.splitext(video_filename)[0]}.json"
        meta_path = os.path.join(os.path.dirname(video_path), meta_filename)
        metadata = generate_metadata(full_caption, video_filename, publish_time_iso, config)
        if not metadata:
            logging.warning(f"跳過影片 '{post_id}' 因為元數據生成失敗。")
            continue
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        upload_successful = upload_video(video_path, meta_path, config)
        if upload_successful:
            try:
                update_upload_status(post_id, status=True)
                # os.remove(meta_path)
            except Exception as e:
                logging.error(f"[致命錯誤] 更新資料庫狀態失敗: {e}，中止執行。")
                break
        else:
            logging.error(f"影片 '{post_id}' 上傳失敗，中止本次所有任務。")
            break
        time.sleep(5)
    logging.info("所有上傳任務處理完畢。")

if __name__ == "__main__":
    main()
