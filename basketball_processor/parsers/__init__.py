"""HTML parsing modules for Sports Reference box scores."""

from .html_parser import parse_sports_reference_boxscore
from .stats_parser import extract_player_stats, extract_team_totals

__all__ = [
    'parse_sports_reference_boxscore',
    'extract_player_stats',
    'extract_team_totals',
]
