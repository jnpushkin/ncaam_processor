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
import sys
from datetime import datetime
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
        print("\nDone!")

        # Show next steps
        print("\nNext steps:")
        print("  1. Sports Reference box score usually available next day")
        print("  2. Run: python -m basketball_processor.scripts.fetch_sportsref")
        print("     to download when available")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
