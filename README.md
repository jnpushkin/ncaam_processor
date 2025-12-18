# NCAA Basketball Game Processor

A Python tool for parsing Sports Reference HTML box scores and generating statistics for NCAA Division I basketball games.

## Features

- Parse HTML box scores from Sports Reference
- Track games attended for both men's and women's basketball
- Generate Excel workbooks with player/team statistics
- Generate interactive HTML website with:
  - Game log
  - Player statistics
  - Team records
  - Milestone tracking (double-doubles, 20+ point games, etc.)
  - Conference checklist (track which teams/arenas you've seen)
  - Gender filtering (Men's, Women's, or All)

## Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ncaam_processor.git
cd ncaam_processor

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
# Process HTML files from default directory
python3 -m basketball_processor

# Process specific directory
python3 -m basketball_processor /path/to/html/files

# Generate website only (skip Excel)
python3 -m basketball_processor --website-only

# Load from cache (skip HTML parsing)
python3 -m basketball_processor --from-cache-only
```

### Command Line Options

| Option | Description |
|--------|-------------|
| `--output-excel FILE` | Excel output filename (default: Basketball_Stats.xlsx) |
| `--gender M/W/both` | Filter by gender |
| `--save-json` | Save intermediate JSON data |
| `--from-cache-only` | Load from cached JSON instead of parsing HTML |
| `--excel-only` | Generate only Excel, skip website |
| `--website-only` | Generate only website, skip Excel |
| `--verbose` | Enable debug output |
| `--no-emoji` | Disable emoji in console output |

## Directory Structure

```
ncaam_processor/
├── basketball_processor/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── excel/               # Excel generation
│   ├── parsers/             # HTML parsing
│   ├── references/
│   │   └── venues.json      # Arena/venue data
│   ├── utils/
│   │   ├── constants.py     # Conference data, team codes
│   │   └── venue_resolver.py
│   └── website/             # HTML website generation
├── cache/                   # Cached parsed game data (gitignored)
├── html_games/              # Input HTML files (gitignored)
├── CONTRIBUTING.md          # Data maintenance guide
└── README.md
```

## Data Sources

- **Box scores:** Download HTML files from [Sports Reference](https://www.sports-reference.com/cbb/)
- **Conference data:** Based on [Wikipedia NCAA D1 Programs](https://en.wikipedia.org/wiki/List_of_NCAA_Division_I_men%27s_basketball_programs)
- **Arena data:** Based on [Wikipedia NCAA D1 Arenas](https://en.wikipedia.org/wiki/List_of_NCAA_Division_I_basketball_arenas)

## Maintaining Data

See [CONTRIBUTING.md](CONTRIBUTING.md) for instructions on:
- Updating team conferences
- Changing arena information
- Handling defunct programs
- Adding new conferences

## Conference Data (2025-26)

The processor includes all 31 NCAA Division I basketball conferences:
- Power conferences: ACC, Big Ten, SEC, Big 12, Big East
- Mid-majors: WCC, AAC, Mountain West, MVC, A-10, etc.
- All other D1 conferences

## License

MIT License
