"""
Excel workbook generator for basketball statistics.
"""

import os
from typing import Dict, List, Any
import pandas as pd
import xlsxwriter

from .formatters import write_dataframe_to_sheet
from ..processors.player_stats_processor import PlayerStatsProcessor
from ..processors.milestones_processor import MilestonesProcessor, OvertimeGamesProcessor, BlowoutGamesProcessor
from ..processors.team_records_processor import TeamRecordsProcessor, GameLogProcessor
from ..utils.log import info
from ..utils.venue_resolver import resolve_venue


def generate_excel_workbook(
    games: List[Dict[str, Any]],
    output_path: str,
    write_file: bool = True
) -> Dict[str, Any]:
    """
    Generate Excel workbook from parsed games data.

    Args:
        games: List of parsed game dictionaries
        output_path: Path to save the Excel file
        write_file: Whether to actually write the file (False for website-only mode)

    Returns:
        Dictionary containing all processed DataFrames
    """
    info(f"Processing {len(games)} games...")

    # Resolve missing venue data
    for game in games:
        if not game.get('basic_info', {}).get('venue'):
            resolved = resolve_venue(game)
            if resolved:
                game['basic_info']['venue'] = resolved

    # Process all data
    processed_data = {}

    # Game Log
    info("  Creating game log...")
    game_log_processor = GameLogProcessor(games)
    processed_data['game_log'] = game_log_processor.create_game_log()

    # Player Stats
    info("  Processing player statistics...")
    player_processor = PlayerStatsProcessor(games)
    player_data = player_processor.process_all_player_stats()
    processed_data['players'] = player_data['players']
    processed_data['player_games'] = player_data['player_games']
    processed_data['starters_vs_bench'] = player_data.get('starters_vs_bench', pd.DataFrame())
    processed_data['season_highs'] = player_data.get('season_highs', pd.DataFrame())

    # Milestones
    info("  Processing milestones...")
    milestones_processor = MilestonesProcessor(games)
    milestones_data = milestones_processor.process_all_milestones()
    processed_data['milestones'] = milestones_data

    # Overtime games
    ot_processor = OvertimeGamesProcessor(games)
    processed_data['overtime_games'] = ot_processor.process_overtime_games()

    # Blowout games
    blowout_processor = BlowoutGamesProcessor(games)
    processed_data['blowout_games'] = blowout_processor.process_blowout_games()

    # Team Records
    info("  Processing team records...")
    team_processor = TeamRecordsProcessor(games)
    team_data = team_processor.process_team_records()
    processed_data['team_records'] = team_data['team_records']
    processed_data['matchup_matrix'] = team_data['matchup_matrix']
    processed_data['venue_records'] = team_data['venue_records']
    processed_data['team_streaks'] = team_data.get('team_streaks', pd.DataFrame())
    processed_data['head_to_head'] = team_data.get('head_to_head_history', pd.DataFrame())
    processed_data['conference_standings'] = team_data.get('conference_standings', pd.DataFrame())
    processed_data['home_away_splits'] = team_data.get('home_away_splits', pd.DataFrame())
    processed_data['attendance_stats'] = team_data.get('attendance_stats', pd.DataFrame())

    if not write_file:
        info("  Skipping Excel file generation (website-only mode)")
        return processed_data

    # Create workbook
    info(f"  Writing Excel file: {output_path}")

    # Ensure directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    workbook = xlsxwriter.Workbook(output_path)

    # Write sheets in order
    _write_sheets(workbook, processed_data)

    workbook.close()
    info(f"  Excel file saved: {output_path}")

    return processed_data


def _write_sheets(workbook: xlsxwriter.Workbook, processed_data: Dict[str, Any]) -> None:
    """Write all sheets to the workbook."""

    # 1. Game Log
    write_dataframe_to_sheet(
        workbook, 'Game Log',
        processed_data.get('game_log', pd.DataFrame())
    )

    # 2. Players
    write_dataframe_to_sheet(
        workbook, 'Players',
        processed_data.get('players', pd.DataFrame())
    )

    # 3-12. Milestones
    milestones = processed_data.get('milestones', {})

    milestone_sheets = [
        # Multi-category achievements (most impressive first)
        ('quadruple_double', 'Quadruple-Doubles'),
        ('triple_doubles', 'Triple-Doubles'),
        ('double_doubles', 'Double-Doubles'),
        ('near_triple_doubles', 'Near Triple-Doubles'),
        ('near_double_doubles', 'Near Double-Doubles'),
        ('five_by_five', '5x5 Games'),
        ('all_around_game', 'All-Around Games'),

        # Scoring milestones
        ('fifty_point_games', '50+ Point Games'),
        ('forty_point_games', '40+ Point Games'),
        ('thirty_point_games', '30+ Point Games'),
        ('twenty_five_point_games', '25+ Point Games'),
        ('twenty_point_games', '20+ Point Games'),

        # Rebounding milestones
        ('twenty_rebound_games', '20+ Rebound Games'),
        ('fifteen_rebound_games', '15+ Rebound Games'),
        ('ten_rebound_games', '10+ Rebound Games'),

        # Assist milestones
        ('twenty_assist_games', '20+ Assist Games'),
        ('fifteen_assist_games', '15+ Assist Games'),
        ('ten_assist_games', '10+ Assist Games'),

        # Defensive milestones
        ('ten_block_games', '10+ Block Games'),
        ('five_block_games', '5+ Block Games'),
        ('ten_steal_games', '10+ Steal Games'),
        ('five_steal_games', '5+ Steal Games'),
        ('defensive_monster', 'Defensive Monsters'),

        # Three-pointer milestones
        ('ten_three_games', '10+ Three Games'),
        ('seven_three_games', '7+ Three Games'),
        ('five_three_games', '5+ Three Games'),
        ('perfect_from_three', 'Perfect From Three'),

        # Efficiency milestones
        ('hot_shooting_games', 'Hot Shooting'),
        ('perfect_ft_games', 'Perfect FT'),
        ('perfect_fg_games', 'Perfect FG'),
        ('efficient_scoring', 'Efficient Scoring'),

        # Combined milestones
        ('thirty_ten_games', '30-10 Games'),
        ('twenty_ten_five_games', '20-10-5 Games'),
        ('twenty_ten_games', '20-10 Games'),
        ('points_assists_dd', 'Points-Assists DD'),

        # Clean games
        ('zero_turnover_games', 'Zero Turnover Games'),
    ]

    for key, sheet_name in milestone_sheets:
        df = milestones.get(key, pd.DataFrame())
        if not df.empty:
            # Select key columns for display
            display_cols = ['Date', 'Player', 'Team', 'Opponent', 'Score', 'Detail', 'GameID']
            display_cols = [c for c in display_cols if c in df.columns]
            if display_cols:
                df = df[display_cols]
            write_dataframe_to_sheet(workbook, sheet_name, df)

    # 13. Overtime Games
    ot_df = processed_data.get('overtime_games', pd.DataFrame())
    if not ot_df.empty:
        write_dataframe_to_sheet(workbook, 'Overtime Games', ot_df)

    # 14. Blowouts
    blowout_df = processed_data.get('blowout_games', pd.DataFrame())
    if not blowout_df.empty:
        write_dataframe_to_sheet(workbook, 'Blowouts', blowout_df)

    # 15. Team Records
    write_dataframe_to_sheet(
        workbook, 'Team Records',
        processed_data.get('team_records', pd.DataFrame())
    )

    # 16. Venues
    venue_df = processed_data.get('venue_records', pd.DataFrame())
    if not venue_df.empty:
        write_dataframe_to_sheet(workbook, 'Venues', venue_df)

    # 17. Matchup Matrix
    matrix_df = processed_data.get('matchup_matrix', pd.DataFrame())
    if not matrix_df.empty:
        write_dataframe_to_sheet(workbook, 'Matchup Matrix', matrix_df)

    # 18. Starters vs Bench
    starters_bench_df = processed_data.get('starters_vs_bench', pd.DataFrame())
    if not starters_bench_df.empty:
        write_dataframe_to_sheet(workbook, 'Starters vs Bench', starters_bench_df)

    # 19. Season Highs
    season_highs_df = processed_data.get('season_highs', pd.DataFrame())
    if not season_highs_df.empty:
        write_dataframe_to_sheet(workbook, 'Season Highs', season_highs_df)

    # 20. Team Streaks
    streaks_df = processed_data.get('team_streaks', pd.DataFrame())
    if not streaks_df.empty:
        write_dataframe_to_sheet(workbook, 'Team Streaks', streaks_df)

    # 21. Head to Head
    h2h_df = processed_data.get('head_to_head', pd.DataFrame())
    if not h2h_df.empty:
        write_dataframe_to_sheet(workbook, 'Head to Head', h2h_df)

    # 22. Conference Standings
    conf_df = processed_data.get('conference_standings', pd.DataFrame())
    if not conf_df.empty:
        write_dataframe_to_sheet(workbook, 'Conference Standings', conf_df)

    # 23. Home Away Splits
    splits_df = processed_data.get('home_away_splits', pd.DataFrame())
    if not splits_df.empty:
        write_dataframe_to_sheet(workbook, 'Home Away Splits', splits_df)

    # 24. Attendance Stats
    attendance_df = processed_data.get('attendance_stats', pd.DataFrame())
    if not attendance_df.empty:
        write_dataframe_to_sheet(workbook, 'Attendance', attendance_df)

    # 25. Summary (create summary sheet)
    _write_summary_sheet(workbook, processed_data)


def _write_summary_sheet(workbook: xlsxwriter.Workbook, processed_data: Dict[str, Any]) -> None:
    """Write summary statistics sheet."""
    worksheet = workbook.add_worksheet('Summary')

    # Header format
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#003087',
        'font_color': 'white',
        'font_size': 14,
    })

    section_format = workbook.add_format({
        'bold': True,
        'font_size': 12,
        'bottom': 1,
    })

    label_format = workbook.add_format({
        'align': 'left',
    })

    value_format = workbook.add_format({
        'align': 'right',
        'num_format': '#,##0',
    })

    row = 0

    # Title
    worksheet.merge_range(row, 0, row, 3, 'Basketball Stats Summary', header_format)
    row += 2

    # Games Summary
    worksheet.write(row, 0, 'Games Summary', section_format)
    row += 1

    game_log = processed_data.get('game_log', pd.DataFrame())
    worksheet.write(row, 0, 'Total Games:', label_format)
    worksheet.write(row, 1, len(game_log), value_format)
    row += 2

    # Players Summary
    worksheet.write(row, 0, 'Players Summary', section_format)
    row += 1

    players = processed_data.get('players', pd.DataFrame())
    worksheet.write(row, 0, 'Total Players:', label_format)
    worksheet.write(row, 1, len(players), value_format)
    row += 1

    if not players.empty and 'Total PTS' in players.columns:
        worksheet.write(row, 0, 'Total Points Scored:', label_format)
        worksheet.write(row, 1, int(players['Total PTS'].sum()), value_format)
        row += 2

    # Milestones Summary
    worksheet.write(row, 0, 'Milestones Summary', section_format)
    row += 1

    milestones = processed_data.get('milestones', {})
    for key, df in milestones.items():
        if isinstance(df, pd.DataFrame) and not df.empty:
            display_name = key.replace('_', ' ').title()
            worksheet.write(row, 0, f'{display_name}:', label_format)
            worksheet.write(row, 1, len(df), value_format)
            row += 1

    row += 1

    # Team Summary
    worksheet.write(row, 0, 'Teams Summary', section_format)
    row += 1

    team_records = processed_data.get('team_records', pd.DataFrame())
    worksheet.write(row, 0, 'Teams Tracked:', label_format)
    worksheet.write(row, 1, len(team_records), value_format)
    row += 2

    # Set column widths
    worksheet.set_column(0, 0, 25)
    worksheet.set_column(1, 1, 15)
