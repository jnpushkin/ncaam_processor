"""
Data serializers for website JSON generation.
"""

from typing import Dict, List, Any, Optional
import pandas as pd
import json

from ..utils.nba_players import get_nba_player_info_by_id, get_nba_status_batch


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

    def serialize_all(self) -> Dict[str, Any]:
        """
        Serialize all data for website.

        Returns:
            Dictionary ready for JSON encoding
        """
        summary = self._serialize_summary()
        players = self._serialize_players()

        # Count NBA and International players after serialization
        nba_count = sum(1 for p in players if p.get('NBA'))
        intl_count = sum(1 for p in players if p.get('International'))
        summary['nbaPlayers'] = nba_count
        summary['intlPlayers'] = intl_count

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

        return {
            'totalGames': len(game_log),
            'totalPlayers': len(players),
            'totalTeams': len(team_records),
            'totalVenues': len(venue_records),
            'totalPoints': total_points,
            'milestones': milestone_counts,
            'nbaPlayers': 0,  # Will be calculated after players are serialized
        }

    def _serialize_games(self) -> List[Dict]:
        """Serialize game log with linescore data."""
        game_log = self.processed_data.get('game_log', pd.DataFrame())
        if game_log.empty:
            return []

        games = self._df_to_records(game_log)

        # Add linescore and DateSort from raw games
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

        return games

    def _serialize_players(self) -> List[Dict]:
        """Serialize player statistics with NBA and international info."""
        players = self.processed_data.get('players', pd.DataFrame())
        if players.empty:
            return []

        records = self._df_to_records(players)

        # Batch fetch NBA/international status for all players
        player_ids = [r.get('Player ID', '') for r in records if r.get('Player ID')]
        pro_status = get_nba_status_batch(player_ids)

        # Add NBA and International flags to each player
        for record in records:
            player_id = record.get('Player ID', '')
            pro_info = pro_status.get(player_id) if player_id else None
            if not pro_info:
                pro_info = get_nba_player_info_by_id(player_id)

            # NBA info
            if pro_info and pro_info.get('nba_url'):
                record['NBA'] = True
                record['NBA_Active'] = pro_info.get('is_active', False)
                record['NBA_URL'] = pro_info.get('nba_url', '')
            else:
                record['NBA'] = False

            # International info
            if pro_info and pro_info.get('intl_url'):
                record['International'] = True
                record['Intl_URL'] = pro_info.get('intl_url', '')
            else:
                record['International'] = False

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
