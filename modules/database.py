# modules/database.py

import sqlite3
from datetime import datetime

DB_FILE = "db/threads_dlp.db"

def get_db_connection():
    """建立並返回一個資料庫連接，並設定較長的超時時間。"""
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """初始化資料庫，並處理可能的結構變更。"""
    conn = get_db_connection()
    try:
        print("正在檢查並初始化資料庫...")
        cursor = conn.cursor()

        # 檢查舊的 'videos' 表格是否存在且主鍵是 post_id
        cursor.execute("PRAGMA table_info(videos)")
        columns = {row['name']: row for row in cursor.fetchall()}
        if 'post_id' in columns and columns['post_id']['pk'] == 1 and 'video_id' not in columns:
            print("[DB] 偵測到舊版資料庫結構，正在進行升級...")
            cursor.execute("ALTER TABLE videos RENAME TO videos_old")
            print("[DB] 已將舊表格重命名為 'videos_old'。")

        # 建立新結構的 videos 表格
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            post_id TEXT NOT NULL,
            post_url TEXT NOT NULL,
            video_url TEXT NOT NULL,
            author TEXT,
            caption TEXT,
            like_count INTEGER,
            comment_count INTEGER,
            timestamp TEXT,
            downloaded_at TEXT NOT NULL,
            local_path TEXT,
            uploaded_to_youtube BOOLEAN DEFAULT FALSE
        );
        """)

        # 建立用於記錄按讚的表格
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS liked_posts (
            post_id TEXT PRIMARY KEY,
            post_url TEXT NOT NULL,
            liked_at TEXT NOT NULL
        );
        """)

        # 嘗試為新表格新增 'uploaded_to_youtube' 欄位 (如果需要的話)
        try:
            # 這段程式碼主要為了向前相容，在新結構下通常不會執行
            cursor.execute("ALTER TABLE videos ADD COLUMN uploaded_to_youtube BOOLEAN DEFAULT FALSE")
            print("[DB] 成功新增 'uploaded_to_youtube' 欄位。")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                pass  # 欄位已存在，正常
            else:
                raise e

        conn.commit()
        print(f"資料庫 '{DB_FILE}' 已準備就緒。")
    finally:
        if conn:
            conn.close()

# --- 下載器使用的函式 ---
def get_all_existing_video_ids() -> set:
    """(批次讀取) 一次性讀取資料庫中所有已存在的 video_id。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT video_id FROM videos")
        return {row['video_id'] for row in cursor.fetchall()}
    finally:
        if conn:
            conn.close()

def add_video_entry(video_data: dict):
    """(逐筆寫入) 為單一影片新增一筆紀錄。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        download_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 組合 video_id
        video_id = f"{video_data.get('post_id')}-{video_data.get('video_index', 1)}"
        
        cursor.execute("""
        INSERT INTO videos (video_id, post_id, post_url, video_url, author, caption, like_count, comment_count, timestamp, downloaded_at, local_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_id,
            video_data.get('post_id'), video_data.get('post_url'), video_data.get('video_url'),
            video_data.get('author'), video_data.get('caption'), video_data.get('like_count'),
            video_data.get('comment_count'), video_data.get('timestamp'), download_time,
            video_data.get('local_path')
        ))
        conn.commit()
        print(f"[DB] 已成功紀錄影片: {video_id}")
    except sqlite3.IntegrityError:
        print(f"[DB] 警告：影片 {video_id} 已存在於資料庫中。")
    except Exception as e:
        print(f"[DB] 新增紀錄時發生錯誤: {e}")
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

def update_upload_status(video_id: str, status: bool = True):
    """(逐筆寫入) 更新單一影片的上傳狀態。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE videos SET uploaded_to_youtube = ? WHERE video_id = ?", (status, video_id))
        conn.commit()
        print(f"[DB] 已更新影片 {video_id} 的上傳狀態為 {status}。")
    except Exception as e:
        print(f"[DB] 更新影片 {video_id} 狀態時發生錯誤: {e}")
        raise
    finally:
        if conn:
            conn.close()

# --- 按讚功能使用的函式 ---

def get_all_liked_post_ids() -> set:
    """(批次讀取) 一次性讀取所有已按讚的 post_id。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT post_id FROM liked_posts")
        return {row['post_id'] for row in cursor.fetchall()}
    finally:
        if conn:
            conn.close()

def add_liked_post(post_id: str, post_url: str):
    """(逐筆寫入) 新增一筆按讚紀錄，包含 post_id 和 post_url。"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        liked_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
        INSERT OR IGNORE INTO liked_posts (post_id, post_url, liked_at) VALUES (?, ?, ?)
        """, (post_id, post_url, liked_time))
        conn.commit()
    except Exception as e:
        print(f"[DB] 新增按讚紀錄時發生錯誤: {e}")
        raise
    finally:
        if conn:
            conn.close()