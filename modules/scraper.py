import os
import time
from dotenv import load_dotenv
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

def scrape_videos(url: str, scroll_count: int = 3) -> list[str]:
    """
    使用 Cookie 進行認證，並透過監聽網路請求來爬取影片連結。

    Args:
        url: 要爬取的 Threads 使用者頁面 URL。
        scroll_count: 模擬向下滾動的次數，以觸發影片載入。

    Returns:
        一個包含所有不重複影片來源 URL 的清單。
    """
    load_dotenv() # 載入 .env 檔案中的環境變數

    session_cookie = os.getenv("THREADS_SESSION_COOKIE")
    if not session_cookie:
        print("錯誤：請在 .env 檔案中設定 THREADS_SESSION_COOKIE。")
        print("詳細教學請參考我們的對話紀錄。")
        return []

    print("正在設定具備網路監聽功能的瀏覽器...")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    video_urls = set()

    try:
        print("正在注入 Cookie 以進行認證...")
        # 必須先訪問一次該域名，才能設定 Cookie
        driver.get("https://www.threads.net/")
        driver.add_cookie({
            'name': 'sessionid', # Threads/Instagram 使用的 session cookie 名稱
            'value': session_cookie
        })
        print("Cookie 注入成功，刷新頁面以完成登入。")
        driver.refresh()
        time.sleep(5) # 等待登入狀態生效

        print(f"\n登入完成，正在導航至目標頁面: {url}")
        driver.get(url)

        print("等待頁面初步載入...")
        time.sleep(5)

        print(f"開始模擬滾動頁面 ({scroll_count} 次) 以觸發網路請求...")
        for i in range(scroll_count):
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            print(f"  滾動 {i + 1}/{scroll_count}...")
            time.sleep(3)

        print("\n正在分析截獲的網路請求 (Content-Type 模式)...")
        for request in driver.requests:
            if request.response and request.response.headers:
                content_type = request.response.headers.get('Content-Type', '')
                if 'video/' in content_type:
                    print(f"  [捕獲影片] -> 類型: {content_type}, URL: {request.url}")
                    video_urls.add(request.url)

        if not video_urls:
            print("警告：在網路請求中未找到 Content-Type 為 'video/' 的資源。")
        
        print(f"\n成功提取到 {len(video_urls)} 個不重複的影片連結。")

    except Exception as e:
        print(f"爬取過程中發生錯誤: {e}")
    finally:
        print("關閉瀏覽器...")
        driver.quit()

    return list(video_urls)