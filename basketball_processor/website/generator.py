"""
Website generator for interactive HTML output.

This module generates only data.js from processed data.
Frontend files (index.html, styles.css, app.js, geo-data.js) are maintained
directly in docs/ and are not generated.
"""

import os
import json
from typing import Dict, Any

from .serializers import DataSerializer
from ..utils.log import info


def generate_website_from_data(processed_data: Dict[str, Any], output_path: str, skip_nba: bool = False) -> None:
    """
    Generate data.js from processed data.

    Only writes data.js — the frontend files (index.html, styles.css, app.js,
    geo-data.js) are maintained directly in docs/ and not overwritten.

    Args:
        processed_data: Dictionary containing processed DataFrames
        output_path: Path to the output directory (or HTML file path for backwards compat)
        skip_nba: If True, skip NBA/WNBA player lookups for faster generation
    """
    info(f"Generating website data: {output_path}")

    # Get raw games if available
    raw_games = processed_data.get('_raw_games', [])

    # Serialize data
    serializer = DataSerializer(processed_data, raw_games)
    data = serializer.serialize_all(skip_nba=skip_nba)
    json_data = json.dumps(data, indent=2, default=str)

    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Write data.js (the only generated file)
    data_path = os.path.join(output_dir, 'data.js')
    with open(data_path, 'w', encoding='utf-8') as f:
        f.write(f'const DATA = {json_data};')
    info(f"  - data.js ({len(json_data):,} bytes)")

    info(f"Website data saved: {data_path}")
