"""
Logging utilities for console output.

Provides consistent logging with support for:
- Log levels (DEBUG, INFO, WARN, ERROR)
- Optional emoji support
- Verbose mode for debug output
- Colored output (when supported)
"""

import sys
import re
from datetime import datetime
from typing import Optional
from enum import IntEnum


class LogLevel(IntEnum):
    """Log levels for filtering output."""
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3


# Module-level configuration
_log_level = LogLevel.INFO
_use_emoji = True
_use_color = True
_show_timestamp = False

# ANSI color codes
_COLORS = {
    'reset': '\033[0m',
    'red': '\033[91m',
    'yellow': '\033[93m',
    'green': '\033[92m',
    'blue': '\033[94m',
    'gray': '\033[90m',
}


def set_verbosity(verbose: bool) -> None:
    """Set verbosity level for logging.

    When verbose=True, DEBUG level messages are shown.
    When verbose=False, only INFO and above are shown.
    """
    global _log_level
    _log_level = LogLevel.DEBUG if verbose else LogLevel.INFO


def set_log_level(level: LogLevel) -> None:
    """Set the minimum log level to display."""
    global _log_level
    _log_level = level


def set_use_emoji(use_emoji: bool) -> None:
    """Enable or disable emoji in output."""
    global _use_emoji
    _use_emoji = use_emoji


def set_use_color(use_color: bool) -> None:
    """Enable or disable colored output."""
    global _use_color
    _use_color = use_color


def set_show_timestamp(show: bool) -> None:
    """Enable or disable timestamps in log output."""
    global _show_timestamp
    _show_timestamp = show


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    if not _use_color:
        return False
    # Check if stdout is a TTY
    if not hasattr(sys.stdout, 'isatty') or not sys.stdout.isatty():
        return False
    # Windows cmd doesn't support ANSI by default
    if sys.platform == 'win32':
        return False
    return True


def _colorize(text: str, color: str) -> str:
    """Apply color to text if supported."""
    if _supports_color() and color in _COLORS:
        return f"{_COLORS[color]}{text}{_COLORS['reset']}"
    return text


def _strip_emoji(msg: str) -> str:
    """Remove emoji from message if emoji is disabled."""
    if _use_emoji:
        return msg
    # Simple emoji removal - strips common emoji characters
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', msg).strip()


def _format_message(msg: str, level: str, color: Optional[str] = None) -> str:
    """Format a log message with optional timestamp and level prefix."""
    msg = _strip_emoji(msg)

    parts = []

    if _show_timestamp:
        timestamp = datetime.now().strftime('%H:%M:%S')
        parts.append(_colorize(f"[{timestamp}]", 'gray'))

    if level:
        level_str = f"[{level}]"
        if color:
            level_str = _colorize(level_str, color)
        parts.append(level_str)

    parts.append(msg)

    return ' '.join(parts)


def debug(msg: str) -> None:
    """Print debug message (only if verbose/debug mode enabled)."""
    if _log_level <= LogLevel.DEBUG:
        print(_format_message(msg, 'DEBUG', 'gray'))


def info(msg: str) -> None:
    """Print info message."""
    if _log_level <= LogLevel.INFO:
        print(_strip_emoji(msg))


def warn(msg: str) -> None:
    """Print warning message."""
    if _log_level <= LogLevel.WARN:
        formatted = _format_message(msg, 'WARN', 'yellow') if _show_timestamp or _supports_color() else _strip_emoji(msg)
        print(formatted, file=sys.stderr)


def error(msg: str) -> None:
    """Print error message."""
    if _log_level <= LogLevel.ERROR:
        print(_format_message(msg, 'ERROR', 'red'), file=sys.stderr)


def success(msg: str) -> None:
    """Print success message (always shown)."""
    if _supports_color():
        print(_colorize(_strip_emoji(msg), 'green'))
    else:
        print(_strip_emoji(msg))
