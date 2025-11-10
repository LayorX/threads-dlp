import os
import json
import subprocess
import time
from datetime import datetime, timedelta, timezone
import google.generativeai as genai
import logging
import sys
import argparse
from dotenv import load_dotenv

from modules.database import init_db, get_all_videos_to_upload, update_upload_status, get_all_uploaded_videos

def setup_logging():
    """設定一個冪等的日誌記錄器，避免在匯入時重複設定。"""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler("upload_log.txt", encoding='utf-8')
        file_handler.setFormatter(log_formatter)
        root_logger.addHandler(file_handler)
        console_handler = logging.StreamHandler(sys.stdout)
        try:
            # 嘗試設定主控台編碼為 UTF-8，以處理 Windows 環境下的特殊字元
            console_handler.stream.reconfigure(encoding='utf-8')
        except TypeError:
            # 在非 Windows 或不支援的環境中，這個操作可能會失敗
            pass
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)
    
def get_folder_size(path='.'):
    """計算指定路徑下所有檔案的大小，並返回 GB 為單位的值。"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # 確保不是符號連結，以避免重複計算
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size / (1024**3) # 從 Bytes 轉換為 Gigabytes

def cleanup_uploaded_files(downloads_path="downloads"):
    """從資料庫獲取已上傳的影片列表，並刪除其本地檔案及對應的 .json 檔案。"""
    logging.info("開始清理已上傳的檔案...")
    uploaded_video_paths = get_all_uploaded_videos()
    deleted_count = 0
    if not uploaded_video_paths:
        logging.info("資料庫中沒有已上傳的影片可供清理。")
        return

    for video_path in uploaded_video_paths:
        if video_path and os.path.exists(video_path):
            try:
                # 刪除影片檔案
                os.remove(video_path)
                logging.info(f"已刪除已上傳的影片: {video_path}")
                deleted_count += 1

                # 嘗試刪除對應的 metadata.json 檔案
                meta_path = os.path.splitext(video_path)[0] + '.json'
                if os.path.exists(meta_path):
                    os.remove(meta_path)
                    logging.info(f"已刪除對應的元數據檔案: {meta_path}")

            except OSError as e:
                logging.error(f"刪除檔案 {video_path} 時發生錯誤: {e}")
    logging.info(f"清理完畢。共刪除了 {deleted_count} 個影片檔案。")


def load_config() -> dict:
    """從 .env 和 config.json 載入設定，並整合環境變數作為最高優先級。"""
    # 為了本地開發方便，從 .env 檔案載入環境變數
    load_dotenv()

    # 先從 config.json 讀取基礎設定 (如果存在)
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}

    # 從環境變數讀取設定，這會覆寫 config.json 中的同名設定
    # API 金鑰
    config['api_key'] = os.getenv('GEMINI_API_KEY', config.get('api_key'))
    
    # 上傳器路徑 (根據作業系統決定預設值)
    default_uploader_path = './youtubeuploader.exe' if os.name == 'nt' else './youtubeuploader'
    config['youtube_uploader_path'] = os.getenv('YOUTUBE_UPLOADER_PATH', config.get('youtube_uploader_path', default_uploader_path))
    
    # 排程邏輯
    config['is_publish_now'] = os.getenv('PUBLISH_NOW', str(config.get('is_publish_now', False))).lower() in ['true', '1', 't']
    config['publish_start_from'] = int(os.getenv('PUBLISH_START_FROM_HOURS', config.get('publish_start_from', 0)))
    config['time_increment_hours'] = int(os.getenv('PUBLISH_INTERVAL_HOURS', config.get('time_increment_hours', 2)))

    # 檢查關鍵設定是否存在
    if not config.get('api_key') or "GEMINI API" in config.get('api_key', ''):
        logging.warning("警告: Gemini API 金鑰未設定。請設定 GEMINI_API_KEY 環境變數或在 config.json 中填寫。")

    return config

def generate_metadata(full_caption: str, video_filename: str, publish_time_iso: str, config: dict):
    """使用 Gemini API 為影片生成標題、描述和標籤。"""
    # 如果影片本身沒有任何文字描述，則嘗試使用影片檔名作為備用描述
    if not full_caption or not full_caption.strip():
        full_caption = os.path.splitext(video_filename)[0].replace('_', ' ').replace('-', ' ').strip()
        logging.info(f"原始描述為空，改用檔名 '{full_caption}' 作為生成內容的基礎。")

    # 雙重保險：如果處理後描述依然為空，則使用一個通用的預設值
    if not full_caption or not full_caption.strip():
        full_caption = "一部有趣的影片"  # 最終的硬編碼備用方案
        logging.warning(f"生成內容的基礎描述依然為空，強制使用通用描述: '{full_caption}'")
         
    api_key = config.get("api_key")
    if not api_key:
        raise ValueError("Gemini API 金鑰未設定。")
    genai.configure(api_key=api_key)
    
    # 使用較新的模型名稱
    model = genai.GenerativeModel('gemini-flash-lite-latest')
    
    # 設定安全設定，以避免因內容審查而被 API 阻擋
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    prompt = f"""
    你是一位專業的 YouTube 內容策略師。
    請根據以下影片資訊，生成一份用於 YouTube 上傳的中繼資料 JSON。

    **嚴格要求:**
    0.  **影片內容核心摘要** : `{full_caption}`
    1.  **純JSON輸出**: 你的回應 **只能** 包含 JSON 內容，禁止包含任何額外的文字或 markdown 標記 (例如 ```json ... ```)。
    2.  **發布時間**: `publishAt` 欄位的值 **必須** 是 `{publish_time_iso}`。
    3.  **多語言在地化**:
        - 主要語言 (`language`) 設定為 `en` (英文)。
        - `title` 和 `description` 必須是英文。
        - 在 `localizations` 物件中，提供 `zh-TW` (繁體中文), `ja` (日文), `ko` (韓文), `fr` (法文), `zh-CN` (簡體中文) 的標題和描述。
    4.  **內容優化**:
        - 標題應吸引人，與影片主題相關，適合 YouTube Shorts，並可適度包含一個 Emoji。
        - 描述內容應詳細，並在結尾附上 3-5 個相關的 hashtags。
    5.  **JSON 結構**: 嚴格遵守下方提供的 meta.json 結構。

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
        "zh-TW": {{"title": "吸引人的繁體中文標題", "description": "詳細的繁體中文影片描述，以 #hashtags 結尾。"}},
        "ja": {{"title": "魅力的な日本語のタイトル", "description": "詳細な日本語の動画説明、最後に #ハッシュタグ。"}},
        "ko": {{"title": "매력적인 한국어 제목", "description": "자세한 한국어 동영상 설명, #해시태그 로 끝납니다."}},
        "fr": {{"title": "Titre français engageant", "description": "Description détaillée de la vidéo en français, se terminant par des #hashtags."}},
        "zh-CN": {{"title": "吸引人的简体中文标题", "description": "详细的简体中文视频描述，以 #hashtags 结尾。"}}
      }}
    }}
    ```
    """

    try:
        logging.info("正在請求 Gemini API 生成影片元數據...")
        response = model.generate_content(prompt, safety_settings=safety_settings)
        
        # 移除潛在的 Markdown 格式
        cleaned_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        
        if not cleaned_text:
            logging.error("Gemini API 返回了空的內容。")
            return None

        return json.loads(cleaned_text)
    except json.JSONDecodeError as e:
        logging.error(f"JSON 解碼失敗: {e}. 從 API 收到的原始文本是: '{response.text}'")
        return None
    except Exception as e:
        logging.error(f"生成元數據時發生未預期的錯誤: {e}")
        return None

def upload_video(video_path: str, meta_path: str, config: dict):
    """呼叫外部的 youtubeuploader 執行檔來上傳影片。"""
    uploader_path = config.get("youtube_uploader_path")
    if not uploader_path or not os.path.exists(uploader_path):
        logging.error(f"上傳器執行檔在 '{uploader_path}' 未找到。請設定 YOUTUBE_UPLOADER_PATH 環境變數或在 config.json 中配置。")
        return False
    
    # 確保授權檔案存在
    try:
        _ensure_file_from_env("client_secrets.json", "YT_CLIENT_SECRETS")
        _ensure_file_from_env("request.token", "YT_REQUEST")
    except FileNotFoundError as e:
        logging.error(f"無法繼續上傳，因為缺少授權檔案: {e}")
        return False

    command = [uploader_path, "-filename", video_path, "-metaJSON", meta_path]
    try:
        logging.info(f"正在上傳 '{video_path}'...")
        process = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8')
        logging.info(f"成功上傳: {video_path}")
        logging.debug(f"Uploader output: {process.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"上傳 '{video_path}' 失敗。Uploader 執行出錯。")
        logging.error(f"Return code: {e.returncode}")
        logging.error(f"STDOUT: {e.stdout}")
        logging.error(f"STDERR: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"上傳期間發生未預期的錯誤: {e}")
        return False

def _ensure_file_from_env(file_path: str, env_var: str):
    """
    輔助函式，確保一個檔案存在。如果檔案不存在，則嘗試從環境變數創建它。
    如果檔案和環境變數都缺失，則拋出 FileNotFoundError。
    """
    if not os.path.exists(file_path):
        logging.info(f"'{file_path}' 不存在。正在嘗試從環境變數 '{env_var}' 創建。")
        file_data = os.getenv(env_var)
        
        if file_data:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_data)
                logging.info(f"成功從環境變數創建了 '{file_path}'。")
            except IOError as e:
                logging.error(f"寫入 '{file_path}' 失敗: {e}")
                raise
        else:
            message = f"致命錯誤: '{file_path}' 不存在且 '{env_var}' 環境變數也未設定。無法繼續。"
            logging.critical(message)
            raise FileNotFoundError(message)

def run_upload_task(cleanup_threshold_gb=0.8):
    """上傳影片的核心任務，包含清理邏輯。"""
    
    # --- 磁碟空間清理檢查 ---
    downloads_folder = "downloads"
    folder_size_gb = get_folder_size(downloads_folder)
    logging.info(f"'{downloads_folder}' 資料夾目前大小: {folder_size_gb:.2f} GB。清理閾值為: {cleanup_threshold_gb} GB。")

    if folder_size_gb > cleanup_threshold_gb:
        logging.warning(f"資料夾大小已超過閾值。觸發已上傳檔案的清理程序...")
        cleanup_uploaded_files(downloads_folder)
    else:
        logging.info("資料夾大小在限制範圍內，無需清理。")

    # --- 執行上傳 ---
    config = load_config()
    videos_to_upload = get_all_videos_to_upload()
    if not videos_to_upload:
        logging.info("資料庫中沒有新的影片需要上傳。")
        return
    logging.info(f"發現 {len(videos_to_upload)} 部影片待上傳。")

    is_publish_now = config.get("is_publish_now")
    publish_start_from = config.get("publish_start_from")
    time_increment_hours = config.get("time_increment_hours")

    first_publish_time = datetime.now(timezone.utc) + (timedelta(minutes=5) if is_publish_now else timedelta(hours=publish_start_from))

    for i, video_data in enumerate(videos_to_upload):
        video_id = video_data['video_id']
        video_path = video_data['local_path']
        if not os.path.exists(video_path):
            logging.warning(f"跳過影片 ID {video_id}，因為檔案不存在: {video_path}")
            continue
        
        logging.info(f"--- 正在處理第 {i+1}/{len(videos_to_upload)} 部影片: {os.path.basename(video_path)} ---")
        
        publish_time = first_publish_time + timedelta(hours=i * time_increment_hours)
        publish_time_iso = publish_time.isoformat()
        
        video_filename = os.path.basename(video_path)
        meta_filename = f"{os.path.splitext(video_filename)[0]}.json"
        meta_path = os.path.join(os.path.dirname(video_path), meta_filename)
        
        metadata = generate_metadata(video_data['caption'], video_filename, publish_time_iso, config)
        if not metadata:
            logging.warning(f"因元數據生成失敗，跳過影片 '{video_id}'。")
            continue
        
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        
        if upload_video(video_path, meta_path, config):
            try:
                update_upload_status(video_id, status=True)
            except Exception as e:
                logging.critical(f"致命錯誤: 更新影片 {video_id} 的資料庫狀態失敗: {e}")
                break 
        else:
            logging.error(f"影片 '{video_id}' 上傳失敗。中止本次上傳任務。")
            break
        time.sleep(5)
    logging.info("所有上傳任務已完成。")

def main():
    """CLI 進入點，解析參數並執行上傳任務。"""
    setup_logging()
    
    parser = argparse.ArgumentParser(description="將 'downloads' 資料夾中的影片上傳到 YouTube。")
    parser.add_argument(
        '-du', '--deleteupload',
        type=float,
        default=0.8,
        help='設定清理閾值 (GB)。當 downloads 資料夾大小超過此值時，將刪除已上傳的影片。預設值為 0.8 GB。'
    )
    args = parser.parse_args()

    init_db()
    run_upload_task(cleanup_threshold_gb=args.deleteupload)

if __name__ == "__main__":
    main()