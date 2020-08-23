from django.conf import settings
import pandas as pd
from os import path
from assets.get_assets_mongodb import *

GRIETA = {
    "name":"Summoner's Rift",
    "mapId":"11"
}

ARAM = {
    "name":"Howling Abyss",
    "mapId":"12"
}

SMITE_SUMM = 11

MAIN_GAMEMODE="CLASSIC"
GAME_TYPE="MATCHED_GAME"

DIVISIONS=["I","II","III","IV"]
TIERS=["DIAMOND","PLATINUM","GOLD","SILVER","BRONZE","IRON"]

TOKEN_HEADER={
    "X-Riot-Token": settings.API_KEY
}

SERVER_ROUTES={
    "LAS":"la2.api.riotgames.com",
    "LAN":"la1.api.riotgames.com",
    "KR":"kr.api.riotgames.com",
    "JP":"jp1.api.riotgames.com",
    "BR":"br1.api.riotgames.com",
    "NA":"na1.api.riotgames.com",
    "EUN":"eun1.api.riotgames.com",
    "EUW":"euw1.api.riotgames.com",
    "OC":"oc1.api.riotgames.com",
    "TR":"tr1.api.riotgames.com",
    "RU":"ru.api.riotgames.com"
}

RANKED_QUEUES=[420,440]

SERVER_REAL_NAME_TO_ROUTE={
    "BR1":"BR",
    "EUN1":"EUN",
    "EUW1":"EUW",
    "JP1":"JP",
    "KR":"KR",
    "LA1":"LAN",
    "LA2":"LAS",
    "OC1":"OC",
    "TR1":"TR",
    "RU":"RU",
    "NA1":"NA",
}


MATCHES_STATS_KEYS=[
    "win","item0","item1","item2","item3","item4","item5","item6","kills",\
        "deaths","assists", "perk0","perk1","perk2","perk3","perk4","perk5",\
                "perkPrimaryStyle","perkSubStyle","statPerk0","statPerk1","statPerk2"
]

PLAYSTYLE_STATS_KEYS = [
    "win","kills","assists","deaths","totalDamageDealtToChampions","magicDamageDealtToChampions",\
        "physicalDamageDealtToChampions","goldEarned","totalMinionsKilled","neutralMinionsKilled","neutralMinionsKilledTeamJungle",\
            "neutralMinionsKilledEnemyJungle","wardsPlaced","wardsKilled","physicalDamageTaken",\
                "damageDealtToObjectives","magicalDamageTaken","trueDamageTaken","visionScore",
]

HIGH_ELO_TIERS = ["DIAMOND","PLATINUM","challengers","masters","grandmasters"]
LOW_ELO_TIERS = ["GOLD","SILVER","BRONZE","IRON"]
POST_DIAMOND_TIERS=["challengers","masters","grandmasters"]
PRE_DIAMOND_TIERS = ['IRON',"BRONZE","SILVER","GOLD","PLATINUM","DIAMOND"]


# =================================
# Item clases
# =================================
df_all_items = pd.DataFrame(get_all_items_data(final_form_only=False)).T[["name","id","price",'final_form',"tags"]]
# Busco items que esten en su forma final
df_items = pd.DataFrame(get_all_items_data(final_form_only=True)).T[["name","id","price",'final_form',"tags"]]
# Items de vision
trinkets = df_items.loc[((df_items['tags'].astype(str).str.contains("Trinket")))]['id'].tolist()
# Items finales
final_form_items = df_items.loc[~((df_items['tags'].astype(str).str.contains("Trinket|Consumable")))]['id'].unique()
# Botas
boots = df_items.loc[(df_items['tags'].astype(str).str.contains("Boots"))]['id'].tolist()
# GoldPer
support_items =  df_items.loc[((df_items['tags'].astype(str).str.contains("GoldPer")))]['id'].unique()
# Jungle items
jungle_items = df_items.loc[(df_items['name'].astype(str).str.contains("Encantamiento"))]['id'].unique()


# Sample de jugadores
player_sample = {
        "DIAMOND":{
            "I":400,
            "II":400,
            "III":400,
            "IV":400
        },
        "challengers":300,
        "masters":300,
        "grandmasters":300,
        "PLATINUM":{
            "I":400,
            "II":400,
            "III":400,
            "IV":400
        },
        "GOLD":{
            "I":100,
            "II":100,
            "III":100,
            "IV":100
        },
        "SILVER":{
            "I":100,
            "II":100,
            "III":100,
            "IV":100
        },
        "BRONZE":{
            "I":100,
            "II":100,
            "III":100,
            "IV":100
        },
        "IRON":{
            "I":100,
            "II":100,
            "III":100,
            "IV":100
        },
    }


division_name_to_n = {
    "I":1,
    "II":2,
    "III":3,
    "IV":4
}
division_n_to_name = {
    1:"I",
    2:"II",
    3:"III",
    4:"IV"
}

lane_name_to_n = {
    "BOTTOM":1,
    "JUNGLE":2,
    "MIDDLE":3,
    "TOP":4,
    "NONE":5
}
lane_n_to_name = {
    1:"BOTTOM",
    2:"JUNGLE",
    3:"MIDDLE",
    4:"TOP",
    5:"NONE"
}

role_name_to_n={
    "DUO":1,
    "DUO_CARRY":2,
    "DUO_SUPPORT":3,
    "NONE":4,
    "SOLO":5
}
role_n_to_name={
    1:"DUO",
    2:"DUO_CARRY",
    3:"DUO_SUPPORT",
    4:"NONE",
    5:"SOLO"
}


tier_name_to_n={
'IRON':1,
"BRONZE":2,
"SILVER":3,
"GOLD":4,
"PLATINUM":5,
"DIAMOND":6,
"masters":7,
"grandmasters":8,
"challengers":9,
}

tier_n_to_name={
1:"IRON",
2:"BRONZE",
3:"SILVER",
4:"GOLD",
5:"PLATINUM",
6:"DIAMOND",
7:"masters",
8:"grandmasters",
9:"challengers"
}


# Crontabs
cron_players={
    "day_of_week":'0,3',
    "hour":"4",
    "minute":"38",
    "day_of_month":"*",
    "month_of_year":"*"
}
cron_players_text = "{} {} {} {} {}".format(cron_players['minute'], cron_players['hour'], \
    cron_players['day_of_month'], cron_players['month_of_year'], cron_players['day_of_week'])



# Fases del juego
MIN_GAME_DURATION = 60 * 5 # 5 minutos
EARLY_GAME_RANGE = [0, 60 * 25]
MID_GAME_RANGE = [EARLY_GAME_RANGE[1], 60 * 35]
LATE_GAME_RANGE = [MID_GAME_RANGE[1], 60 * 100]

PHASE_BAD_RANGE = [0, 48]
PHASE_OK_RANGE = [48, 53]
PHASE_GOOD_RANGE = [53, 100]
