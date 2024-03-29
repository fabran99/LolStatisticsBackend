from django.conf import settings
import pandas as pd
import random
from datetime import datetime as dt

GRIETA = {
    "name": "Summoner's Rift",
    "mapId": "11"
}

ARAM = {
    "name": "Howling Abyss",
    "mapId": "12"
}

SMITE_SUMM = 11

MAIN_GAMEMODE = "CLASSIC"
GAME_TYPE = "MATCHED_GAME"

DIVISIONS = ["I", "II", "III", "IV"]
TIERS = ["DIAMOND", "PLATINUM", "GOLD", "SILVER", "BRONZE", "IRON"]


SERVER_ROUTES = {
    "LAS": "la2.api.riotgames.com",
    "EUN": "eun1.api.riotgames.com",
    "LAN": "la1.api.riotgames.com",
    "OC": "oc1.api.riotgames.com",
    "KR": "kr.api.riotgames.com",
    "JP": "jp1.api.riotgames.com",
    "RU": "ru.api.riotgames.com",
    "BR": "br1.api.riotgames.com",
    "EUW": "euw1.api.riotgames.com",
    "NA": "na1.api.riotgames.com",
    "TR": "tr1.api.riotgames.com",
}


SERVER_ROUTES_API_KEYS = {
    "LAS": settings.API_KEYS[0],
    "LAN": settings.API_KEYS[0],
    "KR": settings.API_KEYS[0],
    "JP": settings.API_KEYS[0],
    "BR": settings.API_KEYS[0],
    "NA": settings.API_KEYS[0],
    "EUN": settings.API_KEYS[1],
    "EUW": settings.API_KEYS[1],
    "OC": settings.API_KEYS[1],
    "TR": settings.API_KEYS[1],
    "RU": settings.API_KEYS[1]
}

MATCHLIST_SERVER_ROUTES = {
    "LAS":"americas.api.riotgames.com",
    "LAN":"americas.api.riotgames.com",
    "BR":"americas.api.riotgames.com",
    "NA":"americas.api.riotgames.com",
    "KR":"asia.api.riotgames.com",
    "JP":"asia.api.riotgames.com",
    "EUN":"europe.api.riotgames.com",
    "EUW":"europe.api.riotgames.com",
    "TR":"europe.api.riotgames.com",
    "RU":"europe.api.riotgames.com",
    "OC":"sea.api.riotgames.com",
}



def get_token_header(token=None):
    if token is None:
        token = settings.API_KEYS[0]
    return {
        "X-Riot-Token":token #random.choice(settings.API_KEYS)
    }
RANKED_QUEUES = [420, 440]
SOLO_QUEUE = 420

SERVER_REAL_NAME_TO_ROUTE = {
    "BR1": "BR",
    "EUN1": "EUN",
    "EUW1": "EUW",
    "JP1": "JP",
    "KR": "KR",
    "LA1": "LAN",
    "LA2": "LAS",
    "OC1": "OC",
    "TR1": "TR",
    "RU": "RU",
    "NA1": "NA",
}


MATCHES_STATS_KEYS = [
    "win", "item0", "item1", "item2", "item3", "item4", "item5", "item6",
    "perk0", "perk1", "perk2", "perk3", "perk4", "perk5",
    "perkPrimaryStyle", "perkSubStyle", "statPerk0", "statPerk1", "statPerk2"
]

PLAYSTYLE_STATS_KEYS = [
    "win", "kills", "assists", "deaths", "totalDamageDealtToChampions", "magicDamageDealtToChampions",
    "physicalDamageDealtToChampions", "goldEarned", "totalMinionsKilled", "neutralMinionsKilled", "neutralMinionsKilledTeamJungle",
    "neutralMinionsKilledEnemyJungle", "wardsPlaced", "wardsKilled", "physicalDamageTaken",
    "damageDealtToObjectives", "magicalDamageTaken", "trueDamageTaken", "visionScore",
]

HIGH_ELO_TIERS = ["DIAMOND", "PLATINUM",
                  "challengers", "masters", "grandmasters"]
LOW_ELO_TIERS = ["GOLD", "SILVER", "BRONZE", "IRON"]
POST_DIAMOND_TIERS = ["challengers", "masters", "grandmasters"]
PRE_DIAMOND_TIERS = ['IRON', "BRONZE", "SILVER", "GOLD", "PLATINUM", "DIAMOND"]


# Sample de jugadores
player_sample = {
    "DIAMOND": {
        "I": 200,
        "II": 200,
        "III": 200,
        "IV": 200
    },
    "challengers": 300,
    "masters": 300,
    "grandmasters": 300,
    "PLATINUM": {
        "I": 100,
        "II": 100,
        "III": 100,
        "IV": 100
    },
    "GOLD": {
        "I": 10,
        "II": 10,
        "III": 10,
        "IV": 10
    },
    "SILVER": {
        "I": 10,
        "II": 10,
        "III": 10,
        "IV": 10
    },
    "BRONZE": {
        "I": 10,
        "II": 10,
        "III": 10,
        "IV": 10
    },
    "IRON": {
        "I": 10,
        "II": 10,
        "III": 10,
        "IV": 10
    },
}


# Conversion de int a datos
division_name_to_n = {
    "I": 1,
    "II": 2,
    "III": 3,
    "IV": 4
}
division_n_to_name = {
    1: "I",
    2: "II",
    3: "III",
    4: "IV"
}

lane_name_to_n = {
    "BOTTOM": 1,
    "JUNGLE": 2,
    "MIDDLE": 3,
    "TOP": 4,
    "UTILITY": 5
}
lane_n_to_name = {
    1: "BOTTOM",
    2: "JUNGLE",
    3: "MIDDLE",
    4: "TOP",
    5: "UTILITY"
}

role_name_to_n = {
    "DUO": 1,
    "DUO_CARRY": 2,
    "DUO_SUPPORT": 3,
    "NONE": 4,
    "SOLO": 5
}
role_n_to_name = {
    1: "DUO",
    2: "DUO_CARRY",
    3: "DUO_SUPPORT",
    4: "NONE",
    5: "SOLO"
}


tier_name_to_n = {
    'IRON': 1,
    "BRONZE": 2,
    "SILVER": 3,
    "GOLD": 4,
    "PLATINUM": 5,
    "DIAMOND": 6,
    "masters": 7,
    "grandmasters": 8,
    "challengers": 9,
}

tier_n_to_name = {
    1: "IRON",
    2: "BRONZE",
    3: "SILVER",
    4: "GOLD",
    5: "PLATINUM",
    6: "DIAMOND",
    7: "masters",
    8: "grandmasters",
    9: "challengers"
}


# Crontabs
cron_players = {
    "day_of_week": '0,4',
    "hour": "5",
    "minute": "47",
    "day_of_month": "*",
    "month_of_year": "*"
}
cron_players_text = "{} {} {} {} {}".format(cron_players['minute'], cron_players['hour'],
                                            cron_players['day_of_month'], cron_players['month_of_year'], cron_players['day_of_week'])


# Fases del juego
MIN_GAME_DURATION = 60 * 5  # 5 minutos
EARLY_GAME_RANGE = [0, 60 * 25]
MID_GAME_RANGE = [EARLY_GAME_RANGE[1], 60 * 35]
LATE_GAME_RANGE = [MID_GAME_RANGE[1], 60 * 100]

PHASE_BAD_RANGE = [0, 48]
PHASE_OK_RANGE = [48, 53]
PHASE_GOOD_RANGE = [53, 100]


LAST_IMPORTANT_PATCH = dt(2020, 11, 9).timestamp()*1000

# Limpiezas
DAYS_TO_REMOVE_DATA = 5