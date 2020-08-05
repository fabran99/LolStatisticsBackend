from stats.riot_api_routes import *
from lol_stats_api.helpers.variables import SERVER_ROUTES, SERVER_REAL_NAME_TO_ROUTE
from lol_stats_api.helpers.variables import DIVISIONS, TIERS, HIGH_ELO_TIERS, LOW_ELO_TIERS, POST_DIAMOND_TIERS, PRE_DIAMOND_TIERS
from lol_stats_api.helpers.variables import GAME_TYPE,MAIN_GAMEMODE,RANKED_QUEUES
from lol_stats_api.helpers.variables import MATCHES_STATS_KEYS,PLAYSTYLE_STATS_KEYS, HIGH_ELO_TIERS
from lol_stats_api.helpers.variables import df_items, trinkets, final_form_items, boots, support_items, jungle_items
from lol_stats_api.helpers.variables import tier_n_to_name, role_n_to_name, division_n_to_name, lane_n_to_name, tier_name_to_n, lane_name_to_n,\
    role_name_to_n, division_name_to_n


from assets.get_assets_mongodb import *
from lol_stats_api.helpers.mongodb import get_mongo_stats, get_monary
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
# from lol_stats_api import tasks

db_metadata = Redis(db=os.getenv("REDIS_METADATA_DB"))

stats_db = get_mongo_stats()
monary_db =  get_monary()

def monary_array_to_df(arrays, columns, column_types):
    y = np.array(np.ma.array(arrays).filled())
    df = pd.DataFrame(y.T, columns=columns)
    df=df.dropna()

    for column, column_type in zip(columns, column_types):
        # df[column]=df[column].str.decode("utf-8")
        if column_type =='bool':
            df = df.replace({column:{1:True,0:False}})
        elif "int" in column_type:
            df[column]=pd.to_numeric(df[column])
        
    return df


def correct_string_data(df):
    if 'role' in df.columns:
        df['role']=df['role']=df['role'].apply(lambda x:role_n_to_name[x])

    if 'lane' in df.columns:
        df['lane']=df['lane']=df['lane'].apply(lambda x:lane_n_to_name[x])

    if 'tier' in df.columns:
        df['tier']=df['tier']=df['tier'].apply(lambda x:tier_n_to_name[x])

    if 'division' in df.columns:
        df['division']=df['division']=df['division'].apply(lambda x:division_n_to_name[x])

    return df
        

def get_champ_data_df(tier):
    """
    Devuelve el dataframe de datos de campeon
    """
    print("Solicitando datos de campeones - {}".format(tier_n_to_name[tier]))
    columns = ['championId','teamId','role','lane','spell1Id','spell2Id',\
        'gameDuration','tier','gameId',\
        'win','item0','item1','item2','item3','item4','item5','item6',\
            'perk0','perk1','perk2','perk3','perk4','perk5',\
        'perkPrimaryStyle','perkSubStyle','statPerk0','statPerk1','statPerk2']

    columns_type = ['uint16','uint16','uint16','uint16','uint32','uint32',\
        'uint32','uint16','uint64','bool','uint32','uint32',\
        'uint32','uint32','uint32','uint32','uint32','uint32',\
        'uint32','uint32','uint32','uint32','uint32','uint32','uint32','uint32','uint32',\
        'uint32']

    champ_data_df = pd.DataFrame()
    for data in monary_db.block_query("statistics","champ_data",{"tier":tier},columns, columns_type, block_size=20000):
        df = monary_array_to_df(data, columns, columns_type)
        champ_data_df = pd.concat([champ_data_df, df], ignore_index=True)
        print("{} datos encontrados".format(len(champ_data_df)))
        if len(champ_data_df) >= 500000:
            break

    # champ_data_df = correct_string_data(champ_data_df)
    return champ_data_df


def get_bans_df(tier):
    """
    Devuelve el dataframe con los bans
    """
    print("Solicitando bans - {}".format(tier_n_to_name[tier]))
    columns = ['championId', 'tier','win','gameId','teamId']
    columns_type = ['uint32','uint32','bool','uint64','uint32']

    champ_ban_df = pd.DataFrame()
    for data in monary_db.block_query("statistics","bans",{"tier":tier},columns, columns_type, block_size=30000):
        df = monary_array_to_df(data, columns, columns_type)
        champ_ban_df = pd.concat([champ_ban_df, df], ignore_index=True)
        print("{} datos encontrados".format(len(champ_ban_df)))
        if len(champ_ban_df) >= 500000:
            break

    # champ_ban_df = correct_string_data(champ_ban_df)
    return champ_ban_df


def get_playstyle_df(tier):
    """
    Devuelve el dataframe con el playstyle
    """
    print("Solicitando playstyle - {}".format(tier_n_to_name[tier]))
    columns = ['championId','totalMinionsKilled','neutralMinionsKilled','neutralMinionsKilledTeamJungle',\
        'neutralMinionsKilledEnemyJungle','gameDuration', 'tier','kills','deaths','assists',\
        'totalDamageDealtToChampions','magicDamageDealtToChampions','physicalDamageDealtToChampions',]
    columns_type = ['uint32','uint32','uint32','uint32','uint32','uint32','uint32','uint32','uint32','uint32',\
        'uint32','uint32','uint32']

    champ_playstyle_df = pd.DataFrame()
    for data in monary_db.block_query("statistics","champ_playstyle",{"tier":tier},columns, columns_type, block_size=30000):
        df = monary_array_to_df(data, columns, columns_type)
        champ_playstyle_df = pd.concat([champ_playstyle_df, df], ignore_index=True)
        print("{} datos encontrados".format(len(champ_playstyle_df)))
        if len(champ_playstyle_df) >= 500000:
            break

    return champ_playstyle_df


def get_skill_up_df(tier):
    """
    Devuelve el dataframe con los level up
    """
    print("Solicitando skills up - {}".format(tier_n_to_name[tier]))
    columns = ["tier","championId"] + [str(i+1) for i in range(18)]
    columns_type = ["uint32" for x in range(len(columns))]

    skills_df = pd.DataFrame()
    for data in monary_db.block_query("statistics","skill_up",{"tier":tier},columns, columns_type, block_size=30000):
        df = monary_array_to_df(data, columns, columns_type)
        skills_df = pd.concat([skills_df, df], ignore_index=True)
        print("{} datos encontrados".format(len(skills_df)))
        if len(skills_df) >= 500000:
            break

    return skills_df


def generate_builds_stats_by_champ():
    now = dt.now()
    patch = get_saved_version()
    if not patch:
        patch = get_current_version()
    # Filtro partidas por tier
    elos = POST_DIAMOND_TIERS+PRE_DIAMOND_TIERS

    df_by_elo={}
    # Agrego tier por tier
    for elo in elos:
        df_by_elo[elo]={
            "champ_data":get_champ_data_df(tier_name_to_n[elo]),
            "champ_ban_data":get_bans_df(tier_name_to_n[elo]),
            "playstyle_data":get_playstyle_df(tier_name_to_n[elo]),
            "skill_data":get_skill_up_df(tier_name_to_n[elo])
        }
        df_by_elo[elo]['total_matches']=len( df_by_elo[elo]['champ_data'])/10

    # Sumo total
    champ_data = pd.concat([x['champ_data'] for x in df_by_elo.values()], ignore_index=True).reset_index()
    champ_ban_data = pd.concat([x['champ_ban_data'] for x in df_by_elo.values()], ignore_index=True).reset_index()
    playstyle_data = pd.concat([x['playstyle_data'] for x in df_by_elo.values()], ignore_index=True).reset_index()
    skill_data = pd.concat([x['skill_data'] for x in df_by_elo.values()], ignore_index=True).reset_index()

    df_by_elo['global']={"champ_data":champ_data,
             "champ_ban_data":champ_ban_data,
             "total_matches": len(champ_data)/10,
             "playstyle_data":playstyle_data,
             "skill_data":skill_data
    }

    high_elo_numbers = [tier_name_to_n[x] for x in HIGH_ELO_TIERS]
    low_elo_numbers = [tier_name_to_n[x] for x in LOW_ELO_TIERS]

    df_by_elo["high_elo"]={"champ_data":champ_data.loc[champ_data['tier'].isin(high_elo_numbers)],
        "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier'].isin(high_elo_numbers)],
        "total_matches": len(champ_data.loc[champ_data['tier'].isin(high_elo_numbers)])/10,
        "playstyle_data":playstyle_data.loc[playstyle_data['tier'].isin(high_elo_numbers)],
        "skill_data":skill_data.loc[skill_data['tier'].isin(high_elo_numbers)],
    }
    df_by_elo["low_elo"]={"champ_data":champ_data.loc[champ_data['tier'].isin(low_elo_numbers)],
        "champ_ban_data":champ_ban_data.loc[champ_ban_data['tier'].isin(low_elo_numbers)],
        "total_matches": len(champ_data.loc[champ_data['tier'].isin(low_elo_numbers)])/10,
        "playstyle_data":playstyle_data.loc[playstyle_data['tier'].isin(low_elo_numbers)],
        "skill_data":skill_data.loc[skill_data['tier'].isin(low_elo_numbers)]
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

        role = role_n_to_name[current_champ_rows['role'].mode().iloc[0]]
        lane = lane_n_to_name[current_champ_rows['lane'].mode().iloc[0]]

        data = df_by_elo['high_elo']['champ_data']
        data = data.loc[data['championId']==champ]
        skills = df_by_elo['high_elo']['skill_data']
        skills = skills.loc[skills['championId']==champ]

        if len(skills) == 0:
            skills = df_by_elo['global']['skill_data']
            skills = skills.loc[skills['championId']==champ]
        # Estadisticas generales
        
        final_data['lane']=get_lane_from_role({"role":str(role),"lane":str(lane)})
        final_data["skill_order"]= get_skill_order(skills)

        byLane[final_data['lane']].append(champ)
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
                'damage':round(current_champ_playstyle['totalDamageDealtToChampions'].mean(), 2)
            }
        
            
            final_data['stats'][elo]['winRate']=round(float(len(current_champ_data.loc[current_champ_data['win']==True] ) * 100 / len(current_champ_data)), 2)
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
                "winRate":final_data['stats'][elo]['winRate'],
                "pickRate":final_data['stats'][elo]['pickRate'],
                "banRate":final_data['stats'][elo]['banRate'],
                "farmPerMin":final_data['stats'][elo]['farmPerMin'],
            })
    

        final_data['date']=now
        final_data['patch']=patch
        champKeys[champ]=len(general_stats)
        general_stats.append(final_data)


    for champ in champs:
        lane = general_stats[champKeys[champ]]['lane']
        champsInLane = byLane[lane]
        percents = []

        counterDf = get_counters(df_by_elo['high_elo']['champ_data'], champ, champsInLane )
        for x in champsInLane:
            total = counterDf.loc[((counterDf['winner']==x) & (counterDf['loser']==champ)) | ((counterDf['winner']==champ) & (counterDf['loser']==x))]
            if len(total) == 0:
                continue
            win = len(counterDf.loc[(counterDf['winner']==champ) & (counterDf['loser']==x)])
            percents.append({
                "champ":x,
                "winRate": win*100/len(total)
            })

        winrate=pd.DataFrame(percents).sort_values("winRate")
        general_stats[champKeys[champ]]['strongAgainst']=winrate.tail(3)['champ'].tolist()
        general_stats[champKeys[champ]]['weakAgainst']=winrate.head(3)['champ'].tolist()
        

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
    
    

def get_skill_order(champ_data):
    df = champ_data[[str(x+1) for x in range(18)]]
    groups = df.groupby(df.columns.tolist(),as_index=False).size()\
        .reset_index().rename(columns={0:"records"}).sort_values("records",ascending=False).reset_index(drop=True)
    
    best_order = groups.iloc[0].to_dict()
    best_order = {x:int(y) for x,y in best_order.items() if x not in ["records"]}
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

