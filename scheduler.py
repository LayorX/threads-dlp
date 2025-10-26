import schedule
import time
import logging
from datetime import datetime
import os

# Import the refactored task functions
from main import run_download_task
from uploader import run_upload_task
from modules.database import get_videos_to_upload_count, init_db

def setup_logging():
    """設定一個冪等的日誌記錄器，避免在匯入時重複設定。"""
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(log_formatter)
        root_logger.addHandler(console_handler)

def download_job():
    """
    根據環境變數執行下載影片的排程任務。
    """
    logging.info("=== 開始排程下載任務 ===")
    
    # 從環境變數讀取參數，如果未設定則使用預設值
    target_user = os.getenv("THREADS_TARGET_USER", "nasa") # 範例: nasa
    scrolls = int(os.getenv("THREADS_SCROLL_COUNT", 5))
    
    logging.info(f"目標使用者: @{target_user}，滾動次數: {scrolls}。")
    
    try:
        run_download_task(
            target_username=target_user,
            scroll_count=scrolls,
            log_level=logging.INFO
        )
    except Exception as e:
        logging.error(f"下載任務執行期間發生錯誤: {e}", exc_info=True)
        
    logging.info("=== 排程下載任務結束 ===")

def upload_job():
    """
    檢查影片數量並在滿足條件時上傳的排程任務。
    """
    logging.info("=== 開始每日上傳檢查任務 ===")
    try:
        init_db()
        video_count = get_videos_to_upload_count()
        
        logging.info(f"資料庫中有 {video_count} 部影片等待上傳。")
        
        upload_threshold = int(os.getenv("UPLOAD_THRESHOLD", 5))
        
        if video_count >= upload_threshold:
            logging.info(f"影片數量 ({video_count}) 已達到門檻 (>= {upload_threshold})，開始執行上傳程序。")
            run_upload_task()
        else:
            logging.info("影片數量未達到門檻，本次跳過上傳。")
    except Exception as e:
        logging.error(f"上傳任務執行期間發生錯誤: {e}", exc_info=True)
        
    logging.info("=== 每日上傳檢查任務結束 ===")

def main():
    """
    排程器主函式。
    """
    setup_logging()
    logging.info("排程器已啟動，正在初始化資料庫...")
    init_db()

    # --- 設定排程任務 ---
    # 每 4 小時執行一次下載任務
    schedule.every(4).hours.do(download_job)
    logging.info("下載任務已排程，每 4 小時執行一次。")
    
    # 每日在指定時間 (UTC) 執行上傳檢查
    upload_time_str = os.getenv("UPLOAD_TIME_UTC", "01:00")
    schedule.every().day.at(upload_time_str).do(upload_job)
    logging.info(f"每日上傳檢查任務已排程，將在每天 {upload_time_str} (UTC) 執行。")

    logging.info(f"初始排程設定完畢。目前時間: {datetime.now()}")
    
    # 為了快速驗證，在啟動時立即執行一次下載任務
    logging.info("正在執行啟動時的首次下載任務...")
    download_job()
    
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    main()
