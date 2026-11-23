# Production Dockerfile for Jarvis AI on Hugging Face Spaces
FROM node:22-bullseye-slim

# Install system dependencies: Python 3, pip, FFmpeg, git
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package specifications and install Node dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Install Python requirements for PyTgCalls, Pyrogram, yt-dlp, and aiohttp
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
    aiohttp \
    pyrogram \
    tgcrypto \
    pytgcalls \
    yt-dlp

# Copy project code
COPY . .

# Set Hugging Face environment variables
ENV PORT=3000
ENV HOST=0.0.0.0
ENV NODE_ENV=production

# Expose Web OS port
EXPOSE 3000

# Start Jarvis Multi-Platform AI Engine (Web OS + Telegram Bot + Voice Bridge)
CMD ["node", "src/index.js"]
