"""
ESPN Boxscore API Parser

Fetches and parses game data from ESPN's API into the same format
as the Sports Reference HTML parser.
"""

import re
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

# ESPN API endpoints
ESPN_SUMMARY_URL = "https://site.api.espn.com/apis/site/v2/sports/basketball/{league}/summary"

def extract_game_id(url_or_id: str) -> Tuple[str, str]:
    """
    Extract ESPN game ID and determine league from URL or raw ID.

    Args:
        url_or_id: ESPN URL or game ID

    Returns:
        Tuple of (game_id, league) where league is 'mens-college-basketball' or 'womens-college-basketball'
    """
    # Default to men's
    league = "mens-college-basketball"

    # Check if it's a URL
    if "espn.com" in url_or_id:
        # Extract game ID from URL
        match = re.search(r'gameId[=/](\d+)', url_or_id)
        if match:
            game_id = match.group(1)
        else:
            raise ValueError(f"Could not extract game ID from URL: {url_or_id}")

        # Check for women's
        if "womens-college-basketball" in url_or_id or "/women" in url_or_id.lower():
            league = "womens-college-basketball"
    else:
        # Assume it's just the game ID
        game_id = url_or_id.strip()

    return game_id, league


def fetch_espn_game(game_id: str, league: str = "mens-college-basketball") -> Dict[str, Any]:
    """
    Fetch game data from ESPN API.

    Args:
        game_id: ESPN game ID
        league: 'mens-college-basketball' or 'womens-college-basketball'

    Returns:
        Raw ESPN API response
    """
    url = ESPN_SUMMARY_URL.format(league=league)
    params = {"event": game_id}

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def parse_espn_boxscore(espn_data: Dict[str, Any], gender: str = "M") -> Dict[str, Any]:
    """
    Parse ESPN API response into the standard game data format.

    Args:
        espn_data: Raw ESPN API response
        gender: 'M' or 'W'

    Returns:
        Game data in standard format compatible with HTML parser output
    """
    header = espn_data.get("header", {})
    boxscore = espn_data.get("boxscore", {})

    # Get competition info
    competitions = header.get("competitions", [{}])
    comp = competitions[0] if competitions else {}

    # Get competitors (teams with scores)
    competitors = comp.get("competitors", [])
    away_comp = next((c for c in competitors if c.get("homeAway") == "away"), {})
    home_comp = next((c for c in competitors if c.get("homeAway") == "home"), {})

    # Parse date
    date_str = comp.get("date", "")
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        date_display = dt.strftime("%B %d, %Y")
        date_yyyymmdd = dt.strftime("%Y%m%d")
    except:
        date_display = date_str
        date_yyyymmdd = ""

    # Get venue info
    venue_info = comp.get("venue", {})
    venue_name = venue_info.get("fullName", "")
    venue_address = venue_info.get("address", {})
    city = venue_address.get("city", "")
    state = venue_address.get("state", "")

    # Build venue string
    venue_parts = [venue_name]
    if city:
        venue_parts.append(city)
    if state:
        venue_parts.append(state)
    venue = ", ".join(filter(None, venue_parts))

    # Get team names
    away_team_info = away_comp.get("team", {})
    home_team_info = home_comp.get("team", {})

    away_team = away_team_info.get("displayName", "").replace(" Lions", "").replace(" Dons", "").replace(" Bulldogs", "")
    home_team = home_team_info.get("displayName", "").replace(" Lions", "").replace(" Dons", "").replace(" Bulldogs", "")

    # Clean up team names (remove mascot)
    away_team = clean_team_name(away_team_info.get("displayName", ""))
    home_team = clean_team_name(home_team_info.get("displayName", ""))

    # Get scores
    away_score = int(away_comp.get("score", 0))
    home_score = int(home_comp.get("score", 0))

    # Build basic info
    basic_info = {
        "away_team": away_team,
        "home_team": home_team,
        "away_score": away_score,
        "home_score": home_score,
        "date": date_display,
        "date_yyyymmdd": date_yyyymmdd,
        "venue": venue,
        "city": city,
        "state": state,
        "attendance": comp.get("attendance"),
        "away_record": away_comp.get("record", [{}])[0].get("summary", "") if away_comp.get("record") else "",
        "home_record": home_comp.get("record", [{}])[0].get("summary", "") if home_comp.get("record") else "",
        "espn_game_id": comp.get("id", ""),
        "away_team_code": away_team_info.get("abbreviation", ""),
        "home_team_code": home_team_info.get("abbreviation", ""),
        "away_espn_id": away_team_info.get("id", ""),
        "home_espn_id": home_team_info.get("id", ""),
        "gender": gender,
        "division": "D1",  # ESPN only has D1
        "source": "espn"
    }

    # Parse box scores
    players_data = boxscore.get("players", [])
    away_players = []
    home_players = []

    for team_data in players_data:
        team_info = team_data.get("team", {})
        is_home = team_info.get("id") == home_team_info.get("id")

        stats_list = team_data.get("statistics", [])
        if stats_list:
            labels = stats_list[0].get("labels", [])
            athletes = stats_list[0].get("athletes", [])

            for athlete in athletes:
                if athlete.get("didNotPlay"):
                    continue

                player_info = athlete.get("athlete", {})
                stats = athlete.get("stats", [])

                # Map stats to our format
                player = parse_player_stats(player_info, stats, labels, athlete.get("starter", False))

                if is_home:
                    home_players.append(player)
                else:
                    away_players.append(player)

    # Parse team totals
    teams_data = boxscore.get("teams", [])
    away_totals = {}
    home_totals = {}

    for team_data in teams_data:
        team_info = team_data.get("team", {})
        is_home = team_info.get("id") == home_team_info.get("id")

        totals = parse_team_totals(team_data.get("statistics", []))

        if is_home:
            home_totals = totals
        else:
            away_totals = totals

    # Parse linescore if available
    linescore = parse_linescore(espn_data)

    # Build final game data
    game_data = {
        "basic_info": basic_info,
        "box_score": {
            "away": {"players": away_players},
            "home": {"players": home_players}
        },
        "team_totals": {
            "away": away_totals,
            "home": home_totals
        },
        "linescore": linescore,
        "officials": parse_officials(espn_data),
        "source": "espn",
        "espn_game_id": comp.get("id", "")
    }

    return game_data


def clean_team_name(full_name: str) -> str:
    """Remove mascot from team name."""
    # Common patterns
    mascots = [
        "Lions", "Dons", "Bulldogs", "Tigers", "Bears", "Wildcats", "Eagles",
        "Cardinals", "Cavaliers", "Huskies", "Bruins", "Trojans", "Gators",
        "Seminoles", "Hurricanes", "Blue Devils", "Tar Heels", "Wolfpack",
        "Volunteers", "Crimson Tide", "Fighting Irish", "Spartans", "Wolverines",
        "Buckeyes", "Hoosiers", "Boilermakers", "Jayhawks", "Mountaineers",
        "Gaels", "Toreros", "Broncos", "Pilots", "Waves", "Cougars", "Zags",
        "Golden Bears", "Cardinal"
    ]

    name = full_name
    for mascot in mascots:
        if name.endswith(" " + mascot):
            name = name[:-len(mascot)-1]
            break

    return name.strip()


def parse_player_stats(player_info: Dict, stats: list, labels: list, starter: bool) -> Dict[str, Any]:
    """Parse individual player stats from ESPN format."""
    # Create label to index mapping
    label_map = {label.upper(): i for i, label in enumerate(labels)}

    def get_stat(label: str, default: Any = 0) -> Any:
        idx = label_map.get(label.upper())
        if idx is not None and idx < len(stats):
            val = stats[idx]
            if val == "--" or val == "":
                return default
            return val
        return default

    def parse_made_att(val: str) -> Tuple[int, int]:
        """Parse '5-10' format to (made, attempted)."""
        if not val or val == "--":
            return 0, 0
        parts = val.split("-")
        if len(parts) == 2:
            try:
                return int(parts[0]), int(parts[1])
            except:
                pass
        return 0, 0

    # Parse shooting stats
    fg_made, fg_att = parse_made_att(get_stat("FG", "0-0"))
    fg3_made, fg3_att = parse_made_att(get_stat("3PT", "0-0"))
    ft_made, ft_att = parse_made_att(get_stat("FT", "0-0"))

    # Get other stats
    try:
        minutes = int(get_stat("MIN", 0))
    except:
        minutes = 0

    try:
        points = int(get_stat("PTS", 0))
    except:
        points = 0

    return {
        "name": player_info.get("displayName", ""),
        "player_id": None,  # ESPN doesn't give us SR-compatible IDs
        "espn_id": player_info.get("id"),
        "starter": starter,
        "mp": minutes,
        "fg": fg_made,
        "fga": fg_att,
        "fg3": fg3_made,
        "fg3a": fg3_att,
        "ft": ft_made,
        "fta": ft_att,
        "orb": int(get_stat("OREB", 0)) if get_stat("OREB", 0) != "--" else 0,
        "drb": int(get_stat("DREB", 0)) if get_stat("DREB", 0) != "--" else 0,
        "trb": int(get_stat("REB", 0)) if get_stat("REB", 0) != "--" else 0,
        "ast": int(get_stat("AST", 0)) if get_stat("AST", 0) != "--" else 0,
        "stl": int(get_stat("STL", 0)) if get_stat("STL", 0) != "--" else 0,
        "blk": int(get_stat("BLK", 0)) if get_stat("BLK", 0) != "--" else 0,
        "tov": int(get_stat("TO", 0)) if get_stat("TO", 0) != "--" else 0,
        "pf": int(get_stat("PF", 0)) if get_stat("PF", 0) != "--" else 0,
        "pts": points
    }


def parse_team_totals(statistics: list) -> Dict[str, Any]:
    """Parse team total statistics."""
    totals = {}

    for stat in statistics:
        label = stat.get("label", "").lower().replace(" ", "_")
        value = stat.get("displayValue", "")

        # Map to our format
        if label == "fg":
            parts = value.split("-")
            if len(parts) == 2:
                totals["fg"] = int(parts[0])
                totals["fga"] = int(parts[1])
        elif label == "3pt":
            parts = value.split("-")
            if len(parts) == 2:
                totals["fg3"] = int(parts[0])
                totals["fg3a"] = int(parts[1])
        elif label == "ft":
            parts = value.split("-")
            if len(parts) == 2:
                totals["ft"] = int(parts[0])
                totals["fta"] = int(parts[1])
        elif label == "rebounds":
            totals["trb"] = int(value) if value else 0
        elif label == "offensive_rebounds":
            totals["orb"] = int(value) if value else 0
        elif label == "defensive_rebounds":
            totals["drb"] = int(value) if value else 0
        elif label == "assists":
            totals["ast"] = int(value) if value else 0
        elif label == "steals":
            totals["stl"] = int(value) if value else 0
        elif label == "blocks":
            totals["blk"] = int(value) if value else 0
        elif label == "turnovers":
            totals["tov"] = int(value) if value else 0
        elif label == "fouls":
            totals["pf"] = int(value) if value else 0
        elif label == "points":
            totals["pts"] = int(value) if value else 0

    return totals


def parse_linescore(espn_data: Dict) -> Dict[str, Any]:
    """Parse period-by-period scoring."""
    header = espn_data.get("header", {})
    competitions = header.get("competitions", [{}])
    comp = competitions[0] if competitions else {}

    competitors = comp.get("competitors", [])

    linescore = {
        "away": {"halves": [], "OT": [], "total": 0},
        "home": {"halves": [], "OT": [], "total": 0}
    }

    for competitor in competitors:
        is_home = competitor.get("homeAway") == "home"
        key = "home" if is_home else "away"

        linescores = competitor.get("linescores", [])
        halves = []
        ot = []

        for i, period in enumerate(linescores):
            score = int(period.get("value", 0))
            if i < 2:  # First two periods are halves
                halves.append(score)
            else:  # OT periods
                ot.append(score)

        linescore[key]["halves"] = halves
        linescore[key]["OT"] = ot
        linescore[key]["total"] = int(competitor.get("score", 0))

    return linescore


def parse_officials(espn_data: Dict) -> list:
    """Parse officials from ESPN data."""
    # ESPN doesn't always include officials in the summary endpoint
    # Would need to check game info endpoint
    return []


def get_espn_game(url_or_id: str) -> Dict[str, Any]:
    """
    Main entry point - fetch and parse an ESPN game.

    Args:
        url_or_id: ESPN URL or game ID

    Returns:
        Parsed game data in standard format
    """
    game_id, league = extract_game_id(url_or_id)
    gender = "W" if "womens" in league else "M"

    espn_data = fetch_espn_game(game_id, league)
    game_data = parse_espn_boxscore(espn_data, gender)

    return game_data


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python espn_boxscore.py <espn_url_or_game_id>")
        sys.exit(1)

    game_data = get_espn_game(sys.argv[1])
    print(json.dumps(game_data, indent=2))
