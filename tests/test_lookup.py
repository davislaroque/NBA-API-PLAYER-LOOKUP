from datetime import datetime, timezone
from types import SimpleNamespace
import json
from pathlib import Path
import pandas as pd
import pytest
import nba_lookup as lookup


def test_print_today_games_includes_every_game(monkeypatch, capsys):
    games = [
        {
            "game_id": str(n),
            "home_team": "Home",
            "away_team": "Away",
            "local_time": None,
        }
        for n in [1, 2]
    ]
    monkeypatch.setattr(lookup, "get_today_games", lambda: games)
    result = lookup.print_today_games()
    assert len(result.splitlines()) == 2
    assert "2 | Away @ Home" in capsys.readouterr().out


def test_player_lookup_normalizes_case_and_whitespace(monkeypatch):
    monkeypatch.setattr(
        lookup.players, "get_players", lambda: [{"id": 1, "full_name": "Alex Demo"}]
    )
    assert lookup.get_player_by_name("  alex demo  ")["id"] == 1
    with pytest.raises(ValueError, match="Player not found"):
        lookup.get_player_by_name("Missing")


def test_boxscore_parsing_accepts_string_id_and_missing_player():
    game = json.loads(
        (Path(__file__).parents[1] / "data/sample_boxscore.json").read_text()
    )
    assert "PTS: 21" in lookup.summarize_player_box(
        lookup.get_player_box_score(game, "900001")
    )
    assert lookup.get_player_box_score(game, 999) is None


def test_recent_games_are_sorted_and_season_sent_to_api(monkeypatch):
    calls = []
    frame = pd.DataFrame({"GAME_DATE": ["2025-01-02", "2025-01-05", "2025-01-03"]})

    def finder(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(get_data_frames=lambda: [frame])

    monkeypatch.setattr(lookup.leaguegamefinder, "LeagueGameFinder", finder)
    result = lookup.get_last_n_games(1, 2, "2025")
    assert result.GAME_DATE.tolist() == ["2025-01-05", "2025-01-03"]
    assert calls[0]["season_nullable"] == "2025-26"
    assert calls[0]["timeout"] == 20


def test_preserves_explicit_timezone_offsets(monkeypatch):
    game = {"gameId": "1", "gameTimeUTC": "2025-01-01T20:00:00+02:00"}
    monkeypatch.setattr(
        lookup.scoreboard,
        "ScoreBoard",
        lambda **kwargs: SimpleNamespace(
            games=SimpleNamespace(get_dict=lambda: [game])
        ),
    )
    actual = lookup.get_today_games()[0]["local_time"].astimezone(timezone.utc)
    assert actual == datetime(2025, 1, 1, 18, tzinfo=timezone.utc)
