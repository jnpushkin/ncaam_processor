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
            bottom: 100%;
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
            z-index: 100;
        }}
        .tooltip:hover::after {{
            opacity: 1;
            visibility: visible;
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
        .player-link, .game-link, .venue-link {{
            color: var(--accent-color);
            cursor: pointer;
            text-decoration: underline;
        }}
        .player-link:hover, .game-link:hover, .venue-link:hover {{
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
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.5rem;
            }}
            .stats-overview {{
                gap: 1rem;
            }}
            .stat-box {{
                padding: 0.75rem 1rem;
            }}
            .stat-box .number {{
                font-size: 1.5rem;
            }}
            .tabs {{
                justify-content: center;
            }}
            .tab {{
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
            }}
            .filters {{
                flex-direction: column;
            }}
            .filter-group {{
                width: 100%;
            }}
            .filter-group input, .filter-group select {{
                width: 100%;
            }}
            .box-score-header {{
                flex-direction: column;
                gap: 1rem;
            }}
            .box-score-vs {{
                padding: 0;
            }}
            .modal-content {{
                padding: 1rem;
            }}
            .table-container {{
                font-size: 0.85rem;
            }}
            th, td {{
                padding: 0.5rem;
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
            <button class="tab" onclick="showSection('checklist')" role="tab" aria-selected="false" data-section="checklist" tabindex="-1">Checklist</button>
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
                        <label for="players-min-games">Min Games</label>
                        <input type="number" id="players-min-games" min="1" placeholder="1" onchange="applyFilters('players')">
                    </div>
                    <button class="clear-filters" onclick="clearFilters('players')">Clear Filters</button>
                </div>
                <div class="table-container">
                    <table id="players-table" aria-label="Player Statistics">
                        <thead>
                            <tr>
                                <th onclick="sortTable('players-table', 0)">Player</th>
                                <th onclick="sortTable('players-table', 1)">Team</th>
                                <th onclick="sortTable('players-table', 2)" class="tooltip" data-tooltip="Games played">GP</th>
                                <th onclick="sortTable('players-table', 3)" class="tooltip" data-tooltip="Points per game">PPG</th>
                                <th onclick="sortTable('players-table', 4)" class="tooltip" data-tooltip="Rebounds per game">RPG</th>
                                <th onclick="sortTable('players-table', 5)" class="tooltip" data-tooltip="Assists per game">APG</th>
                                <th onclick="sortTable('players-table', 6)" class="tooltip" data-tooltip="Field goal percentage">FG%</th>
                                <th onclick="sortTable('players-table', 7)" class="tooltip" data-tooltip="Three-point percentage">3P%</th>
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
                <select class="compare-select" id="gamelog-player" onchange="showPlayerGameLog()" aria-label="Select player for game log">
                    <option value="">Select a player...</option>
                </select>
                <div class="table-container" id="gamelog-container"></div>
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
            </div>
            <div id="checklist-content"></div>
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
                <button class="sub-tab" onclick="showChart('teams')">Team Wins</button>
            </div>
            <div class="chart-container">
                <canvas id="stats-chart"></canvas>
            </div>
        </div>
    </div>

    <!-- Player Detail Modal -->
    <div class="modal" id="player-modal" role="dialog" aria-labelledby="player-modal-title">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('player-modal')" aria-label="Close">&times;</button>
            <div id="player-detail"></div>
        </div>
    </div>

    <!-- Game Detail Modal (Box Score) -->
    <div class="modal" id="game-modal" role="dialog" aria-labelledby="game-modal-title">
        <div class="modal-content">
            <button class="modal-close" onclick="closeModal('game-modal')" aria-label="Close">&times;</button>
            <div id="game-detail"></div>
        </div>
    </div>

    <!-- Venue Detail Modal -->
    <div class="modal" id="venue-modal" role="dialog" aria-labelledby="venue-modal-title">
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
            players: {{ page: 1, pageSize: 50, total: 0 }},
        }};

        // Filtered data cache
        let filteredData = {{
            games: [],
            players: [],
        }};

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

            filteredData.games = (DATA.games || []).filter(game => {{
                const text = `${{game['Away Team']}} ${{game['Home Team']}} ${{game.Venue || ''}}`.toLowerCase();
                if (search && !text.includes(search)) return false;
                if (gender && game.Gender !== gender) return false;
                if (dateFrom && game.Date < dateFrom) return false;
                if (dateTo && game.Date > dateTo) return false;
                if (team && game['Away Team'] !== team && game['Home Team'] !== team) return false;
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
            const minGames = parseInt(document.getElementById('players-min-games').value) || 0;

            filteredData.players = (DATA.players || []).filter(player => {{
                const text = `${{player.Player}} ${{player.Team}}`.toLowerCase();
                if (search && !text.includes(search)) return false;
                if (gender && player.Gender !== gender) return false;
                if (team && player.Team !== team) return false;
                if (player.Games < minGames) return false;
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
                applyGamesFilters();
            }} else if (type === 'players') {{
                document.getElementById('players-search').value = '';
                document.getElementById('players-gender').value = '';
                document.getElementById('players-team').value = '';
                document.getElementById('players-min-games').value = '';
                applyPlayersFilters();
            }}
        }}

        function getStatClass(value, thresholds) {{
            if (value >= thresholds.excellent) return 'stat-excellent';
            if (value >= thresholds.good) return 'stat-good';
            if (value >= thresholds.average) return 'stat-average';
            return 'stat-poor';
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

            rows.sort((a, b) => {{
                let aVal = a.cells[colIndex].textContent.trim();
                let bVal = b.cells[colIndex].textContent.trim();

                const aNum = parseFloat(aVal.replace(/[^0-9.-]/g, ''));
                const bNum = parseFloat(bVal.replace(/[^0-9.-]/g, ''));

                if (!isNaN(aNum) && !isNaN(bNum)) {{
                    return ascending ? aNum - bNum : bNum - aNum;
                }}

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
                tbody.innerHTML = pageData.map(game => `
                    <tr>
                        <td>${{game.Date || ''}} <a href="${{getSportsRefUrl(game)}}" target="_blank" title="View on Sports Reference" class="external-link">&#8599;</a></td>
                        <td>${{game['Away Team'] || ''}}</td>
                        <td><span class="game-link" onclick="showGameDetail('${{game.GameID || ''}}')">${{game['Away Score'] || 0}}-${{game['Home Score'] || 0}}</span></td>
                        <td>${{game['Home Team'] || ''}}</td>
                        <td><span class="venue-link" onclick="showVenueDetail('${{game.Venue || ''}}')">${{game.Venue || ''}}</span></td>
                        <td>${{game.City || ''}}</td>
                        <td>${{game.State || ''}}</td>
                        <td>${{game.Notes || ''}}</td>
                    </tr>
                `).join('');
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
                tbody.innerHTML = '<tr><td colspan="8" class="empty-state"><div class="empty-state-icon">&#129351;</div><h3>No players found</h3><p>Try adjusting your filters</p></td></tr>';
            }} else {{
                tbody.innerHTML = pageData.map(player => {{
                    const ppg = player.PPG || 0;
                    const rpg = player.RPG || 0;
                    const apg = player.APG || 0;
                    const fgPct = player['FG%'] || 0;
                    const threePct = player['3P%'] || 0;

                    return `
                        <tr>
                            <td><span class="player-link" onclick="showPlayerDetail('${{player['Player ID'] || player.Player}}')">${{player.Player || ''}}</span></td>
                            <td>${{player.Team || ''}}</td>
                            <td>${{player.Games || 0}}</td>
                            <td class="${{getStatClass(ppg, STAT_THRESHOLDS.ppg)}}">${{ppg}}</td>
                            <td class="${{getStatClass(rpg, STAT_THRESHOLDS.rpg)}}">${{rpg}}</td>
                            <td class="${{getStatClass(apg, STAT_THRESHOLDS.apg)}}">${{apg}}</td>
                            <td class="${{getStatClass(fgPct, STAT_THRESHOLDS.fgPct)}}">${{(fgPct * 100).toFixed(1)}}%</td>
                            <td class="${{getStatClass(threePct, STAT_THRESHOLDS.threePct)}}">${{(threePct * 100).toFixed(1)}}%</td>
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

            // Populate comparison dropdowns
            const players = DATA.players || [];
            ['compare-player1', 'compare-player2', 'gamelog-player'].forEach(id => {{
                const sel = document.getElementById(id);
                sel.innerHTML = '<option value="">Select a player...</option>';
                players.forEach(p => {{
                    const option = document.createElement('option');
                    option.value = p['Player ID'] || p.Player;
                    option.textContent = `${{p.Player}} (${{p.Team}})`;
                    sel.appendChild(option);
                }});
            }});
        }}

        function populateSeasonHighs() {{
            const tbody = document.querySelector('#highs-table tbody');
            const data = DATA.seasonHighs || [];

            if (data.length === 0) {{
                tbody.innerHTML = '<tr><td colspan="7" class="empty-state"><h3>No career highs data</h3></td></tr>';
                return;
            }}

            tbody.innerHTML = data.map(player => `
                <tr>
                    <td><span class="player-link" onclick="showPlayerDetail('${{player['Player ID'] || player.Player}}')">${{player.Player || ''}}</span></td>
                    <td>${{player.Team || ''}}</td>
                    <td>${{player['High PTS'] || 0}}</td>
                    <td>${{player['High REB'] || 0}}</td>
                    <td>${{player['High AST'] || 0}}</td>
                    <td>${{player['High 3PM'] || 0}}</td>
                    <td>${{(player['Best Game Score'] || 0).toFixed(1)}}</td>
                </tr>
            `).join('');
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
            tbody.innerHTML = entries.map(entry => `
                <tr>
                    <td>${{entry.Date || ''}}</td>
                    <td><span class="player-link" onclick="showPlayerDetail('${{entry['Player ID'] || entry.Player}}')">${{entry.Player || ''}}</span></td>
                    <td>${{entry.Team || ''}}</td>
                    <td>${{entry.Opponent || ''}}</td>
                    <td>${{entry.Detail || ''}}</td>
                </tr>
            `).join('');

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

        function populateChecklist() {{
            const confName = document.getElementById('checklist-conference').value;
            const gender = document.getElementById('checklist-gender').value;
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
            const teamsHtml = teams.map(t => {{
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

                return `
                    <div class="checklist-item ${{seen ? 'seen' : ''}}">
                        <div class="check-icon ${{seen ? 'checked' : 'unchecked'}}">
                            ${{seen ? '✓' : ''}}
                        </div>
                        <div class="checklist-details">
                            <div class="checklist-team">${{t.team}}${{showConference && t.conference ? ` <span class="checklist-conf">(${{t.conference}})</span>` : ''}}</div>
                            <div class="checklist-venue ${{arenaVisited ? 'visited' : ''}}">
                                ${{arenaVisited ? '✓ ' : ''}}${{homeArena}}
                            </div>
                        </div>
                    </div>
                `;
            }}).join('');

            container.innerHTML = summaryHtml + '<div class="checklist-grid">' + teamsHtml + '</div>';
        }}

        function showPlayerDetail(playerId) {{
            const player = DATA.players.find(p => (p['Player ID'] || p.Player) === playerId);
            if (!player) {{
                showToast('Player not found');
                return;
            }}

            const games = (DATA.playerGames || []).filter(g => (g.player_id || g.player) === playerId);

            let gamesHtml = games.slice(0, 10).map(g => `
                <tr>
                    <td>${{g.date}}</td>
                    <td>${{g.opponent}}</td>
                    <td>${{g.result}}</td>
                    <td>${{g.pts || 0}}</td>
                    <td>${{g.trb || 0}}</td>
                    <td>${{g.ast || 0}}</td>
                </tr>
            `).join('');

            document.getElementById('player-detail').innerHTML = `
                <h3 id="player-modal-title">${{player.Player}}</h3>
                <p>Team: ${{player.Team}} | Games: ${{player.Games}}</p>
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
                    <h4 style="margin-top:1rem">Recent Games</h4>
                    <div class="table-container">
                        <table>
                            <thead><tr><th>Date</th><th>Opp</th><th>Result</th><th>PTS</th><th>REB</th><th>AST</th></tr></thead>
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
                                <th>REB</th>
                                <th>AST</th>
                                <th>FG</th>
                                <th>3P</th>
                                <th>FT</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${{players.map(p => `
                                <tr>
                                    <td>${{p.player || ''}}</td>
                                    <td>${{p.mp ? Math.round(p.mp) : 0}}</td>
                                    <td>${{p.pts || 0}}</td>
                                    <td>${{p.trb || 0}}</td>
                                    <td>${{p.ast || 0}}</td>
                                    <td>${{p.fg || 0}}-${{p.fga || 0}}</td>
                                    <td>${{p.fg3 || 0}}-${{p.fg3a || 0}}</td>
                                    <td>${{p.ft || 0}}-${{p.fta || 0}}</td>
                                </tr>
                            `).join('')}}
                        </tbody>
                    </table>
                `;
            }};

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

        function showPlayerGameLog() {{
            const playerId = document.getElementById('gamelog-player').value;
            if (!playerId) return;

            const games = (DATA.playerGames || []).filter(g => (g.player_id || g.player) === playerId);

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
            event.target.classList.add('active');

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
        populateGamesTable();
        populatePlayersTable();
        populateSeasonHighs();
        populateMilestones();
        populateTeamsTable();
        populateStreaksTable();
        populateSplitsTable();
        populateConferenceTable();
        populateVenuesTable();
        initChecklist();
        showChart('scoring');

        // Handle URL on load
        handleURLNavigation();

        // Handle browser back/forward
        window.addEventListener('popstate', handleURLNavigation);
    </script>
</body>
</html>'''

    return html
