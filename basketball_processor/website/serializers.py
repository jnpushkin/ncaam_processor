"""
Data serializers for website JSON generation.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import json

from ..utils.nba_players import get_nba_player_info_by_id, get_nba_status_batch, recheck_female_players_for_wnba
from ..utils.schedule_scraper import (
    get_schedule, filter_upcoming_games, get_visited_venues_from_games,
    SCHEDULE_CACHE_FILE, normalize_state, get_espn_team_id
)


# Team name normalization: map abbreviations to official names
TEAM_NAME_MAP = {
    'UNC': 'North Carolina',
    'Pitt': 'Pittsburgh',
    'UConn': 'Connecticut',
    'USC': 'Southern California',
    'VCU': 'Virginia Commonwealth',
    'UCF': 'Central Florida',
    'UNLV': 'Nevada-Las Vegas',
    'SMU': 'Southern Methodist',
    'LSU': 'Louisiana State',
    'BYU': 'Brigham Young',
    'TCU': 'Texas Christian',
    'UTEP': 'Texas-El Paso',
    'UTSA': 'Texas-San Antonio',
    'UAB': 'Alabama-Birmingham',
    'UMass': 'Massachusetts',
    'UNH': 'New Hampshire',
    'URI': 'Rhode Island',
    'UCSB': 'UC Santa Barbara',
    'UCLA': 'UCLA',  # Keep as-is (official name)
    'Cal': 'California',
}


def normalize_team_name(name: str) -> str:
    """Normalize team name abbreviations to official names."""
    if not name:
        return name
    return TEAM_NAME_MAP.get(name, name)


class DataSerializer:
    """Convert DataFrames to JSON format for website."""

    def __init__(self, processed_data: Dict[str, Any], raw_games: List[Dict] = None):
        """
        Initialize serializer.

        Args:
            processed_data: Dictionary of processed DataFrames
            raw_games: Optional list of raw game dictionaries
        """
        self.processed_data = processed_data
        self.raw_games = raw_games or []

    def serialize_all(self, skip_nba: bool = False) -> Dict[str, Any]:
        """
        Serialize all data for website.

        Args:
            skip_nba: If True, skip NBA/WNBA player lookups for faster generation

        Returns:
            Dictionary ready for JSON encoding
        """
        self._skip_nba = skip_nba

        # Auto-refresh conference data if needed (runs every ~90 days)
        try:
            from ..utils.school_history_scraper import auto_refresh_if_needed
            auto_refresh_if_needed(include_women=True, silent=False)
        except ImportError:
            pass

        # Check female players for WNBA status before serialization (unless skipped)
        if not skip_nba:
            recheck_female_players_for_wnba()

        summary = self._serialize_summary()
        players = self._serialize_players()

        # Count unique future pros (any player with NBA, WNBA, or International status)
        future_pros_count = sum(1 for p in players if p.get('NBA') or p.get('WNBA') or p.get('International'))
        summary['futurePros'] = future_pros_count

        return {
            'summary': summary,
            'games': self._serialize_games(),
            'players': players,
            'milestones': self._serialize_milestones(),
            'teams': self._serialize_teams(),
            'venues': self._serialize_venues(),
            'playerGames': self._serialize_player_games(),
            'startersBench': self._serialize_starters_bench(),
            'seasonHighs': self._serialize_season_highs(),
            'teamStreaks': self._serialize_team_streaks(),
            'headToHead': self._serialize_head_to_head(),
            'conferenceStandings': self._serialize_conference_standings(),
            'homeAwaySplits': self._serialize_home_away_splits(),
            'attendanceStats': self._serialize_attendance_stats(),
            'conferenceChecklist': self._serialize_conference_checklist(),
            'upcomingGames': self._serialize_upcoming_games(),
        }

    def _serialize_summary(self) -> Dict[str, Any]:
        """Serialize summary statistics."""
        game_log = self.processed_data.get('game_log', pd.DataFrame())
        players = self.processed_data.get('players', pd.DataFrame())
        team_records = self.processed_data.get('team_records', pd.DataFrame())
        venue_records = self.processed_data.get('venue_records', pd.DataFrame())
        milestones = self.processed_data.get('milestones', {})

        # Count milestones
        milestone_counts = {}
        for key, df in milestones.items():
            if isinstance(df, pd.DataFrame):
                milestone_counts[key] = len(df)

        total_points = 0
        if not players.empty and 'Total PTS' in players.columns:
            total_points = int(players['Total PTS'].sum())

        # Count unique conferences seen
        from ..utils.constants import get_conference_for_date, DEFUNCT_TEAMS
        conferences_seen = set()
        for game in self.raw_games:
            basic_info = game.get('basic_info', {})
            date_str = basic_info.get('date_yyyymmdd', '')
            gender = basic_info.get('gender', 'M')
            away_team = basic_info.get('away_team', '')
            home_team = basic_info.get('home_team', '')
            if away_team:
                conf = get_conference_for_date(away_team, date_str, gender)
                if conf and conf not in ('Historical/Other', 'D3', 'D2', 'NAIA', 'Non-D1'):
                    conferences_seen.add(conf)
            if home_team:
                conf = get_conference_for_date(home_team, date_str, gender)
                if conf and conf not in ('Historical/Other', 'D3', 'D2', 'NAIA', 'Non-D1'):
                    conferences_seen.add(conf)

        # Count ranked games and upsets from raw games
        ranked_games = 0
        ranked_matchups = 0  # Both teams ranked
        upsets = 0

        for game in self.raw_games:
            basic_info = game.get('basic_info', {})
            away_rank = basic_info.get('away_rank')
            home_rank = basic_info.get('home_rank')
            away_score = basic_info.get('away_score', 0)
            home_score = basic_info.get('home_score', 0)

            if away_rank or home_rank:
                ranked_games += 1
                if away_rank and home_rank:
                    ranked_matchups += 1

                # Check for upset
                away_won = away_score > home_score
                away_rank_num = away_rank or 999
                home_rank_num = home_rank or 999

                if away_won and home_rank_num < away_rank_num:
                    upsets += 1  # Higher-ranked home team lost
                elif not away_won and away_rank_num < home_rank_num:
                    upsets += 1  # Higher-ranked away team lost

        return {
            'totalGames': len(game_log),
            'totalPlayers': len(players),
            'totalTeams': len(team_records),
            'totalVenues': len(venue_records),
            'totalPoints': total_points,
            'conferencesSeen': len(conferences_seen),
            'milestones': milestone_counts,
            'futurePros': 0,  # Will be calculated after players are serialized
            'rankedGames': ranked_games,
            'rankedMatchups': ranked_matchups,
            'upsets': upsets,
        }

    def _serialize_games(self) -> List[Dict]:
        """Serialize game log with linescore data, conferences, and AP rankings."""
        from ..utils.constants import get_conference_for_date

        game_log = self.processed_data.get('game_log', pd.DataFrame())
        if game_log.empty:
            return []

        games = self._df_to_records(game_log)

        # Add linescore, DateSort, conferences, and rankings from raw games
        raw_games_by_id = {g.get('game_id'): g for g in self.raw_games}
        for game in games:
            game_id = game.get('GameID')
            if game_id and game_id in raw_games_by_id:
                raw_game = raw_games_by_id[game_id]
                linescore = raw_game.get('linescore', {})
                if linescore:
                    game['Linescore'] = linescore
                # Add sortable date (YYYYMMDD format)
                basic_info = raw_game.get('basic_info', {})
                date_sort = basic_info.get('date_yyyymmdd', '')
                if date_sort:
                    game['DateSort'] = date_sort

                # Add AP rankings from cached game data
                if basic_info.get('away_rank'):
                    game['AwayRank'] = basic_info['away_rank']
                if basic_info.get('home_rank'):
                    game['HomeRank'] = basic_info['home_rank']

            # Add historical conference for each team based on game date
            date_sort = game.get('DateSort', '')
            gender = game.get('Gender', 'M')
            away_team = game.get('Away Team', '')
            home_team = game.get('Home Team', '')

            if date_sort and away_team:
                away_conf = get_conference_for_date(away_team, date_sort, gender)
                if away_conf:
                    game['AwayConf'] = away_conf

            if date_sort and home_team:
                home_conf = get_conference_for_date(home_team, date_sort, gender)
                if home_conf:
                    game['HomeConf'] = home_conf

        return games

    def _serialize_players(self) -> List[Dict]:
        """Serialize player statistics with NBA and international info."""
        players = self.processed_data.get('players', pd.DataFrame())
        if players.empty:
            return []

        records = self._df_to_records(players)

        # Batch fetch NBA/international status for all players
        skip_nba = getattr(self, '_skip_nba', False)
        player_ids = [r.get('Player ID', '') for r in records if r.get('Player ID')]
        # Use cache_only=-1 to skip new lookups but still use cached data
        pro_status = get_nba_status_batch(player_ids, max_fetch=-1 if skip_nba else 999)

        # Add NBA and International flags to each player
        for record in records:
            player_id = record.get('Player ID', '')
            pro_info = pro_status.get(player_id) if player_id else None
            if not pro_info and not skip_nba:
                pro_info = get_nba_player_info_by_id(player_id)

            # NBA info
            if pro_info and pro_info.get('nba_url'):
                record['NBA'] = True
                record['NBA_Played'] = pro_info.get('nba_played', True)  # Default true for backwards compat
                record['NBA_Active'] = pro_info.get('is_active', False)
                record['NBA_URL'] = pro_info.get('nba_url', '')
                if pro_info.get('nba_games') is not None:
                    record['NBA_Games'] = pro_info.get('nba_games')
            else:
                record['NBA'] = False

            # WNBA info (separate from NBA)
            if pro_info and pro_info.get('wnba_url'):
                record['WNBA'] = True
                record['WNBA_Played'] = pro_info.get('wnba_played', True)  # Default true for backwards compat
                record['WNBA_Active'] = pro_info.get('is_wnba_active', False)
                record['WNBA_URL'] = pro_info.get('wnba_url', '')
                if pro_info.get('wnba_games') is not None:
                    record['WNBA_Games'] = pro_info.get('wnba_games')
            else:
                record['WNBA'] = False

            # International info
            if pro_info and pro_info.get('intl_url'):
                record['International'] = True
                record['Intl_URL'] = pro_info.get('intl_url', '')
            else:
                record['International'] = False

            # Sports Reference page exists (False if 404)
            if pro_info and pro_info.get('sr_page_exists') is False:
                record['HasSportsRefPage'] = False
            else:
                record['HasSportsRefPage'] = True  # Default to true if unknown

        return records

    def _serialize_milestones(self) -> Dict[str, List[Dict]]:
        """Serialize all milestones."""
        milestones = self.processed_data.get('milestones', {})
        result = {}

        for key, df in milestones.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Select display columns
                display_cols = ['Date', 'Player', 'Player ID', 'Team', 'Opponent', 'Score', 'Detail', 'GameID']
                display_cols = [c for c in display_cols if c in df.columns]
                if display_cols:
                    result[key] = self._df_to_records(df[display_cols])
                else:
                    result[key] = self._df_to_records(df)
            else:
                result[key] = []

        return result

    def _serialize_teams(self) -> List[Dict]:
        """Serialize team records."""
        team_records = self.processed_data.get('team_records', pd.DataFrame())
        if team_records.empty:
            return []

        return self._df_to_records(team_records)

    def _serialize_venues(self) -> List[Dict]:
        """Serialize venue records."""
        venue_records = self.processed_data.get('venue_records', pd.DataFrame())
        if venue_records.empty:
            return []

        return self._df_to_records(venue_records)

    def _serialize_upcoming_games(self) -> Dict[str, Any]:
        """Serialize upcoming games at unvisited venues."""
        from ..utils.constants import get_conference_for_date

        # Get visited venues from games
        games_data = self._serialize_games()
        visited_venues = set()
        for game in games_data:
            venue = game.get('Venue', '')
            city = game.get('City', '')
            state = game.get('State', '')
            if venue and city and state:
                visited_venues.add(f"{venue}, {city}, {state}")

        # Try to load schedule
        if not SCHEDULE_CACHE_FILE.exists():
            return {'games': [], 'error': 'No schedule cache. Run schedule scraper first.'}

        try:
            schedule = get_schedule(force_refresh=False)
        except Exception as e:
            return {'games': [], 'error': str(e)}

        # Filter to upcoming games at unvisited venues
        upcoming = filter_upcoming_games(schedule, visited_venues)

        # Format for website
        formatted_games = []
        conferences = {}
        teams = {}

        # Non-D1 schools to filter out entirely
        NON_D1_SCHOOLS = {
            'Dakota St', 'Dakota State',  # NAIA
            'Davenport', 'Grand Canyon JV',
        }

        for game in upcoming:
            # Get team short names (cleaner than full names with mascots)
            home_name = game['home_team'].get('short_name') or game['home_team']['name']
            away_name = game['away_team'].get('short_name') or game['away_team']['name']

            # Skip games with non-D1 teams
            if home_name in NON_D1_SCHOOLS or away_name in NON_D1_SCHOOLS:
                continue

            # Look up conferences using our data
            home_conf = self._lookup_conference(home_name)
            away_conf = self._lookup_conference(away_name)

            state = normalize_state(game['venue']['state'])

            formatted_games.append({
                'date': game['date'],
                'dateDisplay': game['date_display'],
                'time_detail': game.get('time_detail', ''),  # ESPN's actual game time
                'homeTeam': home_name,
                'homeTeamFull': game['home_team']['name'],
                'homeTeamAbbrev': game['home_team']['abbreviation'],
                'homeConf': home_conf,
                'awayTeam': away_name,
                'awayTeamFull': game['away_team']['name'],
                'awayTeamAbbrev': game['away_team']['abbreviation'],
                'awayConf': away_conf,
                'venue': game['venue']['name'],
                'city': game['venue']['city'],
                'state': state,
                'tv': game.get('tv', []),
                'neutralSite': game.get('neutral_site', False),
                'conferenceGame': game.get('conference_game', False),
            })

            # Track conferences
            if home_conf:
                conferences[home_conf] = conferences.get(home_conf, 0) + 1
            if away_conf and away_conf != home_conf:
                conferences[away_conf] = conferences.get(away_conf, 0) + 1

            # Track teams
            teams[home_name] = teams.get(home_name, 0) + 1
            teams[away_name] = teams.get(away_name, 0) + 1

        # Group by state for filtering
        states = {}
        for game in formatted_games:
            state = game['state']
            if state not in states:
                states[state] = 0
            states[state] += 1

        # Format visited venues for map display with upcoming games
        visited_venues_list = []
        venues_seen = {}  # venue -> {city, state, pastGames, upcomingGames, homeTeam}
        for game in games_data:
            venue = game.get('Venue', '')
            city = game.get('City', '')
            state = game.get('State', '')
            home_team = game.get('Home Team', '')
            if venue and city and state:
                key = f"{venue}, {city}"
                if key not in venues_seen:
                    venues_seen[key] = {
                        'venue': venue,
                        'city': city,
                        'state': state,
                        'pastGames': 0,
                        'upcomingGames': [],
                        'homeTeam': home_team  # Track home team for coordinates
                    }
                venues_seen[key]['pastGames'] += 1
                # Update home team if we have one (prefer non-empty)
                if home_team and not venues_seen[key]['homeTeam']:
                    venues_seen[key]['homeTeam'] = home_team

        # Find upcoming games at visited venues from schedule
        from datetime import datetime
        now = datetime.now()
        for sched_game in schedule:
            try:
                game_date = datetime.fromisoformat(sched_game["date"].replace("Z", "+00:00"))
                if game_date.replace(tzinfo=None) < now:
                    continue  # Skip past games
            except (ValueError, AttributeError):
                continue

            espn_venue = sched_game.get("venue", {})
            venue_name = espn_venue.get("name", "")
            venue_city = espn_venue.get("city", "")
            venue_state = normalize_state(espn_venue.get("state", ""))

            # Venue name aliases (ESPN name -> our name variations)
            VENUE_ALIASES = {
                'global credit union arena': ['gcu arena', 'grand canyon arena'],
                'gcu arena': ['global credit union arena'],
            }

            # Check if this venue matches any visited venue
            for key, data in venues_seen.items():
                if data['city'].lower() == venue_city.lower() and data['state'].lower() == venue_state.lower():
                    # Same city/state - check venue name similarity
                    espn_lower = venue_name.lower()
                    our_lower = data['venue'].lower()

                    # Check aliases
                    alias_match = False
                    if espn_lower in VENUE_ALIASES:
                        alias_match = any(a in our_lower or our_lower in a for a in VENUE_ALIASES[espn_lower])
                    if our_lower in VENUE_ALIASES:
                        alias_match = alias_match or any(a in espn_lower or espn_lower in a for a in VENUE_ALIASES[our_lower])

                    if espn_lower == our_lower or alias_match or \
                       any(w in espn_lower for w in our_lower.split() if len(w) > 4):
                        home = sched_game['home_team'].get('short_name') or sched_game['home_team']['name']
                        away = sched_game['away_team'].get('short_name') or sched_game['away_team']['name']
                        data['upcomingGames'].append({
                            'date': sched_game['date'],
                            'time_detail': sched_game.get('time_detail', ''),
                            'home': home,
                            'away': away,
                            'tv': sched_game.get('tv', [])
                        })
                        break

        for data in venues_seen.values():
            # Sort upcoming games by date
            data['upcomingGames'].sort(key=lambda g: g['date'])
            visited_venues_list.append({
                'venue': data['venue'],
                'city': data['city'],
                'state': data['state'],
                'pastGames': data['pastGames'],
                'upcomingGames': data['upcomingGames'][:10],  # Limit to 10
                'homeTeam': data['homeTeam']  # For coordinate lookup
            })

        return {
            'games': formatted_games,
            'totalGames': len(formatted_games),
            'totalVenues': len(set(g['venue'] for g in formatted_games)),
            'stateBreakdown': states,
            'conferenceBreakdown': conferences,
            'teamBreakdown': teams,
            'visitedVenueCount': len(visited_venues),
            'visitedVenues': visited_venues_list,
        }

    def _lookup_conference(self, team_name: str) -> str:
        """Look up conference for a team using explicit mappings only."""
        from ..utils.constants import get_conference_for_date
        import datetime

        if not team_name:
            return ''

        # ESPN name -> our canonical name (explicit mappings only, no fuzzy matching)
        ESPN_TO_CANONICAL = {
            # Abbreviations
            'UConn': 'Connecticut',
            'UMass': 'Massachusetts',
            'UNLV': 'Nevada-Las Vegas',
            'VCU': 'Virginia Commonwealth',
            'UCF': 'Central Florida',
            'SMU': 'Southern Methodist',
            'LSU': 'Louisiana State',
            'BYU': 'Brigham Young',
            'TCU': 'Texas Christian',
            'USC': 'Southern California',
            'UCLA': 'UCLA',
            'UTEP': 'UTEP',
            'UTSA': 'Texas-San Antonio',
            'FGCU': 'Florida Gulf Coast',
            'FIU': 'Florida International',
            'FAU': 'Florida Atlantic',
            'UAB': 'UAB',
            'UIC': 'Illinois-Chicago',
            'IUPUI': 'IUPUI',
            'SIU': 'Southern Illinois',
            'NIU': 'Northern Illinois',
            'WKU': 'Western Kentucky',
            'ETSU': 'East Tennessee State',
            'MTSU': 'Middle Tennessee',
            'LIU': 'Long Island',
            'URI': 'Rhode Island',

            # Direction abbreviations
            'N Carolina': 'North Carolina',
            'S Carolina': 'South Carolina',
            'N Dakota': 'North Dakota',
            'S Dakota': 'South Dakota',
            'N Dakota St': 'North Dakota State',
            'S Dakota St': 'South Dakota State',
            'N Arizona': 'Northern Arizona',
            'N Colorado': 'Northern Colorado',
            'N Kentucky': 'Northern Kentucky',
            'N Iowa': 'Northern Iowa',
            'N Illinois': 'Northern Illinois',
            'N Texas': 'North Texas',
            'S Florida': 'South Florida',
            'S Alabama': 'South Alabama',
            'S Utah': 'Southern Utah',
            'S Illinois': 'Southern Illinois',
            'W Virginia': 'West Virginia',
            'W Kentucky': 'Western Kentucky',
            'W Michigan': 'Western Michigan',
            'W Illinois': 'Western Illinois',
            'E Kentucky': 'Eastern Kentucky',
            'E Michigan': 'Eastern Michigan',
            'E Illinois': 'Eastern Illinois',
            'E Washington': 'Eastern Washington',
            'E Tennessee St': 'East Tennessee State',
            'SE Missouri St': 'Southeast Missouri State',
            'SE Louisiana': 'Southeastern Louisiana',
            'NW State': 'Northwestern State',

            # State abbreviations
            'Miss State': 'Mississippi State',
            'Ariz State': 'Arizona State',
            'Ore State': 'Oregon State',
            'Wash State': 'Washington State',
            'Penn State': 'Penn State',
            'Mich State': 'Michigan State',
            'Ohio State': 'Ohio State',
            'Iowa State': 'Iowa State',
            'Ball State': 'Ball State',
            'Boise State': 'Boise State',
            'Fresno State': 'Fresno State',

            # "St" suffix -> "State"
            'Alabama St': 'Alabama State',
            'Alcorn St': 'Alcorn State',
            'Appalachian St': 'Appalachian State',
            'Arizona St': 'Arizona State',
            'Arkansas St': 'Arkansas State',
            'Ball St': 'Ball State',
            'Boise St': 'Boise State',
            'Bowling Green St': 'Bowling Green',
            'Chicago St': 'Chicago State',
            'Cleveland St': 'Cleveland State',
            'Colorado St': 'Colorado State',
            'Coppin St': 'Coppin State',
            'Delaware St': 'Delaware State',
            'Fresno St': 'Fresno State',
            'Georgia St': 'Georgia State',
            'Grambling St': 'Grambling State',
            'Idaho St': 'Idaho State',
            'Illinois St': 'Illinois State',
            'Indiana St': 'Indiana State',
            'Iowa St': 'Iowa State',
            'Jackson St': 'Jackson State',
            'Jacksonville St': 'Jacksonville State',
            'Kansas St': 'Kansas State',
            'Kennesaw St': 'Kennesaw State',
            'Kent St': 'Kent State',
            'McNeese St': 'McNeese State',
            'Memphis St': 'Memphis',
            'Michigan St': 'Michigan State',
            'Mississippi St': 'Mississippi State',
            'Missouri St': 'Missouri State',
            'Montana St': 'Montana State',
            'Morehead St': 'Morehead State',
            'Morgan St': 'Morgan State',
            'Murray St': 'Murray State',
            'NC St': 'NC State',
            'New Mexico St': 'New Mexico State',
            'Norfolk St': 'Norfolk State',
            'Ohio St': 'Ohio State',
            'Oklahoma St': 'Oklahoma State',
            'Oregon St': 'Oregon State',
            'Penn St': 'Penn State',
            'Pittsburgh St': 'Pittsburg State',
            'Portland St': 'Portland State',
            'Prairie View St': 'Prairie View A&M',
            'Sacramento St': 'Sacramento State',
            'Sam Houston St': 'Sam Houston State',
            'San Diego St': 'San Diego State',
            'San Jose St': 'San Jose State',
            'Savannah St': 'Savannah State',
            'South Carolina St': 'South Carolina State',
            'Stephen F. Austin St': 'Stephen F. Austin',
            'Tennessee St': 'Tennessee State',
            'Texas St': 'Texas State',
            'Texas Southern St': 'Texas Southern',
            'Troy St': 'Troy',
            'Utah St': 'Utah State',
            'Valdosta St': 'Valdosta State',
            'Washington St': 'Washington State',
            'Weber St': 'Weber State',
            'Wichita St': 'Wichita State',
            'Wright St': 'Wright State',
            'Youngstown St': 'Youngstown State',

            # "St" prefix -> "Saint" or "St."
            'St Bonaventure': 'St. Bonaventure',
            "St John's": "St. John's",
            "St Joseph's": "Saint Joseph's",
            'St Louis': 'Saint Louis',
            "St Mary's": "Saint Mary's (CA)",
            "St Peter's": "Saint Peter's",
            'St Thomas': 'St. Thomas',
            'St Thomas (MN)': 'St. Thomas',

            # CSU variations
            'CSU Bakersfield': 'Cal State Bakersfield',
            'CSU Fullerton': 'Cal State Fullerton',
            'CSU Northridge': 'Cal State Northridge',
            'Long Beach St': 'Long Beach State',
            'Cal Poly': 'Cal Poly',
            'Cal Baptist': 'California Baptist',

            # Common nicknames
            'App State': 'Appalachian State',
            'G Washington': 'George Washington',
            'Ole Miss': 'Mississippi',
            'Pitt': 'Pittsburgh',
            'Miami': 'Miami (FL)',
            'Miami (FL)': 'Miami (FL)',
            'Miami (OH)': 'Miami (OH)',
            'UNC': 'North Carolina',
            'NC A&T': 'North Carolina A&T',
            'NC Central': 'North Carolina Central',
            'A&M-Corpus Christi': 'Texas A&M-Corpus Christi',

            # UMES/Maryland schools
            'UMES': 'Maryland-Eastern Shore',
            'MD Eastern': 'Maryland-Eastern Shore',
            'UMBC': 'UMBC',
            'Loyola MD': 'Loyola (MD)',
            'Loyola Chi': 'Loyola Chicago',
            'Loyola Marymount': 'Loyola Marymount',

            # Hawaii
            "Hawai'i": 'Hawaii',
            "Hawai\u2019i": 'Hawaii',  # ESPN right single quotation

            # Other ESPN variations
            'Southern Miss': 'Southern Miss',
            'Little Rock': 'Arkansas-Little Rock',
            'UCSB': 'UC Santa Barbara',
            'UCD': 'UC Davis',
            'UCR': 'UC Riverside',
            'UCSD': 'UC San Diego',
            'UC Irvine': 'UC Irvine',
            'SFA': 'Stephen F. Austin',
            'Omaha': 'Nebraska-Omaha',
            'UNO': 'New Orleans',
            'UNI': 'Northern Iowa',
            'Loyola-Chicago': 'Loyola Chicago',
            'UL Monroe': 'Louisiana-Monroe',
            'UL Lafayette': 'Louisiana',
            'Purdue Fort Wayne': 'Purdue Fort Wayne',
            'IU Indianapolis': 'Indiana-Purdue Indianapolis',
        }

        # Non-D1 schools to skip (ESPN sometimes includes these incorrectly)
        NON_D1_SCHOOLS = {
            'Dakota St', 'Dakota State',  # NAIA
            'Davenport', 'Grand Canyon JV',
        }

        # Check if team should be skipped
        if team_name in NON_D1_SCHOOLS:
            return ''

        # Normalize Unicode
        normalized = team_name.replace(''', "'").replace(''', "'").replace('é', 'e').replace('ñ', 'n')

        # Try explicit ESPN mapping first
        if normalized in ESPN_TO_CANONICAL:
            canonical = ESPN_TO_CANONICAL[normalized]
            conf = get_conference_for_date(canonical, datetime.datetime.now().strftime('%Y%m%d'), 'M')
            if conf and conf not in ('Historical/Other', 'D3', 'D2', 'NAIA', 'Non-D1'):
                return conf

        # Try direct lookup with original name
        conf = get_conference_for_date(normalized, datetime.datetime.now().strftime('%Y%m%d'), 'M')
        if conf and conf not in ('Historical/Other', 'D3', 'D2', 'NAIA', 'Non-D1'):
            return conf

        # No match found - return empty (don't guess)
        return ''

    def _serialize_player_games(self) -> List[Dict]:
        """Serialize per-game player stats."""
        player_games = self.processed_data.get('player_games', pd.DataFrame())
        if player_games.empty:
            return []

        return self._df_to_records(player_games)

    def _df_to_records(self, df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame to list of records, handling NaN values."""
        if df.empty:
            return []

        # Replace NaN with None for JSON serialization
        df = df.fillna('')

        records = df.to_dict('records')

        # Columns that contain team names to normalize
        team_columns = {'Team', 'Away Team', 'Home Team', 'Opponent'}

        # Clean up records
        cleaned = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Convert numpy types to Python types
                if hasattr(value, 'item'):
                    value = value.item()
                # Handle empty strings from fillna
                if value == '':
                    value = None
                # Normalize team names (UNC -> North Carolina, etc.)
                elif key in team_columns and isinstance(value, str):
                    value = normalize_team_name(value)
                cleaned_record[key] = value
            cleaned.append(cleaned_record)

        return cleaned

    def _serialize_starters_bench(self) -> List[Dict]:
        """Serialize starters vs bench splits."""
        df = self.processed_data.get('starters_vs_bench', pd.DataFrame())
        if df.empty:
            return []
        return self._df_to_records(df)

    def _serialize_season_highs(self) -> List[Dict]:
        """Serialize season highs."""
        df = self.processed_data.get('season_highs', pd.DataFrame())
        if df.empty:
            return []
        return self._df_to_records(df)

    def _serialize_team_streaks(self) -> List[Dict]:
        """Serialize team streaks."""
        df = self.processed_data.get('team_streaks', pd.DataFrame())
        if df.empty:
            return []
        return self._df_to_records(df)

    def _serialize_head_to_head(self) -> List[Dict]:
        """Serialize head-to-head history."""
        df = self.processed_data.get('head_to_head', pd.DataFrame())
        if df.empty:
            return []
        return self._df_to_records(df)

    def _serialize_conference_standings(self) -> List[Dict]:
        """Serialize conference standings."""
        df = self.processed_data.get('conference_standings', pd.DataFrame())
        if df.empty:
            return []
        return self._df_to_records(df)

    def _serialize_home_away_splits(self) -> List[Dict]:
        """Serialize home/away splits."""
        df = self.processed_data.get('home_away_splits', pd.DataFrame())
        if df.empty:
            return []
        return self._df_to_records(df)

    def _serialize_attendance_stats(self) -> List[Dict]:
        """Serialize attendance statistics."""
        df = self.processed_data.get('attendance_stats', pd.DataFrame())
        if df.empty:
            return []
        return self._df_to_records(df)

    def _serialize_conference_checklist(self) -> Dict[str, Any]:
        """Serialize conference checklist data - teams and venues seen per conference."""
        from ..utils.constants import CONFERENCES, TEAM_ALIASES, DEFUNCT_TEAMS
        from ..utils.venue_resolver import get_venue_resolver, parse_venue_components

        game_log = self.processed_data.get('game_log', pd.DataFrame())
        venue_resolver = get_venue_resolver()

        # Get teams and venues seen BY GENDER
        seen_teams_by_gender = {'M': set(), 'W': set(), 'all': set()}
        seen_venues_by_gender = {'M': set(), 'W': set(), 'all': set()}

        if not game_log.empty:
            for _, row in game_log.iterrows():
                gender = row.get('Gender', 'M') or 'M'
                away = row.get('Away Team')
                home = row.get('Home Team')
                venue = row.get('Venue')

                if away:
                    seen_teams_by_gender[gender].add(away)
                    seen_teams_by_gender['all'].add(away)
                if home:
                    seen_teams_by_gender[gender].add(home)
                    seen_teams_by_gender['all'].add(home)
                if venue:
                    seen_venues_by_gender[gender].add(venue)
                    seen_venues_by_gender['all'].add(venue)

        # Build reverse alias map (canonical -> [aliases])
        reverse_aliases = {}
        for alias, canonical in TEAM_ALIASES.items():
            if canonical not in reverse_aliases:
                reverse_aliases[canonical] = []
            reverse_aliases[canonical].append(alias)

        def team_seen(team_name: str, seen_teams: set) -> bool:
            """Check if a team has been seen, accounting for aliases."""
            # Direct match
            if team_name in seen_teams:
                return True
            # Check if any alias of this team was seen
            aliases = reverse_aliases.get(team_name, [])
            for alias in aliases:
                if alias in seen_teams:
                    return True
            # Check if this team is an alias and the canonical name was seen
            canonical = TEAM_ALIASES.get(team_name)
            if canonical and canonical in seen_teams:
                return True
            return False

        def arena_visited(home_arena: str, seen_venues: set) -> bool:
            """Check if home arena has been visited."""
            if not home_arena:
                return False
            # Parse the home arena to get just the name
            arena_name = parse_venue_components(home_arena)['name']
            # Check if the arena name matches any seen venue exactly
            if arena_name in seen_venues:
                return True

            # Get venue aliases from venue resolver
            venue_aliases = venue_resolver.get_venue_aliases()
            # Build reverse alias map (new name -> [old names])
            reverse_venue_aliases = {}
            for old_name, new_name in venue_aliases.items():
                if new_name not in reverse_venue_aliases:
                    reverse_venue_aliases[new_name] = []
                reverse_venue_aliases[new_name].append(old_name)

            # Check if any old name (alias) of this arena was visited
            old_names = reverse_venue_aliases.get(arena_name, [])
            for old_name in old_names:
                if old_name in seen_venues:
                    return True

            # Check for exact match (case insensitive only)
            arena_lower = arena_name.lower().strip()
            for venue in seen_venues:
                venue_lower = venue.lower().strip()
                # Exact match (case insensitive)
                if arena_lower == venue_lower:
                    return True
                # Check aliases case-insensitive
                for old_name in old_names:
                    if old_name.lower().strip() == venue_lower:
                        return True
            # No fuzzy matching - too many false positives
            return False

        # Build checklist for each conference
        checklist = {}
        all_d1_teams = []  # For "All D1" option
        all_conference_teams = set()  # Track all teams in conferences

        # Skip non-D1 conferences
        skip_conferences = {'D3', 'D2', 'NAIA', 'Non-D1'}

        for conf_name, conf_teams in CONFERENCES.items():
            if conf_name in skip_conferences:
                continue
            teams_data = []
            for team in sorted(conf_teams):
                # Skip defunct teams - they count for badges but not checklist
                if team in DEFUNCT_TEAMS:
                    continue
                all_conference_teams.add(team)
                # Also add aliases to the set
                aliases = reverse_aliases.get(team, [])
                all_conference_teams.update(aliases)
                canonical = TEAM_ALIASES.get(team)
                if canonical:
                    all_conference_teams.add(canonical)

                # Get gender-specific arenas
                home_arena_m = venue_resolver.get_home_arena(team, 'M')
                home_arena_w = venue_resolver.get_home_arena(team, 'W')
                arena_name_m = parse_venue_components(home_arena_m)['name'] if home_arena_m else 'Unknown'
                arena_name_w = parse_venue_components(home_arena_w)['name'] if home_arena_w else 'Unknown'

                team_data = {
                    'team': team,
                    'seen': team_seen(team, seen_teams_by_gender['all']),
                    'seenM': team_seen(team, seen_teams_by_gender['M']),
                    'seenW': team_seen(team, seen_teams_by_gender['W']),
                    'homeArena': arena_name_m,  # Default to men's
                    'homeArenaM': arena_name_m,
                    'homeArenaW': arena_name_w,
                    'arenaVisited': arena_visited(home_arena_m, seen_venues_by_gender['all']),
                    'arenaVisitedM': arena_visited(home_arena_m, seen_venues_by_gender['M']),
                    'arenaVisitedW': arena_visited(home_arena_w, seen_venues_by_gender['W']),
                    'conference': conf_name,
                    'espnId': get_espn_team_id(team)
                }
                teams_data.append(team_data)
                all_d1_teams.append(team_data)

            checklist[conf_name] = {
                'teams': teams_data,
                'teamsSeen': sum(1 for t in teams_data if t['seen']),
                'teamsSeenM': sum(1 for t in teams_data if t['seenM']),
                'teamsSeenW': sum(1 for t in teams_data if t['seenW']),
                'totalTeams': len(teams_data),
                'venuesVisited': sum(1 for t in teams_data if t['arenaVisited']),
                'venuesVisitedM': sum(1 for t in teams_data if t['arenaVisitedM']),
                'venuesVisitedW': sum(1 for t in teams_data if t['arenaVisitedW']),
                'totalVenues': sum(1 for t in teams_data if t['homeArenaM'] != 'Unknown')
            }

        # Add "All D1" option
        all_d1_teams_sorted = sorted(all_d1_teams, key=lambda x: x['team'])
        checklist['All D1'] = {
            'teams': all_d1_teams_sorted,
            'teamsSeen': sum(1 for t in all_d1_teams_sorted if t['seen']),
            'teamsSeenM': sum(1 for t in all_d1_teams_sorted if t['seenM']),
            'teamsSeenW': sum(1 for t in all_d1_teams_sorted if t['seenW']),
            'totalTeams': len(all_d1_teams_sorted),
            'venuesVisited': sum(1 for t in all_d1_teams_sorted if t['arenaVisited']),
            'venuesVisitedM': sum(1 for t in all_d1_teams_sorted if t['arenaVisitedM']),
            'venuesVisitedW': sum(1 for t in all_d1_teams_sorted if t['arenaVisitedW']),
            'totalVenues': sum(1 for t in all_d1_teams_sorted if t['homeArenaM'] != 'Unknown')
        }

        # Find historical/other teams (seen but not in any current conference)
        historical_teams = []
        for team in seen_teams_by_gender['all']:
            # Check if this team is in any conference (directly or via alias)
            in_conference = team in all_conference_teams
            if not in_conference:
                # Not in a conference - it's historical/other
                home_arena = venue_resolver.get_home_arena(team)
                arena_name = parse_venue_components(home_arena)['name'] if home_arena else 'Unknown'
                historical_teams.append({
                    'team': team,
                    'seen': True,
                    'seenM': team in seen_teams_by_gender['M'],
                    'seenW': team in seen_teams_by_gender['W'],
                    'homeArena': arena_name,
                    'homeArenaM': arena_name,
                    'homeArenaW': arena_name,
                    'arenaVisited': arena_visited(home_arena, seen_venues_by_gender['all']),
                    'arenaVisitedM': arena_visited(home_arena, seen_venues_by_gender['M']),
                    'arenaVisitedW': arena_visited(home_arena, seen_venues_by_gender['W']),
                    'conference': 'Historical/Other',
                    'espnId': get_espn_team_id(team)
                })

        if historical_teams:
            historical_teams_sorted = sorted(historical_teams, key=lambda x: x['team'])
            checklist['Historical/Other'] = {
                'teams': historical_teams_sorted,
                'teamsSeen': len(historical_teams_sorted),
                'teamsSeenM': sum(1 for t in historical_teams_sorted if t['seenM']),
                'teamsSeenW': sum(1 for t in historical_teams_sorted if t['seenW']),
                'totalTeams': len(historical_teams_sorted),
                'venuesVisited': sum(1 for t in historical_teams_sorted if t['arenaVisited']),
                'venuesVisitedM': sum(1 for t in historical_teams_sorted if t['arenaVisitedM']),
                'venuesVisitedW': sum(1 for t in historical_teams_sorted if t['arenaVisitedW']),
                'totalVenues': sum(1 for t in historical_teams_sorted if t['homeArena'] != 'Unknown')
            }

        return checklist


def serialize_to_json(processed_data: Dict[str, Any], raw_games: List[Dict] = None) -> str:
    """
    Serialize all data to JSON string.

    Args:
        processed_data: Dictionary of processed DataFrames
        raw_games: Optional raw game data

    Returns:
        JSON string
    """
    serializer = DataSerializer(processed_data, raw_games)
    data = serializer.serialize_all()
    return json.dumps(data, indent=2, default=str)
