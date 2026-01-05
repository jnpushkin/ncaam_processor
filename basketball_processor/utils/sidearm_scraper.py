"""
SIDEARM athletic website scraper to supplement Sports Reference data.

Fetches box scores from team athletic websites to get:
- Attendance
- Officials
- Other data not available in Sports Reference

Also supports WMT Sports sites (Stanford, Virginia, Virginia Tech, Nebraska)
as a fallback for schools that use Nuxt.js instead of SIDEARM.
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Import WMT scraper for Nuxt.js sites
from .wmt_scraper import (
    is_wmt_site,
    supplement_game_data as wmt_supplement_game_data,
    PLAYWRIGHT_AVAILABLE as WMT_PLAYWRIGHT_AVAILABLE
)

# Import ESPN scraper as fallback
from .espn_scraper import get_espn_attendance

# Rate limiting
RATE_LIMIT_DELAY = 1.5  # seconds between requests

# Cache directory
BASE_DIR = Path(__file__).parent.parent.parent
CACHE_DIR = BASE_DIR / 'cache'
DATA_DIR = BASE_DIR / 'data'

# Athletic website domains for D1 schools
# Format: school_name -> (domain, sidearm_format)
# sidearm_format: 'new' = /sports/.../boxscore/ID, 'old' = /boxscore.aspx?id=ID
ATHLETIC_SITES: Dict[str, Tuple[str, str]] = {
    # WCC
    'San Francisco': ('usfdons.com', 'new'),
    "Saint Mary's": ('smcgaels.com', 'new'),
    "Saint Mary's (CA)": ('smcgaels.com', 'new'),
    'Gonzaga': ('gozags.com', 'new'),
    'Santa Clara': ('santaclarabroncos.com', 'new'),
    'San Diego': ('usdtoreros.com', 'new'),
    'Pacific': ('pacifictigers.com', 'new'),
    'Pepperdine': ('pepperdinewaves.com', 'new'),
    'Portland': ('portlandpilots.com', 'new'),
    'Loyola Marymount': ('lmulions.com', 'new'),

    # Pac-12 / Big Ten (realignment)
    'Stanford': ('gostanford.com', 'new'),
    'California': ('calbears.com', 'new'),
    'Cal': ('calbears.com', 'new'),
    'USC': ('usctrojans.com', 'new'),
    'UCLA': ('uclabruins.com', 'new'),
    'Oregon': ('goducks.com', 'new'),
    'Oregon State': ('osubeavers.com', 'new'),
    'Washington': ('gohuskies.com', 'new'),
    'Washington State': ('wsucougars.com', 'new'),
    'Arizona': ('arizonawildcats.com', 'new'),
    'Arizona State': ('thesundevils.com', 'new'),
    'Colorado': ('cubuffs.com', 'new'),
    'Utah': ('utahutes.com', 'new'),

    # Mountain West
    'San Jose State': ('sjsuspartans.com', 'new'),
    'Fresno State': ('gobulldogs.com', 'new'),
    'San Diego State': ('goaztecs.com', 'new'),
    'UNLV': ('unlvrebels.com', 'new'),
    'Nevada': ('nevadawolfpack.com', 'new'),
    'Boise State': ('broncosports.com', 'new'),
    'Air Force': ('goairforcefalcons.com', 'new'),
    'Wyoming': ('gowyo.com', 'new'),
    'Colorado State': ('csurams.com', 'new'),
    'New Mexico': ('golobos.com', 'new'),
    'Utah State': ('utahstateaggies.com', 'new'),

    # Big West
    'UC Davis': ('ucdavisaggies.com', 'new'),
    'UC Santa Barbara': ('ucsbgauchos.com', 'new'),
    'UC Irvine': ('ucirvinesports.com', 'new'),
    'UC Riverside': ('gohighlanders.com', 'new'),
    'Cal State Fullerton': ('fullertontitans.com', 'new'),
    'Long Beach State': ('longbeachstate.com', 'new'),
    'Cal Poly': ('gopoly.com', 'new'),
    'Hawaii': ('hawaiiathletics.com', 'new'),
    'Cal State Northridge': ('gomatadors.com', 'new'),
    'Cal State Bakersfield': ('gorunners.com', 'new'),

    # WAC
    'Grand Canyon': ('gculopes.com', 'new'),
    'California Baptist': ('cbulancers.com', 'new'),
    'Seattle': ('goseattleu.com', 'new'),
    'Utah Valley': ('gouvu.com', 'new'),
    'UTRGV': ('goutrgv.com', 'new'),
    'Abilene Christian': ('acusports.com', 'new'),
    'Tarleton State': ('tarletonsports.com', 'new'),
    'Southern Utah': ('suutbirds.com', 'new'),

    # Big Ten
    'Maryland': ('umterps.com', 'new'),
    'Northwestern': ('nusports.com', 'new'),
    'Michigan': ('mgoblue.com', 'new'),
    'Michigan State': ('msuspartans.com', 'new'),
    'Ohio State': ('ohiostatebuckeyes.com', 'new'),
    'Penn State': ('gopsusports.com', 'new'),
    'Indiana': ('iuhoosiers.com', 'new'),
    'Purdue': ('purduesports.com', 'new'),
    'Illinois': ('fightingillini.com', 'new'),
    'Iowa': ('hawkeyesports.com', 'new'),
    'Minnesota': ('gophersports.com', 'new'),
    'Wisconsin': ('uwbadgers.com', 'new'),
    'Nebraska': ('huskers.com', 'new'),
    'Rutgers': ('scarletknights.com', 'new'),

    # Big East
    'UConn': ('uconnhuskies.com', 'new'),
    'Connecticut': ('uconnhuskies.com', 'new'),
    'Villanova': ('villanova.com', 'new'),
    'Creighton': ('gocreighton.com', 'new'),
    'Marquette': ('gomarquette.com', 'new'),
    'Xavier': ('goxavier.com', 'new'),
    'Providence': ('friars.com', 'new'),
    'Butler': ('butlersports.com', 'new'),
    'Seton Hall': ('shupirates.com', 'new'),
    "St. John's": ('redstormsports.com', 'new'),
    'DePaul': ('depaulbluedemons.com', 'new'),
    'Georgetown': ('guhoyas.com', 'new'),

    # ACC
    'Duke': ('goduke.com', 'new'),
    'North Carolina': ('goheels.com', 'new'),
    'NC State': ('gopack.com', 'new'),
    'Wake Forest': ('godeacs.com', 'new'),
    'Louisville': ('gocards.com', 'new'),
    'Syracuse': ('cuse.com', 'new'),
    'Clemson': ('clemsontigers.com', 'new'),
    'Boston College': ('bceagles.com', 'new'),
    'Miami': ('miamihurricanes.com', 'new'),
    'Florida State': ('seminoles.com', 'new'),
    'Georgia Tech': ('ramblinwreck.com', 'new'),
    'Pittsburgh': ('pittsburghpanthers.com', 'new'),
    'Notre Dame': ('und.com', 'new'),
    'SMU': ('smumustangs.com', 'new'),
    'Cal': ('calbears.com', 'new'),
    'Stanford': ('gostanford.com', 'new'),

    # SEC
    'Kentucky': ('ukathletics.com', 'new'),
    'Tennessee': ('utsports.com', 'new'),
    'Arkansas': ('arkansasrazorbacks.com', 'new'),
    'Alabama': ('rolltide.com', 'new'),
    'Auburn': ('auburntigers.com', 'new'),
    'Florida': ('floridagators.com', 'new'),
    'Georgia': ('georgiadogs.com', 'new'),
    'South Carolina': ('gamecocksonline.com', 'new'),
    'Mississippi State': ('hailstate.com', 'new'),
    'Ole Miss': ('olemisssports.com', 'new'),
    'LSU': ('lsusports.net', 'new'),
    'Vanderbilt': ('vucommodores.com', 'new'),
    'Missouri': ('mutigers.com', 'new'),
    'Texas A&M': ('12thman.com', 'new'),
    'Texas': ('texassports.com', 'new'),
    'Oklahoma': ('soonersports.com', 'new'),

    # Big 12
    'Kansas': ('kuathletics.com', 'new'),
    'Kansas State': ('kstatesports.com', 'new'),
    'Iowa State': ('cyclones.com', 'new'),
    'Baylor': ('baylorbears.com', 'new'),
    'TCU': ('gofrogs.com', 'new'),
    'Texas Tech': ('texastech.com', 'new'),
    'Oklahoma State': ('okstate.com', 'new'),
    'West Virginia': ('wvusports.com', 'new'),
    'BYU': ('byucougars.com', 'new'),
    'Cincinnati': ('gobearcats.com', 'new'),
    'Houston': ('uhcougars.com', 'new'),
    'UCF': ('ucfknights.com', 'new'),

    # AAC
    'Florida Atlantic': ('fausports.com', 'new'),
    'Memphis': ('gotigersgo.com', 'new'),
    'Tulane': ('tulanegreenwave.com', 'new'),
    'Temple': ('owlsports.com', 'new'),
    'Wichita State': ('goshockers.com', 'new'),
    'Tulsa': ('tulsahurricane.com', 'new'),
    'East Carolina': ('ecupirates.com', 'new'),
    'South Florida': ('gousfbulls.com', 'new'),
    'Charlotte': ('charlotte49ers.com', 'new'),
    'UAB': ('uabsports.com', 'new'),
    'North Texas': ('meangreensports.com', 'new'),
    'UTSA': ('goutsa.com', 'new'),
    'Rice': ('riceowls.com', 'new'),

    # Ivy League
    'Columbia': ('gocolumbialions.com', 'new'),
    'Princeton': ('goprincetontigers.com', 'new'),
    'Penn': ('pennathletics.com', 'new'),
    'Harvard': ('gocrimson.com', 'new'),
    'Yale': ('yalebulldogs.com', 'new'),
    'Brown': ('brownbears.com', 'new'),
    'Cornell': ('cornellbigred.com', 'new'),
    'Dartmouth': ('dartmouthsports.com', 'new'),

    # CAA
    'Towson': ('towsontigers.com', 'new'),
    'Hofstra': ('gohofstra.com', 'new'),
    'Delaware': ('bluehens.com', 'new'),
    'Drexel': ('drexeldragons.com', 'new'),
    'Northeastern': ('gonu.com', 'new'),
    'William & Mary': ('tribeathletics.com', 'new'),
    'Charleston': ('cofcsports.com', 'new'),
    'UNCW': ('uncwsports.com', 'new'),
    'Elon': ('elonphoenix.com', 'new'),
    'Monmouth': ('monmouthhawks.com', 'new'),
    'Stony Brook': ('stonybrookathletics.com', 'new'),
    'Hampton': ('hamptonpirates.com', 'new'),
    'Campbell': ('gocamels.com', 'new'),

    # Patriot League
    'Loyola (MD)': ('loyolagreyhounds.com', 'new'),
    'Loyola Maryland': ('loyolagreyhounds.com', 'new'),
    'Navy': ('navysports.com', 'new'),
    'Army': ('goarmywestpoint.com', 'new'),
    'Colgate': ('gocolgateraiders.com', 'new'),
    'Bucknell': ('bucknellbison.com', 'new'),
    'Lafayette': ('goleopards.com', 'new'),
    'Lehigh': ('lehighsports.com', 'new'),
    'American': ('aueagles.com', 'new'),
    'Boston University': ('goterriers.com', 'new'),
    'Holy Cross': ('goholycross.com', 'new'),

    # Atlantic 10
    'Dayton': ('daytonflyers.com', 'new'),
    'VCU': ('vcuathletics.com', 'new'),
    'Saint Louis': ('slubillikens.com', 'new'),
    'Richmond': ('richmondspiders.com', 'new'),
    'George Mason': ('gomason.com', 'new'),
    'George Washington': ('gwsports.com', 'new'),
    'La Salle': ('goexplorers.com', 'new'),
    'Rhode Island': ('gorhody.com', 'new'),
    'UMass': ('umassathletics.com', 'new'),
    'Fordham': ('fordhamsports.com', 'new'),
    'Duquesne': ('goduquesne.com', 'new'),
    "Saint Joseph's": ('sjuhawks.com', 'new'),
    'Loyola Chicago': ('loyolaramblers.com', 'new'),
}


def get_athletic_site(team_name: str) -> Optional[Tuple[str, str]]:
    """Get the athletic website domain and format for a team."""
    return ATHLETIC_SITES.get(team_name)


def _parse_nuxt_data(html: str) -> Optional[List[Any]]:
    """
    Parse __NUXT_DATA__ JSON array from page HTML.

    NUXT_DATA is a serialized format where values are stored as index references
    into a flat array. For example: {"attendance": 3815} means the attendance
    value is at array[3815].
    """
    match = re.search(r'<script[^>]*id="__NUXT_DATA__"[^>]*>([^<]+)</script>', html)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def _get_nuxt_value(data: List[Any], key: str) -> Optional[Any]:
    """
    Get a value from NUXT_DATA by dereferencing the index.

    NUXT_DATA stores data as a flat array where objects contain index references.
    This searches both:
    1. Direct key-value pairs in the array (key at index i, value at i+1)
    2. Keys inside dict objects that reference other indices
    """
    # Method 1: Search for direct key in array
    for i, item in enumerate(data):
        if item == key and i + 1 < len(data):
            ref = data[i + 1]
            if isinstance(ref, int) and ref < len(data):
                return data[ref]
            return ref

    # Method 2: Search inside dict objects for the key
    for item in data:
        if isinstance(item, dict) and key in item:
            ref = item[key]
            if isinstance(ref, int) and ref < len(data):
                val = data[ref]
                # Handle string numbers
                if isinstance(val, str) and val.replace(',', '').isdigit():
                    return int(val.replace(',', ''))
                return val
            return ref

    return None


def slugify(text: str) -> str:
    """Convert text to URL slug format."""
    # Remove rankings like "#7" or "(RV)"
    text = re.sub(r'#\d+/?(\d+)?', '', text)
    text = re.sub(r'\(RV\)', '', text)
    # Remove parenthetical qualifiers like "(CA)"
    text = re.sub(r'\s*\([^)]+\)\s*', '', text)
    text = text.strip()
    # Convert apostrophes to hyphens (Saint Mary's -> saint-mary-s)
    text = text.replace("'", '-')
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^a-z0-9-]+', '-', text.lower())
    # Clean up multiple hyphens
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    return slug


def fetch_schedule_page(domain: str, sport: str, season: str, gender: str = 'M') -> Optional[str]:
    """Fetch the schedule page HTML from a SIDEARM site."""
    sport_path = 'mens-basketball' if gender == 'M' else 'womens-basketball'
    url = f"https://{domain}/sports/{sport_path}/schedule/{season}"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
        print(f"  Schedule page returned {response.status_code}: {url}")
    except Exception as e:
        print(f"  Error fetching schedule: {e}")

    return None


def find_game_in_schedule(html: str, opponent: str, game_date: str, domain: str, sidearm_format: str) -> Optional[str]:
    """
    Find the box score URL for a specific game in the schedule HTML.

    Args:
        html: Schedule page HTML
        opponent: Opponent team name
        game_date: Date in YYYYMMDD format
        domain: Athletic site domain
        sidearm_format: 'new' or 'old'

    Returns:
        Full box score URL or None
    """
    soup = BeautifulSoup(html, 'html.parser')
    opponent_slug = slugify(opponent)

    # Parse the game date
    try:
        dt = datetime.strptime(game_date, '%Y%m%d')
        date_patterns = [
            dt.strftime('%b %d'),  # "Feb 01"
            dt.strftime('%B %d'),  # "February 01"
            dt.strftime('%-m/%-d'),  # "2/1"
            dt.strftime('%m/%d'),  # "02/01"
            dt.strftime('%b ') + str(dt.day),  # "Feb 1" (no leading zero)
            dt.strftime('%B ') + str(dt.day),  # "February 1" (no leading zero)
        ]
    except ValueError:
        date_patterns = []

    # Look for box score links
    boxscore_links = []

    if sidearm_format == 'old':
        # Old format: /boxscore.aspx?id=####
        for link in soup.find_all('a', href=re.compile(r'boxscore\.aspx\?id=\d+')):
            boxscore_links.append(link)
    else:
        # New format: /sports/.../stats/.../boxscore/#### or /sports/.../boxscore/####
        for link in soup.find_all('a', href=re.compile(r'/(?:stats/[^/]+/[^/]+/)?boxscore/\d+')):
            boxscore_links.append(link)

    # Collect ALL candidate games that match the opponent
    candidates: List[Tuple[str, str, bool]] = []  # (url, parent_text, date_matched)

    for link in boxscore_links:
        href = link.get('href', '')
        full_url = f"https://{domain}{href}" if href.startswith('/') else href

        # Find the game container
        # Supports multiple SIDEARM formats:
        # - Classic: li.sidearm-schedule-game
        # - Newer: div.schedule-game
        # - Newest (Nuxt): div.s-game-card
        game_container = None
        for parent in link.parents:
            if parent.name == 'li':
                classes = parent.get('class', [])
                # Check for the main game container, not sub-containers
                if 'sidearm-schedule-game' in classes and 'sidearm-schedule-game-links' not in ' '.join(classes):
                    game_container = parent
                    break
            elif parent.name == 'div':
                classes = parent.get('class', [])
                # Exact class match for schedule-game
                if 'schedule-game' in classes:
                    game_container = parent
                    break
                # New Nuxt format: s-game-card (but not s-game-card__* subcomponents)
                if 's-game-card' in classes:
                    game_container = parent
                    break
        if not game_container:
            # Try div or tr as fallback
            game_container = link.find_parent(['div', 'tr', 'article'])

        parent_text = game_container.get_text().lower() if game_container else ''

        # Check if this game matches the opponent
        opponent_match = False
        if opponent_slug in href.lower():
            opponent_match = True
        elif opponent_slug.replace('-', ' ') in parent_text or opponent.lower() in parent_text:
            opponent_match = True

        if not opponent_match:
            continue

        # Check if date matches
        date_matched = False
        if date_patterns:
            for pattern in date_patterns:
                if pattern.lower() in parent_text:
                    date_matched = True
                    break

        candidates.append((full_url, parent_text, date_matched))

    # Only return games with date match - no fallback to avoid wrong games
    for url, _, date_matched in candidates:
        if date_matched:
            return url

    return None


def fetch_boxscore(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and parse a SIDEARM box score page.

    Handles both old SIDEARM format (dt/dd elements) and new Nuxt.js format.

    Returns dict with:
        - attendance: int or None
        - officials: list of names
        - game_time: game start time (e.g., "7:00 PM")
        - arena: venue name with city, state
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        soup = BeautifulSoup(response.text, 'html.parser')
        result: Dict[str, Any] = {
            'attendance': None,
            'officials': [],
            'game_time': None,
            'arena': None,
            'sidearm_url': url,
        }

        # First try: Parse using dt/dd pattern (classic SIDEARM format)
        for dt in soup.find_all('dt'):
            dd = dt.find_next_sibling('dd')
            if not dd:
                continue
            label = dt.get_text(strip=True).lower()
            value = dd.get_text(strip=True)

            if 'attendance' in label and value:
                try:
                    result['attendance'] = int(value.replace(',', ''))
                except ValueError:
                    pass
            elif 'referee' in label or 'official' in label:
                # Split by comma for multiple officials
                officials = [o.strip() for o in value.split(',') if o.strip()]
                result['officials'] = officials
            elif label == 'time' and value:
                result['game_time'] = value
            elif label == 'site' or label == 'location' or label == 'arena' or label == 'venue':
                result['arena'] = value

        # Second try: Parse Nuxt.js __NUXT_DATA__ format (newer SIDEARM sites)
        # The data is stored as a JSON array with index references
        if not result['attendance']:
            html = response.text
            nuxt_data = _parse_nuxt_data(html)
            if nuxt_data:
                # Find attendance value using index reference
                attendance = _get_nuxt_value(nuxt_data, 'attendance')
                if attendance and isinstance(attendance, int) and attendance >= 100:
                    result['attendance'] = attendance

                # Try to get officials
                if not result['officials']:
                    officials = _get_nuxt_value(nuxt_data, 'officials')
                    if officials and isinstance(officials, str):
                        result['officials'] = [o.strip() for o in officials.split(',') if o.strip()]

                # Try to get arena/venue
                if not result['arena']:
                    venue = _get_nuxt_value(nuxt_data, 'venue')
                    if venue and isinstance(venue, str):
                        result['arena'] = venue

            # Fallback: regex patterns for older Nuxt format
            if not result['attendance']:
                # Look for venue, attendance, officials pattern in Nuxt data
                # Format: "venue","attendance","officials_string"
                nuxt_match = re.search(
                    r'"([^"]+(?:Arena|Center|Gym|Coliseum|Pavilion|Field House|Stadium|Complex)[^"]*,\s*[A-Z]{2})"\s*,\s*"(\d+)"\s*,\s*"([^"]+,[^"]+,[^"]+)"',
                    html,
                    re.IGNORECASE
                )
                if nuxt_match:
                    if not result['arena']:
                        result['arena'] = nuxt_match.group(1)
                    if not result['attendance']:
                        try:
                            result['attendance'] = int(nuxt_match.group(2))
                        except ValueError:
                            pass
                    if not result['officials']:
                        officials_str = nuxt_match.group(3)
                        result['officials'] = [o.strip() for o in officials_str.split(',') if o.strip()]

            if not result['officials']:
                # Look for comma-separated names pattern (3+ names)
                officials_match = re.search(r'"([A-Z][a-z]+ [A-Z][a-z]+(?:\s*,\s*[A-Z][a-z]+ [A-Z][a-z]+)+)"', html)
                if officials_match:
                    officials_str = officials_match.group(1)
                    officials = [o.strip() for o in officials_str.split(',') if o.strip()]
                    # Validate: should be 2-4 officials with proper name format
                    if 2 <= len(officials) <= 4:
                        result['officials'] = officials

        # Fallback: simple regex patterns
        if not result['attendance']:
            att_match = re.search(r'[Aa]ttendance[:\s]+([0-9,]+)', response.text)
            if att_match:
                try:
                    result['attendance'] = int(att_match.group(1).replace(',', ''))
                except ValueError:
                    pass

        return result

    except Exception as e:
        print(f"  Error fetching boxscore: {e}")
        return None


def get_season_string(date_yyyymmdd: str) -> str:
    """Convert a date to season string (e.g., '2024-25')."""
    try:
        dt = datetime.strptime(date_yyyymmdd, '%Y%m%d')
        year = dt.year
        month = dt.month
        # Basketball season spans two calendar years
        # Nov-Dec = first year of season, Jan-Apr = second year
        if month >= 8:  # Aug-Dec
            return f"{year}-{str(year + 1)[-2:]}"
        else:  # Jan-Jul
            return f"{year - 1}-{str(year)[-2:]}"
    except ValueError:
        return "2024-25"  # Default


def _fetch_from_team_site(
    team: str,
    opponent: str,
    game_date: str,
    gender: str,
    verbose: bool
) -> Optional[Dict[str, Any]]:
    """
    Fetch game data from a team's SIDEARM site.

    Returns dict with game data or None if not found.
    """
    site_info = get_athletic_site(team)
    if not site_info:
        return None

    domain, sidearm_format = site_info
    season = get_season_string(game_date)

    if verbose:
        print(f"  Checking {domain}...")

    # Fetch schedule page
    schedule_html = fetch_schedule_page(domain, 'basketball', season, gender)
    if not schedule_html:
        return None

    time.sleep(RATE_LIMIT_DELAY)

    # Find the game
    boxscore_url = find_game_in_schedule(schedule_html, opponent, game_date, domain, sidearm_format)
    if not boxscore_url:
        return None

    if verbose:
        print(f"  Found boxscore: {boxscore_url}")

    # Fetch box score
    data = fetch_boxscore(boxscore_url)
    return data


def supplement_game_data(
    home_team: str,
    away_team: str,
    game_date: str,
    gender: str = 'M',
    verbose: bool = True,
    expected_venue: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Fetch supplemental data from SIDEARM sites.

    Tries both teams' sites to find the game data. For neutral site games,
    either team's site will have the data.

    Args:
        home_team: Home team name (from Sports Reference)
        away_team: Away team name
        game_date: Date in YYYYMMDD format
        gender: 'M' or 'W'
        verbose: Print status messages
        expected_venue: If provided, validates the SIDEARM venue matches

    Returns:
        Dict with attendance, officials, etc. or None if not found
    """
    if verbose:
        print(f"  Looking for {away_team} @ {home_team} ({game_date})...")

    # Try home team's site first
    data = _fetch_from_team_site(home_team, away_team, game_date, gender, verbose)

    # Try away team's site if:
    # 1. Home team site didn't have the game, OR
    # 2. Home team site had the game but no attendance
    if not data or not data.get('attendance'):
        if verbose:
            reason = "Not found on home team site" if not data else "No attendance on home team site"
            print(f"  {reason}, trying away team...")
        away_data = _fetch_from_team_site(away_team, home_team, game_date, gender, verbose)

        if away_data:
            if not data:
                # Home team had nothing, use away data
                data = away_data
            elif away_data.get('attendance') and not data.get('attendance'):
                # Away team has attendance, merge it in
                data['attendance'] = away_data['attendance']
                if not data.get('sidearm_url'):
                    data['sidearm_url'] = away_data.get('sidearm_url')

    # If SIDEARM failed, try WMT Sports (Nuxt.js sites)
    if not data:
        if is_wmt_site(home_team) or is_wmt_site(away_team):
            if verbose:
                print(f"  Trying WMT Sports scraper...")
            wmt_data = wmt_supplement_game_data(
                home_team, away_team, game_date, gender,
                verbose=verbose, fetch_attendance=WMT_PLAYWRIGHT_AVAILABLE
            )
            if wmt_data:
                # Convert WMT format to SIDEARM format
                data = {
                    'attendance': wmt_data.get('attendance'),
                    'officials': wmt_data.get('officials', []),
                    'arena': wmt_data.get('location'),
                    'game_time': wmt_data.get('game_time'),
                    'wmt_url': wmt_data.get('wmt_url'),
                }

    # If still no attendance, try ESPN as fallback (men's basketball only)
    if (not data or not data.get('attendance')) and gender == 'M':
        if verbose:
            print(f"  Trying ESPN as fallback...")
        espn_attendance = get_espn_attendance(home_team, away_team, game_date, verbose=verbose)
        if espn_attendance:
            if not data:
                data = {'attendance': espn_attendance, 'source': 'espn'}
            else:
                data['attendance'] = espn_attendance
                data['source'] = 'espn'

    if not data:
        if verbose:
            print(f"  Could not find game on any team site")
        return None

    # Validate venue if expected_venue provided
    if expected_venue and data.get('arena'):
        sidearm_venue = data['arena'].lower()
        expected_lower = expected_venue.lower()

        # Check for significant word overlap
        sidearm_words = set(w for w in re.split(r'[\s,]+', sidearm_venue) if len(w) > 3)
        expected_words = set(w for w in re.split(r'[\s,]+', expected_lower) if len(w) > 3)
        common = sidearm_words & expected_words

        if len(common) < 1:
            if verbose:
                print(f"  WARNING: Venue mismatch - expected '{expected_venue}', got '{data['arena']}'")
            # Still return data but flag the mismatch
            data['venue_mismatch'] = True
            data['expected_venue'] = expected_venue

    if data and verbose:
        print(f"  Attendance: {data.get('attendance')}, Officials: {len(data.get('officials', []))}")

    return data


def supplement_all_games(games: List[Dict], verbose: bool = True) -> int:
    """
    Supplement all games with SIDEARM data where available.

    Args:
        games: List of game dictionaries (with basic_info)
        verbose: Print status messages

    Returns:
        Number of games supplemented
    """
    supplemented = 0

    for game in games:
        basic_info = game.get('basic_info', {})

        # Skip if already has attendance
        if basic_info.get('attendance'):
            continue

        home_team = basic_info.get('home_team', '')
        away_team = basic_info.get('away_team', '')
        game_date = basic_info.get('date_yyyymmdd', '')
        gender = basic_info.get('gender', 'M')

        if not home_team or not away_team or not game_date:
            continue

        data = supplement_game_data(home_team, away_team, game_date, gender, verbose)

        if data:
            if data.get('attendance'):
                basic_info['attendance'] = data['attendance']
                supplemented += 1
            if data.get('officials'):
                game['officials'] = data['officials']
            if data.get('sidearm_url'):
                basic_info['sidearm_url'] = data['sidearm_url']

        time.sleep(RATE_LIMIT_DELAY)

    return supplemented


if __name__ == '__main__':
    # Test with a sample game
    result = supplement_game_data(
        home_team='San Francisco',
        away_team="Saint Mary's",
        game_date='20241123',
        gender='M'
    )
    print(f"\nResult: {result}")
