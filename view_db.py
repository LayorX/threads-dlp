# view_db.py

import sqlite3
import os
from tabulate import tabulate

DB_FILE = "db/threads_dlp.db"

def view_database():
    """連接到 SQLite 資料庫，顯示摘要資訊，並以表格形式印出 `videos` 表的內容。"""
    if not os.path.exists(DB_FILE):
        print(f"錯誤：資料庫檔案 '{DB_FILE}' 不存在。請先至少成功運行一次主程式。")
        return

    print(f"正在讀取資料庫: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        # 1. 執行彙總查詢
        cursor.execute("""
        SELECT 
            COUNT(*) as total_videos,
            COUNT(CASE WHEN uploaded_to_youtube = 1 THEN 1 END) as uploaded_count,
            MAX(upload_timestamp) as last_upload_timestamp
        FROM videos
        """)
        summary = cursor.fetchone()

        # 2. 執行詳細資料查詢
        cursor.execute("""
        SELECT 
            post_id, 
            author, 
            caption, 
            like_count, 
            timestamp, 
            uploaded_to_youtube,
            upload_timestamp,
            local_path
        FROM videos 
        ORDER BY timestamp DESC
        """)
        rows = cursor.fetchall()

        if not rows:
            print("資料庫中目前沒有任何紀錄。")
            return

        # 將 sqlite3.Row 物件轉換為字典列表，以便 tabulate 處理
        data_to_tabulate = [dict(row) for row in rows]
        
        # 為了更好的顯示效果，對欄位進行格式化
        for row in data_to_tabulate:
            # 截斷 caption
            if row.get('caption') and len(row['caption']) > 30:
                row['caption'] = row['caption'][:27] + "..."
            # 格式化布林值
            row['uploaded_to_youtube'] = '是' if row['uploaded_to_youtube'] else '否'
            # 格式化時間戳
            if row['timestamp']:
                row['timestamp'] = row['timestamp'][:19] # YYYY-MM-DD HH:MM:SS
            if row['upload_timestamp']:
                row['upload_timestamp'] = row['upload_timestamp'][:19]


        print("\n--- Threads 影片下載紀錄 ---")
        print(tabulate(data_to_tabulate, headers="keys", tablefmt="psql"))
        
        # 3. 印出摘要資訊
        print("\n--- 摘要資訊 ---")
        if summary:
            total_videos = summary['total_videos']
            uploaded_count = summary['uploaded_count']
            last_upload = summary['last_upload_timestamp']
            
            print(f"總影片數: {total_videos}")
            print(f"已上傳至 YouTube: {uploaded_count}")
            print(f"最後上傳日期: {last_upload[:19] if last_upload else 'N/A'}")

    except sqlite3.OperationalError as e:
        print(f"查詢資料庫時發生錯誤: {e}")
        print("提示：這可能是因為資料庫結構已更新。請嘗試重新運行主程式以自動更新資料庫結構。")
    except Exception as e:
        print(f"處理資料庫時發生未預期的錯誤: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    view_database()
