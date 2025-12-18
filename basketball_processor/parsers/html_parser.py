"""
Main HTML parser for Sports Reference college basketball box scores.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup, Comment

from .stats_parser import (
    extract_player_stats,
    extract_team_totals,
    merge_basic_and_advanced_stats,
    find_box_score_tables,
)
from ..utils.helpers import (
    get_team_code,
    parse_date,
    format_date_yyyymmdd,
    generate_game_id,
    safe_int,
    safe_float,
)
from ..engines.milestone_engine import MilestoneEngine
from ..engines.special_events_engine import SpecialEventsEngine
from ..utils.venue_resolver import resolve_venue


def parse_sports_reference_boxscore(html_content: str, gender: str = 'M') -> Dict[str, Any]:
    """
    Parse a Sports Reference college basketball box score HTML file.

    Args:
        html_content: Raw HTML string
        gender: 'M' for men's, 'W' for women's

    Returns:
        game_data dictionary with all extracted information
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Initialize game data structure
    game_data = {
        'basic_info': {},
        'linescore': {},
        'box_score': {
            'away': {'basic': [], 'advanced': []},
            'home': {'basic': [], 'advanced': []},
        },
        'team_totals': {
            'away': {},
            'home': {},
        },
        'officials': [],
        'milestone_stats': {},
        'special_events': {},
        'gender': gender,
    }

    # Extract basic game info
    game_data['basic_info'] = extract_basic_info(soup)

    # Extract linescore
    game_data['linescore'] = extract_linescore(soup)

    # Fallback: If team names are empty, try to extract from title
    if not game_data['basic_info'].get('away_team') or not game_data['basic_info'].get('home_team'):
        away_name, home_name = get_team_names_from_title(soup)
        if away_name and not game_data['basic_info'].get('away_team'):
            game_data['basic_info']['away_team'] = away_name
            game_data['basic_info']['away_team_code'] = get_team_code(away_name)
        if home_name and not game_data['basic_info'].get('home_team'):
            game_data['basic_info']['home_team'] = home_name
            game_data['basic_info']['home_team_code'] = get_team_code(home_name)

    # Fallback: If scores are 0, try to get from linescore totals
    if game_data['basic_info'].get('away_score', 0) == 0:
        linescore_away_total = game_data['linescore'].get('away', {}).get('total', 0)
        if linescore_away_total > 0:
            game_data['basic_info']['away_score'] = linescore_away_total
    if game_data['basic_info'].get('home_score', 0) == 0:
        linescore_home_total = game_data['linescore'].get('home', {}).get('total', 0)
        if linescore_home_total > 0:
            game_data['basic_info']['home_score'] = linescore_home_total

    # Generate game ID early so venue resolver can check game overrides
    game_data['game_id'] = generate_game_id(
        game_data['basic_info'].get('date', ''),
        game_data['basic_info'].get('home_team', '')
    )

    # Resolve venue using venue resolver
    # Always call resolver - it handles game overrides which should take priority
    resolved_venue = resolve_venue(game_data)
    if resolved_venue:
        game_data['basic_info']['venue'] = resolved_venue

    # Find team slugs from box score tables
    team_slugs = find_box_score_tables(soup)

    if len(team_slugs) >= 2:
        # Determine which is away/home based on order (away team listed first)
        away_slug = team_slugs[0]
        home_slug = team_slugs[1]

        # Extract player stats
        game_data['box_score']['away']['basic'] = extract_player_stats(soup, away_slug, is_basic=True)
        game_data['box_score']['away']['advanced'] = extract_player_stats(soup, away_slug, is_basic=False)
        game_data['box_score']['home']['basic'] = extract_player_stats(soup, home_slug, is_basic=True)
        game_data['box_score']['home']['advanced'] = extract_player_stats(soup, home_slug, is_basic=False)

        # Merge basic and advanced stats
        game_data['box_score']['away']['players'] = merge_basic_and_advanced_stats(
            game_data['box_score']['away']['basic'],
            game_data['box_score']['away']['advanced']
        )
        game_data['box_score']['home']['players'] = merge_basic_and_advanced_stats(
            game_data['box_score']['home']['basic'],
            game_data['box_score']['home']['advanced']
        )

        # Extract team totals
        game_data['team_totals']['away'] = extract_team_totals(soup, away_slug, is_basic=True)
        game_data['team_totals']['home'] = extract_team_totals(soup, home_slug, is_basic=True)

        # Store team slugs for reference
        game_data['basic_info']['away_team_slug'] = away_slug
        game_data['basic_info']['home_team_slug'] = home_slug

    # Extract officials if available
    game_data['officials'] = extract_officials(soup)

    # Run milestone detection
    milestone_engine = MilestoneEngine(game_data)
    game_data = milestone_engine.process()

    # Run special events detection
    special_events_engine = SpecialEventsEngine(game_data)
    game_data = special_events_engine.detect()

    return game_data


def extract_basic_info(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract basic game information from the scorebox.

    Returns:
        Dictionary with game metadata
    """
    info = {
        'away_team': '',
        'home_team': '',
        'away_score': 0,
        'home_score': 0,
        'date': '',
        'date_yyyymmdd': '',
        'venue': '',
        'attendance': None,
        'away_record': '',
        'home_record': '',
        'sports_ref_url': '',
    }

    # Extract canonical URL (Sports Reference box score link)
    canonical_link = soup.find('link', rel='canonical')
    if canonical_link and canonical_link.get('href'):
        info['sports_ref_url'] = canonical_link['href']

    # Find scorebox
    scorebox = soup.find('div', class_='scorebox')
    if not scorebox:
        return info

    # Extract team info from scorebox
    # The scorebox has two main team divs
    team_divs = scorebox.find_all('div', recursive=False)

    teams_found = []
    for div in team_divs:
        # Look for team name link
        team_link = div.find('a', href=re.compile(r'/cbb/schools/'))
        if team_link:
            team_name = team_link.get_text(strip=True)

            # Get score
            score_div = div.find('div', class_='score')
            score = 0
            if score_div:
                score = safe_int(score_div.get_text(strip=True), 0)

            # Get record if present (usually in format like "(23-6)")
            record = ''
            record_match = re.search(r'\((\d+-\d+)\)', div.get_text())
            if record_match:
                record = record_match.group(1)

            teams_found.append({
                'name': team_name,
                'score': score,
                'record': record,
            })

    # First team is away, second is home
    if len(teams_found) >= 2:
        info['away_team'] = teams_found[0]['name']
        info['away_score'] = teams_found[0]['score']
        info['away_record'] = teams_found[0]['record']
        info['away_team_code'] = get_team_code(teams_found[0]['name'])

        info['home_team'] = teams_found[1]['name']
        info['home_score'] = teams_found[1]['score']
        info['home_record'] = teams_found[1]['record']
        info['home_team_code'] = get_team_code(teams_found[1]['name'])

    # Extract date, venue, attendance from scorebox_meta
    meta_div = scorebox.find('div', class_='scorebox_meta')
    if meta_div:
        meta_text = meta_div.get_text(separator='\n')
        lines = [line.strip() for line in meta_text.split('\n') if line.strip()]

        for i, line in enumerate(lines):
            # First line is usually the date
            if i == 0 and re.match(r'^[A-Za-z]+ \d+, \d{4}', line):
                info['date'] = line
                info['date_yyyymmdd'] = format_date_yyyymmdd(line)

            # Look for venue - check for arena keywords first
            if 'Arena' in line or 'Center' in line or 'Coliseum' in line or 'Stadium' in line or 'Pavilion' in line or 'Fieldhouse' in line or 'Gym' in line:
                info['venue'] = line
            # Also capture location lines (City, State format) as fallback
            elif not info.get('venue') and re.match(r'^[A-Za-z\s]+,\s*[A-Za-z\s]+$', line):
                # Skip if it looks like the date line or contains logos text
                if 'Logos' not in line and not re.match(r'^[A-Za-z]+ \d+', line):
                    info['location'] = line

            # Look for attendance
            attendance_match = re.search(r'Attendance:?\s*([\d,]+)', line)
            if attendance_match:
                info['attendance'] = safe_int(attendance_match.group(1).replace(',', ''), None)

    # Also try to get date from page title
    if not info['date']:
        title = soup.find('title')
        if title:
            title_text = title.get_text()
            date_match = re.search(r'(\w+ \d+, \d{4})', title_text)
            if date_match:
                info['date'] = date_match.group(1)
                info['date_yyyymmdd'] = format_date_yyyymmdd(info['date'])

    return info


def extract_linescore(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract half-by-half and overtime scoring.

    Returns:
        Dictionary with linescore data
    """
    linescore = {
        'away': {'halves': [], 'OT': [], 'total': 0},
        'home': {'halves': [], 'OT': [], 'total': 0},
    }

    # Find linescore table
    # It may be in a comment, so we need to parse comments
    linescore_table = soup.find('table', {'id': 'line-score'})

    if not linescore_table:
        # Check for commented out content
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'line-score' in comment:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                linescore_table = comment_soup.find('table', {'id': 'line-score'})
                if linescore_table:
                    break

    if not linescore_table:
        return linescore

    rows = linescore_table.find_all('tr')
    team_index = 0

    for row in rows:
        cells = row.find_all(['th', 'td'])
        if len(cells) < 3:
            continue

        # Check if this is a team row (has score data)
        # First cell is team name, then period scores, then total
        team_cell = cells[0]
        # Accept rows where first cell is a th and there are td cells with score data
        # This excludes header rows which have all th cells
        has_td_cells = any(cell.name == 'td' for cell in cells[1:])
        is_team_row = (team_cell.name == 'th' and has_td_cells and
                       (team_cell.find('a') or team_cell.get('data-stat') == 'team'))
        if is_team_row and team_index < 2:
            team_key = 'away' if team_index == 0 else 'home'
            team_index += 1

            period_scores = []
            for cell in cells[1:-1]:  # Skip team name and total
                score = safe_int(cell.get_text(strip=True), 0)
                period_scores.append(score)

            # Last cell is total
            total = safe_int(cells[-1].get_text(strip=True), 0)

            # First 2 periods are halves, rest are OT
            if len(period_scores) >= 2:
                linescore[team_key]['halves'] = period_scores[:2]
                if len(period_scores) > 2:
                    linescore[team_key]['OT'] = period_scores[2:]

            linescore[team_key]['total'] = total

    return linescore


def extract_officials(soup: BeautifulSoup) -> List[str]:
    """
    Extract referee/officials information.

    Returns:
        List of official names
    """
    officials = []

    # Look for officials section
    # This might be in the scorebox_meta or elsewhere
    meta_div = soup.find('div', class_='scorebox_meta')
    if meta_div:
        meta_text = meta_div.get_text()
        officials_match = re.search(r'Officials?:?\s*(.+?)(?:\n|$)', meta_text, re.IGNORECASE)
        if officials_match:
            officials_text = officials_match.group(1)
            # Split by comma or 'and'
            officials = [o.strip() for o in re.split(r',|and', officials_text) if o.strip()]

    return officials


def extract_four_factors(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract Four Factors data if available.

    Returns:
        Dictionary with four factors for both teams
    """
    factors = {
        'away': {},
        'home': {},
    }

    # Find four factors table
    ff_table = soup.find('table', {'id': 'four-factors'})

    if not ff_table:
        # Check comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'four-factors' in comment:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                ff_table = comment_soup.find('table', {'id': 'four-factors'})
                if ff_table:
                    break

    if not ff_table:
        return factors

    rows = ff_table.find_all('tr')
    team_index = 0

    for row in rows:
        cells = row.find_all(['th', 'td'])
        if len(cells) < 2:
            continue

        team_cell = cells[0]
        if team_cell.find('a'):
            team_key = 'away' if team_index == 0 else 'home'
            team_index += 1

            for cell in cells[1:]:
                stat_name = cell.get('data-stat')
                if stat_name:
                    factors[team_key][stat_name] = safe_float(cell.get_text(strip=True), None)

    return factors


def get_team_names_from_title(soup: BeautifulSoup) -> Tuple[str, str]:
    """
    Extract team names from page title as fallback.

    Returns:
        Tuple of (away_team, home_team)
    """
    title = soup.find('title')
    if not title:
        return ('', '')

    title_text = title.get_text()

    # Pattern: "Team1 vs. Team2 Box Score"
    match = re.search(r'(.+?)\s+(?:vs\.?|at)\s+(.+?)\s+Box Score', title_text, re.IGNORECASE)
    if match:
        return (match.group(1).strip(), match.group(2).strip())

    return ('', '')
