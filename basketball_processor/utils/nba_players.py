"""
NBA player lookup utilities.
Uses Sports Reference links to determine if a college player went to the NBA.
Also checks Proballers.com for comprehensive international league data.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime
import time

# Import Proballers scraper for international league data
try:
    from basketball_processor.utils.proballers_scraper import (
        find_player_by_college,
        get_player_career,
        get_player_pro_leagues,
        LEAGUE_NAMES as PROBALLERS_LEAGUE_NAMES,
    )
    HAS_PROBALLERS = True
except ImportError:
    HAS_PROBALLERS = False

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Cache file location (can be cleared)
CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
NBA_LOOKUP_CACHE_FILE = CACHE_DIR / 'nba_lookup_cache.json'
NBA_API_CACHE_FILE = CACHE_DIR / 'nba_api_cache.json'

# Persistent data location (DO NOT DELETE - survives cache clears)
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
NBA_CONFIRMED_FILE = DATA_DIR / 'nba_confirmed.json'
NBA_RECHECK_TIMESTAMP_FILE = DATA_DIR / 'nba_recheck_timestamp.txt'
WNBA_RECHECK_TIMESTAMP_FILE = DATA_DIR / 'wnba_recheck_timestamp.txt'
# Days between automatic null re-checks
RECHECK_INTERVAL_DAYS = 90


def _get_current_nba_seasons() -> Tuple[str, str]:
    """Get current and previous NBA season strings (e.g., '2024-25', '2023-24')."""
    now = datetime.now()
    year = now.year
    month = now.month
    # NBA season runs Oct-June. If Jan-June, we're in (year-1)-(year) season
    if month <= 6:
        current = f"{year-1}-{str(year)[2:]}"
        previous = f"{year-2}-{str(year-1)[2:]}"
    else:
        current = f"{year}-{str(year+1)[2:]}"
        previous = f"{year-1}-{str(year)[2:]}"
    return current, previous


def _get_current_wnba_years() -> Tuple[str, str]:
    """Get current and previous WNBA season years (e.g., '2025', '2024')."""
    now = datetime.now()
    year = now.year
    # WNBA season runs May-Sept. If before May, previous year is more relevant
    if now.month < 5:
        return str(year - 1), str(year - 2)
    return str(year), str(year - 1)

# Sports Reference base URL
SPORTS_REF_BASE = "https://www.sports-reference.com/cbb/players/"

# Rate limiting: Sports Reference allows 20 requests/minute
# We use 3.1 seconds to stay under limit (19 req/min)
RATE_LIMIT_SECONDS = 3.1

# Player ID aliases for typos/spelling differences between SR and BR
# Maps: wrong_id -> correct_id (for Basketball Reference lookups)
PLAYER_ID_ALIASES = {
    # 'example-player-1': 'correct-spelling-1',  # Use when SR has typo but BR has correct spelling
}

# Manual overrides for name-based matching
# Player IDs (e.g., 'marcus-williams-24') to EXCLUDE from NBA matching
FALSE_POSITIVE_IDS = {
    'marcus-williams-24',   # San Francisco player, not the NBA one
    'eric-anderson-2',      # Yale player
    'charles-thomasiv-1',   # Wisconsin player
    'justin-williams-4',    # George Washington player
    'aleem-ford-1',         # Different person
    'isaac-jones-2',        # Different person
    'bernard-thompson-1',   # Different person
    'jack-white-3',         # Different person
    'junjie-wang-1',        # College player is different from BR international player
}

# Professional overseas league URL patterns on Basketball Reference
# These appear in gamelog URLs like /gamelog/YEAR/euroleague/
# Source: https://www.basketball-reference.com/international/
# Maps URL slug to display name
PROFESSIONAL_LEAGUE_NAMES = {
    'euroleague': 'EuroLeague',
    'eurocup': 'EuroCup',
    'cba-china': 'CBA (China)',
    'cba': 'CBA (China)',
    'greek-basket-league': 'Greek League',
    'spain-liga-acb': 'Liga ACB (Spain)',
    'italy-basket-serie-a': 'Serie A (Italy)',
    'france-lnb-pro-a': 'LNB Pro A (France)',
    'turkey-super-league': 'BSL (Turkey)',
    'nbl-australia': 'NBL (Australia)',
    'vtb-united': 'VTB United League',
    'israel-super-league': 'Israeli League',
    'aba-adriatic': 'ABA League',
}

# Set of URL slugs for quick lookup
PROFESSIONAL_LEAGUE_URLS = set(PROFESSIONAL_LEAGUE_NAMES.keys())

# Tournament URL patterns (national team competitions, NOT professional leagues)
# Maps URL slug to display name
NATIONAL_TEAM_TOURNAMENT_NAMES = {
    'fiba-world-cup': 'FIBA World Cup',
    'mens-olympics': 'Olympics',
    'womens-olympics': 'Olympics',
}

NATIONAL_TEAM_TOURNAMENTS = set(NATIONAL_TEAM_TOURNAMENT_NAMES.keys())


def _load_lookup_cache() -> Dict[str, Any]:
    """Load cached NBA lookup results."""
    from .log import warn_once
    if NBA_LOOKUP_CACHE_FILE.exists():
        try:
            with open(NBA_LOOKUP_CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            warn_once(f"NBA lookup cache corrupted ({NBA_LOOKUP_CACHE_FILE}): {e}", key='nba_lookup_cache_corrupt')
        except (IOError, OSError, PermissionError) as e:
            warn_once(f"Failed to load NBA lookup cache: {e}", key='nba_lookup_cache_error')
    return {}


def _save_lookup_cache(cache: Dict[str, Any]) -> None:
    """Save NBA lookup cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(NBA_LOOKUP_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def _load_confirmed() -> Dict[str, Any]:
    """Load persistent confirmed NBA/Intl players (survives cache clears)."""
    from .log import warn_once
    if NBA_CONFIRMED_FILE.exists():
        try:
            with open(NBA_CONFIRMED_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            warn_once(f"NBA confirmed cache corrupted ({NBA_CONFIRMED_FILE}): {e}", key='nba_confirmed_cache_corrupt')
        except (IOError, OSError, PermissionError) as e:
            warn_once(f"Failed to load NBA confirmed cache: {e}", key='nba_confirmed_cache_error')
    return {}


def _save_confirmed(confirmed: Dict[str, Any]) -> None:
    """Save to persistent confirmed file."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(NBA_CONFIRMED_FILE, 'w') as f:
        json.dump(confirmed, f, indent=2)


def _add_to_confirmed(player_id: str, data: Dict[str, Any]) -> None:
    """Add a player to the persistent confirmed file."""
    if data and (data.get('nba_url') or data.get('wnba_url') or data.get('intl_url')):
        confirmed = _load_confirmed()
        confirmed[player_id] = data
        _save_confirmed(confirmed)


def _check_intl_type(intl_url: str, scraper: Any = None) -> Dict[str, Any]:
    """
    Check what types of international play a player has.

    Basketball Reference international pages have gamelog links like:
    - Professional leagues: /gamelog/YEAR/euroleague/, /gamelog/YEAR/cba/
    - National team: /gamelog/YEAR/mens-olympics/, /gamelog/YEAR/fiba-world-cup/

    Args:
        intl_url: Basketball Reference international player URL
        scraper: Optional cloudscraper instance

    Returns:
        Dict with 'pro', 'national_team' boolean flags and 'leagues'/'tournaments' lists
        e.g., {'pro': True, 'national_team': False, 'leagues': ['EuroLeague'], 'tournaments': []}
    """
    result = {'pro': False, 'national_team': False, 'leagues': [], 'tournaments': []}

    try:
        time.sleep(RATE_LIMIT_SECONDS)

        if HAS_CLOUDSCRAPER and scraper:
            response = scraper.get(intl_url, timeout=15)
        elif HAS_REQUESTS:
            response = requests.get(intl_url, timeout=15)
        else:
            return result

        if response.status_code != 200:
            return result

        html = response.text
        found_leagues = set()
        found_tournaments = set()

        # Method 1: Extract gamelog links (newer player pages)
        # Pattern: /gamelog/YEAR/LEAGUE_OR_TOURNAMENT/
        gamelog_links = re.findall(r'/gamelog/\d{4}/([^/"]+)/', html)

        for league_slug in gamelog_links:
            league_slug_lower = league_slug.lower()
            if league_slug_lower in PROFESSIONAL_LEAGUE_URLS:
                result['pro'] = True
                league_name = PROFESSIONAL_LEAGUE_NAMES.get(league_slug_lower, league_slug)
                found_leagues.add(league_name)
            elif league_slug_lower in NATIONAL_TEAM_TOURNAMENTS:
                result['national_team'] = True
                tourney_name = NATIONAL_TEAM_TOURNAMENT_NAMES.get(league_slug_lower, league_slug)
                found_tournaments.add(tourney_name)

        # Method 2: Check for league links in stats tables (older player pages)
        # These pages link to /international/LEAGUE/ from team cells
        if not result['pro'] and not result['national_team']:
            for league_slug in PROFESSIONAL_LEAGUE_URLS:
                if f'/international/{league_slug}/' in html:
                    # Make sure it's in a data context, not just navigation
                    # Look for it near team data or in table context
                    if re.search(rf'<td[^>]*>.*?/international/{league_slug}/.*?</td>', html, re.DOTALL | re.IGNORECASE):
                        result['pro'] = True
                        league_name = PROFESSIONAL_LEAGUE_NAMES.get(league_slug, league_slug)
                        found_leagues.add(league_name)
            for tourney_slug in NATIONAL_TEAM_TOURNAMENTS:
                if f'/international/{tourney_slug}/' in html:
                    if re.search(rf'<td[^>]*>.*?/international/{tourney_slug}/.*?</td>', html, re.DOTALL | re.IGNORECASE):
                        result['national_team'] = True
                        tourney_name = NATIONAL_TEAM_TOURNAMENT_NAMES.get(tourney_slug, tourney_slug)
                        found_tournaments.add(tourney_name)

        # Method 3: If still nothing, check for league names in table headers/data
        # Common patterns: "Greek Basket League", "LNB Pro A", "Serie A", etc.
        if not result['pro'] and not result['national_team']:
            pro_league_patterns = {
                'euroleague': 'EuroLeague',
                'eurocup': 'EuroCup',
                'greek basket': 'Greek League',
                'liga acb': 'Liga ACB (Spain)',
                'serie a': 'Serie A (Italy)',
                'lnb pro': 'LNB Pro A (France)',
                'super league': 'Super League',
                'nbl': 'NBL (Australia)',
                'vtb': 'VTB United League',
                'cba': 'CBA (China)',
                'adriatic': 'ABA League'
            }
            for pattern, name in pro_league_patterns.items():
                if pattern.lower() in html.lower():
                    # Check it's in a stats table context
                    if 'per_game' in html or 'totals' in html:
                        result['pro'] = True
                        found_leagues.add(name)
                        break

        result['leagues'] = sorted(list(found_leagues))
        result['tournaments'] = sorted(list(found_tournaments))
        return result

    except (requests.RequestException, ConnectionError, TimeoutError, ValueError) as e:
        # Network errors or HTML parsing issues - return empty result
        return result


def _check_proballers_leagues(player_name: str, college_team: str, year: Optional[int] = None) -> Tuple[List[str], Optional[int]]:
    """
    Check Proballers.com for international leagues a player has played in.

    Args:
        player_name: Player's full name
        college_team: College team name (e.g., 'Virginia')
        year: Optional basketball season year (e.g., 2025 for 2024-25 season)

    Returns:
        Tuple of (list of league names, Proballers player ID or None)
    """
    if not HAS_PROBALLERS:
        return [], None

    try:
        # Convert college team name to slug format
        college_slug = college_team.lower().replace(' ', '-').replace("'", '')

        # Try variations of the college name
        slug_variations = [
            college_slug,
            f"{college_slug}-cavaliers",
            f"{college_slug}-bulldogs",
            f"{college_slug}-wildcats",
            f"{college_slug}-tigers",
            f"{college_slug}-bears",
            college_slug.replace('-university', ''),
            college_slug.replace('university-of-', ''),
        ]

        proballers_id = None
        for slug in slug_variations:
            proballers_id = find_player_by_college(slug, player_name, year=year)
            if proballers_id:
                break

        if proballers_id is None:
            return [], None

        # Get leagues from Proballers
        leagues = get_player_pro_leagues(proballers_id)
        return leagues, proballers_id

    except (requests.RequestException, ConnectionError, TimeoutError, AttributeError) as e:
        # Network errors or Proballers lookup issues
        return [], None


def _merge_leagues(br_leagues: List[str], proballers_leagues: List[str]) -> List[str]:
    """
    Merge leagues from Basketball Reference and Proballers, avoiding duplicates.

    Args:
        br_leagues: Leagues from Basketball Reference
        proballers_leagues: Leagues from Proballers

    Returns:
        Combined list of unique leagues
    """
    # Normalize league names for comparison
    def normalize(name: str) -> str:
        return name.lower().replace('(', '').replace(')', '').replace(' ', '')

    merged = list(br_leagues)
    br_normalized = {normalize(l) for l in br_leagues}

    for league in proballers_leagues:
        league_norm = normalize(league)
        # Check if we already have this league (or a variant)
        is_duplicate = False
        for existing_norm in br_normalized:
            # Check for overlap (e.g., "EuroLeague" matches "euroleague")
            if league_norm in existing_norm or existing_norm in league_norm:
                is_duplicate = True
                break
            # Check for country matches (e.g., "Greek League" matches "Greece HEBA A1")
            league_country = league_norm.split('(')[0].strip() if '(' in league else league_norm
            existing_country = existing_norm.split('(')[0].strip() if '(' in existing_norm else existing_norm
            if league_country and existing_country and (league_country in existing_country or existing_country in league_country):
                is_duplicate = True
                break

        if not is_duplicate:
            merged.append(league)

    return sorted(merged)


def _verify_nba_stats(nba_url: str, scraper: Any = None) -> Dict[str, Any]:
    """
    Verify that a player actually has NBA game stats on their BR page.

    Some players have BR pages but never played (just draft/G-League).
    This checks for actual per-game stats table.

    Args:
        nba_url: Basketball Reference player URL
        scraper: Optional cloudscraper instance

    Returns:
        Dict with 'played': bool and 'games': int (0 if signed but didn't play)
    """
    try:
        time.sleep(RATE_LIMIT_SECONDS)

        if scraper:
            response = scraper.get(nba_url, timeout=15)
        elif HAS_REQUESTS:
            response = requests.get(nba_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; BasketballStatsBot/1.0)'
            })
        else:
            return {'played': True, 'games': None}  # Can't verify, assume played

        if response.status_code != 200:
            return {'verified': False, 'status_code': response.status_code}  # Can't verify

        html = response.text

        # Check for NBA per-game stats table with actual data
        # The table ID is "per_game_stats" and rows have IDs like "per_game_stats.2023"
        # Note: College stats appear separately with different table structure

        # Look for NBA per_game_stats rows (e.g., id="per_game_stats.2023")
        if re.search(r'id="per_game_stats\.\d{4}"', html):
            # Extract games from the per_game_stats section (after the table starts)
            per_game_section = re.search(r'id="per_game_stats".*?</table>', html, re.DOTALL)
            if per_game_section:
                section_html = per_game_section.group(0)
                # Get career totals from this section (in tfoot)
                # NBA uses data-stat="games" not data-stat="g"
                career_match = re.search(r'<tfoot>.*?data-stat="games"[^>]*>(\d+)<', section_html, re.DOTALL)
                if career_match:
                    games = int(career_match.group(1))
                    return {'played': True, 'games': games}
            # Has row IDs but couldn't get count - still played
            return {'played': True, 'games': None}

        # No NBA per_game_stats rows = never played NBA
        return {'played': False, 'games': 0}

    except (requests.RequestException, ConnectionError, TimeoutError) as e:
        return {'verified': False, 'error': str(e)}  # Can't verify - network error


def _verify_wnba_stats(wnba_url: str, scraper: Any = None) -> Dict[str, Any]:
    """
    Verify that a player actually has WNBA game stats on their BR page.

    Args:
        wnba_url: Basketball Reference WNBA player URL
        scraper: Optional cloudscraper instance

    Returns:
        Dict with 'played': bool and 'games': int (0 if signed but didn't play)
    """
    try:
        time.sleep(RATE_LIMIT_SECONDS)

        if scraper:
            response = scraper.get(wnba_url, timeout=15)
        elif HAS_REQUESTS:
            response = requests.get(wnba_url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; BasketballStatsBot/1.0)'
            })
        else:
            return {'played': True, 'games': None}  # Can't verify, assume played

        if response.status_code != 200:
            return {'verified': False, 'status_code': response.status_code}  # Can't verify

        html = response.text

        # Check for WNBA per-game stats table with actual data
        # WNBA uses id="per_game0" for the table and rows like id="per_game0.2016"

        # Look for WNBA per_game0 rows (e.g., id="per_game0.2023")
        if re.search(r'id="per_game0\.\d{4}"', html):
            # Extract games from the per_game0 section
            per_game_section = re.search(r'id="per_game0".*?</table>', html, re.DOTALL)
            if per_game_section:
                section_html = per_game_section.group(0)
                # Get career totals from this section (in tfoot)
                career_match = re.search(r'<tfoot>.*?data-stat="g"[^>]*>(\d+)<', section_html, re.DOTALL)
                if career_match:
                    games = int(career_match.group(1))
                    return {'played': True, 'games': games}
            # Has row IDs but couldn't get count - still played
            return {'played': True, 'games': None}

        # No WNBA per_game0 rows = never played WNBA
        return {'played': False, 'games': 0}

    except (requests.RequestException, ConnectionError, TimeoutError) as e:
        return {'verified': False, 'error': str(e)}  # Can't verify - network error


def check_player_nba_status(player_id: str) -> Optional[Dict[str, Any]]:
    """
    Check if a player went to the NBA by looking up their Sports Reference page.

    Args:
        player_id: Sports Reference player ID (e.g., 'jayson-tatum-1')

    Returns:
        Dict with NBA info if player went to NBA, None otherwise
    """
    # Check manual exclusions
    if player_id in FALSE_POSITIVE_IDS:
        return None

    # Check persistent confirmed file (survives cache clears, auto-updated by reverify)
    confirmed = _load_confirmed()
    if player_id in confirmed:
        return confirmed[player_id]

    # Check cache
    cache = _load_lookup_cache()
    if player_id in cache:
        cached = cache[player_id]
        if cached is None:
            return None
        return cached

    # Fetch from Sports Reference
    if not HAS_CLOUDSCRAPER and not HAS_REQUESTS:
        return None

    url = f"{SPORTS_REF_BASE}{player_id}.html"
    try:
        # Rate limit to stay under 20 requests/minute
        time.sleep(RATE_LIMIT_SECONDS)

        # Use cloudscraper to bypass Cloudflare protection
        if HAS_CLOUDSCRAPER:
            scraper = cloudscraper.create_scraper()
            response = scraper.get(url, timeout=15)
        else:
            response = requests.get(url, timeout=10, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; BasketballStatsBot/1.0)'
            })

        result = {}

        # Only warn about rate limiting, not missing pages
        if response.status_code == 429:
            print(f" [RATE LIMITED]", end="", flush=True)
        elif response.status_code >= 500:
            print(f" [HTTP {response.status_code}]", end="", flush=True)
        elif response.status_code == 404:
            # Player doesn't have a Sports Reference page
            result['sr_page_exists'] = False

        if response.status_code == 200:
            result['sr_page_exists'] = True
            html = response.text

            # Look for Basketball Reference NBA link
            nba_match = re.search(
                r'href="(https://www\.basketball-reference\.com/players/[^"]+)"[^>]*>Basketball-Reference\.com</a>',
                html
            )

            if nba_match:
                nba_url = nba_match.group(1)
                # Verify they actually played NBA games (not just a draft/G-League page)
                nba_verify = _verify_nba_stats(nba_url, scraper if HAS_CLOUDSCRAPER else None)
                # Always store the URL (they were signed)
                result['nba_url'] = nba_url
                # Only set played status if we could verify
                if nba_verify.get('verified') is not False:
                    result['nba_played'] = nba_verify['played']
                    if nba_verify['games'] is not None:
                        result['nba_games'] = nba_verify['games']
                    if nba_verify['played']:
                        # Check if currently active (look for recent season in stats table)
                        current_season, prev_season = _get_current_nba_seasons()
                        season_pattern = re.compile(rf'<th[^>]*scope="row"[^>]*>({re.escape(current_season)}|{re.escape(prev_season)})</th>')
                        is_active = bool(season_pattern.search(html))
                        result['is_active'] = is_active
                    else:
                        result['is_active'] = False
                        print(" [Signed, no games]", end="", flush=True)

            # Look for Basketball Reference WNBA link
            wnba_match = re.search(
                r'href="(https://www\.basketball-reference\.com/wnba/players/[^"]+)"[^>]*>Basketball-Reference\.com</a>',
                html
            )

            if wnba_match:
                wnba_url = wnba_match.group(1)
                # Verify they actually played WNBA games
                wnba_verify = _verify_wnba_stats(wnba_url, scraper if HAS_CLOUDSCRAPER else None)
                # Always store the URL (they were signed)
                result['wnba_url'] = wnba_url
                # Only set played status if we could verify
                if wnba_verify.get('verified') is not False:
                    result['wnba_played'] = wnba_verify['played']
                    if wnba_verify['games'] is not None:
                        result['wnba_games'] = wnba_verify['games']
                    if wnba_verify['played']:
                        # Check if currently active (look for year in stats table)
                        current_year, prev_year = _get_current_wnba_years()
                        season_pattern = re.compile(rf'<th[^>]*scope="row"[^>]*>({re.escape(current_year)}|{re.escape(prev_year)})</th>')
                        is_wnba_active = bool(season_pattern.search(html))
                        result['is_wnba_active'] = is_wnba_active
                    else:
                        result['is_wnba_active'] = False
                        print(" [Signed, no games]", end="", flush=True)

            # Look for Basketball Reference International link
            intl_match = re.search(
                r'href="(https://www\.basketball-reference\.com/international/players/[^"]+)"',
                html
            )

            if intl_match:
                intl_url = intl_match.group(1)
                result['intl_url'] = intl_url
                # Check if professional league and/or national team
                intl_types = _check_intl_type(intl_url, scraper if HAS_CLOUDSCRAPER else None)
                result['intl_pro'] = intl_types['pro']
                result['intl_national_team'] = intl_types['national_team']
                # Print what was found
                tags = []
                if intl_types['pro']:
                    tags.append("Pro")
                if intl_types['national_team']:
                    tags.append("Nat'l")
                if tags:
                    print(f" [{'+'.join(tags)}]", end="", flush=True)

        # Always check Basketball Reference international directly as fallback
        # (Works even when Sports Reference is rate limited or doesn't show the link)
        if 'intl_url' not in result:
            try:
                time.sleep(RATE_LIMIT_SECONDS)  # Rate limit BR requests too
                # Use alias if player ID has a typo on SR vs BR
                lookup_id = PLAYER_ID_ALIASES.get(player_id, player_id)
                intl_check_url = f"https://www.basketball-reference.com/international/players/{lookup_id}.html"
                if HAS_CLOUDSCRAPER:
                    intl_response = scraper.head(intl_check_url, timeout=10, allow_redirects=True)
                else:
                    intl_response = requests.head(intl_check_url, timeout=10, allow_redirects=True)
                if intl_response.status_code == 200:
                    result['intl_url'] = intl_check_url
                    # Check type (need to fetch the page)
                    intl_types = _check_intl_type(intl_check_url, scraper if HAS_CLOUDSCRAPER else None)
                    result['intl_pro'] = intl_types['pro']
                    result['intl_national_team'] = intl_types['national_team']
                    # Print what was found
                    tags = []
                    if intl_types['pro']:
                        tags.append("Pro")
                    if intl_types['national_team']:
                        tags.append("Nat'l")
                    if tags:
                        print(f" [{'+'.join(tags)}]", end="", flush=True)
            except (requests.RequestException, ConnectionError, TimeoutError):
                pass  # Network errors are expected for players without intl pages

        if result:
            cache[player_id] = result
            _save_lookup_cache(cache)
            _add_to_confirmed(player_id, result)  # Persist for cache clears
            return result
        else:
            cache[player_id] = None
            _save_lookup_cache(cache)
            return None

    except (requests.RequestException, ConnectionError, TimeoutError) as e:
        print(f"Warning: Network error fetching {url}: {e}")
        return None
    except (ValueError, AttributeError) as e:
        print(f"Warning: Parse error for {url}: {e}")
        return None


def get_nba_status_batch(player_ids: List[str], use_api_fallback: bool = True, max_fetch: int = 0) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Get NBA status for multiple players.
    Uses cached data where available, fetches missing data.

    Args:
        player_ids: List of Sports Reference player IDs
        use_api_fallback: If True, also check nba_api for name matches
        max_fetch: Maximum number of new players to fetch (0 = unlimited)

    Returns:
        Dict mapping player_id to NBA info (or None if not NBA)
    """
    results = {}
    cache = _load_lookup_cache()
    confirmed = _load_confirmed()
    to_fetch = []

    for player_id in player_ids:
        # Check manual exclusions - but still return proballers_id if available
        if player_id in FALSE_POSITIVE_IDS:
            # False positives may still have valid Proballers data
            if player_id in confirmed and confirmed[player_id].get('proballers_id'):
                results[player_id] = {'proballers_id': confirmed[player_id]['proballers_id']}
            else:
                results[player_id] = None
            continue

        # Check persistent confirmed file
        if player_id in confirmed:
            results[player_id] = confirmed[player_id]
            continue

        # Check cache
        if player_id in cache:
            results[player_id] = cache[player_id]
            continue

        to_fetch.append(player_id)

    # Fetch missing players (max_fetch=-1 means cache only, skip fetching)
    if to_fetch and HAS_REQUESTS and max_fetch != -1:
        fetch_list = to_fetch if max_fetch == 0 else to_fetch[:max_fetch]
        # Estimate time: ~6.2 seconds per player (2 requests @ 3.1s each)
        est_minutes = (len(fetch_list) * 6.2) / 60
        print(f"Checking {len(fetch_list)} players for NBA status... (est. {est_minutes:.0f} min)")
        for i, player_id in enumerate(fetch_list):
            print(f"  {i+1}/{len(fetch_list)} {player_id}", end="", flush=True)
            result = check_player_nba_status(player_id)
            results[player_id] = result
            # Show what was found (can be multiple)
            tags = []
            if result and result.get('nba_url'):
                tags.append("NBA")
            if result and result.get('wnba_url'):
                tags.append("WNBA")
            if result and result.get('intl_url'):
                tags.append("Intl")
            if tags:
                print(f" → {', '.join(tags)}")
            else:
                print()

    return results


def is_nba_player_by_id(player_id: str) -> bool:
    """Check if a player went to the NBA by their Sports Reference ID."""
    if player_id in FALSE_POSITIVE_IDS:
        return False

    confirmed = _load_confirmed()
    if player_id in confirmed and confirmed[player_id].get('nba_url'):
        return True

    cache = _load_lookup_cache()
    if player_id in cache:
        cached = cache[player_id]
        return cached is not None and 'nba_url' in cached

    # Don't fetch on simple check - use batch function for that
    return False


def is_intl_player_by_id(player_id: str) -> bool:
    """Check if a player had an international career by their Sports Reference ID."""
    if player_id in FALSE_POSITIVE_IDS:
        return False

    cache = _load_lookup_cache()
    if player_id in cache:
        cached = cache[player_id]
        return cached is not None and 'intl_url' in cached

    return False


def get_nba_player_info_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get NBA info for a player by their Sports Reference ID."""
    if player_id in FALSE_POSITIVE_IDS:
        return None

    confirmed = _load_confirmed()
    if player_id in confirmed and confirmed[player_id].get('nba_url'):
        return confirmed[player_id]

    cache = _load_lookup_cache()
    cached = cache.get(player_id)
    if cached and 'nba_url' in cached:
        return cached
    return None


def get_intl_player_info_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get international career info for a player by their Sports Reference ID."""
    if player_id in FALSE_POSITIVE_IDS:
        return None

    confirmed = _load_confirmed()
    if player_id in confirmed and confirmed[player_id].get('intl_url'):
        return confirmed[player_id]

    cache = _load_lookup_cache()
    cached = cache.get(player_id)
    if cached and 'intl_url' in cached:
        return cached
    return None


def get_player_pro_info_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get combined NBA and international info for a player."""
    if player_id in FALSE_POSITIVE_IDS:
        return None

    confirmed = _load_confirmed()
    if player_id in confirmed:
        return confirmed[player_id]

    cache = _load_lookup_cache()
    return cache.get(player_id)


# Legacy functions for backwards compatibility
def is_nba_player(name: str) -> bool:
    """Check if a player name matches an NBA player (legacy name-based)."""
    # This is less accurate - prefer is_nba_player_by_id
    return False  # Disabled - use ID-based lookup


def get_nba_player_info(name: str) -> Optional[Dict[str, Any]]:
    """Get NBA player info by name (legacy)."""
    return None  # Disabled - use ID-based lookup


def check_all_players_from_cache() -> Dict[str, int]:
    """
    Check all players from cached game files for NBA status.
    This function processes all players that haven't been checked yet.

    Returns:
        Dict with counts: {'total': N, 'checked': N, 'nba_found': N, 'skipped': N}
    """
    import json as json_module

    # Get all unique player IDs from cached games
    player_ids: Set[str] = set()
    game_files = list(CACHE_DIR.glob('*.json'))
    game_files = [f for f in game_files if f.name not in ('nba_lookup_cache.json', 'nba_api_cache.json')]

    for game_file in game_files:
        try:
            with open(game_file, 'r') as f:
                data = json_module.load(f)
            box_score = data.get('box_score', {})
            for team_key in ['away', 'home']:
                team_data = box_score.get(team_key, {})
                players = team_data.get('players', [])
                for player in players:
                    pid = player.get('player_id')
                    if pid:
                        player_ids.add(pid)
        except (json.JSONDecodeError, IOError, OSError, KeyError):
            continue

    print(f"Found {len(player_ids)} unique players in {len(game_files)} cached games")

    # Filter out already checked players
    cache = _load_lookup_cache()
    confirmed = _load_confirmed()
    to_check = []
    for pid in player_ids:
        if pid in FALSE_POSITIVE_IDS:
            continue
        if pid in confirmed:
            continue
        if pid in cache:
            continue
        to_check.append(pid)

    print(f"Already in cache: {len(cache)}")
    print(f"Players to check: {len(to_check)}")

    if not to_check:
        print("All players already checked!")
        nba_count = sum(1 for v in cache.values() if v is not None)
        return {'total': len(player_ids), 'checked': 0, 'nba_found': nba_count, 'skipped': len(player_ids) - len(to_check)}

    # Estimate time: ~6.2 seconds per player (2 requests @ 3.1s each)
    est_minutes = (len(to_check) * 6.2) / 60
    print(f"Estimated time: {est_minutes:.0f} minutes (rate limited to 20 req/min)")

    # Check remaining players
    nba_found = 0
    wnba_found = 0
    intl_found = 0
    for i, player_id in enumerate(to_check):
        print(f"  {i+1}/{len(to_check)} {player_id}", end="", flush=True)
        result = check_player_nba_status(player_id)
        # Show what was found (can be multiple)
        tags = []
        if result and result.get('nba_url'):
            nba_found += 1
            tags.append("NBA")
        if result and result.get('wnba_url'):
            wnba_found += 1
            tags.append("WNBA")
        if result and result.get('intl_url'):
            intl_found += 1
            tags.append("Intl")
        if tags:
            print(f" → {', '.join(tags)}")
        else:
            print()

    print(f"\nComplete! Checked {len(to_check)} players, found {nba_found} new NBA players")

    # Count total NBA players in cache and confirmed
    cache = _load_lookup_cache()
    confirmed = _load_confirmed()
    cache_nba = sum(1 for v in cache.values() if v is not None and v.get('nba_url'))
    confirmed_nba = sum(1 for v in confirmed.values() if v and v.get('nba_url'))
    print(f"Total NBA players: {cache_nba + confirmed_nba} (cache: {cache_nba}, confirmed: {confirmed_nba})")

    return {'total': len(player_ids), 'checked': len(to_check), 'nba_found': nba_found, 'skipped': len(player_ids) - len(to_check)}


def _get_last_recheck_time() -> Optional[datetime]:
    """Get the timestamp of the last null re-check."""
    if NBA_RECHECK_TIMESTAMP_FILE.exists():
        try:
            ts = NBA_RECHECK_TIMESTAMP_FILE.read_text().strip()
            return datetime.fromisoformat(ts)
        except (IOError, OSError, ValueError):
            pass
    return None


def _save_recheck_timestamp() -> None:
    """Save the current timestamp as the last re-check time."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    NBA_RECHECK_TIMESTAMP_FILE.write_text(datetime.now().isoformat())


def should_recheck_nulls() -> bool:
    """Check if it's time to re-check null players (every 90 days by default)."""
    last_check = _get_last_recheck_time()
    if last_check is None:
        return True
    days_since = (datetime.now() - last_check).days
    return days_since >= RECHECK_INTERVAL_DAYS


def _check_nba_players_for_intl() -> int:
    """
    Check NBA-only players for international status.
    This catches players who went NBA first, then international.

    Returns:
        Number of players who were found to have international careers
    """
    if not HAS_CLOUDSCRAPER and not HAS_REQUESTS:
        return 0

    # Get all players with NBA but not Intl from cache and confirmed
    cache = _load_lookup_cache()
    confirmed = _load_confirmed()

    nba_only = []
    # Check cache
    for pid, val in cache.items():
        if val and val.get('nba_url') and not val.get('intl_url'):
            nba_only.append(pid)
    # Check confirmed
    for pid, val in confirmed.items():
        if val and val.get('nba_url') and not val.get('intl_url'):
            if pid not in nba_only:
                nba_only.append(pid)

    if not nba_only:
        return 0

    print(f"\nChecking {len(nba_only)} NBA-only players for international status...")

    intl_found = 0
    if HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper()

    for i, player_id in enumerate(nba_only):
        print(f"  {i+1}/{len(nba_only)} {player_id}", end="", flush=True)

        # Rate limit
        time.sleep(RATE_LIMIT_SECONDS)

        # Check Basketball Reference international page directly
        # Use alias if player ID has a typo on SR vs BR
        lookup_id = PLAYER_ID_ALIASES.get(player_id, player_id)
        intl_check_url = f"https://www.basketball-reference.com/international/players/{lookup_id}.html"
        try:
            if HAS_CLOUDSCRAPER:
                response = scraper.head(intl_check_url, timeout=10, allow_redirects=True)
            else:
                response = requests.head(intl_check_url, timeout=10, allow_redirects=True)

            if response.status_code == 200:
                intl_found += 1
                # Update cache
                if player_id in cache and cache[player_id]:
                    cache[player_id]['intl_url'] = intl_check_url
                    _save_lookup_cache(cache)
                # Update confirmed
                if player_id in confirmed and confirmed[player_id]:
                    confirmed[player_id]['intl_url'] = intl_check_url
                    _save_confirmed(confirmed)
                print(" → +Intl")
            else:
                print()
        except (requests.RequestException, ConnectionError, TimeoutError):
            print()

    return intl_found


def recheck_null_players(force: bool = False) -> Dict[str, int]:
    """
    Re-check players cached as null for NBA/Intl status.
    Use this to catch players who have since joined the NBA or gone international.

    By default, only runs if it's been 90+ days since the last re-check.
    Use force=True to run regardless.

    Run manually with:
        python -c "from basketball_processor.utils.nba_players import recheck_null_players; recheck_null_players()"

    Returns:
        Dict with counts: {'checked': N, 'nba_found': N, 'intl_found': N}
    """
    # Check if we should run
    if not force:
        last_check = _get_last_recheck_time()
        if last_check:
            days_since = (datetime.now() - last_check).days
            if days_since < RECHECK_INTERVAL_DAYS:
                print(f"Last re-check was {days_since} days ago. Next re-check in {RECHECK_INTERVAL_DAYS - days_since} days.")
                print("Use force=True to re-check anyway.")
                return {'checked': 0, 'nba_found': 0, 'intl_found': 0}

    cache = _load_lookup_cache()
    null_players = [pid for pid, val in cache.items() if val is None]

    print(f"Found {len(null_players)} players with null cache entries to re-check")

    if not null_players:
        print("No null players to re-check!")
        return {'checked': 0, 'nba_found': 0, 'intl_found': 0}

    # Estimate time: ~6.2 seconds per player (2 requests @ 3.1s each)
    est_minutes = (len(null_players) * 6.2) / 60
    print(f"Estimated time: {est_minutes:.0f} minutes (rate limited to 20 req/min)")

    nba_found = 0
    wnba_found = 0
    intl_found = 0

    for i, player_id in enumerate(null_players):
        print(f"  {i+1}/{len(null_players)} {player_id}", end="", flush=True)

        # Remove from cache so check_player_nba_status will re-fetch
        del cache[player_id]
        _save_lookup_cache(cache)

        # Do a fresh check
        result = check_player_nba_status(player_id)

        # Show what was found
        tags = []
        if result and result.get('nba_url'):
            nba_found += 1
            tags.append("NBA")
        if result and result.get('wnba_url'):
            wnba_found += 1
            tags.append("WNBA")
        if result and result.get('intl_url'):
            intl_found += 1
            tags.append("Intl")
        if tags:
            print(f" → {', '.join(tags)}")
        else:
            print()

        # Reload cache for next iteration
        cache = _load_lookup_cache()

    # Also check NBA-only players for international status
    intl_from_nba = _check_nba_players_for_intl()

    # Save timestamp so we don't re-check again for 90 days
    _save_recheck_timestamp()

    print(f"\nComplete! Re-checked {len(null_players)} null players")
    print(f"  Found {nba_found} NBA, {wnba_found} WNBA, {intl_found} International")
    if intl_from_nba > 0:
        print(f"  Found {intl_from_nba} NBA players who also went international")
    return {'checked': len(null_players), 'nba_found': nba_found, 'wnba_found': wnba_found, 'intl_found': intl_found + intl_from_nba}


def _get_last_wnba_recheck_time() -> Optional[datetime]:
    """Get the timestamp of the last WNBA re-check."""
    if WNBA_RECHECK_TIMESTAMP_FILE.exists():
        try:
            ts = WNBA_RECHECK_TIMESTAMP_FILE.read_text().strip()
            return datetime.fromisoformat(ts)
        except (IOError, OSError, ValueError):
            pass
    return None


def _save_wnba_recheck_timestamp() -> None:
    """Save the current timestamp as the last WNBA re-check time."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    WNBA_RECHECK_TIMESTAMP_FILE.write_text(datetime.now().isoformat())


def should_recheck_wnba() -> bool:
    """Check if it's time to re-check female players for WNBA (every 90 days)."""
    last_check = _get_last_wnba_recheck_time()
    if last_check is None:
        return True
    days_since = (datetime.now() - last_check).days
    return days_since >= RECHECK_INTERVAL_DAYS


def recheck_female_players_for_wnba(force: bool = False) -> Dict[str, int]:
    """
    Re-check female players for WNBA status.
    Only checks players from women's games who don't already have wnba_url in cache.

    By default, only runs if it's been 90+ days since the last WNBA re-check.
    Use force=True to run regardless.

    Run manually with:
        python -c "from basketball_processor.utils.nba_players import recheck_female_players_for_wnba; recheck_female_players_for_wnba(force=True)"

    Returns:
        Dict with counts: {'checked': N, 'wnba_found': N}
    """
    # Check if we should run
    if not force:
        last_check = _get_last_wnba_recheck_time()
        if last_check:
            days_since = (datetime.now() - last_check).days
            if days_since < RECHECK_INTERVAL_DAYS:
                print(f"WNBA re-check: Last check was {days_since} days ago. Next in {RECHECK_INTERVAL_DAYS - days_since} days.")
                return {'checked': 0, 'wnba_found': 0}

    import json as json_module

    # Get all female player IDs from cached games
    female_player_ids: Set[str] = set()
    game_files = list(CACHE_DIR.glob('*.json'))
    game_files = [f for f in game_files if f.name not in ('nba_lookup_cache.json', 'nba_api_cache.json')]

    for game_file in game_files:
        # Check if it's a women's game (filename contains "Women" or game has gender='W')
        is_womens_game = 'Women' in game_file.name

        try:
            with open(game_file, 'r') as f:
                data = json_module.load(f)

            # Also check gender field in basic_info
            if not is_womens_game:
                gender = data.get('basic_info', {}).get('gender', 'M')
                is_womens_game = gender == 'W'

            if not is_womens_game:
                continue

            box_score = data.get('box_score', {})
            for team_key in ['away', 'home']:
                team_data = box_score.get(team_key, {})
                players = team_data.get('players', [])
                for player in players:
                    pid = player.get('player_id')
                    if pid:
                        female_player_ids.add(pid)
        except (json.JSONDecodeError, IOError, OSError, KeyError):
            continue

    print(f"Found {len(female_player_ids)} unique female players in cached women's games")

    # Filter to only those without wnba_url in cache
    cache = _load_lookup_cache()
    to_check = []
    for pid in female_player_ids:
        if pid in FALSE_POSITIVE_IDS:
            continue
        cached = cache.get(pid)
        # Check if we need to look up this player
        if cached is None:
            # Never checked - need to check
            to_check.append(pid)
        elif isinstance(cached, dict) and 'wnba_url' not in cached:
            # Checked but no WNBA info - need to re-check
            to_check.append(pid)
        # If already has wnba_url (or wnba_url check was done), skip

    print(f"Players needing WNBA check: {len(to_check)}")

    if not to_check:
        print("All female players already checked for WNBA!")
        return {'checked': 0, 'wnba_found': 0}

    # Estimate time: ~3.1 seconds per player (1 request to SR)
    est_minutes = (len(to_check) * 3.1) / 60
    print(f"Estimated time: {est_minutes:.0f} minutes (rate limited to 20 req/min)")

    wnba_found = 0
    intl_found = 0

    for i, player_id in enumerate(to_check):
        print(f"  {i+1}/{len(to_check)} {player_id}", end="", flush=True)

        # Remove from cache so check_player_nba_status will re-fetch
        if player_id in cache:
            del cache[player_id]
            _save_lookup_cache(cache)

        # Do a fresh check
        result = check_player_nba_status(player_id)

        # Show what was found
        tags = []
        if result and result.get('wnba_url'):
            wnba_found += 1
            tags.append("WNBA")
        if result and result.get('intl_url'):
            intl_found += 1
            tags.append("Intl")
        if result and result.get('nba_url'):
            tags.append("NBA")  # Unlikely but possible
        if tags:
            print(f" → {', '.join(tags)}")
        else:
            print()

        # Reload cache for next iteration
        cache = _load_lookup_cache()

    # Save timestamp so we don't re-check again for 90 days
    _save_wnba_recheck_timestamp()

    print(f"\nComplete! Checked {len(to_check)} female players")
    print(f"  Found {wnba_found} WNBA, {intl_found} International")
    return {'checked': len(to_check), 'wnba_found': wnba_found, 'intl_found': intl_found}


def reverify_cached_pro_players() -> Dict[str, int]:
    """
    Re-verify cached NBA/WNBA players actually have game stats.
    Removes nba_url/wnba_url from players who have BR pages but no actual games.

    Run manually with:
        python -c "from basketball_processor.utils.nba_players import reverify_cached_pro_players; reverify_cached_pro_players()"

    Returns:
        Dict with counts: {'nba_checked': N, 'nba_removed': N, 'wnba_checked': N, 'wnba_removed': N}
    """
    cache = _load_lookup_cache()
    confirmed = _load_confirmed()

    # Find players with nba_url or wnba_url
    nba_players = [(pid, data) for pid, data in cache.items()
                   if data and data.get('nba_url')]
    wnba_players = [(pid, data) for pid, data in cache.items()
                    if data and data.get('wnba_url')]

    print(f"Found {len(nba_players)} cached NBA players to verify")
    print(f"Found {len(wnba_players)} cached WNBA players to verify")

    if not nba_players and not wnba_players:
        print("No players to verify!")
        return {'nba_checked': 0, 'nba_removed': 0, 'wnba_checked': 0, 'wnba_removed': 0}

    # Estimate time
    total = len(nba_players) + len(wnba_players)
    est_minutes = (total * RATE_LIMIT_SECONDS) / 60
    print(f"Estimated time: {est_minutes:.0f} minutes")

    if HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper()
    else:
        scraper = None

    nba_signed_only = 0
    wnba_signed_only = 0

    # Verify NBA players
    if nba_players:
        print("\nVerifying NBA players...")
        for i, (player_id, data) in enumerate(nba_players):
            nba_url = data.get('nba_url')
            print(f"  {i+1}/{len(nba_players)} {player_id}", end="", flush=True)

            nba_verify = _verify_nba_stats(nba_url, scraper)

            # Skip if we couldn't verify (rate limited, error, etc.)
            if nba_verify.get('verified') is False:
                if 'status_code' in nba_verify:
                    print(f" ⚠️ (HTTP {nba_verify['status_code']} - skipped)")
                elif 'error' in nba_verify:
                    print(f" ⚠️ ({nba_verify['error']} - skipped)")
                else:
                    print(" ⚠️ (unknown error - skipped)")
                continue

            # Update cache with played status
            cache[player_id]['nba_played'] = nba_verify['played']
            if nba_verify['games'] is not None:
                cache[player_id]['nba_games'] = nba_verify['games']
            if not nba_verify['played']:
                cache[player_id]['is_active'] = False
            _save_lookup_cache(cache)

            # Also update confirmed if present
            if player_id in confirmed and confirmed[player_id].get('nba_url'):
                confirmed[player_id]['nba_played'] = nba_verify['played']
                if nba_verify['games'] is not None:
                    confirmed[player_id]['nba_games'] = nba_verify['games']
                if not nba_verify['played']:
                    confirmed[player_id]['is_active'] = False
                _save_confirmed(confirmed)

            if nba_verify['played']:
                print(f" ✓ ({nba_verify['games']} games)" if nba_verify['games'] else " ✓")
            else:
                nba_signed_only += 1
                print(" → Signed, no games")

    # Verify WNBA players
    if wnba_players:
        print("\nVerifying WNBA players...")
        for i, (player_id, data) in enumerate(wnba_players):
            wnba_url = data.get('wnba_url')
            print(f"  {i+1}/{len(wnba_players)} {player_id}", end="", flush=True)

            wnba_verify = _verify_wnba_stats(wnba_url, scraper)

            # Skip if we couldn't verify (rate limited, error, etc.)
            if wnba_verify.get('verified') is False:
                if 'status_code' in wnba_verify:
                    print(f" ⚠️ (HTTP {wnba_verify['status_code']} - skipped)")
                elif 'error' in wnba_verify:
                    print(f" ⚠️ ({wnba_verify['error']} - skipped)")
                else:
                    print(" ⚠️ (unknown error - skipped)")
                continue

            # Update cache with played status
            cache[player_id]['wnba_played'] = wnba_verify['played']
            if wnba_verify['games'] is not None:
                cache[player_id]['wnba_games'] = wnba_verify['games']
            if not wnba_verify['played']:
                cache[player_id]['is_wnba_active'] = False
            _save_lookup_cache(cache)

            # Also update confirmed if present
            if player_id in confirmed and confirmed[player_id].get('wnba_url'):
                confirmed[player_id]['wnba_played'] = wnba_verify['played']
                if wnba_verify['games'] is not None:
                    confirmed[player_id]['wnba_games'] = wnba_verify['games']
                if not wnba_verify['played']:
                    confirmed[player_id]['is_wnba_active'] = False
                _save_confirmed(confirmed)

            if wnba_verify['played']:
                print(f" ✓ ({wnba_verify['games']} games)" if wnba_verify['games'] else " ✓")
            else:
                wnba_signed_only += 1
                print(" → Signed, no games")

    print(f"\nComplete!")
    print(f"  NBA: {len(nba_players)} checked, {nba_signed_only} signed only (no games)")
    print(f"  WNBA: {len(wnba_players)} checked, {wnba_signed_only} signed only (no games)")

    return {
        'nba_checked': len(nba_players),
        'nba_signed_only': nba_signed_only,
        'wnba_checked': len(wnba_players),
        'wnba_signed_only': wnba_signed_only
    }


def recheck_intl_types(force: bool = False) -> Dict[str, int]:
    """
    Check international player types (pro leagues and/or national team).

    Args:
        force: If True, recheck ALL international players (even those already checked).
               If False, only check players missing intl_pro/intl_national_team fields.

    Run manually with:
        python -c "from basketball_processor.utils.nba_players import recheck_intl_types; recheck_intl_types()"

    To recheck all players (e.g., after fixing detection logic):
        python -c "from basketball_processor.utils.nba_players import recheck_intl_types; recheck_intl_types(force=True)"

    Returns:
        Dict with counts: {'checked': N, 'pro': N, 'national_team': N, 'both': N}
    """
    cache = _load_lookup_cache()
    confirmed = _load_confirmed()

    # Find players with intl_url (skip false positives)
    to_check = []
    for pid, data in cache.items():
        if pid in FALSE_POSITIVE_IDS:
            continue
        if data and data.get('intl_url'):
            if force or 'intl_pro' not in data:
                to_check.append((pid, data.get('intl_url')))
    for pid, data in confirmed.items():
        if pid in FALSE_POSITIVE_IDS:
            continue
        if data and data.get('intl_url'):
            if force or 'intl_pro' not in data:
                if pid not in [p[0] for p in to_check]:
                    to_check.append((pid, data.get('intl_url')))

    if not to_check:
        print("No international players need type check!")
        return {'checked': 0, 'pro': 0, 'national_team': 0, 'both': 0}

    if force:
        print(f"Force rechecking {len(to_check)} international players")
    else:
        print(f"Found {len(to_check)} international players to check")

    # Estimate time
    est_minutes = (len(to_check) * RATE_LIMIT_SECONDS) / 60
    print(f"Estimated time: {est_minutes:.0f} minutes (rate limited)")

    if HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper()
    else:
        scraper = None

    pro_count = 0
    national_team_count = 0
    both_count = 0

    for i, (player_id, intl_url) in enumerate(to_check):
        print(f"  {i+1}/{len(to_check)} {player_id}", end="", flush=True)

        # Apply player ID alias if needed (for typos in SR)
        if player_id in PLAYER_ID_ALIASES:
            corrected_id = PLAYER_ID_ALIASES[player_id]
            intl_url = intl_url.replace(player_id, corrected_id)

        intl_types = _check_intl_type(intl_url, scraper)

        # Update cache
        if player_id in cache and cache[player_id]:
            cache[player_id]['intl_pro'] = intl_types['pro']
            cache[player_id]['intl_national_team'] = intl_types['national_team']
            cache[player_id]['intl_leagues'] = intl_types.get('leagues', [])
            cache[player_id]['intl_tournaments'] = intl_types.get('tournaments', [])
            # Remove old intl_type field if present
            cache[player_id].pop('intl_type', None)
            _save_lookup_cache(cache)

        # Update confirmed
        if player_id in confirmed and confirmed[player_id]:
            confirmed[player_id]['intl_pro'] = intl_types['pro']
            confirmed[player_id]['intl_national_team'] = intl_types['national_team']
            confirmed[player_id]['intl_leagues'] = intl_types.get('leagues', [])
            confirmed[player_id]['intl_tournaments'] = intl_types.get('tournaments', [])
            # Remove old intl_type field if present
            confirmed[player_id].pop('intl_type', None)
            _save_confirmed(confirmed)

        # Count results and show leagues
        leagues_str = ', '.join(intl_types.get('leagues', []))
        tourneys_str = ', '.join(intl_types.get('tournaments', []))
        if intl_types['pro'] and intl_types['national_team']:
            both_count += 1
            print(f" → Pro ({leagues_str}) + National Team ({tourneys_str})")
        elif intl_types['pro']:
            pro_count += 1
            print(f" → {leagues_str}" if leagues_str else " → Overseas Pro")
        elif intl_types['national_team']:
            national_team_count += 1
            print(f" → {tourneys_str}" if tourneys_str else " → National Team only")
        else:
            print(" → (none found)")

    print(f"\nComplete! Checked {len(to_check)} international players")
    print(f"  Overseas Pro only: {pro_count}")
    print(f"  National Team only: {national_team_count}")
    print(f"  Both Pro + National Team: {both_count}")

    return {
        'checked': len(to_check),
        'pro': pro_count,
        'national_team': national_team_count,
        'both': both_count
    }


def check_proballers_for_all_players(
    players: List[Dict[str, str]],
    force: bool = False
) -> Dict[str, int]:
    """
    Check Proballers.com for international league data for ALL players.

    This finds players who played internationally but aren't in Basketball Reference's
    international database. Use this to supplement BR data.

    Args:
        players: List of dicts with 'player_id', 'name', 'college_team' keys
        force: If True, recheck even players who already have Proballers data

    Run manually with:
        from basketball_processor.utils.nba_players import check_proballers_for_all_players
        players = [{'player_id': 'john-smith-1', 'name': 'John Smith', 'college_team': 'Virginia'}]
        check_proballers_for_all_players(players)

    Returns:
        Dict with counts: {'checked': N, 'found': N, 'new_international': N}
    """
    if not HAS_PROBALLERS:
        print("Proballers scraper not available!")
        return {'checked': 0, 'found': 0, 'new_international': 0}

    cache = _load_lookup_cache()
    confirmed = _load_confirmed()

    print(f"Checking {len(players)} players against Proballers.com...")

    found_count = 0
    new_intl_count = 0

    for i, player in enumerate(players):
        player_id = player.get('player_id', '')
        name = player.get('name', '')
        college = player.get('college_team', '')
        year = player.get('year')  # Basketball season year (e.g., 2025 for 2024-25)

        if not name or not college:
            continue

        if player_id in FALSE_POSITIVE_IDS:
            continue

        # Skip if already has Proballers data (unless force)
        cached = cache.get(player_id, {}) or {}
        if not force and cached.get('proballers_leagues'):
            continue

        print(f"  {i+1}/{len(players)} {name} ({college})...", end='', flush=True)

        # Check Proballers with year for disambiguation
        proballers_leagues, proballers_id = _check_proballers_leagues(name, college, year=year)

        if proballers_leagues:
            found_count += 1

            # Check if this is a NEW international player (not in BR)
            has_br_intl = bool(cached.get('intl_url'))

            # Update cache with Proballers data
            if player_id not in cache:
                cache[player_id] = {}
            cache[player_id]['proballers_leagues'] = proballers_leagues
            if proballers_id:
                cache[player_id]['proballers_id'] = proballers_id

            # Also save to confirmed for persistent storage and refresh capability
            if player_id not in confirmed:
                confirmed[player_id] = {}
            if confirmed[player_id] is None:
                confirmed[player_id] = {}
            confirmed[player_id]['proballers_leagues'] = proballers_leagues
            if proballers_id:
                confirmed[player_id]['proballers_id'] = proballers_id

            # If no BR international data, mark as international based on Proballers
            if not has_br_intl and proballers_leagues:
                new_intl_count += 1
                # Merge with any existing leagues
                existing_leagues = confirmed[player_id].get('intl_leagues', [])
                merged_leagues = _merge_leagues(existing_leagues, proballers_leagues)
                # Save to both cache and confirmed
                cache[player_id]['intl_pro'] = True
                cache[player_id]['intl_national_team'] = False
                cache[player_id]['intl_leagues'] = merged_leagues
                confirmed[player_id]['intl_pro'] = True
                confirmed[player_id]['intl_national_team'] = False
                confirmed[player_id]['intl_leagues'] = merged_leagues
                print(f" → NEW: {', '.join(proballers_leagues)}")
            else:
                # Merge Proballers leagues with existing BR leagues
                existing_leagues = confirmed[player_id].get('intl_leagues', [])
                merged = _merge_leagues(existing_leagues, proballers_leagues)
                if len(merged) > len(existing_leagues):
                    cache[player_id]['intl_leagues'] = merged
                    confirmed[player_id]['intl_leagues'] = merged
                    print(f" → Added: {', '.join(set(merged) - set(existing_leagues))}")
                else:
                    print(f" → (already have)")
        else:
            print(" → (not found)")

        _save_lookup_cache(cache)
        _save_confirmed(confirmed)

    print(f"\nComplete!")
    print(f"  Checked: {len(players)}")
    print(f"  Found on Proballers: {found_count}")
    print(f"  New international players: {new_intl_count}")

    return {
        'checked': len(players),
        'found': found_count,
        'new_international': new_intl_count
    }


def refresh_active_status() -> Dict[str, Any]:
    """
    Refresh active status for all confirmed pro players.
    Checks all players with pro URLs (not just those who played) since
    players can take time off and return to the league.
    Also refreshes international league/tournament data.
    Runs after website deployment to update cache for next time.
    """
    confirmed = _load_confirmed()
    cache = _load_lookup_cache()

    # Find all players with NBA/WNBA/International URLs or Proballers IDs
    nba_to_check = []
    wnba_to_check = []
    intl_to_check = []
    proballers_to_check = []

    for player_id, data in confirmed.items():
        if not data:
            continue
        # Skip known false positives
        if player_id in FALSE_POSITIVE_IDS:
            continue
        # Check all players with URLs (they could return after time off)
        if data.get('nba_url'):
            nba_to_check.append((player_id, data['nba_url']))
        if data.get('wnba_url'):
            wnba_to_check.append((player_id, data['wnba_url']))
        if data.get('intl_url'):
            intl_to_check.append((player_id, data['intl_url']))
        if data.get('proballers_id'):
            proballers_to_check.append((player_id, data['proballers_id']))

    total = len(nba_to_check) + len(wnba_to_check) + len(intl_to_check) + len(proballers_to_check)
    if total == 0:
        print("No pro players to refresh.")
        return {'nba_checked': 0, 'wnba_checked': 0, 'intl_checked': 0, 'proballers_checked': 0, 'updated': 0}

    print(f"\nRefreshing pro player data: {len(nba_to_check)} NBA + {len(wnba_to_check)} WNBA + {len(intl_to_check)} BR Intl + {len(proballers_to_check)} Proballers...")
    # BR sources have rate limit, Proballers doesn't
    br_count = len(nba_to_check) + len(wnba_to_check) + len(intl_to_check)
    est_minutes = (br_count * RATE_LIMIT_SECONDS) / 60
    print(f"Estimated time: {est_minutes:.1f} minutes (Proballers is fast)")

    if HAS_CLOUDSCRAPER:
        scraper = cloudscraper.create_scraper()
    elif HAS_REQUESTS:
        scraper = None
    else:
        print("No HTTP library available (need cloudscraper or requests)")
        return {'nba_checked': 0, 'wnba_checked': 0, 'updated': 0}

    updated_count = 0
    current_nba, prev_nba = _get_current_nba_seasons()
    current_wnba, prev_wnba = _get_current_wnba_years()

    # Check NBA players
    for i, (player_id, url) in enumerate(nba_to_check):
        print(f"  NBA {i+1}/{len(nba_to_check)} {player_id}...", end='', flush=True)

        try:
            if scraper:
                resp = scraper.get(url, timeout=15)
            else:
                resp = requests.get(url, timeout=15)

            if resp.status_code == 200:
                html = resp.text
                # Look for season in stats table rows only (not nav links)
                # BR uses <th scope="row" ...>2025-26</th> format for season rows
                season_pattern = re.compile(rf'<th[^>]*scope="row"[^>]*>({re.escape(current_nba)}|{re.escape(prev_nba)})</th>')
                is_active = bool(season_pattern.search(html))
                old_status = confirmed[player_id].get('is_active', False)

                if is_active != old_status:
                    confirmed[player_id]['is_active'] = is_active
                    if player_id in cache and cache[player_id]:
                        cache[player_id]['is_active'] = is_active
                    updated_count += 1
                    status_str = "ACTIVE" if is_active else "INACTIVE"
                    print(f" → {status_str} (was {'active' if old_status else 'inactive'})")
                else:
                    print(f" → {'active' if is_active else 'inactive'} (unchanged)")
            else:
                print(f" → HTTP {resp.status_code}")

        except Exception as e:
            print(f" → Error: {e}")

        time.sleep(RATE_LIMIT_SECONDS)

    # Check WNBA players
    for i, (player_id, url) in enumerate(wnba_to_check):
        print(f"  WNBA {i+1}/{len(wnba_to_check)} {player_id}...", end='', flush=True)

        try:
            if scraper:
                resp = scraper.get(url, timeout=15)
            else:
                resp = requests.get(url, timeout=15)

            if resp.status_code == 200:
                html = resp.text
                # Look for season year in stats table rows only (not nav links)
                season_pattern = re.compile(rf'<th[^>]*scope="row"[^>]*>({re.escape(current_wnba)}|{re.escape(prev_wnba)})</th>')
                is_active = bool(season_pattern.search(html))
                old_status = confirmed[player_id].get('is_wnba_active', False)

                if is_active != old_status:
                    confirmed[player_id]['is_wnba_active'] = is_active
                    if player_id in cache and cache[player_id]:
                        cache[player_id]['is_wnba_active'] = is_active
                    updated_count += 1
                    status_str = "ACTIVE" if is_active else "INACTIVE"
                    print(f" → {status_str} (was {'active' if old_status else 'inactive'})")
                else:
                    print(f" → {'active' if is_active else 'inactive'} (unchanged)")
            else:
                print(f" → HTTP {resp.status_code}")

        except Exception as e:
            print(f" → Error: {e}")

        time.sleep(RATE_LIMIT_SECONDS)

    # Check International players
    intl_updated = 0
    for i, (player_id, url) in enumerate(intl_to_check):
        print(f"  Intl {i+1}/{len(intl_to_check)} {player_id}...", end='', flush=True)

        try:
            # _check_intl_type handles its own rate limiting
            intl_types = _check_intl_type(url, scraper)

            old_pro = confirmed[player_id].get('intl_pro', False)
            old_national = confirmed[player_id].get('intl_national_team', False)
            old_leagues = set(confirmed[player_id].get('intl_leagues', []))
            old_tournaments = set(confirmed[player_id].get('intl_tournaments', []))

            new_leagues = set(intl_types.get('leagues', []))
            new_tournaments = set(intl_types.get('tournaments', []))

            # Check for any changes
            changed = False
            changes = []

            if intl_types['pro'] != old_pro:
                changed = True
                changes.append(f"pro: {old_pro}→{intl_types['pro']}")
            if intl_types['national_team'] != old_national:
                changed = True
                changes.append(f"natl: {old_national}→{intl_types['national_team']}")
            if new_leagues - old_leagues:
                changed = True
                changes.append(f"+leagues: {new_leagues - old_leagues}")
            if new_tournaments - old_tournaments:
                changed = True
                changes.append(f"+tournaments: {new_tournaments - old_tournaments}")

            if changed:
                confirmed[player_id]['intl_pro'] = intl_types['pro']
                confirmed[player_id]['intl_national_team'] = intl_types['national_team']
                confirmed[player_id]['intl_leagues'] = intl_types.get('leagues', [])
                confirmed[player_id]['intl_tournaments'] = intl_types.get('tournaments', [])
                if player_id in cache and cache[player_id]:
                    cache[player_id]['intl_pro'] = intl_types['pro']
                    cache[player_id]['intl_national_team'] = intl_types['national_team']
                    cache[player_id]['intl_leagues'] = intl_types.get('leagues', [])
                    cache[player_id]['intl_tournaments'] = intl_types.get('tournaments', [])
                intl_updated += 1
                updated_count += 1
                print(f" → UPDATED: {', '.join(changes)}")
            else:
                leagues_str = ', '.join(new_leagues) if new_leagues else 'none'
                print(f" → {leagues_str} (unchanged)")

        except Exception as e:
            print(f" → Error: {e}")

    # Check Proballers players
    proballers_updated = 0
    if HAS_PROBALLERS and proballers_to_check:
        from .proballers_scraper import get_player_pro_leagues
        for i, (player_id, pb_id) in enumerate(proballers_to_check):
            print(f"  Proballers {i+1}/{len(proballers_to_check)} {player_id}...", end='', flush=True)

            try:
                # Force refresh to get latest data from Proballers
                new_leagues = get_player_pro_leagues(pb_id, scraper, force_refresh=True)
                old_leagues = set(confirmed[player_id].get('proballers_leagues', []))
                new_leagues_set = set(new_leagues)

                added_leagues = new_leagues_set - old_leagues
                if added_leagues:
                    confirmed[player_id]['proballers_leagues'] = new_leagues
                    if player_id in cache and cache[player_id]:
                        cache[player_id]['proballers_leagues'] = new_leagues
                    # Also update intl_leagues if this is their only intl source
                    if not confirmed[player_id].get('intl_url'):
                        existing_intl = set(confirmed[player_id].get('intl_leagues', []))
                        merged_intl = _merge_leagues(list(existing_intl), new_leagues)
                        confirmed[player_id]['intl_leagues'] = merged_intl
                        confirmed[player_id]['intl_pro'] = True
                        if player_id in cache and cache[player_id]:
                            cache[player_id]['intl_leagues'] = merged_intl
                            cache[player_id]['intl_pro'] = True
                    proballers_updated += 1
                    updated_count += 1
                    print(f" → +{added_leagues}")
                else:
                    leagues_str = ', '.join(new_leagues) if new_leagues else 'none'
                    print(f" → {leagues_str} (unchanged)")

            except Exception as e:
                print(f" → Error: {e}")

            # Proballers has no rate limit (network latency is sufficient)
    elif proballers_to_check:
        print("  Skipping Proballers (scraper not available)")

    # Save updated data
    _save_confirmed(confirmed)
    _save_lookup_cache(cache)

    print(f"\nPro player refresh complete!")
    print(f"  NBA checked: {len(nba_to_check)}")
    print(f"  WNBA checked: {len(wnba_to_check)}")
    print(f"  BR International checked: {len(intl_to_check)}")
    print(f"  Proballers checked: {len(proballers_to_check)}")
    print(f"  Updated: {updated_count} (intl: {intl_updated}, proballers: {proballers_updated})")

    return {
        'nba_checked': len(nba_to_check),
        'wnba_checked': len(wnba_to_check),
        'intl_checked': len(intl_to_check),
        'proballers_checked': len(proballers_to_check),
        'updated': updated_count
    }
