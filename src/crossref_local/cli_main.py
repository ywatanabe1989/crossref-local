"""Main CLI entry point with all command groups registered."""

from .cli import cli
from .cli_cache import register_cache_commands
from .cli_completion import register_completion_commands
from .cli_mcp import register_mcp_commands

# Register command groups
register_cache_commands(cli)
register_completion_commands(cli)
register_mcp_commands(cli)


def main():
    """Entry point for CLI."""
    cli()


if __name__ == "__main__":
    main()
