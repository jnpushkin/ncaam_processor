"""
HTML template components for the basketball statistics website.
"""

from .css import get_css
from .javascript import get_javascript
from .html_sections import (
    get_head,
    get_body,
    get_header,
    get_navigation,
    get_main_content,
    get_modals,
)

__all__ = [
    'get_css',
    'get_javascript',
    'get_head',
    'get_body',
    'get_header',
    'get_navigation',
    'get_main_content',
    'get_modals',
]
