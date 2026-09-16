# NBA API Player Lookup

Query NBA schedules, recent team games, and individual player box scores with Python. This project began as a notebook for answering specific basketball questions, then extracted those queries into reusable functions and a command-line interface.

**Python · API integration · pandas · JSON parsing · date/time handling · pytest**

## Quick start

Use Python 3.11 or 3.12 and run commands from the repository root.

```bash
git clone https://github.com/davislaroque/NBA-API-PLAYER-LOOKUP.git
cd NBA-API-PLAYER-LOOKUP
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python nba_lookup.py --sample
python -m pytest -q
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`.

The sample is a small, explicitly fictional box score. It demonstrates parsing and formatting without network access or credentials.

## Live queries

```bash
python nba_lookup.py --today
python nba_lookup.py --team SAS --last 5 --season 2025
python nba_lookup.py --player "Victor Wembanyama" --game-id 0022500523
```

The game ID above comes from the original exploration; availability depends on the upstream endpoint. For another game, get a current ID from the schedule or team history. Preserve leading zeros in IDs.

```python
from nba_lookup import run_player_query

result = run_player_query(
    player_name="Victor Wembanyama",
    team_abbrev="SAS",
    opponent_abbrev="LAL",
    season="2025",
)
```

This resolves player/team IDs, filters the team's latest matchup against the opponent, fetches that game's box score, and returns both source data and a player summary.

## Implementation

| File | Purpose |
| --- | --- |
| [nba_lookup.py](nba_lookup.py) | Importable schedule, history, matchup, and player-stat helpers plus CLI |
| [Notebook](nba_api_queryV1.ipynb) | Short offline walkthrough and opt-in live examples |
| [Sample box score](data/sample_boxscore.json) | Fictional data for a repeatable demo |
| [Tests](tests/test_lookup.py) | Multi-game output, sorting, season forwarding, and safe player lookup |

Requests use 20-second timeouts. Season filters are sent to the API, rather than downloading the entire league history. Missing players and matchups produce clear errors; a player absent from a particular box score returns a readable message. Time conversion preserves existing timezone offsets.

## Limits

[nba_api](https://github.com/swar/nba_api) is a community Python client for NBA endpoints. Live endpoints can be unavailable, slow, or restricted in some environments. Offline checks validate the local logic; they do not establish live endpoint uptime. This repository retrieves and summarizes data; the [sports prediction project](https://github.com/davislaroque/Sports_Prediction_Model) handles model evaluation.
