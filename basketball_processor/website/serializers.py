"""
Data serializers for website JSON generation.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import json

from ..utils.nba_players import (
    get_nba_player_info_by_id, get_nba_status_batch, recheck_female_players_for_wnba,
    check_proballers_for_all_players
)
from ..utils.d2d3_scraper import enrich_player_with_realgm, lookup_player_transfers
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
        self._games_cache = None  # Cache for serialized games

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

        # Auto-refresh AP polls if needed (weekly during season)
        try:
            from ..scrapers.poll_scraper import auto_refresh_polls_if_needed
            auto_refresh_polls_if_needed(silent=False)
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

        # Import TEAM_ALIASES for JavaScript use
        from ..utils.constants import TEAM_ALIASES

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
            'teamAliases': TEAM_ALIASES,
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
        # Return cached result if available
        if self._games_cache is not None:
            return self._games_cache

        from ..utils.constants import get_conference_for_date

        game_log = self.processed_data.get('game_log', pd.DataFrame())
        if game_log.empty:
            return []

        games = self._df_to_records(game_log)

        # Add linescore, officials, DateSort, conferences, and rankings from raw games
        raw_games_by_id = {g.get('game_id'): g for g in self.raw_games}
        for game in games:
            game_id = game.get('GameID')
            if game_id and game_id in raw_games_by_id:
                raw_game = raw_games_by_id[game_id]
                linescore = raw_game.get('linescore', {})
                if linescore:
                    game['Linescore'] = linescore
                # Add officials/referees
                officials = raw_game.get('officials', [])
                if officials:
                    game['Officials'] = officials
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

                # Add play-by-play analysis if available
                pbp_data = raw_game.get('play_by_play', {})
                if pbp_data:
                    # Include summary stats, not the full play list (too large)
                    game['PlayByPlay'] = {
                        'leadChanges': pbp_data.get('lead_changes', 0),
                        'largestLeads': pbp_data.get('largest_leads', {}),
                        'scoringRuns': pbp_data.get('scoring_runs', []),
                        'totalPlays': len(pbp_data.get('plays', [])),
                    }

                # Add ESPN play-by-play analysis if available
                espn_pbp = raw_game.get('espn_pbp_analysis', {})
                if espn_pbp:
                    away_team = game.get('Away Team', '')
                    home_team = game.get('Home Team', '')
                    game['ESPNPBPAnalysis'] = self._serialize_espn_pbp_analysis(
                        espn_pbp, away_team=away_team, home_team=home_team
                    )

                # Add neutral site flag if available
                if basic_info.get('neutral_site'):
                    game['NeutralSite'] = True

            # Known neutral site venues - always mark as neutral regardless of ESPN data
            KNOWN_NEUTRAL_VENUES = {
                # NBA arenas commonly used for college games
                'chase center',
                'barclays center',
                'madison square garden',
                'united center',
                't-mobile arena',
                'mgm grand garden arena',
                'staples center',
                'crypto.com arena',
                'footprint center',
                'state farm arena',
                'spectrum center',
                'smoothie king center',
                'capital one arena',
                'little caesars arena',
                'wells fargo center',
                'prudential center',
                'mohegan sun arena',
                'td garden',
                'american airlines center',
                'toyota center',
                'ball arena',
                'golden 1 center',
                'kia center',
                'amway center',
                'paycom center',
                'frost bank center',
                'kaseya center',
                'gainbridge fieldhouse',
                'target center',
                'delta center',
                'moda center',
            }
            venue = game.get('Venue', '').lower().strip()
            if venue and any(nv in venue for nv in KNOWN_NEUTRAL_VENUES):
                game['NeutralSite'] = True

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

        # Fetch game times from ESPN for dates with multiple games
        self._add_game_times_from_espn(games)

        # Cache the result
        self._games_cache = games
        return games

    def _add_game_times_from_espn(self, games: List[Dict]) -> None:
        """Add game times from ESPN for dates with multiple games."""
        from ..utils.schedule_scraper import get_game_times_for_date
        from collections import defaultdict

        # Group games by date
        games_by_date = defaultdict(list)
        for game in games:
            date_sort = game.get('DateSort', '')
            if date_sort:
                games_by_date[date_sort].append(game)

        # Only fetch times for dates with multiple games
        dates_needing_times = [d for d, g in games_by_date.items() if len(g) > 1]

        if not dates_needing_times:
            return

        print(f"  Loading game times for {len(dates_needing_times)} dates (from cache or ESPN)...")

        for date_str in dates_needing_times:
            # Fetch men's and women's times separately to avoid cross-matching
            espn_times_m = get_game_times_for_date(date_str, gender='M', verbose=True)
            espn_times_w = get_game_times_for_date(date_str, gender='W', verbose=True)

            # Match games to ESPN times based on game gender
            for game in games_by_date[date_str]:
                away_team = game.get('Away Team', '')
                home_team = game.get('Home Team', '')
                game_gender = game.get('Gender', 'M')

                # Use the appropriate ESPN times based on game gender
                espn_times = espn_times_w if game_gender == 'W' else espn_times_m
                if not espn_times:
                    continue

                # Try to find matching ESPN game
                for espn_key, espn_time in espn_times.items():
                    espn_away, espn_home = espn_key.split('|')

                    # Fuzzy match team names
                    away_match = self._teams_match(away_team, espn_away)
                    home_match = self._teams_match(home_team, espn_home)

                    if away_match and home_match:
                        game['TimeSort'] = espn_time
                        break

    def _teams_match(self, team1: str, team2: str) -> bool:
        """Check if two team names likely refer to the same team."""
        from ..utils.constants import TEAM_ALIASES

        def normalize(name: str) -> str:
            # Remove common suffixes like Bulldogs, Bears, etc.
            n = name.lower().replace("'", "").replace(".", "").replace("-", " ").replace("(", "").replace(")", "").strip()
            # Remove team nickname suffixes (common ESPN format)
            # Try to strip any "Lady X" or common nickname pattern
            import re
            # First try to remove "Lady <nickname>" pattern
            lady_match = re.match(r'^(.+?)\s+lady\s+\w+$', n)
            if lady_match:
                return lady_match.group(1).strip()

            # Comprehensive list of D1 college basketball team nicknames
            # Includes men's and women's variants (cowboys/cowgirls, etc.)
            suffixes = [
                # A
                'aces', 'aggies', 'anteaters', 'antelopes', 'aztecs',
                # B
                'badgers', 'banana slugs', 'battlin bears', 'beach', 'bearcats', 'bears',
                'beavers', 'bengals', 'bighornz', 'billikens', 'bison', 'black bears',
                'black knights', 'blazers', 'blue demons', 'blue devils', 'blue hens',
                'blue jays', 'blue raiders', 'bluejays', 'bobcats', 'boilermakers',
                'bonnies', 'braves', 'broncos', 'bruins', 'buckeyes', 'buffaloes',
                'buffs', 'bulldogs', 'bulls',
                # C
                'camels', 'cardinals', 'catamounts', 'cavaliers', 'chanticleers',
                'chippewas', 'citadel', 'clan', 'cobras', 'colonels', 'commodores',
                'cornhuskers', 'cougars', 'cowboys', 'cowgirls', 'coyotes', 'crimson',
                'crimson tide', 'crusaders', 'cyclones',
                # D
                'darters', 'demon deacons', 'demons', 'dolphins', 'dons', 'dragons',
                'ducks', 'dukes', 'dustdevils',
                # E
                'eagles', 'engineers', 'explorers',
                # F
                'falcons', 'fighting camels', 'fighting hawks', 'fighting illini',
                'fighting irish', 'flames', 'flashes', 'flyers', 'friars',
                # G
                'gaels', 'gators', 'golden bears', 'golden eagles', 'golden flashes',
                'golden gophers', 'golden griffins', 'golden grizzlies', 'golden hurricane',
                'golden knights', 'golden panthers', 'gophers', 'gorillas', 'governors',
                'govs', 'great danes', 'green wave', 'greyhounds', 'griffins', 'grizzlies',
                # H
                'hatters', 'hawkeyes', 'hawks', 'highlanders', 'hilltoppers', 'hokies',
                'hoosiers', 'hornets', 'horned frogs', 'hoyas', 'huskies', 'hurricanes',
                # I
                'ichabods', 'illini', 'indians',
                # J
                'jackrabbits', 'jacks', 'jaguars', 'jaspers', 'javelinas', 'jayhawks', 'jets',
                # K
                'kangaroos', 'keydets', 'kingsmen', 'knights',
                # L
                'lancers', 'leathernecks', 'leopards', 'lions', 'lobos', 'longhorns', 'lopes', 'lumberjacks',
                # M
                'mad ants', 'mavericks', 'mean green', 'midshipmen', 'miners', 'mocs',
                'mocassins', 'monarchs', 'mountaineers', 'musketeers', 'mustangs',
                # N
                'nittany lions',
                # O
                'ospreys', 'orange', 'orangemen', 'owls',
                # P
                'paladins', 'panthers', 'patriots', 'peacocks', 'pelicans', 'penguins',
                'phoenix', 'pilots', 'pioneers', 'pirates', 'privateers', 'purple aces',
                'purple eagles',
                # Q-R
                'quakers', 'racers', 'ragin cajuns', 'raiders', 'rainbow wahine',
                'rainbow warriors', 'rams', 'rattlers', 'razorbacks', 'rebels',
                'red flash', 'red foxes', 'red hawks', 'red raiders', 'red storm',
                'red wolves', 'redhawks', 'redbirds', 'retrievers', 'riverhawks',
                'roadrunners', 'rockets', 'runnin bulldogs', 'running rebels',
                # S
                'saints', 'salukis', 'samurai', 'scarlet knights', 'scots', 'seahawks',
                'seawolves', 'seminoles', 'shockers', 'skyhawks', 'sooners', 'spartans',
                'spiders', 'stags', 'statesmen', 'stormy petrels', 'sun devils',
                'sycamores',
                # T
                'tar heels', 'terrapins', 'terriers', 'thunderbirds', 'thundering herd',
                'tides', 'tigers', 'titans', 'tomcats', 'toppers', 'toreadors', 'toreros',
                'tribe', 'tritons', 'trojans', 'tritons',
                # U-V
                'utes', 'vandals', 'vikings', 'vixens', 'vols', 'volunteers',
                # W
                'wahoos', 'war hawks', 'warhawks', 'warriors', 'wasps', 'wave',
                'westerners', 'wildcats', 'wolf pack', 'wolfpack', 'wolverines', 'wolves',
                # Y-Z
                'yellow jackets', 'zags', 'zips',
            ]
            for suffix in suffixes:
                if n.endswith(' ' + suffix):
                    n = n[:-len(suffix)-1].strip()
                    break
            return n

        t1 = normalize(team1)
        t2 = normalize(team2)

        # Direct match after normalization (this handles ESPN suffix removal)
        if t1 == t2:
            return True

        # Check exact alias matches
        # Build equivalence sets from aliases
        t1_equivalents = {t1}
        t2_equivalents = {t2}

        for alias, target in TEAM_ALIASES.items():
            alias_norm = normalize(alias)
            target_norm = normalize(target)
            # If t1 matches alias or target exactly, add both to equivalents
            if t1 == alias_norm or t1 == target_norm:
                t1_equivalents.add(alias_norm)
                t1_equivalents.add(target_norm)
            # Same for t2
            if t2 == alias_norm or t2 == target_norm:
                t2_equivalents.add(alias_norm)
                t2_equivalents.add(target_norm)

        # Check if equivalence sets overlap
        if t1_equivalents & t2_equivalents:
            return True

        return False

    def _serialize_players(self) -> List[Dict]:
        """Serialize player statistics with NBA and international info."""
        players = self.processed_data.get('players', pd.DataFrame())
        if players.empty:
            return []

        records = self._df_to_records(players)

        # Batch fetch NBA/international status
        # - Male players: check cache + fetch new (up to 999)
        # - Female players: cache-only (WNBA checked separately via recheck_female_players_for_wnba)
        skip_nba = getattr(self, '_skip_nba', False)
        male_player_ids = [r.get('Player ID', '') for r in records if r.get('Player ID') and r.get('Gender') == 'M']
        female_player_ids = [r.get('Player ID', '') for r in records if r.get('Player ID') and r.get('Gender') == 'W']

        # Get male players (may fetch new)
        pro_status = get_nba_status_batch(male_player_ids, max_fetch=-1 if skip_nba else 999)
        # Get female players from cache only (no new fetches - handled by recheck_female_players_for_wnba)
        if female_player_ids:
            female_pro_status = get_nba_status_batch(female_player_ids, max_fetch=-1)
            pro_status.update(female_pro_status)

        # Check Proballers for additional international league data (men only)
        if not skip_nba and male_player_ids:
            # Get player years from raw game data for disambiguation
            player_years = {}
            for game in self.raw_games:
                date = game.get('basic_info', {}).get('date_yyyymmdd', '')
                if date:
                    year = int(date[:4])
                    month = int(date[4:6])
                    # Basketball season year: Nov-Dec = next year's season
                    season_year = year + 1 if month >= 11 else year

                    for side in ['away', 'home']:
                        box = game.get('box_score', {}).get(side, {}).get('basic', [])
                        for p in box:
                            pid = p.get('player_id')
                            if pid:
                                if pid not in player_years:
                                    player_years[pid] = set()
                                player_years[pid].add(season_year)

            male_records = [r for r in records if r.get('Gender') == 'M']
            proballers_players = []
            for r in male_records:
                player_id = r.get('Player ID', '')
                name = r.get('Player', '')
                # Get first team (primary team) - Team field may have multiple comma-separated
                team = r.get('Team', '').split(',')[0].strip()
                # Get most recent year for this player
                years = player_years.get(player_id, set())
                year = max(years) if years else None
                if player_id and name and team:
                    proballers_players.append({
                        'player_id': player_id,
                        'name': name,
                        'college_team': team,
                        'year': year
                    })
            if proballers_players:
                check_proballers_for_all_players(proballers_players)
                # Refresh pro_status to include Proballers data
                pro_status = get_nba_status_batch(male_player_ids, max_fetch=-1)

        # Add NBA and International flags to each player
        for record in records:
            player_id = record.get('Player ID', '')
            is_male = record.get('Gender') == 'M'
            pro_info = pro_status.get(player_id) if player_id else None
            # Only fetch NBA status for male players (females checked via recheck_female_players_for_wnba)
            if not pro_info and not skip_nba and is_male:
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

            # International info - check intl_url (from BR) or intl_pro/intl_leagues (from Proballers)
            if pro_info and (pro_info.get('intl_url') or pro_info.get('intl_pro') or pro_info.get('intl_leagues')):
                record['International'] = True
                record['Intl_URL'] = pro_info.get('intl_url', '')
                # Proballers URL as fallback for players not in BR
                proballers_id = pro_info.get('proballers_id')
                if proballers_id:
                    record['Proballers_URL'] = f'https://www.proballers.com/basketball/player/{proballers_id}/'
                else:
                    record['Proballers_URL'] = ''
                # Separate flags for pro leagues vs national team tournaments
                record['Intl_Pro'] = pro_info.get('intl_pro', False)
                record['Intl_National_Team'] = pro_info.get('intl_national_team', False)
                # Specific league/tournament names
                record['Intl_Leagues'] = pro_info.get('intl_leagues', [])
                record['Intl_Tournaments'] = pro_info.get('intl_tournaments', [])
            else:
                record['International'] = False
                record['Intl_Pro'] = False
                record['Intl_National_Team'] = False
                record['Intl_Leagues'] = []
                record['Intl_Tournaments'] = []
                record['Proballers_URL'] = ''

            # Sports Reference page exists (False if 404 or non-D1 only player)
            # Sports Reference only covers D1 players
            divisions_str = record.get('Divisions', 'D1')
            player_divisions = {d.strip() for d in divisions_str.split(',')} if divisions_str else {'D1'}
            # Player has no D1 games - they won't be on Sports Reference
            has_d1_games = 'D1' in player_divisions
            if not has_d1_games:
                record['HasSportsRefPage'] = False
            elif pro_info and pro_info.get('sr_page_exists') is False:
                record['HasSportsRefPage'] = False
            else:
                record['HasSportsRefPage'] = True  # Default to true if unknown

            # RealGM data for transfer history and non-D1 players
            player_name = record.get('Player', '')
            current_school = record.get('Team', '').split(',')[0].strip()
            realgm_data = enrich_player_with_realgm(player_name, current_school)

            # Add RealGM URL (especially useful for non-D1 players without SR pages)
            if realgm_data.get('realgm_url'):
                record['RealGM_URL'] = realgm_data['realgm_url']
            else:
                record['RealGM_URL'] = ''

        return records

    def _serialize_espn_pbp_analysis(
        self, espn_pbp: Dict[str, Any], away_team: str = '', home_team: str = ''
    ) -> Dict[str, Any]:
        """
        Serialize ESPN play-by-play analysis for a single game.

        Args:
            espn_pbp: ESPN PBP analysis dictionary from ESPNPlayByPlayEngine
            away_team: Away team name for mapping 'away' side to team name
            home_team: Home team name for mapping 'home' side to team name

        Returns:
            Serialized analysis for website display
        """
        result = {}

        # Team scoring runs - include top 3
        runs = espn_pbp.get('team_scoring_runs', [])
        if runs:
            result['teamScoringRuns'] = [
                {
                    'team': r.get('team', ''),
                    'points': r.get('points', 0),
                    'startTime': r.get('start_time', ''),
                    'endTime': r.get('end_time', ''),
                    'startPeriod': r.get('start_period', 1),
                    'endPeriod': r.get('end_period', 1),
                    'startScore': r.get('start_score', ''),
                    'endScore': r.get('end_score', ''),
                }
                for r in runs[:3]
            ]

        # Player point streaks - include top 3
        streaks = espn_pbp.get('player_point_streaks', [])
        if streaks:
            result['playerPointStreaks'] = [
                {
                    'player': s.get('player', ''),
                    'team': s.get('team', ''),
                    'points': s.get('points', 0),
                    'startTime': s.get('start_time', ''),
                    'endTime': s.get('end_time', ''),
                    'startPeriod': s.get('start_period', 1),
                    'endPeriod': s.get('end_period', 1),
                    'startScore': s.get('start_score', ''),
                    'endScore': s.get('end_score', ''),
                }
                for s in streaks[:3]
            ]

        # Biggest comeback
        comeback = espn_pbp.get('biggest_comeback')
        if comeback and comeback.get('deficit', 0) >= 5:
            result['biggestComeback'] = {
                'team': comeback.get('team', ''),
                'deficit': comeback.get('deficit', 0),
                'deficitTime': comeback.get('deficit_time', ''),
                'deficitPeriod': comeback.get('deficit_period', 0),
                'won': comeback.get('won', False),
            }

        # Game-winning shots
        gws = espn_pbp.get('game_winning_shots', {})
        if gws.get('clutch_go_ahead'):
            cga = gws['clutch_go_ahead']
            result['clutchGoAhead'] = {
                'player': cga.get('player', ''),
                'team': cga.get('team', ''),
                'time': cga.get('time', ''),
                'points': cga.get('points', 0),
                'score': cga.get('score', ''),
            }
        if gws.get('decisive_shot'):
            ds = gws['decisive_shot']
            result['decisiveShot'] = {
                'player': ds.get('player', ''),
                'team': ds.get('team', ''),
                'time': ds.get('time', ''),
                'period': ds.get('period', 0),
                'points': ds.get('points', 0),
                'score': ds.get('score', ''),
            }

        return result

    def _serialize_milestones(self) -> Dict[str, List[Dict]]:
        """Serialize all milestones."""
        milestones = self.processed_data.get('milestones', {})
        result = {}

        for key, df in milestones.items():
            if isinstance(df, pd.DataFrame) and not df.empty:
                # Select display columns
                display_cols = ['Date', 'Player', 'Player ID', 'Team', 'Opponent', 'Score', 'Detail', 'GameID', 'Gender']
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
        from ..scrapers.poll_scraper import get_team_current_rank

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

            # Look up current AP rankings (men's basketball)
            home_rank = get_team_current_rank(home_name, gender='M')
            away_rank = get_team_current_rank(away_name, gender='M')

            state = normalize_state(game['venue']['state'])

            formatted_games.append({
                'date': game['date'],
                'dateDisplay': game['date_display'],
                'time_detail': game.get('time_detail', ''),  # ESPN's actual game time
                'homeTeam': home_name,
                'homeTeamFull': game['home_team']['name'],
                'homeTeamAbbrev': game['home_team']['abbreviation'],
                'homeConf': home_conf,
                'homeRank': home_rank,
                'awayTeam': away_name,
                'awayTeamFull': game['away_team']['name'],
                'awayTeamAbbrev': game['away_team']['abbreviation'],
                'awayConf': away_conf,
                'awayRank': away_rank,
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

            # Common venue words to exclude from matching (too generic)
            GENERIC_VENUE_WORDS = {
                'arena', 'center', 'stadium', 'pavilion', 'gymnasium', 'gym',
                'coliseum', 'fieldhouse', 'field', 'house', 'complex', 'court',
                'hall', 'memorial', 'sports', 'athletic', 'events', 'event'
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

                    # Check for significant word match (exclude generic venue words)
                    our_words = [w for w in our_lower.split() if len(w) > 4 and w not in GENERIC_VENUE_WORDS]
                    significant_match = any(w in espn_lower for w in our_words)

                    if espn_lower == our_lower or alias_match or significant_match:
                        home = sched_game['home_team'].get('short_name') or sched_game['home_team']['name']
                        away = sched_game['away_team'].get('short_name') or sched_game['away_team']['name']
                        # Get current rankings
                        home_rank = get_team_current_rank(home, gender='M')
                        away_rank = get_team_current_rank(away, gender='M')
                        data['upcomingGames'].append({
                            'date': sched_game['date'],
                            'time_detail': sched_game.get('time_detail', ''),
                            'home': home,
                            'away': away,
                            'homeRank': home_rank,
                            'awayRank': away_rank,
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

            # SWAC schools
            'Bethune': 'Bethune-Cookman',
            'Bethune-Cookman': 'Bethune-Cookman',
            'Miss Valley St': 'Mississippi Valley State',
            'Mississippi Valley St': 'Mississippi Valley State',
            'Prairie View': 'Prairie View A&M',
            'Prairie View A&M': 'Prairie View A&M',
            'AR-Pine Bluff': 'Arkansas-Pine Bluff',
            'Ark-Pine Bluff': 'Arkansas-Pine Bluff',
            'Alabama A&M': 'Alabama A&M',
            'Alabama St': 'Alabama State',
            'Alcorn St': 'Alcorn State',
            'Grambling St': 'Grambling State',
            'Grambling': 'Grambling State',
            'Jackson St': 'Jackson State',
            'Florida A&M': 'Florida A&M',
            'Texas Southern': 'Texas Southern',
            'Southern U': 'Southern',

            # MEAC schools
            'Coppin St': 'Coppin State',
            'Delaware St': 'Delaware State',
            'Morgan St': 'Morgan State',
            'Norfolk St': 'Norfolk State',
            'SC State': 'South Carolina State',
            'Howard': 'Howard',

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
        """Serialize per-game player stats with RealGM transfer data."""
        player_games = self.processed_data.get('player_games', pd.DataFrame())
        if player_games.empty:
            return []

        records = self._df_to_records(player_games)

        # Cache RealGM lookups to avoid repeated calls for same player
        realgm_cache = {}

        for record in records:
            player_name = record.get('player', '')
            if not player_name:
                continue

            # Check cache first
            if player_name not in realgm_cache:
                player_data = lookup_player_transfers(player_name)
                if player_data and player_data.get('schools'):
                    # Extract "from" schools (previous schools before transfer)
                    previous_schools = []
                    for transfer in player_data.get('schools', []):
                        from_school = transfer.get('from')
                        if from_school:
                            previous_schools.append(from_school)
                    realgm_cache[player_name] = previous_schools
                else:
                    realgm_cache[player_name] = []

            # Add previous schools to record if any exist
            if realgm_cache[player_name]:
                record['realgm_previous_schools'] = realgm_cache[player_name]

        return records

    def _df_to_records(self, df: pd.DataFrame) -> List[Dict]:
        """Convert DataFrame to list of records, handling NaN values."""
        if df.empty:
            return []

        records = df.to_dict('records')

        # Columns that contain team names to normalize
        team_columns = {'Team', 'Away Team', 'Home Team', 'Opponent', 'team', 'opponent'}

        # Clean up records
        cleaned = []
        for record in records:
            cleaned_record = {}
            for key, value in record.items():
                # Convert numpy types to Python types
                if hasattr(value, 'item'):
                    value = value.item()
                # Handle NaN/None values - convert to None for JSON serialization
                if pd.isna(value):
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
        from ..utils.constants import CONFERENCES, TEAM_ALIASES, DEFUNCT_TEAMS, D1_EXIT_TEAMS, D1_ENTRY_TEAMS
        from ..utils.venue_resolver import get_venue_resolver, parse_venue_components
        import datetime

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

        # Get current date for checking D1 exit status
        today = int(datetime.datetime.now().strftime('%Y%m%d'))

        for conf_name, conf_teams in CONFERENCES.items():
            if conf_name in skip_conferences:
                continue
            teams_data = []
            for team in sorted(conf_teams):
                # Skip defunct teams - they count for badges but not checklist
                if team in DEFUNCT_TEAMS:
                    continue
                # Skip teams that have exited D1 (after their exit date)
                if team in D1_EXIT_TEAMS:
                    exit_date, _ = D1_EXIT_TEAMS[team]
                    if today >= exit_date:
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

            # Add D1 entry teams to their conference if after entry date and not already included
            for entry_team, (entry_date, target_conf) in D1_ENTRY_TEAMS.items():
                if target_conf == conf_name and today >= entry_date and entry_team not in conf_teams:
                    all_conference_teams.add(entry_team)
                    home_arena_m = venue_resolver.get_home_arena(entry_team, 'M')
                    home_arena_w = venue_resolver.get_home_arena(entry_team, 'W')
                    arena_name_m = parse_venue_components(home_arena_m)['name'] if home_arena_m else 'Unknown'
                    arena_name_w = parse_venue_components(home_arena_w)['name'] if home_arena_w else 'Unknown'
                    entry_team_data = {
                        'team': entry_team,
                        'seen': team_seen(entry_team, seen_teams_by_gender['all']),
                        'seenM': team_seen(entry_team, seen_teams_by_gender['M']),
                        'seenW': team_seen(entry_team, seen_teams_by_gender['W']),
                        'homeArena': arena_name_m,
                        'homeArenaM': arena_name_m,
                        'homeArenaW': arena_name_w,
                        'arenaVisited': arena_visited(home_arena_m, seen_venues_by_gender['all']),
                        'arenaVisitedM': arena_visited(home_arena_m, seen_venues_by_gender['M']),
                        'arenaVisitedW': arena_visited(home_arena_w, seen_venues_by_gender['W']),
                        'conference': conf_name,
                        'espnId': get_espn_team_id(entry_team),
                        'isTransition': True  # Mark as transitioning team
                    }
                    teams_data.append(entry_team_data)
                    all_d1_teams.append(entry_team_data)

            # Re-sort teams_data to include entry teams in alphabetical order
            teams_data = sorted(teams_data, key=lambda x: x['team'])

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

        # Find historical/other teams (seen but not in any current D1 conference)
        # These include D2/D3 teams which should get their actual conference name
        from ..utils.constants import get_conference
        historical_teams = []
        for team in seen_teams_by_gender['all']:
            # Check if this team is in any D1 conference (directly or via alias)
            in_conference = team in all_conference_teams
            if not in_conference:
                # Not in a D1 conference - check D2/D3 conferences or mark as historical
                actual_conf = get_conference(team, format_division=True)
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
                    'conference': actual_conf or 'Historical/Other',
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
