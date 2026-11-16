# Jarvis Telegram voice bridge

This bridge is prepared to accept Telegram text and voice notes, send the request to the existing ElevenLabs Jarvis agent, and return its answer as a Telegram voice note. It uses the Jarvis agent and Simran voice selected for this bot.

## Before activation

The current ElevenLabs Telegram connection owns the bot's Telegram webhook. Telegram allows one webhook or one long-polling consumer per bot. Starting this bridge calls `deleteWebhook` and replaces that connection, so the existing native ElevenLabs trigger will stop receiving messages. The current bot remains the same bot; its message handling moves to this bridge.

This project is prepared but is not connected to the bot yet. It needs the Telegram bot token and an ElevenLabs API key entered locally, plus a machine that stays online. Do not send either key in chat. The Telegram token entered into the ElevenLabs integration is not exposed to this project.

## Requirements

- Node.js 22 or later
- A working internet connection for downloading the app dependencies
- Telegram bot token from BotFather
- ElevenLabs API key with access to speech-to-text, text-to-speech, and the Jarvis agent

## Start locally on macOS

1. Install Node.js 22 or newer.
2. Double-click `Start Jarvis Voice.command` and enter the Telegram bot token and ElevenLabs API key when prompted. The entry is hidden while typing; neither key is saved in this folder.
3. Starting the bridge replaces the current text-only Telegram connection with this voice bridge.
4. Send `/start` to the Telegram bot. Text messages and voice notes should both receive spoken replies while this computer and process stay online.

Press Control+C to stop. When the bridge stops, the native ElevenLabs integration does not automatically take back the Telegram webhook. Restore the native channel in ElevenLabs if you want to switch back. For an always-available bot, this bridge needs to be moved to an always-on server with a protected secret store.

## What is handled

- Text messages are sent to Jarvis and answered as OGG/Opus voice notes.
- Telegram voice notes are transcribed by ElevenLabs, sent into the same Jarvis agent, and answered as voice notes.
- Per-chat agent sessions are kept alive for ten minutes to preserve conversational context.
- API keys stay in the local `.env` file and are never written into source code.

Telegram messages/audio and transcripts are processed by Telegram and ElevenLabs. Review each service's retention and privacy settings before using sensitive information.
