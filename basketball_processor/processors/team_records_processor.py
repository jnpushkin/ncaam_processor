"""
Team records and statistics processor.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
from collections import defaultdict

from .base_processor import BaseProcessor
from ..utils.helpers import safe_int, get_team_code
from ..utils.constants import CONFERENCES, get_conference, get_conference_for_date


class TeamRecordsProcessor(BaseProcessor):
    """Process team-level statistics and records."""

    def __init__(self, games: List[Dict[str, Any]]):
        super().__init__(games)
        self.team_stats = defaultdict(lambda: {
            'wins': 0,
            'losses': 0,
            'home_wins': 0,
            'home_losses': 0,
            'away_wins': 0,
            'away_losses': 0,
            'neutral_wins': 0,
            'neutral_losses': 0,
            'points_for': 0,
            'points_against': 0,
            'games': [],
            'game_results': [],  # Track game-by-game for streaks
            'conference': '',
            'conf_wins': 0,
            'conf_losses': 0,
        })
        self.head_to_head = defaultdict(list)  # Track all games between teams
        self.attendance_data = []  # Track attendance per game

    def process_team_records(self) -> Dict[str, pd.DataFrame]:
        """
        Process all team records.

        Returns:
            Dictionary containing:
            - 'team_records': Main team records DataFrame
            - 'matchup_matrix': Team vs team matrix
            - 'venue_records': Records by venue
            - 'team_streaks': Current and longest streaks
            - 'head_to_head_history': Detailed game history between teams
            - 'conference_standings': Conference-specific standings
            - 'home_away_splits': Detailed home/away/neutral splits
            - 'attendance_stats': Attendance statistics
        """
        self._aggregate_team_stats()

        return {
            'team_records': self._create_team_records_df(),
            'matchup_matrix': self._create_matchup_matrix(),
            'venue_records': self._create_venue_records_df(),
            'team_streaks': self._create_streaks_df(),
            'head_to_head_history': self._create_head_to_head_df(),
            'conference_standings': self._create_conference_standings_df(),
            'home_away_splits': self._create_home_away_splits_df(),
            'attendance_stats': self._create_attendance_stats_df(),
        }

    def _aggregate_team_stats(self):
        """Aggregate statistics for each team."""
        # Sort games by date first
        sorted_games = sorted(self.games,
            key=lambda g: g.get('basic_info', {}).get('date_yyyymmdd', ''))

        for game in sorted_games:
            basic_info = self.get_basic_info(game)
            game_id = self.get_game_id(game)
            date = basic_info.get('date', '')
            date_yyyymmdd = basic_info.get('date_yyyymmdd', '')

            away_team = basic_info.get('away_team', '')
            home_team = basic_info.get('home_team', '')
            away_score = safe_int(basic_info.get('away_score', 0))
            home_score = safe_int(basic_info.get('home_score', 0))
            venue = basic_info.get('venue', '')
            attendance = basic_info.get('attendance')
            is_neutral = basic_info.get('neutral_site', False)

            # Auto-detect conference games - check if both teams are in the same conference
            # Use date-aware lookup to handle historical conference affiliations
            is_conference = basic_info.get('conference_game', False)
            if not is_conference:
                away_conf = get_conference_for_date(away_team, date_yyyymmdd)
                home_conf = get_conference_for_date(home_team, date_yyyymmdd)
                if away_conf and home_conf and away_conf == home_conf:
                    is_conference = True

            if not away_team or not home_team:
                continue

            # Track attendance
            if attendance:
                self.attendance_data.append({
                    'date': date,
                    'game_id': game_id,
                    'venue': venue,
                    'home_team': home_team,
                    'away_team': away_team,
                    'attendance': attendance,
                })

            # Determine winner
            away_won = away_score > home_score

            # Track head-to-head (both directions)
            matchup_key = tuple(sorted([away_team, home_team]))
            self.head_to_head[matchup_key].append({
                'date': date,
                'date_yyyymmdd': date_yyyymmdd,
                'game_id': game_id,
                'away_team': away_team,
                'home_team': home_team,
                'away_score': away_score,
                'home_score': home_score,
                'winner': away_team if away_won else home_team,
                'venue': venue,
            })

            # Update away team stats
            self.team_stats[away_team]['points_for'] += away_score
            self.team_stats[away_team]['points_against'] += home_score
            self.team_stats[away_team]['games'].append(game_id)
            self.team_stats[away_team]['game_results'].append({
                'date': date_yyyymmdd,
                'won': away_won,
                'opponent': home_team,
            })

            # Update home team stats
            self.team_stats[home_team]['points_for'] += home_score
            self.team_stats[home_team]['points_against'] += away_score
            self.team_stats[home_team]['games'].append(game_id)
            self.team_stats[home_team]['game_results'].append({
                'date': date_yyyymmdd,
                'won': not away_won,
                'opponent': away_team,
            })

            if away_won:
                self.team_stats[away_team]['wins'] += 1
                self.team_stats[home_team]['losses'] += 1

                if is_neutral:
                    self.team_stats[away_team]['neutral_wins'] += 1
                    self.team_stats[home_team]['neutral_losses'] += 1
                else:
                    self.team_stats[away_team]['away_wins'] += 1
                    self.team_stats[home_team]['home_losses'] += 1

                if is_conference:
                    self.team_stats[away_team]['conf_wins'] += 1
                    self.team_stats[home_team]['conf_losses'] += 1
            else:
                self.team_stats[away_team]['losses'] += 1
                self.team_stats[home_team]['wins'] += 1

                if is_neutral:
                    self.team_stats[away_team]['neutral_losses'] += 1
                    self.team_stats[home_team]['neutral_wins'] += 1
                else:
                    self.team_stats[away_team]['away_losses'] += 1
                    self.team_stats[home_team]['home_wins'] += 1

                if is_conference:
                    self.team_stats[away_team]['conf_losses'] += 1
                    self.team_stats[home_team]['conf_wins'] += 1

        # Determine conferences for teams (using get_conference which handles aliases)
        for team in self.team_stats.keys():
            conf = get_conference(team)
            if conf:
                self.team_stats[team]['conference'] = conf

    def _create_team_records_df(self) -> pd.DataFrame:
        """Create team records DataFrame."""
        rows = []

        for team, stats in self.team_stats.items():
            total_games = stats['wins'] + stats['losses']
            if total_games == 0:
                continue

            win_pct = round(stats['wins'] / total_games, 3) if total_games > 0 else 0
            ppg = round(stats['points_for'] / total_games, 1) if total_games > 0 else 0
            papg = round(stats['points_against'] / total_games, 1) if total_games > 0 else 0
            diff = round(ppg - papg, 1)

            rows.append({
                'Team': team,
                'Code': get_team_code(team),
                'Conference': stats.get('conference', '') or 'Independent',
                'Games': total_games,
                'Wins': stats['wins'],
                'Losses': stats['losses'],
                'Win%': win_pct,
                'Home W': stats['home_wins'],
                'Home L': stats['home_losses'],
                'Away W': stats['away_wins'],
                'Away L': stats['away_losses'],
                'PPG': ppg,
                'PAPG': papg,
                'Diff': diff,
                'PF': stats['points_for'],
                'PA': stats['points_against'],
            })

        # Sort by wins descending
        rows.sort(key=lambda x: (x['Wins'], x['Win%']), reverse=True)

        columns = [
            'Team', 'Code', 'Conference', 'Games', 'Wins', 'Losses', 'Win%',
            'Home W', 'Home L', 'Away W', 'Away L',
            'PPG', 'PAPG', 'Diff', 'PF', 'PA'
        ]

        return self.create_dataframe(rows, columns)

    def _create_matchup_matrix(self) -> pd.DataFrame:
        """Create team vs team matchup matrix."""
        matchups = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0}))

        for game in self.games:
            basic_info = self.get_basic_info(game)
            away_team = basic_info.get('away_team', '')
            home_team = basic_info.get('home_team', '')
            away_score = safe_int(basic_info.get('away_score', 0))
            home_score = safe_int(basic_info.get('home_score', 0))

            if not away_team or not home_team:
                continue

            if away_score > home_score:
                matchups[away_team][home_team]['wins'] += 1
                matchups[home_team][away_team]['losses'] += 1
            else:
                matchups[away_team][home_team]['losses'] += 1
                matchups[home_team][away_team]['wins'] += 1

        # Create list of all teams
        all_teams = sorted(set(matchups.keys()))

        rows = []
        for team in all_teams:
            row = {'Team': team}
            for opponent in all_teams:
                if team == opponent:
                    row[opponent] = '-'
                else:
                    w = matchups[team][opponent]['wins']
                    l = matchups[team][opponent]['losses']
                    if w + l > 0:
                        row[opponent] = f"{w}-{l}"
                    else:
                        row[opponent] = ''
            rows.append(row)

        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def _create_venue_records_df(self) -> pd.DataFrame:
        """Create records by venue."""
        from ..utils.venue_resolver import parse_venue_components

        venue_stats = defaultdict(lambda: {
            'games': 0,
            'home_points': 0,
            'away_points': 0,
            'home_wins': 0,
            'away_wins': 0,
        })

        for game in self.games:
            basic_info = self.get_basic_info(game)
            venue = basic_info.get('venue', '')
            if not venue:
                venue = 'Unknown'

            away_score = safe_int(basic_info.get('away_score', 0))
            home_score = safe_int(basic_info.get('home_score', 0))

            venue_stats[venue]['games'] += 1
            venue_stats[venue]['home_points'] += home_score
            venue_stats[venue]['away_points'] += away_score

            if home_score > away_score:
                venue_stats[venue]['home_wins'] += 1
            else:
                venue_stats[venue]['away_wins'] += 1

        rows = []
        for venue, stats in venue_stats.items():
            games = stats['games']
            avg_home = round(stats['home_points'] / games, 1) if games > 0 else 0
            avg_away = round(stats['away_points'] / games, 1) if games > 0 else 0

            # Parse venue into components
            venue_parts = parse_venue_components(venue)

            rows.append({
                'Venue': venue_parts['name'] or venue,
                'City': venue_parts['city'],
                'State': venue_parts['state'],
                'Games': games,
                'Home Wins': stats['home_wins'],
                'Away Wins': stats['away_wins'],
                'Avg Home Pts': avg_home,
                'Avg Away Pts': avg_away,
            })

        rows.sort(key=lambda x: x['Games'], reverse=True)

        return self.create_dataframe(rows)

    def _create_streaks_df(self) -> pd.DataFrame:
        """Create team streaks DataFrame (current and longest win/loss streaks)."""
        rows = []

        for team, stats in self.team_stats.items():
            results = stats.get('game_results', [])
            if not results:
                continue

            # Calculate current streak
            current_streak = 0
            current_type = None
            for game in reversed(results):
                if current_type is None:
                    current_type = 'W' if game['won'] else 'L'
                    current_streak = 1
                elif (game['won'] and current_type == 'W') or (not game['won'] and current_type == 'L'):
                    current_streak += 1
                else:
                    break

            # Calculate longest win streak
            longest_win = 0
            current_win = 0
            for game in results:
                if game['won']:
                    current_win += 1
                    longest_win = max(longest_win, current_win)
                else:
                    current_win = 0

            # Calculate longest loss streak
            longest_loss = 0
            current_loss = 0
            for game in results:
                if not game['won']:
                    current_loss += 1
                    longest_loss = max(longest_loss, current_loss)
                else:
                    current_loss = 0

            rows.append({
                'Team': team,
                'Current Streak': f"{current_type}{current_streak}" if current_type else '-',
                'Current Streak Count': current_streak if current_type == 'W' else -current_streak,
                'Longest Win Streak': longest_win,
                'Longest Loss Streak': longest_loss,
                'Last 5': self._get_last_n_record(results, 5),
                'Last 10': self._get_last_n_record(results, 10),
            })

        rows.sort(key=lambda x: x['Current Streak Count'], reverse=True)
        return self.create_dataframe(rows)

    def _get_last_n_record(self, results: list, n: int) -> str:
        """Get W-L record for last N games."""
        last_n = results[-n:] if len(results) >= n else results
        wins = sum(1 for g in last_n if g['won'])
        losses = len(last_n) - wins
        return f"{wins}-{losses}"

    def _create_head_to_head_df(self) -> pd.DataFrame:
        """Create head-to-head matchup history."""
        rows = []

        for matchup_key, games in self.head_to_head.items():
            team1, team2 = matchup_key

            # Sort games by date
            games_sorted = sorted(games, key=lambda x: x['date_yyyymmdd'])

            team1_wins = sum(1 for g in games if g['winner'] == team1)
            team2_wins = len(games) - team1_wins

            for game in games_sorted:
                rows.append({
                    'Team 1': team1,
                    'Team 2': team2,
                    'Series': f"{team1_wins}-{team2_wins}",
                    'Date': game['date'],
                    'Away Team': game['away_team'],
                    'Home Team': game['home_team'],
                    'Score': f"{game['away_score']}-{game['home_score']}",
                    'Winner': game['winner'],
                    'Venue': game['venue'],
                    'GameID': game['game_id'],
                })

        return self.create_dataframe(rows)

    def _create_conference_standings_df(self) -> pd.DataFrame:
        """Create conference standings DataFrame."""
        rows = []

        for team, stats in self.team_stats.items():
            conf = stats.get('conference', '')
            total_games = stats['wins'] + stats['losses']
            if total_games == 0:
                continue

            conf_games = stats['conf_wins'] + stats['conf_losses']

            rows.append({
                'Conference': conf if conf else 'Independent',
                'Team': team,
                'Conf W': stats['conf_wins'],
                'Conf L': stats['conf_losses'],
                'Conf Win%': round(stats['conf_wins'] / conf_games, 3) if conf_games > 0 else 0,
                'Overall W': stats['wins'],
                'Overall L': stats['losses'],
                'Overall Win%': round(stats['wins'] / total_games, 3),
            })

        # Sort by conference, then by conf win%, then by overall win%
        rows.sort(key=lambda x: (x['Conference'], -x['Conf Win%'], -x['Overall Win%']))

        return self.create_dataframe(rows)

    def _create_home_away_splits_df(self) -> pd.DataFrame:
        """Create detailed home/away/neutral splits DataFrame."""
        rows = []

        for team, stats in self.team_stats.items():
            total_games = stats['wins'] + stats['losses']
            if total_games == 0:
                continue

            home_games = stats['home_wins'] + stats['home_losses']
            away_games = stats['away_wins'] + stats['away_losses']
            neutral_games = stats['neutral_wins'] + stats['neutral_losses']

            rows.append({
                'Team': team,
                'Home W': stats['home_wins'],
                'Home L': stats['home_losses'],
                'Home Win%': round(stats['home_wins'] / home_games, 3) if home_games > 0 else 0,
                'Away W': stats['away_wins'],
                'Away L': stats['away_losses'],
                'Away Win%': round(stats['away_wins'] / away_games, 3) if away_games > 0 else 0,
                'Neutral W': stats['neutral_wins'],
                'Neutral L': stats['neutral_losses'],
                'Neutral Win%': round(stats['neutral_wins'] / neutral_games, 3) if neutral_games > 0 else 0,
                'Total W': stats['wins'],
                'Total L': stats['losses'],
            })

        rows.sort(key=lambda x: (x['Total W'], x['Home Win%']), reverse=True)
        return self.create_dataframe(rows)

    def _create_attendance_stats_df(self) -> pd.DataFrame:
        """Create attendance statistics DataFrame."""
        if not self.attendance_data:
            return pd.DataFrame()

        # Team-level attendance
        team_attendance = defaultdict(list)
        for record in self.attendance_data:
            team_attendance[record['home_team']].append(record['attendance'])

        rows = []
        for team, attendances in team_attendance.items():
            rows.append({
                'Team': team,
                'Home Games': len(attendances),
                'Total Attendance': sum(attendances),
                'Avg Attendance': round(sum(attendances) / len(attendances)),
                'Max Attendance': max(attendances),
                'Min Attendance': min(attendances),
            })

        rows.sort(key=lambda x: x['Avg Attendance'], reverse=True)
        return self.create_dataframe(rows)


class GameLogProcessor(BaseProcessor):
    """Process game log."""

    def create_game_log(self) -> pd.DataFrame:
        """Create chronological game log."""
        from ..utils.venue_resolver import parse_venue_components

        rows = []

        for game in self.games:
            basic_info = self.get_basic_info(game)
            special_events = game.get('special_events', {})

            notes = []
            if special_events.get('overtime_game'):
                ot = special_events.get('overtime_periods', 1)
                notes.append(f"{'OT' if ot == 1 else f'{ot}OT'}")
            if special_events.get('blowout'):
                notes.append(f"+{special_events.get('blowout_margin', 0)}")

            # Parse venue into components
            venue_full = basic_info.get('venue', '')
            venue_parts = parse_venue_components(venue_full)

            rows.append({
                'Date': basic_info.get('date', ''),
                'DateSort': basic_info.get('date_yyyymmdd', ''),
                'Away Team': basic_info.get('away_team', ''),
                'Away Score': safe_int(basic_info.get('away_score', 0)),
                'Home Team': basic_info.get('home_team', ''),
                'Home Score': safe_int(basic_info.get('home_score', 0)),
                'Venue': venue_parts['name'],
                'City': venue_parts['city'],
                'State': venue_parts['state'],
                'Notes': ', '.join(notes) if notes else '',
                'GameID': self.get_game_id(game),
                'HomeTeamSlug': basic_info.get('home_team_slug', ''),
                'SportsRefURL': basic_info.get('sports_ref_url', ''),
                'Gender': game.get('gender', 'M'),
            })

        # Sort by date descending (using YYYYMMDD format for proper chronological order)
        rows.sort(key=lambda x: x.get('DateSort', ''), reverse=True)

        columns = [
            'Date', 'DateSort', 'Away Team', 'Away Score', 'Home Team', 'Home Score',
            'Venue', 'City', 'State', 'Notes', 'GameID', 'HomeTeamSlug', 'SportsRefURL', 'Gender'
        ]

        return self.create_dataframe(rows, columns)
