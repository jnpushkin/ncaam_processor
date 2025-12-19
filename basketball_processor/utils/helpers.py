"""
Helper utility functions for the basketball processor.
"""

import re
import unicodedata
from datetime import datetime
from typing import Optional, Dict, Any, List

from .constants import TEAM_CODES, DATE_FORMATS, GID_DATE_RE


def normalize_name(name: str) -> str:
    """
    Normalize a player name by removing accents and special characters.

    Args:
        name: Player name string

    Returns:
        Normalized name string
    """
    if not name:
        return ""
    # Normalize unicode characters (e.g., é -> e)
    normalized = unicodedata.normalize('NFKD', name)
    # Remove non-ASCII characters
    ascii_name = normalized.encode('ASCII', 'ignore').decode('ASCII')
    # Clean up whitespace
    return ' '.join(ascii_name.split())


def get_team_code(team_name: str) -> str:
    """
    Get the standardized team code for a team name.

    Args:
        team_name: Full team name or partial match

    Returns:
        Team code string or the original name if not found
    """
    if not team_name:
        return ""

    # Direct lookup
    if team_name in TEAM_CODES:
        return TEAM_CODES[team_name]

    # Try case-insensitive lookup
    team_lower = team_name.lower()
    for name, code in TEAM_CODES.items():
        if name.lower() == team_lower:
            return code

    # Try partial match
    for name, code in TEAM_CODES.items():
        if team_lower in name.lower() or name.lower() in team_lower:
            return code

    # Return original if no match
    return team_name[:4].upper() if len(team_name) >= 4 else team_name.upper()


def parse_date(date_str: str) -> Optional[datetime]:
    """
    Parse a date string using multiple formats.

    Args:
        date_str: Date string to parse

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None

    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue

    return None


def format_date_yyyymmdd(date_str: str) -> str:
    """
    Convert a date string to YYYYMMDD format.

    Args:
        date_str: Date string in various formats

    Returns:
        Date in YYYYMMDD format or empty string if parsing fails
    """
    dt = parse_date(date_str)
    if dt:
        return dt.strftime("%Y%m%d")
    return ""


def generate_game_id(date_str: str, home_team: str, game_num: int = 0, gender: str = 'M') -> str:
    """
    Generate a unique game ID.

    Format: YYYYMMDD-home_team_code[-W for women's][-N for doubleheaders]

    Args:
        date_str: Game date
        home_team: Home team name
        game_num: Game number for doubleheaders (0 = single game)
        gender: 'M' for men's, 'W' for women's

    Returns:
        Game ID string
    """
    date_part = format_date_yyyymmdd(date_str)
    if not date_part:
        date_part = "00000000"

    team_code = get_team_code(home_team).lower()
    gender_suffix = "-w" if gender == 'W' else ""

    if game_num > 0:
        return f"{date_part}-{game_num:02d}-{team_code}{gender_suffix}"
    return f"{date_part}-{team_code}{gender_suffix}"


def parse_minutes(mp_str: str) -> float:
    """
    Parse minutes played string to decimal minutes.

    Handles formats like "35:20" (35 min 20 sec) or just "35"

    Args:
        mp_str: Minutes played string

    Returns:
        Decimal minutes (e.g., 35.33 for 35:20)
    """
    if not mp_str or mp_str == '':
        return 0.0

    mp_str = str(mp_str).strip()

    if ':' in mp_str:
        parts = mp_str.split(':')
        try:
            minutes = int(parts[0])
            seconds = int(parts[1]) if len(parts) > 1 else 0
            return minutes + seconds / 60.0
        except (ValueError, IndexError):
            return 0.0
    else:
        try:
            return float(mp_str)
        except ValueError:
            return 0.0


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    if value is None or value == '':
        return default
    try:
        # Handle percentage strings
        if isinstance(value, str):
            value = value.strip().rstrip('%')
            if value.startswith('.'):
                value = '0' + value
        return float(value)
    except (ValueError, TypeError):
        return default


def create_sports_ref_hyperlink(player_id: str, player_name: str) -> str:
    """
    Create an Excel-compatible hyperlink to Sports Reference player page.

    Args:
        player_id: Sports Reference player ID
        player_name: Player display name

    Returns:
        Excel HYPERLINK formula string
    """
    if not player_id:
        return player_name

    url = f"https://www.sports-reference.com/cbb/players/{player_id}.html"
    return f'=HYPERLINK("{url}", "{player_name}")'


def extract_player_id_from_href(href: str) -> str:
    """
    Extract player ID from Sports Reference href.

    Example: /cbb/players/john-smith-1.html -> john-smith-1

    Args:
        href: Player page href

    Returns:
        Player ID string
    """
    if not href:
        return ""

    # Pattern: /cbb/players/{player_id}.html
    match = re.search(r'/players/([^/]+)\.html', href)
    if match:
        return match.group(1)

    return ""


def calculate_game_score(player_stats: Dict[str, Any]) -> float:
    """
    Calculate John Hollinger's Game Score metric.

    Game Score = PTS + 0.4*FG - 0.7*FGA - 0.4*(FTA-FT) + 0.7*ORB + 0.3*DRB
                 + STL + 0.7*AST + 0.7*BLK - 0.4*PF - TOV

    Args:
        player_stats: Dictionary with player stats

    Returns:
        Game Score value
    """
    pts = safe_float(player_stats.get('pts', 0))
    fg = safe_float(player_stats.get('fg', 0))
    fga = safe_float(player_stats.get('fga', 0))
    ft = safe_float(player_stats.get('ft', 0))
    fta = safe_float(player_stats.get('fta', 0))
    orb = safe_float(player_stats.get('orb', 0))
    drb = safe_float(player_stats.get('drb', 0))
    stl = safe_float(player_stats.get('stl', 0))
    ast = safe_float(player_stats.get('ast', 0))
    blk = safe_float(player_stats.get('blk', 0))
    pf = safe_float(player_stats.get('pf', 0))
    tov = safe_float(player_stats.get('tov', 0))

    game_score = (
        pts
        + 0.4 * fg
        - 0.7 * fga
        - 0.4 * (fta - ft)
        + 0.7 * orb
        + 0.3 * drb
        + stl
        + 0.7 * ast
        + 0.7 * blk
        - 0.4 * pf
        - tov
    )

    return round(game_score, 1)


def sort_games_by_date(games: List[Dict]) -> List[Dict]:
    """
    Sort games list by date (newest first).

    Args:
        games: List of game dictionaries

    Returns:
        Sorted list of games
    """
    def get_date_key(game: Dict) -> datetime:
        basic_info = game.get('basic_info', {})
        date_str = basic_info.get('date_yyyymmdd', '') or basic_info.get('date', '')
        if date_str:
            dt = parse_date(date_str)
            if dt:
                return dt
        return datetime.min

    return sorted(games, key=get_date_key, reverse=True)
