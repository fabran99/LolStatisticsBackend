from stats.riot_api_routes import *
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import DIVISIONS, TIERS, HIGH_ELO_TIERS, LOW_ELO_TIERS, POST_DIAMOND_TIERS, PRE_DIAMOND_TIERS
from lol_stats_api.helpers.variables import GAME_TYPE,MAIN_GAMEMODE,RANKED_QUEUES
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS,PLAYSTYLE_STATS_KEYS, HIGH_ELO_TIERS
from stats.getItemDfs import df_items, trinkets, final_form_items, boots, support_items, jungle_items,df_all_items
from lol_stats_api.helpers.variables import tier_n_to_name, role_n_to_name, division_n_to_name, lane_n_to_name, tier_name_to_n, lane_name_to_n,\
    role_name_to_n, division_name_to_n

from lol_stats_api.helpers.variables import MIN_GAME_DURATION, EARLY_GAME_RANGE, MID_GAME_RANGE, LATE_GAME_RANGE, \
    PHASE_BAD_RANGE, PHASE_GOOD_RANGE, PHASE_OK_RANGE

from assets.get_assets_mongodb import *
from lol_stats_api.helpers.mongodb import get_mongo_stats
import re
import json
from django.conf import settings
from os import path
import os
import random
from datetime import datetime as dt 

import pandas as pd
import numpy as np
from time import sleep
from redis import Redis

champs_by_id = get_all_champs_name_id()
from lol_stats_api.helpers.mongodb import get_saved_version
from assets.ddragon_routes import get_current_version
import psycopg2
from django_pandas.io import read_frame

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))

stats_db = get_mongo_stats()

param_dic = {
    "host":os.environ.get('PSQL_HOSTNAME'),
    "database":os.environ.get('PSQL_DB_NAME'),
    "user":os.environ.get('PSQL_USERNAME'),
    "password":os.environ.get('PSQL_PASSWORD')
}


def strListToQuots(strs):
    return ['"{}"'.format(x) for x in strs]

# Generar dataframes
def get_champ_data_df():
    """
    Devuelve el dataframe de datos de campeon
    """
    conn = psycopg2.connect(**param_dic)
    cursor = conn.cursor()
    print("Solicitando datos de campeones")
    columns = ['championId','teamId','role','lane','spell1Id','spell2Id',\
        'gameDuration','tier','gameId',\
        'win','item0','item1','item2','item3','item4','item5','item6',\
            'perk0','perk1','perk2','perk3','perk4','perk5',\
        'perkPrimaryStyle','perkSubStyle','statPerk0','statPerk1','statPerk2']

    columns = strListToQuots(columns)
    query = "SELECT {} FROM public.stats_champdata".format(", ".join(columns))
    df = pd.read_sql(query, conn)
    return df


def get_bans_df():
    """
    Devuelve el dataframe con los bans
    """
    conn = psycopg2.connect(**param_dic)
    cursor = conn.cursor()
    print("Solicitando bans")
    columns = ['championId', 'tier','win','gameId','teamId']

    columns = strListToQuots(columns)
    query = "SELECT {} FROM public.stats_ban".format(", ".join(columns))
    df = pd.read_sql(query, conn)
    return df


def get_playstyle_df():
    """
    Devuelve el dataframe con el playstyle
    """
    conn = psycopg2.connect(**param_dic)
    cursor = conn.cursor()
    print("Solicitando playstyle")
    columns = ['championId','totalMinionsKilled','neutralMinionsKilled','neutralMinionsKilledTeamJungle',\
        'neutralMinionsKilledEnemyJungle','gameDuration', 'tier','kills','deaths','assists',\
        'totalDamageDealtToChampions','magicDamageDealtToChampions','physicalDamageDealtToChampions',]
    
    columns = strListToQuots(columns)
    query = "SELECT {} FROM public.stats_champplaystyle".format(", ".join(columns))
    df = pd.read_sql(query, conn)
    return df


def get_skill_up_df():
    """
    Devuelve el dataframe con los level up
    """
    conn = psycopg2.connect(**param_dic)
    cursor = conn.cursor()
    print("Solicitando skills up")
    columns = ["tier","championId"] + ["_"+str(i+1) for i in range(18)]
    
    columns = strListToQuots(columns)
    query = "SELECT {} FROM public.stats_skillup".format(", ".join(columns))
    df = pd.read_sql(query, conn)
    return df


def get_first_buy_df():
    """
    Devuelve el dataframe con los first_buy
    """
    conn = psycopg2.connect(**param_dic)
    cursor = conn.cursor()
    print("Solicitando first_buy")
    columns = ["tier","championId","role","lane"]
    for x in range(1,4):
        columns.extend(["item"+str(x), "item"+str(x)+"_n"])
    columns = strListToQuots(columns)
    query = "SELECT {} FROM public.stats_firstbuy".format(", ".join(columns))
    df = pd.read_sql(query, conn)
    return df


# Calculos de build
def generate_builds_stats_by_champ():
    now = dt.now()
    patch = get_saved_version()
    if not patch:
        patch = get_current_version()
    # Filtro partidas por tier
    elos = POST_DIAMOND_TIERS+PRE_DIAMOND_TIERS

    champ_data = get_champ_data_df()
    champ_ban_data = get_bans_df()
    playstyle_data = get_playstyle_df()
    skill_data = get_skill_up_df()
    first_buy_data = get_first_buy_df()

    df_by_elo={}
    # Agrego tier por tier
    for elo in elos:
        t = tier_name_to_n[elo]
        df_by_elo[elo]={
            "champ_data":champ_data.loc[champ_data['tier']==t],
            "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier']==t],
            "playstyle_data":playstyle_data.loc[playstyle_data['tier']==t],
            "skill_data":skill_data.loc[skill_data['tier']==t],
            "first_buy_data":first_buy_data.loc[first_buy_data['tier']==t],
        }
        df_by_elo[elo]['total_matches']=len(df_by_elo[elo]['champ_data'])/10

    df_by_elo['global']={"champ_data":champ_data,
             "champ_ban_data":champ_ban_data,
             "total_matches": len(champ_data)/10,
             "playstyle_data":playstyle_data,
             "skill_data":skill_data,
             "first_buy_data":first_buy_data
    }

    high_elo_numbers = [tier_name_to_n[x] for x in HIGH_ELO_TIERS]
    low_elo_numbers = [tier_name_to_n[x] for x in LOW_ELO_TIERS]

    df_by_elo["high_elo"]={"champ_data":champ_data.loc[champ_data['tier'].isin(high_elo_numbers)],
        "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier'].isin(high_elo_numbers)],
        "total_matches": len(champ_data.loc[champ_data['tier'].isin(high_elo_numbers)])/10,
        "playstyle_data":playstyle_data.loc[playstyle_data['tier'].isin(high_elo_numbers)],
        "skill_data":skill_data.loc[skill_data['tier'].isin(high_elo_numbers)],
        "first_buy_data":first_buy_data.loc[first_buy_data['tier'].isin(high_elo_numbers)],
    }
    df_by_elo["low_elo"]={"champ_data":champ_data.loc[champ_data['tier'].isin(low_elo_numbers)],
        "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier'].isin(low_elo_numbers)],
        "total_matches": len(champ_data.loc[champ_data['tier'].isin(low_elo_numbers)])/10,
        "playstyle_data":playstyle_data.loc[playstyle_data['tier'].isin(low_elo_numbers)],
        "skill_data":skill_data.loc[skill_data['tier'].isin(low_elo_numbers)],
        "first_buy_data":first_buy_data.loc[first_buy_data['tier'].isin(low_elo_numbers)]
    }
    

    champs = champ_data['championId'].unique()
    general_stats=[]

    radar_rates = {x:[] for x in df_by_elo.keys() }
    champKeys = {}

    byLane = {
    "Top":[],
    "Mid":[],
    "Jungla":[],
    "Support":[],
    "ADC":[],
    }
    
    for champ in champs:
        print("Estadisticas de {}".format(champs_by_id[str(champ)]['name']))
        final_data = {
            "championId":int(champ),
            "champName":champs_by_id[str(champ)]['name'],
            "stats":{}
        }

        current_champ_rows = champ_data.loc[champ_data['championId']==champ]

        # Detecto lineas
        lane_distribution = current_champ_rows['lane'].value_counts()
        main_lane = lane_distribution.index.tolist()[0]
        second_lane = lane_distribution.index.tolist()[1]
        total = lane_distribution.iloc[0] + lane_distribution.iloc[1]
        lanes = [main_lane]
        # Porcentaje en cada linea
        main_lane_percent = lane_distribution.iloc[0] * 100/total
        second_lane_percent = lane_distribution.iloc[1] * 100/total
        percents = [main_lane_percent, second_lane_percent]

        # Si la linea secundaria tiene mas del 20% de uso entonces la muestro
        if second_lane_percent >= 20:
            lanes.append(second_lane)
        else:
            percents=[100]
        
        final_data['lanes']=[]
        final_data['info_by_lane']=[]

        # Calculo fases
        final_data['phases_winrate']=get_phases(current_champ_rows)

        lanes_names = []
        for i,x in enumerate(lanes):
            if len(lanes)>1:
                lane_rows = current_champ_rows.loc[current_champ_rows['lane']==x]
            else:
                lane_rows = current_champ_rows.copy()
            nrows = len(lane_rows)
            role = role_n_to_name[lane_rows['role'].mode().iloc[0]]
            lane = lane_n_to_name[x]
            
            # Saco el nombre de la linea
            lane_name = get_lane_from_role({"role":str(role),"lane":str(lane)})

            # Evito lineas repetidas
            if lane_name in final_data['lanes']:
                lanes = [x for ind, x in enumerate(lanes) if ind != i ]
                continue
            lanes_names.append(lane_name)
            final_data['lanes'].append(lane_name)
            if not champ in byLane[lane_name]:
                byLane[lane_name].append(champ)

            # =====================================
            # Calculo info para datos de esta linea
            # =====================================

            # Datos de early buy
            champ_first_buy = df_by_elo["high_elo"]['first_buy_data']
            champ_first_buy = champ_first_buy.loc[(champ_first_buy['championId']==champ) & (champ_first_buy['lane']==x)]
            first_buy = get_first_buy(champ_first_buy)
            # Datos generales
            data = lane_rows.loc[lane_rows['tier'].isin(high_elo_numbers)]

            if len(data) == 0:
                data = lane_rows.copy()

            champ_info = generate_champ_data(data, lane_name)
            champ_info['lane_percent']=round(percents[i], 2)
            champ_info['lane']=lane_name
            champ_info['build']['starter']=first_buy

            final_data['info_by_lane'].append(champ_info)
        
    
        # Calculo skill order
        skills = df_by_elo['high_elo']['skill_data']
        skills = skills.loc[skills['championId']==champ]

        if len(skills) == 0:
            skills = df_by_elo['global']['skill_data']
            skills = skills.loc[skills['championId']==champ]
        final_data["skill_order"]= get_skill_order(skills)


        # Estadisticas generales
        for elo, data in df_by_elo.items():
            current_champ_data = data['champ_data'].loc[data['champ_data']['championId']==champ]
            current_champ_bans = data['champ_ban_data'].loc[data['champ_ban_data']['championId']==champ]
            current_champ_playstyle = data['playstyle_data'].loc[data['playstyle_data']['championId']==champ]

            # Si no tengo estadisticas de este elo, uso las globales
            if len(current_champ_data) == 0:
                current_champ_data = df_by_elo['global']['champ_data'].loc[df_by_elo['global']['champ_data']['championId']==champ]
            if len(current_champ_bans) == 0:
                current_champ_bans = df_by_elo['global']['champ_ban_data'].loc[df_by_elo['global']['champ_ban_data']['championId']==champ]
            if len(current_champ_playstyle) == 0:
                current_champ_playstyle = df_by_elo['global']['playstyle_data'].loc[df_by_elo['global']['playstyle_data']['championId']==champ]

            final_data['stats'][elo]={
                'farmPerMin':get_farm(current_champ_playstyle),
                'totalMatches':data['total_matches'],
                'damage':round(current_champ_playstyle['totalDamageDealtToChampions'].mean(), 2)
            }

            # El winrate va por linea
            final_data['stats'][elo]['winRate']=[]
            for i,x in enumerate(lanes):
                rows = current_champ_data.loc[current_champ_data['lane']==x]
                if len(rows) ==0:
                    rows = current_champ_data.copy()
                final_data['stats'][elo]['winRate'].append({
                    "lane":lanes_names[i],
                    "winRate":round(float(len(rows.loc[rows['win']==True] ) * 100 / len(rows)), 2)
                })

            
            final_data['stats'][elo]['pickRate']=round(float(len(current_champ_data) * 100 / data['total_matches']), 2)
            final_data['stats'][elo]['banRate']=round(float(len(current_champ_bans) * 100 / data['total_matches']), 2)
            
            final_data['stats'][elo]['damageTypes']=get_damage_statistics(current_champ_playstyle)
            final_data['stats'][elo]['kda']=get_kda(current_champ_playstyle)

            radar_rates[elo].append({
                "kills":final_data['stats'][elo]['kda']['kills'],
                "deaths":final_data['stats'][elo]['kda']['deaths'],
                "assists":final_data['stats'][elo]['kda']['assists'],
                "damage":final_data['stats'][elo]['damage'],
                "championId":int(champ),
                "winRate":final_data['stats'][elo]['winRate'][0]['winRate'],
                "pickRate":final_data['stats'][elo]['pickRate'],
                "banRate":final_data['stats'][elo]['banRate'],
                "farmPerMin":final_data['stats'][elo]['farmPerMin'],
            })
    

        final_data['date']=now
        final_data['patch']=patch
        champKeys[champ]=len(general_stats)
        general_stats.append(final_data)


    for champ in champs:
        lanes = general_stats[champKeys[champ]]['lanes']
        champsInLane = []
        for x in lanes:
            champsInLane.extend(byLane[x])

        champsInLane = list(set(champsInLane))
        percents = []

        counterDf = get_counters(df_by_elo['global']['champ_data'], champ, champsInLane )
        for x in champsInLane:
            total = counterDf.loc[((counterDf['winner']==x) & (counterDf['loser']==champ)) | ((counterDf['winner']==champ) & (counterDf['loser']==x))]
            if len(total) == 0:
                continue
            win = len(counterDf.loc[(counterDf['winner']==champ) & (counterDf['loser']==x)])
            percents.append({
                "championId":x,
                "winRate": win*100/len(total)
            })

        winrate=pd.DataFrame(percents).sort_values("winRate")
        strongAgainst = winrate.tail(5)
        weakAgainst = winrate.head(5)
        
        strongAgainst = strongAgainst.to_dict("records")
        weakAgainst = weakAgainst.to_dict("records")


        general_stats[champKeys[champ]]['strongAgainst']=strongAgainst
        general_stats[champKeys[champ]]['weakAgainst']=weakAgainst


    # stats para grafica radar
    radar_stats = []

    for key, value in radar_rates.items():
        tmp_df = pd.DataFrame(value)
        keys = ['kills','assists','deaths','damage','pickRate','winRate','banRate','farmPerMin']

        tmp_dict = {
            "patch":patch,
            "date":now,
            "elo":key
        }
        for x in keys:
            tmp_dict[x]= {
                "min":round(tmp_df[x].min(), 2),
                "max":round(tmp_df[x].max(), 2),
                "mean":round(tmp_df[x].mean(), 2),
            }

        radar_stats.append(tmp_dict)
    
    # Guardo las nuevas stats
    for stat in general_stats:
        print("Insertando datos actualizados de {}".format(stat['champName']))
        stats_db.stats_by_champ.replace_one({'championId':stat['championId'], 'patch':patch},stat, upsert=True)

    for stat in radar_stats:
        print("Insertando estadisticas generales de elo {}".format(stat['elo']))
        stats_db.radar_stats.replace_one({"elo":stat['elo'], 'patch':patch}, stat, upsert=True)

    db_metadata.set("last_calculated_patch", patch)
    


def get_first_buy(data):
    df = data.copy()[["item1","item2","item3"]]
    groups = df.groupby(df.columns.tolist(),as_index=False).size()\
        .reset_index().rename(columns={0:"records"}).sort_values("records",ascending=False).reset_index(drop=True)

    best_order = groups.iloc[0].to_dict()
    final_buy = []
    for x in range(1,4):
        current_item = int(best_order['item'+str(x)])
        if str(current_item) in df_all_items.id:
            final_buy.append(current_item)
    
    return final_buy

    

def get_skill_order(champ_data):
    df = champ_data[["_"+str(x+1) for x in range(18)]]
    groups = df.groupby(df.columns.tolist(),as_index=False).size()\
        .reset_index().rename(columns={0:"records"}).sort_values("records",ascending=False).reset_index(drop=True)
    
    best_order = groups.iloc[0].to_dict()
    best_order = {x.split("_")[1]:int(y) for x,y in best_order.items() if x not in ["records"]}
    return best_order



def generate_champ_data(champ_data_original, lane):
    # Tomo solo las wins
    champ_data = champ_data_original.loc[champ_data_original['win']]
    if len(champ_data) < 5:
        champ_data = champ_data_original
    # Busco linea y rol principal
    build = []
    boots_list = []
    items_chosen = pd.DataFrame()
    for x in range(6):
        final_items = champ_data.loc[champ_data['item'+str(x)].isin(final_form_items)][['item'+str(x),"win"]]
        
        # Si no es support, quito los items de support 
        if lane != "Support":
            final_items = final_items.loc[~(final_items['item'+str(x)].isin(support_items))]
        # Si no es jungla, quito los items de jungla
        if lane != "Jungla":
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
    if lane == "Jungla":
        # Busco la lista de items
        jungle_list_item = list_items.loc[list_items['itemId'].isin(jungle_items)]
        if len(jungle_list_item)>0:
            jungle_id = jungle_list_item.index[0]
            ids = [jungle_id] + [i for i in range(len(list_items)) if i != jungle_id]
            list_items=list_items.iloc[ids].reset_index(drop=True)
    
    # Si es un support, enlisto el item de support para que vaya primero
    if lane == "Support":
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
        "build":{
            "items":[int(x) for x in build],
            "boots":[int(x) for x in boots_list],
            "secondary":[int(x) for x in secondary_items],
            "trinket":[int(x) for x in trinket_item]
        }        
    }

    # Manejo las runas
    
    primary_stone = champ_data['perkPrimaryStyle'].value_counts().index[0]
    secondary_stone = champ_data.loc[~(champ_data['perkSubStyle']==primary_stone)]['perkSubStyle'].value_counts().index[0]
    # Runas
    runes = {
        "primary":{
            "main":int(primary_stone)
        },
        "secondary":{
            "main":int(secondary_stone)
        },
        "perks":{}
    }

    runes_used = []
    for x in range(4):
        rune = champ_data.loc[champ_data['perkPrimaryStyle']==primary_stone]['perk'+str(x)].value_counts()
        position = 0 
        while int(rune.index[position]) in runes_used:
            position += 1
        rune = int(rune.index[position])
        runes_used.append(rune)
        runes['primary']['perk'+str(x)]=rune

    runes_used = [] 
    for x in range(4,6):
        rune = champ_data.loc[champ_data['perkSubStyle']==secondary_stone]['perk'+str(x)].value_counts()
        position = 0 
        while int(rune.index[position]) in runes_used:
            position += 1
        rune = int(rune.index[position])
        runes_used.append(rune)
        runes['secondary']['perk'+str(x)]=rune

    # Perks
    for x in range(3):
        perk = int(champ_data['statPerk'+str(x)].value_counts().index[0])
        runes['perks']['statPerk'+str(x)]=perk


    data['runes']=runes   

    # Spells
    spells = champ_data[['spell1Id','spell2Id']]

    spells = spells['spell1Id'].append(spells['spell2Id'])
    flash = 4
    smite = 11

    spells = spells.value_counts().index[0:2]
    spells = [int(x) for x in spells]
    if lane == 'Jungla' and not (smite in spells):
        if flash in spells:
            spells =[flash]
        if len(spells) >1:
            spells = spells[0:1]
        
        spells.append(smite)

    # Ordeno el flash
    if flash in spells:
        spells = [x for x in spells if x != flash]
        spells.append(flash)
        spells.reverse()
    data['spells']=spells
    
    return data


def item_key_list_to_name(klist):
    lista = [df_items.loc[df_items['id']==str(int(x))]['name'][0] for x in klist]
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
        if role == "DUO_CARRY":
            return "ADC"
        else:
            return "Support"
    
    return "Jungla"


def get_damage_statistics(data):
    physical=data['physicalDamageDealtToChampions'].sum()
    magic=data['magicDamageDealtToChampions'].sum()
    total=data['totalDamageDealtToChampions'].sum()
    true = total - physical - magic

    damages={
        "physical": round(physical * 100 / total, 2),
        "magic": round(magic  * 100 / total, 2),
        "true": round(true  * 100 / total, 2),
    }

    return damages


def get_kda(data):
    return {
        'kills':round(data['kills'].mean(), 2),
        'deaths':round(data['deaths'].mean(), 2),
        'assists':round(data['assists'].mean(), 2)
    }


def get_farm(data):
    data['farm']=data['totalMinionsKilled']+data['neutralMinionsKilled']+data['neutralMinionsKilledTeamJungle']+data['neutralMinionsKilledEnemyJungle'] 
    return round(((data['farm']/data['gameDuration'])*60).mean(), 2)


def get_counters(data, champ, same_lane_champs ):
    print("Calculando counters de {}".format(champs_by_id[str(champ)]['name']))
    counterList = []
    gameIds_with_champ = data.loc[data['championId']==champ]['gameId'].unique()
    gameIds = data.loc[(data['championId'].isin(same_lane_champs)) & (data['gameId'].isin(gameIds_with_champ))]['gameId'].unique()

    games = data.loc[data['gameId'].isin(gameIds)]
    games = games.loc[games['championId'].isin(same_lane_champs + [champ])]

    champ_wins = games.loc[(games['win']) & (games['championId']==champ)]
    champ_losses = games.loc[(~games['win']) & (games['championId']==champ)]
    
    other_losses = games.loc[(games['championId'] != champ ) & (games['gameId'].isin(champ_wins['gameId'].unique())) & ~(games['win']) ]
    other_wins = games.loc[(games['championId'] != champ ) & (games['gameId'].isin(champ_losses['gameId'].unique())) & (games['win']) ]

    other_wins.loc[:,'loser'] = champ
    other_wins = other_wins.rename(columns= {"championId":"winner"})[['loser','winner']]

    other_losses.loc[:,'winner'] = champ
    other_losses = other_losses.rename(columns= {"championId":"loser"})[['loser','winner']]

    counterDf = pd.concat([other_wins, other_losses], ignore_index=True)
    return counterDf


def get_phases(data):
    """
    Retorna valores del 1 al 3 dependiendo del winrate de un campeon en 
    cada fase del juego
    """
    phase_list = ["early","mid","late"]
    # defaulteo a OK
    phases = {x:2 for x in phase_list}
    df = data.loc[data['gameDuration']>MIN_GAME_DURATION]

    early_games = df.loc[(data['gameDuration']>EARLY_GAME_RANGE[0]) & (data['gameDuration']<=EARLY_GAME_RANGE[1])]
    mid_games = df.loc[(data['gameDuration']>MID_GAME_RANGE[0]) & (data['gameDuration']<=MID_GAME_RANGE[1])]
    late_games = df.loc[(data['gameDuration']>LATE_GAME_RANGE[0]) & (data['gameDuration']<=LATE_GAME_RANGE[1])]

    games_ar = [early_games, mid_games, late_games]

    phase_ranges = [PHASE_BAD_RANGE, PHASE_OK_RANGE, PHASE_GOOD_RANGE]

    for i in range(len(phase_list)):
        games = games_ar[i]
        phase = phase_list[i]

        total = len(games)
        if total ==0:
            continue
        wins = len(games.loc[games['win']==1])
        winrate =  wins*100/total

        for index, x in enumerate(phase_ranges):
            if winrate > x[0] and winrate<=x[1]:
                phases[phase]=index+1
                break


    return phases

