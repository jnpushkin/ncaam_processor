"""Tests for basketball_processor.utils.helpers module."""

import pytest
from datetime import datetime

from basketball_processor.utils.helpers import (
    normalize_name,
    get_team_code,
    parse_date,
    format_date_yyyymmdd,
    generate_game_id,
    parse_minutes,
    safe_int,
    safe_float,
    extract_player_id_from_href,
    calculate_game_score,
)


class TestNormalizeName:
    """Tests for normalize_name function."""

    def test_basic_name(self):
        """Test basic name normalization."""
        assert normalize_name("John Smith") == "John Smith"

    def test_accented_characters(self):
        """Test removal of accented characters."""
        assert normalize_name("José García") == "Jose Garcia"
        assert normalize_name("André François") == "Andre Francois"

    def test_empty_name(self):
        """Test empty string handling."""
        assert normalize_name("") == ""
        assert normalize_name(None) == ""

    def test_extra_whitespace(self):
        """Test whitespace normalization."""
        assert normalize_name("  John   Smith  ") == "John Smith"


class TestGetTeamCode:
    """Tests for get_team_code function."""

    def test_known_teams(self):
        """Test code generation for known teams."""
        assert get_team_code("Duke") == "DUKE"
        assert get_team_code("North Carolina") == "UNC"
        assert get_team_code("Kentucky") == "UK"

    def test_unknown_team(self):
        """Test code generation for unknown teams."""
        # Should return first 4 characters uppercase
        assert get_team_code("Unknown University") == "UNKN"

    def test_empty_team(self):
        """Test empty team name handling."""
        assert get_team_code("") == ""
        assert get_team_code(None) == ""


class TestParseDate:
    """Tests for parse_date function."""

    def test_standard_formats(self):
        """Test standard date formats."""
        assert parse_date("12/25/2024") == datetime(2024, 12, 25)
        assert parse_date("2024-12-25") == datetime(2024, 12, 25)
        assert parse_date("December 25, 2024") == datetime(2024, 12, 25)

    def test_short_year(self):
        """Test two-digit year format."""
        result = parse_date("12/25/24")
        assert result is not None
        assert result.month == 12
        assert result.day == 25

    def test_invalid_date(self):
        """Test invalid date handling."""
        assert parse_date("not a date") is None
        assert parse_date("") is None
        assert parse_date(None) is None


class TestFormatDateYyyymmdd:
    """Tests for format_date_yyyymmdd function."""

    def test_standard_conversion(self):
        """Test standard date conversion."""
        assert format_date_yyyymmdd("December 25, 2024") == "20241225"
        assert format_date_yyyymmdd("12/25/2024") == "20241225"

    def test_invalid_date(self):
        """Test invalid date handling."""
        assert format_date_yyyymmdd("invalid") == ""
        assert format_date_yyyymmdd("") == ""


class TestGenerateGameId:
    """Tests for generate_game_id function."""

    def test_basic_game_id(self):
        """Test basic game ID generation."""
        game_id = generate_game_id("December 25, 2024", "Duke")
        assert game_id.startswith("20241225-")
        assert "duke" in game_id.lower()

    def test_doubleheader(self):
        """Test doubleheader game ID."""
        game_id = generate_game_id("December 25, 2024", "Duke", game_num=2)
        assert "-02-" in game_id


class TestParseMinutes:
    """Tests for parse_minutes function."""

    def test_minutes_seconds_format(self):
        """Test MM:SS format."""
        assert parse_minutes("35:20") == pytest.approx(35.333, rel=0.01)
        assert parse_minutes("40:00") == 40.0

    def test_integer_minutes(self):
        """Test integer minutes."""
        assert parse_minutes("35") == 35.0
        assert parse_minutes("40") == 40.0

    def test_empty_or_invalid(self):
        """Test empty/invalid handling."""
        assert parse_minutes("") == 0.0
        assert parse_minutes(None) == 0.0
        assert parse_minutes("invalid") == 0.0


class TestSafeInt:
    """Tests for safe_int function."""

    def test_valid_integers(self):
        """Test valid integer conversion."""
        assert safe_int(42) == 42
        assert safe_int("42") == 42
        assert safe_int(42.9) == 42

    def test_invalid_values(self):
        """Test invalid value handling."""
        assert safe_int(None) == 0
        assert safe_int("") == 0
        assert safe_int("invalid") == 0

    def test_custom_default(self):
        """Test custom default value."""
        assert safe_int(None, -1) == -1
        assert safe_int("invalid", 99) == 99


class TestSafeFloat:
    """Tests for safe_float function."""

    def test_valid_floats(self):
        """Test valid float conversion."""
        assert safe_float(3.14) == 3.14
        assert safe_float("3.14") == 3.14
        assert safe_float(42) == 42.0

    def test_percentage_string(self):
        """Test percentage string handling."""
        assert safe_float("50%") == 50.0
        assert safe_float(".500") == 0.5

    def test_invalid_values(self):
        """Test invalid value handling."""
        assert safe_float(None) == 0.0
        assert safe_float("") == 0.0
        assert safe_float("invalid") == 0.0


class TestExtractPlayerId:
    """Tests for extract_player_id_from_href function."""

    def test_valid_href(self):
        """Test valid player href."""
        href = "/cbb/players/john-smith-1.html"
        assert extract_player_id_from_href(href) == "john-smith-1"

    def test_invalid_href(self):
        """Test invalid href handling."""
        assert extract_player_id_from_href("") == ""
        assert extract_player_id_from_href(None) == ""
        assert extract_player_id_from_href("/invalid/path") == ""


class TestCalculateGameScore:
    """Tests for calculate_game_score function."""

    def test_basic_game_score(self):
        """Test basic game score calculation."""
        stats = {
            'pts': 20,
            'fg': 8,
            'fga': 15,
            'ft': 2,
            'fta': 3,
            'orb': 2,
            'drb': 5,
            'ast': 4,
            'stl': 1,
            'blk': 1,
            'pf': 2,
            'tov': 2,
        }
        score = calculate_game_score(stats)
        assert isinstance(score, float)
        assert score > 0

    def test_empty_stats(self):
        """Test empty stats handling."""
        score = calculate_game_score({})
        assert score == 0.0
