from .riot_api_routes import *
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import DIVISIONS, TIERS, GAME_TYPE,MAIN_GAMEMODE,RANKED_QUEUES
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS,PLAYSTYLE_STATS_KEYS, HIGH_ELO_TIERS
from lol_stats_api.helpers.variables import df_items, trinkets, final_form_items, boots, support_items, jungle_items
from lol_stats_api.helpers.variables import league_data_route, player_sample_route, matches_sample_route, champ_ban_file, champ_data_file, playstyle_data_file

from assets.get_assets_mongodb import *
from lol_stats_api.helpers.mongodb import get_mongo_stats

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

champs_by_id = get_all_champs_name_id()

stats_db = get_mongo_stats()


def generate_builds_stats_by_champ():
    champ_data = pd.read_csv(champ_data_file)
    champ_ban_data = pd.read_csv(champ_ban_file)

    # Filtro partidas de elo alto
    # @TODO Cambiar division por tier
    champ_data = champ_data.loc[champ_data['tier'].isin(HIGH_ELO_TIERS)]
    champ_ban_data = champ_ban_data.loc[champ_ban_data['tier'].isin(HIGH_ELO_TIERS)]

    total_matches = len(champ_data)/10

    champs = champ_data['championId'].unique()
    general_stats=[]
    for champ in champs:
        current_champ_data = champ_data.loc[champ_data['championId']==champ]
        current_champ_bans = champ_ban_data.loc[champ_ban_data['championId']==champ]
        champ_info = generate_champ_data(current_champ_data)

        final_data = {
            "championId":int(champ),
            "pickRate":round(float(len(current_champ_data) * 100 / total_matches), 2),
            "banRate":round(float(len(current_champ_bans) * 100 / total_matches), 2),
            "winRate":round(float(len(current_champ_data.loc[current_champ_data['win']==True] ) * 100 / len(current_champ_data)), 2),
            "champName":champs_by_id[str(champ)]['name'],
            "champInfo":champ_info
        }
        general_stats.append(final_data)

    
    # Limpio la base de datos
    stats_db.stats_by_champ.delete_many({})
    # Guardo las nuevas stats
    stats_db.stats_by_champ.insert_many(general_stats)
    
    
def generate_champ_data(champ_data):
    # Tomo solo las wins
    champ_data = champ_data.loc[champ_data['win']]
    # Busco linea y rol principal
    role = champ_data['role'].mode().iloc[0] 
    lane = champ_data['lane'].mode().iloc[0]
    final_lane = get_lane_from_role({"role":role,"lane":lane})

    build = []
    boots_list = []
    items_chosen = pd.DataFrame()
    for x in range(6):
        final_items = champ_data.loc[champ_data['item'+str(x)].isin(final_form_items)][['item'+str(x),"win"]]
        
        # Si no es support, quito los items de support 
        if final_lane != "Support":
            final_items = final_items.loc[~(final_items['item'+str(x)].isin(support_items))]
        # Si no es jungla, quito los items de jungla
        if final_lane != "Jungla":
            final_items = final_items.loc[~(final_items['item'+str(x)].isin(jungle_items))]
        
        final_items.rename(columns={'item'+str(x):"itemId"}, inplace=True)
        items_chosen = items_chosen.append(final_items)
    
    # Enlisto los items comprados mas veces
    list_items = pd.DataFrame(items_chosen['itemId'].value_counts()).reset_index().rename(columns={"index":"itemId","itemId":"times_buyed"})

    # Detecto las botas mas usadas
    champ_boots = list_items[list_items['itemId'].isin(boots)]
    if len(champ_boots) > 0:
        boots_list.extend(champ_boots.iloc[0:1]['itemId'].tolist())
    
    list_items=list_items.loc[~(list_items['itemId'].isin(boots))].reset_index(drop=True)
    
    # Si es un jungla, enlisto el item de jungla para que vaya primero
    if final_lane == "Jungla":
        # Busco la lista de items
        jungle_list_item = list_items.loc[list_items['itemId'].isin(jungle_items)]
        if len(jungle_list_item)>0:
            jungle_id = jungle_list_item.index[0]
            ids = [jungle_id] + [i for i in range(len(list_items)) if i != jungle_id]
            list_items=list_items.iloc[ids].reset_index(drop=True)
    
    # Si es un support, enlisto el item de support para que vaya primero
    if final_lane == "Support":
        # Busco la lista de items
        supp_list_item = list_items.loc[list_items['itemId'].isin(support_items)]
        if len(supp_list_item)>0:
            supp_id = supp_list_item.index[0]
            ids = [supp_id] + [i for i in range(len(list_items)) if i != supp_id]
            list_items=list_items.iloc[ids].reset_index(drop=True)

    
    # Armo la build con el item mas utilizado como principal
    build = [list_items.iloc[0]['itemId']]
    build_names = item_key_list_to_name(build)

    itemization = champ_data[['item0', 'item1', 'item2',
       'item3', 'item4', 'item5']]
    
    masks = [itemization[itemization==build[0]].dropna(how='all')]

    total_matches= len(itemization)
    next_item_position = 0
    
    while len(build) < 5:
        # Tomo siguiente item
        next_item_position +=1
        if next_item_position >= len(list_items):
            break
        next_item = list_items.iloc[next_item_position]['itemId']
        # Si es una bota o tiene nombre repetido continuo
        if str(next_item) in boots or item_key_list_to_name([next_item])[0] in build_names:
            continue

        percents = []
        force_next = False        
        new_mask = itemization[itemization==next_item].dropna(how='all')

        # Pruebo el porcentaje de uso de el item actual con los ya agregados a la build
        for mask in masks[::-1]:
            data_mask = itemization.loc[mask.index.intersection(new_mask.index)]
            percent = len(data_mask) * 100 / len(new_mask)
            percents.append(percent)

        if min(percents) < 1.7:
            # Si el porcentaje de uso en conjunto es demasiado bajo con alguno de los existentes
            # Entonces procedo a eliminar
            try:
                build.remove(next_item)
            except:
                continue
        else:
            if not next_item in build:
                build.append(next_item)
                masks.append(new_mask)

    # Agregar recomendaciones secundarias
    secondary_items = list_items.loc[~(list_items['itemId'].isin(build))].reset_index(drop=True)
    secondary_items = secondary_items.iloc[0:5]['itemId'].tolist()

    # Trinket
    trinket_item = champ_data['item6'].value_counts().index.tolist()[0:2]

    data = {
        "lane":final_lane,
        "build":{
            "items":[int(x) for x in build],
            "boots":[int(x) for x in boots_list],
            "secondary":[int(x) for x in secondary_items],
            "trinket":[int(x) for x in trinket_item]
        }        
    }
    
    return data


def item_key_list_to_name(klist):
    lista = [df_items.loc[df_items['id']==str(x)]['name'][0] for x in klist]
    return lista


def get_lane_from_role(data):
    role= data['role']
    lane=data['lane']
    if lane == "TOP":
        return "Top"
    elif lane == "MIDDLE":
        return "Mid"
    elif lane == "JUNGLE":
        return "Jungla"
    elif lane == "BOTTOM":
        if role == "DUO_SUPPORT":
            return "Support"
        else:
            return "ADC"
    
    return "Unknown"