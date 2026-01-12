"""
CSS styles for the basketball statistics website.
"""


def get_css() -> str:
    """Return the CSS styles for the website."""
    return """        :root {
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
        }

        [data-theme="dark"] {
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
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            transition: background 0.3s, color 0.3s;
        }
        .header {
            background: var(--bg-header);
            color: var(--text-header);
            padding: 2.5rem 2rem 2rem;
            text-align: center;
            position: relative;
        }
        .header h1 {
            font-size: 1.75rem;
            font-weight: 600;
            letter-spacing: -0.025em;
            margin-bottom: 0.25rem;
        }
        .header-subtitle {
            font-size: 0.85rem;
            opacity: 0.7;
            font-weight: 400;
            margin-bottom: 1.5rem;
        }
        .header-controls {
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            gap: 0.5rem;
        }
        .theme-toggle, .share-btn {
            background: rgba(255,255,255,0.15);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 1.1rem;
            transition: all 0.2s ease;
            color: white;
            backdrop-filter: blur(10px);
        }
        .theme-toggle:hover, .share-btn:hover {
            background: rgba(255,255,255,0.25);
            transform: translateY(-1px);
        }
        .generated-time {
            position: absolute;
            bottom: 0.75rem;
            right: 1rem;
            font-size: 0.7rem;
            opacity: 0.5;
            font-weight: 400;
        }
        .stats-overview {
            display: flex;
            justify-content: center;
            gap: 0.75rem;
            flex-wrap: nowrap;
            max-width: 1200px;
            margin: 0 auto;
        }
        .stat-box {
            background: rgba(255,255,255,0.08);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.12);
            padding: 0.75rem 1rem;
            border-radius: 12px;
            text-align: center;
            min-width: 85px;
            flex: 1;
            transition: all 0.2s ease;
        }
        .stat-box:hover {
            background: rgba(255,255,255,0.12);
            transform: translateY(-2px);
            border-color: rgba(255,255,255,0.2);
        }
        .stat-box .icon {
            font-size: 1rem;
            margin-bottom: 0.35rem;
            opacity: 0.9;
        }
        .stat-box .number {
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: -0.025em;
            line-height: 1.1;
        }
        .stat-box .label {
            font-size: 0.65rem;
            opacity: 0.7;
            text-transform: uppercase;
            letter-spacing: 0.03em;
            font-weight: 500;
            margin-top: 0.2rem;
        }
        .stat-box.highlight .number {
            color: #ffd700;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        .tabs {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            justify-content: center;
        }
        .tab {
            padding: 0.75rem 1.5rem;
            background: var(--bg-secondary);
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 1rem;
            color: var(--text-primary);
            transition: all 0.2s;
            box-shadow: var(--shadow);
        }
        .tab:hover {
            background: var(--hover-color);
        }
        .tab.active {
            background: var(--accent-color);
            color: white;
        }
        .tab:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }
        .section {
            display: none;
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: var(--shadow);
        }
        .section.active {
            display: block;
        }
        .section h2 {
            margin-bottom: 1rem;
            color: var(--accent-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .section-actions {
            display: flex;
            gap: 0.5rem;
        }
        .btn {
            padding: 0.5rem 1rem;
            background: var(--accent-color);
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            transition: opacity 0.2s;
        }
        .btn:hover {
            opacity: 0.9;
        }
        .btn-secondary {
            background: var(--bg-primary);
            color: var(--text-primary);
            border: 1px solid var(--border-color);
        }
        .sub-tabs {
            display: flex;
            gap: 0.25rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        .sub-tab {
            padding: 0.5rem 1rem;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.85rem;
            color: var(--text-secondary);
            transition: all 0.2s;
        }
        .sub-tab:hover {
            background: var(--hover-color);
        }
        .sub-tab.active {
            background: var(--accent-light);
            color: var(--accent-color);
            border-color: var(--accent-color);
        }
        .sub-section {
            display: none;
        }
        .sub-section.active {
            display: block;
        }
        /* Advanced Filters */
        .filters {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            align-items: flex-end;
            padding: 1rem;
            background: var(--bg-primary);
            border-radius: 8px;
        }
        .filter-group {
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        }
        .filter-group label {
            font-size: 0.75rem;
            color: var(--text-secondary);
            text-transform: uppercase;
        }
        .filter-group input, .filter-group select {
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            min-width: 150px;
        }
        .filter-group input:focus, .filter-group select:focus {
            outline: none;
            border-color: var(--accent-color);
        }
        .clear-filters {
            padding: 0.5rem 1rem;
            background: transparent;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            color: var(--text-secondary);
        }
        .clear-filters:hover {
            background: var(--hover-color);
        }
        .filter-summary {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1rem;
            margin-bottom: 1rem;
            background: var(--bg-secondary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            font-size: 0.9rem;
        }
        .filter-summary-text {
            flex: 1;
            color: var(--text-secondary);
        }
        .filter-summary-text strong {
            color: var(--text-primary);
            font-weight: 600;
        }
        .filter-summary-text .filter-chip {
            display: inline-block;
            background: var(--accent-color);
            color: white;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            margin: 0 0.25rem;
            font-size: 0.85rem;
        }
        .filter-summary-clear {
            padding: 0.4rem 0.8rem;
            background: transparent;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            color: var(--text-secondary);
            font-size: 0.85rem;
            white-space: nowrap;
        }
        .filter-summary-clear:hover {
            background: var(--hover-color);
            color: var(--text-primary);
        }
        .team-rank {
            display: inline-block;
            background: var(--accent-color);
            color: white;
            padding: 0.1rem 0.4rem;
            border-radius: 3px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-right: 0.25rem;
        }
        .suggestions-dropdown {
            position: absolute;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            max-height: 200px;
            overflow-y: auto;
            z-index: 100;
            width: 100%;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .suggestion-item {
            padding: 0.5rem 1rem;
            cursor: pointer;
        }
        .suggestion-item:hover {
            background: var(--hover-color);
        }
        .multi-select-dropdown {
            position: relative;
            display: inline-block;
        }
        .multi-select-btn {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.5rem;
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-primary);
            color: var(--text-primary);
            cursor: pointer;
            min-width: 150px;
            font-size: inherit;
        }
        .multi-select-btn:hover {
            border-color: var(--accent-color);
        }
        .dropdown-arrow {
            font-size: 0.7rem;
            color: var(--text-secondary);
        }
        .multi-select-options {
            display: none;
            position: absolute;
            top: 100%;
            left: 0;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            min-width: 200px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .multi-select-options.show {
            display: block;
        }
        .multi-select-option {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 0.75rem;
            cursor: pointer;
            white-space: nowrap;
        }
        .multi-select-option:hover {
            background: var(--hover-color);
        }
        .multi-select-option input[type="checkbox"] {
            margin: 0;
            cursor: pointer;
        }
        .multi-select-actions {
            display: flex;
            gap: 0.5rem;
            padding: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            background: var(--bg-secondary);
        }
        .multi-select-actions button {
            padding: 0.25rem 0.5rem;
            font-size: 0.75rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-primary);
            cursor: pointer;
            color: var(--text-primary);
        }
        .multi-select-actions button:hover {
            background: var(--hover-color);
        }
        .filter-group {
            position: relative;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        th, td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        th {
            background: var(--bg-primary);
            font-weight: 600;
            position: sticky;
            top: 0;
            cursor: pointer;
            user-select: none;
            white-space: nowrap;
        }
        th:hover {
            background: var(--hover-color);
        }
        th.sorted-asc::after {
            content: ' \\25B2';
            font-size: 0.7rem;
        }
        th.sorted-desc::after {
            content: ' \\25BC';
            font-size: 0.7rem;
        }
        tr:hover {
            background: var(--hover-color);
        }
        .table-container {
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
            margin-bottom: 1rem;
        }
        .table-container table {
            min-width: 100%;
        }
        .table-scroll {
            max-height: none;
        }
        .sticky-col {
            position: sticky;
            left: 0;
            background: var(--bg-primary);
            z-index: 10;
            box-shadow: 2px 0 4px rgba(0,0,0,0.1);
        }
        thead .sticky-col {
            background: var(--bg-secondary);
            z-index: 20;
        }
        tr:hover .sticky-col {
            background: var(--hover-color);
        }
        .clickable-row {
            cursor: pointer;
        }
        .clickable-row:hover {
            background: var(--hover-color);
        }
        .gender-tag {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-left: 0.25rem;
        }
        .nba-badge, .wnba-badge, .intl-badge {
            font-size: 0.85rem;
            margin-left: 0.35rem;
            cursor: help;
            position: relative;
        }
        .league-logo {
            height: 16px;
            width: auto;
            vertical-align: middle;
            margin-top: -2px;
        }
        .league-logo.fiba-logo {
            height: 18px;
            border-radius: 3px;
        }
        .nba-badge[data-tooltip]:hover::after,
        .wnba-badge[data-tooltip]:hover::after,
        .intl-badge[data-tooltip]:hover::after {
            content: attr(data-tooltip);
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0, 0, 0, 0.85);
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            white-space: nowrap;
            z-index: 1000;
            pointer-events: none;
        }
        tr.nba-player {
            background: linear-gradient(90deg, rgba(200, 16, 46, 0.08) 0%, transparent 30%);
        }
        tr.nba-player:hover {
            background: linear-gradient(90deg, rgba(200, 16, 46, 0.15) 0%, var(--hover-color) 30%);
        }
        .status-badge {
            display: inline-block;
            padding: 0.2rem 0.5rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
        }
        .status-badge.nba-active {
            background: #2E7D32;
            color: white;
        }
        .status-badge.nba-former {
            background: #757575;
            color: white;
        }
        .nba-link, .intl-link {
            color: var(--accent-color);
            text-decoration: none;
            font-weight: 500;
        }
        .nba-link:hover, .intl-link:hover {
            text-decoration: underline;
        }
        .proballers-link {
            color: #6B7280;
            text-decoration: none;
            font-size: 0.85rem;
            margin-left: 0.5rem;
            opacity: 0.7;
        }
        .proballers-link:hover {
            text-decoration: underline;
            opacity: 1;
        }
        .intl-badge {
            font-size: 0.85rem;
            margin-left: 0.35rem;
            cursor: help;
        }
        tr.intl-player {
            background: linear-gradient(90deg, rgba(46, 125, 50, 0.08) 0%, transparent 30%);
        }
        tr.intl-player:hover {
            background: linear-gradient(90deg, rgba(46, 125, 50, 0.15) 0%, var(--hover-color) 30%);
        }
        tr.wnba-player {
            background: linear-gradient(90deg, rgba(255, 102, 0, 0.08) 0%, transparent 30%);
        }
        tr.wnba-player:hover {
            background: linear-gradient(90deg, rgba(255, 102, 0, 0.15) 0%, var(--hover-color) 30%);
        }
        /* National Team only (Olympics/FIBA, not professional overseas) */
        tr.national-team-player {
            background: linear-gradient(90deg, rgba(100, 149, 237, 0.08) 0%, transparent 30%);
        }
        tr.national-team-player:hover {
            background: linear-gradient(90deg, rgba(100, 149, 237, 0.15) 0%, var(--hover-color) 30%);
        }
        .intl-badge.national-team {
            opacity: 0.8;
        }
        .natl-link {
            color: #6495ED;
            text-decoration: none;
            font-weight: 500;
        }
        .natl-link:hover {
            text-decoration: underline;
        }
        .status-badge.wnba-active {
            background: #FF6600;
            color: white;
        }
        .status-badge.wnba-former {
            background: #B8860B;
            color: white;
        }
        .wnba-link {
            color: #FF6600;
            text-decoration: none;
            font-weight: 500;
        }
        .wnba-link:hover {
            text-decoration: underline;
        }
        /* Signed but never played styles */
        .nba-badge.signed-only,
        .wnba-badge.signed-only {
            opacity: 0.7;
        }
        tr.nba-player.signed-only,
        tr.wnba-player.signed-only {
            background: linear-gradient(90deg, rgba(128, 128, 128, 0.08) 0%, transparent 30%);
        }
        tr.nba-player.signed-only:hover,
        tr.wnba-player.signed-only:hover {
            background: linear-gradient(90deg, rgba(128, 128, 128, 0.15) 0%, var(--hover-color) 30%);
        }
        .nba-stat .number {
            color: #C8102E;
        }
        .wnba-stat .number {
            color: #FF6600;
        }
        .intl-stat .number {
            color: #2E7D32;
        }
        #nba-table, #wnba-table, #intl-table {
            margin-top: 1rem;
        }
        #nba-table th, #nba-table td, #wnba-table th, #wnba-table td, #intl-table th, #intl-table td {
            text-align: center;
        }
        #nba-table th:first-child, #nba-table td:first-child,
        #wnba-table th:first-child, #wnba-table td:first-child,
        #intl-table th:first-child, #intl-table td:first-child {
            text-align: left;
        }
        .gender-seen {
            display: inline-block;
            font-size: 0.65rem;
            font-weight: 600;
            padding: 0.1rem 0.25rem;
            border-radius: 3px;
            margin-left: 0.15rem;
        }
        .gender-m {
            background: #1976D2;
            color: white;
        }
        .gender-w {
            background: #E91E63;
            color: white;
        }
        .checklist-venue .gender-m, .checklist-venue .gender-w {
            font-size: 0.6rem;
            padding: 0.05rem 0.2rem;
            vertical-align: middle;
        }
        /* Calendar grid */
        .calendar-grid {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
        }
        .calendar-year {
            margin-bottom: 1rem;
        }
        .calendar-year h3 {
            margin-bottom: 0.5rem;
            color: var(--accent-color);
        }
        .calendar-months {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
        }
        .calendar-month {
            background: var(--bg-primary);
            border-radius: 8px;
            padding: 1rem;
            border: 1px solid var(--border-color);
        }
        .calendar-month h4 {
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        .calendar-days {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 2px;
        }
        .calendar-day-header {
            font-size: 0.7rem;
            text-align: center;
            color: var(--text-secondary);
            padding: 2px;
        }
        .calendar-day {
            aspect-ratio: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.75rem;
            border-radius: 4px;
            background: var(--bg-secondary);
            cursor: default;
        }
        .calendar-day.empty {
            background: transparent;
        }
        .calendar-day.has-game {
            background: var(--accent-color);
            color: white;
            font-weight: bold;
            cursor: pointer;
        }
        .calendar-day.has-game:hover {
            background: var(--accent-hover);
            transform: scale(1.1);
        }
        .calendar-day.has-multiple {
            background: var(--excellent);
        }
        .calendar-day.out-of-range {
            background: transparent;
            color: var(--text-secondary);
            opacity: 0.3;
        }
        .calendar-progress {
            margin-bottom: 1.5rem;
            text-align: center;
        }
        .calendar-progress .progress-text {
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }
        .calendar-progress .progress-bar {
            height: 24px;
            background: var(--bg-secondary);
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color);
        }
        .calendar-progress .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-color), var(--excellent));
            border-radius: 12px;
            transition: width 0.3s ease;
        }
        /* Stat highlighting */
        .stat-excellent { color: var(--excellent); font-weight: bold; }
        .stat-good { color: var(--good); }
        .stat-average { color: var(--average); }
        .stat-poor { color: var(--poor); }
        /* Tooltips */
        .tooltip {
            position: relative;
            cursor: help;
        }
        .tooltip::after {
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
        }
        .tooltip:hover::after {
            opacity: 1;
            visibility: visible;
        }
        thead {
            position: relative;
            z-index: 50;
        }
        .search-box {
            width: 100%;
            max-width: 400px;
            padding: 0.75rem 1rem;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            font-size: 1rem;
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        .search-box:focus {
            outline: none;
            border-color: var(--accent-color);
            box-shadow: 0 0 0 3px rgba(0,48,135,0.1);
        }
        .controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            align-items: center;
        }
        /* Pagination */
        .pagination {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.5rem;
            margin-top: 1rem;
            padding: 1rem 0;
        }
        .pagination button {
            padding: 0.5rem 1rem;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            cursor: pointer;
            color: var(--text-primary);
        }
        .pagination button:hover:not(:disabled) {
            background: var(--hover-color);
        }
        .pagination button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .pagination button.active {
            background: var(--accent-color);
            color: white;
            border-color: var(--accent-color);
        }
        .pagination-info {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        .page-size-select {
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text-primary);
        }
        /* Empty state */
        .empty-state {
            text-align: center;
            padding: 3rem;
            color: var(--text-muted);
        }
        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        .empty-state h3 {
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
        }
        /* Loading state */
        .loading {
            text-align: center;
            padding: 2rem;
        }
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid var(--border-color);
            border-top-color: var(--accent-color);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .milestone-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .milestone-card {
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            border: 2px solid transparent;
        }
        .milestone-card:hover {
            border-color: var(--accent-color);
            transform: translateY(-2px);
        }
        .milestone-card.active {
            border-color: var(--accent-color);
            background: var(--accent-light);
        }
        .milestone-card:focus {
            outline: 2px solid var(--accent-color);
            outline-offset: 2px;
        }
        .milestone-card .count {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }
        .milestone-card .name {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        .chart-container {
            position: relative;
            height: 300px;
            margin-bottom: 2rem;
        }
        .player-link, .game-link, .venue-link, .team-link {
            color: var(--accent-color);
            cursor: pointer;
            text-decoration: underline;
        }
        .game-link {
            white-space: nowrap;
        }
        .player-link:hover, .game-link:hover, .venue-link:hover, .team-link:hover {
            opacity: 0.8;
        }
        .external-link {
            color: #666;
            text-decoration: none;
            font-size: 0.85em;
            margin-left: 4px;
        }
        .external-link:hover {
            color: var(--accent-color);
        }
        .checklist-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
        }
        .checklist-item {
            display: flex;
            align-items: center;
            padding: 0.5rem;
            border-radius: 4px;
            background: var(--card-bg);
        }
        .checklist-item.seen {
            background: #e8f5e9;
        }
        .check-icon {
            width: 24px;
            height: 24px;
            margin-right: 0.5rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        .check-icon.checked {
            background: #4caf50;
            color: white;
        }
        .check-icon.unchecked {
            background: #e0e0e0;
            color: #999;
        }
        .checklist-details {
            flex: 1;
        }
        .checklist-team {
            font-weight: 600;
        }
        .checklist-conf {
            font-weight: 400;
            font-size: 0.85em;
            color: var(--text-muted);
        }
        .checklist-venue {
            font-size: 0.85em;
            color: #666;
        }
        .checklist-venue.visited {
            color: #4caf50;
        }
        .checklist-summary {
            background: var(--card-bg);
            padding: 1rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            display: flex;
            gap: 2rem;
        }
        .checklist-stat {
            text-align: center;
        }
        .checklist-stat-value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }
        .checklist-stat-label {
            font-size: 0.85em;
            color: #666;
        }
        .modal {
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
        }
        .modal.active {
            display: flex;
        }
        .modal-content {
            background: var(--bg-secondary);
            border-radius: 12px;
            padding: 2rem;
            max-width: 1000px;
            max-height: 90vh;
            overflow-y: auto;
            width: 95%;
            position: relative;
        }
        .modal-close {
            position: absolute;
            top: 1rem;
            right: 1rem;
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: var(--text-secondary);
        }
        .modal-close:hover {
            color: var(--text-primary);
        }
        .modal-small {
            max-width: 500px;
        }
        .modal-medium {
            max-width: 600px;
        }
        /* Conference Teams Modal */
        .conf-teams-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.5rem;
        }
        .conf-teams-column {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .conf-teams-heading {
            font-size: 0.9rem;
            font-weight: 600;
            margin: 0 0 0.5rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid var(--border-color);
        }
        .conf-teams-heading.seen {
            color: #22c55e;
            border-color: #22c55e;
        }
        .conf-teams-heading.unseen {
            color: var(--text-secondary);
        }
        .conf-team-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 0.5rem;
            border-radius: 4px;
        }
        .conf-team-item.seen {
            background: rgba(34, 197, 94, 0.1);
        }
        .conf-team-item.unseen {
            background: var(--bg-primary);
        }
        .conf-team-check {
            font-size: 0.85rem;
            width: 1.2rem;
            text-align: center;
        }
        .conf-team-item.seen .conf-team-check {
            color: #22c55e;
        }
        .conf-team-item.unseen .conf-team-check {
            color: var(--text-tertiary);
        }
        .conf-team-name {
            font-size: 0.9rem;
        }
        .conf-team-empty {
            color: var(--text-secondary);
            font-style: italic;
            margin: 0;
            padding: 0.5rem;
        }
        @media (max-width: 480px) {
            .conf-teams-grid {
                grid-template-columns: 1fr;
            }
        }
        /* Day Games Modal */
        .day-games-list {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        .day-game-item {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.75rem 1rem;
            background: var(--bg-primary);
            border-radius: 8px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .day-game-item:hover {
            background: var(--hover-color);
        }
        .day-game-year {
            font-weight: 600;
            color: var(--accent-color);
            min-width: 50px;
        }
        .day-game-matchup {
            flex: 1;
        }
        .day-game-score {
            font-weight: 500;
            color: var(--text-secondary);
        }
        .back-to-day-btn {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 0.5rem 1rem;
            cursor: pointer;
            color: var(--accent-color);
            font-size: 0.9rem;
            margin-bottom: 1rem;
            transition: background 0.2s;
        }
        .back-to-day-btn:hover {
            background: var(--hover-color);
        }
        /* Box Score Modal */
        .box-score-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid var(--border-color);
        }
        .box-score-team {
            text-align: center;
            flex: 1;
        }
        .box-score-team h3 {
            font-size: 1.25rem;
            margin-bottom: 0.25rem;
        }
        .box-score-score {
            font-size: 2.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }
        .box-score-vs {
            padding: 0 2rem;
            font-size: 1.5rem;
            color: var(--text-muted);
        }
        .box-score-section {
            margin-bottom: 2rem;
        }
        .box-score-section h4 {
            margin-bottom: 0.5rem;
            color: var(--accent-color);
        }
        /* Game Detail Badges and Info */
        .game-badge {
            display: inline-block;
            padding: 0.2rem 0.6rem;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 600;
            margin: 0 0.25rem;
            text-transform: uppercase;
        }
        .neutral-badge {
            background: #9c27b0;
            color: white;
        }
        .division-badge {
            background: #ff9800;
            color: white;
        }
        .game-info-item {
            display: inline-block;
            margin: 0 0.75rem;
        }
        .game-info-item strong {
            color: var(--text-primary);
        }
        .game-officials {
            border-top: 1px solid var(--border-color);
            padding-top: 0.75rem;
            margin-top: 0.5rem;
        }
        .compare-select {
            padding: 0.5rem;
            border: 1px solid var(--border-color);
            border-radius: 4px;
            background: var(--bg-secondary);
            color: var(--text-primary);
            min-width: 200px;
        }
        .compare-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .compare-card {
            background: var(--bg-primary);
            padding: 1rem;
            border-radius: 8px;
        }
        .compare-card h4 {
            margin-bottom: 0.5rem;
            color: var(--accent-color);
        }
        .stat-row {
            display: flex;
            justify-content: space-between;
            padding: 0.25rem 0;
            border-bottom: 1px solid var(--border-color);
        }
        /* Toast notifications */
        .toast {
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
        }
        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }
        /* Skip to content link for accessibility */
        .skip-link {
            position: absolute;
            top: -40px;
            left: 0;
            background: var(--accent-color);
            color: white;
            padding: 8px;
            z-index: 100;
        }
        .skip-link:focus {
            top: 0;
        }
        /* Mobile-first responsive styles */
        @media (max-width: 768px) {
            .header {
                padding: 1.5rem 1rem 1rem;
            }
            .header h1 {
                font-size: 1.25rem;
                margin-top: 2rem;
            }
            .header-subtitle {
                font-size: 0.75rem;
                margin-bottom: 1rem;
            }
            .header-controls {
                top: 0.5rem;
                right: 0.5rem;
            }
            .theme-toggle, .share-btn {
                width: 34px;
                height: 34px;
                font-size: 0.95rem;
                border-radius: 8px;
            }
            .generated-time {
                font-size: 0.6rem;
                right: 0.5rem;
            }
            .stats-overview {
                gap: 0.5rem;
            }
            .stat-box {
                padding: 0.75rem 1rem;
                min-width: 90px;
                border-radius: 10px;
            }
            .stat-box .icon {
                font-size: 1rem;
                margin-bottom: 0.25rem;
            }
            .stat-box .number {
                font-size: 1.25rem;
            }
            .stat-box .label {
                font-size: 0.65rem;
            }
            .container {
                padding: 1rem;
            }
            .tabs {
                justify-content: flex-start;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                -ms-overflow-style: none;
                padding-bottom: 0.5rem;
                flex-wrap: nowrap;
            }
            .tabs::-webkit-scrollbar {
                display: none;
            }
            .tab {
                padding: 0.5rem 0.75rem;
                font-size: 0.8rem;
                flex-shrink: 0;
                white-space: nowrap;
            }
            .sub-tabs {
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: none;
                flex-wrap: nowrap;
                padding-bottom: 0.5rem;
            }
            .sub-tabs::-webkit-scrollbar {
                display: none;
            }
            .sub-tab {
                flex-shrink: 0;
                white-space: nowrap;
                font-size: 0.75rem;
                padding: 0.4rem 0.75rem;
            }
            .section {
                padding: 1rem;
                border-radius: 8px;
            }
            .section h2 {
                font-size: 1.1rem;
                flex-direction: column;
                align-items: flex-start;
                gap: 0.5rem;
            }
            .section-actions {
                width: 100%;
            }
            .section-actions .btn {
                width: 100%;
                text-align: center;
            }
            .filters {
                flex-direction: column;
                padding: 0.75rem;
                gap: 0.75rem;
            }
            .filter-group {
                width: 100%;
            }
            .filter-group label {
                font-size: 0.7rem;
            }
            .filter-group input, .filter-group select {
                width: 100%;
                padding: 0.6rem;
                font-size: 0.9rem;
            }
            .clear-filters {
                width: 100%;
                padding: 0.6rem;
            }
            .controls {
                flex-direction: column;
                gap: 0.75rem;
            }
            .search-box {
                width: 100%;
                max-width: none;
                font-size: 0.9rem;
            }
            .compare-select {
                width: 100%;
                min-width: auto;
            }
            .box-score-header {
                flex-direction: column;
                gap: 0.75rem;
            }
            .box-score-team h3 {
                font-size: 1rem;
            }
            .box-score-score {
                font-size: 2rem;
            }
            .box-score-vs {
                padding: 0;
                font-size: 1rem;
            }
            .modal-content {
                padding: 1rem;
                width: 98%;
                max-height: 95vh;
            }
            .modal-close {
                top: 0.5rem;
                right: 0.5rem;
            }
            .table-container {
                font-size: 0.75rem;
                margin: 0 -1rem;
                width: calc(100% + 2rem);
                border-radius: 0;
            }
            th, td {
                padding: 0.4rem 0.5rem;
            }
            th {
                font-size: 0.7rem;
            }
            .sticky-col {
                min-width: 100px;
            }
            .milestone-grid {
                grid-template-columns: repeat(2, 1fr);
                gap: 0.5rem;
            }
            .milestone-card {
                padding: 0.75rem;
            }
            .milestone-card .count {
                font-size: 1.25rem;
            }
            .milestone-card .name {
                font-size: 0.8rem;
            }
            .checklist-grid {
                grid-template-columns: 1fr;
            }
            .checklist-summary {
                flex-wrap: wrap;
                gap: 1rem;
                padding: 0.75rem;
            }
            .checklist-stat-value {
                font-size: 1.25rem;
            }
            .compare-grid {
                grid-template-columns: 1fr;
            }
            .chart-container {
                height: 250px;
            }
            .calendar-months {
                grid-template-columns: 1fr;
            }
            .pagination {
                flex-wrap: wrap;
                gap: 0.25rem;
            }
            .pagination button {
                padding: 0.4rem 0.6rem;
                font-size: 0.8rem;
            }
            .toast {
                bottom: 1rem;
                right: 1rem;
                left: 1rem;
                text-align: center;
            }
            #school-map {
                height: 350px !important;
            }
            #map-legend {
                flex-direction: column;
                gap: 0.5rem;
            }
            .onthisday-game {
                padding: 0.75rem !important;
            }
            .onthisday-game > div {
                flex-direction: column !important;
                align-items: flex-start !important;
            }
        }

        /* Extra small screens */
        @media (max-width: 480px) {
            .header h1 {
                font-size: 1.1rem;
            }
            .header-subtitle {
                font-size: 0.7rem;
                margin-bottom: 0.75rem;
            }
            .stats-overview {
                gap: 0.35rem;
            }
            .stat-box {
                padding: 0.5rem 0.6rem;
                min-width: 70px;
                border-radius: 8px;
            }
            .stat-box .icon {
                font-size: 0.85rem;
                margin-bottom: 0.15rem;
            }
            .stat-box .number {
                font-size: 1rem;
            }
            .stat-box .label {
                font-size: 0.55rem;
            }
            .tab {
                padding: 0.4rem 0.6rem;
                font-size: 0.75rem;
            }
            .milestone-grid {
                grid-template-columns: 1fr;
            }
            th, td {
                padding: 0.3rem 0.4rem;
                font-size: 0.7rem;
            }
        }
        /* Print styles */
        @media print {
            .header-controls, .tabs, .sub-tabs, .filters, .pagination, .btn, .modal {
                display: none !important;
            }
            .section {
                display: block !important;
                box-shadow: none;
                page-break-inside: avoid;
            }
            .table-container {
                max-height: none;
                overflow: visible;
            }
        }
        /* Matchup Matrix */
        .matchup-matrix-container {
            overflow-x: auto;
            margin-top: 1rem;
        }
        .matchup-matrix {
            border-collapse: collapse;
            font-size: 0.75rem;
        }
        .matchup-matrix th,
        .matchup-matrix td {
            padding: 4px 6px;
            text-align: center;
            border: 1px solid var(--border-color);
            white-space: nowrap;
        }
        .matchup-matrix th {
            background: var(--bg-primary);
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .matchup-matrix th.row-header {
            position: sticky;
            left: 0;
            z-index: 20;
            text-align: left;
            min-width: 120px;
        }
        .matchup-matrix th.corner {
            position: sticky;
            left: 0;
            top: 0;
            z-index: 30;
        }
        .matchup-matrix td {
            cursor: pointer;
            transition: background 0.15s;
        }
        .matchup-matrix td:hover {
            background: var(--hover-color);
        }
        .matchup-matrix td.win-record {
            background: rgba(39, 174, 96, 0.15);
            color: var(--success);
        }
        .matchup-matrix td.loss-record {
            background: rgba(231, 76, 60, 0.15);
            color: var(--danger);
        }
        .matchup-matrix td.even-record {
            background: rgba(243, 156, 18, 0.1);
            color: var(--warning);
        }
        .matchup-matrix td.no-games {
            color: var(--text-muted);
            cursor: default;
        }
        .matchup-matrix td.diagonal {
            background: var(--bg-primary);
            cursor: default;
        }
        .matrix-filters {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            align-items: flex-end;
        }
        @media (max-width: 768px) {
            .matchup-matrix {
                font-size: 0.65rem;
            }
            .matchup-matrix th,
            .matchup-matrix td {
                padding: 3px 4px;
            }
            .matchup-matrix th.row-header {
                min-width: 80px;
            }
        }
        /* First Matchup Badge */
        .first-matchup-badge {
            background: linear-gradient(135deg, #ffd700, #ffec8b);
            color: #333;
            font-size: 0.6rem;
            font-weight: bold;
            padding: 2px 5px;
            border-radius: 3px;
            margin-left: 6px;
            text-transform: uppercase;
            box-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }
        /* Badge container */
        .badge-container {
            display: inline;
        }
        /* Upset badge */
        .upset-badge {
            background: linear-gradient(135deg, #ff6b6b, #ee5a5a);
            color: white;
            font-size: 0.6rem;
            font-weight: bold;
            padding: 2px 5px;
            border-radius: 3px;
            margin-left: 6px;
            text-transform: uppercase;
            box-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }
        /* AP Ranking Badge */
        .ap-rank {
            background: linear-gradient(135deg, #1a73e8, #4285f4);
            color: white;
            font-size: 0.7rem;
            font-weight: bold;
            padding: 2px 5px;
            border-radius: 3px;
            margin-right: 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.15);
        }
        .ap-rank:hover {
            background: linear-gradient(135deg, #1557b0, #1a73e8);
        }
        /* Ranked matchup row highlighting */
        tr.ranked-matchup {
            background: linear-gradient(90deg, rgba(26, 115, 232, 0.08), rgba(255, 215, 0, 0.08));
        }
        tr.ranked-matchup:hover {
            background: linear-gradient(90deg, rgba(26, 115, 232, 0.15), rgba(255, 215, 0, 0.15));
        }
        tr.has-ranked {
            background: rgba(26, 115, 232, 0.04);
        }
        tr.has-ranked:hover {
            background: rgba(26, 115, 232, 0.1);
        }
        /* OT Label */
        .ot-label {
            background: linear-gradient(135deg, #9c27b0, #7b1fa2);
            color: white;
            font-size: 0.6rem;
            font-weight: bold;
            padding: 2px 5px;
            border-radius: 3px;
            margin-left: 4px;
            text-transform: uppercase;
            box-shadow: 0 1px 2px rgba(0,0,0,0.2);
        }
        /* Milestone badges */
        .milestone-badge {
            background: linear-gradient(135deg, #00bcd4, #0097a7);
            color: white;
            font-size: 0.55rem;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 3px;
            margin: 2px 3px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.15);
            white-space: nowrap;
            display: inline-block;
        }
        .milestone-badge.more {
            background: linear-gradient(135deg, #78909c, #546e7a);
            cursor: pointer;
        }
        .milestone-badge.more:hover {
            background: linear-gradient(135deg, #90a4ae, #607d8b);
        }
        /* Upset badge spacing */
        .upset-badge {
            margin: 2px 3px;
            display: inline-block;
        }
        /* Badges cell and hidden badges */
        .badges-cell {
            white-space: normal;
            max-width: 280px;
            line-height: 1.8;
        }
        .badges-hidden {
            display: none;
        }
        .badges-hidden.expanded {
            display: inline;
        }
        /* Division badges for venues */
        .division-badge, .status-badge {
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            text-transform: uppercase;
        }
        .division-badge.division-d1 {
            background: var(--accent-color);
            color: white;
        }
        .division-badge.division-d2 {
            background: #6c757d;
            color: white;
        }
        .division-badge.division-d3 {
            background: #868e96;
            color: white;
        }
        .status-badge.status-current {
            background: var(--success);
            color: white;
        }
        .status-badge.status-historic {
            background: var(--warning);
            color: white;
        }
        .neutral-badge {
            display: inline-block;
            padding: 0.15rem 0.4rem;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
            background: #9333ea;
            color: white;
            margin-left: 0.4rem;
            vertical-align: middle;
        }
        /* Quick filters */
        .quick-filters {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        .quick-filter {
            padding: 0.4rem 0.8rem;
            border: 1px solid var(--border-color);
            background: var(--bg-secondary);
            color: var(--text-secondary);
            border-radius: 20px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        .quick-filter:hover {
            border-color: var(--accent-color);
            color: var(--accent-color);
        }
        .quick-filter.active {
            background: var(--accent-color);
            border-color: var(--accent-color);
            color: white;
        }
        /* Conference Crossover Matrix */
        .conf-crossover-container {
            overflow-x: auto;
            margin-top: 1rem;
        }
        .conf-crossover {
            border-collapse: collapse;
            font-size: 0.8rem;
        }
        .conf-crossover th,
        .conf-crossover td {
            padding: 6px 8px;
            text-align: center;
            border: 1px solid var(--border-color);
        }
        .conf-crossover th {
            background: var(--bg-primary);
            font-weight: 600;
        }
        .conf-crossover td {
            cursor: pointer;
            transition: background 0.15s;
        }
        .conf-crossover td:hover {
            background: var(--hover-color);
        }
        .conf-crossover td.has-games {
            background: rgba(0, 48, 135, 0.1);
            color: var(--accent-color);
            font-weight: 600;
        }
        .conf-crossover td.diagonal {
            background: var(--bg-primary);
            color: var(--text-muted);
        }
        .conf-crossover td.no-games {
            color: var(--text-muted);
        }
        /* Teams at Venue List */
        .venue-teams-list {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }
        .venue-team-tag {
            background: var(--bg-primary);
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8rem;
            border: 1px solid var(--border-color);
        }
        .venue-team-tag .conf-label {
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-left: 4px;
        }
        .venue-stats-summary {
            display: flex;
            gap: 1.5rem;
            margin: 1rem 0;
            flex-wrap: wrap;
        }
        .venue-stat-item {
            text-align: center;
        }
        .venue-stat-item .value {
            font-size: 1.5rem;
            font-weight: bold;
            color: var(--accent-color);
        }
        .venue-stat-item .label {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        /* Badges Section */
        .badges-summary {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-bottom: 1.5rem;
            flex-wrap: wrap;
        }
        .badges-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .badge-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }
        .badge-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        .badge-card.complete {
            border-color: #4CAF50;
            background: linear-gradient(135deg, var(--bg-primary) 0%, rgba(76,175,80,0.1) 100%);
        }
        .badge-card-header {
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.5rem;
        }
        .badge-icon {
            font-size: 2rem;
            line-height: 1;
        }
        .badge-title {
            font-weight: 600;
            font-size: 1rem;
        }
        .badge-subtitle {
            font-size: 0.8rem;
            color: var(--text-secondary);
        }
        .badge-progress {
            margin-top: 0.75rem;
        }
        .badge-progress-bar {
            height: 8px;
            background: var(--bg-tertiary);
            border-radius: 4px;
            overflow: hidden;
        }
        .badge-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-color), #64B5F6);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        .badge-progress-fill.complete {
            background: linear-gradient(90deg, #4CAF50, #81C784);
        }
        .badge-progress-text {
            font-size: 0.75rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
            text-align: right;
        }
        .badge-date {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
        }
        /* Conference Progress Grid */
        .conference-progress-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 1rem;
            margin-top: 1rem;
        }
        .conf-progress-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .conf-progress-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        .conf-progress-card.complete {
            border-color: #4CAF50;
            background: linear-gradient(135deg, var(--bg-primary) 0%, rgba(76,175,80,0.1) 100%);
        }
        .conf-progress-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.75rem;
        }
        .conf-progress-name {
            font-weight: 600;
            font-size: 1rem;
        }
        .conf-progress-count {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }
        .conf-progress-teams {
            display: flex;
            flex-wrap: wrap;
            gap: 0.25rem;
            margin-top: 0.75rem;
        }
        .conf-team-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
        }
        .conf-team-dot.seen {
            background: #4CAF50;
            border-color: #4CAF50;
        }
        .conf-team-dot.seen-m {
            background: #2196F3;
            border-color: #2196F3;
        }
        .conf-team-dot.seen-w {
            background: #E91E63;
            border-color: #E91E63;
        }
        /* Venue dots */
        .conf-progress-venue-dots {
            display: flex;
            flex-wrap: wrap;
            gap: 3px;
            margin-top: 0.25rem;
        }
        .conf-venue-dot {
            width: 8px;
            height: 8px;
            border-radius: 2px;
            background: var(--bg-tertiary);
            border: 1px solid var(--border-color);
        }
        .conf-venue-dot.visited {
            background: #FF9800;
            border-color: #FF9800;
        }
        /* Badge type colors */
        .badge-type-team { border-left: 4px solid #2196F3; }
        .badge-type-venue { border-left: 4px solid #4CAF50; }
        .badge-type-matchup { border-left: 4px solid #FF9800; }
        .badge-type-conf-first { border-left: 4px solid #9C27B0; }
        .badge-type-conf-matchup { border-left: 4px solid #673AB7; }
        .badge-type-conf-complete { border-left: 4px solid #FFD700; }
        .badge-type-holiday { border-left: 4px solid #E91E63; }
        .badge-type-game-count { border-left: 4px solid #00BCD4; }
        .badge-type-transfer { border-left: 4px solid #795548; }
        .badge-type-d1-game { border-left: 4px solid #1565C0; }
        .badge-type-d1-venue { border-left: 4px solid #2E7D32; }
        /* Badge icons by type */
        .badge-icon-team::before { content: '🏀'; }
        .badge-icon-venue::before { content: '🏟️'; }
        .badge-icon-matchup::before { content: '🤝'; }
        .badge-icon-conf-first::before { content: '🏆'; }
        .badge-icon-conf-matchup::before { content: '⚔️'; }
        .badge-icon-conf-complete::before { content: '👑'; }
        .badge-icon-holiday::before { content: '🎉'; }
        .badge-icon-game-count::before { content: '🎫'; }
        .badge-icon-transfer::before { content: '✈️'; }
        .badge-icon-d1-game::before { content: '🎯'; }
        .badge-icon-d1-venue::before { content: '🏛️'; }

        /* Trip Planner */
        .trip-card {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            margin-bottom: 1rem;
            overflow: hidden;
        }
        .trip-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 1rem;
            background: var(--bg-secondary);
            border-bottom: 1px solid var(--border-color);
            flex-wrap: wrap;
            gap: 0.5rem;
        }
        .trip-title {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }
        .trip-number {
            background: var(--accent-color);
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-weight: bold;
            font-size: 0.85rem;
        }
        .trip-games-count {
            background: #4CAF50;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }
        .trip-venues-count {
            background: #FF9800;
            color: white;
            padding: 0.25rem 0.5rem;
            border-radius: 4px;
            font-size: 0.85rem;
        }
        .trip-meta {
            display: flex;
            align-items: center;
            gap: 1rem;
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        .trip-dates {
            font-weight: 500;
        }
        .trip-total-distance {
            color: var(--accent-color);
        }
        .trip-itinerary {
            padding: 1rem;
        }
        .trip-game {
            padding: 0.75rem 0;
            border-bottom: 1px solid var(--border-color);
        }
        .trip-game:last-child {
            border-bottom: none;
            padding-bottom: 0;
        }
        .trip-game:first-child {
            padding-top: 0;
        }
        .trip-distance {
            display: block;
            color: var(--text-secondary);
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
            padding-left: 1rem;
        }
        .trip-game-info {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem 1rem;
            align-items: baseline;
        }
        .trip-date {
            color: var(--text-secondary);
            font-size: 0.85rem;
            min-width: 140px;
        }
        .trip-matchup {
            flex: 1;
            min-width: 200px;
        }
        .trip-venue {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }
        .trip-tv {
            background: #2196F3;
            color: white;
            padding: 0.15rem 0.4rem;
            border-radius: 3px;
            font-size: 0.75rem;
        }
        @media (max-width: 768px) {
            .trip-header {
                flex-direction: column;
                align-items: flex-start;
            }
            .trip-game-info {
                flex-direction: column;
                gap: 0.25rem;
            }
            .trip-date {
                min-width: unset;
            }
        }

        /* Records grid */
        .records-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }
        .records-section {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 1rem;
        }
        .records-section h3 {
            margin: 0 0 1rem 0;
            font-size: 1rem;
            color: var(--accent-color);
            border-bottom: 2px solid var(--accent-color);
            padding-bottom: 0.5rem;
        }
        .records-list {
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }
        .record-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            background: var(--bg-secondary);
            border-radius: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .record-item:hover {
            background: var(--bg-tertiary);
        }
        .record-item .rank {
            font-weight: bold;
            color: var(--accent-color);
            min-width: 1.5rem;
        }
        .record-item .teams {
            flex: 1;
            margin: 0 0.75rem;
            font-size: 0.9rem;
        }
        .record-item .teams .gender-tag {
            font-size: 0.7rem;
            opacity: 0.7;
        }
        .record-item .score {
            font-weight: bold;
            white-space: nowrap;
            margin-right: 0.75rem;
        }
        .record-item .margin {
            color: var(--accent-color);
            font-weight: bold;
            min-width: 3rem;
            text-align: right;
        }
        .record-item .total {
            color: #4CAF50;
            font-weight: bold;
            min-width: 3rem;
            text-align: right;
        }
        /* Player record specific styles */
        .record-item.player-record {
            align-items: flex-start;
        }
        .record-item .record-details {
            flex: 1;
            min-width: 0;
        }
        .record-item .record-main {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 0.5rem;
        }
        .record-item .player-name {
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .record-item .stat-value {
            color: #4CAF50;
            font-weight: bold;
            white-space: nowrap;
        }
        .record-item .record-sub {
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-top: 0.25rem;
        }"""
