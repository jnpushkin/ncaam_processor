#!/usr/bin/env python3
"""
Conference data updater - scrapes Sports Reference to update conference memberships.

Usage:
    python -m basketball_processor.scripts.update_conferences

This script fetches current conference memberships from Sports Reference
and updates the references/conferences.json file.
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: This script requires 'requests' and 'beautifulsoup4' packages.")
    print("Install them with: pip install requests beautifulsoup4")
    sys.exit(1)


# Major conferences to track (can be expanded)
CONFERENCES_TO_TRACK = {
    'acc': 'ACC',
    'big-ten': 'Big Ten',
    'sec': 'SEC',
    'big-12': 'Big 12',
    'big-east': 'Big East',
    'wcc': 'WCC',
    'pac-12': 'Pac-12',
    'aac': 'AAC',
    'mwc': 'Mountain West',
    'a-10': 'Atlantic 10',
    'mvc': 'MVC',
    'cusa': 'Conference USA',
    'mac': 'MAC',
    'sun-belt': 'Sun Belt',
    'ivy': 'Ivy League',
    'patriot': 'Patriot League',
    'colonial': 'CAA',
    'horizon': 'Horizon League',
    'maac': 'MAAC',
    'summit': 'Summit League',
    'southland': 'Southland',
    'big-sky': 'Big Sky',
    'ovc': 'OVC',
    'big-west': 'Big West',
    'wac': 'WAC',
    'socon': 'Southern Conference',
    'big-south': 'Big South',
    'america-east': 'America East',
    'atlantic-sun': 'ASUN',
    'meac': 'MEAC',
    'swac': 'SWAC',
    'nec': 'NEC',
}

BASE_URL = "https://www.sports-reference.com/cbb/conferences/{conf}/{year}.html"


def get_current_season_year() -> int:
    """Get the current basketball season year (e.g., 2025 for 2024-25 season)."""
    now = datetime.now()
    # Basketball season spans two calendar years
    # If we're in Jan-June, we're in the second half of the season
    if now.month <= 6:
        return now.year
    else:
        return now.year + 1


def fetch_conference_teams(conf_slug: str, year: int) -> Optional[List[str]]:
    """
    Fetch team list for a conference from Sports Reference.

    Args:
        conf_slug: Conference URL slug (e.g., 'acc', 'big-ten')
        year: Season year (e.g., 2025 for 2024-25 season)

    Returns:
        List of team names or None if fetch failed
    """
    url = BASE_URL.format(conf=conf_slug, year=year)

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; CBB-Tracker/1.0)'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the standings table
        standings_table = soup.find('table', {'id': 'standings'})
        if not standings_table:
            # Try alternate table IDs
            standings_table = soup.find('table', {'id': re.compile(r'standings|conf-summary')})

        if not standings_table:
            print(f"  Warning: Could not find standings table for {conf_slug}")
            return None

        teams = []
        rows = standings_table.find_all('tr')

        for row in rows:
            # Look for team name in the first cell
            team_cell = row.find('td', {'data-stat': 'school_name'})
            if not team_cell:
                team_cell = row.find('th', {'data-stat': 'school_name'})

            if team_cell:
                team_link = team_cell.find('a')
                if team_link:
                    team_name = team_link.get_text(strip=True)
                    teams.append(team_name)

        return teams if teams else None

    except requests.RequestException as e:
        print(f"  Error fetching {conf_slug}: {e}")
        return None


def update_conferences(year: Optional[int] = None) -> Dict[str, List[str]]:
    """
    Fetch all conference memberships.

    Args:
        year: Season year to fetch (defaults to current season)

    Returns:
        Dictionary mapping conference names to team lists
    """
    if year is None:
        year = get_current_season_year()

    print(f"Fetching conference data for {year-1}-{str(year)[2:]} season...")

    conferences = {}

    for slug, name in CONFERENCES_TO_TRACK.items():
        print(f"  Fetching {name}...", end=" ")
        teams = fetch_conference_teams(slug, year)

        if teams:
            conferences[name] = sorted(teams)
            print(f"Found {len(teams)} teams")
        else:
            print("Failed")

    return conferences


def save_conferences(conferences: Dict[str, List[str]], output_path: Path):
    """Save conference data to JSON file."""
    data = {
        '_metadata': {
            'updated': datetime.now().isoformat(),
            'source': 'sports-reference.com',
            'season': f"{get_current_season_year()-1}-{str(get_current_season_year())[2:]}",
        },
        'conferences': conferences,
    }

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved to {output_path}")


def main():
    """Main entry point."""
    # Determine output path
    script_dir = Path(__file__).parent
    references_dir = script_dir.parent / 'references'
    references_dir.mkdir(exist_ok=True)
    output_path = references_dir / 'conferences.json'

    # Fetch and save
    conferences = update_conferences()

    if conferences:
        save_conferences(conferences, output_path)

        # Print summary
        print(f"\nSummary:")
        print(f"  Conferences: {len(conferences)}")
        print(f"  Total teams: {sum(len(teams) for teams in conferences.values())}")
    else:
        print("No conference data fetched")
        sys.exit(1)


if __name__ == '__main__':
    main()
