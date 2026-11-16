#!/usr/bin/env python3
"""
Jarvis Voice Chat (VC) & Video Chat Live Media Streamer
Integrates Pyrogram + NTgCalls/PyTgCalls + yt-dlp + FFmpeg
Handles real-time group call audio (320kbps) & video (HD) streaming.
"""

import sys
import os
import asyncio
import json
import re

# Ensure an active event loop exists for Python 3.14 compatibility before pyrogram import
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Route tgcalls to ntgcalls for Python 3.14 compatibility
try:
    import ntgcalls
    sys.modules["tgcalls"] = ntgcalls
except Exception:
    pass

import site
user_site = site.getusersitepackages()
if isinstance(user_site, str) and os.path.exists(user_site) and user_site not in sys.path:
    sys.path.append(user_site)

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.env")

def get_env_var(key, default=""):
    if os.path.exists(ENV_PATH):
        try:
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith(f"{key}="):
                        val = line.split("=", 1)[1].strip()
                        return val.strip('"').strip("'")
        except Exception:
            pass
    return os.environ.get(key, default)

API_ID = get_env_var("TELEGRAM_API_ID", "26159672")
API_HASH = get_env_var("TELEGRAM_API_HASH", "43ca810ccbd4b6282601c99fea20ed92")
SESSION_STRING = get_env_var("TELEGRAM_SESSION_STRING", "")

from music_engine import search_media

async def play_stream(chat_id, query, is_video=False):
    # 1. Search media
    media_info = search_media(query, is_video=is_video)
    if not media_info.get("success"):
        return media_info

    stream_url = media_info.get("stream_url")
    title = media_info.get("title")

    # If session string is not yet set, return media info so bot can play via player card / direct link
    if not SESSION_STRING:
        return {
            **media_info,
            "vc_active": False,
            "assistant_configured": False,
            "message": "Assistant session string not yet configured in .env. To enable live VC streaming, run generate_session.py"
        }

    # If assistant is configured, join group call
    try:
        from pyrogram import Client
        from pytgcalls import GroupCallFactory

        app = Client(
            name="jarvis_assistant_streamer",
            api_id=int(API_ID),
            api_hash=API_HASH,
            session_string=SESSION_STRING,
            in_memory=True
        )

        await app.start()
        group_call = GroupCallFactory(app).get_file_group_call()
        group_call.input_filename = stream_url

        vc_active = False
        msg = "Media loaded and streaming ready."

        try:
            if chat_id and int(chat_id) != 0:
                await group_call.start(int(chat_id))
                vc_active = True
                msg = f"Successfully joined voice chat and streaming: {title}"
        except Exception as join_err:
            msg = f"VC streaming ready. Please ensure group voice chat is started ({join_err})"

        return {
            **media_info,
            "vc_active": vc_active,
            "assistant_configured": True,
            "message": msg
        }
    except Exception as e:
        return {
            **media_info,
            "vc_active": False,
            "assistant_configured": True,
            "error_detail": str(e),
            "message": f"VC stream status: {str(e)}"
        }

def main():
    args = sys.argv[1:]
    if not args:
        print(json.dumps({"error": "No arguments provided"}))
        return

    action = args[0].lower()
    chat_id = args[1] if len(args) > 1 else "0"
    query = " ".join(args[2:]) if len(args) > 2 else ""

    is_video = action in ("vplay", "video", "movie")

    result = asyncio.run(play_stream(chat_id, query, is_video=is_video))
    print(json.dumps(result))

if __name__ == "__main__":
    main()
