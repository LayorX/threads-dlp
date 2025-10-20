# modules/database.py

import sqlite3
from datetime import datetime

DB_FILE = "threads_dlp.db"

def get_db_connection():
    """建立並返回一個資料庫連接，並設定較長的超時時間。"""
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化資料庫。"""
    conn = get_db_connection()
    try:
        print("正在檢查並初始化資料庫...")
        cursor = conn.cursor()
        try:
            cursor.execute("ALTER TABLE videos ADD COLUMN uploaded_to_youtube BOOLEAN DEFAULT FALSE")
            print("[DB] 成功新增 'uploaded_to_youtube' 欄位。")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                pass
            else:
                raise e

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            post_id TEXT PRIMARY KEY, post_url TEXT NOT NULL, video_url TEXT NOT NULL,
            author TEXT, caption TEXT, like_count INTEGER, comment_count INTEGER,
            timestamp TEXT, downloaded_at TEXT NOT NULL, local_path TEXT,
            uploaded_to_youtube BOOLEAN DEFAULT FALSE
        );
        """)
        conn.commit()
        print(f"資料庫 '{DB_FILE}' 已準備就緒。")
    finally:
        if conn:
            conn.close()

# --- 下載器使用的函式 ---
def get_all_existing_post_ids() -> set:
    """(批次讀取) 一次性讀取資料庫中所有已存在的 post_id。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT post_id FROM videos")
        return {row['post_id'] for row in cursor.fetchall()}
    finally:
        if conn:
            conn.close()

def add_video_entry(video_data: dict):
    """(逐筆寫入) 為單一影片新增一筆紀錄。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT INTO videos (post_id, post_url, video_url, author, caption, like_count, comment_count, timestamp, downloaded_at, local_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_data.get('post_id'), video_data.get('post_url'), video_data.get('video_url'),
            video_data.get('author'), video_data.get('caption'), video_data.get('like_count'),
            video_data.get('comment_count'), video_data.get('timestamp'), download_time,
            video_data.get('local_path')
        ))
        conn.commit()
        print(f"[DB] 已成功紀錄貼文: {video_data.get('post_id')}")
    except sqlite3.IntegrityError:
        # 這個錯誤在批次讀取模式下理論上不應該發生，但作為保險依然保留
        print(f"[DB] 警告：貼文 {video_data.get('post_id')} 已存在於資料庫中。")
    except Exception as e:
        print(f"[DB] 新增紀錄時發生錯誤: {e}")
        # 向上拋出異常，讓主程式知道發生了問題
        raise
    finally:
        if conn:
            conn.close()

# --- 上傳器使用的函式 ---
def get_all_videos_to_upload() -> list:
    """(批次讀取) 一次性讀取所有待上傳的影片。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM videos WHERE uploaded_to_youtube = FALSE AND local_path IS NOT NULL")
        return [dict(row) for row in cursor.fetchall()]
    finally:
        if conn:
            conn.close()

def update_upload_status(post_id: str, status: bool = True):
    """(逐筆寫入) 更新單一貼文的上傳狀態。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET uploaded_to_youtube = ? WHERE post_id = ?", (status, post_id))
        conn.commit()
        print(f"[DB] 已更新貼文 {post_id} 的上傳狀態為 {status}。")
    except Exception as e:
        print(f"[DB] 更新貼文 {post_id} 狀態時發生錯誤: {e}")
        # 向上拋出異常
        raise
    finally:
        if conn:
            conn.close()