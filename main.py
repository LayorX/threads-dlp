# main.py

import logging
import argparse
import os
import re
import subprocess
import json
from collections import defaultdict
from urllib.parse import quote
import sys

from modules.downloader import download_video
from modules.scraper import scrape_videos
from modules.database import init_db, get_all_existing_video_ids, add_video_entry, get_all_liked_post_ids

__version__ = "1.0.0"

def load_language_strings(language='zh-TW') -> dict:
    """從 languages.json 載入指定語言的字串。"""
    try:
        with open("languages.json", 'r', encoding='utf-8') as f:
            all_strings = json.load(f)
            # 返回 main 模組專用的字串，如果不存在則返回空字典
            return all_strings.get(language, {}).get('main', {})
    except (FileNotFoundError, json.JSONDecodeError):
        logging.error("語言檔案 languages.json 遺失或格式錯誤，將使用預設的繁體中文。")
        return {}

def sanitize_filename(filename: str) -> str:
    """清理並淨化檔名，移除無效字元和多餘的空格。"""
    sanitized = re.sub(r'[\\/:*?"<>|]', '-', filename)
    sanitized = re.sub(r'[\r\n]', ' ', sanitized)
    sanitized = "".join(c for c in sanitized if c.isprintable())
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    return sanitized[:180] # 限制檔名長度以避免系統問題

def load_config() -> dict:
    """載入設定檔，並為新功能提供預設值。"""
    try:
        with open("config.json", 'r', encoding='utf-8') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        config = {}
    
    config.setdefault('like_threshold', -1)
    config.setdefault('download_threshold', 1000)
    return config

def run_download_task(
    target_username: str = None,
    search_query: str = None,
    scroll_count: int = 3,
    output_dir: str = "downloads",
    like_threshold_override: int = None,
    download_threshold_override: int = None,
    continuous_mode: bool = False,
    log_level: int = logging.WARNING,
    do_upload: bool = False,
    cleanup_threshold: float = 0.8,
    num_videos_to_upload: int = None,
    language: str = 'zh-TW'
):
    """
    核心下載任務邏輯。
    此函式被設計為可由外部腳本匯入和呼叫。
    """
    lang_strings = load_language_strings(language)

    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    # 特別將吵雜的函式庫的日誌等級也設定為 WARNING
    if log_level != logging.DEBUG :
        logging.getLogger('seleniumwire').setLevel(logging.WARNING)
        logging.getLogger('webdriver_manager').setLevel(logging.WARNING)
    config = load_config()

    like_threshold = like_threshold_override if like_threshold_override is not None else config['like_threshold']
    download_threshold = download_threshold_override if download_threshold_override is not None else config['download_threshold']

    # --- 啟動時顯示所有重要參數 ---
    logging.info(lang_strings.get('task_start', "==================== 任務啟動 ===================="))
    logging.info( f"→→→ Version: {__version__} ←←←")
    if search_query:
        logging.info(lang_strings.get('mode_search', " [模式] 搜尋關鍵字: \"{query}\"").format(query=search_query))
        target_url = f"https://www.threads.net/search?q={quote(search_query)}"
    elif target_username:
        logging.info(lang_strings.get('mode_user', " [模式] 指定用戶: @{username}").format(username=target_username))
        target_url = f"https://www.threads.net/@{target_username}"
    else:
        logging.info(lang_strings.get('mode_home', " [模式] 預設首頁推薦內容"))
        target_url = "https://www.threads.net/"

    logging.info(lang_strings.get('like_threshold', " [設定] 按讚門檻: {threshold}").format(threshold=like_threshold if like_threshold != -1 else lang_strings.get('like_disabled', '停用')))
    logging.info(lang_strings.get('download_threshold', " [設定] 下載門檻: {threshold}").format(threshold=download_threshold))
    logging.info(lang_strings.get('scroll_depth', " [設定] 爬取深度 (滾動次數): {count}").format(count=scroll_count))
    logging.info(lang_strings.get('output_dir', " [設定] 影片輸出目錄: {dir}").format(dir=output_dir))
    logging.info(lang_strings.get('auto_upload', " [設定] 下載後自動上傳: {status}").format(status=lang_strings.get('yes', '是') if do_upload else lang_strings.get('no', '否')))
    if do_upload:
        logging.info(lang_strings.get('cleanup_threshold', "   [上傳設定] 清理閾值: {threshold} GB").format(threshold=cleanup_threshold))
        logging.info(lang_strings.get('upload_limit', "   [上傳設定] 本次上傳數量上限: {limit}").format(limit=num_videos_to_upload if num_videos_to_upload is not None else lang_strings.get('unlimited', '無限制')))
    logging.info(lang_strings.get('task_end', "=================================================="))


    existing_video_ids = get_all_existing_video_ids()
    liked_post_ids = get_all_liked_post_ids()
    logging.info(lang_strings.get('db_info', "[DB] 資料庫中已存在 {videos} 筆影片紀錄，{likes} 筆按讚紀錄。").format(videos=len(existing_video_ids), likes=len(liked_post_ids)))
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        scraped_videos = scrape_videos(
            url=target_url, 
            scroll_count=scroll_count,
            like_threshold=like_threshold,
            download_threshold=download_threshold,
            liked_post_ids=liked_post_ids,
            continuous=continuous_mode,
            language=language
        )
    except ValueError as e:
        logging.error(lang_strings.get('operation_aborted', "操作中止：{error}").format(error=e))
        return

    if not scraped_videos:
        logging.info(lang_strings.get('no_new_videos', "未抓取到任何符合下載條件的新影片。"))
        return

    logging.info(lang_strings.get('scraping_complete', "篩選完成，共 {count} 個影片待下載").format(count=len(scraped_videos)))
    videos_by_post = defaultdict(list)
    for video in scraped_videos:
        video_id = f"{video.get('post_id')}-{video.get('video_index', 1)}"
        if video_id in existing_video_ids:
            continue
        videos_by_post[video['post_id']].append(video)

    new_videos_downloaded = 0
    for post_id, videos in videos_by_post.items():
        total_videos_in_post = len(videos)
        
        for video_data in videos:
            video_index = video_data.get('video_index', 1)
            video_id = f"{post_id}-{video_index}"

            safe_caption = str(video_data['caption']).encode('utf-8', 'ignore').decode('utf-8')
            logging.info(lang_strings.get('processing_video', "正在處理影片 ID: {video_id}, 作者: {author}, 內容: {caption}...").format(video_id=video_id, author=video_data['author'], caption=safe_caption[:50]))
            
            author = video_data.get('author', 'unknown')[:20]
            caption_part = video_data.get('caption', '')[:10]
            likes = video_data.get('like_count', 0)
            base_filename = f"{author} - {caption_part} - [{likes}]likes"
            safe_base_filename = sanitize_filename(base_filename)

            if total_videos_in_post > 1:
                final_filename = f"{safe_base_filename}-part{video_index}.mp4"
            else:
                final_filename = f"{safe_base_filename}.mp4"
            
            full_path = os.path.join(output_dir, final_filename)

            success = download_video(video_data['video_url'], full_path)
            
            if success:
                video_data['local_path'] = full_path
                try:
                    add_video_entry(video_data)
                    new_videos_downloaded += 1
                except Exception as e:
                    logging.critical(lang_strings.get('db_write_failed', "寫入資料庫失敗: {error}，中止執行。").format(error=e))
                    # 事務性操作：如果資料庫寫入失敗，則刪除已下載的檔案
                    logging.warning(f"由於資料庫寫入失敗，正在刪除已下載的檔案: {full_path}")
                    try:
                        os.remove(full_path)
                    except OSError as remove_error:
                        logging.error(f"刪除檔案 {full_path} 失敗: {remove_error}")
                    return # 中止執行以避免進一步錯誤
            else:
                logging.error(lang_strings.get('download_failed', "影片 {video_id} 下載失敗，跳過紀錄。").format(video_id=video_id))

    logging.info(lang_strings.get('total_downloaded', "本次共下載了 {count} 個新影片").format(count=new_videos_downloaded))

def main():
    """主函式，負責處理命令列參數並呼叫核心下載任務。"""
    parser = argparse.ArgumentParser(description="Download videos from Threads, with optional smart liking and filtering.")
    
    parser.add_argument("-l", "--language", type=str, default="zh-TW", choices=['zh-TW', 'en'], help="Set the language for log output.")
    parser.add_argument("-t", "--target", nargs='?', default=None, help="Target username (without @).")
    parser.add_argument("-s", "--search", type=str, help="Keyword to search for.")
    parser.add_argument("-r", "--scroll", type=int, default=3, help="Number of times to scroll down the page.")
    parser.add_argument("-o", "--output", type=str, default="downloads", help="Folder to save downloaded videos.")
    parser.add_argument("-u", "--upload", action='store_true', help="Automatically run uploader after download tasks.")
    parser.add_argument(
        '-du', '--deleteupload',
        type=float,
        default=0.8,
        help='(Used with --upload) Sets the cleanup threshold (GB).'
    )
    parser.add_argument(
        '-n', '--num_videos',
        type=int,
        default=None,
        help='(Used with --upload) Specifies the maximum number of videos to upload.'
    )
    
    parser.add_argument("-l^", "--like-above", type=int, default=None, help="Override config: like posts with >= N likes.")
    parser.add_argument("-d^", "--download-above", type=int, default=None, help="Override config: download posts with >= N likes.")
    parser.add_argument("-c", "--continuous", action='store_true', help="Continuous scrolling mode until at least 5 matching videos are found.")

    parser.add_argument("-d", "--debug", action='store_true', help="Enable detailed log output (INFO level).")
    parser.add_argument("-v", "--version", action='version', version=f'%(prog)s {__version__}', help="Show program version number.")

    args = parser.parse_args()

    log_level = logging.DEBUG if args.debug else logging.INFO

    lang_strings = load_language_strings(args.language)

    # --- 參數使用檢查 ---
    if (args.num_videos is not None or args.deleteupload != 0.8) and not args.upload:
        logging.critical(lang_strings.get('upload_param_warning', "錯誤：參數 '-n' 或 '-du' 必須與 '-u' (自動上傳) 參數一起使用。請修正您的指令。"))
        sys.exit(1) # 直接退出程式

    # 在執行任何任務前，先初始化資料庫
    init_db()

    # 執行核心下載任務
    run_download_task(
        target_username=args.target,
        search_query=args.search,
        scroll_count=args.scroll,
        output_dir=args.output,
        like_threshold_override=args.like_above,
        download_threshold_override=args.download_above,
        continuous_mode=args.continuous,
        log_level=log_level,
        do_upload=args.upload,
        cleanup_threshold=args.deleteupload,
        num_videos_to_upload=args.num_videos,
        language=args.language
    )

    if args.upload:
        logging.info(lang_strings.get('starting_uploader', "\n--- 所有下載任務已完成，即將啟動上傳器... ---"))
        try:
            # 匯入 uploader 模組並直接呼叫其核心任務函式
            import uploader
            uploader.run_upload_task(
                cleanup_threshold_gb=args.deleteupload,
                num_videos=args.num_videos,
                language=args.language
            )
        except ImportError:
            logging.error(lang_strings.get('uploader_import_error', "[錯誤] 無法匯入 uploader.py 模組。"))
        except Exception as e:
            logging.error(lang_strings.get('uploader_exec_failed', "[錯誤] uploader.py 執行失敗: {error}").format(error=e))

if __name__ == "__main__":
    main()
