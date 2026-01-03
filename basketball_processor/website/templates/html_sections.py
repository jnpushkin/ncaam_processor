"""
HTML section templates for the basketball statistics website.
"""


def get_head(css: str) -> str:
    """Return the HTML head section."""
    return f"""<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>College Basketball Stats</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin=""/>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <style>
{css}
    </style>
</head>"""


def get_body(total_games: int, total_players: int, total_teams: int, total_venues: int, total_points: int, ranked_matchups: int, upsets: int, future_pros: int, generated_time: str) -> str:
    """
    Return the HTML body content.

    Args:
        total_games: Total number of games processed
        total_players: Total number of players
        total_teams: Total number of teams
        total_venues: Total number of unique venues
        total_points: Total points scored in all games
        nba_players: Number of players who went to the NBA
        intl_players: Number of players with international careers
        generated_time: Timestamp when the page was generated
    """
    body_template = """<body>
    <a href="#main-content" class="skip-link">Skip to main content</a>

    <div class="header">
        <div class="header-controls">
            <button class="share-btn" onclick="shareCurrentView()" title="Share this view" aria-label="Share">&#128279;</button>
            <button class="theme-toggle" onclick="toggleTheme()" title="Toggle dark mode" aria-label="Toggle theme">&#127769;</button>
        </div>
        <h1>College Basketball Stats</h1>
        <p class="header-subtitle">Personal game tracking and analytics</p>
        <div class="stats-overview">
            <div class="stat-box">
                <div class="icon">&#127936;</div>
                <div class="number">{TOTAL_GAMES_PLACEHOLDER}</div>
                <div class="label">Games</div>
            </div>
            <div class="stat-box">
                <div class="icon">&#128101;</div>
                <div class="number">{TOTAL_PLAYERS_PLACEHOLDER}</div>
                <div class="label">Players</div>
            </div>
            <div class="stat-box">
                <div class="icon">&#127942;</div>
                <div class="number">{TOTAL_TEAMS_PLACEHOLDER}</div>
                <div class="label">Teams</div>
            </div>
            <div class="stat-box">
                <div class="icon">&#127967;</div>
                <div class="number">{TOTAL_VENUES_PLACEHOLDER}</div>
                <div class="label">Venues</div>
            </div>
            <div class="stat-box">
                <div class="icon">&#128200;</div>
                <div class="number">{TOTAL_POINTS_PLACEHOLDER}</div>
                <div class="label">Points</div>
            </div>
            <div class="stat-box">
                <div class="icon">&#127941;</div>
                <div class="number">{RANKED_MATCHUPS_PLACEHOLDER}</div>
                <div class="label">Ranked Matchups</div>
            </div>
            <div class="stat-box">
                <div class="icon">&#128165;</div>
                <div class="number">{UPSETS_PLACEHOLDER}</div>
                <div class="label">Ranked Upsets</div>
            </div>
            <div class="stat-box highlight">
                <div class="icon">&#11088;</div>
                <div class="number">{FUTURE_PROS_PLACEHOLDER}</div>
                <div class="label">Future Pros</div>
            </div>
        </div>
        <div class="generated-time">Generated: {GENERATED_TIME_PLACEHOLDER}</div>
    </div>

    <div class="container" id="main-content">
        <div class="tabs" role="tablist">
            <button class="tab active" onclick="showSection('games')" role="tab" aria-selected="true" data-section="games" tabindex="0">Games</button>
            <button class="tab" onclick="showSection('players')" role="tab" aria-selected="false" data-section="players" tabindex="-1">Players</button>
            <button class="tab" onclick="showSection('milestones')" role="tab" aria-selected="false" data-section="milestones" tabindex="-1">Achievements</button>
            <button class="tab" onclick="showSection('teams')" role="tab" aria-selected="false" data-section="teams" tabindex="-1">Teams</button>
            <button class="tab" onclick="showSection('matchups')" role="tab" aria-selected="false" data-section="matchups" tabindex="-1">Matchups</button>
            <button class="tab" onclick="showSection('venues')" role="tab" aria-selected="false" data-section="venues" tabindex="-1">Venues</button>
            <button class="tab" onclick="showSection('calendar')" role="tab" aria-selected="false" data-section="calendar" tabindex="-1">Calendar</button>
            <button class="tab" onclick="showSection('conferences')" role="tab" aria-selected="false" data-section="conferences" tabindex="-1">Conference Progress</button>
            <button class="tab" onclick="showSection('map')" role="tab" aria-selected="false" data-section="map" tabindex="-1">Map</button>
            <button class="tab" onclick="showSection('future-pros')" role="tab" aria-selected="false" data-section="future-pros" tabindex="-1">Future Pros</button>
            <button class="tab" onclick="showSection('upcoming')" role="tab" aria-selected="false" data-section="upcoming" tabindex="-1">Upcoming</button>
        </div>

        <div id="games" class="section active" role="tabpanel">
            <h2>
                Game Log
                <div class="section-actions">
                    <button class="btn btn-secondary" onclick="downloadCSV('games')">Download CSV</button>
                </div>
            </h2>
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('games', 'log')">All Games</button>
                <button class="sub-tab" onclick="showSubSection('games', 'records')">Records</button>
                <button class="sub-tab" onclick="showSubSection('games', 'seasons')">Season Stats</button>
            </div>

            <div id="games-log" class="sub-section active">
            <div class="quick-filters">
                <button class="quick-filter active" onclick="quickFilterGames('all')">All</button>
                <button class="quick-filter" onclick="quickFilterGames('ranked')">Ranked</button>
                <button class="quick-filter" onclick="quickFilterGames('upsets')">Upsets</button>
                <button class="quick-filter" onclick="quickFilterGames('ot')">OT</button>
                <button class="quick-filter" onclick="quickFilterGames('mens')">Men's</button>
                <button class="quick-filter" onclick="quickFilterGames('womens')">Women's</button>
            </div>
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
                    <label for="games-division">Division</label>
                    <select id="games-division" onchange="applyFilters('games')">
                        <option value="">All</option>
                        <option value="D1">D1 Only</option>
                        <option value="non-D1">Non-D1</option>
                        <option value="D2">D2 Only</option>
                        <option value="D3">D3 Only</option>
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
                            <th>Badges</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            <div class="pagination" id="games-pagination"></div>
            </div>

            <div id="games-records" class="sub-section">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">Notable game records from your collection.</p>
                <div class="records-grid">
                    <div class="records-section">
                        <h3>Biggest Blowouts</h3>
                        <div id="records-blowouts" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Closest Games</h3>
                        <div id="records-closest" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Highest Scoring (Combined)</h3>
                        <div id="records-highest" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Lowest Scoring (Combined)</h3>
                        <div id="records-lowest" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Most Points (Single Team)</h3>
                        <div id="records-most-single" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Fewest Points (Single Team)</h3>
                        <div id="records-fewest-single" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>100+ Point Games</h3>
                        <div id="records-100pt" class="records-list"></div>
                    </div>
                </div>
            </div>

            <div id="games-seasons" class="sub-section">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">Compare your game attendance across seasons.</p>
                <div class="season-stats-container">
                    <div class="season-chart-container" style="height: 300px; margin-bottom: 2rem;">
                        <canvas id="season-chart"></canvas>
                    </div>
                    <div class="season-summary" id="season-summary"></div>
                    <div class="table-container" style="margin-top: 1rem;">
                        <table id="season-table" aria-label="Season Statistics">
                            <thead>
                                <tr>
                                    <th>Season</th>
                                    <th>Games</th>
                                    <th>Teams</th>
                                    <th>Players</th>
                                    <th>Venues</th>
                                    <th>OT Games</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
            </div>
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
                <button class="sub-tab" onclick="showSubSection('players', 'records')">Records</button>
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
                <div class="search-container" style="position: relative;">
                    <input type="text" class="search-box" id="gamelog-player-search" placeholder="Search for a player..." oninput="updatePlayerSuggestions()" onkeydown="handlePlayerKeydown(event)" aria-label="Search for player game log">
                    <div id="player-suggestions" class="suggestions-dropdown" style="display: none;"></div>
                </div>
                <div class="table-container" id="gamelog-container">
                    <div class="empty-state">
                        <div class="empty-state-icon">&#128203;</div>
                        <h3>Search for a player</h3>
                        <p>Type a player name above to view their game log</p>
                    </div>
                </div>
            </div>

            <div id="players-records" class="sub-section">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">Top individual game performances.</p>
                <div class="records-grid">
                    <div class="records-section">
                        <h3>Most Points</h3>
                        <div id="player-records-pts" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Most Rebounds</h3>
                        <div id="player-records-reb" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Most Assists</h3>
                        <div id="player-records-ast" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Most 3-Pointers</h3>
                        <div id="player-records-3pm" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Most Steals</h3>
                        <div id="player-records-stl" class="records-list"></div>
                    </div>
                    <div class="records-section">
                        <h3>Most Blocks</h3>
                        <div id="player-records-blk" class="records-list"></div>
                    </div>
                </div>
            </div>
        </div>

        <div id="milestones" class="section" role="tabpanel">
            <h2>Achievements</h2>
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">Your collection of game attendance milestones and achievements.</p>

            <div class="badges-summary" id="badges-summary">
                <div class="stat-box">
                    <div class="number" id="badges-total">0</div>
                    <div class="label">Total Badges</div>
                </div>
                <div class="stat-box">
                    <div class="number" id="badges-conferences-complete">0</div>
                    <div class="label">Conferences Complete</div>
                </div>
                <div class="stat-box">
                    <div class="number" id="badges-venues-count">0</div>
                    <div class="label">Venues Visited</div>
                </div>
                <div class="stat-box">
                    <div class="number" id="badges-matchups">0</div>
                    <div class="label">First Matchups</div>
                </div>
            </div>

            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('milestones', 'badges-all')">All Badges</button>
                <button class="sub-tab" onclick="showSubSection('milestones', 'player-milestones')">Player Milestones</button>
                <button class="sub-tab" onclick="showSubSection('milestones', 'venues')">Venue Badges</button>
                <button class="sub-tab" onclick="showSubSection('milestones', 'special')">Special</button>
            </div>

            <div id="milestones-badges-all" class="sub-section active">
                <div class="badges-grid" id="all-badges-grid"></div>
            </div>

            <div id="milestones-player-milestones" class="sub-section">
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

            <div id="milestones-venues" class="sub-section">
                <div class="badges-grid" id="venue-badges-grid"></div>
            </div>

            <div id="milestones-special" class="sub-section">
                <div class="badges-grid" id="special-badges-grid"></div>
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
                <div class="filters" style="margin-bottom: 1rem;">
                    <div class="filter-group">
                        <label for="teams-gender">Gender</label>
                        <select id="teams-gender" onchange="populateTeamsTable()">
                            <option value="">All</option>
                            <option value="M">Men's</option>
                            <option value="W">Women's</option>
                        </select>
                    </div>
                    <input type="text" class="search-box" placeholder="Search teams..." onkeyup="filterTable('teams-table', this.value)" style="flex: 1;">
                </div>
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
                                <th onclick="sortTable('streaks-table', 2)" class="tooltip" data-tooltip="Longest winning streak">Longest Win Streak</th>
                                <th onclick="sortTable('streaks-table', 3)" class="tooltip" data-tooltip="Longest losing streak">Longest Losing Streak</th>
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
                    <select id="h2h-team1" onchange="updateH2HTeam2Options(); updateHeadToHead()">
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

        <div id="matchups" class="section" role="tabpanel">
            <h2>Matchups</h2>
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('matchups', 'matrix')">Team Matrix</button>
                <button class="sub-tab" onclick="showSubSection('matchups', 'conferences')">Conference Matchups</button>
            </div>

            <div id="matchups-matrix" class="sub-section active">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">View head-to-head records between all teams. Click a cell to see game details.</p>
                <div class="matrix-filters">
                    <div class="filter-group">
                        <label for="matrix-conference">Conference</label>
                        <select id="matrix-conference" onchange="buildMatchupMatrix()">
                            <option value="">All Teams</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label for="matrix-min-games">Min Games</label>
                        <select id="matrix-min-games" onchange="buildMatchupMatrix()">
                            <option value="0">Any</option>
                            <option value="2">2+</option>
                            <option value="3">3+</option>
                            <option value="5">5+</option>
                        </select>
                    </div>
                </div>
                <div class="matchup-matrix-container">
                    <div id="matchup-matrix"></div>
                </div>
            </div>

            <div id="matchups-conferences" class="sub-section">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">See which conference vs conference matchups you've witnessed. Click a cell to filter games.</p>
                <div class="conf-crossover-container">
                    <div id="conf-crossover-matrix"></div>
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
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('venues', 'list')">List</button>
                <button class="sub-tab" onclick="showSubSection('venues', 'map')">Map</button>
            </div>

            <div id="venues-list" class="sub-section active">
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

            <div id="venues-map" class="sub-section">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">Map of all venues you've visited.</p>
                <div id="venues-map-container" style="height: 500px; border-radius: 8px; overflow: hidden;"></div>
                <div id="venues-map-summary" style="margin-top: 1rem; display: flex; gap: 2rem; flex-wrap: wrap;"></div>
            </div>
        </div>

        <div id="calendar" class="section" role="tabpanel">
            <h2>Calendar</h2>
            <div class="sub-tabs">
                <button class="sub-tab active" onclick="showSubSection('calendar', 'season')">Season Day Tracker</button>
                <button class="sub-tab" onclick="showSubSection('calendar', 'onthisday')">On This Day</button>
            </div>

            <div id="calendar-season" class="sub-section active">
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

        <div id="conferences" class="section" role="tabpanel">
            <h2>Conference Progress</h2>
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">Track which teams you've seen play and which home arenas you've visited. Click a conference to see details.</p>
            <div class="conf-progress-summary" style="display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap;">
                <div class="stat-box" style="min-width: 100px;">
                    <div class="number" id="conferences-seen-count">0</div>
                    <div class="label">Conferences</div>
                </div>
                <div class="stat-box" style="min-width: 100px;">
                    <div class="number" id="total-teams-seen-count">0</div>
                    <div class="label">Teams Seen</div>
                </div>
                <div class="stat-box" style="min-width: 100px;">
                    <div class="number" id="total-venues-visited-count">0</div>
                    <div class="label">Venues Visited</div>
                </div>
            </div>
            <div class="filters" style="margin-bottom: 1rem;">
                <div class="filter-group">
                    <label for="conf-progress-search">Search Team</label>
                    <input type="text" id="conf-progress-search" class="search-box" placeholder="Search teams..." onkeyup="searchConferenceTeam()">
                </div>
                <div class="filter-group">
                    <label for="conf-progress-gender">Gender</label>
                    <select id="conf-progress-gender" onchange="populateConferenceProgress(); searchConferenceTeam();">
                        <option value="">All</option>
                        <option value="M">Men's</option>
                        <option value="W">Women's</option>
                    </select>
                </div>
            </div>
            <div id="conference-progress-grid" class="conference-progress-grid"></div>
            <div id="conference-detail-panel" class="conference-detail-panel" style="display: none;">
                <div class="conference-detail-header">
                    <button class="btn btn-secondary" onclick="hideConferenceDetail()">← Back to All Conferences</button>
                    <h3 id="conference-detail-title"></h3>
                </div>
                <div id="conference-detail-content"></div>
            </div>
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

        <div id="future-pros" class="section" role="tabpanel">
            <h2>Future Pros ⭐</h2>
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">Players you've seen in college who went on to play professionally (NBA, WNBA, or overseas).</p>
            <div class="table-wrapper">
                <table id="future-pros-table" class="data-table">
                    <thead>
                        <tr>
                            <th onclick="sortTable('future-pros-table', 0)">Player</th>
                            <th onclick="sortTable('future-pros-table', 1)">College Team</th>
                            <th onclick="sortTable('future-pros-table', 2)">League</th>
                            <th onclick="sortTable('future-pros-table', 3)" class="tooltip" data-tooltip="Pro career games played">Pro Games</th>
                            <th onclick="sortTable('future-pros-table', 4)" class="tooltip" data-tooltip="Games you saw them play in college">Games Seen</th>
                            <th onclick="sortTable('future-pros-table', 5)" class="tooltip" data-tooltip="College points per game">PPG</th>
                            <th onclick="sortTable('future-pros-table', 6)" class="tooltip" data-tooltip="Total college points">Total Points</th>
                            <th>Pro Stats</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>

        <div id="upcoming" class="section" role="tabpanel">
            <h2>Upcoming Games at New Venues</h2>
            <p style="margin-bottom: 1rem; color: var(--text-secondary);">Plan your next trip - games at venues you haven't visited yet.</p>

            <div class="sub-tabs">
                <button class="sub-tab" onclick="showUpcomingSubTab('upcoming-list')">Game List</button>
                <button class="sub-tab active" onclick="showUpcomingSubTab('upcoming-map')">Map View</button>
                <button class="sub-tab" onclick="showUpcomingSubTab('upcoming-trips')">Trip Planner</button>
            </div>

            <div id="upcoming-list" class="sub-section">
                <div class="filters-row" style="margin-bottom: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;">
                    <div class="filter-group">
                        <label>State:</label>
                        <div class="multi-select-dropdown" id="upcoming-state-dropdown">
                            <button type="button" class="multi-select-btn" onclick="toggleStateDropdown()">
                                <span id="upcoming-state-label">All States</span>
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="multi-select-options" id="upcoming-state-options">
                                <!-- Populated by JS -->
                            </div>
                        </div>
                    </div>
                    <div class="filter-group">
                        <label for="upcoming-conf-filter">Conference:</label>
                        <select id="upcoming-conf-filter" onchange="filterUpcomingGames()">
                            <option value="">All Conferences</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Date Range:</label>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <input type="date" id="upcoming-start-date" onchange="filterUpcomingGames()"
                                   style="padding: 0.25rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                            <span>to</span>
                            <input type="date" id="upcoming-end-date" onchange="filterUpcomingGames()"
                                   style="padding: 0.25rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                            <button onclick="clearDateFilter()" style="padding: 0.25rem 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-secondary); cursor: pointer;">Clear</button>
                        </div>
                    </div>
                    <div class="filter-group">
                        <label for="upcoming-tv-filter">TV Only:</label>
                        <input type="checkbox" id="upcoming-tv-filter" onchange="filterUpcomingGames()">
                    </div>
                </div>

                <div class="filters-row" style="margin-bottom: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;">
                    <div class="filter-group" style="flex: 1; min-width: 250px;">
                        <label for="upcoming-team-filter">Teams:</label>
                        <input type="text" id="upcoming-team-filter" placeholder="Type to search teams..."
                               oninput="updateTeamSuggestions()" onkeydown="handleTeamKeydown(event)"
                               style="width: 100%; padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                        <div id="team-suggestions" class="suggestions-dropdown" style="display: none;"></div>
                    </div>
                    <div id="selected-teams" style="display: flex; gap: 0.5rem; flex-wrap: wrap;"></div>
                    <div id="upcoming-summary" style="margin-left: auto; color: var(--text-secondary);"></div>
                </div>

                <div class="table-wrapper">
                    <table id="upcoming-table" class="data-table">
                        <thead>
                            <tr>
                                <th>Date</th>
                                <th>Matchup</th>
                                <th>Conference</th>
                                <th>Venue</th>
                                <th>Location</th>
                                <th>TV</th>
                            </tr>
                        </thead>
                        <tbody></tbody>
                    </table>
                </div>
            </div>

            <div id="upcoming-map" class="sub-section active">
                <div class="filters-row" style="margin-bottom: 1rem; display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;">
                    <div class="filter-group">
                        <label>Date Range:</label>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <input type="date" id="upcoming-map-start-date" onchange="updateUpcomingMap()"
                                   style="padding: 0.25rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                            <span>to</span>
                            <input type="date" id="upcoming-map-end-date" onchange="updateUpcomingMap()"
                                   style="padding: 0.25rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                        </div>
                    </div>
                    <div class="filter-group">
                        <label>
                            <input type="checkbox" id="upcoming-map-filter-visible" onchange="updateMapGamesList()">
                            Only show games in visible area
                        </label>
                    </div>
                    <div id="upcoming-map-summary" style="margin-left: auto; color: var(--text-secondary);"></div>
                </div>
                <div id="upcoming-venues-map" style="height: 500px; border-radius: 8px; border: 1px solid var(--border-color);"></div>
                <div id="upcoming-map-legend" style="margin-top: 1rem; display: flex; gap: 2rem; justify-content: center; color: var(--text-secondary);">
                    <span>🔴 1-2 games</span>
                    <span>🟠 3-5 games</span>
                    <span>🟢 6+ games</span>
                    <span style="margin-left: 2rem;">Click a marker for game details. Zoom and pan to explore regions.</span>
                </div>
                <div id="upcoming-map-games" style="margin-top: 1rem;">
                    <h3 style="margin-bottom: 0.5rem;">Games in View</h3>
                    <div class="table-wrapper">
                        <table id="upcoming-map-table" class="data-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>Matchup</th>
                                    <th>Venue</th>
                                    <th>Location</th>
                                </tr>
                            </thead>
                            <tbody></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <div id="upcoming-trips" class="sub-section">
                <p style="margin-bottom: 1rem; color: var(--text-secondary);">Find multi-game road trips with games on consecutive days within driving distance of each other.</p>

                <div class="trip-planner-controls" style="display: flex; gap: 1.5rem; flex-wrap: wrap; margin-bottom: 1.5rem; padding: 1rem; background: var(--bg-secondary); border-radius: 8px;">
                    <div class="filter-group">
                        <label>States:</label>
                        <div class="multi-select-dropdown" id="trip-state-dropdown">
                            <button type="button" class="multi-select-btn" onclick="toggleTripStateDropdown()">
                                <span id="trip-state-label">Select states...</span>
                                <span class="dropdown-arrow">▼</span>
                            </button>
                            <div class="multi-select-options" id="trip-state-options">
                                <!-- Populated by JS -->
                            </div>
                        </div>
                    </div>
                    <div class="filter-group">
                        <label for="trip-max-distance">Max Distance Between Games:</label>
                        <select id="trip-max-distance" onchange="generateTrips()" style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                            <option value="50">50 miles (~1 hour)</option>
                            <option value="100" selected>100 miles (~2 hours)</option>
                            <option value="150">150 miles (~2.5 hours)</option>
                            <option value="200">200 miles (~3.5 hours)</option>
                            <option value="300">300 miles (~5 hours)</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label for="trip-min-games">Min Games per Trip:</label>
                        <select id="trip-min-games" onchange="generateTrips()" style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                            <option value="2" selected>2+ games</option>
                            <option value="3">3+ games</option>
                            <option value="4">4+ games</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label for="trip-max-gap">Max Days Between Games:</label>
                        <select id="trip-max-gap" onchange="generateTrips()" style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                            <option value="1" selected>1 day (consecutive)</option>
                            <option value="2">2 days</option>
                            <option value="3">3 days</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <label>Date Range:</label>
                        <div style="display: flex; gap: 0.5rem; align-items: center;">
                            <input type="date" id="trip-start-date" onchange="generateTrips()"
                                   style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                            <span>to</span>
                            <input type="date" id="trip-end-date" onchange="generateTrips()"
                                   style="padding: 0.5rem; border: 1px solid var(--border-color); border-radius: 4px; background: var(--bg-primary); color: var(--text-primary);">
                        </div>
                    </div>
                </div>

                <div id="trip-summary" style="margin-bottom: 1rem; padding: 0.75rem; background: var(--bg-tertiary); border-radius: 4px; color: var(--text-secondary);"></div>

                <div id="trip-results"></div>
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

    <!-- Day Games Modal (for calendar multi-game days) -->
    <div class="modal" id="day-games-modal" role="dialog" aria-labelledby="day-games-modal-title" onclick="if(event.target === this) closeModal('day-games-modal')">
        <div class="modal-content modal-small">
            <button class="modal-close" onclick="closeModal('day-games-modal')" aria-label="Close">&times;</button>
            <div id="day-games-detail"></div>
        </div>
    </div>

    <!-- Conference Teams Modal (for conference progress click) -->
    <div class="modal" id="conf-teams-modal" role="dialog" aria-labelledby="conf-teams-modal-title" onclick="if(event.target === this) closeModal('conf-teams-modal')">
        <div class="modal-content modal-medium">
            <button class="modal-close" onclick="closeModal('conf-teams-modal')" aria-label="Close">&times;</button>
            <div id="conf-teams-detail"></div>
        </div>
    </div>

    <!-- Toast container -->
    <div id="toast" class="toast"></div>"""

    return (body_template
        .replace('{TOTAL_GAMES_PLACEHOLDER}', str(total_games))
        .replace('{TOTAL_PLAYERS_PLACEHOLDER}', str(total_players))
        .replace('{TOTAL_TEAMS_PLACEHOLDER}', str(total_teams))
        .replace('{TOTAL_VENUES_PLACEHOLDER}', str(total_venues))
        .replace('{TOTAL_POINTS_PLACEHOLDER}', f'{total_points:,}')
        .replace('{RANKED_MATCHUPS_PLACEHOLDER}', str(ranked_matchups))
        .replace('{UPSETS_PLACEHOLDER}', str(upsets))
        .replace('{FUTURE_PROS_PLACEHOLDER}', str(future_pros))
        .replace('{GENERATED_TIME_PLACEHOLDER}', generated_time))


def get_header(total_games: int, total_players: int, total_teams: int, generated_time: str) -> str:
    """Return the header section with statistics overview."""
    return f"""<a href="#main-content" class="skip-link">Skip to main content</a>

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
    </div>"""


def get_navigation() -> str:
    """Return the main navigation tabs."""
    return """<div class="tabs" role="tablist">
            <button class="tab active" onclick="showSection('games')" role="tab" aria-selected="true" data-section="games" tabindex="0">Games</button>
            <button class="tab" onclick="showSection('players')" role="tab" aria-selected="false" data-section="players" tabindex="-1">Players</button>
            <button class="tab" onclick="showSection('milestones')" role="tab" aria-selected="false" data-section="milestones" tabindex="-1">Milestones</button>
            <button class="tab" onclick="showSection('teams')" role="tab" aria-selected="false" data-section="teams" tabindex="-1">Teams</button>
            <button class="tab" onclick="showSection('venues')" role="tab" aria-selected="false" data-section="venues" tabindex="-1">Venues</button>
            <button class="tab" onclick="showSection('calendar')" role="tab" aria-selected="false" data-section="calendar" tabindex="-1">Calendar</button>
            <button class="tab" onclick="showSection('checklist')" role="tab" aria-selected="false" data-section="checklist" tabindex="-1">Checklist</button>
            <button class="tab" onclick="showSection('map')" role="tab" aria-selected="false" data-section="map" tabindex="-1">Map</button>
        </div>"""


def get_main_content(total_games: int, total_players: int, total_teams: int, total_venues: int, total_points: int, ranked_matchups: int, upsets: int, future_pros: int, generated_time: str) -> str:
    """
    Return the full body HTML content.

    This is the main function to use for getting all body content.
    """
    return get_body(total_games, total_players, total_teams, total_venues, total_points, ranked_matchups, upsets, future_pros, generated_time)


def get_modals() -> str:
    """Return the modal dialogs HTML."""
    return """<!-- Player Detail Modal -->
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
    <div id="toast" class="toast"></div>"""
