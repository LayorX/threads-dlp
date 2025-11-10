# -*- coding: utf-8 -*-
import sqlite3
import logging
from datetime import datetime

DB_FILE = "threads_dlp.db"

def get_db_connection():
    """建立並返回一個資料庫連接，並設定為 row_factory 以便將結果作為字典存取。"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

import logging

def init_db():
    """
    初始化資料庫，建立或遷移 `videos` 和 `liked_posts` 資料表。
    此函式包含一個健壯的遷移邏輯，可處理欄位重命名和新增。
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 檢查 `videos` 資料表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='videos'")
        table_exists = cursor.fetchone()

        if table_exists:
            # 如果資料表存在，檢查是否為需要遷移的舊結構
            cursor.execute("PRAGMA table_info(videos)")
            columns = [row['name'] for row in cursor.fetchall()]

            if 'downloaded_at' in columns:
                # --- 執行一次性的黃金標準遷移 ---
                logging.info("偵測到舊版資料庫結構 (v1)，正在執行一次性升級遷移...")
                try:
                    cursor.execute("BEGIN TRANSACTION")
                    # 1. 重命名舊表
                    cursor.execute("ALTER TABLE videos RENAME TO videos_old")
                    
                    # 2. 建立新表 (使用最終的正確結構)
                    cursor.execute('''
                    CREATE TABLE videos (
                        video_id TEXT PRIMARY KEY,
                        post_id TEXT,
                        post_url TEXT NOT NULL DEFAULT '',
                        author TEXT,
                        caption TEXT,
                        video_url TEXT,
                        like_count INTEGER,
                        comment_count INTEGER,
                        timestamp DATETIME,
                        local_path TEXT,
                        uploaded_to_youtube BOOLEAN DEFAULT FALSE,
                        upload_timestamp DATETIME,
                        youtube_title TEXT
                    )
                    ''')

                    # 3. 從舊表複製數據到新表，並正確映射欄位
                    #    注意：我們只選擇新表中存在的欄位進行複製
                    cursor.execute('''
                    INSERT INTO videos (
                        video_id, post_id, author, caption, video_url, like_count, 
                        comment_count, timestamp, local_path
                    )
                    SELECT 
                        video_id, post_id, author, caption, video_url, like_count, 
                        comment_count, downloaded_at, local_path
                    FROM videos_old
                    ''')

                    # 4. 刪除舊表
                    cursor.execute("DROP TABLE videos_old")
                    cursor.execute("COMMIT")
                    logging.info("資料庫結構遷移成功！")
                except Exception as e:
                    cursor.execute("ROLLBACK")
                    logging.critical(f"資料庫遷移失敗: {e}。請刪除 db/threads_dlp.db 檔案後重試。")
                    raise e
            else:
                # 對於沒有 `downloaded_at` 但可能缺少其他欄位的較新版本，進行補充
                all_columns = {
                    'post_url': 'TEXT NOT NULL DEFAULT ""',
                    'comment_count': 'INTEGER',
                    'youtube_title': 'TEXT'
                    # 其他欄位...
                }
                for col, col_type in all_columns.items():
                    if col not in columns:
                        logging.info(f"正在更新資料庫結構：新增 '{col}' 欄位...")
                        try:
                            cursor.execute(f"ALTER TABLE videos ADD COLUMN {col} {col_type}")
                        except sqlite3.OperationalError as e:
                            logging.error(f"新增欄位 '{col}' 失敗: {e}")

        else:
            # 如果資料表不存在，直接建立最新的
            cursor.execute('''
            CREATE TABLE videos (
                video_id TEXT PRIMARY KEY,
                post_id TEXT,
                post_url TEXT NOT NULL DEFAULT '',
                author TEXT,
                caption TEXT,
                video_url TEXT,
                like_count INTEGER,
                comment_count INTEGER,
                timestamp DATETIME,
                local_path TEXT,
                uploaded_to_youtube BOOLEAN DEFAULT FALSE,
                upload_timestamp DATETIME,
                youtube_title TEXT
            )
            ''')

        # 確保 `liked_posts` 資料表存在
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS liked_posts (
            post_id TEXT PRIMARY KEY,
            like_timestamp DATETIME
        )
        ''')
        
        conn.commit()
    finally:
        conn.close()


def add_video_entry(video_data):
    """新增一筆新的影片紀錄到資料庫中。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO videos (
        video_id, post_id, post_url, author, caption, video_url, like_count, 
        comment_count, timestamp, local_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        f"{video_data['post_id']}-{video_data.get('video_index', 1)}",
        video_data['post_id'],
        video_data.get('post_url', ''),
        video_data['author'],
        video_data['caption'],
        video_data['video_url'],
        video_data.get('like_count', 0),
        video_data.get('comment_count', 0),
        datetime.fromtimestamp(video_data['timestamp']),
        video_data['local_path']
    ))
    conn.commit()
    conn.close()

def get_all_existing_video_ids():
    """從資料庫中獲取所有已存在的影片 ID。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT video_id FROM videos")
    ids = {row['video_id'] for row in cursor.fetchall()}
    conn.close()
    return ids

def get_all_videos_to_upload():
    """獲取所有尚未上傳到 YouTube 的影片紀錄。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM videos WHERE uploaded_to_youtube = FALSE OR uploaded_to_youtube IS NULL")
    videos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return videos

def update_upload_status(video_id, status, title=""):
    """更新指定影片的 YouTube 上傳狀態和標題。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE videos 
    SET uploaded_to_youtube = ?, upload_timestamp = ?, youtube_title = ?
    WHERE video_id = ?
    ''', (status, datetime.now() if status else None, title, video_id))
    conn.commit()
    conn.close()

def add_liked_post(post_id):
    """新增一筆按讚貼文的紀錄。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO liked_posts (post_id, like_timestamp) VALUES (?, ?)", (post_id, datetime.now()))
    conn.commit()
    conn.close()

def get_all_liked_post_ids():
    """獲取所有已按讚的貼文 ID。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT post_id FROM liked_posts")
    ids = {row['post_id'] for row in cursor.fetchall()}
    conn.close()
    return ids

def get_all_uploaded_videos():
    """獲取所有已上傳到 YouTube 的影片紀錄的本地路徑。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT local_path FROM videos WHERE uploaded_to_youtube = 1 AND local_path IS NOT NULL")
    paths = [row['local_path'] for row in cursor.fetchall()]
    conn.close()
    return paths
