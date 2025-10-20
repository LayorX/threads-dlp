# main.py

import argparse
import os
import re
import subprocess
from urllib.parse import urlparse, quote

from modules.downloader import download_video
from modules.scraper import scrape_videos
from modules.database import init_db, get_all_existing_post_ids, add_video_entry

def sanitize_filename(filename: str) -> str:
    sanitized = re.sub(r'[\\/:*?"<>|]', '-', filename)
    sanitized = re.sub(r'[\r\n]', ' ', sanitized)
    sanitized = "".join(c for c in sanitized if c.isprintable())
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    return sanitized[:180]

def main():
    """主函式，採用批次讀取、逐筆寫入的模式。"""
    parser = argparse.ArgumentParser(description="從 Threads 下載影片。")
    parser.add_argument("target", nargs='?', default=None)
    parser.add_argument("--search", type=str)
    parser.add_argument("--scroll", type=int, default=3)
    parser.add_argument("--output", type=str, default="downloads")
    parser.add_argument("--upload", action='store_true')
    args = parser.parse_args()

    # --- 批次讀取 ---
    init_db() # 確保資料庫和資料表存在
    existing_ids = get_all_existing_post_ids()
    print(f"[DB] 資料庫中已存在 {len(existing_ids)} 筆紀錄。")
    # --- 資料庫連線在此已關閉 ---

    if args.search:
        encoded_query = quote(args.search)
        target_url = f"https://www.threads.net/search?q={encoded_query}"
        print(f"模式：搜尋關鍵字 \"{args.search}\"")
    elif args.target:
        target_url = f"https://www.threads.net/@{args.target}"
        print(f"模式：指定用戶 @{args.target}")
    else:
        target_url = "https://www.threads.net/"
        print("模式：預設首頁推薦內容")

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    
    scraped_videos = scrape_videos(target_url, scroll_count=args.scroll)

    if not scraped_videos:
        print("\n--- 未抓取到任何新的影片。 ---")
    else:
        new_videos_downloaded = 0
        for video_data in scraped_videos:
            post_id = video_data['post_id']
            if post_id in existing_ids:
                print(f"[跳過] 貼文 {post_id} 已存在於資料庫中。")
                continue

            safe_caption = str(video_data['caption']).encode('utf-8', 'ignore').decode('utf-8')
            print(f"\n[新增任務] 正在處理 Post ID: {post_id}, 作者: {video_data['author']}, 內容: {safe_caption[:50]}...")
            
            # --- 修正檔名生成邏輯 ---
            author = video_data.get('author', 'unknown')[:20]
            caption_part = video_data.get('caption', '')[:10]
            likes = video_data.get('like_count', 0)
            base_filename = f"{author} - {caption_part} - [{likes}]likes.mp4"
            safe_filename = sanitize_filename(base_filename)
            full_path = os.path.join(output_dir, safe_filename)

            # --- 執行子進程時，無資料庫連線 ---
            success = download_video(video_data['video_url'], full_path)
            
            if success:
                video_data['local_path'] = full_path
                try:
                    # --- 逐筆寫入 ---
                    add_video_entry(video_data)
                    new_videos_downloaded += 1
                except Exception as e:
                    print(f"[致命錯誤] 寫入資料庫失敗: {e}，中止執行。")
                    break # 如果資料庫寫入失敗，則停止後續所有操作
            else:
                print(f"[錯誤] 影片 {post_id} 下載失敗，跳過紀錄。")
        print(f"\n--- 本次共下載了 {new_videos_downloaded} 個新影片 ---")

    if args.upload:
        print("\n--- 所有下載任務已完成，即將啟動上傳器... ---")
        try:
            subprocess.run(["uv", "run", "python", "uploader.py"], check=True)
        except Exception as e:
            print(f"[錯誤] uploader.py 執行失敗: {e}")

if __name__ == "__main__":
    main()
