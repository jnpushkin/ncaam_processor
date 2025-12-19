"""
Website generator for interactive HTML output.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

from .serializers import DataSerializer
from ..utils.log import info


def generate_website_from_data(processed_data: Dict[str, Any], output_path: str):
    """
    Generate interactive HTML website from processed data.

    Args:
        processed_data: Dictionary containing processed DataFrames
        output_path: Path to save the HTML file
    """
    info(f"Generating website: {output_path}")

    # Get raw games if available
    raw_games = processed_data.get('_raw_games', [])

    # Serialize data
    serializer = DataSerializer(processed_data, raw_games)
    data = serializer.serialize_all()
    json_data = json.dumps(data, default=str)

    # Generate HTML
    html_content = _generate_html(json_data, data.get('summary', {}))

    # Write file
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    info(f"Website saved: {output_path}")


def _generate_html(json_data: str, summary: Dict[str, Any]) -> str:
    """Generate the HTML content."""

    total_games = summary.get('totalGames', 0)
    total_players = summary.get('totalPlayers', 0)
    total_teams = summary.get('totalTeams', 0)
    generated_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>College Basketball Stats</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <style>
        :root {{
            --bg-primary: #f5f5f5;
            --bg-secondary: #ffffff;
            --bg-header: linear-gradient(135deg, #003087, #004db3);
            --text-primary: #333333;
            --text-secondary: #666666;
            --text-muted: #999999;
            --text-header: #ffffff;
            --border-color: #e0e0e0;
            --accent-color: #003087;
            --accent-light: #e8f0fe;
            --hover-color: #f8f9fa;
            --shadow: 0 4px 6px rgba(0,0,0,0.1);
            --success: #27ae60;
            --warning: #f39c12;
            --danger: #e74c3c;
            --info: #3498db;
            --excellent: #27ae60;
            --good: #2ecc71;
            --average: #f39c12;
            --poor: #e74c3c;
        }}

        [data-theme="dark"] {{
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-header: linear-gradient(135deg, #0f3460, #1a1a2e);
            --text-primary: #eaeaea;
            --text-secondary: #b0b0b0;
            --text-muted: #777777;
            --text-header: #ffffff;
            --border-color: #2a2a4a;
            --accent-color: #4a9eff;
            --accent-light: #1a3a5c;
            --hover-color: #1e2a4a;
            --shadow: 0 4px 6px rgba(0,0,0,0.3);
            --excellent: #2ecc71;
            --good: #3498db;
            --average: #f1c40f;
            --poor: #e74c3c;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: background 0.3s, color 0.3s;
        }}
        .header {{
            background: var(--bg-header);
            color: var(--text-header);
            padding: 2rem;
            text-align: center;
            position: relative;
        }}
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        .header-controls {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            gap: 0.5rem;
        }}
        .theme-toggle, .share-btn {{
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 1.2rem;
            transition: background 0.3s;
            color: white;
        }}
        .theme-toggle:hover, .share-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        .generated-time {{
            position: absolute;
            bottom: 0.5rem;
            right: 1rem;
            font-size: 0.75rem;
            opacity: 0.7;
        }}
        .stats-overview {{
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: rgba(255,255,255,0.1);
            padding: 1rem 2rem;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-box .number {{
            font-size: 2rem;
            font-weight: bold;
        }}
        .stat-box .label {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }}
        .tabs {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        .tab {{
            padding: 0.75rem 1.5rem;
            background: var(--bg-secondary);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            color: var(--text-primary);
            transition: all 0.2s;
            box-shadow: var(--shadow);
        }}
        .tab:hover {{
            background: var(--hover-color);
        }}
        .tab.active {{
            background: var(--accent-color);
            color: white;
        }}
        .tab:focus {{
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }}
        .section {{
            display: none;
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
        }}
        .section.active {{
            display: block;
        }}
        .section h2 {{
            margin-bottom: 1rem;
            color: var(--accent-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .section-actions {{
            display: flex;
            gap: 0.5rem;
        }}
        .btn {{
            padding: 0.5rem 1rem;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: opacity 0.2s;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}
        .btn-secondary {{
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }}
        .sub-tabs {{
            display: flex;
            gap: 0.25rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        .sub-tab {{
            padding: 0.5rem 1rem;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            color: var(--text-secondary);
            transition: all 0.2s;
        }}
        .sub-tab:hover {{
            background: var(--hover-color);
        }}
        .sub-tab.active {{
            background: var(--accent-light);
            color: var(--accent-color);
            border-color: var(--accent-color);
        }}
        .sub-section {{
            display: none;
        }}
        .sub-section.active {{
            display: block;
        }}
        /* Advanced Filters */
        .filters {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            align-items: flex-end;
            padding: 1rem;
            background: var(--bg-primary);
            border-radius: 8px;
        }}
        .filter-group {{
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }}
        .filter-group label {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
        }}
        .filter-group input, .filter-group select {{
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            min-width: 150px;
        }}
        .filter-group input:focus, .filter-group select:focus {{
            outline: none;
            border-color: var(--accent-color);
        }}
        .clear-filters {{
            padding: 0.5rem 1rem;
            background: transparent;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            color: var(--text-secondary);
        }}
        .clear-filters:hover {{
            background: var(--hover-color);
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }}
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }}
        th {{
            background: var(--bg-primary);
            font-weight: 600;
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }}
        th:hover {{
            background: var(--hover-color);
        }}
        th.sorted-asc::after {{
            content: ' \\25B2';
            font-size: 0.7rem;
        }}
        th.sorted-desc::after {{
            content: ' \\25BC';
            font-size: 0.7rem;
        }}
        tr:hover {{
            background: var(--hover-color);
        }}
        .table-container {{
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
            margin-bottom: 1rem;
        }}
        .table-container table {{
            min-width: 100%;
        }}
        .table-scroll {{
            max-height: none;
        }}
        .sticky-col {{
            position: sticky;
            left: 0;
            background: var(--bg-primary);
            z-index: 10;
            box-shadow: 2px 0 4px rgba(0,0,0,0.1);
        }}
        thead .sticky-col {{
            background: var(--bg-secondary);
            z-index: 20;
        }}
        tr:hover .sticky-col {{
            background: var(--hover-color);
        }}
        .clickable-row {{
            cursor: pointer;
        }}
        .clickable-row:hover {{
            background: var(--hover-color);
        }}
        .gender-tag {{
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-left: 0.25rem;
        }}
        .gender-seen {{
            display: inline-block;
            font-size: 0.65rem;
            font-weight: 600;
            padding: 0.1rem 0.25rem;
            border-radius: 3px;
            margin-left: 0.15rem;
        }}
        .gender-m {{
            background: #1976D2;
            color: white;
        }}
        .gender-w {{
            background: #E91E63;
            color: white;
        }}
        .checklist-venue .gender-m, .checklist-venue .gender-w {{
            font-size: 0.6rem;
            padding: 0.05rem 0.2rem;
            vertical-align: middle;
        }}
        /* Calendar grid */
        .calendar-grid {{
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }}
        .calendar-year {{
            margin-bottom: 1rem;
        }}
        .calendar-year h3 {{
            margin-bottom: 0.5rem;
            color: var(--accent-color);
        }}
        .calendar-months {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }}
        .calendar-month {{
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid var(--border-color);
        }}
        .calendar-month h4 {{
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        .calendar-days {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
        }}
        .calendar-day-header {{
            font-size: 0.7rem;
            text-align: center;
            color: var(--text-secondary);
            padding: 2px;
        }}
        .calendar-day {{
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            border-radius: 4px;
            background: var(--bg-secondary);
            cursor: default;
        }}
        .calendar-day.empty {{
            background: transparent;
        }}
        .calendar-day.has-game {{
            background: var(--accent-color);
            color: white;
            font-weight: bold;
            cursor: pointer;
        }}
        .calendar-day.has-game:hover {{
            background: var(--accent-hover);
            transform: scale(1.1);
        }}
        .calendar-day.has-multiple {{
            background: var(--excellent);
        }}
        .calendar-day.out-of-range {{
            background: transparent;
            color: var(--text-secondary);
            opacity: 0.3;
        }}
        .calendar-progress {{
            margin-bottom: 1.5rem;
            text-align: center;
        }}
        .calendar-progress .progress-text {{
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }}
        .calendar-progress .progress-bar {{
            height: 24px;
            background: var(--bg-secondary);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }}
        .calendar-progress .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent-color), var(--excellent));
            border-radius: 12px;
            transition: width 0.3s ease;
        }}
        /* Monthly calendar */
        .monthly-calendar {{
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            max-width: 700px;
            margin: 0 auto;
        }}
        .monthly-calendar .day-header {{
            text-align: center;
            font-weight: bold;
            padding: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}
        .monthly-calendar .day-cell {{
            min-height: 80px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 4px;
            font-size: 0.75rem;
        }}
        .monthly-calendar .day-cell.empty {{
            background: transparent;
            border-color: transparent;
        }}
        .monthly-calendar .day-cell.has-games {{
            background: var(--accent-color);
            border-color: var(--accent-color);
        }}
        .monthly-calendar .day-cell.has-games:hover {{
            background: var(--accent-hover);
            cursor: pointer;
        }}
        .monthly-calendar .day-number {{
            font-weight: bold;
            margin-bottom: 2px;
        }}
        .monthly-calendar .day-cell.has-games .day-number {{
            color: white;
        }}
        .monthly-calendar .day-games {{
            font-size: 0.7rem;
            color: rgba(255,255,255,0.9);
            overflow: hidden;
        }}
        .monthly-calendar .day-games .game-entry {{
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        /* Stat highlighting */
        .stat-excellent {{ color: var(--excellent); font-weight: bold; }}
        .stat-good {{ color: var(--good); }}
        .stat-average {{ color: var(--average); }}
        .stat-poor {{ color: var(--poor); }}
        /* Tooltips */
        .tooltip {{
            position: relative;
            cursor: help;
        }}
        .tooltip::after {{
            content: attr(data-tooltip);
            position: absolute;
            top: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: var(--text-primary);
            color: var(--bg-secondary);
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            white-space: nowrap;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.2s;
            z-index: 1000;
            margin-top: 4px;
            pointer-events: none;
        }}
        .tooltip:hover::after {{
            opacity: 1;
            visibility: visible;
        }}
        thead {{
            position: relative;
            z-index: 50;
        }}
        .search-box {{
            width: 100%;
            max-width: 400px;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 1rem;
            background: var(--bg-secondary);
            color: var(--text-primary);
        }}
        .search-box:focus {{
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(0,48,135,0.1);
        }}
        .controls {{
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }}
        /* Pagination */
        .pagination {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
            margin-top: 1rem;
            padding: 1rem 0;
        }}
        .pagination button {{
            padding: 0.5rem 1rem;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            color: var(--text-primary);
        }}
        .pagination button:hover:not(:disabled) {{
            background: var(--hover-color);
        }}
        .pagination button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .pagination button.active {{
            background: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }}
        .pagination-info {{
            color: var(--text-secondary);
            font-size: 0.9rem;
        }}
        .page-size-select {{
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text-primary);
        }}
        /* Empty state */
        .empty-state {{
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }}
        .empty-state-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        .empty-state h3 {{
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
        }}
        /* Loading state */
        .loading {{
            text-align: center;
            padding: 2rem;
        }}
        .spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid var(--border-color);
            border-top-color: var(--accent-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .milestone-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }}
        .milestone-card {{
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }}
        .milestone-card:hover {{
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }}
        .milestone-card.active {{
            border-color: var(--accent-color);
            background: var(--accent-light);
        }}
        .milestone-card:focus {{
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }}
        .milestone-card .count {{
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }}
        .milestone-card .name {{
            font-size: 0.9rem;
            color: var(--text-secondary);
        }}
        .chart-container {{
            position: relative;
            height: 300px;
            margin-bottom: 2rem;
        }}
        .player-link, .game-link, .venue-link, .team-link {{
            color: var(--accent-color);
            cursor: pointer;
            text-decoration: underline;
        }}
        .player-link:hover, .game-link:hover, .venue-link:hover, .team-link:hover {{
            opacity: 0.8;
        }}
        .external-link {{
            color: #666;
            text-decoration: none;
            font-size: 0.85em;
            margin-left: 4px;
        }}
        .external-link:hover {{
            color: var(--accent-color);
        }}
        .checklist-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }}
        .checklist-item {{
            display: flex;
            align-items: center;
            padding: 0.5rem;
            border-radius: 4px;
            background: var(--card-bg);
        }}
        .checklist-item.seen {{
            background: #e8f5e9;
        }}
        .check-icon {{
            width: 24px;
            height: 24px;
            margin-right: 0.5rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }}
        .check-icon.checked {{
            background: #4caf50;
            color: white;
        }}
        .check-icon.unchecked {{
            background: #e0e0e0;
            color: #999;
        }}
        .checklist-details {{
            flex: 1;
        }}
        .checklist-team {{
            font-weight: 600;
        }}
        .checklist-conf {{
            font-weight: 400;
            font-size: 0.85em;
            color: var(--text-muted);
        }}
        .checklist-venue {{
            font-size: 0.85em;
            color: #666;
        }}
        .checklist-venue.visited {{
            color: #4caf50;
        }}
        .checklist-summary {{
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            gap: 2rem;
        }}
        .checklist-stat {{
            text-align: center;
        }}
        .checklist-stat-value {{
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }}
        .checklist-stat-label {{
            font-size: 0.85em;
            color: #666;
        }}
        .modal {{
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }}
        .modal.active {{
            display: flex;
        }}
        .modal-content {{
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 2rem;
            max-width: 1000px;
            max-height: 90vh;
            overflow-y: auto;
            width: 95%;
            position: relative;
        }}
        .modal-close {{
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-secondary);
        }}
        .modal-close:hover {{
            color: var(--text-primary);
        }}
        /* Box Score Modal */
        .box-score-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
        }}
        .box-score-team {{
            text-align: center;
            flex: 1;
        }}
        .box-score-team h3 {{
            font-size: 1.25rem;
            margin-bottom: 0.25rem;
        }}
        .box-score-score {{
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }}
        .box-score-vs {{
            padding: 0 2rem;
            font-size: 1.5rem;
            color: var(--text-muted);
        }}
        .box-score-section {{
            margin-bottom: 2rem;
        }}
        .box-score-section h4 {{
            margin-bottom: 0.5rem;
            color: var(--accent-color);
        }}
        .compare-select {{
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            min-width: 200px;
        }}
        .compare-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }}
        .compare-card {{
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 8px;
        }}
        .compare-card h4 {{
            margin-bottom: 0.5rem;
            color: var(--accent-color);
        }}
        .stat-row {{
            display: flex;
            justify-content: space-between;
            padding: 0.25rem 0;
            border-bottom: 1px solid var(--border-color);
        }}
        /* Toast notifications */
        .toast {{
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: var(--text-primary);
            color: var(--bg-secondary);
            padding: 1rem 1.5rem;
            border-radius: 8px;
            box-shadow: var(--shadow);
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.3s;
            z-index: 2000;
        }}
        .toast.show {{
            transform: translateY(0);
            opacity: 1;
        }}
        /* Skip to content link for accessibility */
        .skip-link {{
            position: absolute;
            top: -40px;
            left: 0;
            background: var(--accent-color);
            color: white;
            padding: 8px;
            z-index: 100;
        }}
        .skip-link:focus {{
            top: 0;
        }}
        /* Mobile-first responsive styles */
        @media (max-width: 768px) {{
            .header {{
                padding: 1rem;
            }}
            .header h1 {{
                font-size: 1.25rem;
                margin-top: 2rem;
            }}
            .header-controls {{
                top: 0.5rem;
                right: 0.5rem;
            }}
            .theme-toggle, .share-btn {{
                width: 36px;
                height: 36px;
                font-size: 1rem;
            }}
            .generated-time {{
                font-size: 0.65rem;
                right: 0.5rem;
            }}
            .stats-overview {{
                gap: 0.5rem;
                margin-top: 0.75rem;
            }}
            .stat-box {{
                padding: 0.5rem 0.75rem;
            }}
            .stat-box .number {{
                font-size: 1.25rem;
            }}
            .stat-box .label {{
                font-size: 0.75rem;
            }}
            .container {{
                padding: 1rem;
            }}
            .tabs {{
                justify-content: flex-start;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                -ms-overflow-style: none;
                padding-bottom: 0.5rem;
                flex-wrap: nowrap;
            }}
            .tabs::-webkit-scrollbar {{
                display: none;
            }}
            .tab {{
                padding: 0.5rem 0.75rem;
                font-size: 0.8rem;
                flex-shrink: 0;
                white-space: nowrap;
            }}
            .sub-tabs {{
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                flex-wrap: nowrap;
                padding-bottom: 0.5rem;
            }}
            .sub-tabs::-webkit-scrollbar {{
                display: none;
            }}
            .sub-tab {{
                flex-shrink: 0;
                white-space: nowrap;
                font-size: 0.75rem;
                padding: 0.4rem 0.75rem;
            }}
            .section {{
                padding: 1rem;
                border-radius: 8px;
            }}
            .section h2 {{
                font-size: 1.1rem;
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }}
            .section-actions {{
                width: 100%;
            }}
            .section-actions .btn {{
                width: 100%;
                text-align: center;
            }}
            .filters {{
                flex-direction: column;
                padding: 0.75rem;
                gap: 0.75rem;
            }}
            .filter-group {{
                width: 100%;
            }}
            .filter-group label {{
                font-size: 0.7rem;
            }}
            .filter-group input, .filter-group select {{
                width: 100%;
                padding: 0.6rem;
                font-size: 0.9rem;
            }}
            .clear-filters {{
                width: 100%;
                padding: 0.6rem;
            }}
            .controls {{
                flex-direction: column;
                gap: 0.75rem;
            }}
            .search-box {{
                width: 100%;
                max-width: none;
                font-size: 0.9rem;
            }}
            .compare-select {{
                width: 100%;
                min-width: auto;
            }}
            .box-score-header {{
                flex-direction: column;
                gap: 0.75rem;
            }}
            .box-score-team h3 {{
                font-size: 1rem;
            }}
            .box-score-score {{
                font-size: 2rem;
            }}
            .box-score-vs {{
                padding: 0;
                font-size: 1rem;
            }}
            .modal-content {{
                padding: 1rem;
                width: 98%;
                max-height: 95vh;
            }}
            .modal-close {{
                top: 0.5rem;
                right: 0.5rem;
            }}
            .table-container {{
                font-size: 0.75rem;
                margin: 0 -1rem;
                width: calc(100% + 2rem);
                border-radius: 0;
            }}
            th, td {{
                padding: 0.4rem 0.5rem;
            }}
            th {{
                font-size: 0.7rem;
            }}
            .sticky-col {{
                min-width: 100px;
            }}
            .milestone-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 0.5rem;
            }}
            .milestone-card {{
                padding: 0.75rem;
            }}
            .milestone-card .count {{
                font-size: 1.25rem;
            }}
            .milestone-card .name {{
                font-size: 0.8rem;
            }}
            .checklist-grid {{
                grid-template-columns: 1fr;
            }}
            .checklist-summary {{
                flex-wrap: wrap;
                gap: 1rem;
                padding: 0.75rem;
            }}
            .checklist-stat-value {{
                font-size: 1.25rem;
            }}
            .compare-grid {{
                grid-template-columns: 1fr;
            }}
            .chart-container {{
                height: 250px;
            }}
            .calendar-months {{
                grid-template-columns: 1fr;
            }}
            .monthly-calendar {{
                font-size: 0.7rem;
            }}
            .monthly-calendar .day-cell {{
                min-height: 60px;
                padding: 2px;
            }}
            .monthly-calendar .day-games {{
                font-size: 0.6rem;
            }}
            .pagination {{
                flex-wrap: wrap;
                gap: 0.25rem;
            }}
            .pagination button {{
                padding: 0.4rem 0.6rem;
                font-size: 0.8rem;
            }}
            .toast {{
                bottom: 1rem;
                right: 1rem;
                left: 1rem;
                text-align: center;
            }}
            #school-map {{
                height: 350px !important;
            }}
            #map-legend {{
                flex-direction: column;
                gap: 0.5rem;
            }}
            .onthisday-game {{
                padding: 0.75rem !important;
            }}
            .onthisday-game > div {{
                flex-direction: column !important;
                align-items: flex-start !important;
            }}
        }}

        /* Extra small screens */
        @media (max-width: 480px) {{
            .header h1 {{
                font-size: 1.1rem;
            }}
            .stat-box {{
                padding: 0.4rem 0.5rem;
            }}
            .stat-box .number {{
                font-size: 1rem;
            }}
            .stat-box .label {{
                font-size: 0.65rem;
            }}
            .tab {{
                padding: 0.4rem 0.6rem;
                font-size: 0.75rem;
            }}
            .milestone-grid {{
                grid-template-columns: 1fr;
            }}
            th, td {{
                padding: 0.3rem 0.4rem;
                font-size: 0.7rem;
            }}
        }}
        /* Print styles */
        @media print {{
            .header-controls, .tabs, .sub-tabs, .filters, .pagination, .btn, .modal {{
                display: none !important;
            }}
            .section {{
                display: block !important;
                box-shadow: none;
                page-break-inside: avoid;
            }}
            .table-container {{
                max-height: none;
                overflow: visible;
            }}
        }}
    </style>
</head>
<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <div class="header">
        <div class="header-controls">
            <button class="share-btn" onclick="shareCurrentView()" title="Share this view" aria-label="Share">&#128279;</button>
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode" aria-label="Toggle theme">&#127769;</button>
        </div>
        <h1>College Basketball Stats</h1>
        <div class="stats-overview">
            <div class="stat-box">
                <div class="number">{total_games}</div>
                <div class="label">Games</div>
            </div>
            <div class="stat-box">
                <div class="number">{total_players}</div>
                <div class="label">Players</div>
            </div>
            <div class="stat-box">
                <div class="number">{total_teams}</div>
                <div class="label">Teams</div>
            </div>
        </div>
        <div class="generated-time">Generated: {generated_time}</div>
    </div>

    <div class="container" id="main-content">
        <div class="tabs" role="tablist">
            <button class="tab active" onclick="showSection('games')" role="tab" aria-selected="true" data-section="games" tabindex="0">Games</button>
            <button class="tab" onclick="showSection('players')" role="tab" aria-selected="false" data-section="players" tabindex="-1">Players</button>
            <button class="tab" onclick="showSection('milestones')" role="tab" aria-selected="false" data-section="milestones" tabindex="-1">Milestones</button>
            <button class="tab" onclick="showSection('teams')" role="tab" aria-selected="false" data-section="teams" tabindex="-1">Teams</button>
            <button class="tab" onclick="showSection('venues')" role="tab" aria-selected="false" data-section="venues" tabindex="-1">Venues</button>
            <button class="tab" onclick="showSection('calendar')" role="tab" aria-selected="false" data-section="calendar" tabindex="-1">Calendar</button>
            <button class="tab" onclick="showSection('checklist')" role="tab" aria-selected="false" data-section="checklist" tabindex="-1">Checklist</button>
            <button class="tab" onclick="showSection('map')" role="tab" aria-selected="false" data-section="map" tabindex="-1">Map</button>
            <button class="tab" onclick="showSection('compare')" role="tab" aria-selected="false" data-section="compare" tabindex="-1">Compare</button>
            <button class="tab" onclick="showSection('charts')" role="tab" aria-selected="false" data-section="charts" tabindex="-1">Charts</button>
        </div>

        <div id="games" class="section active" role="tabpanel">
            <h2>
                Game Log
                <div class="section-actions">
                    <button class="btn btn-secondary" onclick="downloadCSV('games')">Download CSV</button>
                </div>
            </h2>
            <div class="filters" id="games-filters">
                <div class="filter-group">
                    <label for="games-search">Search</label>
                    <input type="text" id="games-search" class="search-box" placeholder="Search games..." onkeyup="applyFilters('games')">
                </div>
                <div class="filter-group">
                    <label for="games-gender">Gender</label>
                    <select id="games-gender" onchange="applyFilters('games')">
                        <option value="">All</option>
                        <option value="M">Men's</option>
                        <option value="W">Women's</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="games-date-from">From Date</label>
                    <input type="date" id="games-date-from" onchange="applyFilters('games')">
                </div>
                <div class="filter-group">
                    <label for="games-date-to">To Date</label>
                    <input type="date" id="games-date-to" onchange="applyFilters('games')">
                </div>
                <div class="filter-group">
                    <label for="games-team">Team</label>
                    <select id="games-team" onchange="applyFilters('games')">
                        <option value="">All Teams</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="games-conference">Conference</label>
                    <select id="games-conference" onchange="applyFilters('games')">
                        <option value="">All Conferences</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="games-margin">Min Margin</label>
                    <input type="number" id="games-margin" min="0" max="50" placeholder="0" onchange="applyFilters('games')">
                </div>
                <div class="filter-group" style="display:flex;align-items:center;gap:0.5rem;">
                    <input type="checkbox" id="games-ot" onchange="applyFilters('games')">
                    <label for="games-ot" style="margin:0;">OT Only</label>
                </div>
                <button class="clear-filters" onclick="clearFilters('games')">Clear Filters</button>
            </div>
            <div class="table-container">
                <table id="games-table" aria-label="Game Log">
                    <thead>
                        <tr>
                            <th onclick="sortTable('games-table', 0)" class="tooltip" data-tooltip="Game date">Date</th>
                            <th onclick="sortTable('games-table', 1)" class="tooltip" data-tooltip="Visiting team">Away Team</th>
                            <th onclick="sortTable('games-table', 2)" class="tooltip" data-tooltip="Final score">Score</th>
                            <th onclick="sortTable('games-table', 3)" class="tooltip" data-tooltip="Home team">Home Team</th>
                            <th onclick="sortTable('games-table', 4)" class="tooltip" data-tooltip="Click to see all games">Venue</th>
                            <th onclick="sortTable('games-table', 5)">City</th>
                            <th onclick="sortTable('games-table', 6)">State</th>
                            <th onclick="sortTable('games-table', 7)">Notes</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            <div class="pagination" id="games-pagination"></div>
        </div>

        <div id="players" class="section" role="tabpanel">
            <h2>
                Player Statistics
                <div class="section-actions">
                    <button class="btn btn-secondary" onclick="downloadCSV('players')">Download CSV</button>
                </div>
            </h2>
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('players', 'stats')">Stats</button>
                <button class="sub-tab" onclick="showSubSection('players', 'highs')">Career Highs</button>
                <button class="sub-tab" onclick="showSubSection('players', 'gamelogs')">Game Logs</button>
            </div>

            <div id="players-stats" class="sub-section active">
                <div class="filters" id="players-filters">
                    <div class="filter-group">
                        <label for="players-search">Search</label>
                        <input type="text" id="players-search" class="search-box" placeholder="Search players..." onkeyup="applyFilters('players')">
                    </div>
                    <div class="filter-group">
                        <label for="players-gender">Gender</label>
                        <select id="players-gender" onchange="applyFilters('players')">
                            <option value="">All</option>
                            <option value="M">Men's</option>
                            <option value="W">Women's</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label for="players-team">Team</label>
                        <select id="players-team" onchange="applyFilters('players')">
                            <option value="">All Teams</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label for="players-conference">Conference</label>
                        <select id="players-conference" onchange="applyFilters('players')">
                            <option value="">All Conferences</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label for="players-min-games">Min Games</label>
                        <input type="number" id="players-min-games" min="1" placeholder="1" onchange="applyFilters('players')">
                    </div>
                    <div class="filter-group">
                        <label for="players-min-ppg">Min PPG</label>
                        <input type="number" id="players-min-ppg" min="0" step="0.1" placeholder="0" onchange="applyFilters('players')">
                    </div>
                    <button class="clear-filters" onclick="clearFilters('players')">Clear Filters</button>
                </div>
                <div class="table-container table-scroll">
                    <table id="players-table" aria-label="Player Statistics">
                        <thead>
                            <tr>
                                <th onclick="sortTable('players-table', 0)" class="sticky-col">Player</th>
                                <th onclick="sortTable('players-table', 1)">Team</th>
                                <th onclick="sortTable('players-table', 2)" class="tooltip" data-tooltip="Games played">GP</th>
                                <th onclick="sortTable('players-table', 3)" class="tooltip" data-tooltip="Minutes per game">MPG</th>
                                <th onclick="sortTable('players-table', 4)" class="tooltip" data-tooltip="Points per game">PPG</th>
                                <th onclick="sortTable('players-table', 5)" class="tooltip" data-tooltip="Rebounds per game">RPG</th>
                                <th onclick="sortTable('players-table', 6)" class="tooltip" data-tooltip="Assists per game">APG</th>
                                <th onclick="sortTable('players-table', 7)" class="tooltip" data-tooltip="Steals per game">SPG</th>
                                <th onclick="sortTable('players-table', 8)" class="tooltip" data-tooltip="Blocks per game">BPG</th>
                                <th onclick="sortTable('players-table', 9)" class="tooltip" data-tooltip="Field goals made">FGM</th>
                                <th onclick="sortTable('players-table', 10)" class="tooltip" data-tooltip="Field goals attempted">FGA</th>
                                <th onclick="sortTable('players-table', 11)" class="tooltip" data-tooltip="Field goal percentage">FG%</th>
                                <th onclick="sortTable('players-table', 12)" class="tooltip" data-tooltip="Three-pointers made">3PM</th>
                                <th onclick="sortTable('players-table', 13)" class="tooltip" data-tooltip="Three-pointers attempted">3PA</th>
                                <th onclick="sortTable('players-table', 14)" class="tooltip" data-tooltip="Three-point percentage">3P%</th>
                                <th onclick="sortTable('players-table', 15)" class="tooltip" data-tooltip="Free throws made">FTM</th>
                                <th onclick="sortTable('players-table', 16)" class="tooltip" data-tooltip="Free throws attempted">FTA</th>
                                <th onclick="sortTable('players-table', 17)" class="tooltip" data-tooltip="Free throw percentage">FT%</th>
                                <th onclick="sortTable('players-table', 18)" class="tooltip" data-tooltip="Total points">PTS</th>
                                <th onclick="sortTable('players-table', 19)" class="tooltip" data-tooltip="Total rebounds">REB</th>
                                <th onclick="sortTable('players-table', 20)" class="tooltip" data-tooltip="Total assists">AST</th>
                                <th onclick="sortTable('players-table', 21)" class="tooltip" data-tooltip="Total steals">STL</th>
                                <th onclick="sortTable('players-table', 22)" class="tooltip" data-tooltip="Total blocks">BLK</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
                <div class="pagination" id="players-pagination"></div>
            </div>

            <div id="players-highs" class="sub-section">
                <div class="table-container">
                    <table id="highs-table" aria-label="Career Highs">
                        <thead>
                            <tr>
                                <th onclick="sortTable('highs-table', 0)">Player</th>
                                <th onclick="sortTable('highs-table', 1)">Team</th>
                                <th onclick="sortTable('highs-table', 2)" class="tooltip" data-tooltip="Career high in points">High PTS</th>
                                <th onclick="sortTable('highs-table', 3)" class="tooltip" data-tooltip="Career high in rebounds">High REB</th>
                                <th onclick="sortTable('highs-table', 4)" class="tooltip" data-tooltip="Career high in assists">High AST</th>
                                <th onclick="sortTable('highs-table', 5)" class="tooltip" data-tooltip="Career high in three-pointers made">High 3PM</th>
                                <th onclick="sortTable('highs-table', 6)" class="tooltip" data-tooltip="Best game score (Hollinger formula)">Best GS</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="players-gamelogs" class="sub-section">
                <div class="search-container">
                    <input type="text" class="search-box" id="gamelog-player-search" placeholder="Search for a player..." list="gamelog-player-list" oninput="searchPlayerGameLog()" aria-label="Search for player game log">
                    <datalist id="gamelog-player-list"></datalist>
                </div>
                <div class="table-container" id="gamelog-container">
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128203;</div>
                        <h3>Search for a player</h3>
                        <p>Type a player name above to view their game log</p>
                    </div>
                </div>
            </div>
        </div>

        <div id="milestones" class="section" role="tabpanel">
            <h2>
                Milestones
                <div class="section-actions">
                    <button class="btn btn-secondary" onclick="downloadCSV('milestones')">Download CSV</button>
                </div>
            </h2>
            <div class="milestone-grid" id="milestone-grid" role="listbox"></div>
            <div id="milestones-empty" class="empty-state" style="display:none;">
                <div class="empty-state-icon">&#127942;</div>
                <h3>No milestones yet</h3>
                <p>Milestones will appear here as players achieve them</p>
            </div>
            <div class="table-container">
                <table id="milestones-table" aria-label="Milestone Details">
                    <thead>
                        <tr>
                            <th onclick="sortTable('milestones-table', 0)">Date</th>
                            <th onclick="sortTable('milestones-table', 1)">Player</th>
                            <th onclick="sortTable('milestones-table', 2)">Team</th>
                            <th onclick="sortTable('milestones-table', 3)">Opponent</th>
                            <th>Detail</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>

        <div id="teams" class="section" role="tabpanel">
            <h2>
                Team Statistics
                <div class="section-actions">
                    <button class="btn btn-secondary" onclick="downloadCSV('teams')">Download CSV</button>
                </div>
            </h2>
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('teams', 'records')">Records</button>
                <button class="sub-tab" onclick="showSubSection('teams', 'streaks')">Streaks</button>
                <button class="sub-tab" onclick="showSubSection('teams', 'splits')">Home/Away</button>
                <button class="sub-tab" onclick="showSubSection('teams', 'conference')">Conference</button>
                <button class="sub-tab" onclick="showSubSection('teams', 'headtohead')">Head-to-Head</button>
            </div>

            <div id="teams-records" class="sub-section active">
                <input type="text" class="search-box" placeholder="Search teams..." onkeyup="filterTable('teams-table', this.value)">
                <div class="table-container">
                    <table id="teams-table" aria-label="Team Records">
                        <thead>
                            <tr>
                                <th onclick="sortTable('teams-table', 0)">Team</th>
                                <th onclick="sortTable('teams-table', 1)" class="tooltip" data-tooltip="Games played">GP</th>
                                <th onclick="sortTable('teams-table', 2)">Wins</th>
                                <th onclick="sortTable('teams-table', 3)">Losses</th>
                                <th onclick="sortTable('teams-table', 4)" class="tooltip" data-tooltip="Win percentage">Win%</th>
                                <th onclick="sortTable('teams-table', 5)" class="tooltip" data-tooltip="Points per game">PPG</th>
                                <th onclick="sortTable('teams-table', 6)" class="tooltip" data-tooltip="Points allowed per game">PAPG</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="teams-streaks" class="sub-section">
                <div class="table-container">
                    <table id="streaks-table" aria-label="Team Streaks">
                        <thead>
                            <tr>
                                <th onclick="sortTable('streaks-table', 0)">Team</th>
                                <th onclick="sortTable('streaks-table', 1)" class="tooltip" data-tooltip="Current win/loss streak">Current</th>
                                <th onclick="sortTable('streaks-table', 2)" class="tooltip" data-tooltip="Longest winning streak">Best Win</th>
                                <th onclick="sortTable('streaks-table', 3)" class="tooltip" data-tooltip="Longest losing streak">Worst Loss</th>
                                <th onclick="sortTable('streaks-table', 4)" class="tooltip" data-tooltip="Record in last 5 games">Last 5</th>
                                <th onclick="sortTable('streaks-table', 5)" class="tooltip" data-tooltip="Record in last 10 games">Last 10</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="teams-splits" class="sub-section">
                <div class="table-container">
                    <table id="splits-table" aria-label="Home/Away Splits">
                        <thead>
                            <tr>
                                <th onclick="sortTable('splits-table', 0)">Team</th>
                                <th onclick="sortTable('splits-table', 1)">Home W-L</th>
                                <th onclick="sortTable('splits-table', 2)">Home%</th>
                                <th onclick="sortTable('splits-table', 3)">Away W-L</th>
                                <th onclick="sortTable('splits-table', 4)">Away%</th>
                                <th onclick="sortTable('splits-table', 5)">Neutral</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="teams-conference" class="sub-section">
                <div class="table-container">
                    <table id="conference-table" aria-label="Conference Standings">
                        <thead>
                            <tr>
                                <th onclick="sortTable('conference-table', 0)">Conference</th>
                                <th onclick="sortTable('conference-table', 1)">Team</th>
                                <th onclick="sortTable('conference-table', 2)">Conf W-L</th>
                                <th onclick="sortTable('conference-table', 3)">Conf%</th>
                                <th onclick="sortTable('conference-table', 4)">Overall</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="teams-headtohead" class="sub-section">
                <div class="filter-row" style="margin-bottom: 1rem;">
                    <select id="h2h-team1" onchange="updateHeadToHead()">
                        <option value="">Select Team 1</option>
                    </select>
                    <span style="margin: 0 0.5rem;">vs</span>
                    <select id="h2h-team2" onchange="updateHeadToHead()">
                        <option value="">Select Team 2</option>
                    </select>
                </div>
                <div id="h2h-result" class="card" style="display:none;">
                    <div id="h2h-summary" style="text-align:center; margin-bottom:1rem;"></div>
                    <div id="h2h-games" class="table-container"></div>
                </div>
            </div>

        </div>

        <div id="venues" class="section" role="tabpanel">
            <h2>
                Venue Statistics
                <div class="section-actions">
                    <button class="btn btn-secondary" onclick="downloadCSV('venues')">Download CSV</button>
                </div>
            </h2>
            <input type="text" class="search-box" placeholder="Search venues..." onkeyup="filterTable('venues-table', this.value)">
            <div class="table-container">
                <table id="venues-table" aria-label="Venue Statistics">
                    <thead>
                        <tr>
                            <th onclick="sortTable('venues-table', 0)">Venue</th>
                            <th onclick="sortTable('venues-table', 1)">City</th>
                            <th onclick="sortTable('venues-table', 2)">State</th>
                            <th onclick="sortTable('venues-table', 3)" class="tooltip" data-tooltip="Games played at venue">Games</th>
                            <th onclick="sortTable('venues-table', 4)" class="tooltip" data-tooltip="Home team wins">Home W</th>
                            <th onclick="sortTable('venues-table', 5)" class="tooltip" data-tooltip="Away team wins">Away W</th>
                            <th onclick="sortTable('venues-table', 6)" class="tooltip" data-tooltip="Avg home team points">Avg Home</th>
                            <th onclick="sortTable('venues-table', 7)" class="tooltip" data-tooltip="Avg away team points">Avg Away</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>

        <div id="calendar" class="section" role="tabpanel">
            <h2>Calendar</h2>
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('calendar', 'monthly')">Monthly View</button>
                <button class="sub-tab" onclick="showSubSection('calendar', 'season')">Season Day Tracker</button>
                <button class="sub-tab" onclick="showSubSection('calendar', 'onthisday')">On This Day</button>
            </div>

            <div id="calendar-monthly" class="sub-section active">
                <div class="filter-row" style="margin-bottom: 1rem; justify-content: center;">
                    <button class="btn btn-secondary" onclick="changeMonth(-1)">&larr; Prev</button>
                    <span id="calendar-month-label" style="font-size: 1.25rem; font-weight: bold; margin: 0 1rem;"></span>
                    <button class="btn btn-secondary" onclick="changeMonth(1)">Next &rarr;</button>
                </div>
                <div id="monthly-calendar" class="monthly-calendar"></div>
            </div>

            <div id="calendar-season" class="sub-section">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">Track your progress toward seeing a game on every day of the basketball season (year-agnostic).</p>
                <div id="calendar-grid" class="calendar-grid"></div>
                <div class="calendar-legend" style="margin-top: 1rem; display: flex; gap: 1rem; align-items: center; flex-wrap: wrap;">
                    <span><span class="calendar-day has-game" style="display: inline-block; width: 20px; height: 20px; vertical-align: middle;"></span> Game attended</span>
                    <span><span class="calendar-day has-multiple" style="display: inline-block; width: 20px; height: 20px; vertical-align: middle;"></span> Multiple games</span>
                    <span><span class="calendar-day" style="display: inline-block; width: 20px; height: 20px; vertical-align: middle; background: var(--bg-secondary); border: 1px solid var(--border-color);"></span> No game yet</span>
                </div>
            </div>

            <div id="calendar-onthisday" class="sub-section">
                <div class="onthisday-header" style="text-align: center; margin-bottom: 1.5rem;">
                    <h3 id="onthisday-date" style="font-size: 1.5rem; color: var(--accent-color);"></h3>
                    <p style="color: var(--text-secondary);">Games you attended on this date in previous years</p>
                </div>
                <div id="onthisday-content"></div>
                <div id="onthisday-empty" class="empty-state" style="display: none;">
                    <div class="empty-state-icon">&#128197;</div>
                    <h3>No games on this day</h3>
                    <p>You haven't attended any games on this date in previous years</p>
                </div>
            </div>
        </div>

        <div id="checklist" class="section" role="tabpanel">
            <h2>Conference Checklist</h2>
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">Track which teams you've seen play and which home arenas you've visited.</p>
            <div class="filters" style="margin-bottom: 1rem;">
                <div class="filter-group">
                    <label for="checklist-conference">Conference</label>
                    <select id="checklist-conference" onchange="populateChecklist()">
                        <option value="">Select Conference...</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="checklist-gender">Gender</label>
                    <select id="checklist-gender" onchange="populateChecklist()">
                        <option value="">All</option>
                        <option value="M">Men's</option>
                        <option value="W">Women's</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="checklist-team-filter">Teams</label>
                    <select id="checklist-team-filter" onchange="populateChecklist()">
                        <option value="all">All Teams</option>
                        <option value="seen">Seen</option>
                        <option value="unseen">Not Seen</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="checklist-venue-filter">Venues</label>
                    <select id="checklist-venue-filter" onchange="populateChecklist()">
                        <option value="all">All Venues</option>
                        <option value="visited">Visited</option>
                        <option value="unvisited">Not Visited</option>
                    </select>
                </div>
            </div>
            <div id="checklist-content"></div>
        </div>

        <div id="map" class="section" role="tabpanel">
            <h2>School Map</h2>
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">Interactive map of D1 basketball schools. Green = visited, Blue = seen (away), Gray = not seen.</p>
            <div class="filters" style="margin-bottom: 1rem;">
                <div class="filter-group">
                    <label for="map-conference">Conference</label>
                    <select id="map-conference" onchange="updateMapMarkers()">
                        <option value="All D1">All D1</option>
                    </select>
                </div>
                <div class="filter-group">
                    <label for="map-filter">Show</label>
                    <select id="map-filter" onchange="updateMapMarkers()">
                        <option value="all">All Schools</option>
                        <option value="visited">Visited (Home Arena)</option>
                        <option value="seen">Seen (Any Location)</option>
                        <option value="unseen">Not Seen</option>
                    </select>
                </div>
            </div>
            <div id="school-map" style="height: 600px; border-radius: 8px; border: 1px solid var(--border-color);"></div>
            <div id="map-legend" style="margin-top: 1rem; display: flex; gap: 1.5rem; flex-wrap: wrap;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 16px; height: 16px; background: #2E7D32; border-radius: 50%; display: inline-block;"></span>
                    <span>Visited (Home Arena)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 16px; height: 16px; background: #1976D2; border-radius: 50%; display: inline-block;"></span>
                    <span>Seen (Away Only)</span>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <span style="width: 16px; height: 16px; background: #9E9E9E; border-radius: 50%; display: inline-block;"></span>
                    <span>Not Seen</span>
                </div>
            </div>
        </div>

        <div id="compare" class="section" role="tabpanel">
            <h2>Player Comparison</h2>
            <div class="controls">
                <select class="compare-select" id="compare-player1" onchange="updateComparison()" aria-label="Select first player">
                    <option value="">Select Player 1...</option>
                </select>
                <span>vs</span>
                <select class="compare-select" id="compare-player2" onchange="updateComparison()" aria-label="Select second player">
                    <option value="">Select Player 2...</option>
                </select>
            </div>
            <div class="compare-grid" id="compare-grid">
                <div class="empty-state">
                    <div class="empty-state-icon">&#128101;</div>
                    <h3>Select two players</h3>
                    <p>Choose players from the dropdowns above to compare their statistics</p>
                </div>
            </div>
            <div class="chart-container">
                <canvas id="compare-chart"></canvas>
            </div>
        </div>

        <div id="charts" class="section" role="tabpanel">
            <h2>Statistics Charts</h2>
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showChart('scoring')">Top Scorers</button>
                <button class="sub-tab" onclick="showChart('rebounds')">Top Rebounders</button>
                <button class="sub-tab" onclick="showChart('assists')">Top Assists</button>
                <button class="sub-tab" onclick="showChart('efficiency')">Shooting Efficiency</button>
                <button class="sub-tab" onclick="showChart('teams')">Team Wins</button>
                <button class="sub-tab" onclick="showChart('trends')">Scoring Trends</button>
            </div>
            <div class="chart-container">
                <canvas id="stats-chart"></canvas>
            </div>
        </div>
    </div>

    <!-- Player Detail Modal -->
    <div class="modal" id="player-modal" role="dialog" aria-labelledby="player-modal-title" onclick="if(event.target === this) closeModal('player-modal')">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('player-modal')" aria-label="Close">&times;</button>
            <div id="player-detail"></div>
        </div>
    </div>

    <!-- Game Detail Modal (Box Score) -->
    <div class="modal" id="game-modal" role="dialog" aria-labelledby="game-modal-title" onclick="if(event.target === this) closeModal('game-modal')">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('game-modal')" aria-label="Close">&times;</button>
            <div id="game-detail"></div>
        </div>
    </div>

    <!-- Venue Detail Modal -->
    <div class="modal" id="venue-modal" role="dialog" aria-labelledby="venue-modal-title" onclick="if(event.target === this) closeModal('venue-modal')">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('venue-modal')" aria-label="Close">&times;</button>
            <div id="venue-detail"></div>
        </div>
    </div>

    <!-- Toast container -->
    <div id="toast" class="toast"></div>

    <script>
        const DATA = {json_data};
        let currentSort = {{}};
        let statsChart = null;
        let compareChart = null;
        let currentMilestoneType = null;
        let currentMilestoneData = [];

        // Pagination state
        const pagination = {{
            games: {{ page: 1, pageSize: 50, total: 0 }},
            players: {{ page: 1, pageSize: 1000, total: 0 }},  // Show all players by default
        }};

        // Filtered data cache
        let filteredData = {{
            games: [],
            players: [],
        }};

        // Team to conference mapping (loaded from conferenceChecklist data)
        function getTeamConference(teamName) {{
            if (!teamName) return '';
            const checklist = DATA.conferenceChecklist || {{}};
            for (const [confName, confData] of Object.entries(checklist)) {{
                if (confData.teams && confData.teams.some(t => t.team === teamName || t.name === teamName)) {{
                    return confName;
                }}
            }}
            // Fallback: check teams data
            const teams = DATA.teams || [];
            for (const team of teams) {{
                if (team.Team === teamName && team.Conference) {{
                    return team.Conference;
                }}
            }}
            return '';
        }}

        // Get Sports Reference box score URL (extracted from original HTML)
        function getSportsRefUrl(game) {{
            // Use the actual URL extracted from the HTML canonical link
            if (game.SportsRefURL) {{
                return game.SportsRefURL;
            }}
            // Fallback: construct URL from date and slug
            const dateSort = game.DateSort || '';
            const slug = game.HomeTeamSlug || '';
            if (dateSort && slug) {{
                const formattedDate = dateSort.slice(0, 4) + '-' + dateSort.slice(4, 6) + '-' + dateSort.slice(6, 8);
                return `https://www.sports-reference.com/cbb/boxscores/${{formattedDate}}-${{slug}}.html`;
            }}
            return '#';
        }}

        function getPlayerSportsRefUrl(playerId) {{
            if (!playerId) return '#';
            return `https://www.sports-reference.com/cbb/players/${{playerId}}.html`;
        }}

        // Stat thresholds for highlighting
        const STAT_THRESHOLDS = {{
            ppg: {{ excellent: 20, good: 15, average: 10 }},
            rpg: {{ excellent: 10, good: 7, average: 5 }},
            apg: {{ excellent: 7, good: 5, average: 3 }},
            fgPct: {{ excellent: 0.50, good: 0.45, average: 0.40 }},
            threePct: {{ excellent: 0.40, good: 0.35, average: 0.30 }},
        }};

        // Theme toggle
        function toggleTheme() {{
            const body = document.body;
            const isDark = body.getAttribute('data-theme') === 'dark';
            body.setAttribute('data-theme', isDark ? 'light' : 'dark');
            document.querySelector('.theme-toggle').innerHTML = isDark ? '&#127769;' : '&#9728;';
            localStorage.setItem('theme', isDark ? 'light' : 'dark');
        }}

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {{
            document.body.setAttribute('data-theme', 'dark');
            document.querySelector('.theme-toggle').innerHTML = '&#9728;';
        }}

        // URL hash-based routing
        function updateURL(section, params = {{}}) {{
            let hash = section;
            const paramPairs = Object.entries(params).filter(([k, v]) => v);
            if (paramPairs.length > 0) {{
                hash += '?' + paramPairs.map(([k, v]) => `${{k}}=${{encodeURIComponent(v)}}`).join('&');
            }}
            history.replaceState(null, '', '#' + hash);
        }}

        function parseURL() {{
            const hash = window.location.hash.slice(1);
            if (!hash) return {{ section: 'games', params: {{}} }};

            const [section, queryString] = hash.split('?');
            const params = {{}};
            if (queryString) {{
                queryString.split('&').forEach(pair => {{
                    const [key, value] = pair.split('=');
                    params[key] = decodeURIComponent(value);
                }});
            }}
            return {{ section, params }};
        }}

        function shareCurrentView() {{
            const url = window.location.href;
            navigator.clipboard.writeText(url).then(() => {{
                showToast('Link copied to clipboard!');
            }}).catch(() => {{
                showToast('Could not copy link');
            }});
        }}

        function showToast(message) {{
            const toast = document.getElementById('toast');
            toast.textContent = message;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 3000);
        }}

        function showSection(sectionId) {{
            document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(t => {{
                t.classList.remove('active');
                t.setAttribute('aria-selected', 'false');
                t.setAttribute('tabindex', '-1');
            }});
            document.getElementById(sectionId).classList.add('active');
            const tab = document.querySelector(`[data-section="${{sectionId}}"]`);
            if (tab) {{
                tab.classList.add('active');
                tab.setAttribute('aria-selected', 'true');
                tab.setAttribute('tabindex', '0');
            }}
            updateURL(sectionId);

            // Initialize map when first shown (Leaflet needs visible container)
            if (sectionId === 'map' && !schoolMap) {{
                setTimeout(initMap, 100);
            }} else if (sectionId === 'map' && schoolMap) {{
                schoolMap.invalidateSize();
            }}
        }}

        function showSubSection(parentId, subId) {{
            const parent = document.getElementById(parentId);
            parent.querySelectorAll('.sub-section').forEach(s => s.classList.remove('active'));
            parent.querySelectorAll('.sub-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(parentId + '-' + subId).classList.add('active');
            event.target.classList.add('active');
            updateURL(parentId, {{ sub: subId }});
        }}

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            // Tab navigation with arrow keys
            if (e.target.classList.contains('tab')) {{
                const tabs = Array.from(document.querySelectorAll('.tab'));
                const currentIndex = tabs.indexOf(e.target);
                if (e.key === 'ArrowRight' && currentIndex < tabs.length - 1) {{
                    tabs[currentIndex + 1].focus();
                    tabs[currentIndex + 1].click();
                }} else if (e.key === 'ArrowLeft' && currentIndex > 0) {{
                    tabs[currentIndex - 1].focus();
                    tabs[currentIndex - 1].click();
                }}
            }}
            // Close modals with Escape
            if (e.key === 'Escape') {{
                document.querySelectorAll('.modal.active').forEach(m => m.classList.remove('active'));
            }}
        }});

        function filterTable(tableId, query) {{
            const table = document.getElementById(tableId);
            const rows = table.querySelectorAll('tbody tr');
            const lowerQuery = query.toLowerCase();
            rows.forEach(row => {{
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(lowerQuery) ? '' : 'none';
            }});
        }}

        function filterByTeam(teamName) {{
            // Set the team dropdown and apply filters
            const select = document.getElementById('games-team');
            if (select) {{
                select.value = teamName;
                applyFilters('games');
            }}
        }}

        function updateHeadToHead() {{
            const team1 = document.getElementById('h2h-team1').value;
            const team2 = document.getElementById('h2h-team2').value;
            const resultDiv = document.getElementById('h2h-result');
            const summaryDiv = document.getElementById('h2h-summary');
            const gamesDiv = document.getElementById('h2h-games');

            if (!team1 || !team2 || team1 === team2) {{
                resultDiv.style.display = 'none';
                return;
            }}

            // Find all games between these two teams
            const matchups = (DATA.games || []).filter(g =>
                (g['Away Team'] === team1 && g['Home Team'] === team2) ||
                (g['Away Team'] === team2 && g['Home Team'] === team1)
            ).sort((a, b) => (b.Date || '').localeCompare(a.Date || ''));

            if (matchups.length === 0) {{
                resultDiv.style.display = 'block';
                summaryDiv.innerHTML = `<h3>No games found between ${{team1}} and ${{team2}}</h3>`;
                gamesDiv.innerHTML = '';
                return;
            }}

            // Calculate record
            let team1Wins = 0, team2Wins = 0;
            matchups.forEach(g => {{
                const awayScore = parseInt(g['Away Score']) || 0;
                const homeScore = parseInt(g['Home Score']) || 0;
                const awayWon = awayScore > homeScore;
                if ((g['Away Team'] === team1 && awayWon) || (g['Home Team'] === team1 && !awayWon)) {{
                    team1Wins++;
                }} else {{
                    team2Wins++;
                }}
            }});

            resultDiv.style.display = 'block';
            summaryDiv.innerHTML = `
                <h3 style="margin-bottom:0.5rem;">${{team1}} vs ${{team2}}</h3>
                <div style="font-size:2rem;font-weight:bold;color:var(--accent-color);">${{team1Wins}} - ${{team2Wins}}</div>
                <p style="color:var(--text-secondary);">${{matchups.length}} game${{matchups.length !== 1 ? 's' : ''}}</p>
            `;

            gamesDiv.innerHTML = `
                <table>
                    <thead><tr><th>Date</th><th>Matchup</th><th>Score</th><th>Venue</th></tr></thead>
                    <tbody>
                        ${{matchups.map(g => {{
                            const awayScore = parseInt(g['Away Score']) || 0;
                            const homeScore = parseInt(g['Home Score']) || 0;
                            const awayWon = awayScore > homeScore;
                            const winner = awayWon ? g['Away Team'] : g['Home Team'];
                            return `
                                <tr class="clickable-row" onclick="showGameDetail('${{g.GameID}}')">
                                    <td><span class="game-link">${{g.Date}}</span></td>
                                    <td>${{g['Away Team']}} @ ${{g['Home Team']}}</td>
                                    <td><strong>${{awayWon ? awayScore : homeScore}}</strong>-${{awayWon ? homeScore : awayScore}} (${{winner}})</td>
                                    <td>${{g.Venue || ''}}</td>
                                </tr>
                            `;
                        }}).join('')}}
                    </tbody>
                </table>
            `;
        }}

        function applyFilters(type) {{
            if (type === 'games') {{
                applyGamesFilters();
            }} else if (type === 'players') {{
                applyPlayersFilters();
            }}
        }}

        function applyGamesFilters() {{
            const search = document.getElementById('games-search').value.toLowerCase();
            const gender = document.getElementById('games-gender').value;
            const dateFrom = document.getElementById('games-date-from').value;
            const dateTo = document.getElementById('games-date-to').value;
            const team = document.getElementById('games-team').value;
            const conference = document.getElementById('games-conference').value;
            const minMargin = parseInt(document.getElementById('games-margin').value) || 0;
            const otOnly = document.getElementById('games-ot').checked;

            filteredData.games = (DATA.games || []).filter(game => {{
                const text = `${{game['Away Team']}} ${{game['Home Team']}} ${{game.Venue || ''}}`.toLowerCase();
                if (search && !text.includes(search)) return false;
                if (gender && game.Gender !== gender) return false;
                if (dateFrom && game.Date < dateFrom) return false;
                if (dateTo && game.Date > dateTo) return false;
                if (team && game['Away Team'] !== team && game['Home Team'] !== team) return false;
                if (conference) {{
                    const awayConf = getTeamConference(game['Away Team']);
                    const homeConf = getTeamConference(game['Home Team']);
                    if (awayConf !== conference && homeConf !== conference) return false;
                }}
                if (minMargin > 0) {{
                    const margin = Math.abs((game['Away Score'] || 0) - (game['Home Score'] || 0));
                    if (margin < minMargin) return false;
                }}
                if (otOnly) {{
                    const linescore = game.Linescore || {{}};
                    const otPeriods = (linescore.away || {{}}).OT || [];
                    if (otPeriods.length === 0) return false;
                }}
                return true;
            }});

            pagination.games.page = 1;
            pagination.games.total = filteredData.games.length;
            renderGamesTable();
        }}

        function applyPlayersFilters() {{
            const search = document.getElementById('players-search').value.toLowerCase();
            const gender = document.getElementById('players-gender').value;
            const team = document.getElementById('players-team').value;
            const conference = document.getElementById('players-conference').value;
            const minGames = parseInt(document.getElementById('players-min-games').value) || 0;
            const minPPG = parseFloat(document.getElementById('players-min-ppg').value) || 0;

            filteredData.players = (DATA.players || []).filter(player => {{
                const text = `${{player.Player}} ${{player.Team}}`.toLowerCase();
                if (search && !text.includes(search)) return false;
                if (gender && player.Gender !== gender) return false;
                if (team && player.Team !== team) return false;
                if (conference && getTeamConference(player.Team) !== conference) return false;
                if (player.Games < minGames) return false;
                if ((player.PPG || 0) < minPPG) return false;
                return true;
            }});

            pagination.players.page = 1;
            pagination.players.total = filteredData.players.length;
            renderPlayersTable();
        }}

        function clearFilters(type) {{
            if (type === 'games') {{
                document.getElementById('games-search').value = '';
                document.getElementById('games-gender').value = '';
                document.getElementById('games-date-from').value = '';
                document.getElementById('games-date-to').value = '';
                document.getElementById('games-team').value = '';
                document.getElementById('games-conference').value = '';
                document.getElementById('games-margin').value = '';
                document.getElementById('games-ot').checked = false;
                applyGamesFilters();
            }} else if (type === 'players') {{
                document.getElementById('players-search').value = '';
                document.getElementById('players-gender').value = '';
                document.getElementById('players-team').value = '';
                document.getElementById('players-conference').value = '';
                document.getElementById('players-min-games').value = '';
                document.getElementById('players-min-ppg').value = '';
                applyPlayersFilters();
            }}
        }}

        function getStatClass(value, thresholds) {{
            if (value >= thresholds.excellent) return 'stat-excellent';
            if (value >= thresholds.good) return 'stat-good';
            if (value >= thresholds.average) return 'stat-average';
            return 'stat-poor';
        }}

        function parseDate(dateStr) {{
            // Parse dates like "January 31, 2009" or "12/31/2024"
            if (!dateStr) return null;
            const d = new Date(dateStr);
            if (!isNaN(d.getTime())) return d;
            return null;
        }}

        function sortTable(tableId, colIndex) {{
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const headers = table.querySelectorAll('th');

            const key = tableId + '-' + colIndex;
            const ascending = currentSort[key] !== 'asc';
            currentSort[key] = ascending ? 'asc' : 'desc';

            headers.forEach((h, i) => {{
                h.classList.remove('sorted-asc', 'sorted-desc');
                if (i === colIndex) {{
                    h.classList.add(ascending ? 'sorted-asc' : 'sorted-desc');
                }}
            }});

            // Check if this is a date column by looking at the header
            const headerText = headers[colIndex].textContent.toLowerCase();
            const isDateColumn = headerText.includes('date');

            rows.sort((a, b) => {{
                let aVal = a.cells[colIndex].textContent.trim();
                let bVal = b.cells[colIndex].textContent.trim();

                // Try date parsing first for date columns
                if (isDateColumn) {{
                    const aDate = parseDate(aVal);
                    const bDate = parseDate(bVal);
                    if (aDate && bDate) {{
                        return ascending ? aDate - bDate : bDate - aDate;
                    }}
                }}

                // Try numeric comparison (but not for dates)
                if (!isDateColumn) {{
                    const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                    const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));
                    if (!isNaN(aNum) && !isNaN(bNum)) {{
                        return ascending ? aNum - bNum : bNum - aNum;
                    }}
                }}

                // Fall back to string comparison
                return ascending ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
            }});

            rows.forEach(row => tbody.appendChild(row));
        }}

        function renderPagination(containerId, state, renderFn) {{
            const container = document.getElementById(containerId);
            const totalPages = Math.ceil(state.total / state.pageSize);

            let html = `
                <button onclick="goToPage('${{containerId.replace('-pagination', '')}}', 1)" ${{state.page === 1 ? 'disabled' : ''}}>First</button>
                <button onclick="goToPage('${{containerId.replace('-pagination', '')}}', ${{state.page - 1}})" ${{state.page === 1 ? 'disabled' : ''}}>Prev</button>
                <span class="pagination-info">Page ${{state.page}} of ${{totalPages || 1}} (${{state.total}} items)</span>
                <button onclick="goToPage('${{containerId.replace('-pagination', '')}}', ${{state.page + 1}})" ${{state.page >= totalPages ? 'disabled' : ''}}>Next</button>
                <button onclick="goToPage('${{containerId.replace('-pagination', '')}}', ${{totalPages}})" ${{state.page >= totalPages ? 'disabled' : ''}}>Last</button>
                <select class="page-size-select" onchange="changePageSize('${{containerId.replace('-pagination', '')}}', this.value)">
                    <option value="25" ${{state.pageSize === 25 ? 'selected' : ''}}>25 per page</option>
                    <option value="50" ${{state.pageSize === 50 ? 'selected' : ''}}>50 per page</option>
                    <option value="100" ${{state.pageSize === 100 ? 'selected' : ''}}>100 per page</option>
                    <option value="250" ${{state.pageSize === 250 ? 'selected' : ''}}>250 per page</option>
                    <option value="1000" ${{state.pageSize >= 1000 ? 'selected' : ''}}>Show All</option>
                </select>
            `;
            container.innerHTML = html;
        }}

        function goToPage(type, page) {{
            const state = pagination[type];
            const totalPages = Math.ceil(state.total / state.pageSize);
            state.page = Math.max(1, Math.min(page, totalPages));
            if (type === 'games') renderGamesTable();
            else if (type === 'players') renderPlayersTable();
        }}

        function changePageSize(type, size) {{
            pagination[type].pageSize = parseInt(size);
            pagination[type].page = 1;
            if (type === 'games') renderGamesTable();
            else if (type === 'players') renderPlayersTable();
        }}

        function downloadCSV(type) {{
            let data, filename, headers;

            if (type === 'games') {{
                data = DATA.games || [];
                filename = 'games.csv';
                headers = ['Date', 'Away Team', 'Away Score', 'Home Team', 'Home Score', 'Venue'];
            }} else if (type === 'players') {{
                data = DATA.players || [];
                filename = 'players.csv';
                headers = ['Player', 'Team', 'Games', 'PPG', 'RPG', 'APG', 'FG%', '3P%', 'FT%'];
            }} else if (type === 'teams') {{
                data = DATA.teams || [];
                filename = 'teams.csv';
                headers = ['Team', 'Games', 'Wins', 'Losses', 'Win%', 'PPG', 'PAPG'];
            }} else if (type === 'milestones') {{
                data = currentMilestoneData || [];
                filename = `milestones_${{currentMilestoneType || 'all'}}.csv`;
                headers = ['Date', 'Player', 'Team', 'Opponent', 'Detail'];
            }}

            if (!data.length) {{
                showToast('No data to download');
                return;
            }}

            let csv = headers.join(',') + '\\n';
            data.forEach(row => {{
                const values = headers.map(h => {{
                    const key = h.replace('%', '_pct');
                    let val = row[h] || row[key] || '';
                    if (typeof val === 'string' && val.includes(',')) {{
                        val = `"${{val}}"`;
                    }}
                    return val;
                }});
                csv += values.join(',') + '\\n';
            }});

            const blob = new Blob([csv], {{ type: 'text/csv' }});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
            URL.revokeObjectURL(url);
            showToast(`Downloaded ${{filename}}`);
        }}

        function renderGamesTable() {{
            const tbody = document.querySelector('#games-table tbody');
            const state = pagination.games;
            const data = filteredData.games;
            const start = (state.page - 1) * state.pageSize;
            const end = start + state.pageSize;
            const pageData = data.slice(start, end);

            if (pageData.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><div class="empty-state-icon">&#127936;</div><h3>No games found</h3><p>Try adjusting your filters</p></td></tr>';
            }} else {{
                tbody.innerHTML = pageData.map(game => {{
                    const genderTag = game.Gender === 'W' ? ' <span class="gender-tag">(W)</span>' : '';
                    return `
                    <tr>
                        <td>${{game.Date || ''}} <a href="${{getSportsRefUrl(game)}}" target="_blank" title="View on Sports Reference" class="external-link">&#8599;</a></td>
                        <td><span class="team-link" onclick="filterByTeam('${{game['Away Team'] || ''}}')">${{game['Away Team'] || ''}}</span>${{genderTag}}</td>
                        <td><span class="game-link" onclick="showGameDetail('${{game.GameID || ''}}')">${{game['Away Score'] || 0}}-${{game['Home Score'] || 0}}</span></td>
                        <td><span class="team-link" onclick="filterByTeam('${{game['Home Team'] || ''}}')">${{game['Home Team'] || ''}}</span>${{genderTag}}</td>
                        <td><span class="venue-link" onclick="showVenueDetail('${{game.Venue || ''}}')">${{game.Venue || ''}}</span></td>
                        <td>${{game.City || ''}}</td>
                        <td>${{game.State || ''}}</td>
                        <td>${{game.Notes || ''}}</td>
                    </tr>
                `}}).join('');
            }}

            renderPagination('games-pagination', state);
        }}

        function renderPlayersTable() {{
            const tbody = document.querySelector('#players-table tbody');
            const state = pagination.players;
            const data = filteredData.players;
            const start = (state.page - 1) * state.pageSize;
            const end = start + state.pageSize;
            const pageData = data.slice(start, end);

            if (pageData.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="23" class="empty-state"><div class="empty-state-icon">&#129351;</div><h3>No players found</h3><p>Try adjusting your filters</p></td></tr>';
            }} else {{
                tbody.innerHTML = pageData.map(player => {{
                    const gp = player.Games || 0;
                    const mpg = player.MPG || 0;
                    const ppg = player.PPG || 0;
                    const rpg = player.RPG || 0;
                    const apg = player.APG || 0;
                    const spg = player.SPG || 0;
                    const bpg = player.BPG || 0;
                    const fgm = player.FGM || 0;
                    const fga = player.FGA || 0;
                    const fgPct = player['FG%'] || 0;
                    const tpm = player['3PM'] || 0;
                    const tpa = player['3PA'] || 0;
                    const threePct = player['3P%'] || 0;
                    const ftm = player.FTM || 0;
                    const fta = player.FTA || 0;
                    const ftPct = player['FT%'] || 0;
                    const totalPts = player['Total PTS'] || 0;
                    const totalReb = player['Total REB'] || 0;
                    const totalAst = player['Total AST'] || 0;
                    const totalStl = player['Total STL'] || 0;
                    const totalBlk = player['Total BLK'] || 0;

                    const genderTag = player.Gender === 'W' ? '<span class="gender-tag">(W)</span>' : '';

                    const playerId = player['Player ID'] || '';
                    return `
                        <tr>
                            <td class="sticky-col"><span class="player-link" onclick="showPlayerDetail('${{playerId || player.Player}}')">${{player.Player || ''}}</span>${{playerId ? ` <a href="${{getPlayerSportsRefUrl(playerId)}}" target="_blank" class="external-link" title="View on Sports Reference">&#8599;</a>` : ''}}</td>
                            <td>${{player.Team || ''}} ${{genderTag}}</td>
                            <td>${{gp}}</td>
                            <td>${{mpg.toFixed(1)}}</td>
                            <td class="${{getStatClass(ppg, STAT_THRESHOLDS.ppg)}}">${{ppg.toFixed(1)}}</td>
                            <td class="${{getStatClass(rpg, STAT_THRESHOLDS.rpg)}}">${{rpg.toFixed(1)}}</td>
                            <td class="${{getStatClass(apg, STAT_THRESHOLDS.apg)}}">${{apg.toFixed(1)}}</td>
                            <td>${{spg.toFixed(1)}}</td>
                            <td>${{bpg.toFixed(1)}}</td>
                            <td>${{fgm}}</td>
                            <td>${{fga}}</td>
                            <td class="${{getStatClass(fgPct, STAT_THRESHOLDS.fgPct)}}">${{(fgPct * 100).toFixed(1)}}%</td>
                            <td>${{tpm}}</td>
                            <td>${{tpa}}</td>
                            <td class="${{getStatClass(threePct, STAT_THRESHOLDS.threePct)}}">${{(threePct * 100).toFixed(1)}}%</td>
                            <td>${{ftm}}</td>
                            <td>${{fta}}</td>
                            <td>${{(ftPct * 100).toFixed(1)}}%</td>
                            <td>${{totalPts}}</td>
                            <td>${{totalReb}}</td>
                            <td>${{totalAst}}</td>
                            <td>${{totalStl}}</td>
                            <td>${{totalBlk}}</td>
                        </tr>
                    `;
                }}).join('');
            }}

            renderPagination('players-pagination', state);
        }}

        function populateGamesTable() {{
            filteredData.games = DATA.games || [];
            pagination.games.total = filteredData.games.length;
            renderGamesTable();

            // Populate team filter
            const teams = [...new Set((DATA.games || []).flatMap(g => [g['Away Team'], g['Home Team']]))].filter(t => t).sort();
            const select = document.getElementById('games-team');
            teams.forEach(team => {{
                const option = document.createElement('option');
                option.value = team;
                option.textContent = team;
                select.appendChild(option);
            }});

            // Populate conference filter
            const conferences = [...new Set(teams.map(t => getTeamConference(t)))].filter(c => c).sort();
            const confSelect = document.getElementById('games-conference');
            conferences.forEach(conf => {{
                const option = document.createElement('option');
                option.value = conf;
                option.textContent = conf;
                confSelect.appendChild(option);
            }});

            // Populate head-to-head dropdowns
            const h2h1 = document.getElementById('h2h-team1');
            const h2h2 = document.getElementById('h2h-team2');
            teams.forEach(team => {{
                const opt1 = document.createElement('option');
                opt1.value = team;
                opt1.textContent = team;
                h2h1.appendChild(opt1);
                const opt2 = document.createElement('option');
                opt2.value = team;
                opt2.textContent = team;
                h2h2.appendChild(opt2);
            }});
        }}

        function populatePlayersTable() {{
            filteredData.players = DATA.players || [];
            pagination.players.total = filteredData.players.length;
            renderPlayersTable();

            // Populate team filter
            const teams = [...new Set((DATA.players || []).map(p => p.Team))].filter(t => t).sort();
            const select = document.getElementById('players-team');
            teams.forEach(team => {{
                const option = document.createElement('option');
                option.value = team;
                option.textContent = team;
                select.appendChild(option);
            }});

            // Populate conference filter
            const conferences = [...new Set(teams.map(t => getTeamConference(t)))].filter(c => c).sort();
            const confSelect = document.getElementById('players-conference');
            conferences.forEach(conf => {{
                const option = document.createElement('option');
                option.value = conf;
                option.textContent = conf;
                confSelect.appendChild(option);
            }});

            // Populate comparison dropdowns
            const players = DATA.players || [];
            ['compare-player1', 'compare-player2'].forEach(id => {{
                const sel = document.getElementById(id);
                sel.innerHTML = '<option value="">Select a player...</option>';
                players.forEach(p => {{
                    const option = document.createElement('option');
                    option.value = p['Player ID'] || p.Player;
                    option.textContent = `${{p.Player}} (${{p.Team}})`;
                    sel.appendChild(option);
                }});
            }});

            // Populate game log player search datalist
            const datalist = document.getElementById('gamelog-player-list');
            datalist.innerHTML = '';
            players.forEach(p => {{
                const option = document.createElement('option');
                option.value = `${{p.Player}} (${{p.Team}})`;
                option.dataset.playerId = p['Player ID'] || p.Player;
                datalist.appendChild(option);
            }});
        }}

        function populateSeasonHighs() {{
            const tbody = document.querySelector('#highs-table tbody');
            const data = DATA.seasonHighs || [];

            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><h3>No career highs data</h3></td></tr>';
                return;
            }}

            tbody.innerHTML = data.map(player => {{
                const playerId = player['Player ID'] || '';
                const sportsRefLink = playerId ? ` <a href="${{getPlayerSportsRefUrl(playerId)}}" target="_blank" class="external-link" title="View on Sports Reference">&#8599;</a>` : '';
                return `
                <tr>
                    <td><span class="player-link" onclick="showPlayerDetail('${{playerId || player.Player}}')">${{player.Player || ''}}</span>${{sportsRefLink}}</td>
                    <td>${{player.Team || ''}}</td>
                    <td>${{player['High PTS'] || 0}}</td>
                    <td>${{player['High REB'] || 0}}</td>
                    <td>${{player['High AST'] || 0}}</td>
                    <td>${{player['High 3PM'] || 0}}</td>
                    <td>${{(player['Best Game Score'] || 0).toFixed(1)}}</td>
                </tr>
            `}}).join('');
        }}

        function populateMilestones() {{
            const grid = document.getElementById('milestone-grid');
            const milestones = DATA.milestones || {{}};
            const entries = Object.entries(milestones).filter(([k, v]) => v.length > 0);

            if (entries.length === 0) {{
                grid.innerHTML = '';
                document.getElementById('milestones-empty').style.display = 'block';
                return;
            }}

            document.getElementById('milestones-empty').style.display = 'none';

            grid.innerHTML = entries.map(([key, items]) => `
                <div class="milestone-card" onclick="showMilestoneEntries('${{key}}')" tabindex="0" role="option" aria-selected="false">
                    <div class="count">${{items.length}}</div>
                    <div class="name">${{key.replace(/_/g, ' ').replace(/\\b\\w/g, l => l.toUpperCase())}}</div>
                </div>
            `).join('');

            // Show first milestone by default
            if (entries.length > 0) {{
                showMilestoneEntries(entries[0][0]);
            }}
        }}

        function showMilestoneEntries(key) {{
            const milestones = DATA.milestones || {{}};
            const entries = milestones[key] || [];
            currentMilestoneType = key;
            currentMilestoneData = entries;

            document.querySelectorAll('.milestone-card').forEach(c => {{
                c.classList.remove('active');
                c.setAttribute('aria-selected', 'false');
            }});
            const cards = document.querySelectorAll('.milestone-card');
            cards.forEach(c => {{
                if (c.textContent.toLowerCase().includes(key.replace(/_/g, ' '))) {{
                    c.classList.add('active');
                    c.setAttribute('aria-selected', 'true');
                }}
            }});

            const tbody = document.querySelector('#milestones-table tbody');
            tbody.innerHTML = entries.map(entry => {{
                const playerId = entry['Player ID'] || '';
                const sportsRefLink = playerId ? ` <a href="${{getPlayerSportsRefUrl(playerId)}}" target="_blank" class="external-link" title="View on Sports Reference">&#8599;</a>` : '';
                return `
                <tr>
                    <td>${{entry.Date || ''}}</td>
                    <td><span class="player-link" onclick="showPlayerDetail('${{playerId || entry.Player}}')">${{entry.Player || ''}}</span>${{sportsRefLink}}</td>
                    <td>${{entry.Team || ''}}</td>
                    <td>${{entry.Opponent || ''}}</td>
                    <td>${{entry.Detail || ''}}</td>
                </tr>
            `}}).join('');

            updateURL('milestones', {{ type: key }});
        }}

        function populateTeamsTable() {{
            const tbody = document.querySelector('#teams-table tbody');
            const data = DATA.teams || [];

            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><h3>No team data</h3></td></tr>';
                return;
            }}

            tbody.innerHTML = data.map(team => `
                <tr>
                    <td>${{team.Team || ''}}</td>
                    <td>${{team.Games || 0}}</td>
                    <td>${{team.Wins || 0}}</td>
                    <td>${{team.Losses || 0}}</td>
                    <td>${{((team['Win%'] || 0) * 100).toFixed(1)}}%</td>
                    <td>${{(team.PPG || 0).toFixed(1)}}</td>
                    <td>${{(team.PAPG || 0).toFixed(1)}}</td>
                </tr>
            `).join('');
        }}

        function populateVenuesTable() {{
            const tbody = document.querySelector('#venues-table tbody');
            const data = DATA.venues || [];

            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><h3>No venue data</h3></td></tr>';
                return;
            }}

            tbody.innerHTML = data.map(venue => `
                <tr>
                    <td><span class="venue-link" onclick="showVenueDetail('${{venue.Venue || ''}}')">${{venue.Venue || 'Unknown'}}</span></td>
                    <td>${{venue.City || ''}}</td>
                    <td>${{venue.State || ''}}</td>
                    <td>${{venue.Games || 0}}</td>
                    <td>${{venue['Home Wins'] || 0}}</td>
                    <td>${{venue['Away Wins'] || 0}}</td>
                    <td>${{(venue['Avg Home Pts'] || 0).toFixed(1)}}</td>
                    <td>${{(venue['Avg Away Pts'] || 0).toFixed(1)}}</td>
                </tr>
            `).join('');
        }}

        function populateStreaksTable() {{
            const tbody = document.querySelector('#streaks-table tbody');
            const data = DATA.teamStreaks || [];

            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><h3>No streak data</h3></td></tr>';
                return;
            }}

            tbody.innerHTML = data.map(team => `
                <tr>
                    <td>${{team.Team || ''}}</td>
                    <td>${{team['Current Streak'] || '-'}}</td>
                    <td>${{team['Longest Win Streak'] || 0}}</td>
                    <td>${{team['Longest Loss Streak'] || 0}}</td>
                    <td>${{team['Last 5'] || '-'}}</td>
                    <td>${{team['Last 10'] || '-'}}</td>
                </tr>
            `).join('');
        }}

        function populateSplitsTable() {{
            const tbody = document.querySelector('#splits-table tbody');
            const data = DATA.homeAwaySplits || [];

            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="6" class="empty-state"><h3>No split data</h3></td></tr>';
                return;
            }}

            tbody.innerHTML = data.map(team => `
                <tr>
                    <td>${{team.Team || ''}}</td>
                    <td>${{team['Home W'] || 0}}-${{team['Home L'] || 0}}</td>
                    <td>${{((team['Home Win%'] || 0) * 100).toFixed(1)}}%</td>
                    <td>${{team['Away W'] || 0}}-${{team['Away L'] || 0}}</td>
                    <td>${{((team['Away Win%'] || 0) * 100).toFixed(1)}}%</td>
                    <td>${{team['Neutral W'] || 0}}-${{team['Neutral L'] || 0}}</td>
                </tr>
            `).join('');
        }}

        function populateConferenceTable() {{
            const tbody = document.querySelector('#conference-table tbody');
            const data = DATA.conferenceStandings || [];

            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="5" class="empty-state"><h3>No conference data</h3></td></tr>';
                return;
            }}

            tbody.innerHTML = data.map(team => `
                <tr>
                    <td>${{team.Conference || 'Independent'}}</td>
                    <td>${{team.Team || ''}}</td>
                    <td>${{team['Conf W'] || 0}}-${{team['Conf L'] || 0}}</td>
                    <td>${{((team['Conf Win%'] || 0) * 100).toFixed(1)}}%</td>
                    <td>${{team['Overall W'] || 0}}-${{team['Overall L'] || 0}}</td>
                </tr>
            `).join('');
        }}

        function initChecklist() {{
            const select = document.getElementById('checklist-conference');
            const checklist = DATA.conferenceChecklist || {{}};
            let conferences = Object.keys(checklist).sort();

            // Move special entries to top/bottom
            const specialOrder = ['All D1', 'Historical/Other'];
            conferences = conferences.filter(c => !specialOrder.includes(c));
            if (checklist['All D1']) conferences.unshift('All D1');
            if (checklist['Historical/Other']) conferences.push('Historical/Other');

            conferences.forEach(conf => {{
                const option = document.createElement('option');
                option.value = conf;
                const data = checklist[conf];
                option.textContent = `${{conf}} (${{data.teamsSeen}}/${{data.totalTeams}})`;
                select.appendChild(option);
            }});

            // Auto-select first conference
            if (conferences.length > 0) {{
                select.value = conferences[0];
                populateChecklist();
            }}
        }}

        let currentCalendarMonth = new Date();

        function initCalendar() {{
            try {{
                renderCalendar();
            }} catch (e) {{
                console.error('Error in renderCalendar:', e);
            }}
            try {{
                initMonthlyCalendar();
            }} catch (e) {{
                console.error('Error in initMonthlyCalendar:', e);
            }}
        }}

        function initMonthlyCalendar() {{
            // Find the month with the most recent game
            const games = DATA.games || [];
            if (games.length > 0) {{
                const dates = games.map(g => new Date(g.Date)).filter(d => !isNaN(d));
                if (dates.length > 0) {{
                    const mostRecent = dates.reduce((a, b) => a > b ? a : b);
                    currentCalendarMonth = new Date(mostRecent.getFullYear(), mostRecent.getMonth(), 1);
                }}
            }}
            renderMonthlyCalendar();
        }}

        function changeMonth(delta) {{
            currentCalendarMonth.setMonth(currentCalendarMonth.getMonth() + delta);
            renderMonthlyCalendar();
        }}

        function renderMonthlyCalendar() {{
            const container = document.getElementById('monthly-calendar');
            const label = document.getElementById('calendar-month-label');

            if (!container || !label) {{
                console.warn('Monthly calendar elements not found');
                return;
            }}

            const year = currentCalendarMonth.getFullYear();
            const month = currentCalendarMonth.getMonth();

            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                               'July', 'August', 'September', 'October', 'November', 'December'];
            label.textContent = `${{monthNames[month]}} ${{year}}`;

            // Build a map of games by date string (YYYY-MM-DD)
            const gamesByDate = {{}};
            (DATA.games || []).forEach(g => {{
                const d = new Date(g.Date);
                if (!isNaN(d)) {{
                    const key = `${{d.getFullYear()}}-${{String(d.getMonth() + 1).padStart(2, '0')}}-${{String(d.getDate()).padStart(2, '0')}}`;
                    if (!gamesByDate[key]) gamesByDate[key] = [];
                    gamesByDate[key].push(g);
                }}
            }});

            // Get first day of month and number of days
            const firstDay = new Date(year, month, 1).getDay(); // 0 = Sunday
            const daysInMonth = new Date(year, month + 1, 0).getDate();

            // Build calendar HTML
            let html = `
                <div class="day-header">Sun</div>
                <div class="day-header">Mon</div>
                <div class="day-header">Tue</div>
                <div class="day-header">Wed</div>
                <div class="day-header">Thu</div>
                <div class="day-header">Fri</div>
                <div class="day-header">Sat</div>
            `;

            // Empty cells before first day
            for (let i = 0; i < firstDay; i++) {{
                html += `<div class="day-cell empty"></div>`;
            }}

            // Days of month
            for (let day = 1; day <= daysInMonth; day++) {{
                const dateKey = `${{year}}-${{String(month + 1).padStart(2, '0')}}-${{String(day).padStart(2, '0')}}`;
                const dayGames = gamesByDate[dateKey] || [];
                const hasGames = dayGames.length > 0;

                let gamesHtml = '';
                if (hasGames) {{
                    gamesHtml = dayGames.slice(0, 2).map(g =>
                        `<div class="game-entry">${{g['Away Team']}} @ ${{g['Home Team']}}</div>`
                    ).join('');
                    if (dayGames.length > 2) {{
                        gamesHtml += `<div class="game-entry">+${{dayGames.length - 2}} more</div>`;
                    }}
                }}

                const clickHandler = hasGames ? `onclick="showCalendarDayGames('${{dateKey}}')"` : '';

                html += `
                    <div class="day-cell${{hasGames ? ' has-games' : ''}}" ${{clickHandler}}>
                        <div class="day-number">${{day}}</div>
                        ${{hasGames ? `<div class="day-games">${{gamesHtml}}</div>` : ''}}
                    </div>
                `;
            }}

            container.innerHTML = html;
        }}

        function showCalendarDayGames(dateKey) {{
            // Filter to games on this date and show in a simple alert or modal
            const games = (DATA.games || []).filter(g => {{
                const d = new Date(g.Date);
                if (isNaN(d)) return false;
                const key = `${{d.getFullYear()}}-${{String(d.getMonth() + 1).padStart(2, '0')}}-${{String(d.getDate()).padStart(2, '0')}}`;
                return key === dateKey;
            }});

            if (games.length === 1) {{
                showGameDetail(games[0].GameID);
            }} else if (games.length > 1) {{
                // Show first game, user can navigate from there
                showGameDetail(games[0].GameID);
            }}
        }}

        function initOnThisDay() {{
            renderOnThisDay();
        }}

        function renderOnThisDay() {{
            const today = new Date();
            const currentMonth = today.getMonth() + 1;
            const currentDay = today.getDate();

            const monthNames = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                               'July', 'August', 'September', 'October', 'November', 'December'];
            const dateLabel = document.getElementById('onthisday-date');
            const content = document.getElementById('onthisday-content');
            const emptyState = document.getElementById('onthisday-empty');

            if (!dateLabel || !content || !emptyState) return;

            dateLabel.textContent = `${{monthNames[currentMonth]}} ${{currentDay}}`;

            // Find all games that occurred on this month/day (any year)
            const games = (DATA.games || []).filter(g => {{
                const d = new Date(g.Date);
                if (isNaN(d)) return false;
                return (d.getMonth() + 1) === currentMonth && d.getDate() === currentDay;
            }});

            if (games.length === 0) {{
                content.innerHTML = '';
                emptyState.style.display = 'block';
                return;
            }}

            emptyState.style.display = 'none';

            // Group games by year
            const gamesByYear = {{}};
            games.forEach(g => {{
                const d = new Date(g.Date);
                const year = d.getFullYear();
                if (!gamesByYear[year]) gamesByYear[year] = [];
                gamesByYear[year].push(g);
            }});

            // Sort years descending
            const years = Object.keys(gamesByYear).map(Number).sort((a, b) => b - a);

            let html = '<div class="onthisday-games">';
            years.forEach(year => {{
                const yearGames = gamesByYear[year];
                const yearsAgo = today.getFullYear() - year;
                const yearsAgoText = yearsAgo === 0 ? 'Today' : yearsAgo === 1 ? '1 year ago' : `${{yearsAgo}} years ago`;

                html += `
                    <div class="onthisday-year" style="margin-bottom: 1.5rem;">
                        <h4 style="margin-bottom: 0.75rem; color: var(--text-secondary); border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
                            <span style="font-size: 1.25rem; color: var(--accent-color);">${{year}}</span>
                            <span style="font-size: 0.9rem; margin-left: 0.5rem;">(${{yearsAgoText}})</span>
                        </h4>
                        <div class="onthisday-game-list">
                `;

                yearGames.forEach(g => {{
                    const genderTag = g.Gender === 'M' ? '<span class="gender-seen gender-m">M</span>' :
                                     g.Gender === 'W' ? '<span class="gender-seen gender-w">W</span>' : '';
                    const awayWon = (g['Away Score'] || 0) > (g['Home Score'] || 0);
                    const homeWon = (g['Home Score'] || 0) > (g['Away Score'] || 0);
                    const awayStyle = awayWon ? 'font-weight: bold;' : '';
                    const homeStyle = homeWon ? 'font-weight: bold;' : '';

                    html += `
                        <div class="onthisday-game" style="background: var(--bg-primary); padding: 1rem; border-radius: 8px; margin-bottom: 0.75rem; cursor: pointer;" onclick="showGameDetail('${{g.GameID}}')">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                                <div style="flex: 1; min-width: 200px;">
                                    <span style="${{awayStyle}}">${{g['Away Team']}}</span>
                                    <span style="margin: 0 0.5rem; color: var(--text-muted);">${{g['Away Score'] || 0}}</span>
                                    <span style="color: var(--text-muted);">@</span>
                                    <span style="margin: 0 0.5rem; color: var(--text-muted);">${{g['Home Score'] || 0}}</span>
                                    <span style="${{homeStyle}}">${{g['Home Team']}}</span>
                                    ${{genderTag}}
                                </div>
                                <div style="color: var(--text-secondary); font-size: 0.85rem;">
                                    ${{g.Venue || ''}}${{g.City ? ', ' + g.City : ''}}${{g.State ? ', ' + g.State : ''}}
                                </div>
                            </div>
                        </div>
                    `;
                }});

                html += `
                        </div>
                    </div>
                `;
            }});
            html += '</div>';

            content.innerHTML = html;
        }}

        // School coordinates for map
        const SCHOOL_COORDS = {{
            // ACC
            'Boston College': [42.3355, -71.1685],
            'California': [37.8716, -122.2588],
            'Clemson': [34.6834, -82.8374],
            'Duke': [36.0014, -78.9382],
            'Florida State': [30.4383, -84.3040],
            'Georgia Tech': [33.7756, -84.3963],
            'Louisville': [38.2186, -85.7585],
            'Miami (FL)': [25.7145, -80.2833],
            'NC State': [35.7872, -78.6705],
            'North Carolina': [35.9049, -79.0469],
            'Notre Dame': [41.7052, -86.2352],
            'Pittsburgh': [40.4443, -79.9608],
            'SMU': [32.8412, -96.7852],
            'Stanford': [37.4346, -122.1609],
            'Syracuse': [43.0481, -76.1474],
            'Virginia': [38.0336, -78.5080],
            'Virginia Tech': [37.2296, -80.4139],
            'Wake Forest': [36.1338, -80.2820],
            // Big Ten
            'Illinois': [40.1020, -88.2272],
            'Indiana': [39.1682, -86.5231],
            'Iowa': [41.6611, -91.5499],
            'Maryland': [38.9897, -76.9378],
            'Michigan': [42.2808, -83.7430],
            'Michigan State': [42.7284, -84.4822],
            'Minnesota': [44.9740, -93.2277],
            'Nebraska': [40.8202, -96.7005],
            'Northwestern': [42.0565, -87.6753],
            'Ohio State': [40.0076, -83.0251],
            'Oregon': [44.0448, -123.0726],
            'Penn State': [40.8148, -77.8563],
            'Purdue': [40.4259, -86.9081],
            'Rutgers': [40.5008, -74.4474],
            'UCLA': [34.0689, -118.4452],
            'USC': [34.0224, -118.2851],
            'Washington': [47.6553, -122.3035],
            'Wisconsin': [43.0731, -89.4012],
            // SEC
            'Alabama': [33.2098, -87.5692],
            'Arkansas': [36.0679, -94.1737],
            'Auburn': [32.6026, -85.4808],
            'Florida': [29.6499, -82.3486],
            'Georgia': [33.9480, -83.3773],
            'Kentucky': [38.0406, -84.5037],
            'LSU': [30.4133, -91.1838],
            'Mississippi State': [33.4504, -88.7934],
            'Missouri': [38.9517, -92.3341],
            'Oklahoma': [35.2226, -97.4395],
            'Ole Miss': [34.3647, -89.5387],
            'South Carolina': [33.9940, -81.0254],
            'Tennessee': [35.9544, -83.9295],
            'Texas': [30.2849, -97.7341],
            'Texas A&M': [30.6043, -96.3711],
            'Vanderbilt': [36.1447, -86.8027],
            // Big 12
            'Arizona': [32.2319, -110.9501],
            'Arizona State': [33.4255, -111.9400],
            'Baylor': [31.5586, -97.1164],
            'BYU': [40.2338, -111.6585],
            'Cincinnati': [39.1329, -84.5150],
            'Colorado': [40.0076, -105.2659],
            'Houston': [29.7199, -95.3422],
            'Iowa State': [42.0140, -93.6357],
            'Kansas': [38.9543, -95.2558],
            'Kansas State': [39.1836, -96.5717],
            'Oklahoma State': [36.1156, -97.0584],
            'TCU': [32.7098, -97.3633],
            'Texas Tech': [33.5906, -101.8749],
            'UCF': [28.6024, -81.2001],
            'Utah': [40.7649, -111.8421],
            'West Virginia': [39.6480, -79.9544],
            // Big East
            'Butler': [39.8407, -86.1694],
            'UConn': [41.8084, -72.2495],
            'Creighton': [41.2627, -95.9378],
            'DePaul': [41.9253, -87.6569],
            'Georgetown': [38.9076, -77.0723],
            'Marquette': [43.0389, -87.9295],
            'Providence': [41.8403, -71.4354],
            'Seton Hall': [40.7424, -74.2433],
            "St. John's": [40.7228, -73.7949],
            'Villanova': [40.0346, -75.3378],
            'Xavier': [39.1494, -84.4734],
            // WCC
            'Gonzaga': [47.6671, -117.4017],
            'Loyola Marymount': [33.9700, -118.4175],
            'Oregon State': [44.5646, -123.2750],
            'Pacific': [37.9818, -121.3108],
            'Pepperdine': [34.0400, -118.7098],
            'Portland': [45.5646, -122.7225],
            "Saint Mary's (CA)": [37.8402, -122.1118],
            'San Diego': [32.7710, -117.1878],
            'San Francisco': [37.7765, -122.4506],
            'Santa Clara': [37.3496, -121.9390],
            'Seattle': [47.6062, -122.3321],
            'Washington State': [46.7324, -117.1631],
            // American (AAC)
            'Charlotte': [35.3074, -80.7330],
            'East Carolina': [35.6066, -77.3664],
            'Florida Atlantic': [26.3683, -80.1018],
            'Memphis': [35.1174, -89.9711],
            'North Texas': [33.2148, -97.1331],
            'Rice': [29.7174, -95.4018],
            'South Florida': [28.0587, -82.4139],
            'Temple': [39.9812, -75.1495],
            'Tulane': [29.9340, -90.1185],
            'Tulsa': [36.1512, -95.9446],
            'UAB': [33.5021, -86.7993],
            'UTSA': [29.5830, -98.6197],
            'Wichita State': [37.7200, -97.2957],
            // Mountain West
            'Air Force': [39.0068, -104.8836],
            'Boise State': [43.6034, -116.2024],
            'Colorado State': [40.5734, -105.0865],
            'Fresno State': [36.8116, -119.7485],
            'Grand Canyon': [33.5097, -112.1257],
            'Nevada': [39.5497, -119.8143],
            'New Mexico': [35.0853, -106.6056],
            'San Diego State': [32.7761, -117.0701],
            'San Jose State': [37.3352, -121.8811],
            'UNLV': [36.1085, -115.1397],
            'Utah State': [41.7520, -111.8126],
            'Wyoming': [41.3149, -105.5666],
            // Ivy League
            'Brown': [41.8268, -71.4025],
            'Columbia': [40.8075, -73.9626],
            'Cornell': [42.4534, -76.4735],
            'Dartmouth': [43.7044, -72.2887],
            'Harvard': [42.3770, -71.1167],
            'Penn': [39.9522, -75.1932],
            'Princeton': [40.3440, -74.6514],
            'Yale': [41.3111, -72.9267],
            // Atlantic 10
            'Dayton': [39.7405, -84.1796],
            'Davidson': [35.5016, -80.8428],
            'Duquesne': [40.4365, -79.9878],
            'Fordham': [40.8612, -73.8865],
            'George Mason': [38.8298, -77.3074],
            'George Washington': [38.9007, -77.0508],
            'La Salle': [40.0379, -75.1551],
            'Loyola Chicago': [41.9998, -87.6579],
            'Rhode Island': [41.4806, -71.5276],
            'Richmond': [37.5740, -77.5400],
            "Saint Joseph's": [40.0313, -75.2348],
            'Saint Louis': [38.6361, -90.2340],
            'St. Bonaventure': [42.0778, -78.4756],
            'VCU': [37.5495, -77.4508],
            // MVC
            'Belmont': [36.1330, -86.7967],
            'Bradley': [40.6984, -89.6177],
            'Drake': [41.6005, -93.6527],
            'Evansville': [37.9748, -87.5006],
            'Illinois State': [40.5142, -88.9906],
            'Indiana State': [39.4653, -87.4056],
            'Murray State': [36.6127, -88.3151],
            'Northern Iowa': [42.5142, -92.4631],
            'Southern Illinois': [37.7145, -89.2173],
            'UIC': [41.8719, -87.6484],
            'Valparaiso': [41.4531, -87.0360],
            // CAA
            'Campbell': [35.4174, -78.8553],
            'Charleston': [32.7833, -79.9370],
            'Drexel': [39.9566, -75.1899],
            'Elon': [36.1054, -79.5022],
            'Hampton': [37.0231, -76.3346],
            'Hofstra': [40.7154, -73.6004],
            'Monmouth': [40.2774, -74.0046],
            'UNCW': [34.2257, -77.8723],
            'Northeastern': [42.3398, -71.0892],
            'North Carolina A&T': [36.0726, -79.7777],
            'Stony Brook': [40.9176, -73.1233],
            'Towson': [39.3943, -76.6097],
            'William & Mary': [37.2707, -76.7075],
            // Patriot League
            'American': [38.9365, -77.0878],
            'Army': [41.3915, -73.9653],
            'Boston University': [42.3505, -71.1054],
            'Bucknell': [40.9553, -76.8847],
            'Colgate': [42.8185, -75.5399],
            'Holy Cross': [42.2373, -71.8078],
            'Lafayette': [40.6977, -75.2109],
            'Lehigh': [40.6084, -75.3781],
            'Loyola (MD)': [39.3482, -76.6256],
            'Navy': [38.9847, -76.4888],
            // WAC
            'Abilene Christian': [32.4601, -99.7778],
            'California Baptist': [33.9295, -117.4260],
            'Southern Utah': [37.6772, -113.0619],
            'Tarleton State': [32.2235, -98.2175],
            'Utah Tech': [37.1041, -113.5841],
            'Utah Valley': [40.2789, -111.7144],
            'UT Arlington': [32.7299, -97.1133],
            // Big Sky
            'Eastern Washington': [47.4886, -117.5826],
            'Idaho': [46.7324, -117.0002],
            'Idaho State': [42.8621, -112.4278],
            'Montana': [46.8625, -113.9847],
            'Montana State': [45.6670, -111.0429],
            'Northern Arizona': [35.1894, -111.6514],
            'Northern Colorado': [40.4053, -104.6975],
            'Portland State': [45.5118, -122.6842],
            'Sacramento State': [38.5618, -121.4240],
            'Weber State': [41.1928, -111.9348],
            // Horizon League
            'Cleveland State': [41.5025, -81.6736],
            'Detroit Mercy': [42.3528, -83.0657],
            'Green Bay': [44.5333, -87.9096],
            'IU Indianapolis': [39.7745, -86.1758],
            'Milwaukee': [43.0766, -87.8815],
            'Northern Kentucky': [39.0284, -84.4631],
            'Oakland': [42.6679, -83.2184],
            'Purdue Fort Wayne': [41.1176, -85.1090],
            'Robert Morris': [40.5186, -80.1839],
            'Wright State': [39.7817, -84.0620],
            'Youngstown State': [41.1067, -80.6495],
            // ASUN
            'Austin Peay': [36.5366, -87.3461],
            'Bellarmine': [38.2072, -85.6821],
            'Central Arkansas': [35.0764, -92.4592],
            'Eastern Kentucky': [37.7378, -84.2942],
            'Florida Gulf Coast': [26.4615, -81.7729],
            'Jacksonville': [30.3505, -81.6050],
            'Lipscomb': [36.1194, -86.8007],
            'North Alabama': [34.8059, -87.6771],
            'North Florida': [30.2722, -81.5103],
            'Queens': [35.1872, -80.8326],
            'Stetson': [29.0411, -81.3039],
            'West Georgia': [33.5834, -85.0867],
            // NEC
            'Central Connecticut': [41.5658, -72.7823],
            'Chicago State': [41.7186, -87.6094],
            'Fairleigh Dickinson': [40.8554, -74.2293],
            'Le Moyne': [43.0300, -76.0700],
            'LIU': [40.6891, -73.9866],
            'Mercyhurst': [42.0987, -80.0923],
            'Merrimack': [42.7110, -71.1897],
            'New Haven': [41.2903, -72.9510],
            'Sacred Heart': [41.2059, -73.2207],
            'St. Francis (PA)': [40.4583, -78.5505],
            'Stonehill': [42.1062, -71.1073],
            'Wagner': [40.6162, -74.0936],
            // MAAC
            'Canisius': [42.9383, -78.8442],
            'Fairfield': [41.2054, -73.2413],
            'Iona': [40.9235, -73.8270],
            'Manhattan': [40.8905, -73.8991],
            'Marist': [41.7262, -73.9330],
            "Mount St. Mary's": [39.6936, -77.4364],
            'Niagara': [43.1400, -79.0400],
            'Quinnipiac': [41.4193, -72.8932],
            'Rider': [40.2855, -74.7470],
            "Saint Peter's": [40.7420, -74.0545],
            'Siena': [42.7189, -73.7530],
            // MEAC
            'Coppin State': [39.3409, -76.6654],
            'Delaware State': [39.1896, -75.5422],
            'Howard': [38.9224, -77.0197],
            'Maryland-Eastern Shore': [38.2091, -75.8333],
            'Morgan State': [39.3434, -76.5824],
            'Norfolk State': [36.8474, -76.2672],
            'North Carolina Central': [35.9746, -78.8986],
            'South Carolina State': [33.4934, -80.8544],
            // SWAC
            'Alabama A&M': [34.7831, -86.5686],
            'Alabama State': [32.3643, -86.2956],
            'Alcorn State': [31.8766, -91.1349],
            'Arkansas-Pine Bluff': [34.2284, -92.0032],
            'Bethune-Cookman': [29.2108, -81.0228],
            'Florida A&M': [30.4278, -84.2878],
            'Grambling State': [32.5244, -92.7147],
            'Jackson State': [32.2979, -90.2094],
            'Mississippi Valley State': [33.4897, -90.3073],
            'Prairie View A&M': [30.0943, -95.9898],
            'Southern': [30.5184, -91.1904],
            'Texas Southern': [29.7238, -95.3573],
            // Southland
            'East Texas A&M': [33.2348, -95.9153],
            'Houston Christian': [29.7319, -95.5850],
            'Incarnate Word': [29.4632, -98.4669],
            'Lamar': [30.0580, -94.0657],
            'McNeese': [30.2097, -93.2108],
            'New Orleans': [30.0277, -90.0674],
            'Nicholls': [29.7949, -90.8106],
            'Northwestern State': [31.7497, -93.1035],
            'Southeastern Louisiana': [30.5180, -90.4631],
            'Stephen F. Austin': [31.6250, -94.6437],
            'Texas A&M-Corpus Christi': [27.7130, -97.3256],
            'UTRGV': [26.3038, -98.1784],
            // OVC
            'Eastern Illinois': [39.4780, -88.1759],
            'Little Rock': [34.7257, -92.3421],
            'Lindenwood': [38.6887, -90.3847],
            'Morehead State': [38.1856, -83.4341],
            'SIU Edwardsville': [38.7945, -89.9975],
            'Southeast Missouri State': [37.3091, -89.5503],
            'Southern Indiana': [38.0138, -87.5763],
            'Tennessee State': [36.1681, -86.8326],
            'Tennessee Tech': [36.1720, -85.5088],
            'UT Martin': [36.3450, -88.8528],
            'Western Illinois': [40.4735, -90.6801],
            // Big West
            'Cal Poly': [35.3050, -120.6625],
            'Cal State Bakersfield': [35.3506, -119.1038],
            'Cal State Fullerton': [33.8829, -117.8869],
            'Cal State Northridge': [34.2400, -118.5291],
            'Hawaii': [21.2969, -157.8171],
            'Long Beach State': [33.7838, -118.1141],
            'UC Davis': [38.5382, -121.7617],
            'UC Irvine': [33.6405, -117.8443],
            'UC Riverside': [33.9737, -117.3281],
            'UC San Diego': [32.8801, -117.2340],
            'UC Santa Barbara': [34.4133, -119.8610],
            // Summit League
            'Denver': [39.6774, -104.9619],
            'Kansas City': [39.0997, -94.5786],
            'North Dakota': [47.9253, -97.0329],
            'North Dakota State': [46.8958, -96.8003],
            'Omaha': [41.2565, -96.0135],
            'Oral Roberts': [36.0550, -95.9389],
            'South Dakota': [42.7896, -96.9267],
            'South Dakota State': [44.3114, -96.7984],
            'St. Thomas': [44.9467, -93.1892],
            // Southern Conference
            'Chattanooga': [35.0456, -85.3097],
            'East Tennessee State': [36.3081, -82.3645],
            'Furman': [34.9270, -82.4391],
            'Mercer': [32.8308, -83.6500],
            'Samford': [33.4644, -86.7929],
            'The Citadel': [32.7967, -79.9581],
            'UNC Greensboro': [36.0687, -79.8100],
            'VMI': [37.7910, -79.4420],
            'Western Carolina': [35.3073, -83.1857],
            'Wofford': [34.9507, -81.9320],
            // America East
            'Albany': [42.6867, -73.8232],
            'Binghamton': [42.0873, -75.9693],
            'Bryant': [41.8465, -71.4548],
            'Maine': [44.9010, -68.6731],
            'New Hampshire': [43.1339, -70.9264],
            'NJIT': [40.7424, -74.1790],
            'UMass Lowell': [42.6526, -71.3247],
            'UMBC': [39.2554, -76.7107],
            'Vermont': [44.4759, -73.1983],
            // Conference USA
            'Delaware': [39.6837, -75.7497],
            'FIU': [25.7578, -80.3733],
            'Jacksonville State': [33.8200, -85.7653],
            'Kennesaw State': [34.0234, -84.5819],
            'Liberty': [37.3519, -79.1731],
            'Louisiana Tech': [32.5270, -92.6477],
            'Middle Tennessee': [35.8487, -86.3680],
            'Missouri State': [37.2089, -93.2923],
            'New Mexico State': [32.2830, -106.7473],
            'Sam Houston': [30.7149, -95.5508],
            'UTEP': [31.7706, -106.5069],
            'Western Kentucky': [36.9833, -86.4500],
            // MAC
            'Akron': [41.0733, -81.5068],
            'Ball State': [40.2060, -85.4097],
            'Bowling Green': [41.3763, -83.6275],
            'Buffalo': [42.9984, -78.7911],
            'Central Michigan': [43.5917, -84.7688],
            'Eastern Michigan': [42.2486, -83.6238],
            'Kent State': [41.1461, -81.3420],
            'Miami (OH)': [39.5089, -84.7340],
            'Northern Illinois': [41.9360, -88.7633],
            'Ohio': [39.3203, -82.0997],
            'Toledo': [41.6528, -83.6127],
            'UMass': [42.3868, -72.5301],
            'Western Michigan': [42.2848, -85.6152],
            // Sun Belt
            'Appalachian State': [36.2152, -81.6746],
            'Arkansas State': [35.8423, -90.6792],
            'Coastal Carolina': [33.7959, -79.0103],
            'Georgia Southern': [32.4219, -81.7832],
            'Georgia State': [33.7530, -84.3853],
            'James Madison': [38.4362, -78.8675],
            'Louisiana': [30.2140, -92.0192],
            'Louisiana-Monroe': [32.5293, -92.0755],
            'Marshall': [38.4238, -82.4238],
            'Old Dominion': [36.8865, -76.3059],
            'South Alabama': [30.6965, -88.1780],
            'Southern Miss': [31.3271, -89.3350],
            'Texas State': [29.8884, -97.9384],
            'Troy': [31.7988, -85.9636],
            // Big South
            'Charleston Southern': [32.9804, -80.0634],
            'Gardner-Webb': [35.2284, -81.5856],
            'High Point': [35.9735, -79.9928],
            'Longwood': [37.2968, -78.3961],
            'Presbyterian': [34.5035, -81.8593],
            'Radford': [37.1318, -80.5540],
            'UNC Asheville': [35.6138, -82.5675],
            'USC Upstate': [34.9254, -81.9826],
            'Winthrop': [34.9418, -81.0331],
        }};

        let schoolMap = null;
        let mapMarkers = [];

        function initMap() {{
            // Initialize the map centered on continental US
            schoolMap = L.map('school-map').setView([39.5, -98.35], 4);

            // Add OpenStreetMap tiles
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 18,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            }}).addTo(schoolMap);

            // Populate conference dropdown
            const confSelect = document.getElementById('map-conference');
            const checklist = DATA.conferenceChecklist || {{}};
            const confNames = Object.keys(checklist).sort((a, b) => {{
                if (a === 'All D1') return -1;
                if (b === 'All D1') return 1;
                return a.localeCompare(b);
            }});
            confNames.forEach(conf => {{
                if (conf !== 'Historical/Other') {{
                    const opt = document.createElement('option');
                    opt.value = conf;
                    opt.textContent = conf;
                    confSelect.appendChild(opt);
                }}
            }});

            updateMapMarkers();
        }}

        function updateMapMarkers() {{
            // Clear existing markers
            mapMarkers.forEach(m => schoolMap.removeLayer(m));
            mapMarkers = [];

            const confName = document.getElementById('map-conference').value;
            const filter = document.getElementById('map-filter').value;
            const checklist = DATA.conferenceChecklist || {{}};

            if (!checklist[confName]) return;

            const teams = checklist[confName].teams || [];

            teams.forEach(team => {{
                const coords = SCHOOL_COORDS[team.team];
                if (!coords) return;

                // Determine status
                const visited = team.arenaVisited;
                const seen = team.seen;

                // Apply filter
                if (filter === 'visited' && !visited) return;
                if (filter === 'seen' && !seen) return;
                if (filter === 'unseen' && seen) return;

                // Determine marker color
                let color;
                if (visited) {{
                    color = '#2E7D32';  // Green - visited home arena
                }} else if (seen) {{
                    color = '#1976D2';  // Blue - seen but not at home
                }} else {{
                    color = '#9E9E9E';  // Gray - not seen
                }}

                // Create custom icon
                const icon = L.divIcon({{
                    className: 'custom-marker',
                    html: `<div style="
                        background: ${{color}};
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        border: 2px solid white;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    "></div>`,
                    iconSize: [16, 16],
                    iconAnchor: [8, 8],
                }});

                const marker = L.marker(coords, {{ icon }}).addTo(schoolMap);

                // Add popup
                const statusText = visited ? 'Visited' : (seen ? 'Seen (Away)' : 'Not Seen');
                const arena = team.homeArena || 'Unknown';
                marker.bindPopup(`
                    <strong>${{team.team}}</strong><br>
                    ${{team.conference ? team.conference + '<br>' : ''}}
                    <em>${{arena}}</em><br>
                    <span style="color: ${{color}}; font-weight: bold;">${{statusText}}</span>
                `);

                mapMarkers.push(marker);
            }});

            // Fit bounds if there are markers
            if (mapMarkers.length > 0) {{
                const group = L.featureGroup(mapMarkers);
                schoolMap.fitBounds(group.getBounds().pad(0.1));
            }}
        }}

        function renderCalendar() {{
            const games = DATA.games || [];
            const grid = document.getElementById('calendar-grid');

            if (!grid) {{
                console.warn('calendar-grid element not found');
                return;
            }}

            // Group games by month-day (year agnostic)
            const gamesByMonthDay = {{}};
            let earliestMonthDay = null;  // Format: MM-DD
            let latestMonthDay = null;

            games.forEach(g => {{
                const date = new Date(g.Date);
                if (isNaN(date.getTime())) return;
                const month = date.getMonth();  // 0-11
                const day = date.getDate();
                const monthDay = `${{String(month + 1).padStart(2, '0')}}-${{String(day).padStart(2, '0')}}`;

                if (!gamesByMonthDay[monthDay]) gamesByMonthDay[monthDay] = [];
                gamesByMonthDay[monthDay].push(g);

                // Track earliest and latest in season order (Nov=11 comes before Jan=1)
                // Convert to season order: Nov(11)=1, Dec(12)=2, Jan(1)=3, ..., Oct(10)=12
                const seasonOrder = month >= 10 ? month - 9 : month + 3;
                const seasonKey = seasonOrder * 100 + day;

                if (earliestMonthDay === null || seasonKey < earliestMonthDay.key) {{
                    earliestMonthDay = {{ monthDay, month, day, key: seasonKey }};
                }}
                if (latestMonthDay === null || seasonKey > latestMonthDay.key) {{
                    latestMonthDay = {{ monthDay, month, day, key: seasonKey }};
                }}
            }});

            if (!earliestMonthDay || !latestMonthDay) {{
                grid.innerHTML = '<p>No games found.</p>';
                return;
            }}

            // Build season months array (from earliest to latest)
            const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                               'July', 'August', 'September', 'October', 'November', 'December'];
            const dayNames = ['S', 'M', 'T', 'W', 'T', 'F', 'S'];

            // Season typically runs Nov -> April, so order months accordingly
            const seasonMonthOrder = [10, 11, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9];  // Nov, Dec, Jan, Feb, Mar, Apr, ...

            // Find which months to display based on earliest/latest
            const startSeasonIdx = seasonMonthOrder.indexOf(earliestMonthDay.month);
            const endSeasonIdx = seasonMonthOrder.indexOf(latestMonthDay.month);
            const monthsToShow = [];
            for (let i = startSeasonIdx; i <= endSeasonIdx; i++) {{
                monthsToShow.push(seasonMonthOrder[i]);
            }}

            // Count total days and days with games for progress
            let totalDays = 0;
            let daysWithGames = 0;
            monthsToShow.forEach(month => {{
                const daysInMonth = new Date(2024, month + 1, 0).getDate();  // Use leap year
                const startDay = (month === earliestMonthDay.month) ? earliestMonthDay.day : 1;
                const endDay = (month === latestMonthDay.month) ? latestMonthDay.day : daysInMonth;
                for (let d = startDay; d <= endDay; d++) {{
                    totalDays++;
                    const monthDay = `${{String(month + 1).padStart(2, '0')}}-${{String(d).padStart(2, '0')}}`;
                    if (gamesByMonthDay[monthDay]) daysWithGames++;
                }}
            }});

            let html = `<div class="calendar-progress">
                <div class="progress-text"><strong>${{daysWithGames}}</strong> of <strong>${{totalDays}}</strong> days (${{(daysWithGames/totalDays*100).toFixed(1)}}%)</div>
                <div class="progress-bar"><div class="progress-fill" style="width: ${{(daysWithGames/totalDays*100)}}%"></div></div>
            </div>`;

            html += '<div class="calendar-months">';

            monthsToShow.forEach(month => {{
                const daysInMonth = new Date(2024, month + 1, 0).getDate();  // Use leap year for Feb
                const firstDayOfWeek = new Date(2024, month, 1).getDay();

                // Determine start/end days for this month
                const startDay = (month === earliestMonthDay.month) ? earliestMonthDay.day : 1;
                const endDay = (month === latestMonthDay.month) ? latestMonthDay.day : daysInMonth;

                html += `<div class="calendar-month"><h4>${{monthNames[month]}}</h4><div class="calendar-days">`;

                // Day headers
                dayNames.forEach(d => {{
                    html += `<div class="calendar-day-header">${{d}}</div>`;
                }});

                // Empty cells for days before the 1st
                for (let i = 0; i < firstDayOfWeek; i++) {{
                    html += `<div class="calendar-day empty"></div>`;
                }}

                // Days of the month
                for (let day = 1; day <= daysInMonth; day++) {{
                    const monthDay = `${{String(month + 1).padStart(2, '0')}}-${{String(day).padStart(2, '0')}}`;
                    const dayGames = gamesByMonthDay[monthDay] || [];
                    const hasGame = dayGames.length > 0;
                    const isInRange = day >= startDay && day <= endDay;

                    if (!isInRange) {{
                        html += `<div class="calendar-day out-of-range">${{day}}</div>`;
                    }} else if (hasGame) {{
                        const years = [...new Set(dayGames.map(g => new Date(g.Date).getFullYear()))].sort();
                        const tooltip = dayGames.map(g => `${{new Date(g.Date).getFullYear()}}: ${{g['Away Team']}} @ ${{g['Home Team']}}`).join('\\n');
                        html += `<div class="calendar-day has-game${{dayGames.length > 1 ? ' has-multiple' : ''}}"
                                    onclick="showCalendarDayGames('${{monthDay}}')"
                                    title="${{tooltip}}">${{day}}</div>`;
                    }} else {{
                        html += `<div class="calendar-day">${{day}}</div>`;
                    }}
                }}

                html += `</div></div>`;
            }});

            html += '</div>';
            grid.innerHTML = html;
        }}

        function showCalendarDayGames(monthDay) {{
            // Find all games on this month-day (any year)
            const [month, day] = monthDay.split('-').map(Number);
            const games = DATA.games.filter(g => {{
                const date = new Date(g.Date);
                return date.getMonth() === month - 1 && date.getDate() === day;
            }});

            if (games.length === 1) {{
                showGameDetail(games[0].GameID);
            }} else if (games.length > 1) {{
                // Show toast with game count and years
                const years = [...new Set(games.map(g => new Date(g.Date).getFullYear()))].sort().join(', ');
                showToast(`${{games.length}} games on this date (${{years}})`);
            }}
        }}

        function populateChecklist() {{
            const confName = document.getElementById('checklist-conference').value;
            const gender = document.getElementById('checklist-gender').value;
            const teamFilter = document.getElementById('checklist-team-filter').value;
            const venueFilter = document.getElementById('checklist-venue-filter').value;
            const container = document.getElementById('checklist-content');
            const checklist = DATA.conferenceChecklist || {{}};

            if (!confName || !checklist[confName]) {{
                container.innerHTML = '<p>Select a conference to view the checklist.</p>';
                return;
            }}

            const conf = checklist[confName];
            const teams = conf.teams || [];

            // Get gender-specific counts
            let teamsSeen, venuesVisited;
            if (gender === 'M') {{
                teamsSeen = conf.teamsSeenM || 0;
                venuesVisited = conf.venuesVisitedM || 0;
            }} else if (gender === 'W') {{
                teamsSeen = conf.teamsSeenW || 0;
                venuesVisited = conf.venuesVisitedW || 0;
            }} else {{
                teamsSeen = conf.teamsSeen || 0;
                venuesVisited = conf.venuesVisited || 0;
            }}

            const summaryHtml = `
                <div class="checklist-summary">
                    <div class="checklist-stat">
                        <div class="checklist-stat-value">${{teamsSeen}}/${{conf.totalTeams || 0}}</div>
                        <div class="checklist-stat-label">Teams Seen</div>
                    </div>
                    <div class="checklist-stat">
                        <div class="checklist-stat-value">${{venuesVisited}}/${{conf.totalVenues || 0}}</div>
                        <div class="checklist-stat-label">Home Venues Visited</div>
                    </div>
                </div>
            `;

            const showConference = confName === 'All D1' || confName === 'Historical/Other';

            // Filter teams based on selection
            const filteredTeams = teams.filter(t => {{
                let seen, arenaVisited;
                if (gender === 'M') {{
                    seen = t.seenM;
                    arenaVisited = t.arenaVisitedM;
                }} else if (gender === 'W') {{
                    seen = t.seenW;
                    arenaVisited = t.arenaVisitedW;
                }} else {{
                    seen = t.seen;
                    arenaVisited = t.arenaVisited;
                }}

                // Apply team filter
                if (teamFilter === 'seen' && !seen) return false;
                if (teamFilter === 'unseen' && seen) return false;

                // Apply venue filter
                if (venueFilter === 'visited' && !arenaVisited) return false;
                if (venueFilter === 'unvisited' && arenaVisited) return false;

                return true;
            }});

            const teamsHtml = filteredTeams.map(t => {{
                // Get gender-specific values
                let seen, arenaVisited, homeArena;
                if (gender === 'M') {{
                    seen = t.seenM;
                    arenaVisited = t.arenaVisitedM;
                    homeArena = t.homeArenaM || t.homeArena;
                }} else if (gender === 'W') {{
                    seen = t.seenW;
                    arenaVisited = t.arenaVisitedW;
                    homeArena = t.homeArenaW || t.homeArena;
                }} else {{
                    seen = t.seen;
                    arenaVisited = t.arenaVisited;
                    homeArena = t.homeArena;
                }}

                // Build gender indicators for "All" view (gender === '' means All)
                let genderIndicators = '';
                if (gender === '' && (t.seenM || t.seenW)) {{
                    const parts = [];
                    if (t.seenM) parts.push('<span class="gender-seen gender-m">M</span>');
                    if (t.seenW) parts.push('<span class="gender-seen gender-w">W</span>');
                    genderIndicators = parts.join('');
                }}

                // Arena indicator for "All" view
                let arenaIndicators = '';
                if (gender === '' && (t.arenaVisitedM || t.arenaVisitedW)) {{
                    if (t.arenaVisitedM && t.arenaVisitedW) {{
                        arenaIndicators = '✓ ';  // Both visited
                    }} else if (t.arenaVisitedM) {{
                        arenaIndicators = '<span class="gender-seen gender-m">M</span> ';
                    }} else if (t.arenaVisitedW) {{
                        arenaIndicators = '<span class="gender-seen gender-w">W</span> ';
                    }}
                }} else if (arenaVisited) {{
                    arenaIndicators = '✓ ';
                }}

                return `
                    <div class="checklist-item ${{seen ? 'seen' : ''}}">
                        <div class="check-icon ${{seen ? 'checked' : 'unchecked'}}">
                            ${{seen ? '✓' : ''}}
                        </div>
                        <div class="checklist-details">
                            <div class="checklist-team">${{t.team}}${{genderIndicators ? ' ' + genderIndicators : ''}}${{showConference && t.conference ? ` <span class="checklist-conf">(${{t.conference}})</span>` : ''}}</div>
                            <div class="checklist-venue ${{arenaVisited ? 'visited' : ''}}">
                                ${{arenaIndicators}}${{homeArena}}
                            </div>
                        </div>
                    </div>
                `;
            }}).join('');

            const filterNote = filteredTeams.length !== teams.length ?
                `<p style="color: var(--text-secondary); margin-bottom: 0.5rem;">Showing ${{filteredTeams.length}} of ${{teams.length}} teams</p>` : '';

            container.innerHTML = summaryHtml + filterNote + '<div class="checklist-grid">' + teamsHtml + '</div>';
        }}

        function showPlayerDetail(playerId) {{
            const player = DATA.players.find(p => (p['Player ID'] || p.Player) === playerId);
            if (!player) {{
                showToast('Player not found');
                return;
            }}

            const games = (DATA.playerGames || []).filter(g => (g.player_id || g.player) === playerId)
                .sort((a, b) => (b.date_yyyymmdd || b.date || '').localeCompare(a.date_yyyymmdd || a.date || ''));

            let gamesHtml = games.map(g => `
                <tr class="clickable-row" onclick="closeModal('player-modal'); showGameDetail('${{g.game_id}}')">
                    <td><span class="game-link">${{g.date}}</span></td>
                    <td>${{g.opponent}}</td>
                    <td>${{g.result}} ${{g.score || ''}}</td>
                    <td>${{g.minutes || 0}}</td>
                    <td>${{g.pts || 0}}</td>
                    <td>${{g.trb || 0}}</td>
                    <td>${{g.ast || 0}}</td>
                    <td>${{g.stl || 0}}</td>
                    <td>${{g.blk || 0}}</td>
                    <td>${{g.fg || 0}}-${{g.fga || 0}}</td>
                    <td>${{g.fg3 || 0}}-${{g.fg3a || 0}}</td>
                    <td>${{g.ft || 0}}-${{g.fta || 0}}</td>
                </tr>
            `).join('');

            const genderTag = player.Gender === 'W' ? '<span class="gender-tag">(W)</span>' : '';
            const playerIdForUrl = player['Player ID'] || '';
            const sportsRefLink = playerIdForUrl ? `<a href="${{getPlayerSportsRefUrl(playerIdForUrl)}}" target="_blank" class="external-link" title="View on Sports Reference">&#8599;</a>` : '';

            document.getElementById('player-detail').innerHTML = `
                <h3 id="player-modal-title">${{player.Player}} ${{sportsRefLink}}</h3>
                <p>Team: ${{player.Team}} ${{genderTag}} | Games: ${{player.Games}}</p>
                <div class="compare-grid">
                    <div class="compare-card">
                        <h4>Averages</h4>
                        <div class="stat-row"><span>PPG</span><span class="${{getStatClass(player.PPG || 0, STAT_THRESHOLDS.ppg)}}">${{player.PPG || 0}}</span></div>
                        <div class="stat-row"><span>RPG</span><span class="${{getStatClass(player.RPG || 0, STAT_THRESHOLDS.rpg)}}">${{player.RPG || 0}}</span></div>
                        <div class="stat-row"><span>APG</span><span class="${{getStatClass(player.APG || 0, STAT_THRESHOLDS.apg)}}">${{player.APG || 0}}</span></div>
                        <div class="stat-row"><span>SPG</span><span>${{player.SPG || 0}}</span></div>
                        <div class="stat-row"><span>BPG</span><span>${{player.BPG || 0}}</span></div>
                    </div>
                    <div class="compare-card">
                        <h4>Shooting</h4>
                        <div class="stat-row"><span>FG%</span><span class="${{getStatClass(player['FG%'] || 0, STAT_THRESHOLDS.fgPct)}}">${{((player['FG%'] || 0) * 100).toFixed(1)}}%</span></div>
                        <div class="stat-row"><span>3P%</span><span class="${{getStatClass(player['3P%'] || 0, STAT_THRESHOLDS.threePct)}}">${{((player['3P%'] || 0) * 100).toFixed(1)}}%</span></div>
                        <div class="stat-row"><span>FT%</span><span>${{((player['FT%'] || 0) * 100).toFixed(1)}}%</span></div>
                    </div>
                    <div class="compare-card">
                        <h4>Totals</h4>
                        <div class="stat-row"><span>Total Points</span><span>${{player['Total PTS'] || 0}}</span></div>
                        <div class="stat-row"><span>Total Rebounds</span><span>${{player['Total REB'] || 0}}</span></div>
                        <div class="stat-row"><span>Total Assists</span><span>${{player['Total AST'] || 0}}</span></div>
                    </div>
                </div>
                ${{games.length > 0 ? `
                    <h4 style="margin-top:1rem">Game Log (${{games.length}} games)</h4>
                    <div class="table-container" style="max-height:300px;overflow-y:auto;">
                        <table>
                            <thead><tr><th>Date</th><th>Opp</th><th>Result</th><th>MIN</th><th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th><th>FG</th><th>3P</th><th>FT</th></tr></thead>
                            <tbody>${{gamesHtml}}</tbody>
                        </table>
                    </div>
                ` : ''}}
            `;

            document.getElementById('player-modal').classList.add('active');
            updateURL('players', {{ player: playerId }});
        }}

        function showVenueDetail(venueName) {{
            if (!venueName) {{
                showToast('Venue not specified');
                return;
            }}

            // Find all games at this venue
            const games = (DATA.games || []).filter(g => g.Venue === venueName);

            if (games.length === 0) {{
                showToast('No games found at this venue');
                return;
            }}

            // Sort by date (most recent first)
            games.sort((a, b) => (b.DateSort || '').localeCompare(a.DateSort || ''));

            // Get venue info
            const venueInfo = DATA.venues?.find(v => v.Venue === venueName) || {{}};
            const city = games[0]?.City || venueInfo.City || '';
            const state = games[0]?.State || venueInfo.State || '';

            const gamesHtml = games.map(g => {{
                const homeWon = (g['Home Score'] || 0) > (g['Away Score'] || 0);
                const winner = homeWon ? g['Home Team'] : g['Away Team'];
                const loser = homeWon ? g['Away Team'] : g['Home Team'];
                const winScore = homeWon ? g['Home Score'] : g['Away Score'];
                const loseScore = homeWon ? g['Away Score'] : g['Home Score'];
                return `
                <tr>
                    <td><a href="${{getSportsRefUrl(g)}}" target="_blank" class="game-link">${{g.Date || ''}}</a></td>
                    <td><strong>${{winner || ''}}</strong></td>
                    <td>${{winScore || 0}}-${{loseScore || 0}}</td>
                    <td>${{loser || ''}}</td>
                </tr>
            `}}).join('');

            document.getElementById('venue-detail').innerHTML = `
                <h3 id="venue-modal-title">${{venueName}}</h3>
                <p>${{city}}${{state ? ', ' + state : ''}} | ${{games.length}} game${{games.length !== 1 ? 's' : ''}}</p>
                ${{venueInfo['Home Wins'] !== undefined ? `
                    <p>Home Wins: ${{venueInfo['Home Wins'] || 0}} | Away Wins: ${{venueInfo['Away Wins'] || 0}}</p>
                ` : ''}}
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Winner</th>
                                <th>Score</th>
                                <th>Loser</th>
                            </tr>
                        </thead>
                        <tbody>${{gamesHtml}}</tbody>
                    </table>
                </div>
            `;

            document.getElementById('venue-modal').classList.add('active');
        }}

        function showGameDetail(gameId) {{
            const game = DATA.games.find(g => g.GameID === gameId);
            if (!game) {{
                showToast('Game not found');
                return;
            }}

            // Get players from this game
            const playerGames = (DATA.playerGames || []).filter(pg => pg.game_id === gameId);
            const awayPlayers = playerGames.filter(p => p.team === game['Away Team']);
            const homePlayers = playerGames.filter(p => p.team === game['Home Team']);

            const renderBoxScore = (players, teamName) => {{
                if (players.length === 0) return '<p>No box score data available</p>';
                return `
                    <table>
                        <thead>
                            <tr>
                                <th>Player</th>
                                <th>MIN</th>
                                <th>PTS</th>
                                <th>FG</th>
                                <th>3P</th>
                                <th>FT</th>
                                <th>ORB</th>
                                <th>DRB</th>
                                <th>REB</th>
                                <th>AST</th>
                                <th>STL</th>
                                <th>BLK</th>
                                <th>TOV</th>
                                <th>PF</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${{players.map(p => `
                                <tr>
                                    <td><span class="player-link" onclick="closeModal('game-modal'); showPlayerDetail('${{p.player_id || p.player}}')">${{p.player || ''}}</span>${{p.player_id ? ` <a href="${{getPlayerSportsRefUrl(p.player_id)}}" target="_blank" class="external-link" title="View on Sports Reference">&#8599;</a>` : ''}}</td>
                                    <td>${{p.mp ? Math.round(p.mp) : 0}}</td>
                                    <td>${{p.pts || 0}}</td>
                                    <td>${{p.fg || 0}}-${{p.fga || 0}}</td>
                                    <td>${{p.fg3 || 0}}-${{p.fg3a || 0}}</td>
                                    <td>${{p.ft || 0}}-${{p.fta || 0}}</td>
                                    <td>${{p.orb || 0}}</td>
                                    <td>${{p.drb || 0}}</td>
                                    <td>${{p.trb || 0}}</td>
                                    <td>${{p.ast || 0}}</td>
                                    <td>${{p.stl || 0}}</td>
                                    <td>${{p.blk || 0}}</td>
                                    <td>${{p.tov || 0}}</td>
                                    <td>${{p.pf || 0}}</td>
                                </tr>
                            `).join('')}}
                        </tbody>
                    </table>
                `;
            }};

            // Build linescore table if available
            const linescore = game.Linescore || {{}};
            const awayLine = linescore.away || {{}};
            const homeLine = linescore.home || {{}};
            const periods = awayLine.quarters || awayLine.halves || [];
            const homePeriods = homeLine.quarters || homeLine.halves || [];
            const awayOT = awayLine.OT || [];
            const homeOT = homeLine.OT || [];
            const isQuarters = !!awayLine.quarters;

            let linescoreHtml = '';
            if (periods.length > 0) {{
                const headers = periods.map((_, i) => isQuarters ? `Q${{i+1}}` : `${{i+1}}H`);
                const otHeaders = awayOT.map((_, i) => `OT${{awayOT.length > 1 ? i+1 : ''}}`);
                linescoreHtml = `
                    <table class="linescore-table" style="width:auto;margin:0 auto 1rem auto;">
                        <thead>
                            <tr>
                                <th style="text-align:left;">Team</th>
                                ${{headers.map(h => `<th style="width:40px;text-align:center;">${{h}}</th>`).join('')}}
                                ${{otHeaders.map(h => `<th style="width:40px;text-align:center;">${{h}}</th>`).join('')}}
                                <th style="width:50px;text-align:center;font-weight:bold;">T</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="text-align:left;">${{game['Away Team']}}</td>
                                ${{periods.map(s => `<td style="text-align:center;">${{s}}</td>`).join('')}}
                                ${{awayOT.map(s => `<td style="text-align:center;">${{s}}</td>`).join('')}}
                                <td style="text-align:center;font-weight:bold;">${{awayLine.total || game['Away Score'] || 0}}</td>
                            </tr>
                            <tr>
                                <td style="text-align:left;">${{game['Home Team']}}</td>
                                ${{homePeriods.map(s => `<td style="text-align:center;">${{s}}</td>`).join('')}}
                                ${{homeOT.map(s => `<td style="text-align:center;">${{s}}</td>`).join('')}}
                                <td style="text-align:center;font-weight:bold;">${{homeLine.total || game['Home Score'] || 0}}</td>
                            </tr>
                        </tbody>
                    </table>
                `;
            }}

            document.getElementById('game-detail').innerHTML = `
                <div class="box-score-header">
                    <div class="box-score-team">
                        <h3>${{game['Away Team']}}</h3>
                        <div class="box-score-score">${{game['Away Score'] || 0}}</div>
                    </div>
                    <div class="box-score-vs">vs</div>
                    <div class="box-score-team">
                        <h3>${{game['Home Team']}}</h3>
                        <div class="box-score-score">${{game['Home Score'] || 0}}</div>
                    </div>
                </div>
                <p style="text-align:center;margin-bottom:1rem;color:var(--text-secondary)">
                    ${{game.Date}} | ${{game.Venue || 'Unknown Venue'}}
                </p>
                ${{linescoreHtml}}
                <div class="box-score-section">
                    <h4>${{game['Away Team']}}</h4>
                    <div class="table-container">${{renderBoxScore(awayPlayers, game['Away Team'])}}</div>
                </div>
                <div class="box-score-section">
                    <h4>${{game['Home Team']}}</h4>
                    <div class="table-container">${{renderBoxScore(homePlayers, game['Home Team'])}}</div>
                </div>
            `;

            document.getElementById('game-modal').classList.add('active');
            updateURL('games', {{ game: gameId }});
        }}

        function searchPlayerGameLog() {{
            const searchValue = document.getElementById('gamelog-player-search').value;
            if (!searchValue) {{
                document.getElementById('gamelog-container').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128203;</div>
                        <h3>Search for a player</h3>
                        <p>Type a player name above to view their game log</p>
                    </div>`;
                return;
            }}

            // Find matching player
            const players = DATA.players || [];
            const matchedPlayer = players.find(p => {{
                const displayName = `${{p.Player}} (${{p.Team}})`;
                return displayName.toLowerCase() === searchValue.toLowerCase() ||
                       p.Player.toLowerCase() === searchValue.toLowerCase();
            }});

            if (!matchedPlayer) {{
                // Show partial matches hint
                const partialMatches = players.filter(p =>
                    p.Player.toLowerCase().includes(searchValue.toLowerCase())
                ).slice(0, 5);

                if (partialMatches.length > 0) {{
                    document.getElementById('gamelog-container').innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">&#128269;</div>
                            <h3>Select a player from suggestions</h3>
                            <p>Click a suggestion or keep typing...</p>
                        </div>`;
                }} else {{
                    document.getElementById('gamelog-container').innerHTML = `
                        <div class="empty-state">
                            <div class="empty-state-icon">&#128533;</div>
                            <h3>No player found</h3>
                            <p>Try a different search term</p>
                        </div>`;
                }}
                return;
            }}

            const playerId = matchedPlayer['Player ID'] || matchedPlayer.Player;
            showPlayerGameLogById(playerId);
        }}

        function showPlayerGameLogById(playerId) {{
            if (!playerId) return;

            const games = (DATA.playerGames || []).filter(g => (g.player_id || g.player) === playerId);

            if (games.length === 0) {{
                document.getElementById('gamelog-container').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128203;</div>
                        <h3>No games found</h3>
                        <p>This player has no recorded games</p>
                    </div>`;
                return;
            }}

            let html = `<table><thead><tr>
                <th>Date</th><th>Opponent</th><th>Result</th><th>MIN</th>
                <th>PTS</th><th>REB</th><th>AST</th><th>STL</th><th>BLK</th>
                <th>FG</th><th>3P</th><th>FT</th>
            </tr></thead><tbody>`;

            games.forEach(g => {{
                html += `<tr>
                    <td>${{g.date}}</td>
                    <td>${{g.opponent}}</td>
                    <td>${{g.result}} ${{g.score}}</td>
                    <td>${{g.mp ? g.mp.toFixed(0) : 0}}</td>
                    <td>${{g.pts || 0}}</td>
                    <td>${{g.trb || 0}}</td>
                    <td>${{g.ast || 0}}</td>
                    <td>${{g.stl || 0}}</td>
                    <td>${{g.blk || 0}}</td>
                    <td>${{g.fg || 0}}-${{g.fga || 0}}</td>
                    <td>${{g.fg3 || 0}}-${{g.fg3a || 0}}</td>
                    <td>${{g.ft || 0}}-${{g.fta || 0}}</td>
                </tr>`;
            }});

            html += '</tbody></table>';
            document.getElementById('gamelog-container').innerHTML = html;
        }}

        function closeModal(modalId) {{
            document.getElementById(modalId).classList.remove('active');
            // Clean up URL params
            const {{ section }} = parseURL();
            updateURL(section);
        }}

        function updateComparison() {{
            const id1 = document.getElementById('compare-player1').value;
            const id2 = document.getElementById('compare-player2').value;

            if (!id1 || !id2) {{
                document.getElementById('compare-grid').innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128101;</div>
                        <h3>Select two players</h3>
                        <p>Choose players from the dropdowns above to compare their statistics</p>
                    </div>
                `;
                if (compareChart) {{
                    compareChart.destroy();
                    compareChart = null;
                }}
                return;
            }}

            const p1 = DATA.players.find(p => (p['Player ID'] || p.Player) === id1);
            const p2 = DATA.players.find(p => (p['Player ID'] || p.Player) === id2);

            if (!p1 || !p2) return;

            const stats = ['PPG', 'RPG', 'APG', 'SPG', 'BPG'];

            let html = `
                <div class="compare-card">
                    <h4>${{p1.Player}}</h4>
                    <p style="color:var(--text-secondary);margin-bottom:0.5rem">${{p1.Team}} | ${{p1.Games}} games</p>
                    ${{stats.map(s => `<div class="stat-row"><span>${{s}}</span><span>${{p1[s] || 0}}</span></div>`).join('')}}
                </div>
                <div class="compare-card">
                    <h4>${{p2.Player}}</h4>
                    <p style="color:var(--text-secondary);margin-bottom:0.5rem">${{p2.Team}} | ${{p2.Games}} games</p>
                    ${{stats.map(s => `<div class="stat-row"><span>${{s}}</span><span>${{p2[s] || 0}}</span></div>`).join('')}}
                </div>
            `;

            document.getElementById('compare-grid').innerHTML = html;

            // Update chart
            if (compareChart) compareChart.destroy();

            const ctx = document.getElementById('compare-chart').getContext('2d');
            compareChart = new Chart(ctx, {{
                type: 'radar',
                data: {{
                    labels: stats,
                    datasets: [
                        {{
                            label: p1.Player,
                            data: stats.map(s => p1[s] || 0),
                            borderColor: '#003087',
                            backgroundColor: 'rgba(0, 48, 135, 0.2)',
                        }},
                        {{
                            label: p2.Player,
                            data: stats.map(s => p2[s] || 0),
                            borderColor: '#e74c3c',
                            backgroundColor: 'rgba(231, 76, 60, 0.2)',
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                }}
            }});

            updateURL('compare', {{ p1: id1, p2: id2 }});
        }}

        function showChart(type) {{
            document.querySelectorAll('#charts .sub-tab').forEach(t => t.classList.remove('active'));
            // Find and activate the button for this chart type
            const btn = document.querySelector(`#charts .sub-tab[onclick*="'${{type}}'"]`);
            if (btn) btn.classList.add('active');

            if (statsChart) statsChart.destroy();

            let data, label, color;

            if (type === 'scoring') {{
                const top = [...(DATA.players || [])].sort((a, b) => (b.PPG || 0) - (a.PPG || 0)).slice(0, 10);
                data = {{
                    labels: top.map(p => p.Player),
                    values: top.map(p => p.PPG || 0)
                }};
                label = 'Points Per Game';
                color = '#003087';
            }} else if (type === 'rebounds') {{
                const sorted = [...(DATA.players || [])].sort((a, b) => (b.RPG || 0) - (a.RPG || 0)).slice(0, 10);
                data = {{
                    labels: sorted.map(p => p.Player),
                    values: sorted.map(p => p.RPG || 0)
                }};
                label = 'Rebounds Per Game';
                color = '#27ae60';
            }} else if (type === 'assists') {{
                const sorted = [...(DATA.players || [])].sort((a, b) => (b.APG || 0) - (a.APG || 0)).slice(0, 10);
                data = {{
                    labels: sorted.map(p => p.Player),
                    values: sorted.map(p => p.APG || 0)
                }};
                label = 'Assists Per Game';
                color = '#9b59b6';
            }} else if (type === 'efficiency') {{
                // Shooting efficiency chart - eFG% and TS% for top 10 players by games
                const qualified = [...(DATA.players || [])].filter(p => p.Games >= 3 && p.FGA >= 5).sort((a, b) => (b['TS%'] || 0) - (a['TS%'] || 0)).slice(0, 10);
                const ctx = document.getElementById('stats-chart').getContext('2d');
                statsChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: qualified.map(p => p.Player),
                        datasets: [
                            {{
                                label: 'eFG%',
                                data: qualified.map(p => ((p['eFG%'] || 0) * 100).toFixed(1)),
                                backgroundColor: '#003087',
                            }},
                            {{
                                label: 'TS%',
                                data: qualified.map(p => ((p['TS%'] || 0) * 100).toFixed(1)),
                                backgroundColor: '#27ae60',
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: true }},
                            title: {{ display: true, text: 'Shooting Efficiency (min 3 games, 5 FGA)' }}
                        }},
                        scales: {{
                            y: {{ beginAtZero: true, max: 100, title: {{ display: true, text: 'Percentage' }} }}
                        }}
                    }}
                }});
                return;
            }} else if (type === 'trends') {{
                // Scoring trends over time - average points per game by date
                const games = [...(DATA.games || [])].sort((a, b) => (a.DateSort || '').localeCompare(b.DateSort || ''));
                if (games.length === 0) {{
                    alert('No game data available for trends');
                    return;
                }}
                const labels = games.map(g => g.Date);
                const awayScores = games.map(g => g['Away Score'] || 0);
                const homeScores = games.map(g => g['Home Score'] || 0);
                const totalScores = games.map((g, i) => awayScores[i] + homeScores[i]);

                const ctx = document.getElementById('stats-chart').getContext('2d');
                statsChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: labels,
                        datasets: [
                            {{
                                label: 'Combined Score',
                                data: totalScores,
                                borderColor: '#003087',
                                backgroundColor: 'rgba(0, 48, 135, 0.1)',
                                fill: true,
                                tension: 0.3
                            }},
                            {{
                                label: 'Away Score',
                                data: awayScores,
                                borderColor: '#e74c3c',
                                backgroundColor: 'transparent',
                                tension: 0.3
                            }},
                            {{
                                label: 'Home Score',
                                data: homeScores,
                                borderColor: '#27ae60',
                                backgroundColor: 'transparent',
                                tension: 0.3
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{ display: true }},
                            title: {{ display: true, text: 'Scoring Trends Over Time' }}
                        }},
                        scales: {{
                            y: {{ beginAtZero: true, title: {{ display: true, text: 'Points' }} }},
                            x: {{ title: {{ display: true, text: 'Game Date' }} }}
                        }}
                    }}
                }});
                return;
            }} else {{
                const teams = [...(DATA.teams || [])].sort((a, b) => (b.Wins || 0) - (a.Wins || 0)).slice(0, 10);
                data = {{
                    labels: teams.map(t => t.Team),
                    values: teams.map(t => t.Wins || 0)
                }};
                label = 'Wins';
                color = '#e74c3c';
            }}

            const ctx = document.getElementById('stats-chart').getContext('2d');
            statsChart = new Chart(ctx, {{
                type: 'bar',
                data: {{
                    labels: data.labels,
                    datasets: [{{
                        label: label,
                        data: data.values,
                        backgroundColor: color,
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }}
                    }},
                    scales: {{
                        y: {{ beginAtZero: true }}
                    }}
                }}
            }});
        }}

        // Handle URL navigation on load
        function handleURLNavigation() {{
            const {{ section, params }} = parseURL();

            // Show the right section
            if (section && document.getElementById(section)) {{
                showSection(section);
            }}

            // Handle subsections
            if (params.sub) {{
                const subBtn = document.querySelector(`#${{section}} .sub-tab:nth-child(${{['stats', 'highs', 'gamelogs', 'records', 'streaks', 'splits', 'conference'].indexOf(params.sub) + 1}})`);
                if (subBtn) subBtn.click();
            }}

            // Handle specific views
            if (params.player) {{
                setTimeout(() => showPlayerDetail(params.player), 100);
            }}
            if (params.game) {{
                setTimeout(() => showGameDetail(params.game), 100);
            }}
            if (params.type && section === 'milestones') {{
                setTimeout(() => showMilestoneEntries(params.type), 100);
            }}
            if (params.p1 && params.p2 && section === 'compare') {{
                document.getElementById('compare-player1').value = params.p1;
                document.getElementById('compare-player2').value = params.p2;
                setTimeout(updateComparison, 100);
            }}
        }}

        // Initialize
        try {{ populateGamesTable(); }} catch(e) {{ console.error('populateGamesTable:', e); }}
        try {{ populatePlayersTable(); }} catch(e) {{ console.error('populatePlayersTable:', e); }}
        try {{ populateSeasonHighs(); }} catch(e) {{ console.error('populateSeasonHighs:', e); }}
        try {{ populateMilestones(); }} catch(e) {{ console.error('populateMilestones:', e); }}
        try {{ populateTeamsTable(); }} catch(e) {{ console.error('populateTeamsTable:', e); }}
        try {{ populateStreaksTable(); }} catch(e) {{ console.error('populateStreaksTable:', e); }}
        try {{ populateSplitsTable(); }} catch(e) {{ console.error('populateSplitsTable:', e); }}
        try {{ populateConferenceTable(); }} catch(e) {{ console.error('populateConferenceTable:', e); }}
        try {{ populateVenuesTable(); }} catch(e) {{ console.error('populateVenuesTable:', e); }}
        try {{ initCalendar(); }} catch(e) {{ console.error('initCalendar:', e); }}
        try {{ initChecklist(); }} catch(e) {{ console.error('initChecklist:', e); }}
        try {{ initOnThisDay(); }} catch(e) {{ console.error('initOnThisDay:', e); }}
        try {{ showChart('scoring'); }} catch(e) {{ console.error('showChart:', e); }}

        // Handle URL on load
        handleURLNavigation();

        // Handle browser back/forward
        window.addEventListener('popstate', handleURLNavigation);
    </script>
</body>
</html>'''

    return html
