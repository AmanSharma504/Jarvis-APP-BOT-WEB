# ⚡ J.A.R.V.I.S. Multi-Platform AI Ecosystem
### 🌐 Web OS | 📱 Android App (PWA & APK) | 🤖 Telegram Voice Chat Bot

[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-PyTgCalls-blue.svg)](https://pytgcalls.github.io/)

An ultra-low-latency, supercomputer-inspired conversational AI ecosystem featuring Tony Stark's iconic J.A.R.V.I.S. persona. Seamlessly integrates a **Web Operating System**, **Installable Android Mobile App**, and a **Multi-Group Telegram Voice Chat (VC) Music & Video Streaming Assistant**.

---

## 🌟 Key Features

### ⚡ 1. Live Voice Mode (ChatGPT & Gemini Live Experience)
- **Supercomputer-Level Turnaround**: Sub-second conversational responses (~300ms–500ms) powered by `google/gemini-2.5-flash` and `openai/gpt-4o-mini`.
- **Instant VAD (Voice Activity Detection)**: 280ms conversational silence detection for seamless turn-taking without awkward pauses.
- **Barge-In Interruption**: Start speaking at any moment and J.A.R.V.I.S. instantly stops talking and listens to you.
- **Holographic Arc Reactor Visualizer**: Real-time animated canvas waveform and glowing Iron Man Arc Reactor orb reflecting listening, thinking, and speaking states.

### 🌐 2. Real-Time Web Search & Multi-Model Switching
- **Live Web Intelligence**: Automatically detects queries requiring current information (live weather, stock/crypto prices, breaking news, sports scores) and fetches real-time web data via `google/gemini-2.5-flash:online`.
- **Dynamic AI Model Selector**: Switch seamlessly between:
  - ⚡ `google/gemini-2.5-flash` (Gemini Ultra-Fast)
  - 🌐 `google/gemini-2.5-flash:online` (Gemini Live with Real-Time Web Search)
  - 🚀 `openai/gpt-4o-mini` (ChatGPT Fast)
  - 🧠 `deepseek/deepseek-chat` (DeepSeek V3)
  - 🦙 `meta-llama/llama-3.3-70b-instruct` (Llama 3.3)

### 🎙️ 3. Neural Speech Synthesis (43 Personas & 27 Languages)
- **Studio-Grade Acoustic Warmth**: Formant shaping with chest resonance (+1.4dB @ 180Hz) and anti-sibilance filtering eliminates metallic robotic artifacts.
- **Multi-Tier Zero-Fail Fallback**:
  - **Tier 1**: Microsoft Edge Neural TTS (Direct ultra-fast MP3 stream for Web/App, zero FFmpeg overhead).
  - **Tier 2**: Cartesia Sonic (State-of-the-art realistic human voice).
  - **Tier 3**: Google Universal Speech CDN (100% resilient zero-fail fallback).
- **Extensive Language Support**: All 22+ Scheduled Indian languages (Hindi, Punjabi, Marathi, Bengali, Tamil, Telugu, Gujarati, etc.) plus international languages (English, Spanish, French, German, Japanese, etc.).

### 🎵 4. Media Streaming Studio & Telegram VC Player
- **In-Browser & VC Streaming**: Search and stream YouTube audio/video with YouTube-style progress scrubber.
- **Interactive Seek Controls**: Instant `⏪ -10s` and `⏩ +10s` seeking both in-browser and inside Telegram Voice Chat.
- **English Player Cards**: Pristine track info card displaying title, artist, live queue status, and real-time progress bar.

### 📱 5. Android Mobile App & Web OS
- **PWA WebAPK**: 1-click home screen installation on any Android / iOS device.
- **Dedicated APK Download**: Standalone APK distribution for direct Android deployment.
- **Cross-Device Responsive**: Optimized layout for smartphones, tablets, and desktop workstations.

---

## 🏗️ Architecture Overview

```
                      +---------------------------------------+
                      |       User Interaction Channels       |
                      |  Web OS  |  Android App  |  Telegram  |
                      +-------------------+-------------------+
                                          |
                                          v
                      +---------------------------------------+
                      |      Jarvis High-Speed Gateway        |
                      |       (Node.js HTTP & IPC Server)     |
                      +-------------------+-------------------+
                                          |
         +--------------------------------+-------------------------------+
         |                                |                               |
         v                                v                               v
+------------------+            +-------------------+           +-------------------+
|  OpenRouter AI   |            |   Universal TTS   |           | PyTgCalls VC Node |
| (Gemini / GPT)   |            | (Edge / Cartesia) |           | (Python Streamer) |
+------------------+            +-------------------+           +-------------------+
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.10 or higher
- **FFmpeg**: Installed and available in PATH (or bundled static binaries)

### 1. Clone Repository
```bash
git clone https://github.com/AmanSharma504/Jarvis-APP-BOT-WEB.git
cd Jarvis-APP-BOT-WEB
```

### 2. Configure Environment Variables
Copy `.env.example` to `Telegram Voice Bridge/.env`:
```bash
cp "Telegram Voice Bridge/.env.example" "Telegram Voice Bridge/.env"
```
Fill in your credentials:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
BOT_OWNER_ID=your_numeric_telegram_user_id
OPENROUTER_API_KEY=your_openrouter_api_key
OPENROUTER_MODEL=google/gemini-2.5-flash
ACTIVATE_TELEGRAM_WEBHOOK_REPLACEMENT=true
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_SESSION_STRING=your_pyrogram_session_string
WEB_PORT=3000
```

### 3. Install Dependencies
```bash
# Install Node.js dependencies
cd "Telegram Voice Bridge"
npm install

# Install Python dependencies
pip install pyrogram pytgcalls yt-dlp aiohttp
```

### 4. Launch J.A.R.V.I.S.
From the project root:
```bash
npm start
```
Or directly:
```bash
node "Telegram Voice Bridge/src/index.js"
```

Access the Web OS and Live Voice Mode:
- **Local Workstation**: `http://localhost:3000`
- **Android Phone (Wi-Fi)**: `http://<your-lan-ip>:3000`

---

## 🔒 Security & Privacy
- **Zero Credential Leaks**: `.env` and session files are strictly ignored by `.gitignore`.
- **Sandboxed Execution**: Safe execution boundaries with IPC token verification between Node.js and Python.
- **Memory & Cache Hygiene**: Auto-cleanup daemon purges temporary audio and media cache files every 2 minutes.

---

## 👤 Author
Developed with ❤️ by **Aman Sharma** ([@AmanSharma504](https://github.com/AmanSharma504))
