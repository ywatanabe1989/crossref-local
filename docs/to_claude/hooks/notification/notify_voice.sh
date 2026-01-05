#!/bin/bash
# -*- coding: utf-8 -*-
# Timestamp: "2026-01-04 22:51:32 (ywatanabe)"
# File: ./.claude/to_claude/hooks/notification/notify_voice.sh

ORIG_DIR="$(pwd)"
THIS_DIR="$(cd $(dirname ${BASH_SOURCE[0]}) && pwd)"
LOG_PATH="$THIS_DIR/.$(basename $0).log"
echo > "$LOG_PATH"

GIT_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)"

GRAY='\033[0;90m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GRAY}INFO: $1${NC}"; }
echo_success() { echo -e "${GREEN}SUCC: $1${NC}"; }
echo_warning() { echo -e "${YELLOW}WARN: $1${NC}"; }
echo_error() { echo -e "${RED}ERRO: $1${NC}"; }
echo_header() { echo_info "=== $1 ==="; }
# ---------------------------------------

THIS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_PATH="$THIS_DIR/.$(basename "$0").log"
echo >"$LOG_PATH"

#!/usr/bin/env bash
# Description: Voice notification when Claude needs attention (Notification hook)

# Notification types:
#   - idle_prompt: Claude is waiting for input
#   - permission_prompt: Claude needs permission

# Uses ElevenLabs API directly (requires ELEVENLABS_API_KEY env var)
# Fallback: say (macOS), espeak (Linux), or terminal bell

set -euo pipefail

INPUT=$(cat)

NOTIFICATION_TYPE=$(echo "$INPUT" | python3 -c "import json, sys
d = json.load(sys.stdin)
print(d.get('notification_type', '') or '')" 2>/dev/null || echo "")

[ -n "$NOTIFICATION_TYPE" ] || exit 0

PROJECT_NAME=""
BRANCH_NAME=""
if git rev-parse --is-inside-work-tree &>/dev/null; then
    GIT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || echo "")
    if [ -n "$GIT_ROOT" ]; then
        PROJECT_NAME=$(basename "$GIT_ROOT")
    fi
    BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
fi

PROJECT_PREFIX=""
if [ -n "$PROJECT_NAME" ]; then
    PROJECT_PREFIX="Project - $PROJECT_NAME"
    if [ -n "$BRANCH_NAME" ]; then
        PROJECT_PREFIX="$PROJECT_PREFIX on Branch - $BRANCH_NAME"
    fi
    PROJECT_PREFIX="$PROJECT_PREFIX: "
fi

speak_elevenlabs() {
    local text="$1"
    local api_key="${ELEVENLABS_API_KEY:-}"
    local voice_id="${ELEVENLABS_VOICE_ID:-21m00Tcm4TlvDq8ikWAM}" # Rachel voice
    local model_id="${ELEVENLABS_MODEL_ID:-eleven_turbo_v2_5}"
    local tmp_file
    tmp_file="/tmp/elevenlabs_$$_$(date +%s).mp3"

    [ -n "$api_key" ] || return 1

    curl -s -X POST \
        "https://api.elevenlabs.io/v1/text-to-speech/${voice_id}" \
        -H "xi-api-key: ${api_key}" \
        -H "Content-Type: application/json" \
        -d "{
            \"text\": \"${text}\",
            \"model_id\": \"${model_id}\",
            \"voice_settings\": {
                \"stability\": 0.5,
                \"similarity_boost\": 0.75,
                \"speed\": 1.5
            }
        }" \
        --output "$tmp_file" 2>/dev/null || return 1

    [ -s "$tmp_file" ] || {
        rm -f "$tmp_file"
        return 1
    }

    # Play audio in background
    if command -v mpv &>/dev/null; then
        mpv --no-video --really-quiet "$tmp_file" &>/dev/null &
    elif command -v ffplay &>/dev/null; then
        ffplay -nodisp -autoexit -loglevel quiet "$tmp_file" &>/dev/null &
    elif command -v aplay &>/dev/null; then
        ffmpeg -i "$tmp_file" -f wav - 2>/dev/null | aplay -q &>/dev/null &
    elif command -v paplay &>/dev/null; then
        ffmpeg -i "$tmp_file" -f wav - 2>/dev/null | paplay &>/dev/null &
    else
        rm -f "$tmp_file"
        return 1
    fi

    # Clean up temp file after playback (give it time to start)
    (sleep 10 && rm -f "$tmp_file") &>/dev/null &

    return 0
}

speak_system() {
    local text="$1"

    if command -v say &>/dev/null; then
        say -r 200 "$text" &
    elif command -v espeak &>/dev/null; then
        espeak -s 200 "$text" &
    elif command -v spd-say &>/dev/null; then
        spd-say -r 50 "$text" &
    else
        echo -e "\a" >/dev/tty 2>/dev/null || true
        echo "[NOTIFICATION] $text" >&2
    fi
}

speak() {
    local text="$1"
    speak_elevenlabs "$text" || speak_system "$text"
}

case "$NOTIFICATION_TYPE" in
idle_prompt)
    speak "${PROJECT_PREFIX}Claude needs your input"
    ;;
permission_prompt)
    speak "${PROJECT_PREFIX}Claude needs permission"
    ;;
stop)
    speak "${PROJECT_PREFIX}Task completed"
    ;;
*)
    speak "${PROJECT_PREFIX}Claude needs attention"
    ;;
esac

exit 0

# EOF