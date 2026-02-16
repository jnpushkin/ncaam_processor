"""
Main entry point for the College Basketball Stats Processor.
"""

import os
import sys
import json
import argparse
import traceback
import re
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from .excel.workbook_generator import generate_excel_workbook
from .parsers.html_parser import parse_sports_reference_boxscore, HTMLParsingError
from .parsers.sidearm_parser import parse_sidearm_boxscore, is_sidearm_format, SidearmParsingError
from .utils.constants import BASE_DIR, DEFAULT_INPUT_DIR, CACHE_DIR, DEFAULT_HTML_OUTPUT, SURGE_DOMAIN
from .utils.log import info, warn, error, success, debug, set_verbosity, set_use_emoji
from .website import generate_website_from_data
from .engines.milestone_engine import MilestoneEngine

# ESPN cache directory
ESPN_CACHE_DIR = BASE_DIR / "data" / "espn_cache"


def load_espn_cached_games(existing_game_ids: set) -> List[Dict[str, Any]]:
    """
    Load games from ESPN cache that don't already have Sports Reference data.

    Args:
        existing_game_ids: Set of game IDs already loaded from SR HTML files

    Returns:
        List of ESPN game data dictionaries
    """
    espn_games = []

    if not ESPN_CACHE_DIR.exists():
        return espn_games

    # Load pending games to check which ESPN games have SR data fetched
    pending_file = BASE_DIR / "data" / "pending_games.json"
    sr_fetched_espn_ids = set()
    if pending_file.exists():
        try:
            with open(pending_file, 'r') as f:
                pending_data = json.load(f)
            for game in pending_data.get("games", []):
                if game.get("sportsref_fetched"):
                    sr_fetched_espn_ids.add(game.get("espn_game_id"))
        except Exception:
            pass

    for cache_file in ESPN_CACHE_DIR.glob("*.json"):
        try:
            # ESPN game ID is the filename without extension
            espn_game_id = cache_file.stem

            # Skip if SR data has been fetched for this ESPN game
            if espn_game_id in sr_fetched_espn_ids:
                debug(f"  Skipping ESPN game {espn_game_id} - SR data fetched")
                continue

            with open(cache_file, 'r') as f:
                game_data = json.load(f)

            basic_info = game_data.get('basic_info', {})
            date_yyyymmdd = basic_info.get('date_yyyymmdd', '')
            home_team = basic_info.get('home_team', '')

            # Create a comparable game ID
            home_slug = home_team.lower().replace(' ', '-').replace("'", '').replace('.', '')
            game_id = f"{date_yyyymmdd}-{home_slug}"

            # Skip if we already have this game from Sports Reference (by date/team match)
            if game_id in existing_game_ids:
                debug(f"  Skipping ESPN game {game_id} - already have SR data")
                continue

            # Mark as ESPN source
            game_data['_source'] = 'espn'
            game_data['basic_info']['source'] = 'espn'

            # Ensure milestone_stats exists
            if 'milestone_stats' not in game_data:
                game_data['milestone_stats'] = {}

            # Run milestone detection on ESPN data
            milestone_engine = MilestoneEngine(game_data)
            game_data = milestone_engine.process()

            espn_games.append(game_data)
            info(f"  Added ESPN game: {basic_info.get('away_team')} @ {home_team}")

        except Exception as e:
            warn(f"Failed to load ESPN cache {cache_file}: {e}")

    return espn_games


def enrich_game_with_rankings(game_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add AP rankings to game data if poll data is available.

    Rankings are stored in basic_info as 'away_rank' and 'home_rank'.
    """
    try:
        from .scrapers.poll_scraper import get_rankings_for_game, load_existing_polls
        gender = game_data.get('basic_info', {}).get('gender', 'M')
        polls_data = load_existing_polls(gender=gender)
        if not polls_data:
            return game_data
    except ImportError:
        return game_data

    basic_info = game_data.get('basic_info', {})
    date_yyyymmdd = basic_info.get('date_yyyymmdd', '')
    away_team = basic_info.get('away_team', '')
    home_team = basic_info.get('home_team', '')

    if not (date_yyyymmdd and away_team and home_team):
        return game_data

    # Convert YYYYMMDD to ISO format
    if len(date_yyyymmdd) == 8:
        game_date_iso = f"{date_yyyymmdd[:4]}-{date_yyyymmdd[4:6]}-{date_yyyymmdd[6:8]}"

        # Determine season (Nov-Apr spans two calendar years)
        month = int(date_yyyymmdd[4:6])
        year = int(date_yyyymmdd[:4])
        if month >= 11:
            season = f"{year}-{str(year + 1)[-2:]}"
        else:
            season = f"{year - 1}-{str(year)[-2:]}"

        away_rank, home_rank = get_rankings_for_game(
            away_team, home_team, game_date_iso, season, gender=gender
        )

        if away_rank:
            game_data['basic_info']['away_rank'] = away_rank
            info(f"    #{away_rank} {away_team}")
        if home_rank:
            game_data['basic_info']['home_rank'] = home_rank
            info(f"    #{home_rank} {home_team}")

    return game_data


def process_html_file(
    file_path: str,
    index: Optional[int] = None,
    total: Optional[int] = None,
    gender: str = 'M'
) -> Dict[str, Any]:
    """
    Process a single Sports Reference HTML file, with filename-based caching.

    Args:
        file_path: Path to HTML file
        index: Current file index (for progress display)
        total: Total files (for progress display)
        gender: 'M' for men's, 'W' for women's

    Returns:
        Parsed game data dictionary or error dict
    """
    try:
        # Use filename as cache key
        filename = os.path.basename(file_path)
        filename_no_ext = os.path.splitext(filename)[0]
        safe_filename = re.sub(r'[^\w\-_]', '_', filename_no_ext)

        cache_path = CACHE_DIR / f"{safe_filename}.json"

        # Check cache
        if cache_path.exists():
            html_mtime = os.path.getmtime(file_path)
            json_mtime = os.path.getmtime(cache_path)

            if html_mtime <= json_mtime:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    cached_data['_from_cache'] = True
                    # Normalize venue names to match current venues.json
                    from .utils.venue_resolver import normalize_cached_venue
                    normalized_venue = normalize_cached_venue(cached_data)
                    if normalized_venue:
                        cached_data['basic_info']['venue'] = normalized_venue

                    # Run ESPN PBP analysis if not already present
                    if 'espn_pbp_analysis' not in cached_data:
                        try:
                            from .engines.espn_pbp_engine import ESPNPlayByPlayEngine

                            pbp_data = None

                            # First check if we have stored PBP data (from SIDEARM embedded)
                            if cached_data.get('espn_pbp') and cached_data['espn_pbp'].get('plays'):
                                pbp_data = cached_data['espn_pbp']
                            else:
                                # Try to fetch from ESPN API for D1 games
                                from .utils.espn_pbp_scraper import fetch_espn_play_by_play, get_espn_id_from_cache
                                from datetime import datetime

                                basic_info = cached_data.get('basic_info', {})
                                game_gender = basic_info.get('gender', 'M')
                                date_str = basic_info.get('date', '')
                                away_team = basic_info.get('away_team', '')
                                home_team = basic_info.get('home_team', '')

                                # Convert date from "January 11, 2025" to "20250111" format
                                date_yyyymmdd = ''
                                if date_str:
                                    try:
                                        dt = datetime.strptime(date_str, '%B %d, %Y')
                                        date_yyyymmdd = dt.strftime('%Y%m%d')
                                    except ValueError:
                                        pass

                                if date_yyyymmdd:
                                    espn_id = get_espn_id_from_cache(away_team, home_team, date_yyyymmdd, game_gender)
                                    if espn_id:
                                        # Pass date for ncaahoopR fallback on older games
                                        pbp_data = fetch_espn_play_by_play(
                                            espn_id, game_gender, verbose=False, date_yyyymmdd=date_yyyymmdd
                                        )

                            if pbp_data and pbp_data.get('plays'):
                                engine = ESPNPlayByPlayEngine(pbp_data, cached_data)
                                cached_data['espn_pbp_analysis'] = engine.analyze()
                                # Save updated cache
                                with open(cache_path, 'w', encoding='utf-8') as cf:
                                    json.dump(cached_data, cf)
                        except Exception:
                            pass  # Don't fail if ESPN PBP fails

                    return cached_data

        # Parse HTML (cache miss or outdated)
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Auto-detect gender from filename if not explicitly set
        detected_gender = gender
        filename_lower = os.path.basename(file_path).lower()
        if '(women)' in filename_lower or 'women' in filename_lower or '_w_' in filename_lower or '_w.' in filename_lower:
            detected_gender = 'W'
        elif '(men)' in filename_lower or 'men' in filename_lower or '_m_' in filename_lower or '_m.' in filename_lower:
            detected_gender = 'M'

        # Auto-detect parser format
        if is_sidearm_format(html_content):
            debug("  Detected SIDEARM Stats format")
            game_data = parse_sidearm_boxscore(html_content, detected_gender)
        else:
            game_data = parse_sports_reference_boxscore(html_content, detected_gender)
        game_id = game_data.get("game_id", "UNKNOWN")

        debug(f"  Parsed game: {game_id}")

        # Report any parsing warnings (these are important, keep as warnings)
        parsing_warnings = game_data.get('_parsing_warnings', [])
        if parsing_warnings:
            for warning in parsing_warnings:
                warn(f"  {os.path.basename(file_path)}: {warning}")

        # Enrich with AP rankings if poll data available
        game_data = enrich_game_with_rankings(game_data)

        # Save to cache
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2)

        # Copy HTML file to html_games directory if not already there
        html_games_dir = os.path.join(BASE_DIR, 'html_games')
        if not file_path.startswith(html_games_dir):
            os.makedirs(html_games_dir, exist_ok=True)
            dest_filename = os.path.basename(file_path)
            # Use game_id as filename for consistency
            if game_id and game_id != 'UNKNOWN':
                dest_filename = f"{game_id}.html"
            dest_path = os.path.join(html_games_dir, dest_filename)
            if not os.path.exists(dest_path):
                shutil.copy2(file_path, dest_path)
                debug(f"  Copied to html_games/{dest_filename}")

        return game_data

    except (HTMLParsingError, SidearmParsingError) as e:
        error_msg = str(e)
        error(f"Invalid HTML in {file_path}: {error_msg}")
        return {"_error": True, "file": file_path, "error": error_msg}
    except Exception as e:
        from .utils.log import exception
        exception(f"Error processing {file_path}", e)
        return {"_error": True, "file": file_path, "error": str(e)}


def process_directory_or_file(input_path: str, gender: str = 'M') -> List[Dict[str, Any]]:
    """
    Process HTML files from directory or single file.

    Args:
        input_path: Path to file or directory
        gender: Gender filter

    Returns:
        List of parsed game dictionaries
    """
    all_games_data = []
    failed_files = []

    if os.path.isfile(input_path):
        if input_path.endswith('.html'):
            game_data = process_html_file(input_path, gender=gender)
            if game_data:
                if game_data.get("_error"):
                    failed_files.append(game_data)
                else:
                    all_games_data.append(game_data)
        else:
            warn(f"File must be an HTML file: {input_path}")

    elif os.path.isdir(input_path):
        html_files = [f for f in os.listdir(input_path) if f.endswith('.html')]
        total = len(html_files)
        info(f"Processing {total} HTML files...")

        cached_count = 0
        parsed_count = 0

        for idx, filename in enumerate(html_files, start=1):
            file_path = os.path.join(input_path, filename)
            game_data = process_html_file(file_path, idx, total, gender)
            if game_data:
                if game_data.get("_error"):
                    failed_files.append(game_data)
                else:
                    if game_data.pop('_from_cache', False):
                        cached_count += 1
                    else:
                        parsed_count += 1
                    all_games_data.append(game_data)

            # Show progress every 10% or at completion
            if idx == total or (total >= 10 and idx % max(1, total // 10) == 0):
                pct = idx * 100 // total
                debug(f"  Progress: {idx}/{total} ({pct}%)")
    else:
        warn(f"Invalid path: {input_path}")
        return []

    # Summary line
    summary_parts = [f"{len(all_games_data)} games"]
    if cached_count > 0:
        summary_parts.append(f"{cached_count} cached")
    if parsed_count > 0:
        summary_parts.append(f"{parsed_count} parsed")
    info(f"Loaded {', '.join(summary_parts)}")

    # Report failed files
    if failed_files:
        warn(f"\nFailed to process {len(failed_files)} file(s):")
        for failed in failed_files:
            file_name = os.path.basename(failed["file"])
            error_msg = failed["error"]
            warn(f"   {file_name}")
            warn(f"     Error: {error_msg}")

    # Build set of existing game IDs to avoid duplicates with ESPN
    existing_game_ids = set()
    for game in all_games_data:
        basic = game.get('basic_info', {})
        date_yyyymmdd = basic.get('date_yyyymmdd', '')
        home_team = basic.get('home_team', '')
        if date_yyyymmdd and home_team:
            home_slug = home_team.lower().replace(' ', '-').replace("'", '').replace('.', '')
            existing_game_ids.add(f"{date_yyyymmdd}-{home_slug}")

    # Add ESPN cached games that don't have SR data yet
    espn_games = load_espn_cached_games(existing_game_ids)
    if espn_games:
        info(f"Added {len(espn_games)} game(s) from ESPN cache")
        all_games_data.extend(espn_games)

    return all_games_data


def _find_npx() -> str:
    """Find npx executable cross-platform."""
    # Try shutil.which first (works on all platforms)
    npx_path = shutil.which('npx')
    if npx_path:
        return npx_path

    # Common paths to check on different platforms
    common_paths = [
        '/opt/homebrew/bin/npx',      # macOS Homebrew (Apple Silicon)
        '/usr/local/bin/npx',          # macOS Homebrew (Intel) / Linux
        '/usr/bin/npx',                # Linux system install
        os.path.expanduser('~/.nvm/current/bin/npx'),  # nvm
        os.path.expanduser('~/.volta/bin/npx'),        # volta
    ]

    # Windows paths
    if sys.platform == 'win32':
        common_paths.extend([
            os.path.expandvars(r'%APPDATA%\npm\npx.cmd'),
            os.path.expandvars(r'%ProgramFiles%\nodejs\npx.cmd'),
        ])

    for path in common_paths:
        if os.path.isfile(path):
            return path

    return ''


def _deploy_to_surge(html_path: str) -> None:
    """Deploy the website to surge.sh (cross-platform)."""
    docs_dir = os.path.dirname(html_path)

    info(f"\nDeploying to {SURGE_DOMAIN}...")

    # Find npx executable
    npx_path = _find_npx()
    if not npx_path:
        warn("npx not found - install Node.js to enable surge deployment")
        warn("  macOS: brew install node")
        warn("  Linux: sudo apt install nodejs npm")
        warn("  Windows: https://nodejs.org/")
        return

    try:
        result = subprocess.run(
            [npx_path, "surge", docs_dir, SURGE_DOMAIN],
            capture_output=True,
            text=True,
            timeout=120
        )
        if result.returncode == 0:
            success(f"Deployed to https://{SURGE_DOMAIN}")
        else:
            warn(f"Surge deployment failed: {result.stderr}")
            if "not found" in result.stderr.lower():
                warn("Try running: npx surge login")
    except subprocess.TimeoutExpired:
        warn("Surge deployment timed out (>120s)")
    except FileNotFoundError:
        warn(f"npx not found at {npx_path} - skipping surge deployment")
    except PermissionError:
        warn(f"Permission denied running {npx_path}")
    except OSError as e:
        warn(f"OS error during deployment: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="College Basketball Game Processor - Parse HTML box scores and generate statistics"
    )
    parser.add_argument(
        'input_path',
        nargs='?',
        default=str(DEFAULT_INPUT_DIR),
        help='Directory containing HTML files or single HTML file'
    )
    parser.add_argument(
        '--output-excel',
        default=str(BASE_DIR / 'Basketball_Stats.xlsx'),
        help='Excel output filename'
    )
    parser.add_argument(
        '--output-html',
        default=str(DEFAULT_HTML_OUTPUT),
        help='HTML website output filename'
    )
    parser.add_argument(
        '--gender',
        choices=['M', 'W', 'both'],
        default='M',
        help='Filter by gender (M=men, W=women, both=all)'
    )
    parser.add_argument(
        '--save-json',
        action='store_true',
        help='Save intermediate JSON data file'
    )
    parser.add_argument(
        '--from-cache-only',
        action='store_true',
        help='Load all games from cached JSON files instead of reprocessing HTML'
    )
    parser.add_argument(
        '--excel-only',
        action='store_true',
        help='Generate only Excel workbook, skip website generation'
    )
    parser.add_argument(
        '--website-only',
        action='store_true',
        help='Generate only website, skip Excel workbook'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable extra debug output'
    )
    parser.add_argument(
        '--no-emoji',
        action='store_true',
        help='Disable emoji in console output'
    )
    parser.add_argument(
        '--check-nba',
        action='store_true',
        help='Run NBA/WNBA player lookups (skipped by default during season)'
    )
    parser.add_argument(
        '--no-deploy',
        action='store_true',
        help='Skip automatic surge deployment'
    )
    parser.add_argument(
        '--log-file',
        type=str,
        default=None,
        help='Write logs to file (includes timestamps and full context)'
    )
    parser.add_argument(
        '--show-caller',
        action='store_true',
        help='Show file:line:function context in log messages'
    )
    parser.add_argument(
        '--timestamps',
        action='store_true',
        help='Show timestamps in console log output'
    )
    parser.add_argument(
        '--validate-urls',
        action='store_true',
        help='Validate all Basketball Reference URLs in confirmed players'
    )
    parser.add_argument(
        '--backfill-draft',
        action='store_true',
        help='Backfill draft info for all confirmed NBA/WNBA players'
    )

    args = parser.parse_args()

    # Configure logging
    set_verbosity(args.verbose)
    set_use_emoji(not args.no_emoji)
    if args.log_file:
        from .utils.log import set_log_file
        set_log_file(args.log_file)
        info(f"Logging to file: {args.log_file}")
    if args.show_caller:
        from .utils.log import set_show_caller
        set_show_caller(True)
    if args.timestamps:
        from .utils.log import set_show_timestamp
        set_show_timestamp(True)

    # Handle standalone utility commands
    if args.validate_urls:
        from .utils.nba_players import validate_all_urls
        info("Validating all Basketball Reference URLs...")
        validate_all_urls(auto_fix=True)
        return

    if args.backfill_draft:
        from .utils.nba_players import backfill_draft_info
        info("Backfilling draft info for confirmed players...")
        backfill_draft_info()
        return

    # Validate flags
    if args.excel_only and args.website_only:
        warn("Error: Cannot use both --excel-only and --website-only flags")
        return

    if not os.path.exists(args.input_path) and not args.from_cache_only:
        warn(f"Input path does not exist: {args.input_path}")
        return

    info("Starting College Basketball Game Processor...")
    info(f"Input: {args.input_path}")

    if not args.website_only:
        info(f"Output Excel: {args.output_excel}")
        args.output_excel = os.path.expanduser(args.output_excel)

    # Load game data
    if args.from_cache_only:
        info("Loading games from cache only...")
        from .utils.venue_resolver import normalize_cached_venue
        games_data = []
        skipped_files = 0
        error_files = []
        # Skip non-game cache files (metadata caches that don't contain game data)
        skip_files = {
            'nba_lookup_cache.json', 'nba_api_cache.json', 'schedule_cache.json',
            'proballers_cache.json', 'poll_cache.json', 'conferences_cache.json'
        }
        for file in CACHE_DIR.glob("*.json"):
            if file.name in skip_files:
                skipped_files += 1
                continue
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    game = json.load(f)
                # Validate this looks like a game file (has basic_info with required fields)
                basic_info = game.get('basic_info')
                if not basic_info or not isinstance(basic_info, dict):
                    skipped_files += 1
                    continue
                # Skip if missing essential game fields
                if not basic_info.get('home_team') or not basic_info.get('away_team'):
                    skipped_files += 1
                    continue
                # Normalize venue names to match current venues.json
                # This handles arena renames while preserving neutral site venues
                normalized_venue = normalize_cached_venue(game)
                if normalized_venue:
                    basic_info['venue'] = normalized_venue
                games_data.append(game)
            except json.JSONDecodeError as e:
                error_files.append(f"{file.name}: JSON parse error - {e}")
            except Exception as e:
                error_files.append(f"{file.name}: {e}")
        if error_files:
            warn(f"Failed to load {len(error_files)} cache file(s):")
            for err in error_files[:5]:  # Show first 5 errors
                warn(f"  - {err}")
            if len(error_files) > 5:
                warn(f"  ... and {len(error_files) - 5} more")
    else:
        games_data = process_directory_or_file(args.input_path, args.gender)

    if not games_data:
        warn("No games data to process. Exiting.")
        return

    # Save intermediate JSON
    if args.save_json:
        json_output = os.path.join(os.path.dirname(args.output_excel), "all_games_data.json")
        with open(json_output, 'w', encoding='utf-8') as json_file:
            json.dump(games_data, json_file, indent=2)
        info(f"JSON data saved to {json_output}")

    # Determine what to generate
    generate_excel = not args.website_only
    generate_website = not args.excel_only

    # Generate outputs
    try:
        # Remove existing Excel file if we're writing a new one
        if generate_excel and os.path.exists(args.output_excel):
            debug(f"Removing existing file: {args.output_excel}")
            os.remove(args.output_excel)

        # Process data (always needed for both outputs)
        info(f"\nGenerating {'Excel and website' if generate_excel and generate_website else 'Excel' if generate_excel else 'website'}...")
        processed_data = generate_excel_workbook(
            games_data,
            args.output_excel,
            write_file=generate_excel
        )

        # Generate website if requested
        if generate_website:
            processed_data['_raw_games'] = games_data
            generate_website_from_data(processed_data, args.output_html, skip_nba=not args.check_nba)

        # Report results
        success("\nProcessing complete!")
        if generate_excel:
            info(f"Excel: {os.path.abspath(args.output_excel)}")
        if generate_website:
            info(f"Website: {os.path.abspath(args.output_html)}")

        # Deploy to surge if website was generated
        if generate_website and not args.no_deploy:
            _deploy_to_surge(args.output_html)

            # Refresh active status for pro players in background (updates cache for next run)
            try:
                from .utils.nba_players import refresh_active_status
                refresh_active_status()
            except Exception as e:
                warn(f"Active status refresh failed: {e}")

    except Exception as e:
        from .utils.log import exception
        exception("Error during processing", e)


if __name__ == '__main__':
    main()
