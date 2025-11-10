# -*- coding: utf-8 -*-
import sqlite3
import logging
from datetime import datetime

DB_FILE = "db/threads_dlp.db"

def get_db_connection():
    """建立並返回一個資料庫連接，並設定為 row_factory 以便將結果作為字典存取。"""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

import logging

def init_db():
    """
    初始化資料庫，建立 `videos` 和 `liked_posts` 資料表。
    此函式包含遷移邏輯，可自動為舊版資料庫新增欄位。
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 確保 `videos` 資料表存在，並使用最新的欄位結構
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS videos (
        video_id TEXT PRIMARY KEY,
        post_id TEXT,
        author TEXT,
        caption TEXT,
        video_url TEXT,
        like_count INTEGER,
        download_count INTEGER,
        comment_count INTEGER,
        repost_count INTEGER,
        share_count INTEGER,
        timestamp DATETIME,
        local_path TEXT,
        uploaded_to_youtube BOOLEAN DEFAULT FALSE,
        upload_timestamp DATETIME,
        youtube_title TEXT,
        youtube_description TEXT,
        youtube_tags TEXT
    )
    ''')

    # 2. 遷移邏輯：檢查並新增缺失的欄位，以支援舊版資料庫
    cursor.execute("PRAGMA table_info(videos)")
    columns = [row['name'] for row in cursor.fetchall()]

    missing_columns = {
        'upload_timestamp': 'DATETIME',
        'youtube_title': 'TEXT',
        'youtube_description': 'TEXT',
        'youtube_tags': 'TEXT'
    }

    for col, col_type in missing_columns.items():
        if col not in columns:
            logging.info(f"正在更新資料庫結構：新增 '{col}' 欄位...")
            try:
                cursor.execute(f"ALTER TABLE videos ADD COLUMN {col} {col_type}")
            except sqlite3.OperationalError as e:
                logging.error(f"新增欄位 '{col}' 失敗: {e}")

    # 3. 確保 `liked_posts` 資料表存在
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS liked_posts (
        post_id TEXT PRIMARY KEY,
        like_timestamp DATETIME
    )
    ''')
    
    conn.commit()
    conn.close()

def add_video_entry(video_data):
    """新增一筆新的影片紀錄到資料庫中。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO videos (
        video_id, post_id, author, caption, video_url, like_count, 
        download_count, comment_count, repost_count, share_count, 
        timestamp, local_path
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        f"{video_data['post_id']}-{video_data.get('video_index', 1)}",
        video_data['post_id'],
        video_data['author'],
        video_data['caption'],
        video_data['video_url'],
        video_data.get('like_count', 0),
        video_data.get('download_count', 0),
        video_data.get('comment_count', 0),
        video_data.get('repost_count', 0),
        video_data.get('share_count', 0),
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

def update_upload_status(video_id, status, title="", description="", tags=""):
    """更新指定影片的 YouTube 上傳狀態。"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    UPDATE videos 
    SET uploaded_to_youtube = ?, upload_timestamp = ?, youtube_title = ?, youtube_description = ?, youtube_tags = ?
    WHERE video_id = ?
    ''', (status, datetime.now() if status else None, title, description, tags, video_id))
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
