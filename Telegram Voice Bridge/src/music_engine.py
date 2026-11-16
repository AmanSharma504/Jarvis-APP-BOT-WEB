#!/usr/bin/env python3
"""
Jarvis High-Speed High-Fidelity Music & Video Search, Download & Stream Engine
Powered by yt-dlp & FFmpeg
Optimized with single-pass download, metadata caching, and sub-10ms cache retrieval.
"""

import sys
import os
import json
import re
import glob
import time

# Ensure user site packages are on sys.path
import site
user_site = site.getusersitepackages()
if isinstance(user_site, str) and os.path.exists(user_site) and user_site not in sys.path:
    sys.path.append(user_site)

py314_site = os.path.expanduser("~/Library/Python/3.14/lib/python/site-packages")
if os.path.exists(py314_site) and py314_site not in sys.path:
    sys.path.append(py314_site)

# Prepend project bin/ (ffmpeg and ffprobe) to PATH
BIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bin"))
if os.path.exists(BIN_DIR):
    os.environ["PATH"] = f"{BIN_DIR}:{os.environ.get('PATH', '')}"

try:
    import yt_dlp
except ImportError:
    yt_dlp = None

CACHE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../cache"))
os.makedirs(CACHE_DIR, exist_ok=True)
INDEX_FILE = os.path.join(CACHE_DIR, "media_index.json")

def load_metadata_index():
    if os.path.exists(INDEX_FILE):
        try:
            with open(INDEX_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_metadata_index(index):
    try:
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def format_duration(seconds):
    if not seconds:
        return "Live / Unknown"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def find_cached_file(video_id, is_video=False):
    pattern = os.path.join(CACHE_DIR, f"{video_id}.*")
    candidates = glob.glob(pattern)
    for c in candidates:
        if c.endswith((".part", ".ytdl", ".temp", ".json")):
            continue
        ext = os.path.splitext(c)[1].lower()
        if is_video and ext in [".mp4", ".mkv", ".mov"]:
            if os.path.getsize(c) > 100000:
                return c
        elif not is_video and ext in [".m4a", ".webm", ".opus", ".mp3", ".ogg", ".wav"]:
            if os.path.getsize(c) > 50000:
                return c
    return None

def sanitize_query(query):
    if not query:
        return ""
    # Strip dangerous shell / traversal characters
    cleaned = re.sub(r"[;&|`$><\\{}[\]]", " ", str(query))
    return re.sub(r"\s+", " ", cleaned).strip()

def search_and_download(query, is_video=False):
    if not yt_dlp:
        return {"error": "yt-dlp is not installed"}

    clean_query = sanitize_query(query)
    if not clean_query:
        return {"error": "Empty search query"}

    # 1. Fast In-Memory / Disk Metadata Cache Check (<5ms)
    index = load_metadata_index()
    cache_key = f"{'video' if is_video else 'audio'}_{clean_query.lower()}"
    if cache_key in index:
        cached_meta = index[cache_key]
        cached_file = cached_meta.get("file_path")
        if cached_file and os.path.exists(cached_file) and os.path.getsize(cached_file) > 50000:
            cached_meta["cached"] = True
            return cached_meta

    is_url = bool(re.match(r"^https?://", clean_query, re.I))
    search_target = clean_query if is_url else f"ytsearch1:{clean_query}"

    outtmpl = os.path.join(CACHE_DIR, "%(id)s.%(ext)s")

    # 2. Optimized Single-Pass yt-dlp Configuration
    # Merges extraction and high-speed multi-threaded download into one single operation
    if is_video:
        dl_opts = {
            "format": "bestvideo[height<=720][fps<=30][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "noprogress": True,
            "concurrent_fragment_downloads": 4,
        }
    else:
        dl_opts = {
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "noprogress": True,
            "concurrent_fragment_downloads": 4,
        }

    if os.path.exists(BIN_DIR):
        dl_opts["ffmpeg_location"] = BIN_DIR

    try:
        with yt_dlp.YoutubeDL(dl_opts) as ydl:
            # Single pass: extract and download concurrently
            info = ydl.extract_info(search_target, download=True)
            if not info:
                return {"error": "No media found for query"}

            entry = info
            if "entries" in info and info["entries"]:
                entry = info["entries"][0]

            video_id = entry.get("id") or "stream"
            title = entry.get("title", "Unknown Title")
            duration_sec = entry.get("duration", 0)
            duration_str = format_duration(duration_sec)
            thumbnail = entry.get("thumbnail") or ""
            uploader = entry.get("uploader") or entry.get("channel") or "Unknown Artist"
            webpage_url = entry.get("webpage_url") or entry.get("url") or ""

            # Locate downloaded file
            downloaded = find_cached_file(video_id, is_video)
            if not downloaded:
                cands = glob.glob(os.path.join(CACHE_DIR, f"{video_id}.*"))
                cands = [c for c in cands if not c.endswith((".part", ".ytdl", ".temp", ".json"))]
                if cands:
                    downloaded = cands[0]

            if not downloaded or not os.path.exists(downloaded):
                return {"error": "Failed to download media file to cache"}

            result = {
                "success": True,
                "title": title,
                "duration": duration_str,
                "duration_seconds": duration_sec,
                "thumbnail": thumbnail,
                "artist": uploader,
                "webpage_url": webpage_url,
                "file_path": downloaded,
                "is_video": is_video,
                "query": clean_query,
                "cached": False
            }

            # Update cache index for instant future queries
            index[cache_key] = result
            index[f"{'video' if is_video else 'audio'}_{video_id}"] = result
            save_metadata_index(index)

            return result
    except Exception as e:
        return {"error": f"Failed to extract or download media: {str(e)}"}

def search_media(query, is_video=False):
    return search_and_download(query, is_video)

def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "No arguments provided"}))
        return

    action = args[0].lower()
    query = " ".join(args[1:]) if len(args) > 1 else ""

    if action in ("play", "audio", "music", "song"):
        result = search_and_download(query, is_video=False)
        print(json.dumps(result))
    elif action in ("vplay", "video", "movie", "film"):
        result = search_and_download(query, is_video=True)
        print(json.dumps(result))
    else:
        query = " ".join(args)
        result = search_and_download(query, is_video=False)
        print(json.dumps(result))

if __name__ == "__main__":
    main()
