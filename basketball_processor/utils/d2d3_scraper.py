"""
Scraper for D2 and D3 conference and school data from RealGM.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Any

import cloudscraper
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).parent.parent.parent / 'data'
DATA_DIR.mkdir(parents=True, exist_ok=True)

D2_DATA_FILE = DATA_DIR / "d2_conferences.json"
D3_DATA_FILE = DATA_DIR / "d3_conferences.json"
D2D3_REFRESH_TIMESTAMP_FILE = DATA_DIR / "d2d3_refresh_timestamp.txt"
REALGM_PLAYER_CACHE_FILE = DATA_DIR / "realgm_player_cache.json"
REALGM_TRANSFER_CACHE_FILE = DATA_DIR / "realgm_transfers.json"

RATE_LIMIT_DELAY = 1.5  # seconds between requests
REFRESH_INTERVAL_DAYS = 90  # Re-scrape every 90 days during season


def _get_current_season() -> str:
    """Get the current basketball season string (e.g., '2025-26')."""
    from datetime import datetime
    now = datetime.now()
    year = now.year
    month = now.month

    # Basketball season: Nov-Mar spans two calendar years
    if month >= 11:  # Nov-Dec: season starts
        return f"{year}-{str(year + 1)[-2:]}"
    elif month <= 4:  # Jan-Apr: same season as previous fall
        return f"{year - 1}-{str(year)[-2:]}"
    else:  # May-Oct: off-season, use upcoming season
        return f"{year}-{str(year + 1)[-2:]}"


def _get_last_refresh_time() -> float:
    """Get timestamp of last D2/D3 refresh."""
    if D2D3_REFRESH_TIMESTAMP_FILE.exists():
        try:
            return float(D2D3_REFRESH_TIMESTAMP_FILE.read_text().strip())
        except (ValueError, OSError):
            pass
    return 0


def _save_refresh_timestamp() -> None:
    """Save current time as last refresh timestamp."""
    import time as time_module
    D2D3_REFRESH_TIMESTAMP_FILE.write_text(str(time_module.time()))


def should_refresh_d2d3() -> bool:
    """
    Check if D2/D3 data should be refreshed.

    Refreshes once at the start of each season (Oct-Nov) since
    conference realignment happens between seasons, not during.
    """
    from datetime import datetime

    # Only auto-refresh at season start (Oct-Nov)
    month = datetime.now().month
    if month not in [10, 11]:
        return False

    # Check if we already have data for the current season
    d3_data = load_d3_data()
    current_season = _get_current_season()

    # If D3 data has a season field and matches current, no refresh needed
    if d3_data.get('season') == current_season:
        return False

    return True


def _get_scraper():
    """Create a cloudscraper instance."""
    return cloudscraper.create_scraper()


def _get_conferences(scraper, division: str) -> Dict[str, int]:
    """
    Get all conferences for a division.

    Args:
        scraper: cloudscraper instance
        division: 'ncaa-dii' or 'ncaa-diii'

    Returns:
        Dict mapping conference name (slug) to conference ID
    """
    url = f"https://basketball.realgm.com/{division}/conferences"
    resp = scraper.get(url)

    if resp.status_code != 200:
        print(f"Failed to fetch conferences: {resp.status_code}")
        return {}

    # Find conference links: /ncaa-dii/conferences/Conference-Name/123
    pattern = rf'/{division}/conferences/([^/\"]+)/(\d+)'
    matches = re.findall(pattern, resp.text)

    conferences = {}
    for name, conf_id in matches:
        if name not in conferences:
            conferences[name] = int(conf_id)

    return conferences


def _get_conference_schools(scraper, division: str, conf_slug: str, conf_id: int) -> List[Dict[str, Any]]:
    """
    Get all schools in a conference.

    Args:
        scraper: cloudscraper instance
        division: 'ncaa-dii' or 'ncaa-diii'
        conf_slug: Conference URL slug
        conf_id: Conference ID

    Returns:
        List of school dicts with name, slug, and id
    """
    url = f"https://basketball.realgm.com/{division}/conferences/{conf_slug}/{conf_id}/teams"
    resp = scraper.get(url)

    if resp.status_code != 200:
        print(f"  Failed to fetch {conf_slug}: {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table', class_='table')

    if not table:
        return []

    schools = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue

        link = cells[0].find('a')
        if link:
            school_name = link.get_text(strip=True)
            href = link.get('href', '')
            # Extract school slug and ID from href
            # Format: /ncaa-dii/conferences/Conf-Name/123/School-Name/456/rosters
            match = re.search(rf'/{division}/conferences/[^/]+/\d+/([^/]+)/(\d+)', href)
            if match:
                schools.append({
                    'name': school_name,
                    'slug': match.group(1),
                    'id': int(match.group(2))
                })

    return schools


def scrape_division(division: str, season: str = None) -> Dict[str, Any]:
    """
    Scrape all conferences and schools for a division.

    Args:
        division: 'ncaa-dii' or 'ncaa-diii'
        season: Season string (e.g., '2025-26')

    Returns:
        Dict with conferences, schools, and metadata
    """
    if season is None:
        season = _get_current_season()

    scraper = _get_scraper()

    print(f"Fetching {division.upper()} conferences for {season}...")
    conferences = _get_conferences(scraper, division)
    print(f"Found {len(conferences)} conferences")

    all_data = {
        'division': division,
        'season': season,
        'source': 'realgm.com',
        'conferences': {},
        'total_schools': 0
    }

    for i, (conf_slug, conf_id) in enumerate(sorted(conferences.items()), 1):
        conf_name = conf_slug.replace('-', ' ')
        print(f"  [{i}/{len(conferences)}] {conf_name}...")

        time.sleep(RATE_LIMIT_DELAY)
        schools = _get_conference_schools(scraper, division, conf_slug, conf_id)

        all_data['conferences'][conf_name] = {
            'id': conf_id,
            'slug': conf_slug,
            'schools': schools
        }
        all_data['total_schools'] += len(schools)
        print(f"    {len(schools)} schools")

    return all_data


def scrape_d2() -> Dict[str, Any]:
    """Scrape all D2 conferences and schools."""
    data = scrape_division('ncaa-dii')

    # Save to file
    with open(D2_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved to {D2_DATA_FILE}")

    return data


def _get_d3hoops_conferences(scraper) -> List[str]:
    """Get all D3 conference codes from d3hoops.com."""
    url = "https://www.d3hoops.com/conferences"
    resp = scraper.get(url)

    if resp.status_code != 200:
        print(f"Failed to fetch d3hoops conferences: {resp.status_code}")
        return []

    # Find conference codes like /conf/AMCC
    conf_codes = re.findall(r'/conf/([A-Z0-9]+)(?:/|\")', resp.text)
    return sorted(set(conf_codes))


def _get_d3hoops_conference_schools(scraper, conf_code: str, season: str = None) -> List[Dict[str, Any]]:
    """Get all schools in a D3 conference from d3hoops.com standings."""
    if season is None:
        season = _get_current_season()
    url = f"https://www.d3hoops.com/conf/{conf_code}/men/{season}/standings"
    resp = scraper.get(url)

    if resp.status_code != 200:
        print(f"  Failed to fetch {conf_code}: {resp.status_code}")
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table')

    if not table:
        return []

    schools = []
    for row in table.find_all('tr'):
        cells = row.find_all('td')
        if not cells:
            continue

        school_name = cells[0].get_text(strip=True)
        if school_name and school_name not in ['', 'W-L', 'Win %']:
            schools.append({
                'name': school_name,
                'slug': school_name.lower().replace(' ', '-'),
                'id': None  # d3hoops uses teamId params, not numeric IDs
            })

    return schools


# Map conference codes to full names
D3_CONF_NAMES = {
    'AEC': 'American East Conference',
    'AMCC': 'Allegheny Mountain Collegiate Conference',
    'ARC': 'American Rivers Conference',
    'ASC': 'American Southwest Conference',
    'C2C': 'Coast-to-Coast Athletic Conference',
    'CC': 'Centennial Conference',
    'CCIW': 'College Conference of Illinois and Wisconsin',
    'CCS': 'Colonial Coast South',
    'CNE': 'Commonwealth Coast Conference',
    'CUNYAC': 'City University of New York Athletic Conference',
    'E8': 'Empire 8',
    'GNAC': 'Great Northeast Athletic Conference',
    'HCAC': 'Heartland Collegiate Athletic Conference',
    'IND': 'Independent',
    'LAND': 'Landmark Conference',
    'LEC': 'Little East Conference',
    'LL': 'Liberty League',
    'MACC': 'Middle Atlantic Conference Commonwealth',
    'MACF': 'Middle Atlantic Conference Freedom',
    'MASCAC': 'Massachusetts State Collegiate Athletic Conference',
    'MIAA': 'Michigan Intercollegiate Athletic Association',
    'MIAC': 'Minnesota Intercollegiate Athletic Conference',
    'MWC': 'Midwest Conference',
    'NAC': 'North Atlantic Conference',
    'NACC': 'Northern Athletics Collegiate Conference',
    'NCAC': 'North Coast Athletic Conference',
    'NESCAC': 'New England Small College Athletic Conference',
    'NEWMAC': 'New England Women\'s and Men\'s Athletic Conference',
    'NJAC': 'New Jersey Athletic Conference',
    'NWC': 'Northwest Conference',
    'OAC': 'Ohio Athletic Conference',
    'ODAC': 'Old Dominion Athletic Conference',
    'PAC': 'Presidents\' Athletic Conference',
    'SAA': 'Southern Athletic Association',
    'SCAC': 'Southern Collegiate Athletic Conference',
    'SCIAC': 'Southern California Intercollegiate Athletic Conference',
    'SKY': 'Skyline Conference',
    'SLIAC': 'St. Louis Intercollegiate Athletic Conference',
    'SUNYAC': 'State University of New York Athletic Conference',
    'UAA': 'University Athletic Association',
    'UEC': 'USA East Conference',
    'UMAC': 'Upper Midwest Athletic Conference',
    'USAC': 'USA South Athletic Conference',
    'WIAC': 'Wisconsin Intercollegiate Athletic Conference',
}


def scrape_d3_from_d3hoops(season: str = None) -> Dict[str, Any]:
    """Scrape all D3 conferences and schools from d3hoops.com."""
    if season is None:
        season = _get_current_season()

    scraper = _get_scraper()

    print(f"Fetching D3 conferences from d3hoops.com for {season}...")
    conf_codes = _get_d3hoops_conferences(scraper)
    print(f"Found {len(conf_codes)} conferences")

    all_data = {
        'division': 'D3',
        'source': 'd3hoops.com',
        'season': season,
        'conferences': {},
        'total_schools': 0
    }

    for i, conf_code in enumerate(conf_codes, 1):
        conf_name = D3_CONF_NAMES.get(conf_code, conf_code)
        print(f"  [{i}/{len(conf_codes)}] {conf_name} ({conf_code})...")

        time.sleep(RATE_LIMIT_DELAY)
        schools = _get_d3hoops_conference_schools(scraper, conf_code, season)

        all_data['conferences'][conf_name] = {
            'code': conf_code,
            'slug': conf_code,
            'schools': schools
        }
        all_data['total_schools'] += len(schools)
        print(f"    {len(schools)} schools")

    return all_data


def scrape_d3(season: str = None) -> Dict[str, Any]:
    """Scrape all D3 conferences and schools from d3hoops.com."""
    data = scrape_d3_from_d3hoops(season)

    # Save to file - use season-specific filename for historical data
    if season and season != _get_current_season():
        output_file = DATA_DIR / f"d3_conferences_{season.replace('-', '_')}.json"
    else:
        output_file = D3_DATA_FILE

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved to {output_file}")

    return data


def scrape_historical_seasons(seasons: List[str]) -> None:
    """
    Scrape D3 conference data for historical seasons.

    Args:
        seasons: List of seasons to scrape (e.g., ['2011-12', '2012-13'])
    """
    for season in seasons:
        print(f"\n{'='*50}")
        print(f"Scraping D3 data for {season}...")
        print('='*50)
        scrape_d3(season)


def get_seasons_from_games() -> List[str]:
    """
    Get unique seasons from D2/D3 games in cache.

    Returns list of seasons that need conference data.
    """
    from .constants import CACHE_DIR

    seasons = set()
    skip_files = {'nba_lookup_cache.json', 'nba_api_cache.json', 'schedule_cache.json', 'proballers_cache.json'}

    for file in CACHE_DIR.glob("*.json"):
        if file.name in skip_files:
            continue
        try:
            with open(file, 'r') as f:
                game = json.load(f)
            bi = game.get('basic_info', {})
            div = bi.get('division', 'D1')
            if div in ['D2', 'D3']:
                date_str = bi.get('date_yyyymmdd', '')
                if len(date_str) == 8:
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                    # Basketball season: Nov-Mar spans two calendar years
                    if month >= 11:
                        season = f"{year}-{str(year + 1)[-2:]}"
                    else:
                        season = f"{year - 1}-{str(year)[-2:]}"
                    seasons.add(season)
        except (json.JSONDecodeError, KeyError):
            continue

    return sorted(seasons)


def load_d2_data() -> Dict[str, Any]:
    """Load D2 data from file."""
    if D2_DATA_FILE.exists():
        with open(D2_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def load_d3_data() -> Dict[str, Any]:
    """Load D3 data from file."""
    if D3_DATA_FILE.exists():
        with open(D3_DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


# Common name aliases for lookup
SCHOOL_NAME_ALIASES = {
    'university of chicago': 'chicago',
    'uchicago': 'chicago',
    'johns hopkins university': 'johns hopkins',
    'jhu': 'johns hopkins',
    'brandeis university': 'brandeis',
    'case western': 'case western reserve',
    'carnegie mellon university': 'carnegie mellon',
    'cmu': 'carnegie mellon',
    'nyu': 'new york university',
    'wash u': 'washington u.',
    'wustl': 'washington u.',
}

# Manual conference overrides for schools missing from scraped data
MANUAL_CONFERENCE_OVERRIDES = {
    'sarah lawrence': 'Skyline Conference',
    'sarah lawrence college': 'Skyline Conference',
    'academy of art': 'Pacific West Conference',
    'academy of art university': 'Pacific West Conference',
    'jessup': 'Pacific West Conference',
    'william jessup': 'Pacific West Conference',
}


def get_school_conference(school_name: str, division: str = None) -> str:
    """
    Look up what conference a school belongs to.

    Args:
        school_name: School name to look up
        division: 'D2' or 'D3', or None to search both

    Returns:
        Conference name or empty string if not found
    """
    school_lower = school_name.lower().strip()

    # Check manual overrides first
    if school_lower in MANUAL_CONFERENCE_OVERRIDES:
        return MANUAL_CONFERENCE_OVERRIDES[school_lower]

    # Check aliases
    normalized = SCHOOL_NAME_ALIASES.get(school_lower, school_lower)

    def search_data(data: Dict) -> str:
        for conf_name, conf_data in data.get('conferences', {}).items():
            for school in conf_data.get('schools', []):
                school_name_lower = school['name'].lower()
                # Exact match only - partial matching causes false positives
                if school_name_lower == normalized:
                    return conf_name
                # Also check slug for exact match
                slug_lower = school['slug'].lower().replace('-', ' ')
                if slug_lower == normalized:
                    return conf_name
        return ''

    if division in ('D2', None):
        d2_data = load_d2_data()
        result = search_data(d2_data)
        if result:
            return result

    if division in ('D3', None):
        d3_data = load_d3_data()
        result = search_data(d3_data)
        if result:
            return result

    return ''


def refresh_if_needed() -> bool:
    """Refresh D2/D3 data if it's for an old season. Returns True if refreshed."""
    if not should_refresh_d2d3():
        d2_data = load_d2_data()
        d3_data = load_d3_data()
        d2_season = d2_data.get('season', 'unknown')
        d3_season = d3_data.get('season', 'unknown')
        print(f"D2/D3 data: D2={d2_season}, D3={d3_season} (current season)")
        return False

    current_season = _get_current_season()
    print(f"Refreshing D2/D3 data for {current_season} season...")
    scrape_d2()
    scrape_d3()
    _save_refresh_timestamp()
    return True


def detect_conference_changes() -> Dict[str, Any]:
    """
    Compare current data with fresh scrape to detect conference changes.

    Returns dict with:
        - new_schools: schools that joined conferences
        - departed_schools: schools that left conferences
        - new_conferences: newly created conferences
        - disbanded_conferences: conferences that no longer exist
    """
    # Load existing data
    old_d2 = load_d2_data()
    old_d3 = load_d3_data()

    # Get fresh data
    print("Fetching fresh D2/D3 data to check for changes...")
    new_d2 = scrape_d2()
    new_d3 = scrape_d3()

    changes = {
        'D2': _compare_division_data(old_d2, new_d2),
        'D3': _compare_division_data(old_d3, new_d3)
    }

    _save_refresh_timestamp()
    return changes


def _compare_division_data(old_data: Dict, new_data: Dict) -> Dict[str, Any]:
    """Compare old and new division data to find changes."""
    changes = {
        'new_conferences': [],
        'disbanded_conferences': [],
        'school_moves': []
    }

    old_confs = set(old_data.get('conferences', {}).keys())
    new_confs = set(new_data.get('conferences', {}).keys())

    changes['new_conferences'] = list(new_confs - old_confs)
    changes['disbanded_conferences'] = list(old_confs - new_confs)

    # Build school -> conference mappings
    old_school_conf = {}
    for conf_name, conf_data in old_data.get('conferences', {}).items():
        for school in conf_data.get('schools', []):
            old_school_conf[school['name']] = conf_name

    new_school_conf = {}
    for conf_name, conf_data in new_data.get('conferences', {}).items():
        for school in conf_data.get('schools', []):
            new_school_conf[school['name']] = conf_name

    # Find schools that changed conferences
    for school, new_conf in new_school_conf.items():
        old_conf = old_school_conf.get(school)
        if old_conf and old_conf != new_conf:
            changes['school_moves'].append({
                'school': school,
                'from': old_conf,
                'to': new_conf
            })

    return changes


# ==================== PLAYER SCRAPING ====================

def _load_transfer_cache() -> Dict[str, Any]:
    """Load transfer portal cache."""
    if REALGM_TRANSFER_CACHE_FILE.exists():
        try:
            with open(REALGM_TRANSFER_CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {'players': {}, 'last_updated': None}


def _save_transfer_cache(cache: Dict[str, Any]) -> None:
    """Save transfer portal cache."""
    with open(REALGM_TRANSFER_CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)


def scrape_transfer_portal() -> Dict[str, Any]:
    """
    Scrape the RealGM transfer portal for all transfers.

    Returns:
        Dict mapping normalized player names to their transfer history
    """
    scraper = _get_scraper()
    url = 'https://basketball.realgm.com/ncaa/info/transfers'

    print("Fetching transfer portal data...")
    resp = scraper.get(url)
    if resp.status_code != 200:
        print(f"Failed to fetch transfer portal: {resp.status_code}")
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')
    table = soup.find('table')

    if not table:
        print("No transfer table found")
        return {}

    players = {}
    rows = table.find_all('tr')[1:]  # Skip header

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        # Extract player info
        player_link = cells[0].find('a')
        if not player_link:
            continue

        player_name = player_link.get_text(strip=True)
        href = player_link.get('href', '')

        # Extract RealGM player ID from href: /player/Name/NCAA/123456
        player_id = None
        id_match = re.search(r'/player/[^/]+/[^/]+/(\d+)', href)
        if id_match:
            player_id = id_match.group(1)

        trans_from = cells[1].get_text(strip=True)
        trans_to = cells[2].get_text(strip=True)
        position = cells[3].get_text(strip=True) if len(cells) > 3 else ''
        height = cells[4].get_text(strip=True) if len(cells) > 4 else ''
        year_class = cells[6].get_text(strip=True) if len(cells) > 6 else ''

        # Normalize name for lookup
        name_key = player_name.lower().strip()

        if name_key not in players:
            players[name_key] = {
                'name': player_name,
                'realgm_id': player_id,
                'schools': [],
                'position': position,
                'height': height,
            }

        # Add transfer info
        players[name_key]['schools'].append({
            'from': trans_from,
            'to': trans_to,
            'class': year_class,
        })

    print(f"Found {len(players)} players with transfers")

    cache = {
        'players': players,
        'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_transfers': len(rows),
    }
    _save_transfer_cache(cache)

    return cache


def get_realgm_player_url(player_name: str, realgm_id: str = None) -> str:
    """
    Get the RealGM URL for a player.

    Args:
        player_name: Player name
        realgm_id: Optional RealGM player ID

    Returns:
        RealGM player URL or empty string if not found
    """
    if realgm_id:
        name_slug = player_name.replace(' ', '-').replace('.', '').replace("'", '')
        return f"https://basketball.realgm.com/player/{name_slug}/Summary/{realgm_id}"

    # Try to find in cache
    cache = _load_transfer_cache()
    name_key = player_name.lower().strip()

    if name_key in cache.get('players', {}):
        player_data = cache['players'][name_key]
        if player_data.get('realgm_id'):
            name_slug = player_name.replace(' ', '-').replace('.', '').replace("'", '')
            return f"https://basketball.realgm.com/player/{name_slug}/Summary/{player_data['realgm_id']}"

    return ''


def lookup_player_transfers(player_name: str) -> Dict[str, Any]:
    """
    Look up a player's transfer history from cache.

    Args:
        player_name: Player name to look up

    Returns:
        Dict with player info and transfer history, or empty dict if not found
    """
    cache = _load_transfer_cache()
    name_key = player_name.lower().strip()

    if name_key in cache.get('players', {}):
        return cache['players'][name_key]

    # Try partial matching
    for key, data in cache.get('players', {}).items():
        if name_key in key or key in name_key:
            return data

    return {}


def get_player_school_history(player_name: str) -> List[str]:
    """
    Get list of schools a player has attended.

    Args:
        player_name: Player name

    Returns:
        List of school names
    """
    player_data = lookup_player_transfers(player_name)
    if not player_data:
        return []

    schools = set()
    for transfer in player_data.get('schools', []):
        if transfer.get('from'):
            schools.add(transfer['from'])
        if transfer.get('to'):
            schools.add(transfer['to'])

    return sorted(schools)


def search_realgm_player(player_name: str, school: str = None) -> Dict[str, Any]:
    """
    Search for a player on RealGM by scraping search results.

    Args:
        player_name: Player name to search
        school: Optional school name to narrow results

    Returns:
        Dict with player info if found
    """
    # Check cache first
    cached = lookup_player_transfers(player_name)
    if cached:
        return cached

    # Scrape search
    scraper = _get_scraper()
    search_name = player_name.replace(' ', '+')
    url = f'https://basketball.realgm.com/search?q={search_name}'

    time.sleep(RATE_LIMIT_DELAY)
    resp = scraper.get(url)

    if resp.status_code != 200:
        return {}

    soup = BeautifulSoup(resp.text, 'html.parser')

    # Look for player links in results
    player_links = soup.find_all('a', href=re.compile(r'/player/[^/]+/[^/]+/\d+'))

    for link in player_links:
        link_text = link.get_text(strip=True)
        href = link.get('href', '')

        # Check if name matches
        if player_name.lower() in link_text.lower():
            # Extract ID
            id_match = re.search(r'/player/[^/]+/[^/]+/(\d+)', href)
            if id_match:
                return {
                    'name': link_text,
                    'realgm_id': id_match.group(1),
                    'realgm_url': f"https://basketball.realgm.com{href}",
                }

    return {}


def enrich_player_with_realgm(player_name: str, current_school: str = None, search_if_not_cached: bool = False) -> Dict[str, Any]:
    """
    Enrich player data with RealGM information.

    Args:
        player_name: Player name
        current_school: Current school (optional)
        search_if_not_cached: If True, search RealGM if player not in cache (slow, rate-limited).
                              Default False for batch processing.

    Returns:
        Dict with enriched player data including:
        - realgm_url: URL to player's RealGM page
        - schools: List of schools attended
        - has_transfer_history: Whether player has transferred
    """
    result = {
        'realgm_url': '',
        'schools': [],
        'has_transfer_history': False,
    }

    # Check transfer cache (no network request)
    player_data = lookup_player_transfers(player_name)

    if player_data:
        result['realgm_url'] = get_realgm_player_url(player_name, player_data.get('realgm_id'))
        result['schools'] = get_player_school_history(player_name)
        result['has_transfer_history'] = len(result['schools']) > 1
        return result

    # Only search RealGM if explicitly requested (makes network request)
    if search_if_not_cached:
        search_result = search_realgm_player(player_name, current_school)
        if search_result:
            result['realgm_url'] = search_result.get('realgm_url', '')

    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Scrape D2/D3 conference data')
    parser.add_argument('--d2', action='store_true', help='Scrape D2 data')
    parser.add_argument('--d3', action='store_true', help='Scrape D3 data')
    parser.add_argument('--all', action='store_true', help='Scrape both D2 and D3')
    parser.add_argument('--season', type=str, help='Season to scrape (e.g., 2025-26)')
    parser.add_argument('--check-changes', action='store_true', help='Check for conference changes')
    parser.add_argument('--refresh', action='store_true', help='Refresh if data is stale')
    parser.add_argument('--from-games', action='store_true', help='Scrape historical seasons based on D2/D3 games in cache')
    parser.add_argument('--transfers', action='store_true', help='Scrape transfer portal data')
    parser.add_argument('--lookup', type=str, help='Look up a player by name')

    args = parser.parse_args()

    if args.transfers:
        cache = scrape_transfer_portal()
        if cache:
            print(f"\nTransfer portal: {len(cache.get('players', {}))} unique players")
            print(f"Total transfers: {cache.get('total_transfers', 0)}")
            print(f"Saved to {REALGM_TRANSFER_CACHE_FILE}")
        exit(0)

    if args.lookup:
        player_data = enrich_player_with_realgm(args.lookup)
        if player_data.get('realgm_url') or player_data.get('schools'):
            print(f"Player: {args.lookup}")
            if player_data.get('realgm_url'):
                print(f"RealGM URL: {player_data['realgm_url']}")
            if player_data.get('schools'):
                print(f"Schools: {', '.join(player_data['schools'])}")
            if player_data.get('has_transfer_history'):
                print("Has transfer history: Yes")
        else:
            print(f"Player '{args.lookup}' not found in transfer cache")
            print("Try running --transfers first to refresh the cache")
        exit(0)

    if args.refresh:
        refreshed = refresh_if_needed()
        if not refreshed:
            print("Data is current, no refresh needed")
        exit(0)

    if args.from_games:
        seasons = get_seasons_from_games()
        if seasons:
            print(f"Found D2/D3 games from seasons: {', '.join(seasons)}")
            scrape_historical_seasons(seasons)
        else:
            print("No D2/D3 games found in cache")
        exit(0)

    if args.check_changes:
        changes = detect_conference_changes()
        for div, div_changes in changes.items():
            print(f"\n{div} Changes:")
            if div_changes['new_conferences']:
                print(f"  New conferences: {div_changes['new_conferences']}")
            if div_changes['disbanded_conferences']:
                print(f"  Disbanded: {div_changes['disbanded_conferences']}")
            if div_changes['school_moves']:
                print(f"  School moves:")
                for move in div_changes['school_moves']:
                    print(f"    {move['school']}: {move['from']} -> {move['to']}")
            if not any([div_changes['new_conferences'], div_changes['disbanded_conferences'], div_changes['school_moves']]):
                print("  No changes detected")
        exit(0)

    if args.all or (not args.d2 and not args.d3):
        args.d2 = True
        args.d3 = True

    season = args.season or _get_current_season()

    if args.d2:
        print("=" * 50)
        print(f"Scraping D2 data...")
        print("=" * 50)
        d2 = scrape_d2()
        print(f"\nD2: {len(d2['conferences'])} conferences, {d2['total_schools']} schools")

    if args.d3:
        print("\n" + "=" * 50)
        print(f"Scraping D3 data for {season}...")
        print("=" * 50)
        d3 = scrape_d3(season)
        print(f"\nD3: {len(d3['conferences'])} conferences, {d3['total_schools']} schools")

    _save_refresh_timestamp()
