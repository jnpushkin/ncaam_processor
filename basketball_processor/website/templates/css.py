"""
CSS styles for the basketball statistics website.

The CSS is stored in styles.css for easier editing and IDE support.
"""

import os

# Path to the CSS file
_CSS_PATH = os.path.join(os.path.dirname(__file__), 'styles.css')

# Cache the CSS content
_css_cache: str | None = None


def get_css() -> str:
    """Return the CSS styles for the website."""
    global _css_cache

    if _css_cache is None:
        with open(_CSS_PATH, 'r', encoding='utf-8') as f:
            _css_cache = f.read()

    return _css_cache
