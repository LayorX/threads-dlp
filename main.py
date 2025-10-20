# main.py

import logging
import argparse
import os
import re
import subprocess
import json
from collections import defaultdict
from urllib.parse import quote

from modules.downloader import download_video
from modules.scraper import scrape_videos
from modules.database import init_db, get_all_existing_video_ids, add_video_entry, get_all_liked_post_ids

__version__ = "1.0.0"

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
    
    # 為新功能提供預設值
    config.setdefault('like_threshold', -1)
    config.setdefault('download_threshold', 1000)
    return config

def main():
    """主函式，負責指揮、設定載入、與最終的下載協調。"""
    parser = argparse.ArgumentParser(description="從 Threads 下載影片，並可選擇性地進行智慧按讚與篩選。")
    
    # --- 基本參數 ---
    parser.add_argument("-t", "--target", nargs='?', default=None, help="目標用戶名 (不需加@)")
    parser.add_argument("-s", "--search", type=str, help="要搜尋的關鍵字")
    parser.add_argument("-r", "--scroll", type=int, default=3, help="頁面滾動次數")
    parser.add_argument("--output", type=str, default="downloads", help="影片儲存的資料夾")
    parser.add_argument("-u", "--upload", action='store_true', help="下載完成後，自動執行上傳器")
    
    # --- 智慧互動參數 ---
    parser.add_argument("--like-above", type=int, default=None, help="覆寫設定檔，當讚數 >= N 時按讚")
    parser.add_argument("--download-above", type=int, default=None, help="覆寫設定檔，當讚數 >= N 時下載")
    parser.add_argument("-c", "--continuous", action='store_true', help="持續滾動模式，直到找到至少5個符合條件的影片")

    # --- 元資訊與偵錯參數 ---
    parser.add_argument("-d", "--debug", action='store_true', help="啟用詳細日誌輸出 (INFO 級別)")
    parser.add_argument("-v", "--version", action='version', version=f'%(prog)s {__version__}', help="顯示程式版本號")

    args = parser.parse_args()

    # --- 根據參數設定日誌 --- 
    log_level = logging.INFO if args.debug else logging.WARNING
    logging.basicConfig(level=log_level, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    config = load_config()

    # --- 決定最終的門檻值 (命令列優先於設定檔) ---
    like_threshold = args.like_above if args.like_above is not None else config['like_threshold']
    download_threshold = args.download_above if args.download_above is not None else config['download_threshold']

    # --- 批次讀取初始狀態 ---
    init_db() # 確保所有資料表存在
    existing_video_ids = get_all_existing_video_ids()
    liked_post_ids = get_all_liked_post_ids()
    print(f"[DB] 資料庫中已存在 {len(existing_video_ids)} 筆影片紀錄，{len(liked_post_ids)} 筆按讚紀錄。")
    
    if args.search:
        target_url = f"https://www.threads.net/search?q={quote(args.search)}"
        print(f"模式：搜尋關鍵字 \"{args.search}\"")
    elif args.target:
        target_url = f"https://www.threads.net/@{args.target}"
        print(f"模式：指定用戶 @{args.target}")
    else:
        target_url = "https://www.threads.net/"
        print("模式：預設首頁推薦內容")

    print(f"[設定] 按讚門檻: {like_threshold if like_threshold != -1 else '停用'}, 下載門檻: {download_threshold}")

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    # --- 核心任務委派給 scraper ---
    scraped_videos = scrape_videos(
        url=target_url, 
        scroll_count=args.scroll,
        like_threshold=like_threshold,
        download_threshold=download_threshold,
        liked_post_ids=liked_post_ids,
        continuous=args.continuous
    )

    if not scraped_videos:
        print("\n--- 未抓取到任何符合下載條件的新影片。 ---")
    else:
        print(f"\n--- 篩選完成，共 {len(scraped_videos)} 個影片待下載 ---")
        # --- 按 post_id 分組，以便處理多影片貼文 ---
        videos_by_post = defaultdict(list)
        for video in scraped_videos:
            # 再次檢查，以防萬一在同一次運行中 scraper 傳回了重複的項目
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
                print(f"\n[下載任務] 正在處理影片 ID: {video_id}, 作者: {video_data['author']}, 內容: {safe_caption[:50]}...")
                
                # --- 智慧檔名生成邏輯 ---
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
                        print(f"[致命錯誤] 寫入資料庫失敗: {e}，中止執行。")
                        break
                else:
                    print(f"[錯誤] 影片 {video_id} 下載失敗，跳過紀錄。")
            else: 
                continue
            break

        print(f"\n--- 本次共下載了 {new_videos_downloaded} 個新影片 ---")

    if args.upload:
        print("\n--- 所有下載任務已完成，即將啟動上傳器... ---")
        try:
            subprocess.run(["uv", "run", "python", "uploader.py"], check=True)
        except Exception as e:
            print(f"[錯誤] uploader.py 執行失敗: {e}")

if __name__ == "__main__":
    main()
