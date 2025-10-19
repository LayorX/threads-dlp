# modules/threads_client.py

import requests
from config import THREADS_ACCESS_TOKEN

BASE_URL = "https://graph.threads.net/v1.0"

def get_user_posts(username: str) -> list:
    """獲取指定用戶的貼文列表。"""
    url = f"{BASE_URL}/profile_posts"
    params = {
        "username": username,
        "fields": "id,media_type,media_url,permalink,text,timestamp,thumbnail_url",
        "access_token": THREADS_ACCESS_TOKEN
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        print(f"[API 錯誤] 獲取用戶貼文時發生錯誤: {e}")
        return []
