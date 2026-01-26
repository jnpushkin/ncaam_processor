"""
Website generator for interactive HTML output.

This module serves as a thin orchestrator that assembles HTML output
from template components defined in the templates/ subdirectory.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

from .serializers import DataSerializer
from .templates import get_css, get_body
from ..utils.log import info


def generate_website_from_data(processed_data: Dict[str, Any], output_path: str, skip_nba: bool = False) -> None:
    """
    Generate interactive HTML website from processed data.

    Outputs separate files for better maintainability:
    - index.html: HTML structure with external file references
    - styles.css: CSS styles
    - app.js: JavaScript application code
    - data.js: JSON data as a JavaScript variable

    Args:
        processed_data: Dictionary containing processed DataFrames
        output_path: Path to save the HTML file (other files saved in same directory)
        skip_nba: If True, skip NBA/WNBA player lookups for faster generation
    """
    info(f"Generating website: {output_path}")

    # Get raw games if available
    raw_games = processed_data.get('_raw_games', [])

    # Serialize data
    serializer = DataSerializer(processed_data, raw_games)
    data = serializer.serialize_all(skip_nba=skip_nba)
    # Use indent for debuggability (grep-friendly) - size increase is minimal for static files
    json_data = json.dumps(data, indent=2, default=str)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get template components
    css = get_css()
    summary = data.get('summary', {})

    # Write separate files
    _write_separate_files(output_dir, css, json_data, summary)

    info(f"Website saved: {output_path}")


def _write_separate_files(output_dir: str, css: str, json_data: str, summary: Dict[str, Any]) -> None:
    """
    Write website as separate files for better maintainability.

    Args:
        output_dir: Directory to write files to
        css: CSS content
        json_data: JSON data string
        summary: Summary stats for the HTML template
    """
    total_games = summary.get('totalGames', 0)
    total_players = summary.get('totalPlayers', 0)
    total_teams = summary.get('totalTeams', 0)
    total_venues = summary.get('totalVenues', 0)
    total_points = summary.get('totalPoints', 0)
    ranked_matchups = summary.get('rankedMatchups', 0)
    upsets = summary.get('upsets', 0)
    future_pros = summary.get('futurePros', 0)
    generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Write CSS
    css_path = os.path.join(output_dir, 'styles.css')
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
    info(f"  - styles.css ({len(css):,} bytes)")

    # Write data.js (data as a JavaScript variable)
    data_path = os.path.join(output_dir, 'data.js')
    with open(data_path, 'w', encoding='utf-8') as f:
        f.write(f'const DATA = {json_data};')
    info(f"  - data.js ({len(json_data):,} bytes)")

    # Write app.js - read template and remove the DATA placeholder line
    # (DATA will be loaded from data.js)
    from .templates.javascript import _TEMPLATE_PATH
    with open(_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
        js_template = f.read()
    # Remove the first line which is "const DATA = {JSON_DATA_PLACEHOLDER};"
    js_lines = js_template.split('\n')
    if js_lines[0].startswith('const DATA ='):
        js_lines[0] = '// DATA is loaded from data.js'
    js_content = '\n'.join(js_lines)
    app_path = os.path.join(output_dir, 'app.js')
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
    info(f"  - app.js ({len(js_content):,} bytes)")

    # Write index.html with external file references
    body = get_body(total_games, total_players, total_teams, total_venues, total_points, ranked_matchups, upsets, future_pros, generated_time)

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>College Basketball Stats</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <link rel="stylesheet" href="styles.css">
</head>
{body}
    <script src="data.js"></script>
    <script src="app.js"></script>
</body>
</html>'''

    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html)
    info(f"  - index.html ({len(html):,} bytes)")
