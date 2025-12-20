"""
NBA player lookup utilities.
Uses Sports Reference links to determine if a college player went to the NBA.
Also falls back to nba_api name matching with manual overrides.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import time

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
# Days between automatic null re-checks
RECHECK_INTERVAL_DAYS = 90

# Sports Reference base URL
SPORTS_REF_BASE = "https://www.sports-reference.com/cbb/players/"

# Rate limiting: Sports Reference allows 20 requests/minute
# We use 3.1 seconds to stay under limit (19 req/min)
RATE_LIMIT_SECONDS = 3.1

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
}

# Player IDs to INCLUDE (confirmed NBA players)
CONFIRMED_NBA_IDS = {
    'jayson-tatum-1': {'nba_url': 'https://www.basketball-reference.com/players/t/tatumja01.html', 'is_active': True},
    'zion-williamson-1': {'nba_url': 'https://www.basketball-reference.com/players/w/willizi01.html', 'is_active': True},
    'kyle-guy-1': {'nba_url': 'https://www.basketball-reference.com/players/g/guuky01.html', 'is_active': False},
    'ty-jerome-1': {'nba_url': 'https://www.basketball-reference.com/players/j/jeromty01.html', 'is_active': True},
    'greivis-vasquez-1': {'nba_url': 'https://www.basketball-reference.com/players/v/vasqugr01.html', 'is_active': False},
    'deandre-hunter-1': {'nba_url': 'https://www.basketball-reference.com/players/h/huntede01.html', 'is_active': True},
    'cam-reddish-1': {'nba_url': 'https://www.basketball-reference.com/players/r/reddica01.html', 'is_active': True},
    'grayson-allen-1': {'nba_url': 'https://www.basketball-reference.com/players/a/allengr01.html', 'is_active': True},
    'luke-kennard-1': {'nba_url': 'https://www.basketball-reference.com/players/k/kennalu01.html', 'is_active': True},
    'bronny-james-1': {'nba_url': 'https://www.basketball-reference.com/players/j/jamesbr02.html', 'is_active': True},
    'stephon-castle-1': {'nba_url': 'https://www.basketball-reference.com/players/c/castlst01.html', 'is_active': True},
    'donovan-clingan-1': {'nba_url': 'https://www.basketball-reference.com/players/c/clingdo01.html', 'is_active': True},
    'tre-jones-1': {'nba_url': 'https://www.basketball-reference.com/players/j/jonestr01.html', 'is_active': True},
    'theo-pinson-1': {'nba_url': 'https://www.basketball-reference.com/players/p/pinsoth01.html', 'is_active': False},
    'jose-alvarado-1': {'nba_url': 'https://www.basketball-reference.com/players/a/alvarjo01.html', 'is_active': True},
    'nickeil-alexander-walker-1': {'nba_url': 'https://www.basketball-reference.com/players/a/alexani01.html', 'is_active': True},
    'mamadi-diakite-1': {'nba_url': 'https://www.basketball-reference.com/players/d/diakima01.html', 'is_active': False},
    'isaiah-collier-1': {'nba_url': 'https://www.basketball-reference.com/players/c/colliis01.html', 'is_active': True},
    'ryan-nembhard-1': {'nba_url': 'https://www.basketball-reference.com/players/n/nemhary01.html', 'is_active': True},
    'brooks-barnhizer-1': {'nba_url': 'https://www.basketball-reference.com/players/b/barnhbr01.html', 'is_active': True},
}


def _load_lookup_cache() -> Dict[str, Any]:
    """Load cached NBA lookup results."""
    if NBA_LOOKUP_CACHE_FILE.exists():
        try:
            with open(NBA_LOOKUP_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_lookup_cache(cache: Dict[str, Any]) -> None:
    """Save NBA lookup cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(NBA_LOOKUP_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def _load_confirmed() -> Dict[str, Any]:
    """Load persistent confirmed NBA/Intl players (survives cache clears)."""
    if NBA_CONFIRMED_FILE.exists():
        try:
            with open(NBA_CONFIRMED_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
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

    # Check hardcoded confirmed NBA players
    if player_id in CONFIRMED_NBA_IDS:
        return CONFIRMED_NBA_IDS[player_id]

    # Check persistent confirmed file (survives cache clears)
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
                # Check if currently active (look for recent season stats)
                is_active = '2024-25' in html or '2025-26' in html
                result['nba_url'] = nba_url
                result['is_active'] = is_active

            # Look for Basketball Reference WNBA link
            wnba_match = re.search(
                r'href="(https://www\.basketball-reference\.com/wnba/players/[^"]+)"[^>]*>Basketball-Reference\.com</a>',
                html
            )

            if wnba_match:
                wnba_url = wnba_match.group(1)
                # Check if currently active
                is_wnba_active = '2024' in html or '2025' in html
                result['wnba_url'] = wnba_url
                result['is_wnba_active'] = is_wnba_active

            # Look for Basketball Reference International link
            intl_match = re.search(
                r'href="(https://www\.basketball-reference\.com/international/players/[^"]+)"',
                html
            )

            if intl_match:
                intl_url = intl_match.group(1)
                result['intl_url'] = intl_url

        # Always check Basketball Reference international directly as fallback
        # (Works even when Sports Reference is rate limited or doesn't show the link)
        if 'intl_url' not in result:
            try:
                time.sleep(RATE_LIMIT_SECONDS)  # Rate limit BR requests too
                intl_check_url = f"https://www.basketball-reference.com/international/players/{player_id}.html"
                if HAS_CLOUDSCRAPER:
                    intl_response = scraper.head(intl_check_url, timeout=10, allow_redirects=True)
                else:
                    intl_response = requests.head(intl_check_url, timeout=10, allow_redirects=True)
                if intl_response.status_code == 200:
                    result['intl_url'] = intl_check_url
            except Exception:
                pass  # Silently ignore failures

        if result:
            cache[player_id] = result
            _save_lookup_cache(cache)
            _add_to_confirmed(player_id, result)  # Persist for cache clears
            return result
        else:
            cache[player_id] = None
            _save_lookup_cache(cache)
            return None

    except Exception as e:
        print(f"Warning: Could not fetch {url}: {e}")
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
        # Check manual exclusions
        if player_id in FALSE_POSITIVE_IDS:
            results[player_id] = None
            continue

        # Check hardcoded confirmed list
        if player_id in CONFIRMED_NBA_IDS:
            results[player_id] = CONFIRMED_NBA_IDS[player_id]
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

    # Fetch missing players
    if to_fetch and HAS_REQUESTS:
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
    if player_id in CONFIRMED_NBA_IDS:
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
    if player_id in CONFIRMED_NBA_IDS:
        return CONFIRMED_NBA_IDS[player_id]

    cache = _load_lookup_cache()
    cached = cache.get(player_id)
    if cached and 'nba_url' in cached:
        return cached
    return None


def get_intl_player_info_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get international career info for a player by their Sports Reference ID."""
    if player_id in FALSE_POSITIVE_IDS:
        return None

    cache = _load_lookup_cache()
    cached = cache.get(player_id)
    if cached and 'intl_url' in cached:
        return cached
    return None


def get_player_pro_info_by_id(player_id: str) -> Optional[Dict[str, Any]]:
    """Get combined NBA and international info for a player."""
    if player_id in FALSE_POSITIVE_IDS:
        return None
    if player_id in CONFIRMED_NBA_IDS:
        return CONFIRMED_NBA_IDS[player_id]

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
        except Exception:
            continue

    print(f"Found {len(player_ids)} unique players in {len(game_files)} cached games")

    # Filter out already checked players
    cache = _load_lookup_cache()
    to_check = []
    for pid in player_ids:
        if pid in FALSE_POSITIVE_IDS:
            continue
        if pid in CONFIRMED_NBA_IDS:
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

    # Count total NBA players in cache
    cache = _load_lookup_cache()
    total_nba = sum(1 for v in cache.values() if v is not None) + len(CONFIRMED_NBA_IDS)
    print(f"Total NBA players: {total_nba} (cache: {sum(1 for v in cache.values() if v is not None)}, confirmed: {len(CONFIRMED_NBA_IDS)})")

    return {'total': len(player_ids), 'checked': len(to_check), 'nba_found': nba_found, 'skipped': len(player_ids) - len(to_check)}


def _get_last_recheck_time() -> Optional[datetime]:
    """Get the timestamp of the last null re-check."""
    if NBA_RECHECK_TIMESTAMP_FILE.exists():
        try:
            ts = NBA_RECHECK_TIMESTAMP_FILE.read_text().strip()
            return datetime.fromisoformat(ts)
        except Exception:
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
        intl_check_url = f"https://www.basketball-reference.com/international/players/{player_id}.html"
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
        except Exception:
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


def recheck_female_players_for_wnba() -> Dict[str, int]:
    """
    Re-check female players for WNBA status.
    Only checks players from women's games who don't already have wnba_url in cache.

    Run manually with:
        python -c "from basketball_processor.utils.nba_players import recheck_female_players_for_wnba; recheck_female_players_for_wnba()"

    Returns:
        Dict with counts: {'checked': N, 'wnba_found': N}
    """
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
        except Exception:
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

    print(f"\nComplete! Checked {len(to_check)} female players")
    print(f"  Found {wnba_found} WNBA, {intl_found} International")
    return {'checked': len(to_check), 'wnba_found': wnba_found, 'intl_found': intl_found}
