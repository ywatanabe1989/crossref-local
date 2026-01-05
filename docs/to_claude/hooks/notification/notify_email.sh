#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# Timestamp: "2025-12-18 (ywatanabe)"
# File: ~/.claude/to_claude/hooks/notify_email.sh
# Description: Email notification when Claude needs attention (Notification hook)
#
# Uses SciTeX email (agent@scitex.ai) to send notifications
# Target: ywata1989@gmail.com
#
# Notification types:
#   - idle_prompt: Claude is waiting for input
#   - permission_prompt: Claude needs permission
#   - stop: Task completed

set -euo pipefail

# Email configuration (from SCITEX env)
SMTP_SERVER="${SCITEX_SMTP_SERVER:-mail1030.onamae.ne.jp}"
SMTP_PORT="${SCITEX_SMTP_PORT:-465}"
SENDER_EMAIL="${SCITEX_EMAIL_AGENT:-agent@scitex.ai}"
SENDER_PASSWORD="${SCITEX_EMAIL_PASSWORD:-}"
RECIPIENT_EMAIL="${CLAUDE_NOTIFY_EMAIL:-ywata1989@gmail.com}"

# Read hook input JSON from stdin
INPUT=$(cat)

# Extract notification_type from hook input
NOTIFICATION_TYPE=$(echo "$INPUT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('notification_type', '') or '')
" 2>/dev/null || echo "")

# If no notification type, nothing to do
[ -n "$NOTIFICATION_TYPE" ] || exit 0

# Skip if email not configured
[ -n "$SENDER_PASSWORD" ] || exit 0

# Function to send email via Python
send_email() {
    local subject="$1"
    local body="$2"

    python3 << PYEOF
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

smtp_server = "$SMTP_SERVER"
smtp_port = int("$SMTP_PORT")
sender = "$SENDER_EMAIL"
password = "$SENDER_PASSWORD"
recipient = "$RECIPIENT_EMAIL"
subject = """$subject"""
body = """$body"""

try:
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print(f"Email sent to {recipient}")
except Exception as e:
    print(f"Failed to send email: {e}", file=__import__('sys').stderr)
    __import__('sys').exit(1)
PYEOF
}

# Get project/cwd for context
PROJECT_NAME=$(basename "$(pwd)" 2>/dev/null || echo "unknown")
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Determine message based on notification type
case "$NOTIFICATION_TYPE" in
    idle_prompt)
        send_email \
            "[Claude Code] Waiting for input - $PROJECT_NAME" \
            "Claude Code is waiting for your input.

Project: $PROJECT_NAME
Time: $TIMESTAMP

Please check your terminal."
        ;;
    permission_prompt)
        send_email \
            "[Claude Code] Permission required - $PROJECT_NAME" \
            "Claude Code needs your permission to continue.

Project: $PROJECT_NAME
Time: $TIMESTAMP

Please check your terminal to approve or deny the action."
        ;;
    stop)
        send_email \
            "[Claude Code] Task completed - $PROJECT_NAME" \
            "Claude Code has finished the current task.

Project: $PROJECT_NAME
Time: $TIMESTAMP

Review the changes in your terminal."
        ;;
    *)
        send_email \
            "[Claude Code] Attention needed - $PROJECT_NAME" \
            "Claude Code needs your attention.

Type: $NOTIFICATION_TYPE
Project: $PROJECT_NAME
Time: $TIMESTAMP

Please check your terminal."
        ;;
esac

exit 0
