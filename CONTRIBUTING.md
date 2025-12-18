# Contributing & Data Maintenance Guide

This document explains how to update the basketball processor when team information changes.

## Reference Data Locations

| Data Type | File Location |
|-----------|---------------|
| Conference membership | `basketball_processor/utils/constants.py` → `_DEFAULT_CONFERENCES` |
| Team aliases | `basketball_processor/utils/constants.py` → `TEAM_ALIASES` |
| Home arenas | `basketball_processor/references/venues.json` → `home_arenas` |
| Game-specific venue overrides | `basketball_processor/references/venues.json` → `game_overrides` |

## Common Update Scenarios

### 1. Team Changes Conference

**Example:** Delaware moves from CAA to Conference USA

Edit `basketball_processor/utils/constants.py`:

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

## Annual Update Checklist (July 1)

Conference realignment typically takes effect July 1. Each year:

1. [ ] Check Wikipedia for conference changes
2. [ ] Update `_DEFAULT_CONFERENCES` in `constants.py`
3. [ ] Update `home_arenas` in `venues.json` for any arena changes
4. [ ] Add aliases for renamed teams
5. [ ] Remove defunct programs
6. [ ] Clear cache and regenerate to verify
