"""
JavaScript code for the basketball statistics website.

The JavaScript template is stored in app.template.js for easier editing
and IDE support.
"""

import os

# Path to the JS template file
_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'app.template.js')

# Cache the template content
_template_cache: str | None = None


def get_javascript(json_data: str) -> str:
    """
    Return the JavaScript code for the website.

    Args:
        json_data: JSON string containing all the statistics data

    Returns:
        JavaScript code as a string
    """
    global _template_cache

    if _template_cache is None:
        with open(_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            _template_cache = f.read()

    return _template_cache.replace('{JSON_DATA_PLACEHOLDER}', json_data)
