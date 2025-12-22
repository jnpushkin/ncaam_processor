"""
Scrape conference history from individual school pages on Sports Reference.

This approach is more accurate than scraping conference pages because each
school's page shows their actual year-by-year conference membership.
"""

import json
import os
import re
import time
from typing import Dict, List, Optional, Tuple

import requests

# Rate limiting: 3.1 seconds between requests (under 20/min limit)
REQUEST_DELAY = 3.1

# Data file paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
SCHOOL_HISTORY_FILE = os.path.join(DATA_DIR, 'school_conference_history.json')
REFRESH_TIMESTAMP_FILE = os.path.join(DATA_DIR, 'conference_refresh_timestamp.txt')

# Auto-refresh settings
REFRESH_INTERVAL_DAYS = 90  # Check for updates every 90 days

# Headers for requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}


def _fetch_school_list(gender: str = 'men') -> List[Tuple[str, str]]:
    """
    Fetch list of all schools from Sports Reference index.

    Returns:
        List of (school_name, slug) tuples
    """
    url = "https://www.sports-reference.com/cbb/schools/"

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"Failed to fetch schools index: HTTP {response.status_code}")
            return []

        html = response.text
        schools = []

        # Pattern to match school links: /cbb/schools/{slug}/men/
        # The school name is in the link text
        pattern = re.compile(
            rf'<a href="/cbb/schools/([^/]+)/{gender}/"[^>]*>([^<]+)</a>',
            re.IGNORECASE
        )

        for match in pattern.finditer(html):
            slug = match.group(1)
            name = match.group(2).strip()
            schools.append((name, slug))

        return schools

    except Exception as e:
        print(f"Error fetching schools index: {e}")
        return []


def _fetch_school_conference_history(slug: str, gender: str = 'men') -> List[Dict]:
    """
    Fetch conference history for a single school from their SR page.

    Args:
        slug: School's URL slug (e.g., 'connecticut')
        gender: 'men' or 'women'

    Returns:
        List of dicts with year and conference
    """
    url = f"https://www.sports-reference.com/cbb/schools/{slug}/{gender}/"

    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return []

        html = response.text
        history = []

        # The season table has rows with year and conference
        # Pattern to match: <td data-stat="season">2024-25</td>...<td data-stat="conf_abbr">Big East</td>
        # or it might be in a different format

        # First try to find the main table with season data
        # Look for rows in the school's season-by-season table

        # Pattern for season rows - looking for year and conference in same row
        # Conference can be either plain text or inside a link
        row_pattern = re.compile(
            r'<tr[^>]*>.*?'
            r'data-stat="season"[^>]*>.*?(\d{4})-\d{2}.*?</t[dh]>.*?'
            r'data-stat="conf_abbr"[^>]*>(?:<a[^>]*>)?([^<]+)(?:</a>)?</td>',
            re.DOTALL
        )

        for match in row_pattern.finditer(html):
            year = int(match.group(1))
            conf = match.group(2).strip()
            if conf:  # Skip empty conferences
                history.append({
                    'year': year,
                    'conference': conf
                })

        # Sort by year
        history.sort(key=lambda x: x['year'])

        return history

    except Exception as e:
        print(f"Error fetching {slug}: {e}")
        return []


def _compress_history(yearly_history: List[Dict]) -> List[Dict]:
    """
    Compress year-by-year history into ranges.

    Input: [{'year': 2020, 'conference': 'Big East'}, {'year': 2021, 'conference': 'Big East'}, ...]
    Output: [{'conference': 'Big East', 'from': 2020, 'to': 2024}, ...]
    """
    if not yearly_history:
        return []

    compressed = []
    current_conf = None
    current_from = None
    current_to = None

    for entry in yearly_history:
        year = entry['year']
        conf = entry['conference']

        if conf != current_conf:
            # Save previous range
            if current_conf is not None:
                compressed.append({
                    'conference': current_conf,
                    'from': current_from,
                    'to': current_to
                })
            # Start new range
            current_conf = conf
            current_from = year
            current_to = year
        else:
            # Extend current range
            current_to = year

    # Don't forget the last range
    if current_conf is not None:
        compressed.append({
            'conference': current_conf,
            'from': current_from,
            'to': current_to
        })

    return compressed


def scrape_all_schools(gender: str = 'men', test_mode: bool = False) -> Dict[str, List[Dict]]:
    """
    Scrape conference history for all schools.

    Args:
        gender: 'men' or 'women'
        test_mode: Only scrape first 5 schools

    Returns:
        Dict mapping school names to compressed conference history
    """
    print(f"Fetching list of {gender}'s schools...")
    schools = _fetch_school_list(gender)

    if not schools:
        print("No schools found!")
        return {}

    print(f"Found {len(schools)} schools")

    if test_mode:
        schools = schools[:5]
        print(f"TEST MODE: Only scraping {len(schools)} schools")

    # Estimate time
    est_minutes = len(schools) * REQUEST_DELAY / 60
    print(f"Estimated time: {est_minutes:.1f} minutes")

    time.sleep(REQUEST_DELAY)  # Initial delay after fetching index

    all_history = {}

    for i, (name, slug) in enumerate(schools):
        print(f"  [{i+1}/{len(schools)}] {name} ({slug})...", end=" ", flush=True)

        yearly_history = _fetch_school_conference_history(slug, gender)

        if yearly_history:
            compressed = _compress_history(yearly_history)

            # Use name with (W) suffix for women's
            key = f"{name} (W)" if gender == 'women' else name
            all_history[key] = compressed

            # Show brief summary
            confs = [h['conference'] for h in compressed]
            print(f"{len(yearly_history)} seasons, {len(compressed)} conferences: {', '.join(confs[-3:])}")
        else:
            print("no data")

        # Rate limiting (skip delay after last request)
        if i < len(schools) - 1:
            time.sleep(REQUEST_DELAY)

    return all_history


def save_school_history(history: Dict[str, List[Dict]]) -> None:
    """Save school conference history to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(SCHOOL_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"\nSaved to {SCHOOL_HISTORY_FILE}")
    print(f"Total schools: {len(history)}")


def load_school_history() -> Dict[str, List[Dict]]:
    """Load school conference history from JSON file."""
    if not os.path.exists(SCHOOL_HISTORY_FILE):
        return {}

    with open(SCHOOL_HISTORY_FILE, 'r') as f:
        return json.load(f)


def _get_last_refresh_time() -> Optional[float]:
    """Get timestamp of last refresh, or None if never refreshed."""
    if not os.path.exists(REFRESH_TIMESTAMP_FILE):
        return None
    try:
        with open(REFRESH_TIMESTAMP_FILE, 'r') as f:
            return float(f.read().strip())
    except (ValueError, IOError):
        return None


def _save_refresh_timestamp():
    """Save current time as last refresh timestamp."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(REFRESH_TIMESTAMP_FILE, 'w') as f:
        f.write(str(time.time()))


def should_auto_refresh() -> bool:
    """
    Check if an automatic refresh is needed.

    Returns True if:
    - No data file exists
    - Last refresh was more than REFRESH_INTERVAL_DAYS ago
    - We're in a new basketball season (October-March) and data is stale
    """
    from datetime import datetime

    # No data file - need full scrape, not refresh
    if not os.path.exists(SCHOOL_HISTORY_FILE):
        return False

    last_refresh = _get_last_refresh_time()
    if last_refresh is None:
        # Never refreshed - should refresh
        return True

    # Check if enough time has passed
    days_since_refresh = (time.time() - last_refresh) / (24 * 60 * 60)
    if days_since_refresh >= REFRESH_INTERVAL_DAYS:
        return True

    # Check if we're in basketball season and data might be stale
    now = datetime.now()
    current_year = now.year

    # Basketball season is roughly October-March
    # The season year is the year it starts (e.g., 2025-26 season = 2025)
    if now.month >= 10:
        season_year = current_year
    elif now.month <= 3:
        season_year = current_year - 1
    else:
        # Off-season (April-September) - less urgent
        return False

    # Check if our data covers the current season
    history = load_school_history()
    if not history:
        return False

    # Sample a few major schools to see if data is current
    sample_schools = ['Duke', 'North Carolina', 'Kansas', 'Kentucky', 'Connecticut']
    for school in sample_schools:
        if school in history and history[school]:
            if history[school][-1]['to'] < season_year:
                return True

    return False


def auto_refresh_if_needed(include_women: bool = True, silent: bool = False) -> bool:
    """
    Automatically refresh conference data if needed.

    Called during website generation to ensure data is current.

    Args:
        include_women: Whether to refresh women's data too
        silent: If True, only print if actually refreshing

    Returns:
        True if refresh was performed, False otherwise
    """
    from datetime import datetime

    if not should_auto_refresh():
        if not silent:
            last_refresh = _get_last_refresh_time()
            if last_refresh:
                days_ago = int((time.time() - last_refresh) / (24 * 60 * 60))
                next_in = REFRESH_INTERVAL_DAYS - days_ago
                print(f"Conference data: Last refresh was {days_ago} days ago. Next in {next_in} days.")
        return False

    print("Conference data needs refresh. Starting automatic update...")
    print("(This runs every ~90 days during basketball season)")
    print()

    refresh_current_season(include_women=include_women)
    _save_refresh_timestamp()

    return True


def get_conference_for_school(school: str, year: int, gender: str = 'M') -> Optional[str]:
    """
    Get the conference a school was in for a specific year.

    Args:
        school: School name
        year: Year to look up
        gender: 'M' for men's, 'W' for women's

    Returns:
        Conference name or None
    """
    history = load_school_history()

    # For women's, try with (W) suffix first
    if gender == 'W':
        key = f"{school} (W)"
        if key in history:
            for membership in history[key]:
                if membership['from'] <= year <= membership['to']:
                    return membership['conference']

    # Try without suffix (men's or fallback)
    if school not in history:
        return None

    for membership in history[school]:
        if membership['from'] <= year <= membership['to']:
            return membership['conference']

    return None


def _refresh_school(slug: str, gender: str, existing_history: List[Dict]) -> Optional[List[Dict]]:
    """
    Refresh a single school's conference history for the current season.

    Returns updated history if changed, None if no update needed.
    """
    from datetime import datetime
    current_year = datetime.now().year

    # If season starts in fall, the "year" is the calendar year when season starts
    # e.g., 2025-26 season is year 2025

    # Check if we already have current year
    if existing_history and existing_history[-1]['to'] >= current_year:
        return None  # Already up to date

    # Fetch latest data
    yearly = _fetch_school_conference_history(slug, gender)
    if not yearly:
        return None

    # Get the latest entry
    latest = yearly[-1] if yearly else None
    if not latest:
        return None

    latest_year = latest['year']
    latest_conf = latest['conference']

    # Update existing history
    if existing_history:
        last_entry = existing_history[-1]
        if last_entry['conference'] == latest_conf:
            # Same conference - just extend the range
            last_entry['to'] = latest_year
        else:
            # Conference changed - add new entry
            existing_history.append({
                'conference': latest_conf,
                'from': latest_year,
                'to': latest_year
            })
    else:
        # No existing history - compress and use full history
        return _compress_history(yearly)

    return existing_history


def refresh_current_season(include_women: bool = True):
    """
    Refresh conference data for the current season only.

    Much faster than full scrape - only checks latest season for each school.
    """
    from datetime import datetime

    print("=" * 60)
    print("Conference History Refresh (Current Season)")
    print("=" * 60)
    print(f"Rate limit: {REQUEST_DELAY}s between requests")
    print()

    # Load existing data
    history = load_school_history()
    if not history:
        print("No existing data found. Run full scrape first.")
        return

    print(f"Loaded {len(history)} schools")

    current_year = datetime.now().year

    # Get school lists
    men_schools = _fetch_school_list('men')
    women_schools = _fetch_school_list('women') if include_women else []

    print(f"Checking {len(men_schools)} men's + {len(women_schools)} women's schools")
    print()

    time.sleep(REQUEST_DELAY)

    updated_count = 0
    skipped_count = 0

    # Process men's schools
    print("Checking MEN'S schools...")
    for i, (name, slug) in enumerate(men_schools):
        existing = history.get(name, [])

        # Skip if already current
        if existing and existing[-1]['to'] >= current_year:
            skipped_count += 1
            continue

        print(f"  [{i+1}/{len(men_schools)}] {name}...", end=" ", flush=True)

        updated = _refresh_school(slug, 'men', existing.copy() if existing else [])
        if updated:
            history[name] = updated
            updated_count += 1
            print(f"updated (now through {updated[-1]['to']})")
        else:
            print("no change")

        time.sleep(REQUEST_DELAY)

    # Process women's schools
    if include_women:
        print("\nChecking WOMEN'S schools...")
        for i, (name, slug) in enumerate(women_schools):
            key = f"{name} (W)"
            existing = history.get(key, [])

            # Skip if already current
            if existing and existing[-1]['to'] >= current_year:
                skipped_count += 1
                continue

            print(f"  [{i+1}/{len(women_schools)}] {name}...", end=" ", flush=True)

            updated = _refresh_school(slug, 'women', existing.copy() if existing else [])
            if updated:
                history[key] = updated
                updated_count += 1
                print(f"updated (now through {updated[-1]['to']})")
            else:
                print("no change")

            time.sleep(REQUEST_DELAY)

    # Save updated data
    save_school_history(history)

    print()
    print(f"Summary: {updated_count} updated, {skipped_count} already current")
    print("Done!")


def run_scrape(gender: str = 'men', test_mode: bool = False, include_women: bool = False):
    """
    Run the full scrape and save results.

    Args:
        gender: 'men' or 'women' (or 'both' with include_women)
        test_mode: Only scrape 5 schools for testing
        include_women: Also scrape women's schools after men's
    """
    print("=" * 60)
    print("School Conference History Scraper")
    print("=" * 60)
    print(f"Rate limit: {REQUEST_DELAY}s between requests")
    print()

    all_history = {}

    # Scrape men's
    if gender in ('men', 'both') or not include_women:
        print("Scraping MEN'S schools...")
        men_history = scrape_all_schools('men', test_mode)
        all_history.update(men_history)

    # Scrape women's
    if gender == 'women' or include_women:
        print("\nScraping WOMEN'S schools...")
        women_history = scrape_all_schools('women', test_mode)
        all_history.update(women_history)

    save_school_history(all_history)
    print("\nDone!")


if __name__ == '__main__':
    import sys

    if '--refresh' in sys.argv:
        # Quick refresh for current season only
        include_women = '--women' in sys.argv or '--all' in sys.argv
        refresh_current_season(include_women=include_women)
    else:
        # Full scrape
        test_mode = '--test' in sys.argv
        include_women = '--women' in sys.argv
        run_scrape(test_mode=test_mode, include_women=include_women)
