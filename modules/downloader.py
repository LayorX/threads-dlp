# modules/downloader.py

import subprocess
import os
import time

def download_video(video_url: str, full_path: str) -> bool:
    """接收一個指定的 URL 和完整的儲存路徑，使用 yt-dlp 進行下載。"""
    
    # 從完整路徑中獲取目錄，並確保它存在
    output_dir = os.path.dirname(full_path)
    os.makedirs(output_dir, exist_ok=True)

    command = [
        "uv", "run", "yt-dlp",
        "--output", full_path, # 直接使用傳入的完整路徑
        "--no-overwrites", # 如果檔案已存在，則不覆蓋
        video_url
    ]

    try:
        print(f"開始下載: {video_url}")
        # 增加 timeout，防止卡住
        subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore', timeout=300)
        print(f"下載成功！影片儲存於: {full_path}")
        return True
    except subprocess.TimeoutExpired:
        print(f"[下載錯誤] 下載超時 (300秒)。")
        return False
    except Exception as e:
        # 捕獲所有其他可能的錯誤，例如 CalledProcessError
        print(f"[下載錯誤] yt-dlp 執行失敗。 {getattr(e, 'stderr', e)}")
        return False