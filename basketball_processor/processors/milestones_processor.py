"""
Milestones aggregation processor.
"""

from typing import Dict, List, Any, Optional
import pandas as pd

from .base_processor import BaseProcessor
from ..utils.helpers import safe_int


class MilestonesProcessor(BaseProcessor):
    """Process and compile all milestones across games."""

    def __init__(self, games: List[Dict[str, Any]]):
        super().__init__(games)
        self.all_milestones = {}

    def process_all_milestones(self) -> Dict[str, pd.DataFrame]:
        """
        Process all milestones from all games.

        Returns:
            Dictionary of milestone type -> DataFrame
        """
        # Standard box-score based milestones
        milestone_types = [
            'double_doubles',
            'triple_doubles',
            'twenty_point_games',
            'thirty_point_games',
            'forty_point_games',
            'ten_rebound_games',
            'fifteen_rebound_games',
            'ten_assist_games',
            'five_block_games',
            'five_steal_games',
            'five_three_games',
            'hot_shooting_games',
            'perfect_ft_games',
            'twenty_ten_games',
        ]

        # ESPN PBP-based milestones
        espn_pbp_milestone_types = [
            'ten_point_team_run',
            'twelve_point_team_run',
            'fifteen_point_team_run',
            'eight_point_player_streak',
            'ten_point_player_streak',
            'ten_point_comeback',
            'fifteen_point_comeback',
            'twenty_point_comeback',
            'clutch_ten_points',
            'clutch_fifteen_points',
            'clutch_go_ahead_shot',
            'game_winning_shot',
        ]

        # Combine all milestone types
        all_milestone_types = milestone_types + espn_pbp_milestone_types

        for milestone_type in all_milestone_types:
            self.all_milestones[milestone_type] = []

        # Collect milestones from all games
        for game in self.games:
            basic_info = self.get_basic_info(game)
            game_id = self.get_game_id(game)
            date = basic_info.get('date', '')
            gender = game.get('gender', 'M')
            away_score = safe_int(basic_info.get('away_score', 0))
            home_score = safe_int(basic_info.get('home_score', 0))

            milestone_stats = game.get('milestone_stats', {})

            # Process standard box-score milestones
            for milestone_type in milestone_types:
                entries = milestone_stats.get(milestone_type, [])

                for entry in entries:
                    team = entry.get('team', '')
                    opponent = entry.get('opponent', '')
                    side = entry.get('side', '')

                    # Determine score display
                    if side == 'home':
                        score = f"{home_score}-{away_score}"
                    else:
                        score = f"{away_score}-{home_score}"

                    self.all_milestones[milestone_type].append({
                        'Date': date,
                        'Player': entry.get('player', ''),
                        'Player ID': entry.get('player_id', ''),
                        'Team': team,
                        'Opponent': opponent,
                        'Score': score,
                        'Detail': entry.get('detail', ''),
                        'GameID': game_id,
                        'Gender': gender,
                        **entry.get('stats', {}),
                    })

            # Process ESPN PBP milestones
            espn_pbp = game.get('espn_pbp_analysis', {})
            if espn_pbp:
                self._process_espn_pbp_milestones(
                    game, espn_pbp, game_id, date, gender,
                    basic_info, away_score, home_score
                )

        # Convert to DataFrames
        result = {}
        for milestone_type, entries in self.all_milestones.items():
            if entries:
                df = pd.DataFrame(entries)
                # Sort by date descending
                if 'Date' in df.columns:
                    df = df.sort_values('Date', ascending=False)
                result[milestone_type] = df
            else:
                result[milestone_type] = pd.DataFrame()

        return result

    def _process_espn_pbp_milestones(
        self,
        game: Dict[str, Any],
        espn_pbp: Dict[str, Any],
        game_id: str,
        date: str,
        gender: str,
        basic_info: Dict[str, Any],
        away_score: int,
        home_score: int
    ) -> None:
        """
        Process ESPN play-by-play analysis into milestones.

        Args:
            game: Full game data dictionary
            espn_pbp: ESPN PBP analysis from ESPNPlayByPlayEngine
            game_id: Game identifier
            date: Game date
            gender: 'M' or 'W'
            basic_info: Game basic info
            away_score: Away team final score
            home_score: Home team final score
        """
        away_team = basic_info.get('away_team', '')
        home_team = basic_info.get('home_team', '')

        # Process team scoring runs
        runs = espn_pbp.get('team_scoring_runs', [])
        for run in runs:
            points = run.get('points', 0)
            team = run.get('team', '')
            team_side = run.get('team_side', '')
            opponent = home_team if team_side == 'away' else away_team
            period = run.get('end_period', 1)

            base_entry = {
                'Date': date,
                'Player': '',  # Team milestones don't have a player
                'Player ID': '',
                'Team': team,
                'Opponent': opponent,
                'Score': f"{away_score}-{home_score}",
                'GameID': game_id,
                'Gender': gender,
                'stats': {'points': points, 'period': period},
            }

            # Check thresholds (largest first to avoid duplicates)
            if points >= 15:
                self.all_milestones['fifteen_point_team_run'].append({
                    **base_entry,
                    'Detail': f"{points}-0 run in {'H' if period <= 2 else 'OT'}{period}",
                })
            elif points >= 12:
                self.all_milestones['twelve_point_team_run'].append({
                    **base_entry,
                    'Detail': f"{points}-0 run in {'H' if period <= 2 else 'OT'}{period}",
                })
            elif points >= 10:
                self.all_milestones['ten_point_team_run'].append({
                    **base_entry,
                    'Detail': f"{points}-0 run in {'H' if period <= 2 else 'OT'}{period}",
                })

        # Process player point streaks
        streaks = espn_pbp.get('player_point_streaks', [])
        for streak in streaks:
            points = streak.get('points', 0)
            player = streak.get('player', '')
            team = streak.get('team', '')
            team_side = streak.get('team_side', '')
            opponent = home_team if team_side == 'away' else away_team

            base_entry = {
                'Date': date,
                'Player': player,
                'Player ID': '',  # ESPN doesn't provide player IDs
                'Team': team,
                'Opponent': opponent,
                'Score': f"{away_score}-{home_score}",
                'GameID': game_id,
                'Gender': gender,
                'stats': {'points': points},
            }

            if points >= 10:
                self.all_milestones['ten_point_player_streak'].append({
                    **base_entry,
                    'Detail': f"{points} consecutive points",
                })
            elif points >= 8:
                self.all_milestones['eight_point_player_streak'].append({
                    **base_entry,
                    'Detail': f"{points} consecutive points",
                })

        # Process comebacks
        comeback = espn_pbp.get('biggest_comeback')
        if comeback and comeback.get('won'):
            deficit = comeback.get('deficit', 0)
            team = comeback.get('team', '')
            team_side = comeback.get('team_side', '')
            opponent = home_team if team_side == 'away' else away_team

            base_entry = {
                'Date': date,
                'Player': '',  # Team milestone
                'Player ID': '',
                'Team': team,
                'Opponent': opponent,
                'Score': f"{away_score}-{home_score}",
                'GameID': game_id,
                'Gender': gender,
                'stats': {'deficit': deficit},
            }

            if deficit >= 20:
                self.all_milestones['twenty_point_comeback'].append({
                    **base_entry,
                    'Detail': f"Overcame {deficit}-point deficit to win",
                })
            elif deficit >= 15:
                self.all_milestones['fifteen_point_comeback'].append({
                    **base_entry,
                    'Detail': f"Overcame {deficit}-point deficit to win",
                })
            elif deficit >= 10:
                self.all_milestones['ten_point_comeback'].append({
                    **base_entry,
                    'Detail': f"Overcame {deficit}-point deficit to win",
                })

        # Process clutch scoring
        clutch = espn_pbp.get('clutch_scoring', {})
        for side in ['away', 'home']:
            side_clutch = clutch.get(side, [])
            for player_stats in side_clutch:
                points = player_stats.get('points', 0)
                player = player_stats.get('player', '')
                team = away_team if side == 'away' else home_team
                opponent = home_team if side == 'away' else away_team

                base_entry = {
                    'Date': date,
                    'Player': player,
                    'Player ID': '',
                    'Team': team,
                    'Opponent': opponent,
                    'Score': f"{away_score}-{home_score}",
                    'GameID': game_id,
                    'Gender': gender,
                    'stats': {
                        'points': points,
                        'fg': player_stats.get('fg', 0),
                        'ft': player_stats.get('ft', 0),
                        'three': player_stats.get('three', 0),
                    },
                }

                if points >= 15:
                    self.all_milestones['clutch_fifteen_points'].append({
                        **base_entry,
                        'Detail': f"{points} pts in final 5 min",
                    })
                elif points >= 10:
                    self.all_milestones['clutch_ten_points'].append({
                        **base_entry,
                        'Detail': f"{points} pts in final 5 min",
                    })

        # Process game-winning shots
        gws = espn_pbp.get('game_winning_shots', {})

        # Clutch go-ahead (final 2 minutes)
        clutch_go_ahead = gws.get('clutch_go_ahead')
        if clutch_go_ahead:
            player = clutch_go_ahead.get('player', '')
            team = clutch_go_ahead.get('team', '')
            team_side = clutch_go_ahead.get('team_side', '')
            opponent = home_team if team_side == 'away' else away_team
            shot_time = clutch_go_ahead.get('time', '')
            points = clutch_go_ahead.get('points', 0)

            self.all_milestones['clutch_go_ahead_shot'].append({
                'Date': date,
                'Player': player,
                'Player ID': '',
                'Team': team,
                'Opponent': opponent,
                'Score': f"{away_score}-{home_score}",
                'Detail': f"Go-ahead {points}pts with {shot_time} left",
                'GameID': game_id,
                'Gender': gender,
                'stats': {'points': points, 'time': shot_time},
            })

        # Decisive (game-winning) shot
        decisive = gws.get('decisive_shot')
        if decisive:
            player = decisive.get('player', '')
            team = decisive.get('team', '')
            team_side = decisive.get('team_side', '')
            opponent = home_team if team_side == 'away' else away_team
            shot_score = decisive.get('score', '')
            points = decisive.get('points', 0)

            self.all_milestones['game_winning_shot'].append({
                'Date': date,
                'Player': player,
                'Player ID': '',
                'Team': team,
                'Opponent': opponent,
                'Score': f"{away_score}-{home_score}",
                'Detail': f"Game-winning shot ({shot_score})",
                'GameID': game_id,
                'Gender': gender,
                'stats': {'points': points, 'shot_score': shot_score},
            })

    def get_milestone_summary(self) -> pd.DataFrame:
        """
        Get summary of all milestones.

        Returns:
            DataFrame with milestone counts
        """
        if not self.all_milestones:
            self.process_all_milestones()

        summary_rows = []
        for milestone_type, entries in self.all_milestones.items():
            display_name = milestone_type.replace('_', ' ').title()
            summary_rows.append({
                'Milestone': display_name,
                'Count': len(entries),
            })

        # Sort by count descending
        summary_rows.sort(key=lambda x: x['Count'], reverse=True)

        return pd.DataFrame(summary_rows)

    def get_player_milestone_counts(self) -> pd.DataFrame:
        """
        Get milestone counts by player.

        Returns:
            DataFrame with players and their milestone counts
        """
        if not self.all_milestones:
            self.process_all_milestones()

        player_counts = {}

        for milestone_type, entries in self.all_milestones.items():
            for entry in entries:
                player = entry.get('Player', '')
                if not player:
                    continue

                if player not in player_counts:
                    player_counts[player] = {
                        'Player': player,
                        'Player ID': entry.get('Player ID', ''),
                        'Total': 0,
                    }

                player_counts[player]['Total'] += 1

                # Track specific milestone types
                col_name = milestone_type.replace('_', ' ').title()
                if col_name not in player_counts[player]:
                    player_counts[player][col_name] = 0
                player_counts[player][col_name] += 1

        rows = list(player_counts.values())
        rows.sort(key=lambda x: x['Total'], reverse=True)

        return pd.DataFrame(rows) if rows else pd.DataFrame()


class OvertimeGamesProcessor(BaseProcessor):
    """Process overtime games."""

    def process_overtime_games(self) -> pd.DataFrame:
        """Get all overtime games."""
        ot_games = []

        for game in self.games:
            special_events = game.get('special_events', {})
            if special_events.get('overtime_game'):
                basic_info = self.get_basic_info(game)
                ot_periods = special_events.get('overtime_periods', 1)

                ot_games.append({
                    'Date': basic_info.get('date', ''),
                    'Away Team': basic_info.get('away_team', ''),
                    'Home Team': basic_info.get('home_team', ''),
                    'Score': f"{basic_info.get('away_score', 0)}-{basic_info.get('home_score', 0)}",
                    'OT Periods': ot_periods,
                    'Venue': basic_info.get('venue', ''),
                    'GameID': self.get_game_id(game),
                })

        df = pd.DataFrame(ot_games) if ot_games else pd.DataFrame()
        if not df.empty and 'Date' in df.columns:
            df = df.sort_values('Date', ascending=False)
        return df


class BlowoutGamesProcessor(BaseProcessor):
    """Process blowout games (20+ point margin)."""

    def process_blowout_games(self) -> pd.DataFrame:
        """Get all blowout games."""
        blowouts = []

        for game in self.games:
            special_events = game.get('special_events', {})
            if special_events.get('blowout'):
                basic_info = self.get_basic_info(game)
                margin = special_events.get('blowout_margin', 0)
                winner_side = special_events.get('blowout_winner', '')

                winner = basic_info.get(f'{winner_side}_team', '') if winner_side else ''
                loser_side = 'home' if winner_side == 'away' else 'away'
                loser = basic_info.get(f'{loser_side}_team', '')

                blowouts.append({
                    'Date': basic_info.get('date', ''),
                    'Winner': winner,
                    'Loser': loser,
                    'Score': f"{basic_info.get('away_score', 0)}-{basic_info.get('home_score', 0)}",
                    'Margin': margin,
                    'Venue': basic_info.get('venue', ''),
                    'GameID': self.get_game_id(game),
                })

        df = pd.DataFrame(blowouts) if blowouts else pd.DataFrame()
        if not df.empty:
            df = df.sort_values('Margin', ascending=False)
        return df
