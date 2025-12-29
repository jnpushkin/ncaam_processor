"""
Milestone detection engine for basketball achievements.
"""

from typing import Dict, Any, List, Optional
from ..utils.helpers import safe_int, safe_float, calculate_game_score
from ..utils.stat_utils import (
    is_double_double,
    is_triple_double,
    get_double_double_categories,
    is_hot_shooting,
    is_perfect_ft,
    is_near_double_double,
    get_near_double_double_detail,
    calculate_four_factors,
    calculate_pace,
)
from ..utils.constants import MILESTONE_THRESHOLDS, MILESTONE_STAT_CONFIGS


class MilestoneEngine:
    """Detect milestones during game parsing."""

    def __init__(self, game_data: Dict[str, Any]):
        self.game_data = game_data
        self.milestones = {
            # Multi-category achievements
            'double_doubles': [],
            'triple_doubles': [],
            'near_double_doubles': [],
            'near_triple_doubles': [],
            'five_by_five': [],  # 5+ in 5 categories

            # Scoring milestones
            'fifty_point_games': [],
            'forty_point_games': [],
            'thirty_point_games': [],
            'twenty_five_point_games': [],
            'twenty_point_games': [],

            # Rebounding milestones
            'twenty_rebound_games': [],
            'fifteen_rebound_games': [],
            'ten_rebound_games': [],

            # Assist milestones
            'twenty_assist_games': [],
            'fifteen_assist_games': [],
            'ten_assist_games': [],

            # Defensive milestones
            'ten_block_games': [],
            'five_block_games': [],
            'ten_steal_games': [],
            'five_steal_games': [],
            'defensive_monster': [],  # 7+ combined blocks + steals

            # Three-pointer milestones
            'ten_three_games': [],
            'seven_three_games': [],
            'five_three_games': [],
            'perfect_from_three': [],  # 100% 3PT with 4+ attempts

            # Efficiency milestones
            'hot_shooting_games': [],
            'perfect_ft_games': [],
            'perfect_fg_games': [],  # 100% FG with 5+ attempts
            'efficient_scoring': [],  # 65%+ TS with 15+ pts

            # Combined milestones
            'thirty_ten_games': [],  # 30+ pts, 10+ reb
            'twenty_ten_games': [],
            'twenty_ten_five_games': [],
            'points_assists_dd': [],  # 10+ pts, 10+ ast
            'all_around_game': [],  # 5+ in 5 categories

            # Clean games
            'zero_turnover_games': [],  # 0 TO with 20+ min

            # Rare feats
            'quadruple_double': [],  # 10+ in 4 categories
        }
        self.game_stats = {
            'pace': 0,
            'four_factors': {},
        }

    def process(self) -> Dict[str, Any]:
        """Run all milestone checks and add to game_data."""
        self._process_player_milestones()
        self._calculate_game_stats()
        self.game_data['milestone_stats'] = self.milestones
        self.game_data['game_stats'] = self.game_stats
        return self.game_data

    def _calculate_game_stats(self):
        """Calculate game-level advanced stats."""
        box_score = self.game_data.get('box_score', {})

        away_totals = box_score.get('away', {}).get('totals', {})
        home_totals = box_score.get('home', {}).get('totals', {})

        if away_totals and home_totals:
            # Calculate pace
            basic_info = self.game_data.get('basic_info', {})
            linescore = self.game_data.get('linescore', {})

            # Determine game length (40 min + OT)
            game_minutes = 40
            if linescore:
                away_ot = linescore.get('away', {}).get('OT', [])
                if away_ot:
                    game_minutes += 5 * len(away_ot)

            self.game_stats['pace'] = calculate_pace(away_totals, home_totals, game_minutes)

            # Calculate four factors
            self.game_stats['four_factors'] = {
                'away': calculate_four_factors(away_totals, home_totals),
                'home': calculate_four_factors(home_totals, away_totals),
            }

            # Store game minutes
            self.game_stats['game_minutes'] = game_minutes

    def _process_player_milestones(self):
        """Check individual player achievements for both teams."""
        basic_info = self.game_data.get('basic_info', {})

        for side in ['away', 'home']:
            players = self.game_data.get('box_score', {}).get(side, {}).get('players', [])
            if not players:
                # Fallback to basic stats
                players = self.game_data.get('box_score', {}).get(side, {}).get('basic', [])

            team_name = basic_info.get(f'{side}_team', '')
            opponent = basic_info.get('home_team' if side == 'away' else 'away_team', '')

            for player in players:
                self._check_player_milestones(player, team_name, opponent, side)

    def _add_milestone(
        self,
        milestone_key: str,
        milestone_base: Dict[str, Any],
        detail: str
    ) -> None:
        """Add a milestone entry to the milestones dict."""
        self.milestones[milestone_key].append({
            **milestone_base,
            'detail': detail,
        })

    def _check_simple_thresholds(
        self,
        stats: Dict[str, int],
        milestone_base: Dict[str, Any]
    ) -> None:
        """Check all simple single-stat thresholds from config."""
        for category, thresholds in MILESTONE_STAT_CONFIGS.items():
            for milestone_key, stat_name, min_val, max_val, detail_template in thresholds:
                stat_value = stats.get(stat_name, 0)
                # Check if stat meets threshold
                if stat_value >= min_val:
                    # Check max_val if specified (for range-based milestones)
                    if max_val is None or stat_value <= max_val:
                        detail = detail_template.format(value=stat_value)
                        self._add_milestone(milestone_key, milestone_base, detail)

    def _check_player_milestones(self, player: Dict[str, Any], team: str, opponent: str, side: str):
        """Check all milestones for a single player."""
        player_name = player.get('name', '')
        player_id = player.get('player_id', '')

        pts = safe_int(player.get('pts', 0))
        trb = safe_int(player.get('trb', 0))
        ast = safe_int(player.get('ast', 0))
        stl = safe_int(player.get('stl', 0))
        blk = safe_int(player.get('blk', 0))
        tov = safe_int(player.get('tov', 0))
        fg3 = safe_int(player.get('fg3', 0))
        fg3a = safe_int(player.get('fg3a', 0))
        fg = safe_int(player.get('fg', 0))
        fga = safe_int(player.get('fga', 0))
        ft = safe_int(player.get('ft', 0))
        fta = safe_int(player.get('fta', 0))

        # Get minutes played
        mp = player.get('mp', 0)
        if isinstance(mp, str) and ':' in mp:
            parts = mp.split(':')
            minutes = int(parts[0]) + int(parts[1]) / 60.0
        else:
            minutes = safe_float(mp)

        milestone_base = {
            'player': player_name,
            'player_id': player_id,
            'team': team,
            'opponent': opponent,
            'side': side,
            'stats': {
                'pts': pts, 'trb': trb, 'ast': ast, 'stl': stl, 'blk': blk,
                'fg3': fg3, 'fg': fg, 'fga': fga, 'ft': ft, 'fta': fta, 'tov': tov,
            }
        }

        # Count categories with 10+, 8+, 5+
        categories_10 = sum([pts >= 10, trb >= 10, ast >= 10, stl >= 10, blk >= 10])
        categories_8 = sum([pts >= 8, trb >= 8, ast >= 8, stl >= 8, blk >= 8])
        categories_5 = sum([pts >= 5, trb >= 5, ast >= 5, stl >= 5, blk >= 5])

        # ===================
        # MULTI-CATEGORY ACHIEVEMENTS
        # ===================

        # Quadruple-double (extremely rare)
        if categories_10 >= 4:
            categories = get_double_double_categories(player)
            self.milestones['quadruple_double'].append({
                **milestone_base,
                'detail': categories,
            })

        # Triple-double
        if is_triple_double(player):
            categories = get_double_double_categories(player)
            self.milestones['triple_doubles'].append({
                **milestone_base,
                'detail': categories,
            })

        # Double-double
        if is_double_double(player):
            categories = get_double_double_categories(player)
            self.milestones['double_doubles'].append({
                **milestone_base,
                'detail': categories,
            })

        # Near triple-double (has 2 categories with 10+ and 1 with 8-9)
        if categories_10 == 2 and categories_8 >= 3 and not is_triple_double(player):
            detail = self._get_near_triple_double_detail(player)
            self.milestones['near_triple_doubles'].append({
                **milestone_base,
                'detail': detail,
            })

        # Near double-double
        if is_near_double_double(player):
            detail = get_near_double_double_detail(player)
            self.milestones['near_double_doubles'].append({
                **milestone_base,
                'detail': detail,
            })

        # 5x5 (5+ in all 5 categories) - very rare
        if categories_5 >= 5:
            self.milestones['five_by_five'].append({
                **milestone_base,
                'detail': f'{pts}p/{trb}r/{ast}a/{stl}s/{blk}b',
            })

        # All-around game (5+ in 5 categories or 8+ in 4)
        if categories_5 >= 5 or (categories_8 >= 4 and not is_triple_double(player)):
            self.milestones['all_around_game'].append({
                **milestone_base,
                'detail': f'{pts}p/{trb}r/{ast}a/{stl}s/{blk}b',
            })

        # ===================
        # SIMPLE STAT THRESHOLDS (config-driven)
        # Scoring, rebounding, assists, blocks, steals, three-pointers
        # ===================
        simple_stats = {
            'pts': pts, 'trb': trb, 'ast': ast,
            'blk': blk, 'stl': stl, 'fg3': fg3,
        }
        self._check_simple_thresholds(simple_stats, milestone_base)

        # ===================
        # DEFENSIVE MILESTONES (complex)
        # ===================
        # Defensive monster (7+ combined blocks + steals)
        if blk + stl >= 7:
            self.milestones['defensive_monster'].append({
                **milestone_base,
                'detail': f'{blk} blocks, {stl} steals ({blk + stl} combined)',
            })

        # ===================
        # THREE-POINTER MILESTONES (complex)
        # ===================
        # Perfect from three (100% with 4+ attempts)
        if fg3a >= 4 and fg3 == fg3a:
            self.milestones['perfect_from_three'].append({
                **milestone_base,
                'detail': f'{fg3}/{fg3a} 3PT (100%)',
            })

        # ===================
        # EFFICIENCY MILESTONES
        # ===================
        if is_hot_shooting(player,
                           min_fga=MILESTONE_THRESHOLDS['hot_shooting_min_fga'],
                           min_pct=MILESTONE_THRESHOLDS['hot_shooting_pct']):
            fg_pct = round(fg / fga * 100, 1) if fga > 0 else 0
            self.milestones['hot_shooting_games'].append({
                **milestone_base,
                'detail': f'{fg}/{fga} FG ({fg_pct}%)',
            })

        if is_perfect_ft(player):
            self.milestones['perfect_ft_games'].append({
                **milestone_base,
                'detail': f'{ft}/{fta} FT (100%)',
            })

        # Perfect FG (100% with 5+ attempts)
        if fga >= 5 and fg == fga:
            self.milestones['perfect_fg_games'].append({
                **milestone_base,
                'detail': f'{fg}/{fga} FG (100%)',
            })

        # Efficient scoring (65%+ TS with 15+ pts)
        ts_denom = 2 * (fga + 0.44 * fta)
        ts_pct = (pts / ts_denom) if ts_denom > 0 else 0
        if pts >= 15 and ts_pct >= 0.65:
            self.milestones['efficient_scoring'].append({
                **milestone_base,
                'detail': f'{pts} pts on {round(ts_pct * 100, 1)}% TS',
            })

        # ===================
        # COMBINED MILESTONES
        # ===================
        # 30-10 games
        if pts >= 30 and trb >= 10:
            self.milestones['thirty_ten_games'].append({
                **milestone_base,
                'detail': f'{pts} pts, {trb} reb',
            })

        # 20-10-5 games
        if pts >= 20 and trb >= 10 and ast >= 5:
            self.milestones['twenty_ten_five_games'].append({
                **milestone_base,
                'detail': f'{pts} pts, {trb} reb, {ast} ast',
            })

        # 20-10 games (includes 20-10-5 games too)
        if pts >= 20 and trb >= 10:
            self.milestones['twenty_ten_games'].append({
                **milestone_base,
                'detail': f'{pts} pts, {trb} reb',
            })

        # Points-assists double-double (10+ pts, 10+ ast)
        if pts >= 10 and ast >= 10:
            self.milestones['points_assists_dd'].append({
                **milestone_base,
                'detail': f'{pts} pts, {ast} ast',
            })

        # ===================
        # CLEAN GAMES
        # ===================
        # Zero turnover game (with significant playing time)
        if tov == 0 and minutes >= 20:
            self.milestones['zero_turnover_games'].append({
                **milestone_base,
                'detail': f'{int(minutes)} min, 0 turnovers',
            })

    def _get_near_triple_double_detail(self, player: Dict[str, Any]) -> str:
        """Get detail string for near triple-double."""
        pts = safe_int(player.get('pts', 0))
        trb = safe_int(player.get('trb', 0))
        ast = safe_int(player.get('ast', 0))
        stl = safe_int(player.get('stl', 0))
        blk = safe_int(player.get('blk', 0))

        categories = [
            ('PTS', pts), ('REB', trb), ('AST', ast), ('STL', stl), ('BLK', blk)
        ]

        has_ten = [(name, val) for name, val in categories if val >= 10]
        near_ten = [(name, val) for name, val in categories if 8 <= val < 10]

        parts = [f"{val} {name.lower()}" for name, val in has_ten + near_ten]

        if near_ten:
            closest = near_ten[0]
            needed = 10 - closest[1]
            return f"{', '.join(parts)} (needed {needed} more {closest[0].lower()})"

        return ', '.join(parts)
