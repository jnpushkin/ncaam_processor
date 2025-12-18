"""Tests for basketball_processor.utils.constants module."""

import pytest
from datetime import datetime

from basketball_processor.utils.constants import (
    get_conference,
    get_conference_for_date,
    TEAM_ALIASES,
    CONFERENCES,
    CONFERENCE_HISTORY,
)


class TestGetConference:
    """Tests for get_conference function."""

    def test_direct_team_lookup(self):
        """Test direct team name lookup."""
        assert get_conference("Duke") == "ACC"
        assert get_conference("Kansas") == "Big 12"
        assert get_conference("Gonzaga") == "WCC"

    def test_team_not_found(self):
        """Test that unknown teams return None."""
        assert get_conference("Fake University") is None
        assert get_conference("") is None

    def test_aliased_team_lookup(self):
        """Test lookup via team aliases."""
        # UNC should resolve to North Carolina -> ACC
        assert get_conference("UNC") == "ACC"
        # Mizzou should resolve to Missouri -> SEC
        assert get_conference("Mizzou") == "SEC"


class TestGetConferenceForDate:
    """Tests for historical conference lookups."""

    def test_current_conference(self):
        """Test that None date returns current conference."""
        assert get_conference_for_date("UCLA") == "Big Ten"
        assert get_conference_for_date("Texas") == "SEC"

    def test_historical_pac12_teams(self):
        """Test Pac-12 teams before 2024 realignment."""
        # March 2024 - before July 1 realignment
        assert get_conference_for_date("UCLA", 20240315) == "Pac-12"
        assert get_conference_for_date("USC", 20240315) == "Pac-12"
        assert get_conference_for_date("Oregon", 20240315) == "Pac-12"
        assert get_conference_for_date("Washington", 20240315) == "Pac-12"

    def test_post_realignment(self):
        """Test conferences after July 2024 realignment."""
        # December 2024 - after realignment
        assert get_conference_for_date("UCLA", 20241201) == "Big Ten"
        assert get_conference_for_date("Texas", 20241201) == "SEC"
        assert get_conference_for_date("Arizona", 20241201) == "Big 12"

    def test_string_date_format(self):
        """Test various string date formats."""
        assert get_conference_for_date("UCLA", "2024-03-15") == "Pac-12"
        assert get_conference_for_date("UCLA", "20240315") == "Pac-12"
        assert get_conference_for_date("UCLA", "2024/03/15") == "Pac-12"

    def test_datetime_date_format(self):
        """Test datetime object input."""
        march_2024 = datetime(2024, 3, 15)
        assert get_conference_for_date("UCLA", march_2024) == "Pac-12"

        december_2024 = datetime(2024, 12, 1)
        assert get_conference_for_date("UCLA", december_2024) == "Big Ten"

    def test_uconn_journey(self):
        """Test UConn's Big East -> AAC -> Big East journey."""
        # Pre-2013: Big East
        assert get_conference_for_date("UConn", 20120315) == "Big East"
        # 2013-2020: AAC
        assert get_conference_for_date("UConn", 20150315) == "AAC"
        # 2020+: Big East again
        assert get_conference_for_date("UConn", 20220315) == "Big East"

    def test_colorado_history(self):
        """Test Colorado's multiple conference changes."""
        # Pre-2011: Big 12
        assert get_conference_for_date("Colorado", 20100315) == "Big 12"
        # 2011-2024: Pac-12
        assert get_conference_for_date("Colorado", 20150315) == "Pac-12"
        # 2024+: Big 12 again
        assert get_conference_for_date("Colorado", 20250115) == "Big 12"

    def test_team_without_history(self):
        """Test teams without historical data return current conference."""
        # Duke has always been ACC
        assert get_conference_for_date("Duke", 20100315) == "ACC"
        assert get_conference_for_date("Duke", 20240315) == "ACC"


class TestTeamAliases:
    """Tests for TEAM_ALIASES dictionary."""

    def test_common_nicknames(self):
        """Test common team nicknames."""
        assert TEAM_ALIASES.get("Ole Miss") == "Mississippi"
        assert TEAM_ALIASES.get("Mizzou") == "Missouri"
        assert TEAM_ALIASES.get("Zags") == "Gonzaga"

    def test_state_abbreviations(self):
        """Test state school abbreviations."""
        assert TEAM_ALIASES.get("UNC") == "North Carolina"
        assert TEAM_ALIASES.get("UVA") == "Virginia"
        assert TEAM_ALIASES.get("UK") == "Kentucky"

    def test_renamed_schools(self):
        """Test renamed/transitioned schools."""
        assert TEAM_ALIASES.get("IUPUI") == "IU Indianapolis"
        assert TEAM_ALIASES.get("Texas A&M-Commerce") == "East Texas A&M"

    def test_saint_variations(self):
        """Test Saint/St. variations."""
        assert TEAM_ALIASES.get("Saint Mary's") == "Saint Mary's (CA)"
        assert TEAM_ALIASES.get("St. Mary's") == "Saint Mary's (CA)"


class TestConferences:
    """Tests for CONFERENCES dictionary."""

    def test_power_conferences_exist(self):
        """Test that all power conferences are defined."""
        power_conferences = ["ACC", "Big Ten", "SEC", "Big 12", "Big East"]
        for conf in power_conferences:
            assert conf in CONFERENCES

    def test_conference_team_count(self):
        """Test that major conferences have expected team counts."""
        assert len(CONFERENCES["Big Ten"]) == 18
        assert len(CONFERENCES["SEC"]) == 16
        assert len(CONFERENCES["Big 12"]) == 16
        assert len(CONFERENCES["ACC"]) == 18

    def test_specific_team_memberships(self):
        """Test specific team conference memberships."""
        assert "Duke" in CONFERENCES["ACC"]
        assert "Kansas" in CONFERENCES["Big 12"]
        assert "Michigan" in CONFERENCES["Big Ten"]
        assert "Kentucky" in CONFERENCES["SEC"]


class TestConferenceHistory:
    """Tests for CONFERENCE_HISTORY dictionary."""

    def test_history_format(self):
        """Test that history entries are properly formatted."""
        for team, history in CONFERENCE_HISTORY.items():
            assert isinstance(history, list)
            for entry in history:
                assert len(entry) == 2
                assert isinstance(entry[0], int)
                assert isinstance(entry[1], str)

    def test_history_sorted(self):
        """Test that history entries are sorted by date."""
        for team, history in CONFERENCE_HISTORY.items():
            dates = [entry[0] for entry in history]
            assert dates == sorted(dates), f"{team} history not sorted"

    def test_recent_realignment_covered(self):
        """Test that 2024 realignment teams are covered."""
        realignment_teams = [
            "UCLA", "USC", "Oregon", "Washington",  # To Big Ten
            "Arizona", "Arizona State", "Colorado", "Utah",  # To Big 12
            "Texas", "Oklahoma",  # To SEC
            "California", "Stanford", "SMU",  # To ACC
        ]
        for team in realignment_teams:
            assert team in CONFERENCE_HISTORY, f"{team} missing from CONFERENCE_HISTORY"
