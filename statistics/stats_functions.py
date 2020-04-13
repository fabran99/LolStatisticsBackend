from .riot_api_routes import *
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import DIVISIONS, TIERS, GAME_TYPE,MAIN_GAMEMODE,RANKED_QUEUES
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS,PLAYSTYLE_STATS_KEYS

import json
from django.conf import settings
from os import path
import os
import random

import pandas as pd
from time import sleep

league_data_route=path.join(settings.PREPROCESS_PATH, "league_data.json")
player_sample_route=path.join(settings.PREPROCESS_PATH, "player_sample.csv")
matches_sample_route=path.join(settings.PREPROCESS_PATH, "matches_sample.csv")
champ_ban_file=path.join(settings.PREPROCESS_PATH, "champ_ban.csv")
champ_data_file=path.join(settings.PREPROCESS_PATH, "champ_data.csv")
playstyle_data_file=path.join(settings.PREPROCESS_PATH, "playstyle_data.csv")


def_sample = 5

def get_player_data():
    """
    Genera un json en la carpeta preprocess con
    un listado de jugadores de todas las ligas de todos los servers
    """

    challengers={}
    masters={}
    grandmaster={}
    leagues={}
    for server in SERVER_ROUTES.keys():
        print("Buscando jugadores en {}".format(server))
        challengers[server]=get_player_list_challenger(server)
        masters[server]=get_player_list_master(server)
        grandmaster[server]=get_player_list_grandmaster(server)

        leagues[server]={}
        for tier in TIERS:
            leagues[server][tier]={}
            for division in DIVISIONS:
                leagues[server][tier][division]=get_player_list_by_division(tier,division,server)    

    complete_data = {
        "challengers":challengers,
        "masters":masters,
        "grandmasters":grandmaster,
        "leagues":leagues
    }

    with open(league_data_route, "w") as f:
        json.dump(complete_data, f)

    print("Json generado en {}".format(league_data_route))


def get_player_sample_from_json():
    """
    Guarda en csv una muestra de 5 jugadores random de cada liga,
    si no encuentra el json retorna None
    """

    if not path.isfile(league_data_route):
        print("No se encuentra el archivo")
        return None

    with open(league_data_route, "r") as f:
        league_data = json.load(f)
    
    high_elo_keys = ['challengers','masters','grandmasters']

    sample_data={}
    for elo in high_elo_keys:
        sample_data[elo]={}
        for server, data in league_data[elo].items():
            if league_data[elo][server] is None:
                continue
            sample = def_sample
            if len(league_data[elo][server]['entries']) < sample:
                sample = len(league_data[elo][server]['entries'])
            if sample == 0:
                continue

            sample_data[elo][server]=random.sample(league_data[elo][server]['entries'], sample)

    sample_data['leagues']={}
    for server in SERVER_ROUTES.keys():
        sample_data['leagues'][server]={}
        for tier in TIERS:
            sample_data['leagues'][server][tier]={}
            for division in DIVISIONS:
                sample = def_sample
                total = len(league_data['leagues'][server][tier][division])
                if total < sample:
                    sample = total
                if total == 0:
                    continue
                
                sample_data['leagues'][server][tier][division]= random.sample(league_data['leagues'][server][tier][division], sample)

    save_player_sample_data(sample_data)


    print("Csv generado en {}".format(player_sample_route))


def save_player_sample_data(league_data):
    """
    Procesa y guarda la info de cada jugador que recibe como parametro
    """
    high_elo_keys = ['challengers','masters','grandmasters']

    player_list = pd.DataFrame()

    for elo in high_elo_keys:
        for server in SERVER_ROUTES.keys():
            if not server in league_data[elo].keys():
                continue
            for player in league_data[elo][server]:
                if player['inactive']:
                    continue

                playerData=get_player_by_id(player['summonerId'],server)
                print("Guardando datos de {} ({})".format(player['summonerName'], server))
                # si me devuelve none porque excedi las requests espero un min y sigo
                sleep(0.2)
                if playerData is None:
                    sleep(30)
                    playerData=get_player_by_id(player['summonerId'],server)
                if playerData is None:
                    continue

                player_list = player_list.append([{
                    "summonerId":player['summonerId'],
                    "tier":player['rank'],
                    "leaguePoints":player['leaguePoints'],
                    "wins":player['wins'],
                    "losses":player['losses'],
                    "summonerName":player['summonerName'],
                    "server":server,
                    "division":elo,
                    "winrate":round(player['wins']*100/(player['wins']+player['losses']),1),
                    "accountId":playerData['accountId'],
                    "puuid":playerData['puuid'],
                    "profileIconId":playerData['profileIconId'],
                    "summonerLevel":playerData['summonerLevel'],
                    "revisionDate":playerData['revisionDate'],
                }])
                player_list.to_csv(player_sample_route, index=False)

    for tier in TIERS:
        for division in DIVISIONS:
            for server in SERVER_ROUTES.keys():
                for player in league_data['leagues'][server][tier][division]:
                    if player['inactive']:
                        continue
                    playerData=get_player_by_id(player['summonerId'],server)
                    print("Guardando datos de {} ({})".format(player['summonerName'], server))
                    # si me devuelve none porque excedi las requests espero un min y sigo
                    sleep(0.2)
                    if playerData is None:
                        sleep(30)
                        playerData=get_player_by_id(player['summonerId'],server)
                    if playerData is None:
                        continue

                    player_list = player_list.append([{
                        "summonerId":player['summonerId'],
                        "tier":player['rank'],
                        "leaguePoints":player['leaguePoints'],
                        "wins":player['wins'],
                        "losses":player['losses'],
                        "summonerName":player['summonerName'],
                        "server":server,
                        "division":player['tier'],
                        "winrate":round(player['wins']*100/(player['wins']+player['losses']),1),
                        "accountId":playerData['accountId'],
                        "puuid":playerData['puuid'],
                        "profileIconId":playerData['profileIconId'],
                        "summonerLevel":playerData['summonerLevel'],
                        "revisionDate":playerData['revisionDate'],
                    }])
                    player_list.to_csv(player_sample_route, index=False)

    return player_list


def get_10_matches_from_player_list():
    """
    Guarda lista de las ultimas 10 partidas de cada jugador 
    """
    if not path.isfile(player_sample_route):
        print("No se encuentra el archivo")
        return None

    df = pd.read_csv(player_sample_route,keep_default_na=False)
    # Desordeno el dataframe para evitar agotar el maximo de requests
    df = df.sample(frac=1).reset_index(drop=True)

    game_list_df = pd.DataFrame()
    for index, row in df.iterrows():
        print("Trayendo partidas de {} ({})".format(row['summonerName'], row['server']))
        sleep(0.1)
        game_list = get_matchlist_by_account_id(row['accountId'],row['server'], only_ranked=True, endIndex=10)
        if game_list is not None:
            game_list=[{**x, "division":row['division'] , "tier":row['tier']} for x in game_list]
            game_list_df= game_list_df.append(game_list)
            game_list_df.reset_index(drop=True, inplace=True)

            game_list_df.to_csv(matches_sample_route, index=False)

        else:
            sleep(30)
            game_list = get_matchlist_by_account_id(row['accountId'],row['server'], only_ranked=True, endIndex=10)
            if game_list is not None:
                game_list=[{**x,  "division":row['division'], "tier":row['tier']} for x in game_list]
                game_list_df= game_list_df.append(game_list)
                game_list_df.reset_index(drop=True, inplace=True)

                game_list_df.to_csv(matches_sample_route, index=False)
        
    # filtro juegos repetidos si los hay
    game_list_df = game_list_df.sort_values("gameId").drop_duplicates(['gameId','platformId'])

    # Guardo en csv
    game_list_df.to_csv(matches_sample_route, index=False)


def get_stats_from_matches():
    """
    Arma 3 csv con estadisticas
    """
    if not path.isfile(matches_sample_route):
        print("No se encuentra el archivo")
        return None

    if not path.isfile(player_sample_route):
        print("No se encuentra el archivo")
        return None

    matches = pd.read_csv(matches_sample_route,keep_default_na=False)
    # Desordeno el dataframe para evitar agotar el maximo de requests
    matches = matches.sample(frac=1).reset_index(drop=True)

    champ_ban = pd.DataFrame()
    champ_data = pd.DataFrame()
    playstyle_data = pd.DataFrame()
    
    for index, row in matches.iterrows():
        # Traigo datos del match actual
        print("Procesando partida {} de {}".format(index, len(matches)))
        match_detail = get_match_by_id(row['gameId'], SERVER_REAL_NAME_TO_ROUTE[row['platformId']])

        if match_detail is None:
            sleep(30)
            match_datail = get_match_by_id(row['gameId'], SERVER_REAL_NAME_TO_ROUTE[row['platformId']])
        if match_detail is None:
            continue

        # Manejo bans de la partida
        bans = []
        for team in match_detail['teams']:
            for ban in team['bans']:
                bans.append(
                    {
                        "championId":ban['championId'],
                        "pickTurn":ban['pickTurn'],
                        "division":row['division'],
                        "tier":row['tier'],
                        "win":team['win']=="Win"
                    }
                )
        champ_ban=champ_ban.append(bans)

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
                "division":row['division']
            }

            for x in MATCHES_STATS_KEYS:
                if x in participant['stats']:
                    data[x]=participant['stats'][x]

            champ_data = champ_data.append([data])

            # Playstyle
            playstyle={
                "championId":participant['championId'],
                "teamId":participant['teamId'],
                "role":participant['timeline']['role'],
                "lane":participant['timeline']['lane'],
                "gameDuration":match_detail['gameDuration'],
                "tier":row['tier'],
                "division":row['division']
            }

            for x in PLAYSTYLE_STATS_KEYS:
                if x in participant['stats']:
                    playstyle[x]=participant['stats'][x]

            playstyle_data = playstyle_data.append([playstyle])
    
    playstyle_data.to_csv(playstyle_data_file, index=False)
    champ_data.to_csv(champ_data_file, index=False)
    champ_ban.to_csv(champ_ban_file,index=False)


def process_stats():
    # get_player_sample_from_json()
    get_10_matches_from_player_list()
    get_stats_from_matches()
    

            


        
