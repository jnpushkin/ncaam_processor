"""
Logging utilities for console output.

Provides consistent logging with support for:
- Log levels (DEBUG, INFO, WARN, ERROR)
- Optional emoji support
- Verbose mode for debug output
- Colored output (when supported)
- Exception logging with full tracebacks
- Optional file logging
- Caller context (file, function, line number)
"""

import sys
import re
import traceback
import inspect
from datetime import datetime
from typing import Optional, TextIO
from enum import IntEnum
from pathlib import Path


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
_show_caller = False  # Show file:line:function context
_log_file: Optional[TextIO] = None
_log_file_path: Optional[Path] = None

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


def set_show_caller(show: bool) -> None:
    """Enable or disable caller context (file:line:function) in log output."""
    global _show_caller
    _show_caller = show


def set_log_file(path: Optional[str]) -> None:
    """
    Enable file logging by setting a log file path.

    Args:
        path: Path to log file, or None to disable file logging
    """
    global _log_file, _log_file_path

    # Close existing log file if open
    if _log_file is not None:
        try:
            _log_file.close()
        except Exception:
            pass
        _log_file = None
        _log_file_path = None

    if path is not None:
        try:
            _log_file_path = Path(path)
            _log_file_path.parent.mkdir(parents=True, exist_ok=True)
            _log_file = open(_log_file_path, 'a', encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not open log file {path}: {e}", file=sys.stderr)
            _log_file = None
            _log_file_path = None


def get_log_file_path() -> Optional[Path]:
    """Return the current log file path, or None if file logging is disabled."""
    return _log_file_path


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


def _get_caller_info(stack_depth: int = 3) -> str:
    """
    Get caller context (file:line:function).

    Args:
        stack_depth: How many frames to go back (default 3 for log functions)

    Returns:
        String like "main.py:42:process_game"
    """
    try:
        frame = inspect.currentframe()
        for _ in range(stack_depth):
            if frame is not None:
                frame = frame.f_back
        if frame is not None:
            filename = Path(frame.f_code.co_filename).name
            lineno = frame.f_lineno
            funcname = frame.f_code.co_name
            return f"{filename}:{lineno}:{funcname}"
    except Exception:
        pass
    return "unknown"


def _format_message(msg: str, level: str, color: Optional[str] = None, include_caller: bool = True) -> str:
    """Format a log message with optional timestamp, level prefix, and caller context."""
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

    if _show_caller and include_caller:
        caller = _get_caller_info(stack_depth=4)
        parts.append(_colorize(f"[{caller}]", 'gray'))

    parts.append(msg)

    return ' '.join(parts)


def _format_message_plain(msg: str, level: str, include_caller: bool = True) -> str:
    """Format a log message for file output (no colors)."""
    msg = _strip_emoji(msg)
    parts = []

    # Always include timestamp in file logs
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    parts.append(f"[{timestamp}]")

    if level:
        parts.append(f"[{level}]")

    if include_caller:
        caller = _get_caller_info(stack_depth=5)
        parts.append(f"[{caller}]")

    parts.append(msg)

    return ' '.join(parts)


def _write_to_file(msg: str, level: str, include_caller: bool = True) -> None:
    """Write a log message to the log file if enabled."""
    if _log_file is not None:
        try:
            plain_msg = _format_message_plain(msg, level, include_caller)
            _log_file.write(plain_msg + '\n')
            _log_file.flush()
        except Exception:
            pass  # Don't let file logging errors break the application


def debug(msg: str) -> None:
    """Print debug message (only if verbose/debug mode enabled)."""
    if _log_level <= LogLevel.DEBUG:
        print(_format_message(msg, 'DEBUG', 'gray'))
        _write_to_file(msg, 'DEBUG')


def info(msg: str) -> None:
    """Print info message."""
    if _log_level <= LogLevel.INFO:
        formatted = _format_message(msg, 'INFO', 'blue') if _show_timestamp or _supports_color() or _show_caller else _strip_emoji(msg)
        print(formatted)
        _write_to_file(msg, 'INFO')


def warn(msg: str) -> None:
    """Print warning message."""
    if _log_level <= LogLevel.WARN:
        formatted = _format_message(msg, 'WARN', 'yellow') if _show_timestamp or _supports_color() or _show_caller else _strip_emoji(msg)
        print(formatted, file=sys.stderr)
        _write_to_file(msg, 'WARN')


def error(msg: str) -> None:
    """Print error message."""
    if _log_level <= LogLevel.ERROR:
        print(_format_message(msg, 'ERROR', 'red'), file=sys.stderr)
        _write_to_file(msg, 'ERROR')


def exception(msg: str, exc: Optional[BaseException] = None, include_traceback: bool = True) -> None:
    """
    Log an error message with optional exception details and traceback.

    This is the preferred way to log exceptions - it captures full context
    and writes to both console and log file.

    Args:
        msg: Error message describing what went wrong
        exc: Optional exception object (if None, uses current exception from sys.exc_info)
        include_traceback: Whether to include the full stack trace (default True)

    Example:
        try:
            process_game(data)
        except ValueError as e:
            exception(f"Failed to process game {game_id}", e)
    """
    # Print the main error message
    error(msg)

    # Get exception info
    if exc is None:
        exc_info = sys.exc_info()
        exc = exc_info[1]
    else:
        exc_info = (type(exc), exc, exc.__traceback__)

    if exc is not None:
        # Print exception type and message
        exc_msg = f"  {type(exc).__name__}: {exc}"
        print(_colorize(exc_msg, 'red'), file=sys.stderr)
        _write_to_file(exc_msg, 'ERROR', include_caller=False)

        # Print traceback if requested
        if include_traceback and exc_info[2] is not None:
            tb_lines = traceback.format_exception(*exc_info)
            tb_str = ''.join(tb_lines)
            # Print to stderr (with color if supported)
            if _supports_color():
                print(_colorize(tb_str, 'red'), file=sys.stderr)
            else:
                print(tb_str, file=sys.stderr)
            # Write to log file
            if _log_file is not None:
                try:
                    _log_file.write(tb_str)
                    _log_file.flush()
                except Exception:
                    pass


def warn_once(msg: str, key: Optional[str] = None) -> None:
    """
    Print a warning message only once per unique key.

    Useful for warnings that might occur many times in a loop but
    should only be shown once.

    Args:
        msg: Warning message
        key: Unique key for deduplication (defaults to msg)
    """
    if not hasattr(warn_once, '_seen'):
        warn_once._seen = set()

    dedupe_key = key or msg
    if dedupe_key not in warn_once._seen:
        warn_once._seen.add(dedupe_key)
        warn(msg)


def success(msg: str) -> None:
    """Print success message (always shown)."""
    if _supports_color():
        print(_colorize(_strip_emoji(msg), 'green'))
    else:
        print(_strip_emoji(msg))
    _write_to_file(msg, 'SUCCESS')
