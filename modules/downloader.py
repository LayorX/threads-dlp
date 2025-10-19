# modules/downloader.py

import subprocess
import os

def download_video(video_url: str, output_path: str = "downloads") -> bool:
    """使用 yt-dlp 下載指定的影片 URL。"""
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        print(f"建立下載資料夾: {output_path}")

    command = [
        "uv", "run", "yt-dlp",
        "--output", os.path.join(output_path, "%(title)s.%(ext)s"),
        video_url
    ]

    try:
        print(f"開始下載: {video_url}")
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"下載成功！影片儲存於 {output_path} 資料夾中。")
        # print(result.stdout) # 可選：顯示 yt-dlp 的詳細輸出
        return True
    except FileNotFoundError:
        print("[下載錯誤] yt-dlp 未安裝或未在系統路徑中。請確保已安裝 yt-dlp。")
        return False
    except subprocess.CalledProcessError as e:
        print(f"[下載錯誤] yt-dlp 執行失敗，返回碼: {e.returncode}")
        print(f"錯誤訊息: {e.stderr}")
        return False
