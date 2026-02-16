"""
ESPN play-by-play analysis engine.

Analyzes ESPN PBP data for:
- Team scoring runs (consecutive team points)
- Player point streaks (consecutive player points)
- Biggest comebacks
- Clutch scoring (final 5 minutes)
- Game-winning shots
"""

from typing import Dict, Any, List, Optional, Tuple
import re


class ESPNPlayByPlayEngine:
    """Analyze ESPN play-by-play data for advanced statistics."""

    def __init__(self, espn_pbp: Dict[str, Any], game_data: Dict[str, Any]):
        """
        Initialize the engine.

        Args:
            espn_pbp: Parsed ESPN play-by-play data from espn_pbp_scraper
            game_data: Game data dictionary with basic_info, etc.
        """
        self.espn_pbp = espn_pbp
        self.game_data = game_data
        self.plays = espn_pbp.get('plays', [])
        self.away_team = espn_pbp.get('away_team', '')
        self.home_team = espn_pbp.get('home_team', '')
        self.final_away = espn_pbp.get('away_score', 0)
        self.final_home = espn_pbp.get('home_score', 0)

        # Determine winner from actual game scores (more reliable than PBP last play)
        basic_info = game_data.get('basic_info', {})
        actual_away_score = basic_info.get('away_score', 0)
        actual_home_score = basic_info.get('home_score', 0)

        # Use actual game scores if available, otherwise fall back to PBP scores
        if actual_away_score > 0 or actual_home_score > 0:
            self.winner_side = 'home' if actual_home_score > actual_away_score else 'away'
        else:
            self.winner_side = 'home' if self.final_home > self.final_away else 'away'
        self.winner_team = self.home_team if self.winner_side == 'home' else self.away_team

    def analyze(self) -> Dict[str, Any]:
        """
        Run all analyses and return combined results.

        Returns:
            Dictionary with all analysis results
        """
        if not self.plays:
            return {}

        return {
            'team_scoring_runs': self.analyze_team_scoring_runs(),
            'player_point_streaks': self.analyze_player_point_streaks(),
            'biggest_comeback': self.analyze_biggest_comeback(),
            'clutch_scoring': self.analyze_clutch_scoring(),
            'game_winning_shots': self.analyze_game_winning_shots(),
        }

    def analyze_team_scoring_runs(self, min_points: int = 8) -> List[Dict[str, Any]]:
        """
        Find consecutive team scoring runs.

        A scoring run is consecutive points by one team with no opponent scoring.
        Resets when opponent scores any points.

        Args:
            min_points: Minimum points for a run to be tracked (default 8)

        Returns:
            List of scoring run dictionaries
        """
        runs = []
        if not self.plays:
            return runs

        current_run = {
            'team': None,
            'team_side': None,
            'points': 0,
            'start_time': '',
            'end_time': '',
            'start_period': 0,
            'end_period': 0,
            'start_score': '',
            'end_score': '',
        }

        prev_away = 0
        prev_home = 0

        for play in self.plays:
            if not play.get('scoring_play'):
                continue

            away_score = play['away_score']
            home_score = play['home_score']
            team_side = play.get('team_side', '')

            # Calculate points scored
            away_scored = away_score - prev_away
            home_scored = home_score - prev_home

            # Determine which team scored
            if team_side == 'away' and away_scored > 0:
                scoring_side = 'away'
                points = away_scored
            elif team_side == 'home' and home_scored > 0:
                scoring_side = 'home'
                points = home_scored
            else:
                # Both teams scored or unclear - end run
                if current_run['team'] and current_run['points'] >= min_points:
                    runs.append(current_run.copy())
                current_run = {'team': None, 'team_side': None, 'points': 0, 'start_time': '', 'end_time': '', 'start_period': 0, 'end_period': 0, 'start_score': '', 'end_score': ''}
                prev_away = away_score
                prev_home = home_score
                continue

            # Check if same team continues scoring
            if current_run['team_side'] == scoring_side:
                # Continue the run
                current_run['points'] += points
                current_run['end_time'] = play['time']
                current_run['end_period'] = play['period']
                current_run['end_score'] = f"{away_score}-{home_score}"
            else:
                # Different team scored - save previous run if significant
                if current_run['team'] and current_run['points'] >= min_points:
                    runs.append(current_run.copy())

                # Start new run
                current_run = {
                    'team': play['team'],
                    'team_side': scoring_side,
                    'points': points,
                    'start_time': play['time'],
                    'end_time': play['time'],
                    'start_period': play['period'],
                    'end_period': play['period'],
                    'start_score': f"{prev_away}-{prev_home}",
                    'end_score': f"{away_score}-{home_score}",
                }

            prev_away = away_score
            prev_home = home_score

        # Check final run
        if current_run['team'] and current_run['points'] >= min_points:
            runs.append(current_run)

        # Sort by points descending
        runs.sort(key=lambda x: x['points'], reverse=True)

        return runs

    def analyze_player_point_streaks(self, min_points: int = 6) -> List[Dict[str, Any]]:
        """
        Find consecutive individual player scoring streaks.

        A player streak is consecutive points by one player with no teammate scoring.
        Resets when ANY teammate scores (not just opponent).

        Args:
            min_points: Minimum points for a streak to be tracked (default 6)

        Returns:
            List of player streak dictionaries
        """
        streaks = []
        if not self.plays:
            return streaks

        current_streak = {
            'player': None,
            'team': None,
            'team_side': None,
            'points': 0,
            'start_time': '',
            'end_time': '',
            'start_period': 0,
            'end_period': 0,
            'start_score': '',
            'end_score': '',
        }

        prev_away = 0
        prev_home = 0

        for play in self.plays:
            if not play.get('scoring_play'):
                continue

            player = play.get('player', '')
            team_side = play.get('team_side', '')
            away_score = play['away_score']
            home_score = play['home_score']

            # Calculate points
            points = play.get('score_value', 0)
            if points == 0:
                points = (away_score - prev_away) + (home_score - prev_home)

            if not player or points <= 0:
                prev_away = away_score
                prev_home = home_score
                continue

            # Check if same player continues scoring
            if current_streak['player'] == player:
                # Continue the streak
                current_streak['points'] += points
                current_streak['end_time'] = play['time']
                current_streak['end_period'] = play['period']
                current_streak['end_score'] = f"{away_score}-{home_score}"
            else:
                # Different player scored
                # Save previous streak if significant
                if current_streak['player'] and current_streak['points'] >= min_points:
                    streaks.append(current_streak.copy())

                # Start new streak
                current_streak = {
                    'player': player,
                    'team': play['team'],
                    'team_side': team_side,
                    'points': points,
                    'start_time': play['time'],
                    'end_time': play['time'],
                    'start_period': play['period'],
                    'end_period': play['period'],
                    'start_score': f"{prev_away}-{prev_home}",
                    'end_score': f"{away_score}-{home_score}",
                }

            prev_away = away_score
            prev_home = home_score

        # Check final streak
        if current_streak['player'] and current_streak['points'] >= min_points:
            streaks.append(current_streak)

        # Sort by points descending
        streaks.sort(key=lambda x: x['points'], reverse=True)

        return streaks

    def analyze_biggest_comeback(self) -> Optional[Dict[str, Any]]:
        """
        Find the biggest comeback (largest deficit overcome by winning team).

        Returns:
            Dictionary with comeback info or None if no comeback
        """
        if not self.plays:
            return None

        # Track max deficit for the winning team
        max_deficit = 0
        max_deficit_time = ''
        max_deficit_period = 0
        max_deficit_score = ''

        for play in self.plays:
            away_score = play['away_score']
            home_score = play['home_score']
            margin = away_score - home_score  # Positive = away leading

            # Calculate deficit for winning team
            if self.winner_side == 'away':
                # Away won - check if they were behind
                deficit = -margin if margin < 0 else 0
            else:
                # Home won - check if they were behind
                deficit = margin if margin > 0 else 0

            if deficit > max_deficit:
                max_deficit = deficit
                max_deficit_time = play['time']
                max_deficit_period = play['period']
                max_deficit_score = f"{away_score}-{home_score}"

        if max_deficit == 0:
            return {
                'team': self.winner_team,
                'team_side': self.winner_side,
                'deficit': 0,
                'deficit_time': '',
                'deficit_period': 0,
                'deficit_score': '',
                'won': True,
                'never_trailed': True,
                'final_score': f"{self.final_away}-{self.final_home}",
            }

        return {
            'team': self.winner_team,
            'team_side': self.winner_side,
            'deficit': max_deficit,
            'deficit_time': max_deficit_time,
            'deficit_period': max_deficit_period,
            'deficit_score': max_deficit_score,
            'won': True,
            'never_trailed': False,
            'final_score': f"{self.final_away}-{self.final_home}",
        }

    def analyze_clutch_scoring(self, final_minutes: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """
        Find points scored in final minutes of regulation.

        Args:
            final_minutes: Minutes at end of game to consider "clutch" (default 5)

        Returns:
            Dictionary with 'away' and 'home' lists of player clutch scoring
        """
        result = {
            'away': [],
            'home': [],
        }

        if not self.plays:
            return result

        # Determine regulation periods
        # Men: 2 halves (period 2 is final), Women: 4 quarters (period 4 is final)
        gender = self.espn_pbp.get('gender', 'M')
        final_period = 2 if gender == 'M' else 4

        # Track scoring by player in clutch time
        clutch_stats = {
            'away': {},  # player -> {points, fg, ft, three}
            'home': {},
        }

        for play in self.plays:
            # Only count plays in final regulation period
            if play['period'] != final_period:
                continue

            # Check if within final minutes
            time_str = play.get('time', '')
            minutes = self._parse_time_minutes(time_str)
            if minutes is None or minutes >= final_minutes:
                continue

            # Only count scoring plays
            if not play.get('scoring_play'):
                continue

            player = play.get('player', '')
            team_side = play.get('team_side', '')
            points = play.get('score_value', 0)
            play_type = play.get('play_type', '')

            if not player or not team_side or points == 0:
                continue

            # Initialize player stats if needed
            if player not in clutch_stats[team_side]:
                clutch_stats[team_side][player] = {
                    'player': player,
                    'points': 0,
                    'fg': 0,
                    'ft': 0,
                    'three': 0,
                }

            stats = clutch_stats[team_side][player]
            stats['points'] += points

            # Track shot types
            if 'ft' in play_type or 'free_throw' in play_type:
                stats['ft'] += 1
            elif 'three' in play_type:
                stats['fg'] += 1
                stats['three'] += 1
            elif 'made' in play_type:
                stats['fg'] += 1

        # Convert to lists sorted by points
        for side in ['away', 'home']:
            result[side] = sorted(
                clutch_stats[side].values(),
                key=lambda x: x['points'],
                reverse=True
            )

        return result

    def analyze_game_winning_shots(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Find game-winning shots.

        Returns two types:
        1. clutch_go_ahead: Go-ahead shot in final 2 minutes of regulation
        2. decisive_shot: Last shot that gave winning team the lead (any time)

        Returns:
            Dictionary with 'clutch_go_ahead' and 'decisive_shot'
        """
        result = {
            'clutch_go_ahead': None,
            'decisive_shot': None,
        }

        if not self.plays:
            return result

        # Determine final regulation period
        gender = self.espn_pbp.get('gender', 'M')
        final_period = 2 if gender == 'M' else 4

        # Find the last lead change shot for winning team
        last_go_ahead = None
        clutch_go_ahead = None
        lead_change_count = 0

        prev_away = 0
        prev_home = 0

        for play in self.plays:
            if not play.get('scoring_play'):
                prev_away = play['away_score']
                prev_home = play['home_score']
                continue

            away_score = play['away_score']
            home_score = play['home_score']
            team_side = play.get('team_side', '')

            # Check if this play gave the lead to the scoring team
            prev_margin = prev_away - prev_home  # Positive = away leading
            curr_margin = away_score - home_score

            # Determine if this is a go-ahead shot
            is_go_ahead = False

            if team_side == 'away' and self.winner_side == 'away':
                # Away team scored - check if they took the lead
                if prev_margin <= 0 and curr_margin > 0:
                    is_go_ahead = True
            elif team_side == 'home' and self.winner_side == 'home':
                # Home team scored - check if they took the lead
                if prev_margin >= 0 and curr_margin < 0:
                    is_go_ahead = True

            if is_go_ahead:
                lead_change_count += 1
                shot_info = {
                    'player': play.get('player', ''),
                    'team': play.get('team', ''),
                    'team_side': team_side,
                    'time': play['time'],
                    'period': play['period'],
                    'points': play.get('score_value', 0),
                    'play_type': play.get('play_type', ''),
                    'score': f"{away_score}-{home_score}",
                    'text': play.get('text', ''),
                }

                # Track as decisive shot (last go-ahead)
                last_go_ahead = shot_info

                # Check if in clutch time (final 2 minutes of regulation)
                if play['period'] == final_period:
                    minutes = self._parse_time_minutes(play['time'])
                    if minutes is not None and minutes < 2:
                        clutch_go_ahead = shot_info

            prev_away = away_score
            prev_home = home_score

        result['decisive_shot'] = last_go_ahead
        result['clutch_go_ahead'] = clutch_go_ahead

        return result

    def _parse_time_minutes(self, time_str: str) -> Optional[float]:
        """
        Parse time string to minutes remaining.

        Args:
            time_str: Time string like "5:30" or "0:45"

        Returns:
            Minutes as float or None if unparseable
        """
        if not time_str:
            return None

        match = re.match(r'(\d+):(\d+)', time_str)
        if not match:
            return None

        minutes = int(match.group(1))
        seconds = int(match.group(2))

        return minutes + seconds / 60.0

    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the ESPN PBP analysis.

        Returns:
            Summary dictionary suitable for display
        """
        analysis = self.analyze()

        summary = {
            'has_espn_pbp': True,
            'play_count': len(self.plays),
        }

        # Summarize team runs
        runs = analysis.get('team_scoring_runs', [])
        if runs:
            best_run = runs[0]
            summary['best_team_run'] = {
                'team': best_run['team'],
                'points': best_run['points'],
                'period': best_run['end_period'],
            }

        # Summarize player streaks
        streaks = analysis.get('player_point_streaks', [])
        if streaks:
            best_streak = streaks[0]
            summary['best_player_streak'] = {
                'player': best_streak['player'],
                'team': best_streak['team'],
                'points': best_streak['points'],
            }

        # Summarize comeback
        comeback = analysis.get('biggest_comeback')
        if comeback and comeback['deficit'] > 0:
            summary['comeback'] = {
                'team': comeback['team'],
                'deficit': comeback['deficit'],
            }

        # Summarize clutch scoring
        clutch = analysis.get('clutch_scoring', {})
        top_clutch = []
        for side in ['away', 'home']:
            if clutch.get(side):
                top_clutch.extend(clutch[side][:2])  # Top 2 from each team
        if top_clutch:
            top_clutch.sort(key=lambda x: x['points'], reverse=True)
            summary['top_clutch_scorer'] = top_clutch[0]

        # Summarize game-winning shots
        gws = analysis.get('game_winning_shots', {})
        if gws.get('clutch_go_ahead'):
            summary['clutch_go_ahead'] = {
                'player': gws['clutch_go_ahead']['player'],
                'time': gws['clutch_go_ahead']['time'],
                'points': gws['clutch_go_ahead']['points'],
            }
        if gws.get('decisive_shot'):
            summary['decisive_shot'] = {
                'player': gws['decisive_shot']['player'],
                'time': gws['decisive_shot']['time'],
                'period': gws['decisive_shot']['period'],
            }

        return summary
