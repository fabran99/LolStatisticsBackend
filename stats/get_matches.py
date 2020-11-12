from lol_stats_api.helpers.redis import db_metadata, db_matchlist, db_processed_match, db_celery
from datetime import datetime as dt, timedelta as td
import pandas as pd
import numpy as np
from time import sleep
import json
from redis import Redis
import os
from bson import ObjectId

from lol_stats_api.helpers.mongodb import get_mongo_stats
from lol_stats_api.helpers.variables import player_sample, HIGH_ELO_TIERS, LOW_ELO_TIERS, \
    POST_DIAMOND_TIERS, PRE_DIAMOND_TIERS, SMITE_SUMM
from lol_stats_api.helpers.variables import SERVER_REAL_NAME_TO_ROUTE, RANKED_QUEUES, SERVER_ROUTES, LAST_IMPORTANT_PATCH
from lol_stats_api.helpers.variables import DIVISIONS, TIERS
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS, PLAYSTYLE_STATS_KEYS
from lol_stats_api.helpers.variables import tier_name_to_n, role_name_to_n, division_name_to_n, lane_name_to_n
from stats.riot_api_routes import get_matchlist_by_account_id, get_match_by_id, get_timelist_by_match_id
from lol_stats_api import tasks

from stats.models import *

from django_pandas.io import read_frame

db_stats = get_mongo_stats()


# Variables generales
columns = ['rank', 'tier', 'accountId', "last_time_searched",
           "last_match_number", "zero_matches_number", "id"]


def x_days_ago(days):
    return int((dt.utcnow() - td(hours=24*days)).timestamp()*1000)


def get_matches_sample_from_player_list(server="LAS"):
    """
    Pide partidas en un rango de fechas para los jugadores de un server concreto, y las agrega a la lista de redis
    """
    # Pido la lista de jugadores con este server
    query = {
        "server": server
    }

    qs = Player.objects.filter(server=server)

    df = read_frame(qs, fieldnames=columns)

    if len(df) == 0:
        print("No hay jugadores guardados")
        return

    df = df.loc[df['accountId'].notna()]
    df = df.sort_values(['last_time_searched'],
                        ascending=True).reset_index(drop=True)

    # Rearmo el df para que priorice los que mas tiempo paso desde que se buscaron, y ademas que tengan mas partidas encontradas
    half_rows = round(len(df)/2)
    oldest_searched = df.head(half_rows)
    newest_searched = df.tail(half_rows)

    oldest_searched = oldest_searched.sort_values(
        ['last_match_number'], ascending=False)
    df = oldest_searched.append(newest_searched).reset_index(drop=True)
    for index, row in df.iterrows():
        print("Trayendo partidas de {} ({}) {} de {}".format(
            row['accountId'], server, str(index+1), str(len(df))))
        begin_time = x_days_ago(3)
        # Parche 10.23 en adelante
        begin_time = max(LAST_IMPORTANT_PATCH, more_time_ago)

        if row['last_time_searched'] is not None and not np.isnan(row['last_time_searched']):
            begin_time = max(row['last_time_searched'], begin_time)

        begin_time = int(begin_time)

        end_time = x_days_ago(0)
        # Traigo la lista de datos
        game_list = get_matchlist_by_account_id(
            row['accountId'], server, only_ranked=True, endIndex=20, beginTime=begin_time, endTime=end_time)
        # Actualizo la cantidad de partidas del jugador
        match_number = 0
        if game_list is not None:
            match_number = len(game_list)

        print("{} partidas encontradas".format(str(match_number)))
        # Si llevo 6 iteraciones y el jugador no tiene partidas, lo quito
        if match_number == 0 and not np.isnan(row['zero_matches_number']) and int(row['zero_matches_number']) > 6:
            print("Borrando jugador, 6 pasadas sin partidas\n")
            found = Player.objects.filter(id=row['id'])
            print(found)
            found.delete()
            continue

        zero_matches_number = int(row['zero_matches_number']) if not np.isnan(
            row['zero_matches_number']) else 0

        if match_number == 0:
            zero_matches_number += 1
        else:
            zero_matches_number = 0

        # db_players.player_list.update_one({"_id":ObjectId(row['_id'])}, update)
        pid = row['id']
        update = row.to_dict()
        update["last_match_number"] = match_number
        update["last_time_searched"] = end_time
        update["zero_matches_number"] = zero_matches_number

        Player.objects.filter(id=pid).update(**update)

        # Reviso la info
        if game_list is None or len(game_list) == 0:
            continue

        game_list = [{**x, "division": row['rank'], "tier":row['tier']}
                     for x in game_list]

        # Mando las partidas a redis
        for x in game_list:
            if not db_processed_match.get(x['gameId']):
                db_matchlist.lpush(server, json.dumps(x))
                db_matchlist.ltrim(server, 0, 100000)

        # Evito saturar el bandwidth de la key, disminuyendo las solicitudes
        # en caso de que hayan muchas tareas acumuladas, y por ende, pidiendo datos
        celery_length = db_celery.llen('celery')

        if celery_length > 200:
            sleep(50)


def is_jungler(participant):
    """
    Returna si el participante es jungla o no
    """
    if SMITE_SUMM in [participant['spell1Id'], participant['spell2Id']] and participant['lane'] in [lane_name_to_n['JUNGLE'], lane_name_to_n['NONE']]:
        return True

    return False


def process_match(match):
    """
    Procesa una partida y guarda sus datos en mongo
    """
    match = json.loads(match)
    timestamp = x_days_ago(3)
    # Datos ya procesados o de hace mas de 3 dias los ignoro
    if db_processed_match.get(match['gameId']) is not None or match['timestamp'] <= timestamp:
        print("Partida antigua")
        return
    server = SERVER_REAL_NAME_TO_ROUTE[match['platformId']]
    match_detail = get_match_by_id(match['gameId'], server)

    if match_detail is None:
        sleep(10)
        match_detail = get_match_by_id(match['gameId'], server)

    # Reintento con cada partida hasta 3 veces
    if match_detail is None or len(match_detail) == 0:
        match['retries'] = 1 if "retries" not in match else int(
            match['retries'])+1
        if match['retries'] >= 3:
            return
        else:
            db_matchlist.rpush(server, json.dumps(match))
            return

    bans = []
    c_data = []
    c_pstyle = []

    jungler_list = []

    # Manejo bans de la partida
    for team in match_detail['teams']:
        for ban in team['bans']:
            bans.append(
                {
                    "championId": ban['championId'],
                    "pickTurn": ban['pickTurn'],
                    "division": division_name_to_n[match['division']],
                    "tier": tier_name_to_n[match['tier']],
                    "win": team['win'] == "Win",
                    "gameId": match['gameId'],
                    "teamId": team['teamId'],
                    "server": server,
                    "timestamp": match["timestamp"]
                }
            )

    # Guardo el champ de cada participantId
    participant_id_champ = {}
    participant_id_datarole = {}
    # Manejo datos de campeones y playstyle
    for participant in match_detail['participants']:
        participant_id_champ[participant['participantId']
                             ] = participant['championId']
        participant_id_datarole[participant['participantId']] = {
            "role": role_name_to_n[participant['timeline']['role']],
            "lane": lane_name_to_n[participant['timeline']['lane']],
            "championId": participant['championId'],
            "tier": tier_name_to_n[match['tier']],
            "division": division_name_to_n[match['division']],
            "timestamp": match["timestamp"]
        }
        # Campeones
        data = {
            "championId": participant['championId'],
            "teamId": participant['teamId'],
            "role": role_name_to_n[participant['timeline']['role']],
            "lane": lane_name_to_n[participant['timeline']['lane']],
            "spell1Id": participant['spell1Id'],
            "spell2Id": participant['spell2Id'],
            "gameDuration": match_detail['gameDuration'],
            "tier": tier_name_to_n[match['tier']],
            "division": division_name_to_n[match['division']],
            "gameId": match['gameId'],
            "server": server,
            "participantId": participant['participantId'],
            "timestamp": match["timestamp"]
        }
        if is_jungler(data):
            jungler_list.append(data)

        for x in MATCHES_STATS_KEYS:
            if x in participant['stats']:
                data[x] = participant['stats'][x]

        c_data.append(data)

        # Playstyle
        playstyle = {
            "championId": participant['championId'],
            "teamId": participant['teamId'],
            "role": role_name_to_n[participant['timeline']['role']],
            "lane": lane_name_to_n[participant['timeline']['lane']],
            "gameDuration": match_detail['gameDuration'],
            "tier": tier_name_to_n[match['tier']],
            "division": division_name_to_n[match['division']],
            "gameId": match['gameId'],
            "server": server,
            "timestamp": match["timestamp"]
        }

        for x in PLAYSTYLE_STATS_KEYS:
            if x in participant['stats']:
                playstyle[x] = participant['stats'][x]

        c_pstyle.append(playstyle)

    # Trato de traer la lista de timeline
    timelist_data = get_timelist_by_match_id(match['gameId'], server)
    timelist_stats = []
    print("Pidiendo timelines")
    if timelist_data is None:
        sleep(10)
        timelist_data = get_timelist_by_match_id(match['gameId'], server)

    if timelist_data and 'frames' in timelist_data:
        # Primero solicito la info de los junglas
        for jungler in jungler_list:
            frame = {
                'teamId': jungler['teamId'],
                'tier': jungler['tier'],
                'championId': jungler['championId'],
                'gameTimestamp': jungler['timestamp']
            }
            counter = 0
            for timelist_frame in timelist_data['frames']:
                # Obtengo los primeros 4 minutos
                counter += 1
                if counter > 4:
                    break
                for i, participant in timelist_frame['participantFrames'].items():
                    if int(participant['participantId']) == int(jungler['participantId']):
                        try:
                            frame['x'+str(counter)
                                  ] = participant['position']['x']
                            frame['y'+str(counter)
                                  ] = participant['position']['y']
                        except:
                            pass
                        break
            timelist_stats.append(frame)
        if len(timelist_stats) > 0:
            print("Inserto timelines de los junglas")
            # db_stats.timelines.insert_many(timelist_stats)
            Timeline.objects.bulk_create(
                [Timeline(**x) for x in timelist_stats])

        # ======================================================
        # Ahora busco si tengo jugadores de nivel 17 en adelante
        # ======================================================
        champ_skill_level = {}
        last_frame = timelist_data['frames'][-1]
        for key, participant in last_frame['participantFrames'].items():
            if participant['level'] >= 17:
                champ_skill_level[participant['participantId']] = {"championId": participant_id_champ[participant['participantId']],
                                                                   "skill_count": 0,
                                                                   "timestamp": match["timestamp"],
                                                                   "tier": tier_name_to_n[match['tier']],
                                                                   "division": division_name_to_n[match['division']],
                                                                   "skill_level": {1: 0, 2: 0, 3: 0, 4: 0}
                                                                   }

        if len(champ_skill_level.keys()) > 0:
            for frame in timelist_data['frames']:
                for event in frame['events']:
                    if not 'participantId' in event:
                        continue
                    participantId = event['participantId']
                    if event['type'] == "SKILL_LEVEL_UP" and participantId in champ_skill_level.keys():
                        current_level = champ_skill_level[participantId]['skill_count']
                        skill = event['skillSlot']
                        champ_skill_level[event['participantId']
                                          ][str(current_level+1)] = skill
                        champ_skill_level[participantId]['skill_count'] += 1
                        champ_skill_level[participantId]['skill_level'][skill] += 1

            final_data = []
            for x in champ_skill_level.values():
                # Encuentro el level que falta
                if x['skill_count'] < 17:
                    continue
                if x['skill_count'] == 17:
                    for i, skill_count in x['skill_level'].items():
                        if skill_count == 4:
                            x['18'] = i
                keys = ['tier', 'division', 'timestamp', 'championId']
                obj = {key: x[key] for key in keys}
                block = False
                for i in range(18):
                    try:
                        obj["_"+str(i+1)] = x[str(i+1)]
                    except:
                        print(x)
                        block = True
                        break
                if not block:
                    final_data.append(obj)

            if len(final_data):
                print("Inserto level ups")
                # db_stats.skill_up.insert_many(final_data)
                SkillUp.objects.bulk_create([SkillUp(**x) for x in final_data])

        # =======================================================
        # Ahora busco los eventos de compra de items
        # =======================================================
        first_buy = timelist_data['frames'][1]['events']
        participant_buy = {}
        for c_event in first_buy:
            if not (c_event['type'] == "ITEM_PURCHASED"):
                continue

            partId = c_event['participantId']
            if not partId in participant_buy:
                participant_buy[partId] = {
                    "items": {},
                    "role": participant_id_datarole[partId]['role'],
                    "lane": participant_id_datarole[partId]['lane'],
                    "championId": participant_id_datarole[partId]['championId'],
                    "tier": participant_id_datarole[partId]['tier'],
                    "division": participant_id_datarole[partId]['division'],
                    "timestamp": participant_id_datarole[partId]['timestamp']
                }

            itemId = c_event['itemId']
            if not itemId in participant_buy[partId]['items']:
                participant_buy[partId]['items'][itemId] = 0

            participant_buy[partId]['items'][itemId] += 1

        buys = []

        for key, value in participant_buy.items():
            if len(value['items'].keys()) >= 2 and len(value['items'].keys()) <= 3:
                items = value['items']
                data = value.copy()
                del data['items']
                counter = 0
                for i, x in items.items():
                    counter += 1
                    data['item'+str(counter)] = i
                    data['item'+str(counter)+"_n"] = x

                buys.append(data)

        if len(buys) > 0:
            print("Insertando objetos iniciales en la base de datos")
            # db_stats.first_buy.insert_many(buys)
            FirstBuy.objects.bulk_create([FirstBuy(**x) for x in buys])

    # Inserto en la base
    print("Insertando datos de la partida en la base de datos")
    # db_stats.bans.insert_many(bans)
    Ban.objects.bulk_create([Ban(**x) for x in bans])
    # db_stats.champ_data.insert_many(c_data)
    ChampData.objects.bulk_create([ChampData(**x) for x in c_data])
    # db_stats.champ_playstyle.insert_many(c_pstyle)
    ChampPlaystyle.objects.bulk_create([ChampPlaystyle(**x) for x in c_pstyle])

    # Seteo el gameId para no procesarlo mas veces
    db_processed_match.set(match['gameId'], "True", ex=60*60*24)
