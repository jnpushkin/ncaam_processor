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


class StatsValidationError(Exception):
    """Exception raised when player stats fail validation."""
    pass


def validate_player_stats(
    player_stats: Dict[str, Any],
    game_minutes: int = 40,
    raise_on_error: bool = False
) -> List[str]:
    """
    Validate player stats for logical impossibilities.

    Checks:
    - FG <= FGA (can't make more than you attempt)
    - FT <= FTA (can't make more than you attempt)
    - 3P <= 3PA (can't make more than you attempt)
    - FG <= FGA (field goals include 2s and 3s)
    - Minutes played <= game time (40 min regulation + overtime)
    - All counting stats are non-negative
    - Rebounds = ORB + DRB (if all three present)

    Args:
        player_stats: Dictionary with player stats
        game_minutes: Expected game length (40 for regulation, more for OT)
        raise_on_error: If True, raise StatsValidationError on first error

    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []
    player_name = player_stats.get('player', player_stats.get('name', 'Unknown'))

    # Get stat values with safe defaults
    fg = safe_int(player_stats.get('fg', 0))
    fga = safe_int(player_stats.get('fga', 0))
    fg3 = safe_int(player_stats.get('fg3', player_stats.get('3p', 0)))
    fg3a = safe_int(player_stats.get('fg3a', player_stats.get('3pa', 0)))
    ft = safe_int(player_stats.get('ft', 0))
    fta = safe_int(player_stats.get('fta', 0))
    pts = safe_int(player_stats.get('pts', 0))
    orb = safe_int(player_stats.get('orb', 0))
    drb = safe_int(player_stats.get('drb', 0))
    trb = safe_int(player_stats.get('trb', player_stats.get('reb', 0)))
    ast = safe_int(player_stats.get('ast', 0))
    stl = safe_int(player_stats.get('stl', 0))
    blk = safe_int(player_stats.get('blk', 0))
    tov = safe_int(player_stats.get('tov', player_stats.get('to', 0)))
    pf = safe_int(player_stats.get('pf', 0))

    # Parse minutes (handles "MM:SS" format)
    mp_raw = player_stats.get('mp', player_stats.get('min', 0))
    mp = parse_minutes(str(mp_raw)) if mp_raw else 0

    # Check non-negative counting stats
    counting_stats = {
        'FG': fg, 'FGA': fga, 'FG3': fg3, 'FG3A': fg3a, 'FT': ft, 'FTA': fta,
        'PTS': pts, 'ORB': orb, 'DRB': drb, 'TRB': trb, 'AST': ast,
        'STL': stl, 'BLK': blk, 'TOV': tov, 'PF': pf
    }
    for stat_name, stat_val in counting_stats.items():
        if stat_val < 0:
            err = f"{player_name}: {stat_name} cannot be negative ({stat_val})"
            errors.append(err)
            if raise_on_error:
                raise StatsValidationError(err)

    # Check makes <= attempts
    if fga > 0 and fg > fga:
        err = f"{player_name}: FG ({fg}) > FGA ({fga})"
        errors.append(err)
        if raise_on_error:
            raise StatsValidationError(err)

    if fg3a > 0 and fg3 > fg3a:
        err = f"{player_name}: 3P ({fg3}) > 3PA ({fg3a})"
        errors.append(err)
        if raise_on_error:
            raise StatsValidationError(err)

    if fta > 0 and ft > fta:
        err = f"{player_name}: FT ({ft}) > FTA ({fta})"
        errors.append(err)
        if raise_on_error:
            raise StatsValidationError(err)

    # Check 3-pointers are subset of field goals
    if fga > 0 and fg3 > fg:
        err = f"{player_name}: 3P made ({fg3}) > total FG made ({fg})"
        errors.append(err)
        if raise_on_error:
            raise StatsValidationError(err)

    # Check rebounds add up (if all three stats present and non-zero)
    if orb > 0 or drb > 0:
        if trb > 0 and trb != (orb + drb):
            err = f"{player_name}: TRB ({trb}) != ORB ({orb}) + DRB ({drb})"
            errors.append(err)
            if raise_on_error:
                raise StatsValidationError(err)

    # Check minutes within bounds (with buffer for overtime)
    max_minutes = game_minutes + 25  # Allow up to 5 OT periods
    if mp > max_minutes:
        err = f"{player_name}: Minutes ({mp:.1f}) exceeds max possible ({max_minutes})"
        errors.append(err)
        if raise_on_error:
            raise StatsValidationError(err)

    # Check points formula: PTS should equal 3*3P + 2*(FG-3P) + FT
    if pts > 0 and fg >= 0 and fg3 >= 0 and ft >= 0:
        expected_pts = 3 * fg3 + 2 * (fg - fg3) + ft
        if pts != expected_pts and fga > 0:  # Only check if we have shooting stats
            err = f"{player_name}: PTS ({pts}) doesn't match formula (expected {expected_pts})"
            errors.append(err)
            if raise_on_error:
                raise StatsValidationError(err)

    # Check fouls (max 5 in college, 6 in NBA - use 6 as upper bound)
    if pf > 6:
        err = f"{player_name}: Personal fouls ({pf}) exceeds maximum (6)"
        errors.append(err)
        if raise_on_error:
            raise StatsValidationError(err)

    return errors


def validate_game_stats(game_data: Dict[str, Any]) -> List[str]:
    """
    Validate all player stats in a game.

    Args:
        game_data: Full game data dictionary

    Returns:
        List of all validation errors across all players
    """
    all_errors = []

    # Determine game length (check for overtime)
    basic_info = game_data.get('basic_info', {})
    # Default to 40 min for college, could be 48 for NBA
    game_minutes = 40

    box_score = game_data.get('box_score', {})
    for team_key in ['away', 'home']:
        team_data = box_score.get(team_key, {})
        players = team_data.get('players', [])
        for player in players:
            errors = validate_player_stats(player, game_minutes=game_minutes)
            all_errors.extend(errors)

    return all_errors


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
