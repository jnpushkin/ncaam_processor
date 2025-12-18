"""
Main entry point for the College Basketball Stats Processor.
"""

import os
import sys
import json
import argparse
import traceback
import re
from pathlib import Path

from .excel.workbook_generator import generate_excel_workbook
from .parsers.html_parser import parse_sports_reference_boxscore
from .utils.constants import BASE_DIR, DEFAULT_INPUT_DIR, CACHE_DIR
from .utils.log import info, warn, set_verbosity, set_use_emoji
from .website import generate_website_from_data


def process_html_file(file_path: str, index: int = None, total: int = None, gender: str = 'M'):
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
        if index is not None and total is not None:
            info(f"Processing file {index} of {total}: {os.path.basename(file_path)}")
        else:
            info(f"Processing {file_path}...")

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
                info("  Using cached data")
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                    game_id = cached_data.get("game_id", "Unknown")
                    info(f"     Game ID: {game_id}")
                    return cached_data
            else:
                info("  Cache outdated, re-parsing...")
        else:
            info("  No cache found, parsing HTML...")

        # Parse HTML
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Auto-detect gender from filename if not explicitly set
        detected_gender = gender
        filename_lower = os.path.basename(file_path).lower()
        if '(women)' in filename_lower or 'women' in filename_lower:
            detected_gender = 'W'
        elif '(men)' in filename_lower or 'men' in filename_lower:
            detected_gender = 'M'

        game_data = parse_sports_reference_boxscore(html_content, detected_gender)
        game_id = game_data.get("game_id", "UNKNOWN")

        info(f"  Parsed game: {game_id}")

        # Save to cache
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(game_data, f, indent=2)
        info("  Saved to cache")

        return game_data

    except Exception as e:
        error_msg = str(e)
        warn(f"Error processing {file_path}: {error_msg}")
        traceback.print_exc()
        return {"_error": True, "file": file_path, "error": error_msg}


def process_directory_or_file(input_path: str, gender: str = 'M'):
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
        info(f"Found {len(html_files)} HTML files in {input_path}")

        total = len(html_files)

        for idx, filename in enumerate(html_files, start=1):
            file_path = os.path.join(input_path, filename)
            game_data = process_html_file(file_path, idx, total, gender)
            if game_data:
                if game_data.get("_error"):
                    failed_files.append(game_data)
                else:
                    all_games_data.append(game_data)
    else:
        warn(f"Invalid path: {input_path}")
        return []

    info(f"Successfully processed {len(all_games_data)} games")

    # Report failed files
    if failed_files:
        warn(f"\nFailed to process {len(failed_files)} file(s):")
        for failed in failed_files:
            file_name = os.path.basename(failed["file"])
            error_msg = failed["error"]
            warn(f"   {file_name}")
            warn(f"     Error: {error_msg}")

    return all_games_data


def main():
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

    args = parser.parse_args()

    # Configure logging
    set_verbosity(args.verbose)
    set_use_emoji(not args.no_emoji)

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
        games_data = []
        for file in CACHE_DIR.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                games_data.append(json.load(f))
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

    # Generate outputs
    try:
        if args.website_only:
            info("\nWebsite-only mode: Processing data without writing Excel...")

            processed_data = generate_excel_workbook(
                games_data,
                args.output_excel,
                write_file=False
            )

            html_path = args.output_excel.replace('.xlsx', '.html')
            processed_data['_raw_games'] = games_data
            generate_website_from_data(processed_data, html_path)

            info("\nProcessing complete!")
            info(f"Website: {os.path.abspath(html_path)}")

        elif args.excel_only:
            info("\nExcel-only mode: Skipping website generation...")

            if os.path.exists(args.output_excel):
                info(f"Removing existing file: {args.output_excel}")
                os.remove(args.output_excel)

            processed_data = generate_excel_workbook(
                games_data,
                args.output_excel,
                write_file=True
            )

            info("\nProcessing complete!")
            info(f"Excel: {os.path.abspath(args.output_excel)}")

        else:
            info("\nGenerating both Excel and website...")

            if os.path.exists(args.output_excel):
                info(f"Removing existing file: {args.output_excel}")
                os.remove(args.output_excel)

            processed_data = generate_excel_workbook(
                games_data,
                args.output_excel,
                write_file=True
            )

            info("\nExcel complete, generating website...")

            html_path = args.output_excel.replace('.xlsx', '.html')
            processed_data['_raw_games'] = games_data
            generate_website_from_data(processed_data, html_path)

            info("\nProcessing complete!")
            info(f"Excel: {os.path.abspath(args.output_excel)}")
            info(f"Website: {os.path.abspath(html_path)}")

    except Exception as e:
        warn(f"Error during processing: {str(e)}")
        traceback.print_exc()


if __name__ == '__main__':
    main()
