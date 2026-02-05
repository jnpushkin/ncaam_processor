#!/usr/bin/env python3
"""
Add a game from ESPN URL/ID.

This script:
1. Fetches game data from ESPN's API
2. Saves it to the pending games queue
3. Optionally processes it immediately into the main data

Usage:
    python -m basketball_processor.scripts.add_espn_game <espn_url_or_id> [--process]

Examples:
    python -m basketball_processor.scripts.add_espn_game https://www.espn.com/mens-college-basketball/boxscore/_/gameId/401829228
    python -m basketball_processor.scripts.add_espn_game 401829228 --process
"""

import argparse
import json
import os
import plistlib
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from basketball_processor.utils.espn_boxscore import get_espn_game, extract_game_id

# Paths
PENDING_GAMES_FILE = Path(__file__).parent.parent.parent / "data" / "pending_games.json"
ESPN_CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "espn_cache"


def load_pending_games() -> dict:
    """Load the pending games queue."""
    if PENDING_GAMES_FILE.exists():
        with open(PENDING_GAMES_FILE, 'r') as f:
            return json.load(f)
    return {"games": []}


def save_pending_games(data: dict):
    """Save the pending games queue."""
    PENDING_GAMES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PENDING_GAMES_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def schedule_sportsref_fetch():
    """
    Schedule a one-time Sports Reference fetch for tomorrow at 10 AM.
    Uses launchd on macOS.
    """
    plist_dir = Path.home() / "Library" / "LaunchAgents"
    plist_path = plist_dir / "com.ncaam.sportsref-fetch.plist"

    # Calculate tomorrow at 10 AM
    now = datetime.now()
    tomorrow_10am = (now + timedelta(days=1)).replace(hour=10, minute=0, second=0, microsecond=0)

    # If it's before 10 AM today, schedule for today instead
    today_10am = now.replace(hour=10, minute=0, second=0, microsecond=0)
    if now < today_10am:
        target_time = today_10am
    else:
        target_time = tomorrow_10am

    project_dir = Path(__file__).parent.parent.parent.resolve()
    log_file = project_dir / "logs" / "sportsref_fetch.log"

    plist_content = {
        "Label": "com.ncaam.sportsref-fetch",
        "ProgramArguments": [
            "/usr/bin/python3",
            "-m", "basketball_processor.scripts.fetch_sportsref"
        ],
        "WorkingDirectory": str(project_dir),
        "StartCalendarInterval": {
            "Hour": target_time.hour,
            "Minute": target_time.minute,
            "Day": target_time.day,
            "Month": target_time.month,
        },
        "StandardOutPath": str(log_file),
        "StandardErrorPath": str(log_file),
        "RunAtLoad": False,
    }

    # Ensure directories exist
    plist_dir.mkdir(parents=True, exist_ok=True)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Unload existing job if present
    try:
        subprocess.run(["launchctl", "unload", str(plist_path)],
                      capture_output=True, check=False)
    except:
        pass

    # Write plist
    with open(plist_path, 'wb') as f:
        plistlib.dump(plist_content, f)

    # Load the job
    result = subprocess.run(["launchctl", "load", str(plist_path)],
                           capture_output=True, text=True)

    if result.returncode == 0:
        print(f"\n  Scheduled Sports Reference fetch for {target_time.strftime('%Y-%m-%d %H:%M')}")
        return True
    else:
        print(f"\n  Note: Could not schedule auto-fetch: {result.stderr}")
        return False


def add_game(url_or_id: str, process_now: bool = False) -> dict:
    """
    Add a game from ESPN.

    Args:
        url_or_id: ESPN URL or game ID
        process_now: If True, immediately process into main data

    Returns:
        The game data
    """
    print(f"Fetching game from ESPN: {url_or_id}")

    # Extract game ID
    game_id, league = extract_game_id(url_or_id)
    print(f"  Game ID: {game_id}")
    print(f"  League: {league}")

    # Fetch and parse game data
    game_data = get_espn_game(url_or_id)

    basic = game_data.get("basic_info", {})
    print(f"\n  {basic.get('away_team')} {basic.get('away_score')} @ {basic.get('home_team')} {basic.get('home_score')}")
    print(f"  Date: {basic.get('date')}")
    print(f"  Venue: {basic.get('venue')}")

    # Cache the ESPN data
    ESPN_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = ESPN_CACHE_DIR / f"{game_id}.json"
    with open(cache_file, 'w') as f:
        json.dump(game_data, f, indent=2)
    print(f"\n  Cached to: {cache_file}")

    # Add to pending games queue for Sports Reference fetch
    pending = load_pending_games()

    # Check if already in queue
    existing = next((g for g in pending["games"] if g.get("espn_game_id") == game_id), None)

    game_entry = {
        "espn_game_id": game_id,
        "espn_url": f"https://www.espn.com/{'womens' if 'womens' in league else 'mens'}-college-basketball/boxscore/_/gameId/{game_id}",
        "away_team": basic.get("away_team"),
        "home_team": basic.get("home_team"),
        "date": basic.get("date"),
        "date_yyyymmdd": basic.get("date_yyyymmdd"),
        "gender": basic.get("gender", "M"),
        "added_at": datetime.now().isoformat(),
        "sportsref_fetched": False,
        "sportsref_url": None,
        "processed": process_now
    }

    if existing:
        # Update existing entry
        idx = pending["games"].index(existing)
        pending["games"][idx] = game_entry
        print("  Updated existing entry in pending queue")
    else:
        pending["games"].append(game_entry)
        print("  Added to pending queue for Sports Reference fetch")

    save_pending_games(pending)

    if process_now:
        print("\n  Processing game into main data...")
        # TODO: Integrate with main processor
        print("  (Full processing not yet implemented - ESPN data cached)")

    return game_data


def main():
    parser = argparse.ArgumentParser(
        description="Add a game from ESPN URL or game ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s https://www.espn.com/mens-college-basketball/boxscore/_/gameId/401829228
    %(prog)s 401829228 --process
    %(prog)s https://www.espn.com/womens-college-basketball/boxscore/_/gameId/401729001
        """
    )
    parser.add_argument("url_or_id", help="ESPN URL or game ID")
    parser.add_argument("--process", "-p", action="store_true",
                        help="Process game immediately into main data")

    args = parser.parse_args()

    try:
        game_data = add_game(args.url_or_id, args.process)

        # Schedule automatic fetch
        schedule_sportsref_fetch()

        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
