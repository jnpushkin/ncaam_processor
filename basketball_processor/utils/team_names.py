"""
Shared team name normalization utilities.

Centralizes team name mapping and normalization logic used across scrapers
and serializers.
"""

import re
from typing import Optional

from .constants import TEAM_ALIASES


def normalize_team_name(name: str) -> str:
    """
    Normalize team name using the central TEAM_ALIASES mapping.

    Args:
        name: Team name to normalize

    Returns:
        Normalized team name, or original if no mapping exists
    """
    if not name:
        return name
    return TEAM_ALIASES.get(name, name)


def normalize_team_name_for_comparison(name: str) -> str:
    """
    Normalize team name for string comparison (lowercase, no punctuation).

    Used for matching teams across different data sources where naming
    conventions may vary (e.g., "St. John's" vs "St Johns").

    Args:
        name: Team name to normalize

    Returns:
        Lowercase name with punctuation removed
    """
    if not name:
        return ''
    # First try direct alias lookup
    if name in TEAM_ALIASES:
        name = TEAM_ALIASES[name]
    # Clean up common variations
    name = name.replace("'", "").replace(".", "").replace("-", " ")
    name = name.replace("(", "").replace(")", "")  # Remove parentheses
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name


def get_canonical_name(name: str) -> str:
    """
    Get the canonical (official) team name.

    Alias for normalize_team_name for semantic clarity.

    Args:
        name: Team name or alias

    Returns:
        Canonical team name
    """
    return normalize_team_name(name)
