"""NBA schedule, matchup, and player box-score queries extracted from the original notebook."""

import argparse
import json
import re
import requests
from pathlib import Path
from datetime import timezone
from dateutil import parser
from nba_api.live.nba.endpoints import boxscore, scoreboard
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import players, teams


def _call_endpoint(factory, **kwargs):
    try:
        return factory(**kwargs)
    except requests.RequestException:
        raise RuntimeError(
            "NBA request failed. The endpoint may be unavailable or blocking this network; try the offline sample."
        ) from None


def get_today_games():
    board = _call_endpoint(scoreboard.ScoreBoard, timeout=20)
    games = board.games.get_dict()

    today_games = []

    for game in games:
        try:
            utc_time = parser.parse(game["gameTimeUTC"])
            local_time = (
                utc_time.replace(tzinfo=timezone.utc)
                if utc_time.tzinfo is None
                else utc_time
            ).astimezone()
        except (ValueError, TypeError, KeyError):
            local_time = None

        today_games.append(
            {
                "game_id": game.get("gameId"),
                "away_team": game.get("awayTeam", {}).get("teamName"),
                "home_team": game.get("homeTeam", {}).get("teamName"),
                "local_time": local_time,
            }
        )

    return today_games


def print_today_games():
    lines = []
    for game in get_today_games():
        time = (
            game["local_time"].strftime("%I:%M %p").lstrip("0")
            if game["local_time"]
            else "TBD"
        )
        lines.append(
            f"{game['game_id']} | {game['away_team']} @ {game['home_team']} | {time}"
        )
    result = "\n".join(lines) or "No games found today."
    print(result)
    return result


def get_player_by_name(full_name):
    nba_players = players.get_players()
    for player in nba_players:
        if player["full_name"].casefold() == full_name.strip().casefold():
            return player
    raise ValueError(f"Player not found: {full_name}")


def get_team_by_abbrev(abbrev):
    nba_teams = teams.get_teams()
    for team in nba_teams:
        if team["abbreviation"] == abbrev.strip().upper():
            return team
    raise ValueError(f"Team abbreviation not found: {abbrev}")


def get_team_games(team_id, season=None):
    if season is not None:
        season = str(season)
        if re.fullmatch(r"\d{4}", season):
            season = f"{season}-{(int(season) + 1) % 100:02d}"
        if not re.fullmatch(r"\d{4}-\d{2}", season):
            raise ValueError("Use a season start year or YYYY-YY.")
    finder = _call_endpoint(
        leaguegamefinder.LeagueGameFinder,
        team_id_nullable=team_id,
        season_nullable=season or "",
        timeout=20,
    )
    games = finder.get_data_frames()[0]
    return games.sort_values("GAME_DATE", ascending=False).reset_index(drop=True)


def get_last_n_games(team_id, n=5, season=None):
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise ValueError("n must be a positive integer.")
    return get_team_games(team_id, season).head(n)


def get_last_matchup(team_id, opponent_abbrev, season=None):
    games = get_team_games(team_id, season)
    opponent_games = games[
        games.MATCHUP.str.split().str[-1].eq(opponent_abbrev.strip().upper())
    ]

    if opponent_games.empty:
        raise ValueError("No matchups found.")

    return opponent_games.sort_values("GAME_DATE", ascending=False).iloc[0]


def get_full_game_data(game_id):
    if not re.fullmatch(r"\d{10}", str(game_id)):
        raise ValueError("Game ID must be a ten-digit string, including leading zeros.")
    box = _call_endpoint(boxscore.BoxScore, game_id=str(game_id), timeout=20)
    full_box = box.game.get_dict()
    return full_box


def get_player_box_score(game_dict, player_id):
    home_players = game_dict.get("homeTeam", {}).get("players", [])
    away_players = game_dict.get("awayTeam", {}).get("players", [])

    for p in home_players:
        if str(p.get("personId")) == str(player_id):
            return {
                "teamTricode": game_dict["homeTeam"].get("teamTricode"),
                "side": "home",
                "player": p,
            }

    for p in away_players:
        if str(p.get("personId")) == str(player_id):
            return {
                "teamTricode": game_dict["awayTeam"].get("teamTricode"),
                "side": "away",
                "player": p,
            }

    return None


def summarize_player_box(player_result):
    if not player_result:
        return "Player not found in this game."

    player = player_result["player"]
    stats = player.get("statistics", {})

    def stat(key):
        return stats.get(key, "N/A")

    name = (
        player.get("name")
        or (f"{player.get('firstName', '')} {player.get('familyName', '')}").strip()
    )

    return "\n".join(
        [
            f"{name} | {player_result['teamTricode']} ({player_result['side']})",
            f"MIN: {stat('minutes')}",
            f"PTS: {stat('points')}",
            f"REB: {stat('reboundsTotal')}",
            f"AST: {stat('assists')}",
            f"BLK: {stat('blocks')}",
            f"3PM: {stat('threePointersMade')}",
            f"+/-: {stat('plusMinusPoints')}",
        ]
    )


def run_player_query(player_name, team_abbrev, opponent_abbrev, season=None):
    player = get_player_by_name(player_name)
    team = get_team_by_abbrev(team_abbrev)

    last_game = get_last_matchup(team["id"], opponent_abbrev, season)
    game_dict = get_full_game_data(last_game.GAME_ID)
    player_result = get_player_box_score(game_dict, player["id"])

    summary = summarize_player_box(player_result)
    print(summary)

    return {
        "player": player,
        "team": team,
        "last_matchup": last_game,
        "game_dict": game_dict,
        "player_result": player_result,
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument(
        "--sample",
        action="store_true",
        help="Show a fictional box score without network calls",
    )
    cli.add_argument(
        "--today", action="store_true", help="List current games from the live endpoint"
    )
    cli.add_argument("--player", help="Exact player name (case-insensitive)")
    cli.add_argument("--game-id", help="Ten-digit game ID")
    cli.add_argument("--team", help="Team abbreviation for game history")
    cli.add_argument("--last", type=int, default=5)
    cli.add_argument("--season", help="Season start year or YYYY-YY")
    args = cli.parse_args()
    try:
        if args.sample:
            game = json.loads(
                (Path(__file__).parent / "data/sample_boxscore.json").read_text()
            )
            print("Synthetic fixture: fictional player and game.")
            print(summarize_player_box(get_player_box_score(game, 900001)))
        elif args.today:
            print_today_games()
        elif args.player and args.game_id:
            player = get_player_by_name(args.player)
            print(
                summarize_player_box(
                    get_player_box_score(get_full_game_data(args.game_id), player["id"])
                )
            )
        elif args.team:
            team = get_team_by_abbrev(args.team)
            print(
                get_last_n_games(team["id"], args.last, args.season).to_string(
                    index=False
                )
            )
        else:
            cli.error("Choose --sample, --today, --team, or --player with --game-id.")
    except (ValueError, KeyError, RuntimeError) as exc:
        cli.error(str(exc))


if __name__ == "__main__":
    main()
