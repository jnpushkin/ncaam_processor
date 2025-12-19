"""
Special events detection engine for basketball games.
"""

from typing import Dict, Any, List
from ..utils.helpers import safe_int


class SpecialEventsEngine:
    """Detect special events during games."""

    def __init__(self, game_data: Dict[str, Any]):
        self.game_data = game_data
        self.special_events = {
            'overtime_game': False,
            'overtime_periods': 0,
            'blowout': False,
            'blowout_margin': 0,
            'close_game': False,
            'buzzer_beater': False,
            'comeback_win': False,
            'comeback_deficit': 0,
        }

    def detect(self) -> Dict[str, Any]:
        """Run all special event detections."""
        self._detect_overtime()
        self._detect_blowout()
        self._detect_close_game()
        self._detect_comeback()

        self.game_data['special_events'] = self.special_events
        return self.game_data

    def _detect_overtime(self):
        """Detect overtime games."""
        linescore = self.game_data.get('linescore', {})

        # Check if either team has OT scores
        away_ot = linescore.get('away', {}).get('OT', [])
        home_ot = linescore.get('home', {}).get('OT', [])

        if away_ot or home_ot:
            self.special_events['overtime_game'] = True
            self.special_events['overtime_periods'] = max(len(away_ot), len(home_ot))

    def _detect_blowout(self):
        """Detect blowout games (20+ point margin)."""
        basic_info = self.game_data.get('basic_info', {})
        away_score = safe_int(basic_info.get('away_score', 0))
        home_score = safe_int(basic_info.get('home_score', 0))

        margin = abs(away_score - home_score)

        if margin >= 20:
            self.special_events['blowout'] = True
            self.special_events['blowout_margin'] = margin
            self.special_events['blowout_winner'] = 'away' if away_score > home_score else 'home'

    def _detect_close_game(self):
        """Detect close games (5 or fewer point margin)."""
        basic_info = self.game_data.get('basic_info', {})
        away_score = safe_int(basic_info.get('away_score', 0))
        home_score = safe_int(basic_info.get('home_score', 0))

        margin = abs(away_score - home_score)

        if margin <= 5:
            self.special_events['close_game'] = True
            self.special_events['final_margin'] = margin

    def _detect_comeback(self):
        """
        Detect comeback wins.

        A comeback is when a team overcomes a significant halftime deficit.
        For men's games (2 halves): halftime is after 1st half
        For women's games (4 quarters): halftime is after 2nd quarter
        """
        linescore = self.game_data.get('linescore', {})
        basic_info = self.game_data.get('basic_info', {})
        gender = self.game_data.get('gender', 'M')

        # Get periods - could be halves (men) or quarters (women)
        away_periods = linescore.get('away', {}).get('halves', []) or linescore.get('away', {}).get('quarters', [])
        home_periods = linescore.get('home', {}).get('halves', []) or linescore.get('home', {}).get('quarters', [])

        # Need at least 2 periods for halftime calculation
        if len(away_periods) < 2 or len(home_periods) < 2:
            return

        # Calculate halftime score
        # For men's: 1st half score, for women's: sum of 1st and 2nd quarters
        if gender == 'W' and len(away_periods) >= 2:
            away_halftime = away_periods[0] + away_periods[1]
            home_halftime = home_periods[0] + home_periods[1]
        else:
            away_halftime = away_periods[0]
            home_halftime = home_periods[0]

        # Final score
        away_final = safe_int(basic_info.get('away_score', 0))
        home_final = safe_int(basic_info.get('home_score', 0))

        # Check for comeback
        halftime_deficit_away = home_halftime - away_halftime
        halftime_deficit_home = away_halftime - home_halftime

        # Away team comeback
        if halftime_deficit_away >= 10 and away_final > home_final:
            self.special_events['comeback_win'] = True
            self.special_events['comeback_team'] = 'away'
            self.special_events['comeback_deficit'] = halftime_deficit_away

        # Home team comeback
        if halftime_deficit_home >= 10 and home_final > away_final:
            self.special_events['comeback_win'] = True
            self.special_events['comeback_team'] = 'home'
            self.special_events['comeback_deficit'] = halftime_deficit_home

    def get_game_summary(self) -> str:
        """Generate a summary string of special events."""
        events = []

        if self.special_events['overtime_game']:
            ot_periods = self.special_events['overtime_periods']
            if ot_periods == 1:
                events.append("OT")
            else:
                events.append(f"{ot_periods}OT")

        if self.special_events['blowout']:
            margin = self.special_events['blowout_margin']
            events.append(f"Blowout (+{margin})")

        if self.special_events['close_game']:
            events.append("Close game")

        if self.special_events['comeback_win']:
            deficit = self.special_events['comeback_deficit']
            events.append(f"Comeback ({deficit}-pt deficit)")

        return ", ".join(events) if events else ""
