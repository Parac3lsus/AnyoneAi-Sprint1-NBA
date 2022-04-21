### Complete in this cell: get all active players from the api
#!pip install nba_api
#import numpy as np
#import pandas as pd
from nba_api.stats.static import players
from nba_api.stats.endpoints import commonallplayers
from nba_api.stats.endpoints import commonplayerinfo
from nba_api.stats.endpoints import playercareerstats
from nba_api.stats.endpoints import playernextngames
from nba_api.stats.endpoints import playerprofilev2
import time
import pandas as pd
import chardet
# ================================================================================================================================== #
def get_and_save_players_list():
  players = commonallplayers.CommonAllPlayers(is_only_current_season =1).get_data_frames()[0]
  players = players[ (players["TEAM_NAME"]!="") & (players["GAMES_PLAYED_FLAG"]!="N") & (players["PERSON_ID"]!=1630597)]
  players = players[["PERSON_ID","DISPLAY_FIRST_LAST","TEAM_NAME"]]
  players.rename(columns={'DISPLAY_FIRST_LAST': 'PLAYER_NAME'}, inplace=True)
  players.rename(columns ={'PERSON_ID':'PLAYER_ID'}, inplace = True)
  return players
# ================================================================================================================================== #
current_players_list = get_and_save_players_list()
current_players_list.to_csv("nba_current_players_list.csv")
# ================================================================================================================================== #



# # ================================================================================================================================== #
def clean_players_personal_information(players_list):
  players_list['PLAYER_NAME'] = players_list['FIRST_NAME'] + ' ' + players_list['LAST_NAME']
  players_list = players_list.drop(['FIRST_NAME', 'LAST_NAME'], axis=1)
  players_list.rename(columns={'PERSON_ID': 'PLAYER_ID'}, inplace=True)
  aux_player_names = list(players_list.loc[:, 'PLAYER_NAME'])
  players_list.insert(0, 'PLAYER_NAME', aux_player_names, allow_duplicates=True)
  players_list = players_list.iloc[:, 0:-1]
  players_list['SEASON_EXP'] = players_list['TO_YEAR'] - players_list['FROM_YEAR']
  players_list = players_list[["PLAYER_ID", "PLAYER_NAME", "TEAM_NAME", "POSITION", "HEIGHT", "WEIGHT", "COUNTRY",
                           "BIRTHDATE", "SEASON_EXP", "DRAFT_NUMBER"]]
  return players_list

def get_players_personal_information(current_players_list):

  players_list = list(current_players_list["PLAYER_ID"])
  all_players = pd.DataFrame()
  try:
    for player in players_list:
      player_info = commonplayerinfo.CommonPlayerInfo(player_id=player).get_data_frames()
      player_info = player_info[0]
      all_players = pd.concat([all_players,player_info])
      time.sleep(0.5)
  except:
    pass
  all_players = clean_players_personal_information(all_players)
  print(all_players.head())
  return all_players
# ================================================================================================================================== #
import pandas as pd
from nba_api.stats.endpoints import commonplayerinfo
current_players_list = pd.read_csv("nba_current_players_list.csv")
players_personal_info = get_players_personal_information(current_players_list)
players_personal_info.to_csv("nba_players_personal_info.csv")
# ================================================================================================================================== #



# ================================================================================================================================== #
def get_players_career_stats(current_players_list):
  players_list = list(current_players_list["PLAYER_ID"])
  print(players_list)
  all_players = pd.DataFrame()
  try:
    for player in players_list:
      player_info = playercareerstats.PlayerCareerStats(player_id=str(player),per_mode36="PerGame").get_data_frames()
      player_info = player_info[1]
      all_players = pd.concat([all_players,player_info])
      time.sleep(0.5)
  except:
    pass
  all_players = all_players.drop(['LEAGUE_ID','Team_ID', 'GS', 'FGM',
                        'FGA', 'FG_PCT', 'FG3M', 'FG3A', 'FG3_PCT', 'FTM',
                        'FTA', 'FT_PCT', 'OREB', 'DREB', 'TOV',
                        'PF'], axis=1)
  print(len(all_players.index))
  print(all_players.head())
  return all_players
# ================================================================================================================================== #
from nba_api.stats.endpoints import playercareerstats
import pandas as pd
import time
current_players_list = pd.read_csv("nba_current_players_list.csv")
players_career_stats = get_players_career_stats(current_players_list)
players_career_stats.to_csv("nba_players_career_stats.csv")
# ================================================================================================================================== #




# ================================================================================================================================== #
def get_players_next_game(current_players_list):

  players_list = list(current_players_list["PLAYER_ID"])
  all_players_next_game = pd.DataFrame()
  nxt_game_dtf = pd.DataFrame()
  all_players_next_game['PLAYER_ID'] = pd.Series([], dtype=int)
  all_players_next_game['GAME_DATE'] = pd.Series([], dtype=str)

  for player in players_list:
    try:
      nxt_game_dtf2 = playerprofilev2.PlayerProfileV2(player_id=player, per_mode36="Totals").next_game.get_data_frame()
      nxt_game_dtf['GAME_DATE'] = nxt_game_dtf2['GAME_DATE']
    except:
      nxt_game_dtf['GAME_DATE'] = np.nan
      print("Player not found")

    nxt_game_dtf['PLAYER_ID'] = player
    all_players_next_game = pd.concat([all_players_next_game, nxt_game_dtf])
    time.sleep(0.5)

  all_players_next_game['GAME_DATE']=pd.to_datetime(all_players_next_game['GAME_DATE'])
  #all_players_next_game.set_index('PLAYER_ID', inplace=True)
  return all_players_next_game
# ================================================================================================================================== #
import time
import pandas as pd
import numpy as np
from nba_api.stats.endpoints import playerprofilev2
current_players_list = pd.read_csv("nba_current_players_list.csv")
current_players_list = current_players_list.drop(['Unnamed: 0'], axis=1)
players_next_game = get_players_next_game(current_players_list)
print("Done")
players_next_game.to_csv("nba_players_next_game.csv")
# ================================================================================================================================== #
# ### Complete in this cell: find players salary, save the information to csv
#!pip install chardet
#!pip install gitpython
#!pip install unidecode
def name_cleaner(name):
  spaces = 0
  n = 0
  output_name =""
  for c in name:
    if c == " ":
      spaces += 1
    if spaces > 1:
      output_name = name[:n]
      return output_name.lower()
    n += 1
  return name.lower()

def get_nba_players_salaries(csv_file_path):
  import git
  import os.path
  from os import path
  import pandas as pd
  from unidecode import unidecode

  #-------------Github-----------------#
  repo_path = "NBA/"
  if not path.exists(repo_path):
    repo=git.Repo.clone_from('https://github.com/Parac3lsus/Sprint1.git', 'NBA')
  csv_file_path = repo_path + csv_file_path
  # -------------Github-----------------#
  salaries = pd.read_csv(csv_file_path, encoding='utf-8')
  salaries = salaries.drop_duplicates(subset=['Unnamed: 1'])
  salaries[['Player2', 'Discard']] = salaries['Unnamed: 1'].str.split('\\', expand=True)
  salaries = salaries.drop(['Unnamed: 1', 'Discard'], axis=1)
  salaries = salaries.drop([0], axis=0)
  salaries = salaries[['Player2','Salary']].copy()
  salaries = salaries.rename(columns ={'Player2':'PLAYER_NAME','Salary':'SALARY'}, inplace= False)
  salaries['SALARY'] = salaries['SALARY'].str.replace('$', '')
  salaries['SALARY'] = salaries['SALARY'].str.replace('?', '')
  salaries = salaries.fillna(0)
  salaries['SALARY'] = salaries['SALARY'].astype('int64')
  salaries['PLAYER_ID'] = 0
  print(len(salaries.index))
  for i, row in salaries.iterrows():
    for n, players_row in players_personal_info.iterrows():
      if(name_cleaner(unidecode(row.PLAYER_NAME)) == name_cleaner(unidecode(players_row.PLAYER_NAME))):
        salaries.loc[i, 'PLAYER_ID'] = int(players_row.PLAYER_ID)
        break
  salaries = salaries[salaries['PLAYER_ID']!=0]
  print(len(salaries.index))
  return salaries
# ================================================================================================================================== #
import pandas as pd
players_personal_info = pd.read_csv("nba_players_personal_info.csv")
players_salaries = get_nba_players_salaries("contracts.csv")
players_salaries.to_csv("nba_players_salary.csv")
# ================================================================================================================================== #



# ================================================================================================================================== #
def merge_dataframes(personal_info, career_stats, next_game, salaries):
  raw_players_dataset = pd.merge(personal_info, career_stats, on='PLAYER_ID', how='left')
  raw_players_dataset = pd.merge(raw_players_dataset, next_game, on='PLAYER_ID', how='left')
  raw_players_dataset = pd.merge(raw_players_dataset, salaries, on='PLAYER_ID', how='left')
  return raw_players_dataset

import pandas as pd
current_players_list = pd.read_csv("nba_current_players_list.csv")
players_personal_info = pd.read_csv("nba_players_personal_info.csv")
players_career_stats = pd.read_csv("nba_players_career_stats.csv")
players_next_game = pd.read_csv("nba_players_next_game.csv")
players_salaires = pd.read_csv("nba_players_salary.csv")

raw_players_dataset = merge_dataframes(players_personal_info, players_career_stats, players_next_game, players_salaries)