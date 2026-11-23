FROM node:22-bullseye-slim

# Install system dependencies: Python 3, pip, ffmpeg, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application source code
COPY . .

# Install Node dependencies
RUN npm install --omit=dev && \
    npm --prefix "Telegram Voice Bridge" install --omit=dev

# Install Python requirements for PyTgCalls & AI Engine
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir \
    aiohttp \
    pyrogram \
    tgcrypto \
    pytgcalls \
    yt-dlp

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOST=0.0.0.0
ENV NODE_ENV=production

# Start Jarvis
CMD ["node", "index.js"]
