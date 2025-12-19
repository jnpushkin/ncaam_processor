"""
Excel formatting utilities for the basketball processor.
"""

from typing import Dict, Any, Optional, List
import pandas as pd

from ..utils.constants import EXCEL_COLORS


def get_header_format(workbook) -> Any:
    """Get header cell format."""
    return workbook.add_format({
        'bold': True,
        'bg_color': EXCEL_COLORS['header_blue'],
        'font_color': EXCEL_COLORS['white'],
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
        'text_wrap': True,
    })


def get_default_format(workbook) -> Any:
    """Get default cell format."""
    return workbook.add_format({
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })


def get_alt_row_format(workbook) -> Any:
    """Get alternating row format."""
    return workbook.add_format({
        'bg_color': EXCEL_COLORS['alt_row'],
        'border': 1,
        'align': 'center',
        'valign': 'vcenter',
    })


def get_percentage_format(workbook) -> Any:
    """Get percentage format."""
    return workbook.add_format({
        'num_format': '0.0%',
        'border': 1,
        'align': 'center',
    })


def get_decimal_format(workbook, decimals: int = 1) -> Any:
    """Get decimal number format."""
    num_format = '0.' + '0' * decimals
    return workbook.add_format({
        'num_format': num_format,
        'border': 1,
        'align': 'center',
    })


def get_integer_format(workbook) -> Any:
    """Get integer format."""
    return workbook.add_format({
        'num_format': '0',
        'border': 1,
        'align': 'center',
    })


def get_text_format(workbook) -> Any:
    """Get left-aligned text format."""
    return workbook.add_format({
        'border': 1,
        'align': 'left',
        'valign': 'vcenter',
    })


def get_date_format(workbook) -> Any:
    """Get date format."""
    return workbook.add_format({
        'num_format': 'mm/dd/yyyy',
        'border': 1,
        'align': 'center',
    })


def get_column_width(column_name: str) -> int:
    """
    Get recommended column width based on column name.

    Args:
        column_name: Name of the column

    Returns:
        Recommended width in characters
    """
    width_map = {
        'Player': 20,
        'Player ID': 15,
        'Team': 18,
        'Opponent': 18,
        'Date': 12,
        'Score': 10,
        'GameID': 20,
        'Detail': 25,
        'Venue': 25,
        'Notes': 20,

        # Stats
        'Games': 8,
        'Wins': 7,
        'Losses': 7,
        'MPG': 7,
        'PPG': 7,
        'RPG': 7,
        'APG': 7,
        'SPG': 7,
        'BPG': 7,
        'FG%': 7,
        '3P%': 7,
        'FT%': 7,
        'Win%': 7,

        # Totals
        'Total PTS': 10,
        'Total REB': 10,
        'Total AST': 10,
        'FGM': 6,
        'FGA': 6,
        '3PM': 6,
        '3PA': 6,
        'FTM': 6,
        'FTA': 6,
        'PF': 8,
        'PA': 8,
        'Diff': 7,

        # Scores
        'Away Score': 10,
        'Home Score': 10,
        'Away Team': 18,
        'Home Team': 18,

        # Attendance
        'Attendance': 12,
        'Avg Attendance': 14,
    }

    return width_map.get(column_name, 12)


def apply_column_formats(worksheet, workbook, df: pd.DataFrame, start_row: int = 1) -> None:
    """
    Apply appropriate formats to columns based on column names.

    Args:
        worksheet: xlsxwriter worksheet
        workbook: xlsxwriter workbook
        df: DataFrame being written
        start_row: Starting row (1 if headers in row 0)
    """
    percentage_cols = ['FG%', '3P%', 'FT%', 'Win%', 'efg_pct', 'ts_pct']
    decimal_cols = ['MPG', 'PPG', 'RPG', 'APG', 'SPG', 'BPG', 'Diff', 'Avg Score']
    integer_cols = ['Games', 'Wins', 'Losses', 'pts', 'trb', 'ast', 'stl', 'blk',
                    'fg', 'fga', 'fg3', 'fg3a', 'ft', 'fta', 'tov', 'pf',
                    'Total PTS', 'Total REB', 'Total AST', 'FGM', 'FGA', '3PM', '3PA',
                    'FTM', 'FTA', 'PF', 'PA', 'Attendance', 'Avg Attendance',
                    'Away Score', 'Home Score', 'Home W', 'Home L', 'Away W', 'Away L',
                    'Margin', 'OT Periods']
    text_cols = ['Player', 'Team', 'Opponent', 'Venue', 'Detail', 'Notes', 'GameID',
                 'Away Team', 'Home Team', 'Code', 'Winner', 'Loser']

    pct_format = get_percentage_format(workbook)
    dec_format = get_decimal_format(workbook, 1)
    int_format = get_integer_format(workbook)
    text_format = get_text_format(workbook)
    default_format = get_default_format(workbook)

    for col_idx, col_name in enumerate(df.columns):
        width = get_column_width(col_name)
        worksheet.set_column(col_idx, col_idx, width)


def format_worksheet(worksheet, workbook, df: pd.DataFrame,
                     sheet_name: str = '', freeze_panes: bool = True) -> None:
    """
    Apply standard formatting to a worksheet.

    Args:
        worksheet: xlsxwriter worksheet
        workbook: xlsxwriter workbook
        df: DataFrame that was written
        sheet_name: Name of the sheet
        freeze_panes: Whether to freeze the header row
    """
    if df.empty:
        return

    # Freeze header row
    if freeze_panes:
        worksheet.freeze_panes(1, 0)

    # Set column widths
    for col_idx, col_name in enumerate(df.columns):
        width = get_column_width(col_name)
        worksheet.set_column(col_idx, col_idx, width)

    # Apply header format
    header_format = get_header_format(workbook)
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(0, col_idx, col_name, header_format)

    # Apply alternating row colors for data rows
    default_format = get_default_format(workbook)
    alt_format = get_alt_row_format(workbook)

    for row_idx in range(1, len(df) + 1):
        row_format = alt_format if row_idx % 2 == 0 else default_format
        for col_idx in range(len(df.columns)):
            # Get the value from the DataFrame
            value = df.iloc[row_idx - 1, col_idx]
            worksheet.write(row_idx, col_idx, value, row_format)


def write_dataframe_to_sheet(workbook, sheet_name: str, df: pd.DataFrame,
                             format_sheet: bool = True) -> Any:
    """
    Write a DataFrame to a new worksheet with formatting.

    Args:
        workbook: xlsxwriter workbook
        sheet_name: Name for the worksheet
        df: DataFrame to write
        format_sheet: Whether to apply standard formatting

    Returns:
        The worksheet object
    """
    if df.empty:
        worksheet = workbook.add_worksheet(sheet_name)
        worksheet.write(0, 0, 'No data available')
        return worksheet

    worksheet = workbook.add_worksheet(sheet_name)

    # Write headers
    header_format = get_header_format(workbook)
    for col_idx, col_name in enumerate(df.columns):
        worksheet.write(0, col_idx, col_name, header_format)

    # Write data with alternating row colors
    default_format = get_default_format(workbook)
    alt_format = get_alt_row_format(workbook)

    for row_idx, (_, row) in enumerate(df.iterrows(), start=1):
        row_format = alt_format if row_idx % 2 == 0 else default_format
        for col_idx, value in enumerate(row):
            # Handle NaN/None values
            if pd.isna(value):
                worksheet.write(row_idx, col_idx, '', row_format)
            else:
                worksheet.write(row_idx, col_idx, value, row_format)

    if format_sheet:
        # Freeze header row
        worksheet.freeze_panes(1, 0)

        # Set column widths
        for col_idx, col_name in enumerate(df.columns):
            width = get_column_width(col_name)
            worksheet.set_column(col_idx, col_idx, width)

    return worksheet
