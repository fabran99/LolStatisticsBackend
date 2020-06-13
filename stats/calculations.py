from .riot_api_routes import *
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import DIVISIONS, TIERS, HIGH_ELO_TIERS, LOW_ELO_TIERS, POST_DIAMOND_TIERS, PRE_DIAMOND_TIERS
from lol_stats_api.helpers.variables import GAME_TYPE,MAIN_GAMEMODE,RANKED_QUEUES
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS,PLAYSTYLE_STATS_KEYS, HIGH_ELO_TIERS
from lol_stats_api.helpers.variables import df_items, trinkets, final_form_items, boots, support_items, jungle_items
from lol_stats_api.helpers.variables import saved_players_route, saved_champ_ban_route, saved_champ_data_route, saved_playstyle_route

from assets.get_assets_mongodb import *
from lol_stats_api.helpers.mongodb import get_mongo_stats

import json
from django.conf import settings
from os import path
import os
import random
from datetime import datetime as dt 

import pandas as pd
from time import sleep

champs_by_id = get_all_champs_name_id()
from lol_stats_api.helpers.mongodb import get_saved_version
from assets.ddragon_routes import get_current_version
stats_db = get_mongo_stats()


def generate_builds_stats_by_champ():
    champ_data = pd.read_csv(saved_champ_data_route)
    playstyle_data = pd.read_csv(saved_playstyle_route)
    champ_ban_data = pd.read_csv(saved_champ_ban_route)

    now = dt.now()
    patch = get_saved_version()
    if not patch:
        patch = get_current_version()
    # Filtro partidas por tier
    elos = POST_DIAMOND_TIERS+PRE_DIAMOND_TIERS
    df_by_elo={
        "global":{"champ_data":champ_data,
            "champ_ban_data":champ_ban_data,
            "total_matches": len(champ_data)/10,
            "playstyle_data":playstyle_data
        },
        "high_elo":{"champ_data":champ_data.loc[champ_data['tier'].isin(HIGH_ELO_TIERS)],
            "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier'].isin(HIGH_ELO_TIERS)],
            "total_matches": len(champ_data.loc[champ_data['tier'].isin(HIGH_ELO_TIERS)])/10,
            "playstyle_data":playstyle_data.loc[playstyle_data['tier'].isin(HIGH_ELO_TIERS)]
        },
        "low_elo":{"champ_data":champ_data.loc[champ_data['tier'].isin(LOW_ELO_TIERS)],
            "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier'].isin(LOW_ELO_TIERS)],
            "total_matches": len(champ_data.loc[champ_data['tier'].isin(LOW_ELO_TIERS)])/10,
            "playstyle_data":playstyle_data.loc[playstyle_data['tier'].isin(LOW_ELO_TIERS)]
        }
    }

    counterDf = get_counters(df_by_elo['high_elo']['champ_data'])

    # Agrego tier por tier
    for elo in elos:
        df_by_elo[elo]={
            "champ_data":champ_data.loc[champ_data['tier']==elo],
            "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier']==elo],
            "playstyle_data":playstyle_data.loc[playstyle_data['tier']==elo]

        }
        df_by_elo[elo]['total_matches']=len( df_by_elo[elo]['champ_ban_data'])/10
    

    champs = champ_data['championId'].unique()
    general_stats=[]

    radar_rates = {x:[] for x in df_by_elo.keys() }
    champKeys = {}
    
    for champ in champs:
        print("Estadisticas de {}".format(champs_by_id[str(champ)]['name']))
        final_data = {
            "championId":int(champ),
            "champName":champs_by_id[str(champ)]['name'],
            "stats":{}
        }

        current_champ_rows = champ_data.loc[champ_data['championId']==champ]

        role = current_champ_rows['role'].mode().iloc[0] 
        lane = current_champ_rows['lane'].mode().iloc[0]

        data = df_by_elo['high_elo']['champ_data']
        data = data.loc[data['championId']==champ]

        # Estadisticas generales
        
        final_data['lane']=get_lane_from_role({"role":str(role),"lane":str(lane)})
        final_data.update(generate_champ_data(data, final_data['lane']))

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
                'damage':round(current_champ_data['totalDamageDealtToChampions'].mean(), 2)
            }
        
            
            final_data['stats'][elo]['winRate']=round(float(len(current_champ_data.loc[current_champ_data['win']==True] ) * 100 / len(current_champ_data)), 2)
            final_data['stats'][elo]['pickRate']=round(float(len(current_champ_data) * 100 / data['total_matches']), 2)
            final_data['stats'][elo]['banRate']=round(float(len(current_champ_bans) * 100 / data['total_matches']), 2)
            
            final_data['stats'][elo]['damageTypes']=get_damage_statistics(current_champ_data)
            final_data['stats'][elo]['kda']=get_kda(current_champ_data)

            radar_rates[elo].append({
                "kills":final_data['stats'][elo]['kda']['kills'],
                "deaths":final_data['stats'][elo]['kda']['deaths'],
                "assists":final_data['stats'][elo]['kda']['assists'],
                "damage":final_data['stats'][elo]['damage'],
                "championId":int(champ),
                "winRate":final_data['stats'][elo]['winRate'],
                "pickRate":final_data['stats'][elo]['pickRate'],
                "banRate":final_data['stats'][elo]['banRate'],
                "farmPerMin":final_data['stats'][elo]['farmPerMin'],
            })
    

        final_data['date']=now
        final_data['patch']=patch
        champKeys[champ]=len(general_stats)
        general_stats.append(final_data)


    # Counters
    byLane = {
    "Top":[],
    "Mid":[],
    "Jungla":[],
    "Support":[],
    "ADC":[]
    }

    for x in byLane.keys():
        byLane[x] = [y['championId'] for y in general_stats if y['lane']==x]

    for champ in champs:
        counterDict[champ]={
            'counters':[],
            'counterBy':[]
        }
        lane = general_stats[champKeys[champ]]

        counters = counterDf.loc[counterDf['winner']==champ]['looser'].value_counts().index.tolist()
        print(counters)
        return False




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


def get_counters(data):
    gameIds = data['gameId'].unique()
    counterList = []

    for gameId in gameIds:
        durations = data.loc[data['gameId']==gameId]['gameDuration'].unique()
        for duration in durations:
            matchData = data.loc[(data['gameId']==gameId) & (data['gameDuration']==duration)]
            loosers = matchData.loc[matchData['win']==False]['championId'].unique()
            winners = matchData.loc[matchData['win']==True]['championId'].unique()

            winList = []
            for looser in loosers:
                for winner in winners:
                    winList.append({"looser":looser, 'winner':winner})
            counterList.extend(winList)
    counterDf = pd.DataFrame(counterList)
    return counterDf

