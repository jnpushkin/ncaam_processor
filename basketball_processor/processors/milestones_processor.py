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

        for milestone_type in milestone_types:
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
