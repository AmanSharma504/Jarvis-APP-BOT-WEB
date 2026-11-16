FROM node:20-bullseye-slim

# Install system dependencies: Python 3, pip, ffmpeg, build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy package files
COPY package.json ./
COPY "Telegram Voice Bridge/package*.json" ./"Telegram Voice Bridge"/

# Install Node dependencies
RUN npm --prefix "Telegram Voice Bridge" install

# Copy application source code
COPY . .

# Install Python requirements
RUN pip3 install --no-cache-dir --break-system-packages pyrogram yt-dlp aiohttp || pip3 install --no-cache-dir pyrogram yt-dlp aiohttp

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV NODE_ENV=production

# Start Jarvis
CMD ["node", "index.js"]
