import os
import time
import json
import zstandard
from datetime import datetime
from dotenv import load_dotenv
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def safe_get(data, keys, default=None):
    """安全地從巢狀字典中獲取值。"""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
    return data if data is not None else default

def scrape_videos(url: str, scroll_count: int = 3) -> list[dict]:
    """
    [生產模式 V4 - 精準解析版] 透過 Cookie 認證，攔截並精準解析 API 回應，提取完整的影片元數據。
    """
    load_dotenv()
    session_cookie = os.getenv("THREADS_SESSION_COOKIE")
    if not session_cookie:
        print("錯誤：請在 .env 檔案中設定 THREADS_SESSION_COOKIE。")
        return []

    print("正在啟動爬蟲 (V4 最終版引擎)...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    scraped_videos = []
    processed_post_ids = set()

    try:
        print("正在注入 Cookie...")
        driver.get("https://www.threads.net/")
        driver.add_cookie({'name': 'sessionid', 'value': session_cookie})
        driver.refresh()
        time.sleep(5)

        print(f"\n正在導航至目標頁面: {url}")
        driver.get(url)
        print("等待頁面載入...")
        time.sleep(5)

        print(f"開始滾動頁面 ({scroll_count} 次)...")
        for i in range(scroll_count):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"  滾動 {i + 1}/{scroll_count}...")
            time.sleep(4) # 延長等待時間以確保 API 請求完成

        print("\n--- 分析開始：解析所有捕獲的 GraphQL 數據包 ---")
        
        target_requests = [r for r in driver.requests if 'graphql/query' in r.url and r.response and 'zstd' in r.response.headers.get('Content-Encoding', '') and len(r.response.body) > 1000]

        if not target_requests:
            raise Exception("未能捕獲到任何包含貼文數據的 GraphQL API 請求。" )

        print(f"成功鎖定 {len(target_requests)} 個目標 API 請求。開始解壓縮與解析...")
        
        all_posts = []
        dctx = zstandard.ZstdDecompressor()

        for request in target_requests:
            try:
                decompressed_body = dctx.decompress(request.response.body)
                data = json.loads(decompressed_body.decode('utf-8'))
                
                # 根據真實結構，直接定位到 `edges`
                edges = safe_get(data, ('data', 'feedData', 'edges'))
                if not edges:
                    # 兼容另一種可能的結構
                    if isinstance(data.get('data'), dict):
                         for key, value in data['data'].items():
                            if isinstance(value, dict):
                                inner_edges = value.get('edges')
                                if isinstance(inner_edges, list):
                                    edges = inner_edges
                                    break

                if edges:
                    all_posts.extend(edges)

            except Exception as e:
                print(f"    處理數據包時發生錯誤: {e}")
                continue

        print(f"\n解析到 {len(all_posts)} 個總貼文項目。開始篩選影片...")

        for edge in all_posts:
            thread_items = safe_get(edge, ('node', 'text_post_app_thread', 'thread_items'), [])
            for item in thread_items:
                post = item.get('post')
                if not post:
                    continue

                # 處理單一影片和輪播影片
                media_items = [post] + (post.get('carousel_media') or [])
                for media in media_items:
                    if not media.get('video_versions'):
                        continue

                    post_id = media.get('pk')
                    if not post_id or post_id in processed_post_ids:
                        continue

                    video_data = {}
                    video_data['post_id'] = post_id
                    video_data['post_url'] = f"https://www.threads.net/t/{post.get('code')}" # 使用主 post 的 code
                    video_data['video_url'] = media['video_versions'][0]['url']
                    video_data['author'] = post.get('user', {}).get('username')
                    video_data['caption'] = post.get('caption', {}).get('text') if post.get('caption') else ""
                    video_data['like_count'] = post.get('like_count', 0)
                    video_data['comment_count'] = safe_get(post, ('text_post_app_info', 'direct_reply_count'), 0)
                    video_data['timestamp'] = datetime.fromtimestamp(post.get('taken_at', 0)).strftime('%Y-%m-%d %H:%M:%S')

                    scraped_videos.append(video_data)
                    processed_post_ids.add(post_id)
                    print(f"  [篩選到影片] 作者: {video_data['author']}, Post ID: {video_data['post_id']}")

    except Exception as e:
        print(f"爬取過程中發生錯誤: {e}")
    finally:
        print("關閉瀏覽器...")
        driver.quit()

    print(f"\n本次運行共篩選出 {len(scraped_videos)} 個影片。")
    return scraped_videos
