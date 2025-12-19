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
            padding: 2rem;
            text-align: center;
            position: relative;
        }
        .header h1 {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .header-controls {
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            gap: 0.5rem;
        }
        .theme-toggle, .share-btn {
            background: rgba(255,255,255,0.2);
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            cursor: pointer;
            font-size: 1.2rem;
            transition: background 0.3s;
            color: white;
        }
        .theme-toggle:hover, .share-btn:hover {
            background: rgba(255,255,255,0.3);
        }
        .generated-time {
            position: absolute;
            bottom: 0.5rem;
            right: 1rem;
            font-size: 0.75rem;
            opacity: 0.7;
        }
        .stats-overview {
            display: flex;
            justify-content: center;
            gap: 2rem;
            margin-top: 1rem;
            flex-wrap: wrap;
        }
        .stat-box {
            background: rgba(255,255,255,0.1);
            padding: 1rem 2rem;
            border-radius: 8px;
            text-align: center;
        }
        .stat-box .number {
            font-size: 2rem;
            font-weight: bold;
        }
        .stat-box .label {
            font-size: 0.9rem;
            opacity: 0.9;
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
        /* Monthly calendar */
        .monthly-calendar {
            display: grid;
            grid-template-columns: repeat(7, 1fr);
            gap: 4px;
            max-width: 700px;
            margin: 0 auto;
        }
        .monthly-calendar .day-header {
            text-align: center;
            font-weight: bold;
            padding: 0.5rem;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }
        .monthly-calendar .day-cell {
            min-height: 80px;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            padding: 4px;
            font-size: 0.75rem;
        }
        .monthly-calendar .day-cell.empty {
            background: transparent;
            border-color: transparent;
        }
        .monthly-calendar .day-cell.has-games {
            background: var(--accent-color);
            border-color: var(--accent-color);
        }
        .monthly-calendar .day-cell.has-games:hover {
            background: var(--accent-hover);
            cursor: pointer;
        }
        .monthly-calendar .day-number {
            font-weight: bold;
            margin-bottom: 2px;
        }
        .monthly-calendar .day-cell.has-games .day-number {
            color: white;
        }
        .monthly-calendar .day-games {
            font-size: 0.7rem;
            color: rgba(255,255,255,0.9);
            overflow: hidden;
        }
        .monthly-calendar .day-games .game-entry {
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
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
                padding: 1rem;
            }
            .header h1 {
                font-size: 1.25rem;
                margin-top: 2rem;
            }
            .header-controls {
                top: 0.5rem;
                right: 0.5rem;
            }
            .theme-toggle, .share-btn {
                width: 36px;
                height: 36px;
                font-size: 1rem;
            }
            .generated-time {
                font-size: 0.65rem;
                right: 0.5rem;
            }
            .stats-overview {
                gap: 0.5rem;
                margin-top: 0.75rem;
            }
            .stat-box {
                padding: 0.5rem 0.75rem;
            }
            .stat-box .number {
                font-size: 1.25rem;
            }
            .stat-box .label {
                font-size: 0.75rem;
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
            .monthly-calendar {
                font-size: 0.7rem;
            }
            .monthly-calendar .day-cell {
                min-height: 60px;
                padding: 2px;
            }
            .monthly-calendar .day-games {
                font-size: 0.6rem;
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
            .stat-box {
                padding: 0.4rem 0.5rem;
            }
            .stat-box .number {
                font-size: 1rem;
            }
            .stat-box .label {
                font-size: 0.65rem;
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
        }"""
