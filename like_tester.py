# like_tester.py

import logging
import argparse
import os
import re
import time
import json
import zstd
from dotenv import load_dotenv
from seleniumwire import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

from modules.threads_client import get_like_tokens, like_post

def main():
    """
    专用于测试按赞功能的快速验证脚本。
    """
    parser = argparse.ArgumentParser(description="对指定的 Threads 帖子 URL 执行按赞操作。")
    parser.add_argument("-u", "--url", type=str, required=True, help="要按赞的帖子的完整 URL")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    load_dotenv()
    session_cookie = os.getenv("THREADS_SESSION_COOKIE")
    if not session_cookie:
        logging.error("错误：请在 .env 檔案中设定 THREADS_SESSION_COOKIE。")
        return

    logging.info("正在启动按赞测试浏览器...")
    chrome_options = Options()
    # 为了方便观察，暂时不使用 headless 模式
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        logging.info("正在注入 Cookie...")
        driver.get("https://www.threads.net/")
        driver.add_cookie({'name': 'sessionid', 'value': session_cookie})
        driver.refresh()
        time.sleep(5)

        logging.info("Cookie 注入完成，正在验证...")
        page_title = driver.title.lower()
        if 'log in' in page_title or '登入' in page_title:
            logging.critical("Cookie 已失效或无效，测试中止。")
            return
        logging.info("Cookie 验证成功。")

        logging.info(f"正在导航至目标帖子: {args.url}")
        driver.get(args.url)
        time.sleep(5)

        with open("debug_page_source.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)

        # 从 URL 中提取 Post Code，然后从页面内容中找到真正的 Post ID (pk)
        post_code_match = re.search(r'/(?:post|t)/([^/]+)', args.url)
        if not post_code_match:
            logging.error("无法从 URL 中解析 Post Code。")
            return
        
        post_code = post_code_match.group(1)
        logging.info(f"从 URL 中解析到 Post Code: {post_code}")

        # Give the page time to load all GraphQL data
        logging.info("等待页面加载 GraphQL 数据 (10秒)...")
        time.sleep(10)

        post_id = None
        graphql_responses = []
        
        # 遍历所有捕获的请求
        for request in driver.requests:
            if 'graphql/query' in request.url:
                if request.response:
                    try:
                        body = request.response.body
                        if request.response.headers.get('Content-Encoding') == 'zstd':
                            body = zstd.decompress(body)
                        
                        data = json.loads(body.decode('utf-8'))
                        graphql_responses.append(data) # 保存解码后的JSON

                        # 在 JSON 数据中寻找 post_id
                        if 'data' in data and 'data' in data['data'] and 'posts' in data['data']['data']:
                            if len(data['data']['data']['posts']) > 0 and 'pk' in data['data']['data']['posts'][0]:
                                post_id = data['data']['data']['posts'][0]['pk']
                                logging.info(f"在其中一个 GraphQL 响应中找到了 Post ID: {post_id}")
                                break # 找到就跳出循环
                    except Exception as e:
                        logging.warning(f"解析某个 GraphQL 响应失败: {e}")

        # 将所有捕获的 GraphQL JSON 保存到文件以供调试
        with open("debug_graphql.json", "w", encoding="utf-8") as f:
            json.dump(graphql_responses, f, indent=2, ensure_ascii=False)
        logging.info(f"已将 {len(graphql_responses)} 个 GraphQL 响应保存到 debug_graphql.json")

        if not post_id:
            logging.error("在所有 GraphQL 响应中都未能找到对应的 Post ID (pk)。请检查 debug_graphql.json 文件。")
            return

        page_source = driver.page_source
        csrf_token, lsd_token = get_like_tokens(page_source)
        if not (csrf_token and lsd_token):
            logging.error("提取 CSRF 和 LSD 权杖失败，测试中止。")
            return

        logging.info("已获取所有必要信息，准备执行按赞...")
        
        success = like_post(driver, post_id, csrf_token, lsd_token)

        if success:
            logging.info("="*20)
            logging.info("  按赞操作成功！")
            logging.info("="*20)
        else:
            logging.error("="*20)
            logging.error("  按赞操作失败。请检查控制台输出以获取详细错误。")
            logging.error("="*20)

    except Exception as e:
        logging.error(f"测试过程中发生意外错误: {e}")
    finally:
        logging.info("测试结束，将在 15 秒后自动关闭浏览器...")
        time.sleep(15)
        driver.quit()

if __name__ == "__main__":
    main()
