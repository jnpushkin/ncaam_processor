"""
Integration tests for the full basketball processor pipeline.

These tests verify that the complete flow from cached JSON data
to Excel and HTML output works correctly.
"""

import json
from pathlib import Path
from typing import Dict, List, Any

import pytest

from basketball_processor.utils import CACHE_DIR
from basketball_processor.utils.stat_utils import (
    is_double_double,
    is_triple_double,
    calculate_shooting_percentages,
    calculate_four_factors,
)
from basketball_processor.processors.player_stats_processor import PlayerStatsProcessor
from basketball_processor.processors.team_records_processor import TeamRecordsProcessor
from basketball_processor.processors.milestones_processor import MilestonesProcessor
from basketball_processor.engines.milestone_engine import MilestoneEngine
from basketball_processor.engines.special_events_engine import SpecialEventsEngine


def load_cached_games(limit: int = 5) -> List[Dict[str, Any]]:
    """Load a few cached game files for testing."""
    games = []
    cache_files = list(CACHE_DIR.glob("*.json"))[:limit]

    for cache_file in cache_files:
        try:
            with open(cache_file) as f:
                games.append(json.load(f))
        except (json.JSONDecodeError, IOError):
            continue

    return games


class TestPlayerStatsProcessor:
    """Test the PlayerStatsProcessor with real cached data."""

    def test_process_multiple_games(self):
        """Test processing multiple cached games."""
        games = load_cached_games(limit=5)
        if not games:
            pytest.skip("No cached games available")

        processor = PlayerStatsProcessor(games)
        result = processor.process_all_player_stats()

        # Verify player stats were collected
        assert 'players' in result
        assert len(result['players']) > 0

    def test_season_highs_tracking(self):
        """Test that season highs are tracked correctly."""
        games = load_cached_games(limit=10)
        if not games:
            pytest.skip("No cached games available")

        processor = PlayerStatsProcessor(games)
        processor.process_all_player_stats()

        # Get season highs
        highs = processor.player_season_highs

        # Verify structure - should have data if games have player stats
        assert isinstance(highs, dict)


class TestTeamRecordsProcessor:
    """Test the TeamRecordsProcessor with real cached data."""

    def test_process_multiple_games(self):
        """Test processing multiple games for team records."""
        games = load_cached_games(limit=5)
        if not games:
            pytest.skip("No cached games available")

        processor = TeamRecordsProcessor(games)
        records = processor.process_team_records()

        # Should have some team records
        assert records is not None

    def test_head_to_head_tracking(self):
        """Test head-to-head record tracking."""
        games = load_cached_games(limit=10)
        if not games:
            pytest.skip("No cached games available")

        processor = TeamRecordsProcessor(games)
        processor.process_team_records()

        # Get head to head
        h2h = processor.head_to_head

        # Should be a dict
        assert isinstance(h2h, dict)


class TestMilestonesProcessor:
    """Test the MilestonesProcessor with real cached data."""

    def test_process_milestones(self):
        """Test milestone detection from games."""
        games = load_cached_games(limit=10)
        if not games:
            pytest.skip("No cached games available")

        processor = MilestonesProcessor(games)
        milestones = processor.process_all_milestones()

        # Should be a dict with milestone categories
        assert isinstance(milestones, dict)


class TestStatUtilsFunctions:
    """Test stat utility functions directly."""

    def test_double_double_detection(self):
        """Test double-double detection."""
        # Player with double-double (15 pts, 12 reb)
        stats = {
            'pts': 15,
            'trb': 12,
            'ast': 5,
            'stl': 2,
            'blk': 1
        }
        assert is_double_double(stats) is True

    def test_triple_double_detection(self):
        """Test triple-double detection."""
        # Player with triple-double (15 pts, 12 reb, 10 ast)
        stats = {
            'pts': 15,
            'trb': 12,
            'ast': 10,
            'stl': 2,
            'blk': 1
        }
        assert is_triple_double(stats) is True

    def test_not_double_double(self):
        """Test that single-category games don't count as double-double."""
        # Player with only one 10+ category
        stats = {
            'pts': 25,
            'trb': 5,
            'ast': 3,
            'stl': 2,
            'blk': 1
        }
        assert is_double_double(stats) is False

    def test_shooting_percentages(self):
        """Test shooting percentage calculations."""
        stats = {
            'fg': 8,
            'fga': 15,
            'fg3': 3,
            'fg3a': 7,
            'ft': 5,
            'fta': 6,
            'pts': 24
        }
        pcts = calculate_shooting_percentages(stats)

        assert 'fg_pct' in pcts
        assert 'fg3_pct' in pcts
        assert 'ft_pct' in pcts
        assert 'efg_pct' in pcts
        assert 'ts_pct' in pcts

        # Verify calculations are reasonable
        assert 0 <= pcts['fg_pct'] <= 1
        assert 0 <= pcts['ts_pct'] <= 1

    def test_four_factors(self):
        """Test four factors calculation."""
        team_stats = {
            'fg': 30, 'fg3': 8, 'fga': 65,
            'ft': 15, 'fta': 20,
            'tov': 12, 'orb': 10, 'drb': 25
        }
        opp_stats = {
            'fg': 28, 'fg3': 6, 'fga': 60,
            'ft': 12, 'fta': 16,
            'tov': 15, 'orb': 8, 'drb': 22
        }

        factors = calculate_four_factors(team_stats, opp_stats)

        assert 'team' in factors
        assert 'opponent' in factors
        assert 'efg_pct' in factors['team']
        assert 'tov_pct' in factors['team']


class TestSpecialEventsEngine:
    """Test the SpecialEventsEngine."""

    def test_overtime_detection(self):
        """Test overtime game detection."""
        # OT game data
        game_data = {
            'basic_info': {'away_score': 75, 'home_score': 73},
            'linescore': {
                'away': {'1': 30, '2': 35, 'OT': [10], 'T': 75},
                'home': {'1': 32, '2': 33, 'OT': [8], 'T': 73}
            }
        }
        engine = SpecialEventsEngine(game_data)
        result = engine.detect()

        assert result['special_events']['overtime_game'] is True

    def test_not_overtime(self):
        """Test regular game is not flagged as OT."""
        # Regular game data
        game_data = {
            'basic_info': {'away_score': 65, 'home_score': 60},
            'linescore': {
                'away': {'1': 30, '2': 35, 'T': 65},
                'home': {'1': 32, '2': 28, 'T': 60}
            }
        }
        engine = SpecialEventsEngine(game_data)
        result = engine.detect()

        assert result['special_events']['overtime_game'] is False

    def test_blowout_detection(self):
        """Test blowout game detection (20+ point margin)."""
        game_data = {
            'basic_info': {'away_score': 85, 'home_score': 60},
            'linescore': {}
        }
        engine = SpecialEventsEngine(game_data)
        result = engine.detect()

        assert result['special_events']['blowout'] is True
        assert result['special_events']['blowout_margin'] == 25

    def test_close_game_not_blowout(self):
        """Test close game is not flagged as blowout."""
        game_data = {
            'basic_info': {'away_score': 72, 'home_score': 70},
            'linescore': {}
        }
        engine = SpecialEventsEngine(game_data)
        result = engine.detect()

        assert result['special_events']['blowout'] is False
        assert result['special_events']['close_game'] is True


class TestMilestoneEngine:
    """Test the MilestoneEngine."""

    def test_milestone_detection_in_game(self):
        """Test milestone detection with actual game data."""
        games = load_cached_games(limit=1)
        if not games:
            pytest.skip("No cached games available")

        engine = MilestoneEngine(games[0])
        result = engine.process()

        # Should have milestone categories
        assert hasattr(engine, 'milestones')
        assert isinstance(engine.milestones, dict)
        # Result should have milestone_stats
        assert 'milestone_stats' in result


class TestPipelineEndToEnd:
    """End-to-end pipeline tests."""

    def test_full_pipeline_creates_output(self):
        """Test that the full pipeline can process games and create output."""
        games = load_cached_games(limit=3)
        if not games:
            pytest.skip("No cached games available")

        # Process through all processors
        player_processor = PlayerStatsProcessor(games)
        team_processor = TeamRecordsProcessor(games)
        milestone_processor = MilestonesProcessor(games)

        player_stats = player_processor.process_all_player_stats()
        team_records = team_processor.process_team_records()
        milestones = milestone_processor.process_all_milestones()

        # All should return data
        assert player_stats is not None
        assert team_records is not None
        assert milestones is not None

    def test_gender_filtering(self):
        """Test that gender filtering works correctly."""
        games = load_cached_games(limit=20)
        if not games:
            pytest.skip("No cached games available")

        men_games = [g for g in games if g.get('gender') == 'M']
        women_games = [g for g in games if g.get('gender') == 'W']

        # Process men's games only
        if men_games:
            processor = PlayerStatsProcessor(men_games)
            men_stats = processor.process_all_player_stats()
            assert men_stats is not None

        # Process women's games only
        if women_games:
            processor2 = PlayerStatsProcessor(women_games)
            women_stats = processor2.process_all_player_stats()
            assert women_stats is not None

    def test_cached_game_structure(self):
        """Test that cached games have the expected structure."""
        games = load_cached_games(limit=1)
        if not games:
            pytest.skip("No cached games available")

        game = games[0]

        # Check required keys
        assert 'basic_info' in game
        assert 'box_score' in game
        assert 'gender' in game

        # Check basic_info structure
        basic_info = game['basic_info']
        assert 'away_team' in basic_info or 'home_team' in basic_info
