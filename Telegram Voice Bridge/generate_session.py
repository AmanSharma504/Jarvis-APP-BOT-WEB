#!/usr/bin/env python3
"""
Jarvis Telegram Assistant Session String Generator
Uses Pyrogram with API_ID and API_HASH to generate a Pyrogram String Session.
Automatically appends the generated session to .env
"""

import os
import sys
import asyncio

# Ensure an active event loop exists for Python 3.14 compatibility before pyrogram import
try:
    asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

# Route tgcalls to ntgcalls for Python 3.14 compatibility if needed
try:
    import ntgcalls
    sys.modules["tgcalls"] = ntgcalls
except Exception:
    pass

import site
user_site = site.getusersitepackages()
if isinstance(user_site, str) and os.path.exists(user_site) and user_site not in sys.path:
    sys.path.append(user_site)

py314_site = os.path.expanduser("~/Library/Python/3.14/lib/python/site-packages")
if os.path.exists(py314_site) and py314_site not in sys.path:
    sys.path.append(py314_site)

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def get_env_var(key, default=""):
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get(key, default)

API_ID = get_env_var("TELEGRAM_API_ID", "26159672")
API_HASH = get_env_var("TELEGRAM_API_HASH", "43ca810ccbd4b6282601c99fea20ed92")

try:
    from pyrogram import Client
except ImportError:
    print("❌ Pyrogram is not installed. Run: pip3 install pyrogram")
    sys.exit(1)

async def main():
    print("=" * 60)
    print("🤖 Jarvis Assistant Session String Generator")
    print(f"🔑 Using API_ID: {API_ID}")
    print(f"🔑 Using API_HASH: {API_HASH[:6]}...{API_HASH[-4:]}")
    print("=" * 60)
    print("📱 Telegram will send you a login code via the official Telegram app.")
    print("⚠️ When entering your phone number, include your country code (e.g. +91XXXXXXXXXX)")
    print("-" * 60)

    async with Client(
        name="jarvis_assistant",
        api_id=int(API_ID),
        api_hash=API_HASH,
        in_memory=True
    ) as app:
        session_str = await app.export_session_string()
        me = await app.get_me()

        print("\n" + "=" * 60)
        print(f"✅ Success! Connected as: {me.first_name} (@{me.username or 'No Username'}) [ID: {me.id}]")
        print("=" * 60)

        # Update .env
        env_content = ""
        if os.path.exists(ENV_PATH):
            with open(ENV_PATH, "r", encoding="utf-8") as f:
                env_content = f.read()

        if "TELEGRAM_SESSION_STRING=" in env_content:
            import re
            env_content = re.sub(
                r"TELEGRAM_SESSION_STRING=.*",
                f"TELEGRAM_SESSION_STRING={session_str}",
                env_content
            )
        else:
            env_content += f"\n# Assistant Account MTProto Session String\nTELEGRAM_SESSION_STRING={session_str}\n"

        with open(ENV_PATH, "w", encoding="utf-8") as f:
            f.write(env_content)

        print(f"💾 Session String has been automatically saved to: {ENV_PATH}")
        print("🚀 Jarvis can now join Voice/Video Chats and stream live music and movies!")
        print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error during session generation: {e}")
