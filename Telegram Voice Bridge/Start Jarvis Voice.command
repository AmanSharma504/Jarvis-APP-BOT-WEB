#!/bin/bash
set -e
cd "$(dirname "$0")"

if ! command -v node >/dev/null 2>&1; then
  echo "Node.js 22 or newer is required. Install it, then open this file again."
  read -r -p "Press Return to close..." _
  exit 1
fi

if ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 22 ? 0 : 1)'; then
  echo "Please update Node.js to version 22 or newer."
  read -r -p "Press Return to close..." _
  exit 1
fi

echo "=== Jarvis Telegram Voice Bridge ==="

USE_EXISTING_ENV=false
if [ -f .env ]; then
  # Check if tokens are present in .env
  if grep -q "^TELEGRAM_BOT_TOKEN=.." .env 2>/dev/null && grep -q "^ELEVENLABS_API_KEY=.." .env 2>/dev/null; then
    read -r -p "Found configured .env file. Use saved credentials? [Y/n]: " use_env_choice
    case "$use_env_choice" in
      [nN][oO]|[nN])
        USE_EXISTING_ENV=false
        ;;
      *)
        USE_EXISTING_ENV=true
        ;;
    esac
  fi
fi

if [ "$USE_EXISTING_ENV" = false ]; then
  echo "Please enter your API credentials:"
  read -r -s -p "Paste Telegram bot token (input hidden): " TELEGRAM_BOT_TOKEN
  echo
  read -r -s -p "Paste ElevenLabs API key (input hidden): " ELEVENLABS_API_KEY
  echo

  export TELEGRAM_BOT_TOKEN ELEVENLABS_API_KEY
  export ELEVENLABS_AGENT_ID="${ELEVENLABS_AGENT_ID:-agent_3801m7ck0aggewh93p3rqcg4a3f2}"
  export ELEVENLABS_VOICE_ID="${ELEVENLABS_VOICE_ID:-kFCe7jyOkkYKzOgpe2u0}"
  export ACTIVATE_TELEGRAM_WEBHOOK_REPLACEMENT=true

  read -r -p "Do you want to save these credentials to .env for future runs? [y/N]: " save_env_choice
  case "$save_env_choice" in
    [yY][eE][sS]|[yY])
      cat <<EOF > .env
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
ELEVENLABS_API_KEY=$ELEVENLABS_API_KEY
ELEVENLABS_AGENT_ID=$ELEVENLABS_AGENT_ID
ELEVENLABS_VOICE_ID=$ELEVENLABS_VOICE_ID
ACTIVATE_TELEGRAM_WEBHOOK_REPLACEMENT=true
EOF
      chmod 600 .env
      echo "Saved to .env (permissions set to 600)."
      ;;
  esac
fi

if [ ! -d "node_modules" ]; then
  echo "Installing dependencies..."
  npm install --cache "${TMPDIR:-/tmp}/jarvis-npm-cache"
fi

echo "Starting Jarvis Voice Bridge..."
npm start
