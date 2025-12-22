"""
Data serializers for website JSON generation.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import json

from ..utils.nba_players import get_nba_player_info_by_id, get_nba_status_batch, recheck_female_players_for_wnba


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
        if skip_nba:
            # Skip NBA lookups entirely for faster generation
            pro_status = {}
        else:
            player_ids = [r.get('Player ID', '') for r in records if r.get('Player ID')]
            pro_status = get_nba_status_batch(player_ids, max_fetch=999)

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
        from ..utils.constants import CONFERENCES, TEAM_ALIASES
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
            # Check for exact match (case insensitive only)
            arena_lower = arena_name.lower().strip()
            for venue in seen_venues:
                venue_lower = venue.lower().strip()
                # Exact match (case insensitive)
                if arena_lower == venue_lower:
                    return True
            # No fuzzy matching - too many false positives
            return False

        # Build checklist for each conference
        checklist = {}
        all_d1_teams = []  # For "All D1" option
        all_conference_teams = set()  # Track all teams in conferences

        for conf_name, conf_teams in CONFERENCES.items():
            teams_data = []
            for team in sorted(conf_teams):
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
                    'conference': conf_name
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
                    'conference': 'Historical/Other'
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
