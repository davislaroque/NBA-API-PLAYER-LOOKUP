#!/usr/bin/env python
# coding: utf-8

# In[1]:


#pip install nba_api
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
from nba_api.live.nba.endpoints import boxscore


# In[41]:


#Gets the lineup for all the next NBA games

# Query nba.live.endpoints.scoreboard and  list games in localTimeZone
from datetime import datetime, timezone
from dateutil import parser
from nba_api.live.nba.endpoints import scoreboard

f = "{gameId}: {awayTeam} vs. {homeTeam} @ {gameTimeLTZ}" 

board = scoreboard.ScoreBoard()
print("ScoreBoardDate: " + board.score_board_date)
games = board.games.get_dict()
for game in games:
    gameTimeLTZ = parser.parse(game["gameTimeUTC"]).replace(tzinfo=timezone.utc).astimezone(tz=None)
    print(f.format(gameId=game['gameId'], awayTeam=game['awayTeam']['teamName'], homeTeam=game['homeTeam']['teamName'], gameTimeLTZ=gameTimeLTZ))


# In[2]:


# sets up list of teams -- get_teams returns a list of 30 dictionaries, each an NBA team.
nba_teams = teams.get_teams()


# In[3]:


# sets up list of players -- get_players returns a list of dictionaries, each representing a player.

from nba_api.stats.static import players
nba_players = players.get_players()


# In[42]:


#finds id for your target players  -- change the players name
target_player = [
    player for player in nba_players if player["full_name"] == "Victor Wembanyama"
][0]
target_player


# In[43]:


#Gets the target teams ID  - change team abbrevation

target_team = [team for team in nba_teams if team['abbreviation'] == 'SAS'][0]
target_team_id = target_team['id']
target_team_name = target_team["full_name"]

res = f"The id for the {target_team_name} is {target_team_id}"
print(res)


# In[44]:


# Query for the last 5 games of the target team

gamefinder = leaguegamefinder.LeagueGameFinder(team_id_nullable=target_team_id)


games = gamefinder.get_data_frames()[0]
games.head()


# In[46]:


# Use this block to subset  the games to when the last 4 digits of SEASON_ID were a certain year of playing

# games.groupby(games.SEASON_ID.str[-4:])[['GAME_ID']].count().loc['2025':]
# games_2025 = games[games.SEASON_ID.str[-4:] == '2025']
# games_2025.head()


# In[48]:


# Subset all the games to where MATCHUP contains target opponent's abbreviation 
# in the target season from above: Ex. GSW'.

target_opponent_games_2025 = games_2025[games_2025.MATCHUP.str.contains('LAL')]
target_opponent_games_2025


# In[51]:


#Search for the most recent game against the target opponent in an easy to read pandas series

last_target_game = target_opponent_games_2025.sort_values('GAME_DATE').iloc[-1]
last_target_game


# In[50]:


# To get both teams game stats
# Get all the games so we can filter to an individual GAME_ID
# Find the game_id we want

game_id = last_target_game.GAME_ID


result = leaguegamefinder.LeagueGameFinder()
all_games = result.get_data_frames()[0]

full_game = all_games[all_games.GAME_ID == game_id]
full_game


# In[66]:


#Function to get the individual player box score

        
def get_player_box_score_from_game(game_dict, player_id):
    # pull the two player lists safely
    home_players = game_dict.get("homeTeam", {}).get("players", [])
    away_players = game_dict.get("awayTeam", {}).get("players", [])

    # search both
    for p in home_players + away_players:
        if p.get("personId") == player_id:
            return p

    return None
        


# In[73]:


#All box score functions for a specific gameid
#CHANGE THE GAME ID AND THE PLAYER ID



# Data Sets
#box.game.get_dict()                   #equal to box.get_dict()['game']
#box.arena.get_dict()                  #equal to box.get_dict()['game']['arena']
#box.away_team.get_dict()              #equal to box.get_dict()['game']['awayTeam']
#box.away_team_player_stats.get_dict() #equal to box.get_dict()['game']['awayTeam']['players']
#box.away_team_stats.get_dict()        #equal to box.get_dict()['game']['homeTeam'] w/o ['players']
#box.home_team.get_dict()              #equal to box.get_dict()['game']['homeTeam']
#box.home_team_player_stats.get_dict() #equal to box.get_dict()['game']['homeTeam']['players']
#box.home_team_stats.get_dict()        #equal to box.get_dict()['game']['homeTeam'] w/o ['players']
#box.game_details.get_dict()           #equal to box.get_dict()['game'] scrubbed of all other dictionaries
#box.officials.get_dict()              #equal to box.get_dict()['game']['officials']


target_player = [
    player for player in nba_players if player["full_name"] == "Victor Wembanyama"
][0]
print(target_player)


box = boxscore.BoxScore('0022500523') 

full_box = box.game.get_dict()
#full_box

player_box = get_player_box_score_from_game(full_box, 1641705)
player_box




# In[53]:


# from nba_api.live.nba.endpoints import Odds
# import json

# # Fetch odds data
# odds = Odds()
# games_list = odds.get_games().get_dict()

# # Print first 2 games with nice formatting
# print(json.dumps(games_list[:3], indent=2))


# In[40]:


# from nba_api.live.nba.endpoints import Odds
# from nba_api.stats.static import teams
# from nba_api.stats.endpoints import leaguegamefinder

# # Fetch odds data for today's NBA games
# odds = Odds()
# games_list = odds.get_games().get_dict()

# # Get first game only
# game = games_list[0]
# game_id = game.get('gameId', 'Unknown')
# home_team = teams._find_team_name_by_id(game['homeTeamId'])['full_name'] # Use teams module to get team names
# away_team = teams._find_team_name_by_id(game['awayTeamId'])['full_name']

# # Get game date using LeagueGameFinder
# gamefinder = leaguegamefinder.LeagueGameFinder(
#     league_id_nullable="00",
#     game_id_nullable=game_id
# )
# game_info = gamefinder.get_data_frames()[0]
# specific_game = game_info[game_info['GAME_ID'] == game_id]
# game_date = specific_game['GAME_DATE'].iloc[0]

# # Display basic game information
# print(f"Game ID: {game_id}")
# print(f"Game Date: {game_date}")
# print(f"Home Team: {home_team}")
# print(f"Away Team: {away_team}")

# # Display 2-way odds
# two_way_market = next((m for m in game['markets'] if m['name'] == '2way'), None)
# if two_way_market and two_way_market['books']:
#     first_book = two_way_market['books'][0]
#     print(f"\n2-way Odds from {first_book['name']}:")
#     for outcome in first_book['outcomes']:
#         team_type = outcome['type']
#         team_name = home_team if team_type == 'home' else away_team
#         odds = outcome['odds']
#         print(f"  {team_type.capitalize()} ({team_name}): {odds}")
#         trend = outcome['odds_trend']
#         print(f"  Odds trend is: {trend}")
#         opening = outcome['opening_odds']
#         print(f"  Opening odds were: {opening}")

# # Display spread odds
# spread_market = next((m for m in game['markets'] if m['name'] == 'spread'), None)
# if spread_market and spread_market['books']:
#     first_book = spread_market['books'][0]
#     print(f"\nSpread Odds from {first_book['name']}:")
#     for outcome in first_book['outcomes']:
#         team_type = outcome['type']
#         team_name = home_team if team_type == 'home' else away_team
#         spread = outcome.get('spread', 'N/A')
#         odds = outcome['odds']
#         print(f"  {team_type.capitalize()} ({team_name}) with spread {spread}: {odds}")
#         trend = outcome['odds_trend']
#         print(f"  Odds trend is: {trend}")
#         opening = outcome['opening_odds']
#         print(f"  Opening odds: {opening}")
#         opening_spread = outcome['opening_spread']
#         print(f"  Opening spread: {opening_spread}")


# In[ ]:




