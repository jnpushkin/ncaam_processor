"""
Schedule scraper for ESPN college basketball data.

Fetches upcoming games from ESPN's API to help plan trips to new venues.
"""

import json
import time
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

from .log import info, warn, success


# ESPN API endpoints for college basketball scoreboard
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
ESPN_API_URL_WOMENS = "https://site.api.espn.com/apis/site/v2/sports/basketball/womens-college-basketball/scoreboard"

# Cache file for schedule data
DATA_DIR = Path(__file__).parent.parent.parent / "data"
SCHEDULE_CACHE_FILE = DATA_DIR / "schedule_cache.json"
SCHEDULE_CACHE_FILE_WOMENS = DATA_DIR / "schedule_cache_womens.json"
GAME_TIMES_CACHE_FILE = DATA_DIR / "game_times_cache.json"

# Rate limiting - be respectful to ESPN's servers
REQUEST_DELAY = 0.5  # seconds between requests


def fetch_games_for_date(date: datetime, gender: str = 'M') -> List[Dict[str, Any]]:
    """
    Fetch all D1 basketball games for a specific date.

    Args:
        date: The date to fetch games for
        gender: 'M' for men's, 'W' for women's

    Returns:
        List of game dictionaries with venue and team info
    """
    date_str = date.strftime("%Y%m%d")
    api_url = ESPN_API_URL_WOMENS if gender == 'W' else ESPN_API_URL

    try:
        response = requests.get(
            api_url,
            params={
                "dates": date_str,
                "groups": "50",  # D1
                "limit": "400"   # Get all games
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        games = []
        for event in data.get("events", []):
            game = parse_espn_event(event)
            if game:
                games.append(game)

        return games

    except requests.RequestException as e:
        warn(f"Failed to fetch {gender} games for {date_str}: {e}")
        return []


def parse_espn_event(event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse an ESPN event into our game format.

    Args:
        event: ESPN event dictionary

    Returns:
        Parsed game dictionary or None if invalid
    """
    try:
        competition = event.get("competitions", [{}])[0]
        venue = competition.get("venue", {})
        address = venue.get("address", {})

        # Get teams
        competitors = competition.get("competitors", [])
        home_team = None
        away_team = None

        for comp in competitors:
            team = comp.get("team", {})
            if comp.get("homeAway") == "home":
                home_team = {
                    "id": team.get("id"),
                    "name": team.get("displayName"),
                    "abbreviation": team.get("abbreviation"),
                    "short_name": team.get("shortDisplayName")
                }
            else:
                away_team = {
                    "id": team.get("id"),
                    "name": team.get("displayName"),
                    "abbreviation": team.get("abbreviation"),
                    "short_name": team.get("shortDisplayName")
                }

        if not home_team or not away_team:
            return None

        # Get broadcast info
        broadcasts = competition.get("broadcasts", [])
        tv_info = []
        for broadcast in broadcasts:
            for name in broadcast.get("names", []):
                tv_info.append(name)

        # Parse date - ESPN puts the actual time in status.type.shortDetail
        game_date = event.get("date", "")
        status_type = event.get("status", {}).get("type", {})
        time_detail = status_type.get("shortDetail", "")  # e.g., "12/28 - 7:00 PM EST"

        return {
            "espn_id": event.get("id"),
            "date": game_date,
            "date_display": _format_date(game_date),
            "time_detail": time_detail,  # Contains actual game time
            "name": event.get("name"),
            "short_name": event.get("shortName"),
            "home_team": home_team,
            "away_team": away_team,
            "venue": {
                "id": venue.get("id"),
                "name": venue.get("fullName", ""),
                "city": address.get("city", ""),
                "state": address.get("state", "")
            },
            "neutral_site": competition.get("neutralSite", False),
            "conference_game": competition.get("conferenceCompetition", False),
            "tv": tv_info,
            "status": status_type.get("name", "")
        }

    except (KeyError, IndexError) as e:
        warn(f"Failed to parse event: {e}")
        return None


def _format_date(iso_date: str) -> str:
    """Format ISO date string to readable format in US Eastern time."""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        # Convert UTC to US Eastern (UTC-5 or UTC-4 for DST)
        # For simplicity, use -5 hours (EST) since most games are in winter
        from datetime import timezone, timedelta
        eastern = timezone(timedelta(hours=-5))
        dt_eastern = dt.astimezone(eastern)
        return dt_eastern.strftime("%a, %b %d %Y")
    except (ValueError, AttributeError):
        return iso_date


def scrape_season_schedule(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    gender: str = 'M',
    show_progress: bool = True
) -> List[Dict[str, Any]]:
    """
    Scrape the full season schedule from ESPN.

    Args:
        start_date: Start date (defaults to today)
        end_date: End date (defaults to April 15 for end of season)
        gender: 'M' for men's, 'W' for women's
        show_progress: Whether to show progress messages

    Returns:
        List of all games
    """
    if start_date is None:
        start_date = datetime.now()

    if end_date is None:
        # End of season is typically early April (Final Four)
        # Season runs Nov-April, so if we're in Nov/Dec, end is next year's April
        year = start_date.year
        if start_date.month >= 8:  # Aug onwards = next year's April
            end_date = datetime(year + 1, 4, 15)
        else:
            end_date = datetime(year, 4, 15)

    all_games = []
    current_date = start_date
    total_days = (end_date - start_date).days
    gender_label = "Women's" if gender == 'W' else "Men's"

    if show_progress:
        info(f"Scraping {gender_label} schedule from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({total_days} days)")

    day_count = 0
    while current_date <= end_date:
        day_count += 1

        if show_progress and day_count % 10 == 0:
            info(f"  Day {day_count}/{total_days}: {current_date.strftime('%Y-%m-%d')}")

        games = fetch_games_for_date(current_date, gender=gender)
        all_games.extend(games)

        current_date += timedelta(days=1)
        time.sleep(REQUEST_DELAY)

    if show_progress:
        success(f"Scraped {len(all_games)} {gender_label} games across {total_days} days")

    return all_games


def save_schedule_cache(games: List[Dict[str, Any]], gender: str = 'M') -> None:
    """Save scraped schedule to cache file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    cache_file = SCHEDULE_CACHE_FILE_WOMENS if gender == 'W' else SCHEDULE_CACHE_FILE

    cache_data = {
        "scraped_at": datetime.now().isoformat(),
        "games_count": len(games),
        "gender": gender,
        "games": games
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)

    gender_label = "Women's" if gender == 'W' else "Men's"
    info(f"Saved {len(games)} {gender_label} games to {cache_file}")


def load_schedule_cache(gender: str = 'M') -> Optional[Dict[str, Any]]:
    """Load schedule from cache file."""
    cache_file = SCHEDULE_CACHE_FILE_WOMENS if gender == 'W' else SCHEDULE_CACHE_FILE

    if not cache_file.exists():
        return None

    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        gender_label = "Women's" if gender == 'W' else "Men's"
        warn(f"Failed to load {gender_label} schedule cache: {e}")
        return None


def get_schedule(force_refresh: bool = False, gender: str = 'M') -> List[Dict[str, Any]]:
    """
    Get the schedule, using cache if available and recent.

    Args:
        force_refresh: If True, always scrape fresh data
        gender: 'M' for men's, 'W' for women's

    Returns:
        List of games
    """
    gender_label = "Women's" if gender == 'W' else "Men's"

    if not force_refresh:
        cache = load_schedule_cache(gender=gender)
        if cache:
            scraped_at = datetime.fromisoformat(cache["scraped_at"])
            age_days = (datetime.now() - scraped_at).days

            if age_days < 1:
                info(f"Using cached {gender_label} schedule (scraped {age_days} days ago, {cache['games_count']} games)")
                return cache["games"]
            else:
                info(f"{gender_label} schedule cache is {age_days} days old, refreshing daily for accurate game times...")

    games = scrape_season_schedule(gender=gender)
    save_schedule_cache(games, gender=gender)
    return games


def filter_upcoming_games(
    games: List[Dict[str, Any]],
    visited_venues: Set[str],
    days_ahead: Optional[int] = None,
    state_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Filter games to show upcoming games at unvisited venues.

    Args:
        games: List of all games
        visited_venues: Set of venue strings "Name, City, State"
        days_ahead: Only show games within this many days (None for all)
        state_filter: Only show games in this state

    Returns:
        Filtered list of games at unvisited venues
    """
    now = datetime.now()

    upcoming = []
    for game in games:
        # Parse game date
        try:
            game_date = datetime.fromisoformat(game["date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            continue

        # Only future games
        if game_date.replace(tzinfo=None) < now:
            continue

        # Days ahead filter
        if days_ahead is not None:
            if (game_date.replace(tzinfo=None) - now).days > days_ahead:
                continue

        # State filter
        if state_filter:
            state_normalized = normalize_state(game["venue"]["state"])
            if state_normalized.lower() != normalize_state(state_filter).lower():
                continue

        # Check if venue is visited
        espn_venue = game["venue"]
        is_visited = any(venue_matches(espn_venue, v) for v in visited_venues)

        if not is_visited:
            game["venue_visited"] = False
            upcoming.append(game)

    # Sort by date
    upcoming.sort(key=lambda g: g["date"])

    return upcoming


def get_upcoming_at_unvisited(
    visited_venues: Set[str],
    days_ahead: Optional[int] = None,
    state_filter: Optional[str] = None,
    force_refresh: bool = False
) -> List[Dict[str, Any]]:
    """
    Get upcoming games at venues you haven't visited.

    Args:
        visited_venues: Set of venue strings "Name, City, State"
        days_ahead: Only show games within this many days
        state_filter: Only show games in this state (e.g., "CA", "California")
        force_refresh: Force refresh of schedule cache

    Returns:
        List of upcoming games at unvisited venues
    """
    games = get_schedule(force_refresh=force_refresh)
    return filter_upcoming_games(games, visited_venues, days_ahead, state_filter)


def _normalize_venue_name(name: str) -> str:
    """Normalize venue name for comparison."""
    # Remove common suffixes and normalize
    name = name.lower().strip()

    # Remove common arena/stadium suffixes
    for suffix in ["arena", "center", "coliseum", "fieldhouse", "gymnasium", "pavilion", "stadium", "the "]:
        name = name.replace(suffix, "")

    # Remove extra whitespace
    name = " ".join(name.split())

    return name


# State abbreviation mapping
STATE_ABBREV = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia'
}

# Reverse mapping
STATE_FULL = {v: k for k, v in STATE_ABBREV.items()}


def normalize_state(state: str) -> str:
    """Normalize state to full name."""
    state = state.strip()
    if state.upper() in STATE_ABBREV:
        return STATE_ABBREV[state.upper()]
    return state


def venue_matches(espn_venue: Dict[str, str], user_venue: str) -> bool:
    """
    Check if an ESPN venue matches a user's visited venue.

    Args:
        espn_venue: ESPN venue dict with name, city, state
        user_venue: User's venue string "Name, City, State"

    Returns:
        True if venues match
    """
    # Venue name aliases (ESPN name <-> our name)
    VENUE_ALIASES = {
        'global credit union arena': ['gcu arena', 'grand canyon arena'],
        'gcu arena': ['global credit union arena', 'grand canyon arena'],
    }

    # Parse user venue
    parts = [p.strip() for p in user_venue.split(',')]
    if len(parts) < 2:
        return False

    user_name = parts[0].lower()
    user_city = parts[1].lower() if len(parts) > 1 else ""
    user_state = normalize_state(parts[2]).lower() if len(parts) > 2 else ""

    espn_name = espn_venue.get('name', '').lower()
    espn_city = espn_venue.get('city', '').lower()
    espn_state = normalize_state(espn_venue.get('state', '')).lower()

    # Must be same city and state
    if espn_city != user_city or espn_state != user_state:
        return False

    # Check venue name match
    # Exact match
    if espn_name == user_name:
        return True

    # Check aliases
    if espn_name in VENUE_ALIASES:
        if any(alias in user_name or user_name in alias for alias in VENUE_ALIASES[espn_name]):
            return True
    if user_name in VENUE_ALIASES:
        if any(alias in espn_name or espn_name in alias for alias in VENUE_ALIASES[user_name]):
            return True

    # Normalized match (removes common suffixes)
    if _normalize_venue_name(espn_name) == _normalize_venue_name(user_name):
        return True

    # Partial match - require significant word overlap
    # Must match at least one word of 5+ chars, or match 2+ words
    espn_words = set(_normalize_venue_name(espn_name).split())
    user_words = set(_normalize_venue_name(user_name).split())

    # Remove very short words
    espn_words = {w for w in espn_words if len(w) >= 3}
    user_words = {w for w in user_words if len(w) >= 3}

    if espn_words and user_words:
        overlap = espn_words & user_words
        # Require either: one 5+ char word match, or 2+ word matches
        long_matches = [w for w in overlap if len(w) >= 5]
        if long_matches or len(overlap) >= 2:
            return True

    return False


def get_visited_venues_from_games(games_data: List[Dict]) -> Set[str]:
    """Extract visited venues from game data."""
    venues = set()
    for game in games_data:
        venue = game.get('Venue') or game.get('basic_info', {}).get('venue', '')
        city = game.get('City') or ''
        state = game.get('State') or ''

        if venue:
            # Handle case where city/state might be in venue string
            if city and state:
                venues.add(f"{venue}, {city}, {state}")
            else:
                venues.add(venue)

    return venues


# Cache for ESPN team ID mapping
_espn_team_id_cache: Optional[Dict[str, str]] = None


def _build_espn_team_id_mapping() -> Dict[str, str]:
    """Build mapping of team names to ESPN team IDs from schedule cache."""
    global _espn_team_id_cache
    if _espn_team_id_cache is not None:
        return _espn_team_id_cache

    cache = load_schedule_cache()
    if not cache:
        _espn_team_id_cache = {}
        return _espn_team_id_cache

    teams: Dict[str, str] = {}
    for game in cache.get('games', []):
        for side in ['home_team', 'away_team']:
            team = game.get(side, {})
            tid = team.get('id')
            if not tid:
                continue
            # Store all name variations
            short_name = team.get('short_name', '')
            full_name = team.get('name', '')
            abbrev = team.get('abbreviation', '')

            if short_name and short_name not in teams:
                teams[short_name] = tid
            if abbrev and abbrev not in teams:
                teams[abbrev] = tid
            # Clean full name (remove mascot)
            if full_name and short_name:
                # "Duke Blue Devils" -> "Duke"
                clean_name = full_name
                for suffix in [' Blue Devils', ' Wildcats', ' Bears', ' Eagles', ' Tigers',
                               ' Bulldogs', ' Cardinals', ' Spartans', ' Bruins', ' Trojans',
                               ' Tar Heels', ' Jayhawks', ' Wolverines', ' Buckeyes', ' Fighting Irish',
                               ' Mountaineers', ' Huskies', ' Crimson Tide', ' Sooners', ' Longhorns',
                               ' Gators', ' Seminoles', ' Hurricanes', ' Cavaliers', ' Hokies',
                               ' Yellow Jackets', ' Wolfpack', ' Demon Deacons', ' Orange', ' Panthers',
                               ' Colonels', ' Colonials', ' Owls', ' Hawks', ' Terrapins', ' Nittany Lions',
                               ' Hoosiers', ' Boilermakers', ' Hawkeyes', ' Golden Gophers', ' Badgers',
                               ' Cornhuskers', ' Cyclones', ' Red Raiders', ' Horned Frogs', ' Cougars',
                               ' Ducks', ' Beavers', ' Sun Devils', ' Buffaloes', ' Utes', ' Aztecs',
                               ' Runnin\' Rebels', ' Wolf Pack', ' Broncos', ' Aggies', ' Razorbacks',
                               ' Rebels', ' Volunteers', ' Commodores', ' Gamecocks', ' Dawgs']:
                    clean_name = clean_name.replace(suffix, '')
                if clean_name and clean_name not in teams:
                    teams[clean_name] = tid

    _espn_team_id_cache = teams
    return teams


def get_espn_team_id(team_name: str) -> Optional[str]:
    """
    Get ESPN team ID for a team name.

    Args:
        team_name: Team name (e.g., "Duke", "North Carolina", "UNC")

    Returns:
        ESPN team ID or None if not found
    """
    from .constants import TEAM_ALIASES

    # Manual mappings for teams where our name differs from ESPN's
    MANUAL_ESPN_IDS = {
        'Appalachian State': '2026',
        'Arkansas-Pine Bluff': '2029',
        'Boston University': '104',
        'Cal State Bakersfield': '2934',
        'Cal State Fullerton': '2239',
        'Cal State Northridge': '2463',
        'California Baptist': '2856',
        'Central Michigan': '2117',
        'Charleston Southern': '2127',
        'Coastal Carolina': '324',
        'East Tennessee State': '2193',
        'East Texas A&M': '2563',
        'Fairleigh Dickinson': '2230',
        'George Washington': '45',
        'Grambling State': '2755',
        'Hawaii': '62',
        'IU Indianapolis': '85',
        'Louisiana-Monroe': '2433',
        'Loyola (MD)': '2352',
        'Loyola Marymount': '2350',
        'Maryland-Eastern Shore': '2379',
        'Miami (FL)': '2390',
        'Miami (OH)': '193',
        'Middle Tennessee': '2393',
        'Mississippi Valley State': '2400',
        'North Dakota State': '2449',
        'Northern Arizona': '2464',
        'Northern Kentucky': '94',
        'Northwestern State': '2466',
        'Purdue Fort Wayne': '2870',
        'Saint Francis (PA)': '2598',
        'Saint Joseph\'s': '2603',
        'Saint Mary\'s (CA)': '2608',
        'Saint Peter\'s': '2612',
        'Sam Houston State': '2534',
        'San Jose State': '23',
        'Seattle': '2547',
        'South Carolina State': '2569',
        'South Dakota State': '2571',
        'Southeast Missouri State': '2546',
        'Southeastern Louisiana': '2545',
        'Southern Illinois': '79',
        'Southern Indiana': '88',
        'Southern Utah': '253',
        'St. Bonaventure': '179',
        'St. Francis (NY)': '2597',
        'St. Francis (PA)': '2598',
        'St. John\'s': '2599',
        'St. Thomas': '2900',
        'Stephen F. Austin': '2617',
        'Tennessee-Martin': '2630',
        'Texas A&M-Commerce': '2564',
        'Texas A&M-Corpus Christi': '357',
        'Texas Southern': '2640',
        'UC Santa Barbara': '2540',
        'USC Upstate': '2908',
        'UT Arlington': '250',
        'UT Rio Grande Valley': '292',
        'UTRGV': '292',
        'Western Carolina': '2717',
        'Western Illinois': '2710',
        'Western Kentucky': '98',
        'Albany': '399',
    }

    # Check manual mapping first
    if team_name in MANUAL_ESPN_IDS:
        return MANUAL_ESPN_IDS[team_name]

    teams = _build_espn_team_id_mapping()

    # Direct match
    if team_name in teams:
        return teams[team_name]

    # Try canonical name via alias
    canonical = TEAM_ALIASES.get(team_name)
    if canonical and canonical in teams:
        return teams[canonical]

    # Try case-insensitive match
    team_lower = team_name.lower()
    for name, tid in teams.items():
        if name.lower() == team_lower:
            return tid

    # Try partial match for "State" schools
    # "Michigan State" might be stored as "Michigan St"
    if ' State' in team_name:
        alt_name = team_name.replace(' State', ' St')
        if alt_name in teams:
            return teams[alt_name]

    # Try the reverse
    if ' St' in team_name:
        alt_name = team_name.replace(' St', ' State')
        if alt_name in teams:
            return teams[alt_name]

    return None


def main():
    """CLI entry point for schedule scraping."""
    import argparse

    parser = argparse.ArgumentParser(description="Scrape ESPN college basketball schedule")
    parser.add_argument("--refresh", action="store_true", help="Force refresh of schedule cache")
    parser.add_argument("--days", type=int, default=30, help="Show games within this many days")
    parser.add_argument("--state", type=str, help="Filter by state (e.g., CA, NY)")

    args = parser.parse_args()

    # Get schedule
    games = get_schedule(force_refresh=args.refresh)

    # For now, just show stats
    info(f"\nTotal games in schedule: {len(games)}")

    # Count by venue
    venues = {}
    for game in games:
        venue = game["venue"]["name"]
        if venue:
            venues[venue] = venues.get(venue, 0) + 1

    info(f"Unique venues: {len(venues)}")

    # Show top venues
    top_venues = sorted(venues.items(), key=lambda x: -x[1])[:10]
    info("\nTop 10 venues by game count:")
    for venue, count in top_venues:
        info(f"  {venue}: {count} games")


def fetch_game_time_from_espn(date_str: str, away_team: str, home_team: str) -> Optional[str]:
    """
    Fetch the game time from ESPN for a historical game.

    Args:
        date_str: Date in YYYYMMDD format
        away_team: Away team name
        home_team: Home team name

    Returns:
        ISO datetime string if found, None otherwise
    """
    try:
        response = requests.get(
            ESPN_API_URL,
            params={
                "dates": date_str,
                "groups": "50",
                "limit": "400"
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # Normalize team names for matching
        def normalize(name: str) -> str:
            return name.lower().replace("'", "").replace(".", "").replace("-", " ")

        away_norm = normalize(away_team)
        home_norm = normalize(home_team)

        for event in data.get("events", []):
            name = event.get("name", "")
            # ESPN format: "Away Team at Home Team"
            if " at " in name:
                parts = name.split(" at ")
                if len(parts) == 2:
                    espn_away = normalize(parts[0])
                    espn_home = normalize(parts[1])

                    # Check if teams match (partial match for flexibility)
                    away_match = away_norm in espn_away or espn_away in away_norm
                    home_match = home_norm in espn_home or espn_home in home_norm

                    # Also try shortened names
                    if not away_match:
                        away_match = any(w in espn_away for w in away_norm.split() if len(w) > 3)
                    if not home_match:
                        home_match = any(w in espn_home for w in home_norm.split() if len(w) > 3)

                    if away_match and home_match:
                        return event.get("date", "")

        return None

    except requests.RequestException as e:
        warn(f"Failed to fetch game time for {date_str}: {e}")
        return None


def _load_game_times_cache() -> Dict[str, Dict[str, str]]:
    """Load game times cache from file."""
    if not GAME_TIMES_CACHE_FILE.exists():
        return {}
    try:
        with open(GAME_TIMES_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_game_times_cache(cache: Dict[str, Dict[str, str]]) -> None:
    """Save game times cache to file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(GAME_TIMES_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)


def get_game_times_for_date(date_str: str, gender: str = None) -> Dict[str, str]:
    """
    Fetch all game times for a date from ESPN (with caching).

    Args:
        date_str: Date in YYYYMMDD format
        gender: 'M' for men's, 'W' for women's, or None for both

    Returns:
        Dict mapping "away_team|home_team" to ISO datetime
    """
    # Build cache key based on date and gender
    cache_key = f"{date_str}_{gender or 'all'}"

    # Check cache first
    cache = _load_game_times_cache()
    if cache_key in cache:
        return cache[cache_key]

    game_times = {}

    # Determine which APIs to fetch from
    apis_to_fetch = []
    if gender is None or gender == 'M':
        apis_to_fetch.append(ESPN_API_URL)
    if gender is None or gender == 'W':
        apis_to_fetch.append(ESPN_API_URL_WOMENS)

    for api_url in apis_to_fetch:
        try:
            response = requests.get(
                api_url,
                params={
                    "dates": date_str,
                    "groups": "50",
                    "limit": "400"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            for event in data.get("events", []):
                competition = event.get("competitions", [{}])[0]
                competitors = competition.get("competitors", [])

                home_team = None
                away_team = None
                for comp in competitors:
                    team = comp.get("team", {})
                    if comp.get("homeAway") == "home":
                        home_team = team.get("displayName", "")
                    else:
                        away_team = team.get("displayName", "")

                if home_team and away_team:
                    key = f"{away_team}|{home_team}"
                    game_times[key] = event.get("date", "")

        except requests.RequestException as e:
            warn(f"Failed to fetch game times for {date_str} from {api_url}: {e}")

    # Save to cache
    cache[cache_key] = game_times
    _save_game_times_cache(cache)

    return game_times


if __name__ == "__main__":
    main()
