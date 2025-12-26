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


# ESPN API endpoint for college basketball scoreboard
ESPN_API_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"

# Cache file for schedule data
DATA_DIR = Path(__file__).parent.parent.parent / "data"
SCHEDULE_CACHE_FILE = DATA_DIR / "schedule_cache.json"

# Rate limiting - be respectful to ESPN's servers
REQUEST_DELAY = 0.5  # seconds between requests


def fetch_games_for_date(date: datetime) -> List[Dict[str, Any]]:
    """
    Fetch all D1 men's basketball games for a specific date.

    Args:
        date: The date to fetch games for

    Returns:
        List of game dictionaries with venue and team info
    """
    date_str = date.strftime("%Y%m%d")

    try:
        response = requests.get(
            ESPN_API_URL,
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
        warn(f"Failed to fetch games for {date_str}: {e}")
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

        # Parse date
        game_date = event.get("date", "")

        return {
            "espn_id": event.get("id"),
            "date": game_date,
            "date_display": _format_date(game_date),
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
            "status": event.get("status", {}).get("type", {}).get("name", "")
        }

    except (KeyError, IndexError) as e:
        warn(f"Failed to parse event: {e}")
        return None


def _format_date(iso_date: str) -> str:
    """Format ISO date string to readable format."""
    try:
        dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
        return dt.strftime("%a, %b %d %Y")
    except (ValueError, AttributeError):
        return iso_date


def scrape_season_schedule(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    show_progress: bool = True
) -> List[Dict[str, Any]]:
    """
    Scrape the full season schedule from ESPN.

    Args:
        start_date: Start date (defaults to today)
        end_date: End date (defaults to April 15 for end of season)
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

    if show_progress:
        info(f"Scraping schedule from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({total_days} days)")

    day_count = 0
    while current_date <= end_date:
        day_count += 1

        if show_progress and day_count % 10 == 0:
            info(f"  Day {day_count}/{total_days}: {current_date.strftime('%Y-%m-%d')}")

        games = fetch_games_for_date(current_date)
        all_games.extend(games)

        current_date += timedelta(days=1)
        time.sleep(REQUEST_DELAY)

    if show_progress:
        success(f"Scraped {len(all_games)} games across {total_days} days")

    return all_games


def save_schedule_cache(games: List[Dict[str, Any]]) -> None:
    """Save scraped schedule to cache file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    cache_data = {
        "scraped_at": datetime.now().isoformat(),
        "games_count": len(games),
        "games": games
    }

    with open(SCHEDULE_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2)

    info(f"Saved {len(games)} games to {SCHEDULE_CACHE_FILE}")


def load_schedule_cache() -> Optional[Dict[str, Any]]:
    """Load schedule from cache file."""
    if not SCHEDULE_CACHE_FILE.exists():
        return None

    try:
        with open(SCHEDULE_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        warn(f"Failed to load schedule cache: {e}")
        return None


def get_schedule(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Get the schedule, using cache if available and recent.

    Args:
        force_refresh: If True, always scrape fresh data

    Returns:
        List of games
    """
    if not force_refresh:
        cache = load_schedule_cache()
        if cache:
            scraped_at = datetime.fromisoformat(cache["scraped_at"])
            age_days = (datetime.now() - scraped_at).days

            if age_days < 7:
                info(f"Using cached schedule (scraped {age_days} days ago, {cache['games_count']} games)")
                return cache["games"]
            else:
                info(f"Schedule cache is {age_days} days old, refreshing...")

    games = scrape_season_schedule()
    save_schedule_cache(games)
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

    # Normalized match (removes common suffixes)
    if _normalize_venue_name(espn_name) == _normalize_venue_name(user_name):
        return True

    # Partial match - significant words overlap
    espn_words = set(_normalize_venue_name(espn_name).split())
    user_words = set(_normalize_venue_name(user_name).split())

    # Remove very short words
    espn_words = {w for w in espn_words if len(w) >= 3}
    user_words = {w for w in user_words if len(w) >= 3}

    if espn_words and user_words:
        overlap = espn_words & user_words
        if overlap:
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


if __name__ == "__main__":
    main()
