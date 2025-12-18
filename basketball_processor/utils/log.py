"""
Simple logging utilities for console output.
"""

_verbose = False
_use_emoji = True


def set_verbosity(verbose: bool):
    """Set verbosity level for logging."""
    global _verbose
    _verbose = verbose


def set_use_emoji(use_emoji: bool):
    """Enable or disable emoji in output."""
    global _use_emoji
    _use_emoji = use_emoji


def _strip_emoji(msg: str) -> str:
    """Remove emoji from message if emoji is disabled."""
    if _use_emoji:
        return msg
    # Simple emoji removal - strips common emoji characters
    import re
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


def info(msg: str):
    """Print info message."""
    print(_strip_emoji(msg))


def warn(msg: str):
    """Print warning message."""
    print(_strip_emoji(msg))


def debug(msg: str):
    """Print debug message (only if verbose)."""
    if _verbose:
        print(_strip_emoji(f"[DEBUG] {msg}"))
