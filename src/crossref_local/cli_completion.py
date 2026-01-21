"""Shell completion commands for crossref-local CLI."""

import os
import sys
from pathlib import Path

import click

PROG_NAME = "crossref-local"

# Shell completion scripts
BASH_COMPLETION = f"""# {PROG_NAME} bash completion
eval "$(_CROSSREF_LOCAL_COMPLETE=bash_source {PROG_NAME})"
"""

ZSH_COMPLETION = f"""# {PROG_NAME} zsh completion
eval "$(_CROSSREF_LOCAL_COMPLETE=zsh_source {PROG_NAME})"
"""

FISH_COMPLETION = f"""# {PROG_NAME} fish completion
_CROSSREF_LOCAL_COMPLETE=fish_source {PROG_NAME} | source
"""

# Shell config files
SHELL_CONFIGS = {
    "bash": [Path.home() / ".bashrc", Path.home() / ".bash_profile"],
    "zsh": [Path.home() / ".zshrc"],
    "fish": [Path.home() / ".config" / "fish" / "config.fish"],
}

COMPLETION_SCRIPTS = {
    "bash": BASH_COMPLETION,
    "zsh": ZSH_COMPLETION,
    "fish": FISH_COMPLETION,
}

COMPLETION_MARKER = f"# >>> {PROG_NAME} completion >>>"
COMPLETION_END_MARKER = f"# <<< {PROG_NAME} completion <<<"


def _detect_shell() -> str:
    """Detect current shell from $SHELL environment variable."""
    shell_path = os.environ.get("SHELL", "")
    shell_name = Path(shell_path).name if shell_path else ""

    if shell_name in ("bash", "zsh", "fish"):
        return shell_name

    # Fallback to bash
    return "bash"


def _get_config_file(shell: str) -> Path | None:
    """Get the appropriate config file for the shell."""
    configs = SHELL_CONFIGS.get(shell, [])
    for config in configs:
        if config.exists():
            return config
    # Return first option for creation
    return configs[0] if configs else None


def _is_installed(shell: str) -> tuple[bool, Path | None]:
    """Check if completion is already installed for a shell."""
    configs = SHELL_CONFIGS.get(shell, [])
    for config in configs:
        if config.exists():
            content = config.read_text()
            if COMPLETION_MARKER in content:
                return True, config
    return False, None


def _install_completion(shell: str) -> tuple[bool, str]:
    """Install completion for a shell. Returns (success, message)."""
    installed, existing_file = _is_installed(shell)
    if installed:
        return True, f"Already installed in {existing_file}"

    config_file = _get_config_file(shell)
    if config_file is None:
        return False, f"Could not find config file for {shell}"

    script = COMPLETION_SCRIPTS.get(shell)
    if script is None:
        return False, f"Unsupported shell: {shell}"

    # Create parent directory if needed (for fish)
    config_file.parent.mkdir(parents=True, exist_ok=True)

    # Append completion to config file
    completion_block = f"\n{COMPLETION_MARKER}\n{script}{COMPLETION_END_MARKER}\n"

    with open(config_file, "a") as f:
        f.write(completion_block)

    return True, f"Installed to {config_file}"


def _uninstall_completion(shell: str) -> tuple[bool, str]:
    """Uninstall completion for a shell. Returns (success, message)."""
    installed, config_file = _is_installed(shell)
    if not installed:
        return True, f"Not installed for {shell}"

    if config_file is None:
        return False, f"Could not find config file for {shell}"

    content = config_file.read_text()

    # Remove the completion block
    start_idx = content.find(COMPLETION_MARKER)
    end_idx = content.find(COMPLETION_END_MARKER)

    if start_idx == -1 or end_idx == -1:
        return False, "Could not find completion block to remove"

    # Include the newline before marker and after end marker
    if start_idx > 0 and content[start_idx - 1] == "\n":
        start_idx -= 1
    end_idx = end_idx + len(COMPLETION_END_MARKER)
    if end_idx < len(content) and content[end_idx] == "\n":
        end_idx += 1

    new_content = content[:start_idx] + content[end_idx:]
    config_file.write_text(new_content)

    return True, f"Removed from {config_file}"


@click.group("completion", invoke_without_command=True)
@click.pass_context
def completion(ctx):
    """Shell completion commands.

    \b
    Install shell tab-completion for crossref-local CLI.
    Running without subcommand auto-installs for detected shell.

    \b
    Examples:
      crossref-local completion          # Auto-install for current shell
      crossref-local completion status   # Check installation status
      crossref-local completion bash     # Show bash completion script
    """
    if ctx.invoked_subcommand is None:
        # Auto-install for detected shell
        shell = _detect_shell()
        click.echo(f"Detected shell: {shell}")

        success, message = _install_completion(shell)
        if success:
            click.echo(f"[OK] {message}")
            click.echo(
                f"\nRestart your shell or run: source ~/{_get_config_file(shell).name}"
            )
        else:
            click.echo(f"[ERROR] {message}", err=True)
            sys.exit(1)


@completion.command("install")
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    default=None,
    help="Shell to install completion for (default: auto-detect)",
)
def install_cmd(shell: str | None):
    """Install completion to shell config file."""
    if shell is None:
        shell = _detect_shell()
        click.echo(f"Detected shell: {shell}")

    success, message = _install_completion(shell)
    if success:
        click.echo(f"[OK] {message}")
        config_file = _get_config_file(shell)
        if config_file:
            click.echo(f"\nRestart your shell or run: source {config_file}")
    else:
        click.echo(f"[ERROR] {message}", err=True)
        sys.exit(1)


@completion.command("uninstall")
@click.option(
    "--shell",
    type=click.Choice(["bash", "zsh", "fish"]),
    default=None,
    help="Shell to uninstall completion from (default: auto-detect)",
)
def uninstall_cmd(shell: str | None):
    """Remove completion from shell config file."""
    if shell is None:
        shell = _detect_shell()
        click.echo(f"Detected shell: {shell}")

    success, message = _uninstall_completion(shell)
    if success:
        click.echo(f"[OK] {message}")
    else:
        click.echo(f"[ERROR] {message}", err=True)
        sys.exit(1)


@completion.command("status")
def status_cmd():
    """Check completion installation status for all shells."""
    click.echo(f"{PROG_NAME} Shell Completion Status")
    click.echo("=" * 40)

    current_shell = _detect_shell()
    click.echo(f"Current shell: {current_shell}")
    click.echo()

    for shell in ["bash", "zsh", "fish"]:
        installed, config_file = _is_installed(shell)
        marker = "[x]" if installed else "[ ]"
        location = f" ({config_file})" if installed and config_file else ""
        current = " (current)" if shell == current_shell else ""
        click.echo(f"  {marker} {shell}{current}{location}")


@completion.command("bash")
def bash_cmd():
    """Show bash completion script."""
    click.echo(BASH_COMPLETION.strip())


@completion.command("zsh")
def zsh_cmd():
    """Show zsh completion script."""
    click.echo(ZSH_COMPLETION.strip())


@completion.command("fish")
def fish_cmd():
    """Show fish completion script."""
    click.echo(FISH_COMPLETION.strip())


def register_completion_commands(cli_group):
    """Register completion commands with the main CLI group."""
    cli_group.add_command(completion)
