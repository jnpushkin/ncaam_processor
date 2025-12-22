"""
Historical conference membership scraper and lookup.

Scrapes Sports Reference to get historical conference membership data,
allowing accurate conference lookup for any team in any year.
"""

import json
import os
import re
import time
from typing import Dict, List, Optional, Any

import requests

# Rate limiting: 3.1 seconds between requests (under 20/min limit)
REQUEST_DELAY = 3.1

# Data file path
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'conference_history.json')

# Conference slugs for men's basketball
MEN_CONFERENCE_SLUGS = [
    ('ACC', 'acc'),
    ('America East', 'america-east'),
    ('American', 'american'),
    ('Atlantic 10', 'atlantic-10'),
    ('Atlantic Sun', 'atlantic-sun'),
    ('Big 12', 'big-12'),
    ('Big East', 'big-east'),
    ('Big Sky', 'big-sky'),
    ('Big South', 'big-south'),
    ('Big Ten', 'big-ten'),
    ('Big West', 'big-west'),
    ('CAA', 'coastal'),
    ('Conference USA', 'cusa'),
    ('Horizon', 'horizon'),
    ('Ivy League', 'ivy'),
    ('MAAC', 'maac'),
    ('MAC', 'mac'),
    ('MEAC', 'meac'),
    ('Missouri Valley', 'mvc'),
    ('Mountain West', 'mwc'),
    ('NEC', 'nec'),
    ('Ohio Valley', 'ovc'),
    ('Patriot League', 'patriot'),
    ('SEC', 'sec'),
    ('Southern', 'southern'),
    ('Southland', 'southland'),
    ('Summit League', 'summit'),
    ('Sun Belt', 'sun-belt'),
    ('SWAC', 'swac'),
    ('WAC', 'wac'),
    ('WCC', 'wcc'),
]

# Women's conference slugs (same structure, different URL path)
WOMEN_CONFERENCE_SLUGS = [
    ('ACC', 'acc'),
    ('America East', 'america-east'),
    ('American', 'american'),
    ('Atlantic 10', 'atlantic-10'),
    ('Atlantic Sun', 'atlantic-sun'),
    ('Big 12', 'big-12'),
    ('Big East', 'big-east'),
    ('Big Sky', 'big-sky'),
    ('Big South', 'big-south'),
    ('Big Ten', 'big-ten'),
    ('Big West', 'big-west'),
    ('CAA', 'coastal'),
    ('Conference USA', 'cusa'),
    ('Horizon', 'horizon'),
    ('Ivy League', 'ivy'),
    ('MAAC', 'maac'),
    ('MAC', 'mac'),
    ('MEAC', 'meac'),
    ('Missouri Valley', 'mvc'),
    ('Mountain West', 'mwc'),
    ('NEC', 'nec'),
    ('Ohio Valley', 'ovc'),
    ('Patriot League', 'patriot'),
    ('SEC', 'sec'),
    ('Southern', 'southern'),
    ('Southland', 'southland'),
    ('Summit League', 'summit'),
    ('Sun Belt', 'sun-belt'),
    ('SWAC', 'swac'),
    ('WAC', 'wac'),
    ('WCC', 'wcc'),
]


def _fetch_conference_schools(conf_name: str, slug: str, gender: str = 'men') -> List[Dict[str, Any]]:
    """
    Fetch schools for a conference from Sports Reference.

    Args:
        conf_name: Display name of the conference
        slug: URL slug for the conference
        gender: 'men' or 'women'

    Returns:
        List of dicts with school, from_year, to_year
    """
    url = f"https://www.sports-reference.com/cbb/conferences/{slug}/{gender}/schools.html"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"  [HTTP {response.status_code}] Failed to fetch {conf_name}")
            return []

        html = response.text
        schools = []

        # Parse the schools table
        # Look for rows with school data
        # Format: <td data-stat="school_name"><a>Name</a></td><td data-stat="year_min">1954</td><td data-stat="year_max">2026</td>

        # Pattern to match school rows in the table
        row_pattern = re.compile(
            r'data-stat="school_name"[^>]*><a[^>]*>([^<]+)</a></td>'
            r'<td[^>]*data-stat="year_min"[^>]*>(\d+)</td>'
            r'<td[^>]*data-stat="year_max"[^>]*>(\d+)</td>',
            re.DOTALL
        )

        for match in row_pattern.finditer(html):
            school_name = match.group(1).strip()
            from_year = int(match.group(2))
            to_year = int(match.group(3))

            schools.append({
                'school': school_name,
                'from_year': from_year,
                'to_year': to_year,
            })

        return schools

    except Exception as e:
        print(f"  [ERROR] {conf_name}: {e}")
        return []


def scrape_all_conferences(include_women: bool = False, test_mode: bool = False) -> Dict[str, List[Dict]]:
    """
    Scrape all conference membership data.

    Args:
        include_women: Whether to also scrape women's conferences
        test_mode: If True, only scrape first 3 conferences

    Returns:
        Dict mapping school names to list of conference memberships
    """
    # Structure: { "School Name": [{"conference": "ACC", "from": 1954, "to": 2014}, ...] }
    school_history: Dict[str, List[Dict]] = {}

    conferences_to_scrape = []

    # Add men's conferences
    for conf_name, slug in MEN_CONFERENCE_SLUGS:
        conferences_to_scrape.append((conf_name, slug, 'men'))

    # Optionally add women's conferences
    if include_women:
        for conf_name, slug in WOMEN_CONFERENCE_SLUGS:
            conferences_to_scrape.append((conf_name, slug, 'women'))

    if test_mode:
        conferences_to_scrape = conferences_to_scrape[:3]

    total = len(conferences_to_scrape)
    print(f"Scraping {total} conferences...")

    for i, (conf_name, slug, gender) in enumerate(conferences_to_scrape):
        print(f"  [{i+1}/{total}] {conf_name} ({gender})...")

        schools = _fetch_conference_schools(conf_name, slug, gender)

        for school in schools:
            school_name = school['school']

            # For women's, we might want to track separately or combine
            # For now, we'll use the same school name but track gender in the data
            if gender == 'women':
                key = f"{school_name} (W)"
            else:
                key = school_name

            if key not in school_history:
                school_history[key] = []

            school_history[key].append({
                'conference': conf_name,
                'from': school['from_year'],
                'to': school['to_year'],
            })

        print(f"    Found {len(schools)} schools")

        # Rate limiting (skip delay after last request)
        if i < total - 1:
            time.sleep(REQUEST_DELAY)

    # Sort each school's conference history by from year
    for school in school_history:
        school_history[school].sort(key=lambda x: x['from'])

    return school_history


def save_conference_history(history: Dict[str, List[Dict]]) -> None:
    """Save conference history to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"Saved conference history to {HISTORY_FILE}")
    print(f"Total schools: {len(history)}")


def load_conference_history() -> Dict[str, List[Dict]]:
    """Load conference history from JSON file."""
    if not os.path.exists(HISTORY_FILE):
        return {}

    with open(HISTORY_FILE, 'r') as f:
        return json.load(f)


def get_conference_for_year(team: str, year: int, gender: str = 'M') -> Optional[str]:
    """
    Get the conference a team was in for a specific year.

    Args:
        team: Team name
        year: Year to look up (e.g., 2023)
        gender: 'M' for men's, 'W' for women's

    Returns:
        Conference name or None if not found
    """
    # Common aliases - map short names to full Sports Reference names
    ALIASES = {
        'UNC': 'North Carolina',
        'NC State': 'NC State',
        'NCSU': 'NC State',
        'Ole Miss': 'Mississippi',
        'LSU': 'Louisiana State',
        'USC': 'Southern California',
        'UCF': 'Central Florida',
        'SMU': 'Southern Methodist',
        'TCU': 'Texas Christian',
        'UNLV': 'Nevada-Las Vegas',
        'UTEP': 'Texas-El Paso',
        'UAB': 'Alabama-Birmingham',
        'VCU': 'Virginia Commonwealth',
        'UConn': 'Connecticut',
        'UMass': 'Massachusetts',
        'Pitt': 'Pittsburgh',
        'Cal': 'California',
        'Miami': 'Miami (FL)',
    }

    # Check if team is an alias
    canonical_team = ALIASES.get(team, team)

    history = load_conference_history()

    # Try exact match first
    key = f"{canonical_team} (W)" if gender == 'W' else canonical_team

    if key in history:
        for membership in history[key]:
            if membership['from'] <= year <= membership['to']:
                return membership['conference']

    # Try without gender suffix for men's
    if gender == 'M' and canonical_team in history:
        for membership in history[canonical_team]:
            if membership['from'] <= year <= membership['to']:
                return membership['conference']

    # Also try with original team name if different
    if canonical_team != team:
        original_key = f"{team} (W)" if gender == 'W' else team
        if original_key in history:
            for membership in history[original_key]:
                if membership['from'] <= year <= membership['to']:
                    return membership['conference']

    # Try fuzzy matching for common name variations
    # Only do substring matching if the search term is long enough to avoid false matches
    team_lower = team.lower()
    canonical_lower = canonical_team.lower()

    for school_name, memberships in history.items():
        # Skip women's entries when looking for men's
        if gender == 'M' and school_name.endswith(' (W)'):
            continue
        if gender == 'W' and not school_name.endswith(' (W)'):
            continue

        school_compare = school_name.replace(' (W)', '').lower()

        # Exact match (case-insensitive)
        if school_compare == team_lower or school_compare == canonical_lower:
            for membership in memberships:
                if membership['from'] <= year <= membership['to']:
                    return membership['conference']

        # Only do substring matching if search term is 5+ chars to avoid false matches
        # like "UNC" matching "UNC Asheville"
        if len(team_lower) >= 5:
            if school_compare in team_lower or team_lower in school_compare:
                for membership in memberships:
                    if membership['from'] <= year <= membership['to']:
                        return membership['conference']

    return None


def run_scrape(test_mode: bool = False, include_women: bool = False):
    """
    Run the full scrape and save results.

    Args:
        test_mode: Only scrape 3 conferences for testing
        include_women: Also scrape women's conferences
    """
    print("Starting conference history scrape...")
    print(f"Rate limit: {REQUEST_DELAY}s between requests")

    if test_mode:
        print("TEST MODE: Only scraping 3 conferences")

    history = scrape_all_conferences(include_women=include_women, test_mode=test_mode)
    save_conference_history(history)

    print("\nDone!")


if __name__ == '__main__':
    import sys

    test_mode = '--test' in sys.argv
    include_women = '--women' in sys.argv

    run_scrape(test_mode=test_mode, include_women=include_women)
