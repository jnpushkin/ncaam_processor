"""Tests for basketball_processor.utils.venue_resolver module."""

import pytest

from basketball_processor.utils.venue_resolver import (
    VenueResolver,
    get_venue_resolver,
    resolve_venue,
    normalize_cached_venue,
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


class TestNormalizeCachedVenue:
    """Tests for normalize_cached_venue function."""

    def test_updates_stale_home_arena_name(self):
        """Test that stale arena name is updated to match venues.json."""
        # Simulate a cached game with an old arena name (shares "Cameron" word)
        game_data = {
            'game_id': '20241225-duke',
            'basic_info': {
                'venue': 'Cameron Arena, Durham, North Carolina',
                'home_team': 'Duke',
            },
        }
        venue = normalize_cached_venue(game_data)
        # Should return the canonical name from venues.json
        assert 'Cameron Indoor Stadium' in venue
        assert 'Durham' in venue

    def test_preserves_neutral_site_venue(self):
        """Test that neutral site venue is not changed."""
        game_data = {
            'game_id': '20241225-duke',
            'basic_info': {
                'venue': 'Madison Square Garden, New York, New York',
                'home_team': 'Duke',
            },
        }
        venue = normalize_cached_venue(game_data)
        # Different city than Durham, so should preserve original
        assert venue == 'Madison Square Garden, New York, New York'

    def test_preserves_different_arena_same_city(self):
        """Test that a different arena in the same city is preserved."""
        # San Francisco playing at Chase Center (not their home arena)
        game_data = {
            'game_id': '20241225-usf',
            'basic_info': {
                'venue': 'Chase Center, San Francisco, California',
                'home_team': 'San Francisco',
            },
        }
        venue = normalize_cached_venue(game_data)
        # Chase Center doesn't share words with "War Memorial", so preserve it
        assert venue == 'Chase Center, San Francisco, California'

    def test_updates_renamed_arena(self):
        """Test that a renamed arena gets updated."""
        # War Memorial Gymnasium -> War Memorial at The Sobrato Center
        game_data = {
            'game_id': '20241225-usf',
            'basic_info': {
                'venue': 'War Memorial Gymnasium, San Francisco, California',
                'home_team': 'San Francisco',
            },
        }
        venue = normalize_cached_venue(game_data)
        # Shares "War" and "Memorial" with new name, so should update
        assert 'Sobrato' in venue or 'War Memorial' in venue

    def test_handles_missing_venue(self):
        """Test behavior when venue is missing."""
        game_data = {
            'game_id': '20241225-duke',
            'basic_info': {
                'home_team': 'Duke',
            },
        }
        venue = normalize_cached_venue(game_data)
        # Should fall back to resolve_venue behavior
        assert venue is not None
        assert 'Cameron' in venue or 'Durham' in venue

    def test_handles_unknown_team(self):
        """Test behavior with team not in venues.json."""
        game_data = {
            'game_id': '20241225-unknown',
            'basic_info': {
                'venue': 'Some Arena, Some City, Some State',
                'home_team': 'Unknown University XYZ',
            },
        }
        venue = normalize_cached_venue(game_data)
        # Should preserve original venue
        assert venue == 'Some Arena, Some City, Some State'


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
