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
    "win","item0","item1","item2","item3","item4","item5","item6","kills","deaths","assists","pentaKills","quadraKills","doubleKills","tripleKills","totalDamageDealtToChampions","magicDamageDealtToChampions","physicalDamageDealtToChampions","perk0","perk1","perk2","perk3","perk4","perk5","perkPrimaryStyle","perkSubStyle","statPerk0","statPerk1","statPerk2"
]

PLAYSTYLE_STATS_KEYS = [
    "win","kills","assists","deaths","totalDamageDealtToChampions","magicDamageDealtToChampions","physicalDamageDealtToChampions","goldEarned","totalMinionsKilled","neutralMinionsKilled","neutralMinionsKilledTeamJungle","neutralMinionsKilledEnemyJungle","wardsPlaced","wardsKilled",
]

HIGH_ELO_TIERS = ["DIAMOND","PLATINUM","challengers","masters","grandmasters"]
LOW_ELO_TIERS = ["GOLD","SILVER","BRONZE","IRON"]
POST_DIAMOND_TIERS=["challengers","masters","grandmasters"]
PRE_DIAMOND_TIERS = ['IRON',"BRONZE","SILVER","GOLD","PLATINUM","DIAMOND"]


# =================================
# Item clases
# =================================

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


# =============================
# Csv preprocess de datos
# =============================
saved_players_route = path.join(settings.PREPROCESS_PATH,"saved" ,"players.csv")
saved_matches_route = path.join(settings.PREPROCESS_PATH,"saved" ,"matches.csv")
saved_champ_ban_route = path.join(settings.PREPROCESS_PATH,"saved" ,"champbans.csv")
saved_champ_data_route = path.join(settings.PREPROCESS_PATH,"saved" ,"champdata.csv")
saved_playstyle_route = path.join(settings.PREPROCESS_PATH,"saved" ,"playstyle.csv")

temp_players_route = path.join(settings.PREPROCESS_PATH,"temp" ,"players.csv")
temp_matches_route = path.join(settings.PREPROCESS_PATH,"temp" ,"matches.csv")
temp_champ_ban_route = path.join(settings.PREPROCESS_PATH,"temp" ,"champbans.csv")
temp_champ_data_route = path.join(settings.PREPROCESS_PATH,"temp" ,"champdata.csv")
temp_playstyle_route = path.join(settings.PREPROCESS_PATH,"temp" ,"playstyle.csv")
