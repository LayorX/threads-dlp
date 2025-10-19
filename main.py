# main.py

import argparse
import os
import re
from urllib.parse import urlparse, quote

from modules.downloader import download_video
from modules.scraper import scrape_videos
from modules.database import init_db, post_exists, add_video_entry

def sanitize_filename(filename: str) -> str:
    """清理檔名，移除在 Windows 中不合法的字元並限制長度。"""
    # 移除 Windows 檔名中的非法字元: \ / : * ? " < > |
    sanitized = re.sub(r'[\\/:*?"<>|]', '-', filename)
    # 移除換行符和回車符
    sanitized = re.sub(r'[\r\n]', ' ', sanitized)
    # 移除其他所有不可印出的控制字元
    sanitized = "".join(c for c in sanitized if c.isprintable())
    # 將多個空格合併為一個
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    # 限制總長度以防萬一 (Windows 路徑限制約為 260)
    return sanitized[:180]

def main():
    """主函式，用於解析命令列參數並啟動影片抓取與下載流程。"""
    init_db() # 確保資料庫已初始化

    parser = argparse.ArgumentParser(
        description="從 Threads 下載影片。支援指定用戶、搜尋關鍵字或預設首頁三種模式。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "target",
        nargs='?',
        default=None,
        help="(模式一：指定用戶) 要處理的 Threads 使用者名稱 (例如 zuck)。"
    )
    parser.add_argument(
        "--search",
        type=str,
        help="(模式二：搜尋關鍵字) 在 Threads 上搜尋指定的關鍵字。"
    )
    parser.add_argument(
        "--scroll",
        type=int,
        default=3,
        help="模擬頁面向下滾動的次數，以載入更多內容。預設為 3。"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="downloads",
        help="指定儲存影片的資料夾路徑。預設為 \"downloads\"."
    )

    args = parser.parse_args()

    # --- 決定目標 URL ---
    if args.search:
        if args.target:
            print("錯誤：請不要同時指定 `target` 和 `--search`。請擇一使用。\n")
            return
        # URL 編碼搜尋詞，以處理空格等特殊字元
        encoded_query = quote(args.search)
        target_url = f"https://www.threads.net/search?q={encoded_query}"
        print(f"模式：搜尋關鍵字 \"{args.search}\"")
    elif args.target:
        target_url = args.target
        if not urlparse(target_url).scheme:
            target_url = f"https://www.threads.net/@{args.target}"
        print(f"模式：指定用戶 @{args.target}")
    else:
        target_url = "https://www.threads.net/"
        print("模式：預設首頁推薦內容")

    print(f"目標 URL: {target_url}")

    # --- 執行爬取 ---
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    print(f"影片將儲存至: {os.path.abspath(output_dir)}")
    
    scraped_videos = scrape_videos(target_url, scroll_count=args.scroll)

    if not scraped_videos:
        print("\n--- 未抓取到任何新的影片。 ---")
        return

    # --- 下載與紀錄流程 ---
    new_videos_to_download = []
    for video in scraped_videos:
        if not post_exists(video['post_id']):
            new_videos_to_download.append(video)
        else:
            print(f"[跳過] 貼文 {video['post_id']} 已存在於資料庫中，無需重複下載。")

    if not new_videos_to_download:
        print("\n--- 所有抓取到的影片都已存在，無需下載。 ---")
        return

    print(f"\n--- 共抓取到 {len(scraped_videos)} 個影片，其中 {len(new_videos_to_download)} 個是新的，準備下載 ---")
    
    for i, video_data in enumerate(new_videos_to_download):
        print(f"\n正在下載影片 {i+1}/{len(new_videos_to_download)} (Post ID: {video_data['post_id']}) ")
        # 安全地印出內容，避免編碼錯誤
        safe_caption = str(video_data['caption']).encode('utf-8', 'ignore').decode('utf-8')
        print(f"作者: {video_data['author']}, 內容: {safe_caption[:50]}...")
        
        # --- 生成並淨化檔名 ---
        base_filename = f"{video_data['author']} - {video_data['caption']} [{video_data['post_id']}].mp4"
        safe_filename = sanitize_filename(base_filename)
        full_path = os.path.join(output_dir, safe_filename)

        # 執行下載，傳入完整的儲存路徑
        success = download_video(video_data['video_url'], full_path)
        
        if success:
            # 下載成功後，將包含儲存路徑的完整資訊寫入資料庫
            video_data['local_path'] = full_path
            add_video_entry(video_data)
        else:
            print(f"[錯誤] 影片 {video_data['post_id']} 下載失敗，跳過紀錄。")

    print("\n--- 所有新影片下載任務完成！ ---")

if __name__ == "__main__":
    main()