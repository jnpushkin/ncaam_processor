"""HTML parsing modules for college basketball box scores."""

from .html_parser import (
    parse_sports_reference_boxscore,
    validate_html_content,
    validate_game_data,
    HTMLParsingError,
)
from .stats_parser import extract_player_stats, extract_team_totals
from .sidearm_parser import (
    parse_sidearm_boxscore,
    is_sidearm_format,
    SidearmParsingError,
)

__all__ = [
    'parse_sports_reference_boxscore',
    'validate_html_content',
    'validate_game_data',
    'HTMLParsingError',
    'extract_player_stats',
    'extract_team_totals',
    'parse_sidearm_boxscore',
    'is_sidearm_format',
    'SidearmParsingError',
]
