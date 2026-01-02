"""
Proballers.com scraper for international player career data.

This supplements Basketball Reference data by providing:
- More comprehensive international league coverage
- College team to professional career mapping
- Additional player identification via college rosters

Usage:
    from basketball_processor.utils.proballers_scraper import (
        get_player_career,
        find_player_by_college,
        get_college_roster
    )

    # Get career for known player ID
    career = get_player_career(69259)  # Devon Hall

    # Find player from college roster
    player_id = find_player_by_college('virginia-cavaliers', 'Devon Hall')

    # Get all players from a college
    roster = get_college_roster('virginia-cavaliers')
"""

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Rate limiting (0 = no delay; network latency provides natural throttling)
RATE_LIMIT_SECONDS = 0

# Cache file (can be cleared)
CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
PROBALLERS_CACHE_FILE = CACHE_DIR / 'proballers_cache.json'

# Persistent data (survives cache clears)
DATA_DIR = Path(__file__).parent.parent.parent / 'data'
NCAA_TEAMS_FILE = DATA_DIR / 'proballers_ncaa_teams.json'

# League name mapping (Proballers slug -> display name)
LEAGUE_NAMES = {
    # Major European leagues
    'euroleague': 'EuroLeague',
    'eurocup': 'EuroCup',
    'basketball-champions-league': 'BCL',
    'fiba-europe-cup': 'FIBA Europe Cup',

    # National leagues
    'spain-liga-endesa': 'Liga ACB (Spain)',
    'italy-lba-serie-a': 'Serie A (Italy)',
    'france-betclic-elite': 'LNB Pro A (France)',
    'france-elite-2': 'Pro B (France)',
    'turkey-bsl': 'BSL (Turkey)',
    'germany-easycredit-bbl': 'BBL (Germany)',
    'australia-nbl': 'NBL (Australia)',
    'china-cba': 'CBA (China)',
    'japan-b1-league': 'B.League (Japan)',
    'greece-heba-a1': 'Greek League',
    'greece-basket-league': 'Greek League',
    'israel-winner-league': 'Israeli League',
    'russia-vtb-united-league': 'VTB United League',
    'adriatic-aba-league': 'ABA League',
    'poland-plk': 'PLK (Poland)',
    'philippines-pba': 'PBA (Philippines)',
    'korea-kbl': 'KBL (Korea)',
    'taiwan-p-league': 'P.League (Taiwan)',
    'puerto-rico-bsn': 'BSN (Puerto Rico)',
    'argentina-liga-nacional': 'Liga Nacional (Argentina)',
    'brazil-nbb': 'NBB (Brazil)',
    'mexico-lnbp': 'LNBP (Mexico)',

    # North American
    'nba': 'NBA',
    'wnba': 'WNBA',
    'g-league': 'G-League',
    'ncaa': 'NCAA',
}

# Professional leagues (not college/development)
PRO_LEAGUES = {
    # European
    'euroleague', 'eurocup', 'basketball-champions-league', 'fiba-europe-cup',
    'spain-liga-endesa', 'italy-lba-serie-a', 'france-betclic-elite',
    'turkey-bsl', 'germany-easycredit-bbl', 'greece-heba-a1', 'greece-basket-league',
    'israel-winner-league', 'russia-vtb-united-league', 'adriatic-aba-league',
    'poland-plk',
    # Asia-Pacific
    'australia-nbl', 'china-cba', 'japan-b1-league', 'philippines-pba',
    'korea-kbl', 'taiwan-p-league',
    # Americas
    'nba', 'wnba', 'puerto-rico-bsn', 'argentina-liga-nacional',
    'brazil-nbb', 'mexico-lnbp',
}

try:
    import cloudscraper
    HAS_CLOUDSCRAPER = True
except ImportError:
    HAS_CLOUDSCRAPER = False
    cloudscraper = None


def _get_scraper():
    """Get a cloudscraper instance."""
    if HAS_CLOUDSCRAPER:
        return cloudscraper.create_scraper()
    return None


def _load_cache() -> Dict[str, Any]:
    """Load Proballers cache."""
    if PROBALLERS_CACHE_FILE.exists():
        try:
            with open(PROBALLERS_CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {'players': {}, 'rosters': {}}


def _save_cache(cache: Dict[str, Any]) -> None:
    """Save Proballers cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROBALLERS_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def _load_ncaa_teams() -> Dict[str, Dict[str, Any]]:
    """Load NCAA teams cache."""
    if NCAA_TEAMS_FILE.exists():
        try:
            with open(NCAA_TEAMS_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_ncaa_teams(teams: Dict[str, Dict[str, Any]]) -> None:
    """Save NCAA teams cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(NCAA_TEAMS_FILE, 'w') as f:
        json.dump(teams, f, indent=2)


def fetch_ncaa_teams(scraper=None, force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """
    Fetch all NCAA teams from Proballers and cache them.

    Returns:
        Dict mapping team slug to {'id': int, 'slug': str, 'name': str}
    """
    if not force_refresh:
        cached = _load_ncaa_teams()
        if cached:
            return cached

    if scraper is None:
        scraper = _get_scraper()
    if scraper is None:
        return {}

    print("Fetching NCAA teams from Proballers...")
    time.sleep(RATE_LIMIT_SECONDS)

    url = 'https://www.proballers.com/basketball/league/5/ncaa/teams'
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            print(f"  Failed to fetch teams: {response.status_code}")
            return {}

        html = response.text

        # Find all team links
        team_matches = re.findall(
            r'/basketball/team/(\d+)/([^/\"]+)',
            html
        )

        teams = {}
        for tid, slug in team_matches:
            if slug not in teams:
                # Extract readable name from slug
                name = slug.replace('-', ' ').title()
                teams[slug] = {
                    'id': int(tid),
                    'slug': slug,
                    'name': name
                }

        print(f"  Found {len(teams)} NCAA teams")
        _save_ncaa_teams(teams)
        return teams

    except Exception as e:
        print(f"  Error fetching NCAA teams: {e}")
        return {}


# Manual overrides for SR slugs that need special handling
SR_SLUG_OVERRIDES = {
    'nc-state': 'north-carolina-state-wolfpack',
    'saint-marys': 'saint-mary-s-gaels',
    'saint-marys-ca': 'saint-mary-s-gaels',
    'loyola-(il)': 'loyola-il-ramblers',
    'loyola-(md)': 'loyola-md-greyhounds',
    'miami-(fl)': 'miami-fl-hurricanes',
    'miami-(oh)': 'miami-oh-redhawks',
    'northern-iowa': 'northern-iowa-panthers',
    'pitt': 'pittsburgh-panthers',
    'saint-francis-(pa)': 'st-francis-pa-red-flash',
    'st-francis-(ny)': 'st-francis-ny-terriers',
    'uconn': 'connecticut-huskies',
    'california': 'california-golden-bears',
    'san-francisco': 'san-francisco-dons',
    'drexel': 'drexel-dragons',
    'florida-gulf-coast': 'florida-gulf-coast-eagles',
    'notre-dame': 'notre-dame-fighting-irish',
    'unc': 'north-carolina-tar-heels',
}

# Cache for SR slug -> Proballers slug mapping (built once from teams cache)
_sr_to_pb_mapping: Optional[Dict[str, str]] = None


def _build_sr_mapping(teams: Dict[str, Dict[str, Any]]) -> Dict[str, str]:
    """Build SR slug -> Proballers slug mapping from cached teams."""
    mapping = {}

    # Group by prefix (SR-style slug)
    prefix_groups: Dict[str, List[tuple]] = {}
    for pb_slug, info in teams.items():
        # Common mascot/suffix words to strip
        parts = pb_slug.split('-')
        # Try progressively shorter prefixes
        for i in range(len(parts) - 1, 0, -1):
            prefix = '-'.join(parts[:i])
            if prefix not in prefix_groups:
                prefix_groups[prefix] = []
            prefix_groups[prefix].append((len(pb_slug), pb_slug, info['id']))

    # For each prefix, pick the shortest slug (main school)
    # Skip if prefix starts with regional qualifier
    regional = ('eastern', 'western', 'northern', 'central', 'southern')
    for prefix, candidates in prefix_groups.items():
        if prefix.split('-')[0] in regional:
            continue
        # Filter out regional variants
        filtered = [(l, s, i) for l, s, i in candidates
                    if not s[len(prefix)+1:].split('-')[0] in regional]
        if filtered:
            filtered.sort()  # Shortest first
            mapping[prefix] = filtered[0][1]

    # Add manual overrides
    mapping.update(SR_SLUG_OVERRIDES)

    return mapping


def find_team_id(sr_slug: str, scraper=None) -> Optional[int]:
    """
    Find Proballers team ID from a Sports Reference slug.

    Args:
        sr_slug: Sports Reference team slug (e.g., 'san-francisco')
        scraper: Optional cloudscraper instance

    Returns:
        Proballers team ID if found, None otherwise
    """
    global _sr_to_pb_mapping

    teams = fetch_ncaa_teams(scraper)
    if not teams:
        return None

    # Build mapping once
    if _sr_to_pb_mapping is None:
        _sr_to_pb_mapping = _build_sr_mapping(teams)

    sr_slug = sr_slug.lower().strip()

    # Direct lookup
    if sr_slug in _sr_to_pb_mapping:
        pb_slug = _sr_to_pb_mapping[sr_slug]
        if pb_slug in teams:
            return teams[pb_slug]['id']

    # Exact match on Proballers slug (caller passed full slug)
    if sr_slug in teams:
        return teams[sr_slug]['id']

    return None


def get_player_career(player_id: int, scraper=None, force_refresh: bool = False) -> Optional[Dict[str, Any]]:
    """
    Get a player's career info from Proballers.

    Args:
        player_id: Proballers player ID
        scraper: Optional cloudscraper instance
        force_refresh: If True, ignore cache and fetch fresh data

    Returns:
        Dict with player info including:
        - name: Player name
        - teams: List of team dicts with year, team_name, league info
        - pro_leagues: List of professional leagues played in
        - college: College team if any
    """
    cache = _load_cache()
    cache_key = str(player_id)

    if not force_refresh and cache_key in cache.get('players', {}):
        return cache['players'][cache_key]

    if scraper is None:
        scraper = _get_scraper()
    if scraper is None:
        return None

    time.sleep(RATE_LIMIT_SECONDS)

    url = f'https://www.proballers.com/basketball/player/{player_id}/'
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            return None

        html = response.text

        # Extract player name from title
        name_match = re.search(r'<title>([^,]+),', html)
        name = name_match.group(1).strip() if name_match else 'Unknown'

        # Extract career entries with ACTUAL league info from HTML
        # Pattern: team link followed by league link in same context
        career_pattern = re.findall(
            r'/basketball/team/(\d+)/([^/\"]+)/(\d{4}).*?/basketball/league/(\d+)/([^\"]+)',
            html,
            re.DOTALL
        )

        teams = []
        pro_leagues = set()
        college = None
        seen_entries = set()

        for team_id, team_slug, year, league_id, league_slug in career_pattern:
            # Deduplicate entries
            entry_key = f'{year}:{team_slug}'
            if entry_key in seen_entries:
                continue
            seen_entries.add(entry_key)

            # Get display name for league
            league_display = LEAGUE_NAMES.get(league_slug, league_slug.replace('-', ' ').title())

            teams.append({
                'year': int(year),
                'team_id': int(team_id),
                'team_slug': team_slug,
                'team_name': team_slug.replace('-', ' ').title(),
                'league_slug': league_slug,
                'league': league_display
            })

            # Track pro leagues (not college/development)
            if league_slug in PRO_LEAGUES:
                pro_leagues.add(league_display)
            elif league_slug == 'ncaa' and college is None:
                college = team_slug.replace('-', ' ').title()

        # Sort teams by year
        teams.sort(key=lambda x: x['year'])

        result = {
            'name': name,
            'player_id': player_id,
            'teams': teams,
            'pro_leagues': sorted(list(pro_leagues)),
            'college': college
        }

        # Cache the result
        if 'players' not in cache:
            cache['players'] = {}
        cache['players'][cache_key] = result
        _save_cache(cache)

        return result

    except Exception as e:
        print(f"Error fetching player {player_id}: {e}")
        return None


def _guess_league_from_team(team_slug: str) -> str:
    """Guess league from team slug patterns."""
    # Check if it's an NCAA team (check cached teams)
    ncaa_teams = _load_ncaa_teams()
    if team_slug in ncaa_teams or any(team_slug.startswith(t.split('-')[0] + '-') for t in ncaa_teams):
        return 'ncaa'

    # Known patterns
    patterns = {
        'blue': 'g-league',  # Oklahoma City Blue, etc.
        'thunder': 'nba',
        'lakers': 'nba',
        'celtics': 'nba',
        'warriors': 'nba',
        'istanbul': 'turkey-bsl',
        'efes': 'turkey-bsl',
        'fenerbahce': 'euroleague',
        'milan': 'euroleague',
        'barcelona': 'euroleague',
        'real-madrid': 'euroleague',
        'maccabi': 'euroleague',
        'panathinaikos': 'euroleague',
        'olympiacos': 'euroleague',
        'cska': 'euroleague',
        'taipans': 'australia-nbl',
        'kings': 'australia-nbl',  # Sydney Kings, etc.
        'breakers': 'australia-nbl',
        'bamberg': 'germany-easycredit-bbl',
        'alba-berlin': 'germany-easycredit-bbl',
        'bayern': 'germany-easycredit-bbl',
    }

    for pattern, league in patterns.items():
        if pattern in team_slug.lower():
            return league

    return 'unknown'


def get_college_roster(college_slug: str, scraper=None) -> List[Dict[str, Any]]:
    """
    Get all-time roster for a college team.

    Args:
        college_slug: Sports Reference or Proballers team slug
        scraper: Optional cloudscraper instance

    Returns:
        List of player dicts with 'id', 'name', 'slug'
    """
    cache = _load_cache()
    cache_key = f"roster_{college_slug}"

    if cache_key in cache.get('rosters', {}):
        return cache['rosters'][cache_key]

    if scraper is None:
        scraper = _get_scraper()
    if scraper is None:
        return []

    # Use dynamic team lookup
    team_id = find_team_id(college_slug, scraper)
    if team_id is None:
        return []

    # Get the actual Proballers slug from the teams cache
    teams = _load_ncaa_teams()
    pb_slug = college_slug  # default
    for slug, info in teams.items():
        if info['id'] == team_id:
            pb_slug = slug
            break

    time.sleep(RATE_LIMIT_SECONDS)

    url = f'https://www.proballers.com/basketball/team/{team_id}/{pb_slug}/all-time-roster'
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            return []

        html = response.text

        # Extract player links - use title attribute which has "Last First" format
        players = []
        player_matches = re.findall(
            r'href="/basketball/player/(\d+)/([^\"]+)"[^>]*title="([^\"]*)"',
            html
        )

        seen = set()
        for pid, slug, title_name in player_matches:
            if pid not in seen:
                # Title is "Last First" format, convert to "First Last"
                if title_name.strip():
                    parts = title_name.strip().split()
                    if len(parts) >= 2:
                        # "Sharma Ishan" -> "Ishan Sharma"
                        name = ' '.join(parts[1:] + [parts[0]])
                    else:
                        name = title_name.strip()
                else:
                    name = slug.replace('-', ' ').title()

                players.append({
                    'id': int(pid),
                    'slug': slug,
                    'name': name
                })
                seen.add(pid)

        # Cache the result
        if 'rosters' not in cache:
            cache['rosters'] = {}
        cache['rosters'][cache_key] = players
        _save_cache(cache)

        return players

    except Exception as e:
        print(f"Error fetching roster for {college_slug}: {e}")
        return []


def find_player_by_college(
    college_slug: str,
    player_name: str,
    year: Optional[int] = None,
    scraper=None
) -> Optional[int]:
    """
    Find a player's Proballers ID by their college and name.

    Args:
        college_slug: Proballers team slug (e.g., 'virginia-cavaliers')
        player_name: Player name to search for
        year: Optional year to filter by (basketball season year, e.g., 2025 for 2024-25 season)
        scraper: Optional cloudscraper instance

    Returns:
        Proballers player ID if found, None otherwise
    """
    roster = get_college_roster(college_slug, scraper)

    if not roster:
        return None

    # Normalize name for matching
    search_name = player_name.lower().strip()
    search_parts = set(search_name.split())

    # Collect all candidates that match by name
    candidates = []
    for player in roster:
        roster_name = player['name'].lower()
        roster_parts = set(roster_name.split())

        # Exact match
        if search_name == roster_name:
            candidates.append(player)
            continue

        # Check slug
        if search_name.replace(' ', '-') == player['slug']:
            candidates.append(player)
            continue

        # Fuzzy match - both first and last name match
        if len(search_parts & roster_parts) >= 2:
            candidates.append(player)

    if not candidates:
        return None

    # If only one candidate, return it
    if len(candidates) == 1:
        return candidates[0]['id']

    # Multiple candidates - use year to disambiguate
    if year:
        for candidate in candidates:
            career = get_player_career(candidate['id'], scraper)
            if career:
                # Check if any NCAA team year matches
                for team in career.get('teams', []):
                    if 'ncaa' in team.get('league', '').lower():
                        team_year = team.get('year', 0)
                        # Allow 1 year tolerance for season overlap
                        if abs(team_year - year) <= 1:
                            return candidate['id']

    # No year match found, return first candidate (original behavior)
    return candidates[0]['id']


def get_player_pro_leagues(player_id: int, scraper=None) -> List[str]:
    """
    Get list of professional leagues a player has played in.

    Args:
        player_id: Proballers player ID
        scraper: Optional cloudscraper instance

    Returns:
        List of league display names
    """
    career = get_player_career(player_id, scraper)
    if career:
        return career.get('pro_leagues', [])
    return []


def lookup_player_leagues(college_team: str, player_name: str) -> List[str]:
    """
    High-level function to find a player's professional leagues.

    Args:
        college_team: College team name (will be converted to slug)
        player_name: Player name

    Returns:
        List of professional leagues played in
    """
    # Convert team name to slug
    college_slug = college_team.lower().replace(' ', '-')

    # Find player ID
    player_id = find_player_by_college(college_slug, player_name)
    if player_id is None:
        return []

    # Get their leagues
    return get_player_pro_leagues(player_id)


def supplement_international_data(
    player_name: str,
    college_team: str,
    current_leagues: List[str]
) -> Tuple[List[str], bool]:
    """
    Supplement international league data from Proballers.

    Use this when Basketball Reference doesn't have complete data.

    Args:
        player_name: Player name
        college_team: College team they played for
        current_leagues: Leagues already known from BR

    Returns:
        Tuple of (updated_leagues, found_new_data)
    """
    # Convert team name to slug
    college_slug = college_team.lower().replace(' ', '-').replace("'", '')

    # Common name variations
    slug_variations = [
        college_slug,
        college_slug.replace('-university', ''),
        college_slug.replace('university-of-', ''),
        college_slug.replace('-state', ''),
    ]

    player_id = None
    for slug in slug_variations:
        player_id = find_player_by_college(slug, player_name)
        if player_id:
            break

    if player_id is None:
        return current_leagues, False

    # Get their leagues from Proballers
    proballers_leagues = get_player_pro_leagues(player_id)

    if not proballers_leagues:
        return current_leagues, False

    # Merge with existing leagues
    current_set = set(current_leagues)
    new_leagues = []

    for league in proballers_leagues:
        # Normalize league names for comparison
        normalized = league.lower()
        already_have = False
        for existing in current_set:
            if normalized in existing.lower() or existing.lower() in normalized:
                already_have = True
                break
        if not already_have:
            new_leagues.append(league)

    if new_leagues:
        return current_leagues + new_leagues, True

    return current_leagues, False


def batch_supplement_leagues(
    players: List[Dict[str, str]],
    check_only_missing: bool = True
) -> Dict[str, List[str]]:
    """
    Batch supplement international league data for multiple players.

    Args:
        players: List of dicts with 'name', 'college_team', 'current_leagues'
        check_only_missing: If True, only check players with no current leagues

    Returns:
        Dict mapping player name to their leagues
    """
    results = {}
    scraper = _get_scraper()

    for i, player in enumerate(players):
        name = player['name']
        college = player.get('college_team', '')
        current = player.get('current_leagues', [])

        if check_only_missing and current:
            results[name] = current
            continue

        print(f"  {i+1}/{len(players)} Checking {name}...", end='', flush=True)

        leagues, found_new = supplement_international_data(name, college, current)
        results[name] = leagues

        if found_new:
            print(f" → {', '.join(leagues)}")
        else:
            print(" → (no new data)")

    return results


if __name__ == '__main__':
    # Test the scraper
    print("Testing Proballers scraper...")

    # Test getting Devon Hall's career
    print("\n1. Getting Devon Hall's career:")
    career = get_player_career(69259)
    if career:
        print(f"   Name: {career['name']}")
        print(f"   College: {career['college']}")
        print(f"   Pro leagues: {career['pro_leagues']}")
        print(f"   Teams: {len(career['teams'])}")

    # Test getting Virginia roster
    print("\n2. Getting Virginia roster:")
    roster = get_college_roster('virginia-cavaliers')
    print(f"   Players: {len(roster)}")
    if roster:
        print(f"   First 5: {[p['name'] for p in roster[:5]]}")

    # Test finding a player
    print("\n3. Finding Jack Salt by college:")
    pid = find_player_by_college('virginia-cavaliers', 'Jack Salt')
    if pid:
        print(f"   Found ID: {pid}")
        leagues = get_player_pro_leagues(pid)
        print(f"   Pro leagues: {leagues}")
