"""
ESPN scraper for attendance data.

Fetches attendance from ESPN boxscores when SIDEARM sites don't have it.
"""

import json
import re
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
import requests

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between requests

# ESPN API endpoints
ESPN_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
ESPN_BOXSCORE_URL = "https://www.espn.com/mens-college-basketball/boxscore/_/gameId/{game_id}"

# Team name mappings from our names to ESPN names
TEAM_NAME_MAP = {
    "Saint Mary's": "Saint Mary's",
    "Saint Mary's (CA)": "Saint Mary's",
    "UConn": "Connecticut",
    "Connecticut": "Connecticut",
    "Miami (FL)": "Miami",
    "NC State": "NC State",
    "UNC": "North Carolina",
    "North Carolina": "North Carolina",
    "Pitt": "Pittsburgh",
    "Pittsburgh": "Pittsburgh",
    "USC": "USC",
    "Cal": "California",
    "St. Francis (NY)": "St. Francis (BKN)",
    "Saint Francis (PA)": "Saint Francis (PA)",
}


def normalize_team_name(name: str) -> str:
    """Normalize team name for ESPN matching."""
    return TEAM_NAME_MAP.get(name, name)


def _fetch_espn_scoreboard(date_str: str) -> Optional[Dict]:
    """
    Fetch ESPN scoreboard for a specific date.

    Args:
        date_str: Date in YYYYMMDD format

    Returns:
        Scoreboard JSON data or None
    """
    try:
        url = f"{ESPN_SCOREBOARD_URL}?dates={date_str}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"  ESPN scoreboard error: {e}")
    return None


def _find_game_id(scoreboard: Dict, home_team: str, away_team: str) -> Optional[str]:
    """
    Find ESPN game ID from scoreboard data.

    Args:
        scoreboard: ESPN scoreboard JSON
        home_team: Home team name
        away_team: Away team name

    Returns:
        ESPN game ID or None
    """
    home_norm = normalize_team_name(home_team).lower()
    away_norm = normalize_team_name(away_team).lower()

    events = scoreboard.get('events', [])

    for event in events:
        competitions = event.get('competitions', [])
        for comp in competitions:
            competitors = comp.get('competitors', [])
            if len(competitors) != 2:
                continue

            teams = {}
            for c in competitors:
                team_name = c.get('team', {}).get('displayName', '').lower()
                team_short = c.get('team', {}).get('shortDisplayName', '').lower()
                team_abbrev = c.get('team', {}).get('abbreviation', '').lower()
                home_away = c.get('homeAway', '')

                teams[home_away] = {
                    'name': team_name,
                    'short': team_short,
                    'abbrev': team_abbrev
                }

            # Check if this is our game
            home_match = False
            away_match = False

            if 'home' in teams:
                h = teams['home']
                if home_norm in h['name'] or home_norm in h['short'] or h['name'] in home_norm:
                    home_match = True

            if 'away' in teams:
                a = teams['away']
                if away_norm in a['name'] or away_norm in a['short'] or a['name'] in away_norm:
                    away_match = True

            if home_match and away_match:
                return event.get('id')

    return None


# ESPN team IDs for common teams
ESPN_TEAM_IDS = {
    'Virginia': 258,
    'Duke': 150,
    'North Carolina': 153,
    'UNC': 153,
    'Maryland': 120,
    'Towson': 119,
    'Drexel': 2182,
    'Florida Gulf Coast': 526,
    'St. Francis (NY)': 2597,
    'Saint Francis (PA)': 2598,
    'Youngstown State': 2754,
    'San Francisco': 2608,
    'Memphis': 235,
    'Saint Louis': 139,
}


def _search_team_schedule(team_name: str, opponent: str, game_date: str) -> Optional[str]:
    """
    Search a team's ESPN schedule for a specific game.

    Args:
        team_name: Team to search schedule for
        opponent: Opponent team name
        game_date: Date in YYYYMMDD format

    Returns:
        ESPN game ID or None
    """
    team_id = ESPN_TEAM_IDS.get(team_name)
    if not team_id:
        return None

    # Determine season year (Nov-Dec = current year, Jan-Apr = previous year for season)
    year = int(game_date[:4])
    month = int(game_date[4:6])
    if month >= 8:  # Aug-Dec
        season = year + 1  # e.g., Nov 2016 = 2017 season
    else:
        season = year  # e.g., Feb 2017 = 2017 season

    try:
        url = f"https://www.espn.com/mens-college-basketball/team/schedule/_/id/{team_id}/season/{season}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        html = response.text
        opponent_norm = normalize_team_name(opponent).lower()

        # Parse date for matching
        dt = datetime.strptime(game_date, '%Y%m%d')
        date_patterns = [
            dt.strftime('%b %d'),  # "Feb 15"
            dt.strftime('%B %d'),  # "February 15"
            dt.strftime('%-m/%-d'),  # "2/15"
        ]

        # Find game links with opponent
        # Pattern: /gameId/(\d+)
        game_ids = re.findall(r'/gameId/(\d+)', html)

        # Look for opponent name near game IDs
        for game_id in game_ids:
            # Get context around this game ID
            idx = html.find(f'/gameId/{game_id}')
            if idx > 0:
                context = html[max(0, idx-500):idx+200].lower()
                # Check if opponent is in context
                if opponent_norm in context or opponent.lower() in context:
                    # Check if date matches
                    for pattern in date_patterns:
                        if pattern.lower() in context:
                            return game_id

        return None

    except Exception as e:
        print(f"  ESPN schedule search error: {e}")
        return None


def _fetch_boxscore_attendance(game_id: str) -> Optional[int]:
    """
    Fetch attendance from ESPN boxscore page.

    Args:
        game_id: ESPN game ID

    Returns:
        Attendance as integer or None
    """
    try:
        url = ESPN_BOXSCORE_URL.format(game_id=game_id)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        html = response.text

        # Look for attendance in various patterns
        patterns = [
            r'"attnd"\s*:\s*(\d+)',
            r'"attendance"\s*:\s*(\d+)',
            r'Attendance[:\s]+([0-9,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                att_str = match.group(1).replace(',', '')
                return int(att_str)

    except Exception as e:
        print(f"  ESPN boxscore error: {e}")

    return None


def get_espn_attendance(
    home_team: str,
    away_team: str,
    game_date: str,
    verbose: bool = True
) -> Optional[int]:
    """
    Get attendance from ESPN for a specific game.

    Args:
        home_team: Home team name
        away_team: Away team name
        game_date: Date in YYYYMMDD format
        verbose: Print status messages

    Returns:
        Attendance as integer or None
    """
    if verbose:
        print(f"  Checking ESPN for {away_team} @ {home_team} ({game_date})...")

    # Fetch scoreboard for the date
    scoreboard = _fetch_espn_scoreboard(game_date)
    if not scoreboard:
        if verbose:
            print(f"  ESPN scoreboard not available for {game_date}")
        return None

    time.sleep(RATE_LIMIT_DELAY)

    # Find game ID
    game_id = _find_game_id(scoreboard, home_team, away_team)
    if not game_id:
        if verbose:
            print(f"  Game not found in ESPN scoreboard")
        return None

    if verbose:
        print(f"  Found ESPN game ID: {game_id}")

    # Fetch attendance
    attendance = _fetch_boxscore_attendance(game_id)
    if attendance and verbose:
        print(f"  ESPN attendance: {attendance:,}")

    return attendance


def supplement_with_espn(
    home_team: str,
    away_team: str,
    game_date: str,
    gender: str = 'M',
    verbose: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get game data from ESPN as a fallback.

    Currently only fetches attendance.

    Args:
        home_team: Home team name
        away_team: Away team name
        game_date: Date in YYYYMMDD format
        gender: 'M' or 'W' (only men's supported currently)
        verbose: Print status messages

    Returns:
        Dict with attendance or None
    """
    # Only men's basketball for now
    if gender != 'M':
        return None

    attendance = get_espn_attendance(home_team, away_team, game_date, verbose)

    if attendance:
        return {
            'attendance': attendance,
            'source': 'espn'
        }

    return None


if __name__ == '__main__':
    # Test with Duke @ Virginia Feb 9, 2019
    result = get_espn_attendance(
        home_team='Virginia',
        away_team='Duke',
        game_date='20190209',
        verbose=True
    )
    print(f"\nResult: {result}")
