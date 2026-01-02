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

# Rate limiting
RATE_LIMIT_SECONDS = 2.0

# Cache file
CACHE_DIR = Path(__file__).parent.parent.parent / 'cache'
PROBALLERS_CACHE_FILE = CACHE_DIR / 'proballers_cache.json'

# College team ID mapping (Sports Reference name -> Proballers team ID)
# Built from known teams - can be expanded
COLLEGE_TEAM_IDS = {
    'virginia': 307,
    'duke': 286,
    'north-carolina': 298,
    'kentucky': 293,
    'kansas': 291,
    'gonzaga': 318,
    'villanova': 306,
    'michigan-state': 296,
    'louisville': 294,
    'ucla': 305,
    'arizona': 275,
    'florida': 288,
    'syracuse': 303,
    'connecticut': 284,
    'indiana': 290,
    'wisconsin': 310,
    'purdue': 301,
    'ohio-state': 299,
    'michigan': 295,
    'texas': 304,
    'baylor': 278,
    'oregon': 300,
    'maryland': 372,
    'san-diego-state': 435,
    'san-francisco': 356,
    'santa-clara': 455,
    'stanford': 440,
    'california': 320,
    'usc': 445,
    'saint-marys': 391,
    'notre-dame': 381,
    'wake-forest': 308,
    'clemson': 283,
    'virginia-tech': 446,
    'nc-state': 376,
    'miami-fl': 373,
    'boston-college': 280,
    'pittsburgh': 385,
    'georgia-tech': 289,
    # Add more as needed
}

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
    # Known college teams
    if any(team_slug.startswith(college) for college in COLLEGE_TEAM_IDS.keys()):
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
        college_slug: Proballers team slug (e.g., 'virginia-cavaliers')
        scraper: Optional cloudscraper instance

    Returns:
        List of player dicts with 'id', 'name', 'slug'
    """
    cache = _load_cache()
    cache_key = f"roster_{college_slug}"

    if cache_key in cache.get('rosters', {}):
        return cache['rosters'][cache_key]

    # Get team ID from slug
    base_slug = college_slug.split('-')[0]
    team_id = COLLEGE_TEAM_IDS.get(base_slug)

    if team_id is None:
        # Try to find by full slug
        for key, tid in COLLEGE_TEAM_IDS.items():
            if key in college_slug:
                team_id = tid
                break

    if team_id is None:
        return []

    if scraper is None:
        scraper = _get_scraper()
    if scraper is None:
        return []

    time.sleep(RATE_LIMIT_SECONDS)

    url = f'https://www.proballers.com/basketball/team/{team_id}/{college_slug}/all-time-roster'
    try:
        response = scraper.get(url, timeout=15)
        if response.status_code != 200:
            return []

        html = response.text

        # Extract player links
        players = []
        player_matches = re.findall(
            r'href="/basketball/player/(\d+)/([^\"]+)"[^>]*>([^<]*)',
            html
        )

        seen = set()
        for pid, slug, name in player_matches:
            if pid not in seen:
                players.append({
                    'id': int(pid),
                    'slug': slug,
                    'name': name.strip() if name.strip() else slug.replace('-', ' ').title()
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


def find_player_by_college(college_slug: str, player_name: str, scraper=None) -> Optional[int]:
    """
    Find a player's Proballers ID by their college and name.

    Args:
        college_slug: Proballers team slug (e.g., 'virginia-cavaliers')
        player_name: Player name to search for
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

    for player in roster:
        roster_name = player['name'].lower()
        roster_parts = set(roster_name.split())

        # Exact match
        if search_name == roster_name:
            return player['id']

        # Check slug
        if search_name.replace(' ', '-') == player['slug']:
            return player['id']

        # Fuzzy match - both first and last name match
        if len(search_parts & roster_parts) >= 2:
            return player['id']

    return None


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
