# modules/database.py

import sqlite3
import os
from datetime import datetime

DB_FILE = "threads_dlp.db"

def get_db_connection():
    """建立並返回一個資料庫連接。"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row # 讓查詢結果可以像字典一樣訪問欄位
    return conn

def init_db():
    """初始化資料庫，如果資料表不存在，則建立它。"""
    print("正在檢查並初始化資料庫...")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        post_id TEXT PRIMARY KEY,      -- 貼文的唯一 ID
        post_url TEXT NOT NULL,        -- 貼文的 URL
        video_url TEXT NOT NULL,       -- 影片的直接 URL
        author TEXT,                   -- 作者名稱
        caption TEXT,                  -- 影片描述/標題
        like_count INTEGER,            -- 按讚數
        comment_count INTEGER,         -- 留言數
        timestamp TEXT,                -- 原始發布時間
        downloaded_at TEXT NOT NULL,   -- 我們下載它的時間
        local_path TEXT                -- 儲存在本地的路徑
    );
    """)
    conn.commit()
    conn.close()
    print(f"資料庫 '{DB_FILE}' 已準備就緒。")

def post_exists(post_id: str) -> bool:
    """檢查指定的 post_id 是否已存在於資料庫中。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM videos WHERE post_id = ?", (post_id,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def add_video_entry(video_data: dict):
    """將一筆新的影片紀錄新增到資料庫。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        cursor.execute("""
        INSERT INTO videos (post_id, post_url, video_url, author, caption, like_count, comment_count, timestamp, downloaded_at, local_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_data.get('post_id'),
            video_data.get('post_url'),
            video_data.get('video_url'),
            video_data.get('author'),
            video_data.get('caption'),
            video_data.get('like_count'),
            video_data.get('comment_count'),
            video_data.get('timestamp'),
            download_time,
            video_data.get('local_path')
        ))
        conn.commit()
        print(f"[DB] 已成功紀錄貼文: {video_data.get('post_id')}")
    except sqlite3.IntegrityError:
        print(f"[DB] 錯誤：貼文 {video_data.get('post_id')} 已存在於資料庫中。")
    except Exception as e:
        print(f"[DB] 新增紀錄時發生錯誤: {e}")
    finally:
        conn.close()

