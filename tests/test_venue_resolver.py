"""Tests for basketball_processor.utils.venue_resolver module."""

import pytest

from basketball_processor.utils.venue_resolver import (
    VenueResolver,
    get_venue_resolver,
    resolve_venue,
    parse_venue_components,
)


class TestVenueResolver:
    """Tests for VenueResolver class."""

    def test_singleton_instance(self):
        """Test that get_venue_resolver returns singleton."""
        resolver1 = get_venue_resolver()
        resolver2 = get_venue_resolver()
        assert resolver1 is resolver2

    def test_home_arenas_loaded(self):
        """Test that home arenas are loaded from JSON."""
        resolver = get_venue_resolver()
        assert len(resolver.home_arenas) > 0
        assert "Duke" in resolver.home_arenas
        assert "Kansas" in resolver.home_arenas

    def test_get_home_arena_single(self):
        """Test getting home arena for team with single arena."""
        resolver = get_venue_resolver()
        arena = resolver.get_home_arena("Duke")
        assert arena is not None
        assert "Durham" in arena or "Cameron" in arena

    def test_get_home_arena_gender_specific(self):
        """Test getting gender-specific arena."""
        resolver = get_venue_resolver()
        # Kentucky has different arenas for men and women
        mens_arena = resolver.get_home_arena("Kentucky", "M")
        womens_arena = resolver.get_home_arena("Kentucky", "W")
        # Both should return valid arenas
        assert mens_arena is not None
        assert womens_arena is not None
        # They may or may not be the same depending on data

    def test_get_home_arena_unknown_team(self):
        """Test getting arena for unknown team."""
        resolver = get_venue_resolver()
        arena = resolver.get_home_arena("Unknown University XYZ")
        assert arena is None


class TestResolveVenue:
    """Tests for resolve_venue function."""

    def test_existing_venue_preserved(self):
        """Test that existing venue is preserved."""
        game_data = {
            'game_id': '20241225-duke',
            'basic_info': {
                'venue': 'Madison Square Garden, New York, New York',
                'home_team': 'Duke',
            },
        }
        venue = resolve_venue(game_data)
        assert venue == 'Madison Square Garden, New York, New York'

    def test_venue_from_home_team(self):
        """Test that home team arena is used when venue missing."""
        game_data = {
            'game_id': '20241225-duke',
            'basic_info': {
                'home_team': 'Duke',
            },
        }
        venue = resolve_venue(game_data)
        assert venue is not None
        # Duke plays at Cameron Indoor Stadium


class TestParseVenueComponents:
    """Tests for parse_venue_components function."""

    def test_full_venue_string(self):
        """Test parsing full venue string."""
        result = parse_venue_components("Cameron Indoor Stadium, Durham, North Carolina")
        assert result['name'] == "Cameron Indoor Stadium"
        assert result['city'] == "Durham"
        assert result['state'] == "North Carolina"

    def test_city_state_only(self):
        """Test parsing city, state format."""
        result = parse_venue_components("Durham, North Carolina")
        assert result['city'] == "Durham"
        assert result['state'] == "North Carolina"

    def test_venue_name_only(self):
        """Test parsing venue name only."""
        result = parse_venue_components("Cameron Indoor Stadium")
        assert result['name'] == "Cameron Indoor Stadium"
        assert result['city'] == ""
        assert result['state'] == ""

    def test_empty_string(self):
        """Test parsing empty string."""
        result = parse_venue_components("")
        assert result['name'] == ""
        assert result['city'] == ""
        assert result['state'] == ""

    def test_extra_commas(self):
        """Test handling of extra commas."""
        result = parse_venue_components("Arena Name, City, State, Country")
        assert result['name'] == "Arena Name"
        assert result['city'] == "City"
        assert result['state'] == "State"
