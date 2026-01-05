# Claude Code Hooks - Standalone Implementation

Drop-in hooks for Claude Code that enforce coding standards without manual intervention.

## Philosophy

**"Rules are code, not documentation."**

- Claude follows rules automatically via hooks
- No need to explain rules repeatedly in prompts
- Violations are caught and blocked before they happen
- This is "AI-native pre-commit + CI"

## Directory Structure

Hooks are organized by their execution timing:

```
~/.claude/hooks/
├── pre-tool-use/              # Before Write/Edit - gate violations
│   └── check_line_number_limit.sh
├── post-tool-use/             # After Write/Edit - auto-fix
│   ├── ensure_executable.sh   # Make scripts executable
│   ├── format_code.sh         # Auto-format code
│   ├── run_lint.sh            # Run linters
│   └── run_tests.sh           # Run related tests
├── notification/              # User alerts
│   ├── notify_email.sh        # Email notifications
│   └── notify_voice.sh        # Voice/TTS alerts
├── stop/                      # Task completion checks
│   ├── check_local_rules.sh   # Verify coding rules
│   └── ON_STOP.md             # Instructions for task completion
├── session-start/             # Session initialization
│   └── SessionStart.sh
├── README.md
├── settings.json              # -> ../../settings.json
├── settings.json.example
└── settings.local.json        # -> ../../settings.local.json
```

## Hook Events

| Event            | Directory          | When                  | Purpose                       |
|------------------|--------------------|-----------------------|-------------------------------|
| **PreToolUse**   | `pre-tool-use/`    | Before Write/Edit     | Gate - block violations       |
| **PostToolUse**  | `post-tool-use/`   | After Write/Edit      | Auto-fix - format, lint, test |
| **Notification** | `notification/`    | Claude waiting/asking | Alert user via voice/email    |
| **Stop**         | `stop/`            | Task completion       | Final gate - verify all rules |
| **SessionStart** | `session-start/`   | Session begins        | Initialize environment        |

## File Size Limits

Thresholds (lines):
- **py, ts, tsx, js, jsx, el, sh, src**: 256 lines
- **css**: 512 lines
- **html, htm**: 1024 lines

Files exceeding limits are **blocked** before creation.

## Supported Languages

| Language                          | Format     | Lint         | Test        |
|-----------------------------------|------------|--------------|-------------|
| Python (.py)                      | ruff/black | ruff/flake8  | pytest      |
| TypeScript/JS (.ts/.tsx/.js/.jsx) | prettier   | eslint       | jest/vitest |
| CSS (.css)                        | prettier   | -            | -           |
| Emacs Lisp (.el)                  | elinter    | byte-compile | ERT         |
| Shell (.sh/.src/.bash)            | shfmt      | shellcheck   | -           |
| HTML (.html/.htm)                 | prettier   | htmlhint     | -           |

## Executable Files (ensure_executable.sh)

Automatically makes script files executable after Write/Edit:
- **Always executable**: `.sh`, `.bash`, `.zsh`, `.src`, `.py`, `.pl`, `.rb`, `.lua`
- **Executable if shebang present**: `.js`, `.php`, `.tcl`, `.awk`
- **Extensionless files**: Made executable if they have a recognized shebang

## Configuration

### Project-level settings.json

Add to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/pre-tool-use/check_line_number_limit.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "./.claude/hooks/post-tool-use/ensure_executable.sh" },
          { "type": "command", "command": "./.claude/hooks/post-tool-use/format_code.sh" },
          { "type": "command", "command": "./.claude/hooks/post-tool-use/run_lint.sh" },
          { "type": "command", "command": "./.claude/hooks/post-tool-use/run_tests.sh" }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          { "type": "command", "command": "./.claude/hooks/notification/notify_voice.sh" },
          { "type": "command", "command": "./.claude/hooks/notification/notify_email.sh" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "./.claude/hooks/stop/check_local_rules.sh" }
        ]
      }
    ]
  }
}
```

### How file filtering works

The `matcher` field matches **tool names** (Write, Edit, Bash, etc.), not file paths.
File path filtering happens **inside the hook scripts** by parsing the JSON input:

```bash
# Hook receives JSON via stdin with tool_input.file_path
FILE_PATH=$(cat | python3 -c "
import json, sys
d = json.load(sys.stdin)
print(d.get('tool_input', {}).get('file_path', ''))
")

# Filter by extension in the script
case "$FILE_PATH" in
  *.py) run_python_formatter ;;
  *.ts) run_ts_formatter ;;
  *.sh) run_shell_formatter ;;
esac
```

## Environment Variables

For email notifications, set these in your shell:
```bash
export SCITEX_EMAIL_AGENT="agent@scitex.ai"
export SCITEX_EMAIL_PASSWORD="your-password"
export CLAUDE_NOTIFY_EMAIL="your@email.com"  # Optional, defaults to ywata1989@gmail.com
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | OK - proceed |
| 1 | Warning - Claude sees feedback but continues |
| 2 | Error - Claude must fix before proceeding |

## Requirements

### Quick Install

```bash
# Install prettier, eslint, typescript-eslint
~/.dotfiles/.bin/installers/install_formatter_linter.sh

# Install shellcheck, shfmt
~/.dotfiles/.bin/installers/install_shell_formatter_linter.sh

# Python tools
pip install ruff black flake8 pytest
```

### Tools by Language

| Language | Formatter | Linter | Test |
|----------|-----------|--------|------|
| Python | ruff, black | ruff, flake8 | pytest |
| TS/JS | prettier | eslint | jest, vitest |
| Emacs Lisp | elinter | byte-compile | ERT |
| Shell | shfmt | shellcheck | - |
| HTML/CSS | prettier | htmlhint | - |

### Notifications
- TTS: scitex-audio MCP, espeak, or say (macOS)
- Email: Python smtplib (built-in)

## How It Works

1. **Claude writes a file** -> PreToolUse hook checks size
2. **If too large** -> Hook exits 2, write blocked, Claude sees error
3. **If OK** -> File written, PostToolUse runs format+lint+test
4. **Format fails** -> Auto-fixed, continue
5. **Test fails** -> Exit 2, Claude must fix
6. **Task done** -> Stop hook runs final checks
7. **User input needed** -> Notification hooks alert via voice/email

## Customization

### Adding new rules

1. Create a new hook script in the appropriate timing directory
2. Use exit code 2 to block, exit 0 to allow
3. Write errors to stderr (Claude sees stderr)
4. Add to your settings.json/toml

### Disabling hooks

Remove or comment out the hook entry in settings.json.

## License

MIT - Use freely, modify as needed.
