"""
Play-by-play parser for extracting detailed game events.
"""

from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Comment
import re

from ..utils.helpers import safe_int


def extract_play_by_play(soup: BeautifulSoup, away_team: str, home_team: str) -> List[Dict[str, Any]]:
    """
    Extract play-by-play events from the game.

    Args:
        soup: BeautifulSoup object
        away_team: Away team name
        home_team: Home team name

    Returns:
        List of play dictionaries
    """
    plays = []

    # Find play-by-play table
    pbp_table = soup.find('table', {'id': 'pbp'})

    if not pbp_table:
        # Check comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'id="pbp"' in comment:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                pbp_table = comment_soup.find('table', {'id': 'pbp'})
                if pbp_table:
                    break

    if not pbp_table:
        return plays

    tbody = pbp_table.find('tbody')
    if not tbody:
        return plays

    current_half = 1
    current_score_away = 0
    current_score_home = 0

    for row in tbody.find_all('tr'):
        cells = row.find_all(['th', 'td'])
        if len(cells) < 2:
            continue

        # Check for period header
        if 'thead' in row.get('class', []):
            period_text = row.get_text(strip=True)
            if '2nd' in period_text:
                current_half = 2
            elif 'OT' in period_text:
                current_half += 1
            continue

        play = {
            'half': current_half,
            'time': '',
            'away_action': '',
            'home_action': '',
            'score_away': current_score_away,
            'score_home': current_score_home,
        }

        # Parse cells - typical format: Time, Away Event, Score, Home Event
        for cell in cells:
            data_stat = cell.get('data-stat', '')

            if data_stat == 'time':
                play['time'] = cell.get_text(strip=True)
            elif data_stat == 'away_team' or data_stat == 'away':
                play['away_action'] = cell.get_text(strip=True)
            elif data_stat == 'home_team' or data_stat == 'home':
                play['home_action'] = cell.get_text(strip=True)
            elif data_stat == 'score':
                score_text = cell.get_text(strip=True)
                score_match = re.match(r'(\d+)-(\d+)', score_text)
                if score_match:
                    current_score_away = safe_int(score_match.group(1), current_score_away)
                    current_score_home = safe_int(score_match.group(2), current_score_home)
                    play['score_away'] = current_score_away
                    play['score_home'] = current_score_home

        # Only add if there's an action
        if play['away_action'] or play['home_action']:
            plays.append(play)

    return plays


def classify_play_type(description: str) -> str:
    """
    Classify a play into categories.

    Args:
        description: Play description text

    Returns:
        Play type string
    """
    desc_lower = description.lower()

    if 'made' in desc_lower and ('3-pt' in desc_lower or 'three' in desc_lower):
        return 'three_pointer'
    elif 'made' in desc_lower and ('2-pt' in desc_lower or 'two' in desc_lower or 'dunk' in desc_lower or 'layup' in desc_lower):
        return 'two_pointer'
    elif 'made' in desc_lower and 'free throw' in desc_lower:
        return 'free_throw'
    elif 'missed' in desc_lower:
        return 'missed_shot'
    elif 'rebound' in desc_lower:
        if 'offensive' in desc_lower:
            return 'offensive_rebound'
        elif 'defensive' in desc_lower:
            return 'defensive_rebound'
        return 'rebound'
    elif 'turnover' in desc_lower or 'steal' in desc_lower:
        return 'turnover'
    elif 'foul' in desc_lower:
        return 'foul'
    elif 'assist' in desc_lower:
        return 'assist'
    elif 'block' in desc_lower:
        return 'block'
    elif 'timeout' in desc_lower:
        return 'timeout'
    elif 'substitution' in desc_lower or 'enters' in desc_lower:
        return 'substitution'

    return 'other'


def extract_scoring_runs(plays: List[Dict[str, Any]], min_run: int = 10) -> List[Dict[str, Any]]:
    """
    Identify scoring runs (e.g., 10-0 runs).

    Args:
        plays: List of play dictionaries
        min_run: Minimum point differential for a "run"

    Returns:
        List of scoring run dictionaries
    """
    runs = []

    if not plays:
        return runs

    # Track consecutive scoring
    current_run = {
        'team': None,
        'points': 0,
        'start_time': '',
        'end_time': '',
        'start_score': '',
    }

    prev_away = plays[0]['score_away']
    prev_home = plays[0]['score_home']

    for play in plays[1:]:
        away_scored = play['score_away'] - prev_away
        home_scored = play['score_home'] - prev_home

        if away_scored > 0 and home_scored == 0:
            if current_run['team'] == 'away':
                current_run['points'] += away_scored
                current_run['end_time'] = play['time']
            else:
                # Save previous run if significant
                if current_run['team'] and current_run['points'] >= min_run:
                    runs.append(current_run.copy())
                # Start new run
                current_run = {
                    'team': 'away',
                    'points': away_scored,
                    'start_time': play['time'],
                    'end_time': play['time'],
                    'start_score': f"{prev_away}-{prev_home}",
                }
        elif home_scored > 0 and away_scored == 0:
            if current_run['team'] == 'home':
                current_run['points'] += home_scored
                current_run['end_time'] = play['time']
            else:
                if current_run['team'] and current_run['points'] >= min_run:
                    runs.append(current_run.copy())
                current_run = {
                    'team': 'home',
                    'points': home_scored,
                    'start_time': play['time'],
                    'end_time': play['time'],
                    'start_score': f"{prev_away}-{prev_home}",
                }
        elif away_scored > 0 or home_scored > 0:
            # Both teams scored or run is broken
            if current_run['team'] and current_run['points'] >= min_run:
                runs.append(current_run.copy())
            current_run = {'team': None, 'points': 0, 'start_time': '', 'end_time': '', 'start_score': ''}

        prev_away = play['score_away']
        prev_home = play['score_home']

    # Check final run
    if current_run['team'] and current_run['points'] >= min_run:
        runs.append(current_run)

    return runs


def count_lead_changes(plays: List[Dict[str, Any]]) -> int:
    """
    Count the number of lead changes in the game.

    Args:
        plays: List of play dictionaries

    Returns:
        Number of lead changes
    """
    if not plays:
        return 0

    lead_changes = 0
    prev_leader = None  # 'away', 'home', or 'tie'

    for play in plays:
        away = play['score_away']
        home = play['score_home']

        if away > home:
            current_leader = 'away'
        elif home > away:
            current_leader = 'home'
        else:
            current_leader = 'tie'

        if prev_leader is not None and prev_leader != 'tie' and current_leader != 'tie':
            if prev_leader != current_leader:
                lead_changes += 1

        prev_leader = current_leader

    return lead_changes


def get_largest_lead(plays: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Find the largest lead for each team.

    Args:
        plays: List of play dictionaries

    Returns:
        Dictionary with largest leads for away and home teams
    """
    result = {
        'away': {'lead': 0, 'score': '', 'time': '', 'half': 0},
        'home': {'lead': 0, 'score': '', 'time': '', 'half': 0},
    }

    for play in plays:
        away = play['score_away']
        home = play['score_home']
        margin = away - home

        if margin > result['away']['lead']:
            result['away']['lead'] = margin
            result['away']['score'] = f"{away}-{home}"
            result['away']['time'] = play['time']
            result['away']['half'] = play['half']

        if -margin > result['home']['lead']:
            result['home']['lead'] = -margin
            result['home']['score'] = f"{away}-{home}"
            result['home']['time'] = play['time']
            result['home']['half'] = play['half']

    return result
