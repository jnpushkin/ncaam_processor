"""
Basketball-specific statistical calculations and utilities.
"""

from typing import Dict, Any, Optional
from .helpers import safe_float, safe_int


def calculate_fg_pct(fg: int, fga: int) -> float:
    """Calculate field goal percentage."""
    if fga == 0:
        return 0.0
    return round(fg / fga, 3)


def calculate_efg_pct(fg: int, fg3: int, fga: int) -> float:
    """
    Calculate Effective Field Goal Percentage.

    eFG% = (FG + 0.5 * 3P) / FGA

    This adjusts for the fact that 3-pointers are worth more.
    """
    if fga == 0:
        return 0.0
    return round((fg + 0.5 * fg3) / fga, 3)


def calculate_ts_pct(pts: int, fga: int, fta: int) -> float:
    """
    Calculate True Shooting Percentage.

    TS% = PTS / (2 * (FGA + 0.44 * FTA))

    This measures scoring efficiency accounting for FTs and 3s.
    """
    denominator = 2 * (fga + 0.44 * fta)
    if denominator == 0:
        return 0.0
    return round(pts / denominator, 3)


def calculate_per_game_stats(totals: Dict[str, Any], games: int) -> Dict[str, float]:
    """
    Calculate per-game averages from totals.

    Args:
        totals: Dictionary of total stats
        games: Number of games

    Returns:
        Dictionary of per-game averages
    """
    if games == 0:
        return {}

    per_game = {}
    stat_keys = ['pts', 'trb', 'ast', 'stl', 'blk', 'tov', 'orb', 'drb',
                 'fg', 'fga', 'fg3', 'fg3a', 'ft', 'fta', 'pf', 'mp']

    for key in stat_keys:
        if key in totals:
            per_game[f'{key}_pg'] = round(safe_float(totals[key]) / games, 1)

    return per_game


def calculate_shooting_percentages(stats: Dict[str, Any]) -> Dict[str, float]:
    """
    Calculate all shooting percentages for a player.

    Args:
        stats: Dictionary with fg, fga, fg3, fg3a, ft, fta, pts

    Returns:
        Dictionary with fg_pct, fg3_pct, ft_pct, efg_pct, ts_pct
    """
    fg = safe_int(stats.get('fg', 0))
    fga = safe_int(stats.get('fga', 0))
    fg3 = safe_int(stats.get('fg3', 0))
    fg3a = safe_int(stats.get('fg3a', 0))
    ft = safe_int(stats.get('ft', 0))
    fta = safe_int(stats.get('fta', 0))
    pts = safe_int(stats.get('pts', 0))

    return {
        'fg_pct': calculate_fg_pct(fg, fga),
        'fg3_pct': calculate_fg_pct(fg3, fg3a),
        'ft_pct': calculate_fg_pct(ft, fta),
        'efg_pct': calculate_efg_pct(fg, fg3, fga),
        'ts_pct': calculate_ts_pct(pts, fga, fta),
    }


def is_double_double(stats: Dict[str, Any]) -> bool:
    """
    Check if player achieved a double-double.

    Double-double: 10+ in 2 of pts, reb, ast, stl, blk
    """
    pts = safe_int(stats.get('pts', 0))
    trb = safe_int(stats.get('trb', 0))
    ast = safe_int(stats.get('ast', 0))
    stl = safe_int(stats.get('stl', 0))
    blk = safe_int(stats.get('blk', 0))

    categories_with_10 = sum([
        pts >= 10,
        trb >= 10,
        ast >= 10,
        stl >= 10,
        blk >= 10
    ])

    return categories_with_10 >= 2


def is_triple_double(stats: Dict[str, Any]) -> bool:
    """
    Check if player achieved a triple-double.

    Triple-double: 10+ in 3 of pts, reb, ast, stl, blk
    """
    pts = safe_int(stats.get('pts', 0))
    trb = safe_int(stats.get('trb', 0))
    ast = safe_int(stats.get('ast', 0))
    stl = safe_int(stats.get('stl', 0))
    blk = safe_int(stats.get('blk', 0))

    categories_with_10 = sum([
        pts >= 10,
        trb >= 10,
        ast >= 10,
        stl >= 10,
        blk >= 10
    ])

    return categories_with_10 >= 3


def get_double_double_categories(stats: Dict[str, Any]) -> str:
    """
    Get the categories that qualify for a double-double.

    Returns:
        String like "PTS-REB" or "PTS-AST-REB" for triple-double
    """
    categories = []
    pts = safe_int(stats.get('pts', 0))
    trb = safe_int(stats.get('trb', 0))
    ast = safe_int(stats.get('ast', 0))
    stl = safe_int(stats.get('stl', 0))
    blk = safe_int(stats.get('blk', 0))

    if pts >= 10:
        categories.append(f"PTS:{pts}")
    if trb >= 10:
        categories.append(f"REB:{trb}")
    if ast >= 10:
        categories.append(f"AST:{ast}")
    if stl >= 10:
        categories.append(f"STL:{stl}")
    if blk >= 10:
        categories.append(f"BLK:{blk}")

    return " / ".join(categories)


def is_hot_shooting(stats: Dict[str, Any], min_fga: int = 10, min_pct: float = 0.50) -> bool:
    """
    Check if player had a hot shooting game.

    Args:
        stats: Player stats dictionary
        min_fga: Minimum field goal attempts required
        min_pct: Minimum FG% required

    Returns:
        True if player qualifies as hot shooting
    """
    fga = safe_int(stats.get('fga', 0))
    fg_pct = safe_float(stats.get('fg_pct', 0))

    # If fg_pct not provided, calculate it
    if fg_pct == 0 and fga > 0:
        fg = safe_int(stats.get('fg', 0))
        fg_pct = fg / fga

    return fga >= min_fga and fg_pct >= min_pct


def is_perfect_ft(stats: Dict[str, Any], min_ftm: int = 5) -> bool:
    """
    Check if player had a perfect free throw game.

    Args:
        stats: Player stats dictionary
        min_ftm: Minimum free throws made required

    Returns:
        True if player made all FTs with minimum attempts
    """
    ft = safe_int(stats.get('ft', 0))
    fta = safe_int(stats.get('fta', 0))

    return ft >= min_ftm and ft == fta


def aggregate_player_stats(games_stats: list) -> Dict[str, Any]:
    """
    Aggregate player stats across multiple games.

    Args:
        games_stats: List of dictionaries with per-game stats

    Returns:
        Dictionary with totals and averages
    """
    if not games_stats:
        return {}

    # Stats to sum
    sum_stats = ['pts', 'trb', 'ast', 'stl', 'blk', 'tov', 'orb', 'drb',
                 'fg', 'fga', 'fg3', 'fg3a', 'ft', 'fta', 'pf']

    totals = {stat: 0 for stat in sum_stats}
    total_minutes = 0.0
    games = len(games_stats)

    for game in games_stats:
        for stat in sum_stats:
            totals[stat] += safe_int(game.get(stat, 0))

        # Handle minutes (can be string like "35:20")
        mp = game.get('mp', 0)
        if isinstance(mp, str) and ':' in mp:
            parts = mp.split(':')
            total_minutes += int(parts[0]) + int(parts[1]) / 60.0
        else:
            total_minutes += safe_float(mp)

    # Calculate shooting percentages from totals
    shooting_pcts = calculate_shooting_percentages(totals)

    # Calculate per-game averages
    per_game = calculate_per_game_stats(totals, games)

    # Build result
    result = {
        'games': games,
        'totals': totals,
        'total_minutes': round(total_minutes, 1),
        'mpg': round(total_minutes / games, 1) if games > 0 else 0,
        **shooting_pcts,
        **per_game,
    }

    return result


def calculate_pace(team_stats: Dict[str, Any], opponent_stats: Dict[str, Any],
                   minutes: int = 40) -> float:
    """
    Estimate pace (possessions per 40 minutes).

    Possessions ≈ FGA - ORB + TOV + 0.44 * FTA

    Args:
        team_stats: Team's box score stats
        opponent_stats: Opponent's box score stats
        minutes: Game minutes (default 40)

    Returns:
        Estimated pace
    """
    def estimate_possessions(stats: Dict[str, Any]) -> float:
        fga = safe_int(stats.get('fga', 0))
        orb = safe_int(stats.get('orb', 0))
        tov = safe_int(stats.get('tov', 0))
        fta = safe_int(stats.get('fta', 0))
        return fga - orb + tov + 0.44 * fta

    team_poss = estimate_possessions(team_stats)
    opp_poss = estimate_possessions(opponent_stats)

    # Average the two estimates
    avg_poss = (team_poss + opp_poss) / 2

    # Normalize to 40 minutes
    if minutes > 0:
        pace = avg_poss * (40 / minutes)
    else:
        pace = avg_poss

    return round(pace, 1)


def calculate_usage_rate(fga: int, fta: int, tov: int, team_fga: int,
                         team_fta: int, team_tov: int, mp: float, team_mp: float) -> float:
    """
    Calculate Usage Rate - percentage of team plays used while on court.

    USG% = 100 * ((FGA + 0.44 * FTA + TOV) * (Team MP / 5)) /
           (MP * (Team FGA + 0.44 * Team FTA + Team TOV))

    Args:
        fga, fta, tov: Player's stats
        team_fga, team_fta, team_tov: Team totals
        mp: Player minutes
        team_mp: Team total minutes (usually 200 for 40-min game with 5 players)

    Returns:
        Usage rate as percentage (0-100)
    """
    if mp == 0 or team_mp == 0:
        return 0.0

    player_usage = fga + 0.44 * fta + tov
    team_usage = team_fga + 0.44 * team_fta + team_tov

    if team_usage == 0:
        return 0.0

    usg = 100 * ((player_usage * (team_mp / 5)) / (mp * team_usage))
    return round(min(usg, 100), 1)  # Cap at 100


def calculate_offensive_rating(pts: int, fga: int, fta: int, tov: int, orb: int,
                               team_pts: int, team_fga: int, team_fta: int,
                               team_tov: int, team_orb: int, mp: float, team_mp: float) -> float:
    """
    Simplified Offensive Rating - points produced per 100 possessions.

    This is a simplified version that estimates individual offensive rating.

    Args:
        pts, fga, fta, tov, orb: Player stats
        team_*: Team totals
        mp: Player minutes
        team_mp: Team total minutes

    Returns:
        Offensive rating (points per 100 possessions)
    """
    if mp == 0:
        return 0.0

    # Estimate player possessions
    player_poss = fga + 0.44 * fta + tov - orb * 0.5
    if player_poss <= 0:
        player_poss = 0.1

    # Points per possession, scaled to 100
    ortg = (pts / player_poss) * 100
    return round(ortg, 1)


def calculate_defensive_rating(opp_pts: int, opp_fga: int, opp_fta: int,
                               opp_tov: int, opp_orb: int, stl: int, blk: int,
                               drb: int, mp: float, team_mp: float) -> float:
    """
    Simplified Defensive Rating - opponent points allowed per 100 possessions.

    Lower is better. This is a team-based estimate adjusted for playing time.

    Args:
        opp_*: Opponent team totals
        stl, blk, drb: Player defensive stats
        mp: Player minutes
        team_mp: Team total minutes

    Returns:
        Defensive rating (opponent points per 100 possessions)
    """
    if team_mp == 0:
        return 0.0

    # Estimate opponent possessions
    opp_poss = opp_fga + 0.44 * opp_fta + opp_tov - opp_orb * 0.5
    if opp_poss <= 0:
        opp_poss = 0.1

    # Team defensive rating
    team_drtg = (opp_pts / opp_poss) * 100

    # Adjust for player's defensive contribution (simplified)
    playing_time_pct = mp / team_mp if team_mp > 0 else 0
    defensive_contribution = (stl * 2 + blk * 2 + drb) * playing_time_pct

    # Slight adjustment based on defensive stats (lower is better)
    adjusted_drtg = team_drtg - (defensive_contribution * 0.5)

    return round(max(adjusted_drtg, 0), 1)


def calculate_per(stats: Dict[str, Any], team_stats: Dict[str, Any],
                  opp_stats: Dict[str, Any], league_pace: float = 70.0) -> float:
    """
    Calculate Player Efficiency Rating (simplified version).

    PER is a per-minute rating that sums up all positive contributions,
    subtracts negative contributions, and adjusts for pace.

    Args:
        stats: Player stats dictionary
        team_stats: Team totals
        opp_stats: Opponent totals
        league_pace: Average pace (default 70 for college)

    Returns:
        PER value (league average is ~15)
    """
    mp = safe_float(stats.get('mp', 0))
    if mp == 0:
        return 0.0

    # Get player stats
    pts = safe_int(stats.get('pts', 0))
    fg = safe_int(stats.get('fg', 0))
    fga = safe_int(stats.get('fga', 0))
    fg3 = safe_int(stats.get('fg3', 0))
    ft = safe_int(stats.get('ft', 0))
    fta = safe_int(stats.get('fta', 0))
    orb = safe_int(stats.get('orb', 0))
    drb = safe_int(stats.get('drb', 0))
    trb = safe_int(stats.get('trb', 0))
    ast = safe_int(stats.get('ast', 0))
    stl = safe_int(stats.get('stl', 0))
    blk = safe_int(stats.get('blk', 0))
    tov = safe_int(stats.get('tov', 0))
    pf = safe_int(stats.get('pf', 0))

    # Simplified PER calculation
    # Positive contributions
    positive = (
        pts +
        fg * 0.5 +
        fg3 * 0.5 +
        ft * 0.5 +
        orb * 1.0 +
        drb * 0.5 +
        ast * 1.0 +
        stl * 2.0 +
        blk * 1.5
    )

    # Negative contributions
    negative = (
        (fga - fg) * 0.5 +
        (fta - ft) * 0.3 +
        tov * 1.5 +
        pf * 0.5
    )

    # Raw PER (per minute)
    raw_per = (positive - negative) / mp

    # Scale to league average of ~15
    per = raw_per * 15

    return round(per, 1)


def calculate_four_factors(team_stats: Dict[str, Any], opp_stats: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Calculate Dean Oliver's Four Factors for team performance.

    The Four Factors are:
    1. eFG% - Effective Field Goal Percentage (shooting)
    2. TOV% - Turnover Percentage (ball security)
    3. ORB% - Offensive Rebound Percentage (second chances)
    4. FT Rate - Free Throw Rate (getting to the line)

    Args:
        team_stats: Team totals
        opp_stats: Opponent totals

    Returns:
        Dictionary with four factors for team and opponent
    """
    def get_factors(stats: Dict[str, Any], opp_orb: int) -> Dict[str, float]:
        fg = safe_int(stats.get('fg', 0))
        fg3 = safe_int(stats.get('fg3', 0))
        fga = safe_int(stats.get('fga', 0))
        ft = safe_int(stats.get('ft', 0))
        fta = safe_int(stats.get('fta', 0))
        tov = safe_int(stats.get('tov', 0))
        orb = safe_int(stats.get('orb', 0))
        drb = safe_int(stats.get('drb', 0))

        # eFG% = (FG + 0.5 * 3P) / FGA
        efg_pct = (fg + 0.5 * fg3) / fga if fga > 0 else 0

        # TOV% = TOV / (FGA + 0.44 * FTA + TOV)
        possessions = fga + 0.44 * fta + tov
        tov_pct = tov / possessions if possessions > 0 else 0

        # ORB% = ORB / (ORB + Opp DRB)
        total_reb_opportunities = orb + opp_orb
        orb_pct = orb / total_reb_opportunities if total_reb_opportunities > 0 else 0

        # FT Rate = FT / FGA (or FTA / FGA)
        ft_rate = fta / fga if fga > 0 else 0

        return {
            'efg_pct': round(efg_pct, 3),
            'tov_pct': round(tov_pct, 3),
            'orb_pct': round(orb_pct, 3),
            'ft_rate': round(ft_rate, 3)
        }

    opp_drb = safe_int(opp_stats.get('drb', 0))
    team_drb = safe_int(team_stats.get('drb', 0))

    team_factors = get_factors(team_stats, opp_drb)
    opp_factors = get_factors(opp_stats, team_drb)

    return {
        'team': team_factors,
        'opponent': opp_factors
    }


def is_near_double_double(stats: Dict[str, Any], threshold: int = 8) -> bool:
    """
    Check if player was close to a double-double but didn't get it.

    Near miss: Has one category with 10+ and another with threshold+ (but <10)

    Args:
        stats: Player stats dictionary
        threshold: Minimum value for "near" (default 8)

    Returns:
        True if near double-double (not actual double-double)
    """
    if is_double_double(stats):
        return False  # Already has it

    pts = safe_int(stats.get('pts', 0))
    trb = safe_int(stats.get('trb', 0))
    ast = safe_int(stats.get('ast', 0))
    stl = safe_int(stats.get('stl', 0))
    blk = safe_int(stats.get('blk', 0))

    values = [pts, trb, ast, stl, blk]

    # Count categories with 10+ and threshold+
    has_ten_plus = sum(1 for v in values if v >= 10)
    has_near = sum(1 for v in values if threshold <= v < 10)

    return has_ten_plus >= 1 and has_near >= 1


def get_near_double_double_detail(stats: Dict[str, Any]) -> str:
    """
    Get detail string for near double-double.

    Returns:
        String like "15 pts, 8 reb (needed 2 more reb)"
    """
    pts = safe_int(stats.get('pts', 0))
    trb = safe_int(stats.get('trb', 0))
    ast = safe_int(stats.get('ast', 0))
    stl = safe_int(stats.get('stl', 0))
    blk = safe_int(stats.get('blk', 0))

    categories = [
        ('PTS', pts), ('REB', trb), ('AST', ast), ('STL', stl), ('BLK', blk)
    ]

    has_ten = [(name, val) for name, val in categories if val >= 10]
    near_ten = [(name, val) for name, val in categories if 8 <= val < 10]

    if not has_ten or not near_ten:
        return ""

    detail_parts = [f"{val} {name.lower()}" for name, val in has_ten + near_ten]
    near_part = near_ten[0]
    needed = 10 - near_part[1]

    return f"{', '.join(detail_parts)} (needed {needed} more {near_part[0].lower()})"


def calculate_game_score(stats: Dict[str, Any]) -> float:
    """
    Calculate John Hollinger's Game Score.

    GameScore = PTS + 0.4*FG - 0.7*FGA - 0.4*(FTA-FT) + 0.7*ORB + 0.3*DRB
                + STL + 0.7*AST + 0.7*BLK - 0.4*PF - TOV

    Args:
        stats: Player stats dictionary

    Returns:
        Game Score value
    """
    pts = safe_int(stats.get('pts', 0))
    fg = safe_int(stats.get('fg', 0))
    fga = safe_int(stats.get('fga', 0))
    ft = safe_int(stats.get('ft', 0))
    fta = safe_int(stats.get('fta', 0))
    orb = safe_int(stats.get('orb', 0))
    drb = safe_int(stats.get('drb', 0))
    ast = safe_int(stats.get('ast', 0))
    stl = safe_int(stats.get('stl', 0))
    blk = safe_int(stats.get('blk', 0))
    pf = safe_int(stats.get('pf', 0))
    tov = safe_int(stats.get('tov', 0))

    game_score = (
        pts + 0.4 * fg - 0.7 * fga - 0.4 * (fta - ft) +
        0.7 * orb + 0.3 * drb + stl + 0.7 * ast + 0.7 * blk -
        0.4 * pf - tov
    )

    return round(game_score, 1)
