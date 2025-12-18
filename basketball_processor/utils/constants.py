"""
Basketball constants, team codes, and configuration.
"""

import re
from pathlib import Path
import os


# === Directory and File Path Configuration ===
def _find_project_root():
    """Find the project root directory.

    Searches for CBB_TRACKER_DIR env var, then .project_root marker,
    then falls back to parent.parent.parent.
    """
    # Method 1: Check environment variable first
    env_base = os.environ.get("CBB_TRACKER_DIR")
    if env_base:
        path = Path(env_base).expanduser()
        if path.exists():
            return path

    # Method 2: Look for .project_root marker file
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        marker = parent / ".project_root"
        if marker.exists():
            return parent

    # Method 3: Fall back to parent.parent.parent
    return Path(__file__).resolve().parent.parent.parent


BASE_DIR = _find_project_root()
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
REFERENCES_DIR = BASE_DIR / "basketball_references"
DEFAULT_INPUT_DIR = BASE_DIR / "html_games"

# === BASKETBALL STAT COLUMNS ===
# Basic stats (matching data-stat attributes from Sports Reference)
BASIC_STATS = [
    'mp',       # Minutes Played
    'fg',       # Field Goals Made
    'fga',      # Field Goal Attempts
    'fg_pct',   # Field Goal Percentage
    'fg3',      # 3-Point Field Goals Made
    'fg3a',     # 3-Point Field Goal Attempts
    'fg3_pct',  # 3-Point Field Goal Percentage
    'ft',       # Free Throws Made
    'fta',      # Free Throw Attempts
    'ft_pct',   # Free Throw Percentage
    'orb',      # Offensive Rebounds
    'drb',      # Defensive Rebounds
    'trb',      # Total Rebounds
    'ast',      # Assists
    'stl',      # Steals
    'blk',      # Blocks
    'tov',      # Turnovers
    'pf',       # Personal Fouls
    'pts',      # Points
]

# Advanced stats
ADVANCED_STATS = [
    'efg_pct',          # Effective Field Goal Percentage
    'ts_pct',           # True Shooting Percentage
    'fg3a_per_fga_pct', # 3-Point Attempt Rate
    'fta_per_fga_pct',  # Free Throw Attempt Rate
    'orb_pct',          # Offensive Rebound Percentage
    'drb_pct',          # Defensive Rebound Percentage
    'trb_pct',          # Total Rebound Percentage
    'ast_pct',          # Assist Percentage
    'stl_pct',          # Steal Percentage
    'blk_pct',          # Block Percentage
    'tov_pct',          # Turnover Percentage
    'usg_pct',          # Usage Percentage
    'ortg',             # Offensive Rating
    'drtg',             # Defensive Rating
    'bpm',              # Box Plus/Minus
]

# Four Factors stats
FOUR_FACTORS_STATS = [
    'efg_pct',   # Effective FG%
    'tov_pct',   # Turnover %
    'orb_pct',   # Offensive Rebound %
    'ft_rate',   # Free Throw Rate (FT/FGA)
]

# All stats combined
ALL_STATS = BASIC_STATS + ADVANCED_STATS

# Date formats for parsing
DATE_FORMATS = ["%m/%d/%Y", "%m/%d/%y", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"]

# === TEAM CODES ===
# Maps full team name to abbreviation code
TEAM_CODES = {
    # ACC (Atlantic Coast Conference)
    'Boston College': 'BC',
    'Clemson': 'CLEM',
    'Duke': 'DUKE',
    'Florida State': 'FSU',
    'Georgia Tech': 'GT',
    'Louisville': 'LOU',
    'Miami (FL)': 'MIA',
    'NC State': 'NCST',
    'North Carolina': 'UNC',
    'Notre Dame': 'ND',
    'Pittsburgh': 'PITT',
    'Syracuse': 'SYR',
    'Virginia': 'UVA',
    'Virginia Tech': 'VT',
    'Wake Forest': 'WAKE',
    'California': 'CAL',
    'SMU': 'SMU',
    'Stanford': 'STAN',

    # Big Ten
    'Illinois': 'ILL',
    'Indiana': 'IND',
    'Iowa': 'IOWA',
    'Maryland': 'UMD',
    'Michigan': 'MICH',
    'Michigan State': 'MSU',
    'Minnesota': 'MINN',
    'Nebraska': 'NEB',
    'Northwestern': 'NW',
    'Ohio State': 'OSU',
    'Oregon': 'ORE',
    'Penn State': 'PSU',
    'Purdue': 'PUR',
    'Rutgers': 'RUT',
    'UCLA': 'UCLA',
    'USC': 'USC',
    'Washington': 'WASH',
    'Wisconsin': 'WIS',

    # SEC (Southeastern Conference)
    'Alabama': 'BAMA',
    'Arkansas': 'ARK',
    'Auburn': 'AUB',
    'Florida': 'FLA',
    'Georgia': 'UGA',
    'Kentucky': 'UK',
    'LSU': 'LSU',
    'Mississippi State': 'MSST',
    'Missouri': 'MIZZ',
    'Oklahoma': 'OU',
    'Ole Miss': 'MISS',
    'South Carolina': 'SC',
    'Tennessee': 'TENN',
    'Texas': 'TEX',
    'Texas A&M': 'TAMU',
    'Vanderbilt': 'VAN',

    # Big 12
    'Arizona': 'ARIZ',
    'Arizona State': 'ASU',
    'Baylor': 'BAY',
    'BYU': 'BYU',
    'Cincinnati': 'CIN',
    'Colorado': 'COLO',
    'Houston': 'HOU',
    'Iowa State': 'ISU',
    'Kansas': 'KU',
    'Kansas State': 'KSU',
    'Oklahoma State': 'OKST',
    'TCU': 'TCU',
    'Texas Tech': 'TTU',
    'UCF': 'UCF',
    'Utah': 'UTAH',
    'West Virginia': 'WVU',

    # Big East
    'Butler': 'BUT',
    'UConn': 'CONN',
    'Connecticut': 'CONN',
    'Creighton': 'CREI',
    'DePaul': 'DEP',
    'Georgetown': 'GTOWN',
    'Marquette': 'MARQ',
    'Providence': 'PROV',
    'Seton Hall': 'HALL',
    "St. John's": 'SJU',
    "St. John's (NY)": 'SJU',
    'Villanova': 'NOVA',
    'Xavier': 'XAV',

    # AAC (American Athletic Conference)
    'Charlotte': 'CHAR',
    'East Carolina': 'ECU',
    'FAU': 'FAU',
    'Florida Atlantic': 'FAU',
    'Memphis': 'MEM',
    'Navy': 'NAVY',
    'North Texas': 'UNT',
    'Rice': 'RICE',
    'South Florida': 'USF',
    'Temple': 'TEM',
    'Tulane': 'TUL',
    'Tulsa': 'TLSA',
    'UAB': 'UAB',
    'UTSA': 'UTSA',
    'Wichita State': 'WICH',

    # Mountain West
    'Air Force': 'AFA',
    'Boise State': 'BOIS',
    'Colorado State': 'CSU',
    'Fresno State': 'FRES',
    'Nevada': 'NEV',
    'New Mexico': 'UNM',
    'San Diego State': 'SDSU',
    'San Jose State': 'SJSU',
    'UNLV': 'UNLV',
    'Utah State': 'USU',
    'Wyoming': 'WYO',

    # WCC (West Coast Conference)
    'Gonzaga': 'GONZ',
    'Loyola Marymount': 'LMU',
    'Pacific': 'PAC',
    'Pepperdine': 'PEPP',
    'Portland': 'PORT',
    "Saint Mary's": 'STMCA',
    "Saint Mary's (CA)": 'STMCA',
    'San Diego': 'USD',
    'San Francisco': 'USF',
    'Santa Clara': 'SCU',

    # MVC (Missouri Valley Conference)
    'Belmont': 'BEL',
    'Bradley': 'BRAD',
    'Drake': 'DRAK',
    'Evansville': 'EVAN',
    'Illinois State': 'ILST',
    'Indiana State': 'INST',
    'Missouri State': 'MOST',
    'Murray State': 'MURR',
    'Northern Iowa': 'UNI',
    'Southern Illinois': 'SIU',
    'UIC': 'UIC',
    'Valparaiso': 'VALP',

    # A-10 (Atlantic 10)
    'Dayton': 'DAY',
    'Davidson': 'DVSN',
    'Duquesne': 'DUQ',
    'Fordham': 'FOR',
    'George Mason': 'GMU',
    'George Washington': 'GW',
    'La Salle': 'LAS',
    'Loyola Chicago': 'LCHI',
    'Massachusetts': 'UMASS',
    'Rhode Island': 'URI',
    'Richmond': 'RICH',
    "Saint Joseph's": 'SJU',
    "Saint Louis": 'SLU',
    'St. Bonaventure': 'SBU',
    'VCU': 'VCU',

    # Ivy League
    'Brown': 'BRWN',
    'Columbia': 'CLMB',
    'Cornell': 'COR',
    'Dartmouth': 'DART',
    'Harvard': 'HARV',
    'Penn': 'PENN',
    'Princeton': 'PRIN',
    'Yale': 'YALE',

    # Other notable programs
    'Gonzaga': 'GONZ',
    'Saint Marys': 'SMC',
    'San Diego State': 'SDSU',
    'Creighton': 'CREI',
    'Xavier': 'XAV',
    'Marquette': 'MARQ',
}

# Reverse lookup: code to full name
CODE_TO_TEAM = {v: k for k, v in TEAM_CODES.items()}

# Conference definitions - default fallback values
_DEFAULT_CONFERENCES = {
    'ACC': [
        'Boston College', 'California', 'Clemson', 'Duke', 'Florida State',
        'Georgia Tech', 'Louisville', 'Miami (FL)', 'NC State', 'North Carolina',
        'Notre Dame', 'Pittsburgh', 'SMU', 'Stanford', 'Syracuse', 'Virginia',
        'Virginia Tech', 'Wake Forest'
    ],
    'Big Ten': [
        'Illinois', 'Indiana', 'Iowa', 'Maryland', 'Michigan', 'Michigan State',
        'Minnesota', 'Nebraska', 'Northwestern', 'Ohio State', 'Oregon',
        'Penn State', 'Purdue', 'Rutgers', 'UCLA', 'USC', 'Washington', 'Wisconsin'
    ],
    'SEC': [
        'Alabama', 'Arkansas', 'Auburn', 'Florida', 'Georgia', 'Kentucky', 'LSU',
        'Mississippi State', 'Missouri', 'Oklahoma', 'Ole Miss', 'South Carolina',
        'Tennessee', 'Texas', 'Texas A&M', 'Vanderbilt'
    ],
    'Big 12': [
        'Arizona', 'Arizona State', 'Baylor', 'BYU', 'Cincinnati', 'Colorado',
        'Houston', 'Iowa State', 'Kansas', 'Kansas State', 'Oklahoma State',
        'TCU', 'Texas Tech', 'UCF', 'Utah', 'West Virginia'
    ],
    'Big East': [
        'Butler', 'UConn', 'Creighton', 'DePaul', 'Georgetown', 'Marquette',
        'Providence', 'Seton Hall', "St. John's", 'Villanova', 'Xavier'
    ],
    'WCC': [
        'Gonzaga', 'Loyola Marymount', 'Oregon State', 'Pacific', 'Pepperdine',
        'Portland', "Saint Mary's (CA)", 'San Diego', 'San Francisco', 'Santa Clara', 'Seattle',
        'Washington State'
    ],
    'AAC': [
        'Charlotte', 'East Carolina', 'Florida Atlantic', 'Memphis',
        'North Texas', 'Rice', 'South Florida', 'Temple', 'Tulane', 'Tulsa',
        'UAB', 'UTSA', 'Wichita State'
    ],
    'Mountain West': [
        'Air Force', 'Boise State', 'Colorado State', 'Fresno State', 'Grand Canyon',
        'Nevada', 'New Mexico', 'San Diego State', 'San Jose State', 'UNLV', 'Utah State', 'Wyoming'
    ],
    'Ivy League': [
        'Brown', 'Columbia', 'Cornell', 'Dartmouth', 'Harvard', 'Penn', 'Princeton', 'Yale'
    ],
    'Atlantic 10': [
        'Dayton', 'Davidson', 'Duquesne', 'Fordham', 'George Mason', 'George Washington',
        'La Salle', 'Loyola Chicago', 'Rhode Island', 'Richmond',
        "Saint Joseph's", 'Saint Louis', 'St. Bonaventure', 'VCU'
    ],
    'MVC': [
        'Belmont', 'Bradley', 'Drake', 'Evansville', 'Illinois State', 'Indiana State',
        'Murray State', 'Northern Iowa', 'Southern Illinois', 'UIC', 'Valparaiso'
    ],
    'CAA': [
        'Campbell', 'Charleston', 'Drexel', 'Elon', 'Hampton', 'Hofstra',
        'Monmouth', 'UNCW', 'Northeastern', 'North Carolina A&T', 'Stony Brook', 'Towson', 'William & Mary'
    ],
    'Patriot League': [
        'American', 'Army', 'Boston University', 'Bucknell', 'Colgate', 'Holy Cross',
        'Lafayette', 'Lehigh', 'Loyola (MD)', 'Navy'
    ],
    'WAC': [
        'Abilene Christian', 'California Baptist', 'Southern Utah',
        'Tarleton State', 'Utah Tech', 'Utah Valley', 'UT Arlington'
    ],
    'Big Sky': [
        'Eastern Washington', 'Idaho', 'Idaho State', 'Montana', 'Montana State',
        'Northern Arizona', 'Northern Colorado', 'Portland State', 'Sacramento State', 'Weber State'
    ],
    'Horizon League': [
        'Cleveland State', 'Detroit Mercy', 'Green Bay', 'IU Indianapolis', 'Milwaukee',
        'Northern Kentucky', 'Oakland', 'Purdue Fort Wayne', 'Robert Morris',
        'Wright State', 'Youngstown State'
    ],
    'ASUN': [
        'Austin Peay', 'Bellarmine', 'Central Arkansas', 'Eastern Kentucky',
        'Florida Gulf Coast', 'Jacksonville', 'Lipscomb',
        'North Alabama', 'North Florida', 'Queens', 'Stetson', 'West Georgia'
    ],
    'NEC': [
        'Central Connecticut', 'Fairleigh Dickinson', 'Le Moyne', 'LIU', 'Mercyhurst',
        'Merrimack', 'Sacred Heart', 'St. Francis (PA)', 'Stonehill', 'Wagner'
    ],
    'MAAC': [
        'Canisius', 'Fairfield', 'Iona', 'Manhattan', 'Marist', "Mount St. Mary's",
        'Niagara', 'Quinnipiac', 'Rider', "Saint Peter's", 'Siena'
    ],
    'MEAC': [
        'Coppin State', 'Delaware State', 'Howard', 'Maryland-Eastern Shore',
        'Morgan State', 'Norfolk State', 'North Carolina Central', 'South Carolina State'
    ],
    'SWAC': [
        'Alabama A&M', 'Alabama State', 'Alcorn State', 'Arkansas-Pine Bluff',
        'Bethune-Cookman', 'Florida A&M', 'Grambling State', 'Jackson State',
        'Mississippi Valley State', 'Prairie View A&M', 'Southern', 'Texas Southern'
    ],
    'Southland': [
        'East Texas A&M', 'Houston Christian', 'Incarnate Word', 'Lamar',
        'McNeese', 'New Orleans', 'Nicholls', 'Northwestern State',
        'Southeastern Louisiana', 'Stephen F. Austin', 'Texas A&M-Corpus Christi', 'UTRGV'
    ],
    'OVC': [
        'Little Rock', 'Lindenwood', 'Morehead State', 'SIU Edwardsville',
        'Southeast Missouri State', 'Southern Indiana', 'Tennessee State',
        'Tennessee Tech', 'UT Martin', 'Western Illinois'
    ],
    'Big West': [
        'Cal Poly', 'Cal State Bakersfield', 'Cal State Fullerton', 'Cal State Northridge',
        'Hawaii', 'Long Beach State', 'UC Davis', 'UC Irvine', 'UC Riverside',
        'UC San Diego', 'UC Santa Barbara'
    ],
    'Summit League': [
        'Denver', 'Kansas City', 'North Dakota', 'North Dakota State', 'Omaha',
        'Oral Roberts', 'South Dakota', 'South Dakota State', 'St. Thomas'
    ],
    'Southern Conference': [
        'Chattanooga', 'East Tennessee State', 'Furman', 'Mercer', 'Samford',
        'The Citadel', 'UNC Greensboro', 'VMI', 'Western Carolina', 'Wofford'
    ],
    'America East': [
        'Albany', 'Binghamton', 'Bryant', 'Maine', 'New Hampshire', 'NJIT',
        'UMass Lowell', 'UMBC', 'Vermont'
    ],
    'Conference USA': [
        'Delaware', 'FIU', 'Jacksonville State', 'Kennesaw State', 'Liberty',
        'Louisiana Tech', 'Middle Tennessee', 'Missouri State', 'New Mexico State',
        'Sam Houston', 'UTEP', 'Western Kentucky'
    ],
    'MAC': [
        'Akron', 'Ball State', 'Bowling Green', 'Buffalo', 'Central Michigan',
        'Eastern Michigan', 'Kent State', 'Miami (OH)', 'Northern Illinois',
        'Ohio', 'Toledo', 'UMass', 'Western Michigan'
    ],
}


def _load_conferences():
    """Load conferences from JSON file if available, otherwise use defaults."""
    import json
    conf_file = Path(__file__).parent.parent / 'references' / 'conferences.json'

    if conf_file.exists():
        try:
            with open(conf_file, 'r') as f:
                data = json.load(f)
                conferences = data.get('conferences', {})
                if conferences:
                    return conferences
        except (json.JSONDecodeError, IOError):
            pass

    return _DEFAULT_CONFERENCES


# Load conferences (from JSON if available, else defaults)
CONFERENCES = _load_conferences()

# Team name aliases - maps common variations to canonical names
TEAM_ALIASES = {
    'IUPUI': 'IU Indianapolis',
    'Pitt': 'Pittsburgh',
    'UNC': 'North Carolina',
    'NC State': 'North Carolina State',
    "Saint Mary's": "Saint Mary's (CA)",
    'Southern California': 'USC',
    'UConn': 'Connecticut',
    'Connecticut': 'UConn',  # Both ways since Big East uses UConn
    'SMU': 'Southern Methodist',
    'Southern Methodist': 'SMU',
    'UCF': 'Central Florida',
    'VCU': 'Virginia Commonwealth',
    'GW': 'George Washington',
    'FAU': 'Florida Atlantic',
    'FIU': 'Florida International',
    'UNLV': 'Nevada-Las Vegas',
    'UMass': 'Massachusetts',
    'URI': 'Rhode Island',
    'Loyola (IL)': 'Loyola Chicago',
    'Cal Baptist': 'California Baptist',
    'LMU': 'Loyola Marymount',
    'Saint Francis (PA)': 'St. Francis (PA)',
    'Saint Francis (NY)': 'St. Francis (NY)',
}

# Get conference for a team
def get_conference(team_name):
    """Get conference name for a team."""
    # Try direct match first
    for conf, teams in CONFERENCES.items():
        if team_name in teams:
            return conf

    # Try alias
    canonical = TEAM_ALIASES.get(team_name)
    if canonical:
        for conf, teams in CONFERENCES.items():
            if canonical in teams:
                return conf

    # Try reverse alias (in case canonical name is in CONFERENCES)
    for alias, canonical in TEAM_ALIASES.items():
        if canonical == team_name:
            for conf, teams in CONFERENCES.items():
                if alias in teams:
                    return conf

    return None

# === MILESTONE THRESHOLDS ===
MILESTONE_THRESHOLDS = {
    # Scoring
    'twenty_points': 20,
    'thirty_points': 30,
    'forty_points': 40,
    'fifty_points': 50,

    # Rebounds
    'ten_rebounds': 10,
    'fifteen_rebounds': 15,
    'twenty_rebounds': 20,

    # Assists
    'ten_assists': 10,
    'fifteen_assists': 15,

    # Defense
    'five_blocks': 5,
    'five_steals': 5,

    # Three-pointers
    'five_threes': 5,
    'seven_threes': 7,
    'ten_threes': 10,

    # Efficiency
    'hot_shooting_pct': 0.50,
    'hot_shooting_min_fga': 10,
    'perfect_ft_min': 5,

    # Margin
    'blowout_margin': 20,
}

# === EXCEL COLUMN DEFINITIONS ===
MILESTONE_BASE_COLUMNS = ["Date", "Player", "Team", "Opponent", "Score", "Detail", "GameID"]
PLAYER_BASE_COLUMNS = ["Player", "Player ID", "Team", "Opponent"]

# Excel number formats
DECIMAL_2_CENTER = ("0.00", "center")
DECIMAL_3_CENTER = ("0.000", "center")
INTEGER_CENTER = ("0", "center")
COMMA_NUMBER = ("#,##0", "center")
DATE_CENTER = ("mm/dd/yyyy", "center")
PERCENTAGE_1 = ("0.0%", "center")

# === EXCEL COLOR SCHEME ===
EXCEL_COLORS = {
    'primary_blue': '#003087',      # NCAA blue
    'secondary_orange': '#FF6600',  # NCAA secondary
    'light_blue': '#E8F4F8',
    'accent_green': '#2E7D32',
    'light_green': '#E8F5E8',
    'warning_orange': '#F57C00',
    'light_orange': '#FFF3E0',
    'error_red': '#C62828',
    'light_red': '#FFEBEE',
    'neutral_gray': '#757575',
    'light_gray': '#F5F5F5',
    'white': '#FFFFFF',
    'header_blue': '#1B365D',
    'alt_row': '#F0F8FF',
}

# === REGEX PATTERNS ===
GID_SPLIT_RE = re.compile(r"[,\s]+")
GID_DATE_RE = re.compile(r"^(\d{4})-?(\d{2})-?(\d{2})")

# URL pattern for Sports Reference
SPORTS_REF_PLAYER_URL = "https://www.sports-reference.com/cbb/players/{player_id}.html"
SPORTS_REF_GAME_URL = "https://www.sports-reference.com/cbb/boxscores/{game_id}.html"
