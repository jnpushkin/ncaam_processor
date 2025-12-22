"""
Game box score scraper for college basketball.

Downloads HTML box scores from Sports Reference with rate limiting.

Usage:
    # Download games for a specific team and season
    python -m basketball_processor.scrapers.game_scraper --team virginia --season 2024-25

    # Download games for a date range
    python -m basketball_processor.scrapers.game_scraper --team virginia --start 2025-01-01 --end 2025-01-31

    # Download a specific game by URL
    python -m basketball_processor.scrapers.game_scraper --url "https://www.sports-reference.com/cbb/boxscores/..."

    # Sync recent games for tracked teams (downloads games from last N days)
    python -m basketball_processor.scrapers.game_scraper --sync --days 7

    # Add a team to tracked teams
    python -m basketball_processor.scrapers.game_scraper --track san-francisco

    # List tracked teams
    python -m basketball_processor.scrapers.game_scraper --list-tracked
"""

import json
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin

try:
    import requests
    from bs4 import BeautifulSoup
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Rate limiting: Sports Reference asks for 3+ seconds between requests
REQUEST_DELAY = 3.05
USER_AGENT = "Mozilla/5.0 (compatible; CollegeBasketballTracker/1.0)"

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent.parent / "html_games"

# Config file for tracked teams
CONFIG_DIR = Path(__file__).parent.parent / "references"
TRACKED_TEAMS_FILE = CONFIG_DIR / "tracked_teams.json"


def load_tracked_teams() -> Dict:
    """Load tracked teams configuration."""
    if TRACKED_TEAMS_FILE.exists():
        try:
            with open(TRACKED_TEAMS_FILE, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {"teams": [], "last_sync": None}


def save_tracked_teams(config: Dict):
    """Save tracked teams configuration."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(TRACKED_TEAMS_FILE, 'w') as f:
        json.dump(config, f, indent=2)


def add_tracked_team(team_slug: str, gender: str = 'M'):
    """Add a team to the tracked list."""
    config = load_tracked_teams()
    team_entry = {"slug": team_slug, "gender": gender}

    # Check if already tracked
    for existing in config["teams"]:
        if existing["slug"] == team_slug and existing.get("gender", "M") == gender:
            print(f"Team '{team_slug}' ({gender}) is already tracked")
            return

    config["teams"].append(team_entry)
    save_tracked_teams(config)
    print(f"Added '{team_slug}' ({gender}) to tracked teams")


def remove_tracked_team(team_slug: str, gender: str = 'M'):
    """Remove a team from the tracked list."""
    config = load_tracked_teams()
    original_count = len(config["teams"])

    config["teams"] = [t for t in config["teams"]
                       if not (t["slug"] == team_slug and t.get("gender", "M") == gender)]

    if len(config["teams"]) < original_count:
        save_tracked_teams(config)
        print(f"Removed '{team_slug}' ({gender}) from tracked teams")
    else:
        print(f"Team '{team_slug}' ({gender}) was not in tracked list")


def list_tracked_teams():
    """List all tracked teams."""
    config = load_tracked_teams()
    if not config["teams"]:
        print("No tracked teams. Add teams with: --track <team-slug>")
        return

    print("Tracked teams:")
    for team in config["teams"]:
        gender = team.get("gender", "M")
        gender_label = "Women's" if gender == "W" else "Men's"
        print(f"  {team['slug']} ({gender_label})")

    if config.get("last_sync"):
        print(f"\nLast sync: {config['last_sync']}")


def fetch_page(url: str) -> Optional[str]:
    """Fetch a page with rate limiting."""
    if not HAS_REQUESTS:
        print("Error: 'requests' library not installed.")
        return None

    print(f"Fetching: {url}")
    print(f"(Waiting {REQUEST_DELAY}s to respect rate limits...)")
    time.sleep(REQUEST_DELAY)

    try:
        headers = {'User-Agent': USER_AGENT}
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching URL: {e}")
        return None


def get_team_schedule_url(team_slug: str, season: str, gender: str = 'M') -> str:
    """Get URL for a team's schedule page.

    Args:
        team_slug: Team slug like 'virginia', 'duke', 'north-carolina'
        season: Season like '2024-25'
        gender: 'M' for men's, 'W' for women's
    """
    if '-' in season:
        end_year = int(season.split('-')[0]) + 1
    else:
        end_year = int(season)

    gender_path = "women" if gender == 'W' else "men"
    # Note: team path format varies - most are lowercase with hyphens
    return f"https://www.sports-reference.com/cbb/schools/{team_slug}/{gender_path}/{end_year}-schedule.html"


def extract_boxscore_urls(schedule_html: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[str]:
    """Extract box score URLs from a team's schedule page.

    Args:
        schedule_html: HTML content of schedule page
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    """
    soup = BeautifulSoup(schedule_html, 'html.parser')
    boxscore_urls = []

    # Find schedule table
    table = soup.find('table', {'id': 'schedule'})
    if not table:
        print("Warning: Could not find schedule table")
        return boxscore_urls

    tbody = table.find('tbody')
    if not tbody:
        return boxscore_urls

    # Parse rows to get dates and box score links
    for row in tbody.find_all('tr'):
        # Get date from date column
        date_cell = row.find('td', {'data-stat': 'date_game'})
        if not date_cell:
            continue

        game_date = date_cell.get_text(strip=True)
        # Convert "Nov 11, 2024" to "2024-11-11"
        try:
            parsed_date = datetime.strptime(game_date, "%b %d, %Y")
            iso_date = parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue

        # Apply date filters
        if start_date and iso_date < start_date:
            continue
        if end_date and iso_date > end_date:
            continue

        # Find box score link in this row
        for link in row.find_all('a', href=True):
            href = link['href']
            if '/boxscores/' in href and href.endswith('.html'):
                full_url = urljoin('https://www.sports-reference.com', href)
                if full_url not in boxscore_urls:
                    boxscore_urls.append(full_url)
                break

    return boxscore_urls


def url_to_filename(url: str) -> str:
    """Convert a box score URL to a safe filename."""
    # Extract the path part
    # URL like: https://www.sports-reference.com/cbb/boxscores/2025-01-22-virginia.html
    match = re.search(r'/boxscores/(.+)\.html', url)
    if match:
        base = match.group(1)
        return f"{base}.html"
    return "unknown_game.html"


def download_boxscore(url: str, output_dir: Path) -> Optional[Path]:
    """Download a single box score HTML file."""
    html = fetch_page(url)
    if not html:
        return None

    # Parse to get a better filename from the page title
    soup = BeautifulSoup(html, 'html.parser')
    title = soup.find('title')
    if title:
        title_text = title.get_text()
        # Clean up title for filename
        # "Duke vs. Virginia Box Score, February 9, 2019 | College Basketball..."
        safe_title = re.sub(r'[<>:"/\\|?*]', '', title_text)
        safe_title = safe_title.split('|')[0].strip()
        safe_title = safe_title.replace(' ', '_')
        filename = f"{safe_title}.html"
    else:
        filename = url_to_filename(url)

    output_path = output_dir / filename

    # Don't overwrite existing files
    if output_path.exists():
        print(f"  Already exists: {filename}")
        return output_path

    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"  Saved: {filename}")
    return output_path


def scrape_team_games(team_slug: str, season: str, gender: str = 'M',
                      start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Path]:
    """Scrape box scores for a team's season, optionally filtered by date range."""
    schedule_url = get_team_schedule_url(team_slug, season, gender)

    schedule_html = fetch_page(schedule_url)
    if not schedule_html:
        print(f"Failed to fetch schedule for {team_slug}")
        return []

    boxscore_urls = extract_boxscore_urls(schedule_html, start_date, end_date)
    date_range = ""
    if start_date or end_date:
        date_range = f" ({start_date or 'start'} to {end_date or 'end'})"
    print(f"Found {len(boxscore_urls)} games for {team_slug} {season}{date_range}")

    downloaded = []
    for i, url in enumerate(boxscore_urls, 1):
        print(f"\n[{i}/{len(boxscore_urls)}] ", end="")
        path = download_boxscore(url, OUTPUT_DIR)
        if path:
            downloaded.append(path)

    return downloaded


def get_current_season() -> str:
    """Get the current basketball season string."""
    today = datetime.now()
    if today.month >= 11:
        return f"{today.year}-{str(today.year + 1)[-2:]}"
    else:
        return f"{today.year - 1}-{str(today.year)[-2:]}"


def sync_tracked_teams(days: int = 7) -> List[Path]:
    """Sync recent games for all tracked teams.

    Downloads games from the last N days for all tracked teams.
    """
    config = load_tracked_teams()
    if not config["teams"]:
        print("No tracked teams. Add teams with: --track <team-slug>")
        return []

    today = datetime.now()
    start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    season = get_current_season()

    print(f"Syncing games from {start_date} to {end_date}")
    print(f"Season: {season}")
    print(f"Tracked teams: {len(config['teams'])}")

    all_downloaded = []

    for team in config["teams"]:
        slug = team["slug"]
        gender = team.get("gender", "M")
        print(f"\n=== {slug} ({gender}) ===")

        downloaded = scrape_team_games(
            slug, season, gender,
            start_date=start_date, end_date=end_date
        )
        all_downloaded.extend(downloaded)

    # Update last sync time
    config["last_sync"] = today.strftime("%Y-%m-%d %H:%M")
    save_tracked_teams(config)

    return all_downloaded


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Download game box scores from Sports Reference')

    # Team-specific options
    parser.add_argument('--team', help='Team slug (e.g., virginia, duke, north-carolina)')
    parser.add_argument('--season', default=None, help='Season (e.g., 2024-25). Defaults to current season.')
    parser.add_argument('--gender', choices=['M', 'W'], default='M', help="Gender: M=men's, W=women's")
    parser.add_argument('--start', help='Start date filter (YYYY-MM-DD)')
    parser.add_argument('--end', help='End date filter (YYYY-MM-DD)')

    # Direct URL download
    parser.add_argument('--url', help='Download a specific box score URL')

    # Tracked teams management
    parser.add_argument('--track', metavar='TEAM', help='Add a team to tracked list')
    parser.add_argument('--untrack', metavar='TEAM', help='Remove a team from tracked list')
    parser.add_argument('--list-tracked', action='store_true', help='List tracked teams')

    # Sync functionality
    parser.add_argument('--sync', action='store_true', help='Sync recent games for tracked teams')
    parser.add_argument('--days', type=int, default=7, help='Number of days to look back when syncing (default: 7)')

    parser.add_argument('--output', type=Path, default=OUTPUT_DIR, help='Output directory')

    args = parser.parse_args()

    # Handle tracked teams management
    if args.list_tracked:
        list_tracked_teams()
        return

    if args.track:
        add_tracked_team(args.track, args.gender)
        return

    if args.untrack:
        remove_tracked_team(args.untrack, args.gender)
        return

    # Handle sync
    if args.sync:
        downloaded = sync_tracked_teams(args.days)
        print(f"\n=== Sync complete: {len(downloaded)} games downloaded ===")
        return

    # Handle URL download
    if args.url:
        download_boxscore(args.url, args.output)
        return

    # Handle team download
    if args.team:
        season = args.season or get_current_season()
        downloaded = scrape_team_games(
            args.team, season, args.gender,
            start_date=args.start, end_date=args.end
        )
        print(f"\n=== Downloaded {len(downloaded)} games ===")
        return

    # No action specified - show help
    parser.print_help()
    print("\nExamples:")
    print("  # Add teams to track:")
    print("  python -m basketball_processor.scrapers.game_scraper --track san-francisco")
    print("  python -m basketball_processor.scrapers.game_scraper --track virginia")
    print("")
    print("  # Sync recent games for tracked teams (last 7 days):")
    print("  python -m basketball_processor.scrapers.game_scraper --sync")
    print("")
    print("  # Sync games from last 2 days only:")
    print("  python -m basketball_processor.scrapers.game_scraper --sync --days 2")
    print("")
    print("  # Download all Virginia games for current season:")
    print("  python -m basketball_processor.scrapers.game_scraper --team virginia")
    print("")
    print("  # Download a specific game by URL:")
    print("  python -m basketball_processor.scrapers.game_scraper --url 'https://www.sports-reference.com/cbb/boxscores/...'")


if __name__ == '__main__':
    main()
