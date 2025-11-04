import os
import time
import json
import zstandard
import logging
from datetime import datetime
from dotenv import load_dotenv
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# 匯入新功能所需的模組
from modules.threads_client import like_post, get_like_tokens
from modules.database import add_liked_post

def safe_get(data, keys, default=None):
    """安全地從巢狀字典中獲取值。"""
    for key in keys:
        if not isinstance(data, dict):
            return default
        data = data.get(key)
    return data if data is not None else default

def scrape_videos(url: str, scroll_count: int, like_threshold: int, download_threshold: int, liked_post_ids: set, continuous: bool = False) -> list[dict]:
    """
    [生產模式 V5 - API 模擬版]
    遍歷 GraphQL API 數據，當讚數達標時，呼叫 like_post 函式模擬按讚請求。
    """
    output_filename = "last_run_graphql_output.json"
    if os.path.exists(output_filename):
        try:
            os.remove(output_filename)
        except OSError as e:
            logging.warning(f"[Scraper] 刪除舊的暫存檔失敗: {e}")

    load_dotenv()
    session_cookie = os.getenv("THREADS_SESSION_COOKIE")
    if not session_cookie:
        logging.error("錯誤：請在 .env 檔案中設定 THREADS_SESSION_COOKIE。")
        return []

    logging.info("正在啟動爬蟲 (V5 API 模擬引擎)...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    scraped_videos = []
    processed_post_ids = set() # 用於在單次運行中避免重複解析同一個 post
    
    # --- V5 新增：權杖儲存 ---
    csrf_token = None
    lsd_token = None
    can_like_posts = False

    try:
        logging.info("正在注入 Cookie...")
        driver.get("https://www.threads.net/")
        driver.add_cookie({'name': 'sessionid', 'value': session_cookie})
        driver.refresh()
        time.sleep(5)

        # --- V5 新增：Cookie 有效性驗證 ---
        logging.info("正在驗證 Cookie 有效性...")
        page_title = driver.title.lower()
        if 'log in' in page_title or '登入' in page_title:
            error_message = "Cookie 已失效或無效，請更新您的 .env 檔案中的 THREADS_SESSION_COOKIE。"
            logging.critical(error_message)
            raise ValueError(error_message)
        logging.info("Cookie 驗證成功，帳號已登入。")
        # --- 驗證結束 ---

        # --- V5 新增：獲取按讚權杖 ---
        csrf_token, lsd_token = get_like_tokens(driver)
        if csrf_token and lsd_token:
            can_like_posts = True
        else:
            logging.warning("無法獲取按讚權杖，按讚功能將被停用。")
        # --- 權杖獲取結束 ---

        logging.info(f"\n正在導航至目標頁面: {url}")
        driver.get(url)
        logging.info("等待頁面載入...")
        time.sleep(5)

        total_scrolls = 0
        MAX_TOTAL_SCROLLS = 100

        while True:
            current_scroll_target = scroll_count if not continuous else 3
            logging.info(f"開始滾動頁面 ({current_scroll_target} 次)...")
            for i in range(current_scroll_target):
                if total_scrolls >= MAX_TOTAL_SCROLLS:
                    logging.warning("已達到最大滾動次數上限，停止滾動。")
                    break
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                total_scrolls += 1
                logging.info(f"  滾動 {total_scrolls}/{MAX_TOTAL_SCROLLS if continuous else scroll_count}...")
                time.sleep(4)
            
            if total_scrolls >= MAX_TOTAL_SCROLLS:
                break

            logging.info("\n--- 分析開始：解析所有捕獲的 GraphQL 數據包 ---")
            target_requests = [r for r in driver.requests if 'graphql/query' in r.url and r.response and 'zstd' in r.response.headers.get('Content-Encoding', '')]

            if not target_requests:
                logging.warning("未能捕獲到任何包含貼文數據的 GraphQL API 請求。")
                if continuous and len(scraped_videos) < 5:
                    continue
                else:
                    break

            all_posts = []
            dctx = zstandard.ZstdDecompressor()
            for request in target_requests:
                try:
                    data = json.loads(dctx.decompress(request.response.body).decode('utf-8'))
                    edges = safe_get(data, ('data', 'feedData', 'edges')) or safe_get(data, ('data', 'search_results', 'edges'))
                    if edges: all_posts.extend(edges)
                except Exception as e:
                    logging.error(f"處理數據包時發生錯誤: {e}")
            del driver.requests[:]

            # --- V5 新增：空數據檢查 ---
            if not all_posts:
                logging.warning("警告：未能從 API 回應中解析出任何貼文。目標頁面可能沒有內容，或 API 結構已變更。")
            # --- 檢查結束 ---

            logging.info(f"解析到 {len(all_posts)} 個總貼文項目。開始根據門檻進行互動與篩選...")
            for edge in all_posts:
                thread_items = safe_get(edge, ('node', 'text_post_app_thread', 'thread_items'), [])
                for item in thread_items:
                    post = item.get('post')
                    if not post: continue

                    # --- 黑盒子紀錄器 V1 ---
                    try:
                        log_message = "\n--- 發現貼文 ---\n"
                        author = safe_get(post, ('user', 'username'), '未知作者')
                        post_id = post.get('pk', '未知ID')
                        like_count = post.get('like_count', 0)
                        caption = safe_get(post, ('caption', 'text'), "").replace('\n', ' ')
                        
                        log_message += f"  作者: {author}\n"
                        log_message += f"  ID: {post_id}\n"
                        log_message += f"  讚數: {like_count}\n"
                        log_message += f"  內文: {caption[:80]}...\n"

                        # 檢查影片
                        video_url = "無"
                        if post.get('video_versions'):
                            video_url = post['video_versions'][0]['url']
                        elif post.get('carousel_media'):
                            for media in post.get('carousel_media', []):
                                if media.get('video_versions'):
                                    video_url = media['video_versions'][0]['url']
                                    break # 只記錄第一個找到的影片
                        
                        log_message += f"  影片: {'是' if video_url != '無' else '否'}\n"
                        log_message += "-----------------\n"

                        with open("scraped_posts_audit.log", "a", encoding="utf-8") as f:
                            f.write(log_message)
                    except Exception as e:
                        with open("scraped_posts_audit.log", "a", encoding="utf-8") as f:
                            f.write(f"--- 紀錄貼文時發生錯誤: {e} ---\n")
                    # --- 黑盒子紀錄器結束 ---

                    main_post_id = post.get('pk')
                    if not main_post_id or main_post_id in processed_post_ids: continue

                    like_count = post.get('like_count', 0)

                    # --- V5 按讚決策邏輯 ---
                    if can_like_posts and like_threshold != -1 and like_count >= like_threshold:
                        if main_post_id not in liked_post_ids:
                            logging.info(f"[互動] 貼文 {main_post_id} 讚數 ({like_count}) 已達門檻 ({like_threshold})，準備呼叫 API 按讚...")
                            if like_post(driver, main_post_id, csrf_token, lsd_token):
                                post_url = f"https://www.threads.net/t/{post.get('code')}"
                                add_liked_post(main_post_id, post_url)
                                liked_post_ids.add(main_post_id)
                        else:
                            logging.debug(f"[互動] 貼文 {main_post_id} 已存在於按讚紀錄中，跳過。")

                    # --- 下載篩選邏輯 (V4.1 - 修正版) ---
                    # 檢查貼文本身或輪播中是否包含任何影片
                    has_video_in_post = post.get('video_versions') or any(media.get('video_versions') for media in post.get('carousel_media', []) or [])


                    if like_count >= download_threshold and has_video_in_post:
                        logging.info(f"[篩選] Post ID: {main_post_id} 讚數 ({like_count}) 已達下載門檻 ({download_threshold})，蒐集影片中...")
                        all_media = [post] + (post.get('carousel_media') or [])
                        for video_index, media in enumerate(all_media, 1):
                            if not media.get('video_versions'): continue
                            video_data = {
                                'post_id': main_post_id,
                                'video_index': video_index,
                                'post_url': f"https://www.threads.net/t/{post.get('code')}",
                                'video_url': media['video_versions'][0]['url'],
                                'author': post.get('user', {}).get('username'),
                                'caption': safe_get(post, ('caption', 'text'), ""),
                                'like_count': like_count,
                                'comment_count': safe_get(post, ('text_post_app_info', 'direct_reply_count'), 0),
                                'timestamp': datetime.fromtimestamp(post.get('taken_at', 0)).strftime('%Y-%m-%d %H:%M:%S')
                            }
                            video_unique_id = f"{main_post_id}-{video_index}"
                            if not any(v['post_id'] == main_post_id and v['video_index'] == video_index for v in scraped_videos):
                                scraped_videos.append(video_data)
                                logging.info(f"  [+] 已將影片加入待下載清單: {video_unique_id}")
                    
                    processed_post_ids.add(main_post_id)

            # --- 檢查是否結束持續模式 ---
            if continuous and len(scraped_videos) < 5:
                logging.info(f"目前蒐集到 {len(scraped_videos)}/5 個影片，繼續滾動...")
            else:
                break

    except Exception as e:
        logging.error(f"爬取過程中發生錯誤: {e}")
    finally:
        logging.info("關閉瀏覽器...")
        driver.quit()

    logging.info(f"\n本次運行共篩選出 {len(scraped_videos)} 個符合條件的影片。")
    return scraped_videos