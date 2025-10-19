# view_db.py

import sqlite3
import os
from tabulate import tabulate

DB_FILE = "threads_dlp.db"

def view_database():
    """連接到 SQLite 資料庫並以表格形式印出 `videos` 表的內容。"""
    if not os.path.exists(DB_FILE):
        print(f"錯誤：資料庫檔案 '{DB_FILE}' 不存在。請先至少成功運行一次主程式。")
        return

    print(f"正在讀取資料庫: {DB_FILE}")
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    try:
        cursor.execute("""
        SELECT 
            post_id, 
            author, 
            caption, 
            like_count, 
            comment_count, 
            downloaded_at, 
            local_path 
        FROM videos 
        ORDER BY downloaded_at DESC
        """)
        rows = cursor.fetchall()

        if not rows:
            print("資料庫中目前沒有任何紀錄。")
            return

        # 將 sqlite3.Row 物件轉換為字典列表，以便 tabulate 處理
        data_to_tabulate = [dict(row) for row in rows]
        
        # 獲取欄位名
        headers = [description[0] for description in cursor.description]

        # 為了更好的顯示效果，對 caption 做截斷處理
        for row in data_to_tabulate:
            if row.get('caption') and len(row['caption']) > 40:
                row['caption'] = row['caption'][:37] + "..."

        print("\n--- Threads 影片下載紀錄 ---")
        # 使用 tabulate 格式化輸出
        print(tabulate(data_to_tabulate, headers="keys", tablefmt="grid"))
        print(f"\n總共找到 {len(rows)} 筆紀錄。")

    except Exception as e:
        print(f"查詢資料庫時發生錯誤: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    view_database()
