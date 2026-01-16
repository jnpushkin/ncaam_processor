"""
WMT Sports (Nuxt.js) athletic website scraper.

Used for schools that don't use SIDEARM, including:
- Stanford (gostanford.com)
- Virginia (virginiasports.com)
- Virginia Tech (hokiesports.com)
- Nebraska (huskers.com)

Supports two modes:
1. Basic mode (HTTP only): Extracts venue, opponent, date, result from initial HTML
2. Full mode (with Playwright): Also extracts attendance from JS-rendered iframe

LIMITATION: WMT schedule pages only keep recent games accessible. For historical
games, use fetch_boxscore() directly with the known boxscore URL.

To use full mode, install Playwright: pip install playwright && playwright install chromium
"""

import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import requests

# Try to import Playwright for headless browser support
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

# Rate limiting
RATE_LIMIT_DELAY = 1.5  # seconds between requests

# WMT school slugs for wmt.games URLs
WMT_SCHOOL_SLUGS: Dict[str, str] = {
    'Stanford': 'stanford',
    'Virginia': 'virginia',
    'Virginia Tech': 'vt',
    'Nebraska': 'nebraska',
}


def extract_wmt_game_id(html: str) -> Optional[str]:
    """Extract the wmt.games game ID from boxscore page HTML.

    The game ID is found in the wmt_stats2_iframe_url field in NUXT_DATA,
    e.g., "https://wmt.games/stanford/stats/match/full/5732570"
    """
    # Look for wmt_stats2_iframe_url in the HTML
    match = re.search(r'wmt\.games/[^/]+/stats/match/full/(\d+)', html)
    if match:
        return match.group(1)
    return None


def fetch_attendance_playwright(school_slug: str, game_id: str, verbose: bool = True) -> Optional[int]:
    """Fetch attendance from wmt.games iframe using Playwright headless browser.

    Args:
        school_slug: WMT school slug (e.g., 'stanford', 'virginia')
        game_id: WMT game ID (e.g., '5732570')
        verbose: Print progress

    Returns:
        Attendance as integer, or None if not found/unavailable
    """
    if not PLAYWRIGHT_AVAILABLE:
        if verbose:
            print("  Playwright not available - install with: pip install playwright && playwright install chromium")
        return None

    url = f"https://wmt.games/{school_slug}/stats/match/full/{game_id}"
    if verbose:
        print(f"  Fetching attendance from {url}...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=30000)

            # Wait for content to load (attendance is JS-rendered)
            time.sleep(5)

            content = page.content()
            browser.close()

            # Extract attendance from HTML
            # Pattern: <h3>Attendance</h3><span class="match-stats-header__match-details-item-value">4504</span>
            match = re.search(
                r'Attendance\s*</h3>\s*<span[^>]*class="[^"]*match-stats-header__match-details-item-value[^"]*"[^>]*>\s*([0-9,]+)',
                content
            )
            if match:
                attendance_str = match.group(1).replace(',', '')
                attendance = int(attendance_str)
                if verbose:
                    print(f"  Found attendance: {attendance}")
                return attendance

            if verbose:
                print("  Attendance not found in page content")
            return None

    except (TimeoutError, ConnectionError) as e:
        if verbose:
            print(f"  Network error fetching attendance: {e}")
        return None
    except Exception as e:
        # Playwright-specific errors
        if verbose:
            print(f"  Browser error fetching attendance: {e}")
        return None


def fetch_attendance_from_stats_iframe(stats_url: str, verbose: bool = True) -> Optional[int]:
    """Fetch attendance from statistics.{domain}/stats/game/{id} iframe.

    Used by Virginia Tech (statistics.hokiesports.com) and potentially other schools
    that use a separate statistics subdomain instead of wmt.games.

    Args:
        stats_url: Full URL to stats page (e.g., 'https://statistics.hokiesports.com/stats/game/8754')
        verbose: Print progress

    Returns:
        Attendance as integer, or None if not found/unavailable
    """
    if not PLAYWRIGHT_AVAILABLE:
        if verbose:
            print("  Playwright not available")
        return None

    if verbose:
        print(f"  Fetching attendance from {stats_url}...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(stats_url, timeout=30000)
            time.sleep(3)

            # Get text content - attendance is in plain text format:
            # ATTENDANCE
            # 14623
            text = page.inner_text('body')
            browser.close()

            # Look for ATTENDANCE followed by a number
            match = re.search(r'ATTENDANCE\s*\n?\s*(\d+)', text, re.IGNORECASE)
            if match:
                attendance = int(match.group(1))
                if verbose:
                    print(f"  Found attendance: {attendance}")
                return attendance

            if verbose:
                print("  Attendance not found in stats page")
            return None

    except (TimeoutError, ConnectionError) as e:
        if verbose:
            print(f"  Network error fetching attendance from stats iframe: {e}")
        return None
    except Exception as e:
        # Playwright-specific errors
        if verbose:
            print(f"  Browser error fetching attendance from stats iframe: {e}")
        return None


def extract_stats_iframe_url(html: str) -> Optional[str]:
    """Extract statistics.{domain}/stats/game/{id} URL from page HTML.

    Some WMT sites (like Virginia Tech) embed stats in a separate subdomain iframe
    rather than using wmt.games.
    """
    match = re.search(r'https://statistics\.[^/]+/stats/game/\d+', html)
    if match:
        return match.group()
    return None


# WMT Sports sites
# Format: school_name -> (domain, sport_path)
# sport_path: 'mens-basketball' or 'mbball' depending on site
WMT_SITES: Dict[str, Tuple[str, str]] = {
    # Pac-12 / ACC
    'Stanford': ('gostanford.com', 'mens-basketball'),
    'Virginia': ('virginiasports.com', 'mbball'),
    'Virginia Tech': ('hokiesports.com', 'mens-basketball'),
    # Big Ten
    'Nebraska': ('huskers.com', 'mens-basketball'),
}


def get_wmt_site(team_name: str) -> Optional[Tuple[str, str]]:
    """Get the WMT Sports domain and sport path for a team."""
    return WMT_SITES.get(team_name)


def is_wmt_site(team_name: str) -> bool:
    """Check if a team uses WMT Sports."""
    return team_name in WMT_SITES


def fetch_schedule_page(
    domain: str,
    sport_path: str,
    season: str,
    gender: str = 'M',
    use_playwright: bool = True
) -> Optional[str]:
    """Fetch the schedule page HTML from a WMT Sports site.

    WMT sites use Nuxt.js and require JavaScript to render the full schedule.
    With use_playwright=True (default), uses headless browser to get complete data.
    """
    # WMT sites use different path patterns
    if gender == 'W':
        if sport_path == 'mens-basketball':
            sport_path = 'womens-basketball'
        elif sport_path == 'mbball':
            sport_path = 'wbball'

    url = f"https://{domain}/sports/{sport_path}/schedule"

    # Try Playwright first for full JS rendering
    if use_playwright and PLAYWRIGHT_AVAILABLE:
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, timeout=30000)
                # Wait for schedule to load
                time.sleep(3)
                html = page.content()
                browser.close()
                return html
        except (TimeoutError, ConnectionError) as e:
            print(f"  Network error fetching schedule: {e}")
            # Fall through to HTTP fetch
        except Exception as e:
            # Playwright-specific browser errors
            print(f"  Browser error fetching schedule: {e}")

    # Fallback to HTTP (won't have full schedule data)
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.text
        print(f"  WMT schedule page returned {response.status_code}: {url}")
    except requests.RequestException as e:
        print(f"  Network error fetching WMT schedule: {e}")
    except (TimeoutError, ConnectionError) as e:
        print(f"  Connection error fetching WMT schedule: {e}")

    return None


def parse_nuxt_data(html: str) -> Optional[List]:
    """Extract and parse __NUXT_DATA__ from WMT Sports page."""
    match = re.search(r'__NUXT_DATA__">\s*(\[.*?\])\s*</script>', html, re.DOTALL)
    if not match:
        return None

    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def extract_event_data(nuxt_data: List, event_id: int) -> Optional[Dict[str, Any]]:
    """Extract event data from parsed NUXT_DATA."""
    # Look for schedule-event-{id} in the data
    event_key = f"schedule-event-{event_id}"

    for i, item in enumerate(nuxt_data):
        if isinstance(item, dict) and event_key in item:
            # Found the data index, now find the actual event data
            # Usually at index 5 in WMT structure
            for j in range(max(0, i-10), min(len(nuxt_data), i+10)):
                if isinstance(nuxt_data[j], dict):
                    keys = nuxt_data[j].keys()
                    if 'location' in keys and 'opponent_name' in keys:
                        return _resolve_event_data(nuxt_data, nuxt_data[j])

    # Alternative: find dict with expected event fields
    for item in nuxt_data:
        if isinstance(item, dict):
            keys = set(item.keys())
            if {'id', 'location', 'opponent_name', 'datetime', 'venue_type'}.issubset(keys):
                return _resolve_event_data(nuxt_data, item)

    return None


def _resolve_event_data(nuxt_data: List, event_dict: Dict) -> Dict[str, Any]:
    """Resolve index references in event data to actual values."""
    result = {}

    for key, val in event_dict.items():
        if isinstance(val, int) and val < len(nuxt_data):
            resolved = nuxt_data[val]
            # Skip dict references (those are nested objects)
            if not isinstance(resolved, dict):
                result[key] = resolved
            else:
                result[key] = val  # Keep as index for now
        else:
            result[key] = val

    return result


def fetch_boxscore(
    url: str,
    team_name: Optional[str] = None,
    fetch_attendance: bool = False,
    verbose: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Fetch and parse a WMT Sports box score page.

    Args:
        url: Boxscore URL (e.g., https://gostanford.com/boxscore/24805)
        team_name: Team name for attendance lookup (e.g., 'Stanford')
        fetch_attendance: If True and Playwright available, fetch attendance from wmt.games
        verbose: Print progress

    Returns dict with:
        - location: venue city, state
        - opponent_name: opponent team name
        - datetime: game datetime
        - venue_type: 'home', 'away', or 'neutral'
        - is_conference: boolean
        - result: 'win' or 'loss'
        - score: tuple of (team_score, opponent_score)
        - attendance: integer (if fetch_attendance=True and Playwright available)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return None

        html = response.text
        nuxt_data = parse_nuxt_data(html)
        if not nuxt_data:
            return None

        # Extract event ID from URL
        match = re.search(r'/boxscore/(\d+)', url)
        if not match:
            return None

        event_id = int(match.group(1))
        event_data = extract_event_data(nuxt_data, event_id)

        if not event_data:
            return None

        result = {
            'location': event_data.get('location'),
            'opponent_name': event_data.get('opponent_name'),
            'datetime': event_data.get('datetime'),
            'venue_type': event_data.get('venue_type'),
            'is_conference': event_data.get('is_conference', False),
            'wmt_url': url,
            'attendance': None,
            'officials': [],
            'game_time': None,
        }

        # Parse result if available
        schedule_result = event_data.get('schedule_event_result')
        if isinstance(schedule_result, dict):
            result['result'] = schedule_result.get('result')
            result['winning_score'] = schedule_result.get('winning_score')
            result['losing_score'] = schedule_result.get('losing_score')

        # Fetch attendance using Playwright if requested
        if fetch_attendance and team_name:
            attendance = None

            # Method 1: Try wmt.games iframe (Stanford, Virginia, Nebraska)
            school_slug = WMT_SCHOOL_SLUGS.get(team_name)
            if school_slug:
                wmt_game_id = extract_wmt_game_id(html)
                if wmt_game_id:
                    attendance = fetch_attendance_playwright(school_slug, wmt_game_id, verbose)

            # Method 2: Try statistics.{domain} iframe (Virginia Tech)
            if attendance is None:
                stats_iframe_url = extract_stats_iframe_url(html)
                if stats_iframe_url:
                    attendance = fetch_attendance_from_stats_iframe(stats_iframe_url, verbose)

            if attendance:
                result['attendance'] = attendance
            elif verbose:
                print("  Could not find attendance in any iframe")

        return result

    except requests.RequestException as e:
        print(f"  Network error fetching WMT boxscore: {e}")
        return None
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  Parse error for WMT boxscore: {e}")
        return None


def find_game_in_schedule(
    html: str,
    opponent: str,
    game_date: str,
    domain: str
) -> Optional[str]:
    """
    Find the box score URL for a specific game in the WMT schedule.

    Args:
        html: Schedule page HTML (preferably Playwright-rendered for full content)
        opponent: Opponent team name
        game_date: Date in YYYYMMDD format
        domain: Athletic site domain

    Returns:
        Full box score URL or None
    """
    # Parse date for multiple format matching
    try:
        dt = datetime.strptime(game_date, '%Y%m%d')
        date_iso = dt.strftime('%Y-%m-%d')  # 2025-11-04
        date_slash = dt.strftime('%m/%d/%Y').lstrip('0').replace('/0', '/')  # 11/4/2025
        date_month_day = dt.strftime('%B %d').replace(' 0', ' ')  # November 4
        date_mon_day = dt.strftime('%b %d').replace(' 0', ' ')  # Nov 4
    except ValueError:
        return None

    # Method 1: Search rendered HTML for boxscore link near opponent name
    # This works with Playwright-rendered pages where the full schedule is visible
    opponent_lower = opponent.lower()

    # Look for boxscore ID near opponent name (within 500 chars)
    # Pattern: opponent name ... boxscore/ID or boxscore/ID ... opponent name
    pattern_after = rf'{re.escape(opponent)}.{{0,500}}boxscore/(\d+)'
    pattern_before = rf'boxscore/(\d+).{{0,500}}{re.escape(opponent)}'

    matches_after = re.findall(pattern_after, html, re.IGNORECASE | re.DOTALL)
    matches_before = re.findall(pattern_before, html, re.IGNORECASE | re.DOTALL)

    # Combine and dedupe while preserving order
    all_matches = []
    seen = set()
    for m in matches_after + matches_before:
        if m not in seen:
            all_matches.append(m)
            seen.add(m)

    if all_matches:
        # If we have multiple matches, try to find one that also matches the date
        for boxscore_id in all_matches:
            # Check if date appears near this boxscore ID
            date_pattern = rf'boxscore/{boxscore_id}.{{0,200}}({date_slash}|{date_mon_day}|{date_iso})'
            date_pattern2 = rf'({date_slash}|{date_mon_day}|{date_iso}).{{0,200}}boxscore/{boxscore_id}'
            if re.search(date_pattern, html, re.IGNORECASE | re.DOTALL) or \
               re.search(date_pattern2, html, re.IGNORECASE | re.DOTALL):
                return f"https://{domain}/boxscore/{boxscore_id}"

        # If no date match, return first opponent match (might be wrong if team plays twice)
        return f"https://{domain}/boxscore/{all_matches[0]}"

    # Method 2: Try NUXT_DATA parsing (works for non-rendered pages)
    nuxt_data = parse_nuxt_data(html)
    if nuxt_data:
        for item in nuxt_data:
            if isinstance(item, dict):
                keys = item.keys()
                if 'opponent_name' in keys and 'datetime' in keys:
                    opp_name_idx = item.get('opponent_name')
                    datetime_idx = item.get('datetime')
                    box_url_idx = item.get('box_score_url')

                    if isinstance(opp_name_idx, int) and opp_name_idx < len(nuxt_data):
                        opp_name = nuxt_data[opp_name_idx]
                        if isinstance(opp_name, str) and opponent_lower in opp_name.lower():
                            # Check date
                            if isinstance(datetime_idx, int) and datetime_idx < len(nuxt_data):
                                game_datetime = nuxt_data[datetime_idx]
                                if isinstance(game_datetime, str) and date_iso in game_datetime:
                                    # Found matching game
                                    if isinstance(box_url_idx, int) and box_url_idx < len(nuxt_data):
                                        box_url = nuxt_data[box_url_idx]
                                        if isinstance(box_url, str):
                                            return box_url
                                    # Try to construct URL from event ID
                                    id_idx = item.get('id')
                                    if isinstance(id_idx, int) and id_idx < len(nuxt_data):
                                        event_id = nuxt_data[id_idx]
                                        if event_id:
                                            return f"https://{domain}/boxscore/{event_id}"

    return None


def supplement_game_data(
    home_team: str,
    away_team: str,
    game_date: str,
    gender: str = 'M',
    verbose: bool = True,
    fetch_attendance: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Fetch supplemental data from WMT Sports sites.

    Extracts: venue/location, opponent, date, venue_type, result.
    With fetch_attendance=True (and Playwright installed), also extracts attendance.

    Args:
        home_team: Home team name
        away_team: Away team name
        game_date: Date in YYYYMMDD format
        gender: 'M' or 'W'
        verbose: Print progress
        fetch_attendance: If True and Playwright available, fetch attendance

    Returns:
        Dict with game data or None if not found
    """
    if verbose:
        print(f"  Looking for {away_team} @ {home_team} ({game_date}) on WMT Sports...")

    # Try home team's site first
    site_info = get_wmt_site(home_team)
    if site_info:
        domain, sport_path = site_info
        if verbose:
            print(f"  Checking {domain}...")

        # Calculate season string (e.g., "2024-25")
        try:
            dt = datetime.strptime(game_date, '%Y%m%d')
            if dt.month >= 10:  # Oct-Dec = first year of season
                season = f"{dt.year}-{str(dt.year + 1)[-2:]}"
            else:  # Jan-Apr = second year of season
                season = f"{dt.year - 1}-{str(dt.year)[-2:]}"
        except ValueError:
            return None

        schedule_html = fetch_schedule_page(domain, sport_path, season, gender)
        if schedule_html:
            boxscore_url = find_game_in_schedule(schedule_html, away_team, game_date, domain)
            if boxscore_url:
                time.sleep(RATE_LIMIT_DELAY)
                data = fetch_boxscore(
                    boxscore_url,
                    team_name=home_team,
                    fetch_attendance=fetch_attendance,
                    verbose=verbose
                )
                if data:
                    if verbose:
                        att_str = f", Attendance: {data.get('attendance')}" if data.get('attendance') else ""
                        print(f"  Found on {domain}: {data.get('location', 'N/A')}{att_str}")
                    return data

    # Try away team's site
    site_info = get_wmt_site(away_team)
    if site_info:
        domain, sport_path = site_info
        if verbose:
            print(f"  Checking {domain}...")

        try:
            dt = datetime.strptime(game_date, '%Y%m%d')
            if dt.month >= 10:
                season = f"{dt.year}-{str(dt.year + 1)[-2:]}"
            else:
                season = f"{dt.year - 1}-{str(dt.year)[-2:]}"
        except ValueError:
            return None

        schedule_html = fetch_schedule_page(domain, sport_path, season, gender)
        if schedule_html:
            boxscore_url = find_game_in_schedule(schedule_html, home_team, game_date, domain)
            if boxscore_url:
                time.sleep(RATE_LIMIT_DELAY)
                data = fetch_boxscore(
                    boxscore_url,
                    team_name=away_team,
                    fetch_attendance=fetch_attendance,
                    verbose=verbose
                )
                if data:
                    if verbose:
                        att_str = f", Attendance: {data.get('attendance')}" if data.get('attendance') else ""
                        print(f"  Found on {domain}: {data.get('location', 'N/A')}{att_str}")
                    return data

    if verbose:
        print(f"  Game not found on WMT Sports sites")

    return None
