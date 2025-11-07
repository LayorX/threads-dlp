web: uv run datasette db/threads_dlp.db --host 0.0.0.0 -m datasette.json --create --port $PORT
worker: uv run python scheduler.py