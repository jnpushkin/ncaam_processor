"""
AP Poll scraper for college basketball rankings.

Scrapes historical AP poll data from Sports Reference with rate limiting
and caching to avoid excessive requests.

Usage:
    # Scrape and cache current season (men's)
    python -m basketball_processor.scrapers.poll_scraper

    # Scrape women's polls
    python -m basketball_processor.scrapers.poll_scraper --gender W

    # Scrape specific season
    python -m basketball_processor.scrapers.poll_scraper --season 2024-25

    # Load from local HTML file (to avoid scraping)
    python -m basketball_processor.scrapers.poll_scraper --local polls_2025.html
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Rate limiting: Sports Reference asks for 3+ seconds between requests
REQUEST_DELAY = 3.05  # seconds between requests
USER_AGENT = "Mozilla/5.0 (compatible; CollegeBasketballTracker/1.0)"

# File paths
REFERENCES_DIR = Path(__file__).parent.parent / "references"
POLLS_FILE_MEN = REFERENCES_DIR / "ap_polls.json"
POLLS_FILE_WOMEN = REFERENCES_DIR / "ap_polls_women.json"


def get_polls_file(gender: str = 'M') -> Path:
    """Get the polls JSON file path for the given gender."""
    return POLLS_FILE_WOMEN if gender == 'W' else POLLS_FILE_MEN


def get_season_url(season: str, gender: str = 'M') -> str:
    """Get Sports Reference URL for a season's polls.

    Args:
        season: Season string like '2025-26' or '2026' (end year)
        gender: 'M' for men's, 'W' for women's

    Returns:
        URL string
    """
    # Handle both '2025-26' and '2026' formats
    if '-' in season:
        end_year = int(season.split('-')[0]) + 1
    else:
        end_year = int(season)

    gender_path = "women" if gender == 'W' else "men"
    return f"https://www.sports-reference.com/cbb/seasons/{gender_path}/{end_year}-polls.html"


def parse_poll_table(soup: BeautifulSoup) -> Dict[str, Dict[str, int]]:
    """Parse the AP polls table from the page.

    Returns:
        Dict mapping poll date -> {team_name: rank}
    """
    polls = {}

    # Find the main polls table (ap-polls)
    table = soup.find('table', {'id': 'ap-polls'})
    if not table:
        # Try alternate table ID
        table = soup.find('table', {'id': 'polls'})
    if not table:
        print("Warning: Could not find polls table")
        return polls

    # Get header row to find poll dates
    thead = table.find('thead')
    if not thead:
        return polls

    header_row = thead.find_all('tr')[-1]  # Last header row has dates
    headers = []
    for th in header_row.find_all(['th', 'td']):
        text = th.get_text(strip=True)
        headers.append(text)

    # Find date columns (skip School, Conf)
    date_columns = []
    for i, header in enumerate(headers):
        if header in ['School', 'Conf', 'Rk']:
            continue
        # Convert header to date key
        if header == 'Pre':
            date_columns.append((i, 'preseason'))
        elif '/' in header:
            # Format: 11/10 -> need to add year
            date_columns.append((i, header))
        elif header:
            date_columns.append((i, header))

    # Parse body rows
    tbody = table.find('tbody')
    if not tbody:
        return polls

    for row in tbody.find_all('tr'):
        cells = row.find_all(['th', 'td'])
        if len(cells) < 2:
            continue

        # Get team name from first cell (usually has a link)
        team_cell = cells[0]
        team_link = team_cell.find('a')
        if team_link:
            team_name = team_link.get_text(strip=True)
        else:
            team_name = team_cell.get_text(strip=True)

        if not team_name or team_name == 'School':
            continue

        # Get rankings for each date column
        for col_idx, date_key in date_columns:
            if col_idx >= len(cells):
                continue

            rank_text = cells[col_idx].get_text(strip=True)
            if rank_text and rank_text.isdigit():
                rank = int(rank_text)

                if date_key not in polls:
                    polls[date_key] = {}
                polls[date_key][team_name] = rank

    return polls


def normalize_poll_dates(polls: Dict[str, Dict[str, int]], season: str) -> Dict[str, Dict[str, int]]:
    """Convert poll date keys to ISO format (YYYY-MM-DD).

    Args:
        polls: Raw polls dict with date keys like '11/10' or 'preseason'
        season: Season string like '2025-26'

    Returns:
        Polls dict with ISO date keys
    """
    if '-' in season:
        start_year = int(season.split('-')[0])
    else:
        start_year = int(season) - 1

    normalized = {}

    for date_key, rankings in polls.items():
        if date_key == 'preseason':
            # Preseason is typically early November
            iso_date = f"{start_year}-11-01"
        elif '/' in date_key:
            # Format: MM/DD
            parts = date_key.split('/')
            month = int(parts[0])
            day = int(parts[1])

            # Determine year: Nov-Dec is start_year, Jan-Apr is start_year+1
            if month >= 11:
                year = start_year
            else:
                year = start_year + 1

            iso_date = f"{year}-{month:02d}-{day:02d}"
        else:
            iso_date = date_key

        normalized[iso_date] = rankings

    return normalized


def fetch_polls_from_url(url: str) -> Optional[BeautifulSoup]:
    """Fetch polls page with rate limiting.

    Returns:
        BeautifulSoup object or None if failed
    """
    if not HAS_REQUESTS:
        print("Error: 'requests' library not installed. Use --local option instead.")
        return None

    print(f"Fetching: {url}")
    print(f"(Waiting {REQUEST_DELAY}s to respect rate limits...)")
    time.sleep(REQUEST_DELAY)

    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None


def load_polls_from_file(filepath: Path) -> Optional[BeautifulSoup]:
    """Load polls from local HTML file."""
    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        return None

    print(f"Loading from local file: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return BeautifulSoup(f.read(), 'html.parser')


def load_existing_polls(gender: str = 'M') -> Dict[str, Dict[str, Dict[str, int]]]:
    """Load existing polls data from JSON file."""
    polls_file = get_polls_file(gender)
    if polls_file.exists():
        try:
            with open(polls_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_polls(all_polls: Dict[str, Dict[str, Dict[str, int]]], gender: str = 'M') -> None:
    """Save polls data to JSON file."""
    REFERENCES_DIR.mkdir(parents=True, exist_ok=True)
    polls_file = get_polls_file(gender)
    with open(polls_file, 'w') as f:
        json.dump(all_polls, f, indent=2, sort_keys=True)
    print(f"Saved polls to: {polls_file}")


def scrape_season_polls(season: str, local_file: Optional[Path] = None, gender: str = 'M') -> Dict[str, Dict[str, int]]:
    """Scrape AP polls for a season.

    Args:
        season: Season string like '2025-26'
        local_file: Optional local HTML file to use instead of scraping
        gender: 'M' for men's, 'W' for women's

    Returns:
        Dict mapping ISO date -> {team_name: rank}
    """
    if local_file:
        soup = load_polls_from_file(local_file)
    else:
        url = get_season_url(season, gender)
        soup = fetch_polls_from_url(url)

    if not soup:
        return {}

    raw_polls = parse_poll_table(soup)
    normalized = normalize_poll_dates(raw_polls, season)

    print(f"Parsed {len(normalized)} poll weeks for {season}")
    for date in sorted(normalized.keys()):
        print(f"  {date}: {len(normalized[date])} teams ranked")

    return normalized


def get_team_rank(team_name: str, game_date: str, season: str, gender: str = 'M') -> Optional[int]:
    """Get a team's AP ranking for a specific game date.

    Args:
        team_name: Team name to look up
        game_date: Game date in ISO format (YYYY-MM-DD)
        season: Season string like '2025-26'
        gender: 'M' for men's, 'W' for women's

    Returns:
        Rank (1-25) or None if unranked
    """
    all_polls = load_existing_polls(gender)

    if season not in all_polls:
        return None

    season_polls = all_polls[season]

    # Find the most recent poll before/on the game date
    poll_dates = sorted(season_polls.keys())
    applicable_poll = None

    for poll_date in poll_dates:
        if poll_date <= game_date:
            applicable_poll = poll_date
        else:
            break

    if not applicable_poll:
        return None

    rankings = season_polls[applicable_poll]

    # Try exact match first
    if team_name in rankings:
        return rankings[team_name]

    # Try alias lookup
    try:
        from ..utils.constants import TEAM_ALIASES
        canonical = TEAM_ALIASES.get(team_name, team_name)
        if canonical in rankings:
            return rankings[canonical]

        # Try reverse: maybe the poll uses an alias
        for poll_team, rank in rankings.items():
            poll_canonical = TEAM_ALIASES.get(poll_team, poll_team)
            if poll_canonical == team_name or poll_canonical == canonical:
                return rank
    except ImportError:
        pass

    return None


def get_rankings_for_game(away_team: str, home_team: str, game_date: str, season: str, gender: str = 'M') -> Tuple[Optional[int], Optional[int]]:
    """Get rankings for both teams in a game.

    Returns:
        Tuple of (away_rank, home_rank), None if unranked
    """
    away_rank = get_team_rank(away_team, game_date, season, gender)
    home_rank = get_team_rank(home_team, game_date, season, gender)
    return away_rank, home_rank


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Scrape AP Poll data')
    parser.add_argument('--season', default='2025-26', help='Season to scrape (e.g., 2025-26)')
    parser.add_argument('--local', type=Path, help='Load from local HTML file instead of scraping')
    parser.add_argument('--list', action='store_true', help='List cached seasons')
    parser.add_argument('--gender', choices=['M', 'W'], default='M', help="Gender: M=men's, W=women's")

    args = parser.parse_args()

    gender_label = "Women's" if args.gender == 'W' else "Men's"

    if args.list:
        all_polls = load_existing_polls(args.gender)
        print(f"Cached {gender_label} seasons:")
        for season in sorted(all_polls.keys()):
            weeks = len(all_polls[season])
            print(f"  {season}: {weeks} poll weeks")
        return

    # Load existing data
    all_polls = load_existing_polls(args.gender)

    # Scrape the requested season
    season_polls = scrape_season_polls(args.season, args.local, args.gender)

    if season_polls:
        all_polls[args.season] = season_polls
        save_polls(all_polls, args.gender)
        print(f"\nSuccessfully updated {gender_label} {args.season} poll data")
    else:
        print(f"\nNo poll data found for {gender_label} {args.season}")


if __name__ == '__main__':
    main()
