"""Tests for basketball_processor.parsers module."""

import pytest

from basketball_processor.parsers import (
    HTMLParsingError,
    validate_html_content,
    validate_game_data,
)


class TestValidateHtmlContent:
    """Tests for validate_html_content function."""

    def test_empty_content(self):
        """Test that empty content raises error."""
        with pytest.raises(HTMLParsingError, match="Empty HTML"):
            validate_html_content("")

    def test_none_content(self):
        """Test that None content raises error."""
        with pytest.raises(HTMLParsingError, match="Empty HTML"):
            validate_html_content(None)

    def test_short_content(self):
        """Test that too-short content raises error."""
        with pytest.raises(HTMLParsingError, match="too short"):
            validate_html_content("<html>short</html>")

    def test_non_sports_reference_content(self):
        """Test that non-Sports Reference content raises error."""
        long_content = "<html>" + "x" * 2000 + "</html>"
        with pytest.raises(HTMLParsingError, match="Sports Reference"):
            validate_html_content(long_content)

    def test_valid_content_with_scorebox(self):
        """Test that content with scorebox passes validation."""
        valid_content = "<html>" + "x" * 500 + "scorebox" + "x" * 500 + "</html>"
        # Should not raise
        validate_html_content(valid_content)

    def test_valid_content_with_sports_reference(self):
        """Test that content with sports-reference passes validation."""
        valid_content = "<html>" + "x" * 500 + "sports-reference" + "x" * 500 + "</html>"
        # Should not raise
        validate_html_content(valid_content)

    def test_wrong_type(self):
        """Test that non-string content raises error."""
        with pytest.raises(HTMLParsingError, match="Expected string"):
            validate_html_content(12345)


class TestValidateGameData:
    """Tests for validate_game_data function."""

    def test_complete_game_data(self):
        """Test that complete game data has no warnings."""
        game_data = {
            'basic_info': {
                'away_team': 'Duke',
                'home_team': 'North Carolina',
                'date': 'December 25, 2024',
                'away_score': 75,
                'home_score': 80,
            },
            'box_score': {
                'away': {'players': [{'name': 'Player 1'}]},
                'home': {'players': [{'name': 'Player 2'}]},
            },
        }
        warnings = validate_game_data(game_data)
        assert len(warnings) == 0

    def test_missing_away_team(self):
        """Test that missing away team generates warning."""
        game_data = {
            'basic_info': {
                'home_team': 'North Carolina',
                'date': 'December 25, 2024',
            },
            'box_score': {},
        }
        warnings = validate_game_data(game_data)
        assert any("away team" in w.lower() for w in warnings)

    def test_missing_home_team(self):
        """Test that missing home team generates warning."""
        game_data = {
            'basic_info': {
                'away_team': 'Duke',
                'date': 'December 25, 2024',
            },
            'box_score': {},
        }
        warnings = validate_game_data(game_data)
        assert any("home team" in w.lower() for w in warnings)

    def test_missing_date(self):
        """Test that missing date generates warning."""
        game_data = {
            'basic_info': {
                'away_team': 'Duke',
                'home_team': 'North Carolina',
            },
            'box_score': {},
        }
        warnings = validate_game_data(game_data)
        assert any("date" in w.lower() for w in warnings)

    def test_zero_scores(self):
        """Test that zero scores generate warning."""
        game_data = {
            'basic_info': {
                'away_team': 'Duke',
                'home_team': 'North Carolina',
                'date': 'December 25, 2024',
                'away_score': 0,
                'home_score': 0,
            },
            'box_score': {},
        }
        warnings = validate_game_data(game_data)
        assert any("scores are 0" in w.lower() for w in warnings)

    def test_missing_player_stats(self):
        """Test that missing player stats generate warnings."""
        game_data = {
            'basic_info': {
                'away_team': 'Duke',
                'home_team': 'North Carolina',
                'date': 'December 25, 2024',
                'away_score': 75,
                'home_score': 80,
            },
            'box_score': {
                'away': {'players': []},
                'home': {'players': []},
            },
        }
        warnings = validate_game_data(game_data)
        assert any("away team player" in w.lower() for w in warnings)
        assert any("home team player" in w.lower() for w in warnings)

    def test_empty_game_data(self):
        """Test that empty game data generates multiple warnings."""
        game_data = {}
        warnings = validate_game_data(game_data)
        assert len(warnings) >= 3  # At least away team, home team, date


class TestHTMLParsingError:
    """Tests for HTMLParsingError exception."""

    def test_exception_message(self):
        """Test that exception preserves message."""
        error = HTMLParsingError("Test error message")
        assert str(error) == "Test error message"

    def test_exception_inheritance(self):
        """Test that HTMLParsingError is a proper Exception."""
        assert issubclass(HTMLParsingError, Exception)
