"""
ESPN play-by-play scraper.

Fetches play-by-play data from ESPN API for detailed game analysis.
Falls back to ncaahoopR GitHub data for older games (2002-03 to 2016-17).

Data sources:
- ESPN API: Games from 2017-18 season onwards
- ncaahoopR: Games from 2002-03 to present (fallback for older games)
  https://github.com/lbenz730/ncaahoopR_data
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

import requests

from .constants import BASE_DIR, TEAM_ALIASES

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between requests
_last_request_time = 0.0

# ESPN API endpoints (using /summary endpoint which includes play-by-play)
ESPN_PBP_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/summary"
ESPN_WOMENS_PBP_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/summary"

# Cache directory
CACHE_DIR = BASE_DIR / "cache" / "espn_pbp"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Schedule cache files
SCHEDULE_CACHE_FILE = BASE_DIR / "data" / "schedule_cache.json"
SCHEDULE_CACHE_FILE_WOMENS = BASE_DIR / "data" / "schedule_cache_womens.json"


def _rate_limit():
    """Enforce rate limiting between requests."""
    global _last_request_time
    current_time = time.time()
    elapsed = current_time - _last_request_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    _last_request_time = time.time()


def _normalize_team_name(name: str) -> str:
    """Normalize team name for matching."""
    if not name:
        return ''
    # First try direct alias lookup
    if name in TEAM_ALIASES:
        name = TEAM_ALIASES[name]
    # Clean up common variations
    name = name.replace("'", "").replace(".", "").replace("-", " ")
    name = name.replace("(", "").replace(")", "")  # Remove parentheses
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name


def get_espn_id_from_cache(
    away_team: str,
    home_team: str,
    date_yyyymmdd: str,
    gender: str = 'M'
) -> Optional[str]:
    """
    Find ESPN game ID from schedule cache.

    Args:
        away_team: Away team name
        home_team: Home team name
        date_yyyymmdd: Game date in YYYYMMDD format
        gender: 'M' for men's, 'W' for women's

    Returns:
        ESPN game ID or None if not found
    """
    # Use gender-specific cache file
    cache_file = SCHEDULE_CACHE_FILE_WOMENS if gender == 'W' else SCHEDULE_CACHE_FILE

    if not cache_file.exists():
        return _lookup_espn_id_from_scoreboard(away_team, home_team, date_yyyymmdd, gender)

    try:
        with open(cache_file, 'r') as f:
            cache = json.load(f)
    except (json.JSONDecodeError, IOError):
        return _lookup_espn_id_from_scoreboard(away_team, home_team, date_yyyymmdd, gender)

    games = cache.get('games', [])
    if not games:
        return _lookup_espn_id_from_scoreboard(away_team, home_team, date_yyyymmdd, gender)

    # Convert date to comparable format
    # Schedule cache uses ISO format: "2026-01-16T01:00Z"
    # We need to match on the date portion
    try:
        target_date = datetime.strptime(date_yyyymmdd, '%Y%m%d').date()
    except ValueError:
        return None

    away_norm = _normalize_team_name(away_team)
    home_norm = _normalize_team_name(home_team)

    for game in games:
        # Parse game date from ISO format
        game_date_str = game.get('date', '')
        try:
            # Handle both "2026-01-16T01:00Z" and "2026-01-16" formats
            if 'T' in game_date_str:
                game_dt = datetime.fromisoformat(game_date_str.replace('Z', '+00:00'))
            else:
                game_dt = datetime.fromisoformat(game_date_str)
            game_date = game_dt.date()
        except (ValueError, AttributeError):
            continue

        # ESPN dates can be off by one due to timezone (late night games)
        # Check if within 1 day
        date_diff = abs((game_date - target_date).days)
        if date_diff > 1:
            continue

        # Match teams
        espn_home = game.get('home_team', {})
        espn_away = game.get('away_team', {})

        # Try various name fields
        espn_home_names = [
            _normalize_team_name(espn_home.get('name', '')),
            _normalize_team_name(espn_home.get('short_name', '')),
            _normalize_team_name(espn_home.get('abbreviation', '')),
        ]
        espn_away_names = [
            _normalize_team_name(espn_away.get('name', '')),
            _normalize_team_name(espn_away.get('short_name', '')),
            _normalize_team_name(espn_away.get('abbreviation', '')),
        ]

        # Check for matches
        home_match = any(home_norm in n or n in home_norm for n in espn_home_names if n)
        away_match = any(away_norm in n or n in away_norm for n in espn_away_names if n)

        if home_match and away_match:
            return game.get('espn_id')

    # Not found in cache - try live scoreboard lookup
    return _lookup_espn_id_from_scoreboard(away_team, home_team, date_yyyymmdd, gender)


def _lookup_espn_id_from_scoreboard(
    away_team: str,
    home_team: str,
    date_yyyymmdd: str,
    gender: str = 'M'
) -> Optional[str]:
    """
    Look up ESPN game ID from ESPN's scoreboard API.

    Args:
        away_team: Away team name
        home_team: Home team name
        date_yyyymmdd: Game date in YYYYMMDD format
        gender: 'M' for men's, 'W' for women's

    Returns:
        ESPN game ID or None if not found
    """
    _rate_limit()

    # Build scoreboard URL
    if gender == 'W':
        base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard"
    else:
        base_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"

    # Include groups=50 for D1 and limit=400 to get all games
    url = f"{base_url}?dates={date_yyyymmdd}&groups=50&limit=400"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None

        data = response.json()
        events = data.get('events', [])

        away_norm = _normalize_team_name(away_team)
        home_norm = _normalize_team_name(home_team)

        for event in events:
            # Get competitors
            competitions = event.get('competitions', [])
            if not competitions:
                continue

            comp = competitions[0]
            competitors = comp.get('competitors', [])

            espn_home = None
            espn_away = None

            for c in competitors:
                team = c.get('team', {})
                team_names = [
                    _normalize_team_name(team.get('displayName', '')),
                    _normalize_team_name(team.get('shortDisplayName', '')),
                    _normalize_team_name(team.get('name', '')),
                ]
                if c.get('homeAway') == 'home':
                    espn_home = team_names
                else:
                    espn_away = team_names

            if espn_home and espn_away:
                home_match = any(home_norm in n or n in home_norm for n in espn_home if n)
                away_match = any(away_norm in n or n in away_norm for n in espn_away if n)

                if home_match and away_match:
                    return event.get('id')

    except (requests.RequestException, json.JSONDecodeError):
        pass

    # Also try ncaahoopR schedule lookup for older games
    return _lookup_espn_id_from_ncaahoopr(away_team, home_team, date_yyyymmdd)


# ncaahoopR team name mappings (team name -> ncaahoopR schedule file name)
NCAAHOOPR_TEAM_NAMES = {
    'virginia': 'UVA',
    'virginia cavaliers': 'UVA',
    'uva': 'UVA',
    'north carolina': 'North_Carolina',
    'unc': 'North_Carolina',
    'tar heels': 'North_Carolina',
    'duke': 'Duke',
    'duke blue devils': 'Duke',
    'kentucky': 'Kentucky',
    'kansas': 'Kansas',
    'gonzaga': 'Gonzaga',
    'michigan state': 'Michigan_State',
    'michigan st': 'Michigan_State',
    'ohio state': 'Ohio_State',
    'ohio st': 'Ohio_State',
    'florida state': 'Florida_State',
    'florida st': 'Florida_State',
    'nc state': 'NC_State',
    'north carolina state': 'NC_State',
    'penn state': 'Penn_State',
    'san diego state': 'San_Diego_State',
    'san diego st': 'San_Diego_State',
    'texas a&m': 'Texas_A&M',
    'texas am': 'Texas_A&M',
    'uconn': 'Connecticut',
    'connecticut': 'Connecticut',
    'lsu': 'LSU',
    'louisiana state': 'LSU',
    'smu': 'SMU',
    'southern methodist': 'SMU',
    'ucf': 'UCF',
    'central florida': 'UCF',
    'usc': 'USC',
    'southern california': 'USC',
    'ucla': 'UCLA',
    'pitt': 'Pittsburgh',
    'pittsburgh': 'Pittsburgh',
    # Additional mappings for common teams
    'california': 'Cal',
    'cal': 'Cal',
    'california golden bears': 'Cal',
    'san francisco': 'San_Francisco',
    'san francisco dons': 'San_Francisco',
    'usf': 'San_Francisco',
    'florida gulf coast': 'FGCU',
    'fgcu': 'FGCU',
    'maryland': 'Maryland',
    'maryland terrapins': 'Maryland',
    'saint marys': "Saint_Mary's",
    "saint mary's": "Saint_Mary's",
    "saint mary's (ca)": "Saint_Mary's",
    "st. mary's": "Saint_Mary's",
    'morgan state': 'Morgan_State',
    'northern iowa': 'Northern_Iowa',
    'st. francis (ny)': "St_Francis_BKN",
    'st francis (ny)': "St_Francis_BKN",
    'st. francis brooklyn': "St_Francis_BKN",
    'st francis bkn': "St_Francis_BKN",
    'saint francis (pa)': 'St_Francis_(PA)',
    'st. francis (pa)': 'St_Francis_(PA)',
}


def _get_ncaahoopr_team_name(team_name: str) -> str:
    """Get ncaahoopR schedule file name for a team."""
    normalized = team_name.lower().strip()

    # Check explicit mapping first
    if normalized in NCAAHOOPR_TEAM_NAMES:
        return NCAAHOOPR_TEAM_NAMES[normalized]

    # Default: replace spaces with underscores, remove apostrophes
    return team_name.replace(' ', '_').replace("'", "").replace(".", "")


def _lookup_espn_id_from_ncaahoopr(
    away_team: str,
    home_team: str,
    date_yyyymmdd: str
) -> Optional[str]:
    """
    Look up ESPN game ID from ncaahoopR schedule data.

    Args:
        away_team: Away team name
        home_team: Home team name
        date_yyyymmdd: Game date in YYYYMMDD format

    Returns:
        ESPN game ID or None if not found
    """
    season = _get_ncaahoopr_season(date_yyyymmdd)
    if not season:
        return None

    date_formatted = _format_ncaahoopr_date(date_yyyymmdd)
    if not date_formatted:
        return None

    # Try to fetch the home team's schedule (they play "at home")
    home_schedule_name = _get_ncaahoopr_team_name(home_team)

    url = f"{NCAAHOOPR_BASE_URL}/{season}/schedules/{home_schedule_name}_schedule.csv"

    _rate_limit()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            return None

        # Parse CSV to find game
        import csv
        from io import StringIO

        reader = csv.DictReader(StringIO(response.text))
        away_norm = _normalize_team_name(away_team)

        for row in reader:
            game_date = row.get('date', '')
            opponent = row.get('opponent', '')
            location = row.get('location', '')

            # Match date and opponent
            if game_date == date_formatted and location == 'H':
                opp_norm = _normalize_team_name(opponent)
                if away_norm in opp_norm or opp_norm in away_norm:
                    return row.get('game_id')

    except (requests.RequestException, Exception):
        pass

    return None


# === ncaahoopR GitHub Data Source ===
# Fallback for older games not available via ESPN API

NCAAHOOPR_BASE_URL = "https://raw.githubusercontent.com/lbenz730/ncaahoopR_data/master"


def _get_ncaahoopr_season(date_yyyymmdd: str) -> Optional[str]:
    """
    Get ncaahoopR season folder name for a date.

    Args:
        date_yyyymmdd: Date in YYYYMMDD format

    Returns:
        Season string like "2016-17" or None
    """
    try:
        year = int(date_yyyymmdd[:4])
        month = int(date_yyyymmdd[4:6])

        # NCAA season runs Nov-March
        # Nov-Dec games are start of season (e.g., Nov 2016 = 2016-17)
        # Jan-April games are end of season (e.g., Feb 2017 = 2016-17)
        if month >= 11:
            # Fall semester - season starts
            season_start = year
        else:
            # Spring semester - season ends
            season_start = year - 1

        season_end = season_start + 1
        return f"{season_start}-{str(season_end)[2:]}"
    except (ValueError, IndexError):
        return None


def _format_ncaahoopr_date(date_yyyymmdd: str) -> Optional[str]:
    """
    Format date for ncaahoopR directory structure.

    Args:
        date_yyyymmdd: Date in YYYYMMDD format (e.g., "20170215")

    Returns:
        Date in YYYY-MM-DD format (e.g., "2017-02-15")
    """
    try:
        return f"{date_yyyymmdd[:4]}-{date_yyyymmdd[4:6]}-{date_yyyymmdd[6:8]}"
    except IndexError:
        return None


def fetch_ncaahoopr_play_by_play(
    game_id: str,
    date_yyyymmdd: str,
    gender: str = 'M',
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Fetch play-by-play data from ncaahoopR GitHub repository.

    Args:
        game_id: ESPN game ID
        date_yyyymmdd: Game date in YYYYMMDD format
        gender: 'M' for men's (women's not available in ncaahoopR)
        verbose: Print status messages

    Returns:
        Parsed play-by-play data or None
    """
    # ncaahoopR only has men's data
    if gender != 'M':
        return None

    season = _get_ncaahoopr_season(date_yyyymmdd)
    date_formatted = _format_ncaahoopr_date(date_yyyymmdd)

    if not season or not date_formatted:
        return None

    # Build URL: {base}/{season}/pbp_logs/{date}/{game_id}.csv
    url = f"{NCAAHOOPR_BASE_URL}/{season}/pbp_logs/{date_formatted}/{game_id}.csv"

    if verbose:
        print(f"  Trying ncaahoopR fallback: {url}")

    _rate_limit()

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code != 200:
            if verbose:
                print(f"  ncaahoopR data not found (status {response.status_code})")
            return None

        # Parse CSV data
        return _parse_ncaahoopr_csv(response.text, game_id, verbose)

    except requests.RequestException as e:
        if verbose:
            print(f"  ncaahoopR request error: {e}")
        return None


def _parse_ncaahoopr_csv(csv_text: str, game_id: str, verbose: bool = False) -> Optional[Dict[str, Any]]:
    """
    Parse ncaahoopR CSV play-by-play data into standardized format.

    Args:
        csv_text: Raw CSV text
        game_id: ESPN game ID
        verbose: Print status messages

    Returns:
        Standardized play-by-play data
    """
    import csv
    from io import StringIO

    try:
        reader = csv.DictReader(StringIO(csv_text))
        rows = list(reader)
    except Exception as e:
        if verbose:
            print(f"  CSV parse error: {e}")
        return None

    if not rows:
        return None

    # Get team names from first row
    first_row = rows[0]
    home_team = first_row.get('home', '')
    away_team = first_row.get('away', '')

    # Get final score from last row
    last_row = rows[-1]
    final_home = int(last_row.get('home_score', 0))
    final_away = int(last_row.get('away_score', 0))

    # Parse plays
    parsed_plays = []
    for row in rows:
        description = row.get('description', '')
        if not description or description == 'PLAY':
            continue

        # Determine which team made the play based on description
        # ncaahoopR doesn't explicitly tag team, but we can infer from player names
        # For now, we'll try to match based on scoring changes
        home_score = int(row.get('home_score', 0))
        away_score = int(row.get('away_score', 0))

        # Get previous scores to determine who scored
        play_id = int(row.get('play_id', 0))
        prev_home = 0
        prev_away = 0
        if play_id > 1 and len(parsed_plays) > 0:
            prev_home = parsed_plays[-1].get('home_score', 0)
            prev_away = parsed_plays[-1].get('away_score', 0)

        home_scored = home_score - prev_home
        away_scored = away_score - prev_away
        scoring_play = home_scored > 0 or away_scored > 0
        score_value = home_scored + away_scored

        # Determine team side
        if home_scored > 0:
            team_side = 'home'
            team_name = home_team
        elif away_scored > 0:
            team_side = 'away'
            team_name = away_team
        else:
            # Non-scoring play - try to infer from description
            team_side = ''
            team_name = ''

        # Extract player name from description
        player_name = _extract_player_from_text(description)

        # Convert time format
        time_str = row.get('time_remaining_half', '')
        half = int(row.get('half', 1))

        # Classify play type
        play_type = _classify_espn_play(description, {})

        parsed_plays.append({
            'time': time_str,
            'period': half,
            'team': team_name,
            'team_side': team_side,
            'player': player_name,
            'text': description,
            'play_type': play_type,
            'scoring_play': scoring_play,
            'score_value': score_value,
            'away_score': away_score,
            'home_score': home_score,
            'win_prob': float(row.get('win_prob', 0.5)),
        })

    if verbose:
        print(f"  Parsed {len(parsed_plays)} plays from ncaahoopR")

    return {
        'espn_id': game_id,
        'away_team': away_team,
        'home_team': home_team,
        'away_score': final_away,
        'home_score': final_home,
        'plays': parsed_plays,
        'play_count': len(parsed_plays),
        'gender': 'M',
        'source': 'ncaahoopR',
    }


def fetch_espn_play_by_play(
    game_id: str,
    gender: str = 'M',
    use_cache: bool = True,
    verbose: bool = False,
    date_yyyymmdd: str = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch play-by-play data from ESPN API, with ncaahoopR fallback.

    Args:
        game_id: ESPN game ID
        gender: 'M' for men's, 'W' for women's
        use_cache: Whether to use cached data if available
        verbose: Print status messages
        date_yyyymmdd: Game date (needed for ncaahoopR fallback)

    Returns:
        Parsed play-by-play data or None on failure
    """
    if not game_id:
        return None

    # Check cache first
    cache_file = CACHE_DIR / f"{game_id}.json"
    if use_cache and cache_file.exists():
        try:
            with open(cache_file, 'r') as f:
                cached = json.load(f)
            if verbose:
                print(f"  Using cached PBP for game {game_id}")
            return cached
        except (json.JSONDecodeError, IOError):
            pass  # Cache corrupted, fetch fresh

    # Rate limit
    _rate_limit()

    # Select endpoint based on gender
    base_url = ESPN_WOMENS_PBP_URL if gender == 'W' else ESPN_PBP_URL
    url = f"{base_url}?event={game_id}"

    if verbose:
        print(f"  Fetching ESPN PBP for game {game_id}...")

    parsed = None

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)

        if response.status_code == 200:
            raw_data = response.json()
            # Parse the plays
            parsed = parse_espn_plays(raw_data, gender)

    except (requests.RequestException, json.JSONDecodeError) as e:
        if verbose:
            print(f"  ESPN PBP request error: {e}")

    # Check if we got plays from ESPN
    if parsed and parsed.get('plays'):
        if verbose:
            print(f"  Got {len(parsed['plays'])} plays from ESPN API")
        parsed['source'] = 'espn_api'
    else:
        # No plays from ESPN - try ncaahoopR fallback
        if date_yyyymmdd and gender == 'M':
            if verbose:
                print(f"  ESPN API returned no plays, trying ncaahoopR...")
            parsed = fetch_ncaahoopr_play_by_play(game_id, date_yyyymmdd, gender, verbose)

    # Cache the parsed data
    if parsed and parsed.get('plays'):
        try:
            with open(cache_file, 'w') as f:
                json.dump(parsed, f, indent=2)
        except IOError as e:
            if verbose:
                print(f"  Warning: Could not cache PBP: {e}")

    return parsed


def parse_espn_plays(raw_data: Dict[str, Any], gender: str = 'M') -> Optional[Dict[str, Any]]:
    """
    Parse ESPN API response into standardized play format.

    Args:
        raw_data: Raw ESPN API response
        gender: 'M' for men's, 'W' for women's

    Returns:
        Standardized play-by-play data
    """
    if not raw_data:
        return None

    # Get teams info
    teams_data = raw_data.get('boxscore', {}).get('teams', [])
    teams = {}
    for team in teams_data:
        team_info = team.get('team', {})
        team_id = team_info.get('id')
        home_away = team.get('homeAway', '')
        if team_id and home_away:
            teams[team_id] = {
                'name': team_info.get('displayName', ''),
                'short_name': team_info.get('shortDisplayName', ''),
                'abbreviation': team_info.get('abbreviation', ''),
                'side': home_away,  # 'home' or 'away'
            }

    # Get plays
    plays_data = raw_data.get('plays', [])
    if not plays_data:
        return None

    parsed_plays = []

    for play in plays_data:
        # Get play text
        play_text = play.get('text', '')
        if not play_text:
            continue

        # Get clock info
        clock = play.get('clock', {})
        display_value = clock.get('displayValue', '')  # e.g., "15:30"

        # Get period
        period = play.get('period', {})
        period_number = period.get('number', 1)

        # Get score after play
        away_score = play.get('awayScore', 0)
        home_score = play.get('homeScore', 0)

        # Get team that made the play
        team_id = str(play.get('team', {}).get('id', ''))
        team_info = teams.get(team_id, {})
        team_name = team_info.get('name', '')
        team_side = team_info.get('side', '')  # 'home' or 'away'

        # Determine if scoring play and extract points
        scoring_play = play.get('scoringPlay', False)
        score_value = play.get('scoreValue', 0)

        # Try to get player name from participants first (ESPN sometimes provides this)
        player_name = ''
        participants = play.get('participants', [])
        for p in participants:
            athlete = p.get('athlete', {})
            if athlete.get('displayName'):
                player_name = athlete.get('displayName')
                break

        # Fall back to extracting from text if no participant found
        if not player_name:
            player_name = _extract_player_from_text(play_text)

        # Classify play type
        play_type = _classify_espn_play(play_text, play.get('type', {}))

        parsed_play = {
            'time': display_value,
            'period': period_number,
            'team': team_name,
            'team_side': team_side,
            'player': player_name,
            'text': play_text,
            'play_type': play_type,
            'scoring_play': scoring_play,
            'score_value': score_value,
            'away_score': away_score,
            'home_score': home_score,
        }

        parsed_plays.append(parsed_play)

    # Get final score
    final_away = parsed_plays[-1]['away_score'] if parsed_plays else 0
    final_home = parsed_plays[-1]['home_score'] if parsed_plays else 0

    # Build team info
    away_team = None
    home_team = None
    for tid, tinfo in teams.items():
        if tinfo['side'] == 'away':
            away_team = tinfo['name']
        elif tinfo['side'] == 'home':
            home_team = tinfo['name']

    return {
        'espn_id': raw_data.get('header', {}).get('id', ''),
        'away_team': away_team or '',
        'home_team': home_team or '',
        'away_score': final_away,
        'home_score': final_home,
        'plays': parsed_plays,
        'play_count': len(parsed_plays),
        'gender': gender,
    }


def _extract_player_from_text(text: str) -> str:
    """
    Extract player name from ESPN play text.

    ESPN formats vary:
    - "John Smith made Three Point Jumper"
    - "Kerry Blackshear Jr. made Layup"
    - "Kerry Blackshear Jr. made Layup. Assisted by Justin Robinson."
    - "Dunk by John Smith"
    - "Layup by John Smith"
    - "Three Point Jumper by John Smith"
    - "John Smith missed Free Throw"
    - "Foul on John Smith"
    """
    if not text:
        return ''

    # Name pattern - handles apostrophes, hyphens, suffixes (Jr., Sr., III, IV, etc.)
    # Examples: O'Brien, Smith Jr., Williams III, Abdul-Jabbar
    name_pattern = r"[A-Z][a-zA-Z'\-]+(?:\s+[A-Z][a-zA-Z'\-]+)*(?:\s+(?:Jr\.|Sr\.|III|IV|II|V))?"

    # Common patterns - ORDER MATTERS (more specific first)
    patterns = [
        # "Name made/missed/makes/misses..." - primary scorer (handles both past and present tense)
        (rf'^({name_pattern})\s+(?:made|missed|makes|misses)', 1),
        # "Foul on Name"
        (rf'Foul on\s+({name_pattern})', 1),
        # "Shot/Layup/Dunk/Jumper by Name" - shot types followed by player
        (rf'(?:shot|layup|dunk|jumper|pointer|throw)\s+by\s+({name_pattern})', 1),
        # Generic "by Name" at end of text (not "Assisted by" or "assists")
        (rf'(?<!Assisted\s)(?<!assists\s)by\s+({name_pattern})\s*\.?\s*$', 1),
        # "by Name" anywhere (but not "Assisted by" or "assists")
        (rf'(?<!Assisted\s)(?<!assists\s)by\s+({name_pattern})', 1),
        # "Name Assist/Steal/Rebound/Block/Turnover" at start
        (rf'^({name_pattern})\s+(?:Assist|Offensive Rebound|Defensive Rebound|Steal|Block|Turnover)', 1),
    ]

    for pattern, group in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            name = match.group(group).strip()
            # Verify it looks like a name (at least 2 parts or has suffix)
            if ' ' in name or name.endswith('.'):
                return name

    return ''


def _classify_espn_play(text: str, play_type_info: Dict) -> str:
    """
    Classify ESPN play into a type category.

    Args:
        text: Play text
        play_type_info: ESPN play type object

    Returns:
        Play type string
    """
    text_lower = text.lower()
    type_text = play_type_info.get('text', '').lower()

    # Check for made shots first
    if 'made' in text_lower:
        if 'three point' in text_lower or '3pt' in text_lower or '3-pt' in text_lower:
            return 'made_three'
        elif 'free throw' in text_lower:
            return 'made_ft'
        elif 'dunk' in text_lower:
            return 'made_dunk'
        elif 'layup' in text_lower:
            return 'made_layup'
        elif 'jumper' in text_lower or 'jump shot' in text_lower:
            return 'made_jumper'
        else:
            return 'made_fg'

    # Missed shots
    if 'missed' in text_lower:
        if 'three point' in text_lower or '3pt' in text_lower or '3-pt' in text_lower:
            return 'missed_three'
        elif 'free throw' in text_lower:
            return 'missed_ft'
        else:
            return 'missed_fg'

    # Other plays
    if 'rebound' in text_lower:
        if 'offensive' in text_lower:
            return 'offensive_rebound'
        elif 'defensive' in text_lower:
            return 'defensive_rebound'
        return 'rebound'

    if 'turnover' in text_lower:
        return 'turnover'

    if 'steal' in text_lower:
        return 'steal'

    if 'block' in text_lower:
        return 'block'

    if 'foul' in text_lower:
        return 'foul'

    if 'assist' in text_lower:
        return 'assist'

    if 'timeout' in text_lower:
        return 'timeout'

    if 'jump ball' in text_lower:
        return 'jump_ball'

    if 'end' in text_lower and ('half' in text_lower or 'period' in text_lower or 'game' in text_lower):
        return 'period_end'

    return 'other'


def get_espn_pbp_for_game(
    away_team: str,
    home_team: str,
    date_yyyymmdd: str,
    gender: str = 'M',
    verbose: bool = False
) -> Optional[Dict[str, Any]]:
    """
    Convenience function to get ESPN PBP for a game by team names and date.

    Args:
        away_team: Away team name
        home_team: Home team name
        date_yyyymmdd: Game date in YYYYMMDD format
        gender: 'M' for men's, 'W' for women's
        verbose: Print status messages

    Returns:
        Parsed play-by-play data or None
    """
    # First try to find ESPN ID from cache
    espn_id = get_espn_id_from_cache(away_team, home_team, date_yyyymmdd, gender)

    if not espn_id:
        if verbose:
            print(f"  ESPN ID not found for {away_team} @ {home_team} ({date_yyyymmdd})")
        return None

    if verbose:
        print(f"  Found ESPN ID {espn_id} for {away_team} @ {home_team}")

    return fetch_espn_play_by_play(
        espn_id, gender, use_cache=True, verbose=verbose, date_yyyymmdd=date_yyyymmdd
    )


def clear_pbp_cache():
    """Clear the ESPN play-by-play cache."""
    import shutil
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Cleared ESPN PBP cache at {CACHE_DIR}")


if __name__ == '__main__':
    # Test with a known game
    import sys

    if len(sys.argv) > 1:
        game_id = sys.argv[1]
        result = fetch_espn_play_by_play(game_id, verbose=True)
        if result:
            print(f"\nFound {result['play_count']} plays")
            print(f"{result['away_team']} {result['away_score']} @ {result['home_team']} {result['home_score']}")
            # Print first 5 plays
            for play in result['plays'][:5]:
                print(f"  {play['time']} - {play['text']}")
        else:
            print("No play-by-play data found")
    else:
        print("Usage: python espn_pbp_scraper.py <espn_game_id>")
