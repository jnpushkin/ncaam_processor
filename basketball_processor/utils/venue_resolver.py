"""
Venue resolution utility - resolves missing venue data using reference files.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class VenueResolver:
    """Resolves venue information for games."""

    def __init__(self):
        self.home_arenas: Dict[str, Any] = {}  # Can be string or {"M": str, "W": str}
        self.game_overrides: Dict[str, str] = {}
        self.neutral_sites: Dict[str, str] = {}
        self._load_references()

    def _load_references(self):
        """Load venue reference data from JSON file."""
        ref_path = Path(__file__).parent.parent / "references" / "venues.json"

        if ref_path.exists():
            with open(ref_path, 'r') as f:
                data = json.load(f)
                # Filter out comment keys (keys starting with _)
                self.home_arenas = {
                    k: v for k, v in data.get('home_arenas', {}).items()
                    if not k.startswith('_')
                }
                self.game_overrides = data.get('game_overrides', {})
                self.neutral_sites = data.get('neutral_sites', {})

    def resolve_venue(self, game_data: Dict[str, Any]) -> Optional[str]:
        """
        Resolve venue for a game.

        Priority:
        1. Game-specific override
        2. Existing venue in game data
        3. Home team's arena (only if likely a home game)
        4. Location from game data

        Args:
            game_data: Parsed game dictionary

        Returns:
            Resolved venue string or None
        """
        game_id = game_data.get('game_id', '')
        basic_info = game_data.get('basic_info', {})
        gender = game_data.get('gender', 'M')

        # Check for game-specific override first
        # Try full game_id, then without gender suffix (-m or -w)
        if game_id:
            if game_id in self.game_overrides:
                return self.game_overrides[game_id]
            # Try without gender suffix
            base_id = game_id.rsplit('-', 1)[0] if game_id.endswith('-m') or game_id.endswith('-w') else game_id
            if base_id != game_id and base_id in self.game_overrides:
                return self.game_overrides[base_id]

        # Use existing venue if present
        venue = basic_info.get('venue')
        if venue:
            return venue

        # Check location - if it's a known neutral site, don't assume home arena
        location = basic_info.get('location', '')
        if self._is_likely_neutral_site(location, basic_info):
            return location if location else None

        # Fall back to home team's arena only for likely home games
        home_team = basic_info.get('home_team', '')
        if home_team and home_team in self.home_arenas:
            # Only use home arena if location matches or location is empty
            home_arena = self._get_arena_for_gender(home_team, gender)
            if home_arena and (not location or self._location_matches_arena(location, home_arena)):
                return home_arena

        # Use location as last resort
        if location:
            return location

        return None

    def _get_arena_for_gender(self, team: str, gender: str = 'M') -> Optional[str]:
        """Get the appropriate arena for a team based on gender."""
        arena = self.home_arenas.get(team)
        if arena is None:
            return None

        # If arena is a dict with M/W keys, use the gender-specific one
        if isinstance(arena, dict):
            return arena.get(gender) or arena.get('M') or arena.get('W')

        # Otherwise it's a string, use as-is
        return arena

    def _is_likely_neutral_site(self, location: str, basic_info: Dict) -> bool:
        """Check if game is likely at a neutral site."""
        if not location:
            return False

        # Check if location contains a known neutral site NAME (not just city)
        location_lower = location.lower()
        for site_name in self.neutral_sites.keys():
            if site_name.lower() in location_lower:
                return True

        # Check for tournament-style dates (March/April often = tournament)
        date = basic_info.get('date', '')
        if 'March' in date or 'April' in date:
            # Could be tournament - be conservative
            return True

        return False

    def _location_matches_arena(self, location: str, arena: str) -> bool:
        """Check if location roughly matches arena location."""
        if not location or not arena:
            return False

        # Extract city from arena (usually "Arena Name, City, State")
        arena_parts = arena.split(',')
        if len(arena_parts) >= 2:
            arena_city = arena_parts[-2].strip().lower()
            return arena_city in location.lower()

        return False

    def get_home_arena(self, team: str, gender: str = None) -> Optional[str]:
        """Get home arena for a team, optionally for a specific gender."""
        arena = self.home_arenas.get(team)
        if arena is None:
            return None

        # If arena is a dict with M/W keys
        if isinstance(arena, dict):
            if gender:
                return arena.get(gender) or arena.get('M') or arena.get('W')
            # If no gender specified, return men's arena (or first available)
            return arena.get('M') or arena.get('W')

        # Otherwise it's a string, return as-is
        return arena

    def is_neutral_site(self, venue: str) -> bool:
        """Check if venue is a known neutral site."""
        if not venue:
            return False
        for neutral_name in self.neutral_sites.keys():
            if neutral_name.lower() in venue.lower():
                return True
        return False


# Singleton instance
_resolver = None

def get_venue_resolver() -> VenueResolver:
    """Get singleton venue resolver instance."""
    global _resolver
    if _resolver is None:
        _resolver = VenueResolver()
    return _resolver


def resolve_venue(game_data: Dict[str, Any]) -> Optional[str]:
    """Convenience function to resolve venue for a game."""
    return get_venue_resolver().resolve_venue(game_data)


def parse_venue_components(venue_string: str) -> Dict[str, str]:
    """
    Parse a venue string into name, city, and state components.

    Expected format: "Venue Name, City, State"

    Args:
        venue_string: Full venue string

    Returns:
        Dictionary with 'name', 'city', 'state' keys
    """
    if not venue_string:
        return {'name': '', 'city': '', 'state': ''}

    parts = [p.strip() for p in venue_string.split(',')]

    if len(parts) >= 3:
        # Full format: "Venue Name, City, State"
        return {
            'name': parts[0],
            'city': parts[1],
            'state': parts[2]
        }
    elif len(parts) == 2:
        # Could be "City, State" or "Venue Name, City"
        # Check if second part looks like a state
        if len(parts[1]) <= 15 and parts[1].replace(' ', '').isalpha():
            return {
                'name': '',
                'city': parts[0],
                'state': parts[1]
            }
        else:
            return {
                'name': parts[0],
                'city': parts[1],
                'state': ''
            }
    else:
        # Just one part - assume it's the venue name
        return {
            'name': parts[0],
            'city': '',
            'state': ''
        }
