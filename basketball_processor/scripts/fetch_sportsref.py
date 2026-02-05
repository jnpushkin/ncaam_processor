#!/usr/bin/env python3
"""
Fetch Sports Reference box scores for pending games.

This script:
1. Loads the pending games queue
2. Attempts to download Sports Reference HTML for each game
3. Saves successful downloads to html_games/ directory
4. Updates the pending queue status

Usage:
    python -m basketball_processor.scripts.fetch_sportsref [--all] [--game-id <id>]

Examples:
    python -m basketball_processor.scripts.fetch_sportsref
    python -m basketball_processor.scripts.fetch_sportsref --all
    python -m basketball_processor.scripts.fetch_sportsref --game-id 401829228
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Paths
PENDING_GAMES_FILE = Path(__file__).parent.parent.parent / "data" / "pending_games.json"
HTML_GAMES_DIR = Path(__file__).parent.parent.parent / "html_games"

# Sports Reference URL pattern
SPORTSREF_BASE = "https://www.sports-reference.com/cbb/boxscores"

# Team name to Sports Reference slug mapping
# This maps common team names to their SR slugs
TEAM_SLUG_MAP = {
    # WCC
    "San Francisco": "san-francisco",
    "Loyola Marymount": "loyola-marymount",
    "Gonzaga": "gonzaga",
    "Saint Mary's": "saint-marys-ca",
    "Santa Clara": "santa-clara",
    "BYU": "brigham-young",
    "Pacific": "pacific",
    "Pepperdine": "pepperdine",
    "Portland": "portland",
    "San Diego": "san-diego",

    # Pac-12 / Big Ten / etc
    "California": "california",
    "Stanford": "stanford",
    "UCLA": "ucla",
    "USC": "southern-california",
    "Oregon": "oregon",
    "Oregon State": "oregon-state",
    "Washington": "washington",
    "Washington State": "washington-state",
    "Arizona": "arizona",
    "Arizona State": "arizona-state",
    "Colorado": "colorado",
    "Utah": "utah",

    # ACC
    "Virginia": "virginia",
    "Duke": "duke",
    "North Carolina": "north-carolina",
    "NC State": "north-carolina-state",
    "Wake Forest": "wake-forest",
    "Clemson": "clemson",
    "Florida State": "florida-state",
    "Georgia Tech": "georgia-tech",
    "Louisville": "louisville",
    "Miami": "miami-fl",
    "Notre Dame": "notre-dame",
    "Pittsburgh": "pittsburgh",
    "Syracuse": "syracuse",
    "Boston College": "boston-college",
    "Virginia Tech": "virginia-tech",

    # Big 12
    "Kansas": "kansas",
    "Kansas State": "kansas-state",
    "Baylor": "baylor",
    "Texas": "texas",
    "Texas Tech": "texas-tech",
    "TCU": "texas-christian",
    "Oklahoma": "oklahoma",
    "Oklahoma State": "oklahoma-state",
    "Iowa State": "iowa-state",
    "West Virginia": "west-virginia",
    "Cincinnati": "cincinnati",
    "Houston": "houston",
    "UCF": "central-florida",
    "BYU": "brigham-young",

    # SEC
    "Kentucky": "kentucky",
    "Tennessee": "tennessee",
    "Alabama": "alabama",
    "Auburn": "auburn",
    "Florida": "florida",
    "Georgia": "georgia",
    "South Carolina": "south-carolina",
    "Vanderbilt": "vanderbilt",
    "Arkansas": "arkansas",
    "LSU": "louisiana-state",
    "Mississippi State": "mississippi-state",
    "Ole Miss": "mississippi",
    "Missouri": "missouri",
    "Texas A&M": "texas-am",

    # Big East
    "UConn": "connecticut",
    "Connecticut": "connecticut",
    "Villanova": "villanova",
    "Creighton": "creighton",
    "Marquette": "marquette",
    "Xavier": "xavier",
    "Butler": "butler",
    "Providence": "providence",
    "Seton Hall": "seton-hall",
    "St. John's": "st-johns-ny",
    "Georgetown": "georgetown",
    "DePaul": "depaul",

    # Big Ten
    "Michigan": "michigan",
    "Michigan State": "michigan-state",
    "Ohio State": "ohio-state",
    "Indiana": "indiana",
    "Purdue": "purdue",
    "Illinois": "illinois",
    "Iowa": "iowa",
    "Wisconsin": "wisconsin",
    "Minnesota": "minnesota",
    "Nebraska": "nebraska",
    "Northwestern": "northwestern",
    "Penn State": "penn-state",
    "Maryland": "maryland",
    "Rutgers": "rutgers",

    # Mountain West
    "San Diego State": "san-diego-state",
    "Nevada": "nevada",
    "UNLV": "nevada-las-vegas",
    "Boise State": "boise-state",
    "New Mexico": "new-mexico",
    "Colorado State": "colorado-state",
    "Fresno State": "fresno-state",
    "Wyoming": "wyoming",
    "Air Force": "air-force",
    "Utah State": "utah-state",
    "San Jose State": "san-jose-state",
}


def get_team_slug(team_name: str) -> Optional[str]:
    """
    Convert team name to Sports Reference slug.

    Args:
        team_name: Full team name (e.g., "San Francisco")

    Returns:
        SR slug (e.g., "san-francisco") or None if not found
    """
    # Check exact match first
    if team_name in TEAM_SLUG_MAP:
        return TEAM_SLUG_MAP[team_name]

    # Try case-insensitive match
    for name, slug in TEAM_SLUG_MAP.items():
        if name.lower() == team_name.lower():
            return slug

    # Try to generate slug from name
    # This is a fallback and may not always work
    slug = team_name.lower()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)

    return slug


def find_sportsref_url(date_yyyymmdd: str, home_team: str, away_team: str) -> Tuple[bool, Optional[str]]:
    """
    Find the Sports Reference box score URL by searching the team's schedule.

    Sports Reference URLs can have sequence numbers (e.g., 2026-02-04-22-san-francisco.html)
    when multiple games occur. We search the team schedule page to find the correct URL.

    Args:
        date_yyyymmdd: Date in YYYYMMDD format
        home_team: Home team name
        away_team: Away team name

    Returns:
        Tuple of (success, url or error_message)
    """
    slug = get_team_slug(home_team)
    if not slug:
        return False, f"No slug mapping for team: {home_team}"

    # Format date for matching
    formatted_date = f"{date_yyyymmdd[:4]}-{date_yyyymmdd[4:6]}-{date_yyyymmdd[6:8]}"

    # Also try the previous day (ESPN uses UTC, game might be previous local date)
    from datetime import datetime, timedelta
    game_date = datetime.strptime(date_yyyymmdd, "%Y%m%d")
    prev_date = (game_date - timedelta(days=1)).strftime("%Y-%m-%d")

    # First, try the simple URL without sequence number (most common case)
    simple_url = f"{SPORTSREF_BASE}/{formatted_date}-{slug}.html"
    success, _ = fetch_sportsref_page(simple_url)
    if success:
        return True, simple_url

    # Also try previous day
    prev_url = f"{SPORTSREF_BASE}/{prev_date}-{slug}.html"
    success, _ = fetch_sportsref_page(prev_url)
    if success:
        return True, prev_url

    # If simple URL fails, search the team's schedule page for the correct URL
    year = date_yyyymmdd[:4]
    schedule_url = f"https://www.sports-reference.com/cbb/schools/{slug}/men/{year}-schedule.html"

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(schedule_url, headers=headers, timeout=30)

        if response.status_code != 200:
            return False, f"Could not fetch schedule page: HTTP {response.status_code}"

        # Look for box score links matching the date
        # Pattern: /cbb/boxscores/YYYY-MM-DD[-NN]-slug.html
        import re

        # Try both the expected date and previous day
        for date_to_match in [formatted_date, prev_date]:
            pattern = rf'/cbb/boxscores/({date_to_match}(?:-\d+)?-{re.escape(slug)}\.html)'
            matches = re.findall(pattern, response.text)

            if matches:
                # Return the first matching URL
                box_url = f"https://www.sports-reference.com/cbb/boxscores/{matches[0]}"
                return True, box_url

        return False, f"No box score found in schedule for {formatted_date} or {prev_date}"

    except requests.exceptions.RequestException as e:
        return False, f"Error fetching schedule: {str(e)}"


def build_sportsref_url(date_yyyymmdd: str, home_team: str) -> Optional[str]:
    """
    Build Sports Reference box score URL (simple version without sequence number).
    Used as fallback. Prefer find_sportsref_url() for accurate URL discovery.

    Args:
        date_yyyymmdd: Date in YYYYMMDD format
        home_team: Home team name

    Returns:
        Full SR URL or None if can't build
    """
    slug = get_team_slug(home_team)
    if not slug:
        return None

    # Format date as YYYY-MM-DD
    formatted_date = f"{date_yyyymmdd[:4]}-{date_yyyymmdd[4:6]}-{date_yyyymmdd[6:8]}"

    return f"{SPORTSREF_BASE}/{formatted_date}-{slug}.html"


def fetch_sportsref_page(url: str) -> Tuple[bool, Optional[str]]:
    """
    Attempt to fetch a Sports Reference page.

    Args:
        url: Full SR URL

    Returns:
        Tuple of (success, html_content or error_message)
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code == 200:
            # Check if it's actually a box score page (not a 404 page)
            if "Box Score" in response.text or "box-score" in response.text:
                return True, response.text
            else:
                return False, "Page exists but doesn't appear to be a box score"

        elif response.status_code == 404:
            return False, "Page not found (404) - may not be available yet"
        else:
            return False, f"HTTP {response.status_code}"

    except requests.exceptions.RequestException as e:
        return False, str(e)


def load_pending_games() -> dict:
    """Load the pending games queue."""
    if PENDING_GAMES_FILE.exists():
        with open(PENDING_GAMES_FILE, 'r') as f:
            return json.load(f)
    return {"games": []}


def save_pending_games(data: dict):
    """Save the pending games queue."""
    with open(PENDING_GAMES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def cleanup_scheduled_job():
    """Remove the launchd job after fetch completes."""
    plist_path = Path.home() / "Library" / "LaunchAgents" / "com.ncaam.sportsref-fetch.plist"
    if plist_path.exists():
        try:
            subprocess.run(["launchctl", "unload", str(plist_path)],
                          capture_output=True, check=False)
            plist_path.unlink()
            print("Cleaned up scheduled job.")
        except Exception as e:
            print(f"Note: Could not clean up scheduled job: {e}")


def fetch_pending_games(fetch_all: bool = False, specific_game_id: Optional[str] = None):
    """
    Fetch Sports Reference pages for pending games.

    Args:
        fetch_all: If True, retry even previously failed games
        specific_game_id: If set, only fetch this specific game
    """
    pending = load_pending_games()
    games = pending.get("games", [])

    if not games:
        print("No pending games in queue.")
        print("Add games with: python -m basketball_processor.scripts.add_espn_game <espn_url>")
        return

    HTML_GAMES_DIR.mkdir(parents=True, exist_ok=True)

    fetched = 0
    skipped = 0
    failed = 0

    for game in games:
        espn_id = game.get("espn_game_id")

        # Filter by specific game if requested
        if specific_game_id and espn_id != specific_game_id:
            continue

        # Skip already fetched unless --all
        if game.get("sportsref_fetched") and not fetch_all:
            skipped += 1
            continue

        home_team = game.get("home_team")
        away_team = game.get("away_team")
        date_yyyymmdd = game.get("date_yyyymmdd")
        gender = game.get("gender", "M")

        print(f"\n{away_team} @ {home_team} ({game.get('date')})")

        # Find the correct SR URL (handles sequence numbers and date offsets)
        print(f"  Searching for box score...")
        url_found, sr_url_or_error = find_sportsref_url(date_yyyymmdd, home_team, away_team)

        if not url_found:
            print(f"  {sr_url_or_error}")
            failed += 1
            continue

        sr_url = sr_url_or_error
        print(f"  Found: {sr_url}")

        # Fetch the page
        success, result = fetch_sportsref_page(sr_url)

        if success:
            # Save the HTML
            gender_suffix = "_w" if gender == "W" else ""
            filename = f"{date_yyyymmdd}_{home_team.lower().replace(' ', '_')}{gender_suffix}.html"
            filepath = HTML_GAMES_DIR / filename

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(result)

            print(f"  SUCCESS! Saved to: {filepath}")

            # Update pending entry
            game["sportsref_fetched"] = True
            game["sportsref_url"] = sr_url
            game["sportsref_file"] = str(filepath)
            game["fetched_at"] = datetime.now().isoformat()

            fetched += 1
        else:
            print(f"  Failed: {result}")
            failed += 1

        # Rate limit to be nice to SR
        time.sleep(2)

    # Save updated pending queue
    save_pending_games(pending)

    print(f"\n--- Summary ---")
    print(f"Fetched: {fetched}")
    print(f"Skipped (already done): {skipped}")
    print(f"Failed: {failed}")

    # Check if all pending games are now fetched
    pending = load_pending_games()
    unfetched = [g for g in pending.get("games", []) if not g.get("sportsref_fetched")]
    if not unfetched:
        cleanup_scheduled_job()
    elif failed > 0:
        print(f"\n{len(unfetched)} game(s) still pending - will retry on next scheduled run")

    if fetched > 0:
        print(f"\nNext step: Run the processor to include new games:")
        print(f"  python -m basketball_processor")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Sports Reference box scores for pending games",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s                      # Fetch pending games not yet attempted
    %(prog)s --all                # Retry all pending games
    %(prog)s --game-id 401829228  # Fetch specific game
        """
    )
    parser.add_argument("--all", "-a", action="store_true",
                        help="Retry all pending games, even previously failed")
    parser.add_argument("--game-id", "-g", help="Fetch specific ESPN game ID only")

    args = parser.parse_args()

    fetch_pending_games(fetch_all=args.all, specific_game_id=args.game_id)


if __name__ == "__main__":
    main()
