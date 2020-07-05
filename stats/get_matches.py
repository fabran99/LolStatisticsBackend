from datetime import datetime as dt, timedelta as td
import pandas as pd
import numpy as np
from time import sleep
import json
from redis import Redis
import os
from bson import ObjectId

from lol_stats_api.helpers.mongodb import get_mongo_players, get_monary, get_mongo_stats
from lol_stats_api.helpers.variables import player_sample, HIGH_ELO_TIERS, LOW_ELO_TIERS, \
POST_DIAMOND_TIERS, PRE_DIAMOND_TIERS
from lol_stats_api.helpers.variables import SERVER_REAL_NAME_TO_ROUTE, RANKED_QUEUES, SERVER_ROUTES
from lol_stats_api.helpers.variables import DIVISIONS, TIERS
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS,PLAYSTYLE_STATS_KEYS
from stats.riot_api_routes import get_matchlist_by_account_id, get_match_by_id
from lol_stats_api import tasks

db_players = get_mongo_players()
db_stats = get_mongo_stats()

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))
db_matchlist = Redis(db=os.getenv("REDIS_GAMELIST_DB"))
db_processed_match = Redis(db=os.getenv("REDIS_GAMEID_PROCESSED_DB"))

monary_db = get_monary()

# Variables generales
columns = ['rank', 'tier', 'accountId',"last_time_searched","last_match_number","_id"]
column_types = ["string:15","string:15", "string:60", "date", "uint32","id"]



def get_begin_time(server):
    data = db_metadata.get("last_end_time_{}".format(server))
    if data is not None:
        return int(data)
    else:
        return x_days_ago(3)
    

def x_days_ago(days):
    return int((dt.utcnow() - td(hours=24*days)).timestamp()*1000)


def monary_array_to_df(arrays):
    y = np.array(np.ma.array(arrays, fill_value=np.nan).filled(), dtype=object)
    df = pd.DataFrame(y.T, columns=columns)

    for column, column_type in zip(columns, column_types):
        if "string" in column_type:
            df[column]=df[column].str.decode("utf-8")
        elif column_type == "id":
            df[column]=df[column].apply(lambda x:x.hex())

    return df


def get_matches_sample_from_player_list(server="LAS"):
    """
    Pide partidas en un rango de fechas para los jugadores de un server concreto, y las agrega a la lista de redis
    """
    # Manejo las fechas
    end_time = x_days_ago(0)
    begin_time = get_begin_time(server)

    # Pido la lista de jugadores con este server
    query = {
        "server": server
    }
    
    arrays = monary_db.query("players","player_list",query, columns, column_types)
    df = monary_array_to_df(arrays)

    df = df.loc[df['accountId'].notna()]
    df = df.sort_values(['last_time_searched','last_match_number'], ascending=[True,False]).reset_index(drop=True)


    for index, row in df.iterrows():
        print("Trayendo partidas de {} ({}) {} de {}".format(row['accountId'], server, str(index+1), str(len(df))))

        # Traigo la lista de datos
        game_list = get_matchlist_by_account_id(row['accountId'],server, only_ranked=True, endIndex=20, beginTime=begin_time, endTime=end_time)
        
        # Actualizo la cantidad de partidas del jugador
        time_searched = x_days_ago(0)
        match_number = 0
        if game_list is not None:
            match_number = len(game_list)

        print("{} partidas encontradas".format(str(match_number)))

        # Si llevo dos iteraciones y el jugador no tiene partidas, lo quito
        if str(row['last_match_number']) == "0" and match_number ==0:
            print("Borrando jugador, 2 pasadas sin partidas")
            db_players.player_list.remove({"_id":ObjectId(row['_id'])})
            continue

        update={
            "$set":{
                "last_match_number":match_number,
                "last_time_searched":time_searched
            }
        }

        db_players.player_list.update_one({"_id":ObjectId(row['_id'])}, update)

        # Reviso la info
        if game_list is None or len(game_list)==0:
            continue
        
        game_list=[{**x, "division":row['rank'] , "tier":row['tier']} for x in game_list]

        # Mando las partidas a redis
        for x in game_list:
            if not db_processed_match.get(x['gameId']):
                db_matchlist.lpush(server, json.dumps(x))
                # tasks.process_match_with_celery.delay(x)

    # Actualizo la fecha final
    db_metadata.set("last_end_time_{}".format(server), end_time)


def process_match(match):
    """
    Procesa una partida y guarda sus datos en mongo
    """
    match = json.loads(match)
    if db_processed_match.get(match['gameId']) is not None:
        return 
    server = SERVER_REAL_NAME_TO_ROUTE[match['platformId']]
    match_detail = get_match_by_id(match['gameId'], server)

    if match_detail is None:
        sleep(10)
        match_detail = get_match_by_id(match['gameId'], server)

    # Reintento con cada partida hasta 3 veces
    if match_detail is None or len(match_detail)==0:
        match['retries']=1 if "retries" not in match else int(match['retries'])+1
        if match['retries']>=3:
            return
        else:
            db_matchlist.lpush(server, json.dumps(match))
            return

    bans = []
    c_data = []
    c_pstyle = []

    # Manejo bans de la partida
    for team in match_detail['teams']:
        for ban in team['bans']:
            bans.append(
                {
                    "championId":ban['championId'],
                    "pickTurn":ban['pickTurn'],
                    "division":match['division'],
                    "tier":match['tier'],
                    "win":team['win']=="Win",
                    "gameId":match['gameId'],
                    "teamId":team['teamId'],
                    "server":server,
                    "timestamp":match["timestamp"]
                }
            )

    # Manejo datos de campeones y playstyle
    for participant in match_detail['participants']:
        # Campeones
        data={
            "championId":participant['championId'],
            "teamId":participant['teamId'],
            "role":participant['timeline']['role'],
            "lane":participant['timeline']['lane'],
            "spell1Id":participant['spell1Id'],
            "spell2Id":participant['spell2Id'],
            "gameDuration":match_detail['gameDuration'],
            "tier":match['tier'],
            "division":match['division'],
            "gameId":match['gameId'],
            "server":server,
            "participantId":participant['participantId'],
            "timestamp":match["timestamp"]
        }

        for x in MATCHES_STATS_KEYS:
            if x in participant['stats']:
                data[x]=participant['stats'][x]

        c_data.append(data)

        # Playstyle
        playstyle={
            "championId":participant['championId'],
            "teamId":participant['teamId'],
            "role":participant['timeline']['role'],
            "lane":participant['timeline']['lane'],
            "gameDuration":match_detail['gameDuration'],
            "tier":match['tier'],
            "division":match['division'],
            "gameId":match['gameId'],
            "server":server,
            "timestamp":match["timestamp"]
        }

        for x in PLAYSTYLE_STATS_KEYS:
            if x in participant['stats']:
                playstyle[x]=participant['stats'][x]

        c_pstyle.append(playstyle)

    # Inserto en la base
    print("Insertando datos de la partida en la base de datos")
    db_stats.bans.insert_many(bans)
    db_stats.champ_data.insert_many(c_data)
    db_stats.champ_playstyle.insert_many(c_pstyle)

    # Seteo el gameId para no procesarlo mas veces
    db_processed_match.set(match['gameId'], "True", ex=60*60*24)
    




