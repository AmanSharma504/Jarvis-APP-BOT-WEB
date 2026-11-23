#!/usr/bin/env python3
"""
Jarvis Voice Chat (VC) & Video Live Streaming Server
Powered by Pyrofork + PyTgCalls + yt-dlp + FFmpeg.
Maintains persistent WebRTC connection for instant play, pause, resume, skip, stop, and queue management.
"""

import sys
import os
import site
import asyncio
import json
import logging
import signal

import glob

# Dynamically ensure all user-installed site-packages (e.g. on Render) are loaded
try:
    for p in (site.getsitepackages() if hasattr(site, 'getsitepackages') else []) + [site.getusersitepackages()]:
        if p and os.path.exists(p) and p not in sys.path:
            sys.path.insert(0, p)
except Exception:
    pass

base_dirs = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..")),
    "/opt/render",
    os.path.expanduser("~")
]
for b in base_dirs:
    for sp in glob.glob(os.path.join(b, ".venv/lib/python*/site-packages")) + glob.glob(os.path.join(b, ".local/lib/python*/site-packages")):
        if os.path.exists(sp) and sp not in sys.path:
            sys.path.insert(0, sp)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("JarvisVCServer")

# Prepend project bin/ (ffmpeg and ffprobe) to PATH
BIN_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../bin"))
if os.path.exists(BIN_DIR):
    os.environ["PATH"] = f"{BIN_DIR}:{os.environ.get('PATH', '')}"

# Safe dependency check with zero-crash standard library fallback
HAS_DEPS = False
try:
    from aiohttp import web
    from pyrogram import Client
    from pytgcalls import PyTgCalls
    from pytgcalls.types import MediaStream, AudioQuality, VideoQuality, StreamEnded, GroupCallConfig
    HAS_DEPS = True
    logger.info("[VC Server] Full PyTgCalls WebRTC Live Streaming engine active.")
except ImportError as e:
    logger.info(f"[VC Server] Running in cloud-optimized HTTP zero-crash mode ({e}).")
    HAS_DEPS = False

if not HAS_DEPS:
    from http.server import HTTPServer, BaseHTTPRequestHandler
    class StubHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ready","vcOnline":false}')
        def do_POST(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":false,"error":"PyTgCalls audio-call engine is optional on cloud deployment"}')
        def log_message(self, format, *args):
            pass

    server = HTTPServer(("127.0.0.1", 8765), StubHandler)
    logger.info("Jarvis VC Fallback Server listening on http://127.0.0.1:8765")
    server.serve_forever()
    sys.exit(0)

# Initialize event loop for Python 3.14 compatibility before pyrogram imports
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

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

if not SESSION_STRING:
    logger.error("TELEGRAM_SESSION_STRING is missing in .env! Cannot start Assistant VC client.")
    sys.exit(1)

routes = web.RouteTableDef()

@web.middleware
async def firewall_middleware(request, handler):
    # Enforce loopback IP only
    peername = request.transport.get_extra_info("peername")
    client_ip = peername[0] if peername else ""
    if client_ip not in ("127.0.0.1", "::1", "localhost", ""):
        logger.warning(f"[Firewall Blocked] Unauthorized external IP attempted access to VC server: {client_ip}")
        return web.json_response({"ok": False, "error": "Access forbidden: Localhost only"}, status=403)

    # Check auth header if configured
    expected_token = get_env_var("JARVIS_IPC_SECRET", "")
    auth_header = request.headers.get("X-Jarvis-Auth", "")
    if expected_token and auth_header != expected_token:
        logger.warning("[Firewall Blocked] Invalid or missing IPC token")
        return web.json_response({"ok": False, "error": "Access forbidden: Invalid auth token"}, status=403)

    return await handler(request)

@routes.get("/health")
async def handle_health(request):
    active_streams = request.app["active_streams"]
    return web.json_response({"ok": True, "status": "online", "active_calls": list(active_streams.keys())})

@routes.post("/play")
async def handle_play(request):
    app = request.app["tg_client"]
    pytgcalls = request.app["pytgcalls"]
    active_streams = request.app["active_streams"]

    try:
        data = await request.json()
        chat_id = int(data.get("chat_id", 0))
        url = (data.get("file_path") or data.get("url", "")).strip()
        is_video = bool(data.get("is_video", False))
        invite_link = data.get("invite_link", "").strip()
        title = data.get("title", "Audio Stream")

        if not chat_id or not url:
            return web.json_response({"ok": False, "error": "chat_id and url/file_path are required"}, status=400)

        # 1. Ensure assistant is in the chat
        try:
            await app.get_chat_member(chat_id, "me")
        except Exception:
            if invite_link:
                try:
                    logger.info(f"Assistant joining chat {chat_id} via invite link...")
                    await app.join_chat(invite_link)
                except Exception as join_err:
                    logger.warning(f"Assistant join chat warning: {join_err}")

        # 2. Build media stream with optimized real-time buffer and smooth playback
        if is_video:
            # Video: High-capacity buffer with multi-threading to eliminate stutter and lag
            video_ffmpeg_params = "--video ---start -rtbufsize 64M -thread_queue_size 4096 -probesize 32M -analyzeduration 10M ---mid -threads 4"
            stream = MediaStream(
                url,
                audio_parameters=AudioQuality.STUDIO,
                audio_flags=MediaStream.Flags.REQUIRED,
                video_parameters=VideoQuality.HD_720p,
                ffmpeg_parameters=video_ffmpeg_params
            )
        else:
            # Audio: Stream with 64MB buffer for pristine zero-stutter high-fidelity studio playback
            audio_ffmpeg_params = "--audio ---start -rtbufsize 64M -probesize 16M -analyzeduration 5M ---mid -threads 2"
            stream = MediaStream(
                url,
                audio_parameters=AudioQuality.STUDIO,
                audio_flags=MediaStream.Flags.REQUIRED,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=audio_ffmpeg_params
            )

        # 3. Stream into Voice Chat with retry/recovery (seamlessly join or switch stream)
        try:
            await pytgcalls.play(chat_id, stream, config=GroupCallConfig(auto_start=True))
        except Exception as play_err:
            play_err_str = str(play_err)
            logger.warning(f"Initial play attempt note: {play_err_str}, checking call status...")
            if "CHAT_ADMIN_REQUIRED" in play_err_str or "phone.CreateGroupCall" in play_err_str:
                try:
                    await pytgcalls.play(chat_id, stream, config=GroupCallConfig(auto_start=False))
                except Exception as no_admin_err:
                    raise Exception("CHAT_ADMIN_REQUIRED: Please start a Voice Chat in this group first, or promote assistant to admin.") from no_admin_err
            else:
                try:
                    if hasattr(pytgcalls, "change_stream"):
                        await pytgcalls.change_stream(chat_id, stream)
                    else:
                        try:
                            await pytgcalls.leave_call(chat_id)
                        except Exception:
                            pass
                        await asyncio.sleep(0.3)
                        await pytgcalls.play(chat_id, stream)
                except Exception as retry_err:
                    logger.warning(f"Retry note: {retry_err}")
                    await pytgcalls.play(chat_id, stream)

        active_streams[chat_id] = {
            "is_video": is_video,
            "url": url,
            "title": title
        }
        logger.info(f"Successfully started {'video' if is_video else 'audio'} streaming in chat {chat_id}: {title}")
        return web.json_response({"ok": True, "status": "playing", "chat_id": chat_id, "title": title})
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Play error: {err_msg}")
        return web.json_response({"ok": False, "error": err_msg}, status=500)

@routes.post("/pause")
async def handle_pause(request):
    pytgcalls = request.app["pytgcalls"]
    try:
        data = await request.json()
        chat_id = int(data.get("chat_id", 0))
        await pytgcalls.pause(chat_id)
        return web.json_response({"ok": True, "status": "paused", "chat_id": chat_id})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

@routes.post("/resume")
async def handle_resume(request):
    pytgcalls = request.app["pytgcalls"]
    try:
        data = await request.json()
        chat_id = int(data.get("chat_id", 0))
        await pytgcalls.resume(chat_id)
        return web.json_response({"ok": True, "status": "resumed", "chat_id": chat_id})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

@routes.post("/seek")
async def handle_seek(request):
    pytgcalls = request.app["pytgcalls"]
    active_streams = request.app["active_streams"]
    try:
        data = await request.json()
        chat_id = int(data.get("chat_id", 0))
        seek_seconds = max(0, int(data.get("seconds", 0)))

        if chat_id not in active_streams:
            return web.json_response({"ok": False, "error": "No active stream in this chat"}, status=404)

        stream_info = active_streams[chat_id]
        url = stream_info["url"]
        is_video = stream_info.get("is_video", False)

        if is_video:
            video_ffmpeg_params = f"--video ---start -ss {seek_seconds} -rtbufsize 64M -thread_queue_size 4096 -probesize 32M -analyzeduration 10M ---mid -threads 4"
            stream = MediaStream(
                url,
                audio_parameters=AudioQuality.STUDIO,
                audio_flags=MediaStream.Flags.REQUIRED,
                video_parameters=VideoQuality.HD_720p,
                ffmpeg_parameters=video_ffmpeg_params
            )
        else:
            audio_ffmpeg_params = f"--audio ---start -ss {seek_seconds} -rtbufsize 64M -probesize 16M -analyzeduration 5M ---mid -threads 2"
            stream = MediaStream(
                url,
                audio_parameters=AudioQuality.STUDIO,
                audio_flags=MediaStream.Flags.REQUIRED,
                video_flags=MediaStream.Flags.IGNORE,
                ffmpeg_parameters=audio_ffmpeg_params
            )

        try:
            await pytgcalls.change_stream(chat_id, stream)
        except Exception as change_err:
            logger.warning(f"change_stream seek error: {change_err}, retrying with play...")
            await pytgcalls.play(chat_id, stream, config=GroupCallConfig(auto_start=True))

        stream_info["current_position"] = seek_seconds
        logger.info(f"Seeked stream in chat {chat_id} to {seek_seconds}s")
        return web.json_response({"ok": True, "status": "seeked", "chat_id": chat_id, "position": seek_seconds})
    except Exception as e:
        logger.error(f"Seek error: {e}")
        return web.json_response({"ok": False, "error": str(e)}, status=500)

@routes.post("/stop")
async def handle_stop(request):
    pytgcalls = request.app["pytgcalls"]
    active_streams = request.app["active_streams"]
    try:
        data = await request.json()
        chat_id = int(data.get("chat_id", 0))
        try:
            await pytgcalls.leave_call(chat_id)
        except Exception:
            pass
        if chat_id in active_streams:
            del active_streams[chat_id]
        return web.json_response({"ok": True, "status": "stopped", "chat_id": chat_id})
    except Exception as e:
        return web.json_response({"ok": False, "error": str(e)}, status=500)

async def main():
    logger.info("Initializing Jarvis Assistant Pyrogram client & PyTgCalls...")
    app = Client(
        name="jarvis_vc_assistant",
        api_id=int(API_ID),
        api_hash=API_HASH,
        session_string=SESSION_STRING,
        in_memory=True
    )

    pytgcalls = PyTgCalls(app)
    active_streams = {} # chatId -> { is_video, url, title }

    @pytgcalls.on_update()
    async def on_call_update(client, update):
        if isinstance(update, StreamEnded):
            chat_id = update.chat_id
            logger.info(f"Stream ended for chat {chat_id}")
            if chat_id in active_streams:
                del active_streams[chat_id]
            try:
                import urllib.request
                req = urllib.request.Request(
                    "http://127.0.0.1:8766/stream_ended",
                    data=json.dumps({"chat_id": chat_id}).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    pass
            except Exception as e:
                logger.debug(f"Could not notify bridge of stream_ended: {e}")

    await app.start()
    me = await app.get_me()
    logger.info(f"Assistant logged in as: {me.first_name} (@{me.username or me.id})")

    logger.info("Starting PyTgCalls engine...")
    await pytgcalls.start()

    server = web.Application(middlewares=[firewall_middleware])
    server["tg_client"] = app
    server["pytgcalls"] = pytgcalls
    server["active_streams"] = active_streams
    server.add_routes(routes)

    runner = web.AppRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 8765)
    await site.start()
    logger.info("Jarvis VC Live Streaming Server listening on http://127.0.0.1:8765")

    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Received termination signal, shutting down gracefully...")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            asyncio.get_running_loop().add_signal_handler(sig, signal_handler)
        except Exception:
            pass

    await stop_event.wait()
    logger.info("Cleaning up active calls...")
    for cid in list(active_streams.keys()):
        try:
            await pytgcalls.leave_call(cid)
        except Exception:
            pass
    try:
        binding = getattr(pytgcalls, "_binding", None)
        if binding and hasattr(binding, "calls"):
            for call_id in binding.calls():
                try:
                    await binding.stop(call_id)
                except Exception:
                    pass
    except Exception:
        pass
    await runner.cleanup()
    try:
        await app.stop()
    except Exception:
        pass
    logger.info("Server exited cleanly.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        logger.error(f"Fatal server exception: {e}")
    finally:
        os._exit(0)
