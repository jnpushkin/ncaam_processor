# Contributing & Data Maintenance Guide

This document explains how to update the basketball processor when team information changes.

## Reference Data Locations

| Data Type | File Location |
|-----------|---------------|
| Conference membership | `basketball_processor/utils/constants.py` → `_DEFAULT_CONFERENCES` |
| Historical conferences | `basketball_processor/utils/constants.py` → `CONFERENCE_HISTORY` |
| Team aliases | `basketball_processor/utils/constants.py` → `TEAM_ALIASES` |
| Home arenas | `basketball_processor/references/venues.json` → `home_arenas` |
| Game-specific venue overrides | `basketball_processor/references/venues.json` → `game_overrides` |

## Common Update Scenarios

### 1. Team Changes Conference

**Example:** Delaware moves from CAA to Conference USA

**Step 1:** Update current conference in `_DEFAULT_CONFERENCES`:

```python
# REMOVE from old conference
'CAA': [
    'Campbell', 'Charleston', 'Delaware',  # <- Remove this
    ...
],

# ADD to new conference
'Conference USA': [
    'Delaware',  # <- Add this
    ...
],
```

**Step 2:** Add historical tracking in `CONFERENCE_HISTORY`:

```python
CONFERENCE_HISTORY = {
    'Delaware': [
        (20010701, 'CAA'),       # When they joined CAA
        (20250701, 'Conference USA'),  # When they move to C-USA
    ],
    ...
}
```

This ensures historical games show Delaware in the CAA, while future games show Conference USA.

### 2. Team Changes Arena

**Example:** Kentucky women move to Memorial Coliseum

Edit `basketball_processor/references/venues.json`:

```json
// Single arena (both genders)
"Kentucky": "Rupp Arena, Lexington, Kentucky"

// Different arenas by gender
"Kentucky": {
    "M": "Rupp Arena, Lexington, Kentucky",
    "W": "Memorial Coliseum, Lexington, Kentucky"
}
```

**Important:** Only use the M/W format when men's and women's teams play in DIFFERENT arenas.

### 3. Team Goes Defunct

**Example:** St. Francis Brooklyn discontinued basketball

1. **Remove from conference** in `constants.py`:
```python
'NEC': [
    ...,
    'St. Francis (NY)',  # <- Remove this line
    ...
],
```

2. **Remove from venues.json** (optional - can keep for historical games):
```json
// Remove this entry if desired
"St. Francis (NY)": "Pope Physical Education Center, Brooklyn Heights, New York"
```

3. **Keep alias** in `TEAM_ALIASES` if needed for historical data matching.

### 4. Team Renames

**Example:** Texas A&M-Commerce becomes East Texas A&M

1. **Update conference listing** in `constants.py`:
```python
'Southland': [
    'East Texas A&M',  # Use new name
    ...
],
```

2. **Add alias** for old name:
```python
TEAM_ALIASES = {
    'Texas A&M-Commerce': 'East Texas A&M',
    ...
}
```

3. **Update venues.json** with new name (keep old as alias if needed).

### 5. New Conference Added

**Example:** Adding Conference USA

In `constants.py`, add to `_DEFAULT_CONFERENCES`:

```python
'Conference USA': [
    'Delaware', 'FIU', 'Jacksonville State', 'Kennesaw State', 'Liberty',
    'Louisiana Tech', 'Middle Tennessee', 'Missouri State', 'New Mexico State',
    'Sam Houston', 'UTEP', 'Western Kentucky'
],
```

### 6. Game-Specific Venue Override

**Example:** USF plays at Chase Center instead of home arena

Edit `basketball_processor/references/venues.json`:

```json
"game_overrides": {
    "20241121-usf": "Chase Center, San Francisco, California"
}
```

**Game ID format:** `YYYYMMDD-team` where team is lowercase abbreviated (e.g., `usf`, `uva`, `unc`)

## Schools with Different Men's/Women's Arenas (2025-26)

| School | Men's Arena | Women's Arena |
|--------|-------------|---------------|
| Connecticut/UConn | Gampel Pavilion | PeoplesBank Arena (Hartford) |
| Georgetown | Capital One Arena | McDonough Arena |
| Kentucky | Rupp Arena | Memorial Coliseum |
| NC State | PNC Arena | Reynolds Coliseum |
| North Carolina | Dean Smith Center | Carmichael Arena |
| Seton Hall | Prudential Center | Walsh Gymnasium |
| St. John's | Madison Square Garden | Carnesecca Arena |

## Authoritative Sources

Use these Wikipedia pages as the primary source of truth:

- **Conference membership:** https://en.wikipedia.org/wiki/List_of_NCAA_Division_I_men%27s_basketball_programs
- **Arena information:** https://en.wikipedia.org/wiki/List_of_NCAA_Division_I_basketball_arenas

## After Making Changes

1. **Clear cache** to regenerate data:
   ```bash
   rm -rf cache/*.json
   ```

2. **Regenerate website**:
   ```bash
   python3 -c "from basketball_processor.main import main; import sys; sys.argv = ['', '--website-only', '--from-cache-only']; main()"
   ```

3. **Verify changes** in the generated HTML file.

## Historical Conference Tracking

The system tracks which conference each team was in at any point in time. This allows historical games to display the correct conference, even after realignment.

### How It Works

The `CONFERENCE_HISTORY` dictionary in `constants.py` stores conference membership changes:

```python
CONFERENCE_HISTORY = {
    'UCLA': [
        (19280101, 'Pac-12'),    # Date format: YYYYMMDD
        (20240701, 'Big Ten'),   # July 1, 2024 - moved to Big Ten
    ],
}
```

When processing a game, the system uses `get_conference_for_date(team, game_date)` to find the most recent conference assignment before the game date.

### Adding Historical Data

Only teams that have changed conferences need entries. Format:

```python
'Team Name': [
    (YYYYMMDD, 'Conference'),  # Oldest first
    (YYYYMMDD, 'Conference'),  # Newest last
],
```

### Major Realignment Already Tracked

The following realignments are pre-populated:
- **2024-25**: Pac-12 dissolution (UCLA, USC, Oregon, Washington to Big Ten; Arizona schools, Colorado, Utah to Big 12; Cal, Stanford to ACC)
- **2024-25**: Texas, Oklahoma to SEC
- **2023-24**: BYU, Houston, Cincinnati, UCF to Big 12
- **2020**: UConn back to Big East
- **2013-14**: Big East/AAC split, ACC expansion

## Annual Update Checklist (July 1)

Conference realignment typically takes effect July 1. Each year:

1. [ ] Check Wikipedia for conference changes
2. [ ] Update `_DEFAULT_CONFERENCES` in `constants.py`
3. [ ] Add entries to `CONFERENCE_HISTORY` for any teams changing conferences
4. [ ] Update `home_arenas` in `venues.json` for any arena changes
5. [ ] Add aliases for renamed teams
6. [ ] Remove defunct programs
7. [ ] Clear cache and regenerate to verify
