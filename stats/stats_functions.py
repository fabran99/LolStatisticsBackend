from .riot_api_routes import *
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import DIVISIONS, TIERS, GAME_TYPE,MAIN_GAMEMODE,RANKED_QUEUES
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS,PLAYSTYLE_STATS_KEYS
from lol_stats_api.helpers.variables import HIGH_ELO_TIERS, LOW_ELO_TIERS, PRE_DIAMOND_TIERS, POST_DIAMOND_TIERS

from lol_stats_api.helpers.variables import saved_players_route, saved_matches_route, saved_champ_ban_route, saved_champ_data_route, saved_playstyle_route
from lol_stats_api.helpers.variables import temp_players_route, temp_matches_route, temp_champ_ban_route, temp_champ_data_route, temp_playstyle_route

from .calculations import generate_builds_stats_by_champ

import json
from django.conf import settings
from os import path
import os
from datetime import datetime as dt, timedelta as td
import random
from concurrent.futures import ThreadPoolExecutor
import requests
from stats.riot_api_routes import get_data_or_none

import pandas as pd
from time import sleep
from assets.load_data import load_data

from lol_stats_api.helpers.mongodb import get_saved_version
from assets.ddragon_routes import get_current_version
from redis import Redis

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))

def_sample={
    "challengers":50,
    "masters":50,
    "grandmasters":50,
    "DIAMOND":{
        "I":25,
        "II":10,
        "III":10,
        "IV":10
    },
    "PLATINUM":{
        "I":5,
        "II":5,
        "III":5,
        "IV":5
    }
}

def is_new_patch():
    saved_version = get_saved_version()
    game_version = get_current_version()
    return saved_version != game_version


def has_saved_players():
    return path.isfile(saved_players_route)

def has_saved_matches():
    return path.isfile(saved_matches_route)

def has_saved_champ_ban():
    return path.isfile(saved_champ_ban_route)
    
def has_saved_champ_data():
    return path.isfile(saved_champ_data_route)

def has_saved_playstyle():
    return path.isfile(saved_playstyle_route)

def x_days_ago(days):
    return int((dt.utcnow() - td(hours=24*days)).timestamp()*1000)

def get_begin_time():
    if not has_saved_matches():
        return x_days_ago(3)

    df = pd.read_csv(saved_matches_route,keep_default_na=False)
    return int(df['timestamp'].max())

        


def get_player_data(leagueData=def_sample, servers=SERVER_ROUTES.keys()):
    """
    Genera un csv en la carpeta preprocess con
    un listado de jugadores de todas las ligas de todos los servers
    """

    player_frame = pd.DataFrame()

    #@TODO Comprobar errores
    print('Trayendo lista de jugadores')
    for key, value in leagueData.items():
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
                    data = get_player_list_by_division(key, div, server)

                    if data is None:
                        continue

                    df_data = pd.DataFrame(data)[['summonerId',"summonerName","rank","tier","inactive"]]
                    df_data = df_data.loc[~(df_data['inactive'])]
                    df_data['server']=server

                    sample = min(div_num, len(df_data))
                    df_data=df_data.sample(sample)

                    player_frame=player_frame.append(df_data, ignore_index=True)
                    player_frame.reset_index(drop=True)

    get_player_detail(player_frame)

    return True


def get_player_detail(player_frame):
    """
    Solicita detalle de los jugadores segun un dataframe
    """
    player_frame = player_frame.sample(frac=1).reset_index(drop=True)
    new_frame = pd.DataFrame()
    total = len(player_frame)
    player_list = []

    def add_player_to_frame(row):
        nonlocal new_frame
        nonlocal player_list

        current_player = row.to_dict()
        print("Solicitando detalle de {} ({})".format(current_player['summonerName'], current_player['server']))
        data = get_player_by_id(current_player['summonerId'], current_player['server'])
        
        if data is None:
            sleep(10)
            data = get_player_by_id(current_player['summonerId'], current_player['server'])

        if data is None or len(data)==0:
            return

        current_player['accountId']=data['accountId']
        current_player['puuid']=data['puuid']
        player_list.append(current_player)

        if len(new_frame) %100 == 0:
            new_frame = pd.DataFrame(player_list)
            new_frame.to_csv(temp_players_route, index=False)
            print("Guardando respaldo de {} jugadores".format(len(new_frame)))


    with ThreadPoolExecutor(max_workers=40) as pool:
        pool.map(add_player_to_frame,[row for index,row in player_frame.iterrows()])
        
    print("==========================")
    print("Finalized")
    print("==========================")
    new_frame = pd.DataFrame(player_list)
    new_frame.to_csv(saved_players_route, index=False)
    print("Csv generado en {}".format(saved_players_route))

  
def get_matches_samples_from_player_list(sample_frac=1,total_matches=10000, max_from_same_player=20, begin_time=None, end_time = None, min_date=x_days_ago(3)):
    """
    Trae un maximo de total_matches partidas, con un maximo de max_from_same_player
    partidas de cada jugador de una lista de partidas posteriores a begin_time
    """
    if not path.isfile(saved_players_route):
        print("No se encuentra el archivo")
        return None

    df = pd.read_csv(saved_players_route,keep_default_na=False)
    # Desordeno el dataframe para evitar agotar el maximo de requests
    df = df.sample(frac=sample_frac).reset_index(drop=True)
    game_list_df = pd.DataFrame()
    game_list_list = []

    def add_games_to_list(row):
        nonlocal game_list_df
        nonlocal game_list_list
        
        if len(game_list_list)>=total_matches:
            return

        print("{} - Trayendo partidas de {} ({})".format(len(game_list_list),row['summonerName'], row['server']))
        game_list = get_matchlist_by_account_id(row['accountId'],row['server'], only_ranked=True, endIndex=max_from_same_player, beginTime=begin_time, endTime=end_time)
        
        if game_list is None:
            sleep(10)
            game_list = get_matchlist_by_account_id(row['accountId'],row['server'], only_ranked=True, endIndex=max_from_same_player, beginTime=begin_time, endTime=end_time)

        if game_list is None or len(game_list)==0:
            return

        game_list=[{**x, "division":row['rank'] , "tier":row['tier']} for x in game_list]
        game_list_list.extend(game_list)

        # Cada 100 partidas guardo en el csv
        if len(game_list_list) %100 == 0:
            game_list_df = pd.DataFrame(game_list_list)
            game_list_df.to_csv(temp_matches_route, index=False)

    with ThreadPoolExecutor(max_workers=40) as pool:
        pool.map(add_games_to_list,[row for index,row in df.iterrows()])
        

    # filtro juegos repetidos si los hay
    game_list_df = pd.DataFrame(game_list_list)
    game_list_df = game_list_df.sort_values("gameId").drop_duplicates(['gameId','platformId'])
    print("Se encontraron un total de {} partidas para analizar".format(len(game_list_df)))
    # Guardo en csv
    game_list_df.to_csv(temp_matches_route, index=False)
    if has_saved_matches():
        saved_games = pd.read_csv(saved_matches_route,keep_default_na=False)
        game_list_df = game_list_df.append(saved_games)
        game_list_df = game_list_df.loc[game_list_df['timestamp']>=min_date]
    game_list_df.to_csv(saved_matches_route, index=False)
    return True
        
 
def get_stats_from_matches(min_date=x_days_ago(3)):
    """
    Arma 3 csv con estadisticas
    """
    if not path.isfile(temp_matches_route):
        print("No se encuentra el archivo")
        return None

    matches = pd.read_csv(temp_matches_route,keep_default_na=False)
    # Desordeno el dataframe para evitar agotar el maximo de requests
    matches = matches.sample(frac=1).reset_index(drop=True)

    champ_ban = pd.DataFrame()
    champ_data = pd.DataFrame()
    playstyle_data = pd.DataFrame()

    bans = []
    c_data = []
    c_pstyle= []

    def add_stats(row):
        nonlocal champ_ban
        nonlocal champ_data
        nonlocal playstyle_data
        nonlocal bans
        nonlocal c_data
        nonlocal c_pstyle

        server = SERVER_REAL_NAME_TO_ROUTE[row['platformId']]

        match_detail = get_match_by_id(row['gameId'], server)

        if match_detail is None:
            sleep(10)
            match_detail = get_match_by_id(row['gameId'], server)

        if match_detail is None or len(match_detail)==0:
            return

        # Manejo bans de la partida
        for team in match_detail['teams']:
            for ban in team['bans']:
                bans.append(
                    {
                        "championId":ban['championId'],
                        "pickTurn":ban['pickTurn'],
                        "division":row['division'],
                        "tier":row['tier'],
                        "win":team['win']=="Win",
                        "gameId":row['gameId'],
                        "teamId":team['teamId'],
                        "server":server,
                        "timestamp":row["timestamp"]
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
                "tier":row['tier'],
                "division":row['division'],
                "gameId":row['gameId'],
                "server":server,
                "participantId":participant['participantId'],
                "timestamp":row["timestamp"]
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
                "tier":row['tier'],
                "division":row['division'],
                "gameId":row['gameId'],
                "server":server,
                "timestamp":row["timestamp"]
            }

            for x in PLAYSTYLE_STATS_KEYS:
                if x in participant['stats']:
                    playstyle[x]=participant['stats'][x]

            c_pstyle.append(playstyle)


        print("Procesando partida {} de {}".format(len(c_data)/10, len(matches)))

        if len(c_data) % 2000 == 0:
            print("Salvando respaldo de {}".format(len(c_data)/10))
            playstyle_data = pd.DataFrame(c_pstyle)
            champ_ban = pd.DataFrame(bans)
            champ_data = pd.DataFrame(c_data)

            playstyle_data.to_csv(temp_playstyle_route, index=False)
            champ_data.to_csv(temp_champ_data_route, index=False)
            champ_ban.to_csv(temp_champ_ban_route,index=False)


    with ThreadPoolExecutor(max_workers=40) as pool:
        pool.map(add_stats,[row for index,row in matches.iterrows()])
        


    print("=========================")
    print("Todas las partidas procesadas")
    print("=========================")

    playstyle_data = pd.DataFrame(c_pstyle)
    champ_ban = pd.DataFrame(bans)
    champ_data = pd.DataFrame(c_data)

    if has_saved_playstyle():
        temp_df = pd.read_csv(saved_playstyle_route,keep_default_na=False)
        playstyle_data = playstyle_data.append(temp_df)
        playstyle_data = playstyle_data.loc[playstyle_data['timestamp']>=min_date]

    if has_saved_champ_ban():
        temp_df = pd.read_csv(saved_champ_ban_route,keep_default_na=False)
        champ_ban = champ_ban.append(temp_df)
        champ_ban = champ_ban.loc[champ_ban['timestamp']>=min_date]

    if has_saved_champ_data():
        temp_df = pd.read_csv(saved_champ_data_route,keep_default_na=False)
        champ_data = champ_data.append(temp_df)
        champ_data = champ_data.loc[champ_data['timestamp']>=min_date]

    playstyle_data.to_csv(saved_playstyle_route, index=False)
    champ_data.to_csv(saved_champ_data_route, index=False)
    champ_ban.to_csv(saved_champ_ban_route,index=False)

    return True


def process_stats(force=False):
    sample = {
        "challengers":300,
        "masters":300,
        "grandmasters":300,
        "DIAMOND":{
            "I":120,
            "II":120,
            "III":120,
            "IV":120
        },
        "PLATINUM":{
            "I":120,
            "II":120,
            "III":120,
            "IV":120
        },
        "GOLD":{
            "I":80,
            "II":80,
            "III":80,
            "IV":80
        },
        "SILVER":{
            "I":80,
            "II":80,
            "III":80,
            "IV":80
        },
        "BRONZE":{
            "I":80,
            "II":80,
            "III":80,
            "IV":80
        },
        "IRON":{
            "I":80,
            "II":80,
            "III":80,
            "IV":80
        },
    }

    # Si se actualizo hace menos de 1 hora
    last_update_date = db_metadata.get("last_update_date")
    running = db_metadata.get("running")
    
    if last_update_date:
        current_time = int(dt.now().timestamp())
        time = td(hours=1).total_seconds()

        if current_time - int(last_update_date) < time and not force:
            print("Recently runned")
            return None
    if running is not None and int(running):
        print("Already running")
        return None

    db_metadata.set("running", 1)
    # Borro archivos temporales
    temp_folder = path.join(settings.PREPROCESS_PATH,"temp")
    filelist = [ f for f in os.listdir(temp_folder)]
    for f in filelist:
        os.remove(os.path.join(temp_folder, f))

    min_date = x_days_ago(3)
    # Pido un sample nuevo de jugadores cuando cambie el parche o cuando no los tenga
    player_sample_frac = 1
    total_matches = 7000
    if is_new_patch() or not has_saved_players():
        get_player_data(leagueData=sample)
        total_matches = 60000

    # Inicio peticion de datos
    begin_time = get_begin_time()
    end_time = x_days_ago(0)
    get_matches_samples_from_player_list(sample_frac = player_sample_frac, begin_time=begin_time, end_time = end_time, total_matches=total_matches, max_from_same_player=30, min_date=min_date)

    get_stats_from_matches(min_date=min_date)
    load_data()
    generate_builds_stats_by_champ()
    
    # Seteo info para el siguiente update
    current_time = dt.now().timestamp()
    db_metadata.set("last_update_date", int(current_time))
    db_metadata.set("running", 0)

    # Borro archivos temporales
    temp_folder = path.join(settings.PREPROCESS_PATH,"temp")
    filelist = [ f for f in os.listdir(temp_folder)]
    for f in filelist:
        os.remove(os.path.join(temp_folder, f))



        
# Prueba jungla

def get_frames():
    df = pd.read_csv(champ_data_file,keep_default_na=False)
    df = df.loc[((df['spell1Id']==11) |(df['spell2Id']==11)) & (df['lane'].isin(["JUNGLE", "NONE"]))]
    df = df.reset_index(drop=True)
    df=df[['championId','teamId','tier','gameId','server','participantId']]

    df.to_csv("/home/facundo/Desktop/Code/projects/lol_app_2/lol_stats_api/preprocess/game_participant.csv", index=False)

    frame_list_df = pd.DataFrame()
    frame_list_list = []
    dataframe = df
    dataframe=dataframe.sample(frac=1).reset_index(drop=True)
    
    def add_frames_to_list(gameId):
        nonlocal frame_list_df
        nonlocal frame_list_list
        nonlocal dataframe

        matchDf = dataframe.loc[dataframe['gameId']==gameId]
        if not len(matchDf):
            return
        print('{} frames de {} partidas'.format(len(frame_list_list), len(dataframe['gameId'].unique())))
        first_row = matchDf.iloc[0]
        participants = [int(x) for x in matchDf['participantId'].unique()]
        
        url = "https://{}/lol/match/v4/timelines/by-match/{}".format(SERVER_ROUTES[first_row['server']], str(first_row['gameId']))
        data = get_data_or_none(url)
        
        if not data:
            sleep(10)
            return
        

        frame_list = []

        for x in data['frames']:
            # Solo hasta el min 10
            if int(x['timestamp']) > 600000:
                break

            for index, row in matchDf.iterrows():
                frame = {
                'timestamp':x['timestamp'],
                'teamId':row['teamId'],
                'tier':row['tier'],
                'championId':row['championId']
                }
                for i, participant in x['participantFrames'].items():
                    if int(participant['participantId']) == int(row['participantId']):                
                        try:
                            frame.update({
                            "x":participant['position']['x'],
                            "y":participant['position']['y']
                            })
                            frame_list.append(frame)
                        except:
                            pass
                        break
        frame_list_list.extend(frame_list)
        
    
    with ThreadPoolExecutor(max_workers=40) as pool:
        pool.map(add_frames_to_list,[int(x) for x in dataframe['gameId'].unique()])
        
            
    frame_list_df = pd.DataFrame(frame_list_list)
    frame_list_df.to_csv("/home/facundo/Desktop/Code/projects/lol_app_2/lol_stats_api/preprocess/processed_frames.csv", index=False)

