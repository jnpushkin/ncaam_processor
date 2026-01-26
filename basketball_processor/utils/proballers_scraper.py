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

    # National leagues - Top tier
    'spain-liga-endesa': 'Liga ACB (Spain)',
    'italy-lba-serie-a': 'Serie A (Italy)',
    'france-betclic-elite': 'LNB Pro A (France)',
    'turkey-bsl': 'BSL (Turkey)',
    'turkey-tbl': 'TBL (Turkey)',
    'germany-easycredit-bbl': 'BBL (Germany)',
    'australia-nbl': 'NBL (Australia)',
    'china-cba': 'CBA (China)',
    'japan-b1-league': 'B.League (Japan)',
    'greece-heba-a1': 'Greek League',
    'greece-basket-league': 'Greek League',
    'super-league-basketball': 'Greek League',
    'israel-winner-league': 'Israeli League',
    'russia-vtb-united-league': 'VTB United League',
    'adriatic-aba-league': 'ABA League',
    'poland-plk': 'PLK (Poland)',
    'bnxt-league': 'BNXT League',
    'uk-bbl': 'BBL (UK)',
    'netherlands-dbl': 'DBL (Netherlands)',
    'netherlands-eredivisie': 'Eredivisie (Netherlands)',
    'finland-korisliiga': 'Korisliiga (Finland)',
    'sweden-basketligan': 'Basketligan (Sweden)',
    'denmark-ligaen': 'Ligaen (Denmark)',
    'slovenia-liga-nova-kbm': 'Liga Nova KBM (Slovenia)',
    'hungary-a-league': 'A Liga (Hungary)',
    'romania-division-a': 'Division A (Romania)',
    'switzerland-sbl': 'SBL (Switzerland)',
    'portugal-liga-profissional': 'LPB (Portugal)',

    # National leagues - Second tier
    'spain-leb-oro': 'LEB Oro (Spain)',
    'spain-leb-gold': 'LEB Oro (Spain)',
    'italy-serie-a2': 'Serie A2 (Italy)',
    'france-betclic-elite-2': 'Pro B (France)',
    'france-pro-b': 'Pro B (France)',
    'france-elite-2': 'Pro B (France)',
    'germany-pro-a': 'ProA (Germany)',
    'greece-a2': 'A2 (Greece)',
    'turkey-tb2l': 'TB2L (Turkey)',
    'japan-b2-league': 'B2.League (Japan)',
    'australia-nbl1': 'NBL1 (Australia)',
    'israel-national-league': 'National League (Israel)',

    # Asia-Pacific other
    'philippines-pba': 'PBA (Philippines)',
    'korea-kbl': 'KBL (Korea)',
    'taiwan-p-league': 'P.League (Taiwan)',
    'new-zealand-nbl': 'NBL (New Zealand)',

    # Americas
    'puerto-rico-bsn': 'BSN (Puerto Rico)',
    'argentina-liga-nacional': 'Liga Nacional (Argentina)',
    'argentina-liga-a': 'Liga Nacional (Argentina)',
    'brazil-nbb': 'NBB (Brazil)',
    'mexico-lnbp': 'LNBP (Mexico)',
    'mexico-liga-sisnova-lnbp': 'LNBP (Mexico)',
    'canada-cebl': 'CEBL (Canada)',

    # North American
    'nba': 'NBA',
    'wnba': 'WNBA',
    'g-league': 'G-League',
    'ncaa': 'NCAA',
}

# Professional leagues (not college/development)
PRO_LEAGUES = {
    # European - Top tier
    'euroleague', 'eurocup', 'basketball-champions-league', 'fiba-europe-cup',
    'spain-liga-endesa', 'italy-lba-serie-a', 'france-betclic-elite',
    'turkey-bsl', 'turkey-tbl', 'germany-easycredit-bbl',
    'greece-heba-a1', 'greece-basket-league', 'super-league-basketball',
    'israel-winner-league', 'russia-vtb-united-league', 'adriatic-aba-league',
    'poland-plk', 'bnxt-league',
    # European - Other top tier
    'finland-korisliiga', 'sweden-basketligan', 'denmark-ligaen',
    'slovenia-liga-nova-kbm', 'hungary-a-league', 'romania-division-a',
    'switzerland-sbl', 'portugal-liga-profissional',
    # European - Second tier
    'spain-leb-oro', 'spain-leb-gold', 'italy-serie-a2',
    'france-pro-b', 'france-elite-2', 'france-betclic-elite-2',
    'germany-pro-a', 'greece-a2', 'turkey-tb2l',
    'uk-bbl', 'netherlands-dbl', 'netherlands-eredivisie',
    'israel-national-league',
    # Asia-Pacific
    'australia-nbl', 'australia-nbl1', 'china-cba', 'japan-b1-league', 'japan-b2-league',
    'philippines-pba', 'korea-kbl', 'taiwan-p-league', 'new-zealand-nbl',
    # Americas
    'nba', 'wnba', 'puerto-rico-bsn',
    'argentina-liga-nacional', 'argentina-liga-a',
    'brazil-nbb', 'mexico-lnbp', 'mexico-liga-sisnova-lnbp', 'canada-cebl',
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
    from .log import warn_once
    if PROBALLERS_CACHE_FILE.exists():
        try:
            with open(PROBALLERS_CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            warn_once(f"Proballers cache corrupted ({PROBALLERS_CACHE_FILE}): {e}", key='proballers_cache_corrupt')
        except (IOError, OSError, PermissionError) as e:
            warn_once(f"Failed to load Proballers cache: {e}", key='proballers_cache_error')
    return {'players': {}, 'rosters': {}}


def _save_cache(cache: Dict[str, Any]) -> None:
    """Save Proballers cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROBALLERS_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def _load_ncaa_teams() -> Dict[str, Dict[str, Any]]:
    """Load NCAA teams cache."""
    from .log import warn_once
    if NCAA_TEAMS_FILE.exists():
        try:
            with open(NCAA_TEAMS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            warn_once(f"NCAA teams cache corrupted ({NCAA_TEAMS_FILE}): {e}", key='ncaa_teams_cache_corrupt')
        except (IOError, OSError, PermissionError) as e:
            warn_once(f"Failed to load NCAA teams cache: {e}", key='ncaa_teams_cache_error')
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

    except (ConnectionError, TimeoutError) as e:
        print(f"  Network error fetching NCAA teams: {e}")
        return {}
    except (AttributeError, ValueError) as e:
        print(f"  Parse error fetching NCAA teams: {e}")
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
    'st-francis-(ny)': 'st-francis-bkn-terriers',
    'st-francis-ny': 'st-francis-bkn-terriers',
    'uconn': 'connecticut-huskies',
    'uconn-huskies': 'connecticut-huskies',
    'california': 'california-golden-bears',
    'san-francisco': 'san-francisco-dons',
    'drexel': 'drexel-dragons',
    'florida-gulf-coast': 'florida-gulf-coast-eagles',
    'notre-dame': 'notre-dame-fighting-irish',
    'unc': 'north-carolina-tar-heels',
    # Additional team slug mappings
    'holy-cross': 'holy-cross-crusaders',
    'northern-arizona': 'northern-arizona-lumberjacks',
    'towson': 'towson-tigers',
    'columbia': 'columbia-lions',
    'george-washington': 'george-washington-colonials',
    'east-carolina': 'east-carolina-pirates',
    'florida-atlantic': 'florida-atlantic-owls',
    'loyola-chicago': 'loyola-il-ramblers',
    'maryland': 'maryland-terrapins',
    'memphis': 'memphis-tigers',
    'morgan-state': 'morgan-state-bears',
    'pittsburgh': 'pittsburgh-panthers',
    'san-diego': 'san-diego-toreros',
    'stetson': 'stetson-hatters',
    'usc': 'usc-trojans',
    'wisconsin': 'wisconsin-badgers',
    'yale': 'yale-bulldogs',
    'youngstown-state': 'youngstown-state-penguins',
    'stanford': 'stanford-cardinal',
    'gonzaga': 'gonzaga-bulldogs',
    'sarah-lawrence': None,  # D3 school - not on Proballers
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

    except (ConnectionError, TimeoutError) as e:
        print(f"Network error fetching player {player_id}: {e}")
        return None
    except (AttributeError, ValueError, KeyError) as e:
        print(f"Parse error for player {player_id}: {e}")
        return None


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

    except (ConnectionError, TimeoutError) as e:
        print(f"Network error fetching roster for {college_slug}: {e}")
        return []
    except (AttributeError, ValueError, KeyError) as e:
        print(f"Parse error for roster {college_slug}: {e}")
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

    # Normalize name for matching - use exact matching only to avoid false positives
    search_name = player_name.lower().strip()

    # Common nickname -> full name mappings (excluding 2-letter initials like DJ, RJ, TJ)
    NICKNAMES = {
        'cam': 'cameron', 'will': 'william', 'bill': 'william', 'billy': 'william',
        'bob': 'robert', 'bobby': 'robert', 'rob': 'robert', 'mike': 'michael',
        'mikey': 'michael', 'matt': 'matthew', 'matty': 'matthew',
        'dan': 'daniel', 'danny': 'daniel', 'dave': 'david', 'davey': 'david',
        'chris': 'christopher', 'tony': 'anthony', 'joe': 'joseph', 'joey': 'joseph',
        'nick': 'nicholas', 'nicky': 'nicholas', 'alex': 'alexander',
        'ben': 'benjamin', 'benny': 'benjamin', 'sam': 'samuel', 'sammy': 'samuel',
        'tom': 'thomas', 'tommy': 'thomas', 'tim': 'timothy', 'timmy': 'timothy',
        'jim': 'james', 'jimmy': 'james', 'jake': 'jacob', 'jack': 'john',
        'ted': 'theodore', 'max': 'maximilian', 'rick': 'richard', 'dick': 'richard',
        'drew': 'andrew', 'andy': 'andrew', 'pete': 'peter', 'steve': 'steven',
        'jon': 'jonathan', 'nate': 'nathan', 'zach': 'zachary', 'zack': 'zachary',
        'ken': 'kenneth', 'greg': 'gregory', 'jeff': 'jeffrey', 'geoff': 'geoffrey',
        'ed': 'edward', 'eddie': 'edward', 'fred': 'frederick', 'frank': 'francis',
        'ray': 'raymond', 'ron': 'ronald', 'donny': 'donald', 'don': 'donald',
        'lenny': 'leonard', 'len': 'leonard', 'larry': 'lawrence', 'jerry': 'gerald',
        'terry': 'terrence', 'barry': 'barrington', 'harry': 'harold',
        'chuck': 'charles', 'charlie': 'charles', 'wes': 'wesley',
        'gus': 'augustus', 'auggie': 'augustus',
    }

    # Helper to normalize name (remove punctuation, standardize spacing)
    def normalize(name):
        # Decode HTML entities (&#039; -> ', etc.)
        import html
        name = html.unescape(name)
        # Remove apostrophes, periods, commas, hyphens within names
        normalized = name.replace("'", "").replace(".", "").replace(",", "").replace("-", " ")
        # Collapse multiple spaces
        return ' '.join(normalized.split())

    # Helper to expand nicknames in a name
    def expand_nicknames(name):
        parts = name.split()
        expanded = []
        for part in parts:
            if part in NICKNAMES:
                expanded.append(NICKNAMES[part])
            else:
                expanded.append(part)
        return ' '.join(expanded)

    # Collect all candidates that match by name
    candidates = []
    for player in roster:
        roster_name = player['name'].lower()

        # Exact match
        if search_name == roster_name:
            candidates.append(player)
            continue

        # Normalized match (handles De'Andre vs DeAndre, etc.)
        if normalize(search_name) == normalize(roster_name):
            candidates.append(player)
            continue

        # Nickname-expanded match (handles Cam vs Cameron, DJ vs Dennis, etc.)
        search_expanded = expand_nicknames(normalize(search_name))
        roster_expanded = expand_nicknames(normalize(roster_name))
        if search_expanded == roster_expanded:
            candidates.append(player)
            continue

        # Check slug (Proballers slug format)
        search_slug = normalize(search_name).replace(' ', '-')
        if search_slug == player['slug']:
            candidates.append(player)
            continue

        # Match without suffixes (Jr/Sr/II/III) for cases like "John Smith Jr" vs "John Smith"
        suffixes = {'jr', 'sr', 'ii', 'iii', 'iv', 'v'}
        search_base = ' '.join(p for p in normalize(search_name).split() if p not in suffixes)
        roster_base = ' '.join(p for p in normalize(roster_name).split() if p not in suffixes)
        if search_base == roster_base:
            candidates.append(player)
            continue

        # Nickname + suffix removal combined
        search_base_expanded = ' '.join(p for p in search_expanded.split() if p not in suffixes)
        roster_base_expanded = ' '.join(p for p in roster_expanded.split() if p not in suffixes)
        if search_base_expanded == roster_base_expanded:
            candidates.append(player)

    if not candidates:
        return None

    # Helper to verify candidate played for the college in the expected year
    def verify_candidate(candidate_id: int, expected_year: Optional[int]) -> bool:
        career = get_player_career(candidate_id, scraper)
        if not career:
            return False

        # Check their college history
        for team in career.get('teams', []):
            league = team.get('league', '').lower()
            if 'ncaa' not in league:
                continue

            # If no year specified, any NCAA stint is fine
            if not expected_year:
                return True

            # Verify year matches (allow 1 year tolerance for season overlap)
            team_year = team.get('year', 0)
            if abs(team_year - expected_year) <= 1:
                return True

        # No matching college stint found
        return False

    # Validate ALL candidates - must have played for college in expected year
    verified_candidates = []
    for candidate in candidates:
        if verify_candidate(candidate['id'], year):
            verified_candidates.append(candidate)

    if not verified_candidates:
        return None

    if len(verified_candidates) == 1:
        return verified_candidates[0]['id']

    # Multiple verified candidates - return first (same name, same school, same year = likely same person)
    return verified_candidates[0]['id']


def get_player_pro_leagues(player_id: int, scraper=None, force_refresh: bool = False) -> List[str]:
    """
    Get list of professional leagues a player has played in.

    Args:
        player_id: Proballers player ID
        scraper: Optional cloudscraper instance
        force_refresh: If True, ignore cache and fetch fresh data

    Returns:
        List of league display names
    """
    career = get_player_career(player_id, scraper, force_refresh=force_refresh)
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
