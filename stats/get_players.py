from datetime import datetime as dt
import pandas as pd
from time import sleep

from lol_stats_api.helpers.mongodb import get_mongo_players
from lol_stats_api.helpers.variables import player_sample, HIGH_ELO_TIERS, LOW_ELO_TIERS, \
POST_DIAMOND_TIERS, PRE_DIAMOND_TIERS
from lol_stats_api.helpers.variables import SERVER_REAL_NAME_TO_ROUTE, RANKED_QUEUES, SERVER_ROUTES
from lol_stats_api.helpers.variables import DIVISIONS, TIERS

from stats.riot_api_routes import get_high_elo_player_list_by_elo, get_player_list_by_division,\
    get_player_by_id

from lol_stats_api import tasks

db_players = get_mongo_players()

def update_player_list(player_sample=player_sample,servers=SERVER_ROUTES.keys()):
    """
    Obtiene una lista de jugadores y manda a actualizar o crear en mongo un registro por jugador
    """
    player_frame = pd.DataFrame()

    print("Trayendo lista de jugadores")
    for key, value in player_sample.items():
        for server in servers:
            if key in POST_DIAMOND_TIERS:
                print("{} en {}".format(key, server) )
                data = get_high_elo_player_list_by_elo(key, server)
                if data is None or len(data['entries'])==0:
                    continue
                data = data['entries']

                df_data = pd.DataFrame(data)[['summonerId',"summonerName","rank","inactive"]]
                df_data['tier']=key
                df_data = df_data.loc[~(df_data['inactive'])]
                df_data['server']=server
                sample = min(value, len(df_data))
                df_data=df_data.sample(sample)

                player_frame=player_frame.append(df_data)
                player_frame.reset_index(drop=True)

            elif key in PRE_DIAMOND_TIERS:
                for div, div_num in value.items():
                    print("{} {} en {}".format(key, div, server) )
                    page = 1

                    if key in ["DIAMOND","PLATINUM"]:
                        page = 4
                    else:
                        page = 2

                    while page > 0:
                        data = get_player_list_by_division(key, div, server, page=str(page))
                        if data is None:
                            page= page-1
                            continue
                        if len(data) == 0:
                            page= page-1
                            continue
                        df_data = pd.DataFrame(data)[['summonerId',"summonerName","rank","tier","inactive"]]
                        df_data = df_data.loc[~(df_data['inactive'])]
                        df_data['server']=server

                        sample = min(div_num, len(df_data))
                        df_data=df_data.sample(sample)

                        player_frame=player_frame.append(df_data, ignore_index=True)
                        player_frame.reset_index(drop=True)
                        page = page-1

    # desordeno la lista
    player_frame = player_frame.sample(frac=1).reset_index(drop=True)
    print("Obtenidos {} jugadores".format(str(len(player_frame))))
    for index, row in player_frame.iterrows():
        # Mando a celery el jugador para actualizar
        tasks.update_player_detail_in_celery.delay(row.to_dict())


def update_player_detail(current_player):
    """
    Dado un jugador, crea un registro o actualiza el que tiene
    """
    if not current_player:
        return

    print("Solicitando detalle de {} ({})".format(current_player['summonerName'], current_player['server']))
    data = get_player_by_id(current_player['summonerId'], current_player['server'])

    if data is None:
        sleep(10)
        data = get_player_by_id(current_player['summonerId'], current_player['server'])

    if data is None or len(data)==0:
        return

    current_player['accountId']=data['accountId']
    current_player['puuid']=data['puuid']
    
    player_filter = {
        "puuid":current_player["puuid"],
    }

    update = {
        "$set":current_player
    }

    db_players.player_list.update_one(player_filter,update,upsert=True)






    

