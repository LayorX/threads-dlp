# main.py

import argparse
import os
from urllib.parse import urlparse

# 有條件地導入模組，以便將來擴充
from modules.downloader import download_video
from modules.scraper import scrape_videos

def main():
    """主函式，用於解析命令列參數並根據所選模式啟動影片抓取與下載流程。"""
    parser = argparse.ArgumentParser(
        description="從 Threads 下載影片。預設使用爬蟲模式。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "target",
        help="要處理的目標，可以是 Threads 使用者名稱 (例如 zuck) 或完整的 URL。"
    )
    parser.add_argument(
        "--mode",
        choices=['scraper', 'api'],
        default='scraper',
        help="選擇運作模式:\n" 
             "  scraper (預設): 使用 Selenium 模擬瀏覽器爬取，無需 API 金鑰。\n" 
             "  api: 使用官方 API (目前對您不可用)。"
    )
    parser.add_argument(
        "--scroll",
        type=int,
        default=3,
        help="在 'scraper' 模式下，模擬頁面向下滾動的次數，以載入更多內容。"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="downloads",
        help="指定儲存下載影片的資料夾路徑。"
    )

    args = parser.parse_args()
    video_urls = []

    # 確保輸出目錄存在
    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)
    print(f"影片將儲存至: {os.path.abspath(output_dir)}")


    if args.mode == 'scraper':
        print("\n--- 使用 Scraper 模式 ---")
        target_url = args.target
        # 檢查 target 是否為完整 URL，如果不是，則假定為使用者名稱並建構 URL
        if not urlparse(target_url).scheme:
            target_url = f"https://www.threads.net/@{args.target}"
        
        video_urls = scrape_videos(target_url, scroll_count=args.scroll)

    elif args.mode == 'api':
        print("\n--- 使用 API 模式 ---")
        print("錯誤：API 模式目前對您不可用，因為您沒有 Threads API 金鑰。")
        print("請使用預設的 'scraper' 模式。")
        # 以下為未來 API 模式的程式碼框架
        # from config import THREADS_ACCESS_TOKEN
        # from modules.threads_client import get_user_posts
        # if not THREADS_ACCESS_TOKEN:
        #     print("錯誤：請在 config.py 檔案中設定您的 THREADS_ACCESS_TOKEN。")
        #     return
        # ... (處理 API 邏輯)
        pass

    # --- 下載流程 ---
    if video_urls:
        print(f"\n--- 找到 {len(video_urls)} 個影片，準備下載 ---")
        for i, url in enumerate(video_urls):
            print(f"\n正在下載影片 {i+1}/{len(video_urls)}")
            print(f"URL: {url}")
            download_video(url, output_dir)
        print("\n--- 所有下載任務完成！ ---")
    else:
        print("\n--- 未找到任何可下載的影片。 ---")


if __name__ == "__main__":
    main()
