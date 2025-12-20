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
from .templates import get_css, get_javascript, get_head, get_body
from ..utils.log import info


def generate_website_from_data(processed_data: Dict[str, Any], output_path: str) -> None:
    """
    Generate interactive HTML website from processed data.

    Args:
        processed_data: Dictionary containing processed DataFrames
        output_path: Path to save the HTML file
    """
    info(f"Generating website: {output_path}")

    # Get raw games if available
    raw_games = processed_data.get('_raw_games', [])

    # Serialize data
    serializer = DataSerializer(processed_data, raw_games)
    data = serializer.serialize_all()
    json_data = json.dumps(data, default=str)

    # Generate HTML
    html_content = _generate_html(json_data, data.get('summary', {}))

    # Write file
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    info(f"Website saved: {output_path}")


def _generate_html(json_data: str, summary: Dict[str, Any]) -> str:
    """
    Generate the HTML content by assembling template components.

    Args:
        json_data: JSON string containing serialized game/player data
        summary: Dictionary with totalGames, totalPlayers, totalTeams

    Returns:
        Complete HTML document as a string
    """
    total_games = summary.get('totalGames', 0)
    total_players = summary.get('totalPlayers', 0)
    total_teams = summary.get('totalTeams', 0)
    total_venues = summary.get('totalVenues', 0)
    total_points = summary.get('totalPoints', 0)
    future_pros = summary.get('futurePros', 0)
    generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Get template components
    css = get_css()
    js = get_javascript(json_data)
    head = get_head(css)
    body = get_body(total_games, total_players, total_teams, total_venues, total_points, future_pros, generated_time)

    # Assemble the final HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
{head}
{body}

    <script>
{js}
    </script>
</body>
</html>'''

    return html
