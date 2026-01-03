"""
Parser for SIDEARM Stats college basketball box scores.
Used by ~300+ D2/D3/NAIA athletic department websites.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup

from ..utils.helpers import (
    safe_int,
    safe_float,
    parse_date,
    format_date_yyyymmdd,
    generate_game_id,
)
from ..engines.milestone_engine import MilestoneEngine
from ..engines.special_events_engine import SpecialEventsEngine
from ..utils.venue_resolver import resolve_venue


class SidearmParsingError(Exception):
    """Raised when SIDEARM HTML parsing fails."""
    pass


def is_sidearm_format(html_content: str) -> bool:
    """
    Check if HTML content is from a SIDEARM Stats site.

    Args:
        html_content: Raw HTML string

    Returns:
        True if this appears to be SIDEARM format
    """
    if not html_content:
        return False

    # Check for SIDEARM indicators
    indicators = [
        'sidearm',
        'c-scoreboard',
        'logo_handler.ashx',
        '/sports/mens-basketball/stats/',
        '/sports/womens-basketball/stats/',
    ]

    content_lower = html_content.lower()
    return any(ind in content_lower for ind in indicators)


def _parse_made_attempted(value: str) -> Tuple[int, int]:
    """Parse a 'made-attempted' string like '5-12' into (made, attempted)."""
    if not value or value == '-':
        return 0, 0

    match = re.match(r'(\d+)-(\d+)', str(value).strip())
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def _parse_orb_drb(value: str) -> Tuple[int, int]:
    """Parse 'ORB-DRB' combined string into (orb, drb)."""
    if not value or value == '-':
        return 0, 0

    match = re.match(r'(\d+)-(\d+)', str(value).strip())
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def _parse_minutes(value: str) -> float:
    """Parse minutes, handling MM:SS format."""
    if not value or value == '-':
        return 0.0

    value = str(value).strip()

    # Handle MM:SS format
    if ':' in value:
        parts = value.split(':')
        if len(parts) == 2:
            return float(parts[0]) + float(parts[1]) / 60

    # Handle plain number
    try:
        return float(value)
    except ValueError:
        return 0.0


def _normalize_player_name(name: str) -> str:
    """
    Normalize player name from SIDEARM format.

    Converts "Last,First" or "Last, First" to "First Last" format.
    Also handles suffixes like Jr., Sr., III, IV.
    """
    if not name:
        return name

    # Remove jersey number prefix if present
    name = re.sub(r'^\d+\s*', '', name).strip()

    # Check for "Last,First" or "Last, First" format
    if ',' in name:
        parts = [p.strip() for p in name.split(',', 1)]
        if len(parts) == 2:
            last_name = parts[0]
            first_name = parts[1]

            # Handle suffixes that might be at the end of first name part
            # e.g., "Smith,John Jr." -> "John Smith Jr."
            suffix_match = re.search(r'\s+(Jr\.?|Sr\.?|III|IV|II|V)$', first_name, re.IGNORECASE)
            suffix = ''
            if suffix_match:
                suffix = ' ' + suffix_match.group(1)
                first_name = first_name[:suffix_match.start()]

            name = f"{first_name} {last_name}{suffix}"

    return name.strip()


def _extract_team_names(soup: BeautifulSoup) -> Tuple[str, str]:
    """Extract away and home team names from SIDEARM box score."""
    away_team = ""
    home_team = ""

    # Method 1: Try box score table captions (most reliable)
    # Captions are like: "Jessup 77" or "Academy of Art 85"
    tables = soup.select('table.sidearm-table.overall-stats')
    captions = []
    for table in tables:
        caption = table.select_one('caption')
        if caption:
            text = caption.get_text(strip=True)
            # Remove score from caption (e.g., "Jessup 77" -> "Jessup")
            # Score is typically the last word if it's a number
            parts = text.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].isdigit():
                captions.append(parts[0])
            elif text:
                captions.append(text)

    if len(captions) >= 2:
        away_team = captions[0]
        home_team = captions[1]
        return away_team, home_team

    # Method 2: Try page title
    # Format: "Men's Basketball vs Jessup on 1/18/2025 - Box Score - Academy of Art University Athletics"
    title = soup.select_one('title')
    if title:
        title_text = title.get_text(strip=True)
        # Match pattern: "sport vs OPPONENT on DATE - Box Score - HOME SCHOOL Athletics"
        vs_match = re.search(r'vs\s+(.+?)\s+on\s+\d', title_text, re.IGNORECASE)
        home_match = re.search(r'Box Score\s*-\s*(.+?)\s+Athletics', title_text, re.IGNORECASE)
        if vs_match and home_match:
            away_team = vs_match.group(1).strip()
            home_team = home_match.group(1).strip()
            return away_team, home_team

    # Method 3: Try og:title meta tag
    og_title = soup.select_one('meta[name="og:title"], meta[property="og:title"]')
    if og_title:
        content = og_title.get('content', '')
        vs_match = re.search(r'vs\s+(.+?)\s+on', content, re.IGNORECASE)
        if vs_match:
            away_team = vs_match.group(1).strip()
            # Home team from og:site_name
            og_site = soup.select_one('meta[property="og:site_name"]')
            if og_site:
                home_team = og_site.get('content', '').replace(' Athletics', '').strip()

    return away_team, home_team


def _extract_scores(soup: BeautifulSoup) -> Tuple[int, int, List[int], List[int]]:
    """Extract final scores and period scores."""
    away_score = 0
    home_score = 0
    away_periods = []
    home_periods = []

    # Look for score elements
    score_elems = soup.select('.c-scoreboard__score, .score')
    if len(score_elems) >= 2:
        away_score = safe_int(score_elems[0].get_text(strip=True))
        home_score = safe_int(score_elems[1].get_text(strip=True))

    # Look for period breakdown in tables
    summary_table = soup.select_one('table')
    if summary_table:
        rows = summary_table.select('tr')
        for row in rows:
            cells = row.select('th, td')
            if len(cells) >= 4:
                # Check if this is a score row (has team name and period scores)
                first_cell = cells[0].get_text(strip=True)
                if first_cell and not first_cell.lower() in ['team', 'total', 'half']:
                    period_scores = []
                    for cell in cells[1:-1]:  # Skip team name and total
                        score = safe_int(cell.get_text(strip=True))
                        if score > 0:
                            period_scores.append(score)

                    if not away_periods:
                        away_periods = period_scores
                    elif not home_periods:
                        home_periods = period_scores

    return away_score, home_score, away_periods, home_periods


def _extract_player_stats_sidearm(table: BeautifulSoup) -> List[Dict[str, Any]]:
    """Extract player stats from a SIDEARM format table."""
    players = []

    # Find header row to determine column indices
    header_row = table.select_one('thead tr')
    if not header_row:
        return players

    headers = [th.get_text(strip=True).upper() for th in header_row.select('th')]

    # Map column names to indices
    col_map = {}
    for i, header in enumerate(headers):
        # Normalize header names
        if header in ['PLAYER', 'NAME', '#']:
            col_map['name'] = i
        elif header == 'GS':
            col_map['gs'] = i
        elif header == 'MIN':
            col_map['mp'] = i
        elif header == 'FG':
            col_map['fg'] = i
        elif header in ['3PT', '3P', 'FG3']:
            col_map['fg3'] = i
        elif header == 'FT':
            col_map['ft'] = i
        elif header in ['ORB-DRB', 'OREB-DREB']:
            col_map['orb_drb'] = i
        elif header in ['ORB', 'OREB']:
            col_map['orb'] = i
        elif header in ['DRB', 'DREB']:
            col_map['drb'] = i
        elif header in ['REB', 'TREB']:
            col_map['trb'] = i
        elif header == 'PF':
            col_map['pf'] = i
        elif header in ['A', 'AST']:
            col_map['ast'] = i
        elif header == 'TO':
            col_map['tov'] = i
        elif header in ['BLK', 'BL']:
            col_map['blk'] = i
        elif header in ['STL', 'ST']:
            col_map['stl'] = i
        elif header in ['PTS', 'POINTS']:
            col_map['pts'] = i

    # Parse player rows
    body = table.select_one('tbody')
    if not body:
        return players

    for row in body.select('tr'):
        cells = row.select('td')
        if len(cells) < 5:  # Need at least a few columns
            continue

        # Skip team totals row and team rebound entries
        first_cell_text = cells[0].get_text(strip=True).upper()
        if 'TOTAL' in first_cell_text or 'TEAM' in first_cell_text or 'TMTEAM' in first_cell_text:
            continue

        player = {
            'name': '',
            'mp': 0.0,
            'fg': 0, 'fga': 0,
            'fg3': 0, 'fg3a': 0,
            'ft': 0, 'fta': 0,
            'orb': 0, 'drb': 0, 'trb': 0,
            'ast': 0, 'stl': 0, 'blk': 0,
            'tov': 0, 'pf': 0, 'pts': 0,
        }

        # Extract name (usually in first or second column)
        name_idx = col_map.get('name', 0)
        if name_idx < len(cells):
            name_cell = cells[name_idx]
            # Try to get name from link
            link = name_cell.select_one('a')
            if link:
                raw_name = link.get_text(strip=True)
                # Extract player ID from URL if available
                href = link.get('href', '')
                if href:
                    match = re.search(r'/roster/([^/]+)', href)
                    if match:
                        player['player_id'] = match.group(1)
            else:
                raw_name = name_cell.get_text(strip=True)

            # Normalize name (convert "Last,First" to "First Last")
            player['name'] = _normalize_player_name(raw_name)

        # Skip empty names and team entries
        if not player['name'] or player['name'].upper() in ['TMTEAM', 'TEAM', 'TM']:
            continue

        # Generate player_id if not extracted from URL
        if 'player_id' not in player:
            # Create slug from name: "John Smith Jr." -> "john-smith-jr-1"
            name_slug = re.sub(r'[^\w\s-]', '', player['name'].lower())
            name_slug = re.sub(r'\s+', '-', name_slug.strip())
            player['player_id'] = f"{name_slug}-1"

        # Get cell text by index
        def get_cell(idx):
            return cells[idx].get_text(strip=True) if idx < len(cells) else ''

        # Parse minutes
        if 'mp' in col_map:
            player['mp'] = _parse_minutes(get_cell(col_map['mp']))

        # Parse FG (made-attempted)
        if 'fg' in col_map:
            player['fg'], player['fga'] = _parse_made_attempted(get_cell(col_map['fg']))

        # Parse 3PT
        if 'fg3' in col_map:
            player['fg3'], player['fg3a'] = _parse_made_attempted(get_cell(col_map['fg3']))

        # Parse FT
        if 'ft' in col_map:
            player['ft'], player['fta'] = _parse_made_attempted(get_cell(col_map['ft']))

        # Parse rebounds
        if 'orb_drb' in col_map:
            player['orb'], player['drb'] = _parse_orb_drb(get_cell(col_map['orb_drb']))
            player['trb'] = player['orb'] + player['drb']
        else:
            if 'orb' in col_map:
                player['orb'] = safe_int(get_cell(col_map['orb']))
            if 'drb' in col_map:
                player['drb'] = safe_int(get_cell(col_map['drb']))

        if 'trb' in col_map:
            player['trb'] = safe_int(get_cell(col_map['trb']))
        elif player['trb'] == 0:
            player['trb'] = player['orb'] + player['drb']

        # Parse other stats
        if 'ast' in col_map:
            player['ast'] = safe_int(get_cell(col_map['ast']))
        if 'stl' in col_map:
            player['stl'] = safe_int(get_cell(col_map['stl']))
        if 'blk' in col_map:
            player['blk'] = safe_int(get_cell(col_map['blk']))
        if 'tov' in col_map:
            player['tov'] = safe_int(get_cell(col_map['tov']))
        if 'pf' in col_map:
            player['pf'] = safe_int(get_cell(col_map['pf']))
        if 'pts' in col_map:
            player['pts'] = safe_int(get_cell(col_map['pts']))

        players.append(player)

    return players


def _calculate_team_totals(players: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate team totals from player stats."""
    totals = {
        'mp': sum(p.get('mp', 0) for p in players),
        'fg': sum(p.get('fg', 0) for p in players),
        'fga': sum(p.get('fga', 0) for p in players),
        'fg3': sum(p.get('fg3', 0) for p in players),
        'fg3a': sum(p.get('fg3a', 0) for p in players),
        'ft': sum(p.get('ft', 0) for p in players),
        'fta': sum(p.get('fta', 0) for p in players),
        'orb': sum(p.get('orb', 0) for p in players),
        'drb': sum(p.get('drb', 0) for p in players),
        'trb': sum(p.get('trb', 0) for p in players),
        'ast': sum(p.get('ast', 0) for p in players),
        'stl': sum(p.get('stl', 0) for p in players),
        'blk': sum(p.get('blk', 0) for p in players),
        'tov': sum(p.get('tov', 0) for p in players),
        'pf': sum(p.get('pf', 0) for p in players),
        'pts': sum(p.get('pts', 0) for p in players),
    }

    # Calculate percentages
    if totals['fga'] > 0:
        totals['fg_pct'] = totals['fg'] / totals['fga']
    if totals['fg3a'] > 0:
        totals['fg3_pct'] = totals['fg3'] / totals['fg3a']
    if totals['fta'] > 0:
        totals['ft_pct'] = totals['ft'] / totals['fta']

    return totals


def _extract_game_info(soup: BeautifulSoup, url: str = '') -> Dict[str, Any]:
    """Extract game metadata from SIDEARM page."""
    info = {
        'date': '',
        'venue': '',
        'attendance': None,
        'division': None,  # D1, D2, D3, NAIA, etc.
    }

    # Extract division from window.client_division
    html_str = str(soup)
    div_match = re.search(r'window\.client_division\s*=\s*["\']([^"\']+)["\']', html_str)
    if div_match:
        div_raw = div_match.group(1).upper()
        # Normalize division names
        if div_raw in ['DI', 'D1', 'NCAA D1']:
            info['division'] = 'D1'
        elif div_raw in ['DII', 'D2', 'NCAA D2']:
            info['division'] = 'D2'
        elif div_raw in ['DIII', 'D3', 'NCAA D3']:
            info['division'] = 'D3'
        elif 'NAIA' in div_raw:
            info['division'] = 'NAIA'
        else:
            info['division'] = div_raw

    # Try to extract date from URL or page content
    if url:
        # URL pattern: /stats/2024-2025/opponent/boxscore/id
        date_match = re.search(r'/stats/(\d{4}-\d{4})/', url)
        if date_match:
            info['season'] = date_match.group(1)

    # Method 1: Try title/og:title for date
    # Format: "Men's Basketball vs Jessup on 1/18/2025 - Box Score"
    title = soup.select_one('title')
    if title:
        title_text = title.get_text(strip=True)
        date_match = re.search(r'on\s+(\d{1,2}/\d{1,2}/\d{4})', title_text)
        if date_match:
            info['date'] = date_match.group(1)

    # Method 2: Look for date elements
    if not info['date']:
        date_elems = soup.select('.c-scoreboard__date, .game-date, time')
        for elem in date_elems:
            text = elem.get_text(strip=True)
            if text:
                # Try to parse various date formats
                parsed = parse_date(text)
                if parsed:
                    info['date'] = text
                    break

    # Method 3: Try info-block/dl elements for venue, date, attendance
    # Format: "Date 01/18/13 Time 8:00 PM Attendance 1287 Site Chicago, Ill. (Ratner Center)"
    info_blocks = soup.select('dl, .info-block')
    for block in info_blocks:
        text = block.get_text(' ', strip=True)

        # Extract Site/venue
        site_match = re.search(r'Site\s+([^R][^\n]+?)(?:\s+Referees|\s+VIEW|\s*$)', text)
        if site_match and not info['venue']:
            venue_text = site_match.group(1).strip()

            # Helper to expand state abbreviations
            def expand_state(loc):
                loc = re.sub(r'\bIll\.?$', 'Illinois', loc)
                loc = re.sub(r'\bCalif\.?$', 'California', loc)
                loc = re.sub(r'\bMass\.?$', 'Massachusetts', loc)
                loc = re.sub(r'\bMD$', 'Maryland', loc)
                loc = re.sub(r'\bPA$', 'Pennsylvania', loc)
                loc = re.sub(r'\bNY$', 'New York', loc)
                loc = re.sub(r'\bCA$', 'California', loc)
                loc = re.sub(r'\bTX$', 'Texas', loc)
                loc = re.sub(r'\bFL$', 'Florida', loc)
                loc = re.sub(r'\bOH$', 'Ohio', loc)
                loc = re.sub(r'\bNC$', 'North Carolina', loc)
                loc = re.sub(r'\bVA$', 'Virginia', loc)
                loc = re.sub(r'\bGA$', 'Georgia', loc)
                return loc

            # Format 1: "Chicago, Ill. (Ratner Center)" -> "Ratner Center, Chicago, Illinois"
            paren_match = re.search(r'\(([^)]+)\)', venue_text)
            if paren_match:
                arena = paren_match.group(1)
                location = re.sub(r'\s*\([^)]+\)', '', venue_text).strip()
                location = expand_state(location)
                info['venue'] = f"{arena}, {location}"
            # Format 2: "Baltimore, MD / Goldfarb Gym" -> "Goldfarb Gym, Baltimore, Maryland"
            elif ' / ' in venue_text:
                parts = venue_text.split(' / ', 1)
                location = expand_state(parts[0].strip())
                arena = parts[1].strip()
                info['venue'] = f"{arena}, {location}"
            else:
                info['venue'] = expand_state(venue_text)

        # Extract Attendance
        att_match = re.search(r'Attendance\s+(\d+)', text)
        if att_match and info['attendance'] is None:
            info['attendance'] = int(att_match.group(1))

        # Extract Date if not found
        if not info['date']:
            date_match = re.search(r'Date\s+(\d{1,2}/\d{1,2}/\d{2,4})', text)
            if date_match:
                date_str = date_match.group(1)
                # Convert 2-digit year to 4-digit
                if len(date_str.split('/')[-1]) == 2:
                    parts = date_str.split('/')
                    year = int(parts[2])
                    year = 2000 + year if year < 50 else 1900 + year
                    date_str = f"{parts[0]}/{parts[1]}/{year}"
                info['date'] = date_str

    # Look for venue/location with class selectors (fallback)
    if not info['venue']:
        venue_elems = soup.select('.location, .venue, .c-scoreboard__location')
        for elem in venue_elems:
            text = elem.get_text(strip=True)
            if text and len(text) < 100:
                info['venue'] = text
                break

    return info


def parse_sidearm_boxscore(html_content: str, gender: str = 'M', url: str = '') -> Dict[str, Any]:
    """
    Parse a SIDEARM Stats college basketball box score.

    Args:
        html_content: Raw HTML string
        gender: 'M' for men's, 'W' for women's
        url: Original URL (optional, used for extracting game info)

    Returns:
        Dictionary with game data in standard format
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extract team names and scores from captions
    away_team, home_team = _extract_team_names(soup)
    if not away_team or not home_team:
        raise SidearmParsingError("Could not extract team names from box score")

    tables = soup.select('table.sidearm-table.overall-stats')

    # Find player stats tables (have "Player" in header, not "Team Summary")
    # These are the main box score tables with final scores in their captions
    box_score_tables = []
    for table in tables:
        headers = table.select('thead th')
        header_text = ' '.join(th.get_text(strip=True).upper() for th in headers)
        if 'PLAYER' in header_text and 'TEAM SUMMARY' not in header_text:
            box_score_tables.append(table)

    # Extract scores only from the first two player-stats tables
    # (later tables may have rebounding/shooting stats with different numbers)
    away_score = 0
    home_score = 0
    for table in box_score_tables[:2]:
        caption = table.select_one('caption')
        if caption:
            text = caption.get_text(strip=True)
            # Parse "Team Name SCORE" format
            parts = text.rsplit(' ', 1)
            if len(parts) == 2 and parts[1].isdigit():
                team_name = parts[0]
                score = int(parts[1])
                if team_name.lower() == away_team.lower() and away_score == 0:
                    away_score = score
                elif team_name.lower() == home_team.lower() and home_score == 0:
                    home_score = score

    # Extract period scores
    _, _, away_periods, home_periods = _extract_scores(soup)

    # Extract game info
    game_info = _extract_game_info(soup, url)

    # Parse player stats from each table
    away_players = []
    home_players = []

    if len(box_score_tables) >= 2:
        away_players = _extract_player_stats_sidearm(box_score_tables[0])
        home_players = _extract_player_stats_sidearm(box_score_tables[1])
    elif len(box_score_tables) == 1:
        # Single table with both teams
        all_players = _extract_player_stats_sidearm(box_score_tables[0])
        # Try to split by team (heuristic: look for separator rows)
        away_players = all_players[:len(all_players)//2]
        home_players = all_players[len(all_players)//2:]

    # Calculate team totals
    away_totals = _calculate_team_totals(away_players)
    home_totals = _calculate_team_totals(home_players)

    # Use totals for scores if not extracted
    if away_score == 0:
        away_score = away_totals.get('pts', 0)
    if home_score == 0:
        home_score = home_totals.get('pts', 0)

    # Build linescore
    linescore = {
        'away': {'periods': away_periods} if away_periods else {},
        'home': {'periods': home_periods} if home_periods else {},
    }

    # Generate game ID
    date_str = game_info.get('date', '')
    if date_str:
        date_yyyymmdd = format_date_yyyymmdd(date_str)
    else:
        date_yyyymmdd = '00000000'

    game_id = generate_game_id(date_str, home_team, 0, gender)

    # Build game data structure (same format as Sports Reference parser)
    game_data = {
        'game_id': game_id,
        'source': 'sidearm',
        'basic_info': {
            'away_team': away_team,
            'home_team': home_team,
            'away_score': away_score,
            'home_score': home_score,
            'date': date_str,
            'date_yyyymmdd': date_yyyymmdd,
            'venue': game_info.get('venue', ''),
            'attendance': game_info.get('attendance'),
            'gender': gender,
            'division': game_info.get('division'),  # D1, D2, D3, NAIA, etc.
        },
        'box_score': {
            'away': {
                'team': away_team,
                'players': away_players,
                'totals': away_totals,
            },
            'home': {
                'team': home_team,
                'players': home_players,
                'totals': home_totals,
            },
        },
        'linescore': linescore,
    }

    # Resolve venue
    resolved_venue = resolve_venue(game_data)
    if resolved_venue:
        game_data['basic_info']['venue'] = resolved_venue

    # Calculate milestones
    milestone_engine = MilestoneEngine(game_data)
    game_data = milestone_engine.process()

    # Check special events
    special_events_engine = SpecialEventsEngine(game_data)
    game_data = special_events_engine.detect()

    return game_data
